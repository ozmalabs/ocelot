#!/usr/bin/env python3
"""Read-only per-root census of core seed rule profiles against finite-key v0."""
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
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_core_seed_profile_admission_census_v1.py';PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_CORE_SEED_PROFILE_ADMISSION_CENSUS_V1_PREREG_20261005.md';CHECKER=ROOT/'scripts/analyze_mint_termination_fragment.py';LOCK=ROOT/'evaluation/substrate_capability/substrate_core_seed_profile_admission_census_v1_lock_20261005.json';OUT=ROOT/'evaluation/reports/substrate_core_seed_profile_admission_census_v1_20261005.json'
RUST=('py.rs','rewrite.rs','substrate.rs','graph.rs','persist.rs')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def closure(root):
    done=[];seen=set()
    def visit(sid):
        if sid in seen:return
        m=manifest_for(sid)
        for dep in m.get('depends_on',()):visit(str(dep))
        seen.add(sid);done.append(sid)
    visit(root);return done
def all_seed_ids():return sorted({sid for root in CORE_SEEDS for sid in closure(root)})
def inputs():
    prov=assert_measuring_engine();seeds=all_seed_ids()
    return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'checker_sha256':sha(CHECKER),'native_sha256':sha(Path(_native.__file__).resolve()),'engine_fingerprint':prov['source_fingerprint'],'seed_registry_sha256':sha(ROOT/'domains/seed_registry.py'),'boot_core_sha256':sha(ROOT/'substrate/boot_core.py'),'seed_loader_sha256':sha(ROOT/'substrate/seed_loader.py'),'seed_manifest_sha256':{sid:sha(ROOT/'seeds'/f'{sid}.json') for sid in seeds},'rust_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in RUST},'build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),'core_seed_order':list(CORE_SEEDS)}
def spec(r):
    q={k:r[k] for k in ('name','match','effects') if k in r}
    for k in ('where','batch','match_type'):
        if r.get(k) not in (None,False):q[k]=r[k]
    return q
def main():
    if sys.argv[1:]==['--lock']:
        if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite seed-profile census artifacts')
        LOCK.write_text(json.dumps({'schema':'SubstrateCoreSeedProfileAdmissionCensusV1Lock','locked_inputs':inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    locked=inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=locked:raise SystemExit('missing or stale seed-profile census lock')
    profiles=[]
    for root in CORE_SEEDS:
        s,_=boot_core(seeds=(root,));rules=s._inner.export_rules();graph=s._inner.graph_to_dict();active=[r for r in rules if r.get('active',True)];nodes=[str(n['id']) for n in graph['nodes']];edges=[[str(e['src']),e['type'],str(e['tgt']),e.get('attrs',{})] for e in graph['edges']];specs=[spec(r) for r in active]
        outcomes=[analyze([q],nodes,edges) for q in specs];aggregate=analyze(specs,nodes,edges)
        uids=[r.get('rule_uid') for r in active]
        profiles.append({'root_seed':root,'resolved_seed_order':closure(root),'graph_nodes':len(nodes),'graph_edges':len(edges),'exported_rules':len(rules),'active_rules':len(active),'inactive_rules':len(rules)-len(active),'active_rule_uids':uids,'rule_specs':specs,'rule_checkers':outcomes,'edge_attr_types':sorted({e[1] for e in edges if e[3]}),'aggregate_checker':aggregate})
    post=inputs();checks={'source_stable':locked==post,'seventeen_roots_exact':[p['root_seed'] for p in profiles]==list(CORE_SEEDS),'unique_root_rows':len({p['root_seed'] for p in profiles})==17,'rule_rows_aligned':all(p['active_rules']==len(p['rule_specs'])==len(p['rule_checkers'])==len(p['active_rule_uids']) for p in profiles),'unique_rule_uids_per_profile':all(len(p['active_rule_uids'])==len(set(p['active_rule_uids'])) for p in profiles),'aggregate_matches_individual':all(p['aggregate_checker']['accepted']==all(x['accepted'] for x in p['rule_checkers']) for p in profiles)}
    report={'schema':'SubstrateCoreSeedProfileAdmissionCensusV1','locked_inputs':locked,'post_run_inputs':post,'profiles':profiles,'checks':checks,'passed':all(checks.values()),'claim_limit':'read-only source-locked census of each CORE_SEEDS root and declared dependency closure against the current conservative finite-key fragment; not a general termination analysis or sufficiency claim.'}
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':report['passed'],'checks':checks,'roots':len(profiles),'nonempty_profiles':sum(p['active_rules']>0 for p in profiles),'full_profile_accepts':[p['root_seed'] for p in profiles if p['active_rules'] and p['aggregate_checker']['accepted']],'output':OUT.relative_to(ROOT).as_posix()}));return 0 if report['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
