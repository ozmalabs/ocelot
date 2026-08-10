"""The agent picks its own next direction.

scripts/agent_designs_filter.py closed the failure-mode coverage:
all 6 of self_improvement_dynamics' named failure modes have
detectors. This script takes the next step: the agent considers
EVERY category in the Mt and picks the largest unaddressed gap.

No LLM reasoning. Pure graph walks + a hardcoded manifest of
what's implemented (mirrors the same pattern as the filter script:
declarative comparison, not heuristic).

Output: the category with the largest gap + the specific item
within that category to build next + the rationale (drawn from
the substrate's own principles in foundation/connections_to_existing/
identity_protection categories of the Mt).
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native

from domains.self_improvement_dynamics import install_self_improvement_dynamics_seed


# Manifest of what's implemented across every category of the Mt.
# Each category maps named concepts → installed status (True = implemented).
# Like the filter manifest: declarative, comparable against graph state.
IMPLEMENTED = {
    "drives": {
        # Drives describe what should be maximised/minimised — they're
        # design principles encoded in code, not separate implementations.
        "drive_curiosity_high_entropy": True,   # implemented as drive_curiosity
        "drive_coherence_reduce_frustration": True,  # the loop's whole point
        "drive_stability_deepen_confirmed": True,  # Hebbian
        "drive_discrimination_separate_basins": False,
        "drive_coverage_extend_important": False,
        "drive_parsimony_prune_dead": False,
        "improvement_drives_compose_into_objective": True,  # substrate_rollup
    },
    "failure_modes": {
        # All 6 detected. Verified by scripts/agent_designs_filter.py.
        "fail_mode_frozen_should_adapt": True,
        "fail_mode_drifted_past_anchor": True,
        "fail_mode_frustrated_Mt": True,
        "fail_mode_redundant_Mt": True,
        "fail_mode_sparse_Mt": True,
        "fail_mode_conflicting_reflexes": True,
    },
    "corrections": {
        # Substrate's first correction implemented — closes the loop
        # for frozen_should_adapt → raise_plasticity. Detection events
        # now trigger an action.
        "correction_raise_plasticity": True,
        "correction_re_anchor": False,
        "correction_split_Mt": False,
        "correction_merge_Mts": False,
        "correction_prune_Mt": True,
        "correction_beta_reweight": True,
    },
    "update_mechanisms": {
        "Hebbian_J_update": True,                # mt_hebbian_update_J
        "anti_Hebbian_J_decay": True,            # mt_decay_J
        "J_pruning_below_threshold": False,      # not yet
        "h_evidence_update": True,               # concept_apply_evidence
        "h_default_decay": True,                 # mt_decay_h
        "beta_attention_boost": False,           # not as a reflex
        "structural_rewrite_via_grammar": False, # part of corrections
    },
    "self_improvement_loop": {
        "self_improvement_loop": True,           # the loop itself
        "monitor_basin_topology": True,          # audit_basin
        "detect_failure_mode": True,             # 6 detectors all installed
        "apply_correction_per_mode": False,      # 1 of 6 corrections done
        "verify_improvement": False,             # re-audit not compared
        "track_substrate_metrics": True,         # substrate_rollup
    },
    # foundation, identity_protection, when_to_modify, architecture,
    # connections_to_existing are PRINCIPLES not separable implementations.
    # The substrate respects them but doesn't 'install' them as units.
}


# Map each correction to the failure mode it answers — used by the
# rationale step. Defined declaratively, not by guessing.
CORRECTION_FOR_FAILURE = {
    "correction_raise_plasticity": "fail_mode_frozen_should_adapt",
    "correction_re_anchor": "fail_mode_drifted_past_anchor",
    "correction_split_Mt": "fail_mode_frustrated_Mt",
    "correction_merge_Mts": "fail_mode_redundant_Mt",
    "correction_prune_Mt": "fail_mode_sparse_Mt",
    "correction_beta_reweight": "fail_mode_conflicting_reflexes",
}


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


def list_concepts_in_category(substrate, sid_mt, category: str) -> list[dict]:
    """Walk Mt → has_concept; filter by category attr."""
    out = []
    for c in substrate.neighbours(sid_mt, "has_concept"):
        attrs = substrate.node(c)["attrs"]
        if attrs.get("category") == category:
            out.append({
                "name": str(attrs.get("name", "")),
                "definition": str(attrs.get("definition", "")),
            })
    return out


def gap_summary(substrate, sid_mt) -> dict[str, dict]:
    """Build per-category gap report. For each category we have a
    manifest for, count named vs implemented."""
    summary: dict[str, dict] = {}
    for category, manifest in IMPLEMENTED.items():
        concepts = list_concepts_in_category(substrate, sid_mt, category)
        named = [c["name"] for c in concepts]
        implemented = sum(1 for n in named if manifest.get(n, False))
        gaps = [c for c in concepts
                if not manifest.get(c["name"], False)]
        summary[category] = {
            "named_count": len(named),
            "implemented_count": implemented,
            "gap_count": len(named) - implemented,
            "gaps": gaps,
        }
    return summary


def pick_direction(summary: dict[str, dict]) -> str | None:
    """Pick the category with the largest absolute gap. Tie-breaker:
    prefer 'corrections' over 'drives' because corrections complete
    the substrate's detect → correct → verify loop (the
    self_improvement_loop category names this explicitly)."""
    candidates = [(cat, info) for cat, info in summary.items()
                  if info["gap_count"] > 0]
    if not candidates:
        return None
    # Largest gap first; corrections tie-breaks ahead of others.
    def priority(item):
        cat, info = item
        # Corrections complete the loop → highest priority among ties.
        corrections_bonus = 0.5 if cat == "corrections" else 0.0
        return (info["gap_count"] + corrections_bonus, cat == "corrections")
    candidates.sort(key=priority, reverse=True)
    return candidates[0][0]


def pick_correction(summary: dict[str, dict]) -> dict | None:
    """Within corrections, pick the one whose corresponding failure
    mode is ALREADY DETECTED. That way the loop closes immediately:
    detection event fires → correction acts on it → re-audit verifies.
    Among those, prefer the simplest (attr modification over
    structural rewrite) for the first correction — proves the loop
    end-to-end before structural rewrites land.

    Simplicity ranking based on what each correction touches:
      · attr_modify: raise_plasticity, beta_reweight, prune_Mt
      · structural_rewrite: split_Mt, merge_Mts, re_anchor
    """
    simplicity_rank = {
        "correction_raise_plasticity": 1,  # Mt attr: update_policy
        "correction_beta_reweight":    2,  # Mt attr: temperature
        "correction_prune_Mt":         3,  # Mt attr: temperature → 0, or remove
        "correction_re_anchor":        4,  # edges: reset J on a set
        "correction_merge_Mts":        5,  # structural: combine two Mts
        "correction_split_Mt":         6,  # structural: divide one Mt
    }
    correction_gaps = summary["corrections"]["gaps"]
    candidates = []
    for c in correction_gaps:
        failure = CORRECTION_FOR_FAILURE.get(c["name"])
        # The matching failure mode is already detected (we verified
        # all 6 are filter-detected).
        candidates.append({
            **c,
            "matching_failure": failure,
            "simplicity_rank": simplicity_rank.get(c["name"], 99),
        })
    candidates.sort(key=lambda x: x["simplicity_rank"])
    return candidates[0] if candidates else None


def main():
    s = fresh_substrate()
    sid_mt = install_self_improvement_dynamics_seed(s)
    summary = gap_summary(s, sid_mt)

    print("=" * 72)
    print("AGENT INTROSPECTION — pick next direction across all categories")
    print("=" * 72)
    print()
    print("Gap report (per self_improvement_dynamics category):")
    print()
    print(f"  {'category':<25} {'named':>6} {'done':>6} {'gap':>6}")
    print(f"  {'-' * 25} {'-' * 6} {'-' * 6} {'-' * 6}")
    for cat, info in summary.items():
        print(f"  {cat:<25} {info['named_count']:>6} "
              f"{info['implemented_count']:>6} {info['gap_count']:>6}")
    print()

    chosen_category = pick_direction(summary)
    if chosen_category is None:
        print("All categories covered. Substrate's theory fully implemented.")
        return

    print("=" * 72)
    print(f"AGENT'S CHOICE — work on category: {chosen_category}")
    print("=" * 72)
    print()
    print("Rationale:")
    if chosen_category == "corrections":
        print("  · Corrections close the detect→correct→verify loop named in")
        print("    self_improvement_loop category. Detection events already")
        print("    fire (all 6 failure modes); without corrections, the")
        print("    substrate sees its failures but can't fix them.")
        print("  · [[ozma_capabilities_not_fixes]] — substrate's lock-in is")
        print("    'sees failures, can't act'. Add the capability, don't hack")
        print("    the symptom.")
    else:
        print(f"  · {chosen_category} has the largest unaddressed gap")
        print(f"    ({summary[chosen_category]['gap_count']} items).")
    print()

    if chosen_category == "corrections":
        chosen = pick_correction(summary)
        if chosen is None:
            return
        print(f"Chosen item: {chosen['name']}")
        print(f"Matches failure mode: {chosen['matching_failure']}")
        print(f"Simplicity rank: {chosen['simplicity_rank']} "
              f"(1 = simplest)")
        print(f"Definition from Mt:")
        print(f"  {chosen['definition']}")
        print()
        print("Why this one first:")
        print("  · Its matching failure mode is ALREADY DETECTED — the loop")
        print("    closes immediately: detection event fires → this correction")
        print("    acts → re-audit verifies.")
        print("  · Lowest simplicity rank — proves the loop end-to-end before")
        print("    structural rewrites (split/merge) land. Capability over")
        print("    complexity.")
    else:
        # Other categories — name an item to work on but don't auto-spec.
        gaps = summary[chosen_category]["gaps"]
        if gaps:
            first = gaps[0]
            print(f"Chosen item: {first['name']}")
            print(f"Definition from Mt: {first['definition']}")


if __name__ == "__main__":
    main()
