#!/usr/bin/env python3
"""Measure full prompted edge-identity composition under unrelated graph growth."""
import hashlib,json,platform,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
LOCK=ROOT/'evaluation/substrate_capability/full_structural_composer_graph_scaling_v1_lock_20261002.json'
OUT=ROOT/'evaluation/reports/full_structural_composer_graph_scaling_v1_20261002.json'
PREREG=ROOT/'docs/research/engine_substrate/FULL_STRUCTURAL_COMPOSER_GRAPH_SCALING_V1_PREREG_20261002.md'
NOISE=(0,1000,10000);TRIALS=5;WIDTH='actor+verb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 return {'runner':sha(RUNNER),'preregistration':sha(PREREG),'base_composer_harness':base.frozen(),
  'python':sys.version,'platform':platform.platform()}
def trial(noise,rep):
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 import domains.reflective_faculty as rf
 ctx=base.actor_context(fault=True);sub=ctx['sub']
 started=time.perf_counter_ns()
 for i in range(noise):sub.add_node('UnrelatedScaleNoise',{'ordinal':i})
 graph_setup_ns=time.perf_counter_ns()-started
 key=f'full_compose_scale_{noise}_{rep}'
 base.add_axis(sub,key,base.CUES['actor_recipient_identity'])
 before=ctx['native'].export_rules()
 t=time.perf_counter_ns();result=rf.compose_general_structural_variant(sub,[key],f'scale{noise}_{rep}')
 elapsed=time.perf_counter_ns()-t
 return {'compose_ns':elapsed,'graph_noise_setup_ns':graph_setup_ns,
  'built':bool(result.get('built')),'operator':result.get('kind'),'site':result.get('site'),
  'primary_rules_unchanged':ctx['native'].export_rules()==before}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite')
  LOCK.write_text(json.dumps({'schema':'FullStructuralComposerGraphScalingV1Lock','sources':frozen(),
   'unrelated_node_counts':NOISE,'trials':TRIALS,'target':'mint_actor_goal_recipient',
   'expected_operator':'add_edge_identity_guard','expected_site':'out agent has_actor_goal attributes actor+verb',
   'scope':'full prompted compose_general_structural_variant; graph setup timed separately'},indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 rows=[]
 for n in NOISE:
  reps=[trial(n,i) for i in range(TRIALS)]
  rows.append({'unrelated_nodes':n,'trials':reps,
   'median_compose_ns':int(statistics.median(x['compose_ns'] for x in reps)),
   'median_noise_setup_ns':int(statistics.median(x['graph_noise_setup_ns'] for x in reps))})
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'FullStructuralComposerGraphScalingV1Results',
  'lock_sha256':sha(LOCK),'sources':frozen(),'rows':rows},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
