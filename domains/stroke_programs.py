"""stroke_programs -- RUN 35 GATE 0: "time is not a dimension, it is a series of collapses.
circles are not circles, they are a 2D view of a sinusoid, that is itself, stepped." (creator,
2026-07-05). Translation to this codebase: the `seg` relations (`StrokeQuantize`'s per-SEGMENT
relative-turn quantum, one independent value per of `DK["segments"]`-1 equal-arc-length steps)
are ALREADY the phase-step view of a stroke -- but the entire closed 2x2 (runs 32/34c/34d,
commits 13ebc282/8323f2a9/cc673ee1) measured those steps as INDEPENDENT observations (one
identity per stroke, hashed over the WHOLE per-step vector, with no notion that a run of steps
might be the SAME underlying program token repeated). A circle is not `n` independent turn-
tokens, it is ONE program token: `repeat(turn=k) x n`. A line is `repeat(turn=0) x n`. A
spiral/clothoid is a turn RAMP (`turn=k0, k0+dk, k0+2dk, ...`). A hook is a program CHANGE-POINT
(one token ends, another begins). This module builds that PROGRAM token sequence -- order-N
applied WITHIN a single stroke, the +21pp character-composition move one grain further down.

ARCHITECTURE (CLAUDE.md): a WORLD-ADAPTER-class feature extractor, the same class of thing
`domains/adaptive_bins.py` (descriptive statistics + quantile edges over an already-gathered
population) and `domains/ink_dynamics.py` (fixed-formula candidate-boundary extraction) already
are. Every function here is a MECHANICAL, DETERMINISTIC, NUMPY-ONLY transform over numbers
already produced by the existing held `StrokeQuantize` Term (via `domains.adaptive_bins.
_raw_span_values`, reused verbatim, NOT reimplemented) -- no conditional over graph state, no
rule engine, no agent decision, no `teach()`/codebook mutation anywhere in this module. This
gate MINTS NOTHING: it reads the SAME per-segment turn residual `StrokeQuantize` already
computes and re-groups/re-labels it in plain Python/numpy, exactly the "primitive in Rust,
composition read back out" split CLAUDE.md requires.

PRE-REGISTERED TOKENIZATION METHOD (stated here BEFORE any real number is computed against it --
`scripts/jabberwock_omniglot_run35_programs.py --stage gate0` cites this docstring verbatim in
its own header):

  0. INPUT: one stroke's per-segment RAW turn sequence `t_1, ..., t_{m-1}` (`m =
     DK["segments"]`, segment 0 excluded -- `adaptive_bins.gather_learn_span_values`'s own
     documented convention: segment 0's turn value is a `StrokeQuantize` convention artifact,
     not real turn data), computed on the GLOBALLY DENOISED stroke (`mouse_model.
     denoise_path_global`, run 34b/34d's own proven instrument) via the SAME `StrokeQuantize`
     arc-length resampling the `seg` relations already use (`stroke_turn_sequence`, below --
     `ink.ingest_ink` -> knots -> `adaptive_bins._raw_span_values`, zero new geometry).

  1. PASS 1 -- LEVEL-RUN SEGMENTATION (`segment_level_runs`): a single left-to-right greedy
     online-mean grouping. Start a run at `t_1` (`running_mean = t_1`, `length = 1`). For each
     subsequent `t_i`: if `|t_i - running_mean| <= tol_deg`, EXTEND the current run (fold `t_i`
     into the running mean, `length += 1`); otherwise CLOSE the run (record its final mean
     `level` and `length`) and START a new run at `t_i`. This is the simplest possible online
     change-point rule and is symmetric in nothing else -- no look-ahead, no re-segmentation,
     exactly the "simple pre-registered two-pass" the launch brief asks for.
     TOLERANCE BAND (`tol_deg_from_edges`): `0.5 * median(diff(level_edges))`, where
     `level_edges` is THIS GATE'S OWN CITED reference -- `results/run34d_checkpoints/
     edges_report.json`'s `turn_edges` (the SAME denoised, adaptive, quantile/equal-mass,
     deduped-and-guarded edges run 34d already fit on the IDENTICAL 1500-stroke LEARN
     population's per-segment turn distribution). Ties the grouping tolerance to this
     featureset's OWN already-measured discrimination floor (half a typical bin's width)
     rather than an arbitrary constant, and costs nothing to compute (pure citation, no re-fit)
     -- never re-tuned against any downstream entropy/coherence number this gate reports.

  2. RUN CLASSIFICATION: a closed run is a LINE if `|level| <= tol_deg` (turn ~ 0: a locally-
     straight stretch), else an ARC candidate (turn ~ constant-but-nonzero: locally-constant
     curvature).

  3. PASS 2 -- RAMP PROMOTION (`promote_ramps`): scan the classified run sequence left to
     right. A LINE run is never merged (a straight run is a program token in its own right --
     "a hook is a program change-point", not something to average away). For a maximal run of
     >= 2 CONSECUTIVE ARC entries whose `level` values are STRICTLY MONOTONIC step-to-step
     (all-increasing or all-decreasing -- ties or a direction reversal end the candidate
     immediately, greedy left-to-right, no re-segmentation), merge the whole span into ONE
     RAMP token: `k0` = the first run's level, `dk` = the mean of the (n_runs - 1) consecutive
     level-to-level deltas, `length` = the sum of the merged runs' own lengths (a ramp's length
     is a COUNT of collapsed per-segment steps, per the reframe -- "time ... is a series of
     collapses" -- never re-measured in arc-length). A non-monotonic or length-1 arc run stays
     a plain ARC token.

  4. TOKEN PARAMETER QUANTIZATION (`finalize_tokens`): LINE tokens carry only `length` (a raw
     step-count integer -- "collapse-counts, not arc-length", no binning needed, the value IS
     already a unit-granularity count). ARC tokens quantize `level` into a bin INDEX under the
     SAME cited `level_edges` (`bin_index` -- identical left-edge-inclusive semantics to
     `adaptive_bins.bin_occupancy`, reused not reimplemented in spirit). RAMP tokens quantize
     `k0` under `level_edges` and `dk` under a SEPARATE `delta_edges` set -- a NEW quantile/
     equal-mass/deduped/guarded edge set (`domains.adaptive_bins.compute_quantile_edges`,
     called with this module's own `DEFAULT_DELTA_DOMAIN = (-360, 360)` and
     `DEFAULT_DELTA_BINS = 6`, reused verbatim; falls back to uniform edges under the SAME
     degenerate-input rule if fewer than 2 distinct deltas exist in the gathered population --
     an honest floor for a rare token, never a crash) fit ONCE over every ramp `dk` observed in
     the LEARN population (a two-phase gather: `tokenize_turn_sequence(..., delta_edges=None)`
     returns raw, un-quantized ramp deltas for a first population-wide pass; a caller computes
     `delta_edges` from the pooled result and re-invokes `finalize_tokens` to quantize).

  5. THE PROGRAM STRING: fine-grain IDENTITY = the ordered token sequence formatted with its
     quantized parameters (`format_fine`, e.g. `"line(3)|arc(2,3)|ramp(1,-1,4)"`) -- the
     program-space analogue of the `seg`-relation span identity the 2x2 measured, used AS a
     dict key (a hash of this string would be equally valid and strictly shorter; the raw
     string is kept as the identity for report readability, exactly as run 32/34d's own
     `stroke_18814ab760d8__ref_turn_*` identity names are kept human-legible rather than
     opaque hashes). COARSE-grain IDENTITY = token TYPES only, parameters dropped
     (`format_coarse`, e.g. `"L-A-R"`) -- the second, cheaper grain the launch brief asks be
     reported alongside the fine one.

NO SEED, NO GRAPH MUTATION: every function below takes and returns plain Python/numpy values.
The one substrate touch (`stroke_turn_sequence`) calls `ink.ingest_ink` (existing, unmodified)
on a throwaway `Ink` node purely to reach the geometry it already knows how to fit -- this gate
never calls `decode_ink`, never touches a `ShapeSignature`/codebook node, and never calls
`teach()`; it mints nothing, matching the launch brief's own "this gate should mint NOTHING, it
is pure measurement" requirement.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from domains import ink_decode as ink
from domains.adaptive_bins import _raw_span_values, compute_quantile_edges
from domains.stroke_codebook import _native, _sub

EPS = 1e-9

# Pre-registered (see module docstring step 4) -- NEVER re-tuned against any downstream number.
DEFAULT_DELTA_DOMAIN = (-360.0, 360.0)
DEFAULT_DELTA_BINS = 6


# --------------------------------------------------------------------------- #
#  STEP 0 -- per-segment raw turn sequence, via the EXISTING StrokeQuantize residual read
#  (`adaptive_bins._raw_span_values`, reused verbatim -- zero new geometry, zero new Rust).
# --------------------------------------------------------------------------- #
def stroke_turn_sequence(agent, points, *, segments: int, max_knots: int) -> list[float]:
    """One stroke's raw per-segment turn values (degrees), segment 0 excluded (convention
    artifact, see module docstring step 0). `agent` is any object `ink.ingest_ink` accepts (a
    raw `substrate_rs.Substrate()` is sufficient -- this function mints no seed data and reads
    no seeded Term). Returns `[]` for a degenerate (<2-knot) stroke -- an honest empty program,
    never a crash."""
    ink_node = ink.ingest_ink(agent, points, max_knots=max_knots)
    sub = _sub(agent)
    native = _native(agent)
    knots = sub.node(ink_node)["attrs"].get("knots") or []
    if len(knots) < 2:
        return []
    vals = _raw_span_values(native, knots, segments=segments)
    return [float(t) for (i, t, _l) in vals if i > 0]


# --------------------------------------------------------------------------- #
#  STEP 1 -- tolerance band, cited from this gate's own reference edges (see docstring).
# --------------------------------------------------------------------------- #
def tol_deg_from_edges(level_edges: list) -> float:
    """`0.5 * median(diff(level_edges))` -- half this featureset's own typical (cited) bin
    width. `level_edges` must have >= 2 entries (>= 1 bin); a degenerate 1-edge input has no
    defined width and returns `0.0` (an honest floor -- every value would then start its own
    run, the maximally conservative behaviour, never a crash)."""
    edges = np.asarray(level_edges, dtype=float)
    if edges.size < 2:
        return 0.0
    diffs = np.diff(edges)
    return float(0.5 * np.median(diffs))


# --------------------------------------------------------------------------- #
#  PASS 1 -- level-run segmentation (greedy online-mean grouping, see docstring step 1).
# --------------------------------------------------------------------------- #
def segment_level_runs(turn_seq: list, tol_deg: float) -> list[dict]:
    """`[{"level": float, "length": int}, ...]` -- maximal near-constant runs of `turn_seq`.
    `[]` for an empty input (nothing to segment)."""
    runs: list[dict] = []
    if not turn_seq:
        return runs
    run_sum = float(turn_seq[0])
    run_len = 1
    for t in turn_seq[1:]:
        running_mean = run_sum / run_len
        if abs(float(t) - running_mean) <= tol_deg:
            run_sum += float(t)
            run_len += 1
        else:
            runs.append({"level": run_sum / run_len, "length": run_len})
            run_sum = float(t)
            run_len = 1
    runs.append({"level": run_sum / run_len, "length": run_len})
    return runs


def _is_line(level: float, tol_deg: float) -> bool:
    return abs(level) <= tol_deg


# --------------------------------------------------------------------------- #
#  PASS 2 -- ramp promotion (see docstring step 3).
# --------------------------------------------------------------------------- #
def promote_ramps(runs: list, tol_deg: float) -> list[dict]:
    """`runs` (from `segment_level_runs`) -> a list of `{"kind": "line"|"arc"|"ramp", ...}`.
    `line`/`arc` entries carry `level`/`length`; `ramp` entries carry `k0`/`dk`/`length`/
    `n_runs`. `[]` for an empty input."""
    if not runs:
        return []
    classified = [{"kind": "line" if _is_line(r["level"], tol_deg) else "arc",
                   "level": r["level"], "length": r["length"]} for r in runs]
    out: list[dict] = []
    n = len(classified)
    i = 0
    while i < n:
        if classified[i]["kind"] != "arc":
            out.append(classified[i])
            i += 1
            continue
        j = i + 1
        direction = 0
        while j < n and classified[j]["kind"] == "arc":
            d = classified[j]["level"] - classified[j - 1]["level"]
            if d == 0.0:
                break
            step_dir = 1 if d > 0 else -1
            if direction == 0:
                direction = step_dir
            elif step_dir != direction:
                break
            j += 1
        if j - i >= 2:
            span = classified[i:j]
            deltas = [span[k + 1]["level"] - span[k]["level"] for k in range(len(span) - 1)]
            out.append({"kind": "ramp", "k0": span[0]["level"], "dk": float(np.mean(deltas)),
                        "length": sum(s["length"] for s in span), "n_runs": len(span)})
            i = j
        else:
            out.append(classified[i])
            i += 1
    return out


# --------------------------------------------------------------------------- #
#  STEP 4 -- parameter quantization (see docstring step 4). `bin_index` mirrors
#  `adaptive_bins.bin_occupancy`'s own left-edge-inclusive semantics for a SINGLE value.
# --------------------------------------------------------------------------- #
def bin_index(value: float, edges: list) -> int:
    n_bins = max(1, len(edges) - 1)
    if value <= edges[0]:
        return 0
    for i in range(n_bins):
        if value < edges[i + 1]:
            return i
    return n_bins - 1


def finalize_tokens(promoted: list, level_edges: list, delta_edges: list) -> list[dict]:
    """Quantize `promote_ramps`'s output into the final token parameter set (docstring step
    4). `line` tokens: `{"kind": "line", "length": int}`. `arc` tokens: `{"kind": "arc", "k":
    int, "length": int}`. `ramp` tokens: `{"kind": "ramp", "k0": int, "dk": int, "length":
    int}`."""
    out = []
    for t in promoted:
        if t["kind"] == "line":
            out.append({"kind": "line", "length": int(t["length"])})
        elif t["kind"] == "arc":
            out.append({"kind": "arc", "k": bin_index(t["level"], level_edges),
                        "length": int(t["length"])})
        else:
            out.append({"kind": "ramp", "k0": bin_index(t["k0"], level_edges),
                        "dk": bin_index(t["dk"], delta_edges), "length": int(t["length"])})
    return out


def format_fine(tokens: list) -> str:
    """The fine-grain program string (docstring step 5). `"∅"` (empty set) for an empty
    program -- an honest degenerate-stroke marker, never silently dropped from a histogram."""
    if not tokens:
        return "∅"
    parts = []
    for t in tokens:
        if t["kind"] == "line":
            parts.append(f"line({t['length']})")
        elif t["kind"] == "arc":
            parts.append(f"arc({t['k']},{t['length']})")
        else:
            parts.append(f"ramp({t['k0']},{t['dk']},{t['length']})")
    return "|".join(parts)


_COARSE_LETTER = {"line": "L", "arc": "A", "ramp": "R"}


def format_coarse(tokens: list) -> str:
    """The coarse-grain (types-only) program string (docstring step 5)."""
    if not tokens:
        return "∅"
    return "-".join(_COARSE_LETTER[t["kind"]] for t in tokens)


# --------------------------------------------------------------------------- #
#  FULL PIPELINE -- turn sequence -> (raw promoted runs | finalized program), two-phase to
#  support the population-wide delta-edge gather (see docstring step 4).
# --------------------------------------------------------------------------- #
def tokenize_turn_sequence(turn_seq: list, tol_deg: float, level_edges: list,
                           delta_edges: Optional[list] = None) -> dict:
    """`delta_edges=None` (phase 1 -- gather): returns `{"promoted": [...], "raw_deltas":
    [...]}` -- the un-quantized ramp deltas this stroke contributed, for a caller to pool
    across the LEARN population and fit `delta_edges` from
    (`domains.adaptive_bins.compute_quantile_edges(pooled_deltas, DEFAULT_DELTA_BINS,
    DEFAULT_DELTA_DOMAIN)`). `delta_edges` given (phase 2 -- finalize): returns `{"tokens":
    [...], "fine": str, "coarse": str, "raw_deltas": [...]}` -- the complete program."""
    runs = segment_level_runs(turn_seq, tol_deg)
    promoted = promote_ramps(runs, tol_deg)
    raw_deltas = [t["dk"] for t in promoted if t["kind"] == "ramp"]
    if delta_edges is None:
        return {"promoted": promoted, "raw_deltas": raw_deltas}
    tokens = finalize_tokens(promoted, level_edges, delta_edges)
    return {"tokens": tokens, "fine": format_fine(tokens), "coarse": format_coarse(tokens),
           "raw_deltas": raw_deltas}


def gather_delta_edges(raw_deltas: list, *, n_bins: int = DEFAULT_DELTA_BINS,
                       domain: tuple = DEFAULT_DELTA_DOMAIN) -> list[float]:
    """Thin, named wrapper over `adaptive_bins.compute_quantile_edges` (reused verbatim, per
    the module docstring's "not reimplemented" discipline) for the ramp-delta population."""
    return compute_quantile_edges(raw_deltas, n_bins, domain)


__all__ = [
    "DEFAULT_DELTA_DOMAIN", "DEFAULT_DELTA_BINS",
    "stroke_turn_sequence", "tol_deg_from_edges",
    "segment_level_runs", "promote_ramps",
    "bin_index", "finalize_tokens", "format_fine", "format_coarse",
    "tokenize_turn_sequence", "gather_delta_edges",
]
