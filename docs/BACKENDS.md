# Backends: the outside sources Ember depends on

Required by the global rule "Backends grow continually" (JP 2026-10-27) and plan FOR-AGENTS rule 28 (2026-11-24: every
backend says whether it needs a token, and what would remove it). Statuses were read on **2026-11-24** unless noted.
This repo is public: no addresses or secret names beyond what CLAUDE.md already carries.

`Token` is `none`, `agent vault` (a key a lane holds in the vault) or `JP own` (works only under JP's login).
`Token-less by` names the row or plan that would remove the token, or `—` when there is none yet.

| Backend | How Ember reaches it | Token | Token-less by | Status 2026-11-24 | Notes |
|---|---|---|---|---|---|
| Home Assistant (packages, prompt, dashboards: `homeassistant/tools/deploy-ha.sh`) | REST/WS to the edge name, ssh to the HA VM for files | agent vault | — | live | token ladder: `HA_TOKEN` → `~/.cache/ha-token-tmp` → password manager |
| LiteLLM gateway (the conversation agent's model) | OpenAI-compatible API on ubox0:4000, from HA's conversation entry | agent vault | — | entry loaded (HA config entry `Ember (familiar local)`); no probe turn sent today, and a loaded entry is not a model answer | Ember's own key, held in HA's entry and the vault; the model behind it runs on familiar |
| The local model lane on familiar | behind LiteLLM; never called directly | none | — | not read today | owned by familiar.realm.watch, not mirrored here |
| Speech: STT, TTS, wake word (Wyoming, Piper, openWakeWord on familiar) | Wyoming over the LAN from HA | none | — | piper, openwakeword and onnx-asr entries loaded | the live voice is Piper `en_GB-cori-high` |
| ESPHome voice satellites (the hearths) | ESPHome native API from HA | agent vault | — | Ember Mobile idle (live); the desk unit unavailable since 11-21 (ha card a759c0456e5b, a power check) | per-device API encryption keys live in the ESPHome secrets on the HA VM |
| Slack (quiet-hours route of `script.ember_broadcast`) | HA's Slack notify service | agent vault | — | live: HA's Slack entry is loaded and `notify.the_homefront` is registered (its device reads "down" in the ha lane's link check only because its one sensor is unavailable; ha flow e163214f) | the token belongs to HA's Slack entry; the separate `slack_bridge` add-on is another path |
