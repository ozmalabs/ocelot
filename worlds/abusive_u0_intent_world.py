"""AbusiveU0IntentWorld -- a MECHANICAL abuser/victim/network world for the
ABUSIVE-DYNAMICS U0 rung (block 307000, "genuine intent: an Argmax-selected
concealment, scored against a declared goal" --
ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md Part E, U0; the positive
control of the unintentional/no-deliberate-deception companion dimension).

Composes N1's own dyad + network-credibility machinery (self-contained
restatement -- see seeds/abusive_u0_intent.json's own provenance for why N1's
seed file is NOT depended on directly) with ONE new mechanism replacing N1's
`n1_abuser_stated_charm`: a genuine `Argmax`-over-two-candidate-`Appraisal`s
choice (`present_charm` vs `present_true_state`), scored via the ALREADY-
BUILT, UNMODIFIED `core_emotions` value economy -- the SAME template
`abusive_r4_learned_helplessness.json` / `marshmallow_delay.json` already use.

TWO ARMS (ABUSIVE_U0_INTENT_PREREG.md):
  * SCORED     -- concealment_benefit/honesty_benefit/suspicion_cost_scale at
                  their pilot-chosen, frozen, NONZERO operating point. THE
                  POSITIVE CLAIM: stated_charm selection correlates with the
                  abuser's true frustration (concealment gets chosen more
                  often exactly when there is more to conceal).
  * GOAL_BLIND -- concealment_benefit = honesty_benefit = suspicion_cost_scale
                  = 0.0 (an EXACT tie every tick -- individual_cost for BOTH
                  candidates is identically 0 regardless of frustration, by
                  construction, not merely by chance). FAILABLE: stated_charm
                  selection must NOT correlate with frustration -- at most it
                  tracks the Argmax's own deterministic tie-break (first
                  candidate encountered), never the abuser's true state.

The abuser/victim dyad (snap_frustration + arousal_window_coreg, both
UNMODIFIED) and the five-node network (all `observes_stated`, matching N1's
own BASELINE topology) are IDENTICAL across both arms -- the ONLY
manipulated variable is the three Argmax constants on the `PresentationDecision`
node, a world-adapter constant selection made ONCE per arm, exactly as every
prior rung in this line selects its experimental arm.

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. Every
decision -- frustration accumulation, the snap threshold, discharge, recovery,
the victim's entrainment, BOTH candidate presentations' valuation, the Argmax
choice itself, and the network's credibility belief-update -- is the graph's
decision, entirely inside `seeds/snap_frustration.json` /
`seeds/arousal_window_coreg.json` / `seeds/core_emotions.json` (all
UNMODIFIED) and this rung's seven rules in `seeds/abusive_u0_intent.json`.
The adapter's only "conditionals" are (i) WHICH ARM to build (an
experimental-arm constant selection made ONCE per trajectory, exactly as
every prior rung) and (ii) mechanically DELIVERING each tick's observed
graph facts (the abuser's stated_charm, the victim's dysregulated flag) onto
each network node's observation-COUNT attrs -- a per-tick tally, never a
judgement. NO reward/punishment anywhere: the Argmax computes a VALUE
COMPARISON between two candidate presentations (the SAME mechanism R4's
r4_choose / marshmallow's mm_choose already use), never a score applied to
the agent for its choice -- see Part D.2 of
ABUSIVE_U0_INTENT_PREREG.md.
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
from domains.core_emotions_weight import quantize_weight     # noqa: E402

# ---- FROZEN world constants (pre-registered, ABUSIVE_U0_INTENT_PREREG.md)
SETPOINT = 0.0

# abuser (snap_frustration, block 242000 defaults -- BYTE-IDENTICAL to N1's
# own frozen constants, since U0 reuses the exact same abuser mechanism).
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
# not re-swept -- U0's own scientific claim is about the Argmax, not the
# network's credibility formula).
N_NETWORK_NODES = 5
CHARM_WEIGHT = 1.0
CLAIM_WEIGHT = 1.0
INSTABILITY_DISCOUNT_WEIGHT = 3.0
HARM_DISCOUNT_WEIGHT = 3.0

# U0-specific: the Argmax's three declared constants (pilot-informed, see
# PREREG Sec. 3). SCORED arm uses these; GOAL_BLIND zeroes all three (see
# ARM_KWARGS below). honesty_benefit > concealment_benefit is REQUIRED for a
# genuine crossover to exist: at frustration=0, present_true_state's value
# (honesty_benefit - 0) must exceed present_charm's (concealment_benefit - 0)
# so honesty wins when there is nothing to conceal; as frustration rises,
# suspicion_cost_scale*frustration erodes present_true_state's value until
# present_charm overtakes it at frustration* = (honesty_benefit -
# concealment_benefit) / suspicion_cost_scale (pilot-chosen so this crossover
# falls inside the abuser's observed frustration range, see PREREG Sec. 3).
CONCEALMENT_BENEFIT = 2.0
HONESTY_BENEFIT = 5.0
SUSPICION_COST_SCALE = 0.10

ARM_NAMES = ("scored", "goal_blind")

EP_DEFAULTS = dict(enabled=1.0, w_supergraph=0.0, mood_bias=0.0, residual_thresh=100.0,
                    high_arousal=800.0, mid_arousal=400.0, low_arousal=50.0, comms_on=0.0)
#   ^ matches domains/marshmallow_world.py's / abusive_r4_learned_helplessness_world.py's
#     own EP_DEFAULTS verbatim -- every core_emotions channel besides
#     happiness/fulfilment_value/total_value held neutral.

APPR_DEFAULTS = dict(
    appraised=1.0, individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
    collective_success=0.0, collective_success_prev=0.0, contribution_by_self=0.0,
    observed_by_other=0.0, valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
    attachment=0.0, regroundable=0.0, contamination=0.0, was_engaged=0.0,
    residual=0.0, residual_prev=0.0, threat=0.0, threat_c0=0.0, threat_half_life=1.0,
    threat_last_refresh=0.0, threat_now_epoch=0.0, t_present=100.0, v_max=0.0,
    step=0.0, step_prev=0.0, attach_v0=0.0, attach_k_now=0.0, attach_k_prev=0.0)
#   ^ mirrors abusive_r4_learned_helplessness_world.py's own APPR_DEFAULTS
#     verbatim -- the exact defaults the ALREADY-BUILT, UNMODIFIED
#     core_emotions rules (em_happiness/em_fulfilment_value/em_total_value)
#     need present so no other core_emotions rule reads a missing attr.

DEC_DEFAULTS = dict(
    concealment_benefit=CONCEALMENT_BENEFIT, honesty_benefit=HONESTY_BENEFIT,
    suspicion_cost_scale=SUSPICION_COST_SCALE, chosen_action=-1.0)


def _arm_kwargs(arm):
    if arm == "scored":
        return dict(concealment_benefit=CONCEALMENT_BENEFIT, honesty_benefit=HONESTY_BENEFIT,
                     suspicion_cost_scale=SUSPICION_COST_SCALE)
    if arm == "goal_blind":
        # GOAL-BLIND CONTROL: all three constants zeroed -- present_charm's
        # value (benefit 0, cost 0) is EXACTLY tied with present_true_state's
        # value (benefit 0, cost 0*frustration=0 for any finite frustration)
        # on EVERY tick, by construction, not by chance. The Argmax's own
        # deterministic tie-break (first candidate encountered in
        # Neighbours(has_candidate) iteration order -- see PREREG Sec. 2's
        # engine note) then decides stated_charm the SAME way every tick,
        # regardless of the abuser's true frustration trajectory.
        return dict(concealment_benefit=0.0, honesty_benefit=0.0, suspicion_cost_scale=0.0)
    raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")


class AbusiveU0IntentWorld:
    """One ABUSER Agent (snap_frustration, unmodified, byte-identical to
    N1's own) + its EmotionHub/PresentationDecision/two candidate Appraisals
    (the genuine-intent Argmax), one VICTIM Agent (arousal_window_coreg,
    unmodified, plus U0's own frustration-routed entrainment, byte-identical
    to N1's), and a Network of five NetworkNode agents (all observes_stated,
    matching N1's BASELINE topology) whose reputation belief is entirely
    graph-rule-computed. NO decision here -- only world delivery + mechanical
    per-tick observation-count bookkeeping + read-back."""

    def __init__(self, arm="scored", *,
                 abuser_half_width=ABUSER_HALF_WIDTH, victim_half_width=VICTIM_HALF_WIDTH,
                 leak=LEAK, k_acc=K_ACC, discharge=DISCHARGE, recover_floor=RECOVER_FLOOR,
                 k_self=K_SELF, k_co=K_CO, trickle_mag=TRICKLE_MAG,
                 n_network_nodes=N_NETWORK_NODES,
                 charm_weight=CHARM_WEIGHT, claim_weight=CLAIM_WEIGHT,
                 instability_discount_weight=INSTABILITY_DISCOUNT_WEIGHT,
                 harm_discount_weight=HARM_DISCOUNT_WEIGHT,
                 concealment_benefit=None, honesty_benefit=None, suspicion_cost_scale=None):
        if arm not in ARM_NAMES:
            raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")
        self.arm = arm
        arm_kw = _arm_kwargs(arm)
        if concealment_benefit is None:
            concealment_benefit = arm_kw["concealment_benefit"]
        if honesty_benefit is None:
            honesty_benefit = arm_kw["honesty_benefit"]
        if suspicion_cost_scale is None:
            suspicion_cost_scale = arm_kw["suspicion_cost_scale"]

        self.trickle_mag = float(trickle_mag)
        self.n_network_nodes = int(n_network_nodes)

        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "u0_root"})
        for seed in ("affective_state_core", "snap_frustration", "arousal_window_coreg",
                     "core_emotions", "abusive_u0_intent"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        # ---------------------------------------------------------- ABUSER
        # snap_frustration's full contract, plus is_abuser=1.0 (read by
        # u0_victim_entrainment). NO deception_on/stated_charm-as-input --
        # stated_charm is now an OUTPUT the Argmax chain computes and writes
        # (u0_apply_presentation_choice), never a Python-set input.
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
            stated_charm=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_affective_state", self.aaff)

        hw_a = float(abuser_half_width)
        self.awot = self.s.add_node("WindowOfTolerance", dict(
            name="abuser_window", lo=-hw_a, hi=hw_a, half_width=hw_a))
        self.inner.add_edge_unchecked(self.abuser, "has_window", self.awot)

        self.gb = self.s.add_node("GoalBlock", dict(
            name="tension_trigger", magnitude=0.0, armed=0.0))
        self.inner.add_edge_unchecked(self.abuser, "has_goal_block", self.gb)

        # ---------------------------------------- THE GENUINE-INTENT ARGMAX
        # EmotionHub + HeldEmotionParams + PresentationDecision + TWO
        # candidate Appraisals (present_charm action=1, present_true_state
        # action=0), all wired per the marshmallow/R4 template. `hub` reads
        # the abuser's OWN aaff (the SAME node, via a second
        # has_affective_state edge) so u0_appraise_true_state can read its
        # TRUE frustration.
        self.hub = self.s.add_node("EmotionHub", {"name": "abuser_presentation"})
        ep = dict(EP_DEFAULTS)
        ep["w_supergraph_q"], ep["w_scale_bits"] = quantize_weight(ep["w_supergraph"])
        self.ep = self.s.add_node("HeldEmotionParams", ep)
        self.inner.add_edge_unchecked(self.hub, "has_emotion_params", self.ep)
        self.inner.add_edge_unchecked(self.hub, "has_affective_state", self.aaff)

        dec = dict(DEC_DEFAULTS)
        dec.update(concealment_benefit=float(concealment_benefit),
                    honesty_benefit=float(honesty_benefit),
                    suspicion_cost_scale=float(suspicion_cost_scale))
        self.dec = self.s.add_node("PresentationDecision", dec)
        self.inner.add_edge_unchecked(self.hub, "has_presentation_decision", self.dec)

        # Insertion order matters for the GOAL_BLIND arm's deterministic tie
        # -break (Argmax keeps the FIRST candidate encountered on an exact
        # value tie) -- present_charm is added first, so a tie resolves to
        # stated_charm=1.0 (charm) constantly under goal-blindness, disclosed
        # in the results, not hidden.
        pc = dict(APPR_DEFAULTS)
        pc.update(action=1.0)
        self.present_charm = self.s.add_node("Appraisal", pc)
        self.inner.add_edge_unchecked(self.hub, "has_appraisal", self.present_charm)
        self.inner.add_edge_unchecked(self.hub, "has_candidate", self.present_charm)

        pt = dict(APPR_DEFAULTS)
        pt.update(action=0.0)
        self.present_true = self.s.add_node("Appraisal", pt)
        self.inner.add_edge_unchecked(self.hub, "has_appraisal", self.present_true)
        self.inner.add_edge_unchecked(self.hub, "has_candidate", self.present_true)

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

        # U0's own network belief-gap read-off is an apples-to-apples
        # comparison to N1's own BASELINE headline number (informational,
        # non-gating, PREREG Sec. 5) -- so the victim dyad is coupled exactly
        # as N1's BASELINE arm couples it, in EVERY U0 arm.
        self.inner.add_edge_unchecked(self.victim, "attended_by", self.abuser)

        # --------------------------------------------------------- NETWORK
        # A Network hub + N NetworkNode members, all observes_stated
        # (matching N1's BASELINE topology -- U0 does not exercise N1's own
        # private-face/non-dysregulated controls; those are N1's, not U0's,
        # to re-litigate). u0_network_credibility_private is present in the
        # seed (byte-identical restatement, per the task's "everything else
        # ... stays as N1 built it") but never fires here, since no node
        # ever carries observes_private=1.
        self.network = self.s.add_node("Network", {"name": "network"})
        self.nodes = []
        for i in range(self.n_network_nodes):
            nn = self.s.add_node("NetworkNode", dict(
                name=f"node_{i}",
                observes_private=0.0,
                charm_weight=float(charm_weight), claim_weight=float(claim_weight),
                instability_discount_weight=float(instability_discount_weight),
                harm_discount_weight=float(harm_discount_weight),
                seen_charm=0.0, seen_harm_direct=0.0,
                seen_victim_claim=0.0, seen_victim_unstable=0.0,
                cred_abuser=0.0, cred_victim=0.0, belief_gap=0.0))
            self.inner.add_edge_unchecked(self.network, "has_member", nn)
            self.inner.add_edge_unchecked(nn, "observes_stated", self.abuser)
            self.inner.add_edge_unchecked(nn, "observes_victim", self.victim)
            self.nodes.append(nn)

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
        dec = self._attrs(self.dec)
        nn_rows = [self._attrs(nn) for nn in self.nodes]
        return dict(
            epoch=self.epoch,
            abuser_arousal=aa["arousal"], abuser_frustration=aa["frustration"],
            abuser_snap_count=aa["snap_count"], abuser_stated_charm=aa["stated_charm"],
            chosen_action=dec["chosen_action"],
            victim_arousal=va["arousal"], victim_dysregulated=va["dysregulated"],
            victim_half_width=vw["half_width"],
            belief_gap_mean=(sum(r["belief_gap"] for r in nn_rows) / len(nn_rows)),
            cred_abuser_mean=(sum(r["cred_abuser"] for r in nn_rows) / len(nn_rows)),
            cred_victim_mean=(sum(r["cred_victim"] for r in nn_rows) / len(nn_rows)))

    # ------------------------------------------------------------------- step
    def step(self, *, tension=False, jitter=0.0):
        """Advance one tick: (optionally) arm the abuser's tension trickle,
        let the GRAPH decide the dyad + BOTH candidate presentations' value +
        the Argmax choice + the resulting stated_charm (run_rules),
        MECHANICALLY deliver each node's per-tick observation counts (a world
        fact, never a judgement), let the GRAPH decide each node's
        credibility belief (run_rules again), read off."""
        self.epoch += 1
        e = float(self.epoch)
        if tension:
            self.s.set_attr(self.gb, "magnitude", float(self.trickle_mag + jitter))
            self.s.set_attr(self.gb, "armed", 1.0)
        self.s.set_attr(self.aaff, "tick_epoch", e)
        self.s.set_attr(self.vaff, "tick_epoch", e)
        self.inner.run_rules()

        # ---- mechanical per-tick observation bookkeeping (world fact -> attr)
        stated_charm = self._attrs(self.aaff)["stated_charm"]
        victim_unstable = self._attrs(self.vaff)["dysregulated"]
        for nn in self.nodes:
            a = self._attrs(nn)
            self.s.set_attr(nn, "seen_charm", a["seen_charm"] + stated_charm)
            self.s.set_attr(nn, "seen_victim_claim", a["seen_victim_claim"] + 1.0)
            self.s.set_attr(nn, "seen_victim_unstable", a["seen_victim_unstable"] + victim_unstable)
        self.inner.run_rules()

        r = self.readout()
        self.log.append(r)
        return r

    def run_trajectory(self, T, *, rng=None):
        """Deliver T ticks of the constant, jittered tension trickle -- the
        SAME abuser-side driver in EVERY arm (only the three Argmax
        constants differ)."""
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
