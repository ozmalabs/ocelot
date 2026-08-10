"""Focused boundary tests for the Terra evidence-only teacher transport."""
from __future__ import annotations

import json

import pytest

from domains.openai_teacher import (
    MODEL,
    OpenAITeacher,
    ShadowInterpretationEvidence,
    TeacherEvidence,
    TeacherSchemaError,
    load_openai_api_key,
)


def _lesson(**changes):
    value = {
        "verdict": "corrected",
        "semantic_differences": ["target differs"],
        "candidate_concepts": [{"name": "target", "definition": "a proposed target"}],
        "candidate_relations": [{"subject": "goal", "predicate": "targets", "object": "target"}],
        "candidate_frames": [{"name": "instruction", "slots": ["goal", "target"]}],
        "candidate_constructions": [{"name": "imperative", "pattern": "verb object"}],
        "missing_assumptions": [],
        "clarification_propositions": [],
        "evidence": ["SENTINEL_MODEL_PROSE"],
    }
    value.update(changes)
    return value


class _Response:
    def __init__(self, lesson, *, status=None):
        self.lesson = lesson
        self.status = status

    def raise_for_status(self):
        return None

    def json(self):
        payload = {"output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps(self.lesson)}
        ]}]}
        if self.status is not None:
            payload["status"] = self.status
        return payload


class _Session:
    def __init__(self, lesson, *, status=None):
        self.lesson = lesson
        self.status = status
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return _Response(self.lesson, status=self.status)


def _question():
    return {"instruction": "move the red block", "candidate_interpretation": {"goal": "move"},
            "context_projection": {"objects": ["red block"]}}


def _shadow():
    return {
        "verdict": "corrected",
        "speech_act": "question",
        "predicate": "operate",
        "content": "different body plans",
        "target_scope": "self_graph",
        "answer_mode": "graph_state_description",
        "requested_relations": ["can_operate", "adapts_to"],
        "disagreement_dimensions": ["target_scope", "answer_mode"],
        "ambiguities": [],
        "evidence_spans": ["your capabilities", "different body plans"],
    }


def test_terra_request_is_stateless_structured_and_secret_free():
    secret = "sk-test-secret-must-not-leak"
    session = _Session(_lesson())
    evidence = OpenAITeacher(api_key=secret, session=session).ask(_question())

    assert isinstance(evidence, TeacherEvidence)
    assert evidence.evidence == ("SENTINEL_MODEL_PROSE",)
    _, request = session.calls[0]
    payload = request["json"]
    assert payload["model"] == MODEL == "gpt-5.6-terra"
    assert payload["store"] is False
    assert payload["reasoning"] == {"effort": "medium"}
    assert "previous_response_id" not in payload
    assert payload["text"]["format"]["type"] == "json_schema"
    assert payload["text"]["format"]["strict"] is True
    assert secret not in json.dumps(payload)
    assert request["headers"]["Authorization"] == f"Bearer {secret}"


def test_schema_rejects_answer_or_other_uncontracted_model_fields():
    with pytest.raises(TeacherSchemaError):
        TeacherEvidence.from_mapping(_lesson(answer="do not render me"))
    with pytest.raises(TeacherSchemaError):
        TeacherEvidence.from_mapping(_lesson(candidate_frames=[{"name": "x", "slots": [], "extra": "bad"}]))


def test_interpretation_shadow_is_structured_evidence_not_an_answer():
    session = _Session(_shadow())
    evidence = OpenAITeacher(api_key="not-a-real-key", session=session).interpret({
        "utterance": "What are your capabilities to operate different body plans?",
        "local_interpretation": {"dispatch_path": "wordplay", "topic": "plans"},
        "context_projection": {"speaker": "interlocutor"},
    })

    assert isinstance(evidence, ShadowInterpretationEvidence)
    assert evidence.target_scope == "self_graph"
    assert evidence.disagreement_dimensions == ("target_scope", "answer_mode")
    payload = session.calls[0][1]["json"]
    assert payload["model"] == "gpt-5.6-terra" and payload["store"] is False
    assert payload["text"]["format"]["name"] == "shadow_interpretation"
    assert "answer" not in payload["text"]["format"]["schema"]["properties"]


def test_no_llm_switch_rejects_terra_before_any_transport_is_created(monkeypatch):
    monkeypatch.setenv("OZMA_NO_LLM", "1")
    with pytest.raises(RuntimeError, match="OZMA_NO_LLM"):
        OpenAITeacher(api_key="must-not-be-used")


def test_environment_key_precedes_repository_env_and_neither_is_logged(tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("IGNORED=x\nOPENAI_API_KEY=file-secret\n", encoding="utf-8")
    assert load_openai_api_key(environ={"OPENAI_API_KEY": "process-secret"}, env_path=env_file) == "process-secret"
    assert load_openai_api_key(environ={}, env_path=env_file) == "file-secret"
    assert capsys.readouterr().out == ""


def test_model_sentinel_is_evidence_not_a_teaching_payload_or_user_output():
    session = _Session(_lesson())
    teacher = OpenAITeacher(api_key="not-a-real-key", session=session)
    evidence = teacher.ask(_question())
    assert not hasattr(evidence, "answer")
    assert not hasattr(evidence, "learn")
    assert "SENTINEL_MODEL_PROSE" not in repr(evidence.__dict__.keys())
    with pytest.raises(TypeError):
        teacher("SENTINEL_MODEL_PROSE")
    assert len(session.calls) == 1, "the legacy callable self-teacher path cannot dispatch Terra"


def test_incomplete_response_is_not_accepted_as_teacher_evidence():
    session = _Session(_lesson(), status="incomplete")
    teacher = OpenAITeacher(api_key="not-a-real-key", session=session)
    with pytest.raises(RuntimeError, match="not completed"):
        teacher.ask(_question())


def test_libraries_attach_local_chain_before_final_transport(monkeypatch):
    from domains import libraries

    class _Local:
        fallback = None

    local = [_Local(), _Local(), _Local()]
    remote = object()

    class _Agent:
        def set_self_teacher(self, teacher):
            self.self_teacher = teacher

    specs = [
        libraries.LibrarySpec("grammar", lambda: local[0], True, "teacher"),
        libraries.LibrarySpec("dictionary", lambda: local[1], True, "teacher"),
        libraries.LibrarySpec("wiki", lambda: local[2], True, "teacher"),
        libraries.LibrarySpec("llm", lambda: remote, False, "structured_teacher"),
    ]
    monkeypatch.setattr(libraries, "LIBRARIES", specs)
    monkeypatch.delenv("OZMA_NO_LLM", raising=False)
    agent = _Agent()
    report = libraries.attach_libraries(agent, enable_llm=True, log=lambda *_: None)

    assert report["teacher_order"] == ["grammar", "dictionary", "wiki", "llm"]
    assert agent.self_teacher is local[0]
    assert local[0].fallback is local[1]
    assert local[1].fallback is local[2]
    assert local[2].fallback is None, "Terra must not enter payload/HeldAnswer fallback chain"
    assert agent._teacher_libraries["wikipedia"] is local[2]
    assert agent._teacher_transport is remote
    assert not hasattr(agent, "_llm_partner")


def test_wikipedia_attachment_does_not_count_the_entire_title_index(monkeypatch, tmp_path):
    from domains import libraries
    from domains.wiki_library import WikipediaLibrary

    (tmp_path / "title_index.sqlite").touch()
    shards = tmp_path / "enwiki" / "data"
    shards.mkdir(parents=True)
    (shards / "enwiki_namespace_0_0.parquet").touch()
    monkeypatch.setattr(libraries, "WIKI_DATA", tmp_path)
    monkeypatch.setattr(
        WikipediaLibrary, "index_size",
        lambda _self: (_ for _ in ()).throw(
            AssertionError("COUNT(*) is not an availability probe")),
    )

    assert libraries._wiki() is not None
