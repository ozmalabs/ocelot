#!/usr/bin/env python3
"""Source-lock, execute, and capture the Qwen3 cross-model transport experiment."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
CORPUS=ROOT/'evaluation/substrate_capability/fixtures/llm_cross_model_transport_v1_corpus.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_CROSS_MODEL_TRANSPORT_V1_1_AMENDMENT_20261002.md'
EXPORTER=ROOT/'evaluation/substrate_capability/llm_cross_model_transport_v1_export.py'
WORKER=ROOT/'evaluation/substrate_capability/llm_cross_model_transport_v1_worker.py'
BASE_RUNNER=ROOT/'evaluation/substrate_capability/llm_chain_transport_fanin_v1.py'
BASE_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_chain_transport_fanin_v1.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_cross_model_transport_v1.py'
SEED=ROOT/'seeds/can_native_reimplementation.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_cross_model_transport_v1_1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_cross_model_transport_v1_1_20261002.json'
MODELS={
 'qwen3_0_6b':ROOT/'evaluation/reports/llm_cross_model_transport_v1_qwen3_0_6b.npz',
 'qwen3_1_7b':ROOT/'evaluation/reports/llm_cross_model_transport_v1_qwen3_1_7b.npz'}
REPS=3

def digest(path):
 p=Path(path);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def sources():
 from substrate_rs import _native
 paths=[Path(__file__).resolve(),ANALYZER,CORPUS,PROTOCOL,EXPORTER,WORKER,BASE_RUNNER,BASE_ANALYZER,SEED,
  ROOT/'domains/llm_native_graph.py',ROOT/'domains/can_junction_tree.py',ROOT/'domains/graph_treewidth.py',ROOT/'domains/can_native_bp.py',
  ROOT/'runners/dsl/python/substrate_rs/_native.build.json',Path(_native.__file__).resolve()]
 for key,p in MODELS.items():
  prov=p.with_suffix('.provenance.json');tok=p.with_suffix('.tokenization.json')
  if not all(q.is_file() for q in (p,prov,tok)):raise SystemExit(f'missing locked export artifacts for {key}')
  pv=json.loads(prov.read_text())
  if not pv.get('sources_stable'):raise SystemExit(f'model sources changed during extraction: {key}')
  paths.extend([p,prov,tok])
 return {'artifacts':[digest(p) for p in paths],'replicates':REPS,'fanins':[1,2,4,8],'hops':[[10,11],[11,12],[12,13],[13,14]],'heldout_count':10,'mode_count':8,'ridge':1.0,'vocabulary':[-1.0,0.0,1.0]}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing v1.1 lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmCrossModelTransportV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source/artifact drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"}
 runs=[];failures=[]
 for label,export in MODELS.items():
  for rep in range(REPS):
   p=subprocess.run([sys.executable,str(WORKER),str(export),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=2400)
   if p.returncode:failures.append({'model':label,'replicate':rep,'error':p.stderr[-3000:]});continue
   try:r=json.loads(p.stdout.strip())
   except Exception as e:failures.append({'model':label,'replicate':rep,'error':f'{type(e).__name__}: {e}','stdout':p.stdout[-1000:]});continue
   r['model']=label;runs.append(r)
   print(f"model={label} rep={rep} pid={r.get('worker_pid')} cells={r.get('cells')}",flush=True)
 after=sources();all_rows=[x for r in runs for x in r['rows']]
 expected_models=set(MODELS)
 checks={'source_lock_unchanged':before==lock['sources']==after,'no_worker_failures':not failures,
 'six_fresh_workers':len(runs)==6 and len({r['worker_pid'] for r in runs})==6,
 'complete_per_model_grid':all(sum(1 for r in runs if r['model']==m)==3 and all(r['cells']==160 and len(r['rows'])==160 for r in runs if r['model']==m) for m in expected_models),
 'worker_source_locks':all(r['source_lock_start']==r['source_lock_end'] for r in runs),
 'all_exact_solver_gates':all(c['exact_extraction'] and c['no_mutation'] and c['width']==c['triangulation_width'] and abs(c['jt_energy']-c['oracle_energy'])<1e-8 and abs(c['direct_rescore']-c['oracle_energy'])<1e-8 for c in all_rows)}
 OUT.write_text(json.dumps({'schema':'LlmCrossModelTransportV1Capture','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':before,'post_run_sources':after,'checks':checks,'failures':failures,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failure_count':len(failures)},indent=2))
 return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
