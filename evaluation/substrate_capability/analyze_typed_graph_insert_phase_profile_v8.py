#!/usr/bin/env python3
"""Analyze separated insertion and lookup times from v8."""
import hashlib,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parents[2]
RAW=ROOT/"evaluation/reports/typed_graph_insert_phase_profile_v8_raw_20261006.json"
OUT=ROOT/"evaluation/reports/typed_graph_insert_phase_profile_v8_analysis_20261006.json"
raw=json.loads(RAW.read_text()); med=statistics.median; rows=[]
for x in raw["rows"]:
 c=x["capture"]
 rows.append({"replicate":x["replicate"],"nodes":x["nodes"],"shards":x["shards"],
  "fork_ns_median":med(c["fork_ns"]),"indexed_insert_ns_median":med(c["indexed_insert_ns"]),
  "indexed_lookup_ns_median":med(c["indexed_lookup_ns"]),"noindex_insert_ns_median":med(c["noindex_insert_ns"]),
  "indexed_insert_iqr_ns":[med(sorted(c["indexed_insert_ns"])[:20]),med(sorted(c["indexed_insert_ns"])[21:])],
  "lookup_iqr_ns":[med(sorted(c["indexed_lookup_ns"])[:20]),med(sorted(c["indexed_lookup_ns"])[21:])]})
summary=[]
for n in (7164,50771):
 base={s:[r for r in rows if r["nodes"]==n and r["shards"]==s] for s in (64,128,256,512)}
 for s,rs in base.items():
  indexed=med(r["indexed_insert_ns_median"] for r in rs)
  noindex=med(r["noindex_insert_ns_median"] for r in rs)
  lookup=med(r["indexed_lookup_ns_median"] for r in rs)
  summary.append({"nodes":n,"shards":s,"indexed_insert_us":indexed/1000,"noindex_insert_us":noindex/1000,
   "indexed_over_noindex_ratio":indexed/noindex,"post_insert_lookup_us":lookup/1000,
   "fork_us":med(r["fork_ns_median"] for r in rs)/1000,
   "replicate_indexed_insert_us":[r["indexed_insert_ns_median"]/1000 for r in rs],
   "replicate_noindex_insert_us":[r["noindex_insert_ns_median"]/1000 for r in rs],
   "replicate_lookup_us":[r["indexed_lookup_ns_median"]/1000 for r in rs]})
doc={"raw":RAW.relative_to(ROOT).as_posix(),"raw_sha256":hashlib.sha256(RAW.read_bytes()).hexdigest(),"worker_rows":rows,"summary":summary,
 "interpretation":"The indexed insertion phase includes index maintenance; the post-insert lookup is timed separately. The no-index arm estimates insertion costs without attribute-index maintenance.","limits":"Diagnostic only; do not infer overall engine benefit or select production shard count."}
OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n"); print(OUT)
for x in summary: print(f"N={x['nodes']} S={x['shards']} indexed_insert={x['indexed_insert_us']:.2f}us noindex={x['noindex_insert_us']:.2f}us ratio={x['indexed_over_noindex_ratio']:.2f} lookup={x['post_insert_lookup_us']:.2f}us fork={x['fork_us']:.2f}us")
