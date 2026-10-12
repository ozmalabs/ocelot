#!/usr/bin/env python3
"""Fresh-process ProblemShape transfer panel over unseeded CAN Goal schemas."""
from __future__ import annotations
import hashlib,importlib.util,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_UNSEEDED_SCHEMA_TRANSFER_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_unseeded_schema_transfer_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/problem_shape_unseeded_schema_transfer_v1_20260927.json'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
MEASURE=ROOT/'scripts/substrate_problem_shape_induction_economics.py'
SEEDS=['seeds/problem_shape_growth.json','seeds/shape_decode_loop.json','seeds/bigville_cast100.json']
SCENARIOS=['seeded_exact_control','singleton_controls','relax_recurrence_transfer','bp_recurrence_transfer','mixed_family_separation']
SCHEDULE=[(name,rep) for name in SCENARIOS for rep in range(2)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def runtime_inputs():
 spec=importlib.util.spec_from_file_location('seed_provenance',PROVENANCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.inputs()
def inputs():return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'measure_helper_sha256':sha(MEASURE),'runtime_inputs':runtime_inputs(),'seed_hashes':{p:sha(ROOT/p) for p in SEEDS},'scenario_order':SCENARIOS}
def rss():
 v=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;return int(v*(1024 if sys.platform.startswith('linux') else 1))
def worker(scenario,rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from substrate_rs import _native
 from domains import solver_dispatch as sd,problem_shape as ps
 from worlds import bigville_can_beliefs as bcb
 from scripts.substrate_problem_shape_induction_economics import pump,observe_measure
 boot_wall0=time.perf_counter_ns();boot_cpu0=time.process_time_ns();a=WorldAdapter(seeds=());load=load_all_seeds(a)
 a.register_reflex_response('question_pursue',lambda ag:ag._question_pursue_advance());a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
 native=a.inner;s=a.s;Native=_native.Substrate;bcb.install_productions(native)
 residents=json.loads((ROOT/'seeds/bigville_cast100.json').read_text())['residents']
 def can_mt(i):
  built=bcb.build_resident_can_mt(native,residents[i]);bcb.apply_scenario_evidence(native,built['concepts']);native.set_attr(built['mt_node'],'discrete_mode','3state');native.set_attr(built['mt_node'],'can_tick',0);return built['mt_node']
 if scenario=='seeded_exact_control': specs=[('exact',0,None),('exact',1,None)]
 elif scenario=='singleton_controls':specs=[('relax',0,2),('bp',1,'max_product')]
 elif scenario=='relax_recurrence_transfer':specs=[('relax',2,1),('relax',3,4)]
 elif scenario=='bp_recurrence_transfer':specs=[('bp',4,'max_product'),('bp',5,'sum_product')]
 elif scenario=='mixed_family_separation':specs=[('relax',6,1),('bp',7,'max_product'),('relax',8,3),('bp',9,'sum_product')]
 else:raise ValueError(scenario)
 Native.scale_audit_set_enabled(True);Native.scale_audit_set_per_rule_enabled(True);records=[];resolution=[]
 for idx,(kind,resident,param) in enumerate(specs):
  mt=can_mt(resident)
  if kind=='exact':goal=sd.mint_solve_can_exact_goal(a,mt)
  elif kind=='relax':goal=sd.mint_solve_can_relax_goal(a,mt,k_starts=int(param))
  else:goal=sd.mint_solve_can_bp_goal(a,mt,combine=str(param))
  rr=pump(a,goal);resolution.append({'label':f'{kind}_{idx+1}','status':rr['status'],'iterations':rr['iterations']})
  key=ps.signature_key(ps.goal_signature(s,native,goal));r=observe_measure(a,goal,f'{kind}_{idx+1}',Native);r.update({'solver_family':kind,'resident_index':resident,'parameter':param,'signature_key':key});records.append(r)
 for r in records:
  obs_id=r['observation_id'];attrs=s.node(_native.NodeID(obs_id))['attrs'] if obs_id is not None else {}
  r['observation_status_final']=attrs.get('status');r['covered_by_final']=attrs.get('covered_by')
 Native.scale_audit_set_enabled(False);Native.scale_audit_set_per_rule_enabled(False)
 final_shapes=[{'name':s.node(n)['attrs'].get('name'),'support':s.node(n)['attrs'].get('support'),'minted':s.node(n)['attrs'].get('minted')} for n in s.nodes('ProblemShape')]
 return {'scenario':scenario,'replicate':rep,'pid':os.getpid(),'boot_loaded':load.get('loaded'),'boot_failure_count':len(load.get('failed',[])),'boot_wall_ns':time.perf_counter_ns()-boot_wall0,'boot_cpu_ns':time.process_time_ns()-boot_cpu0,'goal_resolution':resolution,'records':records,'final_problem_shapes':final_shapes,'total_new_shapes':sum(r['problem_shape_count_delta'] for r in records),'total_mints':sum(r['mint_count_delta'] for r in records),'total_ps_candidate_pairs':sum(r['problem_shape_candidate_pairs'] for r in records),'total_ps_term_evaluations':sum(r['problem_shape_term_evaluations'] for r in records),'all_post_observe_fixed_point':all(r['post_observe_settle_report']['status']=='fixed_point' for r in records),'peak_rss_bytes':rss(),'environment':{'python':sys.version,'platform':platform.platform()}}
def worker_ok(r):
 rec=r['records'];keys=[x['signature_key'] for x in rec];initial=[x['observation_status_initial'] for x in rec];final=[x['observation_status_final'] for x in rec];cover=[x['covered_by_final'] for x in rec];kinds=[x['solver_family'] for x in rec]
 if not r['all_post_observe_fixed_point'] or any(x['status']!='resolved' for x in r['goal_resolution']):return False
 if r['scenario']=='seeded_exact_control':return len(rec)==2 and len(set(keys))==1 and initial==['recognized']*2 and final==['recognized']*2 and r['total_mints']==0 and r['total_new_shapes']==0
 if r['scenario']=='singleton_controls':return len(rec)==2 and len(set(keys))==2 and initial==['residual','residual'] and final==initial and r['total_mints']==0 and r['total_new_shapes']==0
 if r['scenario'] in ('relax_recurrence_transfer','bp_recurrence_transfer'):
  return len(rec)==2 and len(set(keys))==1 and initial[0]=='residual' and initial[1]=='recognized' and final==['recognized']*2 and r['total_mints']==1 and r['total_new_shapes']==1 and cover==[keys[0],keys[0]]
 if r['scenario']=='mixed_family_separation':
  return len(rec)==4 and len(set(keys))==2 and keys[0]==keys[2] and keys[1]==keys[3] and keys[0]!=keys[1] and kinds==['relax','bp','relax','bp'] and final==['recognized']*4 and r['total_mints']==2 and r['total_new_shapes']==2 and cover==[keys[0],keys[1],keys[0],keys[1]]
 return False
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  cond=os.environ['OCEL0_PS_SCHEMA_SCENARIO'];rep=int(os.environ['OCEL0_PS_SCHEMA_REP']);before=inputs();r=worker(cond,rep);after=inputs();r.update({'worker_inputs_before':before,'worker_inputs_after':after,'source_stable':before==after});print(json.dumps(r,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale ProblemShape schema-transfer lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT / "runners/dsl/python"}:{ROOT / "scripts"}'};stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')) )"],cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit(f'native build stale: {stale}')
 runs=[]
 for cond,rep in SCHEDULE:
  e=env.copy();e.update(OCEL0_PS_SCHEMA_SCENARIO=cond,OCEL0_PS_SCHEMA_REP=str(rep));p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=e,text=True,capture_output=True,timeout=240)
  r=json.loads(p.stdout) if p.stdout.strip() else {'scenario':cond,'replicate':rep,'worker_error':p.stderr};r['worker_returncode']=p.returncode;r['worker_stderr']=p.stderr;runs.append(r);print(f'completed={cond}/{rep} rc={p.returncode}',file=sys.stderr,flush=True)
 after=inputs();checks={'ten_workers':len(runs)==10,'ten_unique_pids':len({r.get('pid') for r in runs})==10,'two_per_scenario':all(sum(r.get('scenario')==s for r in runs)==2 for s in SCENARIOS),'parent_source_stable':after==locked,'worker_source_stable':all(r.get('source_stable') and r.get('worker_inputs_before')==locked==r.get('worker_inputs_after') for r in runs),'all_goal_observations_settle':all(all(g.get('status')=='resolved' for g in r.get('goal_resolution',[])) and r.get('all_post_observe_fixed_point') for r in runs),'all_scenario_gates_pass':len(runs)==10 and all(p['worker_returncode']==0 and worker_ok(p) for p in runs)}
 report={'schema_version':1,'run_id':'problem-shape-unseeded-schema-transfer-v1-20260927','locked_inputs':locked,'post_run_inputs':after,'schedule':SCHEDULE,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs,'claim_boundary':'Two unseeded CAN solve-goal schemas, five source-stratified scenario families, two cold full-seed workers each; not natural residual prevalence or general concept invention.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('unseeded-schema transfer gates failed')
if __name__=='__main__':main()
