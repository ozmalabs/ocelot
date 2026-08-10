"""PART 5 — RUNG 2's THREE ARMS, RE-MEASURED BOTH WAYS.

*** THIS IS A RECONSTRUCTION, NOT A REPRODUCTION. Read this before quoting any
number out of it. ***

`VISION_RUNG2_PREREG.md` attempt 10 (the BUILT result: normal 0.402 > dark 0.363 >
sutured 0.216) has **no committed runner**. This script rebuilds the design from
the pre-registration's prose:

    phase 1 (1600 steps, all arms bit-identical): waves only, Oja eta=5e-4
    phase 2 (400 steps, all arms driven, equal duration):
        dark    = waves continue
        normal  = real video, waves cease
        sutured = noise,      waves cease
    statistic = mean anisotropy over the run's 10 units; SEED is the unit of analysis

TWO DEPARTURES I COULD NOT AVOID, BOTH STATED RATHER THAN PAPERED OVER:

 1. **The `normal` arm's video source is GONE.**

    *** RETRACTED 2026-07-17 — THIS IS FALSE. The source was never gone. ***
    `catalog()` returns dicts keyed lowercase `name`; the absence check read
    capital `Name`. `.get('Name','')` returns '' and CANNOT raise, so all 137
    items silently missed and a STOCKED library read as empty: Sesame Street is
    Series a6152b4a3b12f70779d1cb6364fa97e6, 78 episodes. An absence claim off a
    soft accessor is evidence of a LOOKUP, not of ABSENCE (PROTOCOL §12).
    Rung 2 now has a runner + a pinned cache: see `scripts/rung2_rerun.py`,
    `scripts/rung2_cache_stimulus.py`, and VISION_RUNG2_PREREG.md's RE-RUN
    section. The re-run's verdict: `dark`/`sutured` reproduce exactly, `normal`
    reaches only 0.317 on the REAL source (still below `dark`) — so this file's
    refusal to score 0.288 as a refutation was RIGHT, but temporal decorrelation
    was worth only ~+0.03; the stimulus CONSTRUCTION (whole-frame downsample vs
    native-res crop, anisotropy 0.21 vs 0.58) is the larger cause.

    Attempt 10 used Sesame Street over Jellyfin. This arm uses **BSDS300
    natural-image crops** area-downsampled to 16x16 — real natural images with
    real oriented structure, which is the property the pre-registration's H1a
    actually rested on ("natural video's leading principal component is MORE
    anisotropic than the waves'"). It is a DIFFERENT source.
 2. Unit count / RF centres are read from the prereg's prose ("that run's 10
    units"), not from code that no longer exists.

**So the DC arm here is a FIDELITY CHECK on the reconstruction, not a
reproduction of the committed numbers.** If DC lands near 0.402/0.363/0.216 the
reconstruction is faithful and the DC-vs-ZERO comparison means something. If it
does not, that is reported, and the arm comparison is read as internal to this
script only. Either way the ablation itself is sound: DC and ZERO run through
IDENTICAL code and identical input, differing only in `add_units(init=)`.
"""
from __future__ import annotations

import numpy as np

from scripts.w0_ablation_lib import (INITS, H, W, RF, ETA, report, pmap,
                                     boot_ci, sign_flip_p)
from domains.cortex_sheet import orientation_selectivity
from domains.engine_provenance import provenance_line

import domains.seed_registry  # noqa: F401
from substrate.boot_core import boot_core, load_seeds_into
from domains.wave_world import WaveWorld

PHASE1 = 1600
PHASE2 = 400
N_UNITS = 10
N_SEEDS = 100
SEEDS = list(range(1900, 1900 + N_SEEDS))     # attempt 10's OWN seeds (reproduction)


def _video_frames(n: int, seed: int) -> np.ndarray:
    """The `normal` arm's input: real natural images, 16x16. Mechanical I/O."""
    from domains.vision_corpus import bsds_crops, area_downsample
    crops = bsds_crops(n=n, seed=seed)
    if len(crops) == 0:
        raise SystemExit("BSDS300 not available — the normal arm cannot run.")
    return np.stack([area_downsample(c, H) for c in crops])


def run_arm(seed: int, init: str, arm: str) -> float:
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", ETA)
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = w.add_units(N_UNITS, rf=RF, **INITS[init])

    for i in range(PHASE1):                                  # phase 1: waves
        w.step(ignite_k=1 if i % 5 == 0 else 0)

    if arm == "dark":                                        # waves CONTINUE
        for i in range(PHASE2):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
    else:                                                    # waves CEASE
        s.set_attr(wp, "propagate", 0.0)
        rng = np.random.default_rng(seed + 555_555)
        frames = _video_frames(PHASE2, seed) if arm == "normal" else None
        for i in range(PHASE2):
            f = (frames[i] if arm == "normal"
                 else rng.random((H, W)).astype(np.float32))
            w.step(ignite_k=0, frame=f)
    return float(np.mean([orientation_selectivity(w.receptive_field(u))
                          for u in us]))


def _run(a):
    """Pool entry point: (seed, init, arm) -> mean anisotropy."""
    return run_arm(a[0], a[1], a[2])


if __name__ == "__main__":
    print(provenance_line())
    print("=" * 78)
    print("PART 5 — RUNG 2 THREE ARMS, BOTH INITS.  *** RECONSTRUCTION ***")
    print(f"phase1={PHASE1} waves | phase2={PHASE2} | n={N_SEEDS} seeds "
          f"{SEEDS[0]}-{SEEDS[-1]} (attempt 10's own; a reproduction, not fresh)")
    print("normal arm = BSDS300 natural crops. NOTE: 'the Sesame Street source is "
          "gone' is RETRACTED (a capital-`Name` read error) — the real source is "
          "cached at tests/fixtures/vision_rung2/; see scripts/rung2_rerun.py")
    print("=" * 78)
    out = {}
    for init in INITS:
        arms = {a: np.array(pmap(_run, [(sd, init, a) for sd in SEEDS]))
                for a in ("dark", "normal", "sutured")}
        out[init] = arms
        print(f"\n--- {init}")
        print(f"  arms: dark {arms['dark'].mean():.3f} | "
              f"normal {arms['normal'].mean():.3f} | "
              f"sutured {arms['sutured'].mean():.3f}")
        report("  d_normal  (normal - dark)", arms["normal"] - arms["dark"])
        report("  d_sutured (sutured - dark)", arms["sutured"] - arms["dark"])

    print("\n" + "=" * 78)
    print("THE ABLATION: does the init move the arm the rung reported?")
    print("=" * 78)
    for a in ("dark", "normal", "sutured"):
        for init in ("ZERO", "ZEROM"):
            report(f"{a:8s} {init:5s} - DC", out[init][a] - out["DC"][a])
