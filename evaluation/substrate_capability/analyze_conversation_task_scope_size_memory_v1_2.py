#!/usr/bin/env python3
"""Independent analysis of per-arm fresh-process matcher scaling."""
import hashlib,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_size_memory_v1_2_lock_20261003.json'
CAP=ROOT/'evaluation/reports/conversation_task_scope_size_memory_v1_2_20261003.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_size_memory_v1_2_analysis_20261003.json'
DOSES=(0,256,1024,4096,16384);POLICIES=('ascending','descending','outside_in');ARMS=('monolithic','partition_fallback','partition_anchor')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def med(x):return statistics.median(x) if x else None
def main():
 errors=[]
 def req(ok,msg):
  if not ok:errors.append(msg)
 lock=json.loads(LOCK.read_text())['locked_inputs'];cap=json.loads(CAP.read_text())
 req(cap.get('locked_inputs')==lock==cap.get('post_run_inputs'),'source lock drift')
 req(cap.get('checks',{}).get('source_stable') is True,'runner source check failed')
 runs=cap.get('runs',[]);req(len(runs)==135,'expected 135 arm-isolated workers');req(len({r.get('pid') for r in runs})==135,'worker PIDs not unique')
 cells={}
 for i,r in enumerate(runs):
  dose=DOSES[i//27];slot=(i//3)%9;arm=ARMS[i%3];policy=POLICIES[slot%3];rep=slot//3
  req(r.get('worker_index')==i and r.get('decoy_count')==dose and r.get('arm')==arm,'worker assignment mismatch')
  req(r.get('scope_order_policy')==policy and r.get('replicate')==rep,'schedule assignment mismatch')
  key=(dose,policy,rep);cells.setdefault(key,{})
  req(arm not in cells[key],'duplicate arm in matched cell');cells[key][arm]=r
  result=r.get('result',{});cps=result.get('checkpoints',[])
  req(bool(cps),'empty checkpoint results')
  req(all(cp.get('closure',{}).get('status')=='fixed_point' for cp in cps),'closure not at fixed point')
  if arm=='partition_fallback':
   for cp in cps:
    sc=cp.get('scale_counters',{});req(sc.get('scoped_declared_anchor_rule_matches',0)==0 and sc.get('scoped_anchor_rejected_rule_matches',0)==0,'fallback used anchor path')
    req(sc.get('scoped_full_fallback_rule_matches',0)>0,'fallback did not use full matcher')
  if arm=='partition_anchor':req(sum(cp.get('scale_counters',{}).get('scoped_declared_anchor_rule_matches',0) for cp in cps)>0,'anchor path not exercised')
 req(len(cells)==45,'matched size/order/replicate cell count mismatch')
 for key,arms in cells.items():
  req(set(arms)==set(ARMS),f'missing arm at {key}')
  if set(arms)!=set(ARMS):continue
  ref=arms['monolithic']['result'];digests=[x.get('graph_digest') for x in ref.get('checkpoints',[])];final=ref.get('final_graph_digest');statuses=[g.get('status') for g in ref.get('goals',[])]
  for arm in ('partition_fallback','partition_anchor'):
   val=arms[arm]['result'];req(val.get('final_graph_digest')==final and [x.get('graph_digest') for x in val.get('checkpoints',[])]==digests,f'{arm} state mismatch at {key}')
   req([g.get('status') for g in val.get('goals',[])]==statuses,f'{arm} lifecycle mismatch at {key}')
 rows=[];by={}
 for dose in DOSES:
  group=[r for r in runs if r['decoy_count']==dose]
  arm_data={}
  for arm in ARMS:
   selected=[r for r in group if r['arm']==arm]
   cps=[cp for r in selected for cp in r['result']['checkpoints']]
   arm_data[arm]={'worker_count':len(selected),'candidate_pairs':sum(int(x.get('candidate_pairs',0)) for x in cps),
    'term_evaluations':sum(int(x.get('term_evaluations',0)) for x in cps),'wall_ns':sum(int(x.get('wall_ns',0)) for x in cps),
    'median_peak_rss_kb':med([int(r.get('peak_rss_kb',0)) for r in selected]),'min_peak_rss_kb':min((int(r.get('peak_rss_kb',0)) for r in selected),default=None),
    'max_peak_rss_kb':max((int(r.get('peak_rss_kb',0)) for r in selected),default=None),
    'median_peak_nodes':med([max((int(x.get('nodes',0)) for x in r['result']['checkpoints']),default=0) for r in selected]),
    'median_peak_edges':med([max((int(x.get('edges',0)) for x in r['result']['checkpoints']),default=0) for r in selected])}
  anchor=arm_data['partition_anchor']
  for metric in ('candidate_pairs','term_evaluations','wall_ns','median_peak_rss_kb'):
   for base in ('monolithic','partition_fallback'):
    denominator=arm_data[base][metric];anchor[f'{metric}_ratio_vs_{base}']=anchor[metric]/denominator if denominator else None
  by[str(dose)]=arm_data
 req(cap.get('checks',{}).get('one_hundred_thirty_five_unique_workers') is True and cap.get('checks',{}).get('one_hundred_thirty_five_cells') is True,'runner integrity checks failed')
 out={'schema':'ConversationTaskScopeSizeMemoryV1_2Analysis','gates_pass':not errors,'errors':errors,'by_decoy_count':by,'matched_cells':len(cells),
  'memory_definition':'ru_maxrss sampled in a fresh process that performs exactly one closure arm at one graph size; includes interpreter, input graph construction, graph representation/indexes, closure temporary memory, and compact summary objects. It is not a native-only allocation measure.',
  'claim_boundary':cap.get('claim_boundary'),'analysis_script_sha256':sha(__file__)}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'gates_pass':out['gates_pass'],'errors':errors,'by_decoy_count':by},indent=2))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
