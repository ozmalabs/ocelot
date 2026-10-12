#!/usr/bin/env python3
"""Native candidate-work replay over authored permutations of a task rule."""
from __future__ import annotations
import hashlib, itertools, json, os, random, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_JOIN_ORDER_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_join_order_v1_lock_20260927.json'
RAW=ROOT/'evaluation/reports/substrate_task_derived_join_order_v1_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_task_derived_join_order_v1_20260927.json'
ANALYZER=ROOT/'scripts/analyze_substrate_task_derived_join_order_v1.py'
PREDECESSOR=ROOT/'scripts/substrate_common_ground_task_identity_replication_v1.py'
SOURCES=(
 'seeds/conversation_discourse_state.json',
 'tests/fixtures/conversational_manifold/phase3_common_ground_stress.json',
 'domains/discourse_state.py','runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs',
 'runners/dsl/src/scale_audit.rs','runners/dsl/python/substrate_rs/_native.build.json',
 'evaluation/reports/substrate_seed_join_shapes_v1_20260927.json',
)
PERMUTATIONS=tuple(itertools.permutations(range(4)))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def native_identity():
 from substrate_rs import _native
 return {'sha256':sha(Path(_native.__file__).resolve()),'path':str(Path(_native.__file__).resolve())}
def fingerprint():
 paths=(*SOURCES,str(PROTOCOL.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),str(PREDECESSOR.relative_to(ROOT)))
 return {'files':{p:sha(ROOT/p) for p in paths},'native':native_identity(),
         'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def jobs(): return [( ''.join(map(str,p)),rep) for p in PERMUTATIONS for rep in range(3)]
def worker(label,rep):
 import importlib.util
 from substrate.world_adapter import WorldAdapter
 path=PREDECESSOR
 spec=importlib.util.spec_from_file_location('common_ground_replication',path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 indices=tuple(int(x) for x in label)
 if len(indices)!=4 or set(indices)!=set(range(4)): raise ValueError(label)
 audit_rows=[];target={'index':None,'installed':None}
 original_init=WorldAdapter.__init__
 def init_with_audit(self,*args,**kwargs):
  original_init(self,*args,**kwargs);inner=self.inner
  reset=inner.scale_audit_reset;enable=inner.scale_audit_set_enabled;snapshot=inner.scale_audit_snapshot
  def reset_both():
   reset();inner.scale_audit_per_rule_reset()
  def enable_both(on):
   inner.scale_audit_set_per_rule_enabled(on);enable(on)
  def capture_snapshot():
   counters=snapshot()
   audit_rows.append({'per_rule':[list(x) for x in inner.scale_audit_per_rule_snapshot()],
                      'clauses':[list(x) for x in inner.scale_audit_match_clause_snapshot()]})
   return counters
  inner.scale_audit_reset=reset_both
  inner.scale_audit_set_enabled=enable_both
  inner.scale_audit_snapshot=capture_snapshot
 WorldAdapter.__init__=init_with_audit
 def patch_rules(inner,arm):
  names={'discourse_goal_select','discourse_goal_execute','discourse_goal_resolve'}
  rows=inner.export_rules()
  targets=[(i,r) for i,r in enumerate(rows) if r.get('name') in names and r.get('active',True)]
  if len(targets)!=3: raise RuntimeError(f'expected three active lifecycle rules, found {len(targets)}')
  for i,_ in targets:
   if not inner.remove_rule(i): raise RuntimeError(f'failed to remove rule {i}')
  new=[]
  for _,prior in targets:
   r={k:v for k,v in prior.items() if k not in {'active','batch','content_hash','mutation_protected','revision','rule_uid'}}
   original_name=r['name'];r['name']=original_name+'_task_order_v1'
   if original_name=='discourse_goal_select':r['match']=[prior['match'][i] for i in indices]
   idx=int(inner.add_rule(r));new.append(idx)
   if original_name=='discourse_goal_select':
    target['index']=idx;target['installed']=[list(e) for e in inner.export_rules()[idx]['match']]
  return new
 mod.patch_rules=patch_rules
 result=mod.worker('explicit',rep)
 if len(audit_rows)!=len(result['checkpoints']): raise RuntimeError('audit/checkpoint cardinality mismatch')
 return {'permutation':label,'replicate':rep,'pid':os.getpid(),
         'target_rule_index':target['index'],'installed_match':target['installed'],
         'audit_rows':audit_rows,'task_run':result}
def main():
 if len(sys.argv)>1 and sys.argv[1]=='--worker':
  before=fingerprint();result=worker(sys.argv[2],int(sys.argv[3]));after=fingerprint()
  print(json.dumps({'before':before,'after':after,'worker':result},sort_keys=True,default=str));return
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps(fingerprint(),indent=2,sort_keys=True)+'\n');print(LOCK);return
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text())!=locked: raise SystemExit('missing or stale source/native lock')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')));env['PYTHONHASHSEED']='0'
 ordered=jobs();random.Random(20260927).shuffle(ordered);runs=[]
 for label,rep in ordered:
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',label,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
  runs.append(json.loads(cp.stdout))
 post=fingerprint()
 RAW.write_text(json.dumps({'schema_version':1,'run_id':'substrate-task-derived-join-order-v1-20260927','locked_inputs':locked,'post_run_inputs':post,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'worker_count':len(runs),'all_worker_inputs_stable':post==locked and all(r['before']==locked==r['after'] for r in runs),'raw':str(RAW.relative_to(ROOT))},indent=2))
if __name__=='__main__': main()
