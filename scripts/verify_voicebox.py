"""verify_voicebox — does the physics-model voicebox produce INTELLIGIBLE,
VARIED-VOICE digit speech?  (verification only, no parent yet.)

The varied-voice physics parent rests on one claim: the agent's OWN source-filter /
Klatt-LF voicebox (synthesize_from_trajectory / synthesize_klatt_lf) can voice a digit
word at ARBITRARY f0 / vocal-tract-length / voice-quality and the result is still
RECOGNISABLE as that digit. If it cannot, the parent is built on sand. This script
verifies the claim BEFORE building the parent (the task's FIRST step):

  1. Build a per-digit A1-patch TRAJECTORY by ingesting FSDD TRAIN clips (each in a
     fresh substrate so the lexical matcher can't merge them) and averaging — the
     same word->sound forward-model trajectory analysis_by_synthesis uses.
  2. Bank a small set of FSDD TRAIN exemplars per digit (the recognizer's memory).
  3. Synthesize each digit at a SWEEP of voices (f0 x vtl x quality) from its
     trajectory (speak_trajectory -> the voicebox) and re-ingest into the agent's
     own front end.
  4. blind_guess the synthesized clip over the banked exemplars (full lexicon).

Intelligibility = the agent recognises its OWN varied-voice synthesis well above the
0.10 unigram floor. The voice sweep probes whether the voicebox spans the voice space
(different f0/vtl all still readable). Pure verification — the recognition is the
agent's blind_guess; we only drive the world I/O.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate
import domains.self_directed_speech_world as W
from domains.stt_pipeline import STTPipeline, STTParams


def extract_trajectory(x, fs):
    """One clip's A1-patch trajectory, ingested into a FRESH substrate (the matcher
    can't merge it). Returns the longest sign's flat trajectory or None."""
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    pipe.ingest(sub, x)
    sub.tick(50000)
    best = None
    for s in sub.nodes("AcousticSign"):
        t = sub.node(s)["attrs"].get("trajectory")
        if t and (best is None or len(t) > len(best)):
            best = t
    return np.array([float(v) for v in best], dtype=np.float32) if best else None


def mean_trajectory(clips, fs):
    """Mean A1 trajectory over several clips of one digit (time-resampled to the
    median length so the per-frame mean is aligned). The word->sound forward model."""
    trajs = [t for t in (extract_trajectory(x, fs) for x, _ in clips) if t is not None]
    if not trajs:
        return None
    # n_patches is fixed by the front end; spp = len/n_patches. Resample each to the
    # median spp so they align frame-for-frame, then average.
    n_patches = 25
    spps = [len(t) // n_patches for t in trajs if len(t) >= n_patches]
    if not spps:
        return None
    target_spp = int(np.median(spps))
    mats = []
    for t in trajs:
        spp = len(t) // n_patches
        if spp == 0:
            continue
        m = t[: spp * n_patches].reshape(spp, n_patches)
        # resample frames spp -> target_spp
        idx = np.linspace(0, spp - 1, target_spp)
        lo = np.floor(idx).astype(int); hi = np.minimum(lo + 1, spp - 1)
        frac = (idx - lo)[:, None]
        mr = m[lo] * (1 - frac) + m[hi] * frac
        mats.append(mr)
    if not mats:
        return None
    return np.mean(mats, axis=0).astype(np.float32).flatten()


def _resample_vtl(audio, vtl):
    audio = np.asarray(audio, dtype=np.float32)
    if vtl == 1.0 or audio.size == 0:
        return audio
    n = max(1, int(round(audio.size / vtl)))
    idx = np.clip((np.arange(n) * vtl).astype(int), 0, audio.size - 1)
    return np.ascontiguousarray(audio[idx])


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-traj", type=int, default=8,
                    help="FSDD train clips averaged into each digit's trajectory")
    ap.add_argument("--n-bank", type=int, default=12,
                    help="FSDD train exemplars banked per digit (recognizer memory)")
    args = ap.parse_args()

    digits = W._DIGIT_WORDS["en"]
    fs = W._TARGET_FS

    # MAIN substrate: holds the bank + front end + A1 patches the voicebox reads.
    s = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=fs))
    pipe.attach(s)
    pipe._ensure_audio_pipeline(s)
    W.install_speech_world_rules(s)

    all_spk = W.fsdd_speakers()
    held_spk = all_spk[-1]
    train_spk = [sp for sp in all_spk if sp != held_spk]
    train_idx = W.fsdd_index_for(train_spk)
    cell_key = "digit|fsdd|en"

    print(f"[traj] building per-digit mean trajectories from {args.n_traj} train clips "
          f"(speakers {train_spk})", flush=True)
    digit_traj = {}
    for w in digits:
        paths = train_idx.get(w, [])[: args.n_traj]
        clips = [W.load_fsdd_clip(p) for p in paths]
        digit_traj[w] = mean_trajectory(clips, fs)
    n_ok = sum(t is not None and t.size > 1 for t in digit_traj.values())
    print(f"[traj] digits with a trajectory: {n_ok}/{len(digits)}", flush=True)
    if n_ok == 0:
        print("[STOP] no digit produced a trajectory — fix trajectory extraction, "
              "not the parent.", flush=True)
        return

    print(f"[bank] banking {args.n_bank} FSDD train exemplars/digit", flush=True)
    for w in digits:
        for p in train_idx.get(w, [])[args.n_traj: args.n_traj + args.n_bank]:
            x, _ = W.load_fsdd_clip(p)
            W.bank_exemplar(s, w, cell_key, x, fs)

    f0s = [95.0, 130.0, 190.0, 230.0]
    vtls = [0.85, 1.0, 1.15]
    qs = [3.0, 5.0]
    nvox = len(f0s) * len(vtls) * len(qs)
    print(f"\n[sweep] synthesizing each digit across {nvox} voices "
          f"(f0 x vtl x q); re-ingest + blind_guess (full lexicon)", flush=True)

    total = correct = 0
    per_digit = {w: [0, 0] for w in digits}
    per_f0 = {f: [0, 0] for f in f0s}
    per_vtl = {v: [0, 0] for v in vtls}
    for w in digits:
        t = digit_traj[w]
        if t is None or t.size <= 1:
            continue
        for f0 in f0s:
            for vtl in vtls:
                for q in qs:
                    audio = pipe.speak_trajectory(s, t, f0_hz=f0, q_factor=q)
                    audio = _resample_vtl(audio, vtl)
                    if np.asarray(audio).size <= 1 or not np.any(np.abs(audio) > 1e-5):
                        continue
                    ch = W.feature_channels(s, audio, fs)
                    guess = W.blind_guess(s, ch, cell_key, restrict_to=None)
                    ok = (guess == w)
                    total += 1; correct += int(ok)
                    per_digit[w][0] += int(ok); per_digit[w][1] += 1
                    per_f0[f0][0] += int(ok); per_f0[f0][1] += 1
                    per_vtl[vtl][0] += int(ok); per_vtl[vtl][1] += 1

    acc = correct / max(total, 1)
    print("\n========== VOICEBOX INTELLIGIBILITY ==========", flush=True)
    print(f"  self-recognition of varied-voice synthesis: {correct}/{total} = "
          f"{acc:.3f}  (unigram floor 0.100)", flush=True)
    print("  per-digit:", {w: f"{c}/{n}" for w, (c, n) in per_digit.items()}, flush=True)
    print("  per-f0:", {f"{f:.0f}": round(c / max(n, 1), 2) for f, (c, n) in per_f0.items()}, flush=True)
    print("  per-vtl:", {f"{v:.2f}": round(c / max(n, 1), 2) for v, (c, n) in per_vtl.items()}, flush=True)
    verdict = ("INTELLIGIBLE — voicebox voices recognisable varied-voice digits; the "
               "varied-voice parent is sound."
               if acc >= 0.30 else
               "WEAK — varied-voice synthesis barely above floor; fix the voicebox first.")
    print(f"\n  VERDICT: {verdict}", flush=True)
    print("[MARKER] VERIFY_VOICEBOX_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
