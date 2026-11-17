#!/usr/bin/env python3
"""Kitchen Ember family asks — the K1 text-path test (spec 2026-11-17 §4).

Each ask runs through HA's Assist pipeline over WebSocket (`assist_pipeline/run`, start_stage intent,
end_stage tts, input.text, pipeline familiar-ember, the satellite's device_id) and is judged by
its response text and, for actions, by the entity state HA reports afterwards.

This is the TEXT half of K1. It skips wake word, microphone and STT, and it does not play audio
on the board (the TTS URL is produced, never sent to a speaker). The SPOKEN half is a person in
the room; record that in the run log by hand.

Default mode is read-only. --mutate adds asks with side effects, each restored at the end:
kitchen light toggled and put back, a timer set then cancelled (it never rings),
a shopping-list item added then removed.

Exit codes: 0 every ask passed · 1 at least one failed · 3 could not reach HA (UNKNOWN, never 0).
Writes a dated JSON line per run to homeassistant/tests/kitchen_asks.log.jsonl. Prints no token.
"""
import argparse, asyncio, datetime, json, os, re, ssl, sys, time

sys.path.insert(0, os.path.expanduser("~/Projects/ha/tools"))
WS = os.environ.get("HA_WS", "wss://ha.jphe.in:8123/api/websocket")
PIPELINE = "01kyqxx0e1rt0y7echpwxdvs3j"  # familiar-ember
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kitchen_asks.log.jsonl")


class HA:
    def __init__(self, ws):
        self.ws, self.n = ws, 0

    async def call(self, **kw):
        self.n += 1
        await self.ws.send(json.dumps({"id": self.n, **kw}))
        while True:
            m = json.loads(await self.ws.recv())
            if m.get("id") == self.n and m.get("type") == "result":
                if not m.get("success"):
                    raise RuntimeError(f"{kw.get('type')}: {m.get('error')}")
                return m.get("result")

    async def ask(self, text, device_id, timeout=60):
        """One pipeline run; returns (speech, intent_output, tts_ok, error, ms)."""
        self.n += 1
        rid = self.n
        t0 = time.monotonic()
        await self.ws.send(json.dumps({
            "id": rid, "type": "assist_pipeline/run", "start_stage": "intent", "end_stage": "tts",
            "input": {"text": text}, "pipeline": PIPELINE, "device_id": device_id, "timeout": timeout}))
        speech, out, tts_ok, err = None, None, False, None
        while True:
            m = json.loads(await asyncio.wait_for(self.ws.recv(), timeout + 10))
            if m.get("id") != rid:
                continue
            if m.get("type") == "result" and not m.get("success"):
                return None, None, False, str(m.get("error")), int((time.monotonic() - t0) * 1000)
            if m.get("type") != "event":
                continue
            ev = m["event"]
            t, d = ev.get("type"), ev.get("data") or {}
            if t == "intent-end":
                out = d.get("intent_output") or {}
                speech = (((out.get("response") or {}).get("speech") or {}).get("plain") or {}).get("speech")
            elif t == "tts-end":
                tts_ok = bool((d.get("tts_output") or {}).get("url"))
            elif t == "error":
                err = f"{d.get('code')}: {d.get('message')}"
            elif t == "run-end":
                return speech, out, tts_ok, err, int((time.monotonic() - t0) * 1000)


def has(pattern):
    return lambda s: bool(s) and re.search(pattern, s, re.I) is not None


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--satellite", default="assist_satellite.ember_mobile_assist_satellite")
    ap.add_argument("--light", default=None, help="kitchen light entity for the mutate toggle (required with --mutate)")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()
    if a.mutate and not a.light:
        ap.error("--mutate needs --light <entity_id>")

    from ha_token import get_token
    import websockets
    try:
        ws = await websockets.connect(WS, ssl=ssl.create_default_context(), max_size=64 << 20, open_timeout=10)
    except Exception as e:  # noqa: BLE001 — any failure to reach HA is UNKNOWN, not a pass or a fail
        print(f"UNKNOWN: cannot reach HA ({type(e).__name__}: {e})")
        return 3
    async with ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "auth", "access_token": get_token()}))
        if json.loads(await ws.recv()).get("type") != "auth_ok":
            print("UNKNOWN: HA auth failed")
            return 3
        ha = HA(ws)
        ents = await ha.call(type="config/entity_registry/list")
        dev = next((e.get("device_id") for e in ents if e["entity_id"] == a.satellite), None)
        if not dev:
            print(f"UNKNOWN: {a.satellite} not in the entity registry")
            return 3
        states = {s["entity_id"]: s for s in await ha.call(type="get_states")}
        sat_state = states.get(a.satellite, {}).get("state")

        asks = [
            ("weather", "what's the weather like", has(r"\d|sun|cloud|rain|clear|fog|wind|degree")),
            ("kitchen temperature", "what's the temperature in the kitchen", has(r"\d")),
            ("a question", "how many days are there in a leap year", has(r"366")),
            ("house check", "is everything okay in the house", lambda s: bool(s) and len(s) > 10),
        ]
        if a.mutate:
            before = states.get(a.light, {}).get("state")
            verb = "off" if before == "on" else "on"
            asks += [
                ("light " + verb, f"turn {verb} the {states.get(a.light, {}).get('attributes', {}).get('friendly_name', 'kitchen light')}", None),
                ("timer set", "set a timer for 7 minutes", has(r"timer|7|seven")),
                ("timer cancel", "cancel the timer", has(r"cancel|timer|stopp")),
                ("shopping add", "add oat milk to the shopping list", has(r"added|oat milk")),
            ]

        shop = [e for e in states if e.startswith("todo.") and "shopping" in e]
        had_item = set()
        for t in shop:
            try:
                items = (await ha.call(type="todo/item/list", entity_id=t)).get("items", [])
                if any((i.get("summary") or "").strip().lower() == "oat milk" for i in items):
                    had_item.add(t)
            except RuntimeError:
                pass
        results, ok_all = [], True
        for name, text, judge in asks:
            speech, out, tts_ok, err, ms = await ha.ask(text, dev)
            ok = err is None and tts_ok and (judge(speech) if judge else bool(speech))
            if name.startswith("light "):
                await asyncio.sleep(2)
                now = {s["entity_id"]: s for s in await ha.call(type="get_states")}.get(a.light, {}).get("state")
                ok = ok and now == name.split()[1]
            results.append({"ask": name, "text": text, "ok": ok, "ms": ms, "speech": (speech or "")[:200], "error": err, "tts": tts_ok})
            ok_all &= ok
            print(f"{'PASS' if ok else 'FAIL'} {name:20s} {ms:6d} ms  {(err or speech or '')[:110]!r}")

        if a.mutate:  # restore, and say so
            await ha.call(type="call_service", domain="light", service="turn_" + (before or "off"), target={"entity_id": a.light})
            for t in shop:
                if t in had_item:   # it was on the list before the test: leave it
                    continue
                try:
                    await ha.call(type="call_service", domain="todo", service="remove_item",
                                  target={"entity_id": t}, service_data={"item": "oat milk"})
                    print(f"restored: removed 'oat milk' from {t}")
                except RuntimeError:
                    pass
            print(f"restored: {a.light} -> {before}")

    rec = {"ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"), "satellite": a.satellite,
           "satellite_state": sat_state, "mutate": a.mutate, "path": "text", "results": results}
    with open(LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"{sum(r['ok'] for r in results)}/{len(results)} passed; logged to {LOG}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
