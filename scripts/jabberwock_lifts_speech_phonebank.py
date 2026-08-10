"""LIFT speech recognition on the CLEAN force-aligned phonebank: exact -> graded.

The earlier gates failed for lack of word boundaries. The phonebank
(/home/matt/data/phonebank) is FORCE-ALIGNED LibriSpeech (torchaudio MMS_FA):
each entry is (word, frames, phones) with CLEAN word boundaries. dev-clean and
train-clean-100 are DISJOINT speakers -> a genuine cross-speaker split.

THE TWO MATCHERS (same clean instances, same cross-speaker split; only the decision
differs) — mirroring the SOLVED trace arc (exact-token 19% -> soft StructSim 35%):
  EXACT  (the lexical_access regime): quantise each cochleagram frame to a codebook
         symbol, dedupe consecutive -> a phoneme-like SEQUENCE from the AUDIO;
         recognise only on EXACT sequence equality. Hard leaf.
  GRADED (the lift): cosine-DTW over the frame trajectory (soft per-frame leaf +
         hard temporal skeleton) — the agent's own speech DTW. Nearest support -> word.

GATE: cross-speaker N-way accuracy GRADED > EXACT > chance. SUPPORT = train-clean-100
words; QUERY = dev-clean words (unseen speakers). No new training, no LLM.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_lifts_speech_phonebank.py [n_words] [max_query] [per_word_support]
"""
from __future__ import annotations
import glob, os, pickle, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
import numpy as np
from collections import Counter, defaultdict
from scripts.jabberwock_reads_oov_from_phones import dtw, STOP

BANK = "/home/matt/data/phonebank"


def _l2(fr):
    fr = np.asarray(fr, dtype=np.float64)
    if fr.ndim == 1:
        fr = fr.reshape(1, -1)
    n = np.linalg.norm(fr, axis=1, keepdims=True)
    return fr / np.clip(n, 1e-9, None)


def _load(split_glob, cap_shards):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, split_glob)))[:cap_shards]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for entry in shard:
            if isinstance(entry, (list, tuple)) and len(entry) >= 2 and isinstance(entry[0], str):
                w = entry[0].lower()
                fr = _l2(entry[1])
                if w not in STOP and len(w) >= 3 and fr.shape[0] >= 2:
                    out.append((w, fr))
    return out


def _code_seq(fr, centroids):
    d = ((fr[:, None, :] - centroids[None, :, :]) ** 2).sum(2)
    lab = d.argmin(1)
    seq = []
    for j in lab:
        if not seq or seq[-1] != j:
            seq.append(int(j))
    return tuple(seq)


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_query = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    per_word = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    print("=" * 92)
    print("LIFT SPEECH on the CLEAN force-aligned phonebank: exact vs graded, cross-speaker")
    print("=" * 92)
    support_all = _load("train-clean-100_*.pkl", cap_shards=8)
    query_all = _load("dev-clean_*.pkl", cap_shards=8)
    print(f"  loaded support(train)={len(support_all)}  query(dev)={len(query_all)} word instances")

    sup_words = Counter(w for w, _ in support_all)
    qry_words = Counter(w for w, _ in query_all)
    vocab = [w for w, _ in sup_words.most_common() if qry_words[w] >= 2][:n_words]
    vset = set(vocab)
    print(f"  cross-split vocab (top {n_words} content words in both): {vocab}")
    chance = 1.0 / len(vocab)
    print(f"  chance = {chance:.3f}")
    if len(vocab) < 3:
        print("  too few shared content words — raise cap_shards."); return 2

    # support: cap per word
    by_word = defaultdict(list)
    for w, fr in support_all:
        if w in vset and len(by_word[w]) < per_word:
            by_word[w].append(fr)
    support = [(w, fr) for w, frs in by_word.items() for fr in frs]
    # codebook for EXACT (k-means on support frames)
    frames = np.concatenate([fr for _w, fr in support], axis=0)
    rng = np.random.default_rng(0)
    K = 48
    cent = frames[rng.choice(len(frames), size=min(K, len(frames)), replace=False)].copy()
    for _ in range(8):
        lab = (((frames[:, None, :] - cent[None, :, :]) ** 2).sum(2)).argmin(1)
        for k in range(len(cent)):
            m = frames[lab == k]
            if len(m):
                cent[k] = m.mean(0)
    sup_codes = [(w, _code_seq(fr, cent)) for w, fr in support]

    # queries
    q = [(w, fr) for w, fr in query_all if w in vset]
    rng2 = np.random.default_rng(1)
    rng2.shuffle(q)
    q = q[:max_query]
    print(f"  support={len(support)} instances  queries={len(q)}")

    exact_ok = exact_fired = graded_ok = 0
    for w, fr in q:
        qcode = _code_seq(fr, cent)
        hits = Counter(sw for sw, sc in sup_codes if sc == qcode)
        if hits:
            exact_fired += 1
            if hits.most_common(1)[0][0] == w:
                exact_ok += 1
        best_d, best_w = 1e18, None
        for sw, sfr in support:
            d = dtw(fr, sfr)
            if d < best_d:
                best_d, best_w = d, sw
        if best_w == w:
            graded_ok += 1

    n = len(q)
    ea, ga = exact_ok / n, graded_ok / n
    print("\n" + "=" * 92)
    print(f"  EXACT  categorical  : acc={ea:.3f}   (exact code-sequence fired on {exact_fired}/{n} = {exact_fired/n:.0%} of queries)")
    print(f"  GRADED DTW (lift)   : acc={ga:.3f}")
    print(f"  chance              : {chance:.3f}")
    print(f"  delta (graded-exact): {ga-ea:+.3f}")
    print("=" * 92)
    lift = ga > ea + 0.02 and ga > chance
    print(f"  {'LIFT' if lift else 'NO LIFT'} — same clean force-aligned instances, same cross-speaker split (dev vs")
    print("  train-clean-100), only the recognition DECISION differs: exact categorical-sequence equality")
    print("  (the lexical_access / trace exact-token regime) vs graded DTW (soft per-frame leaf + hard")
    print("  temporal skeleton). The trace exact->graded lift, on REAL cross-speaker LibriSpeech words.")
    return 0 if lift else 2


if __name__ == "__main__":
    raise SystemExit(main())
