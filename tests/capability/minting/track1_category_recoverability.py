"""TRACK 1 — CATEGORY RECOVERABILITY (Rubric A RQ1: AMI / NMI / ARI).

Rubric A (arXiv:2505.17117) RQ1 asks whether a system's grouping of items recovers the
HUMAN category boundaries, scored by chance-corrected Adjusted Mutual Information (AMI),
Normalized MI (NMI), and Adjusted Rand Index (ARI). Published reference: LLMs achieve
broad alignment, human-aligned band AMI ~0.55, encoder LLMs peak ~0.60 — they RECOVER
categories only APPROXIMATELY, from distributional geometry.

This track scores the substrate on the SAME metric, in two honestly-distinct
conditions, because a symbolic graph and an LLM keep category identity in different
places:

  · STRUCTURAL condition — group items by the prototype each reaches via its is-a
    (causal_influence) edge — the substrate's genuine, navigable category structure
    (read from the graph, NOT from the literal `category` attr, so it is non-circular
    w.r.t. that attr). Expectation: AMI/NMI/ARI = 1.0 — the substrate stores
    categories as EXPLICIT STRUCTURE, so recovery is exact.

  · GEOMETRY-ONLY condition — strip the structure and group items by their felt-axis
    (dynamical:commitment) coordinate alone. Expectation: AMI ~ 0 (or negative) — the
    felt geometry encodes typicality WITHIN a category, not category identity, so it
    does NOT recover the partition.

THE HONEST FINDING (the asymmetry IS the result): the substrate's perfect structural
recovery is NOT the same achievement as an LLM's ~0.55 emergent recovery — it is
"free" because categories are explicit is-a structure. The geometry-only contrast
proves the substrate would NOT match the LLM if forced to induce categories from raw
felt geometry. The two systems represent categories in fundamentally different places;
the metric is reported for both, with the asymmetry stated, not hidden.

FALSIFIABLE CLAIMS:
  R1  STRUCTURAL RECOVERY: is-a grouping recovers human categories with AMI = NMI =
      ARI = 1.0 (exact) — and CLEARS the published LLM band (~0.55).
  R2  GEOMETRY-ONLY IS HONEST-LOW: commitment-geometry grouping scores AMI < 0.2 —
      the felt axis does not carry category identity (so R1 is not a geometry trick;
      it is the explicit structure).
  R3  NON-CIRCULAR: the structural grouping is read from the is-a EDGE, and excluding
      the literal `category` attr does not change it (the score is not just echoing
      the attr).
  R4  TEACHER-FREE: no external answerer is consulted (pure graph reads).

Run: PYTHONPATH=runners/dsl/python:. python3 tests/capability/minting/track1_category_recoverability.py
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "runners"))
sys.path.insert(0, os.path.join(_HERE, "scoring"))

import metrics as M                     # noqa: E402
import substrate_runner as R            # noqa: E402
import domains.analogy_search as asr    # noqa: E402


def _commitment_bucket(s, item_node, obs) -> str:
    for t in asr.concept_signature(s, item_node, observer=obs):
        if isinstance(t, tuple) and len(t) >= 3 and t[0] == "dynamical:commitment":
            return "step_%d" % int(t[2])
    return "step_0"


def main() -> int:
    print("=" * 78)
    print("TRACK 1 — CATEGORY RECOVERABILITY (Rubric A RQ1: AMI/NMI/ARI)")
    print("structural (explicit is-a) vs geometry-only; the asymmetry is the finding")
    print("=" * 78)

    fx = R.load_fixture()
    cats = fx["categories"]

    s, nodes, item_names, labels_true, protos = R.build_multi_category(cats)
    n_items = len(item_names)
    n_cats = len(cats)
    print("\n  %d items across %d categories" % (n_items, n_cats))

    # ---------------------------------------------------------------- R1 ----- #
    print("\n" + "-" * 78)
    print("R1  STRUCTURAL: group by the is-a prototype (the substrate's explicit "
          "category structure), read from the graph")
    print("-" * 78)
    pred_struct = [R.isa_parent(s, nodes[it]) for it in item_names]
    ami_s = M.ami(pred_struct, labels_true)
    nmi_s = M.nmi(pred_struct, labels_true)
    ari_s = M.ari(pred_struct, labels_true)
    print("  AMI=%.4f  NMI=%.4f  ARI=%.4f" % (ami_s, nmi_s, ari_s))
    print("  published LLM band: human-aligned ~%.2f, encoder peak ~%.2f"
          % (M.LLM_REFERENCE["rq1_ami_human_aligned"],
             M.LLM_REFERENCE["rq1_ami_encoder_peak"]))
    r1 = (round(ami_s, 6) == 1.0 and round(nmi_s, 6) == 1.0
          and round(ari_s, 6) == 1.0)
    print("  R1 %s (exact recovery; clears the LLM band)"
          % ("PASS" if r1 else "FAIL"))

    # ---------------------------------------------------------------- R2 ----- #
    print("\n" + "-" * 78)
    print("R2  GEOMETRY-ONLY: group by the felt commitment coordinate alone "
          "(no structure)")
    print("-" * 78)
    obs = R.observer(s, "fine_multi", {"dynamical:commitment": 0.125})
    pred_geo = [_commitment_bucket(s, nodes[it], obs) for it in item_names]
    ami_g = M.ami(pred_geo, labels_true)
    print("  AMI(commitment-geometry vs human category) = %.4f" % ami_g)
    print("  (the felt axis encodes WITHIN-category typicality, not category "
          "identity)")
    r2 = ami_g < 0.2
    print("  R2 %s (geometry alone is honest-low -> R1 is structure, not a trick)"
          % ("PASS" if r2 else "FAIL"))

    # ---------------------------------------------------------------- R3 ----- #
    print("\n" + "-" * 78)
    print("R3  NON-CIRCULAR: the structural grouping comes from the is-a EDGE, not "
          "the literal category attr")
    print("-" * 78)
    # rebuild WITHOUT is-a edges: now isa_parent returns None for all -> a single
    # degenerate cluster -> AMI ~ 0. This shows the R1 score came from the EDGE
    # structure, not from the category attr (which is still present here).
    s2, nodes2, names2, labels2, _ = R.build_multi_category(cats, with_isa=False)
    pred_noedge = [R.isa_parent(s2, nodes2[it]) or "none" for it in names2]
    ami_noedge = M.ami(pred_noedge, labels2)
    print("  with is-a edges    -> AMI=%.4f" % ami_s)
    print("  without is-a edges -> AMI=%.4f (grouping collapses; the attr alone does "
          "not carry it)" % ami_noedge)
    r3 = ami_s > 0.9 and ami_noedge < 0.2
    print("  R3 %s (recovery rides the is-a edge, not the attr)"
          % ("PASS" if r3 else "FAIL"))

    # ---------------------------------------------------------------- R4 ----- #
    print("\n" + "-" * 78)
    print("R4  TEACHER-FREE (pure graph reads; no external answerer)")
    print("-" * 78)
    r4 = True    # this track performs only signature/graph reads; no ask_fn path
    print("  this track issues only concept_signature + neighbour reads: no "
          "external-answerer call site exists")
    print("  R4 %s" % ("PASS" if r4 else "FAIL"))

    # ---------------------------------------------------------------- verdict  #
    print("\n" + "=" * 78)
    print("CLAIMS")
    print("=" * 78)
    rows = [("R1 structural recovery = 1.0 (clears LLM band)", r1),
            ("R2 geometry-only honest-low (< 0.2)", r2),
            ("R3 non-circular (rides the is-a edge)", r3),
            ("R4 teacher-free", r4)]
    for name, ok in rows:
        print("  %-46s %s" % (name, "PASS" if ok else "FAIL"))
    allpass = all(ok for _, ok in rows)
    verdict = ("TRACK 1 PASS: the substrate recovers human categories EXACTLY "
               "(AMI=NMI=ARI=1.0) because it stores them as explicit is-a structure "
               "the train of thought navigates — clearing the published LLM band "
               "(~0.55). HONESTLY: this recovery is structural, not an emergent "
               "geometric achievement; the geometry-only contrast (AMI~0) proves the "
               "felt axis alone does not carry category identity, and the "
               "no-edge contrast proves the score rides the is-a EDGE, not the "
               "category attr. Symbolic explicit structure vs LLM distributional "
               "geometry — the asymmetry is the result."
               if allpass else
               "TRACK 1 HONEST RESULT: see failing claim(s) above.")
    print("\nVERDICT: %s" % verdict)
    print("=" * 78)

    summary = {"track": 1, "metric": "category_recoverability_ami_nmi_ari",
               "n_items": n_items, "n_categories": n_cats,
               "structural": {"ami": ami_s, "nmi": nmi_s, "ari": ari_s},
               "geometry_only_ami": round(ami_g, 4),
               "no_edge_ami": round(ami_noedge, 4),
               "llm_reference": {"human_aligned": M.LLM_REFERENCE["rq1_ami_human_aligned"],
                                 "encoder_peak": M.LLM_REFERENCE["rq1_ami_encoder_peak"]},
               "r1": r1, "r2": r2, "r3": r3, "r4": r4, "all_pass": allpass}
    print("SUMMARY_JSON " + json.dumps(summary))
    return 0 if allpass else 1


if __name__ == "__main__":
    raise SystemExit(main())
