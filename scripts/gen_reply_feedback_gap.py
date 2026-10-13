#!/usr/bin/env python3
"""Emit seeds/reply_feedback_gap.json (plan P2, 2026-10-10): the agent files
its own BAD REPLIES as concerns -- not only its unanswered turns.

Until P2 the loop's supply was the agent's own error floor
(seeds/unanswered_gap.json), reader disagreements (comprehension_health) and
human flags. A reply that was produced but did not fit -- a goal-take for a
statement, a receipt for a question, a dictionary definition for "what do you
like to do for fun?" -- filed nothing. Two kinds of evidence now do:

  * ACT MISMATCH, measured in production. WorldAdapter.record_turn_outcome
    writes the turn's ReplyQuality (domains/reply_quality.py, the measure
    judge v2 uses) as a datum: reply_quality_score / _reason / _reply_class.
    A score of 0 on a reply that is not the error floor or silence (those
    are unanswered_gap's) is evidence.
  * THE INTERLOCUTOR'S NEXT TURN. A turn that follows the agent's reply with
    other-initiated repair ("what?", "huh?", "I don't understand") or a
    rejection aimed at the reply ("that's not what I asked", "no, I meant")
    -- held ReplyFeedbackCue nodes, agent-editable data -- or that asks the
    SAME question again within the attended turn ring, is evidence about the
    PREVIOUS turn's reply (WorldAdapter.receive_utterance links each inbound
    turn to the previous one with `follows_turn`).

Evidence is held as TurnShape{shape_kind:'reply_feedback', sig_signal,
sig_reason} (the conversation turn ring's conceptual tier): signal is
act_mismatch / repair / rejection / repeat, reason the ReplyQuality class pair
of the turn whose reply drew it ("statement->goal_take"). A class files one
SelfConcern{kind:'reply_quality'} once it recurs min_recurrence times
(ReplyFeedbackPolicy), pointing about_message at the class's oldest turn --
the turn whose reply the experiment must change; the feedback turn itself is
linked by `drew_feedback`, never about_message. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/reply_feedback_gap.json"


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Ex(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Or0(x): return {"type": "IfThenElse", "cond": Eq(x, L(None)), "then": L(""), "other": x}
def T(x): return {"__term__": x}


def bare(text):
    """Case-folded, sentence punctuation removed: 'What?' -> 'what'."""
    t = {"type": "CaseFold", "text": text}
    for ch in ("?", "!", "."):
        t = {"type": "Replace", "text": t, "old": L(ch), "new": L("")}
    return t


def shape_effects(sig_signal, member, flag):
    return [
        ["add_node_if_absent", "sh", "TurnShape", {
            "shape_kind": "reply_feedback", "sig_signal": sig_signal,
            "sig_reason": T(Or0(A(member, "reply_quality_reason")))}],
        ["add_edge", "agent", "has_turn_shape", "sh"],
        ["add_edge", "sh", "has_member", member],
        ["add_edge", member, "member_of", "sh"],
        ["set_attr", member, flag, 1],
    ]


def interlocutor(m): return Eq(A(m, "from"), L("interlocutor"))


TALLY_MISMATCH = {
    "name": "tally_reply_act_mismatch",
    "comment": "An attended turn whose produced reply scored inappropriate in production (not the error floor or silence) joins its class shape.",
    "match": [["agent", "received", "m"], ["agent", "has_reply_feedback_policy", "pol"]],
    "where": And(
        Eq(A("pol", "enabled"), L(1)),
        interlocutor("m"),
        Eq(A("m", "reply_quality_score"), L(0.0)),
        Not({"type": "In", "member": A("m", "reply_quality_reply_class"), "container": L(["error", "none"])}),
        Not(Eq(A("m", "reply_mismatch_tallied"), L(1)))),
    "effects": shape_effects(T(L("act_mismatch")), "m", "reply_mismatch_tallied"),
}

TALLY_CUE = {
    "name": "tally_reply_feedback_cue",
    "comment": "The interlocutor's next turn repairs or rejects the agent's reply (a held ReplyFeedbackCue): evidence about the previous turn.",
    "match": [["agent", "received", "m2"], ["m2", "follows_turn", "m1"], ["pol", "has_feedback_cue", "c"],
              ["agent", "has_reply_feedback_policy", "pol"]],
    "where": And(
        Eq(A("pol", "enabled"), L(1)),
        interlocutor("m2"),
        Not(Eq(A("m2", "feedback_cue_tallied"), L(1))),
        Not(Eq(A("m1", "turn_outcome"), L(None))),
        {"type": "Let", "name": "b", "value": bare(A("m2", "text")), "body": Or(
            And(Eq(A("c", "match_mode"), L("whole")), Eq(V("b"), A("c", "phrase"))),
            And(Eq(A("c", "match_mode"), L("prefix")),
                Eq({"type": "StringIndexOf", "haystack": V("b"), "needle": A("c", "phrase")}, L(0))))}),
    "effects": [
        ["add_node_if_absent", "sh", "TurnShape", {
            "shape_kind": "reply_feedback", "sig_signal": T(A("c", "feedback_class")),
            "sig_reason": T(Or0(A("m1", "reply_quality_reason")))}],
        ["add_edge", "agent", "has_turn_shape", "sh"],
        ["add_edge", "sh", "has_member", "m1"],
        ["add_edge", "m1", "member_of", "sh"],
        ["add_edge", "m1", "drew_feedback", "m2"],
        ["set_attr", "m2", "feedback_cue_tallied", 1],
    ],
}

TALLY_REPEAT = {
    "name": "tally_repeated_question",
    "comment": "The interlocutor asks an attended earlier question again: the earlier turn's reply did not answer it.",
    "match": [["agent", "received", "m2"], ["agent", "received", "m1"], ["agent", "has_reply_feedback_policy", "pol"]],
    "where": And(
        Eq(A("pol", "enabled"), L(1)),
        interlocutor("m2"),
        Not(Eq(A("m2", "repeat_tallied"), L(1))),
        {"type": "Gte", "a": {"type": "StringIndexOf", "haystack": A("m2", "text"), "needle": L("?")}, "b": L(0)},
        interlocutor("m1"),
        {"type": "Lt", "a": V("m1"), "b": V("m2")},
        Not(Eq(A("m1", "turn_outcome"), L(None))),
        Eq(bare(A("m1", "text")), bare(A("m2", "text")))),
    "effects": [
        ["add_node_if_absent", "sh", "TurnShape", {
            "shape_kind": "reply_feedback", "sig_signal": "repeat",
            "sig_reason": T(Or0(A("m1", "reply_quality_reason")))}],
        ["add_edge", "agent", "has_turn_shape", "sh"],
        ["add_edge", "sh", "has_member", "m1"],
        ["add_edge", "m1", "member_of", "sh"],
        ["add_edge", "m1", "drew_feedback", "m2"],
        ["set_attr", "m2", "repeat_tallied", 1],
    ],
}

FIRST = {
    "name": "mark_reply_feedback_shape_first_member",
    "comment": "The oldest member of a reply_feedback TurnShape is its first_member (the turn the concern names), marked while it is attended.",
    "match": [["agent", "received", "m"], ["m", "member_of", "sh"]],
    "where": And(
        Eq(A("sh", "shape_kind"), L("reply_feedback")),
        Not(Ex({"type": "Neighbours", "node": V("sh"), "edge_type": "first_member"}, "_f", L(True))),
        Eq(V("m"), {"type": "Argmin", "source": {"type": "Neighbours", "node": V("sh"), "edge_type": "has_member"},
                    "var_name": "x", "value": V("x"), "default": None})),
    "effects": [["add_edge", "sh", "first_member", "m"]],
}

NOTE = {
    "name": "note_reply_quality_gap",
    "comment": "File a recurring bad-reply class as the agent's own experiment-eligible concern (see seed description).",
    "match": [["agent", "has_turn_shape", "sh"], ["sh", "first_member", "m"],
              ["agent", "has_reply_feedback_policy", "pol"]],
    "where": And(
        Eq(A("pol", "enabled"), L(1)),
        Eq(A("sh", "shape_kind"), L("reply_feedback")),
        Not(Eq(A("sh", "reply_quality_noted"), L(1))),
        Not(Ex({"type": "NodesOfType", "node_type": "SelfConcern"}, "sc2", And(
            Eq(A("sc2", "kind"), L("reply_quality")),
            Eq(Or0(A("sc2", "sig_signal")), Or0(A("sh", "sig_signal"))),
            Eq(Or0(A("sc2", "sig_reason")), Or0(A("sh", "sig_reason")))))),
        {"type": "Gte", "a": {"type": "Count", "source": {"type": "Neighbours", "node": V("sh"), "edge_type": "has_member"}},
         "b": A("pol", "min_recurrence")}),
    "effects": [
        ["set_attr", "sh", "reply_quality_noted", 1],
        ["add_node", "sc", "SelfConcern", {
            "status": "noted", "source": "implicit", "kind": "reply_quality",
            "content": T({"type": "StringConcat", "parts": [
                L("my reply to a "), Or0(A("sh", "sig_reason")), L(" turn drew "), Or0(A("sh", "sig_signal")),
                L(", e.g. \""), A("m", "text"), L("\" -> \""), Or0(A("m", "comp_reply_text")), L("\"")]}),
            "sig_signal": T(A("sh", "sig_signal")), "sig_reason": T(A("sh", "sig_reason"))}],
        ["add_edge", "agent", "has_self_concern", "sc"],
        ["add_edge", "sc", "about_message", "m"],
    ],
}

CUES = [
    # other-initiated repair (Schegloff et al. 1977's open-class repair initiators)
    ("what", "whole", "repair"), ("huh", "whole", "repair"), ("sorry", "whole", "repair"),
    ("pardon", "whole", "repair"), ("what do you mean", "prefix", "repair"),
    ("i don't understand", "prefix", "repair"), ("i do not understand", "prefix", "repair"),
    ("that doesn't make sense", "prefix", "repair"), ("that makes no sense", "prefix", "repair"),
    # rejection / correction aimed at the agent's reply
    ("that's not what i asked", "prefix", "rejection"), ("that is not what i asked", "prefix", "rejection"),
    ("that's not what i meant", "prefix", "rejection"), ("no, i meant", "prefix", "rejection"),
    ("no i meant", "prefix", "rejection"), ("you didn't answer", "prefix", "rejection"),
    ("that's not an answer", "prefix", "rejection"), ("that's wrong", "prefix", "rejection"),
]

nodes = [{"local_id": 0, "type": "ReplyFeedbackPolicy", "attrs": {
    "name": "reply_feedback_gap", "enabled": 1, "min_recurrence": 2,
    "description": "Agent-held policy: how many bad replies of one evidence class (signal x ReplyQuality class pair) make a reply_quality concern."}}]
edges = [{"src": {"role": "agent_root"}, "type": "has_reply_feedback_policy", "tgt": {"local": 0}, "attrs": {}}]
for k, (phrase, mode, cls) in enumerate(CUES, start=1):
    nodes.append({"local_id": k, "type": "ReplyFeedbackCue",
                  "attrs": {"phrase": phrase, "match_mode": mode, "feedback_class": cls}})
    edges.append({"src": {"local": 0}, "type": "has_feedback_cue", "tgt": {"local": k}, "attrs": {}})

seed = {
    "id": "reply_feedback_gap",
    "version": "1.0.0",
    "depends_on": ["gap_awareness", "conversation_turn_ring"],
    "description": __doc__,
    "nodes": nodes,
    "edges": edges,
    "productions": [],
    "rules": [TALLY_MISMATCH, TALLY_CUE, TALLY_REPEAT, FIRST, NOTE],
}
P.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("reply_feedback_gap", seed["version"], len(CUES), "cues")
