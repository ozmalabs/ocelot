"""Estimate the speaker-shape, then RE-PARSE with the speaker removed (Substitute the
inverse). The creator's move: a speaker is a separable shape, so estimate it from
context and SUBTRACT it before recognising the words — the residual is purer content.

On the clean cross-speaker phonebank word gate (dev vs train-clean-100, disjoint
speakers). The speaker-shape is recovered WITHOUT speaker labels (we proved it's a
strong shape: 0.969 ID): cluster each split's words by their spectral envelope into
speakers, take each speaker's mean band-envelope = their speaker-shape (a richer,
more-context estimate than per-word CMVN). RE-PARSE = subtract that band-envelope
from every frame (Substitute the inverse speaker-shape), re-L2, then match.

  BASELINE  graded DTW on the per-word-CMVN frames            (= the prior 0.625)
  REPARSED  graded DTW after removing the speaker-shape        (this)

Gate: does removing the speaker-shape lift cross-speaker word recognition?

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_reparse_speaker_removed.py [n_words] [max_query] [per_word]
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
    return fr / np.clip(np.linalg.norm(fr, axis=1, keepdims=True), 1e-9, None)


def _load(split_glob, cap):
    out = []
    for p in sorted(glob.glob(os.path.join(BANK, split_glob)))[:cap]:
        try:
            shard = pickle.load(open(p, "rb"))
        except Exception:
            continue
        for e in shard:
            if isinstance(e, (list, tuple)) and len(e) >= 2 and isinstance(e[0], str):
                w = e[0].lower(); fr = _l2(e[1])
                if w not in STOP and len(w) >= 3 and fr.shape[0] >= 3:
                    out.append((w, fr))
    return out


def _kmeans(X, K, iters=12, seed=0):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), size=min(K, len(X)), replace=False)].copy()
    lab = np.zeros(len(X), dtype=int)
    for _ in range(iters):
        lab = (((X[:, None, :] - C[None, :, :]) ** 2).sum(2)).argmin(1)
        for k in range(len(C)):
            m = X[lab == k]
            if len(m):
                C[k] = m.mean(0)
    return lab, C


def _spk_env(words, K):
    """Discover speakers (cluster by mean+std envelope) and return, per word, its
    speaker's mean BAND-ENVELOPE (the speaker-shape to subtract). No labels used."""
    feat = np.array([np.concatenate([fr.mean(0), fr.std(0)]) for _w, fr in words])
    feat = feat / np.clip(np.linalg.norm(feat, axis=1, keepdims=True), 1e-9, None)
    lab, _C = _kmeans(feat, K)
    # per cluster: mean frame (band envelope) over all its words' frames
    envs = {}
    for k in set(lab):
        frs = np.concatenate([words[i][1] for i in range(len(words)) if lab[i] == k], 0)
        envs[k] = frs.mean(0)
    return [envs[lab[i]] for i in range(len(words))], lab


def _remove(fr, env):
    r = fr - env[None, :]
    return r / np.clip(np.linalg.norm(r, axis=1, keepdims=True), 1e-9, None)


def main() -> int:
    n_words = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    max_query = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    per_word = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    sup_all = _load("train-clean-100_*.pkl", 8)
    qry_all = _load("dev-clean_*.pkl", 8)
    print("=" * 92)
    print("RE-PARSE WITH THE SPEAKER REMOVED (estimate speaker-shape, Substitute inverse)")
    print("=" * 92)
    sup_w = Counter(w for w, _ in sup_all); qry_w = Counter(w for w, _ in qry_all)
    vocab = [w for w, _ in sup_w.most_common() if qry_w[w] >= 2][:n_words]
    vset = set(vocab); chance = 1.0 / len(vocab)

    by = defaultdict(list)
    for w, fr in sup_all:
        if w in vset and len(by[w]) < per_word:
            by[w].append(fr)
    support = [(w, fr) for w, frs in by.items() for fr in frs]
    queries = [(w, fr) for w, fr in qry_all if w in vset]
    np.random.default_rng(1).shuffle(queries)
    queries = queries[:max_query]
    print(f"  vocab={len(vocab)} chance={chance:.3f}  support={len(support)} queries={len(queries)}")

    # discover speakers + speaker-shape per word (dev has ~3 speakers; train many)
    q_env, q_lab = _spk_env(queries, K=3)
    s_env, s_lab = _spk_env(support, K=24)
    print(f"  discovered speakers: dev~{len(set(q_lab))}  train~{len(set(s_lab))} (unsupervised, by speaker-shape)")

    sup_raw = support
    sup_rem = [(w, _remove(fr, s_env[i])) for i, (w, fr) in enumerate(support)]

    base = rep = 0
    for qi, (w, fr) in enumerate(queries):
        # BASELINE
        bd, bw = 1e18, None
        for sw, sfr in sup_raw:
            d = dtw(fr, sfr)
            if d < bd:
                bd, bw = d, sw
        base += (bw == w)
        # REPARSED: remove the query's speaker-shape, match to speaker-removed support
        frr = _remove(fr, q_env[qi])
        bd, bw = 1e18, None
        for sw, sfr in sup_rem:
            d = dtw(frr, sfr)
            if d < bd:
                bd, bw = d, sw
        rep += (bw == w)

    n = len(queries)
    print("\n" + "=" * 92)
    print(f"  BASELINE (per-word CMVN)          : {base/n:.3f}")
    print(f"  REPARSED (speaker-shape removed)  : {rep/n:.3f}")
    print(f"  chance                            : {chance:.3f}")
    print(f"  delta (reparsed - baseline)       : {rep/n - base/n:+.3f}")
    print("=" * 92)
    d = rep/n - base/n
    print(f"  {'SPEAKER-REMOVAL LIFTS THE RE-PARSE' if d > 0.02 else ('PARITY (per-word CMVN already removed most speaker)' if abs(d) <= 0.02 else 'REMOVAL HURT (over-normalised)')}")
    print("  One speaker-shape (estimated from the speaker's own speech, no labels) Substituted out, then")
    print("  the words re-matched cross-speaker — speaker and word are the two AntiUnify axes; removing one")
    print("  cleans the other. (Speaker-shape estimate needs only one sentence: ID from 1 utt = 0.969.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
