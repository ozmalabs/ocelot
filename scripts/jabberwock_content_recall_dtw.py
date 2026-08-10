"""PUSH THE REPRESENTATION FURTHER — DTW RE-RANK: rate-robust non-linear alignment on top of the pyramid recall.

Equal-time chunks (even multi-scale) misalign when phones stretch unevenly across speakers/rates -- the pyramid
plateaus on content top-1/@5. DTW aligns two frame sequences NON-LINEARLY, so it is rate-robust. Full DTW over
every exemplar is too slow, so this is TWO-STAGE, the standard recall->precision design:
  STAGE 1 (recall): the cheap multi-scale pyramid 1-NN surfaces the top-K candidates (content recall@10 ~51%).
  STAGE 2 (precision): DTW re-ranks ONLY those K -- each word is a cochleagram frame sequence (T x bands); the
    candidate distance is the min over its exemplars of DTW(query, exemplar) with a cosine local cost. Re-order.
DTW can only reorder WITHIN the top-K, so it lifts recall@1/@5 (the ORDER) where the priors decode -- exactly the
content top-1/@5 the pyramid plateaued on. Compares pyramid-order vs DTW-reranked-order recall@{1,5,10} over the
top-K. If DTW pulls the true content word up, wire the two-stage scorer into the decode.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u \\
    -m scripts.jabberwock_content_recall_dtw [n_test] [vocab] [bank_utts]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
from domains.filter_settings import cochleagram
from domains.speech_world import SpeechWorld
from scripts.librispeech_wer import gather_pairs, load_flac
from scripts.abs_language_decode import acoustic_logp
from scripts.jabberwock_prosodic_decode import STOP, pyramid_features

FS = 16000
CAP = 8
TOPK = 20            # stage-1 recall set DTW re-ranks
T = 24               # cochleagram frames per word (resampled); DTW aligns the residual non-linear timing
KS = [1, 5, 10]


def frames(seg):
    """Word -> (T, bands) cochleagram frame sequence, CMVN'd (per-band mean+var removal over voiced frames -- the
    same speaker normalisation the pyramid front end applies) so DTW matches PHONETIC content not speaker timbre,
    then each frame L2-normalised (cosine-ready)."""
    M = np.asarray(cochleagram(np.asarray(seg, dtype=np.float64), FS, 50.0, 80.0, T), dtype=np.float64)
    e = M.sum(1); emax = float(e.max()) if e.size else 0.0
    voiced = (e >= 0.25 * emax) if emax > 1e-12 else np.ones(len(M), bool)
    if int(voiced.sum()) < 2:
        voiced = np.ones(len(M), bool)
    mu = M[voiced].mean(0); sd = M[voiced].std(0) + 1e-6
    M = (M - mu) / sd                                       # CMVN: speaker offset + dynamic-range removed
    return M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)


def dtw(A, B):
    """DTW distance between two L2-normed frame sequences, cosine local cost, length-normalised."""
    C = 1.0 - A @ B.T
    ta, tb = C.shape
    D = np.full((ta + 1, tb + 1), np.inf); D[0, 0] = 0.0
    for i in range(1, ta + 1):
        Ci = C[i - 1]
        Di, Dprev = D[i], D[i - 1]
        for j in range(1, tb + 1):
            Di[j] = Ci[j - 1] + min(Dprev[j], Di[j - 1], Dprev[j - 1])
    return D[ta, tb] / (ta + tb)


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    vocab_size = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    bank_utts = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    print("=" * 100)
    print("DTW RE-RANK — rate-robust non-linear alignment on the pyramid recall set (two-stage recall->precision)")
    print("=" * 100)

    sw = SpeechWorld(srs.Substrate(), whisper_model="base.en")
    by_spk = {}
    for (path, sp, ch, ut, tr) in gather_pairs(limit=None):
        by_spk.setdefault(sp, []).append((path, tr))
    spks = sorted(by_spk)
    train_spk, test_spk = spks[:max(1, len(spks) - 2)], spks[max(1, len(spks) - 2):]

    print("\n  whisper-segmenting train utterances...", flush=True)
    word_segs = {}
    budget = 0
    for sp in train_spk:
        for (path, _tr) in by_spk[sp][:10]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if w and seg.size >= int(0.04 * fs):
                    word_segs.setdefault(w, []).append(seg)
            budget += 1
            if budget >= bank_utts:
                break
        if budget >= bank_utts:
            break

    vocab = [w for (w, _c) in Counter({w: len(s) for w, s in word_segs.items()}).most_common(vocab_size)
             if len(word_segs[w]) >= 3]
    cands = sorted(vocab)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})

    print(f"  featuring train ({len(vocab)} words, {CAP}/word): pyramid + frame sequences...", flush=True)
    banked = [(w, pyramid_features(s, seg)) for w in vocab for seg in word_segs[w][:CAP]]
    train_frames = {w: [frames(seg) for seg in word_segs[w][:CAP]] for w in vocab}

    print(f"  whisper-segmenting {n_test} test utts + featuring...", flush=True)
    test = []
    n_utt = 0
    for sp in test_spk:
        for (path, _tr) in by_spk[sp]:
            x, fs = load_flac(path); x = np.asarray(x, dtype=np.float64)
            got = 0
            for (w, t0, t1) in sw.transcribe_lang_timed(x, fs, "en"):
                w = "".join(c for c in w.lower() if c.isalpha())
                seg = x[int(t0 * fs):int(t1 * fs)]
                if w not in vocab or seg.size < int(0.04 * fs):
                    continue
                test.append((w, pyramid_features(s, seg), frames(seg)))
                got += 1
            if got >= 3:
                n_utt += 1
            if n_utt >= n_test:
                break
        if n_utt >= n_test:
            break
    nc = sum(t[0] not in STOP for t in test); nf = sum(t[0] in STOP for t in test)
    print(f"  {nc} content, {nf} function test tokens; DTW re-ranks top-{TOPK}\n")

    pyr_ranks = {"c": [], "f": []}
    dtw_ranks = {"c": [], "f": []}
    for truth, pchan, qframes in test:
        lo = acoustic_logp(pchan, banked, cands)
        order = sorted(cands, key=lambda w: -lo[w])
        topk = order[:TOPK]
        # stage 2: DTW re-rank the top-K by min-over-exemplars DTW distance
        ddist = {w: min(dtw(qframes, ef) for ef in train_frames[w]) for w in topk}
        reranked = sorted(topk, key=lambda w: ddist[w])
        prank = (order.index(truth) + 1) if truth in order else 10 ** 9
        drank = (reranked.index(truth) + 1) if truth in reranked else (10 ** 9 if truth not in order else order.index(truth) + 1)
        key = "f" if truth in STOP else "c"
        pyr_ranks[key].append(prank); dtw_ranks[key].append(drank)

    def rr(rk, k):
        return 100.0 * np.mean([r <= k for r in rk]) if rk else 0.0

    for title, key in (("CONTENT", "c"), ("FUNCTION", "f")):
        print(f"  {title} recall@K  (within top-{TOPK}):")
        print(f"    {'scorer':>16}" + "".join(f"{'@'+str(k):>9}" for k in KS))
        print(f"    {'pyramid':>16}" + "".join(f"{rr(pyr_ranks[key],k):>8.1f}%" for k in KS))
        print(f"    {'pyramid+DTW':>16}" + "".join(f"{rr(dtw_ranks[key],k):>8.1f}%" for k in KS))
        print()

    pc1, dc1 = rr(pyr_ranks["c"], 1), rr(dtw_ranks["c"], 1)
    pc5, dc5 = rr(pyr_ranks["c"], 5), rr(dtw_ranks["c"], 5)
    print("=" * 100)
    print(f"  CONTENT recall@1: pyramid {pc1:.0f}% -> +DTW {dc1:.0f}%   |   @5: {pc5:.0f}% -> {dc5:.0f}%")
    if dc1 - pc1 >= 3 or dc5 - pc5 >= 3:
        print(f"  DTW RE-RANK WINS: rate-robust alignment pulls the true content word UP within the recall set")
        print(f"  (@1 {dc1-pc1:+.0f}, @5 {dc5-pc5:+.0f} pts) -- non-linear timing was the residual. Wire the two-stage")
        print("  scorer (pyramid recall -> DTW re-rank) into the decode acoustic emission.")
    else:
        print(f"  DTW re-rank does NOT clearly help (@1 {dc1-pc1:+.0f}, @5 {dc5-pc5:+.0f}): the cochleagram-frame DTW is")
        print("  redundant with the multi-scale pyramid (both capture the same sequence). The lever is elsewhere")
        print("  (better per-frame features, or phone-aligned landmarks, not just realignment).")
    print("=" * 100)


if __name__ == "__main__":
    main()
