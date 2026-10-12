#!/usr/bin/env python3
"""Locked source-current replay of the frozen list PBE composition suite."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/SUBSTRATE_LIST_PBE_CURRENT_SOURCE_REPLAY_PREREG_20261003.md'
LOCK=ROOT/'evaluation/substrate_capability/list_pbe_current_source_replay_lock_20261003.json';RAW=ROOT/'evaluation/reports/substrate_list_pbe_composition_current_source_20261003.json';ANALYSIS=ROOT/'evaluation/reports/substrate_list_pbe_composition_current_source_analysis_20261003.json';PRIOR=ROOT/'evaluation/reports/substrate_list_pbe_composition_benchmark_amended_20260925.json'
FIXTURE=ROOT/'tests/fixtures/substrate_list_pbe_confirmatory/tasks.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 dsl=ROOT/'runners/dsl';native=dsl/'python/substrate_rs/_native.abi3.so'
 paths={'protocol':PRE,'wrapper':RUNNER,'benchmark':ROOT/'scripts/substrate_list_pbe_composition_benchmark.py','analyzer':ROOT/'scripts/analyze_substrate_list_pbe_composition_benchmark.py','fixture_generator':ROOT/'tests/fixtures/substrate_list_pbe_confirmatory/build_tasks.py','fixture':FIXTURE,'prior_report':PRIOR,'amendment':ROOT/'docs/research/engine_substrate/SUBSTRATE_LIST_PBE_COMPOSITION_BENCHMARK_AMENDMENT_20260925.md','benchmark_protocol':ROOT/'docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md','p4_runner':ROOT/'scripts/prog_synthesis_battery.py','p4_adapter':ROOT/'domains/prog_synthesis.py','p4_seed':ROOT/'seeds/program_synthesis.json','native_synthesizer':dsl/'src/synth_enumerate.rs','native_extension':native,'native_build_manifest':dsl/'python/substrate_rs/_native.build.json','cargo_lock':dsl/'Cargo.lock'}
 return {k:sha(v) for k,v in paths.items()}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or RAW.exists() or ANALYSIS.exists():raise SystemExit('refusing overwrite')
  stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,text=True).strip()
  if stale:raise SystemExit(f'native build stale:\n{stale}')
  LOCK.write_text(json.dumps({'schema':'ListPbeCurrentSourceReplayLock','inputs':inputs(),'frozen_before_execution':True,'arms':['main','frozen','main_replication'],'task_count':30},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --run')
 locked=json.loads(LOCK.read_text())
 if inputs()!=locked['inputs']:raise SystemExit('source/input lock mismatch')
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,cwd=ROOT,text=True).strip()
 if stale:raise SystemExit(f'native build stale:\n{stale}')
 os.environ.setdefault('OZMA_NO_LLM','1');os.environ.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 import substrate_list_pbe_composition_benchmark as bench
 bench.OUT=RAW;bench.main()
 payload=json.loads(RAW.read_text());prior=json.loads(PRIOR.read_text());comparison={}
 for arm in ('main','frozen','main_replication'):
  old={r['task_id']:r for r in prior['cases'][arm]};new={r['task_id']:r for r in payload['cases'][arm]}
  comparison[arm]={'task_count':len(new),'outcome_mismatches':[k for k,v in new.items() if old[k]['outcome']!=v['outcome']],'status_mismatches':[k for k,v in new.items() if old[k]['status']!=v['status']],'construction_mismatches':[k for k,v in new.items() if old[k].get('construction')!=v.get('construction')]}
 payload['run_id']='substrate-list-pbe-current-source-replay-20261003';payload['source_current_replay']={'lock_sha256':sha(LOCK),'locked_inputs':locked['inputs'],'comparison_to_prior':comparison,'all_outcomes_match':all(not x['outcome_mismatches'] for x in comparison.values())}
 RAW.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+'\n')
 import analyze_substrate_list_pbe_composition_benchmark as analyzer
 analyzer.REPORT=RAW;analyzer.OUT=ANALYSIS;analyzer.main()
 print(json.dumps({'raw':str(RAW.relative_to(ROOT)),'analysis':str(ANALYSIS.relative_to(ROOT)),'comparison':payload['source_current_replay']['comparison_to_prior']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
