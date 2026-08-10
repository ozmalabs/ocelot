"""invariant_end_to_end_accept — THE MOMENT OF TRUTH for the speech arc.

Does cleaner PERCEPTION (units LOSO 0.32->0.60, chunk purity ->0.84 in the side
experiments) translate to better actual WORD RECOGNITION, or is the remaining
loss in the recognition stage?

APPLES-TO-APPLES. The SAME recognizer on:
  * RAW units      — the gammatone trajectory the bench already uses.
  * INVARIANT units — the SAME trajectory put through the agent's now-default
                      invariance chain: CMVN -> predict-remove (k=0.5),
                      REPLACING the linear flat-mean context-norm. Applied over
                      the frames x patches trajectory matrix (CMVN + predict-remove
                      are feature-axis-agnostic — per-feature over the temporal
                      frame axis; the only band-axis-specific step, the VTLN warp,
                      is skipped because the recognizer's feature is A1 patches,
                      not gammatone bands).

Two established harnesses, two recognizers, FSDD held-out speaker (jackson),
10-way, chance 10%:
  (1) both-ears kNN          — baseline 61% on RAW units (full_perception_bench)
  (2) 2-stage recognition arch — baseline 55.8% (recognition_arch_accept)

This script runs recognizer (1) directly (cheap, self-contained). It caches each
clip's per-sign trajectory ONCE, then evaluates BOTH feature variants so the only
thing that changes between rows is the feature transform. No tuning.

Run: python -m scripts.invariant_end_to_end_accept
"""
import os
import sys
import random
from collections import Counter

sys.path.insert(0, os.getcwd())
random.seed(1)

import numpy as np

from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import _root
from domains.invariant_units import cmvn, predict_remove

TRAJ_SAMPLES = 32          # lexical_access default frames/sign (frames x patches)


def _nrm(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def invariant_traj(traj_flat):
    """Apply the agent's DEFAULT invariance chain (CMVN -> predict-remove k=0.5,
    REPLACE form) to ONE sign's flat frames x patches trajectory; return the
    re-flattened transformed trajectory (same length). VTLN is skipped (the
    feature axis is A1 patches, not gammatone bands; the warp is band-specific).
    CMVN + predict-remove are per-feature over the frame axis, so they apply to
    the patch axis unchanged — exactly the link-1 + link-2 the agent made default.
    """
    v = np.asarray(traj_flat, dtype=np.float64)
    if v.size % TRAJ_SAMPLES != 0:
        return v.astype(np.float32)          # can't reshape; leave raw
    n_patch = v.size // TRAJ_SAMPLES
    M = v.reshape(TRAJ_SAMPLES, n_patch)       # frames x patches
    M = cmvn(M, do_variance=True)              # link-1 speaker norm
    M = predict_remove(M, window=2, k=0.5)     # link-2 coarticulation (REPLACE)
    return M.reshape(-1).astype(np.float32)


def build():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    sub.set_attr(_root(sub), "resolution", 12)
    return sub, pipe


def feats(sub, pipe, path):
    """Return (raw_gam_centroid, raw_fft_centroid, inv_gam_centroid) for a clip.
    The fft path is untouched (the second ear); only the gammatone trajectory gets
    the invariance chain, since that is the per-sign band/patch trajectory."""
    s, fs = fl.load_wav(path)
    pipe.ingest(sub, s)
    sub.tick(50000)
    st = None
    for n in sub.nodes("AudioStream"):
        st = n
    sg = fl._collect_signs_from_stream(sub, st) if st else []
    g_raw, g_inv, f = [], [], []
    for sid in sg:
        a = sub.node(sid)["attrs"]
        t = a.get("trajectory")
        ft = a.get("fft_trajectory")
        if t:
            tv = np.array(t, dtype=float)
            g_raw.append(tv)
            g_inv.append(invariant_traj(tv))
        if ft:
            f.append(np.array(ft, dtype=float))
    if not g_raw:
        return None
    gr = _nrm(np.mean(g_raw, 0))
    gi = _nrm(np.mean(g_inv, 0))
    fv = _nrm(np.mean(f, 0)) if f else np.zeros(1024)
    return gr, fv, gi


def knn(tr, q_g, q_f, use_fft, k=5):
    sims = []
    for d, g, f in tr:
        sc = float(np.dot(q_g, g))
        if use_fft:
            sc += float(np.dot(q_f, f))
        sims.append((sc, d))
    sims.sort(reverse=True)
    return Counter(d for _, d in sims[:k]).most_common(1)[0][0]


def main():
    sub, pipe = build()
    af = fl.gather_files(limit=None)
    # cache: (digit, raw_gam, fft, inv_gam), split by speaker
    tr_raw, tr_inv, te_raw, te_inv = [], [], [], []
    for path, digit, sp, idx in af:
        r = feats(sub, pipe, path)
        if r is None:
            continue
        gr, fv, gi = r
        if sp == "jackson":
            te_raw.append((digit, gr, fv))
            te_inv.append((digit, gi, fv))
        else:
            tr_raw.append((digit, gr, fv))
            tr_inv.append((digit, gi, fv))

    print(f"FSDD held-out speaker = jackson, 10-way, chance 10%  "
          f"(train {len(tr_raw)}, test {len(te_raw)})")
    print("\nrecognizer (1): both-ears kNN (k=5)\n")
    print(f"  {'features':28s}{'gammatone ear':>16s}{'BOTH ears':>14s}")
    print(f"  {'-'*28}{'-'*16}{'-'*14}")
    results = {}
    for fname, tr, te in [("RAW units", tr_raw, te_raw),
                          ("INVARIANT units (CMVN+PR)", tr_inv, te_inv)]:
        row = {}
        for use_fft, key in [(False, "gam"), (True, "both")]:
            ok = sum(knn(tr, g, f, use_fft) == d for d, g, f in te)
            row[key] = 100.0 * ok / max(1, len(te))
        results[fname] = row
        print(f"  {fname:28s}{row['gam']:>14.1f}% {row['both']:>12.1f}%")

    print(f"\n  {'baselines':28s}{'':>16s}{'61.0% (RAW both-ears)':>14s}")
    raw_b = results["RAW units"]["both"]
    inv_b = results["INVARIANT units (CMVN+PR)"]["both"]
    raw_g = results["RAW units"]["gam"]
    inv_g = results["INVARIANT units (CMVN+PR)"]["gam"]
    print(f"\n  VERDICT (both ears):  raw {raw_b:.1f}% -> invariant {inv_b:.1f}%  "
          f"(Δ {inv_b-raw_b:+.1f} pts)")
    print(f"  VERDICT (gam ear):    raw {raw_g:.1f}% -> invariant {inv_g:.1f}%  "
          f"(Δ {inv_g-raw_g:+.1f} pts)")
    if inv_b > raw_b:
        print("  => cleaner perception MOVES recognition (both ears).")
    elif inv_b == raw_b:
        print("  => recognition FLAT despite cleaner units (both ears) — the "
              "remaining loss is in the recognition stage, not perception.")
    else:
        print("  => invariant units HURT recognition (both ears).")


if __name__ == "__main__":
    main()
