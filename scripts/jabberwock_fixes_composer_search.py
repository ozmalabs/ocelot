"""Make the full-vocabulary composer TRACTABLE: gate lazily, stop at first hit.

Offering the agent's full held vocabulary (39 numeric ops) exploded the eager
depth-2 build, and the hard cap starved the search before it reached Div -> the
core became unfindable. The fix (the agent self-edits its Migrator):

  _compose_candidates(...) — a LAZY breadth-first generator (shallow terms first)
      whose growing pool is bounded by cap; it yields one candidate at a time so
      the caller can GATE each and STOP at the first hit. Success is then fast no
      matter how large the vocabulary is; cap only bounds a genuine-failure search.
  compose_search_gated / migrate_function — iterate the generator and gate lazily
      (stop at first hit / at `want` survivors), cap raised to 600k.

With this, the DEFAULT full vocabulary (NO hand-picked ops) finds the core AND the
clamp end-to-end through the real-test gate.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_fixes_composer_search.py
"""
from __future__ import annotations
import importlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_modification import SelfModification

REL = "domains/self_migration.py"

GEN_METHOD = '''    def _compose_candidates(self, operands, ops, max_depth, cap):
        """Lazily YIELD candidate Term compositions over `ops` (each (name, form),
        form in {'unary','ab','items'}) up to `max_depth`, breadth-first (shallow
        terms first), the growing pool bounded by `cap`. Lazy so the caller GATES
        each and stops at the first hit — success is fast no matter how large the
        held vocabulary is; `cap` only bounds the genuine-failure search."""
        def mk(opname, form, x, y):
            if form == "unary":
                return {"type": opname, "arg": x}
            if form == "ab":
                return {"type": opname, "a": x, "b": y}
            return {"type": opname, "items": [x, y]}
        pool = list(operands)          # operands + every layer so far (args for any op)
        prev = list(operands)          # the previous layer (the new frontier)
        n = 0
        for _d in range(max_depth):
            layer = []
            for opname, form in ops:
                if form == "unary":
                    for x in prev:
                        t = mk(opname, form, x, None); layer.append(t); n += 1
                        yield t
                        if n >= cap:
                            return
                else:
                    for x in pool:
                        for y in prev:
                            t = mk(opname, form, x, y); layer.append(t); n += 1
                            yield t
                            if n >= cap:
                                return
            pool = pool + layer
            prev = layer

    # ----- rung-2 FREE SEARCH fed into the VERIFY gate (autonomous composition) ----
    def compose_search_gated(self, agent, points, operands, ops=None, max_depth=2,'''

CAP_OLD = "    def compose_search_gated(self, agent, points, operands, ops=None, max_depth=2,\n                             tol=1e-6, cap=40000):"
CAP_NEW = "    def compose_search_gated(self, agent, points, operands, ops=None, max_depth=2,\n                             tol=1e-6, cap=600000):"

COMPOSE_OLD = '''        ops = ops or self.held_numeric_ops()          # the WHOLE held vocabulary, not a subset

        def mk(opname, form, x, y):
            if form == "unary":
                return {"type": opname, "arg": x}
            if form == "ab":
                return {"type": opname, "a": x, "b": y}
            return {"type": opname, "items": [x, y]}

        pool = list(operands)
        cands = []
        prev = list(operands)
        for _d in range(max_depth):
            layer = []
            for opname, form in ops:
                if form == "unary":
                    for x in prev:                       # one arg from the new frontier
                        layer.append(mk(opname, form, x, None))
                        if len(cands) + len(layer) > cap:
                            break
                else:
                    for x in pool:
                        for y in prev:                   # at least one arg from the new frontier
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
                    val = float(agent.inner.evaluate(term, pt["env"]))
                except Exception:
                    ok = False
                    break
                if abs(val - pt["expected"]) > tol:
                    ok = False
                    break
            if ok:
                return {"found": True, "term": term, "tried": tried}
        return {"found": False, "tried": tried,
                "impasse": ("the agent's FULL held numeric vocabulary (" + ", ".join(n for n, _ in ops) +
                            ") cannot satisfy the gate on all points at depth %d -> escalate depth/operands, "
                            "or a genuinely new primitive is needed (HumanImpasse, no donkey)" % max_depth)}'''

COMPOSE_NEW = '''        ops = ops or self.held_numeric_ops()          # the WHOLE held vocabulary, not a subset

        def gate(term):
            for pt in points:
                try:
                    val = float(agent.inner.evaluate(term, pt["env"]))
                except Exception:
                    return False
                if abs(val - pt["expected"]) > tol:
                    return False
            return True

        tried = 0
        for term in self._compose_candidates(operands, ops, max_depth, cap):
            tried += 1
            if gate(term):                                # gate lazily, stop at the FIRST hit
                return {"found": True, "term": term, "tried": tried}
        return {"found": False, "tried": tried,
                "impasse": ("the agent's FULL held numeric vocabulary (" + ", ".join(n for n, _ in ops) +
                            ") cannot satisfy the gate on all points within depth %d / %d candidates -> "
                            "escalate depth/operands, or a genuinely new primitive is needed "
                            "(HumanImpasse, no donkey)" % (max_depth, tried))}'''

MIGRATE_OLD = '''        ops = ops or self.held_numeric_ops()          # the WHOLE held vocabulary, not a subset

        def mk(op, form, x, y):
            if form == "unary":
                return {"type": op, "arg": x}
            if form == "ab":
                return {"type": op, "a": x, "b": y}
            return {"type": op, "items": [x, y]}
        prev = list(operands); cands = []; pool = list(operands)
        for _d in range(max_depth):
            layer = []
            for o, f in ops:
                if f == "unary":
                    layer += [mk(o, f, x, None) for x in prev]
                else:
                    layer += [mk(o, f, x, y) for x in pool for y in prev]
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
                    break'''

MIGRATE_NEW = '''        ops = ops or self.held_numeric_ops()          # the WHOLE held vocabulary, not a subset

        def gate(term):
            for pt in points:
                try:
                    v = float(agent.inner.evaluate(term, pt["env"]))
                except Exception:
                    return False
                if abs(v - pt["expected"]) > tol:
                    return False
            return True

        survivors = []
        for term in self._compose_candidates(operands, ops, max_depth, 600000):
            if gate(term):                                # gate lazily, collect up to `want`
                survivors.append(term)
                if len(survivors) >= want:
                    break'''


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
    print("MAKE THE FULL-VOCABULARY COMPOSER TRACTABLE: gate lazily, stop at first hit")
    print("=" * 92)
    edits = [
        ("+_compose_candidates (lazy generator)",
         "    # ----- rung-2 FREE SEARCH fed into the VERIFY gate (autonomous composition) ----\n"
         "    def compose_search_gated(self, agent, points, operands, ops=None, max_depth=2,",
         GEN_METHOD),
        ("compose: raise cap 40k -> 600k", CAP_OLD, CAP_NEW),
        ("compose: lazy gate + stop at first hit", COMPOSE_OLD, COMPOSE_NEW),
        ("migrate_function: lazy gate + collect survivors", MIGRATE_OLD, MIGRATE_NEW),
    ]
    for label, old, new in edits:
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

    print(f"\n  vocab size (default, no ops passed): {len(M.held_numeric_ops())} numeric ops")
    print("\n  stage 1 — DEFAULT full vocabulary (NO ops=) composes the core:")
    r1 = M.compose_search_gated(agent, pts_above, [V("acc"), V("chance"), L(1.0)], max_depth=2)
    D = r1.get("term")
    print(f"     {('FOUND (tried %d): ' % r1['tried']) + _ts(D) if D else 'IMPASSE: ' + r1.get('impasse', '')}")
    if not D:
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
    print(f"  {'PASS' if ok else 'FAIL'} — the composer offers the FULL held vocabulary by default AND stays "
          f"tractable: lazy gate + stop-at-first-hit means success is fast no matter the vocabulary size; the "
          f"cap only bounds genuine failure. With NO hand-picked ops it now composes BOTH the core and the clamp "
          f"and passes the REAL test. Offer-everything + stop-early — no false impasses, no blow-up. No LLM.")
    print("=" * 92)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
