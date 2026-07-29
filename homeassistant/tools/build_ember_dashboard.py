#!/usr/bin/env python3
"""Build/refresh the standalone top-level **Ember** HA dashboard.

Source of truth: ../dashboards/ember-hearth.dashboard.json — the full lovelace
config for the Ember Satellite (Hosyond S3 hearth-spirit) and its whole Assist
pipeline. This script is the authoritative regen path (mirrors
build_smol_dashboard.py): it creates the top-level dashboard if absent, then
pushes the config via the WS API — so the repo, not a UI edit, is the source of
truth and a regen never clobbers (the live!=repo divergence trap).

Editing: hand-edit the JSON. Keep `json.dump(d, f, indent=1, ensure_ascii=True)`
if you ever rewrite it programmatically — any other indent or ensure_ascii=False
re-encodes every non-ASCII glyph and buries a 1-tile change in a 300-line diff
(ha skill, gotcha 7). This file is ~40% ember-ramp glyphs, so that matters here.

Card inventory is 100% HA-core card types (markdown / heading / tile / gauge /
history-graph / logbook / entities / button / conditional, sections views with
badges). The only non-core dependency is **card-mod** for the ember palette
(already a registered lovelace resource: /local/luna-cards/card-mod.js) — it
only injects CSS, so if it ever fails to load the cards still render, just
unstyled. No custom *card types* are used, unlike the rooms/devices cockpits.

Notes:
- HA requires a custom dashboard url_path to contain a hyphen (UI + WS enforce it).
- Depends on `packages/ember_backend_health.yaml` for `binary_sensor.ember_reachable`
  (+ `ember_backend`). The mind stage reads its `detail` attribute rather than the
  on/off state, because "off" covers both "up but not ready" and "host asleep" —
  two facts a user needs told apart. Reachability is rendered ONLY while the
  familiar-hosted pipeline is selected: on a cloud agent a sleeping `familiar` is
  irrelevant, so flagging it would be a false alarm.
- The pipeline -> agent/stt/tts/voice map inside the markdown cards is a snapshot
  of `assist_pipeline/pipeline/list` (2026-07-29). If pipelines are added/renamed
  in Settings -> Voice assistants, refresh those two tables.

Usage:
    build_ember_dashboard.py            # create-if-absent + save config
    build_ember_dashboard.py --dry      # print the config, touch nothing
Auth: env HA_TOKEN -> ~/.cache/ha-token-tmp -> `bw get password ha-llat`.
"""
import asyncio, json, os, pathlib, subprocess, sys
import websockets

HA_WS = os.environ.get("HA_WS", "wss://ha.jphe.in:8123/api/websocket")
URL_PATH = "ember-hearth"       # hyphen required by HA
TITLE = "Ember"
ICON = "mdi:fireplace"
CONFIG_FILE = pathlib.Path(__file__).resolve().parent.parent / "dashboards" / "ember-hearth.dashboard.json"


def get_token() -> str:
    tok = os.environ.get("HA_TOKEN", "").strip()
    if tok:
        return tok
    cache = pathlib.Path.home() / ".cache" / "ha-token-tmp"
    if cache.exists() and cache.stat().st_size:
        return cache.read_text().strip()
    return subprocess.check_output(["bw", "get", "password", "ha-llat"], text=True).strip()


def counts(config):
    v = len(config["views"])
    s = sum(len(x.get("sections", [])) for x in config["views"])
    c = sum(len(sec.get("cards", [])) for x in config["views"] for sec in x.get("sections", []))
    return v, s, c


async def main():
    dry = "--dry" in sys.argv
    config = json.load(open(CONFIG_FILE))
    v, s, c = counts(config)
    if dry:
        print(json.dumps(config, indent=1))
        print(f"[dry] url_path={URL_PATH} views={v} sections={s} cards={c}", file=sys.stderr)
        return
    async with websockets.connect(HA_WS, max_size=32 * 1024 * 1024) as ws:
        json.loads(await ws.recv())
        await ws.send(json.dumps({"type": "auth", "access_token": get_token()}))
        assert json.loads(await ws.recv())["type"] == "auth_ok"
        mid = 0

        async def cmd(p):
            nonlocal mid
            mid += 1
            await ws.send(json.dumps({"id": mid, **p}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == mid:
                    return r

        dlist = (await cmd({"type": "lovelace/dashboards/list"}))["result"]
        if not any(d.get("url_path") == URL_PATH for d in dlist):
            cr = await cmd({"type": "lovelace/dashboards/create", "url_path": URL_PATH,
                            "title": TITLE, "icon": ICON, "show_in_sidebar": True,
                            "require_admin": False, "mode": "storage"})
            print("create:", "OK" if cr.get("success") else cr)
        else:
            print(f"dashboard {URL_PATH} already registered")
        r = await cmd({"type": "lovelace/config/save", "url_path": URL_PATH, "config": config})
        print("save:", "OK" if r.get("success") else r)
        print(f"views={v} sections={s} cards={c}")


if __name__ == "__main__":
    asyncio.run(main())
