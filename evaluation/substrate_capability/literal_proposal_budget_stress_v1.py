#!/usr/bin/env python3
"""Measure exhaustive versus fail-closed capped literal products."""
import hashlib,itertools,json,platform,struct,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/LITERAL_PROPOSAL_BUDGET_STRESS_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_literal_proposal_budget_stress_v1.py';JOINT=ROOT/'evaluation/substrate_capability/term_literal_joint_proposals_v1.py';JLOCK=ROOT/'evaluation/substrate_capability/term_literal_joint_proposals_v1_lock_20261004.json';JRAW=ROOT/'evaluation/reports/term_literal_joint_proposals_v1_20261004.json';JAN=ROOT/'evaluation/reports/term_literal_joint_proposals_v1_analysis_20261004.json';FAMILY=ROOT/'evaluation/substrate_capability/term_literal_adversarial_family_v1.py';FLOCK=ROOT/'evaluation/substrate_capability/term_literal_adversarial_family_v1_lock_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/literal_proposal_budget_stress_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/literal_proposal_budget_stress_v1_20261004.json';CAP=8;BUDGET=64;KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(r):return tuple(struct.pack('>d',float(x)) for x in r)
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,JOINT,JLOCK,JRAW,JAN,FAMILY,FLOCK,ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1.py',ROOT/'domains/contract_query.py']
 b=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def panel():
 import term_literal_adversarial_family_v1 as f
 import term_literal_probe_repair_v1 as h
 p=next(x for x in f.panels() if x['name']=='interval_arity_4');q=dict(p);q['name']='irrelevant_literal_noise_arity_4';q['terms']=p['terms'][:]
 vals={'ax':100.25,'ay':110.25,'ex':120.25,'ey':130.25};parts=[]
 for i,v in enumerate(KEYS):
  lo=100.+10*i;hi=lo+.5;parts.extend([{'type':'Gte','a':h.V(v),'b':h.L(lo)},{'type':'Lt','a':h.V(v),'b':h.L(hi)}])
 main={'type':'And','items':parts};noise=[]
 for i,v in enumerate(KEYS):noise.extend([{'type':'Gte','a':h.V(v),'b':h.L(90.+10*i)},{'type':'Lt','a':h.V(v),'b':h.L(80.+10*i)}])
 impossible={'type':'And','items':noise};guard={'type':'Or','items':[main,impossible]};term={'type':'Or','items':[{'type':'Eq','a':h.V('ax'),'b':h.V('ex')},guard]}
 q['terms']=[q['terms'][0],{'id':'noise_padded_interval_alias','term':term}];q['witness']=[vals[v] for v in KEYS]
 n=None
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 n=_native.Substrate();rows=[]
 for row in q['holdout']:
  if classify(n.evaluate(term,dict(zip(KEYS,row)))) is not True:rows.append(list(row))
 rows.append(q['witness']);q['holdout']=rows[:4096]
 return q
def all_joint(panel):
 import term_literal_probe_repair_v1 as h
 names=sorted(set().union(*(set(h.term_vars(z['term'])) for z in panel['terms'])));bounds={}
 for z in panel['terms']:
  for v,x in h.literal_bounds(z['term']):bounds.setdefault(v,set()).add(float(x))
 vars_=[v for v in names if bounds.get(v)];count=1
 for v in vars_:count*=len(bounds[v])
 if count!=256:raise RuntimeError(f'unexpected product size {count}')
 denied={fpkey(z['row']) for z in panel['training']}|{fpkey(z) for z in panel['prior_pool']}|{fpkey(z) for z in panel['holdout']}
 edge,literal=h.probe_slates(panel);base=edge+literal;seen={fpkey(z) for z in base};rows=[]
 for tup in itertools.product(*(sorted(bounds[v]) for v in vars_)):
  env={k:0. for k in KEYS};env.update(dict(zip(vars_,tup)));row=[env[k] for k in KEYS]
  if fpkey(row) not in denied and fpkey(row) not in seen:rows.append(row)
 return base,rows
def arm(p,policy,probes,incomplete):
 import term_literal_probe_repair_v1 as h
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 n=_native.Substrate();q=h.policy(n,p,probes);underlying=q['decision'];final='request_help' if incomplete and underlying=='accept_behavior_class' else underlying;scores=[]
 for z in p['terms']:
  bad=invalid=0
  for row in p['holdout']:
   pred=classify(n.evaluate(z['term'],dict(zip(KEYS,row))));y=bool(h.truth(p['task'],row))
   if pred is None:invalid+=1
   elif pred is not y:bad+=1
  scores.append({'id':z['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':invalid})
 false=underlying=='accept_behavior_class' and p['terms'][1]['id'] in q['survivor_ids'] and any((s['mismatches'] or s['invalid']) for s in scores if s['id']==p['terms'][1]['id'])
 return {'policy':policy,'incomplete':incomplete,'probe_rows':probes,'events':q['events'],'survivor_ids':q['survivor_ids'],'underlying_decision':underlying,'decision':final,'false_acceptance':bool(false and final=='accept_behavior_class'),'holdout_scores':scores,'native_evaluations':q['native_evaluations'],'wall_ns':q['wall_ns'],'cpu_ns':q['cpu_ns']}
def capture(p):
 base,extra=all_joint(p);return {'panel':p,'total_joint_rows':len(extra),'arms':[arm(p,'exhaustive',base+extra,False),arm(p,'budgeted_64',base+extra[:BUDGET],len(extra)>BUDGET)]}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(JAN.read_text()).get('passed'):raise SystemExit('joint proposal upstream invalid')
  p=panel();base,extra=all_joint(p);LOCK.write_text(json.dumps({'schema':'LiteralProposalBudgetStressV1Lock','sources':source_map(),'upstream_joint_lock_sha256':sha(JLOCK),'upstream_joint_capture_sha256':sha(JRAW),'panel_sha256':hashlib.sha256(canon(p)).hexdigest(),'base_proposal_count':len(base),'total_joint_rows':len(extra),'budget':BUDGET,'label_cap':CAP},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text());p=panel();base,extra=all_joint(p)
  if source_map()!=l['sources'] or hashlib.sha256(canon(p)).hexdigest()!=l['panel_sha256'] or sha(JRAW)!=l['upstream_joint_capture_sha256']:raise SystemExit('source/panel drift')
  res=capture(p)
  if source_map()!=l['sources']:raise SystemExit('source drift during capture')
  OUT.write_text(json.dumps({'schema':'LiteralProposalBudgetStressV1Results','lock_sha256':sha(LOCK),'sources':source_map(),**res,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
