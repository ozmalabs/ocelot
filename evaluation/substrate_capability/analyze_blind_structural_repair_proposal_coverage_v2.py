#!/usr/bin/env python3
"""Independent validation and paired summary for proposal-coverage v2."""
import hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/"evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v2.py"
ANALYZER=Path(__file__).resolve()
PROTOCOL=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_PROPOSAL_COVERAGE_V2_PREREG_20261005.md"
FIXTURE=ROOT/"evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json"
EDIT_OPS=ROOT/"domains/edit_ops.py"
BASELINE=ROOT/"evaluation/reports/blind_structural_repair_proposal_coverage_v1_analysis_20261005.json"
LOCK=ROOT/"evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v2_lock_20261005.json"
CAPTURE=ROOT/"evaluation/reports/blind_structural_repair_proposal_coverage_v2_20261005.json"
OUT=ROOT/"evaluation/reports/blind_structural_repair_proposal_coverage_v2_analysis_20261005.json"

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def frozen():
    return {str(p.relative_to(ROOT)):sha(p) for p in
            (RUNNER,ANALYZER,PROTOCOL,FIXTURE,EDIT_OPS,BASELINE)}

def main():
    lock=json.loads(LOCK.read_text()); capture=json.loads(CAPTURE.read_text())
    baseline=json.loads(BASELINE.read_text()); errors=[]
    if frozen()!=lock["sources"]: errors.append("source hashes differ from lock")
    if capture.get("lock_sha256")!=sha(LOCK): errors.append("capture lock hash mismatch")
    workers=capture.get("workers",[])
    if len(workers)!=lock["workers"]: errors.append("worker count mismatch")
    aligned=[]
    for worker in workers:
        if worker.get("sources_before")!=lock["sources"] or worker.get("sources_after")!=lock["sources"]:
            errors.append(f"worker {worker.get('worker')} source mismatch")
        rows=worker.get("cases",[])
        if len(rows)!=lock["case_count"]: errors.append(f"worker {worker.get('worker')} case count mismatch")
        for row in rows:
            if row.get("truncated"): errors.append(f"truncated pool {row.get('case_id')}")
            if row.get("candidate_count")!=row.get("unique_count"): errors.append(f"unique accounting mismatch {row.get('case_id')}")
            if row.get("candidate_count")!=len(set(row.get("candidate_ids",[]))): errors.append(f"duplicate IDs {row.get('case_id')}")
        aligned.append({r.get("case_id"):r for r in rows})
    if aligned:
        for other in aligned[1:]:
            if set(other)!=set(aligned[0]): errors.append("worker case IDs differ"); continue
            for cid,first in aligned[0].items():
                second=other[cid]
                for key in ("candidate_count","proposal_count_before_dedup","valid_count_before_dedup",
                            "unique_count","truncated","operator_counts","target_in_pool",
                            "target_match_count","candidate_ids"):
                    if first.get(key)!=second.get(key): errors.append(f"worker mismatch {cid}.{key}"); break
    rows=list(aligned[0].values()) if aligned else []
    baseline_rows=baseline.get("summary",{}).get("cases_by_candidate_coverage",[])
    baseline_by_id={r["case_id"]:r for r in baseline_rows}
    if set(baseline_by_id)!={r["case_id"] for r in rows}: errors.append("v1/v2 case panel mismatch")
    hits=sum(bool(r.get("target_in_pool")) for r in rows)
    paired=[]
    for row in rows:
        old=baseline_by_id.get(row["case_id"],{})
        paired.append({"case_id":row["case_id"],"v1_target_in_pool":old.get("target_in_pool"),
                       "v2_target_in_pool":row["target_in_pool"],"candidate_count":row["candidate_count"],
                       "operator_counts":row["operator_counts"]})
    counts=[r["candidate_count"] for r in rows]; times=[r["enumeration_wall_ns"] for r in rows]
    result={"schema":"BlindStructuralRepairProposalCoverageV2Analysis","passed":not errors,
        "errors":errors,"summary":{"cases":len(rows),"target_proposal_hits":hits,
        "target_proposal_misses":len(rows)-hits,"proposal_coverage":hits/len(rows) if rows else None,
        "v1_hits":baseline["summary"]["target_proposal_hits"],
        "v1_coverage":baseline["summary"]["proposal_coverage"],
        "coverage_delta":(hits/len(rows)-baseline["summary"]["proposal_coverage"]) if rows else None,
        "candidate_count_total":sum(counts),"candidate_count_median":sorted(counts)[len(counts)//2] if counts else None,
        "enumeration_wall_ns_median":sorted(times)[len(times)//2] if times else None,"paired_cases":paired},
        "interpretation":"Paired proposal-pool iteration on the v1 authored fixture; no task outcomes, graph selection, held-out generalization, or commit were measured."}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True)); return 0 if not errors else 1

if __name__=="__main__": raise SystemExit(main())
