# On-device wake-word models (microWakeWord)

Models here run **on the ESP32**, via the `micro_wake_word:` block in
`ember-satellite.yaml`. They are a different format from the openWakeWord model in
[`homeassistant/wakewords/`](../../homeassistant/wakewords/README.md), which runs in
Home Assistant — see [`docs/wake-word.md`](../../docs/wake-word.md) for why both exist.

## `okay_nabu` — stock microWakeWord model

| | |
|---|---|
| wake word | "Okay Nabu" |
| author | Kevin Ahrendt (upstream ESPHome model) |
| manifest version | 2 |
| `probability_cutoff` | 0.97 |
| `tensor_arena_size` | 26,080 bytes |
| `feature_step_size` | 10 ms |

### Provenance

Source repository: <https://github.com/esphome/micro-wake-word-models>

Pinned to commit **`05b65922cc433c9df13e98e32a7fe520758c837e`**, files
`models/v2/okay_nabu.json` and `models/v2/okay_nabu.tflite`:

```
6dd65604f70fe5ea9d1af73a7bf239529d1fbabc363807f45d2b22ce464ddbed  okay_nabu.json
0689abe1912a95a3318a0d8cb2e67bad0cbcfe3e24dd6e050c75debddfb6f891  okay_nabu.tflite
```

**Independently cross-checked.** The vendored `.tflite` is byte-identical to the copy
ESPHome downloaded on its own, at a different time and through its own code path, into
its build cache. Two independent fetches agreeing is stronger evidence than one
download and a hash of itself.

### Why vendored instead of `model: okay_nabu`

The bare shorthand is convenient and resolves to:

```
https://github.com/esphome/micro-wake-word-models/raw/main/models/v2/okay_nabu.json
```

Note `main` — an unpinned, moving branch, fetched over the network at build time.
That makes the firmware non-reproducible (a future build can silently get a different
model) and unbuildable offline. This repo keeps artifacts with their provenance, so the
model is committed and referenced by local path. The pinned commit above is the exact
upstream state it came from.

ESPHome resolves the `.tflite` **relative to the manifest**, so the two files must stay
side by side; the path never appears in the YAML.

### Format note

60,264 bytes and int8-quantized, versus 206,748 bytes and float32 for the openWakeWord
`donk_ee.tflite`. That size and dtype gap is the practical signature of the two formats
and is consistent with the tensor-level analysis recorded in issue #42.

### Updating

Re-pin deliberately: pick a new upstream commit, download both files at that commit,
update the hashes and the commit above, and recompile. Do not repoint the YAML at the
`main` shorthand to "keep it fresh" — that trades reproducibility for nothing.
