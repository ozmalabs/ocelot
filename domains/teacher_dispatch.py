"""Mechanical bridge from graph-selected teacher work to evidence nodes.

The graph selects both the demand (``TeacherRequest``) and the host action.
This module only performs the external lookup named by ``teacher_tier`` and
writes its result back as structured graph evidence.  It neither learns a
payload through ``learn_from_teacher`` nor composes an outgoing utterance.
"""
from __future__ import annotations

from copy import copy
from typing import Any, Mapping

from domains.openai_teacher import (
    OpenAITeacher,
    ShadowInterpretationEvidence,
    ShadowInterpretationQuestion,
    TeacherEvidence,
    TeacherQuestion,
)


_LOCAL_TIERS = {"dictionary", "wikipedia"}
_GRAPH_EVIDENCE_VERDICTS = {
    "supported", "corrected", "ambiguous", "unknown", "insufficient", "unavailable",
}


def _attrs(adapter: Any, node: Any) -> dict[str, Any]:
    return dict(adapter.s.node(node)["attrs"])


def _has_node(adapter: Any, node: Any) -> bool:
    checker = getattr(adapter.inner, "has_node", None)
    return bool(checker(node)) if checker is not None else True


def _eligible_host_actions(adapter: Any) -> list[Any]:
    """Read only graph-minted teacher actions.

    The daemon changes an already-selected request from ``requested`` to
    ``running`` immediately before invoking this module, so both states denote
    the same graph-selected action at this narrow I/O boundary.
    """
    eligible = []
    for action in list(adapter.s.nodes("HostActionRequest")):
        if not _has_node(adapter, action):
            continue
        attrs = _attrs(adapter, action)
        if (attrs.get("action") == "teacher"
                and attrs.get("source_type") == "TeacherRequest"
                and attrs.get("status") in {"requested", "running"}):
            eligible.append(action)
    return eligible


def _selected_teacher_requests(adapter: Any) -> set[Any]:
    """The supervisor's explicit source identity is the sole dispatch scope."""
    selected: set[Any] = set()
    for action in _eligible_host_actions(adapter):
        request = _attrs(adapter, action).get("source")
        if request is None or not _has_node(adapter, request):
            continue
        if adapter.s.node(request)["type"] == "TeacherRequest":
            selected.add(request)
    return selected


def _questions_from_request(attrs: Mapping[str, Any]) -> tuple[str, TeacherQuestion]:
    """Return a local lookup subject and the complete remote teaching prompt.

    Dictionary and Wikipedia teachers index subjects, rather than imperative
    clauses.  ``question_content`` is the graph-selected target (for example,
    ``sensor`` in ``calibrate sensor``); only when it is absent is the
    predicate a meaningful local fallback.  Terra receives the full
    predicate/content instruction plus its structured projection.
    """
    predicate = str(attrs.get("question_predicate") or "").strip()
    content = str(attrs.get("question_content") or "").strip()
    instruction_context = str(attrs.get("instruction_context") or "").strip()
    instruction = instruction_context or " ".join(part for part in (predicate, content) if part)
    if not instruction:
        instruction = str(attrs.get("question_kind") or "teacher gap").strip()
    local_subject = content or predicate or instruction
    return local_subject, TeacherQuestion(
        instruction=instruction,
        candidate_interpretation={
            "predicate": predicate,
            "content": content,
            "question_kind": str(attrs.get("question_kind") or ""),
            "speech_act": str(attrs.get("local_speech_act") or ""),
            "dispatch_path": str(attrs.get("local_dispatch_path") or ""),
            "intent": str(attrs.get("local_intent") or ""),
            "topic": str(attrs.get("local_topic") or ""),
        },
        context_projection={
            "origin": str(attrs.get("origin") or "agent"),
            "instruction_context": instruction_context,
        },
    )


def _lesson_key(tier: str, attrs: Mapping[str, Any]) -> str:
    parts = (tier, str(attrs.get("question_predicate") or "gap"),
             str(attrs.get("question_content") or "unknown"))
    return ":".join(part.replace(" ", "_")[:80] for part in parts)


def _local_evidence(tier: str, payload: Any) -> dict[str, Any]:
    """Translate a local lookup payload into untrusted graph candidates.

    Local ``answer`` prose is the actual dictionary definition/Wikipedia
    abstract.  It is retained only as a proposed definition for later graph
    replay/adoption, never translated into a Message, HeldAnswer, or outbound
    user text.
    """
    if not isinstance(payload, Mapping):
        return _unavailable_evidence(tier, "insufficient")
    answer = payload.get("answer")
    answer_text = answer.strip() if isinstance(answer, str) else ""
    concepts = []
    lexical_categories = []
    for item in payload.get("learn", []):
        if not isinstance(item, Mapping):
            continue
        phrase = item.get("phrase")
        description = item.get("description")
        if isinstance(phrase, str) and phrase:
            concepts.append({
                "name": phrase,
                "definition": answer_text or (
                    description if isinstance(description, str) else f"local:{tier}"),
            })
            for category in item.get("parts_of_speech", []):
                if isinstance(category, str) and category:
                    lexical_categories.append({"lexeme": phrase, "category": category})
    if not concepts:
        return _unavailable_evidence(tier, "insufficient")
    return {
        "verdict": "supported",
        "semantic_differences": [],
        "candidate_concepts": concepts,
        "candidate_relations": [],
        "candidate_frames": [],
        "candidate_constructions": [],
        "lexical_categories": lexical_categories,
        "missing_assumptions": [],
        "clarification_propositions": [],
        "evidence": [f"local:{tier}"],
    }


def _shadow_evidence_attrs(tier: str, request_attrs: Mapping[str, Any],
                           evidence: ShadowInterpretationEvidence) -> dict[str, Any]:
    """Mechanical projection of the alternate parse; no adoption or decision."""
    return {
        "status": "received",
        "teacher_tier": tier,
        "verdict": evidence.verdict,
        "lesson_key": _lesson_key(tier, request_attrs),
        "evidence_schema": "interpretation_shadow.v1",
        "speech_act": evidence.speech_act,
        "predicate": evidence.predicate,
        "content": evidence.content,
        "target_scope": evidence.target_scope,
        "answer_mode": evidence.answer_mode,
        "requested_relations": list(evidence.requested_relations),
        "disagreement_dimensions": list(evidence.disagreement_dimensions),
        "ambiguities": list(evidence.ambiguities),
        "evidence_spans": list(evidence.evidence_spans),
    }


def _materialize_shadow_evidence(adapter: Any, evidence_node: Any,
                                 evidence: ShadowInterpretationEvidence) -> None:
    for dimension in evidence.disagreement_dimensions:
        node = adapter.s.add_node("InterpretationDifference", {
            "dimension": dimension, "status": "proposed", "source": "llm_shadow",
        })
        adapter.inner.add_edge_unchecked(evidence_node, "proposes_difference", node)
    for relation in evidence.requested_relations:
        node = adapter.s.add_node("RequestedRelationCandidate", {
            "relation": relation, "status": "proposed", "source": "llm_shadow",
        })
        adapter.inner.add_edge_unchecked(evidence_node, "proposes_requested_relation", node)


def _unavailable_evidence(tier: str, verdict: str = "unavailable") -> dict[str, Any]:
    if verdict not in _GRAPH_EVIDENCE_VERDICTS:
        verdict = "unavailable"
    return {
        "verdict": verdict,
        "semantic_differences": [],
        "candidate_concepts": [],
        "candidate_relations": [],
        "candidate_frames": [],
        "candidate_constructions": [],
        "lexical_categories": [],
        "missing_assumptions": [f"teacher tier unavailable:{tier}"],
        "clarification_propositions": [],
        "evidence": [],
    }


def _evidence_attrs(tier: str, request_attrs: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    verdict = evidence.get("verdict")
    if verdict not in _GRAPH_EVIDENCE_VERDICTS:
        raise ValueError("invalid graph teacher verdict")
    return {
        "status": "received",
        "teacher_tier": tier,
        "verdict": verdict,
        "lesson_key": _lesson_key(tier, request_attrs),
        "evidence_schema": "teacher_evidence.v1",
        "semantic_differences": list(evidence["semantic_differences"]),
        "candidate_concepts": list(evidence["candidate_concepts"]),
        "candidate_relations": list(evidence["candidate_relations"]),
        "candidate_frames": list(evidence["candidate_frames"]),
        "candidate_constructions": list(evidence["candidate_constructions"]),
        "lexical_categories": list(evidence.get("lexical_categories", [])),
        "missing_assumptions": list(evidence["missing_assumptions"]),
        "clarification_propositions": list(evidence["clarification_propositions"]),
        "evidence": list(evidence["evidence"]),
    }


def _materialize_candidates(adapter: Any, evidence_node: Any, tier: str,
                            evidence: Mapping[str, Any]) -> None:
    """Make evidence candidates queryable without adopting any of them.

    These proposal types intentionally are not ``Concept``, ``Frame``, or
    executable constructions. They are untrusted transport facts for the
    graph's replay/adoption rules to inspect later.
    """
    for candidate in evidence["candidate_concepts"]:
        node = adapter.s.add_node("TeacherConceptCandidate", {
            "status": "proposed", "teacher_tier": tier,
            "name": candidate["name"], "definition": candidate["definition"],
        })
        adapter.inner.add_edge_unchecked(evidence_node, "proposes_concept", node)
    for candidate in evidence["candidate_relations"]:
        node = adapter.s.add_node("TeacherRelationCandidate", {
            "status": "proposed", "teacher_tier": tier,
            "subject": candidate["subject"], "predicate": candidate["predicate"],
            "object": candidate["object"],
        })
        adapter.inner.add_edge_unchecked(evidence_node, "proposes_relation", node)
    for candidate in evidence["candidate_frames"]:
        node = adapter.s.add_node("TeacherFrameCandidate", {
            "status": "proposed", "teacher_tier": tier, "name": candidate["name"],
        })
        adapter.inner.add_edge_unchecked(evidence_node, "proposes_frame", node)
        for index, slot in enumerate(candidate["slots"]):
            slot_node = adapter.s.add_node("TeacherFrameSlotCandidate", {
                "status": "proposed", "index": index, "name": slot,
            })
            adapter.inner.add_edge_unchecked(node, "has_slot_candidate", slot_node)
    for candidate in evidence["candidate_constructions"]:
        node = adapter.s.add_node("TeacherConstructionCandidate", {
            "status": "proposed", "teacher_tier": tier,
            "name": candidate["name"], "pattern": candidate["pattern"],
        })
        adapter.inner.add_edge_unchecked(evidence_node, "proposes_construction", node)
    for candidate in evidence.get("lexical_categories", []):
        node = adapter.s.add_node("TeacherLexicalCategoryCandidate", {
            "status": "proposed", "teacher_tier": tier,
            "lexeme": candidate["lexeme"], "category": candidate["category"],
        })
        adapter.inner.add_edge_unchecked(evidence_node, "proposes_lexical_category", node)


def _libraries(adapter: Any) -> Mapping[str, Any]:
    libraries = getattr(adapter, "_teacher_libraries", None)
    return libraries if isinstance(libraries, Mapping) else {}


def _remote_teacher(adapter: Any) -> Any | None:
    transport = getattr(adapter, "_teacher_transport", None)
    if transport is not None:
        return transport
    try:
        teacher = OpenAITeacher()
    except Exception:
        return None
    return teacher if teacher.is_available() else None


def _call_selected_local_tier(teacher: Any, subject: str) -> Any:
    """Call one graph-selected local tier without crossing its legacy fallback.

    ``attach_libraries`` also keeps a compatibility fallback chain for the
    older self-teaching interface.  A selected ``dictionary`` action must not
    silently invoke Wikipedia through that chain: its miss is graph evidence
    and the instruction seed decides whether to mint the next tier.  A shallow
    copy preserves the teacher's shared on-disk indexes while safely clearing
    only the compatibility link for this one I/O call.
    """
    fallback = getattr(teacher, "fallback", None)
    selected_teacher = teacher
    if fallback is not None:
        try:
            selected_teacher = copy(teacher)
            selected_teacher.fallback = None
        except Exception:
            # It is safer to report this exact tier unavailable than to let it
            # cross a graph-governed escalation boundary.
            return None
    return selected_teacher(subject)


def _resolve_tier(adapter: Any, tier: str, local_subject: str,
                  structured_question: TeacherQuestion) -> dict[str, Any]:
    """Capability dispatch only; the tier was selected by graph data."""
    try:
        if tier in _LOCAL_TIERS:
            teacher = _libraries(adapter).get(tier)
            payload = _call_selected_local_tier(teacher, local_subject) if callable(teacher) else None
            return _local_evidence(tier, payload)
        if tier == "llm":
            teacher = _remote_teacher(adapter)
            if teacher is None:
                return _unavailable_evidence(tier)
            evidence = teacher.ask(structured_question)
            if not isinstance(evidence, TeacherEvidence):
                return _unavailable_evidence(tier)
            return {
                "verdict": evidence.verdict,
                "semantic_differences": evidence.semantic_differences,
                "candidate_concepts": evidence.candidate_concepts,
                "candidate_relations": evidence.candidate_relations,
                "candidate_frames": evidence.candidate_frames,
                "candidate_constructions": evidence.candidate_constructions,
                "lexical_categories": (),
                "missing_assumptions": evidence.missing_assumptions,
                "clarification_propositions": evidence.clarification_propositions,
                "evidence": evidence.evidence,
            }
    except Exception:
        # Do not serialize exception text: it can contain provider internals.
        return _unavailable_evidence(tier)
    return _unavailable_evidence(tier)


def _resolve_shadow(adapter: Any, attrs: Mapping[str, Any]) \
        -> ShadowInterpretationEvidence | None:
    teacher = _remote_teacher(adapter)
    if teacher is None:
        return None
    question = ShadowInterpretationQuestion(
        utterance=str(attrs.get("instruction_context") or ""),
        local_interpretation={
            "speech_act": str(attrs.get("local_speech_act") or ""),
            "predicate": str(attrs.get("question_predicate") or ""),
            "content": str(attrs.get("question_content") or ""),
            "dispatch_path": str(attrs.get("local_dispatch_path") or ""),
            "intent": str(attrs.get("local_intent") or ""),
            "topic": str(attrs.get("local_topic") or ""),
        },
        context_projection={"origin": str(attrs.get("origin") or "agent")},
    )
    try:
        result = teacher.interpret(question)
    except Exception:
        return None
    return result if isinstance(result, ShadowInterpretationEvidence) else None


def scan_and_teach(adapter: Any) -> int:
    """Serve graph-selected teacher requests and attach evidence nodes.

    The daemon owns HostActionRequest/HostActionReceipt state. This function
    owns only TeacherRequest status and its ``has_evidence`` graph product.
    """
    selected = _selected_teacher_requests(adapter)
    if not selected:
        return 0
    completed = 0
    for request in list(adapter.s.nodes("TeacherRequest")):
        if request not in selected or not _has_node(adapter, request):
            continue
        request_attrs = _attrs(adapter, request)
        if request_attrs.get("status") != "requested":
            continue
        tier = str(request_attrs.get("teacher_tier") or "")
        if tier == "llm" and request_attrs.get("question_kind") == "shadow_request_interpretation":
            shadow = _resolve_shadow(adapter, request_attrs)
            if shadow is None:
                adapter.inner.set_attr(request, "status", "unavailable")
                completed += 1
                continue
            evidence = adapter.s.add_node(
                "TeacherEvidence", _shadow_evidence_attrs(tier, request_attrs, shadow))
            adapter.inner.add_edge_unchecked(request, "has_evidence", evidence)
            _materialize_shadow_evidence(adapter, evidence, shadow)
            adapter.inner.set_attr(request, "status", "completed")
            completed += 1
            continue
        local_subject, structured_question = _questions_from_request(request_attrs)
        result = _resolve_tier(adapter, tier, local_subject, structured_question)
        evidence = adapter.s.add_node("TeacherEvidence", _evidence_attrs(tier, request_attrs, result))
        adapter.inner.add_edge_unchecked(request, "has_evidence", evidence)
        _materialize_candidates(adapter, evidence, tier, result)
        adapter.inner.set_attr(request, "status", "completed" if result["verdict"] != "unavailable" else "unavailable")
        completed += 1
    return completed


__all__ = ["scan_and_teach"]
