#!/usr/bin/env python3
"""Read-only readiness audit for the Thoughtexperiment five-policy panel."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evaluation/reports/thoughtexperiment_blinded_panel_readiness_v1_20261002.json"
FIXTURES = {
    "shape_axis": ROOT / "evaluation/reports/thoughtexperiment_graph_authored_correction_rank_v1_raw_20261001.json",
    "recurrence": ROOT / "evaluation/reports/thoughtexperiment_recurrence_candidate_admission_v1_raw_20261002.json",
    "navigation": ROOT / "evaluation/reports/thoughtexperiment_navigation_outcome_rank_integration_v1_raw_20261002.json",
    "control_kind": ROOT / "evaluation/reports/thoughtexperiment_control_kind_classification_repair_v1_raw_20261002.json",
}
PANEL_ORDERS = ROOT / "evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_orders_20261002.json"
PANEL_SCORES = ROOT / "evaluation/reports/thoughtexperiment_blinded_proposal_utility_v1_scores_20261002.json"
REQUIRED_COSTS = ("enumeration_ns", "ranking_ns", "branch_ns", "scoring_ns", "adoption_verification_ns")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_rows(name: str, doc: dict) -> tuple[list[dict], int, bool, set[str]]:
    """Return candidate outcome rows, worker count, and recorded source stability."""
    workers = doc.get("workers", [])
    if name == "shape_axis":
        episodes = [episode for worker in workers for episode in worker.get("episodes", [])]
        rows = [trial for episode in episodes for trial in episode.get("tried", [])]
        labels = {label for episode in episodes for label in episode.get("candidate_order_used", [])}
        stable = bool(workers) and all(w.get("source_stable") for w in workers)
        return rows, len({w.get("pid") for w in workers}), stable, labels
    if name == "recurrence":
        rows = [row for worker in workers for row in worker.get("candidate_outcomes", [])]
    elif name == "navigation":
        rows = []
        for worker in workers:
            scores = worker.get("heldout_scores_all_candidates", {})
            rows.extend({"label": label, "heldout_pass": bool(score.get("utility", 0) >= 1.0)}
                        for label, score in scores.items())
    elif name == "control_kind":
        rows = [row for worker in workers for row in worker.get("candidate_outcomes", [])]
    else:
        raise ValueError(name)
    stable = bool(workers) and all(w.get("source_stable") for w in workers)
    if name == "navigation":
        stable = bool(doc.get("source_before")) and doc.get("source_before") == doc.get("source_after")
    return rows, len(workers), stable, set()


def heldout_pass(row: dict, family: str) -> bool:
    if family == "shape_axis":
        return bool(row.get("converges"))
    if family == "recurrence":
        return bool(row.get("heldout", {}).get("pass"))
    if family == "navigation":
        return bool(row.get("heldout_pass"))
    return bool(row.get("heldout")) and all(case.get("pass") for case in row["heldout"])


def main() -> int:
    families = {}
    for name, path in FIXTURES.items():
        doc = json.loads(path.read_text())
        rows, workers, stable, enumerated_labels = fixture_rows(name, doc)
        by_label: dict[str, list[bool]] = {}
        for row in rows:
            label = str(row.get("label", ""))
            if label:
                by_label.setdefault(label, []).append(heldout_pass(row, name))
        # Shape-axis's prior harness records results only for candidates it rehearsed
        # before finding a repair; retain the full enumerated set separately.
        labels = sorted(set(by_label) | enumerated_labels)
        families[name] = {
            "raw": str(path.relative_to(ROOT)), "sha256": digest(path),
            "workers": workers, "source_stability_recorded": stable,
            "distinct_candidates": len(labels), "candidate_labels": labels,
            "utility_measured_candidates": len(by_label),
            "utility_measurement_coverage": f"{len(by_label)}/{len(labels)}",
            "unscored_candidates": sorted(set(labels) - set(by_label)),
            "has_successful_candidate": any(any(v) for v in by_label.values()),
            "has_unsuccessful_candidate": any(not all(v) for v in by_label.values()),
            "utility_measured_for_every_candidate": len(by_label) >= len(labels),
            "candidate_level_cost_fields_present": all(
                all(field in row for field in REQUIRED_COSTS) for row in rows) if rows else False,
        }
    prereg = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_PREREG_20261002.md"
    amendment = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_1_AMENDMENT_20261002.md"
    checks = {
        "four_fixture_artifacts_present": all(path.is_file() for path in FIXTURES.values()),
        "four_families_with_three_candidates_and_mixed_utility": all(
            row["distinct_candidates"] >= 3 and row["has_successful_candidate"]
            and row["has_unsuccessful_candidate"] for row in families.values()),
        "four_fresh_workers_per_family": all(row["workers"] >= 4 for row in families.values()),
        "source_stability_recorded_for_all_families": all(row["source_stability_recorded"] for row in families.values()),
        "common_candidate_level_cost_capture": all(
            row["candidate_level_cost_fields_present"] for row in families.values()),
        "v1_protocol_and_amendment_present": prereg.is_file() and amendment.is_file(),
        "heldout_orders_and_scores_absent_before_capture": not any(p.exists() for p in (PANEL_ORDERS, PANEL_SCORES)),
    }
    report = {
        "schema": "ThoughtexperimentBlindedPanelReadinessV1",
        "scope": "read-only admission audit; does not execute or authorize the confirmatory panel",
        "families": families,
        "required_cost_fields": list(REQUIRED_COSTS),
        "checks": checks,
        "passed": sum(checks.values()), "total": len(checks),
        "panel_capture_ready": all(checks.values()),
        "next_gate": "build a source-locked common runner, scorer, and analyzer; then capture only after all readiness gates pass",
    }
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if OUT.exists():
        if OUT.read_text() != serialized:
            raise SystemExit(f"readiness evidence changed; preserve existing capture and write a new version")
    else:
        OUT.write_text(serialized)
    print(json.dumps({"passed": report["passed"], "total": report["total"],
                      "panel_capture_ready": report["panel_capture_ready"],
                      "capture_matches_current_inputs": OUT.read_text() == serialized,
                      "report": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
