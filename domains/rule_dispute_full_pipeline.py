"""rule_dispute_full_pipeline -- ONE real, callable, persistent entry point
over the whole arc: raw held beliefs -> computed severity -> defuse/escalate
-> residual attribution -> self-conscious emotion -> recorded back into the
claimant's own real, domain-scoped, persistent CAN self_worth.

Per docs/research/psychology_affect/WIRE_IN_PREREG.md. Every piece here was
independently built and tested across five prior rungs:

  seeds/dispute_severity_from_beliefs.json     -- issue_severity as residual
  seeds/rule_dispute_escalation.json           -- defuse/escalate
  seeds/rule_dispute_self_conscious_bridge.json -- outcome -> attribution
  seeds/self_conscious_emotions.json           -- pride/shame/guilt/embarrassment
  domains/can_self_worth_bridge.py             -- real, persistent, domain-
                                                   scoped, personality-
                                                   plastic CAN self_worth

This module is pure world-adapter code (CLAUDE.md's architecture rule): it
mechanically (a) loads all four seeds + installs bigville_can_beliefs'
Gamma productions on one substrate, (b) reads/writes the SAME node shapes
every prior rung's own demo/test harness already used by hand, and (c)
sequences the calls in the one order that makes them compose. No new
decision is made anywhere in this file -- every decision (severity,
outcome, attribution, emotion, the updated belief) is still made entirely
by the engine's own rules or can_self_worth_bridge's own relaxation calls.
"""
from __future__ import annotations

import json

from substrate.seed_loader import engine_rules_only

from domains.can_self_worth_bridge import (
    ensure_can_seed, ensure_peer_comparison_seed, find_or_build_resident_can,
    mint_domain_self_worth, mint_peer_comparison_context, read_relative_self_worth,
    record_incident_outcome, record_self_conscious_consequence,
)

_PIPELINE_SEED_PATHS = [
    "seeds/rule_dispute_escalation.json",
    "seeds/dispute_severity_from_beliefs.json",
    "seeds/self_conscious_emotions.json",
    "seeds/rule_dispute_self_conscious_bridge.json",
]


def ensure_pipeline_seeds(inner) -> None:
    """Idempotently load every seed the full pipeline needs, in the one
    dependency order that lets each seed's own productions be ready before
    the next is loaded, plus can_self_worth_bridge's own CAN seed/
    productions. Guarded by a sentinel node, mirroring ensure_can_seed's
    own idempotency idiom exactly."""
    ensure_peer_comparison_seed(inner)
    if inner.nodes("RuleDisputePipelineSeedLoaded"):
        return
    for path in _PIPELINE_SEED_PATHS:
        d = json.load(open(path))
        inner.load_seed_manifest(engine_rules_only(d))
    inner.add_node("RuleDisputePipelineSeedLoaded", {})


def run_rule_dispute(inner, *, claimant: dict, claim_pred, truth_pred, domain: str,
                     band_code: float, witnesses=(), base_audience_gain: float = 0.15,
                     belief_plasticity: float = 0.3, max_steps: int = 3000):
    """Run ONE real dispute end to end for `claimant` (a
    worlds/bigville_can_beliefs.py-shaped resident record) and return the
    fully-decided result, having ALSO recorded the outcome back into the
    claimant's own persistent, domain-scoped self_worth.

    `claim_pred`/`truth_pred`: predication triples (e.g.
    `["pays_pot", "free_parking", True]`), exactly as
    dispute_severity_from_beliefs.json's own harness already used.
    `domain`: which of the claimant's domain-scoped self-worth beliefs
    this dispute is about (e.g. "monopoly_rules") -- minted/reused via
    mint_domain_self_worth, so repeated disputes about the SAME domain
    accumulate on the SAME belief (WIRE_IN_PREREG.md Sec2).
    `witnesses`: list of per-witness closeness values (rule_dispute_
    escalation.json's own WitnessPresence shape).
    `base_audience_gain`: HABITUATES (EVIDENCE_AND_AUDIENCE_WEIGHTING_
    PREREG.md Sec1) -- the value actually supplied to seeds/rule_dispute_
    escalation.json's own (unedited) `DisputeContext.audience_gain` field
    is `base_audience_gain / (claimant_dispute_count + 1)`,
    `claimant_dispute_count` a REAL observed quantity (how many
    `run_rule_dispute` calls this claimant has been through before,
    ACROSS all domains -- audience habituation generalizes, unlike
    domain-scoped belief). A resident's first-ever dispute is unaffected
    (byte-identical to pre-audit behavior).
    `belief_plasticity`: the claimant's own personality trait
    (DOMAIN_SELF_WORTH_PROJECTION_PREREG.md Sec4b) -- how readily this
    incident's outcome can move their domain-scoped self_worth. A caller
    should read this from `claimant["params"]`, not hard-code it; the
    default exists only for callers that have not drawn the trait.

    Returns {issue_severity, dispute_outcome, attribution_locus, emotion,
    self_worth_before, self_worth_after, domain_concept}. If the two
    beliefs are IDENTICAL (StructSim=1.0), no dispute exists at all
    (DISPUTE_SEVERITY_AS_RESIDUAL_PREREG.md's own registered floor) and
    this returns {"dispute_minted": False} -- there is nothing to record.
    """
    ensure_pipeline_seeds(inner)

    resident_can = find_or_build_resident_can(inner, claimant, max_steps=max_steps)
    domain_concept = mint_domain_self_worth(inner, resident_can, domain,
                                            max_steps=max_steps)
    mint_peer_comparison_context(inner, domain_concept)
    self_worth_before = inner.node(domain_concept)["attrs"]["state"]
    # RELATIVE_SELF_WORTH_PREREG.md: the appraisal reads how the claimant
    # stacks up against their own peer-comparison log-odds baseline, not
    # raw absolute state alone -- self-worth can drop with zero change to
    # the claimant's own track record if the comparison baseline moved.
    relative_self_worth_before = read_relative_self_worth(inner, domain_concept)

    resident_node = resident_can["resident_node"]
    dispute_count = int(inner.node(resident_node)["attrs"].get("dispute_count", 0))
    effective_audience_gain = base_audience_gain / (dispute_count + 1)
    inner.set_attr(resident_node, "dispute_count", dispute_count + 1)

    claims = inner.add_node("HeldBelief", {"pred": list(claim_pred)})
    truth = inner.add_node("HeldBelief", {"pred": list(truth_pred)})
    bd = inner.add_node("BeliefDisagreement", {
        "band_code": band_code, "audience_gain": effective_audience_gain,
    })
    inner.add_edge(bd, "claims", claims, {})
    inner.add_edge(bd, "truth", truth, {})
    for closeness in witnesses:
        w = inner.add_node("WitnessPresence", {"closeness": closeness})
        inner.add_edge(bd, "has_witness", w, {})
    pattern = inner.add_node("SelfPattern", {
        "held_self_worth": float(relative_self_worth_before)})
    inner.add_edge(bd, "has_self_pattern", pattern, {})

    inner.run_rules(50)
    inner.add_node("NativeRuleDisputeReceipt", {
        "schema": "native_rule_dispute_receipt_v1",
        "cluster": "rule_dispute_full_pipeline.dispute_settlement",
        "provenance": "native_rule_readback:rule_dispute_pipeline",
        "native_rule": "rule_dispute_full_pipeline_native_rules",
        "native_steps": ["mint_dispute_evidence", "run_rules", "readback"],
        "outcome_source": "native_rule_readback",
        "python_outcome_selection": False,
    })

    bridged = inner.neighbours(bd, "bridged_to")
    if not bridged:
        return {"dispute_minted": False, "domain_concept": domain_concept,
                "self_worth_before": self_worth_before,
                "self_worth_after": self_worth_before,
                "relative_self_worth_before": relative_self_worth_before,
                "relative_self_worth_after": relative_self_worth_before}
    ctx = bridged[0]
    sig = inner.neighbours(ctx, "has_signal")[0]
    issue_severity = inner.node(ctx)["attrs"]["issue_severity"]
    dispute_outcome = inner.node(sig)["attrs"]["outcome"]

    sc_ctx = inner.neighbours(ctx, "bridged_to")
    sc_ctx = [n for n in sc_ctx if inner.node(n)["type"] == "SelfConsciousContext"][0] \
        if len(sc_ctx) > 1 else sc_ctx[0]
    attribution_locus = inner.node(sc_ctx)["attrs"]["attribution_locus"]
    standard_met = inner.node(sc_ctx)["attrs"]["standard_met"] == 1.0
    sc_sig = inner.neighbours(sc_ctx, "has_appraisal")[0]
    emotion = inner.node(sc_sig)["attrs"]["emotion"]

    self_worth_after = record_incident_outcome(
        inner, {"self_worth": domain_concept}, standard_met=standard_met,
        attribution_locus=attribution_locus, alpha=belief_plasticity,
        max_steps=max_steps)
    relative_self_worth_after = read_relative_self_worth(inner, domain_concept)
    consequence = record_self_conscious_consequence(
        inner, resident_can, domain, emotion=emotion, max_steps=max_steps)

    return {
        "dispute_minted": True, "issue_severity": issue_severity,
        "dispute_outcome": dispute_outcome, "attribution_locus": attribution_locus,
        "emotion": emotion, "self_worth_before": self_worth_before,
        "self_worth_after": self_worth_after,
        "relative_self_worth_before": relative_self_worth_before,
        "relative_self_worth_after": relative_self_worth_after,
        "domain_concept": domain_concept,
        "reparative_desire_state": consequence["reparative_desire_state"],
        "withdrawal_desire_state": consequence["withdrawal_desire_state"],
    }


__all__ = ["ensure_pipeline_seeds", "run_rule_dispute"]
