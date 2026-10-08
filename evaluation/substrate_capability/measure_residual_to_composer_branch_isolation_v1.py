#!/usr/bin/env python3
"""Measure residual-driven proposal induction inside a CoW branch."""
from __future__ import annotations
import copy,hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python"),str(ROOT/"evaluation/substrate_capability")]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/"docs/research/engine_substrate/RESIDUAL_TO_COMPOSER_BRANCH_ISOLATION_V1_PREREG_20261002.md"
ANALYZER=ROOT/"evaluation/substrate_capability/analyze_residual_to_composer_branch_isolation_v1.py"
LOCK=ROOT/"evaluation/substrate_capability/residual_to_composer_branch_isolation_v1_lock_20261002.json"
OUT=ROOT/"evaluation/reports/residual_to_composer_branch_isolation_v1_20261002.json"
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
SOURCES=('domains/reflective_faculty.py','domains/engine_provenance.py','substrate/boot_core.py','substrate/seed_loader.py',
 'runners/dsl/src/py.rs','runners/dsl/src/substrate.rs','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs',
 'runners/dsl/src/term.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs','runners/dsl/src/sym.rs',
 'runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/python/substrate_rs/__init__.py',
 'evaluation/substrate_capability/thoughtexperiment_a8_generalization_adapters_v1.py',
 'evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_1.py',
 'evaluation/substrate_capability/thoughtexperiment_a8_proposal_bridge_v1_4.py',
 'seeds/composer_experiment_graph.json','seeds/composer_dispatch.json','seeds/relation_vocabulary.json',
 'seeds/autonomy.json','seeds/grid_navigation.json')
WORKERS=len(TASKS)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 return {'files':{str(p.relative_to(ROOT)):sha(p) for p in (RUNNER,PREREG,ANALYZER,*(ROOT/s for s in SOURCES))},
  'native_binary':{'path':str(Path(_native.__file__).resolve()),'sha256':sha(Path(_native.__file__).resolve())}}
def canon(x):
 if hasattr(x,'value') and type(x).__name__=='NodeID':return int(x.value)
 if isinstance(x,dict):return {str(k):canon(v) for k,v in sorted(x.items(),key=lambda kv:str(kv[0]))}
 if isinstance(x,(list,tuple)):return [canon(v) for v in x]
 return x
def state(sub,native):
 nodes=[];edge_set=set()
 for nid in sorted(sub.nodes(),key=lambda n:int(n.value)):
  n=int(nid.value);nodes.append({'id':n,'record':canon(sub.node(nid))})
  for e in sub.incident_edges(nid):edge_set.add(json.dumps(canon(e),sort_keys=True,separators=(',',':'),default=str))
 return {'nodes':nodes,'edges':sorted(edge_set),'rules':native.export_rules(),
  'revision':list(native.experiment_graph_rule_revision()),'node_count':sub.node_count(),'edge_count':sub.edge_count()}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def derive(actual,expected):
 if actual not in VECTORS or expected not in VECTORS:return None,'unknown_or_missing_action'
 a,e=VECTORS[actual],VECTORS[expected]
 if a==(0,0) or e==(0,0):return None,'zero_displacement'
 if a==(-e[0],-e[1]) and (a[0]==0 or a[1]==0):return list(CUE),'opposite_axis'
 return None,'not_opposite_axis'
def action_outcome(ctx,state_data):
 sub,native=ctx['sub'],ctx['native']
 game=sub.add_node('Game',{'flood_epoch':0.0,'nav_mode':'frontier_seek'})
 avatar=sub.add_node('Cell',{'is_avatar_cell':1.0,'row':5.0,'col':5.0,'_adist':0.0,'_epoch':0.0,'_dist':1.0})
 target=sub.add_node('Cell',{'is_avatar_cell':0.0,'row':state_data['target'][0],'col':state_data['target'][1],
  '_adist':1.0,'_epoch':0.0,'_dist':0.0})
 native.add_edge_unchecked(game,'reached',avatar,{});native.add_edge_unchecked(game,'reached',target,{})
 work=int(native.run_rules(100))
 return {'case':state_data['case'],'actual':sub.node(game)['attrs'].get('chosen_action'),
  'expected':state_data['expected'],'closure_work':work}
class BranchAgent:
 def __init__(self,sub,agent):self.s=sub;self.inner=sub._inner;self.agent=agent
def worker(i):
 import thoughtexperiment_a8_generalization_adapters_v1 as adapters
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 import domains.reflective_faculty as rf
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 task=TASKS[i];before=frozen();ctx=adapters.prepare('navigation',i,'train');target=ctx['target'];native=ctx['native'];sub=ctx['sub']
 state_data={'case':task['id'],'target':TARGETS.get(task['expected'],[4.0,5.0]),'expected':task['expected'] or 'Up'}
 observed=action_outcome(ctx,state_data)
 if task['kind']=='opposite' and (observed['actual']!=task['actual'] or observed['expected']!=task['expected']):
  raise RuntimeError(f'residual mismatch for {task}: {observed}')
 if task['kind']=='absent_target':
  idx=next((j for j,r in enumerate(native.export_rules()) if r.get('name')==target and r.get('active',True)),None)
  if idx is None or not native.remove_rule(idx):raise RuntimeError('could not remove target in primary fixture')
 primary_before=state(sub,native);snapshot=sub.snapshot();fork_start=time.perf_counter_ns();branch=snapshot.fork();fork_ns=time.perf_counter_ns()-fork_start
 branch_agent=BranchAgent(branch,ctx['agent'].agent);bn=branch._inner
 derived,reason=derive(task['actual'],task['expected'])
 observation=[['actual',str(task['actual'])]]
 if task['expected'] is not None:observation.append(['expected',str(task['expected'])])
 if derived:observation.extend([[p,'present'] for p in derived])
 branch_before=state(branch,bn);t0=time.perf_counter_ns();induced=rf.induce_concern(branch_agent,observation);induce_ns=time.perf_counter_ns()-t0
 key=induced.get('capability_key');t1=time.perf_counter_ns();ground=rf.ground_concern(branch_agent,[key]);ground_ns=time.perf_counter_ns()-t1
 structural=ground.get('structural_variant') or {};branch_after=state(branch,bn)
 target_before=bridge._target_rule(native,target);primary_after_branch=state(sub,native)
 candidate=None;heldout=None
 if structural.get('built') and task['kind']=='opposite':
  candidate={'label':'branch_derived_residual_candidate','rules':{target:structural['rule']}}
  score_ctx=adapters.prepare('navigation',i,'heldout');heldout=adapters.score(score_ctx,candidate)
 primary_residual=sub.add_node('ExperimentResidual',{'experiment_id':f'residual_branch_iso_w{i}_{task["id"]}',
  'source':'residual_to_composer_branch_isolation_v1','task_case':task['id'],'observation':observation,
  'derived_cue':derived or [],'derivation_reason':reason,'proposal_built':bool(structural.get('built')),
  'target_rule':structural.get('removed_rule'),'operator':structural.get('kind'),'site':structural.get('site'),
  'candidate_rule':structural.get('rule') if structural.get('built') else {},
  'heldout_pass':bool(heldout and heldout.get('oracle_pass'))})
 primary_final=state(sub,native);residual_id=int(primary_residual.value)
 residual_payload=canon(sub.node(primary_residual)['attrs'])
 payload_candidate=residual_payload.get('candidate_rule') if isinstance(residual_payload,dict) else None
 before_nodes={n['id']:n['record'] for n in primary_before['nodes']};final_nodes={n['id']:n['record'] for n in primary_final['nodes']}
 new_ids=sorted(set(final_nodes)-set(before_nodes))
 existing_nodes_preserved=all(final_nodes.get(nid)==row for nid,row in before_nodes.items())
 after=frozen()
 return {'worker':i,'task':task,'source_before':before,'source_after':after,'source_stable':before==after,
  'fault_outcome':observed,'observation':observation,'induction':{'minted':induced.get('minted'),'key':key,
   'residual_predicates':induced.get('residual_predicates'),'wall_ns':induce_ns},
  'grounding':{'grounded':ground.get('grounded'),'built':bool(structural.get('built')),'kind':structural.get('kind'),
   'target':structural.get('removed_rule'),'site':structural.get('site'),'wall_ns':ground_ns,
   'candidate':candidate,'heldout_score':heldout},
  'branch':{'fork_ns':fork_ns,'node_delta':branch_after['node_count']-branch_before['node_count'],
   'edge_delta':branch_after['edge_count']-branch_before['edge_count'],'rule_count_delta':len(branch_after['rules'])-len(branch_before['rules']),
   'branch_changed':digest(branch_before)!=digest(branch_after)},
  'primary':{'unchanged_during_branch':digest(primary_before)==digest(primary_after_branch),
   'rules_unchanged_during_branch':primary_before['rules']==primary_after_branch['rules'],
   'revision_unchanged_during_branch':primary_before['revision']==primary_after_branch['revision'],
   'returned_residual_id':residual_id,'new_node_ids':new_ids,
   'returned_residual_payload':residual_payload,'returned_candidate_present':isinstance(payload_candidate,dict) and bool(payload_candidate),
   'only_residual_returned':new_ids==[residual_id] and existing_nodes_preserved and
    primary_final['edges']==primary_before['edges'] and primary_final['rules']==primary_before['rules'],
   'target_rule_preserved':bridge._target_rule(native,target)==target_before,
   'final_primary_graph_digest':digest(primary_final)}}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ResidualToComposerBranchIsolationV1Lock','sources':frozen(),'tasks':TASKS,'workers':WORKERS,
   'branch_backend':'public Substrate.snapshot().fork()','required_return':'one ExperimentResidual, no exploratory rules'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker ID')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for i in range(lock['workers']):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-2500:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ResidualToComposerBranchIsolationV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'sources':frozen(),'workers':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
