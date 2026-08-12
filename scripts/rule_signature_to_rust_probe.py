"""rule_signature_to_rust_probe — AR1 boundary probe (read-only).

Answers, empirically, the three routes RULE_SIGNATURE_TO_RUST_PREREG.md §AR1
registers, and prints the exact engine-boundary facts a P1-subset rewrite
would have to route around. Touches no production file; writes nothing.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/rule_signature_to_rust_probe.py
"""
from __future__ import annotations

import ast
import inspect
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402
from domains import rule_signature as rs  # noqa: E402
from domains.prog_ir_emit import emit_prog_ir  # noqa: E402


def _src(fn) -> str:
    return inspect.getsource(fn)


def part_a_existing_python_blockers():
    print("=" * 72)
    print("A. emit_prog_ir on the EXISTING domains/rule_signature.py functions")
    print("=" * 72)
    for fn in (rs.rule_signature, rs._collect_var_names, rs._atomize,
               rs._is_term_node, rs._is_term_list):
        try:
            out = emit_prog_ir(_src(fn))
        except Exception as e:  # noqa: BLE001
            print(f"  {fn.__name__:22s} EMIT-ERROR {type(e).__name__}: {e}")
            continue
        if out.get("ok"):
            print(f"  {fn.__name__:22s} ok=True  predictable={out.get('predictable')} "
                  f"externs={sorted(out.get('externs') or [])}")
        else:
            print(f"  {fn.__name__:22s} ok=False blockers={out['blockers']}")


def part_b_engine_boundaries():
    print()
    print("=" * 72)
    print("B. ProgEval engine-boundary facts a P1-subset rewrite must handle")
    print("=" * 72)
    s = srs.Substrate()

    def run(prog, env=None, oracles=None, fuel=200000):
        t = {"type": "ProgEval", "prog": prog, "env": {"type": "Lit", "value": env or {}},
             "oracles": {"type": "Lit", "value": {n: "builtin" for n in (oracles or [])}}
             if oracles else None, "fuel": fuel, "field": ""}
        return s._inner.evaluate(t, {})["result"]

    def lit(v):
        return {"type": "Lit", "value": v}

    def var(n):
        return {"type": "Var", "name": n}

    def ret(t):
        return {"type": "ProgSeq", "stmts": [{"type": "ProgReturn", "value": t}]}

    def call(name, args, recv=None):
        d = {"type": "ProgCallExtern", "name": name, "args": args}
        if recv is not None:
            d["recv"] = recv
        return d

    # B1 — sorted() on strings: interner-symbol-id order, or lexicographic?
    keys = ["where", "source", "var_name", "a_zzz", "b"]
    got = run(ret(call("sorted", [var("ks")])), env={"ks": keys}, oracles=["sorted"])
    print(f"  B1 sorted(strings)      engine={list(got)}")  # noqa
    print(f"     CPython sorted        ={sorted(keys)}")
    print(f"     LEXICOGRAPHIC? {list(got) == sorted(keys)}")

    # B2 — string subscript + ord (needed for a hand-written lexicographic compare)
    try:
        got = run(ret(call("ord", [{"type": "ProgSubscript", "obj": var("s"), "index": lit(1)}])),
                  env={"s": "abc"}, oracles=["ord"])
        print(f"  B2 ord(s[1]) on 'abc'   engine={got}  (CPython={ord('abc'[1])})")
    except Exception as e:  # noqa: BLE001
        print(f"  B2 ord(s[1])            TRAP/ERROR: {e}")

    # B3 — set union via `|` on set literals
    try:
        prog = ret({"type": "BitOr", "a": var("x"), "b": var("y")})
        got = run(prog, env={"x": {1, 2}, "y": {2, 3}})
        print(f"  B3 set | set            engine={got} type={type(got).__name__}")
    except Exception as e:  # noqa: BLE001
        print(f"  B3 set | set            TRAP/ERROR: {e}")

    # B4 — tuple accumulation via `+=` (ProgAugAssign 'add')
    prog = {"type": "ProgSeq", "stmts": [
        {"type": "ProgAssignVar", "name": "acc", "value": lit(())},
        {"type": "ProgAugAssign", "name": "acc", "op": "add",
         "value": {"type": "ProgContainerLit", "kind": "list", "items": [lit("x")]}},
        {"type": "ProgAugAssign", "name": "acc", "op": "add",
         "value": {"type": "ProgContainerLit", "kind": "list", "items": [lit("y")]}},
        {"type": "ProgReturn", "value": var("acc")}]}
    try:
        print(f"  B4 tuple +=             engine={run(prog)}")
    except Exception as e:  # noqa: BLE001
        print(f"  B4 tuple +=             TRAP/ERROR: {e}")

    # B5 — dict subscript-set with a TUPLE key, then frozenset(d.keys())
    prog = {"type": "ProgSeq", "stmts": [
        {"type": "ProgAssignVar", "name": "d", "value": {"type": "ProgContainerLit",
                                                          "kind": "dict", "items": []}},
        {"type": "ProgSubscriptSet", "obj": var("d"),
         "index": {"type": "ProgContainerLit", "kind": "tuple",
                   "items": [lit("rt"), lit(""), lit("Exists")]}, "value": lit(1)},
        {"type": "ProgReturn", "value": call("frozenset", [call("keys", [], recv=var("d"))])}]}
    try:
        got = run(prog, oracles=["frozenset", "keys"])
        print(f"  B5 dict[tuple]=1        engine={got} type={type(got).__name__}")
    except Exception as e:  # noqa: BLE001
        print(f"  B5 dict[tuple]=1        TRAP/ERROR: {e}")

    # B6 — how does a nested python list/dict arrive, and come back?
    prog = ret(var("v"))
    for name, v in (("list", ["a", ["b", "c"]]), ("dict", {"k": ["a"]}),
                    ("tuple", ("a", ("b",)))):
        try:
            got = run(prog, env={"v": v})
            print(f"  B6 roundtrip {name:5s}      in={v!r} -> out={got!r} "
                  f"({type(got).__name__})")
        except Exception as e:  # noqa: BLE001
            print(f"  B6 roundtrip {name:5s}      TRAP/ERROR: {e}")

    # B7 — sorted() on dict .keys() of a real where-clause node
    node = {"type": "Exists", "source": {"type": "Var", "name": "x"},
            "var_name": "mn", "where": {"type": "Lit", "value": 1}}
    got = run(ret(call("sorted", [call("keys", [], recv=var("n"))])),
              env={"n": node}, oracles=["sorted", "keys"])
    print(f"  B7 sorted(node.keys())  engine={list(got)}")
    print(f"     CPython               ={sorted(node.keys())}")

    # B8 — isinstance on a dict/list arriving from Python
    for nm, v in (("dict", {"a": 1}), ("list", ["a"]), ("str", "a"), ("tuple", ("a",))):
        outs = []
        for tn in ("dict", "list", "tuple", "str"):
            try:
                outs.append(f"{tn}={run(ret(call('isinstance', [var('v'), lit(tn)])), env={'v': v}, oracles=['isinstance'])}")
            except Exception as e:  # noqa: BLE001
                outs.append(f"{tn}=ERR({e})")
        print(f"  B8 isinstance({nm:5s})     {' '.join(outs)}")


def part_c_population():
    print()
    print("=" * 72)
    print("C. the REAL where-clause population — what atoms actually occur")
    print("=" * 72)
    seeds_dir = os.path.join(ROOT, "seeds")
    kinds: dict[str, int] = {}
    nrules = 0
    maxdepth = 0
    nested = []
    for fname in sorted(os.listdir(seeds_dir)):
        if not fname.endswith(".json"):
            continue
        try:
            blob = json.load(open(os.path.join(seeds_dir, fname)))
        except Exception:  # noqa: BLE001
            continue
        rules = blob.get("rules") if isinstance(blob, dict) else None
        for r in (rules or []):
            if not isinstance(r, dict):
                continue
            w = r.get("where")
            if not isinstance(w, dict):
                continue
            nrules += 1
            sig = rs.rule_signature(w)
            for row in sig:
                if row[0] != "ra":
                    continue
                atom = row[3]
                k = type(atom).__name__
                kinds[k] = kinds.get(k, 0) + 1
                if isinstance(atom, tuple):
                    d = _depth(atom)
                    if d > maxdepth:
                        maxdepth = d
                    if d > 1:
                        nested.append((fname, r.get("name"), row[1], row[2], d))
    print(f"  rules with a where clause (all seeds): {nrules}")
    print(f"  ra-atom python types: {dict(sorted(kinds.items()))}")
    print(f"  max container depth of any atom: {maxdepth}")
    print(f"  atoms with depth > 1: {len(nested)}")
    for row in nested[:10]:
        print(f"    {row}")


def _depth(x) -> int:
    if isinstance(x, tuple):
        return 1 + max([_depth(v) for v in x] or [0])
    return 0




def part_d_more_boundaries():
    print()
    print("=" * 72)
    print("D. further boundary facts")
    print("=" * 72)
    s = srs.Substrate()

    def run(prog, env=None, oracles=None, fuel=200000):
        t = {"type": "ProgEval", "prog": prog, "env": {"type": "Lit", "value": env or {}},
             "oracles": {"type": "Lit", "value": {n: "builtin" for n in (oracles or [])}}
             if oracles else None, "fuel": fuel, "field": ""}
        return s._inner.evaluate(t, {})

    lit = lambda v: {"type": "Lit", "value": v}
    var = lambda n: {"type": "Var", "name": n}
    ret = lambda t: {"type": "ProgSeq", "stmts": [{"type": "ProgReturn", "value": t}]}

    # D1 — `k in dict` : keys or values?
    for k in ("type", "Exists"):
        got = run(ret({"type": "In", "member": lit(k), "container": var("d")}),
                  env={"d": {"type": "Exists"}})
        print(f"  D1 {k!r:10s} in dict  -> {got['result']} trap={got['trap']}")
    # D2 — subscript-set on a LIST value
    prog = {"type": "ProgSeq", "stmts": [
        {"type": "ProgAssignVar", "name": "xs",
         "value": {"type": "ProgContainerLit", "kind": "list",
                   "items": [lit(1), lit(2)]}},
        {"type": "ProgSubscriptSet", "obj": var("xs"), "index": lit(0), "value": lit(9)},
        {"type": "ProgReturn", "value": var("xs")}]}
    got = run(prog)
    print(f"  D2 list literal + [0]=9 -> {got['result']!r} trap={got['trap']}")
    # D3 — f-string
    prog = ret({"type": "ProgFString", "parts": [lit("?"),
                {"type": "ProgCallExtern", "name": "str", "args": [var("i")]}]})
    try:
        got = run(prog, env={"i": 3}, oracles=["str"])
        print(f"  D3 f-string             -> {got['result']!r} trap={got['trap']}")
    except Exception as e:
        print(f"  D3 f-string             ERR {e}")
    # D4 — dict.get with default
    got = run(ret({"type": "ProgCallExtern", "name": "get", "recv": var("d"),
                   "args": [lit("zz"), lit("dflt")]}), env={"d": {"a": 1}}, oracles=["get"])
    print(f"  D4 d.get(k, default)    -> {got['result']!r} trap={got['trap']}")


if __name__ == "__main__":
    part_d_more_boundaries()
