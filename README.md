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

### `m5stack-atom-echo-a14320.yaml`

The older voice satellite. Verified to compile clean against ESPHome 2026.7.2
with no deprecation warnings (RAM 30.5%, Flash 83.2% — note the flash headroom
is tight).
