#!/usr/bin/env python3
"""Fresh-process join-order work sweep with inert task-context distractors."""
from __future__ import annotations
import hashlib, importlib.util, itertools, json, os, random, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_DERIVED_JOIN_ORDER_CONTEXT_SCALE_V1_PREREG_20260929.md'
LOCK=ROOT/'evaluation/substrate_capability/task_derived_join_order_context_scale_v1_lock_20260929.json'
RAW=ROOT/'evaluation/reports/task_derived_join_order_context_scale_v1_raw_20260929.json'
OUT=ROOT/'evaluation/reports/task_derived_join_order_context_scale_v1_20260929.json'
ANALYZER=ROOT/'scripts/analyze_substrate_task_derived_join_order_context_scale_v1.py'
PREDECESSOR=ROOT/'scripts/substrate_common_ground_task_identity_replication_v1.py'
BASE=ROOT/'scripts/substrate_task_derived_join_order_v1.py'
FIXTURE=ROOT/'tests/fixtures/conversational_manifold/phase3_common_ground_stress.json'
SEED=ROOT/'seeds/conversation_discourse_state.json'
COUNTS=(0,8,32)
PERMS=tuple(itertools.permutations(range(4)))

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 paths=(str(PROTOCOL.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),
        str(PREDECESSOR.relative_to(ROOT)),str(BASE.relative_to(ROOT)),str(FIXTURE.relative_to(ROOT)),str(SEED.relative_to(ROOT)),
        'domains/discourse_state.py','substrate/world_adapter.py','runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs',
        'runners/dsl/src/scale_audit.rs','runners/dsl/python/substrate_rs/_native.build.json')
 return {'files':{p:sha(ROOT/p) for p in paths},'native_sha256':sha(Path(_native.__file__).resolve()),
         'native_path':str(Path(_native.__file__).resolve()),
         'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),
         'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def jobs(): return [(d,''.join(map(str,p)),r) for d in COUNTS for p in PERMS for r in range(3)]

def worker(decoy_count,label,rep):
 import importlib.util
 from substrate.world_adapter import WorldAdapter
 spec=importlib.util.spec_from_file_location('common_ground_replication_context_scale',PREDECESSOR)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 indices=tuple(int(x) for x in label)
 if len(indices)!=4 or set(indices)!=set(range(4)): raise ValueError(label)
 audit_rows=[];target={'index':None,'installed':None};instances=[];original_init=WorldAdapter.__init__
 def init_with_audit(self,*args,**kwargs):
  original_init(self,*args,**kwargs);inner=self.inner;s=self.s;instances.append(self)
  for i in range(decoy_count):
   state=s.add_node('DiscourseState',{'schema':'discourse_state.v1','conversation_id':f'context-scale-decoy-{i}'})
   origin=s.add_node('DiscourseEvent',{'schema':'discourse_event.v1','event_index':0,'kind':'request'})
   selection=s.add_node('DiscourseEvent',{'schema':'discourse_event.v1','event_index':1,'kind':'selection'})
   goal=s.add_node('Goal',{'schema':'communicative_goal_lifecycle.v1','lifecycle_status':'proposed','status':'proposed','context_scale_decoy':True})
   inner.add_edge_unchecked(state,'has_active_goal',goal,{})
   inner.add_edge_unchecked(goal,'originated_in',origin,{})
   inner.add_edge_unchecked(state,'has_event',selection,{})
  reset=inner.scale_audit_reset;enable=inner.scale_audit_set_enabled;snapshot=inner.scale_audit_snapshot
  def reset_both(): reset();inner.scale_audit_per_rule_reset()
  def enable_both(on): inner.scale_audit_set_per_rule_enabled(on);enable(on)
  def capture_snapshot():
   counters=snapshot();audit_rows.append({'per_rule':[list(x) for x in inner.scale_audit_per_rule_snapshot()],
      'clauses':[list(x) for x in inner.scale_audit_match_clause_snapshot()]});return counters
  inner.scale_audit_reset=reset_both;inner.scale_audit_set_enabled=enable_both;inner.scale_audit_snapshot=capture_snapshot
 WorldAdapter.__init__=init_with_audit
 def patch_rules(inner,arm):
  names={'discourse_goal_select','discourse_goal_execute','discourse_goal_resolve'};rows=inner.export_rules()
  targets=[(i,r) for i,r in enumerate(rows) if r.get('name') in names and r.get('active',True)]
  if len(targets)!=3: raise RuntimeError(f'expected three active lifecycle rules, found {len(targets)}')
  for i,_ in targets:
   if not inner.remove_rule(i): raise RuntimeError(f'failed to remove rule {i}')
  new=[]
  for _,prior in targets:
   r={k:v for k,v in prior.items() if k not in {'active','batch','content_hash','mutation_protected','revision','rule_uid'}}
   name=r['name'];r['name']=name+'_task_context_scale_v1'
   if name=='discourse_goal_select':r['match']=[prior['match'][i] for i in indices]
   idx=int(inner.add_rule(r));new.append(idx)
   if name=='discourse_goal_select': target['index']=idx;target['installed']=[list(e) for e in inner.export_rules()[idx]['match']]
  return new
 mod.patch_rules=patch_rules;task=mod.worker('explicit',rep)
 if len(audit_rows)!=len(task['checkpoints']): raise RuntimeError('audit/checkpoint cardinality mismatch')
 if len(instances)!=1: raise RuntimeError('expected one task adapter')
 decoy_goals=[n for n in instances[0].s.nodes('Goal') if instances[0].s.node(n)['attrs'].get('context_scale_decoy') is True]
 decoy_transition_count=sum(1 for n in decoy_goals if instances[0].s.node(n)['attrs'].get('lifecycle_status')!='proposed'
                            or instances[0].inner.neighbours(n,'transitioned_by'))
 return {'decoy_count':decoy_count,'permutation':label,'replicate':rep,'pid':os.getpid(),
         'target_rule_index':target['index'],'installed_match':target['installed'],
         'audit_rows':audit_rows,'task_run':task,'decoy_goal_count':len(decoy_goals),
         'decoy_transition_count':decoy_transition_count}

def main():
 if len(sys.argv)>1 and sys.argv[1]=='--worker':
  d=int(sys.argv[2]);label=sys.argv[3];rep=int(sys.argv[4]);before=fingerprint();w=worker(d,label,rep);after=fingerprint()
  print(json.dumps({'before':before,'after':after,'worker':w},sort_keys=True,default=str));return 0
 if sys.argv[1:]==['--lock']:
  f=fingerprint();LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':f},indent=2,sort_keys=True)+'\n');print(LOCK);return 0
 locked=fingerprint()
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked: raise SystemExit('missing or stale source/native lock')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')));env['PYTHONHASHSEED']='0'
 ordered=jobs();random.Random(20260929).shuffle(ordered);runs=[]
 for i,(d,label,rep) in enumerate(ordered,1):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(d),label,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True)
  if cp.returncode: runs.append({'worker_error':cp.stderr[-4000:],'decoy_count':d,'permutation':label,'replicate':rep})
  else: runs.append(json.loads(cp.stdout))
  print(f'worker {i}/{len(ordered)} D={d} order={label} rep={rep} rc={cp.returncode}',flush=True)
 post=fingerprint();RAW.write_text(json.dumps({'schema_version':1,'run_id':'task-derived-join-order-context-scale-v1-20260929',
    'locked_inputs':locked,'post_run_inputs':post,'runs':runs},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'worker_count':len(runs),'source_stable':post==locked,'raw':str(RAW.relative_to(ROOT))},indent=2))
 return 0 if post==locked and len(runs)==216 and all('worker_error' not in x for x in runs) else 1
if __name__=='__main__': raise SystemExit(main())
