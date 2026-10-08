#!/usr/bin/env python3
"""Independent checks for specialized direct graph-read probe outcomes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/reports/substrate_specialized_term_access_trace_probe_v1_20260926.json"
OUTPUT = ROOT / "evaluation/reports/substrate_specialized_term_access_trace_probe_v1_analysis_20260926.json"


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    checks = {"twenty_four_cases_present": len(raw["cells"]) == 24,
              "runner_checks_all_pass": all(raw["checks"].values()),
              "expected_events_present": True,
              "trace_disabled_arms_empty": True,
              "trace_has_no_drop_or_static_mismatch": True,
              "paired_runs_settled": True,
              "enigma_successful_values_and_full_attr_path": True,
              "track_identity_result_and_configured_attr_reads": True,
              "net_forward_successful_two_step_output": True,
              "future_manifold_projection_result_and_reads": True,
              "future_manifold_selection_result_and_reads": True,
              "motor_compose_result_and_reads": True,
              "transform_decode_result_and_reads": True,
              "dim_infer_result_and_generator_reads": True,
              "gen_infer_matrix_and_codebook_reads": True,
              "gen_infer_scaled_matrix_and_search_count": True,
              "gen_infer_minted_generator_redecodes": True,
              "gen_infer_value_noise_rejected": True,
              "indexed_and_fallback_nodes_where_confirmed": True,
              "provenance_source_hashes_current": True,
              "native_extension_hash_current": hashlib.sha256(
                  (ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()
                  == raw["provenance"]["native_extension_sha256"]}
    counts = {}
    for cell in raw["cells"]:
        observed = {row[1] for row in cell["traced"]["events"]}
        checks["expected_events_present"] &= set(cell["expected_event_kinds"]) <= observed
        checks["trace_disabled_arms_empty"] &= cell["plain"]["event_count"] == 0
        checks["trace_has_no_drop_or_static_mismatch"] &= (
            cell["traced"]["dropped"] == 0 and not cell["traced"]["static_mismatches"])
        checks["paired_runs_settled"] &= (cell["outcome_match"] and cell["traced"]["status"] == "fixed_point"
                                           and cell["traced"]["terminal_progress"] == 0)
        counts[cell["case"]] = {kind: sum(e[5] for e in cell["traced"]["events"] if e[1] == kind)
                                for kind in observed}
        if cell["case"].startswith("nodes_where"):
            checks["indexed_and_fallback_nodes_where_confirmed"] &= (
                cell["plain"]["index_active"] == cell["traced"]["index_active"]
                == (cell["case"] == "nodes_where_indexed"))
        if cell["case"] in ("enigma_crib", "enigma_bombe"):
            checks["enigma_successful_values_and_full_attr_path"] &= (
                cell["plain"]["specialized_result"] is True
                and cell["traced"]["specialized_result"] is True
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 9)
        elif cell["case"] == "enigma_bombe_witness":
            checks["enigma_successful_values_and_full_attr_path"] &= (
                isinstance(cell["plain"]["specialized_result"], str)
                and isinstance(cell["traced"]["specialized_result"], str)
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 9)
        elif cell["case"] == "track_identity":
            checks["track_identity_result_and_configured_attr_reads"] &= (
                cell["plain"]["specialized_result"] == {"matched": [["#0", "#1"]], "births": [], "deaths": []}
                and cell["traced"]["specialized_result"] == cell["plain"]["specialized_result"]
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") == 6
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_type_read") >= 2)
        elif cell["case"] == "net_forward":
            checks["net_forward_successful_two_step_output"] &= (
                cell["plain"]["specialized_result"] == [15.0]
                and cell["traced"]["specialized_result"] == [15.0]
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_edge_read") >= 6
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") > 10)
        elif cell["case"] == "future_manifold_projection":
            checks["future_manifold_projection_result_and_reads"] &= (
                cell["plain"]["specialized_result"] == 1.0
                and cell["traced"]["specialized_result"] == 1.0
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 5)
        elif cell["case"] == "future_manifold_selection":
            checks["future_manifold_selection_result_and_reads"] &= (
                cell["plain"]["specialized_result"] == cell["plain"]["expected_specialized_result"]
                and cell["traced"]["specialized_result"] == cell["traced"]["expected_specialized_result"]
                and cell["plain"]["specialized_result"] == cell["traced"]["specialized_result"]
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_type_read") >= 1
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 8)
        elif cell["case"] == "motor_compose":
            checks["motor_compose_result_and_reads"] &= (
                isinstance(cell["plain"]["specialized_result"], bool)
                and cell["plain"]["specialized_result"] == cell["traced"]["specialized_result"]
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_edge_read") >= 1
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 1)
        elif cell["case"] == "transform_decode":
            checks["transform_decode_result_and_reads"] &= (
                cell["plain"]["specialized_result"] == 1.0
                and cell["traced"]["specialized_result"] == 1.0
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_type_read") >= 1
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 1)
        elif cell["case"] == "dim_infer":
            checks["dim_infer_result_and_generator_reads"] &= (
                cell["plain"]["specialized_result"] == 1.0
                and cell["traced"]["specialized_result"] == 1.0
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_type_read") >= 2
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 7)
        elif cell["case"] == "gen_infer":
            checks["gen_infer_matrix_and_codebook_reads"] &= (
                cell["plain"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
                and cell["traced"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
                and cell["plain"]["specialized_result"]["checked"] == 6560
                and cell["traced"]["specialized_result"]["checked"] == 6560
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_type_read") >= 1
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 4)
        elif cell["case"] == "gen_infer_scaled":
            checks["gen_infer_scaled_matrix_and_search_count"] &= (
                cell["plain"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
                and cell["traced"]["specialized_result"]["matrix"] == [2, 1, 1, 1]
                and cell["plain"]["specialized_result"]["checked"] == 83520
                and cell["traced"]["specialized_result"]["checked"] == 83520
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_type_read") >= 1
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 4)
        elif cell["case"] == "gen_infer_redecode":
            result = {"matrix": [2, 1, 1, 1], "checked": 6560,
                      "decoded": True, "generator": "linear_from_gen_infer"}
            checks["gen_infer_minted_generator_redecodes"] &= (
                cell["plain"]["specialized_result"] == result
                and cell["traced"]["specialized_result"] == result
                # The rule-owned GenInfer read is traced; mint and re-decode
                # are direct API operations in this fixture, outside rule tracing.
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_type_read") >= 1
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 4)
        elif cell["case"] == "gen_infer_noise":
            result = {"matrix": [], "checked": 624, "explained": False}
            checks["gen_infer_value_noise_rejected"] &= (
                cell["plain"]["specialized_result"] == result
                and cell["traced"]["specialized_result"] == result
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_type_read") >= 1
                and sum(e[5] for e in cell["traced"]["events"] if e[1] == "term_attr_read") >= 4)
    for path, digest in raw["provenance"]["source_sha256"].items():
        checks["provenance_source_hashes_current"] &= hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    result = {"schema_version": 1, "source": str(SOURCE.relative_to(ROOT)),
              "checks": checks, "all_checks_pass": all(checks.values()), "case_event_counts": counts,
              "claim_boundary": "Direct instrumentation coverage probes only; no workload-prevalence or complete-footprint claim."}
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
