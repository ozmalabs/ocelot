"""Fix the composer to offer the agent's FULL HELD VOCABULARY (wave-17 lesson).

The "need Max" impasse was false: Max { items } was already a held Term; the
composer just never offered it (its op set was a hand-picked binary subset). The
fix, applied by the agent to its OWN Migrator via SelfModification:

  1. held_numeric_ops() — reads the agent's own eval table (term.rs evaluate()
     match arms = the source of truth) and returns EVERY TermNode that evaluates
     its scalar children to a numeric VALUE, tagged by arity form (unary {arg},
     binary {a,b}, variadic {items}); index reductions (ArgMax/ArgMin, which
     return an index not a value) are excluded. New numeric primitives the agent
     authors later are picked up automatically.
  2. compose_search_gated + migrate_function now DEFAULT ops to held_numeric_ops()
     (no hand-picked subset) and the enumeration is unary-aware (Abs/Neg/Sqrt/...).
  3. the impasse message names the actual vocabulary tried, so a real gap reads as
     "the WHOLE held vocabulary, at this depth, can't" — not a subset artifact.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_fixes_composer_vocabulary.py
"""
from __future__ import annotations
import importlib, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from domains.self_modification import SelfModification

REL = "domains/self_migration.py"

HELD_OPS_METHOD = '''    def held_numeric_ops(self, term_rs_path=None):
        """The agent's FULL held numeric vocabulary, read from its OWN eval table
        (term.rs evaluate() match arms = the source of truth) — NOT a hand-picked
        subset. Every TermNode that evaluates its scalar children to a numeric
        Value is offered, tagged by arity form ('unary' {arg}, 'ab' {a,b}, 'items'
        {items}); index reductions (ArgMax/ArgMin) are excluded (they return an
        index, not a value). New numeric primitives the agent authors later are
        picked up automatically. Returns [(name, form), ...]."""
        import os as _os, re as _re
        path = term_rs_path or _os.path.join(self.root, "runners", "dsl", "src", "term.rs")
        src = open(path).read().splitlines()
        start = next((i for i, l in enumerate(src) if l.startswith("pub fn evaluate(")), 0)
        end = next((i for i in range(start + 1, len(src)) if _re.match(r"^(pub )?fn ", src[i])), len(src))
        body = src[start:end]
        forms = {"a, b": "ab", "items": "items", "arg": "unary"}
        arm = _re.compile(r"TermNode::([A-Za-z]\\w*) \\{ (a, b|items|arg) \\} =>(.*)")
        ops, seen = [], set()
        i = 0
        while i < len(body):
            m = arm.search(body[i])
            if not m:
                i += 1
                continue
            name, fld, rest = m.group(1), m.group(2), m.group(3)
            chunk = rest
            if rest.strip().endswith("{"):                 # a block arm: gather to its close
                j = i + 1
                while j < len(body) and not arm.search(body[j]) and body[j] != "        }":
                    chunk += "\\n" + body[j]
                    j += 1
            if _re.search(r"numeric_arg(max|min)\\b", chunk):
                numeric = False                            # index op, not a value
            elif _re.search(r"numeric_(binary|variadic|minmax)\\b", chunk):
                numeric = True
            elif ("Value::Float(" in chunk or "Value::Int(" in chunk) and "evaluate(arena" in chunk:
                numeric = True
            else:
                numeric = False
            if numeric and name not in seen:
                seen.add(name)
                ops.append((name, forms[fld]))
            i += 1
        return ops

    # ----- rung-2 FREE SEARCH fed into the VERIFY gate (autonomous composition) ----
    def compose_search_gated(self, agent, points, operands, ops=None, max_depth=2,'''

COMPOSE_OLD = '''        ops = ops or [("Minus", "ab"), ("Div", "ab"), ("Pow", "ab"),
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
                break'''

COMPOSE_NEW = '''        ops = ops or self.held_numeric_ops()          # the WHOLE held vocabulary, not a subset

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
                break'''

IMPASSE_OLD = '''        return {"found": False, "tried": tried,
                "impasse": ("held binary ops {Minus,Div,Pow,Plus,Times} cannot satisfy the gate on "
                            "all points -> a new primitive is needed (HumanImpasse, no donkey)")}'''

IMPASSE_NEW = '''        return {"found": False, "tried": tried,
                "impasse": ("the agent's FULL held numeric vocabulary (" + ", ".join(n for n, _ in ops) +
                            ") cannot satisfy the gate on all points at depth %d -> escalate depth/operands, "
                            "or a genuinely new primitive is needed (HumanImpasse, no donkey)" % max_depth)}'''

MIGRATE_OLD = '''        ops = ops or [("Minus", "ab"), ("Div", "ab"), ("Plus", "items"), ("Times", "items")]

        def mk(op, form, x, y):
            return ({"type": op, "a": x, "b": y} if form == "ab"
                    else {"type": op, "items": [x, y]})
        prev = list(operands); cands = []; pool = list(operands)
        for _d in range(max_depth):
            layer = [mk(o, f, x, y) for o, f in ops for x in pool for y in prev]
            cands.extend(layer); prev = layer; pool = list(operands) + cands
            if len(cands) > 40000:
                break'''

MIGRATE_NEW = '''        ops = ops or self.held_numeric_ops()          # the WHOLE held vocabulary, not a subset

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
    print("FIX THE COMPOSER TO OFFER THE FULL HELD VOCABULARY (self-edit on the Migrator)")
    print("=" * 92)
    src = mod.read(REL)
    edits = []
    if "def held_numeric_ops(" not in src:
        edits.append(("+held_numeric_ops + unary-aware compose",
                      "    # ----- rung-2 FREE SEARCH fed into the VERIFY gate (autonomous composition) ----\n"
                      "    def compose_search_gated(self, agent, points, operands, ops=None, max_depth=2,",
                      HELD_OPS_METHOD))
    edits += [
        ("compose: default=held_numeric_ops, unary-aware", COMPOSE_OLD, COMPOSE_NEW),
        ("compose: honest impasse names the real vocabulary", IMPASSE_OLD, IMPASSE_NEW),
        ("migrate_function: default=held_numeric_ops, unary-aware", MIGRATE_OLD, MIGRATE_NEW),
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
    print("\n  held_numeric_ops() — the agent's full numeric vocabulary, read from its own eval table:")
    vocab = M.held_numeric_ops()
    print("     " + ", ".join(f"{n}/{f}" for n, f in vocab))
    have = {n for n, _ in vocab}
    for need in ("Max", "Min", "Plus", "Times", "Minus", "Div", "Pow"):
        assert need in have, f"vocab missing {need}"
    print(f"     ({len(vocab)} numeric ops; Max/Min reductions now included by default; ArgMax/ArgMin excluded as index ops)")

    # PROVE the default (no ops passed) now resolves the wave-17 clamp.
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

    print("\n  DEFAULT vocabulary (NO ops passed) resolves the clamp end-to-end:")
    r1 = M.compose_search_gated(agent, pts_above, [V("acc"), V("chance"), L(1.0)], max_depth=2)
    D = r1.get("term")
    print(f"     stage 1 core: {_ts(D) if D else r1.get('impasse')}")
    fn_anchor = "    w = (acc - chance) / (1.0 - chance)\n    return float(max(0.0, w))"
    out = M.migrate_function(agent, "weighted_admissibility", "reliability_to_weight", fn_anchor,
                             {"acc": "acc", "chance": "chance"}, pts_full,
                             operands=[D, L(0.0)], max_depth=2, want=4)   # NO ops= -> full held vocab
    acc = out.get("accepted")
    print(f"     stage 2 accepted by the REAL test: {_ts(acc) if acc else out.get('impasse')}")

    mod.restore("domains/weighted_admissibility.py")
    for f in __import__("glob").glob(os.path.join(ROOT, "domains", "*.selfmod.bak")):
        os.remove(f)
    intact = "return float(max(0.0, w))" in open(os.path.join(ROOT, "domains", "weighted_admissibility.py")).read()

    ok = ("Max" in have and "Min" in have and any(f == "unary" for _, f in vocab)
          and acc is not None and intact)
    print("\n" + "=" * 92)
    print(f"  {'PASS' if ok else 'FAIL'} — the composer now DEFAULTS to the agent's full held numeric vocabulary "
          f"(read from its own eval table: {len(vocab)} ops incl. Max/Min reductions + Abs/Neg/Sqrt/... unary, "
          f"index ops excluded). With NO hand-picked op set it composes the clamp and passes the REAL test. A "
          f"future 'need a primitive' impasse is now trustworthy — it means the WHOLE vocabulary failed, not a "
          f"subset. Faculty restored, no LLM.")
    print("=" * 92)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
