#!/usr/bin/env python3
"""Post-hoc structural profile of locked Bigville dynamic-link raw capture.

This independently reconstructs resident-frame boundaries and a quotient frame
interaction graph at each saved checkpoint. It does not claim native partition
construction/update timing; that timing is absent from the source capture.
"""
import hashlib,json,statistics
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_bigville_runtime_partition_dynamic_links_20260925.json'
LOCK=ROOT/'evaluation/substrate_capability/bigville_runtime_partition_dynamic_links_lock_20260925.json'
FRAME_SIZE=5;FRAME_COUNT=100

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def profile(run,cp):
  flat_to_frame=lambda x:int(x)//FRAME_SIZE
  directed=[tuple(map(int,e[:2])) for e in cp['weights_by_flat_index']]
  directed_set=set(directed)
  nodes=set(range(FRAME_SIZE*FRAME_COUNT))
  undirected={tuple(sorted((a,b))) for a,b in directed if a!=b}
  active_resident_links={tuple(sorted((int(a),int(b)))) for a,b,_ in cp['active_cross_links']}
  within=set();cross=set()
  for a,b in undirected:
    fa,fb=flat_to_frame(a),flat_to_frame(b)
    (within if fa==fb else cross).add((a,b))
  if len(cross)!=len(active_resident_links):raise ValueError(f"cross edge mismatch raw={len(cross)} active={len(active_resident_links)}")
  cross_directed=sum(1 for a,b in directed_set if flat_to_frame(a)!=flat_to_frame(b))
  if cross_directed!=cp['cross_frame_directed_edge_count']:raise ValueError('directed boundary edge count mismatch')
  boundary_nodes=defaultdict(set);incident_edges=CounterLike();frame_edges=set()
  for a,b in cross:
    fa,fb=flat_to_frame(a),flat_to_frame(b)
    boundary_nodes[fa].add(a);boundary_nodes[fb].add(b)
    incident_edges[fa]+=1;incident_edges[fb]+=1
    frame_edges.add(tuple(sorted((fa,fb))))
  sizes=[len(boundary_nodes[i]) for i in range(FRAME_COUNT)]
  incidences=[incident_edges[i] for i in range(FRAME_COUNT)]
  width=__import__('domains.graph_treewidth',fromlist=['min_fill_upper_bound']).min_fill_upper_bound(range(FRAME_COUNT),list(frame_edges))['treewidth']
  return {'stage':cp['stage'],'active_undirected_cross_links':len(active_resident_links),'cross_frame_directed_edges':cross_directed,'within_frame_undirected_edges':len(within),'all_undirected_edges':len(undirected),'active_boundary_frames':sum(x>0 for x in sizes),'boundary_concept_total':sum(sizes),'boundary_concepts_per_frame':sizes,'cross_edge_incidences_per_frame':incidences,'max_boundary_concepts_per_frame':max(sizes,default=0),'median_boundary_concepts_per_frame':statistics.median(sizes),'max_cross_edge_incidences_per_frame':max(incidences,default=0),'median_cross_edge_incidences_per_frame':statistics.median(incidences),'frame_quotient_edge_count':len(frame_edges),'frame_quotient_treewidth_min_fill_upper_bound':width,'partition_semantics':'100 runtime-derived Microtheory owner frames; five Concepts/frame; membership held fixed while links mutate'}
class CounterLike(dict):
  def __missing__(self,k):self[k]=0;return 0
def main():
 d=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text())
 checks={'raw_lock_hash_matches':d['lock_sha256']==sha(LOCK),'raw_locked_inputs_match':d['locked_inputs']==lock.get('locked_inputs'),'27_workers':len(d['runs'])==27,'all_100_five_concept_frames':all(r['runtime_component_count']==100 and r['runtime_component_sizes']==[5]*100 for r in d['runs'])}
 by={}; rows=[]
 for r in d['runs']:
  key=(r['topology'],r['replicate'],r['policy']);by[key]=r
  if r['policy']!='event':continue
  prior=None
  for c in r['checkpoints']:
   p=profile(r,c)
   p.update({'topology':r['topology'],'replicate':r['replicate'],'policy':r['policy'],'mutation_ns':c['mutation_ns'],'settlement_wall_ns':c['settlement_wall_ns']})
   if prior is None:p['boundary_link_delta_from_previous']=None;p['boundary_concept_delta_from_previous']=None
   else:
    p['boundary_link_delta_from_previous']=p['active_undirected_cross_links']-prior['active_undirected_cross_links']
    p['boundary_concept_delta_from_previous']=p['boundary_concept_total']-prior['boundary_concept_total']
   prior=p;rows.append(p)
 checks['profile_rows_63']=len(rows)==63
 # Policies must carry identical structural topology per paired run/checkpoint.
 topo_parity=True
 for t in ('ring','star','random_connected'):
  for rep in range(3):
   rs=[by[(t,rep,p)] for p in ('full','event','omit_evidence_notification')]
   topo_parity &= all([[c['active_cross_links'],c['weights_by_flat_index'],c['cross_frame_directed_edge_count']] for c in r['checkpoints']]==[[c['active_cross_links'],c['weights_by_flat_index'],c['cross_frame_directed_edge_count']] for c in rs[0]['checkpoints']] for r in rs[1:])
 checks['structural_topology_equal_across_policies']=bool(topo_parity)
 # Stage/topology summaries preserve per-replicate values and report medians/ranges.
 summaries=[]
 stages=sorted({x['stage'] for x in rows},key=lambda x:next(i for i,y in enumerate(rows) if y['stage']==x))
 for t in ('ring','star','random_connected'):
  for stage in stages:
   xs=[x for x in rows if x['topology']==t and x['stage']==stage]
   if not xs:continue
   summaries.append({'topology':t,'stage':stage,'n':len(xs),'active_links_median_range':[statistics.median(x['active_undirected_cross_links'] for x in xs),[min(x['active_undirected_cross_links'] for x in xs),max(x['active_undirected_cross_links'] for x in xs)]],'active_frames_median_range':[statistics.median(x['active_boundary_frames'] for x in xs),[min(x['active_boundary_frames'] for x in xs),max(x['active_boundary_frames'] for x in xs)]],'boundary_concepts_total_median_range':[statistics.median(x['boundary_concept_total'] for x in xs),[min(x['boundary_concept_total'] for x in xs),max(x['boundary_concept_total'] for x in xs)]],'max_frame_incidence_median_range':[statistics.median(x['max_cross_edge_incidences_per_frame'] for x in xs),[min(x['max_cross_edge_incidences_per_frame'] for x in xs),max(x['max_cross_edge_incidences_per_frame'] for x in xs)]],'frame_quotient_width_upper_bound_range':[min(x['frame_quotient_treewidth_min_fill_upper_bound'] for x in xs),max(x['frame_quotient_treewidth_min_fill_upper_bound'] for x in xs)]})
 out={'analysis':'posthoc_structural_profile_v1','source_raw_sha256':sha(RAW),'source_lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'treewidth_source_sha256':sha(ROOT/'domains/graph_treewidth.py'),'frame_count':FRAME_COUNT,'frame_size':FRAME_SIZE,'checks':checks,'all_checks_pass':all(checks.values()),'boundary_profile_rows':rows,'stage_topology_summaries':summaries,'claim_boundary':'secondary analysis of a previously locked authored Bigville run; frame ownership is runtime-derived and stable by Microtheory; links are injected cross-frame controls; no partition build/update cost captured; quotient width is a min-fill upper bound, not exact; not natural-task prevalence'}
 path=ROOT/'evaluation/reports/substrate_bigville_dynamic_boundary_profile_v1_20260926.json';path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':str(path),'checks':checks,'all_checks_pass':out['all_checks_pass'],'summaries':summaries},indent=2))
if __name__=='__main__':main()
