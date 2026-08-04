# The house row — what is still awake, seen from the hearth

**Date:** 2026-08-03 · **Status:** implemented and flashed to both boards

One row at the bottom of Ember's screen answering one question at a glance: is
anything still running in the house, and where. Lights, minisplits, radiant
floors, radiators and the towel warmer.

## Requirements, as settled

| | |
|---|---|
| What it says | **Which rooms**, not just a count and not just yes/no — so it can be acted on without opening the app |
| Overflow | **Cap the glyphs at 4, keep the names readable.** Past four rooms the coals become `+N` |
| Grouping | **Rooms, not devices.** The Laundry has a bulb *and* a minisplit and is one room |
| Kinds | Lights, plus cooling and heating as distinct marks |

## Architecture

```
sensor.lights_on                    house-wide, packages/lights_overview.yaml
climate.*  (minus 2 duplicates)     minisplits, floors, radiators
        │
        ▼
sensor.ember_house_watch            homeassistant/packages/ember_house_watch.yaml
  state      = rooms awake (union, deduped)
  names      = "Laundry . Shed"  (joined, capped at 4 + "+N")
  lights / cooling / heating = counts, for glyph typing
  detail     = human-readable why (dashboard + debugging; never on the device)
        │  5 × platform: homeassistant, internal: true
        ▼
TELE_Y + 40                         esphome/ember-satellite.yaml
  <coals> <heat/draught marks>  <room names>
```

**HA shapes, the device draws.** Every set-union, dedupe and truncation is Jinja,
which can be pasted into HA's template editor and watched live. The display lambda
is the hardest place in this project to test anything, so it does no string work
and no arithmetic it could get wrong.

This is the **first state this device has ever imported from Home Assistant** —
everything else flows outward. The consequence worth stating: the values are NaN
until HA connects, which is not an error path but the normal first second of every
boot.

## The three states

```
lit       (o) (o) ≡   Laundry . Shed
quiet     ~ every hearth banked ~
unknown   hearths unknown
```

`unknown` is not decoration. Reporting 0 when nothing is known claims the house is
dark — a lie in the one direction that costs money. `availability:` on the template
sensor propagates unavailability, and `HomeassistantSensor` publishes `NAN` for
anything it cannot parse (`homeassistant_sensor.cpp:14-18`, verified by reading it),
so the device sees unknown rather than zero. Observed live during a
`template.reload`.

## Four traps, all found on the bench

1. **A naive `light.*` count returns 10, not 2.** It sweeps up
   `light.ember_satellite_backlight`, `light.ember_mobile_backlight`, both status
   LEDs, three BLE-proxy Bluetooth LEDs and two minisplit display LEDs. **Ember
   would have counted its own screen as a light left on and never once read zero.**
   `sensor.lights_on` already excludes all of it.
2. **The minisplits are exposed twice.** `climate.air_conditioner` has
   `friendly_name: 'laundry minisplit'` and `air_conditioner_2` is
   `'luna minisplit'` — the same two physical units as `climate.laundry_minisplit`
   / `climate.luna_minisplit` via a second integration. Matching on a name pattern
   makes one running unit read as two. Excluded by entity_id.
3. **`state` is the mode; `hvac_action` is whether it is running.**
   `climate.kitchen_thermostat` ("Kitchen Floor") sits at `state='cool'` with
   `hvac_action='idle'`. Counting `state != 'off'` reports the floor as going while
   it does nothing — and it looks right whenever something *is* running, which is
   what would have shipped it. The minisplits publish no `hvac_action` at all, so
   the two families need different rules.
4. **The floors and radiators are named `*_thermostat`.** Searching entity_ids for
   "radiant", "radiator" or "floor" finds *nothing*; only the friendly names say
   what they are — Kitchen Floor, Bedroom Floor, Pumphouse Floor, Laundry
   Radiators, Towel Warmer. Concluding they didn't exist would have been a search
   proving absence with no control (`verification.md` §13).

## Display constraints that set the design

- **No new band.** Bands tile 0..319 exactly and at most one repaints per frame.
  The fuse precedent is explicit: a 4-row band still consumes a whole frame slot
  and cost the fire ~5fps. This row lives inside TELE, which is chrome that
  overdraws by design and sits outside the flame band's write-once invariant and
  its 18,240 px/frame budget. Four coals is ~256 px — free.
- **Row 3 is the last row.** TELE is 264..319; rows at +6, +24, +40. A row at +58
  would end at 334 and draw outside its band, and because the framebuffer persists
  that litter would be permanent and would look like ghosting, not overflow.
- **Not the +24 slot**, which the op_mode lines own — losing the indicator exactly
  when Ember is quiet is backwards.
- **Shape carries the kind, not colour.** The palette is one fire-temperature ramp
  by design with `alarm` its only exception, and the band's accessibility rule is
  that no state is ever carried by colour alone. A coal is round, heat rises to a
  point, a draught is flat — all three read in greyscale.
- **The breathing period is set by band rotation, not taste.** One band per frame
  at 50 ms means this row redraws ~every 200 ms (5 fps). A short pulse reads as a
  stutter; 3500 ms reads as a breath. Coals are offset 800 ms apart so they look
  like separate fires rather than one blinking row.

## Known gap, deliberately left open

A **full API disconnection** pushes nothing, so the last value persists and the row
can show a stale count. It is not detectable locally without lying: the obvious
guard is "is an API client connected", and `on_client_connected` fires for *any*
client including the `esphome` CLI, so `esphome logs` alone would satisfy it with
HA absent. A guard that reads as a freshness check while testing something else is
worse than the staleness it hides. The honest fix, if ever needed, is a heartbeat
*from* HA — a value that changes on a timer, so absence of change is absence of HA.

## Out of scope

`sensor.lights_unavailable` reports 3 locally-controlled lights (TV Glow, Under
Counter, Outdoor) that HA cannot see. Surfacing "and 3 I can't see" is a real idea
and a second feature; it would crowd a 240px row.
