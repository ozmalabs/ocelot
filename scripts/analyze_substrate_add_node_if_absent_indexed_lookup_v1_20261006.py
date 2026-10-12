#!/usr/bin/env python3
"""Independent gates and paired summaries for indexed AddNodeIfAbsent v1."""
from __future__ import annotations
import gzip,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAP=ROOT/'evaluation/reports/add_node_if_absent_indexed_lookup_v1_20261006/capture.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/add_node_if_absent_indexed_lookup_v1_20261006_lock.json'
OUT=ROOT/'evaluation/reports/add_node_if_absent_indexed_lookup_v1_20261006/analysis.json'
d=json.loads(gzip.decompress(CAP.read_bytes()));lock=json.loads(LOCK.read_text())['locked_inputs'];rows=d['rows']
scale=[r for r in rows if r['kind']=='scale'];live=[r for r in rows if r['kind']=='live_route'];control=next((r for r in rows if r['kind']=='semantic_controls'),{})
checks={'capture_source_lock_stable':d['locked_inputs']==lock==d['post_run_inputs'],'83_records':len(rows)==83,'72_scale_workers':len(scale)==72,'10_live_route_workers':len(live)==10,
 'all_workers_source_stable':all(r.get('source_stable') for r in scale+live+[control]),
 'scale_worker_inputs_match_lock':all(r['before_inputs']==lock and r['after_inputs']==lock for r in scale),
 'five_timing_replicates_and_one_trace_per_scale_cell':all(sum(r['N']==n and r['M']==m and not r['diagnostic_trace'] for r in scale)==5 and sum(r['N']==n and r['M']==m and r['diagnostic_trace'] for r in scale)==1 for n in (512,4096,7164,16384) for m in (1,15,64)),
 'semantic_control_source_stable':bool(control.get('source_stable')) and control.get('before_inputs')==lock==control.get('after_inputs'),
 'semantic_controls_match_reference':bool(control.get('cases')) and all(c['same_digest'] and c['same_witness'] for c in control.get('cases',[])),
 'fork_parent_isolation_all_scale_workers':all(r.get('branch_parent_isolation') for r in scale),
 'diagnostic_traces_no_drops':all(a['trace'] is None or a['trace']['dropped']==0 for r in scale if r['diagnostic_trace'] for a in r['arms'].values()),
 'all_scale_workers_graph_parity':all(r['arms']['reference']['final_graph_digest']==r['arms']['indexed']['final_graph_digest'] and r['arms']['reference']['selected_concept_ids']==r['arms']['indexed']['selected_concept_ids'] and r['arms']['reference']['node_count']==r['arms']['indexed']['node_count'] and r['arms']['reference']['edge_count']==r['arms']['indexed']['edge_count'] for r in scale),
 'all_scale_progress_parity':all(r['arms']['reference']['progress']==r['arms']['indexed']['progress'] for r in scale),
 'live_task_oracle_all_arms':all(r.get('task_oracle_pass') for r in live),
 'live_index_probe_valid':all(r['arm']!='indexed' or (r['index_setup'].get('index_declared') and r['index_setup'].get('index_probe_pass')) for r in live),
 'live_source_inputs_match_lock':all(r['source_locked_inputs']['harvest_inputs']==lock['harvest_inputs'] and r['post_inputs']==lock for r in live),
 'live_graph_digest_and_reply_parity':all((lambda q:len(q)==2 and q[0]['final_graph_digest']==q[1]['final_graph_digest'] and q[0]['reply']==q[1]['reply'])([r for r in live if r['replicate']==rep]) for rep in range(5))}
cell_summary=[]
for n in (512,4096,7164,16384):
 for m in (1,15,64):
  cell=[r for r in scale if r['N']==n and r['M']==m];timed=[r for r in cell if not r['diagnostic_trace']]
  ref=[r['arms']['reference']['closure_wall_ns'] for r in timed];idx=[r['arms']['indexed']['closure_wall_ns'] for r in timed]
  index_build=[r['index_build']['wall_ns'] for r in timed]
  ref_fork=[r['forks']['reference']['wall_ns'] for r in timed];idx_fork=[r['forks']['indexed_state']['wall_ns'] for r in timed]
  per_pair=[(a-b)/a*100 for a,b in zip(ref,idx)]
  row={'N':n,'M':m,'hits':cell[0]['hit_count'],'misses':cell[0]['miss_count'],'replicates':len(timed),
   'reference_closure_median_ns':statistics.median(ref),'indexed_warm_closure_median_ns':statistics.median(idx),
   'indexed_warm_closure_reduction_median_paired_pct':statistics.median(per_pair),
   'indexed_build_median_ns':statistics.median(index_build),
   'indexed_first_use_median_ns':statistics.median([a+b for a,b in zip(index_build,idx)]),
   'reference_fork_median_ns':statistics.median(ref_fork),'indexed_state_fork_median_ns':statistics.median(idx_fork),
   'indexed_fork_over_reference_pct':(statistics.median(idx_fork)/statistics.median(ref_fork)-1)*100 if statistics.median(ref_fork) else None,
   'index_build_rss_delta_median_bytes':statistics.median(r['rss']['after_index_build_bytes']-r['rss']['after_unindexed_forks_bytes'] for r in timed if r['rss']['after_index_build_bytes'] is not None and r['rss']['after_unindexed_forks_bytes'] is not None),
   'process_peak_rss_median_bytes':statistics.median(r['rss']['process_peak_bytes'] for r in timed)}
  diag=next(r for r in cell if r['diagnostic_trace']);rt=diag['arms']['reference']['trace'];it=diag['arms']['indexed']['trace'];row['diagnostic_trace']={'reference_candidate_reads':rt['counts_by_kind'].get('effect_type_candidate_read',0),
   'reference_attr_compare_reads':rt['counts_by_kind'].get('effect_attr_compare_read',0),'indexed_candidate_reads':it['counts_by_kind'].get('effect_type_candidate_read',0),
   'indexed_attr_compare_reads':it['counts_by_kind'].get('effect_attr_compare_read',0),'indexed_queries':it['counts_by_kind'].get('effect_attr_index_query',0),
   'trace_counts_by_kind_reference':rt['counts_by_kind'],'trace_counts_by_kind_indexed':it['counts_by_kind']}
  expected_candidates=(n-cell[0]['hit_count'])*cell[0]['hit_count']+cell[0]['hit_count']*(cell[0]['hit_count']+1)//2+cell[0]['miss_count']*n+cell[0]['miss_count']*(cell[0]['miss_count']-1)//2
  row['expected_reference_candidate_reads']=expected_candidates
  row['diagnostic_candidate_count_conservation']=rt['counts_by_kind'].get('effect_type_candidate_read',0)==expected_candidates
  row['indexed_miss_and_unique_fastpath']=it['counts_by_kind'].get('effect_type_candidate_read',0)==0 and it['counts_by_kind'].get('effect_attr_compare_read',0)==0 and it['counts_by_kind'].get('effect_attr_index_query',0)==m
  cell_summary.append(row)
checks['reference_candidate_counter_formula']=all(x['diagnostic_candidate_count_conservation'] for x in cell_summary)
checks['index_fastpath_covers_misses_and_unique_hits']=all(x['indexed_miss_and_unique_fastpath'] for x in cell_summary)
live_summary=[]
for rep in range(5):
 pair={r['arm']:r for r in live if r['replicate']==rep}
 live_summary.append({'replicate':rep,'order':'/'.join(r['arm'] for r in live if r['replicate']==rep),
  'reference_task_wall_ns':pair['reference']['task_wall_ns'],'indexed_task_wall_ns':pair['indexed']['task_wall_ns'],
  'indexed_build_wall_ns':pair['indexed']['index_setup']['wall_ns'],'indexed_first_use_total_ns':pair['indexed']['task_wall_ns']+pair['indexed']['index_setup']['wall_ns'],
  'paired_task_wall_reduction_pct':(pair['reference']['task_wall_ns']-pair['indexed']['task_wall_ns'])/pair['reference']['task_wall_ns']*100,
  'paired_first_use_total_reduction_pct':(pair['reference']['task_wall_ns']-(pair['indexed']['task_wall_ns']+pair['indexed']['index_setup']['wall_ns']))/pair['reference']['task_wall_ns']*100,
  'graph_parity':pair['reference']['final_graph_digest']==pair['indexed']['final_graph_digest']})
out={'schema':'AddNodeIfAbsentIndexedLookupV1Analysis','integrity_checks':checks,'integrity_pass':all(checks.values()),'scale_cells':cell_summary,
 'live_route_pairs':live_summary,'live_route_summary':{'utility_passes':sum(r['task_oracle_pass'] for r in live),'workers':len(live),
  'reference_wall_median_ns':statistics.median(r['task_wall_ns'] for r in live if r['arm']=='reference'),
  'indexed_wall_median_ns':statistics.median(r['task_wall_ns'] for r in live if r['arm']=='indexed'),
  'indexed_build_median_ns':statistics.median(r['index_setup']['wall_ns'] for r in live if r['arm']=='indexed'),
  'indexed_first_use_total_median_ns':statistics.median(r['task_wall_ns']+r['index_setup']['wall_ns'] for r in live if r['arm']=='indexed')},
 'semantic_controls':control.get('cases',[]),'claim_boundary':'Controlled single-attribute AddNodeIfAbsent scaling plus one authored full-seed unknown-word route. Does not test all effect families, natural workload prevalence, arbitrary index key/value distributions, or general tractability.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'integrity_pass':out['integrity_pass'],'integrity_checks':checks,'scale_pct':[{k:x[k] for k in ('N','M','indexed_warm_closure_reduction_median_paired_pct','indexed_first_use_median_ns','indexed_fork_over_reference_pct','diagnostic_trace')} for x in cell_summary],'live':out['live_route_summary']},indent=2))
if not out['integrity_pass']:raise SystemExit(1)
