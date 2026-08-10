"""Acceptance test for the fused two-ear cue menu.

Runs the agent's OWN cue menu (gammatone band cues + frequency-sharp
FFT formant cues) on the gammatone-confused pairs and reports the best
cue + Fisher per pair. Success: for two|three (and ideally three|zero,
one|zero) the agent picks an FFT formant cue with Fisher far above the
gammatone's; for nine|zero a gammatone cue still wins (ears complementary
-> fusion, not replacement).
"""
import os, sys; sys.path.insert(0, os.getcwd())
import numpy as np
from substrate_rs import Substrate
import scripts.fsdd_learner_world as fl
from domains.stt_pipeline import STTPipeline, STTParams
from domains.speech_cortex import SpeechCortex
from domains.acoustic_resolution import (enrich_sign_bands, enrich_sign_windows,
                                         enrich_sign_fft, _root)
from domains.hint_grounding import compose_from_spec, CUE_MENU

R = 12
N_PER_WORD = 14

GAMMATONE_CUES = ["onset_tilt", "ending_nasal", "movement", "vowel_height",
                  "onset_level", "ending_level"]
FFT_CUES = ["f1_formant", "f2_formant", "f2_minus_f1"]

PAIRS = [("two", "three"), ("three", "zero"), ("nine", "zero"),
         ("one", "zero"), ("four", "five")]


class _P:
    __slots__ = ("_json",)
    def __init__(self, d): self._json = d


def _fisher(a, b):
    a = np.array([x for x in a if x == x]); b = np.array([x for x in b if x == x])
    if len(a) < 2 or len(b) < 2:
        return 0.0
    return abs(a.mean() - b.mean()) / (a.std() + b.std() + 1e-6)


def main():
    sub = Substrate()
    pipe = STTPipeline(STTParams(sample_rate=8000))
    pipe.attach(sub); pipe._ensure_audio_pipeline(sub)
    SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
    sub.set_attr(_root(sub), "resolution", R)
    af = fl.gather_files(limit=None)
    terms = {c: compose_from_spec(R, c) for c in CUE_MENU}

    # word -> {cue: [vals]} aggregated across that word's clips.
    byword = {}

    def collect(word):
        if word in byword:
            return
        d = fl._DIGITS.index(word)
        files = [f for f in af if f[1] == d][:N_PER_WORD]
        bag = {c: [] for c in CUE_MENU}
        for path, *_ in files:
            s, fs = fl.load_wav(path)
            pipe.ingest(sub, s)
            sub.tick(50000)
            st = None
            for n in sub.nodes("AudioStream"):
                st = n
            sg = fl._collect_signs_from_stream(sub, st) if st else []
            enrich_sign_bands(sub, resolution=R, signs=sg)
            enrich_sign_windows(sub, resolution=R, signs=sg)
            enrich_sign_fft(sub, signs=sg)
            for g in sg:
                for c, t in terms.items():
                    try:
                        bag[c].append(float(sub.evaluate(_P(t), {"s": g})))
                    except Exception:
                        pass
        byword[word] = bag

    for X, Y in PAIRS:
        collect(X); collect(Y)

    # best cue overall, best gammatone-only cue, best fft-only cue.
    print(f"{'pair':>11} | {'best gammatone':>22} | {'best FFT formant':>22} | winner")
    print("-" * 84)
    for X, Y in PAIRS:
        gbest = max(((c, _fisher(byword[X][c], byword[Y][c])) for c in GAMMATONE_CUES),
                    key=lambda kv: kv[1])
        fbest = max(((c, _fisher(byword[X][c], byword[Y][c])) for c in FFT_CUES),
                    key=lambda kv: kv[1])
        winner = "FFT ear" if fbest[1] > gbest[1] else "gammatone ear"
        pair = f"{X}|{Y}"
        print(f"{pair:>11} | {gbest[0]:>14} {gbest[1]:6.2f} | "
              f"{fbest[0]:>14} {fbest[1]:6.2f} | {winner} "
              f"(fused best={max(gbest[1], fbest[1]):.2f})")


if __name__ == "__main__":
    main()
