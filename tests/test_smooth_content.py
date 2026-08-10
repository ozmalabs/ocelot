"""test_smooth_content — the SUBSTANTIVE-reply gate: smooth connected prose,
register-shaped voice, and the self_shape-vs-program precedence.

The prior build fixed the social-act SURFACES + register-matching for greetings/
acks. This one does the CONTENT: the agent's substantive replies (describe-scene,
self-account) come out as ONE connected sentence instead of choppy per-item
fragments; the delivery's elaboration matches the tracked interlocutor register;
and a "what shape are you"-type question reads its self_shape faculty rather than
repeating a program named the common word "shape".

Discipline: the CONTENT is always the agent's own produced pieces / real graph
state; smoothing only JOINS them (connectives + a lead-in) — it authors no new
content. Facts are preserved (a smoothed rule reply still names its real writes).
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import conversation_action as ca
from domains import comprehend_text as ct
from domains import comprehend_question as cq
from domains.self_model import _RULE_SUMMARY_TYPE


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def _scene_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.set_self_teacher(lambda q: "D")
    ca.attach_scene(a, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False}])
    return a


# ---------------------------------------------------------------------------
# SMOOTH — the describe-scene reply is ONE connected sentence, not >=2 bare
# "The X <verb>." fragments.
# ---------------------------------------------------------------------------

def _fragment_count(text: str) -> int:
    """How many bare 'The X ...' sentence fragments — the choppy tell."""
    import re
    return len(re.findall(r"\bThe\s+\w+\b[^.]*\.", text))


def test_describe_scene_is_connected_prose_not_fragments():
    a = _scene_agent()
    reply = a.converse("describe what you see", "statement")
    print("\n  BEFORE (per-percept pieces): 'The grey thing stays. The yellow "
          "counter. The blue thing moves.'")
    print(f"  AFTER  (smoothed)           : {reply!r}")
    # one connected sentence: exactly one terminal period, a connective present,
    # and NOT the >=2 bare-fragment choppy form.
    assert reply.count(".") == 1, reply
    assert (" and " in reply) or ("," in reply), reply
    assert _fragment_count(reply) <= 1, reply          # not a string of "The X." fragments
    # still the real content — every percept's clause survives the join.
    for word in ("grey", "yellow", "blue"):
        assert word in reply, (word, reply)


# ---------------------------------------------------------------------------
# CONTENT REGISTER — a FORMAL interlocutor vs a CASUAL one differ in
# elaboration/terseness for the SAME content (aligned with the terse-vs-
# explicit spectrum audience_driven_production selects over).
# ---------------------------------------------------------------------------

def test_register_shapes_the_content_voice_formal_vs_casual():
    aC = _scene_agent(); aC.note_register("hey yeah cool")           # casual cues
    aF = _scene_agent(); aF.note_register("greetings, could you please")  # formal cues
    assert aC.register() == "casual" and aF.register() == "formal"
    casual = aC.converse("describe what you see", "statement")
    formal = aF.converse("describe what you see", "statement")
    print(f"\n  CASUAL: {casual!r}")
    print(f"  FORMAL: {formal!r}")
    # same content, register-shaped delivery: they DIFFER, and the formal reading
    # is the more elaborated (longer) one; the casual is terser.
    assert casual != formal
    assert len(formal.split()) > len(casual.split())
    # verbatim pins
    assert casual == "The grey thing stays, the yellow counter, and the blue thing moves."
    assert formal == "I observe the grey thing stays, the yellow counter, and the blue thing moves."
    # both convey the same three percepts
    for word in ("grey", "yellow", "blue"):
        assert word in casual and word in formal


def test_self_account_is_smoothed_first_person():
    from domains import reflective_faculty as rf
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    reply = a._surface_self_state(rf.reflect("self_modification", None, a.s))
    print(f"\n  self_modification -> {reply!r}")
    # one connected first-person sentence, not four bare "I hold the X." fragments.
    assert reply.count(".") == 1, reply
    assert reply.startswith("I ")
    assert (" and " in reply) or ("," in reply), reply


# ---------------------------------------------------------------------------
# SHAPE PRECEDENCE — "what shape are you?" / "what shape would you say you are?"
# read the self_shape faculty (seven meta-shapes), NOT a program named "shape".
# ---------------------------------------------------------------------------

_SHAPE_QS = ["what shape are you?", "what shape would you say you are?"]


@pytest.mark.parametrize("q", _SHAPE_QS)
def test_shape_question_reads_self_shape_not_program(agent, q):
    ans = agent.answer_question(q)
    print(f"\n  {q!r} -> {ans!r}")
    # the self_shape faculty's meta-shape decomposition, not a "my rule 'X' is
    # active; it fires when ..." program repeat.
    assert "meta-shapes" in ans
    assert "hierarchical invariance" in ans
    assert "my rule" not in ans        # discriminative: NOT the recover_shape_law repeat


def test_both_shape_phrasings_give_the_same_self_shape_answer(agent):
    a1 = agent.answer_question("what shape are you?")
    a2 = agent.answer_question("what shape would you say you are?")
    assert a1 == a2                     # the paraphrase no longer diverges to a program


def test_general_path_precedence_survives_a_spurious_shape_rule():
    """Defense-in-depth: even when the fast-path table is bypassed AND a
    RuleSummary is keyworded the common word 'shape', the reflexive general path
    routes to self_shape (keyword_overlap), never to the spurious program — while
    a GENUINE specific rule name still routes to self_model_rule (control)."""
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    a.s.add_node(_RULE_SUMMARY_TYPE, {"name": "recover_shape_law",
                                      "keywords_text": "shape", "match_text": "x",
                                      "active": True, "name_rank": 0.0})
    a.s.add_node(_RULE_SUMMARY_TYPE, {"name": "hop_descend_gradient",
                                      "keywords_text": "hop_descend_gradient",
                                      "match_text": "x", "active": True, "name_rank": 0.0})
    orig = cq.comprehend
    cq.comprehend = lambda t: None                      # force the general path
    try:
        for q in _SHAPE_QS:
            comp = ct.comprehend_text(a, q)
            assert comp.fastpath is False
            assert comp.dispatch.get("meta_target") == "self_shape", (q, comp.dispatch)
        # control: a genuine, specific rule name keeps its self_model_rule route.
        comp = ct.comprehend_text(a, "what does hop_descend_gradient do, you?")
        assert comp.dispatch.get("meta_target") == "self_model_rule", comp.dispatch
    finally:
        cq.comprehend = orig


# ---------------------------------------------------------------------------
# REGRESSION — facts preserved: a smoothed rule reply still names its real facts.
# ---------------------------------------------------------------------------

def test_smoothing_preserves_rule_facts(agent):
    ans = agent.answer_question("What does hop_descend_gradient do?")
    assert "I hold the rule." in ans          # the produced headline survives
    assert "hop_descend_gradient" in ans
    assert "chosen_action" in ans             # the real write fact
    assert "grid_navigation" in ans           # the from_seed provenance
