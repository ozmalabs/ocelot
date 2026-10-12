#!/usr/bin/env python3
"""Source-locked challenge-query audit for in- and out-of-grammar relations."""
import hashlib,itertools,json,os,platform,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve()
PRE=ROOT/'docs/research/engine_substrate/NUMERIC_RELATION_MODEL_ADEQUACY_AUDIT_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_numeric_relation_model_adequacy_audit_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/numeric_relation_model_adequacy_audit_v1_20261003.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py',
 'runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs',
 'runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs',
 'runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py',
 'evaluation/substrate_capability/numeric_opposition_model_misspecification_v1_1.py',
 'evaluation/substrate_capability/analyze_numeric_opposition_model_misspecification_v1_1.py',
 'evaluation/substrate_capability/numeric_opposition_model_misspecification_v1_1_lock_20261003.json')
TASKS=('additive','product','opposition');WORKERS=5
OPS=('Neg','Eq','And');MAX_SIZE=9;TIMEOUT=12.;MAX_SOLUTIONS=128;ENTROPY_BUDGET=6;AUDIT_BUDGET=6
TRAIN_VALUES=(-3.,-2.,-1.,1.,2.,3.);HELDOUT_VALUES=(-2.5,-1.5,-.5,.5,1.5,2.5)
KEYS=('ax','ay','ex','ey')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(row):return dict(zip(KEYS,map(float,row)))
def truth(task,row):
 if task=='additive':return row[0]+row[1]==row[2]+row[3]
 if task=='product':return row[0]*row[1]==row[2]*row[3]
 return row[0]==-row[2] and row[1]==-row[3]
def panels():
 rows=list(itertools.product(TRAIN_VALUES,repeat=4));out=[]
 for ti,task in enumerate(TASKS):
  positives=[r for r in rows if truth(task,r)];negatives=[r for r in rows if not truth(task,r)]
  for worker in range(WORKERS):
   seed=20261110+ti*100+worker;rng=random.Random(seed)
   train=rng.sample(positives,2)+rng.sample(negatives,2)
   remaining=[r for r in rows if r not in train];rng.shuffle(remaining)
   selected=remaining[:32];challenge=remaining[32:64]
   active_order=list(selected);random.Random(seed+10000).shuffle(active_order)
   audit_order=list(challenge);random.Random(seed+20000).shuffle(audit_order)
   out.append({'task':task,'worker':worker,'seed':seed,
    'training':[{'row':list(r),'label':int(truth(task,r))} for r in train],
    'selection_pool':[list(r) for r in selected],'selection_order':[list(r) for r in active_order],
    'challenge_pool':[list(r) for r in challenge],'challenge_order':[list(r) for r in audit_order]})
 return out
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},
  'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},
  'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def score(native,task,term):
 tp=fp=fn=tn=invalid=0
 for row in itertools.product(HELDOUT_VALUES,repeat=4):
  try:pred=native.evaluate(term,env(row))
  except Exception:invalid+=1;continue
  actual=truth(task,row)
  if type(pred) is not bool:invalid+=1;continue
  if pred and actual:tp+=1
  elif pred:fp+=1
  elif actual:fn+=1
  else:tn+=1
 return {'n':1296,'exact':not invalid and not fp and not fn,'invalid':invalid,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
def retain(native,task,survivors,query,label):
 kept=[]
 for h in survivors:
  try:value=native.evaluate(h['term'],query)
  except Exception:continue
  if type(value) is bool and value is bool(label):kept.append(h)
 return kept
def run_policy(native,task,panel,hypotheses,policy):
 from domains.contract_query import select_discriminating_input
 active_order=panel['selection_order'];audit_order=panel['challenge_order']
 survivors=list(hypotheses);steps=[];used_active=[];used_audit=[];selector_ns=0
 entropy_start=time.perf_counter_ns()
 for _ in range(ENTROPY_BUDGET):
  if len(survivors)<2:break
  available=[env(r) for r in active_order if r not in used_active]
  if not available:break
  observations=[{'inputs':s['input_env'],'expected':s['label']} for s in steps]
  start=time.perf_counter_ns()
  selected=select_discriminating_input(lambda term,e:native.evaluate(term,e),survivors,available,observations)
  selector_ns+=time.perf_counter_ns()-start
  if not selected.get('ok'):break
  query=selected['query'];row=[float(query[k]) for k in KEYS];label=bool(truth(task,row))
  used_active.append(row);before=len(survivors);survivors=retain(native,task,survivors,query,label)
  steps.append({'phase':'entropy','row':row,'input_env':query,'label':label,'before':before,'after':len(survivors),
   'predictions':selected['predictions'],'entropy_bits':selected['entropy_bits']})
  if not survivors:break
 stop_reason='empty' if not survivors else ('singleton' if len(survivors)==1 else 'entropy_budget_or_abstention')
 entropy_ns=time.perf_counter_ns()-entropy_start;challenge_ns=0
 if policy=='challenge_until_six':
  challenge_start=time.perf_counter_ns()
  for row in audit_order:
   if not survivors:break
   if len(steps)>=AUDIT_BUDGET:break
   query=env(row);before=len(survivors);label=bool(truth(task,row))
   predictions=[]
   for h in survivors:
    try:predictions.append({'hypothesis':h['id'],'output':native.evaluate(h['term'],query)})
    except Exception:predictions.append({'hypothesis':h['id'],'output':None,'evaluation_error':True})
   survivors=retain(native,task,survivors,query,label)
   used_audit.append(row)
   steps.append({'phase':'challenge','row':row,'input_env':query,'label':label,'before':before,'after':len(survivors),
    'predictions':predictions})
   if not survivors:break
  challenge_ns=time.perf_counter_ns()-challenge_start
  stop_reason='empty' if not survivors else ('singleton_after_challenge' if len(survivors)==1 else 'ambiguous_after_challenge')
 return {'policy':policy,'steps':steps,'entropy_selector_ns':selector_ns,
  'entropy_phase_ns':entropy_ns,'challenge_phase_ns':challenge_ns,
  'entropy_calls':sum(s['phase']=='entropy' for s in steps),'challenge_calls':sum(s['phase']=='challenge' for s in steps),
  'stop':stop_reason,'survivors':[{'id':h['id'],'term':h['term'],'heldout':score(native,task,h['term'])} for h in survivors]}
def worker(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 native=_native.Substrate();examples=[(env(x['row']),float(x['label'])) for x in panel['training']]
 probes=[env(r) for r in panel['selection_pool']]
 start=time.perf_counter_ns();cpu=time.process_time_ns()
 version=synthesize(native,examples,ops=OPS,consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,
  include_output_constants=False,probe_envs=probes,max_solutions=MAX_SOLUTIONS,saturate_k=999999)
 synth_ns=time.perf_counter_ns()-start;cpu_ns=time.process_time_ns()-cpu
 hypotheses=[] if not version else [{'id':f'h{i:03d}','term':h['term'].to_dict()} for i,h in enumerate(version.get('hypotheses',[]))]
 exact_initial=[h['id'] for h in hypotheses if score(native,panel['task'],h['term'])['exact']]
 arms=[run_policy(native,panel['task'],panel,hypotheses,p) for p in ('entropy_stop','challenge_until_six')]
 return {'task':panel['task'],'worker':panel['worker'],'training':panel['training'],
  'selection_pool':panel['selection_pool'],'selection_order':panel['selection_order'],
  'challenge_pool':panel['challenge_pool'],'challenge_order':panel['challenge_order'],
  'hypotheses':[{'id':h['id'],'term':h['term'],'heldout':score(native,panel['task'],h['term'])} for h in hypotheses],
  'exact_initial_ids':exact_initial,'version_halt_reason':None if not version else version.get('halt_reason'),
  'version_explored':0 if not version else version.get('explored',0),'synthesis_ns':synth_ns,'synthesis_cpu_ns':cpu_ns,
  'arms':arms}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'NumericRelationModelAdequacyAuditV1Lock','sources':source_map(),
   'panels':panels(),'tasks':TASKS,'ops':OPS,'max_size':MAX_SIZE,'timeout_s':TIMEOUT,
   'max_solutions':MAX_SOLUTIONS,'entropy_budget':ENTROPY_BUDGET,'challenge_budget':AUDIT_BUDGET,
   'heldout_values':HELDOUT_VALUES,'heldout_count':1296},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources']:raise SystemExit('source drift')
  envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
  for i,panel in enumerate(lock['panels']):
   p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=90)
   if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2500:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'NumericRelationModelAdequacyAuditV1Results','lock_sha256':sha(LOCK),
   'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
   'host':platform.platform(),'workers':rows},indent=2,sort_keys=True)+'\n')
  print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':
  print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
