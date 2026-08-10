"""jabberwock_pendata_run46.py -- RUN 46: THE FIRST REAL PEN-DATA TEST of the five falsifiable
predictions armed across the Omniglot mousewriting arc (`OMNIGLOT_ARC.md` sections 5 and 9).

BACKGROUND (cited, not re-derived): the Omniglot corpus was discovered (run 33/34,
`81e6da1a`/`70bdfc01`) to be a browser MOUSE trace, not a pen digitizer trace -- 59-65%
integer-pixel coordinate deltas, ~56-60% exactly-0-degree turns (Bresenham staircase), median
inter-sample dt ~15ms (~60Hz event polling), and a two-thirds-power-law median r^2 of only
0.084 (vs the law's ballistic-pen prediction of r^2 near 1, slope -0.333). Five predictions were
armed for REAL pen/finger data (`OMNIGLOT_ARC.md` section 9), never testable before because the
arc had no such corpus. This run gets two real corpora for the first time:
  - UCI Character Trajectories (WACOM tablet, 200Hz, TRUE pen kinematics, ALL 2858 samples from
    ONE writer -- see "UCI CAVEAT" below).
  - Google QuickDraw (`circle`/`square`/`triangle`/`zigzag`/`line`/`star`, RAW format, real
    per-event timestamps, MIXED mouse+touch population across many anonymous contributors --
    split by device via `mouse_model.integer_delta_fraction`, giving a genuine cross-writer
    touchscreen subset for the first time).

DATA ACQUISITION (already performed by the orchestrator via direct `curl`, documented here for
reproducibility -- this script does NOT re-download; it reads the local files):
  curl -sS -o /tmp/pendata/uci_chartraj.zip \\
      "https://archive.ics.uci.edu/static/public/175/character+trajectories.zip"
  unzip -o -q /tmp/pendata/uci_chartraj.zip -d /tmp/pendata/uci_chartraj
  for cat in circle square triangle zigzag line star; do
    curl -sS -r 0-3000000 \\
      "https://storage.googleapis.com/quickdraw_dataset/full/raw/${cat}.ndjson" \\
      -o "/tmp/pendata/${cat}_sample.ndjson"
  done
A range request truncates the LAST line mid-JSON-object -- every ndjson parse in this script
silently drops a line that fails `json.loads` (an honest partial-download artifact, never a
crash, never silently mis-parsed).

UCI FORMAT (verified by this run's own `--stage unit_sanity`, not assumed from paraphrase --
read directly off `scipy.io.loadmat`'s returned structure and `trajectories.names`): `mixout`
is a `(1, 2858)` object array, each entry a `(3, T)` array of [x-velocity, y-velocity, pen-tip
force], numerically differentiated + Gaussian-smoothed (sigma=2) from a WACOM tablet at 200Hz
(`consts.dt == 0.005`s, uniform). `consts.charlabels` (1-indexed) + `consts.key` (20 letters:
a,b,c,d,e,g,h,l,m,n,o,p,q,r,s,u,v,w,y,z) give the class. Position is recovered by
`pos = cumsum(vel_xy, axis=0) * dt` (verified below to produce sane, non-degenerate, bounded
glyph shapes). Sample lengths range 109-205 points (all well above every `max_knots` this run
uses). NO documented cap on the leading near-zero-velocity run (pen-down onset transient, 3-25
samples observed) -- left in place, not trimmed (it is real data, not a padding artifact).

UCI CAVEAT (stated up front, honored throughout every UCI result below): the dataset's own
abstract states "All samples are from the same writer, for the purposes of primitive
extraction." This is NOT "one writer per class" -- it is ONE WRITER FOR THE ENTIRE CORPUS.
Consequences, stated explicitly wherever relevant:
  - P1's "per-writer" framing collapses to "per-sample" for UCI (no cross-writer distribution
    exists to report; every sample already IS one writer's output).
  - P2's "cross-drawer boundary agreement" becomes CROSS-INSTANCE agreement (same writer,
    repeated exemplars of the same class) -- still a meaningful test (does a physically-motivated
    segmentation generalize across independent repetitions of the same character by the same
    hand?), but not the cross-PERSON generalization the mousewriting arc's own P2 measured.
  - P3's "class-grain, not instance-grain, cross-writer coherence" (`_coherence_block`,
    >=3 distinct drawers) is STRUCTURALLY UNMEASURABLE on UCI (there is exactly one "drawer"
    for every class) -- this run does NOT compute a P1b-style coherence number for UCI and says
    so plainly rather than reporting a vacuous 100%/0% coherence figure.
  - P5's "does per-stroke identity return for single-stroke glyphs" is UNCONDITIONALLY testable
    on UCI, because -- per the dataset's own construction rule ("only characters with a single
    'PEN-DOWN' segment were considered") -- EVERY UCI sample is single-stroke. UCI's P3 number
    and UCI's P5 number are therefore the identical measurement; this is stated, not hidden.

QUICKDRAW DEVICE SPLIT: `mouse_model.integer_delta_fraction` is the discriminator (module
docstring: "~59% of sample-to-sample coordinate deltas are exact integers" on Omniglot mouse
data). Applied here as `pooled_integer_delta_fraction` (this script, below) -- consecutive-
sample deltas are computed PER STROKE (never across a pen-up gap between two strokes, which
would inject a meaningless jump-distance into the diagnostic) and pooled across a drawing's
strokes before the delta-integrality fraction is taken. THRESHOLD: pre-registered ALGORITHM
(not a peeked-at magic number) -- a 20-bin histogram of pooled fractions across a background
QuickDraw sample is searched for its two largest local-maxima bins; the split point is the
midpoint of the historgram valley between them (`_find_split_threshold`, below); if the
distribution is not clearly bimodal (fewer than two resolvable peaks, or peaks adjacent), the
algorithm FALLS BACK to a fixed pre-registered default of 0.35 -- chosen because it sits well
below Omniglot's own measured mouse-baseline band (0.59-0.65), giving comfortable margin on
either side of a real bimodal split without having been tuned against any downstream P1-P5
number. The algorithm itself, and the fallback constant, are fixed BEFORE `--stage device_split`
is ever run against real data.

WHAT THIS SCRIPT DOES NOT DO (CLAUDE.md self-check, this is pure numerical/data-science research
over pre-built world-adapter-class feature extractors, explicitly out of scope for the
architecture rule per this run's own launch brief): no `torch`/borrowed model (`_donkey0()`
checked in every stage's report); no write to any `results/run*_checkpoints/` directory other
than this run's own `results/run46_checkpoints/`; `seeds/stroke_shapes.json` (a parallel-
session-owned file) is NEVER opened -- every substrate touch in this script is a throwaway
`substrate_rs.Substrate()` used only to reach `domains/stroke_programs.py`'s existing
`stroke_turn_sequence` (itself calling the existing, unmodified `domains/ink_decode.ingest_ink`)
-- the SAME "mints nothing, no `teach()`, no codebook mutation" discipline
`scripts/jabberwock_omniglot_run35_programs.py` already established for this exact tokenization
path. Adaptive bin edges (`domains/adaptive_bins.py`) are FIT FRESH on each corpus's own
population (UCI's own samples; QuickDraw's own touch subset) -- per this run's own launch brief,
Omniglot's `results/run34d_checkpoints/edges_report.json` edges are NOT reused (different
sensor, different scale/units, would silently import Omniglot-specific bin placement onto a
physically unrelated signal).

PRE-REGISTERED METRICS AND BARS (stated here, before any stage below computes a single real
number against them):

  P1 -- TWO-THIRDS POWER LAW. Primary method (for the bar, DIRECTLY comparable to the
  Omniglot-mouse 0.084 protocol): `domains.ink_dynamics.two_thirds_fit`/`pooled_two_thirds_fit`
  on (x, y, t) -- UCI's t is integrated positions from velocity (see above); QuickDraw's
  positions are used as-is (already real (x, y, t)). UCI is per-SAMPLE (one stroke each, see
  UCI CAVEAT); QuickDraw is per-DRAWING (`pooled_two_thirds_fit` pools a drawing's own strokes
  into one fit, the "one writer's strokes pooled" precedent applied at the drawing grain).
  SECONDARY robustness cross-check (UCI only, reported alongside but NOT used for the bar
  decision): a DIRECT-VELOCITY variant (`two_thirds_fit_given_speed`, below) that regresses the
  dataset's OWN already-smoothed velocity magnitude against curvature computed from the
  integrated positions, skipping `ink_dynamics.speed_profile`'s own re-differentiation +
  re-smoothing (which would compound onto UCI's already-Gaussian-smoothed channel) -- reported
  because it is arguably the more physically direct test on this specific corpus, but the bar
  below is decided on the PRIMARY (comparable-protocol) number, not this one.
  BAR: pen/touch median r^2 >= 3x mouse-control's cited 0.084 (i.e. >= 0.252) AND median slope
  in [-0.45, -0.20]; QuickDraw's OWN freshly-measured mouse-subset median r^2 must land near
  ~0.08 (protocol guard: pre-registered acceptance band [0.04, 0.16] -- if it lands outside this
  band, the guard has FAILED and the corresponding pen/touch P1 result is flagged unreliable,
  not treated as proof of anything).

  P2 -- VELOCITY-MINIMA VS ARC-LENGTH-CORNER SEGMENTATION, count-matched (run-33's exact
  protocol, verbatim machinery: `ink_dynamics.velocity_minima_knots` /
  `arclength_corner_knots` / `mean_pairwise_agreement` / `count_matched_null_agreement`). Per
  class (UCI: 20 character classes, cross-INSTANCE per the UCI CAVEAT; QuickDraw: 6 categories,
  cross-DRAWING/cross-contributor), capped population (`P2_MAX_PER_CLASS`, pre-registered,
  Monte-Carlo tractability only, never re-tuned against a result), compute each method's raw
  mean pairwise agreement and its own count-matched null, average excess-over-null across
  classes.
  BAR: velocity-minima count-matched excess > arc-length excess (the reversal) on BOTH UCI and
  QuickDraw-touch; QuickDraw's OWN mouse-subset control must reproduce run-33's ORIGINAL
  ordering (arc-length excess > velocity excess) as a protocol guard.

  P3/P4/P5 -- STROKE-GRAIN PROGRAM IDENTITY (run-35's exact lightweight tokenize-as-identity
  protocol, verbatim machinery: `domains.stroke_programs.stroke_turn_sequence` /
  `tokenize_turn_sequence` / `finalize_tokens` / `format_fine` / `format_coarse`, with FRESH
  `domains.adaptive_bins.compute_adaptive_edges` per corpus). `_entropy_block` /
  `_coherence_block` / `_p1c_block` (this script, mirroring
  `scripts/jabberwock_omniglot_run35_programs.py`'s own functions of the same names/semantics,
  NOT reimplemented differently -- copied verbatim in behavior) compute, at BOTH fine and coarse
  grain: identity-count + Shannon entropy (P3's own diagnostic), class-grain coherence /
  instance-only fraction where measurable (QuickDraw only, see UCI CAVEAT), and per-class
  program-consistency raw fraction vs a count-matched shuffled-class null (P1c's own protocol --
  THIS SAME NUMBER is read as BOTH P3's "within-class consistency" bar AND P4's "class-
  consistency excess over null" bar, per this run's own launch brief: same function, different
  verdict thresholds).
  P3 BAR: identity count > 10 at fine grain AND fine-grain within-class consistency >= 2x the
  shuffled null (a null of exactly 0 is treated as "any positive excess clears the bar").
  P4 BAR: class-consistency clears >= 2.0x the shuffled null at EITHER grain (fine or coarse) --
  mousewriting's own missed bar was 1.9x (`a85494d3`).
  P5: for UCI, IDENTICAL to P3 (every UCI sample is single-stroke, see UCI CAVEAT -- not
  re-measured separately, the single number is reported under both names). For QuickDraw, the
  SAME P3/P4-style consistency computation is run a SECOND time restricted to the subset of
  touch-subset DRAWINGS that are themselves single-stroke (`len(drawing) == 1` -- expected to be
  common for circle/line/triangle, less common for zigzag/star) -- this is P5's own dedicated
  number, separate from P3's whole-touch-subset number.

EXECUTION DISCIPLINE (ops law this arc's other run scripts all follow): every stage is a
separate `--stage` invocation, self-contained, checkpointed to `results/run46_checkpoints/`,
printed with wall-clock timing; `PER_CALL_BUDGET_SECONDS` batch loops are used in the two
heaviest stages (`p3p4p5_uci`, `p3p4p5_quickdraw`) even though a dry timing check
(0.5ms/stroke for `stroke_turn_sequence`, see this run's own log) suggests they will finish in
well under a minute, as a safety margin consistent with this arc's own established discipline.
No stage ever writes into any `results/run*_checkpoints/` directory other than this run's own.

Run (from the gamma-substrate repo root):
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python3 \\
      scripts/jabberwock_pendata_run46.py --stage <STAGE>
Stages, in dependency order:
  unit_sanity  ->  device_split  ->  p1_uci  ->  p1_quickdraw  ->  p2_uci  ->  p2_quickdraw  ->
  p3p4p5_uci  ->  p3p4p5_quickdraw  ->  summary
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import substrate_rs as srs
from domains import adaptive_bins as ab
from domains import ink_dynamics as idyn
from domains import stroke_programs as sp

SEP = "=" * 92
EPS = 1e-9

DATA_DIR = "/tmp/pendata"
UCI_MAT = os.path.join(DATA_DIR, "uci_chartraj", "mixoutALL_shifted.mat")
QD_CATEGORIES = ["circle", "square", "triangle", "zigzag", "line", "star"]
QD_FILES = {c: os.path.join(DATA_DIR, f"{c}_sample.ndjson") for c in QD_CATEGORIES}

CKPT_DIR = os.path.join(ROOT, "results", "run46_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)

PER_CALL_BUDGET_SECONDS = 460.0

# ------------------------------------------------------------------------------------------- #
# PRE-REGISTERED CONSTANTS (stated before any real-data number is computed; never re-tuned).
# ------------------------------------------------------------------------------------------- #
DK = dict(max_knots=16, segments=8, turn_bins=12, len_bins=6)   # byte-identical to the
                                                                  # Omniglot arc's own default
                                                                  # (run34d/run35's `gate.DK`,
                                                                  # OMNIGLOT_RICH_BINS unset).

QD_LOAD_CAP_PER_CAT = 700          # device_split: background sample size per category.
QD_SPLIT_HIST_BINS = 20
QD_SPLIT_FALLBACK = 0.35           # see module docstring's threshold-algorithm paragraph.

QD_P1_MAX_PER_SUBSET_PER_CAT = 400   # P1 tractability cap, per category per device subset.
P2_MAX_PER_CLASS = 40                # P2 Monte-Carlo tractability cap (UCI classes / QD cats).
P2_NULL_REPS = idyn.__dict__.get("DEFAULT_NULL_REPS", 100)  # ink_dynamics' own default (100).
P2_RNG_SEED = 20260706

P3_STROKE_CAP = 1500                 # QuickDraw touch-subset stroke cap (Omniglot's own
                                      # LEARN_STROKE_CAP convention), apportioned round-robin
                                      # across categories.

BAR_P1_R2_MULT = 3.0                 # >= 3x the cited Omniglot-mouse 0.084 -> 0.252.
BAR_P1_R2_CITED_MOUSE = 0.084
BAR_P1_SLOPE_LO, BAR_P1_SLOPE_HI = -0.45, -0.20
BAR_P1_MOUSE_GUARD_LO, BAR_P1_MOUSE_GUARD_HI = 0.04, 0.16

BAR_P3_MIN_IDENTITIES = 10
BAR_P3_EXCESS_FACTOR = 2.0
BAR_P4_EXCESS_FACTOR = 2.0


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


def _f(x, spec: str = ".4f") -> str:
    """Safe numeric formatter -- prints 'None' instead of raising on a legitimate `None`
    (e.g. an agreement/null computation with too few usable instances), never crashes a report."""
    if x is None:
        return "None"
    return format(x, spec)


def wilson_ci(k: int, n: int, z: float = 1.959963984540054) -> tuple:
    """Copied verbatim (formula) from `scripts/jabberwock_omniglot_run34_mouse.py` lines
    ~141-148 -- the arc's own standard 95% Wilson interval."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((centre - adj) / denom, (centre + adj) / denom)


# ============================================================================================= #
#  LOADERS -- mechanical parsing, no decisions.
# ============================================================================================= #
def load_uci_samples(mat_path: str = UCI_MAT) -> list:
    """`mixout` (1, 2858) object array of (3, T) [xvel, yvel, force] -> per-sample dict with
    integrated position, real time (ms), raw velocity, and raw speed. See module docstring's
    UCI FORMAT paragraph -- structure verified by `--stage unit_sanity`, not assumed."""
    import scipy.io as sio
    d = sio.loadmat(mat_path)
    consts = d["consts"][0, 0]
    key = [str(k[0]) for k in consts["key"][0]]
    charlabels = consts["charlabels"][0]
    dt_s = float(consts["dt"][0, 0])          # seconds (0.005 -> 200Hz)
    mixout = d["mixout"]
    n = mixout.shape[1]
    out = []
    for idx in range(n):
        arr = np.asarray(mixout[0, idx], dtype=float)   # (3, T)
        vel_xy = arr[:2, :].T                           # (T, 2)
        force = arr[2, :]
        cls = key[int(charlabels[idx]) - 1]
        t_ms = np.arange(vel_xy.shape[0], dtype=float) * dt_s * 1000.0
        pos_xy = np.cumsum(vel_xy, axis=0) * dt_s
        speed = np.sqrt((vel_xy ** 2).sum(axis=1))
        out.append({"class": cls, "idx": idx, "pos_xy": pos_xy, "t_ms": t_ms,
                    "vel_xy": vel_xy, "speed": speed, "force": force, "dt_s": dt_s})
    return out


def load_quickdraw_drawings(path: str, limit: int = None) -> list:
    """One ndjson line -> `{"key_id", "word", "strokes": [(N,2) xy arrays], "t_ms": [(N,) per
    stroke]}`. A line that fails `json.loads` (the range-download truncated tail, or any other
    corruption) is silently skipped -- an honest partial-data floor, never a crash, never a
    silently-wrong parse (per module docstring)."""
    out = []
    n_bad = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                n_bad += 1
                continue
            drawing = obj.get("drawing")
            if not drawing:
                continue
            strokes_xy, strokes_t = [], []
            ok = True
            for st in drawing:
                if len(st) < 2 or len(st[0]) == 0:
                    ok = False
                    break
                strokes_xy.append(np.asarray([st[0], st[1]], dtype=float).T)
                t = np.asarray(st[2], dtype=float) if len(st) > 2 else \
                    np.arange(len(st[0]), dtype=float)
                strokes_t.append(t)
            if not ok:
                continue
            out.append({"key_id": obj.get("key_id"), "word": obj.get("word"),
                       "strokes_xy": strokes_xy, "strokes_t": strokes_t})
            if limit and len(out) >= limit:
                break
    return out, n_bad


def pooled_integer_delta_fraction(strokes_xy: list) -> float:
    """`mouse_model.integer_delta_fraction`'s own formula, applied PER STROKE then pooled
    (never across a pen-up gap between two strokes -- a cross-stroke jump is not a real
    consecutive-sample delta and would contaminate the device diagnostic with an arbitrary
    large-jump fractional part). Returns 0.0 (honest floor) if no stroke has >= 2 points."""
    deltas = []
    for s in strokes_xy:
        if s.shape[0] < 2:
            continue
        d = np.diff(s[:, :2], axis=0).flatten()
        deltas.append(d)
    if not deltas:
        return 0.0
    d = np.concatenate(deltas)
    if d.size == 0:
        return 0.0
    return float(np.mean(np.abs(d - np.round(d)) < 1e-6))


def _find_split_threshold(fracs: list, n_bins: int = QD_SPLIT_HIST_BINS,
                          fallback: float = QD_SPLIT_FALLBACK) -> dict:
    """Pre-registered ALGORITHM (module docstring): valley between the two largest histogram
    peaks; falls back to a fixed constant if the distribution isn't resolvably bimodal.
    BOUNDARY BINS (0 and n_bins-1) ARE ELIGIBLE PEAK CANDIDATES -- a fraction-of-integer-deltas
    histogram over [0,1] is a priori just as likely to have its dominant modes AT the domain
    edges (frac~0: no grid structure at all; frac~1: everything on the integer grid) as in the
    interior, and a peak-finder that structurally excludes the two boundary bins would silently
    mis-detect exactly this (verified: this run's own real QuickDraw histogram IS boundary-
    bimodal, see the device_split log) -- fixed before computing the real split, not tuned
    after seeing where the threshold landed."""
    arr = np.asarray(fracs, dtype=float)
    hist, edges = np.histogram(arr, bins=n_bins, range=(0.0, 1.0))
    peaks = []
    for i in range(n_bins):
        if hist[i] <= 0:
            continue
        left_ok = (i == 0) or (hist[i] >= hist[i - 1])
        right_ok = (i == n_bins - 1) or (hist[i] >= hist[i + 1])
        if left_ok and right_ok:
            peaks.append(i)
    method = "fallback"
    thresh = fallback
    if len(peaks) >= 2:
        top2 = sorted(sorted(peaks, key=lambda i: -hist[i])[:2])
        lo, hi = top2
        if hi - lo >= 2:
            valley_i = lo + int(np.argmin(hist[lo:hi + 1]))
            thresh = float((edges[valley_i] + edges[valley_i + 1]) / 2.0)
            method = "valley"
    return {"threshold": thresh, "method": method,
            "histogram": hist.tolist(), "edges": edges.tolist()}


# ============================================================================================= #
#  STAGE: unit_sanity
# ============================================================================================= #
def stage_unit_sanity():
    print(f"\n{SEP}\n  STAGE: unit_sanity\n{SEP}")
    ok_all = True

    # (a) UCI round-trip.
    print("\n  (a) UCI loader round-trip")
    samples = load_uci_samples()
    print(f"      n_samples={len(samples)}  classes={sorted(set(s['class'] for s in samples))}")
    s0 = samples[0]
    t = s0["t_ms"]
    monotone = bool(np.all(np.diff(t) > 0))
    dt_uniform = bool(np.allclose(np.diff(t), t[1] - t[0]))
    extent = s0["pos_xy"].max(axis=0) - s0["pos_xy"].min(axis=0)
    sane_extent = bool(np.all(extent > 1e-3) and np.all(extent < 1e4) and
                       bool(np.all(np.isfinite(s0["pos_xy"]))))
    print(f"      sample0: class={s0['class']!r} n={len(t)}  dt_ms={t[1]-t[0]:.3f}  "
          f"monotone_time={monotone}  uniform_dt={dt_uniform}  extent_xy={extent}  "
          f"sane_extent={sane_extent}")
    ok_a = monotone and dt_uniform and sane_extent
    print(f"      -> {'PASS' if ok_a else 'FAIL'}")
    ok_all &= ok_a

    # (b) QuickDraw ndjson parse.
    print("\n  (b) QuickDraw ndjson parser")
    draws, n_bad = load_quickdraw_drawings(QD_FILES["circle"], limit=20)
    d0 = draws[0]
    shapes_ok = all(s.ndim == 2 and s.shape[1] == 2 for s in d0["strokes_xy"])
    t_ok = all(len(t_) == s.shape[0] for t_, s in zip(d0["strokes_t"], d0["strokes_xy"]))
    print(f"      loaded n={len(draws)}  n_bad_lines={n_bad}  key_id={d0['key_id']}  "
          f"n_strokes={len(d0['strokes_xy'])}  shapes_ok={shapes_ok}  t_len_ok={t_ok}")
    ok_b = shapes_ok and t_ok and len(draws) > 0
    print(f"      -> {'PASS' if ok_b else 'FAIL'}")
    ok_all &= ok_b

    # (c) integer_delta_fraction discriminator sanity.
    print("\n  (c) integer_delta_fraction discriminator sanity")
    from domains import mouse_model as mm
    all_int_trace = np.array([[float(i), float(2 * i)] for i in range(30)])
    rng = np.random.default_rng(0)
    subpixel_trace = np.cumsum(rng.uniform(0.1, 0.9, size=(30, 2)), axis=0)
    frac_int = mm.integer_delta_fraction(all_int_trace)
    frac_float = mm.integer_delta_fraction(subpixel_trace)
    print(f"      all-integer-delta trace -> frac={frac_int:.4f} (expect ~1.0)")
    print(f"      sub-pixel-float trace    -> frac={frac_float:.4f} (expect ~0.0)")
    ok_c = frac_int > 0.99 and frac_float < 0.05
    print(f"      -> {'PASS' if ok_c else 'FAIL'}")
    ok_all &= ok_c

    print(f"\n{SEP}\n  UNIT SANITY: {'ALL PASS' if ok_all else 'SOME FAILED -- DO NOT PROCEED'}"
          f"\n{SEP}")
    _save_json({"ok_a_uci": ok_a, "ok_b_quickdraw": ok_b, "ok_c_classifier": ok_c,
               "ok_all": ok_all}, _ckpt("unit_sanity.json"))
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    return 0 if ok_all else 1


# ============================================================================================= #
#  STAGE: device_split
# ============================================================================================= #
def stage_device_split():
    print(f"\n{SEP}\n  STAGE: device_split (QuickDraw mouse vs touch)\n{SEP}")
    t0 = time.time()
    per_cat = {}
    pooled_fracs = []
    for cat in QD_CATEGORIES:
        draws, n_bad = load_quickdraw_drawings(QD_FILES[cat], limit=QD_LOAD_CAP_PER_CAT)
        fracs = [pooled_integer_delta_fraction(d["strokes_xy"]) for d in draws]
        per_cat[cat] = {"n": len(draws), "n_bad_lines": n_bad, "fracs": fracs}
        pooled_fracs.extend(fracs)
        print(f"  loaded {cat:10s} n={len(draws):4d}  n_bad_lines={n_bad}  "
              f"mean_frac={np.mean(fracs):.3f}  median_frac={np.median(fracs):.3f}")

    split = _find_split_threshold(pooled_fracs)
    thresh = split["threshold"]
    print(f"\n  POOLED histogram (20 bins, [0,1]): {split['histogram']}")
    print(f"  chosen threshold = {thresh:.4f}  (method={split['method']})")

    report = {"threshold": thresh, "threshold_method": split["method"],
             "histogram": split["histogram"], "histogram_edges": split["edges"],
             "per_category": {}}
    n_touch_total, n_mouse_total = 0, 0
    for cat in QD_CATEGORIES:
        fracs = np.asarray(per_cat[cat]["fracs"])
        n_touch = int((fracs < thresh).sum())
        n_mouse = int((fracs >= thresh).sum())
        n = len(fracs)
        lo, hi = wilson_ci(n_touch, n) if n else (0.0, 0.0)
        report["per_category"][cat] = {
            "n": n, "n_touch": n_touch, "n_mouse": n_mouse,
            "touch_frac": (n_touch / n) if n else 0.0,
            "touch_frac_wilson_ci": [lo, hi],
            "mean_frac": float(np.mean(fracs)) if n else None,
            "median_frac": float(np.median(fracs)) if n else None,
        }
        n_touch_total += n_touch
        n_mouse_total += n_mouse
        print(f"  {cat:10s} n={n:4d}  touch={n_touch:4d} ({100*n_touch/max(1,n):.1f}%, "
              f"95% CI [{100*lo:.1f},{100*hi:.1f}])  mouse={n_mouse:4d}")

    n_pooled = n_touch_total + n_mouse_total
    lo_p, hi_p = wilson_ci(n_touch_total, n_pooled)
    report["pooled"] = {"n": n_pooled, "n_touch": n_touch_total, "n_mouse": n_mouse_total,
                        "touch_frac": n_touch_total / max(1, n_pooled),
                        "touch_frac_wilson_ci": [lo_p, hi_p]}
    print(f"\n  POOLED: n={n_pooled}  touch={n_touch_total} "
          f"({100*n_touch_total/max(1,n_pooled):.1f}%, 95% CI [{100*lo_p:.1f},{100*hi_p:.1f}])  "
          f"mouse={n_mouse_total}")

    _save_json(report, _ckpt("device_split.json"))
    print(f"\n  saved -> {_ckpt('device_split.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [device_split wall time: {time.time()-t0:.1f}s]")
    return 0


def _load_device_split() -> dict:
    path = _ckpt("device_split.json")
    if not os.path.exists(path):
        raise SystemExit("WALL: run --stage device_split first.")
    return _load_json(path)


def _classify_qd(cat: str, thresh: float, cap: int) -> tuple:
    """Load a category's drawings, classify each by `pooled_integer_delta_fraction` against the
    stored threshold -- recomputed on demand (cheap) rather than persisting large membership
    lists, per this script's own design note."""
    draws, _n_bad = load_quickdraw_drawings(QD_FILES[cat], limit=cap)
    touch, mouse = [], []
    for d in draws:
        frac = pooled_integer_delta_fraction(d["strokes_xy"])
        (touch if frac < thresh else mouse).append(d)
    return touch, mouse


# ============================================================================================= #
#  P1 -- TWO-THIRDS POWER LAW.
# ============================================================================================= #
def two_thirds_fit_given_speed(pos_xy: np.ndarray, speed: np.ndarray, min_points: int = 5):
    """SECONDARY robustness cross-check (UCI only, see module docstring): regress the corpus's
    OWN already-smoothed speed channel against curvature computed from integrated positions,
    skipping `ink_dynamics.speed_profile`'s own re-differentiation. Same regression/formula as
    `ink_dynamics.two_thirds_fit`, only the speed SOURCE differs."""
    kappa = idyn.curvature_series(pos_xy)
    mask = (kappa[1:-1] > EPS) & (speed[1:-1] > EPS)
    if int(mask.sum()) < min_points:
        return None
    x = np.log(kappa[1:-1][mask])
    y = np.log(speed[1:-1][mask])
    slope, intercept = np.polyfit(x, y, 1)
    y_hat = slope * x + intercept
    ss_res = float(((y - y_hat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > EPS else (1.0 if ss_res <= EPS else 0.0)
    return {"slope": float(slope), "intercept": float(intercept), "r2": float(r2),
            "n": int(mask.sum())}


def _dist_report(vals: list) -> dict:
    arr = np.asarray([v for v in vals if v is not None], dtype=float)
    if arr.size == 0:
        return {"n": 0, "median": None, "q1": None, "q3": None, "mean": None}
    return {"n": int(arr.size), "median": float(np.median(arr)),
            "q1": float(np.percentile(arr, 25)), "q3": float(np.percentile(arr, 75)),
            "mean": float(np.mean(arr))}


def stage_p1_uci():
    print(f"\n{SEP}\n  STAGE: p1_uci (two-thirds power law, UCI pen data)\n{SEP}")
    t0 = time.time()
    samples = load_uci_samples()
    r2s_primary, slopes_primary = [], []
    r2s_secondary, slopes_secondary = [], []
    for s in samples:
        xyt = np.concatenate([s["pos_xy"], s["t_ms"][:, None]], axis=1)
        fit_a = idyn.two_thirds_fit(xyt)
        if fit_a is not None:
            r2s_primary.append(fit_a["r2"])
            slopes_primary.append(fit_a["slope"])
        fit_b = two_thirds_fit_given_speed(s["pos_xy"], s["speed"])
        if fit_b is not None:
            r2s_secondary.append(fit_b["r2"])
            slopes_secondary.append(fit_b["slope"])
    rep_primary_r2 = _dist_report(r2s_primary)
    rep_primary_slope = _dist_report(slopes_primary)
    rep_secondary_r2 = _dist_report(r2s_secondary)
    rep_secondary_slope = _dist_report(slopes_secondary)
    print(f"  n_samples={len(samples)}")
    print(f"  PRIMARY (comparable protocol, ink_dynamics.two_thirds_fit on integrated pos):")
    print(f"    r2:    n={rep_primary_r2['n']} median={_f(rep_primary_r2['median'])} "
          f"IQR=[{_f(rep_primary_r2['q1'])},{_f(rep_primary_r2['q3'])}]")
    print(f"    slope: n={rep_primary_slope['n']} median={_f(rep_primary_slope['median'])} "
          f"IQR=[{_f(rep_primary_slope['q1'])},{_f(rep_primary_slope['q3'])}]")
    print(f"  SECONDARY (direct given-velocity cross-check, no re-differentiation):")
    print(f"    r2:    n={rep_secondary_r2['n']} median={_f(rep_secondary_r2['median'])} "
          f"IQR=[{_f(rep_secondary_r2['q1'])},{_f(rep_secondary_r2['q3'])}]")
    print(f"    slope: n={rep_secondary_slope['n']} median={_f(rep_secondary_slope['median'])} "
          f"IQR=[{_f(rep_secondary_slope['q1'])},{_f(rep_secondary_slope['q3'])}]")

    bar_r2 = BAR_P1_R2_MULT * BAR_P1_R2_CITED_MOUSE
    cond_r2 = rep_primary_r2["median"] is not None and rep_primary_r2["median"] >= bar_r2
    cond_slope = (rep_primary_slope["median"] is not None and
                 BAR_P1_SLOPE_LO <= rep_primary_slope["median"] <= BAR_P1_SLOPE_HI)
    print(f"\n  P1-UCI bar: median r2 >= {bar_r2:.3f} -> "
          f"{'PASS' if cond_r2 else 'FAIL'} ({_f(rep_primary_r2['median'])})")
    print(f"  P1-UCI bar: median slope in [{BAR_P1_SLOPE_LO},{BAR_P1_SLOPE_HI}] -> "
          f"{'PASS' if cond_slope else 'FAIL'} ({_f(rep_primary_slope['median'])})")

    out = {"n_samples": len(samples), "primary": {"r2": rep_primary_r2, "slope": rep_primary_slope},
          "secondary_direct_velocity": {"r2": rep_secondary_r2, "slope": rep_secondary_slope},
          "bar_r2": bar_r2, "cond_r2": bool(cond_r2), "cond_slope": bool(cond_slope)}
    _save_json(out, _ckpt("p1_uci.json"))
    print(f"\n  saved -> {_ckpt('p1_uci.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [p1_uci wall time: {time.time()-t0:.1f}s]")
    return 0


def stage_p1_quickdraw():
    print(f"\n{SEP}\n  STAGE: p1_quickdraw (two-thirds power law, touch vs mouse-control)\n{SEP}")
    t0 = time.time()
    ds = _load_device_split()
    thresh = ds["threshold"]

    def _fit_subset(drawings):
        r2s, slopes = [], []
        for d in drawings:
            xyts = [np.concatenate([s, t[:, None]], axis=1)
                   for s, t in zip(d["strokes_xy"], d["strokes_t"]) if s.shape[0] >= 2]
            if not xyts:
                continue
            fit = idyn.pooled_two_thirds_fit(xyts)
            if fit is not None:
                r2s.append(fit["r2"])
                slopes.append(fit["slope"])
        return r2s, slopes

    touch_r2, touch_slope, mouse_r2, mouse_slope = [], [], [], []
    per_cat_report = {}
    for cat in QD_CATEGORIES:
        touch, mouse = _classify_qd(cat, thresh, QD_LOAD_CAP_PER_CAT)
        touch = touch[:QD_P1_MAX_PER_SUBSET_PER_CAT]
        mouse = mouse[:QD_P1_MAX_PER_SUBSET_PER_CAT]
        tr2, tsl = _fit_subset(touch)
        mr2, msl = _fit_subset(mouse)
        touch_r2 += tr2; touch_slope += tsl
        mouse_r2 += mr2; mouse_slope += msl
        per_cat_report[cat] = {"n_touch": len(touch), "n_mouse": len(mouse),
                               "touch_r2_median": float(np.median(tr2)) if tr2 else None,
                               "mouse_r2_median": float(np.median(mr2)) if mr2 else None}
        print(f"  {cat:10s} touch(n={len(touch):3d}) r2_median="
              f"{per_cat_report[cat]['touch_r2_median']}  mouse(n={len(mouse):3d}) r2_median="
              f"{per_cat_report[cat]['mouse_r2_median']}")

    rep_touch_r2 = _dist_report(touch_r2)
    rep_touch_slope = _dist_report(touch_slope)
    rep_mouse_r2 = _dist_report(mouse_r2)
    rep_mouse_slope = _dist_report(mouse_slope)
    print(f"\n  TOUCH  r2: n={rep_touch_r2['n']} median={_f(rep_touch_r2['median'])} "
          f"IQR=[{_f(rep_touch_r2['q1'])},{_f(rep_touch_r2['q3'])}]   "
          f"slope median={_f(rep_touch_slope['median'])}")
    print(f"  MOUSE  r2: n={rep_mouse_r2['n']} median={_f(rep_mouse_r2['median'])} "
          f"IQR=[{_f(rep_mouse_r2['q1'])},{_f(rep_mouse_r2['q3'])}]   "
          f"slope median={_f(rep_mouse_slope['median'])}")

    bar_r2 = BAR_P1_R2_MULT * BAR_P1_R2_CITED_MOUSE
    cond_r2 = rep_touch_r2["median"] is not None and rep_touch_r2["median"] >= bar_r2
    cond_slope = (rep_touch_slope["median"] is not None and
                 BAR_P1_SLOPE_LO <= rep_touch_slope["median"] <= BAR_P1_SLOPE_HI)
    guard_ok = (rep_mouse_r2["median"] is not None and
               BAR_P1_MOUSE_GUARD_LO <= rep_mouse_r2["median"] <= BAR_P1_MOUSE_GUARD_HI)
    print(f"\n  P1-QuickDraw bar: touch median r2 >= {bar_r2:.3f} -> "
          f"{'PASS' if cond_r2 else 'FAIL'} ({rep_touch_r2['median']})")
    print(f"  P1-QuickDraw bar: touch median slope in [{BAR_P1_SLOPE_LO},{BAR_P1_SLOPE_HI}] -> "
          f"{'PASS' if cond_slope else 'FAIL'} ({rep_touch_slope['median']})")
    print(f"  PROTOCOL GUARD: mouse median r2 in [{BAR_P1_MOUSE_GUARD_LO},"
          f"{BAR_P1_MOUSE_GUARD_HI}] -> {'PASS' if guard_ok else 'FAIL'} "
          f"({rep_mouse_r2['median']})")

    out = {"per_category": per_cat_report,
          "touch": {"r2": rep_touch_r2, "slope": rep_touch_slope},
          "mouse_control": {"r2": rep_mouse_r2, "slope": rep_mouse_slope},
          "bar_r2": bar_r2, "cond_r2": bool(cond_r2), "cond_slope": bool(cond_slope),
          "guard_ok": bool(guard_ok)}
    _save_json(out, _ckpt("p1_quickdraw.json"))
    print(f"\n  saved -> {_ckpt('p1_quickdraw.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [p1_quickdraw wall time: {time.time()-t0:.1f}s]")
    return 0


# ============================================================================================= #
#  P2 -- VELOCITY-MINIMA VS ARC-LENGTH-CORNER SEGMENTATION, count-matched.
# ============================================================================================= #
def _p2_class_block(instance_xyts: list, rng: np.random.Generator) -> dict:
    """One class's worth of per-instance (N,3) xyt arrays -> velocity-minima and arc-length
    knot sets, mean pairwise agreement + count-matched null, excess for each method."""
    vel_knots = [idyn.velocity_minima_knots(xyt) for xyt in instance_xyts]
    arc_knots = [idyn.arclength_corner_knots(xyt[:, :2]) for xyt in instance_xyts]
    vel_raw = idyn.mean_pairwise_agreement(vel_knots)
    arc_raw = idyn.mean_pairwise_agreement(arc_knots)
    vel_null = idyn.count_matched_null_agreement(vel_knots, n_reps=P2_NULL_REPS, rng=rng)
    arc_null = idyn.count_matched_null_agreement(arc_knots, n_reps=P2_NULL_REPS, rng=rng)
    vel_excess = (vel_raw["mean"] - vel_null) if (vel_raw["mean"] is not None and
                                                  vel_null is not None) else None
    arc_excess = (arc_raw["mean"] - arc_null) if (arc_raw["mean"] is not None and
                                                  arc_null is not None) else None
    return {"n_instances": len(instance_xyts),
           "vel_raw": vel_raw["mean"], "vel_null": vel_null, "vel_excess": vel_excess,
           "arc_raw": arc_raw["mean"], "arc_null": arc_null, "arc_excess": arc_excess}


def stage_p2_uci():
    print(f"\n{SEP}\n  STAGE: p2_uci (velocity-minima vs arc-length, count-matched)\n{SEP}")
    t0 = time.time()
    samples = load_uci_samples()
    by_class: dict = {}
    for s in samples:
        by_class.setdefault(s["class"], []).append(s)
    rng = np.random.default_rng(P2_RNG_SEED)

    per_class = {}
    vel_excesses, arc_excesses = [], []
    for cls, insts in sorted(by_class.items()):
        idxs = rng.choice(len(insts), size=min(P2_MAX_PER_CLASS, len(insts)), replace=False)
        sub = [insts[i] for i in idxs]
        xyts = [np.concatenate([s["pos_xy"], s["t_ms"][:, None]], axis=1) for s in sub]
        block = _p2_class_block(xyts, rng)
        per_class[cls] = block
        if block["vel_excess"] is not None:
            vel_excesses.append(block["vel_excess"])
        if block["arc_excess"] is not None:
            arc_excesses.append(block["arc_excess"])
        print(f"  class={cls:2s} n={block['n_instances']:3d}  "
              f"vel: raw={_f(block['vel_raw'])} null={_f(block['vel_null'])} "
              f"excess={_f(block['vel_excess'],'+.4f')}   "
              f"arc: raw={_f(block['arc_raw'])} null={_f(block['arc_null'])} "
              f"excess={_f(block['arc_excess'],'+.4f')}")

    mean_vel_excess = float(np.mean(vel_excesses)) if vel_excesses else None
    mean_arc_excess = float(np.mean(arc_excesses)) if arc_excesses else None
    reversal = (mean_vel_excess is not None and mean_arc_excess is not None and
               mean_vel_excess > mean_arc_excess)
    print(f"\n  MEAN excess-over-null across {len(per_class)} classes: "
          f"velocity={_f(mean_vel_excess,'+.4f')}  arc-length={_f(mean_arc_excess,'+.4f')}")
    print(f"  P2-UCI bar (velocity excess > arc-length excess, the reversal): "
          f"{'PASS' if reversal else 'FAIL'}")

    out = {"per_class": per_class, "mean_vel_excess": mean_vel_excess,
          "mean_arc_excess": mean_arc_excess, "reversal": bool(reversal)}
    _save_json(out, _ckpt("p2_uci.json"))
    print(f"\n  saved -> {_ckpt('p2_uci.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [p2_uci wall time: {time.time()-t0:.1f}s]")
    return 0


def stage_p2_quickdraw():
    print(f"\n{SEP}\n  STAGE: p2_quickdraw (velocity-minima vs arc-length, touch + mouse-control)\n{SEP}")
    t0 = time.time()
    ds = _load_device_split()
    thresh = ds["threshold"]
    rng = np.random.default_rng(P2_RNG_SEED + 1)

    def _subset_block(drawings, tag):
        # Use each drawing's FIRST stroke (consistent treatment across single- and
        # multi-stroke categories -- documented, see module docstring's P2 paragraph).
        xyts = []
        for d in drawings[:P2_MAX_PER_CLASS]:
            if not d["strokes_xy"] or d["strokes_xy"][0].shape[0] < 3:
                continue
            xyt = np.concatenate([d["strokes_xy"][0], d["strokes_t"][0][:, None]], axis=1)
            xyts.append(xyt)
        if len(xyts) < 3:
            return None
        return _p2_class_block(xyts, rng)

    per_cat_touch, per_cat_mouse = {}, {}
    vel_ex_touch, arc_ex_touch = [], []
    vel_ex_mouse, arc_ex_mouse = [], []
    for cat in QD_CATEGORIES:
        touch, mouse = _classify_qd(cat, thresh, QD_LOAD_CAP_PER_CAT)
        bt = _subset_block(touch, "touch")
        bm = _subset_block(mouse, "mouse")
        per_cat_touch[cat] = bt
        per_cat_mouse[cat] = bm
        if bt and bt["vel_excess"] is not None:
            vel_ex_touch.append(bt["vel_excess"]); arc_ex_touch.append(bt["arc_excess"])
        if bm and bm["vel_excess"] is not None:
            vel_ex_mouse.append(bm["vel_excess"]); arc_ex_mouse.append(bm["arc_excess"])
        print(f"  {cat:10s} TOUCH n={len(touch):4d}: "
              f"{('vel_excess=' + _f(bt['vel_excess'],'+.4f') + ' arc_excess=' + _f(bt['arc_excess'],'+.4f')) if bt else 'insufficient'}")
        print(f"  {cat:10s} MOUSE n={len(mouse):4d}: "
              f"{('vel_excess=' + _f(bm['vel_excess'],'+.4f') + ' arc_excess=' + _f(bm['arc_excess'],'+.4f')) if bm else 'insufficient'}")

    mean_vel_touch = float(np.mean(vel_ex_touch)) if vel_ex_touch else None
    mean_arc_touch = float(np.mean(arc_ex_touch)) if arc_ex_touch else None
    mean_vel_mouse = float(np.mean(vel_ex_mouse)) if vel_ex_mouse else None
    mean_arc_mouse = float(np.mean(arc_ex_mouse)) if arc_ex_mouse else None
    reversal_touch = (mean_vel_touch is not None and mean_arc_touch is not None and
                      mean_vel_touch > mean_arc_touch)
    guard_ordering = (mean_vel_mouse is not None and mean_arc_mouse is not None and
                      mean_arc_mouse > mean_vel_mouse)

    print(f"\n  TOUCH mean excess: velocity={mean_vel_touch}  arc-length={mean_arc_touch}  "
          f"reversal={'PASS' if reversal_touch else 'FAIL'}")
    print(f"  MOUSE mean excess: velocity={mean_vel_mouse}  arc-length={mean_arc_mouse}  "
          f"protocol-guard (arc>vel, run-33 ordering)={'PASS' if guard_ordering else 'FAIL'}")

    out = {"per_category_touch": per_cat_touch, "per_category_mouse": per_cat_mouse,
          "mean_vel_excess_touch": mean_vel_touch, "mean_arc_excess_touch": mean_arc_touch,
          "mean_vel_excess_mouse": mean_vel_mouse, "mean_arc_excess_mouse": mean_arc_mouse,
          "reversal_touch": bool(reversal_touch), "guard_ordering_mouse": bool(guard_ordering)}
    _save_json(out, _ckpt("p2_quickdraw.json"))
    print(f"\n  saved -> {_ckpt('p2_quickdraw.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [p2_quickdraw wall time: {time.time()-t0:.1f}s]")
    return 0


# ============================================================================================= #
#  P3/P4/P5 -- STROKE-GRAIN PROGRAM IDENTITY (run-35 protocol, verbatim semantics).
# ============================================================================================= #
def _entropy_block(idents: list) -> dict:
    non_degenerate = [i for i in idents if i != "∅"]
    rep = ab.entropy_report(non_degenerate)
    rep["n_degenerate"] = len(idents) - len(non_degenerate)
    return rep


def _coherence_block(records: list, key_fn) -> dict:
    """`records`: list of (ident, class, drawer). Mirrors
    `scripts/jabberwock_omniglot_run35_programs.py`'s own `_coherence_block` semantics
    verbatim: an identity is COHERENT iff some class it appears in was independently produced
    by >= 3 distinct drawers."""
    coherence: dict = {}
    for (ident, cls, drawer) in records:
        k = key_fn(ident)
        if k == "∅":
            continue
        slot = coherence.setdefault(k, {})
        drawers = slot.setdefault(cls, [])
        if drawer not in drawers:
            drawers.append(drawer)
    n_distinct = len(coherence)
    n_coherent = n_instance_only = 0
    for ident, classes in coherence.items():
        best = max((len(ds) for ds in classes.values()), default=0)
        if best >= 3:
            n_coherent += 1
        if best <= 1:
            n_instance_only += 1
    return {"n_distinct_ids": n_distinct, "n_coherent": n_coherent,
           "coherence_fraction": (n_coherent / n_distinct) if n_distinct else 0.0,
           "n_instance_only": n_instance_only,
           "instance_fraction": (n_instance_only / n_distinct) if n_distinct else 0.0}


def _match_fraction(groups: list) -> tuple:
    matched, total = 0, 0
    for members in groups:
        n = len(members)
        for i in range(n):
            for j in range(i + 1, n):
                total += 1
                if members[i] == members[j]:
                    matched += 1
    return matched, total


def _p1c_block(class_members: dict, rng: np.random.Generator, n_reps: int = 100) -> dict:
    groups = list(class_members.values())
    sizes = [len(g) for g in groups]
    matched, total = _match_fraction(groups)
    raw = (matched / total) if total else 0.0
    flat = [m for g in groups for m in g]
    null_fracs = []
    for _ in range(n_reps):
        perm = rng.permutation(flat).tolist()
        idx = 0
        shuffled = []
        for sz in sizes:
            shuffled.append(perm[idx:idx + sz])
            idx += sz
        m, t = _match_fraction(shuffled)
        if t:
            null_fracs.append(m / t)
    null_mean = float(np.mean(null_fracs)) if null_fracs else 0.0
    excess = raw - null_mean
    bar = (BAR_P4_EXCESS_FACTOR * null_mean) if null_mean > 0 else 0.0
    clears_bar = bool(excess > 0) if null_mean <= 0 else bool(raw >= bar)
    return {"n_classes": len(groups), "n_classes_with_pairs": sum(1 for g in groups if len(g) >= 2),
           "n_pairs": total, "n_matched": matched, "raw_fraction": raw,
           "null_mean": null_mean, "excess": excess, "bar": bar, "excess_clears_bar": clears_bar}


def _tokenize_population(stroke_points: list) -> tuple:
    """`stroke_points`: list of (points_xy, tag) where `tag` is caller-defined metadata carried
    through. Returns (records, delta_edges, level_edges, tol_deg) -- records is a list of
    (fine, coarse, tag). FRESH adaptive edges fit on THIS population (module docstring: never
    reuse Omniglot's edges)."""
    # gather LEARN span values for fresh adaptive edges (this corpus's own population).
    agent_for_gather = srs.Substrate()
    learn_values = ab.gather_learn_span_values(
        agent_for_gather, [p for (p, _tag) in stroke_points],
        segments=DK["segments"], max_knots=DK["max_knots"])
    edges = ab.compute_adaptive_edges(learn_values, turn_bins=DK["turn_bins"],
                                      len_bins=DK["len_bins"])
    level_edges = edges["turn_edges"]
    tol_deg = sp.tol_deg_from_edges(level_edges)

    # phase 1: tokenize + gather ramp deltas.
    per_stroke = []
    pooled_deltas = []
    n_degenerate = 0
    for (points, tag) in stroke_points:
        s = srs.Substrate()
        turn_seq = sp.stroke_turn_sequence(s, points, segments=DK["segments"],
                                           max_knots=DK["max_knots"])
        if not turn_seq:
            n_degenerate += 1
            per_stroke.append(([], tag))
            continue
        res = sp.tokenize_turn_sequence(turn_seq, tol_deg, level_edges, delta_edges=None)
        pooled_deltas.extend(res["raw_deltas"])
        per_stroke.append((res["promoted"], tag))

    delta_edges = sp.gather_delta_edges(pooled_deltas)

    records = []
    for (promoted, tag) in per_stroke:
        if not promoted:
            records.append(("∅", "∅", tag))
            continue
        tokens = sp.finalize_tokens(promoted, level_edges, delta_edges)
        records.append((sp.format_fine(tokens), sp.format_coarse(tokens), tag))
    return records, delta_edges, level_edges, tol_deg, n_degenerate


def stage_p3p4p5_uci():
    print(f"\n{SEP}\n  STAGE: p3p4p5_uci (stroke-grain program identity, pen data)\n{SEP}")
    t0 = time.time()
    samples = load_uci_samples()
    stroke_points = [(s["pos_xy"].tolist(), s["class"]) for s in samples]

    records, delta_edges, level_edges, tol_deg, n_degenerate = _tokenize_population(stroke_points)
    print(f"  n_strokes={len(records)}  n_degenerate={n_degenerate}  tol_deg={tol_deg:.4f}")
    print(f"  level_edges ({len(level_edges)-1} eff bins): {[round(v,2) for v in level_edges]}")
    print(f"  delta_edges ({len(delta_edges)-1} eff bins): {[round(v,2) for v in delta_edges]}")

    fine_idents = [r[0] for r in records]
    coarse_idents = [r[1] for r in records]
    p3_fine = _entropy_block(fine_idents)
    p3_coarse = _entropy_block(coarse_idents)
    print(f"\n  ENTROPY fine:   {p3_fine['entropy_bits']:.4f} bits  n_ids={p3_fine['n_families']} "
          f"top_share={p3_fine['top_family_share']:.4f}")
    print(f"  ENTROPY coarse: {p3_coarse['entropy_bits']:.4f} bits  "
          f"n_ids={p3_coarse['n_families']}  top_share={p3_coarse['top_family_share']:.4f}")
    print(f"  NOTE (UCI CAVEAT): class-grain coherence (P1b, >=3 distinct drawers) is "
          f"STRUCTURALLY UNMEASURABLE on UCI (single writer for the entire corpus) -- not "
          f"computed; reported as N/A, not as a vacuous 100%% figure.")

    class_members_fine: dict = {}
    class_members_coarse: dict = {}
    for (fine, coarse, cls) in records:
        class_members_fine.setdefault(cls, []).append(fine)
        class_members_coarse.setdefault(cls, []).append(coarse)
    rng_fine = np.random.default_rng(P2_RNG_SEED + 10)
    rng_coarse = np.random.default_rng(P2_RNG_SEED + 11)
    p1c_fine = _p1c_block(class_members_fine, rng_fine)
    p1c_coarse = _p1c_block(class_members_coarse, rng_coarse)
    print(f"\n  CONSISTENCY fine:   classes={p1c_fine['n_classes']} pairs={p1c_fine['n_pairs']} "
          f"raw={p1c_fine['raw_fraction']:.4f} null={p1c_fine['null_mean']:.4f} "
          f"excess={p1c_fine['excess']:.4f} clears_2x={p1c_fine['excess_clears_bar']}")
    print(f"  CONSISTENCY coarse: classes={p1c_coarse['n_classes']} "
          f"pairs={p1c_coarse['n_pairs']} raw={p1c_coarse['raw_fraction']:.4f} "
          f"null={p1c_coarse['null_mean']:.4f} excess={p1c_coarse['excess']:.4f} "
          f"clears_2x={p1c_coarse['excess_clears_bar']}")

    p3_cond_ids = p3_fine["n_families"] > BAR_P3_MIN_IDENTITIES
    p3_cond_consistency = p1c_fine["excess_clears_bar"]
    p3_pass = p3_cond_ids and p3_cond_consistency
    p4_pass = p1c_fine["excess_clears_bar"] or p1c_coarse["excess_clears_bar"]
    print(f"\n  P3-UCI bar (identities>{BAR_P3_MIN_IDENTITIES} AND fine consistency >=2x null): "
          f"{'PASS' if p3_pass else 'FAIL'}  (n_ids={p3_fine['n_families']}, "
          f"consistency_clears={p3_cond_consistency})")
    print(f"  P4-UCI bar (class-consistency >=2x null at EITHER grain): "
          f"{'PASS' if p4_pass else 'FAIL'}")
    print(f"  P5-UCI: IDENTICAL to P3 (every UCI sample is single-stroke, see UCI CAVEAT) -> "
          f"{'PASS' if p3_pass else 'FAIL'}")

    out = {"n_strokes": len(records), "n_degenerate": n_degenerate, "tol_deg": tol_deg,
          "level_edges": level_edges, "delta_edges": delta_edges,
          "p3_entropy": {"fine": p3_fine, "coarse": p3_coarse},
          "p1c_consistency": {"fine": p1c_fine, "coarse": p1c_coarse},
          "p3_pass": bool(p3_pass), "p4_pass": bool(p4_pass), "p5_pass": bool(p3_pass),
          "p1b_coherence": "N/A -- single writer for entire UCI corpus, see UCI CAVEAT"}
    _save_json(out, _ckpt("p3p4p5_uci.json"))
    print(f"\n  saved -> {_ckpt('p3p4p5_uci.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [p3p4p5_uci wall time: {time.time()-t0:.1f}s]")
    return 0


def stage_p3p4p5_quickdraw():
    print(f"\n{SEP}\n  STAGE: p3p4p5_quickdraw (stroke-grain program identity, touch subset)\n{SEP}")
    t0 = time.time()
    ds = _load_device_split()
    thresh = ds["threshold"]

    # gather touch-subset strokes, round-robin across categories up to P3_STROKE_CAP, tagged
    # by (category, key_id, single_stroke_drawing?) for later grouping.
    per_cat_touch = {}
    for cat in QD_CATEGORIES:
        touch, _mouse = _classify_qd(cat, thresh, QD_LOAD_CAP_PER_CAT)
        per_cat_touch[cat] = touch
        print(f"  {cat:10s} touch n={len(touch)}")

    stroke_points = []   # (points_xy_list, (cat, key_id, is_single_stroke_drawing))
    cap_per_cat = max(1, P3_STROKE_CAP // len(QD_CATEGORIES))
    for cat in QD_CATEGORIES:
        n_taken = 0
        for d in per_cat_touch[cat]:
            is_single = len(d["strokes_xy"]) == 1
            for st in d["strokes_xy"]:
                if st.shape[0] < 2:
                    continue
                stroke_points.append((st.tolist(), (cat, d["key_id"], is_single)))
                n_taken += 1
                if n_taken >= cap_per_cat:
                    break
            if n_taken >= cap_per_cat:
                break
    print(f"\n  n_strokes gathered (cap={P3_STROKE_CAP}, round-robin): {len(stroke_points)}")

    records, delta_edges, level_edges, tol_deg, n_degenerate = _tokenize_population(stroke_points)
    print(f"  n_degenerate={n_degenerate}  tol_deg={tol_deg:.4f}")

    # ---- P3: whole touch-subset ----
    fine_idents = [r[0] for r in records]
    coarse_idents = [r[1] for r in records]
    p3_fine = _entropy_block(fine_idents)
    p3_coarse = _entropy_block(coarse_idents)
    print(f"\n  P3 (whole touch subset) ENTROPY fine={p3_fine['entropy_bits']:.4f} bits "
          f"n_ids={p3_fine['n_families']}   coarse={p3_coarse['entropy_bits']:.4f} bits "
          f"n_ids={p3_coarse['n_families']}")

    fine_records = [(r[0], r[2][0], r[2][1]) for r in records]     # (ident, category, key_id)
    coarse_records = [(r[1], r[2][0], r[2][1]) for r in records]
    p1b_fine = _coherence_block(fine_records, key_fn=lambda x: x)
    p1b_coarse = _coherence_block(coarse_records, key_fn=lambda x: x)
    print(f"  P1b coherence fine:   {p1b_fine['n_coherent']}/{p1b_fine['n_distinct_ids']}="
          f"{p1b_fine['coherence_fraction']:.4f}   instance-only fraction="
          f"{p1b_fine['instance_fraction']:.4f}")
    print(f"  P1b coherence coarse: {p1b_coarse['n_coherent']}/{p1b_coarse['n_distinct_ids']}="
          f"{p1b_coarse['coherence_fraction']:.4f}   instance-only fraction="
          f"{p1b_coarse['instance_fraction']:.4f}")

    # class_members: one representative identity per drawing (first stroke encountered),
    # grouped by category -- consistent with P2's own "first stroke" convention.
    seen_drawing = set()
    class_members_fine: dict = {}
    class_members_coarse: dict = {}
    for (fine, coarse, tag) in records:
        cat, key_id, _is_single = tag
        dkey = (cat, key_id)
        if dkey in seen_drawing:
            continue
        seen_drawing.add(dkey)
        class_members_fine.setdefault(cat, []).append(fine)
        class_members_coarse.setdefault(cat, []).append(coarse)
    rng_fine = np.random.default_rng(P2_RNG_SEED + 20)
    rng_coarse = np.random.default_rng(P2_RNG_SEED + 21)
    p1c_fine = _p1c_block(class_members_fine, rng_fine)
    p1c_coarse = _p1c_block(class_members_coarse, rng_coarse)
    print(f"\n  P3/P4 CONSISTENCY (class=category) fine:   raw={p1c_fine['raw_fraction']:.4f} "
          f"null={p1c_fine['null_mean']:.4f} excess={p1c_fine['excess']:.4f} "
          f"clears_2x={p1c_fine['excess_clears_bar']}")
    print(f"  P3/P4 CONSISTENCY (class=category) coarse: raw={p1c_coarse['raw_fraction']:.4f} "
          f"null={p1c_coarse['null_mean']:.4f} excess={p1c_coarse['excess']:.4f} "
          f"clears_2x={p1c_coarse['excess_clears_bar']}")

    p3_cond_ids = p3_fine["n_families"] > BAR_P3_MIN_IDENTITIES
    p3_pass = p3_cond_ids and p1c_fine["excess_clears_bar"]
    p4_pass = p1c_fine["excess_clears_bar"] or p1c_coarse["excess_clears_bar"]
    print(f"\n  P3-QuickDraw bar: {'PASS' if p3_pass else 'FAIL'}  "
          f"(n_ids={p3_fine['n_families']}, consistency_clears={p1c_fine['excess_clears_bar']})")
    print(f"  P4-QuickDraw bar: {'PASS' if p4_pass else 'FAIL'}")

    # ---- P5: single-stroke-drawing subset specifically ----
    single_records = [r for r in records if r[2][2]]
    print(f"\n  P5 single-stroke-drawing subset: n_strokes={len(single_records)} "
          f"(of {len(records)} total touch strokes)")
    if len(single_records) >= 20:
        p5_fine_idents = [r[0] for r in single_records]
        p5_entropy_fine = _entropy_block(p5_fine_idents)
        seen_d2 = set()
        p5_class_members_fine: dict = {}
        for (fine, _coarse, tag) in single_records:
            cat, key_id, _is_single = tag
            dkey = (cat, key_id)
            if dkey in seen_d2:
                continue
            seen_d2.add(dkey)
            p5_class_members_fine.setdefault(cat, []).append(fine)
        rng_p5 = np.random.default_rng(P2_RNG_SEED + 22)
        p5_p1c_fine = _p1c_block(p5_class_members_fine, rng_p5)
        p5_cond_ids = p5_entropy_fine["n_families"] > BAR_P3_MIN_IDENTITIES
        p5_pass = p5_cond_ids and p5_p1c_fine["excess_clears_bar"]
        print(f"  P5 entropy fine: {p5_entropy_fine['entropy_bits']:.4f} bits  "
              f"n_ids={p5_entropy_fine['n_families']}")
        print(f"  P5 consistency fine: raw={p5_p1c_fine['raw_fraction']:.4f} "
              f"null={p5_p1c_fine['null_mean']:.4f} excess={p5_p1c_fine['excess']:.4f} "
              f"clears_2x={p5_p1c_fine['excess_clears_bar']}")
        print(f"  P5-QuickDraw bar: {'PASS' if p5_pass else 'FAIL'}")
    else:
        p5_entropy_fine = None
        p5_p1c_fine = None
        p5_pass = None
        print(f"  P5-QuickDraw: INSUFFICIENT single-stroke-drawing touch data (n<20) -- NOT RUN")

    out = {"n_strokes": len(records), "n_degenerate": n_degenerate, "tol_deg": tol_deg,
          "p3_entropy": {"fine": p3_fine, "coarse": p3_coarse},
          "p1b_coherence": {"fine": p1b_fine, "coarse": p1b_coarse},
          "p1c_consistency": {"fine": p1c_fine, "coarse": p1c_coarse},
          "p3_pass": bool(p3_pass), "p4_pass": bool(p4_pass),
          "p5": {"n_single_stroke_strokes": len(single_records),
                "entropy_fine": p5_entropy_fine, "consistency_fine": p5_p1c_fine,
                "p5_pass": p5_pass}}
    _save_json(out, _ckpt("p3p4p5_quickdraw.json"))
    print(f"\n  saved -> {_ckpt('p3p4p5_quickdraw.json')}")
    print(f"  donkey=0: {'PASS' if _donkey0() else 'FAIL'}")
    print(f"  [p3p4p5_quickdraw wall time: {time.time()-t0:.1f}s]")
    return 0


# ============================================================================================= #
#  STAGE: summary -- reads every checkpoint, prints the pre-registered scoreboard.
# ============================================================================================= #
def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 46 PREDICTION SCOREBOARD\n{SEP}")
    needed = ["unit_sanity.json", "device_split.json", "p1_uci.json", "p1_quickdraw.json",
             "p2_uci.json", "p2_quickdraw.json", "p3p4p5_uci.json", "p3p4p5_quickdraw.json"]
    missing = [n for n in needed if not os.path.exists(_ckpt(n))]
    if missing:
        print(f"  INCOMPLETE -- missing checkpoints: {missing}")
        print(f"  Re-invoke the corresponding --stage for each missing file, then re-run summary.")
        return 1
    data = {n: _load_json(_ckpt(n)) for n in needed}

    p1u, p1q = data["p1_uci.json"], data["p1_quickdraw.json"]
    p2u, p2q = data["p2_uci.json"], data["p2_quickdraw.json"]
    p345u, p345q = data["p3p4p5_uci.json"], data["p3p4p5_quickdraw.json"]

    print("\n  P1 (two-thirds power law):")
    print(f"    UCI (pen):      median r2={_f(p1u['primary']['r2']['median'])}  "
          f"median slope={_f(p1u['primary']['slope']['median'])}  "
          f"-> r2_bar={'PASS' if p1u['cond_r2'] else 'FAIL'}  "
          f"slope_bar={'PASS' if p1u['cond_slope'] else 'FAIL'}")
    print(f"    QD touch:       median r2={p1q['touch']['r2']['median']}  "
          f"median slope={p1q['touch']['slope']['median']}  "
          f"-> r2_bar={'PASS' if p1q['cond_r2'] else 'FAIL'}  "
          f"slope_bar={'PASS' if p1q['cond_slope'] else 'FAIL'}")
    print(f"    QD mouse-ctrl:  median r2={p1q['mouse_control']['r2']['median']}  "
          f"-> guard={'PASS' if p1q['guard_ok'] else 'FAIL'}")

    print("\n  P2 (velocity-minima vs arc-length, count-matched excess):")
    print(f"    UCI (pen):  vel_excess={_f(p2u['mean_vel_excess'],'+.4f')}  "
          f"arc_excess={_f(p2u['mean_arc_excess'],'+.4f')}  "
          f"reversal={'PASS' if p2u['reversal'] else 'FAIL'}")
    print(f"    QD touch:   vel_excess={p2q['mean_vel_excess_touch']}  "
          f"arc_excess={p2q['mean_arc_excess_touch']}  "
          f"reversal={'PASS' if p2q['reversal_touch'] else 'FAIL'}")
    print(f"    QD mouse:   vel_excess={p2q['mean_vel_excess_mouse']}  "
          f"arc_excess={p2q['mean_arc_excess_mouse']}  "
          f"guard(arc>vel)={'PASS' if p2q['guard_ordering_mouse'] else 'FAIL'}")

    print("\n  P3 (stroke-grain identity revival):")
    print(f"    UCI (pen): n_ids(fine)={p345u['p3_entropy']['fine']['n_families']}  "
          f"consistency_excess={p345u['p1c_consistency']['fine']['excess']:.4f}  "
          f"-> {'PASS' if p345u['p3_pass'] else 'FAIL'}")
    print(f"    QD touch:  n_ids(fine)={p345q['p3_entropy']['fine']['n_families']}  "
          f"consistency_excess={p345q['p1c_consistency']['fine']['excess']:.4f}  "
          f"-> {'PASS' if p345q['p3_pass'] else 'FAIL'}")

    print("\n  P4 (coarse program-types clear 2.0x null):")
    print(f"    UCI (pen): {'PASS' if p345u['p4_pass'] else 'FAIL'}")
    print(f"    QD touch:  {'PASS' if p345q['p4_pass'] else 'FAIL'}")

    print("\n  P5 (per-stroke identity on single-stroke glyphs):")
    print(f"    UCI (pen): IDENTICAL to P3 -> {'PASS' if p345u['p5_pass'] else 'FAIL'}")
    p5q = p345q["p5"]
    print(f"    QD touch (single-stroke drawings only, n_strokes="
          f"{p5q['n_single_stroke_strokes']}): "
          f"{'PASS' if p5q['p5_pass'] else ('NOT RUN' if p5q['p5_pass'] is None else 'FAIL')}")

    print(f"\n  DEVICE SPLIT: threshold={data['device_split.json']['threshold']:.4f} "
          f"(method={data['device_split.json']['threshold_method']})  "
          f"pooled touch={data['device_split.json']['pooled']['touch_frac']:.4f}")

    print(f"\n{SEP}\n  RUN 46 COMPLETE -- see final agent report for full scoreboard + narrative."
          f"\n{SEP}")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True,
                  choices=["unit_sanity", "device_split", "p1_uci", "p1_quickdraw",
                          "p2_uci", "p2_quickdraw", "p3p4p5_uci", "p3p4p5_quickdraw",
                          "summary"])
    args = p.parse_args()
    fn = {"unit_sanity": stage_unit_sanity, "device_split": stage_device_split,
         "p1_uci": stage_p1_uci, "p1_quickdraw": stage_p1_quickdraw,
         "p2_uci": stage_p2_uci, "p2_quickdraw": stage_p2_quickdraw,
         "p3p4p5_uci": stage_p3p4p5_uci, "p3p4p5_quickdraw": stage_p3p4p5_quickdraw,
         "summary": stage_summary}[args.stage]
    return fn()


if __name__ == "__main__":
    sys.exit(main())
