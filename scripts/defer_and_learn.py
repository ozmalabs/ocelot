"""DEFER-AND-LEARN — the DEFER set IS the "teach me" queue: stream speech, learn OOV one-shot, recognise cross-speaker.

The jabberwock's design: the margin gate is the teacher-trigger (every low-margin defer = "ask"; confident recognitions never
ask -> cheap-first free); on defer the latent reifies as an Unknown, the teacher (oracle here) labels it, and the labelled
exemplar is appended to the bank (one-shot, the teach facility) so the word is IN-VOCAB next time. The cross-speaker-invariant
ear means ONE exemplar from speaker A matches speaker B. Streaming sim (science first): hold words OUT of the bank, stream
test utterances speaker-by-speaker, defer->teach->learn, measure:
  (1) CROSS-SPEAKER ONE-SHOT: a held-out word learned from speaker A's one utterance -> recognised from a DIFFERENT speaker B.
  (2) DEFER-RATE DECAY: teacher queries fall as the bank grows (the agent asks less as it learns).
  (3) EFFICIENCY: it asks ONLY on low margin (uncertain), not on every word.
BAR (jabberwock): cross-speaker one-shot >= 70-80%; defer-rate decays monotonically (not flat); control = held-out words are
~0% before learning (they're not in the bank), so learning is what enabled the cross-speaker recognition.

Run:
  cd experiments/gamma-substrate
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.defer_and_learn
"""
from __future__ import annotations

import os
import pickle
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from scripts.phase0_learned_latent import dtw, fit_pca, pca_apply, NWAY, PRUNE

CACHE = "/tmp/p0lat_cache_L6.pkl"
KMAX_BANK = 6
MARGIN_THRESH = 0.10
N_HOLDOUT = 40


def _l2(M):
    M = np.asarray(M, np.float32); n = np.linalg.norm(M, axis=1, keepdims=True)
    return (M / np.maximum(n, 1e-9)).astype(np.float32)


class GrowingBank:
    """the agent's lexicon — exemplars per word, grows online via teach (nothing frozen)."""
    def __init__(self):
        self.bank = {}; self.vocab = []; self.PW = np.zeros((0, 0), np.float32)
    def _proto(self, w):
        return _l2(np.stack([e.mean(0) for e in self.bank[w]]).mean(0)[None])[0]
    def add(self, w, exemplar):
        new = w not in self.bank
        self.bank.setdefault(w, []).append(exemplar)
        p = self._proto(w)
        if new:
            self.vocab.append(w)
            self.PW = p[None] if self.PW.size == 0 else np.vstack([self.PW, p])
        else:
            self.PW[self.vocab.index(w)] = p
    def recognise(self, traj):
        pv = traj.mean(0); pv = pv / (np.linalg.norm(pv) + 1e-9)
        top = np.argsort(-(self.PW @ pv))[:PRUNE]
        scored = sorted(((self.vocab[i], min(dtw(traj, e) for e in self.bank[self.vocab[i]])) for i in top), key=lambda x: x[1])
        (w1, d1), (w2, d2) = scored[0], scored[1]
        return w1, (d2 - d1) / (d2 + d1 + 1e-9)


def main():
    print("=" * 100)
    print("DEFER-AND-LEARN — stream speech, learn OOV one-shot, recognise cross-speaker")
    print("=" * 100)
    with open(CACHE, "rb") as fh:
        data = pickle.load(fh)
    train, test = data["train"], data["test"]
    mu_p, V_p = fit_pca([t[4] for t in train])
    def proj(lat):
        return pca_apply(lat, mu_p, V_p)

    vc = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        vc[w] += 1
    vocab = [w for w, c in sorted(vc.items(), key=lambda kv: -kv[1])[:NWAY] if c >= 2]
    vset = set(vocab)

    # holdout: in-vocab words that appear across >= 2 test speakers (so we can learn from A, test on B)
    tsp = defaultdict(set)
    for (w, sp, uid, cf, lat) in test:
        if w in vset:
            tsp[w].add(sp)
    cross = [w for w in vocab if len(tsp[w]) >= 2]
    holdout = set(cross[:N_HOLDOUT])
    known = [w for w in vocab if w not in holdout]
    print(f"  bank starts with {len(known)} KNOWN words; {len(holdout)} held out as OOV (each spoken by >=2 test speakers)")

    bank = GrowingBank()
    cnt = defaultdict(int)
    for (w, sp, uid, cf, lat) in train:
        if w in known and cnt[w] < KMAX_BANK:
            bank.add(w, proj(lat)); cnt[w] += 1

    # stream test words speaker-by-speaker (so holdout learned from earlier speaker, tested on later)
    stream = sorted([(w, sp, proj(lat)) for (w, sp, uid, cf, lat) in test if w in vset], key=lambda r: r[1])
    learned_from = {}            # holdout word -> speaker it was first taught from
    one_shot = []                # (correct,) for cross-speaker post-learn holdout encounters
    pre_learn_hit = []           # holdout recognition BEFORE learning (control, ~0)
    defers = []                  # 1 if deferred (teacher queried)
    teacher_queries = 0
    known_correct = []

    for (w, sp, traj) in stream:
        matched, margin = bank.recognise(traj)
        deferred = margin <= MARGIN_THRESH
        defers.append(1 if deferred else 0)
        is_hold = w in holdout
        if is_hold and w not in learned_from:
            pre_learn_hit.append(int(matched == w))     # before learning: should be ~0 (not in bank)
        if is_hold and w in learned_from and sp != learned_from[w]:
            one_shot.append(int(matched == w))          # CROSS-SPEAKER one-shot recognition
        elif (not is_hold):
            known_correct.append(int(matched == w))
        # defer -> teach -> learn (teacher = oracle label; mechanical host I/O)
        if deferred:
            teacher_queries += 1
            bank.add(w, traj)                           # learn: append the labelled exemplar (one-shot / accumulate)
            if is_hold and w not in learned_from:
                learned_from[w] = sp

    n = len(stream)
    # windowed defer-rate (decay)
    W = max(50, n // 12)
    windows = [100 * np.mean(defers[i:i + W]) for i in range(0, n - W, W)]

    print("\n" + "=" * 100)
    print(f"  streamed {n} word-tokens; teacher queried {teacher_queries} times ({100*teacher_queries/n:.0f}% of tokens — only on low margin)")
    print(f"  KNOWN-word recognition (non-holdout):        {100*np.mean(known_correct):.1f}%")
    print(f"  held-out words BEFORE learning (control):    {100*np.mean(pre_learn_hit) if pre_learn_hit else float('nan'):.1f}%  (not in bank -> ~0)")
    print(f"  CROSS-SPEAKER ONE-SHOT (learned A -> heard B): {100*np.mean(one_shot) if one_shot else float('nan'):.1f}%  ({len(one_shot)} cross-speaker instances)")
    print(f"  defer-rate over stream (windows of {W}): {' '.join(f'{x:.0f}' for x in windows)}")
    print("-" * 100)
    cs = 100 * np.mean(one_shot) if one_shot else 0.0
    pre = 100 * np.mean(pre_learn_hit) if pre_learn_hit else 0.0
    decayed = len(windows) >= 2 and windows[-1] < windows[0]
    if cs >= 70 and pre < 15 and decayed:
        print(f"  WORKS — defer-and-learn closes the loop: held-out words were ~{pre:.0f}% (OOV) before, and after ONE taught exemplar")
        print(f"  are recognised CROSS-SPEAKER at {cs:.0f}% (>=70). The agent asked only on low margin ({100*teacher_queries/n:.0f}%), and the")
        print(f"  defer-rate decayed ({windows[0]:.0f}%->{windows[-1]:.0f}%) as the bank grew. One-shot cross-speaker word learning, online,")
        print("  nothing frozen — the cross-speaker ear cashed in. Wire graph-native (Unknown node + ask Rule + teach append).")
    else:
        print(f"  PARTIAL — cross-speaker one-shot {cs:.0f}% (bar 70), pre-learn {pre:.0f}%, defer decay {decayed}. Loop runs; check the")
        print("  margin threshold / accumulation if the one-shot or the decay misses.")
    print("=" * 100)


if __name__ == "__main__":
    main()
