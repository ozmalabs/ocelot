#!/usr/bin/env python3
"""Validate native concurrent snapshot isolation and summarize costs."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from domains.engine_provenance import rust_source_fingerprint
RAW=ROOT/"evaluation/reports/cow_snapshot_concurrent_fork_v1.json"
OUT=ROOT/"evaluation/reports/cow_snapshot_concurrent_fork_v1_analysis.json"
SOURCES=("evaluation/substrate_capability/cow_snapshot_concurrent_fork_v1.py","scripts/analyze_cow_snapshot_concurrent_fork_v1.py","evaluation/substrate_capability/fixtures/cow_snapshot_threads/Cargo.toml","evaluation/substrate_capability/fixtures/cow_snapshot_threads/Cargo.lock","evaluation/substrate_capability/fixtures/cow_snapshot_threads/src/main.rs","runners/dsl/python/substrate_rs/_native.build.json","runners/dsl/src/substrate.rs","runners/dsl/src/graph.rs","runners/dsl/src/py.rs")
def sha(path):return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def med(xs):return statistics.median(xs)
def main():
 c=json.loads(RAW.read_text());m=c["measurements"];rows=m["rows"];expected={(n,f) for n in m["sizes"] for f in m["fanouts"]};actual={(x["size_nodes"],x["fanout"]) for x in rows};src={p:sha(ROOT/p) for p in SOURCES}
 checks={"native_snapshot_compiles_send_sync":m["experiment_snapshot_send_sync"],"nine_size_fanout_cells_complete":actual==expected and len(rows)==9,"five_paired_repeats_each":all(x["repeats"]==5 and len(x["serial_batch_us"])==5 and len(x["concurrent_batch_us"])==5 for x in rows),"arm_order_alternates":all(x["arm_order"]==["serial_then_concurrent","concurrent_then_serial","serial_then_concurrent","concurrent_then_serial","serial_then_concurrent"] for x in rows),"all_semantic_isolation_gates_pass":all(x["all_semantic_gates_pass"] for x in rows),"source_and_artifact_hashes_match":src==c["sources"] and sha(c["runner"]["path"])==c["runner"]["sha256"] and sha(c["probe_binary"]["path"])==c["probe_binary"]["sha256"],"engine_fingerprint_current":c["engine_fingerprint"]==rust_source_fingerprint(str(ROOT))}
 summary=[]
 for x in sorted(rows,key=lambda r:(r["size_nodes"],r["fanout"])):
  s=med(x["serial_batch_us"]);p=med(x["concurrent_batch_us"])
  summary.append({"size_nodes":x["size_nodes"],"fanout":x["fanout"],"repeats":x["repeats"],"snapshot_capture_median_us":med(x["snapshot_capture_us"]),"serial_batch_median_us":s,"concurrent_batch_median_us":p,"serial_over_concurrent_speed_ratio":s/p if p else None,"concurrent_wins_paired_repeats":sum(a>b for a,b in zip(x["serial_batch_us"],x["concurrent_batch_us"]))})
 payload={"protocol":"COW_SNAPSHOT_CONCURRENT_FORK_V1","all_checks_pass":all(checks.values()),"checks":checks,"checks_passed":sum(checks.values()),"checks_total":len(checks),"summary":summary,"claim_boundary":"Native Rust concurrent snapshot fork-plus-one-node-mutation on synthetic isolated-node graphs; one host. Thread safety and measured scaling do not imply concurrent live-Substrate mutation, natural-workload throughput, or universal parallel speedup.","raw_sha256":"sha256:"+hashlib.sha256(RAW.read_bytes()).hexdigest(),"analyzer_sha256":sha(Path(__file__))}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n");print(json.dumps({"all_checks_pass":payload["all_checks_pass"],"checks_passed":payload["checks_passed"],"checks_total":payload["checks_total"],"cells":len(summary)},indent=2))
 if not payload["all_checks_pass"]:raise SystemExit("concurrent snapshot analysis gates failed")
if __name__=="__main__":main()
