#!/usr/bin/env python3
"""Fail if the shipped paint body and the harness's paint body have diverged.

WHY THIS EXISTS, and why it did not exist until 2026-07-31

`paint_flame` lives twice: in `dragon_harness.cpp` (where it can be compiled with
-Wall -Wextra, run under AddressSanitizer, and tiling-checked) and inline in
`ember-satellite.yaml` (where it actually ships). #10 exists because those two drift, and
six stale-copy bugs in one session came out of it.

⚠️ I PREVIOUSLY WROTE, IN `check_art_sync.py` AND AT THE YAML SITE, THAT THIS HALF WAS
**UNGUARDABLE BY DIFF** — on the grounds that the two copies are legitimately different
text: the harness reads `g_*` globals and `it.` stubs where the firmware reads `id(...)`
and ESPHome substitutions, so a textual diff would be all noise. That reasoning was
correct about a plain diff and **wrong about the conclusion**, because it ignored the one
artifact that performs exactly that translation: `tools/make_paste_block.py`. Once the
generator was committed, the comparison became mechanical. The claim was true of the
tools I had and false of the tools that existed — the same shape as concluding a script
had never existed because it was not in the repo.

So: **the stale-copy class #10 exists to eliminate is now DETECTABLE without doing the
extraction.** That does not close #10 — one copy is still better than two checked copies,
and the extraction unlocks the MAXH/GRATE assert that cannot be written while the harness
must mirror the lambda structurally. It does mean #10 is now a structure-and-elegance
issue rather than a safety one.

HOW IT WORKS
  1. run the generator over `art/dragon_harness.cpp` -> the paste block it would produce
  2. splice `art/dragon_spans.inc` in at the generator's "paste it here" marker, because
     the generator deliberately never emitted the tables (they were always manual)
  3. normalise both sides: strip `//` comments, collapse whitespace, drop blank lines
  4. require an exact line-for-line match against the `paint_flame` lambda in the YAML

Comments are stripped on purpose. The two copies carry genuinely different prose — each
explains itself to a different reader — and a guard that fired on that would be disabled
within a day.

RELATIONSHIP TO check_art_sync.py — both are kept, deliberately
  This check subsumes it on paper: the spliced reconstruction includes the tables. But it
  can only run if the GENERATOR runs, and the generator has already been broken once by a
  correct fix to its input (a renamed include path) while nobody could see it, because it
  was not in the repo. `check_art_sync.py` compares the tables by VALUE and needs no
  generator, so it still answers "have the tables drifted?" on a day when this script
  cannot answer anything. Different dependencies, different failure modes.

RUN
  python3 esphome/tools/check_paint_sync.py
  python3 esphome/tools/check_paint_sync.py --self-test   # four controls, must all fire
  python3 esphome/tools/check_paint_sync.py --diff        # show the differing lines
"""
from __future__ import annotations

import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "..", "art")
YAML = os.path.join(HERE, "..", "ember-satellite.yaml")
GEN = os.path.join(HERE, "make_paste_block.py")
HARNESS = os.path.join(ART, "dragon_harness.cpp")
SPANS = os.path.join(ART, "dragon_spans.inc")
MARKER = "paste the whole of"


class Blind(Exception):
    """Could not locate a subject. Distinct from 'the subjects agree' — a checker that
    cannot tell absent from present-and-bad is evidence in neither direction (§21)."""


def _norm(lines):
    out = []
    for l in lines:
        t = re.sub(r"//.*$", "", l).strip()
        if t:
            out.append(re.sub(r"\s+", " ", t))
    return out


def shipped(yaml_text: str):
    """The paint_flame lambda from the YAML, located by brace matching rather than by a
    closing-line pattern — `      };` also closes every table initialiser, which cost one
    wrong extraction before this was written."""
    y = yaml_text.splitlines()
    try:
        s = next(i for i, l in enumerate(y) if "auto paint_flame = [&]()" in l)
    except StopIteration:
        raise Blind("no `auto paint_flame = [&]()` in the YAML")
    d = 0
    for i in range(s, len(y)):
        d += y[i].count("{") - y[i].count("}")
        if i > s and d == 0:
            return y[s:i + 1]
    raise Blind("paint_flame's braces never balance — extraction is unreliable")


def reconstruct(harness_text: str, spans_text: str):
    """Run the generator over a harness and splice the tables in."""
    with tempfile.TemporaryDirectory() as td:
        art = os.path.join(td, "art")
        tools = os.path.join(td, "tools")
        os.makedirs(art)
        os.makedirs(tools)
        shutil.copy(GEN, os.path.join(tools, "make_paste_block.py"))
        with open(os.path.join(art, "dragon_harness.cpp"), "w") as f:
            f.write(harness_text)
        with open(os.path.join(art, "dragon_spans.inc"), "w") as f:
            f.write(spans_text)
        r = subprocess.run([sys.executable, os.path.join(tools, "make_paste_block.py")],
                           capture_output=True, text=True)
        if r.returncode != 0:
            # The generator refuses loudly by design. Surface its own words: it is more
            # specific than anything this script could say.
            raise Blind(f"the generator refused: {(r.stdout + r.stderr).strip()[:400]}")
        out = os.path.join(art, "dragon_paint_flame.inc")
        if not os.path.exists(out):
            raise Blind("the generator exited 0 and produced no output file")
        g = open(out).read().splitlines()
    try:
        gs = next(i for i, l in enumerate(g) if "auto paint_flame = [&]()" in l)
    except StopIteration:
        raise Blind("the generated block has no paint_flame lambda")
    g = g[gs:]
    mi = [i for i, l in enumerate(g) if MARKER in l]
    if len(mi) != 1:
        raise Blind(f"expected exactly 1 table-paste marker in the generated block, "
                    f"found {len(mi)}")
    return g[:mi[0]] + spans_text.splitlines() + g[mi[0] + 2:]


def audit(harness_text: str, yaml_text: str, spans_text: str):
    a = _norm(reconstruct(harness_text, spans_text))
    b = _norm(shipped(yaml_text))
    if not a or not b:
        raise Blind(f"normalised to {len(a)} and {len(b)} lines — one side is empty, so "
                    f"this comparison proves nothing")
    return a, b


def _report(show_diff: bool) -> int:
    try:
        a, b = audit(open(HARNESS).read(), open(YAML).read(), open(SPANS).read())
    except Blind as e:
        print(f"  BLIND  {e}", file=sys.stderr)
        return 1
    print(f"paint body — reconstructed from the harness: {len(a)} code lines; "
          f"shipped in the YAML: {len(b)}")
    if a == b:
        print("the harness and the shipped firmware are the same painter  OK")
        return 0
    dl = [l for l in difflib.unified_diff(a, b, "harness (via generator)", "shipped YAML",
                                          lineterm="", n=0)]
    changed = [l for l in dl if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    print(f"  FAIL  {len(changed)} line(s) differ — the harness is not verifying what "
          f"ships", file=sys.stderr)
    if show_diff or len(changed) <= 24:
        for l in dl:
            print(f"    {l}", file=sys.stderr)
    else:
        print("    (re-run with --diff for the full list)", file=sys.stderr)
    print("\n`-` lines exist only in the harness; `+` lines only in the shipped YAML. "
          "Reconcile INTO the harness — regenerating and pasting would silently revert "
          "whatever the YAML is ahead by.", file=sys.stderr)
    return 1


def _self_test() -> int:
    h, y, s = open(HARNESS).read(), open(YAML).read(), open(SPANS).read()
    ok = True

    def run(label, hh, yy, ss, want_fire):
        """⚠️ A `Blind` NEVER counts as a pass, in either direction.

        The first version of this helper scored a Blind as `fired = False`, so a control
        that expected NO difference passed when the generator had in fact crashed — a
        crash reported as "correctly insensitive". That is §21 exactly (absent and
        present-and-bad given the same verdict), committed inside a control written to
        catch that class. The comment-churn control below was doing it: rewriting every
        comment destroyed the `THE HEARTH-WYRM` marker the generator indexes on, so it
        died with a traceback and the self-test called it a success."""
        nonlocal ok
        try:
            a, b = audit(hh, yy, ss)
            fired = a != b
            n = sum(1 for x, z in zip(a, b) if x != z) or abs(len(a) - len(b))
            verdict = ("DETECTED" if fired else "DETECTOR IS BLIND") if want_fire else \
                      ("FALSE POSITIVE" if fired else "correctly insensitive")
            good = fired == want_fire
            detail = f"{n} diff"
        except Blind as e:
            verdict, good, detail = "INCONCLUSIVE (checker could not run)", False, \
                                    str(e).replace("\n", " ")[:80]
        print(f"self-test: {label} -> {verdict} ({detail})")
        ok = ok and good

    # 1) perturb CODE in the harness
    anchor = "if (silenced) jaw = 0;"
    if h.count(anchor) != 1:
        print(f"self-test: harness anchor matched {h.count(anchor)}x, expected 1 "
              f"-> CONTROL CANNOT RUN", file=sys.stderr)
        ok = False
    else:
        run("a code line changed in the harness", h.replace(anchor, "if (silenced) jaw = 1;"),
            y, s, True)

    # 2) perturb CODE in the shipped YAML.
    #    ⚠️ A LONGER ANCHOR THAN THE HARNESS ONE, because the bare statement occurs TWICE
    #    in the YAML — once as code and once quoted inside the comment that documents this
    #    very drift. The counted assertion caught that; a bare replace would have mutated
    #    the comment and produced a control that could never fire.
    y_anchor = "      if (silenced) jaw = 0;\n"
    if y.count(y_anchor) != 1:
        print(f"self-test: YAML anchor matched {y.count(y_anchor)}x, expected 1 "
              f"-> CONTROL CANNOT RUN", file=sys.stderr)
        ok = False
    else:
        run("a code line changed in the YAML", h,
            y.replace(y_anchor, "      if (silenced) jaw = 2;\n"), s, True)

    # 3) perturb a TABLE VALUE — proves the spliced tables are in scope
    m = re.search(r"(static const uint8_t DGN_B\[\] = \{)(.*?)(\};)", s, re.S)
    if m and "112,113" in m.group(2):
        run("a table value changed in dragon_spans.inc", h, y,
            s[:m.start(2)] + m.group(2).replace("112,113", "112,199", 1) + s[m.end(2):],
            True)
    else:
        print("self-test: DGN_B anchor not found -> CONTROL CANNOT RUN", file=sys.stderr)
        ok = False

    # 4) comment churn must NOT be reported, or the guard gets disabled.
    #    APPENDS to each comment rather than replacing it, so the generator's structural
    #    markers (`THE HEARTH-WYRM`, `END-OF-LAMBDA`, the spans include) survive. Replacing
    #    them wholesale destroyed those anchors, the generator died with a traceback, and
    #    the first version of this control read that crash as "correctly insensitive".
    churned = re.sub(r"//([^\n]*)", r"//\1 [churned]", h)
    run("every comment in the harness churned", churned, y, s, False)

    # and the negative half: the real files must match, or a detector that always fires
    # would pass controls 1-3 while proving nothing.
    run("unmodified files", h, y, s, False)
    return 0 if ok else 1


def main(argv) -> int:
    if "--self-test" in argv:
        return _self_test()
    return _report("--diff" in argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
