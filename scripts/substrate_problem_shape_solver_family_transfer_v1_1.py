#!/usr/bin/env python3
"""Source-locked ProblemShape transfer through real reasoning bridge Goals."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_SOLVER_FAMILY_TRANSFER_V1_PREREG_20260927.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_SOLVER_FAMILY_TRANSFER_V1_1_AMENDMENT_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_solver_family_transfer_v1_1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/problem_shape_solver_family_transfer_v1_1_20260927.json'
ANALYZER=ROOT/'scripts/analyze_substrate_problem_shape_solver_family_transfer_v1_1.py'
HELPER=ROOT/'scripts/measurement_provenance.py'
RESIDENTS=[0,1,2]
WORKERS=[0,1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def tree_hashes(folder,suffixes=None):
 out={}
 for p in sorted(folder.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and (suffixes is None or p.suffix in suffixes):out[p.relative_to(ROOT).as_posix()]=sha(p)
 return out
def inputs():
 from scripts.measurement_provenance import lock_files
 from substrate_rs import _native
 assets={'domains':tree_hashes(ROOT/'domains',{'.py'}),'substrate':tree_hashes(ROOT/'substrate',{'.py'}),'native_python':tree_hashes(ROOT/'runners/dsl/python',{'.py'}),'rust_source':tree_hashes(ROOT/'runners/dsl/src',{'.rs'}),'worlds':tree_hashes(ROOT/'worlds',{'.py'}),'scripts':tree_hashes(ROOT/'scripts',{'.py'}),'seeds':tree_hashes(ROOT/'seeds',{'.json'}),'data/slabs':tree_hashes(ROOT/'data/slabs')}
 explicit=[PROTOCOL,AMENDMENT,__file__,ANALYZER,HELPER,Path(_native.__file__).resolve(),ROOT/'runners/dsl/python/substrate_rs/_native.build.json',ROOT/'runners/dsl/Cargo.toml',ROOT/'runners/dsl/Cargo.lock']
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'helper_sha256':sha(HELPER),'source_commit':os.environ.get('OCEL0_SOURCE_REV','unrecorded'),'immutable_snapshot':os.environ.get('OCEL0_IMMUTABLE_SNAPSHOT')=='1','explicit_files':lock_files(explicit,root=ROOT),'runtime_tree_sha256':assets,'resident_indices':RESIDENTS}
def rss_bytes():
 value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 return int(value*(1024 if sys.platform.startswith('linux') else 1))
def pump(adapter,goal,max_iters=48):
 for i in range(max_iters):
  adapter.fire_reflexes();adapter.inner.run_rules()
  status=adapter.s.node(goal)['attrs'].get('status')
  if status in ('resolved','walled'):return {'status':status,'iterations':i+1}
 raise RuntimeError(f'goal {goal} unresolved after {max_iters} driver rounds')
def worker(rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from substrate_rs import _native
 from domains import solver_dispatch as sd,problem_shape as ps
 from worlds import bigville_can_beliefs as bcb
 from scripts.substrate_problem_shape_induction_economics import observe_measure
 start_wall,start_cpu=time.perf_counter_ns(),time.process_time_ns()
 adapter=WorldAdapter(seeds=());boot=load_all_seeds(adapter)
 adapter.register_reflex_response('question_pursue',lambda ag:ag._question_pursue_advance())
 adapter.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
 boot_wall=time.perf_counter_ns()-start_wall;boot_cpu=time.process_time_ns()-start_cpu
 native=adapter.inner;sub=adapter.s;Native=_native.Substrate;bcb.install_productions(native)
 residents=json.loads((ROOT/'seeds/bigville_cast100.json').read_text())['residents']
 mts=[];resident_names=[];can_goals=[]
 for index in RESIDENTS:
  built=bcb.build_resident_can_mt(native,residents[index]);bcb.apply_scenario_evidence(native,built['concepts'])
  native.set_attr(built['mt_node'],'discrete_mode','3state');native.set_attr(built['mt_node'],'can_tick',0)
  exact=sd.mint_solve_can_exact_goal(adapter,built['mt_node']);resolved=pump(adapter,exact)
  can_goals.append({'goal_id':int(exact.value),'status':resolved['status'],'resolver':[sub.node(n)['attrs'].get('name') for n in native.neighbours(exact,'resolve_with')],'target_mt':int(built['mt_node'].value),'answer':sub.node(exact)['attrs'].get('answer')})
  mts.append(built['mt_node']);resident_names.append(sub.node(built['resident_node'])['attrs'].get('name',''))
 Native.scale_audit_set_enabled(True);Native.scale_audit_set_per_rule_enabled(True)
 observations=[];goals=[]
 # Positive control for the seed's existing shape.
 seeded=sd.mint_solve_can_exact_goal(adapter,mts[0]);status=pump(adapter,seeded)
 goals.append({'label':'seeded_can_exact','goal_id':int(seeded.value),'status':status['status'],'resolver':[sub.node(n)['attrs'].get('name') for n in native.neighbours(seeded,'resolve_with')],'answer':sub.node(seeded)['attrs'].get('answer')})
 row=observe_measure(adapter,seeded,'seeded_can_exact',Native);observations.append(row)
 # Two recurrence examples and one held-out resident network.
 bridge_ids=[]
 for i,mt in enumerate(mts):
  goal=sd.mint_solve_reasoning_bridge_goal(adapter,'can_to_deduction',mt=mt)
  status=pump(adapter,goal);ga=dict(sub.node(goal)['attrs'])
  goals.append({'label':f'bridge_can_to_deduction_{i+1}','goal_id':int(goal.value),'status':status['status'],'resolver':[sub.node(n)['attrs'].get('name') for n in native.neighbours(goal,'resolve_with')],'target_mt':int(mt.value),'answer':ga.get('answer')})
  bridge_ids.append(int(goal.value));observations.append(observe_measure(adapter,goal,f'bridge_can_to_deduction_{i+1}',Native))
 # Valid opposite-direction control on the first resident's actual name.
 entity=str(resident_names[0]).lower().replace(' ','_')
 opposite=sd.mint_solve_reasoning_bridge_goal(adapter,'deduction_to_can',entity=entity,attr='trust_mayor',positive=True)
 status=pump(adapter,opposite);goals.append({'label':'bridge_deduction_to_can_control','goal_id':int(opposite.value),'status':status['status'],'resolver':[sub.node(n)['attrs'].get('name') for n in native.neighbours(opposite,'resolve_with')],'entity':entity,'answer':sub.node(opposite)['attrs'].get('answer')})
 observations.append(observe_measure(adapter,opposite,'bridge_deduction_to_can_control',Native))
 Native.scale_audit_set_enabled(False);Native.scale_audit_set_per_rule_enabled(False)
 final_obs=[]
 for row in observations:
  oid=row['observation_id'];attrs=sub.node(_native.NodeID(oid))['attrs'] if oid is not None else {}
  final_obs.append({'label':row['label'],'status_initial':row['observation_status_initial'],'covered_initial':row['covered_by_initial'],'status_final':attrs.get('status'),'covered_final':attrs.get('covered_by'),'key':attrs.get('key'),'mint_count_delta':row['mint_count_delta'],'candidate_pairs':row['problem_shape_candidate_pairs'],'term_evaluations':row['problem_shape_term_evaluations'],'wall_time_ns':row['wall_time_ns'],'cpu_time_ns':row['cpu_time_ns']})
 return {'replicate':rep,'pid':os.getpid(),'seed_boot':{'loaded':boot.get('loaded'),'total':boot.get('total'),'failed':boot.get('failed',[]),'order':boot.get('order')},'boot_wall_ns':boot_wall,'boot_cpu_ns':boot_cpu,'can_exact_preparations':can_goals,'goals':goals,'observations':final_obs,'new_shapes':[dict(sub.node(n)['attrs']) for n in sub.nodes('ProblemShape') if float(sub.node(n)['attrs'].get('minted',0.0))>0],'peak_rss_bytes':rss_bytes(),'environment':{'python':sys.version,'platform':platform.platform()}}
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  rep=int(os.environ['OCEL0_PS_TRANSFER_REP'])
  if os.environ.get('OCEL0_IMMUTABLE_SNAPSHOT')=='1':
   before=json.loads(LOCK.read_text())['locked_inputs'];r=worker(rep);after=before;stable=True
  else:before=inputs();r=worker(rep);after=inputs();stable=before==after
  r.update({'locked_inputs_before':before,'locked_inputs_after':after,'source_stable':stable,'immutable_snapshot_worker':os.environ.get('OCEL0_IMMUTABLE_SNAPSHOT')=='1'});print(json.dumps(r,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale solver-family transfer lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT/"runners/dsl/python"}:{ROOT/"scripts"}','OZMA_SEED_PERSIST_DISABLED':'1'}
 from domains.engine_provenance import build_is_stale
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('native build stale: '+str(stale))
 runs=[]
 for rep in WORKERS:
  e=env.copy();e.update(OCEL0_PS_TRANSFER_REP=str(rep));p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=e,text=True,capture_output=True,timeout=600)
  try:r=json.loads(p.stdout)
  except Exception:r={'replicate':rep,'worker_error':p.stderr or p.stdout}
  r.update({'worker_returncode':p.returncode,'worker_stderr':p.stderr});runs.append(r);print(f'completed=rep{rep} rc={p.returncode}',file=sys.stderr,flush=True)
 post=inputs();checks={'two_workers':len(runs)==2,'unique_pids':len({r.get('pid') for r in runs})==2,'parent_lock_stable':post==locked,'worker_lock_stable':all(r.get('source_stable') and r.get('locked_inputs_before')==locked==r.get('locked_inputs_after') for r in runs),'immutable_snapshot':all(r.get('immutable_snapshot_worker') for r in runs),'full_boot':all(r.get('seed_boot',{}).get('loaded',0)>0 for r in runs),'goal_rows':all(len(r.get('goals',[]))==5 and len(r.get('can_exact_preparations',[]))==3 for r in runs),'observation_rows':all(len(r.get('observations',[]))==5 for r in runs)}
 report={'schema_version':1,'run_id':'problem-shape-solver-family-transfer-v1.1-20260927','locked_inputs':locked,'post_run_inputs':post,'integrity_checks':checks,'integrity_pass':all(checks.values()),'runs':runs,'claim_boundary':'Two full-seed workers, three real resident CAN targets, one seeded-shape control, three can_to_deduction recurrence/transfer cases, and one opposite-direction singleton. Measures schema reuse, not bridge semantic accuracy or natural prevalence.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'integrity_checks':checks},indent=2))
 if not report['integrity_pass']:raise SystemExit('solver-family transfer integrity gates failed')
if __name__=='__main__':main()
