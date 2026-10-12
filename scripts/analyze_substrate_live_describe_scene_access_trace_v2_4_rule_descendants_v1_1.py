#!/usr/bin/env python3
"""Refine v2.4 ownership: task descendants vs persistent shared side effects."""
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_1_20260927.json'
OWNERSHIP_EDGE_TYPES={'has_subgoal','has_intent','seeks_interpretation_shadow'}
PERSISTENT_SHARED_EDGE_TYPES={'has_self_concern','has_gap_recurrence'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive(run,request):
 b=run['task_boundaries'];mine='a' if request=='request-A' else 'b';other='b' if mine=='a' else 'a'
 own_life=set(b[mine]['owned_node_ids']);other_life=set(b[other]['owned_node_ids']);shared_input=set(b['shared_scene_input']['owned_node_ids'])
 rows=[x for x in run['access_trace']['event_rows'] if x['request']==request]
 mints={int(x['node']):str(x['resource']) for x in rows if x['kind']=='effect_node_mint' and x['node'] is not None}
 edge_writes=[x for x in rows if x['kind']=='effect_edge_upsert' and x['node'] is not None and x['peer'] is not None]
 owned=own_life|shared_input;desc=set();changed=True
 while changed:
  changed=False
  for x in edge_writes:
   if x['resource'] not in OWNERSHIP_EDGE_TYPES:continue
   src,tgt=int(x['node']),int(x['peer'])
   candidate=tgt if src in owned else src if tgt in owned and x['resource']=='has_intent' else None
   if candidate in mints and candidate not in owned:owned.add(candidate);desc.add(candidate);changed=True
 persistent=set()
 for x in edge_writes:
  if x['resource'] in PERSISTENT_SHARED_EDGE_TYPES:
   for n in (int(x['node']),int(x['peer'])):
    if n in mints:persistent.add(n)
 bucket=collections.Counter();kind_bucket=collections.defaultdict(collections.Counter)
 for x in rows:
  touched={int(n) for n in (x['node'],x['peer']) if n is not None};tags=[]
  if touched&own_life:tags.append('own_lifecycle')
  if touched&other_life:tags.append('other_request_lifecycle')
  if touched&shared_input:tags.append('shared_scene_percept_input')
  if touched&desc:tags.append('task_owned_rule_descendant')
  if touched&persistent:tags.append('persistent_shared_side_effect')
  label='+'.join(tags) if tags else 'none_of_classified_nodes'
  bucket[label]+=int(x['count']);kind_bucket[label][x['kind']]+=int(x['count'])
 return {'request':request,'own_lifecycle_node_count':len(own_life),'other_lifecycle_node_count':len(other_life),'shared_input_node_count':len(shared_input),
  'task_owned_rule_descendant_ids':sorted(desc),'task_owned_rule_descendants_by_type':dict(sorted(collections.Counter(mints[n] for n in desc).items())),
  'persistent_shared_side_effect_ids':sorted(persistent),'persistent_shared_side_effects_by_type':dict(sorted(collections.Counter(mints[n] for n in persistent).items())),
  'ownership_evidence_edges':[{'src':int(x['node']),'type':x['resource'],'tgt':int(x['peer']),'rule':x['rule_name']} for x in edge_writes if x['resource'] in OWNERSHIP_EDGE_TYPES and (int(x['node']) in desc or int(x['peer']) in desc)],
  'persistent_side_effect_evidence_edges':[{'src':int(x['node']),'type':x['resource'],'tgt':int(x['peer']),'rule':x['rule_name']} for x in edge_writes if x['resource'] in PERSISTENT_SHARED_EDGE_TYPES and (int(x['node']) in persistent or int(x['peer']) in persistent)],
  'selected_event_total':sum(int(x['count']) for x in rows),'events_by_mutually_exclusive_touch_class':dict(sorted(bucket.items())),
  'event_kinds_by_touch_class':{k:dict(sorted(v.items())) for k,v in sorted(kind_bucket.items())},
  'task_and_input_touch_events':sum(v for k,v in bucket.items() if any(t in k.split('+') for t in ('own_lifecycle','shared_scene_percept_input','task_owned_rule_descendant'))),
  'rule_descendant_policy':{'owned_edges':sorted(OWNERSHIP_EDGE_TYPES),'shared_side_effect_edges':sorted(PERSISTENT_SHARED_EDGE_TYPES)}}
def main():
 raw=json.loads(RAW.read_text());runs=[r for r in raw['runs'] if r['trace_enabled']]
 checks={'three_complete_stable_trace_workers':len(runs)==3 and all(r['access_trace']['dropped']==0 and r['worker_started_inputs']==r['worker_finished_inputs'] for r in runs),
  'all_descendants_have_mint_evidence':True,'repeat_node_sets_equal':True,'counts_reconcile':True}
 rows=[derive(r,q) for r in runs for q in ('request-A','request-B')]
 checks['all_descendants_have_mint_evidence']=all(set(x['task_owned_rule_descendant_ids'])<=set(int(r['node']) for r in runs[i//2]['access_trace']['event_rows'] if r['request']==x['request'] and r['kind']=='effect_node_mint' and r['node'] is not None) for i,x in enumerate(rows))
 checks['repeat_node_sets_equal']=all((rows[0]['task_owned_rule_descendant_ids'],rows[0]['persistent_shared_side_effect_ids'])==(x['task_owned_rule_descendant_ids'],x['persistent_shared_side_effect_ids']) for x in rows[::2]) and all((rows[1]['task_owned_rule_descendant_ids'],rows[1]['persistent_shared_side_effect_ids'])==(x['task_owned_rule_descendant_ids'],x['persistent_shared_side_effect_ids']) for x in rows[1::2])
 checks['counts_reconcile']=all(sum(x['events_by_mutually_exclusive_touch_class'].values())==x['selected_event_total'] for x in rows)
 report={'schema_version':1,'raw_sha256':sha(RAW),'ownership_policy':'Temporary rule-minted children attached by has_subgoal/has_intent/seeks_interpretation_shadow are task-owned. Nodes minted and attached via Agent/global has_self_concern or has_gap_recurrence are persistent shared side effects, not private frame descendants. Shared Concepts remain interfaces.','checks':checks,'all_checks_pass':all(checks.values()),'claim_boundary':'Source-informed classification of captured effect events; ownership edge policy is explicit and auditable but the native trace remains partial and cannot establish complete dependency ownership.','rows':rows}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'summary':[{'replicate':i//2,'request':x['request'],'task_descendants':x['task_owned_rule_descendants_by_type'],'persistent_side_effects':x['persistent_shared_side_effects_by_type'],'touches':x['events_by_mutually_exclusive_touch_class'],'task_input_touch':x['task_and_input_touch_events']} for i,x in enumerate(rows)]},indent=2))
 if not report['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
