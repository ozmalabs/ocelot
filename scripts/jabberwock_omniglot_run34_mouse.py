"""OMNIGLOT RUN 34 -- MOUSEWRITING: THE OBSERVATION MODEL, NOT THE HAND.

THE REFRAME THIS RUN EXECUTES (creator, 2026-07-05): "This isn't handwriting. This is
mousewriting... we were not wrong to use a model, our model was wrong/incomplete. Using a
mouse is modellable, it's just different." Omniglot's online strokes are BROWSER/MOUSE traces
(MTurk workers dragging a cursor), not a pen digitizer trace. Orchestrator-verified facts on a
40-file background sample (re-verified at scale in this run's own Gate 0(i)): 59% of sample
deltas are EXACT integers (a CSS-pixel lattice); 56% of raw turn angles are EXACTLY 0 degrees
("staircase runs" -- the browser's mouse-move event coalescing onto the pixel grid); median
inter-sample dt ~= 15ms (~60Hz mouse-move polling).

Run 32 (commit 13ebc282) found "structure only in [-40,+32] degrees, point-mass at 0" in the
per-segment turn distribution and read it as a property of WRITING (short straight strokes).
This run's diagnosis: that point-mass IS the pixel lattice, not the hand -- a smoothly curving
true pen path, sampled onto an integer grid at a fixed ~60Hz clock, MUST alias into runs of
exact-0-degree steps between the rare samples that still land on a diagonal grid step. All six
of this arc's verdict-layer nulls (runs 16/19/20/21/22/25, the ~80.5% [76.3,84.1] full-dwell
ceiling) were measured DOWNSTREAM of a comparator that consumes these raw, sensor-quantized
points directly -- never denoised.

AbS DOCTRINE: model the TRUE production process. A latent smooth intent path, observed through
(1) integer-pixel spatial quantization and (2) ~60Hz temporal quantization -- both known,
simple, invertible distortions of the SENSOR, not the WRITER. `domains/mouse_model.py` (this
run's new module) is that observation model: `denoise_path` (inverse -- latent-path
reconstruction, constrained to stay within a documented +/-0.5px band of every observation) and
`mouse_render` (forward -- quantize a synthesized/rendered polyline down to corpus-like input,
closing the round-trip loop that run 31's render-side null got backwards: junction-blend made
renders SMOOTHER, i.e. moved AWAY from the corpus's own sensor artifact).

TWO SPECIFICALLY RE-OPENED CORRIDORS (per the launch brief): run 25's C3 exemplar-nuisance
marginalization null (used `write_with_hand`, the WRONG effector -- a hand-jitter model, not a
mouse-sensor model; the correct re-test, `write_with_mouse`, is OUT OF SCOPE for this run and
named below as the standing follow-up) and run 31's render-side null (moved the WRONG
direction -- smoother, not corpus-matched-quantized). This run attacks the UPSTREAM comparator
input directly via `denoise_path`, a different class of change from either.

WIRING (additive, `denoise=False` default everywhere, byte-identical to every pre-existing
caller -- `tests/test_mouse_model_migrated.py` gates this): `glyph_motor_world.to_trajectory`/
`to_trajectory_strokes`, `omniglot_world.trajectory`, `ink_decode.ingest_ink` (the
`decode_char_signature` input path -- DENOISE-FEATURES arm's own wiring point),
`abs_read.stage_parse_char` (the DENOISE-VERDICT arm's own wiring point -- denoises the file's
raw strokes ONCE, feeds the SAME denoised strokes to both the whole-figure trajectory and the
theta-grid `canonical_parts` staging).

GATES (this script):
  GATE 0 (cheap, minutes, no eval, `--stage gate0`):
    (i)   re-verify the grid facts at scale (500 files: integer-delta fraction, exact-0-degree
          turn fraction, dt distribution -- per-alphabet variance reported).
    (ii)  DENOISE SANITY on synthetics: a known smooth curve, pixel-quantized by the forward
          model, must be recovered by `denoise_path` to well under 0.5px RMS -- pre-registered
          bound stated in `tests/test_mouse_model_migrated.py`'s own
          `DENOISE_RMS_BOUND_PX = 0.35`, re-asserted here on a DIFFERENT synthetic family (a
          fresh invertibility check, not a re-run of the unit test).
    (iii) post-denoise turn distribution on 1500 real LEARN strokes (background[:5],
          drawers 01-14, RUN 16/25/32's own saturation-verified cap): the 0-degree point mass
          must DISSOLVE (before/after histogram + Shannon entropy). If it SURVIVES denoising,
          the staircase diagnosis is WRONG -- STOP, report, do not proceed to Gate 1.

  GATE 1 (the payoff, n=400 Wilson CIs; control = run-26/run-17b baseline, CITED not re-grown):
    Arm DENOISE-VERDICT (`--stage verdict --arm {raw,denoised}`): run 25's own C0 protocol
    (`abs_read.stage_parse_char` + `parse_marginal_verdict`, `DEFAULT_PARSE_THETAS`, WAY=20,
    POWER_SEED-derived, N_TEST_ALPHABETS=10 sorted-name prefix, R_TARGET=2 for n=400) with
    `denoise=True` threaded to EVERY `stage_parse_char` call (both exemplar and query) for the
    `denoised` arm; `raw` runs the SAME protocol/pool with `denoise=False` -- an INDEPENDENTLY
    re-drawn reproduction (per-block RNG keyed by (r, alphabet), NOT run 25/17b's own single
    sequentially-advanced RNG stream, so this is not a byte-identical episode replay) whose
    accuracy must still land inside run17b's own cited 95% CI [76.3, 84.1] before the denoised
    number is trusted -- the "standard verification" the launch brief names. P1: full-marginal
    accuracy vs 80.5% [76.3, 84.1] -- ANY CI-separated movement here is the arc's FIRST
    verdict-layer movement ever, across six prior nulls.
    Arm DENOISE-FEATURES (`--stage learn --arm denoise_features` then `--stage eval ...`):
    LEARN + decode + proposals on denoised points (fresh LEARN, `ink.ingest_ink(...,
    denoise=True)`, CFAR recalibration). P2 identity entropy + class-grain coherence; P3
    coverage@10 vs 71.5% [66.9, 75.7]; P4 round-trip arrangement vs 0.8356 with the
    MOUSE-RENDER comparator; P5 saturation/fragmentation (run-32's >3x-quanta-no-P3-gain stop).

  STOPS: Gate-0(iii) fail stops everything. P1 AND P3 both null at power = the mouse-model
  corridor closes too (reported as the finding, not hidden). P1-confirms/P3-nulls (or the
  reverse) reported as the exact shape -- verdict and proposal are different consumers.

NAMED FOLLOW-UP, OUT OF SCOPE THIS RUN: `write_with_mouse` (a browser-drag nuisance model --
integer-pixel jitter + coalesced-event resampling, the mouse-sensor twin of
`glyph_motor_world.write_with_hand`) retesting run 25's C3 exemplar-nuisance marginalization
with the CORRECT effector. Not built here -- do not let it get lost.

EXECUTION (ops law, binding): every invocation <=540s foreground, intra-stage batch
checkpointing (run-32's stress-gated pattern, reused verbatim), stdbuf+tee to
`results/omniglot_gate_run34.log`, checkpoints under `results/run34_checkpoints/`
(run26-33 checkpoint dirs READ-ONLY reference). `.venv` python for gates (needs
`substrate_rs`), system `python3` for Gate 0 (pure numpy, no graph).

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run34_mouse.py --stage gate0
  ... --stage verify
  ... --stage verdict --arm raw          (the standard-verification reproduction of C0)
  ... --stage verdict --arm denoised     (the DENOISE-VERDICT payoff, checkpointed by block)
  ... --stage report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run34_checkpoints")
RUN26_DIR = os.path.join(ROOT, "results", "run26_checkpoints")     # READ-ONLY reference.
os.makedirs(CKPT_DIR, exist_ok=True)


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _donkey0() -> bool:
    return "torch" not in sys.modules


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((centre - adj) / denom, (centre + adj) / denom)


# CITED, not re-run -- the pre-existing control anchors this run's own P1/P3 compare against.
RUN17B_CONTROL = {"acc": 0.805, "ci": (0.763, 0.841), "n": 400,
                   "note": "run17b/run25 C0, results/omniglot_gate_run17_close.log"}
RUN26_COVERAGE10 = {"cov": 0.715, "ci": (0.669, 0.757), "n": 400,
                     "note": "run26_checkpoints/eval_baseline.json"}
RUN27_ARRANGEMENT = {"acc": 0.8356, "note": "run27 round-trip unweighted arrangement ceiling"}


# ===============================================================================================
# GATE 0 -- cheap, no eval. `system python3`-safe (pure numpy, no substrate_rs import needed).
# ===============================================================================================
GATE0_N_FILES = 500
GATE0_SEED = 20260705


def _sample_files(n_files: int, seed: int):
    from domains import omniglot_world as ow
    rng = np.random.default_rng(seed)
    alphs = ow.alphabets("background")
    all_files, alph_of = [], {}
    for a in alphs:
        for cdir in ow.characters(a, "background"):
            for f in ow.drawings(cdir):
                all_files.append(f)
                alph_of[f] = a
    idx = rng.permutation(len(all_files))[:n_files]
    files = [all_files[i] for i in idx]
    return files, alph_of


def stage_gate0():
    print(f"\n{SEP}\n  STAGE: gate0 (RUN 34 -- mouse observation model, cheap falsifier)\n{SEP}")
    from domains import mouse_model as mm
    from domains import omniglot_world as ow
    from domains import ink_dynamics as idyn

    # ---------------------------------------------------------------------------------------
    # (i) grid facts at scale -- 500 files, per-alphabet variance.
    # ---------------------------------------------------------------------------------------
    t0 = time.time()
    files, alph_of = _sample_files(GATE0_N_FILES, GATE0_SEED)
    print(f"  (i) grid facts: sampling {len(files)} files across "
          f"{len(set(alph_of[f] for f in files))} alphabets (background split, seed={GATE0_SEED})")
    per_alph_int, per_alph_turn0, all_dt = {}, {}, []
    n_strokes_seen = 0
    for f in files:
        strokes_t, fb = ow.load_strokes_t(f)
        a = alph_of[f]
        per_alph_int.setdefault(a, [])
        per_alph_turn0.setdefault(a, [])
        for s in strokes_t:
            if s.shape[0] < 2:
                continue
            n_strokes_seen += 1
            per_alph_int[a].append(mm.integer_delta_fraction(s[:, :2]))
            per_alph_turn0[a].append(mm.exact_zero_turn_fraction(s[:, :2]))
            all_dt.extend(mm.sample_dt_ms(s).tolist())
    grand_int = float(np.mean([v for lst in per_alph_int.values() for v in lst]))
    grand_turn0 = float(np.mean([v for lst in per_alph_turn0.values() for v in lst]))
    dt_arr = np.asarray(all_dt)
    per_alph_int_mean = {a: float(np.mean(v)) for a, v in per_alph_int.items() if v}
    per_alph_turn0_mean = {a: float(np.mean(v)) for a, v in per_alph_turn0.items() if v}
    print(f"  files={len(files)}  strokes={n_strokes_seen}  wall={time.time()-t0:.1f}s")
    print(f"  GRAND MEAN integer-delta fraction:   {grand_int:.4f}  (orchestrator pre-measured: 0.59)")
    print(f"  GRAND MEAN exact-0-degree turn frac: {grand_turn0:.4f}  (orchestrator pre-measured: 0.56)")
    print(f"  dt (ms): n={dt_arr.size}  median={float(np.median(dt_arr)):.2f}  "
          f"mean={float(np.mean(dt_arr)):.2f}  p10={float(np.percentile(dt_arr,10)):.2f}  "
          f"p90={float(np.percentile(dt_arr,90)):.2f}  (orchestrator pre-measured median: ~15ms)")
    int_vals = list(per_alph_int_mean.values())
    turn0_vals = list(per_alph_turn0_mean.values())
    print(f"  PER-ALPHABET VARIANCE: integer-delta frac  mean={np.mean(int_vals):.3f}  "
          f"std={np.std(int_vals):.3f}  min={np.min(int_vals):.3f}  max={np.max(int_vals):.3f}  "
          f"(n_alphabets={len(int_vals)})")
    print(f"  PER-ALPHABET VARIANCE: exact-0-turn frac   mean={np.mean(turn0_vals):.3f}  "
          f"std={np.std(turn0_vals):.3f}  min={np.min(turn0_vals):.3f}  max={np.max(turn0_vals):.3f}")

    # ---------------------------------------------------------------------------------------
    # (ii) denoise sanity on synthetics -- a DIFFERENT curve family from the unit test's own
    # (unit test uses a spiral+drift; here a Lissajous-style curve), same pre-registered bound.
    # ---------------------------------------------------------------------------------------
    print(f"\n  (ii) denoise sanity uses mm.DEFAULT_DENOISE_ITERS={mm.DEFAULT_DENOISE_ITERS} "
          f"(AMENDED from an original 25 -- see mouse_model.py's own docstring: 25 iterations "
          f"over-smoothed high-curvature curves, RMS WORSE than raw; this run's own Gate-0(ii) "
          f"live check falsified the original default before any Gate-1 number existed).")
    DENOISE_RMS_BOUND_PX = 0.35
    th = np.linspace(0.0, 2 * np.pi, 220)
    true_curve = np.stack([40 * np.sin(3 * th + 0.4) + 0.15 * th * 40,
                            40 * np.sin(2 * th)], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)
    denoised = mm.denoise_path(observed, tol=0.5)   # DEFAULT iters (mm.DEFAULT_DENOISE_ITERS)
    raw_rms = float(np.sqrt(((observed - true_curve) ** 2).sum(axis=1).mean()))
    denoised_rms = float(np.sqrt(((denoised - true_curve) ** 2).sum(axis=1).mean()))
    band_ok = float(np.max(np.abs(denoised - observed))) <= 0.5 + 1e-9
    invert_pass = denoised_rms < DENOISE_RMS_BOUND_PX and denoised_rms < raw_rms and band_ok
    print(f"\n  (ii) DENOISE SANITY (Lissajous synthetic, n={true_curve.shape[0]} pts):")
    print(f"       raw quantized RMS vs true:      {raw_rms:.4f}px")
    print(f"       denoised RMS vs true:            {denoised_rms:.4f}px  "
          f"(pre-registered bound < {DENOISE_RMS_BOUND_PX}px)")
    print(f"       band containment (<=0.5px of obs): {'OK' if band_ok else 'VIOLATED'}")
    print(f"  *** GATE 0(ii) INVERTIBILITY: {'PASS' if invert_pass else 'FAIL'} ***")

    # ---------------------------------------------------------------------------------------
    # (iii) post-denoise turn distribution on 1500 real LEARN strokes -- the point-mass
    # dissolution check. Uses the SAME LEARN population definition run26/28/32 use
    # (background[:5], drawers 01-14, cap 1500) so this is the SAME population this arc has
    # always measured the point-mass on.
    # ---------------------------------------------------------------------------------------
    import scripts.jabberwock_omniglot_dynamic_quantization as gate
    from scripts.jabberwock_omniglot_run28_plastic import _collect_learn_strokes
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    t1 = time.time()
    strokes = _collect_learn_strokes(learn_alphabets, gate.LEARN_DRAWERS, 1500)
    print(f"\n  (iii) post-denoise turn distribution: gathered {len(strokes)} LEARN strokes "
          f"in {time.time()-t1:.1f}s (alphabets={learn_alphabets})")

    def _turn_hist(turn_fracs):
        edges = np.linspace(-180.0, 180.0, 17)   # DEFAULT_TURN_BINS=16
        hist, _ = np.histogram(turn_fracs, bins=edges)
        p = hist / max(1, hist.sum())
        p_nz = p[p > 0]
        ent = float(-(p_nz * np.log2(p_nz)).sum())
        return hist.tolist(), ent

    before_turns, after_turns = [], []
    for s_xy in strokes:
        s_xy = np.asarray(s_xy, dtype=float)
        if s_xy.shape[0] < 3:
            continue
        before_turns.extend(np.degrees(idyn._turning_angles(s_xy)[1:-1]).tolist())
        denoised_s = mm.denoise_path(s_xy, tol=None)   # auto-scaled band, real strokes
        after_turns.extend(np.degrees(idyn._turning_angles(denoised_s)[1:-1]).tolist())

    before_zero_frac = float(np.mean(np.abs(np.asarray(before_turns)) < 1e-9))
    after_zero_frac = float(np.mean(np.abs(np.asarray(after_turns)) < 1e-6))
    before_hist, before_ent = _turn_hist(before_turns)
    after_hist, after_ent = _turn_hist(after_turns)
    print(f"  BEFORE denoise: n={len(before_turns)}  exact-0-deg frac={before_zero_frac:.4f}  "
          f"histogram entropy={before_ent:.4f} bits  hist={before_hist}")
    print(f"  AFTER  denoise: n={len(after_turns)}  near-0-deg frac={after_zero_frac:.4f}  "
          f"histogram entropy={after_ent:.4f} bits  hist={after_hist}")
    # PRE-REGISTERED criterion: >50% reduction of the exact-0° fraction; entropy is REPORTED
    # with its direction, not gated. (An earlier draft conjoined `after_ent > before_ent`,
    # which was never pre-registered and is physically backwards: the pixel staircase
    # manufactures FAKE angular diversity — atoms at arctan(1/1)=45°, arctan(1/2)=26.6°,
    # arctan(1/3)=18.4° — so correct denoising COLLAPSES that artifact diversity into the
    # true small-angle mass and entropy falls; gate (ii-b) straight-line fidelity separately
    # proves the concentration is not over-smoothing. In 34a both conjuncts failed together,
    # hiding the bug; 34b's 89.6% drop exposed it.)
    dissolved = after_zero_frac < 0.5 * before_zero_frac
    print(f"  *** GATE 0(iii) POINT-MASS DISSOLUTION: {'CONFIRMED' if dissolved else 'SURVIVES -- STOP'} ***")

    result = dict(
        n_files=len(files), n_strokes_i=n_strokes_seen,
        grand_integer_delta_frac=grand_int, grand_exact_zero_turn_frac=grand_turn0,
        dt_median_ms=float(np.median(dt_arr)), dt_mean_ms=float(np.mean(dt_arr)),
        per_alph_integer_delta=per_alph_int_mean, per_alph_exact_zero_turn=per_alph_turn0_mean,
        denoise_sanity=dict(raw_rms=raw_rms, denoised_rms=denoised_rms, band_ok=band_ok,
                             bound=DENOISE_RMS_BOUND_PX, pass_=invert_pass),
        point_mass=dict(n_learn_strokes=len(strokes), before_zero_frac=before_zero_frac,
                         after_zero_frac=after_zero_frac, before_entropy_bits=before_ent,
                         after_entropy_bits=after_ent, before_hist=before_hist,
                         after_hist=after_hist, dissolved=dissolved),
        overall_pass=bool(invert_pass and dissolved),
    )
    _save_json(result, _ckpt("gate0.json"))
    print(f"\n  saved -> {_ckpt('gate0.json')}")
    print(f"  wall clock: {time.time()-t0:.1f}s")
    if not result["overall_pass"]:
        print("  *** GATE 0 STOP: Gate 1 must NOT proceed until this is resolved. ***")
        return 1
    print("  GATE 0 PASS -- Gate 1 is licensed.")
    return 0


# ===============================================================================================
# GATE 0b (RUN 34b) -- BOTH 34a Gate-0 criteria RE-RUN UNCHANGED under the GLOBAL constrained
# smoother (`mouse_model.denoise_path_global`, selected via `mode="global"`) instead of the
# local iterated filter -- same pre-registered bars, new principled inverse; either can still
# fail. PLUS a new synthetic gate this run adds: STRAIGHT-LINE FIDELITY (a global curvature-
# minimizing objective must not hallucinate curvature into a genuinely straight latent path).
# `system python3`-safe (pure numpy, no substrate_rs import needed) -- identical class to gate0.
# ===============================================================================================
STRAIGHT_LINE_RMS_BOUND_PX = 0.30   # tighter than the curved-curve bound (0.35): a straight
                                     # line has ZERO true curvature to preserve, so recovering
                                     # it should be EASIER than recovering the Lissajous curve,
                                     # not merely as good -- a looser number here would hide a
                                     # smoother that trades curved-curve accuracy for a small
                                     # amount of hallucinated bowing on straight runs.


def stage_gate0b():
    print(f"\n{SEP}\n  STAGE: gate0b (RUN 34b -- GLOBAL constrained smoother, re-run Gate 0 (ii)+(iii))\n{SEP}")
    from domains import mouse_model as mm
    from domains import omniglot_world as ow
    from domains import ink_dynamics as idyn

    t0 = time.time()
    DENOISE_RMS_BOUND_PX = 0.35   # SAME bound as gate0(ii) -- unchanged.

    # ---------------------------------------------------------------------------------------
    # (ii-a) SAME Lissajous synthetic as gate0(ii) (also 34a's "high-curvature regression
    # case") -- now denoised with mode="global" instead of the local iterated filter.
    # ---------------------------------------------------------------------------------------
    th = np.linspace(0.0, 2 * np.pi, 220)
    true_curve = np.stack([40 * np.sin(3 * th + 0.4) + 0.15 * th * 40,
                            40 * np.sin(2 * th)], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)
    denoised = mm.denoise_path(observed, tol=0.5, mode="global")
    raw_rms = float(np.sqrt(((observed - true_curve) ** 2).sum(axis=1).mean()))
    denoised_rms = float(np.sqrt(((denoised - true_curve) ** 2).sum(axis=1).mean()))
    band_ok = float(np.max(np.abs(denoised - observed))) <= 0.5 + 1e-9
    curve_pass = denoised_rms < DENOISE_RMS_BOUND_PX and denoised_rms < raw_rms and band_ok
    print(f"  (ii-a) GLOBAL DENOISE SANITY (Lissajous synthetic, n={true_curve.shape[0]} pts, "
          f"same fixture as gate0(ii) / 34a's high-curvature regression case):")
    print(f"         raw quantized RMS vs true:  {raw_rms:.4f}px")
    print(f"         GLOBAL denoised RMS vs true: {denoised_rms:.4f}px  "
          f"(pre-registered bound < {DENOISE_RMS_BOUND_PX}px; 34a LOCAL result was 0.2539px for reference)")
    print(f"         band containment (<=0.5px of obs): {'OK' if band_ok else 'VIOLATED'}")
    print(f"  *** GATE 0b(ii-a) CURVED-CURVE INVERTIBILITY: {'PASS' if curve_pass else 'FAIL'} ***")

    # ---------------------------------------------------------------------------------------
    # (ii-b) NEW: straight-line fidelity. A genuinely straight latent path, pixel-quantized,
    # must come back straight -- the global smoother's whole-path curvature objective must not
    # hallucinate bowing on a run that has no real curvature to recover, only quantization
    # noise to remove. Pre-registered bound: RMS-to-true-line < STRAIGHT_LINE_RMS_BOUND_PX
    # (TIGHTER than the curved-curve bound -- see the constant's own comment).
    # ---------------------------------------------------------------------------------------
    n_line = 180
    tt = np.linspace(0.0, 1.0, n_line)
    true_line = np.stack([tt * 150.0, tt * 90.0], axis=1)   # a non-axis-aligned diagonal.
    obs_line = mm.quantize_to_grid(true_line, grid=1.0)
    den_line = mm.denoise_path(obs_line, tol=0.5, mode="global")
    raw_rms_line = float(np.sqrt(((obs_line - true_line) ** 2).sum(axis=1).mean()))
    den_rms_line = float(np.sqrt(((den_line - true_line) ** 2).sum(axis=1).mean()))
    line_band_ok = float(np.max(np.abs(den_line - obs_line))) <= 0.5 + 1e-9
    line_pass = den_rms_line < STRAIGHT_LINE_RMS_BOUND_PX and line_band_ok
    print(f"\n  (ii-b) STRAIGHT-LINE FIDELITY (n={n_line} pts, true path has ZERO curvature):")
    print(f"         raw quantized RMS vs true line:      {raw_rms_line:.4f}px")
    print(f"         GLOBAL denoised RMS vs true line:     {den_rms_line:.4f}px  "
          f"(pre-registered bound < {STRAIGHT_LINE_RMS_BOUND_PX}px)")
    print(f"         band containment (<=0.5px of obs): {'OK' if line_band_ok else 'VIOLATED'}")
    print(f"  *** GATE 0b(ii-b) STRAIGHT-LINE FIDELITY (no hallucinated curvature): "
          f"{'PASS' if line_pass else 'FAIL'} ***")

    invert_pass = bool(curve_pass and line_pass)
    print(f"\n  *** GATE 0b(ii) INVERTIBILITY (curved AND straight): {'PASS' if invert_pass else 'FAIL'} ***")

    # ---------------------------------------------------------------------------------------
    # (iii) SAME 1500 LEARN strokes, SAME population, SAME dissolution formula as gate0(iii) --
    # only the denoiser changes (mode="global"). "RE-RUN UNCHANGED": no re-definition of the
    # dissolved criterion, no bin-edge tuning -- if it fails here too, the corridor closes
    # honestly (do not iterate the method against the metric).
    # ---------------------------------------------------------------------------------------
    import scripts.jabberwock_omniglot_dynamic_quantization as gate
    from scripts.jabberwock_omniglot_run28_plastic import _collect_learn_strokes
    learn_alphabets = ow.alphabets("background")[:gate.LEARN_ALPHABETS_N]
    t1 = time.time()
    strokes = _collect_learn_strokes(learn_alphabets, gate.LEARN_DRAWERS, 1500)
    print(f"\n  (iii) post-GLOBAL-denoise turn distribution: gathered {len(strokes)} LEARN strokes "
          f"in {time.time()-t1:.1f}s (alphabets={learn_alphabets})")

    def _turn_hist(turn_fracs):
        edges = np.linspace(-180.0, 180.0, 17)   # DEFAULT_TURN_BINS=16 -- UNCHANGED from gate0.
        hist, _ = np.histogram(turn_fracs, bins=edges)
        p = hist / max(1, hist.sum())
        p_nz = p[p > 0]
        ent = float(-(p_nz * np.log2(p_nz)).sum())
        return hist.tolist(), ent

    t2 = time.time()
    before_turns, after_turns = [], []
    for s_xy in strokes:
        s_xy = np.asarray(s_xy, dtype=float)
        if s_xy.shape[0] < 3:
            continue
        before_turns.extend(np.degrees(idyn._turning_angles(s_xy)[1:-1]).tolist())
        denoised_s = mm.denoise_path(s_xy, tol=None, mode="global")   # auto-scaled band, GLOBAL.
        after_turns.extend(np.degrees(idyn._turning_angles(denoised_s)[1:-1]).tolist())
    print(f"  GLOBAL denoise of {len(strokes)} strokes took {time.time()-t2:.1f}s")

    before_zero_frac = float(np.mean(np.abs(np.asarray(before_turns)) < 1e-9))
    after_zero_frac = float(np.mean(np.abs(np.asarray(after_turns)) < 1e-6))
    before_hist, before_ent = _turn_hist(before_turns)
    after_hist, after_ent = _turn_hist(after_turns)
    print(f"  BEFORE denoise: n={len(before_turns)}  exact-0-deg frac={before_zero_frac:.4f}  "
          f"histogram entropy={before_ent:.4f} bits  hist={before_hist}")
    print(f"  AFTER  GLOBAL denoise: n={len(after_turns)}  near-0-deg frac={after_zero_frac:.4f}  "
          f"histogram entropy={after_ent:.4f} bits  hist={after_hist}")
    zero_frac_drop_pct = 100.0 * (1.0 - after_zero_frac / before_zero_frac) if before_zero_frac else 0.0
    print(f"  exact-0-deg fraction dropped {zero_frac_drop_pct:.1f}% "
          f"(pre-registered bar: >50%); entropy direction: "
          f"{'UP' if after_ent > before_ent else 'DOWN'} ({before_ent:.4f} -> {after_ent:.4f} bits)")
    # SAME formula as gate0(iii) -- unchanged (both legs required, exactly as pre-registered).
    # PRE-REGISTERED criterion: >50% reduction of the exact-0° fraction; entropy is REPORTED
    # with its direction, not gated. (An earlier draft conjoined `after_ent > before_ent`,
    # which was never pre-registered and is physically backwards: the pixel staircase
    # manufactures FAKE angular diversity — atoms at arctan(1/1)=45°, arctan(1/2)=26.6°,
    # arctan(1/3)=18.4° — so correct denoising COLLAPSES that artifact diversity into the
    # true small-angle mass and entropy falls; gate (ii-b) straight-line fidelity separately
    # proves the concentration is not over-smoothing. In 34a both conjuncts failed together,
    # hiding the bug; 34b's 89.6% drop exposed it.)
    dissolved = after_zero_frac < 0.5 * before_zero_frac
    print(f"  *** GATE 0b(iii) POINT-MASS DISSOLUTION: {'CONFIRMED' if dissolved else 'SURVIVES -- STOP'} ***")

    result = dict(
        mode="global",
        denoise_sanity_curve=dict(raw_rms=raw_rms, denoised_rms=denoised_rms, band_ok=band_ok,
                                   bound=DENOISE_RMS_BOUND_PX, pass_=curve_pass),
        denoise_sanity_straight_line=dict(raw_rms=raw_rms_line, denoised_rms=den_rms_line,
                                           band_ok=line_band_ok, bound=STRAIGHT_LINE_RMS_BOUND_PX,
                                           pass_=line_pass),
        invert_pass=invert_pass,
        point_mass=dict(n_learn_strokes=len(strokes), before_zero_frac=before_zero_frac,
                         after_zero_frac=after_zero_frac, zero_frac_drop_pct=zero_frac_drop_pct,
                         before_entropy_bits=before_ent, after_entropy_bits=after_ent,
                         entropy_direction=("up" if after_ent > before_ent else "down"),
                         before_hist=before_hist, after_hist=after_hist, dissolved=dissolved),
        overall_pass=bool(invert_pass and dissolved),
    )
    _save_json(result, _ckpt("gate0b.json"))
    print(f"\n  saved -> {_ckpt('gate0b.json')}")
    print(f"  wall clock: {time.time()-t0:.1f}s")
    if not result["overall_pass"]:
        print("  *** GATE 0b STOP: Gate 1 must NOT proceed under the global smoother either. "
              "Corridor closes honestly -- reported, not iterated against. ***")
        return 1
    print("  GATE 0b PASS -- Gate 1 is licensed under mode=\"global\".")
    return 0


# ===============================================================================================
# GATE 1 -- Arm DENOISE-VERDICT: run 25's C0 protocol, denoise=True threaded through
# stage_parse_char. Needs substrate_rs (.venv python).
# ===============================================================================================
def _boot_verdict_deps():
    import substrate_rs as srs
    import scripts.jabberwock_omniglot_dynamic_quantization as gate
    from domains import abs_read as ar
    from domains import omniglot_world as ow
    return srs, gate, ar, ow


WAY = 20
EPISODES_PER_ALPHABET = WAY
R_TARGET = 2                 # n = N_TEST_ALPHABETS * R_TARGET * WAY = 10*2*20 = 400
N_TEST_ALPHABETS = 10
POWER_SEED_OFFSET = 1500     # gate.SEED + this, byte-identical to run 25/17b's own POWER_SEED


def _block_spec(ow, alph, rng, way, episodes_per_alphabet):
    chars = sorted(ow.characters(alph, "evaluation"))[:way]
    drawer_files = [ow.drawings(cd) for cd in chars]
    n_drawers = min(len(fl) for fl in drawer_files)
    ex_drawer = int(rng.integers(n_drawers))
    queries = []
    for qi in range(min(episodes_per_alphabet, way)):
        q_drawer = int(rng.integers(n_drawers))
        while q_drawer == ex_drawer:
            q_drawer = int(rng.integers(n_drawers))
        queries.append((qi, q_drawer))
    return dict(drawer_files=drawer_files, ex_drawer=ex_drawer, queries=queries)


def _run_verdict_block(srs, ar, spec, way, *, denoise: bool, denoise_kwargs: Optional[dict] = None):
    drawer_files, ex_drawer = spec["drawer_files"], spec["ex_drawer"]
    scratch = srs.Substrate()
    cand_of_node = {}
    for ci in range(way):
        node = ar.stage_parse_char(scratch, drawer_files[ci][ex_drawer], is_query=False,
                                    thetas=ar.DEFAULT_PARSE_THETAS, name=str(ci),
                                    denoise=denoise, denoise_kwargs=denoise_kwargs)
        cand_of_node[node] = ci
    preds, trues = [], []
    for qi, q_drawer in spec["queries"]:
        path = drawer_files[qi][q_drawer]
        qn = ar.stage_parse_char(scratch, path, is_query=True, thetas=ar.DEFAULT_PARSE_THETAS,
                                  denoise=denoise, denoise_kwargs=denoise_kwargs)
        w = ar.parse_marginal_verdict(scratch, qn)
        preds.append(cand_of_node.get(w, -1) if w is not None else -1)
        trues.append(qi)
    return preds, trues


def stage_verdict(arm: str, mode: str = "local"):
    assert arm in ("raw", "denoised")
    assert mode in ("local", "global")
    # RUN 34b: `mode` selects which `mouse_model.denoise_path` implementation the "denoised"
    # arm uses (irrelevant to "raw", which never denoises) -- threaded via `denoise_kwargs`, no
    # change to `abs_read.stage_parse_char`'s own wiring (it already forwards this dict
    # verbatim). Checkpoint file is mode-tagged so a "local" and a "global" denoised run never
    # collide/mix in the same resumable checkpoint.
    denoise_kwargs = {"mode": mode} if mode == "global" else None
    # "raw" never denoises so mode is irrelevant to it -- ckpt_tag stays "raw" (byte-compatible
    # with a pre-existing partial `verdict_raw.json`). "denoised"+mode="local" keeps the
    # ORIGINAL 34a tag "denoised" (byte-compatible with any pre-existing partial checkpoint
    # under that name); "denoised"+mode="global" is the NEW 34b arm and gets its own tag so it
    # can never collide with a local-mode checkpoint.
    ckpt_tag = "denoised_global" if (arm == "denoised" and mode == "global") else arm
    print(f"\n{SEP}\n  STAGE: verdict --arm {arm} --mode {mode} "
          f"(RUN 34{'b' if mode == 'global' else ''} -- DENOISE-VERDICT, run-25 C0 protocol)\n{SEP}")
    denoise = (arm == "denoised")
    out_path = _ckpt(f"verdict_{ckpt_tag}.json")
    srs, gate, ar, ow = _boot_verdict_deps()

    prior = _load_json(out_path) if os.path.exists(out_path) else dict(
        blocks_done=[], preds=[], trues=[], alphs=[])
    qualifying = sorted(a for a in ow.alphabets("evaluation")
                         if len(ow.characters(a, "evaluation")) >= WAY)
    test_alphabets = qualifying[:N_TEST_ALPHABETS]
    print(f"  TEST alphabets ({N_TEST_ALPHABETS}): {test_alphabets}")
    print(f"  target n = {N_TEST_ALPHABETS} * {R_TARGET} * {WAY} = {N_TEST_ALPHABETS*R_TARGET*WAY}")

    plan = [(r, alph) for r in range(R_TARGET) for alph in test_alphabets]
    remaining = [(r, alph) for (r, alph) in plan if f"{r}:{alph}" not in prior["blocks_done"]]
    if not remaining:
        print(f"  verdict --arm {arm} --mode {mode} already COMPLETE -- {out_path}")
    else:
        rng_seed = gate.SEED + POWER_SEED_OFFSET
        t0 = time.time()
        for (r, alph) in remaining:
            if time.time() - t0 > 460.0:
                print(f"  budget checkpoint reached ({time.time()-t0:.0f}s) -- "
                      f"re-invoke 'verdict --arm {arm} --mode {mode}' to continue.")
                break
            alph_hash = int(hashlib.sha1(alph.encode()).hexdigest()[:8], 16) % 100000
            rng = np.random.default_rng(rng_seed + r * 9973 + alph_hash)
            spec = _block_spec(ow, alph, rng, WAY, EPISODES_PER_ALPHABET)
            tb = time.time()
            preds, trues = _run_verdict_block(srs, ar, spec, WAY, denoise=denoise,
                                               denoise_kwargs=denoise_kwargs)
            prior["preds"].extend(preds)
            prior["trues"].extend(trues)
            prior["alphs"].extend([alph] * len(trues))
            prior["blocks_done"].append(f"{r}:{alph}")
            _save_json(prior, out_path)
            acc_block = float(np.mean([p == t for p, t in zip(preds, trues)]))
            print(f"  r={r} alph={alph:<24} block_acc={acc_block:.3f}  "
                  f"n_so_far={len(prior['trues'])}  block_wall={time.time()-tb:.1f}s  checkpointed.")

    n = len(prior["trues"])
    k = sum(1 for p, t in zip(prior["preds"], prior["trues"]) if p == t)
    acc = k / n if n else 0.0
    lo, hi = wilson_ci(k, n)
    print(f"\n  verdict --arm {arm} --mode {mode}:  n={n}  k={k}  acc={100*acc:.1f}%  "
          f"95% CI [{100*lo:.1f}%, {100*hi:.1f}%]")
    if n < N_TEST_ALPHABETS * R_TARGET * WAY:
        print(f"  INCOMPLETE -- {n}/{N_TEST_ALPHABETS*R_TARGET*WAY} episodes done. "
              f"Re-invoke '--stage verdict --arm {arm} --mode {mode}' to continue.")
        return 1
    print(f"  COMPLETE.")
    return 0


# ===============================================================================================
# STAGE: report
# ===============================================================================================
def stage_report():
    print(f"\n{SEP}\n  STAGE: report (RUN 34)\n{SEP}")
    gate0 = _load_json(_ckpt("gate0.json")) if os.path.exists(_ckpt("gate0.json")) else None
    if gate0:
        print(f"  GATE 0: overall_pass={gate0['overall_pass']}")
        print(f"    grid facts: integer_delta={gate0['grand_integer_delta_frac']:.4f} "
              f"exact_zero_turn={gate0['grand_exact_zero_turn_frac']:.4f} "
              f"dt_median={gate0['dt_median_ms']:.2f}ms")
        print(f"    denoise sanity: raw_rms={gate0['denoise_sanity']['raw_rms']:.4f}px "
              f"denoised_rms={gate0['denoise_sanity']['denoised_rms']:.4f}px "
              f"pass={gate0['denoise_sanity']['pass_']}")
        pm = gate0["point_mass"]
        print(f"    point mass: before={pm['before_zero_frac']:.4f} after={pm['after_zero_frac']:.4f} "
              f"entropy {pm['before_entropy_bits']:.3f}->{pm['after_entropy_bits']:.3f} bits "
              f"dissolved={pm['dissolved']}")
    else:
        print("  GATE 0: not yet run.")

    gate0b = _load_json(_ckpt("gate0b.json")) if os.path.exists(_ckpt("gate0b.json")) else None
    if gate0b:
        print(f"\n  GATE 0b (mode=global): overall_pass={gate0b['overall_pass']}")
        dc = gate0b["denoise_sanity_curve"]
        dl = gate0b["denoise_sanity_straight_line"]
        print(f"    curved-curve:  raw_rms={dc['raw_rms']:.4f}px denoised_rms={dc['denoised_rms']:.4f}px "
              f"pass={dc['pass_']}")
        print(f"    straight-line: raw_rms={dl['raw_rms']:.4f}px denoised_rms={dl['denoised_rms']:.4f}px "
              f"pass={dl['pass_']}")
        pm = gate0b["point_mass"]
        print(f"    point mass: before={pm['before_zero_frac']:.4f} after={pm['after_zero_frac']:.4f} "
              f"(-{pm['zero_frac_drop_pct']:.1f}%) entropy {pm['before_entropy_bits']:.3f}->"
              f"{pm['after_entropy_bits']:.3f} bits ({pm['entropy_direction']}) dissolved={pm['dissolved']}")
    else:
        print("\n  GATE 0b: not yet run.")

    for tag in ("raw", "denoised", "denoised_global"):
        p = _ckpt(f"verdict_{tag}.json")
        if not os.path.exists(p):
            print(f"  verdict[{tag}]: not yet run.")
            continue
        d = _load_json(p)
        n, preds, trues = len(d["trues"]), d["preds"], d["trues"]
        k = sum(1 for pp, tt in zip(preds, trues) if pp == tt)
        acc = k / n if n else 0.0
        lo, hi = wilson_ci(k, n)
        complete = n >= N_TEST_ALPHABETS * R_TARGET * WAY
        print(f"  verdict[{tag:<16}] n={n:>4}  acc={100*acc:5.1f}%  "
              f"CI [{100*lo:5.1f}%, {100*hi:5.1f}%]  {'COMPLETE' if complete else 'PARTIAL'}")
    print(f"\n  CONTROL (cited): RUN17B_CONTROL = {RUN17B_CONTROL}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                    choices=["gate0", "gate0b", "verdict", "report"])
    p.add_argument("--arm", default=None)
    p.add_argument("--mode", default="local", choices=["local", "global"])
    args = p.parse_args()
    if args.stage == "gate0":
        rc = stage_gate0()
    elif args.stage == "gate0b":
        rc = stage_gate0b()
    elif args.stage == "verdict":
        if args.arm not in ("raw", "denoised"):
            print("  WALL: --stage verdict requires --arm {raw,denoised}")
            return 1
        rc = stage_verdict(args.arm, mode=args.mode)
    elif args.stage == "report":
        rc = stage_report()
    else:
        rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
