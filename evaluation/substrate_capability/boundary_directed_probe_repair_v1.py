#!/usr/bin/env python3
"""Targeted probe repair from a candidate's numeric comparison boundary."""
import hashlib,json,os,platform,subprocess,sys,time,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
HERE=Path(__file__).resolve();PRE=ROOT/'docs/research/engine_substrate/BOUNDARY_DIRECTED_PROBE_REPAIR_V1_PREREG_20261004.md'
AN=ROOT/'evaluation/substrate_capability/analyze_boundary_directed_probe_repair_v1.py'
POLICY=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1.py'
ULOCK=ROOT/'evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json';URAW=ROOT/'evaluation/reports/coverage_aware_class_return_v1_20261003.json'
UOUT=ROOT/'evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json'
FLOCK=ROOT/'evaluation/substrate_capability/probe_coverage_false_equivalent_v1_lock_20261004.json';FRAW=ROOT/'evaluation/reports/probe_coverage_false_equivalent_v1_20261004.json'
FOUT=ROOT/'evaluation/reports/probe_coverage_false_equivalent_v1_analysis_20261004.json'
LOCK=ROOT/'evaluation/substrate_capability/boundary_directed_probe_repair_v1_lock_20261004.json';OUT=ROOT/'evaluation/reports/boundary_directed_probe_repair_v1_20261004.json'
KEYS=('ax','ay','ex','ey')
SOURCES=('docs/research/engine_substrate/BOUNDARY_DIRECTED_PROBE_REPAIR_V1_PREREG_20261004.md','evaluation/substrate_capability/boundary_directed_probe_repair_v1.py','evaluation/substrate_capability/analyze_boundary_directed_probe_repair_v1.py','evaluation/substrate_capability/coverage_aware_class_return_v1.py','evaluation/substrate_capability/coverage_aware_class_return_v1_lock_20261003.json','evaluation/reports/coverage_aware_class_return_v1_20261003.json','evaluation/reports/coverage_aware_class_return_v1_1_analysis_20261004.json','evaluation/substrate_capability/probe_coverage_false_equivalent_v1_lock_20261004.json','evaluation/reports/probe_coverage_false_equivalent_v1_20261004.json','evaluation/reports/probe_coverage_false_equivalent_v1_analysis_20261004.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','domains/engine_provenance.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def smap():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 b=Path(_native.__file__).resolve()
 return {'files':{x:sha(ROOT/x) for x in SOURCES},'binary':{'path':str(b),'sha256':sha(b)},'rust_fingerprint':rust_source_fingerprint(str(ROOT)),'python':sys.version,'platform':platform.platform()}
def inputs():
 ul=json.loads(ULOCK.read_text());ur=json.loads(URAW.read_text());ua=json.loads(UOUT.read_text());fl=json.loads(FLOCK.read_text());fr=json.loads(FRAW.read_text());fa=json.loads(FOUT.read_text())
 if not ua.get('passed') or not fa.get('passed') or fa['summary'].get('false_safe_class_returns')!=5:raise RuntimeError('upstream failure evidence invalid')
 if ur.get('lock_sha256')!=sha(ULOCK) or ur.get('sources')!=ul.get('sources') or ua.get('capture_sha256')!=sha(URAW):raise RuntimeError('policy input provenance mismatch')
 if fr.get('lock_sha256')!=sha(FLOCK) or fr.get('sources')!=fl.get('sources') or fa.get('capture_sha256')!=sha(FRAW):raise RuntimeError('false-control provenance mismatch')
 return [p for p in ul['panels'] if p['task']=='opposition'],fl['candidate_terms']
def lit_boundary(t):
 if isinstance(t,dict):
  if t.get('type') in ('Lt','Gt') and t.get('a',{}).get('type')=='Var' and t.get('b',{}).get('type')=='Lit' and isinstance(t['b'].get('value'),(int,float)):return t['a']['name'],float(t['b']['value'])
  for v in t.values():
   z=lit_boundary(v)
   if z:return z
 if isinstance(t,list):
  for v in t:
   z=lit_boundary(v)
   if z:return z
 return None
def loadpolicy():
 s=importlib.util.spec_from_file_location('coverage_aware_class_return_v1',POLICY);m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m);return m
def worker(i):
 from substrate_rs import _native
 from domains.contract_query import select_discriminating_input,partition_hypotheses_by_behavior
 ps,terms=inputs();p=ps[i];native=_native.Substrate();bounds=[]
 for h in terms:
  z=lit_boundary(h['term'])
  if z and z not in bounds:bounds.append(z)
 if not bounds:raise RuntimeError('no numeric comparison bound')
 var,cut=bounds[0]
 if var!='ax':raise RuntimeError(f'unsupported core variable {var}')
 probes=[{'ax':x,'ay':0.,'ex':-x,'ey':0.} for x in (cut-.5,cut,cut+.5)]
 hyps=[{'id':h['id'],'family':h['family'],'term':h['term']} for h in terms]
 choice=select_discriminating_input(lambda term,e:native.evaluate(term,e),hyps,probes,[])
 if not choice.get('ok'):raise RuntimeError(f'boundary selector abstained {choice}')
 q=choice['query'];row=[float(q[k]) for k in KEYS];label=float(row[0])==-float(row[2]);survivors=[]
 for h in hyps:
  try:v=native.evaluate(h['term'],q)
  except Exception:v=None
  if type(v)is bool and v==label:survivors.append(h)
 from coverage_aware_class_return_v1 import env
 old=p['original_selection_pool']+p['original_challenge_order']+p['zero_selection_pool']+p['zero_challenge_pool']
 covered=list(dict.fromkeys(tuple(x) for x in old+[row]))
 part=partition_hypotheses_by_behavior(lambda term,e:native.evaluate(term,e),survivors,[env(x) for x in covered])
 return {'task':p['task'],'worker':p['worker'],'threshold_variable':var,'threshold':cut,'generated_probes':probes,'selector_choice':choice,'query_row':row,'oracle_label':label,'candidate_ids_before':[h['id'] for h in hyps],'survivor_ids_after':[h['id'] for h in survivors],'partition':part,'covered_probe_count':len(covered),'candidate_evaluations':len(hyps)*len(probes)}
def main():
 a=sys.argv[1:]
 if a==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  ps,t=inputs();LOCK.write_text(json.dumps({'schema':'BoundaryDirectedProbeRepairV1Lock','sources':smap(),'upstream_lock_sha256':sha(ULOCK),'false_control_lock_sha256':sha(FLOCK),'panels':ps,'candidate_terms':t,'boundary_offsets':[-.5,0.,.5]},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if a==['--run']:
  l=json.loads(LOCK.read_text())
  if smap()!=l['sources'] or inputs()!=(l['panels'],l['candidate_terms']):raise SystemExit('source/input drift')
  env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
  for i in range(len(l['panels'])):
   q=subprocess.run([sys.executable,str(HERE),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
   if q.returncode:raise RuntimeError(q.stderr[-2500:])
   rows.append(json.loads(q.stdout.strip().splitlines()[-1]))
  if smap()!=l['sources']:raise SystemExit('source drift during run')
  OUT.write_text(json.dumps({'schema':'BoundaryDirectedProbeRepairV1Results','lock_sha256':sha(LOCK),'sources':smap(),'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
 if len(a)==2 and a[0]=='--worker':print(json.dumps(worker(int(a[1])),sort_keys=True,separators=(',',':')));return 0
 raise SystemExit('usage: --lock | --run | --worker ID')
if __name__=='__main__':raise SystemExit(main())
