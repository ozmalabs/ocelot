#!/usr/bin/env python3
"""Source-locked two-family operator selection using generated Term pools."""
import hashlib,itertools,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/PRIMITIVE_FAMILY_SELECTION_V1_PREREG_20261003.md';ANALYZER=ROOT/'evaluation/substrate_capability/analyze_primitive_family_selection_v1.py';LOCK=ROOT/'evaluation/substrate_capability/primitive_family_selection_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/primitive_family_selection_v1_20261003.json';PANEL_LOCK=ROOT/'evaluation/substrate_capability/numeric_relation_model_adequacy_audit_v1_1_lock_20261003.json'
SOURCES=('domains/generator.py','domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
TASKS=('additive','product');OPS={'Plus':('Neg','Eq','And','Plus'),'Times':('Neg','Eq','And','Times')};FAMILIES=('Plus','Times');KEYS=('ax','ay','ex','ey');VALUES=(-2.5,-1.5,-.5,.5,1.5,2.5);MAX_SIZE=7;TIMEOUT=12.;MAX_SOLUTIONS=128;BUDGET=6
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def env(r):return dict(zip(KEYS,map(float,r)))
def truth(t,r):return r[0]+r[1]==r[2]+r[3] if t=='additive' else r[0]*r[1]==r[2]*r[3]
def score(native,t,term):
 tp=fp=fn=tn=invalid=0
 for r in itertools.product(VALUES,repeat=4):
  try:v=native.evaluate(term,env(r))
  except Exception:invalid+=1;continue
  y=truth(t,r)
  if type(v) is not bool:invalid+=1
  elif v and y:tp+=1
  elif v:fp+=1
  elif y:fn+=1
  else:tn+=1
 return {'n':1296,'exact':not invalid and not fp and not fn,'invalid':invalid,'tp':tp,'fp':fp,'fn':fn,'tn':tn}
def panels():
 p=json.loads(PANEL_LOCK.read_text());return [x for x in p['panels'] if x['task'] in TASKS]
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER,PANEL_LOCK]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def synthesize_families(panel):
 from substrate_rs import _native
 from domains.generator import synthesize
 ex=[(env(x['row']),float(x['label'])) for x in panel['training']];probes=[env(r) for r in panel['selection_pool']];out=[]
 for fam in FAMILIES:
  n=_native.Substrate();wall=time.perf_counter_ns();cpu=time.process_time_ns();v=synthesize(n,ex,ops=OPS[fam],consts=(),max_size=MAX_SIZE,timeout_s=TIMEOUT,include_output_constants=False,probe_envs=probes,max_solutions=MAX_SOLUTIONS,saturate_k=999999);wall=time.perf_counter_ns()-wall;cpu=time.process_time_ns()-cpu
  hs=[] if not v else [{'id':fam+f'{i:03d}','family':fam,'term':h['term'].to_dict(),'heldout':score(n,panel['task'],h['term'].to_dict())} for i,h in enumerate(v.get('hypotheses',[]))]
  out.append({'family':fam,'ops':OPS[fam],'wall_ns':wall,'cpu_ns':cpu,'explored':0 if not v else v.get('explored',0),'halt_reason':None if not v else v.get('halt_reason'),'hypotheses':hs})
 return out
def policy(native,panel,hypotheses,kind):
 from domains.contract_query import select_discriminating_input
 survivors=list(hypotheses);used=[];observations=[];steps=[];selector_ns=0
 for _ in range(BUDGET):
  if len(survivors)<2:break
  available=[env(r) for r in panel['selection_order'] if r not in used]
  if not available:break
  if kind=='entropy':
   start=time.perf_counter_ns();choice=select_discriminating_input(lambda t,e:native.evaluate(t,e),survivors,available,observations);selector_ns+=time.perf_counter_ns()-start
   if not choice.get('ok'):break
   q=choice['query'];preds=choice.get('predictions',[]);entropy=choice.get('entropy_bits')
  else:q=available[0];preds=[];entropy=None
  row=[float(q[k]) for k in KEYS];label=bool(truth(panel['task'],row));used.append(row);before=len(survivors);kept=[]
  for h in survivors:
   try:v=native.evaluate(h['term'],q)
   except Exception:continue
   if type(v) is bool and v==label:kept.append(h)
  survivors=kept;observations.append({'inputs':q,'expected':label});steps.append({'row':row,'input_env':q,'label':label,'before':before,'after':len(survivors),'predictions':preds,'entropy_bits':entropy})
 return {'policy':kind,'steps':steps,'calls':len(steps),'selector_ns':selector_ns,'stop':'empty' if not survivors else ('singleton' if len(survivors)==1 else 'budget_or_abstention'),'survivors':[{'id':h['id'],'family':h['family'],'term':h['term'],'heldout':score(native,panel['task'],h['term'])} for h in survivors]}
def worker(panel):
 from substrate_rs import _native
 arms=synthesize_families(panel);hyps=[h for a in arms for h in a['hypotheses']];n=_native.Substrate();policies=[policy(n,panel,hyps,k) for k in ('fixed_order','entropy')]
 return {'task':panel['task'],'worker':panel['worker'],'training':panel['training'],'selection_pool':panel['selection_pool'],'selection_order':panel['selection_order'],'families':arms,'policies':policies}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'PrimitiveFamilySelectionV1Lock','sources':source_map(),'panels':panels(),'tasks':TASKS,'families':FAMILIES,'ops':OPS,'max_size':MAX_SIZE,'timeout_s':TIMEOUT,'max_solutions':MAX_SOLUTIONS,'query_budget':BUDGET,'heldout_values':VALUES},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  lock=json.loads(LOCK.read_text())
  if source_map()!=lock['sources']:raise SystemExit('source drift')
  envp={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};workers=[]
  for i,p in enumerate(lock['panels']):
   q=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=envp,text=True,capture_output=True,timeout=120)
   if q.returncode:raise RuntimeError(f'worker {i}: {q.stderr[-2000:]}')
   workers.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if source_map()!=lock['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'PrimitiveFamilySelectionV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':print(json.dumps(worker(json.loads(LOCK.read_text())['panels'][int(args[1])]),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
