"""Drive the agent's #1 frontier (statistical SEGMENTATION) with the controlled Saffran
paradigm: a continuous unit stream from an artificial language whose ONLY boundary cue is
TRANSITIONAL PROBABILITY (high within words, low at boundaries). Ground-truth boundaries
are known, so we MEASURE boundary F1 + word-token F1 of the agent's held TP-trough
segmenter (learn_speech_segmented.segment / tp_table — the Saffran operator). Sweep
difficulty (distinct vs shared units, vocabulary size) to find the ceiling + the limiter,
the way the clustering frontier was driven.

Run: python scripts/segmentation_saffran.py
"""
from __future__ import annotations
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))

import math

from scripts.learn_speech_segmented import tp_table, segment


def succ_entropy(seqs):
    """Branching (successor) entropy per unit: H(next | a) over the stream. HIGH = a is
    followed by MANY different units = a is word-final (Harris 1955 / Tanaka-Ishii)."""
    fwd = {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            fwd.setdefault(a, {})[b] = fwd.setdefault(a, {}).get(b, 0) + 1
    H = {}
    for a, nx in fwd.items():
        tot = sum(nx.values())
        H[a] = -sum((c / tot) * math.log2(c / tot) for c in nx.values())
    return H


def bwd_table(seqs):
    """Backward TP: P(a | b) where a precedes b. Drops when a is a RARE predecessor of b
    = b 'starts fresh' = boundary before b."""
    uni, bwd = {}, {}
    for seq in seqs:
        for a, b in zip(seq, seq[1:]):
            uni[b] = uni.get(b, 0) + 1
            bwd.setdefault(b, {})[a] = bwd.setdefault(b, {}).get(a, 0) + 1
    return {b: {a: c / uni[b] for a, c in pv.items()} for b, pv in bwd.items()}


def segment_bidir(seq, fwd, bwd):
    """Cut at troughs of the BIDIRECTIONAL bond = min(forward TP, backward TP): a true
    within-word bigram is tight BOTH ways; a boundary bigram is loose either way."""
    if len(seq) < 2:
        return [tuple(seq)] if seq else []
    def bond(a, b):
        return min(fwd.get(a, {}).get(b, 1.0), bwd.get(b, {}).get(a, 1.0))
    words, cur = [], [seq[0]]
    for i in range(1, len(seq)):
        here = bond(seq[i - 1], seq[i])
        prev = bond(seq[i - 2], seq[i - 1]) if i >= 2 else 1.0
        nxt = bond(seq[i], seq[i + 1]) if i + 1 < len(seq) else 1.0
        if here < prev and here < nxt:
            words.append(tuple(cur)); cur = [seq[i]]
        else:
            cur.append(seq[i])
    words.append(tuple(cur))
    return words


def segment_entropy(seq, H):
    """Cut AFTER a unit whose successor entropy is a LOCAL MAX (it branches to many
    continuations -> word-final). The dual of the TP-trough, using the full successor
    distribution instead of the single forward TP."""
    if len(seq) < 2:
        return [tuple(seq)] if seq else []
    words, cur = [], [seq[0]]
    for i in range(1, len(seq)):
        h_prev = H.get(seq[i - 2], 0.0) if i >= 2 else 0.0
        h_at = H.get(seq[i - 1], 0.0)          # entropy of the unit we'd cut AFTER
        h_next = H.get(seq[i], 0.0)
        if h_at > h_prev and h_at >= h_next and h_at > 0:   # local-max branch -> boundary
            words.append(tuple(cur)); cur = [seq[i]]
        else:
            cur.append(seq[i])
    words.append(tuple(cur))
    return words


def make_language(n_words, wlen, alphabet, seed, shared):
    rng = random.Random(seed)
    units = list(range(alphabet))
    if shared:                                   # words drawn with replacement -> overlap
        return [tuple(rng.choice(units) for _ in range(wlen)) for _ in range(n_words)]
    rng.shuffle(units)                           # distinct units per word (clean TP)
    return [tuple(units[i * wlen:(i + 1) * wlen]) for i in range(n_words)]


def make_stream(words, n_tokens, seed):
    rng = random.Random(seed)
    stream, bounds, prev = [], set(), None
    for _ in range(n_tokens):
        w = rng.choice(words)
        while w == prev and len(words) > 1:       # no immediate repeat (Saffran)
            w = rng.choice(words)
        prev = w
        stream.extend(w)
        bounds.add(len(stream))                   # boundary AFTER this word
    return stream, bounds


def boundary_positions(words):
    """word-tuples -> cumulative boundary positions (after each word)."""
    out, pos = set(), 0
    for w in words:
        pos += len(w); out.add(pos)
    return out


def f1(pred, true):
    inter = len(pred & true)
    p = inter / len(pred) if pred else 0.0
    r = inter / len(true) if true else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0


def token_f1(pred_words, true_words):
    """exact-span match: a token is right if its (start,end) equals a true word's."""
    def spans(ws):
        out, pos = set(), 0
        for w in ws:
            out.add((pos, pos + len(w))); pos += len(w)
        return out
    ps, ts = spans(pred_words), spans(true_words)
    inter = len(ps & ts)
    p = inter / len(ps) if ps else 0.0
    r = inter / len(ts) if ts else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0


def _score(stream, true_words, pred_words):
    end = len(stream)
    return (f1(boundary_positions(pred_words) - {end}, boundary_positions(true_words) - {end}),
            token_f1(pred_words, true_words))


def run(n_words, wlen, alphabet, shared, n_tokens=600, seeds=5):
    tpb, tpt, enb, ent = [], [], [], []
    for sd in range(seeds):
        words = make_language(n_words, wlen, alphabet, sd, shared)
        stream, true_b = make_stream(words, n_tokens, sd + 100)
        cuts = set(true_b)
        true_words, cur = [], []
        for i, u in enumerate(stream):
            cur.append(u)
            if (i + 1) in cuts:
                true_words.append(tuple(cur)); cur = []
        table = tp_table([stream])               # held Saffran forward-TP table
        bwd = bwd_table([stream])                 # backward TP
        b1, t1 = _score(stream, true_words, segment(stream, table))
        b2, t2 = _score(stream, true_words, segment_bidir(stream, table, bwd))
        tpb.append(b1); tpt.append(t1); enb.append(b2); ent.append(t2)
    n = len(tpb)
    return (sum(tpb)/n, sum(tpt)/n, sum(enb)/n, sum(ent)/n)


def main():
    print("=" * 74)
    print("SAFFRAN SEGMENTATION — held TP-trough segmenter, ground-truth boundaries")
    print("=" * 74)
    print(f"  {'condition':30s} {'TP tokF1':>9s} {'BIDIR':>10s} {'BIDIR-TP':>9s}")
    print("-" * 74)
    configs = [
        ("clean 6w x3, distinct units", dict(n_words=6, wlen=3, alphabet=18, shared=False)),
        ("overlap 6w x3, alphabet 9", dict(n_words=6, wlen=3, alphabet=9, shared=True)),
        ("12w x3, alphabet 12", dict(n_words=12, wlen=3, alphabet=12, shared=True)),
    ]
    for name, cfg in configs:
        _, tpt, _, ent = run(**cfg)
        print(f"  {name:30s} {tpt:9.3f} {ent:10.3f} {ent-tpt:+8.3f}")
    print("=" * 74)
    print("  TP = held forward TP-trough; BIDIR = bidirectional (fwd+bwd) bond trough.")



if __name__ == "__main__":
    main()
