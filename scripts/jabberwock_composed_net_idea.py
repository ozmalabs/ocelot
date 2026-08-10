"""Test the jabberwock's COMPOSE-NOT-TRAIN idea — its own answer to the training-cost problem.

Among its surfaced ideas, the distinctive one is composed_net: lift each band b -> [b, b^2, b^3]
(Taylor local approximation = a richer nonlinear feature) + b_t - b_hat(b_{t-1}) (an explicit
predictive-residual = its analytic forward-model analog of the SSL edge). AUTHORED, no gradient
training. Does the agent's analytic basis beat raw cochleagram on per-frame phone readout — a
data-efficient feature with NO training cost?

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_composed_net_idea.py [cap]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_earns_acoustic_phonetic import per_frame_acc

W = 4


def ctx_delta(B):
    """context +-W + delta over a per-frame matrix B (the same wrapper for any base)."""
    n, d = B.shape
    dd = np.vstack([np.zeros((1, d)), np.diff(B, axis=0)])
    Pb = np.pad(B, ((W, W), (0, 0)), mode="edge"); Pd = np.pad(dd, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * d * 2))
    for t in range(n):
        v = np.concatenate([Pb[t:t + 2 * W + 1].reshape(-1), Pd[t:t + 2 * W + 1].reshape(-1)])
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    return out


def base_raw(M):
    return M


def base_composed(M):
    """the agent's composed_net basis: [b, b^2, b^3] local-polynomial lift + predictive-residual
    b_t - b_hat(b_{t-1}) (b_hat = previous frame). Authored, no fit."""
    M = np.asarray(M, float)
    resid = M - np.vstack([M[:1], M[:-1]])               # b_t - b_hat(b_{t-1})
    return np.concatenate([M, M ** 2, M ** 3, resid], axis=1)


def pairs(data, base, cap):
    X, Y = [], []
    for w, fr, ph in data:
        B = ctx_delta(base(fr)); n = len(B); P = len(ph)
        for i in range(n):
            X.append(B[i]); Y.append(str(ph[int(i * P / n)]))
        if len(X) >= cap:
            break
    return np.array(X[:cap]), Y[:cap]


def main():
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 45000
    tr = _load_ph("train-clean-100_*.pkl", 12); de = _load_ph("dev-clean_*.pkl", 12)
    phset = sorted({str(p) for _w, _f, ph in tr for p in ph} |
                   {str(p) for _w, _f, ph in de for p in ph}); pi = {p: i for i, p in enumerate(phset)}
    print("=" * 78)
    print("THE JABBERWOCK'S COMPOSE-NOT-TRAIN IDEA — analytic basis vs raw (NO training)")
    print("=" * 78)
    t0 = time.time()
    for name, base in (("raw cochleagram", base_raw),
                       ("agent composed_net [b,b^2,b^3,resid]", base_composed)):
        Xtr, Ytr = pairs(tr, base, cap); Xde, Yde = pairs(de, base, 15000)
        acc, ch = per_frame_acc(Xtr, Ytr, Xde, Yde)
        print(f"  {name:40} per-frame {acc:.3f}  (chance {ch:.3f})", flush=True)
    print("=" * 78)
    print(f"  [{time.time()-t0:.0f}s]  composed_net > raw => the agent's compose-NOT-train idea is a")
    print("  data-efficient lever with ZERO training cost (the closed-form path its ethos prefers).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
