"""RUNG 6 — POSITIVE CONTROL (PROTOCOL 1): is the learning rule a NULL INSTRUMENT?

Rung 3's eta was a null instrument and ONLY its positive control revealed it.
Rung 5 ran its positive control, watched it fail, and correctly burned NO seeds.

THE QUESTION, asked separately from any hypothesis: given a PERFECTLY BIASED
input ensemble — a single orientation, shown over and over — can the rule grow an
orientation-selective cell AT ALL?

This is the sharpest possible version of the test, because of the correction in
VISION_PRIOR_ART.md: "the average has no direction" is imprecise; the real
argument is ENSEMBLE DEGENERACY, and ON A BIASED ENSEMBLE, OJA WORKS. So a
single-orientation ensemble is exactly the condition under which the rule MUST
succeed if it is capable at all. If it cannot learn orientation when the input
has only ONE orientation, no wave arm can rescue it.

This is a POSITIVE CONTROL, NOT AN ARM: the stimulus is hand-built and is exactly
the structure the paradigm rule forbids handing the agent. It answers "is the
rule a null instrument?" and nothing else. Seeds 0-2, already burned.
"""
from __future__ import annotations

import numpy as np

from scripts.rung6_lib import build, osi_of, adapt_theta, PERIOD, RF, H, W
from domains.onoff_world import set_params, signed_rf, segregation, weights
from domains.complex_cells import grating, binarize, present


def train_on_orientation(world, theta_deg, steps, *, seed=0, period=PERIOD):
    """Show ONE orientation at random phases. Mechanical ingest — `present`
    is rung 5's, unchanged."""
    rng = np.random.default_rng(seed)
    for _ in range(steps):
        ph = float(rng.uniform(0, 2 * np.pi))
        present(world, binarize(grating((world.h, world.w), theta_deg, ph, period)))


def line(k, v):
    print(f"  {k:<50s} {v}")


print("=" * 78)
print("RUNG 6 POSITIVE CONTROL — a PERFECTLY BIASED ensemble (one orientation)")
print("=" * 78)

for subnorm in (1.0, 0.0):
    tag = "MILLER subtractive" if subnorm else "plain OJA"
    print(f"\n--- rule = {tag} (subnorm={subnorm}) ---")
    for eta in (5e-4, 1e-4):
        w, us, _ = build(seed=0, n_units=6, subnorm=subnorm, eta=eta)
        adapt_theta(w, 400)                      # threshold settles first
        set_params(w, oo_eta=eta, frozen=0.0)
        train_on_orientation(w, 0.0, 1500, seed=0)   # <- ONLY 0 degrees, ever
        o, st = osi_of(w, us)
        pk = st["tuning"].max(axis=1)
        bs = np.maximum(st["baseline"], 1e-9)
        prefs = [float(np.argmax(st["tuning"][i])) for i in range(len(us))]
        segs = [segregation(w, u)["clumpiness"] for u in us]
        line(f"eta={eta:g}  mean OSI", f"{o.mean():.4f}  max {o.max():.4f}")
        line("     peak/baseline (responsiveness)", f"{(pk/bs).mean():.2f}")
        line("     pref-orientation bin (0 == 0 deg)", f"{prefs}")
        line("     ON/OFF clumpiness (0.5 = intermixed)", f"{np.mean(segs):.3f}")

print("""
READ: the ensemble contains ONE orientation. A capable rule must (a) raise OSI
well above the 0.3168 untrained floor, (b) make the cells RESPONSIVE (peak >>
baseline, the ideal scores 6.44), and (c) prefer the orientation it was actually
shown. Failing (a) or (b) means the rule is a null instrument and NO confirmatory
arm may be run (PROTOCOL 2, applied one layer up — rung 5's call).
""")
