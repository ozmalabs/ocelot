#!/usr/bin/env python3
"""Multi-family blind candidate tournament with complete lifecycle timings."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_blind_candidate_tournament_v2.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_CANDIDATE_TOURNAMENT_V2_PREREG_20261005.md'
FIXTURE=ROOT/'evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2_fixture_20261005.json'
SEED=ROOT/'seeds/self_change_reasoning.json';EDIT_OPS=ROOT/'domains/edit_ops.py'
BASELINE=ROOT/'evaluation/reports/thoughtexperiment_blind_candidate_tournament_v1_analysis_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v2_lock_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_blind_candidate_tournament_v2_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,FIXTURE,SEED,EDIT_OPS,BASELINE,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def lit(v):return {'type':'Lit','value':v}
def rule_for(case):
 return {'name':'blind_target_'+case['case_id'],'match':[['x','has_task','y'],['y','has_context','z']],
         'where':case['live_where'],'effects':[['set_attr_if_different','y','task_pass',{'__term__':lit(case['live_effect_value'])}]]}
def attrs(adapter,node):return adapter.s.node(node)['attrs']
def neighbours(adapter,node,edge):return list(adapter.inner.neighbours(node,edge))
def outputs(base,target_idx,candidate_rule,samples,observed_relations):
 branch=base.fork_shared_graph_pages_experiment();inner=branch._inner
 if candidate_rule is not None:
  if not inner.remove_rule(target_idx):raise RuntimeError('failed to remove live rule in branch')
  inner.add_rule(candidate_rule)
 predictions=[]
 for sample in samples:
  x=branch.add_node('TaskInput',{'sample_id':sample['id'],'signal':sample['signal']})
  y=branch.add_node('TaskOutput',{'sample_id':sample['id']});z=branch.add_node('TaskContext',{'sample_id':sample['id']})
  inner.add_edge_unchecked(x,'has_task',y);inner.add_edge_unchecked(y,'has_context',z)
  for i,relation in enumerate(observed_relations):
   node=branch.add_node('TaskRelation',{'sample_id':sample['id'],'relation_index':i})
   anchor={'x':x,'y':y,'z':z}.get(relation['anchor_var'])
   if anchor is None:raise RuntimeError('relation anchor is not a known task variable')
   if relation['direction']=='out':inner.add_edge_unchecked(anchor,relation['edge_type'],node)
   elif relation['direction']=='in':inner.add_edge_unchecked(node,relation['edge_type'],anchor)
   else:raise RuntimeError('unsupported relation direction')
  inner.run_rules_delta_report(30,False)
  graph=inner.graph_to_dict();record=next(n for n in graph['nodes'] if n['id']==y.value)
  predictions.append(bool(record['attrs'].get('task_pass',False)))
 return predictions
def score(predictions,samples):return 10*sum(pred==sample['expected'] for pred,sample in zip(predictions,samples))
def one(case):
 from substrate.world_adapter import WorldAdapter
 from domains.edit_ops import enumerate_single_edit_candidates
 adapter=WorldAdapter(seeds=());adapter.inner.load_seed_manifest(json.loads(SEED.read_text()),adapter.agent)
 live=rule_for(case);target_idx=adapter.inner.add_rule(live);meta=adapter.inner.rule_metadata(target_idx)
 t0=time.perf_counter_ns();candidates=enumerate_single_edit_candidates(live,max_candidates=128,observed_relations=case['observed_relations']);generation_ns=time.perf_counter_ns()-t0
 placebo=next((row for row in candidates if row['operator']=='drop_match_edge'),None)
 if placebo is None:raise RuntimeError('no one-edit placebo candidate in generated pool')
 t0=time.perf_counter_ns();noop_reps=[outputs(adapter.s,target_idx,None,case['train'],case['observed_relations']) for _ in range(3)];noop_ns=time.perf_counter_ns()-t0
 t0=time.perf_counter_ns();placebo_reps=[outputs(adapter.s,target_idx,placebo['rule'],case['train'],case['observed_relations']) for _ in range(3)];placebo_ns=time.perf_counter_ns()-t0
 if any(rep!=noop_reps[0] for rep in noop_reps) or any(rep!=placebo_reps[0] for rep in placebo_reps):raise RuntimeError('control replications differ')
 noop_gain=score(noop_reps[0],case['train']);placebo_gain=score(placebo_reps[0],case['train'])
 change=adapter.s.add_node('SelfChange',{'case_id':case['case_id'],'status':'diagnosing','selected':0})
 adapter.inner.add_edge_unchecked(adapter.agent,'considers_change',change)
 noop=adapter.s.add_node('ControlArm',{'kind':'no_op','required':1});placebo_arm=adapter.s.add_node('ControlArm',{'kind':'same_size_placebo','required':1})
 adapter.inner.add_edge_unchecked(change,'has_noop_control',noop);adapter.inner.add_edge_unchecked(change,'has_placebo_control',placebo_arm)
 adapter.inner.add_edge_unchecked(noop,'has_evidence',adapter.s.add_node('TrialEvidence',{'arm':'no_op','causal_gain':noop_gain}))
 adapter.inner.add_edge_unchecked(placebo_arm,'has_evidence',adapter.s.add_node('TrialEvidence',{'arm':'same_size_placebo','causal_gain':placebo_gain}))
 candidate_rows=[];t0=time.perf_counter_ns()
 for row in candidates:
  reps=[outputs(adapter.s,target_idx,row['rule'],case['train'],case['observed_relations']) for _ in range(3)]
  if any(rep!=reps[0] for rep in reps):raise RuntimeError('candidate replications differ')
  gain=score(reps[0],case['train']);field='effects' if row['rule'].get('effects')!=live.get('effects') else 'match' if row['rule'].get('match')!=live.get('match') else 'where'
  clause=row['rule'].get(field)
  patch=adapter.s.add_node('RulePatch',{'candidate_id':row['candidate_id'],'case_id':case['case_id'],'field':field,
   'proposed_clause':clause,'candidate_rule_json':json.dumps(row['rule'],sort_keys=True,separators=(',',':')),
   'mdl_cost':1,'blast_radius':1,'status':'candidate','selected':0,'proofs_passed':0,'trial_complete':0,
   'obligations_minted':0,'resource_cost':1,'resource_budget':3})
  evidence=adapter.s.add_node('TrialEvidence',{'arm':'candidate','causal_gain':gain,'protected_regressions':0,
   'resource_cost':1,'resource_budget':3,'replications':3,'replicated_gain':gain})
  adapter.inner.add_edge_unchecked(change,'has_patch',patch);adapter.inner.add_edge_unchecked(patch,'candidate_evidence',evidence)
  candidate_rows.append({'candidate_id':row['candidate_id'],'operator_hidden':row['operator'],'outputs':reps[0],'gain':gain})
 candidate_ns=time.perf_counter_ns()-t0
 t0=time.perf_counter_ns();adapter.s.tick();selection_ns=time.perf_counter_ns()-t0
 selected=neighbours(adapter,change,'selected_patch');selected_id=attrs(adapter,selected[0]).get('candidate_id') if selected else None
 revision_after_rehearsal=adapter.inner.rule_metadata(target_idx)['revision'];canary_rows=[];final_rows=[];commits=[];aborts=[]
 canary_ns=commit_ns=final_ns=abort_ns=0
 if selected:
  patch=selected[0];pa=attrs(adapter,patch);chosen=json.loads(pa['candidate_rule_json'])
  adapter.s.set_attr(patch,'target_uid',meta['rule_uid']);adapter.s.set_attr(patch,'expected_revision',meta['revision']);adapter.s.set_attr(patch,'expected_content_hash',meta['content_hash'])
  t0=time.perf_counter_ns();canary_reps=[outputs(adapter.s,target_idx,chosen,case['canary'],case['observed_relations']) for _ in range(3)];canary_ns=time.perf_counter_ns()-t0
  if any(rep!=canary_reps[0] for rep in canary_reps):raise RuntimeError('canary replications differ')
  canary_rows=canary_reps[0];canary_gain=score(canary_rows,case['canary']);correct=all(p==s['expected'] for p,s in zip(canary_rows,case['canary']))
  canary=neighbours(adapter,patch,'has_canary')[0];cev=adapter.s.add_node('CanaryEvidence',{'replicated_gain':canary_gain,'protected_regressions':0 if correct else 1,'replications':3})
  adapter.inner.add_edge_unchecked(canary,'has_canary_evidence',cev)
  t0=time.perf_counter_ns();adapter.s.tick();commit_ns=time.perf_counter_ns()-t0;commits=neighbours(adapter,change,'has_commit')
  if commits:
   t0=time.perf_counter_ns();final_rows=outputs(adapter.s,target_idx,None,case['final'],case['observed_relations']);final_ns=time.perf_counter_ns()-t0
 else:
  batch=adapter.s.add_node('EvidenceBatch',{'status':'closed'});adapter.inner.add_edge_unchecked(change,'evidence_batch',batch)
  t0=time.perf_counter_ns();adapter.s.tick();abort_ns=time.perf_counter_ns()-t0;aborts=neighbours(adapter,change,'has_abort')
 final_meta=adapter.inner.rule_metadata(target_idx)
 return {'case_id':case['case_id'],'candidate_count':len(candidates),'candidates':candidate_rows,
  'noop_outputs':noop_reps[0],'placebo_outputs':placebo_reps[0],'noop_gain':noop_gain,'placebo_gain':placebo_gain,
  'selected_candidate_id':selected_id,'selected_count':len(selected),'revision_after_rehearsal':revision_after_rehearsal,
  'canary_outputs':canary_rows,'commit_count':len(commits),'abort_count':len(aborts),
  'abort_reason':attrs(adapter,aborts[0]).get('reason') if aborts else None,'final_outputs':final_rows,
  'target_revision_initial':meta['revision'],'revision_after_terminal':final_meta['revision'],
  'patch_status':attrs(adapter,selected[0]).get('status') if selected else None,
  'patch_reason':attrs(adapter,selected[0]).get('reason') if selected else None,'graph_status':attrs(adapter,change).get('status'),
  'timing_ns':{'candidate_generation':generation_ns,'noop_rehearsal_3x':noop_ns,'placebo_rehearsal_3x':placebo_ns,
   'candidate_rehearsal_pool':candidate_ns,'graph_selection':selection_ns,'canary_rehearsal_3x':canary_ns,
   'canary_commit_tick':commit_ns,'final_verification':final_ns,'abort_close_tick':abort_ns}}
def worker(index):
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise RuntimeError('source mismatch before worker')
 cases=json.loads(FIXTURE.read_text())['cases'];rows=[one(case) for case in cases];after=frozen()
 if after!=lock['sources']:raise RuntimeError('source drift during worker')
 return {'worker':index,'pid':os.getpid(),'sources_before':before,'sources_after':after,'cases':rows}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing capture')
  cases=json.loads(FIXTURE.read_text())['cases']
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentBlindCandidateTournamentV2Lock','sources':frozen(),'workers':3,
   'case_count':len(cases),'replications':3,'candidate_cap':128,
   'splits':{c['case_id']:{'train':[s['id'] for s in c['train']],'canary':[s['id'] for s in c['canary']],'final':[s['id'] for s in c['final']]} for c in cases}},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage --lock|--run|--worker N')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source lock mismatch')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));workers=[]
 for i in range(lock['workers']):
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
  if proc.returncode:raise RuntimeError(f'worker {i}: {proc.stderr[-3000:]}')
  workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentBlindCandidateTournamentV2','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
