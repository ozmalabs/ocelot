#!/usr/bin/env python3
"""Independent verification and reason summary for the core-rule census."""
from __future__ import annotations
import collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];CAPTURE=ROOT/'evaluation/reports/substrate_core_rule_finite_key_admission_census_v1_20261005.json';ANALYSIS=ROOT/'evaluation/reports/substrate_core_rule_finite_key_admission_census_v1_analysis_20261005.json';LOCK=ROOT/'evaluation/substrate_capability/substrate_core_rule_finite_key_admission_census_v1_lock_20261005.json';RUNNER=ROOT/'evaluation/substrate_capability/substrate_core_rule_finite_key_admission_census_v1.py';CHECKER=ROOT/'scripts/analyze_mint_termination_fragment.py';ANALYZER=Path(__file__).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def independent_accept(rule,edge_attr_types):
    """Second conservative implementation of the finite-key grammar gate."""
    if not isinstance(rule,dict) or set(rule)-{'name','match','effects'}:return False
    match=rule.get('match');effects=rule.get('effects')
    if not isinstance(match,list) or not match:return False
    if any(not isinstance(p,list) or len(p)!=3 or not all(isinstance(x,str) for x in p) for p in match):return False
    available={v for p in match for v in (p[0],p[2])}
    if not isinstance(effects,list) or not effects:return False
    for e in effects:
        if not isinstance(e,list) or not e or not isinstance(e[0],str):return False
        if e[0]=='add_node_if_absent' and len(e)==4:
            _,name,typ,attrs=e
            if not isinstance(name,str) or not isinstance(typ,str) or not isinstance(attrs,dict) or name in available:return False
            if any(not isinstance(k,str) or not (v is None or isinstance(v,(bool,int,str))) for k,v in attrs.items()):return False
            available.add(name)
        elif e[0]=='add_edge' and len(e)==5:
            _,src,typ,tgt,attrs=e
            if not all(isinstance(x,str) for x in (src,typ,tgt)) or attrs!={} or src not in available or tgt not in available or typ in edge_attr_types:return False
        else:return False
    return True
def main():
    before=sha(ANALYZER);d=json.loads(CAPTURE.read_text());lock=json.loads(LOCK.read_text());ids=d['initial_graph']['node_ids'];edges=d['initial_graph']['edges'];edge_attr_types={e[1] for e in edges if len(e)==4 and e[3]};unique_ids=len(ids)==len(set(ids));known=set(ids);edge_valid=all(isinstance(e,list) and len(e)==4 and e[0] in known and e[2] in known and isinstance(e[1],str) and isinstance(e[3],dict) for e in edges);attr_types={e[1] for e in edges if isinstance(e,list) and len(e)==4 and isinstance(e[3],dict) and e[3]}
    all_independent=[];per_rule=[];cause_counts=collections.Counter()
    for row in d['per_rule']:
        spec=row['rule_spec'];ind=independent_accept(spec,attr_types);reported=bool(row['checker']['accepted']);all_independent.append(ind);reasons=row['checker']['reasons'];
        for reason in reasons:
            if 'unsupported rule fields' in reason:cause='where/batch/extra semantic field'
            elif 'outside the insertion-only finite-key fragment' in reason:cause='effect outside finite-key fragment'
            elif 'edge endpoints must be bound' in reason:cause='effect endpoint not bound in positive match'
            elif 'AddEdge may replace attributes' in reason:cause='edge type has initial attributes'
            elif 'match must be a nonempty' in reason:cause='unsupported match form'
            elif 'effects must be a nonempty' in reason:cause='missing/empty effects'
            else:cause='other checker rejection'
            cause_counts[cause]+=1
        per_rule.append({'name':row['name'],'rule_uid':row['rule_uid'],'checker_accept':reported,'independent_accept':ind,'agrees':reported==ind,'has_where':row['has_where'],'batch':row['batch'],'effect_ops':row['effect_ops'],'rejection_reasons':reasons})
    checks={'runner_capture_gates_pass':d['passed'] and all(d['checks'].values()),'source_lock_stable':d['locked_inputs']==lock['locked_inputs']==d['post_run_inputs'],'runner_hash_current':sha(RUNNER)==d['locked_inputs']['runner_sha256'],'checker_hash_current':sha(CHECKER)==d['locked_inputs']['checker_sha256'],'independent_analyzer_stable':before==sha(ANALYZER),'initial_node_ids_unique':unique_ids,'initial_edges_endpoint_closed':edge_valid,'per_rule_count_matches_active':len(per_rule)==d['profile']['active_rules'],'checker_independent_agreement':all(x['agrees'] for x in per_rule),'aggregate_gate_matches_independent_profile':bool(d['aggregate_checker']['accepted'])==all(all_independent),'aggregate_gate_matches_capture_summary':bool(d['aggregate_checker']['accepted'])==all(x['checker_accept'] for x in per_rule)}
    accepted=sum(x['checker_accept'] for x in per_rule);rejected=len(per_rule)-accepted
    out={'schema':'SubstrateCoreRuleFiniteKeyAdmissionCensusV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'profile':d['profile'],'summary':{'active_rules':len(per_rule),'accepted_rules':accepted,'rejected_rules':rejected,'accepted_fraction':accepted/len(per_rule) if per_rule else None,'profile_fits_fragment':bool(d['aggregate_checker']['accepted']),'has_where_rules':sum(x['has_where'] for x in per_rule),'batch_rules':sum(x['batch'] for x in per_rule),'effect_op_counts':dict(collections.Counter(op for row in per_rule for op in row['effect_ops'])),'rejection_reason_counts':dict(cause_counts)},'per_rule':per_rule,'checks':checks,'passed':all(checks.values()),'claim_limit':d['claim_limit']};ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'summary':out['summary'],'output':ANALYSIS.relative_to(ROOT).as_posix()}));return 0 if out['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
