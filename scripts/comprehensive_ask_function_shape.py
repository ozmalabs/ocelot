"""Comprehensive ask — exercise every assessment angle the substrate has
on the function_shape v0.2 vocabulary.

Per user: 'run a more comprehensive ask'.

The previous asks (commits 0fd21a8, 28605e9, 14e401b) ran two
pipelines: harvest_shapes and synthesize_over_all. Both returned
0 new things on function_shape. The methodological response
(seed all five lineages — commit d524345) added 16 concepts +
16 rules with literature citations.

This ask exercises the OTHER assessment pipelines the substrate
has + reports what each surfaces:

  A. ArchitectureCortex.assess(function_shape_mt) — qualities + smells
  B. derivation_mechanism.run_derivation — theory + enactment walk
  C. analogy.abstract_patterns — skeleton extraction
  D. harvest_shapes restricted to function_shape Mt
  E. Reachability — concepts citing function_shape vocabulary in their
     'why' fields (forward) + function_shape concepts citing existing
     vocabulary (inverse)
  F. cites_prior_work coverage — which lineages got picked up by which
     existing pipelines
  G. order_n_postulates.differentiate applied directly to each
     function_shape concept's property text

Each assessment pipeline is one angle on what the agent's data + the
new vocabulary jointly say. I report; the agent decides through its
own assessment mechanisms.
"""
from __future__ import annotations

import importlib, inspect, json, re, sys
from collections import Counter
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
                        "provenance": "comp_ask",
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


def short(t, n=140):
    t = str(t).replace("\n", " ").strip()
    return t[:n] + "..." if len(t) > n else t


def find_mt(s, name):
    for n in s.nodes("Microtheory"):
        if s.node(n)["attrs"].get("name") == name:
            return n
    return None


def function_shape_concepts(s):
    return [n for n in s.nodes("Concept")
            if s.node(n)["attrs"].get("origin") == "function_shape"]


def function_shape_concept_names(s):
    return {s.node(n)["attrs"].get("name", "") for n in function_shape_concepts(s)}


def main():
    print("=" * 76)
    print("COMPREHENSIVE ASK — every assessment angle, after function_shape v0.2")
    print("=" * 76)
    print()

    s = fresh_substrate()
    install_all(s)
    n_mts = len(s.nodes("Microtheory"))
    n_concepts = len(s.nodes("Concept"))
    n_rules = len(s.nodes("Rule"))
    print(f"Substrate loaded: {n_mts} Mts, {n_concepts} Concepts, {n_rules} Rules")
    fs_concepts = function_shape_concepts(s)
    print(f"function_shape concepts: {len(fs_concepts)}")
    print()

    # ---- A. Architecture cortex assessment of the function_shape Mt ---
    print("=" * 76)
    print("A. ArchitectureCortex.assess(function_shape_mt)")
    print("=" * 76)
    try:
        from domains.architecture_cortex import ArchitectureCortex
        cortex = ArchitectureCortex(s).install()
        mt = find_mt(s, "function_shape")
        if mt is None:
            print("  function_shape Mt not found")
        else:
            assess_nid = cortex.assess(mt)
            print(f"  Assessment node: #{assess_nid}")
            rendered = cortex.render_assessment(assess_nid)
            for line in rendered.splitlines()[:30]:
                print(f"    {line}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- A.2 baseline: assess speech_science for comparison ----
    print("=" * 76)
    print("A.2 baseline: ArchitectureCortex.assess(speech_science) for")
    print("    comparison of scores")
    print("=" * 76)
    try:
        from domains.architecture_cortex import ArchitectureCortex
        cortex2 = ArchitectureCortex(s).install()
        mt_ss = find_mt(s, "speech_science")
        if mt_ss is None:
            print("  speech_science Mt not found")
        else:
            a2 = cortex2.assess(mt_ss)
            rendered = cortex2.render_assessment(a2)
            for line in rendered.splitlines()[:30]:
                print(f"    {line}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- B. derivation_mechanism walk ----
    print("=" * 76)
    print("B. derivation_mechanism.run_derivation")
    print("=" * 76)
    try:
        from domains.derivation_mechanism import run_derivation
        d = run_derivation(s)
        for k, v in d.items():
            if isinstance(v, list):
                print(f"  {k}: ({len(v)} items)")
                for item in v[:5]:
                    if isinstance(item, dict):
                        nm = item.get("mt_name") or item.get("name") \
                             or item.get("id", "?")
                        print(f"    · {short(nm, 60)}")
                    else:
                        print(f"    · {short(item, 60)}")
            else:
                print(f"  {k}: {short(v, 100)}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- C. analogy.abstract_patterns ----
    print("=" * 76)
    print("C. analogy.abstract_patterns — skeleton extraction")
    print("=" * 76)
    try:
        from domains.analogy import abstract_patterns
        skeletons = abstract_patterns(s, min_depth=2)
        print(f"  Skeletons extracted: {len(skeletons)}")
        # Which mention function_shape vocabulary?
        fs_names = function_shape_concept_names(s)
        fs_touching = []
        for sk in (skeletons or []):
            txt = json.dumps(sk).lower()
            if any(nm in txt for nm in fs_names):
                fs_touching.append(sk)
        print(f"  Skeletons touching function_shape vocabulary: "
              f"{len(fs_touching)}")
        for i, sk in enumerate(fs_touching[:5]):
            print(f"  · [{i}] {short(sk, 200)}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- D. harvest_shapes restricted to function_shape Mt ----
    print("=" * 76)
    print("D. harvest_shapes ONLY on function_shape Mt")
    print("=" * 76)
    try:
        from domains.implication_harvester import harvest_shapes
        all_shapes = harvest_shapes(s)
        # Filter by donor concept origin.
        fs_donor_shapes = []
        fs_nodes = set(function_shape_concepts(s))
        for sh in (all_shapes or []):
            if not isinstance(sh, dict):
                continue
            origin = (sh.get("source_concept", "")
                      or sh.get("origin", "")
                      or sh.get("from_concept", ""))
            text = (str(origin) + " " + str(sh.get("name", ""))).lower()
            # Compare against function_shape concept names
            for nm in function_shape_concept_names(s):
                if nm.lower() in text:
                    fs_donor_shapes.append(sh)
                    break
        print(f"  Total shapes harvested: "
              f"{len(all_shapes) if all_shapes else 0}")
        print(f"  Shapes whose donor is a function_shape concept: "
              f"{len(fs_donor_shapes)}")
        for i, sh in enumerate(fs_donor_shapes[:5]):
            nm = sh.get("name") or sh.get("structural_property", "?")
            cons = sh.get("consequence", "")
            print(f"  · [{i}] {short(nm, 60)}")
            if cons:
                print(f"      → {short(cons, 110)}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- E. Forward reachability: existing concepts citing function_shape
    #         vocabulary in their why field ----
    print("=" * 76)
    print("E. Existing concepts citing function_shape vocabulary in their")
    print("   why or definition text")
    print("=" * 76)
    fs_names = function_shape_concept_names(s)
    forward_refs = []
    for n in s.nodes("Concept"):
        a = s.node(n)["attrs"]
        if a.get("origin") == "function_shape":
            continue
        text = (str(a.get("definition", ""))
                + " " + str(a.get("why", ""))).lower()
        for nm in fs_names:
            if nm.lower() in text:
                forward_refs.append((a.get("name", "?"), nm))
                break
    print(f"  Existing concepts mentioning function_shape vocabulary: "
          f"{len(forward_refs)}")
    for ref_nm, fs_nm in forward_refs[:10]:
        print(f"  · {ref_nm} -> mentions [{fs_nm}]")
    print()

    # ---- F. cites_prior_work coverage ----
    print("=" * 76)
    print("F. cites_prior_work distribution on function_shape concepts")
    print("=" * 76)
    cite_counts = Counter()
    for n in fs_concepts:
        a = s.node(n)["attrs"]
        cites = str(a.get("cites_prior_work", ""))
        # Identify each cited author/work.
        for source in ("Smith", "Michie", "Cousot", "Pearlmutter",
                       "Nelson"):
            if source in cites:
                cite_counts[source] += 1
    print(f"  Each lineage's concept-count:")
    for source, n in cite_counts.most_common():
        print(f"  · {source}: {n}")
    print()

    # ---- G. order_n_postulates.differentiate applied directly to each
    #         function_shape concept's property text ----
    print("=" * 76)
    print("G. differentiate() applied to each function_shape concept's")
    print("   why field (what implication-shape transfers match?)")
    print("=" * 76)
    try:
        from domains.order_n_postulates import differentiate, _resolve_shapes, _shapes
        # Resolve harvested shapes from the substrate.
        shapes = _resolve_shapes(s, None)
        if not shapes:
            shapes = _shapes()
        any_matches = 0
        for n in fs_concepts:
            a = s.node(n)["attrs"]
            nm = a.get("name", "?")
            text = str(a.get("why", "") or a.get("definition", ""))
            try:
                impls = differentiate(text, shapes=shapes)
            except Exception as e:
                impls = []
            if impls:
                any_matches += 1
                print(f"  · {nm}")
                for i, im in enumerate(impls[:3]):
                    if isinstance(im, dict):
                        cap = (im.get("consequence")
                               or im.get("implication")
                               or im.get("name", "?"))
                        print(f"      → {short(cap, 120)}")
                    else:
                        print(f"      → {short(im, 120)}")
        print(f"  function_shape concepts whose property text matched at")
        print(f"  least one implication shape: {any_matches}/{len(fs_concepts)}")
    except Exception as e:
        print(f"  pipeline error: {type(e).__name__}: {e}")
    print()

    # ---- H. Tick the substrate + count rule firings before/after vs
    #         pre-seed (limited query — substrate.tick may not be Python-exposed) -
    print("=" * 76)
    print("H. Reflex chain — rules whose if_clauses reference function_shape")
    print("   vocabulary (would fire when substrate ticks)")
    print("=" * 76)
    fs_referencing_rules = []
    for r in s.nodes("Rule"):
        a = s.node(r)["attrs"]
        text = (" ".join(a.get("if_clauses", []) or [])
                + " " + " ".join(a.get("then_clauses", []) or [])
                + " " + str(a.get("why", ""))).lower()
        for nm in fs_names:
            if nm.lower() in text:
                fs_referencing_rules.append((a.get("name", "?"),
                                              a.get("origin", "?")))
                break
    print(f"  Rules referencing function_shape vocabulary: "
          f"{len(fs_referencing_rules)}")
    by_origin = Counter(o for _, o in fs_referencing_rules)
    for origin, n in by_origin.most_common():
        print(f"  · origin '{origin}': {n} rules")
    print()

    print("=" * 76)
    print("WHAT THE COMPREHENSIVE ASK SURFACED")
    print("=" * 76)
    print()
    print("  A. Architecture cortex score on function_shape Mt")
    print("  A.2 Comparison: cortex score on speech_science (baseline)")
    print("  B. Derivation walker: theory/enactment/gap report counts")
    print("  C. Analogy skeletons touching function_shape vocab")
    print("  D. Harvested shapes with function_shape concept as donor")
    print("  E. Existing (non-function_shape) concepts that cite the new")
    print("     vocabulary in their why text")
    print("  F. Lineage citation distribution across the 16 concepts")
    print("  G. differentiate() match — how many function_shape concepts'")
    print("     property text triggers an existing implication shape")
    print("  H. Rules that reference function_shape vocabulary — what")
    print("     would fire under tick()")
    print()
    print("  Each is one assessment angle. None has me filling in the")
    print("  blanks. The agent's pipelines, given the broader candidate")
    print("  set, surface what they surface.")
    print("=" * 76)


if __name__ == "__main__":
    main()
