"""frame — THE FRAME PRIMITIVE (graph-resident), the creator's founding ontology made explicit
(culminated 2026-07-04). A FRAME is a SET OF DIMENSIONS with RELATIVE WEIGHTING — the physics
reference frame (coordinates = dimensions, metric = the relative weighting). It is the third leg of
"relative all the way down":

  * a VALUE is a relative position in an axis (not an absolute 5);
  * a WEIGHT is a DIMENSIONAL LOG-SCALED VECTOR BETWEEN NODES — the EDGE itself: a directed
    displacement along a dimension with a LOG-SCALED magnitude (a log-ratio log(a)-log(b)=log(a/b),
    so it is frame-independent and path-additive);
  * a FRAME is a set of dimensions with RELATIVE weighting (which axes are in play + how much each
    counts vs the others; the relative weighting makes a frame itself comparable/transformable).

GRAPH FORM (CLAUDE.md — the Frame is GRAPH DATA, not a Python object):

    Frame { key }
      -[in_dim]-> Dimension { name }        (one edge per dimension in the frame)
      -[in_dim]-> Dimension { name }
      ...
    Frame.log_weights = { dim_name: log_weight, ... }

The dimension edges are the graph-resident membership; the per-dimension LOG-WEIGHT rides on the
Frame node's `log_weights` attr keyed by dimension name — the readable form of "the edge's weight"
(substrate_rs stores but does not expose per-edge attrs for read-back, so the log-weight is mirrored
on the node, the same pattern context_model uses for its per-dim `feat_counts`). Both are written on
`build_frame`; the edge and the attr always agree.

WEIGHTS ARE RELATIVE + LOG-SCALED. `build_frame` takes LINEAR relative weights (importance / counts)
and stores their LOGS, so:
  * all-equal dims  -> equal log-weights (a frame with no dominant axis);
  * a dominant dim  -> +k log-steps above the others (its weight is e^k times theirs);
  * the RELATIVE weighting between two dims is `dimension_weight(a) - dimension_weight(b)` = log(a/b)
    — the log-ratio, frame-independent (`relative_weight`).
A dimension NOT in the frame has weight -inf (absent), so `in_frame` is a membership query and
`dimension_weight` degrades to -inf rather than raising.

THE OPS ARE GRAPH QUERIES, NOT CLASSIFIERS. `in_frame` / `dimension_weight` / `frame_dims` read the
frame's dimensions and weights — membership and weight, never a cue-table decision. This is the
substrate the coarse cue-table foreign/live classifiers are replaced by: the DECISION "is concept X
foreign?" becomes the QUERY "is X's dimension in the interlocutor's frame (at/above a weight)?".

A frame is accepted in two forms so a caller with a live substrate uses the graph-resident node and a
caller without one (an agent-less faculty path) uses the frame's VALUE twin — a plain
{dim: log_weight} dict — with identical relative-log-weight semantics:
  * a Frame NodeID (graph-resident) — pass the `agent` so the node's `log_weights` can be read;
  * a {dim: log_weight} dict — the value form; `agent` may be None.

DONKEY=0: no fit, no gradient, no LM — arithmetic over graph data.
"""
from __future__ import annotations

import math
from typing import Iterable, Mapping, Optional, Union

_NEG_INF = float("-inf")

# a frame is either a graph node (NodeID) or its value twin (a {dim: log_weight} dict).
Frame = Union["object", Mapping[str, float]]

_FRAME_TYPE = "Frame"
_DIM_TYPE = "Dimension"
_DIM_EDGE = "in_dim"


# --------------------------------------------------------------------------- #
#  BUILD — write a Frame node + log-weighted Dimension edges into the graph.
# --------------------------------------------------------------------------- #

def _log_weights(dims_with_weights) -> dict:
    """Normalise the input to a {dim: log_weight} map. Accepts either a mapping dim -> LINEAR relative
    weight (importance / count, positive) whose logs are stored, or a bare iterable of dim names (each
    at weight 1.0 -> log_weight 0.0, an equal-weight frame). A non-positive weight is floored to a tiny
    positive so its log is finite-and-low rather than -inf (absence is expressed by omission, not 0)."""
    out: dict = {}
    if isinstance(dims_with_weights, Mapping):
        for dim, w in dims_with_weights.items():
            wv = float(w)
            out[str(dim)] = math.log(wv) if wv > 0 else math.log(1e-9)
    else:
        for dim in dims_with_weights:
            out[str(dim)] = 0.0            # weight 1.0 -> log 0.0 (equal-weight dimension)
    return out


def _dimension_node(agent, name: str):
    """Find-or-create the persistent Dimension node for `name` (dimensions are shared graph
    vocabulary, reused across frames). Mechanical graph write."""
    for nid in agent.s.nodes(_DIM_TYPE):
        if agent.s.node(nid)["attrs"].get("name") == name:
            return nid
    return agent.s.add_node(_DIM_TYPE, {"name": name})


def _frame_node_by_key(agent, key: str):
    for nid in agent.s.nodes(_FRAME_TYPE):
        if agent.s.node(nid)["attrs"].get("key") == key:
            return nid
    return None


def build_frame(agent, dims_with_weights, key: str):
    """Build (or refresh, by `key`) a graph-resident Frame: a Frame node carrying `log_weights`, with
    one `in_dim` edge to each Dimension node in the frame (log-weighted). Returns the Frame NodeID.

    `dims_with_weights` — a mapping dim -> LINEAR relative weight (logged on store) or a bare iterable
    of dim names (equal weight). Rebuilding under the same `key` replaces the frame's dimensions in
    place (idempotent view: the manifold/context/shape frame is refreshed each turn, not accumulated).
    """
    logw = _log_weights(dims_with_weights)
    frame = _frame_node_by_key(agent, key)
    if frame is None:
        frame = agent.s.add_node(_FRAME_TYPE, {"key": key, "log_weights": logw})
    else:
        # refresh: drop stale in_dim edges, then rewrite (idempotent by key).
        for tgt in list(agent.s.neighbours(frame, _DIM_EDGE)):
            try:
                agent.s.remove_edge_unchecked(frame, _DIM_EDGE, tgt)
            except Exception:
                pass
        agent.inner.set_attr(frame, "log_weights", logw)
    for dim, w in logw.items():
        dnode = _dimension_node(agent, dim)
        try:
            agent.s.add_edge_unchecked(frame, _DIM_EDGE, dnode, {"log_weight": w})
        except Exception:
            agent.inner.add_edge_unchecked(frame, _DIM_EDGE, dnode)
    return frame


# --------------------------------------------------------------------------- #
#  QUERY — membership + weight, over a graph Frame node OR its value-form dict.
# --------------------------------------------------------------------------- #

def _weights(agent, frame: Frame) -> dict:
    """The frame's {dim: log_weight} map. A dict frame is returned as-is (the value form); a NodeID
    frame is read off the graph (its `log_weights` attr) — the graph-resident form (needs `agent`)."""
    if isinstance(frame, Mapping):
        return dict(frame)
    return dict(agent.s.node(frame)["attrs"].get("log_weights") or {})


def frame_dims(frame: Frame, agent=None) -> list:
    """The dimensions in the frame (which axes are in play), sorted by name."""
    return sorted(_weights(agent, frame).keys())


def dimension_weight(frame: Frame, dim: str, agent=None) -> float:
    """The dimension's RELATIVE LOG-WEIGHT in the frame, or -inf when the dimension is NOT in the
    frame (absent). Frame-independent: differences of two dims' weights are the log-ratio between
    them (`relative_weight`)."""
    return _weights(agent, frame).get(str(dim), _NEG_INF)


def in_frame(frame: Frame, dim: str, agent=None, *, min_weight: Optional[float] = None) -> bool:
    """Is `dim` a dimension of the frame — and, when `min_weight` is given, at/above that relative
    log-weight? The membership query that replaces the coarse cue-table foreign/live decision."""
    w = dimension_weight(frame, dim, agent=agent)
    if w == _NEG_INF:
        return False
    return True if min_weight is None else w >= float(min_weight)


def relative_weight(frame: Frame, dim_a: str, dim_b: str, agent=None) -> float:
    """The RELATIVE weighting between two dimensions = log_weight(a) - log_weight(b) = log(a/b): the
    log-ratio (the edge between the two axes), frame-independent. -inf/inf when one is absent."""
    wa = dimension_weight(frame, dim_a, agent=agent)
    wb = dimension_weight(frame, dim_b, agent=agent)
    if wa == _NEG_INF and wb == _NEG_INF:
        return 0.0
    return wa - wb


__all__ = ["build_frame", "in_frame", "dimension_weight", "frame_dims", "relative_weight"]
