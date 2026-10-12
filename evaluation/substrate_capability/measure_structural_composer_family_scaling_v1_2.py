#!/usr/bin/env python3
"""Source-locked family/graph-size latency and resident-memory panel."""
from __future__ import annotations
import hashlib,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'runners/dsl/python'),str(ROOT),str(ROOT/'evaluation/substrate_capability')]
RUNNER=Path(__file__).resolve()
PREREG=ROOT/'docs/research/engine_substrate/STRUCTURAL_COMPOSER_FAMILY_SCALING_V1_2_PREREG_20261002.md'
LOCK=ROOT/'evaluation/substrate_capability/structural_composer_family_scaling_v1_2_lock_20261002.json'
OUT=ROOT/'evaluation/reports/structural_composer_family_scaling_v1_2_20261002.json'
BASE=ROOT/'evaluation/substrate_capability/thoughtexperiment_substrate_edge_identity_composer_v1_2.py'
FAMILIES=('recurrence','conversation','actor_recipient_edge','actor_recipient_identity')
NOISE=(0,1000,10000,100000);REPLICATES=3;WARMUPS=2;ORDER_SEED=61004

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def frozen():
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 return {'runner':sha(RUNNER),'preregistration':sha(PREREG),'base_harness':base.frozen(),
  'python':sys.version,'platform':platform.platform()}
def rss_bytes():
 try:
  pages=int(Path('/proc/self/statm').read_text().split()[1])
  return pages*os.sysconf('SC_PAGE_SIZE')
 except (OSError,ValueError,IndexError):return None
def prepare(family,tag,noise=0):
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 import domains.reflective_faculty as rf
 ctx=base.context(family,0,'composer_scale')
 sub=ctx['sub']
 for i in range(noise):sub.add_node('UnrelatedScaleNoise',{'ordinal':i})
 cue=base.CUES[family]
 key=f'{tag}_{family}'
 base.add_axis(sub,key,cue)
 return base,rf,ctx,key
def compose_once(family,tag,noise=0):
 base,rf,ctx,key=prepare(family,tag,noise)
 before=ctx['native'].export_rules()
 started=time.perf_counter_ns();result=rf.compose_general_structural_variant(ctx['sub'],[key],tag)
 elapsed=time.perf_counter_ns()-started
 return {'compose_ns':elapsed,'built':bool(result.get('built')),'operator':result.get('kind'),
  'target':result.get('removed_rule'),'site':result.get('site'),
  'primary_rules_unchanged':ctx['native'].export_rules()==before}
def worker(family,noise,rep):
 for i in range(WARMUPS):compose_once(family,f'warm{rep}_{i}')
 import thoughtexperiment_substrate_edge_identity_composer_v1_2 as base
 import domains.reflective_faculty as rf
 ctx=base.context(family,0,'composer_scale');sub=ctx['sub']
 rss_graph_before=rss_bytes()
 for i in range(noise):sub.add_node('UnrelatedScaleNoise',{'ordinal':i})
 rss_after_noise=rss_bytes()
 key=f'measured{rep}_{family}';base.add_axis(sub,key,base.CUES[family])
 rss_before=rss_bytes();before=ctx['native'].export_rules()
 started=time.perf_counter_ns();result=rf.compose_general_structural_variant(ctx['sub'],[key],f'measured{rep}')
 compose_ns=time.perf_counter_ns()-started;rss_after=rss_bytes()
 return {'family':family,'unrelated_nodes':noise,'replicate':rep,'compose_ns':compose_ns,
  'rss_before_noise_bytes':rss_graph_before,'rss_after_noise_bytes':rss_after_noise,
  'rss_before_compose_bytes':rss_before,'rss_after_compose_bytes':rss_after,
  'rss_noise_delta_bytes':(rss_after_noise-rss_graph_before) if rss_after_noise is not None and rss_graph_before is not None else None,
  'rss_compose_delta_bytes':(rss_after-rss_before) if rss_before is not None and rss_after is not None else None,
  'built':bool(result.get('built')),'operator':result.get('kind'),'site':result.get('site'),
  'target':result.get('removed_rule'),'primary_rules_unchanged':ctx['native'].export_rules()==before}
def main():
 args=sys.argv[1:]
 if args[:1]==['--worker']:
  print(json.dumps(worker(args[1],int(args[2]),int(args[3])),sort_keys=True,separators=(',',':')));return 0
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite existing capture')
  cells=[(f,n,r) for f in FAMILIES for n in NOISE for r in range(REPLICATES)]
  random.Random(ORDER_SEED).shuffle(cells)
  LOCK.write_text(json.dumps({'schema':'StructuralComposerFamilyScalingV1_2Lock','sources':frozen(),
   'families':FAMILIES,'unrelated_node_counts':NOISE,'replicates':REPLICATES,'warmups_per_trial':WARMUPS,
   'order_seed':ORDER_SEED,'capture_order':[list(x) for x in cells],
   'expected':{'recurrence':['mrl_offer_due_once','add_edge_identity_guard','out candidate has_mint_offer any endpoint'],
   'conversation':['reply_to_adjacency_pair','add_edge_identity_guard','in m responds_to any endpoint'],
   'actor_recipient_edge':['mint_actor_goal_recipient','add_edge_identity_guard','out agent has_actor_goal any endpoint'],
   'actor_recipient_identity':['mint_actor_goal_recipient','add_edge_identity_guard','out agent has_actor_goal attributes actor+verb']},
   'memory_metric':'Linux current RSS from /proc/self/statm before/after the measured composition; each trial has its own process'},
   indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock, --run, or --worker FAMILY N REP')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source drift from lock')
 env={**os.environ,'PYTHONPATH':f'{ROOT}/runners/dsl/python:{ROOT}:{ROOT}/evaluation/substrate_capability'}
 records=[]
 for family,n,rep in lock['capture_order']:
  p=subprocess.run([sys.executable,str(RUNNER),'--worker',family,str(n),str(rep)],cwd=ROOT,env=env,
   capture_output=True,text=True,timeout=180)
  if p.returncode:raise RuntimeError(f'worker {family}/{n}/{rep}: {p.stderr[-2000:]}')
  records.append(json.loads(p.stdout.strip().splitlines()[-1]))
 if frozen()!=lock['sources']:raise SystemExit('source drift during capture')
 OUT.write_text(json.dumps({'schema':'StructuralComposerFamilyScalingV1_2Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'sources':frozen(),'trials':records},indent=2,sort_keys=True)+'\n')
 print(OUT.relative_to(ROOT));return 0
if __name__=='__main__':raise SystemExit(main())
