#!/usr/bin/env python3
"""Fail if the shipped art tables and the harness's art tables have diverged.

WHY THIS EXISTS (#10) — the mitigation names a tool that has never existed.

The generated wyrm tables live in TWO places:

  * `esphome/art/dragon_spans.inc`  — `#include`d by `dragon_harness.cpp`, so this is
    what the host harness compiles, sanitises and tiling-checks.
  * inline inside the `paint_flame` lambda in `esphome/ember-satellite.yaml` — this is
    what actually ships to the device.

The YAML copy carries this instruction:

    Generated from dragon_harness.cpp by make_paste_block.py — the same text that
    compiles clean under -Wall -Wextra and passes the tiling invariant in every state.
    Do not hand-edit this copy; edit the harness, re-run it, and regenerate.

⚠️ **`make_paste_block.py` DOES NOT EXIST.** Not in the worktree, and not in any commit
on any branch — verified with a control (the same searches find 8 other `.py` files in
the tree and 28 added across history). So the prescribed process cannot be followed, and
the only executable option left is precisely the one the instruction forbids:
hand-editing the copy.

That reframes #10's history. Six stale-copy bugs in one session were not carelessness
against an available process — **the process was never runnable.** A warning comment is a
weak mitigation; a warning comment pointing at a missing program is not a mitigation at
all, and it reads exactly like one.

WHAT THIS CHECKS
  Every `static const <type> NAME[] = {...}` and `static const int NAME = k` in each
  file, compared by VALUE. It reports names present in one and not the other, and names
  whose values differ. Structural, so reflowing, re-indenting or rewriting comments in
  either copy cannot produce a false positive — which matters, because a guard that
  fires on comment churn gets disabled, and a disabled guard protects nothing.

WHAT IT DOES NOT CHECK
  Only the TABLES. The ~250 lines of painter LOGIC are also duplicated, between the
  harness's `paint_flame_frame()` and the YAML's `paint_flame` lambda.

  ⚠️ **A CORRECTION TO WHAT THIS DOCSTRING USED TO SAY.** It claimed that half "stays
  unguarded until #10 lands", on the grounds that the two copies are legitimately
  different text — the harness reads `g_*` globals and `it.` stubs where the firmware
  reads `id(...)` and ESPHome substitutions, so a plain diff would be all noise. The
  reasoning was right about a plain diff and the conclusion was wrong, because it ignored
  the one artifact that performs exactly that translation: `make_paste_block.py`. Once the
  generator was committed the comparison became mechanical, and it is now
  `check_paint_sync.py`. The claim was true of the tools I had and false of the tools that
  existed — which is the same shape as concluding the generator had never existed because
  it was not in the repo.

WHY BOTH SCRIPTS ARE KEPT
  `check_paint_sync.py` subsumes this one on paper: its reconstruction splices the tables
  in, so it compares them too. But it can only run if the GENERATOR runs — and the
  generator has already been silently broken once, by a correct fix to its input, while
  nobody could see it. This script compares the tables by VALUE and needs no generator, so
  it still answers "have the tables drifted?" on a day when that one answers nothing.
  Different dependencies, different failure modes; that is the whole argument.

RUN
  python3 esphome/tools/check_art_sync.py
  python3 esphome/tools/check_art_sync.py --self-test    # three controls, must all fire
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
YAML = os.path.join(HERE, "..", "ember-satellite.yaml")
INC = os.path.join(HERE, "..", "art", "dragon_spans.inc")

_ARR = re.compile(r"static\s+const\s+\w+\s+(\w+)\s*\[\s*\]\s*=\s*\{(.*?)\}\s*;", re.S)
_INT = re.compile(r"static\s+const\s+int\s+(\w+)\s*=\s*(-?\d+)\s*;")
_NUM = re.compile(r"-?\d+")


def tables(text: str) -> dict[str, tuple[int, ...]]:
    """name -> the integers it holds. Comments stripped first so prose cannot
    contribute values, and so editing a comment is not a divergence."""
    t = re.sub(r"//[^\n]*", "", text)
    out: dict[str, tuple[int, ...]] = {}
    for m in _ARR.finditer(t):
        out[m.group(1)] = tuple(int(x) for x in _NUM.findall(m.group(2)))
    for m in _INT.finditer(t):
        out[m.group(1)] = (int(m.group(2)),)
    return out


def audit(inc_text: str, yaml_text: str):
    inc, yml = tables(inc_text), tables(yaml_text)
    findings = []
    if not inc or not yml:
        # A CHECK THAT PARSED NOTHING MUST NOT REPORT AGREEMENT. "no tables found" and
        # "all tables agree" are indistinguishable from a pass otherwise.
        findings.append(f"parsed {len(inc)} tables from the .inc and {len(yml)} from the "
                        f"YAML — one side is empty, so this comparison proves NOTHING. "
                        f"Fix the extraction before trusting any result from it.")
        return inc, yml, findings

    for n in sorted(set(inc) - set(yml)):
        findings.append(f"`{n}` is in dragon_spans.inc (what the harness compiles) but "
                        f"NOT in the YAML — the harness is checking a table the device "
                        f"does not have")
    for n in sorted(set(yml) - set(inc)):
        findings.append(f"`{n}` is in the YAML (what ships) but NOT in "
                        f"dragon_spans.inc — the device has a table the harness never "
                        f"compiles, sanitises or tiling-checks")
    for n in sorted(set(inc) & set(yml)):
        a, b = inc[n], yml[n]
        if a == b:
            continue
        if len(a) != len(b):
            findings.append(f"`{n}` has {len(a)} values in the .inc and {len(b)} in the "
                            f"YAML — an extent mismatch, which on the device is a "
                            f"read past the end of an array")
        else:
            d = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
            findings.append(f"`{n}` differs in {len(d)} value(s); first at index "
                            f"{d[0][0]}: .inc={d[0][1]} yaml={d[0][2]}")
    return inc, yml, findings


def _report() -> int:
    inc, yml, findings = audit(open(INC).read(), open(YAML).read())
    # Report the positive AND the negative (verification.md §21).
    print(f"art tables — dragon_spans.inc: {len(inc)}   ember-satellite.yaml: {len(yml)}"
          f"   compared by value: {len(set(inc) & set(yml))}")
    for f in findings:
        print(f"  FAIL  {f}", file=sys.stderr)
    if findings:
        print("\nThe shipped tables and the harness's tables have diverged, so the "
              "harness is not checking what runs. There is no regenerate script — "
              "make_paste_block.py has never existed — so reconcile by hand and "
              "re-run this.", file=sys.stderr)
        return 1
    print("shipped tables and harness tables agree  OK")
    print("  (tables only — the painter LOGIC is still duplicated and unguarded; #10)")
    return 0


def _self_test() -> int:
    inc_raw, yml_raw = open(INC).read(), open(YAML).read()
    ok = True

    m = _ARR.search(re.sub(r"//[^\n]*", "", yml_raw))
    anchor = re.search(r"(static\s+const\s+uint8_t\s+DGN_B\s*\[\s*\]\s*=\s*\{)(.*?)(\}\s*;)",
                       yml_raw, re.S)
    if anchor is None:
        print("self-test: could not find DGN_B in the YAML -> CONTROLS CANNOT RUN",
              file=sys.stderr)
        return 1

    # 1) one perturbed value must be caught
    body = anchor.group(2).replace("112,113", "112,199", 1)
    if body == anchor.group(2):
        print("self-test: the perturbation was a NO-OP -> CONTROL CANNOT RUN",
              file=sys.stderr)
        ok = False
    else:
        mut = yml_raw[:anchor.start(2)] + body + yml_raw[anchor.end(2):]
        _, _, f = audit(inc_raw, mut)
        hit = any("`DGN_B` differs" in x for x in f)
        print(f"self-test: one value perturbed in DGN_B -> "
              f"{'DETECTED' if hit else 'DETECTOR IS BLIND'}")
        ok = ok and hit

    # 2) a dropped table must be caught
    mut2 = yml_raw[:anchor.start(0)] + yml_raw[anchor.end(0):]
    _, _, f = audit(inc_raw, mut2)
    hit = any("`DGN_B` is in dragon_spans.inc" in x for x in f)
    print(f"self-test: DGN_B removed from the YAML -> "
          f"{'DETECTED' if hit else 'DETECTOR IS BLIND'}")
    ok = ok and hit

    # 3) comment churn must NOT be reported — a guard that fires on prose gets disabled
    noisy = re.sub(r"//[^\n]*", "// a totally rewritten comment", yml_raw)
    _, _, f = audit(inc_raw, noisy)
    print(f"self-test: every comment rewritten -> "
          f"{'correctly insensitive' if not f else 'FALSE POSITIVE (would fire on prose)'}")
    ok = ok and not f

    # and the negative half: the real files must agree, or a detector that always fires
    # would pass all three controls above while proving nothing.
    _, _, f = audit(inc_raw, yml_raw)
    print(f"self-test: unmodified files -> "
          f"{'agree, as required' if not f else 'REPORTS A FINDING — always fires'}")
    ok = ok and not f
    return 0 if ok else 1


def main(argv) -> int:
    return _self_test() if "--self-test" in argv else _report()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
