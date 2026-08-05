# Intercom relay between the hearths — design

**Date:** 2026-08-05 · **Status:** approved · **Scope:** v1, spoken relay only

Speak into either Ember and have the other hearth (or both) say the message aloud.
Firmware untouched; everything rides the existing announce chain
(`script.ember_announce` / `script.ember_announce_all`, `preannounce: false` pinned).

Live two-way audio (walkie-talkie / drop-in) is **out of scope** and deferred to a
GitHub issue capturing the research: community projects stream raw PCM over UDP
(fallingaway24/esphome-2Way-INTERCOM, samuelthng/intercom-api, n-IA-hane/esphome-intercom),
none document coexistence with `voice_assistant` + `micro_wake_word` on a shared I2S
bus, AEC costs ~22% CPU via ESP-SR, and Ember's I2S arbiter is a known do-not-touch
zone. That is a firmware project, not an easy add.

## Two paths, layered

### Path 1 — built-in `HassBroadcast` (verify + document, no code)

HA 2026.7.4 ships the `HassBroadcast` intent, and the pipeline's
`prefer_local_intents: true` routes *"broadcast/announce [that] {message}"* to it
**before** the LLM. The core handler announces to every satellite *except* the one
that heard the command — with exactly two Embers, "broadcast X" is exactly "tell the
other hearth X". Because it is a local intent, it keeps working when `familiar` is
asleep.

Work: verify end-to-end (API test against the default agent with the desk unit's
`device_id`, then a real spoken test), then document in `docs/home-assistant.md`.

**Known blemish, documented rather than fixed:** the core handler passes no
`preannounce`, so the default (`true`) applies — this path plays HA's generic blip
*and* Ember's local chime, the double herald `script.ember_announce` exists to
suppress. Fixing it would mean shadowing a built-in intent with custom sentences +
`intent_script` (a new deploy surface, no source-device exclusion, registration-order
fragility) for a cosmetic gain. Declined.

### Path 2 — `send_word` tool (the polished directed channel)

One new script-type entry in `homeassistant/functions/ember-functions.yaml`,
following the `palace_recall` / `look_at_camera` pattern. Deployed with
`ember-toolkit.py --deploy`; costs one cold prefill, by design. No prompt edit —
the tool description carries the knowledge.

- **Spec:** `send_word(target: desk|mobile|both, message: string)`, both required.
  Description written as a trigger: use when JP says tell / let know / send word /
  relay a message to the desk, the mobile, or both hearths.
- **Target mapping:** `desk → assist_satellite.ember_satellite_assist_satellite`,
  `mobile → assist_satellite.ember_mobile_assist_satellite`, `both →
  script.ember_announce_all`.
- **Availability pre-check:** for a single target whose satellite state is
  `unavailable`/`unknown`, return `hearth_unreachable=<target>` without attempting —
  the mobile unit may be off, flat, or in a drawer, and a tool must say so rather
  than fail mid-turn. For `both`, always dispatch (`ember_announce_all` is
  `parallel:` with `continue_on_error` per branch) and append
  `hearth_unreachable=<name>` for any satellite currently unavailable, so the reply
  is honest about partial delivery.
- **Fire-and-forget dispatch** via `script.turn_on` with `data.variables`, never a
  direct blocking call: `assist_satellite.announce` blocks until playback completes
  and has a documented 2.5-minute wedge precedent (`ember_announce.yaml` header). A
  hung delivery must not hold Ember's voice turn hostage. Result is dispatch, not
  delivery: `sent=<target>` in `key=value` house style.
- **Chime discipline inherited:** everything lands in `script.ember_announce`, which
  pins `preannounce: false` — single F-pentatonic herald on this path.
- **Quiet hours deliberately bypassed** (no `script.ember_broadcast` hop): a person
  speaking through Ember *is* the editorial decision; quiet-hours → Slack routing
  exists for automated events. Recorded as a comment on the tool.

## Error handling

| Failure | Behaviour |
|:--|:--|
| Mobile off / flat | pre-check catches it; Ember says the hearth is unreachable |
| `familiar` asleep | only affects Path 2, which requires a conversation anyway; Path 1 unaffected |
| Self-target (telling the desk *from* the desk) | speaks on the box in front of you — harmless echo, accepted in v1 |
| Wedged satellite | fire-and-forget means the turn completes; the message may be lost, and `sent=` honestly claims dispatch only |

During implementation, check the VM's EOC v3 source
(`/config/custom_components/extended_openai_conversation/`) for whether script-type
functions can see `device_id`. If they can, a future `other` target becomes possible;
v1 ships explicit targets only.

## Verification

1. `ember-toolkit.py --diff` → `--deploy --dry-run` → `--deploy`.
2. Through the real conversation API (§9.4: a tool that parses is not a tool that
   answers): *"Tell the desk this is a test"*, *"send word to both hearths that…"*.
3. Built-in path: *"broadcast that dinner is ready"* via the default agent with a
   satellite `device_id`, then spoken on-device.
4. Delivery measured, not assumed: `sensor.ember_*_speaker_frames` climbs at
   16000/s on the receiving unit.
5. Unavailable-target test with the mobile unit powered off →
   `hearth_unreachable=mobile`.

## Deliverables

- `homeassistant/functions/ember-functions.yaml` — the `send_word` tool.
- `docs/home-assistant.md` — §9.2 table row + a short intercom subsection covering
  both paths and the Path-1 double-herald note.
- GitHub issue: live-audio intercom research capture.
