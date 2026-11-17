# Kitchen Ember: Nest Hub parity, and one Ember per room

**Author:** nebula (dreamteam). **Date:** 2026-11-17.
**Status:** design. Reviewed once by xreview (gpt-6.1-sol-2026-09-29): MERGE-AFTER-FIXES, with all seven points
applied below. Nothing in it is built yet.

**Asked by:** JP, plan chat 2406/2407/2409, 07:39–07:40:
- *"Work on the kitchen ember now. Get wake word and voice going again. Make sure that it can do everything that
  Google hub can, and more."*
- *"We'll add more embers to every room"*
- *"But first get the kitchen one working super good for the family."*

> **Where this doc lives, and why not in emberburrito.** The brief pointed at emberburrito (`hearthd :8094`,
> `donkey-llm :8092`). Those run on familiar and are the **hearth terminal** for tmux and Claude sessions. They are
> not a room voice device. The machine named as "the emberburrito host" (Dell i7-3770 with a 1050 Ti) is
> **gpu0**: it has no sound card, no capture device and no voice units (checked 2026-11-17 07:52). The voice
> devices called Ember are the ESPHome satellites in **this** repo, so the design lives here.

---

## 1. State on 2026-11-17, measured from 07:40 to 07:58

### 1.1 Which board is the kitchen ember

| Board | MAC | HA state at 07:43 | Network |
|---|---|---|---|
| Ember Satellite (desk, mains) | 28:84:85:44:59:20 | every entity `unavailable` since 2026-11-12 19:32Z | no DHCP lease, no ping |
| **Ember Mobile** (18650) | 28:84:85:44:3E:C4 | `assist_satellite` idle; wake word select *Okay Nabu*; pipeline `familiar-ember` | up, 10.0.8.198 |
| Ember (off-site third board) | 28:84:85:44:3E:A4 | `unavailable` since 2026-11-12 | down |

No Ember has an HA area. The Kitchen area holds only Google devices:
- Kitchen display (Nest Hub, `off`);
- Kitchen hub (Nest Hub, `unavailable`);
- Kitchen speaker (Home Mini);
- the `Kitchen Stereo` and `Counter` cast groups;
- Kitchen Thermostat (Nest).

**A hypothesis, not a fact:** the kitchen ember is Ember Mobile, because it is the only board on the network.
Being on the network says nothing about which room it is in. K0 confirms its room with someone in the house,
or by a beep they hear, **before** the area is written. Writing *Kitchen* first would only encode the guess.

### 1.2 Unit table

| Piece | Where | State | Last error line | Next step |
|---|---|---|---|---|
| **Home Assistant core** | HAOS VM on nodered (10.0.6.249 → VM 10.0.6.108) | **DOWN from 07:45 to at least 07:58**: both hosts fail ping and ARP, and `ha.jphe.in` returns 502 | Ember Mobile at 07:45:22: `Home Assistant 2026.11.1 (10.0.8.111): is unresponsive; disconnecting` | Bring nodered back (power, switch port or kernel). The ha lane owns this and is adding an `ha-host` layer check. |
| Ember Mobile firmware | ESP32-S3 | up; ESPHome 2026.8.0 built 2026-08-25; micro_wake_word *Okay Nabu* (cutoff 0.97); mic gain 42 dB, matching the codec; battery 4.16 V; mic RMS around −56 dB while listening | 07:43:57 → 07:45:22: sat 85 s in `STARTING_PIPELINE` waiting on HA, then went `IDLE` | **Hypothesis to test in K0:** it reconnects and re-arms once HA is back. Test with a spoken wake, not with an idle state. |
| Ember Satellite (desk) | ESP32-S3 | off the network since at least 11-12 (no lease) | none (absent) | Power check. It needs a hand in the room, so it is one tap for the household, or the board is recorded as retired. |
| Wyoming Parakeet STT `:10300` | familiar `wyoming-onnx-asr` | active since 11-14; the `local-voice-probe` every 5 min transcribes a real clip (`asr_ok`, 63–398 ms) | 11-14 17:40 `ConnectionResetError` (peer reset) | none |
| Piper TTS `:10200` (cori-high) | familiar `wyoming-piper` | active; the same probe synthesises a clip (first audio 266–1849 ms) | same peer reset | none |
| openWakeWord `:10400` | familiar docker | up 3 days | none | none; it serves only server-side mode 2, which is not live |
| Qwen3.6-35B `:8091` (Ember's LLM) | familiar `qwen3-coder` | active since 11-15; port open. Not checked: a real inference through LiteLLM | only `common_fit_params` warnings | K0: one text turn through the pipeline |
| LiteLLM `ember` route | ubox0:4000 | `/health/liveliness` 200 (liveness only) | — | the same K0 turn |
| **ESPHome build venv** | familiar `~/esphome-venv` | **was broken**: built on system python3.12, and `/usr/bin/python3` is now 3.14 | `ModuleNotFoundError: No module named 'esphome'` | **Fixed 07:54.** Recreated on uv-managed CPython 3.12.14 with esphome 2026.8.0, so an OS Python upgrade can no longer break it. The old venv was moved to `~/esphome-venv.broken-py312-20261117`. Proven with `esphome logs` handshaking with Ember Mobile at 07:55. |

### 1.3 What "wake word and voice going again" means in units

- **Nothing points at the device having changed.** Its firmware is from 2026-08-25, and the `esphome/` tree has
  no commit since 2026-10-01. Being unchanged is not proof that it works: wake detection, capture and playback are
  unverified until a spoken turn passes (K0).
- **What blocks voice right now:** HA is down, and every voice turn goes through HA's Assist pipeline.
- **A latent second break:** nothing could be compiled or OTA'd from familiar, because of the venv. That is
  fixed.
- **Not measured:** how voice behaved between 11-12 and 07:43. HA's Assist debug runs are held in memory, so
  they are very likely lost once nodered and the VM restart. K0 tries to read them and, if they are gone, records
  that and goes straight to a live spoken test.

---

## 2. Parity matrix: Google Nest Hub against the kitchen ember

**Status words:**

| Word | Meaning |
|---|---|
| **verified** | a spoken end-to-end turn on this board, dated, after the last firmware or HA change |
| **worked before** | evidence exists, but older than the current outage |
| **built, unverified** | the code is there and no use has been observed |
| **needs X** | X is the missing piece |
| **deferred** | a scope decision, with a reason |
| **out** | the hardware can't do it |

Today no row is **verified**, because HA is down. Every row below must pass the K1 spoken test before anyone calls
it done.

| # | Nest Hub does | Kitchen ember today | Status | Slice |
|---|---|---|---|---|
| 1 | Wake word ("Hey Google") | On-chip *Okay Nabu* (`wake_word_mode: 1`), confirmed by JP's voice 2026-08-01; touch also starts a turn | worked before | K0 |
| 2 | Set a timer | `on_timer_finished` is wired, so the satellite advertises FEATURE_TIMERS to HA | built, unverified | K1 |
| 2a | Ask how long is left, list the timers, cancel one, dismiss a ringing one | HA's timer intents exist. Not observed on this board: remaining time, cancel, or how ringing ends | built, unverified | K1 |
| 2b | See the countdown on screen | No `on_timer_started/updated` handlers; the screen shows nothing | needs firmware timer strip | K3 |
| 3 | Alarms, with snooze and dismiss | HA has no alarm intent | needs an alarm design: a persistent schedule (survives an HA or board reboot), snooze, dismiss by voice and touch, quiet-hours rules, and what happens when the board is offline | K3 |
| 4 | Weather | `weather_now` function → `weather.forecast_home` (Met.no), ember#113 | worked before | K1 |
| 5 | General questions | Local Qwen3.6 with no web access, so it knows only its training data | needs a search tool through the LiteLLM/Forge gateway (never Claude on Bedrock) | K4 |
| 5a | Follow-up without the wake word | The firmware has `continue_conversation` | built, unverified | K1 |
| 6 | Lights and scenes, by name and by "the lights" in this room | Local intents (`prefer_local_intents`, 250–350 ms measured in July) plus `execute_services`. "This room" resolution needs the board's area (K0) | worked before by name; room-relative needs K0 | K1 |
| 7 | Thermostat ("set the kitchen to 70") | Nest thermostat and minisplits are in HA. Not checked: whether kitchen `climate.*` is exposed to Assist | needs exposure check | K1 |
| 8 | Music and radio, with pause, resume, stop and volume | The board's media player has only an `announcement_pipeline`. It has no media pipeline, so the normal play/pause/stop semantics are absent, and with no mixer it can't play music and speak at once. The speaker is a small voice driver. **Scope choice:** music plays on the kitchen's existing Cast speakers, controlled by voice from the Ember | needs Music Assistant or cast routing, plus voice pause/resume/stop/volume on the Cast target | K2 |
| 8a | Cast to the hub from a phone | — | out (no Cast receiver on ESPHome) | — |
| 9 | Calendar ("what's on today") | No function reads `calendar.*` | needs a read-only `calendar_today` function scoped to the family calendars | K2 |
| 10 | Shopping list | `HassShoppingListAddItem` belongs to the `shopping_list` integration. The generic todo intents are separate. Not checked: which list integration is configured, and which list a spoken item lands on | needs a check, then a real item seen on the list | K1 |
| 11 | Broadcast to every room | `script.ember_announce_all` reaches the hearths only (in `parallel:`) | needs it to reach the Google speakers too, honouring `ember_broadcast` quiet hours | K2 |
| 12 | Intercom between rooms | `ember_intercom`: tap the horn, speak, and the peer hearth says it. No LLM, so it works while familiar sleeps | built; with one live board there is no peer to reach | Clone |
| 13 | Photo frame when idle | `show_image`/`online_image` exist for Slack visions; idle shows the fire | needs an idle rotation from a family album, shrunk to 320×240 by a small endpoint | K3 |
| 14 | Reminders | Google's reminders have moved to Google Tasks, so the baseline is *a timed spoken nudge plus a list entry*. Ember has nothing | needs a scheduler, not just a due date on a todo: it fires at the time, speaks in the asking room, survives reboots, and can be cancelled | K3 |
| 15 | Routines ("good morning") | `morning-report` skill; HA scripts are exposed | partial; needs named routines per person | K3 |
| 16 | Clock and ambient screen | none (no `strftime` in the firmware) | needs a clock in the idle hearth | K3 |
| 17 | Touch controls for the home on screen | Ember's screen is the fire plus volume and mode overlays; there are no device tiles | deferred: the kitchen wall panel (`ha-dash-kitchen`) already does on-screen control. The 2.8" screen stays voice-first | — |
| 18 | Volume and quiet modes | on-screen volume; Normal / No talking / Hush | worked before | K1 |
| 19 | Microphone off for privacy | Hush silences only the speaker. The mic is never gated (the README says so) | needs a real mic-off state that the screen shows, and that a spoken command or a tap can set | K1 (decide), K3 (build) |
| 20 | Video calls | no camera | out (hardware) | — |
| 21 | YouTube and video | 2.8" screen | out (hardware) | — |
| 22 | Voice Match, a voice per person | none | deferred (a scope decision): first get one household voice right | after K5 |

### "And more": what Google can't do

| # | Capability | Today | Status | Slice |
|---|---|---|---|---|
| M1 | Our own LLM, private, on our hardware | Qwen3.6 on familiar through LiteLLM `ember` | worked before | K0 |
| M2 | A household wake name ("Hey Ember") | Nest Hub can't do this. The openWakeWord `donk_ee` model can't be converted and works only server-side (mode 2, which streams idle audio) | needs a trained microWakeWord model | K5 |
| M3 | Memory ("what did we decide about…") | `palace_recall` → palace-daemon | built, unverified; scope is reviewed in **K1.5** | K1.5 |
| M4 | The plan's cards read aloud | none | needs a `plan_now` function reading an export file, never a token | K4 |
| M5 | House checks ("is everything OK") | `realm_status`, `ember_house_watch`, `ember_backend_health` | built, unverified | K1 |
| M6 | Who's home, cameras, driveway and laundry heralds | `whos_home`, `look_at_camera`, `ember_driveway_watch`, `ember_laundry_herald` | built; scope is reviewed in **K1.5** | K1.5 |
| M7 | Slack word in and out | `slack_send`, `ember_slack` | built; outbound destinations are reviewed in **K1.5** | K1.5 |
| M8 | Works with familiar asleep | the intercom and local intents need no LLM; `ember_wake_backend` wakes familiar | built, unverified | K1 |

---

## 3. One Ember per room: the clone plan

**JP's constraint:** a new room is "a flash and a name". The repo already gives the shape: **one shared config
plus a thin wrapper per board** (`ember-mobile.yaml`, about 70 lines). The repo's CLAUDE.md says not to fork the
big YAML.

### 3.1 Why a wrapper per room, not `name_add_mac_suffix`

`name_add_mac_suffix: true` gives stable, MAC-derived names from a single binary, so identity isn't the problem.
Two other things are:
- **Names people and scripts use.** `ember_announce`, the intercom peer map and every dashboard name a hearth
  by its room. `ember-kitchen` reads better than `ember-mobile-3ec4`, and needs no lookup table.
- **Each board has its own OTA credential.** This is one layer of protection against pushing the wrong
  firmware, not the whole guard (see §3.3).

So "one image" means **one source, one build recipe and a generated wrapper per room**. The binaries differ
only in the wrapper's strings.

### 3.2 `esphome/tools/new_hearth.py <room-slug> "<Friendly Name>" --mac <MAC> [--dry-run]`

It is idempotent: a rerun reuses the existing wrapper and secret. It **refuses** when the state conflicts, for
example a wrapper with another MAC, or a vault item already present with no matching wrapper. It never rotates a
secret silently. `--dry-run` prints every action.

1. **Refuse a protected or claimed MAC**, checked from one list in `esphome/tools/protected_macs.txt`:
   - the emberburrito board `28:84:85:44:45:94`;
   - reliquary's spare;
   - cyd-c5;
   - any MAC another wrapper already claims.
2. **Write `esphome/ember-<slug>.yaml`**, a copy of the mobile wrapper with:
   - `name: ember-<slug>` and `friendly_name`;
   - `ota_password: !secret ota_password_<slug>`;
   - `area: <Room>`. This is only a *suggested* area for HA; step 5 sets the area and reads it back;
   - `has_battery` set from a flag;
   - the expected board, flash size and partition layout, inherited from the shared config and asserted by the
     tool against the compiled `partitions.csv`.
3. **Write the secrets.**
   - Generate a 32-char OTA password. Store it as a **new** vault item `ember-ota-<slug>` (never overwrite by
     name, per the vault rule of 2026-11-16).
   - ESPHome needs the *value*, so the tool writes it into `esphome/secrets.yaml` (gitignored, mode 0600) from
     the vault. It never echoes it and never logs it.
   - The native-API encryption key is a separate decision. Today every board shares `api_key`, and rotating it
     costs a re-adoption. Recommendation: per-board API keys for new rooms only, in vault items
     `ember-api-<slug>`. That is decided in the Clone slice, not here.
4. **Build, then flash.**
   - Build with `remote_build.sh ember-<slug> compile`.
   - **First flash is by USB, guarded by the chip's own MAC.** `/dev/serial/by-id/` names the USB interface, and
     that is not reliably the Wi-Fi MAC. So: list the candidate ports, read each chip's MAC with
     `esptool.py --port <p> read_mac`, and require exactly one match. Check that match against
     `protected_macs.txt` again **immediately before** writing, then write the compiled factory image with
     `esptool.py write_flash 0x0 <factory.bin>` at the default baud.
   - **Every later OTA**:
     - read the target's MAC first, from the ESPHome API device info (`esphome logs` prints it on handshake)
       or from gatekeeper's lease for the hostname;
     - check it against the wrapper's `--mac` and the protected list;
     - only then run `remote_build.sh ember-<slug> flash`.
   - **Recovery:** `safe_mode` (10 failed boots → Wi-Fi and OTA only), then USB `write_flash` of the previous
     factory image. That image is kept under `esphome/.builds/<slug>/<sigil>/`.
5. **Adopt in HA.** The ha lane owns this call, scripted in the ha repo over WS. It reads back each value:
   - add the ESPHome config entry by host;
   - set the device area **explicitly** and read it back;
   - set `select.ember_<slug>_assistant` to `familiar-ember`;
   - set the wake word select to *Okay Nabu*;
   - add the board to `ember_announce_all`'s target list and to the intercom peer map.
6. **Prove it.** All four must pass:
   - (a) `assist_satellite.ember_<slug>_*` reads `idle` in the right area;
   - (b) one `assist_satellite.announce` with `media_id` pointing at a short chime file in `/local` and
     `preannounce: false`, in waking hours, with the room told first. A `message` would be synthesised speech, not
     a chime;
   - (c) **a person in the room** says the wake word and asks for "the lights" (room-relative). The board must
     hear it, the reply must be spoken, and the right room's light must change;
   - (d) the new board and an existing board each target the other in one intercom exchange. This proves
     identities are distinct and that cross-room routing works.

### 3.3 What stops a wrong-target flash

There are three layers, and no single one is the guard:
- the MAC check right before every write, USB or OTA;
- the protected-MAC list;
- the per-board OTA password.

The password does not protect a first USB flash, or boards that share an initial credential. The MAC check is
the layer that covers both.

### 3.4 Room rollout order

1. Kitchen.
2. The rooms with Google speakers today (a bedroom Home Mini, the laundry Nest Hub).
3. The rest.

Each room is one wrapper, one vault item and one adoption. The off-site board stays off this plan.

---

## 4. Slices, in order

| Slice | What | Done when |
|---|---|---|
| **K0** | HA back (ha lane). Try to read HA's Assist debug runs from 11-12 onward; if they were lost in the restart, record that. Confirm with the household which room Ember Mobile is in, then set its area explicitly. Plug in the desk board, or record it as retired. One spoken turn | its room confirmed and set; one spoken wake → STT → LLM → TTS turn heard in the room and dated; the trace read or recorded as lost |
| **K1** | The everyday family asks, each tested in two ways. **(a) Text, scripted:** `assist_pipeline/run` with `start_stage: intent`, `end_stage: tts`, `input.text`, the `familiar-ember` pipeline and the satellite's `device_id`, so that room context and timer association hold. **(b) Spoken, by a person in the room**, at least once per ask. The asks: kitchen light on and off by "the lights"; kitchen temperature; a 1-minute timer created, queried, rung and dismissed; a second timer cancelled; the weather; "add milk to the shopping list", with the item seen on the list; "is everything OK"; one follow-up without a wake word; volume. Also decide the mic-off behaviour (row 19) | a test file `homeassistant/tests/kitchen-asks.yaml`, each ask with its expected service call or answer and a dated run log covering both (a) and (b) |
| **K1.5** | **Family safety gate, before any cloning:** list every tool the agent can call and every exposed entity class (cameras, locks, presence, Slack destinations, memory wings). Decide what a child or guest saying anything can reach; scope `palace_recall` to a family wing; limit `slack_send` destinations | a written allowlist in `homeassistant/prompts/README.md`, enforced in the toolkit, and one refused ask per restricted class in the test file |
| **K2** | Music on the kitchen Cast speakers by voice (play, pause, resume, stop, volume); calendar today; broadcast reaches the Google speakers | each ask passes (a) and (b) |
| **Clone** | `new_hearth.py` plus the HA adoption script, proven on the next room by §3.2 step 6. **Depends only on K0, K1 and K1.5**, not on K2–K5 | the next room passes 6(a)–(d) |
| **K3** | Firmware: timer countdown strip, clock, idle photo frame, mic-off state. HA: alarms and reminders on a persistent scheduler, and named routines | firmware seen on the real screen (a photo). Alarms and reminders proven to: fire on time; survive an HA restart and a board reboot; cancel; snooze or dismiss; follow quiet hours; and say what they do when the board is offline |
| **K4** | Web search tool and `plan_now` | each ask passes (a) and (b); search goes through the gateway |
| **K5** | A trained microWakeWord "Hey Ember", A/B'd against *Okay Nabu* in the kitchen | false wakes per day over 24 h measured for both, then JP picks |

**Rules carried into every slice:**
- no hardware change without a measured reason;
- kitchen audio tests only in waking hours, one short sound, announced first;
- live speech is Piper `en_GB-cori-high`;
- the conversation agent is our own model, never Claude on Bedrock or Foundry.

## 5. Not verified in this doc

- Which room Ember Mobile is in (the only board on the network; its room is unconfirmed).
- Any spoken turn since 2026-08 on any board: wake detection, capture, playback, timers, all of it.
- Voice behaviour between 11-12 and 07:43, which needs HA's debug runs, probably lost in the restart.
- Real inference through LiteLLM → Qwen. Only liveness was checked.
- Whether kitchen `climate.*` is exposed, which shopping-list integration is configured, and whether Music
  Assistant is installed. HA went down before these reads, and each one is a K1 or K2 check.
- That `esptool.py read_mac` returns the same MAC the wrapper table lists for these boards. That is expected,
  because the USB-JTAG serial equals the MAC on the ES3C28P (ember CLAUDE.md), but this doc doesn't prove it.
