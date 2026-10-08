#!/usr/bin/env python3
"""Independently verify counterbalanced multi-task action outcomes."""
import gzip,hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/'evaluation/reports/multi_task_order_effect_v1_20261004.json.gz'
RUNNER=ROOT/'evaluation/substrate_capability/multi_task_order_effect_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_MULTI_TASK_ORDER_EFFECT_V1_PREREG_20261004.md'
LOCK=ROOT/'evaluation/substrate_capability/multi_task_order_effect_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/multi_task_order_effect_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in {'ts','runtime_s'}}
 if isinstance(v,list):return [clean(x) for x in v]
 return v
def ref(v):
 if isinstance(v,dict) and '__nid__' in v:return int(v['__nid__'])
 return int(v) if isinstance(v,int) else None
def expected_contract(t):
 c=t['condition'];actions=t['actions'];routes=[a.get('route') for a in actions];goals=t['goals'];reply=t['reply']
 def has_goal(kind,events=None):return any(g.get('kind')==kind and g.get('status')=='resolved' and (events is None or g.get('events')==events) for g in goals)
 if c=='scene_description':return reply=='I see the grey thing stays, the yellow counter, and the blue thing moves.' and has_goal('describe_scene',['selection','execution','action_result'])
 if c=='held_self_knowledge_answer':return 'organis' in reply.lower() and not reply.rstrip().endswith('?')
 if c=='self_report_action':return 'self_report' in routes and has_goal('report_self',['selection','execution','action_result']) and bool(reply.strip())
 if c=='unknown_word_clarification':return 'quorplezap' in reply.lower() and reply.rstrip().endswith('?') and any('quorplezap' in str(m.get('trouble_source','')).lower() and m.get('expects_response') is True and 'clarification' in m.get('speech_acts',[]) for m in t['outbound_messages'])
 if c=='concern_authoring':return 'concern_authored' in routes and any(a.get('concern') is not None for a in actions) and bool(reply.strip()) and 'no attached world/faculty' not in reply.lower() and t['teacher_calls']==0
 return False
def main():
 with gzip.open(CAP,'rt',encoding='utf-8') as f:x=json.load(f)
 lock=json.loads(LOCK.read_text())['locked_inputs'];checks={}
 checks['schema']=x.get('schema')=='MultiTaskOrderEffectV1'
 checks['runner_hash']=sha(RUNNER)==lock['runner_sha256']==x['locked_inputs']['runner_sha256']
 checks['analyzer_hash']=sha(__file__)==lock['analyzer_sha256']==x['locked_inputs']['analyzer_sha256']
 checks['protocol_hash']=sha(PROTOCOL)==lock['protocol_sha256']==x['locked_inputs']['protocol_sha256']
 checks['ten_fresh_workers']=len(x['runs'])==10 and len({r['pid'] for r in x['runs']})==10
 checks['source_lock_stable']=all(r['locked_inputs']==x['locked_inputs']==r['post_run_inputs'] for r in x['runs'])
 outcomes=[];graphs=[];cross_types=Counter();projection_ok=True
 for r in x['runs']:
  g=r['graph'];ns={int(n['id']):n for n in g['nodes']};es=[(int(e['src']),str(e['type']),int(e['tgt'])) for e in g['edges']]
  graphs.append(clean(g));roots=[];owners=[]
  for t in r['turns']:
   root=t['message_id'];goals=set()
   for a,rel,b in es:
    if rel=='comprehends':
     if a==root and b in ns and ns[b]['type']=='Goal':goals.add(b)
     if b==root and a in ns and ns[a]['type']=='Goal':goals.add(a)
   events=set()
   for gid in goals:
    eid=ref(ns[gid].get('attrs',{}).get('origin_event'))
    if eid in ns and ns[eid]['type']=='DiscourseEvent':events.add(eid)
   for a,rel,b in es:
    if rel=='for_goal':
     if a in ns and ns[a]['type']=='DiscourseEvent' and b in goals:events.add(a)
     if b in ns and ns[b]['type']=='DiscourseEvent' and a in goals:events.add(b)
   owned=({root} if root in ns else set())|goals|events;owners.append(owned)
   got=sorted(t['goals'],key=lambda z:int(z['id']));expected=[]
   for gid in sorted(goals):
    related=[]
    for a,rel,b in es:
     if rel=='for_goal':
      eid=a if b==gid else b if a==gid else None
      if eid in ns and ns[eid]['type']=='DiscourseEvent':related.append(ns[eid]['attrs'].get('kind'))
    if not related:
     eid=ref(ns[gid].get('attrs',{}).get('origin_event'))
     if eid in ns and ns[eid]['type']=='DiscourseEvent':related.append(ns[eid]['attrs'].get('kind'))
    expected.append({'id':gid,'kind':ns[gid]['attrs'].get('kind'),'status':ns[gid]['attrs'].get('lifecycle_status'),'events':related})
   if expected!=got:projection_ok=False
   outcomes.append({'order_id':r['order_id'],'replicate':r['replicate'],'condition':t['condition'],'position':r['order'].index(t['condition']),'reply':t['reply'],'actions':t['actions'],'goal_count':len(goals),'goal_kinds':[ns[z]['attrs'].get('kind') for z in sorted(goals)],'goals':got,'teacher_calls':t['teacher_calls'],'contract_pass':next(z['result']['pass'] for z in x['contract_results'] if z['order_id']==r['order_id'] and z['replicate']==r['replicate'] and z['condition']==t['condition'])})
  owner={n:i for i,s in enumerate(owners) for n in s}
  crossing=[(a,rel,b) for a,rel,b in es if a in owner and b in owner and owner[a]!=owner[b]]
  cross_types.update(rel for _,rel,_ in crossing)
 checks['goal_projection_matches_raw_graph']=projection_ok
 replication=[]
 for order_id in range(5):
  rows=[r for r in x['runs'] if r['order_id']==order_id]
  checks[f'order_{order_id}_two_replicates']=len(rows)==2
  rep_outcomes=[json.dumps([{k:t[k] for k in ('condition','reply','error','actions','goals','outbound_messages','teacher_calls')} for t in r['turns']],sort_keys=True) for r in rows]
  same=len(set(rep_outcomes))==1
  checks[f'order_{order_id}_outcomes_reproduce']=same
  digests={hashlib.sha256(json.dumps(clean(r['graph']),sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest() for r in rows}
  checks[f'order_{order_id}_structure_reproduces']=len(digests)==1
  replication.append({'order_id':order_id,'order':rows[0]['order'],'replicates':len(rows),'normalized_structure_reproduces':len(digests)==1,'outcomes_reproduce':same})
 checks['50_contract_rows']=len(x['contract_results'])==50
 checks['contract_results_match_turns']=all(any(z['order_id']==r['order_id'] and z['replicate']==r['replicate'] and z['condition']==t['condition'] and z['position']==r['order'].index(t['condition']) and z['result']['pass']==expected_contract(t) for z in x['contract_results']) for r in x['runs'] for t in r['turns'])
 checks['runner_capture_integrity']=x['passed'] and all(x['checks'].values())
 summary={'workers':len(x['runs']),'task_runs':len(outcomes),'contract_passes':sum(o['contract_pass'] for o in outcomes),'contract_pass_fraction':sum(o['contract_pass'] for o in outcomes)/len(outcomes),'by_condition':{},'by_position':{},'cross_owner_edge_types':dict(sorted(cross_types.items()))}
 for c in sorted({o['condition'] for o in outcomes}):
  z=[o for o in outcomes if o['condition']==c];summary['by_condition'][c]={'passes':sum(o['contract_pass'] for o in z),'total':len(z),'positions':{str(p):sum(o['contract_pass'] for o in z if o['position']==p) for p in range(5)},'goal_observations':sum(o['goal_count']>0 for o in z)}
 for p in range(5):
  z=[o for o in outcomes if o['position']==p];summary['by_position'][str(p)]={'passes':sum(o['contract_pass'] for o in z),'total':len(z)}
 out={'schema':'MultiTaskOrderEffectV1Analysis','capture_sha256':sha(CAP),'analyzer_sha256':sha(__file__),'checks':checks,'passed':all(checks.values()),'replication':replication,'summary':summary,'outcomes':outcomes,'claim_boundary':'Ten workers over five cyclic orders of one authored five-task panel. This descriptive panel measures sensitivity to order and existing contracts, not natural-task prevalence, causal order effects, complete dependencies, or tractability.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':summary},indent=2))
 if not out['passed']:raise SystemExit('independent analysis failed')
if __name__=='__main__':main()
