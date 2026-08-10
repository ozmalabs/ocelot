"""PUSH THE REPRESENTATION FURTHER — MULTI-SCALE (pyramid) held-parts: whole + halves + quarters, combine-all.

chunk-4 (sub-segment sequence) doubled content top-1 recall but the equal chunks lose the GLOBAL word shape, and
over-splitting hurts short function words (chunk-6 dropped function@5). A multi-scale PYRAMID keeps both: whole-word
(global) + 2 chunks (coarse sequence) + 4 chunks (fine sequence), all channels under the same exclusion-product
1-NN -- combine-all over scales, so each word uses the resolution that separates it. Compares content/function
recall@K for whole | chunk4 | c2+c4 | pyramid(whole+c2+c4). The base scales are featured ONCE per segment and the
combinations composed by concatenating channels (free).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u \\
    -m scripts.jabberwock_content_recall_multiscale [n_test] [vocab] [bank_utts]
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

FS = 16000
CAP = 8
KS = [1, 5, 10, 20, 40]


def base_scales(s, seg):
    """Feature the word at scales {whole, 2-chunk, 4-chunk} ONCE; combinations compose these by concat."""
    seg = np.asarray(seg, dtype=np.float64)
    n = len(seg)

    def chunks(c):
        out = []
        for i in range(c):
            a, b = int(i * n / c), int((i + 1) * n / c)
            sub = seg[a:b]
            if sub.size < int(0.02 * FS):
                sub = np.pad(sub, (0, int(0.02 * FS) - sub.size))
            out.extend(SDW.feature_channels(s, sub, FS))
        return out

    return {"w": SDW.feature_channels(s, seg, FS), "c2": chunks(2), "c4": chunks(4)}


REPS = {
    "whole":          lambda b: b["w"],
    "chunk4":         lambda b: b["c4"],
    "c2+c4":          lambda b: b["c2"] + b["c4"],
    "pyr(w+c2+c4)":   lambda b: b["w"] + b["c2"] + b["c4"],
}


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    vocab_size = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    bank_utts = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    print("=" * 100)
    print("MULTI-SCALE held-parts — whole | chunk4 | c2+c4 | pyramid(whole+c2+c4); does combine-all over scales win?")
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

    print(f"  featuring train ({len(vocab)} words, {CAP}/word) at base scales...", flush=True)
    train_base = {w: [base_scales(s, seg) for seg in word_segs[w][:CAP]] for w in vocab}
    banked = {name: [(w, fn(b)) for w in vocab for b in train_base[w]] for name, fn in REPS.items()}

    print(f"  whisper-segmenting {n_test} test utts + featuring...", flush=True)
    test_base = []
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
                test_base.append((w, base_scales(s, seg)))
                got += 1
            if got >= 3:
                n_utt += 1
            if n_utt >= n_test:
                break
        if n_utt >= n_test:
            break
    test = {name: [(w, fn(b)) for (w, b) in test_base] for name, fn in REPS.items()}
    nc = sum(t not in STOP for t, _ in test_base); nf = sum(t in STOP for t, _ in test_base)
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
        print(f"  {title} recall@K by representation:")
        print(f"    {'rep':>14}" + "".join(f"{'@'+str(k):>9}" for k in KS) + f"{'med_rank':>10}")
        for name in REPS:
            rk = results[name][idx]
            print(f"    {name:>14}" + "".join(f"{rr(rk,k):>8.1f}%" for k in KS) +
                  f"{int(np.median(rk)) if rk else 0:>10}")
        print()

    base_c = rr(results["chunk4"][0], 5)
    best_name = max(REPS, key=lambda n: rr(results[n][0], 5) + 0.25 * rr(results[n][1], 5))   # content-weighted
    best_c = rr(results[best_name][0], 5); best_f = rr(results[best_name][1], 5)
    print("=" * 100)
    print(f"  content recall@5: chunk4 {base_c:.0f}% -> best {best_name} {best_c:.0f}%  (function@5 {best_f:.0f}%)")
    if best_name.startswith("pyr") or best_name == "c2+c4":
        print(f"  MULTI-SCALE WINS: combine-all over scales ({best_name}) beats single-scale chunk4 -- the global word")
        print(f"  shape + the fine sequence ADD. Wire {best_name} into the decode front end and re-measure end-to-end.")
    elif best_name == "chunk4":
        print(f"  single-scale chunk4 stays best (multi-scale didn't add) -- the coarse/global scales are redundant")
        print("  with the fine sequence here. The next lever is rate-robust alignment (DTW) or phone-aligned chunks.")
    print("=" * 100)


if __name__ == "__main__":
    main()
