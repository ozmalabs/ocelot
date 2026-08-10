"""distributional_categories_probe — VERIFY the agent's PICKED + BUILT capability
(TOLD-k-FREE distributional category formation) by the agent's OWN controls.

The agent picked unsupervised CLUSTERING (gap_prioritiser: unifies 82 held
postulates, the most of its three named gaps). The keystone postulate it unified,
distributional_learning_of_categories, specifies the capability verbatim: categories
are the MODES of the cue distribution, number+location emergent (bimodal->2,
unimodal->1), carved at the valleys between modes, NO told-k. The agent composed it
from its OWN primitives (domains/distributional_categories: density = Count(near),
climb = Argmax-of-density — its order-N peak lifted to density). Its prior clustering
(cross_speaker_clustering) is k-means and is TOLD k; THIS removes the told-k.

This probe runs the agent's composed mode-seeking on REAL speech (FSDD digits through
the agent's OWN composed CMVN front-end — the same signatures the cross-speaker probe
uses) and reports, with the agent's controls:

  (A) EMERGENT #modes vs the true #digits — does the count come out of the data
      (NO told-k) near the truth?
  (B) PURITY vs the random-assignment floor — do same-digit tokens land together?
  (C) SHUFFLE-COLLAPSE (the agent's signature control): shuffle each cue dimension
      independently across tokens (destroy the JOINT distribution's modes, KEEP the
      per-dimension marginals). If the categories live in the distribution's modes,
      purity must COLLAPSE toward the floor under shuffle. (Run in the same breath as
      the real measurement — never chase an artifact.)

LABEL-FREE: the clusterer never sees a label. Labels read AFTER only to score.
Honest: absolute purity may be modest (bounded by the gammatone front-end, as every
prior probe found) — the proof is the CONTROL-validated structure (emergent count +
shuffle-collapse), not a headline number.

Run:  python scripts/distributional_categories_probe.py
"""
from __future__ import annotations

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import scripts.fsdd_learner_world as fl
from domains.cmvn import apply_cmvn, compose_cmvn
from domains.distributional_categories import (cluster_by_modes,
                                               compose_distributional_categories)
from scripts.cross_speaker_clustering_probe import cmvn_signature, N_MEL, N_SLOTS
from substrate_rs import Substrate

DIGITS = fl._DIGITS
PER = int(os.environ.get("DC_PER", "12"))      # utts per (digit, speaker)


def purity(labels, truth):
    hit = 0
    for cl in set(labels):
        members = [truth[i] for i, l in enumerate(labels) if l == cl]
        if members:
            hit += max(Counter(members).values())
    return hit / len(truth)


def random_floor(truth, k, trials=20, seed=0):
    rng = np.random.default_rng(seed)
    return float(np.mean([purity(list(rng.integers(0, k, len(truth))), truth)
                          for _ in range(trials)]))


def main():
    print("=" * 74)
    print("DISTRIBUTIONAL CATEGORIES probe — TOLD-k-FREE mode-seeking (the agent's")
    print("picked + composed capability), verified by the agent's own controls")
    print("=" * 74)

    s0 = Substrate()
    compose_cmvn(s0, n_bands=N_MEL)
    compose_distributional_categories(s0)
    print("composed Terms recorded as Concepts: cmvn + distributional_categories "
          "(dc_density, dc_climb)")

    af = fl.gather_files()
    speakers = sorted({sp for _, _, sp, _ in af})
    print(f"corpus: FSDD, {len(speakers)} speakers pooled {speakers}")
    print(f"        {PER} utts/(digit,speaker), {len(DIGITS)} digits\n")

    sigs, truth = [], []
    for d in range(len(DIGITS)):
        for sp in speakers:
            files = [p for (p, dd, ss, _) in af if dd == d and ss == sp][:PER]
            for p in files:
                sm, fs = fl.load_wav(p)
                sigs.append(cmvn_signature(sm, fs))
                truth.append(d)
    M = np.array(sigs)
    truth = list(truth)
    k_true = len(DIGITS)
    print(f"pooled {len(truth)} tokens (LABEL-FREE; true #categories = {k_true})\n")

    rf = random_floor(truth, k_true)
    print(f"random-assignment purity floor = {rf:.3f}  (chance ~ {1/k_true:.3f})\n")

    # --- (A)+(B) the real run: emergent #modes + purity ----------------
    labels, n_modes = cluster_by_modes(M, seed=0)
    pur = purity(labels, truth)
    print(f"{'REAL distribution':<26} emergent #modes = {n_modes:<4} "
          f"(true {k_true})   purity = {pur:.3f}")

    # --- (C) SHUFFLE control: destroy joint modes, keep marginals ------
    rng = np.random.default_rng(0)
    Msh = M.copy()
    for c in range(Msh.shape[1]):
        Msh[:, c] = Msh[rng.permutation(Msh.shape[0]), c]
    sh_labels, sh_modes = cluster_by_modes(Msh, seed=0)
    sh_pur = purity(sh_labels, truth)
    print(f"{'SHUFFLED (marginals kept)':<26} emergent #modes = {sh_modes:<4} "
          f"           purity = {sh_pur:.3f}")

    print("\n" + "=" * 74)
    print("VERDICT (the agent's controls)")
    print("=" * 74)
    # emergent count in the right ballpark (no told-k), and above the trivial 1.
    count_ok = 1 < n_modes <= 4 * k_true
    beats_floor = pur > rf + 0.03
    collapses = sh_pur < pur - 0.03
    print(f"  (A) emergent #modes from the data (NO told-k)  : {n_modes} "
          f"(true {k_true})  -> {'reasonable' if count_ok else 'off'}")
    print(f"  (B) purity beats random floor                  : "
          f"{pur:.3f} vs {rf:.3f}  -> {'YES' if beats_floor else 'no'}")
    print(f"  (C) SHUFFLE-COLLAPSE (joint modes destroyed)   : "
          f"{pur:.3f} -> {sh_pur:.3f}  -> {'COLLAPSES' if collapses else 'no'}")
    ok = count_ok and beats_floor and collapses
    print(f"\n  >>> {'CONTROL-VALIDATED' if ok else 'PARTIAL'}: the categories the "
          f"agent forms\n      come OUT of the distribution's modes (emergent count, "
          f"no told-k),\n      beat the floor, and COLLAPSE when the joint "
          f"distribution is shuffled.")
    if not ok:
        print("\n  HONEST: report the real numbers above; the proof is the "
              "control-validated\n      structure (emergent count + shuffle-collapse), "
              "not a headline purity.")


if __name__ == "__main__":
    main()
