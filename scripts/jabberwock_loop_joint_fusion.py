"""JOINT MULTI-CUE TUNING — the validated loop, scaled past one param via COORDINATE DESCENT over 3 cue weights.

Single-cue stacking gave static 17 -> +delta 21 -> +BPL 23 (each a 1-param loop). The natural close: JOINTLY tune all
cue weights so the loop captures the joint optimum the all-clip sweeps hinted at (~25). score = zA + wB*zB + wC*zC;
coordinate descent (tune wB holding wC via the graph-native hill-climb, then wC holding wB, iterate) -- each coordinate
is the SAME validated loop. CV 5-fold x5 (every clip held out once, joint-tuned on the rest, no test access). The
definitive loop-tuned multi-cue OOV read, and proof the loop scales past 1 param. Caches the cue precompute.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_loop_joint_fusion
"""
from __future__ import annotations

import glob
import math
import os
import pickle
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from substrate.world_adapter import WorldAdapter
from scripts.phonebank import CACHE, _meta
from scripts.jabberwock_reads_oov_from_phones import phones, dtw, STOP
from scripts.jabberwock_realign_emission import build_units, realign_split, uniform_split, template
from scripts.jabberwock_loop_tunes_fusion import manifest
from scripts.jabberwock_loop_stack_bpl import delta, forward_pre

N_WAY = 100
SAMPLE = 60000
TICKS = 20
CAP = 500
BETA = 4.0
CACHEZ = "/tmp/joint_cues.pkl"


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


def precompute():
    if os.path.exists(CACHEZ):
        print("  loading cached cues...", flush=True)
        return pickle.load(open(CACHEZ, "rb"))
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    sample = [words[i] for i in rng.permutation(len(words))[:SAMPLE]]
    vocabcount = Counter(w for (w, _f, _p) in words)
    del words
    uni = [(ph, uniform_split(np.asarray(fr, np.float32), ph)) for (_w, fr, ph) in sample]
    _, _, _, mono0 = build_units(uni)
    re_pw = []
    for (_w, fr, ph) in sample:
        fr = np.asarray(fr, np.float32)
        subs = realign_split(fr, ph, mono0)
        re_pw.append((ph, subs if subs is not None else uniform_split(fr, ph)))
    units = build_units(re_pw)
    store = defaultdict(list)
    for (ph, subs) in re_pw:
        for i, p in enumerate(ph):
            if i < len(subs) and subs[i] is not None and len(subs[i]) > 0:
                store[p].append(np.asarray(subs[i], np.float32))
    cloud = {}
    for p, exs in store.items():
        allf = np.concatenate(exs, 0)
        if len(allf) > CAP:
            allf = allf[np.random.RandomState(0).permutation(len(allf))[:CAP]]
        cloud[p] = allf
    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand = list(dict.fromkeys(list(targets) + distractors))
    cand = [w for w in cand if template(w, units) is not None][:N_WAY]
    tA = {w: np.asarray(template(w, units), np.float32) for w in cand}
    tB = {w: delta(tA[w]) for w in cand}
    cand_phs = {w: phones(w) for w in cand}
    needed = set(p for w in cand for p in cand_phs[w] if p in cloud)
    clips = [(w, np.asarray(cf, np.float32)) for (w, cf) in clips]
    print(f"  scoring {len(clips)} clips x {len(cand)} cand (static/delta/marginal)...", flush=True)
    ZA, ZB, ZC, TRUE = [], [], [], []
    for k, (w, cf) in enumerate(clips):
        dA = np.array([dtw(cf, tA[c]) for c in cand])
        dB = np.array([dtw(delta(cf), tB[c]) for c in cand])
        md = {p: (1.0 - cf @ cloud[p].T).min(1) for p in needed}
        dC = np.array([forward_pre(md, cand_phs[c], len(cf), BETA) for c in cand])
        z = lambda d: (d - d.mean()) / (d.std() + 1e-9)
        ZA.append(z(dA)); ZB.append(z(dB)); ZC.append(z(dC)); TRUE.append(cand.index(w) if w in cand else -1)
        if (k + 1) % 60 == 0:
            print(f"    {k+1}/{len(clips)}...", flush=True)
    out = (np.array(ZA), np.array(ZB), np.array(ZC), np.array(TRUE))
    pickle.dump(out, open(CACHEZ, "wb"))
    return out


def main():
    print("=" * 100)
    print("JOINT MULTI-CUE TUNING — the validated loop via coordinate descent over (static, delta, marginal) weights")
    print("=" * 100)
    ZA, ZB, ZC, TRUE = precompute()
    keep = TRUE >= 0
    ZA, ZB, ZC, TRUE = ZA[keep], ZB[keep], ZC[keep], TRUE[keep]
    n = len(TRUE)
    print(f"  {n} valid clips, {N_WAY}-way\n", flush=True)

    def acc(idx, wB, wC):
        f = ZA + wB * ZB + wC * ZC
        return 100 * np.mean(f[idx].argmin(1) == TRUE[idx])

    def coord_descent(tu, sweeps=3):
        wB, wC = 0.0, 0.0
        for _ in range(sweeps):
            wB = run_loop(lambda w: acc(tu, w, wC) / 100.0)
            wC = run_loop(lambda w: acc(tu, wB, w) / 100.0)
        return wB, wC

    allidx = np.arange(n)
    static_only = acc(allidx, 0.0, 0.0)
    # oracle joint peak (grid, all clips) for the ceiling
    grid = np.round(np.arange(0.0, 1.51, 0.25), 2)
    best = max(((b, c) for b in grid for c in grid), key=lambda bc: acc(allidx, bc[0], bc[1]))
    print(f"  static-only {static_only:.1f}%  |  all-clip joint-oracle peak (wB={best[0]},wC={best[1]}) {acc(allidx,*best):.1f}%\n", flush=True)

    # CV: joint coordinate-descent loop-tuning per fold; baselines (frozen, delta-only) on the same folds
    REPEATS = 5
    rows = {"frozen (static only)": [], "delta-only (loop)": [], "joint (loop)": []}
    ws = []
    for r in range(REPEATS):
        order = np.random.RandomState(300 + r).permutation(n)
        folds = np.array_split(order, 5)
        cor = {k: 0 for k in rows}
        for f in range(5):
            te = folds[f]; tu = np.concatenate([folds[k] for k in range(5) if k != f])
            wB_only = run_loop(lambda w: acc(tu, w, 0.0) / 100.0)
            wB, wC = coord_descent(tu)
            ws.append((wB, wC))
            cor["frozen (static only)"] += int(np.sum((ZA[te]).argmin(1) == TRUE[te]))
            cor["delta-only (loop)"] += int(np.sum((ZA + wB_only * ZB)[te].argmin(1) == TRUE[te]))
            cor["joint (loop)"] += int(np.sum((ZA + wB * ZB + wC * ZC)[te].argmin(1) == TRUE[te]))
        for k in rows:
            rows[k].append(100 * cor[k] / n)

    print(f"    {'read':>24}{'CV acc':>16}{'per-repeat':>28}")
    summ = {}
    for k in ["frozen (static only)", "delta-only (loop)", "joint (loop)"]:
        a = np.array(rows[k]); summ[k] = a.mean()
        print(f"    {k:>24}{a.mean():>9.1f}% (±{a.std(ddof=1):.1f}){str([round(x,1) for x in a]):>28}")
    fro = summ["frozen (static only)"]; dlt = summ["delta-only (loop)"]; jnt = summ["joint (loop)"]
    print(f"\n    mean joint weights: wB(delta) {np.mean([w[0] for w in ws]):.2f}  wC(marginal) {np.mean([w[1] for w in ws]):.2f}")
    print("\n" + "=" * 100)
    print(f"  CUMULATIVE loop-tuned OOV read (CV):  static {fro:.1f}  ->  +delta {dlt:.1f}  ->  +marginal(joint) {jnt:.1f}  "
          f"(+{jnt-fro:.1f} total)")
    if jnt >= dlt + 0.5:
        print(f"  JOINT tuning captures more: the validated loop scaled to {len(ws[0])} params via coordinate descent, lifting")
        print(f"  {fro:.1f}->{jnt:.1f} (+{jnt-fro:.1f}); each cue self-tuned from a valid objective, CV-generalising. The combine-all")
        print("  read, loop-tuned end-to-end.")
    else:
        print(f"  joint ~= delta-only ({jnt:.1f} vs {dlt:.1f}): the marginal adds little even jointly; static+delta is the read.")
        print(f"  The loop scales to multi-param cleanly (a real demonstration), but the headroom is in delta, not marginal.")
    print("=" * 100)


if __name__ == "__main__":
    main()
