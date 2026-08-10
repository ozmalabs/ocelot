"""jabberwock_motorplan_run72.py -- RUN 72: THE MOTOR-PLANNING WRITER (CURSIVE_PLAN.md fork A,
the creator's directive: replace the DISCRETIZED shape-codebook writer with a CONTINUOUS
sigma-lognormal / virtual-target KINEMATIC generator, through the substrate's motor-planning
faculty, and re-test run 71's separation falsifier).

THE PROBLEM THIS RUN ANSWERS (run 71, 34a67b81): motor-simulation AbS reading floored below the
static writer-relative-pose recognizer because our GENERATOR was too lossy to discriminate real
ink -- StrokeQuantize/StrokeRender is a DISCRETIZED shape codebook (SEG=12 arc-length segments x
TURN_BINS=16 turn bins x LEN_BINS=8 length bins): self-consistent (render-vs-own-signature DTW
0.0035) but its true-class-to-own-generated-template distance (median 1.02, reproduced here as
1.057 from read_iso.json's genB_inv/genB_pose) is WORSE than its distance to the nearest WRONG
class's template (median 0.68/0.690) -- NEGATIVE separation on real cursive.

THE DIRECTIVE (creator): the motor cortex plans MOVEMENTS not shapes. Replace the generator with
a MOTOR PLANNER -- Plamondon's sigma-lognormal Kinematic Theory (RESEARCH_CURSIVE.md C4):
handwriting velocity is the space-time superimposition of a small number of LOGNORMAL movement
primitives, each aimed at a virtual target with a constant direction; the trajectory is the
INTEGRAL of that superposed velocity field. This is LOW-DIMENSIONAL (2-6 primitives per letter,
5 params each) and CONTINUOUS (no bin/grid quantization anywhere) -- the biologically-grounded,
donkey=0-compatible (closed-form kinematic model, NOT a trained net) generator BAP's 93% motor-
simulation mechanism (Gilet/Diard/Bessiere 2011) is built on.

THE SPLIT (CLAUDE.md: primitive in Rust, composition/decision in graph or held Term):
  * GENERATE (velocity superposition + trapezoidal integration -> a continuous trajectory) is
    the NEW Rust Term `SigmaLognormalGenerate` (`runners/dsl/src/sigma_lognormal.rs`, wired into
    `term.rs`/`jsonio.rs`/`reflect.rs` exactly like `StrokeQuantize`/`StrokeRender` -- a `native.
    evaluate({"type": "SigmaLognormalGenerate", ...}, {})` one-line handoff, no bespoke py.rs
    binding needed, same as every other JSON-constructed Term in this codebase).
  * FIT (extracting a motor plan -- peak detection + closed-form nonlinear least-squares -- from
    a real trajectory's velocity profile) is Python-side signal processing, the SAME "world-
    adapter-class feature extractor" precedent `domains/motor_plan.py` already established
    (mechanical translation of raw ink into graph-resident data, not a graph/agent decision).
    `fit_sigma_lognormal`'s own least-squares OBJECTIVE evaluates the velocity-domain forward
    model in Python (a scalar residual for scipy's optimizer -- standard curve-fitting, not
    trajectory generation) but NEVER integrates a position trajectory itself -- see
    `tests/test_run72_migrated.py`'s own source-audit gate (no `cumsum`/manual position
    integration anywhere in the FIT path; every POSITION the pipeline ever consumes comes from
    the Rust `SigmaLognormalGenerate` Term).

NO TIMESTAMPS in the DeepWriting corpus (offline ink, absolute x/y only) -- pseudo-time is the
point INDEX (documented assumption: near-uniform digitizer sampling rate, the standard assumption
for corpora derived from IAM-OnDB-style capture). `mu`'s effective scale is CALIBRATED to this
per-sample pseudo-time (not seconds) -- `fit_sigma_lognormal`'s initial `tau_guess` derives from
the OBSERVED average inter-peak sample spacing of the stroke being fit, not a fixed literature
constant, so it adapts to whatever sampling density a given corpus/synthetic fixture provides.

REUSE (nothing new-from-scratch beyond the Rust primitive + the fit function):
  * run 66 (`cc66`) -- `invariant` (StrokeQuantize's own continuous canonicalization, Python-side
    pure geometry, reused verbatim), `_arclen`, `_heading`, `dtw`, `CANON_N`, `STROKE_SHAPES_SEED`.
    `learn_letter_form_sigma` below produces the EXACT SAME schema `cc66.learn_letter_form`
    does (`{signature, n_points, theta, arclen, canon}`) so run 71's own placement machinery
    (`gen_inv_from_form`, `gen_pose_from_form`, `build_within_gen_bank`, `build_cross_gen_bank`,
    `compute_class_scale`) applies UNCHANGED -- imported and reused verbatim as `r71.*` below,
    not re-implemented.
  * run 69 (`r69`) -- `_class_cost` (bank-vs-query DTW minimum, reused verbatim), the ALREADY-
    COMPUTED isolated-char query canons (`inv`/`pose_own`/`pose_pop`) in `run69_checkpoints/
    prep.json`, READ-ONLY.
  * run 71 (`r71`) -- `results/run71_checkpoints/prep.json` (test writers, the UNIONED exclusion
    set, per-writer frames, own-exemplar pools, class_scale -- regenerated once there, reused
    here VERBATIM, READ-ONLY) and `results/run71_checkpoints/read_iso.json` (the STROKEQUANTIZE
    motor-sim genB_inv/genB_pose per query -- the DIRECT COMPARISON BASELINE for this run's own
    separation gate, READ-ONLY, never recomputed).
  * run 61 (`r61`) -- `_wilson_ci`.

STAGE 1 -- FIDELITY: fit a motor plan to real cursive letters, generate (through the Rust Term),
check (a) self-consistency (does the fitted+regenerated trajectory reconstruct the SAME letter it
was fit from -- DTW against the original raw ink) and (b) continuity (no small alphabet of step
vectors, contrast StrokeQuantize's turn/len bins).

STAGE 2 -- THE GATE (run 71's own falsifier, replayed on the new generator): for the SAME 340
within-writer isolated test queries run 69/71 used, LEARN each test writer's own SIGMA-LOGNORMAL
codebook (in place of run 71's StrokeQuantize-based `cc66.learn_letter_form`), place it in the
SAME writer-relative frame (`r71.gen_pose_from_form`, unchanged), and recompute the SAME
own-class-vs-nearest-wrong-class combined-score separation run 71 reported as 1.02/0.68 negative.
POSITIVE (own < wrong) licenses the full motor-sim reader (stage 3); negative means even the
continuous generator's per-letter content isn't discriminative enough on real cursive, and this
run localizes why (fit stability / cross-writer variability / residual geometric ambiguity).

DISCIPLINE: donkey=0 (sigma-lognormal is a CLOSED-FORM kinematic curve fit, NOT an SGD-trained
net). NO git add/commit. SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1, md5(seeds/stroke_shapes.json)
asserted UNCHANGED before/after every stage. run61/66/69/71_checkpoints are READ-ONLY.

Run:
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_motorplan_run72.py \\
    --stage <fit_demo|genforms|read_iso|separation_gate|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
from scipy.optimize import least_squares
from scipy.signal import find_peaks

import scripts.jabberwock_cursive_curriculum_run66 as cc66
import scripts.jabberwock_pose_read_run69 as r69
import scripts.jabberwock_motorsim_run71 as r71
import scripts.jabberwock_wordread_run61 as r61

SEP = "=" * 92
STROKE_SHAPES_SEED = cc66.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run72_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run72.log")
os.makedirs(CKPT_DIR, exist_ok=True)

RUN71_CKPT = os.path.join(ROOT, "results", "run71_checkpoints")           # READ-ONLY.
RUN71_PREP = os.path.join(RUN71_CKPT, "prep.json")
RUN71_READ_ISO = os.path.join(RUN71_CKPT, "read_iso.json")
RUN69_PREP = r71.RUN69_PREP                                               # READ-ONLY.

LOWER_CLASSES = r69.LOWER_CLASSES
CANON_N = cc66.CANON_N
PRIMARY_LAMBDA = r69.PRIMARY_LAMBDA                     # 1.0, reused verbatim (never re-tuned).
PER_CALL_BUDGET_SECONDS = 460.0

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS -- the motor-plan fit, new to this run.
# ------------------------------------------------------------------------------------------- #
MAX_PRIMITIVES = 6              # a "low-dimensional" plan cap -- Plamondon: a handful per letter.
SIGMA0 = 0.4                    # fixed initial lognormal shape width (log-time std dev).
GEN_N_POINTS = 96               # dense CONTINUOUS generation before invariant-resampling to CANON_N.
PEAK_HEIGHT_FRAC = 0.15         # velocity-peak detection threshold, fraction of the stroke's own max.

RUN71_MEDIAN_OWN = 1.057188195191657     # reproduced from run71's read_iso.json (this run's own
RUN71_MEDIAN_WRONG = 0.6903568412438948  # recomputation, matching commit 34a67b81's "1.02/0.68").


# ============================================================================================= #
#  I/O + seed guard (identical pattern to runs 61/66/69/71).
# ============================================================================================= #
def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def _ckpt(name):
    return os.path.join(CKPT_DIR, name)


def _save(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f)


def _load(path):
    with open(path) as f:
        return json.load(f)


def _require(name):
    p = _ckpt(name)
    if not os.path.exists(p):
        raise SystemExit(f"WALL: run the stage that produces {name} first.")
    return _load(p)


def _seed_guard(stage, before=None):
    cur = _md5(STROKE_SHAPES_SEED)
    if before is not None and cur != before:
        raise SystemExit(f"HARD STOP: seeds/stroke_shapes.json md5 changed during {stage} "
                          f"({before} -> {cur}).")
    return cur


def _wilson(k, n):
    return r61._wilson_ci(k, n)


# ============================================================================================= #
#  THE FIT -- Python-side signal processing (peak detection + closed-form nonlinear least-
#  squares), NEVER a trajectory generator itself (see this module's own docstring + the
#  source-audit test). Operates on VELOCITY only; positions are never integrated in Python.
# ============================================================================================= #
def _lognormal_scalar(tau: float, mu: float, sigma: float) -> float:
    if tau <= 1e-9 or sigma <= 1e-9:
        return 0.0
    z = (math.log(tau) - mu) / sigma
    return (1.0 / (sigma * tau * math.sqrt(2.0 * math.pi))) * math.exp(-0.5 * z * z)


def _lognormal_vec(tau: np.ndarray, mu: float, sigma: float) -> np.ndarray:
    """Vectorized velocity-MAGNITUDE forward model -- the fitting objective's own inner
    evaluation, used ONLY to build a scalar residual for `scipy.optimize.least_squares`. This is
    the FIT's closed-form curve-fitting math (donkey=0: no SGD, no trained weights) -- it never
    accumulates a position (no `cumsum`, no running x/y state), so it is NOT a re-implementation
    of the Rust Term's own velocity-superposition-plus-INTEGRATION generator."""
    out = np.zeros_like(tau)
    mask = tau > 1e-9
    t = tau[mask]
    z = (np.log(t) - mu) / sigma
    out[mask] = (1.0 / (sigma * t * math.sqrt(2.0 * math.pi))) * np.exp(-0.5 * z * z)
    return out


def fit_sigma_lognormal(points, max_primitives: int = MAX_PRIMITIVES):
    """Extract a LOW-DIMENSIONAL sigma-lognormal motor plan from a raw stroke's own velocity
    profile: peak-detect (`scipy.signal.find_peaks`) to seed one primitive per detected velocity
    peak (capped at `max_primitives`), then jointly refine ALL primitives via
    `scipy.optimize.least_squares` against the OBSERVED velocity vector sequence (pseudo-time =
    point index, no real timestamps in this corpus -- see module doc). Returns
    `(primitives, t_start, t_end, start_xy)`, `primitives` a list of `[t0, mu, sigma, D, theta]`
    5-tuples ready for the Rust `SigmaLognormalGenerate` Term. Degenerate (<3 points) input
    returns a single fallback primitive spanning the whole chord -- graceful, never raises."""
    pts = np.asarray(points, float)
    n = len(pts)
    if n < 3:
        d = (pts[-1] - pts[0]) if n >= 2 else np.array([1e-3, 0.0])
        theta = math.atan2(float(d[1]), float(d[0]))
        dist = float(np.linalg.norm(d)) or 1e-3
        mu0 = math.log(max(1.0, float(n))) + SIGMA0 ** 2
        peak_d = _lognormal_scalar(math.exp(mu0 - SIGMA0 ** 2), mu0, SIGMA0)
        d0 = dist / max(peak_d, 1e-6)
        return [[0.0, mu0, SIGMA0, d0, theta]], -1.0, float(max(4.0, n + 2)), pts[0].tolist()

    vel = np.diff(pts, axis=0)
    speed = np.linalg.norm(vel, axis=1)
    t_vel = np.arange(len(speed)) + 0.5  # midpoint pseudo-time convention.
    smax = float(speed.max()) or 1e-9

    peak_idx, _ = find_peaks(speed, height=PEAK_HEIGHT_FRAC * smax)
    if len(peak_idx) == 0:
        peak_idx = np.array([int(np.argmax(speed))])
    peak_idx = peak_idx[:max_primitives]

    # Adaptive time-scale calibration: `tau_guess` (the primitive's own characteristic
    # sample-count, NOT a fixed literature constant in seconds) derives from the OBSERVED
    # average inter-peak sample spacing of THIS stroke -- so the same fit code applies whether
    # the caller's pseudo-time convention is "one unit per real point" (this module's own use)
    # or a synthetic fixture with a different point density (the unit tests).
    avg_gap = max(1.0, len(speed) / max(len(peak_idx), 1))
    tau_guess = float(np.clip(avg_gap * 0.35, 1.0, 12.0))
    mu0 = math.log(tau_guess) + SIGMA0 ** 2

    p0: list = []
    lo: list = []
    hi: list = []
    for pk in peak_idx:
        t_peak = float(t_vel[pk])
        t0_0 = t_peak - tau_guess
        peak_d = _lognormal_scalar(tau_guess, mu0, SIGMA0)
        d0 = float(speed[pk]) / max(peak_d, 1e-6)
        theta0 = math.atan2(float(vel[pk][1]), float(vel[pk][0]))
        p0.extend([t0_0, mu0, SIGMA0, d0, theta0])
        lo.extend([t0_0 - 2.0 * avg_gap - 1.0, -1.0, 0.08, 0.0, theta0 - math.pi])
        hi.extend([t0_0 + 2.0 * avg_gap + 1.0, 3.5, 1.5, d0 * 25.0 + 1.0, theta0 + math.pi])

    def residual(p: np.ndarray) -> np.ndarray:
        vx = np.zeros(len(t_vel))
        vy = np.zeros(len(t_vel))
        for i in range(0, len(p), 5):
            t0i, mu, sigma, d, theta = p[i:i + 5]
            mag = d * _lognormal_vec(t_vel - t0i, mu, sigma)
            vx += mag * math.cos(theta)
            vy += mag * math.sin(theta)
        return np.concatenate([vx - vel[:, 0], vy - vel[:, 1]])

    try:
        res = least_squares(residual, p0, bounds=(lo, hi), max_nfev=250, xtol=1e-8, ftol=1e-8)
        p = res.x
    except Exception:
        p = np.asarray(p0, float)

    primitives = [list(map(float, p[i:i + 5])) for i in range(0, len(p), 5)]
    t_start = float(min(pr[0] for pr in primitives) - 1.0)
    t_end = float(len(speed) + max(2.0, tau_guess))
    return primitives, t_start, t_end, pts[0].tolist()


# ============================================================================================= #
#  THE GENERATE -- the ONLY place this run ever produces a position trajectory: one held Rust
#  Term evaluation, `SigmaLognormalGenerate` (velocity superposition + trapezoidal integration).
# ============================================================================================= #
def sigma_generate(native, primitives: list, start: tuple, t_start: float, t_end: float,
                    n_points: int = GEN_N_POINTS) -> np.ndarray:
    """`native.evaluate({"type": "SigmaLognormalGenerate", ...}, {})` -- the one-line Rust
    handoff (`runners/dsl/src/sigma_lognormal.rs`). Returns an `(n_points, 2)` array."""
    out = native.evaluate({
        "type": "SigmaLognormalGenerate",
        "primitives": {"type": "Lit", "value": [[float(x) for x in p] for p in primitives]},
        "start": {"type": "Lit", "value": [float(start[0]), float(start[1])]},
        "t_start": float(t_start), "t_end": float(t_end), "n_points": int(n_points),
    }, {})
    return np.asarray(out["points"], float)


def learn_letter_form_sigma(native, points) -> dict:
    """LEARN one cursive letter allograph via the MOTOR-PLANNING generator: fit (Python signal
    processing) + generate (the Rust Term) + canonicalize (`cc66.invariant`, pure geometry,
    reused verbatim). Produces the EXACT SAME schema `cc66.learn_letter_form` does
    (`{signature, n_points, theta, arclen, canon}`) so run 71's OWN placement machinery
    (`gen_inv_from_form`/`gen_pose_from_form`/`build_within_gen_bank`/`build_cross_gen_bank`)
    applies UNCHANGED -- the drop-in-replacement design this run's docstring states."""
    pts = np.asarray(points, float)
    primitives, t_start, t_end, start_xy = fit_sigma_lognormal(pts)
    gen = sigma_generate(native, primitives, start_xy, t_start, t_end, GEN_N_POINTS)
    canon = cc66.invariant(gen.tolist(), CANON_N)
    return {"signature": primitives, "n_points": int(len(pts)),
            "theta": cc66._heading(pts), "arclen": cc66._arclen(pts), "canon": canon}


# ============================================================================================= #
#  THE SEPARATION METRIC -- run 71's own formula (median own-class combined score vs median
#  nearest-wrong-class combined score, PRIMARY_LAMBDA=1.0), reused byte-identically so the two
#  runs' numbers are directly comparable.
# ============================================================================================= #
def own_vs_wrong(records: list, inv_key: str, pose_key: str, lam: float = PRIMARY_LAMBDA) -> dict:
    owns, wrongs = [], []
    for r in records:
        v = np.asarray(r[inv_key], float) + lam * np.asarray(r[pose_key], float)
        ci = r["true_class"] - 10
        owns.append(float(v[ci]))
        wrongs.append(float(min(v[i] for i in range(26) if i != ci)))
    return {"median_own": float(np.median(owns)), "median_wrong": float(np.median(wrongs)),
            "owns": owns, "wrongs": wrongs, "n": len(records),
            "positive": float(np.median(owns)) < float(np.median(wrongs))}


# ============================================================================================= #
#  STAGE: fit_demo (STAGE 1 -- fidelity: self-consistency + continuity on real cursive letters).
# ============================================================================================= #
def stage_fit_demo():
    print(f"\n{SEP}\n  STAGE: fit_demo (STAGE 1 -- motor-plan fit+generate fidelity on REAL "
          f"cursive letters)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("fit_demo")
    import substrate_rs as srs
    native = srs.Substrate()._inner

    prep = _load(RUN71_PREP)
    own_raw_bank = prep["own_raw_bank"]
    demo_items = []
    for w in prep["test_writers"][:40]:
        for c in LOWER_CLASSES:
            insts = own_raw_bank.get(str(w), {}).get(str(c), [])
            for pts in insts[:1]:
                demo_items.append((w, c, pts))
            if len(demo_items) >= 60:
                break
        if len(demo_items) >= 60:
            break

    records = []
    for w, c, pts in demo_items:
        pts = np.asarray(pts, float)
        primitives, t_start, t_end, start_xy = fit_sigma_lognormal(pts)
        gen = sigma_generate(native, primitives, start_xy, t_start, t_end, n_points=len(pts))
        self_dtw = cc66.dtw(native, pts.tolist(), gen.tolist())
        arclen = cc66._arclen(pts)
        # Continuity: distinct (coarsely-hashed) consecutive step vectors, out of a dense
        # GEN_N_POINTS regeneration -- a grid-quantized generator (StrokeQuantize: 12 segments)
        # collapses onto <= 12 knot deltas; this should show far more.
        dense = sigma_generate(native, primitives, start_xy, t_start, t_end, GEN_N_POINTS)
        deltas = np.round(np.diff(dense, axis=0) * 1e4).astype(np.int64)
        n_distinct_steps = len({tuple(d) for d in deltas.tolist()})
        records.append({
            "writer": w, "class": c, "n_primitives": len(primitives),
            "n_points": int(len(pts)), "self_dtw": self_dtw,
            "self_dtw_normalized": self_dtw / max(arclen, 1e-6),
            "n_distinct_steps": n_distinct_steps, "n_dense_steps": len(deltas),
        })

    _seed_guard("fit_demo", md5_before)
    n = len(records)
    med_self = float(np.median([r["self_dtw"] for r in records]))
    med_self_norm = float(np.median([r["self_dtw_normalized"] for r in records]))
    med_primitives = float(np.median([r["n_primitives"] for r in records]))
    med_distinct_frac = float(np.median([r["n_distinct_steps"] / max(r["n_dense_steps"], 1)
                                          for r in records]))
    print(f"  n_demo_letters={n}")
    print(f"  median primitives/letter = {med_primitives:.1f}  (cap={MAX_PRIMITIVES}, LOW-DIM)")
    print(f"  median self-consistency DTW (raw units) = {med_self:.4f}")
    print(f"  median self-consistency DTW (/arclen)   = {med_self_norm:.4f}   "
          f"(run 71's StrokeQuantize self-consistency: 0.0035, DIFFERENT normalization -- "
          f"reported for context, not a like-for-like ratio)")
    print(f"  median fraction of DENSE ({GEN_N_POINTS}-point) step-vectors that are DISTINCT = "
          f"{med_distinct_frac:.3f}  (StrokeQuantize's own alphabet: <= {cc66.SEG} knot deltas "
          f"total, i.e. a fraction near {cc66.SEG}/{GEN_N_POINTS-1}={cc66.SEG/(GEN_N_POINTS-1):.3f} "
          f"at BEST -- this generator's own fraction should be far higher: CONTINUOUS.")
    _save({"records": records, "median_self_dtw": med_self, "median_self_dtw_norm": med_self_norm,
           "median_primitives": med_primitives, "median_distinct_step_frac": med_distinct_frac,
           "stroke_shapes_md5": md5_before}, _ckpt("fit_demo.json"))
    print(f"  saved -> {_ckpt('fit_demo.json')}  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: genforms -- LEARN each test writer's own SIGMA-LOGNORMAL codebook (drop-in replacement
#  for run 71's stage_genforms, same own_raw_bank input, checkpointed per writer, resumable).
# ============================================================================================= #
def stage_genforms():
    print(f"\n{SEP}\n  STAGE: genforms (learn each test writer's OWN motor-PLANNING codebook -- "
          f"sigma-lognormal fit+generate)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("genforms")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _load(RUN71_PREP)
    own_raw_bank = prep["own_raw_bank"]

    out_path = _ckpt("genforms.json")
    state = _load(out_path) if os.path.exists(out_path) else {"writer_forms": {}, "done": False}
    if state.get("done"):
        print(f"  genforms already COMPLETE (n={len(state['writer_forms'])} writers).", flush=True)
        return 0
    remaining = [w for w in prep["test_writers"] if str(w) not in state["writer_forms"]]
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    n_forms_total = 0

    for w in remaining:
        wf = {}
        for c in LOWER_CLASSES:
            insts = own_raw_bank.get(str(w), {}).get(str(c), [])
            forms = [learn_letter_form_sigma(native, pts) for pts in insts]
            wf[str(c)] = forms
            n_forms_total += len(forms)
        state["writer_forms"][str(w)] = wf
        n_new += 1
        if n_new % 10 == 0:
            _save(state, out_path)
            _seed_guard("genforms", md5_before)
            print(f"    ... {len(state['writer_forms'])}/{len(prep['test_writers'])} writers  "
                  f"[{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("genforms", md5_before)
                print(f"  WALL-BUDGET: {len(state['writer_forms'])}/{len(prep['test_writers'])} "
                      f"done -- re-invoke --stage genforms to resume.", flush=True)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("genforms", md5_before)
    print(f"  learned {len(state['writer_forms'])} writer codebooks ({n_forms_total} forms total)"
          f"  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read_iso -- arm B[sigma-lognormal motor-sim] on the SAME 340 isolated test queries
#  run 69/71 used (WITHIN-writer; CROSS uses run 71's population StrokeQuantize codebook still --
#  out of scope for this run's own generator, named as an honest limitation in the summary).
# ============================================================================================= #
def stage_read_iso():
    print(f"\n{SEP}\n  STAGE: read_iso -- arm B[sigma-lognormal motor-sim] on ISOLATED test "
          f"chars\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read_iso")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _load(RUN71_PREP)
    genforms = _require("genforms.json")
    if not genforms.get("done"):
        raise SystemExit("WALL: genforms not COMPLETE -- re-invoke --stage genforms.")
    writer_forms = genforms["writer_forms"]
    writer_frames = prep["writer_frames"]

    r69_prep = _load(RUN69_PREP)
    queries = r69_prep["queries"]

    out_path = _ckpt("read_iso.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
    if state.get("done"):
        print(f"  read_iso already COMPLETE (n={len(state['records'])}).", flush=True)
        return 0
    done = {r["qid"] for r in state["records"]}
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0
    within_bank_cache = {}

    for q in queries:
        if q["qid"] in done:
            continue
        w = str(q["writer"])
        if w not in within_bank_cache:
            within_bank_cache[w] = r71.build_within_gen_bank(
                writer_forms.get(w, {}), writer_frames.get(w, {"x_height": 1.0, "slant_deg": 0.0}))
        within_bank = within_bank_cache[w]
        genB_inv = r69._class_cost(native, q["inv"], within_bank, "inv")
        genB_pose = r69._class_cost(native, q["pose_own"], within_bank, "pose")
        state["records"].append({
            "qid": q["qid"], "writer": q["writer"], "true_class": q["true_class"],
            "symbol": q["symbol"], "genB_inv": genB_inv, "genB_pose": genB_pose,
        })
        n_new += 1
        if n_new % 20 == 0:
            _save(state, out_path)
            _seed_guard("read_iso", md5_before)
            n = len(state["records"])

            def _acc():
                ok = 0
                for r in state["records"]:
                    v = np.asarray(r["genB_inv"]) + PRIMARY_LAMBDA * np.asarray(r["genB_pose"])
                    ok += int((int(np.argmin(v)) + 10) == r["true_class"])
                return 100.0 * ok / n

            print(f"    ... {n}/{len(queries)}  sigma_genB_within={_acc():.1f}%  "
                  f"[{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("read_iso", md5_before)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(queries)} done -- re-invoke "
                      f"--stage read_iso to resume.", flush=True)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read_iso", md5_before)
    print(f"  read_iso {len(state['records'])} queries  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: separation_gate -- THE GATE. Recomputes run 71's own falsifier on the sigma-lognormal
#  generator, reports side-by-side with run 71's StrokeQuantize number (READ-ONLY reload).
# ============================================================================================= #
def stage_separation_gate():
    print(f"\n{SEP}\n  STAGE: separation_gate -- STAGE 2, THE FALSIFIER (own-class vs nearest-"
          f"wrong-class combined score)\n{SEP}", flush=True)
    md5_now = _seed_guard("separation_gate")

    ri = _require("read_iso.json")
    if not ri.get("done"):
        print("  WALL: read_iso not COMPLETE."); return 1
    sigma_sep = own_vs_wrong(ri["records"], "genB_inv", "genB_pose", PRIMARY_LAMBDA)

    run71_read_iso = _load(RUN71_READ_ISO)
    sq_sep = own_vs_wrong(run71_read_iso["records"], "genB_inv", "genB_pose", PRIMARY_LAMBDA)

    n_iso = len(ri["records"])
    ok = 0
    for r in ri["records"]:
        v = np.asarray(r["genB_inv"]) + PRIMARY_LAMBDA * np.asarray(r["genB_pose"])
        ok += int((int(np.argmin(v)) + 10) == r["true_class"])
    sigma_char_acc = 100.0 * ok / n_iso if n_iso else 0.0
    ci = _wilson(ok, n_iso)

    print(f"  n = {n_iso} (SAME 340 within-writer isolated test queries run 69/71 used)")
    print(f"\n  === RUN 71 STROKEQUANTIZE motor-sim (read-only reload, byte-identical recompute of "
          f"the commit's own 1.02/0.68) ===")
    print(f"    median own-class combined score   = {sq_sep['median_own']:.4f}")
    print(f"    median nearest-wrong combined score = {sq_sep['median_wrong']:.4f}")
    print(f"    separation POSITIVE (own < wrong)?  {sq_sep['positive']}")
    print(f"\n  === RUN 72 SIGMA-LOGNORMAL motor-PLANNING generator (this run, NEW) ===")
    print(f"    median own-class combined score   = {sigma_sep['median_own']:.4f}")
    print(f"    median nearest-wrong combined score = {sigma_sep['median_wrong']:.4f}")
    print(f"    separation POSITIVE (own < wrong)?  {sigma_sep['positive']}")
    print(f"    (for reference) argmin char accuracy from this same bank: {sigma_char_acc:.1f}% "
          f"CI=[{100*ci[0]:.1f},{100*ci[1]:.1f}]")

    print(f"\n  THE GATE: {'PASS -- positive separation, motor-sim reading (stage 3) is '
          'LICENSED' if sigma_sep['positive'] else 'FAIL -- still negative, the continuous '
          'generator does not discriminate real cursive either -- stage 3 not warranted, '
          'localize why below'}")

    _save({"sigma": sigma_sep, "run71_strokequantize": sq_sep, "n": n_iso,
           "sigma_char_acc": sigma_char_acc, "sigma_char_ci": list(ci),
           "gate_positive": sigma_sep["positive"], "stroke_shapes_md5": md5_now},
          _ckpt("separation_gate.json"))
    _seed_guard("separation_gate", md5_now)
    print(f"\n  saved -> {_ckpt('separation_gate.json')}")
    return 0


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 72 SCOREBOARD (THE MOTOR-PLANNING WRITER)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    fd = _load(_ckpt("fit_demo.json")) if os.path.exists(_ckpt("fit_demo.json")) else None
    sg = _load(_ckpt("separation_gate.json")) if os.path.exists(_ckpt("separation_gate.json")) else None

    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}")
    if fd:
        print(f"\n  STAGE 1 (fidelity): median primitives/letter={fd['median_primitives']:.1f}, "
              f"median self-consistency DTW={fd['median_self_dtw']:.4f} "
              f"(/arclen={fd['median_self_dtw_norm']:.4f}), continuity fraction-distinct-steps="
              f"{fd['median_distinct_step_frac']:.3f}")
    if sg:
        print(f"\n  STAGE 2 (the gate): run71 StrokeQuantize own/wrong = "
              f"{sg['run71_strokequantize']['median_own']:.4f}/"
              f"{sg['run71_strokequantize']['median_wrong']:.4f}  (positive={sg['run71_strokequantize']['positive']})")
        print(f"                      run72 sigma-lognormal own/wrong = "
              f"{sg['sigma']['median_own']:.4f}/{sg['sigma']['median_wrong']:.4f}  "
              f"(positive={sg['gate_positive']})")
        print(f"                      argmin char accuracy (this bank) = {sg['sigma_char_acc']:.1f}%")
    print(f"\n{SEP}\n  RUN 72 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                   choices=["fit_demo", "genforms", "read_iso", "separation_gate", "summary"])
    args = p.parse_args()
    return {"fit_demo": stage_fit_demo, "genforms": stage_genforms, "read_iso": stage_read_iso,
            "separation_gate": stage_separation_gate, "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
