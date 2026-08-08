# The candle — the mobile hearth's cell, read as wax

**Date:** 2026-08-08 · **Status:** implemented, flashed to the mobile, HA side live

A candle in the sigil band of `ember-mobile` only: wax height is state of charge,
the flame is the state of the state. Born from a real failure — on 2026-08-06/07
the bare 18650 discharged from 3.76 V to a recorded **2.508 V with nobody
watching**. That cell has no protection IC; a cell left flat goes to zero and does
not come back. The candle is the quiet half of the answer, the escalation ladder
the loud half, and the 1S protection strip remains the actual safety net.

## The glyph (sigil band, right edge)

```
full, on charge      low (guttering)      critical           unknown
     *                                        ▮▮  (blinks)
    ▲▲▲                   ◢◢  (leans           |                 |
     |                     | on 600ms          ▯                 |
   ▓▓▓▓▓                 ▓▓▓  ticks)          ─────           ─────
   ▓▓▓▓▓                 ─────
   ─────
```

- **Wax** = SOC, 0–14 px on a fixed baseline, molten rim on the top face.
- **Flame**: steady teardrop healthy; **white-tipped and taller** when the rail
  reads ≥ 3.98 V (full-or-charging — the TP4054's CHRG pin isn't wired, so the
  flame claims only what the voltage shows); **leaning gutter** at ≤ 20%;
  **blinking alarm spark** at ≤ 8%; **cold wick, no wax claim** before the first
  sample — unknown and empty never share a glyph.
- State carried by shape and motion, never colour alone (band accessibility rule).
- The sub-line's right anchor and the unread dot step left of the candle,
  compile-time gated, so the desk layout is bit-identical to before.

## Two bodies, one firmware

`has_battery: "0"` in the shared config, `"1"` in `ember-mobile.yaml`. Every
battery lambda tests the literal and folds out on the desk build — which is the
*correctness* property, not an optimisation: the desk's GPIO9 floats, and noise
can look like any voltage you name. The **SOC entity lives in the wrapper**, so
the desk cannot grow a confident number derived from a floating pin, and the HA
automation triggering on that entity can never fire from the desk. Verified: the
desk build log contains zero `Battery SOC` references.

## Signal chain

GPIO9 ADC, 60 s → `median(5)` (speaker sag rejection: one deep sample is
*discarded*, not averaged in) → piecewise-linear SOC over an 11-point table
calibrated to this cell's observed discharge, sized-array declarations
(`VS[11]`) so `check_art_sync.py`'s empty-bracket heuristic ignores them —
same convention as `LEN_MS[8]`. Live cross-check at deploy: 3.636 V → 43%,
matching hand interpolation exactly.

## The escalation ladder

| trigger | act | owner |
|---|---|---|
| SOC ≤ 20%, once per discharge | `chime_guttering` — C5→A4→F4, a fall that *sinks past* where `done` resolves; on-pentatonic because a low cell is normal life, not an error | firmware (latched, released at +5 pts) |
| SOC ≤ 8% for 10 min | the mobile speaks one persona line herself, `continue_on_error`; then `ember_broadcast` (importance high) → desk hearth, or Slack in quiet hours | `ember_battery_watch.yaml` |

Case 7 follows §15's discipline: enumerated in the `is_running()` guard list
*and* guarded at its play site — it must never destroy a reply in flight; there
is a whole ladder behind it. `numeric_state` ignores `unknown`, so a rebooting
board (SOC is NAN until the first sample) cannot false-alarm, and a board that is
*offline* is deliberately not this alarm's job — a battery alarm that also means
"wifi hiccup" trains people to ignore it.

## Scheduler cost

Two repaint reasons, both folding out on the desk: a signature-int change test
(wax px + banding + rich bit — a 60 s sample that changes nothing visible
repaints nothing), and a 600 ms gutter tick (a multiple of the 50 ms frame, per
the scheduler's `!!` warning) that runs **only while guttering and idle** — in
conversation the flame band keeps its slots and a frozen mid-lean flame still
reads as guttering. Shape is the signal; motion is a luxury.

## Honest limits

- Voltage→SOC on a flat li-ion curve is an estimate; the middle of the table is
  ±10 points on a warm day. The thresholds are placed on the steep shoulder
  where the estimate is good.
- No charge detection beyond the ≥ 3.98 V read — the CHRG line isn't wired.
- A dead/offline board shows a stale candle on a dark screen — moot — and a
  stale SOC in HA; `ember_backend_health` owns liveness, not this.
- The desk unit was offline (unplugged) at flash time; it runs the previous
  build, whose behavior is identical. It picks the new source up on next flash.
