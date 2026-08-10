"""OMNIGLOT RUN 33 -- DYNAMICS: THE THIRD COLUMN.

THE DISCOVERY THIS RUN EXECUTES (creator: "are we missing something simple and stupid like the
conservation of momentum? YES, literally."): the Omniglot motor files are x,y,t (millisecond
timestamps, third column, monotone). `domains/omniglot_world.py`'s `load_points`/`load_strokes`
parse `parts[0], parts[1]` and SILENTLY DROP `parts[2]`. All 32 prior runs of this arc ran on the
static trace with dynamics discarded at the loader. Worse: every downstream resampling step
(`glyph_motor_world.to_trajectory`, `StrokeQuantize`'s `segments`-way equal-arc-length split) is
CONSTANT-SPEED NORMALIZATION -- run 32's own first-class finding ("len = 1/segments EXACTLY,
dimension information-free by construction", commit 13ebc282) is the flattened velocity profile.

THE PHYSICS BEING IMPORTED: velocity minima are physically real segment boundaries (ballistic
submovements; the pen slows at corners; the two-thirds power law, speed ~ curvature^(-1/3)).
Cuts at fixed-count ARC-LENGTH knots are parameterization-dependent (a decoder's existing
candidate set, `ink_decode._knots`); velocity minima are anchored to the writer's own kinematics
instead. `domains/omniglot_world.load_strokes_t` (additive, byte-identical old behaviour) and
`domains/ink_dynamics.py` (velocity-minima knots, the competing arc-length-only corner detector,
the two-thirds-law fit/residual, cross-drawer agreement scoring) are this run's new machinery --
see their own module docstrings for the full architecture note (CLAUDE.md: pure-numpy world-
adapter/feature-extraction code, no agent decisions, no graph).

GATE 0 -- THE CHEAP FALSIFIER (this script's only stage so far; run BEFORE anything expensive):
cross-instance boundary agreement, NO DECODE, NO EVAL. For ~30 characters (3 alphabets x 10
characters, background split), take all 20 drawers' FIRST strokes; compute cut points under
(a) `ink_dynamics.arclength_corner_knots` (geometry-only, no time -- the competing "physically
arbitrary" baseline) and (b) `ink_dynamics.velocity_minima_knots` (the physical-boundary
hypothesis); measure cross-drawer agreement of interior cut positions in NORMALIZED arc length
(`ink_dynamics.mean_pairwise_agreement`, symmetric nearest-neighbour match within a documented
8%-of-arc-length tolerance band, endpoints excluded as trivially shared by both arms).
PRE-REGISTERED: velocity-minima agreement must EXCEED arc-length agreement -- falsifiable in
seconds. If it fails, mechanism A (segmentation via velocity minima) is STOPPED and this is
reported as the finding; the premise is wrong on this data.

MID-RUN CORRECTION (found by this run's OWN robustness check, before any verdict was reported --
the honest-anomaly discipline this arc's whole commit log enforces): the RAW agreement score
above is CONFOUNDED by candidate COUNT -- velocity-minima proposes ~4x more knots per stroke
than the arc-length detector at their respective default thresholds (~12 vs ~3), and a denser
point set scores a higher nearest-neighbour match rate PURELY BY CHANCE (Monte Carlo check:
uniform-random knots at ~3/stroke already score ~0.40 raw agreement; at ~12/stroke, ~0.86 --
BOTH before any physical alignment is considered). Comparing the two arms' RAW scores directly
therefore tests candidate density, not the physical-boundary hypothesis. THE FIX:
`ink_dynamics.count_matched_null_agreement` computes each arm's own COUNT-MATCHED chance floor
(same per-drawer knot counts, uniform-random positions, Monte Carlo replicates); `excess = raw -
null` is the fair, count-normalized statistic. THE PRE-REGISTERED VERDICT IS RESTATED (before
the corrected numbers were computed) on EXCESS, not raw score: velocity-minima's excess-over-
its-own-chance-floor must EXCEED arc-length's excess-over-its-own-chance-floor. Both the raw
(confounded) and corrected (excess) numbers are reported for full transparency. Also reports the
two-thirds-law fit quality PER WRITER (`ink_dynamics.pooled_two_thirds_fit`, pooled over each
writer's own first strokes across the sampled characters) -- the r^2 DISTRIBUTION across
writers, honestly, even if poor.

Gate 1 (the full protocol -- LEARN/CFAR/codebook arms, P1-P6) is NOT built by this script; it is
licensed only if Gate 0 confirms, per the run-33 brief's staging ("run the cheap falsifier
first"). See the run-33 session's final report for exact resume state.

Run (system python3 -- no substrate/graph involved, pure numpy over real Omniglot files on
disk):
  PYTHONPATH=.:runners/dsl/python python3 \\
      scripts/jabberwock_omniglot_run33_dynamics.py --stage falsifier
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

from domains import ink_dynamics as idyn
from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run33_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)

SPLIT = "background"
N_ALPHABETS = 3
N_CHARS_PER_ALPHABET = 10
MIN_FIRST_STROKE_SAMPLES = 4     # need >=3 interior points for a turning angle / curvature look.
AGREEMENT_TOL = idyn.DEFAULT_AGREEMENT_TOL


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _select_characters():
    alphabets = ow.alphabets(SPLIT)[:N_ALPHABETS]
    char_dirs = []
    for a in alphabets:
        char_dirs.extend(ow.characters(a, SPLIT)[:N_CHARS_PER_ALPHABET])
    return alphabets, char_dirs


def _percentiles(values: list) -> dict:
    if not values:
        return dict(n=0)
    arr = np.asarray(values, dtype=float)
    return dict(n=int(arr.size), mean=float(arr.mean()), median=float(np.median(arr)),
                p25=float(np.percentile(arr, 25)), p75=float(np.percentile(arr, 75)),
                min=float(arr.min()), max=float(arr.max()))


def stage_falsifier():
    print(f"\n{SEP}\n  STAGE: falsifier (GATE 0 -- cross-drawer boundary agreement, no decode, "
          f"no eval)\n{SEP}")
    t0 = time.time()
    alphabets, char_dirs = _select_characters()
    print(f"  split={SPLIT}  alphabets={alphabets}")
    print(f"  characters sampled: {len(char_dirs)} ({N_CHARS_PER_ALPHABET}/alphabet)  "
          f"agreement_tol={AGREEMENT_TOL} (normalized arc length)")

    per_char_detail = []
    per_char_arclen_scores, per_char_vel_scores = [], []
    per_char_arclen_null, per_char_vel_null = [], []
    per_char_arclen_excess, per_char_vel_excess = [], []
    per_char_arclen_avg_n, per_char_vel_avg_n = [], []
    n_files_seen = 0
    n_first_strokes_used = 0
    n_first_strokes_too_short = 0
    n_files_with_no_strokes = 0
    n_fallback_first_stroke = 0
    writer_first_strokes: dict[str, list] = {}
    null_rng = np.random.default_rng(1234)          # ONE rng, reused across all null draws
    N_NULL_REPS = 60                                 # Monte Carlo reps for the count-matched null

    for cdir in char_dirs:
        files = ow.drawings(cdir)
        arclen_sets, vel_sets = [], []
        for f in files:
            n_files_seen += 1
            drawer = f.split("/")[-1].split("_")[-1].replace(".txt", "")
            strokes_xyt, fallback_flags = ow.load_strokes_t(f)
            if not strokes_xyt:
                n_files_with_no_strokes += 1
                continue
            st0 = strokes_xyt[0]
            if fallback_flags[0]:
                n_fallback_first_stroke += 1
            if st0.shape[0] < MIN_FIRST_STROKE_SAMPLES:
                n_first_strokes_too_short += 1
                continue
            n_first_strokes_used += 1
            arclen_sets.append(idyn.arclength_corner_knots(st0[:, :2]))
            vel_sets.append(idyn.velocity_minima_knots(st0))
            writer_first_strokes.setdefault(drawer, []).append(st0)

        if len(arclen_sets) >= 2:
            rep_a = idyn.mean_pairwise_agreement(arclen_sets, tol=AGREEMENT_TOL)
            rep_v = idyn.mean_pairwise_agreement(vel_sets, tol=AGREEMENT_TOL)
            null_a = idyn.count_matched_null_agreement(arclen_sets, tol=AGREEMENT_TOL,
                                                        n_reps=N_NULL_REPS, rng=null_rng)
            null_v = idyn.count_matched_null_agreement(vel_sets, tol=AGREEMENT_TOL,
                                                        n_reps=N_NULL_REPS, rng=null_rng)
            excess_a = (rep_a["mean"] - null_a) if (rep_a["mean"] is not None and null_a is not None) else None
            excess_v = (rep_v["mean"] - null_v) if (rep_v["mean"] is not None and null_v is not None) else None
            avg_n_a = float(np.mean([idyn._interior(k).size for k in arclen_sets]))
            avg_n_v = float(np.mean([idyn._interior(k).size for k in vel_sets]))
            per_char_detail.append(dict(
                char=os.path.relpath(cdir, ow.split_dir(SPLIT)), n_drawers=len(arclen_sets),
                arclen_mean=rep_a["mean"], arclen_pairs=rep_a["n_pairs"], arclen_null=null_a,
                arclen_excess=excess_a, arclen_avg_n_interior=avg_n_a,
                vel_mean=rep_v["mean"], vel_pairs=rep_v["n_pairs"], vel_null=null_v,
                vel_excess=excess_v, vel_avg_n_interior=avg_n_v))
            if rep_a["mean"] is not None:
                per_char_arclen_scores.append(rep_a["mean"])
                per_char_arclen_avg_n.append(avg_n_a)
            if rep_v["mean"] is not None:
                per_char_vel_scores.append(rep_v["mean"])
                per_char_vel_avg_n.append(avg_n_v)
            if null_a is not None:
                per_char_arclen_null.append(null_a)
            if null_v is not None:
                per_char_vel_null.append(null_v)
            if excess_a is not None:
                per_char_arclen_excess.append(excess_a)
            if excess_v is not None:
                per_char_vel_excess.append(excess_v)

    grand_arclen = float(np.mean(per_char_arclen_scores)) if per_char_arclen_scores else None
    grand_vel = float(np.mean(per_char_vel_scores)) if per_char_vel_scores else None
    grand_arclen_null = float(np.mean(per_char_arclen_null)) if per_char_arclen_null else None
    grand_vel_null = float(np.mean(per_char_vel_null)) if per_char_vel_null else None
    grand_arclen_excess = float(np.mean(per_char_arclen_excess)) if per_char_arclen_excess else None
    grand_vel_excess = float(np.mean(per_char_vel_excess)) if per_char_vel_excess else None
    raw_hypothesis_confirmed = bool(grand_arclen is not None and grand_vel is not None
                                    and grand_vel > grand_arclen)
    hypothesis_confirmed = bool(grand_arclen_excess is not None and grand_vel_excess is not None
                                and grand_vel_excess > grand_arclen_excess)

    print(f"\n  files seen: {n_files_seen}  (no-strokes: {n_files_with_no_strokes}, "
          f"first-stroke-too-short: {n_first_strokes_too_short}, "
          f"first-strokes-used: {n_first_strokes_used})")
    fallback_rate = n_fallback_first_stroke / n_files_seen if n_files_seen else 0.0
    print(f"  FALLBACK RATE (first stroke lacked usable monotone time): "
          f"{n_fallback_first_stroke}/{n_files_seen} = {fallback_rate:.4f} "
          f"{'-- DATA-QUALITY WALL (>5%)' if fallback_rate > 0.05 else '-- OK (<=5%)'}")

    print(f"\n  characters scored (>=2 drawers with a usable first stroke): {len(per_char_detail)}")
    print(f"  avg interior candidate count/stroke:  ARC-LENGTH={np.mean(per_char_arclen_avg_n):.2f}  "
          f"VELOCITY-MINIMA={np.mean(per_char_vel_avg_n):.2f}  <- the density confound this run's "
          f"own robustness check found")
    print(f"\n  RAW (CONFOUNDED BY DENSITY -- reported for transparency, NOT the verdict) mean "
          f"cross-drawer agreement:")
    print(f"    ARC-LENGTH (geometry-only, no time):  {grand_arclen}")
    print(f"    VELOCITY-MINIMA (physical boundary):  {grand_vel}")
    print(f"    raw comparison alone would say: "
          f"{'CONFIRMED' if raw_hypothesis_confirmed else 'FALSIFIED'} (velocity {'>' if raw_hypothesis_confirmed else '<='} arc-length) "
          f"-- KNOWN TO BE MISLEADING, see count-matched null below")
    print(f"\n  COUNT-MATCHED NULL (chance floor at each arm's own candidate density, "
          f"{N_NULL_REPS} MC reps/character):")
    print(f"    ARC-LENGTH null:  {grand_arclen_null}")
    print(f"    VELOCITY-MINIMA null:  {grand_vel_null}")
    print(f"\n  EXCESS = raw - null (the CORRECTED, count-normalized statistic):")
    print(f"    ARC-LENGTH excess:      {grand_arclen_excess}")
    print(f"    VELOCITY-MINIMA excess: {grand_vel_excess}")
    print(f"\n  *** GATE 0 PRE-REGISTERED VERDICT (restated on EXCESS, the count-corrected "
          f"statistic, before these numbers were computed): velocity-minima's excess-over-its-"
          f"own-chance-floor must EXCEED arc-length's ***")
    print(f"  *** {'CONFIRMED' if hypothesis_confirmed else 'FALSIFIED -- STOP mechanism A, report the premise is wrong on this data'} ***")

    # -----------------------------------------------------------------------------------
    # Two-thirds law fit quality, per writer (pooled over that writer's own sampled first
    # strokes) -- reported honestly regardless of the Gate-0 verdict above.
    # -----------------------------------------------------------------------------------
    writer_fits = {}
    for d, strokes in writer_first_strokes.items():
        fit = idyn.pooled_two_thirds_fit(strokes)
        if fit is not None:
            writer_fits[d] = fit
    r2_values = [f["r2"] for f in writer_fits.values()]
    slope_values = [f["slope"] for f in writer_fits.values()]
    r2_report = _percentiles(r2_values)
    slope_report = _percentiles(slope_values)
    print(f"\n  TWO-THIRDS LAW fit quality, PER WRITER ({len(writer_fits)} writers with enough "
          f"pooled data):")
    print(f"    r^2 distribution:    {r2_report}")
    print(f"    slope distribution:  {slope_report}  (law predicts slope ~= -0.333)")
    law_holds = bool(r2_report.get("n", 0) > 0 and r2_report.get("median", 0.0) >= 0.3)
    print(f"    two-thirds law holds on this data (median r^2 >= 0.3): "
          f"{'YES' if law_holds else 'NO -- reported honestly, not assumed'}")

    result = dict(
        alphabets=alphabets, n_characters_sampled=len(char_dirs),
        n_characters_scored=len(per_char_detail),
        agreement_tol=AGREEMENT_TOL,
        n_files_seen=n_files_seen, n_files_with_no_strokes=n_files_with_no_strokes,
        n_first_strokes_too_short=n_first_strokes_too_short,
        n_first_strokes_used=n_first_strokes_used,
        n_fallback_first_stroke=n_fallback_first_stroke, fallback_rate=fallback_rate,
        avg_n_interior_arclen=float(np.mean(per_char_arclen_avg_n)) if per_char_arclen_avg_n else None,
        avg_n_interior_velocity=float(np.mean(per_char_vel_avg_n)) if per_char_vel_avg_n else None,
        grand_mean_arclen_agreement_RAW=grand_arclen, grand_mean_velocity_agreement_RAW=grand_vel,
        grand_mean_arclen_null=grand_arclen_null, grand_mean_velocity_null=grand_vel_null,
        grand_mean_arclen_excess=grand_arclen_excess, grand_mean_velocity_excess=grand_vel_excess,
        raw_hypothesis_confirmed_MISLEADING=raw_hypothesis_confirmed,
        hypothesis_confirmed=hypothesis_confirmed,
        n_null_reps_per_character=N_NULL_REPS,
        per_char_detail=per_char_detail,
        two_thirds_r2_distribution=r2_report, two_thirds_slope_distribution=slope_report,
        two_thirds_law_holds_median_r2_ge_0_3=law_holds,
        per_writer_two_thirds_fit={d: f for d, f in writer_fits.items()},
        wall_clock_seconds=time.time() - t0,
    )
    out_path = _ckpt("gate0_falsifier.json")
    _save_json(result, out_path)
    print(f"\n  saved -> {out_path}")
    print(f"  wall clock: {result['wall_clock_seconds']:.2f}s")
    return 0 if hypothesis_confirmed else 2


STAGES = {"falsifier": stage_falsifier}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=sorted(STAGES.keys()))
    args = p.parse_args()
    sys.exit(STAGES[args.stage]())


if __name__ == "__main__":
    main()
