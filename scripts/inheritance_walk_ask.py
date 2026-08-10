"""Fourth ask — pipelines that walk Mt INHERITANCE, not concept text.

Per user: option 1 — "run a fourth ask exercising pipelines that walk
Mt inheritance (genlMt-walker, transitive cited-by closure) rather
than concept-text extractors".

The first three asks queried text-pattern pipelines (harvester,
differentiate, abstract_patterns). All returned 0 hits on
function_shape vocabulary — consistent with the structural-delta
finding (concepts are meta-level, extractors expect concrete-domain
facts). The L6 attachment (commit 5358406) changed the INHERITANCE
graph but not the surface text. This ask exercises pipelines
sensitive to the inheritance change:

  A. genlMt transitive closure — parents + descendants of
     function_shape
  B. ArchitectureCortex on the parent Mts — did L6's compositional_
     reuse and computer_architecture's go up after the attachment?
  C. Rule reachability via inheritance — does any L6 rule now fire on
     function_shape concept names?
  D. Concept reachability via genlMt — what concepts become visible
     from function_shape via the inheritance chain?
  E. Lineage closure — for each L6 concept function_shape bridges to,
     what implication shapes does the harvester find IN THE L6
     CONCEPT itself (which function_shape inherits semantics from)?
  F. derivation_mechanism gap report on function_shape Mt specifically
  G. genlMt-cycle check — does the function_shape -> L6 attachment
     create any inheritance cycles or interesting transitive paths?

Each query walks edges, not text.
"""
from __future__ import annotations

import importlib, inspect, json, re, sys
from collections import deque, Counter
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule",
        "PrimitiveSpec", "Assessment", "QualityScore", "SmellInstance",
        "ArchitectureCortex", "TheoryEnactmentGap",
        "SynthesizedGap", "ImplicationShape", "Postulate",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt",
        "refers_to", "owns_microtheory", "assesses", "produced",
        "scored_on", "detected_smell", "for_quality", "for_smell",
        "applies_to", "implements", "implies", "derives_from",
        "has_gap_report", "classified_as", "cites",
    )
    for t in types:
        for u in types:
            for et in edges:
                try:
                    s.add_production({
                        "src": {"type": t, "var": "a"},
                        "edge_type": et,
                        "tgt": {"type": u, "var": "b"},
                        "where": None,
                        "weight": {"type": "Lit", "value": 1.0},
                        "provenance": "inh_walk",
                    })
                except Exception:
                    pass
    return s


def install_all(s):
    domains_dir = ROOT / "domains"
    for f in sorted(domains_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        src = f.read_text()
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                sig = inspect.signature(fn)
                pos = [p for p in sig.parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                      inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(pos) == 1:
                    fn(s)
            except Exception:
                continue


def find_mt(s, name):
    for n in s.nodes("Microtheory"):
        if s.node(n)["attrs"].get("name") == name:
            return n
    return None


def short(t, n=140):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def walk_genlMt_ancestors(s, start_mt):
    """Transitive closure of genlMt edges from start_mt (going up the
    inheritance tree). Returns list of (mt_nid, mt_name, depth) tuples."""
    seen = {start_mt}
    out = []
    queue = deque([(start_mt, 0)])
    while queue:
        mt, d = queue.popleft()
        for parent in s.neighbours(mt, "genlMt"):
            if parent in seen:
                continue
            seen.add(parent)
            name = s.node(parent)["attrs"].get("name", "?")
            out.append((parent, name, d + 1))
            queue.append((parent, d + 1))
    return out


def walk_genlMt_descendants(s, target_mt):
    """Which Mts inherit (directly or transitively) FROM target_mt."""
    # Build reverse genlMt index by walking everyone.
    descendants = []
    seen = {target_mt}
    queue = deque([target_mt])
    while queue:
        cur = queue.popleft()
        for other_mt in s.nodes("Microtheory"):
            if other_mt in seen:
                continue
            if cur in s.neighbours(other_mt, "genlMt"):
                seen.add(other_mt)
                name = s.node(other_mt)["attrs"].get("name", "?")
                descendants.append((other_mt, name))
                queue.append(other_mt)
    return descendants


def main():
    print("=" * 76)
    print("INHERITANCE-WALK ASK — pipelines that walk genlMt, not text")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    n_mts = len(s.nodes("Microtheory"))
    n_concepts = len(s.nodes("Concept"))
    print(f"Substrate: {n_mts} Mts, {n_concepts} Concepts")
    fs_mt = find_mt(s, "function_shape")
    l6_mt = find_mt(s, "universal_coordination")
    ca_mt = find_mt(s, "computer_architecture")
    ct_mt = find_mt(s, "compiler_theory")
    print(f"function_shape Mt: {fs_mt}")
    print(f"universal_coordination (L6) Mt: {l6_mt}")
    print(f"computer_architecture Mt: {ca_mt}")
    print(f"compiler_theory Mt: {ct_mt}")
    print()

    # ---- A. genlMt transitive closure ----
    print("=" * 76)
    print("A. genlMt transitive closure from function_shape (UP)")
    print("=" * 76)
    ancestors = walk_genlMt_ancestors(s, fs_mt)
    print(f"  function_shape ancestors via genlMt: {len(ancestors)}")
    for nid, name, depth in sorted(ancestors, key=lambda x: x[2]):
        marker = "  " * depth
        print(f"  {marker}↑ depth {depth}: {name}")
    print()

    print("=" * 76)
    print("A.2 genlMt transitive descendants of function_shape (DOWN)")
    print("=" * 76)
    descendants = walk_genlMt_descendants(s, fs_mt)
    print(f"  function_shape descendants: {len(descendants)}")
    for nid, name in descendants:
        print(f"  ↓ {name}")
    if not descendants:
        print("  (none — function_shape is currently a leaf in the inheritance tree)")
    print()

    # ---- B. ArchitectureCortex on the PARENT Mts ----
    print("=" * 76)
    print("B. ArchitectureCortex re-assessment on the parent Mts")
    print("   (does L6 or computer_architecture compositional_reuse rise")
    print("    now that function_shape inherits from them?)")
    print("=" * 76)
    try:
        from domains.architecture_cortex import ArchitectureCortex
        cortex = ArchitectureCortex(s).install()
        for parent_name in ["universal_coordination", "computer_architecture",
                              "compiler_theory"]:
            mt = find_mt(s, parent_name)
            if mt is None:
                print(f"  {parent_name}: not found")
                continue
            assess_nid = cortex.assess(mt)
            rendered = cortex.render_assessment(assess_nid)
            # Extract overall + compositional_reuse + introspectability
            print(f"  {parent_name}:")
            for line in rendered.splitlines():
                line = line.strip()
                if line.startswith("overall:") or "compositional_reuse" in line \
                        or "introspectability" in line:
                    print(f"    {line}")
            print()
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- C. Rule reachability via inheritance ----
    print("=" * 76)
    print("C. Rules in the genlMt-ancestors of function_shape — how many")
    print("   reference function_shape's now-visible vocabulary?")
    print("=" * 76)
    # function_shape concept names
    fs_concept_names = set()
    for n in s.nodes("Concept"):
        a = s.node(n)["attrs"]
        if a.get("origin") == "function_shape":
            fs_concept_names.add(a.get("name", "").lower())

    ancestor_mts = set(nid for nid, _, _ in ancestors)
    # Rules attached to ancestor Mts: walk has_rule
    rules_in_ancestors = set()
    for mt in ancestor_mts:
        for r in s.neighbours(mt, "has_rule"):
            rules_in_ancestors.add(r)
    print(f"  Rules attached to function_shape's genlMt ancestors: "
          f"{len(rules_in_ancestors)}")
    matching = 0
    for r in rules_in_ancestors:
        a = s.node(r)["attrs"]
        text = (" ".join(a.get("if_clauses", []) or [])
                + " " + " ".join(a.get("then_clauses", []) or [])
                + " " + str(a.get("why", ""))).lower()
        if any(nm in text for nm in fs_concept_names if nm):
            matching += 1
    print(f"  Ancestor rules referencing function_shape vocabulary: {matching}")
    print()

    # ---- D. Concept reachability via genlMt ----
    print("=" * 76)
    print("D. All concepts reachable from function_shape via genlMt -> has_concept")
    print("   (the inheritance vocabulary closure)")
    print("=" * 76)
    reachable_mts = {fs_mt} | ancestor_mts
    reachable_concepts = set()
    for mt in reachable_mts:
        for c in s.neighbours(mt, "has_concept"):
            reachable_concepts.add(c)
    print(f"  Mts in reachable closure: {len(reachable_mts)}")
    print(f"  Concepts reachable via genlMt + has_concept: "
          f"{len(reachable_concepts)}")
    by_origin = Counter()
    for c in reachable_concepts:
        a = s.node(c)["attrs"]
        by_origin[a.get("origin", "?")] += 1
    print(f"  By origin:")
    for orig, cnt in by_origin.most_common(10):
        print(f"    · {orig}: {cnt}")
    print()

    # ---- E. Lineage closure — implication shapes from L6 concepts that
    #         function_shape's bridge rules name ----
    print("=" * 76)
    print("E. Lineage closure — which L6 concepts function_shape bridges to")
    print("   ARE themselves implication-shape donors?")
    print("=" * 76)
    # The 6 L6 concepts the v0.3 attachment rules name:
    bridged_l6 = [
        "second_order_observation_of_substrate",
        "bounded_coordination_latency",
        "circular_causality_between_layers",
        "ashby_variety_match_at_system_scale",
        "every_layer_feeds_every_other_via_named_signal",
        "viability_envelope_as_design_constraint",
    ]
    try:
        from domains.implication_harvester import harvest_shapes
        shapes = harvest_shapes(s) or []
        for l6_name in bridged_l6:
            matching_shapes = []
            for sh in shapes:
                if not isinstance(sh, dict):
                    continue
                origin = (sh.get("source_concept", "")
                          or sh.get("origin", "")
                          or sh.get("from_concept", ""))
                text = str(origin) + " " + str(sh.get("name", ""))
                if l6_name in text.lower():
                    matching_shapes.append(sh)
            tag = "✓" if matching_shapes else " "
            print(f"  [{tag}] {l6_name}: "
                  f"{len(matching_shapes)} shapes harvested from this concept")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- F. derivation_mechanism gap report for function_shape Mt ----
    print("=" * 76)
    print("F. derivation_mechanism gap report SPECIFICALLY for function_shape")
    print("=" * 76)
    try:
        from domains.derivation_mechanism import run_derivation
        d = run_derivation(s)
        gaps = d.get("gaps", [])
        for g in gaps:
            if isinstance(g, dict) and g.get("mt_name") == "function_shape":
                print(f"  function_shape gap report:")
                for k, v in g.items():
                    if isinstance(v, list):
                        print(f"    {k}: ({len(v)} items)")
                        for it in v[:5]:
                            print(f"      · {short(it, 100)}")
                    else:
                        print(f"    {k}: {short(v, 200)}")
                break
        else:
            print("  function_shape gap report not found in run_derivation output")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- G. genlMt structural facts ----
    print("=" * 76)
    print("G. Structural facts about the inheritance attachment")
    print("=" * 76)
    # Does function_shape inherit (transitively) from both intended parents?
    ancestor_names = {n for _, n, _ in ancestors}
    print(f"  function_shape inherits from L6 (universal_coordination): "
          f"{'YES' if 'universal_coordination' in ancestor_names else 'NO'}")
    print(f"  function_shape inherits from computer_architecture: "
          f"{'YES' if 'computer_architecture' in ancestor_names else 'NO'}")
    print(f"  function_shape inherits from compiler_theory (transitively): "
          f"{'YES' if 'compiler_theory' in ancestor_names else 'NO'}")
    # Inheritance depth
    if ancestors:
        max_depth = max(d for _, _, d in ancestors)
        print(f"  Inheritance depth of deepest ancestor: {max_depth}")
    # L6's descendants — does function_shape appear?
    if l6_mt:
        l6_descendants = walk_genlMt_descendants(s, l6_mt)
        names = {n for _, n in l6_descendants}
        print(f"  L6 (universal_coordination) now has "
              f"{len(l6_descendants)} descendants: "
              f"{', '.join(sorted(names)) if names else '(none)'}")
    print()

    # ---- bottom line ----
    print("=" * 76)
    print("WHAT THE INHERITANCE-WALK SURFACED")
    print("=" * 76)
    print()
    print("  A. function_shape ancestor chain (UP via genlMt)")
    print("  A.2 function_shape descendants (DOWN via genlMt)")
    print("  B. Cortex score on parent Mts — did L6's compositional_reuse")
    print("     rise with function_shape now inheriting?")
    print("  C. Rules in ancestor Mts that reference fs vocabulary")
    print("  D. All concepts reachable via genlMt+has_concept from fs")
    print("  E. Lineage closure: do the L6 concepts fs bridges TO act as")
    print("     implication-shape donors themselves?")
    print("  F. Derivation gap report specific to function_shape")
    print("  G. Structural facts about the attachment (depth, descendants,")
    print("     inheritance reaches expected targets)")
    print()
    print("  Each query walks edges. The agent's data answers via the")
    print("  graph topology, not via text matching.")
    print("=" * 76)


if __name__ == "__main__":
    main()
