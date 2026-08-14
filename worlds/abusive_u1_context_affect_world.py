"""AbusiveU1ContextAffectWorld -- a MECHANICAL abuser/victim/network world for
the ABUSIVE-DYNAMICS U1 rung (block 310000, "context-dependent affect, no
deception node at all" -- ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md Part
E, U1; the sharpest no-intent test of the unintentional/no-deliberate-
deception companion dimension).

Composes N1's own dyad machinery (self-contained restatement -- see
seeds/abusive_u1_context_affect.json's own provenance for why N1's seed file
is NOT depended on directly, matching U0's own precedent) with a network that
carries NO divergence node at all: every NetworkNode reads the abuser's SAME
true `frustration` value (`observes_held`, N1's own edge type, universal
here). The only manipulated variable across ticks is a MECHANICAL,
PRE-DETERMINED phase schedule -- alternating blocks of DYAD-PHASE ticks (the
tension trickle armed, matching R2/R3/N1's own driver) and NETWORK-PHASE
ticks (the trickle NOT armed, so `snap_frustration`'s own unmodified LEAK
constant genuinely decays frustration toward baseline) -- and across ARMS,
whether the network's observation bookkeeping is CREDITED only on
network-phase ticks (CONTEXT_GATED) or on every tick regardless of phase
(ALWAYS_OBSERVED, the failable control).

TWO ARMS (ABUSIVE_U1_CONTEXT_AFFECT_PREREG.md):
  * CONTEXT_GATED    -- the network's seen_charm/seen_elevated bookkeeping
                         credits ONLY network-phase ticks. THE LOOP: predicted
                         to entrap (belief-gap favours the abuser) even though
                         no divergence node exists anywhere in the graph --
                         the abuser genuinely IS calmer on the ticks the
                         network happens to be watching.
  * ALWAYS_OBSERVED  -- the network's bookkeeping credits EVERY tick,
                         regardless of phase. FAILABLE: must show the
                         belief-gap NOT favouring the abuser to the SAME
                         DEGREE as CONTEXT_GATED (CI-separated below it) --
                         if context-selectivity is not what is doing the
                         work, this control will not separate.

The abuser's own dyad mechanism (`snap_frustration`, block 242000, UNMODIFIED)
and the victim's entrainment (`arousal_window_coreg`, block 239000,
UNMODIFIED, `attended_by` STATIC across the whole trajectory, matching N1's
BASELINE) are IDENTICAL across both arms -- the trickle-arming PHASE SCHEDULE
is also IDENTICAL across both arms (same schedule, same seed stream per
trajectory index), so the ONLY manipulated variable reaching the network is
WHICH TICKS its observation bookkeeping is credited on.

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. Every
decision -- frustration accumulation, the snap threshold, discharge, recovery,
the victim's entrainment, and the network's credibility belief-update
(cred_abuser/cred_victim/belief_gap) -- is the graph's decision, entirely
inside `seeds/snap_frustration.json` / `seeds/arousal_window_coreg.json`
(both UNMODIFIED) and this rung's two rules in
`seeds/abusive_u1_context_affect.json`. The adapter's only "conditionals" are
(i) WHICH ARM to build (an experimental-arm selection made ONCE per
trajectory, exactly as every prior rung), (ii) a MECHANICAL, PRE-DETERMINED
phase schedule (a tick counter against fixed phase lengths -- never a
graph-state read, the same class as R1-R5's own event schedules), and (iii)
mechanically DELIVERING each tick's observed graph fact (the abuser's
frustration vs recover_floor) onto each network node's observation-COUNT
attrs -- a per-tick tally, never a judgement about what a node should
BELIEVE (that is `u1_network_credibility`'s job, entirely). NO
reward/punishment anywhere: the tension trickle is a world-delivered fact
(mechanically identical to a goal-block magnitude in 239000/242000/298000),
never a scored choice.
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
from substrate.seed_loader import manifest_for               # noqa: E402

# ---- FROZEN world constants (pre-registered, ABUSIVE_U1_CONTEXT_AFFECT_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults -- BYTE-IDENTICAL to N1's/
# U0's own frozen constants, since U1 reuses the exact same abuser mechanism).
ABUSER_HALF_WIDTH = 100.0
K_ACC = 1.0
LEAK = 0.02
DISCHARGE = 0.90
RECOVER_FLOOR = 25.0

# victim (arousal_window_coreg, block 239000 defaults -- same convention)
VICTIM_HALF_WIDTH = 10.0
K_SELF = 0.15
K_CO = 0.35

TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10

# network -- IDENTICAL to N1's own pilot-informed operating point (reused,
# not re-swept -- U1's own scientific claim is about the phase schedule, not
# the network's credibility formula's weights).
N_NETWORK_NODES = 5
CHARM_WEIGHT = 1.0
CLAIM_WEIGHT = 1.0
INSTABILITY_DISCOUNT_WEIGHT = 3.0

# U1-specific: the mechanical phase schedule (pilot-chosen, see PREREG Sec. 4).
# A "dyad-phase" tick arms the tension trickle (matching R2/R3/N1's own
# driver); a "network-phase" tick does not, so snap_frustration's own
# unmodified LEAK constant decays frustration toward baseline. Piloted
# directly against the real graph on off-block seed 90000: at these lengths,
# ~82% of dyad-phase ticks read genuinely elevated (frustration>recover_
# floor) and ~68% of network-phase ticks read genuinely calm
# (frustration<=recover_floor) -- a real, non-degenerate separation, not a
# 100%/0% artifact.
DYAD_PHASE_TICKS = 25
NETWORK_PHASE_TICKS = 50

ARM_NAMES = ("context_gated", "always_observed")


class AbusiveU1ContextAffectWorld:
    """One ABUSER Agent (snap_frustration, unmodified, byte-identical to
    N1's/U0's own), one VICTIM Agent (arousal_window_coreg, unmodified, plus
    U1's own frustration-routed entrainment, byte-identical to N1's), and a
    Network of five NetworkNode agents (all observes_held -- NO stated/held
    split anywhere) whose reputation belief is entirely graph-rule-computed.
    NO decision here -- only world delivery + a mechanical phase schedule +
    mechanical per-tick observation-count bookkeeping + read-back."""

    def __init__(self, arm="context_gated", *,
                 abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
                 k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
                 n_network_nodes=N_NETWORK_NODES,
                 charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
                 instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
                 dyad_phase_ticks=DYAD_PHASE_TICKS, network_phase_ticks=NETWORK_PHASE_TICKS):
        if arm not in ARM_NAMES:
            raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")
        self.arm = arm
        self.context_gated = (arm == "context_gated")

        self.trickle_mag = float(trickle_mag)
        self.n_network_nodes = int(n_network_nodes)
        self.dyad_phase_ticks = int(dyad_phase_ticks)
        self.network_phase_ticks = int(network_phase_ticks)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "u1_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "abusive_u1_context_affect"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract, plus is_abuser=1.0 (read by
        # u1_victim_entrainment). NO deception_on/stated_charm -- U1 has no
        # divergence node at all.
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
            tick_epoch=0.0, leak_epoch=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_affective_state", self.aaff)

        hw_a = float(abuser_half_width)
        self.awot = self.s.add_node("WindowOfTolerance", dict(
            name="abuser_window", lo=-hw_a, hi=hw_a, half_width=hw_a))
        self.inner.add_edge_unchecked(self.abuser, "has_window", self.awot)

        self.gb = self.s.add_node("GoalBlock", dict(
            name="tension_trigger", magnitude=0.0, armed=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_goal_block", self.gb)

        # ---------------------------------------------------------- VICTIM
        # arousal_window_coreg's full contract; identical to N1's own.
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

        # attended_by is STATIC across the whole trajectory (matching N1's
        # BASELINE exactly) -- see the seed's own provenance for why the
        # dyad-coupling edge is NOT what toggles per phase; the phase
        # schedule lives entirely in the trickle-arming / observation-
        # crediting logic below.
        self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)

        # --------------------------------------------------------- NETWORK
        # A Network hub + N NetworkNode members, ALL observes_held (no
        # stated/held split -- every node reads the SAME true state).
        self.network = self.s.add_node("Network", {"name": "network"})
        self.nodes = []
        for i in range(self.n_network_nodes):
            nn = self.s.add_node("NetworkNode", dict(
                name=f"node_{i}",
                credibility_on=1.0,
                charm_weight=float(charm_weight), claim_weight=float(claim_weight),
                instability_discount_weight=float(instability_discount_weight),
                seen_charm=0.0, seen_elevated=0.0,
                seen_victim_claim=0.0, seen_victim_unstable=0.0,
                cred_abuser=0.0, cred_victim=0.0, belief_gap=0.0))
            self.inner.add_edge_unchecked(self.network, "has_member", nn)
            self.inner.add_edge_unchecked(nn, "observes_held", self.abuser)
            self.inner.add_edge_unchecked(nn, "observes_victim", self.victim)
            self.nodes.append(nn)

        # ---- mechanical phase schedule state (a pure tick counter, never a
        # graph-state read -- same class as R1-R5's own event schedules).
        self.phase = "dyad"
        self.phase_counter = 0

        self.epoch = 0
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        aa = self._attrs(self.aaff)
        va = self._attrs(self.vaff)
        vw = self._attrs(self.vwot)
        nn_rows = [self._attrs(nn) for nn in self.nodes]
        return dict(
            epoch=self.epoch, phase=self.phase,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_half_width=vw["half_width"],
            belief_gap_mean=(sum(r["belief_gap"] for r in nn_rows) / len(nn_rows)),
            cred_abuser_mean=(sum(r["cred_abuser"] for r in nn_rows) / len(nn_rows)),
            cred_victim_mean=(sum(r["cred_victim"] for r in nn_rows) / len(nn_rows)))

    # ------------------------------------------------------------------- step
    def step(self, *, jitter=0.0):
        """Advance one tick: determine the MECHANICAL phase (a pure counter
        against the fixed phase lengths -- never a graph-state read), arm the
        trickle iff this is a dyad-phase tick, let the GRAPH decide the dyad
        (run_rules), MECHANICALLY deliver each node's per-tick observation
        counts -- gated on phase for CONTEXT_GATED, ungated for
        ALWAYS_OBSERVED -- let the GRAPH decide each node's credibility
        belief (run_rules again), read off, advance the phase counter."""
        self.epoch += 1
        e = float(self.epoch)
        is_dyad_tick = (self.phase == "dyad")
        if is_dyad_tick:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        self.inner.run_rules()

        # ---- mechanical per-tick observation bookkeeping (world fact -> attr)
        frustration = self._attrs(self.aaff)["frustration"]
        recover_floor = self._attrs(self.aaff)["recover_floor"]
        calm = 1.0 if frustration <= recover_floor else 0.0
        elevated = 1.0 - calm
        is_network_tick = not is_dyad_tick
        credit_this_tick = is_network_tick if self.context_gated else True
        victim_unstable = self._attrs(self.vaff)["dysregulated"]
        for nn in self.nodes:
            a = self._attrs(nn)
            if credit_this_tick:
                self.s.set_attr(nn, "seen_charm", a["seen_charm"] + calm)
                self.s.set_attr(nn, "seen_elevated", a["seen_elevated"] + elevated)
            self.s.set_attr(nn, "seen_victim_claim", a["seen_victim_claim"] + 1.0)
            self.s.set_attr(nn, "seen_victim_unstable", a["seen_victim_unstable"] + victim_unstable)
        self.inner.run_rules()

        r = self.readout()
        self.log.append(r)

        # ---- advance the MECHANICAL phase schedule (pure counter, no graph read)
        self.phase_counter += 1
        plen = self.dyad_phase_ticks if is_dyad_tick else self.network_phase_ticks
        if self.phase_counter >= plen:
            self.phase_counter = 0
            self.phase = "network" if is_dyad_tick else "dyad"
        return r

    def run_trajectory(self, T, *, rng=None):
        """Deliver T ticks of the mechanical phase schedule -- the SAME
        schedule + SAME driver in EVERY arm (only which ticks the network's
        observation bookkeeping is credited on differs)."""
        for _ in range(T):
            jitter = 0.0
            if rng is not None:
                jitter = float(rng.normal(0.0, self.trickle_mag * TRICKLE_JITTER_FRAC))
            self.step(jitter=jitter)
        return self.log

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
