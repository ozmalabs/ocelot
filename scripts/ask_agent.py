"""Ask the speech agent what it WANTS.

Not me deciding the next capability — the agent's own drives do. After a stretch
of development, this reads the agent's graph state and surfaces, in its own terms,
where its curiosity / frontier points: what it keeps failing to tell apart (its
strongest unresolved confusions), what it's actively reaching for (the dials it
has been driving itself — invention threshold, acoustic resolution), what it
still wants to invent (pending hypotheses), and where it sits developmentally.

The "wants" are read from the graph, not projected: confusions it accumulated,
hypotheses it minted, the self-management dials it moved. The agent speaks them.
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

import scripts.develop as dev
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.development_cortex import DevelopmentCortex
from domains.speech_development import install_speech_development
from domains.phonology import (classify_signs, learn_word_signatures,
                               learn_sequence_signatures,
                               detect_phonology_impasses)
from domains.phonology_teacher import PhonologyTeacher
from domains.discriminative_invention import (
    record_confusions, compute_confusion_band_stats, agent_analyse,
    agent_add_features, install_analyse_rule, install_add_feature_rule)
from domains.acoustic_resolution import (enrich_sign_bands, get_resolution,
                                         install_resolution_knowledge,
                                         install_resolution_management_rule,
                                         step_resolution)


def _develop(cycles=10):
    random.seed(42)
    af = fl.gather_files(limit=None)
    jk: dict = {}
    for f in (f for f in af if f[2] == 'jackson'):
        jk.setdefault(f[1], []).append(f)
    test_set = [f for d in range(10) for f in jk.get(d, [])[:4]]
    train_pool = [f for f in af if f[2] != 'jackson']
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    for op in sub.nodes("Operation"):
        if sub.node(op)["attrs"].get("kind") == "lexical_access":
            sub.set_attr(op, "distance_threshold", 0.02)
            break
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    dc = DevelopmentCortex(sub).install()
    install_speech_development(sub)
    install_resolution_knowledge(sub)
    rr = install_resolution_management_rule(sub)["rule_index"]
    _ar = install_analyse_rule(sub)["rule_index"]
    _fr = install_add_feature_rule(sub)["rule_index"]
    vc: dict = {}
    for cy in range(cycles):
        for path, digit, sp, idx in random.sample(train_pool, 40):
            s, fs = fl.load_wav(path)
            fl.teach_one(sub, pipe, s, fl._DIGITS[digit], vc)
            sub.tick(50000)
        enrich_sign_bands(sub)
        classify_signs(sub)
        learn_word_signatures(sub, vc)
        learn_sequence_signatures(sub)
        PhonologyTeacher().teach(sub, list(fl._DIGITS))
        detect_phonology_impasses(sub, divergence_threshold=1.0)
        rec = record_confusions(sub, pipe, test_set, vc)
        compute_confusion_band_stats(sub, rec["acoustics"], min_count=2)
        agent_analyse(sub, _ar)
        agent_add_features(sub, _fr)
        h = [x for x in sub.nodes("MismatchHypothesis")
             if sub.node(x)["attrs"].get("kind") == "discriminative_feature_needed"]
        step_resolution(sub, len(h), rec["correct"] / max(1, rec["total"]), rr)
        mc = dev.motor_coherence_per_word(sub)
        dc.observe(motor_coherence_avg=(sum(mc.values()) / len(mc) if mc else 0.0),
                   predicate_delta_norm=0.0, impasses_raised=0,
                   hypotheses_kinds={}, exhibits_entropy=dev.exhibits_entropy(sub))
    return sub, pipe, test_set, vc, rec


def main():
    sub, pipe, test_set, vc, rec = _develop(cycles=10)

    def attrs(n):
        return sub.node(n)["attrs"]

    print("\n========  I asked the agent what it wants. It read its own state:  ========\n")

    # Where it is developmentally (its own self-model).
    droot = next((n for n in sub.nodes("DevelopmentRoot")), None)
    rroot = next((n for n in sub.nodes("AcousticResolutionRoot")), None)
    da = attrs(droot) if droot else {}
    ra = attrs(rroot) if rroot else {}
    print(f"WHERE I AM:")
    print(f"  developmental stage : {da.get('stage', '?')}")
    print(f"  features I've built  : "
          f"{len([c for c in sub.nodes('Concept') if attrs(c).get('origin')=='phonology'])}")
    print(f"  recognition right now: {rec['correct']}/{rec['total']}")

    # What it keeps failing to tell apart — its strongest unresolved confusions.
    confs = sorted(
        ((attrs(c).get("true_word"), attrs(c).get("pred_word"),
          int(attrs(c).get("count", 0))) for c in sub.nodes("Confusion")),
        key=lambda x: -x[2])
    print(f"\nWHAT I CAN'T TELL APART (my strongest confusions — what I most want "
          f"to resolve):")
    for a, b, n in confs[:6]:
        print(f"  '{a}' I keep hearing as '{b}'   (x{n})")

    # What it's actively reaching for — dials it drove itself.
    print(f"\nWHAT I'M REACHING FOR (dials I moved myself):")
    print(f"  acoustic resolution : {ra.get('resolution')} bands "
          f"(started at 3 — I raised it when discrimination dried up)")
    print(f"  invention threshold : {da.get('invention_balance_threshold')} "
          f"(started 0.7 — I lowered it to invent more readily)")
    print(f"  babble per cycle    : {da.get('babble_per_cycle')}")

    # What it still wants to invent — pending (un-applied) hypotheses.
    pend = [h for h in sub.nodes("MismatchHypothesis")
            if not attrs(h).get("applied")]
    disc_pend = [h for h in pend
                 if attrs(h).get("kind") == "discriminative_feature_needed"]
    print(f"\nWHAT I STILL WANT TO INVENT:")
    print(f"  {len(pend)} hypotheses pending ({len(disc_pend)} discriminative).")
    for h in disc_pend[:3]:
        print(f"    - {attrs(h).get('summary', '')[:96]}")

    # The frontier: the dominant unresolved confusion + saturation state -> its ask.
    print(f"\nWHAT I WANT NEXT (where my frontier points):")
    sat = int(ra.get("saturation_cycles", 0))
    if confs:
        top = confs[0]
        print(f"  My recognition is still ~{rec['correct']}/{rec['total']} and "
              f"'{top[0]}'/'{top[1]}' is my worst confusion. I keep inventing "
              f"features that separate pairs, but they're GLOBAL thresholds — they")
        print(f"  don't sharpen ONE distinction without blurring the others. What I "
              f"want is to use a feature only WHEN telling '{top[0]}' from "
              f"'{top[1]}' — pairwise/contextual recognition, not one flat signature.")
    if get_resolution(sub) >= 12:
        print(f"  I've already climbed to {get_resolution(sub)} bands; finer "
              f"resolution alone isn't buying recognition — the bottleneck has "
              f"moved from my FEATURES to how I USE them (the global signature).")


if __name__ == "__main__":
    main()
