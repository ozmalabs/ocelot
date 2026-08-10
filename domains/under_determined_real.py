"""under_determined_real — owned world data prep for the REAL under-determined
regime: a REAL word n-gram counted from REAL LibriSpeech transcripts (NOT an
imposed bigram), over a constrained vocabulary that is acoustically realizable
cross-speaker from real Speech-Commands word clips.

THE REGIME (why this is the PROPER under-determined case, on REAL data):
  · ACOUSTIC under-determination is NATURAL here, not synthetic SNR: a single
    cross-speaker acoustic read of a real word is ambiguous (v1 measured the
    35-word SC cross-speaker frame-relative recogniser at ~0.18 — well above the
    0.029 chance, far below resolved). Speaker variation IS the under-determination.
  · The CONTEXT/FUTURE frames are a REAL language model: the actual word n-gram
    of real English sentences (LibriSpeech dev-clean transcripts), counted here
    (owned counts, add-k smoothed). NOT imposed — it is the world's real statistics.
  · The two are COMPLEMENTARY: where the cross-speaker acoustic can't resolve a
    word, the real sentence context can (and vice-versa) — the intersection
    over-determines what either frame alone leaves ambiguous.

WHAT THIS MODULE OWNS (world data only — no agent reasoning, no decisions):
  · count_ngram      — count uni/bi-gram (+ 2-step) over the FULL real transcript
                       vocabulary from real LibriSpeech transcripts.
  · sc_vocab         — the constrained vocabulary = the Speech-Commands words
                       (real isolated word audio exists for each, cross-speaker).
  · target_instances — real (prev, target_sc_word, next, next2) tuples mined from
                       the real transcripts: every position whose word is in the SC
                       vocab, with its REAL sentence neighbours (the real context).
  · context_logadm / future_logadm — turn the real n-gram into per-candidate
                       SOFT log-admissibility excluders over the SC vocab, given a
                       real (known) neighbour word. Add-k smoothed, max-normalised
                       to [_FLOOR,0] (the soft-excluder convention of v2).

DONKEY BOUNDARY: every count here is a real frequency in a real corpus (the
world's statistics); the smoothing is a fixed add-k (no fit, no sweep-and-keep).
The acoustic frame is the agent's v1 frame-relative recogniser. The collapse ops
are v2's owned weighted_admissibility / dot_product / viterbi. Held-out SPEAKERS
realise the acoustic; the LM is counted from the transcript corpus (no speaker
identity, no acoustic leakage — the LM never sees audio).
"""
from __future__ import annotations

import math
import os
import collections

import numpy as np

import domains.frame_inference_v2 as F2

# The constrained vocabulary = the Speech-Commands words (real cross-speaker audio
# for each). Discovered from the SC dir at import (the world tells us what's real).
_SC_DIR = "/tmp/sc"
_LIBRI_DIR = "/tmp/LibriSpeech"

_BOS, _EOS = "<s>", "</s>"


def sc_vocab():
    """The constrained vocabulary: SC word folders that have real audio. Sorted."""
    if not os.path.isdir(_SC_DIR):
        return []
    return sorted(
        d for d in os.listdir(_SC_DIR)
        if os.path.isdir(os.path.join(_SC_DIR, d)) and not d.startswith("_")
    )


def _iter_transcripts(libri_dir=_LIBRI_DIR):
    """Yield each real utterance's lowercase word list from real LibriSpeech
    transcript files. Pure corpus I/O (the world's real sentences)."""
    if not os.path.isdir(libri_dir):
        return
    for sub in os.listdir(libri_dir):
        d = os.path.join(libri_dir, sub)
        if not os.path.isdir(d):
            continue
        for root, _dirs, names in os.walk(d):
            for fn in names:
                if not fn.endswith(".trans.txt"):
                    continue
                with open(os.path.join(root, fn)) as f:
                    for line in f:
                        line = line.strip()
                        if not line or " " not in line:
                            continue
                        _utt, txt = line.split(" ", 1)
                        yield txt.lower().split()


def count_ngram(libri_dir=_LIBRI_DIR):
    """Count the REAL word n-gram over the FULL transcript vocabulary.
    Returns (fwd, bwd, fwd2, bwd2, n_utts):
      fwd[a][b]  = count of bigram (a -> b)            (a is the predecessor)
      bwd[b][a]  = count of bigram (a -> b)            (b is the successor)
      fwd2[a][c] = count of skip-2 (a _ c)             (a two before c)
      bwd2[c][a] = count of skip-2 (a _ c)             (c two after a)
    All counts are real frequencies in the real corpus (owned, no fit)."""
    fwd = collections.defaultdict(collections.Counter)
    bwd = collections.defaultdict(collections.Counter)
    fwd2 = collections.defaultdict(collections.Counter)
    bwd2 = collections.defaultdict(collections.Counter)
    n_utts = 0
    for ws in _iter_transcripts(libri_dir):
        n_utts += 1
        seq = [_BOS, _BOS] + ws + [_EOS, _EOS]
        for a, b in zip(seq, seq[1:]):
            fwd[a][b] += 1
            bwd[b][a] += 1
        for a, c in zip(seq, seq[2:]):
            fwd2[a][c] += 1
            bwd2[c][a] += 1
    return fwd, bwd, fwd2, bwd2, n_utts


def target_instances(vocab, libri_dir=_LIBRI_DIR):
    """Mine every REAL position whose word is in the constrained SC vocab, with its
    REAL sentence neighbours. Returns a list of dicts:
      {target, prev, prev2, next, next2}  (neighbours are the real words, possibly
      <s>/</s> at sentence edges; possibly out-of-SC-vocab — that's fine, they are
      the real context the LM conditions on). These are the REAL test items: each
      asks 'which SC word is here', given the cross-speaker acoustic AND the real
      surrounding sentence."""
    V = set(vocab)
    out = []
    for ws in _iter_transcripts(libri_dir):
        seq = [_BOS, _BOS] + ws + [_EOS, _EOS]
        for i in range(2, len(seq) - 2):
            if seq[i] in V:
                out.append({
                    "target": seq[i],
                    "prev": seq[i - 1], "prev2": seq[i - 2],
                    "next": seq[i + 1], "next2": seq[i + 2],
                })
    return out


# ===========================================================================
# REAL n-gram -> SOFT log-admissibility excluder over the constrained vocab.
# Given a KNOWN real neighbour word, the conditional distribution over the SC
# candidates (add-k smoothed real counts) -> soft excluder via v2's owned op.
# ===========================================================================

_ADD_K = 0.1  # fixed add-k smoothing (a constant, not a fit; never swept-and-kept)


def _cond_dist(counter, vocab, add_k=_ADD_K):
    """P(sc_candidate | given neighbour) restricted to the SC vocab, add-k smoothed.
    counter: a Counter of co-occurrence counts keyed by candidate word (e.g.
    fwd[prev] gives counts of successors; restrict to SC candidates). Returns a
    (K,) probability vector over vocab. A neighbour never seen with ANY SC word ->
    uniform (the LM ABSTAINS: no real evidence)."""
    K = len(vocab)
    counts = np.array([counter.get(w, 0) for w in vocab], dtype=np.float64)
    tot = counts.sum()
    if tot <= 0:
        return np.ones(K) / K                      # no real evidence -> uniform
    return (counts + add_k) / (tot + add_k * K)


def context_excluder(prev_word, fwd, vocab):
    """Backward/context frame: the real P(target | real predecessor) over the SC
    vocab -> soft excluder (max-normalised log-admissibility). The most-likely
    successor sits at e==0; less-likely real successors carved below. Owned."""
    p = _cond_dist(fwd.get(prev_word, collections.Counter()), vocab)
    return F2.soft_exclude_from_score(p)


def future_excluder(next_word, bwd, vocab):
    """Forward future-sheaf (1-step): the real P(target | real successor) over the
    SC vocab -> soft excluder. Knowing the real next word constrains the current."""
    p = _cond_dist(bwd.get(next_word, collections.Counter()), vocab)
    return F2.soft_exclude_from_score(p)


def future2_excluder(next2_word, bwd2, vocab):
    """Future-sheaf 2-step: real P(target | real word two-ahead) -> soft excluder.
    Another future frame in the sheaf (the polyglot holds several futures)."""
    p = _cond_dist(bwd2.get(next2_word, collections.Counter()), vocab)
    return F2.soft_exclude_from_score(p)


def context2_excluder(prev2_word, fwd2, vocab):
    """Backward 2-step context: real P(target | real word two-behind) -> excluder."""
    p = _cond_dist(fwd2.get(prev2_word, collections.Counter()), vocab)
    return F2.soft_exclude_from_score(p)


__all__ = [
    "sc_vocab", "count_ngram", "target_instances",
    "context_excluder", "future_excluder", "future2_excluder",
    "context2_excluder",
]
