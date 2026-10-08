#!/usr/bin/env python3
"""Prospective arity/operator sweep for finite literal-boundary probes."""
import hashlib,json,platform,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
RUN=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/TERM_LITERAL_ADVERSARIAL_FAMILY_V1_PREREG_20261004.md';AN=ROOT/'evaluation/substrate_capability/analyze_term_literal_adversarial_family_v1.py';HELP=ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/term_literal_adversarial_family_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/term_literal_adversarial_family_v1_20261004.json'
UP=ROOT/'evaluation/substrate_capability/term_literal_probe_repair_v1_lock_20261004.json';UPRAW=ROOT/'evaluation/reports/term_literal_probe_repair_v1_20261004.json';UPAN=ROOT/'evaluation/reports/term_literal_probe_repair_v1_analysis_20261004.json'
VARS=('ax','ay','ex','ey')
_NATIVE=None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native build')
 ps=[RUN,PRE,AN,HELP,UP,UPRAW,UPAN,ROOT/'domains/contract_query.py']
 n=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in ps},'native':{'path':str(n),'sha256':sha(n)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def V(x):return {'type':'Var','name':x}
def L(x):return {'type':'Lit','value':x}
def cmp(t,a,b):return {'type':t,'a':a,'b':b}
def guard_term(arity,kind):
 vars=list(VARS[:arity]);parts=[];vals=[]
 for i,v in enumerate(vars):
  lo=float(10+10*i);hi=lo+0.5;mid=(lo+hi)/2;vals.append(lo if kind=='point' else mid)
  if kind=='interval':parts.extend([cmp('Gte',V(v),L(lo)),cmp('Lt',V(v),L(hi))])
  else:parts.append(cmp('Eq',V(v),L(lo)))
 guard={'type':'And','items':parts} if len(parts)>1 else parts[0]
 return {'type':'Or','items':[cmp('Eq',V('ax'),V('ex')),guard]},vals
def truth(row):return float(row[0])==float(row[2])
def guard_hit(term,row):
 global _NATIVE
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 if _NATIVE is None:_NATIVE=_native.Substrate()
 return classify(_NATIVE.evaluate(term,dict(zip(VARS,row)))) is True
def panels():
 import term_directed_edge_operator_transfer_v2 as base
 src=next(p for p in base.panels() if p['name']=='structured_literal_alias');res=[]
 for arity in (2,3,4):
  for kind in ('interval','point'):
   term,values=guard_term(arity,kind);hid=f'{kind}_arity_{arity}'
   # All candidates fit the frozen examples and prior; holdout includes a positive guard witness.
   rows=[list(r) for r in src['holdout'] if not guard_hit(term,r)]
   witness=[0.,0.,0.,0.]
   for v,x in zip(VARS[:arity],values):witness[VARS.index(v)]=x
   if kind=='interval':rows.append(witness)
   rows=rows[:4096]
   res.append({'name':hid,'task':'identity','terms':[src['terms'][0],{'id':hid,'term':term}],'training':src['training'],'prior_pool':src['prior_pool'],'holdout':rows,'guard_arity':arity,'guard_kind':kind,'witness':witness,'label_cap':8})
 return res
def main():
 import term_literal_probe_repair_v1 as helper
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  if not json.loads(UPAN.read_text()).get('passed'):raise SystemExit('upstream literal repair invalid')
  ps=panels();LOCK.write_text(json.dumps({'schema':'TermLiteralAdversarialFamilyV1Lock','sources':source_map(),'upstream_lock_sha256':sha(UP),'upstream_capture_sha256':sha(UPRAW),'panels':ps,'paired_policies':['edge_only','edge_plus_literal']},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  lock=json.loads(LOCK.read_text());ps=panels()
  if lock['sources']!=source_map() or lock['panels']!=ps or sha(UPRAW)!=lock['upstream_capture_sha256']:raise SystemExit('source/panel drift')
  results=[]
  for p in ps:
   q=dict(p);q['task']='identity';r=helper.worker(q);r.update({'guard_arity':p['guard_arity'],'guard_kind':p['guard_kind'],'witness':p['witness']});results.append(r)
  OUT.write_text(json.dumps({'schema':'TermLiteralAdversarialFamilyV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'workers':results,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage --lock | --run')
if __name__=='__main__':raise SystemExit(main())
