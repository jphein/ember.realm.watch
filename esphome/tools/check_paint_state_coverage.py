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

Measured against the nine original scenarios, the painter reads **14** state fields and
**five** of them were invisible:

    g_level_hist   CONSTANT filled from sin(i*0.21), no k. dependence — identical in all
    g_hist_idx     NEVER    declared = 0 at :145, read at :556, assigned NOWHERE ELSE
    g_frames_mark  CONSTANT assigned 0 in every scenario
    g_silenced     NEVER    the harness says so itself at :158 — "No scenario sets it yet"
    g_wake_reset   NEVER    only ever set by the wake_reset() hook, which no scenario calls

`g_hist_idx` is the sharpest: 0 in every scenario, so **dropping it from the POD entirely
would have been undetectable**. The `hist-rotated` scenario closed it and `g_level_hist`
together — it must run at st == 1, because the history is read only on the listening
branch, so any other state would satisfy a coverage counter and leave the numbers blind.

Still blind, deliberately unwaived: `g_frames_mark`, `g_silenced`, `g_wake_reset`. Each
needs a scenario before #10's move can be trusted. They are left failing rather than
waived because a red guard is a to-do list and a waived one is a lie.

WHAT THIS CHECKS
  The field set is every `g_*` that `paint_flame_frame()` reads, parsed from the harness —
  NOT from `make_paste_block.py`'s `IDS`. IDS covers only the paste block, which is the
  right set for *sync* and the wrong one for *the move*; see `fields()`. IDS is still
  cross-checked as a strict subset, because if it ever isn't, the generator and the
  painter have diverged.

  For each field, the scenario-setup region is scanned for assignments and classified:
    VARIED   — the assigned expression references the scenario variable, so it differs
    CONSTANT — assigned, but the same value in every scenario
    NEVER    — no assignment outside its declaration

  VARIED passes. CONSTANT and NEVER fail unless explicitly waived below, because both mean
  the acceptance test is blind to that field.

⚠️ WHAT THIS STILL CANNOT SEE
  It proves a field is VARIED BY A SCENARIO. It does not prove that varying it MOVES THE
  OUTPUT — a field could be assigned differently per scenario and still reach nothing that
  affects runs/frame, in which case the acceptance test remains blind to it and this guard
  says OK. Closing that properly is mutation testing: force each field and require some
  scenario's number to move.

  Not built. Instead the three scenarios added for this were each checked by hand to move
  the number, which is the same evidence for today's field set and none for tomorrow's:

    hist-rotated  2445  vs listening 2090   (+355)
    silenced      1620  vs speaking  1619   (+1)
    mid-speech    1626  vs speaking  1619   (+7)

  `silenced` moves the metric by ONE run/frame. That is enough under exact-match
  comparison and it is deterministic across runs — but it is thin, and if a future edit
  makes `if (silenced) jaw = 0` a no-op the delta becomes 0 while this guard still reports
  VARIED. If you touch the jaw, re-measure that delta by hand.

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


# Harness-only scaffolding: read by the painter body but never marshalled, because the
# generator strips it (`g_no_dragon`) or it is a test hook rather than frame state.
NOT_STATE = {"g_no_dragon"}


def ids_fields() -> list[str]:
    """The generator's IDS map — the state the PASTE BLOCK translates."""
    src = open(GEN).read()
    m = re.search(r"^IDS\s*=\s*\{(.*?)^\}", src, re.S | re.M)
    if not m:
        sys.exit("REFUSING: could not find IDS in make_paste_block.py.")
    return sorted(re.findall(r'"(g_[a-z0-9_]+)"\s*:', m.group(1)))


def fields() -> list[str]:
    """The POD field set for #10's move: every g_* the WHOLE painter reads.

    ⚠️ **THIS DELIBERATELY DOES NOT USE `IDS`, AND THE FIRST VERSION OF THIS FILE DID.**

    `IDS` covers only the paste block — the region between the HEARTH-WYRM marker and
    END-OF-LAMBDA, which is what `make_paste_block.py` synchronises. That is the right
    field set for *sync* and the wrong one for *the move*.

    #10 extracts `paint_flame_frame()` **entire**, and its preamble (theme colours, state
    decode, TTS progress, spark decay) reads seven more globals that never appear in IDS —
    among them `g_silenced`, which the harness itself documents at :158 as "No scenario
    sets it yet". Scoping the guard to IDS reported 6 fields and missed more than half of
    the real marshalling surface, which is the same error the guard exists to catch, made
    by the guard.

    So: derived from the painter body, with IDS kept only as a cross-check that the paste
    region is a strict subset. If it ever isn't, the generator and the painter have
    diverged and that is its own bug.
    """
    src = open(HARNESS).read()
    s = src.index("static void paint_flame_frame() {")
    e = src.index("// ------------------------------------------------------- END-OF-LAMBDA")
    body = re.sub(r"//[^\n]*", "", src[s:e])
    got = sorted(set(re.findall(r"\bg_[a-z0-9_]+", body)) - NOT_STATE)
    if len(got) < 6:
        sys.exit(f"REFUSING: the painter body parsed to only {len(got)} state fields, "
                 f"which reads as near-total coverage and is not. Check the markers.")
    stray = set(ids_fields()) - set(got) - NOT_STATE
    if stray:
        sys.exit(f"REFUSING: IDS translates {sorted(stray)}, which the painter body does "
                 f"not read. The generator and the painter have diverged.")
    return got


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


def writers_called(src: str, region: str, field: str) -> str | None:
    """A helper that assigns `field` and is CALLED from the scenario region, if any.

    ⚠️ SECOND INDIRECTION, AND IT PRODUCED A FALSE POSITIVE. `g_wake_reset` is never
    assigned in the scenario region, so a direct-assignment scan calls it NEVER — but
    `wake_reset()` sets it and the strip scenarios call that. Reporting it blind would have
    sent someone to write a scenario that already exists.

    That matters more than it sounds: this guard's whole value is that a red line means
    real work. A guard that cries wolf gets waived, and a waived guard protects nothing —
    the same reason `check_art_sync` compares by value rather than by text.
    """
    for name, body in re.findall(r"\b(?:static\s+)?void\s+(\w+)\s*\([^)]*\)\s*\{([^}]*)\}",
                                 src):
        if re.search(re.escape(field) + r"\s*=", body) and \
           re.search(r"\b%s\s*\(" % re.escape(name), region):
            return name
    return None


def classify(src: str, field: str) -> tuple[str, str]:
    """-> (VARIED | CONSTANT | NEVER, evidence)."""
    region = scenario_region(src)
    dep = scenario_dependent_names(region)
    # assignments of the form `field = expr;` or `field[i] = expr;`
    hits = re.findall(re.escape(field) + r"\s*(?:\[[^\]]*\])?\s*=\s*([^;]+);", region)
    if not hits:
        w = writers_called(src, region, field)
        if w:
            return "VARIED", f"set by {w}(), called from a scenario"
        return "NEVER", "no assignment in the scenario region"
    for h in hits:
        if any(re.search(r"\b%s\b" % re.escape(n), h) for n in dep):
            return "VARIED", h.strip()[:60]
    return "CONSTANT", hits[0].strip()[:60]


def report() -> int:
    src = open(HARNESS).read()
    fs = fields()
    print(f"painter POD fields (every g_* paint_flame_frame reads): {len(fs)}")
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


# A synthetic harness exercising every classification path.
#
# ⚠️ SYNTHETIC ON PURPOSE, AND IT TOOK THREE FAILURES TO LEARN IT. The controls first named
# real fields — g_level_hist, g_hist_idx, then g_frames_mark, g_silenced. Every time the
# guard did its job and someone added the missing scenario, the control that depended on
# that field being blind went red. The self-test was measuring the codebase instead of the
# instrument, so **fixing the bug broke the test that found it** — three times.
#
# A control must fail when the INSTRUMENT breaks, not when the code improves. Fixtures make
# the four paths permanent, and the real harness having zero blind fields no longer leaves
# the failure directions untested.
_FIXTURE = r"""
static void wake_reset() { g_reset_me = true; }
int main() {
  struct Case { const char *name; int st; bool live; };
  const Case cases[] = { {"a",0,false}, {"b",1,true} };
  for (int c = 0; c < 2; c++) {
    const Case &k = cases[c];
    const bool loud = (std::string(k.name) == "b");
    g_direct = k.st;
    g_indirect = loud ? -12.0f : -40.0f;
    g_pinned = 0;
    wake_reset();
  }
}
"""


def self_test() -> int:
    """Five controls against a synthetic harness. Must fire in BOTH directions."""
    ok = True
    checks = [
        ("g_direct",   "VARIED",   "assigned straight from k."),
        ("g_indirect", "VARIED",   "assigned via a k.-derived local"),
        ("g_pinned",   "CONSTANT", "assigned, same value every scenario"),
        ("g_absent",   "NEVER",    "never assigned at all"),
        ("g_reset_me", "VARIED",   "written by a helper the loop calls"),
    ]
    for i, (field, want, why) in enumerate(checks, 1):
        got, _ = classify(_FIXTURE, field)
        good = got == want
        print(f"  control {i}  {field:<11} {why:<38} -> {got:<8}"
              f"{'  ok' if good else '  *** FAIL, wanted ' + want + ' ***'}")
        ok &= good

    n = len(fields())
    print(f"  control 6  painter body parses to {n} fields"
          f"{'':<21}-> {'ok' if n >= 6 else '*** FAIL ***'}")
    ok &= n >= 6

    print("\nall controls behaved" if ok else "\n*** a control did not fire ***")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(self_test() if "--self-test" in sys.argv else report())

# ─────────────────────────────────────────────────────────────────────────────────────
# ⚠️ SCOPE CORRECTION, FOUND AFTER c36c585 AND LEFT HERE RATHER THAN QUIETLY REWRITTEN.
#
# c36c585 says "#10 extracts paint_flame_frame() ENTIRE". That is FALSE, and the evidence
# was available the whole time in the harness's own comment at :156.
#
# The firmware preamble and the harness preamble are NOT two copies of one thing. They
# differ BY DESIGN:
#
#     harness                       firmware (ember-satellite.yaml)
#     st = g_va_state               st = id(va_state), coerced to 3 when
#                                     audio_live && !chiming && (st==0||st==2)
#     silenced = g_silenced         silenced = (st == 3) && id(op_mode) >= 1
#     frames_mark injected          maintained via `static bool was_live`
#
# `g_silenced` is documented at :156 as "Mirrors the firmware's silenced" — a MIRROR, so
# the harness can force states the firmware derives. That is correct design, not drift,
# and it is why make_paste_block.py starts extracting at the HEARTH-WYRM marker and not at
# the top of the function.
#
# So the shareable region is the PASTE BLOCK ONLY. Everything above the marker is
# per-environment and always will be. A "pure move" of the whole painter would have to
# unify two preambles that are deliberately different — which is not a move, it is a
# redesign, and it would delete the harness's ability to force a state.
#
# The 14-field number stays useful as the full state surface, and the four scenarios it
# drove out (hist-rotated, silenced, mid-speech) exercise painter paths that had never run
# in any test — worth having regardless of whether #10 ever lands. But nobody should read
# c36c585 as a plan for the move.
