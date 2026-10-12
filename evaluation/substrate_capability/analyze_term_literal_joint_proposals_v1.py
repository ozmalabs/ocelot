#!/usr/bin/env python3
"""Independent replay for joint literal proposal experiment v1."""
import hashlib,itertools,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/term_literal_joint_proposals_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/term_literal_joint_proposals_v1_20261004.json';OUT=ROOT/'evaluation/reports/term_literal_joint_proposals_v1_analysis_20261004.json';KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(row):return tuple(struct.pack('>d',float(x)) for x in row)
def main():
 import term_literal_joint_proposals_v1 as m,term_literal_adversarial_family_v1 as family,term_literal_probe_repair_v1 as h
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());ps=family.panels();errors=[];details=[];n=_native.Substrate()
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture binding')
 if m.source_map()!=lock.get('sources') or sha(m.FRAW)!=lock.get('family_capture_sha256') or {p['name']:hashlib.sha256(canon(p)).hexdigest() for p in ps}!=lock.get('panel_sha256'):errors.append('source or panel drift')
 if not json.loads(m.FAN.read_text()).get('passed'):errors.append('upstream family analysis')
 workers=raw.get('workers',[])
 if len(workers)!=6:errors.append('panel count')
 for p,w in zip(ps,workers):
  if w.get('name')!=p['name']:errors.append(f"{p['name']}: panel identity")
  edge,literal=h.probe_slates(p);pair=edge+literal
  names=sorted(set().union(*(set(h.term_vars(z['term'])) for z in p['terms'])));bounds={}
  for z in p['terms']:
   for var,val in h.literal_bounds(z['term']):bounds.setdefault(var,set()).add(float(val))
  vars_=[v for v in names if bounds.get(v)];count=1
  for v in vars_:count*=len(bounds[v])
  if count>m.JOINT_CAP:errors.append(f"{p['name']}: joint cap")
  forbid={fpkey(z['row']) for z in p['training']}|{fpkey(z) for z in p['prior_pool']}|{fpkey(z) for z in p['holdout']};joint=[]
  for values in itertools.product(*(sorted(bounds[v]) for v in vars_)):
   env={k:0. for k in KEYS};env.update(dict(zip(vars_,values)));row=[env[k] for k in KEYS]
   if fpkey(row) not in forbid and fpkey(row) not in {fpkey(z) for z in pair+joint}:joint.append(row)
  if w.get('pairwise_probe_count')!=len(pair) or w.get('joint_probe_count')!=len(joint):errors.append(f"{p['name']}: proposal counts")
  arms={z.get('policy'):z for z in w.get('arms',[])}
  if set(arms)!={'pairwise_literal','joint_literal'}:errors.append(f"{p['name']}: arm identity");continue
  cell={}
  for policy,probes in [('pairwise_literal',pair),('joint_literal',pair+joint)]:
   a=arms[policy]
   if a.get('probe_rows')!=probes:errors.append(f"{p['name']}/{policy}: proposal replay")
   if len({fpkey(x) for x in probes})!=len(probes) or any(fpkey(x) in forbid for x in probes):errors.append(f"{p['name']}/{policy}: probe overlap")
   calls=0
   def ev(term,env):
    nonlocal calls
    calls+=1;return classify(n.evaluate(term,env))
   survivors=p['terms'][:];prior=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in p['prior_pool']]);events=[];used=set()
   while len(survivors)>1 and len(events)<m.CAP:
    available=[dict(zip(KEYS,r)) for r in probes if fpkey(r) not in used];choice=select_discriminating_input(ev,survivors,available,[])
    if not choice.get('ok'):break
    q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(h.truth(p['task'],row));before=[z['id'] for z in survivors];survivors=[z for z in survivors if ev(z['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[z['id'] for z in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
   part=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in probes]);decision='accept_behavior_class' if survivors and part['all_agree_on_probes'] else 'request_help'
   if a.get('prior_partition')!=prior or a.get('events')!=events or a.get('survivor_ids')!=[z['id'] for z in survivors] or a.get('final_partition')!=part or a.get('decision')!=decision:errors.append(f"{p['name']}/{policy}: selector replay")
   scores=[]
   for z in p['terms']:
    mismatch=invalid=0
    for row in p['holdout']:
     pred=classify(n.evaluate(z['term'],dict(zip(KEYS,row))));y=bool(h.truth(p['task'],row))
     if pred is None:invalid+=1
     elif pred is not y:mismatch+=1
    scores.append({'id':z['id'],'n':len(p['holdout']),'mismatches':mismatch,'invalid':invalid})
   if a.get('holdout_scores')!=scores:errors.append(f"{p['name']}/{policy}: holdout replay")
   if a.get('native_evaluations')!=calls:errors.append(f"{p['name']}/{policy}: cost replay")
   bad=decision=='accept_behavior_class' and p['terms'][1]['id'] in [z['id'] for z in survivors] and fpkey(p['witness']) not in {fpkey(e['row']) for e in events}
   cell[policy]={'decision':decision,'labels':len(events),'false_candidate_unfalsified':bool(bad),'survivors':[z['id'] for z in survivors],'native_evaluations':calls,'wall_ns':a.get('wall_ns'),'cpu_ns':a.get('cpu_ns')}
  details.append({'panel':p['name'],'arity':p['guard_arity'],'kind':p['guard_kind'],'pairwise_proposals':len(pair),'joint_proposals':len(joint),'cells':cell})
 checks={'lock_and_upstream_binding':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'six_panel_replay':len(details)==6 and not any('identity' in e for e in errors),'joint_generation_and_disjointness':not any('proposal' in e or 'overlap' in e or 'cap' in e for e in errors),'selector_and_cost_replay':not any('selector replay' in e or 'cost replay' in e for e in errors),'holdout_replay':not any('holdout replay' in e for e in errors),'joint_policy_repairs_all_six':all(not d['cells'].get('joint_literal',{}).get('false_candidate_unfalsified') and d['cells'].get('joint_literal',{}).get('labels',m.CAP+1)<=m.CAP for d in details),'cost_reported_by_guard_arity':all(d['joint_proposals']>=0 and d['cells'].get('joint_literal',{}).get('native_evaluations',0)>0 for d in details)}
 res={'schema':'TermLiteralJointProposalsV1Analysis','passed':all(checks.values()) and not errors,'checks':checks,'errors':errors,'cells':details,'claim_boundary':'Joint literal combinations repair this six-cell authored guard family under a cap of 64 proposals and eight labels. The measured Cartesian growth is not a general scaling theorem or natural-task prevalence estimate.'}
 OUT.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n');print(json.dumps(res,indent=2,sort_keys=True));return 0 if res['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
