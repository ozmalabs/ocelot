#!/usr/bin/env python3
"""Measure residual-workflow memory and latency across CoW fanout."""
from __future__ import annotations
import gc,hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/RESIDUAL_COW_FANOUT_MEMORY_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_fanout_memory_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_fanout_memory_v1_20261002.json'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_residual_cow_fanout_memory_v1.py'
BACKENDS=('full_copy','shared_graph_pages');SIZE=100000;FANOUTS=(1,4,16);REPEATS=3
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def frozen():
 import measure_residual_cow_candidate_rehydration_v1 as rehydrate
 import measure_residual_cow_return_v1 as prior
 from substrate_rs import _native
 return {'candidate_rehydration_sources':rehydrate.frozen(),'prior_cow_sources':prior.frozen(),
  'runner':sha(RUNNER),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
  'native_binary':sha(Path(_native.__file__).resolve())}
def smaps():
 wanted={'Rss','Pss','Private_Dirty','Private_Clean','Shared_Dirty','Shared_Clean','Swap'};out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in wanted:out[k]=int(v.strip().split()[0])*1024
 if wanted-out.keys():raise RuntimeError(f"missing smaps fields: {sorted(wanted-out.keys())}")
 return out
class BranchAgent:
 def __init__(self,branch,original):self.s=branch;self.inner=branch._inner;self.agent=original.agent
def worker(backend,fanout,rep):
 import measure_residual_to_composer_cue_derivation_v1 as cue
 import thoughtexperiment_a8_generalization_adapters_v1 as adapters
 import thoughtexperiment_a8_proposal_bridge_v1_4 as bridge
 import domains.reflective_faculty as rf
 from domains.engine_provenance import build_is_stale
 if build_is_stale(str(ROOT)):raise RuntimeError('stale native engine')
 before=frozen();ctx=adapters.prepare('navigation',rep,'train');sub=ctx['sub'];native=ctx['native'];target=ctx['target']
 from measure_residual_to_composer_grounding_boundary_v1 import action_outcome
 actual=action_outcome(ctx,{'case':'up','target':[4.,5.],'expected':'Up'})
 if (actual.get('actual'),actual.get('expected'))!=('Down','Up'):raise RuntimeError('fault control failed')
 for n in range(SIZE):sub.add_node('ResidualScaleNoise',{'ordinal':n,'payload':'n'*24})
 graph_before=sub.graph_to_dict();rules_before=native.export_rules();revision=sub.experiment_graph_rule_revision()
 stages={'host_baseline':smaps()};branches=[];fork_times=[];operation_times=[]
 fork_fn=sub.fork_full_copy_experiment if backend=='full_copy' else sub.fork_shared_graph_pages_experiment
 for j in range(fanout):
  t=time.perf_counter_ns();branch=fork_fn();fork_times.append(time.perf_counter_ns()-t)
  agent=BranchAgent(branch,ctx['agent'])
  branches.append({'branch':branch,'agent':agent,'target_before':bridge._target_rule(branch._inner,target)})
 stages['branches_forked']=smaps()
 for j,row in enumerate(branches):
  branch=row['branch'];agent=row['agent'];branch.begin_experiment_delta_journal()
  obs=[['actual','Down'],['expected','Up'],*[[p,'present'] for p in cue.CUE]]
  t=time.perf_counter_ns();ind=rf.induce_concern(agent,obs);branch.checkpoint_experiment_delta_journal()
  ground=rf.ground_concern(agent,[ind['capability_key']]);operation_times.append(time.perf_counter_ns()-t)
  structural=ground.get('structural_variant') or {}
  if not (structural.get('built') and structural.get('kind')=='flip_comparison' and structural.get('removed_rule')==target):
   raise RuntimeError(f'candidate proposal failed at branch {j}')
  row.update({'candidate':{'label':'fanout_candidate','rules':{target:structural['rule']}},
   'branch_target_unchanged':row['target_before']==bridge._target_rule(branch._inner,target)})
  if not row['branch_target_unchanged']:raise RuntimeError('branch target rule changed during proposal')
 stages['candidate_generated']=smaps()
 # A matched held-out score runs on every branch-produced candidate.
 scores=[]
 for j,row in enumerate(branches):
  score_ctx=adapters.prepare('navigation',rep,'heldout');score=adapters.score(score_ctx,row['candidate'])
  if not (score.get('oracle_pass') and score.get('receipt_verified') and score.get('primary_preserved')):
   raise RuntimeError(f'heldout score failed at branch {j}')
  scores.append(score);del score_ctx
  rule= row['candidate']['rules'][target]
  row['branch'].add_node('ThoughtexperimentCandidateResidual',{
   'schema':'thoughtexperiment_candidate_residual.v1','target_rule':target,'operator':'flip_comparison',
   'candidate_json':json.dumps(row['candidate'],sort_keys=True,separators=(',',':')),
   'candidate_digest':digest(row['candidate']),'validated_before_return':1.0,'heldout_pass':1.0})
  row['delta']=row['branch'].finish_experiment_delta_journal()
 stages['all_branches_validated_and_packaged']=smaps()
 graph_unchanged=(digest(sub.graph_to_dict())==digest(graph_before));rules_unchanged=(digest(native.export_rules())==digest(rules_before))
 branch_target_ok=all(row['branch_target_unchanged'] for row in branches)
 if not (graph_unchanged and rules_unchanged):raise RuntimeError('host changed during exploration')
 t=time.perf_counter_ns();sub.apply_experiment_graph_delta(revision,branches[0]['delta']['derived_only']);adopt_ns=time.perf_counter_ns()-t
 if digest(native.export_rules())!=digest(rules_before):raise RuntimeError('host rewrite-rule store changed on return')
 stages['one_residual_returned']=smaps()
 returned_ids={int(n['id']) for n in branches[0]['delta']['derived_only']['nodes_added']}
 # Dropping every branch must not remove the adopted graph residual.
 for row in branches:
  row.pop('branch',None);row.pop('agent',None)
 branches.clear()
 del row,agent,branch,ground,ind,structural,score
 gc.collect();stages['unreturned_branches_dropped']=smaps()
 from substrate_rs import NodeID
 if any(not sub.has_node(NodeID(i)) for i in returned_ids):raise RuntimeError('adopted residual was reclaimed with branch')
 after_graph=sub.graph_to_dict();after_rules=native.export_rules()
 source_after=frozen()
 return {'backend':backend,'fanout':fanout,'repeat':rep,'pid':os.getpid(),'noise_nodes':SIZE,
  'source_before':before,'source_after':source_after,'source_stable':before==source_after,
  'outcomes':{'branch_count':fanout,'all_heldout_pass':len(scores)==fanout,
   'all_branch_targets_unchanged':branch_target_ok,
   'all_host_rules_unchanged':digest(after_rules)==digest(rules_before),
   'host_unchanged_until_return':graph_unchanged and rules_unchanged,
   'one_residual_returned':len(returned_ids)>0,'returned_nodes':len(returned_ids),
   'host_graph_counts_before': [len(graph_before['nodes']),len(graph_before['edges'])],
   'host_graph_counts_after':[len(after_graph['nodes']),len(after_graph['edges'])]},
  'timing_ns':{'forks':fork_times,'candidate_operation':operation_times,'single_return':adopt_ns},
  'memory_bytes':stages,'peak_rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  row=worker(args[1],int(args[2]),int(args[3]));print(json.dumps(row,sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ResidualCowFanoutMemoryV1Lock','sources':frozen(),'size':SIZE,
   'fanouts':FANOUTS,'backends':BACKENDS,'repeats':REPEATS},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker BACKEND FANOUT REPEAT')
 if not Path('/proc/self/smaps_rollup').exists():raise SystemExit('Linux smaps_rollup required')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 schedule=[(b,f,r) for r in range(REPEATS) for f in FANOUTS for b in BACKENDS]
 for b,f,r in schedule:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',b,str(f),str(r)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=240)
  if p.returncode:raise RuntimeError(f'worker {b}/{f}/{r}: {p.stderr[-2500:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ResidualCowFanoutMemoryV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'schedule':[list(x) for x in schedule],'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
