"""audience_production_dispatch — the mechanical host hook for AUDIENCE-DRIVEN
PRODUCTION COGNITION (host I/O only, per CLAUDE.md): finds `ProduceForAudienceRequest{
status: "requested"}` nodes (the agent's own rule minted -- `seeds/
composer_audience_produce_graph.json`'s `request_produce_for_audience_<tag>` -- or
`mint_produce_for_audience_request` for a test/script exercising the same contract),
calls `domains.audience_driven_production.audience_model` + `select_utterance` -- an
in-process Python call a Rust rule effect cannot make (`audience_model` chains
`domains.system_model.model_system`'s foreign_snapshot path; `select_utterance` chains
`domains.pragmatic_speaker.choose_encoding` + `domains.language.produce`, all Python) --
and mechanically wires `req -has_audience_model-> sm` so the agent's OWN authored rules
(`seeds/composer_audience_produce_graph.json`'s `default_explicit_produce_<tag>` /
`tailor_when_grounded_<tag>`) can match on it. Twin of `domains/system_model_dispatch.py`'s
`scan_and_model` -- SAME discipline: this module makes NO decision about whether to tailor
or fall back to explicit (entirely the agent's own composed rules' concern, reading
`SystemModel.grounded` off the graph); it only calls Python host functions a Rust rule
effect cannot call, on a mechanical "any pending request" scan, and mechanically exposes
the result to the rule engine as a matchable edge (the same idiom `domains.
reflective_faculty.ensure_grounding_gap_edges` uses for `GroundingGap`, and `domains.
system_model_dispatch.scan_and_model` uses for `has_system_model`).

ONE HONEST WRINKLE vs `system_model_dispatch` (documented, not hidden): `domains.
audience_driven_production.audience_model` intentionally builds NO `SystemModel` node at
all when the interlocutor was never observed (its own module docstring: "an unobserved
audience contributes NOTHING to the shared-model credit, on purpose") -- there is nothing
to ground. So the agent's own `default_explicit_produce_<tag>` / `tailor_when_grounded_
<tag>` rules, which need to read `SystemModel.grounded` off the graph EITHER WAY (the
"GROUNDED-ATTR-DRIVEN" discipline -- never a host-side flag), would have nothing to match
in the ungrounded case. This module closes that gap the same way `tests/
test_system_model_cognition.py`'s own `test_model_other_belief_does_not_trust_an_
ungrounded_model` proves the rule's gate: it mints an HONEST placeholder `SystemModel{
grounded: false}` node -- the SAME node type and attr vocabulary the grounded case uses,
never a new invented shape -- so the branch always has a real `SystemModel` node to read,
whichever way the observation actually went.

`mint_produce_for_audience_request(agent, meaning, interlocutor, **extra_attrs)` is the
host-side helper that REQUESTS an audience-tailored production of `meaning` for
`interlocutor` (mints the `Interlocutor` node + the `ProduceForAudienceRequest` + the
`for_interlocutor` edge). The DECISION of WHAT to say to WHOM belongs to whoever calls
this -- an agent-authored rule (the SAME contract `request_produce_for_audience_<tag>`
satisfies when it recognises a `produce_utterance` Goal carrying a `for_audience` edge), a
test/gate script here exercising the same contract this hook consumes. This function only
performs the mechanical graph write, never a judgement about who to tailor to.

`scan_and_speak_to_audience(agent, lexicon, **select_kwargs)` is safe to call every tick:
it scans `ProduceForAudienceRequest` nodes still `status:"requested"`, calls
`audience_model` + `select_utterance` once per pending request, marks it
`status:"modeled"` (idempotent -- a re-scan never re-models the same request), and returns
the per-request results produced this call (empty list on a no-op scan)."""
from __future__ import annotations

from typing import Any, Optional

import domains.audience_driven_production as adp

_REQUEST_TYPE = "ProduceForAudienceRequest"
_INTERLOCUTOR_TYPE = "Interlocutor"
_FOR_INTERLOCUTOR_EDGE = "for_interlocutor"
_HAS_AUDIENCE_MODEL_EDGE = "has_audience_model"
_REQUESTS_EDGE = "requests_audience_produce"


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


def mint_produce_for_audience_request(agent, meaning, interlocutor: dict, **extra_attrs) -> Any:
    """Mint an `Interlocutor{id, observed, known_concepts}` node (mechanical snapshot of
    `interlocutor`) + a `ProduceForAudienceRequest{status:'requested', meaning: [...]}` node
    + a `req -for_interlocutor-> interlocutor_node` edge + an `agent -requests_audience_
    produce-> req` edge. Mechanical graph I/O only -- the caller decides WHAT to say to
    WHOM; this only writes the nodes `scan_and_speak_to_audience` will later consume."""
    sub, native, ag_node = _resolve(agent)
    aid = interlocutor.get("id", "interlocutor")
    interlocutor_attrs = {
        "id": aid,
        "observed": bool(interlocutor.get("observed", False)),
        "known_concepts": [str(c) for c in interlocutor.get("known_concepts", [])],
    }
    interlocutor_node = sub.add_node(_INTERLOCUTOR_TYPE, interlocutor_attrs)
    attrs = {"status": "requested", "meaning": sorted({str(c) for c in meaning})}
    attrs.update(extra_attrs)
    req = sub.add_node(_REQUEST_TYPE, attrs)
    _add_edge_unchecked(native, req, _FOR_INTERLOCUTOR_EDGE, interlocutor_node)
    if ag_node is not None:
        _add_edge_unchecked(native, ag_node, _REQUESTS_EDGE, req)
    return req


def _read_interlocutor(sub, native, req) -> dict:
    for nb in native.neighbours(req, _FOR_INTERLOCUTOR_EDGE):
        iat = sub.node(nb)["attrs"]
        return {
            "id": iat.get("id", "interlocutor"),
            "observed": bool(iat.get("observed", False)),
            "known_concepts": list(iat.get("known_concepts") or []),
        }
    return {"id": "interlocutor", "observed": False, "known_concepts": []}


def _mint_ungrounded_placeholder(sub, aid: str):
    """An HONEST `grounded:false` `SystemModel` -- the SAME node type/attr vocabulary
    `system_model.model_system`'s grounded path writes -- for the case `audience_model`
    intentionally builds NO model at all (an unobserved interlocutor). Mints no new shape,
    invents no new semantics: just makes the already-true fact ('this audience was never
    grounded') matchable by the agent's own rule, the same way the grounded case is."""
    return sub.add_node("SystemModel", {
        "target_kind": "foreign_snapshot", "target_id": f"audience:{aid}",
        "converged": False, "residual": 1.0, "grounded": False,
        "method": ("audience_production_dispatch: no observation of this interlocutor -- "
                   "domains.audience_driven_production.audience_model() intentionally builds "
                   "no SystemModel for an unobserved audience (nothing to ground); this is an "
                   "honest grounded:false placeholder in the SAME node type/attr vocabulary "
                   "the grounded case uses, so the agent's own rule always has a real "
                   "SystemModel to read grounded off, whichever way observation went."),
    })


def scan_and_speak_to_audience(agent, lexicon: list[dict], **select_kwargs) -> list[dict]:
    """Call `audience_model` + `select_utterance` for every `ProduceForAudienceRequest{
    status:'requested'}`, mechanically wire `req -has_audience_model-> sm` (a real grounded
    SystemModel, or the honest `grounded:false` placeholder when the interlocutor was never
    observed), record the host's mechanically-computed utterance/terseness/grounded_used
    onto the request, then mark it `status:'modeled'` so a re-scan never re-models it.
    Returns `[{"request", "system_model", "result", "interlocutor"}, ...]` for this call
    (empty if no pending requests -- safe to call every tick regardless). Makes no
    decision: WHOM to model was already decided by whoever minted the request; WHETHER to
    tailor or fall back to explicit is entirely the agent's own composed rules' concern
    (`seeds/composer_audience_produce_graph.json`), read off `sm.grounded` after this call
    plus a `run_rules`."""
    sub, native, ag_node = _resolve(agent)
    results: list[dict] = []
    for req in list(sub.nodes(_REQUEST_TYPE)):
        at = sub.node(req)["attrs"]
        if at.get("status") != "requested":
            continue
        interlocutor = _read_interlocutor(sub, native, req)
        meaning = set(at.get("meaning") or [])

        bundle = adp.audience_model(agent, interlocutor)
        if bundle["system_model"] is not None:
            sm_node = bundle["system_model"].model_node
        else:
            sm_node = _mint_ungrounded_placeholder(sub, interlocutor.get("id", "interlocutor"))
        _add_edge_unchecked(native, req, _HAS_AUDIENCE_MODEL_EDGE, sm_node)

        res = adp.select_utterance(agent, meaning, bundle, lexicon, **select_kwargs)
        native.set_attr(req, "utterance", res["utterance"])
        native.set_attr(req, "terseness", res["terseness"])
        native.set_attr(req, "grounded_used", res["grounded_used"])
        native.set_attr(req, "status", "modeled")

        results.append({"request": req, "system_model": sm_node, "result": res,
                         "interlocutor": interlocutor})
    return results


__all__ = ["mint_produce_for_audience_request", "scan_and_speak_to_audience"]
