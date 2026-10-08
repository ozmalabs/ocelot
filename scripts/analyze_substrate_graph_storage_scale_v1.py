#!/usr/bin/env python3
"""Independent integrity and scaling summary for native graph storage v1."""
from __future__ import annotations
import hashlib,json,pathlib,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_graph_storage_scale_v1_20260928.json'
LOCK=ROOT/'evaluation/substrate_capability/graph_storage_scale_v1_lock_20260928.json'
OUT=ROOT/'evaluation/reports/substrate_graph_storage_scale_v1_analysis_20260928.json'
SIZES=(10_000,100_000,1_000_000)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def median(rows,key):return int(statistics.median(r[key] for r in rows))
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=raw.get('runs',[])
 checks={
  'runner_checks_all_pass':bool(raw.get('all_checks_pass')) and all(raw.get('checks',{}).values()),
  'six_worker_rows':len(runs)==6,
  'two_replicates_at_each_size':all(sum(r.get('n')==n for r in runs)==2 for n in SIZES),
  'unique_worker_processes':len({r.get('pid') for r in runs})==6,
  'all_workers_match_source_lock':all(r.get('before')==lock==r.get('after') for r in runs),
  'parent_post_snapshot_matches_lock':raw.get('locked_inputs')==lock==raw.get('post_run_inputs'),
  'exact_size_and_chain_counts':all(r.get('node_count')==r.get('n') and r.get('edge_count')==r.get('n')-1 for r in runs),
  'all_sampled_reads_pass':all(r.get('sampled_checks_pass') and all(x.get('exists') and x.get('type')=='StorageProbe' for x in r.get('sampled_node_reads',[])) and all(x.get('actual_tgts')==[x.get('expected_tgt')] for x in r.get('sampled_edge_reads',[])) for r in runs),
  'timings_positive':all(all(r.get(k,0)>0 for k in ('node_build_wall_ns','node_build_cpu_ns','edge_build_wall_ns','edge_build_cpu_ns')) for r in runs),
  'raw_worker_stderr_empty':all(not r.get('worker_stderr') for r in runs),
 }
 summaries=[]
 for n in SIZES:
  group=[r for r in runs if r.get('n')==n]
  if not group:continue
  deltas=[r['rss_after_edges_bytes']-r['rss_before_bytes'] for r in group]
  summaries.append({'nodes':n,'edges':n-1,'replicates':len(group),'median_node_build_wall_ns':median(group,'node_build_wall_ns'),'median_node_build_cpu_ns':median(group,'node_build_cpu_ns'),'median_edge_build_wall_ns':median(group,'edge_build_wall_ns'),'median_edge_build_cpu_ns':median(group,'edge_build_cpu_ns'),'median_total_build_wall_ns':median(group,'total_build_wall_ns'),'median_total_build_cpu_ns':median(group,'total_build_cpu_ns'),'median_rss_delta_bytes':int(statistics.median(deltas)),'rss_delta_bytes_by_worker':deltas,'median_rss_delta_bytes_per_node':int(statistics.median(deltas)/n),'peak_rss_bytes_by_worker':[r['peak_rss_bytes'] for r in group]})
 current_files=lock.get('files',{});current_match=all((ROOT/p).is_file() and sha(ROOT/p)==h for p,h in current_files.items())
 checks['locked_source_files_still_match_checkout']=current_match
 analysis={'schema_version':1,'analysis_id':'substrate-graph-storage-scale-v1-independent-analysis','raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'checks':checks,'all_checks_pass':all(checks.values()),'size_summaries':summaries,'interpretation':'Measurements cover direct Python-to-native graph mutation with empty node attributes and a directed chain only. RSS is process-level; timings include PyO3 calls, interning, and allocator effects. This is not a closure, inference, or natural-workload scale law.'}
 OUT.write_text(json.dumps(analysis,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'checks_passed':sum(checks.values()),'checks_total':len(checks),'all_checks_pass':analysis['all_checks_pass'],'size_summaries':summaries},indent=2))
 if not analysis['all_checks_pass']:raise SystemExit('graph storage independent analysis failed')
if __name__=='__main__':main()
