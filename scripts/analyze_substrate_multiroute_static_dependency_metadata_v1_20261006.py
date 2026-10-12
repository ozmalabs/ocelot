#!/usr/bin/env python3
"""Reconcile the multi-route dynamic traces against observed rules' static keys."""
from __future__ import annotations
import gzip,hashlib,importlib.util,json
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FRAME=ROOT/'evaluation/reports/multiroute_frame_access_v1_20261006/capture.json.gz'
META=ROOT/'evaluation/reports/multiroute_frame_access_v1_20261006/static_rule_metadata.json'
OUT=ROOT/'evaluation/reports/multiroute_frame_access_v1_20261006/dependency_reconciliation.json'
OLD=ROOT/'scripts/analyze_rooted_frame_access_scope_reconciliation_v1_2.py'
s=importlib.util.spec_from_file_location('rooted_reconciliation',OLD);old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
frame=json.loads(gzip.decompress(FRAME.read_bytes()));meta=json.loads(META.read_text());meta_by={r['condition']:r for r in meta['runs']};byroute={}
def static_pair_set(observed,implicit_reads):
 pairs=set()
 for wuid,w in observed.items():
  for ruid,r in observed.items():
   wr=set(w['writes']);rr=set(r['reads'])|set(r['term_edge_reads'])|implicit_reads.get(ruid,set())
   if wr&rr or w['writes_any'] or r['reads_any']:pairs.add((wuid,ruid))
 return pairs
for run in frame['runs']:
 cond=run['condition'];table={int(x['rule_uid']):x for x in meta_by[cond]['rule_access_table']};trace=run['postcheckpoint_rule_access']['events']
 observed={int(e['rule_uid']) for e in trace};unresolved=sorted(observed-set(table));names_mismatch=[];categories=Counter();mismatches=[];reads={};writes={};outside_by_rule=Counter();outside_by_kind=Counter();implicit_reads=defaultdict(set)
 for e in trace:
  uid=int(e['rule_uid']);rule=table.get(uid);name=str(e.get('rule_name'))
  if rule is not None and name!=rule['rule_name']:names_mismatch.append({'uid':uid,'trace_name':name,'static_name':rule['rule_name']})
  if rule is None:cat='uid_unresolved'
  else:cat=old.static_match(e,rule)
  count=int(e['count']);categories[cat]+=count
  if 'outside_cut' in e.get('scope_roles',[]):
   outside_by_rule[(uid,rule['rule_name'] if rule else name)] += count
   outside_by_kind[(str(e['kind']),cat)] += count
  if e['kind']=='effect_attr_compare_read' and e.get('resource') is not None:
   implicit_reads[uid].add('attr:'+str(e['resource']))
  if cat in ('static_key_mismatch','implicit_read_not_declared'):
   mismatches.append({'rule_uid':uid,'rule_name':rule['rule_name'] if rule else name,'kind':e['kind'],'resource':e.get('resource'),'scope_roles':e.get('scope_roles'),'count':count,'category':cat})
  identity=old.concrete_identity(e)
  if identity:
   direction,key=identity;(reads if direction=='read' else writes).setdefault(key,set()).add(uid)
 # Pair graph is based on rules that actually generated a trace row in this route.
 observed_rules={u:table[u] for u in observed if u in table};static_pairs=static_pair_set(observed_rules,implicit_reads)
 dynamic_pairs=set()
 for key,writers in writes.items():
  for reader in reads.get(key,()):
   for writer in writers:dynamic_pairs.add((writer,reader))
 byroute.setdefault(cond,[]).append({'replicate':run['replicate'],'trace_events':run['postcheckpoint_rule_access']['event_count'],
  'observed_rule_uids':len(observed),'unresolved_rule_uids':unresolved,'rule_name_mismatches':names_mismatch,
  'static_event_class_counts_weighted':dict(sorted(categories.items())),'static_key_mismatch_weight':sum(x['count'] for x in mismatches),
  'static_key_mismatches':mismatches,'concrete_read_identity_count':len(reads),'concrete_write_identity_count':len(writes),
  'dynamic_concrete_dependency_pairs':len(dynamic_pairs),'static_possible_pairs_among_observed_rules':len(static_pairs),
  'dynamic_pairs_outside_static_projection':[list(x) for x in sorted(dynamic_pairs-static_pairs)],
  'static_pairs_without_observed_concrete_overlap':len(static_pairs-dynamic_pairs),
  'outside_cut_events_by_kind_and_static_class':{f'{k}/{c}':v for (k,c),v in sorted(outside_by_kind.items())},
  'top_outside_cut_rules':[{'rule_uid':uid,'rule_name':name,'weighted_events':count,'reads_any':table[uid]['reads_any'] if uid in table else None,'read_key_count':len(table[uid]['reads'])+len(table[uid]['term_edge_reads']) if uid in table else None} for (uid,name),count in outside_by_rule.most_common(20)]})
checks={'five_route_metadata_rows':len(meta['runs'])==5,'metadata_source_stable':meta['locked_inputs']==meta['post_run_inputs'] and all(r['source_stable'] for r in meta['runs']),
 'worker_inputs_match_parent_lock':all(r['locked_inputs']==meta['locked_inputs']['harvest_inputs'] and r['post_run_inputs']==meta['locked_inputs']['harvest_inputs'] for r in meta['runs']),
 'ten_frame_workers':len(frame['runs'])==10,'all_trace_uids_resolve':all(not x['unresolved_rule_uids'] for rows in byroute.values() for x in rows),
 'all_trace_names_resolve':all(not x['rule_name_mismatches'] for rows in byroute.values() for x in rows),
 'metadata_route_tables_have_unique_uids':all(len({int(x['rule_uid']) for x in r['rule_access_table']})==len(r['rule_access_table']) for r in meta['runs']),
 'metadata_locks_frame_protocol':meta['locked_inputs']['frame_lock_sha256']==('sha256:'+hashlib.sha256((ROOT/'evaluation/substrate_capability/multiroute_frame_access_v1_20261006_lock.json').read_bytes()).hexdigest())}
out={'schema':'MultiRouteStaticDependencyReconciliationV1','integrity_checks':checks,'integrity_pass':all(checks.values()),'routes':byroute,
 'interpretation':'Observed access resource keys are compared with declared keys for observed RuleUIDs only. A static-key match does not prove dependency completeness; unmatched or resource-free event kinds may be uncheckable. Concrete overlap is a dynamic witness, not a complete dependency graph. No semantic-necessity or host-side-read claim is made.'}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'analysis':str(OUT.relative_to(ROOT)),'integrity_checks':checks,'integrity_pass':out['integrity_pass'],'route_mismatch_weights':{k:[x['static_key_mismatch_weight'] for x in v] for k,v in byroute.items()},'top_rule_per_route':{k:v[0]['top_outside_cut_rules'][:3] for k,v in byroute.items()}},indent=2))
if not out['integrity_pass']:raise SystemExit(1)
