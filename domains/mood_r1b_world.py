#!/usr/bin/env python3
"""MOOD R1b world adapter (block 237000) — the FAIR persistent-regime world.

R1b re-tests the mood-momentum adaptive gate on a world that has genuine
momentum WITHOUT the mean-reversion that punished it in R1's AR(1). This file
is a MECHANICAL world adapter: it only GENERATES reward sequences (a hidden
two-state regime process + its matched-marginal i.i.d. permutation) and drives
the SAME graph agent R1 built (``domains.mood_r1_world.MoodR1World``, which
loads ``seeds/mood_r1_task.json`` + ``seeds/mood_r1.json`` verbatim) at the
pre-registered lagging learning rate ``lr = 0.1``.

There is NO ``if``/``else`` over graph state and NO Python rule engine here.
Every DECISION — the choice, the value learning, the momentum EMA, the
appraisal feedback — is a graph RULE inside the reused seeds. The regime stream
and its permutation are pure reward-sequence generation (mechanical world I/O).
The WITH-mood and WITHOUT-mood arms are the SAME graph, differing only in
``Mood.enabled`` (1 vs 0).

IMPORT-INERT: nothing runs at import.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.mood_r1_world import MoodR1World      # noqa: E402  (reuse R1 agent)

# ------------------------------------------------------------------------
# Pinned R1b primary configuration (MOOD_R1B_PREREG §4). PINNED BY PRINCIPLE,
# committed before any number.
# ------------------------------------------------------------------------
MU = 1.0            # regime levels are +/- MU (GOOD / BAD)
SIGMA = 0.5         # within-regime reward noise (SNR = 2*MU/SIGMA = 4 sigma sep)
P_SWITCH = 0.05     # per-step regime-switch prob -> geometric dwell, mean 20
LR_LAGGING = 0.1    # THE LAGGING fast-layer lr (the condition the hypothesis is about)
MOMENTUM_LR = 0.3   # eta' — REUSED from R1 unchanged
GAIN = 1.0          # f_t — REUSED from R1 unchanged
ACCEPT_THRESH = 0.0  # accept iff v>0 — REUSED from R1 unchanged
N_TRIALS = 200      # trials per episode
K_EPISODES = 200    # independent episodes
B_BOOT = 10000      # bootstrap resamples


# ------------------------------------------------------- reward-stream world
def regime_stream(rng, n=N_TRIALS, p_switch=P_SWITCH, mu=MU, sigma=SIGMA):
    """A hidden two-state regime (GOOD=+mu, BAD=-mu) that PERSISTS: at each step
    it switches with probability ``p_switch`` (geometric dwell, mean
    ``1/p_switch``), else holds. Within a regime reward ~ N(state*mu, sigma).

    Recent good outcomes PREDICT future good outcomes (persistence) WITHOUT
    mean-reversion — the paper's "natural momentum" (Eldar/Niv 2016). Returns
    ``(r, regimes)`` where ``regimes`` is the +/-1 hidden state per trial.
    """
    r = np.empty(n)
    regimes = np.empty(n, dtype=int)
    state = 1 if rng.random() < 0.5 else -1        # start GOOD/BAD 50/50
    for t in range(n):
        if t > 0 and rng.random() < p_switch:
            state = -state
        regimes[t] = state
        r[t] = state * mu + rng.normal(0.0, sigma)
    return r, regimes


def iid_permute(rng, r):
    """The matched-marginal i.i.d. control: a random permutation of the regime
    stream. A permutation preserves the multiset EXACTLY -> identical marginal
    mean/variance; only the persistence/autocorrelation is destroyed. The two
    worlds differ in autocorrelation and NOTHING else."""
    return rng.permutation(r)


def lag1_autocorr(x):
    x = np.asarray(x, float)
    x = x - x.mean()
    denom = float(np.dot(x, x))
    if denom == 0.0:
        return 0.0
    return float(np.dot(x[:-1], x[1:]) / denom)


# ------------------------------------------------ drive the reused graph agent
def run_arm(stream, mood_enabled, *, lr=LR_LAGGING, momentum_lr=MOMENTUM_LR,
            gain=GAIN, accept_thresh=ACCEPT_THRESH):
    """Run ONE reward stream through the reused R1 graph agent at the pinned
    lagging lr; return the final cumulative reward. Mechanical: create the
    opt-in nodes, deliver r, tick (run_rules), read cum_reward. No decision."""
    w = MoodR1World(mood_enabled=mood_enabled, lr=lr, momentum_lr=momentum_lr,
                    gain=gain, accept_thresh=accept_thresh)
    out = w.run([float(x) for x in stream])
    w.close()
    return out["cum_reward"]


def run_arm_trace(stream, mood_enabled, *, lr=LR_LAGGING, momentum_lr=MOMENTUM_LR,
                  gain=GAIN, accept_thresh=ACCEPT_THRESH):
    """As ``run_arm`` but return the full per-trial trace (for the momentum
    mechanism check / glass-box readouts)."""
    w = MoodR1World(mood_enabled=mood_enabled, lr=lr, momentum_lr=momentum_lr,
                    gain=gain, accept_thresh=accept_thresh)
    out = w.run([float(x) for x in stream])
    ma = w.mood_attrs(); ta = w.task_attrs()
    w.close()
    return out, ma, ta
