#!/usr/bin/env python3
"""Classify v2.4 selected accesses against its declared task/input projections."""
import collections, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_boundary_touch_v1_20260927.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def analyze():
 raw=json.loads(RAW.read_text());traces=[r for r in raw['runs'] if r['trace_enabled']]
 checks={'three_traced_workers':len(traces)==3,'no_dropped_events':all(r['access_trace']['dropped']==0 for r in traces),'source_stable':all(r['worker_started_inputs']==r['worker_finished_inputs'] for r in traces)}
 results=[]
 for run in traces:
  bounds=run['task_boundaries'];owners={k:set(bounds[k]['owned_node_ids']) for k in ('a','b','shared_scene_input')}
  for req in ('request-A','request-B'):
   rows=[x for x in run['access_trace']['event_rows'] if x['request']==req]
   bucket=collections.Counter();kinds=collections.defaultdict(collections.Counter);nodes=collections.Counter();unprojected=collections.Counter()
   for x in rows:
    hits=tuple(k for k,ids in owners.items() if x['node'] in ids or x['peer'] in ids)
    name='+'.join(hits) if hits else 'neither_declared_projection'
    bucket[name]+=x['count'];kinds[name][x['kind']]+=x['count']
    if name=='neither_declared_projection':unprojected[(x['kind'],x['resource'],x['rule_name'])]+=x['count']
    for nid in (x['node'],x['peer']):
     if nid is not None:nodes[str(nid)]+=x['count']
   total=sum(x['count'] for x in rows)
   results.append({'replicate':run['replicate'],'request':req,'total_selected_events':total,'events_by_mutually_exclusive_projection_touch':dict(sorted(bucket.items())),
    'fraction_touching_neither_declared_projection':bucket['neither_declared_projection']/total if total else None,
    'kind_counts_by_projection':{k:dict(sorted(v.items())) for k,v in sorted(kinds.items())},
    'top_unprojected_kind_resource_rule': [{'kind':k,'resource':resource,'rule_name':rule,'count':count} for (k,resource,rule),count in unprojected.most_common(25)],
    'top_node_ids_by_event_touch':nodes.most_common(15)})
 # The published v2.4 capture asserts identical ownership and traces across traced workers.
 checks['repeated_touch_signatures_identical']=len({json.dumps([(x['request'],x['events_by_mutually_exclusive_projection_touch'],x['kind_counts_by_projection']) for x in results if x['replicate']==r['replicate']],sort_keys=True) for r in traces})==1
 # Check raw replay consistency from the captured rows.
 checks['counts_reconcile']=all(sum(x['events_by_mutually_exclusive_projection_touch'].values())==x['total_selected_events'] for x in results)
 report={'schema_version':1,'run_id':'live-describe-scene-v2.4-boundary-touch-v1-20260927','raw_sha256':sha(RAW),'checks':checks,'all_checks_pass':all(checks.values()),'rows':results,
  'claim_boundary':'Derived classification of selected, aggregated native events against v2.4 declared request lifecycle and shared Scene+Percept node sets. Events touching neither named set may touch unenumerated descendants, shared hubs, or unrelated global state; this does not classify dependency necessity or prove a complete cut.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');return report
if __name__=='__main__':
 p=analyze();print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':p['checks'],'summary':[{'replicate':x['replicate'],'request':x['request'],'total':x['total_selected_events'],'neither_fraction':x['fraction_touching_neither_declared_projection'],'buckets':x['events_by_mutually_exclusive_projection_touch']} for x in p['rows']]},indent=2))
 if not p['all_checks_pass']:raise SystemExit(1)
