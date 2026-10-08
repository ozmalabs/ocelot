#!/usr/bin/env python3
"""Blind structural candidate generation, measured rehearsal, graph selection, and CAS."""
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_blind_candidate_tournament_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_BLIND_CANDIDATE_TOURNAMENT_V1_PREREG_20261005.md'
SEED=ROOT/'seeds/self_change_reasoning.json';EDIT_OPS=ROOT/'domains/edit_ops.py'
BASELINE=ROOT/'evaluation/reports/blind_structural_repair_relation_evidence_v1_analysis_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_blind_candidate_tournament_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_blind_candidate_tournament_v1_20261005.json'
SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json')
CASES=(
 {'case_id':'opaque_repair_needed','live_effect_value':False,'oracle_value':True,'train_ids':[1,2],'canary_ids':[10,11,12],'final_ids':[20,21]},
 {'case_id':'opaque_no_repair','live_effect_value':True,'oracle_value':True,'train_ids':[3,4],'canary_ids':[13,14,15],'final_ids':[22,23]},
)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 files=(RUNNER,ANALYZER,PROTOCOL,SEED,EDIT_OPS,BASELINE,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve()
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in files},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def lit(v):return {'type':'Lit','value':v}
def base_rule(value,name='blind_target'):
 return {'name':name,'match':[['x','has_task','y'],['y','has_context','z']],
         'where':lit(True),'effects':[['set_attr_if_different','y','task_pass',{'__term__':lit(value)}]]}
def attrs(adapter,node):return adapter.s.node(node)['attrs']
def neighbours(adapter,node,edge):return list(adapter.inner.neighbours(node,edge))
def outputs(base,target_idx,rule,ids):
 branch=base.fork_shared_graph_pages_experiment();inner=branch._inner
 if rule is not None:
  if not inner.remove_rule(target_idx):raise RuntimeError('failed to remove base rule in branch')
  inner.add_rule(rule)
 results=[]
 for sample_id in ids:
  x=branch.add_node('TaskInput',{'sample_id':sample_id});y=branch.add_node('TaskOutput',{'sample_id':sample_id});z=branch.add_node('TaskContext',{'sample_id':sample_id})
  inner.add_edge_unchecked(x,'has_task',y);inner.add_edge_unchecked(y,'has_context',z)
  inner.run_rules_delta_report(30,False)
  graph=inner.graph_to_dict();record=next(n for n in graph['nodes'] if n['id']==y.value)
  results.append(bool(record['attrs'].get('task_pass',False)))
 return results
def score(rows,expected):return 10*sum(a==expected for a in rows)
def one(case):
 from substrate.world_adapter import WorldAdapter
 from domains.edit_ops import enumerate_single_edit_candidates
 adapter=WorldAdapter(seeds=());adapter.inner.load_seed_manifest(json.loads(SEED.read_text()),adapter.agent)
 target_idx=adapter.inner.add_rule(base_rule(case['live_effect_value']))
 meta=adapter.inner.rule_metadata(target_idx)
 live=base_rule(case['live_effect_value']);candidates=enumerate_single_edit_candidates(live,max_candidates=128)
 # Candidate generation sees only the live rule; candidate IDs are the only
 # identities passed to the graph selector. No operator/family labels enter.
 placebo=next((row for row in candidates if row['operator']=='drop_match_edge'),None)
 if placebo is None:raise RuntimeError('no same-size one-edit placebo in candidate pool')
 train_ids=case['train_ids'];truth=case['oracle_value'];timing={}
 t0=time.perf_counter_ns();noop_runs=[outputs(adapter.s,target_idx,None,train_ids) for _ in range(3)];noop_wall=time.perf_counter_ns()-t0
 placebo_runs=[outputs(adapter.s,target_idx,placebo['rule'],train_ids) for _ in range(3)]
 placebo_wall=time.perf_counter_ns()-t0-noop_wall
 noop_gain=score(noop_runs[0],truth);placebo_gain=score(placebo_runs[0],truth)
 if not all(row==noop_runs[0] for row in noop_runs) or not all(row==placebo_runs[0] for row in placebo_runs):raise RuntimeError('control replication disagreement')
 change=adapter.s.add_node('SelfChange',{'case_id':case['case_id'],'status':'diagnosing','selected':0})
 adapter.inner.add_edge_unchecked(adapter.agent,'considers_change',change)
 noop=adapter.s.add_node('ControlArm',{'kind':'no_op','required':1});placebo_arm=adapter.s.add_node('ControlArm',{'kind':'same_size_placebo','required':1})
 adapter.inner.add_edge_unchecked(change,'has_noop_control',noop);adapter.inner.add_edge_unchecked(change,'has_placebo_control',placebo_arm)
 ne=adapter.s.add_node('TrialEvidence',{'arm':'no_op','causal_gain':noop_gain});pe=adapter.s.add_node('TrialEvidence',{'arm':'same_size_placebo','causal_gain':placebo_gain})
 adapter.inner.add_edge_unchecked(noop,'has_evidence',ne);adapter.inner.add_edge_unchecked(placebo_arm,'has_evidence',pe)
 patch_by_id={};trial_rows=[];t0=time.perf_counter_ns()
 for row in candidates:
  replications=[outputs(adapter.s,target_idx,row['rule'],train_ids) for _ in range(3)]
  if not all(rep==replications[0] for rep in replications):raise RuntimeError('candidate replication disagreement')
  gain=score(replications[0],truth)
  patch=adapter.s.add_node('RulePatch',{'candidate_id':row['candidate_id'],'case_id':case['case_id'],
      'field':'effects' if row['rule'].get('effects')!=live.get('effects') else 'match' if row['rule'].get('match')!=live.get('match') else 'where',
      'proposed_clause':row['rule'].get('effects') if row['rule'].get('effects')!=live.get('effects') else row['rule'].get('match') if row['rule'].get('match')!=live.get('match') else row['rule'].get('where'),
      'candidate_rule_json':json.dumps(row['rule'],sort_keys=True,separators=(',',':')),
      'mdl_cost':1,'blast_radius':1,'status':'candidate','selected':0,'proofs_passed':0,
      'trial_complete':0,'obligations_minted':0,'resource_cost':1,'resource_budget':3})
  adapter.inner.add_edge_unchecked(change,'has_patch',patch);adapter.inner.add_edge_unchecked(patch,'candidate_evidence',adapter.s.add_node('TrialEvidence',{
      'arm':'candidate','causal_gain':gain,'protected_regressions':0,'resource_cost':1,'resource_budget':3,
      'replications':3,'replicated_gain':gain}))
  patch_by_id[row['candidate_id']]=(patch,row)
  trial_rows.append({'candidate_id':row['candidate_id'],'outputs':replications[0],'gain':gain,'operator_hidden':row['operator']})
 rehearsal_wall=time.perf_counter_ns()-t0
 t0=time.perf_counter_ns();adapter.s.tick();selection_wall=time.perf_counter_ns()-t0
 selected=neighbours(adapter,change,'selected_patch');selected_id=attrs(adapter,selected[0]).get('candidate_id') if selected else None
 revision_after_rehearsal=adapter.inner.rule_metadata(target_idx)['revision']
 aborts=[];commits=[];canary_rows=[];final_rows=[]
 if selected:
  patch=selected[0];selected_attrs=attrs(adapter,patch);selected_rule=json.loads(selected_attrs['candidate_rule_json'])
  # The target UID/revision/hash are attached only after the graph selection.
  adapter.s.set_attr(patch,'target_uid',meta['rule_uid']);adapter.s.set_attr(patch,'expected_revision',meta['revision']);adapter.s.set_attr(patch,'expected_content_hash',meta['content_hash'])
  canary_runs=[outputs(adapter.s,target_idx,selected_rule,case['canary_ids']) for _ in range(3)]
  if not all(row==canary_runs[0] for row in canary_runs):raise RuntimeError('canary replication disagreement')
  canary_gain=score(canary_runs[0],truth);canary_rows=canary_runs[0]
  canary=neighbours(adapter,patch,'has_canary')[0]
  cev=adapter.s.add_node('CanaryEvidence',{'replicated_gain':canary_gain,'protected_regressions':0 if canary_gain==30 else 1,'replications':3})
  adapter.inner.add_edge_unchecked(canary,'has_canary_evidence',cev);adapter.s.tick()
  commits=neighbours(adapter,change,'has_commit')
  if commits:
   final_rows=outputs(adapter.s,target_idx,None,case['final_ids'])
 else:
  batch=adapter.s.add_node('EvidenceBatch',{'status':'closed'});adapter.inner.add_edge_unchecked(change,'evidence_batch',batch);adapter.s.tick()
  aborts=neighbours(adapter,change,'has_abort')
 after=adapter.inner.rule_metadata(target_idx)
 return {'case_id':case['case_id'],'target_rule_uid_withheld_until_selection':True,
   'candidate_count':len(candidates),'candidates':trial_rows,'noop_outputs':noop_runs[0],
   'placebo_outputs':placebo_runs[0],'noop_gain':noop_gain,'placebo_gain':placebo_gain,
   'selected_candidate_id':selected_id,'selected_count':len(selected),'revision_after_rehearsal':revision_after_rehearsal,
   'canary_outputs':canary_rows,'commit_count':len(commits),'abort_count':len(aborts),
   'abort_reason':attrs(adapter,aborts[0]).get('reason') if aborts else None,
   'final_outputs':final_rows,'revision_after_terminal':after['revision'],
   'target_revision_initial':meta['revision'],'patch_status':attrs(adapter,selected[0]).get('status') if selected else None,
   'patch_reason':attrs(adapter,selected[0]).get('reason') if selected else None,
   'graph_status':attrs(adapter,change).get('status'),
   'timing_ns':{'noop_rehearsal_3x':noop_wall,'placebo_rehearsal_3x':placebo_wall,
                'candidate_rehearsal':rehearsal_wall,'graph_selection':selection_wall}}
def worker(i):
 lock=json.loads(LOCK.read_text());before=frozen()
 if before!=lock['sources']:raise RuntimeError('source lock mismatch before worker')
 rows=[one(case) for case in CASES];after=frozen()
 if after!=lock['sources']:raise RuntimeError('source lock mismatch after worker')
 return {'worker':i,'pid':os.getpid(),'sources_before':before,'sources_after':after,'cases':rows}
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing overwrite')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentBlindCandidateTournamentV1Lock','sources':frozen(),
   'workers':3,'case_count':len(CASES),'replications':3,'candidate_cap':128,
   'case_inputs':[{'case_id':c['case_id'],'train_ids':c['train_ids'],'canary_ids':c['canary_ids'],'final_ids':c['final_ids']} for c in CASES]},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,separators=(',',':')));return 0
 if sys.argv[1:]!=['--run']:raise SystemExit('usage --lock|--run|--worker N')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source lock mismatch')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT/'runners/dsl/python'),str(ROOT)));workers=[]
 for i in range(lock['workers']):
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
  if proc.returncode:raise RuntimeError(f'worker {i}: {proc.stderr[-3000:]}')
  workers.append(json.loads(proc.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during run')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentBlindCandidateTournamentV1','lock_sha256':sha(LOCK),'host':platform.platform(),'workers':workers},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
