#!/usr/bin/env python3
"""Source-locked direct ProgEval audit for fresh string compositions."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
HERE=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/STRING_COMPOSITION_NATIVE_EXECUTION_AUDIT_V1_PREREG_20261003.md';FIX=ROOT/'tests/fixtures/substrate_string_composition_fresh/tasks.json';GEN=ROOT/'tests/fixtures/substrate_string_composition_fresh/build_tasks.py'
PRIOR=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_20261003.json';PRIORLOCK=ROOT/'evaluation/substrate_capability/string_composition_fresh_pbe_v1_lock_20261003.json'
LOCK=ROOT/'evaluation/substrate_capability/string_composition_native_execution_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/string_composition_native_execution_v1_20261003.json';AN=ROOT/'evaluation/substrate_capability/analyze_string_composition_native_execution_v1.py'
SOURCES=('scripts/prog_synthesis_battery.py','domains/prog_synthesis.py','runners/dsl/src/term.rs','runners/dsl/src/prog_eval.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def v(n):return {'type':'Var','name':n}
def lit(x):return {'type':'Lit','value':x}
def compose(t):
 fam=t['oracle_kind'];arg=t['parameter'];s=v('s')
 if fam=='casefold_count':value={'type':'StrCount','text':{'type':'CaseFold','text':s},'sub':lit(arg)}
 elif fam=='casefold_split':value={'type':'Split','text':{'type':'CaseFold','text':s},'sep':lit(arg.casefold())}
 elif fam=='reverse_then_split':value={'type':'Split','text':{'type':'Reverse','seq':s},'sep':lit(arg)}
 elif fam=='remove_separator':
  value={'type':'Fold','source':{'type':'Split','text':s,'sep':lit(arg)},'var_name':'piece','acc_name':'acc','init':lit(''),'body':{'type':'StringConcat','parts':[v('acc'),v('piece')]}}
 elif fam=='reverse_then_replace':
  value={'type':'Replace','text':{'type':'Reverse','seq':s},'old':lit(arg[0]),'new':lit(arg[1])}
 elif fam=='split_reverse_tokens':
  value={'type':'MapList','source':{'type':'Split','text':s,'sep':lit(arg)},'var_name':'piece','value':{'type':'Reverse','seq':v('piece')}}
 else:raise ValueError(fam)
 return {'type':'ProgSeq','stmts':[{'type':'ProgDefFnParam','name':'s','default':None},{'type':'ProgReturn','value':value}]}
def inputs():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 paths=[ROOT/x for x in SOURCES]+[HERE,AN,PRE,FIX,GEN,PRIOR,PRIORLOCK]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'engine':rust_source_fingerprint(str(ROOT))}
def fresh():
 s=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,text=True).strip()
 if s:raise SystemExit('native build stale:\n'+s)
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  fresh();LOCK.write_text(json.dumps({'schema':'StringCompositionNativeExecutionV1Lock','inputs':inputs(),'rows_per_task':7,'task_count':18},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--analyze']:
  import analyze_string_composition_native_execution_v1 as audit;return audit.main()
 if a!=['--run']:raise SystemExit('usage --lock | --run | --analyze')
 l=json.loads(LOCK.read_text())
 if inputs()!=l['inputs']:raise SystemExit('source lock mismatch')
 fresh();os.environ.setdefault('OZMA_NO_LLM','1');os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 import prog_synthesis_battery as p4
 suite=json.loads(FIX.read_text());rows=[];t0=time.perf_counter_ns()
 for task in suite['tasks']:
  ir=compose(task);out=[]
  for row in task['example_rows']+task['held_out_rows']:
   result=p4.prog_eval(ir,dict(row['inputs']));got=result.get('result');ok=result.get('halted') is True and result.get('trap') is None and p4.agree(got,row['expected'])
   out.append({'inputs':row['inputs'],'expected':row['expected'],'got':got,'halted':result.get('halted'),'trap':result.get('trap'),'exact':bool(ok)})
  rows.append({'task_id':task['id'],'family':task['family'],'ir':ir,'rows':out,'exact':all(x['exact'] for x in out),'heldout_exact':all(x['exact'] for x in out[4:])})
 payload={'schema':'StringCompositionNativeExecutionV1Results','lock_sha256':sha(LOCK),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':inputs(),'elapsed_ns':time.perf_counter_ns()-t0,'tasks':rows,'summary':{'task_count':len(rows),'all_row_exact_tasks':sum(x['exact'] for x in rows),'heldout_exact_tasks':sum(x['heldout_exact'] for x in rows),'rows_checked':sum(len(x['rows']) for x in rows),'evaluation_errors':sum(bool(x['trap']) or x['halted'] is not True for t in rows for x in t['rows'])}}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n');print(json.dumps(payload['summary'],indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
