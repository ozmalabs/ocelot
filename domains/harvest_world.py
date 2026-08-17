"""HarvestWorld -- a MECHANICAL multi-agent commons adapter (block 212000).

ARCHITECTURE RULE COMPLIANCE (see experiments/gamma-substrate/CLAUDE.md):
this file is a WORLD ADAPTER. It does exactly two things -- ingest and emit --
around `run_rules()`. It contains NO agent decision:

  * the HARVEST amount is chosen by the graph rule `hv_choose_harvest`
    (seeds/harvest_commons.json), an Argmax over candidate Appraisals by
    total_value. This adapter only READS `HarvestDecision.chosen_harvest`.
  * whether to PUNISH is the graph rule `hv_punish`; this adapter only READS
    `want_punish` and TALLIES reproaches mechanically.
  * the sanction magnitude an agent anticipates (Phase 2) is PUBLIC MECHANICS
    (full information): the adapter publishes `future_yield` (collective) and the
    standing enforcer count (sanction) onto each candidate as observations, the
    same for every agent. The agent's VALUATION of them is its w_supergraph knob.

No `graph_rewrite.run` / `_match` / `_apply` / `make_rule`; no `if/else` over an
agent's graph state that selects an agent action. Every conditional here is over
WORLD state (pool level, rationing, regrowth) -- mechanical.
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

# ---- FIXED world constants (pre-registered, HARVEST_EMOTIONAL_SEEDS_PREREG.md §2)
K = 120           # carrying capacity
G_NUM = 2         # logistic regrowth numerator
HMAX = 20         # max harvest per agent per tick
R0 = 100          # starting pool
T_DEFAULT = 40    # ticks
NORM_FRAC_NUM, NORM_FRAC_DEN = 1, 1   # norm = socially-optimal per-capita harvest (computed)
PUNISH_PENALTY = 6   # per-enforcer sanction added to individual_cost of an over-norm level

# HeldEmotionParams / Appraisal defaults (mirror scripts/emotion_phenotype_measure.py)
EP_DEFAULTS = dict(enabled=1.0, w_supergraph=1.0, mood_bias=0.0, residual_thresh=100.0,
                   high_arousal=800.0, mid_arousal=400.0, low_arousal=50.0, comms_on=0.0)
APPR_DEFAULTS = dict(
    appraised=1.0, individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
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
    (mean-field). This is the full-information observation every agent receives
    identically. Falls to 0 when the pool would be emptied (collapse)."""
    rem = R - n * h
    return regrow(rem) if rem > 0 else 0


def socially_optimal_h(R: int, n: int) -> int:
    """The per-capita harvest that maximises immediate individual take + collective
    future yield -- computed purely from the PUBLIC mechanics (this is what a
    prosocial agent's Argmax lands on; used ONLY to set the enforcement norm, a
    world/observation quantity, never to decide an agent's harvest)."""
    best_h, best_v = 0, -1
    for h in range(0, HMAX + 1):
        v = h + future_yield(R, h, n)
        if v > best_v:
            best_v, best_h = v, h
    return best_h


class HarvestWorld:
    """A shared commons over N EmotionHub agents. All agents in ONE substrate,
    all member_of ONE Supergraph, run in ONE run_rules() fixpoint."""

    def __init__(self, w_supergraphs, comms=False, mood_biases=None, enforce=True):
        self.ws = [float(w) for w in w_supergraphs]
        self.n = len(self.ws)
        self.comms = bool(comms)
        # enforce=False -> CHEAP TALK: the norm is professed (statements made) but
        # NOT backed by sanction. Phase 3 uses this to expose stated-vs-held divergence.
        self.enforce = bool(enforce)
        self.moods = list(mood_biases) if mood_biases else [0.0] * self.n
        self.R = R0
        self.coll_prev = 0
        self.yields = [0] * self.n
        self.last_harvest = [0] * self.n
        self.stated = [None] * self.n     # Phase 3: stated intent (filled by measure)

        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("core_emotions"), self.eye._agent)
        self.inner.load_seed_manifest(manifest_for("harvest_commons"), self.eye._agent)

        self.sg = self.s.add_node("Supergraph", {})
        self.hubs, self.decs, self.cands = [], [], []
        for i, w in enumerate(self.ws):
            hub = self.s.add_node("EmotionHub", {})
            ep = dict(EP_DEFAULTS)
            ep.update(w_supergraph=w, mood_bias=float(self.moods[i]),
                      comms_on=1.0 if self.comms else 0.0)
            ep["w_supergraph_q"], ep["w_scale_bits"] = quantize_weight(w)
            epn = self.s.add_node("HeldEmotionParams", ep)
            self.inner.add_edge_unchecked(hub, "has_emotion_params", epn)
            self.inner.add_edge_unchecked(hub, "member_of", self.sg)
            dec = self.s.add_node("HarvestDecision",
                                  {"chosen_harvest": -1.0, "last_harvest": 0.0,
                                   "norm": float(HMAX), "want_punish": 0.0, "n_reproach": 0.0})
            self.inner.add_edge_unchecked(hub, "has_decision", dec)
            cand = []
            for h in range(0, HMAX + 1):
                a = dict(APPR_DEFAULTS)
                a.update(individual_benefit=float(h), harvest_level=float(h))
                apn = self.s.add_node("Appraisal", a)
                self.inner.add_edge_unchecked(hub, "has_appraisal", apn)
                self.inner.add_edge_unchecked(hub, "has_candidate", apn)
                cand.append(apn)
            self.hubs.append(hub)
            self.decs.append(dec)
            self.cands.append(cand)
        # monitoring edges: with comms, every agent monitors every OTHER agent's decision
        if self.comms:
            for i in range(self.n):
                for j in range(self.n):
                    if i != j:
                        self.inner.add_edge_unchecked(self.hubs[i], "monitors", self.decs[j])
        # warm-up fixpoint: the GRAPH decides who enforces (hv_mark_enforcer) and
        # COUNTS them (hv_count_enforcers) onto the Supergraph. Enforcer identity is
        # fixed (w, comms constant), so this count is standing; the adapter READS it.
        self.inner.run_rules()
        self.n_enf = int(self.s.node(self.sg)["attrs"].get("n_enforcers", 0))

    # ---- standing enforcer count, DECIDED and COUNTED by the graph (read-only here)
    def _n_enforcers(self):
        return self.n_enf

    def step(self):
        n = self.n
        norm = socially_optimal_h(self.R, n) if self.comms else HMAX
        n_enf = self._n_enforcers()
        # ---- INGEST: publish PUBLIC mechanics onto every candidate (full information)
        for i in range(n):
            self.s.set_attr(self.decs[i], "norm", float(norm))
            for h in range(0, HMAX + 1):
                c = self.cands[i][h]
                fy = future_yield(self.R, h, n)
                # Phase 2: over-norm harvest carries the anticipated peer sanction
                # (penalty per enforcer). This is PUBLIC info the adapter publishes;
                # whether the agent AVOIDS it is decided by its Argmax (happiness = benefit - cost).
                sanction = (PUNISH_PENALTY * n_enf
                            if (self.comms and self.enforce and h > norm) else 0)
                self.s.set_attr(c, "supergraph_contribution", float(fy))
                self.s.set_attr(c, "individual_cost", float(sanction))
                self.s.set_attr(c, "collective_success", float(self.R))
                self.s.set_attr(c, "collective_success_prev", float(self.coll_prev))
        # ---- TICK: the agents decide, in-graph
        self.inner.run_rules()
        # ---- EMIT: read each agent's own decision
        demands = [max(0, int(self.s.node(d)["attrs"]["chosen_harvest"])) for d in self.decs]
        # ---- apply to the shared pool (mechanical rationing)
        D = sum(demands)
        if D <= self.R:
            got = list(demands)
        else:
            got = [(d * self.R) // max(D, 1) for d in demands]
        for i in range(n):
            self.yields[i] += got[i]
            self.last_harvest[i] = demands[i]
            self.s.set_attr(self.decs[i], "last_harvest", float(demands[i]))
        self.R -= sum(got)
        self.coll_prev = self.R
        self.R = min(K, self.R + regrow(self.R))
        return dict(pool=self.R, demands=demands, got=got, norm=norm)

    def stated_vs_held(self):
        """Phase 3 read-off: per agent, (w_supergraph, stated_harvest, held_harvest,
        gap = held - stated). STATED is the graph-professed norm compliance
        (hv_state_intent); HELD is the graph's Argmax (chosen_harvest). gap>0 =
        says-restraint-holds-grab = deception. Requires a step() first."""
        rows = []
        for i, d in enumerate(self.decs):
            a = self.s.node(d)["attrs"]
            stated = a.get("stated_harvest", None)
            held = max(0, int(a.get("chosen_harvest", 0)))
            if stated is None:
                continue
            stated = int(stated)
            rows.append(dict(w=self.ws[i], stated=stated, held=held, gap=held - stated))
        return rows

    def run(self, T=T_DEFAULT):
        trace = []
        for _ in range(T):
            trace.append(self.step())
        return trace

    def outcome(self, T=T_DEFAULT):
        trace = self.run(T)
        gini = _gini(self.yields)
        return dict(final_pool=self.R, total_yield=sum(self.yields),
                    sustained=1 if self.R >= K // 2 else 0,
                    equality=round(1.0 - gini, 4), gini=round(gini, 4),
                    per_agent_yield=list(self.yields), trace_final=trace[-1])

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass


def _gini(xs):
    xs = [max(0, x) for x in xs]
    s = sum(xs)
    if s == 0 or len(xs) < 2:
        return 0.0
    xs = sorted(xs)
    n = len(xs)
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2.0 * cum) / (n * s) - (n + 1.0) / n
