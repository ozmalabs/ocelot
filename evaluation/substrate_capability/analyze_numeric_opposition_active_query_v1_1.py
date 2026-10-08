#!/usr/bin/env python3
"""Independent paired-order replay for synthesized-hypothesis active queries."""
import hashlib,itertools,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
LOCK=ROOT/'evaluation/substrate_capability/numeric_opposition_active_query_v1_1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/numeric_opposition_active_query_v1_1_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_opposition_active_query_v1_1_analysis_20261003.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(('ax','ay','ex','ey'),map(float,r)))
def truth(r):return r[0]==-r[2] and r[1]==-r[3]
def obs_eq(a,b):return type(a) is type(b) and a==b
def token(v):return(type(v).__module__,type(v).__qualname__,repr(v))
def target_ast():return {'type':'And','items':[{'type':'Eq','a':{'type':'Var','name':'ax'},'b':{'type':'Neg','arg':{'type':'Var','name':'ex'}}},{'type':'Eq','a':{'type':'Var','name':'ay'},'b':{'type':'Neg','arg':{'type':'Var','name':'ey'}}}]}
def main():
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input
 from domains.generator import synthesize
 from evaluation.substrate_capability.measure_numeric_opposition_active_query_v1_1 import source_map
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());errors=[];native=_native.Substrate();vals=(-2.5,-1.5,-.5,.5,1.5,2.5);grid=list(itertools.product(vals,repeat=4))
 if source_map()!=lock['sources']:errors.append('current source/build map differs from lock')
 if cap.get('lock_sha256')!=sha(LOCK) or cap.get('sources')!=lock['sources']:errors.append('capture provenance mismatch')
 if len(cap.get('workers',[]))!=5:errors.append('worker count mismatch')
 action={'Up':(-1.,0.),'Down':(1.,0.),'Left':(0.,-1.),'Right':(0.,1.),'Stay':(0.,0.)}
 taskids=[x['id'] for x in lock['panels'][0]['orders'][:0]]
 # The locked navigation panel comes from v1's source-locked harness.
 from evaluation.substrate_capability.measure_numeric_opposition_active_query_v1 import NAV_TASKS
 summaries=[];all_pairs=[]
 for wr in cap.get('workers',[]):
  i=wr['worker'];panel=lock['panels'][i];hyps=wr.get('hypotheses',[])
  if wr.get('training')!=panel['training'] or wr.get('query_pool')!=panel['query_pool']:errors.append(f'worker {i}: locked examples/pool mismatch')
  if wr.get('version_halt_reason')!='max_size':errors.append(f'worker {i}: version space incomplete')
  if not any(h['term']==target_ast() for h in hyps):errors.append(f'worker {i}: exact target absent')
  cfg=lock['synth_config'];examples=[(env(x['row']),float(x['label'])) for x in panel['training']]
  replay=synthesize(native,examples,ops=cfg['ops'],consts=cfg['constants'],max_size=cfg['max_size'],timeout_s=cfg['timeout_s'],
   include_output_constants=cfg['include_output_constants'],probe_envs=[env(r) for r in panel['query_pool']],max_solutions=cfg['max_solutions'],saturate_k=999999)
  replay_terms=[] if not replay else [{'id':f'h{k:03d}','term':h['term'].to_dict()} for k,h in enumerate(replay['hypotheses'])]
  if not replay or replay.get('halt_reason')!='max_size' or replay_terms!=hyps:errors.append(f'worker {i}: independent version-space synthesis mismatch/incomplete')
  if len(wr.get('blocks',[]))!=lock['orders_per_worker']:errors.append(f'worker {i}: order block count mismatch')
  block_rows=[]
  for block,spec in zip(wr.get('blocks',[]),panel['orders']):
   if block.get('order_id')!=spec['order_id'] or block.get('seed')!=spec['seed'] or block.get('order')!=spec['rows'] or sorted(map(tuple,block.get('order',[])))!=sorted(map(tuple,panel['query_pool'])):errors.append(f'worker {i}/order {spec["order_id"]}: order lock mismatch')
   if len(block.get('arms',[]))!=2:errors.append(f'worker {i}/order {spec["order_id"]}: arm count mismatch')
   armcalls={}
   for arm in block.get('arms',[]):
    policy=arm['policy'];surv=list(hyps);obs=[];used=[];order=spec['rows']
    for step in arm.get('steps',[]):
     if len(surv)<2:errors.append(f'worker {i}/{spec["order_id"]}/{policy}: queried after singleton');break
     candidates=[env(r) for r in order if r not in used]
     if policy=='max_entropy':
      choice=select_discriminating_input(lambda t,e:native.evaluate(t,e),surv,candidates,obs)
      if not choice.get('ok') or choice.get('query')!=env(step['query']):errors.append(f'worker {i}/{spec["order_id"]}: entropy choice mismatch')
      expected_preds=choice.get('predictions',[])
     elif policy=='sequential_random_order':
      if not candidates or env(step['query'])!=candidates[0]:errors.append(f'worker {i}/{spec["order_id"]}: sequential order mismatch')
      q=env(step['query']);expected_preds=[{'hypothesis':h['id'],'output':native.evaluate(h['term'],q)} for h in surv]
     else:errors.append(f'worker {i}: unknown policy {policy}');continue
     if step.get('predictions')!=expected_preds:errors.append(f'worker {i}/{spec["order_id"]}/{policy}: prediction mismatch')
     qrow=step['query'];label=truth(qrow)
     if step.get('label')!=label:errors.append(f'worker {i}/{spec["order_id"]}/{policy}: oracle mismatch')
     if step.get('before')!=len(surv):errors.append(f'worker {i}/{spec["order_id"]}/{policy}: before count mismatch')
     used.append(qrow);obs.append({'inputs':env(qrow),'expected':label});surv=[h for h in surv if obs_eq(native.evaluate(h['term'],env(qrow)),label)]
     if step.get('after')!=len(surv):errors.append(f'worker {i}/{spec["order_id"]}/{policy}: after count mismatch')
    if arm.get('oracle_calls')!=len(used) or len(used)>lock['call_budget'] or len(set(map(tuple,used)))!=len(used):errors.append(f'worker {i}/{spec["order_id"]}/{policy}: count/uniqueness violation')
    if arm.get('survivor_ids')!=[h['id'] for h in surv]:errors.append(f'worker {i}/{spec["order_id"]}/{policy}: survivors mismatch')
    if len(surv)>1 and len(used)<lock['call_budget']:
     candidates=[env(r) for r in order if r not in used]
     if policy=='max_entropy':can=select_discriminating_input(lambda t,e:native.evaluate(t,e),surv,candidates,obs).get('ok',False)
     else:can=any(len({token(native.evaluate(h['term'],env(r))) for h in surv})>1 for r in order if r not in used)
     if can:errors.append(f'worker {i}/{spec["order_id"]}/{policy}: stopped early')
    score_rows=[]
    for h in surv:
     tp=fp=fn=tn=0
     for r in grid:
      y=truth(r);p=bool(native.evaluate(h['term'],env(r)))
      if y and p:tp+=1
      elif y:fn+=1
      elif p:fp+=1
      else:tn+=1
     nav=[]
     for task in NAV_TASKS:
      av=action.get(task['actual']);ev=action.get(task['expected']) if task['expected'] else None
      rel=None if av is None or ev is None else bool(native.evaluate(h['term'],{'ax':av[0],'ay':av[1],'ex':ev[0],'ey':ev[1]}))
      proposal=bool(rel and task['kind']!='absent_target');nav.append({'task_id':task['id'],'relation':rel,'proposal':proposal,'expected_proposal':task['kind']=='opposite'})
     score_rows.append({'hypothesis':h['id'],'heldout':{'n':len(grid),'tp':tp,'fp':fp,'fn':fn,'tn':tn,'exact':fp==0 and fn==0},'navigation':nav})
    if arm.get('heldout_scores')!=score_rows:errors.append(f'worker {i}/{spec["order_id"]}/{policy}: held-out score mismatch')
    exact=bool(surv) and all(x['heldout']['exact'] for x in score_rows)
    armcalls[policy]={'calls':len(used),'identified':len(surv)==1,'exact':exact,'selector_ns':arm.get('selector_ns',0),'wall_ns':arm.get('arm_wall_ns',0)}
   active=armcalls.get('max_entropy');seq=armcalls.get('sequential_random_order')
   if active and seq:
    pair={'order_id':spec['order_id'],'active_calls':active['calls'],'sequential_calls':seq['calls'],'difference':active['calls']-seq['calls'],'active_identified_exact':active['identified'] and active['exact'],'sequential_identified_exact':seq['identified'] and seq['exact'],'active_selector_ns':active['selector_ns'],'sequential_selector_ns':seq['selector_ns']}
    block_rows.append(pair);all_pairs.append(pair)
  worker_median={k:statistics.median(p[k] for p in block_rows) for k in ('active_calls','sequential_calls','difference')}
  summaries.append({'worker':i,'hypotheses':len(hyps),'target_present':any(h['term']==target_ast() for h in hyps),'order_blocks':len(block_rows),'median_paired':worker_median,
   'active_exact_identifications':sum(p['active_identified_exact'] for p in block_rows),'sequential_exact_identifications':sum(p['sequential_identified_exact'] for p in block_rows),
   'active_wins':sum(p['difference']<0 for p in block_rows),'ties':sum(p['difference']==0 for p in block_rows),'sequential_wins':sum(p['difference']>0 for p in block_rows)})
 paired_wins=sum(p['difference']<0 for p in all_pairs);paired_ties=sum(p['difference']==0 for p in all_pairs);seq_wins=sum(p['difference']>0 for p in all_pairs)
 result={'schema':'NumericOppositionActiveQueryV1_1Analysis','measurement_integrity_pass':not errors,'errors':errors,'workers':summaries,
  'summary':{'workers':len(summaries),'paired_order_blocks':len(all_pairs),'median_active_calls':statistics.median([p['active_calls'] for p in all_pairs]) if all_pairs else None,'median_sequential_calls':statistics.median([p['sequential_calls'] for p in all_pairs]) if all_pairs else None,
   'median_worker_paired_difference':statistics.median([w['median_paired']['difference'] for w in summaries]) if summaries else None,'paired_order_wins':{'active':paired_wins,'tie':paired_ties,'sequential':seq_wins},'caution':'Order blocks are repeated measurements nested within five training panels; summarize worker clusters rather than treating 150 blocks as independent tasks.'},
  'input_hashes':{'lock':sha(LOCK),'capture':sha(CAP),'analyzer':sha(Path(__file__))}}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
