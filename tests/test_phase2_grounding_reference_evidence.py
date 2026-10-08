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
    "signal,speech_act,expected_status",
    [
        ("Move it there.", "instruction", "unresolved_reference"),
        ("Describe the object behind you.", "instruction", "unresolved"),
        ("What is a blorf?", "question", "unresolved"),
        ("The south gate is open.", "statement", "unresolved"),
    ],
)
def test_false_grounding_requires_referent_evidence_path(
        agent, signal, speech_act, expected_status):
    """Epistemic labels cannot be promoted by a parse or by reply shape.

    These are the Phase 2D violation classes: unresolved reference,
    unavailable world, unknown topic, and contradiction.  With no graph path
    to a supported referent, the communication interpretation remains
    unresolved and carries no grounding evidence path.
    """
    agent.converse(signal, speech_act=speech_act,
                   context={"interaction_mode": "non_turn"})
    attrs = _last_interpretation(agent)
    assert attrs["grounding_status"] == expected_status
    assert attrs["grounding_evidence_path"] == ""


def test_selected_relation_is_preserved_without_claiming_world_grounding(agent):
    """Keep typed parse roles available to graph cognition as unverified input."""
    agent.converse(
        "The monitor reports a fault.", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"})
    attrs = _last_interpretation(agent)

    assert attrs["parsed_relation_schema"] == (
        "communication_relation_projection.v1")
    assert attrs["parsed_relation_status"] == "selected_parse_unverified"
    assert attrs["parsed_subject"] == "monitor"
    assert attrs["parsed_subject_pos"] == "noun"
    assert attrs["parsed_predicate"] == "reports"
    assert attrs["parsed_predicate_pos"] == "verb"
    assert attrs["parsed_object"].rstrip(".") == "fault"
    assert attrs["predicate"] == "reports"
    assert attrs["object"].rstrip(".") == "fault"
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    event = agent.s.node(inbound)["attrs"]["discourse_event_id"]
    assert list(agent.inner.neighbours(event, "represents_message")) == [inbound]
    assert list(agent.inner.neighbours(event, "has_interpretation")) == [
        interpretation]
    # A selected linguistic relation is not a world assertion: missing
    # referents keep the epistemic decision unresolved and fail-closed.
    assert attrs["grounding_status"] == "unresolved"
    assert attrs["grounding_evidence_path"] == ""


def test_relation_links_only_the_lexical_concept_not_a_world_instance(agent):
    agent.converse(
        "Can you confirm the route?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"})
    attrs = _last_interpretation(agent)
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    concept_links = agent.inner.neighbours(
        interpretation, "relation_object_concept")

    assert attrs["parsed_relation_status"] == "selected_parse_unverified"
    assert attrs["parsed_object"].rstrip(".") == "route"
    assert len(concept_links) == 1
    assert agent.s.node(concept_links[0])["type"] == "Concept"
    assert agent.s.node(concept_links[0])["attrs"]["name"] == "route"
    assert attrs["grounding_status"] == "unresolved"
    assert attrs["grounding_evidence_path"] == ""


def test_relation_concept_projection_skips_repeated_surface_mentions(agent):
    """A spelling shared by multiple mentions is not an occurrence link."""
    mid = agent.s.add_node("Message", {})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "parsed_relation_schema": "communication_relation_projection.v1",
        "parsed_subject": "bank",
    })
    agent.s.set_attr(mid, "communication_interpretation_id", interpretation)
    for name in ("bank_financial", "bank_river"):
        mention = agent.s.add_node("Mention", {"text": "bank"})
        concept = agent.s.add_node("Concept", {"name": name})
        agent.inner.add_edge_unchecked(mid, "has_mention", mention)
        agent.inner.add_edge_unchecked(mention, "refers_to", concept)

    agent._record_relation_concept_links(mid)

    assert list(agent.inner.neighbours(
        interpretation, "relation_subject_concept")) == []


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


def test_self_gap_meta_route_is_not_vetoed_by_spatial_pp_signal(agent):
    """A graph-selected self-gap faculty is not an external scene query."""
    reply = agent.converse(
        "What gaps do you have in your knowledge?", speech_act="question",
        context={"interaction_mode": "non_turn"})
    attrs = _last_interpretation(agent)
    assert attrs["dispatch_path"] == "table"
    assert attrs["grounding_status"] == "candidate_grounded"
    assert attrs["grounding_evidence_path"].endswith("selected_graph_faculty")
    assert reply != "ERROR: no communicative response could be generated."


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


def test_topic_grounding_evidence_precedes_generic_matching_resolved_query(agent):
    agent._persist_held_answer("sensor status", "nominal")
    agent.s.add_node("ResolvedQuery", {"answer": "sensor status"})
    comp = SimpleNamespace(
        dispatch={"path": "know", "concept": "sensor status",
                  "pre_resolved": "sensor status"},
        table_spec=None,
    )

    status, path = agent._communication_grounding_evidence(comp, "know")

    assert status == "candidate_grounded"
    assert path == (
        "CommunicationInterpretation -> HeldAnswer -> "
        "TopicGroundingEvidence")


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


def test_anaphoric_question_requires_event_scoped_graph_binding(agent):
    """Global focus is insufficient; a same-participant discourse event binds."""
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
    unscoped = comprehend_text(agent, "Why did it close?")
    assert unscoped.dispatch.get("language_evidence", {}).get(
        "resolved_reference_status") is None

    from domains.discourse_state import ensure_discourse_state, record_event
    speaker = agent.attach_chat_world("user")["interlocutor"]
    state = ensure_discourse_state(
        agent, conversation_id="scoped-reference", addressee=agent.agent)
    record_event(
        agent, state, kind="question", speaker=speaker,
        addressee=agent.agent, topic="gate",
        payload={"grounding_status": "candidate_grounded"},
    )
    inbound = agent.receive_utterance("Why did it close?", speaker="user")
    scope = agent._live_discourse_reference_scope(
        inbound, {"conversation_id": "scoped-reference",
                  "interaction_relation": "response"})
    assert scope == {"state_id": state, "speaker_id": speaker,
                     "addressee_id": agent.agent,
                     "interaction_relation": "response"}
    comp = comprehend_text(
        agent, "Why did it close?", discourse_scope=scope)
    assert comp.dispatch["path"] == "know"
    assert comp.dispatch["language_evidence"][
        "resolved_reference_status"] == "supported"
    clarification = comprehend_text(
        agent, "Which valve do you mean?", discourse_scope=scope)
    assert clarification.dispatch.get("language_evidence", {}).get(
        "resolved_reference_status") is None
    standalone = comprehend_text(
        agent, "Will it rain today?",
        discourse_scope={**scope, "interaction_relation": "standalone"})
    assert standalone.dispatch.get("language_evidence", {}).get(
        "resolved_reference_status") is None
    observer = agent.attach_chat_world("observer")["interlocutor"]
    wrong_speaker = comprehend_text(
        agent, "Why did it close?",
        discourse_scope={**scope, "speaker_id": observer})
    wrong_addressee = comprehend_text(
        agent, "Why did it close?",
        discourse_scope={**scope, "addressee_id": observer})
    other_state = ensure_discourse_state(
        agent, conversation_id="other-conversation", addressee=agent.agent)
    other_conversation = comprehend_text(
        agent, "Why did it close?",
        discourse_scope={**scope, "state_id": other_state})
    for unrelated in (wrong_speaker, wrong_addressee, other_conversation):
        assert unrelated.dispatch.get("language_evidence", {}).get(
            "resolved_reference_status") is None
    status, path = agent._communication_grounding_evidence(
        comp, comp.dispatch["path"])
    assert status == "candidate_grounded"
    assert path.endswith("(same speaker/addressee scope)")

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


def test_definite_nominal_correction_requires_matching_scoped_action_head(agent):
    """The parser supplies a cue; only the native rule resolves it in scope."""
    from domains.comprehend_text import comprehend_text
    from domains.discourse_state import ensure_discourse_state, record_event

    speaker = agent.attach_chat_world("user")["interlocutor"]
    correction = comprehend_text(
        agent, "No, the gate is closed.")
    language_evidence = correction.dispatch["language_evidence"]
    assert language_evidence["discourse_relation"] == "correction"
    assert language_evidence["definite_nominal_reference"] == 1.0
    assert language_evidence["referential_head"] == "gate"
    assert language_evidence.get("resolved_reference_status") is None
    status, path = agent._communication_grounding_evidence(
        correction, correction.dispatch["path"])
    assert status != "candidate_grounded"
    assert path == ""

    # Indefinite and mismatched nominals are only parse facts; they do not
    # receive the definite-reference cue for the native rule.
    indefinite = comprehend_text(
        agent, "No, a gate is closed.")
    assert indefinite.dispatch.get("language_evidence", {}).get(
        "definite_nominal_reference") is None
    mismatch = comprehend_text(
        agent, "No, the valve is closed.")
    mismatch_evidence = mismatch.dispatch["language_evidence"]
    assert mismatch_evidence.get("definite_nominal_reference") == 1.0
    assert mismatch_evidence.get("referential_head") == "valve"
    assert mismatch_evidence.get("resolved_reference_status") is None

    def native_case(name, *, prior_head="gate", prior_status="candidate_grounded",
                    prior_speaker=speaker, current_speaker=speaker,
                    current_addressee=None, relation="response",
                    current_head="gate", reverse_order=False,
                    intermediate=False):
        state = ensure_discourse_state(
            agent, conversation_id=name, addressee=agent.agent)

        def add_prior():
            event = record_event(
                agent, state, kind="instruction", speaker=prior_speaker,
                addressee=agent.agent, topic="north " + prior_head,
                interaction_mode="turn_compatible",
                payload={"grounding_status": prior_status})
            prior_i = agent.s.add_node("CommunicationInterpretation", {
                "schema": "communication_interpretation.v1",
                "grounding_status": prior_status,
                "language_action_target_head": prior_head,
            })
            agent.inner.add_edge_unchecked(
                event, "has_interpretation", prior_i, {})

        if reverse_order:
            current = add_current(state, current_speaker, current_addressee,
                                  relation, current_head)
            add_prior()
            return current
        add_prior()
        if intermediate:
            record_event(
                agent, state, kind="statement", speaker=speaker,
                addressee=agent.agent, interaction_mode="non_turn",
                payload={"grounding_status": "unresolved"})
        return add_current(state, current_speaker, current_addressee,
                           relation, current_head)

    def add_current(state, current_speaker, current_addressee, relation, head):
        addressee = agent.agent if current_addressee is None else current_addressee
        event = record_event(
            agent, state, kind="statement", speaker=current_speaker,
            addressee=addressee, interaction_mode="turn_compatible",
            payload={"interaction_relation": relation,
                     "grounding_status": "unresolved"})
        current = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "evidence_schema": "communication_evidence.v1",
            "language_definite_nominal_reference": 1.0,
            "language_discourse_relation": "correction",
            "language_referential_head": head,
            "interaction_relation": relation,
            "parsed_subject_pos": "noun",
            "grounding_status": "unresolved",
            "grounding_evidence_path": "",
        })
        agent.inner.add_edge_unchecked(event, "has_interpretation", current, {})
        agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation",
                                       current, {})
        return current

    positive = native_case("nominal-positive", intermediate=True)
    mismatch_i = native_case("nominal-mismatch", prior_head="valve")
    wrong_speaker_i = native_case(
        "nominal-wrong-speaker", prior_speaker=agent.attach_chat_world(
            "other-user")["interlocutor"])
    wrong_addressee_i = native_case(
        "nominal-wrong-addressee", current_addressee=agent.attach_chat_world(
            "other-agent")["interlocutor"])
    ungrounded_i = native_case(
        "nominal-ungrounded", prior_status="unresolved")
    standalone_i = native_case("nominal-standalone", relation="standalone")
    future_only_i = native_case("nominal-future-only", reverse_order=True)

    agent.inner.run_rules(20_000)
    assert agent.s.node(positive)["attrs"]["grounding_status"] == (
        "candidate_grounded")
    assert "matching action-target head" in agent.s.node(positive)[
        "attrs"]["grounding_evidence_path"]
    for unsupported in (mismatch_i, wrong_speaker_i, wrong_addressee_i,
                        ungrounded_i, standalone_i, future_only_i):
        attrs = agent.s.node(unsupported)["attrs"]
        assert attrs["grounding_status"] == "unresolved"
        assert attrs["grounding_evidence_path"] == ""


def test_preparse_reference_scope_does_not_create_discourse_state(agent):
    inbound = agent.receive_utterance("What is here?", speaker="user")
    assert list(agent.s.nodes("DiscourseState")) == []

    scope = agent._live_discourse_reference_scope(
        inbound, {"conversation_id": "first-event"})

    assert scope is None
    assert list(agent.s.nodes("DiscourseState")) == []


def test_anaphoric_question_without_graph_binding_stays_unresolved(agent):
    agent.converse("Why did it close?", speech_act="question",
                   context={"interaction_mode": "non_turn"})
    attrs = _last_interpretation(agent)
    status = attrs["grounding_status"]
    path = attrs["grounding_evidence_path"]
    assert status == "unresolved_reference"
    assert path == ""


def test_typed_unresolved_reference_is_not_a_generic_gap(agent):
    from domains.comprehend_text import comprehend_text
    comp = comprehend_text(agent, "Move it now.", kind="instruction")
    status, path = agent._communication_grounding_evidence(
        comp, comp.dispatch["path"])
    assert comp.dispatch["language_evidence"]["anaphoric_reference"] is True
    assert status == "unresolved_reference"
    assert path == ""


def test_untyped_action_gap_remains_generic_unresolved(agent):
    from domains.comprehend_text import comprehend_text
    comp = comprehend_text(
        agent, "Look left then quorplezap the door.", kind="instruction")
    status, path = agent._communication_grounding_evidence(
        comp, comp.dispatch["path"])
    assert comp.dispatch["language_evidence"]["sequence_status"] == (
        "unresolved_action_head")
    assert status == "unresolved"
    assert path == ""


def test_continuing_information_request_with_unresolved_deixis_repairs(agent):
    agent.converse(
        "Describe the place over there.", speech_act="instruction",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "continuation"},
    )
    attrs = _last_interpretation(agent)
    assert attrs["grounding_status"] == "unresolved_reference"
    assert attrs["cognitive_disposition"] == "repair"
    assert attrs["arbitration_basis"] == (
        "unresolved_continuing_information_referent")


def test_action_anaphor_candidate_without_event_bound_resolution_repairs(agent):
    from domains.discourse_state import ensure_discourse_state, record_event

    speaker = agent.attach_chat_world("user")["interlocutor"]
    state = ensure_discourse_state(
        agent, conversation_id="anaphoric-action", addressee=agent.agent)
    record_event(
        agent, state, kind="question", speaker=speaker,
        addressee=agent.agent, topic="gate",
        payload={"grounding_status": "candidate_grounded"},
    )
    agent.converse(
        "Move it now.", speech_act="instruction", speaker="user",
        context={"conversation_id": "anaphoric-action",
                 "interaction_mode": "turn_compatible",
                 "interaction_relation": "continuation"},
    )
    attrs = _last_interpretation(agent)
    assert attrs["grounding_status"] == "unresolved_reference"
    assert attrs["grounding_evidence_path"] == ""
    assert attrs["cognitive_disposition"] == "repair"


def test_fragment_actor_pronoun_is_not_mislabeled_as_unresolved_anaphor(agent):
    agent.converse(
        "Can you tell me—", speech_act="instruction",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"},
    )
    attrs = _last_interpretation(agent)
    assert attrs["literal_form"] == "fragment"
    assert attrs["grounding_status"] != "unresolved_reference"
    assert attrs["cognitive_disposition"] == "defer"


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
    "signal,speech_act,expected_path,expected_force,expected_grounding",
    [
        ("What is beyond the wall?", "question", "frontier", "repair_or_defer", "unresolved"),
        ("Which valve do you mean?", "question", "frontier", "repair_or_defer", "unresolved"),
        ("Reset that device.", "instruction", "instruction", "action_request", "unresolved_reference"),
    ],
)
def test_phase2_regressions_keep_missing_world_and_referents_unresolved(
        agent, signal, speech_act, expected_path, expected_force,
        expected_grounding):
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
    assert attrs["grounding_status"] == expected_grounding
    assert attrs["grounding_evidence_path"] == ""
