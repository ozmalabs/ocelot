#!/usr/bin/env python3
"""Extract replicated operational frame-cut statistics from current v1.2 capture."""
from __future__ import annotations
import gzip, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_workers_raw_20261004.json.gz'
SUMMARY=ROOT/'evaluation/reports/substrate_live_frame_rule_scope_capture_v1_2_20261004.json'
RULE_ANALYSIS=ROOT/'evaluation/reports/live_frame_rule_scope_capture_v1_2_analysis_20261004.json'
OUT=ROOT/'evaluation/reports/live_frame_rule_scope_structural_v1_2_analysis_20261004.json'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    summary=json.loads(SUMMARY.read_text())
    if sha(RAW)!=summary['raw_compressed_sha256']: raise SystemExit('raw archive hash differs from capture summary')
    with gzip.open(RAW,'rt',encoding='utf-8') as f: raw=json.load(f)
    rule_analysis=json.loads(RULE_ANALYSIS.read_text())
    runs=raw['runs']; expected=raw['locked_inputs']
    stability=all(r.get('worker_started_inputs')==expected==r.get('worker_finished_inputs') for r in runs)
    graph_digests={r['capture'].get('graph_semantic_sha256') for r in runs}
    summaries=[r['capture'].get('graph_summary',{}) for r in runs]
    boundaries=[]
    signatures={}
    for i,r in enumerate(runs):
        cuts=r['capture'].get('task_result',{}).get('task_boundaries',{})
        for name,cut in cuts.items():
            if name=='pair' or not isinstance(cut,dict): continue
            member_count=cut.get('owned_node_count',cut.get('member_count',cut.get('frame_size',len(cut.get('node_ids',cut.get('owned_node_ids',[]))))))
            whole_nodes=cut.get('whole_graph_node_count',summaries[i].get('node_count'))
            whole_edges=cut.get('whole_graph_edge_count',summaries[i].get('edge_count'))
            row={'worker':i,'cut':name,'member_count':member_count,'whole_graph_nodes':whole_nodes,
                 'frame_node_fraction': member_count/whole_nodes if member_count and whole_nodes else None,
                 'internal_edge_count':cut.get('internal_edge_count'),
                 'crossing_incidences':cut.get('boundary_incidence_count',cut.get('crossing_incidence_count')),
                 'distinct_external_nodes':cut.get('boundary_unique_external_node_count',cut.get('distinct_external_node_count')),
                 'whole_graph_edges':whole_edges,
                 'crossing_per_owned_node': (cut.get('boundary_incidence_count',cut.get('crossing_incidence_count'))/member_count if member_count else None),
                 'owned_induced_width_upper_bound':cut.get('owned_induced_treewidth_upper_bound',cut.get('member_induced_treewidth_upper_bound')),
                 'boundary_edge_types':cut.get('boundary_edge_type_counts'),
                 'external_node_types':cut.get('boundary_external_node_type_counts'),
                 'width_bound_recorded':any(k in cut for k in ('owned_induced_treewidth_upper_bound','member_induced_treewidth_upper_bound'))}
            boundaries.append(row)
            signatures.setdefault(name,[]).append({k:v for k,v in row.items() if k not in ('worker',)})
    replicated={k:len({json.dumps(x,sort_keys=True) for x in v})==1 for k,v in signatures.items()}
    request_records=rule_analysis.get('per_request_resolution',[])
    report={'schema':'LiveFrameRuleScopeStructuralV1_2Analysis','raw_sha256':sha(RAW),'capture_summary_sha256':sha(SUMMARY),
      'rule_scope_analysis_sha256':sha(RULE_ANALYSIS),'analysis_script_sha256':sha(Path(__file__)),
      'checks':{'raw_digest_matches_summary':True,'source_lock_stable_per_worker':stability,
                'same_final_graph_digest_across_workers':len(graph_digests)==1,
                'same_graph_size_across_workers':len({(s.get('node_count'),s.get('edge_count')) for s in summaries})==1,
                'cut_signatures_reproduce_across_workers':all(replicated.values()),
                'request_rule_uid_mapping_complete':rule_analysis['summary']['runtime_rule_uid_observations']==rule_analysis['summary']['runtime_rule_uid_mappings']},
      'worker_count':len(runs),'graph':summaries[0] if summaries else {},'operational_cuts':boundaries,
      'cut_signature_replicates':{k:{'workers':len(v),'identical':replicated[k]} for k,v in signatures.items()},
      'request_rule_uid_observations':rule_analysis['summary']['runtime_rule_uid_observations'],
      'request_weighted_access_events':rule_analysis['summary']['weighted_access_events'],
      'rule_term_classes':{'whole_population_rules':rule_analysis['summary']['whole_population_term_rules'],
        'local_adjacency_rules':rule_analysis['summary']['local_adjacency_term_rules'],
        'subgraph_or_reachability_rules':rule_analysis['summary']['subgraph_or_reachability_term_rules'],
        'external_boundary_rules':rule_analysis['summary']['external_boundary_term_rules']},
      'claim_boundary':'Replicated cuts are protocol-declared operational projections. They are not learned separators or complete factor/dependency scopes. Whole-population terms and missing interface domains prevent deriving bounded treewidth or exact-inference complexity from these counts.'}
    report['passed']=all(report['checks'].values())
    if OUT.exists(): raise SystemExit(f'refusing to overwrite {OUT}')
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':report['passed'],'cuts':len(boundaries),'check_summary':report['checks'],'output':str(OUT.relative_to(ROOT))},sort_keys=True))
    if not report['passed']: raise SystemExit(1)
if __name__=='__main__': main()
