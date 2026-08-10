"""imagination — TIER 3 of the collapse-modeling stack: holding/running the
collapse DETACHED from the external reference frame (= UNGROUNDING =
imagination / simulation / counterfactual), with a RETURN PATH back to
reality.

THE TIER LAW (the creator's correction this module implements): tier 1 is
collapse itself; tier 2 is residual-feedback, model-layer cognition that is
frame-LOCKED (confidently wrong outside its own basin, see
`seeds/residual_salience.json` / the 2026-07-02 incident); tier 3 is running
the SAME collapse machinery with the external-grounding pins REMOVED, so the
graph can explore a hypothesis reality doesn't currently support -- the
prerequisite for genuinely CHANGING frame, not just re-deriving within one.
This module builds ONLY the mechanical machinery (snapshot / cut / inject /
run / diff / reground / gated writeback) -- a separate follow-on task has the
agent AUTHOR the engage/judge rules that decide WHEN to imagine and WHAT to
do with the result. Nothing here is an agent decision: every function is
graph I/O (translate a request into mutations, run the substrate's own
collapse, translate the result back out), the exact shape CLAUDE.md permits
a Python adapter.

THE MECHANISM, end to end:

  1. SNAPSHOT   -- `graph_to_dict` (whole graph, or a `focus_nodes` BFS
                   closure) into a brand-new, id-preserving detached
                   `substrate_rs.Substrate` via `graph_from_dict`. Node ids
                   are shared vocabulary between the live graph and the
                   detached copy, so a conclusion's `detached_id` names the
                   SAME conceptual entity in both -- that is what lets
                   `reground` map an imagined conclusion back onto a live
                   node by identity. IMPORTANT: `graph_to_dict` /
                   `graph_from_dict` serialise ONLY the graph (nodes/edges,
                   e.g. graph-resident `Rule` nodes matched by
                   `run_graph_rules`) -- never the separate `add_rule`
                   rewrite-rule store (see tests/test_composer_graph_pilot.py's
                   module docstring). The agent's real cognition is
                   graph-resident `Rule` nodes, so it snapshots faithfully;
                   a caller that installed extra logic only via `add_rule`
                   on the LIVE substrate would not see it survive into the
                   detached copy -- install such logic on the detached copy
                   directly if that shape is ever needed.
  2. CUT GROUNDING -- remove every `grounded_in` edge (the provenance
                   channel `domains/grounding_reach.py` defines) from the
                   DETACHED copy only. This does not delete the anchor nodes
                   or the facts they were grounding -- only the "this is
                   externally confirmed" pin -- so the detached collapse can
                   no longer distinguish a grounded fact from an ungrounded
                   one via `ReachableFrom(*, "grounded_in")`, and any Rule
                   whose `where`/`match` is conditioned on that reachability
                   (a guard rule the follow-on task authors, or the
                   demonstration rules in `scripts/jabberwock_imagines.py`)
                   behaves differently than it would live.
  3. INJECT HYPOTHESIS -- mechanically translate a declarative
                   `{"nodes": [...], "edges": [...]}` spec into mutations on
                   the detached copy (the counterfactual assumption). Pure
                   ingest, no decision -- see `_inject_hypothesis`.
  4. RUN THE COLLAPSE -- `tick()` on the detached copy: this runs BOTH rule
                   stores the substrate has (graph-resident `Rule` nodes via
                   `run_graph_rules`, AND any `add_rule`-installed rewrite
                   rules already present on that specific Python object) to
                   a fixed point. The graph rules ARE the collapse; this
                   call propagates the hypothesis's consequences, unpinned
                   by reality.

`imagine()` returns a `DetachedCollapse` -- the imagined graph state itself
PLUS what changed (`graph_diff` against the pre-hypothesis snapshot) PLUS a
durable `Imagination` + `ImaginedConclusion` trace minted on the LIVE graph
(so an agent-authored rule can read "an imagination happened, here is what it
concluded" without touching the detached copy). The LIVE graph's own nodes
and edges are NEVER mutated by `imagine()` beyond that trace -- see
`tests/test_imagination.py::test_reversibility_*` for the exact invariant
(node/edge counts unchanged, no `Commitment` minted).

`reground()` is the return path: for each `ImaginedConclusion`, check it
against the LIVE grounded graph by shared node identity -- a conclusion
about a node that is currently GROUNDED (`grounding_reach` reaches an
anchor) and holds a DIFFERENT value live is a caught fantasy (discarded);
everything else survives. `reground` never writes the survivors' content
back into the live graph -- only `commit_imagination` does that, and it
routes through `domains/commitment_gate.py:commit_gate` (an
`imagination_writeback` action kind the reversibility frame has no entry
for, so it fails CLOSED -- committing, gated, gets a `Commitment` record --
by the frame's own `default_category`, with zero edits to that read-only
frame file).
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import substrate_rs as srs

from domains.commitment_gate import commit_gate
from domains.grounding_reach import grounding_reach

_GROUNDED_IN = "grounded_in"     # must match domains/grounding_reach.py's _EDGE
_IMAGINATION_TYPE = "Imagination"
_CONCLUSION_TYPE = "ImaginedConclusion"
_WRITEBACK_KIND = "imagination_writeback"


# ---------------------------------------------------------------------------
# duck-typed (substrate, native) resolution -- same shape
# domains/grounding_reach.py._resolve uses, duplicated locally (not imported)
# so this module carries no coupling to a file under concurrent edit.
# ---------------------------------------------------------------------------
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _v(nid: Any) -> Any:
    return nid.value if hasattr(nid, "value") else nid


def _add_edge_unchecked(native, src, edge_type, tgt, attrs=None) -> None:
    try:
        native.add_edge_unchecked(src, edge_type, tgt, attrs or {})
    except TypeError:
        native.add_edge_unchecked(src, edge_type, tgt)


# ---------------------------------------------------------------------------
# the return value of imagine()
# ---------------------------------------------------------------------------
@dataclass
class DetachedCollapse:
    """Everything one `imagine()` call produced. `detached` is the live,
    still-queryable detached `substrate_rs.Substrate` -- a caller (or the
    follow-on agent-authored rule) may keep reading it after the call
    returns; nothing about it touches the real graph."""
    detached: Any                       # substrate_rs.Substrate wrapper (detached copy)
    imagination_node: Any               # NodeID of the durable Imagination record (LIVE graph)
    conclusion_nodes: list              # [NodeID, ...] of ImaginedConclusion records (LIVE graph)
    focus_nodes: Optional[list]
    hypothesis: Optional[dict]
    hyp_map: dict                       # hypothesis local key -> detached NodeID
    cut_grounding: bool
    grounding_cut_count: int
    steps_run: int
    steps_budget: int
    converged: bool                     # fixed point reached before steps_budget was exhausted
    conclusions: dict                   # graph_diff(pre-hypothesis snapshot, post-run) -- everything new
    derived_only: dict                  # graph_diff(post-injection, post-run) -- collapse-derived only
    n_conclusions: int
    residual: float
    confidence: float


# ---------------------------------------------------------------------------
# (1) SNAPSHOT
# ---------------------------------------------------------------------------
def _focus_closure(native, focus_nodes: list, hops: int) -> set:
    """BFS closure (both directions, any edge type) from `focus_nodes` out to
    `hops` hops. Mechanical graph read only."""
    seen = {_v(n) for n in focus_nodes}
    frontier = list(seen)
    for _ in range(max(0, hops)):
        nxt = []
        for val in frontier:
            nid = srs.NodeID(val)
            if not native.has_node(nid):
                continue
            for nb in native.neighbours(nid, None):
                if nb.value not in seen:
                    seen.add(nb.value)
                    nxt.append(nb.value)
            for nb in native.in_neighbours(nid, None):
                if nb.value not in seen:
                    seen.add(nb.value)
                    nxt.append(nb.value)
        frontier = nxt
        if not frontier:
            break
    return seen


def _snapshot_dict(native, focus_nodes: Optional[list], focus_hops: int) -> dict:
    """graph_to_dict of the whole graph (focus_nodes is None), or -- for a
    focused snapshot -- ALL live nodes (full identity space) but only the
    EDGES within the focus BFS closure.

    Keeping every node's identity (not just the ones in the closure) is
    NOT a memory optimisation choice; it is a correctness requirement.
    `graph_from_dict` -> `restore_node` ignores any "next_id" this function
    supplies and re-derives the detached copy's own id allocator from the
    max node id actually PRESENT in `nodes` (see runners/dsl/src/persist.rs
    `graph_from_value`). If focus were used to drop nodes too, a hypothesis
    node minted afterwards could be allocated an id that an EXCLUDED live
    node already owns -- silently aliasing two different entities the next
    time `reground` maps a `detached_id` back onto the live graph by
    identity. Restricting only the EDGE set still bounds what the detached
    collapse can structurally REACH (a Rule only matches through an edge),
    which is the actual point of `focus_nodes` -- limiting blast radius,
    not id-space."""
    full = native.graph_to_dict()
    if not focus_nodes:
        return full
    keep = _focus_closure(native, focus_nodes, focus_hops)
    edges = [e for e in full["edges"] if e["src"] in keep and e["tgt"] in keep]
    return {"next_id": full["next_id"], "nodes": full["nodes"], "edges": edges}


# ---------------------------------------------------------------------------
# (2) CUT GROUNDING
# ---------------------------------------------------------------------------
def _cut_grounding_edges(dnative) -> int:
    """Remove every `grounded_in` edge from the DETACHED copy. Anchor nodes
    and the facts they were grounding are untouched -- only the provenance
    pin is cut. Returns the number of edges actually removed."""
    d = dnative.graph_to_dict()
    cut = 0
    for e in d["edges"]:
        if e["type"] != _GROUNDED_IN:
            continue
        try:
            if dnative.remove_edge(srs.NodeID(e["src"]), _GROUNDED_IN, srs.NodeID(e["tgt"])):
                cut += 1
        except Exception:
            pass
    return cut


# ---------------------------------------------------------------------------
# (3) INJECT HYPOTHESIS
# ---------------------------------------------------------------------------
def _inject_hypothesis(dnative, hypothesis: Optional[dict]) -> dict:
    """Mechanically translate a declarative hypothesis spec into mutations
    on the detached copy. No decision -- pure ingest, the same shape a world
    adapter's `add_inbound` uses for external text/audio.

    `hypothesis` shape (all keys optional, default {}):
        {"nodes": [{"key": str, "type": str, "attrs": dict}, ...],
         "edges": [{"src": key_or_nodeid_or_int, "type": str,
                     "tgt": key_or_nodeid_or_int, "attrs": dict}, ...]}

    `src`/`tgt` may reference a `key` minted by this same call, or an
    existing node id (int or NodeID) already present in the detached copy
    (shared id space with the snapshot) -- has_node-guarded, a dangling
    reference is silently skipped (never raises: injecting a hypothesis is
    adapter-mechanical, not a place to crash the caller over a typo in a
    hand-authored spec).

    Returns {key: NodeID} for the newly minted hypothesis nodes.
    """
    if not hypothesis:
        return {}
    key_map: dict = {}
    for spec in hypothesis.get("nodes", []):
        nid = dnative.add_node(spec["type"], dict(spec.get("attrs", {})))
        key_map[spec["key"]] = nid

    def _endpoint(tok):
        if isinstance(tok, str) and tok in key_map:
            return key_map[tok]
        if hasattr(tok, "value"):
            return tok
        return srs.NodeID(int(tok))

    for espec in hypothesis.get("edges", []):
        try:
            src = _endpoint(espec["src"])
            tgt = _endpoint(espec["tgt"])
        except (KeyError, TypeError, ValueError):
            continue
        if not (dnative.has_node(src) and dnative.has_node(tgt)):
            continue
        _add_edge_unchecked(dnative, src, espec["type"], tgt, espec.get("attrs"))
    return key_map


def _install_detached_rewrite_delta(live_native, detached_native,
                                    rewrite_delta: Optional[dict]) -> dict:
    """Clone the live rewrite store into a detached mind and apply a proposed
    rule/attribute delta there only.

    Graph-resident Rule nodes already survive ``graph_to_dict``.  The native
    rewrite store does not, so a self-modification rehearsal must copy it or
    it would be testing an amputated cognition engine.  The supplied delta is
    graph-authored data; this function only performs its named operations.
    """
    delta = rewrite_delta or {}
    removed_names = {str(n) for n in (delta.get("remove_rules") or [])}
    copied = 0
    removed = []
    for rule in live_native.export_rules():
        if not isinstance(rule, dict) or not rule.get("active", True):
            continue
        name = str(rule.get("name") or "")
        if name and name in removed_names:
            removed.append(name)
            continue
        detached_native.add_rule(rule)
        copied += 1

    added = []
    for rule in delta.get("add_rules") or []:
        if not isinstance(rule, dict):
            continue
        detached_native.add_rule(rule)
        added.append(str(rule.get("name") or ""))

    attrs_changed = []
    for edit in delta.get("set_node_attrs") or []:
        if not isinstance(edit, (list, tuple)) or len(edit) != 3:
            continue
        node_value, key, value = edit
        try:
            node = node_value if hasattr(node_value, "value") else srs.NodeID(int(node_value))
        except (TypeError, ValueError):
            continue
        if not detached_native.has_node(node):
            continue
        detached_native.set_attr(node, str(key), value)
        attrs_changed.append([_v(node), str(key)])

    return {
        "rules_copied": copied,
        "rules_removed": sorted(set(removed)),
        "rules_added": added,
        "attrs_changed": attrs_changed,
    }


# ---------------------------------------------------------------------------
# durable trace on the LIVE graph
# ---------------------------------------------------------------------------
def _mint_conclusion_records(sub, native, imagination_node, conclusions: dict) -> list:
    minted = []
    for n in conclusions.get("nodes_added", []):
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": "node_added", "detached_id": n["id"],
            "node_type": n.get("type"), "attrs": dict(n.get("attrs", {})),
            "status": "pending", "reason": "",
        })
        _add_edge_unchecked(native, imagination_node, "imagined", cid)
        minted.append(cid)
    for n in conclusions.get("nodes_changed", []):
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": "node_changed", "detached_id": n["id"],
            "attrs_before": dict(n.get("attrs_before", {})),
            "attrs_after": dict(n.get("attrs_after", {})),
            "status": "pending", "reason": "",
        })
        _add_edge_unchecked(native, imagination_node, "imagined", cid)
        minted.append(cid)
    for e in conclusions.get("edges_added", []):
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": "edge_added", "src": e["src"], "edge_type": e["type"], "tgt": e["tgt"],
            "status": "pending", "reason": "",
        })
        _add_edge_unchecked(native, imagination_node, "imagined", cid)
        minted.append(cid)
    return minted


# ---------------------------------------------------------------------------
# THE ENTRY POINT
# ---------------------------------------------------------------------------
def imagine(agent, *, focus_nodes: Optional[list] = None, hypothesis: Optional[dict] = None,
            steps: int = 100_000, cut_grounding: bool = True, focus_hops: int = 2,
            rewrite_delta: Optional[dict] = None) -> DetachedCollapse:
    """Run the substrate's OWN collapse (`tick()` -- graph-resident Rules +
    any rewrite rules already installed on the fresh detached object) on a
    DETACHED, id-preserving copy of (a neighbourhood of) the graph, with
    `hypothesis` injected and (by default) every `grounded_in` provenance
    edge cut so the collapse is not pinned by external reference. The LIVE
    graph is never mutated by this call except to mint the durable
    `Imagination` / `ImaginedConclusion` trace (see module docstring) --
    reversible, no `Commitment` record (see `tests/test_imagination.py`).

    `cut_grounding=False` runs the identical snapshot/inject/run pipeline
    WITHOUT cutting -- the "what would the GROUNDED collapse have done"
    contrast case a caller (or a discriminative test) uses to show
    frame-independence actually changed the outcome, not just relabelled it.
    """
    sub, native = _resolve(agent)
    focus_nodes = list(focus_nodes) if focus_nodes else None

    # (1) SNAPSHOT
    snap = _snapshot_dict(native, focus_nodes, focus_hops)
    detached = srs.Substrate()
    detached._inner.graph_from_dict(snap)
    dnative = detached._inner

    # A normal imagination needs no separate rewrite-store copy.  A
    # self-modification rehearsal does: its hypothesis is specifically about
    # what a changed cognition engine would derive.
    delta_report = (_install_detached_rewrite_delta(native, dnative, rewrite_delta)
                    if rewrite_delta is not None else None)

    # (2) CUT GROUNDING (detached copy only)
    cut_count = _cut_grounding_edges(dnative) if cut_grounding else 0

    # baseline for "conclusions" = everything new relative to the
    # grounding-cut, pre-hypothesis state (hypothesis injection + whatever
    # the collapse then derives from it).
    pre_dict = dnative.graph_to_dict()

    # (3) INJECT HYPOTHESIS
    hyp_map = _inject_hypothesis(dnative, hypothesis)
    injected_dict = dnative.graph_to_dict()

    # (4) RUN THE COLLAPSE
    steps_run = detached.tick(steps)
    post_dict = dnative.graph_to_dict()

    conclusions = srs._native.Substrate.graph_diff(pre_dict, post_dict)
    derived_only = srs._native.Substrate.graph_diff(injected_dict, post_dict)
    n_conclusions = (len(conclusions["nodes_added"]) + len(conclusions["nodes_changed"])
                     + len(conclusions["edges_added"]))
    converged = steps_run < steps
    residual = 0.0 if converged else 1.0
    confidence = 1.0 - residual

    imagination_node = sub.add_node(_IMAGINATION_TYPE, {
        "focus": [_v(n) for n in focus_nodes] if focus_nodes else [],
        "hypothesis_keys": sorted(hyp_map.keys(), key=str),
        "grounding_cut": bool(cut_grounding),
        "grounding_cut_count": cut_count,
        "steps_run": steps_run,
        "steps_budget": steps,
        "converged": converged,
        "n_conclusions": n_conclusions,
        "status": "explored",
        "ts": time.time(),
    })
    if delta_report is not None:
        native.set_attr(imagination_node, "rewrite_delta_report", delta_report)
        native.set_attr(imagination_node, "epistemic_scope", "graph_counterfactual")
    conclusion_nodes = _mint_conclusion_records(sub, native, imagination_node, conclusions)

    return DetachedCollapse(
        detached=detached, imagination_node=imagination_node,
        conclusion_nodes=conclusion_nodes, focus_nodes=focus_nodes,
        hypothesis=hypothesis, hyp_map=hyp_map, cut_grounding=bool(cut_grounding),
        grounding_cut_count=cut_count, steps_run=steps_run, steps_budget=steps,
        converged=converged, conclusions=conclusions, derived_only=derived_only,
        n_conclusions=n_conclusions, residual=residual, confidence=confidence,
    )


# ---------------------------------------------------------------------------
# THE RETURN PATH
# ---------------------------------------------------------------------------
def _judge_conclusion(agent, sub, at: dict) -> tuple[bool, str]:
    """A conclusion SURVIVES unless it is a `node_changed` whose imagined
    `attrs_after` disagrees, key-for-key, with the CURRENT live value of the
    SAME node id (shared identity, since the detached copy was snapshotted
    id-preserving) AND that live node is currently GROUNDED
    (`grounding_reach` reaches an anchor). Only a grounded live fact can
    veto a fantasy; a live value that merely differs but is itself
    ungrounded is unconfirmed, not a contradiction, so it does not discard
    the conclusion. `node_added` / `edge_added` conclusions describe
    structure that doesn't exist live at all -- nothing to contradict by
    identity, so they always survive (a caller wanting a stronger novel-
    structure check composes one on top; this stays purely mechanical)."""
    kind = at.get("kind")
    if kind != "node_changed":
        return True, "novel structure -- nothing live to contradict by identity"
    nid_val = at.get("detached_id")
    if nid_val is None:
        return True, "no identity recorded -- nothing to contradict"
    nid = srs.NodeID(nid_val)
    if not sub.has_node(nid):
        return True, "live counterpart absent (has_node-guard, ids recycle) -- nothing to contradict"
    gr = grounding_reach(agent, nid)
    if not gr["reached"]:
        return True, "live counterpart not grounded -- unconfirmed, not vetoed"
    live_attrs = sub.node(nid)["attrs"]
    after = at.get("attrs_after") or {}
    for k, v in after.items():
        if k in live_attrs and live_attrs[k] != v:
            return False, f"contradicts grounded live fact {k!r}: live={live_attrs[k]!r} imagined={v!r}"
    return True, "consistent with grounded live state"


def reground(agent, detached: DetachedCollapse) -> dict:
    """Reconnect an imagined collapse to reality. For each
    `ImaginedConclusion` under `detached.imagination_node`, judge it against
    the LIVE grounded graph (`_judge_conclusion`) and record the verdict on
    the SAME `ImaginedConclusion` node (`status`/`reason` -- durable trace
    bookkeeping, not a writeback of the conclusion's CONTENT). Never mutates
    any node/edge other than these trace records and the `Imagination`
    summary -- writing the survivors' content into the live graph as new
    facts is `commit_imagination`'s job, gated separately.

    Returns {"survivors": [NodeID, ...], "discarded": [NodeID, ...],
             "residual": float, "detail": [...]}.
    `residual` = discarded / (survivors + discarded) -- 0.0 if every
    conclusion held up, 1.0 if every one was a caught fantasy."""
    sub, native = _resolve(agent)
    survivors, discarded, detail = [], [], []
    for cid in detached.conclusion_nodes:
        if not sub.has_node(cid):
            continue
        at = sub.node(cid)["attrs"]
        ok, why = _judge_conclusion(agent, sub, at)
        native.set_attr(cid, "status", "survived" if ok else "discarded")
        native.set_attr(cid, "reason", why[:500])
        (survivors if ok else discarded).append(cid)
        detail.append({"conclusion": cid, "kind": at.get("kind"), "survived": ok, "reason": why})
    total = len(survivors) + len(discarded)
    residual = (len(discarded) / total) if total else 0.0
    if sub.has_node(detached.imagination_node):
        native.set_attr(detached.imagination_node, "status", "regrounded")
        native.set_attr(detached.imagination_node, "n_survived", len(survivors))
        native.set_attr(detached.imagination_node, "n_discarded", len(discarded))
    return {"survivors": survivors, "discarded": discarded, "residual": residual, "detail": detail}


# ---------------------------------------------------------------------------
# THE COMMIT STEP -- the only path that writes an imagined conclusion's
# CONTENT into the live graph. Routed through commit_gate: "imagination_
# writeback" has no entry in seeds/reversibility_frame.json, so it fails
# CLOSED (committing) by that frame's own default_category -- no edit to
# the frame was needed to get this right.
# ---------------------------------------------------------------------------
def commit_imagination(agent, detached: DetachedCollapse, survivors: list, *,
                        approver: Optional[str] = None, policy: Optional[dict] = None) -> dict:
    """Write the given SURVIVOR `ImaginedConclusion` nodes' content into the
    live graph -- the COMMITTING half of the reversible-explore/committing
    split (`domains/commitment_gate.py`). `survivors` is normally
    `reground(...)["survivors"]`, but this function performs NO regrounding
    of its own -- it trusts the list it is given (an agent-authored rule
    would only ever pass the already-regrounded survivor set).

    Returns {"gate": <commit_gate result>, "written": [...]}. `written` is
    empty and no live mutation happens if the gate refuses (e.g. no
    approver and the default policy requires one) -- a `Commitment` record
    is still minted either way (see `commit_gate`)."""
    sub, native = _resolve(agent)
    gate = commit_gate(agent, {"kind": _WRITEBACK_KIND,
                                "imagination": _v(detached.imagination_node),
                                "n_survivors": len(survivors)},
                        approver=approver, policy=policy)
    written: list = []
    if not gate["allowed"]:
        return {"gate": gate, "written": written}

    remap: dict = {}   # detached-id (int) -> live NodeID, for edge_added endpoint resolution
    for cid in survivors:
        if not sub.has_node(cid):
            continue
        at = sub.node(cid)["attrs"]
        kind = at.get("kind")
        if kind == "node_changed":
            nid_val = at.get("detached_id")
            if nid_val is None:
                continue
            nid = srs.NodeID(nid_val)
            if not sub.has_node(nid):
                continue
            for k, v in (at.get("attrs_after") or {}).items():
                native.set_attr(nid, k, v)
            remap[nid_val] = nid
            written.append({"kind": kind, "node": nid})
        elif kind == "node_added":
            new_id = sub.add_node(at.get("node_type", "ImaginedFact"), dict(at.get("attrs", {})))
            remap[at.get("detached_id")] = new_id
            written.append({"kind": kind, "node": new_id})
        elif kind == "edge_added":
            src_v, tgt_v, et = at.get("src"), at.get("tgt"), at.get("edge_type")
            src = remap.get(src_v) or (srs.NodeID(src_v) if sub.has_node(srs.NodeID(src_v)) else None)
            tgt = remap.get(tgt_v) or (srs.NodeID(tgt_v) if sub.has_node(srs.NodeID(tgt_v)) else None)
            if src is None or tgt is None or et is None:
                continue
            _add_edge_unchecked(native, src, et, tgt)
            written.append({"kind": kind, "edge": (src, et, tgt)})
        else:
            continue
        native.set_attr(cid, "status", "committed")

    if sub.has_node(detached.imagination_node):
        native.set_attr(detached.imagination_node, "status", "committed")
        if gate.get("record") is not None:
            _add_edge_unchecked(native, detached.imagination_node, "committed_as", gate["record"])
    return {"gate": gate, "written": written}


__all__ = [
    "DetachedCollapse",
    "imagine",
    "reground",
    "commit_imagination",
]
