"""Run the assess->triage loop across a BATCH (the competitive_inhibition bucket).
Per faculty: the AGENT assigns the cognitive shape (categorise_by_shape, its own
faculty); concrete CODE-FACTS (AST/source, not invented categories) separate the
HOST form:
  · already_graph_native  — the module CONSTRUCTS Term-JSON / Argmax-Times terms
                            (the decision is the graph Term it builds) -> KEEP.
  · adapter_io            — *_world/*_pipeline or byte/sample I/O -> KEEP.
  · decision_candidate    — reads substrate state, BRANCHES, and mutates
                            (add_rule/set_attr/add_node) -> a genuine Python
                            decision = the real migrate-to-graph target.
  · thin_helper           — none of the above -> KEEP/fold.
Output = the real migration BACKLOG (the decision_candidates), the only faculties
where the per-faculty rung-2 design+burn would actually change anything.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_batch_loop.py
"""
from __future__ import annotations
import ast, glob, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.teach import categorise_by_shape
from domains.analogical_thinking import shape_hits


def _dom_shape(agent, text):
    """the agent's per-concept dominant shape — the agent's own classifier
    (graph vocabulary + a Term run by Rust), no Python keyword table."""
    return shape_hits(agent, text)


def _faculty_dominant_shape(agent, path):
    try:
        tree = ast.parse(open(path).read())
    except Exception:
        return None
    v = Counter()
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for s in _dom_shape(agent, n.name.replace("_", " ") + " " + (ast.get_docstring(n) or "")):
                v[s] += 1
    return v.most_common(1)[0][0] if v else None


def _host_form(src, mod):
    builds_term = ('{"type":' in src or "_Argmax(" in src or "_Times(" in src
                   or "'type':" in src and "Lit" in src)
    adapter = (mod.endswith("_world") or mod.endswith("_pipeline")
               or any(s in src for s in ("sample_rate", "wav", "cochlea", "pixels",
                                         "read_bytes", "ingest", "mic", "stt")))
    reads = any(s in src for s in (".node(", ".nodes(", "neighbours(", "nodes_where("))
    branches = bool(re.search(r"\n\s+if ", src))
    mutates = any(s in src for s in ("add_rule(", "set_attr(", "add_node(", "add_edge("))
    if builds_term:
        return "already_graph_native"
    if adapter:
        return "adapter_io"
    if reads and branches and mutates:
        return "decision_candidate"
    return "thin_helper"


def main() -> int:
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.set_self_teacher(lambda q: "")   # donkey present-but-silent (we never ask)

    faculties = [(os.path.basename(p)[:-3], p)
                 for p in sorted(glob.glob(os.path.join(ROOT, "domains", "*.py")))
                 if os.path.basename(p) != "__init__.py"]

    print("=" * 84)
    print(f"BATCH LOOP over ALL {len(faculties)} faculties — assess (agent) + host-form triage")
    print("=" * 84)
    verdicts = Counter()
    by_shape = Counter()
    backlog = []
    for mod, p in faculties:
        src = open(p).read()
        shape = _faculty_dominant_shape(agent, p)
        if shape:
            by_shape[shape] += 1
        # the AGENT confirms a shape from the faculty's own docstring (its faculty)
        doc = ast.get_docstring(ast.parse(src)) or mod
        categorise_by_shape(agent, "Faculty", {"description": doc[:400]})
        form = _host_form(src, mod)
        verdicts[form] += 1
        if form == "decision_candidate":
            backlog.append((mod, src.count("\n") + 1, shape))
    print("  host-form verdicts:")
    for f, c in verdicts.most_common():
        print(f"     {f}: {c}")
    bl = sum(x[1] for x in backlog)
    print(f"\n  MIGRATION BACKLOG = genuine Python decisions (rung-2 design+burn): "
          f"{len(backlog)} faculties, {bl} lines")
    for mod, loc, shape in sorted(backlog, key=lambda x: -x[1]):
        print(f"     {mod} ({loc} lines) [{shape}]")
    print("=" * 84)
    keep = verdicts["already_graph_native"] + verdicts["adapter_io"] + verdicts["thin_helper"]
    print(f"  VERDICT: of {len(faculties)} faculties, {keep} are already-native / adapters / helpers "
          f"(KEEP); {len(backlog)} are genuine Python-decision migration targets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
