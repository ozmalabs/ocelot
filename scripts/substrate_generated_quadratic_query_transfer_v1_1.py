#!/usr/bin/env python3
"""Source-locked synthesis-to-native-query-selector integration gate."""
from __future__ import annotations
import hashlib, itertools, json, os, platform, random, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('OZMA_NO_LLM','1'); os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
from domains.generator import synthesize
from domains.contract_query import select_discriminating_input
import substrate_rs as srs
RUNNER=Path(__file__).resolve()
STEM='generated_quadratic_query_transfer_v1_1_20261005'
PROTOCOL=ROOT/'docs/research/engine_substrate/GENERATED_QUADRATIC_QUERY_TRANSFER_V1_1_AMENDMENT_20261005.md'
ANALYZER=ROOT/'scripts/analyze_generated_quadratic_query_transfer_v1_1.py'
LOCK=ROOT/f'evaluation/substrate_capability/{STEM}_lock.json'
RAW=ROOT/f'evaluation/reports/{STEM}_raw.json'
OUT=ROOT/f'evaluation/reports/{STEM}_analysis.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json')
TRAIN=[{'r':r,'c':c} for r,c in [(0,0),(1,0),(0,1),(1,1),(0,2),(1,2)]]
GRID=[{'r':r,'c':c} for r,c in itertools.product((-2,-1,0,1,2,3),(-2,-1,0,1,2,3))]
HELDOUT=[{'r':r,'c':c} for r,c in [(2,4),(3,-1),(-1,2),(4,3),(5,-2),(-3,4)]]
TASKS={'first_output':lambda e:e['r']+e['r']*e['c'],'second_output':lambda e:e['c']+e['r']*e['r']}
OPS=('Plus','Times'); CONSTANTS=(); MAX_SIZE=5; TIMEOUT_S=15.; MAX_SOLUTIONS=1000; REPS=20; SEED=20261005

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 native=Path(srs._native.__file__).resolve()
 return {'source_sha256':{p:sha(ROOT/p) for p in SOURCES},'native_path':str(native),'native_sha256':sha(native),'native_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'engine_provenance':engine_provenance(),'rust_source_fingerprint':rust_source_fingerprint(str(ROOT))}
def design(): return {'tasks':list(TASKS),'train':TRAIN,'candidate_grid':GRID,'heldout':HELDOUT,'ops':list(OPS),'constants':list(CONSTANTS),'max_size':MAX_SIZE,'timeout_s':TIMEOUT_S,'max_solutions':MAX_SOLUTIONS,'repetitions':REPS,'seed':SEED,'policies':['entropy','fixed_first','seeded_random'],'heldout_hidden_until_scoring':True}
def payload(): return {'schema':'GeneratedQuadraticQueryTransferV1Lock','files':{'runner':sha(RUNNER),'analyzer':sha(ANALYZER),'protocol':sha(PROTOCOL)},'engine':fingerprint(),'design':design()}
def train_rows(fn): return [{'inputs':e,'expected':fn(e)} for e in TRAIN]
def make_pool(sub,fn):
 t=time.perf_counter_ns(); c=time.process_time_ns()
 result=synthesize(sub,[(e,fn(e)) for e in TRAIN],ops=OPS,consts=CONSTANTS,max_size=MAX_SIZE,timeout_s=TIMEOUT_S,saturate_k=5,probe_envs=GRID,max_solutions=MAX_SOLUTIONS,include_output_constants=False)
 return result,{'wall_ns':time.perf_counter_ns()-t,'cpu_ns':time.process_time_ns()-c}
def exact_transfer(native,term,fn): return all(native.evaluate(term,e)==fn(e) for e in HELDOUT)
def run_policy(native,terms,task,rep,policy):
 fn=TASKS[task]; observations=train_rows(fn); order=list(GRID); rng=random.Random(SEED+rep*1009+list(TASKS).index(task)*100003); rng.shuffle(order)
 random_order=list(order); random.Random(SEED+rep*2027+list(TASKS).index(task)*200003).shuffle(random_order)
 alive=list(range(len(terms))); history=[]; eval_count=0; selector_ns=0; start=time.perf_counter_ns()
 def counted(term, env):
  nonlocal eval_count
  eval_count+=1
  return native.evaluate(term,env)
 while len(alive)>1 and len(history)<len(order):
  if policy=='entropy':
   rows=[{'id':str(i),'term':terms[i]} for i in alive]
   ts=time.perf_counter_ns(); choice=select_discriminating_input(counted,rows,order,observations); selector_ns+=time.perf_counter_ns()-ts
   if not choice.get('ok'): break
   query=choice['query']; predictions={int(x['hypothesis']):x.get('output') for x in choice['predictions']}
  elif policy=='fixed_first':
   query=next(e for e in order if e not in [o['inputs'] for o in observations]); predictions={i:counted(terms[i],query) for i in alive}
  else:
   query=next(e for e in random_order if e not in [o['inputs'] for o in observations]); predictions={i:counted(terms[i],query) for i in alive}
  label=fn(query); history.append({'query':query,'predictions':{str(i):predictions[i] for i in alive},'oracle_label':label,'survivors_before':alive[:]})
  alive=[i for i in alive if predictions[i]==label]; observations.append({'inputs':query,'expected':label})
 end=time.perf_counter_ns()-start
 return {'policy':policy,'rep':rep,'query_order':order,'random_order':random_order,'history':history,'survivors':alive,'oracle_calls':len(history),'prediction_evaluations':eval_count,'selector_wall_ns':selector_ns,'decision_wall_ns':end,'unique_survivor_is_heldout_exact':len(alive)==1 and exact_transfer(native,terms[alive[0]],fn),'pool_contains_heldout_exact':any(exact_transfer(native,t,fn) for t in terms)}
def capture():
 sub=srs.Substrate(); native=sub._inner; tasks={}
 for task,fn in TASKS.items():
  result,timing=make_pool(sub,fn); hypotheses=result.get('hypotheses',[]); terms=[h['term'].to_dict() for h in hypotheses]
  tasks[task]={'generation':{'wall_ns':timing['wall_ns'],'cpu_ns':timing['cpu_ns'],'explored':result.get('explored'),'distinct':result.get('distinct'),'halt_reason':result.get('halt_reason'),'pool_size':len(terms),'term_strings':[h.get('term_str') for h in hypotheses]},'terms':terms,'runs':[run_policy(native,terms,task,rep,policy) for rep in range(1,REPS+1) for policy in ('entropy','fixed_first','seeded_random')]}
 return {'schema':'GeneratedQuadraticQueryTransferV1Capture','lock':json.loads(LOCK.read_text()),'tasks':tasks,'post_engine':fingerprint(),'environment':{'python':sys.version,'platform':platform.platform()}}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or RAW.exists(): raise SystemExit('refusing to overwrite artifacts')
  LOCK.write_text(json.dumps(payload(),indent=2,sort_keys=True)+'\n'); print(LOCK.relative_to(ROOT)); return
 if not LOCK.exists() or json.loads(LOCK.read_text())!=payload(): raise SystemExit('missing/stale source lock')
 if RAW.exists(): raise SystemExit('refusing to overwrite capture')
 RAW.write_text(json.dumps(capture(),indent=2,sort_keys=True)+'\n'); print(RAW.relative_to(ROOT))
if __name__=='__main__': main()
