#!/usr/bin/env python3
"""Independent closure, utility, source, coverage, and cost analysis."""
from __future__ import annotations
import hashlib,json,math,statistics,sys
from collections import defaultdict,deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/llm_taxonomy_traversal_scaling_v1_1_lock_20261002.json'
CAPTURE=ROOT/'evaluation/reports/llm_taxonomy_traversal_scaling_v1_1_20261002.json'
QUERY=ROOT/'evaluation/substrate_capability/fixtures/llm_taxonomy_traversal_scaling_v1_queries.json'
OUT=ROOT/'evaluation/reports/llm_taxonomy_traversal_scaling_v1_1_analysis_20261002.json'
MAX_HOPS=6;TOL=0

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());qset=json.loads(QUERY.read_text());runs=data.get('runs',[]);errors=[]
 def req(ok,msg):
  if not ok:errors.append(msg)
 req(data.get('lock_sha256')==sha(LOCK),'capture lock hash mismatch')
 req(data.get('sources')==lock['sources']==data.get('post_run_sources'),'source lock drift')
 req(not data.get('failures'),'worker failures present')
 req(len(runs)==3 and len({r['pid'] for r in runs})==3,'expected three fresh worker PIDs')
 seed=json.load(open(ROOT/'domain_data/llm_harvest/qwen3_reaped_isa_full.json'))
 edges=[(e['subject'],e['object']) for e in seed['edges'] if e['relation']=='isa' and e['subject']!=e['object']]
 nodes=sorted({v for e in edges for v in e});adj={n:[] for n in nodes}
 for a,b in edges:adj[a].append(b)
 oracle={};allpos=[]
 for src in nodes:
  q=deque([(src,0)]);seen={src};dist={}
  while q:
   u,d=q.popleft()
   for v in adj[u]:
    if v not in seen:seen.add(v);dist[v]=d+1;q.append((v,d+1))
  oracle[src]=dist
  allpos.extend((src,t,d) for t,d in dist.items() if d>=2)
 allpos.sort(key=lambda r:(r[0],r[1]))
 expected_pos=[(x['source'],x['target'],x['shortest_distance']) for x in qset['positive']]
 req(expected_pos==allpos,'positive fixture does not equal independently recomputed full closure')
 req(len(qset['negative'])==len(allpos) and len({(x['source'],x['target']) for x in qset['negative']})==len(allpos),'negative fixture size/uniqueness')
 req(all(x['target'] not in oracle[x['source']] and x['source']!=x['target'] for x in qset['negative']),'negative fixture contains reachable pair')
 summary_workers=[];shuffle_all=[]
 for ri,r in enumerate(runs):
  label=f'worker {ri}'
  req(r['queries_per_worker']==9640 and len(r['answers']['positive'])==4820 and len(r['answers']['negative'])==4820,label+': query coverage')
  req(r['source_lock_start']==r['source_lock_end'],label+': worker source drift')
  g=r['graph'];req(g['concepts']==len(nodes) and g['relation_edges']==len(edges),label+': graph size')
  req(r['graph_unchanged'] and r['graph_digest_before']==r['graph_digest_after'],label+': graph mutation')
  by_depth=defaultdict(lambda:{'n':0,'correct':0,'closure_correct':0,'latency_ns':[],'calls':[],'scans':[]})
  for group,queries in (('positive',qset['positive']),('negative',qset['negative'])):
   answers=r['answers'][group];ops=r['ops'][group]
   req(len(answers)==len(queries)==len(ops),label+f': {group} coverage')
   for i,(x,y,o) in enumerate(zip(queries,answers,ops)):
    d=x['shortest_distance'];expect=(d<=MAX_HOPS) if group=='positive' else False
    got=y['answer'];item=by_depth[str(d) if d is not None else 'negative']
    item['n']+=1;item['correct']+=int(got==expect);item['closure_correct']+=int(got==(group=='positive'));item['latency_ns'].append(y['latency_ns']);item['calls'].append(o['neighbour_calls']);item['scans'].append(o['edge_scans'])
    req(y['reported_hops']==(d if got else 0),label+f': reported hop count mismatch at {group}/{i}')
    req(o['answer']==got,label+f': instrumented/uninstrumented answer mismatch at {group}/{i}')
    req(0<=o['neighbour_calls']<=MAX_HOPS and 0<=o['edge_scans']<=o['neighbour_calls'],label+f': operation count outside bounded path')
  req(r['direct_positive_recall']==0.0,label+': direct lookup found multi-hop positive')
  req(all(v['correct']==v['n'] for v in by_depth.values()),label+': query answers differ from the registered six-hop operating envelope')
  sh=r['shuffle_answers'];req(len(sh['positive'])==len(qset['positive']) and len(sh['negative'])==len(qset['negative']),label+': shuffle coverage')
  sh_acc=(sum(bool(x) for x in sh['positive'])+sum(not bool(x) for x in sh['negative']))/(len(sh['positive'])+len(sh['negative']))
  shuffle_all.append(sh_acc)
  summary_workers.append({'pid':r['pid'],'graph_build_ms':r['build_ns']/1e6,'query_batch_ms':r['measured_query_batch_ns']/1e6,
   'queries_per_second':9640/(r['measured_query_batch_ns']/1e9),'shuffle_build_ms':r['shuffle_build_ns']/1e6,'shuffle_accuracy':sh_acc,
   'peak_rss_mib':r['process_peak_rss_kib']/1024,'by_shortest_distance':{
    k:{'queries':v['n'],'bounded_accuracy':v['correct']/v['n'],'full_closure_accuracy':v['closure_correct']/v['n'],'median_latency_us':statistics.median(v['latency_ns'])/1000,
       'p95_latency_us':float(__import__('numpy').percentile(v['latency_ns'],95))/1000,
       'median_neighbour_calls':statistics.median(v['calls']),'median_edge_scans':statistics.median(v['scans'])}
    for k,v in sorted(by_depth.items(),key=lambda z:(z[0]=='negative',int(z[0]) if z[0]!='negative' else 0))}})
 req(len(allpos)==4820,'full closure positive count mismatch')
 long_count=sum(x['shortest_distance']>MAX_HOPS for x in qset['positive'])
 req(long_count==3,'expected three positive pairs beyond the implementation depth bound')
 req(bool(runs) and all(r['graph']==runs[0]['graph'] for r in runs),'task-graph topology differs across workers')
 all_answers=[x for r in runs for x in r['answers']['positive']]
 all_negative=[x for r in runs for x in r['answers']['negative']]
 true_pos=sum(x['answer'] for x in all_answers);true_neg=sum(not x['answer'] for x in all_negative)
 req(len(all_answers)==3*len(qset['positive']) and len(all_negative)==3*len(qset['negative']),'answer coverage incomplete')
 req(true_pos==3*(len(qset['positive'])-long_count) and true_neg==3*len(qset['negative']),'closure classification differs from bounded-depth prediction')
 out={'schema':'LlmTaxonomyTraversalScalingV1Analysis','gates_pass':not errors,'errors':errors,
  'interpretation':{'closure_oracle':'independent host adjacency traversal of the locked harvested seed','external_truth':'not tested by this closure assay; WordNet audit reports only 27.2% valid-ancestor yield','depth_limit':MAX_HOPS,'expected_default_misses':long_count,'treewidth_claim':False},
  'summary':{'workers':summary_workers,'closure_positive_pairs':len(allpos),'sampled_nonreachable_pairs':len(qset['negative']),
   'closure_accuracy':(true_pos+true_neg)/(len(all_answers)+len(all_negative)),'positive_recall':true_pos/len(all_answers),'negative_specificity':true_neg/len(all_negative),
   'shuffle_accuracy_median':statistics.median(shuffle_all),'depth_limit_misses':long_count}}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
