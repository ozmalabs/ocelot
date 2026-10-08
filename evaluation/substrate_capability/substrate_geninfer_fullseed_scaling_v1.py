#!/usr/bin/env python3
"""Full-seed GenInfer scaling by relation count and data-derived matrix bound."""
from __future__ import annotations
import hashlib,json,os,platform,resource,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import build_is_stale,provenance_line
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from domains import reflective_faculty as rf
from substrate_rs import _native
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENINFER_FULLSEED_SCALING_V1_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_geninfer_fullseed_scaling_v1.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1_lock_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_fullseed_scaling_v1_20261003.json'
RELATION_COUNTS=(4,8,16,32,64)
BOUNDS=(3,4,5,6)
REPEATS=(1,2,3)
CONTROL_REPEATS=(1,2,3)
DIM_TYPES=['pred','coord:x','coord:y','value']
TRAIN_POINTS=[(0,0),(1,0),(0,1),(1,1)]
HELD_POINTS=[(0,0),(1,1),(2,1),(1,2)]

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def seed_closure():
 pending=[*__import__('substrate.boot_core',fromlist=['CORE_SEEDS']).CORE_SEEDS,'shape_decode_loop'];seen=set()
 while pending:
  name=str(pending.pop())
  if name in seen:continue
  seen.add(name);pending.extend(str(x) for x in manifest_for(name).get('depends_on',()))
 return sorted(f'seeds/{x}.json' for x in seen)
def source_paths():
 core=['domains/engine_provenance.py','domains/reflective_faculty.py','substrate/boot_core.py','substrate/seed_loader.py',
  'runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs','runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs',
  'runners/dsl/src/rewrite.rs','runners/dsl/src/py.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs',
  'runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
  'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json',
  str(RUNNER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT))]
 return sorted(set((*core,*seed_closure())))
def frozen():
 native=Path(_native.__file__).resolve()
 return {'source_sha256':{x:sha(ROOT/x) for x in source_paths()},'native_path':str(native),
  'native_sha256':sha(native),'engine':provenance_line()}
def matrix(bound):return [bound-1,1,1,1]
def cases():
 out=[]
 for n in RELATION_COUNTS:
  for b in BOUNDS:
   for rep in REPEATS:out.append({'id':f'positive_n{n}_b{b}_r{rep}','kind':'positive','n':n,'bound':b,'repeat':rep})
 for b in BOUNDS:
  for rep in CONTROL_REPEATS:
   out.append({'id':f'disabled_n8_b{b}_r{rep}','kind':'disabled','n':8,'bound':b,'repeat':rep})
   out.append({'id':f'predicate_corrupt_n8_b{b}_r{rep}','kind':'predicate_corrupt','n':8,'bound':b,'repeat':rep})
 return out
def rss_kib():return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
def rows(prefix,points,n):return [[f'{prefix}_{i}',*points[i%len(points)],'signal'] for i in range(n)]
def apply(m,rs):
 a,b,c,d=m
 return [[x[0],a*x[1]+b*x[2],c*x[1]+d*x[2],x[3]] for x in rs]
def generators(sub):
 out=[]
 for node in sub.nodes('DimensionGenerator'):
  a=sub.node(node)['attrs']
  if a.get('kind')=='linear':out.append({'id':str(node),'name':a.get('name'),'matrix':list(a.get('matrix') or [])})
 return out
def receipts(sub,obs):
 out=[]
 for node in sub.neighbours(obs,'has_transform'):
  a=sub.node(node)['attrs'];out.append({k:a.get(k) for k in ('source','generator','generators','base','dim','dims','k','ks','transforms') if k in a})
 return out
def observe(sub,agent,native,signature,key):
 obs=sub.add_node('Observation',{'signature':signature,'key':['fullseed_scaling',key],
  'status':'decoded','residual':signature,'decoded_epoch':sub.node(agent)['attrs'].get('codebook_epoch') or 0.0,'dim_types':DIM_TYPES})
 sub.add_edge(agent,'observed',obs)
 nodes0=len(list(sub.nodes()));edges0=sub.edge_count();rss0=rss_kib();cpu0=time.process_time_ns();t0=time.perf_counter_ns()
 work=int(native.run_rules());wall=time.perf_counter_ns()-t0;cpu=time.process_time_ns()-cpu0;rss1=rss_kib()
 return obs,{'status':sub.node(obs)['attrs'].get('status'),'covered_by':sub.node(obs)['attrs'].get('covered_by'),
  'residual':sub.node(obs)['attrs'].get('residual'),'transform_receipts':receipts(sub,obs),
  'closure_work':work,'closure_wall_ns':wall,'closure_cpu_ns':cpu,'hwm_before_kib':rss0,
  'hwm_after_kib':rss1,'hwm_delta_kib':max(0,rss1-rss0),'nodes_before':nodes0,
  'nodes_after':len(list(sub.nodes())),'edges_after':sub.edge_count()}
def run_case(case):
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 source0=frozen();sub,agent=boot_core();native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,agent)
 if case['kind']!='disabled':sub.set_attr(agent,'gen_infer_enabled',1.0)
 b=case['bound'];m=matrix(b);n=case['n'];initial=generators(sub)
 trbase=rows('tr',TRAIN_POINTS,n);trgoal=apply(m,trbase)
 if case['kind']=='predicate_corrupt':trgoal[-1][0]='noise_'+str(n)
 sub.add_node('ShapeSignature',{'name':'fullseed_train_'+case['id'],'signature':json.dumps(trbase),
  'kind':'faculty','faculty':'fullseed_scaling_train','dim_types':DIM_TYPES})
 axes0=len(list(sub.nodes('CapabilityAxis')));train_obs,train=observe(sub,agent,native,trgoal,case['id']+'_train')
 after_train=generators(sub);axes_train=len(list(sub.nodes('CapabilityAxis')))-axes0
 acquired=[g for g in after_train if g['matrix']==m]
 heldbase=rows('ho',HELD_POINTS,n);heldgoal=apply(m,heldbase)
 sub.add_node('ShapeSignature',{'name':'fullseed_held_'+case['id'],'signature':json.dumps(heldbase),
  'kind':'faculty','faculty':'fullseed_scaling_heldout','dim_types':DIM_TYPES})
 held_obs,held=observe(sub,agent,native,heldgoal,case['id']+'_held')
 held_exact=(heldgoal==apply(m,heldbase));held_names={x.get('generator') for x in held['transform_receipts']}
 corr=[row[:] for row in heldgoal];corr[min(1,n-1)][1]+=1
 corr_obs,corr_result=observe(sub,agent,native,corr,case['id']+'_corrupt_held')
 corrupt_exact=(corr==apply(m,heldbase))
 post=generators(sub);source1=frozen()
 return {'pid':os.getpid(),'case':case,'matrix':m,'expected_bound':b,'expected_candidate_checks_per_part':(2*b+1)**4-1,
  'initial_linear_generators':initial,'linear_generators_after_training':after_train,
  'linear_generators_after_all':post,'target_acquired_during_training':bool(acquired),
  'training_acquired_generator_names':[x['name'] for x in acquired],
  'heldout_generator_names':sorted(x for x in held_names if isinstance(x,str)),
  'same_training_generator_on_heldout':bool({x['name'] for x in acquired}&held_names),
  'train':train,'heldout':held,'corrupted_heldout':corr_result,
  'training_quanta_added':axes_train,'heldout_exact_match':held_exact,
  'corrupted_heldout_exact_match':corr==apply(m,heldbase),
  'training_oracle_exact_match':trgoal==apply(m,trbase),
  'source_stable':source0==source1,'source_before':source0,'source_after':source1}
def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite lock/capture')
  if build_is_stale(str(ROOT)):raise SystemExit('native engine stale')
  LOCK.write_text(json.dumps({'schema':'GenInferFullSeedScalingV1Lock','sources':frozen(),'cases':cases(),
   'relation_counts':RELATION_COUNTS,'bounds':BOUNDS,'matrix_rule':'[B-1,1,1,1]',
   'candidate_formula':'(2B+1)^4-1 per codebook part','train_points':TRAIN_POINTS,'heldout_points':HELD_POINTS,
   'repeat_count':3},indent=2,sort_keys=True)+'\n');print(LOCK.relative_to(ROOT));return 0
 if len(args)==2 and args[0]=='--worker':
  lock=json.loads(LOCK.read_text());case=next((x for x in lock['cases'] if x['id']==args[1]),None)
  if not case:raise SystemExit('unknown case')
  if frozen()!=lock['sources']:raise SystemExit('source drift')
  print(json.dumps(run_case(case),sort_keys=True));return 0
 if args!=['--run']:raise SystemExit('usage: --lock | --worker ID | --run')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source/native drift from lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 env['PYTHONPATH']=str(ROOT/'runners/dsl/python')+os.pathsep+str(ROOT)+os.pathsep+env.get('PYTHONPATH','')
 rows=[]
 for case in lock['cases']:
  proc=subprocess.run([sys.executable,str(RUNNER),'--worker',case['id']],cwd=ROOT,env=env,text=True,
   capture_output=True,check=True,timeout=300)
  rows.append(json.loads(proc.stdout))
 if frozen()!=lock['sources'] or not all(r['source_stable'] for r in rows):raise SystemExit('source drift during capture')
 payload={'schema':'GenInferFullSeedScalingV1Results','captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'host':platform.platform(),'lock_sha256':sha(LOCK),'source_manifest':frozen(),'cases':rows}
 OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'case_count':len(rows),'source_stable':True},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
