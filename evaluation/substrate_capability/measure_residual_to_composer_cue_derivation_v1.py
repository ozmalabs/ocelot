#!/usr/bin/env python3
"""Test an explicit action-geometry bridge from residuals to composer cues."""
from __future__ import annotations
import hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/RESIDUAL_TO_COMPOSER_CUE_DERIVATION_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/residual_to_composer_cue_derivation_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/residual_to_composer_cue_derivation_v1_20261002.json'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_residual_to_composer_cue_derivation_v1.py'
TASKS=[
 {'id':'opposite_up','actual':'Down','expected':'Up','kind':'opposite'},
 {'id':'opposite_down','actual':'Up','expected':'Down','kind':'opposite'},
 {'id':'opposite_left','actual':'Right','expected':'Left','kind':'opposite'},
 {'id':'opposite_right','actual':'Left','expected':'Right','kind':'opposite'},
 {'id':'orthogonal','actual':'Right','expected':'Up','kind':'other'},
 {'id':'orthogonal_2','actual':'Up','expected':'Left','kind':'other'},
 {'id':'same_direction','actual':'Up','expected':'Up','kind':'other'},
 {'id':'same_direction_2','actual':'Left','expected':'Left','kind':'other'},
 {'id':'unknown_action','actual':'Teleport','expected':'Up','kind':'unknown'},
 {'id':'unknown_expected','actual':'Down','expected':'Portal','kind':'unknown'},
 {'id':'missing_expected','actual':'Down','expected':None,'kind':'missing'},
 {'id':'zero_displacement','actual':'Stay','expected':'Up','kind':'zero'},
 {'id':'target_absent','actual':'Down','expected':'Up','kind':'absent_target'},
]
VECTORS={'Up':(-1,0),'Down':(1,0),'Left':(0,-1),'Right':(0,1),'Stay':(0,0)}
TARGETS={'Up':[4.0,5.0],'Down':[6.0,5.0],'Left':[5.0,4.0],'Right':[5.0,6.0]}
CUE=['test','send','judge','structure','gradient','flip','comparison','gate']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 from substrate_rs import _native
 return {'bridge_sources':bridge.frozen(),'runner':sha(RUNNER),'protocol':sha(PREREG),
  'analyzer':sha(ANALYZER),
  'loaded_native_binary':sha(Path(_native.__file__).resolve())}
def derive(actual,expected):
 """Emit an operator cue only for exact 180-degree reversal along one axis."""
 if actual not in VECTORS or expected not in VECTORS:return None,'unknown_or_missing_action'
 a,e=VECTORS[actual],VECTORS[expected]
 if a==(0,0) or e==(0,0):return None,'zero_displacement'
 if a==(-e[0],-e[1]) and (a[0]==0 or a[1]==0):return list(CUE),'opposite_axis'
 return None,'not_opposite_axis'

def worker(i):
 import thoughtexperiment_a8_generalization_adapters_v1 as adapters
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 import domains.reflective_faculty as rf
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine is stale')
 task=TASKS[i];before=frozen();ctx=adapters.prepare('navigation',i,'train')
 # Establish that this fresh graph has the intended fault and task context.
 state={'case':task['id'],'target':TARGETS.get(task['expected'],[4.0,5.0]),'expected':task['expected'] or 'Up'}
 from measure_residual_to_composer_grounding_boundary_v1 import action_outcome
 observed=action_outcome(ctx,state)
 target=ctx['target'];native=ctx['native'];sub=ctx['sub']
 if task['kind']=='opposite' and (observed.get('actual')!=task['actual'] or observed.get('expected')!=task['expected']):
  raise RuntimeError(f"task residual mismatch: expected {task}, got {observed}")
 derived,reason=derive(task['actual'],task['expected'])
 # Each trial receives actual/expected labels; only the candidate derivation
 # contributes operator predicates. Ambiguous cases retain the raw residual.
 observation=[['actual',str(task['actual'])]]
 if task['expected'] is not None:observation.append(['expected',str(task['expected'])])
 if derived:
  observation.extend([[p,'present'] for p in derived])
 if task['kind']=='absent_target':
  idx=next((j for j,row in enumerate(native.export_rules()) if row.get('name')==target and row.get('active',True)),None)
  if idx is None or not native.remove_rule(idx):raise RuntimeError('could not remove target for absent-target control')
 target_before=bridge._target_rule(native,target)
 if task['kind']!='absent_target':target_before=bridge._target_rule(native,target)
 rules_before=sorted(row.get('name') for row in native.export_rules() if row.get('active',True))
 start=time.perf_counter_ns();induced=rf.induce_concern(ctx['agent'],observation);induce_ns=time.perf_counter_ns()-start
 key=induced.get('capability_key')
 start=time.perf_counter_ns();ground=rf.ground_concern(ctx['agent'],[key]);ground_ns=time.perf_counter_ns()-start
 structural=ground.get('structural_variant') or {}
 target_after=bridge._target_rule(native,target)
 rules_after=sorted(row.get('name') for row in native.export_rules() if row.get('active',True))
 # For opposite-action cases independently confirm that the proposal is useful
 # on the held-out navigation panel without installing it in the primary graph.
 heldout=None
 if structural.get('built') and task['kind']=='opposite':
  score_ctx=adapters.prepare('navigation',i,'heldout')
  candidate={'label':'derived_residual_candidate','rules':{target:structural['rule']}}
  heldout=adapters.score(score_ctx,candidate)
 after=frozen()
 return {'worker':i,'task':task,'source_before':before,'source_after':after,'source_stable':before==after,
  'fault_task_outcome':observed,'derived_cue':derived,'derivation_reason':reason,
  'observation':observation,'induction':{'minted':induced.get('minted'),'key':key,
   'residual_predicates':induced.get('residual_predicates'),'wall_ns':induce_ns},
  'grounding':{'grounded':ground.get('grounded'),'path':ground.get('path'),'reason':ground.get('reason'),
   'wall':ground.get('wall'),'built':bool(structural.get('built')),'kind':structural.get('kind'),
   'target':structural.get('removed_rule'),'site':structural.get('site'),'wall_ns':ground_ns,
   'primary_rule_preserved':target_before==target_after,'active_rule_additions':sorted(set(rules_after)-set(rules_before)),
   'active_rule_removals':sorted(set(rules_before)-set(rules_after))},'heldout_score':heldout}

def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ResidualToComposerCueDerivationV1Lock','sources':frozen(),
   'tasks':TASKS,'workers':len(TASKS),'candidate':'action-vector inversion yields composer cue; otherwise abstain'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker ID')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
 rows=[]
 for i in range(lock['workers']):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ResidualToComposerCueDerivationV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'workers':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
