# CLAUDE.md — ember.realm.watch

Guidance for Claude Code working in this repo. **[README.md](README.md) is the encyclopedia**
(~1000 lines: pipeline, hardware, enclosure, HA side, provenance). This file is the operational
layer: what to run, what will bite you, and where the source of truth lives for each concern.

Ember is an ESPHome voice satellite on a cheap 2.8" ESP32-S3 touchscreen, wired to a Home
Assistant Assist pipeline whose conversation agent is a local Qwen3.6 on the `familiar` host.
The screen *is* the hearth: one fire in a grate whose temperature is the whole state machine.

## Read this before editing anything

- **The comments in `esphome/ember-satellite.yaml` are the documentation.** ~3700 lines, and the
  ⚠️ / `>>> <<<` blocks record decisions that cost real debugging time. They are not decoration.
  Several say *do not "simplify" this back* and mean it (the row-major fire, the banded redraw,
  the I2S arbiter). Read the surrounding comment before changing a constant.
- **`docs/verification.md` is the repo's conscience** — 32 numbered cases of a check that passed
  while the thing it checked was wrong. Skim it before claiming something is verified. Its §32 is
  about a stale ⚠️ comment causing a misdiagnosis, so: **if you retire a warning, date it and say
  what observation retired it.**
- Generated files must not be hand-edited: `docs/index.html` (from `site/index.src.html` via
  `site/build.py`), `docs/print-sheet.html`, `enclosure/*.stl` (from the build123d scripts),
  `site/renders/`. The next build destroys hand edits silently.

## The two devices

There are **two** boards as of 2026-08-03 (issue #44). Both run the *same firmware* — one shared
config, two thin identity wrappers.

| | config | MAC | notes |
|---|---|---|---|
| Desk | `esphome/ember-satellite.yaml` | `28:84:85:44:59:20` | the original; mains powered |
| Mobile | `esphome/ember-mobile.yaml` | `28:84:85:44:3E:C4` | 1× bare 18650, portable |

`ember-mobile.yaml` is a ~70-line wrapper that `!include`s the desk config as a package and
overrides only `name` / `friendly_name`. **This works because the shared config never hardcodes
its own name** (`name: ${name}`), and because main-config substitutions take precedence over a
package's. Keep it that way:

> **Do not fork the big YAML for a third device.** Add another wrapper. If two boards genuinely
> differ in hardware, put the difference behind a substitution in the shared file — not in a copy.
> The repo already argues this about the paint body (issue #10).

⛔ **The board has no protection IC** (fact, per `docs/vendor/ES3C28P_Schematic.pdf`: `BAT`
straight to the cell, regulator floor ~3.4 V, ~9 µA divider drain below it). ✅ **1S protection
strips are FITTED on both battery boards** (mobile + dad, 2026-08-09). The strip is the floor;
the on-screen candle + battery ladder are the early warning. Still binding: do not add a firmware
low-voltage cutoff and call anything solved — firmware cannot protect a cell it is no longer
powered by.

## Build and flash

```bash
cd esphome
cp secrets.yaml.example secrets.yaml     # three keys: wifi_ssid, wifi_password, api_key
esphome compile ember-mobile.yaml
esphome run     ember-mobile.yaml        # OTA — target derived from the config's own name
esphome logs    ember-mobile.yaml --device /dev/ttyACM2   # USB serial
```

Verified against ESPHome **2026.7.3** (config declares `min_version: 2025.11.0`). Compiling on a
workstation is ~5× faster than on the HA host.

Three traps, all of which have already cost time here:

- ⚠️ **`esphome config` is not a build check.** It validates YAML and never compiles the lambdas —
  it will echo broken C++ back at you and then print `Configuration is valid!`. See
  `docs/verification.md` §4.
- ⚠️ **`esphome upload` does not compile either.** It ships whatever is already in `.esphome/build/`.
  Use `esphome compile` first, or `esphome run` which does both.
- ⚠️ **`/dev/ttyACM*` renumbers on replug, and both boards are from the same batch.** Check the
  MAC, never the port number. The USB-JTAG serial number *is* the MAC:
  `udevadm info -q property -n /dev/ttyACM2 | grep ID_SERIAL_SHORT`.

### OTA — the iteration loop

Both boards are OTA-only in practice. The desk unit is cased; the mobile unit runs off its cell.

```bash
esphome compile ember-mobile.yaml                              # ALWAYS compile first
esphome upload  ember-mobile.yaml --device ember-mobile.local   # then push
esphome logs    ember-mobile.yaml --device ember-mobile.local
```

⚠️ **Pass `--device <name>.local`, and make the name match the config.** Omitting `--device` does
*not* auto-derive the target — ESPHome prompts interactively for a choice, which EOFs in any
non-interactive context (scripts, agents, CI). An earlier version of this file claimed omitting it
was a safety feature; it isn't. The safety comes from the hostname matching the config filename.

⚠️ **Nothing in ESPHome ties a binary to a device.** `esphome upload ember-mobile.yaml --device
ember-satellite.local` would flash mobile firmware onto the desk unit, which reboots *renamed* —
two boards claiming `ember-mobile.local` and 25 HA entities orphaned. What now prevents this is
**per-device OTA passwords** (`ota_password_satellite` / `ota_password_mobile`, distinct 32-char
secrets, selected by the `ota_password` substitution): a mis-targeted push fails at authentication
instead of succeeding at renaming.

> The guard is **not** verified by a live cross-flash, deliberately. The password is compiled
> *into* the firmware, so any test that sends a wrong password from a config would also bake that
> wrong password into whatever it flashed — manufacturing the un-OTA-able board the guard exists to
> prevent. Verified instead: each config resolves to its own distinct secret, and a
> password-authenticated OTA succeeds on both boards.

**`safe_mode:` is enabled** (defaults: 10 attempts, `boot_is_good_after: 1min`). A boot only counts
as good once the device has stayed up a minute, so a crash 20 s in still counts as failed. After
repeated failures the board comes up with WiFi + OTA only — no display, no I2S — so a fixed build
can be pushed over the air. This is what makes a cased or battery-only board recoverable without a
disassembly, and it has never had to fire.

**Rotating an OTA password costs a USB flash of that board and nothing else** — HA authenticates
over the native API, not OTA, so there is no re-adoption and no entity loss. Rotating `api_key`
is the expensive one.

### A fresh flash looks broken and isn't

A board on WiFi but **not yet adopted in Home Assistant** sits in a ~1 Hz loop: `micro_wake_word`
Stopping/Starting, `[E][voice_assistant]: No API client connected`, `sound_level ... Microphone
isn't running`. The re-arm triggers fire on `voice_assistant` *ending* and a failed start counts as
an end. **Nothing is wrong with the board or the I2S bus.** It stops the moment HA adopts the
device. Do not go hunting the arbiter for it — `docs/verification.md` §32.

## Home Assistant side

**[docs/home-assistant.md](docs/home-assistant.md) is the full guide.** Roughly half of Ember's
HA-side config is not expressible as a repo file (add-ons, the conversation agent entry, the
pipeline) and that document enumerates every manual step. This repo is the source of truth for
what *is* a file.

```bash
homeassistant/tools/deploy-ha.sh --check       # validate only, no SSH
homeassistant/tools/deploy-ha.sh --dry-run     # ALWAYS run this first
homeassistant/tools/deploy-ha.sh ember_announce  # one package by stem — prefer this
homeassistant/tools/deploy-ha.sh               # all packages + reload changed domains
python3 homeassistant/tools/build_ember_dashboard.py --dry
```

> 🔴 **The VM is frequently AHEAD of this repo.** JP edits packages live on the HA
> host, so *"the files differ"* never means *"the repo is ahead"*. `deploy-ha.sh`
> now answers that question itself: it compares the VM's mtime against what the
> repo last **authored** (last commit touching the file, or its mtime if locally
> dirty) and **refuses to overwrite a newer VM copy, exiting 2**. `--force`
> discards the VM copy and is almost never what you want.
>
> This is a guard, not a substitute for looking: on 2026-08-03, before it existed,
> a deploy would have reverted that morning's wake-on-LAN retry in
> `ember_announce`. Reconcile repo ← VM, re-apply your change on that base, then
> deploy **one package by stem**. Precedent: `404da12`; the reasoning is
> `docs/verification.md` §33. The script also backs up remotely (`.bak-<date>`).
>
> ⚠️ **`PACKAGES=(...)` in `deploy-ha.sh` is a drift mechanism.** A package not named
> there is never deployed, never compared, and **never reported by `--dry-run`** — so it
> can live on the VM forever and nothing complains. Add new packages to that array *in
> the same commit that creates them*.

**This repo owns every `ember_*.yaml`, and it is the only owner.** All ten live in
`homeassistant/packages/` and deploy only through `deploy-ha.sh`.

> ⛔ **Do not let them reappear in `~/Projects/ha/packages/`.** Five of them used to
> live in both repos, each with its own deploy path to the same VM paths and nothing
> keeping them in step — whichever ran last won. That is the *actual* cause of the
> 2026-08-03 drift; the `PACKAGES` gap above was a symptom. The ha repo's copies are
> deleted and its CLAUDE.md now says why (ha commit `ca8b06f`).
>
> The boundary that remains, and it is the right one: `lights_overview.yaml` is
> **house-wide and owned by `~/Projects/ha`**. `ember_house_watch` consumes
> `sensor.lights_on` from it without owning it. To stop a fixture being counted as a
> house light, label it `indicator` in HA — never by editing Ember. That curation
> lives in HA's entity registry (`.storage`), so it is in neither repo; it travels
> with HA backups.

- ⚠️ **The API host and the SSH host are different machines.** The public name resolves to the
  reverse proxy, not the HA VM; `sudo tee` there writes to the *proxy* and reports success while
  changing nothing. `deploy-ha.sh` keeps them separate deliberately — don't "tidy" it.
- ⚠️ `HA_WS` wants the name on the TLS cert (the edge host, no port), never a LAN name or IP.
- Auth resolves `HA_TOKEN` → `~/.cache/ha-token-tmp` → password manager.
- Address the backend host **by hostname** (`familiar.lan` from the HA VM, `familiar` from a
  workstation). Never the IP — it moved once and the stale literal cost a session.

**Announcements never call `assist_satellite.announce` directly** — the raw service prepends HA's
generic blip on top of Ember's own chime. The chain is:

```
ember_driveway_watch / ember_laundry_herald
  -> script.ember_broadcast        (ember_slack.yaml — quiet hours? -> Slack)
     -> script.ember_announce[_if_awake]   (ember_announce.yaml — the terminal speaker)
        -> assist_satellite.announce
```

`ember_broadcast` decides *whether* a thing is spoken; `ember_announce` decides *which box*
speaks it. Both take an optional `satellite` that **defaults to the desk unit**, so every
pre-existing caller is unchanged. `script.ember_announce_all` hits both hearths.

> ⚠️ **`ember_announce_all` uses `parallel:`, and that is load-bearing.** As an ordered
> sequence it hung: `assist_satellite.announce` blocks until the device reports completion,
> the desk unit once sat in `responding` for ~2.5 min, and the second step never ran — the
> healthy mobile unit simply never got asked. **`continue_on_error` catches an error, not a
> hang.** Do not tidy it back into a sequence.

**The persona is shared, deliberately.** Both boards use one Assist pipeline, one system prompt
(`homeassistant/prompts/ember-system.md.j2`), one toolkit. Six of the seven `packages/*.yaml` have
zero device-entity references because they configure Ember-the-persona, not Ember-the-box. Ember is
one persona with two bodies — do not fork the prompt per device.

## Checks

No CI and no Makefile. The invariant checks are scripts, run by hand, and they are the closest
thing to a test suite — run the relevant ones after touching their subject:

```
esphome/tools/check_*.py        art sync, chime guards, navigability, paint coverage/sync, restore resync
enclosure/tools/check_and_render.py, label_export_check.py, minfeature.py
site/check_generated_current.py, check_served_current.py
homeassistant/tools/check_dashboard_deployed.py
```

`enclosure/README.md` explains what each enclosure check does and how to build from a fresh clone.
The CAD toolchain lives in `enclosure/cadenv/` (gitignored *and* stignored).

## Boundary with familiar.realm.watch

Ember's conversation agent runs on the `familiar` host, but **that config is owned by
[familiar.realm.watch](https://github.com/jphein/familiar.realm.watch), not mirrored here.** Cross-
reference, don't copy (JP's call, 2026-08-03) — a second copy of a systemd unit is a thing to go
stale, not a backup. What lives there:

- `ops/systemd/units/qwen3-coder.service` — Ember's LLM lane; owns both P102s, which is why Ember
  wins the GPU by construction rather than by luck.
- `ops/systemd/familiar/llama-server-extractor.service.d/zz-cpu.conf` — moves the MemPalace KG
  extractor onto CPU so it can coexist with Ember instead of racing it for VRAM.

Reached **through LiteLLM at `ubox0:4000`**, not straight at `familiar:8091` — pointing at the
backend directly connects fine and behaves wrongly, which is the worst failure shape. See README
"The pipeline".

## Conventions

- Versioning is **realm-sigil**: `./build-sigil.sh` writes only `docs/version.json`.
- Fantasy theming matters on anything user-facing. Chimes are F-pentatonic; keep new tones on it.
- Commits are conventional (`feat:`, `fix:`, `docs:`) and usually reference the issue (`(#44)`).
- Issues are load-bearing documentation here — #41 is the physical validation checklist, #44 the
  mobile variant, #42 the wake word. Read the issue before working its area.
