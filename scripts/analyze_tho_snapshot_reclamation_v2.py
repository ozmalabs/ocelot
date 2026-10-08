#!/usr/bin/env python3
"""Independent integrity and memory summary for snapshot reclamation v2."""
import hashlib,json,statistics
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from domains.engine_provenance import rust_source_fingerprint
RAW=ROOT/"evaluation/reports/thoughtexperiment_snapshot_reclamation_v2.json"
OUT=ROOT/"evaluation/reports/thoughtexperiment_snapshot_reclamation_v2_analysis.json"
def sha(path):return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def med(xs):return statistics.median(xs)
def main():
 d=json.loads(RAW.read_text());rows=d["rows"];sizes=d["protocol"]["sizes_added_nodes"];backends=d["protocol"]["backends"];reps=d["protocol"]["repeats"];warm=d["protocol"]["warmups"];expected={(n,b) for n in sizes for b in backends}
 actual={(r["size_added_nodes"],r["backend"]) for r in rows};sources={k:sha(ROOT/k) for k in d["sources"]}
 checks={"expected_45_measured_workers":len(rows)==len(sizes)*len(backends)*reps,"unique_fresh_process_per_measured_worker":len({r["pid"] for r in rows})==len(rows),"complete_size_backend_repeat_grid":actual==expected and all(sum((r["size_added_nodes"],r["backend"])==(n,b) for r in rows)==reps for n,b in expected),"complete_warmup_and_measurement_schedule":len(d["schedule"])==len(sizes)*len(backends)*(reps+warm),"all_primary_and_branch_semantics_pass":all(r["primary_revision_unchanged"] and r["branch_mutation_isolated"] and r["later_fork_sees_captured_base"] for r in rows),"all_memory_stages_present":all(set(("primary_baseline","snapshot_live","branch_live","branch_written","branch_dropped_snapshot_live","verification_branch_dropped","snapshot_dropped","primary_dropped"))<=r["samples_bytes"].keys() for r in rows),"source_and_runner_hashes_match_capture":sources==d["sources"] and sha(d["runner"]["path"])==d["runner"]["sha256"],"engine_fingerprint_current":d["engine_fingerprint"]==rust_source_fingerprint(str(ROOT))}
 stages=("snapshot_live","branch_live","branch_written","branch_dropped_snapshot_live","verification_branch_dropped","snapshot_dropped","primary_dropped");metrics=("Rss","Pss","Private_Clean","Private_Dirty","Shared_Clean","Shared_Dirty","Swap");summary=[]
 for n,b in sorted(expected):
  cell=[r for r in rows if r["size_added_nodes"]==n and r["backend"]==b]
  summary.append({"size_added_nodes":n,"backend":b,"median_stage_delta_kib":{s:{m:med([r["stage_delta_from_baseline_bytes"][s].get(m,0) for r in cell])/1024 for m in metrics} for s in stages},"all_semantic_gates_pass":all(r["primary_revision_unchanged"] and r["branch_mutation_isolated"] and r["later_fork_sees_captured_base"] for r in cell)})
 payload={"protocol":"THOUGHTEXPERIMENT_SNAPSHOT_RECLAMATION_V2","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"summary":summary,"interpretation_limit":"PSS/RSS deltas are current whole-process readings relative to baseline; negative post-drop values reflect runtime/allocator/process noise and are not a reclamation guarantee. One host and one synthetic fixture.","raw_sha256":sha(RAW),"analyzer_sha256":sha(Path(__file__))}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"measured_workers":len(rows)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("snapshot reclamation analysis failed")
if __name__=="__main__":main()
