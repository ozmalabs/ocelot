#!/usr/bin/env python3
"""Independent source, parity, isolation, and phase-summary analysis."""
import hashlib,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];RUNNER=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1.py';ANALYZER=Path(__file__).resolve();PROTOCOL=ROOT/'docs/research/engine_substrate/THOUGHTEXPERIMENT_CANDIDATE_BRANCH_SCALING_V1_PREREG_20261005.md';FIXTURE=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1_fixture_20261005.json';SEED=ROOT/'seeds/self_change_reasoning.json';LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v1_lock_20261005.json';CAPTURE=ROOT/'evaluation/reports/thoughtexperiment_candidate_branch_scaling_v1_20261005.json';OUT=ROOT/'evaluation/reports/thoughtexperiment_candidate_branch_scaling_v1_analysis_20261005.json';SOURCES=('runners/dsl/Cargo.toml','runners/dsl/Cargo.lock','runners/dsl/src/graph.rs','runners/dsl/src/graph_rules.rs','runners/dsl/src/rewrite.rs','runners/dsl/src/substrate.rs','runners/dsl/src/py.rs','runners/dsl/python/substrate_rs/ext.py','runners/dsl/python/substrate_rs/_native.build.json');PHASES=('fork','rule_install','task_input','closure','targeted_read')
import sys
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frozen():
 from substrate_rs import _native
 paths=(RUNNER,ANALYZER,PROTOCOL,FIXTURE,SEED,*(ROOT/x for x in SOURCES));binary=Path(_native.__file__).resolve();return {'files':{str(p.relative_to(ROOT)):sha(p) for p in paths},'native_binary':{'path':str(binary),'sha256':sha(binary)}}
def main():
 lock=json.loads(LOCK.read_text());cap=json.loads(CAPTURE.read_text());fx=json.loads(FIXTURE.read_text());errors=[]
 if frozen()!=lock['sources']:errors.append('source lock mismatch')
 if cap.get('lock_sha256')!=sha(LOCK):errors.append('capture lock digest mismatch')
 workers=cap.get('workers',[]);expected=len(lock['sizes'])*lock['workers_per_size']
 if len(workers)!=expected:errors.append('worker count mismatch')
 summary={}
 for size in lock['sizes']:
  group=[w for w in workers if w.get('decoy_nodes')==size]
  if len(group)!=lock['workers_per_size']:errors.append(f'size {size} worker count mismatch')
  vals={phase:[] for phase in PHASES};cpu={phase:[] for phase in PHASES};noop=[];cand=[]
  for w in group:
   if w.get('sources_before')!=lock['sources'] or w.get('sources_after')!=lock['sources']:errors.append(f'size {size} worker source mismatch')
   if w.get('primary_digest_before')!=w.get('primary_digest_after'):errors.append(f'size {size} primary graph mutated')
   if w.get('primary_rule_before')!=w.get('primary_rule_after'):errors.append(f'size {size} primary rule/revision mutated')
   if w.get('nodes')!=w.get('nodes_after') or w.get('edges')!=w.get('edges_after'):errors.append(f'size {size} primary graph counts changed')
   reps=w.get('measurements',[])
   if len(reps)!=fx['replications_per_arm']:errors.append(f'size {size} repetition count mismatch')
   for rep in reps:
    a,b=rep.get('noop',{}),rep.get('candidate',{})
    if a.get('output')!=fx['case']['input']['expected_live']:errors.append(f'size {size} no-op output mismatch')
    if b.get('output')!=fx['case']['input']['expected_candidate']:errors.append(f'size {size} candidate output mismatch')
    for arm,row in [('noop',a),('candidate',b)]:
     t=row.get('times_ns',{})
     if set(t)!=set(PHASES):errors.append(f'size {size} {arm} timing fields mismatch')
     for p in PHASES:vals[p].append(t.get(p,0))
    noop.append(a['output']);cand.append(b['output'])
  summary[str(size)]={'workers':len(group),'branches':sum(len(w.get('measurements',[]))*2 for w in group),'nodes_median':statistics.median(w.get('nodes',0) for w in group) if group else None,'edges_median':statistics.median(w.get('edges',0) for w in group) if group else None,'graph_setup_median_ns':statistics.median(w.get('graph_setup_ns',0) for w in group) if group else None,'rss_snapshots_kib':{'before_median':statistics.median(w.get('rss_before_kib') or 0 for w in group) if group else None,'after_median':statistics.median(w.get('rss_after_kib') or 0 for w in group) if group else None},'phase_medians_ns':{p:statistics.median(v) if v else None for p,v in vals.items()},'noop_correct':len(noop)==len(group)*fx['replications_per_arm'] and all(noop),'candidate_correct':len(cand)==len(group)*fx['replications_per_arm'] and not any(cand)}
 result={'schema':'ThoughtexperimentCandidateBranchScalingV1Analysis','passed':not errors,'errors':errors,'summary':summary,'interpretation':'Fixed-aperture task branch scaling over one sparse decoy-path topology; timings are phase-local and do not establish asymptotic complexity or natural-task prevalence.'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,sort_keys=True));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
