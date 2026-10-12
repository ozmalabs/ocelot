#!/usr/bin/env python3
"""Current-source, source-locked scale sweep for finite-key rule closure."""
from __future__ import annotations
import gzip, hashlib, json, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evaluation/reports/mint_termination_scale_v1_2_20261004.json.gz'
LOCK=ROOT/'evaluation/substrate_capability/mint_termination_scale_v1_2_lock_20261004.json'
ANALYZER=ROOT/'scripts/analyze_mint_termination_scale_v1_2.py'
PREREG=ROOT/'docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_CLOSURE_SCALE_V1_2_PREREG_20261004.md'
FRAGMENT=ROOT/'scripts/analyze_mint_termination_fragment.py'
RUST=('graph.rs','rewrite.rs','substrate.rs','py.rs','term.rs','jsonio.rs')
sys.path.insert(0,str(ROOT/'scripts')); sys.path.insert(0,str(ROOT/'runners/dsl/python'))
from analyze_mint_termination_fragment import analyze
from substrate_rs import _native

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lock_inputs():
    return {'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'protocol_sha256':sha(PREREG),'fragment_checker_sha256':sha(FRAGMENT),
      'rust_sources_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in RUST},
      'cargo_lock_sha256':sha(ROOT/'runners/dsl/Cargo.lock'),
      'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
      'native_extension_sha256':sha(Path(_native.__file__).resolve()),
      'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
TAG_VALUES=(None,True,1,'w3')
def specs(m):
    return [{'name':f'mint_tag_{i}','match':[['x','link','y']],
      'effects':[['add_node_if_absent',f'w{i}','Witness',{'tag':TAG_VALUES[i]}],['add_edge','y','link',f'w{i}',{}]]} for i in range(m)]
def initial_edges(n,topology):
    if topology=='cycle': return [(i,(i+1)%n) for i in range(n)]
    if topology=='dense_no_self': return [(i,j) for i in range(n) for j in range(n) if i!=j]
    raise ValueError(topology)
def native_case(n,m,topology,replicate):
    ins=initial_edges(n,topology); rule_specs=specs(m)
    input_edges=[[f'n{i}','link',f'n{j}',{}] for i,j in ins]
    classified=analyze(rule_specs,[f'n{i}' for i in range(n)],input_edges)
    t0=time.perf_counter_ns(); sub=_native.Substrate()
    node_ids=[sub.add_node('Seed',{'idx':i}) for i in range(n)]
    for i,j in ins: sub.add_edge_unchecked(node_ids[i],'link',node_ids[j])
    for rule in rule_specs: sub.add_rule(rule)
    report=sub.run_rules_report(200000,False); graph=sub.graph_to_dict(); elapsed=time.perf_counter_ns()-t0
    actual_nodes={(node['type'],json.dumps(node['attrs'],sort_keys=True)) for node in graph['nodes']}
    expected_nodes={('Seed',json.dumps({'idx':i},sort_keys=True)) for i in range(n)}
    runtime_tags=[]
    for value in TAG_VALUES[:m]:
        if not any(value==earlier for earlier in runtime_tags): runtime_tags.append(value)
    expected_nodes.update(('Witness',json.dumps({'tag':v},sort_keys=True)) for v in runtime_tags)
    actual_edges={(e['src'],e['type'],e['tgt'],json.dumps(e['attrs'],sort_keys=True)) for e in graph['edges']}
    edge_pairs=set(ins)
    for y in range(n+len(runtime_tags)):
        for w in range(n,n+len(runtime_tags)): edge_pairs.add((y,w))
    expected_edges={(i,'link',j,'{}') for i,j in edge_pairs}
    bound=classified.get('progress_steps_upper_bound')
    checks={'analyzer_accepts':classified['accepted'],'native_fixed_point':report['status']=='fixed_point',
      'exact_node_multiset':actual_nodes==expected_nodes,'exact_edge_set':actual_edges==expected_edges,
      'progress_within_bound':report['progress_steps']<=bound,'no_budget_overshoot':report['budget_overshoot']==0,
      'analyzer_count_is_conservative':classified['unique_mint_signatures']>=len(runtime_tags),
      'positive_measured_runtime':elapsed>0}
    return {'case_id':f'n{n}_m{m}_{topology}_r{replicate}','n_initial_nodes':n,'m_mint_signatures':m,'n_rules':m,
      'topology':topology,'replicate':replicate,'analyzer':classified,'native_report':report,
      'execution_wall_ns':elapsed,'actual_node_count':len(graph['nodes']),'actual_edge_count':len(graph['edges']),
      'actual_graph':graph,'authored_mint_signatures':m,'runtime_distinct_witnesses':len(runtime_tags),
      'expected_node_count':n+len(runtime_tags),'expected_edge_count':len(expected_edges),
      'checks':checks,'all_checks_pass':all(checks.values())}
def main():
    if sys.argv[1:]==['--lock']:
        if OUT.exists(): raise SystemExit('refusing to overwrite capture')
        LOCK.write_text(json.dumps({'schema':'MintTerminationScaleV1_2Lock','locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return 0
    if not LOCK.is_file() or json.loads(LOCK.read_text()).get('locked_inputs')!=lock_inputs(): raise SystemExit('missing or stale source lock')
    from domains.engine_provenance import build_is_stale
    stale=build_is_stale(str(ROOT))
    if stale: raise SystemExit(f'native build stale: {stale}')
    locked=lock_inputs();cases=[native_case(n,m,topo,r) for n in (4,16,64,128,256) for topo in ('cycle','dense_no_self') for m in (1,2,4) for r in (1,2,3)]
    post=lock_inputs();failed=[c['case_id'] for c in cases if not c['all_checks_pass']]
    result={'schema':'MintTerminationScaleV1_2','run_id':'mint-termination-scale-v1-2-20261004','locked_inputs':locked,'post_run_inputs':post,
      'source_stable':post==locked,'python':sys.version,'platform':platform.platform(),
      'design':{'initial_node_counts':[4,16,64,128,256],'mint_signature_counts':[1,2,4],'topologies':['cycle','dense_no_self'],'replicates_per_cell':3,'cases':len(cases),'budget':200000,
       'claim_limit':'current-source scale sweep of one fixed positive finite-key rule family; not a uniform wall-time theorem or natural-workload estimate'},
      'cases':cases,'failed_cases':failed,'all_checks_pass':not failed and post==locked}
    if OUT.exists(): raise SystemExit('refusing to overwrite capture')
    with gzip.open(OUT,'wt',encoding='utf-8') as f: json.dump(result,f,indent=2,sort_keys=True)
    print(json.dumps({'all_checks_pass':result['all_checks_pass'],'cases':len(cases),'failed_cases':failed,'output':str(OUT),'source_stable':result['source_stable']},indent=2))
    return 0 if result['all_checks_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
