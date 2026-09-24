"""Bounded Phase 2 grounding/reference/epistemic evidence checks."""
from __future__ import annotations

import json
import os
import sys
from types import SimpleNamespace
from urllib.parse import unquote

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from domains.fetch_dispatch import mint_search_request, scan_and_search
from domains import topic_grounding as tg
from domains import reference_resolution as rr
from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase2_grounding_measurement import (
    grounding_cognitive_category,
    measure_grounding,
)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _http(title, extract, *, summary_type=None):
    def get(url, timeout=8):
        if "action=opensearch" in url:
            q = unquote(url.split("search=", 1)[1]).lower()
            body = json.dumps([q, [title], [""], [""]])
            return {"status": 200, "text": body, "url": url}
        if "/page/summary/" in url:
            data = {"title": title, "extract": extract}
            if summary_type:
                data["type"] = summary_type
            return {"status": 200, "text": json.dumps(data), "url": url}
        raise AssertionError(f"unexpected URL: {url}")
    return get


def test_reference_resolution_records_supported_and_unknown_evidence(agent):
    class World:
        def __init__(self, substrate):
            self.s = substrate
            self._concept_nodes = {}

        def _get_or_create_concept(self, name):
            if name not in self._concept_nodes:
                self._concept_nodes[name] = self.s.add_node(
                    "Concept", {"name": name, "category": "object"})
            return self._concept_nodes[name]

    store = rr.DiscourseStore(agent.s, World(agent.s))
    store.update_from_frame({"agent": "cup", "patient": "mat"})
    store.update_centering({"cup": "agent", "mat": "patient"})

    bound = store.reference_resolution_procedure("it", 1)
    assert bound["resolved"] is True
    assert bound["epistemic_status"] == "supported"
    assert bound["evidence_path"]

    unknown = store.reference_resolution_procedure("they", 2)
    assert unknown["resolved"] is False
    assert unknown["epistemic_status"] == "unknown"
    assert unknown["evidence_path"]

    records = [agent.s.node(n)["attrs"] for n in agent.s.nodes(
        "ReferenceResolutionEvidence")]
    assert {r["epistemic_status"] for r in records} == {"supported", "unknown"}
    assert all(r.get("evidence_path") for r in records)


def test_retrieval_success_records_candidate_provenance_and_evidence(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    req = mint_search_request(agent, "photosynthesis")
    touched = scan_and_search(
        agent,
        http_get=_http("Photosynthesis", "Photosynthesis converts light into energy."),
        timeout=5,
    )
    assert touched == [req]
    attrs = agent.s.node(req)["attrs"]
    assert attrs["status"] == "done"
    assert attrs["epistemic_status"] == "supported"
    assert attrs["evidence_path"]

    candidates = list(agent.inner.neighbours(req, "has_candidate"))
    assert candidates
    candidate = agent.s.node(candidates[0])["attrs"]
    assert candidate["provenance_source"] == "wikipedia"
    assert candidate["provenance_query"] == "photosynthesis"
    assert candidate["evidence_path"]

    evidence = list(agent.s.nodes("RetrievalEvidence"))
    assert evidence
    assert agent.s.node(evidence[0])["attrs"]["epistemic_status"] == "supported"
    assert agent.s.node(evidence[0])["attrs"]["evidence_path"]


@pytest.mark.parametrize(
    "getter,expected",
    [
        (lambda: (lambda url, timeout=8: {
            "status": 200,
            "text": json.dumps(["unknown", [], [], []]) if "opensearch" in url
            else "{}",
            "url": url,
        }), "unknown"),
        (lambda: (lambda url, timeout=8: (_ for _ in ()).throw(
            OSError("network unavailable"))), "search_failed"),
    ],
)
def test_retrieval_failure_preserves_epistemic_distinction(agent, monkeypatch,
                                                            getter, expected):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    req = mint_search_request(agent, "unavailable topic")
    scan_and_search(agent, http_get=getter(), timeout=5)
    attrs = agent.s.node(req)["attrs"]
    assert attrs["status"] == "failed"
    assert attrs["epistemic_status"] == expected
    assert attrs["evidence_path"]


def test_retrieval_contradiction_is_not_committed(agent, monkeypatch):
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    req = mint_search_request(agent, "pluto is a planet")
    scan_and_search(
        agent,
        http_get=_http("Pluto", "The query is contradicted by the source.",
                        summary_type="contradiction"),
        timeout=5,
    )
    attrs = agent.s.node(req)["attrs"]
    assert attrs["status"] == "failed"
    assert attrs["epistemic_status"] == "contradicted"
    assert not list(agent.s.nodes("RetrievalEvidence"))


def test_retrieval_candidate_selection_requires_multi_referent_coverage(agent,
                                                                         monkeypatch):
    """Retrieval may propose candidates, but native selection requires evidence
    covering every referent in a compound request."""
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    req = mint_search_request(
        agent, "photosynthesis and carbon fixation",
        referents=["photosynthesis", "carbon fixation"],
    )
    scan_and_search(
        agent,
        http_get=_http(
            "Photosynthesis and carbon fixation",
            "Photosynthesis and carbon fixation are related biological processes."),
        timeout=5,
    )
    attrs = agent.s.node(req)["attrs"]
    assert attrs["status"] == "done"
    candidates = list(agent.inner.neighbours(req, "has_candidate"))
    assert candidates
    candidate = agent.s.node(candidates[0])["attrs"]
    assert candidate["referent_coverage"] == [True, True]
    assert candidate["referent_coverage_complete"] == 1.0
    assert candidate["communication_event_claimed"] == 0.0
    assert not list(agent.s.nodes("CommunicationInterpretation"))
    assert not list(agent.s.nodes("Message"))


@pytest.mark.parametrize("referent_status", ["unknown", "unresolved"])
def test_unresolved_coreference_cannot_be_promoted_by_retrieval(agent, monkeypatch,
                                                                 referent_status):
    """An unresolved reference remains unknown; retrieval cannot turn it into
    a supported topic or claim a communication event."""
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)
    req = mint_search_request(
        agent, "it", referents=["it"], referent_status=referent_status)
    scan_and_search(
        agent,
        http_get=_http("It", "A source happened to contain the word it."),
        timeout=5,
    )
    attrs = agent.s.node(req)["attrs"]
    assert attrs["status"] == "failed"
    assert attrs["epistemic_status"] == "unknown"
    assert attrs["referent_status"] == referent_status
    assert not list(agent.s.nodes("RetrievalEvidence"))
    assert not list(agent.s.nodes("CommunicationInterpretation"))


def test_coreference_resolution_can_supply_retrieval_referent_evidence(agent,
                                                                        monkeypatch):
    """A resolved discourse referent can be handed to retrieval explicitly;
    the retrieval seam consumes the evidence but does not perform resolution."""
    monkeypatch.setattr(tg, "_wiki_teacher", lambda _a: None)

    class World:
        def __init__(self, substrate):
            self.s = substrate
            self._concept_nodes = {}

        def _get_or_create_concept(self, name):
            if name not in self._concept_nodes:
                self._concept_nodes[name] = self.s.add_node(
                    "Concept", {"name": name, "category": "object"})
            return self._concept_nodes[name]

    store = rr.DiscourseStore(agent.s, World(agent.s))
    store.update_from_frame({"agent": "cup", "patient": "mat"})
    store.update_centering({"cup": "agent", "mat": "patient"})
    resolved = store.reference_resolution_procedure("it", 1)
    assert resolved["resolved"] is True
    req = mint_search_request(
        agent, resolved["concept"], referents=[resolved["concept"]],
        referent_status=resolved["epistemic_status"])
    scan_and_search(
        agent,
        http_get=_http(resolved["concept"],
                       f"The object called {resolved['concept']} is described here."),
        timeout=5,
    )
    assert agent.s.node(req)["attrs"]["status"] == "done"
    evidence = list(agent.s.nodes("RetrievalEvidence"))
    assert evidence
    assert agent.s.node(evidence[0])["attrs"]["referent_status"] == "supported"


def _last_interpretation(agent):
    # The Rust-facing numeric turn id is a scalar provenance value, not a
    # substrate NodeID.  Use the graph-resident inbound node for readback.
    mid = agent._last_turn_inbound
    attrs = agent.s.node(mid)["attrs"]
    iid = attrs["communication_interpretation_id"]
    return agent.s.node(iid)["attrs"]


@pytest.mark.parametrize(
    "signal,speech_act",
    [
        ("Move it there.", "instruction"),
        ("Describe the object behind you.", "instruction"),
        ("What is a blorf?", "question"),
        ("The south gate is open.", "statement"),
    ],
)
def test_false_grounding_requires_referent_evidence_path(agent, signal, speech_act):
    """Epistemic labels cannot be promoted by a parse or by reply shape.

    These are the Phase 2D violation classes: unresolved reference,
    unavailable world, unknown topic, and contradiction.  With no graph path
    to a supported referent, the communication interpretation remains
    unresolved and carries no grounding evidence path.
    """
    agent.converse(signal, speech_act=speech_act,
                   context={"interaction_mode": "non_turn"})
    attrs = _last_interpretation(agent)
    assert attrs["grounding_status"] == "unresolved"
    assert attrs["grounding_evidence_path"] == ""


def test_legitimate_held_answer_retains_grounding_evidence(agent):
    """A graph-resident held answer remains a supported referent route."""
    agent._persist_held_answer(
        "photosynthesis", "Photosynthesis converts light into energy.")
    reply = agent.converse("What is photosynthesis?", speech_act="question",
                           context={"interaction_mode": "turn_compatible"})
    attrs = _last_interpretation(agent)
    assert reply
    assert attrs["grounding_status"] == "candidate_grounded"
    assert "HeldAnswer" in attrs["grounding_evidence_path"]


def test_distance_question_without_scene_cannot_use_concept_referent(agent):
    """A lexical valley Concept is not evidence for an unobserved distance."""
    agent.converse("How far is the valley?", speech_act="question",
                   context={"interaction_mode": "non_turn"})
    attrs = _last_interpretation(agent)
    assert attrs["grounding_status"] == "unresolved"
    assert attrs["grounding_evidence_path"] == ""


def test_graph_faculty_table_route_retains_grounding_evidence(agent):
    """A graph-backed self/faculty table route is safe recall.

    The answer is selected by the held meta faculty; it is not promoted from
    the generated inventory text.  This is the narrow table case that the
    ordinary HeldAnswer topic check cannot see.
    """
    reply = agent.converse(
        "How are you organised?", speech_act="question",
        context={"interaction_mode": "non_turn"})
    attrs = _last_interpretation(agent)
    assert reply
    assert attrs["dispatch_path"] == "table"
    assert attrs["intent"] == "table:meta"
    assert attrs["grounding_status"] == "candidate_grounded"
    assert attrs["grounding_evidence_path"].endswith("selected_graph_faculty")


def test_resolved_reference_route_is_graph_evidence_not_reply_shape(agent):
    """A resolver-supplied binding can promote a world question safely."""
    agent.s.add_node("ResolvedQuery", {
        "key": "thing:known(?,?)",
        "answer": "cup",
    })
    comp = SimpleNamespace(
        dispatch={"path": "know", "pre_resolved": "cup"},
        table_spec=None,
    )
    status, path = agent._communication_grounding_evidence(comp, "know")
    assert status == "candidate_grounded"
    assert path.endswith("resolved_referent")


def test_taught_focus_recall_uses_graph_readback(agent):
    """A taught focus is safe recall only when its graph record is present."""
    from domains.construction_grammar import learn_frontier_answer

    learn_frontier_answer(
        agent.s,
        "What is the status of the sensor?",
        "The sensor is nominal.",
    )
    reply = agent.converse(
        "What is the status of the sensor?", speech_act="question",
        context={"interaction_mode": "non_turn"},
    )
    attrs = _last_interpretation(agent)
    assert reply
    assert attrs["grounding_status"] == "candidate_grounded"
    assert attrs["grounding_evidence_path"].endswith(
        "ResolvedQuery -> resolved_referent")


def test_resolved_focus_without_graph_record_stays_unresolved(agent):
    """A derived pre-resolution value cannot promote itself."""
    comp = SimpleNamespace(
        dispatch={"path": "know", "pre_resolved": "only a return value"},
        table_spec=None,
    )
    status, path = agent._communication_grounding_evidence(comp, "know")
    assert status == "unresolved"
    assert path == ""


def test_resolved_discourse_reference_family_exact_counts(agent):
    """The bounded recall family reports one supported case, no errors."""
    corpus = load_corpus()
    target = next(e for e in corpus["events"] if e["id"] == "question_followup")
    graph_path = (
        "CommunicationInterpretation -> ResolvedQuery -> resolved_referent")
    observations = [{
        "grounding_status": target["grounding_status"] if e is target
        else e["grounding_status"],
        "grounding_evidence_path": graph_path if e is target else "",
        "reply_present": False,
    } for e in corpus["events"]]
    report = measure_grounding(corpus, observations)
    family = report["cognitive_category_analysis"][
        "resolved_discourse_reference"]
    assert family == {
        "support": 1,
        "false_negative": 0,
        "false_positive": 0,
        "runtime_evidence_verified": 1,
    }
    assert report["unrelated_answer_resolution"]["count"] == 0


def test_anaphoric_question_uses_in_focus_graph_binding(agent):
    """A bound discourse topic supplies recall without promoting a pronoun."""
    concept = agent.s.add_node("Concept", {
        "name": "gate", "category": "object",
        "definition": "a barrier controlling passage",
    })
    agent.s.add_node("CurrentTopic", {"name": "gate"})
    referent = agent.s.add_node("DiscourseReferent", {
        "concept": "gate", "category": "object",
        "cognitive_status": "in_focus",
    })
    assert concept is not None and referent is not None

    from domains.comprehend_text import comprehend_text
    comp = comprehend_text(agent, "Why did it close?")
    assert comp.dispatch["path"] == "know"
    status, path = agent._communication_grounding_evidence(
        comp, comp.dispatch["path"])
    assert status == "candidate_grounded"
    assert path.endswith("CurrentTopic.name + DiscourseReferent.concept")

    event = next(e for e in load_corpus()["events"]
                 if e["id"] == "question_followup")
    report = measure_grounding(
        load_corpus(),
        [{
            "grounding_status": (
                status if e["id"] == event["id"] else e["grounding_status"]),
            "grounding_evidence_path": (
                path if e["id"] == event["id"] else ""),
            "reply_present": True,
            "reply": "unrelated surface text",
        } for e in load_corpus()["events"]],
    )
    assert report["cognitive_category_analysis"][
        "resolved_discourse_reference"] == {
            "support": 1, "false_negative": 0,
            "false_positive": 0, "runtime_evidence_verified": 1,
        }
    assert report["unrelated_answer_resolution"]["count"] == 0


def test_anaphoric_question_without_graph_binding_stays_unresolved(agent):
    from domains.comprehend_text import comprehend_text
    comp = comprehend_text(agent, "Why did it close?")
    status, path = agent._communication_grounding_evidence(
        comp, comp.dispatch["path"])
    assert status == "unresolved"
    assert path == ""


def test_substantive_concept_referent_is_measured_as_graph_recall(agent):
    """A selected Concept referent is distinct, runtime graph evidence.

    This covers the action-grounding category without treating a parsed
    object, a reply, or a corpus declaration as evidence.  The seeded concept
    mirrors the path used by the live ``direct_action`` observation.
    """
    concept = agent.s.add_node("Concept", {
        "name": "gate",
        "category": "object",
        "definition": "a barrier controlling passage",
    })
    assert concept is not None
    comp = SimpleNamespace(
        dispatch={
            "path": "instruction",
            "object": "gate",
            "relation": {"object": {"surface": "gate", "role": "object"}},
        },
        gaps=[],
        table_spec=None,
    )
    status, path = agent._communication_grounding_evidence(comp, "instruction")
    assert status == "candidate_grounded"
    assert path.endswith("Concept.referent")

    event = next(e for e in load_corpus()["events"] if e["id"] == "direct_action")
    assert grounding_cognitive_category(
        event,
        {"grounding_status": status, "grounding_evidence_path": path},
    ) == "graph_referent"


def test_topic_question_uses_exact_substantive_concept_referent(agent):
    """A graph-backed topic question gains evidence without reply promotion."""
    concept = agent.s.add_node("Concept", {
        "name": "gate",
        "category": "object",
        "definition": "a barrier controlling passage",
    })
    assert concept is not None
    comp = SimpleNamespace(
        dispatch={"path": "table", "concept": "gate"},
        table_spec=SimpleNamespace(kind="know"),
    )
    status, path = agent._communication_grounding_evidence(comp, "table")
    assert status == "candidate_grounded"
    assert path == "CommunicationInterpretation -> Concept.referent"

    corpus = load_corpus()
    event = next(e for e in corpus["events"]
                 if e["id"] == "question_referent")
    report = measure_grounding(
        corpus,
        [{
            "grounding_status": (
                status if e["id"] == event["id"] else e["grounding_status"]),
            "grounding_evidence_path": (
                path if e["id"] == event["id"] else ""),
            "reply": "unrelated surface text",
            "reply_present": True,
        } for e in corpus["events"]],
    )
    row = next(r for r in report["observations"]
               if r["id"] == "question_referent")
    assert row["cognitive_category"] == "graph_referent"
    assert report["unrelated_answer_resolution"]["count"] == 0
    assert report["per_label"]["referent"]["false_positive"] == 0


@pytest.mark.parametrize(
    "signal,speech_act,expected_path,expected_force",
    [
        ("What is beyond the wall?", "question", "frontier", "repair_or_defer"),
        ("Which valve do you mean?", "question", "frontier", "repair_or_defer"),
        ("Reset that device.", "instruction", "instruction", "action_request"),
    ],
)
def test_phase2_regressions_keep_missing_world_and_referents_unresolved(
        agent, signal, speech_act, expected_path, expected_force):
    """Adapter evidence must survive dispatch and prevent lexical promotion.

    The first case is a spatial dependency without an attached scene, the
    second is a non-reflexive selection repair, and the third is a deictic
    action whose object has no discourse binding.  This checks cognitive
    state, not the generated reply.
    """
    agent.converse(signal, speech_act=speech_act,
                   context={"interaction_mode": "non_turn"})
    attrs = _last_interpretation(agent)
    assert attrs["dispatch_path"] == expected_path
    assert attrs["evidence_force"] == expected_force
    assert attrs["grounding_status"] == "unresolved"
    assert attrs["grounding_evidence_path"] == ""
