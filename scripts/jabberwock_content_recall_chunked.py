"""RAISE CONTENT RECALL via REPRESENTATION — whole-word vector vs a SUB-SEGMENT SEQUENCE (the held-parts route).

Density and width both failed to raise content recall: more exemplars help only function words, and a wider lattice
raises the ceiling but the weak priors can't convert it. The diagnosis: the ear matches each word as ONE
fixed-length whole-word vector per cue, which blurs a content word's phonetic SEQUENCE -- so it ranks the true
content word ~14th. Content words are long and ordered; function words are short.

The fix tested here: represent a word as C equal time CHUNKS, feature each chunk, and score chunk-aligned (the same
exclusion-product 1-NN, now over C x cues channels). This preserves phonetic ORDER and length -- the held-parts
representation. Compares content/function recall@K for WHOLE-word vs CHUNKED(C). If chunking lifts content recall@5,
the representation was the limit (not data, not width) and it should be wired into the decode.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u \\
    -m scripts.jabberwock_content_recall_chunked [n_test] [vocab] [bank_utts]
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
CHUNKS = [4, 6]      # sub-segment counts to test


def whole_features(s, seg):
    return SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS)


def chunk_features(s, seg, c):
    """C equal time chunks, each featured -> a flat list of C x cues channels (order-preserving)."""
    seg = np.asarray(seg, dtype=np.float64)
    n = len(seg); out = []
    for i in range(c):
        a, b = int(i * n / c), int((i + 1) * n / c)
        sub = seg[a:b]
        if sub.size < int(0.02 * FS):                       # too short -> pad so the cue is defined
            sub = np.pad(sub, (0, int(0.02 * FS) - sub.size))
        out.extend(SDW.feature_channels(s, sub, FS))
    return out


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    vocab_size = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    bank_utts = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    print("=" * 100)
    print("CONTENT RECALL via REPRESENTATION — whole-word vector vs sub-segment SEQUENCE (held-parts)")
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

    reps = {"whole": (lambda seg: whole_features(s, seg))}
    for c in CHUNKS:
        reps[f"chunk{c}"] = (lambda seg, c=c: chunk_features(s, seg, c))

    print(f"  extracting train features ({len(vocab)} words, {CAP}/word) for {len(reps)} representations...", flush=True)
    banked = {name: [(w, fn(seg)) for w in vocab for seg in word_segs[w][:CAP]] for name, fn in reps.items()}

    print(f"  whisper-segmenting {n_test} test utts + extracting...", flush=True)
    test = {name: [] for name in reps}        # name -> [(truth, channels)]
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
                for name, fn in reps.items():
                    test[name].append((w, fn(seg)))
                got += 1
            if got >= 3:
                n_utt += 1
            if n_utt >= n_test:
                break
        if n_utt >= n_test:
            break
    nc = sum(t[0] not in STOP for t in test["whole"]); nf = sum(t[0] in STOP for t in test["whole"])
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

    results = {name: ranks(name) for name in reps}
    print("  CONTENT recall@K by representation:")
    print(f"    {'rep':>8}" + "".join(f"{'@'+str(k):>9}" for k in KS) + f"{'med_rank':>10}")
    for name in reps:
        cr, _ = results[name]
        print(f"    {name:>8}" + "".join(f"{rr(cr,k):>8.1f}%" for k in KS) +
              f"{int(np.median(cr)) if cr else 0:>10}")
    print("\n  FUNCTION recall@K by representation:")
    print(f"    {'rep':>8}" + "".join(f"{'@'+str(k):>9}" for k in KS) + f"{'med_rank':>10}")
    for name in reps:
        _, fr = results[name]
        print(f"    {name:>8}" + "".join(f"{rr(fr,k):>8.1f}%" for k in KS) +
              f"{int(np.median(fr)) if fr else 0:>10}")

    base = rr(results["whole"][0], 5)
    best_name = max(reps, key=lambda n: rr(results[n][0], 5))
    best = rr(results[best_name][0], 5)
    print("\n" + "=" * 100)
    print(f"  content recall@5: whole {base:.0f}% -> best {best_name} {best:.0f}%")
    if best_name != "whole" and best - base >= 4:
        print(f"  THE REPRESENTATION WAS THE LIMIT: a sub-segment SEQUENCE ({best_name}) lifts content recall +{best-base:.0f} pts")
        print("  over the whole-word vector -- preserving phonetic order ranks content words better. Held-parts wins;")
        print("  wire the chunked representation into the decode front end.")
    else:
        print(f"  chunking did not clearly help content (+{best-base:.0f}); the limit is deeper than fixed-chunk order")
        print("  (chunk misalignment / cue noise on short chunks) -- a DTW / phone-aligned sub-unit match is the next try.")
    print("=" * 100)


if __name__ == "__main__":
    main()
