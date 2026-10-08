#!/usr/bin/env python3
"""Source-locked measurement of finite behavior grouping and H×P cost."""
import hashlib,json,os,platform,subprocess,sys,time,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/BEHAVIOR_EQUIVALENCE_PARTITION_API_V1_PREREG_20261003.md';ANALYZER=ROOT/'evaluation/substrate_capability/analyze_behavior_equivalence_partition_v1.py';LOCK=ROOT/'evaluation/substrate_capability/behavior_equivalence_partition_v1_lock_20261003.json';OUT=ROOT/'evaluation/reports/behavior_equivalence_partition_v1_20261003.json'
UPLOCK=ROOT/'evaluation/substrate_capability/primitive_semantic_equivalence_v1_lock_20261003.json';UPRAW=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_20261003.json';UPAN=ROOT/'evaluation/reports/primitive_semantic_equivalence_v1_analysis_20261003.json';UPRUN=ROOT/'evaluation/substrate_capability/primitive_semantic_equivalence_v1.py'
SOURCES=('domains/contract_query.py','domains/engine_provenance.py','runners/dsl/src/term.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py')
REPS=5;H_SIZES=(1,2,4,8,16,32,64);P_SIZES=(4,8,16,32,64);TASKS=('additive','product','ordering','opposition','inequality')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def source_map():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 paths=[ROOT/p for p in SOURCES]+[RUNNER,PRE,ANALYZER,UPLOCK,UPRAW,UPAN,UPRUN]
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__))},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
# The upstream raw is the semantic-equivalence capture; each worker stores both
# original and zero-aware final survivors and the source lock supplies probes.
def study_inputs():
 up_l=json.loads(UPLOCK.read_text());up_r=json.loads(UPRAW.read_text());cells=[];scale=[]
 panel_by={(p['task'],p['worker']):p for p in up_l['panels']}
 for w in up_r['workers']:
  p=panel_by[(w['task'],w['worker'])]
  for domain in ('original','zero_aware'):
   probes=(p['original_selection_pool']+p['original_challenge_order']) if domain=='original' else (p['zero_selection_pool']+p['zero_challenge_pool'])
   cells.append({'task':w['task'],'worker':w['worker'],'domain':domain,'hypotheses':w[domain]['scored_survivors'],'probes':probes})
  if w['worker']==0:
   initial=p['initial_hypotheses'];probes=p['zero_selection_pool']+p['zero_challenge_pool'];scale.append({'task':w['task'],'worker':w['worker'],'hypotheses':initial,'probes':probes})
 return cells,scale
def measure(hypotheses,probes,reps=REPS):
 from domains.contract_query import partition_hypotheses_by_behavior
 from substrate_rs import _native
 n=_native.Substrate();times=[];counts=[];result=None
 for _ in range(reps):
  calls=[0]
  def evaluate(term,env):calls[0]+=1;return n.evaluate(term,env)
  t=time.perf_counter_ns();result=partition_hypotheses_by_behavior(evaluate,hypotheses,probes);times.append(time.perf_counter_ns()-t);counts.append(calls[0])
 compact={'ok':result.get('ok'),'probe_count':result.get('probe_count'),'probe_sha256':result.get('probe_sha256'),'hypothesis_count':result.get('hypothesis_count'),'class_count':result.get('class_count'),'all_agree_on_probes':result.get('all_agree_on_probes'),'class_ids':[x['hypothesis_ids'] for x in result.get('classes',[])]}
 return {'partition':compact,'elapsed_ns':times,'median_ns':statistics.median(times),'evaluation_calls':counts}
def worker():
 cells,scale=study_inputs();actual=[]
 for c in cells:
  m=measure([{'id':h['id'],'term':h['term']} for h in c['hypotheses']], [dict(zip(('ax','ay','ex','ey'),r)) for r in c['probes']])
  actual.append({**{k:c[k] for k in ('task','worker','domain')},'hypothesis_count':len(c['hypotheses']),'probe_count':len(c['probes']),**m})
 curves=[]
 for s in scale:
  source=s['hypotheses'];base=source[0]['term'] if source else None
  for hsize in H_SIZES:
   hs=[{'id':f"scale{i:03d}",'term':source[i%len(source)]['term'] if source else base} for i in range(hsize)]
   for psize in P_SIZES:
    m=measure(hs,[dict(zip(('ax','ay','ex','ey'),r)) for r in s['probes'][:psize]])
    curves.append({'task':s['task'],'worker':s['worker'],'H':hsize,'P':psize,'distinct_source_terms':len({json.dumps(h['term'],sort_keys=True) for h in source}),'synthetic_repetition':hsize>len(source),**m})
 from domains.contract_query import partition_hypotheses_by_behavior
 error_hyps=[{'id':'bool','term':{'kind':'bool'}},{'id':'int','term':{'kind':'int'}},{'id':'error','term':{'kind':'error'}}];error_counts=[];error_result=None
 for _ in range(REPS):
  calls=[0]
  def error_eval(term,env):
   calls[0]+=1
   if term['kind']=='error':raise RuntimeError('controlled evaluation failure')
   return True if term['kind']=='bool' else 1
  error_result=partition_hypotheses_by_behavior(error_eval,error_hyps,[{'probe':0},{'probe':1}]);error_counts.append(calls[0])
 return {'actual_panels':actual,'scaling_curves':curves,'typed_error_control':{'partition':{k:v for k,v in error_result.items() if k!='classes'},'class_ids':[x['hypothesis_ids'] for x in error_result['classes']],'evaluation_calls':error_counts}}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  cells,scale=study_inputs();LOCK.write_text(json.dumps({'schema':'BehaviorEquivalencePartitionV1Lock','sources':source_map(),'cells':cells,'scale_inputs':scale,'repetitions':REPS,'H_sizes':H_SIZES,'P_sizes':P_SIZES,'tasks':TASKS},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args==['--run']:
  l=json.loads(LOCK.read_text())
  if source_map()!=l['sources']:raise SystemExit('source drift')
  result=worker()
  if source_map()!=l['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'BehaviorEquivalencePartitionV1Results','lock_sha256':sha(LOCK),'sources':source_map(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**result},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 raise SystemExit('usage: --lock | --run')
if __name__=='__main__':raise SystemExit(main())
