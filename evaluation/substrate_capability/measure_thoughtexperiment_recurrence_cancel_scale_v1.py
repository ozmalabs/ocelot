#!/usr/bin/env python3
"""Cancel half of in-progress recurrence branches at million-node scale."""
import gc,hashlib,importlib.util,json,os,platform,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_wave_v1.py'
BASE_LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_wave_v1_lock_20261001.json'
BASE_CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_recurrence_parallel_wave_v1_raw_20261001.json'
PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANCEL_SCALE_V1_PREREG_20261002.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_thoughtexperiment_recurrence_cancel_scale_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_cancel_scale_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_cancel_scale_v1_20261002.json'
SIZE=1_000_000;FANOUT=8;CANCEL_COUNT=4;BACKENDS=('full_copy','shared_pages');REPEATS=3

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load_base():
 spec=importlib.util.spec_from_file_location('recurrence_parallel_wave_cancel_base_v1',BASE)
 mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod);return mod
def frozen():
 from substrate_rs import _native
 base=load_base()
 return {'runner':sha(Path(__file__).resolve()),'protocol':sha(PROTOCOL),'analyzer':sha(ANALYZER),
  'parent_runner':sha(BASE),'parent_lock_reference':sha(BASE_LOCK),'parent_capture_reference':sha(BASE_CAPTURE),
  'inherited_current_sources':{p:sha(ROOT/p) for p in base.SOURCES},'loaded_native_binary':sha(Path(_native.__file__).resolve())}
def smaps():
 out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in {'Rss','Pss','Private_Dirty','Private_Clean','Shared_Dirty','Shared_Clean','Swap'}:out[k]=int(v.strip().split()[0])*1024
 return out
def available_bytes():
 for line in Path('/proc/meminfo').read_text().splitlines():
  if line.startswith('MemAvailable:'):return int(line.split()[1])*1024
 raise RuntimeError('MemAvailable missing')
def patch_branch(primary,authored,backend):
 base=load_base();branch=getattr(primary,base.BACKENDS[backend])();native=branch._inner
 idx=next(i for i,r in enumerate(native.export_rules()) if r.get('name')=='mrl_offer_due_once' and r.get('active',True))
 removed=bool(native.remove_rule(idx));native.add_rule(authored)
 restored=next(r for r in native.export_rules() if r.get('name')=='mrl_offer_due_once' and r.get('active',True)).get('where')==authored.get('where')
 return {'branch':branch,'native':native,'removed':removed,'restored':restored}
def finish_branch(row,candidate_count):
 branch=row['branch'];native=row['native'];progress=[int(native.run_rules(100)) for _ in range(5)];counts=[]
 for i in range(candidate_count):
  key='audit-key' if i==0 else f'audit-key-{i:03d}'
  candidate=next(n for n in branch.nodes('PredicateRecurrenceCandidate') if branch.node(n)['attrs'].get('recurrence_key')==key)
  counts.append(len(list(branch.neighbours(candidate,'has_mint_offer'))))
 fixed=int(native.run_rules(100));result={'removed':row['removed'],'restored':row['restored'],'closure_progress':progress,
  'offer_counts':counts,'fixedpoint_progress':fixed,'valid':row['removed'] and row['restored'] and all(x==1 for x in counts) and fixed==0}
 row['branch']=None;row['native']=None;del branch,native;return result
def worker(backend,rep):
 import json as _json
 base=load_base();before_sources={p:sha(ROOT/p) for p in base.SOURCES}
 base.SIZE=SIZE;base.FANOUTS=(FANOUT,);base.CANDIDATES=64
 primary,native,authored,keys=base.make_task();counts=(native.node_count(),native.edge_count());revision=native.experiment_graph_rule_revision();rules=_json.dumps(native.export_rules(),sort_keys=True,default=str)
 gc.collect();baseline=smaps();samples=[baseline];stop=threading.Event()
 def sampler():
  while not stop.wait(.01):
   try:samples.append(smaps())
   except (OSError,ValueError):pass
 thread=threading.Thread(target=sampler,daemon=True);thread.start()
 started=time.perf_counter_ns()
 with ThreadPoolExecutor(max_workers=FANOUT) as pool:branches=list(pool.map(lambda _:patch_branch(primary,authored,backend),range(FANOUT)))
 all_live=smaps();cancelled=[]
 for i in range(CANCEL_COUNT):
  row=branches[i];cancelled.append({'removed':row['removed'],'restored':row['restored'],'branch_reference_present':row['branch'] is not None,'inner_reference_present':row['native'] is not None})
  row['branch']=None;row['native']=None
 gc.collect();after_cancel=smaps();survivors=branches[CANCEL_COUNT:]
 with ThreadPoolExecutor(max_workers=FANOUT-CANCEL_COUNT) as pool:outcomes=list(pool.map(lambda row:finish_branch(row,len(keys)),survivors))
 branches.clear();survivors.clear();gc.collect();after_release=smaps();wall_ms=(time.perf_counter_ns()-started)/1e6
 stop.set();thread.join();peak={k:max(r.get(k,0) for r in samples) for k in baseline}
 host_unchanged=(native.node_count(),native.edge_count())==counts and native.experiment_graph_rule_revision()==revision and _json.dumps(native.export_rules(),sort_keys=True,default=str)==rules
 after_sources={p:sha(ROOT/p) for p in base.SOURCES}
 return {'pid':os.getpid(),'backend':backend,'repeat':rep,'noise_nodes':SIZE,'candidate_count':len(keys),'fanout':FANOUT,
  'cancelled_count':len(cancelled),'cancelled_stages':cancelled,'survivor_results':outcomes,'host_unchanged':host_unchanged,
  'source_hashes_before':before_sources,'source_hashes_after':after_sources,'sources_stable':before_sources==after_sources,
  'stages_bytes':{'host_baseline':baseline,'all_branches_patched_live':all_live,'half_cancelled':after_cancel,'survivors_finished_and_released':after_release},
  'sampled_peak_bytes':peak,'sample_count':len(samples),'wall_ms':wall_ms}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  LOCK.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceCancelScaleV1Lock','sources':frozen(),
   'size':SIZE,'fanout':FANOUT,'cancel_count':CANCEL_COUNT,'backends':BACKENDS,'repeats':REPEATS,'candidate_count':64},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker BACKEND REPEAT')
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 if not Path('/proc/self/smaps_rollup').exists():raise SystemExit('Linux smaps_rollup required')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}'};rows=[]
 for rep in range(REPEATS):
  for backend in (BACKENDS if rep%2==0 else tuple(reversed(BACKENDS))):
   if available_bytes()<12*1024**3:raise SystemExit('available memory below preregistered 12 GiB floor')
   p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',backend,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=1800)
   if p.returncode:raise RuntimeError(f'worker {backend}/{rep}: {p.stderr[-3000:]}')
   rows.append(json.loads(p.stdout.strip().splitlines()[-1]));print(f'completed {backend} repeat={rep}; {len(rows)}/6',flush=True)
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'ThoughtexperimentRecurrenceCancelScaleV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
