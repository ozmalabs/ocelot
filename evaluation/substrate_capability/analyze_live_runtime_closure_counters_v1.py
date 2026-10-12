#!/usr/bin/env python3
"""Independent validation of live runtime rule counter capture v1."""
from __future__ import annotations
import gzip,hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/live_runtime_closure_counters_v1_lock_20261004.json'
OUT=ROOT/'evaluation/reports/live_runtime_closure_counters_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def turn_projection(run):
 return [{'reply':t.get('reply'),'route':t.get('route'),'reply_nonempty':t.get('reply_nonempty'),'goal_count':t.get('goal_count'),'goal':{k:t.get('goal',{}).get(k) for k in ('kind','status','transition_kinds','transition_links_all_bound','closed')} if isinstance(t.get('goal'),dict) else None,'lifecycle_events':t.get('lifecycle_events'),'producer_work':t.get('producer_work')} for t in run.get('turns',[])]
def main():
 with gzip.open(RAW,'rt',encoding='utf8') as f:raw=json.load(f)
 locked=json.loads(LOCK.read_text())['locked_inputs'];errors=[];rows=[]
 def req(ok,msg):
  if not ok:errors.append(msg)
 req(raw['locked_inputs']==locked==raw['post_run_inputs'],'parent source lock mismatch')
 req(raw['source_stable'] and raw['all_checks_pass'] and len(raw['runs'])==6,'parent worker/source gate failed')
 req(set((r.get('replicate'),r.get('audit_mode')) for r in raw['runs'])=={(rep,mode) for rep in (0,1,2) for mode in ('off','on')},'six-worker crossed design incomplete')
 runs={ (r.get('replicate'),r.get('audit_mode')):r for r in raw['runs'] if 'capture' in r }
 digests=set();prompt_schedule=None;uid_total=mapped_total=unmapped_total=0;global_on=0;global_candidates=0;global_tests=0
 for key,run in runs.items():
  req(run.get('worker_returncode')==0 and run.get('worker_started_inputs')==locked==run.get('worker_finished_inputs'),'worker provenance '+str(key))
  capture=run['capture'];digests.add(capture.get('graph_semantic_sha256'));prompts=[x.get('prompt') for x in run['native_counter_observations']]
  req(len(prompts)==2 and prompts==raw['design']['prompts'],'two-request schedule '+str(key))
  req(len(run['native_counter_observations'])==len(capture.get('requests',[]))==2,'counter/request cardinality '+str(key))
  if prompt_schedule is None:prompt_schedule=prompts
  else:req(prompts==prompt_schedule,'prompt schedule differs '+str(key))
  for obs in run['native_counter_observations']:
   req(not obs['unmapped_rule_uids'],'runtime RuleUID unmapped '+str(key)+'/'+str(obs['prompt']))
   req(obs['access_dropped']==0,'access trace dropped '+str(key))
   uid_total+=len(obs['used_rule_uids']);mapped_total+=len(obs['mapped_rules']);unmapped_total+=len(obs['unmapped_rule_uids'])
   c=obs['counter_rows'];g=dict(c['global']);per=c['per_rule'];clauses=c['clauses'];meta=c['metadata'];edge=c['edge_candidates']
   if run['audit_mode']=='off':
    req(not per and not clauses and not meta and not edge and all(v==0 for v in g.values()),'audit-off counters nonzero '+str(key))
    continue
   global_on+=1;req(not any(bool(x[4]) for x in meta),'ambiguous matcher metadata '+str(key))
   req(g.get('cand_tested_unattributed',0)==0 and g.get('term_evals_unattributed',0)==0,'unattributed candidate/Term events '+str(key))
   per_by={int(i):{} for i,_,_ in per}
   for i,name,count in per:per_by[int(i)][name]=int(count)
   req(sum(x.get('candidate_pairs',0) for x in per_by.values())==g.get('cand_enum',-1),'per-rule/global candidate enumeration conservation '+str(key))
   req(sum(x.get('candidate_tests',0) for x in per_by.values())==g.get('cand_tested',-1),'per-rule/global candidate test conservation '+str(key))
   for i in per_by:
    req(sum(int(v) for rid,_,v in clauses if int(rid)==i)==per_by[i].get('candidate_tests',0),'clause conservation '+str(key)+f' rule {i}')
    req(sum(int(r[5]) for r in edge if int(r[0])==i)==per_by[i].get('candidate_pairs',0),'edge candidate conservation '+str(key)+f' rule {i}')
   req(g.get('cand_enum_local',0)+g.get('cand_enum_scan',0)+g.get('cand_enum_hinted',0)==g.get('cand_enum',-1),'candidate path conservation '+str(key))
   req(g.get('cand_enum_first',0)+g.get('cand_enum_repeat',0)==g.get('cand_enum',-1),'first/repeat conservation '+str(key))
   rows.append({'replicate':key[0],'prompt':obs['prompt'],'rule_count_before':obs['before_rule_count'],'rule_count_after':obs['after_rule_count'],'used_uid_count':len(obs['used_rule_uids']),'mapped_uid_count':len(obs['mapped_rules']),'active_rule_ids':len(meta),'candidate_tests':g.get('cand_tested',0),'candidate_expansions':g.get('cand_enum',0),'term_evaluations':g.get('term_evals_total',0),'term_units':g.get('term_units_total',0),'unattributed_candidate_tests':g.get('cand_tested_unattributed',0),'unattributed_term_evaluations':g.get('term_evals_unattributed',0),'per_rule':c['per_rule']})
 req(len(digests)==1 and None not in digests,'semantic graph digest differs across audit modes or workers')
 for rep in (0,1,2):
  if (rep,'off') in runs and (rep,'on') in runs:
   off,on=runs[(rep,'off')],runs[(rep,'on')]
   req(turn_projection(off['capture']['task_result'])==turn_projection(on['capture']['task_result']),'task behavior differs by audit mode '+str(rep))
   req(off['capture']['graph_semantic_sha256']==on['capture']['graph_semantic_sha256'],'paired graph digest differs '+str(rep))
 req(uid_total==mapped_total and unmapped_total==0,'aggregate runtime UID resolution')
 req(global_on==6,'expected six audit-on request captures')
 out={'schema':'LiveRuntimeClosureCountersV1Analysis','passed':not errors,'errors':errors,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'worker_count':len(runs),'request_count':sum(len(r['native_counter_observations']) for r in runs.values()),'audit_on_request_count':global_on,'semantic_graph_digest_count':len(digests),'runtime_rule_uid_observations':uid_total,'mapped_rule_uid_observations':mapped_total,'unmapped_rule_uid_observations':unmapped_total,'requests':rows,'claim_boundary':raw['design']['claim_limit']}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'errors':errors[:30],'error_count':len(errors),'workers':len(runs),'requests':out['request_count'],'audit_on':global_on,'uids':uid_total,'mapped':mapped_total,'unmapped':unmapped_total,'digests':len(digests)},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
