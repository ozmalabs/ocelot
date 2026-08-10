"""FIX THE EAR / SPEAKER NORM — does the agent's VTLN + predict-remove break the cross-speaker plateau on the trajectory read?

The trajectory read recovered +17 over pooled but plateaus ~20% @500-way cross-speaker; exemplar count plateaued, the
tell that SPEAKER VARIATION is the remaining bound. The agent's own forward speaker-norm (invariant_transform: VTLN
warp estimated from the utterance's own formants vs a cohort canonical -> CMVN -> coarticulation predict-remove) is the
fix. Compare the trajectory read (K=5 + delta) on:
  BASELINE (CMVN only, the current frames)  vs  +VTLN  vs  +VTLN+predict-remove (full invariant_transform).
Held-out cross-speaker, 400-way. Architecture-clean: the warp is the agent's own formant science, no sweep.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.fix_the_ear_speakernorm
"""
from __future__ import annotations

import glob
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.jabberwock_reads_oov_from_phones import frames, dtw, FS
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from domains.filter_settings import cochleagram
from domains.cmvn import apply_cmvn
from domains.invariant_units import invariant_transform, estimate_vtl_logalpha

N_BANK = 250
KMAX = 5
NWAY = 400
N_TEST = 250
PRUNE = 30


def _l2rows(M):
    M = np.asarray(M, np.float32)
    n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


def delta(F):
    F = np.asarray(F, np.float32)
    if len(F) < 2:
        return F
    d = np.diff(F, axis=0)
    return d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)


def feats(seg, canonical):
    """returns (A=CMVN baseline, B=+VTLN, C=+VTLN+predict-remove) L2-normed trajectories from ONE cochleagram."""
    seg = np.asarray(seg, dtype=np.float64)
    nf = max(4, len(frames(seg)[0]))
    M = np.asarray(cochleagram(seg, FS, n_frames=nf), dtype=np.float64)
    A = _l2rows(apply_cmvn(M))
    B = _l2rows(invariant_transform(M, canonical, do_vtln=True, do_cmvn=True, do_context=False))
    C = _l2rows(invariant_transform(M, canonical, do_vtln=True, do_cmvn=True, do_context=True))
    return A, B, C


def main():
    print("=" * 100)
    print("FIX THE EAR / SPEAKER NORM — trajectory read: CMVN baseline vs +VTLN vs +VTLN+predict-remove @400-way")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-3:], spks[:-3]

    # collect raw bank segments per word; compute the cohort canonical log-centroid
    segs = defaultdict(list); nb = 0; cents = []
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nb >= N_BANK:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nb += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if len(w) >= MINW and len(segs[w]) < KMAX:
                    s = x[int(t0 * fs):int(t1 * fs)]
                    if s.size >= int(0.05 * fs):
                        segs[w].append(s)
                        if len(cents) < 4000:
                            nf = max(4, len(frames(s)[0]))
                            cents.append(estimate_vtl_logalpha(np.asarray(cochleagram(s, FS, n_frames=nf)), 0.0))
        if nb >= N_BANK:
            break
    canonical = float(np.median(cents))
    vocab = [w for w, e in sorted(segs.items(), key=lambda kv: -len(kv[1]))[:NWAY]]
    vset = set(vocab)
    print(f"  bank {len(segs)} words ({nb} utts, {len(train_spk)} spk); {len(vocab)}-way; canonical log-centroid {canonical:.3f}\n", flush=True)

    # build bank trajectories (A/B/C) + pooled fingerprint (A) for the prefilter
    bankA, bankB, bankC = defaultdict(list), defaultdict(list), defaultdict(list)
    for w in vocab:
        for s in segs[w]:
            A, B, C = feats(s, canonical)
            bankA[w].append(A); bankB[w].append(B); bankC[w].append(C)
    pooled = {w: (np.stack([a.mean(0) for a in bankA[w]]).mean(0)) for w in vocab}
    PW = np.stack([pooled[w] / (np.linalg.norm(pooled[w]) + 1e-9) for w in vocab])

    test = []
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            if len(test) >= N_TEST:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in align_utt(x, fs, t):
                if w in vset and len(w) >= MINW:
                    s = x[int(t0 * fs):int(t1 * fs)]
                    if s.size >= int(0.05 * fs):
                        test.append((w, feats(s, canonical)))
        if len(test) >= N_TEST:
            break
    print(f"  {len(test)} held-out cross-speaker instances; scoring 3 norms (K={KMAX}+delta)...\n", flush=True)

    def score(bank, idx):
        ok = 0
        for (w, fset) in test:
            fr = fset[idx]; dl = delta(fr)
            pv = fr.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
            top = np.argsort(-(PW @ pv))[:PRUNE]
            best, arg = 1e18, None
            for i in top:
                c = vocab[i]
                d = min(dtw(fr, e) for e in bank[c]) + 0.3 * min(dtw(dl, delta(e)) for e in bank[c])
                if d < best:
                    best, arg = d, c
            ok += int(arg == w)
        return 100 * ok / len(test)

    a = score(bankA, 0); b = score(bankB, 1); c = score(bankC, 2)
    print("\n" + "=" * 100)
    print(f"  trajectory read (K={KMAX}+delta), {len(vocab)}-way cross-speaker:")
    print(f"    BASELINE (CMVN only):            {a:.1f}%")
    print(f"    + VTLN:                          {b:.1f}%  ({b-a:+.1f})")
    print(f"    + VTLN + predict-remove (full):  {c:.1f}%  ({c-a:+.1f})")
    best = max(b, c)
    if best >= a + 3:
        print(f"  SPEAKER NORM HELPS: {'+predict-remove' if c>=b else '+VTLN'} lifts the ear {a:.1f}->{best:.1f} (+{best-a:.1f}) by")
        print("  normalising cross-speaker vocal-tract variation -- the plateau the exemplar count couldn't break. The ear")
        print("  is the trajectory read on speaker-normalised features.")
    elif best >= a + 1:
        print(f"  SPEAKER NORM helps modestly (+{best-a:.1f}); cross-speaker variation is partly the bound but the ceiling is")
        print("  deeper (the training-free exemplar matcher itself). Honest.")
    else:
        print(f"  SPEAKER NORM does NOT help here ({a:.1f} vs {best:.1f}); the forward VTLN/predict-remove doesn't move the")
        print("  trajectory read -- the bound is the matcher, not residual speaker variation. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
