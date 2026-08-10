"""frame_weights — RUN 30: WEIGHTS AS EDGES, A FRAME AS N DIMENSIONS WITH RELATIVE WEIGHTING.

The creator's directive, verbatim: "All weights are not vectors, they are edges to other
nodes — weights are relative, order n and log scaled." + "A frame is N dimensions/axes with
relative weighting." This is a REPRESENTATION REFORM of what run 29 built
(`domains/arrangement_codebook.py`'s `relation_weights`: a Python-mutated dict living in ONE
node attr, invisible to `run_rules` — the metric arithmetic WAS cognition, a CLAUDE.md
violation in spirit even though every individual comparison stayed within the codebase's own
"plain comparison of two already-fetched values" allowance).

THE REFORM: a codebook quantum's signature (N relations) + its per-relation stability IS A
FRAME — basis + metric, graph-resident, updated only by graph rules.

GRAPH FORM:

    ShapeSignature{kind:"character"} --has_frame--> Frame{key}
                                                        |--in_dim--> FrameAxis{name,kind,log_weight}
                                                        |--in_dim--> FrameAxis{name,kind,log_weight}
                                                        ...
    FrameAxis --has_evidence--> AxisEvidence{agree, applied}   (one per observed rep, the
                                                                 adapter's mechanical write)

REUSE, NOT A PARALLEL FRAME TYPE (per the run-30 directive's own instruction — check first
whether the substrate already has Frame conventions, reuse them if they fit): `domains/
frame.py` already established the Frame node TYPE + the `in_dim` edge convention exactly ("a
FRAME is a set of dimensions with RELATIVE weighting... the log-weight is mirrored on the
node [it points at], the same pattern context_model uses" — because `substrate_rs` stores but
does not expose per-edge attrs for read-back). Both facts transfer here unchanged, so this
module reuses the `Frame` node TYPE (`domains.frame`'s own module-level string) and the
`in_dim` edge type verbatim.

WHAT DOES NOT TRANSFER, AND WHY A DISTINCT AXIS TYPE: `domains/frame.py`'s own `Dimension`
node type is explicitly documented as SHARED VOCABULARY, find-or-created BY NAME GLOBALLY and
REUSED ACROSS MANY frames (its own worked example: "ethics"/"philosophy" as concepts many
different frames reference). A character quantum's own "rel:0:x" axis is NOT that — it is
intrinsically LOCAL to ONE quantum's own observed reliability; two different quanta that both
happen to have a "rel:0:x" key must NOT share one graph node (that would silently pool their
reliabilities, exactly the bug this reform exists to avoid at the SHARED-frame layer only,
deliberately, via `fw_pool` — never by accidental node aliasing at the per-quantum layer). So
this module introduces `FrameAxis` — a NODE TYPE DISTINCT from `Dimension` — scoped to
belong to exactly one Frame (found via ITS OWN `in_dim` edge, never a global by-name lookup).
The one place axes genuinely ARE shared vocabulary — the POOLED frame, one axis per relation
KIND across every held quantum — uses the exact same `FrameAxis` type with `scope="pooled"`;
`fw_pool` computes ITS log_weight from every `scope="quantum"` FrameAxis sharing that `kind`.

WEIGHT DYNAMICS ARE GRAPH RULES, NOT PYTHON ARITHMETIC (`seeds/frame_weights.json`):
  * `fw_update` — an AxisEvidence node (the adapter's mechanical write: "axis X agreed/
    disagreed this rep") drives ONE weight recomputation, entirely inside a held Term
    (Exp(log_weight) -> affine EMA-toward-bound combination -> Log(...) back) fired by
    `run_rules`. Python never computes or writes a new weight value — it only compares two
    already-fetched scalars to decide agree/disagree (mechanical evidence translation, the
    same class of comparison `homework_loop._resolved_key`'s own family-root equality check
    already uses throughout this codebase) and writes the evidence node.
  * `fw_pool` — the shared frame's own per-kind pooling is a log-additive evidence
    combination (mean of linear reliabilities via Sum(Exp(...))/Count, then Log(...) back),
    likewise a held Term inside a rule, triggered only by an explicit `PoolRequest` marker
    (cheap match_type-indexed enumeration: zero cost when nothing asked for a pool refresh,
    so the per-rep `fw_update` hot path never pays for pooling it did not request).

DONKEY=0: no fit, no gradient, no LM — graph rules + arithmetic over already-fetched scalars.
"""
from __future__ import annotations

import math
from typing import Optional

from domains import frame as fr
from domains.reflective_faculty import _agent_root_node, _ensure_seed_chain
from domains.stroke_codebook import _native, _sub

FRAME_WEIGHTS_SEED = ("frame_weights",)

AXIS_TYPE = "FrameAxis"
EVIDENCE_TYPE = "AxisEvidence"
POOL_REQUEST_TYPE = "PoolRequest"
IN_AXIS_EDGE = "in_dim"            # reuse domains.frame's OWN Frame -> dimension-like edge type.
HAS_FRAME_EDGE = "has_frame"
HAS_EVIDENCE_EDGE = "has_evidence"
REQUESTED_BY_EDGE = "requested_by"

DEFAULT_WEIGHT = 1.0
MIN_WEIGHT = 0.1
MAX_WEIGHT = 1.0
DEFAULT_STABILITY_STEP = 0.15
_DEFAULT_LOG_WEIGHT = 0.0          # log(DEFAULT_WEIGHT) == log(1.0) == 0.0.

POOLED_FRAME_KEY = "pooled:character_relation_kind"


# --------------------------------------------------------------------------- #
#  SEED LOADING — idempotent, mirrors `reflective_faculty._ensure_shape_decode_loop`'s own
#  pattern via the shared `_ensure_seed_chain` helper (no per-module reimplementation).
# --------------------------------------------------------------------------- #
def ensure_loaded(sub, native, ag_node) -> None:
    _ensure_seed_chain(sub, native, ag_node, FRAME_WEIGHTS_SEED)


def _agent_of(agent, sub):
    ag = getattr(agent, "agent", None)
    return ag if ag is not None else _agent_root_node(sub)


# --------------------------------------------------------------------------- #
#  RELATION-KEY -> KIND — moved here from `arrangement_codebook.py` (its sole use is axis
#  "kind" tagging, now a frame_weights concern): mechanical (no decision) reduction of a
#  position-specific weight key (`rel:<k>:<x|y|o|s>`) to its position-INDEPENDENT kind label
#  (`'x'/'y'/'o'/'s'`), or the key unchanged for an already position-independent `cpose_*`
#  singleton.
# --------------------------------------------------------------------------- #
def _relation_kind_from_weight_key(key: str) -> str:
    if key.startswith("rel:"):
        return key.rsplit(":", 1)[-1]
    return key


# --------------------------------------------------------------------------- #
#  FRAME + AXIS — find-or-create, reusing `domains.frame`'s OWN Frame node TYPE (a plain
#  string constant reference, not a call into `build_frame` — that function REPLACES a
#  frame's dimensions wholesale on every call, wrong for an incrementally-grown frame whose
#  axes accrue one at a time and are updated by RULES, never rebuilt from scratch).
# --------------------------------------------------------------------------- #
def _frame_node_by_key(sub, key: str) -> Optional[int]:
    for nid in sub.nodes(fr._FRAME_TYPE):
        if sub.node(nid)["attrs"].get("key") == key:
            return nid
    return None


def ensure_frame(sub, key: str) -> int:
    node = _frame_node_by_key(sub, key)
    if node is None:
        node = sub.add_node(fr._FRAME_TYPE, {"key": key})
    return node


def _axis_node_in_frame(sub, frame_node, name: str) -> Optional[int]:
    for nid in sub.neighbours(frame_node, IN_AXIS_EDGE):
        if sub.node(nid)["attrs"].get("name") == name:
            return nid
    return None


def ensure_axis(sub, frame_node, name: str, *, scope: str, kind: Optional[str] = None) -> int:
    """Find-or-create the FrameAxis node for `name` WITHIN this one frame (never a global
    by-name lookup — see this module's own top-of-file docstring for why axes are
    frame-local, unlike `domains.frame`'s shared `Dimension` vocabulary). A freshly-created
    axis starts at `DEFAULT_WEIGHT` (`log_weight=0.0`) — every relation defaults to full
    reliability until evidence says otherwise, the same convention run 29's own
    `relation_weights.get(key, DEFAULT_WEIGHT)` fallback established."""
    node = _axis_node_in_frame(sub, frame_node, name)
    if node is not None:
        return node
    attrs = {"name": name, "scope": scope, "log_weight": _DEFAULT_LOG_WEIGHT,
             "kind": kind or _relation_kind_from_weight_key(name)}
    node = sub.add_node(AXIS_TYPE, attrs)
    sub.add_edge_unchecked(frame_node, IN_AXIS_EDGE, node)
    return node


def axis_log_weight(sub, frame_node, name: str) -> float:
    """Mechanical read: an axis absent from this frame reads at `DEFAULT_WEIGHT`'s own log
    (0.0) — never fabricates a different default, mirrors run 29's own dict `.get(key,
    DEFAULT_WEIGHT)` fallback exactly."""
    node = _axis_node_in_frame(sub, frame_node, name)
    if node is None:
        return _DEFAULT_LOG_WEIGHT
    return float(sub.node(node)["attrs"].get("log_weight", _DEFAULT_LOG_WEIGHT))


def axis_weight(sub, frame_node, name: str) -> float:
    """`exp(axis_log_weight(...))` — a representation CONVERSION of an already-computed
    value, not a decision (the same class of "arithmetic on an already-Term-computed value"
    this codebase's own docstrings repeatedly sanction, e.g. `ink_decode.py`'s lattice-
    emission formula, `homework_loop._round_trip_score`'s `(n-len(residual))/n`)."""
    return math.exp(axis_log_weight(sub, frame_node, name))


def frame_axis_weights(sub, frame_node) -> dict:
    """Mechanical read-back: every axis this frame holds, `{name: weight}` (linear, via
    `exp`) — the frame-based twin of run 29's own `relation_weights` dict return shape, so
    callers built against that shape need no changes."""
    out: dict = {}
    for nid in sub.neighbours(frame_node, IN_AXIS_EDGE):
        at = sub.node(nid)["attrs"]
        nm = at.get("name")
        if nm:
            out[nm] = math.exp(float(at.get("log_weight", _DEFAULT_LOG_WEIGHT)))
    return out


# --------------------------------------------------------------------------- #
#  PER-QUANTUM FRAME — construction at MINT time (called from `character_compose.
#  grow_character_quantum`'s install path — graph DATA EMISSION from an already-composed
#  signature's own already-known relation keys, legal seed-builder work per CLAUDE.md, never
#  a re-decision) + evidence writing (called from `arrangement_codebook.
#  update_relation_stability` — mechanical translation of an already-decided agree/disagree
#  fact into graph data, never the weight arithmetic itself).
# --------------------------------------------------------------------------- #
def quantum_frame_key(quantum_name: str) -> str:
    return f"character_frame:{quantum_name}"


def ensure_quantum_frame(agent, quantum_node, quantum_name: str, relation_keys) -> int:
    """MINT-TIME install: the Frame + one FrameAxis per relation key already present on the
    composed signature (`relation_keys` — the caller's own already-extracted key list, e.g.
    `list(arrangement_codebook._relation_map(signature))`; kept as a plain argument here
    rather than re-deriving it from a raw signature so this module carries no dependency on
    `arrangement_codebook`'s own relation-extraction format, avoiding an import cycle:
    `arrangement_codebook` -> `character_compose` already exists, so `character_compose` ->
    `arrangement_codebook` would close a loop)."""
    sub = _sub(agent)
    native = _native(agent)
    ag_node = _agent_of(agent, sub)
    ensure_loaded(sub, native, ag_node)
    frame_node = ensure_frame(sub, quantum_frame_key(quantum_name))
    if not sub.has_edge(quantum_node, HAS_FRAME_EDGE, frame_node):
        sub.add_edge_unchecked(quantum_node, HAS_FRAME_EDGE, frame_node)
    for key in relation_keys:
        ensure_axis(sub, frame_node, key, scope="quantum")
    return frame_node


def write_axis_evidence(sub, axis_node, agree: bool) -> int:
    """Mechanical write (no decision — `agree` is an already-decided fact the caller computed
    by comparing two already-fetched scalar values, exactly like `homework_loop.
    _resolved_key`'s own family-root equality check): one `AxisEvidence` node, `has_evidence`
    edge from its own axis. `fw_update` (seeds/frame_weights.json) is the ONLY place that
    reads this node and decides the new weight."""
    ev = sub.add_node(EVIDENCE_TYPE, {"agree": 1.0 if agree else 0.0, "applied": 0.0})
    sub.add_edge_unchecked(axis_node, HAS_EVIDENCE_EDGE, ev)
    return ev


def update_quantum_frame(agent, quantum_node, quantum_name: str, agreements: dict) -> dict:
    """ONE evidence-writing + tick pass: `agreements` is `{relation_key: bool_agree, ...}`,
    already decided by the caller. Ensures each axis exists (defensive — normally already
    installed at mint time by `ensure_quantum_frame`, but a re-render can in principle carry
    a relation key the mint-time signature did not, e.g. a stroke split/merge; an honest
    lazy-create rather than a crash, mirrors run 29's own dict `.get(key, DEFAULT_WEIGHT)`
    tolerance for an unseen key), writes evidence for every key, then fires `run_rules` ONCE
    so `fw_update` recomputes every touched axis's weight inside its own held Term — never
    Python arithmetic on the weight. Returns `{"weights": {...}}`, the frame's full weight
    dict AFTER this pass (mechanical read-back)."""
    sub = _sub(agent)
    native = _native(agent)
    ag_node = _agent_of(agent, sub)
    ensure_loaded(sub, native, ag_node)
    frame_node = ensure_frame(sub, quantum_frame_key(quantum_name))
    if not sub.has_edge(quantum_node, HAS_FRAME_EDGE, frame_node):
        sub.add_edge_unchecked(quantum_node, HAS_FRAME_EDGE, frame_node)
    for key, agree in agreements.items():
        axis = ensure_axis(sub, frame_node, key, scope="quantum")
        write_axis_evidence(sub, axis, bool(agree))
    native.run_rules()
    return {"weights": frame_axis_weights(sub, frame_node)}


# --------------------------------------------------------------------------- #
#  SHARED / POOLED FRAME — one axis per relation KIND, pooled ACROSS every held quantum's own
#  `scope="quantum"` axes of that kind. `request_pool_refresh` is mechanical (enumerating
#  which kinds currently exist + minting a `PoolRequest` marker per kind is a fixed
#  structural scan, never a ranking); `fw_pool` (the rule) does the actual log-additive
#  combination.
# --------------------------------------------------------------------------- #
def request_pool_refresh(sub) -> int:
    frame_node = ensure_frame(sub, POOLED_FRAME_KEY)
    kinds = set()
    for nid in sub.nodes(AXIS_TYPE):
        at = sub.node(nid)["attrs"]
        if at.get("scope") == "quantum":
            k = at.get("kind")
            if k:
                kinds.add(k)
    for k in kinds:
        axis = ensure_axis(sub, frame_node, k, scope="pooled", kind=k)
        req = sub.add_node(POOL_REQUEST_TYPE, {"kind": k, "applied": 0.0})
        sub.add_edge_unchecked(axis, REQUESTED_BY_EDGE, req)
    return frame_node


def pooled_reliability(sub) -> dict:
    """`{kind: weight}` — the shared frame's own current pooled reliability, refreshed via
    `fw_pool` (one `run_rules` pass) before reading back. `{}` when no quantum axis exists
    yet (honest empty prior, never fabricated), the SAME contract run 29's own
    `pooled_relation_kind_reliability` established."""
    native = _native(sub)
    ag_node = _agent_of(sub, sub)
    has_any_quantum_axis = any(
        sub.node(nid)["attrs"].get("scope") == "quantum" for nid in sub.nodes(AXIS_TYPE))
    if not has_any_quantum_axis:
        return {}
    ensure_loaded(sub, native, ag_node)
    frame_node = request_pool_refresh(sub)
    native.run_rules()
    return frame_axis_weights(sub, frame_node)


__all__ = [
    "AXIS_TYPE", "EVIDENCE_TYPE", "POOL_REQUEST_TYPE", "IN_AXIS_EDGE", "HAS_FRAME_EDGE",
    "HAS_EVIDENCE_EDGE", "REQUESTED_BY_EDGE", "DEFAULT_WEIGHT", "MIN_WEIGHT", "MAX_WEIGHT",
    "DEFAULT_STABILITY_STEP", "POOLED_FRAME_KEY", "ensure_loaded", "ensure_frame",
    "ensure_axis", "axis_log_weight", "axis_weight", "frame_axis_weights",
    "quantum_frame_key", "ensure_quantum_frame", "write_axis_evidence",
    "update_quantum_frame", "request_pool_refresh", "pooled_reliability",
]
