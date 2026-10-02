#!/usr/bin/env python3
"""Source-locked semantic parity for CowPagedVec-backed graph mutations."""
from __future__ import annotations
import argparse, hashlib, json, platform, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CRATE = ROOT / "runners/dsl"
SOURCES = ("runners/dsl/src/cow_paged_vec.rs", "runners/dsl/src/cow_sharded_map.rs", "runners/dsl/src/graph.rs", "runners/dsl/src/bin/typed_graph_cow_mutation_semantics_probe_v3.rs", "runners/dsl/src/lib.rs", "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock")
def sha(p: Path) -> str: return "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
def output(cmd: list[str]) -> str: return subprocess.run(cmd, cwd=CRATE, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--sizes",nargs="+",type=int,default=[771,10771,50771]); ap.add_argument("--no-build",action="store_true"); ap.add_argument("--out",type=Path); a=ap.parse_args()
    if any(n<50 for n in a.sizes): ap.error("all sizes must be at least 50")
    if not a.no_build: output(["cargo","build","--release","--bin","typed_graph_cow_mutation_semantics_probe_v3"])
    binary=CRATE/"target/release/typed_graph_cow_mutation_semantics_probe_v3"
    rows=json.loads(output([str(binary),",".join(map(str,a.sizes))]))
    gates=("primary_unchanged","fork_matches_eager","nested_matches_eager","sibling_isolated","delete_append_id_reuse","derived_indexes_match_eager")
    if len(rows)!=27*len(a.sizes) or any(not all(r[g] for g in gates) for r in rows): raise RuntimeError("semantic gate failed")
    capture={"schema":"TypedGraphCowMutationSemanticsV3","host":{"platform":platform.platform(),"machine":platform.machine()},"toolchain":{"rustc":output(["rustc","--version"]),"cargo":output(["cargo","--version"])},"runner":{"path":str(Path(__file__).resolve()),"sha256":sha(Path(__file__).resolve())},"binary":{"path":str(binary.resolve()),"sha256":sha(binary)},"sources":{s:sha(ROOT/s) for s in SOURCES},"protocol":{"sizes":a.sizes,"topologies":["path","star_augmented","grid_augmented"],"operation_schedules":["attributes then retype then edge/delete/reuse","edge operations then retype then attributes then delete/reuse","delete/reuse then edge operations then attributes and retype"],"backends":["eager","shared_records","shared_graph_pages"],"mutations":["node attribute update and insertion","attribute removal","node retype","edge deletion","node deletion with incident-edge cascade","node append with freelist ID reuse","edge append","nested fork","divergent sibling mutation"],"semantic_oracle":"canonical graph and derived-index query signatures compared to eager controls independently for each topology and operation schedule; queries cover declared attribute values, type membership, edge-type buckets, and incoming/outgoing neighbours on base, main branch, nested branch, and sibling","limitations":["graph-level only; typed in/out adjacency buckets share CowShardedMap shards in shared_graph_pages, while other hash indexes and wider Substrate fields retain their current clone policies","three deterministic topology families with a shared path backbone and topology-specific type-5 edges","does not time operations or measure memory","no concurrent mutation"]},"rows":rows}
    rendered=json.dumps(capture,indent=2,sort_keys=True)+"\n"
    if a.out: a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(rendered,encoding="utf-8")
    else: print(rendered,end="")
    return 0
if __name__=="__main__": raise SystemExit(main())
