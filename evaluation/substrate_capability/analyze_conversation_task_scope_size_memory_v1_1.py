#!/usr/bin/env python3
"""Independent parity, schedule, work, and memory analysis for size/memory v1.1."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_size_memory_v1_1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/conversation_task_scope_size_memory_v1_1_20261003.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_size_memory_v1_1_analysis_20261003.json'
DOSES=(0,256,1024,4096,16384);POLICIES=('ascending','descending','outside_in')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def med(xs):return statistics.median(xs) if xs else None
def main():
 e=[]
 def req(x,m):
  if not x:e.append(m)
 lock=json.loads(LOCK.read_text())['locked_inputs'];cap=json.loads(CAP.read_text())
 req(cap.get('locked_inputs')==lock==cap.get('post_run_inputs'),'source lock drift')
 req(cap.get('checks',{}).get('source_stable') is True,'runner source stability failed')
 runs=cap.get('runs',[]);req(len(runs)==45,'expected 45 workers');req(len({r.get('pid') for r in runs})==45,'worker PIDs not unique')
 rows=[]
 for i,r in enumerate(runs):
  dose=DOSES[i//9];local=i%9;policy=POLICIES[local%3];rep=local//3
  req(r.get('worker_index')==i and r.get('decoy_count')==dose,'worker-dose assignment mismatch')
  req(r.get('scope_order_policy')==policy and r.get('replicate')==i//3,'order/replicate assignment mismatch')
  req(len(r.get('cases',[]))==1,'worker must contain one case')
  if not r.get('cases'):continue
  c=r['cases'][0];req(c.get('ownership_variant')=='aligned' and c.get('decoy_profile')=='shared_event_complete' and c.get('decoy_count')==dose,'workload mismatch')
  arms={k:c[k] for k in ('monolithic','partition_fallback','partition_anchor')};m=arms['monolithic']
  for name,a in arms.items():
   req(len(a.get('checkpoints',[]))==len(m.get('checkpoints',[])),f'{name} checkpoint count mismatch')
   req(all(cp.get('closure',{}).get('status')=='fixed_point' for cp in a.get('checkpoints',[])),f'{name} not fixed point')
   req(a.get('final_graph_digest')==m.get('final_graph_digest') and [cp.get('graph_digest') for cp in a.get('checkpoints',[])]==[cp.get('graph_digest') for cp in m.get('checkpoints',[])],f'{name} state mismatch')
  req([g.get('status') for g in arms['partition_anchor'].get('goals',[])]==[g.get('status') for g in m.get('goals',[])],'lifecycle mismatch')
  for cp in arms['partition_fallback']['checkpoints']:
   sc=cp.get('scale_counters',{})
   req(sc.get('scoped_declared_anchor_rule_matches',0)==0 and sc.get('scoped_anchor_rejected_rule_matches',0)==0,'fallback used anchor path')
   req(sc.get('scoped_full_fallback_rule_matches',0)>0,'fallback did not invoke full matcher')
  req(sum(cp.get('scale_counters',{}).get('scoped_declared_anchor_rule_matches',0) for cp in arms['partition_anchor']['checkpoints'])>0,'anchor path not exercised')
  stats={}
  for name,a in arms.items():
   cp=a['checkpoints'];stats[name]={'candidate_pairs':sum(int(x.get('candidate_pairs',0)) for x in cp),'term_evaluations':sum(int(x.get('term_evaluations',0)) for x in cp),'wall_ns':sum(int(x.get('wall_ns',0)) for x in cp),'peak_nodes':max((int(x.get('nodes',0)) for x in cp),default=0),'peak_edges':max((int(x.get('edges',0)) for x in cp),default=0)}
  rows.append({'worker_index':i,'decoy_count':dose,'scope_order_policy':policy,'replicate_within_size':rep,'peak_rss_kb':int(r.get('peak_rss_kb',0)),'checkpoint_count':len(m['checkpoints']),'arms':stats})
 req(len(rows)==45,'analysis row count mismatch')
 by={}
 for d in DOSES:
  group=[x for x in rows if x['decoy_count']==d];req(len(group)==9,f'expected nine runs at {d}')
  a={arm:{metric:sum(x['arms'][arm][metric] for x in group) for metric in ('candidate_pairs','term_evaluations','wall_ns')} for arm in ('monolithic','partition_fallback','partition_anchor')}
  a['graph']={'median_peak_nodes':med([x['arms']['partition_anchor']['peak_nodes'] for x in group]),'median_peak_edges':med([x['arms']['partition_anchor']['peak_edges'] for x in group])}
  a['process_memory']={'median_peak_rss_kb':med([x['peak_rss_kb'] for x in group]),'min_peak_rss_kb':min(x['peak_rss_kb'] for x in group),'max_peak_rss_kb':max(x['peak_rss_kb'] for x in group)}
  for metric in ('candidate_pairs','term_evaluations','wall_ns'):
   for base in ('monolithic','partition_fallback'):
    den=a[base][metric];a[f'anchor_{metric}_ratio_vs_{base}']=a['partition_anchor'][metric]/den if den else None
  by[str(d)]=a
 out={'schema':'ConversationTaskScopeSizeMemoryV1_1Analysis','gates_pass':not e,'errors':e,'workers':rows,'by_decoy_count':by,
  'memory_measurement':'Each worker runs one size, launches no trace arm, discards each full arm payload after extracting compact checkpoint summaries, samples ru_maxrss before output serialization, and emits a compact result. This is whole-worker high-water RSS across the three closure arms, not per-arm allocation.',
  'analysis_amendment':'The v1 analysis incorrectly expected replicate labels to restart at each size. Here the original runner schedule is checked as replicate blocks numbered by worker_index // 3; this v1.1 run uses the same schedule with compact summaries.',
  'claim_boundary':cap.get('claim_boundary'),'analysis_script_sha256':sha(__file__)}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'gates_pass':not e,'errors':e,'by_decoy_count':by},indent=2))
 return int(bool(e))
if __name__=='__main__':raise SystemExit(main())
