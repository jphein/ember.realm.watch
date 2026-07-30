# The audible pop on audio start

Hard-won analysis of the ES8311 + FM8002E audio path on the ES3C28P, moved out of the
original `esphome/README.md` when Ember was extracted into its own repository.

**The original prose is unchanged.** Nothing has been edited away or summarised —
several paragraphs exist specifically to correct earlier wrong claims, and that record
is the point. What has been *added* is signposting: banners marking which conclusions
were later superseded, and a coda documenting how the question was finally settled.
Additions are always marked; nothing was quietly revised to look prescient.

Start at [the gotcha table in the README](../README.md#settings-that-look-like-mistakes-and-arent)
for the settings this analysis justifies.

> ## ✅ RESOLVED — read this before the analysis below
>
> **The pop is gone, and the mechanism is the amplifier.** Gating the amp on the speaker
> fixed it; the codec mute is positively excluded. Jump to
> **[The answer](#the-answer-the-amp-is-the-mechanism)**.
>
> **Everything between here and the coda is the analysis as it stood while the question
> was still open.** It is kept because it is the most instructive part of this project —
> it reaches the right mechanisms, argues itself into two opposite errors, and states
> honestly that the evidence available to it could not decide. Sections below marked
> *"partly fixed"*, *"we have not distinguished the two"*, or proposing an experiment as
> future work are **superseded**, not current. They are history, deliberately not
> rewritten.

---

#### ⚠️ Partly fixed: an audible pop on some audio starts

*(Historical heading. This was true when written; see [The answer](#the-answer-the-amp-is-the-mechanism).)*

`use_mclk: true`, and MCLK is only driven while an I2S channel is loaded — so
when *both* the speaker and the microphone are unloaded, MCLK stops entirely.
Every start therefore restarts the codec's clock, and that restart is when the
pop happens.

**Why a clock restart pops, and why the amp is the fix.** REG31's `DAC_DSMMUTE`
(bit 6) and `DAC_DEMMUTE` (bit 5) are latched I²C bits, written over CCLK/CDATA
(ES8311 rev 8.0 §5). ESPHome's only writer is `set_mute_state_()`
(`es8311.cpp:207-223`, a read-modify-write of just those two bits) and `setup()`
never re-runs, so a mute asserted before an MCLK stop is **still asserted** when
the clock returns. That much is confirmed from the driver source.

What does *not* follow is that the mute is therefore **in force at the analog
output** across the gap. Both bits act on the DAC's digital blocks — the
datasheet expresses the mute target as a modulator *code* (`DAC_DSMMUTE_TO`,
"mute to 8" / "mute to 7/9"), and the same register's bit 3 `DAC_RAMCLR` is
explicitly qualified *"when lrck/dac_mclk active"* — while everything after them
in the block diagram (§1: DAC → **HP Driver** → OUTP/OUTN, biased from VMID) is
analog and stays powered continuously, because ESPHome writes REG0D=0x01,
REG0E=0x02, REG12=0x00, REG13=0x10 once at boot and never revisits them.

**The ES8311 datasheet does not specify what OUTP/OUTN do while the DAC is
powered but unclocked**, gives no power-up/power-down sequence, and mentions "pop
and click noise suppression" exactly once — a page-1 feature bullet with no
application section behind it. The mechanisms that *are* documented as
clock-counted are the staged power-up timers (REG0x0B/0x0C, specified in LRCK
periods: "0~31: 21us~232ms (LRCK=48KHz)") and the volume/DRC soft ramp
(REG0x37[7:4], "0.25dB/N LRCK") — and **the ramp is off**: ESPHome writes
REG37=0x08 for `DAC_EQBYPASS`, which leaves `DAC_RAMPRATE=0` = "disable soft
ramp" as an incidental side effect, not a choice.

So the restart transient is either **analog** — the FM8002E's own datasheet names
one: a large input coupling cap Ci lengthens its feedback network's settling and
*causes* pop; Ci recommended 0.1–0.39µF, this board reported at 0.39µF
(**unconfirmed, from pdftotext of the schematic**; and note these are the amp's
*input* caps — its outputs need none, it is BTL) — **or** it is digital but
arrives in the first LRCK cycles before the muted modulator has converged, with
no soft ramp to cover them. **We have not distinguished the two, and the
available evidence cannot:** both predict every observation we have.

What both agree on is the fix. Gating the amp on GPIO1 (SHUTDOWN high = off;
TD = 100ms typ wake, hence a 180ms default) interrupts the path **downstream of
every transient the codec can produce**, digital or analog. That makes it the
**primary** mitigation, not the second choice. Codec mute is still worth
asserting — it demonstrably suppresses the speaker-side discontinuity inside the
50ms preloaded-silence window when MCLK is already up — but it acts upstream of
the analog output stage and **has never been shown, on its own, to suppress a
clock-restart transient.**

> **Two earlier claims in this file were wrong, in opposite directions.** The
> first said REG31 mute "is enforced inside the clock domain" and so could not
> hold across a restart — wrong about the *bit*, which is latched. The
> correction then overshot: it said the mute therefore *does* suppress the
> restart pop, and that `amp_blank_ms` "defaults to 0". **`amp_blank_ms` was
> never 0 in any commit** — that described an intent that was never applied. Two
> commit messages (`feat(ember): blank the amp…`, `feat(ember): haptic touch
> feedback…`) carry one or other wrong version; this section supersedes both.

| transient | suppressed? |
|---|---|
| Speaker start, MCLK already up | **Yes** — REG31 inside the 50ms preloaded-silence window |
| Mic-side start (tap to talk) | **Yes** — but by `amp_blank` *and* `audio_dac.mute_on` together; the two have never been separated |
| Failed starts (`Parent bus is busy`) | **Nothing to suppress** — see below |
| The amp's own enable click | Datasheet claims it is suppressed; 0.39µF Ci would be worst-case. Unmeasured — but blanking was a net win by ear |

**The one experiment that settles it, now runnable without a reflash.** The
"pop returned with blanking off" listening test predates `talk_begin`'s
`audio_dac.mute_on`, so it only shows blanking works *without* codec mute — not
that codec mute is insufficient *with* it. Set the **Amp Blank Width** number to
`0` and tap to talk. Pop returns ⇒ codec mute is insufficient and the transient
is downstream of the digital mute. Pop stays away ⇒ blanking is redundant and the
subsystem can be deleted.

> **✅ ANSWERED — this paragraph is history.** The experiment ran, in a form nobody
> designed: two reports on one build gave the comparison directly. **Pop returns.**
> Codec mute is insufficient, the transient is downstream of the digital mute, and the
> amp is the mechanism — so the subsystem stays. See
> [The answer](#the-answer-the-amp-is-the-mechanism). Note the second branch above
> ("blanking is redundant and the subsystem can be deleted") is the reasoning that later
> became **wrong claim #4** — it was proposed after the reply-side pop and refuted by
> tabulation. Left in place; the trap is instructive.

**Part-number provenance:** the two hard numbers cited above (Ci 0.1–0.39µF,
TD = 100ms typ) come from the **FM8002E** datasheet specifically. Comments in the
YAML still say SC8002B. These are very likely the same part — FM8002E's vendor is
深圳市富满电子 / `superchip.cn`, i.e. **SC = SuperChip** — but pin-for-pin
equivalence is unconfirmed.

**One unexplained disagreement between driver and datasheet**, recorded because
it is the only place the two visibly diverge in the analog bias domain: ESPHome
writes `REG0D = 0x01`, which is `VMIDSEL = 0b01` = *"start up vmid normal speed
charge"*, and **never advances to `0b10` = "normal vmid operation"**. The codec is
parked permanently in VMID start-up-charge mode. There is no evidence this
contributes to the pop and it is not a proposed fix.

**Failed starts are not a pop source**, despite looking like the obvious suspect.
`Parent bus is busy` is the `try_lock()` failure at
`i2s_audio_speaker_standard.cpp:400-403`, which returns `ESP_ERR_INVALID_STATE`
**before `i2s_new_channel()`** — before any DMA allocation or channel enable. A
failed start touches zero hardware; it costs latency and log noise only. (An
earlier revision of this file claimed otherwise. It was wrong.)

**Cheapest falsification if you doubt the trigger:** turn `Hush` on and tap to talk.
Hush blocks `voice_assistant.start`, so no clock start occurs. If the pop still
happens, the trigger is not the mic-side start and something else is restarting
the clock.

**A pop that is not a race, and needs a different fix.** The chime→reply gap
measures **2.716s** — longer than the speaker's `timeout: 500ms`. So the driver
unloads and reloads *mid-response*, before every single reply, which is a clock
restart nobody asked for. The gap is Piper's synthesis latency, not driver
policy, so raising `timeout` past ~3s or holding the driver loaded across the
turn are the real levers — not anything in the codec.

> **Two settings on the speaker look alike and are not.**
> `buffer_duration: 500ms` is the measured fix for choppy playback (a 16s
> utterance went 45.8% → 100.7% delivered) — do not lower it.
> `timeout: 500ms` is how long the driver stays loaded holding the shared I2S
> lock. It was briefly cut to 100ms to stop the speaker starving the mic, which
> was **the wrong side of the contention** — the log shows the speaker blocking
> because the *mic* held the lock, and no `timeout` value affects that direction.
> Worse, 100ms multiplied driver cycles: six volume taps became six load/unload
> cycles instead of coalescing into one session. Reverted. The mic-stall it was
> meant to fix is now handled precisely by `wait_until: speaker.is_stopped` in
> `talk_begin`, which waits the ~0-500ms actually required instead of losing a
> blind second to the driver's retry backoff.

---

# Coda — how it was actually resolved

*Added when Ember was extracted. Everything above is the analysis as it stood while
the question was open; this section is what closed it. The two are kept separate on
purpose — the reasoning above was correct about the mechanisms and wrong about where
the protection sat, and that distinction is the transferable lesson.*

## The protection was behind the transient

Everything above assumes the pop happens at a clock restart the config is positioned
to cover. It wasn't. The pop heard "before the chime" **was the haptic's own driver
cold start**, and the device log puts it 1.1 seconds ahead of the protection:

```
08.403  speaker_media_player: ANNOUNCING     (haptic queued)
08.502  i2s_audio.speaker: Starting          (COLD START — amp live, DAC unmuted)
08.599  Stopped
 ...~1.1s later...  talk_begin: audio_dac.mute_on + amp_blank
```

So **no value of `amp_blank_ms` could ever have reached it.** That is a falsifiable
prediction, and it explains the one loose thread above: why the `amp_blank` A/B test
kept coming back inconclusive. It was measuring a knob that acted after the event.

## The correction chain, in order

This file has now been wrong in three distinguishable ways, and each error was found
by a different method. That progression is worth more than the conclusion.

| # | The claim | Why it was wrong | What found it |
|---|---|---|---|
| 1 | REG31 mute "is enforced inside the clock domain" and cannot hold across a restart | Wrong about the **bit** — it is a latched I²C bit and does hold | Reading the driver source |
| 2 | The correction overshot: the mute therefore *does* suppress the restart pop, and `amp_blank_ms` "defaults to 0" | `amp_blank_ms` was **never** 0 in any commit; that described an intent never applied | Reading the commit history against the file |
| 3 | "The amp finishes waking before the blank lifts" | **Inverted mental model.** GPIO1 is `inverted: true` on an **active-low** SHUTDOWN, so `output.turn_off: amp_enable` genuinely *disables* the amp — and a disabled amp is not waking. Its ~100 ms wake begins only when the watchdog **re-enables** it | Trying to hoist the blank ahead of the tone, and finding the timeline impossible |
| 4 | "It still pops with the DAC muted, so amp gating can be retired too" | **Exactly backwards.** Tabulating the evidence shows amp gating was the *only* mechanism ever observed **in position** at a transient that did **not** pop. The muted-DAC pop is evidence against the *codec mute*, not against the *amp* | Tabulating every observation instead of reasoning forward from the newest datapoint. Refuted within minutes of being proposed |

Correcting #3 gives the real timeline: **off at T+0, re-enabled at T+180, usably awake
at ~T+280.** A 24 ms tone starting ~110 ms in is therefore **silenced, not protected**.
Amp blanking and a short touch tone are structurally incompatible — which no amount of
tuning would have revealed, because the two mechanisms were never in the same window.

## The decisive experiment had never been staged

The section above proposes the one test that settles it: set **Amp Blank Width** to `0`
and tap to talk. An earlier datasheet audit went looking for that result and found
something more useful — **the experiment had never actually been run in a form that
could answer the question.** The protection had never once been given a transient it
was in position to cover, so every "inconclusive" result was correct and uninformative
at the same time.

Exempting the talk tap from the haptic is what finally staged it. With no tone at tap
time, the only remaining transient on that path is the mic's own MCLK restart — which
happens *inside* `talk_begin`, the one place the config was designed to protect. A
clean binary: no pop ⇒ the protection works; still pops ⇒ amp gating can be retired
outright.

**It came back clean.** Confirmed by ear: the touch pop is gone. So the mute and
`amp_blank` in `talk_begin` **do** work — they had simply never been given a transient
they could reach.

## Which isolated the one nothing covered

The residual is on the **reply** path: its own driver cold start, ~2.8 s after the
chime, because the 500 ms driver timeout unloads the driver while Piper is still
synthesising. (That 2.716 s chime→reply gap is measured above — it was the right
observation attached to the wrong conclusion.)

The fix was to **invert the policy** rather than add a third mute site. The mute had
been asserted at two specific places, boot and `talk_begin`, which could only ever
protect transients someone had thought of. The 10 ms watchdog now also does the
reverse: **hold the DAC muted whenever the speaker is stopped**, so every cold start
begins muted, including ones nobody has enumerated.

Same principle as guarding the chimes on `spk->is_running()` instead of per-call-site
flags — *ask the hardware the direct question, and future call sites inherit the
answer.* It costs no audio, and the proof was already in the file: every playback
preloads 5 × 10 ms of memset-zero silence before `i2s_channel_enable()`, so the unmute
lands inside that window.

The re-mute is **deferred 200 ms and cancellable**, which is not belt-and-braces.
Asserting REG31 mute steps the DAC output while the amp is still enabled — the same
class of transient this whole subsystem exists to suppress, at the other end of
playback. Two things argue it's harmless (the last frame is end-of-speech
near-silence; ES8311 mute is normally a soft step) and one argues it isn't (this
board's 0.39 µF coupling caps are worst-case for pop per the amp's own datasheet).
Not worth betting on. Deferring also coalesces bursts, and cancelling on resume means
a stuttering reply can't be muted mid-sentence.

---

# The answer: the amp is the mechanism

**The pop is gone.** Confirmed by ear on the shipped build: tap-to-talk, conversation,
and multi-turn all clean.

What settled it was **not a datasheet.** Everything above is a datasheet argument, and
the datasheets could not discriminate — they specify what the mute *bit* does and are
silent on what OUTP/OUTN do while the DAC is powered but unclocked. What settled it was
**two reports on the same build**, which happened to constitute a controlled experiment:

| transient | protection in place | result |
|---|---|---|
| **mic** cold start (inside `talk_begin`) | DAC muted **+ amp blanked** | **no pop** |
| **reply** cold start (after the synthesis gap) | DAC muted, **amp not** | **pop** |

Same clock domain, same codec, same build. **One variable: the amp.** Gating the amp on
the speaker removed the remaining pop.

And the codec mute is now **positively excluded**, not merely doubted. That's a stronger
claim than anything above, and it's only available because of the muted-while-stopped
policy: the watchdog holds REG31 asserted whenever the speaker is stopped, so the DAC
was **provably muted** before the reply's cold start — and it popped anyway. A mute that
is demonstrably in force and demonstrably doesn't help is excluded, not suspected.

## The two audits were both right

This is the part most worth keeping, because the instinct is to declare a winner and
there isn't one.

- **Audit A** held that the REG31 mute is a **latched I²C bit** and therefore survives
  an MCLK stop. **True** — confirmed from the driver source.
- **Audit B** held that every documented ES8311 anti-pop mechanism is **counted in LRCK
  periods**, and so cannot act while the clock is stopped. **Also true** — the staged
  power-up timers are specified in LRCK periods and the soft ramp is disabled outright.

Both are correct, and together they give the actual answer: **the bit persists *and* has
no effect.** Neither audit was wrong; the question was **underdetermined**, and the two
findings only look contradictory if you assume "the mute is asserted" and "the mute is
working" are the same proposition. They are not, and this file spent three revisions
conflating them.

## The accepted trade

Amp gating is not free. The FM8002E wakes in **~100 ms** typical, while playback preloads
only **~50 ms** of silence — so roughly **50 ms of every reply is a soft start.** That is
a deliberate trade: a slightly soft first fraction of a syllable in exchange for no pop,
on a device whose whole job is to be pleasant to talk to in a quiet room.

It is **live-adjustable** without a reflash via the **Amp Blank Width** number. Setting
it to **0 restores the amp immediately — and brings the pop back.** That is also the
cheapest way for anyone to re-confirm the conclusion above for themselves.

## ⚠️ Known hazard, quantified and deliberately accepted

The unmute's safety rests on landing inside that 50 ms silence window. But
`is_running()` flips in the speaker's own `loop()` while the watchdog is an
`interval:` — **both in the same main loop**, so a long-running frame delays the flip
and the unmute together.

Measured blocks on this device: **80 ms** (overlay dismiss) and **126 ms**, the latter
landing 309 ms after speaker start — precisely in the exposure window. 126 > 50, so
worst case **~76 ms of a reply plays muted**.

> **The symptom is not a pop. It is a quiet or clipped first syllable** — which would
> be blamed on TTS and debugged in an entirely different subsystem. That is the only
> reason this paragraph exists. **The mitigation is display-side** (keep any frame at
> playback start under ~40 ms), not audio-side.

## What generalises

The resolution method is more instructive than the answer, so this is the part to take
away.

1. **Check whether your protection is positioned to see the event before you tune it.**
   Three rounds of inconclusive A/B testing were all measuring a knob that fired *after*
   the transient it was meant to suppress. No amount of tuning could have worked, and
   the inconclusiveness was the clue.
2. **An inconclusive result is a claim about the experiment, not only about the
   hypothesis.** Three explanations were published before anyone checked whether the
   test could discriminate between them. The audit that found the decisive experiment
   **had never been staged** was worth more than any individual measurement — until then
   every result was simultaneously correct and uninformative.
3. **Two contradictory audits can both be right.** "The mute bit persists" and "no
   documented anti-pop mechanism can act without a clock" only look incompatible if you
   assume *asserted* and *working* are the same proposition. They aren't, and conflating
   them cost three revisions. When two careful investigations disagree, suspect the
   question is underdetermined before you suspect one of them.
4. **A controlled experiment can fall out of ordinary use.** What finally settled it was
   two reports on one build — mic start protected by mute *and* amp, reply start
   protected by mute alone. One variable. No instrumentation, no reflash. Look for the
   comparison you already have before building one.
5. **Excluding a mechanism beats doubting it.** The muted-while-stopped policy was a fix,
   but its real value was epistemic: it made the DAC *provably* muted at a transient that
   popped anyway, which converts "the mute probably doesn't help" into "the mute
   demonstrably doesn't."
6. **Tabulate before you reason forward from the newest datapoint.** Wrong claim #4 —
   that amp gating could also be retired — followed plausibly from the latest
   observation and collapsed instantly against the whole table, which showed amp gating
   was the only mechanism ever observed *in position* at a transient that didn't pop.
7. **Prefer asking the hardware to enumerating call sites.** Both fixes that held —
   `spk->is_running()` for the chimes, muted-while-stopped for the DAC — replaced a list
   of remembered cases with a direct question, and both then covered cases nobody had
   listed.
8. **An active-low signal behind `inverted: true` will invert your mental model too.**
   Write the real timeline out in milliseconds before trusting any reasoning about it.
9. **A fix that succeeds wrongly is worse than one that stops.** The accepted ~50 ms soft
   start is disclosed and adjustable; the hazard whose symptom is a clipped syllable is
   written down precisely *because* it would present as a TTS bug. Silence about a
   known cost is how the next person loses a week.
