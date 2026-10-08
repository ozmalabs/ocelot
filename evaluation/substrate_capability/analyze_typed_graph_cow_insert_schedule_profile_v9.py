#!/usr/bin/env python3
"""Analyze v9 split insert timings against v7's combined timing."""
import hashlib,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parents[2]
RAW=ROOT/"evaluation/reports/typed_graph_cow_insert_schedule_profile_v9_raw_20261006.json"
V7=ROOT/"evaluation/reports/typed_graph_cow_shard_count_v7_raw_20261006.json"
OUT=ROOT/"evaluation/reports/typed_graph_cow_insert_schedule_profile_v9_analysis_20261006.json"
med=statistics.median; raw=json.loads(RAW.read_text()); v7=json.loads(V7.read_text()); rows=[]
for x in raw["rows"]:
 cell=x["capture"]["cells"][0]
 ins=next(r for r in cell["mutation_samples"] if r["name"]=="insert")
 rows.append({"replicate":x["replicate"],"nodes":x["nodes"],"shards":x["shards"],
  "shared_total_ns":med(ins["shared_write_ns"]),"shared_op_ns":med(ins["shared_insert_op_ns"]),"shared_lookup_ns":med(ins["shared_insert_lookup_ns"]),
  "eager_total_ns":med(ins["eager_write_ns"]),"eager_op_ns":med(ins["eager_insert_op_ns"]),"eager_lookup_ns":med(ins["eager_insert_lookup_ns"])})
v7rows=[]
for x in v7["rows"]:
 c=x["capture"]["cells"][0]
 ins=next(r for r in c["mutation_samples"] if r["name"]=="insert")
 v7rows.append({"replicate":x["replicate"],"nodes":x["nodes"],"shards":x["shards"],"shared_total_ns":med(ins["shared_write_ns"])})
summary=[]
for n in (7164,50771):
 for s in (64,128,256,512):
  cur=[r for r in rows if r["nodes"]==n and r["shards"]==s]
  old=[r for r in v7rows if r["nodes"]==n and r["shards"]==s]
  summary.append({"nodes":n,"shards":s,"shared_operation_us":med(r["shared_op_ns"] for r in cur)/1000,
   "shared_lookup_us":med(r["shared_lookup_ns"] for r in cur)/1000,"shared_total_us":med(r["shared_total_ns"] for r in cur)/1000,
   "v7_combined_us":med(r["shared_total_ns"] for r in old)/1000,
   "eager_operation_us":med(r["eager_op_ns"] for r in cur)/1000,"eager_lookup_us":med(r["eager_lookup_ns"] for r in cur)/1000,
   "replicate_shared_operation_us":[r["shared_op_ns"]/1000 for r in cur],"replicate_shared_lookup_us":[r["shared_lookup_ns"]/1000 for r in cur],
   "replicate_shared_total_us":[r["shared_total_ns"]/1000 for r in cur],"replicate_v7_combined_us":[r["shared_total_ns"]/1000 for r in old]})
doc={"raw":RAW.relative_to(ROOT).as_posix(),"raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"v7_raw":V7.relative_to(ROOT).as_posix(),"rows":rows,"summary":summary,
 "interpretation":"V9 reproduces v7 operation order and splits insert_node from exact post-insert lookup. V7 versus V9 outer totals are cross-capture descriptive; V9 nested timings identify phase cost.","limits":"Synthetic graph mutation only; does not establish closure or live route performance."}
OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n"); print(OUT)
for r in summary: print(f"N={r['nodes']} S={r['shards']} v7={r['v7_combined_us']:.2f}us v9op={r['shared_operation_us']:.2f}us lookup={r['shared_lookup_us']:.2f}us outer={r['shared_total_us']:.2f}us")
