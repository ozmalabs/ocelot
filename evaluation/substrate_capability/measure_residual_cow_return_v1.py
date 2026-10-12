#!/usr/bin/env python3
"""Measure isolated residual proposal and graph-delta return for CoW and copy."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/RESIDUAL_COW_RETURN_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_return_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_return_v1_20261002.json'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_residual_cow_return_v1.py'
BACKENDS=('full_copy','shared_graph_pages')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def frozen():
 import measure_residual_to_composer_cue_derivation_v1 as cue
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 from substrate_rs import _native
 return {'cue_v1_sources':cue.frozen(),'bridge_sources':bridge.frozen(),'runner':sha(RUNNER),
  'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),'loaded_native_binary':sha(Path(_native.__file__).resolve())}
class BranchAgent:
 def __init__(self,branch,original):self.s=branch;self.inner=branch._inner;self.agent=original.agent
def counts(graph):return (len(graph.get('nodes',[])),len(graph.get('edges',[])))
def worker(index):
 import measure_residual_to_composer_cue_derivation_v1 as cue
 import thoughtexperiment_a8_generalization_adapters_v1 as adapters
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 import domains.reflective_faculty as rf
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native engine')
 task=cue.TASKS[index];rows=[]
 for backend in BACKENDS:
  before_source=frozen();ctx=adapters.prepare('navigation',index,'train')
  state={'case':task['id'],'target':cue.TARGETS.get(task['expected'],[4.,5.]),'expected':task['expected'] or 'Up'}
  from measure_residual_to_composer_grounding_boundary_v1 import action_outcome
  observed=action_outcome(ctx,state);parent=ctx['sub'];native=ctx['native'];target=ctx['target']
  if task['kind']=='opposite' and (observed.get('actual')!=task['actual'] or observed.get('expected')!=task['expected']):
   raise RuntimeError(f"task residual mismatch for {task['id']}: {observed}")
  target_before=bridge._target_rule(native,target)
  if task['kind']=='absent_target':
   idx=next((j for j,r in enumerate(native.export_rules()) if r.get('name')==target and r.get('active',True)),None)
   if idx is None or not native.remove_rule(idx):raise RuntimeError('absent-target control setup failed')
   target_before=bridge._target_rule(native,target)
  host_graph_before=parent.graph_to_dict();host_rules_before=native.export_rules()
  host_graph_digest=digest(host_graph_before);host_rules_digest=digest(host_rules_before)
  revision=parent.experiment_graph_rule_revision()
  fork_fn=parent.fork_full_copy_experiment if backend=='full_copy' else parent.fork_shared_graph_pages_experiment
  started=time.perf_counter_ns();branch=fork_fn();fork_ns=time.perf_counter_ns()-started
  agent=BranchAgent(branch,ctx['agent']);branch_native=branch._inner
  branch.begin_experiment_delta_journal()
  observation=[['actual',str(task['actual'])]]
  if task['expected'] is not None:observation.append(['expected',str(task['expected'])])
  derived,why=cue.derive(task['actual'],task['expected'])
  if derived:observation.extend([[p,'present'] for p in derived])
  started=time.perf_counter_ns();induced=rf.induce_concern(agent,observation);induce_ns=time.perf_counter_ns()-started
  branch.checkpoint_experiment_delta_journal()
  started=time.perf_counter_ns();ground=rf.ground_concern(agent,[induced.get('capability_key')]);ground_ns=time.perf_counter_ns()-started
  structural=ground.get('structural_variant') or {};delta=branch.finish_experiment_delta_journal()
  branch_target_after=bridge._target_rule(branch_native,target)
  host_unchanged_before_return=(digest(parent.graph_to_dict())==host_graph_digest and digest(native.export_rules())==host_rules_digest)
  heldout=None
  if structural.get('built') and task['kind']=='opposite':
   score_ctx=adapters.prepare('navigation',index,'heldout')
   heldout=adapters.score(score_ctx,{'label':'cow_residual_candidate','rules':{target:structural['rule']}})
  adopt=False;adopt_ns=0;host_graph_after=parent.graph_to_dict();host_rules_after=native.export_rules()
  if task['kind']=='opposite' and structural.get('built') and heldout and heldout.get('oracle_pass') and host_unchanged_before_return:
   started=time.perf_counter_ns();parent.apply_experiment_graph_delta(revision,delta['derived_only']);adopt_ns=time.perf_counter_ns()-started
   adopt=True;host_graph_after=parent.graph_to_dict();host_rules_after=native.export_rules()
  host_rule_store_preserved=digest(host_rules_after)==host_rules_digest
  branch_graph=branch.graph_to_dict()
  added=delta['derived_only'].get('nodes_added',[]);edges=delta['derived_only'].get('edges_added',[])
  # Verify every adopted graph fact is present with the exact branch value.
  after_nodes={r['id']:r for r in host_graph_after.get('nodes',[])}
  branch_nodes={r['id']:r for r in branch_graph.get('nodes',[])}
  node_parity=all(after_nodes.get(r['id'])==branch_nodes.get(r['id']) for r in added) if adopt else True
  edge_keys=lambda g:{(r['src'],r['type'],r['tgt'],json.dumps(r.get('attrs',{}),sort_keys=True)) for r in g.get('edges',[])}
  adopted_edges=edge_keys(host_graph_after)-edge_keys(host_graph_before)
  expected_edges={(r['src'],r['type'],r['tgt'],json.dumps(r.get('attrs',{}),sort_keys=True)) for r in edges}
  edge_parity=adopted_edges==expected_edges if adopt else True
  changed_node_parity=all(after_nodes.get(r['id'])==branch_nodes.get(r['id']) for r in delta['derived_only'].get('nodes_changed',[])) if adopt else True
  removed_node_parity=all(r not in after_nodes for r in delta['derived_only'].get('nodes_removed',[])) if adopt else True
  branch_edge_rows={(r['src'],r['type'],r['tgt']):r for r in branch_graph.get('edges',[])}
  host_edge_rows={(r['src'],r['type'],r['tgt']):r for r in host_graph_after.get('edges',[])}
  changed_edge_parity=all(host_edge_rows.get((r['src'],r['type'],r['tgt']))==branch_edge_rows.get((r['src'],r['type'],r['tgt'])) for r in delta['derived_only'].get('edges_changed',[])) if adopt else True
  removed_edge_parity=all((r['src'],r['type'],r['tgt']) not in host_edge_rows for r in delta['derived_only'].get('edges_removed',[])) if adopt else True
  after_source=frozen()
  rows.append({'worker':index,'backend':backend,'task':task,'source_before':before_source,'source_after':after_source,
   'source_stable':before_source==after_source,'fault_task_outcome':observed,'derived_cue':derived,'derivation_reason':why,
   'proposal':{'built':bool(structural.get('built')),'kind':structural.get('kind'),'target':structural.get('removed_rule'),
    'branch_target_preserved':target_before==branch_target_after},
   'heldout_score':heldout,'host_unchanged_before_return':host_unchanged_before_return,
   'residual':{'total':delta['conclusions'],'derived_only':delta['derived_only'],'derived_digest':digest(delta['derived_only']),
    'nonempty_derived_delta':bool(added or edges)},
   'return':{'applied':adopt,'revision':list(revision),'adoption_ns':adopt_ns,
    'host_rule_store_preserved':host_rule_store_preserved,'added_node_parity':node_parity,'added_edge_parity':edge_parity,
    'changed_node_parity':changed_node_parity,'removed_node_parity':removed_node_parity,
    'changed_edge_parity':changed_edge_parity,'removed_edge_parity':removed_edge_parity,
    'host_graph_before_counts':list(counts(host_graph_before)),'host_graph_after_counts':list(counts(host_graph_after)),
    'host_rule_count_before':len(host_rules_before),'host_rule_count_after':len(host_rules_after)},
   'timing_ns':{'fork':fork_ns,'induce':induce_ns,'ground':ground_ns},
   'branch_rule_count_before':len(host_rules_before),'branch_rule_count_after':len(branch_native.export_rules())})
 return rows
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ResidualCowReturnV1Lock','sources':frozen(),'backends':BACKENDS,
   'workers':13,'protocol_tasks':'residual cue derivation v1 task matrix'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker ID')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for i in range(lock['workers']):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-3000:]}')
  rows.extend(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ResidualCowReturnV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
