#!/usr/bin/env python3
"""Post-capture check for domain coverage and semantic-vs-syntactic ambiguity."""
import hashlib,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'runners/dsl/python'))
from substrate_rs import _native
RAW=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_1_20261003.json';LOCK=ROOT/'evaluation/substrate_capability/primitive_menu_help_policy_v1_1_lock_20261003.json';ANALYSIS=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_1_analysis_20261003.json';SCRIPT=Path(__file__).resolve();OUT=ROOT/'evaluation/reports/primitive_menu_help_policy_v1_1_semantic_addendum_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());primary=json.loads(ANALYSIS.read_text());native=_native.Substrate();values=(-2.5,-1.5,-.5,0.,.5,1.5,2.5);keys=('ax','ay','ex','ey')
def truth(task,row):
 if task=='additive':return row[0]+row[1]==row[2]+row[3]
 if task=='product':return row[0]*row[1]==row[2]*row[3]
 if task=='ordering':return row[0]<row[2]
 if task=='opposition':return row[0]==-row[2]
 return row[0]!=row[2]
def exact(task,term):
 for row in itertools.product(values,repeat=4):
  try:pred=native.evaluate(term,dict(zip(keys,row)))
  except Exception:return False
  if type(pred)is not bool or pred!=truth(task,row):return False
 return True
by={}
for task in lock['tasks']:
 init={'panels':0,'panels_with_any_zero_inclusive_exact':0,'exact_candidates':0};policies={}
 for w in raw['workers']:
  if w['task']!=task:continue
  init['panels']+=1;init_exact=[h for arm in w['families'] for h in arm['hypotheses'] if exact(task,h['term'])];init['panels_with_any_zero_inclusive_exact']+=int(bool(init_exact));init['exact_candidates']+=len(init_exact)
  for p in w['policies']:
   name=p['policy']+('_help' if p['assisted'] else '_query_only');s=policies.setdefault(name,{'panels':0,'zero_inclusive_all_survivors_exact':0,'zero_inclusive_any_exact_survivor':0,'multi_survivor_panels':0,'exact_survivors':0,'help_calls':0,'help_exact_panels':0,'labels':[],'stops':{}});s['panels']+=1;s['labels'].append(p['calls']);s['help_calls']+=int(bool(p['help']));s['stops'][p['stop']]=s['stops'].get(p['stop'],0)+1
   exact_survivors=sum(exact(task,h['term']) for h in p['survivors']);s['exact_survivors']+=exact_survivors;s['zero_inclusive_any_exact_survivor']+=int(exact_survivors>0);s['zero_inclusive_all_survivors_exact']+=int(bool(p['survivors']) and exact_survivors==len(p['survivors']));s['multi_survivor_panels']+=int(len(p['survivors'])>1)
   if p['helped_result']:
    s['help_exact_panels']+=int(any(exact(task,h['term']) for h in p['helped_result']['hypotheses']))
 for s in policies.values():
  labels=sorted(s.pop('labels'));s['median_labels']=labels[(s['panels']-1)//2] if s['panels']%2 else sum(labels[s['panels']//2-1:s['panels']//2+1])/2
 by[task]={'initial_candidates':init,'policies':policies}
summary={'schema':'PrimitiveMenuHelpPolicyV1_1SemanticAddendum','classification':'post-capture descriptive analysis; added holdout scores are never policy inputs','source_hashes':{'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'primary_analysis_sha256':sha(ANALYSIS),'script_sha256':sha(SCRIPT)},'primary_analysis_passed':primary['passed']==primary['total'],'zero_inclusive_holdout':{'values':values,'n':len(values)**4},'by_task':by,'interpretation':'The original nonzero grid can hide domain-specific aliases. This zero-inclusive finite-grid audit checks semantic agreement; it does not prove universal correctness or provide a runtime adequacy certificate.'}
OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n');print(json.dumps(summary,indent=2,sort_keys=True))
