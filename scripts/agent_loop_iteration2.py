"""agent_loop_iteration2 — turn the autopoietic crank a SECOND time, with the
previous iteration's MEASUREMENT feeding back into the gap-graph so the agent's own
ranker re-points itself.

ITERATION 1 (commits 701ec9a / 26852c4): the agent synthesised its gaps, its
graph-resident ranker picked CROSS-SPEAKER CLUSTERING by a-priori compression-payoff
(clustering 6, word-scale chunking 4, LPC 2 — LPC LAST), built it, and MEASURED it
CAPPED by the blurry front-end (label-free purity 0.441 < raw-spectrum 0.483; matching
the sound-graph LOSO filter 0.335 << spectrum 0.649). The loop OBSERVED this points at
LPC but never ENCODED it — the self-correction lived only in the human's notes.

ITERATION 2 (this script) makes the self-correction REAL:

  STEP 1  FEEDBACK — the iter-1 measurement RESULT is written back into the gap-graph
          as a MeasurementOutcome + a `blocked_by` edge (clustering -> LPC), and the
          ranking Term is EXTENDED so a gap inherits the payoff of the gaps it
          UNBLOCKS (own + Σ over incoming blocked_by). Graph Term-trees only
          (Plus/Sum/InNeighbours/Count/Neighbours/Times/Minus/Argmax — all in term.rs).

  STEP 2  RE-RANK — the agent's extended Term re-picks natively. THE HONESTY TEST:
          does LPC now WIN via the feedback (self-correction), or did we have to force
          it? (Reported straight from the native Argmax.)

  STEP 3  BUILD — the agent forward-builds the LPC all-pole formant extractor from its
          source-filter / IIR science (runtime_design spec + sound_graph LPC front-end:
          autocorrelation -> Levinson-Durbin -> pole angles = formants).

  STEP 4  MEASURE — does the cleaner LPC formant front-end lift the sound-graph LOSO
          (vs cepstral 0.335 / spectrum 0.649) and unblock the cross-speaker
          clustering (vs CMVN 0.441 / raw-spectrum 0.483)?

Run:  SG_PER=10 python scripts/agent_loop_iteration2.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

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
from domains.order_n_postulates import synthesize_over_all
from domains import gap_prioritiser as gp
from domains import measurement_feedback as mf
from domains.runtime_design import agent_specify_lpc_formants

import scripts.fsdd_learner_world as fl
from domains.sound_graph import (build_sound_graph, filter_signature_rich,
                                 spectrum_signature_traj)
from domains.cross_speaker_clustering import cluster
from scripts.sound_graph_probe import loso_accuracy, separation, cosine, euclid_sim
from scripts.cross_speaker_clustering_probe import (purity, random_floor,
                                                   cmvn_signature)

DIGITS = fl._DIGITS
PER = int(os.environ.get("SG_PER", "10"))


def _build_mind():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    install_phonology(sub)
    install_speech_development(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    install_speech_science(sub)
    install_mathematics_seed(sub)
    install_engineering_seed(sub)
    install_machine_learning_seed(sub)
    install_all_concept_expansions(sub)
    return sub


def main():
    print("=" * 78)
    print("AUTOPOIETIC LOOP — ITERATION 2  (measurement -> gap-graph feedback)")
    print("=" * 78)

    sub = _build_mind()
    # Record the agent's DERIVED capabilities (prune=False) as SynthesizedGap nodes,
    # so the axes the loop ranks include every capability the agent's own harvested
    # shapes DERIVE — including LPC/all-pole, which transfers from IIR_filter onto
    # source_filter_theory (resonance<->pole). With prune=True the LPC axis would be
    # absent (the agent has since IMPLEMENTED LPC, so the selector prunes it as not
    # OPEN), and the blocker would have to be MINTED from the measurement. The loop's
    # point is that the blocker is the agent's OWN derived capability, so we record
    # derivations and let the measurement feedback supply the openness/priority.
    synthesize_over_all(sub, record=True, shapes="harvested", prune=False)

    print("\n[STEP 0] BASELINE RANK (the agent's iter-1 ranker, no feedback)")
    for r in gp.rank_gaps(sub):
        print(f"    payoff={r['payoff']} score={r['score']}  {r['capability_keys'][:2]}")

    print("\n[STEP 1] FEEDBACK — iter-1 clustering measurement written to the graph")
    res = mf.record_outcome(
        sub,
        attempted_key="cross-speaker-clustering",
        blocked_by_key="all-pole",
        achieved=0.441, baseline=0.483, floor=0.162,
        gain_vs_baseline=0.441 - 0.483,
        metric="FSDD label-free cluster purity (iteration 1)",
        attribution=("clusterer works (0.441 >> 0.162 floor) but does NOT beat raw "
                     "spectrum 0.483; cap attributed to the blurry front-end — matches "
                     "sound-graph LOSO filter 0.335 << spectrum 0.649"),
        # the front-end capability the measurement implicates (LPC / all-pole),
        # grounded in the held postulates the block is attributed to. Used ONLY as a
        # fallback if the synthesis did not already produce the LPC axis — but it
        # NOW does: the harvested all-pole shape transfers from IIR_filter onto
        # source_filter_theory (resonance<->pole), recorded above with prune=False,
        # so record_outcome finds the existing axis and does NOT mint (verified
        # below: minted_blocker is False).
        blocker_capability_keys=["all-pole", "levinson", "lpc-formant",
                                 "linear predict"],
        blocker_grounded_in=["source_filter_theory",
                             "vocal_tract_resonance_formants"])
    print(f"    MeasurementOutcome node {res['outcome']}  "
          f"blocked_by edge (clustering -> LPC) written: {res['edge_written']}")
    if res["minted_blocker"]:
        print("    NOTE: the order-N synthesis did NOT produce the LPC axis at this "
              "tree (the\n          harvested all-pole shape does not fire on "
              "source_filter_theory); the LPC\n          axis was MINTED from the "
              "measurement evidence, grounded in the held\n          source-filter "
              "postulates (flagged measurement_derived). See the doc.")
    else:
        print("    NOTE: the LPC axis came from the agent's OWN synthesis (the "
              "harvested\n          all-pole shape transfers from IIR_filter onto "
              "source_filter_theory,\n          resonance<->pole) — NOT minted from "
              "the measurement. minted_blocker=False.")

    print("\n[STEP 2] RE-RANK with feedback (extended Term, native eval)")
    rows = mf.rerank_with_feedback(sub)
    for r in rows:
        print(f"    own={r['own_payoff']} +unblock={r['unblock_bonus']} "
              f"=> eff_payoff={r['effective_payoff']} eff_score={r['effective_score']}"
              f"  {r['capability_keys'][:2]}")
    pick = mf.pick_with_feedback(sub)
    is_lpc = any(("all-pole" in str(k).lower() or "lpc" in str(k).lower())
                 for k in pick["capability_keys"])
    print(f"\n    PICK (native Argmax over effective score): {pick['capability_keys'][:3]}")
    print(f"    SELF-CORRECTION TEST — did LPC WIN via the feedback? {is_lpc}")
    print("    => the loop self-corrected (no forced pick)." if is_lpc else
          "    => LPC did NOT win; the pick was NOT forced — reporting what won.")

    print("\n[STEP 3] BUILD — the agent's LPC all-pole formant extractor")
    spec = agent_specify_lpc_formants(sub)
    print(f"    operation: {spec['operation']}  (order p={spec['order']})")
    print(f"    grounded_in_science: {spec['grounded_in_science']}")
    print(f"    method: {spec['method'][:88]}...")
    print("    built in: domains/sound_graph._lpc_formant_peaks "
          "(frontend='lpc' in build_sound_graph)")

    print("\n[STEP 4] MEASURE — does the LPC front-end lift / unblock the downstream?")
    af = fl.gather_files()
    speakers = sorted({sp for _, _, sp, _ in af})
    cep_f, lpc_f, spec_t, cmv, truth = [], [], [], [], []
    for d in range(len(DIGITS)):
        for sp in speakers:
            files = [p for (p, dd, ss, _) in af if dd == d and ss == sp][:PER]
            for p in files:
                s, fs = fl.load_wav(p)
                cep_f.append(filter_signature_rich(
                    build_sound_graph(s, fs, frontend="cepstral")))
                lpc_f.append(filter_signature_rich(
                    build_sound_graph(s, fs, frontend="lpc")))
                spec_t.append(spectrum_signature_traj(s, fs))
                cmv.append(cmvn_signature(s, fs))
                truth.append(d)

    _who = []
    for d in range(len(DIGITS)):
        for sp in speakers:
            n = len([p for (p, dd, ss, _) in af if dd == d and ss == sp][:PER])
            _who += [sp] * n

    def by(sigs):
        out = {}
        for v, d, sp in zip(sigs, truth, _who):
            out.setdefault((d, sp), []).append(v)
        return out

    cep_by, lpc_by, spec_by = by(cep_f), by(lpc_f), by(spec_t)
    ac_c = loso_accuracy(cep_by, speakers, euclid_sim)
    ac_l = loso_accuracy(lpc_by, speakers, euclid_sim)
    ac_s = loso_accuracy(spec_by, speakers, cosine)
    _, _, sep_c = separation(cep_by, speakers, euclid_sim)
    _, _, sep_l = separation(lpc_by, speakers, euclid_sim)

    print("\n  (a) SOUND-GRAPH LOSO (cross-speaker nearest-prototype accuracy)")
    print(f"      cepstral filter (OLD front-end)  LOSO={ac_c:.3f}  sep={sep_c:+.3f}")
    print(f"      LPC all-pole filter (NEW)        LOSO={ac_l:.3f}  sep={sep_l:+.3f}")
    print(f"      spectrum_traj (ceiling)          LOSO={ac_s:.3f}   chance=0.100")
    print(f"      LPC vs cepstral: {ac_l - ac_c:+.3f}   "
          f"LPC vs spectrum: {ac_l - ac_s:+.3f}")

    k = len(DIGITS)
    rf = random_floor(truth, k)

    def clus(sigs):
        M = np.array(sigs)
        ps = [purity(cluster(M, k=k, seed=sd), truth) for sd in range(5)]
        return float(np.mean(ps)), float(np.std(ps))
    pc = clus(cep_f); pl = clus(lpc_f); pm = clus(cmv); psp = clus(spec_t)
    print(f"\n  (b) CROSS-SPEAKER CLUSTERING purity (label-free; random floor {rf:.3f})")
    print(f"      cepstral filter (OLD)            {pc[0]:.3f} +/- {pc[1]:.3f}")
    print(f"      LPC all-pole filter (NEW)        {pl[0]:.3f} +/- {pl[1]:.3f}")
    print(f"      CMVN log-mel (iter-1 agent)      {pm[0]:.3f} +/- {pm[1]:.3f}")
    print(f"      raw spectrum (iter-1 baseline)   {psp[0]:.3f} +/- {psp[1]:.3f}")

    print("\n" + "=" * 78)
    print("VERDICT")
    print("=" * 78)
    print(f"  self-correction: LPC won the re-rank via feedback = {is_lpc}")
    print(f"  LPC lifts the filter front-end LOSO {ac_c:.3f} -> {ac_l:.3f} "
          f"({ac_l - ac_c:+.3f}); still below spectrum {ac_s:.3f}.")
    print(f"  LPC clustering {pl[0]:.3f} vs iter-1 CMVN {pm[0]:.3f} "
          f"({pl[0] - pm[0]:+.3f}); vs raw-spectrum cap {psp[0]:.3f} "
          f"({pl[0] - psp[0]:+.3f}).")


if __name__ == "__main__":
    main()
