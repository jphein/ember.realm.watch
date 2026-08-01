# Assist pipeline snapshots

Assist pipelines are **not** YAML-configurable — they live in HA's `.storage` and are
edited through the UI or the `assist_pipeline/pipeline/*` websocket API. Nothing here
is deployed; these are read-back snapshots so the settings are reviewable in a diff and
restorable if `.storage` is lost.

## `familiar-ember.json`

Ember's pipeline. Captured live on 2026-07-31 after setting the wake word.

- `wake_word_id: donk_ee` — set in this branch (was `null`). See [`docs/wake-word.md`](../../docs/wake-word.md).
- `stt.vosk` — true-streaming STT, chosen because it collapses STT_VAD_END → result
  from ~6.5 s to ~0 ms versus faster_whisper.
- `prefer_local_intents: true` — HA answers what it can without the LLM.

⚠️ Editing a pipeline writes to disk immediately but the **in-memory runner caches the
old configuration** — an HA core restart is required before a change takes effect. That
applies to the `wake_word_id` set here: it is written but not yet live.

To re-read the current state:

```bash
# wss://ha.jphe.in/api/websocket → auth → {"type": "assist_pipeline/pipeline/list"}
```
