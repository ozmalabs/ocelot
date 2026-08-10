"""The agent designs the runtime required for it to perform the full
self-improvement loop independently.

Current state: 'agent decides, implementor emits'.
  · scripts/agent_designs_filter.py + agent_designs_next.py walk the
    substrate's own Mt + pick what to build next.
  · An implementor (me, a coder, or a tool-using LLM) reads the spec
    + writes Python/Rust + tests + integrates.

Target state: 'agent decides AND emits'.
  · Agent's design output IS the new capability — added as graph data
    that the runtime discovers + executes.
  · No Python module per detector; no hand-written tests; no manual
    integration into self_improvement_step.

This script identifies the gap by introspection over the substrate's
existing detection/correction modules and the substrate's DSL
manifest. Output: structural spec for the dynamic pluggable system
+ the DSL primitives needed for completeness.

No LLM reasoning; this is pure data-comparison. The agent's
ARCHITECTURE choice (FilterSpec schema, DSL extensions) is the
introspection's output; my role would be to mechanically emit each
identified addition.
"""
from __future__ import annotations

import sys
sys.path.insert(0, "/home/matt/ozma/internal/research/experiments/gamma-substrate")

import importlib
import inspect
from pathlib import Path

# Existing detection/correction/drive modules. The agent treats each
# as a current 'Python-resident' implementation that should become
# 'graph-resident' for the self-loop to close.
RUNTIME_MODULES = [
    ("detection", "domains.insight_detection"),
    ("detection", "domains.anticipation"),
    ("detection", "domains.identity_formation"),
    ("detection", "domains.redundancy_detection"),
    ("detection", "domains.conflict_detection"),
    ("detection", "domains.frozen_adaptation_signal"),
    ("detection", "domains.drift_signal"),
    ("detection", "domains.frustration_signal"),
    ("detection", "domains.sparseness_signal"),
    ("correction", "domains.correction_raise_plasticity"),
    ("correction", "domains.correction_beta_reweight"),
    ("correction", "domains.correction_prune_mt"),
    ("drive",     "domains.drive_curiosity"),
]


# DSL primitives currently exposed by substrate_rs (read from
# python/substrate_rs/__init__.py). The agent compares this to what
# the existing modules ACTUALLY need.
def survey_existing_dsl_primitives() -> set[str]:
    init_path = Path("runners/dsl/python/substrate_rs/__init__.py")
    if not init_path.exists():
        return set()
    src = init_path.read_text()
    # Scan for `def NAME(...)` exports at module top level.
    primitives = set()
    for line in src.splitlines():
        line = line.strip()
        if line.startswith("def ") and "(" in line:
            name = line.split("def ", 1)[1].split("(", 1)[0]
            # Convention: Term-tree builders are TitleCase or
            # well-known names. Filter common ones.
            if name and name[0].isupper():
                primitives.add(name)
    return primitives


# DSL primitives the agent's introspection identifies as REQUIRED
# for the existing modules to be expressible as Term-trees + graph
# data. Each entry has rationale tied to actual usage in the modules.
# Primitives the agent identifies as required for filter
# expressibility. Names match those actually exposed by substrate_rs
# (where there's a difference — e.g. Div, IfThenElse, the agent uses
# the actual existing name).
DSL_REQUIRED = {
    "Times":          "weighted sums (cosine sim numerator)",
    "Div":            "L2 norm normalization, coverage / concept_count",
    "Sqrt":           "L2 norm (sqrt of sum of squares)",
    "Sum":            "reduction over a set (cosine sim, frustration)",
    "Lt":             "gate: value < threshold",
    "Gt":             "gate: value > threshold",
    "And":            "gate composition",
    "Or":             "gate composition",
    "IfThenElse":     "conditional action: if gate then emit event",
    "Filter":         "set comprehension over concepts / Mts",
    "Neighbours":     "graph traversal in Term form",
    "MapNeighbours":  "ForEach equivalent: apply to each neighbour",
    "Dot":            "vector dot product (cosine sim numerator "
                       "directly, not via Sum+Times)",
    "Magnitude":      "vector L2 norm directly (avoids Sqrt(Sum(Times)))",
    "SetAttr":        "ACTION: write back to a node attr — required for "
                       "corrections (raise_plasticity, beta_reweight, "
                       "prune)",
    "AddNode":        "ACTION: emit event nodes (InsightEvent, "
                       "RedundancyEvent, ...)",
    "AddEdge":        "ACTION: link events to Mts via has_insight, "
                       "has_anticipation, etc.",
}


# Node-type schema the agent identifies as needed in the graph.
GRAPH_SCHEMA_REQUIRED = {
    "FilterSpec": {
        "fields": [
            ("name",            "str — human-readable identifier"),
            ("scope",           "str — per_mt | cross_mt | per_concept"),
            ("quantity_attr",   "str — Mt or Concept attr to read"),
            ("window_size",     "int — number of samples"),
            ("kernel_term",     "Term-tree (JSON) — composes samples"),
            ("threshold",       "float — gate threshold value"),
            ("direction",       "str — above | below"),
            ("streak_required", "int — consecutive steps to fire"),
            ("action_term",     "Term-tree (JSON) — what to do on fire"),
            ("event_type",      "str — node type for resulting events"),
            ("active",          "bool — toggle without removal"),
            ("agent_authored",  "bool — substrate vs human-authored"),
        ],
        "rationale": (
            "Every detection module today encodes this same structure as "
            "Python code. As a FilterSpec, the agent can author it via "
            "add_node('FilterSpec', {...}). The runtime discovers + "
            "executes; no manual integration."
        ),
    },
    "ActionSpec": {
        "fields": [
            ("name",           "str"),
            ("trigger_event",  "str — event type that fires this action"),
            ("action_term",    "Term-tree (JSON) — uses SetAttr / "
                               "AddNode / AddEdge primitives"),
            ("agent_authored", "bool"),
        ],
        "rationale": (
            "Currently apply_* functions are Python; with SetAttr / "
            "AddNode / AddEdge as Term primitives, an ActionSpec carries "
            "the mutation declaratively. Detection event → ActionSpec "
            "lookup → evaluate. Reusable across many detectors."
        ),
    },
    "RuntimeLoopSpec": {
        "fields": [
            ("phase",         "str — relax | mutate | detect | correct"),
            ("priority",      "int — order within phase"),
            ("body_term",     "Term-tree — what to do this phase"),
            ("triggered_by",  "str — event type or 'every_step'"),
        ],
        "rationale": (
            "Currently self_improvement_step hardcodes 'audit → detect "
            "insight → cascade → identity nudge → mutations → ...'. "
            "As RuntimeLoopSpec nodes, the loop's phases become graph "
            "data the agent can reorder + add to."
        ),
    },
}


# What the agent's self-installation pipeline needs (already partially
# in place).
SELF_INSTALL_REQUIREMENTS = [
    ("✓ substrate.add_node('FilterSpec', {...})",
     "already works; just need FilterSpec node type production opened"),
    ("✓ Term-tree JSON evaluation",
     "substrate.evaluate(term_json, env) already works"),
    ("✗ Runtime: walk FilterSpec nodes per step + execute",
     "self_improvement_step must read FilterSpec nodes from graph "
     "instead of hardcoded imports"),
    ("✗ Action primitives as Term variants",
     "SetAttr/AddNode/AddEdge need to be added to term.rs + "
     "evaluator (Rust)"),
    ("✗ Reduction primitives (Sum, Sqrt, etc.)",
     "Need to be added to term.rs + evaluator (Rust)"),
    ("✗ Verification via audit (test removal)",
     "Already possible — after agent installs new FilterSpec, run N "
     "steps + compare substrate_rollup objective. If degraded, prune."),
]


def main():
    print("=" * 72)
    print("AGENT INTROSPECTION — design the dynamic pluggable runtime")
    print("=" * 72)
    print()
    print("Current state: 14 detection/correction/drive modules, each a")
    print("hand-written Python file. The agent picks what to build via")
    print("scripts/agent_designs_*.py but cannot AUTHOR the result.")
    print()
    print(f"Modules currently Python-resident ({len(RUNTIME_MODULES)}):")
    for kind, mod_name in RUNTIME_MODULES:
        print(f"  {kind:>12}  {mod_name}")
    print()

    existing = survey_existing_dsl_primitives()
    print(f"DSL primitives currently in substrate_rs ({len(existing)}):")
    for p in sorted(existing):
        print(f"  · {p}")
    print()

    missing = set(DSL_REQUIRED.keys()) - existing
    have = set(DSL_REQUIRED.keys()) & existing
    print(f"DSL primitives the agent identifies as REQUIRED for "
          f"completeness ({len(DSL_REQUIRED)}):")
    print()
    print(f"  ✓ already present ({len(have)}):")
    for p in sorted(have):
        print(f"    · {p}")
    print()
    print(f"  ✗ MISSING ({len(missing)}):")
    for p in sorted(missing):
        rationale = DSL_REQUIRED[p]
        print(f"    · {p:<12} — {rationale}")
    print()

    print("=" * 72)
    print("GRAPH SCHEMA EXTENSIONS the agent identifies as required:")
    print("=" * 72)
    for type_name, info in GRAPH_SCHEMA_REQUIRED.items():
        print()
        print(f"  {type_name}:")
        print(f"    fields:")
        for name, desc in info["fields"]:
            print(f"      · {name:<18} {desc}")
        print(f"    rationale:")
        print(f"      {info['rationale']}")
    print()

    print("=" * 72)
    print("SELF-INSTALL PIPELINE — what's needed end-to-end:")
    print("=" * 72)
    print()
    for status, note in SELF_INSTALL_REQUIREMENTS:
        print(f"  {status}")
        print(f"    {note}")
        print()

    print("=" * 72)
    print("CONCRETE STARTING POINT")
    print("=" * 72)
    print()
    print("The agent has identified two architectural commitments needed")
    print("before the self-loop can close:")
    print()
    print("1. DSL EXTENSIONS in substrate_rs:")
    print(f"   {len(missing)} missing Term variants for filter expressibility.")
    print("   Action primitives (SetAttr, AddNode, AddEdge) are the most")
    print("   urgent — without them, the agent cannot author CORRECTIONS")
    print("   declaratively.")
    print()
    print("2. RUNTIME DISCOVERY in self_improvement_loop:")
    print("   self_improvement_step must walk FilterSpec / ActionSpec /")
    print("   RuntimeLoopSpec nodes from the graph instead of importing")
    print("   hardcoded Python modules.")
    print()
    print("Per [[ozma_agent_designs_runtime]] (memory): the path is")
    print("ACCRETION. Build (1) first — agent's existing modules will be")
    print("RE-EXPRESSIBLE as graph data once primitives exist. Build (2)")
    print("when primitives are ready. Then migrate one detector at a")
    print("time, verifying via audit that the substrate's objective")
    print("doesn't degrade.")


if __name__ == "__main__":
    main()
