"""Mechanical boundary for Phase 4A deliberative candidates.

This module does not choose a candidate.  It transports evidence from
graph-resident cognition into graph nodes and asks the native rule engine to
score, collapse, and trace the deliberation.  Candidate generation here is
therefore an evidence-materialization operation; valuation, selection, and
counterfactual credit remain substrate decisions.
"""
from __future__ import annotations

from typing import Any, Iterable


def materialize_deliberation(agent, *, goal, candidates: Iterable[dict[str, Any]],
                             epoch: int = 1, grounding_floor: float = 1.0,
                             residual_cost_gain: float = 1.0,
                             consequence_gain: float = 1.0,
                             novelty_gain: float = 1.0,
                             valuation_mode: str = "complete_phase4_tuple") -> Any:
    """Create a graph-resident deliberation and candidate ledger.

    The input candidates are evidence-bearing proposals from cognition/faculty
    boundaries.  This function performs no ranking, sorting, or fallback
    selection.  Missing grounding is preserved for the native rejection rule.
    """
    if valuation_mode not in {"complete_phase4_tuple", "authored_family_prior"}:
        raise ValueError("unsupported deliberation valuation mode")
    candidates = list(candidates)
    d = agent.s.add_node("Deliberation", {
        "status": "proposed",
        "epoch": float(epoch),
        "grounding_floor": float(grounding_floor),
        "residual_cost_gain": float(residual_cost_gain),
        "consequence_gain": float(consequence_gain),
        "novelty_gain": float(novelty_gain),
        "candidate_trace_complete": 0.0,
        "valuation_mode": valuation_mode,
    })
    agent.inner.add_edge_unchecked(d, "about_goal", goal)
    for ordinal, spec in enumerate(candidates):
        if not isinstance(spec, dict):
            raise TypeError("each deliberative candidate must be an evidence mapping")
        required = {"candidate_id", "grounding"}
        if valuation_mode == "complete_phase4_tuple":
            required.update({"expected_value", "residual_cost",
                             "consequence", "novelty"})
        elif set(spec).intersection({"expected_value", "residual_cost",
                                     "consequence", "novelty"}):
            raise ValueError("authored-prior candidates must not supply Phase 4 tuple fields")
        missing = list(required.difference(spec))
        if missing:
            raise ValueError(f"candidate missing evidence fields: {missing}")
        c = agent.s.add_node("DeliberativeCandidate", {
            "candidate_id": str(spec["candidate_id"]),
            "kind": str(spec.get("kind", "unspecified")),
            "grounding": float(spec["grounding"]),
            "valuation_mode": valuation_mode,
            "evidence_path": str(spec.get("evidence_path", "")),
            "source_relation": str(spec.get("source_relation", "")),
            "status": "proposed",
            "ordinal": float(ordinal),
            "score_epoch": -1.0,
            "rejection_trace": 0.0,
            "counterfactual_trace": 0.0,
            "execution_ready": float(spec.get("execution_ready", 0.0)),
            "outcome_status": str(spec.get("outcome_status", "pending")),
        })
        for field in ("expected_value", "residual_cost", "consequence", "novelty"):
            if field in spec:
                agent.s.set_attr(c, field, float(spec[field]))
        agent.inner.add_edge_unchecked(d, "has_candidate", c)
    return d


def materialize_from_discourse_state(agent, *, state, goal=None, epoch: int = 1,
                                     grounding_floor: float = 1.0,
                                     residual_cost_gain: float = 1.0,
                                     consequence_gain: float = 1.0,
                                     novelty_gain: float = 1.0) -> Any:
    """Generate evidence-bearing proposals from graph-resident discourse state.

    This is deliberately not a selector.  Active goals, linked repair needs,
    and residual stance nodes are read as cognitive evidence and converted to
    a ledger; the native Phase 4 rules remain authoritative for valuation and
    collapse.  A state with no such evidence still creates a deliberation so
    the native ``no_candidate`` outcome is explicit.
    """
    if not agent.s.has_node(state):
        raise ValueError("discourse state source does not exist")
    if agent.s.node(state)["type"] != "DiscourseState":
        raise TypeError("candidate source must be a DiscourseState node")

    goals = list(agent.inner.neighbours(state, "has_active_goal"))
    if goal is not None:
        if goal not in goals or not agent.s.has_node(goal):
            raise ValueError("selected goal must be active in the source state")
        goals = [goal]
    repair_nodes = list(agent.inner.neighbours(state, "has_repair_need"))
    stance_nodes = list(agent.inner.neighbours(state, "has_residual_stance"))
    state_attrs = dict(agent.s.node(state)["attrs"])
    residuals = list(state_attrs.get("unresolved_residuals") or [])
    specs = []

    required = {"grounding", "expected_value", "residual_cost",
                "consequence", "novelty"}

    for ordinal, goal in enumerate(goals):
        attrs = dict(agent.s.node(goal)["attrs"])
        # A lifecycle goal is not itself deliberative evidence.  In particular,
        # do not turn absent numeric evidence into fabricated defaults.
        evidence_source = goal
        if not required.issubset(attrs):
            # A goal may be supported by a separate faculty/evidence node.
            # Consume that explicit evidence without copying policy defaults
            # onto the lifecycle goal itself.
            for support in agent.inner.neighbours(goal, "supported_by"):
                support_attrs = dict(agent.s.node(support)["attrs"])
                if required.issubset(support_attrs):
                    attrs = support_attrs
                    evidence_source = goal
                    break
            else:
                continue
        goal_id = str(attrs.get("goal_id", goal))
        specs.append({
            "candidate_id": f"goal:{goal_id}", "kind": str(attrs.get("kind", "goal")),
            "grounding": float(attrs["grounding"]),
            "expected_value": float(attrs["expected_value"]),
            "residual_cost": float(attrs["residual_cost"]),
            "consequence": float(attrs["consequence"]),
            "novelty": float(attrs["novelty"]),
            "evidence_path": "discourse_state->active_goal",
            "source_evidence": evidence_source,
        })

    for repair in repair_nodes:
        attrs = dict(agent.s.node(repair)["attrs"])
        if not required.issubset(attrs):
            continue
        repair_id = str(attrs.get("repair_id", repair))
        specs.append({
            "candidate_id": f"repair:{repair_id}", "kind": "repair",
            "grounding": float(attrs["grounding"]),
            "expected_value": float(attrs["expected_value"]),
            "residual_cost": float(attrs["residual_cost"]),
            "consequence": float(attrs["consequence"]),
            "novelty": float(attrs["novelty"]),
            "evidence_path": "discourse_state->repair_need",
            "source_evidence": repair,
        })

    for stance in stance_nodes:
        attrs = dict(agent.s.node(stance)["attrs"])
        if not required.issubset(attrs):
            continue
        stance_id = str(attrs.get("stance_id", stance))
        specs.append({
            "candidate_id": f"stance:{stance_id}", "kind": "repair_or_defer",
            "grounding": float(attrs["grounding"]),
            "expected_value": float(attrs["expected_value"]),
            "residual_cost": float(attrs["residual_cost"]),
            "consequence": float(attrs["consequence"]),
            "novelty": float(attrs["novelty"]),
            "evidence_path": "discourse_state->residual_stance",
            "source_evidence": stance,
        })

    # A residual carried directly by state is evidence for a repair proposal,
    # not a language-specific trigger or an implicit reply.
    for ordinal, residual in enumerate(residuals):
        if not isinstance(residual, dict) or not required.issubset(residual):
            continue
        specs.append({
            "candidate_id": f"residual:{ordinal}", "kind": "repair_or_defer",
            "grounding": float(residual["grounding"]),
            "expected_value": float(residual["expected_value"]),
            "residual_cost": float(residual["residual_cost"]),
            "consequence": float(residual["consequence"]),
            "novelty": float(residual["novelty"]),
            "evidence_path": "discourse_state->unresolved_residual",
        })

    d = materialize_deliberation(
        agent, goal=goal if goal is not None else (goals[0] if goals else state),
        candidates=specs,
        epoch=epoch, grounding_floor=grounding_floor,
        residual_cost_gain=residual_cost_gain, consequence_gain=consequence_gain,
        novelty_gain=novelty_gain,
    )
    agent.inner.add_edge_unchecked(d, "generated_from_discourse_state", state)
    agent.s.set_attr(d, "candidate_source", "discourse_state")
    agent.s.set_attr(d, "source_candidate_count", float(len(specs)))
    for candidate, spec in zip(agent.inner.neighbours(d, "has_candidate"), specs):
        source = spec.get("source_evidence")
        if source is not None:
            agent.inner.add_edge_unchecked(candidate, "derived_from_evidence", source)
    return d


def materialize_from_thought_manifold(agent, *, goal, manifold,
                                      epoch: int = 1,
                                      grounding_floor: float = 1.0,
                                      residual_cost_gain: float = 1.0,
                                      consequence_gain: float = 1.0,
                                      novelty_gain: float = 1.0) -> Any:
    """Bridge a live graph-resident thought manifold into the ledger.

    A thought manifold is an upstream cognition object, not a selector.  It
    exposes evidence-bearing ``proposes_candidate`` edges; this boundary
    copies those proposals into the deliberation ledger and records their
    provenance.  It deliberately performs no ordering, scoring, or fallback
    choice.  Native rules remain authoritative for valuation and collapse.
    """
    if not agent.s.has_node(manifold):
        raise ValueError("thought manifold source does not exist")
    if agent.s.node(manifold)["type"] != "ThoughtManifold":
        raise TypeError("candidate source must be a ThoughtManifold node")
    source_candidates = list(agent.inner.neighbours(manifold,
                                                     "proposes_candidate"))
    if not source_candidates:
        raise ValueError("thought manifold has no candidate proposals")

    specs = []
    for source_candidate in source_candidates:
        attrs = dict(agent.s.node(source_candidate)["attrs"])
        required = {"candidate_id", "grounding", "expected_value",
                    "residual_cost", "consequence", "novelty"}
        missing = sorted(required.difference(attrs))
        if missing:
            raise ValueError(f"thought-manifold candidate missing evidence fields: {missing}")
        spec = {key: attrs[key] for key in required}
        spec.update({key: attrs[key] for key in (
            "kind", "evidence_path", "execution_ready", "outcome_status"
        ) if key in attrs})
        spec["source_candidate"] = source_candidate
        specs.append(spec)

    d = materialize_deliberation(
        agent, goal=goal, candidates=specs, epoch=epoch,
        grounding_floor=grounding_floor,
        residual_cost_gain=residual_cost_gain,
        consequence_gain=consequence_gain,
        novelty_gain=novelty_gain,
    )
    agent.inner.add_edge_unchecked(d, "generated_from_manifold", manifold)
    agent.s.set_attr(d, "candidate_source", "thought_manifold")
    agent.s.set_attr(d, "source_candidate_count", float(len(specs)))
    for ledger_candidate, spec in zip(
            agent.inner.neighbours(d, "has_candidate"), specs):
        agent.inner.add_edge_unchecked(ledger_candidate, "copied_from",
                                       spec["source_candidate"])
    return d


def materialize_from_live_thought_manifold(agent, *, goal, manifold,
                                           epoch: int = 1,
                                           grounding_floor: float = 1.0,
                                           residual_cost_gain: float = 1.0,
                                           consequence_gain: float = 1.0,
                                           novelty_gain: float = 1.0) -> Any:
    """Materialize proposals from several graph-native manifold evidence paths.

    This is a cognition boundary, not an arbitrator.  A live manifold may
    expose goal, repair, stance, and residual evidence through distinct graph
    relations.  Each source node must already carry the numeric evidence used
    by native deliberation; this function only transports it and records the
    relation and source provenance.  It never ranks, filters, selects, or
    invents a response when evidence is absent.
    """
    if not agent.s.has_node(manifold):
        raise ValueError("thought manifold source does not exist")
    if agent.s.node(manifold)["type"] != "ThoughtManifold":
        raise TypeError("candidate source must be a ThoughtManifold node")

    # Relations encode substrate-level evidence classes, not language forms.
    source_relations = (
        ("has_goal_evidence", "goal"),
        ("has_repair_evidence", "repair"),
        ("has_stance_evidence", "repair_or_defer"),
        ("has_residual_evidence", "repair_or_defer"),
    )
    specs = []
    source_records = []
    required = {"grounding", "expected_value", "residual_cost",
                "consequence", "novelty"}
    for relation, default_kind in source_relations:
        for source in agent.inner.neighbours(manifold, relation):
            attrs = dict(agent.s.node(source)["attrs"])
            missing = [key for key in required if key not in attrs]
            if missing:
                raise ValueError(
                    f"live manifold evidence missing fields for {source}: {missing}")
            source_id = str(attrs.get("candidate_id", source))
            spec = {
                "candidate_id": f"{relation}:{source_id}",
                "kind": str(attrs.get("kind", default_kind)),
                "grounding": float(attrs["grounding"]),
                "expected_value": float(attrs["expected_value"]),
                "residual_cost": float(attrs["residual_cost"]),
                "consequence": float(attrs["consequence"]),
                "novelty": float(attrs["novelty"]),
                "evidence_path": f"thought_manifold->{relation}",
                "source_relation": relation,
                "execution_ready": float(attrs.get("execution_ready", 0.0)),
                "outcome_status": str(attrs.get("outcome_status", "pending")),
            }
            specs.append(spec)
            source_records.append((source, relation))

    d = materialize_deliberation(
        agent, goal=goal, candidates=specs, epoch=epoch,
        grounding_floor=grounding_floor,
        residual_cost_gain=residual_cost_gain,
        consequence_gain=consequence_gain,
        novelty_gain=novelty_gain,
    )
    agent.inner.add_edge_unchecked(d, "generated_from_thought_manifold", manifold)
    agent.s.set_attr(d, "candidate_source", "live_thought_manifold")
    agent.s.set_attr(d, "source_candidate_count", float(len(specs)))
    for ledger_candidate, (source, relation) in zip(
            agent.inner.neighbours(d, "has_candidate"), source_records):
        agent.inner.add_edge_unchecked(ledger_candidate, "derived_from_evidence", source)
        agent.s.set_attr(ledger_candidate, "source_relation", relation)
    return d
