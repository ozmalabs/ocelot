#!/usr/bin/env python3
"""Independent checks and summary for the core seed-root admission census."""
from __future__ import annotations
import collections, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CAPTURE=ROOT/'evaluation/reports/substrate_core_seed_profile_admission_census_v1_20261005.json'
ANALYSIS=ROOT/'evaluation/reports/substrate_core_seed_profile_admission_census_v1_analysis_20261005.json'
LOCK=ROOT/'evaluation/substrate_capability/substrate_core_seed_profile_admission_census_v1_lock_20261005.json'
RUNNER=ROOT/'evaluation/substrate_capability/substrate_core_seed_profile_admission_census_v1.py'
CHECKER=ROOT/'scripts/analyze_mint_termination_fragment.py'
ANALYZER=Path(__file__).resolve()

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def independent_accept(rule, edge_attr_types):
    if not isinstance(rule,dict) or set(rule)-{'name','match','effects'}: return False
    match=rule.get('match'); effects=rule.get('effects')
    if not isinstance(match,list) or not match or any(not isinstance(p,list) or len(p)!=3 or not all(isinstance(x,str) for x in p) for p in match): return False
    available={v for p in match for v in (p[0],p[2])}
    if not isinstance(effects,list) or not effects: return False
    for effect in effects:
        if not isinstance(effect,list) or not effect or not isinstance(effect[0],str): return False
        if effect[0]=='add_node_if_absent' and len(effect)==4:
            _,name,typ,attrs=effect
            if not isinstance(name,str) or not isinstance(typ,str) or not isinstance(attrs,dict) or name in available: return False
            if any(not isinstance(k,str) or not (v is None or isinstance(v,(bool,int,str))) for k,v in attrs.items()): return False
            available.add(name)
        elif effect[0]=='add_edge' and len(effect)==5:
            _,src,typ,tgt,attrs=effect
            if not all(isinstance(x,str) for x in (src,typ,tgt)) or attrs!={} or src not in available or tgt not in available or typ in edge_attr_types: return False
        else: return False
    return True

def main():
    before=sha(ANALYZER); capture=json.loads(CAPTURE.read_text()); lock=json.loads(LOCK.read_text())
    agreement=[]; per_root=[]; reasons=collections.Counter(); ids=[]
    for profile in capture['profiles']:
        rules=profile['rule_specs']; outcomes=profile['rule_checkers']; nodes=[]
        # The runner includes no graph snapshot. Derive edge types represented in
        # the checker input by capturing them in each profile row.
        edge_attr_types=set(profile['edge_attr_types'])
        accepted=[]; rows=[]
        for index,(rule,outcome) in enumerate(zip(rules,outcomes)):
            independent=independent_accept(rule,edge_attr_types); reported=bool(outcome['accepted'])
            agreement.append(independent==reported); accepted.append(independent)
            ids.append((profile['root_seed'],rule.get('name')))
            for reason in outcome.get('reasons',[]): reasons[reason]+=1
            rows.append({'name':rule.get('name'),'checker_accept':reported,'independent_accept':independent,'agrees':reported==independent,'reasons':outcome.get('reasons',[])})
        total=len(rules); accepted_count=sum(accepted); aggregate=bool(profile['aggregate_checker']['accepted'])
        per_root.append({'root_seed':profile['root_seed'],'resolved_seed_order':profile['resolved_seed_order'],'active_rules':total,'accepted_rules':accepted_count,'rejected_rules':total-accepted_count,'accepted_fraction':accepted_count/total if total else None,'nonempty_profile_fits_fragment':aggregate if total else None,'independent_profile_fits_fragment':all(accepted) if total else None,'checker_independent_agreement':all(x['agrees'] for x in rows),'rules':rows})
    checks={
      'runner_capture_gates_pass':capture['passed'] and all(capture['checks'].values()),
      'source_lock_stable':capture['locked_inputs']==lock['locked_inputs']==capture['post_run_inputs'],
      'runner_hash_current':sha(RUNNER)==capture['locked_inputs']['runner_sha256'],
      'checker_hash_current':sha(CHECKER)==capture['locked_inputs']['checker_sha256'],
      'independent_analyzer_stable':before==sha(ANALYZER),
      'seventeen_roots_exact':len(per_root)==17 and len({p['root_seed'] for p in per_root})==17,
      'rule_identity_unique_per_profile':len(ids)==len(set(ids)),
      'all_decisions_agree':all(agreement),
      'aggregate_decisions_agree':all(p['nonempty_profile_fits_fragment']==p['independent_profile_fits_fragment'] for p in per_root if p['active_rules']),
      'no_vacuous_profile_claimed_as_candidate':all(p['nonempty_profile_fits_fragment'] is None or p['active_rules']>0 for p in per_root),
    }
    candidates=[p['root_seed'] for p in per_root if p['active_rules'] and p['nonempty_profile_fits_fragment']]
    out={'schema':'SubstrateCoreSeedProfileAdmissionCensusV1Analysis','analyzer_sha256':before,'capture_sha256':sha(CAPTURE),'lock_sha256':sha(LOCK),'summary':{'roots':len(per_root),'nonempty_profiles':sum(p['active_rules']>0 for p in per_root),'candidate_nonempty_profiles':candidates,'total_active_rule_rows':sum(p['active_rules'] for p in per_root),'checker_independent_agreements':sum(agreement),'rejection_reason_counts':dict(reasons)},'per_root':per_root,'checks':checks,'passed':all(checks.values()),'claim_limit':capture['claim_limit']}
    ANALYSIS.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'passed':out['passed'],'checks':checks,'summary':out['summary'],'output':ANALYSIS.relative_to(ROOT).as_posix()})); return 0 if out['passed'] else 2

if __name__=='__main__': raise SystemExit(main())
