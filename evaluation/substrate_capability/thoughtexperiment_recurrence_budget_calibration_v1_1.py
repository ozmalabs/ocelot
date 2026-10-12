#!/usr/bin/env python3
"""Paired recurrence budget calibration on an independently generated graph."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_BUDGET_CALIBRATION_V1_1_PREREG_20261002.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_BUDGET_CALIBRATION_V1_AMENDMENT_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_budget_calibration_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_budget_calibration_v1_1_lock_20261002.json'
ORDERS=ROOT/'evaluation/reports/thoughtexperiment_recurrence_budget_calibration_v1_1_orders_20261002.json'
SCORES=ROOT/'evaluation/reports/thoughtexperiment_recurrence_budget_calibration_v1_1_scores_20261002.json'
TARGET='mrl_offer_due_once'; WORKERS=4; ARITIES=(2,4,8); SAMPLES=2
BUDGETS=(200,400,800); REFERENCE_BUDGET=1000; BATCH=100
ACTIVE=('domains/contract_query.py','domains/self_correction.py','domains/engine_provenance.py',
 'substrate/boot_core.py','substrate/seed_loader.py','runners/dsl/src/py.rs','runners/dsl/src/substrate.rs',
 'runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/term.rs',
 'runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py',
 'seeds/minting_recurrence_ledger.json','seeds/relation_vocabulary.json','seeds/composer_dispatch.json','seeds/autonomy.json')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=[ROOT/p for p in ACTIVE]+[RUNNER,PROTOCOL,AMENDMENT,ANALYZER]
 out={str(p.relative_to(ROOT)):sha(p) for p in paths}
 out['loaded_native_binary']=sha(Path(_native.__file__).resolve())
 return out
def candidate_digest(c):
 bundle={}
 for target,rule in sorted((c.get('rules') or {}).items()):
  r=json.loads(json.dumps(rule,sort_keys=True)) if rule is not None else None
  if isinstance(r,dict): r.pop('name',None)
  bundle[target]=r
 return 'sha256:'+hashlib.sha256(json.dumps(bundle,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def generate_graph(worker,arity,split,sample):
 """Construct a fresh graph directly from a keyed episode specification."""
 from substrate.boot_core import boot_core
 from substrate.seed_loader import manifest_for
 from domains.self_correction import _default_candidates
 sub,agent=boot_core(seeds=()); native=sub._inner
 for seed in ('relation_vocabulary','composer_dispatch','autonomy','minting_recurrence_ledger'):
  native.load_seed_manifest(manifest_for(seed),agent)
 rows=native.export_rules()
 active=[(i,r) for i,r in enumerate(rows) if r.get('name')==TARGET and r.get('active',True)]
 if not active: raise RuntimeError('active target rule missing')
 faulty=json.loads(json.dumps(active[0][1]))
 faulty['where']['items']=[x for x in faulty['where']['items'] if x.get('type')!='Not']
 if not all(native.remove_rule(i) for i,_ in reversed(active)): raise RuntimeError('could not isolate faulty rule')
 native.add_rule(faulty)
 episode=sub.add_node('MintingRecurrenceEpisode',{'mint_after_quanta':1,'integer_native':1,
  'generator':'budget_calibration_v1','arity':arity})
 sub.add_edge(agent,'has_minting_recurrence_episode',episode)
 keys=[f'cal-w{worker}-a{arity}-{split}-s{sample}-k{i}' for i in range(arity)]
 def attrs_for(ordinal):
  key=keys[ordinal]
  return {'predicate':'bind','recurrence_key':key,
   'structural_signature':[['relation','bind','ITEM',f'CAL_SLOT_{ordinal}',worker]],
   'capability_key':['budget-calibration',str(arity),key]}
 def add_candidate(ordinal):
  attrs=attrs_for(ordinal)
  cand=sub.add_node('PredicateRecurrenceCandidate',attrs)
  ev=sub.add_node('ResidualSegmentEvidence',{**attrs,'segment_ordinal':ordinal,'integer_native':1})
  sub.add_edge(episode,'has_predicate_recurrence_candidate',cand)
  sub.add_edge(cand,'supported_by_segment',ev)
  return cand
 add_candidate(0)
 proposals=_default_candidates(native,TARGET)
 proposals=[c for c in proposals if (c.get('rules') or {}).get(TARGET) is not None]
 if len(proposals)!=8: raise RuntimeError(f'expected 8 proposals, got {len(proposals)}')
 spec={'worker':worker,'arity':arity,'split':split,'sample':sample,'recurrence_keys':keys,
  'candidate_attrs':[attrs_for(i) for i in range(arity)],
  'input_digest':hashlib.sha256(json.dumps({'worker':worker,'arity':arity,'split':split,'sample':sample,
   'keys':keys,'candidate_attrs':[attrs_for(i) for i in range(arity)]},sort_keys=True,separators=(',',':')).encode()).hexdigest()}
 return sub,native,episode,keys,proposals,spec

def install(native,candidate):
 ids=[(i,r) for i,r in enumerate(native.export_rules()) if r.get('name')==TARGET and r.get('active',True)]
 if not ids or not all(native.remove_rule(i) for i,_ in reversed(ids)): raise RuntimeError('target rule replacement failed')
 native.add_rule(candidate['rules'][TARGET])
def offers(sub,keys):
 out=[]
 for key in keys:
  node=next((n for n in sub.nodes('PredicateRecurrenceCandidate') if sub.node(n)['attrs'].get('recurrence_key')==key),None)
  out.append(len(list(sub.neighbours(node,'has_mint_offer'))) if node is not None else 0)
 return out
def close_stage(native,budget):
 work=0; batches=[]
 while work<budget:
  limit=min(BATCH,budget-work); n=int(native.run_rules(limit)); batches.append(n); work+=n
  if n<limit:
   return {'fixedpoint':True,'work':work,'batches':batches,'budget_exhausted':False}
 return {'fixedpoint':False,'work':work,'batches':batches,'budget_exhausted':True}
def evaluate(worker,arity,split,sample,candidate,budget):
 start=time.perf_counter_ns(); sub,native,episode,keys,_,spec=generate_graph(worker,arity,split,sample)
 install(native,candidate); primary_before=native.export_rules(); stages=[]
 for ordinal,key in enumerate(keys):
  if ordinal:
   attrs=spec['candidate_attrs'][ordinal]
   cand=sub.add_node('PredicateRecurrenceCandidate',attrs)
   ev=sub.add_node('ResidualSegmentEvidence',{**attrs,'segment_ordinal':ordinal,'integer_native':1})
   sub.add_edge(episode,'has_predicate_recurrence_candidate',cand)
   sub.add_edge(cand,'supported_by_segment',ev)
  stage=close_stage(native,budget);stages.append(stage)
  if not stage['fixedpoint']: break
 counts=offers(sub,keys); complete=len(stages)==arity and all(x['fixedpoint'] for x in stages)
 correct=complete and counts==[1]*arity
 return {'worker':worker,'arity':arity,'split':split,'sample':sample,'candidate_id':candidate_digest(candidate),
  'input_digest':spec['input_digest'],'oracle_correct':correct,'fixedpoint':complete,'offer_counts':counts,
  'stage_results':stages,'work_units':sum(x['work'] for x in stages),
  'budget_rejected_stage':next((i for i,x in enumerate(stages) if x['budget_exhausted']),None),
  'primary_rules_unchanged':native.export_rules()==primary_before,'runtime_ns':time.perf_counter_ns()-start}

def proposals_for(worker,arity):
 _s,_n,_e,_k,cs,_spec=generate_graph(worker,arity,'inventory',0)
 ds=[{'candidate_id':candidate_digest(c),'proposal_label':f'candidate_{i}'} for i,c in enumerate(cs)]
 if len({d['candidate_id'] for d in ds})!=8: raise RuntimeError('candidate identity collision')
 return cs,ds
def training_worker(worker):
 from domains.contract_query import select_candidate_from_graph_evidence
 source_before=frozen(); result={}
 for arity in ARITIES:
  cs,ds=proposals_for(worker,arity); train={}
  for arm,budget in [('reference',REFERENCE_BUDGET)]+[(f'budget_{b}',b) for b in BUDGETS]:
   by={d['candidate_id']:[] for d in ds}; evidence=[]; inputs=[]
   for c,d in zip(cs,ds):
    for sample in range(SAMPLES):
     row=evaluate(worker,arity,'train',sample,c,budget);by[d['candidate_id']].append(row)
     inputs.append(row['input_digest'])
     evidence.append({'proposal_id':d['candidate_id'],'probe_id':f'w{worker}_a{arity}_s{sample}',
      'predicted':'correct' if row['oracle_correct'] else 'incorrect','expected':'correct'})
   snap=generate_graph(worker,arity,'selection',0)[0].snapshot();branch=snap.fork()
   rank_descriptors=[{'proposal_id':d['candidate_id'],'proposal_label':d['proposal_label']} for d in ds]
   before=len(branch.nodes('CandidateProposal'))+len(branch.nodes('CandidateEvidence'))
   t=time.perf_counter_ns();decision=select_candidate_from_graph_evidence(branch,
    f'budget_cal_w{worker}_a{arity}_{arm}',rank_descriptors,evidence);decision_ns=time.perf_counter_ns()-t
   decision.pop('proposal_node',None)
   if len(branch.nodes('CandidateProposal'))+len(branch.nodes('CandidateEvidence'))<before: raise RuntimeError('branch evidence state invalid')
   train[arm]={'outcomes':by,'decision':decision,'decision_ns':decision_ns,'input_digests':inputs}
  controls={}
  snap=generate_graph(worker,arity,'control',0)[0].snapshot()
  for control,predicted in [('all_wrong','incorrect'),('tie','correct')]:
   branch=snap.fork(); ev=[{'proposal_id':d['candidate_id'],'probe_id':f'{control}_{j}',
     'predicted':predicted,'expected':'correct'} for d in ds for j in range(2)]
   decision=select_candidate_from_graph_evidence(branch,f'budget_cal_{control}_w{worker}_a{arity}',rank_descriptors,ev)
   decision.pop('proposal_node',None);controls[control]=decision
  result[str(arity)]={'descriptors':ds,'arms':train,'controls':controls}
 source_after=frozen()
 return {'worker':worker,'training':result,'source_before':source_before,'source_after':source_after,
  'source_stable':source_before==source_after}
def heldout_worker(order):
 worker=order['worker']; source_before=frozen(); result={}
 for arity in ARITIES:
  cs,ds=proposals_for(worker,arity)
  if ds!=order['training'][str(arity)]['descriptors']: raise RuntimeError('proposal set drift')
  arms={}
  for arm,budget in [('reference',REFERENCE_BUDGET)]+[(f'budget_{b}',b) for b in BUDGETS]:
   rows={d['candidate_id']:[] for d in ds}
   for c,d in zip(cs,ds):
    for sample in range(SAMPLES): rows[d['candidate_id']].append(evaluate(worker,arity,'heldout',sample,c,budget))
   arms[arm]=rows
  result[str(arity)]={'arms':arms}
 source_after=frozen()
 return {'worker':worker,'heldout':result,'source_before':source_before,'source_after':source_after,
  'source_stable':source_before==source_after}
def main():
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale: raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'}
 if sys.argv[1:]==['--lock']:
  if any(p.exists() for p in (LOCK,ORDERS,SCORES)): raise SystemExit('refusing to overwrite study artifacts')
  LOCK.write_text(json.dumps({'schema':'RecurrenceBudgetCalibrationV1_1Lock','sources':frozen(),
   'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'workers':WORKERS,'arities':ARITIES,
   'samples_per_split':SAMPLES,'budgets':BUDGETS,'reference_budget':REFERENCE_BUDGET,'batch':BATCH},indent=2,sort_keys=True)+'\n')
  print(LOCK);return
 if not LOCK.exists() or frozen()!=json.loads(LOCK.read_text())['sources']: raise SystemExit('missing lock or source drift')
 if sys.argv[1:]==['--orders']:
  if ORDERS.exists() or SCORES.exists(): raise SystemExit('capture exists')
  workers=[]
  for i in range(WORKERS):
   p=subprocess.run([sys.executable,str(RUNNER),'--orders-worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode: raise RuntimeError(p.stderr[-3000:])
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  ORDERS.write_text(json.dumps({'schema':'RecurrenceBudgetCalibrationV1_1Orders','lock_sha256':sha(LOCK),
   'workers':workers,'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
   'host':{'platform':platform.platform(),'python':sys.version.split()[0]}},indent=2,sort_keys=True)+'\n')
  print(ORDERS);return
 if sys.argv[1:]==['--score']:
  if not ORDERS.exists() or SCORES.exists(): raise SystemExit('orders missing or scores already exist')
  orders=json.loads(ORDERS.read_text())
  if orders['lock_sha256']!=sha(LOCK): raise SystemExit('orders lock mismatch')
  workers=[]
  for order in orders['workers']:
   p=subprocess.run([sys.executable,str(RUNNER),'--score-worker'],input=json.dumps(order),cwd=ROOT,env=env,text=True,capture_output=True)
   if p.returncode: raise RuntimeError(p.stderr[-3000:])
   workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
  SCORES.write_text(json.dumps({'schema':'RecurrenceBudgetCalibrationV1_1Scores','orders_sha256':sha(ORDERS),'workers':workers},indent=2,sort_keys=True)+'\n')
  print(SCORES);return
 if sys.argv[1:2]==['--orders-worker']:
  i=int(sys.argv[2]);print(json.dumps(training_worker(i),sort_keys=True,separators=(',',':')));return
 if sys.argv[1:2]==['--score-worker']:
  print(json.dumps(heldout_worker(json.load(sys.stdin)),sort_keys=True,separators=(',',':')));return
 raise SystemExit('use --lock, --orders, or --score')
if __name__=='__main__': main()
