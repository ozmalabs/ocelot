"""jabberwock_pose_read_run69.py -- RUN 69: RE-ADMIT POSE IN A WRITER-RELATIVE FRAME.

CURSIVE_PLAN.md step 2 (the highest-leverage, hardest step). Runs 62-67 floored cross-writer
cursive char reading at ~13-19% (run66 no-context 13.1%, run66/67 lexicon-collapse floor 18.6%)
using a ROTATION/SCALE-INVARIANT letter representation (`cc66.invariant` / StrokeQuantize's own
translate-start/rotate-initial-heading/arclen-1 normalization). Run 66's own honest diagnosis:
invariance DISCARDS pose/placement, and the separating signal that remains (same-letter DTW 0.205
vs different-letter 0.235) lives THERE. RESEARCH_CURSIVE.md's external calibration: the Bayesian
Action-Perception model (Gilet/Diard/Bessiere 2011, PLoS ONE), a training-free MOTOR-SIMULATION
cursive recognizer, scores 93.36% for a KNOWN writer and 49.68% for an UNKNOWN writer -- writer
ADAPTATION is the 50->93 lever, not per-letter recognizer strength in isolation.

THE HYPOTHESIS (pre-registered): re-admitting pose, scored in a WRITER-RELATIVE frame (baseline,
x-height, slant estimated from the writer's OWN ink -- closed-form, NOT a trained net), lifts
WITHIN-writer char accuracy toward BAP's 93% while CROSS-writer (no writer-specific info) stays
near the ~18-50% floor. This is BAP's "known writer" condition made operational.

THE WRITER FRAME (closed-form / donkey=0, Plamondon's virtual-target geometry made concrete):
  * BASELINE / TOPLINE are LOCAL, per line-instance, not writer-global constants -- DeepWriting's
    absolute coordinates are a per-SAMPLE integrated cumsum (`_abs_xy`), so they reset to an
    arbitrary origin at each ~300-point window; pooling raw y across DIFFERENT samples of one
    writer is meaningless (verified empirically: naive per-writer pooling gave nonsensical
    ascender/descender orderings; a corrected LOCAL, per-sample neighbor-window estimate does not).
    baseline = median(max_y) of the K nearest OTHER chars in the SAME sample (window);
    topline (x-height ceiling) = median(min_y) of the same neighbors. Sign convention (y increases
    DOWNWARD) empirically verified on n=800 real samples: ascender letters push their local min_y
    ~1.76 units BELOW the neighbor-median topline while their max_y matches baseline (median +0.01);
    descender letters push their max_y ~2.65 units BELOW baseline (in the more-positive/lower-page
    direction) while their min_y matches topline (median +0.28); x-height letters match both
    (median +/-0.04 to +0.30). See `local_baseline_topline`.
  * X-HEIGHT SCALE and SLANT are the genuinely WRITER-CHARACTERISTIC (adaptation) quantities --
    dimensionless/angle, so (unlike baseline) they CAN be pooled across a writer's many different
    samples/windows. `aggregate_scale_slant` computes the LOCAL x_height (baseline-topline) and a
    LOCAL slant deviation (median angle-from-vertical of near-vertical stroke segments -- classical
    chain-code slant estimation, Bozinovic & Srihari 1989) at every glyph instance, then takes the
    ROBUST MEDIAN over the whole pool -- closed-form throughout, no SGD.
  * TWO frame SOURCES for x_height/slant (the writer-adaptation lever): OWN (aggregated from the
    SAME writer's OTHER ink, excluding any sample that contains a selected test char) vs POPULATION
    (aggregated by pooling ALL background writers together -- a generic, writer-unaware default).
    Baseline/topline are ALWAYS local (a mechanical prerequisite for placing ink vertically at all,
    available even for a total stranger's line -- not itself a "writer adaptation" lever).

POSE CANON (the thing invariance discards, re-admitted): de-slant the glyph's points by the
frame's slant (a SHEAR, not a rotation -- keeps absolute page orientation, unlike `invariant()`'s
own-heading rotation which is per-instance idiosyncratic and destroys it), translate to the frame's
baseline + own entry-x, SCALE by x_height (writer-relative absolute size, NOT the letter's own
arc-length-normalized-to-1 as `invariant()` does), then arc-length resample to CANON_N points for
DTW alignment. This ONE representation folds in all four requested pose cues at once: vertical
extent relative to x-height (ascender/x-height/descender), key-point position relative to
baseline, slant-normalized shape, and aspect/width relative to x-height -- because they are all
just coordinates of the same normalized polyline. `invariant_canon` is run 66/67's OWN channel,
reused verbatim (`cc66.invariant`, first stroke only, their convention) -- pose is ADDED to it, not
a replacement (SCORE = invariant + lambda * pose, per-class costs each a min over that class's
bank exemplars, decoupled per channel then summed -- documented simplification, not a joint
per-exemplar optimum).

THE 5 CONDITIONS (fills the requested 2x2 + the frame-vs-bank diagnostic on ONE shared query set):
  A  INV_CROSS        invariant-only,      bank=CROSS (background writers)      [2x2: inv x cross]
  B  INV_WITHIN       invariant-only,      bank=OWN   (writer's own allographs) [2x2: inv x within]
  C  POSE_CROSS       invariant+pose,      frame=POPULATION, bank=CROSS         [2x2: pose x cross]
  D  POSE_FRAME_ONLY  invariant+pose,      frame=OWN,        bank=CROSS         [diagnostic]
  E  POSE_WITHIN      invariant+pose,      frame=OWN,        bank=OWN           [2x2: pose x within]
Ladder A -> B (bank alone) -> D (frame alone) -> E (both) decomposes writer-adaptation into its
two components, per the pre-registered diagnostic question.

GIVEN char segmentation (isolated glyphs via `extract_char_glyphs`, run 62's loader) -- isolates
the pose/frame question from segmentation, noted honestly (per CURSIVE_PLAN.md step 2's own scope).

PRE-REGISTERED: PRIMARY_LAMBDA = 1.0 (chosen before running, not tuned post-hoc); the fuller sweep
LAMBDAS=(0,0.5,1,2,4) is reported for transparency/robustness, not for cherry-picking a number.
WIN bar: E (within-writer, +pose) char accuracy > BAR_WITHIN_CHAR (40%) AND CI-separated above A
(cross-writer, invariant-only). NULL: pose doesn't lift within-writer -> pose isn't the
discriminative signal after all, or frame estimation is too unstable; report which, and whether
bank-alone (B) or frame-alone (D) drove any partial lift.

DISCIPLINE: donkey=0 -- every frame/pose primitive above is closed-form geometry (median,
percentile, shear, arclength resample), NOT an SGD-trained net; the DTW comparison is the SAME
held `DtwTo` Term run 66/67 use for their DECISION. SEED GUARD: OZMA_SEED_PERSIST_DISABLED=1,
md5(seeds/stroke_shapes.json) asserted UNCHANGED before/after every stage. run6*_checkpoints are
READ-ONLY (this script only READS cc66's dtw()/invariant() code, writes nothing there). NO git
add/commit.

Stages: prep (frame estimation + bank/query canon precompute, pure numpy, no native calls) ->
read (the DTW evaluation, needs substrate_rs, block-checkpointed) -> summary.
Run:
  OZMA_SEED_PERSIST_DISABLED=1 DEEPWRITING_DIR=/tmp/handwriting PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 scripts/jabberwock_pose_read_run69.py \\
    --stage <prep|read|summary>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict

os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
os.environ.setdefault("DEEPWRITING_DIR", "/tmp/handwriting")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

import scripts.jabberwock_wordread_run61 as r61
import scripts.jabberwock_cursive_curriculum_run66 as cc66
from domains import deepwriting_world as dww
from domains import glyph_motor_world as gmw

SEP = "=" * 92
CANON_N = cc66.CANON_N                            # 24, run 66/67's own canonical resample length.
STROKE_SHAPES_SEED = cc66.STROKE_SHAPES_SEED
CKPT_DIR = os.path.join(ROOT, "results", "run69_checkpoints")
LOG = os.path.join(ROOT, "results", "omniglot_gate_run69.log")
os.makedirs(CKPT_DIR, exist_ok=True)

SYMBOLS = dww.CANON_SYMBOLS
LOWER_CLASSES = list(range(10, 36))               # canonical 62-class ids for 'a'..'z'.

# ------------------------------------------------------------------------------------------- #
#  PRE-REGISTERED CONSTANTS.
# ------------------------------------------------------------------------------------------- #
SPLIT = "training"
WRITER_SPLIT_SEED = 20260706                      # byte-identical to run 62/64/66's own split.
N_BACKGROUND_FRAC = 0.5

LOCAL_WINDOW = 3                                  # +/- K neighbor chars for local baseline/topline.
M_BANK = 3                                        # exemplars per class (both cross- and own-bank).
N_TEST_TARGET = 340                               # >= 300 pre-reg.
TEST_SELECT_SEED = 20260720
BANK_SELECT_SEED = 20260721
PER_WRITER_CAP_MULT = 3                           # spread test chars across many held-out writers.

LAMBDAS = (0.0, 0.5, 1.0, 2.0, 4.0)               # pose-weight sweep (reported, not cherry-picked).
PRIMARY_LAMBDA = 1.0                               # pre-registered BEFORE running.
BIG = 1e6
PER_CALL_BUDGET_SECONDS = 480.0

# BAP (Gilet, Diard, Bessiere 2011) calibration numbers -- 26-way per-letter, cursive, motor model.
BAP_WITHIN = 93.36
BAP_CROSS = 49.68

# Pre-registered milestone bar (RUN 69 task spec: "within-writer char > 40-50%").
BAR_WITHIN_CHAR = 40.0
FLOOR_CHAR_REF = 18.6                             # run 66/67's own reported cross-writer floor.


# ============================================================================================= #
#  I/O + seed guard (identical pattern to runs 62-68).
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
#  GEOMETRY PRIMITIVES -- pure numpy, closed-form, NO native/substrate_rs calls (donkey=0).
# ============================================================================================= #
def _all_points(strokes) -> np.ndarray:
    """Concatenate every stroke of a glyph into one (N,2) point array (used for POSE -- vertical
    extent needs the WHOLE glyph incl. a t-crossbar/i-dot, unlike run66/67's invariant channel
    which by their own convention uses only the first/main stroke)."""
    return np.concatenate([np.asarray(s, float)[:, :2] for s in strokes], axis=0)


def _glyph_vextent(strokes):
    pts = _all_points(strokes)
    return float(pts[:, 1].min()), float(pts[:, 1].max())


def _steep_slant_devs(strokes) -> list:
    """Angle-from-vertical (degrees) of every near-vertical ('steep', |dy|>|dx|) point-to-point
    segment in a glyph. Direction-agnostic (uses abs(dy)) so it doesn't matter whether a stroke was
    drawn upward or downward -- classical chain-code slant estimation (Bozinovic & Srihari 1989)."""
    pts = _all_points(strokes)
    if len(pts) < 2:
        return []
    d = np.diff(pts, axis=0)
    out = []
    for dx, dy in d:
        if abs(dy) > abs(dx) and abs(dy) > 1e-6:
            out.append(math.degrees(math.atan2(dx, abs(dy))))
    return out


def local_baseline_topline(sample_glyphs_sorted: list, idx: int, window: int = LOCAL_WINDOW):
    """CLOSED-FORM LOCAL baseline/topline for the glyph at position `idx` in a list of glyphs from
    ONE sample (shared coordinate origin), sorted by char_idx: median(max_y) / median(min_y) of the
    `window` nearest OTHER chars either side (excludes self). y increases DOWNWARD -- empirically
    verified on n=800 real DeepWriting samples (ascenders push local min_y ~1.76 units below the
    neighbor topline while matching baseline; descenders push max_y ~2.65 units below baseline
    while matching topline; x-height letters match both within +/-0.3). Degenerate (no neighbors):
    falls back to the glyph's own extent (both baseline and topline collapse to its own range --
    the resulting frame has zero measured pose lift for THAT one instance, not a crash)."""
    exts = [_glyph_vextent(g["strokes"]) for g in sample_glyphs_sorted]
    lo, hi = max(0, idx - window), min(len(sample_glyphs_sorted), idx + window + 1)
    neigh = [exts[j] for j in range(lo, hi) if j != idx]
    if not neigh:
        mn, mx = exts[idx]
        return mx, mn
    mins = [e[0] for e in neigh]
    maxs = [e[1] for e in neigh]
    return float(np.median(maxs)), float(np.median(mins))    # (baseline, topline)


def aggregate_scale_slant(glyphs_by_sample: dict) -> dict:
    """The WRITER- (or POPULATION-) characteristic x_height / slant: the LOCAL x_height
    (baseline-topline) and LOCAL slant deviation are computed at EVERY glyph instance in the pool
    (closed-form, no identity needed), then the ROBUST MEDIAN over the whole pool is taken --
    donkey=0 (a percentile/median reduction, not an SGD fit). `glyphs_by_sample`: {sample_id:
    [glyphs sorted by char_idx]} -- samples with <4 chars are skipped (too few neighbors for a
    stable local estimate)."""
    xhs, slants = [], []
    n_glyphs = 0
    for gl in glyphs_by_sample.values():
        if len(gl) < 4:
            continue
        n_glyphs += len(gl)
        for i, g in enumerate(gl):
            base, top = local_baseline_topline(gl, i)
            xh = base - top
            if xh > 1e-6:
                xhs.append(xh)
            slants.extend(_steep_slant_devs(g["strokes"]))
    x_height = float(np.median(xhs)) if xhs else 1.0
    slant_deg = float(np.median(slants)) if slants else 0.0
    return {"x_height": x_height, "slant_deg": slant_deg, "n_glyphs": n_glyphs,
            "n_samples": len(glyphs_by_sample), "n_xh_obs": len(xhs), "n_slant_obs": len(slants)}


def deslant_points(pts: np.ndarray, slant_deg: float, baseline: float) -> np.ndarray:
    """De-slant by a horizontal SHEAR proportional to height above baseline (the standard HWR
    de-slant technique -- NOT a rotation: rotation would also re-orient the letter's absolute
    up/down extent, which is exactly the pose cue we want to KEEP; a shear removes only the
    writer's consistent lean)."""
    pts = np.asarray(pts, float)
    t = math.tan(math.radians(slant_deg))
    # inverse of the forward shear a slanted writer's ink exhibits (x_sheared = x_true +
    # t*(baseline - y), the SAME sign convention `_steep_slant_devs`'s atan2(dx, abs(dy)) recovers
    # -- verified: a synthetic line sheared by +slant_deg and de-slanted by the SAME +slant_deg
    # returns to zero horizontal variation, see tests/test_run69_migrated.py).
    x2 = pts[:, 0] + t * (pts[:, 1] - baseline)
    return np.stack([x2, pts[:, 1]], axis=1)


def pose_canon(strokes, baseline: float, x_height: float, slant_deg: float, n: int = CANON_N) -> list:
    """The WRITER-RELATIVE pose canon -- what `invariant()` discards, re-admitted: de-slant (shear)
    by the frame's slant, translate to (own entry-x, the frame's baseline), SCALE by x_height
    (writer-relative absolute size -- NOT the letter's own arc-length-normalized-to-1), then
    arc-length resample to `n` points. One representation folds in vertical extent relative to
    x-height, key-point position relative to baseline, slant-normalized shape, and aspect/width
    relative to x-height all at once (they are just coordinates of this one normalized polyline)."""
    pts = _all_points(strokes)
    ds = deslant_points(pts, slant_deg, baseline)
    xh = x_height or 1.0
    x0 = ds[0, 0]
    norm = np.stack([(ds[:, 0] - x0) / xh, (ds[:, 1] - baseline) / xh], axis=1)
    return gmw._resample_arclen(norm, n).tolist()


def invariant_canon(strokes) -> list:
    """Run 66/67's OWN rotation/scale-invariant channel, reused VERBATIM (`cc66.invariant`), on the
    FIRST stroke only (their own convention -- `cs["strokes"][0]` in run66/67's `_char_canon`).
    This is the channel that DISCARDS pose; pose is ADDED to it (SCORE = invariant + lambda*pose),
    never replaces it."""
    pts = np.asarray(strokes[0], float)
    return cc66.invariant(pts, CANON_N)               # already a plain list (sc._invariant_points).


# ============================================================================================= #
#  DATASET / WRITER-SPLIT / FRAME + BANK CONSTRUCTION  (pure numpy; the "prep" stage).
# ============================================================================================= #
def _group_by_writer(glyphs: list) -> dict:
    out = defaultdict(list)
    for g in glyphs:
        out[g["writer"]].append(g)
    return out


def _index_by_writer_sample(glyphs: list) -> dict:
    """{(writer, sample): [glyphs sorted by char_idx]} -- built ONCE, O(n); every local-frame
    lookup below is an O(1) dict hit into this index (never re-scans the full glyph list)."""
    out = defaultdict(list)
    for g in glyphs:
        out[(g["writer"], g["sample"])].append(g)
    for k in out:
        out[k].sort(key=lambda x: x["char_idx"])
    return out


def local_frame_of(g: dict, ws_index: dict):
    gl = ws_index[(g["writer"], g["sample"])]
    idx = next(i for i, x in enumerate(gl) if x["char_idx"] == g["char_idx"])
    return local_baseline_topline(gl, idx)


def glyphs_by_sample(glyph_list: list, exclude_samples: set | None = None) -> dict:
    exclude_samples = exclude_samples or set()
    out = defaultdict(list)
    for g in glyph_list:
        if g["sample"] not in exclude_samples:
            out[g["sample"]].append(g)
    for k in out:
        out[k].sort(key=lambda x: x["char_idx"])
    return out


def select_test_chars(by_writer: dict, ho_writers: set, target_n: int, seed: int) -> list:
    """Held-out (test) lowercase glyphs, seeded shuffle, capped per-writer so the test set spreads
    across MANY held-out writers rather than a few. Light dedupe by an approximate (writer, class,
    start-point, end-point, length) signature (safety net -- an empirical check on real
    DeepWriting found ZERO exact duplicates for even the busiest writer, but the corpus's windowed
    construction makes near-duplicates plausible in principle)."""
    pool = [g for g in ((w, gl) for w in ho_writers for gl in by_writer.get(w, []))
            if g[1]["class"] in LOWER_CLASSES]
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(pool))
    cap = max(4, (target_n // max(1, len(ho_writers))) * PER_WRITER_CAP_MULT)
    per_writer_count = Counter()
    seen_keys = set()
    selected = []
    for i in order:
        _, g = pool[int(i)]
        pts = np.asarray(g["strokes"][0], float)
        key = (g["writer"], g["class"], tuple(np.round(pts[0], 1)), tuple(np.round(pts[-1], 1)),
               len(pts))
        if key in seen_keys:
            continue
        if per_writer_count[g["writer"]] >= cap:
            continue
        seen_keys.add(key)
        selected.append(g)
        per_writer_count[g["writer"]] += 1
        if len(selected) >= target_n:
            break
    return selected


def select_bank(glyph_list: list, classes: list, M: int, rng) -> dict:
    by_class = defaultdict(list)
    for g in glyph_list:
        if g["class"] in classes:
            by_class[g["class"]].append(g)
    bank = {}
    for c in classes:
        insts = by_class.get(c, [])
        if not insts:
            bank[c] = []
            continue
        idx = rng.choice(len(insts), size=min(M, len(insts)), replace=False)
        bank[c] = [insts[int(i)] for i in idx]
    return bank


def _bank_canons(bank: dict, frame_of_writer: dict, ws_index: dict) -> dict:
    """{class: [{"inv": [...], "pose": [...]}]} -- each exemplar's pose canon uses ITS OWN
    writer's frame (`frame_of_writer[exemplar_writer]`); baseline is always local."""
    out = {}
    for c, insts in bank.items():
        recs = []
        for g in insts:
            fr = frame_of_writer[g["writer"]]
            baseline, _topline = local_frame_of(g, ws_index)
            recs.append({"inv": invariant_canon(g["strokes"]),
                         "pose": pose_canon(g["strokes"], baseline, fr["x_height"], fr["slant_deg"])})
        out[str(c)] = recs
    return out


def build_prep(target_n: int = N_TEST_TARGET, m_bank: int = M_BANK, dw=None, all_glyphs=None):
    """The full prep computation (pure numpy, no native calls). Returns the dict serialized to
    prep.json. `target_n`/`m_bank` are overridable (tests use small values for speed); `dw`/
    `all_glyphs` may be pre-loaded/pre-extracted by a caller that wants to reuse them across
    several small test builds without re-reading the corpus each time."""
    if dw is None:
        dw = dww.load_deepwriting(SPLIT)
    if all_glyphs is None:
        all_glyphs = dww.extract_char_glyphs(dw)
    words = dww.extract_words(dw, min_len=3, max_len=8, lowercase_only=True, complete_only=True)
    bg_words, ho_words = dww.writer_split(words, n_background_frac=N_BACKGROUND_FRAC,
                                          seed=WRITER_SPLIT_SEED)
    bg_writers = {w["writer"] for w in bg_words}
    ho_writers = {w["writer"] for w in ho_words}
    assert bg_writers.isdisjoint(ho_writers), "writer split must be disjoint"

    by_writer = _group_by_writer(all_glyphs)
    ws_index = _index_by_writer_sample(all_glyphs)

    test_chars = select_test_chars(by_writer, ho_writers, target_n, TEST_SELECT_SEED)
    test_writers = sorted({g["writer"] for g in test_chars})
    test_samples_by_writer = defaultdict(set)
    for g in test_chars:
        test_samples_by_writer[g["writer"]].add(g["sample"])

    # -- per-writer frames: OWN (test writers, excluding samples that contain a test char) + ALL
    #    background writers (no exclusion needed -- they never contribute a query char). --
    frame_of_writer = {}
    for w in test_writers:
        gbs = glyphs_by_sample(by_writer.get(w, []), exclude_samples=test_samples_by_writer[w])
        frame_of_writer[w] = aggregate_scale_slant(gbs)
    bg_glyphs_by_sample_all = {}
    for w in bg_writers:
        gbs = glyphs_by_sample(by_writer.get(w, []))
        frame_of_writer[w] = aggregate_scale_slant(gbs)
        bg_glyphs_by_sample_all.update(gbs)          # sample ids are GLOBAL -> no cross-writer clash.
    population_frame = aggregate_scale_slant(bg_glyphs_by_sample_all)

    # -- cross bank: M exemplars/class pooled across ALL background writers. --
    cross_pool = [g for w in bg_writers for g in by_writer.get(w, []) if g["class"] in LOWER_CLASSES]
    cross_bank_raw = select_bank(cross_pool, LOWER_CLASSES, m_bank,
                                 np.random.default_rng(BANK_SELECT_SEED))
    cross_bank = _bank_canons(cross_bank_raw, frame_of_writer, ws_index)

    # -- own bank per test writer: M exemplars/class from that writer's OTHER (test-excluded) ink.
    own_bank = {}
    own_bank_coverage = {}
    for w in test_writers:
        pool = [g for g in by_writer.get(w, []) if g["sample"] not in test_samples_by_writer[w]]
        raw = select_bank(pool, LOWER_CLASSES, m_bank, np.random.default_rng(BANK_SELECT_SEED + w))
        own_bank[str(w)] = _bank_canons(raw, frame_of_writer, ws_index)
        own_bank_coverage[str(w)] = {str(c): len(v) for c, v in raw.items()}

    # -- query canons: invariant + pose under BOTH the writer's OWN frame and the POPULATION frame.
    queries = []
    for qi, g in enumerate(test_chars):
        w = g["writer"]
        baseline, _topline = local_frame_of(g, ws_index)
        own_fr = frame_of_writer[w]
        rec = {
            "qid": qi, "writer": w, "true_class": g["class"], "symbol": g["symbol"],
            "baseline": baseline,
            "inv": invariant_canon(g["strokes"]),
            "pose_own": pose_canon(g["strokes"], baseline, own_fr["x_height"], own_fr["slant_deg"]),
            "pose_pop": pose_canon(g["strokes"], baseline, population_frame["x_height"],
                                   population_frame["slant_deg"]),
        }
        queries.append(rec)

    return {
        "bg_writers": sorted(bg_writers), "ho_writers": sorted(ho_writers),
        "test_writers": test_writers,
        "population_frame": population_frame,
        "writer_frames": {str(w): fr for w, fr in frame_of_writer.items()},
        "cross_bank": cross_bank,
        "own_bank": own_bank,
        "own_bank_coverage": own_bank_coverage,
        "queries": queries,
        "n_test_chars": len(test_chars),
        "n_test_writers": len(test_writers),
        "class_dist": dict(Counter(SYMBOLS[g["class"]] for g in test_chars)),
    }


def stage_prep():
    print(f"\n{SEP}\n  STAGE: prep (writer frames + cross/own bank + query canons -- pure numpy, "
          f"no native)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("prep")
    print(f"  seeds/stroke_shapes.json md5 (before): {md5_before}", flush=True)

    out = build_prep()
    out["stroke_shapes_md5"] = md5_before
    _save(out, _ckpt("prep.json"))
    _seed_guard("prep", md5_before)

    print(f"  bg writers={len(out['bg_writers'])}  ho writers={len(out['ho_writers'])}  "
          f"test writers={out['n_test_writers']}  test chars={out['n_test_chars']}", flush=True)
    print(f"  class dist (top 10): {Counter(out['class_dist']).most_common(10)}", flush=True)
    pf = out["population_frame"]
    print(f"  population frame: x_height={pf['x_height']:.3f} slant={pf['slant_deg']:.2f}deg "
          f"(n_glyphs={pf['n_glyphs']}, n_samples={pf['n_samples']})", flush=True)
    xhs = [fr["x_height"] for fr in out["writer_frames"].values()]
    sls = [fr["slant_deg"] for fr in out["writer_frames"].values()]
    print(f"  per-writer frames (n={len(xhs)}): x_height median={np.median(xhs):.3f} "
          f"range=[{min(xhs):.3f},{max(xhs):.3f}]  slant median={np.median(sls):.2f}deg "
          f"range=[{min(sls):.2f},{max(sls):.2f}]", flush=True)
    empty_own = sum(1 for cov in out["own_bank_coverage"].values()
                    for c, n in cov.items() if n == 0)
    print(f"  own-bank empty (writer,class) cells: {empty_own} / "
          f"{out['n_test_writers'] * len(LOWER_CLASSES)}", flush=True)
    print(f"  saved -> {_ckpt('prep.json')}  [prep {time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  STAGE: read -- THE DTW EVALUATION (needs substrate_rs). Block-checkpointed, resumable.
# ============================================================================================= #
def _class_cost(native, query_canon, bank_by_class: dict, key: str) -> list:
    """26-length cost vector (lower=better): entry[li] = min DTW over that class's bank exemplars'
    `key` canon ("inv" or "pose")."""
    vec = [BIG] * 26
    for c in LOWER_CLASSES:
        li = c - 10
        items = bank_by_class.get(str(c), [])
        if not items:
            continue
        best = min(cc66.dtw(native, query_canon, it[key]) for it in items)
        vec[li] = best
    return vec


def stage_read():
    print(f"\n{SEP}\n  STAGE: read -- MILESTONE (5-condition DTW evaluation)\n{SEP}", flush=True)
    t0 = time.time()
    md5_before = _seed_guard("read")
    import substrate_rs as srs
    native = srs.Substrate()._inner
    prep = _require("prep.json")
    cross_bank = prep["cross_bank"]
    own_bank = prep["own_bank"]
    queries = prep["queries"]

    out_path = _ckpt("read.json")
    state = _load(out_path) if os.path.exists(out_path) else {"records": [], "done": False}
    if state.get("done"):
        print(f"  read already COMPLETE (n={len(state['records'])}).", flush=True)
        return 0
    done = {r["qid"] for r in state["records"]}
    deadline = time.time() + PER_CALL_BUDGET_SECONDS
    n_new = 0

    for q in queries:
        if q["qid"] in done:
            continue
        w = str(q["writer"])
        ob = own_bank.get(w, {})
        invA = _class_cost(native, q["inv"], cross_bank, "inv")
        invB = _class_cost(native, q["inv"], ob, "inv")
        poseC = _class_cost(native, q["pose_pop"], cross_bank, "pose")
        poseD = _class_cost(native, q["pose_own"], cross_bank, "pose")
        poseE = _class_cost(native, q["pose_own"], ob, "pose")
        state["records"].append({
            "qid": q["qid"], "writer": q["writer"], "true_class": q["true_class"],
            "symbol": q["symbol"], "invA": invA, "invB": invB,
            "poseC": poseC, "poseD": poseD, "poseE": poseE,
        })
        n_new += 1
        if n_new % 15 == 0:
            _save(state, out_path)
            _seed_guard("read", md5_before)
            n = len(state["records"])
            a_ok = sum(1 for r in state["records"]
                      if (int(np.argmin(r["invA"])) + 10) == r["true_class"])
            e_ok = sum(1 for r in state["records"]
                      if int(np.argmin(np.asarray(r["invB"]) + PRIMARY_LAMBDA * np.asarray(r["poseE"])))
                      + 10 == r["true_class"])
            print(f"    ... {n}/{len(queries)}  A_char={100*a_ok/n:.1f}%  E_char(lam=1)="
                  f"{100*e_ok/n:.1f}%  [{time.time()-t0:.1f}s]", flush=True)
            if time.time() > deadline:
                _save(state, out_path)
                _seed_guard("read", md5_before)
                print(f"  WALL-BUDGET: {len(state['records'])}/{len(queries)} done -- re-invoke "
                      f"--stage read to resume.", flush=True)
                return 2

    state["done"] = True
    _save(state, out_path)
    _seed_guard("read", md5_before)
    print(f"  read {len(state['records'])} queries  [{time.time()-t0:.1f}s]", flush=True)
    return 0


# ============================================================================================= #
#  REPORTING / VERDICT.
# ============================================================================================= #
def _acc(records, key_fn):
    n = len(records)
    k = sum(1 for r in records if key_fn(r) == r["true_class"])
    return k, n


def _pred_inv(vec):
    return int(np.argmin(vec)) + 10


def _pred_mix(inv_vec, pose_vec, lam):
    return int(np.argmin(np.asarray(inv_vec) + lam * np.asarray(pose_vec))) + 10


def _row(label, k, n):
    ci = _wilson(k, n)
    pct = 100 * k / n if n else 0.0
    print(f"  {label:<42}{pct:>8.1f}%{f'[{100*ci[0]:.1f},{100*ci[1]:.1f}]':>15}{'n='+str(n):>10}")
    return pct, ci


def stage_summary():
    print(f"\n{SEP}\n  STAGE: summary -- RUN 69 SCOREBOARD (POSE IN A WRITER-RELATIVE FRAME)\n{SEP}",
          flush=True)
    md5_now = _seed_guard("summary")
    prep = _require("prep.json")
    print(f"  SEED-GUARD: seeds/stroke_shapes.json md5 = {md5_now}  "
          f"(== prep capture {prep['stroke_shapes_md5']}: {md5_now == prep['stroke_shapes_md5']})")
    rd = _require("read.json")
    if not rd.get("done"):
        print(f"  WALL: read not COMPLETE ({len(rd['records'])} so far) -- re-invoke --stage read.")
        return 1
    recs = rd["records"]
    n = len(recs)
    print(f"\n  n test chars = {n}  (writers: {prep['n_test_writers']}; "
          f"bg writers: {len(prep['bg_writers'])})")
    print(f"  BAP calibration: within-writer {BAP_WITHIN:.1f}%  cross-writer {BAP_CROSS:.1f}%  "
          f"(Gilet/Diard/Bessiere 2011, 26-way per-letter motor model)")
    print(f"  run 66/67's own cross-writer floor (different test set/method): {FLOOR_CHAR_REF:.1f}% "
          f"char (lexicon-aided); 13.1% char no-context")

    kA, _ = _acc(recs, lambda r: _pred_inv(r["invA"]))
    kB, _ = _acc(recs, lambda r: _pred_inv(r["invB"]))
    print(f"\n  === THE 2x2 (invariant-only vs +writer-relative-pose) x (cross- vs within-writer) "
          f"===  [pose rows @ PRIMARY_LAMBDA={PRIMARY_LAMBDA}]")
    hdr = f"  {'condition':<42}{'char_acc':>9}{'char_CI':>15}{'n':>10}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    pA = _row("A  INV_CROSS       (inv-only, cross bank)", kA, n)
    pB = _row("B  INV_WITHIN      (inv-only, own bank)", kB, n)
    kC, _ = _acc(recs, lambda r: _pred_mix(r["invA"], r["poseC"], PRIMARY_LAMBDA))
    kD, _ = _acc(recs, lambda r: _pred_mix(r["invA"], r["poseD"], PRIMARY_LAMBDA))
    kE, _ = _acc(recs, lambda r: _pred_mix(r["invB"], r["poseE"], PRIMARY_LAMBDA))
    pC = _row("C  POSE_CROSS      (+pose, pop frame, cross bank)", kC, n)
    pD = _row("D  POSE_FRAME_ONLY (+pose, OWN frame, cross bank) *diag*", kD, n)
    pE = _row("E  POSE_WITHIN     (+pose, OWN frame, own bank)", kE, n)

    print(f"\n  WRITER-ADAPTATION LADDER (char acc, decomposing the two components):")
    print(f"    A (no adaptation)            = {100*kA/n:5.1f}%")
    print(f"    B (own BANK alone)           = {100*kB/n:5.1f}%  (delta vs A: {100*(kB-kA)/n:+.1f})")
    print(f"    D (own FRAME alone, +pose)   = {100*kD/n:5.1f}%  (delta vs A: {100*(kD-kA)/n:+.1f})")
    print(f"    E (own frame+bank, +pose)    = {100*kE/n:5.1f}%  (delta vs A: {100*(kE-kA)/n:+.1f})")
    frame_alone = kD - kA
    bank_alone = kB - kA
    full = kE - kA
    driver = ("BANK is the dominant lever" if bank_alone > frame_alone + n * 0.02 else
             "FRAME is the dominant lever" if frame_alone > bank_alone + n * 0.02 else
             "frame and bank contribute comparably")
    print(f"    -> diagnostic: {driver} (bank-alone {100*bank_alone/n:+.1f}pp, "
          f"frame-alone {100*frame_alone/n:+.1f}pp, full {100*full/n:+.1f}pp)")

    print(f"\n  LAMBDA SWEEP (char acc; PRIMARY_LAMBDA={PRIMARY_LAMBDA} marked *; not cherry-picked):")
    hdr2 = f"  {'lambda':>8}{'C (pose+cross)':>18}{'D (frame-only)':>18}{'E (pose+within)':>18}"
    print(hdr2)
    for lam in LAMBDAS:
        kc, _ = _acc(recs, lambda r: _pred_mix(r["invA"], r["poseC"], lam))
        kd, _ = _acc(recs, lambda r: _pred_mix(r["invA"], r["poseD"], lam))
        ke, _ = _acc(recs, lambda r: _pred_mix(r["invB"], r["poseE"], lam))
        mark = "*" if lam == PRIMARY_LAMBDA else " "
        print(f"  {lam:>7.1f}{mark}{100*kc/n:>17.1f}%{100*kd/n:>17.1f}%{100*ke/n:>17.1f}%")

    # McNemar: does the FULL within-writer condition (E) beat the cross-writer floor (A)?
    fa = [_pred_inv(r["invA"]) == r["true_class"] for r in recs]
    fe = [_pred_mix(r["invB"], r["poseE"], PRIMARY_LAMBDA) == r["true_class"] for r in recs]
    mc_ea = r61._mcnemar(fa, fe)
    fd = [_pred_mix(r["invA"], r["poseD"], PRIMARY_LAMBDA) == r["true_class"] for r in recs]
    mc_ed = r61._mcnemar(fd, fe)
    fb = [_pred_inv(r["invB"]) == r["true_class"] for r in recs]
    mc_eb = r61._mcnemar(fb, fe)
    print(f"\n  McNemar (E vs A): fixed={mc_ea['fixed']} broken={mc_ea['broken']} p={mc_ea['p']:.3g}")
    print(f"  McNemar (E vs D -- own bank ON TOP OF own frame): fixed={mc_ed['fixed']} "
          f"broken={mc_ed['broken']} p={mc_ed['p']:.3g}")
    print(f"  McNemar (E vs B -- pose ON TOP OF own bank): fixed={mc_eb['fixed']} "
          f"broken={mc_eb['broken']} p={mc_eb['p']:.3g}")

    ciE = _wilson(kE, n)
    ciA = _wilson(kA, n)
    sep = (100 * ciE[0]) > (100 * ciA[1])
    win = (100 * kE / n > BAR_WITHIN_CHAR) and sep
    print(f"\n  MILESTONE (pre-registered bar: E char > {BAR_WITHIN_CHAR:.0f}% AND E CI-separated "
          f"above A):")
    print(f"    E (within-writer, +pose) = {100*kE/n:.1f}% CI[{100*ciE[0]:.1f},{100*ciE[1]:.1f}]  "
          f"(> {BAR_WITHIN_CHAR:.0f}%? {100*kE/n > BAR_WITHIN_CHAR})")
    print(f"    A (cross-writer, inv-only) = {100*kA/n:.1f}% CI[{100*ciA[0]:.1f},{100*ciA[1]:.1f}]  "
          f"separated? {sep}")
    a_pct, e_pct = 100 * kA / n, 100 * kE / n
    gap_closed = 100 * (e_pct - a_pct) / (BAP_WITHIN - a_pct) if BAP_WITHIN > a_pct else float("nan")
    print(f"    vs BAP: within {BAP_WITHIN:.1f}% / cross {BAP_CROSS:.1f}%  "
          f"(E closes {gap_closed:.0f}% of the A->BAP-within gap: ({e_pct:.1f}-{a_pct:.1f})/"
          f"({BAP_WITHIN:.1f}-{a_pct:.1f}))")
    print(f"    VERDICT: {'WIN -- writer-relative pose lifts within-writer reading toward BAP' if win else 'NULL -- writer-relative pose does not materially lift within-writer reading'}")
    print(f"\n{SEP}\n  RUN 69 COMPLETE -- see final agent report.\n{SEP}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=["prep", "read", "summary"])
    args = p.parse_args()
    return {"prep": stage_prep, "read": stage_read, "summary": stage_summary}[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
