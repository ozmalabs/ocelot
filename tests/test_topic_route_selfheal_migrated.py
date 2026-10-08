"""The 'moon bug' fix + self-healing knowledge gaps (graph-native).

Before: "What do you know about the moon?" -> "I am Jabberwock." The Python
front end (comprehend_text) sees the self-cue 'you' and routes the WHOLE turn
to a self/meta faculty, discarding the real topic.

After: the adapter writes the external object/oblique nominal onto the Message
(comp_topic + topic_pending marker -- NEVER the self-word subject), and the
graph rule route_question_to_topic (seeds/conversation_topic_route.json) DECIDES
the turn is about that external topic and mints Goal{kind:answer_topic}. The
adapter renders the answer from that decision via answer_about, and SELF-HEALS a
miss by grounding the topic through the agent's OWN self-teacher chain
(ground_unknowns) and re-answering -- the agent fixing its own knowledge gap.

A genuinely self-referential question ("What are you?") writes no comp_topic, so
the rule never fires and the self/meta path is byte-unchanged.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _answer_topic_goals(a, concept=None):
    out = []
    for g in a.inner.neighbours(a.agent, "has_goal"):
        if not a.inner.has_node(g):
            continue
        ga = a.s.node(g)["attrs"]
        if ga.get("kind") == "answer_topic" and (concept is None or ga.get("concept") == concept):
            out.append(g)
    return out


def test_reflexive_topic_question_routes_to_topic_not_self(agent):
    # No teacher attached -> the topic can't be grounded, but the ROUTING must
    # still be fixed: the turn is about 'moon', not the agent's identity.
    reply = agent.converse("What do you know about the moon?", speech_act="question")
    assert _answer_topic_goals(agent, "moon"), (
        "the graph must route the reflexive question to its external topic "
        "(mint Goal{kind:answer_topic, concept:'moon'}), not to a self faculty")
    assert "moon" in reply.lower(), "the honest reply must be ABOUT the topic"
    assert "i am jabberwock" not in reply.lower(), "the self-identity misroute must be gone"


def test_self_heals_knowledge_gap_via_teacher(agent, monkeypatch):
    # The self-heal now flows through domains.topic_grounding.ground_topic (PHRASE
    # grounding: local Wikipedia library, then web) -- the per-word ground_unknowns
    # teacher chain is only the FALLBACK when that module is absent. Monkeypatch the
    # phrase grounder so the heal is deterministic and offline (it stands in for the
    # dictionary/wiki source), and assert the agent CONSULTS it on a miss and then
    # holds the answer.
    calls = {"n": 0, "allow_web": []}
    import domains.topic_grounding as _tg

    def fake_ground_topic(ag, phrase, **kw):
        calls["n"] += 1
        calls["allow_web"].append(kw.get("allow_web"))
        assert str(phrase).lower() == "moon"
        ans = "the moon is Earth's natural satellite"
        return ag.learn_from_teacher(
            phrase, {"answer": ans, "learn": [{"phrase": phrase, "answer": ans}]})

    monkeypatch.setattr(_tg, "ground_topic", fake_ground_topic)
    reply = agent.converse("What do you know about the moon?", speech_act="question")

    assert _answer_topic_goals(agent, "moon"), "routed to the topic"
    assert "natural satellite" in reply.lower(), (
        "on a miss the agent must GROUND the topic through its own phrase grounder "
        "and re-answer -- fixing its own knowledge gap")
    assert calls["n"] >= 1, "the phrase grounder (ground_topic) must have been consulted"
    assert calls["allow_web"] == [False], (
        "a graph-minted SearchRequest owns the remote lookup; inline grounding "
        "must stay local to avoid repeating the same network search")
    # It actually LEARNED the concept (memoised, answerable without re-grounding).
    assert "taught_moon" in agent.taught_capabilities(), "the grounding must persist"


def test_explicit_native_repair_disposition_blocks_topic_grounding(agent, monkeypatch):
    # A lexical topic can coexist with a native repair decision. The adapter
    # must respect an explicit selected disposition, but must not infer that
    # disposition from a force/goal hypothesis alone.
    import domains.topic_grounding as _tg

    calls = []

    def unexpected_http(url, timeout=8):
        calls.append((url, timeout))
        raise AssertionError("native repair must leave remote retrieval pending")

    monkeypatch.setattr(_tg, "_http_get", unexpected_http)
    def local_grounder(ag, phrase, **_kwargs):
        answer = f"A local summary of {phrase}."
        return ag.learn_from_teacher(
            phrase, {"answer": answer,
                     "learn": [{"phrase": phrase, "answer": answer}]})

    monkeypatch.setattr(_tg, "ground_topic", local_grounder)
    reply = agent.converse("What do you know about the moon?",
                           speech_act="question")

    inbound = agent._last_turn_inbound
    interpretation_id = agent.s.node(inbound)["attrs"].get(
        "communication_interpretation_id")
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert _answer_topic_goals(agent, "moon")
    assert "local summary" in reply.lower()
    assert interpretation.get("cognitive_disposition") != "repair"

    # Simulate a subsequent native adjudication on this same interpretation;
    # a topic goal remains inspectable, but neither its renderer nor request
    # dispatcher may overrule the explicit selected disposition.
    agent.inner.set_attr(interpretation_id, "cognitive_disposition", "repair")
    from domains.fetch_dispatch import mint_search_request
    request = mint_search_request(agent, "moon")
    agent.inner.set_attr(request, "source", "answer_topic")
    before_calls = len(calls)
    assert agent._answer_topic_reply(inbound) is None
    agent._dispatch_pending_io(inbound)
    assert len(calls) == before_calls
    assert agent.s.node(request)["attrs"]["status"] == "requested"


def test_genuinely_self_referential_question_is_unchanged(agent):
    reply = agent.converse("What are you?", speech_act="question")
    assert not _answer_topic_goals(agent), (
        "a self-referential question has no external topic -> route rule must NOT "
        "fire (topic_pending stays absent)")
    # The self path answered it -- not the topic-gap floor.
    assert "couldn't find it through the sources" not in reply.lower()


def test_no_external_topic_when_subject_is_self_word(agent):
    # 'how do you learn' -- reflexive, but no object/oblique topic -> no routing.
    agent.converse("How do you learn?", speech_act="question")
    assert not _answer_topic_goals(agent), (
        "a manner self-question has no external object/oblique nominal, so no "
        "answer_topic goal is minted")


def test_possessive_self_topic_is_not_grounded_externally(agent):
    # "how does YOUR collapse function work" -- the topic is the agent's OWN
    # faculty (a second-person POSSESSIVE 'your' determining a following noun).
    # The graph understands this (your -refers_to-> a second-person Concept, and
    # it has a next_mention) and DEFERS the external route -> no answer_topic
    # goal, no grounding of "your collapse". It falls to the reflexive self path.
    reply = agent.converse("How does your collapse function work?", speech_act="question")
    assert not _answer_topic_goals(agent, "collapse function") and not _answer_topic_goals(agent, "collapse"), (
        "a second-person-possessed topic ('your collapse') must NOT route to "
        "external-topic grounding -- the graph understands it is about the agent")
    assert "couldn't find it through the sources" not in (reply or "").lower(), (
        "it must not fall to the external-topic gap floor")


def test_external_topic_still_routes_with_possessive_guard(agent):
    # The possessive guard must not break the moon route ('you' is the subject,
    # 'moon' is preceded by 'the' -- no possessive determining the topic).
    agent.converse("What do you know about the moon?", speech_act="question")
    assert _answer_topic_goals(agent, "moon"), (
        "an external topic with no possessive self-reference still routes")


def test_typed_fragment_does_not_mint_topic_or_grounding_requests(agent):
    reply = agent.converse(
        "I could—", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "overlap",
                 "evidence": ["explicit_uncertainty"]})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["literal_form"] == "fragment"
    assert interpretation["cognitive_disposition"] == "defer"
    assert not _answer_topic_goals(agent)
    assert not [
        node for kind in ("GroundRequest", "SearchRequest")
        for node in agent.s.nodes(kind)
        if agent.inner.has_node(node)
        and agent.s.node(node)["attrs"].get("status") in ("requested", "running")
    ]
    assert reply == "", (
        "an overlapping turn-compatible fragment selected native defer, so no "
        "reply or error surface is expected")


def test_what_is_x_made_of_routes_to_topic_not_know_tail(agent, monkeypatch):
    # "What is the moon made of?" must route to topic=moon (composition ask),
    # NOT know('moon made of') -> "I don't know moon made of."
    import domains.topic_grounding as _tg

    def fake_aspect(agent, concept, aspect, **kw):
        assert concept == "moon" and aspect == "made_of"
        ans = "The Moon's crust is mostly oxygen and silicon; its mantle is silicate rock."
        return agent.learn_from_teacher(
            f"composition of {concept}",
            {"answer": ans, "learn": [{"phrase": f"composition of {concept}", "answer": ans}]})

    monkeypatch.setattr(_tg, "ground_topic_aspect", fake_aspect)
    reply = agent.converse("What is the moon made of?", speech_act="question")
    assert _answer_topic_goals(agent, "moon"), (
        "composition question must mint Goal{kind:answer_topic, concept:'moon'}")
    assert "moon made of" not in reply.lower(), (
        "the mangled know-tail reply must be gone")
    assert "silicate" in reply.lower() or "oxygen" in reply.lower() or "crust" in reply.lower(), (
        "composition aspect must answer with material/composition content, not generic orbit prose")
    assert "i am jabberwock" not in reply.lower()


def test_embedded_wh_topic_routes_not_self_identity(agent):
    # "do you know what dancing is?" — reflexive (you), but the topic is the
    # embedded wh-clause nominal (dancing), not the agent's identity.
    reply = agent.converse("Do you know what dancing is?", speech_act="question")
    assert _answer_topic_goals(agent, "dancing"), (
        "embedded wh-clause topic must route to answer_topic, not self_identity")
    assert "i am jabberwock" not in reply.lower(), (
        "the self-identity misroute must be gone")
    assert "dancing" in reply.lower() or "dance" in reply.lower() or "couldn't find" in reply.lower(), (
        "the reply must be about dancing (or an honest topic miss), not identity")


def test_polar_capability_question_honest_reply(agent):
    reply = agent.converse("Can you dance?", speech_act="question")
    assert "i don't hold that" not in reply.lower(), (
        "a capability question must not get the knowledge-gap shrug")
    assert "can't dance" in reply.lower() or "no embodiment" in reply.lower(), (
        "the graph must honestly decline dance from held capability knowledge")
    assert "no body" not in reply.lower(), (
        "adapter must not inject the retired 'no body' floor")


def test_navigate_3d_spaces_graph_capability_reply(agent):
    reply = agent.converse("Can you navigate 3D spaces?", speech_act="question")
    meta = agent.last_turn_reply_meta()
    assert meta.get("reply_from") == "agent"
    assert "no body" not in reply.lower()
    assert "yes" in reply.lower() or "can navigate" in reply.lower(), (
        "spatial navigation is a held graph capability, not a body-dependent refusal")


def test_polar_capability_with_object_still_routes_topic(agent):
    # The external object still creates a topic goal, but the graph cannot use
    # topic presence alone as support for the polar capability proposition.
    reply = agent.converse("Can you play chess?", speech_act="question")
    goals = _answer_topic_goals(agent, "chess")
    assert goals, (
        "an object-bearing polar question routes to the external topic")
    assert agent.s.node(goals[-1])["attrs"].get("outcome") not in {
        "answered", "resolved"}
    assert "information" in reply.lower() and "answer" in reply.lower(), (
        "missing proposition support should request grounding, not invent a "
        "capability or confuse topic knowledge with relation evidence")
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    release = trace.get("production_release") if trace else None
    receipt = next((agent.s.node(node)["attrs"]
                    for node in agent.s.nodes("ProductionGateReceipt")
                    if release and int(node.value) == release.get("receipt_id")),
                   {})
    assert (release is not None
            and receipt.get("status") == "released"
            and release.get("parse_back_mode") == "conversation_action_graph"
            and release.get("semantic_event") == "repair"
            and release.get("semantic_intent") == "request"
            and trace.get("reply_commitment", {}).get("speech_acts")
            == ["clarification"]
            and trace.get("answer_commitment") is None
            and receipt.get("surface") == reply), (
        "release the graph-authored relation repair, never as a grounded "
        "answer")


def test_self_polar_inventory_question_repairs_without_false_negative(agent):
    # A large Rule inventory is not, by itself, a supported proposition about
    # the parsed "hold" relation. Do not turn an absent relation link into a
    # false claim that the agent holds nothing; let native arbitration repair.
    reply = agent.converse("You hold rules, yes?", speech_act="question")
    assert len(list(agent.s.nodes("Rule"))) > 0
    goals = _answer_topic_goals(agent, "rules")
    assert goals, "the parsed external object remains an event-bound topic goal"
    assert "don't hold" not in reply.lower()
    assert "do not hold" not in reply.lower()

    inbound_id = agent.last_turn_inbound_id()
    inbound = next(node for node in agent.s.nodes("Message")
                   if int(node.value) == inbound_id)
    interpretation_id = agent.s.node(inbound)["attrs"].get(
        "communication_interpretation_id")
    assert interpretation_id is not None
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation.get("arbitration_basis") \
        == "missing_polar_relation_support"
    assert interpretation.get("cognitive_disposition") == "repair"

    trace = agent.reply_turn_trace(inbound_id)
    release = trace.get("production_release") if trace else None
    receipt = next((agent.s.node(node)["attrs"]
                    for node in agent.s.nodes("ProductionGateReceipt")
                    if release and int(node.value) == release.get("receipt_id")),
                   {})
    assert (release is not None
            and release.get("semantic_event") == "repair"
            and trace.get("reply_commitment", {}).get("speech_acts")
            == ["clarification"]
            and trace.get("answer_commitment") is None
            and receipt.get("status") == "released"
            and receipt.get("surface") == reply)


def test_self_polar_memory_question_does_not_infer_seen_from_topic(agent):
    reply = agent.converse("Have you seen the report?", speech_act="question")
    assert _answer_topic_goals(agent, "report")
    assert "i have seen" not in reply.lower()
    assert "i haven't seen" not in reply.lower()

    inbound_id = agent.last_turn_inbound_id()
    inbound = next(node for node in agent.s.nodes("Message")
                   if int(node.value) == inbound_id)
    interpretation_id = agent.s.node(inbound)["attrs"].get(
        "communication_interpretation_id")
    assert interpretation_id is not None
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation.get("arbitration_basis") \
        == "missing_polar_relation_support"
    trace = agent.reply_turn_trace(inbound_id)
    assert trace["answer_commitment"] is None
    assert trace["production_release"]["semantic_event"] == "repair"
    assert trace["reply_commitment"]["speech_acts"] == ["clarification"]


def test_unresolved_event_time_selection_repairs_without_fabricated_history(agent):
    reply = agent.converse("Which rule fired last?", speech_act="question")
    inbound_id = agent.last_turn_inbound_id()
    inbound = next(node for node in agent.s.nodes("Message")
                   if int(node.value) == inbound_id)
    message_attrs = agent.s.node(inbound)["attrs"]
    assert message_attrs.get("comp_dispatch_path") == "frontier"
    interpretation_id = message_attrs.get("communication_interpretation_id")
    assert interpretation_id is not None
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation.get("relation_scope") == "event_specific"
    assert interpretation.get("cognitive_disposition") == "repair"
    assert interpretation.get("arbitration_basis") \
        == "missing_event_history_support"
    history = agent.s.nodes("RuleFiringHistory")
    assert len(history) == 1
    history_attrs = agent.s.node(history[0])["attrs"]
    assert history_attrs.get("schema") == "rule_firing_history.v1"
    assert history_attrs.get("last_inbound_message_id") == inbound_id
    assert history_attrs.get("last_rule_name")
    assert "don't know 'rule'" not in reply.lower()
    assert "information" in reply.lower() and "answer" in reply.lower()

    trace = agent.reply_turn_trace(inbound_id)
    assert (trace["answer_commitment"] is None
            and trace["production_release"]["semantic_event"] == "repair"
            and trace["reply_commitment"]["speech_acts"] == ["clarification"])


def test_event_time_selection_answers_from_prior_turn_history(agent):
    agent.converse("Good morning.", speech_act="greeting")
    history = agent.s.nodes("RuleFiringHistory")
    assert len(history) == 1
    prior_history = dict(agent.s.node(history[0])["attrs"])
    prior_rule = prior_history["last_rule_name"]
    prior_message_id = prior_history["last_inbound_message_id"]

    reply = agent.converse("Which rule fired last?", speech_act="question")
    inbound_id = agent.last_turn_inbound_id()
    inbound = next(node for node in agent.s.nodes("Message")
                   if int(node.value) == inbound_id)
    interpretation_id = agent.s.node(inbound)["attrs"].get(
        "communication_interpretation_id")
    assert interpretation_id is not None
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation.get("cognitive_disposition") == "answer"
    assert interpretation.get("arbitration_basis") \
        == "grounded_rule_firing_history"
    assert interpretation.get("selected_rule_name") == prior_rule
    assert prior_rule in reply

    evidence = agent.inner.neighbours(
        interpretation_id, "has_rule_firing_answer_evidence")
    assert len(evidence) == 1
    evidence_attrs = agent.s.node(evidence[0])["attrs"]
    assert evidence_attrs.get("status") == "supported"
    assert evidence_attrs.get("rule_name") == prior_rule
    assert evidence_attrs.get("source_message_id") == prior_message_id
    trace = agent.reply_turn_trace(inbound_id)
    assert trace["production_release"]["parse_back_mode"] \
        == "grounded_comprehension"
    assert trace["production_release"]["semantic_event"] == "answer_fragment"
    assert reply == prior_rule + "."


@pytest.mark.parametrize(("language", "question", "punctuation"), [
    ("es", "¿Qué regla se ejecutó por última vez?", "."),
    ("ja", "最後にどのルールが発火しましたか？", "。"),
])
def test_live_multilingual_event_time_selection_uses_native_history(
        agent, language, question, punctuation):
    agent.converse("Good morning.", speech_act="greeting")
    history = agent.s.nodes("RuleFiringHistory")
    assert len(history) == 1
    prior = dict(agent.s.node(history[0])["attrs"])
    prior_rule = prior["last_rule_name"]

    reply = agent.converse(question, speech_act="question")
    inbound_id = agent.last_turn_inbound_id()
    inbound = next(node for node in agent.s.nodes("Message")
                   if int(node.value) == inbound_id)
    message_attrs = agent.s.node(inbound)["attrs"]
    assert message_attrs.get("language") == language
    assert message_attrs.get("comp_dispatch_path") == "frontier"
    assert message_attrs.get("comp_predicate") == "fire"
    interpretation_id = message_attrs.get("communication_interpretation_id")
    assert interpretation_id is not None
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation.get("relation_scope") == "event_specific"
    assert interpretation.get("relation_focus") == "selection"
    assert interpretation.get("selection_target_kind") == "rule"
    assert interpretation.get("cognitive_disposition") == "answer"
    assert interpretation.get("arbitration_basis") \
        == "grounded_rule_firing_history"
    assert interpretation.get("selected_rule_name") == prior_rule

    evidence = agent.inner.neighbours(
        interpretation_id, "has_rule_firing_answer_evidence")
    assert len(evidence) == 1
    evidence_attrs = agent.s.node(evidence[0])["attrs"]
    assert evidence_attrs.get("status") == "supported"
    assert evidence_attrs.get("rule_name") == prior_rule
    assert evidence_attrs.get("source_message_id") \
        == prior["last_inbound_message_id"]
    trace = agent.reply_turn_trace(inbound_id)
    assert trace["production_release"]["parse_back_mode"] \
        == "grounded_comprehension"
    assert trace["production_release"]["semantic_event"] == "answer_fragment"
    assert reply == prior_rule + punctuation


@pytest.mark.parametrize(("language", "question"), [
    ("es", "¿Qué regla se ejecutó por última vez?"),
    ("ja", "最後にどのルールが発火しましたか？"),
])
def test_async_ingress_records_multilingual_selection_evidence(
        agent, language, question):
    agent.converse("Good morning.", speech_act="greeting")
    inbound_id = int(agent.ingest_turn(
        question, speech_act="question").value)
    inbound = next(node for node in agent.s.nodes("Message")
                   if int(node.value) == inbound_id)
    attrs = agent.s.node(inbound)["attrs"]
    assert attrs.get("language") == language
    assert attrs.get("comp_dispatch_path") == "frontier"
    assert attrs.get("comp_predicate") == "fire"
    interpretation_id = attrs.get("communication_interpretation_id")
    assert interpretation_id is not None
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation.get("relation_scope") == "event_specific"
    assert interpretation.get("relation_focus") == "selection"
    assert interpretation.get("selection_target_kind") == "rule"
    assert interpretation.get("evidence_provider") == "language_adapter"
    assert interpretation.get("evidence_force") == "repair_or_defer"


def test_rule_firing_history_does_not_answer_other_event_selections(agent):
    agent.converse("Good morning.", speech_act="greeting")
    prior_rule = agent.s.node(
        agent.s.nodes("RuleFiringHistory")[0])["attrs"]["last_rule_name"]
    reply = agent.converse("Which alarm fired last?", speech_act="question")
    inbound_id = agent.last_turn_inbound_id()
    inbound = next(node for node in agent.s.nodes("Message")
                   if int(node.value) == inbound_id)
    interpretation_id = agent.s.node(inbound)["attrs"].get(
        "communication_interpretation_id")
    assert interpretation_id is not None
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation.get("language_repair_focus") == "alarm"
    assert interpretation.get("cognitive_disposition") == "repair"
    assert interpretation.get("arbitration_basis") \
        == "missing_event_history_support"
    assert prior_rule not in reply


def test_infer_3d_from_2d_image_graph_capability_reply(agent):
    q = "Can you infer 3D spaces from a 2D image that has perspective?"
    reply = agent.converse(q, speech_act="question")
    meta = agent.last_turn_reply_meta()
    assert meta.get("reply_from") == "agent", (
        "capability question must be answered by the graph, not the adapter topic floor")
    assert "visual representation" not in reply.lower(), (
        "must not blind-lookup the 'image' topic instead of answering capability")
    assert "infer" in reply.lower() or "perspective" in reply.lower() or "spatial" in reply.lower(), (
        "reply must address spatial inference capability")


def test_polar_capability_conditional_clause_not_topic_routed(agent):
    # "if you had a body" must not hijack a capability question into grounding
    # the Wikipedia disambiguation page for "body" ("Body may refer to:").
    reply = agent.converse("Could you dance if you had a body?", speech_act="question")
    assert not _answer_topic_goals(agent, "body"), (
        "a conditional clause noun must not become an answer_topic route")
    assert "body may refer to" not in reply.lower(), (
        "the disambiguation header is the symptom of the misroute")
    assert "imagining i had" in reply.lower(), (
        "a counterfactual capability question must route to imagination")
    assert "dance" in reply.lower(), (
        "the reply must address dancing under the hypothetical")
    assert "no body" not in reply.lower() or "imagining" in reply.lower(), (
        "must not flat-refuse with only 'I have no body'")
