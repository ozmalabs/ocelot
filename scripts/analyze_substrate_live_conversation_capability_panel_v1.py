#!/usr/bin/env python3
"""Independent integrity and per-task summary for live capability panel v1."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/live_conversation_capability_panel_v1_20260927.json'
LOCK=ROOT/'evaluation/substrate_capability/live_conversation_capability_panel_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/live_conversation_capability_panel_v1_analysis_20260927.json'
TASKS=('scene_description','held_self_knowledge_answer','self_report_action','unknown_word_clarification','concern_authoring')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stat(v):return {'median':statistics.median(v),'min':min(v),'max':max(v),'replicates':v}
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];runs=d['runs'];integrity={'ten_workers':len(runs)==10,'unique_worker_pids':len({r.get('pid') for r in runs})==10,'two_workers_per_task':all(sum(r.get('condition')==k for r in runs)==2 for k in TASKS),'every_worker_source_stable':all(r.get('source_stable') and r.get('locked_inputs')==lock==r.get('post_run_inputs') for r in runs),'every_worker_full_seed_boot':all(r.get('boot_loaded',0)>0 for r in runs),'parent_lock_stable':d['locked_inputs']==d['post_run_inputs']==lock}
 by_task={}
 for task in TASKS:
  rs=[r for r in runs if r.get('condition')==task];items=[]
  for r in rs:
   turn=r.get('turns',[{}])[0];act_routes=[x.get('route') for x in r.get('action_results',[])];goals=turn.get('goals',[]);outs=turn.get('outbound_messages',[])
   items.append({'replicate':r['replicate'],'reply':r.get('reply'),'action_routes':act_routes,'interpretation':turn.get('interpretation',{}),'communication_route':turn.get('communication_route'),
    'goal_kinds':[g.get('kind') for g in goals],'goal_status_events':[(g.get('status'),g.get('events')) for g in goals],
    'outbound_messages':outs,'public_reply_matches_outbound':any(str(m.get('text') or '').strip()==str(r.get('reply') or '').strip() for m in outs),
    'faculty_build_calls':r.get('faculty_build_calls',[]),'teacher_calls':r.get('teacher_calls'),'task_wall_s':r.get('task_wall_ns',0)/1e9,'task_cpu_s':r.get('task_process_cpu_ns',0)/1e9,'boot_wall_s':r.get('boot_wall_ns',0)/1e9,'boot_cpu_s':r.get('boot_process_cpu_ns',0)/1e9,'peak_rss_gib':r.get('peak_rss_bytes',0)/2**30})
  if task=='scene_description':ok=lambda x:x['reply']=="I see the grey thing stays, the yellow counter, and the blue thing moves." and 'describe_scene' in x['action_routes'] and x['goal_kinds']==['describe_scene'] and x['goal_status_events']==[('resolved',['selection','execution','action_result'])]
  elif task=='held_self_knowledge_answer':ok=lambda x:'organis' in x['reply'].lower() and not x['reply'].rstrip().endswith('?')
  elif task=='self_report_action':ok=lambda x:'self_report' in x['action_routes'] and x['goal_kinds']==['report_self'] and x['goal_status_events']==[('resolved',['selection','execution','action_result'])] and bool(x['reply'].strip())
  elif task=='unknown_word_clarification':ok=lambda x:'quorplezap' in x['reply'].lower() and x['reply'].rstrip().endswith('?') and any('quorplezap' in str(m.get('trouble_source','')).lower() and m.get('expects_response') is True and 'clarification' in m.get('speech_acts',[]) for m in x['outbound_messages'])
  else:ok=lambda x:'concern_authored' in x['action_routes'] and bool(x['reply'].strip()) and x['teacher_calls']==0
  lat=[x['task_wall_s'] for x in items];by_task[task]={'replicate_count':len(items),'task_contract_pass_count':sum(bool(ok(x)) for x in items),'task_contract_pass':len(items)==2 and all(ok(x) for x in items),'median_task_wall_s':statistics.median(lat),'request_wall_s':stat(lat),'workers':items}
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'integrity_checks':integrity,'integrity_pass':all(integrity.values()),'by_task':by_task,'task_contract_pass_count':sum(x['task_contract_pass_count'] for x in by_task.values()),'task_contract_total':sum(x['replicate_count'] for x in by_task.values()),'all_task_contracts_pass':all(x['task_contract_pass'] for x in by_task.values()),'claim_boundary':'Selected live conversation tasks from repository behavior contracts, two fresh full-seed processes each. Per-task outcomes and runtime route evidence are reported; not natural prevalence, general accuracy, rule necessity, or scaling.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'integrity_pass':out['integrity_pass'],'task_contracts':{k:{'passes':v['task_contract_pass_count'],'n':v['replicate_count'],'median_wall_s':round(v['median_task_wall_s'],3),'outbound_alignment':[w['public_reply_matches_outbound'] for w in v['workers']]} for k,v in by_task.items()}},indent=2))
 if not out['integrity_pass']:raise SystemExit('live panel integrity failed')
if __name__=='__main__':main()
