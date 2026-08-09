#!/usr/bin/env python3
"""Button-only navigability walk: every ui_mode reachable AND exitable without touch.

WHY THIS EXISTS (#23)

Three bugs in one day were the same KIND of bug, and no existing check could see any of
them, because each is a question about whether a PATH EXISTS. `esphome compile` and
`check_tiling` only confirm that the code ON a path is well-formed:

  * the mode-submenu cursor advanced `% 4` in a 3-row menu — a cursor state that lands
    on a row that is never drawn (#4);
  * the mode submenu had no `ui_mode == 3` long-press branch, so it was enterable from
    the BOOT button and NOT LEAVABLE from it (#4);
  * and the enclosure equivalents: a stand in front of the screen, buttons sealed inside
    it — present, and unreachable.

The second is the dangerous shape and it is specifically dangerous here. GPIO0/BOOT is
the ENTIRE hardware input budget (K1/RESET is hardwired to CHIP_PU and cannot be read),
so these menus exist ON the button precisely because recovering the device must not
require the touchscreen — `btn_rouse_touch` is a row in the power menu for exactly that
reason. A mode you cannot leave without a working touch controller defeats the menu's
whole purpose, and it was introduced within an hour of the submenu being added, by
reusing a mechanism that looked like it transferred. **A reused mechanism does not carry
its guarantees with it.**

HOW IT AVOIDS BEING A COPY OF THE FIRMWARE

The obvious way to write this is to hand-transcribe the two button lambdas into a
simulator. That inherits exactly the drift problem it is meant to catch — this repo has
a figure that hand-wrote a button outline as a rectangle and went on drawing squares
after the part became hexagonal, and a twelve-row truth table that verified *a
transcription of* the watchdog rather than the watchdog.

So this script EXTRACTS the action lists from `ember-satellite.yaml` and TRANSLATES them
into C++ mechanically, then compiles and runs them. The lambda bodies are emitted
verbatim. If the firmware's lambdas change, this walk changes with them; if they stop
compiling, this fails.

⚠️ THE TRANSLATION PRESERVES THE ONE SEMANTIC THAT MATTERS MOST. Each `- lambda:` action
becomes an immediately-invoked `[&]{ ... }();`, because **a `return` in an ESPHome lambda
ends that lambda and does NOT abort its sibling actions in the enclosing action list.**
That is not a detail — it is the bug in #15 and the bug oracle-verifier found on the
`va_state == 1` guard. A translation that let `return` escape the whole handler would be
a *different state machine* that happened to look right.

WHAT IT ASSERTS
  1. every ui_mode (0 normal, 1 volume, 2 power, 3 modes) is REACHABLE from (0, -1) by
     GPIO0 short/long presses only — no touch events at all;
  2. every reachable state can get BACK to ui_mode == 0 the same way, without rebooting;
  3. the cursor visits exactly the rows that are DRAWN — every drawn row reachable, and
     no row beyond the drawn count ever selected (this is the `% 4` bug);
  4. the three places that independently encode each menu's row count agree: the paint
     loop bound, the cursor modulus, and the touch hit-test bound;
  5. every drawn row is ACTIONABLE from the button — a long press on it must not do
     merely what a long press with nothing selected does.

⚠️ PROPERTY 5 EXISTS BECAUSE PROPERTY 2 PASSES ON THE BUG THIS FILE WAS WRITTEN FOR, and
that is worth stating here rather than discovering twice. #23 describes the missing
`ui_mode == 3` long-press branch as a mode that was "enterable from hardware, not
leavable from it." Measured, it was leavable: the long press fell through to the `else`
and RE-OPENED THE POWER MENU, from which the device escapes normally. Control A in this
script removes that branch and property 2 reports nothing at all — the walk was
structurally insensitive to the defect it was commissioned for, while looking like it
covered it. What was actually unreachable was not the exit but **the menu's purpose**:
you could not pick a mode. So the assert is on row actionability, and property 2 is kept
because it is a real (weaker) property, not because it catches this.

It also REPORTS, without failing, which exits cost a side effect — "Bank the fire" turns
the backlight off on the way out and "Rouse the touch sensor" resets the touch
controller. Those are real exits and they are not free, and a check that silently
counted them as clean escapes would be overstating what it verified. On the shipped file
the mode submenu's three rows are in that category: once the cursor leaves `-1` it can
never return to it (`ui_sel = (ui_sel + 1) % 3` has no path back), so the only button
exit from a selected row is to APPLY a mode. That is recoverable — re-selecting the
current mode is a no-op, and the 12 s auto-dismiss also escapes — but it is not a cancel,
and the menu's own on-screen text says "tap away to leave", which is touch.

RUN
  python3 esphome/tools/check_navigability.py [yaml]
  python3 esphome/tools/check_navigability.py --self-test   # four controls, must all fire
  python3 esphome/tools/check_navigability.py --emit        # dump the generated C++
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "ember-satellite.yaml")

MODES = (0, 1, 2, 3, 4)
# ui_mode 5 (a chronicle entry) is TOUCH-ONLY BY DESIGN and that is not a trap:
# a wedged touch controller cannot get INTO it, so button-reachability is not a
# recovery property there. Button-EXITABILITY is: the walk seeds (5, -1) as if a
# touch had opened it and asserts the button path out. Everything else keeps the
# full contract.
TOUCH_SEEDED = (5, 6, 7)


# See check_restore_resync.py for why this SafeLoader subclass is safe: it swallows
# ESPHome's `!`-prefixed tags as strings and constructs nothing.
class _Loose(yaml.SafeLoader):
    pass


_Loose.add_multi_constructor("!", lambda loader, suffix, node: getattr(node, "value", ""))


class Blind(Exception):
    """The checker could not find its subject. Distinct from 'the subject is fine' —
    verification.md §21: a detector that cannot tell absent from present-and-bad is not
    evidence in either direction."""


# ---------------------------------------------------------------- extraction

def _subst(text: str, subs: dict) -> str:
    """Resolve ESPHome ${name} substitutions textually, the way ESPHome does."""
    def rep(m):
        k = m.group(1)
        if k not in subs:
            raise Blind(f"unknown substitution ${{{k}}}")
        return str(subs[k])
    return re.sub(r"\$\{(\w+)\}", rep, text)


def _find(seq, pred, what):
    for x in seq or []:
        if pred(x):
            return x
    raise Blind(f"could not find {what}")


def load(path):
    with open(path) as f:
        raw = f.read()
    doc = yaml.load(raw, Loader=_Loose) or {}
    subs = doc.get("substitutions") or {}

    btn = _find(doc.get("binary_sensor"), lambda b: isinstance(b, dict)
                and b.get("id") == "btn_boot", "the btn_boot binary_sensor")
    clicks = btn.get("on_click") or []
    multi = btn.get("on_multi_click") or []
    dbl_then = []
    if len(clicks) == 2 and not multi:
        # the pre-chronicle shape: short and long both plain on_click
        def ms(c):
            return int(re.sub(r"[^0-9]", "", str(c.get("min_length", "0"))) or 0)
        short, long_ = sorted(clicks, key=ms)
    elif len(clicks) == 1 and len(multi) == 2:
        # the chronicle shape (2026-08-09): long stays an on_click; single and
        # double live in on_multi_click, told apart by their timing pattern —
        # the double has two ON phases, the single has one. Identified by
        # STRUCTURE, not list order, so reordering the YAML cannot swap them.
        long_ = clicks[0]
        def ons(m):
            return sum(1 for t in (m.get("timing") or []) if str(t).strip().upper().startswith("ON"))
        multi_sorted = sorted(multi, key=ons)
        if ons(multi_sorted[0]) != 1 or ons(multi_sorted[1]) != 2:
            raise Blind("on_multi_click entries are not one single-ON and one "
                        "double-ON pattern — the walk cannot tell single from double")
        short, dbl = multi_sorted
        dbl_then = dbl.get("then") or []
    else:
        raise Blind(f"btn_boot has {len(clicks)} on_click and {len(multi)} "
                    "on_multi_click blocks — expected (2,0) legacy or (1,2) "
                    "chronicle shape")

    dispatch = _find(doc.get("script"), lambda s: isinstance(s, dict)
                     and s.get("id") == "ui_dispatch", "the ui_dispatch script")

    return raw, subs, short.get("then") or [], long_.get("then") or [], \
        dispatch.get("then") or [], dbl_then


def row_counts(raw, subs):
    """The row count per menu, from the THREE independent places that encode it.

    They are written in three different syntaxes in three different lambdas, which is
    exactly why they can disagree — and did, as `% 4` in a 3-row menu.

    ⚠️ ANCHORED ON THE MENU HEADERS' CODE, not on `id(ui_mode) == N` and not on the bare
    header strings. Two revisions, each for a reason worth keeping:

    1. The first draft split on the branch test and landed on
       `const int OH = (id(ui_mode) == 3) ? ...` twenty lines earlier, then reported "no
       row loop found" — a checker failing to locate its subject and saying so, which is
       the only reason it did not silently pass.
    2. The second anchored on the bare string `"MODE"` and broke the moment someone wrote
       a COMMENT mentioning `"MODE"` in quotes — which happened within the hour, in the
       same commit that added the cancel cursor. It raised `Blind` rather than passing,
       correctly, but a guard that trips on prose about the code is a guard that gets
       disabled. Anchoring on `c_gold, "MODE")` includes the call's shape, so a sentence
       naming the string cannot collide with it.

    That is the third time today a search matched prose describing code rather than the
    code (§14's "read the line before counting it"), so the fix is structural rather than
    a reminder."""
    raw = _subst(raw, subs)
    A3, A2 = 'c_gold, "MODE")', 'c_gold, "THE HEARTH")'
    for anchor in (A3, A2):
        if raw.count(anchor) != 1:
            raise Blind(f"the paint-branch anchor {anchor!r} occurs "
                        f"{raw.count(anchor)} times, expected exactly 1 — re-anchor "
                        f"this extraction before trusting it")
    seg3 = raw.split(A3)[1].split(A2)[0]
    seg2 = raw.split(A2)[1]

    def loop_bound(seg, label):
        m = re.search(r"for\s*\(\s*int\s+i\s*=\s*0\s*;\s*i\s*<\s*(\d+)\s*;", seg)
        if not m:
            raise Blind(f"no row loop found in the {label} paint branch")
        return int(m.group(1))

    def names_len(seg, label):
        m = re.search(r"names\[(\d+)\]", seg)
        if not m:
            raise Blind(f"no names[] array found in the {label} paint branch")
        return int(m.group(1))

    drawn = {3: loop_bound(seg3, "mode-submenu"), 2: loop_bound(seg2, "power-menu")}
    named = {3: names_len(seg3, "mode-submenu"), 2: names_len(seg2, "power-menu")}

    # --- the touch hit-test bounds, scoped to the on_touch handler ---
    # `id(ui_mode) == 2` also appears in the long-press lambda ~3000 lines earlier, so
    # this must be scoped rather than searched globally.
    if "on_touch:" not in raw:
        raise Blind("no on_touch handler found")
    touch = raw.split("on_touch:")[1]
    hit = {}
    for mode in (2, 3):
        seg = touch.split(f"id(ui_mode) == {mode}")
        if len(seg) < 2:
            raise Blind(f"no ui_mode == {mode} hit-test branch found in on_touch")
        m = re.search(r"row\s*<\s*(\d+)", seg[1])
        if not m:
            raise Blind(f"no `row < N` bound in the ui_mode == {mode} hit-test")
        hit[mode] = int(m.group(1))

    return drawn, named, hit


# ---------------------------------------------------------------- translation

# Actions that touch no ui_mode/ui_sel state. Recorded as side effects so an exit that
# costs something is visible rather than counted as free.
SIDE_EFFECTS = {
    "number.increment": "number.increment",
    "number.decrement": "number.decrement",
    "light.turn_off": "light.turn_off",
    "light.turn_on": "light.turn_on",
    "button.press": "button.press",
    "voice_assistant.stop": "voice_assistant.stop",
    "audio_dac.mute_on": "audio_dac.mute_on",
    "audio_dac.mute_off": "audio_dac.mute_off",
}


def _cond_text(cond):
    """A condition is either {lambda: text} or a one-element list of that."""
    if isinstance(cond, list):
        if len(cond) != 1:
            raise Blind(f"condition list has {len(cond)} entries, expected 1")
        cond = cond[0]
    if not isinstance(cond, dict) or not isinstance(cond.get("lambda"), str):
        raise Blind(f"condition is not a lambda: {cond!r}")
    return cond["lambda"]


def translate(actions, subs, indent="  "):
    """Translate an ESPHome action list to C++, preserving sequential semantics."""
    out = []
    for a in actions or []:
        if not isinstance(a, dict):
            continue
        if len(a) == 1 and "lambda" in a and isinstance(a["lambda"], str):
            body = _subst(a["lambda"], subs)
            # ⚠️ IMMEDIATELY-INVOKED, NOT INLINED. A `return` in an ESPHome lambda ends
            # that lambda only; it does not abort the sibling actions after it. Inlining
            # the body would let a `return` escape the whole handler and would model a
            # different state machine. This is the #15 semantic.
            out.append(f"{indent}[&]{{\n{body}\n{indent}}}();")
            continue
        if "if" in a:
            blk = a["if"] or {}
            cond = _subst(_cond_text(blk.get("condition")), subs)
            out.append(f"{indent}if ([&]() -> bool {{ {cond} }}()) {{")
            out.append(translate(blk.get("then"), subs, indent + "  "))
            if blk.get("else"):
                out.append(f"{indent}}} else {{")
                out.append(translate(blk["else"], subs, indent + "  "))
            out.append(f"{indent}}}")
            continue
        key = next(iter(a))
        if key == "script.execute":
            tgt = a[key]
            name = tgt.get("id") if isinstance(tgt, dict) else tgt
            if name == "ui_dispatch":
                out.append(f"{indent}ui_dispatch();")
            else:
                out.append(f'{indent}SIDE("script.execute:{name}");')
            continue
        base = key.split(":")[0]
        if base in SIDE_EFFECTS:
            tgt = a[key]
            name = tgt.get("id") if isinstance(tgt, dict) else tgt
            out.append(f'{indent}SIDE("{base}:{name}");')
            continue
        out.append(f'{indent}SIDE("{base}");')
    return "\n".join(out)


HARNESS = r"""
// GENERATED by esphome/tools/check_navigability.py — do not edit.
// The lambda bodies below are the SHIPPED text from ember-satellite.yaml.
#include <cstdint>
#include <cstdio>
#include <cstddef>
#include <set>
#include <map>
#include <queue>
#include <string>
#include <vector>

// ---- the globals the button path touches, as plain values ----
static int ui_mode_v = 0, ui_sel_v = -1, ui_action_v = 0, ui_gen_v = 0;
static uint32_t ui_last_ms_v = 0;
static int va_state_v = 0, op_mode_v = 0;
static bool screen_banked_v = false, force_full_repaint_v = false;
// the chronicle's state (2026-08-09). Six dummy entries so index arithmetic in
// the dispatch lambdas runs against a populated ring, as it would in life.
static std::vector<std::string> chron_v = {"ha","sb","hc","sd","ae","sf"};
static std::vector<std::string> chron_chan_v = {"","","","","",""};
static int chron_page_v = 0, chron_sel_v = -1, chron_play_idx_v = -1;
// the horn's picker
static struct { std::string state; bool has_state() { return true; } }
    ic_targets_v = {std::string("Ember Dad|Ember Mobile|Shed speaker")};
static int ic_page_v = 0;
static std::string ic_pick_v;
static int help_page_v = 0;
static uint32_t chron_play_ms_v = 0;
static uint32_t clock_ms = 1000;
static uint32_t millis() { return clock_ms += 10; }

static std::vector<std::string> effects;
static void SIDE(const char *w) { effects.push_back(w); }

// `id(x)` resolves to a value for globals, and to a pointer-ish stub for entities.
struct SelStub {
  struct Call {
    size_t idx = 0;
    Call &set_index(size_t i) { idx = i; return *this; }
    void perform() { op_mode_v = (int) idx; SIDE("sel_mode.set_index"); }
  };
  Call make_call() { return Call(); }
};
static SelStub sel_mode_v;
struct SelPtr { SelStub *operator->() { return &sel_mode_v; } };

#define ui_mode      ui_mode_v
#define ui_sel       ui_sel_v
#define ui_action    ui_action_v
#define ui_gen       ui_gen_v
#define ui_last_ms   ui_last_ms_v
#define va_state     va_state_v
#define op_mode      op_mode_v
#define screen_banked        screen_banked_v
#define force_full_repaint   force_full_repaint_v
#define sel_mode     SelPtr()
#define chron          chron_v
#define chron_page     chron_page_v
#define chron_sel      chron_sel_v
#define chron_play_idx chron_play_idx_v
#define chron_play_ms  chron_play_ms_v
#define help_page      help_page_v
#define chron_chan     chron_chan_v
#define ic_targets     ic_targets_v
#define ic_page        ic_page_v
#define ic_pick        ic_pick_v
#define id(x) x

static void ui_dispatch() {
__DISPATCH__
}

static void press_short() {
__SHORT__
}

static void press_long() {
__LONG__
}

static void press_dbl() {
__DBL__
}

// ---------------------------------------------------------------- the walk
struct St { int mode, sel; };
static bool operator<(const St &a, const St &b) {
  return a.mode != b.mode ? a.mode < b.mode : a.sel < b.sel;
}

static void set_state(St s) {
  ui_mode_v = s.mode; ui_sel_v = s.sel; ui_action_v = 0;
  screen_banked_v = false; force_full_repaint_v = false;
  effects.clear();
}

struct Edge { St to; std::vector<std::string> fx; bool reboot; bool costly; };

// An ACKNOWLEDGEMENT is feedback for the press you just made; a CONSEQUENCE changes
// something about the device you would have to undo. The haptic chime fires on almost
// every dispatch, so counting it as a consequence made every single exit look costly and
// the report then named "bank/rouse" for all of them — a detector with one verdict
// applying it to every anomaly (verification.md §21). Keep this list explicit: anything
// not named here is treated as consequential, so a NEW action defaults to loud.
static bool is_ack(const std::string &f) {
  return f == "script.execute:chime";
}

static Edge step(St from, int which) {
  set_state(from);
  if (which == 0) press_short(); else if (which == 1) press_long(); else press_dbl();
  Edge e;
  e.to = St{ui_mode_v, ui_sel_v};
  e.fx = effects;
  e.reboot = false;
  e.costly = false;
  for (auto &f : effects) {
    if (f == "button.press:btn_restart") e.reboot = true;
    if (!is_ack(f)) e.costly = true;
  }
  return e;
}

int main() {
  const St start{0, -1};
  std::set<St> seen{start};
  std::map<St, std::vector<Edge>> g;
  std::queue<St> q;
  q.push(start);
  // ui_mode 5 is touch-entered by design; seed it so its BUTTON EXIT is walked
  // even though no button path leads in.
  for (int tm : {5, 6, 7}) {       // touch-entered: chronicle detail, help, picker
    const St ts{tm, -1};
    seen.insert(ts);
    q.push(ts);
  }
  while (!q.empty()) {
    St s = q.front(); q.pop();
    for (int w = 0; w < 3; w++) {
      Edge e = step(s, w);
      g[s].push_back(e);
      if (!seen.count(e.to)) { seen.insert(e.to); q.push(e.to); }
    }
  }

  // reachable states
  printf("STATES %zu\n", seen.size());
  for (auto &s : seen) printf("STATE %d %d\n", s.mode, s.sel);

  // Every edge, with its outcome, so the caller can ask whether a row DOES anything
  // rather than only whether the menu can be escaped.
  for (auto &kv : g) {
    for (size_t w = 0; w < kv.second.size(); w++) {
      const Edge &e = kv.second[w];
      printf("EDGE %d %d %zu %d %d", kv.first.mode, kv.first.sel, w, e.to.mode, e.to.sel);
      for (auto &f : e.fx) printf(" %s", f.c_str());
      printf("\n");
    }
  }

  // exitability: can each state reach mode 0 without rebooting?  And can it do so
  // with NO side effects at all?  Reported separately — an exit that turns the screen
  // off is a real exit and is not a free one.
  for (auto &s : seen) {
    std::set<St> vis{s};
    std::queue<St> qq; qq.push(s);
    bool ok = false, clean = false;
    std::map<St, bool> cleanTo;
    cleanTo[s] = true;
    while (!qq.empty()) {
      St c = qq.front(); qq.pop();
      if (c.mode == 0) { ok = true; if (cleanTo[c]) clean = true; }
      for (auto &e : g[c]) {
        if (e.reboot) continue;
        bool nc = cleanTo[c] && !e.costly;
        if (!vis.count(e.to)) {
          vis.insert(e.to); cleanTo[e.to] = nc; qq.push(e.to);
        } else if (nc && !cleanTo[e.to]) {
          cleanTo[e.to] = true; qq.push(e.to);   // found a cleaner route
        }
      }
    }
    printf("EXIT %d %d %d %d\n", s.mode, s.sel, ok ? 1 : 0, clean ? 1 : 0);
  }
  return 0;
}
"""


def build_source(path):
    raw, subs, short, long_, dispatch, dbl = load(path)
    src = (HARNESS
           .replace("__DISPATCH__", translate(dispatch, subs))
           .replace("__SHORT__", translate(short, subs))
           .replace("__LONG__", translate(long_, subs))
           .replace("__DBL__", translate(dbl, subs)))
    return src, raw, subs


def run_walk(path):
    src, raw, subs = build_source(path)
    drawn, named, hit = row_counts(raw, subs)
    with tempfile.TemporaryDirectory() as td:
        cpp = os.path.join(td, "walk.cpp")
        exe = os.path.join(td, "walk")
        with open(cpp, "w") as f:
            f.write(src)
        cc = subprocess.run(["g++", "-std=c++17", "-O0", "-w", cpp, "-o", exe],
                            capture_output=True, text=True)
        if cc.returncode != 0:
            raise Blind("the extracted button handlers DO NOT COMPILE — this is a real "
                        "failure, not a checker fault, unless the translator is at "
                        f"fault:\n{cc.stderr[:3000]}")
        run = subprocess.run([exe], capture_output=True, text=True, timeout=60)
        if run.returncode != 0:
            raise Blind(f"the walk crashed: {run.stderr[:2000]}")
    states, exits, edges = set(), {}, {}
    for line in run.stdout.splitlines():
        p = line.split()
        if p[0] == "STATE":
            states.add((int(p[1]), int(p[2])))
        elif p[0] == "EXIT":
            exits[(int(p[1]), int(p[2]))] = (p[3] == "1", p[4] == "1")
        elif p[0] == "EDGE":
            # (from_mode, from_sel, which) -> (to_mode, to_sel, sorted effects)
            edges[(int(p[1]), int(p[2]), int(p[3]))] = \
                (int(p[4]), int(p[5]), tuple(sorted(p[6:])))
    return states, exits, edges, drawn, named, hit


LONG = 1  # index of the long-press edge, matching the sorted-by-min_length order


def audit(path):
    findings, notes = [], []
    states, exits, edges, drawn, named, hit = run_walk(path)

    if not states:
        raise Blind("the walk visited no states at all — it never entered the state "
                    "machine, which is a vacuous pass, not a clean one")

    reached = {m for m, _ in states}

    # 1. reachability
    for m in MODES:
        if m not in reached:
            findings.append(f"ui_mode {m} is NOT REACHABLE from (0, -1) by button "
                            f"presses alone — it can only be entered by touch or from "
                            f"Home Assistant")

    # 2. exitability
    for (m, s), (ok, clean) in sorted(exits.items()):
        if not ok:
            findings.append(f"state (ui_mode={m}, ui_sel={s}) CANNOT return to "
                            f"ui_mode 0 by button presses without rebooting — with a "
                            f"wedged touch controller this is a mode you cannot leave")
        elif not clean and m != 0:
            # PROMOTED FROM A NOTE TO A FAILURE, 2026-07-31, on JP's decision.
            #
            # This was reported for information while the mode submenu had no cancel:
            # once its cursor left -1 it could never return (`% 3` has no path back), so
            # from any lit row the only button exit was to APPLY a mode. That is a menu
            # you cannot back out of with a wedged touch controller — in the menu that
            # exists BECAUSE recovery must not need the touchscreen.
            #
            # A cancel cursor position now exists, so every reachable state has a
            # button-only escape that commits nothing, and anything less is a
            # regression rather than a quirk. `clean` excludes the haptic
            # acknowledgement chime (see is_ack) and counts everything else as a
            # consequence, so a NEW action defaults to loud.
            findings.append(
                f"state (ui_mode={m}, ui_sel={s}) can ONLY reach ui_mode 0 by "
                f"committing an action that changes device state — there is no "
                f"button-only escape that commits nothing. With a wedged touch "
                f"controller the user's only way out of this state is to change "
                f"something they did not come here to change")

    # 3. the cursor visits exactly the drawn rows
    for m in (2, 3):
        sels = {s for mm, s in states if mm == m}
        n = drawn[m]
        over = {s for s in sels if s >= n}
        missing = set(range(n)) - sels
        if over:
            findings.append(f"ui_mode {m} draws {n} rows but the cursor reaches "
                            f"ui_sel {sorted(over)} — a row that is never drawn. This "
                            f"is the `% 4`-in-a-3-row-menu bug (#4)")
        if missing:
            findings.append(f"ui_mode {m} draws {n} rows but rows {sorted(missing)} "
                            f"are never selectable from the button path")

    # 4. the three encodings of each row count agree
    for m in (2, 3):
        trio = {"paint loop": drawn[m], "names[]": named[m], "hit-test": hit[m]}
        if len(set(trio.values())) != 1:
            findings.append(f"ui_mode {m}: the row count is encoded three times and "
                            f"they disagree — {trio}. The cursor modulus, the paint "
                            f"loop and the tap hit-test must agree or one of them is "
                            f"walking off the menu")

    # 5. EVERY DRAWN ROW MUST ACTUALLY DO SOMETHING FROM THE BUTTON.
    #
    # ⚠️ THIS IS THE ASSERT THAT CATCHES #4, AND PROPERTY 2 DOES NOT. When the
    # `ui_mode == 3` long-press branch was missing, a long press in the mode submenu
    # fell through to the `else` and RE-OPENED THE POWER MENU — from which the device
    # is still escapable. So "every mode is exitable" passed on the shipped bug. The
    # menu was leavable; what was unreachable was *the thing the menu is for*.
    #
    # The test needs no per-row model of what each row should do, which would be a
    # hand-copy of the firmware again. `ui_sel == -1` means "nothing aimed at, dismiss",
    # so a drawn row whose long-press outcome is IDENTICAL to the -1 outcome — same
    # resulting state, same effects — is a row that does nothing. That is the defect,
    # stated without naming any row's intent.
    for m in (2, 3):
        base = edges.get((m, -1, LONG))
        if base is None:
            notes.append(f"ui_mode {m} is never reached with ui_sel == -1, so row "
                         f"actionability could not be compared against a dismiss")
            continue
        for r in range(drawn[m]):
            got = edges.get((m, r, LONG))
            if got is None:
                continue          # unreachable rows are already reported by property 3
            if got == base:
                findings.append(
                    f"ui_mode {m} row {r} is INERT from the button: a long press on it "
                    f"does exactly what a long press with nothing selected does "
                    f"(-> ui_mode {base[0]}, effects {list(base[2]) or 'none'}). The "
                    f"row is drawn and selectable and cannot be activated without "
                    f"touch — this is #4's shape, and it is NOT caught by asking "
                    f"whether the menu can be escaped")

    return states, exits, edges, drawn, named, hit, findings, notes


def _report(path) -> int:
    try:
        states, exits, edges, drawn, named, hit, findings, notes = audit(path)
    except Blind as e:
        print(f"  BLIND  {e}", file=sys.stderr)
        return 1

    # Report the positive AND the negative (verification.md §21).
    print(f"button-only walk: {len(states)} reachable (ui_mode, ui_sel) states")
    print(f"  ui_modes reached : {sorted({m for m, _ in states})}  (want {list(MODES)})")
    for m in (2, 3):
        sels = sorted({s for mm, s in states if mm == m})
        print(f"  ui_mode {m}: rows drawn={drawn[m]} names[]={named[m]} "
              f"hit-test<{hit[m]}  cursor visits ui_sel {sels}")
    exitable = sum(1 for ok, _ in exits.values() if ok)
    clean = sum(1 for ok, c in exits.values() if ok and c)
    print(f"  exitable to ui_mode 0 without reboot: {exitable}/{len(exits)} "
          f"({clean} with no side effect at all)")
    for n in notes:
        print(f"  note  {n}")
    for f in findings:
        print(f"  FAIL  {f}", file=sys.stderr)
    if findings:
        print("\nGPIO0/BOOT is the entire hardware input budget. A mode that is "
              "enterable from it and not leavable from it defeats the reason these "
              "menus are on the button at all.", file=sys.stderr)
        return 1
    print("every mode reachable and exitable by button alone  OK")
    return 0


# ---------------------------------------------------------------- self-test

CONTROLS = [
    # A) the #4 bug: delete the ui_mode == 3 long-press branch. Mode 3 becomes
    #    enterable and not leavable.
    #    Anchored WITH the following comment line: `if (id(ui_mode) == 3) {` alone
    #    occurs three times (long-press, on_touch, paint) and the counted assertion
    #    below refused to run until this was narrowed.
    ("ui_mode == 3 long-press branch removed (#4)",
     "if (id(ui_mode) == 3) {\n"
     "                // ⚠️ WITHOUT THIS BRANCH",
     "if (false) {\n"
     "                // ⚠️ WITHOUT THIS BRANCH",
     "is INERT from the button"),
    # B) the #4 bug: let the mode cursor walk onto a row that is never drawn. Post-cancel
    #    the mode branch is its own `s >= 3` wrap rather than a shared modulus, so the
    #    mutation is the bound. (The previous spelling of this control anchored on
    #    `const int n = (id(ui_mode) == 3) ? 3 : ${ui_pm_n};`, which the cancel change
    #    deleted — the counted assertion below refused to run rather than silently
    #    mutating nothing, which is the only reason this was updated and not lost.)
    ("mode cursor wrap raised to 4 in a 3-row menu (#4)",
     "id(ui_sel) = (s >= 3) ? -1 : s;",
     "id(ui_sel) = (s >= 4) ? -1 : s;",
     "never drawn"),
    # E) THE CANCEL ITSELF: remove the path back to -1, restoring the state JP asked to
    #    fix. Every lit row then has no commit-free button exit.
    ("the cancel cursor position removed (cursor can never return to -1)",
     "id(ui_sel) = (s >= 3) ? -1 : s;",
     "id(ui_sel) = (s >= 3) ? 0 : s;",
     "no button-only escape that commits nothing"),
    # C) mode 1 unreachable: remove the short-press summon.
    ("short-press summon of the volume overlay removed",
     "id(ui_mode) = 1;              // summon the volume overlay",
     "id(ui_action) = 0;",
     "NOT REACHABLE"),
    # D) the row counts disagree: shrink the mode-submenu paint loop to 2 rows while
    #    the cursor modulus still says 3.
    ("mode-submenu paint loop shrunk to 2 rows, cursor still 3",
     "for (int i = 0; i < 3; i++) {\n            const int iy = ${ui_pm_iy}",
     "for (int i = 0; i < 2; i++) {\n            const int iy = ${ui_pm_iy}",
     "never drawn"),
]


def _self_test() -> int:
    with open(DEFAULT) as f:
        raw = f.read()
    ok = True
    tmp = os.path.join(HERE, ".selftest-nav.yaml")

    for label, old, new, want in CONTROLS:
        # A SILENT-NO-OP EDIT IS NOT A CONTROL. str.replace does not report whether it
        # replaced anything, so count the anchor first.
        if raw.count(old) != 1:
            print(f"self-test: anchor for {label!r} matched {raw.count(old)} times, "
                  f"expected 1 -> CONTROL CANNOT RUN", file=sys.stderr)
            ok = False
            continue
        with open(tmp, "w") as f:
            f.write(raw.replace(old, new))
        try:
            try:
                *_, findings, _notes = audit(tmp)
                fired = any(want in f for f in findings)
                detail = f"{len(findings)} finding(s)"
            except Blind as e:
                fired, detail = False, f"BLIND: {str(e)[:80]}"
        finally:
            os.unlink(tmp)
        print(f"self-test: {label} -> "
              f"{'DETECTED' if fired else 'DETECTOR IS BLIND'} ({detail})")
        ok = ok and fired

    # The negative half: a detector that always fires would pass every control above
    # while proving nothing.
    try:
        *_, findings, _notes = audit(DEFAULT)
        clean = not findings
    except Blind as e:
        clean, findings = False, [str(e)]
    print(f"self-test: unmodified file -> "
          f"{'clean, as required' if clean else 'REPORTS A FINDING — always fires'}")
    if not clean:
        for f in findings:
            print(f"    {f}", file=sys.stderr)
    ok = ok and clean
    return 0 if ok else 1


def main(argv) -> int:
    if "--self-test" in argv:
        return _self_test()
    path = next((a for a in argv[1:] if not a.startswith("-")), DEFAULT)
    if "--emit" in argv:
        src, _, _ = build_source(path)
        print(src)
        return 0
    return _report(path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
