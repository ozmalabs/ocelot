"""AbusiveR3CoerciveControlWorld -- a MECHANICAL two/three-agent world for the
ABUSIVE-DYNAMICS R3 rung (block 289000, "coercive control: window-narrowing +
prior-mis-setting + isolation/frontier-collapse"). Extends R2's OWN dyad
(`worlds/abusive_r2_cycle_limit_world.py`, block 286000) -- composing the SAME
TWO ALREADY-BUILT, UNMODIFIED seeds -- across TWO STRUCTURAL ARMS:

  * SINGLE-ANCHOR arm -- victim `attended_by` the abuser ONLY. The only
    available regulator IS the dysregulation source (Main & Hesse's "fright
    without solution," A7 of ABUSIVE_RELATIONSHIPS_SCOPING.md) -- a
    STRUCTURAL fact, not a scored choice.
  * OUTSIDE-REGULATOR arm (the failable control) -- victim `attended_by`
    BOTH the abuser AND a second, fixed-calm, ALWAYS-REGULATED outside
    source. The frontier is NOT collapsed to one.

R2's PREREG (Sec. 7) already named the phenomenon this rung measures as an
honest, disclosed, NON-gated residual: the victim's window narrows to its
floor over the cycle-arm episode because the abuser never satisfies
`arousal_window_coreg`'s own `got_coreg` ("regulated==1") condition. R3
REUSES R2's exact abuser mechanism (the leaky-integrate-fire relaxation
oscillator, `seeds/snap_frustration.json`, block 242000, UNMODIFIED) and R2's
own genuine composition finding (route the victim's entrainment through
`frustration`, never fight `snap_arousal_track`'s unconditional
`arousal := setpoint+frustration` commit) -- run over MANY incident cycles
(narrowing OVER EPISODES, not a single cycle) instead of R2's single-episode
oscillation read-off, and adds the second, structural arm.

FOUR COMPOSITION HAZARDS FOUND AND RESOLVED DURING THIS RUNG'S DESIGN
(`ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md` Sec. 3 has the full empirical
derivation, including the bisection trail for hazard 3 -- summarised here
because the fix is encoded in this file's own node/edge construction, not in
any rule):

  1. (R2's own finding, reused unchanged) `snap_arousal_track` (order 5,
     `snap_frustration`, matches `has_affective_state` ALONE) unconditionally
     commits `arousal := setpoint + frustration` on EVERY has_affective_state
     node -- so the victim's (and, here, the outside regulator's) entrained
     arousal must be routed through `frustration`, never written directly.
  2. NEW (R3-specific, structural): the abuser and outside-regulator
     variables inside the DYAD-arm entrainment rule's match must not be
     allowed to cross-bind (a naive two-variable match over TWO edges could
     bind either target to either role). The fix is an explicit `is_abuser`
     ROLE ATTRIBUTE (1.0 on the abuser's AffectiveState, 0.0 on the outside
     regulator's), checked in the rule's `where` clause -- a graph fact each
     node carries, read by a graph Rule, never a Python decision.
  3. NEW (R3-specific, the significant one): connecting the outside
     regulator via a SECOND `attended_by` edge (the same edge TYPE the
     abuser edge uses) was piloted FIRST and found to silently corrupt this
     rung's own entrainment rule: every cross-node `Attr` read inside its
     effect (the abuser's and the outside regulator's own `arousal`) came
     back as `0.0`, regardless of the real graph values, WHENEVER
     `arousal_window_coreg`'s `selfreg_pull` was also loaded -- reproduced
     directly (not assumed), isolated by bisection (loading `snap_frustration`
     + `arousal_window_coreg` rule-by-rule): `selfreg_pull` structurally
     matches the victim (its own match needs only `has_affective_state` +
     `has_window`, which the victim has for its OWN window-of-tolerance
     machinery) and its mere PRESENCE in the loaded rule set corrupts the
     read, even with its own epoch guard (`sr_epoch`) poisoned to a value
     that should make it permanently unable to fire (`1e15`) -- ruling out
     "prevent it from firing" as an explanation and pointing at something in
     how the engine resolves cross-node attribute reads when TWO edges of
     the SAME type leave the SAME source node. This is the same hazard
     FAMILY the codebase's own engine-gotcha note already names elsewhere
     ("two same-type incoming edges on one node can break `run_rules`
     matching for that edge type") -- R3's variant is two same-type
     OUTGOING edges. The fix, empirically confirmed to work and adopted
     WITHOUT further chasing the Rust internals: give the outside regulator
     a DIFFERENT edge type, `also_attended_by`, instead of a second
     `attended_by` -- the corruption disappears entirely once no node
     carries two same-typed edges of this shape.
  4. CONSEQUENCE of hazard 3's fix: `arousal_window_coreg`'s own
     `mark_coreg_support` (UNMODIFIED) matches specifically on the
     `attended_by` edge type, so it cannot see a regulator connected via
     `also_attended_by`. This rung adds ONE more small rule,
     `r3_mark_coreg_support_outside` -- a literal edge-type substitution of
     `mark_coreg_support`'s own match/where/effect shape (same "smallest
     possible reader" precedent as R1's OPEN QUESTION #2 / R2's Sec. 3.0),
     never editing the original rule -- so the outside source's
     `got_coreg` attribution still happens. Also confirmed by reading the
     unmodified seed rather than assumed: `mark_coreg_support` reads
     `regulated` directly off the ATTENDED-TO AGENT NODE (bound straight
     from the edge target), not off that agent's AffectiveState -- so the
     outside regulator's `regulated=1.0` is set on its Agent node here, to
     match.

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. Every
decision -- frustration accumulation, the snap threshold, discharge, recovery,
the victim's entrainment (solo or dyad), window narrowing/widening, the prior
(`others_trust`/`self_worth`) tracking -- is the graph's decision, entirely
inside the two pre-existing, unmodified seeds plus the four small rules in
`seeds/abusive_r3_coercive_control.json`. The world adapter's only
"conditional" is WHICH ARM to build (single-anchor vs outside-regulator) --
an experimental-arm selection made ONCE per trajectory by the
runner/experimenter (exactly as every prior rung in this line does), never a
graph-state-dependent branch. NO reward/punishment anywhere: the tension
trickle and the outside regulator's fixed calm arousal are both
world-delivered facts (mechanically identical to a goal-block magnitude or a
caregiver arousal reading in 239000/242000), never a scored choice.
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

# ---- FROZEN world constants (pre-registered, ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults -- BYTE-IDENTICAL to R2's
# own frozen constants, since R3 reuses R2's exact abuser mechanism)
ABUSER_HALF_WIDTH = 100.0
K_ACC = 1.0
LEAK = 0.02
DISCHARGE = 0.90
RECOVER_FLOOR = 25.0

# victim (arousal_window_coreg, block 239000 defaults -- same convention)
VICTIM_HALF_WIDTH = 10.0
K_SELF = 0.15
K_CO = 0.35

# outside regulator -- fixed-calm, always-regulated. CALM_AROUSAL == SETPOINT
# (the victim's own resting point) so the outside source is a genuine "inside
# the window, nothing to entrain away from" anchor, not an artificially
# soothing extreme.
CALM_AROUSAL = 0.0

# prior step (others_trust / self_worth) -- matches arousal_window_coreg's
# own safety_step magnitude (0.03), disclosed, not re-tuned.
TRUST_STEP = 0.03
WORTH_STEP = 0.03
PRIOR_INIT = 0.5   # neutral starting point, same convention as safety_prior's
#                     own 0.5 initial value in R2's world.

TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10


class AbusiveR3CoerciveControlWorld:
    """One ABUSER Agent (snap_frustration, unmodified, byte-identical to R2's
    own), one VICTIM Agent (arousal_window_coreg, unmodified, plus this
    rung's own frustration-routed entrainment + prior-tracking rules), and,
    ONLY in the outside-regulator arm, one fixed-calm OUTSIDE Agent. NO
    decision here -- only world delivery + read-back."""

    def __init__(self, *, outside_regulator=False,
                 abuser_half_width=ABUSER_HALF_WIDTH,
                 victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE,
                 recover_floor=RECOVER_FLOOR, k_self=K_SELF, k_co=K_CO,
                 trickle_mag=TRICKLE_MAG, calm_arousal=CALM_AROUSAL):
        self.trickle_mag = float(trickle_mag)
        self.outside_regulator = bool(outside_regulator)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "r3_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "abusive_r3_coercive_control"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract, plus is_abuser=1.0 (the NEW role
        # attribute this rung's dyad rule reads). Deliberately carries NO
        # arousal_window_coreg-specific bookkeeping key (see R2's own
        # docstring for the full omission list) AND no `regulated` key
        # (keeps snap_coreg_pull dormant on the victim's abuser-edge match,
        # exactly as in R2).
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
        # arousal_window_coreg's full contract; deliberately carries NO
        # snap_frustration-specific key (frustration, leak, leak_epoch,
        # k_acc, discharge, recover_floor, snapped, in_snap, snap_count,
        # snap_magnitude, snap_directed, snap_undirected, last_trigger_mag)
        # AND, NEW for R3, no `cr_epoch` key either -- its absence blocks
        # BOTH arousal_window_coreg's own `coreg_pull` and (once a second,
        # `regulated=1` source exists) snap_frustration's own
        # `snap_coreg_pull` from ever matching (see module docstring,
        # hazard 2; PREREG Sec. 3).
        self.victim = self.s.add_node("Agent", {"role": "victim"})
        self.vaff = self.s.add_node("AffectiveState", dict(
            name="victim_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            tick_epoch=0.0, sr_epoch=0.0, pcr_epoch=0.0,
            k_self=float(k_self), k_co=float(k_co), setpoint=float(SETPOINT),
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0, got_coreg=0.0,
            has_outside_regulator=(1.0 if self.outside_regulator else 0.0)))
        self.inner.add_edge_unchecked(self.victim, "has_affective_state", self.vaff)

        hw_v = float(victim_half_width)
        self.vwot = self.s.add_node("WindowOfTolerance", dict(
            name="victim_window", lo=-hw_v, hi=hw_v, half_width=hw_v,
            widen_delta=2.0, narrow_delta=2.0, min_half_width=5.0,
            safety_prior=0.5, safety_step=0.03, widen_count=0.0, narrow_count=0.0,
            others_trust=float(PRIOR_INIT), self_worth=float(PRIOR_INIT),
            pn_last_narrow=0.0, pn_last_widen=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_window", self.vwot)

        self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)

        # ------------------------------------------------- OUTSIDE (optional)
        # Connected via `also_attended_by` -- a DIFFERENT edge type from the
        # abuser's `attended_by` -- not `attended_by` again. See the module
        # docstring, hazard 4: a SECOND `attended_by` edge from the victim
        # (same edge TYPE as the abuser's) was piloted and found to corrupt
        # this rung's own entrainment rule's cross-node attribute reads
        # whenever `arousal_window_coreg`'s `selfreg_pull` is also loaded --
        # reproduced, isolated by bisection (removing `selfreg_pull` from the
        # loaded rule set, or changing the outside edge's type, both
        # independently fix it; epoch-guard poisoning does NOT), and
        # sidestepped by giving the outside regulator its own edge type
        # rather than chasing the Rust engine internals further (PREREG
        # Sec. 3 has the full empirical trail). `regulated=1.0` is set on
        # the OUTSIDE AGENT NODE ITSELF (not its AffectiveState) because
        # that is what `arousal_window_coreg`'s own `mark_coreg_support` --
        # and this rung's own edge-type-substituted mirror of it,
        # `r3_mark_coreg_support_outside` -- actually reads (`Eq(attr(cg,
        # "regulated"),1.0)` where `cg` binds directly to the attended-to
        # AGENT, not to its AffectiveState -- confirmed by reading the
        # unmodified seed, not assumed).
        self.outside = None
        self.oaff = None
        if self.outside_regulator:
            self.outside = self.s.add_node("Agent", {"role": "outside", "regulated": 1.0})
            self.oaff = self.s.add_node("AffectiveState", dict(
                name="outside_affect", baseline=1.0, valence=0.0,
                arousal=float(calm_arousal), setpoint=float(calm_arousal),
                resolution=0.0, selection_threshold=0.0, securing=0.0,
                competence=0.0, epoch=-1.0, is_abuser=0.0,
                tick_epoch=0.0))
            self.inner.add_edge_unchecked(self.outside, "has_affective_state", self.oaff)
            self.inner.add_edge_unchecked(self.victim, "also_attended_by", self.outside)

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
        row = dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_in_snap=aa["in_snap"], abuser_snapped=aa["snapped"],
            abuser_snap_count=aa["snap_count"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_in_episode=va["in_episode"], victim_got_coreg=va["got_coreg"],
            victim_half_width=vw["half_width"],
            victim_others_trust=vw["others_trust"], victim_self_worth=vw["self_worth"],
            victim_widen_count=vw["widen_count"], victim_narrow_count=vw["narrow_count"])
        if self.outside_regulator:
            row["outside_arousal"] = self._attrs(self.oaff)["arousal"]
        return row

    # ------------------------------------------------------------------- step
    def step(self, *, tension=False, jitter=0.0):
        """Advance one tick: (optionally) arm the abuser's tension trickle,
        advance the tick clocks, let the GRAPH decide, read off. NO decision
        here."""
        self.epoch += 1
        e = float(self.epoch)
        if tension:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        if self.outside_regulator:
            self.s.set_attr(self.oaff, "tick_epoch", e)
        self.inner.run_rules()
        r = self.readout()
        self.log.append(r)
        return r

    def run_trajectory(self, T, *, rng=None):
        """Deliver T ticks of the constant, jittered tension trickle -- the
        SAME abuser-side driver in BOTH arms (only whether the outside
        regulator exists differs)."""
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
