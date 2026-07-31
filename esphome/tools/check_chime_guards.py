#!/usr/bin/env python3
"""Fail if a chime case is guarded in the enumeration but not where the guard bites.

WHY THIS EXISTS — a fix that was applied, compiled clean, and changed nothing.

`chime_play` guards against preempting in-flight audio in TWO places, and only one of
them declines a play:

  1. an enumeration inside the script's first `- lambda:` —
         if ((which == 0 || which == 1 || ...) && id(spk)->is_running()) return;
  2. a per-case `!id(spk)->is_running()` in each play action's own `condition:`

Half 1 gates `chime_until` and NOTHING ELSE, because **a `return` in a lambda cannot
abort its sibling actions in the enclosing action list.** The satellite's own comments
state this three times and it is the bug oracle-verifier found on the `va_state == 1`
guard. Half 2 is the half that stops the audio.

#15 is the instance. Case 3 (thinking) was added to the enumeration and its play
condition was left as `which == 3 && id(va_state) != 1`. The diff read as the fix, the
build was clean, `esphome config` was happy, and the thinking chime went on destroying
in-flight replies exactly as before — `enqueue: false` calls
announcement_playlist_.clear() then start_file(), so the preempted item's remaining
audio is discarded and never resumed.

⚠️ THE FAILURE IS INVISIBLE IN REVIEW AND WAS LATENT ON TOP OF THAT. `chime_on_thinking`
defaults to 0, so the case that was "fixed" is also the case nobody plays — it would
first misbehave for whoever flipped that substitution to try the feature, mid-taste-
experiment, with a reply dying mid-sentence and no reason to suspect a chime.

WHAT IT CHECKS
  The two halves agree. The set of cases enumerated in the top guard must equal the set
  of cases whose play condition carries `!id(spk)->is_running()`. It reports BOTH
  directions and names both sets, so "absent" is distinguishable from "present and bad"
  (verification.md §21). It does NOT judge which cases *ought* to be guarded — cases 2
  and 4 are exempt for stated reasons and this script has no opinion about taste; it
  only refuses to let the two halves disagree.

RUN
  python3 esphome/tools/check_chime_guards.py [yaml]        # default: the satellite
  python3 esphome/tools/check_chime_guards.py --self-test   # prove it can fail, twice
"""
from __future__ import annotations

import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "ember-satellite.yaml")

N_CASES = 7  # 0 done · 1 error · 2 announce · 3 thinking · 4 timer · 5 touch · 6 haptic

# See check_restore_resync.py for why this SafeLoader subclass is safe: it swallows
# ESPHome's `!`-prefixed tags as strings and constructs nothing. Do not rebase it on
# yaml.Loader to make the tags resolve — that turns a parser into an executor.
class _Loose(yaml.SafeLoader):
    pass


_Loose.add_multi_constructor("!", lambda loader, suffix, node: getattr(node, "value", ""))

PLAY_KEY = "media_player.speaker.play_on_device_media_file"
RUNNING = "id(spk)->is_running()"

# The enumeration, matched on its STRUCTURE rather than on a copy of its text: a
# parenthesised disjunction of `which == N` immediately followed by `&& <running>`.
_ENUM_RE = re.compile(
    r"if\s*\(\s*\((?P<cases>[^()]*?)\)\s*&&\s*" + re.escape(RUNNING), re.S)
_WHICH_RE = re.compile(r"which\s*==\s*(\d+)")


def _script(doc, sid):
    for s in doc.get("script") or []:
        if isinstance(s, dict) and s.get("id") == sid:
            return s
    return None


def audit(path: str):
    with open(path) as f:
        doc = yaml.load(f.read(), Loader=_Loose) or {}

    findings = []
    sc = _script(doc, "chime_play")
    if sc is None:
        return None, None, None, ["no `chime_play` script found — this checker is "
                                  "pointed at the wrong file or the script was renamed"]
    actions = sc.get("then") or []

    # ---- half 1: the enumeration in the first lambda ----
    body = ""
    for a in actions:
        if isinstance(a, dict) and isinstance(a.get("lambda"), str):
            body = a["lambda"]
            break
    m = _ENUM_RE.search(body)
    if not m:
        # A CHECK THAT CANNOT LOCATE ITS SUBJECT MUST SAY SO RATHER THAN PASS.
        # "no cases enumerated" and "the regex missed" are indistinguishable from a
        # clean run otherwise (verification.md §21, and the `n=0` rule).
        return None, None, None, [
            "could not locate the `(which == ...) && id(spk)->is_running()` enumeration "
            "in chime_play's first lambda — DETECTOR IS BLIND, fix the checker before "
            "trusting any result from it"]
    enumerated = {int(n) for n in _WHICH_RE.findall(m.group("cases"))}

    # ---- half 2: the per-case play conditions ----
    play_guarded, plays = set(), {}
    for a in actions:
        if not (isinstance(a, dict) and "if" in a):
            continue
        blk = a["if"] or {}
        cond = blk.get("condition") or {}
        ctext = cond.get("lambda") if isinstance(cond, dict) else None
        if not isinstance(ctext, str):
            continue
        # only action blocks that actually PLAY are in scope
        thens = blk.get("then") or []
        if not any(isinstance(t, dict) and PLAY_KEY in t for t in thens):
            continue
        which = _WHICH_RE.findall(ctext)
        if len(which) != 1:
            findings.append(f"a play action's condition names {len(which)} `which ==` "
                            f"tests; expected exactly 1: {ctext.strip()!r}")
            continue
        n = int(which[0])
        plays.setdefault(n, []).append(ctext)
        # Whitespace-insensitive so a reflow cannot silently un-detect the guard — the
        # repo has a line-oriented-grep false negative on record (verification.md §13).
        if f"!{RUNNING}" in re.sub(r"\s+", "", ctext):
            play_guarded.add(n)

    # ---- structural sanity: exactly one play per case ----
    for n in range(N_CASES):
        k = len(plays.get(n, []))
        if k != 1:
            findings.append(f"case {n} has {k} play actions; expected exactly 1")

    # ---- the property: the two halves must agree ----
    for n in sorted(enumerated - play_guarded):
        findings.append(
            f"case {n} is in the enumeration but its play condition does NOT carry "
            f"`!{RUNNING}` — the enumeration only gates chime_until, so this case still "
            f"plays and still destroys in-flight audio. This is #15 exactly.")
    for n in sorted(play_guarded - enumerated):
        findings.append(
            f"case {n} declines the play but is NOT in the enumeration — so when it "
            f"does play, chime_until is set for a sound the gate will classify as "
            f"speech. Add it to the enumeration or explain the asymmetry.")

    return enumerated, play_guarded, plays, findings


def _report(enumerated, play_guarded, plays, findings) -> int:
    # Report the positive AND the negative explicitly, so a reader can tell "looked and
    # found nothing" from "did not look" (verification.md §21).
    if enumerated is None:
        for f in findings:
            print(f"  FAIL  {f}", file=sys.stderr)
        return 1
    exempt = sorted(set(range(N_CASES)) - enumerated)
    print(f"chime_play cases found: {sorted(plays)}")
    print(f"  enumerated in top guard : {sorted(enumerated)}")
    print(f"  guarded at the play site: {sorted(play_guarded)}")
    print(f"  exempt (neither)        : {exempt}  "
          f"(2 announce herald, 4 timer — both exempt with stated reasons)")
    for f in findings:
        print(f"  FAIL  {f}", file=sys.stderr)
    if findings:
        print("\nThe two halves of the preempt guard disagree. A `return` in the "
              "enumeration lambda cannot abort sibling actions — the play condition is "
              "the half that declines a sound.", file=sys.stderr)
        return 1
    print("both halves of the preempt guard agree  OK")
    return 0


def _self_test() -> int:
    """Two deliberately-broken inputs, one per direction. A check that has never
    produced a positive is not evidence (verification.md §13), and this check can fail
    two different ways, so it needs two controls rather than one."""
    with open(DEFAULT) as f:
        raw = f.read()
    tmp = os.path.join(HERE, ".selftest-chime.yaml")
    ok = True

    controls = [
        # A) strip the play-side guard from case 3 — the #15 bug, re-injected.
        ("play-side guard removed from case 3",
         "return which == 3 && id(va_state) != 1 && !id(spk)->is_running();",
         "return which == 3 && id(va_state) != 1;", 3),
        # B) remove case 3 from the enumeration — the opposite asymmetry.
        ("case 3 removed from the enumeration",
         "which == 0 || which == 1 || which == 3 || which == 5 || which == 6",
         "which == 0 || which == 1 || which == 5 || which == 6", 3),
    ]

    for label, old, new, expect in controls:
        # A SILENT-NO-OP EDIT IS NOT A CONTROL. str.replace returns a string, not
        # whether it replaced anything, so count the anchor first — the repo has already
        # paid for skipping this once.
        if raw.count(old) != 1:
            print(f"self-test: anchor for {label!r} matched {raw.count(old)} times, "
                  f"expected 1 -> CONTROL CANNOT RUN", file=sys.stderr)
            ok = False
            continue
        with open(tmp, "w") as f:
            f.write(raw.replace(old, new))
        try:
            enumerated, play_guarded, plays, findings = audit(tmp)
        finally:
            os.unlink(tmp)
        fired = any(f"case {expect} " in f for f in findings)
        print(f"self-test: {label} -> "
              f"{'DETECTED' if fired else 'DETECTOR IS BLIND'} "
              f"({len(findings)} finding(s))")
        ok = ok and fired

    # And the negative half: the real file must be clean, or a detector that always
    # fires would pass this self-test while proving nothing.
    enumerated, play_guarded, plays, findings = audit(DEFAULT)
    clean = enumerated is not None and not findings
    print(f"self-test: unmodified file -> "
          f"{'clean, as required' if clean else 'REPORTS A FINDING — detector always fires'}")
    ok = ok and clean
    return 0 if ok else 1


def main(argv) -> int:
    if "--self-test" in argv:
        return _self_test()
    path = next((a for a in argv[1:] if not a.startswith("-")), DEFAULT)
    return _report(*audit(path))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
