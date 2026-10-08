#!/usr/bin/env python3
"""Analyze population traversal and candidate work in the locked GenInfer probe."""
from __future__ import annotations
import hashlib, json, statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAP=ROOT/'evaluation/reports/geninfer_scoped_population_trace_v1_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/geninfer_scoped_population_trace_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/geninfer_scoped_population_trace_v1_analysis_20261005.json'
FAMILY={1:'shape_decode',2:'transform_decode',3:'dim_infer',4:'gen_infer',5:'time_infer',6:'depth_infer',
 7:'blink_bridge',8:'gap_abduce',9:'gap_verify',10:'prog_eval_decode',11:'join_render',12:'ratio_induce',13:'support_infer'}
KINDS={'dynamic_helper_invocation','helper_codebook_population_node','helper_node_attribute_examined',
 'helper_codebook_part_parsed','helper_relation_cue_population_node','helper_search_candidate',
 'helper_candidate_part_scored','helper_graph_term_node_decoded','helper_render_rule_candidate',
 'helper_auxiliary_population_node'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 raw=json.loads(CAP.read_text());lock=json.loads(LOCK.read_text());groups=defaultdict(list);errors=[]
 for row in raw['cases']:
  mode=row['case']['mode'];groups[mode].append(row)
  if not row.get('source_stable'):errors.append(f"{mode}/{row.get('replicate')}: source drift")
  trace=row.get('runtime_work_trace',{})
  if trace.get('dropped')!=0:errors.append(f"{mode}/{row.get('replicate')}: trace drops")
  if len(row.get('outputs',[]))!=2 or not all(o.get('oracle_exact') and o.get('target_generator_present') for o in row.get('outputs',[])):
   errors.append(f"{mode}/{row.get('replicate')}: exact positive output failed")
  if not all(m.get('members_agree') for m in row.get('scope_membership',[])):
   errors.append(f"{mode}/{row.get('replicate')}: scope membership mismatch")
 summary={};row_signatures={};pids=set()
 for mode,rows in sorted(groups.items()):
  if len(rows)!=3:errors.append(f'{mode}: expected three replicates, got {len(rows)}')
  pids.update(r['pid'] for r in rows)
  per_rep=[]
  for r in rows:
   counts=Counter()
   for event in r['runtime_work_trace']['rows']:
    if len(event)!=6:errors.append(f'{mode}/{r.get("replicate")}: malformed work row');continue
    _,_,rule_uid,kind,helper,units=event
    if str(kind) in KINDS and int(helper or 0)==4:
     counts[str(kind)]+=int(units)
     if int(rule_uid)==0:errors.append(f'{mode}/{r.get("replicate")}: GenInfer work lacks rule UID')
   per_rep.append({'replicate':r['replicate'],'rule_uid':sorted({int(e[2]) for e in r['runtime_work_trace']['rows']
    if len(e)==6 and int(e[4] or 0)==4 and str(e[3]) in KINDS}),
    'geninfer_work':dict(sorted(counts.items()))})
   row_signatures.setdefault(mode,[]).append(dict(sorted(counts.items())))
  all_kinds=sorted({kind for counts in row_signatures[mode] for kind in counts})
  median_work={kind:int(statistics.median(counts.get(kind,0) for counts in row_signatures[mode])) for kind in all_kinds}
  summary[mode]={'replicates':len(rows),'distinct_worker_pids':len({r['pid'] for r in rows}),
   'median_wall_ns':sorted(int(r['closure_wall_ns']) for r in rows)[1],
   'median_cpu_ns':sorted(int(r['closure_cpu_ns']) for r in rows)[1],
   'median_work_by_kind':dict(sorted(median_work.items())), 'per_replicate':per_rep}
 signatures_reproduce=all(len({json.dumps(s,sort_keys=True) for s in sigs})==1 for sigs in row_signatures.values())
 if not signatures_reproduce:errors.append('work counters did not reproduce within condition')
 if len(raw['cases'])!=9:errors.append(f"expected 9 captures, found {len(raw['cases'])}")
 scoped=summary.get('frame_scoped',{}).get('median_work_by_kind',{})
 global_=summary.get('explicit_global',{}).get('median_work_by_kind',{})
 unscoped=summary.get('unscoped_global',{}).get('median_work_by_kind',{})
 comparisons={}
 for kind in ('helper_codebook_population_node','helper_node_attribute_examined','helper_codebook_part_parsed','helper_search_candidate'):
  comparisons[kind]={'frame_scoped':scoped.get(kind,0),'explicit_global':global_.get(kind,0),'unscoped_global':unscoped.get(kind,0)}
 checks={'all_three_conditions_have_three_replicates':len(raw['cases'])==9 and all(len(v)==3 for v in groups.values()),
  'fresh_worker_processes':len(pids)==9,'source_stable_and_no_trace_drops':not any('source drift' in e or 'trace drops' in e for e in errors),
  'exact_outputs_and_scope_membership':not any('exact positive' in e or 'scope membership' in e for e in errors),
  'work_counts_reproduce_within_condition':signatures_reproduce,
  'helper_work_rule_attributed':not any('lacks rule UID' in e for e in errors),
  'scoped_codebook_work_is_lower_than_global':scoped.get('helper_codebook_part_parsed',0)<global_.get('helper_codebook_part_parsed',0)
   and scoped.get('helper_search_candidate',0)<global_.get('helper_search_candidate',0),
  'typed_population_scan_is_not_reduced_by_scope':scoped.get('helper_codebook_population_node',0)==global_.get('helper_codebook_population_node',-1)}
 result={'schema':'GenInferScopedPopulationTraceV1Analysis','capture_sha256':sha(CAP),'lock_sha256':sha(LOCK),
  'analyzer_sha256':sha(Path(__file__)),'checks':checks,'summary':summary,'scoped_vs_global':comparisons,
  'errors':errors,'passed':all(checks.values()),'claim_limit':'Authored two-frame GenInfer fixtures only. The production scoped loader still enumerates the full typed population before filtering; the comparison does not discover safe scopes or establish natural-task prevalence.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'checks':checks,'scoped_vs_global':comparisons,'passed':result['passed'],'errors':errors},indent=2))
 if not result['passed']:raise SystemExit('scoped population trace analysis failed')
if __name__=='__main__':main()
