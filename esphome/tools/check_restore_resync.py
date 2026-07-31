#!/usr/bin/env python3
"""Fail if a restoring template control can lie about the hardware after a reboot.

WHY THIS EXISTS — a bug that was found, fixed, documented, and then shipped again.

`TemplateNumber::setup()` calls `publish_state()` and never `control()`
(components/template/number/template_number.cpp). So a control with `restore_value: true`
comes back after a reboot displaying its stored value while its `set_action` — the thing
that actually writes the hardware — never runs. The entity and the device disagree, and
the entity is the one people read.

That was diagnosed for `spk_volume`, fixed with an `on_boot` resync, and written up in a
comment carrying the exact source line numbers. Then `mic_gain_num` was added months of
work later with the same shape and the same defect, because **the fix had been applied to
an instance rather than turned into a rule.** A note saying "this component behaves like X"
does not protect the next component that behaves like X. This script is the rule.

⚠️ THE FAILURE IS QUIET AND ITS ONLY IMMUNE CASE IS THE ONE YOU WOULD TEST WITH. For mic
gain the codec kept the compile-time default, so the divergence appeared only after storing
a NON-default value. Set it to the default, reboot, and everything looks perfect.

WHAT IT CHECKS
  For every `number:`/`select:`/`switch:` entry with `restore_value: true` AND a
  `set_action`, require that some `esphome.on_boot` trigger mentions that entity's id.
  It does not try to prove the resync is *correct* — only that one exists. A check that
  claims more than it verifies is the thing this repo keeps cataloguing.

RUN
  python3 esphome/tools/check_restore_resync.py [yaml]        # default: the satellite
  python3 esphome/tools/check_restore_resync.py --self-test   # prove it can fail
"""
from __future__ import annotations

import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "ember-satellite.yaml")

# ESPHome's YAML is full of local tags (!lambda, !secret, !include). A plain loader dies on
# them, so swallow every unknown tag as a string. Anchored to the tag *class*, not a list of
# the tags this file happens to use today.
#
# ⚠️ `yaml.load(..., Loader=_Loose)` below is SAFE and the distinction is worth stating,
# because the dangerous-looking call is the one a scanner flags. `_Loose` derives from
# **SafeLoader**, not the default Loader, so `!!python/object` and friends are still refused —
# this is `safe_load` plus a tolerance for ESPHome's own `!`-prefixed tags. The multi
# constructor returns a plain string for every one of them and constructs nothing. Do not
# "fix" this by switching the base to `yaml.Loader` to make the tags resolve properly; that
# would turn a parser into an executor.
class _Loose(yaml.SafeLoader):
    pass


_Loose.add_multi_constructor("!", lambda loader, suffix, node: getattr(node, "value", ""))


def _boot_text(doc) -> str:
    """Every on_boot block, flattened to text. The resync can be a number.set, a lambda, or
    anything else that names the id — matching on the id rather than on a specific action
    keeps this from being a search narrower than the property (verification.md §18)."""
    boot = (doc.get("esphome") or {}).get("on_boot")
    return "" if boot is None else yaml.safe_dump(boot, default_flow_style=False)


def audit(path: str):
    with open(path) as f:
        raw = f.read()
    doc = yaml.load(raw, Loader=_Loose) or {}
    boot = _boot_text(doc)

    findings, checked = [], []
    for domain in ("number", "select", "switch"):
        for ent in doc.get(domain) or []:
            if not isinstance(ent, dict):
                continue
            if ent.get("restore_value") is not True:
                continue
            if not any(k.endswith("_action") for k in ent):
                continue  # restores, but writes no hardware — not the shape
            eid = ent.get("id")
            if not eid:
                findings.append((domain, "<no id>", "has restore_value + a *_action but no id"))
                continue
            checked.append(f"{domain}.{eid}")
            # word-boundary so `spk_volume` does not match `spk_volume_extra`, and so both
            # the `id: x` and `id(x)` spellings count. A reviewer's regex matched only the
            # first spelling today and nearly reported a fixed bug as live.
            if not re.search(rf"\b{re.escape(str(eid))}\b", boot):
                findings.append((domain, eid,
                                 "restores a value and writes hardware in its *_action, but no "
                                 "on_boot trigger mentions it — after a reboot the entity will "
                                 "show the stored value while the hardware holds its own default"))
    return checked, findings


def main(argv) -> int:
    if "--self-test" in argv:
        # A CHECK THAT HAS NEVER PRODUCED A POSITIVE IS NOT EVIDENCE (verification.md §13).
        # Strip the on_boot block and confirm both known members are then reported.
        with open(DEFAULT) as f:
            doc = yaml.load(f.read(), Loader=_Loose)
        doc["esphome"].pop("on_boot", None)
        tmp = os.path.join(HERE, ".selftest.yaml")
        with open(tmp, "w") as f:
            yaml.safe_dump(doc, f)
        try:
            checked, findings = audit(tmp)
        finally:
            os.unlink(tmp)
        ok = len(findings) == len(checked) and checked
        print(f"self-test: {len(checked)} controls in the class, "
              f"{len(findings)} reported with on_boot removed -> "
              f"{'DETECTOR WORKS' if ok else 'DETECTOR IS BLIND'}")
        return 0 if ok else 1

    path = next((a for a in argv[1:] if not a.startswith("-")), DEFAULT)
    checked, findings = audit(path)
    print(f"restore+hardware controls checked: {', '.join(checked) or '(none)'}")
    for domain, eid, why in findings:
        print(f"  FAIL  {domain}.{eid}: {why}", file=sys.stderr)
    if findings:
        print("\nAdd an on_boot trigger that pushes the restored state back through the "
              "control, so the register is written by the same path a user tap writes it.",
              file=sys.stderr)
        return 1
    print("all resynced at boot  OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
