"""PROVE the deep context cone is À LA CARTE — every dimension independently
SALIENCE/RELEVANCE-gated against THIS artifact, NOT a wholesale blob.

THE PRINCIPLE (the admissibility/efficiency thesis, granular). The deep cone is a
SET OF DIMENSIONS, each independently relevance-gated — not a fixed full web:
  · IDENTITY {name, owner, when}  — the cheap core, ALWAYS kept once deep.
  · ALIGNMENT_WEB (politics / content_moderation / elon_musk / ai_output_incident)
    — RELEVANT only if the artifact TOUCHES alignment (its surface references those
    concepts).
  · TRUST (epistemic weight)      — RELEVANT only if the artifact makes a
    reliability-relevant CLAIM (a promo / opinion does not invoke source trust).
  · TIMELINE_EVENTS               — EACH event gated by its OWN grounded concepts
    overlapping the artifact (the verification/moderation event for a censorship
    post; grok_mechahitler for an AI-safety post) — NOT the whole timeline.
  · STANCE                        — already gated (no clues -> not relevant).
An irrelevant dimension is a NOT-RELEVANT salience verdict (omitted + logged),
exactly like the no-clue stance abstain — never materialized.

PROVEN here (no LLM, no Rust, no per-case Python decision — the per-dimension
relevance test REUSES the cheap surface-clue machinery; the dimensions are
decomposed from context_for's output + composition):

  SAME venue@2024, THREE salient artifacts -> DIFFERENT included dimensions:
    1. a PRODUCT-LAUNCH post   -> identity only (alignment/trust/timeline NOT
       RELEVANT). The cone is SPARSE; the implied web is EMPTY.
    2. a FREE-SPEECH / censorship post -> identity + alignment_web
       (content_moderation/elon_musk) + the moderation/verification timeline
       events + trust. The relevant SUBSET of the web.
    3. an AI-SAFETY post (about the platform's AI) -> identity + the
       grok_mechahitler event + trust; finance/acquisition NOT relevant; stance
       NOT relevant (a question, no stance clues).

  The SAME venue cone yields DIFFERENT included dimensions purely by the artifact's
  relevance — the implied web is the RELEVANT SUBSET, not the full union.

  EFFICIENCY: the omitted dimensions are NOT materialized (the assembled implied
  web is the relevant subset; the full union is computed once as the substrate but
  only the relevant dimensions enter the cone). Report dimensions_included vs
  dimensions_not_relevant per artifact.

  NO REGRESSION: a free-speech artifact still gets the full relevant alignment cone
  (the venue×author divergence holds when alignment IS relevant); the cheap-vs-deep
  gate, stance gating, and the Wikipedia static case are intact.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT))

from substrate_rs import _native
from domains.communication_concepts import install_communication_concepts_seed
from domains import contextualization_depth as cd


def _show(tag, deep):
    print(f"\n  {tag}")
    print(f"    dimensions_included     = {deep['dimensions_included']}")
    print(f"    dimensions_not_relevant = "
          f"{[x['dimension'] for x in deep['dimensions_not_relevant']]}")
    print(f"    assembled_implied (the RELEVANT subset) = "
          f"{deep['assembled_implied']}")
    print(f"    full_implied (the substrate union)      = "
          f"{sorted(deep.get('implied') or [])}")
    for x in deep["dimensions_not_relevant"]:
        print(f"      - {x['dimension']}: {x['why']}")


def main() -> int:
    s = _native.Substrate()
    install_communication_concepts_seed(s)
    ok = True

    print("=" * 78)
    print("THE PER-DIMENSION RELEVANCE GATE (reuses the cheap surface-clue scan)")
    print("=" * 78)
    print("  the deep cone is a SET OF DIMENSIONS, each independently gated:")
    print("    identity (always) | alignment_web | trust | timeline_events | stance")
    print("  each irrelevant dimension = a NOT-RELEVANT salience verdict (omitted).")

    # ======================================================================
    # SAME venue@2024, THREE salient artifacts -> DIFFERENT cone dimensions.
    # ======================================================================
    care = {"source": "X post", "when": "2024-03-01", "topic": "twitter_x",
            "stake": 0.9, "surprise": 0.8, "relevance": 0.7}

    # 1. PRODUCT-LAUNCH — promotional, audience-directed; touches NO alignment,
    #    makes NO reliability claim (low stake), references NO timeline concept.
    launch = dict(care, stake=0.2,
                  surface=("new drop is out now! check out our latest sneakers "
                           "— link in bio, use code SPRING. still here for you."))
    # 2. FREE-SPEECH / CENSORSHIP — touches the alignment web (moderation/elon),
    #    a high-stakes claim about the platform.
    rant = dict(care,
                surface=("free speech is back — thank you Elon, no more "
                         "censorship on this platform. the moderation regime is "
                         "gone and that's a good thing."))
    # 3. AI-SAFETY — about the platform's AI; touches ai_output_incident + trust,
    #    NOT finance/acquisition. A question -> NO stance clues.
    safety = {"source": "X post", "when": "2025-09-01", "topic": "twitter_x",
              "stake": 0.9, "surprise": 0.9, "relevance": 0.7,
              "surface": ("the platform's AI Grok just produced MechaHitler "
                          "extremist output — can anything it says be trusted "
                          "as reliable now?")}

    d_launch = cd.deep_context_for_author(s, "X post", "2024-03-01",
                                          author=None, artifact=launch)
    d_rant = cd.deep_context_for_author(s, "X post", "2024-03-01",
                                        author=None, artifact=rant)
    d_safety = cd.deep_context_for_author(s, "X post", "2025-09-01",
                                          author=None, artifact=safety)

    print("\n" + "=" * 78)
    print("SAME venue cone, THREE artifacts -> DIFFERENT included dimensions")
    print("=" * 78)
    _show("1. PRODUCT-LAUNCH (promotional, no alignment, no claim):", d_launch)
    _show("2. FREE-SPEECH / CENSORSHIP (touches alignment + claim):", d_rant)
    _show("3. AI-SAFETY (about the platform AI; a question):", d_safety)

    print("\n" + "-" * 78)
    # 1. LAUNCH: SPARSE — identity kept; alignment/trust/timeline NOT relevant.
    launch_sparse = ("identity" in d_launch["dimensions_included"]
                     and "alignment_web" not in d_launch["dimensions_included"]
                     and "trust" not in d_launch["dimensions_included"]
                     and "timeline_events" not in d_launch["dimensions_included"]
                     and d_launch["assembled_implied"] == [])
    print(f"  [{'OK ' if launch_sparse else 'XX '}] LAUNCH is SPARSE: identity only "
          f"(alignment/trust/timeline NOT RELEVANT); implied web EMPTY")
    ok = ok and launch_sparse

    # 2. RANT: alignment_web + moderation/verification timeline + trust.
    rant_inc = set(d_rant["dimensions_included"])
    rant_align = ("alignment_web" in rant_inc
                  and {"content_moderation", "elon_musk"}
                  <= set(d_rant["dimensions"].get("alignment_web", [])))
    rant_events = {e["id"] for e in
                   d_rant["dimensions"].get("timeline_events", [])}
    rant_timeline = ("timeline_events" in rant_inc
                     and "moderation_change" in rant_events)
    rant_trust = "trust" in rant_inc
    print(f"  [{'OK ' if rant_align else 'XX '}] RANT pulls the alignment_web SUBSET "
          f"{d_rant['dimensions'].get('alignment_web')}")
    print(f"  [{'OK ' if rant_timeline else 'XX '}] RANT pulls the moderation/"
          f"verification timeline events {sorted(rant_events)}")
    print(f"  [{'OK ' if rant_trust else 'XX '}] RANT pulls trust (a reliability "
          f"claim about the platform)")
    ok = ok and rant_align and rant_timeline and rant_trust

    # 3. SAFETY: grok_mechahitler event + trust; finance/acquisition NOT pulled;
    #    stance NOT relevant (a question).
    safety_events = {e["id"] for e in
                     d_safety["dimensions"].get("timeline_events", [])}
    safety_grok = "grok_mechahitler" in safety_events
    safety_no_finance = not ({"finance", "acquisition"}
                             & set(d_safety["assembled_implied"]))
    safety_stance_omitted = ("stance" not in d_safety["dimensions_included"]
                             and any(x["dimension"] == "stance"
                                     for x in d_safety["dimensions_not_relevant"]))
    safety_trust = "trust" in d_safety["dimensions_included"]
    print(f"  [{'OK ' if safety_grok else 'XX '}] SAFETY pulls the grok_mechahitler "
          f"event {sorted(safety_events)}")
    print(f"  [{'OK ' if safety_no_finance else 'XX '}] SAFETY does NOT pull "
          f"finance/acquisition (not relevant to an AI-safety post)")
    print(f"  [{'OK ' if safety_trust else 'XX '}] SAFETY pulls trust (a "
          f"reliability question)")
    print(f"  [{'OK ' if safety_stance_omitted else 'XX '}] SAFETY stance NOT "
          f"RELEVANT (a question, no stance clues) — omitted + logged")
    ok = ok and safety_grok and safety_no_finance and safety_trust \
        and safety_stance_omitted

    # ======================================================================
    # THE IMPLIED WEB IS THE RELEVANT SUBSET, NOT THE FULL UNION.
    # ======================================================================
    print("\n" + "=" * 78)
    print("THE IMPLIED WEB IS THE RELEVANT SUBSET (à la carte, not wholesale)")
    print("=" * 78)
    full = set(d_rant.get("implied") or [])
    subset = set(d_rant["assembled_implied"])
    is_subset = subset <= full and subset != full
    print(f"  RANT full venue web (substrate) : {sorted(full)}")
    print(f"  RANT assembled (relevant subset): {sorted(subset)}")
    print(f"  [{'OK ' if is_subset else 'XX '}] the assembled web is a PROPER SUBSET "
          f"of the full union — not a dumped blob")
    # the launch materializes NOTHING of the web — the omitted dimensions are not
    # walked into the cone.
    launch_nothing = d_launch["assembled_implied"] == [] and full != set()
    print(f"  [{'OK ' if launch_nothing else 'XX '}] the LAUNCH materializes NONE of "
          f"the web (omitted dimensions not pulled), though the union is non-empty")
    ok = ok and is_subset and launch_nothing

    # the three artifacts pull DIFFERENT dimension sets — purely by relevance.
    diff = (d_launch["dimensions_included"] != d_rant["dimensions_included"]
            and d_rant["dimensions_included"] != d_safety["dimensions_included"]
            and d_launch["dimensions_included"]
            != d_safety["dimensions_included"])
    print(f"  [{'OK ' if diff else 'XX '}] all THREE artifacts include DIFFERENT "
          f"dimension sets over the SAME venue cone")
    ok = ok and diff

    # ======================================================================
    # NO REGRESSION — the prior proofs still hold.
    # ======================================================================
    print("\n" + "=" * 78)
    print("NO REGRESSION — cheap-vs-deep gate + venue×author when alignment IS rel.")
    print("=" * 78)
    # cheap-vs-deep: a bland artifact stays cheap (context_for not called).
    counter = cd.ConeCounter()
    bland = {"surface": "had coffee this morning", "source": "X post",
             "when": "2024-03-01", "topic": "twitter_x",
             "stake": 0.0, "surprise": 0.0, "relevance": 0.0}
    counter.reset()
    r_bland = cd.contextualize(s, bland, context_for=counter)
    cheap_ok = r_bland["depth"] == "cheap" and counter.calls == 0
    print(f"  [{'OK ' if cheap_ok else 'XX '}] bland artifact stays cheap "
          f"(context_for ran {counter.calls} times) — the salience gate intact")
    ok = ok and cheap_ok

    # venue×author: the rant's endorser stance still amplifies the (relevant)
    # alignment — the prior divergence holds WHEN alignment IS relevant.
    align_amplified = (d_rant.get("stance") == "endorses"
                       and set(d_rant.get("amplified") or [])
                       & {"content_moderation", "elon_musk"})
    print(f"  [{'OK ' if align_amplified else 'XX '}] the RANT endorser still "
          f"AMPLIFIES the relevant alignment {d_rant.get('amplified')} "
          f"(venue×author intact when alignment IS relevant)")
    ok = ok and align_amplified

    print("\n" + "=" * 78)
    print("RESULT:", "ALL OK" if ok else "FAILURE")
    print("=" * 78)
    print("""
The LEARNING: the WHOLE deep cone is salience-gated DIMENSION-BY-DIMENSION —
assembled À LA CARTE from only the dimensions RELEVANT to THIS artifact, each
irrelevant dimension a decisive NOT-RELEVANT verdict (never materialized). The
SAME venue@2024 yields DIFFERENT included dimensions purely by the artifact's
relevance: a product launch pulls IDENTITY ONLY (sparse, empty implied web); a
free-speech rant pulls the alignment_web SUBSET + the moderation/verification
timeline events + trust; an AI-safety post pulls the grok_mechahitler event +
trust but NOT finance/acquisition and NOT stance. The implied web is the RELEVANT
SUBSET, not a dumped blob — the admissibility/efficiency thesis, granular: JIT/
include only the admitted dimensions, never spend on the inadmissible-for-this-
artifact ones.

FAITHFUL: the per-dimension relevance test REUSES the cheap surface-clue scan
(the same kind _surface_clues uses for stance) — does the artifact's surface
reference the dimension's concepts? The dimensions are decomposed from
context_for's output; the gate + assembly are composition. No LLM, no Rust, no
per-case Python decision.

HONEST / coarse: the relevance test is surface-concept overlap (a small
hand-tied synonym set per alignment concept, the same coarse marker vocabulary
the stance clues use); the dimension decomposition is a small fixed set
(identity/alignment_web/trust/timeline_events/stance); the timeline-event
relevance is concept-overlap; the trust-claim test leans on the world-supplied
`stake` care-signal, not a learned claim detector. The full venue union is still
computed ONCE as the substrate (the cheap context_for), but only the RELEVANT
dimensions enter the assembled cone — the blob is never surfaced.""")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
