"""The MIGRATION WORKLIST: enumerate the genuine-faculty methods of curious_agent.py and classify
what each becomes. This is the bounded hand-work the converged analysis points to — NOT 456 methods
or 18.5k lines, but the ~dozens of faculty methods the agent actually composes from.

A "faculty" = a self.method() or bare-local call target that ISN'T a Term constructor / builtin /
graph op / collection op (those are mechanical). For each that is DEFINED in the file, classify by
its body shape into the action the migration takes:

  RULE         — writes self.<attr> / node.attrs[k]: a decision over state -> a graph Rule.
  GRAPH-BUILD  — calls tx/mind_graph add_node/add_edge: graph construction -> Rule effects.
  FACTORY      — returns a Term-constructor tree: a Term the agent owns -> a derived attr / seed.
  PRIMITIVE    — pure compute (np/math/arith over args, no self, no faculty) -> Layer-B / held op.
  COMPOSITION  — calls other faculty methods: composes sub-faculties (the recursive structure).
  IO/ADAPTER   — file/socket/external: stays world-adapter Python.

Run:  python -m scripts.faculty_worklist
"""
from __future__ import annotations

import ast
import collections

CTOR = {"Var", "Lit", "Attr", "TypeOf", "Eq", "Lt", "Lte", "Gt", "Gte", "Div", "Pow", "Minus",
        "Dot", "Union", "Neg", "Not", "Abs", "Sqrt", "Log", "Exp", "Count", "Pick", "Neighbours",
        "InNeighbours", "MapNeighbours", "Filter", "Exists", "Sum", "Prod", "MinOver", "MaxOver",
        "Plus", "Times", "And", "Or", "SetT", "Cat", "Min", "Max", "MkDict", "Vec", "In",
        "NodePattern", "Production", "Surface", "Field", "Term", "Rule"}
GRAPH_BASES = {"mind_graph", "tx", "substrate", "mind_substrate", "g", "graph", "s", "gr", "G"}
COLL_OPS = {"get", "append", "add", "update", "items", "keys", "values", "pop", "setdefault",
            "extend", "discard", "remove", "sort", "join", "split", "node", "nodes", "out_edges",
            "in_edges", "add_node", "add_edge", "neighbours", "edges", "attrs", "has_edge",
            "add_production", "transform"}
BUILTINS = set("len min max abs sum sorted set list dict tuple range enumerate zip map filter any "
               "all isinstance str int float bool round print getattr setattr hasattr id type next "
               "iter reversed frozenset field deque".split())
IO = {"open", "read", "write", "load", "dump", "loads", "dumps", "Path", "json", "socket"}


def faculty_targets(calls):
    fac = collections.Counter()
    for c in calls:
        f = c.func
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "self":
            fac[f.attr] += 1
        elif isinstance(f, ast.Name) and f.id not in CTOR and f.id not in BUILTINS:
            fac[f.id] += 1
    return fac


def classify_def(fn: ast.FunctionDef) -> str:
    writes_state = graph_build = returns_term = calls_faculty = calls_np = io = False
    for n in ast.walk(fn):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) \
                        and t.value.id == "self":
                    writes_state = True
                if isinstance(t, ast.Subscript):
                    writes_state = True
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                if isinstance(f.value, ast.Name) and f.value.id in GRAPH_BASES \
                        and f.attr in ("add_node", "add_edge", "add_production"):
                    graph_build = True
                if isinstance(f.value, ast.Name) and f.value.id == "np":
                    calls_np = True
                if isinstance(f.value, ast.Name) and f.value.id == "self":
                    calls_faculty = True
            if isinstance(f, ast.Name):
                if f.id in CTOR:
                    pass
                elif f.id in IO:
                    io = True
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Call):
            f = n.value.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else "")
            if nm in CTOR:
                returns_term = True
    if io:
        return "IO/ADAPTER"
    if graph_build:
        return "GRAPH-BUILD"
    if writes_state:
        return "RULE"
    if returns_term:
        return "FACTORY"
    if calls_faculty:
        return "COMPOSITION"
    if calls_np:
        return "PRIMITIVE"
    return "REVIEW"


def main() -> None:
    tree = ast.parse(open("domains/curious_agent.py").read())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    defs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    fac = faculty_targets(calls)
    defined = {nm: c for nm, c in fac.items() if nm.lstrip("_") and nm in defs}
    cats = collections.Counter()
    rows = []
    for nm, cnt in defined.items():
        kind = classify_def(defs[nm])
        cats[kind] += 1
        rows.append((cnt, nm, kind))
    rows.sort(reverse=True)
    print("=" * 74)
    print(f"FACULTY MIGRATION WORKLIST — {len(defined)} distinct faculty methods defined in-file")
    print(f"  (of {sum(fac.values())} faculty call sites; the rest of the file is mechanical)")
    print("=" * 74)
    for kind, c in cats.most_common():
        print(f"  {c:>4}  {kind}")
    print(f"\n  the worklist (call-count  method  -> action), top 30:")
    for cnt, nm, kind in rows[:30]:
        print(f"     {cnt:>4}  {nm:<34} -> {kind}")
    print("\n" + "=" * 74)
    print("  THIS is the migration: a few dozen faculty methods, each -> Rule / Term factory /")
    print("  primitive / kept-composition. The other ~80% of the file (constructors, graph ops,")
    print("  builtins, np) transcribes mechanically around them.")
    print("=" * 74)


if __name__ == "__main__":
    main()
