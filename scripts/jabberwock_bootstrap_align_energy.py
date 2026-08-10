"""Earn the acoustic-phonetic decoder, part 2: BOOTSTRAP forced alignment so the ENERGY
channel can be tested on properly-aligned energy-bearing audio.

Part 1 (jabberwock_earns_acoustic_phonetic) was confounded: whole-utterance proportional
alignment -> chance for ALL variants. The fix is the standard ASR bootstrap: a weak phone
model (the phonebank's spectral one, ~0.13) VITERBI-FORCE-ALIGNS the fresh audio's KNOWN
phone sequence (the monotonic sequence constraint does most of the work, far better than
free per-frame decoding), giving good (frame, phone) labels on energy-bearing frames. Then
train spectral vs spectral+energy and read per-frame phone accuracy on force-aligned data.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_bootstrap_align_energy.py [n_tr] [n_de]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
import scripts.librispeech_wer as L
from scripts.jabberwock_reads_oov_from_phones import frames, phones as cmu_phones
from scripts.jabberwock_learned_encoder import _fit_pca, _fit_lda
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_earns_phone_model import ctxd, fit_model, phone_emission, viterbi_align
from scripts.jabberwock_earns_acoustic_phonetic import gather, utt_phones, context, per_frame_acc


def build_aligner():
    """the phonebank spectral phone model (~0.13) used only to force-align fresh audio."""
    train = _load_ph("train-clean-100_*.pkl", 12)
    phset = sorted({p for _w, _f, ph in train for p in ph}); pi = {p: i for i, p in enumerate(phset)}
    X, Y = [], []
    for w, fr, ph in train:
        cx = ctxd(fr); n = len(cx); P = len(ph)
        for i in range(n):
            X.append(cx[i]); Y.append(ph[int(i * P / n)])
        if len(X) >= 40000:
            break
    enc, cent, cph = fit_model(np.array(X), Y, phset, pi)
    return enc, cent, cph, phset, pi


def aligned_pairs(utts, enc, cent, cph, phset, pi, mode, cap=45000):
    """force-align each utt's known phone seq to its frames; emit (feature, phone) pairs.
    mode: spectral | energy."""
    nP = len(phset); X, Y = [], []
    for path, tr in utts:
        try:
            M, e = frames(L.load_flac(path)[0])
        except Exception:
            continue
        seq = [p for p in utt_phones(tr) if p in pi]
        if len(seq) < 2 or len(M) < len(seq):
            continue
        emis = phone_emission(ctxd(M), enc, cent, cph, nP)        # spectral emission for alignment
        labs = viterbi_align(emis, [pi[p] for p in seq])          # per-frame phone idx (forced)
        if mode == "energy":
            le = np.log(np.asarray(e, float) + 1e-6); le = (le - le.mean()) / (le.std() + 1e-6)
            B = np.concatenate([M, le[:, None]], axis=1)
        else:
            B = M
        F = context(B)
        for i in range(len(F)):
            X.append(F[i]); Y.append(phset[labs[i]])
        if len(X) >= cap:
            break
    return np.array(X), Y


def main():
    n_tr = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    n_de = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    print("=" * 80)
    print("EARN ACOUSTIC-PHONETIC DECODER pt2 — BOOTSTRAP forced alignment + ENERGY channel")
    print("=" * 80)
    t0 = time.time()
    enc, cent, cph, phset, pi = build_aligner()
    print(f"  aligner built (phonebank spectral model, {len(phset)} phones) [{time.time()-t0:.0f}s]", flush=True)
    tr = gather("train-clean-100", n_tr); de = gather("dev-clean", n_de)
    print(f"  train utts={len(tr)}  dev utts={len(de)} (force-aligned)", flush=True)
    for mode in ("spectral", "energy"):
        Xtr, Ytr = aligned_pairs(tr, enc, cent, cph, phset, pi, mode)
        Xde, Yde = aligned_pairs(de, enc, cent, cph, phset, pi, mode, cap=15000)
        acc, ch = per_frame_acc(Xtr, Ytr, Xde, Yde)
        print(f"  [{mode:9}] per-frame phone acc (force-aligned): {acc:.3f}  (chance {ch:.3f})  dim={Xtr.shape[1]}", flush=True)
    print("=" * 80)
    print(f"  [{time.time()-t0:.0f}s]  vs proportional-align chance 0.03 and phonebank per-word 0.13.")
    print("  energy>spectral => the discarded energy channel is the lever; else the floor is deeper")
    print("  (cochleagram representation / per-frame granularity / the weak bootstrap aligner).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
