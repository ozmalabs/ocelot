#!/usr/bin/env python3
"""Generate guarded, graph-native reusable process sequence learning rules."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Eq, Exists, Gt, L, Lte, Lt, MapList, N, Not, OFFLINE_AREA,
    PRepairVerify, Plus, StringConcat, T, V, Vec, policy_on, productions, rule,
)

SEED_ID = "library_learning"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def verified_shared_sequence_rule():
    # Process algebra's native sequence encoding preserves each step's own
    # native representation.  Only exact repeated, successful traces compete.
    # Wrap each mapped process in a one-member sequence. The native process
    # parser flattens nested sequences in order while keeping each params
    # value as one process, including matrix and delta process shapes.
    sequence = Vec(
        L("seq"),
        MapList(A("t1", "trace"), "step", Vec(L("seq"), A("step", "params"))),
    )
    old_cost = Plus(Count(A("t1", "trace")), Count(A("t2", "trace")))
    # Stored definition is one reference per primitive step; each use pays
    # one reference, one decoder and one exception record.
    library_cost = Plus(Count(A("t1", "trace")), L(7))
    equivalent = PRepairVerify(
        sequence,
        Vec(A("t1", "initial_state"), A("t2", "initial_state")),
        Vec(A("t1", "goal"), A("t2", "goal")),
    )
    already = Exists(N("agent", "has_process_library_chunk"), "old",
                     Eq(A("old", "source_trace"), A("t1", "trace")))
    return rule(
        "ll_learn_verified_shared_sequence", OFFLINE_AREA, 35,
        "Learn a repeated solved trace only when native sequence execution verifies both source tasks and the full definition/reference/decode/exception cost is lower. Preserve source traces and failed tasks.",
        [["agent", "has_library_learning_policy", "pol"],
         ["agent", "has_sleep_stage_receipt", "receipt"],
         ["agent", "has_process_domain", "d"],
         ["agent", "has_solve_task", "t1"], ["t1", "about_domain", "d"],
         ["agent", "has_solve_task", "t2"], ["t2", "about_domain", "d"]],
        And(
            policy_on(), Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("receipt", "stage"), L("library")),
            Eq(A("receipt", "status"), L("deferred")),
            Lte(Count(N("agent", "has_solve_task")), A("pol", "max_tasks")),
            Eq(A("t1", "status"), L("solved")),
            Eq(A("t2", "status"), L("solved")), Lt(V("t1"), V("t2")),
            Eq(A("t1", "trace"), A("t2", "trace")),
            Gt(Count(A("t1", "trace")), L(7)),
            Lte(Count(A("t1", "trace")), A("pol", "max_trace_steps")),
            Eq(A("d", "name"), A("t1", "domain")),
            Not(already),
            Gt(old_cost, library_cost),
            Eq(equivalent, L(True)),
        ),
        [["add_node", "chunk", "ProcessLibraryChunk", {
            "status": "verified", "kind": "process_sequence",
            "domain": T(A("d", "name")), "source_trace": T(A("t1", "trace")),
            "equivalence_witness": "native_process_repair_verify_on_both_source_tasks",
            "source_count": 2, "definition_cost": T(Count(A("t1", "trace"))),
            "reference_cost": 2, "decoder_cost": 1, "exception_cost": 1,
            "dispatch_cost": 1, "retrieval_cost": 1, "validation_cost": 1,
            "inline_cost": T(old_cost), "library_cost": T(library_cost),
            "cost_savings": T({"type": "Minus", "a": old_cost, "b": library_cost}),
            "model_epoch": T(A("d", "model_epoch")),
            "probe_epoch": T(A("d", "probe_epoch")),
            "provenance": "verified_successful_process_traces",
        }],
         ["add_node", "schema", "ProcessSchema", {
            "kind": T(A("d", "kind")), "domain": T(A("d", "name")),
            "domain_kind": T(A("d", "kind")),
            "name": T(StringConcat(L("library:"), A("t1", "name"))),
            "params": T(sequence), "cost": 1.0, "status": "active",
            "provenance": "library_learned", "invented": 1,
            "effect_evaluation": "exact:native_sequence_verified_on_sources",
            "verification_receipt": "native_process_repair_verify_on_both_source_tasks",
            "source_epoch": T(A("d", "source_epoch")),
            "model_epoch": T(A("d", "model_epoch")),
            "frame_epoch": T(A("d", "frame_epoch")),
            "probe_epoch": T(A("d", "probe_epoch")),
        }],
         ["add_edge", "agent", "has_process_library_chunk", "chunk", {}],
         ["add_edge", "agent", "has_process_schema", "schema", {}],
         ["add_edge", "d", "has_held_process", "schema", {}],
         ["set_attr", "chunk", "rewritten_trace", T(Vec(V("schema")))],
         ["add_edge", "chunk", "has_library_process", "schema", {}],
         ["add_edge", "chunk", "has_source_task", "t1", {}],
         ["add_edge", "chunk", "has_source_task", "t2", {}],
         ["add_edge", "chunk", "based_on_sleep_stage", "receipt", {}],
         ["set_attr", "t1", "compressed_trace", T(Vec(V("schema")))],
         ["set_attr", "t1", "compression_witness", T(V("chunk"))],
         ["set_attr", "t2", "compressed_trace", T(Vec(V("schema")))],
         ["set_attr", "t2", "compression_witness", T(V("chunk"))],
         ["set_attr", "receipt", "status", "completed"],
         ["set_attr", "receipt", "completion_reason", "verified_compression_created"]],
        batch=False,
    )


def close_empty_library_stage_rule():
    receipt_chunk = Exists(
        N("agent", "has_process_library_chunk"), "chunk",
        Exists(N("chunk", "based_on_sleep_stage"), "stage_receipt",
               Eq(V("stage_receipt"), V("receipt"))),
    )
    return rule(
        "ll_close_empty_library_stage", OFFLINE_AREA, 36,
        "Finish the bounded library sleep stage with an explicit no-compression outcome when its preceding candidate rule found no verified cost-positive trace sequence.",
        [["agent", "has_library_learning_policy", "pol"],
         ["agent", "has_sleep_stage_receipt", "receipt"]],
        And(policy_on(), Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("receipt", "stage"), L("library")),
            Eq(A("receipt", "status"), L("deferred")),
            Not(receipt_chunk)),
        [["set_attr", "receipt", "status", "completed"],
         ["set_attr", "receipt", "completion_reason", "no_eligible_cost_positive_sequence_within_bound"]],
    )


def build_seed():
    return {
        "id": SEED_ID, "version": "1.0.0", "depends_on": ["process_solving", "sleep_regime"],
        "self_load_only": True, "area": OFFLINE_AREA,
        "description": "Learn cost-positive reusable process sequences only from repeated solved native traces; retain the original task traces and all failed evidence.",
        "microtheory": {"name": SEED_ID,
                        "description": "Compress verified repeated process traces into reusable native sequence schemas."},
        "nodes": [{"local_id": 0, "type": "LibraryLearningPolicy", "attrs": {
            "name": "core_library_learning_policy", "enabled": 0.0,
            "max_sources": 2.0, "max_tasks": 8.0, "max_trace_steps": 32.0,
        }}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_library_learning_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, [
            ("Agent", "has_library_learning_policy", "LibraryLearningPolicy"),
            ("Agent", "has_process_library_chunk", "ProcessLibraryChunk"),
            ("ProcessLibraryChunk", "has_library_process", "ProcessSchema"),
            ("ProcessLibraryChunk", "has_source_task", "SolveTask"),
            ("ProcessLibraryChunk", "based_on_sleep_stage", "SleepStageReceipt"),
        ]),
        "rules": [verified_shared_sequence_rule(), close_empty_library_stage_rule()],
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
