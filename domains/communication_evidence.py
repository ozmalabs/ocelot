"""Language-neutral communication evidence boundary.

Language adapters translate their own semantic frames into this small schema.
No surface words, scripts, POS tags, or language-specific ordering belong here.
"""
from __future__ import annotations


_FORCE_TO_GOAL = {
    "information_request": "answer_or_learn",
    "action_request": "act_or_clarify",
    "assertion_or_correction": "update_common_ground",
    "repair_or_defer": "clarify_or_defer",
    "social_action": "coordinate_socially",
}


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
    for key in ("language", "modality", "polarity", "temporal_scope"):
        if key in frame and frame[key] is not None:
            evidence[f"evidence_{key}"] = frame[key]
    return evidence
