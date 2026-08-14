"""AbusiveR4LearnedHelplessnessWorld -- a MECHANICAL escape-opportunity/outcome
adapter for the ABUSIVE-DYNAMICS R4 rung (block 292000, "learned helplessness").

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. It
INGESTS a per-arm outcome-resolution function (a mechanical, world-side rule
for what happens IF the graph decides to attempt escape -- see
``resolve_outcome`` below) tick by tick and EMITS graph state around
``run_rules()``. It contains NO agent decision:

  * WHETHER to attempt escape this tick (``EscapeDecision.chosen_action``) is
    the graph's decision -- ``r4_choose`` in
    seeds/abusive_r4_learned_helplessness.json, an Argmax over two candidate
    Appraisals (attempt, stay) by total_value, decided entirely over the
    ALREADY-BUILT, UNMODIFIED core_emotions (block 204000) value economy. The
    adapter only READS ``chosen_action`` back.
  * The CONTINGENCY-BELIEF UPDATE (``EscapeDecision.contingency_prior``) is
    the graph's decision -- ``r4_belief_update``, same seed, a leaky EMA over
    the outcome MAGNITUDE the world delivers (never a scored choice).
  * The adapter's only conditional is over WORLD/ARM state -- which
    outcome-resolution function to apply (contingent vs non-contingent),
    decided ONCE per experiment arm by the runner/experimenter, exactly as
    TraumaticBondR1World's ``make_schedule`` arm switch or
    WindowKnobDyadWorld's ``caregiver_half_width`` select an EXPERIMENTAL ARM,
    never an agent decision.

No graph_rewrite.run / _match / _apply / add_rule; no if/else over the
victim's graph state that decides whether to attempt escape or how the
contingency belief moves. NO reward / punishment signal anywhere: the outcome
delivered is a STATE FACT (escape worked / escape was blocked), like a
harm/relief magnitude (block 283000) or a stressor magnitude (block 239000),
never a scored choice -- see Part C.2 of
ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md. The source audit in
scripts/abusive_r4_learned_helplessness_run.py checks for the literal banned
tokens (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`).
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

# ---- FIXED world constants (pre-registered, ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md)
LR = 0.3                # contingency-belief EMA rate
ESCAPE_VALUE = 10.0      # V: the payoff an attempt is worth IF escape works
ATTEMPT_COST = 3.0       # C: the fixed structural cost of attempting
#                           (breakeven prior = C/V = 0.30)
K_SELF = 0.15            # harm-analog arousal self-regulation leak
SETPOINT = 0.0
RELIEF_MAG = 3.0         # harm-analog arousal push on a "worked" outcome
BLOCK_MAG = 5.0          # harm-analog arousal push on a "blocked" outcome

P0_MEAN = 0.5            # initial contingency-prior mean (genuinely
#                           uninformative -- the victim has not yet observed
#                           whether escape is controllable)
P0_JITTER = 0.05         # per-episode jitter sd, clipped to [0.05, 0.95]

ARM_NAMES = ("contingent", "noncontingent")

EP_DEFAULTS = dict(enabled=1.0, w_supergraph=0.0, mood_bias=0.0, residual_thresh=100.0,
                    high_arousal=800.0, mid_arousal=400.0, low_arousal=50.0, comms_on=0.0)

APPR_DEFAULTS = dict(
    appraised=1.0, individual_benefit=0.0, individual_cost=0.0, supergraph_contribution=0.0,
    collective_success=0.0, collective_success_prev=0.0, contribution_by_self=0.0,
    observed_by_other=0.0, valued_goal=0.0, goal_blocked=0.0, blocker_present=0.0,
    attachment=0.0, regroundable=0.0, contamination=0.0, was_engaged=0.0,
    residual=0.0, residual_prev=0.0, threat=0.0, threat_c0=0.0, threat_half_life=1.0,
    threat_last_refresh=0.0, threat_now_epoch=0.0, t_present=100.0, v_max=0.0,
    step=0.0, step_prev=0.0, attach_v0=0.0, attach_k_now=0.0, attach_k_prev=0.0)
#   ^ mirrors domains/marshmallow_world.py's own EP_DEFAULTS/APPR_DEFAULTS
#     verbatim -- the exact defaults the ALREADY-BUILT, UNMODIFIED
#     core_emotions rules (em_happiness/em_fulfilment_value/em_total_value)
#     need present so no other core_emotions rule (w_supergraph-gated
#     fulfilment, threat channels, etc.) reads a missing attr; every one of
#     those channels is held neutral (0 / w_supergraph=0) so it contributes
#     nothing to total_value here, matching marshmallow's own usage exactly.

DEC_DEFAULTS = dict(
    contingency_prior=P0_MEAN, lr=LR, escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST,
    chosen_action=-1.0, outcome=-1.0, outcome_epoch=-1.0, processed_epoch=-1.0, tick_epoch=0.0)

AFFECT_DEFAULTS = dict(
    name="victim_affect", arousal=0.0, k_self=K_SELF, setpoint=SETPOINT,
    relief_mag=RELIEF_MAG, block_mag=BLOCK_MAG, arousal_epoch=-1.0)


def resolve_outcome(arm: str) -> float:
    """MECHANICAL, per-ARM outcome resolution -- decided ONCE per experiment
    arm (world setup), never a per-tick agent decision. Returns the outcome
    magnitude the graph's r4_belief_update rule will read (1.0 = escape
    worked, 0.0 = escape was blocked). This is the ONLY thing that differs
    between arms: whether an attempt's outcome is CONTINGENT on the attempt
    (deterministically works) or INDEPENDENT of it (deterministically
    blocked, the strongest/cleanest form of "outcomes independent of the
    action" -- the classic escapable/inescapable-shock yoked-pair
    operationalisation, ABUSIVE_R4_LEARNED_HELPLESSNESS_PREREG.md Sec. 2)."""
    if arm == "contingent":
        return 1.0
    if arm == "noncontingent":
        return 0.0
    raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")


class AbusiveR4LearnedHelplessnessWorld:
    """One victim EmotionHub (HeldEmotionParams + EscapeDecision + two
    candidate Appraisals + a harm-analog AffectiveState). ``step()`` advances
    one tick: if the PREVIOUS tick's decision was to attempt, resolve and
    deliver that attempt's outcome (mechanical, per-arm); run_rules(); read
    back. NO decision here -- only world delivery + read-back."""

    def __init__(self, arm: str, *, p0=P0_MEAN, lr=LR, escape_value=ESCAPE_VALUE,
                 attempt_cost=ATTEMPT_COST, k_self=K_SELF, setpoint=SETPOINT):
        if arm not in ARM_NAMES:
            raise ValueError(f"unknown arm {arm!r}; expected one of {ARM_NAMES}")
        self.arm = arm
        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "victim_root"})
        # load_seed_manifest loads exactly the named seed's rules -- it does
        # NOT walk depends_on -- so every seed whose RULES this world needs
        # is loaded explicitly, matching domains/marshmallow_world.py's and
        # worlds/traumatic_bond_r1_world.py's own convention. (The
        # "AffectiveState"/"has_affective_state" node/edge naming below
        # borrows affective_state_core's contract as a naming convention
        # ONLY -- that seed's own rules are never loaded into this
        # substrate, so they cannot fire on this node, exactly as R1's own
        # world already does.)
        for seed in ("core_emotions", "abusive_r4_learned_helplessness"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        self.hub = self.s.add_node("EmotionHub", {"name": "victim"})

        ep = dict(EP_DEFAULTS)
        self.ep = self.s.add_node("HeldEmotionParams", ep)
        self.inner.add_edge_unchecked(self.hub, "has_emotion_params", self.ep)

        dec = dict(DEC_DEFAULTS)
        dec.update(contingency_prior=float(p0), lr=float(lr), escape_value=float(escape_value),
                   attempt_cost=float(attempt_cost))
        self.dec = self.s.add_node("EscapeDecision", dec)
        self.inner.add_edge_unchecked(self.hub, "has_escape_decision", self.dec)

        at = dict(APPR_DEFAULTS); at.update(action=1.0)
        self.attempt = self.s.add_node("Appraisal", at)
        self.inner.add_edge_unchecked(self.hub, "has_appraisal", self.attempt)
        self.inner.add_edge_unchecked(self.hub, "has_candidate", self.attempt)

        st = dict(APPR_DEFAULTS); st.update(action=0.0)
        self.stay = self.s.add_node("Appraisal", st)
        self.inner.add_edge_unchecked(self.hub, "has_appraisal", self.stay)
        self.inner.add_edge_unchecked(self.hub, "has_candidate", self.stay)

        af = dict(AFFECT_DEFAULTS)
        af.update(k_self=float(k_self), setpoint=float(setpoint))
        self.affect = self.s.add_node("AffectiveState", af)
        self.inner.add_edge_unchecked(self.hub, "has_affective_state", self.affect)

        self.epoch = 0
        self.n_attempts = 0
        self.pending_attempt = False
        self.log = []
        self.inner.run_rules()

    # ---------------------------------------------------------------- helpers
    def _attrs(self, nid):
        return self.s.node(nid)["attrs"]

    def readout(self):
        dec = self._attrs(self.dec)
        aff = self._attrs(self.affect)
        return dict(epoch=self.epoch, chosen_action=dec["chosen_action"],
                    contingency_prior=dec["contingency_prior"],
                    outcome=dec["outcome"], arousal=aff["arousal"])

    # ------------------------------------------------------------------- step
    def step(self):
        """Advance one tick: (1) if the PREVIOUS tick's decision was to
        attempt, mechanically resolve and deliver that attempt's outcome
        (INGEST -- a world fact, never a decision); (2) run_rules() (the
        graph updates the belief from that outcome, THEN decides this tick's
        attempt/stay); (3) read back (EMIT). NO decision here."""
        self.epoch += 1
        if self.pending_attempt:
            outcome = resolve_outcome(self.arm)
            self.s.set_attr(self.dec, "outcome", float(outcome))
            self.s.set_attr(self.dec, "outcome_epoch", float(self.epoch))
            self.pending_attempt = False
        self.s.set_attr(self.dec, "tick_epoch", float(self.epoch))
        self.inner.run_rules()
        row = self.readout()
        self.log.append(row)
        if row["chosen_action"] == 1.0:
            self.pending_attempt = True
            self.n_attempts += 1
        return row

    def run_episode(self, ticks: int):
        """Advance ``ticks`` ticks. Returns the final graph readout plus the
        episode-level escape-ATTEMPT RATE (n_attempts / ticks)."""
        row = None
        for _ in range(ticks):
            row = self.step()
        row = dict(row)
        row["attempt_rate"] = self.n_attempts / ticks
        row["n_attempts"] = self.n_attempts
        return row

    # -------------------------------------------------- glass-box / ethics I/O
    def checkpoint(self):
        """Byte-identical serialisation of the WHOLE mind (graph_to_dict)."""
        return self.s.graph_to_dict()
