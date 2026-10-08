#!/usr/bin/env python3
"""Independent validation of live runtime rule counter capture v1."""
from __future__ import annotations
import gzip,hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_3_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_3_lock_20261004.json'
OUT=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_3_reconciled_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def turn_projection(run):
 return [{'route':t.get('route'),'reply_nonempty':t.get('reply_nonempty'),'goal_count':t.get('goal_count'),'goal':{k:t.get('goal',{}).get(k) for k in ('kind','status','transition_kinds','transition_links_all_bound','closed')} if isinstance(t.get('goal'),dict) else None} for t in run.get('turns',[])]

def main():
 with gzip.open(RAW,'rt',encoding='utf8') as f:raw=json.load(f)
 locked=json.loads(LOCK.read_text())['locked_inputs'];errors=[];rows=[]
 def req(ok,msg):
  if not ok:errors.append(msg)
 req(raw['locked_inputs']==locked==raw['post_run_inputs'],'parent source lock mismatch')
 req(raw['source_stable'] and len(raw['runs'])==6 and all(r.get('worker_returncode')==0 for r in raw['runs']),'worker/source gate failed'); aggregate_schema_bug=(raw.get('all_checks_pass') is False and all(r.get('worker_returncode')==0 and 'capture' not in r for r in raw['runs']))
 expected={(rep,mode) for rep in (0,1,2) for mode in ('off','on')}
 req(set((r.get('replicate'),r.get('audit_mode')) for r in raw['runs'])==expected,'crossed 3x2 worker design incomplete')
 runs={(r.get('replicate'),r.get('audit_mode')):r for r in raw['runs'] if r.get('worker_returncode')==0 and 'native_counter_observations' in r}
 digests=set();uid_total=mapped_total=0;on_requests=0;worker_prompts=None
 for key,run in runs.items():
  req(run.get('worker_returncode')==0 and run.get('worker_started_inputs')==locked==run.get('worker_finished_inputs'),'worker provenance '+str(key))
  cap=run;digests.add(cap.get('graph_semantic_sha256'));obsrows=run['native_counter_observations'];requests=cap.get('requests',[])
  req(len(obsrows)==len(requests)==2,'request/counter cardinality '+str(key))
  prompts=[x.get('prompt') for x in requests]
  req(prompts==raw['design']['prompts'],'prompt order '+str(key))
  if worker_prompts is None:worker_prompts=prompts
  else:req(worker_prompts==prompts,'prompt schedule varies '+str(key))
  for obs,request in zip(obsrows,requests):
   req(obs.get('prompt')==request.get('prompt'),'counter prompt mismatch '+str(key))
   access=request.get('access_rows',[]);used={int(x[0]) for x in access};uid_map={int(x['uid']):x for x in obs['uid_definitions']}
   missing=used-uid_map.keys();uid_total+=len(used);mapped_total+=len(used&uid_map.keys())
   req(not missing,'unmapped runtime RuleUIDs '+str(key)+' '+obs['prompt']+f' ({len(missing)})')
   req(request.get('access_dropped_events',0)==0 and request.get('work_dropped_events',0)==0,'trace events dropped '+str(key))
   c=obs['counter_rows'];g=dict(c['global']);per=c['per_rule'];clauses=c['clauses'];metadata=c['metadata'];edge=c['edge_candidates']
   if run['audit_mode']=='off':
    req(not per and not clauses and not metadata and not edge and all(v==0 for v in g.values()),'audit-off counters nonzero '+str(key));continue
   on_requests+=1;req(not any(bool(x[4]) for x in metadata),'ambiguous rule metadata '+str(key))
   req(g.get('cand_tested_unattributed',0)==0 and g.get('term_evals_unattributed',0)==0,'unattributed matcher/Term work '+str(key))
   per_by={i:{} for i,_,_ in per}
   for rid,metric,count in per:per_by[int(rid)][metric]=int(count)
   req(sum(x.get('candidate_pairs',0) for x in per_by.values())==g.get('cand_enum',-1),'per-rule/global candidate conservation '+str(key))
   req(sum(x.get('candidate_tests',0) for x in per_by.values())==g.get('cand_tested',-1),'per-rule/global test conservation '+str(key))
   for rid in per_by:
    req(sum(int(v) for i,_,v in clauses if int(i)==rid)==per_by[rid].get('candidate_tests',0),'clause conservation '+str(key)+f' id={rid}')
    req(sum(int(x[5]) for x in edge if int(x[0])==rid)==per_by[rid].get('candidate_pairs',0),'edge conservation '+str(key)+f' id={rid}')
   req(g.get('cand_enum_local',0)+g.get('cand_enum_scan',0)+g.get('cand_enum_hinted',0)==g.get('cand_enum',-1),'candidate path conservation '+str(key))
   req(g.get('cand_enum_first',0)+g.get('cand_enum_repeat',0)==g.get('cand_enum',-1),'first/repeat conservation '+str(key))
   name_by={int(x[0]):str(x[2]) for x in metadata}
   named={name_by[i]:v for i,v in per_by.items() if i in name_by}
   rows.append({'replicate':key[0],'mode':key[1],'prompt':obs['prompt'],'runtime_rule_uid_count':len(used),'mapped_uid_count':len(used&uid_map.keys()),'native_rule_ids':len(metadata),'candidate_tests':g.get('cand_tested',0),'candidate_expansions':g.get('cand_enum',0),'unattributed_candidate_tests':g.get('cand_tested_unattributed',0),'ambiguous_rule_id_count':sum(bool(x[4]) for x in metadata),'term_evaluations':g.get('term_evals_total',0),'term_units':g.get('term_units_total',0),'per_rule':named})
 req(len(digests)==1 and None not in digests,'semantic graph digest differs across workers/modes')
 for rep in (0,1,2):
  off,on=runs.get((rep,'off')),runs.get((rep,'on'))
  if off and on:
   req(off['graph_semantic_sha256']==on['graph_semantic_sha256'],'paired graph digest mismatch '+str(rep))
   req(turn_projection(off['task_result'])==turn_projection(on['task_result']),'paired task contract mismatch '+str(rep))
   req([r.get('reply') for r in off['requests']]==[r.get('reply') for r in on['requests']],'paired request replies differ '+str(rep))
 req(uid_total==mapped_total,'not all access UIDs resolved')
 req(on_requests==6,'expected six audit-on request records')
 out={'schema':'LiveRuntimeClosureCountersV1_3ReconciledAnalysis','passed':not errors,'errors':errors,'parent_aggregate_flag_false_due_schema_bug':aggregate_schema_bug,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'worker_count':len(runs),'request_count':sum(len(x['native_counter_observations']) for x in runs.values()),'audit_on_request_count':on_requests,'semantic_graph_digest_count':len(digests),'paired_task_contracts_match':not any('paired task contract mismatch' in e for e in errors),'runtime_rule_uid_observations':uid_total,'mapped_rule_uid_observations':mapped_total,'unmapped_rule_uid_observations':uid_total-mapped_total,'requests':rows,'claim_boundary':raw['design']['claim_limit'],'post_capture_analyzer_sha256':sha(Path(__file__).resolve())}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'aggregate_schema_bug':aggregate_schema_bug,'errors':errors[:30],'error_count':len(errors),'workers':len(runs),'requests':out['request_count'],'audit_on':on_requests,'uids':uid_total,'mapped':mapped_total,'digests':len(digests)},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
