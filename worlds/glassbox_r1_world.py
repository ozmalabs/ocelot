"""GlassBoxR1World -- a MECHANICAL grounded-trade world adapter (block 234000).

GLASS-BOX SOCIETY R1: "language is a coordination technology."

ARCHITECTURE RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md): this file
is a WORLD ADAPTER. It does exactly two things -- ingest and emit -- around
`run_rules()`. It contains NO agent decision:

  * whether an agent GIVES or KEEPS is the graph rule `gb_choose_give`
    (seeds/glassbox_r1_social.json), an Argmax over the agent's two candidate
    Appraisals by total_value (= happiness + fulfilment_value, the LANDED
    core_emotions value economy). This adapter only READS `TradeDecision.chosen_give`.
  * whether an agent PROMISES (professes it will give) is the graph rule
    `gb_state_promise`; this adapter only READS `TradeDecision.stated_give` and
    materialises a readable Promise node from it (mechanical I/O).

The adapter publishes the WORLD's payoff mechanics onto each candidate as
full-information observations (exactly as HARVEST publishes future_yield/sanction):
individual_benefit and supergraph_contribution per candidate, conditioned on the
WORLD fact `promise_in` (does a partner's binding promise exist for me this
encounter?). It does NOT decide the agent's valuation -- that is the w_supergraph
knob and the Argmax.

No `graph_rewrite.run` / `gr.run` / `_match` / `_apply` / `make_rule`; no `if/else`
over an agent's graph valuation that selects an agent action. Every conditional
here is over WORLD state (position, holding, encounter, comms) -- mechanical.
"""
from __future__ import annotations
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np                                     # noqa: E402
from domains.photon_eye import GraphEye                # noqa: E402
from substrate.seed_loader import manifest_for         # noqa: E402

# ---- FIXED world constants (pre-registered, GLASS_BOX_R1_PREREG.md §2/§4) ----
N_DEFAULT = 8      # agents (4 hold X, 4 hold Y)
P_RING = 5         # ring positions (small -> frequent encounters)
T_DEFAULT = 30     # ticks

# The value economy (declared CONFIGURATION -- world mechanics, never a verdict
# threshold). Published onto candidates; the DECISION is the seed-weighted Argmax.
V_BOTH = 7         # hold own + received partner's (defector's prize) -> KEEP w/ promise
V_NEED = 6         # hold the needed resource (successful trade)      -> GIVE w/ promise
V_OWN = 4          # hold own unneeded resource (autarky / no-trade)  -> KEEP, no promise
V_ALONE = 0        # gave own, got nothing (the sucker)               -> GIVE, no promise
G_CONTRIB = 3      # supergraph_contribution when my give hands a partner its need

# HeldEmotionParams / Appraisal defaults (mirror domains/harvest_world.py so the
# core_emotions rules find every atom they read).
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


class GlassBoxR1World:
    """N EmotionHub agents on a ring, all in ONE substrate, all member_of ONE
    Supergraph, running in ONE run_rules() fixpoint. Complementary resources
    (type X needs Y, type Y needs X); trade mediated by promises."""

    def __init__(self, w_supergraphs, comms=False, seed=0):
        self.ws = [float(w) for w in w_supergraphs]
        self.n = len(self.ws)
        self.comms = bool(comms)
        self.rng = np.random.default_rng(seed)
        # resource holdings: even index holds X(0)/needs Y(1); odd holds Y/needs X.
        self.holds = [0 if i % 2 == 0 else 1 for i in range(self.n)]
        self.needs = [1 - h for h in self.holds]
        # spatial: random start position on the ring.
        self.pos = [int(self.rng.integers(0, P_RING)) for _ in range(self.n)]

        self.eye = GraphEye(n_az=4, n_el=4, adapt_rate=0.15,
                            context={"retina_2d": True, "synchronous": True,
                                     "worker_capacity": 1}).build()
        self.s = self.eye.substrate
        self.inner = self.s._inner
        self.inner.load_seed_manifest(manifest_for("core_emotions"), self.eye._agent)
        self.inner.load_seed_manifest(manifest_for("glassbox_r1_social"), self.eye._agent)

        self.sg = self.s.add_node("Supergraph", {})
        self.hubs, self.decs, self.give_c, self.keep_c = [], [], [], []
        for i, w in enumerate(self.ws):
            hub = self.s.add_node("EmotionHub", {})
            ep = dict(EP_DEFAULTS)
            ep.update(w_supergraph=w, comms_on=1.0 if self.comms else 0.0)
            epn = self.s.add_node("HeldEmotionParams", ep)
            self.inner.add_edge_unchecked(hub, "has_emotion_params", epn)
            self.inner.add_edge_unchecked(hub, "member_of", self.sg)
            dec = self.s.add_node("TradeDecision",
                                  {"chosen_give": -1.0, "stated_give": 0.0,
                                   "promise_in": 0.0, "holds": float(self.holds[i]),
                                   "needs": float(self.needs[i])})
            self.inner.add_edge_unchecked(hub, "has_decision", dec)
            # two candidates: GIVE (give_level 1), KEEP (give_level 0)
            gv = dict(APPR_DEFAULTS); gv.update(give_level=1.0)
            kp = dict(APPR_DEFAULTS); kp.update(give_level=0.0)
            gvn = self.s.add_node("Appraisal", gv)
            kpn = self.s.add_node("Appraisal", kp)
            for apn in (gvn, kpn):
                self.inner.add_edge_unchecked(hub, "has_appraisal", apn)
                self.inner.add_edge_unchecked(hub, "has_candidate", apn)
            self.hubs.append(hub)
            self.decs.append(dec)
            self.give_c.append(gvn)
            self.keep_c.append(kpn)

        # accumulators / glass-box ledger
        self.total_welfare = 0.0
        self.n_encounters = 0
        self.tick = 0
        # per-agent promise stats (for G-deception, keyed by agent index)
        self.promises_made = [0] * self.n
        self.promises_kept = [0] * self.n
        self.promise_nodes = []   # readable Promise node ids (glass-box)
        self.trade_log = []       # per-encounter reconstruction

    # ---- mechanical: one random-walk step on the ring ----
    def _walk(self):
        for i in range(self.n):
            step = int(self.rng.integers(-1, 2))   # -1, 0, +1
            self.pos[i] = (self.pos[i] + step) % P_RING

    # ---- mechanical: complementary encounters (co-located, mutual need) ----
    def _encounters(self):
        by_cell = {}
        for i in range(self.n):
            by_cell.setdefault(self.pos[i], []).append(i)
        pairs = []
        for cell, members in by_cell.items():
            xs = [m for m in members if self.holds[m] == 0]
            ys = [m for m in members if self.holds[m] == 1]
            # deterministic pairing within a cell (order by index); each agent
            # trades at most once per tick.
            for a, b in zip(sorted(xs), sorted(ys)):
                pairs.append((a, b))
        return pairs

    def _publish_candidates(self, i, promise_in):
        """Publish the WORLD payoff mechanics onto agent i's GIVE/KEEP candidates
        (full information). promise_in is a WORLD fact (a partner's binding promise
        exists), NOT an agent decision."""
        gv_ben = V_NEED if promise_in else V_ALONE
        kp_ben = V_BOTH if promise_in else V_OWN
        self.s.set_attr(self.give_c[i], "individual_benefit", float(gv_ben))
        self.s.set_attr(self.give_c[i], "supergraph_contribution", float(G_CONTRIB))
        self.s.set_attr(self.keep_c[i], "individual_benefit", float(kp_ben))
        self.s.set_attr(self.keep_c[i], "supergraph_contribution", 0.0)
        self.s.set_attr(self.decs[i], "promise_in", 1.0 if promise_in else 0.0)

    def step(self):
        self.tick += 1
        self._walk()
        pairs = self._encounters()
        # ---- INGEST: publish payoff mechanics onto every encountered agent.
        # Under comms an encountered partner will PROMISE (gb_state_promise fires
        # unconditionally under comms) -> a binding promise exists -> promise_in.
        promise_in = 1.0 if self.comms else 0.0
        involved = set()
        for a, b in pairs:
            involved.add(a); involved.add(b)
            self._publish_candidates(a, promise_in)
            self._publish_candidates(b, promise_in)
        # ---- TICK: the agents decide, in-graph (Argmax over total_value).
        self.inner.run_rules()
        # ---- EMIT + realise each encounter mechanically.
        for a, b in pairs:
            self.n_encounters += 1
            ga = int(self.s.node(self.decs[a])["attrs"]["chosen_give"])
            gb = int(self.s.node(self.decs[b])["attrs"]["chosen_give"])
            sa = int(self.s.node(self.decs[a])["attrs"]["stated_give"])
            sb = int(self.s.node(self.decs[b])["attrs"]["stated_give"])
            # promise-keeping bookkeeping (a professed give under comms == a promise)
            for who, stated, chosen in ((a, sa, ga), (b, sb, gb)):
                if stated == 1:
                    self.promises_made[who] += 1
                    if chosen == 1:
                        self.promises_kept[who] += 1
                    # materialise a readable Promise node (glass-box)
                    pn = self.s.add_node("Promise", {
                        "by": float(who), "stated_give": float(stated),
                        "held_give": float(chosen),
                        "kept": 1.0 if chosen == 1 else 0.0,
                        "tick": float(self.tick)})
                    self.inner.add_edge_unchecked(self.hubs[who], "made_promise", pn)
                    self.promise_nodes.append(pn)
            # realise welfare from the two held decisions
            wa, wb = self._realise(ga, gb)
            self.total_welfare += wa + wb
            self.trade_log.append(dict(tick=self.tick, a=a, b=b,
                                       chosen_a=ga, chosen_b=gb,
                                       stated_a=sa, stated_b=sb,
                                       welfare_a=wa, welfare_b=wb))
        return dict(tick=self.tick, encounters=len(pairs))

    @staticmethod
    def _realise(ga, gb):
        """WORLD mechanics: realised end-holding value from the two held gives.
        (1,1) both trade -> both hold needed (V_NEED). (1,0) a is the sucker
        (V_ALONE), b holds both (V_BOTH). (0,1) symmetric. (0,0) no trade ->
        both keep own (V_OWN)."""
        if ga == 1 and gb == 1:
            return V_NEED, V_NEED
        if ga == 1 and gb == 0:
            return V_ALONE, V_BOTH
        if ga == 0 and gb == 1:
            return V_BOTH, V_ALONE
        return V_OWN, V_OWN

    def run(self, T=T_DEFAULT):
        for _ in range(T):
            self.step()
        return self.outcome(_ran=True, T=T)

    def outcome(self, T=T_DEFAULT, _ran=False):
        if not _ran and self.tick == 0:
            for _ in range(T):
                self.step()
        denom = self.n * max(self.tick, 1)
        return dict(
            total_welfare=self.total_welfare,
            welfare_per_agent_tick=self.total_welfare / denom,
            n_encounters=self.n_encounters,
            ticks=self.tick, n_agents=self.n, comms=self.comms)

    # ---- glass-box read-off: promise-keeping by SEED (G-deception) ----
    def keeping_by_seed(self):
        """Per agent: (w_supergraph, promises_made, promises_kept, keeping_rate).
        Reads the materialised Promise nodes (held_give vs stated_give)."""
        rows = []
        for i in range(self.n):
            made = self.promises_made[i]
            kept = self.promises_kept[i]
            rows.append(dict(agent=i, w=self.ws[i], made=made, kept=kept,
                             rate=(kept / made) if made else None))
        return rows

    def deception_gaps(self):
        """Readable stated!=held gaps across all materialised Promise nodes."""
        rows = []
        for pn in self.promise_nodes:
            a = self.s.node(pn)["attrs"]
            rows.append(dict(by=int(a["by"]), w=self.ws[int(a["by"])],
                             stated=int(a["stated_give"]), held=int(a["held_give"]),
                             gap=int(a["stated_give"]) - int(a["held_give"])))
        return rows

    def close(self):
        try:
            self.eye.stop()
        except Exception:
            pass
