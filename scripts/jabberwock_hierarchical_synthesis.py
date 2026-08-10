"""HIERARCHICAL (library-growth) synthesis over the agent's held Term primitives. Synthesise small kernels
from atoms, ADD them to the library, then synthesise deeper targets USING the kernels — including
aggregation targets (Sum-over-dims) whose BODY is searched and verified by the agent's evaluator. This is
the earn-not-borrow library-growth (DreamCoder-shape): the composer builds from primitives, then from what
it built. donkey=0; the evaluator decides every candidate, Python only enumerates.

  L1  absdiff(a,b) = |a-b|                          from atoms {Var,Minus,Gte,Ite}
  L2  dist(pos,target,dims) = Σ_i absdiff(pos[i],target[i])     using absdiff + IndexAt + Sum   <-- N-DIM
      (the SAME synthesised term verifies on 1-D, 2-D, 3-D, 4-D vectors — works for ANY game's coords)
  L2  dist_moved(pos,delta,target,dims) = Σ_i absdiff(pos[i]+delta[i], target[i])    using absdiff
  L3  progress = dist - dist_moved                  composing the L2 blocks

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_hierarchical_synthesis.py
"""
from __future__ import annotations
import os, sys, json, copy
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import _native_eval2

def L(v): return {"type": "Lit", "value": v}
def V(n): return {"type": "Var", "name": n}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Plus(a, b): return {"type": "Plus", "items": [a, b]}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def IA(s, i): return {"type": "IndexAt", "seq": s, "index": i}
def Sum(src, var, body): return {"type": "Sum", "source": src, "var_name": var, "value": body}

# base primitive ops: (name, kind, arg-kinds, builder)
BASE = [
    ("Minus", "num", ("num", "num"), lambda a, b: Minus(a, b)),
    ("Plus",  "num", ("num", "num"), lambda a, b: Plus(a, b)),
    ("Gte",   "bool", ("num", "num"), lambda a, b: Gte(a, b)),
    ("Ite",   "num", ("bool", "num", "num"), lambda c, t, o: Ite(c, t, o)),
    ("IndexAt", "num", ("list", "num"), lambda s, i: IA(s, i)),
]


def subst(term, mapping):
    t = copy.deepcopy(term)
    def go(n):
        if isinstance(n, dict):
            if n.get("type") == "Var" and n.get("name") in mapping:
                return copy.deepcopy(mapping[n["name"]])
            return {k: go(v) for k, v in n.items()}
        if isinstance(n, list):
            return [go(x) for x in n]
        return n
    return go(t)


def lib_op(name, params, template, kind="num", argkinds=None):
    """make a library block callable as an op: substitute params with args."""
    argkinds = argkinds or tuple("num" for _ in params)
    return (name, kind, argkinds, lambda *args: subst(template, dict(zip(params, args))))


def flat_synth(ev, terminals, ops, examples, max_rounds=4, cap=6000):
    """bottom-up, observational-equivalence pruned; the evaluator decides each candidate."""
    envs = [e for e, _ in examples]; expected = tuple(o for _, o in examples)
    bank = {}; seen = set()
    def consider(term, kind):
        try:
            outs = tuple(ev(term, e) for e in envs)
        except Exception:
            return None
        if any(o is None for o in outs):
            return None
        if (kind, outs) in seen:
            return None
        seen.add((kind, outs)); bank.setdefault(kind, []).append((term, outs))
        return outs
    for term, kind in terminals:
        if consider(term, kind) == expected:
            return term
    for _ in range(max_rounds):
        snap = {k: list(v) for k, v in bank.items()}
        for name, kind, aks, build in ops:
            pools = [snap.get(ak, []) for ak in aks]
            if any(not pl for pl in pools):
                continue
            stack = [([],)]
            # iterative cartesian product over pools
            def rec(i, acc):
                if i == len(pools):
                    t = build(*[x for x, _ in acc])
                    return t if consider(t, kind) == expected else None
                for it in pools[i]:
                    r = rec(i + 1, acc + [it])
                    if r is not None:
                        return r
                return None
            got = rec(0, [])
            if got is not None:
                return got
        if sum(len(v) for v in bank.values()) > cap:
            break
    return None


def synth_sum(ev, examples, src_var, idx_var, body_terminals, body_ops, max_rounds=3, cap=350):
    """synthesise Sum(src, idx, BODY): enumerate BODY over the bound index + inputs, wrap in Sum, and
    verify the WHOLE aggregate on the examples (no lifting needed — the evaluator checks the sum)."""
    envs = [e for e, _ in examples]; expected = tuple(o for _, o in examples)
    # build a bank of candidate bodies (numeric), then wrap each in Sum and test the aggregate
    bank = {}; seen = set()
    bodies = []
    def probe(term):
        outs = []
        for e in envs:
            ee = dict(e); ee[idx_var] = (ee.get(src_var) or [0])[0]
            try:
                outs.append(ev(term, ee))
            except Exception:
                return None
        return tuple(outs)
    def add(term, kind):
        sig = probe(term)
        if sig is None or any(o is None for o in sig):
            return
        key = (kind, sig)
        if key in seen:                                  # observational-equivalence pruning (REAL skip)
            return
        seen.add(key)
        bank.setdefault(kind, []).append(term)
        if kind == "num":
            bodies.append(term)
    for t, k in body_terminals:
        add(t, k)
    def try_bodies():
        for b in bodies:
            whole = Sum(V(src_var), idx_var, b)
            try:
                outs = tuple(ev(whole, e) for e in envs)
            except Exception:
                continue
            if outs == expected:
                return whole, b
        return None, None
    w, b = try_bodies()
    if w:
        return w, b
    for _ in range(max_rounds):
        snap = {k: list(v) for k, v in bank.items()}
        for name, kind, aks, build in body_ops:
            if len(bodies) > cap:
                break
            pools = [snap.get(ak, []) for ak in aks]
            if any(not pl for pl in pools):
                continue
            def rec(i, acc):
                if len(bodies) > cap:
                    return
                if i == len(pools):
                    add(build(*acc), kind); return
                for it in pools[i]:
                    rec(i + 1, acc + [it])
            rec(0, [])
        w, b = try_bodies()
        if w:
            return w, b
        if len(bodies) > cap:
            break
    return None, None


def term_size(t):
    if isinstance(t, dict):
        return 1 + sum(term_size(v) for v in t.values())
    if isinstance(t, list):
        return sum(term_size(x) for x in t)
    return 0


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    nat = _native_eval2(a); ev = lambda t, env: nat.evaluate(t, env)

    print("=" * 92)
    print("HIERARCHICAL SYNTHESIS — the composer builds kernels from atoms, then builds FROM the kernels")
    print("=" * 92)
    library = []

    # L1: absdiff(a,b) from atoms
    absdiff = flat_synth(ev, [(V("a"), "num"), (V("b"), "num")], BASE,
                         [({"a": 3, "b": 0}, 3), ({"a": 0, "b": 5}, 5), ({"a": 4, "b": 4}, 0),
                          ({"a": 2, "b": 7}, 5), ({"a": 9, "b": 1}, 8)])
    print(f"\n  L1 absdiff(a,b): {json.dumps(absdiff) if absdiff else 'NOT FOUND'}")
    if not absdiff:
        return 1
    library.append(lib_op("absdiff", ["a", "b"], absdiff))

    # L2: dist(pos,target,dims) = Σ_i absdiff(pos[i],target[i]) — N-DIMENSIONAL.
    # The deeper body search uses STRUCTURAL ops (IndexAt, Plus) + the LIBRARY blocks (absdiff) — NOT the
    # atoms that would re-derive absdiff. That is the library's whole point: reuse, and it stays tractable.
    STRUCT = [("IndexAt", "num", ("list", "num"), lambda s, i: IA(s, i)),
              ("Plus", "num", ("num", "num"), lambda a, b: Plus(a, b))]
    body_terms = [(V("i"), "num"), (V("pos"), "list"), (V("target"), "list")]
    body_ops = STRUCT + library
    # examples include pos[i] < target[i] (negative raw diff) so plain Minus FAILS -> absdiff is forced
    dist_ex = [({"pos": [3, 1], "target": [0, 0], "dims": [0, 1]}, 4),
               ({"pos": [1, 3], "target": [4, 0], "dims": [0, 1]}, 6),          # pos<target
               ({"pos": [0, 0, 2], "target": [3, 1, 0], "dims": [0, 1, 2]}, 6),  # 3-D, pos<target
               ({"pos": [2], "target": [5], "dims": [0]}, 3),                    # 1-D, pos<target
               ({"pos": [1, 1, 1, 1], "target": [0, 0, 0, 0], "dims": [0, 1, 2, 3]}, 4)]
    dist, dbody = synth_sum(ev, dist_ex, "dims", "i", body_terms, body_ops)
    print(f"\n  L2 dist(pos,target,dims) — Σ over dims, body uses the L1 kernel:")
    print(f"     body : {json.dumps(dbody) if dbody else 'NOT FOUND'}")
    print(f"     dist : {json.dumps(dist)[:160] if dist else 'NOT FOUND'} ...")
    if dist:
        for ex, exp in dist_ex:
            got = ev(dist, ex)
            print(f"       {len(ex['dims'])}-D  dist({ex['pos']},{ex['target']}) = {got}  (want {exp})  "
                  f"{'OK' if got == exp else 'WRONG'}")
        library.append(lib_op("dist", ["pos", "target", "dims"], dist,
                              argkinds=("list", "list", "list")))

    # L2': dist_moved(pos,delta,target,dims) = Σ_i absdiff(pos[i]+delta[i], target[i])
    body_terms2 = [(V("i"), "num"), (V("pos"), "list"), (V("delta"), "list"), (V("target"), "list")]
    # non-zero targets + moves that overshoot -> forces absdiff(pos[i]+delta[i], target[i])
    dm_ex = [({"pos": [1, 3], "delta": [2, -1], "target": [5, 0], "dims": [0, 1]}, 4),    # moved[3,2]
             ({"pos": [4, 0], "delta": [-1, 0], "target": [1, 1], "dims": [0, 1]}, 3),    # moved[3,0]
             ({"pos": [1, 1, 1], "delta": [0, 0, 1], "target": [0, 0, 3], "dims": [0, 1, 2]}, 3),
             ({"pos": [2, 2], "delta": [1, 1], "target": [5, 5], "dims": [0, 1]}, 4)]      # moved[3,3]
    distm, dmbody = synth_sum(ev, dm_ex, "dims", "i", body_terms2, STRUCT + library, max_rounds=4)
    print(f"\n  L2' dist_moved(pos,delta,target,dims) — Σ with delta added inside (uses L1 kernel):")
    print(f"     body : {json.dumps(dmbody) if dmbody else 'NOT FOUND'}")
    if distm:
        ok = all(ev(distm, e) == o for e, o in dm_ex)
        print(f"     verified on examples: {ok}")
        library.append(lib_op("dist_moved", ["pos", "delta", "target", "dims"], distm,
                              argkinds=("list", "list", "list", "list")))

    # L3: progress = dist - dist_moved  (compose the L2 blocks)
    if dist and distm:
        progress = flat_synth(
            ev,
            [(V("pos"), "list"), (V("delta"), "list"), (V("target"), "list"), (V("dims"), "list")],
            BASE + library,
            [({"pos": [3, 1], "delta": [0, -1], "target": [0, 0], "dims": [0, 1]}, 1),
             ({"pos": [1, 3], "delta": [2, 0], "target": [4, 0], "dims": [0, 1]}, 2),     # varied progress
             ({"pos": [2, 2], "delta": [1, 0], "target": [0, 0], "dims": [0, 1]}, -1),    # negative progress
             ({"pos": [0, 0], "delta": [1, 1], "target": [5, 5], "dims": [0, 1]}, 2)],
            max_rounds=3)
        print(f"\n  L3 progress = dist − dist_moved (composed from L2 blocks): "
              f"{'FOUND' if progress else 'not found by flat search'}")
        if progress:
            print(f"     {json.dumps(progress)[:160]} ...")

    print("\n" + "=" * 92)
    print(f"  donkey (LLM calls): {donkey['n']}")
    print("  The composer grew a LIBRARY from primitives: absdiff (atoms) -> N-dimensional dist (Σ over dims")
    print("  using absdiff) -> dist_moved -> progress. The SAME dist verifies across 1-D..4-D, so the core is")
    print("  coordinate-count agnostic (any game). The outer decision (Argmax over affordances of Σ over")
    print("  candidates of progress) is the SAME aggregation mechanism over GRAPH sources — the next layer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
