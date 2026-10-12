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
                   `substrate_rs.Substrate` via `graph_from_dict`, then copy
                   the active native `add_rule` rewrite-rule store. Node ids
                   are shared vocabulary between the live graph and the
                   detached copy, so a conclusion's `detached_id` names the
                   SAME conceptual entity in both -- that is what lets
                   `reground` map an imagined conclusion back onto a live
                   node by identity. `graph_to_dict` / `graph_from_dict`
                   serialise only graph nodes/edges; the native rule store is
                   copied separately and any candidate delta is applied only
                   to that detached copy.
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
  4. RUN THE COLLAPSE -- explicit graph-then-struct execution on the
                   detached copy: graph-resident `Rule` nodes run first,
                   followed by the copied native rewrite-rule store. This
                   avoids the ordinary `tick()` Default plan, which can run
                   structural rules only and silently skip graph-resident
                   cognition. The counterfactual consequences stay detached.

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
import copy
from dataclasses import dataclass, field
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
    phase_timings_ms: dict = field(default_factory=dict)


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


def _retain_focus_edges(dnative, focus_nodes: Optional[list], focus_hops: int) -> None:
    """Apply the serializer snapshot's edge aperture to a native deep copy."""
    if not focus_nodes:
        return
    keep = _focus_closure(dnative, focus_nodes, focus_hops)
    for edge in dnative.graph_to_dict()["edges"]:
        if edge["src"] not in keep or edge["tgt"] not in keep:
            dnative.remove_edge(srs.NodeID(edge["src"]), edge["type"],
                                srs.NodeID(edge["tgt"]))


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
                                    rewrite_delta: Optional[dict], *,
                                    copy_live_rules: bool = True) -> dict:
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
    if copy_live_rules:
        for rule in live_native.export_rules():
            if not isinstance(rule, dict) or not rule.get("active", True):
                continue
            name = str(rule.get("name") or "")
            if name and name in removed_names:
                removed.append(name)
                continue
            detached_native.add_rule(rule)
            copied += 1
    else:
        summarize = getattr(detached_native, "experiment_rule_store_summary", None)
        if summarize is not None:
            copied, removed = summarize(sorted(removed_names))
        else:
            # Compatibility fallback for a native extension built before the
            # branch-local summary method was introduced.
            branch_rules = detached_native.export_rules()
            copied = sum(bool(rule.get("active", True)) for rule in branch_rules
                         if isinstance(rule, dict))
            removals = [
                idx for idx, rule in enumerate(branch_rules)
                if isinstance(rule, dict) and rule.get("active", True)
                and str(rule.get("name") or "") in removed_names
            ]
            for idx in reversed(removals):
                detached_native.remove_rule(idx)
                removed.append(str(branch_rules[idx].get("name") or ""))

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
def _mint_conclusion_records(sub, native, imagination_node, conclusions: dict, *,
                             assumption_ids: set[int] | None = None,
                             assumption_edges: set[tuple[int, str, int]] | None = None) -> list:
    assumption_ids = assumption_ids or set()
    assumption_edges = assumption_edges or set()
    minted = []
    for n in conclusions.get("nodes_added", []):
        kind = "assumption_added" if int(n["id"]) in assumption_ids else "node_added"
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": kind, "detached_id": n["id"],
            "node_type": n.get("type"), "attrs": dict(n.get("attrs", {})),
            "status": "pending", "reason": "",
        })
        _add_edge_unchecked(native, imagination_node, "imagined", cid)
        minted.append(cid)
    for n in conclusions.get("nodes_changed", []):
        kind = "assumption_changed" if int(n["id"]) in assumption_ids else "node_changed"
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": kind, "detached_id": n["id"],
            "attrs_before": dict(n.get("attrs_before", {})),
            "attrs_after": dict(n.get("attrs_after", {})),
            "status": "pending", "reason": "",
        })
        _add_edge_unchecked(native, imagination_node, "imagined", cid)
        minted.append(cid)
    for e in conclusions.get("edges_added", []):
        key = (int(e["src"]), str(e["type"]), int(e["tgt"]))
        if key in assumption_edges:
            kind = "assumption_edge_added"
        elif key[0] in assumption_ids or key[2] in assumption_ids:
            kind = "conditional_edge_added"
        else:
            kind = "edge_added"
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": kind, "src": e["src"], "edge_type": e["type"], "tgt": e["tgt"],
            "attrs": dict(e.get("attrs", {})),
            "status": "pending", "reason": "",
        })
        _add_edge_unchecked(native, imagination_node, "imagined", cid)
        minted.append(cid)
    for e in conclusions.get("edges_changed", []):
        kind = ("conditional_edge_changed" if int(e["src"]) in assumption_ids
                or int(e["tgt"]) in assumption_ids else "edge_changed")
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": kind, "src": e["src"], "edge_type": e["type"], "tgt": e["tgt"],
            "attrs_before": dict(e.get("attrs_before", {})),
            "attrs_after": dict(e.get("attrs_after", {})),
            "status": "pending", "reason": "",
        })
        _add_edge_unchecked(native, imagination_node, "imagined", cid)
        minted.append(cid)
    removed_nodes = {int(n["id"]) for n in conclusions.get("nodes_removed_details", [])}
    for n in conclusions.get("nodes_removed_details", []):
        incident_edges = [
            {"src": int(e["src"]), "type": str(e["type"]), "tgt": int(e["tgt"]),
             "attrs": dict(e.get("attrs", {}))}
            for e in conclusions.get("edges_removed_details", [])
            if int(e["src"]) == int(n["id"]) or int(e["tgt"]) == int(n["id"])
        ]
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": "node_removed", "detached_id": n["id"],
            "node_type_before": n.get("type"),
            "attrs_before": dict(n.get("attrs", {})),
            "incident_edges_before": incident_edges,
            "status": "pending", "reason": "",
        })
        _add_edge_unchecked(native, imagination_node, "imagined", cid)
        minted.append(cid)
    for e in conclusions.get("edges_removed_details", []):
        src, tgt = int(e["src"]), int(e["tgt"])
        # Removing a node already removes every incident edge. Keep one
        # explicit proposal for that operation instead of duplicating it.
        if src in removed_nodes or tgt in removed_nodes:
            continue
        cid = sub.add_node(_CONCLUSION_TYPE, {
            "kind": "edge_removed", "src": src, "edge_type": e["type"], "tgt": tgt,
            "attrs_before": dict(e.get("attrs", {})),
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
            rewrite_delta: Optional[dict] = None,
            snapshot_backend: str = "serialization",
            _force_full_noop_readout: bool = False,
            _force_full_graph_readout: bool = False,
            _process_forked: bool = False,
            _snapshot_handle=None,
            _measure_phases: bool = False,
            record_trace: bool = True) -> DetachedCollapse:
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
    phase_clock = time.perf_counter_ns if _measure_phases else None
    phase_started = phase_clock() if phase_clock else 0

    # (1) SNAPSHOT
    if snapshot_backend == "serialization":
        snap = _snapshot_dict(native, focus_nodes, focus_hops)
        detached = srs.Substrate()
        detached._inner.graph_from_dict(snap)
    elif snapshot_backend == "native_full_copy":
        fork = getattr(sub, "fork_full_copy_experiment", None)
        if fork is None:
            raise RuntimeError("native full-copy experiment fork is unavailable")
        detached = fork()
        _retain_focus_edges(detached._inner, focus_nodes, focus_hops)
    elif snapshot_backend == "native_full_copy_scoped":
        fork = getattr(sub, "fork_full_copy_experiment", None)
        if fork is None:
            raise RuntimeError("native full-copy experiment fork is unavailable")
        detached = fork()
        if focus_nodes:
            detached.set_experiment_edge_scope([_v(n) for n in focus_nodes], focus_hops)
    elif snapshot_backend == "native_shared_slab":
        fork = getattr(sub, "fork_shared_slab_experiment", None)
        if fork is None:
            raise RuntimeError("native shared-slab experiment fork is unavailable")
        detached = fork()
        _retain_focus_edges(detached._inner, focus_nodes, focus_hops)
    elif snapshot_backend == "native_shared_slab_scoped":
        fork = getattr(sub, "fork_shared_slab_experiment", None)
        if fork is None:
            raise RuntimeError("native shared-slab experiment fork is unavailable")
        detached = fork()
        if focus_nodes:
            detached.set_experiment_edge_scope([_v(n) for n in focus_nodes], focus_hops)
    elif snapshot_backend == "native_shared_graph_pages":
        fork = getattr(sub, "fork_shared_graph_pages_experiment", None)
        if fork is None:
            raise RuntimeError("native shared-graph-pages experiment fork is unavailable")
        detached = fork()
        _retain_focus_edges(detached._inner, focus_nodes, focus_hops)
    elif snapshot_backend == "native_shared_graph_pages_scoped":
        fork = getattr(sub, "fork_shared_graph_pages_experiment", None)
        if fork is None:
            raise RuntimeError("native shared-graph-pages experiment fork is unavailable")
        detached = fork()
        if focus_nodes:
            detached.set_experiment_edge_scope([_v(n) for n in focus_nodes], focus_hops)
    elif snapshot_backend == "native_reusable_snapshot":
        # A batch may provide one immutable source snapshot to many candidate
        # consumers. A standalone call captures its own snapshot. The public
        # backend-neutral snapshot contract keeps this consumer independent of
        # the underlying graph-page representation.
        snapshot = _snapshot_handle or sub.snapshot()
        expected_revision = tuple(native.experiment_graph_rule_revision())
        if tuple(snapshot.source_revision) != expected_revision:
            raise RuntimeError(
                "reusable experiment snapshot revision does not match source substrate")
        detached = snapshot.fork()
        if focus_nodes:
            detached.set_experiment_edge_scope([_v(n) for n in focus_nodes], focus_hops)
    elif snapshot_backend == "process_in_place":
        if not _process_forked:
            raise RuntimeError("process_in_place requires an isolated forked child")
        # The OS has already made this process a CoW child. Reuse its inherited
        # native state as the branch rather than taking another eager copy.
        detached = sub
        _retain_focus_edges(native, focus_nodes, focus_hops)
    elif snapshot_backend == "process_in_place_scoped":
        if not _process_forked:
            raise RuntimeError("process_in_place_scoped requires an isolated forked child")
        detached = sub
        if focus_nodes:
            detached.set_experiment_edge_scope([_v(n) for n in focus_nodes], focus_hops)
    else:
        raise ValueError(f"unknown imagination snapshot backend: {snapshot_backend}")
    dnative = detached._inner

    # A normal imagination needs no separate rewrite-store copy.  A
    # self-modification rehearsal does: its hypothesis is specifically about
    # what a changed cognition engine would derive.
    # graph_to_dict excludes native rewrite rules, so copy that semantic
    # state on every detached branch, applying any candidate delta there.
    # Without this, a detached prediction runs an amputated engine.
    delta_report = _install_detached_rewrite_delta(
        native, dnative, rewrite_delta or {},
        copy_live_rules=(snapshot_backend == "serialization"),
    )
    snapshot_setup_ms = ((phase_clock() - phase_started) / 1_000_000
                         if phase_clock else None)

    # Candidate rehearsal asks for a zero-step, no-hypothesis detached base
    # before applying its candidate rules. In this exact case there can be no
    # graph delta: avoid serializing the complete branch twice and diffing two
    # identical graphs. Keep this guard narrow so grounding cuts, injected
    # hypotheses, and any executed collapse retain the ordinary readout path.
    no_op_probe = (steps == 0 and hypothesis is None and not cut_grounding
                   and not _force_full_noop_readout)

    # (2) CUT GROUNDING (detached copy only)
    cut_count = _cut_grounding_edges(dnative) if cut_grounding else 0

    # baseline for "conclusions" = everything new relative to the
    # grounding-cut, pre-hypothesis state (hypothesis injection + whatever
    # the collapse then derives from it).
    use_delta_journal = not _force_full_graph_readout and not no_op_probe
    if use_delta_journal:
        detached.begin_experiment_delta_journal()
        pre_dict = injected_dict = None
    else:
        pre_dict = None if no_op_probe else dnative.graph_to_dict()

    # (3) INJECT HYPOTHESIS
    hyp_map = {} if no_op_probe else _inject_hypothesis(dnative, hypothesis)
    if use_delta_journal:
        detached.checkpoint_experiment_delta_journal()
    else:
        injected_dict = pre_dict if no_op_probe else dnative.graph_to_dict()
    preparation_ms = ((phase_clock() - phase_started - int(snapshot_setup_ms * 1_000_000)) / 1_000_000
                      if phase_clock else None)

    # (4) RUN THE COLLAPSE. The ordinary native `tick()` uses the substrate's
    # Default cycle plan, which can be structural-rules-only. An imagination
    # must explicitly execute graph-resident Rules followed by the native
    # rewrite-rule store; otherwise graph-authored cognition in the detached
    # graph is silently skipped and a counterfactual may look like a no-op.
    tick_graph_then_struct = getattr(dnative, "tick_graph_then_struct", None)
    if tick_graph_then_struct is None:
        raise RuntimeError(
            "detached imagination requires native tick_graph_then_struct support; "
            "refusing a structural-only counterfactual"
        )
    tick_started = phase_clock() if phase_clock else 0
    steps_run = 0 if no_op_probe else tick_graph_then_struct(steps)
    collapse_tick_ms = ((phase_clock() - tick_started) / 1_000_000
                        if phase_clock else None)
    readout_started = phase_clock() if phase_clock else 0
    if no_op_probe:
        empty_diff = {"nodes_added": [], "nodes_changed": [], "nodes_removed": [],
                      "edges_added": [], "edges_removed": []}
        conclusions = empty_diff
        derived_only = empty_diff.copy()
    elif use_delta_journal:
        delta = detached.finish_experiment_delta_journal()
        conclusions = delta["conclusions"]
        derived_only = delta["derived_only"]
    else:
        post_dict = dnative.graph_to_dict()
        conclusions = srs._native.Substrate.graph_diff(pre_dict, post_dict)
        derived_only = srs._native.Substrate.graph_diff(injected_dict, post_dict)
    n_conclusions = (len(conclusions["nodes_added"]) + len(conclusions["nodes_changed"])
                     + len(conclusions["edges_added"]) + len(conclusions.get("edges_changed", [])))
    result_readout_ms = ((phase_clock() - readout_started) / 1_000_000
                         if phase_clock else None)
    converged = steps_run < steps
    residual = 0.0 if converged else 1.0
    confidence = 1.0 - residual

    imagination_node = None
    conclusion_nodes = []
    trace_started = phase_clock() if phase_clock else 0
    if record_trace:
        imagination_node = sub.add_node(_IMAGINATION_TYPE, {
            "focus": [_v(n) for n in focus_nodes] if focus_nodes else [],
            "hypothesis_keys": sorted(hyp_map.keys(), key=str),
            "hypothesis": copy.deepcopy(hypothesis),
            "grounding_cut": bool(cut_grounding),
            "grounding_cut_count": cut_count,
            "steps_run": steps_run,
            "steps_budget": steps,
            "converged": converged,
            "n_conclusions": n_conclusions,
            "status": "explored",
            "ts": time.time(),
        })
        native.set_attr(imagination_node, "rewrite_delta_report", delta_report)
        native.set_attr(imagination_node, "epistemic_scope", "graph_counterfactual")
        assumption_ids = {_v(nid) for nid in hyp_map.values()}
        assumption_edges = set()
        if hypothesis:
            def endpoint_id(token):
                if isinstance(token, str) and token in hyp_map:
                    return _v(hyp_map[token])
                if hasattr(token, "value"):
                    return int(token.value)
                try:
                    return int(token)
                except (TypeError, ValueError):
                    return None
            for edge in hypothesis.get("edges", []):
                src_id, tgt_id = endpoint_id(edge.get("src")), endpoint_id(edge.get("tgt"))
                if src_id is not None and tgt_id is not None:
                    assumption_edges.add((src_id, str(edge.get("type", "")), tgt_id))
        conclusion_nodes = _mint_conclusion_records(
            sub, native, imagination_node, conclusions,
            assumption_ids=assumption_ids, assumption_edges=assumption_edges)
    trace_mint_ms = ((phase_clock() - trace_started) / 1_000_000
                     if phase_clock else None)

    return DetachedCollapse(
        detached=detached, imagination_node=imagination_node,
        conclusion_nodes=conclusion_nodes, focus_nodes=focus_nodes,
        hypothesis=hypothesis, hyp_map=hyp_map, cut_grounding=bool(cut_grounding),
        grounding_cut_count=cut_count, steps_run=steps_run, steps_budget=steps,
        converged=converged, conclusions=conclusions, derived_only=derived_only,
        n_conclusions=n_conclusions, residual=residual, confidence=confidence,
        phase_timings_ms={
            "branch_snapshot_and_rule_setup": snapshot_setup_ms,
            "grounding_and_hypothesis_preparation": preparation_ms,
            "collapse_tick": collapse_tick_ms,
            "residual_readout": result_readout_ms,
            "trace_minting": trace_mint_ms,
        } if _measure_phases else {},
    )


# ---------------------------------------------------------------------------
# THE RETURN PATH
# ---------------------------------------------------------------------------
def _judge_conclusion(agent, sub, at: dict) -> tuple[bool, str]:
    """Reground an imagined conclusion against current live state.

    Node changes are vetoed only by contradictory grounded values. Edge
    additions and changed-edge attributes use structural identity plus sparse
    before-images: a missing target or conflicting live write is rejected,
    while an already-realized outcome is idempotently accepted. Assumption and
    conditional records remain auditable but are filtered from writeback."""
    kind = at.get("kind")
    if kind == "edge_added":
        native = _resolve(agent)[1]
        src, tgt, edge_type = at.get("src"), at.get("tgt"), at.get("edge_type")
        if src is None or tgt is None or not edge_type:
            return False, "added edge has incomplete identity"
        live_attrs = native.edge_attrs(srs.NodeID(int(src)), str(edge_type), srs.NodeID(int(tgt)))
        if live_attrs is None:
            return True, "added edge is still absent from the live graph"
        if live_attrs == (at.get("attrs") or {}):
            return True, "added edge outcome is already present live"
        return False, "edge appeared with conflicting attributes since imagination"
    if kind == "edge_changed":
        native = _resolve(agent)[1]
        src, tgt, edge_type = at.get("src"), at.get("tgt"), at.get("edge_type")
        if src is None or tgt is None or not edge_type:
            return False, "changed edge has incomplete identity"
        live_attrs = native.edge_attrs(srs.NodeID(int(src)), str(edge_type), srs.NodeID(int(tgt)))
        if live_attrs is None:
            return False, "changed edge is absent from the live graph"
        before = at.get("attrs_before") or {}
        after = at.get("attrs_after") or {}
        missing = object()
        keys = set(before) | set(after)
        matches_before = all(live_attrs.get(k, missing) == before.get(k, missing) for k in keys)
        matches_after = all(live_attrs.get(k, missing) == after.get(k, missing) for k in keys)
        if matches_before:
            return True, "changed edge before-image still matches live graph"
        if matches_after:
            return True, "changed edge outcome is already present live"
        return False, "changed edge conflicts with live attributes since imagination"
    if kind == "edge_removed":
        native = _resolve(agent)[1]
        src, tgt, edge_type = at.get("src"), at.get("tgt"), at.get("edge_type")
        if src is None or tgt is None or not edge_type:
            return False, "removed edge has incomplete identity"
        live_attrs = native.edge_attrs(srs.NodeID(int(src)), str(edge_type), srs.NodeID(int(tgt)))
        if live_attrs is None:
            return True, "removed edge is already absent from the live graph"
        if live_attrs == (at.get("attrs_before") or {}):
            return True, "removed edge before-image still matches live graph"
        return False, "removed edge conflicts with live attributes since imagination"
    if kind == "node_removed":
        native = _resolve(agent)[1]
        nid_val = at.get("detached_id")
        if nid_val is None:
            return False, "removed node has incomplete identity"
        nid = srs.NodeID(int(nid_val))
        if not sub.has_node(nid):
            return True, "removed node is already absent from the live graph"
        live = sub.node(nid)
        if live["type"] != at.get("node_type_before"):
            return False, "removed node type conflicts with its live before-image"
        if live["attrs"] != (at.get("attrs_before") or {}):
            return False, "removed node attrs conflict with its live before-image"
        expected_edges = {
            (int(edge["src"]), str(edge["type"]), int(edge["tgt"])):
                dict(edge.get("attrs") or {})
            for edge in (at.get("incident_edges_before") or [])
        }
        current_edges = {
            (int(edge["src"]), str(edge["type"]), int(edge["tgt"])):
                dict(edge.get("attrs") or {})
            for edge in native.incident_edges(nid)
        }
        if current_edges != expected_edges:
            return False, "removed node incident edges conflict with their live before-image"
        return True, "removed node before-image still matches live graph"
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
                        approver: Optional[str] = None, policy: Optional[dict] = None,
                        projections: Optional[dict] = None,
                        manifold: Optional[dict] = None,
                        _targeted_commit_reads: bool = True) -> dict:
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
    # No survivor means no content can be written: this is a true no-op and
    # must not mint a commitment or invent a future-manifold measurement.
    if not survivors:
        return {"gate": {"allowed": True, "reason": "no_survivors_noop",
                          "record": None}, "written": []}

    noncommittable = {"assumption_added", "assumption_changed", "assumption_edge_added",
                      "conditional_edge_added", "conditional_edge_changed"}
    writeable = [cid for cid in survivors if sub.has_node(cid)
                 and sub.node(cid)["attrs"].get("kind") not in noncommittable]
    writeable.sort(key=lambda cid: {"edge_removed": 0, "node_removed": 1}.get(
        sub.node(cid)["attrs"].get("kind"), 2))
    if not writeable:
        return {"gate": {"allowed": True, "reason": "assumptions_remain_uncommitted",
                          "record": None}, "written": []}
    for cid in writeable:
        at = sub.node(cid)["attrs"]
        if at.get("kind") in {"edge_added", "edge_changed", "edge_removed", "node_removed"}:
            valid, why = _judge_conclusion(agent, sub, at)
            if not valid:
                return {"gate": {"allowed": False, "reason": "stale_conclusion_before_image",
                                  "detail": why, "record": None}, "written": []}

    action = {"kind": _WRITEBACK_KIND,
              "imagination": _v(detached.imagination_node),
              "n_survivors": len(writeable)}
    # Epistemic survival is not a measurement of viable future trajectories.
    # Nonempty writeback therefore requires an explicit manifold shape projection and
    # policy from the caller; otherwise commit_gate fails closed.
    if manifold is not None and projections is not None:
        action["risk"] = {
            "commit": {"name": _WRITEBACK_KIND,
                        "expected_goal_work": float(len(writeable)),
                        "projection": projections["commit"]},
            "wait": {"name": "wait", "delay_cost": 0.1,
                      "projection": projections["wait"]},
            "refine": {"name": "refine", "refinement_cost": 0.2,
                        "projection": projections["refine"]},
            "manifold": manifold,
        }
    gate = commit_gate(agent, action, approver=approver, policy=policy)
    written: list = []
    if not gate["allowed"]:
        return {"gate": gate, "written": written}

    # Route representable graph mutations through one native staged delta.
    # The revision is captured before reading the graph used for ID allocation;
    # any intervening writer makes the native transaction reject the plan.
    transaction_kinds = {"node_added", "node_changed", "node_removed",
                         "edge_added", "edge_changed", "edge_removed"}
    if all(sub.node(cid)["attrs"].get("kind") in transaction_kinds for cid in writeable):
        try:
            revision = native.experiment_graph_rule_revision()
            if _targeted_commit_reads:
                # These accessors touch only receipt endpoints and preserve
                # the legacy max-live-ID allocation rule without materializing
                # every graph node/edge as Python objects.
                live_nodes = None
                live_edges = None
                next_id = int(native.next_live_node_id())

                def live_node(nid):
                    nid = int(nid)
                    return native.node(srs.NodeID(nid)) if native.has_node(srs.NodeID(nid)) else None

                def live_edge(key):
                    src, edge_type, tgt = key
                    attrs = native.edge_attrs(srs.NodeID(int(src)), str(edge_type), srs.NodeID(int(tgt)))
                    return None if attrs is None else {"src": int(src), "type": str(edge_type),
                                                       "tgt": int(tgt), "attrs": dict(attrs)}
            else:
                # Differential control retained for source-locked performance
                # and semantic comparisons.
                live_graph = native.graph_to_dict()
                live_nodes = {int(row["id"]): row for row in live_graph["nodes"]}
                live_edges = {(int(row["src"]), str(row["type"]), int(row["tgt"])): row
                              for row in live_graph["edges"]}

                def live_node(nid):
                    return live_nodes.get(int(nid))

                def live_edge(key):
                    return live_edges.get(key)

                next_id = max(live_nodes, default=-1) + 1
            records = [(cid, sub.node(cid)["attrs"]) for cid in writeable]
            added_records = [(cid, at) for cid, at in records if at.get("kind") == "node_added"]
            id_map = {}
            nodes_added = []
            for _, at in added_records:
                detached_id = int(at["detached_id"])
                id_map[detached_id] = next_id
                nodes_added.append({"id": next_id, "type": at.get("node_type") or "ImaginedFact",
                                    "attrs": dict(at.get("attrs") or {})})
                next_id += 1

            nodes_changed, nodes_removed, nodes_removed_details = [], [], []
            edges_added, edges_changed, removed_edges = [], [], {}
            skipped = set()
            removed_node_ids = set()
            for cid, at in records:
                kind = at.get("kind")
                if kind == "node_changed":
                    nid = int(at["detached_id"])
                    node_before = live_node(nid)
                    if node_before is None:
                        skipped.add(cid)
                        continue
                    before, after = dict(at.get("attrs_before") or {}), dict(at.get("attrs_after") or {})
                    if all(node_before["attrs"].get(k) == v for k, v in after.items()) and all(
                            k in node_before["attrs"] for k in after):
                        if all(k not in node_before["attrs"] for k in before if k not in after):
                            skipped.add(cid)
                            continue
                    nodes_changed.append({"id": nid, "attrs_before": before, "attrs_after": after})
                elif kind == "node_removed":
                    nid = int(at["detached_id"])
                    if live_node(nid) is None:
                        skipped.add(cid)
                        continue
                    removed_node_ids.add(nid)
                    nodes_removed.append(nid)
                    nodes_removed_details.append({"id": nid, "type": at.get("node_type_before"),
                                                  "attrs": dict(at.get("attrs_before") or {})})
                    for edge in (at.get("incident_edges_before") or []):
                        key = (int(edge["src"]), str(edge["type"]), int(edge["tgt"]))
                        removed_edges[key] = {"src": key[0], "type": key[1], "tgt": key[2],
                                              "attrs": dict(edge.get("attrs") or {})}
                elif kind == "edge_removed":
                    key = (int(at["src"]), str(at["edge_type"]), int(at["tgt"]))
                    if live_edge(key) is None:
                        skipped.add(cid)
                        continue
                    removed_edges[key] = {"src": key[0], "type": key[1], "tgt": key[2],
                                          "attrs": dict(at.get("attrs_before") or {})}
                elif kind == "edge_added":
                    src0, tgt0 = int(at["src"]), int(at["tgt"])
                    src, tgt = id_map.get(src0, src0), id_map.get(tgt0, tgt0)
                    edge_type = str(at["edge_type"])
                    if src not in id_map.values() and live_node(src) is None:
                        raise RuntimeError("added edge source is absent from the live graph")
                    if tgt not in id_map.values() and live_node(tgt) is None:
                        raise RuntimeError("added edge target is absent from the live graph")
                    key = (src, edge_type, tgt)
                    existing = live_edge(key)
                    attrs = dict(at.get("attrs") or {})
                    if existing is not None:
                        if dict(existing.get("attrs") or {}) != attrs:
                            raise RuntimeError("added edge conflicts with a live edge")
                        skipped.add(cid)
                        continue
                    edges_added.append({"src": src, "type": edge_type, "tgt": tgt,
                                        "attrs": attrs})
                elif kind == "edge_changed":
                    key = (int(at["src"]), str(at["edge_type"]), int(at["tgt"]))
                    existing = live_edge(key)
                    if existing is None:
                        raise RuntimeError("changed edge is absent from the live graph")
                    before, after = dict(at.get("attrs_before") or {}), dict(at.get("attrs_after") or {})
                    attrs = dict(existing.get("attrs") or {})
                    if all(attrs.get(k) == v for k, v in after.items()) and all(
                            k in attrs for k in after) and all(k not in attrs for k in before if k not in after):
                        skipped.add(cid)
                        continue
                    edges_changed.append({"src": key[0], "type": key[1], "tgt": key[2],
                                          "attrs_before": before, "attrs_after": after})

            delta = {
                "nodes_added": nodes_added, "nodes_changed": nodes_changed,
                "nodes_removed": sorted(nodes_removed),
                "nodes_removed_details": nodes_removed_details,
                "edges_added": edges_added, "edges_changed": edges_changed,
                "edges_removed": [{"src": key[0], "type": key[1], "tgt": key[2]}
                                  for key in sorted(removed_edges)],
                "edges_removed_details": [removed_edges[key] for key in sorted(removed_edges)],
            }
            native.apply_experiment_graph_delta(revision, delta)
            written.extend({"kind": "node_added", "node": srs.NodeID(id_map[int(at["detached_id"])])}
                           for _, at in added_records)
            written.extend({"kind": at["kind"], "node": srs.NodeID(int(at["detached_id"]))}
                           for cid, at in records if at.get("kind") == "node_changed" and cid not in skipped)
            written.extend([{"kind": "edge_added", "edge": (srs.NodeID(int(row["src"])), row["type"],
                                                                    srs.NodeID(int(row["tgt"]))) }
                           for row in edges_added])
            written.extend([{"kind": "edge_changed", "edge": (srs.NodeID(int(row["src"])), row["type"],
                                                                      srs.NodeID(int(row["tgt"]))) }
                           for row in edges_changed])
            written.extend({"kind": "edge_removed", "edge": (srs.NodeID(key[0]), key[1], srs.NodeID(key[2]))}
                           for key in sorted(removed_edges))
            written.extend({"kind": "node_removed", "node": srs.NodeID(nid)}
                           for nid in sorted(removed_node_ids))
            for cid, _ in records:
                native.set_attr(cid, "status", "committed")
            if sub.has_node(detached.imagination_node):
                native.set_attr(detached.imagination_node, "status", "committed")
                if gate.get("record") is not None:
                    _add_edge_unchecked(native, detached.imagination_node, "committed_as", gate["record"])
            return {"gate": gate, "written": written,
                    "writeback": {"applied": True, "reason": "committed"}}
        except RuntimeError as exc:
            return {"gate": gate, "written": [],
                    "writeback": {"applied": False, "reason": "graph_batch_conflict",
                                  "detail": str(exc)}}

    remap: dict = {}   # detached-id (int) -> live NodeID, for edge_added endpoint resolution
    for cid in writeable:
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
            _add_edge_unchecked(native, src, et, tgt, at.get("attrs") or {})
            written.append({"kind": kind, "edge": (src, et, tgt)})
        elif kind == "edge_changed":
            src_v, tgt_v, et = at.get("src"), at.get("tgt"), at.get("edge_type")
            if src_v is None or tgt_v is None or not et:
                continue
            src, tgt = srs.NodeID(int(src_v)), srs.NodeID(int(tgt_v))
            current = native.edge_attrs(src, et, tgt)
            if current is None:
                continue
            updated = dict(current)
            before = at.get("attrs_before") or {}
            after = at.get("attrs_after") or {}
            for key in before.keys() - after.keys():
                updated.pop(key, None)
            updated.update(after)
            native.add_edge_unchecked(src, et, tgt, updated)
            written.append({"kind": kind, "edge": (src, et, tgt)})
        elif kind == "edge_removed":
            src_v, tgt_v, et = at.get("src"), at.get("tgt"), at.get("edge_type")
            if src_v is None or tgt_v is None or not et:
                continue
            src, tgt = srs.NodeID(int(src_v)), srs.NodeID(int(tgt_v))
            if sub.remove_edge(src, et, tgt):
                written.append({"kind": kind, "edge": (src, et, tgt)})
        elif kind == "node_removed":
            nid_val = at.get("detached_id")
            if nid_val is None:
                continue
            nid = srs.NodeID(int(nid_val))
            if sub.remove_node(nid):
                written.append({"kind": kind, "node": nid})
        else:
            continue
        native.set_attr(cid, "status", "committed")

    if sub.has_node(detached.imagination_node):
        native.set_attr(detached.imagination_node, "status", "committed")
        if gate.get("record") is not None:
            _add_edge_unchecked(native, detached.imagination_node, "committed_as", gate["record"])
    return {"gate": gate, "written": written,
            "writeback": {"applied": True, "reason": "committed"}}


__all__ = [
    "DetachedCollapse",
    "imagine",
    "reground",
    "commit_imagination",
]
