#!/usr/bin/env python3
"""Measure graph-resident edge identity site materialization."""
from __future__ import annotations
import hashlib,json,platform,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
RUNNER=Path(__file__).resolve()
OUT=ROOT/'evaluation/reports/graph_site_materialization_scaling_v1_20261002.json'
LOCK=ROOT/'evaluation/substrate_capability/graph_site_materialization_scaling_v1_lock_20261002.json'
SIZES=(0,1000,10000); WIDTHS=(8,32,64); WARMUPS=1; TRIALS=5

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 return {'domains/edit_ops.py':sha(ROOT/'domains/edit_ops.py'),
  'domains/reflective_faculty.py':sha(ROOT/'domains/reflective_faculty.py'),
  'substrate/boot_core.py':sha(ROOT/'substrate/boot_core.py'),
  'runner':sha(RUNNER),'native_binary':sha(Path(_native.__file__).resolve()),
  'python':sys.version,'platform':platform.platform()}
def synthetic_rule(m):
 attrs={f'f{i:03d}':{'__term__':{'type':'Attr','node':{'type':'Var','name':'input'},'key':f'f{i:03d}'}} for i in range(m)}
 return {'match':[['agent','has_input','input']], 'effects':[['add_node','fresh','SyntheticGoal',attrs],['add_edge','agent','has_goal','fresh']]}
def one(n,m):
 from substrate.boot_core import boot_core
 import domains.edit_ops as eo
 import domains.reflective_faculty as rf
 sub,_=boot_core(seeds=())
 for i in range(n):sub.add_node('UnrelatedScaleNoise',{'ordinal':i})
 t=time.perf_counter_ns();rf._ensure_edge_identity_sites(sub,'scale_probe',synthetic_rule(m),eo);elapsed=time.perf_counter_ns()-t
 count=sum(1 for _ in sub.nodes('EditSite'))
 return elapsed,count
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'GraphSiteMaterializationScalingV1Lock','sources':frozen(),
   'unrelated_node_counts':SIZES,'attribute_widths':WIDTHS,'warmups':WARMUPS,'trials':TRIALS,
   'scope':'_ensure_edge_identity_sites end-to-end, including extraction and adding typed EditSite graph nodes'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 rows=[]
 for n in SIZES:
  for m in WIDTHS:
   for _ in range(WARMUPS):one(n,m)
   trials=[];counts=[]
   for _ in range(TRIALS):
    ns,count=one(n,m);trials.append(ns);counts.append(count)
   expected=m+m*(m-1)//2+(1 if m>2 else 0)+1
   rows.append({'unrelated_nodes':n,'attribute_fields':m,'expected_edit_sites':expected,
    'observed_edit_sites':counts,'median_ns':int(statistics.median(trials)),'trial_ns':trials})
 if frozen()!=lock['sources']:raise SystemExit('source drift during measurement')
 OUT.write_text(json.dumps({'schema':'GraphSiteMaterializationScalingV1Results','lock_sha256':sha(LOCK),
  'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
