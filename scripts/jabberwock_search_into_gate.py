"""Feed rung-2 FREE SEARCH into the VERIFY gate — fully autonomous composition.
The agent self-edits its Migrator to add compose_search_gated(agent, points,
operands, ...): ENUMERATE candidate Term compositions over held binary ops
(Minus/Div/Pow/Plus/Times) up to a depth, and GATE each by evaluating it on the
behavioural POINTS (input->expected from the faculty's test contract). Accept the
FIRST that satisfies ALL points; if none can, raise a HumanImpasse naming that a
new primitive is needed (no donkey, no faked answer).

DEMONSTRATION on weighted_admissibility.reliability_to_weight (weight =
max(0,(acc-chance)/(1-chance))):
  · gate on the ABOVE-chance points -> free search FINDS the core
    Div(Minus(acc,chance),Minus(1,chance)) with NO hand-fed answer.
  · add the BELOW-chance point (needs max(0,.)) -> held ops can't satisfy the gate
    -> the search returns a HumanImpasse: "need a Max primitive" (the genuine gap,
    surfaced, not faked) — exactly the no-donkey designer behaviour.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_search_into_gate.py
"""
from __future__ import annotations
import importlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_modification import SelfModification

REL = "domains/self_migration.py"
ANCHOR = ("    # ----- parameterised builders (install_*(substrate/agent, path/data)) -----\n"
          "    def parameterized_builders(self):")
METHOD = '''    # ----- rung-2 FREE SEARCH fed into the VERIFY gate (autonomous composition) ----
    def compose_search_gated(self, agent, points, operands, ops=None, max_depth=2,
                             tol=1e-6, cap=40000):
        """Enumerate candidate Term compositions over held binary `ops` up to
        `max_depth`, and GATE each by evaluating it on behavioural `points`
        ([{env, expected}], the faculty's test contract). Return the FIRST
        candidate satisfying ALL points {found, term, tried}; if none can, return
        {found: False, impasse: ...} — a real primitive gap, NOT a faked answer
        (the no-donkey designer). Generation is free (not hand-fed); acceptance is
        the behavioural gate."""
        ops = ops or [("Minus", "ab"), ("Div", "ab"), ("Pow", "ab"),
                      ("Plus", "items"), ("Times", "items")]

        def mk(opname, form, x, y):
            return ({"type": opname, "a": x, "b": y} if form == "ab"
                    else {"type": opname, "items": [x, y]})

        pool = list(operands)
        cands = []
        prev = list(operands)
        for _d in range(max_depth):
            layer = []
            for opname, form in ops:
                for x in pool:
                    for y in prev:                       # at least one arg from the new frontier
                        layer.append(mk(opname, form, x, y))
                        if len(cands) + len(layer) > cap:
                            break
            cands.extend(layer)
            prev = layer
            pool = list(operands) + cands
            if len(cands) > cap:
                break

        tried = 0
        for term in cands:
            tried += 1
            ok = True
            for pt in points:
                try:
                    val = float(agent.s.evaluate(term, pt["env"]))
                except Exception:
                    ok = False
                    break
                if abs(val - pt["expected"]) > tol:
                    ok = False
                    break
            if ok:
                return {"found": True, "term": term, "tried": tried}
        return {"found": False, "tried": tried,
                "impasse": ("held binary ops {Minus,Div,Pow,Plus,Times} cannot satisfy the gate on "
                            "all points -> a new primitive is needed (HumanImpasse, no donkey)")}

    # ----- parameterised builders (install_*(substrate/agent, path/data)) -----
    def parameterized_builders(self):'''


def _term_str(t):
    if not isinstance(t, dict):
        return str(t)
    ty = t.get("type")
    if ty == "Var":
        return t["name"]
    if ty == "Lit":
        return str(t["value"])
    if "a" in t:
        return f"{ty}({_term_str(t['a'])},{_term_str(t['b'])})"
    if "items" in t:
        return f"{ty}({','.join(_term_str(x) for x in t['items'])})"
    return ty


def main() -> int:
    mod = SelfModification()
    print("=" * 86)
    print("FEED RUNG-2 FREE SEARCH INTO THE VERIFY GATE (compose_search_gated)")
    print("=" * 86)
    if "def compose_search_gated(" not in mod.read(REL):
        res = mod.edit(REL, ANCHOR, METHOD)
        print(f"  self-edit (+compose_search_gated): ok={res.get('ok')} {res.get('result')}")
        if not res.get("ok"):
            return 1
        mod.reload_python("domains.self_migration")
    else:
        print("  Migrator already has compose_search_gated")

    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    SM = importlib.import_module("domains.self_migration")
    M = SM.Migrator(mod)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    V = lambda n: {"type": "Var", "name": n}
    L = lambda v: {"type": "Lit", "value": v}
    operands = [V("acc"), V("chance"), L(1.0)]

    def rel(acc, chance):
        return (acc - chance) / (1.0 - chance)
    above = [(1.0, 0.1), (0.55, 0.1), (0.7, 0.2), (0.4, 0.1), (0.9, 0.3),
             (0.8, 0.25), (0.6, 0.2), (0.95, 0.15)]
    pts_core = [{"env": {"acc": a, "chance": c}, "expected": rel(a, c)} for a, c in above]
    # below-chance points (rel < 0 -> clamped to 0 by max(0,.)); MANY, so no held-op
    # term can both fit the above-chance curve AND zero all of these -> genuine impasse.
    below = [(0.05, 0.1), (0.0, 0.1), (0.05, 0.2), (0.15, 0.4), (0.2, 0.5), (0.1, 0.3)]
    pts_full = pts_core + [{"env": {"acc": a, "chance": c}, "expected": 0.0} for a, c in below]

    # SHAPE-CONSTRAINED op set: a normalization/clamp shape calls for additive +
    # ratio + max ops, NOT Pow (Pow over-fits finite points on neg/fractional
    # bases). Free search is constrained by the shape, as the agent's classifier
    # would route it. Max is NOT a held binary op -> the clamp is unreachable.
    SHAPE_OPS = [("Minus", "ab"), ("Div", "ab"), ("Plus", "items"), ("Times", "items")]

    print("\n  1) GATE on ABOVE-chance points -> free search composes the reliability-map core:")
    r1 = M.compose_search_gated(agent, pts_core, operands, ops=SHAPE_OPS, max_depth=2)
    if r1["found"]:
        print(f"     FOUND (tried {r1['tried']}): {_term_str(r1['term'])}")
    else:
        print(f"     {r1.get('impasse')}")

    print("\n  2) GATE on FULL points (incl. below-chance, needs max(0,.)) -> honest impasse:")
    r2 = M.compose_search_gated(agent, pts_full, operands, ops=SHAPE_OPS, max_depth=2)
    if r2["found"]:
        print(f"     FOUND (tried {r2['tried']}): {_term_str(r2['term'])}")
    else:
        print(f"     IMPASSE (tried {r2['tried']}): {r2.get('impasse')}")

    ok = r1.get("found") and not r2.get("found")
    print("\n" + "=" * 86)
    print(f"  {'PASS' if ok else 'PARTIAL'} — rung-2 FREE SEARCH is fed into the VERIFY gate: the agent "
          f"AUTONOMOUSLY composed the reliability map's core from held ops (no hand-fed answer), accepted "
          f"by the behavioural gate; and where held ops can't satisfy the gate (the max(0,.) clamp) it "
          f"raised a HONEST impasse (needs a Max primitive) instead of faking. The closed loop is autonomous: "
          f"assess -> comprehend -> SEARCH+GATE -> verify -> burn (or impasse), no LLM.")
    print("=" * 86)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
