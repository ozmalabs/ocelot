#!/usr/bin/env python3
"""MOOD R1 world adapter (block 236000) — MECHANICAL, no agent decision.

A one-offer-per-trial accept/decline world. Each trial the adapter delivers a
scalar reward ``r_t``, bumps ``input_epoch``, calls ``run_rules()``, and reads
``decision`` / ``cum_reward`` back off the graph. Every DECISION — the choice,
the value learning, the momentum EMA, the appraisal feedback — is a graph RULE
(``seeds/mood_r1_task.json`` + ``seeds/mood_r1.json``). This file only creates
the opt-in nodes, sets ``r`` + ``input_epoch``, ticks, and reads. There is NO
``if``/``else`` over graph state, NO Python rule engine.

The WITH-mood and WITHOUT-mood arms are the SAME graph; the ONLY difference is
``Mood.enabled`` (1 vs 0). With ``enabled=0`` the mood rules never fire, ``bias``
stays 0, and ``mt_learn`` is a plain delta rule — the otherwise-identical agent.

IMPORT-INERT: nothing runs at import.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.photon_eye import GraphEye            # noqa: E402
from substrate.seed_loader import manifest_for     # noqa: E402

# Pinned R1 primary configuration (MOOD_R1_PREREG §3).
LR = 0.3            # value delta-rule learning rate (the fast appraisal)
MOMENTUM_LR = 0.3   # momentum EMA rate (eta')
GAIN = 1.0          # f_t: momentum -> appraisal feedback sensitivity
ACCEPT_THRESH = 0.0  # accept the offer iff v > 0

MT_DEFAULTS = dict(
    v=0.0, lr=LR, r=0.0, raw_rpe=0.0, bias=0.0,
    decision=0.0, reward_got=0.0, cum_reward=0.0,
    accept_thresh=ACCEPT_THRESH, input_epoch=0.0,
    e_dec=-1.0, e_acc=-1.0, e_rpe=-1.0, e_learn=-1.0)

MOOD_DEFAULTS = dict(
    enabled=0.0, momentum=0.0, gain=GAIN, momentum_lr=MOMENTUM_LR,
    e_bias=-1.0, e_mom=-1.0)


class MoodR1World:
    """One MoodTask + Mood under one EmotionHub. ``step(r)`` runs one trial."""

    def __init__(self, mood_enabled: bool, *, lr=LR, momentum_lr=MOMENTUM_LR,
                 gain=GAIN, accept_thresh=ACCEPT_THRESH):
        self.eye = GraphEye(n_az=2, n_el=2, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("mood_r1_task"), self.eye._agent)
        self.inner.load_seed_manifest(manifest_for("mood_r1"), self.eye._agent)

        self.hub = self.s.add_node("EmotionHub", {})
        mt = dict(MT_DEFAULTS); mt.update(lr=float(lr), accept_thresh=float(accept_thresh))
        self.mt = self.s.add_node("MoodTask", mt)
        self.inner.add_edge_unchecked(self.hub, "has_mood_task", self.mt)

        md = dict(MOOD_DEFAULTS)
        md.update(enabled=1.0 if mood_enabled else 0.0,
                  momentum_lr=float(momentum_lr), gain=float(gain))
        self.mood = self.s.add_node("Mood", md)
        self.inner.add_edge_unchecked(self.hub, "has_mood", self.mood)

        self._epoch = 0

    # -- mechanical trial: deliver r, tick, read back -----------------------
    def step(self, r: float) -> dict:
        self._epoch += 1
        self.s.set_attr(self.mt, "r", float(r))
        self.s.set_attr(self.mt, "input_epoch", float(self._epoch))
        self.inner.run_rules()
        a = self.s.node(self.mt)["attrs"]
        return dict(decision=int(a["decision"]), reward_got=float(a["reward_got"]),
                    cum_reward=float(a["cum_reward"]), v=float(a["v"]),
                    raw_rpe=float(a["raw_rpe"]), bias=float(a["bias"]),
                    momentum=float(self.s.node(self.mood)["attrs"]["momentum"]))

    def run(self, stream) -> dict:
        """Run a whole reward stream; return final readouts + per-trial trace."""
        trace = []
        for r in stream:
            trace.append(self.step(r))
        return dict(cum_reward=trace[-1]["cum_reward"] if trace else 0.0,
                    momentum=trace[-1]["momentum"] if trace else 0.0,
                    trace=trace)

    def mood_attrs(self) -> dict:
        return dict(self.s.node(self.mood)["attrs"])

    def task_attrs(self) -> dict:
        return dict(self.s.node(self.mt)["attrs"])

    def close(self):
        self.eye.stop()
