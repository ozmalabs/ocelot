#!/usr/bin/env python3
"""Independent acceptance replay for registered seed-root admission census."""
from __future__ import annotations
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
from registered_seed_profile_admission_census_v1 import LOCK,OUT as CAPTURE,RUNNER,PROTOCOL,lock_inputs
ANALYZER=Path(__file__).resolve();CHECKER=ROOT/'scripts/analyze_mint_termination_fragment.py'
ANALYSIS=ROOT/'evaluation/reports/registered_seed_profile_admission_census_v1_1_analysis_20261005.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def independent_accept(rule,edge_attr_types):
 if not isinstance(rule,dict) or set(rule)-{'name','match','effects'}:return False
 match=rule.get('match');effects=rule.get('effects')
 if not isinstance(match,list) or not match or any(not isinstance(p,list) or len(p)!=3 or not all(isinstance(x,str) for x in p) for p in match):return False
 available={v for p in match for v in (p[0],p[2])}
 if not isinstance(effects,list) or not effects:return False
 for e in effects:
  if not isinstance(e,list) or not e or not isinstance(e[0],str):return False
  if e[0]=='add_node_if_absent' and len(e)==4:
   _,v,t,attrs=e
   if not isinstance(v,str) or v in available or not isinstance(t,str) or not isinstance(attrs,dict):return False
   if any(not isinstance(k,str) or not(vv is None or isinstance(vv,(bool,int,str))) for k,vv in attrs.items()):return False
   available.add(v)
  elif e[0]=='add_edge' and len(e)==5:
   _,a,t,b,attrs=e
   if not all(isinstance(x,str) for x in (a,t,b)) or attrs!={} or a not in available or b not in available or t in edge_attr_types:return False
  else:return False
 return True
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(CAPTURE.read_text());stable=lock_inputs()==lock['locked_inputs']
 per_root=[];reason_counts=collections.Counter();decision_n=0;agrees=True
 for p in raw['profiles']:
  if p['status']!='booted':
   per_root.append({'root_seed':p['root_seed'],'status':p['status'],'missing_manifests':p['missing_manifests'],'active_rules':0,'candidate_profile':False});continue
  edge_types=set(p['edge_attr_types']);ind=[independent_accept(r,edge_types) for r in p['rule_specs']]
  reported=[bool(r['accepted']) for r in p['rule_checkers']];same=len(ind)==len(reported) and all(a==b for a,b in zip(ind,reported))
  decision_n+=len(ind);agrees &= same
  for result in p['rule_checkers']:
   reason_counts.update(result.get('reasons',[]))
  whole=bool(ind) and all(ind);agg=bool(p['aggregate_checker']['accepted'])
  if ind and agg!=whole:agrees=False
  if not ind and not agg:agrees=False
  per_root.append({'root_seed':p['root_seed'],'status':'booted','resolved_seed_order':p['resolved_seed_order'],'active_rules':len(ind),'individually_accepted_rules':sum(ind),'profile_accepted':whole,'aggregate_checker_accepted':agg,'checker_independent_agreement':same})
 root_ids=lock['locked_inputs']['seed_registry_order'];statuses=[p['status'] for p in raw['profiles']]
 candidates=[p['root_seed'] for p in per_root if p['status']=='booted' and p['active_rules']>0 and p['profile_accepted']]
 checks={'raw_lock_equals_lock_file':raw['locked_inputs']==lock['locked_inputs'] and raw['post_run_inputs']==lock['locked_inputs'],'current_sources_match_lock':stable,'registered_root_population_exact':len(raw['profiles'])==len(root_ids)==len(set(root_ids)) and [p['root_seed'] for p in raw['profiles']]==root_ids,'all_known_roots_have_explicit_outcome':all(x in ('booted','root_manifest_missing','dependency_manifest_missing') for x in statuses),'all_rule_decisions_match_independent_predicate':agrees,'missing_profiles_not_counted_as_candidates':all(not p['candidate_profile'] for p in per_root if p['status']!='booted'),'analysis_script_stable':sha(ANALYZER)==lock['locked_inputs']['analyzer_sha256']}
 out={'schema':'RegisteredSeedProfileAdmissionCensusV1Analysis','lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE),'analyzer_sha256':sha(ANALYZER),'summary':{'registered_roots':len(root_ids),'booted_profiles':statuses.count('booted'),'root_manifest_missing':statuses.count('root_manifest_missing'),'dependency_manifest_missing':statuses.count('dependency_manifest_missing'),'nonempty_profiles':sum(p['status']=='booted' and p['active_rules']>0 for p in per_root),'active_rule_instances':decision_n,'individually_accepted_rule_instances':sum(p.get('individually_accepted_rules',0) for p in per_root),'fully_accepted_nonempty_profiles':candidates,'rejection_reason_occurrences':dict(reason_counts)},'per_root':per_root,'checks':checks,'passed':all(checks.values()),'claim_limit':raw['claim_limit']}
 ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':out['summary'],'analysis':ANALYSIS.relative_to(ROOT).as_posix()},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
