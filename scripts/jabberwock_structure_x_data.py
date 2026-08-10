"""Execute the jabberwock's plan — the STRUCTURE x DATA surface (free-first, measure-or-drop).

The agent's grounded plan: stack FREE analytic priors on the cochlear baseline and measure how much
DATA each unit of earned STRUCTURE buys back. Structure levels (cumulative, all zero-data/analytic):
  S0  raw cochleagram (the gammatone front end = step-1 cochlea, already the baseline)
  S1  + predictive-residual  b_t - b_hat(b_{t-1})            (step 2, FREE, the keystone)
  S2  + source-filter decomposition (cepstral env=filter/formants, residual=source)  (step 3, FREE)
  S3  + compose-not-train poly lift [b^2, b^3]               (the validated +7% basis)
Data axis: labeled budget N. Metric: per-frame phone acc. GUARD (bitter-lesson): keep a level only
if it buys back data (improves at fixed N, esp. small N); else it conflicts -> drop.

DELIVERABLE: the iso-accuracy surface — acc vs (structure level) x N, and the data-efficiency
multiplier (how many fewer labels a higher structure level needs to match a lower one's best).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_structure_x_data.py [cap]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from scripts.jabberwock_subword_recognizer import _load_ph
from scripts.jabberwock_earns_acoustic_phonetic import per_frame_acc

NB = 32
W = 4


def dctmat(N):
    n = np.arange(N); k = np.arange(N)[:, None]
    D = np.cos(np.pi * (2 * n + 1) * k / (2 * N)).astype(float)
    D[0] *= 1 / np.sqrt(N); D[1:] *= np.sqrt(2.0 / N)
    return D
DCT = dctmat(NB)


def prev(M):
    return np.vstack([M[:1], M[:-1]])


def source_filter(M, K=8):
    """analytic source-filter: low cepstra = smooth spectral envelope (filter/formants),
    residual = source (pitch/fine structure). The source-filter prior, zero data."""
    logb = np.log(np.abs(np.asarray(M, float)) + 1e-4)
    cep = logb @ DCT.T
    lo = cep.copy(); lo[:, K:] = 0.0
    env = lo @ DCT                         # filter/formant envelope (log domain)
    src = logb - env                       # source / fine structure
    return env, src


def base(M, level):
    M = np.asarray(M, float)
    parts = [M]
    if level >= 1:
        parts.append(M - prev(M))                      # S1 predictive-residual
    if level >= 2:
        env, src = source_filter(M); parts += [env, src]   # S2 source-filter
    if level >= 3:
        parts += [M ** 2, M ** 3]                       # S3 compose-not-train poly
    return np.concatenate(parts, axis=1)


def ctxd(B):
    n, d = B.shape
    dd = np.vstack([np.zeros((1, d)), np.diff(B, axis=0)])
    Pb = np.pad(B, ((W, W), (0, 0)), mode="edge"); Pd = np.pad(dd, ((W, W), (0, 0)), mode="edge")
    out = np.empty((n, (2 * W + 1) * d * 2))
    for t in range(n):
        v = np.concatenate([Pb[t:t + 2 * W + 1].reshape(-1), Pd[t:t + 2 * W + 1].reshape(-1)])
        out[t] = v / max(np.linalg.norm(v), 1e-9)
    return out


def pairs(data, level, cap):
    X, Y = [], []
    for w, fr, ph in data:
        B = ctxd(base(fr, level)); n = len(B); P = len(ph)
        for i in range(n):
            X.append(B[i]); Y.append(str(ph[int(i * P / n)]))
        if len(X) >= cap:
            break
    return np.array(X[:cap]), Y[:cap]


def main():
    cap = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
    tr = _load_ph("train-clean-100_*.pkl", 12); de = _load_ph("dev-clean_*.pkl", 12)
    phset = sorted({str(p) for _w, _f, ph in tr for p in ph} |
                   {str(p) for _w, _f, ph in de for p in ph}); pi = {p: i for i, p in enumerate(phset)}
    Ns = (250, 1000, 4000, 16000)
    names = ["S0 raw cochlea", "S1 +pred-residual", "S2 +source-filter", "S3 +poly"]
    print("=" * 84)
    print("STRUCTURE x DATA SURFACE (per-frame phone acc; free analytic priors stacked)")
    print("=" * 84)
    print(f"  {'structure level':22}" + "".join(f"{('N='+str(n)):>10}" for n in Ns), flush=True)
    rng = np.random.default_rng(1); t0 = time.time(); surface = []
    for lvl in range(4):
        Xtr, Ytr = pairs(tr, lvl, cap); Xde, Yde = pairs(de, lvl, 12000)
        row = []
        for N in Ns:
            s = rng.choice(len(Xtr), min(N, len(Xtr)), replace=False)
            acc, _ = per_frame_acc(Xtr[s], [Ytr[i] for i in s], Xde, Yde)
            row.append(acc)
        surface.append(row)
        print(f"  {names[lvl]:22}" + "".join(f"{a:10.3f}" for a in row), flush=True)
    print("=" * 84)
    # measure-or-drop guard + the data multiplier
    print("  GUARD (keep level iff it buys back data vs the one below):")
    for lvl in range(1, 4):
        d_small = surface[lvl][0] - surface[lvl - 1][0]      # buyback at smallest N
        d_big = surface[lvl][-1] - surface[lvl - 1][-1]
        verdict = "KEEP" if d_small > 0.003 or d_big > 0.003 else "DROP (conflicts/no buyback)"
        print(f"     {names[lvl]:22} vs below: dN={Ns[0]} {d_small:+.3f}  dN={Ns[-1]} {d_big:+.3f}  -> {verdict}")
    best0 = max(surface[0])                                  # raw's best (most labels)
    # how few labels does the top kept level need to match raw's best?
    top = surface[-1]
    mult = next((f"<={Ns[i]}" for i in range(len(Ns)) if top[i] >= best0), f">{Ns[-1]}")
    print(f"  DATA MULTIPLIER: top structure matches raw's best ({best0:.3f}) at N {mult} "
          f"(raw needed N={Ns[-1]}) [{time.time()-t0:.0f}s]")
    print("  => earned analytic structure buys back labels; the iso-accuracy surface is the deliverable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
