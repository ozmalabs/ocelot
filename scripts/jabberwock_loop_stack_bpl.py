"""STACK THE BPL PHONE-MARGINAL READ through the validated loop — does a 3rd, differently-built cue stack on static+delta?

The loop is now a validated tool (jabberwock_loop_valid_objective): give it a headroom cue + a valid objective and it
self-tunes a generalising fusion weight. The static+delta fusion reached 21.1% CV. Now STACK a genuinely DIFFERENT
reader: the BPL phone-marginal (forward over a phone library, marginalising the alignment -- a different model from
template-DTW). Frozen baseline = the static+delta read (NOT the old 17.1%); the loop tunes ONLY the marginal cue's
weight on top. KEEP iff it stacks a CV-stable lift over static+delta.

cue1 = z(static+delta fused)  ;  cue2 = z(phone-marginal forward)  ;  score(w) = cue1 + w*cue2 ; loop tunes w (hard
tuning-accuracy objective, the validated correctness-tracking one). CV 5-fold x 5 repeats, every clip held out once.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_loop_stack_bpl
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

N_WAY = 100
SAMPLE = 60000
TICKS = 24
CAP = 500
BETA = 4.0
NEG = 1e18


def delta(F):
    F = np.asarray(F, np.float32)
    if len(F) < 2:
        return F
    d = np.diff(F, axis=0)
    return d / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-9)


def _softmin2(a, b, beta):
    m = a if a < b else b
    if m > 1e17:
        return m
    return m - math.log(math.exp(-beta * (a - m)) + math.exp(-beta * (b - m))) / beta


def forward_pre(md, phs, T, beta):
    phs = [p for p in phs if p in md]
    L = len(phs)
    if L == 0 or T < L:
        return 1e9
    E = np.stack([md[p] for p in phs], axis=1)
    a = np.full((T, L), NEG); a[0, 0] = E[0, 0]
    for t in range(1, T):
        hi = min(t, L - 1)
        for l in range(hi + 1):
            stay = a[t - 1, l]; adv = a[t - 1, l - 1] if l > 0 else NEG
            if stay >= 1e17 and adv >= 1e17:
                continue
            a[t, l] = E[t, l] + _softmin2(stay, adv, beta)
    return a[T - 1, L - 1] / (T + L) if a[T - 1, L - 1] < 1e17 else 1e9


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
    print("STACK THE BPL PHONE-MARGINAL through the validated loop — does it stack on the static+delta 21% read?")
    print("=" * 100)
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
    print(f"  realigned units built ({len(units[0])} triphone medoids).", flush=True)

    # phone cloud for the BPL forward emission (1-NN over banked phone frames)
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
    print(f"  phone cloud: {len(cloud)} phones (cap {CAP}); BETA={BETA}", flush=True)

    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand = list(dict.fromkeys(list(targets) + distractors))
    cand = [w for w in cand if template(w, units) is not None][:N_WAY]
    tA = {w: np.asarray(template(w, units), np.float32) for w in cand}
    tB = {w: delta(tA[w]) for w in cand}
    cand_phs = {w: phones(w) for w in cand}
    needed = set(p for w in cand for p in cand_phs[w] if p in cloud)
    clips = [(w, np.asarray(cf, np.float32)) for (w, cf) in clips]
    print(f"  {len(cand)}-way; {len(clips)} clips; cues: static DTW, delta DTW, phone-marginal forward\n", flush=True)

    ZA, ZB, ZC, TRUE = [], [], [], []
    for k, (w, cf) in enumerate(clips):
        dca, dcb = cf, delta(cf)
        dA = np.array([dtw(dca, tA[c]) for c in cand])
        dB = np.array([dtw(dcb, tB[c]) for c in cand])
        md = {p: (1.0 - cf @ cloud[p].T).min(1) for p in needed}     # per-phone 1-NN dist, once per clip
        dC = np.array([forward_pre(md, cand_phs[c], len(cf), BETA) for c in cand])
        z = lambda d: (d - d.mean()) / (d.std() + 1e-9)
        ZA.append(z(dA)); ZB.append(z(dB)); ZC.append(z(dC))
        TRUE.append(cand.index(w) if w in cand else -1)
        if (k + 1) % 60 == 0:
            print(f"    scored {k+1}/{len(clips)} clips...", flush=True)
    ZA = np.array(ZA); ZB = np.array(ZB); ZC = np.array(ZC); TRUE = np.array(TRUE)
    keep = TRUE >= 0
    ZA, ZB, ZC, TRUE = ZA[keep], ZB[keep], ZC[keep], TRUE[keep]
    n = len(TRUE)

    # cue1 = static+delta validated fusion (re-z so the stack weight is meaningful); cue2 = phone-marginal
    SD = ZA + ZB
    ZSD = (SD - SD.mean(1, keepdims=True)) / (SD.std(1, keepdims=True) + 1e-9)

    def fused(w):
        return ZSD + w * ZC

    def hard_acc(idx, w):
        f = fused(w)[idx]
        return 100 * np.mean(f.argmin(1) == TRUE[idx])

    # cue sanity: each alone + the static+delta baseline
    sd_only = 100 * np.mean((ZSD).argmin(1) == TRUE)
    c_only = 100 * np.mean((ZC).argmin(1) == TRUE)
    print(f"\n  cue accuracies @ {N_WAY}-way over {n} clips: static+delta {sd_only:.1f}% | phone-marginal {c_only:.1f}%", flush=True)

    ws = np.round(np.arange(-1.0, 2.01, 0.25), 2)
    print(f"    {'w':>6}{'all-clip acc':>14}")
    for w in ws:
        print(f"    {w:>6.2f}{hard_acc(np.arange(n), w):>13.1f}%", flush=True)

    # CV: every clip held out once, loop-tunes the marginal weight on the rest (hard objective), no test access
    frozen_all = hard_acc(np.arange(n), 0.0)
    REPEATS = 5
    cv_accs, cv_ws = [], []
    for r in range(REPEATS):
        order = np.random.RandomState(200 + r).permutation(n)
        folds = np.array_split(order, 5)
        correct = 0
        for f in range(5):
            te = folds[f]; tu = np.concatenate([folds[k] for k in range(5) if k != f])
            w = run_loop(lambda w: hard_acc(tu, w) / 100.0)
            cv_ws.append(w)
            correct += int(np.sum(fused(w)[te].argmin(1) == TRUE[te]))
        cv_accs.append(100 * correct / n)
    cv_accs = np.array(cv_accs)
    lift = cv_accs.mean() - frozen_all
    se = cv_accs.std(ddof=1) / math.sqrt(REPEATS)

    print("\n" + "=" * 100)
    print(f"  static+delta (frozen w=0): {frozen_all:.1f}%  |  + BPL-marginal, loop-tuned (CV): {cv_accs.mean():.1f}% "
          f"(±{cv_accs.std(ddof=1):.1f}; mean w {np.mean(cv_ws):.2f})  |  lift {lift:+.1f}")
    print(f"    per-repeat: {[round(a,1) for a in cv_accs]}")
    stable = lift > 0 and (cv_accs > frozen_all).mean() >= 0.8
    if lift >= 1.0 and stable:
        print(f"  KEEP — the BPL phone-marginal STACKS on static+delta: {frozen_all:.1f}->{cv_accs.mean():.1f} (+{lift:.1f}), CV-stable")
        print(f"  ({(cv_accs>frozen_all).mean()*100:.0f}% of repeats beat frozen). A 3rd, differently-built reader adds via the")
        print("  validated loop — the combine-all pattern compounds. Speech: gooderer (stacked).")
    elif lift > 0 and stable:
        print(f"  WEAK-POSITIVE — small CV-stable stack (+{lift:.1f}); real-leaning but modest. Honest, don't over-claim.")
    else:
        print(f"  NO STACK — the BPL marginal does not add over static+delta (CV {cv_accs.mean():.1f} vs {frozen_all:.1f}, lift "
              f"{lift:+.1f}); it's redundant with / weaker than the template cues here. Honest; static+delta stands at 21.")
    print("=" * 100)


if __name__ == "__main__":
    main()
