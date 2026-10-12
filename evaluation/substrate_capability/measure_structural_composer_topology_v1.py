#!/usr/bin/env python3
"""Compare full composer latency across matched-count unrelated graph topologies."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,time
from array import array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/STRUCTURAL_COMPOSER_TOPOLOGY_V1_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/structural_composer_topology_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/structural_composer_topology_v1_20261002.json'
FAMILIES=('recurrence','conversation','actor_recipient_edge','actor_recipient_identity')
LAYOUTS=('cyclic','hub','clustered','random_regular')
NODES=100000;EDGES_PER_NODE=4;REPLICATES=3;WARMUPS=2;ORDER_SEED=61008
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 return {'runner':sha(RUNNER),'preregistration':sha(PREREG),'base_harness':base.frozen(),
  'python':sys.version,'platform':platform.platform()}
def rss():
 try:return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
 except (OSError,ValueError,IndexError):return None
def compose_warmup(family,tag):
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 import domains.reflective_faculty as rf
 c=base.context(family,0,'topology_warmup');key=f'{tag}_{family}';base.add_axis(c['sub'],key,base.CUES[family])
 rf.compose_general_structural_variant(c['sub'],[key],tag)
def add_noise_edges(native,nodes,layout,rep):
 n=len(nodes);out=array('I',[0])*n;ind=array('I',[0])*n;cluster_width=1000
 rng=random.Random(ORDER_SEED+rep);count=0;within=0
 if layout=='hub':
  specs=((j%100,1000+((j//100)%(n-1000)),(j//100000)) for j in range(n*EDGES_PER_NODE))
 elif layout=='random_regular':
  def random_specs():
   for i in range(n):
    targets=[x if x<i else x+1 for x in rng.sample(range(n-1),EDGES_PER_NODE)]
    for k,t in enumerate(targets):yield i,t,k
  specs=random_specs()
 elif layout in ('cyclic','clustered'):
  def regular_specs():
   for i in range(n):
    for k in range(EDGES_PER_NODE):
     if layout=='cyclic':t=(i+k+1)%n
     else:
      start=(i//cluster_width)*cluster_width
      t=start+((i-start+k+1)%cluster_width);nonlocal_within[0]+=1
     yield i,t,k
  nonlocal_within=[0];specs=regular_specs()
 else:raise ValueError(layout)
 for i,j,k in specs:
  native.add_edge_unchecked(nodes[i],f'topology_noise_{k}',nodes[j]);out[i]+=1;ind[j]+=1;count+=1
 if layout=='clustered':within=nonlocal_within[0]
 return {'edge_count':count,'max_out_degree':max(out),'max_in_degree':max(ind),
  'within_cluster_edges':within,'within_cluster_fraction':within/count if count else None}
def worker(family,layout,rep):
 for k in range(WARMUPS):compose_warmup(family,f'warm{rep}_{k}')
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 import domains.reflective_faculty as rf
 c=base.context(family,0,'topology_capture');sub=c['sub'];native=c['native'];rss_start=rss()
 t=time.perf_counter_ns();nodes=[sub.add_node('UnrelatedTopologyNode',{'ordinal':i}) for i in range(NODES)]
 node_ns=time.perf_counter_ns()-t;rss_nodes=rss();t=time.perf_counter_ns()
 facts=add_noise_edges(native,nodes,layout,rep);edge_ns=time.perf_counter_ns()-t;rss_edges=rss()
 key=f'topology_{family}_{layout}_{rep}';base.add_axis(sub,key,base.CUES[family]);before=native.export_rules()
 rss_before=rss();t=time.perf_counter_ns();result=rf.compose_general_structural_variant(sub,[key],key)
 compose_ns=time.perf_counter_ns()-t;rss_after=rss()
 return {'family':family,'layout':layout,'replicate':rep,'nodes':NODES,**facts,
  'edges_per_node':EDGES_PER_NODE,'node_insert_ns':node_ns,'edge_insert_ns':edge_ns,'compose_ns':compose_ns,
  'rss_start_bytes':rss_start,'rss_after_nodes_bytes':rss_nodes,'rss_after_edges_bytes':rss_edges,
  'rss_before_compose_bytes':rss_before,'rss_after_compose_bytes':rss_after,
  'rss_node_delta_bytes':rss_nodes-rss_start if rss_start is not None and rss_nodes is not None else None,
  'rss_edge_delta_bytes':rss_edges-rss_nodes if rss_nodes is not None and rss_edges is not None else None,
  'built':bool(result.get('built')),'target':result.get('removed_rule'),'operator':result.get('kind'),
  'site':result.get('site'),'primary_rules_unchanged':native.export_rules()==before}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],args[2],int(args[3])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  cells=[(f,l,r) for f in FAMILIES for l in LAYOUTS for r in range(REPLICATES)];random.Random(ORDER_SEED).shuffle(cells)
  expected={'recurrence':['mrl_offer_due_once','add_edge_identity_guard','out candidate has_mint_offer any endpoint'],
   'conversation':['reply_to_adjacency_pair','add_edge_identity_guard','in m responds_to any endpoint'],
   'actor_recipient_edge':['mint_actor_goal_recipient','add_edge_identity_guard','out agent has_actor_goal any endpoint'],
   'actor_recipient_identity':['mint_actor_goal_recipient','add_edge_identity_guard','out agent has_actor_goal attributes actor+verb']}
  LOCK.write_text(json.dumps({'schema':'StructuralComposerTopologyV1Lock','sources':frozen(),
   'families':FAMILIES,'layouts':LAYOUTS,'nodes':NODES,'edges_per_node':EDGES_PER_NODE,
   'replicates':REPLICATES,'warmups_per_trial':WARMUPS,'order_seed':ORDER_SEED,
   'capture_order':[list(x) for x in cells],'expected':expected,
   'matched_shape':'directed graph, 100k nodes, 400k edges, four edge types at 100k each; topology varies degree/clustering'},
   indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker FAMILY LAYOUT REP')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'};rows=[]
 for f,l,r in lock['capture_order']:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',f,l,str(r)],cwd=ROOT,env=env,text=True,capture_output=True,timeout=300)
  if p.returncode:raise RuntimeError(f'worker {f}/{l}/{r}: {p.stderr[-2000:]}')
  rows.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'StructuralComposerTopologyV1Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
