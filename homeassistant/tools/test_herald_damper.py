#!/usr/bin/env python3
"""test_herald_damper.py — simulate the driveway herald's REPEAT-SPOT DAMPER (ember_driveway_watch.yaml) on live HA.

Pulls the REAL templates from the package — the counter's new_spot, the herald's spot_n + message, the
muted-record value, the mover's condition + spot decrement — and renders them via /api/template with the
input_text state, now() and sun.sun substituted per step, so a whole night can be replayed in seconds.
Read-only on the house (/api/template renders, touches nothing).

    homeassistant/tools/test_herald_damper.py [path/to/ember_driveway_watch.yaml]
Token: $HA_TOKEN, else ~/.cache/ha-token-tmp.
"""
import json, os, sys, urllib.request
from pathlib import Path
import yaml

HA = os.environ.get("HA_URL", "https://ha.jphe.in:8123")
PKG = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "packages/ember_driveway_watch.yaml"
TOKEN = os.environ.get("HA_TOKEN") or open(os.path.expanduser("~/.cache/ha-token-tmp")).read().strip()


class L(yaml.SafeLoader):
    pass
L.add_multi_constructor("!", lambda l, s, n: None)
doc = yaml.load(PKG.read_text(), Loader=L)
A = {a["id"]: a for a in doc["automation"]}
herald = A["ember_driveway_watch"]
V = herald["variables"]
bc = next(x for x in herald["action"] if isinstance(x, dict) and x.get("action") == "script.ember_broadcast")
MSG = bc["data"]["message"]
SILENT = bc["data"].get("silent", "false")
MUTED_REC = next((x["then"][0]["data"]["value"] for x in herald["action"] if isinstance(x, dict) and "if" in x), None)
CNT = A.get("ember_herald_spot_counter")
MOV = A.get("ember_herald_spot_mover")


def render(tpl, after, mtype, spot, muted, now):
    t = (tpl.replace("states('input_text.ember_herald_spot')", json.dumps(json.dumps(spot)))
            .replace("states('input_text.ember_herald_muted')", json.dumps(json.dumps(muted)))
            .replace("now().timestamp()", str(now))
            .replace("is_state('sun.sun', 'below_horizon')", "true").replace("is_state('sun.sun','below_horizon')", "true"))
    pre = ("{% set trigger = " + json.dumps({"payload_json": {"type": mtype, "after": after}}).replace("null", "none") + " %}"
           "{% set label = trigger.payload_json.after.label %}{% set place = 'up the drive' %}"
           "{% set person_lines = ['PLAIN'] %}{% set vehicle_lines = ['CAR'] %}{% set animal_lines = ['x'] %}{% set bear_lines = ['x'] %}"
           "{% set stumpish = false %}{% set glareish = false %}")
    if "spot_n" in tpl and "{% set spot_n" not in tpl and tpl is not V.get("spot_n"):
        pre += "{% set spot_n %}" + render.spot_n_src + "{% endset %}"
    req = urllib.request.Request(f"{HA}/api/template", json.dumps({"template": pre + t}).encode(),
                                 {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=15).read().decode().strip()


def sub(tpl, spot, muted, now):  # spot_n source with state substituted, for embedding
    return (tpl.replace("states('input_text.ember_herald_spot')", json.dumps(json.dumps(spot)))
               .replace("now().timestamp()", str(now)))


def P(cx, cy, tid, has_snapshot=True, box=True, w=110, h=150):
    # default = a FLOATING near-lens box like the cobweb (area 16500 px, bottom 225 px)
    b = [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2] if box else None
    return {"id": tid, "camera": "driveway", "label": "person", "has_snapshot": has_snapshot, "box": b}


def step(state, t, after, moves_to=None):
    """One confirmed track: herald (spot_n/message/silent) → counter → (muted record) → optional move."""
    spot, muted = state
    render.spot_n_src = sub(V.get("spot_n", "0"), spot, muted, t)
    n = int(float(render(V.get("spot_n", "0"), after, "new", spot, muted, t) or 0)) if "spot_n" in V else 0
    msg = render(MSG, after, "new", spot, muted, t)
    silent = render(str(SILENT), after, "new", spot, muted, t) == "True"
    if CNT:
        cond = CNT["condition"][0]["value_template"]
        if render(cond, after, "new", spot, muted, t) == "True":
            ns = render(CNT["action"][0]["variables"]["new_spot"], after, "new", spot, muted, t).strip()
            if ns != "KEEP":
                spot = json.loads(ns)
    if silent and MUTED_REC:
        muted = json.loads(render(MUTED_REC, after, "new", spot, muted, t))
    spoke_late = False
    if moves_to and MOV:
        upd = dict(after, box=P(*moves_to, after["id"])["box"])
        if render(MOV["condition"][0]["value_template"], upd, "update", spot, muted, t + 5) == "True":
            if isinstance(spot, dict) and spot.get("id") == after["id"]:
                spot = json.loads(render(MOV["action"][1]["then"][0]["data"]["value"], upd, "update", spot, muted, t + 5))
            if isinstance(muted, list) and any(m.get("id") == after["id"][-24:] for m in muted):
                muted = [m for m in muted if m.get("id") != after["id"][-24:]]
                spoke_late = True
    kind = "hedged" if "cobweb" in msg else "plain" if "PLAIN" in msg else msg[:30]
    return (spot, muted), {"n": n, "kind": kind, "silent": silent, "spoke_late": spoke_late}


T0, SPOT, ELSE = 1_800_000_000, (330, 150), (600, 380)
checks = []

# 1. a static cobweb spot, one track every 40 s → plain, plain, hedged ×3, then hedged+silent
st, out = ({}, {}), []
for i in range(8):
    st, r = step(st, T0 + 40 * i, P(SPOT[0] + (i % 3) * 4, SPOT[1], f"web{i}"))
    out.append(r)
checks.append(("static spot: tracks 1-2 plain", all(r["kind"] == "plain" and not r["silent"] for r in out[:2])))
checks.append(("static spot: tracks 3-5 hedged, still spoken", all(r["kind"] == "hedged" and not r["silent"] for r in out[2:5])))
checks.append(("static spot: track 6+ hedged and SILENT", all(r["kind"] == "hedged" and r["silent"] for r in out[5:])))

# 2. a person crossing the muted spot: silent at first (looks like the cobweb), then MOVES → spoken late
st2, r = step(st, T0 + 40 * 8, P(*SPOT, "walker"), moves_to=(SPOT[0] + 120, SPOT[1] + 90))
checks.append(("moving track in the spot: spoken once it moves", r["spoke_late"]))
checks.append(("moving track is taken back out of the count", st2[0].get("n") == st[0].get("n")))

# 2b. Oracle R1: two tracks muted, then the FIRST one moves → still spoken (records kept, not overwritten)
stA, rA = step(st, T0 + 40 * 8, P(*SPOT, "mutedA"))
stB, rB = step(stA, T0 + 40 * 9, P(SPOT[0] + 3, SPOT[1], "mutedB"))
mv = dict(P(SPOT[0] + 140, SPOT[1] + 60, "mutedA"))
spoken_A = render(MOV["condition"][0]["value_template"], mv, "update", stB[0], stB[1], T0 + 40 * 9 + 5) == "True" if MOV else False
checks.append(("R1: 2 muted, the FIRST later moves → still spoken", rA["silent"] and rB["silent"] and spoken_A))

# 3. a person ELSEWHERE while the spot is active: plain + spoken, and the damper is NOT reset
st3, r = step(st, T0 + 40 * 8, P(*ELSE, "elsewhere"))
checks.append(("track elsewhere: plain and spoken", r["kind"] == "plain" and not r["silent"]))
checks.append(("track elsewhere: damper state unchanged", st3[0] == st[0]))

# 3b. Oracle F1: a SMALL distant walker in the muted cobweb spot → plain + SPOKEN, never damped, not counted
st3b, r = step(st, T0 + 40 * 8, P(*SPOT, "farwalker", w=30, h=70))
checks.append(("small (distant) walker in the muted spot: plain + spoken", r["kind"] == "plain" and not r["silent"]))
checks.append(("small walker is not counted", st3b[0] == st[0]))
# 3c. a person close to the camera (box reaching the ground) in the spot → plain + spoken
st3c, r = step(st, T0 + 40 * 8, P(SPOT[0], 330, "nearwalker", w=160, h=300))
checks.append(("near walker (box to the ground) in the spot: plain + spoken", r["kind"] == "plain" and not r["silent"]))

# 3d. Oracle F2: no cooldown after a silent herald
dl = next(x for x in herald["action"] if isinstance(x, dict) and "delay" in x)["delay"]["minutes"]
render.spot_n_src = "7"
cool = render(dl.replace("spot_n | default(0)", "7 | default(0)"), P(*SPOT, "c"), "new", st[0], st[1], T0)
checks.append(("silent herald → cooldown 0", cool.strip() == "0"))

# 4. missing coordinates → plain, spoken, state untouched (fail-open)
st4, r = step(st, T0 + 40 * 8, P(*SPOT, "nobox", box=False))
checks.append(("missing box: plain + spoken (fail-open)", r["kind"] == "plain" and not r["silent"] and st4[0] == st[0]))

# 5. garbage in the helper (not JSON) → read as empty → plain, spoken (fail-open)
st5, r = step(("garbage", "garbage"), T0, P(*SPOT, "fresh"))
checks.append(("garbage helper state: plain + spoken (fail-open)", r["kind"] == "plain" and not r["silent"]))

# 6. the spot goes quiet for 31 min → damping ends (new spot, plain again)
st6, r = step(st, T0 + 40 * 7 + 31 * 60, P(*SPOT, "later"))
checks.append(("after 31 quiet minutes: plain again", r["kind"] == "plain" and not r["silent"]))

fail = 0
for name, ok in checks:
    fail += not ok
    print(("PASS " if ok else "FAIL ") + name)
print(f"{len(checks) - fail}/{len(checks)} passed")
sys.exit(1 if fail else 0)
