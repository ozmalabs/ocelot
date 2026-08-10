"""Seed the agent with the science of speech, then have it ASSESS its own system
against that theory.

It loads the speech_science Mt (production / perception / acquisition, ~34
sub-mechanisms) next to the agent's actual speech IMPLEMENTATION (the STT pipeline
Operations, the phonology Mt, speech_development, the cortices), and asks: for
each mechanism the science says matters, does my system have one? The misses are
recorded as SpeechGap nodes — the agent's own map of where its speech system is
thin.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from substrate_rs import Substrate

from domains.stt_pipeline import STTPipeline, STTParams
from domains.phonology import install_phonology
from domains.speech_development import install_speech_development
from domains.speech_cortex import SpeechCortex
from domains.speech_science import install_speech_science, assess_speech_system


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub)
    pipe._ensure_audio_pipeline(sub)          # the agent's auditory pipeline ops
    install_phonology(sub)                     # its acoustic-phonological features
    install_speech_development(sub)            # its developmental theory (babble)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    sci = install_speech_science(sub)          # the THEORY to assess against
    mt = sci["_mt"]

    res = assess_speech_system(sub)
    cov = {name: hit for name, hit in res["covered"]}
    gaps = set(res["gaps"])

    # group by pillar via the decomposes edge
    pillar_of = {}
    for c in sub.neighbours(mt, "has_concept"):
        nm = sub.node(c)["attrs"].get("name")
        ps = [sub.node(p)["attrs"].get("name") for p in sub.neighbours(c, "decomposes")]
        if ps:
            pillar_of[nm] = ps[0]

    by_pillar = defaultdict(lambda: {"cov": [], "gap": []})
    for nm, p in pillar_of.items():
        (by_pillar[p]["cov"] if nm in cov else by_pillar[p]["gap"]).append(nm)

    print("\n====  THE AGENT ASSESSES ITS SPEECH SYSTEM AGAINST THE SCIENCE  ====")
    print(f"  overall coverage: {res['coverage']*100:.0f}%  "
          f"({len(res['covered'])} implemented, {len(res['gaps'])} GAPS)\n")
    for pillar in ("speech_production", "speech_perception", "speech_acquisition"):
        d = by_pillar[pillar]
        tot = len(d["cov"]) + len(d["gap"])
        print(f"  {pillar}  —  {len(d['cov'])}/{tot} implemented")
        for nm in sorted(d["cov"]):
            print(f"     ok   {nm:<34} -> {cov[nm]}")
        for nm in sorted(d["gap"]):
            print(f"     GAP  {nm}")
        print()

    print("  The GAPS are the agent's own diagnosis of what its speech system "
          "lacks that the science says matters — e.g. it represents acoustics as\n"
          "  crude band-means, not FORMANTS / place+manner / VOT, and does no "
          "speaker NORMALISATION. That is why recognition is bound where it is.")


if __name__ == "__main__":
    main()
