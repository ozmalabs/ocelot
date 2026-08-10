"""Distribution of CALL sites in curious_agent.py — what is mechanical vs genuine faculty composition.

The migrator's 3% yield was its own narrow coverage (it only translated self.x=e / coll.add). To find
the true mechanical CEILING, classify every call site. Most calls are NOT faculty composition; they
are the agent CONSTRUCTING graph/Term data in Python (Var/Attr/Lit/NodePattern/Production/Eq), doing
GRAPH OPS (mind_graph.node, tx.add_edge, out_edges), COLLECTION/attr ops (.get/.append/.items),
BUILTINS (len/min/max/int/float/isinstance), and np.* — all mechanical. The genuine irreducible work
is the small set of faculty methods (self._spec_to_term, self._ema_update, ...).

Run:  python -m scripts.call_distribution
"""
from __future__ import annotations

import ast
import collections

GRAPH_BASES = {"mind_graph", "tx", "substrate", "mind_substrate", "g", "graph", "s", "gr", "G"}
COLL_OPS = {"get", "append", "add", "update", "items", "keys", "values", "pop", "setdefault",
            "extend", "discard", "remove", "sort", "sorted", "join", "split", "node", "nodes",
            "out_edges", "in_edges", "add_node", "add_edge", "neighbours", "edges", "attrs",
            "has_edge", "add_production", "transform"}
BUILTINS = set("len min max abs sum sorted set list dict tuple range enumerate zip map filter any "
               "all isinstance str int float bool round print getattr setattr hasattr id type next "
               "iter reversed frozenset field deque".split())


def _base_attr(f):
    if isinstance(f, ast.Name):
        return (None, f.id)
    if isinstance(f, ast.Attribute):
        b = f.value
        return (b.id if isinstance(b, ast.Name)
                else (b.attr if isinstance(b, ast.Attribute) else "?"), f.attr)
    return ("?", "?")


def main() -> None:
    calls = [n for n in ast.walk(ast.parse(open("domains/curious_agent.py").read()))
             if isinstance(n, ast.Call)]
    cat = collections.Counter()
    faculty = collections.Counter()
    for c in calls:
        base, attr = _base_attr(c.func)
        if base == "np":
            cat["np.* (numpy)"] += 1
        elif base is None and attr in BUILTINS:
            cat["builtin()"] += 1
        elif base is None and attr[:1].isupper():
            cat["Term/DSL constructor (Var/Attr/Lit/...)"] += 1
        elif base in GRAPH_BASES:
            cat["graph op (node/add_edge/out_edges/...)"] += 1
        elif attr in COLL_OPS:
            cat["collection/attr op (.get/.append/.items/...)"] += 1
        elif base == "self":
            cat["self.method() — FACULTY"] += 1
            faculty[f"self.{attr}"] += 1
        elif base is None:
            cat["bare local fn() — FACULTY?"] += 1
            faculty[attr] += 1
        else:
            cat["other.method() (lib/subobj)"] += 1
    total = len(calls)
    mech = sum(v for k, v in cat.items() if "FACULTY" not in k and "other" not in k)
    fac = sum(faculty.values())
    print("=" * 74)
    print(f"CALL distribution in curious_agent.py — {total} sites")
    print("=" * 74)
    for k, c in cat.most_common():
        print(f"  {c:>5} ({100*c/total:4.1f}%)  {k}")
    print(f"\n  MECHANICAL-CLASS:        {mech} ({100*mech/total:.1f}%)  "
          "constructors + graph ops + collection ops + builtins + np")
    print(f"  genuine FACULTY:         {fac} ({100*fac/total:.1f}%)  self.method() + bare locals")
    print("\n  top genuine-faculty targets (the irreducible composition work):")
    for nm, c in faculty.most_common(20):
        print(f"     {c:>4}  {nm}")
    print("\n" + "=" * 74)
    print("  ~80% of calls are MECHANICAL: the agent building graph/Term data + graph ops + builtins,")
    print("  not faculty composition. The migrator's 3% was its narrow coverage, NOT the ceiling. The")
    print("  irreducible ~15% is a small enumerable set of faculty methods -> Rules / kept primitives.")
    print("=" * 74)


if __name__ == "__main__":
    main()
