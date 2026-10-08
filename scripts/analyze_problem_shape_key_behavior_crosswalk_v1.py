#!/usr/bin/env python3
"""Post-hoc join of structural ProblemShape transfer and BP behavior panels."""
from __future__ import annotations
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
TRANSFER=ROOT/'evaluation/reports/problem_shape_unseeded_schema_transfer_v1_20260927.json'
TRANSFER_ANALYSIS=ROOT/'evaluation/reports/problem_shape_unseeded_schema_transfer_v1_analysis_20260927.json'
BEHAVIOR=ROOT/'evaluation/reports/problem_shape_bp_parameter_semantics_v1_1_20260927.json'
BEHAVIOR_ANALYSIS=ROOT/'evaluation/reports/problem_shape_bp_parameter_semantics_v1_1_analysis_20260927.json'
SOURCE=ROOT/'domains/problem_shape.py'
OUT=ROOT/'evaluation/reports/problem_shape_key_behavior_crosswalk_v1_20260928.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    tr=json.loads(TRANSFER.read_text());ta=json.loads(TRANSFER_ANALYSIS.read_text());br=json.loads(BEHAVIOR.read_text());ba=json.loads(BEHAVIOR_ANALYSIS.read_text())
    pairs=[]
    for w in tr['runs']:
        if w.get('scenario') not in ('bp_recurrence_transfer','mixed_family_separation'):continue
        by={r.get('parameter'):r for r in w.get('records',[]) if r.get('solver_family')=='bp'}
        if {'max_product','sum_product'}<=set(by):
            pairs.append({'panel':w['scenario'],'replicate':w['replicate'],'max_key':by['max_product']['signature_key'],'sum_key':by['sum_product']['signature_key'],'max_final_status':by['max_product']['observation_status_final'],'sum_final_status':by['sum_product']['observation_status_final'],'max_covered_by':by['max_product']['covered_by_final'],'sum_covered_by':by['sum_product']['covered_by_final']})
    behavior=[]
    for w in br['runs']:
        by={r.get('combine'):r for r in w.get('rows',[])}
        if {'max_product','sum_product'}<=set(by):
            behavior.append({'resident_index':w['resident_index'],'replicate':w['replicate'],'same_key':w['same_signature_key'],'max_key':by['max_product']['signature_key'],'sum_key':by['sum_product']['signature_key'],'belief_maps_equal':w['belief_maps_exactly_equal'],'max_abs_belief_delta':w['max_abs_belief_delta'],'max_converged':by['max_product']['answer'].get('converged'),'sum_converged':by['sum_product']['answer'].get('converged')})
    checks={
      'input_transfer_analysis_passes':bool(ta.get('all_checks_pass')),
      'input_behavior_analysis_passes':bool(ba.get('all_checks_pass')),
      'transfer_workers_source_stable':bool(tr.get('all_checks_pass')) and all(w.get('source_stable') for w in tr.get('runs',[])),
      'behavior_workers_source_stable':bool(br.get('all_checks_pass')) and all(w.get('source_stable') for w in br.get('runs',[])),
      'four_transfer_bp_pairs':len(pairs)==4,
      'all_transfer_pairs_share_structural_key':len(pairs)==4 and all(p['max_key']==p['sum_key'] for p in pairs),
      'six_behavior_pairs':len(behavior)==6,
      'all_behavior_pairs_share_structural_key':len(behavior)==6 and all(p['same_key'] and p['max_key']==p['sum_key'] for p in behavior),
      'all_behavior_pairs_differ_in_belief_map':len(behavior)==6 and all(not p['belief_maps_equal'] and p['max_abs_belief_delta']==2.0 for p in behavior),
      'source_axis_is_presence_only': '"has_combine"' in SOURCE.read_text() and '"yes" if at.get("combine") else _ABSENT' in SOURCE.read_text(),
    }
    result={'schema_version':1,'analysis_class':'post-hoc cross-study evidence join; not preregistered','inputs':{p.relative_to(ROOT).as_posix():sha(p) for p in (TRANSFER,TRANSFER_ANALYSIS,BEHAVIOR,BEHAVIOR_ANALYSIS,SOURCE)},'checks':checks,'all_checks_pass':all(checks.values()),'transfer_bp_pairs':pairs,'behavior_pairs':behavior,'interpretation':'ProblemShape successfully groups the two BP calls as one structural schema and transfers recognition across recurrence in the study fixtures. The same key does not imply behavioral equivalence: max_product and sum_product share it while their measured belief maps differ in every behavior-panel pair. The key is appropriate as structural description only; any consumer that treats recognition as a substitute for parameter-level behavior must preserve and evaluate combine values separately.','limits':['The cross-study join relates separate locked panels, not identical Goal instances or one shared held-out checkpoint.','Only three resident networks and two BP combine settings are represented in the behavior panel.','No solver-quality oracle establishes which belief map is preferable.','This establishes one known omitted behavior axis, not general false-mint precision or the full learning class.']}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'all_checks_pass':result['all_checks_pass'],'checks':checks,'transfer_pairs':len(pairs),'behavior_pairs':len(behavior)},indent=2))
    if not result['all_checks_pass']:raise SystemExit('crosswalk checks failed')
if __name__=='__main__':main()
