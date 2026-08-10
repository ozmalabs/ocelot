"""THE VACUITY AUDIT — can the pre-visual double dissociation FAIL?

*Run BEFORE `VISION_PREVISUAL_PREREG.md`'s confirmatory run, and it decides
whether that run happens at all.*

H3, the discriminating test, is a DOUBLE DISSOCIATION:

    (a) waves move the photometric gain by ~0, diffuse light MOVES it
    (b) waves MOVE the relational measures, diffuse light moves them by ~0

`VISION_EYE_PREREG.md`'s Amendment 1 already says (a)'s first half is
STRUCTURAL — "the photometric rules read `EyeCell.lum`; waves live on
`RetinaCell.bursting`; NO EDGE JOINS THEM" — and gates it (waves move theta by
exactly 0.0). The task's instruction is explicit: do not "confirm" a structural
fact by construction; say which half is structural and which is measured; and
**if everything is structural, the test is vacuous — report that instead of a
pass**.

So this audit asks the only question that matters: **is the OTHER half
structural too?** It answers it two ways, because a code reading is an opinion
and a measurement is not:

  1. STATIC — the rule/edge audit. Which rules read which attributes, and is
     there ANY path by which light reaches the relational population?
  2. DYNAMIC — the four cells of the dissociation, MEASURED. Each of the four
     is run and its effect reported, so a claimed zero is an observed zero.

An effect that is zero because no edge exists is not a finding. It is the
architecture restating itself.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402
from domains.eye_world import (EyeWorld, PreVisualWorld, lid_diffuse,  # noqa: E402
                               set_params)
from domains.engine_provenance import provenance_line  # noqa: E402

H = W = 16
PHOTOMETRIC = ("lum", "resp", "theta", "xbar")
RELATIONAL = ("bursting",)


def static_audit() -> dict:
    """WHICH RULES READ WHAT. A rule is on the photometric path if it reads a
    photometric attr, on the relational path if it reads `bursting`. A rule that
    reads BOTH is the only thing that could COUPLE them."""
    d = json.load(open(os.path.join(ROOT, "seeds", "vision_eye.json")))
    both, photo, rel = [], [], []
    for r in d["rules"]:
        s = json.dumps(r)
        p = any(f'"{k}"' in s for k in PHOTOMETRIC)
        b = any(f'"{k}"' in s for k in RELATIONAL)
        (both if (p and b) else photo if p else rel if b else []).append(r["name"])
    return {"coupling_rules": both, "photometric": photo, "relational": rel}


def _eye_theta(w, ey) -> float:
    return float(np.mean([w.s.node(c)["attrs"]["theta"] for c in ey.cells.values()]))


def _wunit_weights(w, pv) -> np.ndarray:
    return np.array([float(w.s.node(s)["attrs"]["weight"])
                     for s in pv.syn.values()])


def build(seed: int):
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves", "vision_eye"])
    s.set_attr(s.nodes("WaveParams")[0], "propagate", 1.0)
    s.set_attr(s.nodes("WaveParams")[0], "oja", 1.0)
    s.set_attr(s.nodes("WaveParams")[0], "oja_eta", 0.0)
    ww = WaveWorld(s, h=H, w=W, seed=seed)
    ey = EyeWorld(s, h=H, w=W, seed=seed)
    pv = PreVisualWorld(ww, n_units=4, seed=seed)
    # `eye=0` IS THE MASTER DEFAULT-OFF (PROTOCOL 9) and `phase0=0` gates the
    # relational rules. Both MUST be switched on, or every arm is INERT and the
    # audit reports a beautiful all-zero "dissociation" that is really a dead
    # instrument. This is exactly the failure the eye's own positive controls
    # caught three times; my first run of this script hit it (all four cells
    # 0.000000, including the one that MUST move) and the positive control below
    # is what makes that impossible to report as a result.
    set_params(ey, eye=1.0, phase0=1.0, saw=0.0)
    return s, ww, ey, pv


def cell(seed: int, *, waves: bool, light: bool, steps: int = 400):
    """One cell of the dissociation: run with waves on/off and diffuse light
    on/off, and report how far BOTH read-outs moved."""
    s, ww, ey, pv = build(seed)
    th0 = _eye_theta(ww, ey)
    w0 = _wunit_weights(ww, pv)
    rng = np.random.default_rng(seed + 31)
    scene = rng.random((H, W)).astype(np.float32)
    lit = lid_diffuse(scene) if light else None
    for i in range(steps):
        # The EYE's clock always advances, so the photometric read-out gets the
        # same number of ticks in every arm — an unfired clock starving one arm
        # is exactly the bug the eye's own positive control caught (§2.1).
        ey.step(frame=lit)
        if waves:
            pv.step(ignite_k=1 if i % 5 == 0 else 0)
    return {"dtheta": abs(_eye_theta(ww, ey) - th0),
            "dw_rel": float(np.linalg.norm(_wunit_weights(ww, pv) - w0))}


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 78)
    print("VACUITY AUDIT — can H3's double dissociation FAIL?")
    print("=" * 78)

    a = static_audit()
    print("\n1. STATIC — which rules read which path")
    print(f"   photometric-only rules : {len(a['photometric'])}")
    print(f"   relational-only rules  : {len(a['relational'])}")
    print(f"   COUPLING rules (read BOTH): {len(a['coupling_rules'])}  "
          f"{a['coupling_rules']}")

    print("\n2. POSITIVE CONTROL — the instrument must be ALIVE first.")
    print("   Diffuse light MUST move theta. If it does not, every zero below is")
    print("   a dead instrument, not a dissociation. (My first run of this")
    print("   script scored 0.000000 in ALL FOUR cells: `eye=0` is the master")
    print("   default-off and I had not set it. The audit was measuring nothing.)")
    pc = [cell(s_, waves=False, light=True) for s_ in range(3)]
    live = float(np.mean([r["dtheta"] for r in pc]))
    print(f"   diffuse light -> |d theta| = {live:.6f}   "
          f"{'ALIVE' if live > 1e-6 else '*** DEAD — DO NOT READ THE TABLE ***'}")
    assert live > 1e-6, ("the photometric path is INERT; the audit cannot "
                         "distinguish 'no edge' from 'no instrument'")

    print("\n3. DYNAMIC — the four cells, MEASURED (n=3 burned seeds, 400 steps)")
    print(f"{'arm':28s} {'|d theta| (photometric)':>24s} "
          f"{'|dw| (relational)':>20s}")
    for label, kw in (("waves only", dict(waves=True, light=False)),
                      ("diffuse light only", dict(waves=False, light=True)),
                      ("both", dict(waves=True, light=True)),
                      ("neither (null control)", dict(waves=False, light=False))):
        rs = [cell(s, **kw) for s in range(3)]
        print(f"{label:28s} {np.mean([r['dtheta'] for r in rs]):24.6f} "
              f"{np.mean([r['dw_rel'] for r in rs]):20.6f}")
