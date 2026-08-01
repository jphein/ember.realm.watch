# Wake word — "don-kee"

Status: **wired, compiled, not flashed, and off by default.**

Ember answers to a tap today. This document describes how it also answers to
"don-kee", why that wake word runs in Home Assistant rather than on the ESP32, and
what is left to do.

---

## The short version

| | |
|---|---|
| Model | `donk_ee.tflite`, openWakeWord format ([provenance + hash](../homeassistant/wakewords/README.md)) |
| Runs on | Home Assistant (`openwakeword` add-on), **not** on the device |
| Device's job | Stream microphone audio to HA whenever it is idle |
| Enable with | `wake_word_enabled: "1"` in `esphome/ember-satellite.yaml` substitutions |
| Default | `"0"` — off. Touch-only, exactly as before. |
| Remaining | Flash the device; set the `familiar-ember` pipeline's wake word; restart HA |

## Why server-side, when on-device would be better

On-device (`micro_wake_word`) is the better architecture and it is not available to us.

The only surviving "don-kee" artifact is an **openWakeWord** model. That was verified
by parsing the model rather than by trusting where it sat on disk — input tensor
`[1, 16, 96]` float32, which is openWakeWord's classifier head over its shared
embedding frontend. ESPHome's `micro_wake_word` component implements a *different*
frontend and needs an int8, self-contained microWakeWord model with a JSON manifest.

The formats are not interconvertible. Getting "don-kee" on-device means **retraining**
it, which is a real but separate piece of work. The full reasoning, and the trail of
the microWakeWord "donkee" that used to exist and has been lost, is in
[`homeassistant/wakewords/README.md`](../homeassistant/wakewords/README.md).

### The tradeoff you are accepting

| | On-device (not available) | Server-side (what this is) |
|---|---|---|
| Idle network | silent | **continuous 16 kHz audio to HA** |
| Detection latency | ~0, local | one WiFi hop + HA inference |
| Works if HA is down | yes | no |
| Privacy posture | audio leaves only after the word | **all room audio leaves, always** |

That last row is the reason this ships **off**. Turning it on is a decision about what
the microphone does when nobody is talking to it, not a feature toggle.

---

## How it is wired on the device

Four small pieces in `esphome/ember-satellite.yaml`, all inert while
`wake_word_enabled` is `"0"`:

1. **`wake_word_arm` script** — sets `use_wake_word` true and starts a continuous
   listen, but only if the assistant is not already running.
2. **`api: on_client_connected:`** — arms it once HA is actually connected. Arming in
   `on_boot` would race the WiFi/API handshake and lose.
3. **Touch path (`talk_begin`)** — clears `use_wake_word`, stops the continuous listen,
   waits for IDLE, then starts the conversation.
4. **`on_end` / `on_error`** — re-arm.

### Two traps this wiring exists to avoid

Both are silent — neither shows up in `esphome config`, and neither logs an error.

**`use_wake_word` is a flag, not a mode.** `voice_assistant.cpp:336` stamps it onto
*every* pipeline-start request:

```cpp
if (!this->continue_conversation_ && this->use_wake_word_)
    flags |= VOICE_ASSISTANT_REQUEST_USE_WAKE_WORD;
```

There is no test for whether this start came from the wake word or from a finger. So
the obvious implementation — `use_wake_word: true` on the `voice_assistant:` block —
means **tapping the glass also starts at the wake-word stage**: you press it, and Ember
still waits for you to say "don-kee". The flag has to be cleared for the duration of a
touch conversation, which is why it is owned by a script instead of set in config.

**`request_start` silently does nothing unless the assistant is IDLE**
(`voice_assistant.cpp:682`). While armed, the assistant is *never* idle — it is sitting
in a continuous listen. A tap that just called `voice_assistant.start` would be dropped
on the floor: no error, no log, a screen that never starts listening. Hence the
stop-and-wait before the start.

Both failures look like "the touchscreen is flaky", which is the worst possible
presentation for a bug whose cause is three files away.

---

## How it is wired in Home Assistant

The model is already installed and already loaded. HA's openWakeWord engine offers it:

```
$ wake_word/info on wake_word.openwakeword
  okay_nabu · hey_jarvis · hey_mycroft · alexa · hey_rhasspy · donk_ee
```

What is **not** set is the wake word on Ember's pipeline. `familiar-ember` has
`wake_word_entity: wake_word.openwakeword` but `wake_word_id: null`, so no wake word is
selected. Compare `Gemini-vosk-piper-donkee`, which already uses `wake_word_id:
donk_ee` and is the working reference for this configuration.

Setting it requires **an HA core restart** to take effect — `assist_pipeline/pipeline/update`
writes to disk, but the in-memory pipeline runner caches the old configuration. This is
the same trap recorded for the STT engine swap during the M5Stack latency work.

---

## Remaining steps

1. `wake_word_enabled: "1"` in the substitutions block.
2. Compile and flash with JP present (`esphome run ember-satellite.yaml`).
3. Set `familiar-ember`'s `wake_word_id` to `donk_ee`.
4. Restart HA core.
5. Say "don-kee".

Tuning, once it runs: openWakeWord sensitivity lives in the add-on's `threshold`
option, not in the model. The microWakeWord tuning note in project memory
(`probability_cutoff` 0.73 → 0.60) belongs to the *other*, lost model and does not
apply here.

---

## The unavailable `wake_word` selects — not a regression

`select.ember_satellite_wake_word` and `..._wake_word_2` report `unavailable` with
`options: ['no_wake_word']`. That is correct and expected, and **enabling the wake word
as described here will not change it.**

Those selects are HA's picker for **on-device** (`micro_wake_word`) models. They are
populated from the device's model list, which ESPHome exposes only from the
`micro_wake_word` component (`micro_wake_word.h:79`, `get_wake_words()`). Ember has no
such component, so the list is empty, the options degenerate to the `no_wake_word`
placeholder, and the entity has nothing to be available *for*.

The controlled comparison, both read live:

```
select.ember_satellite_wake_word          state=unavailable    options=['no_wake_word']
select.m5stack_..._wake_word              state=no_wake_word   options=['no_wake_word','Okay Nabu','donkee']
```

The M5Stack has `micro_wake_word` and its selects work. Ember does not and its do not.

They are also **not stale entities from an older wake-word firmware** — the HA entity
registry created them on 2026-07-29, during the recent flashing work, and
`ember-satellite.yaml` has never contained a `micro_wake_word:` block in its git
history. They are placeholders HA creates for any voice-assistant device, empty because
this device has no on-device models.

They will populate only if "don-kee" is retrained as a microWakeWord model.
