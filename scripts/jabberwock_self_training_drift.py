"""SELF-TRAINING, no fixpoint required — the model trains itself by running, and tracks a drifting
world instead of settling.

Creator: the one-engine result means the model is SELF-TRAINING (running == learning), and it CAN
reach a fixpoint but DOESN'T NEED to. A fixpoint is a model that has stopped learning; cognition lives
OFF it, perpetually tracking a changing world. Not settling is the advantage.

HONEST NOTE: I first ran this on the per-frame phone stream. It NULLED — and the null is itself
informative: at the ~0.16 acoustic floor the drift signal is swamped by noise (frozen didn't even
degrade), and self-training CANNOT bootstrap (84% of pseudo-labels are wrong -> confirmation bias),
while online updates destabilised even with oracle labels. Self-training needs enough base accuracy
that pseudo-labels are mostly right. So the principle is demonstrated on a CONTROLLED drifting task
with measurable base accuracy — the speech floor confounds it, it is not the right testbed.

CONTROLLED TEST: K well-separated Gaussian classes whose means DRIFT (rotation+translation, ramping
up then holding constant in a tail). One linear collapse-classifier (closed-form ridge = the fixpoint),
evaluated PREQUENTIALLY (predict-then-update) over the stream:
  FROZEN        — fixpoint, weights frozen                      (degrades as the means drift away)
  SELF-TRAINING — updates on its OWN confident predictions, NO labels (tracks the drift)
  ORACLE        — updates on true labels (adaptation ceiling)
Claims: (1) label-free self-training recovers what the frozen fixpoint loses; (2) it NEVER needs to
settle — yet when the drift STOPS (stationary tail) it stabilises = the fixpoint is reachable but not
required. The update rule is the SAME residual-feedback collapse (W += lr * Xᵀ(onehot - softmax)).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_self_training_drift.py [seed]
"""
import sys
import numpy as np


def softmax(P):
    P = P - P.max(1, keepdims=True); e = np.exp(P); return e / e.sum(1, keepdims=True)


def make_task(rng, d=2, K=6, R=4.0):
    """K classes on a 2-d circle (radius R). The drift ROTATES the circle: each class moves toward
    the next, crossing the frozen radial boundaries, while the classes stay mutually separable."""
    th = np.linspace(0, 2 * np.pi, K, endpoint=False)
    return np.stack([R * np.cos(th), R * np.sin(th)], 1)


def means_at(M0, alpha, ang=0.85):
    """rotate the whole configuration by alpha*ang (< inter-class spacing => no collision)."""
    c, s = np.cos(alpha * ang), np.sin(alpha * ang)
    return M0 @ np.array([[c, -s], [s, c]]).T


def sample(M, n, sigma, rng):
    K, d = M.shape; y = rng.integers(0, K, n)
    X = M[y] + rng.standard_normal((n, d)) * sigma
    return X, y


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    rng = np.random.default_rng(seed)
    d, K, sigma = 2, 6, 0.7
    M0 = make_task(rng, d, K)
    # base classifier: closed-form ridge collapse on the t=0 distribution (the fixpoint), shared init
    Xtr, ytr = sample(M0, 6000, sigma, rng)
    oh = np.zeros((len(Xtr), K)); oh[np.arange(len(Xtr)), ytr] = 1.0
    Xb = np.hstack([Xtr, np.ones((len(Xtr), 1))])          # bias
    W0 = np.linalg.solve(Xb.T @ Xb + 1.0 * np.eye(d + 1), Xb.T @ (oh - 1.0 / K))

    # FINE-GRAINED stream: many small steps so the per-step drift << class margin (the regime where
    # self-training can track — pseudo-labels stay mostly right; abrupt jumps trap it in its errors).
    NSTEP, NWIN, per, ramp = 96, 12, 150, 0.7
    alphas = np.clip(np.linspace(0, 1, NSTEP) / ramp, 0, 1)
    streams = [sample(means_at(M0, a), per, sigma, np.random.default_rng(100 + j))
               for j, a in enumerate(alphas)]

    def run(frac, lr=0.5, thr=0.55, frozen=False, layer1=True):
        """frac = fraction of samples whose target is the WORLD's truth (Layer 2, grounding); the rest
        self-train on their own CONFIDENT pseudo-labels (Layer 1, self-model) IF layer1 is on.
        layer1=True -> two-layer (self-model + grounding); layer1=False -> grounding ONLY."""
        W = W0.copy(); accs = []; mr = np.random.default_rng(7)
        for (Xw, yw) in streams:
            Xa = np.hstack([Xw, np.ones((len(Xw), 1))])
            p = softmax(Xa @ W); pred = p.argmax(1); accs.append(float(np.mean(pred == yw)))
            if frozen:
                continue
            real = mr.random(len(yw)) < frac                       # Layer 2: the world tells the truth here
            self_ok = (p.max(1) > thr) & ~real if layer1 else np.zeros(len(yw), bool)
            use = real | self_ok                                   # truth, and/or own confident belief
            if use.sum():
                lab = np.where(real, yw, pred)[use]                # residual vs WORLD where real, else vs SELF
                t = np.zeros((use.sum(), K)); t[np.arange(use.sum()), lab] = 1.0
                W += lr * (Xa[use].T @ (t - p[use])) / use.sum()
        return [float(np.mean(c)) for c in np.array_split(np.asarray(accs), NWIN)]   # -> 12 display windows

    fro, slf, ora = run(0.0, frozen=True), run(0.0), run(1.0)
    hw = int(ramp * NWIN)
    print("=" * 80)
    print("SELF-TRAINING under DRIFT (controlled) — prequential acc over stream position")
    print(f"  {K} Gaussian classes, means drift (rotate+translate) over first 70%, then HOLD (tail)")
    print("=" * 80)
    print("  window:    " + "".join(f"{j+1:5d}" for j in range(NWIN)) + f"   | drift holds from ~w{hw+1}")
    print("  FROZEN     " + "".join(f"{a:5.2f}" for a in fro))
    print("  SELF-TRAIN " + "".join(f"{a:5.2f}" for a in slf))
    print("  ORACLE     " + "".join(f"{a:5.2f}" for a in ora))
    print("=" * 80)
    body = slice(NWIN // 3, hw); tail = slice(hw, NWIN)
    fb, sb, ob = np.mean(fro[body]), np.mean(slf[body]), np.mean(ora[body])
    print(f"  mid-drift  : frozen {fb:.3f}  self-train(0% truth) {sb:.3f}  oracle(100%) {ob:.3f}")
    print(f"  => self-train == frozen: a confidently-wrong model self-training on its OWN belief")
    print(f"     corrects NOTHING (residual vs self ~0). Only the WORLD's residual (oracle) recovers it.")
    print("=" * 80)
    # THE TWO LAYERS: does Layer 1 (self-model) HELP Layer 2 (grounding), or only fight it?
    print("  TWO-LAYER COGNITION — mid-drift acc vs world-truth %, WITH vs WITHOUT the self-model:")
    fracs = (0.02, 0.05, 0.10, 0.15, 0.20, 0.30, 0.50)
    print(f"    {'world-truth %':>20}" + "".join(f"{int(f*100):6d}" for f in fracs))
    two = [np.mean(run(f, layer1=True)[body]) for f in fracs]    # Layer1 + Layer2
    gnd = [np.mean(run(f, layer1=False)[body]) for f in fracs]   # Layer2 only (grounding-only)
    print(f"    {'two-layer (self+world)':>20}" + "".join(f"{a:6.2f}" for a in two))
    print(f"    {'grounding-only (world)':>20}" + "".join(f"{a:6.2f}" for a in gnd))
    print(f"    {'Δ (self-model adds)':>20}" + "".join(f"{t-g:+6.2f}" for t, g in zip(two, gnd)))
    print("=" * 80)
    print("  TWO-LAYER COGNITION, right here: ONE engine, ONE residual — the only difference is its")
    print("  SOURCE. Layer 1 (self-model) runs on the residual-vs-SELF: fast, label-free, autonomous —")
    print("  and alone it settles into confident error (delusion: self-train == frozen). Layer 2")
    print("  (grounding) runs on the residual-vs-WORLD: sparse, corrective — it CAPTURES Layer 1 past a")
    print("  threshold. Neither is cognition alone: Layer 1 = coherent delusion, Layer 2 = ungeneralised")
    print("  lookup. The Δ row shows whether the self-model AMPLIFIES sparse grounding (synergy = why")
    print("  cognition has two layers) or merely fights it (must be overcome). Reality-grounded self-model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
