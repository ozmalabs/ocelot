"""Question vs statement split — the heuristic the chat REPL uses to decide
which pipeline a typed line goes through.

Questions → answer_within (Frame layer + capabilities + teacher chain).
Statements → agent.receive({kind: "assert", text: ...}) — the agent's own
message-processing path. What the agent does with the statement is the
agent's call; the chat doesn't encode behaviour for it.
"""
from __future__ import annotations

import pytest

from domains.chat_routing import is_question


@pytest.mark.parametrize("text", [
    "what is photosynthesis?",
    "Who is Ada Lovelace?",
    "tell me about black holes",
    "is 17 prime?",
    "How does a transformer work?",
    "What time is it?",
    "Why is the sky blue",        # no question mark, still leads with why
    "could you help me",
    "should I do that",
    # the existing tool-imperatives also route through answer_within
    # (Frames installed by agent_tools)
    "read hello",
    "run echo gamma",
    "write hi to greeting",
])
def test_question_or_imperative_routes_through_reasoning(text):
    assert is_question(text) is True, text


@pytest.mark.parametrize("text", [
    "I am Matt",
    "I am your creator, Matt",
    "My name is Matt",
    "hi",
    "this is fine",
    "Matt is the user",
    "the kernel is fast",
    "you should be more careful",   # 'you' is not in lead set, statement
    "thanks",
    "the answer is 42",
])
def test_statement_routes_through_receive(text):
    assert is_question(text) is False, text


def test_empty_line_is_not_a_question():
    assert is_question("") is False
    assert is_question("   ") is False
