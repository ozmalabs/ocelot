"""Empirical cutover: does the GRAPH recogniser (recognize_sign, feature-signature
overlap, agent-owned weights) match the Python NB band-mean recogniser (predict_one)
on real held-out speech? And does the agent's do-contrast self-tuning help?
Honest measurement, no claims — the band-mean base is a DTW match, the graph
recogniser is feature-overlap; they are different algorithms.
"""
import os
import sys
import wave
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(2)

from substrate_rs import Substrate
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
import scripts.fsdd_learner_world as fl
from domains.phonology import classify_signs, learn_word_signatures
from domains.acoustic_resolution import enrich_sign_bands, enrich_sign_windows
from domains.formant_features import compose_peak_features, evaluate_peak_features
from domains.dynamics_features import (compose_transition_features,
                                       exhibit_predicate_features)
from domains.recognition_graph import (mark_words, install_recognition_weights,
                                       recognize_sign, agent_tune_recognition,
                                       measure_recognition)

SC = "/tmp/sc"
WORDS = [w for w in ["yes", "no", "up", "down"] if os.path.isdir(f"{SC}/{w}")]


def load(p):
    w = wave.open(p)
    r = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
         .astype(np.float32) / 32768.0)
    return np.ascontiguousarray((r[::2] if w.getframerate() == 16000 else r)
                                .astype(np.float32))


def feature_all(sub):
    """Re-derive all of the agent's features on every sign (mechanical perception)."""
    enrich_sign_bands(sub)
    enrich_sign_windows(sub, resolution=12)
    classify_signs(sub)
    compose_peak_features(sub)
    evaluate_peak_features(sub)
    compose_transition_features(sub, resolution=12)
    exhibit_predicate_features(sub, "transition")


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()

    data = {w: [(f"{SC}/{w}/{f}", f.split("_")[0])
                for f in sorted(os.listdir(f"{SC}/{w}")) if f.endswith(".wav")]
            for w in WORDS}
    tsp = set()
    for w in WORDS:
        sp = sorted({s for _, s in data[w]})
        tsp |= set(sp[::5])
    train = {w: [p for p, s in data[w] if s not in tsp][:14] for w in WORDS}
    test = {w: [p for p, s in data[w] if s in tsp][:6] for w in WORDS}

    vote_counts = {}
    for w in WORDS:
        for p in train[w]:
            fl.teach_one(sub, pipe, load(p), w, vote_counts)
    feature_all(sub)
    learn_word_signatures(sub, vote_counts)     # signatures over ALL features
    mark_words(sub, WORDS)
    install_recognition_weights(sub)
    print(f"{len(WORDS)} words; trained. chance {100//len(WORDS)}%")

    def graph_predict(samples):
        pipe.ingest(sub, samples)
        sub.tick(50000)
        st = None
        for s in sub.nodes("AudioStream"):
            st = s
        signs = fl._collect_signs_from_stream(sub, st)
        feature_all(sub)
        votes = {}
        for s in signs:
            r = recognize_sign(sub, s)
            if r:
                votes[r] = votes.get(r, 0) + 1
        return max(votes, key=votes.get) if votes else None

    nb_ok = g_ok = n = 0
    for w in WORDS:
        for p in test[w]:
            nb = fl.predict_one(sub, pipe, load(p), vote_counts, phonology_weight=0.0)
            g = graph_predict(load(p))
            n += 1
            nb_ok += (nb == w)
            g_ok += (g == w)
    print(f"\nNB band-mean (predict_one):  {nb_ok}/{n} = {100*nb_ok/n:.0f}%")
    print(f"GRAPH recogniser (recognize_sign, before tuning): {g_ok}/{n} = "
          f"{100*g_ok/n:.0f}%")

    # the agent tunes its own recogniser by do-contrast over the TRAIN signs
    lex = next(iter(sub.nodes("AcousticLexicon")), None)
    tr_signs = []
    if lex:
        for s in sub.neighbours(lex, "has_entry"):
            a = sub.node(s)["attrs"]
            for c in sub.neighbours(s, "denotes"):
                nm = sub.node(c)["attrs"].get("name")
                if nm in WORDS:
                    tr_signs.append((s, nm))
    print(f"\nagent do-contrasts {len(tr_signs)} train signs ...")
    verdicts = agent_tune_recognition(sub, lambda: measure_recognition(sub, tr_signs))
    from collections import Counter
    print("  verdict tally:", dict(Counter(verdicts.values())))

    g2 = sum(1 for w in WORDS for p in test[w] if graph_predict(load(p)) == w)
    print(f"GRAPH recogniser AFTER agent self-tuning: {g2}/{n} = {100*g2/n:.0f}%")


if __name__ == "__main__":
    main()
