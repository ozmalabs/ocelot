"""AbusiveR7ReturnCycleWorld -- a MECHANICAL dyad+resources world for the
ABUSIVE-DYNAMICS R7 rung (block 316000, "the return cycle: residual bond +
post-separation contact + post-leaving material collapse -> a new Return
Appraisal"). Composes ``abusive_r5_recovery`` (block 295000, UNMODIFIED,
transitively pulling ``traumatic_bond_r1``/``abusive_r2_cycle_limit``/
``abusive_r3_coercive_control``/``abusive_r4_learned_helplessness``) with
FOUR new rules of its own (``seeds/abusive_r7_return_cycle.json``):
``r7_resource_collapse_sever``, ``r7_appraise_return``, ``r7_appraise_remain``,
``r7_choose``.

THREE STRUCTURAL PHASES per trajectory (ABUSIVE_R7_RETURN_CYCLE_PREREG.md
Part D subsection, "what R7 changes about minimal induction / settled end"):

  * PHASE 1 -- INDUCTION (ticks 0..T1) -- BYTE-IDENTICAL to R5's own
    induction: R1's own intermittent bond schedule, R2/R3's continuous
    abuser tension trickle, R4's own non-contingent escape resolution.
    Reproduces R5's own trapped state exactly (R5's own T1=396 reused
    UNCHANGED -- R7 does not re-derive or lengthen R5's own trap-formation
    timescale).
  * PHASE 2 -- RECOVERY-THEN-LEAVE (ticks T1..T1+T2) -- R5's own SUPPORT
    arm's recovery mechanism, UNCHANGED (``introduce_support()``, R5's own
    method, reused directly): an outside regulator attaches, the bond
    channel stops receiving fresh events (letting ``r5_bond_extinguish``'s
    decay dominate), and periodic support evidence begins restoring the
    escape-contingency belief. R7 reuses R5's own FULL T2=396 recovery
    window UNCHANGED -- this is the SAME window R5's own confirmatory run
    used to reach ``attempt_rate~=0.95`` AND the SAME window that lets the
    bond decay to R5's own reported residual (``~9.60``) via the SAME fixed
    ``decay_rate=0.01`` -- R7's whole premise (Part C of the scoping doc)
    is that THIS SPECIFIC residual, not a fresh guess, is what a leave-pull
    has to work against, so the window that produces it is reused exactly,
    not re-derived. At the END of Phase 2 (tick T1+T2), the mechanical
    ``leave()`` world event fires ONCE: it removes the victim's
    ``attended_by`` edge to the abuser (R2/R3's entrainment machinery
    becomes structurally inert -- no coupling to entrain through) and sets
    ``ReturnDecision.left_at_tick`` to that fixed tick.
  * PHASE 3 -- POST-LEAVE TEST (ticks T1+T2..T1+T2+T3) -- genuinely new.
    Per-arm, TWO independent drivers may be active: (a) a SPARSE,
    post-leaving-specific honeymoon-contact bond-event schedule (feeding
    R1's OWN ``tb_bond_accrue``, UNMODIFIED -- see ``make_honeymoon_
    schedule`` below), and (b) the material-resource-collapse schedule
    (``r7_resource_collapse_sever``, gated on the arm's ``collapse_on``
    switch). ``r7_choose``'s Argmax (return vs. remain_left) runs every
    tick from the moment leaving happens; the measured ``return_rate`` is
    the fraction of Phase-3 ticks where ``chosen_action == 1.0``.

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER.
Every decision -- the bond accrual/decay, the entrainment, the window
narrowing/widening, the prior tracking, the escape appraisal/choice, the
resource severing, the return/remain appraisal and choice -- is the graph's
decision, entirely inside R5's own four composed seeds plus R7's own four
new rules. The adapter's only conditionals are over WORLD/ARM state: which
phase (an episode-clock comparison), which arm (a 2x2 factorial over
honeymoon-contact-on/off x resource-collapse-on/off, an experimental-arm
selection made ONCE per trajectory, exactly as every prior rung in this
line), when ``leave()`` fires (a FIXED tick), and a FIXED periodic schedule
for honeymoon-contact delivery -- never a branch over the victim's own graph
state. NO reward/punishment anywhere: every delivered value is a world-side
magnitude or state fact (a harm/relief magnitude, a tension-trickle
magnitude, an escape outcome, a support-evidence magnitude, a honeymoon-
contact magnitude, a resource-severing schedule), never a scored choice --
see Part D of ABUSIVE_R7_RETURN_CYCLE_PREREG.md.
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

# ---- FROZEN world constants (pre-registered, ABUSIVE_R7_RETURN_CYCLE_PREREG.md)
# Phase 1/2 constants are BYTE-IDENTICAL to R5's own frozen values (Part D:
# Phase 1 reuses R5's own already-validated minimal parameters exactly).
SETPOINT = 0.0

ABUSER_HALF_WIDTH = 100.0
K_ACC = 1.0
LEAK = 0.02
DISCHARGE = 0.90
RECOVER_FLOOR = 25.0

VICTIM_HALF_WIDTH = 10.0
K_SELF = 0.15
K_CO = 0.35

CALM_AROUSAL = 0.0

TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10

BOND_LR = 0.3
BOND_MOMENTUM_LR = 0.3
BOND_GAIN = 1.0
BOND_MAGNITUDE = 10.0
BOND_MAGNITUDE_JITTER = 0.5

ESCAPE_VALUE = 10.0
ATTEMPT_COST = 3.0
ESCAPE_LR = 0.3
ESCAPE_P0 = 0.5

DECAY_RATE = 0.01
SUPPORT_LR = 0.3
SUPPORT_INTERVAL = 20
SUPPORT_OUTCOME = 1.0

# ---- R7's OWN new constants (pilot-chosen, see PREREG Sec. 3)
N_RESOURCE_NODES = 4                  # housing, joint finances, transportation,
#                                        health-insurance access (A7's own
#                                        antecedents/consequences list)
RESOURCE_NAMES = ("housing", "joint_finances", "transportation", "health_insurance")
RESOURCE_SEVER_STEP = 25.0            # per-node stagger, ticks AFTER left_at_tick
#                                        (node i severs at left_at_tick +
#                                        (i+1)*RESOURCE_SEVER_STEP) -- mechanical
#                                        per-node setup, identical in KIND to
#                                        N2's own (i+1)*EPISODE_TICKS idiom.
#                                        Pilot-chosen (PREREG Sec. 3) so the
#                                        four-node population collapses over
#                                        roughly the first half of Phase 3,
#                                        not instantaneously.
RESOURCE_VALUE = 10.0                 # value of ONE intact resource to the
#                                        remain_left candidate's benefit.
#                                        Pilot-chosen (PREREG Sec. 3) so the
#                                        FULL 4-node safety net
#                                        (N_RESOURCE_NODES*RESOURCE_VALUE=40)
#                                        is comparable to several honeymoon-
#                                        contact events' cumulative pull, not
#                                        so small that ONE event already
#                                        swamps it regardless of collapse.
BOND_WEIGHT = 1.0                     # scales partner.value into the return
#                                        candidate's benefit
RETURN_COST = 2.0                     # fixed structural cost of going back
#                                        (mirrors ATTEMPT_COST's role exactly)
HONEYMOON_INTERVAL = 20               # ticks between sparse post-leaving
#                                        contact events (honeymoon-on arms).
#                                        Pilot-chosen (PREREG Sec. 3).
HONEYMOON_MAGNITUDE = BOND_MAGNITUDE  # reuses R1's own frozen per-event
#                                        magnitude, not a fresh number
HONEYMOON_JITTER = BOND_MAGNITUDE_JITTER

T1 = 396     # Phase 1 -- R5's own induction length, UNCHANGED
T2 = 396     # Phase 2 -- R5's own recovery length, UNCHANGED
T3 = 180     # Phase 3 -- post-leave test (pilot-chosen, PREREG Sec. 3)

ARM_CONFIG = {
    "both_drivers":   dict(honeymoon_on=True,  collapse_on=True),
    "honeymoon_only": dict(honeymoon_on=True,  collapse_on=False),
    "collapse_only":  dict(honeymoon_on=False, collapse_on=True),
    "neither":        dict(honeymoon_on=False, collapse_on=False),
}
ARM_NAMES = tuple(ARM_CONFIG.keys())


class AbusiveR7ReturnCycleWorld:
    """One ABUSER Agent (snap_frustration + R1's Partner-role attrs), one
    VICTIM Agent (arousal_window_coreg + R3's prior attrs + R1's MoodTask/
    Mood + R4's EscapeDecision/HeldEmotionParams/Appraisals + R7's own
    ReturnDecision/resource population/return-remain Appraisals), and, from
    tick T1 onward, one fixed-calm OUTSIDE Agent (R5's own recovery
    mechanism). NO decision here -- only world delivery + read-back."""

    def __init__(self, arm: str, *, n_resource_nodes=N_RESOURCE_NODES,
                 resource_sever_step=RESOURCE_SEVER_STEP,
                 resource_value=RESOURCE_VALUE, bond_weight=BOND_WEIGHT,
                 return_cost=RETURN_COST,
                 honeymoon_interval=HONEYMOON_INTERVAL,
                 honeymoon_magnitude=HONEYMOON_MAGNITUDE,
                 honeymoon_jitter=HONEYMOON_JITTER):
        if arm not in ARM_CONFIG:
            raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")
        self.arm = arm
        cfg = ARM_CONFIG[arm]
        self.honeymoon_on = bool(cfg["honeymoon_on"])
        self.collapse_on = bool(cfg["collapse_on"])
        self.trickle_mag = float(TRICKLE_MAG)
        self.bond_magnitude = float(BOND_MAGNITUDE)
        self.support_interval = int(SUPPORT_INTERVAL)
        self.support_outcome = float(SUPPORT_OUTCOME)
        self.n_resource_nodes = int(n_resource_nodes)
        self.resource_sever_step = float(resource_sever_step)
        self.honeymoon_interval = int(honeymoon_interval)
        self.honeymoon_magnitude = float(honeymoon_magnitude)
        self.honeymoon_jitter = float(honeymoon_jitter)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "r7_root"})
        for seed in ("affective_state_core", "mood_r1_task", "mood_r1",
                     "core_emotions", "snap_frustration", "arousal_window_coreg",
                     "traumatic_bond_r1", "abusive_r2_cycle_limit",
                     "abusive_r3_coercive_control", "abusive_r4_learned_helplessness",
                     "abusive_r5_recovery", "abusive_r7_return_cycle"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # BYTE-IDENTICAL to R5's own abuser construction.
        self.abuser = self.s.add_node("Agent", {"role": "abuser"})
        self.aaff = self.s.add_node("AffectiveState", dict(
            name="abuser_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0, is_abuser=1.0,
            frustration=0.0, setpoint=float(SETPOINT), k_acc=float(K_ACC),
            leak=float(LEAK), discharge=float(DISCHARGE),
            recover_floor=float(RECOVER_FLOOR),
            snapped=0.0, in_snap=0.0, snap_count=0.0, snap_magnitude=0.0,
            snap_directed=0.0, snap_undirected=0.0, last_trigger_mag=0.0,
            tick_epoch=0.0, leak_epoch=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_affective_state", self.aaff)

        hw_a = float(ABUSER_HALF_WIDTH)
        self.awot = self.s.add_node("WindowOfTolerance", dict(
            name="abuser_window", lo=-hw_a, hi=hw_a, half_width=hw_a))
        self.inner.add_edge_unchecked(self.abuser, "has_window", self.awot)

        self.gb = self.s.add_node("GoalBlock", dict(
            name="tension_trigger", magnitude=0.0, armed=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_goal_block", self.gb)

        # Partner-role attrs, directly on the abuser Agent node.
        self.s.set_attr(self.abuser, "value", 0.0)
        self.s.set_attr(self.abuser, "e_bond", -1.0)
        self.s.set_attr(self.abuser, "e_extinct", -1.0)
        self.s.set_attr(self.abuser, "decay_rate", float(DECAY_RATE))

        # ---------------------------------------------------------- VICTIM
        self.victim = self.s.add_node("Agent", {"role": "victim"})
        self.vaff = self.s.add_node("AffectiveState", dict(
            name="victim_affect", baseline=1.0, valence=0.0, arousal=SETPOINT,
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0,
            tick_epoch=0.0, sr_epoch=0.0, pcr_epoch=0.0, tb_epoch=-1.0,
            k_self=float(K_SELF), k_co=float(K_CO), setpoint=float(SETPOINT),
            dysregulated=0.0, dysreg_kind=0.0, in_episode=0.0, got_coreg=0.0,
            has_outside_regulator=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_affective_state", self.vaff)

        hw_v = float(VICTIM_HALF_WIDTH)
        self.vwot = self.s.add_node("WindowOfTolerance", dict(
            name="victim_window", lo=-hw_v, hi=hw_v, half_width=hw_v,
            widen_delta=2.0, narrow_delta=2.0, min_half_width=5.0,
            safety_prior=0.5, safety_step=0.03, widen_count=0.0, narrow_count=0.0,
            others_trust=0.5, self_worth=0.5, pn_last_narrow=0.0, pn_last_widen=0.0))
        self.inner.add_edge_unchecked(self.victim, "has_window", self.vwot)

        self.attended = True
        self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)
        self.inner.add_edge_unchecked(self.victim, "bonded_to", self.abuser)

        # -------------------------------------------------- VICTIM: bond channel
        mt = dict(v=0.0, lr=float(BOND_LR), r=0.0, raw_rpe=0.0, bias=0.0,
                  decision=0.0, reward_got=0.0, cum_reward=0.0,
                  accept_thresh=0.0, input_epoch=0.0,
                  e_dec=-1.0, e_acc=-1.0, e_rpe=-1.0, e_learn=-1.0)
        self.mt = self.s.add_node("MoodTask", mt)
        self.inner.add_edge_unchecked(self.victim, "has_mood_task", self.mt)

        md = dict(enabled=1.0, momentum=0.0, gain=float(BOND_GAIN),
                  momentum_lr=float(BOND_MOMENTUM_LR), e_bias=-1.0, e_mom=-1.0)
        self.mood = self.s.add_node("Mood", md)
        self.inner.add_edge_unchecked(self.victim, "has_mood", self.mood)

        # -------------------------------------------------- VICTIM: escape channel
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
            contingency_prior=float(ESCAPE_P0), lr=float(ESCAPE_LR),
            escape_value=float(ESCAPE_VALUE), attempt_cost=float(ATTEMPT_COST),
            chosen_action=-1.0, outcome=-1.0, outcome_epoch=-1.0, processed_epoch=-1.0,
            tick_epoch=0.0,
            support_epoch=-1.0, support_processed_epoch=-1.0,
            support_outcome=0.0, support_lr=float(SUPPORT_LR)))
        self.inner.add_edge_unchecked(self.victim, "has_escape_decision", self.dec)

        # -------------------------------------------------- VICTIM: R7's own
        # RETURN/REMAIN decision + candidate Appraisals (has_return_candidate,
        # DISTINCT from has_candidate above) + the resource population.
        rappr = dict(appr_defaults)
        rt = dict(rappr); rt.update(action=1.0)
        self.ret_c = self.s.add_node("Appraisal", rt)
        self.inner.add_edge_unchecked(self.victim, "has_appraisal", self.ret_c)
        self.inner.add_edge_unchecked(self.victim, "has_return_candidate", self.ret_c)

        rl = dict(rappr); rl.update(action=0.0)
        self.remain_c = self.s.add_node("Appraisal", rl)
        self.inner.add_edge_unchecked(self.victim, "has_appraisal", self.remain_c)
        self.inner.add_edge_unchecked(self.victim, "has_return_candidate", self.remain_c)

        self.ret_dec = self.s.add_node("ReturnDecision", dict(
            bond_weight=float(bond_weight), return_cost=float(return_cost),
            resource_value=float(resource_value), resource_intact_count=float(self.n_resource_nodes),
            chosen_action=-1.0, left_at_tick=-1.0,
            collapse_on=(1.0 if self.collapse_on else 0.0)))
        self.inner.add_edge_unchecked(self.victim, "has_return_decision", self.ret_dec)

        self.resources = []
        for i, name in enumerate(RESOURCE_NAMES[:self.n_resource_nodes]):
            rn = self.s.add_node("ResourceNode", dict(
                name=name, tick_epoch=0.0,
                sever_at_tick=-1.0,   # set by leave() once the fixed leave tick is known
                severed=0.0))
            self.inner.add_edge_unchecked(self.victim, "resource_edge", rn)
            self.resources.append(rn)
        self._resource_sever_offsets = [(i + 1) * self.resource_sever_step
                                         for i in range(self.n_resource_nodes)]

        # -------------------------------------------------- OUTSIDE (Phase 2+)
        self.outside = None
        self.oaff = None
        self.support_active = False
        self._next_support_tick = None
        self.left = False
        self._next_honeymoon_tick = None

        self.epoch = 0
        self.n_attempts_this_phase = 0
        self.n_return_this_phase = 0
        self.pending_attempt = False
        self.escape_arm_current = "noncontingent"
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
        rdec = self._attrs(self.ret_dec)
        row = dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"],
            bond_value=ab["value"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            half_width=vw["half_width"], others_trust=vw["others_trust"],
            self_worth=vw["self_worth"], widen_count=vw["widen_count"],
            narrow_count=vw["narrow_count"],
            contingency_prior=dec["contingency_prior"], chosen_action=dec["chosen_action"],
            left_at_tick=rdec["left_at_tick"],
            return_chosen_action=rdec["chosen_action"],
            resource_intact_count=rdec["resource_intact_count"])
        if self.support_active:
            row["outside_arousal"] = self._attrs(self.oaff)["arousal"]
        return row

    # ------------------------------------------------------ introduce_support
    def introduce_support(self):
        """R5's OWN mechanical world event, reused UNCHANGED: attach a
        fixed-calm outside Agent via an ``also_attended_by`` edge (R3's own
        proven-safe outside-regulator mechanism) and flip
        ``has_outside_regulator=1.0``. Called ONCE, at the start of Phase 2 --
        an experimental-arm/phase decision, never a graph-state-dependent
        branch."""
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

    # ------------------------------------------------------------------ leave
    def leave(self):
        """THE mechanical ``leave()`` world event (Part B2 of the scoping
        doc): fires ONCE, at a FIXED tick (the Phase2/Phase3 boundary).
        Removes the victim's ``attended_by`` edge to the abuser (R2/R3's
        entrainment machinery becomes structurally inert -- no coupling to
        entrain through) and sets ``ReturnDecision.left_at_tick`` -- read by
        ``r7_resource_collapse_sever``'s and every R7 appraisal rule's
        ``where`` guard. Each ResourceNode's own ``sever_at_tick`` is set
        HERE too, relative to this fixed tick (a FIXED, disclosed
        post-leaving schedule, mechanical per-node setup, never a live
        decision)."""
        if self.left:
            return
        if self.attended:
            self.inner.remove_edge_unchecked(self.victim, "attended_by", self.abuser)
            self.attended = False
        left_tick = float(self.epoch)
        self.s.set_attr(self.ret_dec, "left_at_tick", left_tick)
        for rn, offset in zip(self.resources, self._resource_sever_offsets):
            self.s.set_attr(rn, "sever_at_tick", left_tick + offset)
        self.left = True
        if self.honeymoon_on:
            self._next_honeymoon_tick = self.epoch + self.honeymoon_interval

    # ------------------------------------------------------------------- step
    def step(self, *, deliver_bond_event=0.0, tension_jitter=0.0, honeymoon_rng=None):
        """Advance one tick: deliver the tension trickle (only while still
        attended -- once ``leave()`` has fired the abuser's tension trickle
        no longer reaches an entrainment coupling, matching R2/R3's own
        structural-inertness finding), the bond event (mechanical,
        world-scheduled -- either the Phase-1 induction schedule or, post-
        leave, the sparse honeymoon-contact schedule), resolve any pending
        escape attempt, deliver periodic support evidence once active, and
        mechanically increment every ResourceNode's own tick counter. Then
        run_rules() and read back. NO decision here."""
        self.epoch += 1
        e = float(self.epoch)

        if self.attended:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + tension_jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        else:
            self.s.set_attr(self.gb, "armed", 0.0)

        self.s.set_attr(self.mt, "r", float(deliver_bond_event))
        self.s.set_attr(self.mt, "input_epoch", e)

        if self.pending_attempt:
            outcome = resolve_outcome(
                "contingent" if self.escape_arm_current == "contingent" else "noncontingent")
            self.s.set_attr(self.dec, "outcome", float(outcome))
            self.s.set_attr(self.dec, "outcome_epoch", e)
            self.pending_attempt = False
        self.s.set_attr(self.dec, "tick_epoch", e)

        if self.support_active and self.epoch >= self._next_support_tick:
            self.s.set_attr(self.dec, "support_outcome", float(self.support_outcome))
            self.s.set_attr(self.dec, "support_epoch", e)
            self._next_support_tick = self.epoch + self.support_interval

        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        if self.support_active:
            self.s.set_attr(self.oaff, "tick_epoch", e)
        for rn in self.resources:
            self.s.set_attr(rn, "tick_epoch", e)

        self.inner.run_rules()
        row = self.readout()
        self.log.append(row)
        if row["chosen_action"] == 1.0:
            self.pending_attempt = True
            self.n_attempts_this_phase += 1
        if self.left and row["return_chosen_action"] == 1.0:
            self.n_return_this_phase += 1
        return row

    def run_phase(self, T, *, bond_schedule, rng=None):
        """Deliver T ticks. ``bond_schedule`` is a pre-generated, mechanical
        per-tick event stream for the bond channel (length T). Returns the
        phase's escape-attempt rate AND (once leaving has happened)
        return_rate alongside the final readout; resets both counters for
        the NEXT phase."""
        self.n_attempts_this_phase = 0
        self.n_return_this_phase = 0
        row = None
        for t in range(T):
            jitter = 0.0
            if rng is not None:
                jitter = float(rng.normal(0.0, self.trickle_mag * TRICKLE_JITTER_FRAC))
            row = self.step(deliver_bond_event=float(bond_schedule[t]), tension_jitter=jitter)
        row = dict(row)
        row["attempt_rate"] = self.n_attempts_this_phase / T
        row["n_attempts"] = self.n_attempts_this_phase
        row["return_rate"] = self.n_return_this_phase / T
        row["n_return"] = self.n_return_this_phase
        return row

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()


BOND_BLOCK_H = 18
BOND_BLOCK_T = 36


def make_bond_schedule(T, rng, *, n_blocks=1, magnitude=BOND_MAGNITUDE,
                        jitter=BOND_MAGNITUDE_JITTER, active=True):
    """Phase-1 induction schedule -- BYTE-IDENTICAL to R5's own
    ``make_bond_schedule`` (reproduced here rather than imported, to keep
    R7's own world module self-contained the same way R5 reproduces rather
    than re-imports R1's constants)."""
    if not active:
        return [0.0] * T
    events = []
    for _ in range(n_blocks):
        events.extend(make_schedule("intermittent", rng, h=BOND_BLOCK_H, r=BOND_BLOCK_H,
                                     magnitude=magnitude, jitter=jitter))
    if len(events) > T:
        raise ValueError(f"n_blocks*{BOND_BLOCK_T} ({len(events)}) exceeds phase length T={T}")
    return events + [0.0] * (T - len(events))


def make_honeymoon_schedule(T, rng, *, interval=HONEYMOON_INTERVAL,
                             magnitude=HONEYMOON_MAGNITUDE,
                             jitter=HONEYMOON_JITTER, active=True):
    """THE HONEYMOON-PULL COMPONENT'S ONLY NEW MACHINERY -- a MECHANICAL,
    SPARSE, POST-LEAVING-SPECIFIC event stream for R1's OWN (UNMODIFIED)
    bond channel. Delivers ONE relief-shaped event (R1's own ``reliefs``
    magnitude formula: ``magnitude + N(0, jitter)``, reused verbatim) every
    ``interval`` ticks, zero otherwise -- unlike R1's own dense, within-
    relationship H=R=18 intermittent multiset, this is a sparse, purely
    positive (relief-only) contact schedule, representing occasional
    reconciliation contact (a call, a text, an apology) rather than an
    ongoing incident cycle. ``active=False`` (honeymoon-off arms) delivers
    an all-zero stream -- no post-leaving contact at all."""
    events = [0.0] * T
    if not active:
        return events
    t = interval - 1
    while t < T:
        events[t] = float(magnitude + rng.normal(0.0, jitter))
        t += interval
    return events
