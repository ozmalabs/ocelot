#!/usr/bin/env python3
"""Independent deterministic replay and holdout scoring for Term audit v1."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
LOCK=ROOT/'evaluation/substrate_capability/term_conditioned_audit_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/term_conditioned_audit_v1_20261004.json';OUT=ROOT/'evaluation/reports/term_conditioned_audit_v1_analysis_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import term_conditioned_audit_v1 as m
 import adaptive_factored_operator_search_v1 as ad
 from substrate_rs import _native
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());up=json.loads(m.UPRAW.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture/lock/source binding')
 if m.source_map()!=lock.get('sources') or m.panels()!=lock.get('panels'):errors.append('current source/panel drift')
 if sha(m.UPRAW)!=lock['upstream_capture_sha256'] or sha(m.CLRAW)!=lock['conditioned_capture_sha256'] or sha(m.GRAW)!=lock['generic_capture_sha256']:errors.append('upstream capture binding')
 if not json.loads(m.CLOUT.read_text()).get('passed') or not json.loads(m.GOUT.read_text()).get('passed'):errors.append('paired baseline analysis')
 rows=raw.get('workers',[]);panels=lock.get('panels',[]);uprows=up.get('workers',[]);n=_native.Substrate();caps=m.CAPS
 agg={c:{'panels':0,'correct_accepts':0,'false_accepts':0,'help':0,'labels':[],'term_evaluations':[]} for c in caps}; by={t:{c:{'panels':0,'correct_accepts':0,'false_accepts':0,'help':0,'labels':[],'term_evaluations':[]} for c in caps} for t in m.TASKS};details=[]
 held={tuple(x) for x in itertools.product((-2.5,-1.5,-.5,.5,1.5,2.5),repeat=4)}
 if len(rows)!=20:errors.append('panel count')
 for i,(w,p,u) in enumerate(zip(rows,panels,uprows)):
  if any(w.get(k)!=p.get(k) or p.get(k)!=u.get(k) for k in ('task','worker','seed')):errors.append(f'{i}: panel binding')
  cand=next((h for h in u.get('final_terms',[]) if h['id']==u.get('accepted_id')),None)
  if w.get('candidate_id')!=u.get('accepted_id') or w.get('candidate_term')!=(None if cand is None else cand['term']):errors.append(f'{i}: candidate binding')
  forbidden=[x['row'] for x in p['training']]+p['selection_pool']
  chosen,evals,wall,cpu,counts=m.proposals(p['task'],p['seed'],None if cand is None else cand['term'],forbidden,n) if cand else ([],0,0,0,{'true':0,'false':0,'proposals':0})
  if w.get('proposal_stream')!=chosen or w.get('native_term_evaluations')!=evals or w.get('proposal_counts')!=counts:errors.append(f'{i}: proposal replay/count')
  events=[];stop=None
  for j,item in enumerate(chosen):
   row=item['row'];pred=item['prediction'];label=bool(m.truth(p['task'],row));events.append({'index':j,'proposal_index':item['proposal_index'],'row':row,'prediction':pred,'label':label,'match':pred is label})
   if tuple(row) in held or tuple(row) in {tuple(map(float,x)) for x in forbidden}:errors.append(f'{i}: sample overlap')
   if pred is not label:stop=j+1;break
  if w.get('events')!=events or w.get('first_mismatch_labels')!=stop:errors.append(f'{i}: oracle/stopping transcript')
  exact=bool(cand and ad.score(n,p['task'],cand['term'])['exact']); expected=[]
  for cap in caps:
   decision='request_help' if not cand or (stop is not None and stop<=cap) else 'accept';labels=0 if not cand else min(cap,len(events))
   expected.append({'cap':cap,'decision':decision,'labels':labels,'correct_accept':decision=='accept' and exact,'false_accept':decision=='accept' and not exact,'help':decision!='accept'})
   aa=agg[cap];tt=by[p['task']][cap]
   for x in (aa,tt):
    x['panels']+=1;x['correct_accepts']+=int(decision=='accept' and exact);x['false_accepts']+=int(decision=='accept' and not exact);x['help']+=int(decision!='accept');x['labels'].append(labels);x['term_evaluations'].append(evals)
  if w.get('outcomes')!=expected:errors.append(f'{i}: outcome mismatch')
  if w.get('help_control')!={'decision':'request_help','labels':0}:errors.append(f'{i}: help control')
  if w.get('proposal_wall_ns',0)<0 or w.get('proposal_cpu_ns',0)<0:errors.append(f'{i}: negative timing')
  details.append({'task':p['task'],'worker':p['worker'],'candidate_id':u.get('accepted_id'),'holdout_exact':exact if cand else None,'candidate_true_proposals':counts['true'],'candidate_false_proposals':counts['false'],'term_evaluations':evals,'first_mismatch_labels':stop,'outcomes':expected})
 for bundle in [agg,*by.values()]:
  for x in bundle.values():
   x['median_labels']=statistics.median(x.pop('labels')) if x['labels'] else None;x['median_term_evaluations']=statistics.median(x.pop('term_evaluations')) if x['term_evaluations'] else None
 checks={'twenty_paired_candidates':len(rows)==20,'provenance_and_baseline_binding':not any('binding' in e or 'drift' in e or 'baseline' in e for e in errors),'term_conditioned_proposals_replay':not any('proposal replay' in e for e in errors),'disjoint_balanced_candidate_classes':not any('overlap' in e for e in errors),'oracle_transcript_and_stopping':not any('transcript' in e for e in errors),'holdout_scoring_and_costs':not any('outcome mismatch' in e or 'candidate binding' in e for e in errors),'help_control_and_timing':not any('help control' in e or 'negative timing' in e for e in errors)}
 cond=json.loads(m.CLOUT.read_text()).get('by_task_and_policy',{});generic=json.loads(m.GOUT.read_text()).get('by_cap',{})
 res={'schema':'TermConditionedAuditV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'by_cap':agg,'by_task_and_cap':by,'cells':details,'comparison_reference':{'conditioned_audit':cond,'uniform_audit':generic},'claim_boundary':'Candidate-Term-conditioned finite-support post-search audit; policy is task blind but candidate aware, with no resynthesis or equivalence guarantee.'}
 OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True));return 0 if res['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
