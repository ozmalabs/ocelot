#!/usr/bin/env python3
"""Current-source scale replay for interacting finite-key positive rules."""
from __future__ import annotations
import gzip,hashlib,json,platform,subprocess,sys,time
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/reports/mint_termination_interaction_v2_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/mint_termination_interaction_v2_lock_20261004.json'
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CLOSURE_RULE_INTERACTION_V2_PREREG_20261004.md'
RUNNER=Path(__file__).resolve(); ANALYZER=ROOT/'scripts/analyze_mint_termination_interaction_v2.py'
RUST=('py.rs','rewrite.rs','graph.rs','substrate.rs','scale_audit.rs','term.rs','jsonio.rs')
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
from analyze_mint_termination_fragment import analyze
from substrate_rs import _native

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PREREG),'checker_sha256':sha(ROOT/'scripts/analyze_mint_termination_fragment.py'),'manifest_helper_sha256':sha(ROOT/'scripts/substrate_run_manifest.py'),'rust_sources_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in RUST},'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def rules():return {'A':{'name':'mint_A','match':[['x','link','y']],'effects':[['add_node_if_absent','a','Witness',{'tag':'A'}],['add_edge','x','made_a','a',{}]]},'B':{'name':'mint_B','match':[['x','link','y'],['y','rel','z']],'effects':[['add_node_if_absent','b','Witness',{'tag':'B'}],['add_edge','x','made_b','b',{}]]},'C':{'name':'join_AB','match':[['x','made_a','a'],['x','made_b','b']],'effects':[['add_node_if_absent','c','Witness',{'tag':'C'}],['add_edge','a','result','c',{}],['add_edge','b','result','c',{}]]}}
def input_edges(n,topology):
    pairs=[(i,(i+1)%n) for i in range(n)] if topology=='cycle' else [(i,i+1) for i in range(n-1)]
    return [(et,s,t) for et in ('link','rel') for s,t in pairs]
def one_case(n,topology,order,rep):
    edges0=input_edges(n,topology); rb=rules(); specs=[rb[x] for x in order]
    ids=[f'n{i}' for i in range(n)]; edges=[[f'n{s}',et,f'n{t}',{}] for et,s,t in edges0]
    static=analyze(specs,ids,edges)
    t0=time.perf_counter_ns(); sub=_native.Substrate(); native_ids=[sub.add_node('Seed',{'idx':i}) for i in range(n)]
    for et,s,t in edges0:sub.add_edge_unchecked(native_ids[s],et,native_ids[t])
    for rule in specs:sub.add_rule(rule)
    report=sub.run_rules_report(200000,False); graph=sub.graph_to_dict(); elapsed=time.perf_counter_ns()-t0
    return {'case_id':f'n{n}_{topology}_{order}_r{rep}','n_initial_nodes':n,'topology':topology,'rule_order':order,'replicate':rep,'initial_node_ids':ids,'initial_edges':edges,'rule_specs':specs,'static_analysis':static,'native_report':report,'native_graph':graph,'execution_wall_ns':elapsed}
def main():
    if sys.argv[1:]==['--lock']:
        if OUT.exists():raise SystemExit('refusing to overwrite capture')
        LOCK.write_text(json.dumps({'schema':'MintTerminationInteractionV2Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=lock_inputs():raise SystemExit('missing or stale source lock')
    from domains.engine_provenance import build_is_stale
    stale=build_is_stale(str(ROOT))
    if stale:raise SystemExit(f'native build stale: {stale}')
    locked=lock_inputs();cells=[one_case(n,top,o,r) for n in (4,8,16,32,64,128,256) for top in ('cycle','line') for o in ('ABC','CBA','BCA') for r in (1,2,3)]
    post=lock_inputs(); failed=[c['case_id'] for c in cells if c['native_report']['status']!='fixed_point' or c['native_report']['budget_overshoot'] or c['native_report']['progress_steps']>c['static_analysis']['progress_steps_upper_bound']]
    result={'schema':'MintTerminationInteractionV2','run_id':'mint-termination-interaction-v2-20261004','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),'design':{'N':[4,8,16,32,64,128,256],'topologies':['cycle','line'],'rule_orders':['ABC','CBA','BCA'],'replicates':3,'cases':len(cells),'budget':200000,'M':3,'E':5,'claim_limit':'one three-rule positive schema; no deletion, updates, negation, or external state'},'cases':cells,'failed_cases':failed,'all_checks_pass':locked==post and not failed}
    with gzip.open(OUT,'wt',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps({'all_checks_pass':result['all_checks_pass'],'cases':len(cells),'failed_cases':failed,'source_stable':result['source_stable'],'capture':OUT.relative_to(ROOT).as_posix()}))
    return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
