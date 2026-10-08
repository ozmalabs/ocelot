#!/usr/bin/env python3
"""Paired current-source closure replay with native audit off/on."""
from __future__ import annotations
import gzip,hashlib,json,platform,subprocess,sys,time
from pathlib import Path
from domains.engine_provenance import engine_preamble,provenance_line
engine_preamble()
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/reports/mint_termination_native_counters_v1_2_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/mint_termination_native_counters_v1_2_lock_20261004.json'
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CLOSURE_NATIVE_COUNTERS_V1_1_PREREG_20261004.md'
RUNNER=Path(__file__).resolve();ANALYZER=ROOT/'scripts/analyze_mint_termination_native_counters_v1_2.py'
RUST=('py.rs','rewrite.rs','graph.rs','substrate.rs','scale_audit.rs','term.rs','jsonio.rs')
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
from analyze_mint_termination_fragment import analyze
from substrate_rs import _native
NATIVE=_native.Substrate

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():return {'runner_sha256':sha(RUNNER),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PREREG),'checker_sha256':sha(ROOT/'scripts/analyze_mint_termination_fragment.py'),'manifest_helper_sha256':sha(ROOT/'scripts/substrate_run_manifest.py'),'rust_sources_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in RUST},'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def rules():return {'A':{'name':'mint_A','match':[['x','link','y']],'effects':[['add_node_if_absent','a','Witness',{'tag':'A'}],['add_edge','x','made_a','a',{}]]},'B':{'name':'mint_B','match':[['x','link','y'],['y','rel','z']],'effects':[['add_node_if_absent','b','Witness',{'tag':'B'}],['add_edge','x','made_b','b',{}]]},'C':{'name':'join_AB','match':[['x','made_a','a'],['x','made_b','b']],'effects':[['add_node_if_absent','c','Witness',{'tag':'C'}],['add_edge','a','result','c',{}],['add_edge','b','result','c',{}]]}}
def input_edges(n,d):return [(et,i,(i+k)%n) for et in ('link','rel') for k in range(1,d+1) for i in range(n)]
def one_arm(n,d,order,rep,mode):
    NATIVE.scale_audit_set_enabled(False);NATIVE.scale_audit_set_per_rule_enabled(False);NATIVE.scale_audit_reset();NATIVE.scale_audit_per_rule_reset()
    t0=time.perf_counter_ns();sub=NATIVE();ids=[sub.add_node('Seed',{'idx':i}) for i in range(n)]
    edges0=input_edges(n,d)
    for et,s,t in edges0:sub.add_edge_unchecked(ids[s],et,ids[t])
    rb=rules()
    for key in order:sub.add_rule(rb[key])
    if mode=='on':NATIVE.scale_audit_set_per_rule_enabled(True);NATIVE.scale_audit_set_enabled(True)
    report=sub.run_rules_report(200000,False);graph=sub.graph_to_dict();elapsed=time.perf_counter_ns()-t0
    global_rows=[list(x) for x in NATIVE.scale_audit_snapshot()]
    rule_rows=[list(x) for x in NATIVE.scale_audit_per_rule_snapshot()]
    clause_rows=[list(x) for x in NATIVE.scale_audit_match_clause_snapshot()]
    NATIVE.scale_audit_set_enabled(False);NATIVE.scale_audit_set_per_rule_enabled(False)
    return {'mode':mode,'report':report,'graph':graph,'execution_wall_ns':elapsed,'scale_global':global_rows,'per_rule':rule_rows,'clauses':clause_rows}
def one_pair(n,d,order,rep):
    modes=('off','on') if rep%2==1 else ('on','off')
    arms=[one_arm(n,d,order,rep,m) for m in modes]
    ids=[f'n{i}' for i in range(n)];edges=[[f'n{s}',et,f'n{t}',{}] for et,s,t in input_edges(n,d)];specs=[rules()[k] for k in order]
    return {'pair_id':f'n{n}_d{d}_{order}_r{rep}','n':n,'degree':d,'order':order,'replicate':rep,'initial_node_ids':ids,'initial_edges':edges,'rule_specs':specs,'static_analysis':analyze(specs,ids,edges),'arms':arms}
def main():
    if sys.argv[1:]==['--lock']:
        if OUT.exists():raise SystemExit('refusing to overwrite capture')
        LOCK.write_text(json.dumps({'schema':'MintTerminationNativeCountersV1_2Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
    if not LOCK.exists() or json.loads(LOCK.read_text()).get('locked_inputs')!=lock_inputs():raise SystemExit('missing or stale source lock')
    from domains.engine_provenance import build_is_stale
    stale=build_is_stale(str(ROOT))
    if stale:raise SystemExit(f'native build stale: {stale}')
    locked=lock_inputs();pairs=[one_pair(n,d,o,r) for n in (32,64,128,256) for d in (1,2,4,8,16) for o in ('ABC','CBA','BCA') for r in (1,2,3)];post=lock_inputs()
    result={'schema':'MintTerminationNativeCountersV1_2','run_id':'mint-termination-native-counters-v1-20261004','locked_inputs':locked,'post_run_inputs':post,'source_stable':locked==post,'engine':provenance_line(),'python':sys.version,'platform':platform.platform(),'design':{'N':[32,64,128,256],'degrees':[1,2,4,8,16],'orders':['ABC','CBA','BCA'],'replicates':3,'pairs':len(pairs),'closures':2*len(pairs),'budget':200000,'claim_limit':'one regular circulant three-rule positive finite-key family'},'pairs':pairs,'all_checks_pass':locked==post}
    with gzip.open(OUT,'wt',encoding='utf-8') as f:json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps({'pairs':len(pairs),'closures':2*len(pairs),'source_stable':result['source_stable'],'capture':OUT.relative_to(ROOT).as_posix()}));return 0 if result['all_checks_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
