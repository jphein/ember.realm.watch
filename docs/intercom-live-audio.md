# Live two-way audio intercom — research capture

Status: **research only, nothing built, nothing approved.** This is the deliverable of
[#57](https://github.com/jphein/ember.realm.watch/issues/57): the survey, the constraints,
a recommended shape *if* a v2 is ever green-lit, and the questions only JP can answer.

**Provenance discipline** (this repo's, per `docs/verification.md`): every claim below is
tagged. *[repo]* means verified against this repo's files, which are themselves traced to
source or bench. *[README, 2026-08-24]* means read from a community project's documentation
on that date — **a claim someone else published, not a thing anyone here has run.** Nothing
in this document has been bench-verified on an ES3C28P by us.

---

## 1 · Where v1 already leaves us

The spoken relay shipped, and it is more capable than the issue text assumes — three
hearths now, not two:

| hearth | power | where |
|---|---|---|
| desk (`ember-satellite`) | mains | JP's desk |
| mobile (`ember-mobile`) | 1× 18650 (protection strip fitted) | roams the house |
| dad (`ember-dad`) | 1× 18650 (protection strip fitted) | **Dad's house**, behind the south-dads realm AP |

What already works, all without live audio *[repo]*:

- **`HassBroadcast`** — "broadcast that dinner is ready" reaches every other satellite,
  locally, even with `familiar` asleep.
- **`send_word`** — the LLM tool for directed messages
  (`docs/superpowers/specs/2026-08-05-intercom-relay-design.md`).
- **The horn** — a drawn button on each hearth (action 16) that opens a **speaker picker**
  (ui_mode 7), captures speech via `assist_satellite.ask_question` STT, and relays the
  *transcription* to the chosen hearth through `script.ember_intercom_to`. No LLM in the
  chain; works while `familiar` sleeps.

So the gap v2 would close is precisely and only: **the receiving hearth plays a
reconstruction of your words in Ember's voice, not your actual voice, and there is no
continuous conversation** — each exchange is a discrete captured turn. Whether that gap is
worth a firmware project is the first open question (§6).

---

## 2 · The constraints any v2 must live inside

### 2.1 The bus is simplex in software, duplex in hardware

One I2S bus (`GPIO4/5/7`), one ES8311 mono codec carrying both the analog MEMS mic
(DIN `GPIO6`) and the speaker (DOUT `GPIO8`), both at 16 kHz / 16-bit mono *[repo:
`esphome/ember-satellite.yaml` i2s section]*.

ESPHome's stock `i2s_audio` is **simplex behind one mutex**: the microphone takes the bus
lock for its entire running life (`i2s_audio_microphone.cpp:98,228`), the speaker asks with
a non-blocking `try_lock()` and retries every second forever
(`i2s_audio_speaker_standard.cpp:400`). That is why the wake-word arbiter exists at all
*[repo: "THE WAKE-WORD ARBITER" comment block]*. Upstream knows the shape — the same
contention is filed as [esphome#16043](https://github.com/esphome/esphome/issues/16043)
on ESP32-P4.

The **hardware** has no such limit. The ES8311 runs ADC and DAC simultaneously on one bus;
vendor firmware for this codec class (Espressif Korvo BSP, xiaozhi) creates duplex channels
once and never tears them down *[repo: amp-blanking comment, independently confirmed by
nebula's prior-art review]*. Full-duplex intercom on this board is therefore **not blocked
by hardware — it is blocked by ESPHome's audio component architecture**, and every
community project below solves it the same way: by replacing that layer.

### 2.2 Replacing the audio layer invalidates a museum of paid-for fixes

This is the real cost, and the issue undersells it. The following mechanisms are all keyed
to ESPHome's simplex load/unload behavior, several with line-numbered citations into the
exact source they'd no longer be running on *[repo]*:

| mechanism | what it assumes | fate under a duplex stack |
|---|---|---|
| the wake-word arbiter (100 ms interval + predictive yields in `ui_dispatch`, `on_announcement`, `talk_begin`) | mic and speaker fight over one mutex | **obsolete** — duplex means nobody yields; must be deleted, not ported |
| DAC-mute manager + amp blanking | every playback starts with `i2s_del_channel`/enable → MCLK cold-start transient | **obsolete in the good direction** — a clock that never stops has no cold-start pop. But this must be *demonstrated*, not assumed |
| `timeout: 500ms` speaker tuning, `talk_begin`'s wait-for-release | driver load/unload cycles exist | obsolete |
| the silence gate + chime guard (op_mode / Hush) | `spk->is_running()` distinguishes speech; declining-to-unmute silences it | **must be re-derived** — with the driver always running, `is_running()` stops meaning "audio now" |
| `spk_frames` + the display's SPEAKING promotion | frame callback fires only during real playback | must be re-verified against the new stack's callback semantics |

Net: a migration deletes roughly as much hard-won code as it adds, and the ⚠️ comment
corpus — this repo's documentation of record — needs a matching pass, each retirement dated
per the CLAUDE.md rule. The one genuine upside: the entire pop-management apparatus exists
*because* ESPHome stops the clock; a duplex stack removes the disease, not just the symptom.

### 2.3 Echo — the acoustic problem, and what the board can afford

Mic and speaker share one small enclosure, centimetres apart, and there is **no acoustic
echo cancellation today** — the pipeline's `noise_suppression` and `auto_gain` are not AEC
*[repo: listening-chime comment]*. Full-duplex without AEC on this geometry is a feedback
machine.

What the community reports about ESP-SR AEC on the S3 *[README, 2026-08-24, all of it]*:

- `sr_low_cost` (linear adaptive filter): **~22 % CPU**, preserves spectral features, so
  microWakeWord keeps working on the post-AEC stream.
- `voip_low_cost` (Speex): ~58 % CPU, and samuelthng reports it degrades wake-word
  detection "from 10/10 to 2/10". Not compatible with keeping "Okay Nabu" alive in a call.
- PSRAM is required.

**The PSRAM question the issue asked is answered**: the ES3C28P carries an N16R8 module —
**8 MB octal (OPI) PSRAM**, 16 MB flash, and the config is already `esp-idf` *[repo:
`esp32:`/`psram:` blocks, traced to the vendor schematic]*. So ESP-SR's stated requirements
are met on paper. What is *not* answered is contention: the display already spends up to
60 ms of main-loop per full frame with the fire buffer living in that same PSRAM, and the
500 ms speaker buffer exists precisely because main-loop time is the scarce resource here
*[repo: `buffer_duration` comment]*. 22 % sustained CPU for AEC plus a pinned audio task
plus the fire has to be measured, not believed.

**Half-duplex sidesteps all of this.** A push-to-talk call never has mic and speaker live
at the same instant, needs no AEC, and matches what "walkie-talkie" means anyway. That is
the single biggest scope lever available.

### 2.4 The assist pipeline must survive a call

- `micro_wake_word` (mode 1, on-device "Okay Nabu") must be suspended for the duration of
  a call and restored after — the issue's proof-point 2. Under the stock stack that is the
  arbiter's job; under a duplex stack the projects claim the *opposite* discipline: wake
  word keeps running on the post-AEC mic even during playback *[README, 2026-08-24]*.
  Either way the transition edges (call start, call end, call while a conversation is
  running, conversation attempt mid-call) are exactly where §7.1-class bugs live.
- Verification is by counter, not by ear: `sensor.ember_*_speaker_frames` climbing at
  16 000/s on the receiving unit is the delivery proof; chime/TTS regression checks measure
  the same counter *[repo: relay spec §verification, home-assistant.md §7.1]*.
- A call must obey the silence ladder: **Hush means no sound, including a ringing call**,
  and `amp_switch` remains the user's master over everything *[repo: silence-gate block]*.

### 2.5 Power on the battery hearths

Two of three hearths run on a bare 18650 behind a 1S protection strip. A live call is
continuous WiFi TX + amp + (if full-duplex) AEC CPU — a different profile from
push-to-talk turns, and nobody has measured it (the issue's proof-point 3). The battery
ladder (candle, guttering chime at ≤ 20 %, critical alarm via `ember_battery_watch`)
already exists as the warning surface; an SOC gate on *accepting* calls is a plausible
policy (§6).

### 2.6 Topology — the constraint the issue predates

`ember-dad` lives in **another house**, behind the south-dads realm AP *[repo:
`ember-dad.yaml` header]*. Every P2P design in the survey assumes one L2 segment: raw UDP
to an mDNS-discovered peer does not cross houses unless the realm network makes it look
flat. The moment dad's hearth is in scope — and a live voice call to Dad is arguably the
*strongest* use case here — the architecture needs either routed transport over the
site-to-site link or a server hop (go2rtc, or SIP with HA as the registrar). This
reshapes the option ranking below and is a question about the realm network as much as
about firmware.

---

## 3 · The survey, as of 2026-08-24

All four are MIT-licensed, ESP-IDF, external components. All claims *[README,
2026-08-24]* unless marked.

### A · fallingaway24/esphome-2Way-INTERCOM

Raw UDP PCM (16 kHz/16-bit mono, 1024-byte packets + 4-byte sequence), P2P via mDNS or
through go2rtc (HA ≥ 2024.11 has it built in) for WebRTC/browser join. Custom
`i2s_audio_udp` / `mdns_discovery` / `esp_aec` components that **bypass ESPHome's audio
infrastructure entirely**; full-duplex via separate DMA channels; optional ESP-SR AEC.
Tested on Xiaozhi Ball V3 (an ES8311-class S3 device). **No documented coexistence with
`voice_assistant` / `micro_wake_word`** — the issue's characterization stands for this one.
Simplest transport, weakest integration story.

### B · samuelthng/intercom-api

A fork of the n-IA-hane work. ESP-to-ESP over **TCP :6054** (1024-byte / 32 ms chunks,
typed 4-byte headers), full-duplex via a custom `i2s_audio_duplex` component, `esp_aec`
with the `sr_low_cost` / `voip_low_cost` modes described in §2.3. **Documents the
coexistence claim the issue flagged as undocumented**: "MWW + VA + intercom all use the
same post-AEC mic". Ships an HA integration (`intercom_native`: PBX hub + Lovelace card).
The issue's "undocumented how" is therefore **retired for this project — by reading, not
by bench** (per verification.md discipline, that distinction is the whole point).

### C · n-IA-hane/esphome-intercom

Full **SIP/2.0 + RTP** stack: HA-managed phonebook (`sensor.voip_phonebook`), browser
softphones, ring/conference groups, optional SIP trunk, and — notably — **Assist pipelines
as phonebook destinations**. Requires ESPHome ≥ 2026.6.5 / HA 2026.7.x (Ember is verified
on 2026.8.0, so compatible on paper). Heaviest, but standards-based, which is exactly what
the cross-house topology in §2.6 wants: SIP was built for endpoints that are not on one
LAN. Actively maintained, 670+ commits.

### D · n-IA-hane/esphome-audio-stack — the actual decision underneath

The foundation under C (and by lineage, B): a **full-duplex audio backend replacing
`i2s_audio`** — codec ownership via `esp_codec_dev` (**ES8311 explicitly the recommended
single-bus codec**), one pinned FreeRTOS task with an `idle/mic/speaker/duplex` state
machine, AEC topologies including software-reference and ES8311-class DAC feedback, and —
the load-bearing claim — **standard ESPHome `microphone`/`speaker` interfaces on top, so
`voice_assistant`, `micro_wake_word`, and `media_player` run unmodified**. PSRAM
mandatory (have it), ESP-IDF only (already are), S3 release-tested.

This reframes the whole issue: the real v2 decision is **"replace the audio layer or
not"**, and the intercom protocol on top (UDP vs TCP vs SIP) is the smaller, swappable
choice.

---

## 4 · Recommended architecture, if v2 is ever green-lit

**Recommendation: the audio-stack family (D as foundation, C's SIP layer for transport),
half-duplex push-to-talk first, proven on a bench board that is none of the three
production hearths.** Reasoning:

1. **D is the only option that even claims to preserve the existing pipeline** —
   `voice_assistant` + `micro_wake_word` unmodified is the property everything in §2.2
   and §2.4 cares about. A is disqualified by its silence on exactly that.
2. **SIP survives the topology** (§2.6): dad's hearth stops being a special case the
   moment the transport has a registrar instead of an mDNS assumption. HA is already the
   hub of everything else Ember does.
3. **PTT-first cuts the two riskiest axes at once**: no AEC needed (echo, §2.3) and a
   bounded, turn-shaped power profile (battery, §2.5). Full-duplex with `sr_low_cost` AEC
   becomes a later experiment on the same stack, not a different architecture.
4. **The horn is already the right UI seam**: the picker (ui_mode 7) chooses a hearth
   today; a long-press-to-talk or a picker entry that opens a call is an extension of a
   shipped surface, not a new gesture language. The fire has a state for everything —
   a joined-hearths state is a display question for later, noted and parked.

Staged, each stage a separate go/no-go:

- **Stage 0 — bench spike, fourth board.** audio-stack alone on a spare ES3C28P: duplex
  bring-up on ES8311, then the §5 coexistence matrix, measured by `speaker_frames` and
  logs, not ears. *No production hearth is flashed in stage 0.* (The sealed Espressif
  spare on katana's bench belongs to reliquary — per repo CLAUDE.md it is never a test
  target. A fourth board is ~the price of a takeaway meal.)
- **Stage 1 — LAN PTT, desk ↔ mobile.** The migration cost of §2.2 is paid here, as its
  own reviewed change, before any intercom feature lands on top.
- **Stage 2 — cross-house, dad.** Only after the realm-network question (§6) is settled.

**Doing nothing is a respectable outcome.** v1 relay + the horn covers "send word" in both
directions on all three hearths with zero firmware risk. v2 buys presence — the actual
voice, the open channel — at the cost of replacing the most carefully documented subsystem
in the repo. That trade is JP's to make, not this document's.

---

## 5 · What a v2 must prove before merging (expanded from the issue)

1. **Bus coexistence, measured**: intercom stream, chime, and TTS on one bus with no
   §7.1-class regression — `speaker_frames` advances correctly for each audio class, on
   both ends, including chime-during-call and announce-during-call. Not ears.
2. **Wake-word lifecycle**: `micro_wake_word` suspended and restored around a call, with
   the four transition edges of §2.4 each exercised; if the post-AEC-mic claim is relied
   on instead, *that claim gets bench-verified first* — it is currently a README sentence.
3. **Battery draw during a call, measured** on a real 18650 hearth: idle vs PTT vs (if
   attempted) full-duplex with AEC, long enough to see the candle move.
4. **Silence ladder honored**: Hush rejects/ silences calls; `amp_switch` overrides all.
5. **Pop status re-established**: the §2.2 prediction that a never-stopped clock has no
   transient is verified with the amp-blanking apparatus *disabled*, before any of it is
   deleted — retire warnings by dated observation, per CLAUDE.md.
6. **Main-loop budget**: fire animation frame times with the pinned audio task (and AEC,
   if full-duplex) running — the display, not the audio, is the likely first victim.

---

## 6 · Open questions for JP

1. **Is v2 wanted at all?** Does the relay's remaining gap (§1) — real voice, open
   channel — justify replacing the audio layer? If drop-in-to-Dad is the killer use case,
   say so; it changes the ordering (SIP earlier, LAN P2P never).
2. **Buy a fourth ES3C28P for the bench?** Stage 0 has no other safe substrate.
3. **PTT or full-duplex as the target?** PTT is the recommendation; full-duplex is where
   the AEC/CPU/battery risk concentrates.
4. **Can dad's site carry it?** Is south-dads reachable from the home LAN at the IP layer
   (site-to-site tunnel), and with what latency/jitter? SIP-through-HA vs go2rtc vs
   nothing hangs on this. A realm-network question, not an Ember one.
5. **Privacy posture of drop-in.** A hearth that can be *opened* remotely is a live
   microphone in someone else's room — Dad's room. Ring-before-connect (callee taps to
   accept) vs true drop-in (auto-answer with a chime + full-screen fire state) is a
   consent policy, and on `ember-dad` it is a policy about a person who never reads this
   repo. Recommend: ring-before-connect everywhere, no silent open, ever; Hush refuses.
6. **Battery policy**: refuse (or warn into) calls below an SOC threshold on 18650
   hearths, or let the existing ladder be the only guard?
7. **Upstream bet**: audio-stack is a single-maintainer external component replacing the
   audio layer of three production devices. Acceptable, or is "wait for ESPHome upstream
   duplex support" (no signal it is coming; #16043 is open) the position?

---

## Sources

- This repo: `esphome/ember-satellite.yaml` (arbiter, I2S, silence gate, amp blanking),
  `esphome/ember-dad.yaml`, `docs/home-assistant.md` §7.1,
  `docs/superpowers/specs/2026-08-05-intercom-relay-design.md`,
  `docs/superpowers/specs/2026-08-05-intercom-button-design.md`, `docs/verification.md`.
- [fallingaway24/esphome-2Way-INTERCOM](https://github.com/fallingaway24/esphome-2Way-INTERCOM) *(fetched 2026-08-24)*
- [samuelthng/intercom-api](https://github.com/samuelthng/intercom-api) *(fetched 2026-08-24)*
- [n-IA-hane/esphome-intercom](https://github.com/n-IA-hane/esphome-intercom) *(fetched 2026-08-24)*
- [n-IA-hane/esphome-audio-stack](https://github.com/n-IA-hane/esphome-audio-stack) *(fetched 2026-08-24)*
- [esphome/esphome#16043](https://github.com/esphome/esphome/issues/16043) — shared-bus mic/speaker contention upstream
