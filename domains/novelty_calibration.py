"""novelty_calibration — RUN 28 LEVER 1: calibrated novelty (CFAR) on the stroke-decode
fallback tier.

THE WALL THIS CLOSES (runs 26/27's own traced diagnosis): `domains/ink_decode.py`'s
recognition ladder (fine -> mid -> coarse -> `_dtw_fallback`) ALWAYS matched something on real
held-out ink across 6 full reading cycles (`results/omniglot_gate_run27.log`,
`mints_during_reading` stuck at 0/0/0 in both arms) — not because real novel ink never occurs,
but because `_dtw_fallback`'s own accept/reject threshold (`DEFAULT_DTW_THRESHOLD = 0.15`,
`domains/stroke_codebook.py`) was an ENGINEERING GUESS calibrated against synthetic jitter
perturbations of ALREADY-KNOWN glyphs (that constant's own module comment: "a realistic small
pen jitter ... scores ~0.108; a genuinely different shape class ... scores ~0.50"), never
against the TRUE distribution of what a real, independently-drawn in-family stroke's own
continuous distance-to-prototype looks like. With no calibrated "I don't know", no genuinely
novel span could ever be told apart from a merely-jittered one — no new information could enter
via decode, ever, regardless of how novel the input.

THE FIX (Constant False Alarm Rate calibration, the radar-detection precedent this arc's own
"VARIABLE-APERTURE-RADAR" frame already names): measure the REAL in-family distance
distribution directly from the LEARN population the codebook was built from (each LEARN
stroke's own continuous shape vs. the prototype of whichever family DECODE resolved it to, at
ANY tier — fine/mid/coarse exact matches included, not only the rare dtw-fallback-path subset:
the WHOLE LEARN population's own family-resolved strokes ARE the "accepted" distribution this
lever calibrates against; restricting to literally-only-the-dtw-path subset would be
data-starved by construction, since the ladder's higher tiers absorb most real strokes before
DTW is ever consulted — see `calibrate_dtw_thresholds`'s own docstring for the exact,
pre-registered scope of this choice), then set threshold = max(observed distances) + a fixed
safety margin — the tightest threshold that provably NEVER rejects a single already-recognized
LEARN item (the false-novelty regression gate's own contract, satisfied BY CONSTRUCTION: every
future re-decode of a byte-identical or near-identical LEARN stroke reproduces a distance
<= its own observed value <= max <= threshold). A p95+margin alternative is computed and
reported for transparency (the honest "this is tighter, we did not apply it" comparison) but is
NEVER the applied value — max+margin is the one PRE-REGISTERED formula this module installs.

SCOPE (corrected 2026-07-04, an ANOMALY-FOUND-AND-FIXED — itself fresh evidence for the
standing "check every read-back" rule): an intermediate draft of this module restricted the
measured population to spans the DTW-FALLBACK tier itself had accepted (`tier == "dtw"`
entries only), reasoning that the broader population would calibrate looser. Run against the
REAL 1500-stroke LEARN population, that scope measured NOTHING — `n_strokes_measured=1500,
n_spans_measured=0, n_families=0` (`results/omniglot_gate_run28.log`, first calibrate
invocation) — because in-family LEARN material, by the very saturation that makes it
"in-family," virtually always matches at fine/mid/coarse BEFORE the fallback is ever
consulted: the sample set was EMPTY BY CONSTRUCTION. A calibration that measures nothing is
not a tight calibration, it is NO calibration — every downstream arm would silently run with
the lever inert (the fallback chain in `ink_decode._resolve_dtw_threshold` then reads the
legacy `dtw_near_threshold`/`DEFAULT_DTW_THRESHOLD`, i.e. byte-identical PRE-lever behaviour,
producing vacuous "null" mint counts that measure a no-op, not the lever). The CORRECTED
scope (coordinator-directed): for EVERY accepted span (WHATEVER tier matched it — fine, mid,
coarse, dtw alike), compute the continuous `DtwTo` distance from the span's own invariant
prototype (`_invariant_points`, the SAME normalization `_dtw_fallback`'s candidates use) to
its matched family's stored prototype, and build the in-family distribution from that. This
is the true null distribution a CFAR threshold needs — "what continuous distances do real,
accepted in-family observations exhibit against their own family's reference" — and whether
it lands tighter or looser than the legacy constant is a MEASURED FACT the report states,
never assumed in either direction. DATA-STARVATION (pre-registered,
`DEFAULT_MIN_FAMILY_SAMPLES`): a family with fewer than `min_family_samples` observed
distances gets NO per-family threshold of its own (a single-digit sample cannot support a
`max()`-based tail estimate) — its observations are POOLED into one GLOBAL sample instead,
and the resulting pooled threshold is stored once, on the AGENT ROOT, as the fallback every
data-starved family's own decode consults. Which families end up per-family vs pooled is
REPORTED, never hidden. SANITY GATE (the fix's second half): a calibration whose TOTAL
measured sample is empty is a HARD FAILURE (`fail_on_empty=True`, raises
`EmptyCalibrationError`) — never a silent pass; the exact failure mode the intermediate
draft exhibited must be structurally impossible to repeat unnoticed.

ARCHITECTURE (CLAUDE.md): this module is a SEED-ADJACENT MEASUREMENT + GRAPH-DATA INSTALL, the
same class of thing `stroke_codebook.migrate_multigrain_codebook` already is — it measures a
FIXED already-computed population (the LEARN strokes a caller hands it) via the SAME held
`DtwTo` Term `ink_decode._dtw_fallback`/`stroke_codebook.continuous_mint_or_note` already use,
then writes a FIXED FORMULA's output (`max + margin`) onto graph nodes/attrs. No Python
argmin/argmax over the collected numbers (Python's own built-in `max()` over a plain list of
floats it already assembled is arithmetic, not a graph-state-conditional ranking DECISION — the
same class of "fixed formula on an already-computed value" this codebase's own module
docstrings repeatedly name, e.g. `ink_decode.py`'s "`emit = covered_count if full else
covered_count - segments`"); the ACCEPT/REJECT verdict at decode time stays exactly where it
already was, a held `Lt` Term evaluate in `ink_decode._dtw_fallback` — this module only changes
WHICH NUMBER that Term reads as its threshold operand (a mechanical graph-attr lookup,
`ink_decode._resolve_dtw_threshold`), never the decision mechanism itself."""
from __future__ import annotations

import json
from typing import Any, Optional

import numpy as np

from domains import ink_decode as ink
from domains import stroke_codebook as sc
from domains.reflective_faculty import _agent_root_node
from domains.stroke_codebook import _native, _sub


class EmptyCalibrationError(RuntimeError):
    """Raised when a calibration pass measured NO in-family distances at all — a calibration
    that measures nothing must be a hard failure, never a silent pass (see the module
    docstring's SCOPE correction: this exact failure mode occurred once, silently, and both
    downstream arms ran with the lever inert)."""

# Pre-registered BEFORE any calibration run against real data (never tuned against eval/
# practice-alphabet outcomes, per the run-28 gate's own header): a fixed additive safety
# margin on top of the observed max in-family distance. Same order of magnitude as the
# jitter/false-positive band `stroke_codebook.DEFAULT_DTW_THRESHOLD`'s own module comment
# already established (realistic jitter ~0.108, distinct-shape floor ~0.50) — large enough to
# absorb ordinary measurement noise in the max-distance estimate itself, small enough to still
# separate from the distinct-shape floor in every case that comment documents.
DEFAULT_MARGIN = 0.05

# Pre-registered: a family needs at least this many measured in-family distances before its
# OWN max-based threshold is trusted; fewer than this pools into the GLOBAL sample instead.
DEFAULT_MIN_FAMILY_SAMPLES = 20


def _measure_stroke(agent, points: list, dk: dict,
                     turn_edges: Optional[list] = None,
                     len_edges: Optional[list] = None) -> list[tuple[str, float]]:
    """INGEST -> DECODE one raw stroke (mechanical, reuses `ink_decode.ingest_ink`/`decode_ink`
    verbatim -- no new geometry, no new decision), then for EVERY accepted span (whatever tier
    matched it — fine, mid, coarse, dtw alike; the CORRECTED scope, see the module docstring's
    SCOPE section): resolve which FAMILY it matched (`r.get("family") or r.get("name")`,
    walked to its top-level, prototype-bearing root via `stroke_codebook._prototype_anchor` —
    the SAME resolution `homework_loop._family_root` already performs), then ONE held `DtwTo`
    evaluate between the span's own invariant prototype (`_invariant_points`, the identical
    real-valued normalization `_dtw_fallback`'s own candidates use) and that family's stored
    prototype. A family root carrying no prototype (a rebinned-legacy entry,
    `stroke_codebook.migrate_multigrain_codebook`'s own honest `prototype_available: False`
    case) contributes nothing — skipped, never a fabricated zero. An OOV/minted span
    contributes nothing to the IN-FAMILY distribution by definition (it has no family yet).
    NOTE on read-backs (the standing rule): `res["recognized"]` entries are plain dicts this
    codebase's own Python assembled, and `knots` comes from a graph attr (JSON lists) — no
    Rust-tuple surface here; the one `native.evaluate` result consumed (`DtwTo`) is a scalar.
    Returns `[(family_root, distance), ...]`, one entry per accepted span."""
    sub = _sub(agent)
    native = _native(agent)
    ink_node = ink.ingest_ink(agent, points, max_knots=dk["max_knots"])
    knots = np.asarray(sub.node(ink_node)["attrs"].get("knots") or [], dtype=float)
    res = ink.decode_ink(agent, ink_node, min_span=dk["min_span"], max_span=dk["max_span"],
                          segments=dk["segments"], turn_bins=dk["turn_bins"],
                          len_bins=dk["len_bins"], grid=dk["grid"], scale_bins=dk["scale_bins"],
                          turn_edges=turn_edges, len_edges=len_edges)
    out: list[tuple[str, float]] = []
    for r in res.get("recognized", []):
        family = r.get("family") or r.get("name")
        if family is None:
            continue
        family_root = sc._prototype_anchor(sub, family) or family
        proto_node = sc._find_stroke_node(sub, family_root)
        if proto_node is None:
            continue
        proto_json = sub.node(proto_node)["attrs"].get("prototype")
        if not proto_json:
            continue
        try:
            proto = json.loads(proto_json)
        except (TypeError, ValueError):
            continue
        span_pts = knots[r["start"]:r["end"]].tolist()
        span_proto = sc._invariant_points(span_pts)
        dist = native.evaluate({"type": "DtwTo", "a": {"type": "Lit", "value": span_proto},
                                 "b": {"type": "Lit", "value": proto}}, {})
        out.append((family_root, float(dist or 0.0)))
    return out


def _percentile(values: list, p: float) -> float:
    """Mechanical arithmetic (numpy's own interpolated percentile) — a descriptive statistic
    computed for the honest REPORT only (see module docstring: p95+margin is never applied)."""
    return float(np.percentile(np.asarray(values, dtype=float), p)) if values else 0.0


def calibrate_dtw_thresholds(agent, stroke_sources: list, dk: dict, *,
                              margin: float = DEFAULT_MARGIN,
                              min_family_samples: int = DEFAULT_MIN_FAMILY_SAMPLES,
                              fail_on_empty: bool = True,
                              turn_edges: Optional[list] = None,
                              len_edges: Optional[list] = None,
                              measured_pairs: Optional[list] = None) -> dict[str, Any]:
    """THE calibration pass. `stroke_sources`: a plain list of raw `[[x, y], ...]` point-lists
    — the caller's own job (a world-adapter / gate-script concern, per CLAUDE.md's own
    ingest/emit split) is gathering WHICH strokes constitute "the LEARN population" (this
    module stays domain-general, no Omniglot-specific alphabet/drawer logic here). Must be run
    against a substrate whose codebook is ALREADY BUILT (LEARN already complete) — this
    function never mints, it only measures + calibrates against what is already held.

    For each source stroke, `_measure_stroke` yields zero or more `(family_root, distance)`
    pairs (one per recognized span — a multi-span stroke contributes multiple observations,
    exactly reflecting how many real in-family shape instances it contained). Pooled by
    `family_root`: a family with `>= min_family_samples` observations gets its OWN
    `dtw_reject_threshold` attr (`max(distances) + margin`) written onto its own top-level
    `ShapeSignature{kind:"stroke"}` node; every data-starved family's observations are pooled
    into ONE global sample, whose own `max + margin` is written as
    `dtw_near_threshold_calibrated` on the agent root (the fallback `ink_decode.
    _resolve_dtw_threshold` reads for any family with no per-family threshold of its own).

    SANITY GATE (`fail_on_empty`, default True): a calibration whose TOTAL measured sample is
    empty raises `EmptyCalibrationError` instead of returning — a calibration that measured
    nothing installed nothing, and every downstream consumer would silently run with the lever
    inert (the exact anomaly the SCOPE correction documents). Additionally, every family that
    DID clear `min_family_samples` is asserted to have received a finite threshold before
    return.

    Returns a full, honest report: per-family sample counts/max/p95/mean and which calibration
    each family received, the pooled-global sample stats, and the exact threshold values
    written — nothing here is applied silently."""
    sub = _sub(agent)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = _agent_root_node(sub)

    by_family: dict[str, list] = {}
    n_strokes_measured = 0
    n_spans_measured = 0
    if measured_pairs is not None:
        # RUN 32 (ops): `measured_pairs` = `[(family, dist), ...]` a checkpointed caller
        # ALREADY collected via per-stroke `_measure_stroke` calls (a gate script batching
        # measurement across <=540s foreground invocations — the run31 discipline). The
        # measurement itself is the SAME code path (`_measure_stroke`, called by the batching
        # caller); this branch only skips re-measuring, then applies the identical
        # pre-registered install/report formula below. `stroke_sources` is ignored;
        # `n_strokes_measured` is reported as the caller's own pair count provenance
        # (per-stroke counts live in the caller's checkpoint meta).
        n_strokes_measured = -1
        for (family, dist) in measured_pairs:
            by_family.setdefault(family, []).append(float(dist))
            n_spans_measured += 1
    else:
        for points in stroke_sources:
            pairs = _measure_stroke(agent, points, dk, turn_edges=turn_edges, len_edges=len_edges)
            n_strokes_measured += 1
            for (family, dist) in pairs:
                by_family.setdefault(family, []).append(dist)
                n_spans_measured += 1

    if fail_on_empty and (n_spans_measured == 0 or not by_family):
        raise EmptyCalibrationError(
            f"calibration measured NOTHING (n_strokes_measured={n_strokes_measured}, "
            f"n_spans_measured={n_spans_measured}, n_families={len(by_family)}) — no threshold "
            "was installed and every downstream arm would run with the lever silently inert; "
            "refusing to return a vacuous report (pass fail_on_empty=False only in a test that "
            "deliberately exercises this failure mode)")

    per_family_report: dict[str, dict] = {}
    pooled: list = []
    calibrated_families: list = []
    pooled_families: list = []

    for family, dists in by_family.items():
        n = len(dists)
        stats = {
            "n": n, "max": max(dists), "p95": _percentile(dists, 95.0),
            "mean": float(np.mean(dists)),
        }
        if n >= min_family_samples:
            threshold = stats["max"] + margin
            node = sc._find_stroke_node(sub, family)
            if node is not None:
                sub.set_attr(node, "dtw_reject_threshold", float(threshold))
                stats["calibration"] = "per_family"
                stats["threshold"] = float(threshold)
                calibrated_families.append(family)
            else:
                # Honest edge case: the family root disappeared from the graph between
                # measurement and install (should not happen in a single calibration call) --
                # fall through to pooling rather than silently dropping the data.
                pooled.extend(dists)
                stats["calibration"] = "pooled_missing_node"
                pooled_families.append(family)
        else:
            pooled.extend(dists)
            stats["calibration"] = "pooled_data_starved"
            pooled_families.append(family)
        per_family_report[family] = stats

    global_report: Optional[dict] = None
    if pooled:
        pooled_threshold = max(pooled) + margin
        global_report = {"n": len(pooled), "max": max(pooled), "p95": _percentile(pooled, 95.0),
                          "mean": float(np.mean(pooled)), "threshold": float(pooled_threshold)}
        if ag_node is not None:
            sub.set_attr(ag_node, "dtw_near_threshold_calibrated", float(pooled_threshold))

    # SANITY GATE, second half: every well-sampled family must actually carry a FINITE
    # installed threshold (max over a nonempty float list + a finite margin is finite by
    # construction — this guards the install/read-back path, not the arithmetic).
    for family in calibrated_families:
        installed = per_family_report[family].get("threshold")
        if installed is None or not np.isfinite(installed):
            raise EmptyCalibrationError(
                f"family {family!r} cleared min_family_samples but carries no finite "
                f"threshold ({installed!r}) — install/read-back path broken")

    return {
        "n_strokes_measured": n_strokes_measured, "n_spans_measured": n_spans_measured,
        "n_families": len(by_family), "per_family": per_family_report,
        "calibrated_families": calibrated_families, "pooled_families": pooled_families,
        "global": global_report, "margin": margin, "min_family_samples": min_family_samples,
        "formula": "threshold = max(observed_in_family_distances) + margin (pre-registered; "
                   "p95+margin reported per-family/global for transparency but never applied)",
    }


__all__ = ["calibrate_dtw_thresholds", "EmptyCalibrationError", "DEFAULT_MARGIN",
           "DEFAULT_MIN_FAMILY_SAMPLES"]
