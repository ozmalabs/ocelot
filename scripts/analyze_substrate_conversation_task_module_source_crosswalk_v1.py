#!/usr/bin/env python3
"""Join observed conversation-task module calls to the Python source inventory."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/conversation_task_module_activation_v1_1_20260928.json"
INVENTORY = ROOT / "evaluation/substrate_capability/python_source_coverage_audit_v1_1_20260928.json"
OUT = ROOT / "evaluation/reports/conversation_task_module_source_crosswalk_v1_20260928.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(RAW.read_text())
    inventory = json.loads(INVENTORY.read_text())
    files = {row["module"]: row for row in inventory["files"]}
    runs = raw["runs"]
    modules_by_condition: dict[str, set[str]] = {}
    for run in runs:
        condition = run["condition"]
        modules_by_condition.setdefault(condition, set()).update(
            run["module_activation"]["module_call_counts"])

    all_modules = sorted(set().union(*modules_by_condition.values()))
    rows = []
    for module in all_modules:
        source = files.get(module)
        rows.append({
            "module": module,
            "source_path": source["path"] if source else None,
            "source_sha256": source["sha256"] if source else None,
            "capability_rows": source["capability_rows"] if source else [],
            "conditions": sorted(name for name, modules in modules_by_condition.items()
                                  if module in modules),
        })

    checks = {
        "capture_complete": raw.get("capture_status") == "complete",
        "ten_workers": len(runs) == 10,
        "worker_inputs_stable": all(run.get("module_activation_inputs_stable") is True
                                     for run in runs),
        "five_conditions_two_replicates_each": (
            len(modules_by_condition) == 5
            and all(sum(run["condition"] == name for run in runs) == 2
                    for name in modules_by_condition)),
        "all_activated_modules_in_inventory": all(module in files for module in all_modules),
    }
    result = {
        "schema_version": 1,
        "run_id": "conversation-task-module-source-crosswalk-v1-20260928",
        "input_sha256": {"capture": sha(RAW), "source_inventory": sha(INVENTORY)},
        "scope": "Post-hoc join of profiled Python domain calls to the v1.1 per-file source inventory and capability-map links.",
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "inventory_source_file_count": inventory["source_file_count"],
        "inventory_capability_linked_file_count": inventory["capability_linked_file_count"],
        "activated_module_count": len(all_modules),
        "activated_modules_with_capability_map_links": sum(bool(row["capability_rows"])
                                                            for row in rows),
        "modules_by_condition": {name: len(modules) for name, modules
                                 in sorted(modules_by_condition.items())},
        "module_rows": rows,
        "claim_boundary": (
            "This crosswalk describes Python modules with at least one observed call in the five authored conversation tasks. "
            "A capability-map link is source-navigation coverage, not proof of causal necessity or complete capability coverage. "
            "Unobserved modules may serve other tasks; native Rust execution is outside this trace."
        ),
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "checks", "all_checks_pass", "inventory_source_file_count",
        "inventory_capability_linked_file_count", "activated_module_count",
        "activated_modules_with_capability_map_links", "modules_by_condition")}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit("source crosswalk integrity check failed")


if __name__ == "__main__":
    main()
