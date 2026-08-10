"""adaptive_bins — RUN 32 (OPTION R, "attack the bin grain"): DATA-PLACED (quantile/equal-
mass) turn/length bin edges for `StrokeQuantize`'s FINE grain, computed from the LEARN
population's own span distribution and held as graph data, per the creator's standing law
"quanta is dynamic per dimension" (`seeds/shape_decode_loop.json`'s dynamic-quantization
precedent, applied here to bin PLACEMENT rather than bin COUNT/topology).

THE WALL THIS CLOSES: `results/run28_checkpoints/calibration_report.json` measured
10,230/10,231 real LEARN spans resolving to ONE family under the pre-existing UNIFORM
turn/length bins (`domains/stroke_codebook.DEFAULT_TURN_BINS`/`DEFAULT_LEN_BINS`, spanning
the full `(-180,180]`/`[0,1)` range with EQUAL-WIDTH cells) — real handwriting's per-segment
turn/length values are not uniformly distributed over that range (most strokes turn gently
and take near-equal-length steps), so almost every observation lands in the SAME one or two
central cells regardless of bin COUNT. This module repositions the cell BOUNDARIES to match
where the data actually falls (equal population mass per cell, not equal geometric width) —
the featureset itself should carry more discriminative information without touching anything
downstream (`ShapeDecode`/`TransformDecode`/the `sd_*` loop apply UNCHANGED to whatever
signature ints arrive, adaptive or uniform).

ARCHITECTURE (CLAUDE.md): this is a SEED-ADJACENT MEASUREMENT + GRAPH-DATA INSTALL module,
the SAME class of thing `domains/novelty_calibration.py` already is — it measures a FIXED
already-computed population (the LEARN strokes a caller hands it) via the EXISTING held
`StrokeQuantize` Term (a bins=1 call reads off the RAW pre-quantization continuous value via
that Term's own `emit_residual` field — see `_raw_span_values`'s docstring for why this needs
NO new Rust primitive and NO duplicated Python geometry), then writes a FIXED FORMULA's output
(`numpy.quantile` over the collected floats — arithmetic, not a graph-state-conditional
decision) onto agent-root graph data. The quantile computation itself is standard descriptive
statistics over an already-gathered population, the same class of thing
`novelty_calibration._percentile` already is. WHICH edges a decode call actually USES stays
exactly where it always was — a held `StrokeQuantize`/`StrokeRender` Term evaluate — this
module only supplies the DATA those Terms read.
"""
from __future__ import annotations

import json
import math
from typing import Any, Optional

import numpy as np

from domains import ink_decode as ink
from domains.reflective_faculty import _agent_root_node
from domains.stroke_codebook import DEFAULT_LEN_BINS, DEFAULT_SEGMENTS, DEFAULT_TURN_BINS, _native, _quantize, _sub

# Pre-registered DEFAULT (stated in RUN 32's own header, before any edge was computed against
# real data): QUANTILE / EQUAL-MASS edges — `n_bins + 1` boundaries at
# `np.quantile(values, k/n_bins)` for `k in 0..=n_bins`, then the two OUTER boundaries are
# CLAMPED to the dimension's own full domain (`-180/180` for turn, `0/1` for length) so every
# possible value (including ones the LEARN sample never happened to hit) still lands in a
# valid cell — a decode-time query is never left with an out-of-range raw value with nowhere
# to bucket (RUN 32's own doc: "`quantize_edges` clamps a value outside `[edges[0],
# edges[last]]` to the nearest end bin" — the domain-clamp here just makes that clamp only
# ever fire on genuinely out-of-sample data, never on the LEARN population it was fit to).
#
# AMENDMENT (2026-07-05, pre-registered BEFORE the re-run, coordinator-directed — the first
# live gather-edges against real ink found DEGENERATE quantiles and the first learn attempt
# HUNG on them; the finding itself is a first-class result, see the run-32 log): real
# handwriting's turn distribution has a POINT MASS at exactly 0.0 degrees (locally-straight
# segments) — four consecutive quantiles landed on 0.0 — and the LENGTH dimension collapses
# onto 1/segments EXACTLY (with equal-ARC-LENGTH resampling, per-segment normalized length is
# 1/segments BY CONSTRUCTION: the dimension is information-free, an artifact of the
# extractor; this pair of facts mechanistically EXPLAINS the run-28 10,230/10,231 identity
# collapse — one dead dimension + one point-massed dimension). An earlier draft NUDGED equal
# quantiles apart by epsilon, which manufactured near-zero-width bins: point-mass values then
# scattered across them under float jitter, every span became a fresh signature, and LEARN
# exploded (47,833 seed-lines of mints, killed at 11+ min). The corrected, pre-registered
# handling: (a) DEDUPE — merge quantiles closer than `min_width = domain_width *
# MIN_BIN_WIDTH_FRAC`, yielding FEWER effective bins where mass is point-like (equal-mass
# cannot spread a point mass and must not pretend to); (b) KEEP the length dimension with its
# deduped (likely ~2-3 effective) bins and REPORT its measured entropy (~zero expected) — a
# dimension dead by construction is a falsifiable RECORD, never silently dropped; (c) GUARD —
# `_assert_strictly_increasing` hard-fails (`DegenerateEdgesError`, the
# `EmptyCalibrationError` precedent) if any post-dedupe edge pair is not strictly increasing.
EDGE_METHOD = "quantile_equal_mass_deduped"
TURN_DOMAIN = (-180.0, 180.0)
LEN_DOMAIN = (0.0, 1.0)
# Pre-registered dedupe threshold: 1e-3 of the domain width (turn: 0.36 degrees; len: 0.001).
# Small enough never to merge genuinely-separated quantiles of a spread distribution; large
# enough that float jitter around a point mass can never straddle a boundary pair.
MIN_BIN_WIDTH_FRAC = 1e-3


class DegenerateEdgesError(RuntimeError):
    """Raised when an edges array is not strictly increasing after dedupe — the exact failure
    mode the first learn attempt hung on must be structurally impossible to repeat unnoticed
    (the `EmptyCalibrationError` precedent, `domains/novelty_calibration.py`)."""


# --------------------------------------------------------------------------- #
#  RAW VALUE EXTRACTION — via the EXISTING StrokeQuantize Term's own `emit_residual` field,
#  at `turn_bins=1`/`len_bins=1` (a single bin spanning the WHOLE domain): the bin-0 CENTER is
#  then a FIXED constant (`angle_bin_center(0, 1) == 0.0`; `bucket_center(0, 0, 1, 1) == 0.5`)
#  by construction, so `residual = raw - center` recovers the RAW pre-quantization continuous
#  value exactly (`raw = residual + center`) — NO new Rust primitive, NO Python re-
#  implementation of the arc-length/heading geometry (which would be exactly the "primitive
#  in Python" CLAUDE.md forbids).
# --------------------------------------------------------------------------- #
_RAW_TURN_CENTER = 0.0     # angle_bin_center(0, bins=1) -- wrap180(0 * 360) == 0.0
_RAW_LEN_CENTER = 0.5      # bucket_center(0, 0.0, 1.0, bins=1) -- 0.0 + (0+0.5)*1.0


def _raw_span_values(native, points: list, *, segments: int) -> list[tuple[float, float]]:
    """One `StrokeQuantize` evaluate at `turn_bins=1, len_bins=1, emit_residual=True` —
    returns `[(raw_turn_deg, raw_len_frac), ...]`, one pair per segment (segment 0's turn is
    always `0.0` by `StrokeQuantize`'s own convention — excluded by every caller here, see
    `gather_learn_span_values`'s docstring). Mechanical Term evaluate + residual-to-raw
    arithmetic, no decision."""
    q = _quantize(native, points, segments=segments, turn_bins=1, len_bins=1, grid=1,
                  scale_bins=1, invariant_only=True, emit_residual=True)
    out = []
    for (i, turn_res, len_res) in q.get("residuals") or []:
        raw_turn = float(turn_res) + _RAW_TURN_CENTER
        raw_len = float(len_res) + _RAW_LEN_CENTER
        out.append((int(i), raw_turn, raw_len))
    return out


def gather_learn_span_values(agent, stroke_sources: list, *,
                              segments: int = DEFAULT_SEGMENTS,
                              max_knots: int = 16) -> dict[str, list]:
    """Mechanical gather (a world-adapter/seed-builder concern, per `novelty_calibration`'s
    own precedent): `stroke_sources`, a plain list of raw `[[x,y],...]` point-lists (the SAME
    LEARN population `novelty_calibration.calibrate_dtw_thresholds`/
    `scripts/jabberwock_omniglot_dynamic_quantization.py::run_learn` iterate), each
    INGESTED via `ink.ingest_ink` (unchanged geometry) then measured PER SEGMENT via
    `_raw_span_values`. Segment 0's turn value is EXCLUDED from `turn` (it carries no
    information — `StrokeQuantize`'s own `turn_q=0` convention for the first segment; the
    RAW value read back at `turn_bins=1` would be a meaningless artifact of that convention,
    not real turn data) — segment 0's LENGTH value IS included (real data). Returns
    `{"turn": [...], "len": [...], "n_strokes": int, "n_spans": int}`."""
    sub = _sub(agent)
    native = _native(agent)
    turns: list[float] = []
    lens: list[float] = []
    n_spans = 0
    for points in stroke_sources:
        ink_node = ink.ingest_ink(agent, points, max_knots=max_knots)
        knots = sub.node(ink_node)["attrs"].get("knots") or []
        if len(knots) < 2:
            continue
        vals = _raw_span_values(native, knots, segments=segments)
        for (i, raw_turn, raw_len) in vals:
            n_spans += 1
            lens.append(raw_len)
            if i > 0:
                turns.append(raw_turn)
    return {"turn": turns, "len": lens, "n_strokes": len(stroke_sources), "n_spans": n_spans}


# --------------------------------------------------------------------------- #
#  QUANTILE (EQUAL-MASS) EDGES — pure descriptive statistics, the pre-registered DEFAULT.
# --------------------------------------------------------------------------- #
def _assert_strictly_increasing(edges: list, label: str = "") -> None:
    """The AMENDMENT's hard guard (c): every adjacent pair must be strictly increasing —
    hard-fail, never a silent pass (the exact failure mode the first learn attempt hung on)."""
    for i in range(1, len(edges)):
        if not (edges[i] > edges[i - 1]):
            raise DegenerateEdgesError(
                f"edges{f' ({label})' if label else ''} not strictly increasing at index {i}: "
                f"{edges[i - 1]!r} -> {edges[i]!r} (full array: {edges!r}) — zero/negative-width "
                "bins scatter point-mass values under float jitter and explode the codebook; "
                "refusing to return them")


def compute_quantile_edges(values: list, n_bins: int, domain: tuple, *,
                            min_width_frac: float = MIN_BIN_WIDTH_FRAC) -> list[float]:
    """`n_bins + 1` ascending boundaries: `np.quantile(values, k/n_bins)` for
    `k in 0..=n_bins`, outer boundaries clamped to `domain = (lo, hi)`, then DEDUPED per the
    AMENDMENT (see module docstring): quantiles closer than `min_width = (hi - lo) *
    min_width_frac` to the previously-kept edge are MERGED (dropped), yielding FEWER effective
    bins where the distribution is point-like — equal-mass cannot spread a point mass and must
    not pretend to. The domain endpoints are always kept (every possible value has a cell).
    Degenerate input (fewer than 2 distinct values, or `n_bins < 1`) falls back to UNIFORM
    edges over `domain` (an honest non-crash — a data-starved dimension gets the pre-existing
    uniform behaviour). The returned array is GUARANTEED strictly increasing
    (`_assert_strictly_increasing`, hard-fail otherwise — never a silent nudge)."""
    lo, hi = float(domain[0]), float(domain[1])
    n_bins = max(1, int(n_bins))
    arr = np.asarray([float(v) for v in values], dtype=float)
    if arr.size < 2 or len(set(np.round(arr, 9).tolist())) < 2:
        out = list(np.linspace(lo, hi, n_bins + 1))
        _assert_strictly_increasing(out, "uniform-fallback")
        return out
    qs = np.linspace(0.0, 1.0, n_bins + 1)
    edges = np.clip(np.quantile(arr, qs), lo, hi)
    edges[0], edges[-1] = lo, hi

    # DEDUPE (amendment (a)): keep an interior quantile only if it clears the previously-KEPT
    # edge by at least min_width AND still leaves room to reach `hi` (the final edge is always
    # `hi`; an interior edge within min_width of `hi` would recreate a sliver at the top).
    min_width = max((hi - lo) * float(min_width_frac), 1e-12)
    kept = [lo]
    for v in edges[1:-1]:
        if v >= kept[-1] + min_width and v <= hi - min_width:
            kept.append(float(v))
    kept.append(hi)

    _assert_strictly_increasing(kept, "post-dedupe")
    return [float(v) for v in kept]


def bin_occupancy(values: list, edges: list) -> dict[str, Any]:
    """AMENDMENT (b)'s per-dimension diagnostic: quantize every raw value against `edges`
    (the SAME left-edge-inclusive semantics the Rust `quantize_edges` applies — reproduced
    here as descriptive statistics over an already-gathered population, the
    `novelty_calibration._percentile` precedent) and report the bin-count histogram + its
    Shannon entropy in bits. A dimension that is dead by construction (length under equal-arc
    resampling) shows ~0 bits HERE, in the report, as a falsifiable record — never silently
    dropped."""
    n_bins = max(1, len(edges) - 1)
    counts: dict[str, int] = {}
    for v in values:
        v = float(v)
        idx = n_bins - 1
        if v <= edges[0]:
            idx = 0
        else:
            for i in range(n_bins):
                if v < edges[i + 1]:
                    idx = i
                    break
        counts[str(idx)] = counts.get(str(idx), 0) + 1
    return {"n_bins": n_bins, "counts": counts, "entropy_bits": shannon_entropy_bits(counts),
            "max_entropy_bits": math.log2(n_bins) if n_bins > 1 else 0.0}


def compute_adaptive_edges(learn_values: dict, *, turn_bins: int = DEFAULT_TURN_BINS,
                            len_bins: int = DEFAULT_LEN_BINS) -> dict[str, Any]:
    """The full RUN 32 edge-computation report: quantile edges for BOTH dimensions
    (`gather_learn_span_values`'s own output), REQUESTED `n_bins` matching the pre-existing
    `DEFAULT_TURN_BINS`/`DEFAULT_LEN_BINS` bin COUNT (the lever is PLACEMENT, not count) —
    the EFFECTIVE bin count after the amendment's dedupe may be smaller wherever the
    distribution is point-like, and is reported alongside per-dimension bin-occupancy
    entropy (`bin_occupancy`, amendment (b))."""
    turn_edges = compute_quantile_edges(learn_values["turn"], turn_bins, TURN_DOMAIN)
    len_edges = compute_quantile_edges(learn_values["len"], len_bins, LEN_DOMAIN)
    return {
        "method": EDGE_METHOD, "turn_bins_requested": turn_bins, "len_bins_requested": len_bins,
        "turn_bins_effective": len(turn_edges) - 1, "len_bins_effective": len(len_edges) - 1,
        "turn_edges": turn_edges, "len_edges": len_edges,
        "turn_occupancy": bin_occupancy(learn_values["turn"], turn_edges),
        "len_occupancy": bin_occupancy(learn_values["len"], len_edges),
        "n_turn_values": len(learn_values["turn"]), "n_len_values": len(learn_values["len"]),
        "n_strokes": learn_values.get("n_strokes"), "n_spans": learn_values.get("n_spans"),
    }


# --------------------------------------------------------------------------- #
#  GRAPH-DATA STORAGE — held on the agent root, mirroring `novelty_calibration`'s own
#  `dtw_near_threshold_calibrated` convention (a single JSON-string attr per dimension).
# --------------------------------------------------------------------------- #
def store_adaptive_edges(agent, turn_edges: list, len_edges: list) -> None:
    sub = _sub(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    sub.set_attr(ag_node, "adaptive_turn_edges", json.dumps([float(v) for v in turn_edges]))
    sub.set_attr(ag_node, "adaptive_len_edges", json.dumps([float(v) for v in len_edges]))


def read_adaptive_edges(agent) -> tuple[Optional[list], Optional[list]]:
    """Mechanical graph-attr read-back — `(None, None)` when nothing was ever stored (an
    honest absent-lever state, byte-identical to every caller that never touches this
    module)."""
    sub = _sub(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)
    at = sub.node(ag_node)["attrs"]
    turn_json, len_json = at.get("adaptive_turn_edges"), at.get("adaptive_len_edges")
    turn_edges = json.loads(turn_json) if turn_json else None
    len_edges = json.loads(len_json) if len_json else None
    return turn_edges, len_edges


# --------------------------------------------------------------------------- #
#  ENTROPY — P2's own diagnostic metric ("the identity-collapse metric"). Mechanical Shannon
#  entropy over a family-name histogram, in BITS (log base 2) — pure descriptive statistics,
#  the same class of computation `novelty_calibration._percentile` already is.
# --------------------------------------------------------------------------- #
def family_histogram(families: list) -> dict[str, int]:
    hist: dict[str, int] = {}
    for f in families:
        if f is None:
            continue
        hist[f] = hist.get(f, 0) + 1
    return hist


def shannon_entropy_bits(hist: dict[str, int]) -> float:
    """`H = -sum(p * log2(p))` over the histogram's own probabilities (`count / total`). `0.0`
    for an empty or single-bucket histogram (the run-28 "10,230/10,231 in ONE family" collapse
    case: `H == 0.0` bits, by construction — one bucket holding everything carries zero
    information). Never raises on a zero-count input."""
    total = sum(hist.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for count in hist.values():
        if count <= 0:
            continue
        p = count / total
        h -= p * math.log2(p)
    return float(h)


def entropy_report(families: list) -> dict[str, Any]:
    hist = family_histogram(families)
    return {"n_families": len(hist), "n_observations": sum(hist.values()),
            "entropy_bits": shannon_entropy_bits(hist),
            "max_entropy_bits": math.log2(len(hist)) if len(hist) > 1 else 0.0,
            "top_family_share": (max(hist.values()) / sum(hist.values())) if hist else 0.0,
            "histogram": hist}


__all__ = ["compute_quantile_edges", "compute_adaptive_edges", "gather_learn_span_values",
           "store_adaptive_edges", "read_adaptive_edges", "family_histogram",
           "shannon_entropy_bits", "entropy_report", "bin_occupancy",
           "DegenerateEdgesError", "MIN_BIN_WIDTH_FRAC",
           "EDGE_METHOD", "TURN_DOMAIN", "LEN_DOMAIN"]
