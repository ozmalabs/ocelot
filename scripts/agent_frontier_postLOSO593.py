"""ASK THE AGENT its frontier AFTER the cross-speaker LOSO 0.593 session — register
the CURRENT state HONESTLY (NO answer seeded) and run the agent's OWN LIVE machinery.

Companion to scripts/agent_frontier_selfdiagnosis_postiter40.py, but for the state
AFTER this session's bottom-up work: real 40-speaker LOSO speaker recognition reached
0.593 (CMVN + VTL + order-N dynamic front-end features, then the DTW temporal-alignment
recognizer = the big +0.152 jump, then multi-stream DTW = near-exhausted at +0.023).

CRITICAL — this harness AVOIDS the framing trap in the iter-40 harness's section [4]:
that harness HAND-FED front-end shortfalls (all-pole / speaker-norm / coarticulation
measured-below-target), which is what made its pick land on the feature front-end. Here
the iter-40 bound was the front-end; THIS session's premise is the OPPOSITE — the
bottom-up feature+alignment levers are now LARGELY EXHAUSTED. So we:

  (A) run the UNBIASED live ranker first (synthesize_gaps + synthesize_over_all +
      gap_prioritiser.pick_frontier) with NO measurements injected — the agent's bare
      a-priori compression-payoff pick over its OWN harvested shapes. Verbatim.

  (B) then feed ONLY the session's EMPIRICAL fact — that the bottom-up front-end +
      alignment axes were ATTEMPTED and are near-marginal — via the agent's OWN
      exhaustion mechanism (measurement_feedback.mark_attempted_marginal, the
      attempted_marginal=1 "move-on" signal). We do NOT tell it where to go; we record
      what was tried, and let its OWN Argmax (effective_score with the exhaust penalty)
      re-pick. Where it lands AFTER the bottom-up axes are marked exhausted is the
      agent's own answer to "the residual is top-down?" — NOT imposed.

Everything decision-bearing is the agent's graph-resident Term (synthesize_gaps'
order-N derivative + selector; gap_prioritiser's Argmax-of-score; measurement_feedback's
exhaust-penalised Argmax), evaluated natively. The Python here only builds the mind,
registers the honest state text, records the empirical exhaustion, and prints what the
agent derives + picks.

Run:  python scripts/agent_frontier_postLOSO593.py
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
from domains import measurement_feedback as mf


POSTULATE_NAME = "recognition_state_postLOSO593"

# definition = WHAT the state IS (structural description, no remedy).
POSTULATE_DEFINITION = (
    "Cross-speaker speaker recognition is a BOTTOM-UP audio pipeline. Real 40-speaker "
    "leave-one-speaker-out (LOSO) accuracy reached 0.593. The pipeline is: a FRONT-END "
    "that extracts per-frame features (cepstral mean-variance normalisation CMVN, "
    "vocal-tract-length VTL warping, and order-N dynamic / velocity-acceleration "
    "features), feeding a DTW TEMPORAL-ALIGNMENT recogniser that warps two utterances "
    "onto a common time axis and scores their aligned distance, extended to MULTI-STREAM "
    "DTW (several feature streams aligned jointly). The recogniser compares a held-out "
    "utterance to a banked exemplar library by aligned distance."
)

# why = the OBSERVED behaviour the state exhibits (the load-bearing session facts), no
# remedy named.
POSTULATE_WHY = (
    "Measured this session: the DTW temporal-alignment recogniser was the single largest "
    "lift (+0.152 LOSO over the front-end-features-only nearest-neighbour baseline). "
    "Adding MULTI-STREAM DTW on top gained only +0.023 (near-exhausted). The front-end "
    "feature levers (CMVN, VTL, order-N dynamics) and the alignment levers (single- then "
    "multi-stream DTW) are therefore LARGELY EXHAUSTED as bottom-up signal sources: each "
    "successive bottom-up addition returns less. The residual is 0.407 (0.593 to perfect). "
    "The recogniser uses NO model of WHO the speakers are beyond the banked exemplars, NO "
    "context or expectation about which speaker is likely, and NO sequential / lexical "
    "structure across an utterance beyond the frame alignment — every cue it uses is a "
    "bottom-up acoustic measurement of the current utterance in isolation."
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
    mt = next(n for n in sub.nodes("Microtheory")
              if sub.node(n)["attrs"].get("name") == "speech_science")
    cid = _install_concept(sub, mt, POSTULATE_NAME, POSTULATE_DEFINITION)
    sub.set_attr(cid, "why", POSTULATE_WHY)
    sub.set_attr(cid, "origin", "frontier_state_postLOSO593")
    sub.set_attr(cid, "category", "self_state")
    return cid


def main():
    print("=" * 80)
    print("ASK THE AGENT — frontier self-diagnosis, post cross-speaker LOSO 0.593")
    print("=" * 80)

    sub = _build_mind()
    cid = _register_postulate(sub)
    print("\n[REGISTERED] the post-LOSO-0.593 state as a held postulate (NO fix seeded):")
    print(f"    concept name : {POSTULATE_NAME}")
    posts = {nm for _, nm, _ in onp.harvest_postulates(sub)}
    print(f"    held as order-0 postulate? {POSTULATE_NAME in posts}  "
          f"(total held postulates: {len(posts)})")

    shape_lib, mode = onp._resolve_shapes(sub, None)
    print("\n[LIVE-PROOF] implication-shape library used by the order-N derivative:")
    print(f"    mode = '{mode}'  shape count = {len(shape_lib)}  "
          f"(frozen hand stencil = {len(onp._shapes())}; not the driver)")

    # ===================================================================
    # (A) UNBIASED live derivation + pick — NO measurements injected.
    # ===================================================================
    print("\n" + "-" * 80)
    print("[A1] order-N derivative OF THE NEW POSTULATE (prune=False = what DERIVES)")
    print("-" * 80)
    derived = onp.synthesize_gaps(sub, POSTULATE_NAME, max_order=3,
                                  shapes="harvested", prune=False, record=False)
    if not derived:
        print("    (nothing derived — no harvested shape transferred onto the text)")
    for g in derived:
        print(f"    - order {g['order']} via {g['via_shapes']}: {g['capability_keys']}")

    print("\n    [A1'] prune=True (OPEN gaps only — un-realized):")
    open_gaps = onp.synthesize_gaps(sub, POSTULATE_NAME, max_order=3,
                                    shapes="harvested", prune=True, record=True)
    if not open_gaps:
        print("    (selector judged NO OPEN gap derivable — all derived caps already built)")
    for g in open_gaps:
        print(f"    - order {g['order']}: {g['capability_keys']}  ({g['gap'][:80]})")

    print("\n" + "-" * 80)
    print("[A2] full gap-map + UNBIASED ranking (compression payoff, NO injected state)")
    print("-" * 80)
    onp.synthesize_over_all(sub, record=True, shapes="harvested", prune=False)
    breadth = gp.shape_firing_breadth(sub, shape_lib)
    gp.build_axis_env(sub, shape_breadth=breadth)
    rows = gp.rank_gaps(sub, shape_breadth=breadth)
    for r in rows[:12]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        print(f"      payoff={r['payoff']:>3} order={r['min_order']} "
              f"score={r['score']:>8}  level={lvl:<22} {r['capability_keys'][:3]}")

    print("\n[A3] THE UNBIASED PICK (graph Argmax Term, native eval):")
    pick = gp.pick_frontier(sub, shape_breadth=breadth)
    if pick:
        print(f"    PICKED : {pick['capability_keys']}")
        print(f"    level  : {gp.axis_pipeline_level(pick['capability_keys'])[0]}")
        print(f"    payoff : {pick['postulates_unified']} (runner-up {pick.get('runner_up_payoff')})")
        print(f"    gap    : {pick.get('gap_text', '')[:160]}")
        print(f"    from   : {pick.get('source_concepts')}")
    unbiased_keys = list(pick["capability_keys"]) if pick else []
    unbiased_level = gp.axis_pipeline_level(unbiased_keys)[0] if pick else None

    # ===================================================================
    # (B) Feed ONLY the session's EMPIRICAL fact (bottom-up exhausted) via the
    #     agent's OWN exhaustion signal, then let its OWN Argmax re-pick.
    # ===================================================================
    print("\n" + "-" * 80)
    print("[B] record the session's EMPIRICAL bottom-up EXHAUSTION (agent's own "
          "attempted_marginal 'move-on' signal) — then its OWN Argmax re-picks")
    print("-" * 80)
    # The bottom-up axes the session BUILT + MEASURED + found near-marginal. We mark
    # them attempted (the move-on signal). We do NOT add any new axis or point anywhere.
    bottom_up = [
        ("all-pole", 0.593, 0.570, "front-end features CMVN/VTL/order-N dynamics: built, near-marginal"),
        ("lpc-formant", 0.593, 0.570, "front-end spectral-envelope features: built, near-marginal"),
        ("speaker normalization", 0.593, 0.570, "VTL / speaker-norm front-end: built, near-marginal"),
        ("formant ratio", 0.593, 0.570, "formant-ratio normalisation: built, near-marginal"),
        ("vocal-tract-length", 0.593, 0.570, "VTL warp: built, near-marginal"),
        # DTW temporal alignment was the big lift but multi-stream added only +0.023:
        ("dtw", 0.593, 0.570, "DTW + multi-stream temporal alignment: built, +0.023 near-exhausted"),
        ("alignment", 0.593, 0.570, "temporal alignment recogniser: built, near-exhausted"),
    ]
    marked = []
    for key, achieved, baseline, note in bottom_up:
        res = mf.mark_attempted_marginal(
            sub, attempted_key=key, achieved=achieved, baseline=baseline,
            floor=0.025, n_attempts=2, metric="LOSO speaker recognition",
            note=note)
        if res["axis"] is not None:
            marked.append(key)
    print(f"    marked attempted_marginal (move-on) on bottom-up axes present: {marked}")
    print("    (axes the session BUILT; NO new axis minted, NO target injected — only "
          "the empirical 'tried, near-marginal' fact)")

    rows_b = mf.rerank_with_feedback(sub)
    print("\n    THE AGENT'S RE-RANK after exhausting bottom-up (effective_score with "
          "the exhaust penalty; native Term):")
    for r in rows_b[:12]:
        lvl, _ = gp.axis_pipeline_level(r["capability_keys"])
        exh = "EXHAUSTED" if r["effective_score"] < 0 else ""
        print(f"      eff_score={r['effective_score']:>14}  level={lvl:<22} "
              f"{r['capability_keys'][:3]} {exh}")

    print("\n[B2] THE AGENT'S PICK after bottom-up exhausted (graph Argmax, native eval):")
    pick_b = mf.pick_with_feedback(sub)
    after_keys = list(pick_b["capability_keys"]) if pick_b else []
    after_level = gp.axis_pipeline_level(after_keys)[0] if pick_b else None
    if pick_b:
        print(f"    PICKED : {after_keys}")
        print(f"    level  : {after_level}")
        print(f"    eff_score : {pick_b['effective_score']}")
        a = sub.node(pick_b["axis_id"])["attrs"]
        print(f"    gap    : {str(a.get('gap_text',''))[:160]}")

    # ===================================================================
    # Convergence read-out.
    # ===================================================================
    print("\n" + "=" * 80)
    print("BEFORE vs AFTER — bottom-up exhaustion")
    print("=" * 80)
    print(f"  UNBIASED pick (bare compression)      : {unbiased_keys[:3]}  [level {unbiased_level}]")
    print(f"  AFTER bottom-up marked exhausted      : {after_keys[:3]}  [level {after_level}]")
    front_end = {"feature_extraction", "speaker_normalization", "perception_units"}
    top_down_ish = {"recognition", "segmentation"}
    print(f"\n  Did exhausting the bottom-up axes move the agent OFF the front-end?")
    print(f"     unbiased level = {unbiased_level}  ->  after-exhaustion level = {after_level}")
    print(f"     (front-end levels = {sorted(front_end)};")
    print(f"      more-top-down/structural levels = {sorted(top_down_ish)})")

    print("\n" + "=" * 80)
    print("END — the above is the agent's OWN live derivation + pick, verbatim.")
    print("=" * 80)


if __name__ == "__main__":
    main()
