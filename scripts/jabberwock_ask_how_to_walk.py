"""ASK SOMEONE HOW TO WALK — nets need REALITY grounding, not COGNITIVE grounding.

Creator: "nets do not need to be grounded in cognition. ask someone how to walk." Two groundings were
being conflated:
  - grounded in REALITY  — the residual comes from the WORLD (you fall over). NECESSARY (else delusion;
    the two-layer / capture result). A walking net is fully grounded here: physics is its teacher.
  - grounded in COGNITION — reachable by the deliberative / articulable / self-report layer. NOT
    necessary. Ask someone how they walk -> nothing, or a confabulated rule that wouldn't keep them up.

TEST: learn a motor skill — the INVERSE of an unknown nonlinear body g(a) (produce the action a that
hits a desired outcome y*) — PURELY from world feedback (the residual y*-g(a); the dynamics are never
given; the residual-feedback recurrence = our engine). The learned experience (y*, a*) is then read
out two ways:
  NET        — a flexible inarticulable map (RBF)         -> the skill, reality-grounded
  ARTICULABLE— the compact rule cognition could STATE     -> "how you walk", said out loud
                (linear "a = k*y*"; and a cubic, a more generous articulable account)
Measure the WORLD reaching error |y* - g(pi(y*))| on fresh targets. Claim: the net walks (low error);
the articulable account does NOT (high error) — competence is reality-grounded and inarticulable.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_ask_how_to_walk.py
"""
import numpy as np


def g(a):
    """the BODY / world: an unknown nonlinear map action->outcome (saturating, monotone)."""
    return 2.0 * np.tanh(1.5 * a)


def learn_by_world_feedback(targets, rng, steps=60, k=0.4):
    """gather experience the only way a body can: try an action, FEEL the world's error, adjust.
    a <- a + k*(y* - g(a)) — the residual is the WORLD's, the dynamics g are never known. = walking."""
    A = np.zeros_like(targets)
    for _ in range(steps):
        A = A + k * (targets - g(A))            # the world's residual feeds the correction
    return A                                     # a* ~ g^{-1}(y*), discovered by reality, not by formula


def rbf(x, c, gam):
    return np.exp(-gam * (x[:, None] - c[None]) ** 2)


def main():
    rng = np.random.default_rng(0)
    # experience: targets within the body's reachable range, solved by world feedback (no formula)
    ytr = rng.uniform(-1.7, 1.7, 4000)
    atr = learn_by_world_feedback(ytr, rng)      # reality-grounded experience (y*, a*)
    yte = rng.uniform(-1.7, 1.7, 2000)

    # NET — flexible, inarticulable map (RBF ridge) fit to the reality-gathered experience
    c = np.linspace(-1.7, 1.7, 40); gam = 6.0
    Phi = rbf(ytr, c, gam); Wn = np.linalg.solve(Phi.T @ Phi + 1e-3 * np.eye(40), Phi.T @ atr)
    a_net = rbf(yte, c, gam) @ Wn

    # ARTICULABLE — the compact rule cognition could STATE ("how to walk"), same experience
    def poly_fit(deg):
        X = np.vstack([ytr ** d for d in range(deg + 1)]).T
        w = np.linalg.solve(X.T @ X + 1e-9 * np.eye(deg + 1), X.T @ atr)
        Xte = np.vstack([yte ** d for d in range(deg + 1)]).T
        return Xte @ w, w
    a_lin, wlin = poly_fit(1)
    a_cub, _ = poly_fit(3)

    def reach_err(a):                            # the only thing that matters: did you hit it (in the world)?
        return float(np.mean(np.abs(yte - g(a))))

    print("=" * 78)
    print("ASK SOMEONE HOW TO WALK — reality grounding vs cognitive grounding")
    print("  skill = hit a desired outcome y* through an unknown nonlinear body g(a),")
    print("  learned PURELY from world feedback (residual y*-g(a); g never known)")
    print("=" * 78)
    print(f"  {'readout of the learned skill':38}{'world reaching error':>22}")
    print(f"  {'NET (inarticulable RBF map)':38}{reach_err(a_net):22.3f}")
    print(f"  {'ARTICULABLE linear rule  a = %+.2f*y*' % wlin[1]:38}{reach_err(a_lin):22.3f}")
    print(f"  {'ARTICULABLE cubic rule (generous)':38}{reach_err(a_cub):22.3f}")
    print("=" * 78)
    # control: the skill REQUIRES reality grounding — strip world feedback (0 steps) and it cannot reach
    a_nofeedback = learn_by_world_feedback(yte, rng, steps=0)
    print(f"  control — NO world feedback (cognition alone, no reality): reach error {reach_err(a_nofeedback):.3f}")
    print("=" * 78)
    print("  The NET walks (low world error); the ARTICULABLE rule — what you'd SAY if asked how — does")
    print("  NOT (it cannot express the body's nonlinear inverse, on the SAME experience). Strip the")
    print("  world's residual and nothing is learned at all. So: competence needs REALITY grounding")
    print("  (the world's residual), NOT COGNITIVE grounding (an articulable account). Ask someone how")
    print("  to walk and the answer they can state is not the skill — the skill lives in a net cognition")
    print("  cannot reach, and does not need to.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
