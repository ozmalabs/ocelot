#!/usr/bin/env python3
"""Source-locked paired follow-up for syntax-only repair proposal coverage."""
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_blind_structural_repair_proposal_coverage_v2.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_PROPOSAL_COVERAGE_V2_PREREG_20261005.md"
FIXTURE = ROOT / "evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json"
EDIT_OPS = ROOT / "domains/edit_ops.py"
BASELINE = ROOT / "evaluation/reports/blind_structural_repair_proposal_coverage_v1_analysis_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v2_lock_20261005.json"
OUT = ROOT / "evaluation/reports/blind_structural_repair_proposal_coverage_v2_20261005.json"

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def frozen():
    return {str(p.relative_to(ROOT)): sha(p) for p in
            (RUNNER, ANALYZER, PROTOCOL, FIXTURE, EDIT_OPS, BASELINE)}
def canonical(rule):
    semantic = dict(rule); semantic.pop("name", None); semantic.pop("active", None)
    return json.dumps(semantic, sort_keys=True, separators=(",", ":"))

def worker(index):
    from domains.edit_ops import enumerate_single_edit_candidates
    lock = json.loads(LOCK.read_text()); before = frozen()
    if before != lock["sources"]: raise RuntimeError("source lock mismatch before worker")
    cases = json.loads(FIXTURE.read_text())["cases"]; rows = []
    for case in cases:
        start = time.perf_counter_ns()
        proposals = enumerate_single_edit_candidates(case["faulted_rule"], max_candidates=lock["candidate_cap"])
        elapsed = time.perf_counter_ns() - start
        candidate_rules = [canonical(row["rule"]) for row in proposals]
        target = canonical(case["target_rule_sealed"])
        rows.append({"case_id": case["case_id"], "candidate_count": len(proposals),
                     "proposal_count_before_dedup": proposals[0]["proposal_count_before_dedup"] if proposals else 0,
                     "valid_count_before_dedup": proposals[0]["valid_count_before_dedup"] if proposals else 0,
                     "unique_count": proposals[0]["unique_count"] if proposals else 0,
                     "truncated": proposals[0]["truncated"] if proposals else False,
                     "operator_counts": {op: sum(row["operator"] == op for row in proposals)
                                         for op in sorted({row["operator"] for row in proposals})},
                     "target_in_pool": target in candidate_rules,
                     "target_match_count": candidate_rules.count(target),
                     "candidate_ids": [row["candidate_id"] for row in proposals],
                     "enumeration_wall_ns": elapsed})
    after = frozen()
    if after != lock["sources"]: raise RuntimeError("source drift during worker")
    return {"worker": index, "pid": os.getpid(), "sources_before": before,
            "sources_after": after, "cases": rows}

def main():
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists(): raise SystemExit("refusing to overwrite lock/capture")
        LOCK.write_text(json.dumps({"schema":"BlindStructuralRepairProposalCoverageV2Lock",
            "sources":frozen(),"workers":3,"case_count":len(json.loads(FIXTURE.read_text())["cases"]),
            "candidate_cap":256},indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT)); return 0
    if len(sys.argv)==3 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":"))); return 0
    if sys.argv[1:] != ["--run"]: raise SystemExit("usage: --lock | --run | --worker N")
    lock=json.loads(LOCK.read_text())
    if frozen()!=lock["sources"]: raise SystemExit("source lock mismatch")
    env=dict(os.environ); env["PYTHONPATH"]=str(ROOT); workers=[]
    for i in range(lock["workers"]):
        proc=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,
            text=True,capture_output=True,timeout=120)
        if proc.returncode: raise RuntimeError(f"worker {i} failed: {proc.stderr[-2000:]}")
        workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    if frozen()!=lock["sources"]: raise SystemExit("source drift during capture")
    OUT.write_text(json.dumps({"schema":"BlindStructuralRepairProposalCoverageV2",
        "lock_sha256":sha(LOCK),"host":platform.platform(),"workers":workers},indent=2,sort_keys=True)+"\n")
    print(OUT.relative_to(ROOT)); return 0

if __name__=="__main__": raise SystemExit(main())
