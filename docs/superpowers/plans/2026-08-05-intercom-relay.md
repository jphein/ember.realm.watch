# Intercom Relay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Speak into either Ember and have the other hearth (or both) say the message aloud — the built-in `HassBroadcast` path verified and documented, plus a new `send_word` LLM tool.

**Architecture:** No firmware changes. Path 1 is HA's built-in broadcast intent (already active because `prefer_local_intents: true`); we verify it and document its double-herald blemish. Path 2 adds one script-type function to `ember-functions.yaml` that fire-and-forgets through the existing `script.ember_announce` / `script.ember_announce_all` chain, inheriting `preannounce: false`.

**Tech Stack:** Home Assistant 2026.7.4 (packages + Extended OpenAI Conversation v3), `ember-toolkit.py` deploy flow, `gh` CLI. Spec: `docs/superpowers/specs/2026-08-05-intercom-relay-design.md`.

**Ground rules for the executor:**

- This repo has no test framework, deliberately (CLAUDE.md). Verification is running real commands against the live HA instance and reading real output. Do not add a test framework.
- The HA API host is `https://ha.jphe.in` (the proxy carries the API). Auth for every curl below: `TOKEN=$(cat ~/.cache/ha-token-tmp 2>/dev/null || echo "$HA_TOKEN")`.
- Testing conversations requires the `familiar` backend awake. Check first; if asleep, wake it (Task 0 shows how).
- After the functions deploy, the FIRST conversation turn takes ~15–20 s (cold prefill — the deploy invalidates llama.cpp's prefix cache once, by design, see `docs/home-assistant.md` §7.4). Do not diagnose it.
- Branch: all work happens on `feat/intercom-relay` (already exists, spec committed).

---

### Task 0: Preflight — entities, backend, device_id

No files change. This task collects live facts every later task uses.

- [ ] **Step 1: Confirm both assist_satellite entities and their availability**

```bash
HA=https://ha.jphe.in
TOKEN=$(cat ~/.cache/ha-token-tmp 2>/dev/null || echo "$HA_TOKEN")
curl -sS "$HA/api/states" -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[] | select(.entity_id | startswith("assist_satellite.")) | "\(.entity_id) = \(.state)"'
```

Expected: exactly two lines —
`assist_satellite.ember_satellite_assist_satellite` and
`assist_satellite.ember_mobile_assist_satellite`, each `idle` (any state other
than `unavailable`/`unknown` is fine). If the mobile unit is `unavailable`,
note it: Task 1 needs it on; Task 5 Step 4 can run early instead.

- [ ] **Step 2: Confirm the speaker-frames sensor names (delivery instrument)**

```bash
curl -sS "$HA/api/states" -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[] | select(.entity_id | test("speaker_frames")) | .entity_id'
```

Expected: `sensor.ember_satellite_speaker_frames` and
`sensor.ember_mobile_speaker_frames`. If the mobile one is named differently,
use the name printed here everywhere the plan says `ember_mobile_speaker_frames`.

- [ ] **Step 3: Check the backend is awake; wake it if not**

```bash
curl -sS "$HA/api/states/binary_sensor.ember_reachable" -H "Authorization: Bearer $TOKEN" \
  | jq -r '.state + " — " + .attributes.detail'
```

Expected: `on — serving`. If not, wake and re-check (takes ~30 s):

```bash
curl -sS -X POST "$HA/api/services/script/ember_wake_backend" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}'
sleep 30
curl -sS "$HA/api/states/binary_sensor.ember_reachable" -H "Authorization: Bearer $TOKEN" \
  | jq -r '.state + " — " + .attributes.detail'
```

- [ ] **Step 4: Get the desk unit's device_id (needed to test source-exclusion)**

```bash
curl -sS -X POST "$HA/api/template" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"template": "{{ device_id(\"assist_satellite.ember_satellite_assist_satellite\") }}"}'
```

Expected: a 32-char hex id. Save it — Task 1 passes it as `device_id`.

---

### Task 1: Verify Path 1 — built-in `HassBroadcast`

No repo files change; the *findings* feed Task 3's docs. Requires both
satellites available and someone able to hear the mobile unit (or watch its
frames sensor).

- [ ] **Step 1: Record the mobile unit's frames counter before the test**

```bash
HA=https://ha.jphe.in
TOKEN=$(cat ~/.cache/ha-token-tmp 2>/dev/null || echo "$HA_TOKEN")
curl -sS "$HA/api/states/sensor.ember_mobile_speaker_frames" \
  -H "Authorization: Bearer $TOKEN" | jq -r .state
```

Expected: a number. Save it.

- [ ] **Step 2: Fire the broadcast through the DEFAULT agent, as if spoken on the desk**

`agent_id` is `conversation.home_assistant` (the built-in intent recognizer —
this is what `prefer_local_intents` consults before the LLM), and `device_id`
is the desk unit's from Task 0 Step 4:

```bash
curl -sS -X POST "$HA/api/conversation/process" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text": "broadcast this is a relay test",
       "agent_id": "conversation.home_assistant",
       "device_id": "<DESK_DEVICE_ID_FROM_TASK_0>",
       "language": "en"}' | jq -r .response.speech.plain.speech
```

Expected: a short confirmation (e.g. `Done`), the call taking a few seconds —
`HassBroadcast` blocks until playback finishes. The MOBILE unit speaks
"this is a relay test"; the DESK unit stays silent (source-excluded).

- [ ] **Step 3: Confirm delivery on the instrument, not the ear**

```bash
curl -sS "$HA/api/states/sensor.ember_mobile_speaker_frames" \
  -H "Authorization: Bearer $TOKEN" | jq -r .state
```

Expected: strictly greater than Step 1's value.

- [ ] **Step 4: Note the herald behaviour for the docs**

If anyone is within earshot of the mobile unit: expect HA's generic blip
*followed by* Ember's own chime — the double herald. Record whether it
happened (it should; core passes no `preannounce`). This sentence goes into
Task 3's subsection as "Verified 2026-08-05" — with whatever was actually
observed. If it did NOT double-herald, say so in the docs instead; do not
copy the expectation in as an observation (`docs/verification.md` exists
because of exactly that move).

---

### Task 2: Add the `send_word` tool

**Files:**
- Modify: `homeassistant/functions/ember-functions.yaml` (append after the `realm_query` entry, end of file)

- [ ] **Step 0: Check whether EOC script functions can see the source device (spec follow-up)**

The spec defers an `other` target on whether Extended OpenAI Conversation v3
exposes `device_id` to script-type function templates. Read the VM's copy —
it is v3.0.0; the local clone is v2.0.2 and answers this wrongly:

```bash
ssh jp@ha.lan "grep -rn 'device_id\|user_input' /config/custom_components/extended_openai_conversation/*.py /config/custom_components/extended_openai_conversation/functions/*.py 2>/dev/null | grep -iv 'entity' | head -25"
```

Look for whether the script-function executor passes `user_input` (which
carries `device_id`) into the template variables it renders. Record the
answer — one sentence, yes or no plus the line reference — in the PR body.
Do NOT build the `other` target now either way (v1 ships explicit targets).

- [ ] **Step 1: Append the tool definition**

Add to the end of `homeassistant/functions/ember-functions.yaml`:

```yaml
- spec:
    name: send_word
    description: >-
      Speak a message aloud on another hearth — the desk unit, the mobile unit,
      or both. Use when JP asks to tell, relay, pass on, let someone know, or
      send word to the desk, the mobile, the other hearth, or the whole house.
      The message is spoken there in your own voice.
    parameters:
      type: object
      properties:
        target:
          type: string
          description: >-
            Which hearth speaks. desk is the cased, mains-powered unit; mobile
            is the portable battery one; both speaks on every hearth at once.
          enum:
            - desk
            - mobile
            - both
        message:
          type: string
          description: What to say, short and plain.
      required:
        - target
        - message
  function:
    # Fire-and-forget by design: `assist_satellite.announce` blocks until the
    # device reports playback complete, and the desk unit has a documented
    # 2.5-minute wedge precedent (packages/ember_announce.yaml header). A hung
    # delivery must not hold a voice turn hostage, so this dispatches via
    # `script.turn_on` and reports sent= (dispatch), never delivered=.
    #
    # Deliberately NOT routed through script.ember_broadcast: its quiet-hours →
    # Slack routing exists for automated events. A person speaking through
    # Ember IS the editorial decision, so this goes straight to the terminal
    # speaker scripts, which pin preannounce: false (the single herald).
    type: script
    sequence:
      - variables:
          t: "{{ (target | default('', true)) | lower | trim }}"
          sat: >-
            {%- if t == 'desk' -%}assist_satellite.ember_satellite_assist_satellite
            {%- elif t == 'mobile' -%}assist_satellite.ember_mobile_assist_satellite
            {%- endif -%}
          # Which hearths are known dark right now. The mobile unit is portable:
          # off, flat, or in a drawer are all normal states for it.
          down: >-
            {%- set ns = namespace(out=[]) -%}
            {%- for pair in [('desk', 'assist_satellite.ember_satellite_assist_satellite'),
                             ('mobile', 'assist_satellite.ember_mobile_assist_satellite')] -%}
            {%-   if states(pair[1]) in ['unavailable', 'unknown'] -%}
            {%-     set ns.out = ns.out + [pair[0]] -%}
            {%-   endif -%}
            {%- endfor -%}
            {{ ns.out | join(',') }}
      - choose:
          # A single target that is down gets no dispatch at all — the final
          # result names it unreachable instead of failing mid-turn.
          - conditions: "{{ sat != '' and t not in down.split(',') }}"
            sequence:
              - action: script.turn_on
                target:
                  entity_id: script.ember_announce
                data:
                  variables:
                    message: "{{ message }}"
                    satellite: "{{ sat }}"
          # both: always dispatch — ember_announce_all is parallel: with
          # continue_on_error per branch, so one dark hearth costs only itself.
          - conditions: "{{ t == 'both' }}"
            sequence:
              - action: script.turn_on
                target:
                  entity_id: script.ember_announce_all
                data:
                  variables:
                    message: "{{ message }}"
      - variables:
          _function_result: >-
            {%- if t == 'both' -%}
            sent=both{% if down %}; hearth_unreachable={{ down }}; the message went to the rest{% endif %}
            {%- elif sat == '' -%}
            unknown_target={{ target }}; the hearths are desk, mobile, or both.
            {%- elif t in down.split(',') -%}
            hearth_unreachable={{ t }}; it may be off, flat, or out of the house; nothing was sent.
            {%- else -%}
            sent={{ t }}; note=dispatched, playback not awaited
            {%- endif -%}
```

- [ ] **Step 2: Diff against the live instance**

```bash
cd /home/jp/Projects/ember.realm.watch
./homeassistant/tools/ember-toolkit.py --diff
```

Expected: a diff showing ONLY the `send_word` addition to `functions`; skills
unchanged. If the live side shows other differences (JP edits live —
see CLAUDE.md's "the VM is frequently AHEAD" warning), STOP and reconcile
repo ← live before deploying, exactly as `deploy-ha.sh` would demand.

- [ ] **Step 3: Dry-run, then deploy**

```bash
./homeassistant/tools/ember-toolkit.py --deploy --dry-run
./homeassistant/tools/ember-toolkit.py --deploy
```

Expected: dry-run prints the intended submit; deploy reports the subentry
updated (it retries a transient `entry_not_loaded` read-back — that retry
succeeding is a pass, not a warning). No HA restart.

- [ ] **Step 4: Commit**

```bash
git add homeassistant/functions/ember-functions.yaml
git commit -m "feat(toolkit): send_word — speak a message on the other hearth (intercom relay v1)"
```

---

### Task 3: Verify `send_word` end-to-end

No files change. Reminder: the first turn after Task 2's deploy is the
expected ~15–20 s cold prefill.

- [ ] **Step 1: Directed message, desk**

```bash
HA=https://ha.jphe.in
TOKEN=$(cat ~/.cache/ha-token-tmp 2>/dev/null || echo "$HA_TOKEN")
BEFORE=$(curl -sS "$HA/api/states/sensor.ember_satellite_speaker_frames" -H "Authorization: Bearer $TOKEN" | jq -r .state)
curl -sS -X POST "$HA/api/conversation/process" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text": "Tell the desk that this is a send word test",
       "agent_id": "conversation.extended_openai_conversation_2",
       "language": "en"}' | jq -r .response.speech.plain.speech
sleep 8
AFTER=$(curl -sS "$HA/api/states/sensor.ember_satellite_speaker_frames" -H "Authorization: Bearer $TOKEN" | jq -r .state)
echo "frames: $BEFORE -> $AFTER"
```

Expected: Ember's reply acknowledges sending word to the desk (phrasing is
hers); frames strictly increase. Single chime (Ember's own), no HA blip —
that is the whole point of this path; if a double herald is audible here,
something is calling `assist_satellite.announce` outside `ember_announce`
and it is a bug to chase, not to document.

- [ ] **Step 2: Both hearths**

```bash
curl -sS -X POST "$HA/api/conversation/process" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text": "Send word to both hearths that supper is ready",
       "agent_id": "conversation.extended_openai_conversation_2",
       "language": "en"}' | jq -r .response.speech.plain.speech
```

Expected: both units speak (check both `speaker_frames` sensors climb if not
within earshot). If the mobile is currently unavailable, Ember's reply should
name it unreachable while the desk still speaks.

- [ ] **Step 3: Unreachable hearth (run whenever the mobile is actually off)**

With `assist_satellite.ember_mobile_assist_satellite` reading `unavailable`
(mobile powered off or flat — do not force it just for this; run the step
opportunistically):

```bash
curl -sS -X POST "$HA/api/conversation/process" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text": "Tell the mobile that this should not arrive",
       "agent_id": "conversation.extended_openai_conversation_2",
       "language": "en"}' | jq -r .response.speech.plain.speech
```

Expected: Ember says the hearth is unreachable (off, flat, or out of the
house) and does NOT claim to have sent it. If the mobile is on when this
task runs, record this step as deferred in the PR body rather than skipping
it silently.

---

### Task 4: Document the intercom

**Files:**
- Modify: `docs/home-assistant.md` — new §6.7 after §6.6, one row in the §9.2 tool table

- [ ] **Step 1: Add §6.7 after the end of §6.6 (before the `## 7 · Troubleshooting` rule)**

Insert, adjusting the two ⚠️/verified sentences to match what Task 1 Step 4
and Task 3 Step 1 actually observed:

```markdown
### 6.7 The intercom — sending word between hearths

Two ways to speak through the *other* Ember, layered deliberately
(design: `docs/superpowers/specs/2026-08-05-intercom-relay-design.md`):

**"Broadcast …" — the built-in path.** `prefer_local_intents` is on
([§6.4](#64-prefer_local_intents--why-its-on)), so HA's own `HassBroadcast`
intent catches *"broadcast [that] {message}"* before the LLM and announces on
every satellite **except the one that heard you** — with two Embers, exactly
"tell the other hearth". No LLM in the path means **this works while
`familiar` is asleep**: it is both the quickest intercom and the one of last
resort. Verified 2026-08-05 on HA 2026.7.4.

⚠️ The built-in path double-heralds, and that is accepted, not forgotten:
core's broadcast handler passes no `preannounce`, so the receiving Ember plays
HA's generic blip *and* its own chime. Fixing it means shadowing a built-in
intent (custom sentences + `intent_script`: a new deploy surface, no
source-device exclusion, registration-order fragility) for a cosmetic gain.
The polished path is `send_word`.

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
drawer is a normal state, not an error.

**Quiet hours are deliberately bypassed on both paths.** A person speaking
through Ember *is* the editorial decision; `script.ember_broadcast`'s
quiet-hours → Slack routing exists for automated events, not the intercom.

Live two-way audio (walkie-talkie / drop-in) is **not** this feature — the
research and the reasons it is a firmware project live in the issue named by
the design doc.
```

- [ ] **Step 2: Add the tool row to the §9.2 table**

In the tools table (after the `realm_query` row if present, else after
`look_at_camera`), add:

```markdown
| `send_word` | script | `assist_satellite.*` states | the intercom — speaks a message on the desk, the mobile, or both hearths ([§6.7](#67-the-intercom--sending-word-between-hearths)) |
```

Also update the sentence above the table that counts the tools (it says
"Ten total: the integration's stock four, plus six from this repo" —
make it eleven / seven, and check the count matches
`grep -c '^- spec:' homeassistant/functions/ember-functions.yaml`).

- [ ] **Step 3: Commit**

```bash
git add docs/home-assistant.md
git commit -m "docs(ha): the intercom — the broadcast path and send_word (§6.7)"
```

---

### Task 5: Open the live-audio research issue

No repo files change.

- [ ] **Step 1: Create the issue**

```bash
gh issue create \
  --title "Live two-way audio intercom (walkie-talkie / drop-in) — research capture" \
  --body "$(cat <<'EOF'
v1 intercom shipped as a spoken relay (design:
`docs/superpowers/specs/2026-08-05-intercom-relay-design.md`): the built-in
`HassBroadcast` intent plus the `send_word` tool, both riding
`assist_satellite.announce`. This issue captures the research for the part
deliberately NOT built: live audio streaming between the two boards.

## What the community does

- **fallingaway24/esphome-2Way-INTERCOM** — full-duplex raw PCM over UDP
  (16 kHz 16-bit mono), P2P via mDNS or through go2rtc for WebRTC/browser
  join. ESP32-S3, external component.
  https://github.com/fallingaway24/esphome-2Way-INTERCOM
- **samuelthng/intercom-api** — ESP-to-ESP UDP with ESP-SR echo
  cancellation; claims voice-assistant compatibility (undocumented how).
  https://github.com/samuelthng/intercom-api
- **n-IA-hane/esphome-intercom** — a full VoIP/SIP stack: phonebook, HA
  softphone, Assist intents for call control. The heaviest option.
  https://github.com/n-IA-hane/esphome-intercom

## Why it is a firmware project, not an easy add

- **The I2S arbiter.** Chimes and speech already share one decoder
  (`single_pipeline_()`), and the arbiter is a documented
  do-not-simplify zone that cost real debugging time. None of the three
  projects documents coexistence with `voice_assistant` +
  `micro_wake_word` on a shared I2S bus.
- **Echo cancellation** needs ESP-SR at ~22% CPU, wants octal PSRAM —
  verify what the ES3C28P actually has before believing any of it fits.
- **The mobile unit runs on a bare 18650** (no protection IC, #44): a
  continuous audio stream is a very different power profile from
  push-to-talk turns.

## What a v2 would have to prove before merging

1. Intercom stream and the existing chime/TTS pipeline sharing the I2S bus
   without regressing §7.1-class bugs (measure `speaker_frames`, not ears).
2. Wake/talk gesture and `micro_wake_word` suspended and restored cleanly
   around a call.
3. Battery draw on the mobile unit during a call, measured.
EOF
)"
```

Expected: prints the new issue URL.

- [ ] **Step 2: Cross-reference the issue number in the docs**

Replace the last paragraph of §6.7 ("…live in the issue named by the design
doc") with the real number, e.g. `(#57)`, matching the URL from Step 1. Also
add the number in the design doc's "Deferred" paragraph
(`docs/superpowers/specs/2026-08-05-intercom-relay-design.md`, the
"deferred to a GitHub issue" sentence).

```bash
git add docs/home-assistant.md docs/superpowers/specs/2026-08-05-intercom-relay-design.md
git commit -m "docs: pin the live-audio research issue number"
```

---

### Task 6: Finish the branch

- [ ] **Step 1: Final review of the whole diff**

```bash
git log --oneline main..feat/intercom-relay
git diff main...feat/intercom-relay
```

Expected: the spec, the tool, the docs, the issue-number pin. Check for
secrets: `git diff main...feat/intercom-relay | grep -iE 'api.?key|token|secret' | grep -v '!secret'`
must print nothing.

- [ ] **Step 2: Hand off for ship decision**

Use superpowers:finishing-a-development-branch — push, PR
(`feat/intercom-relay` → `main`, referencing the research issue), and note in
the PR body: whether Task 3 Step 3 (unreachable hearth) ran or was deferred,
and what Task 1 Step 4 observed about the double herald. Then return to
`main` (CLAUDE.md end-of-task rule).
