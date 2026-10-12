#!/usr/bin/env python3
"""Fresh seeded confirmation of caller-notified CAN boundary propagation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_can_boundary_mutation_confirmatory_v2_20260925.json"
BASE_RUNNER = ROOT / "scripts/substrate_can_boundary_mutation_matrix_v1_1.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_CAN_BOUNDARY_MUTATION_CONFIRMATORY_PREREG_20260925.md"
SEEDS = (20260925, 8675309, 104729)
SIZES = (8, 16, 32)
MUTATIONS = (
    "insert_boundary_edge", "delete_boundary_edge", "replace_boundary_weight",
    "external_field_change", "identity_field_change", "node_birth",
    "node_deletion", "mixed_weight_and_field_change",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def seeded_model(n: int, mutation: str, seed: int):
    rng = random.Random(seed + 1009 * n)
    fields = [rng.choice((-0.2, -0.1, 0.1, 0.2)) for _ in range(n)]
    fields[0] = 0.0
    fields[3], fields[4] = 1.0, -0.1
    if mutation == "node_deletion":
        fields[3], fields[4] = 0.0, 1.0
    weights = {}
    for a in range(n - 1):
        if a == 3 and mutation == "insert_boundary_edge":
            continue
        w = 0.75 if a == 3 else rng.choice((-0.35, -0.25, -0.15, 0.15, 0.25, 0.35))
        weights[a, a + 1] = weights[a + 1, a] = w
    return fields, weights


def main():
    global CURRENT_SEED
    spec = importlib.util.spec_from_file_location("boundary_v1_1", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load the frozen v1.1 mechanism implementation")
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    base.initial_model = lambda n, mutation: seeded_model(n, mutation, CURRENT_SEED)

    import substrate_rs as sr
    from substrate.seed_loader import engine_rules_only
    from substrate_rs import _native
    from domains.engine_provenance import engine_provenance

    seed_path = ROOT / "seeds/can_native_reimplementation.json"
    seed_doc = json.loads(seed_path.read_text())
    manifest = dict(engine_rules_only(seed_doc))
    manifest["rules"] = [r for r in manifest.get("rules", [])
                         if r.get("name") == "can_native_update_3state"]
    if len(manifest["rules"]) != 1:
        raise RuntimeError("expected only the authored 3-state update rule")
    cases = []
    for seed in SEEDS:
        CURRENT_SEED = seed
        for n in SIZES:
            for mutation in MUTATIONS:
                negative = n == 8 and mutation in {
                    "insert_boundary_edge", "node_birth", "node_deletion"}
                case = base.run_case(sr, manifest, n, mutation, negative_control=negative)
                case["fixture_seed"] = seed
                cases.append(case)
    result = {
        "protocol": "CAN boundary mutation confirmatory v2",
        "protocol_path": str(PREREG.relative_to(ROOT)),
        "fixture_seeds": list(SEEDS), "sizes": list(SIZES), "mutations": list(MUTATIONS),
        "case_count": len(cases), "cases": cases,
        "all_event_cases_match_full_rescan_and_fixed_point": all(
            c["equal_terminal_projection"] and c["both_fixed_points"]
            and c["event"]["complete"] and c["full_rescan"]["complete"]
            and c["mutation_changed_state_or_active_projection"] for c in cases),
        "all_negative_controls_detect_staleness": all(
            c["negative_control"] is None or
            (c["negative_control"]["detects_stale"] and
             c["negative_control"]["residual_count"] > 0) for c in cases),
        "provenance": {
            "python": sys.version, "platform": platform.platform(),
            "runner_sha256": sha(Path(__file__)),
            "base_mechanism_runner_sha256": sha(BASE_RUNNER),
            "protocol_sha256": sha(PREREG),
            "seed_manifest_sha256": sha(seed_path),
            "native_extension_path": str(Path(_native.__file__).resolve()),
            "native_extension_sha256": sha(Path(_native.__file__).resolve()),
            "engine_provenance": engine_provenance(),
            "source_sha256": {name: sha(ROOT / "runners/dsl/src" / name)
                              for name in ("rewrite.rs", "substrate.rs", "term.rs")},
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT.relative_to(ROOT)),
        "case_count": len(cases),
        "all_event_cases_match_full_rescan_and_fixed_point": result["all_event_cases_match_full_rescan_and_fixed_point"],
        "all_negative_controls_detect_staleness": result["all_negative_controls_detect_staleness"],
        "cells": [{"seed": c["fixture_seed"], "n": c["n"], "mutation": c["case"],
                   "equal": c["equal_terminal_projection"], "fixed": c["both_fixed_points"],
                   "event_steps": c["event"]["steps"], "full_steps": c["full_rescan"]["steps"]}
                  for c in cases],
    }, indent=2))
    if not (result["all_event_cases_match_full_rescan_and_fixed_point"]
            and result["all_negative_controls_detect_staleness"]):
        raise SystemExit("confirmatory matrix failed its preregistered criteria")


if __name__ == "__main__":
    CURRENT_SEED = SEEDS[0]
    main()
