#!/usr/bin/env python3
"""Source-locked admission census across every registered seed root."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python'),str(ROOT/'scripts')]
from domains.engine_provenance import engine_preamble,assert_measuring_engine
engine_preamble()
import domains.seed_registry
from substrate.seeds import REGISTRY
from substrate.seed_loader import SEED_DIR,manifest_for
from substrate.boot_core import boot_core
from substrate_rs import _native
from analyze_mint_termination_fragment import analyze
RUNNER=Path(__file__).resolve()
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_registered_seed_profile_admission_census_v1.py'
PROTOCOL=ROOT/'docs/research/engine_substrate/REGISTERED_SEED_PROFILE_ADMISSION_CENSUS_V1_PREREG_20261005.md'
LOCK=ROOT/'evaluation/substrate_capability/registered_seed_profile_admission_census_v1_lock_20261005.json'
OUT=ROOT/'evaluation/reports/registered_seed_profile_admission_census_v1_20261005.json'
RUST=('py.rs','rewrite.rs','substrate.rs','graph.rs','persist.rs')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def registered_roots():return REGISTRY.known()
def closure(root):
 order=[];seen=set();missing=[]
 def visit(sid):
  if sid in seen:return
  path=SEED_DIR/f'{sid}.json'
  if not path.exists():missing.append(sid);return
  manifest=manifest_for(sid)
  for dep in manifest.get('depends_on',()):visit(str(dep))
  if sid not in seen:seen.add(sid);order.append(sid)
 visit(root);return order,sorted(set(missing))
def closures():return {root:{'order':c,'missing':m} for root in registered_roots() for c,m in [closure(root)]}
def lock_inputs():
 prov=assert_measuring_engine();cs=closures();seed_ids=sorted({sid for x in cs.values() for sid in x['order']})
 return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PROTOCOL),'checker_sha256':sha(ROOT/'scripts/analyze_mint_termination_fragment.py'),'engine_fingerprint':prov['source_fingerprint'],'native_sha256':sha(Path(_native.__file__).resolve()),'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'seed_registry_sha256':sha(ROOT/'domains/seed_registry.py'),'seed_registry_order':registered_roots(),'boot_core_sha256':sha(ROOT/'substrate/boot_core.py'),'seed_loader_sha256':sha(ROOT/'substrate/seed_loader.py'),'seed_registry_module_sha256':sha(ROOT/'substrate/seeds.py'),'seed_manifest_sha256':{sid:sha(SEED_DIR/f'{sid}.json') for sid in seed_ids},'root_closures':cs,'rust_sha256':{name:sha(ROOT/'runners/dsl/src'/name) for name in RUST},'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock')}
def spec(r):
 q={k:r[k] for k in ('name','match','effects') if k in r}
 for k in ('where','batch','match_type'):
  if r.get(k) not in (None,False):q[k]=r[k]
 return q
def main():
 if sys.argv[1:]==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite census artifacts')
  LOCK.write_text(json.dumps({'schema':'RegisteredSeedProfileAdmissionCensusV1Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 before=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=before:raise SystemExit('missing or stale census lock')
 profiles=[]
 for root in before['seed_registry_order']:
  cr=before['root_closures'][root]
  root_present=(SEED_DIR/f'{root}.json').exists()
  if not root_present:
   profiles.append({'root_seed':root,'status':'root_manifest_missing','resolved_seed_order':cr['order'],'missing_manifests':cr['missing']});continue
  if cr['missing']:
   profiles.append({'root_seed':root,'status':'dependency_manifest_missing','resolved_seed_order':cr['order'],'missing_manifests':cr['missing']});continue
  sub,_=boot_core(seeds=(root,));rules=sub._inner.export_rules();active=[r for r in rules if r.get('active',True)]
  graph=sub._inner.graph_to_dict();nodes=[str(n['id']) for n in graph['nodes']]
  edges=[[str(e['src']),e['type'],str(e['tgt']),e.get('attrs',{})] for e in graph['edges']]
  specs=[spec(r) for r in active];checks=[analyze([q],nodes,edges) for q in specs]
  aggregate=analyze(specs,nodes,edges);edge_attr_types=sorted({e[1] for e in edges if e[3]})
  profiles.append({'root_seed':root,'status':'booted','resolved_seed_order':cr['order'],'graph_nodes':len(nodes),'graph_edges':len(edges),'exported_rules':len(rules),'active_rules':len(active),'active_rule_uids':[r.get('rule_uid') for r in active],'rule_specs':specs,'rule_checkers':checks,'edge_attr_types':edge_attr_types,'aggregate_checker':aggregate})
 after=lock_inputs();checks={'source_lock_stable':before==after,'registry_population_exact':len(profiles)==len(before['seed_registry_order']) and [p['root_seed'] for p in profiles]==before['seed_registry_order'],'unique_root_rows':len({p['root_seed'] for p in profiles})==len(profiles),'booted_rule_rows_aligned':all(p['active_rules']==len(p['rule_specs'])==len(p['rule_checkers'])==len(p['active_rule_uids']) for p in profiles if p['status']=='booted'),'all_unavailable_profiles_explicit':all(p['status'] in ('booted','root_manifest_missing','dependency_manifest_missing') for p in profiles),'nonempty_aggregate_agrees_with_rule_rows':all((p['aggregate_checker']['accepted']==all(r['accepted'] for r in p['rule_checkers'])) for p in profiles if p['status']=='booted')}
 result={'schema':'RegisteredSeedProfileAdmissionCensusV1','locked_inputs':before,'post_run_inputs':after,'profiles':profiles,'checks':checks,'passed':all(checks.values()),'claim_limit':'source-locked current registry coverage against the conservative finite-key fragment; no implication of runtime termination, profile usefulness, or enforcement.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'registered':len(profiles),'booted':sum(p['status']=='booted' for p in profiles),'unavailable':sum(p['status']!='booted' for p in profiles),'output':OUT.relative_to(ROOT).as_posix()}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
