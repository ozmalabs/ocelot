#!/usr/bin/env python3
"""Source-locked proposal-coverage probe for syntax-only rule repair candidates."""
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_blind_structural_repair_proposal_coverage_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_V1_PREREG_20261005.md"
FIXTURE = ROOT / "evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json"
EDIT_OPS = ROOT / "domains/edit_ops.py"
LOCK = ROOT / "evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/blind_structural_repair_proposal_coverage_v1_20261005.json"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def frozen():
    return {str(p.relative_to(ROOT)): sha(p)
            for p in (RUNNER, ANALYZER, PROTOCOL, FIXTURE, EDIT_OPS)}


def canonical(rule):
    semantic = dict(rule)
    semantic.pop("name", None)
    semantic.pop("active", None)
    return json.dumps(semantic, sort_keys=True, separators=(",", ":"))


def worker(index):
    from domains.edit_ops import enumerate_single_edit_candidates

    locked = json.loads(LOCK.read_text())
    before = frozen()
    if before != locked["sources"]:
        raise RuntimeError("source lock mismatch before worker")
    fixture = json.loads(FIXTURE.read_text())
    rows = []
    for case in fixture["cases"]:
        # Deliberately hand only the faulty live rule to the candidate
        # generator. The target/oracle stays in this runner's evaluation layer.
        t0 = time.perf_counter_ns()
        candidates = enumerate_single_edit_candidates(case["faulted_rule"])
        elapsed = time.perf_counter_ns() - t0
        target = canonical(case["target_rule_sealed"])
        candidate_canonicals = [canonical(row["rule"]) for row in candidates]
        rows.append({
            "case_id": case["case_id"],
            "candidate_count": len(candidates),
            "proposal_count_before_dedup": candidates[0]["proposal_count_before_dedup"] if candidates else 0,
            "valid_count_before_dedup": candidates[0]["valid_count_before_dedup"] if candidates else 0,
            "unique_count": candidates[0]["unique_count"] if candidates else 0,
            "truncated": candidates[0]["truncated"] if candidates else False,
            "operator_counts": {op: sum(row["operator"] == op for row in candidates)
                                for op in sorted({row["operator"] for row in candidates})},
            "target_in_pool": target in candidate_canonicals,
            "target_match_count": candidate_canonicals.count(target),
            "enumeration_wall_ns": elapsed,
            "candidate_ids": [row["candidate_id"] for row in candidates],
        })
    after = frozen()
    if after != locked["sources"]:
        raise RuntimeError("source lock mismatch after worker")
    return {"worker": index, "pid": os.getpid(), "sources_before": before,
            "sources_after": after, "cases": rows}


def main():
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists():
            raise SystemExit("refusing to overwrite existing lock/capture")
        LOCK.write_text(json.dumps({"schema": "BlindStructuralRepairProposalCoverageV1Lock",
                                   "sources": frozen(), "workers": 3,
                                   "case_count": len(json.loads(FIXTURE.read_text())["cases"]),
                                   "candidate_cap": 256}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, separators=(",", ":")))
        return 0
    if sys.argv[1:] != ["--run"]:
        raise SystemExit("usage: --lock | --run | --worker N")
    lock = json.loads(LOCK.read_text())
    if frozen() != lock["sources"]:
        raise SystemExit("source lock mismatch")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT)
    workers = []
    for index in range(lock["workers"]):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(index)],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
        if proc.returncode:
            raise RuntimeError(f"worker {index} failed: {proc.stderr[-2000:]}")
        workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    if frozen() != lock["sources"]:
        raise SystemExit("source drift during capture")
    OUT.write_text(json.dumps({"schema": "BlindStructuralRepairProposalCoverageV1",
                               "lock_sha256": sha(LOCK), "host": platform.platform(),
                               "workers": workers}, indent=2, sort_keys=True) + "\n")
    print(OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
