#!/usr/bin/env python3
"""Independent checks for the full seeded GenInfer/mint measurement."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/reports/substrate_genmint_measurement_20260926.json"
OUTPUT = ROOT / "evaluation/reports/substrate_genmint_measurement_analysis_20260926.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    checks = {
        "all_six_registered_gates_pass": all(raw["verdict"].values())
        and len(raw["verdict"]) == 6
        and raw["overturn_bounded_to_linear_class"],
        "experiment_runtime_recorded": (
            isinstance(raw.get("runtime_seconds"), (int, float))
            and math.isfinite(raw["runtime_seconds"])
            and raw["runtime_seconds"] > 0),
        "three_distinct_generators_recovered": all(
            row["correct"] and row["status"] == "recognized_transformed"
            and row["quanta"] == 0 for row in raw["H_discovery"].values())
        and {tuple(row["lingens"][0]) for row in raw["H_discovery"].values()}
        == {(1, 0, 1, 1), (1, 1, 0, 1), (2, 1, 1, 1)},
        "six_member_orbit_compresses": raw["H_compression"] == {
            "K": 6, "quanta_without": 6, "quanta_with": 0,
            "generators": [[1, 0, 1, 1]], "recognized": 6,
            "mdl_without": 24, "mdl_with": 12, "ratio": 2.0},
        "four_hundred_seeded_value_noise_cases_do_not_mint": (
            raw["H_floor"]["n"] == 400
            and raw["H_floor"]["non_paying_generators_minted"] == 0),
        "held_transform_does_not_spuriously_mint": (
            raw["H_occam"]["status"] == "recognized_transformed"
            and raw["H_occam"]["quanta"] == 0
            and raw["H_occam"]["lingens"] == []),
        "mint_changes_downstream_decode": (
            raw["H_downstream"]["new_member_status_ON"] == "recognized_transformed"
            and raw["H_downstream"]["new_member_status_OFF"] == "minted"
            and raw["H_downstream"]["generators_present"] == [[1, 0, 1, 1]]),
        "nonlinear_control_is_refused_by_linear_inducer": (
            raw["H_nonlinear"]["status"] == "minted"
            and raw["H_nonlinear"]["quanta"] == 1
            and raw["H_nonlinear"]["lingens"] == []),
        "engine_artifact_hash_current": digest(Path(
            raw["provenance"]["native_extension_path"]))
            == raw["provenance"]["native_extension_sha256"],
        "measurement_source_hashes_current": all(
            digest(ROOT / rel) == sha
            for rel, sha in raw["provenance"]["source_sha256"].items()),
    }
    result = {
        "schema_version": 1,
        "source": str(SOURCE.relative_to(ROOT)),
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "claim_boundary": (
            "End-to-end seeded, authored 2-D integer-linear GenInfer regime only. "
            "The 400 seeded colourings are a fixed finite control, not a proof "
            "of incompressibility, natural-task prevalence, or general learning "
            "tractability. The MDL count uses the runner's declared token model."),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
