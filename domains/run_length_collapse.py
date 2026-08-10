"""run_length_collapse — the agent COARSENS the per-frame unit grain BEFORE
chunking, the next constraint iteration-3 located by live measurement.

WHAT IT FIXES (iteration-3's located binding constraint). The per-frame unit
stream runs at ~7.5 units/word (frames/word grain 7.56, measured live). The
TP-trough chunker — even the local-minimum boundary Term the agent forward-built
— can only ever land near ~7 chunks/word because ANY chunker that cuts within a
word inherits the grain: the stream is ~7.5x finer than the word rate, so the
boundary RULE was never the binding constraint, the GRAIN is. The agent's own
diagnosis (docs/agent_loop_iteration3.md §3): coarsen the unit grain (run-length
collapse) BEFORE the TP chunker runs.

THE SCIENCE the agent reasons from (its OWN segmentation science). A PHONE is a
STABLE acoustic segment that SPANS MULTIPLE FRAMES sharing one articulatory
configuration. The k-means codebook already discretises each frame to the nearest
unit; a phone is therefore a RUN of consecutive frames that quantise to the SAME
unit. Collapsing each such run to ONE coarser unit drops the stream from the
per-frame grid (~7.5/word) toward the phone/syllable grid (a few per word) — the
HuBERT-style "de-duplicate consecutive units" step, which is exactly the infant /
self-supervised move from frame-rate to segment-rate before lexical grouping.

THE COLLAPSE CRITERION (the agent's choice, from its science). Two readings:

  • RAW-ID run-collapse (the DIRECT reading): merge a maximal run of consecutive
    frames carrying the SAME codebook id. The unit IS the discretised stable
    segment — that is what the codebook is FOR — so equal-id runs ARE the phones.
    No free parameter: the run boundary is exactly where the id changes.

  • STABILITY run-collapse (the order-1 refinement): per-frame quantisation
    FLICKERS (a steady phone can dither between two near-equidistant centroids),
    so raw-id under-merges at the dither points. The agent's own order-1
    sign-change / low-velocity concept (order_n_concepts) says a phone is where the
    acoustic trajectory is SLOW — low frame-to-frame change. Merge across a flicker
    when the frames are acoustically close (a small spectral step), splitting only
    at a LARGE step (a real articulatory move). The split level is the running
    median of the inter-frame steps — a statistic OF the data, NOT a swept knob
    (the same structure-derived-level discipline forward_segmentation uses).

The agent's PRIMARY pick is RAW-ID (the direct, parameter-free reading of its own
codebook); STABILITY is the order-1 refinement offered for the flicker the raw
reading leaves. The probe reports both, LIVE, and lets the measurement say which —
no tuning to a number.

GRAPH-RESIDENT DECISION (architecture rule, mirrors forward_segmentation). The
collapse DECISION is NOT a Python `if`. Each frame becomes a `Frame` node carrying
its `unit` id, its `prev_unit` id, and (for the stability variant) its inter-frame
`step` and the running-median `step_level`. The RUN-START set — the frames that
BEGIN a new coarse unit — is a Filter Term the agent evaluates natively:

    raw-id     : Filter(frames, f, Neq(f.unit, f.prev_unit))
    stability  : Filter(frames, f, Gt(f.step, f.step_level))   # large step = split

— "the frames where the unit changes / the acoustic step is large." The agent runs
its own program over the frame structure to find the run starts; Python only
translates frames->nodes (the same mechanical structure translation `tp`/`prev_tp`
are in forward_segmentation) and assembles the merged spans the run-starts delimit.

This module is the world-adapter + the agent's coarsening operator. The decision
runs in the substrate; the span-merge is mechanical assembly. No agent reasoning
lives in Python beyond that translation.
"""
from __future__ import annotations

from collections import defaultdict


# ---------------------------------------------------------------------------
# Graph-resident Term constructors (raw JSON wire form — identical encoding to
# substrate_rs Term.to_dict; the forward_segmentation / recognition_graph
# pattern). These BUILD the agent's reasoning as data; they make no decision.
# ---------------------------------------------------------------------------

def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def _Not(x): return {"type": "Not", "arg": x}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t,
                                  "attr_key": k, "value": v}
def _Filter(src, var, pred): return {"type": "Filter", "source": src,
                                     "var_name": var, "predicate": pred}


class _Pred:
    """Tiny Term carrier so substrate.evaluate (which unwraps `._json`) accepts a
    raw JSON Term dict — the same shim forward_segmentation / recognition_graph use."""
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def runstart_term_raw(seq_tag: str) -> dict:
    """The graph-resident RUN-START rule (raw-id collapse): the Frame nodes whose
    codebook unit DIFFERS from the previous frame's — i.e. the frames that BEGIN a
    new maximal equal-id run.

        Filter(NodesWhere(Frame, seq, <tag>), f, Not(Eq(f.unit, f.prev_unit)))

    A run start is exactly where the discretised stable segment changes. The agent
    evaluates this Term natively to find every coarse-unit boundary."""
    f = _V("f")
    return _Filter(
        _NodesWhere("Frame", "seq", _Lit(seq_tag)),
        "f",
        _Not(_Eq(_Attr(f, "unit"), _Attr(f, "prev_unit"))))


def runstart_term_stability(seq_tag: str) -> dict:
    """The graph-resident RUN-START rule (stability / order-1 refinement): the Frame
    nodes whose inter-frame acoustic STEP exceeds the running-median step level — a
    LARGE articulatory move, the true segment boundary; small steps (flicker within a
    steady phone) are merged across.

        Filter(NodesWhere(Frame, seq, <tag>), f, Gt(f.step, f.step_level))

    `step` is the L2 distance from the previous frame; `step_level` is the running
    median of all steps (structure-derived, not swept). The agent's order-1
    low-velocity concept on the trajectory."""
    f = _V("f")
    return _Filter(
        _NodesWhere("Frame", "seq", _Lit(seq_tag)),
        "f",
        _Gt(_Attr(f, "step"), _Attr(f, "step_level")))


def _median(values) -> float:
    vs = sorted(values)
    n = len(vs)
    if n == 0:
        return 0.0
    m = n // 2
    return vs[m] if n % 2 else 0.5 * (vs[m - 1] + vs[m])


def _install_frames(substrate, units, steps, step_level, seq_tag: str) -> list:
    """Translate one utterance's per-frame units (and inter-frame steps) into graph
    Frame nodes carrying the structure the run-start Terms read. Mechanical I/O->graph
    (the same role forward_segmentation._install_transitions plays).

      • `unit`      : this frame's codebook id.
      • `prev_unit` : the previous frame's id (a SENTINEL for frame 0, which is always
                      a run start).
      • `step`      : L2 distance from the previous frame (for the stability variant);
                      frame 0 gets a SENTINEL-high step so it always starts a run.
      • `step_level`: the running median of the steps (the structure-derived split
                      level), stored on every frame so the Term reads it via Attr.
    Returns the ordered Frame NodeIDs."""
    try:
        substrate.add_production({
            "src": {"type": "Frame", "var": "a"},
            "edge_type": "in_seq",
            "tgt": {"type": "FrameSeq", "var": "b"},
            "provenance": "run_length_collapse:frame"})
    except Exception:
        pass
    SENTINEL_ID = -987654321        # never a real codebook id -> frame 0 differs
    SENTINEL_STEP = 1e9             # frame 0 step is huge -> always a run start
    nodes = []
    for i, u in enumerate(units):
        nodes.append(substrate.add_node("Frame", {
            "seq": seq_tag, "pos": i,
            "unit": int(u),
            "prev_unit": int(units[i - 1]) if i > 0 else SENTINEL_ID,
            "step": float(steps[i]) if i > 0 else SENTINEL_STEP,
            "step_level": float(step_level),
            "origin": "run_length_collapse"}))
    return nodes


def _frame_steps(M):
    """Per-frame L2 step from the previous frame (frame 0 -> 0.0; the installer
    overrides frame 0 with a sentinel). M is frames x bands. Pure structure stat."""
    import numpy as np
    if M is None or len(M) < 2:
        return [0.0] * (0 if M is None else len(M))
    d = np.linalg.norm(np.diff(M, axis=0), axis=1)
    return [0.0] + [float(x) for x in d]


def find_runstarts_via_graph(substrate, units, seq_tag, mode="raw_id", M=None):
    """The agent finds the coarse-unit run starts by EVALUATING its own run-start Term
    over the Frame structure — natively, in the substrate (NOT a Python loop). Returns
    the SORTED list of run-start positions (each begins a new coarse unit).

    mode:
      • "raw_id"    — split where the codebook id changes (Neq term). Direct reading.
      • "stability" — split where the inter-frame step exceeds its running median (Gt
                      term). Order-1 refinement; needs the frame matrix M for steps.
    """
    if mode == "stability":
        if M is None:
            raise ValueError("stability mode needs the frame matrix M for steps")
        steps = _frame_steps(M)
        # structure-derived level: median of the genuine inter-frame steps (skip the
        # sentinel frame-0). Not a swept knob.
        step_level = _median(steps[1:]) if len(steps) > 1 else 0.0
        term = runstart_term_stability(seq_tag)
    else:
        steps = [0.0] * len(units)
        step_level = 0.0
        term = runstart_term_raw(seq_tag)
    _install_frames(substrate, units, steps, step_level, seq_tag)
    try:
        start_nodes = substrate.evaluate(_Pred(term), None)
    except Exception:
        raise
    starts = sorted(int(substrate.node(n)["attrs"].get("pos", -1))
                    for n in start_nodes)
    starts = [s for s in starts if s >= 0]
    if not starts or starts[0] != 0:
        starts = [0] + starts          # position 0 always begins the first run
    return starts


# ---------------------------------------------------------------------------
# Mechanical assembly: the run-starts delimit the coarse units. A coarse unit's
# id = the (majority) codebook id of its run; its span = [start, next_start).
# ---------------------------------------------------------------------------

def collapse_units(units, starts):
    """Assemble coarse units from the run-start positions. Returns a list of
    (coarse_unit_id, run_length) pairs. The coarse id is the run's majority codebook
    id (== the single id for a raw-id run; the dominant id for a stability run that
    merged across flicker). Mechanical."""
    starts = sorted(set(starts) | {0})
    bounds = starts + [len(units)]
    out = []
    for a, b in zip(bounds, bounds[1:]):
        if b <= a:
            continue
        run = units[a:b]
        counts = defaultdict(int)
        for u in run:
            counts[int(u)] += 1
        cid = max(counts.items(), key=lambda kv: kv[1])[0]
        out.append((cid, b - a))
    return out


def collapse_stream(substrate, units, seq_tag, mode="raw_id", M=None):
    """Full coarsening of ONE utterance: find run starts via the graph Term, assemble
    the coarse (id, length) units. Returns {coarse_units, coarse_ids, lengths,
    starts}."""
    if len(units) == 0:
        return {"coarse_units": [], "coarse_ids": [], "lengths": [], "starts": []}
    starts = find_runstarts_via_graph(substrate, units, seq_tag, mode=mode, M=M)
    coarse = collapse_units(units, starts)
    return {
        "coarse_units": coarse,
        "coarse_ids": [c for c, _ in coarse],
        "lengths": [L for _, L in coarse],
        "starts": starts,
    }


__all__ = [
    "runstart_term_raw",
    "runstart_term_stability",
    "find_runstarts_via_graph",
    "collapse_units",
    "collapse_stream",
]
