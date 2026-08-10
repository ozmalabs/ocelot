"""META-MODEL — collapse one level up: a model of the model-manifold makes new models faster.

Creator: model-building IS the collapse engine, and models (like data) live on a low-dim manifold ->
we can collapse ONE LEVEL UP, over many models, to recover the MANIFOLD OF MODELS. That recovered
manifold is the META-MODEL. Building a NEW model is then no longer a search of the full parameter
space — it is a COLLAPSE WITHIN the meta-manifold: far fewer steps, far less data. The meta-model is
STRUCTURE that replaces the per-model data ("structure replaces data", applied to model-building).

TEST: a family of tasks sharing a hidden low-dim discriminative subspace U (Ks of D dims; the other
D-Ks dims are nuisance). The meta-model is U recovered from META-TRAIN tasks (PCA of their class-mean
structure — collapse over models). For a NEW task, build a classifier:
  FROM-SCRATCH — centroids in full D (must beat down D-Ks nuisance dims -> needs many labels)
  META         — project onto the recovered meta-subspace, centroids in Ks (-> needs ~Ks labels)
  ORACLE       — the true U (upper bound on the meta-model)
Claim: META reaches high accuracy with FAR fewer labels than from-scratch = making models faster.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_meta_model.py [seed]
"""
import sys
import numpy as np

D, Ks, K, sep, sig = 300, 5, 6, 2.4, 1.0    # ambient, shared subspace, classes, separation, noise


def make_task(U, rng):
    """a task = K class means living in the shared subspace U, embedded in D dims."""
    msub = rng.standard_normal((K, Ks)) * sep
    return msub @ U.T                        # (K, D)


def sample(mD, npc, rng):
    y = np.repeat(np.arange(K), npc)
    X = mD[y] + rng.standard_normal((len(y), D)) * sig
    return X, y


def centroid_acc(Xs, ys, Xq, yq, P=None):
    """build a model = class centroids (a cheap collapse); optionally in projected space P (D,k)."""
    A, B = (Xs @ P, Xq @ P) if P is not None else (Xs, Xq)
    C = np.stack([A[ys == k].mean(0) for k in range(K)])
    pred = (((B[:, None] - C[None]) ** 2).sum(2)).argmin(1)
    return float(np.mean(pred == yq))


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    rng = np.random.default_rng(seed)
    U, _ = np.linalg.qr(rng.standard_normal((D, Ks)))     # the TRUE shared subspace (hidden)

    # META-TRAIN: recover the shared subspace by collapsing over many models (PCA of class-mean structure)
    diffs = []
    for _ in range(40):
        mD = make_task(U, rng); diffs.append(mD - mD.mean(0))
    _, _, Vt = np.linalg.svd(np.vstack(diffs), full_matrices=False)
    Uhat = Vt[:Ks].T                                       # the META-MODEL: recovered manifold of models
    align = np.linalg.svd(U.T @ Uhat, compute_uv=False).mean()
    print("=" * 76)
    print("META-MODEL — a model of the model-manifold makes new models faster")
    print(f"  ambient D={D}, hidden shared subspace Ks={Ks}, {K} classes; meta-model recovered from 40")
    print(f"  tasks (subspace alignment to truth: {align:.3f}, 1.0=perfect)")
    print("=" * 76)
    print(f"  {'labels/class':>14}" + "".join(f"{n:7d}" for n in (1, 2, 3, 5, 10, 20)))
    tr = np.random.default_rng(seed + 99)
    for tag, P in (("from-scratch (D=%d)" % D, None), ("META (Ks=%d)" % Ks, Uhat), ("oracle U", U)):
        row = []
        for npc in (1, 2, 3, 5, 10, 20):
            accs = []
            for _ in range(60):
                mD = make_task(U, tr)
                Xs, ys = sample(mD, npc, tr); Xq, yq = sample(mD, 200, tr)
                accs.append(centroid_acc(Xs, ys, Xq, yq, P))
            row.append(np.mean(accs))
        print(f"  {tag:>14}" + "".join(f"{a:7.2f}" for a in row))
    print("=" * 76)
    print("  META reaches high accuracy with FAR fewer labels than from-scratch: the meta-model collapses")
    print("  model-building from a D-dim search to a Ks-dim one. Building each NEW model is now a fast")
    print("  collapse WITHIN the meta-manifold — structure (the meta-model) replaces per-model data.")
    print("  This is the recursion: the collapse engine run one level up makes making models faster.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
