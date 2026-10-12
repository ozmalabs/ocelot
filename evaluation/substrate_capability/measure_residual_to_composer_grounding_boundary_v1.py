#!/usr/bin/env python3
"""Measure whether raw task-error residuals ground into structural proposals."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/RESIDUAL_TO_COMPOSER_GROUNDING_BOUNDARY_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_grounding_boundary_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/residual_to_composer_grounding_boundary_v1_20261002.json'
WORKERS=4
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 return {'runner':sha(RUNNER),'preregistration':sha(PREREG),
  'bridge_sources':bridge.frozen(),'python':sys.version,'platform':platform.platform()}
def action_outcome(ctx,state):
 sub,native=ctx['sub'],ctx['native']
 game=sub.add_node('Game',{'flood_epoch':0.0,'nav_mode':'frontier_seek'})
 avatar=sub.add_node('Cell',{'is_avatar_cell':1.0,'row':5.0,'col':5.0,'_adist':0.0,'_epoch':0.0,'_dist':1.0})
 target=sub.add_node('Cell',{'is_avatar_cell':0.0,'row':state['target'][0],'col':state['target'][1],
  '_adist':1.0,'_epoch':0.0,'_dist':0.0})
 native.add_edge_unchecked(game,'reached',avatar,{})
 native.add_edge_unchecked(game,'reached',target,{})
 work=int(native.run_rules(100))
 return {'case':state['case'],'actual':sub.node(game)['attrs'].get('chosen_action'),
  'expected':state['expected'],'closure_work':work}
def worker(i):
 import thoughtexperiment_a8_generalization_adapters_v1 as adapters
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 import domains.reflective_faculty as rf
 before=frozen();state=bridge.TRAIN_STATES[i%len(bridge.TRAIN_STATES)]
 raw_ctx=adapters.prepare('navigation',i,'train');target=raw_ctx['target']
 target_before=bridge._target_rule(raw_ctx['native'],target)
 observed=action_outcome(raw_ctx,state)
 if observed['actual']==observed['expected']:raise RuntimeError('fault control did not produce an outcome residual')
 # Generic task-result fields are passed as the observation; no target/operator cue or name_hint.
 observation=[['actual',str(observed['actual'])],['expected',str(observed['expected'])]]
 induce_started=time.perf_counter_ns();induced=rf.induce_concern(raw_ctx['agent'],observation)
 induce_ns=time.perf_counter_ns()-induce_started
 key=induced.get('capability_key')
 ground_started=time.perf_counter_ns();raw_ground=rf.ground_concern(raw_ctx['agent'],[key])
 raw_ground_ns=time.perf_counter_ns()-ground_started
 raw_after=bridge._target_rule(raw_ctx['native'],target)
 # Independent positive control uses the already measured authored A8 cue on a fresh branch.
 prompt_ctx=adapters.prepare('navigation',i,'train')
 prompt=bridge._compose(prompt_ctx,i,True)
 after=frozen()
 return {'worker':i,'case':state['case'],'source_before':before,'source_after':after,
  'source_stable':before==after,'fault_outcome':observed,'observation':observation,
  'induction':{'minted':induced.get('minted'),'key':key,'residual_predicates':induced.get('residual_predicates'),
   'name_hint_supplied':False,'wall_ns':induce_ns},
  'raw_residual_grounding':{'grounded':raw_ground.get('grounded'),'path':raw_ground.get('path'),
   'reason':raw_ground.get('reason'),'wall':raw_ground.get('wall'),'wall_ns':raw_ground_ns,
   'primary_rule_preserved':target_before==raw_after},
  'authored_cue_control':prompt}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'ResidualToComposerGroundingBoundaryV1Lock','sources':frozen(),
   'workers':WORKERS,'raw_observation':'actual/expected output fields from the faulted navigation task',
   'raw_no_target_cue':True,'authored_control_cue':'A8 v1.4 PROMPT_CUE',
   'expected_raw_boundary':'induced axis exists, but ground_concern has no held relation and emits no proposal',
   'expected_control':{'built':True,'target':'hop_descend_gradient','operator':'flip_comparison'}},
   indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker ID')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for i in range(lock['workers']):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ResidualToComposerGroundingBoundaryV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'workers':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
