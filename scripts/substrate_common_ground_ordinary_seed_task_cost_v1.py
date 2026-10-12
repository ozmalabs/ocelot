#!/usr/bin/env python3
"""Current-source ordinary seed and task cost capture, counters disabled."""
from __future__ import annotations
import hashlib,json,os,platform,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_COMMON_GROUND_ORDINARY_SEED_TASK_COST_V1_PREREG_20260929.md'
FIXTURE=ROOT/'tests/fixtures/conversational_manifold/phase3_common_ground_stress.json'
SEED=ROOT/'seeds/conversation_discourse_state.json'
LOCK=ROOT/'evaluation/substrate_capability/common_ground_ordinary_seed_task_cost_v1_lock_20260929.json'
RAW=ROOT/'evaluation/reports/common_ground_ordinary_seed_task_cost_v1_raw_20260929.json'
OUT=ROOT/'evaluation/reports/common_ground_ordinary_seed_task_cost_v1_20260929.json'
ANALYZER=ROOT/'scripts/analyze_substrate_common_ground_ordinary_seed_task_cost_v1.py'
REPEATS=tuple(range(10));CAP=100_000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale
 paths=(str(PROTOCOL.relative_to(ROOT)),str(FIXTURE.relative_to(ROOT)),str(SEED.relative_to(ROOT)),
  str(Path(__file__).relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),
  'domains/discourse_state.py','domains/seed_registry.py','substrate/seed_loader.py','substrate/boot_core.py',
  'substrate/world_adapter.py','substrate/graph.py','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs',
  'runners/dsl/src/py.rs','runners/dsl/src/scale_audit.rs','runners/dsl/python/substrate_rs/_native.build.json')
 return {'files':{p:sha(ROOT/p) for p in paths},'native_sha256':sha(Path(_native.__file__).resolve()),
  'native_path':str(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),
  'build_stale':build_is_stale(str(ROOT)),
  'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def nid(x):return int(x.value if hasattr(x,'value') else x)
def worker(rep):
 full_wall=time.perf_counter_ns();full_cpu=time.process_time_ns()
 imports_wall=time.perf_counter_ns();imports_cpu=time.process_time_ns()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_core import load_seeds_into
 from domains.discourse_state import ensure_common_ground,ensure_discourse_state,open_goal,record_event
 module_import_wall=time.perf_counter_ns()-imports_wall;module_import_cpu=time.process_time_ns()-imports_cpu
 fixture_wall=time.perf_counter_ns();fixture=json.loads(FIXTURE.read_text());fixture_load_ns=time.perf_counter_ns()-fixture_wall
 t=time.perf_counter_ns();c=time.process_time_ns();a=WorldAdapter(seeds=());adapter_init_wall=time.perf_counter_ns()-t;adapter_init_cpu=time.process_time_ns()-c
 t=time.perf_counter_ns();c=time.process_time_ns();loaded=load_seeds_into(a.s,a.agent,['conversation_discourse_state']);seed_wall=time.perf_counter_ns()-t;seed_cpu=time.process_time_ns()-c
 rules=[r for r in a.inner.export_rules() if r.get('name') in {'discourse_goal_select','discourse_goal_execute','discourse_goal_resolve'} and r.get('active',True)]
 t=time.perf_counter_ns();c=time.process_time_ns();person=a.attach_chat_world('shared_user');user=person['interlocutor'];state=ensure_discourse_state(a,conversation_id='common_ground_ordinary_task',addressee=user);ensure_common_ground(a,state,addressee=user);setup_wall=time.perf_counter_ns()-t;setup_cpu=time.process_time_ns()-c
 goals=[];events=[];event_idx={};checkpoints=[];event_construction_wall=0;event_construction_cpu=0
 intended={4:0,5:0,6:0,7:1,8:1,9:1}
 for row in fixture['events']:
  i=int(row['index']);kind=row['kind'];topic='calendar' if i<5 else 'location';t=time.perf_counter_ns();c=time.process_time_ns()
  if kind=='request':
   payload={'common_ground_delta':'calendar_request'} if i==0 else None
   event=record_event(a,state,kind=kind,speaker=user,addressee=a.agent,topic=topic,expectation='action',interaction_mode=row['mode'],payload=payload)
   goal=open_goal(a,state,kind=f'task_{len(goals)}',origin_event=event,addressee=user);goals.append(goal)
  elif kind=='observation':event=record_event(a,state,kind=kind,speaker=user,addressee=a.agent,topic=topic,interaction_mode=row['mode'])
  elif kind=='assertion':event=record_event(a,state,kind=kind,speaker=user,addressee=a.agent,topic=topic,interaction_mode=row['mode'],payload={'common_ground_delta':'calendar_shared'})
  elif kind in {'selection','execution'}:event=record_event(a,state,kind=kind,speaker=a.agent,addressee=user,interaction_mode=row['mode'])
  elif kind=='action_result':
   claim='calendar_checked' if i==6 else 'location_shared'
   event=record_event(a,state,kind=kind,speaker=a.agent,addressee=user,interaction_mode=row['mode'],payload={'common_ground_delta':claim})
  else:raise RuntimeError(f'unhandled event kind {kind}')
  if i in intended:a.inner.add_edge_unchecked(event,'for_goal',goals[intended[i]])
  construct_wall=time.perf_counter_ns()-t;construct_cpu=time.process_time_ns()-c;event_construction_wall+=construct_wall;event_construction_cpu+=construct_cpu
  eid=nid(event);events.append(eid);event_idx[eid]=i
  t=time.perf_counter_ns();c=time.process_time_ns();progress=int(a.inner.run_rules(CAP));closure_wall=time.perf_counter_ns()-t;closure_cpu=time.process_time_ns()-c
  graph=a.inner.graph_to_dict();paths={str(j):sorted(event_idx[nid(x)] for x in a.inner.neighbours(g,'transitioned_by') if nid(x) in event_idx) for j,g in enumerate(goals)}
  checkpoints.append({'event_index':i,'event_id':eid,'progress_steps':progress,'closure_wall_ns':closure_wall,'closure_cpu_ns':closure_cpu,'paths':paths,'graph_digest':digest(graph),'node_count':len(graph['nodes']),'edge_count':len(graph['edges'])})
 t=time.perf_counter_ns();c=time.process_time_ns();terminal_progress=int(a.inner.run_rules(CAP));terminal_wall=time.perf_counter_ns()-t;terminal_cpu=time.process_time_ns()-c
 final_graph=a.inner.graph_to_dict();final_digest=digest(final_graph)
 final_paths={str(j):sorted(event_idx[nid(x)] for x in a.inner.neighbours(g,'transitioned_by') if nid(x) in event_idx) for j,g in enumerate(goals)}
 grounds=sorted(tuple(sorted(a.s.node(n)['attrs'].get('claims',[]))) for n in a.s.nodes('CommonGround'))
 audits={str(k):int(v) for k,v in dict(a.inner.scale_audit_snapshot()).items()}
 full_task_wall=time.perf_counter_ns()-full_wall;full_task_cpu=time.process_time_ns()-full_cpu
 return {'replicate':rep,'pid':os.getpid(),'loaded_seed_ids':sorted(loaded),'active_lifecycle_rules':[str(r['name']) for r in rules],
  'closure_api':'inner.run_rules','audit_enable_calls':0,
  'event_count':len(events),'goal_count':len(goals),'fixture_links_added':len(intended),'checkpoints':checkpoints,
  'final_paths':final_paths,'expected_paths':{'0':[4,5,6],'1':[7,8,9]},'task_oracle_pass':final_paths=={'0':[4,5,6],'1':[7,8,9]},
  'common_grounds':grounds,'expected_common_grounds':[['calendar_checked','location_shared'],['calendar_request','calendar_shared']],
  'common_ground_oracle_pass':grounds==[('calendar_checked','location_shared'),('calendar_request','calendar_shared')],
  'terminal_probe':{'progress_steps':terminal_progress,'graph_unchanged':digest(final_graph)==checkpoints[-1]['graph_digest'],'wall_ns':terminal_wall,'cpu_ns':terminal_cpu},
  'final_digest':final_digest,'final_node_count':len(final_graph['nodes']),'final_edge_count':len(final_graph['edges']),
  'scale_audit_counters':audits,'timings_ns':{'python_module_import_wall':module_import_wall,'python_module_import_cpu':module_import_cpu,
   'fixture_load':fixture_load_ns,'adapter_init_wall':adapter_init_wall,'adapter_init_cpu':adapter_init_cpu,
   'seed_load_wall':seed_wall,'seed_load_cpu':seed_cpu,'chat_state_setup_wall':setup_wall,'chat_state_setup_cpu':setup_cpu,
   'event_construction_wall_total':event_construction_wall,'event_construction_cpu_total':event_construction_cpu,
   'closure_wall_total':sum(x['closure_wall_ns'] for x in checkpoints),'closure_cpu_total':sum(x['closure_cpu_ns'] for x in checkpoints),
   'terminal_probe_wall':terminal_wall,'terminal_probe_cpu':terminal_cpu,'full_task_wall':full_task_wall,'full_task_cpu':full_task_cpu},
  'peak_rss_kib':int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
def main():
 if len(sys.argv)>1 and sys.argv[1]=='--worker':
  before=fingerprint();w=worker(int(sys.argv[2]));after=fingerprint();print(json.dumps({'before':before,'after':after,'worker':w},sort_keys=True,default=str));return 0
 if sys.argv[1:]==['--lock']:
  f=fingerprint()
  if f['build_stale']:raise SystemExit('native build is stale')
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':f},indent=2,sort_keys=True)+'\n');print(LOCK);return 0
 locked=fingerprint()
 if locked['build_stale']:raise SystemExit('native build is stale')
 if not LOCK.is_file() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale source/native lock')
 env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join((str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts'),env.get('PYTHONPATH','')));env['PYTHONHASHSEED']='0';env['OZMA_NO_LLM']='1';env['OZMA_SEED_PERSIST_DISABLED']='1'
 order=list(REPEATS);random.Random(20260929).shuffle(order);runs=[]
 for i,rep in enumerate(order,1):
  cp=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True)
  runs.append(json.loads(cp.stdout) if cp.returncode==0 else {'worker_error':cp.stderr[-4000:],'replicate':rep})
  print(f'worker {i}/10 replicate={rep} rc={cp.returncode}',flush=True)
  partial={'schema_version':1,'run_id':'common-ground-ordinary-seed-task-cost-v1-20260929','locked_inputs':locked,'post_run_inputs':fingerprint(),'runs':runs}
  RAW.with_suffix('.partial.json').write_text(json.dumps(partial,indent=2,sort_keys=True)+'\n')
 post=fingerprint();RAW.write_text(json.dumps({'schema_version':1,'run_id':'common-ground-ordinary-seed-task-cost-v1-20260929','locked_inputs':locked,'post_run_inputs':post,'runs':runs},indent=2,sort_keys=True)+'\n')
 summary={'schema_version':1,'run_id':'common-ground-ordinary-seed-task-cost-v1-20260929','locked_inputs':locked,'post_run_inputs':post,'raw_path':str(RAW.relative_to(ROOT))}
 OUT.write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
 if RAW.with_suffix('.partial.json').exists():RAW.with_suffix('.partial.json').unlink()
 print(json.dumps({'workers':len(runs),'source_stable':post==locked,'raw':str(RAW.relative_to(ROOT))},indent=2))
 return 0 if post==locked and len(runs)==10 and all('worker_error' not in x for x in runs) else 1
if __name__=='__main__':raise SystemExit(main())
