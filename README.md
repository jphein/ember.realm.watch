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

### `m5stack-atom-echo-a14320.yaml`

The older voice satellite. Verified to compile clean against ESPHome 2026.7.2
with no deprecation warnings (RAM 30.5%, Flash 83.2% — note the flash headroom
is tight).
