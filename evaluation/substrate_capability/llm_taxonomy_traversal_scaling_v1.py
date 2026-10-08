#!/usr/bin/env python3
"""Lock and run a task-derived open-vocabulary graph traversal benchmark."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
BASE_PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TAXONOMY_TRAVERSAL_SCALING_V1_PREREG_20261002.md'
PROTOCOL=ROOT/'docs/research/engine_substrate/LLM_TAXONOMY_TRAVERSAL_SCALING_V1_1_AMENDMENT_20261002.md'
PREP=ROOT/'evaluation/substrate_capability/prepare_llm_taxonomy_traversal_scaling_v1.py'
WORKER=ROOT/'evaluation/substrate_capability/llm_taxonomy_traversal_scaling_v1_worker.py'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_llm_taxonomy_traversal_scaling_v1.py'
SEED=ROOT/'domain_data/llm_harvest/qwen3_reaped_isa_full.json'
QUERY=ROOT/'evaluation/substrate_capability/fixtures/llm_taxonomy_traversal_scaling_v1_queries.json'
LOCK=ROOT/'evaluation/substrate_capability/llm_taxonomy_traversal_scaling_v1_1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/llm_taxonomy_traversal_scaling_v1_1_20261002.json'
REPS=3
def digest(path):
 p=Path(path);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def sources():
 from substrate_rs import _native
 paths=[Path(__file__).resolve(),BASE_PROTOCOL,PROTOCOL,PREP,WORKER,ANALYZER,SEED,QUERY,
  ROOT/'domains/llm_knowledge_seed.py',ROOT/'seeds/can_native_reimplementation.json',
  Path(_native.__file__).resolve(),ROOT/'runners/dsl/python/substrate_rs/_native.build.json']
 return {'artifacts':[digest(p) for p in paths],'replicates':REPS,'positive_queries':4820,'negative_queries':4820,'max_hops':6,'warmup_queries':64}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'LlmTaxonomyTraversalScalingV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source/query/seed drift from lock')
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native engine stale: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}:{os.environ.get('PYTHONPATH','')}"}
 runs=[];failures=[]
 for rep in range(REPS):
  p=subprocess.run([sys.executable,str(WORKER),str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1800)
  if p.returncode:failures.append({'replicate':rep,'error':p.stderr[-3000:]});continue
  try:r=json.loads(p.stdout.strip())
  except Exception as e:failures.append({'replicate':rep,'error':f'{type(e).__name__}: {e}','stdout':p.stdout[-1000:]});continue
  runs.append(r);print(f"rep={rep} pid={r['pid']} queries={r['queries_per_worker']} graph={r['graph']['concepts']}/{r['graph']['relation_edges']}",flush=True)
 after=sources()
 checks={'source_lock_unchanged':before==lock['sources']==after,'no_worker_failures':not failures,
  'three_fresh_workers':len(runs)==3 and len({r['pid'] for r in runs})==3,
  'complete_worker_query_sets':all(r['queries_per_worker']==9640 and len(r['answers']['positive'])==4820 and len(r['answers']['negative'])==4820 for r in runs),
  'worker_locks_stable':all(r['source_lock_start']==r['source_lock_end'] for r in runs),
  'graph_not_mutated':all(r['graph_unchanged'] and r['graph_digest_before']==r['graph_digest_after'] for r in runs)}
 OUT.write_text(json.dumps({'schema':'LlmTaxonomyTraversalScalingV1Capture','lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':before,'post_run_sources':after,
  'checks':checks,'failures':failures,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':checks,'failure_count':len(failures)},indent=2))
 return 0 if all(checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
