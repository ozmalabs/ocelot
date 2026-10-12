#!/usr/bin/env python3
"""Paired native counter-on/off closure timings for the frozen task replay."""
from __future__ import annotations
import hashlib,importlib.util,json,os,random,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_JOIN_ORDER_AUDIT_OVERHEAD_V1_PREREG_20260929.md'
BASE=ROOT/'scripts/substrate_task_derived_join_order_context_scale_v1.py'
EXPECTED=ROOT/'evaluation/reports/task_derived_join_order_context_scale_v1_analysis_20260929.json'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_join_order_audit_overhead_v1_lock_20260929.json'
RAW=ROOT/'evaluation/reports/task_derived_join_order_audit_overhead_v1_raw_20260929.json'
OUT=ROOT/'evaluation/reports/task_derived_join_order_audit_overhead_v1_analysis_20260929.json'
ANALYZER=ROOT/'scripts/analyze_substrate_task_derived_join_order_audit_overhead_v1.py'
COUNTS=(0,8,32);REPEATS=tuple(range(10));MODES=('off','on')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 paths=(str(PROTOCOL.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),
  str(BASE.relative_to(ROOT)),str(EXPECTED.relative_to(ROOT)),
  'scripts/analyze_substrate_task_derived_join_order_context_scale_v1.py',
  'docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_JOIN_ORDER_CONTEXT_SCALE_V1_PREREG_20260929.md',
  'evaluation/substrate_capability/task_derived_join_order_context_scale_v1_lock_20260929.json',
  'evaluation/reports/task_derived_join_order_context_scale_v1_raw_20260929.json',
  'tests/fixtures/conversational_manifold/phase3_common_ground_stress.json','seeds/conversation_discourse_state.json',
  'domains/discourse_state.py','substrate/world_adapter.py','runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs',
  'runners/dsl/src/scale_audit.rs','runners/dsl/python/substrate_rs/_native.build.json')
 return {'files':{p:sha(ROOT/p) for p in paths},'native_sha256':sha(Path(_native.__file__).resolve()),
  'native_path':str(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),
  'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def jobs():return [(d,r,m) for d in COUNTS for r in REPEATS for m in MODES]
def worker(d,rep,mode):
 spec=importlib.util.spec_from_file_location('context_scale_base_audit_pair',BASE);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
 from substrate.world_adapter import WorldAdapter
 original=WorldAdapter.__init__
 def init_controlled(self,*args,**kwargs):
  original(self,*args,**kwargs)
  if mode=='off':
   inner=self.inner;set_global=inner.scale_audit_set_enabled;set_rule=inner.scale_audit_set_per_rule_enabled
   inner.scale_audit_set_enabled=lambda enabled:set_global(False)
   inner.scale_audit_set_per_rule_enabled=lambda enabled:set_rule(False)
 WorldAdapter.__init__=init_controlled
 out=base.worker(d,'0123',rep)
 out['audit_mode']=mode;out['pair_id']=f'D{d}-r{rep}'
 return out
def main():
 if len(sys.argv)>1 and sys.argv[1]=='--worker':
  d=int(sys.argv[2]);rep=int(sys.argv[3]);mode=sys.argv[4];before=fingerprint();w=worker(d,rep,mode);after=fingerprint()
  print(json.dumps({'before':before,'after':after,'worker':w},sort_keys=True,default=str));return 0
 if sys.argv[1:]==['--lock']:
  f=fingerprint();LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':f},indent=2,sort_keys=True)+'\n');print(LOCK);return 0
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale source/native lock')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')));env['PYTHONHASHSEED']='0'
 ordered=jobs();random.Random(20260929).shuffle(ordered);runs=[]
 for i,(d,r,m) in enumerate(ordered,1):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(d),str(r),m],cwd=ROOT,env=env,text=True,capture_output=True)
  runs.append(json.loads(cp.stdout) if cp.returncode==0 else {'worker_error':cp.stderr[-4000:],'decoy_count':d,'replicate':r,'audit_mode':m})
  print(f'worker {i}/60 D={d} rep={r} audit={m} rc={cp.returncode}',flush=True)
 post=fingerprint();RAW.write_text(json.dumps({'schema_version':1,'run_id':'task-derived-join-order-audit-overhead-v1-20260929',
  'locked_inputs':locked,'post_run_inputs':post,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'worker_count':len(runs),'source_stable':post==locked,'raw':str(RAW.relative_to(ROOT))},indent=2))
 return 0 if post==locked and len(runs)==60 and all('worker_error' not in x for x in runs) else 1
if __name__=='__main__':raise SystemExit(main())
