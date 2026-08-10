"""The agent designs its next filter from its own graph-resident theory.

No LLM reasoning, no Python heuristics — just graph walks over what the
substrate's self_improvement_dynamics Mt names as important. The Mt
declares 6 failure modes; the substrate compares them to its installed
filter manifest; the gap surfaces the next capability to build.

Output: a filter specification, including which Mt-named failure mode
it targets, the samples + scope + kernel + gate + action shape. I
mechanically implement what the substrate specifies.

Pattern from memory [[ozma_agent_designs_runtime]]:
    agent reasons from its science to a primitive its language LACKS;
    a MECHANICAL compiler emits the code. The agent decides WHAT,
    the implementor emits HOW.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native

from domains.self_improvement_dynamics import install_self_improvement_dynamics_seed


# Manifest of filters currently installed in the substrate (declared
# statically — would live as FilterSpec graph nodes if the registry
# were itself graph-resident, but this is sufficient for now). Each
# entry describes one filter that's already running per loop step.
INSTALLED_FILTERS = [
    {
        "name": "insight_delta_F",
        "quantity": "frustration",
        "scope": "per_mt",
        "max_order": 1,
        "targets_failure_mode": None,  # detects basin transitions, not
                                        # failure modes per se
    },
    {
        "name": "anticipation_d2_F",
        "quantity": "frustration",
        "scope": "per_mt",
        "max_order": 2,
        "targets_failure_mode": None,
    },
    {
        "name": "identity_formation_delta_h_id",
        "quantity": "identity_field",
        "scope": "per_concept",
        "max_order": 1,
        "targets_failure_mode": None,
    },
    {
        # Added by the 1st design step + implementor pass (eece6ba).
        "name": "redundancy_detection",
        "quantity": "marginal_vector",
        "scope": "cross_mt",
        "kernel": "cosine_similarity",
        "targets_failure_mode": "fail_mode_redundant_Mt",
    },
    {
        # Added by the 2nd design step + implementor pass (5a2bcb7).
        "name": "conflict_detection",
        "quantity": "marginal_vector",
        "scope": "cross_mt_per_node",
        "kernel": "opposite_sign_with_magnitude",
        "targets_failure_mode": "fail_mode_conflicting_reflexes",
    },
    {
        # Added by the 3rd design step + implementor pass (dc18ef6).
        "name": "frozen_should_adapt",
        "quantity": "distance_to_target_magnitude",
        "scope": "per_mt",
        "kernel": "streak_over_threshold",
        "targets_failure_mode": "fail_mode_frozen_should_adapt",
    },
    {
        # Added by the 4th design step + implementor pass (b2120e6).
        "name": "drifted_past_anchor",
        "quantity": "distance_to_target_magnitude",
        "scope": "per_mt",
        "kernel": "streak_over_threshold",
        "targets_failure_mode": "fail_mode_drifted_past_anchor",
    },
    {
        # Added by the 5th design step + implementor pass (4737cf9).
        "name": "frustration_signal",
        "quantity": "previous_frustration",
        "scope": "per_mt",
        "kernel": "streak_over_threshold",
        "targets_failure_mode": "fail_mode_frustrated_Mt",
    },
    {
        # Added by the 6th design step + implementor pass (this commit).
        # Closes the failure-mode coverage: all 6 failure modes named
        # by self_improvement_dynamics now have a filter.
        "name": "sparseness_signal",
        "quantity": "coverage",
        "scope": "per_mt",
        "kernel": "streak_under_threshold",  # inverse direction
        "targets_failure_mode": "fail_mode_sparse_Mt",
    },
]


def fresh_substrate():
    s = _native.Substrate()
    for src_t in ("Microtheory", "Concept", "Rule", "DerivationRule"):
        for tgt_t in ("Microtheory", "Concept", "Rule", "DerivationRule"):
            for et in ("has_concept", "has_rule", "in_category",
                       "genlMt", "refers_to"):
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "design",
                })
    return s


def list_failure_modes(substrate, sid_mt):
    """Walk Mt → has_concept → Concept where category == 'failure_modes'.
    Each is something the substrate's own theory says it should detect."""
    modes = []
    for c in substrate.neighbours(sid_mt, "has_concept"):
        attrs = substrate.node(c)["attrs"]
        if attrs.get("category") == "failure_modes":
            modes.append({
                "name": str(attrs.get("name", "")),
                "definition": str(attrs.get("definition", "")),
            })
    return modes


def classify_failure_mode(mode_definition: str) -> dict:
    """Mechanical pattern-match on the Mt's own definition text. The
    definition tells us what the failure mode references — single-Mt
    quantity (uses existing primitive), or cross-Mt (needs new
    capability). Pattern keys are drawn directly from the substrate's
    self-theory."""
    d = mode_definition.lower()
    if "two" in d and ("mts" in d or "different mts" in d):
        return {"scope": "cross_mt", "complexity": "new_primitive"}
    if "sustained" in d or "persistent" in d or "for many cycles" in d:
        return {"scope": "per_mt_streak", "complexity": "existing_primitive"}
    if "drifted" in d or "displacement" in d:
        return {"scope": "per_mt_distance", "complexity": "existing_primitive"}
    return {"scope": "per_mt", "complexity": "existing_primitive"}


def find_gaps(failure_modes, installed):
    """A failure mode is a gap iff no installed filter targets it.
    Currently NONE of the installed filters target a failure mode —
    so every named failure mode is a gap."""
    targeted = {f["targets_failure_mode"] for f in installed
                if f["targets_failure_mode"] is not None}
    gaps = []
    for mode in failure_modes:
        if mode["name"] not in targeted:
            classification = classify_failure_mode(mode["definition"])
            gaps.append({**mode, **classification})
    return gaps


def specify_filter_for_gap(gap: dict) -> dict:
    """The agent's design output: a structural specification of the
    filter that detects this failure mode. The implementor reads this
    + writes the code."""
    name = gap["name"]
    scope = gap["scope"]
    if scope == "cross_mt":
        return {
            "filter_name": f"detect_{name}",
            "scope": "cross_mt",
            "samples_per_step": [
                "marginal_vector(mt_a)",  # σ over mt_a's concepts
                "marginal_vector(mt_b)",  # σ over mt_b's concepts
            ],
            "kernel": "cosine_similarity_over_shared_concepts",
            "gate": (
                "similarity > 0.9 sustained for N steps + shared_concept_count > 2"
                if "redundant" in name
                else "h_drive_a · h_drive_b < 0 on shared node"
            ),
            "action": (
                "emit RedundancyEvent linking the two Mts; trigger merge correction"
                if "redundant" in name
                else "emit ConflictEvent flagging the shared node"
            ),
            "new_primitive_needed": (
                "cross_mt_sample helper — extend windowed_filter to "
                "accept samples from multiple Mts simultaneously"
            ),
        }
    elif scope == "per_mt_streak":
        return {
            "filter_name": f"detect_{name}",
            "scope": "per_mt",
            "samples_per_step": ["mt audit quantity"],
            "kernel": "identity (read raw value)",
            "gate": "value > threshold AND streak_count >= K",
            "action": f"emit {name.replace('fail_mode_', '').title()}Event",
            "new_primitive_needed": "none — existing streak pattern from identity_formation",
        }
    else:
        return {
            "filter_name": f"detect_{name}",
            "scope": scope,
            "samples_per_step": ["TBD"],
            "kernel": "TBD",
            "gate": "TBD",
            "action": "TBD",
        }


def main():
    s = fresh_substrate()
    sid_mt = install_self_improvement_dynamics_seed(s)

    failure_modes = list_failure_modes(s, sid_mt)
    gaps = find_gaps(failure_modes, INSTALLED_FILTERS)

    print("=" * 72)
    print("AGENT INTROSPECTION — design next filter from own theory")
    print("=" * 72)
    print()
    print(f"Self_improvement_dynamics Mt declares {len(failure_modes)} failure modes:")
    print()
    for m in failure_modes:
        print(f"  · {m['name']}")
        print(f"      {m['definition'][:90]}")
    print()
    print(f"Currently installed filters ({len(INSTALLED_FILTERS)}):")
    for f in INSTALLED_FILTERS:
        target = f["targets_failure_mode"] or "(none — detects basin transitions)"
        print(f"  · {f['name']}: targets {target}")
    print()
    print(f"GAP: {len(gaps)} of {len(failure_modes)} failure modes are NOT filter-detected.")
    print()

    # Group by complexity — the substrate's principle 'build for capability'
    # says prefer the gap that adds the most reusable capability.
    new_primitive_gaps = [g for g in gaps if g["complexity"] == "new_primitive"]
    existing_primitive_gaps = [g for g in gaps if g["complexity"] == "existing_primitive"]

    print(f"  · {len(new_primitive_gaps)} require a NEW primitive (cross-Mt sampling)")
    print(f"  · {len(existing_primitive_gaps)} use the EXISTING WindowedFilter primitive")
    print()

    # The agent's choice. Two principles in play:
    #   [[ozma_build_for_capability]] → prefer capability-additive
    #                                   (new_primitive)
    #   [[ozma_capabilities_not_fixes]] → fix the lock-in, add the
    #                                     missing capability, never
    #                                     hack the symptom
    # Both push toward new_primitive. Pick from there.
    if not gaps:
        print("=" * 72)
        print("ALL FAILURE MODES COVERED")
        print("=" * 72)
        print()
        print("Every failure mode named by self_improvement_dynamics has a")
        print("filter that detects it. The substrate's own theory is FULLY")
        print("OPERATIONALISED in detection.")
        print()
        print("Next move requires either:")
        print("  · extend self_improvement_dynamics with new failure modes")
        print("    (the substrate's theory grows)")
        print("  · build CORRECTION operators that act on the detected")
        print("    events (split_Mt, merge_Mts, re_anchor, prune_Mt,")
        print("    β_reweight from the corrections category)")
        print("  · build new Mts whose own theories declare new failure")
        print("    modes (the substrate's coverage extends to new domains)")
        return

    if new_primitive_gaps:
        chosen = new_primitive_gaps[0]
        rationale = (
            "build for capability — cross-Mt sampling adds a new primitive "
            "that immediately enables 2+ filters (redundancy + conflict), "
            "and opens cross-correlation / multi-Mt-coupling cases beyond "
            "failure-mode detection"
        )
    else:
        chosen = existing_primitive_gaps[0]
        rationale = "use existing primitive; first single-Mt gap"

    spec = specify_filter_for_gap(chosen)
    print("=" * 72)
    print("AGENT DESIGN — chosen gap to fill next")
    print("=" * 72)
    print()
    print(f"Failure mode targeted: {chosen['name']}")
    print(f"Definition from Mt:    {chosen['definition']}")
    print(f"Rationale:             {rationale}")
    print()
    print("Specification:")
    for k, v in spec.items():
        if isinstance(v, list):
            print(f"  {k}:")
            for item in v:
                print(f"    - {item}")
        else:
            print(f"  {k}: {v}")
    print()


if __name__ == "__main__":
    main()
