# ESPHome device configs

Version-controlled copies of the ESPHome configs that run on the HA VM at
`/config/esphome/`. Until now those existed as a single copy on the VM with no
history — this directory is the backup.

## Workflow

Compile locally (about 5x faster than building on the HA VM):

```bash
cd ~/Projects/ha/scratch
cp ~/Projects/ha/esphome/<device>.yaml .
esphome compile <device>.yaml
esphome upload <device>.yaml --device <device>.lan     # OTA
esphome logs   <device>.yaml --device <device>.lan
```

`secrets.yaml` is deliberately not tracked. Refresh it with:

```bash
ssh jp@10.0.6.108 "cat /config/esphome/secrets.yaml" > ~/Projects/ha/scratch/secrets.yaml
```

> **`esphome upload` does NOT compile.** It ships whatever is already in
> `.esphome/build/`, silently. Always run `esphome compile` first, or use
> `esphome run`. Two debugging rounds were lost to flashing a stale binary
> whose symptoms reproduced to the millisecond.

## Devices

### `ember-satellite.yaml`

Voice satellite on an **LCDWIKI/QDtech ES3C28P** (sold as "Hosyond 2.8in
ESP32-S3 Touchscreen"): ESP32-S3 N16R8, 240x320 ILI9341V, FT6336G capacitive
touch, ES8311 codec with analog mic and external speaker, microSD, WS2812.

Talks to the `familiar-ember` Assist pipeline — vosk STT, a local
Qwen3.6-35B-A3B conversation agent, and Piper `en_GB-cori-medium` TTS.
Activation is by touching the screen; there is no wake word.

The screen is a hearth: one fire whose temperature tracks the assistant state,
drawn with a banded partial-redraw scheduler so the animation runs at ~18fps
without starving the voice stream.

**The pinout is traced to the manufacturer's schematic, not to community
tables.** Several published tables for this board are wrong, and the file
carries comments explaining each non-obvious choice. The ones that cost real
debugging time:

| Setting | Why it looks wrong but isn't |
|---|---|
| `i2s_din_pin: 6` / `i2s_dout_pin: 8` | The silkscreen names I2S data pins from the *codec's* perspective, so most published tables are inverted. Confirmed four ways, including the vendor's own shipped source. |
| `use_microphone:` omitted | In ESPHome's es8311 driver that flag enables a *PDM digital* mic. This board's mic is analog-differential into MIC1P/MIC1N. |
| `data_rate: 40MHz` | `mipi_spi`'s base ILI9341 model declares no data rate, so it defaults to **10MHz** — which made full frames take 141ms instead of 60ms. |
| GPIO18 left unconfigured | It's CTP_RST. Both a `reset_pin:` and a gpio `output:` broke touch init — ESPHome's `ft63x6` asserts reset then reads the chip ID with zero delay, ignoring the datasheet's `Trsi >= 300ms`. The FT6336G has a 3k internal pull-up, so leaving it alone is correct. |
| `bits_per_sample: 16bit` on the mic | ESPHome's default is **32bit**, which silently mismatches the 16-bit codec and produces a dead mic. This is the actual bug in the only other published config for this board. |
| `channel: left` | Cosmetic. ES8311 REG 0x44 defaults to "ADC + ADC", duplicating the mono ADC into both slots, and no driver writes that register — so left and right are equivalent here. |

Calibration knobs that are guesses until measured on your hardware are marked
in-file: `db_floor`/`db_ceil`, `tts_ms_per_char`, `cpl_body`/`cpl_sm`.

#### Chimes

`sounds/` holds six 16kHz mono tones plus `generate_chimes.py`, which produced
them. Struck-glass synthesis — inharmonic partials, exponential decay, 4ms
raised-cosine attack, warm F-pentatonic so any two are consonant. `error` is the
one deliberate dissonance. 16kHz keeps every partial under Nyquist, so nothing
resamples on the way to the codec.

Four fire: `announce`, `error`, `done`, `timer`. `thinking` is a switch, default
off. **`chime_listening` is generated but deliberately never declared** — 1.4s of
tone out of a speaker sharing one I2S hub with the mic, no AEC, would make HA's
VAD end the utterance before you spoke. The symptom would read as an STT bug.
Don't wire it; the reasoning is at the point of use in the YAML.

#### ⚠️ Partly fixed: an audible pop on some audio starts

**The codec cannot fix all of it, and this is a mechanism limit rather than a
tuning problem.** `use_mclk: true`, and MCLK is only driven while an I2S channel
is loaded — so when *both* the speaker and the microphone are unloaded, MCLK
stops entirely. The ES8311 is fully clock-dependent, and **REG31 mute is enforced
inside that same clock domain**. It therefore cannot hold the analog output
across an MCLK stop/start, because during the transition there is no clock with
which to enforce it. No anchor, no poll period and no earlier hook changes that.

| transient | fixable by muting the codec? |
|---|---|
| Speaker start, MCLK already up | **Yes** — REG31 inside the 50ms preloaded-silence window (shipped) |
| MCLK cold start (both unloaded → first load) | **No.** Only the amp is downstream of it |
| Mic-side start (e.g. tap to talk) | **No** — same reason |
| Failed starts (`Parent bus is busy`) | **Nothing to suppress** — see below |
| The amp's own enable click | Unmeasured |

**Failed starts are not a pop source**, despite looking like the obvious suspect.
`Parent bus is busy` is the `try_lock()` failure at
`i2s_audio_speaker_standard.cpp:400-403`, which returns `ESP_ERR_INVALID_STATE`
**before `i2s_new_channel()`** — before any DMA allocation or channel enable. A
failed start touches zero hardware; it costs latency and log noise only. (An
earlier revision of this file claimed otherwise. It was wrong.)

The only remaining lever for the clock-cold-start pop is gating the **SC8002B**
amp on GPIO1. `amp_blank_ms` (default 180ms, set to `0` to disable) blanks the
amp across the microphone's clock start. That is an **experiment, not a
settled fix** — the amp has its own enable click, and a permanently-enabled BTL
amp is *why* this board has no idle hiss. Deliberately not applied to the speaker
path, so the two mechanisms stay separately measurable.

**Cheapest falsification if you doubt the mechanism:** turn `Hush` on and tap to
talk. Hush blocks `voice_assistant.start`, so no clock start occurs. If the pop
persists, the clock-domain explanation above is wrong.

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

### `m5stack-atom-echo-a14320.yaml`

The older voice satellite. Verified to compile clean against ESPHome 2026.7.2
with no deprecation warnings (RAM 30.5%, Flash 83.2% — note the flash headroom
is tight).
