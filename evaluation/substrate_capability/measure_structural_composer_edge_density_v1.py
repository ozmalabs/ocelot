#!/usr/bin/env python3
"""Measure full structural composer sensitivity to unrelated edge density."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/STRUCTURAL_COMPOSER_EDGE_DENSITY_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/structural_composer_edge_density_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/structural_composer_edge_density_v1_20261002.json'
FAMILIES=('recurrence','conversation','actor_recipient_edge','actor_recipient_identity')
NODES=100000;DENSITIES=(0,1,4);REPLICATES=3;WARMUPS=2;ORDER_SEED=61007
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 return {'runner':sha(RUNNER),'preregistration':sha(PREREG),'base_harness':base.frozen(),
  'python':sys.version,'platform':platform.platform()}
def rss():
 try:return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
 except (OSError,ValueError,IndexError):return None
def compose_once(family,tag):
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 import domains.reflective_faculty as rf
 ctx=base.context(family,0,'edge_density_warmup');key=f'{tag}_{family}'
 base.add_axis(ctx['sub'],key,base.CUES[family]);before=ctx['native'].export_rules()
 r=rf.compose_general_structural_variant(ctx['sub'],[key],tag)
 return r,ctx['native'].export_rules()==before
def worker(family,density,rep):
 for i in range(WARMUPS):compose_once(family,f'warm{rep}_{i}')
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 import domains.reflective_faculty as rf
 ctx=base.context(family,0,'edge_density_capture');sub=ctx['sub'];native=ctx['native']
 rss_start=rss();t=time.perf_counter_ns()
 nodes=[sub.add_node('UnrelatedDensityNode',{'ordinal':i}) for i in range(NODES)]
 node_ns=time.perf_counter_ns()-t;rss_nodes=rss();edge_count=NODES*density;t=time.perf_counter_ns()
 for i,src in enumerate(nodes):
  for k in range(density):native.add_edge_unchecked(src,f'unrelated_density_edge_{k}',nodes[(i+k+1)%NODES])
 edge_ns=time.perf_counter_ns()-t;rss_edges=rss()
 key=f'edge_density_{family}_{density}_{rep}';base.add_axis(sub,key,base.CUES[family])
 before=native.export_rules();rss_before_compose=rss();t=time.perf_counter_ns()
 result=rf.compose_general_structural_variant(sub,[key],key);compose_ns=time.perf_counter_ns()-t;rss_after_compose=rss()
 return {'family':family,'nodes':NODES,'edges':edge_count,'edges_per_node':density,'replicate':rep,
  'node_insert_ns':node_ns,'edge_insert_ns':edge_ns,'compose_ns':compose_ns,
  'node_insert_per_s':NODES/(node_ns/1e9),'edge_insert_per_s':edge_count/(edge_ns/1e9) if edge_count else None,
  'rss_start_bytes':rss_start,'rss_after_nodes_bytes':rss_nodes,'rss_after_edges_bytes':rss_edges,
  'rss_before_compose_bytes':rss_before_compose,'rss_after_compose_bytes':rss_after_compose,
  'rss_nodes_delta_bytes':rss_nodes-rss_start if rss_nodes is not None and rss_start is not None else None,
  'rss_edges_delta_bytes':rss_edges-rss_nodes if rss_edges is not None and rss_nodes is not None else None,
  'rss_compose_delta_bytes':rss_after_compose-rss_before_compose if rss_after_compose is not None and rss_before_compose is not None else None,
  'built':bool(result.get('built')),'target':result.get('removed_rule'),'operator':result.get('kind'),
  'site':result.get('site'),'primary_rules_unchanged':native.export_rules()==before}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2]),int(args[3])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  cells=[(f,d,r) for f in FAMILIES for d in DENSITIES for r in range(REPLICATES)]
  random.Random(ORDER_SEED).shuffle(cells)
  expected={'recurrence':['mrl_offer_due_once','add_edge_identity_guard','out candidate has_mint_offer any endpoint'],
   'conversation':['reply_to_adjacency_pair','add_edge_identity_guard','in m responds_to any endpoint'],
   'actor_recipient_edge':['mint_actor_goal_recipient','add_edge_identity_guard','out agent has_actor_goal any endpoint'],
   'actor_recipient_identity':['mint_actor_goal_recipient','add_edge_identity_guard','out agent has_actor_goal attributes actor+verb']}
  LOCK.write_text(json.dumps({'schema':'StructuralComposerEdgeDensityV1Lock','sources':frozen(),
   'families':FAMILIES,'nodes':NODES,'edges_per_node':DENSITIES,'replicates':REPLICATES,
   'warmups_per_trial':WARMUPS,'order_seed':ORDER_SEED,'capture_order':[list(x) for x in cells],
   'expected':expected,'edge_shape':'directed cyclic offsets; distinct edge type per offset; inserted with add_edge_unchecked'},
   indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker FAMILY DENSITY REP')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for f,d,r in lock['capture_order']:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',f,str(d),str(r)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
  if p.returncode:raise RuntimeError(f'worker {f}/{d}/{r}: {p.stderr[-2000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'StructuralComposerEdgeDensityV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
