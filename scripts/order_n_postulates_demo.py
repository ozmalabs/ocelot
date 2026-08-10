"""order-N postulates — the agent SYNTHESIZES its own gaps, from its OWN shapes.

The agent already has an order-N operator over SIGNALS (0=value, 1=tilt,
2=curvature; recursive finite difference). order_n_postulates LIFTS it to its
KNOWLEDGE: order-0 = a postulate it holds, order-1 = what that postulate IMPLIES
but it has not yet realized, order-2 = implications of implications. A GAP is an
order-k implication that is not already held/implemented and that coheres.

The derivative step (order k -> k+1) transfers an implication-SHAPE — a structural
pattern like "X is a linear system => X is invertible / parametrically
identifiable", "X is a distribution => X can be clustered". Until now that SET of
shapes was a finite, HAND-CURATED stencil — the one part bounded by a human's
breadth, not the agent's.

This demo closes that caveat: the shapes are now HARVESTED from the agent's OWN
Concepts across ALL its domains (linear-algebra, signals/DSP, statistics, ML,
control, ...) by domains/implication_harvester — the same move analogy.py's
abstract_patterns makes for features, applied to the implication relation a
concept's text encodes. The hand stencil is kept only for the comparison below.

Run:  python scripts/order_n_postulates_demo.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

from domains.stt_pipeline import STTPipeline, STTParams
from domains.phonology import install_phonology
from domains.speech_development import install_speech_development
from domains.speech_cortex import SpeechCortex
from domains.speech_science import install_speech_science
from domains.mathematics import install_mathematics_seed
from domains.engineering import install_engineering_seed
from domains.machine_learning import install_machine_learning_seed
from domains.concept_expansions import install_all_concept_expansions
from domains.implication_harvester import harvest_report
from domains.order_n_postulates import (synthesize_gaps, synthesize_over_all,
                                        harvest_postulates)

# The three KNOWN gaps the operator must reproduce (capability -> identifying key).
_KNOWN = {
    "LPC formant extraction": "all-pole",
    "cross-speaker clustering": "cross-speaker-clustering",
    "word-scale chunking": "word-scale chunking",
}


def _build():
    """The agent with its speech IMPLEMENTATION + the speech SCIENCE it holds +
    its cross-domain BREADTH (math / engineering / ML expansion packs). The
    breadth is what the harvester draws its implication-shapes FROM — without it
    the agent has no shapes to transfer (it would fall back to the stencil)."""
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    install_phonology(sub)
    install_speech_development(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    install_speech_science(sub)
    # the agent's cross-domain breadth — the SOURCE of the harvested shapes.
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def _caps(syn) -> set:
    return {frozenset(k.lower() for k in g["capability_keys"])
            for gg in syn.values() for g in gg}


def _show_chain(gap):
    for line in gap["chain"]:
        print(f"      {line}")
    print(f"      => GAP (order-{gap['order']}): keys={gap['capability_keys']}")


def main():
    sub = _build()

    print("=" * 78)
    print("THE HARVEST — the agent's OWN implication-shapes (no hand stencil)")
    print("=" * 78)
    rep = harvest_report(sub)
    print(f"  harvested {rep['n_shapes']} implication-shapes ({rep['n_kinds']} "
          f"kinds) from {rep['n_donor_concepts']} of the agent's own concepts")
    print(f"  across {rep['n_domains']} domains: {rep['domains']}\n")
    for s in rep["shapes"]:
        alts = ", ".join(f"{n}({d})" for n, d in s["alt_sources"][:2])
        print(f"    {s['kind']:<22} <- '{s['source_concept']}' ({s['domain']})"
              f"   [donors={s['n_donors']}; also {alts}]")

    print("\n" + "=" * 78)
    print("ACCEPTANCE 1 — SELF-SUFFICIENCY: known gaps from HARVESTED shapes ONLY")
    print("=" * 78)
    print("Stencil OFF. The shapes come entirely from the agent's own concepts.")
    print("Two DISTINCT questions, reported separately (conflating them is what")
    print("produced the old stale 'MISS LPC'):")
    print("  • DERIVED?  does a harvested shape TRANSFER onto the postulate and")
    print("    produce the capability? (the harvester's self-sufficiency.)")
    print("  • STILL OPEN?  given it derives, has the agent NOT yet implemented it?")
    print("    (the selector, vs the agent's live speech codebase.)\n")
    # DERIVATION pass (prune off): self-sufficiency of the harvest, regardless of
    # whether the agent has since acted on the capability.
    syn_d = synthesize_over_all(sub, record=False, shapes="harvested", prune=False)
    caps_d = _caps(syn_d)
    # OPENNESS pass (prune on): which derived capabilities are still un-realized.
    syn_h = synthesize_over_all(sub, record=False, shapes="harvested")
    caps_h = _caps(syn_h)
    # show the LPC derivation chain explicitly (from the DERIVATION pass).
    for g in synthesize_gaps(sub, "source_filter_theory", shapes="harvested",
                             record=False, prune=False):
        if "all-pole" in [k.lower() for k in g["capability_keys"]]:
            print("  LPC derivation (order-0 postulate -> harvested shape):")
            _show_chain(g)
            print(f"      shape harvested from concept: {g['source_concepts']}\n")

    def _src(syn, key):
        return sorted({sc for gg in syn.values() for g in gg
                       for sc in g.get("source_concepts", [])
                       if key in [k.lower() for k in g["capability_keys"]]})

    derived_ok = True
    for name, key in _KNOWN.items():
        got = any(key in c for c in caps_d)
        derived_ok = derived_ok and got
        still_open = any(key in c for c in caps_h)
        src = _src(syn_d, key)
        print(f"    {'OK ' if got else 'MISS'} {name:<26} key='{key}'"
              f"  DERIVED={got}  still-open={still_open}"
              f"  from concept(s)={src}")
    print(f"\n  ==> harvested-only DERIVES ALL known capabilities: {derived_ok}")
    print("      The hand-curated stencil is NO LONGER load-bearing for derivation."
          if derived_ok else
          "      HARVEST INSUFFICIENT — stencil still load-bearing (see honesty).")
    # which of the known capabilities the selector now (correctly) treats as CLOSED
    # because the agent has since implemented them (e.g. LPC via sound_graph.py).
    closed = [n for n, k in _KNOWN.items()
              if any(k in c for c in caps_d) and not any(k in c for c in caps_h)]
    if closed:
        print(f"      NB selector now treats as ALREADY-IMPLEMENTED (not open): "
              f"{closed}")
        print("      — derivation still works; these are no longer OPEN gaps.")

    print("\n" + "=" * 78)
    print("ACCEPTANCE 2 — BREADTH PAYOFF: harvested vs hand-curated stencil")
    print("=" * 78)
    syn_s = synthesize_over_all(sub, record=False, shapes="stencil")
    caps_s = _caps(syn_s)
    np_h = sum(1 for _ in syn_h)
    np_s = sum(1 for _ in syn_s)
    print(f"  postulates that YIELD a gap:   harvested={np_h}   stencil={np_s}")
    print(f"  distinct capability-axes flagged: harvested={len(caps_h)}   "
          f"stencil={len(caps_s)}")
    new_caps = caps_h - caps_s
    print(f"  NEW capability-axes from harvest (not in stencil): "
          f"{[sorted(c)[:2] for c in new_caps] or 'none'}")
    print("\n  Postulates the harvest reaches that the stencil did NOT:")
    for p in sorted(set(syn_h) - set(syn_s)):
        keys = sorted({k for g in syn_h[p] for k in g["capability_keys"]})[:2]
        print(f"    + {p:<34} -> {keys}")
    print("\n  The selector still PRUNES (not flag-everything): already-solved")
    print("  postulates yield NO gap even with the richer library:")
    for p in ("coarticulation", "lack_of_invariance", "speaker_normalization"):
        if p in {n for _, n, _ in harvest_postulates(sub)}:
            gg = synthesize_gaps(sub, p, shapes="harvested", record=False)
            print(f"    {p:<34} -> {'PRUNED (no gap)' if not gg else gg}")

    print("\n" + "=" * 78)
    print("ACCEPTANCE 3 — HONESTY: agent-vs-human split + harvest quality")
    print("=" * 78)
    print(f"""  WHAT IS THE AGENT'S (no human in the loop for these):
    - the order-N STRUCTURE (recursive differentiate over its own postulates);
    - the implication-SHAPES, now HARVESTED from its OWN {rep['n_donor_concepts']}
      concepts across {rep['n_domains']} domains by implication_harvester — the SAME
      abstract-the-structure move analogy.abstract_patterns makes for features;
    - the SELECTOR (compression vs covered set + speech-codebase scan).

  WHAT IS STILL HUMAN SCAFFOLDING (named plainly):
    - the EXTRACTORS in implication_harvester._extractors are the agent's GENERIC
      grasp of "what kinds of implication exist" (invertibility, latent-structure,
      ...) — keyword recognisers, NOT the implications themselves. They are the
      analogue of analogy._skeletonize's "an Attr is a hole": domain-general, ~7
      kinds. The SHAPES (which structures the agent holds, what they entail, which
      concept donates each) come entirely from the agent's concepts. A NEW kind of
      implication still needs a new extractor (as a new finite-difference stencil
      order would) — that is the residual human-bounded surface, much smaller than
      a per-shape hand list.
    - the speech-side consequence wording + name_keys per kind (so the gap reads in
      the agent's speech vocabulary) is templated, not free-form from the concept.

  HARVEST QUALITY (honest): {rep['n_shapes']} shapes, one per kind, each named from
  the donor concept that BEST exhibits it (ranked by evidence + a name-level
  structural signal, so 'IIR_filter' beats 'causal_attention_mask' for the all-pole
  shape). Loose donors exist in the long tail (e.g. thermodynamic 'entropy' brushes
  the sequence kind) but the ranking does not promote them to the named source.""")
    n_known = len(_KNOWN)
    n_derived = sum(1 for k in _KNOWN.values() if any(k in c for c in caps_d))
    n_open = sum(1 for k in _KNOWN.values() if any(k in c for c in caps_h))
    print(f"""
  DERIVATION RECALL (live-computed, not a print constant): {n_derived}/{n_known}
  of the known capabilities are DERIVED from the agent's harvested shapes with the
  stencil OFF — self-sufficiency is real. Of those, {n_open}/{n_known} are still
  OPEN gaps; the rest the agent has since IMPLEMENTED (e.g. LPC: the iter-2 loop
  built the all-pole front-end in sound_graph.py, so the selector correctly stops
  flagging it as a gap while the all-pole shape still DERIVES it from
  source_filter_theory). The earlier '3/3 recall' prose was a stale CONSTANT that
  conflated derivation with openness; this line is computed from the live run.""")


if __name__ == "__main__":
    main()
