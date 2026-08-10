"""imagination_dispatch — the TIER-3 imagine-on-escalation MECHANISM (host I/O
only, CLAUDE.md). Twin of `domains/experiment_dispatch.py`, same discipline.

The DECISION to imagine is the agent's: its own authored ENGAGE rules
(`seeds/composer_imagination_graph.json`, minted via `ground_concern`'s
'imagination' composer — see `domains/reflective_faculty.py`'s
`_try_graph_composer`) mint an `ImagineRequest{status:"requested"}` node
whenever an escalated `Impasse` (`kind` `grounding_gap` OR
`cost_worth_refining` — the SAME two arms `composer_grounding_guard_graph`
/ `composer_escalation_gate_graph` mint `agent -surprised_by-> impasse`
into) is seen. This module does not decide WHETHER to imagine or WHAT
counterfactual to explore — both are already fixed on the request node by
the agent's own rule. It only:

  1. **sees** a requested `ImagineRequest`,
  2. **resolves** its focus mechanically: `focuses_on_gap -> GroundingGap`
     reads that gap's own `node` attr (the actually-flagged live node —
     `domains/grounding_reach.py:flag_ungrounded_confident` put it there);
     `focuses_on_axis -> CapabilityAxis` and the generic
     `focuses_on_node -> Node` need no indirection: that node itself IS the
     focus. (The agent's rule could not point directly at the
     flagged node — `add_edge` targets must be match-bound vars, and the
     flagged node is never bound by the engage rule's own match — so it
     points at the one hop it COULD bind, and this hook walks the rest.)
  3. **splices** the resolved focus id into the request's own
     `hypothesis_template` (a JSON string the agent's rule wrote,
     containing the sentinel `"__FOCUS__"` wherever it wants the focus
     wired in) — mechanical string substitution, not a decision about
     WHAT the hypothesis says.
  4. **calls** `domains.imagination.imagine()` + `reground()` — Python host
     calls that CANNOT run inside a Rust rule effect, exactly why this
     hook exists (the same reason `experiment_dispatch.py` spawns a child
     process the rule engine can't spawn itself).
  5. **wires** the durable provenance the rule engine could not yet reach
     (`request -produced_imagination-> imagination`,
     `agent -produced_imagination-> imagination` — the latter is what the
     agent's OWN judge rule, `judge_imagined_conclusion_<tag>`, matches on
     to find imaginations to read the reground verdict off; the rule
     cannot add this edge itself because the `Imagination` node does not
     exist until `imagine()`, a Python call, mints it).
  6. **marks** the request `"done"`.

Node vocabulary (fixed contract — do not deviate):
    ImagineRequest{status, kind, hypothesis_template, why}
      -focuses_on_gap-> GroundingGap        (grounding_gap kind)
      -focuses_on_axis-> CapabilityAxis     (cost_worth_refining kind)
      -about_impasse-> Impasse
      -produced_imagination-> Imagination   (written by THIS module)
    Agent -produced_imagination-> Imagination   (written by THIS module)

`scan_and_imagine` is safe to call repeatedly and does nothing when there
is nothing to do — same idiom as `experiment_dispatch.scan_and_dispatch`,
minus the out-of-process detachment (`imagine()` is an in-process, bounded
-step call; no subprocess is needed). It does NOT call `tick()` /
`run_rules()` itself — same as `scan_and_dispatch` — so the agent's own
`judge_imagined_conclusion_<tag>` rule (which matches on the
`produced_imagination` edge this hook writes) only fires on the caller's
next tick, whatever cadence the host already runs.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import substrate_rs as srs

from domains.imagination import imagine, reground


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    return sub, native, ag_node


def mint_imagine_request(agent, *, kind: str, focus_edge: str, focus_node,
                          why: str = "", hypothesis_template: Optional[dict] = None) -> Any:
    """Test/authoring helper — mirrors `experiment_dispatch.mint_experiment`:
    hand-mints an `ImagineRequest` the agent will normally mint itself via
    its own authored engage rule (`seeds/composer_imagination_graph.json`).
    Exists so the dispatch MECHANISM can be exercised/tested without that
    agent-authoring machinery. `focus_edge` is `"focuses_on_gap"` or
    `"focuses_on_axis"`; `hypothesis_template` defaults to the SAME shape
    the agent's own authored rule writes (a Hypothesis node that
    `contradicts` the resolved focus, sentinel `"__FOCUS__"`)."""
    sub, native, _ag = _resolve(agent)
    tmpl = hypothesis_template if hypothesis_template is not None else {
        "nodes": [{"key": "h", "type": "Hypothesis", "attrs": {}}],
        "edges": [{"src": "h", "type": "contradicts", "tgt": "__FOCUS__"}],
    }
    ir = sub.add_node("ImagineRequest", {
        "status": "requested", "kind": str(kind),
        "hypothesis_template": json.dumps(tmpl), "why": str(why),
    })
    native.add_edge_unchecked(ir, focus_edge, focus_node)
    return ir


def _resolve_focus(sub, native, req) -> Optional[list]:
    """Mechanically resolve an `ImagineRequest`'s focus node(s). No
    decision — pure attr read + one neighbour hop, guarded throughout
    (`has_node`, missing-attr) so a malformed/partial request never
    crashes the scan, only produces an unfocused (whole-graph) imagine."""
    for g in native.neighbours(req, "focuses_on_gap"):
        if not native.has_node(g):
            continue
        node_val = sub.node(g)["attrs"].get("node")
        if node_val is None:
            continue
        nid = node_val if hasattr(node_val, "value") else srs.NodeID(int(node_val))
        if native.has_node(nid):
            return [nid]
    for ax in native.neighbours(req, "focuses_on_axis"):
        if native.has_node(ax):
            return [ax]
    for node in native.neighbours(req, "focuses_on_node"):
        if native.has_node(node):
            return [node]
    return None


def _splice_focus(hypothesis_template: str, focus_val) -> dict:
    """Splice the resolved focus's real node-id value into the request's
    own hypothesis TEMPLATE (the agent's authored content — never chosen
    here) wherever the sentinel `"__FOCUS__"` appears as an edge endpoint.
    Mechanical substitution; an edge that still references an unresolved
    sentinel (no focus could be resolved) is dropped rather than passed
    through — never hand a dangling reference into `_inject_hypothesis`."""
    try:
        tmpl = json.loads(hypothesis_template or "{}")
    except Exception:
        tmpl = {}
    if not isinstance(tmpl, dict):
        tmpl = {}
    edges = tmpl.get("edges") or []
    resolved_edges = []
    for espec in edges:
        e = dict(espec)
        if e.get("tgt") == "__FOCUS__":
            if focus_val is None:
                continue
            e["tgt"] = focus_val
        if e.get("src") == "__FOCUS__":
            if focus_val is None:
                continue
            e["src"] = focus_val
        resolved_edges.append(e)
    tmpl["edges"] = resolved_edges
    tmpl.setdefault("nodes", [])
    return tmpl


def scan_and_imagine(agent) -> list:
    """NON-BLOCKING (nothing to block on — `imagine()` is an in-process,
    bounded-step call): run every REQUESTED `ImagineRequest` through
    `imagine()` + `reground()`, write the durable linkage the agent's rule
    could not yet reach (see module docstring), and mark it done. Returns
    the `ImagineRequest` NodeIDs processed this call. Makes NO decision
    about whether/what to imagine — both are already fixed on the request
    node by the agent's own authored rule; this only runs what was asked,
    exactly the shape `experiment_dispatch.scan_and_dispatch` uses for
    Experiment requests."""
    sub, native, ag_node = _resolve(agent)
    touched: list = []

    for req in list(sub.nodes("ImagineRequest")):
        if not native.has_node(req):
            continue
        at = sub.node(req)["attrs"]
        if at.get("status") != "requested":
            continue

        focus_nodes = _resolve_focus(sub, native, req)
        focus_val = focus_nodes[0].value if focus_nodes else None
        hypothesis = _splice_focus(at.get("hypothesis_template") or "{}", focus_val)

        rehearsed = [exp for exp in native.neighbours(req, "rehearses_experiment")
                     if native.has_node(exp)]
        rewrite_delta = None
        if rehearsed:
            # Mechanical decoding of the SeedDelta the graph selected.  Some
            # deltas require a fresh seed boot or concept-library rebuild and
            # cannot honestly be represented by an in-place detached collapse;
            # expose that boundary instead of silently running a false test.
            from domains.experiment_dispatch import _seed_delta_of
            rewrite_delta = _seed_delta_of(agent, rehearsed[0])
            unsupported = []
            for key in ("skip_seeds", "add_concepts", "remove_concepts"):
                if rewrite_delta.get(key):
                    unsupported.append(key)
            if unsupported:
                native.set_attr(req, "status", "needs_external_grounding")
                native.set_attr(req, "unsupported_delta_dimensions", unsupported)
                for exp in rehearsed:
                    native.set_attr(exp, "status", "counterfactual_blocked")
                    native.set_attr(exp, "counterfactual_limit",
                                    "delta requires a fresh boot or concept-library reconstruction")
                touched.append(req)
                continue

        dc = imagine(agent, focus_nodes=focus_nodes, hypothesis=hypothesis or None,
                     rewrite_delta=rewrite_delta)
        rg = reground(agent, dc)

        native.add_edge_unchecked(req, "produced_imagination", dc.imagination_node)
        for experiment in rehearsed:
            native.add_edge_unchecked(
                experiment, "received_counterfactual_imagination",
                dc.imagination_node)
        if ag_node is not None and native.has_node(ag_node):
            native.add_edge_unchecked(ag_node, "produced_imagination", dc.imagination_node)
        native.set_attr(req, "status", "done")
        native.set_attr(req, "n_survived", len(rg["survivors"]))
        native.set_attr(req, "n_discarded", len(rg["discarded"]))
        touched.append(req)

    return touched


__all__ = ["mint_imagine_request", "scan_and_imagine"]
