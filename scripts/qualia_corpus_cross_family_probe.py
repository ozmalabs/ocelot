#!/usr/bin/env python3
"""Corpus-scale CROSS-FAMILY probe — does a REAL corpus concept carry BOTH a
relational (lexical:telic/agentive) AND a dynamical (valence/commitment)
coordinate at once, ON THE REAL CORPUS (not the constructed debt/toxin demo)?

Run: python3 scripts/qualia_corpus_cross_family_probe.py [--domain computer_architecture]

This is the honest corpus-scale analogue of scripts/qualia_cross_family_demo.py
(which built a tiny hand-made econ/bio network to PROVE debt~toxin can span
lexical:telic + dynamical:valence). Here we take a WHOLE domain seed and ask
whether the two families overlap NATURALLY:

  1. materialise the domain (qualia_vibe_probe._materialise_domain — reads the
     SAME JSON the real loader reads);
  2. derive REAL relational structure from each concept's OWN prose
     (relation_grounding.ground_relations → typed telic/agentive/constitutive
     edges) and its author `category` (grounded_representation.ground_categories
     → genls). NOTHING invented: ground_relations drops any object that does not
     resolve to a held concept.
  3. light the DYNAMICAL axes by running the native CAN relaxation from real
     text-evidence + category basins (exactly the sweep's mechanism, reused
     verbatim from qualia_felt_sweep);
  4. read concept_signature per concept and count how many carry BOTH a
     lexical:telic/agentive coordinate (which can ONLY come from ground_relations
     — the synthetic same-category couplings the sweep adds are `causal_influence`
     → lexical:agentive, so we report lexical:TELIC separately as the
     unambiguous real-relational witness) AND a dynamical coordinate.

The felt coordinate is PRODUCED by relaxation, never hand-written. The relational
coordinate is DERIVED from prose, never invented. If the overlap is empty we say
so and explain why (the concepts with telic edges have no valence evidence, or
vice versa).

CONSTRAINTS honoured: native CAN 3-state path only; reuses _materialise_domain,
ground_relations, ground_categories, concept_signature, find_analogies, and the
sweep's own _prepare_can_mt / _relax_and_crystallise. Does NOT touch CAN backend
internals or toolbox solvers.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent
                       / "runners" / "dsl" / "python"))

from substrate_rs import _native

import domains.analogical_thinking as at
import domains.analogy_search as asr
from domains.can_self_worth_bridge import ensure_can_seed
from domains.relation_grounding import ground_relations
from domains.grounded_representation import ground_categories

import qualia_vibe_probe as vibe
import qualia_felt_sweep as sweep

ROOT = Path(__file__).resolve().parent.parent
SEEDS = ROOT / "seeds"

# lexical dimensions that the synthetic same-category coupling (causal_influence
# → lexical:agentive) can produce vs the ones only real prose-derived edges can.
_REAL_RELATIONAL = ("lexical:telic", "lexical:constitutive")
_ANY_RELATIONAL = ("lexical:telic", "lexical:constitutive", "lexical:agentive")


def _boot():
    for cache in (at._CONCEPT_READING_CACHE, at._VOCAB_KEYS_CACHE,
                  at._METASHAPE_COUNT_CACHE, asr._QUALIA_SCHEMA_CACHE):
        cache.clear()
    s = _native.Substrate()
    ag = s.add_node("Agent", {})
    for name in ("shape_vocabulary", "qualia_space", "analogy_search"):
        path = SEEDS / f"{name}.json"
        if path.exists():
            s.load_seed_manifest(json.load(open(path)), ag)
    ensure_can_seed(s)
    sweep._open_productions(s)
    return s, ag


def _families(sig):
    """Which qualia families a concept's signature carries, split into the
    unambiguous real-relational (telic/constitutive), any-relational
    (incl. agentive), and dynamical buckets."""
    dims = {d for d, _, _ in sig}
    real_rel = sorted(d for d in dims if d in _REAL_RELATIONAL)
    any_rel = sorted(d for d in dims if d in _ANY_RELATIONAL)
    dyn = sorted(d for d in dims if d.startswith("dynamical:"))
    return real_rel, any_rel, dyn


def main():
    ap = argparse.ArgumentParser(description="corpus-scale cross-family probe")
    ap.add_argument("--domain", default="computer_architecture")
    ap.add_argument("--ticks", type=int, default=16)
    ap.add_argument("--evidence-scale", type=float, default=1.0)
    ap.add_argument("--coupling", type=float, default=0.2)
    args = ap.parse_args()

    print("booting substrate + qualia seeds + native CAN seeds…")
    s, _ag = _boot()

    mt = vibe._materialise_domain(s, args.domain)
    if mt is None:
        print(f"  '{args.domain}' is not a materialisable domain seed.")
        return
    mt_name = s.node(mt)["attrs"].get("name", args.domain)
    concepts = list(s.neighbours(mt, "has_concept"))
    print(f"materialised '{mt_name}' — {len(concepts)} concepts")

    # (2) REAL relational structure from prose + category.
    gr = ground_relations(s, mt_name)
    ground_categories(s, mt_name)
    print(f"ground_relations: {gr['edges_added']} edges added "
          f"(telic={gr['telic']}, agentive={gr['agentive']}, "
          f"constitutive={gr['constitutive']}, formal={gr['formal']}); "
          f"drop_rate={gr['drop_rate']:.2f}")

    # how many concepts carry a REAL relational coordinate BEFORE we add any
    # synthetic couplings (pure ground_relations + ground_categories signal).
    rel_before = 0
    telic_before = []
    for c in concepts:
        sig = asr.concept_signature(s, c)
        real_rel, any_rel, _ = _families(sig)
        if real_rel:
            rel_before += 1
        if "lexical:telic" in real_rel:
            telic_before.append(s.node(c)["attrs"].get("name"))
    print(f"  concepts carrying a REAL relational coord (telic/constitutive) "
          f"from prose alone: {rel_before}/{len(concepts)}")
    print(f"  of which telic: {len(telic_before)} "
          f"→ {sorted(telic_before)[:12]}{' …' if len(telic_before) > 12 else ''}")

    # (3) light the dynamical axes — the sweep's exact mechanism.
    concepts, by_category, evidence, n_edges = sweep._prepare_can_mt(
        s, mt, evidence_scale=args.evidence_scale, coupling=args.coupling)
    print(f"\nwired native-CAN field: {len(by_category)} basins, {n_edges} "
          f"synthetic coupling edges (causal_influence → lexical:agentive)")
    sweep._relax_and_crystallise(s, mt, concepts, ticks=args.ticks)

    # (4) the cross-family overlap, ON THE REAL CORPUS.
    both_real = []      # real relational (telic/constitutive) AND dynamical
    both_any = []       # any relational (incl. synthetic agentive) AND dynamical
    dyn_lit = 0
    for c in concepts:
        sig = asr.concept_signature(s, c)
        real_rel, any_rel, dyn = _families(sig)
        if dyn:
            dyn_lit += 1
        if real_rel and dyn:
            both_real.append((s.node(c)["attrs"].get("name"), real_rel, dyn))
        if any_rel and dyn:
            both_any.append((s.node(c)["attrs"].get("name"), any_rel, dyn))

    print("\n─── CORPUS-SCALE CROSS-FAMILY RESULT ───")
    print(f"  dynamical-lit concepts: {dyn_lit}/{len(concepts)}")
    print(f"  concepts carrying BOTH a REAL relational (telic/constitutive) AND "
          f"a dynamical coord: {len(both_real)}")
    for name, rel, dyn in sorted(both_real):
        print(f"    ✓ {name:28s} relational={rel}  dynamical={dyn}")
    if not both_real:
        print("    (none — see explanation below)")

    print(f"\n  concepts carrying BOTH ANY relational (incl. synthetic "
          f"agentive coupling) AND a dynamical coord: {len(both_any)}")
    print("    (agentive here is dominated by the sweep's own same-category "
          "couplings, so this is a WEAKER witness than the telic/constitutive "
          "count above — reported for completeness, not as the corpus result.)")

    # honest explanation when the real overlap is empty.
    if not both_real:
        # why? intersect the telic-bearing set with the dynamical-lit set.
        telic_set = set(telic_before)
        lit_names = {s.node(c)["attrs"].get("name") for c in concepts
                     if _families(asr.concept_signature(s, c))[2]}
        print("\n─── why the real cross-family overlap is empty ───")
        print(f"  telic-bearing concepts:   {sorted(telic_set)[:12]}")
        print(f"  dynamical-lit concepts:   {len(lit_names)} total")
        print(f"  intersection:             {sorted(telic_set & lit_names)}")
        print("  → the concepts whose prose yields a telic/constitutive edge are "
              "a DIFFERENT population from those whose prose carries enough "
              "affective (valence) evidence to commit a state, so no single real "
              "concept lights both families at once on this corpus.")
    else:
        print("\n  → a REAL corpus concept carries both families at once: the "
              "corpus-scale analogue of the hand-built debt~toxin cross-family "
              "result, with NOTHING invented (relational from prose, dynamical "
              "from relaxation).")

    print("\ndone.")


if __name__ == "__main__":
    main()
