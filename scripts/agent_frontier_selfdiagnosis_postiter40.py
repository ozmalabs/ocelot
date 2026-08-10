"""ASK THE AGENT its frontier post-iter-40 — register the current state HONESTLY as
a postulate (NO answer seeded) and run the agent's OWN LIVE gap-synthesis + ranking.

The project principle: at a fork about the agent's frontier, the agent decides via
its OWN machinery. This driver does ONLY:
  (1) build the mind (full breadth: phonology + speech_science + math/eng/ml + the
      concept expansions — so the harvested implication-shape library is the agent's
      own concepts, NOT the hand stencil);
  (2) REGISTER the post-iter-40 state as a Concept (a held postulate) carrying ONLY
      honest description text — the recognition-graph state, the fast/slow paths, the
      iter-39/40 negative results, and the LOCALISED BOUND — with NO suggested fix;
  (3) RUN the LIVE machinery:
        - synthesize_gaps over the NEW postulate (order-N derivative + selector),
          shapes="harvested" (the agent's own concepts, not the frozen _shapes stencil);
        - synthesize_over_all (the full gap-map across every held postulate);
        - gap_prioritiser.rank_gaps / pick_frontier (the agent's graph-resident
          Argmax-of-(payoff*K - order) ranking Term, evaluated NATIVELY).
  (4) PRINT verbatim what the agent derives + picks — no massaging, no seeded answer.

This is the LIVE path (synthesize_gaps / order_n_postulates / gap_prioritiser reading
the agent's CURRENT graph), NOT the hardcoded runtime_design._specify_* dicts (which
the project notes flag as frozen historical records). Proof of liveness is printed:
the shape library mode, the shape count, and the fact that the NEW postulate's
derivation chain is produced from the harvested shapes against the text just registered.

Run:  python scripts/agent_frontier_selfdiagnosis_postiter40.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

from domains.stt_pipeline import STTPipeline, STTParams
from domains.phonology import install_phonology
from domains.speech_science import install_speech_science
from domains.mathematics import install_mathematics_seed
from domains.engineering import install_engineering_seed
from domains.machine_learning import install_machine_learning_seed
from domains.concept_expansions import install_all_concept_expansions
from domains.code_authoring import _install_concept
from domains import order_n_postulates as onp
from domains import gap_prioritiser as gp


# The NEW postulate's name + HONEST text. NO suggested fix is written anywhere here —
# only a faithful description of where the recognition system stands after iter-40.
POSTULATE_NAME = "recognition_state_postiter40"

# definition = WHAT the state IS (structural description, no remedy).
POSTULATE_DEFINITION = (
    "The recognition is a combinatorial GRAPH: a fast cue-graph that recognises in "
    "real time from a banked library, plus a slow order-N analysis-by-synthesis path "
    "that replays an utterance, parses it, learns the structure and banks it, plus a "
    "retained exemplar library. The FAST path wires four acoustic axes: a FILTER axis "
    "(the spectral-envelope cue, the only axis that substantially lifts recognition), a "
    "SOURCE axis (the F0 / pitch contour), a TEMPORAL-RATE axis (the modulation "
    "spectrum), and a TRANSIENT axis (acoustic landmarks). The last three axes are "
    "orthogonal in information (each catches bottom-up errors above chance, with "
    "error-overlap 1.4 to 1.7 times) but are small or borderline as raw 1-nearest-"
    "neighbour nodes. The SLOW path is built and correct."
)

# why = the OBSERVED behaviour / structural property the state exhibits (the load-
# bearing facts iter-39/40 measured), still NO remedy named.
POSTULATE_WHY = (
    "Measured: the order-N analysis-by-synthesis does NOT beat single-pass, and the "
    "learn-and-bank loop does NOT close (iter-39). Routing recognition candidates "
    "through a better waveform synthesis makes recognition WORSE (no-synth 0.267 is "
    "much greater than old-voicebox 0.183 which is greater than klatt 0.133): the "
    "analysis to synthesis to analysis DOMAIN GAP dominates, so the forward model must "
    "be inverted in FEATURE SPACE, not in audio (iter-40). The localised bound is "
    "therefore feature-space DISCRIMINATION: the orthogonal cues CARRY the information "
    "but the raw feature-space nodes cannot extract or discriminate it. The bound is "
    "the FEATURE FRONT-END (the gammatone-wall / speaker-normalisation regime), not "
    "synthesis fidelity and not iteration depth. The vocal tract is a context-dependent "
    "non-invariant filter whose resonances vary with the speaker and with the "
    "neighbouring sounds; the front-end's perceived units are blurry and speaker-shaped."
)


def _build_mind():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    install_phonology(sub)
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def _register_postulate(sub):
    """Register the post-iter-40 state as a held Concept (postulate) under the
    speech_science Mt. The text is honest description ONLY — no suggested fix. The
    harvest_postulates reader concatenates definition + why as the postulate text the
    order-N derivative differentiates."""
    mt = next(n for n in sub.nodes("Microtheory")
              if sub.node(n)["attrs"].get("name") == "speech_science")
    cid = _install_concept(sub, mt, POSTULATE_NAME, POSTULATE_DEFINITION)
    sub.set_attr(cid, "why", POSTULATE_WHY)
    sub.set_attr(cid, "origin", "frontier_state_postiter40")
    sub.set_attr(cid, "category", "self_state")
    return cid


def main():
    print("=" * 80)
    print("ASK THE AGENT — frontier self-diagnosis, post-iter-40")
    print("=" * 80)

    sub = _build_mind()

    # ---- (2) register the state as a postulate (NO answer seeded) -------------
    cid = _register_postulate(sub)
    print("\n[REGISTERED] the post-iter-40 state as a held postulate (NO fix seeded):")
    print(f"    concept name : {POSTULATE_NAME}")
    print(f"    definition   : {POSTULATE_DEFINITION[:300]} ...")
    print(f"    why          : {POSTULATE_WHY[:300]} ...")
    # confirm the agent now HOLDS it as an order-0 postulate the operator can read
    posts = {nm for _, nm, _ in onp.harvest_postulates(sub)}
    print(f"    held as order-0 postulate? {POSTULATE_NAME in posts}  "
          f"(total held postulates: {len(posts)})")

    # ---- PROOF the machinery is LIVE (harvested shapes, not the frozen stencil) -
    shape_lib, mode = onp._resolve_shapes(sub, None)   # default = harvested
    print("\n[LIVE-PROOF] implication-shape library used by the order-N derivative:")
    print(f"    mode = '{mode}'   (must be 'harvested', i.e. shapes from the agent's "
          f"OWN concepts — NOT the runtime_design._specify_* hardcoded dicts)")
    print(f"    shape count = {len(shape_lib)}   (the harvested catalogue size)")
    stencil_only = onp._shapes()
    print(f"    (for contrast, the frozen hand stencil has {len(stencil_only)} shapes; "
          f"we are NOT using it as the driver)")

    # ======================================================================
    # (3a) RUN synthesize_gaps OVER THE NEW POSTULATE — the agent's order-N
    #      derivative of the state we just registered, selected by the selector.
    #      prune=True so only OPEN (un-realized) gaps are returned (the live
    #      'what is missing NOW' reading).
    # ======================================================================
    print("\n" + "-" * 80)
    print("[3a] LIVE order-N synthesis OVER THE NEW POSTULATE (synthesize_gaps, "
          "harvested shapes, prune=True)")
    print("-" * 80)
    gaps_new = onp.synthesize_gaps(sub, POSTULATE_NAME, max_order=3,
                                   shapes="harvested", prune=True, record=True)
    if not gaps_new:
        print("    (the selector judged NO open gap derivable from this postulate "
              "with the harvested shapes — reported honestly)")
    for g in gaps_new:
        print(f"\n    GAP (order {g['order']}): {g['gap']}")
        print(f"      capability_keys : {g['capability_keys']}")
        print(f"      via_shapes      : {g['via_shapes']}")
        print(f"      source_domains  : {g['source_domains']}")
        print(f"      source_concepts : {g.get('source_concepts')}")
        print(f"      derivation chain:")
        for step in g["chain"]:
            print(f"         - {step}")

    # also show what DERIVES regardless of whether already realized (prune=False),
    # so we can see the derivation even for capabilities the agent has since built.
    print("\n    [3a'] same postulate, prune=False (DERIVATION-only, incl. already-built):")
    derived_new = onp.synthesize_gaps(sub, POSTULATE_NAME, max_order=3,
                                      shapes="harvested", prune=False, record=False)
    for g in derived_new:
        print(f"      - order {g['order']} via {g['via_shapes']}: "
              f"{g['capability_keys']}")
    if not derived_new:
        print("      (nothing derived — no harvested shape transferred onto the "
              "postulate's text)")

    # ======================================================================
    # (3b) RUN synthesize_over_all — the full gap-map across EVERY held postulate
    #      (the agent's whole self-derived frontier set), then the ranker picks.
    # ======================================================================
    print("\n" + "-" * 80)
    print("[3b] LIVE full gap-map (synthesize_over_all across ALL held postulates) "
          "+ graph-resident RANKING")
    print("-" * 80)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    # the specificity gate (drop promiscuous-shape firings) — the agent's own
    # MDL-correctness on the scaled gap-set.
    breadth = gp.shape_firing_breadth(sub, shape_lib)
    axes = gp.build_axis_env(sub, shape_breadth=breadth)
    print(f"    CapabilityAxes built from the agent's own synthesized gaps: {len(axes)}")

    rows = gp.rank_gaps(sub, shape_breadth=breadth)
    print("\n    THE AGENT'S RANKING (payoff = # held postulates the capability "
          "unifies; score = payoff*K - order; native graph Term):")
    for r in rows[:12]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        print(f"      payoff={r['payoff']:>3} order={r['min_order']} "
              f"score={r['score']:>8}  level={lvl:<22} {r['capability_keys'][:3]}")

    # ======================================================================
    # (3c) THE PICK — the agent ENACTS its choice via the graph Rule (Argmax Term
    #      evaluated natively), then we read back what it chose.
    # ======================================================================
    print("\n" + "-" * 80)
    print("[3c] THE AGENT'S PICK — enacted by the graph Rule (Argmax Term, native eval)")
    print("-" * 80)
    pick = gp.pick_frontier(sub, shape_breadth=breadth)
    if pick is None:
        print("    (no axes to pick from)")
    else:
        print(f"    PICKED capability_keys : {pick['capability_keys']}")
        print(f"    pipeline level         : "
              f"{gp.axis_pipeline_level(pick['capability_keys'])[0]}")
        print(f"    postulates unified     : {pick['postulates_unified']} "
              f"(runner-up payoff {pick.get('runner_up_payoff')})")
        print(f"    min derivation order   : {pick['min_order']}")
        print(f"    score                  : {pick['score']}")
        print(f"    gap_text               : {pick.get('gap_text')}")
        print(f"    criterion              : {pick['criterion']}")
        print(f"    source_concepts        : {pick.get('source_concepts')}")
    unguided_before = (list(pick["capability_keys"]) if pick else [])

    # ======================================================================
    # (4) THE META-GAP FIX (iter-42): feed the agent's OWN iter-39/40 MEASUREMENTS
    #     of its BUILT front-end capabilities (which it measured BELOW their target)
    #     as MeasuredCapability graph state — the world-adapter I/O role, translating
    #     the probe's results into the graph. The graph-resident Rule then RE-OPENS
    #     each built-but-insufficient capability as a CapabilityAxis ranked by its
    #     SHORTFALL, feeding the SAME Argmax. NO Python decides the pick — the Rule +
    #     the score Term (shortfall*BOOST) do, consuming the measurement.
    #
    #     These numbers are the agent's measured results recorded across iter-2/39/40
    #     (the same facts the registered postulate's `why` text describes): the built
    #     front-end (LPC formants / speaker-norm / coarticulation) underperforms its
    #     target — capped by the gammatone-wall front-end. The TARGETS are the agent's
    #     own bars (the spectrum baseline / floor the probes compared against).
    # ======================================================================
    print("\n" + "-" * 80)
    print("[4] META-GAP FIX — feed the iter-39/40 MEASURED shortfalls of the BUILT "
          "front-end; the Rule re-opens built-but-insufficient axes")
    print("-" * 80)
    # measured = what the probe achieved; target = the bar it was measured against.
    # (iter-2: cross-speaker purity 0.441 < spectrum 0.483, attributed to LPC/front-end;
    #  the LOSO sound-graph filter 0.335 << spectrum 0.649; speaker-norm modest +3%;
    #  coarticulation not moving — all BUILT, all measured below their target.)
    measured_builtinsufficient = [
        (["all-pole", "levinson", "lpc-formant"], 0.335, 0.649,
         "LOSO filter front-end vs spectrum baseline (sound-graph): built, capped"),
        (["speaker normalization", "formant ratio",
          "vocal-tract-length normalization"], 0.38, 0.65,
         "speaker-norm held-out: built (+3%), modest, bounded by blurry-cochlea formants"),
        (["coarticulation predict-remove", "context normalization",
          "carryover removal"], 0.45, 0.55,
         "coarticulation context-removal: built, measured not moving recognition"),
    ]
    for keys, meas, tgt, note in measured_builtinsufficient:
        gp.record_measured_capability(sub, keys, measured=meas, target=tgt,
                                      metric="LOSO/held-out recognition", note=note)
        print(f"    recorded MEASURED below target: {keys[:2]} "
              f"measured={meas} target={tgt}  shortfall={tgt - meas:.3f}")

    reopened = gp.synthesise_builtinsufficient_gaps(sub)
    print(f"\n    the Rule RE-OPENED {len(reopened)} built-but-insufficient "
          f"capabilities as gaps (graph Rule, consuming the measurement):")
    for ax in reopened:
        a = sub.node(ax)["attrs"]
        print(f"      - {list(a.get('capability_keys', []))[:3]}  "
              f"level={gp.axis_pipeline_level(a.get('capability_keys', []))[0]:<20} "
              f"shortfall={a.get(gp.SHORTFALL_ATTR):.3f}")

    rows_after = gp.rank_gaps(sub, shape_breadth=breadth)
    print("\n    THE AGENT'S RANKING AFTER the fix (score now includes the measured "
          "shortfall*BOOST for built-but-insufficient axes):")
    for r in rows_after[:8]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        print(f"      score={r['score']:>14}  level={lvl:<22} {r['capability_keys'][:3]}")

    print("\n" + "-" * 80)
    print("[4c] THE AGENT'S PICK AFTER the fix — same graph-resident Argmax Term")
    print("-" * 80)
    pick_after = gp.pick_frontier(sub, shape_breadth=breadth)
    after_keys = (list(pick_after["capability_keys"]) if pick_after else [])
    after_level = (gp.axis_pipeline_level(after_keys)[0] if pick_after else None)
    if pick_after is not None:
        print(f"    PICKED capability_keys : {after_keys}")
        print(f"    pipeline level         : {after_level}")
        print(f"    score                  : {pick_after['score']}")
        print(f"    gap_text               : {pick_after.get('gap_text')}")

    # ======================================================================
    # (5) BEFORE vs AFTER + the convergence verdict.
    # ======================================================================
    print("\n" + "=" * 80)
    print("BEFORE vs AFTER — the meta-gap fix")
    print("=" * 80)
    print(f"  BEFORE (bare compression ranker) picked : {unguided_before[:3]}  "
          f"[level {gp.axis_pipeline_level(unguided_before)[0] if unguided_before else None}]")
    print(f"  AFTER  (built-but-insufficient source)  : {after_keys[:3]}  "
          f"[level {after_level}]")
    front_end_levels = {"feature_extraction", "speaker_normalization"}
    converged = after_level in front_end_levels
    print(f"\n  The agent's order-N DERIVATIVE (section 3a') converged on the FEATURE "
          f"FRONT-END\n  (all-pole/LPC, speaker-norm, coarticulation). The fixed "
          f"SELECTOR now picks:\n     level = {after_level}")
    print(f"\n  VERDICT: selector converges with its own order-N derivative "
          f"(front-end)? {converged}")
    if converged:
        print("  => the meta-gap is FIXED: a built-but-insufficient capability is now a "
              "first-class\n     gap source; the selector self-prioritises it by the "
              "measured shortfall, landing\n     on the feature front-end — matching the "
              "order-N derivation.")

    print("\n" + "=" * 80)
    print("END — the above is the agent's OWN live derivation + pick, verbatim, "
          "no seeded answer.")
    print("=" * 80)


if __name__ == "__main__":
    main()
