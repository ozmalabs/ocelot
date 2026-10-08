#!/usr/bin/env python3
"""Source-locked measurement of graph-evidence-guided match-edge proposals."""
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/"evaluation/substrate_capability/analyze_blind_structural_repair_relation_evidence_v1.py"
PROTOCOL=ROOT/"docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_STRUCTURAL_REPAIR_RELATION_EVIDENCE_V1_PREREG_20261005.md"
RULES=ROOT/"evaluation/substrate_capability/blind_structural_repair_proposal_coverage_v1_fixture_20261005.json"
GRAPHS=ROOT/"evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1_fixture_20261005.json"
EDIT_OPS=ROOT/"domains/edit_ops.py"
BASELINE=ROOT/"evaluation/reports/blind_structural_repair_proposal_coverage_v2_analysis_20261005.json"
LOCK=ROOT/"evaluation/substrate_capability/blind_structural_repair_relation_evidence_v1_lock_20261005.json"
OUT=ROOT/"evaluation/reports/blind_structural_repair_relation_evidence_v1_20261005.json"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen(): return {str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,ANALYZER,PROTOCOL,RULES,GRAPHS,EDIT_OPS,BASELINE)}
def canonical(rule):
    value=json.loads(json.dumps(rule)); value.pop("name",None); value.pop("active",None); names={}
    def normalize(name):
        if name not in names: names[name]=f"VAR{len(names)}"
        return names[name]
    def walk(node):
        if isinstance(node,dict):
            if node.get("type")=="Var" and isinstance(node.get("name"),str):
                node["name"]=normalize(node["name"])
            for key,child in node.items():
                if key=="match" and isinstance(child,list):
                    for edge in child:
                        if isinstance(edge,list) and len(edge)>=3:
                            if isinstance(edge[0],str): edge[0]=normalize(edge[0])
                            if isinstance(edge[2],str): edge[2]=normalize(edge[2])
                else: walk(child)
        elif isinstance(node,list):
            for child in node: walk(child)
    walk(value)
    return json.dumps(value,sort_keys=True,separators=(",",":"))

def worker(index):
    from domains.edit_ops import enumerate_single_edit_candidates, observed_relation_signatures
    lock=json.loads(LOCK.read_text()); before=frozen()
    if before!=lock["sources"]: raise RuntimeError("source mismatch before worker")
    cases=json.loads(RULES.read_text())["cases"]; graph_rows=json.loads(GRAPHS.read_text())["cases"]; rows=[]
    for case in cases:
        graph=graph_rows[case["case_id"]]
        signatures=observed_relation_signatures(case["faulted_rule"],graph["bindings"],graph["edges"])
        t0=time.perf_counter_ns()
        candidates=enumerate_single_edit_candidates(case["faulted_rule"],max_candidates=lock["candidate_cap"],observed_relations=signatures)
        elapsed=time.perf_counter_ns()-t0
        cands=[canonical(row["rule"]) for row in candidates]; target=canonical(case["target_rule_sealed"])
        relation_count=sum(row["operator"]=="add_match_edge" for row in candidates)
        rows.append({"case_id":case["case_id"],"candidate_count":len(candidates),
            "proposal_count_before_dedup":candidates[0]["proposal_count_before_dedup"] if candidates else 0,
            "valid_count_before_dedup":candidates[0]["valid_count_before_dedup"] if candidates else 0,
            "unique_count":candidates[0]["unique_count"] if candidates else 0,
            "truncated":candidates[0]["truncated"] if candidates else False,
            "relation_signatures":signatures,"relation_candidate_count":relation_count,
            "target_in_pool":target in cands,"target_match_count":cands.count(target),
            "operator_counts":{op:sum(row["operator"]==op for row in candidates) for op in sorted({row["operator"] for row in candidates})},
            "candidate_ids":[row["candidate_id"] for row in candidates],"enumeration_wall_ns":elapsed})
    after=frozen()
    if after!=lock["sources"]: raise RuntimeError("source drift during worker")
    return {"worker":index,"pid":os.getpid(),"sources_before":before,"sources_after":after,"cases":rows}

def main():
    if sys.argv[1:]==["--lock"]:
        if LOCK.exists() or OUT.exists(): raise SystemExit("refusing overwrite")
        LOCK.write_text(json.dumps({"schema":"BlindStructuralRepairRelationEvidenceV1Lock","sources":frozen(),
            "workers":3,"case_count":len(json.loads(RULES.read_text())["cases"]),"candidate_cap":256},indent=2,sort_keys=True)+"\n")
        print(LOCK.relative_to(ROOT)); return 0
    if len(sys.argv)==3 and sys.argv[1]=="--worker":
        print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(",",":"))); return 0
    if sys.argv[1:]!=["--run"]: raise SystemExit("usage: --lock | --run | --worker N")
    lock=json.loads(LOCK.read_text())
    if frozen()!=lock["sources"]: raise SystemExit("source lock mismatch")
    env=dict(os.environ);env["PYTHONPATH"]=str(ROOT);workers=[]
    for i in range(lock["workers"]):
        proc=subprocess.run([sys.executable,str(RUNNER),"--worker",str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=120)
        if proc.returncode: raise RuntimeError(f"worker {i} failed: {proc.stderr[-2000:]}")
        workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    if frozen()!=lock["sources"]: raise SystemExit("source drift during capture")
    OUT.write_text(json.dumps({"schema":"BlindStructuralRepairRelationEvidenceV1","lock_sha256":sha(LOCK),
        "host":platform.platform(),"workers":workers},indent=2,sort_keys=True)+"\n")
    print(OUT.relative_to(ROOT)); return 0

if __name__=="__main__": raise SystemExit(main())
