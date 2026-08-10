"""OMNIGLOT RUN 39 GATE 0 -- THE MOTOR PLAN IS IMPLIED, NOT JUST THE INK.

THE CREATOR'S INSIGHT (2026-07-05, verbatim): "Mousewriting only registers the lines when the
button is depressed, but the mouse movement is encoded within." The button-UP half of the motor
program never touches the drawn line, but it is IMPLIED by the recorded data: stroke ORDER (motor
files record strokes in draw order), stroke DIRECTION (the point sequence within a stroke = which
end the writer started from), TRANSITION VECTORS (last point of stroke N -> first point of stroke
N+1 = the invisible pen-up travel), TRANSITION DURATIONS (the time column continues across BREAK
gaps -- `domains/omniglot_world.load_strokes_t`, landed run 33), and START POSITION (first
pen-down, normalized to the glyph frame). NONE of this has ever been used anywhere in this arc's
80.5% [76.3,84.1] verdict comparator (`abs_read.sctps_verdict_term`, a point-cloud comparator --
order/direction-blind by construction, RUN 16) or in the composed committed-shape signatures
(`domains/committed_shape.py` uses draw-order ARRANGEMENT relations but never direction,
transitions, or start position). RUN 36 (commit 5aa6bcb6) showed the verdict's own errors are
near-duplicate confusions on nearly identical GEOMETRY -- the motor plan is orthogonal evidence,
untried. BPL's stroke-order/direction priors are a named chunk of its 96.7 anchor. Motor
CONVENTIONS (start top-left, top-to-bottom strokes) are argued to be PLANNING-level, not
kinematic -- expected to survive the mouse effector, unlike run 33's momentum/velocity-minima
finding (which WAS a sensor artifact, run 34's diagnosis) and unlike run 32's turn-angle point
mass (also a sensor artifact, run 34).

THIS IS PURE MEASUREMENT -- the cheap-falsifier pattern of runs 33/35: no minting, no eval spend,
no LEARN, no teach(), no graph/agent code (CLAUDE.md: pure-numpy world-adapter/feature-extraction
code is the allowed class; this script and everything it imports stays in that class). It answers
one question per feature: does the SAME character, drawn by 20 DIFFERENT people, cohere on that
feature MORE than a count-matched, class-shuffled chance floor?

POPULATION (background split, LEARN alphabets quarantined): `ow.alphabets("background")[:5]` are
run 25/34's own LEARN_ALPHABETS_N=5 alphabets (`gate.LEARN_ALPHABETS_N`) -- excluded here so this
measurement never touches data any LEARN run has fit against. The next N_ALPHABETS=6 background
alphabets by sorted name (`ow.alphabets("background")[5:11]`) x N_CHARS_PER_ALPHABET=7 characters
each (first 7 by sorted character-dir name) = 42 characters, ALL 20 drawers each (840 files). The
10 evaluation alphabets (run 25/36's own N_TEST_ALPHABETS test set) are NEVER touched -- kept
quarantined for any later gate, per the launch brief.

PER-DRAWER LOAD: `ow.load_strokes_t(path, drop_degenerate=True)` (run 33's x,y,t parser + run
37C's degenerate-stroke filter, both ON per the launch brief). GLYPH FRAME: run-36's own
`_normalize_glyph` convention (center = mean of ALL the glyph's points across every stroke; scale
= max absolute deviation from center) -- NOT plain bbox; stated here because the brief allows
either. The normalized frame gives at least one axis exactly [-1,1] by construction, which is
also the fixed span the 3x3 START-POSITION grid is defined over (no per-drawer bbox recomputation
needed for the grid itself).

CANONICAL STROKE CORRESPONDENCE (per class, reused run-36 greedy matcher, THE FALSY-ZERO BUG
FIXED in this LOCAL copy, never in the read-only run-36 original): reference drawer = the drawer
with the class's own MODAL stroke count (ties broken by lowest drawer id); every other drawer
with that SAME stroke count is greedily matched to the reference stroke-by-stroke via the Rust
`PointSetDist` Term (whole-stroke point-cloud distance, cheapest-cost-first, no double-assignment
-- run 36's `_greedy_stroke_match`). THE FIX: run 36 read `float(native.evaluate(term, {}) or
float("nan"))` -- `or` treats an exact-zero distance (two literally identical strokes, e.g. this
script's own unit-test fixtures) as FALSY and silently replaces it with NaN, which would corrupt
the cheapest-cost-first ordering and could drop a genuine zero-cost match. This script's
`_pointset_cost` reads `v = native.evaluate(term, {}); float(v) if v is not None else nan` --
`None` (Rust-side "undefined", e.g. an empty point set) still maps to NaN, but 0.0 stays 0.0.
Drawers whose stroke count differs from the reference, or whose greedy match does not reach a
full bijection, are EXCLUDED from order/direction/transitions (counted, reported as an honest QC
number) but STILL contribute to START POSITION (which needs no correspondence at all).

FEATURES (each reduced to ONE categorical or bounded-continuous value per drawer per "group" --
see below):
  ORDER (canon_k>=2): the drawer's own draw-order sequence of REFERENCE-canonical stroke ids,
    e.g. reference draws (A,B,C) in that order -> canonical ids (0,1,2); a drawer who draws
    (C,A,B) has order tuple (2,0,1). EXACT metric: pairwise tuple equality. RELAXED metric:
    1 - normalized Kendall-tau distance (fraction of discordant pairs) between two drawers' order
    tuples -- an "adjacent-transposition" style partial-credit distance (swapping two adjacent
    strokes costs less than reversing the whole sequence).
  DIRECTION (canon_k>=1): per (class, canonical_stroke_id), does drawer X's matched stroke start
    from the SAME end as the reference's stroke? `polarity=1` if
    dist(drawer_start, ref_start) <= dist(drawer_start, ref_end), else `polarity=0` (reversed).
    Single-stroke classes need no correspondence at all (n=1 on both sides, trivial "match").
  START POSITION (canon_k>=1): first pen-down of the glyph's OWN first-drawn stroke, quantized to
    a 3x3 grid over the fixed [-1,1]^2 span of the run-36-normalized frame. Uses EVERY drawer of
    the class (no correspondence needed).
  TRANSITIONS (canon_k>=2): restricted to drawers whose FULL order tuple is IDENTICAL to the
    reference's (so canonical edge (ref_order[p], ref_order[p+1]) is the SAME motor event for
    every drawer in the group -- drawers with a different order are honestly excluded from this
    feature only, counted). Per (class, transition position p): the vector from the end of
    canonical stroke ref_order[p] to the start of canonical stroke ref_order[p+1], quantized to 8
    compass sectors (45-degree bins, sector 0 centred on 0 degrees / +x axis).
  TRANSITION DURATION (canon_k>=2, same restricted subset+positions as TRANSITIONS): the gap
    duration `t(start of stroke p+1) - t(end of stroke p)`, EXCLUDING any transition touching a
    fallback-timed stroke (`load_strokes_t`'s own `fallback_flags`, a non-monotone/missing-time
    stroke got a synthetic arc-length clock -- comparing ITS duration to a real one is comparing
    unlike units) and any transition whose raw duration is negative (a genuine cross-stroke clock
    glitch, reported as an anomaly, not silently kept or silently dropped uncounted). Usable
    durations are quantized into GLOBAL population TERTILES (fast/medium/slow), computed ONCE
    over every usable duration pooled across the whole sample BEFORE any per-class scoring, so
    every class's duration-bucket labels share one yardstick.

NULLS (mandatory, the run-33/35 law: report excess over a class-shuffled, count-matched null, not
raw score): every feature is bucketed by canonical stroke count `canon_k` (`1`,`2`,`3`,`4`,`5+`);
within a bucket, RAW is the MICRO-averaged pooled same-group-pair-agreement fraction (run 35's own
`_p1c_block`/`_match_fraction` convention: pool ALL same-group pairs across ALL groups in the
bucket, one raw fraction, not a macro-average of per-group fractions); NULL is the mean over
`N_NULL_REPS` reshuffles of group MEMBERSHIP within the bucket (values pooled and redealt into
groups of the SAME sizes, preserving stroke-count profile exactly by construction -- shuffling
only ever happens inside one bucket) of that SAME pooled-pair statistic; EXCESS = RAW - NULL. The
"ALL CLASSES" pooled row sums matched/total pairs across every bucket for RAW and pair-count-
weights each bucket's NULL by its own RAW pair count -- honest pooling, not a same-length
average, since order/direction/transitions/duration groups from different canon_k are literally
incomparable and must never be shuffled into each other.

PRE-REGISTERED VERDICT BARS (stated BEFORE any number below was computed):
  LIVE (per feature, run-35's own convention, `BAR_EXCESS_FACTOR=2.0`): `bar = 2 * null` when
  `null > 0`, and the feature is LIVE iff `raw >= bar`; when `null <= 0` (an honest edge case --
  a chance floor that happens to land at/below zero), LIVE iff `excess > 0` (any positive excess
  clears a non-positive bar). Anything else is DEAD.
  DESERT CHECK (the target population -- run 36's 1-2-stroke failure classes are the prize):
  on the pooled canon_k in {1,2} bucket, DIRECTION and START POSITION excess must ALSO clear the
  same LIVE bar computed WITHIN that pooled bucket (its own null, not borrowed from the ALL-
  CLASSES row) -- stated here as the SAME bar, not a separate weaker one, because a feature that
  is only live on multi-stroke classes does not help the desert this run is aimed at.
  Any LIVE feature (ALL-CLASSES or DESERT) licenses the run-39 FULL gate -- named per feature in
  the final report (proposal modality #4 and/or an additive verdict supplement, run-37A's
  supplement-only law) -- but that full gate is explicitly OUT OF SCOPE and NOT built by this
  script.

EXECUTION (ops law, binding): single foreground invocation, <=540s, `.venv` python (needs
`substrate_rs` for the `PointSetDist` Term), `stdbuf -oL ... | tee -a
results/omniglot_gate_run39.log`. Checkpoints under `results/run39_checkpoints/` only; every
other `run*_checkpoints/` dir and `seeds/stroke_shapes.json` are READ-ONLY / never touched (md5
of `seeds/stroke_shapes.json` recorded before and after, parallel-session-owned, per run
37a/37b/37c/38's own convention). No `git add`/`commit`. No minting, no `teach()`.

Run:
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python \\
      scripts/jabberwock_omniglot_run39_motorplan.py --stage gate0
  ... --stage report
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np

from domains import omniglot_world as ow

SEP = "=" * 92
CKPT_DIR = os.path.join(ROOT, "results", "run39_checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)

STROKE_SHAPES_PATH = os.path.join(ROOT, "seeds", "stroke_shapes.json")   # parallel-session-
                                                                          # owned; READ-ONLY,
                                                                          # never opened here --
                                                                          # md5 logged only.

# ---------------------------------------------------------------------------------------------
# Population.
# ---------------------------------------------------------------------------------------------
SPLIT = "background"
LEARN_ALPHABETS_N = 5            # cited verbatim from jabberwock_omniglot_dynamic_quantization.
N_ALPHABETS = 6
N_CHARS_PER_ALPHABET = 7         # 6 x 7 = 42 characters, all 20 drawers each.

# ---------------------------------------------------------------------------------------------
# Feature constants.
# ---------------------------------------------------------------------------------------------
GRID_N = 3                        # 3x3 start-position grid.
N_SECTORS = 8                     # 8-way transition-direction quantization.
N_DURATION_BUCKETS = 3            # fast / medium / slow tertiles.
BAR_EXCESS_FACTOR = 2.0           # run-35's own LIVE-bar convention.
N_NULL_REPS = 300                 # Monte Carlo reshuffle reps per bucket.
NULL_SEED = 20260705              # one fixed seed -- deterministic, reproducible reruns.


def _ckpt(name: str) -> str:
    return os.path.join(CKPT_DIR, name)


def _save_json(obj, path: str) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, default=str)


def _load_json(path: str):
    with open(path) as f:
        return json.load(f)


def _md5(path: str) -> str:
    if not os.path.exists(path):
        return "MISSING"
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _drawer_id(path: str) -> str:
    return path.split("/")[-1].split("_")[-1].replace(".txt", "")


# ===============================================================================================
# Population selection.
# ===============================================================================================
def select_characters():
    bg = ow.alphabets(SPLIT)
    learn = set(bg[:LEARN_ALPHABETS_N])
    non_learn = [a for a in bg if a not in learn]
    chosen_alphabets = non_learn[:N_ALPHABETS]
    char_dirs = []
    for a in chosen_alphabets:
        char_dirs.extend(sorted(ow.characters(a, SPLIT))[:N_CHARS_PER_ALPHABET])
    return chosen_alphabets, char_dirs


# ===============================================================================================
# Glyph-frame normalization (run-36 convention: center + abs-max scale over ALL points).
# ===============================================================================================
def normalize_glyph_xy(strokes_xy: list) -> list:
    allpts = np.concatenate(strokes_xy, axis=0)
    center = allpts.mean(0)
    scale = float(np.abs(allpts - center).max()) or 1e-9
    return [(s - center) / scale for s in strokes_xy]


def grid_cell(pt, n: int = GRID_N) -> tuple:
    """Quantize a point in the [-1,1]^2 normalized frame into an n x n grid cell."""
    def _bin(v):
        v = max(-1.0, min(1.0, v))
        # map [-1,1] -> [0, n) evenly, n-1 clamp for the v==1.0 edge.
        idx = int((v + 1.0) / 2.0 * n)
        return min(idx, n - 1)
    return (_bin(pt[0]), _bin(pt[1]))


def sector8(vec: np.ndarray, n: int = N_SECTORS) -> int:
    ang = float(np.degrees(np.arctan2(vec[1], vec[0])) % 360.0)
    width = 360.0 / n
    return int(((ang + width / 2.0) % 360.0) // width)


def _bucket_key(k: int) -> str:
    return str(k) if k < 5 else "5+"


# ===============================================================================================
# Canonical stroke correspondence -- greedy matcher, THE FALSY-ZERO BUG FIXED (see docstring).
# ===============================================================================================
def _pointset_cost(native, a: np.ndarray, b: np.ndarray) -> float:
    term = {"type": "PointSetDist",
            "a": {"type": "Lit", "value": a.tolist()},
            "b": {"type": "Lit", "value": b.tolist()}}
    v = native.evaluate(term, {})
    return float(v) if v is not None else float("nan")     # THE FIX -- never `or`.


def greedy_match(native, ref_strokes: list, other_strokes: list) -> dict:
    """Returns {other_stroke_idx -> reference_canonical_idx}, cheapest-cost-first, no
    double-assignment. May be a partial map if some costs are NaN (empty stroke) -- callers
    check `len(map) == len(ref_strokes) == len(other_strokes)` for a full bijection."""
    costs = {}
    for i, rs in enumerate(ref_strokes):
        for j, os_ in enumerate(other_strokes):
            costs[(i, j)] = _pointset_cost(native, rs, os_)
    order = sorted(costs.items(), key=lambda kv: (kv[1] != kv[1], kv[1]))   # NaN sorts last.
    used_i, used_j, mapping = set(), set(), {}
    for (i, j), c in order:
        if i in used_i or j in used_j or c != c:      # c != c <=> NaN.
            continue
        used_i.add(i)
        used_j.add(j)
        mapping[j] = i
    return mapping


def polarity(ref_stroke: np.ndarray, other_stroke: np.ndarray) -> int:
    ref_start, ref_end = ref_stroke[0], ref_stroke[-1]
    oth_start = other_stroke[0]
    d_start = float(np.linalg.norm(oth_start - ref_start))
    d_end = float(np.linalg.norm(oth_start - ref_end))
    return 1 if d_start <= d_end else 0


def kendall_tau_normalized(perm_a: tuple, perm_b: tuple) -> float:
    """Fraction of discordant pairs between two permutations of the SAME label set (0.0 =
    identical order, 1.0 = fully reversed pairwise)."""
    pos_a = {v: i for i, v in enumerate(perm_a)}
    pos_b = {v: i for i, v in enumerate(perm_b)}
    items = list(pos_a.keys())
    n = len(items)
    if n < 2:
        return 0.0
    discordant = 0
    total = 0
    for x in range(n):
        for y in range(x + 1, n):
            u, v = items[x], items[y]
            total += 1
            if (pos_a[u] < pos_a[v]) != (pos_b[u] < pos_b[v]):
                discordant += 1
    return discordant / total if total else 0.0


# ===============================================================================================
# Per-drawer load + per-class processing.
# ===============================================================================================
def load_class_drawers(cdir: str) -> list:
    """One entry per drawer file with >=1 usable (non-degenerate) stroke:
    {drawer, path, xy (normalized per-stroke point arrays), t (per-stroke raw/fallback time
    arrays), fallback (per-stroke bool), n_strokes}."""
    out = []
    for f in ow.drawings(cdir):
        strokes_xyt, fallback = ow.load_strokes_t(f, drop_degenerate=True)
        if not strokes_xyt:
            continue
        xy_raw = [s[:, :2] for s in strokes_xyt]
        t_raw = [s[:, 2] for s in strokes_xyt]
        xy_norm = normalize_glyph_xy(xy_raw)
        out.append(dict(drawer=_drawer_id(f), path=f, xy=xy_norm, t=t_raw,
                         fallback=fallback, n_strokes=len(xy_norm)))
    return out


def process_class(native, cdir: str) -> dict:
    """Everything this run measures about ONE character class, gathered in a single pass
    (duration BUCKET labels are assigned in a later global pass -- see `finalize_duration`)."""
    drawers = load_class_drawers(cdir)
    if len(drawers) < 2:
        return dict(cdir=cdir, drawers=drawers, canon_k=None, qc=dict(n_drawers=len(drawers)))

    counts = Counter(d["n_strokes"] for d in drawers)
    canon_k = counts.most_common(1)[0][0]
    modal_drawers = sorted([d for d in drawers if d["n_strokes"] == canon_k],
                            key=lambda d: d["drawer"])
    ref = modal_drawers[0]
    ref_order = tuple(range(canon_k))     # reference's own draw order IS the canonical labeling.

    per_drawer = []
    n_wrong_count = len(drawers) - len(modal_drawers)
    n_incomplete_match = 0
    for d in drawers:
        rec = dict(drawer=d["drawer"], n_strokes=d["n_strokes"],
                    start_cell=grid_cell(d["xy"][0][0]))
        if d["n_strokes"] != canon_k:
            rec["matched"] = False
            per_drawer.append(rec)
            continue
        if d is ref:
            mapping = {i: i for i in range(canon_k)}
        else:
            mapping = greedy_match(native, ref["xy"], d["xy"])
        if len(mapping) != canon_k:
            n_incomplete_match += 1
            rec["matched"] = False
            per_drawer.append(rec)
            continue
        rec["matched"] = True
        # order tuple: canonical id at each of THIS drawer's own draw positions 0..canon_k-1.
        rec["order"] = tuple(mapping[j] for j in range(canon_k))
        # direction: per canonical id, polarity of this drawer's matched stroke vs reference.
        rec["direction"] = {mapping[j]: polarity(ref["xy"][mapping[j]], d["xy"][j])
                             for j in range(canon_k)}
        if canon_k >= 2:
            # transitions only meaningful when this drawer's order == reference's order
            # (canonical edge identity is otherwise ambiguous -- see module docstring).
            rec["order_matches_ref"] = (rec["order"] == ref_order)
            if rec["order_matches_ref"]:
                transitions = []
                for p in range(canon_k - 1):
                    j_from, j_to = p, p + 1     # this drawer's own draw-position indices.
                    end_pt = d["xy"][j_from][-1]
                    start_pt = d["xy"][j_to][0]
                    vec = start_pt - end_pt
                    fb = d["fallback"][j_from] or d["fallback"][j_to]
                    dur = float(d["t"][j_to][0] - d["t"][j_from][-1])
                    transitions.append(dict(pos=p, sector=sector8(vec), duration=dur,
                                             fallback=bool(fb)))
                rec["transitions"] = transitions
        per_drawer.append(rec)

    return dict(cdir=cdir, canon_k=canon_k, ref_drawer=ref["drawer"],
                per_drawer=per_drawer,
                qc=dict(n_drawers=len(drawers), n_modal=len(modal_drawers),
                        n_wrong_count=n_wrong_count, n_incomplete_match=n_incomplete_match))


# ===============================================================================================
# Global duration-tertile edges (one pass over every usable transition duration, BEFORE any
# per-class duration-bucket scoring -- one shared yardstick, pre-registered as a measurement
# step, not a tuned parameter).
# ===============================================================================================
def collect_all_transition_durations(classes: list) -> list:
    durs = []
    for c in classes:
        if c["canon_k"] is None or c["canon_k"] < 2:
            continue
        for rec in c["per_drawer"]:
            if not rec.get("matched") or not rec.get("order_matches_ref"):
                continue
            for tr in rec.get("transitions", []):
                if tr["fallback"]:
                    continue
                durs.append(tr["duration"])
    return durs


def duration_edges(durs: list) -> tuple:
    if len(durs) < N_DURATION_BUCKETS:
        return None
    usable = [d for d in durs if d >= 0.0]
    if len(usable) < N_DURATION_BUCKETS:
        return None
    qs = np.linspace(0, 100, N_DURATION_BUCKETS + 1)[1:-1]
    return tuple(float(x) for x in np.percentile(usable, qs))


def duration_bucket(dur: float, edges: tuple) -> int:
    b = 0
    for e in edges:
        if dur > e:
            b += 1
    return b


# ===============================================================================================
# Feature-group extraction (per bucket = canonical stroke count "1"/"2"/"3"/"4"/"5+").
# ===============================================================================================
def build_groups(classes: list, edges) -> dict:
    """Returns groups[feature][bucket] = list of groups, each group a list of per-drawer
    values (order tuple / direction bit / grid cell tuple / sector int / duration bucket int)."""
    groups = {f: defaultdict(list) for f in
              ("order", "direction", "start", "transitions", "duration")}
    anomalies = dict(negative_duration=0, fallback_excluded_duration=0, n_duration_usable=0)

    for c in classes:
        if c["canon_k"] is None:
            continue
        k = c["canon_k"]
        bkt = _bucket_key(k)

        # START POSITION: every drawer of the class, correspondence not needed.
        start_vals = [rec["start_cell"] for rec in c["per_drawer"]]
        if len(start_vals) >= 2:
            groups["start"][bkt].append(start_vals)

        matched = [rec for rec in c["per_drawer"] if rec.get("matched")]

        # DIRECTION -- works for canon_k >= 1 (process_class already computed a 1-element
        # `direction` dict for single-stroke classes via the same generic matching path).
        if len(matched) >= 2:
            per_canon = defaultdict(list)
            for rec in matched:
                for cid, bit in rec["direction"].items():
                    per_canon[cid].append(bit)
            for cid, bits in per_canon.items():
                if len(bits) >= 2:
                    groups["direction"][bkt].append(bits)

        if k >= 2 and len(matched) >= 2:
            order_vals = [rec["order"] for rec in matched]
            groups["order"][bkt].append(order_vals)

            order_match_recs = [rec for rec in matched if rec.get("order_matches_ref")]
            if len(order_match_recs) >= 2:
                for p in range(k - 1):
                    sectors, durs = [], []
                    for rec in order_match_recs:
                        tr = rec["transitions"][p]
                        sectors.append(tr["sector"])
                        if tr["fallback"]:
                            anomalies["fallback_excluded_duration"] += 1
                            continue
                        if tr["duration"] < 0.0:
                            anomalies["negative_duration"] += 1
                            continue
                        if edges is not None:
                            durs.append(duration_bucket(tr["duration"], edges))
                            anomalies["n_duration_usable"] += 1
                    if len(sectors) >= 2:
                        groups["transitions"][bkt].append(sectors)
                    if len(durs) >= 2:
                        groups["duration"][bkt].append(durs)

    return groups, anomalies


# ===============================================================================================
# RAW / NULL / EXCESS -- run-35's own micro-averaged-pooled-pair-fraction convention
# (`_p1c_block`/`_match_fraction`), generalized to an arbitrary pairwise agreement score so the
# SAME machinery serves exact-categorical (order/direction/start/sector/duration-bucket) and the
# continuous relaxed-order metric.
# ===============================================================================================
def _pooled_pair_stat(groups: list, pair_score) -> tuple:
    total = 0
    ssum = 0.0
    for members in groups:
        n = len(members)
        for i in range(n):
            for j in range(i + 1, n):
                total += 1
                ssum += pair_score(members[i], members[j])
    return (ssum / total if total else None), total


def _shuffled_null(groups: list, pair_score, n_reps: int, rng) -> float | None:
    sizes = [len(g) for g in groups if len(g) >= 2]
    flat = [v for g in groups for v in g if len(g) >= 2]
    if len(flat) < 2 or not sizes:
        return None
    reps = []
    for _ in range(n_reps):
        idx = rng.permutation(len(flat))
        perm = [flat[k] for k in idx]
        pos = 0
        shuffled_groups = []
        for sz in sizes:
            shuffled_groups.append(perm[pos:pos + sz])
            pos += sz
        s, t = _pooled_pair_stat(shuffled_groups, pair_score)
        if s is not None:
            reps.append(s)
    return float(np.mean(reps)) if reps else None


def raw_null_excess(groups: list, pair_score, n_reps: int = N_NULL_REPS,
                     rng=None) -> dict:
    rng = rng if rng is not None else np.random.default_rng(NULL_SEED)
    raw, n_pairs = _pooled_pair_stat(groups, pair_score)
    null = _shuffled_null(groups, pair_score, n_reps, rng)
    excess = (raw - null) if (raw is not None and null is not None) else None
    if null is not None and null > 0:
        bar = BAR_EXCESS_FACTOR * null
        live = bool(raw is not None and raw >= bar)
    else:
        bar = 0.0
        live = bool(excess is not None and excess > 0)
    return dict(raw=raw, null=null, excess=excess, bar=bar, live=live,
                n_groups=len([g for g in groups if len(g) >= 2]), n_pairs=n_pairs)


_EQ_SCORE = lambda a, b: 1.0 if a == b else 0.0
_KENDALL_SCORE = lambda a, b: 1.0 - kendall_tau_normalized(a, b)


def pool_all_buckets(per_bucket: dict) -> dict:
    """Honest pooling across canon_k buckets: RAW sums matched/total pairs directly (each
    bucket's pairs are internally homogeneous-length, so pooling pair COUNTS is always valid);
    NULL is pair-count-weighted across buckets (each bucket's null was computed by shuffling
    ONLY within that bucket -- never mixed)."""
    raw_num = raw_den = null_weighted = 0.0
    any_raw = any_null = False
    for b, stat in per_bucket.items():
        if stat["raw"] is not None and stat["n_pairs"]:
            raw_num += stat["raw"] * stat["n_pairs"]
            raw_den += stat["n_pairs"]
            any_raw = True
            if stat["null"] is not None:
                null_weighted += stat["null"] * stat["n_pairs"]
                any_null = True
    raw = (raw_num / raw_den) if any_raw and raw_den else None
    null = (null_weighted / raw_den) if any_null and raw_den else None
    excess = (raw - null) if (raw is not None and null is not None) else None
    if null is not None and null > 0:
        bar = BAR_EXCESS_FACTOR * null
        live = bool(raw is not None and raw >= bar)
    else:
        bar = 0.0
        live = bool(excess is not None and excess > 0)
    return dict(raw=raw, null=null, excess=excess, bar=bar, live=live,
                n_pairs=int(raw_den), n_groups=sum(s["n_groups"] for s in per_bucket.values()))


def score_feature(groups_by_bucket: dict, pair_score, n_reps: int = N_NULL_REPS) -> dict:
    rng = np.random.default_rng(NULL_SEED)
    per_bucket = {}
    for bkt in ("1", "2", "3", "4", "5+"):
        gs = groups_by_bucket.get(bkt, [])
        if gs:
            per_bucket[bkt] = raw_null_excess(gs, pair_score, n_reps=n_reps, rng=rng)
    all_stat = pool_all_buckets(per_bucket) if per_bucket else dict(
        raw=None, null=None, excess=None, bar=0.0, live=False, n_pairs=0, n_groups=0)
    desert_buckets = {b: per_bucket[b] for b in ("1", "2") if b in per_bucket}
    desert_stat = pool_all_buckets(desert_buckets) if desert_buckets else dict(
        raw=None, null=None, excess=None, bar=0.0, live=False, n_pairs=0, n_groups=0)
    return dict(per_bucket=per_bucket, all=all_stat, desert=desert_stat)


# ===============================================================================================
# STAGE: gate0 -- run everything, print RAW/NULL/EXCESS tables, save checkpoint.
# ===============================================================================================
def stage_gate0() -> int:
    print(f"\n{SEP}\n  RUN 39 GATE 0 -- MOTOR-PLAN FEATURES (pure measurement)\n{SEP}")
    t0 = time.time()
    md5_before = _md5(STROKE_SHAPES_PATH)
    print(f"  seeds/stroke_shapes.json md5 (parallel-session-owned, this run never writes "
          f"there): {md5_before}")

    import substrate_rs as srs
    native = srs.Substrate()._inner

    alphabets, char_dirs = select_characters()
    print(f"  split={SPLIT}  LEARN alphabets excluded (first {LEARN_ALPHABETS_N}): "
          f"{ow.alphabets(SPLIT)[:LEARN_ALPHABETS_N]}")
    print(f"  sampled alphabets ({N_ALPHABETS}): {alphabets}")
    print(f"  characters sampled: {len(char_dirs)} ({N_CHARS_PER_ALPHABET}/alphabet), "
          f"all 20 drawers each -> up to {len(char_dirs) * 20} files")

    classes = []
    for cdir in char_dirs:
        classes.append(process_class(native, cdir))
    print(f"\n  {len(classes)} classes processed in {time.time() - t0:.1f}s")

    canon_ks = Counter(_bucket_key(c["canon_k"]) for c in classes if c["canon_k"] is not None)
    n_skipped = sum(1 for c in classes if c["canon_k"] is None)
    print(f"  canon_k distribution: {dict(sorted(canon_ks.items()))}  "
          f"(classes skipped, <2 usable drawers: {n_skipped})")
    tot_qc = defaultdict(int)
    for c in classes:
        if "qc" in c and "n_modal" in c["qc"]:
            for k, v in c["qc"].items():
                tot_qc[k] += v
    print(f"  QC totals (pooled over all classes): {dict(tot_qc)}")

    durs_all = collect_all_transition_durations(classes)
    edges = duration_edges(durs_all)
    print(f"\n  transition-duration pool: n={len(durs_all)}  "
          f"n_negative={sum(1 for d in durs_all if d < 0.0)}  "
          f"tertile edges (ms)={edges}")
    if durs_all:
        arr = np.asarray(durs_all, dtype=float)
        pos = arr[arr >= 0.0]
        print(f"  duration distribution (usable, >=0, ms): n={pos.size}  "
              f"mean={pos.mean():.1f}  median={np.median(pos):.1f}  "
              f"p10={np.percentile(pos,10):.1f}  p90={np.percentile(pos,90):.1f}  "
              f"max={pos.max():.1f}")

    groups, anomalies = build_groups(classes, edges)
    print(f"\n  duration anomalies: {anomalies}")

    features = {
        "order_exact": score_feature(groups["order"], _EQ_SCORE),
        "order_relaxed": score_feature(groups["order"], _KENDALL_SCORE),
        "direction": score_feature(groups["direction"], _EQ_SCORE),
        "start_position": score_feature(groups["start"], _EQ_SCORE),
        "transitions": score_feature(groups["transitions"], _EQ_SCORE),
        "transition_duration": score_feature(groups["duration"], _EQ_SCORE),
    }

    print(f"\n{SEP}\n  RAW / NULL / EXCESS -- per feature, per canon_k bucket\n{SEP}")
    header = f"  {'feature':<22}{'bucket':<8}{'raw':>8}{'null':>8}{'excess':>9}{'bar':>8}" \
             f"{'n_pairs':>9}{'n_grp':>7}  live"
    print(header)
    for fname, fstat in features.items():
        for bkt, s in fstat["per_bucket"].items():
            def fmt(x):
                return f"{x:.4f}" if isinstance(x, float) else "n/a"
            print(f"  {fname:<22}{bkt:<8}{fmt(s['raw']):>8}{fmt(s['null']):>8}"
                  f"{fmt(s['excess']):>9}{fmt(s['bar']):>8}{s['n_pairs']:>9}{s['n_groups']:>7}"
                  f"  {'LIVE' if s['live'] else 'dead'}")
        s = fstat["all"]
        print(f"  {fname:<22}{'ALL':<8}{fmt(s['raw']):>8}{fmt(s['null']):>8}"
              f"{fmt(s['excess']):>9}{fmt(s['bar']):>8}{s['n_pairs']:>9}{s['n_groups']:>7}"
              f"  {'LIVE' if s['live'] else 'dead'}")
        s = fstat["desert"]
        print(f"  {fname:<22}{'DESERT(1,2)':<8}{fmt(s['raw']):>8}{fmt(s['null']):>8}"
              f"{fmt(s['excess']):>9}{fmt(s['bar']):>8}{s['n_pairs']:>9}{s['n_groups']:>7}"
              f"  {'LIVE' if s['live'] else 'dead'}")
        print()

    print(f"\n{SEP}\n  VERDICT (pre-registered bars, restated from the module docstring)\n{SEP}")
    for fname, fstat in features.items():
        all_live = fstat["all"]["live"]
        desert_live = fstat["desert"]["live"]
        print(f"  {fname:<22} ALL-CLASSES: {'LIVE' if all_live else 'DEAD'}   "
              f"DESERT(1,2-stroke): {'LIVE' if desert_live else 'DEAD'}")

    any_live = any(f["all"]["live"] or f["desert"]["live"] for f in features.values())
    print(f"\n  ANY feature LIVE (licenses the run-39 full gate, not built here): "
          f"{'YES' if any_live else 'NO'}")

    md5_after = _md5(STROKE_SHAPES_PATH)
    print(f"\n  seeds/stroke_shapes.json md5 AFTER (must be unchanged): {md5_after}  "
          f"{'OK -- unchanged' if md5_after == md5_before else 'MISMATCH -- INVESTIGATE, this run never writes there'}")

    result = dict(
        alphabets=alphabets, n_classes=len(classes), n_skipped=n_skipped,
        canon_k_distribution=dict(canon_ks), qc_totals=dict(tot_qc),
        duration_edges=edges, duration_anomalies=anomalies,
        n_duration_pooled=len(durs_all),
        features=features,
        md5_before=md5_before, md5_after=md5_after,
        wall_clock_seconds=time.time() - t0,
    )
    _save_json(result, _ckpt("gate0.json"))
    print(f"\n  saved -> {_ckpt('gate0.json')}")
    print(f"  wall clock: {result['wall_clock_seconds']:.2f}s")
    return 0


def stage_report() -> int:
    p = _ckpt("gate0.json")
    if not os.path.exists(p):
        print("  WALL: run --stage gate0 first.")
        return 1
    result = _load_json(p)
    print(f"\n{SEP}\n  RUN 39 GATE 0 -- REPORT (from checkpoint)\n{SEP}")
    print(json.dumps({k: v for k, v in result.items() if k != "features"}, indent=1))
    for fname, fstat in result["features"].items():
        print(f"\n  {fname}: ALL live={fstat['all']['live']}  DESERT live={fstat['desert']['live']}")
    return 0


STAGES = {"gate0": stage_gate0, "report": stage_report}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", required=True, choices=sorted(STAGES.keys()))
    args = ap.parse_args()
    return STAGES[args.stage]()


if __name__ == "__main__":
    sys.exit(main())
