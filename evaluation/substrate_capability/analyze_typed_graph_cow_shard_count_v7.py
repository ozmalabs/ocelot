#!/usr/bin/env python3
"""Analyze TypedGraph shard-count profile v7."""
import hashlib,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parents[2]
RAW=ROOT/"evaluation/reports/typed_graph_cow_shard_count_v7_raw_20261006.json"
OUT=ROOT/"evaluation/reports/typed_graph_cow_shard_count_v7_analysis_20261006.json"
raw=json.loads(RAW.read_text()); med=statistics.median
rows=[]
for item in raw["rows"]:
 c=item["capture"]["cells"][0]
 for m in c["mutation_samples"]:
  rows.append({"replicate":item["replicate"],"shards":item["shards"],"nodes":c["nodes"],"mutation":m["name"],
   "shared_fork_ns_median":med(m["shared_fork_ns"]),"shared_write_ns_median":med(m["shared_write_ns"]),
   "shared_total_ns_median":med([a+b for a,b in zip(m["shared_fork_ns"],m["shared_write_ns"])]),
   "eager_fork_ns_median":med(m["eager_fork_ns"]),"eager_write_ns_median":med(m["eager_write_ns"]),
   "query_sweep_ns_median":med(c["query_sweep_ns"]),"fixture_rss_kb":c["fixture_rss_kb"],
   "post_run_rss_kb":c["post_run_rss_kb"],"hwm_kb":c["hwm_kb"]})
comparisons=[]
for n in (7164,16384,50771):
 base={}
 for mutation in ("set_attr","insert","delete","retype"):
  base[mutation]=[r for r in rows if r["nodes"]==n and r["shards"]==64 and r["mutation"]==mutation]
 for s in (128,256,512):
  for mutation,b in base.items():
   c=[r for r in rows if r["nodes"]==n and r["shards"]==s and r["mutation"]==mutation]
   b_write=med(r["shared_write_ns_median"] for r in b); c_write=med(r["shared_write_ns_median"] for r in c)
   b_total=med(r["shared_total_ns_median"] for r in b); c_total=med(r["shared_total_ns_median"] for r in c)
   b_query=med(r["query_sweep_ns_median"] for r in b); c_query=med(r["query_sweep_ns_median"] for r in c)
   comparisons.append({"nodes":n,"shards":s,"mutation":mutation,"baseline_shared_write_us":b_write/1000,
    "candidate_shared_write_us":c_write/1000,"write_ratio_candidate_over_64":c_write/b_write,
    "baseline_total_us":b_total/1000,"candidate_total_us":c_total/1000,
    "query_sweep_ratio_candidate_over_64":c_query/b_query,
    "baseline_fixture_rss_kb_median":med(r["fixture_rss_kb"] for r in b),
    "candidate_fixture_rss_kb_median":med(r["fixture_rss_kb"] for r in c),
    "candidate_hwm_kb_median":med(r["hwm_kb"] for r in c),
    "replicate_write_us_baseline":[r["shared_write_ns_median"]/1000 for r in b],
    "replicate_write_us_candidate":[r["shared_write_ns_median"]/1000 for r in c]})
doc={"raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"raw":RAW.relative_to(ROOT).as_posix(),
 "rows":rows,"comparisons_vs_64":comparisons,"interpretation":"Graph microbenchmark only; RSS page-granular and closure/natural prevalence not measured."}
OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n"); print(OUT)
for r in comparisons: print(f"N={r['nodes']} S={r['shards']} {r['mutation']} write={r['candidate_shared_write_us']:.1f}us ({r['write_ratio_candidate_over_64']:.2f}x of 64) query={r['query_sweep_ratio_candidate_over_64']:.2f}x")
