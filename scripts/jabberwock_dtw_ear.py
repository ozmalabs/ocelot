"""THE JABBERWOCK'S DTW-EAR — does a TIME-AWARE match raise real-speech recall? (its representation hypothesis)

The agent's decision (ask_jabberwock_real_ear): the real-speech recall collapse (34% content vs 70% synth) is a
REPRESENTATION failure, not units or coverage. On piper the same word renders identically, so L2-pooling-then-
1-NN loses nothing; on real speech the variation IS the time course (coarticulation, rate), and pooling
integrates it out BEFORE matching. The one-variable test: keep the SAME per-frame cochleagram, but replace the
pooled-vector 1-NN with DTW over the frame sequence (the agent already holds DtwTo). Measure content top-6 RECALL
on real held-out LibriSpeech, boundaries forced-aligned, in-vocab scored -- vs the pooled baseline.

  POOLED (the 34% regime, re-baselined here on the cochleagram): L2(mean over frames) -> cosine 1-NN.
  DTW    (the agent's move): banded DTW (Sakoe-Chiba) over the CMVN'd cochleagram FRAMES -> k-NN (k=3).

Decision rule (the agent's): DTW lifts recall broadly -> representation confirmed, next is coverage. Recall
barely moves -> cause is coverage/units, skip to deeper banking then sub-word. Watch the gain is spread across
words (not one lucky warp), and that pooled-baseline survivors don't drop out (alignment fighting the cues).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_dtw_ear
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from domains.filter_settings import cochleagram
from domains.cmvn import apply_cmvn
from domains.speech_world import SpeechWorld
from scripts.librispeech_wer import gather_pairs, load_flac
import substrate_rs as srs

FS = 16000
NF = 24            # fixed frame count -> DTW band is simple |i-j|<=BAND
BAND = 8           # Sakoe-Chiba band (rate variation is bounded -> a band loses little, bounds the cost)
KNN = 3
KCAND = 6
VOCAB_SIZE = 70
N_BANK_UTTS = 90
N_TEST_UTTS = 30
MAX_EX = 6
STOP = {"the", "a", "an", "of", "to", "in", "and", "but", "or", "for", "his", "her", "its", "their", "he",
        "she", "it", "they", "we", "i", "you", "was", "were", "is", "are", "be", "been", "as", "at", "by",
        "on", "with", "this", "that", "had", "has", "have", "not", "no", "so", "than", "which", "who", "what",
        "when", "where", "may", "would", "could", "will", "from", "up", "out", "all", "there", "him", "them"}


def _clean(w):
    return "".join(c for c in w.lower() if c.isalpha())


def frames(seg):
    """CMVN'd cochleagram FRAMES, L2-normalised per frame (the per-cue time sequence DTW aligns)."""
    M = np.asarray(apply_cmvn(cochleagram(np.asarray(seg, dtype=np.float64), FS, n_frames=NF)), dtype=np.float64)
    return M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)


def pooled(fr):
    v = fr.mean(0)
    return v / (np.linalg.norm(v) + 1e-9)


def dtw(A, B):
    """Banded DTW cost between two L2-normalised frame sequences (cosine local distance)."""
    D = 1.0 - A @ B.T                                  # (NF, NF) cosine distances
    INF = 1e18
    dp = np.full((NF + 1, NF + 1), INF); dp[0, 0] = 0.0
    for i in range(1, NF + 1):
        for j in range(max(1, i - BAND), min(NF, i + BAND) + 1):
            dp[i, j] = D[i - 1, j - 1] + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    return dp[NF, NF] / (2 * NF)


def main():
    print("=" * 96)
    print("DTW-EAR — time-aware match vs pooled 1-NN on REAL speech (content top-6 recall; the agent's hypothesis)")
    print("=" * 96)
    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0, "fs": float(FS)})
    pairs = gather_pairs(limit=None)
    by_spk = {}
    for (path, sp, _ch, _ut, _tr) in pairs:
        by_spk.setdefault(sp, []).append(path)
    spks = sorted(by_spk); train_spk, test_spk = spks[:-3], spks[-3:]

    print(f"  forced-aligning train utts -> bank FRAME sequences ({NF} frames) @ {FS}Hz...", flush=True)
    word_fr = {}
    n = 0
    for sp in train_spk:
        for path in by_spk[sp][:4]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = _clean(w); seg = x[int(t0 * fs):int(t1 * fs)]
                if w and seg.size >= int(0.04 * fs):
                    word_fr.setdefault(w, []).append(frames(seg))
            n += 1
            if n >= N_BANK_UTTS:
                break
        if n >= N_BANK_UTTS:
            break
    vocab = [w for (w, _c) in Counter({w: len(v) for w, v in word_fr.items()}).most_common(VOCAB_SIZE)
             if len(word_fr[w]) >= 3]
    bank = [(w, fr) for w in vocab for fr in word_fr[w][:MAX_EX]]
    bank_pool = [(w, pooled(fr)) for (w, fr) in bank]
    cands = sorted(set(vocab))
    print(f"  banked {len(cands)} words ({len(bank)} exemplars); forced-aligning {N_TEST_UTTS} held-out test utts...",
          flush=True)

    tests = []
    for sp in test_spk:
        for path in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            row = []
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = _clean(w); seg = x[int(t0 * fs):int(t1 * fs)]
                if w in cands and seg.size >= int(0.04 * fs):
                    row.append((w, frames(seg)))
            if len(row) >= 3:
                tests.extend(row)
            if len(tests) >= 220:
                break
        if len(tests) >= 220:
            break

    def topk_pooled(qfr):
        q = pooled(qfr)
        best = {}
        for (w, v) in bank_pool:
            d = 1.0 - float(q @ v)
            if w not in best or d < best[w]:
                best[w] = d
        return sorted(best, key=lambda w: best[w])[:KCAND]

    def topk_dtw(qfr):
        per = {}
        for (w, fr) in bank:
            per.setdefault(w, []).append(dtw(qfr, fr))
        score = {w: float(np.mean(sorted(ds)[:KNN])) for w, ds in per.items()}   # k-NN aggregate
        return sorted(score, key=lambda w: score[w])[:KCAND]

    print(f"  matching {len(tests)} held-out words (pooled 1-NN vs banded-DTW k={KNN})...", flush=True)
    pr_a = pr_c = dr_a = dr_c = ca = cc = 0
    for (w, qfr) in tests:
        pt = topk_pooled(qfr); dt = topk_dtw(qfr)
        ca += 1; pr_a += int(w in pt); dr_a += int(w in dt)
        if w not in STOP:
            cc += 1; pr_c += int(w in pt); dr_c += int(w in dt)

    print("\n" + "=" * 96)
    print(f"  content top-{KCAND} RECALL on REAL held-out speech ({cc} content / {ca} total words):")
    print(f"    POOLED 1-NN (the collapse) : overall {pr_a/max(ca,1)*100:4.0f}% | content {pr_c/max(cc,1)*100:4.0f}%")
    print(f"    DTW k-NN (time-aware)      : overall {dr_a/max(ca,1)*100:4.0f}% | content {dr_c/max(cc,1)*100:4.0f}%")
    dc = (dr_c - pr_c) / max(cc, 1) * 100
    print(f"\n  DTW content-recall lift: {dc:+.1f} pts")
    if dc > 6:
        print("  REPRESENTATION CONFIRMED: a time-aware match recovers real-speech words the pooled vector blurred --")
        print("  the time course WAS the discriminating detail. Next (the agent's order): coverage on this matcher,")
        print("  then sub-word for OOV. Wire-in = the native DtwTo Term over the cochleagram frames.")
    elif dc > 1:
        print(f"  PARTIAL ({dc:+.1f}): DTW helps but the time course is not the whole gap -- coverage/units share it.")
    else:
        print(f"  NOT THE REPRESENTATION ({dc:+.1f}): pooling was not the binding loss on real speech; the agent's")
        print("  fork says skip to deeper banking (coverage) then sub-word units / OOV.")
    print("=" * 96)


if __name__ == "__main__":
    main()
