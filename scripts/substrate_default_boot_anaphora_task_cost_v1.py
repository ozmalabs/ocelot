#!/usr/bin/env python3
"""Default-boot two-turn anaphora task cost, with scale counters disabled."""
from __future__ import annotations
import hashlib,json,os,random,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_DEFAULT_BOOT_ANAPHORA_TASK_COST_V1_PREREG_20260929.md'
TEST_ORACLE=ROOT/'tests/test_intent_migrated.py'
LOCK=ROOT/'evaluation/substrate_capability/default_boot_anaphora_task_cost_v1_lock_20260929.json'
RAW=ROOT/'evaluation/reports/default_boot_anaphora_task_cost_v1_raw_20260929.json'
ANALYZER=ROOT/'scripts/analyze_substrate_default_boot_anaphora_task_cost_v1.py'
OUT=ROOT/'evaluation/reports/default_boot_anaphora_task_cost_v1_20260929.json'
REPEATS=tuple(range(10));CAP=100_000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seed_paths():
 from substrate.boot_core import CORE_SEEDS
 from substrate.seeds import REGISTRY
 import domains.seed_registry
 closure=REGISTRY.resolve((*CORE_SEEDS,'intent'))
 paths=sorted({f'seeds/{s.id}.json' for s in closure})
 missing=[p for p in paths if not (ROOT/p).is_file()]
 if missing:raise RuntimeError(f'missing seed manifest files: {missing}')
 return paths
def fingerprint():
 from substrate_rs import _native
 from domains.engine_provenance import build_is_stale
 seedfiles=seed_paths()
 paths=tuple(seedfiles)+(str(PROTOCOL.relative_to(ROOT)),str(TEST_ORACLE.relative_to(ROOT)),
  str(Path(__file__).relative_to(ROOT)),str(ANALYZER.relative_to(ROOT)),
  'substrate/world_adapter.py','substrate/boot_core.py','substrate/seed_loader.py','substrate/seeds.py',
  'domains/seed_registry.py','domains/engine_provenance.py','domains/language_world.py',
  'runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs',
  'runners/dsl/src/scale_audit.rs','runners/dsl/python/substrate_rs/_native.build.json')
 return {'files':{p:sha(ROOT/p) for p in paths},'native_sha256':sha(Path(_native.__file__).resolve()),
  'native_path':str(Path(_native.__file__).resolve()),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),
  'build_stale':build_is_stale(str(ROOT)),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def digest(g):return hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def nid(x):return int(x.value if hasattr(x,'value') else x)
def seed_ids(wa):
 out=set()
 for n in wa.s.nodes('Seed'):
  out.add(str(wa.s.node(n)['attrs'].get('id')))
 for n in wa.s.nodes('SeedSummary'):
  sid=wa.s.node(n)['attrs'].get('seed_id')
  if sid:out.add(str(sid))
 return sorted(out)
def task_projection(wa,mid):
 mentions=[n for n in wa.inner.neighbours(mid,'has_mention') if wa.s.node(n)['attrs'].get('text')=='it']
 refs=[]
 for mention in mentions:
  refs.extend(wa.inner.neighbours(mention,'refers_to'))
 names=sorted(str(wa.s.node(n)['attrs'].get('name')) for n in refs if wa.s.has_node(n))
 intent=wa.intent_of(mid);about=[] if intent is None else list(wa.inner.neighbours(intent,'about_concept'))
 aboutnames=sorted(str(wa.s.node(n)['attrs'].get('name')) for n in about)
 target=[r for r in wa.inner.export_rules() if r.get('name')=='rule_anaphoric_it_resolves_to_prior_about_concept' and r.get('active',True)]
 order=[] if len(target)!=1 else [list(e) for e in target[0]['match']]
 return {'it_mention_count':len(mentions),'it_refers_to_names':names,'intent_exists':intent is not None,
  'intent_about_concept_names':aboutnames,'target_rule_count':len(target),'target_rule_match_order':order}
def worker(rep):
 full_wall=time.perf_counter_ns();full_cpu=time.process_time_ns()
 imports_wall=time.perf_counter_ns();imports_cpu=time.process_time_ns()
 from substrate.world_adapter import WorldAdapter
 from substrate.boot_core import CORE_SEEDS
 module_import_wall=time.perf_counter_ns()-imports_wall;module_import_cpu=time.process_time_ns()-imports_cpu
 t=time.perf_counter_ns();c=time.process_time_ns();wa=WorldAdapter();adapter_wall=time.perf_counter_ns()-t;adapter_cpu=time.process_time_ns()-c
 initial_seeds=seed_ids(wa)
 t=time.perf_counter_ns();c=time.process_time_ns();mid1=wa.receive_utterance('the question matters',speech_act='statement',speaker='user');receive1_wall=time.perf_counter_ns()-t;receive1_cpu=time.process_time_ns()-c
 after_receive1_seeds=seed_ids(wa)
 t=time.perf_counter_ns();c=time.process_time_ns();progress1=int(wa.comprehend());comprehend1_wall=time.perf_counter_ns()-t;comprehend1_cpu=time.process_time_ns()-c
 t=time.perf_counter_ns();c=time.process_time_ns();mid2=wa.receive_utterance('answer it',speech_act='statement',speaker='user');receive2_wall=time.perf_counter_ns()-t;receive2_cpu=time.process_time_ns()-c
 after_receive2_seeds=seed_ids(wa)
 t=time.perf_counter_ns();c=time.process_time_ns();progress2=int(wa.comprehend());comprehend2_wall=time.perf_counter_ns()-t;comprehend2_cpu=time.process_time_ns()-c
 projection=task_projection(wa,mid2);task_graph=wa.inner.graph_to_dict();task_digest=digest(task_graph)
 task_oracle=projection['it_refers_to_names']==['question'] and projection['intent_exists'] and 'question' in projection['intent_about_concept_names']
 task_wall=time.perf_counter_ns()-full_wall;task_cpu=time.process_time_ns()-full_cpu
 t=time.perf_counter_ns();c=time.process_time_ns();settle_progress=int(wa.inner.run_rules(CAP));settle_wall=time.perf_counter_ns()-t;settle_cpu=time.process_time_ns()-c
 settled_graph=wa.inner.graph_to_dict();settled_digest=digest(settled_graph)
 t=time.perf_counter_ns();c=time.process_time_ns();probe_progress=int(wa.inner.run_rules(CAP));probe_wall=time.perf_counter_ns()-t;probe_cpu=time.process_time_ns()-c
 probe_graph=wa.inner.graph_to_dict();probe_digest=digest(probe_graph)
 audit={str(k):int(v) for k,v in dict(wa.inner.scale_audit_snapshot()).items()}
 return {'replicate':rep,'pid':os.getpid(),'default_core_seed_ids':list(CORE_SEEDS),
  'initial_seed_ids':initial_seeds,'after_first_receive_seed_ids':after_receive1_seeds,
  'after_second_receive_seed_ids':after_receive2_seeds,'turns':[{'message_id':nid(mid1),'receive_wall_ns':receive1_wall,'receive_cpu_ns':receive1_cpu,'comprehend_progress':progress1,'comprehend_wall_ns':comprehend1_wall,'comprehend_cpu_ns':comprehend1_cpu},
   {'message_id':nid(mid2),'receive_wall_ns':receive2_wall,'receive_cpu_ns':receive2_cpu,'comprehend_progress':progress2,'comprehend_wall_ns':comprehend2_wall,'comprehend_cpu_ns':comprehend2_cpu}],
  'task_projection':projection,'task_oracle_pass':task_oracle,'task_graph_digest':task_digest,
  'post_task_settle':{'progress_steps':settle_progress,'wall_ns':settle_wall,'cpu_ns':settle_cpu,'graph_digest':settled_digest},
  'terminal_probe':{'progress_steps':probe_progress,'wall_ns':probe_wall,'cpu_ns':probe_cpu,'graph_unchanged':probe_digest==settled_digest,'graph_digest':probe_digest},
  'scale_audit_counters':audit,'graph_size':{'nodes':len(probe_graph['nodes']),'edges':len(probe_graph['edges'])},
  'timings_ns':{'python_module_import_wall':module_import_wall,'python_module_import_cpu':module_import_cpu,
   'default_adapter_init_wall':adapter_wall,'default_adapter_init_cpu':adapter_cpu,
   'first_receive_wall':receive1_wall,'first_receive_cpu':receive1_cpu,'first_comprehend_wall':comprehend1_wall,'first_comprehend_cpu':comprehend1_cpu,
   'second_receive_wall':receive2_wall,'second_receive_cpu':receive2_cpu,'second_comprehend_wall':comprehend2_wall,'second_comprehend_cpu':comprehend2_cpu,
   'two_turn_task_wall':task_wall,'two_turn_task_cpu':task_cpu,'post_task_settle_wall':settle_wall,'post_task_settle_cpu':settle_cpu,
   'terminal_probe_wall':probe_wall,'terminal_probe_cpu':probe_cpu},
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
  RAW.with_suffix('.partial.json').write_text(json.dumps({'schema_version':1,'run_id':'default-boot-anaphora-task-cost-v1-20260929','locked_inputs':locked,'post_run_inputs':fingerprint(),'runs':runs},indent=2,sort_keys=True)+'\n')
 post=fingerprint();RAW.write_text(json.dumps({'schema_version':1,'run_id':'default-boot-anaphora-task-cost-v1-20260929','locked_inputs':locked,'post_run_inputs':post,'runs':runs},indent=2,sort_keys=True)+'\n')
 OUT.write_text(json.dumps({'schema_version':1,'run_id':'default-boot-anaphora-task-cost-v1-20260929','locked_inputs':locked,'post_run_inputs':post,'raw_path':str(RAW.relative_to(ROOT))},indent=2,sort_keys=True)+'\n')
 if RAW.with_suffix('.partial.json').exists():RAW.with_suffix('.partial.json').unlink()
 print(json.dumps({'workers':len(runs),'source_stable':post==locked,'raw':str(RAW.relative_to(ROOT))},indent=2))
 return 0 if post==locked and len(runs)==10 and all('worker_error' not in x for x in runs) else 1
if __name__=='__main__':raise SystemExit(main())
