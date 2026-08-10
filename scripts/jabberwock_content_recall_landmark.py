"""PUSH THE REPRESENTATION FURTHER — LANDMARK-ALIGNED chunks (the canonical-parse move, in the multi-cue framework).

DTW realignment failed (it threw away the multi-cue richness). Landmark chunks are the OTHER alignment idea, and
they stay in the channel/1-NN framework: instead of EQUAL-time chunk boundaries, place them at acoustic LANDMARKS
(onset / spectral-flux peaks = phone/syllable onsets), so the same phone lands in the same chunk across speakers
and rates -- the speech analogue of the glyph canonical-parse (re-segment at structural corners). Each word still
becomes C chunks x cues channels, scored by the same exclusion-product 1-NN, so the multi-cue richness is kept.
The boundaries are forced to exactly C-1 (the C-1 strongest onsets, padded with equal-time if too few).

Compares content/function recall@K for EQUAL chunk-4 vs LANDMARK chunk-4 (the clean A/B: does phonetic alignment
beat equal-time?), with the equal pyramid as reference. If landmark alignment lifts content recall, build a
landmark pyramid and wire it in; if not, the representation has plateaued and alignment is not the residual.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u \\
    -m scripts.jabberwock_content_recall_landmark [n_test] [vocab] [bank_utts]
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
import domains.self_directed_speech_world as SDW
from domains.speech_world import SpeechWorld
from scripts.librispeech_wer import gather_pairs, load_flac
from scripts.abs_language_decode import acoustic_logp
from scripts.jabberwock_prosodic_decode import STOP
from scripts.jabberwock_ear_ignition import onsets

FS = 16000
CAP = 8
KS = [1, 5, 10, 20]


def equal_chunks(s, seg, c):
    seg = np.asarray(seg, dtype=np.float64); n = len(seg); out = []
    for i in range(c):
        a, b = int(i * n / c), int((i + 1) * n / c)
        sub = seg[a:b]
        if sub.size < int(0.02 * FS):
            sub = np.pad(sub, (0, int(0.02 * FS) - sub.size))
        out.extend(SDW.feature_channels(s, sub, FS))
    return out


def landmark_bounds(seg, c):
    """Exactly C segments: boundaries at the C-1 strongest interior onsets (padded with equal-time if too few)."""
    n = len(seg); lo, hi = int(0.03 * FS), n - int(0.03 * FS)
    try:
        ts, stress, _M, _hop = onsets(np.asarray(seg, dtype=np.float64))
    except Exception:
        ts, stress = [], []
    cand = sorted(((int(ts[i] * FS), float(stress[i])) for i in range(len(ts))
                   if lo < int(ts[i] * FS) < hi), key=lambda z: -z[1])
    cuts = sorted(p for p, _ in cand[:c - 1])
    eq = [int(k * n / c) for k in range(1, c)]
    ei = 0
    while len(cuts) < c - 1 and ei < len(eq):
        e = eq[ei]; ei += 1
        if all(abs(e - cc) > int(0.015 * FS) for cc in cuts):
            cuts.append(e)
    cuts = sorted(cuts)
    if len(cuts) < c - 1:
        cuts = sorted(eq)                                  # degenerate -> equal-time
    return [0] + cuts[:c - 1] + [n]


def landmark_chunks(s, seg, c):
    seg = np.asarray(seg, dtype=np.float64); b = landmark_bounds(seg, c); out = []
    for i in range(c):
        sub = seg[b[i]:b[i + 1]]
        if sub.size < int(0.02 * FS):
            sub = np.pad(sub, (0, int(0.02 * FS) - sub.size))
        out.extend(SDW.feature_channels(s, sub, FS))
    return out


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    vocab_size = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    bank_utts = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    print("=" * 100)
    print("LANDMARK-ALIGNED chunks — equal-time chunk-4 vs onset-aligned chunk-4 (does phonetic alignment win?)")
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

    REPS = {
        "equal-c4":    lambda seg: equal_chunks(s, seg, 4),
        "landmark-c4": lambda seg: landmark_chunks(s, seg, 4),
        "pyr-equal":   lambda seg: SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS)
                                   + equal_chunks(s, seg, 2) + equal_chunks(s, seg, 4),
    }

    print(f"  featuring train ({len(vocab)} words, {CAP}/word) for {len(REPS)} representations...", flush=True)
    banked = {name: [(w, fn(seg)) for w in vocab for seg in word_segs[w][:CAP]] for name, fn in REPS.items()}

    print(f"  whisper-segmenting {n_test} test utts + featuring...", flush=True)
    test = {name: [] for name in REPS}
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
                for name, fn in REPS.items():
                    test[name].append((w, fn(seg)))
                got += 1
            if got >= 3:
                n_utt += 1
            if n_utt >= n_test:
                break
        if n_utt >= n_test:
            break
    nc = sum(t[0] not in STOP for t in test["equal-c4"]); nf = sum(t[0] in STOP for t in test["equal-c4"])
    print(f"  {nc} content, {nf} function test tokens\n")

    def ranks(name):
        cr, fr = [], []
        for truth, channels in test[name]:
            lo = acoustic_logp(channels, banked[name], cands)
            order = sorted(cands, key=lambda w: -lo[w])
            rank = order.index(truth) + 1 if truth in order else 10 ** 9
            (cr if truth not in STOP else fr).append(rank)
        return cr, fr

    def rr(rk, k):
        return 100.0 * np.mean([r <= k for r in rk]) if rk else 0.0

    results = {name: ranks(name) for name in REPS}
    for title, idx in (("CONTENT", 0), ("FUNCTION", 1)):
        print(f"  {title} recall@K:")
        print(f"    {'rep':>14}" + "".join(f"{'@'+str(k):>9}" for k in KS) + f"{'med':>8}")
        for name in REPS:
            rk = results[name][idx]
            print(f"    {name:>14}" + "".join(f"{rr(rk,k):>8.1f}%" for k in KS) +
                  f"{int(np.median(rk)) if rk else 0:>8}")
        print()

    ec = rr(results["equal-c4"][0], 5); lc = rr(results["landmark-c4"][0], 5)
    ec1 = rr(results["equal-c4"][0], 1); lc1 = rr(results["landmark-c4"][0], 1)
    print("=" * 100)
    print(f"  CONTENT @1: equal-c4 {ec1:.0f}% vs landmark-c4 {lc1:.0f}%   |   @5: {ec:.0f}% vs {lc:.0f}%")
    if lc1 - ec1 >= 3 or lc - ec >= 3:
        print(f"  LANDMARK ALIGNMENT WINS: onset-aligned chunks rank content words better than equal-time (@1 {lc1-ec1:+.0f},")
        print(f"  @5 {lc-ec:+.0f}) -- phonetic boundaries align the same phone to the same chunk. Build a landmark pyramid")
        print("  and wire it in.")
    else:
        print(f"  LANDMARK ALIGNMENT DOES NOT WIN (@1 {lc1-ec1:+.0f}, @5 {lc-ec:+.0f}): equal-time chunks already align well")
        print("  enough (words are roughly rate-normalised by relative-time chunking), and onset detection on a single")
        print("  word is too noisy to improve it. The representation has PLATEAUED at the multi-scale pyramid; alignment")
        print("  is not the residual -- the remaining gap is acoustic discriminability (cues/data), not chunking.")
    print("=" * 100)


if __name__ == "__main__":
    main()
