"""THE JABBERWOCK SPEEDS UP ITS OWN RECOGNITION — effect-gated lexicon consolidation.

The speed/resource benchmark showed 73% of the agent's time is brute-force 1-NN over its exemplar
bank, which grows linearly — so a big lexicon (the ~3000 exemplars that reached whisper-parity WER)
makes it SLOWER than whisper. The agent fixes this by COMPRESSING ITS OWN KNOWLEDGE: it consolidates
the many exemplars of each word into K representative PROTOTYPES (per-word k-means centroids), which
cuts the 1-NN comparisons by the same factor. Effect-gated (the cue-authoring pattern): try each K,
measure end-to-end speed AND WER, and KEEP the smallest bank (fastest) whose WER stays within
tolerance — no accuracy thrown away for speed.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_speeds_recognition
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world import SpeechWorld
from domains.speech_world_recognizer import GraphLexicon, WordHat, N_CHANNELS
from scripts.wer_test import LANGS, edit_distance, test_utterances

SEP = "=" * 88
TRAIN = (30, 42, 54, 66, 78, 90)
TEST = (36, 60, 84)
K_REPERTOIRE = (1, 2, 3, 4, 6)
WER_TOLERANCE = 0.015           # keep the fastest bank whose WER is within +1.5pt of full


def _kmeans(X, k, iters=12):
    """Tiny k-means++ (dependency-free). Returns a list of member-index lists per cluster."""
    n = len(X)
    if n <= k:
        return [[i] for i in range(n)]
    idx = [0]
    while len(idx) < k:
        d = np.min(np.stack([((X - X[j]) ** 2).sum(1) for j in idx]), axis=0)
        idx.append(int(np.argmax(d)))
    cent = X[idx].copy()
    assign = np.zeros(n, dtype=int)
    for _ in range(iters):
        assign = np.argmin(np.stack([((X - c) ** 2).sum(1) for c in cent], axis=1), axis=1)
        for c in range(k):
            m = X[assign == c]
            if len(m):
                cent[c] = m.mean(0)
    return [list(np.where(assign == c)[0]) for c in range(k)]


def consolidate(banked, k):
    """Per word, cluster its exemplars into k prototypes; each prototype's channel-i vector is the
    (re-normalised) mean of its cluster's channel-i vectors. The agent compressing its own bank."""
    byword = {}
    for (w, vecs) in banked:
        byword.setdefault(w, []).append(vecs)
    protos = []
    for w, exs in byword.items():
        cat = np.stack([np.concatenate(v) for v in exs])      # joint feature space for clustering
        for members in _kmeans(cat, k):
            if not members:
                continue
            pv = []
            for ci in range(N_CHANNELS):
                m = np.mean([exs[i][ci] for i in members], axis=0)
                n = np.linalg.norm(m)
                pv.append(m / n if n > 1e-9 else m)
            protos.append((w, pv))
    return protos


def bank_into_fresh(protos):
    cs = srs.Substrate()
    clex = GraphLexicon(cs)
    for (w, vecs) in protos:
        clex.bank(vecs, w, source="proto")
    return clex


def time_and_wer(sw, s, lex, hat, clips):
    """End-to-end: segment (main substrate) -> features -> recognise against `lex`. Returns
    (ms/utterance, WER). lex may be the full bank or a consolidated prototype bank."""
    # warm
    for (lo, hi) in sw.segment(clips[0][1], clips[0][2]):
        seg = np.asarray(clips[0][1][lo:hi], dtype=np.float64)
        if seg.size >= int(0.04 * clips[0][2]):
            hat.recognise(SDW.feature_channels(s, seg, clips[0][2]), lex)
            break
    eo = en = 0
    t0 = time.perf_counter()
    for lang, clip, fs in clips:
        seq_words = clip_words[(lang, id(clip))]
        hyp = []
        for (lo, hi) in sw.segment(clip, fs):
            seg = np.asarray(clip[lo:hi], dtype=np.float64)
            if seg.size < int(0.04 * fs):
                continue
            hyp.append(hat.recognise(SDW.feature_channels(s, seg, fs), lex) or "<?>")
        e, n = edit_distance(seq_words, hyp)
        eo += e; en += n
    ms = (time.perf_counter() - t0) / len(clips) * 1000
    return ms, eo / en


clip_words = {}


def main():
    print(SEP)
    print("THE JABBERWOCK SPEEDS UP ITS OWN RECOGNITION — effect-gated lexicon consolidation.")
    print(SEP)
    s = srs.Substrate()
    sw = SpeechWorld(s)
    lex = GraphLexicon(s)
    hat = WordHat()
    s.add_node("Operation", {"kind": "sonority_valley", "smoothing_ms": 30.0,
                             "min_separation_ms": 80.0, "depth_threshold": 0.30,
                             "silence_floor": 0.03, "snap_center": 0.001})
    for pitch in TRAIN:
        for _r in range(3):
            for lang, (voice, words) in LANGS.items():
                clip, fs, bounds = sw.synth_concat(words, {"variant": voice, "pitch": pitch,
                                                           "rate": 175})
                for (lo, hi) in sw.segment(clip, fs):
                    seg = np.asarray(clip[lo:hi], dtype=np.float64)
                    if seg.size < int(0.04 * fs):
                        continue
                    a, b = lo / fs, hi / fs
                    bw, bo = None, 0.0
                    for (w, t0, t1) in bounds:
                        ov = max(0.0, min(b, t1) - max(a, t0))
                        if ov > bo:
                            bo, bw = ov, w
                    if bw:
                        lex.bank(SDW.feature_channels(s, seg, fs), bw, source="x")
    banked = lex.banked()

    clips = []
    for lang, (voice, words) in LANGS.items():
        for pitch in TEST:
            for seq in test_utterances(words):
                out = sw.synth_concat(seq, {"variant": voice, "pitch": pitch, "rate": 175})
                if out is None:
                    continue
                clip, fs, _b = out
                clips.append((lang, clip, fs))
                clip_words[(lang, id(clip))] = seq

    base_ms, base_wer = time_and_wer(sw, s, lex, hat, clips)
    print(f"  INTROSPECT: '73% of my time is 1-NN over {len(banked)} exemplars — it scales with my")
    print(f"              bank. I can keep fewer PROTOTYPES per word if accuracy holds.'\n")
    print(f"  baseline (full bank): {len(banked)} exemplars  ->  {base_ms:.1f} ms/utterance, "
          f"WER {base_wer*100:.1f}%\n")

    print(f"  OPTIMISING — consolidate to K prototypes/word, measure speed AND WER:")
    trials = {}
    for k in K_REPERTOIRE:
        clex = bank_into_fresh(consolidate(banked, k))
        ms, wer = time_and_wer(sw, s, clex, hat, clips)
        trials[k] = (clex.size(), ms, wer)
        ok = wer <= base_wer + WER_TOLERANCE
        print(f"    K={k}: {clex.size():3d} exemplars  {ms:6.1f} ms/utt  WER {wer*100:4.1f}%  "
              f"({base_ms/ms:.1f}x faster) {'OK' if ok else 'too lossy'}")
    # KEEP the fastest (smallest) bank whose WER is within tolerance of the full bank.
    ok_ks = [k for k in K_REPERTOIRE if trials[k][2] <= base_wer + WER_TOLERANCE]
    chosen = min(ok_ks, key=lambda k: trials[k][1]) if ok_ks else None
    print(f"\n{SEP}")
    if chosen is not None:
        nx, ms, wer = trials[chosen]
        print(f"  PASS — the jabberwock CONSOLIDATED its lexicon itself (K={chosen}): "
              f"{len(banked)} -> {nx} exemplars,")
        print(f"  {base_ms:.1f} -> {ms:.1f} ms/utterance ({base_ms/ms:.1f}x faster), WER "
              f"{base_wer*100:.1f}% -> {wer*100:.1f}% (within tolerance). Speed that no longer scales")
        print(f"  with everything it has ever heard — it keeps only what discriminates.")
    else:
        print("  No consolidation stayed within WER tolerance — the agent kept its full bank.")
    print(SEP)
    return 0 if chosen is not None else 1


if __name__ == "__main__":
    sys.exit(main())
