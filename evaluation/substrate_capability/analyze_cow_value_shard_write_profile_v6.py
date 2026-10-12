#!/usr/bin/env python3
"""Analyze the locked v6 value-shard write profile."""
import json, pathlib, statistics
ROOT=pathlib.Path(__file__).resolve().parents[2]
RAW=ROOT/"evaluation/reports/cow_value_shard_write_profile_v6_raw_20261006.json"
OUT=ROOT/"evaluation/reports/cow_value_shard_write_profile_v6_analysis_20261006.json"
def med(xs): return statistics.median(xs)
data=json.loads(RAW.read_text())
summaries=[]
for row in data["rows"]:
    for key in ("fork_ns","write_ns","total_ns"):
        row[key+"_median"]=med(row[key])
    summaries.append({k:row[k] for k in ("n","shards","arm","reps","fork_ns_median","write_ns_median","total_ns_median","root_refs_copied","selected_shard_entries","rss_before_kb","rss_fixture_kb","rss_after_kb","hwm_kb")})
groups={(r["n"],r["shards"]):r for r in data["rows"] if r["arm"]=="cow"}
eager={(r["n"],r["shards"]):r for r in data["rows"] if r["arm"]=="eager"}
comparisons=[]
for key,c in groups.items():
    e=eager[key]
    comparisons.append({"n":key[0],"shards":key[1],"cow_total_ns_median":med(c["total_ns"]),"eager_total_ns_median":med(e["total_ns"]),"total_speedup":med(e["total_ns"])/med(c["total_ns"]),"cow_write_ns_median":med(c["write_ns"]),"eager_write_ns_median":med(e["write_ns"]),"estimated_entries_copied":c["selected_shard_entries"],"mean_shard_occupancy":key[0]/key[1],"max_shard_occupancy":max(c["shard_lengths"]),"p95_shard_occupancy":sorted(c["shard_lengths"])[int(.95*(len(c["shard_lengths"])-1))],"cow_rss_delta_kb":c["rss_after_kb"]-c["rss_fixture_kb"],"eager_rss_delta_kb":e["rss_after_kb"]-e["rss_fixture_kb"]})
doc={"raw":RAW.relative_to(ROOT).as_posix(),"raw_sha256":__import__('hashlib').sha256(RAW.read_bytes()).hexdigest(),"interpretation":"Direct component profile; timings and RSS are descriptive, not end-to-end graph claims.","rows":summaries,"comparisons":comparisons}
OUT.write_text(json.dumps(doc,indent=2)+"\n")
print(OUT)
for r in comparisons: print(f"N={r['n']} S={r['shards']} entries={r['estimated_entries_copied']} COW={r['cow_total_ns_median']/1000:.1f}us eager={r['eager_total_ns_median']/1000:.1f}us ratio={r['total_speedup']:.1f}x")
