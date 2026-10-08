#!/usr/bin/env python3
"""Create deterministic closure positives and matched non-reachable queries."""
from __future__ import annotations
import argparse,hashlib,json
from collections import deque
from pathlib import Path
import numpy as np

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--seed',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 seed_path=Path(a.seed);out=Path(a.output)
 if out.exists():raise SystemExit('refusing to overwrite query fixture')
 d=json.loads(seed_path.read_text());edges=[(e['subject'],e['object']) for e in d['edges'] if e['relation']=='isa' and e['subject']!=e['object']]
 nodes=sorted({x for e in edges for x in e});adj={n:[] for n in nodes}
 for s,o in edges:adj[s].append(o)
 positives=[];reach={}
 for src in nodes:
  q=deque([(src,0)]);seen={src};dist={}
  while q:
   node,depth=q.popleft()
   for nxt in adj[node]:
    if nxt not in seen:
     seen.add(nxt);dist[nxt]=depth+1;q.append((nxt,depth+1))
  reach[src]=set(dist)
  positives.extend({'source':src,'target':dst,'shortest_distance':depth} for dst,depth in dist.items() if depth>=2)
 positives.sort(key=lambda r:(r['source'],r['target']))
 rng=np.random.default_rng(20261003);neg=[];seen_neg=set();n=len(nodes);tries=0
 while len(neg)<len(positives):
  i,j=map(int,rng.integers(0,n,size=2));tries+=1
  if i==j or nodes[j] in reach[nodes[i]] or (i,j) in seen_neg:continue
  seen_neg.add((i,j));neg.append({'source':nodes[i],'target':nodes[j],'shortest_distance':None})
 if not positives:raise SystemExit('no closure positives')
 doc={'schema':'LlmTaxonomyTraversalQuerySetV1','seed_sha256':sha(seed_path),'generation':'all unique non-self transitive pairs with shortest path >=2; matched unique random non-reachable pairs','negative_rng':'numpy.default_rng(20261003)','nodes':len(nodes),'edges':len(edges),'positive_count':len(positives),'negative_count':len(neg),'positive':positives,'negative':neg}
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
 print(json.dumps({k:doc[k] for k in ('seed_sha256','nodes','edges','positive_count','negative_count')}))
if __name__=='__main__':main()
