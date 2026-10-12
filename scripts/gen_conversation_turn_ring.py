#!/usr/bin/env python3
"""Emit seeds/conversation_turn_ring.json: the reading aperture applied to
conversation turns (the ring, its retention salience and its one-shot widen).

The conversation keeps the last N concluded interlocutor turns ATTENDED
(`agent received m`), N from the conversational ApertureBudget row's
turn_capacity_* attrs via the SAME held reading_derive_trace_capacity
Program the reading ring uses (domains/reading_norms.effective_turn_capacity,
seeds/reading_aperture.json v1.3.0). domains/conversation_aperture.
enforce_turn_buffer (mechanical, the reading_scope.enforce_trace_buffer twin)
evicts the lowest-salience, oldest eligible turn: `received` is replaced by
`agent remembers m`, nothing else changes. Older turns survive conceptually
in the TurnShape tier, which the shape-owning seeds build and read
(unanswered_gap, comprehension_health).

Rules (graph decisions; Python only executes):
  * turn_salience_from_outcome -- a concluded turn's retention salience, from
    held TurnRingPolicy weights (unanswered > reader disagreement > other).
    It is written only once the turn has been folded into its shapes, so a
    turn is never evicted before the shape tier holds it. A turn with no
    salience is never evicted.
  * conversation_widen_turn_capacity_once -- the reading ladder's rung 1: an
    eviction at or above the held turn_widen_salience_threshold widens the
    ring once (TurnRing.capacity_widened).
Each shape-owning seed marks its own shapes' first_member (the oldest
member, while it is attended) right after its tally, because rules run in
load order within a pass and the ring loads before the shape seeds.
Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/conversation_turn_ring.json"


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Nb(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e}
def InNb(n, e): return {"type": "InNeighbours", "node": V(n), "edge_type": e}
def Ex(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def T(x): return {"__term__": x}
def Any(t): return Ex({"type": "NodesOfType", "node_type": t}, "_any", L(True))


# A turn is folded into its shapes when every shape that applies to it has
# tallied it. A shape kind whose owning seed is not loaded does not block.
UNANSWERED_FOLDED = Or(
    Not(Eq(A("m", "turn_outcome"), L("explicit_error"))),
    Eq(A("m", "unanswered_tallied"), L(1)),
    Not(Any("UnansweredGapPolicy")),
    Not(Ex(InNb("m", "interprets"), "i", Eq(A("i", "schema"), L("communication_interpretation.v1")))))
DIVERGENCE_FOLDED = Or(
    Not(Eq(A("m", "speech_act_divergence"), L(1.0))),
    Eq(A("m", "divergence_tallied"), L(1)),
    Not(Any("HealthNorm")))

SALIENCE = {
    "name": "turn_salience_from_outcome",
    "comment": "A concluded, shape-folded interlocutor turn gets its ring-retention salience from the held TurnRingPolicy weights (see seed description).",
    "match": [["agent", "received", "m"], ["agent", "has_turn_ring_policy", "pol"]],
    "where": And(
        Eq(A("pol", "enabled"), L(1)),
        Eq(A("m", "from"), L("interlocutor")),
        Not(Eq(A("m", "turn_outcome"), L(None))),
        Eq(A("m", "turn_salience"), L(None)),
        UNANSWERED_FOLDED, DIVERGENCE_FOLDED),
    "effects": [["set_attr", "m", "turn_salience", T(
        Ite(Eq(A("m", "turn_outcome"), L("explicit_error")), A("pol", "salience_unanswered"),
            Ite(Eq(A("m", "speech_act_divergence"), L(1.0)), A("pol", "salience_divergent"),
                A("pol", "salience_default"))))]],
}

BUDGET = {"type": "Argmax", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "ApertureBudget"},
                                       "var_name": "b", "predicate": Eq(A("b", "register"), L("conversational"))},
          "var_name": "x", "value": L(0), "default": None}
WIDEN = {
    "name": "conversation_widen_turn_capacity_once",
    "comment": "Rung 1 of the reading overflow ladder, for turns: an eviction at or above the held turn_widen_salience_threshold widens the turn ring once.",
    "match": [["agent", "has_turn_ring", "ring"]],
    "where": And(
        Not(Eq(A("ring", "capacity_widened"), L(1.0))),
        Not(Eq(A("ring", "max_evicted_salience"), L(None))),
        {"type": "Let", "name": "budget", "value": BUDGET, "body": And(
            Not(Eq(V("budget"), L(None))),
            Not(Eq(A("budget", "turn_widen_salience_threshold"), L(None))),
            {"type": "Gte", "a": A("ring", "max_evicted_salience"), "b": A("budget", "turn_widen_salience_threshold")})}),
    "effects": [["set_attr", "ring", "capacity_widened", 1.0]],
}

seed = {
    "id": "conversation_turn_ring",
    "version": "1.0.0",
    "depends_on": ["reading_aperture"],
    "description": __doc__,
    "nodes": [
        {"local_id": 0, "type": "TurnRingPolicy", "attrs": {
            "name": "conversation_turn_ring", "enabled": 1,
            "salience_unanswered": 1.0, "salience_divergent": 0.5, "salience_default": 0.0,
            "description": "Agent-held retention weights for the conversation turn ring: an unanswered turn is kept longest, then a turn the two readers disagreed on, then the rest. Editing these changes which turns stay attended."}},
        {"local_id": 1, "type": "TurnRing", "attrs": {
            "name": "conversation", "description": "The conversation's turn ring: eviction pressure (traces_evicted, max_evicted_salience) and its one-shot widen (capacity_widened)."}}],
    "edges": [
        {"src": {"role": "agent_root"}, "type": "has_turn_ring_policy", "tgt": {"local": 0}, "attrs": {}},
        {"src": {"role": "agent_root"}, "type": "has_turn_ring", "tgt": {"local": 1}, "attrs": {}}],
    "productions": [],
    "rules": [SALIENCE, WIDEN],
}
P.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("conversation_turn_ring", seed["version"])
