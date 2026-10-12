#!/usr/bin/env python3
"""Full-corpus parity gate for native manifest projection."""
from __future__ import annotations
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"scripts")]
BASE=ROOT/"evaluation/reports/substrate_seed_boot_prefix_scale_v1_20260925.json"
OUT=ROOT/"evaluation/reports/substrate_native_seed_projection_integration_v1_20260925.json"
PART=ROOT/"evaluation/reports/substrate_native_seed_projection_integration_v1_partial.json"
LOCK=ROOT/"evaluation/substrate_capability/native_seed_projection_integration_lock_20260925.json"
PROTOCOL=ROOT/"docs/research/engine_substrate/SUBSTRATE_NATIVE_SEED_PROJECTION_INTEGRATION_PREREG_20260925.md"
SOURCES=["runners/dsl/src/py.rs","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/python/substrate_rs/_native.abi3.so","runners/dsl/python/substrate_rs/_native.build.json","substrate/boot_all.py","substrate/world_adapter.py","evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json"]
CHILD=r'''
import hashlib,json,resource,sys,time,os
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
mode,seed_dir=sys.argv[1:]
t,c=time.perf_counter_ns(),time.process_time_ns();a=WorldAdapter(seeds=());r=load_all_seeds(a,seed_dir=seed_dir);wall=time.perf_counter_ns()-t;cpu=time.process_time_ns()-c;rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()
rules=sorted((x for x in a.inner.rule_access_sets() if x[2]),key=lambda x:int(x[0]));names=[str(x[1]) for x in rules]
print(json.dumps({"pid":os.getpid(),"mode":mode,"wall_ns":wall,"cpu_ns":cpu,"peak_rss_native_units":rss,"report":r,"node_count":a.inner.node_count(),"edge_count":a.inner.edge_count(),"graph_sha256":h(a.inner.graph_to_dict()),"grammar_sha256":h(a.inner.grammar_to_json()),"rule_store_sha256":h(a.inner.export_rules()),"rule_access_sha256":h(a.inner.rule_access_sets()),"active_rule_count":len(names),"rule_order":names,"rule_order_sha256":h(names)}))
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sources():return {x:sha(ROOT/x) for x in SOURCES}
def state(x):return {k:x[k] for k in ("report","node_count","edge_count","graph_sha256","grammar_sha256","rule_store_sha256","rule_access_sha256","active_rule_count","rule_order","rule_order_sha256")}
def main():
    if OUT.exists() or PART.exists():raise SystemExit("result/checkpoint exists")
    baseline=json.loads(BASE.read_text()); corpus_path=ROOT/SOURCES[-1];corpus=json.loads(corpus_path.read_text());snapshot=Path(baseline["snapshot"]["full_seed_dir"])
    if not snapshot.is_dir():raise SystemExit("frozen corpus snapshot unavailable")
    for item in corpus["manifests"]:
        if sha(snapshot/item["path"])!=item["sha256"]:raise SystemExit(f"corpus mismatch: {item['path']}")
    from domains.engine_provenance import build_is_stale
    stale=build_is_stale(str(ROOT))
    if stale:raise SystemExit(f"native build stale: {stale}")
    source=sources();ph=sha(PROTOCOL);rh=sha(Path(__file__));lock={"schema_version":1,"protocol_sha256":ph,"runner_sha256":rh,"sources":source,"baseline_raw_sha256":sha(BASE),"corpus_digest":corpus["corpus_digest"],"workers":4}
    LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+"\n")
    from substrate_rs import _native
    cases=[]
    fields={"nodes":[],"edges":[],"productions":[],"rules":[],"reflexes":[],"id":"projection-contract","self_modification_patchable_rules":[],"area":"test","order":7,"latency_class":"test"}
    for key,value in fields.items():
        manifest={"id":"projection-contract",key:value} if key!="id" else {key:value}
        sub=_native.Substrate();summary=sub.load_seed_manifest(manifest)
        if key in ("nodes","edges","productions","rules","reflexes","id","self_modification_patchable_rules","area","order","latency_class"):cases.append({"label":"present_optional_"+key,"summary":summary,"nodes":sub.node_count(),"edges":sub.edge_count()})
        absent_manifest={} if key=="id" else {"id":"projection-contract"}
        sub2=_native.Substrate();summary2=sub2.load_seed_manifest(absent_manifest)
        cases.append({"label":"absent_optional_"+key,"summary":summary2,"nodes":sub2.node_count(),"edges":sub2.edge_count()})
    for label,manifest in (("unknown_json",{"id":"projection-contract","graph":{"nodes":[1]}}),("unknown_non_json",{"id":"projection-contract","graph":object()})):
        original_items=dict(manifest);sub=_native.Substrate();summary=sub.load_seed_manifest(manifest)
        unchanged=len(manifest)==len(original_items) and all(k in manifest and manifest[k] is v for k,v in original_items.items())
        cases.append({"label":label,"summary":summary,"nodes":sub.node_count(),"edges":sub.edge_count(),"caller_manifest_unchanged":unchanged})
        if not unchanged:raise RuntimeError(f"caller manifest mutated: {label}")
    try:_native.Substrate().load_seed_manifest([]);root_error=None
    except Exception as e:root_error={"class":type(e).__name__,"message":str(e)}
    if root_error!={"class":"ValueError","message":"seed manifest must be a JSON object"}:raise RuntimeError(f"root error contract failed: {root_error}")
    sub=_native.Substrate()
    try:sub.load_seed_manifest({"nodes":[{"type":"Broken"}]});node_error=None
    except Exception as e:node_error={"class":type(e).__name__,"message":str(e)}
    if node_error!={"class":"ValueError","message":"seed node missing local_id"}:raise RuntimeError(f"consumed-node error contract failed: {node_error}")
    cases.extend(({"label":"non_dict_root","error":root_error},{"label":"malformed_consumed_node","error":node_error,"post_error_nodes":sub.node_count()}))
    malformed={"edges":{"edges":[{"type":"broken","src":{},"tgt":{}}]},
                "productions":{"productions":[{}]},"rules":{"rules":[{"name":"broken"}]},
                "reflexes":{"reflexes":[{"name":"broken"}]}}
    for key,manifest in malformed.items():
        sub=_native.Substrate()
        try:summary=sub.load_seed_manifest(manifest);error=None
        except Exception as e:summary=None;error={"class":type(e).__name__,"message":str(e)}
        cases.append({"label":"malformed_consumed_"+key,"error":error,"summary":summary,"nodes":sub.node_count(),"edges":sub.edge_count()})
    seed_dir=baseline["snapshot"]["subsets"]["737"]["seed_dir"];env={**os.environ,"PYTHONHASHSEED":"0","PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}"};arms=[]
    for i,mode in enumerate(("cold","warm","warm","cold"),1):
        from substrate.boot_all import _read_seed_index,_seed_index_cache_path
        cache=Path(_seed_index_cache_path(seed_dir))
        if mode=="cold":cache.unlink(missing_ok=True);before=None
        else:_read_seed_index(seed_dir);before=sha(cache)
        p=subprocess.run([sys.executable,"-c",CHILD,mode,seed_dir],cwd=ROOT,env=env,capture_output=True,text=True,timeout=900)
        if p.returncode:raise RuntimeError(p.stderr[-3000:])
        row=json.loads(p.stdout.strip().splitlines()[-1]);after=sha(cache)
        if before is not None and before!=after:raise RuntimeError("warm cache changed")
        arms.append({"ordinal":i,"cache_mode":mode,"cache_before":before,"cache_after":after,"worker":row})
        PART.write_text(json.dumps({"lock":lock,"contract_probes":cases,"arms":arms},indent=2,sort_keys=True)+"\n")
        print(json.dumps({"ordinal":i,"mode":mode,"wall_ns":row["wall_ns"],"nodes":row["node_count"],"pid":row["pid"]}),flush=True)
    baseline_row=next(a["worker"] for a in baseline["arms"] if a["requested_size"]==737)
    parity=all(state(a["worker"])==state(baseline_row) for a in arms)
    result={"schema_version":1,"probe_id":"native-seed-projection-integration-v1-20260925","lock":lock,"contract_probes":cases,"arms":arms,"frozen_baseline_state_parity":parity,"within_run_state_parity":all(state(a["worker"])==state(arms[0]["worker"]) for a in arms),"unique_processes":len({a["worker"]["pid"] for a in arms})==4,"source_hashes_after":sources(),"protocol_sha256_after":sha(PROTOCOL),"runner_sha256_after":sha(Path(__file__))}
    result["all_gates_pass"]=result["frozen_baseline_state_parity"] and result["within_run_state_parity"] and result["unique_processes"] and result["source_hashes_after"]==source and result["protocol_sha256_after"]==ph and result["runner_sha256_after"]==rh
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n");PART.unlink(missing_ok=True)
    print(json.dumps({"all_gates_pass":result["all_gates_pass"],"frozen_baseline_state_parity":parity,"output":str(OUT)}));return 0 if result["all_gates_pass"] else 2
if __name__=="__main__":raise SystemExit(main())
