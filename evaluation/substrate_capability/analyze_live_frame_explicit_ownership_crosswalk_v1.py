#!/usr/bin/env python3
"""Crosswalk operational task cuts with conservative relation-based ownership."""
from __future__ import annotations
import gzip, hashlib, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_workers_raw_20261004.json.gz'
SUMMARY=ROOT/'evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_20261004.json'
OUT=ROOT/'evaluation/reports/live_frame_explicit_ownership_crosswalk_v1_20261004.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(v):
    if isinstance(v,dict) and set(v)=={'__nid__'}: return int(v['__nid__'])
    if isinstance(v,int): return int(v)
    return None
def main():
    summary=json.loads(SUMMARY.read_text())
    if sha(CAPTURE)!=summary['raw_compressed_sha256']:raise SystemExit('raw archive hash mismatch')
    with gzip.open(CAPTURE,'rt',encoding='utf-8') as f: raw=json.load(f)
    worker=next(r for r in raw['runs'] if int(r['replicate'])==0)
    capture=worker['capture'];graph=capture['full_graph'];nodes={int(n['id']):n for n in graph['nodes']}
    edges=[(int(e['src']),str(e['type']),int(e['tgt'])) for e in graph['edges']]
    edges_by_type=Counter(t for _,t,_ in edges);boundary_data=capture['task_result']['task_boundaries']
    per_turn=[];owned_sets=[];operational_sets=[]
    for i,turn in enumerate(capture['task_result']['turns']):
        root=int(turn['message_id']);goal_ids=set()
        for a,rel,b in edges:
            if rel=='comprehends':
                if a==root and b in nodes and nodes[b]['type']=='Goal':goal_ids.add(b)
                if b==root and a in nodes and nodes[a]['type']=='Goal':goal_ids.add(a)
        explicit={root}|goal_ids
        event_ids=set()
        for gid in goal_ids:
            origin=ref(nodes[gid].get('attrs',{}).get('origin_event'))
            if origin in nodes and nodes[origin]['type']=='DiscourseEvent':event_ids.add(origin)
        for a,rel,b in edges:
            if rel=='for_goal':
                if a in nodes and nodes[a]['type']=='DiscourseEvent' and b in goal_ids:event_ids.add(a)
                if b in nodes and nodes[b]['type']=='DiscourseEvent' and a in goal_ids:event_ids.add(b)
        explicit|=event_ids
        operational=set(map(int,boundary_data[f'turn_{i}']['owned_node_ids']))
        owned_sets.append(explicit);operational_sets.append(operational)
        inter=explicit&operational;union=explicit|operational
        type_counts=lambda ids:dict(sorted(Counter(nodes[n]['type'] for n in ids).items()))
        per_turn.append({'turn':i,'prompt':turn.get('prompt'),'root_message_id':root,
          'explicit_goal_ids':sorted(goal_ids),'explicit_event_ids':sorted(event_ids),
          'relation_owned_node_count':len(explicit),'operational_owned_node_count':len(operational),
          'overlap_node_count':len(inter),'operational_precision_of_relation_projection':len(inter)/len(operational) if operational else None,
          'relation_projection_recall_of_operational_cut':len(inter)/len(explicit) if explicit else None,
          'jaccard':len(inter)/len(union) if union else 1.0,
          'relation_only_nodes':sorted(explicit-operational),'operational_only_nodes':sorted(operational-explicit),
          'relation_only_types':type_counts(explicit-operational),'operational_only_types':type_counts(operational-explicit),
          'relation_projection_types':type_counts(explicit),'operational_types':type_counts(operational),
          'operational_cut_metrics':{k:v for k,v in boundary_data[f'turn_{i}'].items() if k not in ('owned_node_ids','internal_edges','boundary_edges')}})
    direct_cross=[];owner={n:i for i,ids in enumerate(operational_sets) for n in ids}
    for src,rel,tgt in edges:
        if src in owner and tgt in owner and owner[src]!=owner[tgt]:direct_cross.append([src,rel,tgt])
    checks={'two_turns_reconstructed':len(per_turn)==2,'all_relation_owned_ids_resolve':all(n in nodes for ids in owned_sets for n in ids),
            'all_operational_ids_resolve':all(n in nodes for ids in operational_sets for n in ids),
            'full_graph_hash_bound':bool(summary.get('raw_uncompressed_sha256'))}
    result={'schema':'LiveFrameExplicitOwnershipCrosswalkV1','capture_sha256':sha(CAPTURE),'capture_summary_sha256':sha(SUMMARY),
      'analysis_sha256':None,'checks':checks,'passed':all(checks.values()),'graph':{'nodes':len(nodes),'edges':len(edges)},
      'edge_type_counts':dict(sorted(edges_by_type.items())),'turns':per_turn,
      'operational_frame_overlap_node_count':len(operational_sets[0]&operational_sets[1]),
      'operational_direct_cross_frame_edges':direct_cross,
      'claim_boundary':'A one-sequence comparison of protocol-supplied operational cuts with a conservative relation projection; neither defines complete task dependencies or factor scopes.'}
    result['analysis_sha256']=sha(Path(__file__))
    if OUT.exists():raise SystemExit(f'refusing to overwrite {OUT}')
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':result['passed'],'turn_summaries':[{'turn':r['turn'],'prompt':r['prompt'],'jaccard':r['jaccard'],'operational_count':r['operational_owned_node_count'],'relation_count':r['relation_owned_node_count'],'relation_only_types':r['relation_only_types'],'operational_only_types':r['operational_only_types']} for r in per_turn]},sort_keys=True))
    if not result['passed']:raise SystemExit(1)
if __name__=='__main__':main()
