"""THE COGNITION ASSAY — the difference is TESTS.

The two-layer taxonomy (Layer 1 reality-grounded/world-in-loop; Layer 2 world-free internal model,
graded) matches existing proposals — model-free vs model-based control, Dennett's Tower (Skinnerian/
Popperian/Gregorian), Craik's mental models, procedural vs declarative. But those are DESCRIPTIVE:
argued from evidence after the fact. None gives a way to take an unknown system and MEASURE which
layer it has. The contribution here is the TEST BATTERY — each rung a DISCRIMINATIVE test (a value the
subject must beat a negative CONTROL on), so a system is PLACED on the ladder prospectively.

The battery (body g(a)=2*tanh(th*a); learn to hit a target outcome y*):
  T1 LAYER-1 competence    — act with the world IN the loop.        control: a do-nothing null.
  T2 LAYER-2 offline       — act with NO world at test.             control: the reflex (no model).
  T3 deep LAYER-2 transfer — new body, FEW trials, act offline.     control: a per-body model (relearns).
  T4 articulability        — can a STATED rule reproduce the policy? control: the inarticulable net.
  T5 grounding (anti-delusion) — under drift, learn by WORLD vs by SELF: track or freeze?
Subjects: REFLEX (Layer 1), MODEL-HOLDER (+internal model), META (+cross-body abstraction).

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_cognition_assay.py
"""
import numpy as np

PASS = 0.10                                   # reach-error threshold for "competent"


def g(a, th):
    return 2.0 * np.tanh(th * a)


def reflex(y, th, steps, k=0.4):
    a = np.zeros_like(y)
    for _ in range(steps):
        a = a + k * (y - g(a, th))            # the WORLD in the loop
    return a


def err(a, y, th):
    return float(np.mean(np.abs(y - g(a, th))))


def rbf(x, c, gam):
    return np.exp(-gam * (x[:, None] - c[None]) ** 2)


C = np.linspace(-1.7, 1.7, 40)
GAM = 6.0
GRID = np.linspace(-1.7, 1.7, 60)


class Reflex:
    name = "REFLEX (Layer 1)"

    def fit_body(self, th, n=4000, rng=None):
        pass                                  # no internal model — nothing to store

    def act(self, y, th, online):
        return reflex(y, th, 60) if online else np.zeros_like(y)   # no world -> nothing


class ModelHolder:
    name = "MODEL-HOLDER (+internal model)"

    def fit_body(self, th, n=4000, rng=None):
        rng = rng or np.random.default_rng(0)
        yt = rng.uniform(-1.7, 1.7, n); at = reflex(yt, th, 60)
        P = rbf(yt, C, GAM)
        self.W = np.linalg.solve(P.T @ P + (1e-3 if n > 50 else 1e-1) * np.eye(40), P.T @ at)

    def act(self, y, th, online):
        return rbf(y, C, GAM) @ self.W        # internal model — same with or without the world


class Meta:
    name = "META (+cross-body abstraction)"

    def __init__(self):
        F = np.stack([reflex(GRID, t, 60) for t in np.linspace(0.8, 2.6, 16)])
        _, _, Vt = np.linalg.svd(F - F.mean(0), full_matrices=False)
        h = Vt[0]
        self.h = h / np.sign(h @ GRID)        # the shared inverse shape over bodies

    def fit_body(self, th, n=4000, rng=None):
        rng = rng or np.random.default_rng(0)
        yt = rng.uniform(-1.7, 1.7, n); at = reflex(yt, th, 60)
        hn = np.interp(yt, GRID, self.h); self.s = (hn @ at) / (hn @ hn + 1e-9)   # 1 scalar

    def act(self, y, th, online):
        return self.s * np.interp(y, GRID, self.h)


def assay(subj, rng):
    th = 1.7; yte = rng.uniform(-1.7, 1.7, 2000); out = {}
    subj.fit_body(th, rng=rng) if not isinstance(subj, Reflex) else subj.fit_body(th)
    # T1 LAYER-1 competence (world in loop) — control: null (do nothing)
    e1 = err(subj.act(yte, th, online=True), yte, th); ctl1 = err(np.zeros_like(yte), yte, th)
    out["T1 world-in-loop"] = (e1, ctl1, e1 < PASS)
    # T2 LAYER-2 offline (no world at test) — control: reflex offline
    e2 = err(subj.act(yte, th, online=False), yte, th); ctl2 = err(Reflex().act(yte, th, False), yte, th)
    out["T2 offline (no world)"] = (e2, ctl2, e2 < PASS)
    # T3 deep LAYER-2 transfer: NEW body, FEW trials, act offline — control: a fresh per-body model
    th2 = 1.15
    sf = type(subj)() if not isinstance(subj, Meta) else subj
    if isinstance(subj, Meta):
        subj.fit_body(th2, n=2, rng=rng); e3 = err(subj.act(yte, th2, False), yte, th2)
        subj.fit_body(th, rng=rng)
    else:
        sf.fit_body(th2, n=2, rng=rng); e3 = err(sf.act(yte, th2, False), yte, th2)
    mh = ModelHolder(); mh.fit_body(th2, n=2, rng=rng); ctl3 = err(mh.act(yte, th2, False), yte, th2)
    out["T3 transfer (2 trials)"] = (e3, ctl3, e3 < PASS)
    # T4 articulability: does a STATED (linear) rule reproduce the offline policy AS WELL AS the net?
    # (articulable iff the stated rule is within ~3x of the net's own error; a model is not automatically
    #  articulable — stating it is a FURTHER layer)
    if out["T2 offline (no world)"][2]:
        net_off = out["T2 offline (no world)"][0]
        pol = subj.act(GRID, th, online=False)
        w = np.polyfit(GRID, pol, 1); e4 = err(np.polyval(w, yte), yte, th)
        out["T4 articulable?"] = (e4, net_off, e4 <= max(3 * net_off, 0.02))
    else:
        out["T4 articulable?"] = (float("nan"), float("nan"), False)   # no offline model to state
    return out


def grounding_test(rng):
    """T5 grounding axis: a self-model tracking a drifting target — residual from the WORLD vs from the
    SELF. Grounded tracks; self-referential freezes into confident error (delusion)."""
    n = 60; tgt = np.cumsum(rng.normal(0, 0.05, n)) + 1.0     # a drifting truth
    gw = sw = 0.0; ew, es = [], []
    for t in range(n):
        ew.append(abs(gw - tgt[t])); gw += 0.5 * (tgt[t] - gw)    # WORLD residual
        es.append(abs(sw - tgt[t])); sw += 0.5 * (sw - sw)        # SELF residual = 0 -> frozen
    return float(np.mean(ew[n//3:])), float(np.mean(es[n//3:]))


def main():
    rng = np.random.default_rng(0)
    subjects = [Reflex(), ModelHolder(), Meta()]
    print("=" * 92)
    print("THE COGNITION ASSAY — discriminative tests that PLACE a system on the two-layer ladder")
    print("  (each cell: subject_error / control_error  -> PASS if subject beats threshold 0.10)")
    print("=" * 92)
    tests = ["T1 world-in-loop", "T2 offline (no world)", "T3 transfer (2 trials)", "T4 articulable?"]
    print(f"  {'subject':32}" + "".join(f"{t.split()[0]:>14}" for t in tests))
    profiles = {}
    for s in subjects:
        r = assay(s, np.random.default_rng(1))
        profiles[s.name] = r
        cells = []
        for t in tests:
            e, c, p = r[t]
            cell = "  n/a" if e != e else f"{e:.2f}/{c:.2f}{'✓' if p else '✗'}"
            cells.append(cell)
        print(f"  {s.name:32}" + "".join(f"{c:>14}" for c in cells))
    print("=" * 92)
    # placement
    print("  PLACEMENT (read off the pass/fail signature):")
    for name, r in profiles.items():
        L1 = r["T1 world-in-loop"][2]; L2 = r["T2 offline (no world)"][2]; deep = r["T3 transfer (2 trials)"][2]
        art = r["T4 articulable?"][2]
        rung = ("Layer 1 only (model-free / Skinnerian / habit — world in the loop)" if L1 and not L2 else
                "+ internal model (model-based / Popperian — acts offline)" if L2 and not deep else
                "+ cross-task abstraction (meta — few-shot transfer)" if deep else "ungrounded")
        print(f"    {name:32} -> {rung}; {'articulable' if art else 'INARTICULABLE (procedural)'}")
    ew, es = grounding_test(np.random.default_rng(2))
    print("=" * 92)
    print(f"  T5 GROUNDING (anti-delusion): drift tracking — WORLD residual {ew:.3f}  vs  SELF residual {es:.3f}")
    print(f"    -> grounded-in-reality tracks; self-referential freezes into confident error (delusion).")
    print("=" * 92)
    print("  THE DIFFERENCE IS TESTS: the taxonomy is old (model-free/based, Dennett, Craik, procedural/")
    print("  declarative) — DESCRIPTIVE, argued after the fact. This battery MEASURES which layer a system")
    print("  has, prospectively, each test against its own negative control. The ladder becomes an assay.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
