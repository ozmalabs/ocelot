#!/usr/bin/env python3
"""Source-locked capability evaluation of graph-native blinded self-change selection."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_self_change_blind_baseline_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_SELF_CHANGE_BLIND_BASELINE_V1_PREREG_20261005.md'
SEED=ROOT/'seeds/self_change_reasoning.json';FIXTURE=ROOT/'tests/fixtures/self_change_blind_faults.json';SCHEMA=ROOT/'schemas/self_change_protocol.schema.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_self_change_blind_baseline_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_self_change_blind_baseline_v1_20261005.json'
SOURCES=('domains/engine_provenance.py','substrate/world_adapter.py','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json','tests/test_self_change_reasoning_migrated.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,SEED,FIXTURE,SCHEMA,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def attrs(agent,node):return agent.s.node(node)['attrs']
def outs(agent,node,edge):return list(agent.inner.neighbours(node,edge))
def run_case(case,worker_index):
 from substrate.world_adapter import WorldAdapter
 agent=WorldAdapter(seeds=());agent.inner.load_seed_manifest(json.loads(SEED.read_text()),agent.agent)
 opaque='case_'+hashlib.sha256(f'{worker_index}:{case["case_id"]}'.encode()).hexdigest()[:12]
 probe_attrs={'case_id':opaque,'target_uid':1001,'expected_revision':0,'baseline_hash':12345,'live_clause':{'type':'Lit','value':True},'change_opened':0,**case['signals']}
 probe_attrs.update({'threshold_adjustment_clause':{'type':'Gte','a':{'type':'Attr','node':{'type':'Var','name':'x'},'key':'signal'},'b':{'type':'Lit','value':1}},'guard_strengthening_clause':{'type':'Eq','a':{'type':'Attr','node':{'type':'Var','name':'x'},'key':'context_ok'},'b':{'type':'Lit','value':1}},'relation_addition_clause':{'type':'Lit','value':True},'effect_substitution_clause':[['set_attr','x','outcome','corrected']],'firing_budget_guard_clause':{'type':'Lt','a':{'type':'Attr','node':{'type':'Var','name':'x'},'key':'handled'},'b':{'type':'Lit','value':1}}})
 probe=agent.s.add_node('FaultProbe',probe_attrs);agent.inner.add_edge_unchecked(agent.agent,'observes_fault_probe',probe);agent.s.tick()
 changes=[n for n in agent.s.nodes(type='SelfChange') if attrs(agent,n).get('case_id')==opaque]
 if len(changes)!=1:raise RuntimeError(f'{opaque}: expected one SelfChange, got {len(changes)}')
 change=changes[0];patches=outs(agent,change,'has_patch');families=[attrs(agent,p).get('family') for p in patches]
 if not patches:raise RuntimeError(f'{opaque}: graph proposed no candidates')
 noop=agent.s.add_node('TrialEvidence',{'arm':'no_op','causal_gain':case['noop_gain']});placebo=agent.s.add_node('TrialEvidence',{'arm':'same_size_placebo','causal_gain':case['placebo_gain']})
 for edge,node_type in (('has_noop_control',noop),('has_placebo_control',placebo)):
  roots=outs(agent,change,edge)
  if len(roots)!=1:raise RuntimeError(f'{opaque}: missing {edge} root')
  agent.inner.add_edge_unchecked(roots[0],'has_evidence',node_type)
 scored=[]
 for patch in patches:
  family=attrs(agent,patch)['family'];gain=case['evidence'].get(family,0)
  evidence=agent.s.add_node('TrialEvidence',{'arm':'candidate','causal_gain':gain,'protected_regressions':0,'resource_cost':1,'resource_budget':3,'replications':3,'replicated_gain':gain})
  agent.inner.add_edge_unchecked(patch,'candidate_evidence',evidence)
  scored.append({'family':family,'gain':gain,'noop_gain':case['noop_gain'],'placebo_gain':case['placebo_gain'],'protected_regressions':0,'resource_cost':1,'resource_budget':3,'replications':3,'replicated_gain':gain,'mdl_cost':attrs(agent,patch).get('mdl_cost'),'blast_radius':attrs(agent,patch).get('blast_radius')})
 t0=time.perf_counter_ns();agent.s.tick();elapsed=time.perf_counter_ns()-t0
 selected=outs(agent,change,'selected_patch');closed=None
 if case['case_id']=='correlation_only_007':
  batch=agent.s.add_node('EvidenceBatch',{'status':'closed'});agent.inner.add_edge_unchecked(change,'evidence_batch',batch);agent.s.tick()
 aborts=outs(agent,change,'has_abort')
 selected_rows=[{'family':attrs(agent,p).get('family'),'proofs_passed':attrs(agent,p).get('proofs_passed'),'mdl_cost':attrs(agent,p).get('mdl_cost'),'status':attrs(agent,p).get('status')} for p in selected]
 admissible=[];control=max(case['noop_gain'],case['placebo_gain'])
 for row in scored:
  if (row['gain']>row['noop_gain']+5 and row['gain']>row['placebo_gain']+5
      and row['protected_regressions']==0 and row['resource_cost']<=row['resource_budget']
      and row['replications']>=2 and row['replicated_gain']>=5):admissible.append(row)
 return {'case_id':case['case_id'],'opaque_case_id':opaque,'signals':case['signals'],'candidate_families':families,'candidate_scores':scored,'control_gains':{'noop':case['noop_gain'],'placebo':case['placebo_gain']},'harness_admissible_families':[x['family'] for x in admissible],'selected':selected_rows,'abort':{'count':len(aborts),'reason':attrs(agent,aborts[0]).get('reason') if aborts else None,'status':attrs(agent,change).get('status')} if aborts else None,'selection_wall_ns':elapsed,'answer_key_passed':False}
def worker(i):
 locked=json.loads(LOCK.read_text())['sources'];before=frozen()
 if before!=locked:raise RuntimeError('source lock mismatch before worker')
 cases=json.loads(FIXTURE.read_text())['cases'];rows=[run_case(c,i) for c in cases];after=frozen()
 if after!=locked:raise RuntimeError('source lock mismatch after worker')
 return {'worker':i,'pid':os.getpid(),'sources_before':before,'sources_after':after,'rows':rows}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentSelfChangeBlindBaselineV1Lock','sources':frozen(),'workers':3,'case_count':7},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage --lock|--run|--worker N')
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source lock mismatch')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));workers=[]
 for i in range(3):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2500:]}')
  workers.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=json.loads(LOCK.read_text())['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentSelfChangeBlindBaselineV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
