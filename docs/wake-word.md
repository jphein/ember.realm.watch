# Wake word

Status: **flashed and heard.** Ember answers to **"Okay Nabu"**, detected on-device.

> This line read *"wired and compiled, never flashed"* until 2026-08-25, which was stale
> — the YAML's own substitution block records the flash: JP confirmed "Okay Nabu" on the
> desk unit 2026-08-03, and ember-mobile's first flash came up clean the same day. The
> desk unit was reflashed to main `558b01d` on 2026-08-25 (clean boot, safe_mode counter
> reset, no `Parent bus is busy` in the idle log). Mode 2 (don-kee) rides in every build
> and remains **never selected** — see "What #42 still awaits" below.

There are two wake-word implementations in this repo because there are two models in two
incompatible formats. One `wake_word_mode` substitution picks between them.

| mode | wake word | runs on | idle audio leaves the device | default |
|---|---|---|---|---|
| `0` | — | — | no | |
| `1` | **Okay Nabu** | the ESP32 (microWakeWord) | **no** | ✅ |
| `2` | don-kee | Home Assistant (openWakeWord) | **yes, continuously** | |

Set it in the substitutions block of `esphome/ember-satellite.yaml`.

---

## Why the wake word is "Okay Nabu" and not "don-kee"

Because of the model format, not preference.

The only surviving "don-kee" artifact is an **openWakeWord** model — verified by parsing
it: input `[1,16,96]` float32, openWakeWord's classifier head over its shared embedding
frontend. ESPHome's on-device `micro_wake_word` needs a **microWakeWord** model: int8,
self-contained, its own streaming frontend. They are not interconvertible, so "don-kee"
can only run server-side, and running it server-side means streaming room audio to HA
continuously while idle.

"Okay Nabu" is a stock microWakeWord model, so it runs locally and nothing leaves the
device until the word fires. Mode 1 is therefore strictly better on privacy and latency,
at the cost of the wake word being someone else's. Getting "don-kee" on-device requires
**retraining** it as a microWakeWord model — a training task, not a wiring task.

Provenance and hashes: [`esphome/wakewords/`](../esphome/wakewords/README.md) (on-device)
and [`homeassistant/wakewords/`](../homeassistant/wakewords/README.md) (server-side).

---

## ⚠️ The thing that makes mode 1 hard: one I2S bus

**A naively always-on `micro_wake_word:` makes Ember mute.** This is the single most
important fact about the on-device wake word on this board.

`micro_wake_word` holds the **microphone** open continuously. On this device the
microphone and the speaker are the same `i2s_bus`, behind **one mutex**:

- the mic takes it in `start_driver_()` and returns it only in `stop_driver_()`
  (`i2s_audio_microphone.cpp:98, 228`) — its entire running life;
- the speaker asks with a **non-blocking `try_lock()`**, logs `Parent bus is busy`
  (`i2s_audio_speaker_standard.cpp:400`) and gives up, retrying a second later, forever.

So while the wake word listens, every reply, chime and announcement silently fails to
get the bus. This is the exact mirror of the `timeout: never` trap already documented on
the speaker in the YAML — that one starves the microphone, this one starves the speaker.
One mutex, two directions, both silent.

### What makes it safe: the arbiter

A 100 ms loop in `interval:` (search **WAKE-WORD ARBITER**) owns the rule *"the wake word
may hold the mic only while nothing wants to speak and no conversation is running"*:

```
want = (mode == 1) && spk->is_stopped() && !va->is_running()
```

It keys on `is_stopped()`, **not** `is_running()`. `is_running()` means
`state_ == STATE_RUNNING`, which the speaker only reaches *after* winning the lock —
which it cannot do while we hold it. Keying on it would deadlock on a state our own
behaviour prevents. `is_stopped()` goes false at `STATE_STARTING`: the moment the
speaker *wants* the bus, before it asks.

Two predictive anchors yield the mic ahead of time, to shorten the window in which the
speaker asks for a bus the wake word still holds:

- **`talk_begin`** — the conversation entry point, for the touch path.
- **`media_player: on_announcement:`** — for pushed audio (HA announcements, finished
  timers) where there is no tap to hang the yield on.

The touch yield is deliberately **not** in `ui_dispatch`, which looks like the better
choke point because every touch target converges there. That is exactly the problem: it
includes *pure navigation*, so yielding there makes cursor moves and menu dismissals stop
the wake word. `check_navigability.py` measures the cost precisely — clean button-only
exits drop from 11 to 1 — and it rejected that placement during this work. Menu
navigation must not make Ember deaf.

⚠️ **The yield is not instantaneous.** `mww->stop()` unwinds through the wake-word task,
which calls `microphone_source_->stop()` on its own schedule
(`micro_wake_word.cpp:216`), so the I2S lock returns some time after the action rather
than at it. If the speaker asks before then it still eats the 1 s backoff. These anchors
shorten the window; they do not close it. **Whether the touch chime is audibly late is an
open question for the first flash** — see the symptom table at the bottom.

`on_announcement` is deliberately reused here even though the DAC-unmute manager
explicitly *rejected* it. That rejection is still correct: it fires before the speaker
starts, so unmuting there lands ahead of the clock transient and the pop survives. The
same early timing is precisely what a bus hand-off needs. Same trigger, opposite
requirement — do not unify them.

`stop_after_detection` (default true) covers the wake path itself: the mic is dropped
the instant the word fires, in time for the listening chime.

---

## What changes for the touch path

The two traps documented for **server-side** wake word in
[#42](https://github.com/jphein/ember.realm.watch/issues/42) **do not apply to mode 1**,
and it is worth being explicit because the fixes look transferable and are not:

| | mode 2 (server) | mode 1 (on-device) |
|---|---|---|
| `use_wake_word` stamped on every pipeline start | **yes** — a tap would demand the phrase, so the flag is toggled around each conversation | **not used at all** |
| `request_start()` no-ops unless IDLE | **yes** — an armed assistant is never IDLE, so a tap is dropped silently | **no** — `micro_wake_word` is a separate component; the assistant *is* IDLE while it listens, so `voice_assistant.start` works normally |
| contention introduced | network (continuous streaming) | **I2S bus** (the arbiter above) |

So mode 1 needs no arm/re-arm scripts around the assistant. It needs bus arbitration
instead. Different failure surface entirely.

Both wake-word entries reuse **`talk_begin`**, the single conversation entry point, which
already waits for `spk->is_stopped()` before opening the mic. Its long-standing
FORWARD COMPATIBILITY note — that an on-device wake word needs no operating-mode gate,
because hush means "do not make noise", not "do not listen" — is now load-bearing rather
than hypothetical.

---

## The wake-word selects come alive

`select.ember_satellite_wake_word` and `..._wake_word_2` have been `unavailable` with
options `['no_wake_word']` for this device's entire life. **This change is what populates
them**, and they will list "Okay Nabu".

They were never broken. They are HA's picker for *on-device* models, fed from
`micro_wake_word`'s model list (`micro_wake_word.h:79`, `get_wake_words()`), and the
device had no such component — so the list was empty and the entity had nothing to be
available for. (Ember was otherwise fully online the whole time: 23 of 25 entities live,
with only these two dead.)

⚠️ **They populate in every mode, including 0 and 2.** The enumeration is static
configuration and knows nothing about `wake_word_mode`, so at mode 0 or 2 HA will offer a
wake word that is never armed and selecting it will appear to do nothing. That is a
cosmetic inaccuracy HA gives us for free; it is recorded rather than papered over.

Selecting a wake word in HA calls `on_set_configuration`, which enables/disables models
on the device (`voice_assistant.cpp:1084`). With one model installed, the meaningful
choices are "Okay Nabu" and `no_wake_word`.

---

## Home Assistant side

Ember's pipeline is `familiar-ember`. Its `wake_word_id` is set to `donk_ee`, which
matters **only in mode 2** — in mode 1 detection never reaches HA's wake-word stage, so
the setting sits unused and harmless.

Snapshot: [`homeassistant/pipelines/familiar-ember.json`](../homeassistant/pipelines/familiar-ember.json).
Note that pipeline edits need an HA core restart to take effect.

---

## What #42 still awaits (all JP's, none of it firmware)

The don-kee wiring is on both boards — it ships in every build, inert at mode 1. For it
to actually answer to "don-kee", three things remain, and none is a repo change:

1. **`wake_word_mode: "2"` + reflash** — the privacy decision (idle 16 kHz audio streams
   to HA continuously). It also gives up mode 1's on-device advantage, so it is a real
   trade, not an upgrade.
2. **An HA core restart** — the `familiar-ember` pipeline's `wake_word_id: donk_ee` was
   written 2026-07-31 and the runner caches the old config until restart.
3. **Tuning the openWakeWord add-on `threshold`** — the 0.60 `probability_cutoff` in
   project memory belongs to the *lost* microWakeWord "donkee", not this model.

---

## Flashing this, and what to listen for

Flash with the device in reach. ~~The arbiter has never been heard~~ — retired
2026-08-03: JP confirmed "Okay Nabu" on the desk unit and ember-mobile's first flash ran
wake word → STREAMING_MICROPHONE → STT with no bus errors. The symptom table below stays
as the diagnostic reference for any future regression.

Good: Ember chimes on a tap with no delay, replies audibly, and answers to "Okay Nabu".

Bad, and what it means:

| symptom | cause |
|---|---|
| silent — no chimes, no replies; log repeats `Parent bus is busy` / `Driver failed to start; retrying in 1 second` | the arbiter is not yielding the bus |
| chimes and replies arrive ~1 s late | the arbiter works but a predictive anchor is missing for that path |
| never wakes, but audio is fine | mic never armed — check the select is not `no_wake_word` |
| wakes at random speech | tune `probability_cutoff`, or add the VAD gate (deliberately omitted) |

**Revert is one character:** `wake_word_mode: "0"` and reflash restores today's exact
behaviour.
