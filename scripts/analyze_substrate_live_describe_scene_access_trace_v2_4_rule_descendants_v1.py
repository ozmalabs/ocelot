#!/usr/bin/env python3
"""Derive a lower-bound task descendant set from v2.4 native mint/edge effects."""
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_20260927.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def derive(run,request):
 bounds=run['task_boundaries'];letter='a' if request=='request-A' else 'b'
 lifecycle=set(bounds[letter]['owned_node_ids']);other=set(bounds['b' if letter=='a' else 'a']['owned_node_ids']);scene=set(bounds['shared_scene_input']['owned_node_ids'])
 rows=[r for r in run['access_trace']['event_rows'] if r['request']==request]
 mints={int(r['node']):str(r['resource']) for r in rows if r['kind']=='effect_node_mint' and r['node'] is not None}
 effects=[r for r in rows if r['kind']=='effect_edge_upsert' and r['node'] is not None and r['peer'] is not None]
 owned=lifecycle|scene;desc=set();changed=True
 while changed:
  changed=False
  for row in effects:
   src,tgt=int(row['node']),int(row['peer'])
   for candidate in (src,tgt):
    if candidate in mints and candidate not in owned and (src in owned or tgt in owned):
     owned.add(candidate);desc.add(candidate);changed=True
 desc_edges=[]
 for row in effects:
  src,tgt=int(row['node']),int(row['peer'])
  if src in desc or tgt in desc:
   desc_edges.append({'src':src,'edge_type':row['resource'],'tgt':tgt,'rule_name':row['rule_name'],'count':row['count'],'other_endpoint_type':'rule_minted' if (tgt if src in desc else src) in mints else 'preexisting_or_host_created'})
 partition=collections.Counter();kinds=collections.defaultdict(collections.Counter)
 for row in rows:
  nodes={n for n in (row['node'],row['peer']) if n is not None}
  hits=[]
  if nodes&lifecycle:hits.append('request_lifecycle')
  if nodes&other:hits.append('other_request_lifecycle')
  if nodes&scene:hits.append('shared_scene_input')
  if nodes&desc:hits.append('rule_produced_descendant')
  label='+'.join(hits) if hits else 'none_of_measured_frame_sets'
  partition[label]+=int(row['count']);kinds[label][row['kind']]+=int(row['count'])
 return {'request':request,'base_lifecycle_nodes':len(lifecycle),'shared_scene_input_nodes':len(scene),'rule_produced_descendant_count':len(desc),'rule_produced_descendants_by_type':dict(sorted(collections.Counter(mints[n] for n in desc).items())),
  'rule_produced_descendant_ids':sorted(desc),'candidate_rule_minted_node_ids':sorted(mints),'rule_effect_edges_incident_to_descendants':desc_edges,'selected_events_total':sum(int(r['count']) for r in rows),'events_by_expanded_frame_touch':dict(sorted(partition.items())),
  'event_kinds_by_expanded_frame_touch':{k:dict(sorted(v.items())) for k,v in sorted(kinds.items())},'events_touching_any_measured_frame_node':sum(v for k,v in partition.items() if k!='none_of_measured_frame_sets'),
  'limitation':'Descendants are only rule-minted nodes connected by captured native effect_edge_upsert rows. Host-created nodes, non-mint descendant mutations, specialized untraced operations, and dependencies without concrete node/peer events are omitted; this is a lower bound, not a complete ownership assignment.'}
def main():
 raw=json.loads(RAW.read_text());runs=[r for r in raw['runs'] if r['trace_enabled']]
 checks={'three_traces':len(runs)==3,'source_stable':all(r['worker_started_inputs']==r['worker_finished_inputs'] for r in runs),'trace_complete':all(r['access_trace']['dropped']==0 for r in runs),'nonempty_requests':all({x['request'] for x in r['access_trace']['event_rows']}=={'request-A','request-B'} for r in runs)}
 details=[derive(r,q) for r in runs for q in ('request-A','request-B')]
 checks['all_derived_descendants_have_native_mint_rows']=all(set(d['rule_produced_descendant_ids'])<=set(d['candidate_rule_minted_node_ids']) for d in details)
 checks['repeated_derived_sets_match']=all(details[0]['rule_produced_descendant_ids']==d['rule_produced_descendant_ids'] for d in details if d['request']=='request-A') and all(details[1]['rule_produced_descendant_ids']==d['rule_produced_descendant_ids'] for d in details if d['request']=='request-B')
 checks['event_counts_reconcile']=all(sum(d['events_by_expanded_frame_touch'].values())==d['selected_events_total'] for d in details)
 report={'schema_version':1,'raw_sha256':sha(RAW),'checks':checks,'all_checks_pass':all(checks.values()),'claim_boundary':'Lower-bound descendants inferred from native rule mint and edge-upsert events in three identical v2.4 traced workers; not a complete dynamic dependency graph or proof of task locality.','rows':details}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'summary':[{'replicate':i//2,'request':d['request'],'descendants':d['rule_produced_descendant_count'],'by_type':d['rule_produced_descendants_by_type'],'events_touching_measured_frame':d['events_touching_any_measured_frame_node'],'total':d['selected_events_total']} for i,d in enumerate(details)]},indent=2))
 if not report['all_checks_pass']:raise SystemExit(1)
if __name__=='__main__':main()
