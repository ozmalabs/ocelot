"""test_reply_fallbacks_register — the conversational surface is ALWAYS honest and
substantive: it NEVER leaks a bare speech-act NAME ("acknowledgment"/"greeting")
as the reply text, and it NEVER returns None/silence. AND it uses the agent's
register VOICE: the same act renders a different surface depending on the register
the interlocutor has been using (casual "hey!" / formal "good day").

This gates the WIRING of the already-built register machinery
(`_REGISTER_SURFACES` / `note_register` / `register` / `surface_for`) into
`WorldAdapter.emit_reply` + `converse` + `conversation_action`, plus the always-
honest fallback ladder. donkey=0 throughout.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


# the bare tokens that must NEVER appear as a whole reply (the act-name leak).
_BARE_TOKENS = frozenset({
    "greeting", "acknowledgment", "thanks", "farewell", "closing", "statement",
    "answer", "backchannel", "clarification", "inquire_unknown", "instruction",
})


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a._donkey = {"n": 0}
    a.set_self_teacher(lambda q: (a._donkey.__setitem__("n", a._donkey["n"] + 1), "D")[1])
    return a


@pytest.fixture()
def agent():
    return _agent()


def _is_leak(reply) -> bool:
    """A leak = None/empty (silence) OR the whole reply is a bare act name."""
    if reply is None or not str(reply).strip():
        return True
    return str(reply).strip().lower() in _BARE_TOKENS


# ---------------------------------------------------------------------------
# NO BARE TOKEN / NO SILENCE — a battery of turn kinds, every reply honest.
# ---------------------------------------------------------------------------

def test_no_bare_token_no_silence_battery(agent, capsys):
    battery = [
        ("hey there", "greeting"),
        ("thanks a lot", "thanks"),
        ("what is a borogove", "question"),      # unanswerable
        ("move north", "statement"),             # unperformable instruction (no world)
        ("quorplezap the door", "statement"),    # comprehension gap -> ask back
        ("the sky is blue", "statement"),        # plain statement
        ("goodbye", "farewell"),
        ("it is blue", "answer"),                # terminal act (was silence)
    ]
    print("\n--- NO-BARE-TOKEN / NO-SILENCE battery ---")
    for text, sa in battery:
        reply = agent.converse(text, sa)
        print(f"  [{sa:10}] {text!r:26} -> {reply!r}")
        assert not _is_leak(reply), f"leaked bare token / silence for {text!r}: {reply!r}"
    assert agent._donkey["n"] == 0        # every reply from held machinery, no LLM


# ---------------------------------------------------------------------------
# REGISTER MATCH — the VOICE capability: same act, surface by tracked register.
# ---------------------------------------------------------------------------

def test_casual_vs_formal_surfaces(capsys):
    casual = _agent()
    cas_greet = casual.converse("hey, what's up?", "greeting")
    cas_ack = casual.converse("yeah cool, the sky is blue", "statement")

    formal = _agent()
    fml_greet = formal.converse("Good day, kindly tell me the time.", "greeting")
    fml_ack = formal.converse("Indeed, the sky is certainly blue.", "statement")

    print("\n--- REGISTER MATCH (same act, different surface by register) ---")
    print(f"  casual: register={casual.register()!r} greeting={cas_greet!r} ack={cas_ack!r}")
    print(f"  formal: register={formal.register()!r} greeting={fml_greet!r} ack={fml_ack!r}")

    assert casual.register() == "casual" and formal.register() == "formal"
    # the VOICE: same speech act, register-matched surface.
    assert cas_greet == "hey!" and cas_ack == "got it"
    assert fml_greet == "good day" and fml_ack == "understood"
    # discriminative: the two registers produce DIFFERENT surfaces for one act.
    assert cas_greet != fml_greet and cas_ack != fml_ack


# ---------------------------------------------------------------------------
# HONEST FALLBACKS — an "I don't ..." / "no world" statement, never token/silence.
# ---------------------------------------------------------------------------

def test_unanswerable_question_is_honest_statement(agent, capsys):
    reply = agent.converse("what is a borogove", "question")
    print(f"\n  unanswerable question -> {reply!r}")
    assert isinstance(reply, str) and "borogove" in reply
    assert reply.lower().startswith("i don't")
    assert not _is_leak(reply)


def test_unperformable_instruction_is_honest(agent, capsys):
    reply = agent.converse("move north", "statement")
    print(f"  unperformable instruction -> {reply!r}")
    assert isinstance(reply, str)
    assert "no attached world" in reply.lower() or "no scene" in reply.lower()
    assert reply.strip().lower() != "acknowledgment"
    assert not _is_leak(reply)


def test_gap_asks_back_register_matched(agent, capsys):
    reply = agent.converse("quorplezap the door", "statement")
    print(f"  gap ask-back -> {reply!r}")
    assert isinstance(reply, str) and "quorplezap" in reply
    assert reply.rstrip().endswith("?")       # it ASKED (a repair first-pair-part)
    assert not _is_leak(reply)


def test_terminal_answer_is_acknowledged_not_silent(agent, capsys):
    reply = agent.converse("it is blue", "answer")
    print(f"  terminal answer -> {reply!r}")
    assert isinstance(reply, str) and reply.strip().lower() in ("noted", "got it",
                                                                "understood")
