"""RUNG 2 — THE COMMITTED RUNNER for the experience rung's three arms.

*** This is the runner attempt 10 never committed. ***

`VISION_RUNG2_PREREG.md` attempt 10 is the arc's headline (normal 0.402 > dark 0.363 >
sutured 0.216, both p<0.0001) and its verdict is CONJUNCTIVE, so it depends on every
arm — yet it shipped with no runner and no cached stimulus. This file closes that.

THE DESIGN (attempt 10's, unchanged — see the prereg's RE-RUN section):

    phase 1 (1600 steps, ALL arms bit-identical): waves only, Oja eta=5e-4
    phase 2 (400 steps, ALL arms driven, equal duration):
        dark    = waves continue        (dark-reared)
        normal  = real video,  waves cease   (normal rearing)
        sutured = noise,       waves cease   (lid suture)
    statistic = mean anisotropy over the run's 10 units; SEED is the unit of analysis
    d_normal  = anis(normal)  - anis(dark)     two-sided, predicted > 0
    d_sutured = anis(sutured) - anis(dark)     two-sided, predicted < 0
    BUILT iff both pass, Bonferroni alpha=0.025 each.

THE `normal` ARM NOW USES THE REAL SOURCE. Attempt 10 used Sesame Street over
Jellyfin; a reconstruction substituted BSDS300 crops after a FALSE absence claim
(root cause: `catalog()` keys are lowercase `name`, the check read capital `Name`;
`.get` cannot raise, so a stocked 137-item library read as empty). The substitution
was not harmless: BSDS crops are each an independent random crop from a random
photograph -- spatially natural but TEMPORALLY DECORRELATED -- and rung 2 is about
spatioTEMPORAL structure. That arm landed at 0.288, between video and noise, exactly
where a shuffled stream predicts. Frames here come from the committed, content-hashed
cache (`rung2_cache_stimulus.py`), so this runs with no live server.

SEEDS (declared in the prereg BEFORE this ran):
    1900-1999  block A -- EXACT REPRODUCTION on attempt 10's own confirmatory block.
               The only legitimate use of a burned block: reproducing its own numbers.
    9200-9299  block B -- FRESH CONFIRMATION, claimed from the ledger's FREE list.

`dark` and `sutured` use NO video, so they are bit-exact reproductions and act as the
HARNESS FIDELITY CHECK: if they land on 0.363 / 0.216, `normal` is read on a sound
instrument.

Python here is a world adapter: it builds the world, decodes frames, advances the
clock, and reads weights back. Every decision is a seed rule (CLAUDE.md).

    python scripts/rung2_rerun.py            # both blocks
    python scripts/rung2_rerun.py --block A  # one block
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# PROTOCOL §10.1 rule 3: a non-pytest entrypoint must pin its OWN tree's engine.
# This MUST precede any `substrate_rs` import (and any module that does one).
# A bare `sys.path.insert(0, runners/dsl/python)` is NOT enough and is actively
# wrong in a worktree (§10.2, the headless-package trap): the Python package is
# TRACKED but `_native.abi3.so` is GITIGNORED, so the insert pins a package with
# no binary, shadows the `.pth`, and dies with a misleading "circular import".
# `engine_preamble()` symlinks a source-identical build to this tree's own path.
from domains.engine_provenance import engine_preamble, provenance_line  # noqa: E402
engine_preamble()

import numpy as np  # noqa: E402

from scripts.w0_ablation_lib import INITS, H, W, RF, ETA, report, pmap  # noqa: E402
from scripts.rung2_cache_stimulus import load as load_frames, frames_hash  # noqa: E402
from domains.cortex_sheet import orientation_selectivity  # noqa: E402

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.wave_world import WaveWorld  # noqa: E402

PHASE1 = 1600
PHASE2 = 400
N_UNITS = 10
N_SEEDS = 100

BLOCKS = {
    "A": (1900, "EXACT REPRODUCTION -- attempt 10's own block"),
    "B": (9200, "FRESH CONFIRMATION -- claimed from the ledger's FREE list"),
}

_FRAMES = None          # (10 episodes, 600 frames, 16, 16), lazily loaded per process


def video_window(seed: int) -> np.ndarray:
    """PHASE2 CONTIGUOUS frames of real video for this seed. Mechanical I/O.

    Contiguity is the point: it preserves the temporal correlation that IS this
    arm's content (adjacent-frame corr ~0.99), which is exactly what the BSDS
    substitution destroyed. The episode and the start offset vary per seed so that
    seeds stay independent -- "SEED is the unit of analysis" requires it.
    """
    global _FRAMES
    if _FRAMES is None:
        _FRAMES = load_frames()
    n_ep, per_ep = _FRAMES.shape[0], _FRAMES.shape[1]
    rng = np.random.default_rng(seed + 777_777)
    ep = seed % n_ep
    start = int(rng.integers(0, per_ep - PHASE2 + 1))
    return _FRAMES[ep, start:start + PHASE2]


def run_arm(seed: int, arm: str) -> float:
    """One arm, one seed -> mean anisotropy over the run's units."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_waves"])
    wp = s.nodes("WaveParams")[0]
    s.set_attr(wp, "propagate", 1.0)
    s.set_attr(wp, "oja", 1.0)
    s.set_attr(wp, "oja_eta", ETA)
    w = WaveWorld(s, h=H, w=W, seed=seed)
    us = w.add_units(N_UNITS, rf=RF, **INITS["DC"])      # the committed default init

    for i in range(PHASE1):                              # phase 1: waves, all arms
        w.step(ignite_k=1 if i % 5 == 0 else 0)

    if arm == "dark":                                    # waves CONTINUE
        for i in range(PHASE2):
            w.step(ignite_k=1 if i % 5 == 0 else 0)
    else:                                                # waves CEASE
        s.set_attr(wp, "propagate", 0.0)
        rng = np.random.default_rng(seed + 555_555)
        frames = video_window(seed) if arm == "normal" else None
        for i in range(PHASE2):
            f = (frames[i] if arm == "normal"
                 else rng.random((H, W)).astype(np.float32))
            w.step(ignite_k=0, frame=f)

    return float(np.mean([orientation_selectivity(w.receptive_field(u))
                          for u in us]))


def _run(a):
    """Pool entry point: (seed, arm) -> mean anisotropy."""
    return run_arm(a[0], a[1])


def run_block(key: str) -> dict:
    base, label = BLOCKS[key]
    seeds = list(range(base, base + N_SEEDS))
    print(f"\n{'=' * 78}\nBLOCK {key}: seeds {seeds[0]}-{seeds[-1]}  ({label})\n{'=' * 78}")
    arms = {a: np.array(pmap(_run, [(sd, a) for sd in seeds]))
            for a in ("dark", "normal", "sutured")}
    print(f"  arms: dark {arms['dark'].mean():.3f} | "
          f"normal {arms['normal'].mean():.3f} | "
          f"sutured {arms['sutured'].mean():.3f}")
    r = {"d_normal": report("  d_normal  (normal - dark)",
                            arms["normal"] - arms["dark"]),
         "d_sutured": report("  d_sutured (sutured - dark)",
                             arms["sutured"] - arms["dark"])}
    ok = (r["d_normal"]["mean"] > 0 and r["d_normal"]["p"] < 0.025 and
          r["d_sutured"]["mean"] < 0 and r["d_sutured"]["p"] < 0.025)
    print(f"  CONJUNCTIVE GATE: {'PASS -- normal > dark > sutured' if ok else 'FAIL'}")
    return r


if __name__ == "__main__":
    which = sys.argv[sys.argv.index("--block") + 1] if "--block" in sys.argv else "AB"
    print(provenance_line())
    f = load_frames()
    print(f"stimulus: {f.shape} sha256[:16]={frames_hash(f)}  "
          f"(Sesame Street, 10 pinned episodes, start_s=300 every=6 size=16)")
    print(f"design: phase1={PHASE1} waves | phase2={PHASE2} | {N_UNITS} units rf={RF} "
          f"| oja eta={ETA} | n={N_SEEDS}/block")
    print("PRE-REGISTERED: normal 0.402 | dark 0.363 | sutured 0.216 | "
          "d_sutured -0.1474")
    for k in which:
        run_block(k)
