# Parakeet ears — the STT swap, and the tap that lets JP hear what Ember hears

**Date:** 2026-08-09 · **Status:** live · Phase 1 of the mic/STT improvement effort

## The symptoms (JP, 2026-08-09)

1. **Transcripts are just wrong** ← this phase
2. Can't hear across the room ← phase 2 (mic gain calibration, live session)
3. Cuts off mid-sentence ← partially this phase (`--endpoint-ms 800`), rest in phase 2/3
4. Misses the first word ← phase 3 (wake-word handoff; audio never captured — no STT can fix that)
5. *(added mid-flight)* Says it did things it didn't ← separate investigation, agent layer, task #8

## What changed

| | before | after |
|---|---|---|
| Engine | `stt.vosk` (HA add-on, Kaldi-era) | `stt.onnx_asr` — **NVIDIA parakeet-tdt-0.6b-v2** |
| Where | HA VM | `familiar`, 8 CPU threads, GPUs untouched |
| Bridge | — | [`wyoming-onnx-asr`](https://github.com/chiabre/wyoming-onnx-asr) at `familiar:10300` |
| End-of-speech | HA default | server-side silero VAD, `--endpoint-ms 800` (was 500) for JP's pause tolerance |

Vosk was the best of what JP tested *inside local HA* — the finding is that add-ons
were the wrong pond. Parakeet-TDT tops the open English leaderboards in 2026 and the
ONNX build runs realtime-class on CPU. English-only v2 chosen over multilingual v3.

**Ownership**: unit + patch live in **familiar.realm.watch** (`ops/systemd/units/
wyoming-onnx-asr.service`, `ops/patches/wyoming-onnx-asr-save-audio.patch`) — the
qwen3-coder boundary, cross-referenced never mirrored. This repo owns the pipeline
snapshot + docs.

## The audio tap (JP: "where can I listen to what ember hears?")

Nowhere existed: the satellite has no storage, HA keeps no pipeline audio. The
Wyoming server is the perfect tap point — byte-for-byte what HA forwarded from the
mic, i.e. exactly what the model transcribed. The upstream clone is patched:
`--save-audio /opt/wyoming-onnx-asr/debug-audio` writes `utt-<ts>.wav` + a `.txt`
sidecar with the transcript, newest 40 kept, short-ignored segments included (those
are the first-word diagnostics). A wrong transcript can now be replayed against the
audio that produced it — which is also the instrument phase 2's gain calibration
needs.

Patch-vs-upstream hazard is made LOUD: a `git pull` in the clone drops the flag and
the unit fails on an unknown argument rather than silently losing the tap.

## Verified

- Round trip, piper-voiced test sentence → **"Turn off the laundry minisplit and
  check the pumph house floor heating."** One split compound ("pumphouse"); the
  realm word "minisplit" — Vosk's exact failure class — came through clean.
- The tap captured that utterance, wav + sidecar.
- Wyoming integration `onnx-asr` created; `familiar-ember` pipeline updated
  (`stt.vosk` → `stt.onnx_asr`), all other stages untouched.
- The log's `infer=0.000s` is upstream instrumentation timing a lazy generator, not
  reality; felt latency is sub-second on this box.

## The real test

JP talking to the mobile hearth (desk unit is unplugged). "Heard" line on the glass
shows the transcript; the tap shows what it heard. Vosk remains installed as an
inert fallback engine — flip the pipeline's STT back if familiar is ever down.
