#!/usr/bin/env python3
"""Replay predeclared agreement thresholds on the frozen grammar-expansion trace."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runners/dsl/python'))
CAP=ROOT/'evaluation/reports/numeric_opposition_cegis_grammar_expansion_v1_2_20261003.json';LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_cegis_grammar_expansion_v1_2_lock_20261003.json';OUT=ROOT/'evaluation/reports/numeric_opposition_cegis_stop_rule_v1_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r):return (r[0]==-r[2]) != (r[1]==-r[3])
def score(n,term,grid):
 fp=fn=0
 for r in itertools.product(grid,repeat=4):
  y=truth(r);p=bool(n.evaluate(term,env(r)))
  if p and not y:fp+=1
  if y and not p:fn+=1
 return {'exact':not(fp or fn),'fp':fp,'fn':fn}
def main():
 from substrate_rs import _native
 cap=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text());n=_native.Substrate();threshold_rows=[]
 for k in range(1,7):
  outcomes=[]
  for w in cap['workers']:
   streak=0;chosen=None;used=None;stop=None
   for i,e in enumerate(w['repair_events'],1):
    streak=0 if e['disagrees'] else streak+1
    if streak>=k:
     chosen=e['candidate_term'];used=i;stop='agreement_threshold';break
   if chosen is None:
    chosen=w['final_term'];used=len(w['repair_events']);stop='trace_exhausted'
   s=score(n,chosen,lock['heldout_grid']) if chosen is not None else {'exact':False,'fp':None,'fn':None}
   outcomes.append({'worker':w['worker'],'exact':s['exact'],'fp':s['fp'],'fn':s['fn'],'additional_labels':used,'labels_saved':12-used,'stop':stop})
  threshold_rows.append({'k':k,'exact_workers':sum(x['exact'] for x in outcomes),'false_singletons':sum(not x['exact'] for x in outcomes),'median_additional_labels':statistics.median(x['additional_labels'] for x in outcomes),'total_additional_labels':sum(x['additional_labels'] for x in outcomes),'total_labels_saved':sum(x['labels_saved'] for x in outcomes),'workers':outcomes})
 out={'schema':'NumericOppositionCegisStopRuleV1Results','thresholds':threshold_rows,'input_hashes':{'capture':sha(CAP),'lock':sha(LOCK),'protocol':sha(ROOT/'docs/research/engine_substrate/NUMERIC_OPPOSITION_CEGIS_STOP_RULE_V1_PREREG_20261003.md'),'analyzer':sha(Path(__file__))},'interpretation':'Retrospective stopping replay; no general reliability guarantee.'}
 if OUT.exists():raise SystemExit('refusing overwrite')
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
