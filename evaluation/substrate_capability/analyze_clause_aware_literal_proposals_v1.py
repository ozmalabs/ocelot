#!/usr/bin/env python3
"""Independent replay for clause-aware literal proposal v1."""
import hashlib,itertools,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'evaluation/substrate_capability'),str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/clause_aware_literal_proposals_v1_lock_20261004.json';RAW=ROOT/'evaluation/reports/clause_aware_literal_proposals_v1_20261004.json';OUT=ROOT/'evaluation/reports/clause_aware_literal_proposals_v1_analysis_20261004.json';KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def fpkey(r):return tuple(struct.pack('>d',float(x)) for x in r)
def extract_clauses(term):
 out=[]
 def walk(x):
  if isinstance(x,dict):
   if x.get('type')=='And':
    items=x.get('items',[]);constraints=[]
    for item in items:
     if not isinstance(item,dict) or item.get('type') not in ('Eq','Lt','Lte','Gt','Gte'):
      constraints=[];break
     a=item.get('a',{});b=item.get('b',{});op=item['type']
     if a.get('type')=='Var' and b.get('type')=='Lit' and isinstance(b.get('value'),(int,float)):constraints.append((a['name'],op,float(b['value'])))
     elif b.get('type')=='Var' and a.get('type')=='Lit' and isinstance(a.get('value'),(int,float)):
      inv={'Lt':'Gt','Lte':'Gte','Gt':'Lt','Gte':'Lte','Eq':'Eq'};constraints.append((b['name'],inv[op],float(a['value'])))
     else:constraints=[];break
    if constraints:out.append(constraints)
   for z in x.values():walk(z)
  elif isinstance(x,list):
   for z in x:walk(z)
 walk(term);uniq=[]
 for c in out:
  if c not in uniq:uniq.append(c)
 return uniq
def sat(v,cs):
 for op,x in cs:
  if op=='Eq' and v!=x:return False
  if op=='Lt' and not v<x:return False
  if op=='Lte' and not v<=x:return False
  if op=='Gt' and not v>x:return False
  if op=='Gte' and not v>=x:return False
 return True
def replay_clause_rows(p,base):
 clauses=[]
 for h in p['terms']:clauses.extend(extract_clauses(h['term']))
 denied={fpkey(x['row']) for x in p['training']}|{fpkey(x) for x in p['prior_pool']}|{fpkey(x) for x in p['holdout']}|{fpkey(x) for x in base};rows=[];checks=0
 for branch in clauses:
  by={}
  for v,op,x in branch:by.setdefault(v,[]).append((op,x))
  env={k:0. for k in KEYS};valid=True
  for v,cs in by.items():
   candidates=set()
   for _,x in cs:candidates.update((x,math.nextafter(x,-math.inf),math.nextafter(x,math.inf)))
   match=[]
   for c in sorted(candidates):
    checks+=len(cs)
    if sat(c,cs):match.append(c)
   if not match:valid=False;break
   env[v]=match[0]
  if not valid or env['ax']==env['ex']:continue
  row=[env[k] for k in KEYS]
  if fpkey(row) not in denied and row not in rows:rows.append(row)
 return rows,len(clauses),checks
def main():
 import clause_aware_literal_proposals_v1 as m,literal_proposal_budget_stress_v1 as b,term_literal_probe_repair_v1 as h
 from substrate_rs import _native
 from adaptive_factored_operator_search_v1 import classify
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 lock=json.loads(LOCK.read_text());raw=json.loads(RAW.read_text());p=b.panel();errors=[];details={};n=_native.Substrate()
 if raw.get('lock_sha256')!=sha(LOCK) or raw.get('sources')!=lock.get('sources'):errors.append('capture binding')
 if m.source_map()!=lock.get('sources') or hashlib.sha256(canon(p)).hexdigest()!=lock.get('panel_sha256') or sha(m.BUDGET_RAW)!=lock.get('upstream_capture_sha256'):errors.append('source/panel drift')
 if not json.loads(m.BUDGET_ANALYSIS.read_text()).get('passed'):errors.append('upstream analysis')
 base,extra=b.all_joint(p);clauses,branch_count,checks=replay_clause_rows(p,base)
 if len(extra)!=256 or len(extra)!=lock['joint_product_size'] or raw.get('joint_product_size')!=len(extra):errors.append('exhaustive product')
 if raw.get('panel')!=p or raw.get('pairwise_base_count')!=len(base):errors.append('locked input binding')
 if raw.get('clause_rows')!=clauses or raw.get('clause_generation',{}).get('branch_count')!=branch_count or raw.get('clause_generation',{}).get('constraint_checks')!=checks:errors.append('clause extraction/solver replay')
 arms={a.get('policy'):a for a in raw.get('arms',[])}
 if set(arms)!={'exhaustive','budgeted_64','clause_aware'}:errors.append('arm identity')
 for name,probes,incomplete in [('exhaustive',base+extra,False),('budgeted_64',base+extra[:64],True),('clause_aware',base+clauses,False)]:
  a=arms.get(name,{})
  if a.get('probe_rows')!=probes or a.get('incomplete')!=incomplete:errors.append(f'{name}: proposal slate')
  denied={fpkey(x['row']) for x in p['training']}|{fpkey(x) for x in p['prior_pool']}|{fpkey(x) for x in p['holdout']}
  if any(fpkey(x) in denied for x in probes) or len({fpkey(x) for x in probes})!=len(probes):errors.append(f'{name}: proposal overlap')
  calls=0
  def ev(term,env):
   nonlocal calls
   calls+=1;return classify(n.evaluate(term,env))
  survivors=p['terms'][:];prior=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in p['prior_pool']]);events=[];used=set()
  while len(survivors)>1 and len(events)<8:
   available=[dict(zip(KEYS,r)) for r in probes if fpkey(r) not in used];choice=select_discriminating_input(ev,survivors,available,[])
   if not choice.get('ok'):break
   q=choice['query'];row=[float(q[k]) for k in KEYS];label=bool(h.truth(p['task'],row));before=[z['id'] for z in survivors];survivors=[z for z in survivors if ev(z['term'],q) is label];used.add(fpkey(row));events.append({'row':row,'label':label,'before':before,'after':[z['id'] for z in survivors],'entropy_bits':choice['entropy_bits'],'predictions':choice['predictions']})
  part=partition_hypotheses_by_behavior(ev,survivors,[dict(zip(KEYS,r)) for r in probes]);under='accept_behavior_class' if survivors and part['all_agree_on_probes'] else 'request_help';final='request_help' if incomplete and under=='accept_behavior_class' else under
  if a.get('events')!=events or a.get('survivor_ids')!=[z['id'] for z in survivors] or a.get('underlying_decision')!=under or a.get('decision')!=final:errors.append(f'{name}: selector replay')
  scores=[]
  for z in p['terms']:
   bad=inv=0
   for row in p['holdout']:
    pred=classify(n.evaluate(z['term'],dict(zip(KEYS,row))));y=bool(h.truth(p['task'],row))
    if pred is None:inv+=1
    elif pred is not y:bad+=1
   scores.append({'id':z['id'],'n':len(p['holdout']),'mismatches':bad,'invalid':inv})
  if a.get('holdout_scores')!=scores or a.get('native_evaluations')!=calls:errors.append(f'{name}: holdout/cost replay')
  bad=under=='accept_behavior_class' and p['terms'][1]['id'] in [z['id'] for z in survivors] and any(s['mismatches'] or s['invalid'] for s in scores if s['id']==p['terms'][1]['id'])
  details[name]={'proposals':len(probes),'labels':len(events),'decision':final,'false_acceptance':bool(bad and final=='accept_behavior_class'),'native_evaluations':calls,'wall_ns':a.get('wall_ns')}
 cg=raw.get('clause_generation',{});checks_out={'source_and_upstream_binding':not any('binding' in e or 'drift' in e or 'upstream' in e for e in errors),'256_row_exhaustive_product':len(extra)==256 and not any('product' in e for e in errors),'clause_extraction_replay':not any('clause' in e for e in errors),'all_policy_replay':not any('replay' in e or 'overlap' in e or 'slate' in e for e in errors),'exhaustive_resolves':details.get('exhaustive',{}).get('labels')==1 and not details.get('exhaustive',{}).get('false_acceptance'),'budgeted_abstains':details.get('budgeted_64',{}).get('decision')=='request_help','clause_aware_resolves_with_small_slate':details.get('clause_aware',{}).get('labels')==1 and not details.get('clause_aware',{}).get('false_acceptance') and len(clauses)<=2,'clause_generation_cost_accounted':cg.get('constraint_checks')==checks and cg.get('wall_ns',0)>0 and cg.get('cpu_ns',0)>0}
 result={'schema':'ClauseAwareLiteralProposalsV1Analysis','passed':all(checks_out.values()) and not errors,'checks':checks_out,'errors':errors,'cartesian_rows':len(extra),'clause_rows':clauses,'clause_generation':cg,'cells':details,'claim_boundary':'One source-locked noise-padded four-variable Term shows that a host-side direct-comparison clause solver can locate a separator on this authored shape without full product enumeration. This does not establish general clause coverage or substrate-owned proposal learning.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
