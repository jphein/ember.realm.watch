#!/usr/bin/env python3
"""test_herald_wording.py — render the driveway herald's REAL wording templates (read from
packages/ember_driveway_watch.yaml) on live HA via /api/template, for synthetic Frigate payloads.

Checks the demotions: stumpish (roadside post) and glareish (night headlights on the solar panels).
`sun.sun` is pinned per case by substitution, so a case runs the same by day or night.
Read-only on the house: /api/template renders and touches nothing.

    homeassistant/tools/test_herald_wording.py [path/to/ember_driveway_watch.yaml]
Token: $HA_TOKEN, else ~/.cache/ha-token-tmp.
"""
import json, os, sys, urllib.request
from pathlib import Path
import yaml

HA = os.environ.get("HA_URL", "https://ha.jphe.in:8123")
PKG = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "packages/ember_driveway_watch.yaml"
TOKEN = os.environ.get("HA_TOKEN") or open(os.path.expanduser("~/.cache/ha-token-tmp")).read().strip()


class Loader(yaml.SafeLoader):
    pass
Loader.add_multi_constructor("!", lambda l, s, n: None)  # !secret etc. are irrelevant here

doc = yaml.load(PKG.read_text(), Loader=Loader)
auto = next(a for a in doc["automation"] if a.get("id") == "ember_driveway_watch")
v = auto["variables"]
msg = next(s["data"]["message"] for s in auto["action"] if isinstance(s, dict) and s.get("action") == "script.ember_broadcast")


def render(after, night):
    sun = "true" if night else "false"
    fix = lambda t: t.replace("is_state('sun.sun', 'below_horizon')", sun).replace("is_state('sun.sun','below_horizon')", sun)
    tpl = ("{% set trigger = " + json.dumps({"payload_json": {"type": "new", "after": after}}) + " %}"
           "{% set label = trigger.payload_json.after.label %}"
           "{% set place = 'up the drive' %}"
           "{% set person_lines = ['Someone approaches on foot, up the drive.'] %}"
           "{% set vehicle_lines = ['A car approaches up the drive.'] %}{% set animal_lines = ['x'] %}{% set bear_lines = ['x'] %}"
           "{% set stumpish %}" + fix(v["stumpish"]) + "{% endset %}"
           "{% set glareish %}" + fix(v.get("glareish", "false")) + "{% endset %}" + fix(msg))
    req = urllib.request.Request(f"{HA}/api/template", json.dumps({"template": tpl}).encode(),
                                 {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=15).read().decode().strip()


P = lambda box, area=1000, label="person": {"camera": "driveway", "label": label, "box": box, "area": area}
GLARE, POST = "headlights on the solar panels", "roadside post"
CASES = [
    ("night, person box over the panels (10-15 20:42 oxgxxx)", P([40, 88, 220, 317], 41220), True, GLARE),
    ("DAY, same box over the panels → plain wording", P([40, 88, 220, 317], 41220), False, None),
    ("night, person far right of the frame → plain", P([560, 150, 640, 330], 14400), True, None),
    ("night, CAR over the panels → vehicle wording, no hedge", P([40, 88, 220, 317], 41220, "car"), True, None),
    ("night, roadside post box → post wording wins", P([451, 219, 460, 251], 588), True, POST),
    ("day, roadside post box → post wording", P([451, 219, 460, 251], 588), False, POST),
    ("night, malformed box → plain (fail-open)", P(["x", 1, 2, 3], 10), True, None),
]
fail = 0
for name, after, night, want in CASES:
    out = render(after, night)
    got = GLARE if GLARE in out else POST if POST in out else None
    ok = got == want
    fail += not ok
    print(f"{'PASS' if ok else 'FAIL'}  {name}  -> {out[:70]!r}")
print(f"{len(CASES) - fail}/{len(CASES)} passed")
sys.exit(1 if fail else 0)
