"""STATIC+DELTA EAR ON A HIGH-RECALL BANK — does the validated precision lever hold at complete-bank scale?

The complete extracted bank stores POOLED whole-word fingerprint vectors (3 channels, temporal structure pooled away)
for fast 1-NN -> broad recall but COARSE precision, and it CAN'T use delta (no per-frame structure). The validated
static+delta lever (+4-6 CV) lives on FRAME TRAJECTORIES. So test the precision lever properly on a high-recall bank:
build a TRAJECTORY whole-word bank (every test word banked = recall solved), and compare reads at LARGER vocab:
  POOLED 1-NN (the complete-bank read)  vs  STATIC-trajectory DTW  vs  STATIC+DELTA-trajectory DTW (loop-tuned, CV).
Does the temporal/delta read convert the solved recall into top-1 precision -- and does delta still add at this scale?

Pre-committed bar: static+delta >= static-only + 2 (CV) AND both beat pooled 1-NN (trajectory read is the precision
lever the pooled bank lacks). Fairness: every test word IS banked (recall solved), so this measures PRECISION.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_static_delta_complete
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
from substrate.world_adapter import WorldAdapter
from scripts.jabberwock_reads_oov_from_phones import frames, dtw, STOP
from scripts.phonebank import align_utt
from scripts.librispeech_wer import load_flac
from scripts.jabberwock_harvest_exemplars import transcripts, DEV, MINW
from scripts.jabberwock_loop_tunes_fusion import manifest

N_BANK = 150
K = 3
NWAY = 500
N_TEST = 60
TICKS = 22


def delta(F):
    F = np.asarray(F, np.float32)
    if len(F) < 2:
        return F
    d = np.diff(F, axis=0)
    return d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)


def run_loop(obj):
    ad = WorldAdapter()
    ad.inner.load_seed_manifest(manifest(theta0=0.0, step0=0.5), ad.agent)
    o = next(nn for nn in ad.s.nodes("TunedOp"))
    w = 0.0
    for _t in range(TICKS):
        a = ad.s.node(o)["attrs"]
        ad.s.set_attr(o, "skill", obj(a["theta"]))
        ad.master_tick(); ad.tick()
        b = ad.s.node(o)["attrs"]
        ad.s.set_attr(o, "theta", b["next_theta"]); ad.s.set_attr(o, "last_skill", obj(a["theta"]))
        ad.s.set_attr(o, "dir", b["next_dir"]); ad.s.set_attr(o, "step", b["next_step"])
        w = b["next_theta"]
    return w


def main():
    print("=" * 100)
    print("STATIC+DELTA EAR ON A HIGH-RECALL BANK — pooled 1-NN vs static DTW vs static+delta DTW, larger vocab")
    print("=" * 100)
    tr = transcripts(DEV)
    flacs = sorted(glob.glob(os.path.join(DEV, "**", "*.flac"), recursive=True))
    by_spk = defaultdict(list)
    for f in flacs:
        b = os.path.basename(f)[:-5]
        if b in tr:
            by_spk[os.path.basename(f).split("-")[0]].append((f, tr[b]))
    spks = sorted(by_spk)
    test_spk, train_spk = spks[-3:], spks[:-3]

    # TRAJECTORY bank (oracle labels -> correct, recall is the point): word -> list of frame trajectories
    bank = defaultdict(list)
    nb = 0
    for sp in train_spk:
        for (f, t) in by_spk[sp]:
            if nb >= N_BANK:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64); nb += 1
            for (w, t0, t1) in align_utt(x, fs, t):
                if len(w) >= MINW and len(bank[w]) < K:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        bank[w].append(frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32))
        if nb >= N_BANK:
            break
    # candidate vocab: most-banked words (cap NWAY)
    vocab = [w for w, _ in sorted(bank.items(), key=lambda kv: -len(kv[1]))[:NWAY]]
    vset = set(vocab)
    st_bank = {w: bank[w] for w in vocab}
    dl_bank = {w: [delta(e) for e in bank[w]] for w in vocab}
    pooled_bank = {w: [np.asarray(e).mean(0) for e in bank[w]] for w in vocab}
    print(f"  trajectory bank: {len(bank)} words ({nb} utts), candidate vocab {len(vocab)} (high-recall: test words banked)\n", flush=True)

    # TEST: held-out test-speaker instances of BANKED words (so recall is solved -> precision test)
    test = []
    for sp in test_spk:
        for (f, t) in by_spk[sp]:
            if len([1 for (w, _s) in test]) >= N_TEST * 8:
                break
            x, fs = load_flac(f); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in align_utt(x, fs, t):
                if w in vset and len(w) >= MINW:
                    seg = x[int(t0 * fs):int(t1 * fs)]
                    if seg.size >= int(0.05 * fs):
                        test.append((w, frames(np.asarray(seg, dtype=np.float64))[0].astype(np.float32)))
    print(f"  {len(test)} held-out test instances (all banked); scoring 3 reads...\n", flush=True)

    # precompute per-instance candidate distances: pooled (cosine), static DTW, delta DTW
    POOL, STAT, DELT, TRUE = [], [], [], []
    for k, (w, fr) in enumerate(test):
        pv = np.asarray(fr).mean(0)
        dl = delta(fr)
        pool = np.array([min(1.0 - pv @ (e / (np.linalg.norm(e) + 1e-9)) for e in pooled_bank[c]) for c in vocab])
        stat = np.array([min(dtw(fr, e) for e in st_bank[c]) for c in vocab])
        delt = np.array([min(dtw(dl, e) for e in dl_bank[c]) for c in vocab])
        z = lambda d: (d - d.mean()) / (d.std() + 1e-9)
        POOL.append(z(pool)); STAT.append(z(stat)); DELT.append(z(delt)); TRUE.append(vocab.index(w))
        if (k + 1) % 50 == 0:
            print(f"    scored {k+1}/{len(test)}...", flush=True)
    POOL = np.array(POOL); STAT = np.array(STAT); DELT = np.array(DELT); TRUE = np.array(TRUE)
    n = len(TRUE)

    def acc(score, idx):
        return 100 * np.mean(score[idx].argmin(1) == TRUE[idx])

    def fused_acc(w, idx):
        return 100 * np.mean((STAT + w * DELT)[idx].argmin(1) == TRUE[idx])

    allidx = np.arange(n)
    pooled = acc(POOL, allidx); static = acc(STAT, allidx)
    # CV loop-tune the delta weight (no test access), content+function combined (these are mostly content words)
    REP = 5
    cv = []; ws = []
    for r in range(REP):
        order = np.random.RandomState(700 + r).permutation(n)
        folds = np.array_split(order, 5)
        ok = 0
        for fdx in range(5):
            te = folds[fdx]; tu = np.concatenate([folds[k] for k in range(5) if k != fdx])
            w = run_loop(lambda W: fused_acc(max(0.0, W), tu) / 100.0)
            ws.append(w)
            ok += int(np.sum((STAT + max(0.0, w) * DELT)[te].argmin(1) == TRUE[te]))
        cv.append(100 * ok / n)
    sd_cv = float(np.mean(cv))

    print("\n" + "=" * 100)
    print(f"  {len(vocab)}-way, {n} held-out instances (all banked = recall solved):")
    print(f"    POOLED 1-NN (complete-bank read):  {pooled:.1f}%")
    print(f"    STATIC trajectory DTW:             {static:.1f}%")
    print(f"    STATIC+DELTA (loop-tuned, CV):     {sd_cv:.1f}%   (mean w {np.mean(ws):.2f}; per-repeat {[round(x,1) for x in cv]})")
    sd_lift = sd_cv - static
    if static >= pooled + 3 and sd_lift >= 2.0:
        print(f"  KEEP — the precision lever HOLDS at scale: the trajectory read beats pooled 1-NN ({pooled:.1f}->{static:.1f}),")
        print(f"  and DELTA adds on top (+{sd_lift:.1f} CV) -> {sd_cv:.1f}. Recall solved by the harvest; static+delta converts it")
        print("  to top-1 precision. The pooled complete bank should carry trajectories (or this read) for the precision win.")
    elif static >= pooled + 3:
        print(f"  PARTIAL — trajectory DTW beats pooled ({pooled:.1f}->{static:.1f}) but delta adds only +{sd_lift:.1f} (<2) at this")
        print("  larger vocab. The temporal read is the lever; delta's marginal gain shrinks at scale. Honest.")
    else:
        print(f"  NEGATIVE — trajectory DTW did not clearly beat pooled ({pooled:.1f} vs {static:.1f}); precision is bounded by")
        print(f"  something other than the read here (static+delta CV {sd_cv:.1f}). Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
