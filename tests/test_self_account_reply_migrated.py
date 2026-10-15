"""Honest self-account replies (seeds/self_account_reply.json, 2026-10-10).

Pinned claims:
  * domains/self_account.evidence reads a question about the agent's own
    preferences or pastimes and what kind of thing its topic is, from WordNet
    (the dictionary used, not recited); a world question, a work question and
    a statement carry no evidence;
  * on the production path the question gets the self-account and the
    question turned back -- released as the agent's answer, not a definition
    and not the error floor;
  * route_question_to_topic declines a turn carrying the evidence.
"""
from __future__ import annotations

import collections
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "scripts"), os.path.join(ROOT, "runners", "dsl", "python"),
          os.path.join(ROOT, "evaluation", "substrate_capability")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains import self_account as sa     # noqa: E402


@pytest.mark.parametrize("text,mode,topic", [
    ("What do you do for fun?", "pastime", "fun"),
    ("What kind of music do you like?", "listen", "music"),
    ("What are some of your favorite movies and TV shows?", "watch", "movies and tv shows"),
    ("Do you like video games?", "play", "video games"),
    ("What's your favorite food?", "taste", "food"),
    ("What do you like to read?", "read", "books"),
    ("Do you like to travel?", "do", "travel"),
    ("What are your hobbies?", "pastime", "hobbies"),
])
def test_evidence(text, mode, topic):
    assert sa.evidence(text) == {"self_account_mode": mode, "self_account_topic": topic}


@pytest.mark.parametrize("text", ["What is music?", "What do you do for work?", "I like music.",
                                  "Do you like it?"])
def test_no_evidence(text):
    assert sa.evidence(text) is None


def test_route_rule_declines_self_account_turns():
    seed = json.load(open(os.path.join(ROOT, "seeds", "conversation_topic_route.json")))
    assert "self_account_mode" in json.dumps(seed["rules"][0]["where"])


@pytest.fixture(scope="module")
def st():
    import endemic_rsi_daemon_v1 as E
    from domains import topic_grounding as tg
    tg._http_get = lambda *a, **k: (_ for _ in ()).throw(OSError("offline"))
    s = E.boot(True, promote=False)
    E.say(s, "Hello.")
    return s


def test_production_path_releases_the_self_account(st, monkeypatch):
    import long_session_cost_v1 as L
    monkeypatch.delenv("OZMA_SELF_ACCOUNT", raising=False)
    status, reply = L.say(st, "What do you do for fun?", collections.defaultdict(float))
    assert status == "reply_released", (status, reply)
    assert reply.startswith("I don't have hobbies or pastimes") and reply.endswith("How about you?")
    status, reply = L.say(st, "What kind of music do you like?", collections.defaultdict(float))
    assert status == "reply_released" and "listen to music" in reply, (status, reply)
    # criteria 1.3.0 classes any reply ending in '?' as a clarification, so a
    # self-account that turns the question back scores 1, not as self_content
    # (a criterion question for the human; recorded in the results doc)
    from domains import reply_quality as rq
    assert rq.assess("What kind of music do you like?", reply)["reason"] == "question->clarification"
