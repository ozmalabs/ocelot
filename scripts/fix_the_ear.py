"""FIX THE EAR — realize the trajectory read at scale + push its precision (exemplar diversity, static+delta).

The wall is acoustic precision (the meaning prior confirmed it). The validated lever: a TRAJECTORY read (+17 over the
pooled fingerprint, 21.3 vs 3.9 @500-way). The likely next bound is CROSS-SPEAKER exemplar matching -- a held-out
speaker's word vs train-speaker exemplars. The harvest gives many exemplars from many speakers, so MORE exemplars
(K) should let the 1-NN find a voice-matched exemplar. Test:
  POOLED 1-NN (the complete-bank read)  vs  TRAJECTORY DTW (coarse-to-fine: pooled prune -> DTW), sweeping K
  exemplars/word, + static+delta. Held-out cross-speaker, 500-way (recall solved: every test word banked).
Does the trajectory read + exemplar diversity lift top-1 -- and where does the ear land?

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.fix_the_ear
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
from scripts.jabberwock_reads_oov_from_phones import frames, dtw
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW

N_BANK = 400        # more utts -> more exemplars/word (more speakers) -> the cross-speaker lever
KMAX = 8
NWAY = 500
N_TEST = 300
PRUNE = 30          # pooled-prefilter candidate words before DTW


def _l2(v):
    v = np.asarray(v, np.float32); n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def delta(F):
    F = np.asarray(F, np.float32)
    if len(F) < 2:
        return F
    d = np.diff(F, axis=0)
    return d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)


def main():
    print("=" * 100)
    print("FIX THE EAR — pooled vs trajectory DTW (coarse-to-fine), sweep K exemplars, + static+delta @500-way")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk); test_spk, train_spk = spks[-3:], spks[:-3]

    bank = defaultdict(list); nb = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nb >= N_BANK:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nb += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if len(w) >= MINW and len(bank[w]) < KMAX:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        bank[w].append(frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32))
        if nb >= N_BANK:
            break
    # vocab: words with the most exemplars (so a K sweep is meaningful), capped to NWAY
    vocab = [w for w, e in sorted(bank.items(), key=lambda kv: -len(kv[1]))[:NWAY]]
    vset = set(vocab)
    avgK = np.mean([min(len(bank[w]), KMAX) for w in vocab])
    pooled_word = {w: _l2(np.stack([e.mean(0) for e in bank[w]]).mean(0)) for w in vocab}
    PW = np.stack([pooled_word[w] for w in vocab])
    print(f"  bank {len(bank)} words ({nb} utts, {len(train_spk)} speakers); {len(vocab)}-way; avg {avgK:.1f} exemplars/word\n", flush=True)

    test = []
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            if len(test) >= N_TEST:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in align_utt(x, fs, t):
                if w in vset and len(w) >= MINW:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        test.append((w, frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32)))
        if len(test) >= N_TEST:
            break
    print(f"  {len(test)} held-out cross-speaker instances; scoring...\n", flush=True)

    # precompute, per test instance: pooled prune -> the PRUNE candidate words + their per-exemplar static/delta dists
    PRE = []
    for (w, fr) in test:
        pv = _l2(np.asarray(fr).mean(0))
        top = np.argsort(-(PW @ pv))[:PRUNE]
        cwords = [vocab[i] for i in top]
        dl = delta(fr)
        st = {c: [dtw(fr, e) for e in bank[c][:KMAX]] for c in cwords}
        de = {c: [dtw(dl, delta(e)) for e in bank[c][:KMAX]] for c in cwords}
        PRE.append((w, cwords, st, de, float(PW[top[0]] @ pv)))

    def acc_pooled():
        ok = 0
        for (w, cwords, _st, _de, _t) in PRE:
            # pooled = nearest word fingerprint (the prune's top-1)
            ok += int(cwords[0] == w)
        return 100 * ok / len(PRE)

    def acc_traj(kuse, wdelta=0.0):
        ok = 0
        for (w, cwords, st, de, _t) in PRE:
            best, arg = 1e18, None
            for c in cwords:
                d = min(st[c][:kuse])
                if wdelta:
                    d = d + wdelta * min(de[c][:kuse])
                if d < best:
                    best, arg = d, c
            ok += int(arg == w)
        return 100 * ok / len(PRE)

    pooled = acc_pooled()
    print(f"  POOLED 1-NN (complete-bank read):  {pooled:.1f}%\n")
    print(f"  TRAJECTORY DTW (coarse-to-fine), by #exemplars K:")
    print(f"    {'K':>4}{'static':>10}{'+delta(0.3)':>14}")
    best = (0, 0.0)
    for k in [1, 2, 3, 5, KMAX]:
        s = acc_traj(k); sd = acc_traj(k, 0.3)
        print(f"    {k:>4}{s:>9.1f}%{sd:>13.1f}%", flush=True)
        if sd > best[1]:
            best = (k, sd)

    print("\n" + "=" * 100)
    print(f"  EAR: pooled {pooled:.1f}% -> trajectory K={best[0]} +delta {best[1]:.1f}%  (+{best[1]-pooled:.1f} over pooled)")
    k1 = acc_traj(1); kbest_static = acc_traj(best[0])
    print(f"  exemplar-diversity lever: K=1 {k1:.1f}% -> K={best[0]} {kbest_static:.1f}% (+{kbest_static-k1:.1f}); delta adds "
          f"+{best[1]-kbest_static:.1f}")
    if best[1] >= pooled + 12:
        print(f"  FIXED (the big lever): the trajectory read realises the precision the pooled bank threw away (+{best[1]-pooled:.0f}).")
        if kbest_static - k1 >= 4:
            print(f"  Exemplar diversity is load-bearing (+{kbest_static-k1:.0f} from K) -- the harvest's many-speaker exemplars let the")
            print("  1-NN find a voice match. The ear is the trajectory read over a deep multi-speaker bank.")
        else:
            print(f"  More exemplars help modestly (+{kbest_static-k1:.0f}); the trajectory read itself is the lever. Next: speaker norm.")
    else:
        print(f"  trajectory read helps (+{best[1]-pooled:.0f}) but the ear is still low ({best[1]:.0f}% @500-way); deeper levers")
        print("  (speaker normalisation / richer features / better alignment) needed. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
