"""The agent invents features OUTSIDE its seeded set: it GENERATES novel Term-trees
from its primitives and SELECTS the discriminative ones — no seeded pattern, no LLM.
"""
import os
import sys
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
random.seed(1)

from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import enrich_sign_bands, _root
from domains.feature_generator import discover_features


def _render(d):
    if hasattr(d, "to_dict"):
        d = d.to_dict()
    ty = d["type"]
    if ty == "Attr":
        return d["key"]
    if ty == "Lit":
        return str(d["value"])
    if ty == "Var":
        return d["name"]
    if ty in ("Gt", "Lt", "Div", "Minus"):
        op = {"Gt": ">", "Lt": "<", "Div": "/", "Minus": "-"}[ty]
        return f"({_render(d['a'])} {op} {_render(d['b'])})"
    if ty in ("Plus", "Max", "Min"):
        items = list(d["items"])
        if ty == "Plus":
            return "(" + " + ".join(_render(i) for i in items) + ")"
        return f"{ty.lower()}(" + ", ".join(_render(i) for i in items) + ")"
    return ty


def main():
    af = fl.gather_files(limit=None)
    train = random.sample([f for f in af if f[2] != "jackson"], 120)
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    sub.set_attr(_root(sub), "resolution", 12)
    vc = {}
    print(f"training on {len(train)} samples...")
    for path, d, sp, idx in train:
        s, fs = fl.load_wav(path)
        fl.teach_one(sub, pipe, s, fl._DIGITS[d], vc)
        sub.tick(50000)
    enrich_sign_bands(sub)

    by_word = {}
    for s in sub.nodes("AcousticSign"):
        ws = [sub.node(w)["attrs"].get("name") for w in sub.neighbours(s, "denotes")]
        if ws:
            by_word.setdefault(ws[0], []).append(s)
    print("signs per word:", {k: len(v) for k, v in by_word.items()})

    bands = [f"band12_{i}" for i in range(12)]
    top = discover_features(sub, by_word, bands, n=800, keep=8, seed=7)

    print("\n=== the agent GENERATED novel features from its primitives and SELECTED")
    print("    the discriminative ones (structures NO seed contained, NO LLM wrote):\n")
    for disc, term, rates in top:
        best = max(rates, key=rates.get)
        worst = min(rates, key=rates.get)
        print(f"  spread={disc:.2f}   {_render(term)}")
        print(f"            fires {rates[best]:.0%} on '{best}'  vs  "
              f"{rates[worst]:.0%} on '{worst}'")
    print("\n  These are ratios / differences / nested resonances — compositions the")
    print("  seed never named. Generation (DSL grammar) + selection (discrimination)")
    print("  = ideas outside the seeded set.")


if __name__ == "__main__":
    main()
