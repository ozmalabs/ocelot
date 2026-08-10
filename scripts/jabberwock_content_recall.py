"""RAISE THE EAR'S CONTENT RECALL — diagnose which lever moves it: density (exemplars/word) x lattice width (K).

The prosodic/LM decode is capped by content lattice recall (~29% @ top-5): the true content word reaches the
candidate list only 29% of the time. The ear matches each word as a single fixed-length whole-word vector per cue,
scored by 1-NN min-cosine over that word's exemplars. Content words are rarer (sparse 1-NN coverage) and longer
(a fixed vector blurs their phonetic sequence). Two cheap levers to test first:
  - DENSITY: more exemplars per word (better 1-NN coverage). Earlier the density track climbed 33->39% with data.
  - WIDTH K: a wider lattice mechanically raises recall@K -- the priors then have more to work with.
This sweeps both cheaply: whisper-segment train+test ONCE, extract features ONCE at the max cap, then for each
exemplar-cap rebuild the bank (a numpy subset) and read recall@K off the full per-word ranking. Reports content vs
function recall@{1,5,10,20,40} and median true-word rank -- so we see whether the candidates are THERE (raise K) or
MISSING (need density / a better representation).

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python /home/matt/ozma/internal/research/.venv/bin/python -u \\
    -m scripts.jabberwock_content_recall [n_test] [vocab] [bank_utts]
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
MAXCAP = 24
CAPS = [4, 8, 16, 24]
KS = [1, 5, 10, 20, 40]


def main():
    n_test = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    vocab_size = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    bank_utts = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    print("=" * 100)
    print("CONTENT RECALL — density (exemplars/word) x lattice width (K); which lever raises the ceiling?")
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
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})

    # Extract features ONCE at the max cap; bank-at-cap is then a cheap subset.
    print(f"  extracting train features ({len(vocab)} words, up to {MAXCAP}/word)...", flush=True)
    train_feats = {}
    for w in vocab:
        train_feats[w] = [SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS)
                          for seg in word_segs[w][:MAXCAP]]

    print(f"  whisper-segmenting {n_test} held-out test utterances + extracting features...", flush=True)
    cands = sorted(vocab)
    test = []                       # (truth, channels)
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
                test.append((w, SDW.feature_channels(s, np.asarray(seg, dtype=np.float64), FS)))
                got += 1
            if got >= 3:
                n_utt += 1
            if n_utt >= n_test:
                break
        if n_utt >= n_test:
            break
    print(f"  {len(test)} test tokens ({sum(t[0] not in STOP for t in test)} content, "
          f"{sum(t[0] in STOP for t in test)} function)\n")

    def recall_at_cap(cap):
        banked = [(w, ch) for w in vocab for ch in train_feats[w][:cap]]
        c_ranks, f_ranks = [], []
        for truth, channels in test:
            lo = acoustic_logp(channels, banked, cands)
            order = sorted(cands, key=lambda w: -lo[w])
            rank = order.index(truth) + 1 if truth in order else 10 ** 9
            (c_ranks if truth not in STOP else f_ranks).append(rank)
        return c_ranks, f_ranks

    def recall_row(ranks, k):
        return 100.0 * np.mean([r <= k for r in ranks]) if ranks else 0.0

    print(f"  CONTENT recall@K (the decode ceiling), by exemplars-per-word:")
    print(f"    {'cap':>5}" + "".join(f"{'@'+str(k):>9}" for k in KS) + f"{'med_rank':>10}")
    content_best = {}
    func_rows = {}
    for cap in CAPS:
        cr, fr = recall_at_cap(cap)
        content_best[cap] = cr; func_rows[cap] = fr
        print(f"    {cap:>5}" + "".join(f"{recall_row(cr,k):>8.1f}%" for k in KS) +
              f"{int(np.median(cr)) if cr else 0:>10}")
    print(f"\n  FUNCTION recall@K (for contrast):")
    print(f"    {'cap':>5}" + "".join(f"{'@'+str(k):>9}" for k in KS) + f"{'med_rank':>10}")
    for cap in CAPS:
        fr = func_rows[cap]
        print(f"    {cap:>5}" + "".join(f"{recall_row(fr,k):>8.1f}%" for k in KS) +
              f"{int(np.median(fr)) if fr else 0:>10}")

    cr4 = recall_row(content_best[CAPS[0]], 5); crM = recall_row(content_best[CAPS[-1]], 5)
    crK = recall_row(content_best[CAPS[-1]], 20)
    print("\n" + "=" * 100)
    print(f"  content recall@5: {cr4:.0f}% (cap {CAPS[0]}) -> {crM:.0f}% (cap {CAPS[-1]})  [DENSITY effect]")
    print(f"  content recall@20 at cap {CAPS[-1]}: {crK:.0f}%  [WIDTH effect: raising K]")
    dens = crM - cr4; width = crK - crM
    if dens >= 4 and dens >= width:
        print(f"  DENSITY is the lever: more exemplars/word lifts content recall +{dens:.0f} pts -> bank more, raise the cap.")
    elif width >= 4:
        print(f"  WIDTH is the lever: the true word IS in a wider lattice (+{width:.0f} pts at K=20) -> widen K and lean")
        print("  on the prosodic/LM priors to pick it. Cheaper than more data.")
    else:
        print(f"  NEITHER cheap lever moves it much (density +{dens:.0f}, width +{width:.0f}): the whole-word fixed vector")
        print("  is the limit -> a sub-word / sequence representation is needed (the held-parts route).")
    print("=" * 100)


if __name__ == "__main__":
    main()
