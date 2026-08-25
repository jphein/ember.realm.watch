#!/usr/bin/env python3
"""Analyze the STT debug recordings: levels, clipping, SNR, transcript outcome.

The wyoming-onnx-asr service on familiar tees every utterance to
/opt/wyoming-onnx-asr/debug-audio when started with --save-audio: the .wav is
EXACTLY the bytes Home Assistant forwarded from the satellite's microphone —
i.e. post the ESP-side processing chain (noise_suppression_level,
auto_gain, volume_multiplier in voice_assistant:) — and the sidecar .txt is
what the model made of them. So these numbers measure what Parakeet actually
sees, not what the mic hears. The on-device sound_level sensor taps the RAW
mic ring buffer instead; do not calibrate db_floor/db_ceil from this output.

Run it where the recordings are (needs numpy; familiar has it):

    ssh familiar "python3 -" < esphome/tools/analyze_stt_audio.py
    # or, against a local copy:
    python3 esphome/tools/analyze_stt_audio.py /path/to/debug-audio [--md]

Method, so the numbers mean the same thing next time:
  - frames of 30 ms; noise floor = mean RMS of the quietest 10% of frames
  - speech level = 95th-percentile frame RMS, and RMS over "active" frames
    (frame RMS > 3x noise floor)
  - SNR = p95 speech - noise floor, both in dBFS
  - clipping = samples with |s| >= 32700 of 32767, plus the longest
    consecutive run (isolated 1-sample hits are impulse spikes, not
    sustained saturation)

First used for issue #56 (2026-08-24); findings in docs/stt-mic-analysis.md.
"""
import glob
import json
import os
import sys
import wave

import numpy as np

FRAME = 480  # 30 ms @ 16 kHz
CLIP_AT = 32700


def dbfs(x):
    if x <= 0:
        return -120.0
    return 20.0 * np.log10(x / 32768.0)


def analyze_file(wav_path):
    stem = wav_path[:-4]
    txt_path = stem + ".txt"
    transcript = None
    if os.path.exists(txt_path):
        with open(txt_path, "r", errors="replace") as f:
            transcript = f.read().strip()
    row = {"file": os.path.basename(wav_path), "transcript": transcript}
    try:
        with wave.open(wav_path, "rb") as w:
            nch, sw, sr, nframes = (
                w.getnchannels(),
                w.getsampwidth(),
                w.getframerate(),
                w.getnframes(),
            )
            raw = w.readframes(nframes)
    except Exception as e:
        row["error"] = str(e)
        return row
    if sw != 2:
        row["error"] = f"sampwidth={sw}, expected 16-bit"
        return row
    s = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if nch > 1:
        s = s.reshape(-1, nch)[:, 0]
    row["sr"] = sr
    row["dur_s"] = round(len(s) / sr, 2) if sr else 0.0
    if len(s) < FRAME:
        row["error"] = "too short to analyze"
        return row

    clip_mask = np.abs(s) >= CLIP_AT
    n_clip = int(np.sum(clip_mask))
    longest_run = 0
    run = 0
    for v in clip_mask:
        run = run + 1 if v else 0
        longest_run = max(longest_run, run)

    nfr = len(s) // FRAME
    fr = s[: nfr * FRAME].reshape(nfr, FRAME)
    fr_rms = np.sqrt(np.mean(fr**2, axis=1))
    fr_sorted = np.sort(fr_rms)
    noise = np.mean(fr_sorted[: max(1, nfr // 10)])
    speech_p95 = np.percentile(fr_rms, 95)
    active = fr_rms > max(noise * 3.0, 1.0)
    speech_rms = float(np.sqrt(np.mean(fr_rms[active] ** 2))) if active.any() else 0.0

    row.update(
        peak_dbfs=round(dbfs(np.max(np.abs(s))), 1),
        speech_p95_dbfs=round(dbfs(speech_p95), 1),
        speech_rms_dbfs=round(dbfs(speech_rms), 1) if speech_rms else None,
        noise_floor_dbfs=round(dbfs(noise), 1),
        snr_db=round(dbfs(speech_p95) - dbfs(noise), 1),
        active_frac=round(float(np.mean(active)), 2),
        clip_samples=n_clip,
        clip_run_max=int(longest_run),
        dc_offset=round(float(np.mean(s)), 1),
    )
    return row


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    as_md = "--md" in sys.argv
    d = args[0] if args else "/opt/wyoming-onnx-asr/debug-audio"
    rows = [analyze_file(p) for p in sorted(glob.glob(os.path.join(d, "*.wav")))]
    if as_md:
        cols = [
            "file", "dur_s", "peak_dbfs", "speech_rms_dbfs", "noise_floor_dbfs",
            "snr_db", "clip_samples", "clip_run_max", "transcript",
        ]
        print("| " + " | ".join(cols) + " |")
        print("|" + "---|" * len(cols))
        for r in rows:
            vals = []
            for c in cols:
                v = r.get(c)
                if c == "transcript":
                    v = "(empty)" if v == "" else (v or "-")
                    v = v[:48].replace("|", "\\|")
                vals.append(str(v) if v is not None else "-")
            print("| " + " | ".join(vals) + " |")
    else:
        print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
