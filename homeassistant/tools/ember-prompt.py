#!/usr/bin/env python3
"""ember-prompt.py — sync Ember's system prompt between this repo and Home Assistant.

The repo is the SOURCE OF TRUTH: homeassistant/prompts/ember-system.md.j2.

    ./ember-prompt.py --diff      # repo vs live, unified diff, changes nothing
    ./ember-prompt.py --extract   # live -> repo file
    ./ember-prompt.py --deploy    # repo file -> live, immediately, no HA restart

Auth, matching deploy-ha.sh: env HA_TOKEN -> ~/.cache/ha-token-tmp -> `bw get password ha-llat`.

WHY THIS EXISTS AND WHY IT DOESN'T JUST WRITE THE FILE
------------------------------------------------------
Ember's prompt lives in HA's `.storage/core.config_entries`, inside a config *subentry* of the
`extended_openai_conversation` entry. It is not YAML and `deploy-ha.sh` cannot reach it.

Do NOT be tempted to edit that JSON on disk:

  * HA reads the store into memory once at startup and rewrites it from memory on every save.
    A disk edit is therefore ignored until a full restart, and will be silently overwritten by
    the next unrelated config change.
  * There is no "reload" for the config-entry store; `config_entries/reload` re-sets-up the
    entry from the in-memory object, not from disk.

So this tool drives HA's config-subentry **reconfigure flow** over the REST API instead, which
applies live with no restart:

    POST /api/config/config_entries/subentries/flow      {handler:[entry_id,"conversation"],
                                                          subentry_id: ...}   -> flow_id + schema
    POST /api/config/config_entries/subentries/flow/<id> {all fields}          -> reconfigure_successful

⚠ That second POST **replaces subentry.data wholesale**. Every field must be resubmitted or it
is dropped — losing `functions` would silently disable all of Ember's tool calling. This tool
reads the live values, substitutes only `prompt`, and aborts if the live payload is missing any
field the flow's own schema advertises.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

# The Ember agent, not the LiteLLM-Bedrock one ("claude-donkee") which shares the integration.
ENTRY_ID = "01KYQXW03MVY47TGX9SCP6JJYW"
SUBENTRY_ID = "01KYQXW03MN75893YT87YY6XYW"

# ⚠ The API host is the reverse proxy, NOT the SSH host. See deploy-ha.sh's warning: SSHing to
# the public name and writing files succeeds against the *proxy* and changes nothing in HA.
BASE = os.environ.get("HA_URL", "https://ha.jphe.in")

REPO = pathlib.Path(__file__).resolve().parents[2]
PROMPT_FILE = REPO / "homeassistant" / "prompts" / "ember-system.md.j2"


def token() -> str:
    if tok := os.environ.get("HA_TOKEN"):
        return tok.strip()
    cache = pathlib.Path.home() / ".cache" / "ha-token-tmp"
    if cache.is_file():
        return cache.read_text().strip()
    out = subprocess.run(
        ["bw", "get", "password", "ha-llat"], capture_output=True, text=True, check=False
    )
    if out.returncode == 0 and out.stdout.strip():
        return out.stdout.strip()
    sys.exit("no HA token: set HA_TOKEN, or ~/.cache/ha-token-tmp, or unlock bw")


def api(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        BASE + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + token(), "Content-Type": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"HA API {method} {path} -> {e.code}: {e.read().decode()[:400]}")


def abort_flow(flow_id: str) -> None:
    """Best-effort: drop an opened flow we are not going to submit, so they don't pile up."""
    req = urllib.request.Request(
        f"{BASE}/api/config/config_entries/subentries/flow/{flow_id}",
        headers={"Authorization": "Bearer " + token()},
        method="DELETE",
    )
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except (urllib.error.HTTPError, urllib.error.URLError):
        pass


def live_subentry() -> dict:
    """Current subentry data, read through the reconfigure flow's own suggested values."""
    flow = api(
        "POST",
        "/api/config/config_entries/subentries/flow",
        {"handler": [ENTRY_ID, "conversation"], "subentry_id": SUBENTRY_ID},
    )
    if flow.get("type") != "form":
        sys.exit(f"expected a form, got {flow.get('type')}: {flow.get('reason')}")
    fields = [f["name"] for f in flow.get("data_schema") or []]
    data = {
        f["name"]: f["description"]["suggested_value"]
        for f in flow.get("data_schema") or []
        if "suggested_value" in (f.get("description") or {})
    }
    return {"flow_id": flow["flow_id"], "fields": fields, "data": data}


def deploy(new_prompt: str, dry: bool = False) -> None:
    live = live_subentry()
    payload = dict(live["data"])

    missing = [f for f in live["fields"] if f not in payload]
    if missing:
        hint = ""
        if "skills" in missing:
            # The flow only advertises `skills` once skills are loaded from disk, and
            # it carries no suggested value until something has enabled some. Guessing
            # `[]` here would silently disable every skill, so refuse and point at the
            # tool that owns that field.
            hint = (
                "\n   `skills` is advertised but unset: skills exist on disk but none are "
                "enabled.\n   Run `homeassistant/tools/ember-toolkit.py --deploy` first — it "
                "owns that field."
            )
        sys.exit(
            "refusing to deploy: the flow advertises fields with no live value: "
            f"{missing}. Submitting would DROP them. Reconfigure once in the HA UI first."
            + hint
        )
    if "functions" not in payload or not payload["functions"]:
        sys.exit("refusing to deploy: no `functions` in the live payload — would kill tool calling")

    payload["prompt"] = new_prompt
    if dry:
        print(f"would submit {len(payload)} fields: {sorted(payload)}")
        abort_flow(live["flow_id"])
        return

    res = api(
        "POST", f"/api/config/config_entries/subentries/flow/{live['flow_id']}", payload
    )
    if res.get("reason") != "reconfigure_successful":
        sys.exit(f"reconfigure failed: {json.dumps(res)[:400]}")
    print("deployed — live immediately, no restart needed")

    check = live_subentry()
    back = check["data"].get("prompt")
    abort_flow(check["flow_id"])
    if back != new_prompt:
        sys.exit("VERIFY FAILED: prompt read back does not match what was sent")
    print("verified: live prompt matches the repo file")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--diff", action="store_true", help="repo vs live")
    g.add_argument("--extract", action="store_true", help="live -> repo file")
    g.add_argument("--deploy", action="store_true", help="repo file -> live")
    ap.add_argument("--dry-run", action="store_true", help="with --deploy, show and stop")
    args = ap.parse_args()

    if args.extract:
        live = live_subentry()
        prompt = live["data"]["prompt"]
        abort_flow(live["flow_id"])
        PROMPT_FILE.write_text(prompt)
        print(f"wrote {len(prompt)} chars -> {PROMPT_FILE.relative_to(REPO)}")
        return

    repo_prompt = PROMPT_FILE.read_text()

    if args.diff:
        live = live_subentry()
        live_prompt = live["data"]["prompt"]
        abort_flow(live["flow_id"])
        d = list(
            difflib.unified_diff(
                live_prompt.split("\n"),
                repo_prompt.split("\n"),
                fromfile="live (HA .storage)",
                tofile=f"repo ({PROMPT_FILE.relative_to(REPO)})",
                lineterm="",
            )
        )
        print("\n".join(d) if d else "identical")
        sys.exit(1 if d else 0)

    deploy(repo_prompt, dry=args.dry_run)


if __name__ == "__main__":
    main()
