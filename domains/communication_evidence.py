"""Language-neutral communication evidence boundary.

Language adapters translate their own semantic frames into this small schema.
No surface words, scripts, POS tags, or language-specific ordering belong here.
"""
from __future__ import annotations

from collections.abc import Mapping


_FORCE_TO_GOAL = {
    "information_request": "answer_or_learn",
    "action_request": "act_or_clarify",
    "assertion_or_correction": "update_common_ground",
    "repair_or_defer": "clarify_or_defer",
    "social_action": "coordinate_socially",
    "acknowledgement": "update_common_ground",
    "refusal": "update_common_ground",
}
_RELATION_SCOPES = frozenset({"event_specific", "conceptual_general"})
_RELATION_FOCI = frozenset({"polar", "reason", "thing", "selection"})
_SELECTION_TARGET_KINDS = frozenset({"rule"})
_COMMUNICATIVE_ACTS = frozenset({
    "inability_action", "ability_action_offer", "nonunderstanding_report",
})
_OFFER_TARGET_STATUSES = frozenset({"concept_available", "unresolved", "missing"})
_NEUTRAL_ACT_TYPES = frozenset({
    "greeting", "thanks", "farewell", "polar_question",
    "information_question", "action_request", "assertion",
    "acknowledgement", "refusal", "inability_action",
    "ability_action_offer", "nonunderstanding_report",
})


def normalize_communicative_acts(value) -> list[dict]:
    """Validate a language adapter's ordered, non-exclusive act evidence.

    A compound utterance can contain multiple true acts. The legacy event-level
    force remains available as a summary, but this list preserves every typed
    act and its order so that summary does not erase co-occurring meaning.
    """
    if value is None:
        return []
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError("communicative_acts must be a non-empty sequence")
    normalized = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError("each communicative act must be a mapping")
        act_type = item.get("act_type")
        force = item.get("force")
        if act_type not in _NEUTRAL_ACT_TYPES:
            raise ValueError("communicative act has an unsupported act_type")
        if force not in _FORCE_TO_GOAL:
            raise ValueError("communicative act has an unsupported force")
        goal = item.get("goal", _FORCE_TO_GOAL[force])
        if goal != _FORCE_TO_GOAL[force]:
            raise ValueError("communicative act goal conflicts with its force")
        normalized.append({
            "act_type": act_type,
            "force": force,
            "goal": goal,
            "sequence_index": index,
        })
    return normalized


def from_semantic_frame(frame: dict, *, provider: str) -> dict:
    """Convert an adapter-produced semantic frame into neutral evidence.

    ``frame`` is already language-adapted; this function does not inspect its
    surface form. Providers may supply the neutral force directly or use the
    cross-language speech-act category as a provisional mapping.
    """
    force = frame.get("communicative_force")
    if force is None:
        force = {
            "question": "information_request",
            "command": "action_request",
            "instruction": "action_request",
            "assertion": "assertion_or_correction",
            "report": "assertion_or_correction",
            "social": "social_action",
        }.get(frame.get("speech_act"))
        if force is None:
            raise ValueError(
                "semantic frame lacks a supported neutral communicative force")
    if force not in _FORCE_TO_GOAL:
        raise ValueError("semantic frame lacks a supported neutral communicative force")
    evidence = {
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": provider,
        "evidence_force": force,
        "evidence_goal": frame.get("cognitive_goal") or _FORCE_TO_GOAL[force],
    }
    communicative_acts = normalize_communicative_acts(
        frame.get("communicative_acts"))
    if communicative_acts:
        if not any(act["force"] == force for act in communicative_acts):
            raise ValueError(
                "communicative_acts must include the event-level force")
        evidence["evidence_communicative_acts"] = communicative_acts
    communicative_act = frame.get("communicative_act")
    if communicative_act is not None:
        if communicative_act not in _COMMUNICATIVE_ACTS:
            raise ValueError("semantic frame has an unsupported communicative act")
        evidence["evidence_communicative_act"] = communicative_act
    offer_target_status = frame.get("offer_target_status")
    if offer_target_status is not None:
        if offer_target_status not in _OFFER_TARGET_STATUSES:
            raise ValueError("semantic frame has an unsupported offer target status")
        if communicative_act != "ability_action_offer":
            raise ValueError("offer target status requires an ability action offer")
        evidence["evidence_offer_target_status"] = offer_target_status
    # Semantic content is optional and remains adapter-owned.  Preserve it
    # only when the provider explicitly supplies a neutral proposition record;
    # this boundary never derives content from surface text or from a lexical
    # concept.  The proposition bridge validates the record before minting
    # any epistemic graph state.
    proposition = frame.get("proposition")
    if proposition is not None:
        if not isinstance(proposition, dict):
            raise ValueError("semantic proposition evidence must be a mapping")
        evidence["evidence_proposition"] = dict(proposition)
    content_refs = frame.get("content_refs")
    relation_target_ref = frame.get("relation_target_ref")
    normalized_relation_target = None
    if relation_target_ref is not None:
        if not isinstance(relation_target_ref, dict):
            raise ValueError("semantic relation target ref must be a mapping")
        node_type = relation_target_ref.get("type")
        name = relation_target_ref.get("name")
        if (node_type != "Concept" or not isinstance(name, str)
                or not name.strip()):
            raise ValueError(
                "semantic relation target ref needs a named Concept")
        normalized_relation_target = {
            "type": "Concept", "name": name.strip(),
        }
        if content_refs is None:
            content_refs = []
        if not isinstance(content_refs, (list, tuple)):
            raise ValueError("semantic content_refs must be a sequence")
        content_refs = [*content_refs, normalized_relation_target]
    if content_refs is not None:
        if not isinstance(content_refs, (list, tuple)):
            raise ValueError("semantic content_refs must be a sequence")
        normalized_refs = set()
        for ref in content_refs:
            if not isinstance(ref, dict):
                raise ValueError("semantic content ref must be a mapping")
            node_type, name = ref.get("type"), ref.get("name")
            if (not isinstance(node_type, str) or not node_type.strip()
                    or not isinstance(name, str) or not name.strip()):
                raise ValueError("semantic content ref needs typed name")
            normalized_refs.add((node_type.strip(), name.strip()))
        evidence["evidence_content_refs"] = [
            {"type": node_type, "name": name}
            for node_type, name in sorted(normalized_refs)
        ]
    if normalized_relation_target is not None:
        evidence["evidence_relation_target_ref"] = normalized_relation_target
    for key in ("language", "modality", "polarity", "temporal_scope",
                "relation_scope", "relation_focus"):
        if key in frame and frame[key] is not None:
            if (key == "relation_scope"
                    and frame[key] not in _RELATION_SCOPES):
                raise ValueError("semantic frame relation_scope is unsupported")
            if (key == "relation_focus"
                    and frame[key] not in _RELATION_FOCI):
                raise ValueError("semantic frame relation_focus is unsupported")
            evidence[f"evidence_{key}"] = frame[key]
    selection_target_kind = frame.get("selection_target_kind")
    if selection_target_kind is not None:
        if selection_target_kind not in _SELECTION_TARGET_KINDS:
            raise ValueError("semantic frame selection_target_kind is unsupported")
        if frame.get("relation_focus") != "selection":
            raise ValueError(
                "selection_target_kind requires relation_focus=selection")
        evidence["evidence_selection_target_kind"] = selection_target_kind
    return evidence
