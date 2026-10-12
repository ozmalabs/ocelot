#!/usr/bin/env python3
"""Independent parity, ownership, and provenance audit for the access panel."""
import hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_1_20261003.json'
BASE=ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());base=json.loads(BASE.read_text());errors=[]
 def req(c,msg):
  if not c:errors.append(msg)
 req(cap['source_lock_sha256']==sha(LOCK),'source lock hash mismatch')
 req(cap['locked_inputs']==lock['locked_inputs']==cap['post_run_inputs'],'source lock drift')
 req(all(cap['checks'].values()),'runner check failure')
 req(cap['baseline_capture_sha256']==sha(BASE),'baseline capture changed')
 basemap={(r['replicate'],c['case_id'],c.get('requested_goal_count')):c for r in base['runs'] for c in r['cases']}
 parity={(x['replicate'],x['case_id'],x.get('requested_goal_count')):x for x in cap['baseline_parity']}
 req(len(parity)==36,'baseline parity row count mismatch')
 rows=[];kinds=Counter();rules=Counter();relations=Counter();static=Counter();wild=Counter();events_total=0;closures=0
 for run in cap['runs']:
  req(run['started_inputs']==lock['locked_inputs']==run['finished_inputs'],'worker source drift '+str(run['replicate']))
  req(run['replicate'] in (0,1,2),'unexpected replicate')
  for ci,c in enumerate(run['cases']):
   key=(run['replicate'],c['case_id'],c.get('requested_goal_count'));old=basemap.get(key);p=parity.get(key)
   req(old is not None and p is not None,'baseline row missing '+str(key))
   if old and p:
    req(c['final_graph_digest']==old['final_graph_digest']==p['graph_digest_equal'],'final graph parity mismatch '+str(key))
    req(len(c['checkpoints'])==len(old['checkpoints'])==len(p['checkpoint_digests_equal']),'checkpoint count mismatch '+str(key))
    req(all(a['graph_digest']==b['graph_digest'] for a,b in zip(c['checkpoints'],old['checkpoints'])),'checkpoint graph parity mismatch '+str(key))
   owners={int(n):int(f) for n,f in c['frame_owner']};uids={x['uid']:x['name'] for x in c['static_rule_access']};
   req(len(owners)==c['event_count']+c['goal_count'],'owner count mismatch '+str(key))
   req(all(not x['reads_any'] or isinstance(x['reads_any'],bool) for x in c['static_rule_access']),'bad wildcard field')
   for s in c['static_rule_access']:
    static[(s['name'],'read')]+=len(s['reads']);static[(s['name'],'write')]+=len(s['writes'])
    if s['reads_any'] or s['writes_any']:wild[s['name']]+=1
   local_kinds=Counter();local_relations=Counter();local_rules=Counter();local_count=0
   for cp in c['checkpoints']:
    closures+=1;req(cp['closure'].get('status')=='fixed_point','non-fixed closure '+str(key))
    req(cp['trace_dropped']==0,'trace drops '+str(key))
    for e in cp['runtime_access_trace_events']:
     events_total+=1;local_count+=int(e['count']);local_kinds[e['kind']]+=int(e['count']);kinds[e['kind']]+=int(e['count'])
     local_rules[e['rule_name']]+=int(e['count']);rules[e['rule_name']]+=int(e['count'])
     req(e['rule_uid'] in uids and e['rule_name']==uids.get(e['rule_uid']),'unattributed access '+str(key))
     req(e['node_frame']==(owners.get(e['node']) if e['node'] is not None else None),'node owner mismatch '+str(key))
     req(e['peer_frame']==(owners.get(e['peer']) if e['peer'] is not None else None),'peer owner mismatch '+str(key))
     nf,pf=e['node_frame'],e['peer_frame']
     rel='same_frame' if nf is not None and pf is not None and nf==pf else 'cross_frame' if nf is not None and pf is not None else 'one_endpoint_shared_or_unowned' if (nf is None)!=(pf is None) else 'both_unowned_or_node_only'
     local_relations[rel]+=int(e['count']);relations[rel]+=int(e['count'])
   rows.append({'key':list(key),'closure_calls':len(c['checkpoints']),'trace_event_rows':sum(len(cp['runtime_access_trace_events']) for cp in c['checkpoints']),'trace_event_multiplicity':local_count,'access_counts_by_kind':dict(sorted(local_kinds.items())),'access_counts_by_rule':dict(sorted(local_rules.items())),'access_counts_by_owner_relation':dict(sorted(local_relations.items())),'static_rule_count':len(c['static_rule_access']),'wildcard_rule_count':sum(bool(x['reads_any'] or x['writes_any']) for x in c['static_rule_access'])})
 req(len(rows)==36,'worker/case coverage mismatch')
 manifest=cap.get('run_manifest',{});req(manifest.get('manifest_schema')=='substrate-run-manifest-v1','shared manifest missing')
 explicit=manifest.get('explicit_inputs',{});required=['evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_1.py','evaluation/substrate_capability/analyze_substrate_connected_conversation_access_trace_panel_v1_1.py','docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_METHOD_20261003.md','docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_1_AMENDMENT_20261003.md','scripts/substrate_run_manifest.py','scripts/substrate_discourse_connected_task_census_v1.py','scripts/substrate_connected_conversation_boundary_panel_v1.py','scripts/substrate_discourse_connected_task_census_v2_1.py','evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json','evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json','tests/fixtures/conversational_manifold/phase3_common_ground_stress.json','tests/fixtures/conversational_manifold/phase3_same_addressee_concurrent_goals_scale.json','seeds/conversation_discourse_state.json','domains/discourse_state.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock','evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1.py','evaluation/substrate_capability/analyze_substrate_connected_conversation_access_trace_panel_v1.py','evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_lock_20261003.json','docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_FAILURE_20261003.md']+[f'runners/dsl/src/{x}' for x in ('graph.rs','rewrite.rs','substrate.rs','term.rs','access_trace.rs','py.rs')];req(all(x in explicit and explicit[x].get('exists') for x in required),'manifest explicit input coverage incomplete')
 req(manifest.get('hardware',{}).get('cpu_model') is not None and cap['timing']['process_cpu_ns']>0 and cap['timing']['peak_rss_bytes']>0,'hardware/CPU/RSS missing')
 log=manifest.get('stdout_stderr_capture') or {};lp=ROOT/log.get('path','missing');req(lp.is_file() and sha(lp)==log.get('sha256'),'parent console log mismatch')
 summary={'replicated_case_rows':len(rows),'closure_calls':closures,'concrete_access_event_rows':events_total,'concrete_access_event_multiplicity':sum(kinds.values()),'access_counts_by_kind':dict(sorted(kinds.items())),'access_counts_by_rule':dict(sorted(rules.items())),'access_counts_by_owner_relation':dict(sorted(relations.items())),'static_rules_observed':sorted({x['name'] for r in cap['runs'] for c in r['cases'] for x in c['static_rule_access']}),'wildcard_rule_counts_by_case':dict(sorted(wild.items())),'all_current_graphs_match_historical_untraced_capture':all(x['graph_digest_equal'] and all(x['checkpoint_digests_equal']) for x in parity.values()),'trace_is_complete':False}
 out={'schema':'ConnectedConversationAccessTracePanelV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary,'rows':rows,'claim_boundary':'Exact graph parity demonstrates state preservation under tracing for this fixed panel. Concrete access traces remain partial and this panel does not prove partition safety, natural-task prevalence, or speedup.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
