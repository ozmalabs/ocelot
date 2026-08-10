"""THE JABBERWOCK'S TWO FOLLOW-UPS (ask_jabberwock_next): firm the test, then PROJECT OUT the speaker key.

Its plan, verbatim: "stop authoring absolute cues; widen the speaker bank and PROJECT OUT the empirically-
estimated key; gate the whole thing behind a noise-floor check on the test." And: cross-SPEAKER normalisation
is "the same move as CMVN, but over the SPEAKER axis instead of time -- subtract the per-word speaker-mean /
whiten the cross-speaker covariance, recognise in the RESIDUAL." Estimable only from MANY speakers (you can't
characterise the nuisance manifold from 2).

(1) FIRM THE TEST: average over more renditions to damp the piper-VITS noise that gave a 19pt swing.
(2) PROJECT OUT THE KEY (WCCN -- within-word, across-speaker covariance whitening; closed-form linear algebra,
    NO gradient): pool the within-word-centred exemplars across the N banked speakers = the SPEAKER (nuisance)
    covariance; whiten by Sigma^-1/2 so the high-variance speaker directions are shrunk and the word directions
    dominate; recognise UNSEEN speakers in the whitened residual. With more speakers, Sigma is better estimated,
    so the project-out should LIFT the curve -- the key-recovery the cipher asked for, estimated from coverage.

Compares PLAIN (1-NN cosine on the pooled feature) vs PROJECTED-OUT (WCCN) held-out recall vs N. Real English
speakers, scored against the KNOWN word.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_project_out
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world import SpeechWorld

FS = 8000
WORDS = ("one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
TRAIN_POOL = ["lessac", "amy", "alan", "joe", "alba", "hfc_female", "northern", "john",
              "kusal", "cori", "norman", "hfc_male", "sam", "bryce", "ljspeech", "danny"]  # 16, diverse
HELDOUT = ["ryan", "jenny", "kristin", "kathleen"]   # 4 UNSEEN (US-M, GB-F, US-F, US-F-low)
N_VALUES = [1, 2, 4, 8, 16]
RENDS = 4                  # bank 0,1 ; test 2,3
BANK_R, TEST_R = (0, 1), (2, 3)


def vec_of(channels):
    """Pool the agent's per-cue readouts into ONE feature vector (the space WCCN whitens)."""
    return np.concatenate([np.asarray(c, dtype=np.float64).ravel() for c in channels])


def wccn(X, y, lam=0.1):
    """Within-word, across-speaker covariance whitening (the agent's project-out; closed-form, no gradient).
    Center each exemplar by ITS WORD's mean -> residuals = speaker(nuisance)+noise variation; Sigma = their
    covariance; W = Sigma^-1/2 (regularised). Returns W (d x d): X@W shrinks the speaker directions."""
    d = X.shape[1]
    R = np.empty_like(X)
    for w in set(y):
        m = (y == w)
        R[m] = X[m] - X[m].mean(0)
    Sig = (R.T @ R) / max(len(X), 1) + lam * np.eye(d)
    ev, U = np.linalg.eigh(Sig)
    ev = np.clip(ev, 1e-8, None)
    return U @ np.diag(ev ** -0.5) @ U.T


def main():
    print("=" * 96)
    print("THE JABBERWOCK'S FOLLOW-UPS — firm the test + PROJECT OUT the speaker key (WCCN), recall vs N.")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    sw = SpeechWorld(s, source_world=None)
    print(f"  held-out (UNSEEN) {HELDOUT} | {len(WORDS)} words | {RENDS} renditions (bank {len(BANK_R)}, test {len(TEST_R)})")
    print("  synthesising + extracting (real English voices)...", flush=True)
    vecs = {}
    for spk in TRAIN_POOL + HELDOUT:
        for w in WORDS:
            for r in range(RENDS):
                out = sw.synth(w, {"variant": spk, "pitch": 50, "rate": 175})
                if out is not None:
                    vecs[(spk, w, r)] = vec_of(SDW.feature_channels(s, np.asarray(out[0], dtype=np.float64), out[1]))
    D = min(len(v) for v in vecs.values())
    for k in vecs:
        vecs[k] = vecs[k][:D]                    # align dims (cue lengths can vary by clip length)

    def bank(train, project):
        X = np.stack([vecs[(spk, w, r)] for spk in train for w in WORDS for r in BANK_R if (spk, w, r) in vecs])
        y = np.array([w for spk in train for w in WORDS for r in BANK_R if (spk, w, r) in vecs])
        W = wccn(X, y) if project else np.eye(D)
        Xn = X @ W; Xn /= (np.linalg.norm(Xn, axis=1, keepdims=True) + 1e-9)
        return Xn, y, W

    def recall(train, project, rend):
        Xn, y, W = bank(train, project)
        hits = tot = 0
        for spk in HELDOUT:
            for w in WORDS:
                if (spk, w, rend) not in vecs:
                    continue
                q = vecs[(spk, w, rend)] @ W; q /= (np.linalg.norm(q) + 1e-9)
                guess = y[int(np.argmax(Xn @ q))]            # 1-NN cosine
                tot += 1; hits += int(guess == w)            # SCORE against known w
        return hits / tot if tot else 0.0

    # firm-the-test: noise floor at N=4 over the 5 test renditions (plain).
    sw4 = [recall(TRAIN_POOL[:4], False, r) for r in TEST_R]
    spread = max(sw4) - min(sw4)
    print(f"\n  NOISE FLOOR (N=4 plain, {len(TEST_R)} test renditions): {[f'{v*100:.0f}%' for v in sw4]}  "
          f"spread {spread*100:.0f}pt -> {'still noisy' if spread>0.10 else 'RESOLVES'} (avg damps it further)\n")

    print(f"  held-out recall vs N (avg over {len(TEST_R)} test renditions, chance {100/len(WORDS):.0f}%):")
    print(f"    {'N speakers':>11}{'PLAIN':>10}{'PROJECT-OUT (WCCN)':>22}")
    pl, pr = [], []
    for N in N_VALUES:
        p = float(np.mean([recall(TRAIN_POOL[:N], False, r) for r in TEST_R]))
        q = float(np.mean([recall(TRAIN_POOL[:N], True, r) for r in TEST_R]))
        pl.append(p); pr.append(q)
        print(f"    {N:>11}{p*100:>9.0f}%{q*100:>21.0f}%")

    print("\n" + "=" * 96)
    climb = pl[-1] - pl[0]
    lift = pr[-1] - pl[-1]
    cov = "COVERAGE WALL CONFIRMED" if climb > 0.10 else "flat"
    print(f"  CURVE: plain held-out recall {pl[0]*100:.0f}% -> {pl[-1]*100:.0f}% over N=1->{N_VALUES[-1]} ({cov}).")
    if lift > 0.05:
        print(f"  PROJECT-OUT WORKS: WCCN lifts held-out recall a further +{lift*100:.0f}pt at N={N_VALUES[-1]} "
              f"({pl[-1]*100:.0f}% -> {pr[-1]*100:.0f}%). Estimating + removing the speaker key from the multi-speaker bank")
        print("  recovers the word on UNSEEN speakers -- the cipher's key-recovery, earned from coverage, no gradient.")
    elif lift > 0.0:
        print(f"  project-out marginal (+{lift*100:.0f}pt): the pooled-vector WCCN helps a little; the bigger lever is")
        print("  coverage itself. A per-cue / shrinkage-tuned whitening, or more banked speakers, is the next refinement.")
    else:
        print(f"  project-out did NOT help ({pr[-1]*100:.0f}% vs plain {pl[-1]*100:.0f}%): the speaker variation is not a")
        print("  low-rank linear nuisance in this pooled feature -- coverage (more exemplars) is doing the real work, not whitening.")
    print("=" * 96)


if __name__ == "__main__":
    main()
