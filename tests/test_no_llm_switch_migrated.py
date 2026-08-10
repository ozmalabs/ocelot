"""OZMA_NO_LLM — the hard kill-switch for hosted-LLM assistance at runtime.

Phase B5-prep gate (see docs/llm_touchpoint_audit.md): when OZMA_NO_LLM is
set (truthy), every LLM link in the teacher machinery is SKIPPED — the chain
falls through to its existing non-LLM links and honest-miss path (the
human-gated close) — and any code that would STILL attempt a hosted call
raises RuntimeError so violations are loud instead of silent.

The switch is adapter POLICY at the teacher-construction/invocation boundary
(mechanical host I/O per CLAUDE.md), not an agent decision: nothing here
reads graph state.
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
def no_llm_env(monkeypatch):
    monkeypatch.setenv("OZMA_NO_LLM", "1")


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


# ---------------------------------------------------------------------------
# the switch itself
# ---------------------------------------------------------------------------

def test_switch_truthiness(monkeypatch):
    from domains.no_llm import no_llm
    for off in ("", "0", "false", "no", "off", "False", "OFF"):
        monkeypatch.setenv("OZMA_NO_LLM", off)
        assert not no_llm(), f"{off!r} must read as OFF"
    monkeypatch.delenv("OZMA_NO_LLM", raising=False)
    assert not no_llm(), "unset must read as OFF"
    for on in ("1", "true", "yes", "anything"):
        monkeypatch.setenv("OZMA_NO_LLM", on)
        assert no_llm(), f"{on!r} must read as ON"


# ---------------------------------------------------------------------------
# LLM links are never invoked / constructed under the switch — LOUDLY
# ---------------------------------------------------------------------------

def test_llm_partner_construction_raises(no_llm_env):
    from domains.llm_partner import LLMPartner
    with pytest.raises(RuntimeError, match="OZMA_NO_LLM"):
        LLMPartner()


def test_llm_partner_ask_raises_on_prebuilt_instance(monkeypatch):
    # An instance built BEFORE the switch was set must still refuse to call.
    monkeypatch.delenv("OZMA_NO_LLM", raising=False)
    from domains.llm_partner import LLMPartner
    p = LLMPartner(backend="ollama")     # construction is offline (no probe)
    try:
        monkeypatch.setenv("OZMA_NO_LLM", "1")
        with pytest.raises(RuntimeError, match="OZMA_NO_LLM"):
            p.ask("hello?")
    finally:
        p.close()


def test_claude_cli_teacher_raises(no_llm_env):
    from scripts.claude_teacher import make_ask
    ask = make_ask()
    with pytest.raises(RuntimeError, match="OZMA_NO_LLM"):
        ask("what distinguishes /b/ from /p/?")


def test_teacher_via_claude_raises(no_llm_env):
    from domains.language_world import teacher_via_claude as lang_teacher
    from domains.structured_data_world import teacher_via_claude as sd_teacher
    with pytest.raises(RuntimeError, match="OZMA_NO_LLM"):
        lang_teacher("gap", "el gato bebe leche")
    with pytest.raises(RuntimeError, match="OZMA_NO_LLM"):
        sd_teacher("gap", '{"a": 1}')


def test_phonology_teacher_falls_back_to_expert(no_llm_env):
    # The phonology chain's non-LLM link is the expert signatures — under the
    # switch the LLM path is nulled at construction; the fallback SERVES.
    from domains.phonology_teacher import PhonologyTeacher

    class _Boom:  # an LLM stand-in that must never be consulted
        def is_available(self):
            raise AssertionError("LLM consulted under OZMA_NO_LLM")

        def ask(self, prompt):
            raise AssertionError("LLM consulted under OZMA_NO_LLM")

    t = PhonologyTeacher(llm_partner=_Boom())
    assert t.llm is None, "the LLM link must be skipped at construction"
    sigs = t._fetch_signatures(["zero", "one"])
    assert set(sigs) == {"zero", "one"}, "expert fallback must still answer"


# ---------------------------------------------------------------------------
# the teacher chain: LLM spec skipped, on-disk links unchanged
# ---------------------------------------------------------------------------

def test_attach_libraries_skips_llm_even_when_enabled(no_llm_env, agent):
    from domains.libraries import attach_libraries
    rep = attach_libraries(agent, enable_llm=True, log=lambda *a: None)
    assert rep["partner"] is None, "no LLM partner may attach under the switch"
    assert any("OZMA_NO_LLM" in s for s in rep["skipped"]), (
        "the skip must be attributed to the switch (detectable in the report)")
    assert getattr(agent, "_llm_partner", None) is None
    # the on-disk, non-LLM links still form the chain (grammar is built-in).
    assert "grammar" in rep["teachers"], (
        "the non-LLM teacher chain must be unaffected by the switch")
    assert getattr(agent, "_self_teacher", None) is not None


def test_dictionary_link_still_works(no_llm_env):
    # DictionaryTeacher (WordNet, on-disk) is a non-LLM link: under the switch
    # it must still answer, and its miss must still fall through to `fallback`.
    from domains import dict_teacher
    if not dict_teacher.is_available():
        pytest.skip("wordnet corpus not on disk")
    from domains.dict_teacher import DictionaryTeacher
    seen = []

    def wiki_stub(question):   # stands in for the on-disk wiki link
        seen.append(question)
        return None

    t = DictionaryTeacher(fallback=wiki_stub)
    payload = t("what is a cat?")
    assert payload and payload.get("answer"), "dictionary must still answer"
    assert t("what is a zzqqwx?") is None and seen, (
        "a dictionary miss must still fall through to the non-LLM fallback")


def test_ground_unknowns_uses_non_llm_chain(no_llm_env, agent):
    # The self-heal path (the moon-bug fix) must be byte-equivalent under the
    # switch: grounding flows through the agent's own non-LLM phrase grounder.
    import domains.topic_grounding as _tg
    calls = {"n": 0}

    def fake_ground_topic(ag, phrase, **kw):
        calls["n"] += 1
        assert str(phrase).lower() == "moon"
        ans = "the moon is Earth's natural satellite"
        return ag.learn_from_teacher(
            phrase, {"answer": ans, "learn": [{"phrase": phrase, "answer": ans}]})

    orig = _tg.ground_topic
    _tg.ground_topic = fake_ground_topic
    try:
        reply = agent.converse("What do you know about the moon?",
                               speech_act="question")
    finally:
        _tg.ground_topic = orig
    assert calls["n"] >= 1, "the non-LLM phrase grounder must be consulted"
    assert "natural satellite" in reply.lower(), (
        "the self-heal must still work with the LLM link killed")
    assert "taught_moon" in agent.taught_capabilities(), "grounding persists"


def test_honest_miss_reply_invites_teaching(no_llm_env, agent):
    # When NOTHING non-LLM can ground the topic, the chain must fall through
    # to the human-gated close: an honest miss that invites the human to teach
    # — never a hosted call, never a fabricated answer.
    import domains.topic_grounding as _tg
    orig = _tg.ground_topic
    _tg.ground_topic = lambda ag, phrase, **kw: None   # every source misses
    try:
        reply = agent.converse("What do you know about the zorblax?",
                               speech_act="question")
    finally:
        _tg.ground_topic = orig
    low = (reply or "").lower()
    assert "couldn't find it through the sources" in low, (
        f"the honest-miss floor must still be produced, got: {reply!r}")
    assert "tell me about it" in low, "the close must invite teaching"
