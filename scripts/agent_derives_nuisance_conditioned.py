"""agent_derives_nuisance_conditioned — put the NUISANCE-CONDITIONED clustering problem
to the agent's OWN live derivation machinery and report VERBATIM what it derives.
NO-DONKEY (same shape as agent_derives_xspeaker).

The situation (why whitened-EM was a null, commit ce9a449d): cross-speaker WORD
clustering has NO word labels, so the within-class whitening the agent derived+wired
(supervised, +7.3%) cannot be estimated — pseudo-labels are speaker-contaminated. BUT
each token's SPEAKER is OBSERVABLE. The open question this puts to the machinery: given a
KNOWN, observable nuisance attribute that explains the dominant structured variation, and
an UNKNOWN target to group by, what transform does the agent's own reasoning DERIVE to
remove the variation attributable to the KNOWN attribute so the unknown target surfaces?

This does NOT assert the answer. It (1) registers the situation as a held postulate
(honest; names NO fix — no "regress", "condition", "project out", "covariate", "nuisance
subspace", "between-class"); (2) harvests the agent's OWN shape library (its concepts
donate the shapes, incl. the seeded LDA / within_class_scatter); (3) runs differentiate +
synthesize_gaps; (4) reports VERBATIM every shape that fires + the chain. Whatever fires
IS the agent's derivation — including a frozen edge, honestly.

Run:  python -m scripts.agent_derives_nuisance_conditioned
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


POSTULATE_NAME = "nuisance_conditioned_grouping"
POSTULATE_DEFINITION = (
    "Each token is a vector of cues that carries TWO attributes. The first is the TARGET "
    "we want to group the tokens by (which word): it is UNKNOWN — no token is labelled "
    "with its target. The second is a different attribute (which speaker produced it): it "
    "is OBSERVABLE — every token comes tagged with the value of this second attribute. "
    "The second, observed attribute explains a large STRUCTURED part of the variation: "
    "tokens that share the same observed value (same speaker) sit close together whatever "
    "their target, while tokens that share the target (same word) but differ in the "
    "observed value (different speakers) sit far apart. So grouping the tokens by raw "
    "proximity recovers the OBSERVED attribute, not the target. The target labels are "
    "absent, but the value of the observed attribute is known for every token. The "
    "structured variation the observed attribute contributes is the dominant term in the "
    "distance between two tokens that share the target.")


def _build_mind():
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
        "name": "nuisance_conditioned_paradigm",
        "origin": "agent_derives_nuisance_conditioned"})
    try:
        sub.add_production({
            "src": {"type": "Microtheory", "var": "a"},
            "edge_type": "has_concept",
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "nuisance:has_concept"})
    except Exception:
        pass
    return _install_concept(sub, mt, POSTULATE_NAME, POSTULATE_DEFINITION)


def main():
    print("=" * 80, flush=True)
    print("AGENT DERIVES NUISANCE-CONDITIONED GROUPING — live synthesize_gaps, verbatim",
          flush=True)
    print("=" * 80, flush=True)
    sub = _build_mind()
    _register_residual(sub)
    print(f"\n[breadth] held Concepts: {len(sub.nodes('Concept'))}", flush=True)
    lib = harvest_shapes_combined(sub)
    print(f"[harvest] harvested shape library size: {len(lib)}", flush=True)
    print("\n[postulate] the situation (honest; names NO fix):\n  ",
          POSTULATE_DEFINITION, flush=True)

    print("\n" + "=" * 80, flush=True)
    print("[order-1] which of the agent's shapes FIRE on the postulate?", flush=True)
    print("=" * 80, flush=True)
    impls = differentiate(POSTULATE_DEFINITION, shapes=lib)
    print(f"  shapes that fired: {len(impls)}", flush=True)
    for im in impls:
        print(f"\n   via_shape   : {im['via_shape']}  (domain={im['source_domain']}"
              f"  from concept '{im.get('source_concept')}')", flush=True)
        print(f"   name_keys   : {im['name_keys']}", flush=True)
        print(f"   consequence : {im['consequence']}", flush=True)

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
        print(f"  [{','.join(roles) or 'unclassified':16}] order-{g['order']}  "
              f"keys={g['capability_keys']}", flush=True)
        print(f"     via_shapes = {g['via_shapes']}  concepts={g.get('source_concepts')}",
              flush=True)
        print(f"     gap        = {g['gap']}", flush=True)

    # VERDICT — does it derive USING THE OBSERVED attribute to remove its contributed
    # variation (regress-out / condition / model-and-subtract / project the known
    # between-attribute direction), vs only target-label moves it cannot apply here?
    COND = ("regress", "residual", "context", "function of", "removable", "model",
            "subtract", "condition", "covariate", "project", "between", "scatter",
            "discrimin", "whiten", "subspace", "known")
    hay = " ".join(k.lower() for g in gaps for k in g["capability_keys"]) + " " + \
        " ".join(g["gap"].lower() for g in gaps)
    hits = sorted({t for t in COND if t in hay})
    print("\n" + "=" * 80, flush=True)
    print("[VERDICT] does it derive removing the KNOWN-attribute variation?", flush=True)
    print("=" * 80, flush=True)
    print(f"  conditioning / removal terms in derived output: {hits}", flush=True)
    print("  => " + ("DERIVED a nuisance-removal move — report the transform."
                     if hits else
                     "NOT derived — frozen edge; no shape uses a KNOWN attribute to "
                     "remove its contributed variation."), flush=True)


if __name__ == "__main__":
    main()
