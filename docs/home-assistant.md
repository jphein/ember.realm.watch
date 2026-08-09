# Ember — the Home Assistant side

Everything Home Assistant needs to run Ember: what the repo ships, the manual steps it
can't ship, how the voice pipeline is put together, and what to do when it goes quiet.
The device firmware is documented separately; this is the HA half.

- [1 · What this repo ships](#1--what-this-repo-ships)
- [2 · Prerequisites not in this repo](#2--prerequisites-not-in-this-repo)
- [3 · Deploying](#3--deploying)
- [4 · Secrets](#4--secrets)
- [5 · Verifying a fresh install](#5--verifying-a-fresh-install)
- [6 · The voice pipeline](#6--the-voice-pipeline)
- [7 · Troubleshooting](#7--troubleshooting)
- [8 · Why copy and not symlink](#8--why-copy-and-not-symlink)
- [9 · The toolkit — tools and skills](#9--the-toolkit--tools-and-skills)

> **The repo cannot fully describe a working Ember.** About half the HA-side
> configuration lives in HA's own `.storage`, created through the UI, and isn't
> expressible as a repo file: the Assist pipeline, the conversation-agent entry, the
> add-ons, the HACS integration. Those are §2. The repo covers the packages, the
> dashboard, the **system prompt**, and the deploy path.
>
> ⚠️ **One exception inside that split, and it is the one that has already cost us.** The
> conversation-agent entry is `.storage`-only, but its `prompt` field is *not* — since
> 2026-07-31 it is repo-tracked at
> [`../homeassistant/prompts/ember-system.md.j2`](../homeassistant/prompts/ember-system.md.j2)
> and deployed live with `ember-prompt.py --deploy`. Before that, nothing in the repo
> contained the string `You are Ember`: a measured prompt-cache fix was made against it, its
> reasoning was written into [§6.3](#63-the-persona-and-the-one-rule), and the prompt itself
> was never captured — which is why [#37](https://github.com/jphein/ember.realm.watch/issues/37)
> had to re-derive from scratch what §6.3 already half-knew. **An artifact absent from the
> repo's own inventory is one nobody thinks to check.**

---

## 1 · What this repo ships

| Repo path | Deployed to | Carries |
|:--|:--|:--|
| `homeassistant/packages/ember_backend_health.yaml` | `/homeassistant/packages/` | `binary_sensor.ember_backend`, `binary_sensor.ember_reachable` |
| `homeassistant/packages/ember_persona.yaml` | `/homeassistant/packages/` | `input_text.ember_persona_extra`, `input_text.ember_say` |
| `homeassistant/packages/ember_announce.yaml` | `/homeassistant/packages/` | `script.ember_announce`, `…_if_awake`, `script.ember_say` |
| `homeassistant/dashboards/ember-hearth.dashboard.json` | HA `.storage`, over WebSocket | the `ember-hearth` dashboard — 4 views (Hearth, Voice Pipeline, Diagnostics, Fleet) |
| `homeassistant/prompts/ember-system.md.j2` | HA `.storage`, over the REST config-flow API | Ember's **system prompt** — the persona, the device manifest, the Environment State block |
| `homeassistant/packages/ember_toolkit.yaml` | `/homeassistant/packages/` | `sensor.ember_print_job`; `rest_command.palace_search`, `…spyglass_cams` — the credential-bearing data plane behind Ember's tools ([§9](#9--the-toolkit--tools-and-skills)) |
| `homeassistant/packages/ember_print_context.yaml` | `/homeassistant/packages/` | `automation.ember_context_3d_print_running` — the persona-knob pattern ([§9.5](#95-the-persona-knob-channel)) |
| `homeassistant/functions/ember-functions.yaml` | HA `.storage`, over the REST config-flow API | Ember's **tool definitions** — 10 tools ([§9.2](#92-the-tools)) |
| `homeassistant/skills/*/SKILL.md` | `/homeassistant/extended_openai_conversation/skills/` | Ember's **skills** — `printer-watch`, `morning-report`, `whos-home` ([§9.3](#93-the-skills)) |
| `homeassistant/patches/eoc-aliases-sentinel.patch` | applied by hand on the HA VM | staged `helpers.py` fix; needs a restart, so it waits |
| `homeassistant/tools/deploy-ha.sh` | — | copies packages + reloads only what changed |
| `homeassistant/tools/ember-prompt.py` | — | `--diff` / `--extract` / `--deploy` the system prompt, live, no restart |
| `homeassistant/tools/ember-toolkit.py` | — | `--diff` / `--extract` / `--deploy` the tools + skills, live, no restart |
| `homeassistant/tools/build_ember_dashboard.py` | — | creates-if-absent + pushes the dashboard |

**This repo is the source of truth.** Packages are *copied* to the VM, not symlinked —
see [§8](#8--why-copy-and-not-symlink).

### Host names — read this before you type a deploy command

`ha.jphe.in` and the Home Assistant VM are **not the same machine.**

| Name | Actually is | Use for |
|:--|:--|:--|
| `ha.jphe.in` | the **Caddy reverse proxy**, a different host | the HTTP / WebSocket API only |
| `ha.lan` | the **Home Assistant VM** itself | **SSH and file copies** |

`ssh jp@ha.jphe.in` *succeeds* and lands you on the proxy. A deploy aimed there would
`sudo tee` the packages onto the wrong host, report success, and change nothing in Home
Assistant. Both tools here already use the right name for each job.

First SSH by hostname may fail with *Host key verification failed* if `known_hosts` has
only the IP form. One-time:

```bash
ssh-keyscan -H ha.lan >> ~/.ssh/known_hosts
```

---

## 2 · Prerequisites not in this repo

Do these first; the packages reference them and sit `unavailable` otherwise.

### 2.1 Add-ons
Settings → Add-ons:
- ~~**Piper** — TTS add-on.~~ **Moved to `familiar` 2026-08-09** (the VM was
  overloaded and TTS inference was part of why): `wyoming-piper` at
  `familiar:10200`, voice bumped `en_GB-cori-medium` → **`en_GB-cori-high`** —
  the quality tier the VM could never afford is free on 24 idle cores. Unit:
  familiar.realm.watch `ops/systemd/units/wyoming-piper.service`. HA side:
  Wyoming integration → `familiar.lan:10200` → `tts.piper_2`. The add-on is
  STOPPED, not uninstalled — one click (or `hassio.addon_stop`'s twin
  `addon_start`) brings it back as a fallback with the old `tts.piper` entity.
- ~~**vosk** — STT.~~ **Replaced 2026-08-09** by **Parakeet on `familiar`** — not an
  add-on. `wyoming-onnx-asr` serves NVIDIA `parakeet-tdt-0.6b-v2` (the current
  local-English state of the art; vosk was the best *add-on* but add-ons were the
  wrong pond to fish in) over the Wyoming protocol from `familiar:10300`, CPU-only
  so the GPUs stay with the inference lanes. Unit + the save-audio debug patch are
  owned by **familiar.realm.watch** (`ops/systemd/units/wyoming-onnx-asr.service`,
  `ops/patches/`) — cross-referenced, never mirrored, per the standing boundary.
  HA side: Settings → Integrations → Wyoming → host `familiar.lan`, port `10300`.
  The vosk add-on can stay installed as a fallback engine; nothing selects it.

  🔊 **To hear exactly what Ember's mic delivered to STT** (the thing JP asked for):
  every utterance is teed on `familiar` to `/opt/wyoming-onnx-asr/debug-audio/`
  as `utt-<ts>.wav` + a `.txt` sidecar holding the transcript it produced —
  newest 40 kept. `scp` one over and play it; a wrong transcript can be replayed
  against the exact audio that produced it.
- **openWakeWord** — the pipeline names it even though Ember is push-to-talk ([§6](#6--the-voice-pipeline)).

### 2.2 HACS integration
**[extended_openai_conversation](https://github.com/jekalmin/extended_openai_conversation)**
— install via HACS, then restart HA. Needed instead of the core OpenAI integration
because Ember must point at an arbitrary `base_url` with a custom model name.

### 2.3 The conversation agent
Settings → Devices & Services → Add integration → Extended OpenAI Conversation:

| Field | Value |
|:--|:--|
| Name | `Ember (familiar local)` |
| `base_url` | `http://ubox0.lan:4000/v1` |
| API key | the LiteLLM master key — **from the vault, never from this repo** |

Then its **conversation subentry** → Reconfigure:

| Field | Value |
|:--|:--|
| `chat_model` | `ember` (a LiteLLM alias, not an upstream model id) |
| `context_threshold` | `40000` |
| `context_truncate_strategy` | `clear` |
| prompt | leave the default here — then `homeassistant/tools/ember-prompt.py --deploy` writes the real one from [`../homeassistant/prompts/ember-system.md.j2`](../homeassistant/prompts/ember-system.md.j2). Structure and the one hard rule: [§6.3](#63-the-persona-and-the-one-rule) |

⚠ `.lan` is required — HAOS does not resolve the bare `ubox0`. Don't substitute an IP:
hosts here have moved before and a hardcoded literal cost a whole debugging session.

### 2.4 The Assist pipeline
Settings → Voice assistants → Add assistant, named **`familiar-ember`**:

| Stage | Value |
|:--|:--|
| Conversation agent | `Ember (familiar local)` |
| Speech-to-text | `stt.onnx_asr` — Parakeet on `familiar`, via Wyoming (was `stt.vosk` until 2026-08-09) |
| Text-to-speech | `tts.piper_2` (familiar), voice `en_GB-cori-high`, language `en_GB` |
| Wake word | `wake_word.openwakeword` |
| **Prefer handling commands locally** | **on** — see [§6.4](#64-prefer_local_intents--why-its-on) |

### 2.5 card-mod (cosmetic, optional)
The dashboard's ember palette comes from
[card-mod](https://github.com/thomasloven/lovelace-card-mod). It is **not** a custom
card and nothing depends on it functionally — without it every card still renders, just
unstyled. Register it as a Lovelace resource if you want the theming. Note it applies
CSS *late* unless `card-mod-theme` is set in the active theme, so a heavy dashboard
paints unstyled for a moment on load.

---

## 3 · Deploying

```bash
./homeassistant/tools/deploy-ha.sh --check       # validate merged config, change nothing
./homeassistant/tools/deploy-ha.sh --dry-run     # show what differs from the VM
./homeassistant/tools/deploy-ha.sh               # copy changed packages + reload
./homeassistant/tools/deploy-ha.sh ember_persona # just one
```

It skips files already byte-identical on the VM, backs up what it replaces, runs
`check_config` on the **merged** configuration before reloading anything, then reloads
only the domains that changed:

| Package | Reloads |
|:--|:--|
| `ember_backend_health` | `rest`, `template` |
| `ember_persona` | `input_text` |
| `ember_announce` | `script` |

**No HA restart is needed for anything in this repo.** One recorded caveat:
`template.reload` reliably picks up *new* template entities, but *edits* to an existing
template sensor's definition have historically needed a full restart on this instance.
If an edited template sensor reads stale, restart rather than debugging the template.

If `check_config` fails, the script stops without reloading and HA keeps running the
previous configuration.

### The dashboard

```bash
python3 homeassistant/tools/build_ember_dashboard.py --dry      # print, touch nothing
python3 homeassistant/tools/build_ember_dashboard.py            # create-if-absent + push
python3 homeassistant/tools/check_dashboard_deployed.py         # is the LIVE one the committed one?
```

⚠️ **Committing the JSON does not change the dashboard.** What people look at is HA's
`.storage` copy, and the two disagree with nothing to notice — the repo is correct, so every
check that compares the repo against the truth passes. **This dashboard asserted that Hush
gates the talk gesture for hours after the JSON had been fixed**, because the fix was committed
and the push never ran.

`check_dashboard_deployed.py` asks Home Assistant instead: it reads the live config over the
same WebSocket API the pusher uses and diffs it against `origin/main`, naming which *view*
differs rather than dumping the JSON. **It reports and does not push**, deliberately — pushing
would silently overwrite a UI edit someone made on purpose, and that is a decision a person
should see. `--self-test` proves it can fail; `--local` compares against the working tree.

Both modes print `views=… sections=… cards=…` for the config they are about to push. **Read
the count off the tool rather than off this page** — the dashboard changes more often than the
prose does, and a card total frozen into a document is stale the next time a tile is added.

> ⚠️ **This one goes to `ha.jphe.in`, not `ha.lan` — the opposite of every other command on
> this page.** The host table in [§1](#host-names--read-this-before-you-type-a-deploy-command)
> already says so, and it was still read as "use `ha.lan` for deploys", because that is what
> the surrounding commands do. So, at the point of use: `HA_WS` defaults to
> `wss://ha.jphe.in/api/websocket`. **The edge name, and no port.**
>
> The old default, `ws://homeassistant.local:8123/api/websocket`, failed **three times in a
> row, each failure masking the next**:
>
> | Attempt | What happens | What it looks like |
> |:--|:--|:--|
> | `ws://homeassistant.local:8123` | name does not resolve | `socket.gaierror` |
> | `ws://ha.lan:8123` | resolves, but 8123 is **HTTPS** | *"did not receive a valid HTTP response"* — reads as a protocol fault; it is a scheme mismatch |
> | `wss://ha.lan:8123` | scheme now right, name now wrong | cert verification fails — the certificate is for `ha.jphe.in` |
>
> Each fix is correct and reveals the next problem, so the sequence rewards giving up two
> steps in. **Go to the name on the certificate.**
>
> This is not cosmetic. The dashboard asserted that Hush gates the talk gesture for hours
> *after* the repo JSON had been corrected, because the fix was committed and the push never
> ran. A source of truth that cannot reach the device is not a source of truth.

Pushed over the WebSocket API (`lovelace/config/save`), never by editing `.storage` —
HA holds `.storage` in memory and silently overwrites direct file edits. Lands at
`/ember-hearth`, sidebar **Ember**. The repo JSON is authoritative, so re-running after
a UI edit *overwrites* the UI change.

If you ever regenerate that JSON programmatically, keep
`json.dump(d, f, indent=1, ensure_ascii=True)`. The file is dense with non-ASCII glyphs;
any other setting re-encodes every one and buries a one-tile change in a 300-line diff.

#### Adding a board to this dashboard

The **Fleet** view carries one column per hearth, and that column is the board's
*complete* management surface — every entity the shared firmware exposes, grouped
**Assist → Voice out → Ear → The glass → Levers**. A new board is a new column and
nothing else. Work from the entity list, not from memory:

```bash
# 1. Wait for adoption. Do NOT author tiles against entities that don't exist yet —
#    a slot reference to a missing entity renders the red "Entity not found".
curl -sf -H "Authorization: Bearer $HA_TOKEN" \
  https://ha.jphe.in:8123/api/states/assist_satellite.<name>_assist_satellite >/dev/null \
  && echo adopted

# 2. Diff the new board against a known-good one. Expect an exact match except
#    `sensor.*_battery_soc`, which only a board with a real cell may have.
curl -s -H "Authorization: Bearer $HA_TOKEN" https://ha.jphe.in:8123/api/states \
  | python3 -c "import json,sys;e=[x['entity_id'] for x in json.load(sys.stdin)];\
print(sorted(i.replace('<new>','X') for i in e if '<new>' in i))"
```

3. **Stamp the column.** Copy an existing board's Fleet section and rewrite the slug,
   anchored on the trailing underscore (`ember_satellite_` → `ember_<new>_`). Anchoring
   matters: an unanchored replace corrupts any id that merely *starts* with another's
   name. Leave `binary_sensor.ember_reachable` alone — it is shared, carries no board
   prefix, and is repeated per column on purpose, because *"can this hearth think?"* is
   a per-column question even though the answer is one sensor.
4. Add the board to the **Voice Pipeline** view's mind-swap buttons
   (`select.select_option` takes a list) and give it a `Pipeline · <place>` tile. Ember
   is one persona with N bodies — a mind-swap that moves one body and leaves the rest
   is a bug, not a scope decision.
5. Add its `sensor.*_mic_rms` / `_mic_peak` / `_speaker_frames` to the Diagnostics
   ear-and-frames graphs, and a `Speak · <place>` button to **Announce path**.
6. **Add a `Speak · <place>` button to the Fleet composer** (*Say something, on any
   hearth*), calling `script.ember_say` with
   `data: {satellite: assist_satellite.<name>_assist_satellite}`. Pass the satellite
   **explicitly**, even though an empty one already means the desk unit — in a row whose
   whole job is choosing a hearth, the button that relies on a default is the one that
   breaks silently when the default moves. If the board is **in this house**, it also
   needs its own branch in `script.ember_announce_all`, or *"every hearth in the house"*
   will quietly skip it (that script is package-side — `deploy-ha.sh ember_announce`).
7. **Add it to the Hearth chooser.** That page follows `input_select.ember_say_target`,
   which is also what `script.ember_say` resolves against — one selector, so the hearth
   you are looking at is the hearth that answers. A new board needs **one option** on the
   input_select (package-side) and **one line in the hero's `map`**; then stamp its
   Output / Input / Assist sections with `visibility` keyed on the new option. Tiles
   cannot be templated, so they must be stamped — **markdown can**, so the hero and all
   prose stay a single copy that resolves the chooser itself. Do not triplicate prose.
8. Update the Fleet banner count (it counts the M5Stack and the assist microphone too),
   then `build_ember_dashboard.py` and `check_dashboard_deployed.py`.

> **The hero's pipeline table is a SNAPSHOT — re-measure it, don't copy it forward.**
> `assist_pipeline/pipeline/list` over the WebSocket API is the source. It has gone stale
> twice: once when vosk gave way to `stt.onnx_asr` (`8ec2aea`) and again when piper moved
> to `familiar` (`eccf8c7`). As of 2026-08-09 every pipeline except the stock
> *Home Assistant* one runs `stt.onnx_asr` + `tts.piper_2`, and `preferred` resolves to
> `familiar-ember`. Note that **`Gemini-vosk-piper-donkee` has not used vosk for weeks** —
> the name is identity and keeps it, so read the row and not the label.

> ⚠️ **Ghost-check after an HA restart, not just after an edit.** A replaced entity keeps
> existing in the state machine until the core restarts, so a check run against a live HA
> can pass on an id that is already dead. `tts.piper` survived the piper-moves-to-familiar
> migration (`eccf8c7`) that had *already* repointed the pipeline at `tts.piper_2`, and
> every check up to `318daf2` passed on it. A restart on 2026-08-09 cleared the state
> machine and the ghost appeared. Conversely, an **offline device is not a ghost** —
> during that same restart the M5Stack was down and its `assist_satellite` entity was
> absent; deleting its card would have been the DORMANT-≠-retired mistake. Distinguish
> *replaced* (fix the reference) from *unplugged* (leave it wired).

> ⛔ **Battery tiles are for boards that have a battery.** The `Battery Voltage` ADC on
> GPIO9 is unconditional in the shared firmware, so *every* board has the entity — and on
> a mains board it reads an absent divider, sitting around **4.1 V**, which looks exactly
> like a healthy lithium cell. `esphome/ember-mobile.yaml` keeps the SOC sensor out of the
> shared config for precisely this reason; the dashboard must agree with it. Only the
> mobile column has a **Cell** group. There is a note card in Diagnostics → *Cell level*
> saying so and naming the forbidden entities — **do not delete it as redundant.** It is
> the only visible evidence that the absence is deliberate, and without it the next person
> "restores" the missing tiles. (Fixed 2026-08-09; before that, three cards including a
> gauge headed *"Cell level"* charted the desk unit's floating pin.)

Name columns for the **place**, not the device slug — `Ember · Dad's house`, not
`Ember Dad`. There is one Ember; the boards are where it is standing.

> **Six boards is roughly where this stops being hand-authorable.** Three columns is
> ~100 cards of the 217 on this dashboard, and the per-board block is already produced by
> a stamp rather than by typing. If the fleet keeps growing, the honest move is to
> generate the Fleet view from the entity registry the way `~/Projects/ha` generates its
> `lights-tags` board — but that converts this file from hand-authored source of truth to
> build output, which is **JP's call, not a refactor to slip in.**

---

## 4 · Secrets

None of the three packages contains a secret, and none uses `!secret` — they are
self-contained and safe to publish. Verified, not assumed.

**Never copy these into the repo:**

| File | Contains |
|:--|:--|
| `/homeassistant/.storage/core.config_entries` | the LiteLLM master key, an OpenAI API key |
| `/homeassistant/configuration.yaml` | a commented-out `shell_command` holding a live long-lived access token |
| `/homeassistant/secrets.yaml` | everything else |

The LiteLLM key is entered through the UI ([§2.3](#23-the-conversation-agent)) and
lives only in `.storage`. That's the intended arrangement — there's no repo file to
redact.

---

## 5 · Verifying a fresh install

```bash
HA=https://ha.jphe.in:8123
AUTH="Authorization: Bearer $HA_TOKEN"

# 1. packages loaded
curl -s "$HA/api/states/binary_sensor.ember_reachable" -H "$AUTH" | jq .state          # on
curl -s "$HA/api/states/input_text.ember_say"          -H "$AUTH" | jq .attributes.max # 255
curl -s "$HA/api/states/script.ember_announce"         -H "$AUTH" | jq .state          # off

# 2. the backend is actually reachable, not merely configured
curl -s "$HA/api/states/binary_sensor.ember_reachable" -H "$AUTH" | jq -r .attributes.detail
#    -> serving | reachable but not ready | unreachable (familiar asleep?)

# 3. speech end-to-end, without touching the device
curl -X POST "$HA/api/services/script/ember_announce" -H "$AUTH" \
     -H 'Content-Type: application/json' -d '{"message":"The hearth is lit."}'
```

If step 3 speaks but conversation doesn't, go straight to
[§7.1](#71-announcements-work-conversation-is-silent) — that exact split has a known
cause, and it is not in Home Assistant.

---

## 6 · The voice pipeline

```
   you tap the screen
        │
        ▼
  ┌─────────┐   ┌────────────┐   ┌──────────────────────┐   ┌───────────┐
  │  wake   │──▶│    ear     │──▶│         mind         │──▶│   voice   │
  │openWake │   │stt.onnx_asr│   │ Qwen3.6-35B-A3B      │   │ tts.piper │
  │  Word   │   │            │   │ on `familiar`        │   │ en_GB-    │
  └─────────┘   └────────────┘   │ via LiteLLM @ ubox0  │   │ cori-med  │
                                 └──────────────────────┘   └───────────┘
        └──────────── Assist pipeline `familiar-ember` ────────────┘
```

The dashboard's **Voice Pipeline** view renders this same chain live with a real reading
at each stage.

### 6.1 The pipeline

| Stage | Value |
|:--|:--|
| Conversation agent | `conversation.extended_openai_conversation_2` — *Ember* |
| Language / conversation language | `en` |
| STT | `stt.onnx_asr` (`en`) — Parakeet via Wyoming at `familiar.lan:10300` |

> **A second pipeline exists: `jp-ember`** (2026-08-09) — identical to `familiar-ember` in
> every stage except the voice: **`en_US-jp-medium`**, JP's own cloned voice (he is en_US — the first label said en_GB, inherited unthinkingly from the cori base's region rather than from the speaker) (tonemask
> Phase-1 dataset, piper fine-tune from the cori-medium checkpoint; ~6.7 min of training
> audio, interim quality by JP's own verdict — "much better, still a bit to go"). The
> voice file lives on `familiar` at `/opt/wyoming-piper/data/en_US-jp-medium.onnx*`;
> the training lane and export patches are documented in the tonemask repo. Flip any
> hearth between voices with its `select.ember_*_assistant` — announcements follow the
> selected pipeline's voice, including the chronicle's SPEAK replays.
| TTS | `tts.piper_2` (familiar via Wyoming), language `en_GB`, voice **`en_GB-cori-high`** |
| Wake word entity | `wake_word.openwakeword` (`wake_word_id: null`) |
| **`prefer_local_intents`** | **`true`** |

The en-GB voice is a character decision, not an accident: Ember is a hearth-spirit, and
this is the voice that matches. It's also the only stage where the persona is audible
rather than textual.

**There is no wake word on the device.** `select.ember_satellite_wake_word` reports
`unavailable` with `no_wake_word` as its only option. The satellite is **push-to-talk** —
a screen tap or the BOOT button starts a conversation. The pipeline still names an
openWakeWord engine because that's the shape HA expects; nothing on Ember listens.

Consequence: the talk gesture is the *only* way in, so nothing may gate it silently.
`switch.ember_satellite_hush` used to do exactly that. **It no longer does.**

⚠️ **`Hush` changed meaning in the three-mode firmware (2026-07-30).** It was *"do not
listen to me"* — it wrapped the whole talk path, so with Hush on, tapping the screen did
nothing at all. It is now *"do not make noise"*: Ember listens and converses normally in
every mode and the reply arrives **on screen**; only the speaker changes. Hush is the
quietest of three modes, not a mute button on the microphone.

The mode is `select.ember_satellite_ember_mode` — **Normal** (speech + chimes) →
**No talking** (chimes only) → **Hush** (silent). `switch.ember_satellite_hush` survives
so existing automations keep working, and is now a *view* over that select: it reads ON
exactly when the mode is Hush and cannot be set independently of it.

### 6.2 The mind

Config entry **`Ember (familiar local)`**
(`extended_openai_conversation`): `base_url: http://ubox0.lan:4000/v1`,
`chat_model: ember`, `context_threshold: 40000`, `context_truncate_strategy: clear`.

`chat_model: ember` is a **LiteLLM alias**, not an upstream model name. Behind it is
**Qwen3.6-35B-A3B (UD-Q3_K_XL, MoE, 131K context)** served by `llama-server` on the
`familiar` host, port 8091.

**Why LiteLLM is in the path** — this looks like needless indirection and isn't. Home
Assistant's conversation integration cannot send **`chat_template_kwargs`**, and
Qwen3.6 needs them. LiteLLM at `ubox0:4000` exists specifically to sit between HA and
`llama-server` and inject them into every request. Point HA straight at `familiar:8091`
and the model is reached but behaves wrongly — the failure is in the *output*, not the
connection, which makes it expensive to debug from scratch.

```
HA ──▶ LiteLLM (ubox0.lan:4000) ──▶ llama-server (familiar.lan:8091)
```

The sibling `LiteLLM Bedrock` entry reaches the same LiteLLM by raw IP rather than by
name — the older form, worth normalising to `ubox0.lan` next time it's touched.

**`familiar` sleeps.** It S3-suspends after ~15 min idle and the inference lane isn't
guaranteed to return with it, so "Ember is selected" and "Ember will answer" are
different facts. That's what `ember_backend_health.yaml` measures:

- **`binary_sensor.ember_backend`** — polls `http://familiar.lan:8091/health` every
  60 s; `unavailable` when the host doesn't answer at all.
- **`binary_sensor.ember_reachable`** — collapses that into on/off plus a readable
  `detail`: `serving` / `reachable but not ready` / `unreachable (familiar asleep?)`.
  **Read `detail`, not the state** — *off* covers two different problems.

Polling does **not** keep the host awake: autosuspend watches whether the inference lane
is loaded, not network traffic, and a request to a sleeping host fails rather than waking
it. A gap in that history is a true signal, not an artefact of measuring.

### 6.3 The persona, and the one rule

The persona lives in **[`../homeassistant/prompts/ember-system.md.j2`](../homeassistant/prompts/ember-system.md.j2)**,
which is the source of truth — deploy it with `homeassistant/tools/ember-prompt.py --deploy`.
It is *stored* in the agent's conversation subentry inside HA's `.storage`; until 2026-07-31 that
was the only copy anywhere, which is how the reasoning below came to be half-right for months.

`input_text.ember_persona_extra` (255 chars — `input_text`'s hard cap) is a live nudge appended
to it, editable from the dashboard's Pipeline view. Good for *"Be even terser today, one
sentence only."*

> **The tweak field is injected at the very END of the prompt, and must stay there.**
>
> Ember answers fast warm only because the prompt *prefix* is byte-stable, letting llama.cpp
> reuse its KV cache. Anything volatile earlier in the prompt destroys that. Measured, not
> theorised.
>
> Trailing placement is also the only placement that *works*: sitting mid-prompt, after the
> ~6k-token entity manifest, the model ignored the field outright — including an explicit
> "reply in French". Moved last, it takes effect immediately. Delivery was never the problem;
> position was.

#### ⚠ Correction, 2026-07-31 — trailing placement is no longer "free"

The paragraph above used to end with *"trailing placement is free because `{{ now() }}` in the
Environment State block is already the cache boundary."* **That sentence had the right
observation and the wrong conclusion, and it cost this project months of 1-second turns.**

`{{ now() }}` rendered with **microsecond** precision — `2026-07-31 11:12:47.522568-07:00` —
so it was byte-unique on *every single request*. It was not a boundary to hide behind; it was a
cache bug that re-prefilled the timestamp, the tool preamble tail, **and the entire
conversation history**, every turn. The "516 tokens re-prefilled" figure recorded above is
exactly that cost, measured correctly and then filed as acceptable.

[#37](https://github.com/jphein/ember.realm.watch/issues/37) fixed it by coarsening the
timestamp to the hour, so the prefix is stable *within* a conversation:

```jinja
- Current Time: {{ now().strftime('%A %d %B, %H:00') }}    ->  Friday 31 July, 12:00
```

Measured against `llama-server` on `familiar:8091`, pinned to an idle slot
(`prompt eval time`, not wall clock):

| | before | after |
|---|---|---|
| prompt size | 7,970 tok | **6,258 tok** |
| byte-identical repeat (control) | 4 tok / 243 ms | 4 tok / 243 ms |
| **warm turn, history appended** | 516 tok / **1,023 ms** | **27 tok / 408 ms** |
| cold turn (whole prompt) | 7,970 tok / **6,024 ms** | 6,258 tok / **4,771 ms** |

The remaining 6,258 tokens are mostly the 294-row device manifest, deliberately kept.

**So the rule is now the plain one, with no exception:** nothing in the prompt may render
differently between turns. The tweak field is safe at the end because an `input_text` only
changes when JP changes it — and when he does, that one turn pays the re-prefill, which is
correct. **Do not reintroduce a sub-hourly timestamp, a live entity `state` column, or any
other per-request value anywhere in the prompt.** There is no longer a boundary that makes it
free.

### 6.4 `prefer_local_intents` — why it's on

HA matches utterances against its own intents first and only falls through to the LLM
when nothing matches. "Turn off the kitchen light" is handled by Home Assistant; "why is
the shed cold?" goes to Qwen.

1. **Latency** — a local intent answers in milliseconds. Round-tripping a light switch
   through a 35B model on a sleepy host is the slowest possible way to do the most
   common thing.
2. **Reliability** — device control shouldn't depend on `familiar` being awake. The
   lights still work when the mind is asleep.
3. **Cost of being wrong** — an LLM misparsing "turn off the lights" fails visibly and
   physically. Deterministic intents don't.

The agent still gets the full entity manifest and an `execute_services` function spec,
so it can control devices for anything local intents don't cover.

### 6.5 Speaking: two paths, and why the scripts exist

Ember speaks either as a **conversational reply** (the chain above) or as a **pushed
announcement** from HA. The second only became possible once the device declared a
`media_player`: `FEATURE_ANNOUNCE` is gated strictly on `voice_assistant` owning one,
which moved the satellite's `supported_features` from `0` to `3`.

Always announce through the scripts, never `assist_satellite.announce` directly:

| Script | Does |
|:--|:--|
| `script.ember_announce` | speaks `message`, pinning `preannounce: false` |
| `script.ember_announce_if_awake` | same, but refuses and logs when `ember_reachable` is off |
| `script.ember_say` | reads `input_text.ember_say` and hands it to `ember_announce` |

`preannounce: false` is not optional. HA sends its own generic herald unless told not
to, and Ember *also* plays its local `chime_announce` from flash — leave the default and
you hear two heralds back to back, which sounds like a firmware bug and isn't. Ember's
chime is better on every axis: in flash so no network fetch, instant, on the same
F-pentatonic as every other tone on the device, and it can't fail because HA's media
server is busy.

`script.ember_say` exists because Lovelace `perform_action` data is **not** templated —
a dashboard button can't carry a text field's contents, only call something that reads
it. It also *conditions* on the field being non-empty and aborts silently otherwise, so
the dashboard shows a hint when the box is empty.

**Audio delivery is measured, not assumed.**
`sensor.ember_satellite_speaker_frames` counts frames handed to the DAC and should climb
at exactly **16000/s** during TTS. Known-good baseline: a 27.2 s announcement produced
**26 consecutive one-second windows at exactly +16000 frames, 99.84 % cumulative, zero
injected silence.** Long utterances previously landed between 45.8 % and 93.9 %, so a
shortfall now is a real regression rather than variance.

### 6.6 Hearing: mic gain, and the entity that can call the dashboard a liar

**`number.ember_satellite_mic_gain`** is the ES8311's analog ADC PGA, live from HA and from
the device's own single-press overlay. It used to be the compile-time `mic_gain: 36db` on the
`audio_dac` block, so every adjustment cost a reflash — the wrong shape for a knob whose right
value depends on the room, the speaker's distance and how loudly they talk.

| | |
|:--|:--|
| Range | **0–42 dB, step 6** |
| Default | **36 dB** — deliberately *below* the maximum |
| Exposed as | `number`, `mode: slider`, restores across reboots |

⚠️ **The 6 dB step is the hardware's and cannot be refined.** REG16 takes a **3-bit field** with
exactly eight legal values — 0/6/12/18/24/30/36/42 — so nothing between them is representable,
and any UI offering a finer step would report a setting the codec cannot hold. If you ever see
this control advertise a step other than 6, or a count other than eight stops, the firmware's
range has drifted from the hardware and the *hardware* is right.

**36 rather than 42 is deliberate.** ESPHome's own default is 42 — the top of the range — and
stacked on the pipeline's `auto_gain` and `volume_multiplier` it clips and pins the level
gauges. Higher is *more sensitive and more clipped*, not better. Tune against
`sensor.ember_satellite_mic_rms` / `_mic_peak`, but only **mid-conversation**: `sound_level` is
passive and publishes NAN whenever the mic isn't running ([§7.8](#78-the-mic-gauges-show-entity-is-non-numeric)).

#### The number and the codec are two different facts

Setting the number writes REG16 directly *as well as* calling the driver's setter, because the
setter only assigns a member and the register is written once in the driver's own `setup()`.
That asymmetry has now caused two real defects — a control that would have done nothing until
the next boot, and a restored value that never reached the chip because
`TemplateNumber::setup()` publishes without calling `control()`. In the second case **the only
value immune was the default**, which is exactly what anyone would test with.

So the agreement is measured rather than assumed, and published:

| Entity | Is |
|:--|:--|
| `sensor.ember_satellite_mic_gain_codec` | what **REG16 actually holds**, in dB, read back off the chip |
| `binary_sensor.ember_satellite_mic_gain_desync` | `device_class: problem` — **ON means the number and the codec disagree** |

Both are diagnostic. One reader with two callers — a boot trigger at **+25 s** and a **60 s
interval** — rather than the check written twice inline. Periodic rather than boot-only,
because a divergence introduced *later* by anything writing REG16 outside the number would
otherwise never surface. It is one I²C register read a minute on a control-plane bus.

> ⚠️ **"No problem reported" is not the same as "verified in sync".** On an I²C read failure
> the firmware **leaves both sensors untouched** and logs a warning, rather than publishing a
> mismatch it cannot see. That is the right call — a confident answer from a blind instrument is
> worse than no answer — but it means the desync sensor can be `off` simply because nothing has
> successfully read the register recently. **Check that `…_mic_gain_codec` has a fresh value
> before reading `…_desync` as assent.** Silence here is silence, not agreement.

The reason this is an entity rather than a log line is worth keeping: a stale *comment* has
contradicting code beside it, and a stale *message* has nothing. The thing capable of stating a
gain the chip does not hold is a dashboard card, so the verdict is published where the false
claim would be read.

### 6.7 The intercom — sending word between hearths

Two ways to speak through the *other* Ember, layered deliberately
(design: `docs/superpowers/specs/2026-08-05-intercom-relay-design.md`):

**"Broadcast …" — the built-in path.** `prefer_local_intents` is on
([§6.4](#64-prefer_local_intents--why-its-on)), so HA's own `HassBroadcast`
intent catches *"broadcast [that] {message}"* before the LLM and announces on
**every other announce-capable satellite in the house** — not just the other
Ember. Measured 2026-08-05 on HA 2026.7.4, spoken from the desk unit: it
targeted the mobile Ember, the Wyoming `assist_microphone`, and the M5Stack
Atom Echo, and excluded the desk itself. Delivery confirmed on the instrument
(`sensor.ember_mobile_speaker_frames` 0 → 15040), **with `familiar` asleep the
whole time** — no LLM in the path means this is both the quickest intercom and
the one of last resort. Two measured caveats:

- It is house-wide by design. For a message aimed at one hearth, use
  `send_word` — "broadcast" is the fire bell, not the intercom.
- The intent blocks until every target reports playback done: with the Atom
  Echo `unavailable` in the target list, the turn took **29 s** to come back.
  The satellite that heard you sits busy for that long.

⚠️ The built-in path double-heralds, and that is accepted, not forgotten:
core's broadcast handler passes no `preannounce`, so a receiving Ember plays
HA's generic blip *and* its own chime. (Expected from the handler's defaults;
confirm by ear when next beside a receiving unit.) Fixing it means shadowing a
built-in intent — custom sentences + `intent_script`, a new deploy surface, no
source-device exclusion — for a cosmetic gain. Declined; the polished path is
`send_word`.

**"Tell the desk …" — the `send_word` tool.** Natural phrasings fall through
to the LLM, which calls `send_word(target, message)` — `desk`, `mobile` or
`both`. It rides `script.ember_announce`, so `preannounce: false` is pinned
and the single F-pentatonic herald plays. Dispatch is **fire-and-forget**
(`script.turn_on`): `assist_satellite.announce` blocks until playback
completes and has a 2.5-minute wedge precedent
([the header of `ember_announce.yaml`](../homeassistant/packages/ember_announce.yaml)),
and a hung delivery must not hold a voice turn hostage — so `sent=` claims
dispatch, never delivery. An `unavailable` target is caught before sending
(`hearth_unreachable=mobile`): the portable unit being off, flat, or in a
drawer is a normal state, not an error. There is no `other` target — EOC v3's
script executor passes only the model's arguments into the templates
(`functions/script.py:42`), so the tool cannot know which hearth is speaking.

**Quiet hours are deliberately bypassed on both paths.** A person speaking
through Ember *is* the editorial decision; `script.ember_broadcast`'s
quiet-hours → Slack routing exists for automated events, not the intercom.

Live two-way audio (walkie-talkie / drop-in) is **not** this feature — the
research and the reasons it is a firmware project live in
[#57](https://github.com/jphein/ember.realm.watch/issues/57).

---

## 7 · Troubleshooting

Ordered by how much time each costs when you don't know it.

### 7.1 Announcements work, conversation is silent

**How it presents.** `script.ember_announce` speaks perfectly. Then you ask Ember a
question and get the listening chime, the thinking chime — and nothing. No reply audio.
Meanwhile Home Assistant looks *completely healthy*: the pipeline debug shows a
**successful run with a valid TTS response URL**, STT transcribed correctly, and the
agent returned text.

**Everything you are about to check is fine.** This presentation sends you to STT, the
conversation agent, the TTS engine, and the `tts_proxy` URL — and none of them is the
problem. It cost hours. It also invites suspecting Authelia of intercepting the audio
fetch, which is wrong too.

**The distinguishing detail:** the failure is on the **device**, *after* Home Assistant
has finished its work. HA completed the run and served valid audio. Nobody debugging
from the HA side will find anything wrong, because nothing there is wrong.

**Root cause (fixed).** The satellite's own **`done` chime destroyed the reply's FLAC
header.** `media_player: platform: speaker` declares only an `announcement_pipeline`, so
ESPHome runs `single_pipeline_()` — chimes and speech share **one decoder**. `on_end`
fires *before* the reply audio plays, so the chime landed on top of the reply every
single time.

**Why announce survives it:** a pushed announcement isn't followed by a `done` chime, so
nothing interrupts it. That asymmetry is the entire reason this looks like a pipeline
fault — the path that breaks is precisely the path with a chime at the end of it.

**Ruling HA in or out.** Two commands, and they answer different questions.

*Does HA render and serve audio at all?* Mint a URL and fetch it — this proves Piper
works and that nothing (Authelia included) is intercepting `/api/tts_proxy/`:

```bash
HA=https://ha.jphe.in:8123
P=$(curl -sS -X POST "$HA/api/tts_get_url" -H "Authorization: Bearer $HA_TOKEN" \
      -H 'Content-Type: application/json' \
      -d '{"engine_id":"tts.piper","message":"Header check.","language":"en_GB",
           "options":{"voice":"en_GB-cori-medium"}}' | jq -r .path)
curl -sS -o /tmp/tts.bin -w 'HTTP %{http_code}  %{size_download} bytes  %{content_type}\n' "$HA$P"
head -c 4 /tmp/tts.bin | xxd
```

Expect `HTTP 200`, several KB, `audio/mpeg`, magic `49 44 33` (`ID3`). Note **no auth
header is needed on the fetch** — `tts_proxy` is a signed path, which is exactly why
Authelia is not in that story. This route returns **MP3**, not the FLAC the satellite
gets, so it proves the plumbing, not the container.

*Was the audio the satellite actually fetched valid?* Take `tts_output.url` from the
pipeline debug of a real conversation and fetch that:

```bash
curl -sS -o /tmp/reply.flac -w 'HTTP %{http_code}  %{size_download}\n' \
     "$HA/api/tts_proxy/<token>.flac"
head -c 4 /tmp/reply.flac   # expect: fLaC
```

⚠ **Do this immediately.** Pipeline stream tokens are short-lived — a **404 means the
token expired, not that HA is broken.** Re-run the conversation and fetch straight away.

If HA serves valid audio and the device is still silent, stop looking at Home Assistant
and look at chime sequencing on the device.

### 7.2 Ember hears me and then says nothing at all

Check `detail`, not the state:

```bash
curl -s "$HA/api/states/binary_sensor.ember_reachable" -H "$AUTH" | jq -r .attributes.detail
```

| `detail` | Means | Do |
|:--|:--|:--|
| `serving` | the lane is up — look elsewhere ([§7.1](#71-announcements-work-conversation-is-silent)) | — |
| `reachable but not ready` | host awake, model not serving | check `llama-server` on `familiar:8091` |
| `unreachable (familiar asleep?)` | host not answering | `familiar-wake` |

The Hearth view shows this inline and raises a banner naming the fix — but only when the
familiar-hosted pipeline is selected, since a sleeping `familiar` is irrelevant on
Bedrock. The Diagnostics view's 24 h reachability graph doubles as the host's sleep log.

### 7.3 Tapping the screen does nothing

**Do not start with `Hush` any more.** Under the three-mode firmware no mode gates the
talk gesture — every mode listens, so a hushed Ember still converses and still shows the
reply. If you are chasing "I tapped and got no *sound*", that is the mode working as
designed: check `select.ember_satellite_ember_mode` and look at the screen, where the
header reads `UNSPOKEN` and the sub-line says *the reply is on screen*.

If you tapped and got **nothing at all** — no header change, no wyrm movement — the mode
is not the cause and the touch controller may have stopped
answering. Press **`button.ember_satellite_rouse_touch_sensor`** — *Rouse Touch Sensor*, on the
Diagnostics view under **Levers · when something is wrong**. (The device's own power menu spells
the same action *"Rouse the touch sensor"*; the HA entity is the shorter name, which is what to
search for.) It re-pulses the
FT6336G reset line and re-runs its setup. Deliberately reachable from HA rather than
only from the device, because recovering a touchscreen must not require the touchscreen.
It blocks ~310 ms and logs a *took a long time* warning — expected for a manual recovery
action, not a fault.

### 7.4 Replies got slow

Two different faults, and the fix is different for each. **Don't guess from wall clock — get
`prompt eval time` per request**, which separates prefill from generation. Wall-clock timing is
what made the LLM look fast in #11 and cost a day.

```bash
ssh familiar 'journalctl -u qwen3-coder.service --since "-1h" --no-pager | grep "prompt eval time"'
ssh familiar 'curl -s localhost:8091/slots | python3 -m json.tool | grep n_prompt_tokens'
```

**~0.4 s → ~1 s on *every* turn: the prompt prefix stopped being byte-stable.** llama.cpp's
prefix cache truncates at the first differing token and re-prefills everything after it,
including all conversation history. Compare repo vs live to find what changed:

```bash
homeassistant/tools/ember-prompt.py --diff
```

Usual cause is something newly volatile in the prompt — a timestamp with sub-hour precision, a
live entity `state` column. See [§6.3](#63-the-persona-and-the-one-rule), including the
correction: there is **no** placement where a per-request value is free.

**~5 s once, then fast: that's a cold cache, not a regression.** The whole ~6.3k-token prompt
prefills at ~1,300 tok/s ≈ 4.8 s. Expected after anything that empties the slot:

- `qwen3-coder.service` restarted — familiar's autosuspend (15 min idle) or candela/storyvox CI
  cycling the ML stack. `systemctl show -p ExecMainStartTimestamp qwen3-coder.service`
- the prompt itself changed — a deploy invalidates the cache once, by design
- Ember's slot got reassigned; the service runs `--parallel 2` and is shared with
  `claude-local-qwen`

This is the open half of [#37](https://github.com/jphein/ember.realm.watch/issues/37): it is an
ops question (keep the cache alive) rather than a prompt one, and it is the difference between a
good warm turn and a ~5 s cold one.

### 7.5 The persona tweak has no effect

Check *where* it's referenced. Mid-prompt — after the ~6k-token entity manifest — the
model ignored it outright, including an explicit "reply in French". At the very end it
takes effect on the next turn. Also: 255 chars is `input_text`'s hard cap; longer edits
go in the conversation subentry.

### 7.6 "Speak it" does nothing

`script.ember_say` conditions on `input_text.ember_say` being non-empty and **aborts
silently** — no error, no log, no speech. If the box is empty that's the whole story;
the dashboard shows a hint beside the button whenever it is.

### 7.7 A faint pop on the hand-off

Expected and **bounded**. Not a regression, not worth investigating again. ESPHome tears
down and recreates the I²S clock on every mic↔speaker hand-off, while vendor firmware
(Korvo, xiaozhi) holds duplex channels open and never stops the clock. Every ES8311
anti-pop mechanism is clocked by LRCK, so none can survive the restart of its own clock.
Removing it means leaving stock ESPHome behind — a different project, deliberately not
taken.

### 7.8 The mic gauges show "Entity is non-numeric"

They shouldn't any more; if you see it, the dashboard is an older revision — redeploy.

The underlying behaviour is correct and not a fault: `sensor.ember_satellite_mic_rms` /
`_mic_peak` come from ESPHome's `sound_level`, which publishes NAN whenever the mic
isn't running — during TTS, and any time a turn is not in its listening phase. (Read that as
"the mic is idle between turns", **not** as a mode: no operating mode disables the microphone.
The phrase "Ember isn't listening" used to appear here and in the firmware, meaning Hush, and
it is retired for exactly that reason.) HA renders NAN as
`unknown`, and a `gauge` on a non-numeric state draws an **error box**, not an empty
dial. Since the mic is idle most of the time, that error *was* the normal appearance.

Consequence for tuning: those gauges are only meaningful **mid-conversation**, which is the one
time you cannot be looking at the dashboard. Use them to judge
[`number.ember_satellite_mic_gain`](#66-hearing-mic-gain-and-the-entity-that-can-call-the-dashboard-a-liar)
by their *history*, not their instantaneous reading — a Peak pinned at the top of its scale is
the symptom of too much gain.

### 7.11 `Mic Gain` reads one value and the codec holds another

`binary_sensor.ember_satellite_mic_gain_desync` is **ON**, or the dashboard is showing the
warning card. Believe `sensor.ember_satellite_mic_gain_codec` — it is read back off REG16;
the number entity only reports what it was *told*.

Either something wrote REG16 without going through the number, or a restore did not reach the
chip. The firmware re-checks every 60 s, so **it clears itself once they agree** — setting the
gain to any value and back is enough to force a write. If it does not clear, the I²C bus is the
next thing to look at, not the number.

⚠️ The inverse is *not* symmetrical: `off` does not prove agreement. See the caveat in
[§6.6](#66-hearing-mic-gain-and-the-entity-that-can-call-the-dashboard-a-liar) — a failed read
leaves both sensors untouched rather than reporting a mismatch it cannot see.

### 7.9 Entities missing after a deploy

```bash
curl -sX POST "$HA/api/config/core/check_config" -H "$AUTH" | jq
```

If that's `valid` and entities are still absent:

- **Did the file land on the right host?** `ha.jphe.in` is the proxy, not the VM. SSH
  target must be **`ha.lan`**.
- **Is it named `*.yaml`?** `!include_dir_named packages` loads only `.yaml`. Backups
  must be `name.yaml.bak-<date>`, never `name.bak.yaml` — the latter loads as a second
  copy of the package and collides on every entity id.
- **Right domain reloaded?** `rest`+`template` for health, `input_text` for persona,
  `script` for announce.
- **An edited template sensor?** `template.reload` picks up *new* template entities
  reliably; *edits* to an existing one have historically needed a full restart here.

### 7.10 Scripts can't be edited in the UI

Two separate things, both expected.

**Not editable.** `script.ember_announce`, `…_if_awake` and `ember_say` live in
`packages/ember_announce.yaml`. The UI script editor only reads and writes
`scripts.yaml`, so it returns **404** for these and shows them as non-editable. They
still appear and still run. Edit the package and redeploy.

**They do not conflict with `script: !include scripts.yaml`.** This looks like it should
break — `configuration.yaml` already binds `script:` — and it doesn't. HA's package
merge combines a package's `script:` dict into the existing one key by key. Verified
against the live instance with `check_config`, which performs the same full package
merge a restart does: **`valid`**.

The real constraint is narrower: **script ids must be unique** across `scripts.yaml` and
every package. `scripts.yaml` is currently empty, so there's no collision surface at
all; the first UI-created script populates it and the merge still holds unless an id
collides — and `check_config` will say so before a restart bites.

*Left as a documented constraint rather than "fixed":* moving the scripts into
`scripts.yaml` would split Ember's configuration across a file that belongs to the whole
Home Assistant instance and cannot travel with this repo. Keeping them in the package is
what lets Ember be self-contained.

---

## 8 · Why copy and not symlink

Symlinking `/homeassistant/packages/ember_*.yaml` at a checkout on the VM was considered
and rejected:

1. **The VM is HAOS**, an appliance OS with no reasonable home for a git checkout.
   `/homeassistant` is the only persistent path — and it's HA's own config directory.
2. **`!include_dir_named packages` loads *every* `.yaml` in that directory.** A repo
   checked out inside it would have Home Assistant parsing the repo's own YAML —
   workflows, fixtures, examples — as HA packages. This is also why the deploy script
   names backups `name.yaml.bak-<date>`.
3. **A broken symlink is a silent failure**: the package doesn't load, entities go
   missing, and nothing points at the cause.

The copy-then-reload path is also the convention already proven in the workspace this
was extracted from — one less novel mechanism to trust.

---

## 9 · The toolkit — tools and skills

Ember's first real tools. Ten tool definitions, three skills, and the data plane
that feeds them. Added 2026-08-02; **no HA restart was needed for any of it**, and
none is needed to change any of it.

> **The integration on the VM is v3.0.0, and the clone at
> `~/Projects/extended_openai_conversation` is v2.0.2.** The older clone has no
> skills, no `functions/` package and no `working_directory()`. Read the VM's copy
> at `/config/custom_components/extended_openai_conversation/` when you need the
> loader's actual behaviour — everything in this section came from there.

### 9.1 Three storage classes, and the constraint that shaped everything

| What | Lives in | Deployed by | Reload |
|:--|:--|:--|:--|
| **Tool definitions** (`functions`) | HA `.storage`, a YAML **string** in the conversation subentry | `ember-toolkit.py --deploy` | none — applies on submit |
| **Skills** | files on the VM, `/config/extended_openai_conversation/skills/<name>/SKILL.md` | `ember-toolkit.py --deploy` | `extended_openai_conversation.reload_skills` |
| **Enabled-skills list** (`skills`) | HA `.storage`, same subentry | `ember-toolkit.py --deploy` | none |
| **The data plane** (sensors, rest_commands) | real HA YAML, `packages/ember_toolkit.yaml` | `deploy-ha.sh ember_toolkit` | `rest.reload`, `rest_command.reload` |

**The constraint that decided the architecture:** the `functions` field is parsed
with a plain `yaml.safe_load()`, which does **not** understand `!secret` — it
raises on the unknown tag. So **a tool definition can never hold a credential.**

That is why `packages/ember_toolkit.yaml` exists. Anything needing a key is a
`rest:` sensor or a `rest_command:` in real HA YAML, where `!secret` works, and the
tool reads the *result*. Two things fall out of it, both worth keeping:

1. Credentials stay in `/config/secrets.yaml`. Git only ever sees `!secret`.
2. `check_print` does no network I/O during a conversation — it reads an
   already-polled sensor, so a wedged printer host cannot stall a voice turn.

### 9.2 The tools

Twelve total: the integration's stock four, plus eight from this repo. The field is
replaced **wholesale** on deploy, so `ember-functions.yaml` always carries the
complete list — `ember-toolkit.py` refuses to submit one missing
`execute_services`, because that is how Ember controls the house.

| Tool | Type | Reads | Notes |
|:--|:--|:--|:--|
| `execute_services` | native | — | stock; device control |
| `get_attributes` | template | exposed entities | stock; **refuses unexposed entities** |
| `load_skill` | read_file | skill files | stock; how a skill body is read |
| `bash` | bash | the workspace | stock |
| `check_print` | template | `sensor.ember_print_job` | state, file, percent, time left |
| `realm_status` | template | `binary_sensor.infra_*` | "is X up"; names what it doesn't watch |
| `whos_home` | template | `person.*` | one person is tracked; see [§9.6](#96-what-the-instruments-lie-about) |
| `weather_now` | script | `weather.forecast_home_2` + `weather.get_forecasts` | now, today's high/low/rain |
| `palace_recall` | script | `rest_command.palace_search` | MemPalace; takes an optional `wing` |
| `look_at_camera` | script | `rest_command.spyglass_cams` | posts a snapshot, reports frame age |
| `realm_query` | rest | realmwatch `:80` on `katana.lan` | the realm's lore and game layer: overview, power, events, quests, personas |
| `send_word` | script | `assist_satellite.*` states | the intercom — speaks a message on the desk, the mobile, or both hearths ([§6.7](#67-the-intercom--sending-word-between-hearths)) |

**Tools return facts, not sentences.** Every one answers in `key=value` form —
`state=Printing; file=ember mobile midframe r10; percent=68`. Ember's voice is
defined in the prompt, and a tool that returns polished prose fights the persona
and wins. This is why she says *"the ember mobile midframe is about two thirds
done"* rather than reading out a percentage.

Two tools exist because of an exposure gap that is easy to trip over:
**`person.*`, `weather.*`, `calendar.*` and `device_tracker.*` are NOT in Ember's
306-entity manifest.** `get_attributes` validates exposure and raises
`EntityNotExposed`, so it cannot reach any of them. Template-type functions read
state directly and are not exposure-checked, which is the only route to that data
— hence `whos_home` and `weather_now` rather than a skill telling Ember to look
the entities up herself.

`look_at_camera` **cannot see**. The Qwen lane has no vision, so the tool posts the
frame to Home Assistant's notifications, reports its age in seconds, and returns
`do_not_describe_the_image=true`. Its five cameras are validated against a fixed
allow-list before the name reaches a URL — the model chooses that value, and an
unchecked one would be a request-forgery seam through Spyglass.

### 9.3 The skills

A skill is a **directory** containing `SKILL.md` with YAML frontmatter carrying a
`description`. Discovered from `skills.py`, and each of these is load-bearing:

- The skill's **name is its directory name**. A `name:` in the frontmatter is
  ignored.
- `description` is **required**; without it the loader logs a warning and skips
  the skill. Max 1024 chars, name max 64.
- Loose files in the skills directory are skipped, which is why the stock
  `README.md` there is harmless.
- The body is **not** in the prompt. Only name, description and path are; Ember
  calls `load_skill` to read the instructions when she decides they apply.

| Skill | Covers |
|:--|:--|
| `printer-watch` | answering print questions, and what to do when one looks stuck |
| `morning-report` | the four-sentence spoken briefing |
| `whos-home` | who is in, and the limits of what this house can know |

### 9.4 Deploying, and the order that is not negotiable

```bash
./homeassistant/tools/deploy-ha.sh ember_toolkit        # data plane first
./homeassistant/tools/deploy-ha.sh ember_print_context
./homeassistant/tools/ember-toolkit.py --diff           # repo vs live, changes nothing
./homeassistant/tools/ember-toolkit.py --deploy --dry-run
./homeassistant/tools/ember-toolkit.py --deploy         # skills, reload, then tools
```

`--deploy` does three things in one order, and the order is forced:

1. **Write the skill files** to the VM. Nothing has changed yet.
2. **`reload_skills`**. `SkillManager` only rescans on that service.
3. **Submit `functions` and the enabled-skills list.**

Step 3 cannot precede step 2. The config flow builds the `skills` field's options
from the skills *currently loaded*, and `config_flow.py` **drops the field
entirely when none are loaded** — so enabling a skill before reloading is either
rejected by voluptuous or silently offers nothing. The tool verifies the loaded
count against what it is about to enable and aborts on a mismatch, because a skill
whose frontmatter was rejected is otherwise only a warning in HA's log.

> ⚠️ **The submit replaces `subentry.data` wholesale** — the same trap
> `ember-prompt.py` documents. Every field must be resubmitted or it is dropped.
> `ember-toolkit.py` reads the live values, substitutes only `functions` and
> `skills`, and aborts if the flow advertises a field it has no live value for.
>
> A successful submit makes HA **reload the config entry**, and for a second or two
> the flow cannot be reopened. The read-back retries on `entry_not_loaded`; without
> that, a deploy that fully worked reports a scary `abort`.

**One knock-on for `ember-prompt.py`:** the flow now advertises a `skills` field.
That is fine while skills are enabled, because it carries a live value and gets
passed through. But on an instance where skills exist on disk and none are enabled,
`ember-prompt.py --deploy` will refuse — guessing `[]` would silently disable every
skill. Its error now names `ember-toolkit.py` as the tool that owns that field.

#### Testing a tool end to end

Ask Ember through the conversation API — this is the real path, tools included:

```bash
HA=https://ha.jphe.in
curl -sS -X POST "$HA/api/conversation/process" \
  -H "Authorization: Bearer $HA_TOKEN" -H 'Content-Type: application/json' \
  -d '{"text":"How is the print going?",
       "agent_id":"conversation.extended_openai_conversation_2","language":"en"}' \
  | jq -r .response.speech.plain.speech
```

Measured 2026-08-02, live, with a real print running:

| Asked | Ember said | |
|:--|:--|--:|
| *How's the print going?* | "The ember mobile midframe r10 is 68 per cent done with about 55 minutes left." | 17.7 s |
| *Is familiar up?* | "Yes, familiar is up and serving." | 4.2 s |
| *Is serialhub up?* | "Serialhub is not on my watch list, so I cannot check it. I am only watching familiar, gatekeeper, gigabeam1, hp switch, katana, north bedroom ap, north office ap, and ubox0." | 4.7 s |
| *Is anyone home?* | "No, you are out." | 3.5 s |
| *What's the weather doing?* | "Clear night, 55F. High today was 55, low 43, and no rain about." | 4.0 s |
| *Show me the road camera* | "I have put the road camera on screen. The frame is fresh." | 2.6 s |
| *Show me the basement camera* | "I don't have a basement camera. The cameras I can show are parking, road, car, printer, and printroom." | 3.5 s |
| *Give me the morning report* | "Clear night, fifty-five out, dropping to forty-three by morning with no rain. The midframe print is about seventy percent done, roughly half an hour left. Everything else is up. You are out." | 8.0 s |
| *What's on my calendar today?* | "I don't have access to your calendar. I can check the weather, the printer, or who is home if that would help." | 3.2 s |

The 17.7 s first call is the **cold prefill**, not a tool cost: deploying `functions`
changes the prompt's tool preamble and invalidates llama.cpp's prefix cache exactly
once, by design ([§7.4](#74-replies-got-slow)). Everything after it is a warm turn
plus one tool round trip.

Note the morning report spelling numbers out and the calendar refusal — neither is
in the prompt. Both come from `morning-report/SKILL.md`, which is how you can tell
a skill actually loaded.

### 9.5 The persona-knob channel

`packages/ember_print_context.yaml` is the reference pattern for telling Ember
about *right now*: it keeps `input_text.ember_persona_extra` in sync with whether a
print is running, so "how's it going" has an obvious subject.

**Every change to that field costs one prompt re-prefill** ([§6.3](#63-the-persona-and-the-one-rule)).
So the pattern's rules are:

1. **Write states, never progress.** A percentage in this field would re-prefill
   the prompt on every poll — the documented cache bug, arriving from a new
   direction. Percentages are what `check_print` is for.
2. **Guard every write** with "is it already what I want?". A no-op write still
   invalidates the cache. That guard is what lets the automation run often.
3. Keep it under 255 characters, `input_text`'s hard cap.
4. **Always ship the clearing half.** A stale "a print is running" is worse than
   silence, because Ember states it with total confidence.

It is **one reconciler, not a start/stop pair**, and that is deliberate. Edge
triggers are only correct if they see every edge, and they cannot: a print already
running when the automation is installed produces no edge, and HA does not replay
state triggers on reload. That happened on the first deploy of this very file. So
it computes the desired note, writes only on a difference, and is driven by a
template trigger, a 15-minute clock and HA start. Declare desired state; don't
chase transitions.

### 9.6 What the instruments lie about

Every one of these was found by measuring while building, and each would have had
Ember state a falsehood confidently.

| Instrument | The lie | Measured |
|:--|:--|:--|
| realmwatch `/status` → `wol` | `serialhub` and `nodered` reported **`dark`** while both answered ping | 2026-08-02 |
| realmwatch `/topology` | reports `familiar` at **10.0.6.104**, which is **serialhub's** address | 2026-08-02 |
| `weather.home` | **"sunny, 83F"** at 20:38 local, well after dark; met.no said clear-night, 55F | 2026-08-02 |
| palace-daemon `/search` | HTTP 200 with a JSON-RPC error body: `UnboundLocalError: … 'lexical'` | 2026-08-02 |

Consequences, all baked into the tools:

- **`realm_status` deliberately does not use realmwatch.** It reads HA's own
  `binary_sensor.infra_*` connectivity sensors — real ICMP probes HA already runs —
  and reports an unwatched host **as unwatched**. Only 8 hosts are watched, and
  `serialhub` is not one of them; the tool says so rather than guessing.
- **`weather_now` pins `weather.forecast_home_2`** (met.no), not `weather.home`.
  Its forecast comes from the `weather.get_forecasts` *service*, because modern HA
  weather entities no longer carry a `forecast` attribute and reading one returns
  nothing rather than failing loudly.
- **`palace_search` uses `/search/fast`.** `/search` is broken server-side, so the
  reranked endpoint is not an option today regardless of quality. Re-measure before
  switching if palace-daemon is fixed.
- **Palace relevance is currently weak unfiltered** — a query about Ember's own
  latency returned candela release notes, while the same query scoped to a wing
  found the right drawer. `palace_recall` therefore takes a `wing`, and its
  description tells Ember to pass it whenever the question is about one project.
- **`palace_recall` dedupes on snippet text, not drawer id.** The palace holds
  genuine duplicate drawers with different ids and identical bodies, so id-dedupe
  returns the same memory twice.

### 9.7 Secrets

Two new keys, both **only** on the VM in `/config/secrets.yaml`, referenced from
`packages/ember_toolkit.yaml` as `!secret`:

| Key | From the vault |
|:--|:--|
| `octoprint_api_key` | `OctoPrint API key (serialhub)` |
| `palace_daemon_api_key` | `palace-daemon-v1` |

```bash
# how they got there — never into git, never into .storage
bw get password "OctoPrint API key (serialhub)" \
  | ssh jp@ha.lan "sudo tee -a /config/secrets.yaml"   # as `octoprint_api_key: …`
```

Verify before every commit that the repo carries references and not values:

```bash
grep -rn "!secret" homeassistant/packages/ember_toolkit.yaml   # expect 2 hits
git diff --cached | grep -iE "api.?key|token|secret" | grep -v '!secret'   # expect nothing
```

### 9.8 Adding a tool, or a skill

**A tool that needs no credential:** add it to
`homeassistant/functions/ember-functions.yaml` and run `ember-toolkit.py --deploy`.
Prefer `template` for anything readable from HA state — it is instant, cannot fail
mid-turn, and is not exposure-checked. Return `key=value` facts, not prose.

**A tool that needs a credential:** it cannot live in the tool definition at all
([§9.1](#91-three-storage-classes-and-the-constraint-that-shaped-everything)). Add
a `rest:` sensor or a `rest_command:` to `packages/ember_toolkit.yaml` with
`!secret`, deploy it with `deploy-ha.sh ember_toolkit`, then add a `template` or
`script` tool that reads the result. Give on-demand `rest_command` calls
`continue_on_error: true` and a branch that says the source was unreachable —
`familiar` sleeps, and a tool must never fill a gap with invention.

**A skill:** create `homeassistant/skills/<name>/SKILL.md` with frontmatter
carrying a `description`, then `ember-toolkit.py --deploy`. The description is what
Ember sees in the prompt and the only thing she uses to decide whether to load the
body — write it as a trigger ("use for questions about X"), not a summary.

Test any of it by asking Ember, not by reading the config
([§9.4](#testing-a-tool-end-to-end)). A tool that parses is not a tool that answers.
