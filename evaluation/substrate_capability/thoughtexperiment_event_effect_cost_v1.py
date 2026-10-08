#!/usr/bin/env python3
"""Source-locked cost and parity panel for opt-in per-effect rule snapshots."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve(); ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_event_effect_cost_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_EVENT_EFFECT_COST_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_event_effect_cost_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_event_effect_cost_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json','runners/dsl/Cargo.lock')
MODES=('plain','events','effects','exact','combined')
FIXTURES=('direct','same_event_multiwrite','report_object_cap')

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,*(ROOT/x for x in SOURCES)); binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}

def make_case(kind):
 from substrate_rs import Substrate
 s=Substrate()
 if kind=='direct':
  a=s.add_node('A',{'initial':1});b=s.add_node('B',{});s.add_edge_unchecked(a,'input',b)
  s._inner.add_rule({'name':'direct_writer','match':[['x','input','y']],'effects':[['set_attr','x','observed',True],['add_edge','x','derived','y',{}]]})
 elif kind=='same_event_multiwrite':
  a=s.add_node('A',{'value':0});b=s.add_node('B',{});s.add_edge_unchecked(a,'input',b)
  s._inner.add_rule({'name':'multiwrite_then_remove','match':[['x','input','y']],'effects':[['set_attr','x','value',1],['set_attr','x','value',2],['del_edge','x','input','y']]})
 elif kind=='report_object_cap':
  for group in range(33):
   edge_type=f'input_{group:02d}'
   for _ in range(512):
    a=s.add_node('A',{});b=s.add_node('B',{});s.add_edge_unchecked(a,edge_type,b)
   s._inner.add_rule({'name':f'bulk_writer_{group:02d}','match':[['x',edge_type,'y']],'effects':[['set_attr','x',f'added_{group:02d}',1]]})
 else:raise ValueError(kind)
 return s

def run_arm(kind,mode):
 s=make_case(kind);budget=40 if kind=='report_object_cap' else 3
 if mode=='combined':
  s._inner.begin_experiment_delta_journal_with_rule_effect_attribution();s._inner.checkpoint_experiment_delta_journal()
 elif mode=='exact':
  pass
 before=s._inner.graph_to_dict(); t0=time.perf_counter_ns();c0=time.process_time_ns()
 if mode=='plain': report=s._inner.run_rules_report(budget,False)
 elif mode=='events': report=s._inner.run_rules_delta_report(budget,False)
 elif mode=='effects': report=s._inner.run_rules_effect_delta_report(budget,False)
 elif mode=='exact': report=s._inner.run_rules_snapshot_delta_report(budget,False)
 elif mode=='combined':
  settlement=s._inner.run_rules_report(budget,False); residual=s._inner.finish_experiment_delta_journal();report=dict(settlement);report.update(residual)
 else:raise ValueError(mode)
 cpu=time.process_time_ns()-c0;wall=time.perf_counter_ns()-t0;after=s._inner.graph_to_dict()
 events=report.get('rule_write_events',[])
 compact_events=[]
 if kind=='same_event_multiwrite':
  compact_events=[e for e in events if e['rule_name']=='multiwrite_then_remove']
 event_bytes=len(json.dumps(events,sort_keys=True,separators=(',',':')).encode())
 semantic={k:report[k] for k in ('status','progress_steps','passes_completed')}
 semantic['graph_sha256']=hashlib.sha256(json.dumps(after,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return {'fixture':kind,'mode':mode,'wall_ns':wall,'cpu_ns':cpu,'semantic':semantic,'event_count':len(events),'event_json_bytes':event_bytes,'events':compact_events,
  'event_snapshot_bytes':report.get('rule_write_snapshot_bytes_estimated',0),'event_snapshot_objects':report.get('rule_write_snapshot_objects',0),'event_truncated':report.get('rule_write_snapshots_truncated',0),
  'effect_snapshot_bytes':report.get('rule_write_effect_snapshot_bytes',0),'effect_snapshot_objects':report.get('rule_write_effect_snapshot_objects',0),'effect_truncated':report.get('rule_write_effect_snapshots_truncated',0),
  'effect_snapshot_budget_bytes':report.get('rule_write_effect_snapshot_budget_bytes',4*1024*1024),'effect_snapshot_budget_objects':report.get('rule_write_effect_snapshot_budget_objects',16384),
  'residual_count':len(report.get('conclusions',{}).get('nodes',[]))+len(report.get('conclusions',{}).get('edges',[])) if mode=='combined' else None}

def rss_pss():
 result={}
 try:
  for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
   if line.startswith(('Rss:','Pss:')):
    k,v,*_=line.split();result[k[:-1].lower()+'_kib']=int(v)
 except OSError:pass
 return result

def isolated(kind,mode,rep):
 base=make_case(kind); # construct outside measured arm for resident-memory baseline
 budget=40 if kind=='report_object_cap' else 3
 if mode=='combined':base._inner.begin_experiment_delta_journal_with_rule_effect_attribution();base._inner.checkpoint_experiment_delta_journal()
 method={'plain':'run_rules_report','events':'run_rules_delta_report','effects':'run_rules_effect_delta_report','exact':'run_rules_snapshot_delta_report'}
 before_mem=rss_pss();t0=time.perf_counter_ns();c0=time.process_time_ns()
 if mode=='combined':
  settlement=base._inner.run_rules_report(budget,False);residual=base._inner.finish_experiment_delta_journal();report=dict(settlement);report.update(residual)
 else:report=getattr(base._inner,method[mode])(budget,False)
 wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-c0;after_mem=rss_pss()
 return {'fixture':kind,'mode':mode,'replicate':rep,'pid':os.getpid(),'wall_ns':wall,'cpu_ns':cpu,'rss_delta_kib':after_mem.get('rss_kib',0)-before_mem.get('rss_kib',0),'pss_delta_kib':after_mem.get('pss_kib',0)-before_mem.get('pss_kib',0),'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'event_count':len(report.get('rule_write_events',[])),'event_json_bytes':len(json.dumps(report.get('rule_write_events',[]),sort_keys=True,separators=(',',':')).encode()),'event_snapshot_bytes':report.get('rule_write_snapshot_bytes_estimated',0),'event_snapshot_objects':report.get('rule_write_snapshot_objects',0),'effect_snapshot_bytes':report.get('rule_write_effect_snapshot_bytes',0),'effect_snapshot_objects':report.get('rule_write_effect_snapshot_objects',0),'effect_truncated':report.get('rule_write_effect_snapshots_truncated',0),'semantic':(report['status'],report['progress_steps'],report['passes_completed'])}

def worker(i):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source/native lock mismatch before worker')
 rows=[run_arm(f,m) for f in FIXTURES for m in MODES];after=frozen()
 if after!=locked:raise RuntimeError('source/native lock mismatch after worker')
 return {'worker':i,'pid':os.getpid(),'sources_before':before,'sources_after':after,'rows':rows}

def isolated_worker(kind,mode,rep):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source/native lock mismatch before isolated probe')
 row=isolated(kind,mode,rep);after=frozen()
 if after!=locked:raise RuntimeError('source/native lock mismatch after isolated probe')
 return {'sources_before':before,'sources_after':after,**row}

def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock or capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentEventEffectCostV1Lock','sources':frozen(),'workers':3,'isolated_replicates':3,'modes':MODES,'fixtures':FIXTURES},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),separators=(',',':'),sort_keys=True));return 0
 if len(sys.argv)==5 and sys.argv[1]=='--isolated':print(json.dumps(isolated_worker(sys.argv[2],sys.argv[3],int(sys.argv[4])),separators=(',',':'),sort_keys=True));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage: --lock | --run | --worker N')
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source/native lock mismatch before capture')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)))
 iso=[]
 for kind in FIXTURES:
  for mode in MODES:
   for rep in range(3):
    p=subprocess.run([sys.executable,str(RUNNER),'--isolated',kind,mode,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
    if p.returncode:raise RuntimeError(f'isolated {kind}/{mode}/{rep}: {p.stderr[-2000:]}')
    iso.append(json.loads(p.stdout.strip().splitlines()[-1]))
 workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source/native lock drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentEventEffectCostV1','lock_sha256':sha(LOCK),'host':platform.platform(),'build_profile':'opt-level=3; lto=false; codegen-units=16','workers':workers,'isolated':iso},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0

if __name__=='__main__':raise SystemExit(main())
