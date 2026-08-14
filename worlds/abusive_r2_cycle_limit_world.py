"""AbusiveR2CycleLimitWorld -- a MECHANICAL two-agent dyad world for the
ABUSIVE-DYNAMICS R2 rung (block 286000, "the cycle of abuse as a limit
cycle"). Maps Walker's four cycle-of-abuse phases (A1/B2 of
docs/research/bigville/ABUSIVE_RELATIONSHIPS_SCOPING.md) onto ONE closed
orbit in arousal, composing TWO ALREADY-BUILT, UNMODIFIED seeds:

  * ``seeds/snap_frustration.json`` (block 242000) drives the ABUSER's own
    tension-building -> incident dynamics: a leaky frustration accumulator
    fed by a constant per-tick "tension" trickle crosses the window's upper
    bound and SNAPS (abruptly, disproportionately, with discharge+recovery)
    -- a relaxation oscillator, entirely unmodified.
  * ``seeds/arousal_window_coreg.json`` (block 239000) drives the VICTIM's
    entrainment (``coreg_pull``, an unconditional leaky pull of the victim's
    real AffectiveState.arousal toward whatever the attended-to caregiver's
    arousal currently is), self-regulation, and window
    dysregulation/plasticity bookkeeping -- entirely unmodified.

R2's STRUCTURAL composition is one edge: give the victim an ``attended_by``
edge to the abuser. Because both seeds share the SAME ``affective_state_
core`` ``AffectiveState`` node type (arousal lives at the same attr key for
both), ``coreg_pull`` reading the abuser's arousal receives whatever
``snap_frustration``'s own ``snap_arousal_track`` rule just wrote there --
tension-building pulls the victim up; the incident (the snap) pulls it up
hard; discharge+recovery pulls it back down -- the honeymoon reset, for
free, via the SAME leaky pull that heals in 239000.

THIS SEED ADDS ONE SMALL RULE (``seeds/abusive_r2_cycle_limit.json``,
``r2_victim_entrainment_via_frustration``) FOR AN EMPIRICALLY-DISCOVERED
REASON, NOT TO ADD NEW DYNAMICS -- see ABUSIVE_R2_CYCLE_LIMIT_PREREG.md
Sec. 3.0 for the full two-stage derivation. In brief: ``snap_frustration``'s
own ``snap_arousal_track`` (order 5, match = ``has_affective_state`` ONLY --
no ``has_window`` / goal-block needed) unconditionally overwrites
``arousal := setpoint + frustration`` for EVERY ``has_affective_state``-
connected node in the substrate, including the victim's (whose
``frustration`` defaults to 0.0 via the engine's own arithmetic-context
attribute defaulting even though the victim never sets it) -- and because
``run_rules()`` is a REPEATING fixpoint over all orders, not a single
ascending sweep, a rule that instead tries to write ``victim.arousal``
directly at a LATER order is not a fix: ``snap_arousal_track`` has no
per-tick epoch guard, so it keeps re-matching on every later pass within
the same tick and re-clobbers arousal back to 0 until the fixpoint settles
-- and 0 is the only value at which its own where-clause goes false, so a
direct-arousal-write composition converges there regardless of order
(verified empirically, not assumed: an order-8/9 direct-write version of
this fix was built, piloted, and found to still converge to victim arousal
== 0.0 for exactly this reason). The resolution is to stop writing
``victim.arousal`` at all and instead write ``victim.frustration`` (an
attribute ``arousal_window_coreg`` never touches) to the value that makes
``setpoint + frustration`` equal the desired entrained arousal;
``snap_arousal_track`` itself then becomes the mechanism that COMMITS the
entrained value, and the fixpoint converges there because that is now the
only value at which its own where-clause goes false.
``r2_victim_entrainment_via_frustration`` computes, once per tick
(epoch-guarded), the SAME ``coreg_pull`` + ``selfreg_pull`` deltas (a
single simultaneous-Euler-step combination of both, a disclosed minor
simplification of ``arousal_window_coreg``'s own sequential two-rule
order-4-then-order-5 form) as an offset from setpoint, written to
``frustration``. Neither ``snap_arousal_track`` nor ``coreg_pull`` /
``selfreg_pull`` is disabled or edited; all three still fire exactly as
designed, every tick. This is a genuine composition hazard between two
independently-gated seeds sharing the generic ``has_affective_state`` edge
shape, resolved by routing through an attribute the colliding rule was
already designed to read, not by fighting its own commit.

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. It
INGESTS a mechanical, world-side "tension" trickle stream (a fixed, jittered
magnitude delivered onto the abuser's GoalBlock every tick, or NOT delivered
at all for the constant-regulation control arm -- deciding WHICH arm to run
is an experimental-arm selection made ONCE per episode by the
runner/experimenter, exactly as every prior rung in this line selects an
arm) into the substrate and EMITS graph state around ``run_rules()``. Every
decision -- frustration accumulation, the snap threshold, discharge,
recovery, the co-regulation pull, the victim's own window
dysregulation/plasticity -- is the graph's decision, entirely inside the two
pre-existing, unmodified seeds (plus the one small rule above). NO reward
/ punishment anywhere: the tension trickle is a world-delivered
magnitude (mechanically identical to a stressor magnitude in 239000 or a
goal-block magnitude in 242000), never a scored choice.
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

# ---- FROZEN world constants (pre-registered, ABUSIVE_R2_CYCLE_LIMIT_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults, unmodified mechanism)
ABUSER_HALF_WIDTH = 100.0   # abuser's own snap threshold (wot.hi)
K_ACC = 1.0                 # goal-block magnitude accumulates in full (glass-box)
LEAK = 0.02                 # sd_blend leak toward 0 (242000's own pinned value)
DISCHARGE = 0.90            # fraction of residual discharged on a snap
RECOVER_FLOOR = 25.0        # residual below which the snap latch clears --
#                              comfortably ABOVE the ~0.10*hi post-discharge
#                              value, so recovery actually triggers (see
#                              PREREG Sec. 3.1: at recover_floor=10.0 the
#                              post-discharge residual landed just ABOVE the
#                              floor and the latch never cleared -- measured,
#                              not assumed)

# victim (arousal_window_coreg, block 239000 defaults, unmodified mechanism)
VICTIM_HALF_WIDTH = 10.0    # victim's OWN window (secondary/descriptive read-off;
#                              pilot-chosen so the entrained oscillation crosses
#                              it on a meaningful fraction of cycles)
K_SELF = 0.15               # victim self-regulation leak (239000's own pinned value)
K_CO = 0.35                 # victim<-abuser entrainment gain (coreg_pull)

# the tension-building driver: a CONSTANT (non-periodic-by-design) per-tick
# trickle onto the abuser's GoalBlock magnitude. See PREREG Sec. 2 for why a
# constant driver (not a hand-scheduled "incident" driver) was chosen: the
# INCIDENT'S OWN PERIODICITY EMERGES from the leaky-integrate-fire relaxation
# oscillator (accumulate -> leak -> threshold -> discharge -> recover), not
# from any exogenous scheduling -- this resolves OPEN QUESTION #4 in favour
# of the self-sustaining design.
TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10  # per-tick jitter as a fraction of TRICKLE_MAG


class AbusiveR2CycleLimitWorld:
    """One ABUSER Agent (snap_frustration's tension-building/incident
    relaxation oscillator, unmodified) and one VICTIM Agent (arousal_window_
    coreg's entrainment/self-regulation/window dynamics, unmodified),
    coupled by ONE ``attended_by`` edge (victim -> abuser). ``run_episode``
    delivers a pre-generated tension-trickle event stream (or none, for the
    constant-regulation control) tick by tick and reads back the graph's
    decisions. NO decision here -- only world delivery + read-back.
    """

    def __init__(self, *, abuser_half_width=ABUSER_HALF_WIDTH,
                 victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE,
                 recover_floor=RECOVER_FLOOR, k_self=K_SELF, k_co=K_CO,
                 trickle_mag=TRICKLE_MAG):
        self.trickle_mag = float(trickle_mag)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "r2_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "abusive_r2_cycle_limit"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract; deliberately carries NO
        # arousal_window_coreg-specific bookkeeping key (in_episode,
        # sr_epoch, dysregulated, dysreg_kind, got_coreg, cr_epoch,
        # "regulated") -- their ABSENCE is what keeps that seed's own
        # onset/self-regulation/window-plasticity rules from also matching
        # the abuser (see module docstring; empirically verified, PREREG
        # Sec. 3.0).
        self.abuser = self.s.add_node("Agent", {"role": "abuser"})
        self.aaff = self.s.add_node("AffectiveState", dict(
            name="abuser_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
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
        # arousal_window_coreg's full contract; deliberately carries NO
        # snap_frustration-specific key (frustration, leak, leak_epoch,
        # k_acc, discharge, recover_floor, snapped, in_snap, snap_count,
        # snap_magnitude, snap_directed, snap_undirected, last_trigger_mag)
        # -- their ABSENCE keeps THAT seed's rules from matching the victim.
        self.victim = self.s.add_node("Agent", {"role": "victim"})
        self.vaff = self.s.add_node("AffectiveState", dict(
            name="victim_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            tick_epoch=0.0, sr_epoch=0.0, cr_epoch=0.0, pcr_epoch=0.0,
            k_self=float(k_self), k_co=float(k_co), setpoint=float(SETPOINT),
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0, got_coreg=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_affective_state", self.vaff)

        hw_v = float(victim_half_width)
        self.vwot = self.s.add_node("WindowOfTolerance", dict(
            name="victim_window", lo=-hw_v, hi=hw_v, half_width=hw_v,
            widen_delta=2.0, narrow_delta=2.0, min_half_width=5.0,
            safety_prior=0.5, safety_step=0.03, widen_count=0.0, narrow_count=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_window", self.vwot)

        # THE ENTIRE NEW COMPOSITION: one coupling edge. coreg_pull
        # (arousal_window_coreg, unmodified) reads the abuser's AffectiveState
        # arousal through this edge every tick, unconditionally.
        self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)

        self.epoch = 0
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        aa = self._attrs(self.aaff)
        aw = self._attrs(self.awot)
        va = self._attrs(self.vaff)
        vw = self._attrs(self.vwot)
        return dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_in_snap=aa["in_snap"], abuser_snapped=aa["snapped"],
            abuser_snap_count=aa["snap_count"], abuser_hi=aw["hi"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_in_episode=va["in_episode"],
            victim_half_width=vw["half_width"], victim_hi=vw["hi"],
            victim_safety_prior=vw["safety_prior"])

    # ------------------------------------------------------------------- step
    def step(self, *, tension=False, jitter=0.0):
        """Advance one tick: (optionally) arm the abuser's tension trickle,
        advance both tick clocks, let the GRAPH decide (accumulate / leak /
        snap / discharge / recover / entrain / self-regulate / window
        plasticity), read off. NO decision here."""
        self.epoch += 1
        e = float(self.epoch)
        if tension:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        self.inner.run_rules()
        r = self.readout()
        self.log.append(r)
        return r

    def run_episode(self, T, *, driver_on=True, rng=None):
        """Deliver T ticks. driver_on=True -> the CYCLE arm (a constant,
        jittered tension trickle every tick -- the "incident driver").
        driver_on=False -> the CONSTANT-REGULATION control (no incident
        driver at all -- the failable control, per
        ABUSIVE_RELATIONSHIPS_SCOPING.md Part E, R2)."""
        for _ in range(T):
            jitter = 0.0
            if driver_on and rng is not None:
                jitter = float(rng.normal(0.0, self.trickle_mag * TRICKLE_JITTER_FRAC))
            self.step(tension=driver_on, jitter=jitter)
        return self.log

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
