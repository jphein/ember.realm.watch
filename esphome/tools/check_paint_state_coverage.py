#!/usr/bin/env python3
"""Fail if the painter reads state that no scenario varies (#10's marshalling guard).

WHY THIS EXISTS

#10 moves the wyrm painter out of the YAML lambda and into a shared header so the harness
and the firmware compile the same file. Its acceptance test is good and falsifiable:

    identical runs/frame and px/frame across every scenario, before and after the move.

⚠️ **THAT TEST IS ONLY AS STRONG AS SCENARIO COVERAGE, AND THAT IS NOT A DETAIL.**

The one real risk in the move is marshalling: state the painter reaches today via `g_*`
(firmware: `id(...)`) has to be packed into a POD. If a field is dropped, zeroed or wired
to the wrong source, behaviour changes.

But a field that **no scenario varies** produces identical runs/frame and px/frame whether
it is marshalled correctly or not marshalled at all. The acceptance test passes, and it
passes *confidently*, which is worse than having no test — a green result that cannot
distinguish a correct move from a broken one is an appearance of verification.

Measured when this was written, against nine scenarios:

    g_db_rms       VARIED   -12.0 when "listen-loud" else -40.0
    g_db_peak      VARIED   -12.0 when "listen-loud" else -34.0
    g_tts_est_ms   VARIED   k.live ? 4200 : 0
    g_spark_col    VARIED   from k.hit
    g_level_hist   CONSTANT filled from sin(i*0.21) with no k. dependence — identical
                            in all nine
    g_hist_idx     NEVER    declared = 0 at dragon_harness.cpp:145, read at :556, and
                            assigned NOWHERE ELSE in the file

So two of six fields were invisible to the acceptance test. `g_hist_idx` is the sharper
case: it is 0 in every scenario, so **dropping it from the POD entirely is undetectable**.

WHAT THIS CHECKS
  The field set is read from `make_paste_block.py`'s `IDS` map rather than from a list
  maintained here. That map is authoritative because the generator ABORTS if any `g_*`
  survives its rewrite — so it cannot silently fall behind the painter. A hand-kept list
  here would be a second copy of exactly the kind #10 exists to eliminate.

  For each field, the scenario-setup region is scanned for assignments and classified:
    VARIED   — the assigned expression references the scenario variable, so it differs
    CONSTANT — assigned, but the same value in every scenario
    NEVER    — no assignment outside its declaration

  VARIED passes. CONSTANT and NEVER fail unless explicitly waived below, because both mean
  the acceptance test is blind to that field.

WAIVERS
  A waiver is a claim that a field's correctness is proven by something OTHER than the
  ten-scenario numbers. Write the reason. An empty reason is not a waiver.

RUN
  python3 esphome/tools/check_paint_state_coverage.py
  python3 esphome/tools/check_paint_state_coverage.py --self-test
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(HERE, "make_paste_block.py")
HARNESS = os.path.join(HERE, "..", "art", "dragon_harness.cpp")

# field -> why it is allowed to be invisible to the acceptance test.
# Keep this EMPTY unless there is a real argument; the point of the guard is that a green
# acceptance test means something.
WAIVERS: dict[str, str] = {}


def fields() -> list[str]:
    """The POD field set, taken from the generator's IDS map (see WHAT THIS CHECKS)."""
    src = open(GEN).read()
    m = re.search(r"^IDS\s*=\s*\{(.*?)^\}", src, re.S | re.M)
    if not m:
        sys.exit("REFUSING: could not find IDS in make_paste_block.py — the field set is "
                 "derived from it, so a rename here must not silently pass.")
    got = re.findall(r'"(g_[a-z0-9_]+)"\s*:', m.group(1))
    if not got:
        sys.exit("REFUSING: IDS parsed to ZERO fields, which reads as a pass and is not "
                 "one. Every field would trivially count as covered.")
    return sorted(got)


def scenario_region(src: str) -> str:
    """The per-scenario setup: from the Case table to the end of the loop body.

    Anchored on `struct Case` rather than a line number so it survives edits above it.
    """
    i = src.index("struct Case")
    return src[i:]


def scenario_dependent_names(region: str) -> set[str]:
    """Names whose value differs between scenarios, by transitive closure from `k`.

    ⚠️ THE INDIRECTION IS REAL AND THE FIRST VERSION OF THIS MISSED IT. `g_db_rms` is
    assigned `loud ? -12.0f : -40.0f`, which contains no `k.` at all — but `loud` is
    `std::string(k.name) == "listen-loud"` two lines above. Matching only `k.` inside the
    assignment classified two genuinely-covered fields as blind.

    Caught by control 1, which is the entire reason that control names a field known to be
    varied rather than only testing the failure direction. A guard that over-reports gets
    waived into uselessness just as surely as one that under-reports gets ignored.
    """
    names = {"k"}
    # iterate to a fixpoint: locals assigned from anything already scenario-dependent
    for _ in range(8):
        before = len(names)
        for name, expr in re.findall(
                r"\b(?:const\s+)?(?:bool|int|float|auto|std::string)\s+(\w+)\s*=\s*([^;]+);",
                region):
            if any(re.search(r"\b%s\b" % re.escape(n), expr) for n in names):
                names.add(name)
        if len(names) == before:
            break
    return names


def classify(src: str, field: str) -> tuple[str, str]:
    """-> (VARIED | CONSTANT | NEVER, evidence)."""
    region = scenario_region(src)
    dep = scenario_dependent_names(region)
    # assignments of the form `field = expr;` or `field[i] = expr;`
    hits = re.findall(re.escape(field) + r"\s*(?:\[[^\]]*\])?\s*=\s*([^;]+);", region)
    if not hits:
        return "NEVER", "no assignment in the scenario region"
    for h in hits:
        if any(re.search(r"\b%s\b" % re.escape(n), h) for n in dep):
            return "VARIED", h.strip()[:60]
    return "CONSTANT", hits[0].strip()[:60]


def report() -> int:
    src = open(HARNESS).read()
    fs = fields()
    print(f"painter POD fields (from make_paste_block.py IDS): {len(fs)}")
    bad = []
    for f in fs:
        kind, why = classify(src, f)
        mark = "ok " if kind == "VARIED" else ("WAIVED" if f in WAIVERS else "BLIND")
        print(f"  {f:<16} {kind:<9} {mark:<7} {why}")
        if kind != "VARIED" and f not in WAIVERS:
            bad.append((f, kind, why))
    print()
    if bad:
        print(f"FAIL: {len(bad)} of {len(fs)} fields are invisible to the acceptance test.")
        for f, kind, why in bad:
            print(f"  {f}: {kind} — identical in every scenario, so the ten-scenario "
                  f"runs/frame + px/frame comparison CANNOT tell a correct marshalling "
                  f"of this field from a dropped one.")
        print("\nFix by varying the field in at least one scenario, or add a WAIVER with "
              "a reason that does not rely on the acceptance test.")
        return 1
    print(f"all {len(fs)} painter fields are varied by at least one scenario — the "
          f"acceptance test can see every one of them  OK")
    return 0


def self_test() -> int:
    """Three controls. The instrument must fire, and must not fire on the good case."""
    src = open(HARNESS).read()
    ok = True

    # 1. a field the harness genuinely varies must read VARIED
    k, _ = classify(src, "g_db_rms")
    print(f"  control 1  g_db_rms (varied by k.name)        -> {k}"
          f"{'  ok' if k == 'VARIED' else '  *** FAIL ***'}")
    ok &= k == "VARIED"

    # 2. a field assigned but never from `k` must read CONSTANT
    k, _ = classify(src, "g_level_hist")
    print(f"  control 2  g_level_hist (assigned, no k.)     -> {k}"
          f"{'  ok' if k == 'CONSTANT' else '  *** FAIL ***'}")
    ok &= k == "CONSTANT"

    # 3. a field never assigned must read NEVER
    k, _ = classify(src, "g_hist_idx")
    print(f"  control 3  g_hist_idx (declared once, :145)   -> {k}"
          f"{'  ok' if k == 'NEVER' else '  *** FAIL ***'}")
    ok &= k == "NEVER"

    # 4. the field set must be non-empty AND come from the generator
    n = len(fields())
    print(f"  control 4  IDS parsed {n} fields             -> "
          f"{'ok' if n >= 4 else '*** FAIL ***'}")
    ok &= n >= 4

    print("\nall controls behaved" if ok else "\n*** a control did not fire ***")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(self_test() if "--self-test" in sys.argv else report())
