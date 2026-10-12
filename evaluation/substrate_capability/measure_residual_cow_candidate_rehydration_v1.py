#!/usr/bin/env python3
"""Round-trip a validated candidate through a CoW graph residual."""
from __future__ import annotations
import hashlib,json,os,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/RESIDUAL_COW_CANDIDATE_REHYDRATION_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_candidate_rehydration_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_candidate_rehydration_v1_20261002.json'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_residual_cow_candidate_rehydration_v1.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def frozen():
 import measure_residual_to_composer_cue_derivation_v1 as cue
 import measure_residual_cow_return_v1 as prior
 from substrate_rs import _native
 return {'cue_sources':cue.frozen(),'prior_cow_sources':prior.frozen(),'runner':sha(RUNNER),
  'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),'native_binary':sha(Path(_native.__file__).resolve())}
class BranchAgent:
 def __init__(self,branch,original):self.s=branch;self.inner=branch._inner;self.agent=original.agent
def worker(i):
 import measure_residual_to_composer_cue_derivation_v1 as cue
 import thoughtexperiment_a8_generalization_adapters_v1 as adapters
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 import domains.reflective_faculty as rf
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native engine')
 task=cue.TASKS[i];before=frozen();ctx=adapters.prepare('navigation',i,'train')
 state={'case':task['id'],'target':cue.TARGETS[task['expected']],'expected':task['expected']}
 from measure_residual_to_composer_grounding_boundary_v1 import action_outcome
 observed=action_outcome(ctx,state)
 if observed.get('actual')!=task['actual'] or observed.get('expected')!=task['expected']:
  raise RuntimeError(f"faulted outcome mismatch: {observed}")
 parent=ctx['sub'];native=ctx['native'];target=ctx['target'];host_graph_before=parent.graph_to_dict()
 host_rules_before=native.export_rules();host_graph_hash=digest(host_graph_before);host_rules_hash=digest(host_rules_before)
 base_revision=parent.experiment_graph_rule_revision()
 fork_started=time.perf_counter_ns();branch=parent.fork_shared_graph_pages_experiment();fork_ns=time.perf_counter_ns()-fork_started
 agent=BranchAgent(branch,ctx['agent']);branch.begin_experiment_delta_journal()
 observation=[['actual',task['actual']],['expected',task['expected']],*[[p,'present'] for p in cue.CUE]]
 induce_started=time.perf_counter_ns();induced=rf.induce_concern(agent,observation);induce_ns=time.perf_counter_ns()-induce_started
 branch.checkpoint_experiment_delta_journal()
 ground_started=time.perf_counter_ns();ground=rf.ground_concern(agent,[induced['capability_key']]);ground_ns=time.perf_counter_ns()-ground_started
 structural=ground.get('structural_variant') or {}
 candidate={'label':'returned_residual_candidate','rules':{target:structural['rule']}}
 initial_ctx=adapters.prepare('navigation',i,'heldout');initial_score=adapters.score(initial_ctx,candidate)
 if not (structural.get('built') and structural.get('kind')=='flip_comparison' and initial_score.get('oracle_pass')):
  raise RuntimeError('candidate failed pre-return held-out gate')
 candidate_json=json.dumps(candidate,sort_keys=True,separators=(',',':'))
 candidate_digest=digest(candidate)
 residual_node=branch.add_node('ThoughtexperimentCandidateResidual',{
  'schema':'thoughtexperiment_candidate_residual.v1','target_rule':target,'operator':'flip_comparison',
  'candidate_json':candidate_json,'candidate_digest':candidate_digest,'validated_before_return':1.0,
  'heldout_pass':1.0,'source_capability_key':str(induced['capability_key'])})
 residual_node_id=int(residual_node.value)
 journal_started=time.perf_counter_ns();delta=branch.finish_experiment_delta_journal();journal_ns=time.perf_counter_ns()-journal_started
 host_unchanged_before_return=(digest(parent.graph_to_dict())==host_graph_hash and digest(native.export_rules())==host_rules_hash)
 stale_rejected=None;stale_host_unchanged=None;adoption_revision=base_revision
 if i==0:
  game=parent.nodes('Game')[-1];parent.set_attr(game,'cow_stale_revision_probe',1.0)
  mutated_graph=parent.graph_to_dict();stale_revision=base_revision
  try:parent.apply_experiment_graph_delta(stale_revision,delta['derived_only'])
  except RuntimeError:stale_rejected=True
  else:stale_rejected=False
  stale_host_unchanged=digest(parent.graph_to_dict())==digest(mutated_graph)
  adoption_revision=parent.experiment_graph_rule_revision()
 adopt_started=time.perf_counter_ns();parent.apply_experiment_graph_delta(adoption_revision,delta['derived_only']);adopt_ns=time.perf_counter_ns()-adopt_started
 from substrate_rs import NodeID
 returned_attrs=parent.node(NodeID(residual_node_id))['attrs']
 returned_candidate=json.loads(returned_attrs['candidate_json'])
 readback_digest=digest(returned_candidate)
 replay_ctx=adapters.prepare('navigation',i,'heldout');replayed=adapters.score(replay_ctx,returned_candidate)
 final_graph=parent.graph_to_dict();final_rules=native.export_rules()
 after=frozen()
 return {'worker':i,'task':task,'source_before':before,'source_after':after,'source_stable':before==after,
  'proposal':{'built':bool(structural.get('built')),'kind':structural.get('kind'),'target':structural.get('removed_rule')},
  'pre_return_score':initial_score,'host_unchanged_before_return':host_unchanged_before_return,
  'residual_node_id':residual_node_id,'residual_delta':delta['derived_only'],
  'return':{'stale_revision_rejected':stale_rejected,'stale_attempt_host_unchanged':stale_host_unchanged,
   'applied':True,'candidate_readback_digest':readback_digest,'candidate_digest_matches':readback_digest==candidate_digest,
   'candidate_semantic_identity':bridge._semantic_digest(returned_candidate)==bridge._semantic_digest(candidate),
   'replayed_score':replayed,'host_rules_unchanged':digest(final_rules)==host_rules_hash,
   'receipt_node_present':parent.has_node(NodeID(residual_node_id)),
   'returned_graph_count':[parent.node_count(),parent.edge_count()],
   'host_graph_delta_counts':[len(final_graph['nodes'])-len(host_graph_before['nodes']),len(final_graph['edges'])-len(host_graph_before['edges'])]},
  'timing_ns':{'fork':fork_ns,'induce':induce_ns,'ground':ground_ns,'journal':journal_ns,'adopt':adopt_ns}}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(int(args[1])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ResidualCowCandidateRehydrationV1Lock','sources':frozen(),'workers':4,
   'backend':'shared_graph_pages'},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker ID')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for i in range(lock['workers']):
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker {i}: {p.stderr[-3000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ResidualCowCandidateRehydrationV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n');print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
