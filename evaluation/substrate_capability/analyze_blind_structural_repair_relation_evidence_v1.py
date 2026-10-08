#!/usr/bin/env python3
"""Independent validation and paired summary for graph relation proposals."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
RUNNER=ROOT/"evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1.py"
ANALYZER=Path(__file__).resolve()
PROTOCOL=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_RELATION_EVIDENCE_V1_PREREG_20261005.md"
RULES=ROOT/"evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json"
GRAPHS=ROOT/"evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1_fixture_20261005.json"
EDIT_OPS=ROOT/"domains/edit_ops.py"
BASELINE=ROOT/"evaluation/reports/blind_structural_repair_proposal_coverage_v2_analysis_20261005.json"
LOCK=ROOT/"evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1_lock_20261005.json"
CAPTURE=ROOT/"evaluation/reports/blind_structural_repair_relation_evidence_v1_20261005.json"
OUT=ROOT/"evaluation/reports/blind_structural_repair_relation_evidence_v1_analysis_20261005.json"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():return {str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL,RULES,GRAPHS,EDIT_OPS,BASELINE)}

def main():
    lock=json.loads(LOCK.read_text()); capture=json.loads(CAPTURE.read_text()); baseline=json.loads(BASELINE.read_text()); errors=[]
    if frozen()!=lock["sources"]:errors.append("source hashes differ from lock")
    if capture.get("lock_sha256")!=sha(LOCK):errors.append("capture lock hash mismatch")
    workers=capture.get("workers",[])
    if len(workers)!=lock["workers"]:errors.append("worker count mismatch")
    aligned=[]
    for worker in workers:
        if worker.get("sources_before")!=lock["sources"] or worker.get("sources_after")!=lock["sources"]:errors.append("worker source mismatch")
        rows=worker.get("cases",[])
        if len(rows)!=lock["case_count"]:errors.append("case count mismatch")
        for row in rows:
            if row.get("truncated"):errors.append(f"truncated candidates: {row.get('case_id')}")
            if row.get("candidate_count")!=row.get("unique_count"):errors.append(f"candidate count mismatch: {row.get('case_id')}")
            if row.get("candidate_count")!=len(set(row.get("candidate_ids",[]))):errors.append(f"duplicate candidate id: {row.get('case_id')}")
            if row.get("relation_candidate_count")!=len(row.get("relation_signatures",[])):errors.append(f"relation accounting mismatch: {row.get('case_id')}")
        aligned.append({r.get("case_id"):r for r in rows})
    if aligned:
        for other in aligned[1:]:
            if set(other)!=set(aligned[0]):errors.append("worker case IDs differ");continue
            for cid,first in aligned[0].items():
                second=other[cid]
                for key in ("candidate_count","proposal_count_before_dedup","valid_count_before_dedup","unique_count","truncated","relation_signatures","relation_candidate_count","target_in_pool","target_match_count","operator_counts","candidate_ids"):
                    if first.get(key)!=second.get(key):errors.append(f"worker mismatch {cid}.{key}");break
    rows=list(aligned[0].values()) if aligned else []
    old={r["case_id"]:r for r in baseline["summary"]["paired_cases"]}
    if set(old)!={r["case_id"] for r in rows}:errors.append("v2 panel mismatch")
    hits=sum(bool(r.get("target_in_pool")) for r in rows)
    paired=[{"case_id":r["case_id"],"v2_target_in_pool":old[r["case_id"]]["v2_target_in_pool"],"v3_target_in_pool":r["target_in_pool"],"relation_candidate_count":r["relation_candidate_count"],"candidate_count":r["candidate_count"]} for r in rows if r["case_id"] in old]
    times=[r["enumeration_wall_ns"] for r in rows]; counts=[r["candidate_count"] for r in rows]
    result={"schema":"BlindStructuralRepairRelationEvidenceV1Analysis","passed":not errors,"errors":errors,
        "summary":{"cases":len(rows),"target_proposal_hits":hits,"target_proposal_misses":len(rows)-hits,
        "proposal_coverage":hits/len(rows) if rows else None,"v2_hits":baseline["summary"]["target_proposal_hits"],
        "v2_coverage":baseline["summary"]["proposal_coverage"],"coverage_delta":hits/len(rows)-baseline["summary"]["proposal_coverage"] if rows else None,
        "relation_candidates_total":sum(r.get("relation_candidate_count",0) for r in rows),
        "candidate_count_total":sum(counts),"candidate_count_median":sorted(counts)[len(counts)//2] if counts else None,
        "enumeration_wall_ns_median":sorted(times)[len(times)//2] if times else None,"paired_cases":paired},
        "interpretation":"Controlled graph-evidence-to-proposal translation only; no candidate utility, selection, held-out behavior, or commit was measured."}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");print(json.dumps(result,sort_keys=True));return 0 if not errors else 1
if __name__=="__main__":raise SystemExit(main())
