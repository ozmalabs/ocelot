"""PHASE 2, on the PART level — per-PRIMITIVE deformation modes (clean alignment via the Phase-1 basis).

Phase 2 at the whole-trajectory level HURT: drawings aren't point-aligned, so within-char variation = noise.
The fix the diagnosis named: ride the basis. Parts that activate the SAME sparse PRIMITIVE are the same
stroke shape -> pre-aligned -> their variation IS the clean deformation manifold of that primitive. So learn
per-primitive deformation modes (PCA of part - atom over each atom's instances), and match parts by the
OFF-MODE residual under the query part's primitive. Does the learned per-primitive deformation prior now beat
the raw geometric part match?
  raw part-shape distance  vs  per-primitive OFF-MODE residual (learned deformation prior)

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_part_deformation [episodes]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from substrate_rs import _native
from domains import omniglot_world as ow
from scripts.jabberwock_sparse_primitives import part_vecs, D, K_ATOMS, LAM, EPOCHS, LR, ITERS, STEP

SEP = "=" * 92
M_MODES = 8            # deformation modes per primitive
PEN = 0.15            # deformation-magnitude penalty (the prior's neg-log-likelihood weight)


def chamfer(A, dist):
    pass


def main():
    episodes = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    way = 20
    print(SEP)
    print("PHASE 2 (PART level) — per-PRIMITIVE deformation modes via the basis; OFF-MODE residual match.")
    print(SEP)
    if not (ow.have_data("evaluation") and ow.have_data("background")):
        print("\n  data missing."); return 1

    bg = []
    for al in ow.alphabets("background"):
        for ch in ow.characters(al, "background"):
            for dr in ow.drawings(ch)[:2]:
                bg.extend(part_vecs(dr))
            if len(bg) >= 7000:
                break
        if len(bg) >= 7000:
            break
    Bg = np.asarray(bg)
    print(f"\n  learning {K_ATOMS}-atom basis + per-primitive deformation modes over {len(Bg)} background parts...", flush=True)
    atoms = np.asarray(_native.sparse_dict_learn(Bg.reshape(-1).tolist(), len(Bg), D, K_ATOMS, LAM, EPOCHS, LR, ITERS, STEP)).reshape(K_ATOMS, D)

    # assign each background part to its nearest atom; per atom, PCA of (part - atom) = its deformation modes.
    an = atoms / (np.linalg.norm(atoms, axis=1, keepdims=True) + 1e-9)
    Bn = Bg / (np.linalg.norm(Bg, axis=1, keepdims=True) + 1e-9)
    assign = np.argmax(Bn @ an.T, axis=1)
    modes = np.zeros((K_ATOMS, D, M_MODES))
    for a in range(K_ATOMS):
        grp = Bg[assign == a]
        if len(grp) < M_MODES + 2:
            continue
        res = grp - atoms[a]
        cov = res.T @ res / len(res)
        ev, evec = np.linalg.eigh(cov)
        modes[a] = evec[:, ::-1][:, :M_MODES]
    print(f"    deformation modes learned (avg {np.mean([np.count_nonzero(assign==a) for a in range(K_ATOMS)]):.0f} parts/atom).\n", flush=True)

    def atom_of(v):
        vn = v / (np.linalg.norm(v) + 1e-9)
        return int(np.argmax(an @ vn))

    by_alph = {a: ow.characters(a, "evaluation") for a in ow.alphabets("evaluation")}
    by_alph = {a: cs for a, cs in by_alph.items() if len(cs) >= way}
    alph = sorted(by_alph); pc: dict = {}

    def parts(p):
        if p not in pc:
            pc[p] = part_vecs(p)
        return pc[p]

    rng = np.random.default_rng(7); specs = []
    for _ in range(episodes):
        ch = by_alph[alph[int(rng.integers(len(alph)))]]
        idx = rng.permutation(len(ch))[:way]
        ex = int(rng.integers(20)); qd = int(rng.integers(20))
        while qd == ex:
            qd = int(rng.integers(20))
        specs.append((ch, idx, ex, qd))

    def raw_pd(q, e):
        return float(np.linalg.norm(q - e))

    def off_pd(q, e):
        d = q - e
        Ma = modes[atom_of(q)]
        c = Ma.T @ d
        off = d - Ma @ c
        return float(np.linalg.norm(off) + PEN * np.linalg.norm(c))

    def char_dist(Q, E, pd):
        if not len(Q) or not len(E):
            return 9.9
        dm = np.array([[pd(q, e) for e in E] for q in Q])
        return dm.min(1).mean() + dm.min(0).mean()

    def recog(pd):
        ok = tot = 0
        for ch, idx, ex, qd in specs:
            lib = [(ch[j], parts(ow.drawings(ch[j])[ex])) for j in idx if len(ow.drawings(ch[j])) >= 20]
            for j in idx:
                ds = ow.drawings(ch[j])
                if len(ds) < 20:
                    continue
                Q = parts(ds[qd]); tot += 1
                best, arg = 1e18, None
                for nm, E in lib:
                    dd = char_dist(Q, E, pd)
                    if dd < best:
                        best, arg = dd, nm
                ok += (arg == ch[j])
        return 100 * ok / max(tot, 1)

    print(f"  {episodes} episodes, {way}-way one-shot:\n", flush=True)
    r = recog(raw_pd); print(f"    raw part-shape distance                  : {r:5.1f}%", flush=True)
    o = recog(off_pd); print(f"    per-primitive OFF-MODE (learned deform)  : {o:5.1f}%   ({o-r:+.1f})", flush=True)

    print(f"\n  {SEP[:88]}")
    d = o - r
    if d >= 1.5:
        print(f"  THE PART-LEVEL DEFORMATION PRIOR PAYS (+{d:.1f}). With the basis providing clean alignment (same")
        print(f"  primitive = same shape), the learned per-primitive deformation modes explain away plausible")
        print(f"  distortion; only off-manifold residual counts. The whole-trajectory version failed on alignment;")
        print(f"  riding the basis fixes it. Phase 2 stands on the part level -- fold into the full recogniser next.")
    else:
        print(f"  honest reading ({d:+.1f}): even with basis-clean alignment, projecting out the learned deformation")
        print(f"  does not beat the raw part match -- the per-primitive modes also absorb DISCRIMINATIVE shape")
        print(f"  variation (a stroke's 'deformation' and its identity overlap at this scale). The off-mode residual")
        print(f"  is the right idea but the deformation/identity split is not clean for single strokes; the gain")
        print(f"  needs the COMPOSITION level (Phase 3) where identity lives in the part ARRANGEMENT, not one stroke.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
