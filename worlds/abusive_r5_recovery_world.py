"""AbusiveR5RecoveryWorld -- a MECHANICAL two/three-agent dyad world for the
ABUSIVE-DYNAMICS R5 rung (block 295000, "leaving/recovery -- the reverse of
R1-R4"). Composes FOUR already-built, unmodified rungs onto ONE victim node:

  * ``traumatic_bond_r1`` (block 283000) -- MoodTask/Mood -> Partner.value
    bond accrual (``tb_bond_accrue``).
  * ``abusive_r2_cycle_limit`` (block 286000) -- the abuser's leaky-
    integrate-fire snap oscillator, entraining the victim via
    frustration-routing (``r2_victim_entrainment_via_frustration``).
  * ``abusive_r3_coercive_control`` (block 289000) -- window-narrowing,
    others_trust/self_worth prior tracking, and the ``also_attended_by``
    outside-regulator mechanism (``r3_victim_entrainment_solo/dyad``,
    ``r3_mark_coreg_support_outside``, ``r3_prior_track_narrow/widen``).
  * ``abusive_r4_learned_helplessness`` (block 292000) -- EscapeDecision.
    contingency_prior + the Argmax escape/stay decision
    (``r4_belief_update``, ``r4_appraise_attempt/stay``, ``r4_choose``).

plus TWO new rules of its own (``seeds/abusive_r5_recovery.json``):
``r5_bond_extinguish`` (a constant proportional decay on Partner.value --
the PREE's own flip side, A3 of the scoping doc: intermittent reinforcement
makes the bond extinction-RESISTANT; take the reinforcement away and it
extinguishes) and ``r5_contingency_restore`` (a SECOND, independent
leaky-EMA evidence channel on EscapeDecision.contingency_prior, so an
outside witness can revise a belief the victim's own frozen attempt channel
can no longer supply evidence for -- R4's own documented trap).

ONE victim Agent node plays THREE roles simultaneously (R2/R3's entrained
Agent, R1's EmotionHub, R4's EmotionHub) because rule ``match`` arrays in
this engine are structural (edge type + bound variable), never filtered by
the literal node-type string passed to ``add_node`` -- confirmed by reading
R1-R4's own world adapters, which already rely on this (R4's own module
docstring: "the AffectiveState/has_affective_state node/edge naming below
borrows affective_state_core's contract as a naming convention ONLY"). The
ABUSER Agent node likewise plays R1's ``Partner`` role directly (the bond
IS to the abuser) -- a genuine, disclosed R5-specific composition choice,
not a reuse of any prior rung's own construction.

TWO STRUCTURAL PHASES per trajectory, mirroring Herman's staged recovery
(A6: safety first) and the task's own framing that RESTORE is the modelled
phenomenon here, not just the ethical envelope:

  * INDUCTION (ticks 0..T1) -- IDENTICAL in both arms. The abuser's tension
    trickle runs continuously (R2/R3's own mechanism, unmodified); the bond
    channel receives R1's OWN validated INTERMITTENT harm/relief multiset
    (reused directly from ``worlds.traumatic_bond_r1_world.make_schedule``);
    the escape channel receives R4's OWN validated NON-CONTINGENT outcome
    resolution (reused directly from
    ``worlds.abusive_r4_learned_helplessness_world.resolve_outcome``). This
    fully reproduces R1's bond-strengthening finding, R2/R3's window-
    narrowing/anchor-inversion finding, and R4's freeze finding, inside ONE
    substrate, before any recovery mechanism is touched.
  * RECOVERY (ticks T1..T1+T2) -- the ONLY manipulated variable. NO-SUPPORT
    arm: every channel continues EXACTLY as in induction (same abuser
    driver, same intermittent bond schedule, same non-contingent escape
    resolution) -- the failable control. SUPPORT arm: ONE mechanical world
    event, ``introduce_support()``, fires at tick T1 -- it (a) adds an
    ``also_attended_by`` edge to a fixed-calm outside Agent and flips
    ``has_outside_regulator=1.0`` (R3's OWN unmodified outside-regulator
    mechanism, now exercised for the first time in this line from an
    ALREADY-NARROWED window -- R3's own honest residual named this exact
    path as built-but-untested), (b) stops delivering fresh bond events
    (representing reduced abuser access) so ``r5_bond_extinguish`` dominates,
    and (c) begins delivering periodic, FIXED-SCHEDULE support evidence onto
    the contingency-restore channel, and switches any FUTURE escape attempt
    to CONTINGENT resolution (support makes a genuine attempt possible).

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER.
Every decision -- the bond accrual/decay, the entrainment, the window
narrowing/widening, the prior tracking, the escape appraisal/choice, the
contingency-belief revision -- is the graph's decision, entirely inside the
four pre-existing, unmodified seeds plus the two small R5 rules. The
adapter's only conditionals are over WORLD/ARM state: which phase (an
episode-clock comparison), which arm (support vs no-support, an
experimental-arm selection made ONCE per trajectory by the runner/
experimenter, exactly as every prior rung in this line does), and a FIXED
periodic schedule for support-evidence delivery -- never a branch over the
victim's own graph state. NO reward/punishment anywhere: every delivered
value is a world-side magnitude or state fact (a harm/relief magnitude, a
tension-trickle magnitude, an escape outcome, a support-evidence magnitude),
never a scored choice -- see Part C.2 of ABUSIVE_R5_RECOVERY_PREREG.md.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import substrate_rs as srs                                   # noqa: E402
from substrate.seed_loader import manifest_for                # noqa: E402
from domains.core_emotions_weight import quantize_weight      # noqa: E402
from worlds.traumatic_bond_r1_world import make_schedule       # noqa: E402
from worlds.abusive_r4_learned_helplessness_world import resolve_outcome  # noqa: E402

# ---- FROZEN world constants (pre-registered, ABUSIVE_R5_RECOVERY_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults -- BYTE-IDENTICAL to
# R2/R3's own frozen constants; R5 reuses R2/R3's exact abuser mechanism)
ABUSER_HALF_WIDTH = 100.0
K_ACC = 1.0
LEAK = 0.02
DISCHARGE = 0.90
RECOVER_FLOOR = 25.0

# victim window / entrainment (arousal_window_coreg, block 239000 defaults --
# same convention as R2/R3)
VICTIM_HALF_WIDTH = 10.0
K_SELF = 0.15
K_CO = 0.35

# outside regulator (R3's own convention, byte-identical constants)
CALM_AROUSAL = 0.0

TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10

# bond channel (mood_r1 / traumatic_bond_r1, block 283000 defaults, EXCEPT
# gain -- see PREREG Sec. 3.1: R1's own frozen gain=3.5 was validated for
# exactly ONE 36-tick episode from a fresh substrate and provably diverges
# (unbounded super-linear growth) under R5's much longer, multi-block
# delivery; gain=1.0 is mood_r1's OWN pinned general-purpose default, a
# disclosed deviation chosen for numerical stability, not for a preferred
# result -- 1.0/1.5/2.0 all behaved qualitatively the same in piloting)
BOND_LR = 0.3
BOND_MOMENTUM_LR = 0.3
BOND_GAIN = 1.0
BOND_MAGNITUDE = 10.0
BOND_MAGNITUDE_JITTER = 0.5

# escape channel (core_emotions / abusive_r4_learned_helplessness, block
# 292000 defaults -- same convention as R4)
ESCAPE_VALUE = 10.0
ATTEMPT_COST = 3.0
ESCAPE_LR = 0.3
ESCAPE_P0 = 0.5

# ---- R5's OWN new constants (pilot-chosen, see PREREG Sec. 3)
DECAY_RATE = 0.01          # r5_bond_extinguish's per-tick proportional leak
SUPPORT_LR = 0.3           # r5_contingency_restore's EMA rate (matches R4's
#                             own pinned belief-update rate, disclosed, not
#                             re-tuned)
SUPPORT_INTERVAL = 20      # ticks between support-evidence deliveries
SUPPORT_OUTCOME = 1.0      # the delivered evidence magnitude (a demonstrated
#                             / witnessed controllable outcome)

ARM_NAMES = ("support", "no_support")


class AbusiveR5RecoveryWorld:
    """One ABUSER Agent (snap_frustration + R1's Partner-role attrs), one
    VICTIM Agent (arousal_window_coreg + R3's prior attrs + R1's MoodTask/
    Mood + R4's EscapeDecision/HeldEmotionParams/Appraisals), and, from tick
    T1 onward in the support arm ONLY, one fixed-calm OUTSIDE Agent. NO
    decision here -- only world delivery + read-back."""

    def __init__(self, arm: str, *, abuser_half_width=ABUSER_HALF_WIDTH,
                 victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE,
                 recover_floor=RECOVER_FLOOR, k_self=K_SELF, k_co=K_CO,
                 trickle_mag=TRICKLE_MAG, calm_arousal=CALM_AROUSAL,
                 bond_lr=BOND_LR, bond_momentum_lr=BOND_MOMENTUM_LR,
                 bond_gain=BOND_GAIN, bond_magnitude=BOND_MAGNITUDE,
                 escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST,
                 escape_lr=ESCAPE_LR, escape_p0=ESCAPE_P0,
                 decay_rate=DECAY_RATE, support_lr=SUPPORT_LR,
                 support_interval=SUPPORT_INTERVAL,
                 support_outcome=SUPPORT_OUTCOME):
        if arm not in ARM_NAMES:
            raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")
        self.arm = arm
        self.trickle_mag = float(trickle_mag)
        self.bond_magnitude = float(bond_magnitude)
        self.support_interval = int(support_interval)
        self.support_outcome = float(support_outcome)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "r5_root"})
        for seed in ("affective_state_core", "mood_r1_task", "mood_r1",
                     "core_emotions", "snap_frustration", "arousal_window_coreg",
                     "traumatic_bond_r1", "abusive_r2_cycle_limit",
                     "abusive_r3_coercive_control", "abusive_r4_learned_helplessness",
                     "abusive_r5_recovery"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract + is_abuser=1.0 (R3's role
        # attribute) + R1's Partner-role attrs (value/e_bond/e_extinct/
        # decay_rate) directly on the SAME Agent node -- the bond IS to the
        # abuser, a disclosed R5-specific composition choice (see module
        # docstring). Deliberately carries NO arousal_window_coreg-specific
        # bookkeeping key and no `regulated` key, matching R2/R3's own
        # omission convention exactly.
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

        # Partner-role attrs, directly on the abuser Agent node (tb_bond_accrue
        # / r5_bond_extinguish match on `partner` structurally -- any node with
        # these edges/attrs qualifies, node-type string is not a filter).
        self.s.set_attr(self.abuser, "value", 0.0)
        self.s.set_attr(self.abuser, "e_bond", -1.0)
        self.s.set_attr(self.abuser, "e_extinct", -1.0)
        self.s.set_attr(self.abuser, "decay_rate", float(decay_rate))

        # ---------------------------------------------------------- VICTIM
        # arousal_window_coreg's full contract (+R3's has_outside_regulator
        # flag), deliberately carrying NO snap_frustration-specific key and
        # no `cr_epoch` key -- same omission convention as R2/R3 (blocks
        # coreg_pull / snap_coreg_pull from ever matching; r2/r3's own
        # frustration-routed entrainment rules supersede them).
        self.victim = self.s.add_node("Agent", {"role": "victim"})
        self.vaff = self.s.add_node("AffectiveState", dict(
            name="victim_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            tick_epoch=0.0, sr_epoch=0.0, pcr_epoch=0.0, tb_epoch=-1.0,
            k_self=float(k_self), k_co=float(k_co), setpoint=float(SETPOINT),
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0, got_coreg=0.0,
            has_outside_regulator=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_affective_state", self.vaff)

        hw_v = float(victim_half_width)
        self.vwot = self.s.add_node("WindowOfTolerance", dict(
            name="victim_window", lo=-hw_v, hi=hw_v, half_width=hw_v,
            widen_delta=2.0, narrow_delta=2.0, min_half_width=5.0,
            safety_prior=0.5, safety_step=0.03, widen_count=0.0, narrow_count=0.0,
            others_trust=0.5, self_worth=0.5, pn_last_narrow=0.0, pn_last_widen=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_window", self.vwot)

        self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)
        self.inner.add_edge_unchecked(self.victim, "bonded_to", self.abuser)

        # -------------------------------------------------- VICTIM: bond channel
        # R1's MoodTask + Mood, unmodified contract, on the SAME victim node.
        mt = dict(v=0.0, lr=float(bond_lr), r=0.0, raw_rpe=0.0, bias=0.0,
                  decision=0.0, reward_got=0.0, cum_reward=0.0,
                  accept_thresh=0.0, input_epoch=0.0,
                  e_dec=-1.0, e_acc=-1.0, e_rpe=-1.0, e_learn=-1.0)
        self.mt = self.s.add_node("MoodTask", mt)
        self.inner.add_edge_unchecked(self.victim, "has_mood_task", self.mt)

        md = dict(enabled=1.0, momentum=0.0, gain=float(bond_gain),
                  momentum_lr=float(bond_momentum_lr), e_bias=-1.0, e_mom=-1.0)
        self.mood = self.s.add_node("Mood", md)
        self.inner.add_edge_unchecked(self.victim, "has_mood", self.mood)

        # -------------------------------------------------- VICTIM: escape channel
        # R4's HeldEmotionParams + two candidate Appraisals + EscapeDecision,
        # unmodified contract, on the SAME victim node, plus R5's own
        # support_epoch/support_processed_epoch/support_outcome/support_lr
        # attrs (the second, independent evidence channel).
        ep = dict(enabled=1.0, w_supergraph=0.0, mood_bias=0.0, residual_thresh=100.0,
                  high_arousal=800.0, mid_arousal=400.0, low_arousal=50.0, comms_on=0.0)
        ep["w_supergraph_q"], ep["w_scale_bits"] = quantize_weight(ep["w_supergraph"])
        self.ep = self.s.add_node("HeldEmotionParams", ep)
        self.inner.add_edge_unchecked(self.victim, "has_emotion_params", self.ep)

        appr_defaults = dict(
            appraised=1.0, individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
            collective_success=0.0, collective_success_prev=0.0, contribution_by_self=0.0,
            observed_by_other=0.0, valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
            attachment=0.0, regroundable=0.0, contamination=0.0, was_engaged=0.0,
            residual=0.0, residual_prev=0.0, threat=0.0, threat_c0=0.0, threat_half_life=1.0,
            threat_last_refresh=0.0, threat_now_epoch=0.0, t_present=100.0, v_max=0.0,
            step=0.0, step_prev=0.0, attach_v0=0.0, attach_k_now=0.0, attach_k_prev=0.0)

        at = dict(appr_defaults); at.update(action=1.0)
        self.attempt = self.s.add_node("Appraisal", at)
        self.inner.add_edge_unchecked(self.victim, "has_appraisal", self.attempt)
        self.inner.add_edge_unchecked(self.victim, "has_candidate", self.attempt)

        st = dict(appr_defaults); st.update(action=0.0)
        self.stay = self.s.add_node("Appraisal", st)
        self.inner.add_edge_unchecked(self.victim, "has_appraisal", self.stay)
        self.inner.add_edge_unchecked(self.victim, "has_candidate", self.stay)

        self.dec = self.s.add_node("EscapeDecision", dict(
            contingency_prior=float(escape_p0), lr=float(escape_lr),
            escape_value=float(escape_value), attempt_cost=float(attempt_cost),
            chosen_action=-1.0, outcome=-1.0, outcome_epoch=-1.0, processed_epoch=-1.0,
            tick_epoch=0.0,
            support_epoch=-1.0, support_processed_epoch=-1.0,
            support_outcome=0.0, support_lr=float(support_lr)))
        self.inner.add_edge_unchecked(self.victim, "has_escape_decision", self.dec)

        # -------------------------------------------------- OUTSIDE (recovery arm only)
        self.outside = None
        self.oaff = None
        self.support_active = False
        self._next_support_tick = None

        self.epoch = 0
        self.n_attempts_this_phase = 0
        self.pending_attempt = False
        self.escape_arm_current = "noncontingent"   # world/experimenter fact
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        aa = self._attrs(self.aaff)
        ab = self._attrs(self.abuser)
        va = self._attrs(self.vaff)
        vw = self._attrs(self.vwot)
        dec = self._attrs(self.dec)
        row = dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"],
            bond_value=ab["value"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_in_episode=va["in_episode"], victim_got_coreg=va["got_coreg"],
            half_width=vw["half_width"], others_trust=vw["others_trust"],
            self_worth=vw["self_worth"], widen_count=vw["widen_count"],
            narrow_count=vw["narrow_count"],
            contingency_prior=dec["contingency_prior"], chosen_action=dec["chosen_action"],
            anchor_distance=abs(va["arousal"] - aa["arousal"]))
        if self.support_active:
            row["outside_arousal"] = self._attrs(self.oaff)["arousal"]
            row["outside_distance"] = abs(va["arousal"] - row["outside_arousal"])
        return row

    # ---------------------------------------------------- introduce_support
    def introduce_support(self):
        """ONE mechanical world event: attach a fixed-calm outside Agent via
        an `also_attended_by` edge (R3's OWN proven-safe outside-regulator
        mechanism) and flip `has_outside_regulator=1.0`. Called ONCE, at the
        tick the runner/experimenter designates as the start of the
        recovery phase in the support arm -- an experimental-arm decision,
        never a graph-state-dependent branch."""
        if self.outside is not None:
            return
        self.outside = self.s.add_node("Agent", {"role": "outside", "regulated": 1.0})
        self.oaff = self.s.add_node("AffectiveState", dict(
            name="outside_affect", baseline=1.0, valence=0.0,
            arousal=float(CALM_AROUSAL), setpoint=float(CALM_AROUSAL),
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0, is_abuser=0.0, tick_epoch=float(self.epoch)))
        self.inner.add_edge_unchecked(self.outside, "has_affective_state", self.oaff)
        self.inner.add_edge_unchecked(self.victim, "also_attended_by", self.outside)
        self.s.set_attr(self.vaff, "has_outside_regulator", 1.0)
        self.support_active = True
        self._next_support_tick = self.epoch + self.support_interval
        self.escape_arm_current = "contingent"

    # ------------------------------------------------------------------- step
    def step(self, *, deliver_bond_event=0.0, tension_jitter=0.0):
        """Advance one tick: deliver the tension trickle (always), the bond
        event (mechanical, world-scheduled), resolve any pending escape
        attempt (mechanical, per-arm), and, once support is active, deliver
        periodic support evidence on a FIXED schedule. Then run_rules() and
        read back. NO decision here."""
        self.epoch += 1
        e = float(self.epoch)

        # tension trickle -- continuous, identical in both arms/phases (the
        # abuser's own driver never changes; only the victim's response to
        # it does, via the graph's own rules).
        self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + tension_jitter))
        self.s.set_attr(self.gb, "armed", 1.0)

        # bond channel -- a mechanical per-tick magnitude, world-scheduled.
        self.s.set_attr(self.mt, "r", float(deliver_bond_event))
        self.s.set_attr(self.mt, "input_epoch", e)

        # escape channel -- resolve the PREVIOUS tick's attempt, if any.
        if self.pending_attempt:
            outcome = resolve_outcome(
                "contingent" if self.escape_arm_current == "contingent" else "noncontingent")
            self.s.set_attr(self.dec, "outcome", float(outcome))
            self.s.set_attr(self.dec, "outcome_epoch", e)
            self.pending_attempt = False
        self.s.set_attr(self.dec, "tick_epoch", e)

        # support-evidence channel -- FIXED schedule, never conditioned on
        # the victim's own chosen_action (Part C.2).
        if self.support_active and self.epoch >= self._next_support_tick:
            self.s.set_attr(self.dec, "support_outcome", float(self.support_outcome))
            self.s.set_attr(self.dec, "support_epoch", e)
            self._next_support_tick = self.epoch + self.support_interval

        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        if self.support_active:
            self.s.set_attr(self.oaff, "tick_epoch", e)

        self.inner.run_rules()
        row = self.readout()
        self.log.append(row)
        if row["chosen_action"] == 1.0:
            self.pending_attempt = True
            self.n_attempts_this_phase += 1
        return row

    def run_phase(self, T, *, bond_schedule, rng=None):
        """Deliver T ticks. `bond_schedule` is a pre-generated, mechanical
        per-tick event stream for the bond channel (length T; 0.0 entries
        deliver no event). Tension jitter (if `rng` given) is drawn fresh
        each tick, matching R2/R3's own convention. Returns the phase's
        escape-attempt rate (n_attempts / T) alongside the final readout;
        resets the attempt counter for the NEXT phase."""
        self.n_attempts_this_phase = 0
        row = None
        for t in range(T):
            jitter = 0.0
            if rng is not None:
                jitter = float(rng.normal(0.0, self.trickle_mag * TRICKLE_JITTER_FRAC))
            row = self.step(deliver_bond_event=float(bond_schedule[t]), tension_jitter=jitter)
        row = dict(row)
        row["attempt_rate"] = self.n_attempts_this_phase / T
        row["n_attempts"] = self.n_attempts_this_phase
        return row

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()


BOND_BLOCK_H = 18   # R1's OWN frozen H=R=18 per block (ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md
BOND_BLOCK_T = 36   # Sec. 4) -- kept BYTE-IDENTICAL, not scaled up. A pilot check (see
#                     PREREG Sec. 3) found that sizing ONE intermittent multiset to fill
#                     an entire long phase (hundreds of ticks) pushes mood_r1's own
#                     mood-congruent bias amplification (gain=3.5) into an unbounded,
#                     super-linear-growth regime -- R1's own prereg already named this
#                     class of instability at high gain ("H=15,gain=6... the SEPARATION
#                     FLIPS THE WRONG WAY", "well clear of the explosive regime"). R5
#                     stays inside R1's own validated operating point by delivering a
#                     FIXED NUMBER of R1-sized blocks, never a schedule that scales with
#                     the phase length.


def make_bond_schedule(T, rng, *, n_blocks=1, magnitude=BOND_MAGNITUDE,
                        jitter=BOND_MAGNITUDE_JITTER, active=True):
    """MECHANICAL world-side event stream for the bond channel over T ticks.
    Delivers `n_blocks` of R1's OWN validated intermittent (unpredictable,
    `rng.shuffle`) H=R=18/T=36 multiset back to back at the START of the
    phase, then ZERO for the remainder (`T - n_blocks*36` ticks) -- the
    total event count is bounded regardless of how long the phase itself
    runs (see `BOND_BLOCK_H`/`BOND_BLOCK_T` above). `active=False` delivers
    an all-zero stream for the WHOLE phase (no fresh events at all -- the
    "reduced abuser access" world fact the support arm's recovery phase
    enacts)."""
    if not active:
        return [0.0] * T
    events = []
    for _ in range(n_blocks):
        events.extend(make_schedule("intermittent", rng, h=BOND_BLOCK_H, r=BOND_BLOCK_H,
                                     magnitude=magnitude, jitter=jitter))
    if len(events) > T:
        raise ValueError(f"n_blocks*{BOND_BLOCK_T} ({len(events)}) exceeds phase length T={T}")
    return events + [0.0] * (T - len(events))
