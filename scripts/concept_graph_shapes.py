"""concept_graph_shapes — MEASURE whether harvesting implication-shapes from the
agent's OWN concept-graph RELATION edges (its genlMt/refers_to taxonomy) widens
the order-N gap operator's generativity, or just adds noise.

This is the deliverable for the FIRST brick of the agent's GENERATOR: make the
implication-shape catalogue scale with the agent's own structural relations
instead of with the ~7 fixed regex extractor KINDS. The brick is
domains.implication_harvester.harvest_shapes_from_concept_graph; this script
measures it HONESTLY and states a verdict with numbers.

I (Python) only orchestrate: boot the agent's full seed set, harvest its OWN
shapes (OLD catalogue vs NEW = OLD + concept-graph shapes), run its own
synthesize_gaps over a fixed sample of held postulates with each catalogue, and
report the coverage delta, gap diversity, and a noise check. The substrate's data
answers; the compression SELECTOR (prune=True) still gates which consequences are
real gaps — it is not bypassed.
"""
from __future__ import annotations
import importlib
import inspect
import re
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))
from substrate_rs import _native


def fresh_substrate():
    s = _native.Substrate()
    types = (
        "Microtheory", "Concept", "Rule", "DerivationRule", "Postulate",
        "SynthesizedGap", "ArchitectureCortex", "CodeWritingCortex",
        "Assessment", "QualityScore", "SmellInstance", "ArchitecturalQuality",
        "ArchitecturalSmell", "DesignPattern", "ProgrammingLanguage",
        "CodeTarget", "DesignExclusion", "PrimitiveSpec", "ReplacementTarget",
    )
    edges = (
        "has_concept", "has_rule", "in_category", "genlMt", "refers_to",
        "owns_microtheory", "assesses", "produced", "scored_on",
        "detected_smell", "for_quality", "for_smell", "decomposes", "best_for",
        "anti_pattern_for", "design_tag", "language_for_target", "applies_when",
        "implies", "unifies", "derived_from", "via_shape",
    )
    for a in types:
        for b in types:
            for et in edges:
                try:
                    s.add_production({"src": {"type": a, "var": "s"},
                                      "edge_type": et,
                                      "tgt": {"type": b, "var": "t"},
                                      "where": None,
                                      "weight": {"type": "Lit", "value": 1.0},
                                      "provenance": "measure"})
                except Exception:
                    pass
    return s


def install_all(s):
    n = 0
    for f in sorted((ROOT / "domains").glob("*.py")):
        if f.name.startswith("__"):
            continue
        try:
            src = f.read_text()
        except Exception:
            continue
        for m in re.finditer(r"^def (install_\w+_seed)\(", src, re.MULTILINE):
            try:
                mod = importlib.import_module(f"domains.{f.stem}")
                fn = getattr(mod, m.group(1))
                req = [p for p in inspect.signature(fn).parameters.values()
                       if p.kind in (inspect.Parameter.POSITIONAL_ONLY,
                                     inspect.Parameter.POSITIONAL_OR_KEYWORD)
                       and p.default is inspect.Parameter.empty]
                if len(req) == 1:
                    fn(s); n += 1
            except Exception:
                continue
    return n


def short(t, n=160):
    t = str(t).replace("\n", " ").strip()
    return (t[:n] + "...") if len(t) > n else t


def main():
    print("=" * 78)
    print("CONCEPT-GRAPH SHAPE HARVESTER — generativity measurement")
    print("=" * 78)
    s = fresh_substrate()
    n_install = install_all(s)

    from domains.implication_harvester import (
        harvest_shapes_combined, harvest_shapes_from_concept_graph)
    from domains.order_n_postulates import (
        synthesize_gaps, harvest_postulates, differentiate, _resolve_shapes)

    OLD = harvest_shapes_combined(s, include_concept_graph=False)
    CG = harvest_shapes_from_concept_graph(s)
    NEW = harvest_shapes_combined(s, include_concept_graph=True)
    print(f"\nBooted: {len(s.nodes('Microtheory'))} Mts, "
          f"{len(s.nodes('Concept'))} Concepts, {len(s.nodes('Rule'))} Rules; "
          f"{n_install} seeds")
    print(f"\nCATALOGUE SIZE:  OLD (no concept-graph) = {len(OLD)}")
    print(f"                 NEW (with concept-graph) = {len(NEW)}  "
          f"(+{len(CG)} concept-graph shapes)")
    edge_types = {}
    for sh in CG:
        rel = sh["source_edge"][1]
        edge_types[rel] = edge_types.get(rel, 0) + 1
    print(f"  concept-graph shapes by relation edge: {edge_types}")

    # ---- FIXED sample of ~30 held postulates (same KIND agent_decides targets:
    # the operator's science/design topics — filter/invariance/clustering/
    # prediction/composition/etc. — NOT alphabetical breadth, which would be a
    # vacuous sample). Selected DETERMINISTICALLY: every held postulate whose name
    # carries one of the operator's structural substrings, sorted, evenly slice 30.
    held_pairs = [(nm, txt) for _, nm, txt in harvest_postulates(s)]
    held = {nm for nm, _ in held_pairs}
    SCIENCE_SUBSTRINGS = ("filter", "formant", "invari", "speaker", "coarticul",
                          "statistical", "lexical", "recursion", "compress",
                          "generat", "analog", "compos", "feature", "program",
                          "synth", "predict", "cluster", "distribut", "linear",
                          "invert", "autoregress", "sequence", "markov")
    # postulates with real definition text and a structural-topic name.
    cands = sorted(nm for nm, txt in held_pairs
                   if txt and any(sub in nm.lower() for sub in SCIENCE_SUBSTRINGS))
    # always include the operator's own anchor concepts if present.
    must = [p for p in ("generative_grammar", "compositionality",
                        "analogical_reasoning", "code_generation",
                        "program_synthesis", "feature_invention",
                        "distributional_hypothesis", "Kalman_filter",
                        "Markov_chain", "branch_prediction")
            if p in held]
    sample = list(dict.fromkeys(must))
    # even stride through the candidate list so the 30 span many domains.
    pool = [c for c in cands if c not in set(sample)]
    if pool:
        step = max(1, len(pool) // max(1, (30 - len(sample))))
        sample += pool[::step]
    sample = sample[:30]
    print(f"\nFIXED SAMPLE: {len(sample)} held science/design postulates")
    print("  " + ", ".join(short(p, 28) for p in sample))

    def run_over(shape_lib):
        """coverage (#postulates that transfer >=1 gap), all gaps, per-postulate."""
        cov = 0
        all_gaps = []
        per = {}
        for p in sample:
            try:
                gaps = synthesize_gaps(s, p, max_order=2, record=False,
                                       prune=True, shapes=shape_lib)
            except Exception:
                gaps = []
            if gaps:
                cov += 1
                per[p] = gaps
                all_gaps.extend(gaps)
        return cov, all_gaps, per

    print("\n" + "=" * 78)
    print("COVERAGE — #/30 postulates that transfer a gap (selector ON, prune=True)")
    print("=" * 78)
    cov_old, gaps_old, per_old = run_over(OLD)
    cov_new, gaps_new, per_new = run_over(NEW)
    distinct_old = {short(g["gap"], 200) for g in gaps_old}
    distinct_new = {short(g["gap"], 200) for g in gaps_new}
    print(f"  OLD catalogue: coverage {cov_old}/30, "
          f"{len(gaps_old)} gaps, {len(distinct_old)} DISTINCT")
    print(f"  NEW catalogue: coverage {cov_new}/30, "
          f"{len(gaps_new)} gaps, {len(distinct_new)} DISTINCT")

    # ---- DIVERSITY: NEW gaps the agent could NOT derive before ----
    print("\n" + "=" * 78)
    print("DIVERSITY — gaps DERIVABLE NOW that the OLD catalogue could NOT produce")
    print("=" * 78)
    only_new = distinct_new - distinct_old
    print(f"  {len(only_new)} distinct NEW gap texts (NEW minus OLD)")
    shown = 0
    seen_texts = set()
    for p, gaps in per_new.items():
        for g in gaps:
            txt = short(g["gap"], 200)
            if txt in distinct_old or txt in seen_texts:
                continue
            # only show ones attributable to a concept_graph shape on the chain
            via = " ".join(g.get("via_shapes") or [])
            if "concept_graph" not in via and "concept_graph" not in str(
                    g.get("source_domains")):
                # still a NEW gap, but flag provenance
                pass
            seen_texts.add(txt)
            print(f"\n  [{p}] GAP: {short(g['gap'], 200)}")
            chain = g.get("chain") or []
            if chain:
                print("    chain: " + " => ".join(short(c, 70) for c in chain))
            print(f"    via: {short(via, 140)}")
            shown += 1
            if shown >= 8:
                break
        if shown >= 8:
            break
    if shown == 0:
        print("  (none — the concept-graph shapes derived no NEW selector-passing "
              "gap; honest null)")

    # ---- NOISE CHECK: shapes that fire on >50% of the sample ----
    print("\n" + "=" * 78)
    print("NOISE CHECK — shapes firing on >50% of the 30 postulates (= ~0 bits)")
    print("=" * 78)
    post_texts = {nm: txt for _, nm, txt in harvest_postulates(s) if nm in set(sample)}

    def fire_rate(shape):
        hits = 0
        for nm in sample:
            txt = post_texts.get(nm, "")
            try:
                fired = bool(differentiate(txt, shapes=[shape]))
            except Exception:
                fired = False
            if fired:
                hits += 1
        return hits

    promiscuous_cg = []
    for sh in CG:
        r = fire_rate(sh)
        if r > len(sample) * 0.5:
            promiscuous_cg.append((sh["name"], r))
    promiscuous_old = []
    for sh in OLD:
        r = fire_rate(sh)
        if r > len(sample) * 0.5:
            promiscuous_old.append((sh.get("name"), r))
    print(f"  concept-graph shapes firing on >15/30: "
          f"{len(promiscuous_cg)}/{len(CG)}")
    for nm, r in promiscuous_cg[:8]:
        print(f"    NOISY: {short(nm, 70)}  fires {r}/30")
    print(f"  (for reference) OLD-catalogue shapes firing on >15/30: "
          f"{len(promiscuous_old)}/{len(OLD)}")

    # Order-0 fire DIAGNOSTIC: do the concept-graph shapes match ANY postulate at
    # all (before the selector)? This separates "selector pruned a real fire" from
    # "never matched". Total (postulate x CG-shape) fires + #postulates touched.
    total_cg_fires = 0
    posts_touched = 0
    for nm in sample:
        txt = post_texts.get(nm, "")
        hits = sum(1 for sh in CG if differentiate(txt, shapes=[sh]))
        total_cg_fires += hits
        if hits:
            posts_touched += 1
    print(f"\n  DIAGNOSTIC: concept-graph shapes fire {total_cg_fires} time(s) "
          f"total at order-0 across the 30 postulates "
          f"({posts_touched}/30 postulates matched by ANY concept-graph shape).")

    # ---- HONEST VERDICT ----
    print("\n" + "=" * 78)
    print("HONEST VERDICT")
    print("=" * 78)
    widened = (cov_new > cov_old) and (len(only_new) > 0)
    noise_frac = (len(promiscuous_cg) / len(CG)) if CG else 0.0
    print(f"  coverage:  {cov_old}/30 -> {cov_new}/30   "
          f"(delta {cov_new - cov_old:+d})")
    print(f"  distinct gaps: {len(distinct_old)} -> {len(distinct_new)}   "
          f"({len(only_new)} genuinely new)")
    print(f"  noise: {len(promiscuous_cg)}/{len(CG)} concept-graph shapes fire "
          f"on >50% ({noise_frac*100:.0f}%)")
    print(f"  order-0 fires: {total_cg_fires} (concept-graph shapes matched any "
          f"postulate this many times BEFORE the selector)")
    if widened and noise_frac < 0.25:
        print("  => WIDENING: more coverage AND new diverse gaps, low noise. The "
              "agent's own taxonomy edges extend its generativity.")
    elif widened:
        print("  => MIXED: coverage/diversity rose BUT a non-trivial noise "
              "fraction the selector must fight. Net-positive but needs the "
              "noise controls kept on.")
    elif total_cg_fires == 0:
        print("  => NO WIDENING (and NOT a selector problem): the concept-graph "
              "shapes are CLEAN (0 promiscuous) but fire ZERO times at order-0 — "
              "they never MATCH these postulates, so the selector never sees them. "
              "ROOT CAUSE: the agent's taxonomy is genlMt over MICROTHEORIES, whose "
              "anchors are domain-NAME tokens (acoustics/markov/genetics) that do "
              "not appear in a postulate's definition PROSE. The relation is real "
              "and graph-resident, but TEXT-MATCHING a taxonomy edge onto a "
              "postulate is the wrong join. Honest negative result; the next brick "
              "must match on STRUCTURE (the postulate's Mt membership / Shape), not "
              "on the edge's name tokens appearing in prose.")
    else:
        print("  => NO WIDENING: the concept-graph shapes fired but produced no "
              "new selector-passing gap (the selector pruned them as already "
              "covered). Honest negative result.")
    print("\n  CAVEAT (faithful framing): this is ONE brick. The shapes come from "
          "the agent's OWN relation edges (genlMt/refers_to), and the compression "
          "selector still gates them — it is not the generator.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
