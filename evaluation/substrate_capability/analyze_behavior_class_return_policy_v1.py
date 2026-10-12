#!/usr/bin/env python3
"""Replay a finite behavior-class return policy from locked v1 captures."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/primitive_semantic_equivalence_v1_lock_20261003.json'
RAW=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_20261003.json'
BASE=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_analysis_20261003.json'
OUT=ROOT/'evaluation/reports/behavior_class_return_policy_v1_analysis_20261003.json'
SCRIPT=Path(__file__).resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());base=json.loads(BASE.read_text())
 errors=[]
 if base.get('passed')!=base.get('total') or base.get('total')!=7:errors.append('upstream semantic-equivalence analysis not fully passing')
 if raw.get('lock_sha256')!=sha(LOCK):errors.append('upstream lock hash mismatch')
 if raw.get('sources')!=lock.get('sources'):errors.append('upstream source map mismatch')
 if len(raw.get('workers',[]))!=25:errors.append('expected 25 panels')
 rows=[]
 for w in raw.get('workers',[]):
  for domain in ('original','zero_aware'):
   r=w[domain];surv=r.get('scored_survivors',[]);classes=r.get('equivalence_classes',[])
   ids=[x['id'] for x in surv];class_ids=[i for c in classes for i in c]
   if sorted(ids)!=sorted(class_ids):errors.append(f"{w['task']}/{w['worker']}/{domain}: class partition mismatch")
   single_class=bool(surv) and len(classes)==1
   all_exact=bool(surv) and all(x['heldout'].get('exact') is True and x['heldout'].get('n')==6560 for x in surv)
   harmful=single_class and not all_exact
   help_obj=r.get('help');help_ns=help_obj.get('wall_ns') if help_obj else None
   help_has_exact=bool(help_obj) and any(h['heldout'].get('exact') for h in help_obj.get('hypotheses',[]))
   nprobe=len(lock['panels'][0]['zero_selection_pool'])+len(lock['panels'][0]['zero_challenge_pool']) if domain=='zero_aware' else len(lock['panels'][0]['original_selection_pool'])+len(lock['panels'][0]['original_challenge_order'])
   rows.append({'task':w['task'],'worker':w['worker'],'domain':domain,'labels':r['calls'],'survivor_count':len(surv),'behavior_class_count':len(classes),'single_class_return':single_class,'all_returned_members_exact_on_heldout':all_exact,'harmful_class_return':harmful,'current_help_called':bool(help_obj),'current_help_wall_ns':help_ns,'current_help_has_exact_candidate':help_has_exact,'class_evaluation_term_rows':len(surv)*nprobe})
 summary={}
 for domain in ('original','zero_aware'):
  rr=[x for x in rows if x['domain']==domain]
  current_help=[x for x in rr if x['current_help_called']]
  single=[x for x in rr if x['single_class_return']]
  summary[domain]={'panels':len(rr),'labels_total':sum(x['labels'] for x in rr),'single_class_returns':len(single),'class_return_exact_panels':sum(x['single_class_return'] and x['all_returned_members_exact_on_heldout'] for x in rr),'harmful_class_returns':sum(x['harmful_class_return'] for x in rr),'current_help_calls':len(current_help),'current_help_exact_candidate_panels':sum(x['current_help_has_exact_candidate'] for x in current_help),'class_evaluation_term_rows':sum(x['class_evaluation_term_rows'] for x in rr),'help_wall_ns_total':sum(x['current_help_wall_ns'] or 0 for x in current_help),'help_wall_ns_median':statistics.median([x['current_help_wall_ns'] for x in current_help]) if current_help else None}
 result={'schema':'BehaviorClassReturnPolicyV1Analysis','retrospective':True,'passed':not errors,'errors':errors,'policy_definition':'After the recorded query policy, return the entire survivor set without help if it forms one class over all supplied selection+challenge inputs; otherwise preserve abstention/help. Holdout labels are excluded from this decision and used only for evaluation.','upstream_sources':{'lock':sha(LOCK),'capture':sha(RAW),'base_analysis':sha(BASE),'analyzer':sha(SCRIPT)},'summary':summary,'panels':rows,'limits':['same five authored task families and five fixed panels each','class equality holds only on the supplied finite probe pool','holdout results evaluate policy output and were not policy inputs','teacher help is an oracle callback supplying task-relevant family','class-evaluation latency is not separately measured; term-row count is a work proxy','no deployed consumer or persistent rule update was tested']}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'summary':summary,'errors':errors},indent=2));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
