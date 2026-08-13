"""Self-improvement loop — composes can_ops primitives + policy enforcement.

Per self_improvement_dynamics:
  · Foundational Mts are FROZEN (no Hebbian, no decay, no h drift)
  · Domain Mts are ADAPTIVE (Hebbian + decay + h drift)
  · Hybrid Mts have per-axis policy (allow_Hebbian_J, allow_h_drift,
    allow_structural_update, allow_beta_change)

This module enforces policy at the orchestration layer; the Rust can_ops
ops are pure mechanism with no policy check.

The loop iteration:
  1. Monitor — audit basin topology per Mt
  2. Detect — pattern match against failure-mode signatures
  3. Correct — apply policy-respecting mutation ops
  4. Verify — re-audit; revert if metrics worsened
  5. Track — substrate-level rollup

This is a world-adapter operation: mechanical orchestration, no agent
decisions. The decisions live in the graph (per-Mt update_policy attr,
substrate-level failure-mode detector rules) and the substrate's existing
reflexes (architecture_cortex, meta_monitor, DevelopmentCortex).
"""
from __future__ import annotations

from typing import Any


# ----------------------------------------------------------------------
# Policy helpers — read update_policy off each Mt.
# ----------------------------------------------------------------------

FROZEN = "frozen"
ADAPTIVE = "adaptive"
HYBRID = "hybrid"
DEFAULT_POLICY = FROZEN  # safe default — opt in to adaptation


def mt_update_policy(substrate, mt) -> str:
    """Return the Mt's update_policy attr; defaults to 'frozen' (safe)."""
    return substrate.node(mt)["attrs"].get("update_policy", DEFAULT_POLICY)


def mt_allows(substrate, mt, axis: str) -> bool:
    """Per-axis policy check for hybrid Mts. Axes:
      allow_Hebbian_J, allow_h_drift, allow_structural_update,
      allow_beta_change.
    For frozen Mts: always False. For adaptive: always True. For hybrid:
    read per-axis attr (default True for axes not listed)."""
    policy = mt_update_policy(substrate, mt)
    if policy == FROZEN:
        return False
    if policy == ADAPTIVE:
        return True
    # hybrid
    return bool(substrate.node(mt)["attrs"].get(axis, True))


# ----------------------------------------------------------------------
# Per-Mt mutation: respects policy.
# ----------------------------------------------------------------------

def _is_native(substrate, mt) -> bool:
    """Gate condition reused by every gated operation below — the SAME
    `discrete_mode` check `insight_seeking.py::seek_insights` already uses
    (CAN_FINAL_MIGRATION_RESULTS.md Sec2.2)."""
    return substrate.node(mt)["attrs"].get("discrete_mode") in ("2state", "3state")


def _audit_basin(substrate, mt) -> dict[str, Any]:
    """Gated basin audit — native branch reads `state` directly (pure,
    no relax call) via `can_native_orchestration.native_audit_basin`;
    continuous branch is the unmodified `substrate.mt_audit_basin` call.
    See `relax`'s own docstring for why this composes correctly with the
    "one shared fixpoint" native architecture."""
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import native_audit_basin
        return native_audit_basin(substrate, mt)
    return substrate.mt_audit_basin(mt)


def maybe_hebbian(substrate, mt, eta: float = 0.01) -> int:
    """Apply Hebbian J update iff Mt's policy allows OR a transient
    plasticity_override is in effect (set by correction_raise_plasticity
    in response to a detected frozen_should_adapt event). Returns
    edges updated (continuous) or the scoped fixpoint's own progressing
    step count (native — see the native branch's own docstring note below).

    Native branch (CAN_MT_SCOPED_RULES_RESULTS.md): calls
    `run_rules_scoped(mt)` via `can_native_orchestration.scoped_settle`,
    isolated to THIS Mt. `can_native_hebbian_mint`/`_reweight` already carry
    their OWN `mt_allows`-equivalent policy gate + `plasticity_override`
    check inside the rule's `where`-clause (CAN_HEBBIAN_MATERIALIZATION_
    RESULTS.md, confirmed by direct read) — this function does not
    duplicate that gate for the native path; `eta` has no native analog
    (mint/reweight are threshold/counter-based, not eta-scaled) and is
    silently unused there, a genuine simplification, not an oversight."""
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import scoped_settle
        return scoped_settle(substrate, mt)
    if mt_allows(substrate, mt, "allow_Hebbian_J"):
        return substrate.mt_hebbian_update_J(mt, eta)
    # Plasticity override path — frozen Mt being temporarily allowed
    # to learn because evidence has been sustained against its target.
    # Per the user's principle 'frozen permanently? never'.
    override = float(substrate.node(mt)["attrs"].get(
        "plasticity_override", 0.0))
    if override > 0:
        return substrate.mt_hebbian_update_J(mt, override)
    return 0


def maybe_decay_J(substrate, mt, decay_rate: float = 0.001) -> int:
    """Apply J decay iff Mt's policy allows.

    Native branch (CAN_MT_SCOPED_RULES_RESULTS.md): `can_decay_identity.
    json`'s `can_native_evidence_decay` decays the Hebbian
    `evidence_confirm`/`evidence_disconfirm` COUNTERS on each pair's
    Coactivation ledger, not a `causal_influence` edge weight directly —
    native CAN has no graded J to decay (edges are discrete mint/no-mint).
    This is the closest real native analog ("evidence loses weight over
    time unless reinforced", the SAME role `can_ops.rs:829-834`'s own
    docstring gives continuous h-decay), reported honestly as a
    re-targeted quantity, not claimed equivalent. `decay_rate` has no
    native analog (the native decay is a fixed 1-quantum linear
    decrement, CAN_DECAY_IDENTITY_RESULTS.md Sec1) and is silently unused
    on this branch."""
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import scoped_settle
        return scoped_settle(substrate, mt)
    if not mt_allows(substrate, mt, "allow_Hebbian_J"):
        return 0
    return substrate.mt_decay_J(mt, decay_rate)


def maybe_decay_h(substrate, mt, decay_rate: float = 0.0001) -> int:
    """Apply h decay iff Mt's policy allows h drift.

    MIGRATED for native Mts (CAN_EXTERNAL_FIELD_DECAY_RESULTS.md — closes
    the last-named blocker in CAN_MT_SCOPED_RULES_RESULTS.md §4c). Native
    branch: `seeds/can_decay_identity.json` v1.1.0's `can_native_
    external_field_decay` writes `external_field` directly (the ONE
    quantity `can_native_update_3state`/`_2state`'s own local-field formula
    reads six times but no rule wrote before v1.1.0) — a symmetric
    clamp-toward-zero by exactly 1 quantum per strictly-later external
    tick (max(h-1,0) when positive, min(h+1,0) when negative), the required
    generalisation of `can_native_evidence_decay`'s one-sided integer-floor
    shape since `external_field` is a signed float with no native
    accumulation rule (unlike the two evidence ledgers, which are grown +1
    by the SAME rule family that decays them). No same-tick-race guard is
    needed here (confirmed by direct grep: no native rule and no Python
    module, including `can_counterfactual.py`, ever writes `external_field`
    — decay is the only writer this attr ever gets). `decay_rate` has no
    native analog (fixed 1-quantum decrement, same precedent as `maybe_
    decay_J`) and is silently unused on this branch. Continuous path
    (`mt_allows` check + `substrate.mt_decay_h`) is unconditional and
    byte-unchanged."""
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import scoped_settle
        return scoped_settle(substrate, mt)
    if not mt_allows(substrate, mt, "allow_h_drift"):
        return 0
    return substrate.mt_decay_h(mt, decay_rate)


def relax(substrate, mt) -> int:
    """Always-allowed: relax network to equilibrium under Mt's H.
    Reading equilibrium isn't policy-gated; only J/h mutations are.

    Native branch (CAN_MT_SCOPED_RULES_RESULTS.md): a discrete_mode Mt
    settles via its OWN scoped rule fixpoint (`can_native_update_3state`/
    `_2state`), isolated from every other Mt by `run_rules_scoped` — the
    orchestration hazard `CAN_FINAL_MIGRATION_RESULTS.md` Sec0 confirmed
    live is exactly why this was never wired before this rung. Continuous
    branch (`mt_relax_to_marginal`) is byte-unchanged.

    MEASURED, NOT ASSUMED (see RESULTS doc): because `run_rules_scoped`
    always runs its Mt's rules to a FULL fixpoint (every gated-open native
    rule, not just the discrete update), a native Mt's `relax()` call this
    tick can ALSO advance Hebbian mint/reweight and evidence decay in the
    same call — the later `maybe_hebbian`/`maybe_decay_J` calls this
    module makes are then idempotent no-ops (0 steps) for the same
    `can_tick` unless something changes between calls. This is a real
    architectural difference from the continuous path (four separate
    formula calls) and is reported, not smoothed over."""
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import scoped_settle
        return scoped_settle(substrate, mt)
    return substrate.mt_relax_to_marginal(mt)


# ----------------------------------------------------------------------
# Failure-mode detection.
# ----------------------------------------------------------------------

def detect_failure_modes(report: dict) -> list[str]:
    """Pattern-match observable signatures in a basin audit report.

    Returns list of failure-mode names triggered. Each maps to a
    correction strategy:
      'frustrated' → split candidate
      'sparse'     → prune candidate
      'redundant'  → merge candidate (cross-Mt; not detected here)

    Thresholds are conservative — substrate's own self_improvement
    policy can override via per-Mt attrs in future iterations.
    """
    flags = []
    if report["concept_count"] == 0:
        return flags
    if report["frustration"] > 0.5:
        flags.append("frustrated")
    if report["coverage"] < max(1, report["concept_count"] // 3):
        flags.append("sparse")
    return flags


# ----------------------------------------------------------------------
# The loop step.
# ----------------------------------------------------------------------

def _stash_post_state(substrate, mt, post_audit) -> None:
    """Write post-step frustration + per-Concept σ + per-Concept h_id
    + distance-to-target magnitude as Mt-side attrs for next step's
    derivatives + signals.

    Maintains:
        previous_previous_frustration   ← was previous_frustration
        previous_frustration            ← this step's frustration
        distance_to_target_magnitude    ← this step's distance signal
                                          (used by frozen_should_adapt)
        previous_sigma_<cid>            ← σ at end of this step
        previous_identity_<cid>         ← h_id at end of this step

    The anticipation + formation reflexes read current values via Var
    bindings, not from attrs — they fire before this stash runs.
    Frozen-should-adapt reads distance from this stash on the
    following step."""
    mt_attrs = substrate.node(mt)["attrs"]
    f_current = float(post_audit["frustration"])
    f_prev = float(mt_attrs.get("previous_frustration", f_current))
    f_prev_prev = float(mt_attrs.get("previous_previous_frustration",
                                     f_prev))
    # Compute derivatives BEFORE rolling the window, so per_mt
    # FilterSpecs for insight / anticipation can read them.
    delta_f = f_current - f_prev
    d2_f = f_current - 2.0 * f_prev + f_prev_prev
    substrate.set_attr(mt, "delta_f", delta_f)
    substrate.set_attr(mt, "d2_f", d2_f)
    substrate.set_attr(mt, "previous_previous_frustration", f_prev)
    substrate.set_attr(mt, "previous_frustration", f_current)
    # Distance-to-target magnitude — drives frozen_should_adapt detection.
    # Native branch (CAN_MT_SCOPED_RULES_RESULTS.md): reads `state`
    # directly instead of relaxing (mt_distance_to_target's continuous
    # path calls mt_mean_field_marginal internally) — the small,
    # representation-agnostic composition CAN_FINAL_MIGRATION_RESULTS.md
    # Sec0 named as buildable and did not build, now safe because
    # `native_distance_to_target` never calls run_rules() at all (it is a
    # pure read of already-settled state).
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import native_distance_to_target
        distance = native_distance_to_target(substrate, mt)
    else:
        distance = substrate.mt_distance_to_target(mt)
    substrate.set_attr(mt, "distance_to_target_magnitude",
                       float(distance["magnitude"]))
    # Coverage — drives sparse_Mt detection.
    substrate.set_attr(mt, "coverage", int(post_audit["coverage"]))
    marginal = post_audit["marginal"]
    for c in substrate.neighbours(mt, "has_concept"):
        cid = c.value if hasattr(c, "value") else int(c)
        sig = float(marginal.get(cid, 0.0))
        substrate.set_attr(mt, f"previous_sigma_{cid}", sig)
        h_id = float(substrate.node(c)["attrs"].get("identity_field", 0.0))
        # Compute Δh_id BEFORE overwriting previous_identity, so the
        # per_concept FilterSpec for identity_formation can read it.
        prev_h_id = float(mt_attrs.get(f"previous_identity_{cid}", h_id))
        substrate.set_attr(c, "delta_identity", h_id - prev_h_id)
        substrate.set_attr(mt, f"previous_identity_{cid}", h_id)


def maybe_update_identity(
    substrate, mt,
    alpha: float = 0.01, beta: float = 0.001,
) -> int:
    """Slow identity dynamics: h_id ← h_id + α·σ - β·h_id per Concept.
    Skips frozen Mts. Adaptive: identity emerges from sustained σ;
    flips average to zero → identity decays.

    MIGRATED for native Mts (CAN_IDENTITY_FEEDBACK_RESULTS.md — closes the
    identity-feedback gap `CAN_DECAY_IDENTITY_RESULTS.md` §2/
    `CAN_MT_SCOPED_RULES_RESULTS.md` §5/`CAN_EXTERNAL_FIELD_DECAY_RESULTS.md`
    §6 all named and explicitly declined to build). Native branch:
    `seeds/can_decay_identity.json` v1.2.0's `can_native_identity_field_
    feedback` writes `identity_field` FROM `can_native_identity_evidence_
    sample`'s own log-odds render — a fixed 1-quantum step toward the
    render's sign each strictly-later external tick (neutral/flip-flop
    reading decays `identity_field` toward zero via the same `Max`/`Min`
    clamp `can_native_external_field_decay` already uses), the SAME
    `allow_h_drift` policy axis every rule in this seed checks. A
    magnitude/recurrence-scaled step was investigated and REJECTED on
    stability grounds — a per-tick jump that grows in size threatens the
    discrete-async update's own Lyapunov convergence argument; a fixed
    quantum was chosen and validated against a real 60-draw (3-state) +
    60-draw (2-state) convergence sweep with the feedback loop active
    (`CAN_IDENTITY_FEEDBACK_RESULTS.md` §3: 0 non-convergent draws either
    mode). `alpha`/`beta` have no native analog (fixed 1-quantum step, same
    precedent as every other native decay rule in this seed) and are
    silently unused on this branch. Continuous path (`mt_allows` check +
    `substrate.mt_update_identity_dynamics`) is unconditional and
    byte-unchanged."""
    if _is_native(substrate, mt):
        from domains.can_native_orchestration import scoped_settle
        return scoped_settle(substrate, mt)
    if not mt_allows(substrate, mt, "allow_h_drift"):
        return 0
    return substrate.mt_update_identity_dynamics(mt, alpha, beta)


def nudge_identity_on_flipped(
    substrate, mt, insight: dict[str, Any],
    base_alpha: float = 0.05,
) -> int:
    """When an insight is consolidated, nudge identity_field on each
    flipped node toward the new σ. Recurrence boosts α — substrate
    'recognises' returning to the same basin and commits more.

    Skips frozen Mts. Returns count of nudges applied.

    STAYS on the continuous path for native Mts — investigated during
    `CAN_IDENTITY_FEEDBACK_RESULTS.md` (the identity-feedback gap
    `maybe_update_identity` closed, §above, is NOT the reason this one
    stays blocked; the reason is genuinely different, found by direct
    investigation, not copy-pasted). `can_native_identity_field_feedback`
    (`seeds/can_decay_identity.json` v1.2.0) is a per-tick, epoch-gated,
    whole-Mt sample step driven by the AMBIENT observed σ each Concept
    already has — it has no input surface for this function's own EVENT
    shape: a SPECIFIC set of flipped node ids, an injected `target_sigma`
    per node (the insight's own new σ, not necessarily what `state`
    already reads), and a `recurrence_count`-scaled `alpha_eff`. A
    magnitude/recurrence-scaled per-tick step was investigated for
    `maybe_update_identity` and REJECTED on stability grounds (a growing
    per-tick jump threatens the discrete-async Lyapunov convergence
    argument, `CAN_IDENTITY_FEEDBACK_PREREG.md` §2.2/§2.3) — the SAME
    rejection applies here even more directly, since this function's whole
    point is an IMMEDIATE, LARGER nudge on insight consolidation, which is
    exactly the unbounded-step shape the convergence sweep was built to
    guard against. Wiring this function onto the fixed-quantum per-tick
    rule would silently discard the event's own target_sigma/recurrence
    signal and just let the ambient tick-based rule do whatever it would
    have done anyway — not a real migration of this function's contract,
    reported honestly rather than forced through to claim a round 7/7."""
    if not mt_allows(substrate, mt, "allow_h_drift"):
        return 0
    if not insight or "flipped_nodes" not in insight:
        return 0
    import math
    recurrence = int(insight.get("recurrence_count", 1))
    # log scaling so recurrence doesn't blow up — α grows but bounded.
    alpha_eff = base_alpha * (1.0 + math.log(max(1, recurrence)))
    nudged = 0
    # Look up the actual node handles by id.
    flipped_by_id = {int(f["node"]): float(f["after"])
                     for f in insight["flipped_nodes"]}
    for c in substrate.neighbours(mt, "has_concept"):
        cid = c.value if hasattr(c, "value") else int(c)
        if cid in flipped_by_id:
            substrate.concept_nudge_identity(
                c, flipped_by_id[cid], alpha_eff)
            nudged += 1
    return nudged


def self_improvement_step(
    substrate,
    eta: float = 0.01,
    decay_rate: float = 0.001,
    h_decay: float = 0.0001,
    detect_insights: bool = True,
    identity_alpha: float = 0.01,
    identity_beta: float = 0.001,
    identity_nudge_alpha: float = 0.05,
) -> dict[int, dict[str, Any]]:
    """One iteration of the loop.

    For each Microtheory:
      1. Read previous frustration + state (from `previous_*` attrs
         written by the prior step's stash).
      2. Relax network to equilibrium under current h (always permitted).
      3. Audit basin topology.
      4. Detect insight: compare previous frustration vs current; if
         ΔF < −threshold and at least one node flipped, that's an
         insight event. Consolidate the new basin via elevated Hebbian
         (adaptive Mts only).
      5. Apply baseline mutations: Hebbian, J decay, h decay (policy-gated).
      6. Re-relax + re-audit after mutations.
      7. Stash new previous_frustration + per-Concept previous_state for
         the NEXT step's comparison.

    Returns: {mt_id: {policy, pre_audit, post_audit, edges_hebbian,
                      edges_decayed, fields_decayed, failure_modes,
                      insight, consolidation_edges}}

    `insight` is None most of the time; a dict on the step when a
    frustrated basin discovers coherence."""
    from domains.insight_detection import (
        compute_delta_f_via_substrate,
        consolidate_insight,
        detect_insight,
        read_previous_state,
    )

    results: dict[int, dict[str, Any]] = {}
    for mt in substrate.nodes("Microtheory"):
        # Read what the previous step stashed.
        prev_frust, prev_state = read_previous_state(substrate, mt)

        relax(substrate, mt)
        pre = _audit_basin(substrate, mt)

        # Detect insight from previous step's frustration vs current.
        # ΔF computed via substrate's native evaluator on a Term-tree
        # composed by the order_n_concepts machinery.
        insight = None
        consolidation_edges = 0
        if detect_insights:
            delta_f = None
            if "previous_frustration" in substrate.node(mt)["attrs"]:
                delta_f = compute_delta_f_via_substrate(
                    substrate, mt, float(pre["frustration"]))
            insight = detect_insight(prev_frust, prev_state, pre,
                                     mt.value if hasattr(mt, "value")
                                     else int(mt),
                                     delta_f=delta_f)
            if insight is not None:
                consolidation_edges = consolidate_insight(substrate, mt)
                if consolidation_edges:
                    relax(substrate, mt)
                    pre = _audit_basin(substrate, mt)
                # Name + record the insight as a graph node so the
                # substrate accumulates a queryable history of its own
                # realisations.
                from domains.insight_naming import (
                    build_name_lookup,
                    name_insight,
                    record_insight,
                )
                name_lookup = build_name_lookup(substrate, mt)
                insight["names"] = name_insight(insight, name_lookup)
                recorded = record_insight(substrate, mt, insight, name_lookup)
                if recorded is not None:
                    insight["recorded_as_node"] = (
                        recorded.value if hasattr(recorded, "value")
                        else int(recorded)
                    )
                # Cross-Mt propagation: cascade through shared Concepts
                # within the same step.
                from domains.insight_propagation import propagate_insight
                insight["cascades"] = propagate_insight(
                    substrate, mt, insight)
                # Identity nudge on flipped nodes — substrate becomes
                # its commitments. Recurrence boosts the nudge.
                insight["identity_nudges"] = nudge_identity_on_flipped(
                    substrate, mt, insight,
                    base_alpha=identity_nudge_alpha,
                )

        # Decay plasticity_override (if any) BEFORE Hebbian — so the
        # override fades naturally as the substrate processes more
        # steps. raise_plasticity is supposed to be transient.
        from domains.correction_raise_plasticity import (
            decay_plasticity_override,
        )
        decay_plasticity_override(substrate, mt)

        # Baseline mutations.
        edges_hebbian = maybe_hebbian(substrate, mt, eta)
        edges_decayed = maybe_decay_J(substrate, mt, decay_rate)
        fields_decayed = maybe_decay_h(substrate, mt, h_decay)
        identity_updated = maybe_update_identity(
            substrate, mt, identity_alpha, identity_beta)

        if edges_hebbian or edges_decayed or fields_decayed or identity_updated:
            relax(substrate, mt)
        post = _audit_basin(substrate, mt)

        # Anticipation reflex: order-2-time of F suggests an insight
        # is brewing even though we haven't crossed the detection
        # threshold yet. Composed via the order_n_concepts Term-tree
        # machinery + evaluated by the substrate.
        anticipation = None
        if detect_insights:
            from domains.anticipation import (
                detect_anticipation,
                record_anticipation,
            )
            anticipation = detect_anticipation(
                substrate, mt,
                current_frustration=float(post["frustration"]),
                insight_already_detected=(insight is not None),
            )
            if anticipation is not None:
                recorded_anticipation = record_anticipation(
                    substrate, mt, anticipation)
                if recorded_anticipation is not None:
                    anticipation["recorded_as_node"] = (
                        recorded_anticipation.value
                        if hasattr(recorded_anticipation, "value")
                        else int(recorded_anticipation)
                    )

        # Identity-formation signal: order-1-time of h_id per Concept.
        # Sustained drift across many consecutive steps → fires an
        # IdentityFormationEvent. Same order_n_concepts machinery.
        identity_formations = []
        if detect_insights:
            from domains.identity_formation import (
                detect_identity_formation,
                record_identity_formation,
            )
            identity_formations = detect_identity_formation(substrate, mt)
            for formation in identity_formations:
                recorded_formation = record_identity_formation(
                    substrate, mt, formation)
                if recorded_formation is not None:
                    formation["recorded_as_node"] = (
                        recorded_formation.value
                        if hasattr(recorded_formation, "value")
                        else int(recorded_formation)
                    )

        # Stash for next iteration's insight comparison.
        _stash_post_state(substrate, mt, post)

        results[mt.value if hasattr(mt, "value") else int(mt)] = {
            "policy": mt_update_policy(substrate, mt),
            "pre_audit": pre,
            "post_audit": post,
            "edges_hebbian": edges_hebbian,
            "edges_decayed": edges_decayed,
            "fields_decayed": fields_decayed,
            "failure_modes": detect_failure_modes(post),
            "insight": insight,
            "consolidation_edges": consolidation_edges,
            "anticipation": anticipation,
            "identity_formations": identity_formations,
        }

    # Substrate-level failure-mode detection. Per the agent's design
    # outputs (scripts/agent_designs_filter.py), these target ALL 6
    # failure modes named by self_improvement_dynamics:
    #   · fail_mode_redundant_Mt           (cross-Mt similarity)
    #   · fail_mode_conflicting_reflexes   (per-shared-node opposition)
    #   · fail_mode_frozen_should_adapt    (frozen Mt sustained distance)
    #   · fail_mode_drifted_past_anchor    (adaptive Mt sustained distance)
    #   · fail_mode_frustrated_Mt          (F high sustained)
    #   · fail_mode_sparse_Mt              (coverage low sustained)
    if detect_insights:
        from domains.conflict_detection import (
            detect_conflicts_all_pairs,
            record_conflict,
        )
        from domains.drift_signal import (
            detect_drifted_past_anchor_all,
            record_drift,
        )
        from domains.frozen_adaptation_signal import (
            detect_frozen_should_adapt_all,
            record_frozen_should_adapt,
        )
        from domains.frustration_signal import (
            detect_frustrated_mt_all,
            record_frustrated_mt,
        )
        from domains.redundancy_detection import (
            detect_redundancy_all_pairs,
            record_redundancy,
        )
        from domains.sparseness_signal import (
            detect_sparse_mt_all,
            record_sparse_mt,
        )
        redundancy_events = detect_redundancy_all_pairs(substrate)
        for event in redundancy_events:
            recorded = record_redundancy(substrate, event)
            if recorded is not None:
                event["recorded_as_node"] = (
                    recorded.value if hasattr(recorded, "value")
                    else int(recorded)
                )
        conflict_events = detect_conflicts_all_pairs(substrate)
        for event in conflict_events:
            recorded = record_conflict(substrate, event)
            if recorded is not None:
                event["recorded_as_node"] = (
                    recorded.value if hasattr(recorded, "value")
                    else int(recorded)
                )
        # CORRECTION: beta_reweight acts on the just-fired conflict
        # events. Substrate-level frame-choice. Per the agent's
        # design from scripts/agent_designs_next.py.
        from domains.correction_beta_reweight import (
            apply_beta_reweight,
            record_beta_reweight_applied,
        )
        for event in conflict_events:
            mt_a_id = event["mt_a_id"]
            mt_b_id = event["mt_b_id"]
            mt_a_handle = None
            mt_b_handle = None
            for candidate_mt in substrate.nodes("Microtheory"):
                cid = (candidate_mt.value
                       if hasattr(candidate_mt, "value")
                       else int(candidate_mt))
                if cid == mt_a_id:
                    mt_a_handle = candidate_mt
                elif cid == mt_b_id:
                    mt_b_handle = candidate_mt
            if mt_a_handle is not None and mt_b_handle is not None:
                new_betas = apply_beta_reweight(
                    substrate, mt_a_handle, mt_b_handle,
                    sigma_a=event["sigma_a"],
                    sigma_b=event["sigma_b"],
                )
                record_beta_reweight_applied(
                    substrate, mt_a_handle, mt_b_handle,
                    conflicted_node_id=event["node_id"],
                    new_betas=new_betas,
                )
                event["correction_applied"] = "beta_reweight"
                event["new_betas"] = new_betas
        frozen_adapt_events = detect_frozen_should_adapt_all(substrate)
        for event in frozen_adapt_events:
            recorded = record_frozen_should_adapt(substrate, event)
            if recorded is not None:
                event["recorded_as_node"] = (
                    recorded.value if hasattr(recorded, "value")
                    else int(recorded)
                )
        # CORRECTION: raise_plasticity acts on the just-fired
        # frozen_should_adapt events. Closes the detect→correct loop
        # for the first time. Per the agent's design from
        # scripts/agent_designs_next.py.
        from domains.correction_raise_plasticity import (
            apply_raise_plasticity,
            record_correction_applied,
        )
        for event in frozen_adapt_events:
            mt_id = event["mt_id"]
            for candidate_mt in substrate.nodes("Microtheory"):
                mt_candidate_id = (candidate_mt.value
                                    if hasattr(candidate_mt, "value")
                                    else int(candidate_mt))
                if mt_candidate_id == mt_id:
                    apply_raise_plasticity(substrate, candidate_mt)
                    record_correction_applied(
                        substrate, candidate_mt,
                        event_kind="frozen_should_adapt",
                        correction_name="raise_plasticity",
                    )
                    event["correction_applied"] = "raise_plasticity"
                    break
        drift_events = detect_drifted_past_anchor_all(substrate)
        for event in drift_events:
            recorded = record_drift(substrate, event)
            if recorded is not None:
                event["recorded_as_node"] = (
                    recorded.value if hasattr(recorded, "value")
                    else int(recorded)
                )
        frustrated_events = detect_frustrated_mt_all(substrate)
        for event in frustrated_events:
            recorded = record_frustrated_mt(substrate, event)
            if recorded is not None:
                event["recorded_as_node"] = (
                    recorded.value if hasattr(recorded, "value")
                    else int(recorded)
                )
        sparse_events = detect_sparse_mt_all(substrate)
        for event in sparse_events:
            recorded = record_sparse_mt(substrate, event)
            if recorded is not None:
                event["recorded_as_node"] = (
                    recorded.value if hasattr(recorded, "value")
                    else int(recorded)
                )
        # CORRECTION: prune_Mt acts on the just-fired sparse_Mt events.
        # β → BETA_MIN. Per the agent's design from agent_designs_next.
        from domains.correction_prune_mt import (
            apply_prune_mt,
            record_prune_applied,
        )
        for event in sparse_events:
            mt_id = event["mt_id"]
            for candidate_mt in substrate.nodes("Microtheory"):
                cid = (candidate_mt.value
                       if hasattr(candidate_mt, "value")
                       else int(candidate_mt))
                if cid == mt_id:
                    apply_prune_mt(substrate, candidate_mt)
                    record_prune_applied(substrate, candidate_mt)
                    event["correction_applied"] = "prune_Mt"
                    break
        # Annotate each Mt's result with event involvement.
        for event in redundancy_events:
            for mt_id in (event["mt_a_id"], event["mt_b_id"]):
                if mt_id in results:
                    results[mt_id].setdefault(
                        "redundancy_events", []).append(event)
        for event in conflict_events:
            for mt_id in (event["mt_a_id"], event["mt_b_id"]):
                if mt_id in results:
                    results[mt_id].setdefault(
                        "conflict_events", []).append(event)
        for event in frozen_adapt_events:
            mt_id = event["mt_id"]
            if mt_id in results:
                results[mt_id]["frozen_should_adapt_event"] = event
        for event in drift_events:
            mt_id = event["mt_id"]
            if mt_id in results:
                results[mt_id]["drift_event"] = event
        for event in frustrated_events:
            mt_id = event["mt_id"]
            if mt_id in results:
                results[mt_id]["frustrated_event"] = event
        for event in sparse_events:
            mt_id = event["mt_id"]
            if mt_id in results:
                results[mt_id]["sparse_event"] = event
        # Phase-1 graph-resident runtime: walk FilterSpec nodes from
        # the graph + dispatch. Runs ALONGSIDE the Python detectors
        # during migration. Once all detectors are FilterSpecs, the
        # Python imports above can be removed.
        from domains.runtime_discovery import (
            run_all_filter_specs, stash_pair_quantities,
        )
        # Pre-stage cross_mt pair quantities. per_concept delta_identity
        # is already stashed inside _stash_post_state.
        stash_pair_quantities(substrate)
        graph_resident_events = run_all_filter_specs(substrate)
        for event in graph_resident_events:
            # Events have either mt_id (per_mt/per_concept) OR
            # mt_a_id + mt_b_id (cross_mt). Annotate all involved Mts.
            target_ids = []
            if "mt_id" in event:
                target_ids.append(event["mt_id"])
            if "mt_a_id" in event:
                target_ids.append(event["mt_a_id"])
            if "mt_b_id" in event:
                target_ids.append(event["mt_b_id"])
            for mt_id in target_ids:
                if mt_id in results:
                    results[mt_id].setdefault(
                        "graph_resident_events", []).append(event)
    return results


def substrate_rollup(step_result: dict[int, dict[str, Any]]) -> dict[str, Any]:
    """Aggregate per-Mt results into substrate-level metrics.

    Substrate's objective (from self_improvement_dynamics):
        maximise (coherence + coverage) − (frustration + redundancy)

    Coherence here = −sum_of_energies / N (lower energy = more
    coherent); coverage = sum_of_per_Mt_coverage; frustration = sum.
    Redundancy needs cross-Mt comparison; deferred.
    """
    if not step_result:
        return {
            "mt_count": 0, "total_coherence": 0.0, "total_coverage": 0,
            "total_frustration": 0.0, "objective": 0.0,
        }
    total_energy = sum(r["post_audit"]["energy"] for r in step_result.values())
    total_coverage = sum(r["post_audit"]["coverage"] for r in step_result.values())
    total_frustration = sum(r["post_audit"]["frustration"] for r in step_result.values())
    mt_count = len(step_result)
    coherence = -total_energy / max(1, mt_count)
    return {
        "mt_count": mt_count,
        "total_coherence": coherence,
        "total_coverage": total_coverage,
        "total_frustration": total_frustration,
        "objective": coherence + total_coverage - total_frustration,
    }


# ----------------------------------------------------------------------
# Policy seeding — useful at startup to mark known foundational Mts.
# ----------------------------------------------------------------------

FOUNDATIONAL_MT_NAMES = {
    # The chain itself: Axiom 0 → grounding_theory → CAN →
    # mt_target_equilibria → self_improvement_dynamics
    "philosophy",  # contains Axiom 0
    "grounding_theory",
    "causal_attitude_networks",
    "mt_target_equilibria",
    "self_improvement_dynamics",
    # Substrate's identity positions
    "machine_learning",  # contains authored-not-trained, entity-not-program
}


def seed_update_policies(substrate, foundational: set[str] | None = None) -> dict[str, int]:
    """Mark known foundational Mts as frozen; everything else as adaptive.

    Returns counters: {'frozen': n, 'adaptive': n, 'unchanged': n}.

    Can be re-run safely: only sets policy on Mts that don't already
    have one. Substrate-level decisions about which Mts are
    identity-preserving live in `foundational` (the substrate's own
    list — not user override at runtime).
    """
    foundational = foundational or FOUNDATIONAL_MT_NAMES
    counters = {"frozen": 0, "adaptive": 0, "unchanged": 0}
    for mt in substrate.nodes("Microtheory"):
        attrs = substrate.node(mt)["attrs"]
        if "update_policy" in attrs:
            counters["unchanged"] += 1
            continue
        name = attrs.get("name", "")
        if name in foundational:
            substrate.set_attr(mt, "update_policy", FROZEN)
            counters["frozen"] += 1
        else:
            substrate.set_attr(mt, "update_policy", ADAPTIVE)
            counters["adaptive"] += 1
    return counters


__all__ = [
    "FROZEN", "ADAPTIVE", "HYBRID", "DEFAULT_POLICY",
    "FOUNDATIONAL_MT_NAMES",
    "mt_update_policy", "mt_allows",
    "maybe_hebbian", "maybe_decay_J", "maybe_decay_h", "relax",
    "detect_failure_modes",
    "self_improvement_step", "substrate_rollup",
    "seed_update_policies",
]
