"""TWO LAYERS OF COGNITION — and the ladder of animals.

Creator: this defines cognition into two layers and delineates different animals. The cut (from "ask
how to walk"):
  LAYER 1 — reality-grounded nets, the WORLD IN THE LOOP. Walk by walking; correct via the world's
            residual each step. Inarticulable, UNIVERSAL — every animal has it.
  LAYER 2 — an INTERNAL MODEL you can run WITHOUT the world. Act open-loop, PLAN, TRANSFER, articulate.
            Present in DEGREES — and the degree is the delineation between animals.

The animal ladder (same body g(a)=2*tanh(th*a); learn to hit a target outcome):
  R1  CLOSED-LOOP (world in loop)          — reflex search a<-a+k(y*-g(a)). ALL animals; competent.
  R2  OPEN-LOOP / OFFLINE (no world test)  — needs an INTERNAL MODEL. Reflex (no world) FAILS;
                                             a learned inverse model acts open-loop. = Layer 2 appears.
  R3  TRANSFER to a NEW body, few trials   — needs a META-MODEL over bodies (the shared inverse shape,
                                             per-body scale). Scratch relearns; meta adapts few-shot.
                                             = deeper Layer 2.
Each rung is a Layer-2 affordance the rung below lacks; an animal's place on the ladder = how much
Layer 2 it has on top of the universal Layer 1.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_two_layers_animals.py
"""
import numpy as np


def g(a, th):
    return 2.0 * np.tanh(th * a)


def reflex(y, th, steps, k=0.4):
    """LAYER 1: closed-loop, the world in the loop. steps>0 -> the world corrects; steps=0 -> no world."""
    a = np.zeros_like(y)
    for _ in range(steps):
        a = a + k * (y - g(a, th))          # the WORLD's residual, every step
    return a


def err(a, y, th):
    return float(np.mean(np.abs(y - g(a, th))))


def rbf(x, c, gam):
    return np.exp(-gam * (x[:, None] - c[None]) ** 2)


def main():
    rng = np.random.default_rng(0)
    th_test = 1.7                                   # the body this animal must act in
    yte = rng.uniform(-1.7, 1.7, 2000)
    print("=" * 80)
    print("TWO LAYERS OF COGNITION — the animal ladder (graded by Layer 2 on top of universal Layer 1)")
    print("=" * 80)

    # R1 — LAYER 1, closed-loop (the world in the loop). Every animal.
    a_cl = reflex(yte, th_test, steps=60)
    print(f"\nR1  CLOSED-LOOP (world in the loop)   reach error {err(a_cl, yte, th_test):.3f}   "
          f"[Layer 1 — UNIVERSAL: every animal walks by walking]")

    # R2 — OPEN-LOOP / OFFLINE (no world at test). Reflex fails; an internal model acts without the world.
    a_reflex_offline = reflex(yte, th_test, steps=0)            # reflex with NO world = nothing
    ytr = rng.uniform(-1.7, 1.7, 4000); atr = reflex(ytr, th_test, 60)   # experience via world feedback
    c = np.linspace(-1.7, 1.7, 40); gam = 6.0
    Wm = np.linalg.solve(rbf(ytr, c, gam).T @ rbf(ytr, c, gam) + 1e-3 * np.eye(40),
                         rbf(ytr, c, gam).T @ atr)
    a_model_offline = rbf(yte, c, gam) @ Wm                     # internal model, NO world at test
    print(f"\nR2  OPEN-LOOP / OFFLINE (no world)    reflex {err(a_reflex_offline, yte, th_test):.3f}   "
          f"vs internal-model {err(a_model_offline, yte, th_test):.3f}")
    print("    [Layer 2 APPEARS: an internal model acts without the world; the reflex cannot — this is")
    print("     the first cognitive rung: imagine/plan instead of needing the world in the loop]")

    # R3 — TRANSFER to a NEW body with few trials. Meta-model over bodies = the shared inverse shape.
    grid = np.linspace(-1.7, 1.7, 60)
    train_th = np.linspace(0.8, 2.6, 16)
    F = np.stack([reflex(grid, t, 60) for t in train_th])       # per-body inverse functions
    # collapse over bodies -> the SHARED shape (they are scalar multiples: a*_th(y)=h(y)/th) => rank-1
    _, _, Vt = np.linalg.svd(F - F.mean(0), full_matrices=False)
    hbar = Vt[0]                                                # the shared inverse shape h(y), up to scale
    hbar = hbar / np.sign(hbar @ (grid))                       # orient with the target

    print(f"\nR3  TRANSFER to a NEW body (th={th_test}), open-loop error vs #world-trials:")
    print(f"    {'trials':>10}" + "".join(f"{n:7d}" for n in (1, 2, 4, 8, 20)))
    sc, mt = [], []
    for n in (1, 2, 4, 8, 20):
        es_s, es_m = [], []
        for _ in range(40):
            yn = rng.uniform(-1.7, 1.7, n); an = reflex(yn, th_test, 60)         # n trials, world feedback
            # SCRATCH model-holder: fit a fresh RBF inverse from n trials only
            P = rbf(yn, c, gam); Ws = np.linalg.solve(P.T @ P + 1e-1 * np.eye(40), P.T @ an)
            es_s.append(err(rbf(yte, c, gam) @ Ws, yte, th_test))
            # META: a(y) = s * hbar(y); fit only the scalar s from n trials (1 param)
            hn = np.interp(yn, grid, hbar); s = (hn @ an) / (hn @ hn + 1e-9)
            es_m.append(err(s * np.interp(yte, grid, hbar), yte, th_test))
        sc.append(np.mean(es_s)); mt.append(np.mean(es_m))
    print(f"    {'scratch':>10}" + "".join(f"{e:7.2f}" for e in sc) + "   [Layer-2 internal model, per body]")
    print(f"    {'meta':>10}" + "".join(f"{e:7.2f}" for e in mt) + "   [Layer-2 META over bodies — few-shot]")

    print("=" * 80)
    print("  THE LADDER: R1 closed-loop = LAYER 1, universal (every animal walks, world in the loop).")
    print("  R2 open-loop = LAYER 2 appears (an internal model acts WITHOUT the world — imagine/plan;")
    print("  the reflex cannot). R3 = DEEPER Layer 2 (a meta-model over bodies transfers few-shot where")
    print("  a per-body model must relearn). Different animals = how far up this ladder — how much")
    print("  Layer 2 sits on the universal reality-grounded Layer 1. Cognition is the world-free model;")
    print("  competence (Layer 1) never needed it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
