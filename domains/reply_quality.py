"""ReplyQuality v1: does a reply fit the turn it answers? (report-only)

P0 of docs/research/engine_substrate/OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md.
The replay judge counted any non-error change as a fix, so "got it" in answer
to a question scored +1. This module measures reply fit as a proxy, from
criteria held as data (domains/reply_quality_criteria_v1.json):

  inbound class  greeting | question | imperative | statement
  reply class    none | error | pending | goal_take | deferred | gap_floor |
                 receipt | greeting | clarification | definition |
                 self_content | content
  score          criteria.score_table[inbound][reply], upgraded 1 -> 2 for an
                 on-topic content reply that fits its addressee

2 = appropriate, 1 = acceptable-minimal, 0 = inappropriate. Mechanical: every
judgement here is a lookup in the criteria data. v1 gates nothing; its
agreement with human labels is the plan's gate Q0.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

_CRITERIA_PATH = Path(__file__).with_name("reply_quality_criteria_v1.json")
_WORD = re.compile(r"[a-z][a-z']*")


@lru_cache(maxsize=4)
def criteria(path: str = str(_CRITERIA_PATH)) -> dict:
    return json.loads(Path(path).read_text())


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _bare(text: str) -> str:
    return _norm(text).strip(" .!?,")


def _tokens(text: str) -> list:
    return _WORD.findall(_norm(text))


def _content_words(text: str, c: dict) -> set:
    stop = set(c["stopwords"])
    out = set()
    for t in _tokens(text):
        t = t.strip("'")
        if len(t) < 3 or t in stop:
            continue
        out.add(t[:-1] if t.endswith("s") and len(t) > 3 else t)
    return out


def _has_real_question(text: str, c: dict) -> bool:
    """A sentence ending in '?' that is not a rhetorical tag ('I know, right?')."""
    for sent in re.split(r"(?<=[.!?])\s+", (text or "").strip()):
        if sent.endswith("?") and _bare(sent) not in c["tag_questions"]:
            return True
    return False


def inbound_class(text: str, literal_form: Optional[str] = None, c: Optional[dict] = None) -> str:
    c = c or criteria()
    bare = _bare(text)
    toks = _tokens(text)
    greets = c["inbound_greeting_surfaces"]
    # a short turn that IS a greeting ("Hi! I'm Mary.", "What's up?"), not a
    # longer turn that merely opens with one ("Hey, what do you do for fun?")
    if bare in greets or (toks and len(toks) <= 4 and (toks[0] in greets or
                                                       any(bare.startswith(g) for g in greets))):
        return "greeting"
    if _has_real_question(text, c):
        return "question"
    if literal_form == "imperative":
        return "imperative"
    return "statement"


def addressed_to_agent(text: str, c: Optional[dict] = None) -> bool:
    c = c or criteria()
    return any(t in c["second_person_tokens"] for t in _tokens(text))


def reply_class(text: str, c: Optional[dict] = None) -> str:
    c = c or criteria()
    raw = (text or "").strip()
    if not raw:
        return "none"
    if raw in c["error_surfaces"]:
        return "error"
    low = _norm(raw)
    bare = _bare(raw)
    if any(low.startswith(p) for p in c["pending_prefixes"]):
        return "pending"
    if any(low.startswith(p) for p in c["goal_take_prefixes"]):
        return "goal_take"
    if any(m in low for m in c["deferred_markers"]):
        return "deferred"
    if any(m in low for m in c["gap_floor_markers"]):
        return "gap_floor"
    if bare in c["receipt_surfaces"]:
        return "receipt"
    if bare in c["greeting_surfaces"]:
        return "greeting"
    if any(low.startswith(p) for p in c["clarification_prefixes"]) or raw.endswith("?"):
        return "clarification"
    padded = " " + low + " "
    first = _first_sentence(raw)
    if any(m in padded for m in c["definition_markers"]) and not any(
            t in c["first_person_tokens"] for t in _tokens(first)):
        return "definition"
    if any(t in c["first_person_tokens"] for t in _tokens(first)):
        return "self_content"
    return "content"


def _first_sentence(text: str) -> str:
    """The reply's first sentence: whether a reply is ABOUT the agent is read
    there, not from a first-person token anywhere in a long quoted passage."""
    m = re.split(r"(?<=[.!?])\s+", (text or "").strip(), maxsplit=1)
    return m[0] if m else ""


def assess(inbound: str, reply: str, literal_form: Optional[str] = None,
           c: Optional[dict] = None) -> dict:
    """{score, inbound_class, reply_class, on_topic, addressed_to_agent, reason}."""
    c = c or criteria()
    ic = inbound_class(inbound, literal_form, c)
    rc = reply_class(reply, c)
    score = int(c["score_table"][ic][rc])
    on_topic = bool(_content_words(inbound, c) & _content_words(reply, c))
    to_agent = addressed_to_agent(inbound, c)
    first_person_in = any(t in c["first_person_tokens"] for t in _tokens(inbound))
    reason = f"{ic}->{rc}"
    if score == 1 and ic == "question" and to_agent and rc == "self_content":
        # a first-person answer to a question addressed to the agent fits its
        # addressee even without shared content words (v1 cannot check that it
        # answers THIS question; the Q0 labels measure how often that misleads)
        score, reason = 2, reason + " +self_answer"
    elif score == 1 and rc in c["upgrades"]["on_topic_classes"] and on_topic:
        if rc == "definition":
            if not (to_agent or first_person_in):
                score, reason = 2, reason + " +on_topic"
        elif ic == "question" and to_agent:
            pass        # a non-self content reply to a question about the agent stays minimal
        else:
            score, reason = 2, reason + " +on_topic"
    # CAPS (plan P6 criterion grammar, criteria >= 1.2.0): a held cap lowers a
    # (inbound, reply) class pair's score when its condition holds. Absent in
    # criteria 1.1.0, so the measure is unchanged until a human adopts one.
    person_turn = to_agent or first_person_in
    for cap in c.get("caps") or []:
        if rc not in cap.get("reply_classes", ()) or ic not in cap.get("inbound_classes", ()):
            continue
        cond = cap.get("when", "always")
        holds = (cond == "always" or (cond == "off_topic" and not on_topic)
                 or (cond == "addressed_to_agent" and to_agent) or (cond == "person_turn" and person_turn))
        if holds and score > int(cap.get("to", 0)):
            score, reason = int(cap.get("to", 0)), reason + f" -{cap.get('name', 'cap')}"
    return {"score": score, "inbound_class": ic, "reply_class": rc, "on_topic": on_topic,
            "addressed_to_agent": to_agent, "reason": reason}


def summarise(scores: list) -> dict:
    """Distribution of a list of assess() scores (ints)."""
    n = len(scores)
    return {"n": n, "mean": round(sum(scores) / n, 4) if n else None,
            "appropriate": scores.count(2), "minimal": scores.count(1), "inappropriate": scores.count(0)}
