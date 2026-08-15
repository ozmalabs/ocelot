"""AbusiveR6DependentCostWorld -- a MECHANICAL escape-opportunity/outcome
adapter for the ABUSIVE-DYNAMICS R6 rung (block 361000, "dependent/
resource-cost devaluation of escape's value").

ARCHITECTURE RULE COMPLIANCE (CLAUDE.md): this file is a WORLD ADAPTER. It
EMITS graph state around ``run_rules()`` and contains NO agent decision:

  * WHETHER to attempt escape this tick (``EscapeDecision.chosen_action``) is
    the graph's decision -- ``r4_choose`` in
    seeds/abusive_r4_learned_helplessness.json (UNMODIFIED, depended on
    directly), an Argmax over two candidate Appraisals (attempt, stay) by
    total_value, decided entirely over the ALREADY-BUILT, UNMODIFIED
    core_emotions (block 204000) value economy. The adapter only READS
    ``chosen_action`` back.
  * The CONTINGENCY-BELIEF UPDATE (``EscapeDecision.contingency_prior``) is
    the graph's decision -- ``r4_belief_update``, R4's own rule, UNMODIFIED.
  * The DEPENDENT-COST TERM (``Appraisal.individual_cost`` for the attempt
    candidate) is the graph's decision -- ``r6_appraise_attempt_dependent``,
    seeds/abusive_r6_dependent_cost.json, a pure re-derivation from
    ``EscapeDecision``'s own fixed declared attrs.
  * The adapter's only "conditional" is which FIXED ``dependent_cost`` value
    to set on the ``EscapeDecision`` node at CONSTRUCTION time -- decided
    ONCE per experiment arm by the runner/experimenter, exactly as
    AbusiveR4LearnedHelplessnessWorld's own ``arm`` selects
    ``resolve_outcome``, never a per-tick agent decision. Unlike R4's own
    world, R6's world carries NO arm-selecting outcome-resolution function
    at all: BOTH R6 arms use the SAME, deterministic, always-succeeds
    outcome resolution (R4's own CONTINGENT arm, unchanged) -- isolating the
    material-cost axis from R4's already-tested controllability axis, per
    ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md Part B1.

No graph_rewrite.run / _match / _apply / add_rule; no if/else over the
victim's graph state that decides whether to attempt escape, how the
contingency belief moves, or how much the attempt candidate costs. NO
reward / punishment signal anywhere: ``dependent_cost`` is a structural FACT
about material circumstances, exactly like ``attempt_cost``, never a scored
choice -- see Part D.2 of ABUSIVE_R6_DEPENDENT_COST_PREREG.md. The source
audit in scripts/abusive_r6_dependent_cost_run.py checks for the literal
banned tokens (`reward_signal` / `punish` / `reinforce` / `backprop` /
`gradient`).
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
from worlds.abusive_r4_learned_helplessness_world import (   # noqa: E402
    EP_DEFAULTS, APPR_DEFAULTS, AFFECT_DEFAULTS,
    LR, ESCAPE_VALUE, ATTEMPT_COST, K_SELF, SETPOINT,
    RELIEF_MAG, BLOCK_MAG, P0_MEAN, P0_JITTER,
)
#   ^ Imported directly, never re-declared -- this is what makes the
#     ZERO-DEPENDENTS/R4-contingent-arm harness-neutrality check a property
#     of the CODE (the same numeric constants, the same defaults dict), not
#     merely of stated intent.

# ---- FIXED, R6-own world constants (pre-registered, ABUSIVE_R6_DEPENDENT_COST_PREREG.md Sec. 5)
ZERO_DEPENDENT_COST = 0.0     # the harness-neutrality-check arm
HIGH_DEPENDENT_COST = 10.0    # escape_value(10.0) - attempt_cost(3.0) - 10.0 = -3.0 < 0
#                                even at contingency_prior=1.0 (the ceiling) -- Sec. 3's
#                                derivation: dependent_cost > 7.0 is required; 10.0 is a
#                                disclosed, comfortable, round-number margin above that.

ARM_NAMES = ("zero_dependents", "high_dependents")
ARM_DEPENDENT_COST = {"zero_dependents": ZERO_DEPENDENT_COST,
                       "high_dependents": HIGH_DEPENDENT_COST}

DEC_DEFAULTS = dict(
    contingency_prior=P0_MEAN, lr=LR, escape_value=ESCAPE_VALUE, attempt_cost=ATTEMPT_COST,
    dependent_cost=0.0,
    chosen_action=-1.0, outcome=-1.0, outcome_epoch=-1.0, processed_epoch=-1.0, tick_epoch=0.0)
#   ^ mirrors R4's own DEC_DEFAULTS exactly, plus the one new declared attr,
#     dependent_cost (defaults to 0.0; always explicitly overridden below).

AFFECT_DEFAULTS_R6 = dict(AFFECT_DEFAULTS)  # unchanged, re-exported for clarity


def resolve_outcome() -> float:
    """MECHANICAL, ARM-INDEPENDENT outcome resolution -- R6's own design
    (ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md Part B1/Part E)
    keeps escape's CONTINGENCY fixed at R4's own CONTINGENT-arm operating
    point (an attempt, when made, always succeeds) in BOTH R6 arms, so that
    dependent_cost is the ONLY axis varied. Returns 1.0 unconditionally --
    the SAME constant R4's own contingent arm delivers."""
    return 1.0


class AbusiveR6DependentCostWorld:
    """One victim EmotionHub (HeldEmotionParams + EscapeDecision + two
    candidate Appraisals + a harm-analog AffectiveState), riding R4's own
    escape/stay Argmax and belief update UNMODIFIED plus R6's one new
    dependent-cost re-derivation. ``step()`` advances one tick: if the
    PREVIOUS tick's decision was to attempt, deliver that attempt's outcome
    (always 1.0, mechanical, arm-independent); run_rules(); read back. NO
    decision here -- only world delivery + read-back."""

    def __init__(self, dependent_cost: float, *, p0=P0_MEAN, lr=LR, escape_value=ESCAPE_VALUE,
                 attempt_cost=ATTEMPT_COST, k_self=K_SELF, setpoint=SETPOINT):
        self.dependent_cost = float(dependent_cost)
        self.s = srs.Substrate()
        self.inner = self.s._inner
        self.root = self.s.add_node("Agent", {"role": "victim_root"})
        # load_seed_manifest loads exactly the named seed's rules -- it does
        # NOT walk depends_on -- so every seed whose RULES this world needs
        # is loaded explicitly, matching R4's own world's convention.
        for seed in ("core_emotions", "abusive_r4_learned_helplessness", "abusive_r6_dependent_cost"):
            self.inner.load_seed_manifest(manifest_for(seed), self.root)

        self.hub = self.s.add_node("EmotionHub", {"name": "victim"})

        ep = dict(EP_DEFAULTS)
        self.ep = self.s.add_node("HeldEmotionParams", ep)
        self.inner.add_edge_unchecked(self.hub, "has_emotion_params", self.ep)

        dec = dict(DEC_DEFAULTS)
        dec.update(contingency_prior=float(p0), lr=float(lr), escape_value=float(escape_value),
                   attempt_cost=float(attempt_cost), dependent_cost=float(dependent_cost))
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

        af = dict(AFFECT_DEFAULTS_R6)
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
                    dependent_cost=dec["dependent_cost"],
                    outcome=dec["outcome"], arousal=aff["arousal"])

    # ------------------------------------------------------------------- step
    def step(self):
        """Advance one tick: (1) if the PREVIOUS tick's decision was to
        attempt, mechanically resolve and deliver that attempt's outcome
        (INGEST -- a world fact, always 1.0, never a decision); (2)
        run_rules() (the graph updates the belief from that outcome, applies
        R6's own dependent-cost re-derivation, THEN decides this tick's
        attempt/stay); (3) read back (EMIT). NO decision here."""
        self.epoch += 1
        if self.pending_attempt:
            outcome = resolve_outcome()
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
