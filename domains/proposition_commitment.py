"""A narrow graph boundary for explicitly supplied neutral propositions.

This module is deliberately not a parser and not a semantic interpreter.  Its
input is the output contract of an upstream semantic adapter: a predicate,
role-labelled argument values, polarity, and provenance.  Surface text,
lexical concepts, and parse-only predications are rejected before any graph
mutation takes place.

The bridge keeps four things separate:

* ``Proposition`` is structured content;
* ``PropositionEvidence`` is the adapter/provenance record;
* attribution edges identify speaker, addressee, and originating event;
* an optional ``CommonGround`` edge records where the proposition is being
  considered, without silently treating it as accepted truth.

The node types are intentionally not seeded: this file is a mechanical
adapter boundary, and the graph APIs already support graph-native node/edge
creation.  No rule or text-reading path is invoked here.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


EVIDENCE_SCHEMA = "neutral_proposition_evidence.v1"
PROPOSITION_SCHEMA = "structured_proposition.v1"
EVIDENCE_KIND = "explicit_neutral"

_ALLOWED_KEYS = frozenset({
    "schema", "kind", "predicate", "arguments", "polarity",
    "provider", "evidence_id", "confidence", "commitment_status",
    "uptake_signal",
})
_POLARITIES = frozenset({"affirmed", "negated"})
_COMMITMENT_STATUSES = frozenset({
    "uncommitted", "proposed", "accepted", "challenged", "suspended",
    "retracted", "rejected", "uncertain",
})
_UPTAKE_SIGNALS = frozenset({"accept", "challenge", "suspend", "retract"})
_SURFACE_OR_PARSE_KEYS = frozenset({
    "text", "surface", "sentence", "utterance", "parse", "parsed",
    "predication", "predications", "construction", "lexical", "tokens",
})


def _resolve(agent):
    substrate = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(substrate, "_inner", substrate)
    return substrate, native


def _unsupported(reason: str) -> dict[str, Any]:
    """Return an explicit, non-mutating failure result."""
    return {
        "supported": False,
        "error": "unsupported_proposition_evidence",
        "reason": reason,
        "proposition": None,
        "evidence": None,
    }


def _node_exists(native, node) -> bool:
    if node is None:
        return False
    try:
        return bool(native.has_node(node))
    except (AttributeError, TypeError):
        return False


def _edge(native, source, edge_type: str, target) -> None:
    """Use the existing mechanical graph insertion API across arities."""
    try:
        native.add_edge_unchecked(source, edge_type, target)
    except TypeError:
        native.add_edge_unchecked(source, edge_type, target, {})


def _validate(evidence: Any) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(evidence, Mapping):
        return None, "evidence must be a mapping"

    keys = set(evidence)
    forbidden = sorted(keys & _SURFACE_OR_PARSE_KEYS)
    if forbidden:
        return None, "surface_or_parse_fields_are_not_supported:%s" % ",".join(forbidden)
    unknown = sorted(keys - _ALLOWED_KEYS)
    if unknown:
        return None, "unsupported_evidence_fields:%s" % ",".join(unknown)
    if evidence.get("schema") != EVIDENCE_SCHEMA:
        return None, "schema_must_be:%s" % EVIDENCE_SCHEMA
    if evidence.get("kind") != EVIDENCE_KIND:
        return None, "kind_must_be:%s" % EVIDENCE_KIND

    predicate = evidence.get("predicate")
    if not isinstance(predicate, str) or not predicate.strip():
        return None, "predicate_must_be_nonempty_neutral_identifier"
    arguments = evidence.get("arguments")
    if not isinstance(arguments, Mapping) or not arguments:
        return None, "arguments_must_be_nonempty_role_mapping"
    normalized_args: dict[str, str] = {}
    for role, value in arguments.items():
        if not isinstance(role, str) or not role.strip():
            return None, "argument_roles_must_be_nonempty_identifiers"
        if not isinstance(value, str) or not value.strip():
            return None, "argument_values_must_be_nonempty_neutral_identifiers"
        normalized_args[role.strip()] = value.strip()

    polarity = evidence.get("polarity")
    if polarity not in _POLARITIES:
        return None, "polarity_must_be_affirmed_or_negated"
    provider = evidence.get("provider")
    if not isinstance(provider, str) or not provider.strip():
        return None, "provider_is_required_for_provenance"
    evidence_id = evidence.get("evidence_id")
    if not isinstance(evidence_id, str) or not evidence_id.strip():
        return None, "evidence_id_is_required_for_provenance"

    confidence = evidence.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            return None, "confidence_must_be_numeric"
        if not 0.0 <= float(confidence) <= 1.0:
            return None, "confidence_must_be_between_zero_and_one"
    status = evidence.get("commitment_status", "uncommitted")
    if status not in _COMMITMENT_STATUSES:
        return None, "commitment_status_is_unsupported"
    uptake = evidence.get("uptake_signal")
    if uptake is not None and uptake not in _UPTAKE_SIGNALS:
        return None, "uptake_signal_is_unsupported"

    normalized = dict(evidence)
    normalized.update({
        "predicate": predicate.strip(),
        "arguments": normalized_args,
        "provider": provider.strip(),
        "evidence_id": evidence_id.strip(),
        "commitment_status": status,
    })
    if uptake is not None:
        normalized["uptake_signal"] = uptake
    return normalized, None


def bridge_proposition_evidence(
    agent,
    evidence: Mapping[str, Any],
    *,
    speaker=None,
    addressee=None,
    source_event=None,
    common_ground=None,
) -> dict[str, Any]:
    """Materialize one explicitly supplied neutral proposition.

    ``speaker``, ``addressee``, ``source_event``, and ``common_ground`` are
    existing graph node handles supplied by the caller.  They are never
    guessed from the evidence payload.  Invalid evidence or invalid handles
    return an explicit unsupported result and leave the graph unchanged.
    """
    normalized, reason = _validate(evidence)
    if normalized is None:
        return _unsupported(reason or "invalid_evidence")

    substrate, native = _resolve(agent)
    handles = (
        ("speaker", speaker), ("addressee", addressee),
        ("source_event", source_event), ("common_ground", common_ground),
    )
    for name, node in handles:
        if node is not None and not _node_exists(native, node):
            return _unsupported("%s_is_not_a_live_graph_node" % name)

    # Evidence ids are the adapter's provenance identity.  Replaying the same
    # event must not mint a second proposition or argument family; a conflicting
    # reuse is an explicit evidence error rather than an overwrite.
    expected_roles = json.dumps(sorted(normalized["arguments"]),
                                separators=(",", ":"))
    for existing in substrate.nodes("Proposition"):
        attrs = substrate.node(existing)["attrs"]
        if attrs.get("evidence_id") != normalized["evidence_id"]:
            continue
        if (attrs.get("predicate") != normalized["predicate"]
                or attrs.get("polarity") != normalized["polarity"]
                or attrs.get("argument_roles") != expected_roles
                or attrs.get("uptake_signal") != normalized.get("uptake_signal")):
            return _unsupported("evidence_id_conflicts_with_existing_proposition")
        evidence_nodes = list(native.neighbours(existing, "evidenced_by"))
        return {
            "supported": True,
            "error": None,
            "reason": "explicit_neutral_proposition_already_materialized",
            "proposition": existing,
            "evidence": evidence_nodes[0] if evidence_nodes else None,
        }

    # Validate everything before the first add_node: unsupported input is
    # guaranteed to be a no-op, including bad attribution handles.
    proposition_attrs = {
        "schema": PROPOSITION_SCHEMA,
        "predicate": normalized["predicate"],
        "polarity": normalized["polarity"],
        "commitment_status": normalized["commitment_status"],
        "argument_roles": expected_roles,
        "evidence_id": normalized["evidence_id"],
    }
    if normalized.get("confidence") is not None:
        proposition_attrs["confidence"] = float(normalized["confidence"])
    if normalized.get("uptake_signal") is not None:
        proposition_attrs["uptake_signal"] = normalized["uptake_signal"]
    proposition = substrate.add_node("Proposition", proposition_attrs)
    # Native lifecycle rules use the existing graph self-edge idiom to bind
    # exactly this proposition family without scanning arbitrary nodes.
    _edge(native, proposition, "is_structured_proposition", proposition)

    evidence_attrs = {
        "schema": EVIDENCE_SCHEMA,
        "kind": EVIDENCE_KIND,
        "provider": normalized["provider"],
        "evidence_id": normalized["evidence_id"],
    }
    evidence_node = substrate.add_node("PropositionEvidence", evidence_attrs)
    _edge(native, proposition, "evidenced_by", evidence_node)

    for role, value in normalized["arguments"].items():
        argument = substrate.add_node("PropositionArgument", {
            "schema": "proposition_argument.v1",
            "role": role,
            "value": value,
        })
        _edge(native, proposition, "has_argument", argument)

    if speaker is not None:
        _edge(native, speaker, "asserts", proposition)
    if addressee is not None:
        _edge(native, proposition, "addressed_to", addressee)
    if source_event is not None:
        _edge(native, proposition, "originated_in", source_event)
    if common_ground is not None:
        _edge(native, common_ground, "contains_claim", proposition)

    return {
        "supported": True,
        "error": None,
        "reason": "explicit_neutral_proposition_materialized",
        "proposition": proposition,
        "evidence": evidence_node,
    }


def apply_situation_consequence(agent, proposition) -> dict[str, Any]:
    """Project one accepted proposition into the existing situation model.

    This is a mechanical adapter seam, not a truth or parsing decision.  Only
    a graph-resident proposition whose native lifecycle records an explicit
    ``accept`` signal is eligible.  Its predicate and role-labelled arguments
    are already neutral adapter evidence; the existing situation-model reader
    and native event rules own the state transition and inference.
    """
    substrate, native = _resolve(agent)
    if not _node_exists(native, proposition) or substrate.node(proposition)["type"] != "Proposition":
        return _unsupported("proposition_is_not_a_live_graph_node")
    attrs = substrate.node(proposition)["attrs"]
    if (attrs.get("commitment_status") != "accepted"
            or attrs.get("uptake_applied") != "accept"):
        return _unsupported("proposition_has_no_explicit_accepted_uptake")
    if attrs.get("polarity") != "affirmed":
        return _unsupported(
            "negative_or_nonaffirmed_proposition_has_no_positive_consequence")
    if not list(native.neighbours(proposition, "evidenced_by")):
        return _unsupported("proposition_has_no_evidence")

    for receipt in substrate.nodes("SituationModelConsequence"):
        if native.has_edge(receipt, "for_proposition", proposition):
            return {
                "supported": True,
                "error": None,
                "reason": "situation_consequence_already_applied",
                "consequence": receipt,
            }

    values = {}
    for argument in native.neighbours(proposition, "has_argument"):
        a = substrate.node(argument)["attrs"]
        role, value = a.get("role"), a.get("value")
        if isinstance(role, str) and isinstance(value, str):
            if role in values and values[role] != value:
                return _unsupported("duplicate_argument_role_conflict")
            values[role] = value
    subject = values.get("agent") or values.get("subject")
    object_value = (values.get("theme") or values.get("patient")
                    or values.get("object") or values.get("goal")
                    or values.get("recipient"))
    if not subject or not object_value:
        return _unsupported("situation_consequence_requires_agent_and_object_roles")

    source_events = list(native.neighbours(proposition, "originated_in"))
    t = 0
    if source_events and substrate.has_node(source_events[0]):
        try:
            t = int(substrate.node(source_events[0])["attrs"].get("event_index", 0))
        except (TypeError, ValueError):
            t = 0
    from domains import situation_model_reader
    ingest = situation_model_reader.ingest_predication(
        agent, [str(attrs["predicate"]), subject, object_value], t=t)
    # Structural acceptance is not itself a typed world-state transition.
    # Leave properties, statives, generic events, and other unsupported
    # predications without a positive consequence record; the situation-model
    # faculty remains the authority for its own change-of-state classification.
    if ingest.get("kind") != "change_of_state" or not ingest.get("cos"):
        return {
            **_unsupported(
                "situation_model_did_not_confirm_change_of_state:%s"
                % str(ingest.get("kind") or "unknown")),
            "ingest": ingest,
        }
    consequence = substrate.add_node("SituationModelConsequence", {
        "schema": "situation_model_consequence.v1",
        "status": "applied",
        "predicate": str(attrs["predicate"]),
        "subject": subject,
        "object": object_value,
        "ingest_kind": str(ingest.get("kind") or ""),
        "source": "accepted_common_ground_projection",
    })
    _edge(native, consequence, "for_proposition", proposition)
    if source_events:
        _edge(native, consequence, "originated_in", source_events[0])
    return {
        "supported": True,
        "error": None,
        "reason": "accepted_proposition_projected_to_situation_model",
        "consequence": consequence,
        "ingest": ingest,
    }


__all__ = [
    "EVIDENCE_SCHEMA",
    "PROPOSITION_SCHEMA",
    "EVIDENCE_KIND",
    "bridge_proposition_evidence",
    "apply_situation_consequence",
]
