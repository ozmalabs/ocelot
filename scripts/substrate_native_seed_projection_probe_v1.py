#!/usr/bin/env python3
"""Paired control/projection startup probe for the native seed boundary."""
from __future__ import annotations

import hashlib, importlib.util, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
BASELINE_RAW = ROOT / "evaluation/reports/substrate_seed_boot_prefix_scale_v1_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_native_seed_projection_probe_v1_20260925.json"
PART = ROOT / "evaluation/reports/substrate_native_seed_projection_probe_v1_partial.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_NATIVE_SEED_PROJECTION_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/native_seed_projection_lock_20260925.json"
SOURCES = ["substrate/boot_all.py", "substrate/world_adapter.py", "runners/dsl/src/py.rs",
           "runners/dsl/python/substrate_rs/_native.abi3.so",
           "runners/dsl/python/substrate_rs/_native.build.json"]
NATIVE_KEYS = ("nodes", "edges", "productions", "rules", "reflexes", "id",
               "self_modification_patchable_rules", "area", "order", "latency_class")
CHILD = r'''
import hashlib,json,os,resource,sys,time
from substrate_rs import _native
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
mode,seed_dir=sys.argv[1:]
keys=("nodes","edges","productions","rules","reflexes","id","self_modification_patchable_rules","area","order","latency_class")
original=_native.Substrate.load_seed_manifest
stats={"calls":0,"manifests":[]}
def wrapped(self,manifest,*args,**kwargs):
    stats["calls"]+=1
    sent=manifest if mode=="control" else {k:manifest[k] for k in keys if k in manifest}
    stats["manifests"].append((manifest,sent))
    return original(self,sent,*args,**kwargs)
_native.Substrate.load_seed_manifest=wrapped
t0,c0=time.perf_counter_ns(),time.process_time_ns(); adapter=WorldAdapter(seeds=());report=load_all_seeds(adapter,seed_dir=seed_dir);wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0;peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
input_bytes=sum(len(json.dumps(m,separators=(",",":"),ensure_ascii=False).encode()) for m,_ in stats["manifests"])
projected_bytes=sum(len(json.dumps(m,separators=(",",":"),ensure_ascii=False).encode()) for _,m in stats["manifests"])
stats={"calls":stats["calls"],"input_bytes":input_bytes,"projected_bytes":projected_bytes}
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
rules=sorted((x for x in adapter.inner.rule_access_sets() if x[2]),key=lambda x:int(x[0])); names=[str(x[1]) for x in rules]
print(json.dumps({"process_id":os.getpid(),"mode":mode,"wall_ns":wall,"cpu_ns":cpu,"peak_rss_native_units":peak,"native_call_stats":stats,"report":report,"node_count":adapter.inner.node_count(),"edge_count":adapter.inner.edge_count(),"graph_sha256":h(adapter.inner.graph_to_dict()),"grammar_sha256":h(adapter.inner.grammar_to_json()),"rule_store_sha256":h(adapter.inner.export_rules()),"rule_access_sha256":h(adapter.inner.rule_access_sets()),"active_rule_count":len(names),"rule_order_sha256":h(names),"self_model":report.get("self_model",{})}))
'''

def sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def source_hashes(): return {p:sha(ROOT/p) for p in SOURCES}

def main():
    if OUT.exists() or PART.exists(): raise SystemExit("refusing to overwrite prior result/checkpoint")
    baseline=json.loads(BASELINE_RAW.read_text())
    snapshot_root=Path(baseline["snapshot"]["full_seed_dir"])
    if not snapshot_root.is_dir(): raise SystemExit("locked full snapshot is unavailable; regenerate an isolated snapshot")
    corpus=json.loads((ROOT/"evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json").read_text())
    for item in corpus["manifests"]:
        path=snapshot_root/item["path"]
        if not path.is_file() or sha(path)!=item["sha256"]: raise SystemExit(f"frozen corpus mismatch: {item['path']}")
    for size in (512,737):
        seed_dir=Path(baseline["snapshot"]["subsets"][str(size)]["seed_dir"])
        rows=[(p.relative_to(seed_dir).as_posix(),sha(p)) for p in sorted(seed_dir.rglob("*.json"))]
        digest=hashlib.sha256(json.dumps(rows,separators=(",",":")).encode()).hexdigest()
        if digest!=baseline["snapshot"]["subsets"][str(size)]["subset_digest"]: raise SystemExit(f"subset hash mismatch: N={size}")
    locked=source_hashes()
    protocol_hash=sha(PROTOCOL); runner_hash=sha(Path(__file__))
    lock={"schema_version":1,"protocol_sha256":protocol_hash,"runner_sha256":runner_hash,
          "sources":locked,"sizes":[512,737],"replicates":3,"native_keys":list(NATIVE_KEYS),
          "corpus_digest":json.loads((ROOT/"evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json").read_text())["corpus_digest"]}
    if LOCK.exists():
        old=json.loads(LOCK.read_text())
        if old != lock: raise SystemExit("existing source/protocol lock differs; refusing overwrite")
    else: LOCK.write_text(json.dumps(lock,indent=2,sort_keys=True)+"\n")
    env={**os.environ,"PYTHONHASHSEED":"0","PYTHONPATH":f"{ROOT}:{ROOT/'runners/dsl/python'}:{ROOT/'scripts'}"}
    arms=[]
    schedule=[(512,"control"),(512,"projection"),(737,"projection"),(737,"control")]*3
    for i,(size,mode) in enumerate(schedule,1):
        seed_dir=baseline["snapshot"]["subsets"][str(size)]["seed_dir"]
        if not Path(seed_dir).is_dir(): raise SystemExit(f"subset snapshot missing: N={size}")
        proc=subprocess.run([sys.executable,"-c",CHILD,mode,seed_dir],cwd=ROOT,env=env,capture_output=True,text=True,timeout=900)
        if proc.returncode: raise RuntimeError(proc.stderr[-3000:])
        row=json.loads(proc.stdout.strip().splitlines()[-1])
        arms.append({"ordinal":i,"size":size,"mode":mode,"worker":row})
        PART.write_text(json.dumps({"lock":lock,"arms":arms},indent=2,sort_keys=True)+"\n")
        print(json.dumps({"ordinal":i,"size":size,"mode":mode,"wall_ns":row["wall_ns"],"rss":row["peak_rss_native_units"],"bytes":row["native_call_stats"]["input_bytes"],"projected":row["native_call_stats"]["projected_bytes"]}),flush=True)
    def fp(row): return {k:row[k] for k in ("report","node_count","edge_count","graph_sha256","grammar_sha256","rule_store_sha256","rule_access_sha256","active_rule_count","rule_order_sha256")}
    parity={}
    for size in (512,737):
        group=[a["worker"] for a in arms if a["size"]==size]
        parity[str(size)]=len(group)==6 and all(fp(x)==fp(group[0]) for x in group)
    result={"schema_version":1,"probe_id":"native-seed-projection-v1-20260925","lock":lock,"arms":arms,
            "state_parity_by_size":parity,"all_state_parity":all(parity.values()),
            "unique_processes":len({a["worker"]["process_id"] for a in arms})==12,
            "source_hashes_after":source_hashes(),"protocol_sha256_after":sha(PROTOCOL),"runner_sha256_after":sha(Path(__file__))}
    result["all_gates_pass"]=result["all_state_parity"] and result["unique_processes"] and result["source_hashes_after"]==locked and result["protocol_sha256_after"]==protocol_hash and result["runner_sha256_after"]==runner_hash
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n"); PART.unlink(missing_ok=True)
    print(json.dumps({"all_gates_pass":result["all_gates_pass"],"state_parity_by_size":parity,"output":str(OUT)}))
    return 0 if result["all_gates_pass"] else 2

if __name__=="__main__": raise SystemExit(main())
