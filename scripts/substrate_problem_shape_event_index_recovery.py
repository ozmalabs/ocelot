#!/usr/bin/env python3
"""Checkpoint, rebuild derived ProblemShape index, and compare resumed closure."""
from __future__ import annotations
import argparse,hashlib,json,os,platform,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from substrate_problem_shape_induction_economics import pump,sha,rss_bytes
from substrate_problem_shape_population_scale import STATEMENTS
from substrate_problem_shape_all_transitions import indexed_rules,PS_RULES
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_EVENT_INDEX_RECOVERY_PREREG_20260925.md'
LOCK=ROOT/'evaluation/substrate_capability/problem_shape_event_index_recovery_lock_20260925.json'
CANDIDATE=ROOT/'scripts/substrate_problem_shape_all_transitions.py'
SEEDS=[ROOT/'seeds/problem_shape_growth.json',ROOT/'seeds/shape_decode_loop.json',ROOT/'seeds/bigville_cast100.json']

def wire(agent):
 from domains import solver_dispatch as sd
 agent.register_reflex_response('question_pursue',lambda ag:ag._question_pursue_advance())
 agent.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))

def productions(native):
 for name,src,et,tgt in [
  ('index','ProblemShapeObservation','indexed_problem_shape','ProblemShapeKeyIndex'),
  ('index_reverse','ProblemShapeKeyIndex','indexed_problem_shape_observation','ProblemShapeObservation'),
  ('pending','Agent','problem_shape_pending_decode','ProblemShapeObservation'),
  ('decoded','Agent','problem_shape_decoded','ProblemShapeObservation'),
  ('residual','Agent','problem_shape_residual_candidate','ProblemShapeObservation')]:
  native.add_production({'provenance':'recovery_probe:'+name,'src':{'type':src,'var':'s'},'edge_type':et,'tgt':{'type':tgt,'var':'t'}})

def prepare(size=8):
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_all import load_all_seeds
 from domains import solver_dispatch as sd
 from domains import problem_decomposition as pdec
 from substrate_rs import _native
 agent=WorldAdapter(seeds=());load_all_seeds(agent);wire(agent)
 sub,native,Native=agent.s,agent.inner,_native.Substrate
 productions(native)
 seed=json.loads((ROOT/'seeds/problem_shape_growth.json').read_text())
 rules=indexed_rules(native,seed)
 for name in ('ps_decode','ps_recognize','ps_residual','ps_mint','ps_redecode'):native.add_rule(rules[name])
 scaffolds=[]
 for statement in STATEMENTS[:3]:
  g=sd.mint_solve_deduction_goal(agent,statement);result=pump(agent,g)
  if result['status']!='resolved':raise RuntimeError('scaffold did not resolve')
  scaffolds.append(g)
 schemas=[sd._solve_caps(agent)[g]['result']['node'] for g in scaffolds]
 shared=pdec.project_deduction_shared_attr(sub,schemas);complete=pdec.project_deduction_complete(sub,schemas)
 tasks=[]
 for i in range(size):
  if i==0:candidates,bound=[shared,complete],1
  elif i==1:candidates,bound=[complete],0
  else:candidates,bound=[shared],5+i
  tasks.append(sd.mint_solve_decompose_goal(agent,candidates,bound=bound))
 Native.scale_audit_set_enabled(True);Native.scale_audit_set_per_rule_enabled(True)
 return agent,tasks,Native

def observe(agent,goal,label,index):
 from domains import problem_shape as ps
 s,native=agent.s,agent.inner
 obs=ps.observe(agent,goal,run=False)
 if obs is None:raise RuntimeError('observer refused goal')
 key=str(s.node(obs)['attrs']['key'])
 ix=index.get(key)
 if ix is None:ix=s.add_node('ProblemShapeKeyIndex',{'key':key,'support_count':0});index[key]=ix
 count=int(s.node(ix)['attrs']['support_count'])+1;s.set_attr(ix,'support_count',count)
 s.add_edge(obs,'indexed_problem_shape',ix);s.add_edge(ix,'indexed_problem_shape_observation',obs)
 s.add_edge(agent.agent,'problem_shape_pending_decode',obs)
 native.run_rules()
 s.add_node('NativeProblemShapeReceipt',{'schema':'native_problem_shape_receipt_v1','cluster':'problem_shape.observation_decode','provenance':'native_rule_readback:problem_shape','native_rule':'problem_shape_growth_native_decode','native_steps':['observe_goal','run_rules','readback'],'outcome_source':'native_rule_readback','python_outcome_selection':False})
 return {'goal_id':int(goal.value),'observation_id':int(obs.value),'key':key,'status_at_settle':s.node(obs)['attrs'].get('status')}

def rebuild_index(agent):
 s=agent.s
 observations=list(s.nodes('ProblemShapeObservation'))
 for ix in list(s.nodes('ProblemShapeKeyIndex')):s.remove_node(ix)
 groups={}
 for obs in observations:
  key=str(s.node(obs)['attrs']['key']);groups.setdefault(key,[]).append(obs)
 mapping={}
 for key,obs_nodes in groups.items():
  ix=s.add_node('ProblemShapeKeyIndex',{'key':key,'support_count':len(obs_nodes)});mapping[key]=ix
  for obs in obs_nodes:
   s.add_edge(obs,'indexed_problem_shape',ix);s.add_edge(ix,'indexed_problem_shape_observation',obs)
 return mapping

def snapshot(agent,tasks,records,arm,checkpoint_bytes=0,restore_details=None):
 from substrate_rs import _native
 s,native=agent.s,agent.inner
 observations=[]
 for r in records:
  oid=_native.NodeID(r['observation_id']);a=s.node(oid)['attrs']
  about_goal_ids=sorted(int(x.value) for x in s.neighbours(oid,'about_goal'))
  observations.append({'goal_id':r['goal_id'],'observation_id':r['observation_id'],'about_goal_ids':about_goal_ids,'key':a.get('key'),'status':a.get('status'),'covered_by':a.get('covered_by'),'decoded_epoch':a.get('decoded_epoch')})
 observations.sort(key=lambda x:x['observation_id'])
 shapes=sorted([{'name':s.node(n)['attrs'].get('name'),'support':s.node(n)['attrs'].get('support'),'minted':s.node(n)['attrs'].get('minted')} for n in s.nodes('ProblemShape') if float(s.node(n)['attrs'].get('minted',0))>0],key=lambda x:x['name'] or '')
 indexes=sorted([{'key':s.node(n)['attrs']['key'],'support_count':int(s.node(n)['attrs']['support_count'])} for n in s.nodes('ProblemShapeKeyIndex')],key=lambda x:x['key'])
 edge_types=['problem_shape_pending_decode','problem_shape_decoded','problem_shape_residual_candidate']
 events={et:sum(1 for e in s.graph_to_dict()['edges'] if e.get('type')==et) for et in edge_types}
 access=native.rule_access_sets();active_rules=sorted(row[1] for row in access if row[2] and row[1] in PS_RULES)
 grouped={}
 for n in s.nodes('ProblemShapeObservation'):
  k=str(s.node(n)['attrs']['key']);grouped[k]=grouped.get(k,0)+1
 support_exact={x['key']:x['support_count'] for x in indexes}==grouped
 link_exact=all(len(s.neighbours(n,'indexed_problem_shape'))==1 for n in s.nodes('ProblemShapeObservation'))
 goal_link_exact=all(x['about_goal_ids']==[x['goal_id']] for x in observations)
 fixed=native.run_rules_report(100000,False)
 return {'arm':arm,'process_id':os.getpid(),'observations':observations,'shapes':shapes,'indexes':indexes,'event_counts':events,'active_problem_shape_rules':active_rules,'support_exact':support_exact,'one_index_link_per_observation':link_exact,'about_goal_links_exact':goal_link_exact,'fixed_point':fixed['status']=='fixed_point','settle_report':fixed,'checkpoint_bytes':checkpoint_bytes,'restore_details':restore_details or {},'rss_peak_bytes':rss_bytes()}

def worker(arm,path):
 from substrate import world_adapter as wa
 from substrate_rs import _native
 agent,tasks,Native=prepare(8);idx={};records=[]
 records.append(observe(agent,tasks[0],'decompose_1',idx))
 checkpoint_bytes=0;restore={}
 if arm=='resume_rebuild':
  save0=time.perf_counter_ns();agent.save(path);save_ns=time.perf_counter_ns()-save0;checkpoint_bytes=Path(path).stat().st_size
  pre_event_count=sum(1 for e in agent.s.graph_to_dict()['edges'] if e.get('type')=='problem_shape_residual_candidate')
  pre_support=[agent.s.node(n)['attrs'] for n in agent.s.nodes('ProblemShapeKeyIndex')]
  before_rules=sorted(row[1] for row in agent.inner.rule_access_sets() if row[2] and row[1] in PS_RULES)
  load0=time.perf_counter_ns();agent=wa.WorldAdapter.load(path);load_ns=time.perf_counter_ns()-load0;wire(agent)
  post_rules=sorted(row[1] for row in agent.inner.rule_access_sets() if row[2] and row[1] in PS_RULES)
  event_vocab=set(p['edge_type'] for p in agent.s.grammar_to_json()['productions'])
  missing_vocab=[et for et in ('problem_shape_pending_decode','problem_shape_decoded','problem_shape_residual_candidate','indexed_problem_shape') if et not in event_vocab]
  restored_candidate_events=sum(1 for e in agent.s.graph_to_dict()['edges'] if e.get('type')=='problem_shape_residual_candidate')
  rebuild0=time.perf_counter_ns();idx=rebuild_index(agent);rebuild_ns=time.perf_counter_ns()-rebuild0
  rebuilt_nodes=[agent.s.node(n)['attrs'] for n in agent.s.nodes('ProblemShapeKeyIndex')]
  restore={'pre_save_residual_event_count':pre_event_count,'pre_save_index_rows':pre_support,'rules_before':before_rules,'rules_after':post_rules,'missing_event_productions':missing_vocab,'restored_residual_event_count':restored_candidate_events,'rebuilt_index_rows':rebuilt_nodes,'save_wall_ns':save_ns,'load_wall_ns':load_ns,'derived_index_rebuild_wall_ns':rebuild_ns}
 elif arm!='uninterrupted':raise ValueError(arm)
 for i in range(1,8):
  from substrate_rs import _native as native_module
  goal=native_module.NodeID(int(tasks[i].value))
  # A restored adapter persists graph nodes, so convert ids; task objects are id wrappers only.
  from domains import solver_dispatch as sd
  result=pump(agent,goal)
  if result['status'] not in ('resolved','walled'):raise RuntimeError('goal failed after checkpoint')
  records.append(observe(agent,goal,f'decompose_{i+1}',idx))
 result=snapshot(agent,tasks,records,arm,checkpoint_bytes,restore)
 result['records']=records
 expected_rules=sorted(PS_RULES)
 expected_obs=[{'status':'recognized','covered_by':'ps_has_bound=yes'} for _ in range(8)]
 obs_ok=[{'status':x['status'],'covered_by':x['covered_by']} for x in result['observations']]==expected_obs
 shape_ok=result['shapes']==[{'name':'ps_has_bound=yes','support':2,'minted':1.0}]
 epoch=int(agent.s.node(agent.agent)['attrs'].get('problem_codebook_epoch',0))==1
 events_empty=all(v==0 for v in result['event_counts'].values())
 restore_ok=(arm=='uninterrupted' or (result['restore_details']['pre_save_residual_event_count']==1 and result['restore_details']['restored_residual_event_count']==1 and result['restore_details']['rules_before']==expected_rules and result['restore_details']['rules_after']==expected_rules and not result['restore_details']['missing_event_productions'] and result['restore_details']['rebuilt_index_rows'][0]['support_count']==1))
 result['checks']={'expected_final_observations':obs_ok,'expected_minted_shape_support':shape_ok,'codebook_epoch_one':epoch,'all_transition_events_consumed':events_empty,'restored_rules_vocabulary_event_and_rebuilt_index':restore_ok,'index_support_exact':result['support_exact'],'one_index_link_each':result['one_index_link_per_observation'],'about_goal_links_exact':result['about_goal_links_exact'],'fixed_point':result['fixed_point']}
 result['all_checks_pass']=all(result['checks'].values())
 Native.scale_audit_set_enabled(False);Native.scale_audit_set_per_rule_enabled(False)
 return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);ap.add_argument('--worker-arm',choices=['uninterrupted','resume_rebuild']);ap.add_argument('--checkpoint',type=Path);a=ap.parse_args()
 if a.worker_arm:
  if a.worker_arm=='resume_rebuild' and not a.checkpoint:ap.error('resume arm requires checkpoint path')
  r=worker(a.worker_arm,a.checkpoint);print(json.dumps(r,sort_keys=True));return 0 if r['all_checks_pass'] else 2
 if not a.output:ap.error('--output required')
 stale=subprocess.check_output([sys.executable,'-c',"from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],cwd=ROOT,text=True).strip()
 if stale:raise SystemExit(f'native build stale:\n{stale}')
 lock=json.loads(LOCK.read_text()); expected={'preregistration_sha256':sha(PREREG),'runner_sha256':sha(Path(__file__)),'candidate_runner_sha256':sha(CANDIDATE),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'seed_hashes':{p.name:sha(p) for p in SEEDS}}
 if any(lock.get(k)!=v for k,v in expected.items()):raise SystemExit('checkpoint experiment lock mismatch')
 env={**os.environ,'PYTHONPATH':f'{ROOT}:{ROOT/"runners/dsl/python"}:{ROOT/"scripts"}'}
 with tempfile.TemporaryDirectory(prefix='problem-shape-recovery-') as td:
  checkpoint=Path(td)/'mid-residual.json';arms=[]
  for arm in ('uninterrupted','resume_rebuild'):
   cmd=[sys.executable,str(Path(__file__).resolve()),'--worker-arm',arm]
   if arm=='resume_rebuild':cmd+=['--checkpoint',str(checkpoint)]
   p=subprocess.run(cmd,cwd=ROOT,env=env,text=True,capture_output=True,timeout=180)
   if p.returncode:raise RuntimeError(f'{arm} worker failed:\n{p.stdout}\n{p.stderr}')
   arms.append(json.loads(p.stdout));print(json.dumps({'arm':arm,'checks':arms[-1]['checks']}),flush=True)
 a0,a1=arms
 projected=lambda x:{'observations':sorted([{k:o[k] for k in ('goal_id','about_goal_ids','key','status','covered_by','decoded_epoch')} for o in x['observations']],key=lambda o:o['goal_id']),**{k:x[k] for k in ('shapes','indexes','event_counts','active_problem_shape_rules','fixed_point')}}
 same=projected(a0)==projected(a1)
 result={'schema_version':1,'run_id':f'problem-shape-event-index-recovery-{time.strftime("%Y%m%dT%H%M%SZ",time.gmtime())}','preregistration':{'path':str(PREREG.relative_to(ROOT)),'sha256':sha(PREREG)},'lock':{'path':str(LOCK.relative_to(ROOT)),'sha256':sha(LOCK)},'runner_sha256':sha(Path(__file__)),'candidate_runner_sha256':sha(CANDIDATE),'native_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.abi3.so'),'seed_hashes':{p.name:sha(p) for p in SEEDS},'arms':arms,'final_projections_equal':same,'distinct_processes':len({x['process_id'] for x in arms})==2,'all_checks_pass':same and len({x['process_id'] for x in arms})==2 and all(x['all_checks_pass'] for x in arms)}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'all_checks_pass':result['all_checks_pass']}));return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
