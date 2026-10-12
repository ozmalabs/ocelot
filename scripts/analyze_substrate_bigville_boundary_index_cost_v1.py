#!/usr/bin/env python3
"""Independent gates and cost summaries for the owner-boundary index probe."""
import hashlib,json,random,statistics
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_bigville_boundary_index_cost_v1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/bigville_boundary_index_cost_lock_20260926.json'
TOPO=('ring','star','random_connected');REPS=3;SAMPLES=31;SEED=20260927
STAGES=('runtime_partition_baseline','insert_cross_links','authored_evidence_update','delete_one_third','reweight_remaining','reinsert_deleted_pairs','remove_all_cross_links')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());runs=d['workers']
 checks={'raw_lock_matches':d['locked_inputs']==lock,'lock_sha_matches':d['lock_sha256']==sha(LOCK),'worker_count_9':len(runs)==9,'unique_pids':len({r['pid'] for r in runs})==9,'native_hash_matches':d['native']['sha256']==sha(Path(d['native']['path'])),'protocol_tag':d['protocol']=='BIGVILLE_BOUNDARY_INDEX_COST_V1','runner_hash_matches':lock['locked_inputs']['files_sha256']['scripts/substrate_bigville_boundary_index_cost_v1.py']==sha(ROOT/'scripts/substrate_bigville_boundary_index_cost_v1.py'),'analyzer_hash_matches':lock['locked_inputs']['files_sha256']['scripts/analyze_substrate_bigville_boundary_index_cost_v1.py']==sha(Path(__file__))}
 expected=[(t,r) for t in TOPO for r in range(REPS)];random.Random(SEED).shuffle(expected)
 checks['exact_randomized_schedule']=d['schedule']==[list(x) for x in expected]
 cells={(r['topology'],r['replicate']):r for r in runs};checks['balanced_topology_replicates']=len(cells)==9 and all((t,r) in cells for t in TOPO for r in range(REPS))
 stage_parity=True;owner_parity=True;timing_samples=True;sequence=True
 for r in runs:
  cps=r['checkpoints'];sequence &= [c['stage'] for c in cps]==list(STAGES) and len(cps)==7
  owner_parity &= r['owner_frame_count']==100 and r['owner_frame_sizes']==[5]*100 and all(c['owner_frame_count']==100 and c['owner_frame_sizes']==[5]*100 for c in cps)
  for c in cps:
   stage_parity &= c['profile']==c['incremental_profile']
   for k in ('owner_discovery_samples_ns','live_edge_extraction_samples_ns','boundary_rebuild_samples_ns','incremental_update_samples_ns'):
    timing_samples &= len(c[k])==SAMPLES and all(isinstance(x,int) and x>=0 for x in c[k])
 checks['seven_stage_sequence']=bool(sequence);checks['100_owner_frames_revalidated']=bool(owner_parity);checks['incremental_equals_live_full_rebuild']=bool(stage_parity);checks['31_timing_samples_per_operation']=bool(timing_samples)
 # Expected topology/boundary transitions are acquisition-independent integrity gates.
 expected_links={'ring':(100,100),'star':(99,99),'random_connected':(100,100)}
 transitions=True
 for t in TOPO:
  n,_=expected_links[t]
  for rep in range(REPS):
   cs=cells[t,rep]['checkpoints'];want=[0,n,n,n-len(range(0,n,3)),n-len(range(0,n,3)),n,0]
   transitions &= [c['profile']['undirected_cross_edges'] for c in cs]==want
   transitions &= cs[0]['profile']['active_boundary_frames']==0 and cs[1]['profile']['active_boundary_frames']==100 and cs[-1]['profile']['active_boundary_frames']==0
 checks['expected_link_sequence']=bool(transitions)
 summaries=[]
 for t in TOPO:
  for stage in STAGES:
   cs=[cells[t,r]['checkpoints'][i] for r in range(REPS) for i,s in enumerate(STAGES) if s==stage]
   def med(key):return statistics.median([statistics.median(c[key]) for c in cs])
   def span(key):
    xs=[x for c in cs for x in c[key]];return [min(xs),max(xs)]
   summaries.append({'topology':t,'stage':stage,'n_workers':len(cs),'full_graph_build_plus_initial_partition_ns_median':statistics.median(cells[t,r]['full_graph_build_and_initial_partition_ns'] for r in range(REPS)) if stage==STAGES[0] else None,'owner_discovery_median_ns':med('owner_discovery_samples_ns'),'owner_discovery_range_ns':span('owner_discovery_samples_ns'),'live_edge_extraction_median_ns':med('live_edge_extraction_samples_ns'),'live_edge_extraction_range_ns':span('live_edge_extraction_samples_ns'),'boundary_rebuild_median_ns':med('boundary_rebuild_samples_ns'),'boundary_rebuild_range_ns':span('boundary_rebuild_samples_ns'),'incremental_update_median_ns':med('incremental_update_samples_ns'),'incremental_update_range_ns':span('incremental_update_samples_ns'),'raw_graph_mutation_median_ns':statistics.median(c['raw_graph_mutation_ns'] for c in cs),'boundary_concepts':sum(len(v) for v in cs[0]['profile']['boundary_node_ids_by_frame'].values()),'undirected_cross_edges':cs[0]['profile']['undirected_cross_edges'],'max_fanout':cs[0]['profile']['max_frame_fanout']})
 out={'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'checks':checks,'all_checks_pass':all(checks.values()),'summaries':summaries,'claim_boundary':'nine fresh processes on one authored Bigville owner-frame workload; timing micro-measures for full graph build+partition, live ownership discovery, edge extraction, boundary rebuild and index updates; no closure, task-frequency or general complexity claim'}
 path=ROOT/'evaluation/reports/substrate_bigville_boundary_index_cost_v1_analysis_20260926.json';path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':str(path),'all_checks_pass':out['all_checks_pass'],'failed_checks':[k for k,v in checks.items() if not v],'summaries':summaries},indent=2))
if __name__=='__main__':main()
