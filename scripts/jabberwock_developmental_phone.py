"""The jabberwock earns the phone model DEVELOPMENTALLY — clear-first curriculum, like a child.

Creator: "it earns it iteratively, not all at once, like a child. you do not start with full
co-articulated speech." A child gets SLOW, CLEAR, hyper-articulated input first (infant-
directed speech, isolated words) — phones long and well-separated, alignment easy — learns
THOSE, then bootstraps UP to fast/reduced/continuous. The thermodynamic frame inverted: start
where effort is HIGHEST (clearest), not at the reduced end. Iterative: the clear model aligns
the harder data, which trains a better model, which aligns harder data.

"Clear vs reduced" = frames-PER-PHONE (slow/hyper-articulated words have MANY frames/phone;
fast/reduced have few — the same effort axis as the efficiency finding).

TESTS:
  (1) per-frame phone acc on CLEAR (slow) words vs REDUCED (fast) vs ALL — is clear learnable?
  (2) CURRICULUM: train on CLEAR -> use it to force-align REDUCED -> retrain on clear +
      clear-aligned-reduced. vs FLAT-START on ALL (proportional). Does clear-first win?

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_developmental_phone.py [cap]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_earns_phone_model import ctxd, fit_model, phone_emission, viterbi_align
from scripts.jabberwock_earns_acoustic_phonetic import per_frame_acc


def fpp(fr, ph):
    return len(fr) / max(len(ph), 1)


def pairs_proportional(data, pred, cap):
    X, Y = [], []
    for w, fr, ph in data:
        if not pred(fpp(fr, ph)):
            continue
        cx = ctxd(fr); n = len(cx); P = len(ph)
        for i in range(n):
            X.append(cx[i]); Y.append(ph[int(i * P / n)])
        if len(X) >= cap:
            break
    return np.array(X), Y


def main():
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 45000
    train = _load_ph("train-clean-100_*.pkl", 12)
    dev = _load_ph("dev-clean_*.pkl", 12)
    phset = sorted({p for _w, _f, ph in train for p in ph}); pi = {p: i for i, p in enumerate(phset)}
    fvals = np.array([fpp(fr, ph) for _w, fr, ph in train])
    hi = np.percentile(fvals, 60); lo = np.percentile(fvals, 40)
    clear = lambda v: v >= hi          # slow / hyper-articulated
    reduced = lambda v: v <= lo        # fast / reduced
    allp = lambda v: True
    print("=" * 80)
    print(f"DEVELOPMENTAL PHONE MODEL — clear-first curriculum (clear>={hi:.1f} f/phone, reduced<={lo:.1f})")
    print("=" * 80)

    # (1) is CLEAR speech more learnable than REDUCED?
    t0 = time.time()
    for name, pred in (("CLEAR (slow)", clear), ("REDUCED (fast)", reduced), ("ALL", allp)):
        Xtr, Ytr = pairs_proportional(train, pred, cap)
        Xde, Yde = pairs_proportional(dev, pred, 15000)
        acc, ch = per_frame_acc(Xtr, Ytr, Xde, Yde)
        print(f"  [{name:14}] per-frame phone acc {acc:.3f}  (chance {ch:.3f})", flush=True)
    print("-" * 80, flush=True)

    # (2) CURRICULUM vs FLAT-START, both evaluated on ALL dev (proportional labels, same for both)
    Xde_all, Yde_all = pairs_proportional(dev, allp, 15000)

    # FLAT-START: train on ALL with proportional alignment
    Xfs, Yfs = pairs_proportional(train, allp, cap)
    fs_acc, ch = per_frame_acc(Xfs, Yfs, Xde_all, Yde_all)
    print(f"  FLAT-START on ALL (proportional)     : per-frame acc {fs_acc:.3f}", flush=True)

    # CURRICULUM: stage1 train on CLEAR; use it to FORCE-ALIGN reduced; retrain on clear+aligned-reduced
    Xc, Yc = pairs_proportional(train, clear, cap)
    enc, cent, cph = fit_model(Xc, Yc, phset, pi)
    nP = len(phset)
    Xr, Yr = [], []
    for w, fr, ph in train:
        if not reduced(fpp(fr, ph)):
            continue
        seq = [p for p in ph if p in pi]
        if len(seq) < 1 or len(fr) < len(seq):
            continue
        cx = ctxd(fr)
        labs = viterbi_align(phone_emission(cx, enc, cent, cph, nP), [pi[p] for p in seq])
        for i in range(len(cx)):
            Xr.append(cx[i]); Yr.append(phset[labs[i]])
        if len(Xr) >= cap:
            break
    Xcur = np.concatenate([Xc, np.array(Xr)]); Ycur = list(Yc) + Yr
    cur_acc, ch = per_frame_acc(Xcur, Ycur, Xde_all, Yde_all)
    print(f"  CURRICULUM (clear-first -> align reduced): per-frame acc {cur_acc:.3f}", flush=True)
    print("=" * 80)
    print(f"  flat-start {fs_acc:.3f} -> curriculum {cur_acc:.3f}  (delta {cur_acc-fs_acc:+.3f})  [{time.time()-t0:.0f}s]")
    print(f"  {'CLEAR-FIRST CURRICULUM WINS — earn it like a child, clear before co-articulated' if cur_acc > fs_acc + 0.01 else 'curriculum ~ flat-start here'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
