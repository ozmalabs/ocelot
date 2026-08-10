"""Generic, agent-controlled ACT-ON-GAP — pick the next METHOD for a stalled frontier, as a graph Term.

The dual of gap_prioritiser's frontier pick, at the method level and entirely domain-agnostic. A frontier
(CapabilityAxis) has CANDIDATE operators (the methods that could investigate it, `candidate` edges), each
carrying the agent's OWN expertise about it — `expected_payoff`, the gain the agent's own measured history
leads it to expect from that method on this kind of bottleneck. When a method stalls, the agent picks the
NEXT method to try via a graph Term it owns — argmax over the UNTRIED candidates of expected_payoff. No
teacher: the agent brings its own expertise. As each tried method stalls it is marked, so the next argmax
ESCALATES to the next-most-promising untried one. Generic: ANY domain plugs in its operators + runners +
the agent's payoff beliefs; the policy ("use your expertise; escalate when a method stalls") is the Term.
"""
from __future__ import annotations

CANDIDATE_EDGE = "candidate"     # CapabilityAxis -> Operator (a method that could investigate the frontier)
EXPECTED_ATTR = "expected_payoff"  # the agent's expertise: the gain it expects from this method
TRIED_ATTR = "tried"             # 1.0 once the agent has tried this method on its frontier
_BIG = 1.0e9


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Nbrs(node, e): return {"type": "Neighbours", "node": node, "edge_type": e, "any_type": False}
def _Neg(a): return {"type": "Neg", "arg": a}
def _Times(items): return {"type": "Times", "items": list(items)}
def _Plus(items): return {"type": "Plus", "items": list(items)}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val}


def declare_candidate_production(substrate) -> None:
    try:
        substrate.add_production({"src": {"type": "CapabilityAxis", "var": "a"}, "edge_type": CANDIDATE_EDGE,
                                  "tgt": {"type": "Operator", "var": "b"}, "provenance": "act_on_gap:candidate"})
    except Exception:
        pass


def pick_next_method_term() -> dict:
    """argmax over the frontier's CANDIDATE operators of [ expected_payoff - tried*BIG ] — the agent's OWN
    expertise drives the choice (highest expected gain it believes from its history), never trying a method
    twice (tried=1 subtracts BIG). As each tried method stalls it is marked, so the next argmax ESCALATES
    to the next-most-promising untried one. No teacher. A graph Term-tree the agent owns; binds `ax`."""
    op = _V("op")
    score = _Plus([_Attr(op, EXPECTED_ATTR), _Neg(_Times([_Attr(op, TRIED_ATTR), _Lit(_BIG)]))])
    return _Argmax(_Nbrs(_V("ax"), CANDIDATE_EDGE), "op", score)


def pick_next_method(substrate, axis_id):
    """The agent's ACT decision, ENACTED: evaluate the pick Term over the frontier's candidates and return
    the operator node it chose (or None if every candidate is exhausted / there are none). Host I/O only —
    the DECISION is the Term."""
    op = substrate.evaluate(_Pred(pick_next_method_term()), {"ax": axis_id})
    if op is None:
        return None
    if float(substrate.node(op)["attrs"].get(TRIED_ATTR, 0.0) or 0.0) >= 1.0:
        return None                                              # the cheapest-untried argmax fell back to a tried one => exhausted
    return op


def mark_tried(substrate, op_id) -> None:
    substrate.set_attr(op_id, TRIED_ATTR, 1.0)
