"""The "need Max" impasse was FALSE — the agent ALREADY HOLDS Max.

Wave 16 ended with a HumanImpasse: held ops {Minus,Div,Pow,Plus,Times} couldn't
express reliability_to_weight's below-chance max(0,.) clamp -> "needs a Max
primitive". But Max { items } is ALREADY a Term in the agent's Rust vocabulary
(a variadic reduction) — the composer simply never OFFERED it (its op set was a
hand-picked binary subset). The fix is not to author Rust; it is to give the
agent its FULL held vocabulary, reductions included.

This driver, using only the agent's own faculties (compose_search_gated +
migrate_function, both already installed), STAGED:
  stage 1  free search (above-chance points) -> the core D = Div(Minus(acc,
           chance), Minus(1,chance))  [no Max needed]
  stage 2  offer the HELD Max/Min reductions, with D as an operand + Lit(0),
           gate on the FULL points (incl. below-chance) -> free search composes
           Max(Lit(0), D) = max(0,D); WIRE it as reliability_to_weight and run
           verify_faculty (the REAL test) as the final gate -> PASS.

The impasse dissolves: the migration COMPLETES with a primitive the agent already
owned. No Rust rebuild, no donkey. The lesson: offer the composer the agent's
whole held vocabulary, or it reports a false primitive gap.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_dissolves_max_impasse.py
"""
from __future__ import annotations
import importlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_modification import SelfModification


def _ts(t):
    if not isinstance(t, dict):
        return str(t)
    ty = t.get("type")
    if ty == "Var":
        return t["name"]
    if ty == "Lit":
        return str(t["value"])
    if "a" in t:
        return f"{ty}({_ts(t['a'])},{_ts(t['b'])})"
    return f"{ty}([{','.join(_ts(x) for x in t.get('items', []))}])"


def main() -> int:
    mod = SelfModification()
    print("=" * 90)
    print('THE "NEED MAX" IMPASSE WAS FALSE — THE AGENT ALREADY HOLDS Max { items }')
    print("=" * 90)

    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    SM = importlib.import_module("domains.self_migration")
    M = SM.Migrator(mod)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    V = lambda n: {"type": "Var", "name": n}
    L = lambda v: {"type": "Lit", "value": v}
    rel = lambda a, c: (a - c) / (1.0 - c)
    above = [(1.0, 0.1), (0.55, 0.1), (0.7, 0.2), (0.4, 0.1), (0.9, 0.3), (0.8, 0.25)]
    below = [(0.05, 0.1), (0.0, 0.1), (0.05, 0.2), (0.15, 0.4), (0.2, 0.5), (0.1, 0.3)]
    pts_above = [{"env": {"acc": a, "chance": c}, "expected": rel(a, c)} for a, c in above]
    pts_full = pts_above + [{"env": {"acc": a, "chance": c}, "expected": 0.0} for a, c in below]

    # ---- stage 1: free search composes the core D (no Max needed) ----------------
    print("\n  stage 1 — free search (above-chance points) composes the reliability-map core:")
    r1 = M.compose_search_gated(agent, pts_above, [V("acc"), V("chance"), L(1.0)],
                                ops=[("Minus", "ab"), ("Div", "ab"), ("Plus", "items"), ("Times", "items")],
                                max_depth=2)
    if not r1.get("found"):
        print(f"     unexpected: {r1.get('impasse')}")
        return 1
    D = r1["term"]
    print(f"     FOUND core (tried {r1['tried']}): D = {_ts(D)}")

    # ---- stage 2: OFFER the held Max/Min reductions; D + Lit(0) as operands;
    #               gate on FULL points; then the REAL test (verify_faculty) ------
    print("\n  stage 2 — offer the HELD Max/Min reductions (D, Lit0 as operands), FULL points,")
    print("            then the REAL test as the final gate:")
    fn_anchor = "    w = (acc - chance) / (1.0 - chance)\n    return float(max(0.0, w))"
    out = M.migrate_function(
        agent, "weighted_admissibility", "reliability_to_weight", fn_anchor,
        {"acc": "acc", "chance": "chance"}, pts_full,
        operands=[D, L(0.0)],
        ops=[("Max", "items"), ("Min", "items"), ("Plus", "items"),
             ("Times", "items"), ("Minus", "ab"), ("Div", "ab")],
        max_depth=2, want=4)
    print(f"     survivors (passed FULL points pre-filter): {out['n_survivors']}")
    for term, verdict in out["results"]:
        print(f"       {_ts(term)} -> real test: {verdict}")
    accepted = out.get("accepted")
    print(f"     ACCEPTED by the REAL test: {(_ts(accepted) if accepted else None)}")
    if out.get("impasse"):
        print(f"     impasse: {out['impasse']}")

    # safety: faculty restored
    mod.restore("domains/weighted_admissibility.py")
    for f in __import__("glob").glob(os.path.join(ROOT, "domains", "*.selfmod.bak")):
        os.remove(f)
    intact = "return float(max(0.0, w))" in open(os.path.join(ROOT, "domains", "weighted_admissibility.py")).read()
    print(f"     faculty intact after run: {intact}")

    ok = (accepted is not None) and intact
    print("\n" + "=" * 90)
    if ok:
        print("  PASS — the impasse DISSOLVED with a primitive the agent ALREADY OWNED. Offered its full held")
        print("  vocabulary (Max/Min reductions), free search composed Max(Lit0, D) = max(0,(acc-chance)/(1-chance)),")
        print("  the REAL test ACCEPTED it, and the migration of reliability_to_weight COMPLETES. No Rust rebuild,")
        print("  no donkey. Lesson: a 'need a primitive' impasse must be checked against the WHOLE held vocabulary")
        print("  first — the gap was the composer's op set, not the agent's primitives.")
    else:
        print("  FAIL — see above.")
    print("=" * 90)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
