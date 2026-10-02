#!/usr/bin/env python3
"""Independent source and semantic audit of mutation/topology panel."""
from __future__ import annotations
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CAP=ROOT/"evaluation/reports/cow_concurrent_mutation_scale_v1.json"
RUNNER="evaluation/substrate_capability/cow_concurrent_mutation_scale_v1.py";ANALYZER="scripts/analyze_cow_concurrent_mutation_scale_v1.py"
def sha(p):return "sha256:"+hashlib.sha256(Path(p).read_bytes()).hexdigest()
def med(vals):return statistics.median(vals)
def main():
 d=json.loads(CAP.read_text())
 if d.get("schema")!="CowConcurrentMutationScaleCaptureV1":raise SystemExit("bad capture schema")
 if d["source_sha256"].get(RUNNER)!=sha(ROOT/RUNNER) or d["source_sha256"].get(ANALYZER)!=sha(ROOT/ANALYZER):raise SystemExit("runner/analyzer source hash mismatch")
 for p,h in d["source_sha256"].items():
  if sha(ROOT/p)!=h:raise SystemExit(f"captured source changed: {p}")
 binary=Path(d["probe_binary"]["path"])
 if binary.exists() and sha(binary)!=d["probe_binary"]["sha256"]:raise SystemExit("probe binary hash mismatch")
 rows=d["measurements"]["rows"]
 if len(rows)!=144:raise SystemExit(f"expected 144 rows, got {len(rows)}")
 gates=("all_semantics_pass","primary_unchanged","all_live_bytes_increased","cancel_reduced_live_bytes","adjusted_reclamation_pass")
 if not all(all(r.get(g) is True for g in gates) and r["mutation_adjusted_after_drop_bytes"]==0 for r in rows):raise SystemExit("semantic or allocator gate failed")
 cells=[]
 for top in ("path","star","grid"):
  for n in (10000,50000):
   for density in (1,10):
    for fanout in (4,16):
     pair={}
     for backend in ("shared_snapshot","eager_copy"):
      cell=[r for r in rows if (r["topology"],r["size_nodes"],r["write_density_percent"],r["fanout"],r["backend"])==(top,n,density,fanout,backend)]
      if len(cell)!=3:raise SystemExit(f"repeat mismatch: {top=} {n=} {density=} {fanout=} {backend=}")
      pair[backend]={r["repeat"]:r for r in cell}
     for rep in range(3):
      a,b=pair["shared_snapshot"][rep],pair["eager_copy"][rep]
      if a["branch_added_ids"]!=b["branch_added_ids"]:raise SystemExit("branch ID parity mismatch")
      if (a["target_nodes"],a["payload_bytes"])!=(b["target_nodes"],b["payload_bytes"]):raise SystemExit("paired workload mismatch")
     s=list(pair["shared_snapshot"].values());e=list(pair["eager_copy"].values())
     sm,em=med([r["all_live_delta_bytes"] for r in s]),med([r["all_live_delta_bytes"] for r in e])
     cells.append({"topology":top,"size_nodes":n,"write_density_percent":density,"fanout":fanout,"repeats":3,
      "target_nodes":s[0]["target_nodes"],"payload_bytes":s[0]["payload_bytes"],
      "shared_median_all_live_mib":sm/1048576,"eager_median_all_live_mib":em/1048576,
      "shared_median_after_cancel_mib":med([r["after_cancel_delta_bytes"] for r in s])/1048576,
      "eager_median_after_cancel_mib":med([r["after_cancel_delta_bytes"] for r in e])/1048576,
      "shared_median_mutation_increment_mib":med([r["mutation_adjusted_all_live_bytes"] for r in s])/1048576,
      "eager_median_mutation_increment_mib":med([r["mutation_adjusted_all_live_bytes"] for r in e])/1048576,
      "shared_median_mutation_increment_after_cancel_mib":med([r["mutation_adjusted_after_cancel_bytes"] for r in s])/1048576,
      "eager_median_mutation_increment_after_cancel_mib":med([r["mutation_adjusted_after_cancel_bytes"] for r in e])/1048576,
      "shared_median_wave_ms":med([r["wall_us"] for r in s])/1000,
      "eager_median_wave_ms":med([r["wall_us"] for r in e])/1000,
      "eager_to_shared_live_allocation_ratio":em/sm if sm else None,
      "mutation_adjusted_reclamation_max_abs_bytes":max(abs(r["mutation_adjusted_after_drop_bytes"]) for r in s+e),
      "all_gates_pass":True})
 out={"schema":"CowConcurrentMutationScaleAnalysisV1","capture":str(CAP),"row_count":len(rows),"cell_count":len(cells),
  "all_semantic_and_allocator_gates_pass":True,"cells":cells,
  "claim_boundary":"concurrent native branch mutation on path/star/grid synthetic graphs; requested System allocator payload and wave time only, one host; not natural-task or serving evidence"}
 dest=ROOT/"evaluation/reports/cow_concurrent_mutation_scale_v1_analysis.json";dest.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"rows":len(rows),"cells":len(cells),"all_gates_pass":True,"analysis":str(dest.relative_to(ROOT))},sort_keys=True))
if __name__=="__main__":main()
