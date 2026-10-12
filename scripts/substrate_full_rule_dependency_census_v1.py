#!/usr/bin/env python3
"""Capture the native loaded rule access graph on the frozen full corpus."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
BASE=ROOT/"evaluation/reports/substrate_seed_boot_prefix_scale_v1_20260925.json"
CORPUS=ROOT/"evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_FULL_RULE_DEPENDENCY_CENSUS_PREREG_20260925.md"
OUT=ROOT/"evaluation/reports/substrate_full_rule_dependency_census_v1_20260925.json"
PART=ROOT/"evaluation/reports/substrate_full_rule_dependency_census_v1_partial.json"
LOCK=ROOT/"evaluation/substrate_capability/full_rule_dependency_census_lock_20260925.json"
SOURCES=["runners/dsl/src/py.rs","runners/dsl/src/rewrite.rs","runners/dsl/python/substrate_rs/_native.abi3.so","runners/dsl/python/substrate_rs/_native.build.json","substrate/boot_all.py","substrate/world_adapter.py",str(CORPUS.relative_to(ROOT))]
CHILD=r'''
import hashlib,json,os,resource,sys,time
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
mode,seed_dir=sys.argv[1:]
t,c=time.perf_counter_ns(),time.process_time_ns();a=WorldAdapter(seeds=());report=load_all_seeds(a,seed_dir=seed_dir);wall=time.perf_counter_ns()-t;cpu=time.process_time_ns()-c;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
access=a.inner.rule_access_sets();rules=a.inner.export_rules()
if len(access)!=len(rules):raise RuntimeError(f"rule slot mismatch: access={len(access)} rules={len(rules)}")
rows=[]
for slot,(ar,rule) in enumerate(zip(access,rules)):
    idx,name,active,reads,term_reads,writes,reads_any,writes_any=ar
    if int(idx)!=slot:raise RuntimeError(f"noncanonical RuleIdx {idx} at {slot}")
    rows.append({"index":slot,"name":name,"active":bool(active),"reads":list(reads),"term_edge_reads":list(term_reads),"writes":list(writes),"reads_any":bool(reads_any),"writes_any":bool(writes_any),"area":rule.get("area"),"latency_class":rule.get("latency_class"),"rule_order":rule.get("order")})
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
state={"report":report,"nodes":a.inner.node_count(),"edges":a.inner.edge_count(),"graph":h(a.inner.graph_to_dict()),"grammar":h(a.inner.grammar_to_json()),"rules":h(rules),"access":h(access),"rule_order":[x["name"] for x in rows if x["active"]]}
print(json.dumps({"pid":os.getpid(),"cache_mode":mode,"wall_ns":wall,"cpu_ns":cpu,"peak_rss_native_units":rss,"state":state,"slot_count":len(rows),"active_count":sum(r["active"] for r in rows),"access_rows":rows}))
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_hashes():return {p:sha(ROOT/p) for p in SOURCES}
def main():
    if OUT.exists() or PART.exists():raise SystemExit("result/checkpoint exists")
    baseline=json.loads(BASE.read_text());corpus=json.loads(CORPUS.read_text());snapshot=Path(baseline["snapshot"]["full_seed_dir"])
    if not snapshot.is_dir():raise SystemExit("frozen full-corpus snapshot unavailable")
    for item in corpus["manifests"]:
        if sha(snapshot/item["path"])!=item["sha256"]:raise SystemExit(f"corpus mismatch: {item['path']}")
    from domains.engine_provenance import build_is_stale
    stale=build_is_stale(str(ROOT))
    if stale:raise SystemExit(f"native build stale: {stale}")
    lock={"schema_version":1,"protocol_sha256":sha(PROTOCOL),"runner_sha256":sha(Path(__file__)),"sources":source_hashes(),"corpus_digest":corpus["corpus_digest"],"baseline_raw_sha256":sha(BASE),"worker_count":2,"frame_widths":[16,32,64,128],"shuffle_seeds":[8101,8102,8103,8104,8105]}
    LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+"\n")
    seed_dir=baseline["snapshot"]["subsets"]["737"]["seed_dir"]
    env={**os.environ,"PYTHONHASHSEED":"0","PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}"}
    from substrate.boot_all import _read_seed_index,_seed_index_cache_path
    rows=[]
    for i,mode in enumerate(("cold","warm"),1):
        cache=Path(_seed_index_cache_path(seed_dir))
        if mode=="cold":cache.unlink(missing_ok=True);before=None
        else:_read_seed_index(seed_dir);before=sha(cache)
        p=subprocess.run([sys.executable,"-c",CHILD,mode,seed_dir],cwd=ROOT,env=env,capture_output=True,text=True,timeout=900)
        if p.returncode:raise RuntimeError(p.stderr[-3000:])
        worker=json.loads(p.stdout.strip().splitlines()[-1]);after=sha(cache)
        if before is not None and before!=after:raise RuntimeError("warm cache changed")
        rows.append({"ordinal":i,"cache_before":before,"cache_after":after,"worker":worker})
        PART.write_text(json.dumps({"lock":lock,"workers":rows},indent=2,sort_keys=True)+"\n")
        print(json.dumps({"worker":i,"mode":mode,"active_rules":worker["active_count"],"slots":worker["slot_count"],"wall_ns":worker["wall_ns"]}),flush=True)
    old=next(x["worker"] for x in baseline["arms"] if x["requested_size"]==737)
    base_state={"report":old["report"],"nodes":old["node_count"],"edges":old["edge_count"],"graph":old["graph_sha256"],"grammar":old["grammar_sha256"],"rules":old["rule_store_sha256"],"access":old["rule_access_sha256"],"rule_order":old["rule_order"]}
    parity=all(w["worker"]["state"]==base_state for w in rows)
    result={"schema_version":1,"probe_id":"full-rule-dependency-census-v1-20260925","lock":lock,"workers":rows,"frozen_state_parity":parity,"worker_state_parity":rows[0]["worker"]["state"]==rows[1]["worker"]["state"],"unique_processes":len({x["worker"]["pid"] for x in rows})==2,"source_hashes_after":source_hashes(),"protocol_sha256_after":sha(PROTOCOL),"runner_sha256_after":sha(Path(__file__))}
    result["all_gates_pass"]=result["frozen_state_parity"] and result["worker_state_parity"] and result["unique_processes"] and result["source_hashes_after"]==lock["sources"] and result["protocol_sha256_after"]==lock["protocol_sha256"] and result["runner_sha256_after"]==lock["runner_sha256"]
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");PART.unlink(missing_ok=True)
    print(json.dumps({"all_gates_pass":result["all_gates_pass"],"state_parity":parity,"output":str(OUT)}));return 0 if result["all_gates_pass"] else 2
if __name__=="__main__":raise SystemExit(main())
