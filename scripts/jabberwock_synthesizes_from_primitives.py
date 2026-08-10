"""STRENGTHEN THE COMPOSER into a PROGRAM SYNTHESIZER over the agent's HELD Term primitives. The agent
assembles a Term from its primitives; its OWN evaluator decides correctness (runs each candidate on the
spec examples). Python only enumerates the frontier (bottom-up, observational-equivalence pruned) — no LLM,
no Python decision over the composition. This is "the agent synthesizes from primitives".

Demonstrated on two building blocks the decision faculty is made of:
  abs(x)      = Ite(Gte(x,0), x, Minus(0,x))     — the distance kernel (|p-t|)
  max2(x,y)   = Ite(Gte(x,y), x, y)              — the argmax kernel (pick the better)
synthesised purely from primitives {Var, Lit, Minus, Plus, Gte, IfThenElse} against input/output examples,
verified by the agent's evaluator. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_synthesizes_from_primitives.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2

# --- the agent's HELD Term primitives, as a typed grammar (kind in: num|bool) ----------------------
def L(v): return {"type": "Lit", "value": v}
def V(n): return {"type": "Var", "name": n}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Plus(a, b): return {"type": "Plus", "items": [a, b]}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}

# (name, kind, arg-kinds, builder) — these are the agent's own Term variants
OPS = [
    ("Minus", "num", ("num", "num"), lambda a, b: Minus(a, b)),
    ("Plus",  "num", ("num", "num"), lambda a, b: Plus(a, b)),
    ("Gte",   "bool", ("num", "num"), lambda a, b: Gte(a, b)),
    ("Ite",   "num", ("bool", "num", "num"), lambda c, t, o: Ite(c, t, o)),
]


def synthesize(ev, terminals, examples, max_rounds=4, bank_cap=4000):
    """Bottom-up synthesis over the held primitives; the agent's evaluator decides each candidate by
    running it on the spec examples. Observational-equivalence pruning keeps the frontier finite."""
    envs = [e for e, _ in examples]; expected = tuple(o for _, o in examples)
    bank = {"num": [], "bool": []}                      # kind -> [(term, outputs)]
    seen = set()

    def consider(term, kind):
        try:
            outs = tuple(ev(term, e) for e in envs)
        except Exception:
            return None
        if any(o is None for o in outs):
            return None
        key = (kind, outs)
        if key in seen:
            return None
        seen.add(key); bank[kind].append((term, outs))
        return outs

    for term, kind in terminals:
        if consider(term, kind) == expected:
            return term, 0
    for rnd in range(1, max_rounds + 1):
        snapshot = {k: list(v) for k, v in bank.items()}
        for name, kind, argkinds, build in OPS:
            pools = [snapshot[ak] for ak in argkinds]
            # enumerate arg combinations from the current bank
            def rec(i, acc):
                if i == len(pools):
                    term = build(*[t for t, _o in acc])
                    outs = consider(term, kind)
                    if outs == expected:
                        return term
                    return None
                for item in pools[i]:
                    r = rec(i + 1, acc + [item])
                    if r is not None:
                        return r
                return None
            got = rec(0, [])
            if got is not None:
                return got, rnd
            if sum(len(v) for v in bank.values()) > bank_cap:
                break
    return None, max_rounds


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    nat = _native_eval2(a); ev = lambda t, env: nat.evaluate(t, env)

    print("=" * 92)
    print("THE AGENT SYNTHESISES A TERM FROM ITS HELD PRIMITIVES (its evaluator verifies; Python enumerates)")
    print("=" * 92)
    terminals = [(V("x"), "num"), (V("y"), "num"), (L(0), "num")]

    # 1) abs(x) — the distance kernel |p - t|
    abs_ex = [({"x": 3, "y": 0}, 3), ({"x": -5, "y": 0}, 5), ({"x": 0, "y": 0}, 0), ({"x": -2, "y": 0}, 2)]
    term, rnd = synthesize(ev, terminals, abs_ex)
    print(f"\n  TARGET abs(x)  (distance kernel) — examples {[(e['x'], o) for e, o in abs_ex]}")
    print(f"    synthesised at round {rnd}: {json.dumps(term) if term else 'NOT FOUND'}")
    if term:
        chk = all(ev(term, e) == o for e, o in abs_ex)
        print(f"    verified on all examples by the agent's evaluator: {chk}")

    # 2) max2(x,y) — the argmax kernel (pick the better of two)
    max_ex = [({"x": 3, "y": 7}, 7), ({"x": 9, "y": 2}, 9), ({"x": 4, "y": 4}, 4), ({"x": -1, "y": -5}, -1)]
    term2, rnd2 = synthesize(ev, terminals, max_ex)
    print(f"\n  TARGET max2(x,y)  (argmax kernel) — examples {[((e['x'], e['y']), o) for e, o in max_ex]}")
    print(f"    synthesised at round {rnd2}: {json.dumps(term2) if term2 else 'NOT FOUND'}")
    if term2:
        chk = all(ev(term2, e) == o for e, o in max_ex)
        print(f"    verified on all examples by the agent's evaluator: {chk}")

    print("\n" + "=" * 92)
    print(f"  donkey (LLM calls): {donkey['n']}")
    print("  The agent SYNTHESISED these Terms from its own held primitives — its evaluator decided")
    print("  correctness by running each candidate on the examples; Python only enumerated the frontier.")
    print("  abs is the distance kernel and max2 is the argmax kernel of the decision faculty: the composer")
    print("  now BUILDS from primitives. The full decision Term is deeper — reachable by composing these")
    print("  synthesised blocks (and over graph sources Neighbours/Attr) rather than enumerating atoms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
