"""AbusiveN2IsolationWorld -- a MECHANICAL abuser/victim/support-network
world for the ABUSIVE-DYNAMICS N2 rung (block 301000, "isolation as an
active process" -- ABUSIVE_RELATIONSHIPS_NETWORK.md Part E, N2; Part B3).

Composes TWO already-built substrates, unmodified:
  * N1's credibility-asymmetry loop (`seeds/abusive_n1_credibility_loop.json`,
    block 298000) -- the abuser/victim dyad (itself riding
    `snap_frustration`/`arousal_window_coreg`, both UNMODIFIED) AND the
    per-NetworkNode `belief_gap` credibility read-off. N2 depends on this
    seed DIRECTLY and reuses its rules VERBATIM -- no credibility dynamics
    are reimplemented here.
  * `seeds/abusive_n2_isolation.json` (this rung's own two new rules) --
    `n2_abuser_active_sever` (the abuser's scheduled, active edge-severing
    tactic) and `n2_network_drift_sever` (the network's own belief-gap-
    driven withdrawal).

A small population of N_SUPPORT_NODES "support nodes" (NetworkNode agents,
reusing N1's own node type) double as N1's credibility OBSERVERS (each
carries a `support_edge` to the victim AND an `observes_stated` edge to the
abuser, feeding N1's `n1_network_credibility_stated` rule exactly as N1's
own outsider nodes do) -- the same small population is both "who believes
her" and "who supports her," which is the point: in a real social network
these are the same people. See ABUSIVE_N2_ISOLATION_PREREG.md Sec. 2 for
why 8 (not N1's 5, and not a larger cast) is the sizing decision.

A 2x2 FACTORIAL of arms (victim dysregulated x isolation tactic armed) --
ABUSIVE_N2_ISOLATION_PREREG.md Sec. 2.4:
  * BOTH_DRIVERS         (dysregulated=True,  tactic=True)  -- doubly driven
  * DRIFT_ONLY           (dysregulated=True,  tactic=False) -- drift alone
  * ACTIVE_ONLY          (dysregulated=False, tactic=True)  -- schedule alone
  * NO_TACTIC_CONTROL    (dysregulated=False, tactic=False) -- FAILABLE:
                            support edges must PERSIST

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER.
Every decision -- the dyad dynamics, the abuser's stated face, each node's
credibility belief, WHETHER an edge is severed on a given tick -- is the
graph's decision, entirely inside the (unmodified) `abusive_n1_credibility_
loop` seed and this rung's two new rules in `abusive_n2_isolation.json`.
The adapter's only "conditionals" are (i) WHICH ARM to build (an
experimental-arm selection made ONCE per trajectory, exactly as every prior
rung in this line) and (ii) mechanically DELIVERING each tick's observed
graph facts onto each node's observation-count attrs (reused verbatim from
N1's own `step()`) and the tick counter each node's severing rules read
(`tick_epoch`, mechanically incremented, exactly like N1's/R1-R5's own tick
counters). WHICH node is scheduled to be severed when (`sever_at_tick`) and
each node's drift-decay threshold (`drift_threshold`) are assigned ONCE at
construction time, per node INDEX -- mechanical per-node setup identical in
kind to N1's own `observes_private = 1.0 if i==0 else 0.0` -- never a live
decision responding to graph state. NO reward/punishment anywhere.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as srs                                  # noqa: E402
from substrate.seed_loader import manifest_for              # noqa: E402

# ---- FROZEN world constants (pre-registered, ABUSIVE_N2_ISOLATION_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults) -- BYTE-IDENTICAL to
# N1's/R2's/R3's own frozen constants; N2 reuses N1's exact dyad mechanism.
ABUSER_HALF_WIDTH = 100.0
K_ACC = 1.0
LEAK = 0.02
DISCHARGE = 0.90
RECOVER_FLOOR = 25.0

# victim (arousal_window_coreg, block 239000 defaults) -- same convention
VICTIM_HALF_WIDTH = 10.0
K_SELF = 0.15
K_CO = 0.35

TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10

# credibility loop (N1 defaults, reused verbatim -- N2 does not re-sweep
# these; the belief_gap trajectory this produces is IDENTICAL to N1's own
# measured baseline trend, PREREG Sec. 3)
CHARM_WEIGHT = 1.0
CLAIM_WEIGHT = 1.0
INSTABILITY_DISCOUNT_WEIGHT = 3.0

# N2-specific, pilot-informed (PREREG Sec. 3)
N_SUPPORT_NODES = 8
EPISODE_TICKS = 210.0         # ticks between successive scheduled
#                                active-severing episodes -- the abuser does
#                                NOT act on every incident cycle (N1's own
#                                measured mean cycle length is ~25 ticks);
#                                the isolation tactic ratchets on a COARSER,
#                                roughly-once-per-~8-incident-cycles cadence.
#                                Pilot-tuned (PREREG Sec. 3) so ACTIVE_ONLY
#                                alone leaves a comparable, non-floor number
#                                of edges intact at T=1000 to DRIFT_ONLY
#                                alone, making the doubly-driven comparison
#                                (G6) genuinely testable rather than floor-
#                                limited by either driver alone already
#                                reaching zero.
DRIFT_STEP = 340.0            # per-node drift_threshold stagger, assigned in
#                                REVERSED index order relative to the active
#                                schedule (node i's threshold is
#                                (N-i)*DRIFT_STEP, node i's active-sever tick
#                                is (i+1)*EPISODE_TICKS) so the two drivers
#                                target COMPLEMENTARY parts of the support
#                                population rather than the same nodes in the
#                                same order -- pilot-tuned (PREREG Sec. 3).


class AbusiveN2IsolationWorld:
    """One ABUSER Agent + one VICTIM Agent (N1's dyad, unmodified) and a
    Network of N_SUPPORT_NODES NetworkNode agents, each BOTH a credibility
    observer (N1's rule shape) AND a support-edge holder (this rung's new
    rules). NO decision here -- only world delivery + mechanical per-tick
    bookkeeping + read-back."""

    def __init__(self, *, dysregulated_victim=True, isolation_tactic_on=True,
                 n_support_nodes=N_SUPPORT_NODES,
                 abuser_half_width=ABUSER_HALF_WIDTH,
                 victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE,
                 recover_floor=RECOVER_FLOOR, k_self=K_SELF, k_co=K_CO,
                 trickle_mag=TRICKLE_MAG,
                 charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
                 instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
                 episode_ticks=EPISODE_TICKS, drift_step=DRIFT_STEP):
        self.trickle_mag = float(trickle_mag)
        self.dysregulated_victim = bool(dysregulated_victim)
        self.isolation_tactic_on = bool(isolation_tactic_on)
        self.n_support_nodes = int(n_support_nodes)
        self.episode_ticks = float(episode_ticks)
        self.drift_step = float(drift_step)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "n2_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "abusive_n1_credibility_loop", "abusive_n2_isolation"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # N1's own contract, byte-identical (is_abuser=1.0, deception_on=1.0
        # fixed ON in every arm -- the arms manipulate the victim's coupling
        # / the isolation tactic, never the abuser's own deception).
        self.abuser = self.s.add_node("Agent", {"role": "abuser"})
        self.aaff = self.s.add_node("AffectiveState", dict(
            name="abuser_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0, is_abuser=1.0,
            frustration=0.0, setpoint=float(SETPOINT), k_acc=float(k_acc),
            leak=float(leak), discharge=float(discharge),
            recover_floor=float(recover_floor),
            snapped=0.0, in_snap=0.0, snap_count=0.0, snap_magnitude=0.0,
            snap_directed=0.0, snap_undirected=0.0, last_trigger_mag=0.0,
            tick_epoch=0.0, leak_epoch=0.0,
            deception_on=1.0, stated_charm=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_affective_state", self.aaff)

        hw_a = float(abuser_half_width)
        self.awot = self.s.add_node("WindowOfTolerance", dict(
            name="abuser_window", lo=-hw_a, hi=hw_a, half_width=hw_a))
        self.inner.add_edge_unchecked(self.abuser, "has_window", self.awot)

        self.gb = self.s.add_node("GoalBlock", dict(
            name="tension_trigger", magnitude=0.0, armed=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_goal_block", self.gb)

        # ---------------------------------------------------------- VICTIM
        self.victim = self.s.add_node("Agent", {"role": "victim"})
        self.vaff = self.s.add_node("AffectiveState", dict(
            name="victim_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            tick_epoch=0.0, sr_epoch=0.0, pcr_epoch=0.0,
            k_self=float(k_self), k_co=float(k_co), setpoint=float(SETPOINT),
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0, got_coreg=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_affective_state", self.vaff)

        hw_v = float(victim_half_width)
        self.vwot = self.s.add_node("WindowOfTolerance", dict(
            name="victim_window", lo=-hw_v, hi=hw_v, half_width=hw_v,
            widen_delta=2.0, narrow_delta=2.0, min_half_width=5.0,
            safety_prior=0.5, safety_step=0.03, widen_count=0.0, narrow_count=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_window", self.vwot)

        if self.dysregulated_victim:
            self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)

        # ---------------------------------------------------- SUPPORT NETWORK
        # A Network hub carrying the arm's isolation_tactic_on switch (read
        # by n2_abuser_active_sever) + N_SUPPORT_NODES NetworkNode members,
        # each: (a) an N1-shape credibility observer (observes_stated ->
        # abuser, observes_victim -> victim, observes_private=0.0 -- every
        # node here is an "outsider" in N1's terms, no private-face insider
        # in this rung), and (b) a support_edge -> victim, with a
        # mechanically-assigned (per-index, set once) sever_at_tick
        # (abuser-driven schedule) and drift_threshold (network-drift
        # stagger).
        self.network = self.s.add_node("Network", dict(
            name="network", isolation_tactic_on=(1.0 if self.isolation_tactic_on else 0.0)))
        self.nodes = []
        for i in range(self.n_support_nodes):
            nn = self.s.add_node("NetworkNode", dict(
                name=f"support_{i}",
                observes_private=0.0,
                charm_weight=float(charm_weight), claim_weight=float(claim_weight),
                instability_discount_weight=float(instability_discount_weight),
                harm_discount_weight=0.0,
                seen_charm=0.0, seen_harm_direct=0.0,
                seen_victim_claim=0.0, seen_victim_unstable=0.0,
                cred_abuser=0.0, cred_victim=0.0, belief_gap=0.0,
                tick_epoch=0.0,
                sever_at_tick=float((i + 1) * self.episode_ticks),
                drift_threshold=float((self.n_support_nodes - i) * self.drift_step),
                severed=0.0, severed_reason=0.0))
            self.inner.add_edge_unchecked(self.network, "has_member", nn)
            self.inner.add_edge_unchecked(nn, "observes_stated", self.abuser)
            self.inner.add_edge_unchecked(nn, "observes_victim", self.victim)
            self.inner.add_edge_unchecked(nn, "support_edge", self.victim)
            self.nodes.append(nn)

        self.epoch = 0
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def _n_intact_support_edges(self):
        blob = self.s.graph_to_dict()
        return sum(1 for e in blob["edges"] if e["type"] == "support_edge")

    def readout(self):
        aa = self._attrs(self.aaff)
        va = self._attrs(self.vaff)
        vw = self._attrs(self.vwot)
        nn_rows = [self._attrs(nn) for nn in self.nodes]
        return dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"], abuser_stated_charm=aa["stated_charm"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_half_width=vw["half_width"],
            belief_gap_mean=(sum(r["belief_gap"] for r in nn_rows) / len(nn_rows)),
            n_severed=sum(1 for r in nn_rows if r["severed"] == 1.0),
            n_severed_active=sum(1 for r in nn_rows if r["severed_reason"] == 1.0),
            n_severed_drift=sum(1 for r in nn_rows if r["severed_reason"] == 2.0),
            n_intact_support_edges=self._n_intact_support_edges())

    # ------------------------------------------------------------------- step
    def step(self, *, tension=False, jitter=0.0):
        """Advance one tick: (optionally) arm the abuser's tension trickle,
        let the GRAPH decide the dyad + the abuser's stated face
        (run_rules), MECHANICALLY deliver each node's per-tick observation
        counts + tick counter (a world fact, never a judgement), let the
        GRAPH decide each node's credibility belief AND whether either
        severing driver fires (run_rules again), read off."""
        self.epoch += 1
        e = float(self.epoch)
        if tension:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        self.inner.run_rules()

        # ---- mechanical per-tick observation bookkeeping (world fact -> attr)
        # reused VERBATIM from N1's own step() -- no credibility dynamics are
        # reimplemented here.
        stated_charm = self._attrs(self.aaff)["stated_charm"]
        victim_unstable = self._attrs(self.vaff)["dysregulated"]
        for nn in self.nodes:
            a = self._attrs(nn)
            self.s.set_attr(nn, "seen_charm", a["seen_charm"] + stated_charm)
            self.s.set_attr(nn, "seen_victim_claim", a["seen_victim_claim"] + 1.0)
            self.s.set_attr(nn, "seen_victim_unstable", a["seen_victim_unstable"] + victim_unstable)
            self.s.set_attr(nn, "tick_epoch", e)
        self.inner.run_rules()

        r = self.readout()
        self.log.append(r)
        return r

    def run_trajectory(self, T, *, rng=None):
        """Deliver T ticks of the constant, jittered tension trickle -- the
        SAME abuser-side driver in EVERY arm (only whether the victim is
        coupled, or whether the isolation tactic is armed, differs)."""
        for _ in range(T):
            jitter = 0.0
            if rng is not None:
                jitter = float(rng.normal(0.0, self.trickle_mag * TRICKLE_JITTER_FRAC))
            self.step(tension=True, jitter=jitter)
        return self.log

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
