# The horn — an intercom button on the hearth — design

**Date:** 2026-08-05 · **Status:** approved (JP: "do it all") · **Scope:** v1, STT→TTS relay

Tap a horn glyph in the bottom-right of either Ember's screen → that Ember says
*"Send word."* and listens → the words are transcribed by the pipeline's normal STT
(vosk) → the **other** hearth speaks *"Word from the desk hearth: 〈words〉"* through
`script.ember_announce` (single herald). No LLM in the chain: **the intercom works
while `familiar` sleeps.** Live streaming of the actual voice remains
[#57](https://github.com/jphein/ember.realm.watch/issues/57).

## The primitive, verified before design

`assist_satellite.ask_question` with `answers` omitted returns
`{id: null, sentence: <raw STT text>}` (core `entity.py`: on no answer list it
returns the raw response text). **Probed live 2026-08-05 on the desk unit, HA
2026.7.4 / ESPHome 2026.7.3: the device spoke the question, listened, and returned
`sentence: "huh"`.** This is what lets the firmware stay a dumb button: HA drives
the listen session through the same satellite machinery conversations already use —
no I2S, VA-state, or pipeline changes on device.

## Firmware (shared config; both boards inherit via the wrapper pattern)

- **Touch zone:** bottom-right block of the telemetry band — `x ≥ 192, y ≥ 264`
  (47×56 px ≈ 8.7×10.3 mm). New `ui_ic_x`/`ui_ic_y` substitutions, shared by
  hit-test and drawing per the overlay-geometry rule (drawn and tappable cannot
  drift). Hit only in normal mode (`ui_mode == 0`); during overlays the corner
  stays tap-away-dismiss and the glyph is not drawn.
- **⚠️ This carves the first exception into "any touch is talk".** That invariant's
  comment (touchscreen `on_touch`) is amended in place, dated 2026-08-05, JP's
  call: a *drawn, visible* control is not the silent misbehavior the rule guards
  against, and the rest of the screen stays byte-for-byte the talk gesture.
- **Action `16`** (next free): latched in `on_touch`, dispatched in `ui_dispatch`
  on release like every other target. Gated to idle exactly like talk
  (`va_state == 0 || 4`). Gets the standard haptic chime (its existing
  `va_state != 1` guard already protects the mic). **No coal strike** for this
  corner — feedback comes from the thing touched: the glyph flashes bright for
  ~400 ms via a new `ic_ms` global (the `spark_ms` pattern).
- **Signal to HA:** a template `event` entity (`Intercom`, event type `pressed`)
  — no HA-actions permission needed, and each device's event entity carries its
  identity, which is how the automation knows source from peer.
- **Glyph:** a small horn in the ember palette (dim amber at rest, gold while
  flashing), drawn in the telemetry band's right block. The band is chrome — it
  erases and overdraws by design, outside the flame band's write-once invariant —
  so the glyph costs nothing and cannot ghost.

## Home Assistant (new package `homeassistant/packages/ember_intercom.yaml`)

One automation, `mode: restart` (a new press supersedes a stuck capture; the
relayed announce itself is dispatched fire-and-forget via `script.turn_on`, so a
restart cannot kill a delivery in flight):

1. Trigger: state change of either `event.ember_*_intercom` entity. Guard: both
   `from_state` and `to_state` real (not `unavailable`/`unknown`) — event entities
   flap through `unavailable` on every device boot and HA restart, and a phantom
   summon on reboot is exactly the kind of bug this repo documents.
2. Map source → peer (desk ↔ mobile).
3. Peer satellite `unavailable`/`unknown` → speak on the **source**:
   *"The mobile hearth is dark."* Stop. (Fail before capture — don't take the
   user's speech and then lose it.)
4. `assist_satellite.ask_question` on the source — `question: "Send word."`,
   `preannounce: false` (Ember chimes locally, same rule as announce),
   `continue_on_error: true`, `response_variable: reply`.
5. `reply.sentence` non-empty → fire-and-forget `script.ember_announce` to the
   peer: *"Word from the {source} hearth: {sentence}"*. Empty or errored →
   fire-and-forget to the source: *"I heard nothing to carry."*

Registered in `deploy-ha.sh`'s `PACKAGES` array **in the same commit** (the
documented drift trap), with `automation` in the reload map.

## Out of scope

- Live voice streaming (#57).
- A relay *target picker* — with two hearths, "the other one" is fully determined
  by which button was pressed. The `send_word` LLM tool already covers arbitrary
  targeting by voice.
- Wyoming/Atom Echo satellites — this is a hearth-to-hearth feature.

## Verification

1. `esphome compile` both configs; OTA both boards (MAC-checked names).
2. Press the horn on the desk → mobile speaks the relayed words
   (`speaker_frames` climbs); press on the mobile → desk speaks.
3. Peer powered off → *"…hearth is dark."* on the source.
4. Silence after the prompt → *"I heard nothing to carry."*
5. Overlay open → corner tap dismisses the overlay (no intercom fire).
6. `check_navigability.py` and the other `esphome/tools/check_*.py` that apply;
   `deploy-ha.sh --check` before deploy.
7. Live two-hearth test with JP (also closes PR #58's two deferred items:
   the by-ear double-herald note and the unreachable-hearth reply).
