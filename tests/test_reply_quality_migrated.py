"""P0 of the open-ended self-improvement plan: ReplyQuality v1 (report-only).

Pinned: the reply/inbound classes and scores on the cases that motivated the
measure, chiefly that a neutral receipt in answer to a question is
inappropriate (the replay judge counted it as a fix), plus the agreement
statistic used by gate Q0.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "evaluation", "substrate_capability")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.reply_quality import assess, reply_class, inbound_class, summarise   # noqa: E402

ERR = "ERROR: no communicative response could be generated."


@pytest.mark.parametrize("inbound,reply,score,reason", [
    ("What's your favorite book?", "got it", 0, "question->receipt"),
    # criteria 1.2.0/1.3.0 (human decision, 2026-10-10): a dictionary definition is never a reply
    ("What do you do for fun?", 'Fun is defined by the Oxford English Dictionary as "pleasure".', 0, "question->definition"),
    ("What do you do for a living?", "I talk with people for a living.", 2, "question->self_content +self_answer"),
    ("What kind of music do they play?", "Pink Floyd play progressive rock music.", 2, "question->content +on_topic"),
    ("I like to watch movies and TV shows.", "got it", 1, "statement->receipt"),
    ("I like to watch movies and TV shows.", "Television (TV) is a medium for moving images.", 0, "statement->definition"),
    ("I like to play video games too!", "I took on the goal to play the video games, but I have no world.", 0,
     "statement->goal_take"),
    ("Hi! I'm someone.", "hey!", 2, "greeting->greeting"),
    ("What's up?", ERR, 0, "greeting->error"),
    ("Ok, sounds good.", "", 0, "statement->none"),
])
def test_assess_on_motivating_cases(inbound, reply, score, reason):
    out = assess(inbound, reply)
    assert (out["score"], out["reason"]) == (score, reason), out


def test_imperative_goal_take_is_an_honest_minimal_reply():
    out = assess("Bake the cake.", "I took on the goal to Bake the cake, but I have no world.", literal_form="imperative")
    assert out["inbound_class"] == "imperative" and out["score"] == 1


def test_v1_1_fixes_found_on_the_production_stream():
    long_quote = ("Romanian singer Alexandra Stan has released six studio albums. Stan's career began in 2009, "
                  "when producers heard her sing and I quote.")
    assert reply_class(long_quote) == "definition"          # about the agent? read from the FIRST sentence
    assert reply_class("I don't hold anything about \u201crussia\u201d yet, and I couldn't find it.") == "gap_floor"
    assert inbound_class("I know, right? They're the best.") == "statement"   # a rhetorical tag is not a question
    assert inbound_class("I know, right? What do you think?") == "question"


def test_classes_and_summary():
    assert inbound_class("Hey, what do you do for fun on weekends?") == "question"
    assert reply_class("what's 'I've'?") == "clarification"
    assert reply_class("I hold no faculty for that yet -- I've filed it as a gap.") == "gap_floor"
    assert summarise([2, 1, 0, 0]) == {"n": 4, "mean": 0.75, "appropriate": 1, "minimal": 1, "inappropriate": 2}


def test_kappa_statistic():
    import reply_quality_agreement_v1 as ag
    assert ag.kappa([(0, 0), (1, 1), (2, 2)]) == 1.0
    assert ag.kappa([(0, 1), (1, 0)]) < 0
    assert ag.kappa([]) is None
