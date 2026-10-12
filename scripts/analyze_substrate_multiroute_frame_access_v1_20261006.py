#!/usr/bin/env python3
"""Summarize locked five-route ingress-frame/access capture."""
import gzip,json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAPTURE=ROOT/'evaluation/reports/multiroute_frame_access_v1_20261006/capture.json.gz'
OUT=ROOT/'evaluation/reports/multiroute_frame_access_v1_20261006/analysis.json'
data=json.loads(gzip.decompress(CAPTURE.read_bytes()));runs=data['runs'];by=defaultdict(list)
for r in runs:
 t=r['turns'][0];f=r['preoutcome_frame'];a=r['postcheckpoint_rule_access']
 by[r['condition']].append({'replicate':r['replicate'],'task_ok':r.get('task_ok'),'reply':r.get('reply'),'frame_nodes':f['owned_node_count'],'frame_types':f['owned_type_counts'],'boundary_nodes':f['boundary_unique_external_node_count'],'boundary_incidences':f['boundary_incidence_count'],'state_width_upper_bound':f['owned_induced_state_treewidth_upper_bound'],'trace_events':a['event_count'],'touched_nodes_by_scope':a['touched_nodes_by_scope'],'access_counts_by_scope_and_kind':a['access_counts_by_scope_and_kind'],'dropped':a['dropped'],'unmapped_rule_uids':a['unmapped_rule_uids']})
# The harvest runner's task oracle is applied to the captured worker records.
import importlib.util
s=importlib.util.spec_from_file_location('harvest_analysis',ROOT/'evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v2.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
for r in runs:
 locked_ok=bool(r.get('source_stable') and r.get('locked_inputs')==r.get('post_run_inputs') and r.get('boot_loaded',0)>0 and r.get('error') is None)
 r['task_ok']=locked_ok and h.task_oracle(r)
 if r['condition']=='scene_description':r['task_ok']=r['task_ok'] and len(r.get('faculty_build_calls',[]))==1 and r['faculty_build_calls'][0].get('rule_delta')==18
 # Replace derived value after oracle evaluation.
 for row in by[r['condition']]:
  if row['replicate']==r['replicate']:row['task_ok']=r['task_ok']
integrity={'ten_workers':len(runs)==10,'one_frame_and_trace_each':all(len(r['turns'])==1 and 'preoutcome_frame' in r and 'postcheckpoint_rule_access' in r for r in runs),'source_stable':data['locked_inputs']==data['post_run_inputs'] and all(r.get('source_stable') for r in runs),'trace_complete':all(r['postcheckpoint_rule_access']['dropped']==0 and not r['postcheckpoint_rule_access']['unmapped_rule_uids'] for r in runs)}
out={'schema':'MultiRouteFrameAccessV1Analysis','integrity_checks':integrity,'integrity_pass':all(integrity.values()),'task_utility_by_route':{k:{'passes':sum(x['task_ok'] is True for x in v),'replicates':len(v)} for k,v in by.items()},'routes':dict(by),'interpretation':'Selected authored panel only. Ingress state-graph projection and observed native trace roles do not establish factor interfaces, semantic necessity, natural-task prevalence, or speedup.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'integrity_pass':out['integrity_pass'],'task_utility_by_route':out['task_utility_by_route']},indent=2))
