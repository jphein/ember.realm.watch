#!/usr/bin/env python3
"""
Turn the VERIFIED harness source into the block that goes in the YAML.

The point is that nobody retypes anything. dragon_harness.cpp is the thing that
was compiled with -Wall -Wextra and driven through every state with the tiling
invariant asserted; this script mechanically rewrites that same text into the
`paint_flame` lambda, so the code in the design and the code that passed cannot
drift apart. It fails loudly rather than emitting something half-translated.

  python3 esphome/tools/make_paste_block.py   ->  esphome/art/dragon_paint_flame.inc

---------------------------------------------------------------------------------
WHY THIS FILE ARRIVED IN THE REPO ON 2026-07-31, TWO DAYS AFTER IT WAS WRITTEN
(everything above this line is the original author's; everything below is lucid-fw)

⚠️ THIS SCRIPT EXISTED AND WAS NEVER COMMITTED. It sat in a session scratch
directory — `~/.claude/projects/-home-jp-Projects-familiar-realm-watch/scratch/`
`hosyond-s3/` — with its own output beside it as evidence it had run. So the
instruction in ember-satellite.yaml ("edit the harness, re-run it, and regenerate")
was executable *exactly once, by one person, inside one session*, and by nobody
afterwards. Invisible to every search of the repo, and one directory-cleanup away
from being gone for good.

I searched the repo, found nothing, and wrote **"make_paste_block.py has never
existed"** into the firmware. That claim was false. The search was correct — not in
the worktree, not in any commit on any branch, controls run in both directions — and
the conclusion was one step wider than it, because the repo was the only place I
looked. `nebula-site` found it in scratch. **An instrument's window is part of the
instrument** (verification.md §19), and mine was the repo.

The honest version of the finding is stronger than the false one, and it belongs to a
class the file already has: **committed is not deployed** — arriving here as
**uncommitted is not available.** The tool built to prevent the copies from drifting
was itself outside version control, which is a failure mode worse than drift, because
drift is at least discoverable.

TWO REPAIRS were needed before it would run at all; both are marked inline below.
It aborted with "REFUSING: the span-table include marker was lost" against the
current harness, because it matched a pre-extraction include path that has since been
correctly fixed. Its own loud-failure promise held — it refused rather than emitting
half a translation.

⚠️ IT DOES NOT EMIT THE ART TABLES, and that is by design rather than an omission.
It replaces the spans include with a comment telling a human to paste
`esphome/art/dragon_spans.inc` in by hand. So the ~700 lines of tables were ALWAYS a
manual step; only the ~250 lines of logic are mechanised. `check_art_sync.py` is what
guards the half this script never covered.

⚠️ AND THE OUTPUT DOES NOT CURRENTLY REPRODUCE THE SHIPPED BLOCK — 8 lines differ,
all of them present in the YAML and absent from the harness, so the YAML is AHEAD:

  1 line   `if (silenced) jaw = 0;`      the three-mode work (#4); the harness has no
                                         `silenced` concept, so it renders a jaw that
                                         opens in a speech-muted mode
  7 lines  `static_assert(CW == 4, …)`   and `static_assert(NC == 60, …)`

The asserts are the sharp one. The harness comment at `dragon_harness.cpp:465`
says of them: *"a fix belongs in the yaml … Flagged to the firmware owner rather
than changed here."* The firmware owner added them; nobody closed the loop back. So
this is not accidental drift — it is a **deliberate one-way handoff completed on one
side only**, which leaves the NC/CW guards living exclusively in the copy that cannot
be sanitised, and absent from the copy where `NC = 80` was actually tried and smashed
the stack. That harness comment is now stale rather than wrong: it was true when
written, and describes an item that is closed elsewhere.

DO NOT run this and paste the result until those 8 lines are reconciled INTO THE
HARNESS — regenerating today would silently revert them. Reconciling is the next
step and is deliberately not done here: it changes what the harness compiles, needs
a `g_silenced` global, and would take the harness's standing `-Wunused-variable 'CW'`
count from 1 to 0 (the assert reads CW, which is the correct way to silence a warning
that was telling the truth). All of that wants verifying against the recorded
runs/frame baseline, not doing at the end of a long session.
"""

import os
import re
import sys

# Anchored to THIS file, not the cwd. The original read "dragon_harness.cpp" from
# whatever directory it was invoked in, which worked only inside the scratch dir that
# held a copy of the harness. Same reason the harness's own include is file-relative.
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "art", "dragon_harness.cpp")
OUT = os.path.join(HERE, "..", "art", "dragon_paint_flame.inc")

# harness global -> ESPHome id(). Every g_* MUST appear here or the run aborts.
IDS = {
    "g_db_rms": "id(db_rms)",
    "g_db_peak": "id(db_peak_hold)",
    "g_tts_est_ms": "id(tts_est_ms)",
    "g_spark_col": "id(spark_col)",
    "g_hist_idx": "id(hist_idx)",
    "g_level_hist": "id(level_hist)",
    "g_unread": "id(unread)",       # the chronicle aura's pulse (2026-08-09)
}

# literals the live YAML carries as substitutions
SUBS = [
    (r"% 120\b", "% ${hist_len}"),
    (r"const int DGN_X = 60, DGN_Y = 22, DGN_W = 120, DGN_H = 50;",
     "const int DGN_X = ${dgn_x}, DGN_Y = ${dgn_y};\n"
     "  const int DGN_W = ${dgn_w}, DGN_H = ${dgn_h};"),
    (r"static uint8_t topy\[144\], boty\[144\];",
     "static uint8_t topy[${dgn_w} + 24], boty[${dgn_w} + 24];"),
    (r"static bool rim_hd\[144\];", "static bool rim_hd[${dgn_w} + 24];"),
    (r"static uint8_t nk0\[50\], nk1\[50\];",
     "static uint8_t nk0[${dgn_h}], nk1[${dgn_h}];"),
    (r"static Color k_row\[50\];", "static Color k_row[${dgn_h}];"),
    (r"static bool k_row_hot\[50\];", "static bool k_row_hot[${dgn_h}];"),
    (r"static uint8_t drow\[144\];", "static uint8_t drow[${dgn_w} + 24];"),
]

src = open(SRC).read()
start = src.index("  // =====================  THE HEARTH-WYRM  =====================")
end = src.index("// ------------------------------------------------------- END-OF-LAMBDA")
body = src[start:end]
body = body[: body.rindex("}")]                       # drop the function brace

# ⚠️ MATCHED BY FILENAME, NOT BY PATH, AND THAT IS A BUG FIX (lucid-fw, 2026-07-31).
# This originally matched the literal string
#   #include "../../../../../Projects/ha/esphome/art/dragon_spans.inc"
# a path from before this project was extracted out of ~/Projects/ha. The harness's
# include was later corrected to a file-relative "dragon_spans.inc" — a real fix,
# because the old path meant the harness did not compile from a clone at all — and
# that correct fix SILENTLY INVALIDATED THIS SCRIPT. Run against the current harness
# it aborted with "REFUSING: the span-table include marker was lost".
# Nobody could see that, because this file was never committed (see the header note).
# A filename match cannot break the same way again.
body = re.sub(r'#include\s+"[^"]*dragon_spans\.inc"', "@@SPANS@@", body)

# harness-only scaffolding
body = body.replace(" && !g_no_dragon", "")
for pat in [r"[ \t]*n_sqrt\+\+;", r"[ \t]*n_classify\+\+;", r"[ \t]*n_row\+\+;",
            r"[ \t]*n_memset \+= [^;]+;"]:
    body = re.sub(pat, "", body)
body = re.sub(r"\n[ \t]*\n([ \t]*(?:int|const|if|for|\}))", r"\n\1", body)
body = body.replace("std::memset", "memset")

for g, i in IDS.items():
    body = re.sub(r"\b%s\b" % g, i, body)
for pat, rep in SUBS:
    body = re.sub(pat, rep, body)

leftover = sorted(set(re.findall(r"\bg_[a-z_]+", body)) | set(re.findall(r"\bn_[a-z]+\b", body)))
if leftover:
    sys.exit("REFUSING: harness-only symbols survived the rewrite: %s" % leftover)
if "@@SPANS@@" not in body:
    sys.exit("REFUSING: the span-table include marker was lost")

lines = ["    " + l if l.strip() else "" for l in body.split("\n")]
body = "\n".join(lines).rstrip()
body = body.replace("    @@SPANS@@",
                    "      // >>> paste the whole of esphome/art/dragon_spans.inc HERE <<<\n"
                    "      //     (generated; ~3.6 KB of static const tables)")

hdr = (
    "      // ---------------------------- THE FIRE, AND WHAT SLEEPS IN IT -------\n"
    "      // Generated from dragon_harness.cpp by make_paste_block.py — the same\n"
    "      // text that compiles clean under -Wall -Wextra and passes the tiling\n"
    "      // invariant in every state. Do not hand-edit this copy; edit the\n"
    "      // harness, re-run it, and regenerate.\n"
    "      auto paint_flame = [&]() {\n")
open(OUT, "w").write(hdr + body + "\n      };\n")
print("%s: %d lines" % (OUT, (hdr + body).count("\n") + 2))
