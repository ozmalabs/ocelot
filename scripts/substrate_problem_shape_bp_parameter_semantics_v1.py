#!/usr/bin/env python3
"""Source-locked paired BP setting audit for ProblemShape key semantics."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_BP_PARAMETER_SEMANTICS_V1_PREREG_20260927.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_bp_parameter_semantics_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/problem_shape_bp_parameter_semantics_v1_20260927.json'
PROVENANCE=ROOT/'scripts/substrate_seed_rule_provenance_live_capture_v1.py'
SEED=ROOT/'seeds/bigville_cast100.json'
RESIDENTS=[0,25,50]
SCHEDULE=[(r,rep) for r in RESIDENTS for rep in range(2)]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def runtime_inputs():
 spec=importlib.util.spec_from_file_location('seed_provenance_bpsem',PROVENANCE);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m.inputs()
def inputs():return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'runtime_inputs':runtime_inputs(),'seed_sha256':sha(SEED),'resident_indices':RESIDENTS,'settings':['max_product','sum_product']}
def worker(resident,rep):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from substrate_rs import _native
 from domains import solver_dispatch as sd,problem_shape as ps
 from worlds import bigville_can_beliefs as bcb
 from scripts.substrate_problem_shape_induction_economics import pump
 t0=time.perf_counter_ns();c0=time.process_time_ns();a=WorldAdapter(seeds=());load=load_all_seeds(a)
 a.register_reflex_response('question_pursue',lambda ag:ag._question_pursue_advance());a.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
 native=a.inner;s=a.s;Native=_native.Substrate;bcb.install_productions(native)
 residents=json.loads(SEED.read_text())['residents'];built=bcb.build_resident_can_mt(native,residents[resident]);bcb.apply_scenario_evidence(native,built['concepts']);native.set_attr(built['mt_node'],'discrete_mode','3state');native.set_attr(built['mt_node'],'can_tick',0);mt=built['mt_node']
 def projection():
  concepts=[]
  for n in native.neighbours(mt,'has_concept'):
   concepts.append((int(n.value),dict(s.node(n)['attrs'])))
  return {'concepts':sorted(concepts,key=lambda row:row[0])}
 before_state=projection();rows=[];resolutions=[]
 for combine in ('max_product','sum_product'):
  goal=sd.mint_solve_can_bp_goal(a,mt,combine=combine,commit=False)
  result=pump(a,goal);resolutions.append({'combine':combine,'status':result['status'],'iterations':result['iterations']})
  attrs=s.node(goal)['attrs'];answer=attrs.get('answer') or {};state={str(k):float(v) for k,v in (answer.get('final_state') or {}).items()}
  signature=ps.goal_signature(s,native,goal);rows.append({'combine':combine,'status':attrs.get('status'),'answer':answer,'belief_state':state,'signature_key':ps.signature_key(signature),'note':attrs.get('note')})
 after_state=projection();left,right=(x['belief_state'] for x in rows);same_keys=rows[0]['signature_key']==rows[1]['signature_key'];same_state=left==right
 ids=set(left)|set(right);delta=max((abs(left.get(k,0.0)-right.get(k,0.0)) for k in ids),default=0.0)
 return {'resident_index':resident,'replicate':rep,'pid':os.getpid(),'boot_loaded':load.get('loaded'),'boot_failure_count':len(load.get('failed',[])),'elapsed_wall_ns':time.perf_counter_ns()-t0,'elapsed_cpu_ns':time.process_time_ns()-c0,'goal_resolution':resolutions,'rows':rows,'same_signature_key':same_keys,'belief_maps_exactly_equal':same_state,'max_abs_belief_delta':delta,'finite_beliefs':all(__import__('math').isfinite(v) for row in rows for v in row['belief_state'].values()),'can_state_unchanged':before_state==after_state,'can_state_before':before_state,'can_state_after':after_state,'environment':{'python':sys.version,'platform':platform.platform()}}
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':inputs()},indent=2,sort_keys=True));return
 if sys.argv[1:]==['--worker']:
  before=inputs();return_worker=worker(int(os.environ['OCEL0_BPSEM_RESIDENT']),int(os.environ['OCEL0_BPSEM_REP']));after=inputs();return_worker.update({'worker_inputs_before':before,'worker_inputs_after':after});return_worker['source_stable']=before==after;print(json.dumps(return_worker,sort_keys=True));return
 locked=inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing/stale BP parameter semantics lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT / "runners/dsl/python"}:{ROOT / "scripts"}'}
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')) )"],cwd=ROOT,env=env,text=True).strip()
 if stale:raise SystemExit(f'native build stale: {stale}')
 runs=[]
 for resident,rep in SCHEDULE:
  e=env.copy();e.update(OCEL0_BPSEM_RESIDENT=str(resident),OCEL0_BPSEM_REP=str(rep));p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],cwd=ROOT,env=e,text=True,capture_output=True,timeout=240)
  r=json.loads(p.stdout) if p.stdout.strip() else {'resident_index':resident,'replicate':rep,'worker_error':p.stderr};r['worker_returncode']=p.returncode;r['worker_stderr']=p.stderr;runs.append(r);print(f'completed=resident{resident}/{rep} rc={p.returncode}',file=sys.stderr,flush=True)
 after=inputs();checks={'six_workers':len(runs)==6,'unique_pids':len({r.get('pid') for r in runs})==6,'two_per_resident':all(sum(r.get('resident_index')==i for r in runs)==2 for i in RESIDENTS),'parent_source_stable':after==locked,'worker_source_stable':all(r.get('source_stable') and r.get('worker_inputs_before')==locked==r.get('worker_inputs_after') for r in runs),'resolved_goals':all(r.get('worker_returncode')==0 and all(g.get('status')=='resolved' for g in r.get('goal_resolution',[])) for r in runs),'same_keys_finite_outputs':all(r.get('same_signature_key') and r.get('finite_beliefs') for r in runs),'no_commit_state_parity':all(r.get('can_state_unchanged') for r in runs)}
 report={'schema_version':1,'run_id':'problem-shape-bp-parameter-semantics-v1-20260927','locked_inputs':locked,'post_run_inputs':after,'schedule':SCHEDULE,'checks':checks,'all_checks_pass':all(checks.values()),'runs':runs,'claim_boundary':'Paired solver-setting semantics on three selected CAN residents; shared structural key is not assumed to imply behavioral equivalence.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('BP parameter semantics integrity gates failed')
if __name__=='__main__':main()
