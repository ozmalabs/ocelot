#!/usr/bin/env python3
"""Capture source-locked TypedGraph mutations at alternate CowShardedMap counts."""
import argparse, hashlib, json, pathlib, platform, shutil, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
CRATE=ROOT/"runners/dsl"
BIN=CRATE/"target/release/typed_graph_cow_attr_index_mutation_v3"
NAME="typed_graph_cow_attr_index_mutation_v3"
CONFIGS=((64,None),(128,"cow_shards_128"),(256,"cow_shards_256"),(512,"cow_shards_512"))
SOURCES=("runners/dsl/src/graph.rs","runners/dsl/src/cow_sharded_map.rs","runners/dsl/src/cow_paged_vec.rs",
 "runners/dsl/src/bin/typed_graph_cow_attr_index_mutation_v3.rs","runners/dsl/Cargo.toml","runners/dsl/Cargo.lock",
 "docs/research/engine_substrate/TYPED_GRAPH_COW_SHARD_COUNT_V7_PREREG_20261006.md",
 "evaluation/substrate_capability/typed_graph_cow_shard_count_v7.py",
 "evaluation/substrate_capability/analyze_typed_graph_cow_shard_count_v7.py")
LOCK=ROOT/"evaluation/substrate_capability/typed_graph_cow_shard_count_v7_lock_20261006.json"
OUT=ROOT/"evaluation/reports/typed_graph_cow_shard_count_v7_raw_20261006.json"
TMP=pathlib.Path("/tmp/ocelot_typed_graph_cow_shard_count_v7")
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def cmd(args): return subprocess.check_output(args,cwd=CRATE,text=True,stderr=subprocess.DEVNULL).strip()
def build(feature):
    args=["cargo","build","--release","--no-default-features"]
    if feature: args += ["--features",feature]
    args += ["--bin",NAME]
    subprocess.run(args,cwd=CRATE,check=True,stdout=subprocess.DEVNULL)
    return sha(BIN)
def source_hashes(): return {p:sha(ROOT/p) for p in SOURCES}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--lock",action="store_true"); args=ap.parse_args()
    binaries={}
    for count,feature in CONFIGS:
        TMP.mkdir(parents=True,exist_ok=True)
        worker=TMP/f"worker_{count}"
        if not worker.exists():
            binaries[str(count)]=build(feature)
            shutil.copy2(BIN,worker)
        else:
            binaries[str(count)]=sha(worker)
    inputs={"source_sha256":source_hashes(),"binary_sha256_by_shards":binaries,
      "rustc":cmd(["rustc","--version"]),"cargo":cmd(["cargo","--version"]),"platform":platform.platform()}
    if args.lock:
        LOCK.write_text(json.dumps(inputs,indent=2,sort_keys=True)+"\n"); print(LOCK.relative_to(ROOT)); return
    if not LOCK.exists() or json.loads(LOCK.read_text())!=inputs: raise SystemExit("missing/stale lock")
    rows=[]
    sizes=(7164,16384,50771)
    for replicate in range(3):
      for size_index,n in enumerate(sizes):
        order=CONFIGS[(replicate+size_index)%len(CONFIGS):]+CONFIGS[:(replicate+size_index)%len(CONFIGS)]
        for count,feature in order:
            worker=TMP/f"worker_{count}"
            if not worker.exists() or sha(worker)!=binaries[str(count)]:
                if build(feature)!=binaries[str(count)]: raise SystemExit("binary changed during capture")
                shutil.copy2(BIN,worker)
            raw=subprocess.check_output([str(worker),str(n),"21"],text=True)
            capture=json.loads(raw)
            if len(capture["cells"])!=1: raise SystemExit("expected one isolated graph size per worker")
            cell=capture["cells"][0]
            if not capture["reuse_compaction_controls_pass"] or not cell["baseline_queries_exact"] or not cell["baseline_type_order_exact"]: raise SystemExit("baseline gate failed")
            for sample in cell["mutation_samples"]:
                for key in ("shared_semantics","eager_semantics","shared_order_semantics","eager_order_semantics"):
                    if len(sample[key])!=21 or not all(sample[key]): raise SystemExit(f"mutation gate failed: S={count} N={n} {sample['name']} {key}")
            rows.append({"replicate":replicate,"shards":count,"nodes":n,"capture":capture})
            print(f"captured replicate={replicate} shards={count} nodes={n}",flush=True)
    if source_hashes()!=inputs["source_sha256"]: raise SystemExit("source changed during capture")
    payload={"schema":"TypedGraphCowShardCountV7ReplicatedRaw","locked_inputs":inputs,"replicates":3,"rows":rows}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n"); print(OUT.relative_to(ROOT))
if __name__=="__main__": main()
