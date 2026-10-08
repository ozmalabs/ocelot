#!/usr/bin/env python3
"""Prototype end-to-end graph-native patch generation, rehearsal, canary, and commit."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
SEED=ROOT/'seeds/self_change_reasoning.json'
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_self_change_end_to_end_v1.py';PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SELF_CHANGE_END_TO_END_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_self_change_end_to_end_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_self_change_end_to_end_v1_20261005.json'
SOURCES=('substrate/world_adapter.py','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,SEED,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
LIT_FALSE={'type':'Lit','value':False}
PLACEBO={'type':'Lt','a':{'type':'Attr','node':{'type':'Var','name':'x'},'key':'signal'},'b':{'type':'Lit','value':0}}
def node_attrs(s,nid):
 g=s._inner.graph_to_dict();return next(n['attrs'] for n in g['nodes'] if n['id']==nid.value)
def run_inputs(base,where,signals,patch_target=None,backend='shared_graph_pages'):
 b=getattr(base,f'fork_{backend}_experiment')();meta=b._inner.rule_metadata(patch_target['rule_idx'])
 rec=None
 if where is not None:rec=b._inner.apply_rule_patch(meta['rule_uid'],meta['revision'],meta['content_hash'],'where',where)
 outputs=[]
 for value in signals:
  x=b.add_node('TaskInput',{'signal':value});y=b.add_node('TaskOutput',{});b.add_edge_unchecked(x,'has_task',y);b._inner.run_rules_delta_report(30,False)
  outputs.append(bool(node_attrs(b,y).get('task_pass',False)))
 return outputs,rec

def one(backend='shared_graph_pages'):
 from substrate.world_adapter import WorldAdapter
 a=WorldAdapter(seeds=());a.inner.load_seed_manifest(json.loads(SEED.read_text()),a.agent)
 idx=a.inner.add_rule({'name':'measured_target','match':[['x','has_task','y']],'where':LIT_FALSE,'effects':[['set_attr_if_different','y','task_pass',True]]})
 meta=a.inner.rule_metadata(idx)
 probe_attrs={'case_id':'opaque_case_4b71','target_uid':0,'expected_revision':0,'baseline_hash':0,'live_clause':LIT_FALSE,'false_negative':1,'threshold_sensitivity':1,'threshold_adjustment_clause':{'type':'Gte','a':{'type':'Attr','node':{'type':'Var','name':'x'},'key':'signal'},'b':{'type':'Lit','value':1}},'guard_strengthening_clause':{'type':'Eq','a':{'type':'Attr','node':{'type':'Var','name':'x'},'key':'context_ok'},'b':{'type':'Lit','value':1}},'relation_addition_clause':LIT_FALSE,'effect_substitution_clause':[['set_attr','y','task_pass',True]],'firing_budget_guard_clause':PLACEBO}
 probe=a.s.add_node('FaultProbe',probe_attrs);a.inner.add_edge_unchecked(a.agent,'observes_fault_probe',probe);a.s.tick()
 changes=[n for n in a.s.nodes(type='SelfChange') if a.s.node(n)['attrs'].get('case_id')=='opaque_case_4b71'];change=changes[0]
 patches=list(a.inner.neighbours(change,'has_patch'));pa=patches[0];pattrs=a.s.node(pa)['attrs'];clause=pattrs['proposed_clause']
 t0=time.perf_counter_ns();candidate,creceipt=run_inputs(a.s,clause,[1,0],{'rule_idx':idx},backend);noop,_=run_inputs(a.s,None,[1,0],{'rule_idx':idx},backend);placebo,_=run_inputs(a.s,PLACEBO,[1,0],{'rule_idx':idx},backend);training_rehearsal_ns=time.perf_counter_ns()-t0
 revision_after_rehearsal=a.inner.rule_metadata(idx)['revision']
 gain=10 if candidate==[True,False] else 0;noop_gain=10 if noop==[True,False] else 0;placebo_gain=10 if placebo==[True,False] else 0
 for edge,kind,g in (('has_noop_control','no_op',noop_gain),('has_placebo_control','same_size_placebo',placebo_gain)):
  root=list(a.inner.neighbours(change,edge))[0];ev=a.s.add_node('TrialEvidence',{'arm':kind,'causal_gain':g});a.inner.add_edge_unchecked(root,'has_evidence',ev)
 evidence=a.s.add_node('TrialEvidence',{'arm':'candidate','causal_gain':gain,'protected_regressions':0,'resource_cost':1,'resource_budget':3,'replications':3,'replicated_gain':gain});a.inner.add_edge_unchecked(pa,'candidate_evidence',evidence);t0=time.perf_counter_ns();a.s.tick();selection_tick_ns=time.perf_counter_ns()-t0
 selected=list(a.inner.neighbours(change,'selected_patch'));canary=None
 if selected:
  pa=selected[0];attrs=a.s.node(pa)['attrs'];a.s.set_attr(pa,'target_uid',meta['rule_uid']);a.s.set_attr(pa,'expected_revision',meta['revision']);a.s.set_attr(pa,'expected_content_hash',meta['content_hash'])
  canary=list(a.inner.neighbours(pa,'has_canary'))[0]
  t0=time.perf_counter_ns();holdout,_=run_inputs(a.s,attrs['proposed_clause'],[2,3,4,-1,-2],{'rule_idx':idx},backend);canary_rehearsal_ns=time.perf_counter_ns()-t0
  hgain=10 if holdout==[True,True,True,False,False] else 0
  cev=a.s.add_node('CanaryEvidence',{'replicated_gain':hgain,'protected_regressions':0 if hgain else 1,'replications':3});a.inner.add_edge_unchecked(canary,'has_canary_evidence',cev);t0=time.perf_counter_ns();a.s.tick();commit_tick_ns=time.perf_counter_ns()-t0
 else:holdout=[]
 final_meta=a.inner.rule_metadata(idx);commits=list(a.inner.neighbours(change,'has_commit'))
 t0=time.perf_counter_ns();final_outputs,_=run_inputs(a.s,None,[5,-3],{'rule_idx':idx},backend);final_verification_ns=time.perf_counter_ns()-t0
 return {'backend':backend,'candidate_families':[a.s.node(p)['attrs'].get('family') for p in patches],'proposed_clause':clause,'faultprobe_target_uid':probe_attrs['target_uid'],'target_uid_bound_after_selection':meta['rule_uid'] if selected else None,'training_outputs':candidate,'no_op_outputs':noop,'placebo_outputs':placebo,'training_gain':gain,'selected_count':len(selected),'selected_family':a.s.node(pa)['attrs'].get('family') if selected else None,'canary_outputs':holdout,'commits':len(commits),'target_revision_after_rehearsal':revision_after_rehearsal,'target_revision_after_commit':final_meta['revision'],'committed_patch_status':a.s.node(pa)['attrs'].get('status') if selected else None,'final_outputs':final_outputs,'final_correct':final_outputs==[True,False],'candidate_branch_patch_receipt':creceipt,'graph_status':a.s.node(change)['attrs'].get('status'),'timing_ns':{'training_rehearsal_candidate_noop_placebo':training_rehearsal_ns,'selection_tick':selection_tick_ns,'canary_rehearsal':canary_rehearsal_ns if selected else 0,'commit_tick':commit_tick_ns if selected else 0,'final_verification':final_verification_ns}}
def worker(i):
 lock=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=lock:raise RuntimeError('source lock mismatch before lifecycle')
 order=('full_copy','shared_graph_pages') if i%2==0 else ('shared_graph_pages','full_copy')
 results=[one(backend) for backend in order];after=frozen()
 if after!=lock:raise RuntimeError('source lock mismatch after lifecycle')
 return {'worker':i,'pid':os.getpid(),'order':order,'sources_before':before,'sources_after':after,'results':results}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentSelfChangeEndToEndV1Lock','sources':frozen(),'workers':3,'branch_backends':['full_copy','shared_graph_pages'],'task_split':{'train':[1,0],'canary':[2,3,4,-1,-2],'final':[5,-3]}},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage --lock|--run|--worker N')
 lock=json.loads(LOCK.read_text());
 if frozen()!=lock['sources']:raise SystemExit('source lock mismatch')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));rows=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2500:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during run')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentSelfChangeEndToEndV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
