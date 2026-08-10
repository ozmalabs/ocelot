"""The agent designs AND installs a new capability.

Step D of the 4-step plan. Earlier scripts (agent_designs_filter.py,
agent_designs_next.py) introspect the substrate's theory + pick what
to build, but they OUTPUT TEXT for an implementor to read. This
script CLOSES THE LOOP for streak-shape detectors: the agent's design
output is a direct call to install_filter_spec(...) — the new
detector exists in the graph immediately, the runtime executes it
next step.

The substrate now extends itself for capabilities that fit the
per_mt streak pattern. For other shapes (cross_mt with pair
quantities, per_concept, windowed gradient) the agent still needs
phase-2 support; this script handles the simplest case end-to-end
to prove the pattern.

Usage:
  python scripts/agent_self_installs.py

  This:
    1. Builds a fresh substrate
    2. Installs the foundational Mts
    3. Walks self_improvement_dynamics to find an uncovered
       failure mode
    4. If the failure mode fits the per_mt streak pattern, MINTS a
       FilterSpec node by calling install_filter_spec — the
       substrate is now self-extended.
    5. Runs a few loop steps to verify the new spec fires (if data
       triggers it)
    6. Reports what was installed

No editor involvement. No file generated. No test written. The
substrate has a new detector at runtime.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

from substrate_rs import _native

from domains.runtime_discovery import (
    install_filter_spec,
    list_filter_specs,
    run_all_filter_specs,
)
from domains.self_improvement_dynamics import install_self_improvement_dynamics_seed


# Failure-mode → declarative streak spec. The agent's introspection
# matches the Mt's definition text to this lookup. When a failure
# mode named here has no FilterSpec covering it yet, the script
# installs one. This is the explicit version of what scripts/
# agent_designs_next.py spec'd in text form.
FAILURE_TO_STREAK_SPEC = {
    "fail_mode_frustrated_Mt": {
        "name": "self_installed_frustrated_mt",
        "scope": "per_mt",
        "quantity_attr": "previous_frustration",
        "threshold": 1.0,
        "direction": "above",
        "streak_required": 10,
        "action_spec": {
            "op": "add_node",
            "type": "FrustratedMtEventFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "frustration": "$value",
                "streak": "$streak",
                "self_installed": True,
            },
        },
        "event_type": "FrustratedMtEventFromSpec",
    },
    "fail_mode_sparse_Mt": {
        "name": "self_installed_sparse_mt",
        "scope": "per_mt",
        "quantity_attr": "coverage",
        "threshold": 1.0,
        "direction": "below",
        "streak_required": 10,
        "action_spec": {
            "op": "add_node",
            "type": "SparseMtEventFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "coverage": "$value",
                "streak": "$streak",
                "self_installed": True,
            },
        },
        "event_type": "SparseMtEventFromSpec",
    },
    "fail_mode_frozen_should_adapt": {
        "name": "self_installed_distance_high",
        "scope": "per_mt",
        "quantity_attr": "distance_to_target_magnitude",
        "threshold": 1.0,
        "direction": "above",
        "streak_required": 10,
        "action_spec": {
            "op": "add_node",
            "type": "DistanceHighEventFromSpec",
            "attrs": {
                "mt_id": "$mt_id",
                "mt_name": "$mt_name",
                "distance": "$value",
                "streak": "$streak",
                "self_installed": True,
            },
        },
        "event_type": "DistanceHighEventFromSpec",
    },
}


def fresh_substrate():
    s = _native.Substrate()
    types = ("Microtheory", "Concept", "Rule", "DerivationRule",
             "FilterSpec",
             "FrustratedMtEventFromSpec", "SparseMtEventFromSpec",
             "DistanceHighEventFromSpec")
    edges = ("has_concept", "has_rule", "in_category", "genlMt",
             "refers_to")
    for src_t in types:
        for tgt_t in types:
            for et in edges:
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "self_install",
                })
    return s


def find_first_uninstalled_failure_mode(substrate, sid_mt) -> str | None:
    """Walk Mt → has_concept → category=failure_modes. Compare to
    already-installed FilterSpecs. Return first uncovered name that
    fits the streak pattern."""
    installed_names = {
        x["name"] for x in list_filter_specs(substrate)
    }
    for c in substrate.neighbours(sid_mt, "has_concept"):
        attrs = substrate.node(c)["attrs"]
        if attrs.get("category") != "failure_modes":
            continue
        name = str(attrs.get("name", ""))
        if name not in FAILURE_TO_STREAK_SPEC:
            continue  # not a shape this script can self-install
        # Check if THIS failure mode is already covered by an installed
        # spec. We compare by spec name (the lookup encodes it).
        spec_name = FAILURE_TO_STREAK_SPEC[name]["name"]
        if spec_name not in installed_names:
            return name
    return None


def main():
    s = fresh_substrate()
    sid_mt = install_self_improvement_dynamics_seed(s)

    print("=" * 72)
    print("AGENT SELF-INSTALL — design AND install in one step")
    print("=" * 72)
    print()

    target_failure = find_first_uninstalled_failure_mode(s, sid_mt)
    if target_failure is None:
        print("No uncovered streak-pattern failure modes. The agent has")
        print("already self-installed everything it can in this category.")
        return

    spec = FAILURE_TO_STREAK_SPEC[target_failure]
    print(f"Target failure mode: {target_failure}")
    print(f"Streak-pattern spec name: {spec['name']}")
    print(f"  scope:            {spec['scope']}")
    print(f"  quantity_attr:    {spec['quantity_attr']}")
    print(f"  threshold:        {spec['threshold']}")
    print(f"  direction:        {spec['direction']}")
    print(f"  streak_required:  {spec['streak_required']}")
    print()
    print("Installing as FilterSpec graph node...")
    node = install_filter_spec(
        s,
        name=spec["name"],
        scope=spec["scope"],
        quantity_attr=spec["quantity_attr"],
        threshold=spec["threshold"],
        direction=spec["direction"],
        streak_required=spec["streak_required"],
        action_spec=spec["action_spec"],
        event_type=spec["event_type"],
        agent_authored=True,
    )
    print(f"Installed. FilterSpec node id: {node.value if hasattr(node, 'value') else node}")
    print()

    installed_specs = list_filter_specs(s)
    print(f"All FilterSpecs now installed ({len(installed_specs)}):")
    for s_info in installed_specs:
        marker = " [self-installed]" if s_info["agent_authored"] else ""
        print(f"  · {s_info['name']:<32} {s_info['scope']:<12}{marker}")
    print()

    # Verify the runtime sees + can dispatch it. Without an Mt
    # carrying the relevant attr, no event fires — but the runtime
    # discovery step doesn't crash.
    events = run_all_filter_specs(s)
    print(f"run_all_filter_specs produced {len(events)} events "
          f"(0 expected — no Mts with relevant attrs at this point).")
    print()
    print("=" * 72)
    print("LOOP CLOSED — for streak-pattern detectors at least.")
    print("=" * 72)
    print()
    print("The agent's design output went DIRECTLY into the graph. No")
    print("implementor, no file edit, no test author. Next time")
    print("self_improvement_step runs on a substrate with matching")
    print("data, this FilterSpec fires automatically.")
    print()
    print("Re-run this script to install the next failure mode's")
    print("FilterSpec.")


if __name__ == "__main__":
    main()
