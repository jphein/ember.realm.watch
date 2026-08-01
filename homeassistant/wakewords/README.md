# Wake-word models

## `donk_ee.tflite` — "don-kee"

JP's custom wake word. **openWakeWord format.** Runs in Home Assistant, not on the device.

| | |
|---|---|
| sha256 | `bcc3955cef2dcf358260773ea44e30c0ad2eef51e73ccd436013f0f8b05d98c0` |
| size | 206,748 bytes |
| engine | openWakeWord (HA `openwakeword` add-on) |
| wake word id | `donk_ee` (HA displays it as "Donk Ee") |
| installed at | `/share/openwakeword/donk_ee.tflite` on the HA VM (`ha.lan`) |
| mtime on HA | 2024-06-24 |

### Why this file is in git

It was found in exactly one place — `/share/openwakeword/` on the HA VM — with no
copy anywhere else on the network, no training repo, and no training data. It is a
custom-trained model that **cannot be regenerated**. A VM rebuild or a bad `rm` would
have destroyed it permanently. The copy here is byte-identical to the deployed one
(hash above verified against the live file, not assumed).

This is a backup and a provenance record. HA reads the copy in `/share`, not this one.

### How the format was determined (and why it matters)

Directory placement is not proof of format — both engines use `.tflite`. The model was
parsed with the TFLite schema:

```
INPUT   serving_default_onnx_tf__tf_Flatten_0_f362316c:0   [1, 16, 96]  float32
OUTPUT  PartitionedCall:0                                  [1, 1]       float32
```

`[1, 16, 96]` float32 is the **openWakeWord classifier head**: 16 frames of 96-dim
embeddings produced by openWakeWord's shared melspectrogram + embedding frontend. The
`onnx_tf__tf_Flatten` tensor name is openWakeWord's PyTorch → ONNX → TF export path.

**microWakeWord** — the format ESPHome's `micro_wake_word` component requires — is
different in kind: int8-quantized, self-contained, with its own streaming spectrogram
frontend and a JSON manifest carrying `micro.probability_cutoff`, `sliding_window_size`
and `tensor_arena_size`. Typical size ~40 KB, not ~200 KB.

The two are **not interconvertible**. There is no conversion script, because the
difference is the feature frontend and the training regime, not the serialization.
Putting this file in an ESPHome `micro_wake_word:` block will not work.

### If you want "don-kee" on-device one day

It has to be **retrained** as a microWakeWord model (the
[microWakeWord](https://github.com/kahrendt/microWakeWord) trainer generates samples
with a TTS piper voice — no original recordings needed). That would remove the
constant audio streaming described in `docs/wake-word.md` and is the better end state.
It is a training task, not a wiring task.

### Known loose end, not in this repo

The M5Stack ATOM Echo (`m5stack-atom-echo-a14320`) currently reports an **on-device**
wake word literally named `donkee` in HA:

```
select.m5stack_atom_echo_a14320_wake_word  options=['no_wake_word', 'Okay Nabu', 'donkee']
```

So a microWakeWord "donkee" model *did* exist — a project memory records tuning
`micro.probability_cutoff` in `wake_word_models/donkee.json` from 0.73 → 0.60 on
2026-05-14. That model and manifest are **gone**: not in `~/Projects/ha` (whose
committed `m5stack-atom-echo-a14320.yaml` lists only the three stock models), not in
`/config/esphome` on the HA VM, not in any ESPHome build cache, and not in any GitHub
repo. The live M5Stack firmware simply predates the current YAML and still carries it.

It survives only as flashed firmware on that device. **Do not reflash the M5Stack
without extracting it first** — that flash is the last copy.
