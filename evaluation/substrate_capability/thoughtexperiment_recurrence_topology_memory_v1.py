#!/usr/bin/env python3
"""Compare recurrence repair rehearsal memory across equal-size graph topologies."""
from __future__ import annotations
import gc, hashlib, json, os, subprocess, sys, threading, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=Path(__file__).resolve();RAW=ROOT/'evaluation/reports/thoughtexperiment_recurrence_topology_memory_v1_raw_20261001.json'
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_topology_memory_v1_lock_20261001.json'
BACKENDS={'full_copy':'fork_full_copy_experiment','shared_pages':'fork_shared_graph_pages_experiment'}
TOPOLOGIES=('path','star','balanced_tree');SIZES=(100000,200000)
SOURCES=('docs/research/engine_substrate/THOUGHTEXPERIMENT_RECURRENCE_TOPOLOGY_MEMORY_V1_PREREG_20261001.md','evaluation/substrate_capability/thoughtexperiment_recurrence_topology_memory_v1.py','evaluation/substrate_capability/thoughtexperiment_recurrence_offer_idempotence_v1.py','substrate/boot_core.py','substrate/seed_loader.py','seeds/minting_recurrence_ledger.json','runners/dsl/python/substrate_rs/__init__.py','runners/dsl/src/cow_paged_vec.rs','runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','domains/engine_provenance.py')
def sha(path):return 'sha256:'+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def smaps():
 out={}
 for line in Path('/proc/self/smaps_rollup').read_text().splitlines():
  k,sep,v=line.partition(':')
  if sep and k in {'Rss','Pss','Private_Clean','Private_Dirty','Shared_Clean','Shared_Dirty','Swap'}:out[k]=int(v.strip().split()[0])*1024
 return out
def worker(size,topology,backend,rep):
 from evaluation.substrate_capability.thoughtexperiment_recurrence_offer_idempotence_v1 import make_case
 before={p:sha(ROOT/p) for p in SOURCES};primary,native,authored,_candidate,fault_only=make_case()
 if not fault_only:raise RuntimeError('fault fixture mismatch')
 nodes=[]
 for i in range(size):
  node=primary.add_node('ThoughtexperimentNoise',{'ordinal':i,'partition':i%32,'payload':'x'*24})
  if i:
   source={'path':i-1,'star':0,'balanced_tree':(i-1)//2}[topology]
   primary.add_edge_unchecked(nodes[source],'te_noise_next',node)
  nodes.append(node)
 revision=native.experiment_graph_rule_revision();counts=(native.node_count(),native.edge_count())
 rules=json.dumps(native.export_rules(),sort_keys=True,default=str);gc.collect();baseline=smaps();samples=[baseline];stop=threading.Event()
 def sample():
  while not stop.wait(.01):
   try:samples.append(smaps())
   except (OSError,ValueError):pass
 monitor=threading.Thread(target=sample,daemon=True);monitor.start();start=time.perf_counter_ns()
 branch=getattr(primary,BACKENDS[backend])();bn=branch._inner
 idx=next(i for i,r in enumerate(bn.export_rules()) if r.get('name')=='mrl_offer_due_once' and r.get('active',True))
 removed=bool(bn.remove_rule(idx));bn.add_rule(authored);closure=[int(bn.run_rules(100)) for _ in range(5)]
 target=next(n for n in branch.nodes('PredicateRecurrenceCandidate') if branch.node(n)['attrs'].get('recurrence_key')=='audit-key')
 offers=len(list(branch.neighbours(target,'has_mint_offer')));fixed=int(bn.run_rules(100))
 restored=next(r for r in bn.export_rules() if r.get('name')=='mrl_offer_due_once' and r.get('active',True)).get('where')==authored.get('where')
 duration=(time.perf_counter_ns()-start)/1e6;samples.append(smaps());del branch;gc.collect();samples.append(smaps());stop.set();monitor.join();after=smaps()
 peak={k:max(x.get(k,0) for x in samples) for k in baseline};after_hashes={p:sha(ROOT/p) for p in SOURCES}
 return {'pid':os.getpid(),'size':size,'topology':topology,'backend':backend,'replicate':rep,'edges_added':size-1,'samples':len(samples),'duration_ms':duration,'fault_only_guard_removed':fault_only,'fault_rule_removed':removed,'restored_authored_where':restored,'closure_progress':closure,'offer_count':offers,'fixedpoint_progress':fixed,'primary_revision_unchanged':native.experiment_graph_rule_revision()==revision,'primary_counts_unchanged':(native.node_count(),native.edge_count())==counts,'primary_rules_unchanged':json.dumps(native.export_rules(),sort_keys=True,default=str)==rules,'baseline_bytes':baseline,'peak_bytes':peak,'peak_delta_bytes':{k:peak[k]-baseline[k] for k in baseline},'after_drop_bytes':after,'source_hashes_before':before,'source_hashes_after':after_hashes,'sources_stable':before==after_hashes}
def main():
 if len(sys.argv)==6 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2]),sys.argv[3],sys.argv[4],int(sys.argv[5])),sort_keys=True,default=str));return 0
 from domains.engine_provenance import build_is_stale,rust_source_fingerprint
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
 env={**os.environ,'PYTHONPATH':f"{ROOT/'runners/dsl/python'}:{ROOT}"};rows=[]
 for size in SIZES:
  for topology in TOPOLOGIES:
   for rep in range(3):
    order=list(BACKENDS) if rep%2==0 else list(reversed(BACKENDS))
    for backend in order:
     p=subprocess.run([sys.executable,str(RUNNER),'--worker',str(size),topology,backend,str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True)
     rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 lock=json.loads(LOCK.read_text());locked_ok=all(sha(ROOT/p)==value for p,value in lock['sources'].items())
 from substrate_rs import _native
 native_binary=Path(_native.__file__).resolve()
 binary_locked=sha(native_binary)==lock['native_binary']['sha256']
 cell={(s,t,b):[r for r in rows if (r['size'],r['topology'],r['backend'])==(s,t,b)] for s in SIZES for t in TOPOLOGIES for b in BACKENDS}
 gates={'36_unique_fresh_processes':len(rows)==36 and len({r['pid'] for r in rows})==36,'locked_inputs_stable':locked_ok and binary_locked and all(r['sources_stable'] for r in rows),'repair_oracle':all(r['fault_only_guard_removed'] and r['fault_rule_removed'] and r['restored_authored_where'] and r['offer_count']==1 and r['fixedpoint_progress']==0 for r in rows),'primary_isolation':all(r['primary_revision_unchanged'] and r['primary_counts_unchanged'] and r['primary_rules_unchanged'] for r in rows),'backend_outcome_parity':all(len({(tuple(r['closure_progress']),r['offer_count'],r['fixedpoint_progress']) for r in cell[(s,t,'full_copy')]+cell[(s,t,'shared_pages')]})==1 for s in SIZES for t in TOPOLOGIES),'matched_graph_cardinality':all(r['edges_added']==r['size']-1 for r in rows)}
 binary=native_binary
 capture={'schema':'ThoughtexperimentRecurrenceTopologyMemoryV1','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'engine_fingerprint':rust_source_fingerprint(str(ROOT)),'native_binary':{'path':str(binary),'sha256':sha(binary)},'lock_sha256':sha(LOCK),'protocol':{'sizes':list(SIZES),'topologies':list(TOPOLOGIES),'backends':list(BACKENDS),'repeats_per_cell':3,'warmups':0,'sampler_ms':10},'source_hashes':rows[0]['source_hashes_before'],'rows':rows,'gates':gates}
 RAW.parent.mkdir(parents=True,exist_ok=True);RAW.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'gates':gates,'rows':len(rows),'raw':str(RAW)},indent=2,sort_keys=True));return 0 if all(gates.values()) else 1
if __name__=='__main__':raise SystemExit(main())
