#!/usr/bin/env python3
"""Independent checks for the exploratory task-scope closure parity pilot."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/conversation_task_scope_parity_pilot_v1_20261003.json'
OUT=ROOT/'evaluation/reports/conversation_task_scope_parity_pilot_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 errors=[]
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());inputs=lock['locked_inputs']
 def req(ok,msg):
  if not ok:errors.append(msg)
 req(cap['locked_inputs']==inputs==cap['post_run_inputs'],'locked input drift')
 req(cap['checks'].get('three_fresh_workers') is True,'fresh worker gate failed')
 req(cap['checks'].get('three_paired_cases') is True,'paired case count mismatch')
 rows=[]
 for run in cap['runs']:
  req(run['replicate'] in (0,1,2),'unexpected replicate')
  for case in run['cases']:
   mono=case['monolithic'];part=case['partition_sweep'];paired=case['paired']
   req(mono['final_graph_digest']==sha_json(mono['final_graph']),'monolithic digest mismatch')
   req(part['final_graph_digest']==sha_json(part['final_graph']),'partition digest mismatch')
   cp=[a['graph_digest']==b['graph_digest'] for a,b in zip(mono['checkpoints'],part['checkpoints'])]
   req(len(mono['checkpoints'])==len(part['checkpoints']),'checkpoint count mismatch')
   req(paired['final_graph_equal']==(mono['final_graph_digest']==part['final_graph_digest']),'final equality flag mismatch')
   req(paired['checkpoint_graph_equal']==cp,'checkpoint equality flags mismatch')
   req(all(cp),'checkpoint state mismatch')
   req(paired['goal_status_equal']==([g['status'] for g in mono['goals']]==[g['status'] for g in part['goals']]),'goal status flag mismatch')
   req(paired['goal_status_equal'],'goal status mismatch')
   req(all(cp['closure'].get('status')=='fixed_point' for cp in mono['checkpoints']+part['checkpoints']),'non-fixed-point closure')
   req(all(not cp.get('deferred_effects_pending',False) for cp in part['checkpoints']),'deferred work remains')
   req(all(cp.get('scoped_calls',0)>0 for cp in part['checkpoints']),'missing scoped closure accounting')
   rows.append({'replicate':run['replicate'],'case_id':case['case_id'],'final_equal':paired['final_graph_equal'],
     'checkpoint_count':len(cp),'partition_scoped_calls':paired['partition_scoped_calls'],
     'monolithic_goal_statuses':[g['status'] for g in mono['goals']],
     'partition_goal_statuses':[g['status'] for g in part['goals']]})
 req(len(rows)==3,'independent row count mismatch')
 out={'schema':'ConversationTaskScopeParityPilotV1Analysis','gates_pass':not errors,'errors':errors,
  'paired_cases':rows,'summary':{'paired_case_count':len(rows),'final_state_matches':sum(r['final_equal'] for r in rows),
   'checkpoint_count':sum(r['checkpoint_count'] for r in rows),'scoped_calls':sum(r['partition_scoped_calls'] for r in rows)},
  'analysis_script_sha256':sha(__file__),
  'claim_boundary':cap['claim_boundary']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errors))
def sha_json(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
if __name__=='__main__':raise SystemExit(main())
