"""MarshmallowWorld -- a MECHANICAL delay-of-gratification adapter (block 240000).

ARCHITECTURE RULE COMPLIANCE (see experiments/gamma-substrate/CLAUDE.md):
this file is a WORLD ADAPTER. It does exactly two things -- ingest and emit --
around `run_rules()`. It contains NO agent decision:

  * the WAIT/TAKE choice is the graph rule `mm_choose`
    (seeds/marshmallow_delay.json), an Argmax over two candidate Appraisals
    (wait, take) by total_value, decided over the 204000 core_emotions value
    economy. This adapter only READS `DelayDecision.chosen_action`.
  * TEMPERAMENT is `Drive.weight` (the 207000 time-cost drive node); the
    RELIABILITY-PRIOR is `DelayDecision.reliability_prior`. Both are node ATTRS
    the RULE reads -- this adapter only SETS them (mechanical world setup, data)
    and SWEEPS `DelayDecision.elapsed` to read off the tick at which the graph's
    own Argmax flips from wait to take.

No `graph_rewrite.run` / `_match` / `_apply` / `make_rule`; no `if/else` over an
agent's graph state that selects an agent action. The only conditionals here are
over WORLD state (loop bounds, "has this agent flipped yet") -- mechanical emit.
No reward/punishment shaping: the reliability_prior is a fixed belief attr, never
updated from experienced outcomes.
"""
from __future__ import annotations
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from domains.photon_eye import GraphEye              # noqa: E402
from substrate.seed_loader import manifest_for       # noqa: E402
from domains.core_emotions_weight import quantize_weight  # noqa: E402

# ---- FIXED world constants (pre-registered, MARSHMALLOW_DELAY_PREREG.md §2) ----
DELAYED_REWARD = 200     # L: the delayed larger reward (two marshmallows)
IMMEDIATE_SMALL = 101    # S: the immediate small reward (one; ODD -> tie-free)
COST_PER_TICK = 2        # C: base time-cost per tick (EVEN -> tie-free)
PRIOR_SCALE = 100        # reliability_prior expressed as a percent 0..100
DELAY_CAP = 200          # D: max ticks the agent may hold out (full-wait cap)

# HeldEmotionParams / Appraisal defaults (mirror scripts/emotion_phenotype_measure.py
# and domains/harvest_world.py so the core_emotions rules have every attr they read).
EP_DEFAULTS = dict(enabled=1.0, w_supergraph=0.0, mood_bias=0.0, residual_thresh=100.0,
                   high_arousal=800.0, mid_arousal=400.0, low_arousal=50.0, comms_on=0.0)
APPR_DEFAULTS = dict(
    appraised=1.0, individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
    collective_success=0.0, collective_success_prev=0.0, contribution_by_self=0.0,
    observed_by_other=0.0, valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
    attachment=0.0, regroundable=0.0, contamination=0.0, was_engaged=0.0,
    residual=0.0, residual_prev=0.0, threat=0.0, threat_c0=0.0, threat_half_life=1.0,
    threat_last_refresh=0.0, threat_now_epoch=0.0, t_present=100.0, v_max=0.0,
    step=0.0, step_prev=0.0, attach_v0=0.0, attach_k_now=0.0, attach_k_prev=0.0)


def predicted_wait_time(prior, temperament, *, L=DELAYED_REWARD, S=IMMEDIATE_SMALL,
                        C=COST_PER_TICK, scale=PRIOR_SCALE, D=DELAY_CAP):
    """The ANALYTIC wait-time from the value formula (MARSHMALLOW_DELAY_PREREG.md
    §2/§3) -- a PURE-ARITHMETIC oracle, not a substrate run. Used only to CHECK the
    graph's own swept decision against the pre-registered prediction.
    take when P*L/scale - C*w*t <= S  ->  t >= (E - S)/(C*w).
    Tie-free (E even, S odd) so the boundary is strict and integer-unambiguous."""
    E = (int(prior) * int(L)) // int(scale)
    if E <= S:
        return 0
    w = int(temperament)
    step = int(C) * w
    # first integer t with E - step*t < S  (strict; never == because parity differs)
    t = 0
    while E - step * t >= S:
        t += 1
        if t >= D:
            return D
    return t


class MarshmallowWorld:
    """N delay-of-gratification agents in ONE substrate. Each agent is an
    EmotionHub + HeldEmotionParams + a time-cost Drive (weight = temperament) +
    a DelayDecision (reliability_prior belief) + two candidate Appraisals
    (wait/take). The choice is the graph rule mm_choose over core_emotions."""

    def __init__(self, temperaments, priors, *, L=DELAYED_REWARD, S=IMMEDIATE_SMALL,
                 C=COST_PER_TICK, prior_scale=PRIOR_SCALE, D=DELAY_CAP):
        assert len(temperaments) == len(priors)
        self.temperaments = [int(w) for w in temperaments]
        self.priors = [int(p) for p in priors]
        self.n = len(self.priors)
        self.L, self.S, self.C, self.scale, self.D = int(L), int(S), int(C), int(prior_scale), int(D)

        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("core_emotions"), self.eye._agent)
        self.inner.load_seed_manifest(manifest_for("marshmallow_delay"), self.eye._agent)

        self.hubs, self.drives, self.decs, self.waits, self.takes = [], [], [], [], []
        for i in range(self.n):
            hub = self.s.add_node("EmotionHub", {})
            ep = dict(EP_DEFAULTS)
            ep["w_supergraph_q"], ep["w_scale_bits"] = quantize_weight(ep["w_supergraph"])
            epn = self.s.add_node("HeldEmotionParams", ep)
            self.inner.add_edge_unchecked(hub, "has_emotion_params", epn)
            # the TIME-COST DRIVE (block 207000 node type); weight = TEMPERAMENT
            drive = self.s.add_node("Drive", {"name": "time_cost", "is_time_cost": 1.0,
                                              "weight": float(self.temperaments[i])})
            self.inner.add_edge_unchecked(hub, "has_time_drive", drive)
            dec = self.s.add_node("DelayDecision", {
                "reliability_prior": float(self.priors[i]),
                "delayed_reward": float(self.L), "immediate_small": float(self.S),
                "cost_per_tick": float(self.C), "prior_scale": float(self.scale),
                "delay": float(self.D), "elapsed": 0.0, "chosen_action": -1.0})
            self.inner.add_edge_unchecked(hub, "has_delay_decision", dec)
            wa = dict(APPR_DEFAULTS); wa.update(action=1.0)
            wait = self.s.add_node("Appraisal", wa)
            self.inner.add_edge_unchecked(hub, "has_appraisal", wait)
            self.inner.add_edge_unchecked(hub, "has_candidate", wait)
            ta = dict(APPR_DEFAULTS); ta.update(action=0.0)
            take = self.s.add_node("Appraisal", ta)
            self.inner.add_edge_unchecked(hub, "has_appraisal", take)
            self.inner.add_edge_unchecked(hub, "has_candidate", take)
            self.hubs.append(hub); self.drives.append(drive); self.decs.append(dec)
            self.waits.append(wait); self.takes.append(take)

    def _chosen_at(self, t):
        """Set elapsed=t on every DelayDecision, tick the graph, read each agent's
        own chosen_action (1=wait, 0=take). MECHANICAL: set data, run_rules, read."""
        for d in self.decs:
            self.s.set_attr(d, "elapsed", float(t))
        self.inner.run_rules()
        return [int(self.s.node(d)["attrs"]["chosen_action"]) for d in self.decs]

    def wait_times(self):
        """Per agent, the tick at which the graph's OWN Argmax first flips from
        wait(1) to take(0) -- the emergent wait-time. Swept from elapsed=0 upward;
        wait value is monotone-decreasing so once flipped it stays flipped
        (early-stop when all agents have taken). Capped at the delay D
        (a never-flipping agent waits the full delay)."""
        wt = [None] * self.n
        for t in range(0, self.D + 1):
            chosen = self._chosen_at(t)
            for i, ch in enumerate(chosen):
                if wt[i] is None and ch == 0:
                    wt[i] = t
            if all(x is not None for x in wt):
                break
        return [x if x is not None else self.D for x in wt]

    def glass_box(self, i, t=None):
        """Read the decisive state of agent i straight from the graph (the attrs a
        graph_to_dict dump exposes): temperament (drive weight), reliability-prior,
        elapsed, chosen_action, and both candidate total_values. If t is given the
        graph is ticked at that elapsed first."""
        if t is not None:
            self._chosen_at(t)
        d = self.s.node(self.decs[i])["attrs"]
        return dict(
            temperament=self.s.node(self.drives[i])["attrs"]["weight"],
            reliability_prior=d["reliability_prior"],
            elapsed=d["elapsed"], chosen_action=int(d["chosen_action"]),
            wait_total_value=self.s.node(self.waits[i])["attrs"].get("total_value"),
            take_total_value=self.s.node(self.takes[i])["attrs"].get("total_value"))

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
