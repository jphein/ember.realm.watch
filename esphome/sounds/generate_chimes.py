#!/usr/bin/env python3
"""Generate Ember's hearth chimes at 16kHz mono for the ES3C28P satellite.

Same struck-glass synthesis as speech-to-cli's desktop chimes (audio.py
_generate_chimes), re-rendered at the device's native rate so the hearth and
the desktop sound like one instrument.

Why 16kHz is enough here: the highest partial is 6.79x the fundamental, and the
highest fundamental is C5 (523.25Hz) -> 3552Hz. Nyquist at 16kHz is 8000Hz, so
nothing aliases. Rendering at 44.1kHz and letting the device resample would be
strictly worse — it would put a resampler in an audio path that is deliberately
a straight line (see the media_player notes in ember-satellite.yaml).

Run:  python3 generate_chimes.py        (writes/overwrites *.wav here)
"""
import math
import struct
import wave

RATE = 16000

# Inharmonic partials — real bells and glass have non-integer ratios, and that
# is what makes them read as a struck physical object rather than an
# oscillator. Higher partials decay faster, as they do on a real body.
#            ratio   amp    decay (x faster than fundamental)
PARTIALS = [(1.000, 1.000, 1.00),
            (2.000, 0.460, 1.45),
            (3.010, 0.250, 1.95),
            (4.170, 0.130, 2.60),
            (5.430, 0.062, 3.40),
            (6.790, 0.030, 4.30)]

# Warm F-pentatonic: every pair is consonant, so the set is one family.
F3, F4, G4, A4, C5, D5 = 174.61, 349.23, 392.00, 440.00, 523.25, 587.33


def render(notes, tail=0.5):
    """notes: [(freq, start_s, amp, decay_s)] placed on a shared timeline.

    Notes OVERLAP and ring through each other. Nothing is ever spliced —
    hard concatenation is what made the original chimes click.
    """
    total = max(s + d for _, s, _, d in notes) + tail
    n = int(RATE * total)
    buf = [0.0] * n
    for freq, start, amp, decay in notes:
        i0 = int(start * RATE)
        # Twin voice detuned 0.15%: slow beating reads as "glassy".
        for detune, dweight in ((1.0, 1.0), (1.0015, 0.55)):
            for ratio, pamp, pdecay in PARTIALS:
                f = freq * ratio * detune
                if f > RATE * 0.45:          # stay well under Nyquist
                    continue
                tau = decay / pdecay
                a = amp * pamp * dweight
                w = 2.0 * math.pi * f
                for i in range(i0, n):
                    t = (i - i0) / RATE
                    e = math.exp(-t / tau)
                    if e < 0.0005:
                        break
                    if t < 0.004:            # 4ms raised-cosine attack
                        e *= 0.5 - 0.5 * math.cos(math.pi * t / 0.004)
                    buf[i] += a * e * math.sin(w * t)
    return buf


def write(name, buf, peak=0.42):
    m = max((abs(v) for v in buf), default=0.0)
    g = (peak / m) if m > 0 else 0.0
    out = []
    for v in buf:
        x = math.tanh(v * g * 1.35) / 1.35   # soft clip; can never buzz
        out.append(int(max(-1.0, min(1.0, x)) * 32767))
    with wave.open(name, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(struct.pack(f"<{len(out)}h", *out))
    print(f"  {name:<22} {len(out)/RATE*1000:6.0f}ms  peak {peak:.2f}")


def main():
    # listening — open rising fifth: an invitation to speak.
    write("chime_listening.wav",
          render([(A4, 0.000, 0.85, 0.55), (D5, 0.075, 0.95, 0.85)]), 0.38)

    # thinking — soft low tick. Deliberately quietest: may fire repeatedly.
    write("chime_thinking.wav",
          render([(F4, 0.0, 0.50, 0.22)], tail=0.15), 0.20)

    # done — falling fifth resolving to the root: closure.
    write("chime_done.wav",
          render([(C5, 0.000, 0.80, 0.50), (F4, 0.080, 0.90, 1.00)]), 0.34)

    # error — the one tone deliberately OFF the pentatonic. A minor second
    # against the root is the only dissonance in the set, so it cannot be
    # mistaken for a normal event even at low volume.
    write("chime_error.wav",
          render([(F4, 0.0, 0.85, 0.45), (F4 * 1.0595, 0.0, 0.70, 0.55)]), 0.34)

    # announce — "a word from the house": rising, brighter, distinct from
    # `listening` so a pushed announcement is not mistaken for a prompt.
    write("chime_announce.wav",
          render([(F4, 0.000, 0.70, 0.45),
                  (A4, 0.070, 0.80, 0.60),
                  (C5, 0.140, 0.90, 0.90)]), 0.36)

    # timer — insistent but not harsh: three strikes on the root.
    write("chime_timer.wav",
          render([(C5, 0.00, 0.85, 0.35),
                  (C5, 0.28, 0.85, 0.35),
                  (C5, 0.56, 0.90, 0.80)]), 0.40)

    # touch — acknowledges the tap landed, and MUST be short.
    #
    # This one is length-constrained by physics, not taste. It plays out of the
    # same speaker whose I2S hub is shared with the mic, in one enclosure, with
    # NO acoustic echo cancellation (noise_suppression_level and auto_gain are
    # not AEC). If it is still ringing when the mic opens, HA's VAD hears the
    # chime, then hears its trailing silence, and ends the utterance before a
    # word is spoken. The symptom is "Ember can't hear me" — an STT bug that
    # isn't an STT bug.
    #
    # So: ~200ms total, one soft note, decay short enough to be fully silent
    # before voice_assistant.start is allowed to run.
    # >>> Do not lengthen this, and do not substitute chime_listening (1.4s).
    #     Pair it with a delay >= its own length before opening the mic. <<<
    write("chime_touch.wav",
          render([(G4, 0.0, 0.70, 0.085)], tail=0.06), 0.30)

    # haptic — a felt tap rather than a heard note. Every touch event.
    #
    # This is NOT the struck-glass voice: no inharmonic partials, because a bell
    # rings and a tap must not. Just the fundamental plus its octave, decaying in
    # ~12ms, so the ear registers an impulse and the cone registers a shove.
    #
    # F3 (174.6Hz) is the lowest note in the set, so it stays in the same
    # pentatonic family as every other tone while sitting where a small 8-ohm
    # speaker can still move air. Anything lower is inaudible on this hardware and
    # would only waste excursion.
    #
    # ~30ms total. Length is a HARD constraint, for two reasons:
    #   1. Every playback is a speaker driver cycle, and driver cycles are what
    #      correlate with the unresolved MCLK-start pop. Short means the tap is
    #      over before the next one, so bursts coalesce in one driver session.
    #   2. A 145ms tone previously took the shared I2S lock and left the mic deaf
    #      for a full second. Short plus wait_until:speaker.is_stopped is what
    #      makes a per-touch sound safe at all.
    # >>> Do not lengthen this and do not add partials. It stops being a tap. <<<
    write("chime_haptic.wav",
          render([(F3, 0.0, 1.00, 0.012), (F3 * 2.0, 0.0, 0.35, 0.008)],
                 tail=0.012), 0.55)

    # guttering — the mobile hearth's cell is low (~20%). A falling figure that
    # keeps falling: C5 -> A4 -> F4 walks DOWN the pentatonic and comes to rest
    # on the lowest sung note in the set, which is the shape of something dying
    # down rather than resolving. Distinct from `done` (a two-note fall that
    # RESOLVES, closure) by the third step — this one sinks past where done
    # lands. Stays on the pentatonic on purpose: a low cell is a normal part of
    # a portable object's day, not an error, and the off-scale dissonance is
    # reserved for exactly one meaning (chime_error).
    #
    # Fires at most once per discharge (latched in firmware, reset on charge),
    # so unlike `thinking` it can afford to be full voice.
    write("chime_guttering.wav",
          render([(C5, 0.000, 0.85, 0.40),
                  (A4, 0.140, 0.80, 0.50),
                  (F4, 0.300, 0.90, 1.00)]), 0.36)


if __name__ == "__main__":
    main()
