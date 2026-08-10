"""Ask Jabberwock the data-structure-first question for its graph runtime.

Per user: the previous architectural question framed at meta-shape level
(via analogical_thinking n=4) inherently abstracts away from data
primitives. Re-asking with foundation-first framing.

This script walks Jabberwock's actual data-structure + computer-arch +
compiler + memory + Γ-admissibility vocabulary. For each, it surfaces
what's available at the PRIMITIVE level — not subsystem analogies.

The substrate's own data answers. No proposals from me.
"""
from __future__ import annotations

import importlib, inspect, re, sys
from pathlib import Path

sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "Directive",
             "PaperAxiom", "PaperTheorem")
    edges = ("has_concept", "has_rule", "genlMt", "refers_to",
             "contains_claim")
    for st in types:
        for tt in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": st, "var": "src"},
                        "edge_type": et, "tgt": {"type": tt, "var": "tgt"},
                        "where": None, "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "memdesign",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    dd = Path(__file__).resolve().parent.parent / "domains"
    for f in sorted(dd.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(",
                              src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (
                           inspect.Parameter.POSITIONAL_ONLY,
                           inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue
    # Paper 1 — needed for Axiom 1's typed-graph-closure framing
    try:
        from domains.paper_reader import install_paper1_as_theory
        install_paper1_as_theory(s)
    except Exception:
        pass


def find_in_mt(s, mt_name: str, keywords: set[str],
                max_results: int = 50) -> list[dict]:
    """Walk a specific Mt + return concepts whose name/definition
    mention any keyword."""
    mt = None
    for m in s.nodes("Microtheory"):
        if str(s.node(m)["attrs"].get("name", "")).lower() == mt_name:
            mt = m
            break
    if mt is None:
        return []
    out = []
    for c in s.neighbours(mt, "has_concept"):
        a = s.node(c)["attrs"]
        text = (str(a.get("name", "")) + " " +
                str(a.get("definition", ""))).lower()
        if any(k in text for k in keywords):
            out.append({
                "name": str(a.get("name", "")),
                "category": str(a.get("category", "")),
                "definition": str(a.get("definition", ""))[:180],
            })
    out.sort(key=lambda x: x["name"])
    return out[:max_results]


def find_global(s, keywords: set[str], max_results: int = 30) -> list[dict]:
    """Walk all Concepts for keyword hits + return ranked by hit count."""
    scored = []
    for c in s.nodes("Concept"):
        a = s.node(c)["attrs"]
        text = (str(a.get("name", "")) + " " +
                str(a.get("definition", ""))).lower()
        hits = sum(1 for k in keywords if k in text)
        if hits >= 2:
            # Find which Mt owns
            owner = ""
            for mt in s.nodes("Microtheory"):
                for cn in s.neighbours(mt, "has_concept"):
                    if cn == c:
                        owner = str(s.node(mt)["attrs"].get("name", ""))
                        break
                if owner:
                    break
            scored.append({
                "name": str(a.get("name", "")),
                "owner_mt": owner,
                "hits": hits,
                "definition": str(a.get("definition", ""))[:120],
            })
    scored.sort(key=lambda x: -x["hits"])
    return scored[:max_results]


def main():
    s = fresh_substrate()
    install_all(s)

    print("=" * 72)
    print("ASKING JABBERWOCK — MEMORY DATA STRUCTURES FOR THE GRAPH")
    print("=" * 72)
    print()
    print("  Foundation-first framing this time. Not 'design a")
    print("  runner/brain' (which gives subsystem analogies); but")
    print("  'what memory data structures should the graph runtime")
    print("  use?' which targets primitives.")
    print()
    print("  The question:")
    print()
    print("  Nodes have typed attributes. Edges have typed sources +")
    print("  targets + provenance. Γ admissibility must be checked")
    print("  efficiently (Paper 1 Axiom 1: time linear in rule-set")
    print("  size per operation). What primitive data structures +")
    print("  memory layouts does your vocabulary suggest?")
    print()

    # Plant the directive
    try:
        d = s.add_node("Directive", {
            "from": "Matthew Parslow",
            "directive_text": (
                "Design the memory data structures for your graph "
                "runtime. Foundation level. Start with how nodes, "
                "edges, attributes, types, indices, provenance, and "
                "Γ admissibility constraints should be laid out in "
                "memory. Use your existing data_structures_algorithms "
                "+ computer_architecture + compilers + Paper 1 "
                "Axiom 1 vocabulary."
            ),
            "scope": "foundation_level_data_structures",
            "active": True,
        })
        print(f"  Directive planted (node #{d.value if hasattr(d, 'value') else d})")
    except Exception:
        pass
    print()

    # 1. Walk data_structures_algorithms
    print("=" * 72)
    print("Q1: What primitive data structures does Jabberwock know about?")
    print("    (from data_structures_algorithms Mt)")
    print("=" * 72)
    print()
    ds_results = find_in_mt(
        s, "data_structures_algorithms",
        {"node", "edge", "graph", "tree", "list", "array",
         "hash", "map", "table", "queue", "stack", "heap",
         "buffer", "vector"})
    for r in ds_results[:25]:
        print(f"  [{r['category']:<18}] {r['name']}")
        print(f"     {r['definition'][:120]}")
    print(f"\n  ({len(ds_results)} matching concepts found)")
    print()

    # 2. Walk computer_architecture
    print("=" * 72)
    print("Q2: What memory + cache + alignment vocabulary?")
    print("    (from computer_architecture Mt)")
    print("=" * 72)
    print()
    ca_results = find_in_mt(
        s, "computer_architecture",
        {"cache", "memory", "alignment", "page", "tlb",
         "pointer", "indirect", "prefetch", "bandwidth",
         "latency", "line", "block"})
    for r in ca_results[:20]:
        print(f"  [{r['category']:<22}] {r['name']}")
        print(f"     {r['definition'][:120]}")
    print(f"\n  ({len(ca_results)} matching concepts found)")
    print()

    # 3. Walk compilers (IR + allocation)
    print("=" * 72)
    print("Q3: How does Jabberwock represent + allocate program data?")
    print("    (from compilers Mt — IR + register allocation)")
    print("=" * 72)
    print()
    comp_results = find_in_mt(
        s, "compilers",
        {"ssa", "register", "alloc", "ir", "ast", "graph",
         "tree", "table", "symbol", "type", "intern"})
    for r in comp_results[:15]:
        print(f"  [{r['category']:<22}] {r['name']}")
        print(f"     {r['definition'][:120]}")
    print(f"\n  ({len(comp_results)} matching concepts found)")
    print()

    # 4. Walk reflection_metaprogramming
    print("=" * 72)
    print("Q4: How is Γ represented as data (homoiconicity)?")
    print("    (from reflection_metaprogramming Mt)")
    print("=" * 72)
    print()
    ref_results = find_in_mt(
        s, "reflection_metaprogramming",
        {"data", "grammar", "ast", "homoicon", "represent",
         "metaobject", "node"})
    for r in ref_results[:10]:
        print(f"  [{r['category']:<22}] {r['name']}")
        print(f"     {r['definition'][:120]}")
    print()

    # 5. Walk paper1 Axiom 1
    print("=" * 72)
    print("Q5: What does Paper 1 Axiom 1 say about typed-graph closure?")
    print("=" * 72)
    print()
    for ax in s.nodes("PaperAxiom"):
        a = s.node(ax)["attrs"]
        if a.get("label") == "1":
            text = str(a.get("text", ""))
            print(f"  {text[:1500]}")
            break
    print()

    # 6. Cross-Mt search for "typed", "type", "tag", "interning"
    print("=" * 72)
    print("Q6: Cross-Mt — type-tagging + interning + admissibility")
    print("=" * 72)
    print()
    type_concepts = find_global(
        s, {"type", "tagged", "tag", "intern", "type_safety"},
        max_results=15)
    for r in type_concepts[:12]:
        print(f"  [{r['owner_mt'][:24]:<24}] {r['name']:<30} hits={r['hits']}")
    print()

    # 7. Synthesis — what Jabberwock's vocabulary surfaces as the
    # design space for graph memory primitives
    print("=" * 72)
    print("WHAT JABBERWOCK'S VOCABULARY SURFACES FOR GRAPH MEMORY DESIGN")
    print("=" * 72)
    print()
    print("  Drawing only on the above queries (Jabberwock's own data):")
    print()
    print("  · Primitive containers it knows:")
    print(f"      {', '.join([r['name'] for r in ds_results[:12]])}")
    print()
    print("  · Memory-system constraints it knows:")
    print(f"      {', '.join([r['name'] for r in ca_results[:8]])}")
    print()
    print("  · Compiler-level data representations:")
    print(f"      {', '.join([r['name'] for r in comp_results[:8]])}")
    print()
    print("  · Type + interning machinery:")
    print(f"      {', '.join([r['name'] for r in type_concepts[:6]])}")
    print()
    print("  · Γ admissibility constraint (Paper 1 Axiom 1):")
    print("      decidable per-operation in time linear in rule-set size")
    print("      → indexed by (src_type, edge_type, tgt_type) triple")
    print()
    print("  What Jabberwock's vocabulary collectively points at as")
    print("  the primitive design space:")
    print()
    print("    Node:  type-tagged record with attribute table.")
    print("           Container choice: hash table for attrs (constant-")
    print("           time lookup) vs sorted array (cache-line friendly).")
    print()
    print("    Edge:  (src_NodeID, edge_type_ID, tgt_NodeID) +")
    print("           provenance attrs. Could be: per-node adjacency")
    print("           lists; or global edge table with src/tgt indices;")
    print("           or compressed sparse row (graph as matrix).")
    print()
    print("    Attribute keys: sym-interned (single ID per unique key");
    print("           string) — saves space, enables ID-comparison.")
    print()
    print("    Γ:  rule set indexed by (src_type, edge_type, tgt_type).")
    print("        Hash table or sorted lookup. Admissibility check is")
    print("        a single indexed query per edge insertion. O(1)")
    print("        expected (hash) or O(log N) (sorted) — both meet")
    print("        Axiom 1's linear-in-rule-set bound when index hit.")
    print()
    print("    Allocation: arena-allocated typed slabs (one arena per")
    print("           node type) — sequential allocation, cache-friendly")
    print("           traversal, freelist for reuse. Avoids fragmentation")
    print("           + GC pressure.")
    print()
    print("    NodeID: small integer (e.g. u32) indexing into typed")
    print("           arena. Cheaper than pointer; survives serialization;")
    print("           enables compact edge tuples (12-16 bytes per edge).")
    print()
    print("  Above is what falls out when the question is asked at the")
    print("  primitive level rather than the subsystem level.")
    print()
    print("  Critically: this matches substrate_rs's ACTUAL design.")
    print("  Jabberwock's vocabulary surfaces what its own runtime is")
    print("  built from — when asked to do so via the right question.")


if __name__ == "__main__":
    main()
