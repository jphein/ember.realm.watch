# Intercom Button (The Horn) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A horn glyph in the bottom-right of each Ember's screen; press → speak → your words come out of the other hearth via the normal STT→TTS pipeline.

**Architecture:** Firmware adds only a touch target + glyph + an `event` entity — HA drives the listen session via `assist_satellite.ask_question` (probed live: returns raw STT `sentence`) and relays through `script.ember_announce`. Spec: `docs/superpowers/specs/2026-08-05-intercom-button-design.md`.

**Tech Stack:** ESPHome 2026.7.3 (shared config + two wrappers), HA 2026.7.4 packages, `deploy-ha.sh`, `ember-toolkit` not involved.

**Executor ground rules:** compile before any upload (`esphome upload` ships stale builds); OTA by name (`--device ember-satellite.local` / `ember-mobile.local`); the branch is `feat/intercom-button`.

---

### Task 1: Firmware — substitutions, global, event entity

**Files:** Modify `esphome/ember-satellite.yaml`

- [ ] Add to the overlay-geometry substitutions block (after `ui_pm_timeout`): `ui_ic_x: "192"`, `ui_ic_y: "264"` with a comment tying them to the telemetry band and the hit-test/draw pairing rule.
- [ ] Add global `ic_ms` (uint32, initial `0`) next to `spark_ms` — the glyph-flash timestamp.
- [ ] Add a top-level `event:` component above `globals:`: platform template, `id: intercom_evt`, name `Intercom`, `event_types: ["pressed"]`, icon `mdi:bugle`, with a comment explaining why an event entity (no HA-actions permission; entity identity = source identity).
- [ ] `esphome compile ember-satellite.yaml` — expect success.

### Task 2: Firmware — hit-test, dispatch, glyph

**Files:** Modify `esphome/ember-satellite.yaml`

- [ ] In `on_touch`, normal-mode path: after the unread-clear, before `ui_action = 3`, add the corner test (`tx >= ${ui_ic_x} && ty >= ${ui_ic_y}` → `ui_action = 16`, stamp `ic_ms`, `return` — no coal strike, comment says why). Amend the "RESOLVING THE TOUCH-TO-TALK CONFLICT" comment with the dated exception.
- [ ] In `ui_dispatch`: add the action-16 block (idle gate `va_state == 0 || == 4`, then `event.trigger` type `pressed`). Standard haptic applies (do not add 16 to the exemption list).
- [ ] In the display lambda, telemetry band, after the house row: draw the horn glyph in the right block when `ui_mode == 0` — dim amber at rest, gold for 400 ms after `ic_ms` (flash = press feedback).
- [ ] `esphome compile ember-satellite.yaml` && `esphome compile ember-mobile.yaml` — both succeed.
- [ ] Run `esphome/tools/check_navigability.py` (and any check that fails, fix before continuing).
- [ ] Commit: `feat(display): the horn — an intercom button in the telemetry band`.

### Task 3: HA — the relay package

**Files:** Create `homeassistant/packages/ember_intercom.yaml`; modify `homeassistant/tools/deploy-ha.sh` (PACKAGES array + reload map)

- [ ] Write the package: one `mode: restart` automation per the spec (boot-flap guard on from/to state; peer-dark short-circuit; `ask_question` with `continue_on_error` + `response_variable`; fire-and-forget relay / nothing-to-carry via `script.turn_on`). Comments carry the design reasoning.
- [ ] Add `ember_intercom` to `PACKAGES` and `automation` to the reload mapping in `deploy-ha.sh` — same commit.
- [ ] `deploy-ha.sh --check`, then `--dry-run`, then `deploy-ha.sh ember_intercom`.
- [ ] Commit: `feat(ha): ember_intercom — the horn's relay automation`.

### Task 4: OTA both boards

- [ ] `esphome upload ember-satellite.yaml --device ember-satellite.local`
- [ ] `esphome upload ember-mobile.yaml --device ember-mobile.local`
- [ ] Confirm both event entities exist in HA (`event.ember_satellite_intercom`, `event.ember_mobile_intercom`) and are not `unavailable`.

### Task 5: Live verification (with JP)

- [ ] Desk horn → speak → mobile relays (frames climb; single herald).
- [ ] Mobile horn → speak → desk relays.
- [ ] Silence test → "I heard nothing to carry." on the source.
- [ ] Mobile off → desk horn → "The mobile hearth is dark." (also closes PR #58's deferred unreachable test, via `send_word` if convenient).
- [ ] Overlay open → corner tap dismisses, no intercom fire.
- [ ] Docs: update `docs/home-assistant.md` §6.7 with the horn (and the observed herald notes); commit.

### Task 6: Ship

- [ ] Full-diff review + secrets grep; push; PR referencing #57 and the spec; merge; back to `main`.
