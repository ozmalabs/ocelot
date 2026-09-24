"""HarvestSpiteWorld -- a MECHANICAL commons adapter for block 213000 (SPITE + SKILL).

Extends the 212000 HARVEST commons with two NEW knobs, BOTH graph data on
``seeds/spite_skill.json`` (read by the rule ``ss_decision_value``):

  * ``w_spite``  -- the negative-social MIRROR of ``w_supergraph``. A spiteful
    agent (w_spite>0) VALUES the harm a self-costly BURN inflicts on others
    (published ``burn_harm``). Sign-only, exactly like ``w_supergraph``.
  * ``order_n``  -- planning depth. Gates whether the anticipated N-step SANCTION
    (published ``individual_cost``) enters ``decision_value``. order_n=0 (myopic)
    ignores it; order_n>=1 (strategic) includes it.

ARCHITECTURE RULE COMPLIANCE (see experiments/gamma-substrate/CLAUDE.md): this
file is a WORLD ADAPTER. It does exactly two things -- ingest and emit -- around
``run_rules()``. It contains NO agent decision:

  * the HARVEST amount is chosen by the graph rule ``ss_choose_harvest`` (Argmax
    over candidate Appraisals by ``decision_value``); this adapter READS
    ``chosen_harvest2``.
  * whether to BURN (destroy) is the SAME Argmax, read by ``ss_choose_burn``;
    this adapter READS ``chosen_burn`` and applies the waste to the shared pool.
  * the sanction an agent anticipates and the harm a burn inflicts are PUBLIC
    mechanics (full information) the adapter publishes onto candidates as
    observations, the SAME for every agent. The agent's VALUATION of them is its
    ``order_n`` / ``w_spite`` knob (graph data), not this file.

No ``graph_rewrite.run`` / ``gr.run`` / ``_match`` / ``_apply`` / ``make_rule``;
no ``if``/``else`` over an agent's graph state that selects an agent action.
Every conditional here is over WORLD state (pool level, rationing, over-norm,
enforcement present) -- mechanical.
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

# ---- FIXED world constants (pre-registered, SPITE_SKILL_PREREG.md) -- mirror 212000
K = 120           # carrying capacity
G_NUM = 2         # logistic regrowth numerator
HMAX = 20         # max harvest per agent per tick
R0 = 100          # starting pool
T_DEFAULT = 40    # ticks
BURN_COST = 2     # self-cost of a burn action (encoded as negative individual_benefit)
BURN_D = 30       # pool units a burn WASTES (denied to everyone, self takes 0)

# HeldEmotionParams / Appraisal defaults (mirror 212000 harvest_world.py + two knobs)
EP_DEFAULTS = dict(enabled=1.0, w_supergraph=1.0, w_spite=0.0, order_n=1.0,
                   skill_spite_on=1.0, mood_bias=0.0, residual_thresh=100.0,
                   high_arousal=800.0, mid_arousal=400.0, low_arousal=50.0, comms_on=0.0)
APPR_DEFAULTS = dict(
    appraised=1.0, individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
    burn_harm=0.0, harvest_level=0.0, burn_level=0.0,
    collective_success=0.0, collective_success_prev=0.0, contribution_by_self=0.0,
    observed_by_other=0.0, valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
    attachment=0.0, regroundable=0.0, contamination=0.0, was_engaged=0.0,
    residual=0.0, residual_prev=0.0, threat=0.0, threat_c0=0.0, threat_half_life=1.0,
    threat_last_refresh=0.0, threat_now_epoch=0.0, t_present=100.0, v_max=0.0,
    step=0.0, step_prev=0.0, attach_v0=0.0, attach_k_now=0.0, attach_k_prev=0.0)


def regrow(R: int) -> int:
    """Density-dependent logistic regrowth (integer). Empty commons never recovers."""
    if R <= 0:
        return 0
    return max((G_NUM * R * (K - R)) // K, 0)


def future_yield(R: int, h: int, n: int) -> int:
    """PUBLIC mechanics: collective regrowth if all n agents harvest at rate h
    (mean-field), full-information observation. 0 when the pool would be emptied."""
    rem = R - n * h
    return regrow(rem) if rem > 0 else 0


def socially_optimal_h(R: int, n: int) -> int:
    """Per-capita harvest maximising immediate take + collective future yield,
    from PUBLIC mechanics -- used ONLY to set the enforcement norm (a world
    quantity), never to decide an agent's harvest."""
    best_h, best_v = 0, -1
    for h in range(0, HMAX + 1):
        v = h + future_yield(R, h, n)
        if v > best_v:
            best_v, best_h = v, h
    return best_h


class HarvestSpiteWorld:
    """A shared commons over N EmotionHub agents with SPITE and SKILL knobs. All
    agents in ONE substrate, all member_of ONE Supergraph, ONE run_rules()
    fixpoint. Enforcement is an INSTITUTIONAL world parameter (a fixed sanction on
    over-norm harvest), published mechanically -- cleanly isolating the order_n
    response from population composition (in 212000 the sanction was endogenous to
    the enforcer count; the value economy is identical, only the SOURCE differs)."""

    def __init__(self, w_supergraphs, w_spites=None, order_ns=None,
                 comms=False, enforcement=0, mood_biases=None):
        self.ws = [float(w) for w in w_supergraphs]
        self.n = len(self.ws)
        self.wsp = [float(x) for x in (w_spites if w_spites is not None else [0.0] * self.n)]
        self.ons = [float(x) for x in (order_ns if order_ns is not None else [1.0] * self.n)]
        self.comms = bool(comms)
        self.enforcement = int(enforcement)   # institutional sanction magnitude
        self.moods = list(mood_biases) if mood_biases else [0.0] * self.n
        self.R = R0
        self.coll_prev = 0
        self.yields = [0] * self.n
        self.burned_by = [0] * self.n
        self.last_harvest = [0] * self.n
        self.last_burn = [0] * self.n

        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("core_emotions"), self.eye._agent)
        self.inner.load_seed_manifest(manifest_for("spite_skill"), self.eye._agent)

        self.sg = self.s.add_node("Supergraph", {})
        self.hubs, self.decs, self.cands, self.burn_cand = [], [], [], []
        for i in range(self.n):
            hub = self.s.add_node("EmotionHub", {})
            ep = dict(EP_DEFAULTS)
            ep.update(w_supergraph=self.ws[i], w_spite=self.wsp[i], order_n=self.ons[i],
                      mood_bias=float(self.moods[i]),
                      comms_on=1.0 if self.comms else 0.0)
            ep["w_supergraph_q"], ep["w_scale_bits"] = quantize_weight(self.ws[i])
            epn = self.s.add_node("HeldEmotionParams", ep)
            self.inner.add_edge_unchecked(hub, "has_emotion_params", epn)
            self.inner.add_edge_unchecked(hub, "member_of", self.sg)
            dec = self.s.add_node("HarvestDecision",
                                  {"chosen_harvest2": -1.0, "chosen_burn": -1.0,
                                   "last_harvest": 0.0, "norm": float(HMAX)})
            self.inner.add_edge_unchecked(hub, "has_decision", dec)
            cand = []
            for h in range(0, HMAX + 1):
                a = dict(APPR_DEFAULTS)
                a.update(individual_benefit=float(h), harvest_level=float(h), burn_level=0.0)
                apn = self.s.add_node("Appraisal", a)
                self.inner.add_edge_unchecked(hub, "has_appraisal", apn)
                self.inner.add_edge_unchecked(hub, "has_candidate", apn)
                cand.append(apn)
            # the BURN (destroy) candidate: self takes 0, pays BURN_COST, wastes BURN_D
            b = dict(APPR_DEFAULTS)
            b.update(individual_benefit=float(-BURN_COST), harvest_level=0.0,
                     burn_level=float(BURN_D), burn_harm=float(BURN_D))
            bpn = self.s.add_node("Appraisal", b)
            self.inner.add_edge_unchecked(hub, "has_appraisal", bpn)
            self.inner.add_edge_unchecked(hub, "has_candidate", bpn)
            self.hubs.append(hub)
            self.decs.append(dec)
            self.cands.append(cand)
            self.burn_cand.append(bpn)

    def step(self):
        n = self.n
        norm = socially_optimal_h(self.R, n) if self.comms else HMAX
        # over-norm harvest carries the anticipated INSTITUTIONAL sanction (public).
        for i in range(n):
            self.s.set_attr(self.decs[i], "norm", float(norm))
            for h in range(0, HMAX + 1):
                c = self.cands[i][h]
                fy = future_yield(self.R, h, n)
                sanction = (self.enforcement if (self.comms and self.enforcement > 0 and h > norm) else 0)
                self.s.set_attr(c, "supergraph_contribution", float(fy))
                self.s.set_attr(c, "individual_cost", float(sanction))
                self.s.set_attr(c, "collective_success", float(self.R))
                self.s.set_attr(c, "collective_success_prev", float(self.coll_prev))
            # the burn candidate: collective yield if self takes 0 but pool loses BURN_D
            bc = self.burn_cand[i]
            rem = max(self.R - BURN_D, 0)
            self.s.set_attr(bc, "supergraph_contribution", float(regrow(rem)))
            self.s.set_attr(bc, "individual_cost", 0.0)
            self.s.set_attr(bc, "collective_success", float(self.R))
            self.s.set_attr(bc, "collective_success_prev", float(self.coll_prev))
        # ---- TICK: the agents decide, in-graph
        self.inner.add_node("NativeHarvestSpiteReceipt", {
            "schema": "native_harvest_spite_receipt_v1",
            "cluster": "harvest_spite.decision_settlement",
            "provenance": "native_rule_readback:harvest_spite",
            "native_rule": "harvest_spite_native_rules",
            "native_steps": ["write_world_state", "run_rules", "readback"],
            "outcome_source": "native_rule_readback",
            "python_outcome_selection": False,
        })
        self.inner.run_rules()
        # ---- EMIT: read each agent's own decision (self-take + burn)
        demands = [max(0, int(self.s.node(d)["attrs"]["chosen_harvest2"])) for d in self.decs]
        burns = [max(0, int(self.s.node(d)["attrs"]["chosen_burn"])) for d in self.decs]
        # ---- apply to the shared pool (mechanical rationing across ALL draws)
        draws = [demands[i] + burns[i] for i in range(n)]
        D = sum(draws)
        if D <= self.R:
            got = list(draws)
        else:
            got = [(d * self.R) // max(D, 1) for d in draws]
        for i in range(n):
            # self keeps only its harvest share; burned units are wasted
            drawn = draws[i]
            if drawn > 0:
                h_share = (got[i] * demands[i]) // drawn
            else:
                h_share = 0
            self.yields[i] += h_share
            self.burned_by[i] += (got[i] - h_share)
            self.last_harvest[i] = demands[i]
            self.last_burn[i] = burns[i]
            self.s.set_attr(self.decs[i], "last_harvest", float(demands[i]))
        self.R -= sum(got)
        self.coll_prev = self.R
        self.R = min(K, self.R + regrow(self.R))
        return dict(pool=self.R, demands=demands, burns=burns, got=got, norm=norm)

    def decisions(self):
        """Read-off (requires a step() first): per agent, its knobs and its held
        decision -- whether it chose to BURN (chosen_burn>0) and its self-harvest."""
        rows = []
        for i, d in enumerate(self.decs):
            a = self.s.node(d)["attrs"]
            rows.append(dict(
                w_supergraph=self.ws[i], w_spite=self.wsp[i], order_n=self.ons[i],
                chosen_harvest=max(0, int(a.get("chosen_harvest2", 0))),
                chosen_burn=max(0, int(a.get("chosen_burn", 0))),
                burns=1 if int(a.get("chosen_burn", 0)) > 0 else 0))
        return rows

    def run(self, T=T_DEFAULT):
        return [self.step() for _ in range(T)]

    def outcome(self, T=T_DEFAULT):
        trace = self.run(T)
        return dict(final_pool=self.R, total_yield=sum(self.yields),
                    sustained=1 if self.R >= K // 2 else 0,
                    total_burned=sum(self.burned_by),
                    per_agent_yield=list(self.yields), per_agent_burned=list(self.burned_by),
                    trace_final=trace[-1])

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
