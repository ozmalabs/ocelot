#!/usr/bin/env python3
"""Independent verification of paired trace-off/trace-on conversation runs."""
import hashlib,json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3_lock_20261003.json'
CAP=ROOT/'evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_3_20261003.json'
BASE=ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json'
BASE_LOCK=ROOT/'evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_3_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());base=json.loads(BASE.read_text());oldlock=json.loads(BASE_LOCK.read_text())['locked_inputs'];errors=[]
 def req(c,msg):
  if not c:errors.append(msg)
 req(cap['source_lock_sha256']==sha(LOCK),'source lock hash mismatch')
 req(cap['locked_inputs']==lock['locked_inputs']==cap['post_run_inputs'],'source lock drift')
 req(all(cap['checks'].values()),'runner check failure')
 req(cap['baseline_capture_sha256']==sha(BASE),'historical baseline capture changed')
 current=lock['locked_inputs'];compat={k:oldlock.get(k)==current.get(k) for k in ('native_extension_sha256','native_build_manifest_sha256','rust_sources_sha256','materializer_sha256')}
 req(cap['historical_source_compatibility']==compat,'historical source compatibility mismatch')
 base_index={(r['replicate'],c['case_id'],c.get('requested_goal_count')):c for r in base['runs'] for c in r['cases']}
 pairs=[];kinds=Counter();rules=Counter();relations=Counter();wild=Counter();closures=0;trace_rows=0;trace_mult=0;static_rules=set();case_rows=0
 for run in cap['runs']:
  req(run['started_inputs']==current==run['finished_inputs'],'worker source drift '+str(run['replicate']))
  req(run['replicate'] in (0,1,2),'unexpected replicate')
  req(len(run['cases'])==4,'worker case count mismatch '+str(run['replicate']))
  for pair in run['cases']:
   case_rows+=1;off=pair['trace_off'];on=pair['trace_on'];key=(run['replicate'],pair['case_id'],pair.get('requested_goal_count'))
   req(off['case_id']==on['case_id']==pair['case_id'] and off.get('requested_goal_count')==on.get('requested_goal_count')==pair.get('requested_goal_count'),'paired case identity mismatch '+str(key))
   req(digest(off['final_graph'])==off['final_graph_digest'],'trace-off final graph digest mismatch '+str(key))
   req(digest(on['final_graph'])==on['final_graph_digest'],'trace-on final graph digest mismatch '+str(key))
   cp_equal=[a['graph_digest']==b['graph_digest'] for a,b in zip(off['checkpoints'],on['checkpoints'])]
   req(len(off['checkpoints'])==len(on['checkpoints']) and all(cp_equal),'checkpoint graph parity mismatch '+str(key))
   req(off['final_graph_digest']==on['final_graph_digest'],'final graph parity mismatch '+str(key))
   req(off['static_rule_access']==on['static_rule_access'],'static rule access signature changed '+str(key))
   req(off['frame_interaction_edges']==on['frame_interaction_edges'],'frame interaction changed '+str(key))
   req(len(off['frame_owner'])==off['event_count']+off['goal_count'] and off['frame_owner']==on['frame_owner'],'owner labels mismatch '+str(key))
   req(all(cp['closure'].get('status')=='fixed_point' for c in (off,on) for cp in c['checkpoints']),'closure not at fixed point '+str(key))
   req(all(g['status']=='resolved' and len(g['transition_indices'])==3 for c in (off,on) for g in c['goals']),'goal resolution mismatch '+str(key))
   req(all(not cp['runtime_access_trace_events'] for cp in off['checkpoints']),'trace-off arm recorded accesses '+str(key))
   req(all(cp['trace_dropped']==0 for cp in on['checkpoints']),'trace drops '+str(key))
   uids={r['uid']:r['name'] for r in on['static_rule_access']}
   for s in on['static_rule_access']:
    static_rules.add(s['name'])
    if s['reads_any'] or s['writes_any']:wild[s['name']]+=1
   owners={int(n):int(f) for n,f in on['frame_owner']}
   local_kind=Counter();local_rule=Counter();local_relation=Counter();nrows=0;mult=0
   for cp in on['checkpoints']:
    closures+=1
    for e in cp['runtime_access_trace_events']:
     nrows+=1;trace_rows+=1;mult+=int(e['count']);trace_mult+=int(e['count']);local_kind[e['kind']]+=int(e['count']);kinds[e['kind']]+=int(e['count']);local_rule[e['rule_name']]+=int(e['count']);rules[e['rule_name']]+=int(e['count'])
     req(e['rule_uid'] in uids and e['rule_name']==uids.get(e['rule_uid']),'unattributed event '+str(key))
     req(e['node_frame']==(owners.get(e['node']) if e['node'] is not None else None),'node owner mismatch '+str(key))
     req(e['peer_frame']==(owners.get(e['peer']) if e['peer'] is not None else None),'peer owner mismatch '+str(key))
     nf,pf=e['node_frame'],e['peer_frame'];rel='same_frame' if nf is not None and pf is not None and nf==pf else 'cross_frame' if nf is not None and pf is not None else 'one_endpoint_shared_or_unowned' if (nf is None)!=(pf is None) else 'both_unowned_or_node_only'
     local_relation[rel]+=int(e['count']);relations[rel]+=int(e['count'])
   req(nrows>0,'trace-on arm has no access events '+str(key))
   historical=base_index.get(key);hist_match={'final':bool(historical and off['final_graph_digest']==historical['final_graph_digest']),
     'checkpoints':[a['graph_digest']==b['graph_digest'] for a,b in zip(off['checkpoints'],historical['checkpoints'])] if historical else []}
   pairs.append({'key':list(key),'final_graph_equal':off['final_graph_digest']==on['final_graph_digest'],'checkpoint_graph_equal':cp_equal,
    'trace_event_rows':nrows,'trace_event_multiplicity':mult,'access_counts_by_kind':dict(sorted(local_kind.items())),
    'access_counts_by_rule':dict(sorted(local_rule.items())),'access_counts_by_owner_relation':dict(sorted(local_relation.items())),
    'static_rule_count':len(on['static_rule_access']),'wildcard_rule_count':sum(bool(x['reads_any'] or x['writes_any']) for x in on['static_rule_access']),'historical_baseline_match':hist_match})
 req(case_rows==12,'paired task coverage mismatch')
 req(len({(tuple(x['key'][1:])) for x in pairs})==4,'case families/counts incorrect')
 historical_rows=cap['historical_baseline_comparison'];req(len(historical_rows)==12,'historical comparison coverage mismatch')
 offmap={(r['replicate'],p['case_id'],p.get('requested_goal_count')):p['trace_off'] for r in cap['runs'] for p in r['cases']}
 for x in historical_rows:
  key=tuple(x['key']);c=base_index.get(key);off=offmap.get(key)
  req(c is not None and off is not None,'historical comparison row unmatched')
  if c and off:
   req(x['matches_historical_final_graph']==(off['final_graph_digest']==c['final_graph_digest']),'historical final comparison mismatch')
   req(x['matches_historical_checkpoints']==[a['graph_digest']==b['graph_digest'] for a,b in zip(off['checkpoints'],c['checkpoints'])],'historical checkpoint comparison mismatch')
 req(bool(trace_rows),'no concrete access events')
 req(cap['timing']['process_cpu_ns']==cap['timing']['parent_process_cpu_ns']+cap['timing']['worker_process_cpu_ns_sum'],'CPU aggregation mismatch')
 manifest=cap.get('run_manifest',{});req(manifest.get('manifest_schema')=='substrate-run-manifest-v1','shared manifest missing')
 required=['evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_3.py','evaluation/substrate_capability/analyze_substrate_connected_conversation_access_trace_panel_v1_3.py','docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_METHOD_20261003.md','docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_3_AMENDMENT_20261003.md','scripts/substrate_run_manifest.py','scripts/substrate_discourse_connected_task_census_v1.py','scripts/substrate_connected_conversation_boundary_panel_v1.py','scripts/substrate_discourse_connected_task_census_v2_1.py','evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json','evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json','tests/fixtures/conversational_manifold/phase3_common_ground_stress.json','tests/fixtures/conversational_manifold/phase3_same_addressee_concurrent_goals_scale.json','seeds/conversation_discourse_state.json','domains/discourse_state.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock','evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1.py','evaluation/substrate_capability/analyze_substrate_connected_conversation_access_trace_panel_v1.py','evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_lock_20261003.json','docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_FAILURE_20261003.md','evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_1.py','evaluation/substrate_capability/analyze_substrate_connected_conversation_access_trace_panel_v1_1.py','evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_1_lock_20261003.json','evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_1_20261003.json','evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_1_analysis_20261003.json','docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_1_AMENDMENT_20261003.md','evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_2.py','evaluation/substrate_capability/analyze_substrate_connected_conversation_access_trace_panel_v1_2.py','evaluation/substrate_capability/substrate_connected_conversation_access_trace_panel_v1_2_lock_20261003.json','evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_2_20261003.json','evaluation/reports/substrate_connected_conversation_access_trace_panel_v1_2_analysis_20261003.json','docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_ACCESS_TRACE_PANEL_V1_2_AMENDMENT_20261003.md']+[f'runners/dsl/src/{x}' for x in ('graph.rs','rewrite.rs','substrate.rs','term.rs','access_trace.rs','py.rs')]
 explicit=manifest.get('explicit_inputs',{});req(all(p in explicit and explicit[p].get('exists') for p in required),'manifest explicit-input coverage incomplete')
 log=manifest.get('stdout_stderr_capture') or {};lp=ROOT/log.get('path','missing');req(lp.is_file() and sha(lp)==log.get('sha256'),'parent console hash mismatch')
 req(manifest.get('hardware',{}).get('cpu_model') is not None and cap['timing']['process_cpu_ns']>0 and cap['timing']['peak_rss_bytes']>0,'hardware/CPU/RSS missing')
 summary={'paired_case_replicates':case_rows,'paired_graph_states_equal':sum(p['final_graph_equal'] and all(p['checkpoint_graph_equal']) for p in pairs),'trace_event_rows':trace_rows,'trace_event_multiplicity':trace_mult,'access_counts_by_kind':dict(sorted(kinds.items())),'access_counts_by_rule':dict(sorted(rules.items())),'access_counts_by_owner_relation':dict(sorted(relations.items())),'static_rules_observed':sorted(static_rules),'wildcard_rule_observations':dict(sorted(wild.items())),'historical_source_compatibility':compat,'matches_historical_graph_count':sum(bool(x['matches_historical_final_graph']) and all(x['matches_historical_checkpoints']) for x in historical_rows),'trace_completeness_claimed':False}
 out={'schema':'ConnectedConversationAccessTracePanelV1_3Analysis','gates_pass':not errors,'errors':errors,'summary':summary,'rows':pairs,'claim_boundary':'Exact paired graph parity establishes state preservation under tracing for this fixed current-source panel. Access traces remain partial; no partition safety, natural-task prevalence, or speedup is established.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\\n');print(json.dumps(out,indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
