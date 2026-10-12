#!/usr/bin/env python3
"""Differential semantic gate for sorted GenInfer identity keys."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
WORKLOAD = ROOT / "evaluation/substrate_capability/geninfer_full_rank_sorted_join_scale_v2_3.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/GENINFER_FULL_RANK_SORTED_JOIN_KEY_SEMANTICS_V1_PREREG_20261006.md"
LOCK = ROOT / "evaluation/substrate_capability/geninfer_full_rank_sorted_join_key_semantics_v1_lock_20261006.json"
DEFAULT_OUT = ROOT / "evaluation/reports/geninfer_full_rank_sorted_join_key_semantics_v1_20261006.json"
SCENARIOS = ("mixed_numeric", "float_keys", "bool_int")
VARIANTS = ("nested", "sorted")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def workload_module():
    spec = importlib.util.spec_from_file_location("geninfer_sorted_join_workload_v2_3", WORKLOAD)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def frozen_inputs():
    paths = (RUNNER, WORKLOAD, PROTOCOL, ROOT / "runners/dsl/Cargo.toml",
             ROOT / "runners/dsl/Cargo.lock", ROOT / "runners/dsl/src/shape_decode.rs",
             ROOT / "runners/dsl/src/value.rs")
    return {str(path.relative_to(ROOT)): sha(path) for path in paths}


def case_worker(scenario: str, variant: str, overlay: Path) -> dict:
    module = workload_module()
    module.BASE = overlay
    original_rows = module.rows
    call_count = 0

    def typed_rows(points, dim, prefix, kind):
        nonlocal call_count
        rows = original_rows(points, dim, prefix, kind)
        if prefix not in ("train", "held") or call_count >= 4:
            return rows
        call_count += 1
        source_side = call_count % 2 == 1
        for index, row in enumerate(rows):
            if scenario == "mixed_numeric":
                row[1] = index if source_side else float(index)
            elif scenario == "float_keys":
                row[1] = float(index)
            elif scenario == "bool_int":
                row[0] = f"cell{index // 2}"
                row[1] = bool(index % 2) if source_side else int(index % 2)
        return rows

    module.rows = typed_rows
    case = {"id": f"key_semantics_{scenario}", "family": "key_semantics_v1",
            "dimension": 3, "kind": "positive", "matrix_case": "shear_cycle",
            "relation_count": 16, "relation_order": "independent_deterministic_shuffle",
            "replicate": 0}
    result = module.worker(variant, case, False)
    if not result["source_stable"]:
        raise RuntimeError(f"source drift in {scenario}/{variant}")
    phases = {}
    for phase in ("train", "heldout"):
        item = result["phases"][phase]
        phases[phase] = {"status": item.get("status"), "covered_by": item.get("covered_by"),
                         "receipts": item.get("receipts")}
    return {"scenario": scenario, "variant": variant, "native_sha256": result["native_sha256"],
            "source_stable": result["source_stable"], "phases": phases}


def assert_parity(rows: list[dict]) -> None:
    for scenario in SCENARIOS:
        pair = {row["variant"]: row for row in rows if row["scenario"] == scenario}
        if set(pair) != set(VARIANTS):
            raise RuntimeError(f"incomplete arm pair: {scenario}")
        for phase in ("train", "heldout"):
            baseline = pair["nested"]["phases"][phase]
            candidate = pair["sorted"]["phases"][phase]
            if baseline != candidate:
                raise RuntimeError(f"semantic mismatch: {scenario}/{phase}: {baseline!r} != {candidate!r}")
            if baseline["status"] != "recognized_transformed" or not baseline["receipts"]:
                raise RuntimeError(f"fixture did not exercise expected solver path: {scenario}/{phase}")


def main() -> int:
    args = sys.argv[1:]
    if len(args) == 4 and args[0] == "--prepare":
        _, overlay, baseline, candidate = args
        module = workload_module()
        module.BASE = Path(overlay)
        module.prepare(baseline, candidate)
        return 0
    if len(args) == 4 and args[0] == "--worker":
        _, overlay, scenario, variant = args
        print(json.dumps(case_worker(scenario, variant, Path(overlay)), sort_keys=True))
        return 0
    if len(args) == 3 and args[0] == "--capture":
        _, overlay_arg, out_arg = args
        overlay, out = Path(overlay_arg), Path(out_arg).resolve()
        locked = json.loads(LOCK.read_text())
        if locked["inputs"] != frozen_inputs():
            raise SystemExit("frozen input hash mismatch")
        env = dict(os.environ)
        env.setdefault("OZMA_NO_LLM", "1")
        env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
        rows = []
        for scenario in SCENARIOS:
            for variant in VARIANTS:
                proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(overlay),
                                       scenario, variant], cwd=ROOT, env=env, text=True,
                                      capture_output=True, check=True, timeout=300)
                rows.append(json.loads(proc.stdout))
        assert_parity(rows)
        payload = {"schema": "GenInferFullRankSortedJoinKeySemanticsV1",
                   "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "host": platform.platform(), "lock_sha256": sha(LOCK),
                   "inputs": frozen_inputs(), "scenarios": list(SCENARIOS),
                   "expected_features": {"nested": ["geninfer_full_rank_matrix_solver"],
                                         "sorted": ["geninfer_full_rank_matrix_solver",
                                                    "geninfer_full_rank_sorted_identity_join"]},
                   "worker_count": len(rows), "parity_gate": "passed", "workers": rows}
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"output": str(out.relative_to(ROOT)), "worker_count": len(rows),
                          "parity_gate": "passed"}, sort_keys=True))
        return 0
    raise SystemExit("usage: --prepare OVERLAY_DIR BASELINE_SO SORTED_SO | --worker OVERLAY_DIR SCENARIO VARIANT | --capture OVERLAY_DIR OUTPUT_JSON")


if __name__ == "__main__":
    raise SystemExit(main())
