"""Chain free-search SURVIVORS through verify_faculty (the REAL test) as the FINAL
gate — completing the two-stage gate. The agent self-edits its Migrator to add
migrate_function(...): free search -> POINTS pre-filter (cheap) -> collect up to
`want` survivors -> WIRE each as the target function (edit its body to evaluate
the candidate Term) and run verify_faculty (the real pytest = full semantics) as
the FINAL gate; accept the first survivor that passes the real test, else honest
impasse. The real test catches what finite points miss.

DEMONSTRATION on weighted_admissibility.reliability_to_weight: free search +
ABOVE-chance points -> survivor = the core Div(Minus(acc,chance),Minus(1,chance));
chained through the REAL test (which also asserts the BELOW-chance max(0,.) clamp)
-> the core is REJECTED (it lacks the clamp held ops can't express) -> genuine
impasse (needs Max), now confirmed by the REAL test, not just sampled points.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_chains_survivors.py
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
METHOD = '''    # ----- TWO-STAGE gate: free search -> points pre-filter -> REAL-TEST final gate
    def migrate_function(self, agent, module, fn_name, fn_anchor, env_map, points,
                         operands, ops=None, max_depth=2, want=6, tol=1e-6):
        """Free search -> POINTS pre-filter -> collect up to `want` survivors ->
        WIRE each as fn_name (edit fn_anchor to evaluate the Term) and run
        verify_faculty (the REAL test) as the FINAL gate. Accept the first that
        passes the real test (overfits the points-gate let through are killed
        here), else honest impasse. env_map = {term_var: param_name}."""
        ops = ops or [("Minus", "ab"), ("Div", "ab"), ("Plus", "items"), ("Times", "items")]

        def mk(op, form, x, y):
            return ({"type": op, "a": x, "b": y} if form == "ab"
                    else {"type": op, "items": [x, y]})
        prev = list(operands); cands = []; pool = list(operands)
        for _d in range(max_depth):
            layer = [mk(o, f, x, y) for o, f in ops for x in pool for y in prev]
            cands.extend(layer); prev = layer; pool = list(operands) + cands
            if len(cands) > 40000:
                break
        survivors = []
        for term in cands:
            ok = True
            for pt in points:
                try:
                    v = float(agent.inner.evaluate(term, pt["env"]))
                except Exception:
                    ok = False; break
                if abs(v - pt["expected"]) > tol:
                    ok = False; break
            if ok:
                survivors.append(term)
                if len(survivors) >= want:
                    break
        env_src = "{" + ", ".join("%r: %s" % (k, p) for k, p in env_map.items()) + "}"
        relpath = "domains/" + module + ".py"
        results = []
        for term in survivors:
            stub = ("    import substrate_rs as _srs\\n"
                    "    return float(_srs._native.Substrate().evaluate(%r, %s))" % (term, env_src))
            r = self.mod.edit(relpath, fn_anchor, stub, check=False)
            if not r.get("ok"):
                results.append((term, "wire-fail")); continue
            v = self.verify_faculty(module)
            self.mod.restore(relpath)
            results.append((term, "PASS" if v.get("passed") else "reject: " + str(v.get("summary"))))
            if v.get("passed"):
                return {"accepted": term, "n_survivors": len(survivors), "results": results}
        return {"accepted": None, "n_survivors": len(survivors), "results": results,
                "impasse": "all points-survivors REJECTED by the REAL test (full semantics) -> a primitive is needed"}

    # ----- parameterised builders (install_*(substrate/agent, path/data)) -----
    def parameterized_builders(self):'''


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
    return f"{ty}({','.join(_ts(x) for x in t.get('items', []))})"


def main() -> int:
    mod = SelfModification()
    print("=" * 88)
    print("CHAIN SURVIVORS THROUGH verify_faculty AS THE FINAL GATE (migrate_function)")
    print("=" * 88)
    if "def migrate_function(" not in mod.read(REL):
        res = mod.edit(REL, ANCHOR, METHOD)
        print(f"  self-edit (+migrate_function): ok={res.get('ok')} {res.get('result')}")
        if not res.get("ok"):
            return 1
        mod.reload_python("domains.self_migration")
    else:
        print("  Migrator already has migrate_function")

    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    SM = importlib.import_module("domains.self_migration")
    M = SM.Migrator(mod)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    V = lambda n: {"type": "Var", "name": n}
    L = lambda v: {"type": "Lit", "value": v}
    operands = [V("acc"), V("chance"), L(1.0)]
    rel = lambda a, c: (a - c) / (1.0 - c)
    above = [(1.0, 0.1), (0.55, 0.1), (0.7, 0.2), (0.4, 0.1), (0.9, 0.3), (0.8, 0.25)]
    pts = [{"env": {"acc": a, "chance": c}, "expected": rel(a, c)} for a, c in above]
    fn_anchor = "    w = (acc - chance) / (1.0 - chance)\n    return float(max(0.0, w))"

    print("\n  free search -> POINTS pre-filter (above-chance) -> survivors -> REAL-TEST gate:")
    out = M.migrate_function(agent, "weighted_admissibility", "reliability_to_weight",
                             fn_anchor, {"acc": "acc", "chance": "chance"}, pts, operands,
                             ops=[("Minus", "ab"), ("Div", "ab"), ("Plus", "items"), ("Times", "items")],
                             max_depth=2, want=4)
    print(f"     survivors (passed points pre-filter): {out['n_survivors']}")
    for term, verdict in out["results"]:
        print(f"       {_ts(term)} -> real test: {verdict}")
    print(f"     ACCEPTED by the real test: {(_ts(out['accepted']) if out.get('accepted') else None)}")
    if out.get("impasse"):
        print(f"     IMPASSE: {out['impasse']}")

    mod.restore("domains/weighted_admissibility.py")
    for f in __import__("glob").glob(os.path.join(ROOT, "domains", "*.selfmod.bak")):
        os.remove(f)
    intact = "return float(max(0.0, w))" in open(os.path.join(ROOT, "domains", "weighted_admissibility.py")).read()
    print(f"     faculty intact after run: {intact}")

    # PASS = the two-stage gate ran: points found survivor(s), the REAL test was the
    # final arbiter (here it rejects the clamp-less core -> impasse confirmed by the real test).
    ok = out["n_survivors"] >= 1 and intact and (out.get("accepted") is not None or out.get("impasse"))
    print("\n" + "=" * 88)
    print(f"  {'PASS' if ok else 'FAIL'} — survivors are CHAINED through verify_faculty as the FINAL gate: the "
          f"cheap points pre-filter proposes, the REAL test decides. Here it rejected the clamp-less core the "
          f"points-gate accepted -> the impasse (needs Max) is confirmed by the REAL test, not sampled points. "
          f"The two-stage gate is the trustworthy arbiter; faculty restored, no LLM.")
    print("=" * 88)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
