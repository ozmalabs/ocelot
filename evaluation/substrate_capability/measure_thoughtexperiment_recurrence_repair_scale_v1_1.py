#!/usr/bin/env python3
"""Explicit-release follow-up for the million-node recurrence repair probe."""
import gc,hashlib,importlib.util,json,os,platform,subprocess,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'evaluation/substrate_capability')]
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_repair_memory_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_repair_memory_v1_lock_20261001.json'
AMENDMENT=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_REPAIR_SCALE_V1_1_AMENDMENT_20261002.md'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_REPAIR_SCALE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_repair_scale_v1_1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_repair_scale_v1_1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_1_20261002.json'
SIZE=1_000_000;BACKENDS=('full_copy','shared_pages');REPEATS=3

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('thoughtexperiment_recurrence_repair_memory_v1_1_base',BASE)
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
 from substrate_rs import _native
 base=load_base()
 return {'runner':sha(Path(__file__).resolve()),'protocol':sha(PROTOCOL),'amendment':sha(AMENDMENT),'analyzer':sha(ANALYZER),
  'base_runner':sha(BASE),'base_lock':sha(BASE_LOCK),'base_sources':json.loads(BASE_LOCK.read_text())['sources'],
  'loaded_native_binary':sha(Path(_native.__file__).resolve()),'base_source_list':list(base.SOURCES)}
def smaps():
 out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in {'Rss','Pss','Private_Dirty','Private_Clean','Shared_Dirty','Shared_Clean','Swap'}:out[k]=int(v.strip().split()[0])*1024
 return out
def worker(backend,rep):
 from thoughtexperiment_recurrence_offer_idempotence_v1 import make_case
 base=load_base();before={p:sha(ROOT/p) for p in base.SOURCES}
 primary,native,authored,_candidate,fault_only=make_case()
 if not fault_only:raise RuntimeError('fault fixture did not remove only the authored guard')
 previous=None
 for i in range(SIZE):
  node=primary.add_node('ThoughtexperimentNoise',{'ordinal':i,'partition':i%32,'payload':'x'*24})
  if previous is not None:primary.add_edge_unchecked(previous,'te_noise_next',node)
  previous=node
 candidate=next(n for n in primary.nodes('PredicateRecurrenceCandidate') if primary.node(n)['attrs'].get('recurrence_key')=='audit-key')
 revision=native.experiment_graph_rule_revision();counts=(native.node_count(),native.edge_count())
 rules=json.dumps(native.export_rules(),sort_keys=True,default=str)
 del previous;gc.collect();baseline=smaps();samples=[baseline];stop=threading.Event()
 def sample_loop():
  while not stop.wait(.01):
   try:samples.append(smaps())
   except (OSError,ValueError):pass
 monitor=threading.Thread(target=sample_loop,daemon=True);monitor.start();start=time.perf_counter_ns()
 branch=getattr(primary,base.BACKENDS[backend])();bn=branch._inner
 idx=next(i for i,r in enumerate(bn.export_rules()) if r.get('name')=='mrl_offer_due_once' and r.get('active',True))
 removed=bool(bn.remove_rule(idx));bn.add_rule(authored)
 closure=[int(bn.run_rules(100)) for _ in range(5)]
 branch_candidate=next(n for n in branch.nodes('PredicateRecurrenceCandidate') if branch.node(n)['attrs'].get('recurrence_key')=='audit-key')
 offer_count=len(list(branch.neighbours(branch_candidate,'has_mint_offer')))
 fixedpoint=int(bn.run_rules(100));active=next(r for r in bn.export_rules() if r.get('name')=='mrl_offer_due_once' and r.get('active',True))
 duration_ms=(time.perf_counter_ns()-start)/1e6;samples.append(smaps())
 active_where_restored=active.get('where')==authored.get('where')
 primary_revision_unchanged=native.experiment_graph_rule_revision()==revision
 primary_counts_unchanged=(native.node_count(),native.edge_count())==counts
 primary_rules_unchanged=json.dumps(native.export_rules(),sort_keys=True,default=str)==rules
 del branch_candidate,active,bn,branch
 gc.collect();samples.append(smaps());stop.set();monitor.join();after=smaps()
 peak={k:max(row.get(k,0) for row in samples) for k in baseline}
 after_hashes={p:sha(ROOT/p) for p in base.SOURCES}
 return {'pid':os.getpid(),'size':SIZE,'backend':backend,'replicate':rep,'sample_interval_ms':10,'sample_count':len(samples),
  'duration_ms':duration_ms,'fault_only_guard_removed':fault_only,'removed_fault_rule':removed,
  'restored_authored_where':active_where_restored,'closure_progress':closure,'offer_count':offer_count,'fixedpoint_progress':fixedpoint,
  'primary_revision_unchanged':primary_revision_unchanged,'primary_counts_unchanged':primary_counts_unchanged,
  'primary_rules_unchanged':primary_rules_unchanged,'baseline_bytes':baseline,'peak_bytes':peak,
  'peak_delta_bytes':{k:peak[k]-baseline[k] for k in baseline},'after_drop_bytes':after,
  'branch_and_inner_references_deleted':True,'source_hashes_before':before,'source_hashes_after':after_hashes,'sources_stable':before==after_hashes}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceRepairScaleV1_1Lock','sources':frozen(),'size':SIZE,
   'backends':BACKENDS,'repeats':REPEATS,'sampler_ms':10,'closure_sweeps':5,'release':'delete branch wrapper and inner substrate'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker BACKEND REPEAT')
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if not Path('/proc/self/smaps_rollup').exists():raise SystemExit('Linux smaps_rollup required')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for rep in range(REPEATS):
  order=list(BACKENDS) if rep%2==0 else list(reversed(BACKENDS))
  for backend in order:
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',backend,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1200)
   if p.returncode:raise RuntimeError(f'worker {backend}/{rep}: {p.stderr[-2500:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]));print(f'completed {backend} repeat={rep}; {len(rows)}/6',flush=True)
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceRepairScaleV1_1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
