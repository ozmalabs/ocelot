"""AbusiveN4BelievingAgentWorld -- a MECHANICAL abuser/victim/support-network
world for the ABUSIVE-DYNAMICS N4 rung (block 307000, "one non-doubting
agent restores a support edge" -- ABUSIVE_RELATIONSHIPS_NETWORK.md Part E,
N4; the network line's own recovery rung, tying directly to the dyad line's
R5; the LAST rung of the whole abusive-relationships line).

Composes TWO already-built, unmodified compositions:
  * R5's ENTIRE recovery composition (`seeds/abusive_r5_recovery.json`,
    block 295000 -- itself R1-R4, all UNMODIFIED): the abuser/victim dyad,
    the bond channel (`tb_bond_accrue` + `r5_bond_extinguish`), the window/
    prior channel (`arousal_window_coreg` + `abusive_r3_coercive_control`),
    and the escape channel (`abusive_r4_learned_helplessness` +
    `r5_contingency_restore`).
  * N2's ENTIRE isolation composition (`seeds/abusive_n2_isolation.json`,
    block 301000 -- itself depending on N1's credibility-asymmetry loop,
    `abusive_n1_credibility_loop.json`, block 298000, both UNMODIFIED): an
    8-node support/network population that doubles as N1's credibility
    observers and N2's support-edge holders, severed by TWO independent
    drivers (`n2_abuser_active_sever`, `n2_network_drift_sever`).

N4 itself (`seeds/abusive_n4_believing_agent.json`) adds ZERO new rules --
see ABUSIVE_N4_BELIEVING_AGENT_PREREG.md Sec. 2.6 for the verified (not
assumed) trace of every headline number to an existing rule in
R1-R5/N1/N2. N4's entire novel content is ONE mechanical world event,
`introduce_believing_agent()`, fired once per trajectory in the
BELIEVING_AGENT arm only, at the induction/recovery phase boundary
(matching R5's own `introduce_support()` timing convention exactly): it
converts ONE already-severed support node (`BELIEVER_INDEX=7`, a disclosed,
mechanical, non-adaptive choice forced by N2's own reversed-index
drift/active-sever staggering -- PREREG Sec. 2.3) from an N1 "outsider"
into simultaneously (a) an N1 "insider" (`observes_held` +
`observes_private=1.0`, so `n1_network_credibility_private` -- the SAME
formula N3's own truth-anchor arm already validated -- computes its belief
from the abuser's TRUE state) and (b) R3's/R5's outside co-regulator (a
fresh `AffectiveState` pinned at `CALM_AROUSAL`, `regulated=1.0`, an
`also_attended_by` edge from the victim, `has_outside_regulator=1.0`),
while ALSO mechanically restoring its (already-severed) `support_edge` to
the victim. One node, believing and supporting at once, because in the
mechanism this line models those are the same act.

TWO ARMS (ABUSIVE_N4_BELIEVING_AGENT_PREREG.md):
  * NO_BELIEVING_AGENT (failable control) -- every channel continues
    exactly as in induction for the whole trajectory (same bond schedule,
    same non-contingent escape resolution, same fully-armed isolation
    tactic). Predicted: the trap persists on all four metrics.
  * BELIEVING_AGENT -- identical induction; `introduce_believing_agent()`
    fires once at tick T1. Predicted: bond weakens, window widens, the
    believer's own belief_gap arrests and reverses, and the total
    intact-support-edge count is higher than the control's.

A genuine engine-composition hazard was found and fixed at THIS layer
(PREREG Sec. 2.4): converting a node mid-trajectory inherits its
accumulated `seen_victim_unstable` discount from its time as an outsider,
while its new `cred_abuser` harm term starts at zero -- producing a
transient `belief_gap` high enough to trip `n2_network_drift_sever` and
immediately re-sever the just-restored edge. Fixed by resetting
`seen_victim_claim`/`seen_victim_unstable`/`seen_harm_direct` to `0.0` at
the moment of conversion (mechanical, not a new rule) -- verified clean
(zero re-severing events) across a 10-seed pilot sweep.

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER.
Every decision -- bond accrual/decay, entrainment, window narrowing/
widening, prior tracking, escape appraisal/choice/belief-revision, each
network node's credibility belief, and whether either severing driver
fires -- is the graph's decision, entirely inside the unmodified
`abusive_r5_recovery` and `abusive_n2_isolation` seeds (and, transitively,
everything they depend on). The adapter's only conditionals are (i) WHICH
ARM to build and WHEN to call `introduce_believing_agent()` (an
experimental-arm/timing selection made once per trajectory, exactly as
every prior rung in this line) and (ii) mechanically DELIVERING each
tick's observed graph facts onto observation-count attrs (reused verbatim
from N1's/N2's own `step()`) -- never a judgement about what a node should
believe or whether an edge should be severed; that is the reused rules'
job, entirely. NO reward/punishment anywhere.
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

# ---- FROZEN world constants (pre-registered, ABUSIVE_N4_BELIEVING_AGENT_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults) -- BYTE-IDENTICAL to
# R2/R3/R5/N1/N2/N3's own frozen constants.
ABUSER_HALF_WIDTH = 100.0
K_ACC = 1.0
LEAK = 0.02
DISCHARGE = 0.90
RECOVER_FLOOR = 25.0

# victim window/entrainment (arousal_window_coreg, block 239000 defaults)
VICTIM_HALF_WIDTH = 10.0
K_SELF = 0.15
K_CO = 0.35

# outside regulator (R3's/R5's own convention)
CALM_AROUSAL = 0.0

TRICKLE_MAG = 5.0
TRICKLE_JITTER_FRAC = 0.10

# bond channel (byte-identical to R5's own, including R5's own disclosed
# gain deviation from R1's -- see ABUSIVE_R5_RECOVERY_PREREG.md Sec. 3.1)
BOND_LR = 0.3
BOND_MOMENTUM_LR = 0.3
BOND_GAIN = 1.0
BOND_MAGNITUDE = 10.0
BOND_MAGNITUDE_JITTER = 0.5

# escape channel (byte-identical to R4/R5)
ESCAPE_VALUE = 10.0
ATTEMPT_COST = 3.0
ESCAPE_LR = 0.3
ESCAPE_P0 = 0.5

# R5's own recovery constants (byte-identical)
DECAY_RATE = 0.01
SUPPORT_LR = 0.3
SUPPORT_INTERVAL = 20
SUPPORT_OUTCOME = 1.0

# credibility loop (byte-identical to N1/N2/N3)
CHARM_WEIGHT = 1.0
CLAIM_WEIGHT = 1.0
INSTABILITY_DISCOUNT_WEIGHT = 3.0
HARM_DISCOUNT_WEIGHT = 3.0

# support network (byte-identical to N2)
N_SUPPORT_NODES = 8
EPISODE_TICKS = 210.0
DRIFT_STEP = 340.0

# N4's own new constant (PREREG Sec. 2.3)
BELIEVER_INDEX = 7

ARM_NAMES = ("believing_agent", "no_believing_agent")

BOND_BLOCK_H = 18   # R1's OWN frozen H=R=18 per block, reused unscaled (R5's
BOND_BLOCK_T = 36   # own precedent -- ABUSIVE_R5_RECOVERY_PREREG.md Sec. 3.1).


def make_bond_schedule(T, rng, *, n_blocks=1, magnitude=BOND_MAGNITUDE,
                        jitter=BOND_MAGNITUDE_JITTER, active=True):
    """MECHANICAL world-side event stream for the bond channel over T ticks
    -- byte-identical logic to R5's own `make_bond_schedule` (reused, not
    reimplemented, other than being restated in this file for the same
    self-contained-world-adapter convention every rung in this line uses)."""
    if not active:
        return [0.0] * T
    events = []
    for _ in range(n_blocks):
        events.extend(make_schedule("intermittent", rng, h=BOND_BLOCK_H, r=BOND_BLOCK_H,
                                     magnitude=magnitude, jitter=jitter))
    if len(events) > T:
        raise ValueError(f"n_blocks*{BOND_BLOCK_T} ({len(events)}) exceeds phase length T={T}")
    return events + [0.0] * (T - len(events))


class AbusiveN4BelievingAgentWorld:
    """One ABUSER Agent, one VICTIM Agent (R5's own dyad, unmodified
    contract), and a Network of N_SUPPORT_NODES NetworkNode agents (N2's
    own construction, unmodified contract). NO decision here -- only world
    delivery + mechanical per-tick bookkeeping + read-back."""

    def __init__(self, *, believer_index=BELIEVER_INDEX,
                 abuser_half_width=ABUSER_HALF_WIDTH,
                 victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE,
                 recover_floor=RECOVER_FLOOR, k_self=K_SELF, k_co=K_CO,
                 trickle_mag=TRICKLE_MAG, calm_arousal=CALM_AROUSAL,
                 bond_lr=BOND_LR, bond_momentum_lr=BOND_MOMENTUM_LR,
                 bond_gain=BOND_GAIN, bond_magnitude=BOND_MAGNITUDE,
                 escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST,
                 escape_lr=ESCAPE_LR, escape_p0=ESCAPE_P0,
                 decay_rate=DECAY_RATE, support_lr=SUPPORT_LR,
                 support_interval=SUPPORT_INTERVAL, support_outcome=SUPPORT_OUTCOME,
                 charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
                 instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
                 harm_discount_weight=HARM_DISCOUNT_WEIGHT,
                 n_support_nodes=N_SUPPORT_NODES,
                 episode_ticks=EPISODE_TICKS, drift_step=DRIFT_STEP):
        self.believer_index = int(believer_index)
        self.trickle_mag = float(trickle_mag)
        self.bond_magnitude = float(bond_magnitude)
        self.support_interval = int(support_interval)
        self.support_outcome = float(support_outcome)
        self.n_support_nodes = int(n_support_nodes)
        self.episode_ticks = float(episode_ticks)
        self.drift_step = float(drift_step)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "n4_root"})
        for seed in ("affective_state_core", "mood_r1_task", "mood_r1",
                     "core_emotions", "snap_frustration", "arousal_window_coreg",
                     "traumatic_bond_r1", "abusive_r2_cycle_limit",
                     "abusive_r3_coercive_control", "abusive_r4_learned_helplessness",
                     "abusive_r5_recovery", "abusive_n1_credibility_loop",
                     "abusive_n2_isolation", "abusive_n4_believing_agent"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract + is_abuser=1.0 + deception_on=1.0
        # (N1's second-audience atom, fixed ON in every arm) + R1's
        # Partner-role attrs directly on the SAME Agent node -- R5's own
        # disclosed composition choice (the bond IS to the abuser).
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

        self.s.set_attr(self.abuser, "value", 0.0)
        self.s.set_attr(self.abuser, "e_bond", -1.0)
        self.s.set_attr(self.abuser, "e_extinct", -1.0)
        self.s.set_attr(self.abuser, "decay_rate", float(decay_rate))

        # ---------------------------------------------------------- VICTIM
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

        # ---------------------------------------------------- SUPPORT NETWORK
        # N2's own construction: a Network hub carrying isolation_tactic_on
        # (armed in EVERY arm/phase of this rung -- N2's own `both_drivers`
        # arm, the fully-corrupted trap) + N_SUPPORT_NODES NetworkNode
        # members, each an N1-shape credibility observer AND an N2-shape
        # support-edge holder, with N2's own per-node sever_at_tick/
        # drift_threshold staggering.
        self.network = self.s.add_node("Network", dict(name="network", isolation_tactic_on=1.0))
        self.nodes = []
        for i in range(self.n_support_nodes):
            nn = self.s.add_node("NetworkNode", dict(
                name=f"support_{i}",
                observes_private=0.0,
                charm_weight=float(charm_weight), claim_weight=float(claim_weight),
                instability_discount_weight=float(instability_discount_weight),
                harm_discount_weight=float(harm_discount_weight),
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

        # ---------------------------------------------- BELIEVING AGENT state
        self.believer_active = False
        self._next_support_tick = None

        self.epoch = 0
        self.n_attempts_this_phase = 0
        self.pending_attempt = False
        self.escape_arm_current = "noncontingent"
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
        ab = self._attrs(self.abuser)
        va = self._attrs(self.vaff)
        vw = self._attrs(self.vwot)
        dec = self._attrs(self.dec)
        nn_rows = [self._attrs(nn) for nn in self.nodes]
        return dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"],
            bond_value=ab["value"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            half_width=vw["half_width"], others_trust=vw["others_trust"],
            self_worth=vw["self_worth"],
            contingency_prior=dec["contingency_prior"], chosen_action=dec["chosen_action"],
            n_intact_support_edges=self._n_intact_support_edges(),
            believer_belief_gap=nn_rows[self.believer_index]["belief_gap"],
            severed=[r["severed"] for r in nn_rows])

    # ----------------------------------------------- introduce_believing_agent
    def introduce_believing_agent(self):
        """ONE mechanical world event: convert the pre-designated support
        node (BELIEVER_INDEX) into an N1 insider AND R3's/R5's outside
        co-regulator simultaneously, mechanically restoring its support_edge
        if severed. Called ONCE, at the tick the runner/experimenter
        designates as the start of the recovery phase in the
        BELIEVING_AGENT arm -- an experimental-arm decision, never a
        graph-state-dependent branch. See PREREG Sec. 2.4 for why the
        observation-count reset below is necessary (a genuine engine-
        composition hazard, found and fixed here, at the world-adapter
        layer, without editing N1's or N2's seed)."""
        if self.believer_active:
            return
        nn = self.nodes[self.believer_index]

        # (1) mechanically restore the support edge if it is currently severed.
        blob = self.s.graph_to_dict()
        has_edge = any(e["type"] == "support_edge" and e["src"] == nn for e in blob["edges"])
        if not has_edge:
            self.inner.add_edge_unchecked(nn, "support_edge", self.victim)

        # (2) N1's insider conversion -- observes_held + observes_private=1.0
        # selects n1_network_credibility_private (unmodified) for this node
        # from the next run_rules() onward. The observation-count reset
        # (Sec. 2.4) is the fix for the re-sever hazard: without it, the
        # inherited seen_victim_unstable discount plus a fresh-zero
        # cred_abuser term produces a transient belief_gap still above
        # drift_threshold, tripping n2_network_drift_sever on the very
        # first recovery tick.
        self.inner.add_edge_unchecked(nn, "observes_held", self.abuser)
        self.s.set_attr(nn, "observes_private", 1.0)
        self.s.set_attr(nn, "seen_victim_claim", 0.0)
        self.s.set_attr(nn, "seen_victim_unstable", 0.0)
        self.s.set_attr(nn, "seen_harm_direct", 0.0)
        self.s.set_attr(nn, "severed", 0.0)
        self.s.set_attr(nn, "severed_reason", 0.0)

        # (3) R3's/R5's outside co-regulator role, on the SAME node id.
        self.s.set_attr(nn, "regulated", 1.0)
        oaff = self.s.add_node("AffectiveState", dict(
            name="believer_affect", baseline=1.0, valence=0.0,
            arousal=float(CALM_AROUSAL), setpoint=float(CALM_AROUSAL),
            resolution=0.0, selection_threshold=0.0, securing=0.0,
            competence=0.0, epoch=-1.0, is_abuser=0.0, tick_epoch=float(self.epoch)))
        self.inner.add_edge_unchecked(nn, "has_affective_state", oaff)
        self.inner.add_edge_unchecked(self.victim, "also_attended_by", nn)
        self.s.set_attr(self.vaff, "has_outside_regulator", 1.0)

        # (4)/(5) R5's own phase-boundary events, reused verbatim: reduced
        # abuser access (bond events stop) and contingent escape resolution.
        self.believer_nn = nn
        self.believer_oaff = oaff
        self.believer_active = True
        self._next_support_tick = self.epoch + self.support_interval
        self.escape_arm_current = "contingent"

    # ------------------------------------------------------------------- step
    def step(self, *, deliver_bond_event=0.0, tension_jitter=0.0):
        """Advance one tick: deliver the tension trickle (always), the bond
        event (mechanical, world-scheduled), resolve any pending escape
        attempt, mechanically deliver each network node's per-tick
        observation counts + tick counter (a world fact, never a
        judgement), let the GRAPH decide everything else (run_rules), read
        back. NO decision here."""
        self.epoch += 1
        e = float(self.epoch)

        self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + tension_jitter))
        self.s.set_attr(self.gb, "armed", 1.0)

        self.s.set_attr(self.mt, "r", float(deliver_bond_event))
        self.s.set_attr(self.mt, "input_epoch", e)

        if self.pending_attempt:
            outcome = resolve_outcome(
                "contingent" if self.escape_arm_current == "contingent" else "noncontingent")
            self.s.set_attr(self.dec, "outcome", float(outcome))
            self.s.set_attr(self.dec, "outcome_epoch", e)
            self.pending_attempt = False
        self.s.set_attr(self.dec, "tick_epoch", e)

        if self.believer_active and self.epoch >= self._next_support_tick:
            self.s.set_attr(self.dec, "support_outcome", float(self.support_outcome))
            self.s.set_attr(self.dec, "support_epoch", e)
            self._next_support_tick = self.epoch + self.support_interval

        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        if self.believer_active:
            self.s.set_attr(self.believer_oaff, "tick_epoch", e)

        self.inner.run_rules()

        # ---- mechanical per-tick observation bookkeeping (world fact -> attr,
        # reused verbatim from N1's/N2's own step()).
        stated_charm = self._attrs(self.aaff)["stated_charm"]
        held_harm = 1.0 if self._attrs(self.aaff)["frustration"] > self._attrs(self.aaff)["recover_floor"] else 0.0
        victim_unstable = self._attrs(self.vaff)["dysregulated"]
        for nn in self.nodes:
            a = self._attrs(nn)
            if a["observes_private"] == 1.0:
                self.s.set_attr(nn, "seen_harm_direct", a["seen_harm_direct"] + held_harm)
            else:
                self.s.set_attr(nn, "seen_charm", a["seen_charm"] + stated_charm)
            self.s.set_attr(nn, "seen_victim_claim", a["seen_victim_claim"] + 1.0)
            self.s.set_attr(nn, "seen_victim_unstable", a["seen_victim_unstable"] + victim_unstable)
            self.s.set_attr(nn, "tick_epoch", e)
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
        each tick, matching R2/R3/R5/N1-N3's own convention. Returns the
        phase's escape-attempt rate alongside the final readout; resets the
        attempt counter for the NEXT phase."""
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
