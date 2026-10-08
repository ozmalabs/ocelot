#!/usr/bin/env python3
"""Independent validation of the typed frame-interaction capture."""
from __future__ import annotations
import collections,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_typed_frame_interaction_census_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/substrate_typed_frame_interaction_census_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_typed_frame_interaction_census_v1_analysis_20261003.json'
CAPTURES=[ROOT/'evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json',ROOT/'evaluation/reports/substrate_connected_conversation_boundary_panel_v1_20260926.json',ROOT/'evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_items():
 b,c,d=[json.loads(p.read_text()) for p in CAPTURES];out=[]
 for ri,r in enumerate(b['runs']):
  mem={int(n):{int(f)} for n,f in r.get('runtime_node_frame',[])}
  for ci,cp in enumerate(r['checkpoints']):out.append(('bigville_dynamic_link',str(r.get('replicate',ri)),str(r.get('topology')),str(cp.get('stage',ci)),cp['graph'],mem))
 for r in c['runs']:
  for ci,z in enumerate(r['cases']):
   mem={int(n):{int(f)} for n,f in z.get('frame_owner',[])}
   for n,fs in z.get('boundary_nodes_by_frames',{}).items():mem[int(n)]={int(f) for f in fs}
   out.append(('connected_conversation',str(r.get('replicate')),str(z.get('case_id',ci)),'final',z['final_graph'],mem))
 for ri,r in enumerate(d['runs']):
  mem={int(n):{int(f)} for n,f in r.get('frame_owner',[])}
  for n,fs in r.get('boundary_nodes_by_frames',{}).items():mem[int(n)]={int(f) for f in fs}
  out.append(('discourse_connected_task',str(r.get('replicate') or r.get('arm') or f'run_{ri}'),'two_goal_connected_task','final',r['final_graph'],mem))
 return out
def recompute(g,mem):
 nodes=sorted(int(n['id']) for n in g['nodes']);types={};edge_rows=[];canon=[]
 for e in g['edges']:
  src=int(e['src']);tgt=int(e['tgt']);typ=str(e['type']);sm=sorted(mem.get(src,set()));tm=sorted(mem.get(tgt,set()))
  status='unassigned_endpoint' if not sm or not tm else ('common_frame' if set(sm)&set(tm) else 'disjoint_frames');touch=len(sm)>1 or len(tm)>1
  q=types.setdefault(typ,{'total':0,'common_frame':0,'disjoint_frames':0,'unassigned_endpoint':0,'touches_shared_boundary':0});q['total']+=1;q[status]+=1;q['touches_shared_boundary']+=int(touch)
  edge_rows.append({'src':src,'tgt':tgt,'type':typ,'status':status,'src_frames':sm,'tgt_frames':tm,'touches_shared_boundary':bool(touch)})
  canon.append((src,tgt,typ,e.get('attrs',{})))
 gh=hashlib.sha256(json.dumps([nodes,sorted(canon,key=lambda x:json.dumps(x,sort_keys=True))],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 return {'graph_sha256':gh,'node_count':len(nodes),'edge_occurrences':len(edge_rows),'typed_edges':types,'frame_labeled_nodes':sum(bool(mem.get(n)) for n in nodes),
  'shared_frame_nodes':sum(len(mem.get(n,set()))>1 for n in nodes),'edge_class_counts':{k:sum(e['status']==k for e in edge_rows) for k in ('common_frame','disjoint_frames','unassigned_endpoint')},
  'shared_boundary_incident_edges':sum(e['touches_shared_boundary'] for e in edge_rows),'edge_rows':edge_rows}
def main():
 lock=json.loads(LOCK.read_text());cap=json.loads(CAP.read_text());errs=[]
 if cap.get('lock_sha256')!=sha(LOCK):errs.append('capture lock hash mismatch')
 if cap.get('sources_before')!=lock['sources'] or cap.get('sources_after')!=lock['sources']:errs.append('capture source hash mismatch')
 items=load_items();rows=cap.get('rows',[])
 if len(items)!=78 or len(rows)!=78:errs.append('row count differs from 78')
 summary=collections.defaultdict(lambda:collections.Counter());by_type=collections.defaultdict(lambda:collections.defaultdict(collections.Counter))
 for ix,(item,row) in enumerate(zip(items,rows)):
  fam,run,case,checkpoint,g,mem=item
  if (row.get('family'),row.get('source_run'),row.get('case'),row.get('checkpoint'))!=(fam,run,case,checkpoint):errs.append(f'row {ix}: identity mismatch')
  m=recompute(g,mem)
  for key,val in m.items():
   if row.get(key)!=val:errs.append(f'row {ix}: {key} differs from independent recomputation')
  summary[fam]['graphs']+=1;summary[fam]['edges']+=len(g['edges']);summary[fam]['shared_nodes']+=m['shared_frame_nodes']
  for typ,counts in m['typed_edges'].items():
   for k,v in counts.items():by_type[fam][typ][k]+=v
 results={fam:{'graphs':v['graphs'],'edge_occurrences':v['edges'],'median_shared_frame_nodes':sorted(r['shared_frame_nodes'] for r in rows if r['family']==fam)[v['graphs']//2],
  'edge_type_profile':{typ:dict(counts) for typ,counts in sorted(by_type[fam].items())},
  'totals':{k:sum(r['edge_class_counts'][k] for r in rows if r['family']==fam) for k in ('common_frame','disjoint_frames','unassigned_endpoint')},
  'shared_boundary_incident_edges':sum(r['shared_boundary_incident_edges'] for r in rows if r['family']==fam)} for fam,v in summary.items()}
 # Compact, directly relevant list of types that actually bridge disjoint frame memberships.
 bridging={fam:{typ:counts['disjoint_frames'] for typ,counts in by_type[fam].items() if counts['disjoint_frames']} for fam in by_type}
 out={'schema':'TypedFrameInteractionCensusV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'gates_pass':not errs,'errors':errs,
  'summary':{'graphs':len(rows),'families':results,'disjoint_frame_relation_counts':bridging}}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':not errs,'error_count':len(errs),'summary':out['summary']},sort_keys=True));return 0 if not errs else 1
if __name__=='__main__':sys.exit(main())
