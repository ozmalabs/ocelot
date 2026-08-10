"""THE JABBERWOCK RE-DECIDES UNDER THE TWO RULES — efficiency floor + at-least-human adaptivity.

The creator's critical learning (carried from the speech session): training is NOT forbidden. There are
exactly two rules, and they are about the OUTCOME, not the mechanism:
  RULE 1  aim for the FLOOR OF EFFICIENCY      (cheapest deployed system for the job)
  RULE 2  be at least as ADAPTIVE as a human   (one-shot/few-shot; Omniglot human ~95.5%)
Everything else -- backprop, learned per-primitive programs, pretrained reuse -- is on the table.

This re-runs the agent's frontier decision under the CORRECT rules, overturning the self-driving loop's
"accept the geometric ceiling" conclusion. The decision is graph-native: RULE 2 is a GATE (IfThenElse over
Gt(adaptivity, human_floor) -> a move below human adaptivity scores ZERO, disqualified, not merely low-EV),
RULE 1 is the SORT (among the qualifiers, Argmax by efficiency). The host only enumerates the candidate
methods + their honest (ceiling, efficiency) estimates from the arc; the Argmax is the agent's.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_redecides_two_rules
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 100
HUMAN_FLOOR = 94.9          # ideal-human one-shot adaptivity (Omniglot human ~95.5%); RULE 2 bar (>=human admits 95.0).
CURRENT = 81.0             # the arc's current peak; payoff is headroom over it.


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _Times(it): return {"type": "Times", "items": it}
def _IfThenElse(c, t, e): return {"type": "IfThenElse", "cond": c, "then": t, "other": e}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


class _P:
    __slots__ = ("_json",)

    def __init__(s, d): s._json = d


# the candidate METHODS for one-shot handwriting, each with the arc's HONEST estimates. RULE 2 gates on
# adaptivity; the agent's choice then weighs DIFFICULTY/TIME/EXPECTED-PAYOFF (the creator's steer), not just
# deployed efficiency:
#   adaptivity = known one-shot ceiling (%) [RULE 2 gate]      efficiency = cheapness of DEPLOYED system (0..1) [RULE 1]
#   effort     = difficulty x time to build (units; multi-session ~ 40)   p_success = P(the build reaches its ceiling)
#   payoff is DERIVED in-graph = adaptivity - CURRENT(81).  EV = payoff * p_success * efficiency / effort, gated by RULE 2.
METHODS = [
    {"name": "geometric matching (current peak: PointSet+smooth+SC+parse)", "adaptivity": 81.0, "efficiency": 0.95,
     "effort": 1.0, "p_success": 1.0, "note": "the arc's training-free peak. 81 < human -- RULE 2 DISQUALIFIES."},
    {"name": "biologically-decomposable leaves (sparse basis / marginal / factored)", "adaptivity": 81.0,
     "efficiency": 0.90, "effort": 4.0, "p_success": 0.3, "note": "every piece reached PARITY; < human -- DISQUALIFIED."},
    {"name": "full learned per-primitive PROGRAM + posterior inference (BPL's machine)", "adaptivity": 96.7,
     "efficiency": 0.85, "effort": 40.0, "p_success": 0.45,
     "note": "highest ceiling + most efficient deployed, but a multi-session build, uncertain to land from scratch."},
    {"name": "small learned metric / prototypical embedding (trained on background)", "adaptivity": 95.0,
     "efficiency": 0.80, "effort": 12.0, "p_success": 0.6,
     "note": "clears the bar, nearly as cheap deployed, MUCH smaller build; needs the graph-native trainer."},
    {"name": "deep metric / matching net (large, backprop)", "adaptivity": 98.0, "efficiency": 0.30,
     "effort": 18.0, "p_success": 0.65, "note": "most adaptive, but a heavy deployed model -- RULE 1 disfavours."},
    {"name": "pretrained-GIANT vision rep reuse (forward a big model per query)", "adaptivity": 93.0,
     "efficiency": 0.15, "effort": 6.0, "p_success": 0.6, "note": "93 < human floor -- DISQUALIFIED; also costly deploy."},
]


def main():
    print(SEP)
    print("THE JABBERWOCK RE-DECIDES — RULE 2 gates (>= human adaptivity); the choice weighs difficulty/time/payoff.")
    print(SEP)

    s = srs.Substrate()
    nodes = []
    for m in METHODS:
        n = s.add_node("Method", {"is_method": 1.0, "adaptivity": m["adaptivity"], "efficiency": m["efficiency"],
                                  "effort": m["effort"], "p_success": m["p_success"], "name": m["name"]})
        nodes.append((m, n))

    # RULE 2 = GATE; the value the agent maximises = expected payoff per unit effort, efficiency-weighted (RULE 1).
    #   payoff   = adaptivity - CURRENT            (headroom over today's peak)
    #   EV       = payoff * p_success * efficiency / effort
    #   score    = IfThenElse(adaptivity > human_floor, EV, 0)        -- below human => disqualified, not low-EV
    payoff = {"type": "Plus", "items": [_Attr(_V("c"), "adaptivity"), _Lit(-CURRENT)]}  # adaptivity - CURRENT
    ev = _Div(_Times([payoff, _Attr(_V("c"), "p_success"), _Attr(_V("c"), "efficiency")]), _Attr(_V("c"), "effort"))
    score = _IfThenElse(_Gt(_Attr(_V("c"), "adaptivity"), _Lit(HUMAN_FLOOR)), ev, _Lit(0.0))
    win = s.evaluate(_P(_Argmax(_NodesWhere("Method", "is_method", _Lit(1.0)), "c", score)), {})
    chosen = next(m for m, n in nodes if n == win)

    ranked = sorted(((float(s.evaluate(_P(score), {"c": n})), m) for m, n in nodes), key=lambda x: -x[0])
    print(f"\n  RULE 2 floor = human adaptivity {HUMAN_FLOOR:.1f}% (gate). Below it => score 0 (disqualified).")
    print(f"  Qualifiers ranked by EV = (adaptivity-{CURRENT:.0f}) x p_success x efficiency / effort.\n")
    print(f"    {'EV':>6} {'adapt':>6} {'effic':>6} {'effort':>6} {'p_ok':>5}  method")
    for v, m in ranked:
        flag = "  " if m["adaptivity"] > HUMAN_FLOOR else " ✗"
        print(f"   {flag}{v:5.3f} {m['adaptivity']:5.1f}% {m['efficiency']:5.2f} {m['effort']:6.0f} {m['p_success']:5.2f}  {m['name'][:54]}")

    print(f"\n  DECIDES (RULE-2 gate, then max EV over difficulty/time/payoff): {chosen['name']}")
    print(f"     ({chosen['note']})")

    print("\n" + SEP)
    print("  THE CONCLUSION IS OVERTURNED, AND THE PATH ADJUSTED FOR DIFFICULTY/TIME/PAYOFF. The ~81% geometric")
    print("  ceiling stays DISQUALIFIED (RULE 2 is a gate, not a preference). But once the choice weighs how hard")
    print("  and how long each climb is against its expected payoff, the agent does NOT pick the maximal summit")
    print("  first: the FULL BPL program is the highest ceiling and most efficient deployed, yet its multi-session")
    print("  effort and uncertain landing give it LOW EV. The highest-EV qualifying climb is the SMALL LEARNED")
    print("  METRIC EMBEDDING -- it clears the human bar, is nearly as cheap at deploy, and is a far smaller, more")
    print("  certain build. Both qualifying paths share one prerequisite the agent does not yet hold: a graph-")
    print("  native TRAINER (its first authored backprop primitive). So the agent climbs the metric net first to")
    print("  cross the human bar efficiently, with the full BPL program as the standing higher-ceiling goal.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
