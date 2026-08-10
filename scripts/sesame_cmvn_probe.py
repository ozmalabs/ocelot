"""SESAME CMVN PROBE — does the agent's GRAPH-NATIVE CMVN lift real-speech recognition?

The Sesame diagnosis located the frontier: in-vocab recognition caps at ~23% even for well-heard
words — the exemplar ear can't hold word identity across speakers. The agent's own composed
speaker-normalisation faculty (domains/cmvn.py — a graph Term-tree, NOT numpy: per-band mean+var
removal over time) is the lever. This probe streams Sesame ONCE (cached), then measures held-out
in-vocab recognition with the agent's CMVN cue OFF vs ON (a graph-resident EarConfig flag), bucketed
by training frequency, to see whether speaker-normalising the cochleagram lifts the 23% ceiling.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.sesame_cmvn_probe [train_min]
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
import domains.self_directed_speech_world as SDW
from domains.speech_world import SpeechWorld, FS
from domains.speech_world_recognizer import GraphLexicon, WordHat
from scripts.source_world import SourceWorld

SEP = "=" * 86
CACHE = "/tmp/sesame_cmvn_segs.pkl"


def extract(train_min):
    """Stream Sesame once, whisper-segment, return (train, test) lists of (word, raw_seg)."""
    if os.path.exists(CACHE):
        d = pickle.load(open(CACHE, "rb"))
        if d.get("train_min") == train_min:
            print(f"  using cached segments ({len(d['train'])} train, {len(d['test'])} test)")
            return d["train"], d["test"]
    sw = SpeechWorld(srs.Substrate(), source_world=SourceWorld(include_jellyfin=True))
    src = next((x for x in sw.sources() if "sesame" in str(x.get("name", "")).lower()), None)
    if src is None:
        raise SystemExit("Sesame Street not found on jellyfin.")

    def grab(t0, t1):
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

    print(f"  streaming Sesame Street (train {train_min} min + test 2 min)...")
    train = grab(0.0, train_min * 60)
    test = grab(train_min * 60 + 30, train_min * 60 + 150)
    pickle.dump({"train_min": train_min, "train": train, "test": test}, open(CACHE, "wb"))
    return train, test


def run(train, test, cmvn):
    s = srs.Substrate()
    if cmvn:
        s.add_node("EarConfig", {"cmvn": 1.0})       # the agent's graph-native CMVN cue ON
    lex = GraphLexicon(s)
    hat = WordHat()
    from collections import Counter
    for (w, seg) in train:
        lex.bank(SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS), w, source="ses")
    wcount = Counter(w for (w, _v) in lex.banked())
    vocab = set(wcount)
    buckets = {"1": [0, 0], "2": [0, 0], "3-5": [0, 0], "6+": [0, 0]}

    def bk(c):
        return "1" if c == 1 else "2" if c == 2 else "3-5" if c <= 5 else "6+"
    c = t = 0
    for (w, seg) in test:
        if w not in vocab:
            continue
        t += 1
        ok = hat.recognise(SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS), lex) == w
        c += int(ok)
        b = buckets[bk(wcount[w])]
        b[1] += 1; b[0] += int(ok)
    return (c / t if t else 0.0), buckets, len(vocab)


def main():
    train_min = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    print(SEP)
    print("SESAME CMVN PROBE — does the agent's graph-native speaker-normalisation lift the ceiling?")
    print(SEP)
    train, test = extract(train_min)
    print(f"  {len(train)} train tokens, {len(test)} test tokens\n")
    for cmvn in (False, True):
        acc, buckets, nv = run(train, test, cmvn)
        tag = "CMVN ON (graph-native)" if cmvn else "CMVN OFF (raw)"
        by = "  ".join(f"{k}x:{b[0]}/{b[1]}={b[0]/b[1]*100:.0f}%" for k, b in buckets.items() if b[1])
        print(f"  {tag:24} in-vocab recall {acc*100:.0f}%   [{by}]")
    print(f"\n{SEP}")
    print("  If CMVN ON lifts the 6+x bucket, the agent's own graph-native speaker normalisation is")
    print("  the right lever for real open-vocab speech; if not, the exemplar ear needs deeper work.")
    print(SEP)


if __name__ == "__main__":
    main()
