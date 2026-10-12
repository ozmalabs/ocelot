#!/usr/bin/env python3
"""Read-only census of default core rules against the finite-key fragment."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
import domains.seed_registry
from domains.engine_provenance import assert_measuring_engine
from substrate.boot_core import CORE_SEEDS,boot_core
from substrate.seed_loader import manifest_for
from substrate_rs import _native
from analyze_mint_termination_fragment import analyze
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_core_rule_finite_key_admission_census_v1.py';PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CORE_RULE_FINITE_KEY_ADMISSION_CENSUS_V1_PREREG_20261005.md';CHECKER=ROOT/'scripts/analyze_mint_termination_fragment.py';LOCK=ROOT/'evaluation/substrate_capability/substrate_core_rule_finite_key_admission_census_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/substrate_core_rule_finite_key_admission_census_v1_20261005.json'
RUST=('py.rs','rewrite.rs','substrate.rs','graph.rs','persist.rs')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def seed_closure():
    done=[];seen=set()
    def visit(sid):
        if sid in seen:return
        m=manifest_for(sid)
        for dep in m.get('depends_on',()):visit(str(dep))
        seen.add(sid);done.append(sid)
    for sid in CORE_SEEDS:visit(sid)
    return done
def inputs():
    prov=assert_measuring_engine();seeds=seed_closure()
    return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'checker_sha256':sha(CHECKER),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_registry_sha256':sha(ROOT/'domains/seed_registry.py'),'boot_core_sha256':sha(ROOT/'substrate/boot_core.py'),'seed_loader_sha256':sha(ROOT/'substrate/seed_loader.py'),'seed_manifest_sha256':{sid:sha(ROOT/'seeds'/f'{sid}.json') for sid in seeds},'rust_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in RUST},'build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),'core_seed_order':list(CORE_SEEDS),'resolved_seed_order':seeds}
def rule_spec(r):
    q={k:r[k] for k in ('name','match','effects') if k in r}
    for k in ('where','batch','match_type'):
        if r.get(k) not in (None,False):q[k]=r[k]
    return q
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite core admission census artifacts')
        LOCK.write_text(json.dumps({'schema':'SubstrateCoreRuleFiniteKeyAdmissionCensusV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale core admission census lock')
    s,_=boot_core();rules=s._inner.export_rules();graph=s._inner.graph_to_dict();active=[r for r in rules if r.get('active',True)];specs=[rule_spec(r) for r in active]
    node_ids=[str(n['id']) for n in graph['nodes']];edges=[[str(e['src']),e['type'],str(e['tgt']),e.get('attrs',{})] for e in graph['edges']]
    per_rule=[]
    for raw,spec in zip(active,specs):
        result=analyze([spec],node_ids,edges)
        per_rule.append({'name':raw.get('name'),'rule_uid':raw.get('rule_uid'),'active':raw.get('active',True),'mutation_protected':raw.get('mutation_protected'),'has_where':raw.get('where') is not None,'batch':bool(raw.get('batch',False)),'match_type':raw.get('match_type'),'effect_ops':[e[0] if isinstance(e,list) and e else '<malformed>' for e in raw.get('effects',[])],'rule_spec':spec,'checker':result})
    whole=analyze(specs,node_ids,edges);post=inputs()
    checks={'source_stable':locked==post,'resolved_seed_order_stable':locked['resolved_seed_order']==post['resolved_seed_order'],'exported_rule_count_stable':len(rules)>=len(active)>0,'graph_inventory_complete':len(node_ids)==len(graph['nodes']) and len(edges)==len(graph['edges']),'one_result_per_active_rule':len(per_rule)==len(active),'aggregate_checker_matches_profile':whole['accepted']==all(x['checker']['accepted'] for x in per_rule)}
    report={'schema':'SubstrateCoreRuleFiniteKeyAdmissionCensusV1','locked_inputs':locked,'post_run_inputs':post,'profile':{'name':'boot_core_default','core_seed_order':list(CORE_SEEDS),'resolved_seed_order':locked['resolved_seed_order'],'exported_rules':len(rules),'active_rules':len(active),'inactive_rules':len(rules)-len(active),'graph_nodes':len(node_ids),'graph_edges':len(edges)},'initial_graph':{'node_ids':node_ids,'edges':edges},'per_rule':per_rule,'aggregate_checker':whole,'checks':checks,'passed':all(checks.values()),'claim_limit':'read-only syntax census of active rules in the default boot_core profile against one sufficient finite-key fragment; rejection does not imply nontermination and no rule execution or admission change is measured.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'exported_rules':len(rules),'active_rules':len(active),'profile_accepted':whole['accepted'],'individually_accepted':sum(r['checker']['accepted'] for r in per_rule),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
