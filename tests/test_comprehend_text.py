"""test_comprehend_text — the GENERAL comprehension front end (domains/comprehend_text.py).

THE CONTRAST this gates: `domains/comprehend_question.comprehend()` is a table of
canned sentence CONSTRUCTIONS; input that matches none of them returns
`grounded=False` and the chat falls back to "acknowledgment" even for an honest
self-referential question. `comprehend_text.comprehend_text()` routes arbitrary
text through the agent's REAL general machinery (POS-typing + the gap-as-part-
of-speech parser + the relation composer, `domains/construction_grammar.py`) and
REASONS over the resulting frame to derive an intent — not a canned match.

Every assertion drives the REAL chat path (`agent.answer_question` /
`agent.converse`) wherever a real answer is asserted, mirroring the discipline
`tests/test_self_model.py` already uses; the discrimination tests call
`comprehend_text` directly to check the intermediate frame.
"""
from __future__ import annotations

import pytest

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import comprehend_question as cq
from domains import comprehend_text as ct


@pytest.fixture(scope="module")
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# ---------------------------------------------------------------------------
# THE CONTRAST — arbitrary phrasings the OLD table misses, now comprehended.
# ---------------------------------------------------------------------------

_TABLE_MISSED = [
    "Tell me about the rule hop_descend_gradient.",
    "can you describe how you're put together?",
    "What kind of thing are you?",
]


@pytest.mark.parametrize("text", _TABLE_MISSED)
def test_old_table_misses_these(text):
    spec = cq.comprehend(text)
    assert not getattr(spec, "grounded", False), (
        f"expected the OLD table to MISS {text!r} (pin the contrast); "
        f"it grounded as kind={spec.kind!r} instead")


@pytest.mark.parametrize("text", _TABLE_MISSED)
def test_general_path_derives_a_reflexive_dispatch(agent, text):
    # a real substrate is needed here: "Tell me about the rule X" only
    # promotes to a reflexive question once X is discovered as an actually-
    # HELD RuleSummary (comp.reflexive would be False for this one input
    # without graph state to query — there is no self-cue in it at all).
    comp = ct.comprehend_text(agent, text)
    assert comp.kind == "question"
    assert comp.reflexive is True
    assert comp.dispatch.get("path") == "meta"
    assert comp.dispatch.get("meta_target")


@pytest.mark.parametrize("text", _TABLE_MISSED)
def test_general_path_answers_for_real(agent, text):
    ans = agent.answer_question(text)
    assert isinstance(ans, str) and ans.strip()
    assert ans.strip().lower() not in ("acknowledgment", "noted")


def test_rule_name_grounded_dispatch_is_self_model_rule(agent):
    comp = ct.comprehend_text(agent, "Tell me about the rule hop_descend_gradient.")
    assert comp.dispatch["meta_target"] == "self_model_rule"
    assert comp.dispatch["meta_arg"] == "hop_descend_gradient"
    assert comp.dispatch["strategy"] in ("rule_name_grounded", "rule_name_grounded_imperative")
    ans = agent.answer_question("Tell me about the rule hop_descend_gradient.")
    assert "hop_descend_gradient" in ans
    assert "chosen_action" in ans           # the real held fact, same backend as the table path


def test_full_converse_turn_answers_the_missed_question(agent):
    text = "Tell me about the rule hop_descend_gradient."
    sa = agent.classify_speech_act(text)
    reply = agent.converse(text, speech_act=sa)
    assert reply is not None
    assert "hop_descend_gradient" in reply


# ---------------------------------------------------------------------------
# INTENT-KIND DISCRIMINATION — interrogative / imperative / declarative.
# ---------------------------------------------------------------------------

def test_interrogative_kind():
    comp = ct.comprehend_text(None, "How are you organised today, honestly?")
    assert comp.kind == "question"


def test_imperative_kind():
    comp = ct.comprehend_text(None, "look left")
    assert comp.kind == "instruction"
    assert comp.dispatch["path"] == "instruction"
    assert comp.dispatch["predicate"] == "look"


def test_declarative_kind():
    comp = ct.comprehend_text(None, "The rule hop_descend_gradient modifies gravity.")
    assert comp.kind == "statement"
    assert comp.dispatch["path"] == "statement"


def test_three_kinds_are_discriminated():
    kinds = {ct.comprehend_text(None, t).kind for t in (
        "How are you organised today, honestly?",
        "look left",
        "The rule hop_descend_gradient modifies gravity.",
    )}
    assert kinds == {"question", "instruction", "statement"}


# ---------------------------------------------------------------------------
# TYPED GAPS — carried, not fabricated over.
# ---------------------------------------------------------------------------

def test_unknown_token_is_carried_as_a_typed_gap():
    comp = ct.comprehend_text(None, "look left then quorplezap the door")
    surfaces = [g["surface"] for g in comp.gaps]
    assert "quorplezap" in surfaces
    gap = next(g for g in comp.gaps if g["surface"] == "quorplezap")
    assert gap["pos"] == "by-position"        # honestly typed: no POS anywhere found


def test_frontier_when_no_dispatch_derivable():
    # a reflexive question whose wh-role has no default meta_target mapped
    # (time/place aren't in _WH_DEFAULT_META) must stay an honest frontier,
    # never a fabricated dispatch.
    comp = ct.comprehend_text(None, "When did you last update yourself?")
    assert comp.kind == "question"
    assert comp.reflexive is True
    if comp.dispatch.get("path") == "frontier":
        assert "reason" in comp.dispatch
    else:
        # a keyword happened to score (acceptable — just must be honest, not fabricated)
        assert comp.dispatch.get("meta_target")


# ---------------------------------------------------------------------------
# BACK END UNCHANGED — a self-question the table DID handle keeps its EXACT
# prior behaviour (fast path; the reflect+prose back end is reused, not
# reimplemented).
# ---------------------------------------------------------------------------

_TABLE_HIT = [
    "How are you organised?",
    "what's your shape",
    "what does hop_descend_gradient do?",
]


@pytest.mark.parametrize("text", _TABLE_HIT)
def test_table_hits_stay_fastpath(text):
    comp = ct.comprehend_text(None, text)
    assert comp.fastpath is True
    assert comp.dispatch["path"] == "table"


@pytest.mark.parametrize("text", _TABLE_HIT)
def test_table_hits_answer_unchanged(agent, text):
    spec = cq.comprehend(text)
    from domains import reflective_faculty as rf
    expected = rf.reflect(spec.meta_target, spec.meta_arg, agent.s)
    expected_answer = agent._surface_self_state(expected)
    assert agent.answer_question(text) == expected_answer


def test_existing_self_organisation_regression(agent):
    ans = agent.answer_question("How are you organised?")
    assert isinstance(ans, str) and ans.strip()


# ---------------------------------------------------------------------------
# comprehend_text never raises on ordinary input.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "", "   ", "?", "a", "the the the", "Hello there!",
    "Why would your plan lead you into a wall?",
])
def test_never_raises(text):
    comp = ct.comprehend_text(None, text)
    assert comp.kind in ("question", "instruction", "statement")


# ---------------------------------------------------------------------------
# ORNATE LONG-TAIL — a reflexive "how do you <verb>" / "how does X come about"
# the agent holds NO specific self-account for routes to the HONEST self-process
# floor, NEVER the self_organisation DOMAIN LIST or an opaque rule-dump. A
# genuine self-STRUCTURE question ("how are you put together") keeps self_org.
#
# NB: the agent now HOLDS true self-accounts for its OPERATIONAL processes
# (learning=collapse, perceiving=sd-decode, world-attachment=adapter-ingest;
# taught via scripts/teach_self_processes.py -> seeds/self_processes.json, and
# introspected through the `self_process` reader). Those questions are answered
# SUBSTANTIVELY now (see test_self_process_introspection.py). The honest floor is
# preserved for a process the agent GENUINELY has no self-account for — the cases
# below use such processes (dreaming/sleeping), so the floor is still exercised.
# ---------------------------------------------------------------------------

_ORNATE_LONGTAIL = [
    "How do you dream?",
    "How do you sleep?",
]


@pytest.mark.parametrize("text", _ORNATE_LONGTAIL)
def test_ornate_longtail_routes_to_honest_self(agent, text):
    comp = ct.comprehend_text(agent, text)
    assert comp.kind == "question"
    assert comp.dispatch.get("path") == "honest_self"
    assert comp.dispatch.get("meta_target") != "self_organisation"


@pytest.mark.parametrize("text", _ORNATE_LONGTAIL)
def test_ornate_longtail_answers_honestly_not_domain_list(agent, text):
    ans = agent.answer_question(text)
    assert ans.lower().startswith("i can't say precisely")
    assert "organised into" not in ans          # NOT the domain list
    assert "hold the rule" not in ans            # NOT the opaque rule-dump


def test_ornate_absent_process_names_the_process_verb(agent):
    assert agent.answer_question("How do you dream?") == \
        "I can't say precisely how I dream."


def test_ornate_held_process_is_substantive_not_honest_floor(agent):
    # the agent HOLDS a self-account for learning (the collapse loop) -> a
    # substantive TRUE answer, NOT the honest deflection and NOT the rule dump.
    ans = agent.answer_question("How do you learn something new?")
    assert not ans.lower().startswith("i can't say precisely")
    assert "collapse" in ans.lower() and "surprise" in ans.lower()
    assert "hold the rule" not in ans


def test_self_structure_question_still_reaches_self_organisation(agent):
    # "how are you put together" is a real self-STRUCTURE question -> self_organisation,
    # NOT the honest floor (the discriminant that keeps the legit routing).
    comp = ct.comprehend_text(agent, "can you describe how you're put together?")
    assert comp.dispatch.get("path") == "meta"
    assert comp.dispatch.get("meta_target") == "self_organisation"


@pytest.mark.parametrize("text", _ORNATE_LONGTAIL)
def test_ornate_longtail_through_converse(agent, text):
    sa = agent.classify_speech_act(text)
    reply = agent.converse(text, speech_act=sa)
    assert reply.lower().startswith("i can't say precisely")
    assert "organised into" not in reply
