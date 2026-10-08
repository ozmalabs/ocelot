#!/usr/bin/env python3
"""Locked installation-cost replication for context-scale join ordering."""
from __future__ import annotations
import hashlib,importlib.util,itertools,json,os,random,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
AMENDMENT=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_JOIN_ORDER_CONTEXT_SCALE_V1_1_AMENDMENT_20260929.md'
BASE=ROOT/'scripts/substrate_task_derived_join_order_context_scale_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_JOIN_ORDER_CONTEXT_SCALE_V1_PREREG_20260929.md'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_join_order_context_scale_v1_1_lock_20260929.json'
RAW=ROOT/'evaluation/reports/task_derived_join_order_context_scale_v1_1_raw_20260929.json'
ANALYZER=ROOT/'scripts/analyze_substrate_task_derived_join_order_context_scale_v1_1.py'
COUNTS=(0,8,32);PERMS=tuple(itertools.permutations(range(4)))
LIFECYCLE={'discourse_goal_select','discourse_goal_execute','discourse_goal_resolve'}
SUFFIX='_task_context_scale_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 paths=(str(AMENDMENT.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT)),
        str(ANALYZER.relative_to(ROOT)),str(BASE.relative_to(ROOT)),
        'scripts/substrate_common_ground_task_identity_replication_v1.py',
        'tests/fixtures/conversational_manifold/phase3_common_ground_stress.json','seeds/conversation_discourse_state.json',
        'domains/discourse_state.py','substrate/world_adapter.py','runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs',
        'runners/dsl/src/scale_audit.rs','runners/dsl/python/substrate_rs/_native.build.json')
 return {'files':{p:sha(ROOT/p) for p in paths},'native_sha256':sha(Path(_native.__file__).resolve()),
  'native_path':str(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),
  'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def jobs():return [(d,''.join(map(str,p)),r) for d in COUNTS for p in PERMS for r in range(3)]
def worker(d,label,rep):
 spec=importlib.util.spec_from_file_location('context_scale_base',BASE);base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
 from substrate.world_adapter import WorldAdapter
 additions=[];removals=[];original_init=WorldAdapter.__init__
 def init_timed(self,*args,**kwargs):
  original_init(self,*args,**kwargs);inner=self.inner
  add=inner.add_rule;remove=inner.remove_rule
  def timed_add(rule):
   name=str(rule.get('name',''));wall=time.perf_counter_ns();cpu=time.process_time_ns();result=add(rule)
   elapsed={'rule_name':name,'wall_ns':time.perf_counter_ns()-wall,'cpu_ns':time.process_time_ns()-cpu}
   if name in LIFECYCLE or name.endswith(SUFFIX):additions.append(elapsed)
   return result
  def timed_remove(index):
   rules=inner.export_rules();name=str(rules[index].get('name','')) if 0<=int(index)<len(rules) else ''
   wall=time.perf_counter_ns();cpu=time.process_time_ns();result=remove(index)
   if name in LIFECYCLE or name.endswith(SUFFIX):removals.append({'rule_name':name,'wall_ns':time.perf_counter_ns()-wall,'cpu_ns':time.process_time_ns()-cpu})
   return result
  inner.add_rule=timed_add;inner.remove_rule=timed_remove
 WorldAdapter.__init__=init_timed
 result=base.worker(d,label,rep)
 target_name='discourse_goal_select'+SUFFIX
 target=[x for x in additions if x['rule_name']==target_name]
 if len(target)!=1 or len(additions)!=3 or len(removals)!=3:raise RuntimeError('unexpected lifecycle install/remove call count')
 result['installation_timing']={'target_rule_add':target[0],'lifecycle_add_calls':additions,
   'lifecycle_remove_calls':removals,'lifecycle_add_wall_ns':sum(x['wall_ns'] for x in additions),
   'lifecycle_add_cpu_ns':sum(x['cpu_ns'] for x in additions),
   'lifecycle_remove_wall_ns':sum(x['wall_ns'] for x in removals),
   'lifecycle_remove_cpu_ns':sum(x['cpu_ns'] for x in removals)}
 return result
def main():
 if len(sys.argv)>1 and sys.argv[1]=='--worker':
  d=int(sys.argv[2]);label=sys.argv[3];rep=int(sys.argv[4]);before=fingerprint();w=worker(d,label,rep);after=fingerprint()
  print(json.dumps({'before':before,'after':after,'worker':w},sort_keys=True,default=str));return 0
 if sys.argv[1:]==['--lock']:
  f=fingerprint();LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':f},indent=2,sort_keys=True)+'\n');print(LOCK);return 0
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale source/native lock')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')));env['PYTHONHASHSEED']='0'
 ordered=jobs();random.Random(20260930).shuffle(ordered);runs=[]
 for i,(d,label,rep) in enumerate(ordered,1):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(d),label,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True)
  runs.append(json.loads(cp.stdout) if cp.returncode==0 else {'worker_error':cp.stderr[-4000:],'decoy_count':d,'permutation':label,'replicate':rep})
  print(f'worker {i}/216 D={d} order={label} rep={rep} rc={cp.returncode}',flush=True)
 post=fingerprint();RAW.write_text(json.dumps({'schema_version':1,'run_id':'task-derived-join-order-context-scale-v1.1-20260929',
   'locked_inputs':locked,'post_run_inputs':post,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'worker_count':len(runs),'source_stable':post==locked,'raw':str(RAW.relative_to(ROOT))},indent=2))
 return 0 if post==locked and len(runs)==216 and all('worker_error' not in x for x in runs) else 1
if __name__=='__main__':raise SystemExit(main())
