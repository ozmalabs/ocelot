#!/usr/bin/env python3
"""Independent replay for bounded Cartesian literal proposal stress v1."""
import hashlib,itertools,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/literal_proposal_budget_stress_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/literal_proposal_budget_stress_v1_20261004.json';OUT=ROOT/'evaluation/reports/literal_proposal_budget_stress_v1_analysis_20261004.json';KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(r):return tuple(struct.pack('>d',float(x)) for x in r)
def main():
 import literal_proposal_budget_stress_v1 as m,term_literal_joint_proposals_v1 as joint,term_literal_probe_repair_v1 as h
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());p=m.panel();errors=[];checks={};n=_native.Substrate()
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture binding')
 if m.source_map()!=lock.get('sources') or hashlib.sha256(canon(p)).hexdigest()!=lock.get('panel_sha256') or sha(m.JRAW)!=lock.get('upstream_joint_capture_sha256'):errors.append('source or panel drift')
 if not json.loads(m.JAN.read_text()).get('passed'):errors.append('upstream joint analysis')
 names=sorted(set().union(*(set(h.term_vars(z['term'])) for z in p['terms'])));bounds={}
 for z in p['terms']:
  for var,val in h.literal_bounds(z['term']):bounds.setdefault(var,set()).add(float(val))
 vars_=[v for v in names if bounds.get(v)];product_count=1
 for v in vars_:product_count*=len(bounds[v])
 if product_count!=256:errors.append('cartesian product cardinality')
 denied={fpkey(z['row']) for z in p['training']}|{fpkey(z) for z in p['prior_pool']}|{fpkey(z) for z in p['holdout']};edge,literal=h.probe_slates(p);base=edge+literal;seen={fpkey(z) for z in base};extra=[]
 for vals in itertools.product(*(sorted(bounds[v]) for v in vars_)):
  env={k:0. for k in KEYS};env.update(dict(zip(vars_,vals)));row=[env[k] for k in KEYS]
  if fpkey(row) not in denied and fpkey(row) not in seen:extra.append(row)
 if len(extra)!=lock['total_joint_rows'] or len(extra)>product_count:errors.append('joint slate count')
 if raw.get('panel')!=p or raw.get('total_joint_rows')!=len(extra):errors.append('locked inputs')
 witness=p['witness'];witness_truth=float(witness[0])==float(witness[2])
 if classify(n.evaluate(p['terms'][1]['term'],dict(zip(KEYS,witness)))) is not True or witness_truth:errors.append('false witness construction')
 arms={a.get('policy'):a for a in raw.get('arms',[])}
 if set(arms)!={'exhaustive','budgeted_64'}:errors.append('arm identity')
 details={}
 for name,probes,incomplete in [('exhaustive',base+extra,False),('budgeted_64',base+extra[:m.BUDGET],len(extra)>m.BUDGET)]:
  a=arms.get(name,{})
  if a.get('probe_rows')!=probes or a.get('incomplete')!=incomplete:errors.append(f'{name}: proposal slate')
  if any(fpkey(x) in denied for x in probes) or len({fpkey(x) for x in probes})!=len(probes):errors.append(f'{name}: probe overlap')
  calls=0
  def ev(term,env):
   nonlocal calls
   calls+=1;return classify(n.evaluate(term,env))
  survivors=p['terms'][:];prior=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in p['prior_pool']]);events=[];used=set()
  while len(survivors)>1 and len(events)<m.CAP:
   available=[dict(zip(KEYS,r)) for r in probes if fpkey(r) not in used];choice=select_discriminating_input(ev,survivors,available,[])
   if not choice.get('ok'):break
   q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(h.truth(p['task'],row));before=[z['id'] for z in survivors];survivors=[z for z in survivors if ev(z['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[z['id'] for z in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
  part=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in probes]);underlying='accept_behavior_class' if survivors and part['all_agree_on_probes'] else 'request_help';final='request_help' if incomplete and underlying=='accept_behavior_class' else underlying
  if a.get('events')!=events or a.get('survivor_ids')!=[z['id'] for z in survivors] or a.get('underlying_decision')!=underlying or a.get('decision')!=final:errors.append(f'{name}: selector/decision replay')
  scores=[]
  for z in p['terms']:
   bad=invalid=0
   for row in p['holdout']:
    pred=classify(n.evaluate(z['term'],dict(zip(KEYS,row))));y=bool(h.truth(p['task'],row))
    if pred is None:invalid+=1
    elif pred is not y:bad+=1
   scores.append({'id':z['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':invalid})
  if a.get('holdout_scores')!=scores or a.get('native_evaluations')!=calls:errors.append(f'{name}: holdout/cost replay')
  false=underlying=='accept_behavior_class' and p['terms'][1]['id'] in [z['id'] for z in survivors] and any(s['mismatches'] or s['invalid'] for s in scores if s['id']==p['terms'][1]['id'])
  details[name]={'generated_joint_rows':len(extra) if name=='exhaustive' else min(len(extra),m.BUDGET),'incomplete':incomplete,'underlying_decision':underlying,'decision':final,'false_acceptance':bool(false and final=='accept_behavior_class'),'labels':len(events),'native_evaluations':calls,'wall_ns':a.get('wall_ns'),'holdout_scores':scores}
 checks={'lock_and_upstream_binding':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'256_candidate_product':product_count==256 and len(extra)==256-len(seen.intersection({fpkey(r) for r in extra})),'proposal_replay_and_disjointness':not any('slate' in e or 'overlap' in e or 'count' in e for e in errors),'selector_holdout_and_cost_replay':not any('replay' in e for e in errors),'witness_is_real_counterexample':not any('witness' in e for e in errors),'exhaustive_finds_and_rejects':details.get('exhaustive',{}).get('decision')=='accept_behavior_class' and not details.get('exhaustive',{}).get('false_acceptance') and details.get('exhaustive',{}).get('labels')==1,'capped_policy_abstains_on_incomplete_slate':details.get('budgeted_64',{}).get('incomplete') and details.get('budgeted_64',{}).get('decision')=='request_help' and not details.get('budgeted_64',{}).get('false_acceptance')}
 result={'schema':'LiteralProposalBudgetStressV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cartesian_product_size':product_count,'generated_joint_rows':len(extra),'cells':details,'claim_boundary':'One authored four-variable guard with contradictory literal noise demonstrates Cartesian growth and the behavior of one fail-closed proposal cap. It is not a prevalence estimate or general tractability theorem.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
