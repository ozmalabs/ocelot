"""Ask the speech agent — through its OWN machinery — what it needs re: perception.

Four steps, each reporting the agent's RAW machinery output:

  1. ASK — seed speech_science, develop a bit, run assess_speech_system. Does the
     agent's own assessment NAME a perception/segmentation/unit gap, or only
     recognition-side things?
  2. SIGNAL — give it the missing signal: measure the predictability/compression of
     its OWN unit-sequences on continuous speech, attach as graph-resident state.
  3. PROPOSE — with that signal in state, run the agent's self-specification
     (agent_specify_frontend / agent_specify_primitive) and the meta-monitor over
     the new unit_segmentation process; report what it specifies VERBATIM.
  4. FLAG — fire the graph-resident flagging rule; can the agent now flag
     perception as its frontier from its own state?
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scripts.sentence_learning as sl
import scripts.ask_agent as aa
from domains.speech_science import (install_speech_science, assess_speech_system,
                                    reason_about_gap)
from domains.runtime_design import (agent_specify_primitive,
                                    agent_specify_frontend)
from domains.perception_self_assessment import (
    assess_perception, install_perception_frontier_rule, agent_flag_perception,
    get_frontier)
from domains.meta_monitor import (install_meta_issue_rule,
                                  install_meta_response_rule, agent_check_meta,
                                  get_meta_issues)


def _rule(line=""):
    print("=" * 72)
    if line:
        print(line)
        print("=" * 72)


def main():
    n_utts = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    n_speakers = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    # ---- set the agent up + develop it (its own dev loop) ----
    print("Developing the agent (its own dev loop, 6 cycles)...", flush=True)
    sub, pipe, test_set, vc, rec = aa._develop(cycles=6)
    print(f"  developed. recognition right now: {rec['correct']}/{rec['total']}",
          flush=True)
    install_speech_science(sub)

    # ============================================================
    _rule("STEP 1 — ASK: the agent assesses its own speech system (VERBATIM)")
    res = assess_speech_system(sub)
    print(f"coverage: {res['coverage']*100:.0f}%  "
          f"({len(res['covered'])} implemented, {len(res['gaps'])} gaps)\n")
    print("COVERED (concept -> implementing element):")
    for name, hit in sorted(res["covered"]):
        print(f"  ok   {name:<36} -> {hit}")
    print("\nGAPS (its own diagnosis of what's missing):")
    for name in sorted(res["gaps"]):
        print(f"  GAP  {name}")
    perception_words = ("segment", "unit", "invarian", "categor", "distribut",
                        "statistical", "normal")
    perc_gaps = [g for g in res["gaps"]
                 if any(w in g.lower() for w in perception_words)]
    seg_covered = [c for c, h in res["covered"] if "segment" in c.lower()]
    print(f"\n-> perception/segmentation-ish GAPS it named: {perc_gaps}")
    print(f"-> segmentation is marked COVERED as: {seg_covered}  "
          f"(keyword-matched, NOT a quality check)")

    # ============================================================
    _rule("STEP 2 — SIGNAL: measure predictability of the agent's OWN units")
    print(f"Ingesting {n_utts} LibriSpeech utterances through the agent's "
          f"perception...", flush=True)
    pairs = sl.gather_pairs()
    speakers = sorted(set(p[1] for p in pairs))[:n_speakers]
    sel = [p for p in pairs if p[1] in speakers]
    import random
    random.seed(1)
    random.shuffle(sel)
    sel = sel[:n_utts]

    def utt_iter():
        for path, sp, ch, ut, tr in sel:
            try:
                samples, _ = sl.load_flac_8k(path)
            except Exception:
                continue
            yield samples

    signal = assess_perception(sub, pipe, list(utt_iter()), meta=True)
    print("\nThe agent's self-signal on its OWN perceived units:")
    print(f"  utterances ingested      : {signal['n_utterances']}")
    print(f"  total unit tokens        : {signal['n_tokens']}")
    print(f"  distinct units (lexicon) : {signal['lexicon_size']}")
    print(f"  recurrence               : {signal['recurrence']:.3f}  "
          f"(fraction of tokens reusing an existing unit)")
    print(f"  next-unit predict top-1  : {signal['predict_top1']:.3f}  "
          f"(chance {signal['predict_chance']:.4f})")
    print(f"  predict / chance         : {signal['predict_over_chance']:.2f}x  "
          f"(the MISLEADING number — inflated by recurrence)")
    print(f"  frequency baseline       : {signal['predict_freq_baseline']:.3f}  "
          f"(predict the globally most-frequent unit, NO context)")
    print(f"  predict / frequency      : {signal['predict_over_freq']:.2f}x  "
          f"(the HONEST number — context beyond raw frequency)")
    print(f"  info gain H(next)-H(.|cur): {signal['info_gain_bits']:.3f} bits")
    print(f"  compression ratio        : {signal['compress_ratio']:.3f}  "
          f"(1.0 = no structure / bag of noise; lower = better units)")
    print(f"\n-> {signal['predict_over_chance']:.1f}x chance LOOKS good, but the "
          f"bigram beats the units' own frequency baseline only "
          f"{signal['predict_over_freq']:.2f}x — the frequency-artifact trap.")

    # ============================================================
    _rule("STEP 3 — PROPOSE: the agent's self-specification (VERBATIM)")
    print("(a) agent_specify_frontend — the agent reasons about its perception:")
    band_centres = []
    for op in sub.nodes("Operation"):
        a = sub.node(op)["attrs"]
        if a.get("kind") in ("cochlea", "gammatone") and a.get("band_centres_hz"):
            band_centres = list(a.get("band_centres_hz"))
            break
    if not band_centres:
        # default log-spaced layout the pipeline ships with (80-7500 Hz)
        import numpy as np
        band_centres = list(np.logspace(np.log10(80), np.log10(7500), 32))
    fe = agent_specify_frontend(band_centres, n_patches=25)
    for k, v in fe.items():
        print(f"    {k}: {v}")

    print("\n(b) agent_specify_primitive — the primitive its language lacks:")
    sp = agent_specify_primitive(sub)
    for k, v in sp.items():
        print(f"    {k}: {v}")

    print("\n(c) meta-monitor over the unit_segmentation process "
          "(payoff = perception, not recognition):")
    install_meta_issue_rule(sub)
    install_meta_response_rule(sub)
    # one more report so the window has > 1 sample (spinning needs a window)
    from domains.perception_self_assessment import report_to_meta_monitor
    report_to_meta_monitor(sub, signal)
    issues = get_meta_issues(sub)
    note = issues or "none yet (needs a full window of cycles to flag spinning)"
    print(f"    meta-issues on perception process: {note}")

    print("\n(d) reason_about_gap on a perception gap it named "
          "(its derivation over its own science):")
    for g in ("lack_of_invariance", "distributional_learning_of_categories",
              "speaker_normalization"):
        r = reason_about_gap(sub, g)
        if r.get("hypothesis"):
            print(f"    [{g}] from rule '{r.get('rule')}':")
            print(f"      {r['hypothesis']}")
            break

    # ============================================================
    _rule("STEP 4 — FLAG: can the agent flag perception from its OWN state?")
    fr = install_perception_frontier_rule(sub)
    # the rule was installed AFTER record_perception_quality, so re-mark pending
    root = next(n for n in sub.nodes("PerceptionSelfRoot"))
    sub.set_attr(root, "perception_quality_pending", 1)
    frontier = agent_flag_perception(sub, fr["rule_index"])
    ra = sub.node(root)["attrs"]
    print(f"PerceptionSelfRoot state the rule read:")
    print(f"  predict_over_freq        : {ra.get('predict_over_freq'):.3f}  "
          f"(floor {ra.get('predict_over_freq_floor')})")
    print(f"  compress_ratio           : {ra.get('compress_ratio'):.3f}  "
          f"(ceiling {ra.get('compress_ratio_ceiling')})")
    print(f"\n>>> the agent's own verdict — frontier = '{frontier}'")
    print(f">>> get_frontier(sub) = '{get_frontier(sub)}'")
    if frontier == "perception":
        print(">>> the agent now FLAGS perception as its frontier from its own "
              "graph state, with no external label.")
    else:
        print(">>> the agent does NOT flag perception — its units were good "
              "enough by its own thresholds.")


if __name__ == "__main__":
    main()
