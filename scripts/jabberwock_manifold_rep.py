"""Ground the jabberwock in the manifold approach, have it plan, and EXECUTE the key experiment.

Grounding (docs/manifold_approach_grounding.md): learning cost scales with INTRINSIC dim (~4-13
for speech), not ambient (32) -> the manifold coords are a data-efficient rep. CRITICAL CATCH
(Ben-David): only if the manifold carries PHONETIC info — by default it carries SPEAKER (the
nuisance / lack_of_invariance). FIX: quotient out the speaker (project out per-word/utterance mean)
BEFORE building the manifold. METHOD #1: diffusion maps + Nystrom out-of-sample (closed-form).

THE EXPERIMENT (the agent's plan, executed): build a SPEAKER-QUOTIENTED diffusion-map manifold
(Nystrom-extended), and test per-frame phone readout DATA-EFFICIENCY vs ambient at varying labels.
Measure-or-drop guard: keep the manifold rep only if it buys back data AND carries phonetic info.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_manifold_rep.py [Kdim]
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_earns_acoustic_phonetic import per_frame_acc


W = 4


def ctxd(B):
    """context +-W + delta (phones need temporal context; single frames are at the floor)."""
    n, d = B.shape
    dd = np.vstack([np.zeros((1, d)), np.diff(B, axis=0)])
    Pb = np.pad(B, ((W, W), (0, 0)), mode="edge"); Pd = np.pad(dd, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * d * 2))
    for t in range(n):
        v = np.concatenate([Pb[t:t + 2 * W + 1].reshape(-1), Pd[t:t + 2 * W + 1].reshape(-1)])
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    return out


def quotient(fr):
    """speaker/channel nuisance fix: subtract the per-word mean (the available per-utterance proxy)."""
    fr = np.asarray(fr, float)
    return fr - fr.mean(0, keepdims=True)


def diffusion_fit(L, K, sigma=None):
    """symmetric diffusion map on landmarks L -> (eigvecs V (M,K), eigvals lam, d, sigma)."""
    G = L @ L.T; sq = np.diag(G).copy()
    D2 = np.maximum(sq[:, None] + sq[None, :] - 2 * G, 0.0)
    if sigma is None:
        sigma = np.sqrt(np.median(D2[D2 > 0]))
    Kk = np.exp(-D2 / (2 * sigma ** 2))
    d = Kk.sum(1); A = Kk / np.sqrt(d[:, None] * d[None, :])
    w, V = np.linalg.eigh(A)                      # ascending
    order = np.argsort(-w)[1:K + 1]              # top-K, skip trivial (largest)
    return V[:, order], w[order], d, sigma


def diffusion_extend(X, L, V, lam, d, sigma):
    """Nystrom out-of-sample: extended eigenfunctions for X (n,K)."""
    G = X @ L.T; sqx = (X ** 2).sum(1); sql = (L ** 2).sum(1)
    D2 = np.maximum(sqx[:, None] + sql[None, :] - 2 * G, 0.0)
    Kk = np.exp(-D2 / (2 * sigma ** 2))
    dx = Kk.sum(1); A = Kk / np.sqrt(dx[:, None] * d[None, :])
    psi = (A @ V) / np.clip(lam, 1e-9, None)     # (n,K)
    return psi / np.clip(np.linalg.norm(psi, axis=1, keepdims=True), 1e-9, None)


def frames_labeled(data, q, cap):
    """CONTEXT vectors (ctxd over quotiented or raw frames) + phone labels."""
    X, Y = [], []
    for w, fr, ph in data:
        base = quotient(fr) if q else np.asarray(fr, float)
        B = ctxd(base); n = len(B); P = len(ph)
        for i in range(n):
            X.append(B[i]); Y.append(str(ph[int(i * P / n)]))
        if len(X) >= cap:
            break
    return np.array(X[:cap]), Y[:cap]


def main():
    K = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    tr = _load_ph("train-clean-100_*.pkl", 10); de = _load_ph("dev-clean_*.pkl", 10)
    print("=" * 80)
    print(f"MANIFOLD REP — speaker-quotiented diffusion map ({K}d), Nystrom; phonetic data-efficiency")
    print("=" * 80)
    t0 = time.time()
    Xtr, Ytr = frames_labeled(tr, q=True, cap=40000)
    Xde, Yde = frames_labeled(de, q=True, cap=12000)
    XtrA, _ = frames_labeled(tr, q=False, cap=40000)   # ambient (un-quotiented) raw
    XdeA, _ = frames_labeled(de, q=False, cap=12000)
    phset = sorted(set(Ytr) | set(Yde)); pi = {p: i for i, p in enumerate(phset)}
    rng = np.random.default_rng(0)

    # fit diffusion manifold on speaker-quotiented landmarks
    lmk = Xtr[rng.choice(len(Xtr), 1500, replace=False)]
    V, lam, d, sigma = diffusion_fit(lmk, K)
    Ztr = diffusion_extend(Xtr, lmk, V, lam, d, sigma)
    Zde = diffusion_extend(Xde, lmk, V, lam, d, sigma)
    print(f"  manifold fit on 1500 landmarks, Nystrom-extended [{time.time()-t0:.0f}s]", flush=True)

    print(f"\n  {'#labels':>8} {'ambient raw(32)':>16} {'quotient raw(32)':>17} {'manifold('+str(K)+'d)':>14}")
    for N in (250, 1000, 4000, 16000):
        if N > len(Xtr):
            N = len(Xtr)
        s = rng.choice(len(Xtr), N, replace=False); Ys = [Ytr[i] for i in s]
        amb, _ = per_frame_acc(XtrA[s], Ys, XdeA, Yde, )
        quo, _ = per_frame_acc(Xtr[s], Ys, Xde, Yde)
        man, _ = per_frame_acc(Ztr[s], Ys, Zde, Yde)
        print(f"  {N:8d} {amb:16.3f} {quo:17.3f} {man:14.3f}", flush=True)
    print("=" * 80)
    print(f"  [{time.time()-t0:.0f}s]  manifold > ambient at LOW N => the {K}d phonetic manifold buys back")
    print("  data; if manifold ~ ambient, the recovered manifold is the SPEAKER one (nuisance not quotiented).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
