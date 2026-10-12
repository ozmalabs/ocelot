#!/usr/bin/env python3
"""Source-locked crossed scaling of full edge identity composition."""
import copy, hashlib, json, os, platform, random, statistics, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/EDGE_IDENTITY_FULL_COMPOSE_CROSSED_SCALING_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_edge_identity_full_compose_crossed_scaling_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/edge_identity_full_compose_crossed_scaling_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/edge_identity_full_compose_crossed_scaling_v1_20261003.json'
FIELDS=(2,4,8,16,32); NOISE=(0,1000,10000); WARMUPS=1; TRIALS=3; SEED=61003; CAP=600

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rss_bytes():
    try: return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
    except Exception: return None
def frozen():
    import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
    from substrate_rs import _native
    from domains.engine_provenance import rust_source_fingerprint
    paths=[PREREG,RUNNER,ANALYZER,ROOT/'domains/edit_ops.py',ROOT/'domains/reflective_faculty.py',
      ROOT/'domains/seed_registry.py',ROOT/'evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1_2.py',
      ROOT/'seeds/actor_goals.json',ROOT/'runners/dsl/Cargo.toml',ROOT/'runners/dsl/Cargo.lock']
    out={str(p.relative_to(ROOT)):sha(p) for p in paths}
    out['loaded_native_binary']=sha(Path(_native.__file__).resolve())
    out['base_composer']=base.frozen();out['semantic_engine']=rust_source_fingerprint(str(ROOT))
    out['python']=sys.version;out['platform']=platform.platform()
    return out
def trial(fields,noise,rep):
    import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
    import domains.reflective_faculty as rf
    import domains.edit_ops as eo
    ctx=base.actor_context(fault=True);sub,native,target=ctx['sub'],ctx['native'],ctx['target']
    rule=copy.deepcopy(ctx['rule'])
    effect=next(e for e in rule['effects'] if isinstance(e,list) and e[0]=='add_node' and e[1]=='goal')
    attrs=effect[3]
    for i in range(fields-2): attrs[f'identity_aux_{i:02d}']=copy.deepcopy(attrs['actor'])
    source_rows=native.export_rules();before=next(r for r in source_rows if r.get('name')==target and r.get('active',True))
    ix=next(i for i,r in enumerate(source_rows) if r.get('name')==target and r.get('active',True))
    if not native.remove_rule(ix): raise RuntimeError('could not install synthetic field rule')
    native.add_rule(rule)
    active_before=native.export_rules()
    ax_before=sorted(sub.nodes('EditSite'))
    t0=time.perf_counter_ns()
    for i in range(noise): sub.add_node('UnrelatedCrossScaleNoise',{'ordinal':i})
    setup_ns=time.perf_counter_ns()-t0
    candidate_sites=eo.find_edge_identity_sites(rule)
    if len(candidate_sites)>CAP: raise RuntimeError(f'candidate cap exceeded: {len(candidate_sites)} > {CAP}')
    base.add_axis(sub,f'cross_{fields}_{noise}_{rep}',['actor','verb','pair','identity'])
    rss_before=rss_bytes();t0=time.perf_counter_ns()
    result=rf.compose_general_structural_variant(sub,[f'cross_{fields}_{noise}_{rep}'],f'cross{fields}_{noise}_{rep}')
    compose_ns=time.perf_counter_ns()-t0;rss_after=rss_bytes()
    edit_nodes=[]
    for nid in sub.nodes('EditSite'):
        a=sub.node(nid)['attrs']
        if a.get('target_rule')==target and a.get('operator')=='add_edge_identity_guard': edit_nodes.append(a)
    selected={'out':next((a for a in edit_nodes if a.get('identity_keys')==['actor','verb'] and a.get('scope')=='node_attrs'),None)}
    exact=bool(result.get('built') and result.get('kind')=='add_edge_identity_guard' and
      result.get('site')=='out agent has_actor_goal attributes actor+verb' and selected['out'] is not None)
    return {'fields':fields,'unrelated_nodes':noise,'replicate':rep,'graph_setup_ns':setup_ns,
      'compose_ns':compose_ns,'rss_before_bytes':rss_before,'rss_after_bytes':rss_after,
      'enumerated_sites':len(candidate_sites),'materialized_target_sites':len(edit_nodes),
      'expected_attribute_sites':fields+(fields*(fields-1))//2+(1 if fields>2 else 0),
      'built':bool(result.get('built')),'operator':result.get('kind'),'site':result.get('site'),
      'selected_actor_verb':exact,'primary_rule_store_unchanged':native.export_rules()==active_before,
      'preexisting_edit_sites':len(ax_before)}
def main():
    from domains.engine_provenance import build_is_stale
    if build_is_stale(str(ROOT)): raise SystemExit('native engine is stale')
    args=sys.argv[1:]
    if args==['--lock']:
        if LOCK.exists() or OUT.exists(): raise SystemExit('refusing to overwrite existing artifacts')
        cells=[(f,n) for f in FIELDS for n in NOISE];random.Random(SEED).shuffle(cells)
        LOCK.write_text(json.dumps({'schema':'EdgeIdentityFullComposeCrossedScalingV1Lock','sources':frozen(),
          'fields':FIELDS,'unrelated_nodes':NOISE,'cells':cells,'warmups_per_cell':WARMUPS,
          'trials_per_cell':TRIALS,'seed':SEED,'candidate_cap':CAP,
          'expected_operator':'add_edge_identity_guard','expected_site':'out agent has_actor_goal attributes actor+verb'},indent=2,sort_keys=True)+'\n')
        print(LOCK.relative_to(ROOT));return 0
    if args!=['--run']: raise SystemExit('usage: --lock or --run')
    lock=json.loads(LOCK.read_text())
    if frozen()!=lock['sources']: raise SystemExit('source drift from lock')
    rows=[]
    for fields,noise in lock['cells']:
        for w in range(WARMUPS): trial(fields,noise,100+w)
        reps=[trial(fields,noise,i) for i in range(TRIALS)]
        rows.append({'fields':fields,'unrelated_nodes':noise,'trials':reps,
          'median_compose_ns':int(statistics.median(r['compose_ns'] for r in reps)),
          'median_graph_setup_ns':int(statistics.median(r['graph_setup_ns'] for r in reps))})
    if frozen()!=lock['sources']: raise SystemExit('source drift during capture')
    OUT.write_text(json.dumps({'schema':'EdgeIdentityFullComposeCrossedScalingV1Results',
      'lock_sha256':sha(LOCK),'sources':frozen(),'host':platform.platform(),'rows':rows},indent=2,sort_keys=True)+'\n')
    print(OUT.relative_to(ROOT));return 0
if __name__=='__main__': raise SystemExit(main())
