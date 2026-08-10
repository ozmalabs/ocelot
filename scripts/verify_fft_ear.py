"""Verify the FFT second ear reaches the signs + that the agent's formant
cues separate the gammatone-confused pairs (fusion, not replacement)."""
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


class P:
    def __init__(s, d): s._json = d


sub = Substrate()
pipe = STTPipeline(STTParams(sample_rate=8000)); pipe.attach(sub)
pipe._ensure_audio_pipeline(sub)
SpeechCortex(sub, lexicon_name="stt", tick_period_ms=99999).install()
sub.set_attr(_root(sub), "resolution", R)
af = fl.gather_files(limit=None)

# --- sanity: a sign carries fft_trajectory of length 1024 + metadata ----
s, fs = fl.load_wav([f for f in af if f[1] == 2][0][0])  # a "two"
pipe.ingest(sub, s); sub.tick(50000)
st = None
for n in sub.nodes("AudioStream"):
    st = n
sg = fl._collect_signs_from_stream(sub, st)
assert sg, "no signs minted"
g0 = sg[0]
a = sub.node(g0)["attrs"]
ft = a.get("fft_trajectory")
print("SANITY: fft_trajectory present:", ft is not None,
      "len:", len(ft) if ft else None,
      "n_frames:", a.get("fft_n_frames"), "n_bins:", a.get("fft_n_bins"),
      "sr:", a.get("fft_sample_rate"))
assert ft is not None and len(ft) == 1024, "fft_trajectory not 8*128=1024"
assert a.get("fft_n_frames") == 8 and a.get("fft_n_bins") == 128
print()

terms = {c: compose_from_spec(R, c) for c in CUE_MENU}


def clipvals(word, n):
    d = fl._DIGITS.index(word); rows = []
    for path, *_ in [f for f in af if f[1] == d][:n]:
        s, fs = fl.load_wav(path); pipe.ingest(sub, s); sub.tick(50000)
        st = None
        for x in sub.nodes("AudioStream"):
            st = x
        sg = fl._collect_signs_from_stream(sub, st) if st else []
        enrich_sign_bands(sub, resolution=R, signs=sg)
        enrich_sign_windows(sub, resolution=R, signs=sg)
        enrich_sign_fft(sub, signs=sg)
        row = {}
        for c, t in terms.items():
            vs = []
            for g in sg:
                try:
                    vs.append(float(sub.evaluate(P(t), {"s": g})))
                except Exception:
                    pass
            row[c] = np.mean(vs) if vs else np.nan
        wb = []
        for g in sg:
            v = [sub.node(g)["attrs"].get(f"band{R}_{i}") for i in range(R)]
            if all(x is not None for x in v):
                wb.append(np.mean(v))
        row["_whole"] = np.mean(wb) if wb else np.nan
        rows.append(row)
    return rows


def fish(a, b):
    a = np.array([x for x in a if x == x]); b = np.array([x for x in b if x == x])
    if len(a) < 2 or len(b) < 2:
        return 0.0
    return abs(a.mean() - b.mean()) / (a.std() + b.std() + 1e-6)


pairs = [("two", "three"), ("three", "zero"), ("nine", "zero"),
         ("one", "zero"), ("four", "five")]
# Deterministic word order (a set's iteration order is nondeterministic and
# the shared lexicon's DTW running-mean is order-sensitive).
words = []
for X, Y in pairs:
    for w in (X, Y):
        if w not in words:
            words.append(w)
cache = {w: clipvals(w, 14) for w in words}

GAMMA = {"onset_tilt", "ending_nasal", "movement", "vowel_height",
         "onset_level", "ending_level"}
FFT = {"f1_formant", "f2_formant", "f2_minus_f1"}

print(f"{'pair':>11} | best GAMMA cue          | F_g  | best FFT cue       | F_fft | best overall (fused)    | winner")
for X, Y in pairs:
    base = fish([r['_whole'] for r in cache[X]], [r['_whole'] for r in cache[Y]])
    scored = [(fish([r[c] for r in cache[X]], [r[c] for r in cache[Y]]), c)
              for c in CUE_MENU]
    g = max([(f, c) for f, c in scored if c in GAMMA], default=(0.0, "-"))
    ff = max([(f, c) for f, c in scored if c in FFT], default=(0.0, "-"))
    overall = max(scored)
    winner = "FFT" if overall[1] in FFT else "GAMMA"
    print(f"{X+'|'+Y:>11} | {g[1]:<22} | {g[0]:4.2f} | {ff[1]:<18} | {ff[0]:5.2f} "
          f"| {overall[1]:<22} ({overall[0]:.2f}) | {winner}")
