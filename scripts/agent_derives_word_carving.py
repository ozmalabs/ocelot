"""agent_derives_word_carving — drive the #1 frontier via the agent's OWN derivation.
After removing the observed speaker, cross-speaker WORD clustering tops out ~0.47 purity;
the bound is now REPRESENTATIONAL (word overlap), not the speaker. Put that residual to
the agent's live synthesize_gaps and report VERBATIM what carves the words. NO-DONKEY
(same shape as agent_derives_xspeaker / _nuisance_conditioned). Honest postulate, no fix
named (no "DTW", "alignment", "warp", "HMM", "segment", "valley", "mixture").

Run:  python -m scripts.agent_derives_word_carving
"""
from __future__ import annotations
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

NAME = "word_clusters_overlap_after_speaker_removed"
DEFN = (
    "After removing the variation explained by the observed speaker, the tokens of the "
    "same word still do not all fall in one group — clustering purity tops out near half. "
    "The remaining confusion is WITHIN-word variation: the same word is produced "
    "differently from token to token — spoken at different RATES, its sounds blending "
    "into their neighbours, its parts falling at different points in time — and this "
    "within-word variation spreads a word's tokens until they overlap the tokens of OTHER "
    "words. Each token is a TRAJECTORY over time whose successive pieces correspond to the "
    "word's parts; two tokens of the same word are the same ORDERED sequence of parts but "
    "stretched and compressed differently in time and run together at the joins. Comparing "
    "the trajectories as fixed-length vectors, by cutting them into equal time bins and "
    "stacking the bins, lines up bin 3 of one with bin 3 of the other even when those bins "
    "hold different parts — so two tokens of the same word are measured as far apart while "
    "tokens of different words are measured as close.")


def _build():
    s = Substrate()
    install_phonology(s); install_speech_science(s); install_mathematics_seed(s)
    install_engineering_seed(s); install_machine_learning_seed(s)
    install_all_concept_expansions(s)
    return s


def main():
    print("=" * 80, flush=True)
    print("AGENT DERIVES WORD-CARVING (post speaker-removal) — live, verbatim", flush=True)
    print("=" * 80, flush=True)
    s = _build()
    mt = s.add_node("Microtheory", {"name": "word_carving_paradigm", "origin": "drive"})
    try:
        s.add_production({"src": {"type": "Microtheory", "var": "a"},
                          "edge_type": "has_concept",
                          "tgt": {"type": "Concept", "var": "b"},
                          "provenance": "carve:has_concept"})
    except Exception:
        pass
    _install_concept(s, mt, NAME, DEFN)
    print(f"\n[breadth] held Concepts: {len(s.nodes('Concept'))}", flush=True)
    lib = harvest_shapes_combined(s)
    print(f"[harvest] shape library: {len(lib)}", flush=True)
    print("\n[postulate]\n  ", DEFN, flush=True)

    print("\n" + "=" * 80 + "\n[order-1] shapes that FIRE:", flush=True)
    for im in differentiate(DEFN, shapes=lib):
        print(f"\n   via_shape  : {im['via_shape']}  (concept '{im.get('source_concept')}')",
              flush=True)
        print(f"   name_keys  : {im['name_keys']}", flush=True)
        print(f"   consequence: {im['consequence']}", flush=True)

    print("\n" + "=" * 80 + "\n[synthesize_gaps] recursive (max_order=3):", flush=True)
    gaps = synthesize_gaps(s, NAME, shapes=lib, record=False, prune=False, max_order=3)
    print(f"  total gaps: {len(gaps)}\n", flush=True)
    for g in gaps:
        roles = breadth_audit.classify_shape_role(breadth_audit._gap_to_shapelike(g))
        print(f"  [{','.join(roles) or 'unclassified':16}] order-{g['order']} "
              f"keys={g['capability_keys']}", flush=True)
        print(f"     via={g['via_shapes']}  gap={g['gap']}", flush=True)


if __name__ == "__main__":
    main()
