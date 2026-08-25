# STT mic analysis — what Parakeet actually hears (#56)

*2026-08-24. Data: the 40 utterances saved by wyoming-onnx-asr's `--save-audio` tap on
`familiar` (`/opt/wyoming-onnx-asr/debug-audio`), spanning 2026-08-12 → 2026-08-24.
Analyzer: [`esphome/tools/analyze_stt_audio.py`](../esphome/tools/analyze_stt_audio.py) —
run `ssh familiar "python3 -" < esphome/tools/analyze_stt_audio.py` to reproduce or
re-measure after a change.*

## What these recordings are (and are not)

The tap saves **exactly the bytes Home Assistant forwarded from the satellite's mic** —
i.e. *after* the ESP-side processing chain (`noise_suppression_level: 2`,
`auto_gain: 31dBFS`, `volume_multiplier: 2.0` in `voice_assistant:`). These numbers
measure what the STT model sees, which is the quantity that decides transcription.

Two limitations, so nobody over-reads the data:

- **No device tag.** HA does not tell Wyoming which satellite spoke, so desk vs mobile
  recordings are indistinguishable here.
- **Not the raw mic.** The on-device `sound_level` sensor taps the raw ring buffer,
  *before* this processing. Do **not** calibrate the level-meter `db_floor`/`db_ceil`
  substitutions from these numbers — different tap, different domain.

Distances below are inferred from level physics (−6 dB per doubling), not measured.
Nothing in this analysis was verified by listening to the audio.

## Method

30 ms frames; noise floor = mean RMS of the quietest 10% of frames; speech level =
95th-percentile frame RMS and RMS over active frames (>3× noise); SNR = p95 − floor;
clipping = samples at ≥32700 of 32767 full scale, with the longest consecutive run
(an isolated 1-sample hit is an impulse spike, not saturation). All dBFS.

## Headline: failures are a *level* problem, not a clipping problem

Of the 40 files: 11 are sub-200 ms spurious triggers (the server ignores them —
`MIN_AUDIO_MS = 200`), 1 is pure digital silence (below), leaving **28 real
utterances: 12 clean transcripts, 4 garbled, 12 empty.** A ~43 % clean rate.

The outcome tracks speech level and SNR almost perfectly:

| outcome | speech RMS (dBFS) | SNR (dB) |
|---|---|---|
| clean transcript (12) | −14 … −42 | 15 … 46 |
| garbled — "tricky me.", "my phone.", "Nadu. Mm-hmm." (4) | −35 … −49 | 12 … 21 |
| empty transcript, real speech present (≈9 of 12) | −28 … −51 | 4 … 19 |

**Empirical threshold: speech RMS ≥ ~−40 dBFS *and* SNR ≥ ~18 dB transcribes cleanly;
below either, results degrade to fragments and then to nothing.** The cleanest border
pair: `utt-20260824-203229` ("How are you doing, Ember?", −34.6 dBFS / 15.2 dB, clean)
vs `utt-20260824-213843` (−37.2 dBFS / 15.7 dB, empty) — right at the line, a coin flip.

**Clipping is a non-issue at the current 36 dB mic gain.** 33 of 40 files have zero
clipped samples. The worst file has 58 (0.07 % of its samples), longest run 5 samples
(0.3 ms). Close-talk recordings peak at −0.0 dBFS with exactly *one* clipped sample —
the ceiling is being touched, not leaned on.

The 15.0 s files (the pipeline's max-utterance timeout) are all empty-transcript with
near-zero active-frame fraction: speech too quiet for the VAD to segment, so the
pipeline waits out the full window. Same root cause, second symptom.

## Distance falloff

Two clear regimes in the data:

- **Close-talk** (2026-08-14 evening, "Run the tests in the Veil session" ×3, plus
  18:13): speech RMS −14 … −17 dBFS, SNR 39–46 dB, **4/4 perfect transcripts**.
- **Normal room use** (everything else): speech RMS −30 … −51 dBFS, SNR 6–28 dB,
  clean rate roughly half.

The 20–33 dB gap between regimes is 3.5–5.5 distance doublings — consistent with
~10–15 cm close-talk vs 1.5–4 m across-the-room. At room distance the post-processing
speech level lands only 10–20 dB above the (already noise-suppressed) floor, which is
exactly where the threshold above says Parakeet starts dropping words.

Noise floor is −62 dBFS on quiet days, −49 … −54 dBFS on several files (room noise /
fan). The failures on 08-24 (`203315`, `213843`) coincide with the noisier −49 … −54
floor. DC offset is negligible everywhere (≤ 8 counts; one file at 256 counts, still
−42 dBFS).

## Anomalies (not gain problems — filed so nobody chases them as one)

- **`utt-20260816-114113`**: 5.1 s of *exact digital zeros*. The mic path delivered
  silence — an I2S handoff/capture failure, one instance in 12 days. If it recurs,
  it is a firmware bus question, not a gain question.
- **`utt-20260816-191457`**: healthy level (−22.3 dBFS, 34 dB SNR), 58 clipped
  samples, yet an empty transcript. The one outlier that breaks the level pattern —
  possibly non-speech audio (TV/music). Single instance; noted, not diagnosed.
- **11 sub-200 ms triggers** (clustered 08-16/08-17): the pipeline started and
  delivered ~30 ms of room noise. Spurious activations — wake-word false accepts or
  touch mishits. `MIN_AUDIO_MS` already stops them reaching the model; the cost is
  log noise and a pointless chime. Worth an eye, not action.

## Proposed changes

### 1. Mic gain 36 → 42 dB — the live slider first, no flash

The ES8311's analog PGA is the **only stage ahead of quantization and noise
suppression**, so it is the only knob that improves what the whole downstream chain
has to work with. The data bounds the risk that made 36 dB the conservative choice
(`ember-satellite.yaml` line ~1184, "stacked on auto_gain and volume_multiplier that
clips"): at 36 dB there is *no sustained clipping anywhere in 12 days of captures*,
while far-field speech sits 0–10 dB *below* the transcription threshold. +6 dB moves
typical room-distance speech from −45 → −39 dBFS — across the line.

Cost: close-talk already touches −0.0 dBFS peaks; at 42 dB it will clip harder. But
close-talk has 25+ dB of SNR margin and transcribed 4/4 — it can afford it. Far-field
is the failing regime and gets the entire benefit.

**How: flip `number.ember_satellite_mic_gain` and `number.ember_mobile_mic_gain` to
42 dB in HA** (or one press of the on-screen mic-gain "+" in the touch overlay — same
number entity). The slider writes REG16 live and `restore_value: true` persists it
across reboots — no reflash, reversible in seconds. Then let a week of debug-audio
accumulate and re-run the analyzer; success = clean-rate up, far-field speech RMS
≥ −40 dBFS, `clip_run_max` staying in single digits.

If validated, bake it in firmware so a factory-reset board boots there:
`initial_value: 36` → `42` on `mic_gain_num` *and* `mic_gain: 36db` → `42db` on the
`audio_dac` (the pre-restore boot seed). That commit should also update the
line-1184 comment — per `docs/verification.md` §32 discipline, retire its clipping
warning with the date and the observation that retired it (this document).

### 2. Leave `auto_gain: 31dBFS` / `volume_multiplier: 2.0` alone

These recordings are *post* that chain, and far-field speech still arrives at
−45 dBFS — so more digital gain would amplify signal and suppressed noise floor
alike, buying loudness but no SNR. Change one knob, measure, then decide. If 42 dB
analog proves insufficient, the next lever is acoustic (speaking distance, enclosure
mic porting), not more digital multiplication.

### 3. Re-measure with the same ruler

`esphome/tools/analyze_stt_audio.py` is now in-repo so the before/after comparison
uses identical definitions. Baseline to beat, from this dataset: **12/28 clean
(43 %)**; far-field speech RMS median ≈ −45 dBFS.

## Appendix: per-file measurements (2026-08-24 snapshot)

All values dBFS except as noted; generated by the analyzer with `--md`. The
analyzer prints verbatim transcripts; here they are deliberately reduced to an
outcome class, because `docs/` is the public Pages root and household speech
does not belong on it.

| file | dur_s | peak_dbfs | speech_rms_dbfs | noise_floor_dbfs | snr_db | clip_samples | clip_run_max | outcome |
|---|---|---|---|---|---|---|---|---|
| utt-20260812-090954.wav | 8.02 | -26.0 | -42.3 | -61.0 | 21.1 | 0 | 0 | clean |
| utt-20260812-091033.wav | 3.78 | 0.0 | -34.2 | -61.6 | 22.2 | 3 | 3 | clean |
| utt-20260812-091103.wav | 5.37 | -15.6 | -32.1 | -51.1 | 23.1 | 0 | 0 | clean |
| utt-20260812-110130.wav | 5.16 | -24.3 | -39.3 | -63.4 | 27.9 | 0 | 0 | clean |
| utt-20260812-110246.wav | 9.44 | -29.0 | -46.2 | -63.8 | 19.9 | 0 | 0 | clean |
| utt-20260812-110315.wav | 15.0 | -16.7 | -26.1 | -38.6 | 4.3 | 0 | 0 | empty |
| utt-20260812-110357.wav | 5.18 | -31.2 | -45.0 | -62.1 | 19.0 | 0 | 0 | garbled |
| utt-20260812-110416.wav | 2.73 | 0.0 | -32.4 | -61.0 | 18.9 | 2 | 1 | empty |
| utt-20260812-162551.wav | 8.84 | -28.5 | -49.0 | -62.5 | 12.1 | 0 | 0 | garbled |
| utt-20260812-162621.wav | 4.02 | 0.0 | -34.9 | -62.1 | 21.0 | 5 | 4 | garbled |
| utt-20260812-162646.wav | 15.0 | 0.0 | -28.1 | -62.4 | 7.2 | 4 | 3 | empty |
| utt-20260812-175434.wav | 15.0 | -14.0 | -46.7 | -64.0 | 18.1 | 0 | 0 | empty |
| utt-20260814-121420.wav | 5.21 | -16.5 | -30.5 | -53.9 | 24.0 | 0 | 0 | clean |
| utt-20260814-141639.wav | 6.07 | -19.0 | -44.8 | -63.3 | 14.6 | 0 | 0 | empty |
| utt-20260814-181327.wav | 3.39 | -0.2 | -16.6 | -51.2 | 38.8 | 0 | 0 | clean |
| utt-20260814-214229.wav | 2.26 | -0.0 | -14.3 | -51.9 | 42.9 | 1 | 1 | clean |
| utt-20260814-214312.wav | 2.24 | -0.0 | -14.1 | -54.1 | 45.6 | 1 | 1 | clean |
| utt-20260814-214410.wav | 2.38 | -0.0 | -14.2 | -54.4 | 45.1 | 1 | 1 | clean |
| utt-20260815-082703.wav | 15.0 | -43.6 | -51.8 | -61.8 | 6.0 | 0 | 0 | empty |
| utt-20260816-114113.wav | 5.1 | -120.0 | - | -120.0 | 0.0 | 0 | 0 | empty (digital zeros) |
| utt-20260816-120433.wav | 0.03 | -54.5 | - | -62.6 | 0.0 | 0 | 0 | too short (ignored) |
| utt-20260816-122105.wav | 0.03 | -58.7 | - | -65.9 | 0.0 | 0 | 0 | too short (ignored) |
| utt-20260816-122321.wav | 0.03 | -62.4 | - | -70.1 | 0.0 | 0 | 0 | too short (ignored) |
| utt-20260816-122327.wav | 0.03 | -58.3 | - | -67.8 | 0.0 | 0 | 0 | too short (ignored) |
| utt-20260816-122524.wav | 0.15 | -56.2 | - | -67.6 | 2.7 | 0 | 0 | too short (ignored) |
| utt-20260816-191457.wav | 5.42 | 0.0 | -22.3 | -63.8 | 34.4 | 58 | 5 | empty |
| utt-20260816-215915.wav | 0.03 | -55.8 | - | -64.2 | 0.0 | 0 | 0 | too short (ignored) |
| utt-20260816-221734.wav | 0.03 | -58.5 | - | -65.0 | 0.0 | 0 | 0 | too short (ignored) |
| utt-20260816-222123.wav | 0.06 | -56.0 | - | -66.1 | 1.8 | 0 | 0 | too short (ignored) |
| utt-20260817-002016.wav | 0.03 | -57.2 | - | -64.6 | 0.0 | 0 | 0 | too short (ignored) |
| utt-20260817-002653.wav | 0.03 | -61.1 | - | -66.2 | 0.0 | 0 | 0 | too short (ignored) |
| utt-20260817-164430.wav | 2.49 | -34.9 | -45.8 | -58.9 | 13.8 | 0 | 0 | garbled |
| utt-20260817-164521.wav | 15.0 | -15.3 | -44.5 | -59.7 | 9.7 | 0 | 0 | empty |
| utt-20260817-184202.wav | 3.27 | -40.3 | -50.9 | -63.6 | 12.5 | 0 | 0 | empty |
| utt-20260819-073439.wav | 15.0 | -39.3 | -47.4 | -61.8 | 6.6 | 0 | 0 | empty |
| utt-20260822-084209.wav | 3.03 | -37.0 | -49.6 | -61.8 | 10.1 | 0 | 0 | empty |
| utt-20260823-144747.wav | 5.14 | -18.1 | -36.5 | -51.9 | 17.8 | 0 | 0 | clean |
| utt-20260824-203229.wav | 4.07 | -24.1 | -34.6 | -48.8 | 15.2 | 0 | 0 | clean |
| utt-20260824-203315.wav | 15.0 | -26.3 | -39.6 | -49.8 | 5.8 | 0 | 0 | empty |
| utt-20260824-213843.wav | 4.47 | -16.0 | -37.2 | -53.8 | 15.7 | 0 | 0 | empty |
