#!/usr/bin/env python3
"""Source-locked typed edge/frame-membership census on 78 task graphs."""
from __future__ import annotations
import hashlib,json,platform,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_typed_frame_interaction_census_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_TYPED_FRAME_INTERACTION_CENSUS_V1_PREREG_20261003.md'
LOCK=ROOT/'evaluation/substrate_capability/substrate_typed_frame_interaction_census_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_typed_frame_interaction_census_v1_20261003.json'
CENSUS=ROOT/'evaluation/substrate_capability/substrate_task_graph_structural_census_v1_3.py'
CENSUS_ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_task_graph_structural_census_v1_3.py'
CENSUS_RESULT=ROOT/'docs/research/engine_substrate/SUBSTRATE_TASK_GRAPH_STRUCTURAL_CENSUS_V1_3_RESULTS_20261003.md'
CAPTURES=[ROOT/'evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json',ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json',ROOT/'evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json']
LOCKS=[ROOT/'evaluation/substrate_capability/bigville_dynamic_link_cut_capture_v1_lock_20260926.json',ROOT/'evaluation/substrate_capability/connected_conversation_boundary_panel_v1_lock_20260926.json',ROOT/'evaluation/substrate_capability/discourse_connected_task_census_v2_1_lock_20260926.json']
def digest(p):
 p=Path(p);return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def sources():return {'files':[digest(p) for p in [RUNNER,ANALYZER,PROTOCOL,CENSUS,CENSUS_ANALYZER,CENSUS_RESULT,*CAPTURES,*LOCKS]],'planned_rows':78,'edge_policy':'preserve raw directed edge occurrences, type, and attrs; do not collapse parallel typed edges'}
def norm_membership(owner,boundaries):
 out={int(n):{int(f)} for n,f in owner.items()}
 for n,frames in boundaries.items():out[int(n)]={int(f) for f in frames}
 return out
def input_graphs():
 b,c,d=[json.loads(p.read_text()) for p in CAPTURES];out=[]
 for ri,r in enumerate(b['runs']):
  owner={int(n):int(f) for n,f in r.get('runtime_node_frame',[])}
  for ci,cp in enumerate(r['checkpoints']):out.append({'family':'bigville_dynamic_link','source_run':str(r.get('replicate',ri)),'case':str(r.get('topology')),'checkpoint':str(cp.get('stage',ci)),'graph':cp['graph'],'membership':norm_membership(owner,{})})
 for r in c['runs']:
  for ci,case in enumerate(r['cases']):
   owner={int(n):int(f) for n,f in case.get('frame_owner',[])};boundary=case.get('boundary_nodes_by_frames',{})
   out.append({'family':'connected_conversation','source_run':str(r.get('replicate')),'case':str(case.get('case_id',ci)),'checkpoint':'final','graph':case['final_graph'],'membership':norm_membership(owner,boundary)})
 for ri,r in enumerate(d['runs']):
  run=str(r.get('replicate') or r.get('arm') or f'run_{ri}');owner={int(n):int(f) for n,f in r.get('frame_owner',[])}
  out.append({'family':'discourse_connected_task','source_run':run,'case':'two_goal_connected_task','checkpoint':'final','graph':r['final_graph'],'membership':norm_membership(owner,r.get('boundary_nodes_by_frames',{}))})
 return out
def classify(item):
 g=item['graph'];nodes=sorted(int(n['id']) for n in g['nodes']);mem=item['membership'];types={};edge_rows=[]
 canon=[]
 for e in g['edges']:
  src=int(e['src']);tgt=int(e['tgt']);typ=str(e['type']);sm=sorted(mem.get(src,set()));tm=sorted(mem.get(tgt,set()))
  if not sm or not tm:status='unassigned_endpoint'
  elif set(sm)&set(tm):status='common_frame'
  else:status='disjoint_frames'
  touch=bool(len(sm)>1 or len(tm)>1)
  row=types.setdefault(typ,{'total':0,'common_frame':0,'disjoint_frames':0,'unassigned_endpoint':0,'touches_shared_boundary':0})
  row['total']+=1;row[status]+=1;row['touches_shared_boundary']+=int(touch)
  edge_rows.append({'src':src,'tgt':tgt,'type':typ,'status':status,'src_frames':sm,'tgt_frames':tm,'touches_shared_boundary':touch})
  canon.append((src,tgt,typ,e.get('attrs',{})))
 gh=hashlib.sha256(json.dumps([nodes,sorted(canon,key=lambda x:json.dumps(x,sort_keys=True))],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return {'family':item['family'],'source_run':item['source_run'],'case':item['case'],'checkpoint':item['checkpoint'],'graph_sha256':gh,
  'node_count':len(nodes),'edge_occurrences':len(edge_rows),'typed_edges':types,
  'frame_labeled_nodes':sum(bool(mem.get(n)) for n in nodes),'shared_frame_nodes':sum(len(mem.get(n,set()))>1 for n in nodes),
  'edge_class_counts':{k:sum(e['status']==k for e in edge_rows) for k in ('common_frame','disjoint_frames','unassigned_endpoint')},
  'shared_boundary_incident_edges':sum(e['touches_shared_boundary'] for e in edge_rows),'edge_rows':edge_rows}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing lock/capture')
  LOCK.write_text(json.dumps({'schema':'TypedFrameInteractionCensusV1Lock','sources':sources()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text());before=sources()
 if before!=lock['sources']:raise SystemExit('source drift from lock')
 rows=[classify(x) for x in input_graphs()];after=sources();capture={'schema':'TypedFrameInteractionCensusV1Capture','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),'lock_sha256':hashlib.sha256(LOCK.read_bytes()).hexdigest(),'sources_before':before,'sources_after':after,'checks':{'source_stable':before==after==lock['sources'],'rows_78':len(rows)==78,'families_3':len(set(r['family'] for r in rows))==3},'rows':rows}
 OUT.write_text(json.dumps(capture,indent=2,sort_keys=True)+'\n');print(json.dumps({'capture':OUT.relative_to(ROOT).as_posix(),'checks':capture['checks']},sort_keys=True));return 0 if all(capture['checks'].values()) else 1
if __name__=='__main__':raise SystemExit(main())
