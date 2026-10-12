#!/usr/bin/env python3
"""One fresh process for the task-derived taxonomy traversal measurement."""
from __future__ import annotations
import hashlib,json,os,resource,sys,time
from collections import defaultdict,deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT)]
SEED=ROOT/'domain_data/llm_harvest/qwen3_reaped_isa_full.json'
QUERY=ROOT/'evaluation/substrate_capability/fixtures/llm_taxonomy_traversal_scaling_v1_queries.json'

def digest(path):
 p=Path(path);h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def lock():
 from substrate_rs import _native
 paths=[Path(__file__).resolve(),SEED,QUERY,ROOT/'domains/llm_knowledge_seed.py',ROOT/'seeds/can_native_reimplementation.json',Path(_native.__file__).resolve(),ROOT/'runners/dsl/python/substrate_rs/_native.build.json']
 return [digest(p) for p in paths]
def oracle(edges,nodes):
 adj={n:[] for n in nodes}
 for a,b in edges:adj[a].append(b)
 result={};positive=[]
 for src in nodes:
  q=deque([(src,0)]);seen={src};dist={}
  while q:
   u,d=q.popleft()
   for v in adj[u]:
    if v not in seen:
     seen.add(v);dist[v]=d+1;q.append((v,d+1))
  result[src]=dist
  positive.extend((src,t,d) for t,d in dist.items() if d>=2)
 return adj,result,positive
class CountingSubstrate:
 def __init__(self,inner):self.inner=inner;self.calls=0;self.scans=0
 def reset(self):self.calls=0;self.scans=0
 def neighbours(self,node,edge_type):
  items=list(self.inner.neighbours(node,edge_type));self.calls+=1;self.scans+=len(items);return items

def build(triples):
 from substrate_rs import _native
 from domains import llm_knowledge_seed as ks
 s=_native.Substrate();t=time.perf_counter_ns()
 mt,n2n=ks.build_knowledge_mt(s,[str(ROOT/'seeds/can_native_reimplementation.json')],triples,relation='isa')
 return s,mt,n2n,time.perf_counter_ns()-t
def graph_digest(s):
 return hashlib.sha256(json.dumps(s.graph_to_dict(),sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def run(worker):
 from domains import llm_knowledge_seed as ks
 before=lock();seed=json.loads(SEED.read_text());qset=json.loads(QUERY.read_text())
 triples=[(e['subject'],e['object']) for e in seed['edges'] if e['relation']=='isa' and e['subject']!=e['object']]
 nodes=sorted({v for e in triples for v in e});adj,distances,positives=oracle(triples,nodes)
 if len(positives)!=qset['positive_count']:raise RuntimeError('independent closure/fixture cardinality mismatch')
 s,mt,n2n,build_ns=build(triples)
 if len(n2n)!=len(nodes):raise RuntimeError('native concept count mismatch')
 before_graph=graph_digest(s)
 pos=qset['positive'];neg=qset['negative'];allq=[('positive',x) for x in pos]+[('negative',x) for x in neg]
 for group,x in allq[:64]:ks.query_transitive(s,n2n,x['source'],x['target'])
 answers={'positive':[],'negative':[]};total_start=time.perf_counter_ns()
 for group,x in allq:
  t=time.perf_counter_ns();ans,hops=ks.query_transitive(s,n2n,x['source'],x['target']);elapsed=time.perf_counter_ns()-t
  answers[group].append({'answer':bool(ans),'reported_hops':int(hops),'latency_ns':int(elapsed)})
 total_ns=time.perf_counter_ns()-total_start
 counter=CountingSubstrate(s);ops={'positive':[],'negative':[]}
 for group,x in allq:
  counter.reset();ans,hops=ks.query_transitive(counter,n2n,x['source'],x['target'])
  ops[group].append({'answer':bool(ans),'neighbour_calls':counter.calls,'edge_scans':counter.scans})
 direct_tp=sum(ks.query_direct(s,n2n,x['source'],x['target']) for x in pos)
 import numpy as np
 rng=np.random.default_rng(0);targets=[o for _,o in triples];shuffled_targets=list(targets);rng.shuffle(shuffled_targets)
 shuffled=list(zip([a for a,_ in triples],shuffled_targets));ss,smt,sn2n,shuffle_build_ns=build(shuffled)
 shuffle={'positive':[],'negative':[]}
 for group,x in allq:
  ans,hops=ks.query_transitive(ss,sn2n,x['source'],x['target']);shuffle[group].append(bool(ans))
 after_graph=graph_digest(s);after=lock()
 outdeg=[len(adj[n]) for n in nodes];indeg=defaultdict(int)
 for a,b in triples:indeg[b]+=1
 weak={n:set(adj[n]) for n in nodes}
 for a,b in triples:weak[a].add(b);weak[b].add(a)
 seen=set();components=[]
 for root in nodes:
  if root in seen:continue
  stack=[root];seen.add(root);count=0
  while stack:
   u=stack.pop();count+=1
   for v in weak[u]-seen:seen.add(v);stack.append(v)
  components.append(count)
 dist_hist=defaultdict(int)
 for _,_,d in positives:dist_hist[str(d)]+=1
 indeg_vals=[indeg[n] for n in nodes]
 return {'worker':worker,'pid':os.getpid(),'source_lock_start':before,'source_lock_end':after,
  'graph':{'concepts':len(n2n),'relation_edges':len(triples),
   'outdegree_histogram':{str(k):outdeg.count(k) for k in sorted(set(outdeg))},
   'indegree_p50_p90_max':[int(np.percentile(indeg_vals,50)),int(np.percentile(indeg_vals,90)),max(indeg_vals)],
   'weak_component_count':len(components),'largest_weak_components':sorted(components,reverse=True)[:10],
   'closure_positive_by_shortest_distance':dict(sorted(dist_hist.items(),key=lambda z:int(z[0]))),
   'max_shortest_distance':max((d for _,_,d in positives),default=0)},
  'build_ns':build_ns,'shuffle_build_ns':shuffle_build_ns,'measured_query_batch_ns':total_ns,
  'queries_per_worker':len(allq),'answers':answers,'ops':ops,
  'direct_positive_recall':direct_tp/len(pos) if pos else 0.0,'shuffle_answers':shuffle,
  'graph_unchanged':before_graph==after_graph,'graph_digest_before':before_graph,'graph_digest_after':after_graph,
  'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
if __name__=='__main__':print(json.dumps(run(int(sys.argv[1])),sort_keys=True,separators=(',',':')))
