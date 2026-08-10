"""Author seeds/frames.json — the Frame / Microtheory register layer as a
graph-data MANIFEST the Rust seed loader installs at boot.

This is one-off migration tooling (like tools/capture_intent_rules.py): it EMITS
graph data to JSON, it does NOT run the agent. The Frame library is the SEED —
3 root Microtheories + their genlMt sub-Mts, the agent's operates_in scope, and
the inquiry Frames (each carrying evoked_by surface forms + binding_pattern +
core-element slots, realised_by -> its capability Concept, holds_in -> its Mt).
The agent BOOTS from this manifest; no Python constructs it at runtime.

Faithful to CuriousAgent's _seed_default_microtheories / _seed_default_frames
(the migrated source); the migrated structural tests (test_frames_seed_migrated)
are the parity check.
"""
from __future__ import annotations

import json
from pathlib import Path

SEED = Path(__file__).resolve().parent.parent / "seeds" / "frames.json"

# --- the Microtheory tree (root -> genlMt children) ----------------------
ROOTS = ("mathematics", "computer_science", "computer_architecture")
SUB_MTS = {
    "mathematics": ("elementary_arithmetic", "linear_algebra",
                    "finitely_presented_groups", "continuous_probability",
                    "sequence_inference", "equation_solving"),
    "computer_science": ("data_structures", "algorithms", "complexity_theory",
                         "systems_programming", "programming_languages",
                         "compilers", "concurrency"),
    "computer_architecture": ("instruction_set_architecture", "microarchitecture",
                              "memory_hierarchy", "vector_processing",
                              "concurrency_primitives", "performance_analysis"),
}

# --- the Frame library: (name, evoked_by, realised_by, holds_in, pattern, slots)
_F, _P, _B = "function_of_subject", "predicate_of_subject", "function_of_two_subjects"
FRAMES = [
    ("largest_prime_factor_inquiry", ["largest prime divisor", "largest prime factor"],
     "largest_prime_factor", "elementary_arithmetic", _F, ["of"]),
    ("prime_factors_inquiry", ["prime factors"], "prime_factors",
     "elementary_arithmetic", _F, ["of"]),
    ("divides_inquiry", ["divides"], "divides", "elementary_arithmetic", _F, ["of"]),
    ("determinant_inquiry", ["determinant"], "det", "linear_algebra", _F, ["of"]),
    ("rank_inquiry", ["rank"], "rank", "linear_algebra", _F, ["of"]),
    ("trace_inquiry", ["trace"], "trace", "linear_algebra", _F, ["of"]),
    ("order_inquiry", ["order"], "order", "finitely_presented_groups", _F, ["of"]),
    ("index_inquiry", ["index"], "index", "finitely_presented_groups", _F, ["of"]),
    ("expectation_inquiry", ["expectation"], "expectation",
     "continuous_probability", _F, ["of"]),
    ("variance_inquiry", ["variance"], "variance", "continuous_probability", _F, ["of"]),
    ("next_term_inquiry", ["next term"], "next_term", "sequence_inference", _F, ["of"]),
    ("wolfram_code_inquiry", ["Wolfram code"], "wolfram_code",
     "sequence_inference", _F, ["of"]),
    ("solution_inquiry", ["solution"], "solution", "equation_solving", _F, ["of"]),
    ("factorial_inquiry", ["factorial"], "factorial", "elementary_arithmetic", _F, ["of"]),
    ("totient_inquiry", ["Euler's totient", "Euler totient", "totient"], "totient",
     "elementary_arithmetic", _F, ["of"]),
    ("divisor_count_inquiry", ["number of divisors", "divisor count"], "divisor_count",
     "elementary_arithmetic", _F, ["of"]),
    ("divisor_sum_inquiry", ["sum of divisors", "divisor sum"], "divisor_sum",
     "elementary_arithmetic", _F, ["of"]),
    ("nth_fibonacci_inquiry", ["Fibonacci number", "nth Fibonacci"], "nth_fibonacci",
     "elementary_arithmetic", _F, ["of"]),
    # predicate-shaped
    ("primality_inquiry", ["prime number", "prime"], "prime",
     "elementary_arithmetic", _P, ["arg"]),
    ("evenness_inquiry", ["even"], "even", "elementary_arithmetic", _P, ["arg"]),
    ("oddness_inquiry", ["odd"], "odd", "elementary_arithmetic", _P, ["arg"]),
    ("perfect_square_inquiry", ["perfect square"], "is_perfect_square",
     "elementary_arithmetic", _P, ["arg"]),
    ("invertibility_inquiry", ["invertible"], "invertible", "linear_algebra", _P, ["arg"]),
    # binary-shaped
    ("gcd_inquiry", ["gcd", "greatest common divisor"], "gcd",
     "elementary_arithmetic", _B, ["a", "b"]),
    ("lcm_inquiry", ["lcm", "least common multiple"], "lcm",
     "elementary_arithmetic", _B, ["a", "b"]),
    ("sum_inquiry", ["sum", "plus"], "plus", "elementary_arithmetic", _B, ["left", "right"]),
    ("product_inquiry", ["product", "times"], "times", "elementary_arithmetic",
     _B, ["left", "right"]),
    # performance-analysis introspection
    ("op_mean_cost_inquiry", ["mean cost of", "average cost of"], "op_mean_cost",
     "performance_analysis", _F, ["of"]),
    ("op_count_inquiry", ["call count of", "number of calls to"], "op_count",
     "performance_analysis", _F, ["of"]),
    ("op_total_cost_inquiry", ["total cost of", "total time of"], "op_total_cost",
     "performance_analysis", _F, ["of"]),
]


def build() -> dict:
    nodes, edges = [], []
    nid = iter(range(7000, 99999))
    mt_id, concept_id = {}, {}

    def mt(name):
        if name not in mt_id:
            i = next(nid)
            mt_id[name] = i
            nodes.append({"local_id": i, "type": "Microtheory",
                          "attrs": {"name": name, "description": ""}})
        return mt_id[name]

    def concept(name):
        if name not in concept_id:
            i = next(nid)
            concept_id[name] = i
            nodes.append({"local_id": i, "type": "Concept", "attrs": {"name": name}})
            edges.append({"src": {"role": "agent_root"}, "type": "knows_concept",
                          "tgt": {"local": i}, "attrs": {}})
        return concept_id[name]

    # Microtheory tree + agent scope (operates_in the 3 roots).
    for root in ROOTS:
        rid = mt(root)
        edges.append({"src": {"role": "agent_root"}, "type": "operates_in",
                      "tgt": {"local": rid}, "attrs": {}})
        for sub in SUB_MTS[root]:
            sid = mt(sub)
            edges.append({"src": {"local": sid}, "type": "genlMt",
                          "tgt": {"local": rid}, "attrs": {}})

    # Frames + their realised_by Concept + holds_in scope.
    for name, evoked, realised, holds, pattern, slots in FRAMES:
        fi = next(nid)
        nodes.append({"local_id": fi, "type": "Frame", "attrs": {
            "name": name, "evoked_by": list(evoked),
            "binding_pattern": pattern,
            "core_elements": [{"slot": s} for s in slots]}})
        ci = concept(realised)
        edges.append({"src": {"local": fi}, "type": "realised_by",
                      "tgt": {"local": ci}, "attrs": {}})
        mi = mt(holds)
        edges.append({"src": {"local": fi}, "type": "holds_in",
                      "tgt": {"local": mi}, "attrs": {}})
        edges.append({"src": {"local": ci}, "type": "holds_in",
                      "tgt": {"local": mi}, "attrs": {}})

    # The autonomous impasse-resolution reflex (graph-resident): when the agent
    # has unresolved impasses, the master loop fires it to consult the teacher.
    ri = next(nid)
    nodes.append({"local_id": ri, "type": "Reflex", "attrs": {
        "name": "auto_resolve_impasse", "stimulus": "unresolved_impasses",
        "response": "resolve_impasse"}})
    edges.append({"src": {"role": "agent_root"}, "type": "has_reflex",
                  "tgt": {"local": ri}, "attrs": {}})

    return {"id": "frames", "version": "1.0.0", "depends_on": [],
            "description": "Frame / Microtheory register layer (FrameNet + CYC): "
            "inquiry Frames evoked_by surface forms, realised_by capability "
            "Concepts, scoped by holds_in Microtheories under genlMt inheritance.",
            "nodes": nodes, "edges": edges}


def main() -> None:
    manifest = build()
    SEED.write_text(json.dumps(manifest, indent=1))
    print(f"wrote {SEED}: {len(manifest['nodes'])} nodes, "
          f"{len(manifest['edges'])} edges, {len(FRAMES)} frames")


if __name__ == "__main__":
    main()
