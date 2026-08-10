"""yardstick_fix_resteer — LIVE verification of (1) the reliability-gated yardstick
and (2) the re-steered guided loop, on real FSDD through the agent's own perception.

This is a WORLD ADAPTER / verification driver (no agent decisions): it ingests FSDD,
reads the agent's own unit sequence, fires the graph-resident reliability gate Rule,
and prints what the gate + the guided ranker decide. All numbers are live.

  STEP 1  the FIXED yardstick on two samples:
            - the STARVED 108-utt subset (lex ~= tok, singleton-dominated) -> the gate
              SUPPRESSES the false 'perception' (frontier 'inconclusive', reliability
              low). Shows the gate predicates (tok/lex, shuffle-collapse) live.
            - a RELIABLE at-scale sample -> the units clear the floor (frontier 'none').

  STEP 2  re-steer: with perception gated OUT, the guided ranker no longer redirects to
            a perception/units artifact; it lands on the highest open REAL gap (the
            recognition stage / chunker->lexicon). Side by side with iter-6's pick.

Run:  python scripts/yardstick_fix_resteer.py
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
from domains.order_n_postulates import synthesize_over_all
from domains import gap_prioritiser as gp
from domains import perception_self_assessment as psa
from domains import process_meta_assessor as pma

import scripts.fsdd_learner_world as fl


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
    return sub, pipe


def _utts(per, ndig, nspk):
    af = fl.gather_files()
    speakers = sorted({sp for _, _, sp, _ in af})[:nspk]
    out = []
    for d in range(ndig):
        for sp in speakers:
            for p in [p for (p, dd, ss, _) in af if dd == d and ss == sp][:per]:
                s, _ = fl.load_wav(p)
                out.append(s)
    return out


def _run_yardstick(label, per, ndig, nspk):
    sub, pipe = _build_mind()
    utts = _utts(per, ndig, nspk)
    seqs = psa.read_unit_sequences(sub, pipe, utts)
    sig = psa.measure_unit_predictability(seqs)
    psa.record_perception_quality(sub, sig)
    fr = psa.install_perception_frontier_rule(sub)
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "perception_quality_pending", 1)
    flag = psa.agent_flag_perception(sub, fr["rule_index"])
    rel = psa.get_reliability(sub)
    a = sub.node(root)["attrs"]
    print(f"\n  [{label}]  {len(utts)} utterances -> {len(seqs)} usable sequences")
    print(f"    tokens={sig['n_tokens']}  lexicon={sig['lexicon_size']}  "
          f"tokens/lexicon={sig['tokens_per_lexicon']:.2f}  "
          f"(min adequate {a['min_tokens_per_lexicon']})")
    print(f"    predict_over_freq={sig['predict_over_freq']:.3f}  "
          f"shuffled_over_freq={sig['shuffled_over_freq']:.3f}  "
          f"shuffle_gap={sig['predict_over_freq'] - sig['shuffled_over_freq']:+.3f}  "
          f"(bite margin {a['shuffle_bite_margin']})  floor {a['predict_over_freq_floor']}")
    # the gate predicates, evaluated the way the Rule does:
    adequate = sig['tokens_per_lexicon'] >= a['min_tokens_per_lexicon']
    bites = (sig['predict_over_freq'] - sig['shuffled_over_freq']) >= a['shuffle_bite_margin']
    bad = (sig['predict_over_freq'] < a['predict_over_freq_floor'] or
           sig['compress_ratio'] > a['compress_ratio_ceiling'])
    print(f"    gate predicates: adequate_sample={adequate}  shuffle_bites={bites}  "
          f"bad_units={bad}")
    print(f"    => FRONTIER FLAG = '{flag}'   reliability = '{rel}'")
    return flag, rel, sig


def main():
    print("=" * 78)
    print("STEP 1 — THE FIXED YARDSTICK (reliability-gated, graph-resident Rule)")
    print("=" * 78)
    print("  The flag fires 'perception' ONLY when the reading is trustworthy:")
    print("    (a) adequate sample  (tokens/lexicon >= min — not singleton-dominated)")
    print("    (b) shuffle witness  (a PASS survives order-destruction; a FAIL has power)")

    starved_flag, starved_rel, _ = _run_yardstick(
        "STARVED 108-utt subset", per=6, ndig=6, nspk=3)
    scale_flag, scale_rel, _ = _run_yardstick(
        "RELIABLE at-scale sample", per=20, ndig=10, nspk=6)

    print("\n  ACCEPTANCE (1):")
    print(f"    starved -> '{starved_flag}' (reliability {starved_rel}): "
          f"{'NO false perception (GATED)' if starved_flag != 'perception' else 'STILL MIS-FIRES'}")
    print(f"    at-scale -> '{scale_flag}' (reliability {scale_rel}): "
          f"{'units read as passing (frontier none)' if scale_flag == 'none' else scale_flag}")

    # ======================================================================
    print("\n" + "=" * 78)
    print("STEP 2 — RE-STEER THE LOOP WITH THE FIXED YARDSTICK")
    print("=" * 78)
    print("  Build the agent's gap-set, run the guided ranker with the FIXED frontier")
    print("  (perception gated out at scale). The pick should land on the genuine")
    print("  recognition-stage gap, NOT the iter-6 perception_units artifact.")

    sub, pipe = _build_mind()
    synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    # the FIXED yardstick on the reliable at-scale sample drives the frontier.
    utts = _utts(per=20, ndig=10, nspk=6)
    seqs = psa.read_unit_sequences(sub, pipe, utts)
    sig = psa.measure_unit_predictability(seqs)
    psa.record_perception_quality(sub, sig)
    fr = psa.install_perception_frontier_rule(sub)
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "perception_quality_pending", 1)
    flag = psa.agent_flag_perception(sub, fr["rule_index"])
    rel = psa.get_reliability(sub)
    f_level, f_rank = pma.frontier_rank_from_perception(sub)
    print(f"\n  FIXED frontier: flag='{flag}' reliability='{rel}' "
          f"-> level='{f_level}' rank={f_rank}")

    # the Step-1b synthesis Rule: with a reliable PASS the flag is 'none'/'inconclusive',
    # so the units-gap synthesis Rule does NOT mint a perception artifact.
    pg = psa.install_perception_gap_rule(sub)
    sub.set_attr(root, "perception_gap_pending", 1)
    units_axis = psa.agent_synthesise_perception_gap(sub, pg["rule_index"])
    print(f"  perception/units gap synthesised from the yardstick? "
          f"{'YES (artifact)' if units_axis is not None else 'NO (units pass -> no gap)'}")

    print("\n  --- iter-6 (OLD yardstick, starved 108-utt subset) ---")
    print("    frontier flag      : 'perception' (FALSE — small-sample artifact)")
    print("    frontier rank      : 1.0 (perception_units)")
    print("    GUIDED PICK        : ['improve-unit-predictiveness', 'perception-units']")
    print("                         (a synthesised perception_units artifact)")

    print("\n  --- re-steered (FIXED yardstick) ---")
    base_rows = gp.rank_gaps(sub)
    unguided = base_rows[0] if base_rows else None
    u_level = gp.axis_pipeline_level(unguided["capability_keys"])[0] if unguided else ""
    guided = gp.pick_with_guidance(sub, frontier_rank=f_rank)
    print(f"    frontier rank      : {f_rank} "
          f"({'far-downstream default -> no redirect' if f_rank >= 999 else f_level})")
    print(f"    UNGUIDED PICK      : {list(unguided['capability_keys'][:2])}  "
          f"level='{u_level}'")
    print(f"    GUIDED PICK        : {list(guided['capability_keys'][:2])}  "
          f"level='{guided['pipeline_level']}'")
    print(f"    pick changed by guidance? {guided['pick_changed']}")

    print("\n  ACCEPTANCE (2):")
    landed_perception = guided["pipeline_level"] == "perception_units"
    print(f"    guided pick is perception_units artifact? {landed_perception}  "
          f"(want False)")
    print(f"    guided pick lands on the genuine stage: '{guided['pipeline_level']}'  "
          f"keys={list(guided['capability_keys'][:3])}")
    is_recognition = guided["pipeline_level"] in ("recognition", "segmentation")
    print(f"    -> recognition-stage gap (recognition / chunker->lexicon segmentation)? "
          f"{is_recognition}")


if __name__ == "__main__":
    main()
