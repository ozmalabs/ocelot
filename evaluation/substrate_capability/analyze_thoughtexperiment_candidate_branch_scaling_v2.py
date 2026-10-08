#!/usr/bin/env python3
"""Independent source-lock, semantic-parity, isolation, and factorial analysis."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2.py';ANALYZER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_CANDIDATE_BRANCH_SCALING_V2_PREREG_20261005.md';FIXTURE=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2_fixture_20261005.json';SEED=ROOT/'seeds/self_change_reasoning.json';LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2_lock_20261005.json';CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_candidate_branch_scaling_v2_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_candidate_branch_scaling_v2_analysis_20261005.json';SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json');PHASES=('fork','rule_install','task_frame','separator_edges','closure','targeted_read')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=(RUNNER,ANALYZER,PROTOCOL,FIXTURE,SEED,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve();return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def main():
 lock=json.loads(LOCK.read_text());capture=json.loads(CAPTURE.read_text());errors=[]
 if frozen()!=lock['sources']:errors.append('source hashes differ from lock')
 if capture.get('lock_sha256')!=sha(LOCK):errors.append('capture lock hash mismatch')
 workers=capture.get('workers',[]);expected=len(lock['cells'])*lock['workers_per_cell']
 if len(workers)!=expected:errors.append(f'worker count {len(workers)} != {expected}')
 result={}
 for cell in lock['cells']:
  key='|'.join(str(cell[k]) for k in ('topology','background_nodes','task_aperture_nodes','separator_edges'))
  rows=[w for w in workers if all(w.get(k)==cell[k] for k in cell)]
  if len(rows)!=lock['workers_per_cell']:errors.append(f'{key}: worker count mismatch')
  vals={arm:{phase:[] for phase in PHASES} for arm in ('noop','candidate')};setup=[];nodes=[];edges=[];rss=[]
  for w in rows:
   if w.get('sources_before')!=lock['sources'] or w.get('sources_after')!=lock['sources']:errors.append(f'{key}: source mismatch')
   if w.get('primary_graph_before')!=w.get('primary_graph_after'):errors.append(f'{key}: primary graph changed')
   if w.get('primary_rule_before')!=w.get('primary_rule_after'):errors.append(f'{key}: primary rule/revision changed')
   if w.get('nodes')!=w.get('nodes_after') or w.get('edges')!=w.get('edges_after'):errors.append(f'{key}: primary graph counts changed')
   setup.append(w.get('graph_setup_ns',0));nodes.append(w.get('nodes',0));edges.append(w.get('edges',0));rss.extend([w.get('rss_before_kib'),w.get('rss_after_kib')])
   reps=w.get('measurements',[])
   if len(reps)!=lock['replications_per_arm']:errors.append(f'{key}: repetitions mismatch')
   for rep in reps:
    for arm,expected_out in (('noop',True),('candidate',False)):
     branch=rep.get(arm,{})
     if branch.get('output') is not expected_out:errors.append(f'{key}: {arm} output mismatch')
     timing=branch.get('times_ns',{})
     if set(timing)!=set(PHASES) or any(not isinstance(timing.get(p),int) or timing[p]<0 for p in PHASES):errors.append(f'{key}: {arm} phase timing invalid')
     for phase in PHASES:vals[arm][phase].append(timing[phase])
   audit=w.get('audit_probe',{})
   if audit.get('output') is not True:errors.append(f'{key}: audit probe output mismatch')
   if audit.get('boundary_neighbor_count')!=cell['separator_edges']:errors.append(f'{key}: actual boundary degree mismatch')
   exists_units=audit.get('audit_global',{}).get('term_unit:Exists')
   exists_calls=audit.get('audit_global',{}).get('term_eval:Exists',0)
   if exists_calls<1 or exists_units!=cell['separator_edges']*exists_calls:errors.append(f"{key}: Exists work {exists_units} does not equal boundary degree {cell['separator_edges']} × evaluations {exists_calls}")
   if audit.get('audit_metrics',{}).get('Exists')!=exists_calls or audit.get('audit_metrics',{}).get('term_units')!=exists_units:errors.append(f'{key}: per-rule Exists audit does not reconcile with process totals')
  result[key]={'workers':len(rows),'branches':sum(len(w.get('measurements',[]))*2 for w in rows),'nodes_median':statistics.median(nodes) if nodes else None,'edges_median':statistics.median(edges) if edges else None,'graph_setup_median_ns':statistics.median(setup) if setup else None,'rss_snapshots_kib':{'median':statistics.median(x for x in rss if x is not None) if any(x is not None for x in rss) else None},'phase_medians_ns':{arm:{p:statistics.median(v) if v else None for p,v in phases.items()} for arm,phases in vals.items()}}
 output={'schema':'ThoughtexperimentCandidateBranchScalingV2Analysis','passed':not errors,'errors':errors,'cell_count':len(result),'episode_count':sum(x['branches'] for x in result.values()),'cells':result,'interpretation':'Factorial fixed-task rehearsal over one authored rule family; exact parity and locality evidence is limited to registered topologies, apertures, and separator widths.'}
 OUT.write_text(json.dumps(output,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':output['passed'],'errors':errors,'cell_count':len(result),'episode_count':output['episode_count']},sort_keys=True));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
