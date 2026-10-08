#!/usr/bin/env python3
"""Capture separated TypedGraph insertion and lookup costs for four shard counts."""
import argparse,hashlib,json,pathlib,platform,shutil,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]; CRATE=ROOT/"runners/dsl"
NAME="typed_graph_insert_phase_profile_v8"; BIN=CRATE/"target/release"/NAME
CONFIGS=((64,None),(128,"cow_shards_128"),(256,"cow_shards_256"),(512,"cow_shards_512"))
SOURCES=("runners/dsl/src/graph.rs","runners/dsl/src/cow_sharded_map.rs","runners/dsl/src/bin/typed_graph_insert_phase_profile_v8.rs","runners/dsl/Cargo.toml","runners/dsl/Cargo.lock",
 "docs/research/engine_substrate/TYPED_GRAPH_INSERT_PHASE_PROFILE_V8_PREREG_20261006.md","evaluation/substrate_capability/typed_graph_insert_phase_profile_v8.py","evaluation/substrate_capability/analyze_typed_graph_insert_phase_profile_v8.py")
LOCK=ROOT/"evaluation/substrate_capability/typed_graph_insert_phase_profile_v8_lock_20261006.json"
OUT=ROOT/"evaluation/reports/typed_graph_insert_phase_profile_v8_raw_20261006.json"
TMP=pathlib.Path("/tmp/ocelot_typed_graph_insert_phase_profile_v8")
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def cmd(args): return subprocess.check_output(args,cwd=CRATE,text=True,stderr=subprocess.DEVNULL).strip()
def build(feature):
 args=["cargo","build","--release","--no-default-features"]
 if feature: args += ["--features",feature]
 args += ["--bin",NAME]
 subprocess.run(args,cwd=CRATE,check=True,stdout=subprocess.DEVNULL)
 return sha(BIN)
def sources(): return {p:sha(ROOT/p) for p in SOURCES}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--lock",action="store_true"); args=ap.parse_args()
 TMP.mkdir(parents=True,exist_ok=True); binaries={}
 for count,feature in CONFIGS:
  worker=TMP/f"worker_{count}"
  if not worker.exists():
   binaries[str(count)]=build(feature); shutil.copy2(BIN,worker)
  else: binaries[str(count)]=sha(worker)
 inputs={"source_sha256":sources(),"binary_sha256_by_shards":binaries,"rustc":cmd(["rustc","--version"]),"cargo":cmd(["cargo","--version"]),"platform":platform.platform()}
 if args.lock: LOCK.write_text(json.dumps(inputs,indent=2,sort_keys=True)+"\n"); print(LOCK.relative_to(ROOT)); return
 if not LOCK.exists() or json.loads(LOCK.read_text())!=inputs: raise SystemExit("missing/stale source lock")
 rows=[]; sizes=(7164,50771)
 for rep in range(3):
  for size_i,n in enumerate(sizes):
   shift=(rep+size_i)%len(CONFIGS); order=CONFIGS[shift:]+CONFIGS[:shift]
   for count,_feature in order:
    worker=TMP/f"worker_{count}"
    if sha(worker)!=binaries[str(count)]: raise SystemExit("worker binary hash mismatch")
    c=json.loads(subprocess.check_output([str(worker),str(n),"41"],text=True))
    if not c["semantics_pass"] or c["repeats"]!=41 or c["shards"]!=count: raise SystemExit("worker semantic/config gate failed")
    rows.append({"replicate":rep,"shards":count,"nodes":n,"capture":c})
    print(f"captured rep={rep} N={n} shards={count}",flush=True)
 if sources()!=inputs["source_sha256"]: raise SystemExit("source changed during capture")
 OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps({"schema":"TypedGraphInsertPhaseProfileV8Raw","locked_inputs":inputs,"rows":rows},indent=2,sort_keys=True)+"\n"); print(OUT.relative_to(ROOT))
if __name__=="__main__": main()
