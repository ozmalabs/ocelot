"""agent_derives_xspeaker — put the CROSS-SPEAKER-INVARIANCE problem to the agent's
OWN live derivation machinery and report VERBATIM what it derives. NO-DONKEY.

The frontier synthesizer already NAMED the capability (cross-speaker clustering /
invariance-from-structure: docs/ask_the_agent_frontier_v3.md). The OPEN question this
script puts to the machinery is the NEXT one — the one a human was about to hand-build
(WCCN/LDA): given that the agent's existing per-speaker MEAN subtraction (xspeaker_norm /
iter41 centroids) does NOT make a word's cross-speaker tokens cluster tighter than
different words, what TRANSFORM does the agent's own reasoning DERIVE to remove the
residual SPEAKER term?

This script does NOT assert the answer. Exactly as iter24_scale_invariant_derive did, it:
  1. registers the residual state as a held postulate (honest text — the residual after
     mean removal, no answer named: a BETWEEN-SPEAKER scatter DIRECTION still dominates the
     within-word distance; nothing says "projection" / "discriminant" / "scatter matrix");
  2. runs the agent's LIVE synthesize_gaps over the agent's FULL harvested shape library
     (its own concepts donate the shapes — linear algebra, ML normalization, statistics);
  3. reports VERBATIM every shape that fires + the derived consequence + the chain.

Whatever the live machinery surfaces IS the agent's derivation. If it derives a concrete
remove-the-speaker-term transform, that is reported. If the closest it derives is the moves
it already holds (per-source mean subtraction / ratio normalization / model-and-subtract)
and NOT a discriminative subspace projection, THAT is reported honestly as the frozen edge.

Run:  python -m scripts.agent_derives_xspeaker
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

from domains.phonology import install_phonology
from domains.speech_science import install_speech_science
from domains.mathematics import install_mathematics_seed
from domains.engineering import install_engineering_seed
from domains.machine_learning import install_machine_learning_seed
from domains.concept_expansions import install_all_concept_expansions
from domains.code_authoring import _install_concept
from domains.implication_harvester import harvest_shapes_combined
from domains.order_n_postulates import synthesize_gaps, differentiate
from domains import breadth_audit


# ---------------------------------------------------------------------------
# The residual postulate — the cross-speaker state AFTER the agent's existing
# per-speaker MEAN removal. HONEST: it states what is LEFT (a between-speaker scatter
# DIRECTION dominates the within-word distance) and names NO fix. No "projection",
# no "discriminant", no "scatter matrix", no "whitening" — the synthesizer must supply
# the transform, not read it off the prose.
# ---------------------------------------------------------------------------
POSTULATE_NAME = "cross_speaker_residual_after_mean_removal"
POSTULATE_DEFINITION = (
    "Each spoken word is measured as a vector of acoustic cues across speakers. The "
    "agent already subtracts a per-speaker BASELINE (the speaker's mean / centroid) "
    "from every token, which cancels an additive per-speaker OFFSET. But after that "
    "mean removal the same word's tokens from different speakers still do NOT cluster "
    "tighter than tokens of different words: a held-out speaker's token matches the "
    "nearest TOKEN (often a same-speaker wrong word) rather than the right word's "
    "cross-speaker group. The residual nuisance is no longer a single offset — it is a "
    "structured BETWEEN-SPEAKER VARIATION that spreads each word's tokens along certain "
    "directions of the cue space (vocal-tract length, glottal source shape, channel), "
    "and this WITHIN-WORD BETWEEN-SPEAKER spread is large compared with the "
    "BETWEEN-WORD spread. The speaker identity is a structured component of the "
    "measured vector that co-varies across the cue dimensions and is NOT removed by "
    "subtracting a per-speaker scalar baseline; it is the dominant remaining term in "
    "the raw distance between two tokens of the same word.")


def _build_mind():
    """Load the agent's breadth so the harvester can draw shapes from its OWN concepts
    (linear algebra, ML normalization, statistics, physics) — not a human stencil."""
    sub = Substrate()
    install_phonology(sub)
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def _register_residual(sub):
    mt = sub.add_node("Microtheory", {
        "name": "cross_speaker_residual_paradigm",
        "origin": "agent_derives_xspeaker"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "xspeaker:has_concept"})
    except Exception:
        pass
    return _install_concept(sub, mt, POSTULATE_NAME, POSTULATE_DEFINITION)


def main():
    print("=" * 80, flush=True)
    print("AGENT DERIVES CROSS-SPEAKER INVARIANCE — live synthesize_gaps, verbatim",
          flush=True)
    print("=" * 80, flush=True)

    sub = _build_mind()
    cid = _register_residual(sub)
    n_concepts = len(sub.nodes("Concept"))
    print(f"\n[breadth] held Concepts: {n_concepts}", flush=True)

    # The agent's OWN harvested shape library (concepts + rules donate shapes).
    lib = harvest_shapes_combined(sub)
    print(f"[harvest] harvested shape library size: {len(lib)}", flush=True)

    print("\n[postulate] the residual state (honest; names NO fix):", flush=True)
    print("  ", POSTULATE_DEFINITION, flush=True)

    # ---- order-1 derivative: which shapes TRANSFER onto the residual? ----------
    print("\n" + "=" * 80, flush=True)
    print("[order-1] which of the agent's shapes FIRE on the residual postulate?",
          flush=True)
    print("=" * 80, flush=True)
    impls = differentiate(POSTULATE_DEFINITION, shapes=lib)
    print(f"  shapes that fired (order-0 -> order-1): {len(impls)}", flush=True)
    for im in impls:
        print(f"\n   via_shape   : {im['via_shape']}  (domain={im['source_domain']}"
              f"  from concept '{im.get('source_concept')}')", flush=True)
        print(f"   name_keys   : {im['name_keys']}", flush=True)
        print(f"   consequence : {im['consequence']}", flush=True)

    # ---- full recursive synthesis (order 0..3), DERIVATION mode (prune=False) ---
    print("\n" + "=" * 80, flush=True)
    print("[synthesize_gaps] full recursive derivation (max_order=3, prune=False)",
          flush=True)
    print("=" * 80, flush=True)
    gaps = synthesize_gaps(sub, POSTULATE_NAME, shapes=lib, record=False,
                           prune=False, max_order=3)
    print(f"  total derived gaps: {len(gaps)}\n", flush=True)
    for g in gaps:
        roles = breadth_audit.classify_shape_role(
            breadth_audit._gap_to_shapelike(g))
        tag = ",".join(roles) or "unclassified"
        print(f"  [{tag:14}] order-{g['order']}  keys={g['capability_keys']}",
              flush=True)
        print(f"     via_shapes   = {g['via_shapes']}", flush=True)
        print(f"     domains      = {g['source_domains']}", flush=True)
        print(f"     concepts     = {g.get('source_concepts')}", flush=True)
        print(f"     gap          = {g['gap']}", flush=True)
        print("     chain:", flush=True)
        for step in g["chain"]:
            print(f"       - {step}", flush=True)
        print(flush=True)

    # ---- VERDICT: did it derive a DISCRIMINATIVE SUBSPACE PROJECTION? ----------
    # The capability the human was about to hand-build is a transform that removes a
    # whole DIRECTION (the within-word between-speaker scatter subspace) — WCCN/LDA:
    # whiten by the within-class scatter, or project to maximise between/within. Test
    # whether the derived keys name THAT (projection / scatter / discriminant /
    # whiten / subspace / eigen), distinct from the moves the agent already holds
    # (per-source mean subtraction, ratio normalization, model-and-subtract).
    PROJECTION_TERMS = ("project", "scatter", "discrimin", "whiten", "subspace",
                        "eigen", "lda", "wccn", "metric", "mahalanob", "covariance")
    HELD_TERMS = ("ratio", "normaliz", "normalis", "subtract", "mean", "baseline",
                  "cluster", "centroid", "predict", "residual")
    derived_keys = [k.lower() for g in gaps for k in g["capability_keys"]]
    derived_cons = " ".join(g["gap"].lower() for g in gaps)
    hay = " ".join(derived_keys) + " " + derived_cons
    hit_proj = sorted({t for t in PROJECTION_TERMS if t in hay})
    hit_held = sorted({t for t in HELD_TERMS if t in hay})
    print("=" * 80, flush=True)
    print("[VERDICT] does the live machinery derive a DISCRIMINATIVE SUBSPACE "
          "PROJECTION (the un-held move) vs only moves the agent already holds?",
          flush=True)
    print("=" * 80, flush=True)
    print(f"  projection/scatter/discriminant terms in derived output: {hit_proj}",
          flush=True)
    print(f"  already-held moves (mean/ratio/cluster/model-subtract):  {hit_held}",
          flush=True)
    if hit_proj:
        print("  => DERIVED a subspace-projection move (report the transform + LOSO).",
              flush=True)
    else:
        print("  => NOT derived. The machinery surfaces only the moves the agent "
              "ALREADY holds (per-source mean/ratio normalization, model-and-subtract, "
              "cluster the distribution). The discriminative WITHIN/BETWEEN scatter "
              "PROJECTION that removes the speaker DIRECTION is NOT in the agent's "
              "harvestable shape library — there is no extractor / donor concept whose "
              "structural property is 'a nuisance SUBSPACE is removed by projecting "
              "onto the complement of the within-class scatter'. This is the honest "
              "frozen edge.", flush=True)


if __name__ == "__main__":
    main()
