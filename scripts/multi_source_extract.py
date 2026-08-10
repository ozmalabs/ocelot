"""Multi-source speech extraction — more hours, more speakers, for the rare-content-word data wall.

Streams several clear-speech children's shows off jellyfin, whisper-segments+labels each, and caches
a combined (train, test) set of (word, raw 8kHz segment) pairs. More hours -> more exemplars of rare
content words; more shows -> speaker variety (what the talker-invariant shape + local learner need).
"""
from __future__ import annotations

import os
import pickle
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
from domains.speech_world import SpeechWorld, FS
from scripts.source_world import SourceWorld

CACHE = "/tmp/multi_speech_segs2.pkl"
# (name substring, train minutes, test minutes) — narration-heavy, content-rich, clear single speakers
SPECS = [("sesame", 22.0, 3.0), ("ask the storybots", 18.0, 3.0), ("absurd planet", 18.0, 3.0),
         ("animal kingdom", 18.0, 3.0), ("secrets of the zoo: tampa", 16.0, 3.0)]


def _grab(sw, src, t0, t1):
    out = []
    t = t0
    while t < t1:
        a = sw.play(src, t, t + 30.0)
        if isinstance(a, tuple):
            a = a[0]
        a = np.asarray(a, dtype=np.float64)
        if a.size < FS:
            break
        for (w, s0, s1) in sw.transcribe_lang_timed(a, FS, "en"):
            seg = a[int(s0 * FS):int(s1 * FS)]
            if seg.size >= int(0.04 * FS):
                out.append((w, np.asarray(seg, dtype=np.float32)))
        t += 30.0
    return out


def multi_extract():
    if os.path.exists(CACHE):
        d = pickle.load(open(CACHE, "rb"))
        return d["train"], d["test"]
    sw = SpeechWorld(srs.Substrate(), source_world=SourceWorld(include_jellyfin=True))
    srcs = sw.sources()
    train, test = [], []
    for sub, trm, tem in SPECS:
        src = next((x for x in srcs if sub in str(x.get("name", "")).lower()), None)
        if src is None:
            print(f"  source '{sub}' not found, skipping")
            continue
        print(f"  streaming '{src['name']}' ({trm} min train + {tem} test)...", flush=True)
        train += _grab(sw, src, 0.0, trm * 60)
        test += _grab(sw, src, trm * 60 + 30, trm * 60 + 30 + tem * 60)
        print(f"    so far: {len(train)} train, {len(test)} test tokens", flush=True)
    pickle.dump({"train": train, "test": test}, open(CACHE, "wb"))
    return train, test


if __name__ == "__main__":
    tr, te = multi_extract()
    print(f"DONE: {len(tr)} train / {len(te)} test tokens cached -> {CACHE}")
