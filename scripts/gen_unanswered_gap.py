#!/usr/bin/env python3
"""Emit seeds/unanswered_gap.json (tranche 22): the agent files its OWN
unanswered turns as concerns.

Measured on the production path (tranche 21, 120 natural turns): 66 replies
were the explicit error floor or nothing, and none of them filed a concern,
so the self-improvement loop never saw its commonest failure.
`note_unanswered_turn` files one SelfConcern{kind:'unanswered'} per EVIDENCE
CLASS: the (evidence_force, literal_form, interaction_mode,
interaction_relation, language_statement_act) signature of the turn's
communication interpretation. It files only once that class has gone
unanswered at least `min_recurrence` times (UnansweredGapPolicy, agent-
editable), and never twice for a class already held by a concern. "Unanswered"
is read off the graph: the turn's own `turn_outcome` datum is 'explicit_error'
(WorldAdapter.record_turn_outcome, written when the daemon completes the turn). The concern points about_message at the turn, so the
conversation replay treats it as the flagged probe, the turn that must change.

v1.1.0 (2026-10-10, long-session cost): same decision, cheaper evaluation.
Measured: this rule was the costliest in a long session (1.5 ms/turn at turn
25, 245 ms/turn at turn 150) because every unanswered message whose class
already had a concern was never marked noted and re-ran two scans over ALL
Messages on every re-match. Now (a) the "class already held" check, over the
few SelfConcerns, runs before the scans, so such a message is rejected
cheaply, and (b) the two scans enumerate NodesWhere(Message, turn_outcome,
'explicit_error') -- the unanswered messages only -- instead of every Message
(WorldAdapter.record_turn_outcome declares the attr index). The where clause
is a pure conjunction, so reordering it cannot change which bindings fire.

v2.0.0 (2026-10-10, conversation turn ring): the rule reads the SHAPE, not
the history. Only the last N turns stay attended (seeds/
conversation_turn_ring.json, the reading aperture applied to turns), so the
recurrence is held as a TurnShape{shape_kind:'unanswered', sig_*} per
evidence class: `tally_unanswered_class` folds each attended unanswered turn
into its class shape (has_member / member_of) while it is attended, and
`note_unanswered_turn` fires on the shape -- its oldest member (first_member,
marked by `mark_unanswered_shape_first_member` while that turn is attended;
it sits right after the tally so one rule pass folds a turn, marks the
shape's first member and files) once the class has min_recurrence members -- with
the same concern, content and about_message as before. Same decision as
v1.x: the class count, the oldest member and the no-concern-yet guard are
unchanged; only where they are read from changed.
Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/unanswered_gap.json"
SIG = ["evidence_force", "literal_form", "interaction_mode", "interaction_relation", "language_statement_act"]


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Ex(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def InNb(n, e): return {"type": "InNeighbours", "node": V(n), "edge_type": e}
def Or0(x): return {"type": "IfThenElse", "cond": Eq(x, L(None)), "then": L(""), "other": x}


def unanswered(m):
    # the turn's own terminal outcome, recorded mechanically when the daemon
    # completed it (WorldAdapter.record_turn_outcome). An error-candidate reply
    # Message is not evidence: a later faculty may have released a reply and
    # suppressed it (measured: goal-take turns carry one).
    return Eq(A(m, "turn_outcome"), L("explicit_error"))


def same_sig(i_a, i_b):
    return And(*[Eq(Or0(A(i_a, k)), Or0(A(i_b, k))) for k in SIG])


TALLY = {
    "name": "tally_unanswered_class",
    "comment": "Fold an attended unanswered turn into its evidence-class TurnShape (the conceptual tier the history rule reads).",
    "match": [["agent", "received", "m"], ["i", "interprets", "m"]],
    "where": And(
        Eq(A("m", "from"), L("interlocutor")),
        Eq(A("i", "schema"), L("communication_interpretation.v1")),
        unanswered("m"),
        Not(Eq(A("m", "unanswered_tallied"), L(1)))),
    "effects": [
        ["add_node_if_absent", "sh", "TurnShape", {
            "shape_kind": "unanswered", **{"sig_" + k: {"__term__": Or0(A("i", k))} for k in SIG}}],
        ["add_edge", "agent", "has_turn_shape", "sh"],
        ["add_edge", "sh", "has_member", "m"],
        ["add_edge", "m", "member_of", "sh"],
        ["set_attr", "m", "unanswered_tallied", 1],
    ],
}

def first_member_rule(kind):
    """The oldest member of a `kind` TurnShape is its first_member (the turn a
    concern about the class names), marked while that turn is attended. Owned
    by the shape seed and loaded right after its tally (rules run in load
    order within a pass)."""
    return {
        "name": "mark_%s_shape_first_member" % kind,
        "comment": "The oldest member of a %s TurnShape is its first_member, marked while that turn is attended." % kind,
        "match": [["agent", "received", "m"], ["m", "member_of", "sh"]],
        "where": And(
            Eq(A("sh", "shape_kind"), L(kind)),
            Not(Ex({"type": "Neighbours", "node": V("sh"), "edge_type": "first_member"}, "_f", L(True))),
            Eq(V("m"), {"type": "Argmin", "source": {"type": "Neighbours", "node": V("sh"), "edge_type": "has_member"},
                        "var_name": "x", "value": V("x"), "default": None})),
        "effects": [["add_edge", "sh", "first_member", "m"]],
    }


FIRST = first_member_rule("unanswered")

RULE = {
    "name": "note_unanswered_turn",
    "comment": "File the agent's own recurring unanswered turn class as an experiment-eligible concern (see seed description).",
    # v2.0.0: matched on the class SHAPE and its oldest member, not on every received turn
    "match": [["agent", "has_turn_shape", "sh"], ["sh", "first_member", "m"], ["i", "interprets", "m"],
              ["agent", "has_unanswered_gap_policy", "pol"]],
    "where": And(
        Eq(A("pol", "enabled"), L(1)),
        Eq(A("sh", "shape_kind"), L("unanswered")),
        Eq(A("i", "schema"), L("communication_interpretation.v1")),
        Not(Eq(A("m", "unanswered_gap_noted"), L(1))),
        # no concern already holds this class (SelfConcerns are few)
        Not(Ex({"type": "NodesOfType", "node_type": "SelfConcern"}, "sc2", And(
            Eq(A("sc2", "kind"), L("unanswered")),
            *[Eq(Or0(A("sc2", "sig_" + k)), Or0(A("i", k))) for k in SIG]))),
        # the class has gone unanswered at least min_recurrence times
        {"type": "Gte", "a": {"type": "Count", "source": {"type": "Neighbours", "node": V("sh"), "edge_type": "has_member"}},
         "b": A("pol", "min_recurrence")}),
    "effects": [
        ["set_attr", "m", "unanswered_gap_noted", 1],
        ["add_node", "sc", "SelfConcern", {
            "status": "noted", "source": "implicit", "kind": "unanswered",
            "content": {"__term__": {"type": "StringConcat", "parts": [
                L("I could not respond to a "), Or0(A("i", "literal_form")), L(" "), Or0(A("i", "evidence_force")),
                L(" turn (relation '"), Or0(A("i", "interaction_relation")), L("', act '"),
                Or0(A("i", "language_statement_act")), L("'), e.g. \""), A("m", "text"), L("\"")]}},
            **{"sig_" + k: {"__term__": Or0(A("i", k))} for k in SIG}}],
        ["add_edge", "agent", "has_self_concern", "sc"],
        ["add_edge", "sc", "about_message", "m"],
    ],
}

seed = {
    "id": "unanswered_gap",
    "version": "2.0.0",
    "depends_on": ["gap_awareness", "conversation_turn_ring"],
    "description": __doc__,
    "nodes": [{"local_id": 0, "type": "UnansweredGapPolicy", "attrs": {
        "name": "unanswered_gap", "enabled": 1, "min_recurrence": 2,
        "description": "Agent-held policy: how many unanswered turns of one evidence class make a concern."}}],
    "edges": [{"src": {"role": "agent_root"}, "type": "has_unanswered_gap_policy", "tgt": {"local": 0}, "attrs": {}}],
    "productions": [],
    "rules": [TALLY, FIRST, RULE],
}
P.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("unanswered_gap", seed["version"])
