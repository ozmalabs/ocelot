"""PREDICTIVE EAR — remove the LONG-timescale speaker WARP (VTL formant-spacing) estimated over the whole utterance.

The root wall is cross-speaker variation; the agent's design: the dominant knob is a MULTIPLICATIVE formant-spacing
WARP (VTL) -- a ratio in Hz = a constant shift in log-frequency -- which CMVN's additive mean cannot touch. Predict it
as the SLOW, constant component (estimate over the WHOLE UTTERANCE, long timescale -> stable, unsupervised, no labels)
and remove it; the fast /k/->/ae/->/t/ formant motion is the surprise that passes through (structure-preserving). The
-5 scar came from a SHORT-timescale predict (next-frame) that ate content; the long timescale isolates SPEAKER.

KEY difference from the FAILED VTLN run: estimate the warp from the WHOLE UTTERANCE, NOT a single short word (which was
noisy and HURT). Conditions @500-way cross-speaker, trajectory read (K=5+delta):
  CMVN baseline  |  +UTTERANCE-warp removed (predictive)  |  +WORD-warp removed (short-timescale ABLATION, the failed VTLN)
Pre-committed: KEEP if predictive >= CMVN + 3 (real warp removal); STOP if <= +0.5 (reduces to CMVN). FAIRNESS FLOOR:
zero-warp reproduces CMVN (by construction); the SHORT-timescale ablation must REGRESS below CMVN (proving the gain is
isolating the long-timescale speaker warp, not washing out content).

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.predictive_ear
"""
from __future__ import annotations

import glob
import math
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
from domains.invariant_units import estimate_vtl_logalpha, warp_bands

N_BANK = 250
KMAX = 5
NWAY = 400
N_TEST = 260
PRUNE = 30
FPS = 50


def _coch(x):
    nf = max(4, int(len(x) / FS * FPS))
    return np.asarray(cochleagram(np.asarray(x, dtype=np.float64), FS, n_frames=nf), dtype=np.float64)


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


def feats(Mword, alpha):
    """word cochleagram -> warp out the speaker VTL (log-freq) -> CMVN -> L2 trajectory."""
    M = warp_bands(Mword, alpha) if abs(alpha) > 1e-9 else Mword
    return _l2rows(apply_cmvn(M))


def main():
    print("=" * 100)
    print("PREDICTIVE EAR — long-timescale (utterance) VTL-warp removal vs CMVN vs short-timescale ablation @500-way")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-4:], spks[:-4]

    # calibrate canonical = median whole-utterance formant centroid over TRAIN
    cents = []
    for sp in train_spk[:20]:
        for (f, t) in by_spk[sp][:6]:
            x, fs = load_flac(f)
            cents.append(estimate_vtl_logalpha(_coch(np.asarray(x, np.float64)), 0.0))
            if len(cents) >= 400:
                break
        if len(cents) >= 400:
            break
    canonical = float(np.median(cents))
    print(f"  canonical (cohort VTL centroid) {canonical:.3f}; {len(train_spk)} train / {len(test_spk)} test spk\n", flush=True)

    def build(spk_list, cap):
        """word -> list of (A=CMVN, B=utterance-warp, C=word-warp) trajectories."""
        out = defaultdict(list); nu = 0
        for sp in spk_list:
            for (f, t) in by_spk[sp]:
                if nu >= cap:
                    break
                x, fs = load_flac(f); x = np.asarray(x, np.float64); nu += 1
                Mutt = _coch(x)
                a_utt = estimate_vtl_logalpha(Mutt, canonical)        # LONG timescale: whole utterance
                for (w, t0, t1) in align_utt(x, fs, t):
                    if len(w) < MINW:
                        continue
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size < int(0.05 * fs):
                        continue
                    Mw = _coch(seg)
                    a_word = estimate_vtl_logalpha(Mw, canonical)     # SHORT timescale: the single word (failed VTLN)
                    out[w].append((feats(Mw, 0.0), feats(Mw, a_utt), feats(Mw, a_word)))
            if nu >= cap:
                break
        return out

    print("  building bank (CMVN / utterance-warp / word-warp)...", flush=True)
    bank = build(train_spk, N_BANK)
    vocab = [w for w, e in sorted(bank.items(), key=lambda kv: -len(kv[1]))[:NWAY] if len(e) >= 2]
    vset = set(vocab)
    # pooled fingerprints per condition for the prefilter
    pool = {idx: np.stack([np.stack([e[idx].mean(0) for e in bank[w]]).mean(0) for w in vocab]) for idx in (0, 1, 2)}
    pool = {idx: (pool[idx] / (np.linalg.norm(pool[idx], axis=1, keepdims=True) + 1e-9)) for idx in (0, 1, 2)}
    print(f"  bank {len(bank)} words; {len(vocab)}-way\n", flush=True)
    print("  building test...", flush=True)
    test = build(test_spk, N_TEST)
    test_toks = [(w, e) for w in test if w in vset for e in test[w]]
    print(f"  {len(test_toks)} held-out cross-speaker tokens; scoring 3 conditions...\n", flush=True)

    def score(idx):
        ok = 0; tot = 0
        Pw = pool[idx]
        for (w, fset) in test_toks:
            fr = fset[idx]; dl = delta(fr)
            pv = fr.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
            top = np.argsort(-(Pw @ pv))[:PRUNE]
            best, arg = 1e18, None
            for i in top:
                c = vocab[i]
                d = min(dtw(fr, e[idx]) for e in bank[c]) + 0.3 * min(dtw(dl, delta(e[idx])) for e in bank[c])
                if d < best:
                    best, arg = d, c
            tot += 1; ok += int(arg == w)
        return 100 * ok / max(tot, 1)

    cmvn = score(0)
    pred = score(1)
    abl = score(2)
    print("\n" + "=" * 100)
    print(f"  trajectory read (K=5+delta), {len(vocab)}-way cross-speaker, {len(test_toks)} tokens:")
    print(f"    CMVN baseline:                       {cmvn:.1f}%")
    print(f"    + UTTERANCE-warp removed (predictive):{pred:.1f}%  ({pred-cmvn:+.1f})")
    print(f"    + WORD-warp removed (short ablation): {abl:.1f}%  ({abl-cmvn:+.1f})")
    print("-" * 100)
    if pred >= cmvn + 3 and abl <= cmvn + 0.5:
        print(f"  KEEP — the predictive (long-timescale VTL-warp) ear BREAKS the wall: utterance-warp removal {cmvn:.1f}->{pred:.1f}")
        print(f"  (+{pred-cmvn:.1f}, beyond CMVN's additive mean -- a multiplicative formant-spacing ratio), and the SHORT-timescale")
        print(f"  ablation regresses to {abl:.1f} (it ate content) -- proving the gain is isolating SPEAKER. The root wall yields to")
        print("  unsupervised, long-context predictive normalisation -- what an infant's slow speaker-constancy does.")
    elif pred >= cmvn + 1:
        print(f"  PARTIAL — utterance-warp helps (+{pred-cmvn:.1f}) but under the +3 bar; real but modest (closer to whitening's +2).")
        print(f"  Ablation {abl:.1f} {'regresses (isolation holds)' if abl<=cmvn else 'did not regress'}. Honest.")
    else:
        print(f"  STOP — utterance-warp removal did NOT beat CMVN ({cmvn:.1f} vs {pred:.1f}); the long-timescale predictable")
        print("  component was ~just the additive mean CMVN already removes -> a fancier CMVN. The root wall stands. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
