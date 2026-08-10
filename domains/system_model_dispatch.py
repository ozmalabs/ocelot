"""system_model_dispatch — the mechanical host hook for TIER 5 SYSTEM-MODEL
COGNITION (host I/O only, per CLAUDE.md): finds `ModelRequest{status:
"requested", target_spec: <target>}` nodes (the agent's own rule minted, or
`mint_model_request` for a test/script exercising the same contract), calls
`domains.system_model.model_system(agent, target)` — an in-process Python
call a Rust rule effect cannot make (`model_system` chains
`domains.collapse_model.predict_collapse` / `domains.imagination.imagine` /
`domains.grounding_reach.grounding_reach`, all Python) — and mechanically
wires `agent -has_system_model-> model` so the agent's OWN authored rules
(`seeds/composer_system_model_graph.json`'s `model_other_belief_<tag>` /
`recognize_modeling_terminates_<tag>`) can match on it. Twin of
`domains/collapse_watch.py`'s `scan_and_predict` — SAME discipline: this
module makes NO decision about what the model MEANS or what to DO about it
(entirely the agent's own composed rules' concern); it only calls a Python
host function a Rust rule effect cannot call, on a mechanical "any pending
request" scan, and mechanically exposes the result to the rule engine as a
matchable edge (the same idiom `domains.reflective_faculty.
ensure_grounding_gap_edges` uses for `GroundingGap`).

`mint_model_request(agent, target, **extra_attrs)` is the host-side helper
that REQUESTS a model of some target system. The DECISION of WHICH target to
model belongs to whoever calls this — an agent-authored rule, in a future
autonomous build that decides WHEN to model a foreign system; a test/gate
script, here, exercising the same contract this hook consumes. This function
only performs the mechanical graph write (mint the node + wire the
`requests_model` edge), never a judgement about what's worth modelling.

`scan_and_model(agent, **model_kwargs)` is safe to call every tick: it scans
`ModelRequest` nodes still `status:"requested"`, calls `model_system` once
per pending request, marks it `status:"done"` (idempotent — a re-scan never
re-models the same request), and returns the `SystemModelResult`s produced
this call (empty list on a no-op scan)."""
from __future__ import annotations

from typing import Any, Optional

from domains.system_model import SystemModelResult, model_system

_REQUEST_TYPE = "ModelRequest"
_HAS_MODEL_EDGE = "has_system_model"
_REQUESTS_EDGE = "requests_model"
_PRODUCED_EDGE = "produced"


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        for n in sub.nodes("Agent"):
            if not sub.node(n)["attrs"].get("is_class"):
                ag_node = n
                break
    return sub, native, ag_node


def _add_edge_unchecked(native, src, edge_type, tgt, attrs=None) -> None:
    try:
        native.add_edge_unchecked(src, edge_type, tgt, attrs or {})
    except TypeError:
        native.add_edge_unchecked(src, edge_type, tgt)


def mint_model_request(agent, target: Any, **extra_attrs) -> Any:
    """Mint a `ModelRequest{status:'requested', target_spec: target}` node +
    `agent -requests_model-> mr` edge. Mechanical graph I/O only — the
    caller decides WHICH target; this only writes the node `scan_and_model`
    will later consume."""
    sub, native, ag_node = _resolve(agent)
    attrs = {"status": "requested", "target_spec": target}
    attrs.update(extra_attrs)
    mr = sub.add_node(_REQUEST_TYPE, attrs)
    if ag_node is not None:
        _add_edge_unchecked(native, ag_node, _REQUESTS_EDGE, mr)
    return mr


def scan_and_model(agent, **model_kwargs) -> list:
    """Call `model_system(agent, target_spec, **model_kwargs)` for every
    `ModelRequest{status:'requested'}`, mechanically wire `agent
    -has_system_model-> model_node` + `mr -produced-> model_node`, then mark
    the request `status:'done'` so a re-scan never re-models it. Returns the
    `SystemModelResult`s produced this call (empty if no pending requests —
    safe to call every tick regardless). Makes no decision: WHICH target was
    already decided by whoever minted the `ModelRequest`; WHAT to do with
    the resulting `SystemModel` is entirely the agent's own composed rules'
    concern (`seeds/composer_system_model_graph.json`)."""
    sub, native, ag_node = _resolve(agent)
    results: list[SystemModelResult] = []
    for mr in list(sub.nodes(_REQUEST_TYPE)):
        at = sub.node(mr)["attrs"]
        if at.get("status") != "requested":
            continue
        target = at.get("target_spec")
        res = model_system(agent, target if target is not None else "self", **model_kwargs)
        if ag_node is not None:
            _add_edge_unchecked(native, ag_node, _HAS_MODEL_EDGE, res.model_node)
        _add_edge_unchecked(native, mr, _PRODUCED_EDGE, res.model_node)
        native.set_attr(mr, "status", "done")
        results.append(res)
    return results


__all__ = ["mint_model_request", "scan_and_model"]
