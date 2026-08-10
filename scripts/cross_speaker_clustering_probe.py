"""cross-speaker clustering probe — does the capability the agent PICKED close
the gap it synthesized?

The agent (gap_prioritiser) picked CROSS-SPEAKER CLUSTERING as its frontier: the
order-N synthesis derived it from six of its own postulates, and its
compression-payoff criterion ranked it most foundational. It then forward-built it
by COMPOSING the clustering as a graph Term-tree from its own latent_structure
science (domains/cross_speaker_clustering — Argmin nearest-centroid assignment +
Sum/Count centroid mean, the CMVN move lifted from frames to tokens).

This probe MEASURES whether that built capability closes the gap: pool every
speaker's FSDD digit utterances into ONE unlabelled point cloud, run the agent's
composed clustering (k = #digits, LABEL-FREE), and score CLUSTER PURITY against the
held-out true digit labels. Higher purity = the same word's tokens across speakers
land in one cluster = the gap is closed. Two representations, the honest head-to-head:

  baseline   raw absolute-spectrum trajectory (the current representation — what
             shifts with vocal-tract length; the thing CMVN/VTLN try to fix).
  agent      the agent's OWN speaker-invariant signature: per-frame log-mel bands
             passed through the agent's COMPOSED CMVN Term (domains/cmvn), then the
             same trajectory flatten — its own front-end, clustered by its own
             composed clusterer.

LABEL-FREE: the clusterer never sees a label. Labels are read AFTER, only to score
purity (and a random-assignment floor for context). Corpus: FSDD (/tmp/fsdd),
SG_PER utterances per (digit, speaker), all six speakers pooled.

Run:  python scripts/cross_speaker_clustering_probe.py
"""
from __future__ import annotations

import math
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import scripts.fsdd_learner_world as fl
from domains.sound_graph import _voiced_frames, spectrum_signature_traj
from domains.cmvn import apply_cmvn, compose_cmvn
from domains.cross_speaker_clustering import (cluster,
                                             compose_cross_speaker_clustering)
from substrate_rs import Substrate

DIGITS = fl._DIGITS
PER = int(os.environ.get("SG_PER", "10"))     # utterances per (digit, speaker)
N_MEL = 16
N_SLOTS = 6


def _mel_edges(n_mel, lo_hz, hi_hz, fs):
    def hz2mel(f): return 2595.0 * math.log10(1.0 + f / 700.0)
    def mel2hz(m): return 700.0 * (10 ** (m / 2595.0) - 1.0)
    mels = np.linspace(hz2mel(lo_hz), hz2mel(hi_hz), n_mel + 1)
    return mel2hz(mels)


def logmel_frames(samples, fs, n_mel=N_MEL, lo_hz=80.0, hi_hz=3800.0):
    """Per-voiced-frame log-mel band matrix (n_frames x n_mel). The raw per-frame
    representation the agent's CMVN Term then normalizes over time."""
    edges = _mel_edges(n_mel, lo_hz, hi_hz, fs)
    rows = []
    for _, win in _voiced_frames(samples, fs):
        mag = np.abs(np.fft.rfft(win, n=2048)) + 1e-9
        freqs = np.fft.rfftfreq(2048, 1.0 / fs)
        row = []
        for b in range(n_mel):
            m = (freqs >= edges[b]) & (freqs < edges[b + 1])
            row.append(math.log(float(np.mean(mag[m])) + 1e-9) if m.any()
                       else -20.0)
        rows.append(row)
    return np.array(rows) if rows else np.zeros((0, n_mel))


def _traj_flatten(arr, n_slots=N_SLOTS):
    """Resample a (T x bands) matrix to n_slots time points, flatten, unit-norm —
    matched to spectrum_signature_traj so the comparison is fair."""
    if arr.shape[0] == 0:
        return np.zeros(n_slots * arr.shape[1])
    T = arr.shape[0]
    if T == 1:
        out = np.repeat(arr, n_slots, axis=0)
    else:
        xs = np.linspace(0, T - 1, n_slots)
        out = np.stack([np.interp(xs, np.arange(T), arr[:, c])
                        for c in range(arr.shape[1])], axis=1)
    v = out.flatten()
    v = v - v.mean()
    return v / (np.linalg.norm(v) + 1e-9)


def cmvn_signature(samples, fs):
    """The agent's OWN speaker-invariant signature: log-mel frames -> the agent's
    COMPOSED CMVN Term (per-band mean/var removal over time) -> trajectory flatten."""
    M = logmel_frames(samples, fs)
    if M.shape[0] == 0:
        return np.zeros(N_SLOTS * N_MEL)
    Mn = apply_cmvn(M)                 # the agent's composed CMVN Term, evaluated
    return _traj_flatten(Mn)


def purity(labels, truth):
    """Cluster purity: Σ_clusters max-class-count / N. 1.0 = every cluster pure."""
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
    print("=" * 72)
    print("CROSS-SPEAKER CLUSTERING probe — the agent's PICKED + BUILT capability")
    print("=" * 72)

    # The agent records its composed Terms (so they live as Concepts it owns).
    s0 = Substrate()
    compose_cmvn(s0, n_bands=N_MEL)
    compose_cross_speaker_clustering(s0, n_bands=N_SLOTS * N_MEL)
    print("composed Terms recorded as Concepts: cmvn + cross_speaker_clustering")

    af = fl.gather_files()
    speakers = sorted({sp for _, _, sp, _ in af})
    print(f"corpus: FSDD, {len(speakers)} speakers pooled {speakers}")
    print(f"        {PER} utts/(digit,speaker), {len(DIGITS)} digits\n")

    baseline_sigs, agent_sigs, truth, who = [], [], [], []
    for d in range(len(DIGITS)):
        for sp in speakers:
            files = [p for (p, dd, ss, _) in af if dd == d and ss == sp][:PER]
            for p in files:
                sm, fs = fl.load_wav(p)
                baseline_sigs.append(spectrum_signature_traj(sm, fs))
                agent_sigs.append(cmvn_signature(sm, fs))
                truth.append(d)
                who.append(sp)
    truth = list(truth)
    k = len(DIGITS)
    print(f"pooled {len(truth)} tokens across speakers (LABEL-FREE clustering)\n")

    # multiple seeds (k-means is seed-sensitive); report mean +/- spread.
    def run(sigs, name):
        M = np.array(sigs)
        purs = []
        for seed in range(5):
            labels = cluster(M, k=k, seed=seed)
            purs.append(purity(labels, truth))
        return float(np.mean(purs)), float(np.std(purs))

    rf = random_floor(truth, k)
    print(f"random-assignment purity floor = {rf:.3f}   (chance ~ {1/k:.3f})\n")
    print(f"{'representation':<34}{'cluster purity (mean+/-sd over 5 seeds)'}")
    print("-" * 72)
    b_mu, b_sd = run(baseline_sigs, "baseline")
    a_mu, a_sd = run(agent_sigs, "agent")
    print(f"{'raw spectrum trajectory (baseline)':<34}{b_mu:.3f} +/- {b_sd:.3f}")
    print(f"{'agent CMVN-invariant signature':<34}{a_mu:.3f} +/- {a_sd:.3f}")

    print("\n" + "=" * 72)
    print("VERDICT")
    print("=" * 72)
    delta = a_mu - b_mu
    print(f"  agent purity {a_mu:.3f}  vs  baseline {b_mu:.3f}   (delta {delta:+.3f})")
    print(f"  both vs random floor {rf:.3f}")
    if a_mu > b_mu + 0.02:
        print("  -> The agent's invariant front-end + composed clusterer cluster")
        print("     same-digit tokens across speakers BETTER than the raw spectrum.")
        print("     The gap is (partly) closed: cross-speaker clustering now works.")
    elif a_mu > rf + 0.05:
        print("  -> The composed clusterer works (well above random) but its")
        print("     front-end does not beat the raw spectrum here — the clustering")
        print("     mechanism is real; the invariance lever is bounded by the")
        print("     front-end, as the LOSO probe also found. Honest partial close.")
    else:
        print("  -> Clustering near the random floor: the build runs but does not")
        print("     close the gap on this corpus.")


if __name__ == "__main__":
    main()
