#!/usr/bin/env python3
"""Post-hoc, deterministic structural summary of the frozen runtime graph capture."""
from __future__ import annotations
import collections, hashlib, json, math, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
GRAPH=ROOT/'evaluation/reports/substrate_live_task_runtime_join_capture_v1_runtime_graph_20260927.json'
RAW=ROOT/'evaluation/reports/substrate_live_task_runtime_join_capture_v1_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_live_runtime_graph_structure_v1_20260928.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def components(nodes, edges):
    adj={n:set() for n in nodes}
    for s,t in edges:
        if s!=t: adj[s].add(t);adj[t].add(s)
    seen=set();sizes=[]
    for root in nodes:
        if root in seen:continue
        stack=[root];seen.add(root);size=0
        while stack:
            u=stack.pop();size+=1
            for v in adj[u]:
                if v not in seen:seen.add(v);stack.append(v)
        sizes.append(size)
    return adj,sorted(sizes,reverse=True)
def articulation_points(adj):
    sys.setrecursionlimit(max(100000,len(adj)+100))
    disc={};low={};parent={};points=set();clock=0
    def visit(u):
        nonlocal clock
        clock+=1;disc[u]=low[u]=clock;children=0
        for v in adj[u]:
            if v not in disc:
                parent[v]=u;children+=1;visit(v);low[u]=min(low[u],low[v])
                if u not in parent and children>1:points.add(u)
                if u in parent and low[v]>=disc[u]:points.add(u)
            elif parent.get(u)!=v:low[u]=min(low[u],disc[v])
    for n in adj:
        if n not in disc:visit(n)
    return points
def quantiles(values):
    a=sorted(values)
    if not a:return {}
    def q(p): return a[min(len(a)-1,math.ceil(p*(len(a)-1)))]
    return {'min':a[0],'p50':q(.5),'p90':q(.9),'p99':q(.99),'max':a[-1]}
def main():
    g=json.loads(GRAPH.read_text());raw=json.loads(RAW.read_text());actual=hashlib.sha256(json.dumps(g,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if actual!=raw['runtime_graph_sha256']:raise SystemExit('runtime graph hash disagrees with capture manifest')
    ids=[int(n['id']) for n in g['nodes']]; edge_types=collections.Counter(e['type'] for e in g['edges'])
    all_edges=[(int(e['src']),int(e['tgt'])) for e in g['edges']]
    adj,sizes=components(ids,all_edges);degrees=[len(x) for x in adj.values()]
    points=articulation_points(adj)
    removal={}
    for typ,_ in edge_types.most_common(12):
        kept=[(int(e['src']),int(e['tgt'])) for e in g['edges'] if e['type']!=typ]
        _,parts=components(ids,kept)
        removal[typ]={'removed_edges':edge_types[typ],'component_count':len(parts),'largest_component_nodes':parts[0] if parts else 0,'largest_component_fraction':round((parts[0] if parts else 0)/max(1,len(ids)),6)}
    result={'schema_version':1,'analysis_class':'post-hoc descriptive analysis of an existing captured graph; no preregistered hypothesis test','source_capture':str(GRAPH.relative_to(ROOT)),'capture_sha256':actual,'capture_manifest':str(RAW.relative_to(ROOT)),'capture_manifest_sha256':sha(RAW),'nodes':len(ids),'edges':len(all_edges),'distinct_edge_types':len(edge_types),'node_type_top20':collections.Counter(n['type'] for n in g['nodes']).most_common(20),'edge_type_top20':edge_types.most_common(20),'undirected_simple_projection':{'component_count':len(sizes),'largest_component_nodes':sizes[0] if sizes else 0,'largest_component_fraction':round((sizes[0] if sizes else 0)/max(1,len(ids)),6),'isolated_nodes':sum(x==0 for x in degrees),'degree_quantiles':quantiles(degrees),'articulation_point_count':len(points),'articulation_point_fraction':round(len(points)/max(1,len(ids)),6)},'top12_relation_removal_sensitivity':removal,'limits':['Undirected projection ignores edge direction and semantics.','Articulation points are single-node separators, not frame boundaries or treewidth.','Removing relation types is sensitivity analysis, not a learned or justified decomposition.','The captured graph is one full-profile runtime snapshot and does not establish a workload distribution or scaling law.']}
    OUT.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'out':str(OUT.relative_to(ROOT)),'nodes':len(ids),'edges':len(all_edges),'components':len(sizes),'largest_component':sizes[0] if sizes else 0,'articulation_points':len(points),'top_type_removal':removal},indent=2))
if __name__=='__main__':main()
