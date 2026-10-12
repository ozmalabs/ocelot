#!/usr/bin/env python3
"""Measure recurrence-repair throughput across candidate counts."""
from __future__ import annotations
import copy,gc,hashlib,json,os,platform,subprocess,sys,threading,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_scale_v1_lock_20261001.json';RAW=ROOT/'evaluation/reports/thoughtexperiment_recurrence_candidate_scale_v1_raw_20261001.json'
BACKENDS={'full_copy':'fork_full_copy_experiment','shared_pages':'fork_shared_graph_pages_experiment'};FANOUTS=(1,8);CANDIDATE_COUNTS=(1,16,64,128);SIZE=100000;CANDIDATES=int(os.environ.get('TE_CANDIDATES','64'))
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_CANDIDATE_SCALE_V1_PREREG_20261001.md','docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_SCALE_V1_RESULTS_20261001.md','evaluation/substrate_capability/thoughtexperiment_recurrence_candidate_scale_v1.py','evaluation/substrate_capability/thoughtexperiment_recurrence_scale_v1.py','evaluation/substrate_capability/thoughtexperiment_recurrence_offer_idempotence_v1.py','substrate/boot_core.py','substrate/seed_loader.py','seeds/minting_recurrence_ledger.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','domains/engine_provenance.py')
def sha(path):return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def host_info():
 try:cpu_max=Path('/sys/fs/cgroup/cpu.max').read_text().strip()
 except OSError:cpu_max=None
 return {'platform':platform.platform(),'logical_cpus':os.cpu_count(),'cgroup_cpu_max':cpu_max}
def smaps():
 out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in {'Rss','Pss','Private_Clean','Private_Dirty','Shared_Clean','Shared_Dirty','Swap'}:out[k]=int(v.strip().split()[0])*1024
 return out
def make_task():
 from evaluation.substrate_capability.thoughtexperiment_recurrence_offer_idempotence_v1 import make_case
 sub,native,authored,first,fault_only=make_case()
 if not fault_only:raise RuntimeError('fault fixture mismatch')
 first_attrs=copy.deepcopy(sub.node(first)['attrs']);episode=next(iter(sub.nodes('MintingRecurrenceEpisode')))
 evidence_id=next(iter(sub.neighbours(first,'supported_by_segment')));evidence_attrs=copy.deepcopy(sub.node(evidence_id)['attrs'])
 keys=[first_attrs['recurrence_key']]
 for i in range(1,CANDIDATES):
  key=f'audit-key-{i:03d}';keys.append(key)
  ca=copy.deepcopy(first_attrs);ca['recurrence_key']=key;ca['capability_key']=['recurrence-audit',str(i)]
  ev=copy.deepcopy(evidence_attrs);ev['recurrence_key']=key;ev['capability_key']=['recurrence-audit',str(i)]
  candidate=sub.add_node('PredicateRecurrenceCandidate',ca);evidence=sub.add_node('ResidualSegmentEvidence',ev)
  sub.add_edge_unchecked(episode,'has_predicate_recurrence_candidate',candidate);sub.add_edge_unchecked(candidate,'supported_by_segment',evidence)
 previous=None
 for i in range(SIZE):
  node=sub.add_node('ThoughtexperimentNoise',{'ordinal':i,'partition':i%32,'payload':'x'*24})
  if previous is not None:sub.add_edge_unchecked(previous,'te_noise_next',node)
  previous=node
 return sub,native,authored,keys
def branch_job(primary,authored,backend):
 cpu_started=time.thread_time_ns()
 branch=getattr(primary,BACKENDS[backend])();native=branch._inner
 idx=next(i for i,r in enumerate(native.export_rules()) if r.get('name')=='mrl_offer_due_once' and r.get('active',True))
 removed=bool(native.remove_rule(idx));native.add_rule(authored);progress=[int(native.run_rules(100)) for _ in range(5)]
 counts=[]
 candidates={branch.node(n)['attrs'].get('recurrence_key'):n for n in branch.nodes('PredicateRecurrenceCandidate')}
 for key in range(CANDIDATES):
  wanted='audit-key' if key==0 else f'audit-key-{key:03d}'
  candidate=candidates[wanted]
  counts.append(len(list(branch.neighbours(candidate,'has_mint_offer'))))
 fixed=int(native.run_rules(100));restored=next(r for r in native.export_rules() if r.get('name')=='mrl_offer_due_once' and r.get('active',True)).get('where')==authored.get('where')
 valid=removed and restored and all(x==1 for x in counts) and fixed==0
 del branch;return {'valid':valid,'offer_counts':counts,'closure_progress':progress,'fixedpoint_progress':fixed,'restored_authored_where':restored,'thread_cpu_ms':(time.thread_time_ns()-cpu_started)/1e6}
def wave(primary,authored,backend,fanout,concurrent):
 gc.collect();baseline=smaps();samples=[baseline];stop=threading.Event()
 def sampler():
  while not stop.wait(.01):
   try:samples.append(smaps())
   except (OSError,ValueError):pass
 monitor=threading.Thread(target=sampler,daemon=True);monitor.start();start=time.perf_counter_ns()
 if concurrent:
  with ThreadPoolExecutor(max_workers=fanout) as pool:results=list(pool.map(lambda _:branch_job(primary,authored,backend),range(fanout)))
 else:results=[branch_job(primary,authored,backend) for _ in range(fanout)]
 elapsed=(time.perf_counter_ns()-start)/1e6;samples.append(smaps());stop.set();monitor.join();after=smaps()
 peak={k:max(x.get(k,0) for x in samples) for k in baseline}
 return {'mode':'concurrent' if concurrent else 'sequential','wall_ms':elapsed,'experiments_per_second':fanout/(elapsed/1000),'sum_thread_cpu_ms':sum(r['thread_cpu_ms'] for r in results),'cpu_overlap_factor':sum(r['thread_cpu_ms'] for r in results)/elapsed,'valid_branches':sum(r['valid'] for r in results),'branch_results':results,'samples':len(samples),'baseline_bytes':baseline,'peak_bytes':peak,'peak_delta_bytes':{k:peak[k]-baseline[k] for k in baseline},'after_bytes':after}
def worker(backend,fanout,rep):
 before={p:sha(ROOT/p) for p in SOURCES};primary,native,authored,keys=make_task();counts=(native.node_count(),native.edge_count());revision=native.experiment_graph_rule_revision();rules=json.dumps(native.export_rules(),sort_keys=True,default=str)
 first='sequential' if rep%2==0 else 'concurrent';modes=[first,'concurrent' if first=='sequential' else 'sequential'];results={}
 for mode in modes:results[mode]=wave(primary,authored,backend,fanout,mode=='concurrent')
 stable=(native.node_count(),native.edge_count())==counts and native.experiment_graph_rule_revision()==revision and json.dumps(native.export_rules(),sort_keys=True,default=str)==rules
 after={p:sha(ROOT/p) for p in SOURCES}
 return {'pid':os.getpid(),'backend':backend,'fanout':fanout,'replicate':rep,'order':modes,'task_candidate_count':len(keys),'noise_nodes':SIZE,'candidate_count_protocol':CANDIDATES,'results':results,'primary_unchanged':stable,'source_hashes_before':before,'source_hashes_after':after,'sources_stable':before==after}
def main():
 if len(sys.argv)==5 and sys.argv[1]=='--worker':print(json.dumps(worker(sys.argv[2],int(sys.argv[3]),int(sys.argv[4])),sort_keys=True,default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};rows=[]
 jobs=[(count,backend,fanout,rep) for rep in range(3) for count in CANDIDATE_COUNTS for fanout in FANOUTS for backend in (('full_copy','shared_pages') if rep%2==0 else ('shared_pages','full_copy'))]
 for count,backend,fanout,rep in jobs:
  worker_env={**env,'TE_CANDIDATES':str(count)}
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',backend,str(fanout),str(rep)],cwd=ROOT,env=worker_env,text=True,capture_output=True,check=True)
  rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
 lock=json.loads(LOCK.read_text());source_lock=all(sha(ROOT/p)==h for p,h in lock['sources'].items())
 from substrate_rs import _native
 binary=Path(_native.__file__).resolve();binary_lock=sha(binary)==lock['native_binary']['sha256']
 groups={(b,c,f):[r for r in rows if (r['backend'],r['task_candidate_count'],r['fanout'])==(b,c,f)] for b in BACKENDS for c in CANDIDATE_COUNTS for f in FANOUTS}
 def signature(result):return [(x['valid'],x['offer_counts'],x['closure_progress'],x['fixedpoint_progress'],x['restored_authored_where']) for x in result['branch_results']]
 gates={'48_unique_fresh_processes':len(rows)==48 and len({r['pid'] for r in rows})==48,'source_binary_lock':source_lock and binary_lock and all(r['sources_stable'] for r in rows),'primary_isolation':all(r['primary_unchanged'] for r in rows),'all_branches_correct':all(r['results'][m]['valid_branches']==r['fanout'] for r in rows for m in ('sequential','concurrent')),'sequential_concurrent_semantic_parity':all(signature(r['results']['sequential'])==signature(r['results']['concurrent']) for r in rows),'candidate_count_matches_protocol':all(r['task_candidate_count']==r['candidate_count_protocol'] for r in rows),'finite_positive_measurements':all(v['wall_ms']>0 and v['experiments_per_second']>0 and v['sum_thread_cpu_ms']>=0 and v['cpu_overlap_factor']>=0 and v['peak_delta_bytes']['Pss']>=0 and v['peak_delta_bytes']['Rss']>=0 for r in rows for v in r['results'].values())}
 summaries=[]
 for backend in BACKENDS:
  for candidate_count in CANDIDATE_COUNTS:
   for fanout in FANOUTS:
    rs=groups[(backend,candidate_count,fanout)];row={'backend':backend,'candidate_count':candidate_count,'fanout':fanout}
    for mode in ('sequential','concurrent'):
     vals=[r['results'][mode] for r in rs];row[mode]={'median_wall_ms':sorted(v['wall_ms'] for v in vals)[1],'median_experiments_per_second':sorted(v['experiments_per_second'] for v in vals)[1],'median_cpu_overlap_factor':sorted(v['cpu_overlap_factor'] for v in vals)[1],'median_sum_thread_cpu_ms':sorted(v['sum_thread_cpu_ms'] for v in vals)[1],'median_peak_delta_pss_mib':sorted(v['peak_delta_bytes']['Pss']/1048576 for v in vals)[1],'median_peak_delta_rss_mib':sorted(v['peak_delta_bytes']['Rss']/1048576 for v in vals)[1],'median_samples':sorted(v['samples'] for v in vals)[1]}
    row['concurrent_speedup_vs_sequential']=row['sequential']['median_wall_ms']/row['concurrent']['median_wall_ms'];summaries.append(row)
 capture={'schema':'ThoughtexperimentRecurrenceCandidateScaleV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':host_info(),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':sha(binary)},'lock_sha256':sha(LOCK),'protocol':{'noise_nodes':SIZE,'candidate_counts':list(CANDIDATE_COUNTS),'backends':list(BACKENDS),'fanouts':list(FANOUTS),'repeats_per_cell':3,'gil_release_on_branch_fork':True,'candidate_lookup':'single-pass key index per branch','warmups':0,'sampler_ms':10},'source_hashes':rows[0]['source_hashes_before'],'rows':rows,'summaries':summaries,'gates':gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates':gates,'summaries':summaries,'raw':str(RAW)},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
