"""Iterative teach→adjust loop test — does the autopoietic loop
converge?

Trains the substrate on FSDD, installs expert phonology
signatures, then loops detect→investigate→analyse→act→re-classify
N rounds. Measures per-round:
  - threshold values per predicate
  - total impasses raised
  - hypotheses minted + acted
  - recognition accuracy on held-out test set

Demonstrates whether predicate threshold retuning converges
(predicates progressively align with teaching) or oscillates.
"""
from __future__ import annotations

import argparse
import time

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

from substrate_rs import Substrate

import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams, _node_sort_key
from domains.speech_cortex import SpeechCortex
from domains.phonology import (
    classify_signs, learn_word_signatures,
    detect_phonology_impasses,
    investigate_phonology_impasses,
    analyse_persistent_mismatches,
    apply_top_hypotheses,
    _reset_detect_gate,
)
from domains.phonology_teacher import PhonologyTeacher


def thresholds(sub) -> dict:
    out = {}
    for c in sub.nodes("Concept"):
        a = sub.node(c)["attrs"]
        if a.get("origin") == "phonology":
            out[a.get("name")] = a.get("threshold")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_limit", type=int, default=500)
    parser.add_argument("--test_speakers", nargs='+',
                        default=['jackson'])
    parser.add_argument("--rounds", type=int, default=8)
    parser.add_argument("--apply_min_score", type=float,
                          default=0.7)
    parser.add_argument("--phonology_weight", type=float, default=0.0)
    args = parser.parse_args()

    files = fl.gather_files(limit=args.train_limit)
    test_set = set(args.test_speakers)
    train = [f for f in files if f[2] not in test_set]
    test = [f for f in files if f[2] in test_set]
    print(f"train: {len(train)}  test: {len(test)}")

    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    for op in sub.nodes("Operation"):
        if sub.node(op)["attrs"].get("kind") == "lexical_access":
            sub.set_attr(op, "distance_threshold", 0.02)
            break

    cortex = SpeechCortex(sub, lexicon_name="stt",
                              tick_period_ms=99999).install()

    # === train (cortex tick period set high so it doesn't tick
    # during training; we drive the chain manually post-train) ===
    vote_counts = {}
    t0 = time.time()
    for path, digit, sp, idx in train:
        samples, fs = fl.load_wav(path)
        word = fl._DIGITS[digit]
        fl.teach_one(sub, pipe, samples, word, vote_counts)
        sub.tick(50000)
    print(f"training: {time.time() - t0:.1f}s  "
          f"signs={len(pipe.lexicon(sub))}")

    classify_signs(sub)
    learn_word_signatures(sub, vote_counts)
    PhonologyTeacher().teach(sub, list(fl._DIGITS))

    initial_thr = thresholds(sub)
    print(f"\ninitial thresholds: {initial_thr}\n")

    def measure_accuracy() -> int:
        correct = 0
        for path, digit, sp, idx in test:
            samples, fs = fl.load_wav(path)
            ref = fl._DIGITS[digit]
            hyp = fl.predict_one(sub, pipe, samples, vote_counts,
                                       phonology_weight=args.phonology_weight)
            if hyp == ref:
                correct += 1
        return correct

    initial_acc = measure_accuracy()
    print(f"round 0 (post-teach, pre-adjust): "
          f"acc={initial_acc}/{len(test)}")

    # === iterate teach→adjust ===
    for r in range(1, args.rounds + 1):
        _reset_detect_gate(sub)
        imps = detect_phonology_impasses(sub,
                                              divergence_threshold=1.0)
        inv = investigate_phonology_impasses(sub,
                                                   learning_rate=0.3)
        hyps = analyse_persistent_mismatches(sub,
                                                   min_impasses_per_pair=3)
        applied = apply_top_hypotheses(
            sub, min_score=args.apply_min_score)
        classify_signs(sub)
        acc = measure_accuracy()
        thr = thresholds(sub)
        # Print compact per-round summary.
        thr_str = "  ".join(
            f"{k[:3]}={float(v):.3f}"
            for k, v in thr.items() if v is not None)
        applied_str = "  ".join(
            f"{k.split('_')[0][:4]}={v}"
            for k, v in applied['applied'].items())
        print(f"round {r}: imps={len(imps):3d} hyps={len(hyps):3d} "
              f"applied={{{applied_str}}} acc={acc}/{len(test)} "
              f"thr=[{thr_str}]")


if __name__ == "__main__":
    main()
