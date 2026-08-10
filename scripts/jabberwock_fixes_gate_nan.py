"""Fix the gate's NaN/inf hole — exposed by offering the full vocabulary.

With the full held vocabulary the search reaches distance ops (DtwTo, ...) that
return inf; 0*inf = NaN, and in Python `NaN > tol` is False, so the tolerance
check `if abs(val-expected) > tol: return False` let a NaN-valued (identically
useless) term PASS the gate as a false positive. The hand-picked arithmetic
subset never produced inf/NaN, so the hole was latent. Fix (agent self-edits both
gates): reject any non-finite value before the tolerance test.

Then re-demonstrate: DEFAULT full vocabulary (NO ops=) composes a CORRECT core and
the clamp, both passing the gate and the REAL test.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_fixes_gate_nan.py
"""
from __future__ import annotations
import importlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_modification import SelfModification

REL = "domains/self_migration.py"

COMPOSE_GATE_OLD = '''                if abs(val - pt["expected"]) > tol:
                    return False
            return True

        tried = 0'''
COMPOSE_GATE_NEW = '''                if not (-1e308 < val < 1e308) or abs(val - pt["expected"]) > tol:
                    return False                          # reject NaN/inf (e.g. 0*inf) too
            return True

        tried = 0'''

MIGRATE_GATE_OLD = '''                if abs(v - pt["expected"]) > tol:
                    return False
            return True

        survivors = []'''
MIGRATE_GATE_NEW = '''                if not (-1e308 < v < 1e308) or abs(v - pt["expected"]) > tol:
                    return False                          # reject NaN/inf (e.g. 0*inf) too
            return True

        survivors = []'''


def _ts(t):
    if not isinstance(t, dict):
        return str(t)
    ty = t.get("type")
    if ty == "Var":
        return t["name"]
    if ty == "Lit":
        return str(t["value"])
    if "arg" in t:
        return f"{ty}({_ts(t['arg'])})"
    if "a" in t:
        return f"{ty}({_ts(t['a'])},{_ts(t['b'])})"
    return f"{ty}([{','.join(_ts(x) for x in t.get('items', []))}])"


def main() -> int:
    mod = SelfModification()
    print("=" * 92)
    print("FIX THE GATE'S NaN/inf HOLE (exposed by the full vocabulary)")
    print("=" * 92)
    for label, old, new in [("compose gate: reject non-finite", COMPOSE_GATE_OLD, COMPOSE_GATE_NEW),
                            ("migrate gate: reject non-finite", MIGRATE_GATE_OLD, MIGRATE_GATE_NEW)]:
        if new in mod.read(REL):
            print(f"  [skip] {label} (already applied)")
            continue
        r = mod.edit(REL, old, new)
        print(f"  [edit] {label}: ok={r.get('ok')}{' ROLLED BACK' if r.get('rolled_back') else ''}")
        if not r.get("ok"):
            print(f"         {r.get('result')}")
            return 1
    mod.reload_python("domains.self_migration")

    SM = importlib.import_module("domains.self_migration")
    M = SM.Migrator(mod)
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)

    V = lambda n: {"type": "Var", "name": n}
    L = lambda v: {"type": "Lit", "value": v}
    rel = lambda a, c: (a - c) / (1.0 - c)
    above = [(1.0, 0.1), (0.55, 0.1), (0.7, 0.2), (0.4, 0.1), (0.9, 0.3), (0.8, 0.25)]
    below = [(0.05, 0.1), (0.0, 0.1), (0.05, 0.2), (0.15, 0.4), (0.2, 0.5)]
    pts_above = [{"env": {"acc": a, "chance": c}, "expected": rel(a, c)} for a, c in above]
    pts_full = pts_above + [{"env": {"acc": a, "chance": c}, "expected": 0.0} for a, c in below]

    print("\n  stage 1 — DEFAULT full vocabulary (NO ops=) composes a CORRECT core:")
    r1 = M.compose_search_gated(agent, pts_above, [V("acc"), V("chance"), L(1.0)], max_depth=2)
    D = r1.get("term")
    print(f"     {('FOUND (tried %d): ' % r1['tried']) + _ts(D) if D else 'IMPASSE: ' + r1.get('impasse', '')}")
    # sanity: the found core must actually reproduce rel on the above points
    if D:
        bad = [(pt["env"], M.compose_search_gated.__self__ and agent.inner.evaluate(D, pt["env"]), pt["expected"])
               for pt in pts_above
               if abs(float(agent.inner.evaluate(D, pt["env"])) - pt["expected"]) > 1e-6]
        print(f"     core verified on above-points: {not bad}")
        if bad:
            print(f"     STILL SPURIOUS: {bad[:2]}")
            return 1
    else:
        return 1

    print("\n  stage 2 — DEFAULT full vocabulary (NO ops=) composes the clamp + REAL-test gate:")
    fn_anchor = "    w = (acc - chance) / (1.0 - chance)\n    return float(max(0.0, w))"
    out = M.migrate_function(agent, "weighted_admissibility", "reliability_to_weight", fn_anchor,
                             {"acc": "acc", "chance": "chance"}, pts_full,
                             operands=[D, L(0.0)], max_depth=2, want=4)
    acc = out.get("accepted")
    print(f"     ACCEPTED by the REAL test: {_ts(acc) if acc else out.get('impasse')}")

    mod.restore("domains/weighted_admissibility.py")
    for f in __import__("glob").glob(os.path.join(ROOT, "domains", "*.selfmod.bak")):
        os.remove(f)
    intact = "return float(max(0.0, w))" in open(os.path.join(ROOT, "domains", "weighted_admissibility.py")).read()
    print(f"     faculty intact after run: {intact}")

    ok = (D is not None and acc is not None and intact)
    print("\n" + "=" * 92)
    print(f"  {'PASS' if ok else 'FAIL'} — gate now rejects NaN/inf, so the full vocabulary can't slip a "
          f"degenerate term through. With NO hand-picked ops the composer finds a CORRECT core and the clamp "
          f"and passes the REAL test. Offering everything surfaced (and the agent fixed) a latent gate hole. No LLM.")
    print("=" * 92)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
