"""The graph-selected teacher bridge only produces evidence data."""
from __future__ import annotations

from dataclasses import asdict

from domains.openai_teacher import (
    ShadowInterpretationEvidence,
    ShadowInterpretationQuestion,
    TeacherEvidence,
    TeacherQuestion,
)
from domains.teacher_dispatch import scan_and_teach


class _Graph:
    def __init__(self):
        self.data = {}
        self.next_id = 1

    def add_node(self, node_type, attrs=None):
        node = self.next_id
        self.next_id += 1
        self.data[node] = {"type": node_type, "attrs": dict(attrs or {})}
        return node

    def node(self, node):
        return self.data[node]

    def nodes(self, node_type):
        return [node for node, value in self.data.items() if value["type"] == node_type]


class _Native:
    def __init__(self, graph):
        self.graph = graph
        self.edges = []

    def has_node(self, node):
        return node in self.graph.data

    def add_edge_unchecked(self, source, edge_type, target):
        self.edges.append((source, edge_type, target))

    def set_attr(self, node, key, value):
        self.graph.data[node]["attrs"][key] = value

    def neighbours(self, source, edge_type):
        return [target for src, edge, target in self.edges if src == source and edge == edge_type]


class _Adapter:
    def __init__(self):
        self.s = _Graph()
        self.inner = _Native(self.s)
        self._teacher_libraries = {}


class _LocalTeacher:
    def __init__(self, payload):
        self.payload = payload
        self.questions = []

    def __call__(self, question):
        self.questions.append(question)
        return self.payload


class _MissesIntoFallback(_LocalTeacher):
    def __call__(self, question):
        self.questions.append(question)
        return self.fallback(question) if self.fallback is not None else None


class _RemoteTeacher:
    def __init__(self, evidence):
        self.evidence = evidence
        self.questions = []

    def ask(self, question):
        assert isinstance(question, TeacherQuestion)
        self.questions.append(question)
        return self.evidence


class _UnavailableRemoteTeacher:
    def ask(self, _question):
        raise RuntimeError("transport unavailable")


class _ShadowRemoteTeacher:
    def __init__(self, evidence):
        self.evidence = evidence
        self.questions = []

    def interpret(self, question):
        assert isinstance(question, ShadowInterpretationQuestion)
        self.questions.append(question)
        return self.evidence


def _host(adapter, request, status="requested"):
    return adapter.s.add_node("HostActionRequest", {
        "action": "teacher", "source_type": "TeacherRequest", "source": request, "status": status,
    })


def _request(adapter, tier, *, predicate="calibrate", content="sensor"):
    return adapter.s.add_node("TeacherRequest", {
        "status": "requested", "teacher_tier": tier, "origin": "agent",
        "question_kind": "resolve_instruction_gap", "question_predicate": predicate,
        "question_content": content,
    })


def _evidence_for(adapter, request):
    evidence = [target for source, edge, target in adapter.inner.edges
                if source == request and edge == "has_evidence"]
    assert len(evidence) == 1
    return adapter.s.node(evidence[0])["attrs"]


def test_dispatch_requires_graph_minted_teacher_host_action():
    adapter = _Adapter()
    request = _request(adapter, "dictionary")
    teacher = _LocalTeacher({"learn": [{"phrase": "sensor", "description": "dictionary definition"}]})
    adapter._teacher_libraries["dictionary"] = teacher

    assert scan_and_teach(adapter) == 0
    assert teacher.questions == []
    assert adapter.s.node(request)["attrs"]["status"] == "requested"
    assert adapter.s.nodes("TeacherEvidence") == []


def test_dictionary_tier_writes_structured_evidence_without_copying_answer_or_output():
    adapter = _Adapter()
    request = _request(adapter, "dictionary")
    _host(adapter, request)
    sentinel = "MODEL_OR_LOCAL_PROSE_MUST_NOT_BE_USER_OUTPUT"
    dictionary = _LocalTeacher({
        "answer": sentinel,
        "learn": [{"phrase": "sensor", "description": "dictionary definition"}],
    })
    wiki = _LocalTeacher({"learn": [{"phrase": "sensor", "description": "wrong tier"}]})
    adapter._teacher_libraries.update(dictionary=dictionary, wikipedia=wiki)

    assert scan_and_teach(adapter) == 1
    evidence = _evidence_for(adapter, request)
    assert dictionary.questions == ["sensor"]
    assert wiki.questions == []
    assert evidence["verdict"] == "supported"
    assert evidence["candidate_concepts"] == [{"name": "sensor", "definition": sentinel}]
    concepts = adapter.s.nodes("TeacherConceptCandidate")
    assert len(concepts) == 1
    assert adapter.s.node(concepts[0])["attrs"]["status"] == "proposed"
    assert adapter.s.node(concepts[0])["attrs"]["definition"] == sentinel
    assert (next(node for node, value in adapter.s.data.items() if value["type"] == "TeacherEvidence"),
            "proposes_concept", concepts[0]) in adapter.inner.edges
    assert adapter.s.node(request)["attrs"]["status"] == "completed"
    assert adapter.s.nodes("Message") == []
    assert adapter.s.nodes("HeldAnswer") == []


def test_wikipedia_tier_runs_only_after_its_graph_selected_tier():
    adapter = _Adapter()
    request = _request(adapter, "wikipedia", content="Ada Lovelace")
    _host(adapter, request)
    dictionary = _LocalTeacher({"learn": [{"phrase": "ada", "description": "wrong tier"}]})
    wiki = _LocalTeacher({"learn": [{"phrase": "ada lovelace", "description": "wikipedia article"}]})
    adapter._teacher_libraries.update(dictionary=dictionary, wikipedia=wiki)

    assert scan_and_teach(adapter) == 1
    assert dictionary.questions == []
    assert wiki.questions == ["Ada Lovelace"]
    assert _evidence_for(adapter, request)["teacher_tier"] == "wikipedia"


def test_local_lookup_uses_predicate_only_when_graph_target_is_absent():
    adapter = _Adapter()
    request = _request(adapter, "dictionary", predicate="calibrate", content="")
    _host(adapter, request)
    dictionary = _LocalTeacher({"learn": [{"phrase": "calibrate", "description": "dictionary"}]})
    adapter._teacher_libraries["dictionary"] = dictionary

    assert scan_and_teach(adapter) == 1
    assert dictionary.questions == ["calibrate"]


def test_selected_dictionary_tier_cannot_silently_follow_legacy_wikipedia_fallback():
    adapter = _Adapter()
    request = _request(adapter, "dictionary")
    _host(adapter, request)
    wiki = _LocalTeacher({"learn": [{"phrase": "sensor", "description": "wrong tier"}]})
    dictionary = _MissesIntoFallback(None)
    dictionary.fallback = wiki
    adapter._teacher_libraries.update(dictionary=dictionary, wikipedia=wiki)

    assert scan_and_teach(adapter) == 1
    assert dictionary.questions == ["sensor"]
    assert wiki.questions == [], "the seed, not a Python fallback, governs escalation"
    assert _evidence_for(adapter, request)["verdict"] == "insufficient"


def test_llm_tier_serializes_teacher_question_and_attaches_schema_valid_evidence():
    adapter = _Adapter()
    request = _request(adapter, "llm")
    _host(adapter, request, status="running")  # daemon changes selected work to running before handler call
    remote = _RemoteTeacher(TeacherEvidence(
        verdict="corrected", semantic_differences=("target differs",),
        candidate_concepts=({"name": "sensor", "definition": "instrument"},),
        candidate_relations=(), candidate_frames=(), candidate_constructions=(),
        missing_assumptions=(), clarification_propositions=(), evidence=("remote lesson",),
    ))
    adapter._teacher_transport = remote

    assert scan_and_teach(adapter) == 1
    assert remote.questions and remote.questions[0].candidate_interpretation["predicate"] == "calibrate"
    assert remote.questions[0].instruction == "calibrate sensor"
    evidence = _evidence_for(adapter, request)
    assert evidence["verdict"] == "corrected"
    assert evidence["candidate_concepts"] == [asdict(remote.evidence)["candidate_concepts"][0]]
    assert evidence["evidence_schema"] == "teacher_evidence.v1"
    assert adapter.s.nodes("TeacherConceptCandidate")
    assert adapter.s.node(request)["attrs"]["status"] == "completed"


def test_unavailable_teacher_is_graph_evidence_without_provider_error_or_secret():
    adapter = _Adapter()
    request = _request(adapter, "llm")
    _host(adapter, request)
    adapter._teacher_transport = _UnavailableRemoteTeacher()

    assert scan_and_teach(adapter) == 1
    evidence = _evidence_for(adapter, request)
    assert evidence["verdict"] == "unavailable"
    assert adapter.s.node(request)["attrs"]["status"] == "unavailable"
    assert "OPENAI_API_KEY" not in str(evidence)
    assert adapter.s.nodes("Message") == []
    assert adapter.s.nodes("HeldAnswer") == []


def test_selected_host_action_cannot_consume_an_unrelated_pending_teacher_request():
    adapter = _Adapter()
    selected = _request(adapter, "dictionary", content="selected term")
    unrelated = _request(adapter, "wikipedia", content="unrelated term")
    _host(adapter, selected)
    dictionary = _LocalTeacher({"learn": [{"phrase": "selected term", "description": "dictionary"}]})
    wikipedia = _LocalTeacher({"learn": [{"phrase": "unrelated term", "description": "wiki"}]})
    adapter._teacher_libraries.update(dictionary=dictionary, wikipedia=wikipedia)

    assert scan_and_teach(adapter) == 1
    assert adapter.s.node(selected)["attrs"]["status"] == "completed"
    assert adapter.s.node(unrelated)["attrs"]["status"] == "requested"
    assert dictionary.questions == ["selected term"]
    assert wikipedia.questions == []
    assert len(adapter.s.nodes("TeacherEvidence")) == 1


def test_llm_shadow_materializes_alternate_parse_without_a_message_or_adoption():
    adapter = _Adapter()
    request = adapter.s.add_node("TeacherRequest", {
        "status": "requested", "teacher_tier": "llm", "origin": "agent",
        "question_kind": "shadow_request_interpretation",
        "instruction_context": "What are your capabilities to operate different body plans?",
        "question_predicate": "operate", "question_content": "plans",
        "local_speech_act": "question", "local_dispatch_path": "wordplay",
        "local_intent": "wordplay:operate", "local_topic": "plans",
    })
    _host(adapter, request)
    remote = _ShadowRemoteTeacher(ShadowInterpretationEvidence(
        verdict="corrected", speech_act="question", predicate="operate",
        content="different body plans", target_scope="self_graph",
        answer_mode="graph_state_description",
        requested_relations=("can_operate", "adapts_to"),
        disagreement_dimensions=("target_scope", "answer_mode"),
        ambiguities=(), evidence_spans=("your capabilities",),
    ))
    adapter._teacher_transport = remote

    assert scan_and_teach(adapter) == 1
    assert remote.questions[0].local_interpretation["dispatch_path"] == "wordplay"
    evidence_id = adapter.s.nodes("TeacherEvidence")[0]
    evidence = adapter.s.node(evidence_id)["attrs"]
    assert evidence["evidence_schema"] == "interpretation_shadow.v1"
    assert evidence["target_scope"] == "self_graph"
    differences = adapter.s.nodes("InterpretationDifference")
    assert {adapter.s.node(n)["attrs"]["dimension"] for n in differences} == {
        "target_scope", "answer_mode"}
    relations = adapter.s.nodes("RequestedRelationCandidate")
    assert {adapter.s.node(n)["attrs"]["relation"] for n in relations} == {
        "can_operate", "adapts_to"}
    assert adapter.s.nodes("Message") == [] and adapter.s.nodes("HeldAnswer") == []
