#!/usr/bin/env python3
"""Does the LIVE ember-hearth dashboard match what is committed?

WHY THIS EXISTS — the repo being right is not the same as the dashboard being right.

`dashboards/ember-hearth.dashboard.json` is the source of truth, but what a person looks
at is the copy inside Home Assistant's `.storage`, put there by `build_ember_dashboard.py`
over the WebSocket API. Edit the JSON, commit it, and forget to push it, and the repo and
the dashboard disagree with **nothing to notice** — every check comparing the repo against
the truth passes, because the repo is correct.

That is not hypothetical here. This dashboard **asserted that Hush gates the talk gesture
for hours after the repo JSON had been corrected**, because the fix was committed and the
push never ran. A source of truth that cannot reach the device is not a source of truth.

One member of a class that hit three surfaces in a session — *committed is not deployed,
and deployed is not served.* See `docs/verification.md` §19.

WHAT IT DOES **NOT** DO
  It does not push. A guard that fixes what it finds turns a visible decision into an
  invisible one, and this one would silently overwrite a UI edit somebody made on purpose.
  It reports; a human runs `build_ember_dashboard.py`.

  It does not check that the dashboard is *good*, that its entities exist, or that its
  cards render — only that the config HA holds is the config in git. Claiming more than it
  verifies is the failure this class is made of.

⚠️ It reuses `build_ember_dashboard.py`'s connection and auth rather than re-implementing
them, so the host, the token path and the `url_path` cannot drift between the pusher and
the checker. Two copies of a connection detail is the same hazard as two copies of a
geometry: they agree until one is edited.

RUN
  python3 check_dashboard_deployed.py              # live vs origin/main
  python3 check_dashboard_deployed.py --local      # live vs the working tree
  python3 check_dashboard_deployed.py --self-test  # prove it can fail
"""
import asyncio
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import websockets                                   # noqa: E402
from build_ember_dashboard import HA_WS, URL_PATH, get_token, counts   # noqa: E402

REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                      capture_output=True, text=True, check=True).stdout.strip()
REL = "homeassistant/dashboards/ember-hearth.dashboard.json"


def committed(ref="origin/main"):
    subprocess.run(["git", "-C", REPO, "fetch", "-q"], capture_output=True)
    out = subprocess.run(["git", "-C", REPO, "show", f"{ref}:{REL}"], capture_output=True)
    if out.returncode != 0:
        raise SystemExit(f"cannot read {REL} at {ref}")
    return json.loads(out.stdout)


async def fetch_live():
    async with websockets.connect(HA_WS, max_size=32 * 1024 * 1024) as ws:
        json.loads(await ws.recv())
        await ws.send(json.dumps({"type": "auth", "access_token": get_token()}))
        assert json.loads(await ws.recv())["type"] == "auth_ok", "HA auth failed"
        await ws.send(json.dumps({"id": 1, "type": "lovelace/config", "url_path": URL_PATH}))
        while True:
            r = json.loads(await ws.recv())
            if r.get("id") == 1:
                if not r.get("success"):
                    raise SystemExit(f"HA refused lovelace/config: {r.get('error')}")
                return r["result"]


def norm(cfg):
    """Canonical bytes. HA round-trips key order, so compare structure not formatting."""
    return json.dumps(cfg, sort_keys=True, ensure_ascii=True)


def describe(live, want):
    """-> list of human-readable differences. Empty means in sync."""
    if norm(live) == norm(want):
        return []
    out = []
    lv, ls, lc = counts(live)
    wv, ws_, wc = counts(want)
    if (lv, ls, lc) != (wv, ws_, wc):
        out.append(f"shape: live views={lv} sections={ls} cards={lc}  |  "
                   f"committed views={wv} sections={ws_} cards={wc}")
    for i in range(max(len(live.get("views", [])), len(want.get("views", [])))):
        a = live.get("views", [])[i] if i < len(live.get("views", [])) else None
        b = want.get("views", [])[i] if i < len(want.get("views", [])) else None
        if a is None:
            out.append(f"view {i} '{b.get('title')}' is COMMITTED BUT NOT LIVE")
        elif b is None:
            out.append(f"view {i} '{a.get('title')}' is LIVE BUT NOT COMMITTED")
        elif norm(a) != norm(b):
            ta, tb = a.get("title"), b.get("title")
            where = f"view {i} '{ta}'" + ("" if ta == tb else f" (committed calls it '{tb}')")
            out.append(f"{where} differs")
    if not out:
        out.append("configs differ outside the views array (title, icon or top-level keys)")
    return out


def report(diffs, label):
    if not diffs:
        print(f"live dashboard matches {label}  OK")
        return 0
    print(f"DRIFT: the dashboard Home Assistant is serving is not {label}\n")
    for d in diffs:
        print(f"  {d}")
    print("\n  ⚠️  Someone looking at this dashboard is being shown something the repo does "
          "not say.\n      That is how it asserted a retired Hush behaviour for hours.")
    print("\n  python3 homeassistant/tools/build_ember_dashboard.py   "
          "# this script deliberately does not do it for you")
    print("  ...but check for UI edits first: pushing overwrites them.")
    return 1


def self_test():
    """Demand two results: silent when identical, and reporting when deliberately drifted."""
    want = json.load(open(f"{REPO}/{REL}"))
    clean = describe(want, want)
    tampered = json.loads(json.dumps(want))
    tampered["views"][0]["title"] = tampered["views"][0].get("title", "") + " (self-test)"
    dropped = json.loads(json.dumps(want))
    dropped["views"] = dropped["views"][:-1]
    d1, d2 = describe(want, tampered), describe(want, dropped)
    ok = (len(clean) == 0 and len(d1) > 0 and len(d2) > 0)
    print(f"self-test: identical -> {len(clean)} reported (want 0) | "
          f"retitled view -> {len(d1)} | removed view -> {len(d2)} (both want >0) -> "
          f"{'DETECTOR WORKS' if ok else 'DETECTOR IS BROKEN'}")
    for d in d1 + d2:
        print(f"    caught: {d}")
    return 0 if ok else 1


def main():
    if "--self-test" in sys.argv:
        return self_test()
    ref = None if "--local" in sys.argv else "origin/main"
    want = json.load(open(f"{REPO}/{REL}")) if ref is None else committed(ref)
    label = "the working tree" if ref is None else ref
    live = asyncio.run(fetch_live())
    return report(describe(live, want), label)


if __name__ == "__main__":
    sys.exit(main())
