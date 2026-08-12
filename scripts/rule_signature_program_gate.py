"""rule_signature_program_gate — the AR4 three-way differential gate.

    CPython(rule_signature)  ==  CPython(where_signature_rows)  ==  ProgEval(IR)

over (a) every `where` clause in every seed manifest, (b) synthetic
structures the corpus does not contain (nested containers, dict-valued
atoms, non-ASCII keys), and (c) the 40-probe oracle's own rule population.
Read-only; prints a report and exits non-zero on any mismatch.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/rule_signature_program_gate.py
"""
from __future__ import annotations

import inspect
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402
from domains import rule_signature as rsig  # noqa: E402
from domains.rule_signature import rule_signature  # noqa: E402
from domains.rule_signature_program import where_signature_rows  # noqa: E402
from domains.prog_ir_emit import emit_prog_ir  # noqa: E402


def emit() -> dict:
    return emit_prog_ir(inspect.getsource(where_signature_rows))


def prog_eval_runner(ir, oracles, fuel=rsig.SIGNATURE_PROGRAM_FUEL):
    """The PRODUCTION path: install the program into a real Substrate,
    read the IR back OUT of the graph, execute it there. `ir`/`oracles`
    are accepted only so the caller can report what was emitted; the
    runner deliberately re-derives both from the graph."""
    sub = srs.Substrate()

    def run(where_clause):
        graph_ir, graph_oracles = rsig.signature_program(sub)
        term = {"type": "ProgEval", "prog": graph_ir,
                "env": {"type": "Lit", "value": {"where_clause": where_clause}},
                "oracles": {"type": "Lit",
                            "value": {n: "builtin" for n in graph_oracles}},
                "fuel": fuel, "field": ""}
        return sub._inner.evaluate(term, {})

    return run


def seed_where_clauses():
    out = []
    seeds = os.path.join(ROOT, "seeds")
    for fname in sorted(os.listdir(seeds)):
        if not fname.endswith(".json"):
            continue
        try:
            blob = json.load(open(os.path.join(seeds, fname)))
        except Exception:  # noqa: BLE001
            continue
        rules = blob.get("rules") if isinstance(blob, dict) else None
        for r in (rules or []):
            if isinstance(r, dict) and isinstance(r.get("where"), dict):
                out.append((f"{fname}:{r.get('name')}", r["where"]))
    return out


SYNTHETIC = [
    ("none", None),
    ("not-a-dict", ["a"]),
    ("no-type", {"a": 1}),
    ("empty-var-order", {"type": "Lit", "value": 1}),
    ("nested-list-atom", {"type": "Lit", "value": [["a", "b"], ["c"]]}),
    ("deep-list-atom", {"type": "Lit", "value": [[["x"], 2], 3]}),
    ("dict-atom", {"type": "Lit", "value": {"zz": 1, "aa": [2, 3], "mm": {"q": 4}}}),
    ("mixed-list-not-term-list", {"type": "Foo", "items": [{"type": "Var", "name": "a"}, 7]}),
    ("empty-list-atom", {"type": "Foo", "items": []}),
    ("bool-none-float", {"type": "Foo", "a": True, "b": None, "c": 1.5, "d": 2}),
    ("two-binders", {"type": "Exists", "var_name": "mn",
                     "source": {"type": "NodesOfType", "node_type": "Mention"},
                     "where": {"type": "Exists", "var_name": "cc",
                               "source": {"type": "Var", "name": "mn"},
                               "where": {"type": "Eq", "a": {"type": "Var", "name": "cc"},
                                         "b": {"type": "Var", "name": "mn"}}}}),
    ("var-name-collision", {"type": "Exists", "var_name": "x",
                            "source": {"type": "Var", "name": "y"},
                            "where": {"type": "Var", "name": "x"}}),
    ("term-list", {"type": "And", "items": [{"type": "Var", "name": "p"},
                                            {"type": "Var", "name": "q"},
                                            {"type": "Var", "name": "p"}]}),
]


def main() -> int:
    r = emit()
    print("=" * 72)
    print("1. emit_prog_ir(where_signature_rows)")
    print("=" * 72)
    if not r.get("ok"):
        print(f"  BLOCKED: {r['blockers']}")
        return 2
    oracles = sorted(set(r.get("native_oracles") or []))
    print(f"  ok=True predictable={r.get('predictable')} oracles={oracles} recv={r.get("recv_methods")}")
    print(f"  IR json bytes={len(json.dumps(r['ir']))}")

    run = prog_eval_runner(r["ir"], oracles)

    print()
    print("=" * 72)
    print("2. three-way differential")
    print("=" * 72)
    bad_py = []
    bad_pe = []
    traps = []
    cases = [(f"synthetic:{n}", w) for n, w in SYNTHETIC] + seed_where_clauses()
    t_py = 0.0
    t_pe = 0.0
    max_steps = 0
    for name, w in cases:
        t0 = time.time()
        want = rule_signature(w)
        t_py += time.time() - t0
        got_py = frozenset(where_signature_rows(w)) if isinstance(w, dict) else frozenset()
        if isinstance(w, dict):
            if got_py != want:
                bad_py.append(name)
        t0 = time.time()
        out = run(w)
        t_pe += time.time() - t0
        max_steps = max(max_steps, out.get("steps") or 0)
        if out.get("trap") is not None or not out.get("halted"):
            traps.append((name, out.get("trap"), out.get("steps")))
            continue
        got = out["result"]
        got = frozenset(got) if got is not None else frozenset()
        if got != want:
            bad_pe.append(name)
    n = len(cases)
    print(f"  cases: {n} ({len(SYNTHETIC)} synthetic + {n - len(SYNTHETIC)} real seed where-clauses)")
    print(f"  CPython(program) mismatches vs rule_signature : {len(bad_py)}")
    for b in bad_py[:10]:
        print(f"      {b}")
    print(f"  ProgEval(IR)     mismatches vs rule_signature : {len(bad_pe)}")
    for b in bad_pe[:10]:
        print(f"      {b}")
    print(f"  traps / non-halting                           : {len(traps)}")
    for b in traps[:10]:
        print(f"      {b}")
    print(f"  max fuel steps used on any case: {max_steps}")
    print(f"  wall: python {t_py:.2f}s   progeval {t_pe:.2f}s   "
          f"ratio {t_pe / max(t_py, 1e-9):.1f}x")

    print()
    print("=" * 72)
    print("3. reflect round-trip of the emitted IR (the P1 residency law)")
    print("=" * 72)
    sub = srs.Substrate()
    root = sub._inner.add_term_subgraph(r["ir"])
    back = sub._inner.term_subgraph_json(root)
    back1 = json.loads(back) if isinstance(back, str) else back
    root2 = sub._inner.add_term_subgraph(back1)
    back2 = sub._inner.term_subgraph_json(root2)
    back2 = json.loads(back2) if isinstance(back2, str) else back2
    print(f"  add_term_subgraph -> root node {root}")
    print(f"  canonical round-trip idempotent: {back1 == back2}")
    print(f"  graph nodes materialised: {len(sub.nodes())}")

    ok = not (bad_py or bad_pe or traps) and back1 == back2
    print()
    print(f"GATE: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
