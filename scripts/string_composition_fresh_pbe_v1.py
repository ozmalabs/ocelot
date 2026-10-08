#!/usr/bin/env python3
"""Prelocked four-arm P4 evaluation on a fresh generated string suite."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/STRING_COMPOSITION_FRESH_PBE_V1_PREREG_20261003.md';FIXTURE=ROOT/'tests/fixtures/substrate_string_composition_fresh/tasks.json';GEN=ROOT/'tests/fixtures/substrate_string_composition_fresh/build_tasks.py';BENCH=ROOT/'scripts/substrate_string_pbe_contrast_benchmark.py';AN=ROOT/'evaluation/substrate_capability/analyze_string_composition_fresh_pbe_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/string_composition_fresh_pbe_v1_lock_20261003.json';RAW=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_20261003.json';ANALYSIS=ROOT/'evaluation/reports/string_composition_fresh_pbe_v1_analysis_20261003.json'
SOURCES=('scripts/prog_synthesis_battery.py','domains/prog_synthesis.py','domains/prog_retrieval.py','domains/code_writing.py','seeds/program_synthesis.json','seeds/mbpp_exemplars.json','seeds/code_write_constructions.json','runners/dsl/src/synth_enumerate.rs','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 from substrate_rs import _native
 from domains.engine_provenance import rust_source_fingerprint
 files=[ROOT/p for p in SOURCES]+[RUNNER,PRE,FIXTURE,GEN,BENCH,AN]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'engine':rust_source_fingerprint(str(ROOT))}
def fresh():
 out=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,text=True).strip()
 if out:raise SystemExit('native build stale:\n'+out)
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or RAW.exists() or ANALYSIS.exists():raise SystemExit('refusing overwrite')
  fresh();LOCK.write_text(json.dumps({'schema':'StringCompositionFreshPbeV1Lock','inputs':inputs(),'task_count':18,'arms':['main','no_retrieval','no_retrieval_escalated','main_replay'],'escalated_candidate_budget':500000},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --run')
 lock=json.loads(LOCK.read_text())
 if inputs()!=lock['inputs']:raise SystemExit('source/input lock mismatch')
 fresh();os.environ.setdefault('OZMA_NO_LLM','1');os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 import substrate_string_pbe_contrast_benchmark as bench
 bench.FIXTURE=FIXTURE;bench.OUT=RAW;bench.main()
 payload=json.loads(RAW.read_text());payload['run_id']='string-composition-fresh-pbe-v1-20261003';payload['run_state']='prelocked_fresh_task_family'
 payload['design']['suite_id']='substrate-string-composition-fresh-v1';payload['source_lock_sha256']=sha(LOCK);payload['task_generator_sha256']=sha(GEN);payload['fixture_sha256']=sha(FIXTURE)
 prov=payload.get('provenance',{}).get('sha256',{});prov['task_generator']=sha(GEN);prov['fixture']=sha(FIXTURE);prov['preregistration']=sha(PRE);prov['current_source_wrapper']=sha(RUNNER);prov['independent_analyzer']=sha(AN)
 RAW.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+'\n')
 sys.path.insert(0,str(ROOT/'evaluation/substrate_capability'))
 import analyze_string_composition_fresh_pbe_v1 as audit
 audit.FIXTURE=FIXTURE;audit.RAW=RAW;audit.OUT=ANALYSIS
 code=audit.main()
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'analysis':str(ANALYSIS.relative_to(ROOT)),'summary':payload['summary'],'analysis_passed':code==0},indent=2));return code
if __name__=='__main__':raise SystemExit(main())
