#!/usr/bin/env python3
"""Recompute graph-node boundary sizes from the typed frame census capture."""
from __future__ import annotations
import collections,hashlib,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/'evaluation/reports/substrate_typed_frame_interaction_census_v1_20261003.json'
OUT=ROOT/'evaluation/reports/task_frame_boundary_sizes_posthoc_v1_20261005.json'
SCRIPT=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def percentile(xs,p):return sorted(xs)[max(0,math.ceil(p*len(xs))-1)]
def derive(row):
 members=collections.defaultdict(set)
 for e in row['edge_rows']:
  for f in e['src_frames']:members[f].add(e['src'])
  for f in e['tgt_frames']:members[f].add(e['tgt'])
 boundary=collections.defaultdict(set);inc=collections.Counter();unknown=collections.Counter();typed=collections.defaultdict(collections.Counter)
 for e in row['edge_rows']:
  a,b=e['src'],e['tgt'];af=set(e['src_frames']);bf=set(e['tgt_frames'])
  for f in af-bf:
   boundary[f].add(b);inc[f]+=1;typed[f][e['type']]+=1
   if not bf:unknown[f]+=1
  for f in bf-af:
   boundary[f].add(a);inc[f]+=1;typed[f][e['type']]+=1
   if not af:unknown[f]+=1
 frames=[];node_frames=collections.defaultdict(set)
 for f,nodes in members.items():
  for node in nodes:node_frames[node].add(f)
 for f,nodes in sorted(members.items()):
  shared=sum(1 for node in nodes if len(node_frames[node])>1)
  frames.append({'frame':f,'frame_nodes':len(nodes),'shared_membership_nodes':shared,'distinct_external_graph_nodes':len(boundary[f]),'crossing_edge_incidences':inc[f],'unassigned_endpoint_incidences':unknown[f],'crossing_by_type':dict(sorted(typed[f].items()))})
 return frames,len(set(n for e in row['edge_rows'] for n,fs in ((e['src'],e['src_frames']),(e['tgt'],e['tgt_frames'])) if fs))
def main():
 raw=json.loads(CAP.read_text());allrows=[];errors=[];families=collections.defaultdict(list)
 for row in raw['rows']:
  frames,labeled=derive(row)
  if len(frames)==0 and row['frame_labeled_nodes']!=0:errors.append(f"no derived frames {row['graph_sha256']}")
  if labeled!=row['frame_labeled_nodes']:errors.append(f"node membership count mismatch {row['graph_sha256']}")
  if sum(row['edge_class_counts'].values())!=row['edge_occurrences'] or len(row['edge_rows'])!=row['edge_occurrences']:errors.append(f"edge count mismatch {row['graph_sha256']}")
  for fr in frames:
   fr.update({'family':row['family'],'case':row['case'],'checkpoint':row['checkpoint'],'graph_sha256':row['graph_sha256']});families[row['family']].append(fr);allrows.append(fr)
 summary={}
 for family,rs in sorted(families.items()):
  sizes=[r['frame_nodes'] for r in rs];bs=[r['distinct_external_graph_nodes'] for r in rs];incs=[r['crossing_edge_incidences'] for r in rs];unknown=[r['unassigned_endpoint_incidences'] for r in rs]
  summary[family]={'frame_count':len(rs),'frame_size_median_p90_max':[statistics.median(sizes),percentile(sizes,.9),max(sizes)],'shared_membership_nodes_median_p90_max':[statistics.median(r['shared_membership_nodes'] for r in rs),percentile([r['shared_membership_nodes'] for r in rs],.9),max(r['shared_membership_nodes'] for r in rs)],'distinct_external_nodes_median_p90_max':[statistics.median(bs),percentile(bs,.9),max(bs)],'crossing_incidences_median_p90_max':[statistics.median(incs),percentile(incs,.9),max(incs)],'unassigned_endpoint_incidences_median_p90_max':[statistics.median(unknown),percentile(unknown,.9),max(unknown)],'median_external_nodes_per_frame_node':statistics.median(b/s for b,s in zip(bs,sizes) if s)}
 out={'schema':'PosthocTaskFrameBoundarySizesV1','capture_sha256':sha(CAP),'script_sha256':sha(SCRIPT),'capture_snapshot_count':len(raw['rows']),'derived_frame_count':len(allrows),'definition':'For each runtime-labeled frame, distinct external graph nodes and directed edge incidences across typed edge occurrences whose endpoint frame sets have no common membership. Unassigned counterpart nodes are counted and separately labeled; this is not a factor-variable separator/interface.','summary':summary,'frames':allrows,'errors':errors,'passed':not errors,'claim_limit':'retrospective state-graph boundary sizes on three selected annotated capture families; not learned frames, inference width, task prevalence, or partitioned-execution parity'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'snapshots':len(raw['rows']),'frames':len(allrows),'summary':summary,'errors':errors,'output':OUT.relative_to(ROOT).as_posix()},indent=2));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
