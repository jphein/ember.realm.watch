#!/usr/bin/env python3
"""ember-toolkit.py — sync Ember's tools and skills between this repo and Home Assistant.

The repo is the SOURCE OF TRUTH:
    homeassistant/functions/ember-functions.yaml   -> the subentry's `functions` field
    homeassistant/skills/<name>/SKILL.md           -> /config/extended_openai_conversation/skills/

    ./ember-toolkit.py --diff        # repo vs live, changes nothing
    ./ember-toolkit.py --deploy      # skills to the VM, then functions + enabled skills, live
    ./ember-toolkit.py --extract     # live functions -> repo file
    ./ember-toolkit.py --deploy --dry-run

Auth, matching deploy-ha.sh and ember-prompt.py:
    env HA_TOKEN -> ~/.cache/ha-token-tmp -> `bw get password ha-llat`.

No HA restart at any point. Verified 2026-08-02.

WHY THE ORDER IN --deploy IS NOT NEGOTIABLE
-------------------------------------------
Discovered by reading the integration (v3.0.0) rather than guessing, because the
failure mode is silent:

  1. A skill is a DIRECTORY containing `SKILL.md` with YAML frontmatter carrying a
     `description`. The skill's *name* is its directory name; the frontmatter name,
     if any, is ignored. Files directly in the skills directory are skipped, which
     is why the stock `README.md` there is harmless.
  2. `SkillManager` only rescans on the `extended_openai_conversation.reload_skills`
     service. Writing files changes nothing until then.
  3. A loaded skill is still not *offered* to Ember. The prompt lists
     `subentry.data["skills"]`, an explicit enabled-list, and the conversation
     entity filters loaded skills against it.
  4. The config-flow schema builds that field's options from the skills currently
     loaded — and `config_flow.py` DROPS the `skills` field entirely when none are
     loaded. So a deploy that writes the enabled-list before reloading is rejected
     by voluptuous, or worse, silently offers nothing.

Hence: write files -> reload_skills -> submit functions AND the enabled-list.

⚠ The subentry submit REPLACES `subentry.data` wholesale. Every field must be
resubmitted or it is dropped — losing `functions` would disable Ember's tool
calling, and losing `prompt` would revert the persona to the integration default.
This tool reads the live values, substitutes only `functions` and `skills`, and
aborts if the flow advertises a field it has no live value for.
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request

import yaml

# The Ember agent, not the LiteLLM-Bedrock one ("claude-donkee") which shares the
# integration. Same ids ember-prompt.py uses.
ENTRY_ID = "01KYQXW03MVY47TGX9SCP6JJYW"
SUBENTRY_ID = "01KYQXW03MN75893YT87YY6XYW"

# ⚠ Two different hosts, and mixing them up is the classic failure here.
#   HA_URL      -> the Caddy edge, for the HTTP API.
#   HA_SSH_HOST -> the HAOS VM itself, for file copies. SSHing to the edge
#                  succeeds and writes files onto the wrong machine.
BASE = os.environ.get("HA_URL", "https://ha.jphe.in")
SSH_HOST = os.environ.get("HA_SSH_HOST", "jp@ha.lan")

# The integration's working directory, from its own const.py:
#   DEFAULT_WORKING_DIRECTORY = "extended_openai_conversation/"  (under config_dir)
#   DEFAULT_SKILLS_DIRECTORY  = "skills"
REMOTE_SKILLS_DIR = "/config/extended_openai_conversation/skills"

REPO = pathlib.Path(__file__).resolve().parents[2]
FUNCTIONS_FILE = REPO / "homeassistant" / "functions" / "ember-functions.yaml"
SKILLS_DIR = REPO / "homeassistant" / "skills"

# A tool list without this is a broken Ember: it is how she controls the house.
REQUIRED_TOOL = "execute_services"


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
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"HA API {method} {path} -> {e.code}: {e.read().decode()[:400]}")


def abort_flow(flow_id: str) -> None:
    """Drop an opened flow we are not going to submit, so they don't pile up."""
    req = urllib.request.Request(
        f"{BASE}/api/config/config_entries/subentries/flow/{flow_id}",
        headers={"Authorization": "Bearer " + token()},
        method="DELETE",
    )
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except (urllib.error.HTTPError, urllib.error.URLError):
        pass


def live_subentry(retries: int = 6) -> dict:
    """Current subentry data, read through the reconfigure flow's own suggested values.

    Retries on `entry_not_loaded`: a successful submit makes HA reload the config
    entry, and for a second or two afterwards the flow cannot be opened. Read back
    too eagerly and a deploy that fully worked reports a scary abort. Observed
    2026-08-02 on the first real deploy.
    """
    for attempt in range(retries):
        flow = api(
            "POST",
            "/api/config/config_entries/subentries/flow",
            {"handler": [ENTRY_ID, "conversation"], "subentry_id": SUBENTRY_ID},
        )
        if flow.get("type") == "form":
            break
        if flow.get("reason") == "entry_not_loaded" and attempt < retries - 1:
            time.sleep(1.5)
            continue
        sys.exit(f"expected a form, got {flow.get('type')}: {flow.get('reason')}")
    schema = flow.get("data_schema") or []
    fields = [f["name"] for f in schema]
    data = {
        f["name"]: f["description"]["suggested_value"]
        for f in schema
        if "suggested_value" in (f.get("description") or {})
    }
    # The options voluptuous will accept for `skills`; submitting a name that is
    # not loaded is rejected, so surface the list for a legible error.
    skill_options: list[str] = []
    for f in schema:
        if f["name"] == "skills":
            sel = (f.get("selector") or {}).get("select") or {}
            skill_options = [
                o["value"] if isinstance(o, dict) else o for o in sel.get("options", [])
            ]
    return {
        "flow_id": flow["flow_id"],
        "fields": fields,
        "data": data,
        "skill_options": skill_options,
    }


def repo_functions() -> str:
    """The repo's tool list, validated before it can reach HA.

    Trailing newlines are stripped: HA stores the submitted string without them,
    so keeping them here would make `--diff` report a permanent one-line
    difference that no edit could ever resolve.
    """
    text = FUNCTIONS_FILE.read_text().rstrip("\n")
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as e:
        sys.exit(f"{FUNCTIONS_FILE.name} is not valid YAML: {e}")
    if not isinstance(parsed, list) or not parsed:
        sys.exit(f"{FUNCTIONS_FILE.name} must be a non-empty YAML list of tools")
    names = []
    for i, tool in enumerate(parsed):
        if not isinstance(tool, dict) or "spec" not in tool or "function" not in tool:
            sys.exit(f"tool #{i} is missing `spec` or `function`")
        if "type" not in tool["function"]:
            sys.exit(f"tool `{tool['spec'].get('name')}` has no function type")
        names.append(tool["spec"]["name"])
    if REQUIRED_TOOL not in names:
        sys.exit(
            f"refusing to deploy: `{REQUIRED_TOOL}` is missing from "
            f"{FUNCTIONS_FILE.name}. That is how Ember controls the house — "
            "the field is replaced wholesale, so omitting it disables it."
        )
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        sys.exit(f"duplicate tool names: {sorted(dupes)}")
    return text


def repo_skills() -> list[pathlib.Path]:
    """Skill directories in the repo, each of which must contain SKILL.md."""
    if not SKILLS_DIR.is_dir():
        return []
    out = []
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir():
            continue
        if not (d / "SKILL.md").is_file():
            print(f"!! {d.name}/ has no SKILL.md — the loader will skip it", file=sys.stderr)
            continue
        # The loader requires frontmatter with a description; catch that here
        # rather than discovering it as a silently missing skill.
        head = (d / "SKILL.md").read_text()
        if not head.startswith("---"):
            sys.exit(f"{d.name}/SKILL.md has no YAML frontmatter — loader will reject it")
        fm = head.split("---", 2)
        try:
            meta = yaml.safe_load(fm[1]) or {}
        except yaml.YAMLError as e:
            sys.exit(f"{d.name}/SKILL.md frontmatter is not valid YAML: {e}")
        if not meta.get("description"):
            sys.exit(f"{d.name}/SKILL.md frontmatter has no `description` — loader requires it")
        if len(d.name) > 64:
            sys.exit(f"skill name `{d.name}` exceeds the loader's 64-character limit")
        out.append(d)
    return out


def push_skills(skills: list[pathlib.Path], dry: bool) -> None:
    """Copy skill directories to the VM. `sudo`, because /config is root-owned."""
    for d in skills:
        remote = f"{REMOTE_SKILLS_DIR}/{d.name}"
        for f in sorted(p for p in d.rglob("*") if p.is_file()):
            rel = f.relative_to(d)
            target = f"{remote}/{rel}"
            if dry:
                print(f"++  would copy {d.name}/{rel}")
                continue
            subprocess.run(
                ["ssh", SSH_HOST, f"sudo mkdir -p {pathlib.PurePosixPath(target).parent}"],
                check=True,
            )
            with f.open("rb") as fh:
                subprocess.run(
                    ["ssh", SSH_HOST, f"sudo tee {target} >/dev/null"],
                    stdin=fh,
                    check=True,
                )
            print(f"->  copied {d.name}/{rel}")


def reload_skills() -> int:
    """Ask the integration to rescan. Returns how many it loaded."""
    res = api(
        "POST",
        "/api/services/extended_openai_conversation/reload_skills?return_response",
        {},
    )
    loaded = (res.get("service_response") or {}).get("loaded_skills")
    print(f"   reload_skills: {loaded} loaded")
    return loaded if isinstance(loaded, int) else -1


def deploy(dry: bool = False) -> None:
    functions = repo_functions()
    skills = repo_skills()
    want_skills = [d.name for d in skills]
    print(f"==> {len(yaml.safe_load(functions))} tools, {len(skills)} skills: {want_skills}")

    push_skills(skills, dry)
    if not dry:
        loaded = reload_skills()
        if loaded != -1 and loaded < len(want_skills):
            sys.exit(
                f"refusing to continue: asked to enable {len(want_skills)} skills but the "
                f"integration loaded {loaded}. A skill whose frontmatter it rejected is "
                "logged as a warning in HA's log."
            )

    live = live_subentry()
    payload = dict(live["data"])

    missing = [f for f in live["fields"] if f not in payload and f != "skills"]
    if missing:
        abort_flow(live["flow_id"])
        sys.exit(
            "refusing to deploy: the flow advertises fields with no live value: "
            f"{missing}. Submitting would DROP them. Reconfigure once in the HA UI first."
        )
    if "prompt" not in payload or not payload["prompt"]:
        abort_flow(live["flow_id"])
        sys.exit("refusing to deploy: no `prompt` in the live payload — would reset the persona")

    if "skills" in live["fields"]:
        unknown = [s for s in want_skills if s not in live["skill_options"]]
        if unknown and not dry:
            abort_flow(live["flow_id"])
            sys.exit(
                f"the integration has not loaded these skills: {unknown}. "
                f"It offers: {live['skill_options']}. Check HA's log for a frontmatter warning."
            )
        payload["skills"] = [s for s in want_skills if s in live["skill_options"]]
    elif want_skills and not dry:
        abort_flow(live["flow_id"])
        sys.exit(
            "the flow advertises no `skills` field even after reload_skills, which means "
            "the integration loaded none. Skills would be deployed to disk but never offered."
        )

    payload["functions"] = functions

    if dry:
        print(f"would submit {len(payload)} fields: {sorted(payload)}")
        print(f"  functions: {len(functions)} chars")
        print(f"  skills:    {payload.get('skills')}")
        abort_flow(live["flow_id"])
        return

    res = api(
        "POST", f"/api/config/config_entries/subentries/flow/{live['flow_id']}", payload
    )
    if res.get("reason") != "reconfigure_successful":
        sys.exit(f"reconfigure failed: {json.dumps(res)[:400]}")
    print("deployed — live immediately, no restart needed")

    check = live_subentry()
    abort_flow(check["flow_id"])
    if check["data"].get("functions") != functions:
        sys.exit("VERIFY FAILED: live functions do not match the repo file")
    got = check["data"].get("skills") or []
    if sorted(got) != sorted(payload.get("skills") or []):
        sys.exit(f"VERIFY FAILED: live skills {got} != submitted {payload.get('skills')}")
    print(f"verified: {len(yaml.safe_load(functions))} tools live, skills enabled: {got}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--diff", action="store_true", help="repo vs live")
    g.add_argument("--extract", action="store_true", help="live functions -> repo file")
    g.add_argument("--deploy", action="store_true", help="repo -> live")
    ap.add_argument("--dry-run", action="store_true", help="with --deploy, show and stop")
    args = ap.parse_args()

    if args.extract:
        live = live_subentry()
        fns = live["data"].get("functions") or ""
        abort_flow(live["flow_id"])
        FUNCTIONS_FILE.write_text(fns)
        print(f"wrote {len(fns)} chars -> {FUNCTIONS_FILE.relative_to(REPO)}")
        return

    if args.diff:
        repo = repo_functions()
        live = live_subentry()
        live_fns = live["data"].get("functions") or ""
        live_skills = live["data"].get("skills") or []
        abort_flow(live["flow_id"])
        d = list(
            difflib.unified_diff(
                live_fns.split("\n"),
                repo.split("\n"),
                fromfile="live (HA .storage)",
                tofile=f"repo ({FUNCTIONS_FILE.relative_to(REPO)})",
                lineterm="",
            )
        )
        want = [p.name for p in repo_skills()]
        skills_differ = sorted(live_skills) != sorted(want)
        if d:
            print("\n".join(d))
        else:
            print("functions: identical")
        print(f"skills live={sorted(live_skills)} repo={sorted(want)}"
              f"{'  <- DIFFERS' if skills_differ else '  (identical)'}")
        sys.exit(1 if (d or skills_differ) else 0)

    deploy(dry=args.dry_run)


if __name__ == "__main__":
    main()
