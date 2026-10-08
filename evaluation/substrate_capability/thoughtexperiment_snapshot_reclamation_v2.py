#!/usr/bin/env python3
"""Measure full-process memory through reusable snapshot and drop stages."""
from __future__ import annotations
import argparse,gc,hashlib,json,os,platform,random,statistics,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"runners/dsl/python")]
from domains.engine_provenance import build_is_stale,rust_source_fingerprint
from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
BACKENDS=("full_copy","shared_slabs","shared_graph_pages")
SOURCES=("evaluation/substrate_capability/thoughtexperiment_snapshot_reclamation_v2.py","evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py","domains/engine_provenance.py","domains/imagination.py","domains/self_correction.py","domains/collapse_model.py","runners/dsl/python/substrate_rs/__init__.py","runners/dsl/src/cow_paged_vec.rs","runners/dsl/src/cow_sharded_map.rs","runners/dsl/src/graph.rs","runners/dsl/src/substrate.rs","runners/dsl/src/py.rs","runners/dsl/src/persist.rs")
def sha(path):return "sha256:"+hashlib.sha256(Path(path).read_bytes()).hexdigest()
def smaps():
 values={}
 for line in Path("/proc/self/smaps_rollup").read_text(encoding="ascii").splitlines():
  name,sep,tail=line.partition(":")
  if sep and name in {"Rss","Pss","Pss_Anon","Pss_File","Pss_Shmem","Private_Clean","Private_Dirty","Shared_Clean","Shared_Dirty","Swap"}:values[name]=int(tail.strip().split()[0])*1024
 required={"Rss","Pss","Private_Clean","Private_Dirty","Shared_Clean","Shared_Dirty"}
 if required-values.keys():raise RuntimeError(f"smaps_rollup missing {sorted(required-values.keys())}")
 return values
def worker(size,backend,iteration):
 substrate,native,*_=make_fixture(size);revision=tuple(native.experiment_graph_rule_revision());counts=(native.node_count(),native.edge_count());gc.collect();samples={"primary_baseline":smaps()}
 snapshot=substrate._snapshot_with_backend(backend);samples["snapshot_live"]=smaps()
 branch=snapshot.fork();branch_before=(branch.node_count(),branch.edge_count());samples["branch_live"]=smaps()
 branch.add_node("SnapshotReclamationBranchWrite",{"size":size,"iteration":iteration});branch_after=(branch.node_count(),branch.edge_count());samples["branch_written"]=smaps()
 primary_ok=tuple(native.experiment_graph_rule_revision())==revision and (native.node_count(),native.edge_count())==counts
 isolation=(primary_ok and branch_after==(branch_before[0]+1,branch_before[1]) and len(branch.nodes("SnapshotReclamationBranchWrite"))==1)
 del branch;gc.collect();samples["branch_dropped_snapshot_live"]=smaps()
 later=snapshot.fork();later_ok=(later.node_count(),later.edge_count())==counts and len(later.nodes("SnapshotReclamationBranchWrite"))==0
 del later;gc.collect();samples["verification_branch_dropped"]=smaps()
 del snapshot;gc.collect();samples["snapshot_dropped"]=smaps()
 del substrate,native;gc.collect();samples["primary_dropped"]=smaps()
 deltas={stage:{k:v-samples["primary_baseline"].get(k,0) for k,v in row.items()} for stage,row in samples.items() if stage!="primary_baseline"}
 return {"size_added_nodes":size,"backend":backend,"iteration":iteration,"pid":os.getpid(),"baseline_counts":list(counts),"branch_before":list(branch_before),"branch_after":list(branch_after),"primary_revision_unchanged":primary_ok,"branch_mutation_isolated":isolation,"later_fork_sees_captured_base":later_ok,"samples_bytes":samples,"stage_delta_from_baseline_bytes":deltas}
def median(values):return statistics.median(values)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--sizes",nargs="+",type=int,default=[0,10000,50000]);p.add_argument("--repeats",type=int,default=5);p.add_argument("--warmups",type=int,default=1);p.add_argument("--seed",type=int,default=20261001);p.add_argument("--out",type=Path);p.add_argument("--worker",action="store_true",help=argparse.SUPPRESS);p.add_argument("--worker-size",type=int,help=argparse.SUPPRESS);p.add_argument("--worker-backend",choices=BACKENDS,help=argparse.SUPPRESS);p.add_argument("--worker-iteration",type=int,default=0,help=argparse.SUPPRESS);a=p.parse_args()
 if a.worker:
  if a.worker_size is None or a.worker_backend is None:p.error("worker mode requires size and backend")
  print(json.dumps(worker(a.worker_size,a.worker_backend,a.worker_iteration),sort_keys=True));return
 if a.repeats<3 or a.warmups<0 or any(x<0 for x in a.sizes):p.error("repeats >= 3; sizes and warmups nonnegative")
 if not Path("/proc/self/smaps_rollup").exists():raise SystemExit("Linux /proc/self/smaps_rollup required")
 stale=build_is_stale(str(ROOT))
 if stale:raise SystemExit("stale native engine: "+"; ".join(stale))
 rng=random.Random(a.seed);rows=[];schedule=[];exe=Path(__file__).resolve()
 for size in a.sizes:
  for it in range(a.warmups+a.repeats):
   order=list(BACKENDS);rng.shuffle(order)
   for backend in order:
    command=[sys.executable,str(exe),"--worker","--worker-size",str(size),"--worker-backend",backend,"--worker-iteration",str(it)]
    done=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
    if done.returncode:raise RuntimeError(f"worker failed size={size} backend={backend} iteration={it}: {done.stderr[-4000:]}")
    row=json.loads(done.stdout);schedule.append({"size":size,"iteration":it,"backend":backend})
    if it>=a.warmups:rows.append(row)
    if not row["branch_mutation_isolated"] or not row["later_fork_sees_captured_base"]:raise RuntimeError(f"semantic gate failed: {size=} {backend=} {it=}")
 summaries=[];metrics=("Rss","Pss","Private_Clean","Private_Dirty","Shared_Clean","Shared_Dirty","Swap")
 for size in a.sizes:
  for backend in BACKENDS:
   cell=[x for x in rows if x["size_added_nodes"]==size and x["backend"]==backend]
   med={stage:{key:median([x["stage_delta_from_baseline_bytes"][stage].get(key,0) for x in cell]) for key in metrics} for stage in cell[0]["stage_delta_from_baseline_bytes"]}
   summaries.append({"size_added_nodes":size,"backend":backend,"measured_repeats":a.repeats,"median_stage_delta_bytes":med,"all_isolation_and_later_fork_gates_pass":all(x["branch_mutation_isolated"] and x["later_fork_sees_captured_base"] for x in cell)})
 capture={"schema":"ThoughtexperimentSnapshotReclamationV2","host":{"platform":platform.platform(),"machine":platform.machine()},"engine_fingerprint":rust_source_fingerprint(str(ROOT)),"runner":{"path":str(exe),"sha256":sha(exe)},"sources":{x:sha(ROOT/x) for x in SOURCES},"protocol":{"sizes_added_nodes":a.sizes,"backends":list(BACKENDS),"repeats":a.repeats,"warmups":a.warmups,"seed":a.seed,"snapshot_lifecycle":["primary baseline","snapshot retained","branch retained","branch written","branch dropped while snapshot retained","verification fork dropped","snapshot dropped","primary dropped"],"semantics":"branch-local mutation, unchanged primary, and later fork reproducing captured revision","memory":"Linux current smaps_rollup RSS/PSS and clean/dirty private/shared values; current, not kernel peak"},"schedule":schedule,"summaries":summaries,"rows":rows}
 rendered=json.dumps(capture,indent=2,sort_keys=True)+"\n"
 if a.out:dest=a.out if a.out.is_absolute() else ROOT/a.out;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(rendered,encoding="utf-8");print(dest.relative_to(ROOT) if dest.is_relative_to(ROOT) else dest)
 else:print(rendered,end="")
if __name__=="__main__":main()
