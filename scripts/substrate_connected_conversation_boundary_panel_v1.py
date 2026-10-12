#!/usr/bin/env python3
"""Fresh-process native graph census for connected discourse frame panels."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from itertools import combinations,permutations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CONNECTED_CONVERSATION_BOUNDARY_PANEL_PREREG_20260926.md';STRESS=ROOT/'tests/fixtures/conversational_manifold/phase3_common_ground_stress.json';SCALE=ROOT/'tests/fixtures/conversational_manifold/phase3_same_addressee_concurrent_goals_scale.json';RULE=ROOT/'seeds/conversation_discourse_state.json';MATERIALIZER=ROOT/'domains/discourse_state.py';BASE_RUNNER=ROOT/'scripts/substrate_discourse_connected_task_census_v1.py';LOCK=ROOT/'evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json';OUT=ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json';SIZES=(2,4,8);CAP=100_000
RUST=('graph.rs','rewrite.rs','substrate.rs','term.rs','access_trace.rs','py.rs')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nid(x):return int(x.value if hasattr(x,'value') else x)
def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def lock_inputs():
 from substrate_rs import _native
 return {'protocol_sha256':sha(PROTOCOL),'runner_sha256':sha(__file__),'base_runner_sha256':sha(BASE_RUNNER),'stress_fixture_sha256':sha(STRESS),'scale_fixture_sha256':sha(SCALE),'rule_seed_sha256':sha(RULE),'materializer_sha256':sha(MATERIALIZER),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),'rust_sources_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in RUST},'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_worktree':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip())}
def exact_width(vertices,edges):
 best=len(vertices)
 for order in permutations(vertices):
  adj={v:set() for v in vertices}
  for a,b in edges:adj[a].add(b);adj[b].add(a)
  width=0
  for v in order:
   ns=adj[v];width=max(width,len(ns))
   for a,b in combinations(ns,2):adj[a].add(b);adj[b].add(a)
   for x in ns:adj[x].discard(v)
   adj[v].clear()
  best=min(best,width)
 return best
def base_world():
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_core import load_seeds_into
 from domains.discourse_state import ensure_common_ground,ensure_discourse_state
 a=WorldAdapter(seeds=());load_seeds_into(a.s,a.agent,['conversation_discourse_state']);people=a.attach_chat_world('user');user=people['interlocutor'];state=ensure_discourse_state(a,conversation_id='boundary_panel',addressee=user);ensure_common_ground(a,state,addressee=user);return a,user,state
def run_case(case_id,rep,n=None):
 from domains.discourse_state import open_goal,record_event
 a,user,state=base_world();inner=a.inner;events=[];event_frame={};goal_frame={};goals=[];checkpoints=[];active=-1
 if case_id=='common_ground_stress':
  fixture=json.loads(STRESS.read_text());rows=fixture['events'];n_goals=2
  for row in rows:
   idx=int(row['index']);kind=row['kind'];rel=row['relation']
   if rel in ('origin','independent'):active+=1
   topic='calendar' if idx<5 else 'location';goal=None
   if kind=='request':
    gi=len(goals);ev=record_event(a,state,kind=kind,speaker=user,addressee=a.agent,topic=topic,expectation='action' if gi==0 else 'answer',interaction_mode=row.get('mode','event'));goal=open_goal(a,state,kind='act_or_clarify',origin_event=ev,addressee=user);goals.append(goal);goal_frame[nid(goal)]=active
   elif kind=='observation':ev=record_event(a,state,kind=kind,speaker=user,topic=topic,interaction_mode=row.get('mode','event'),payload={'value':'calendar_open'})
   elif kind=='assertion':ev=record_event(a,state,kind=kind,speaker=user,addressee=a.agent,topic=topic,interaction_mode=row.get('mode','event'),payload={'common_ground_delta':'calendar_shared'})
   elif kind in ('selection','execution','action_result'):
    gi=0 if idx<=6 else 1;goal=goals[gi];kwargs={'speaker':a.agent,'addressee':user,'goal':goal,'interaction_mode':row.get('mode','event')}
    if kind=='action_result':kwargs['payload']={'common_ground_delta':f'result_{gi}'}
    ev=record_event(a,state,kind=kind,**kwargs)
   else:raise ValueError(f'unsupported stress event {kind}')
   eid=nid(ev);events.append(eid);event_frame[eid]=goal_frame[nid(goal)] if goal is not None else active
   checkpoints.append(settle_checkpoint(a,eid,len(events)-1,event_frame,goal_frame,goals))
 elif case_id=='concurrent_goals':
  n_goals=int(n);goals_by=[]
  for i in range(n_goals):
   ev=record_event(a,state,kind='request',speaker=user,addressee=a.agent,topic=f'task_{i}',expectation='action',interaction_mode='asynchronous');eid=nid(ev);events.append(eid);event_frame[eid]=i;goal=open_goal(a,state,kind='act_or_clarify',origin_event=ev,addressee=user);goals_by.append(goal);goals.append(goal);goal_frame[nid(goal)]=i;checkpoints.append(settle_checkpoint(a,eid,len(events)-1,event_frame,goal_frame,goals))
  for i,goal in enumerate(goals_by):
   for kind in ('selection','execution','action_result'):
    kw={'speaker':a.agent,'addressee':user,'goal':goal,'interaction_mode':'native'}
    if kind=='action_result':kw['payload']={'common_ground_delta':f'task_{i}_done'}
    ev=record_event(a,state,kind=kind,**kw);eid=nid(ev);events.append(eid);event_frame[eid]=i;checkpoints.append(settle_checkpoint(a,eid,len(events)-1,event_frame,goal_frame,goals))
 else:raise ValueError(case_id)
 graph=inner.graph_to_dict();owner={**event_frame,**goal_frame};frames=sorted(set(owner.values()));direct=[];boundaries={};interaction=set()
 for e in graph['edges']:
  s,t=int(e['src']),int(e['tgt']);sf,tf=owner.get(s),owner.get(t)
  if sf is not None and tf is not None and sf!=tf:direct.append({'src':s,'type':e['type'],'tgt':t,'src_frame':sf,'tgt_frame':tf});interaction.add(tuple(sorted((sf,tf))))
  elif (sf is None)!=(tf is None):
   fr=sf if sf is not None else tf;bn=t if sf is not None else s;boundaries.setdefault(bn,set()).add(fr)
 for touched in boundaries.values():interaction.update(combinations(sorted(touched),2))
 rule_status=[]
 for goal in goals:
  gid=nid(goal);attrs=a.s.node(goal)['attrs'];trans=[nid(x) for x in inner.neighbours(goal,'transitioned_by')];rule_status.append({'node':gid,'frame':goal_frame[gid],'status':attrs.get('lifecycle_status'),'transition_events':trans,'transition_indices':sorted(events.index(x) for x in trans if x in events)})
 state_nodes=[{'node':nid(x),'attrs':a.s.node(x)['attrs']} for x in a.s.nodes('DiscourseState')];grounds=[{'node':nid(x),'attrs':a.s.node(x)['attrs']} for x in a.s.nodes('CommonGround')]
 return {'case_id':case_id,'goal_count':len(goals),'requested_goal_count':n,'event_count':len(events),'event_ids':events,'frame_owner':[[v,owner[v]] for v in sorted(owner)],'frame_sizes':{str(f):sum(x==f for x in owner.values()) for f in frames},'frame_count':len(frames),'final_graph':graph,'final_graph_digest':digest(graph),'checkpoints':checkpoints,'goals':rule_status,'final_state_attrs':state_nodes,'common_grounds':grounds,'direct_cross_frame_edges':direct,'boundary_nodes_by_frames':{str(k):sorted(v) for k,v in boundaries.items()},'boundary_incidence_count':sum(len(v) for v in boundaries.values()),'frame_interaction_edges':[list(e) for e in sorted(interaction)],'exact_interaction_treewidth':exact_width(frames,interaction),'total_candidate_pairs':sum(x['candidate_pairs'] for x in checkpoints),'total_term_evaluations':sum(x['term_evaluations'] for x in checkpoints),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
def settle_checkpoint(a,event_id,event_index,event_frame,goal_frame,goals):
 inner=a.inner;inner.scale_audit_reset();inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True);inner.scale_audit_set_per_rule_enabled(True);t=time.perf_counter_ns();report=dict(inner.run_rules_report(CAP,False));wall=time.perf_counter_ns()-t;counters={str(k):int(v) for k,v in dict(inner.scale_audit_snapshot()).items()};inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_set_enabled(False);g=inner.graph_to_dict();idx={int(n):int(i) for i,n in []}
 return {'event_id':event_id,'event_index':event_index,'closure':report,'wall_ns':wall,'graph_digest':digest(g),'nodes':len(g['nodes']),'edges':len(g['edges']),'candidate_pairs':counters.get('cand_enum',0),'term_evaluations':counters.get('term_evals_total',0),'goal_statuses':[a.s.node(x)['attrs'].get('lifecycle_status') for x in goals]}
def worker(rep):
 before=lock_inputs();cases=[run_case('common_ground_stress',rep)]+[run_case('concurrent_goals',rep,n) for n in SIZES];return {'replicate':rep,'pid':os.getpid(),'started_inputs':before,'cases':cases,'finished_inputs':lock_inputs()}
def main():
 if sys.argv[1:]==['--lock']:print(json.dumps({'locked_inputs':lock_inputs()},indent=2,sort_keys=True));return
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True,default=str));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1');env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
 runs=[json.loads(subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(i)],cwd=ROOT,env=env,text=True,capture_output=True,check=True,timeout=180).stdout) for i in range(3)];post=lock_inputs();cases=[c for r in runs for c in r['cases']]
 checks={'three_fresh_source_stable_workers':len({r['pid'] for r in runs})==3 and post==locked and all(r['started_inputs']==locked==r['finished_inputs'] for r in runs),'12_case_replicated_design':len(cases)==12 and all(sum(c['case_id']==cid and c.get('requested_goal_count')==n for c in cases)==3 for cid,n in [('common_ground_stress',None),('concurrent_goals',2),('concurrent_goals',4),('concurrent_goals',8)]),'complete_ownership':all(len(c['frame_owner'])==c['event_count']+c['goal_count'] and len({v for v,_ in c['frame_owner']})==len(c['frame_owner']) for c in cases),'all_closures_fixed_point':all(cp['closure'].get('status')=='fixed_point' for c in cases for cp in c['checkpoints']),'goal_resolution_and_provenance':all(all(g['status']=='resolved' and len(g['transition_indices'])==3 for g in c['goals']) for c in cases),'cross_replica_graph_and_counter_parity':all(len({c['final_graph_digest'] for c in cases if c['case_id']==cid and c.get('requested_goal_count')==n})==1 and len({json.dumps([(x['graph_digest'],x['candidate_pairs'],x['term_evaluations']) for x in c['checkpoints']],sort_keys=True) for c in cases if c['case_id']==cid and c.get('requested_goal_count')==n})==1 for cid,n in [('common_ground_stress',None),('concurrent_goals',2),('concurrent_goals',4),('concurrent_goals',8)]),'recomputed_topology_counts':all(c['frame_count']>0 and len(c['frame_interaction_edges'])==len(set(tuple(x) for x in c['frame_interaction_edges'])) and c['exact_interaction_treewidth']>=0 and c['boundary_incidence_count']==sum(len(v) for v in c['boundary_nodes_by_frames'].values()) for c in cases)}
 payload={'schema_version':1,'run_id':'substrate-connected-conversation-boundary-panel-v1-20260926','claim_boundary':'Native graph structural census of one authored common-ground stress fixture and generated same-addressee concurrent-goal workloads; not a representative everyday conversation distribution, a partitioned closure result, or a speedup claim.','locked_inputs':locked,'post_run_inputs':post,'lock_sha256':sha(LOCK),'environment':{'python':sys.version,'platform':platform.platform(),'OZMA_NO_LLM':env['OZMA_NO_LLM'],'OZMA_SEED_PERSIST_DISABLED':env['OZMA_SEED_PERSIST_DISABLED']},'configuration':{'replicates':3,'concurrent_goal_counts':SIZES,'frame_rule':'authored origin/independent markers; goal-owned continuation events follow for_goal identity'},'runs':runs,'checks':checks};OUT.write_text(json.dumps(payload,indent=2,sort_keys=True,default=str)+'\n');print(json.dumps({'output':str(OUT),'checks':checks},indent=2))
 if not all(checks.values()):raise SystemExit('capture validation failed')
if __name__=='__main__':main()
