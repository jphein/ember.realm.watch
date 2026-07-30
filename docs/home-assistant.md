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

> **The repo cannot fully describe a working Ember.** About half the HA-side
> configuration lives in HA's own `.storage`, created through the UI, and isn't
> expressible as a repo file: the Assist pipeline, the conversation-agent entry, the
> add-ons, the HACS integration. Those are §2. The repo covers the packages, the
> dashboard, and the deploy path.

---

## 1 · What this repo ships

| Repo path | Deployed to | Carries |
|:--|:--|:--|
| `homeassistant/packages/ember_backend_health.yaml` | `/homeassistant/packages/` | `binary_sensor.ember_backend`, `binary_sensor.ember_reachable` |
| `homeassistant/packages/ember_persona.yaml` | `/homeassistant/packages/` | `input_text.ember_persona_extra`, `input_text.ember_say` |
| `homeassistant/packages/ember_announce.yaml` | `/homeassistant/packages/` | `script.ember_announce`, `…_if_awake`, `script.ember_say` |
| `homeassistant/dashboards/ember-hearth.dashboard.json` | HA `.storage`, over WebSocket | the `ember-hearth` dashboard (4 views, 118 cards) |
| `homeassistant/tools/deploy-ha.sh` | — | copies packages + reloads only what changed |
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
- **Piper** — TTS. Download voice `en_GB-cori-medium`.
- **vosk** — STT.
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
| prompt | Ember's persona — structure and the one hard rule in [§6.3](#63-the-persona-and-the-one-rule) |

⚠ `.lan` is required — HAOS does not resolve the bare `ubox0`. Don't substitute an IP:
hosts here have moved before and a hardcoded literal cost a whole debugging session.

### 2.4 The Assist pipeline
Settings → Voice assistants → Add assistant, named **`familiar-ember`**:

| Stage | Value |
|:--|:--|
| Conversation agent | `Ember (familiar local)` |
| Speech-to-text | `stt.vosk` |
| Text-to-speech | `tts.piper`, voice `en_GB-cori-medium`, language `en_GB` |
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
python3 homeassistant/tools/build_ember_dashboard.py --dry   # print, touch nothing
python3 homeassistant/tools/build_ember_dashboard.py         # create-if-absent + push
```

Pushed over the WebSocket API (`lovelace/config/save`), never by editing `.storage` —
HA holds `.storage` in memory and silently overwrites direct file edits. Lands at
`/ember-hearth`, sidebar **Ember**. The repo JSON is authoritative, so re-running after
a UI edit *overwrites* the UI change.

If you ever regenerate that JSON programmatically, keep
`json.dump(d, f, indent=1, ensure_ascii=True)`. The file is dense with non-ASCII glyphs;
any other setting re-encodes every one and buries a one-tile change in a 300-line diff.

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
  │openWake │   │ stt.vosk   │   │ Qwen3.6-35B-A3B      │   │ tts.piper │
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
| STT | `stt.vosk` (`en`) |
| TTS | `tts.piper`, language `en_GB`, voice **`en_GB-cori-medium`** |
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

The full persona (~1000 chars) lives in the agent's conversation subentry.
`input_text.ember_persona_extra` (255 chars — `input_text`'s hard cap) is a live nudge
appended to it, editable from the dashboard's Pipeline view. Good for *"Be even terser
today, one sentence only."*

> **The tweak field is injected at the very END of the prompt, and must stay there.**
>
> Ember answers in ~1.7 s warm only because the prompt *prefix* is byte-stable, letting
> llama.cpp reuse its KV cache — 516 tokens re-prefilled instead of 7,559. Anything
> volatile early in the prompt destroys that and costs ~6.5 s per turn. Measured, not
> theorised.
>
> Trailing placement is free because `{{ now() }}` in the Environment State block is
> already the cache boundary. It's also the only placement that *works*: sitting
> mid-prompt, after the ~7k-token entity manifest, the model ignored the field outright
> — including an explicit "reply in French". Moved last, it takes effect immediately.
> Delivery was never the problem; position was.
>
> Move that reference earlier and you silently trade 1.7 s replies for 7.6 s ones.

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
answering. Press **Rouse the touch sensor** (Diagnostics → Levers): it re-pulses the
FT6336G reset line and re-runs its setup. Deliberately reachable from HA rather than
only from the device, because recovering a touchscreen must not require the touchscreen.
It blocks ~310 ms and logs a *took a long time* warning — expected for a manual recovery
action, not a fault.

### 7.4 Replies got slow (~7 s instead of ~1.7 s)

Almost always the prompt prefix stopped being byte-stable, so llama.cpp re-prefills
7,559 tokens instead of reusing 516. Usual cause: something volatile moved earlier in
the prompt. See [§6.3](#63-the-persona-and-the-one-rule).

### 7.5 The persona tweak has no effect

Check *where* it's referenced. Mid-prompt — after the ~7k-token entity manifest — the
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
isn't running — during TTS, and any time Ember isn't listening. HA renders that as
`unknown`, and a `gauge` on a non-numeric state draws an **error box**, not an empty
dial. Since the mic is idle most of the time, that error *was* the normal appearance.

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
