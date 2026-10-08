#!/usr/bin/env python3
"""Measure full-seed GenInfer learning and transfer on a held-out relation task."""
from __future__ import annotations
import hashlib,json,platform,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'runners/dsl/python')]
from domains.engine_provenance import build_is_stale,engine_preamble,provenance_line
engine_preamble()
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from domains import reflective_faculty as rf
from substrate_rs import _native
RUNNER=Path(__file__).resolve()
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_GENINFER_RELATION_TRANSFER_V2_PREREG_20261003.md'
ANALYZER=ROOT/'evaluation/substrate_capability/analyze_substrate_geninfer_relation_transfer_v2.py'
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_relation_transfer_v2_lock_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_relation_transfer_v2_20261003.json'
MATRICES={'det3_positive':[2,1,1,2],'det3_negative_entry':[2,-1,1,1],'asymmetric_shear':[1,1,1,2]}
TRAIN_POINTS=[(0,0),(1,0),(0,1),(1,1)]
HELD_POINTS=[(0,0),(1,1),(2,1),(1,2)]
DIM_TYPES=['pred','coord:x','coord:y','value']

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def seed_closure():
 pending=[*__import__('substrate.boot_core',fromlist=['CORE_SEEDS']).CORE_SEEDS,'shape_decode_loop']
 seen=set()
 while pending:
  name=str(pending.pop())
  if name in seen:continue
  seen.add(name)
  pending.extend(str(dep) for dep in manifest_for(name).get('depends_on',()))
 return sorted(f'seeds/{name}.json' for name in seen)
def source_paths():
 core=['domains/engine_provenance.py','domains/reflective_faculty.py','substrate/boot_core.py',
  'substrate/seed_loader.py','runners/dsl/src/shape_decode.rs','runners/dsl/src/term.rs',
  'runners/dsl/src/graph.rs','runners/dsl/src/substrate.rs','runners/dsl/src/rewrite.rs',
  'runners/dsl/src/py.rs','runners/dsl/src/persist.rs','runners/dsl/src/grammar.rs',
  'runners/dsl/src/sym.rs','runners/dsl/src/lib.rs','runners/dsl/Cargo.toml','runners/dsl/Cargo.lock',
  'runners/dsl/python/substrate_rs/__init__.py','runners/dsl/python/substrate_rs/_native.build.json',
  str(RUNNER.relative_to(ROOT)),str(PROTOCOL.relative_to(ROOT)),str(ANALYZER.relative_to(ROOT))]
 return sorted(set((*core,*seed_closure())))
def frozen():
 native=Path(_native.__file__).resolve()
 return {'source_sha256':{p:sha(ROOT/p) for p in source_paths()},
  'native_path':str(native),'native_sha256':sha(native),'engine':provenance_line()}

def cases():
 out=[]
 for name,matrix in MATRICES.items():
  for enabled in (True,False):
   for rep in range(1,4):out.append({'id':f'{name}_{"enabled" if enabled else "disabled"}_r{rep}',
    'family':name,'matrix':matrix,'enabled':enabled,'holdout_corrupted':False,'identity_control':False,'repeat':rep})
 for rep in range(1,4):out.append({'id':f'identity_enabled_r{rep}','family':'identity','matrix':[1,0,0,1],
  'enabled':True,'holdout_corrupted':False,'identity_control':True,'repeat':rep})
 for name,matrix in MATRICES.items():
  for rep in range(1,4):out.append({'id':f'{name}_corrupt_holdout_r{rep}','family':name,'matrix':matrix,
   'enabled':True,'holdout_corrupted':True,'identity_control':False,'repeat':rep})
 return out

def transform(matrix,rows):
 a,b,c,d=matrix
 return [[row[0],a*row[1]+b*row[2],c*row[1]+d*row[2],row[3]] for row in rows]
def base_rows(prefix,points):
 return [[f'{prefix}_{i}',x,y,'signal'] for i,(x,y) in enumerate(points)]
def linear_generators(sub):
 result=[]
 for node in sub.nodes('DimensionGenerator'):
  attrs=sub.node(node)['attrs']
  if attrs.get('kind')=='linear':result.append({'id':str(node),'name':attrs.get('name'),
   'matrix':list(attrs.get('matrix') or []),'coord_dims':list(attrs.get('coord_dims') or [])})
 return result
def transform_receipts(sub,obs):
 out=[]
 for node in sub.neighbours(obs,'has_transform'):
  attrs=sub.node(node)['attrs']
  out.append({key:attrs.get(key) for key in ('source','generator','generators','base','dim','dims','k','ks','transforms') if key in attrs})
 return out
def observe(sub,agent,native,signature,key):
 epoch=sub.node(agent)['attrs'].get('codebook_epoch') or 0.0
 obs=sub.add_node('Observation',{'signature':signature,'key':['relation_transfer',key],
  'status':'decoded','residual':signature,'decoded_epoch':epoch,'dim_types':DIM_TYPES})
 sub.add_edge(agent,'observed',obs)
 started=time.perf_counter_ns();work=int(native.run_rules());elapsed=time.perf_counter_ns()-started
 attrs=sub.node(obs)['attrs']
 return obs,{'status':attrs.get('status'),'covered_by':attrs.get('covered_by'),
  'residual':attrs.get('residual'),'decoded_epoch':attrs.get('decoded_epoch'),
  'transform_receipts':transform_receipts(sub,obs),'closure_work':work,'closure_ns':elapsed,
  'capability_axis_count':len(list(sub.nodes('CapabilityAxis'))),'linear_generators':linear_generators(sub)}

def run_case(case):
 if build_is_stale(str(ROOT)):raise RuntimeError('native engine stale')
 before=frozen();sub,agent=boot_core();native=rf._native_eval2(sub);rf._ensure_shape_decode_loop(sub,native,agent)
 if case['enabled']:sub.set_attr(agent,'gen_infer_enabled',1.0)
 initial_gens=linear_generators(sub)
 axes_before_train=len(list(sub.nodes('CapabilityAxis')))
 train_base=base_rows('train',TRAIN_POINTS);train_goal=transform(case['matrix'],train_base)
 sub.add_node('ShapeSignature',{'name':'relation_train_'+case['id'],'signature':json.dumps(train_base),
  'kind':'faculty','faculty':'relation_transfer','dim_types':DIM_TYPES})
 training_nodes_before=len(list(sub.nodes()));training_edges_before=sub.edge_count()
 t0=time.perf_counter_ns();train_obs,train=observe(sub,agent,native,train_goal,case['id']+'_train')
 train_wall_ns=time.perf_counter_ns()-t0;after_train=linear_generators(sub)
 train_quanta=len(list(sub.nodes('CapabilityAxis')))-axes_before_train
 axes_before_heldout=len(list(sub.nodes('CapabilityAxis')))
 held_base=base_rows('held',HELD_POINTS);held_goal=transform(case['matrix'],held_base)
 if case['holdout_corrupted']:
  # One post-training label violates the learned map. The learner never sees this before acquisition.
  held_goal[1][1]+=1
 sub.add_node('ShapeSignature',{'name':'relation_held_'+case['id'],'signature':json.dumps(held_base),
  'kind':'faculty','faculty':'relation_transfer_heldout','dim_types':DIM_TYPES})
 heldout_nodes_before=len(list(sub.nodes()));heldout_edges_before=sub.edge_count()
 t1=time.perf_counter_ns();held_obs,held=observe(sub,agent,native,held_goal,case['id']+'_heldout')
 held_wall_ns=time.perf_counter_ns()-t1;after_held=linear_generators(sub)
 heldout_quanta=len(list(sub.nodes('CapabilityAxis')))-axes_before_heldout
 acquired=[g for g in after_train if g['matrix']==case['matrix']]
 acquired_names={g['name'] for g in acquired}
 used_names={name for receipt in held['transform_receipts']
             for name in ([receipt.get('generator')] if isinstance(receipt.get('generator'),str) else [])}
 exact_expected=transform(case['matrix'],held_base)
 exact_rows=[a==b for a,b in zip(exact_expected,held_goal)]
 result={'case':case,'source_before':before,'source_after':frozen(),
  'stages':{'training':train,'heldout':held},'initial_linear_generators':initial_gens,
  'linear_generators_after_training':after_train,'linear_generators_after_heldout':after_held,
  'target_matrix_acquired_during_training':bool(acquired),
  'training_acquired_generator_names':sorted(str(x) for x in acquired_names),
  'heldout_transform_generator_names':sorted(str(x) for x in used_names),
  'same_training_generator_used_heldout':bool(acquired_names & used_names),
  'heldout_base':held_base,'heldout_observed_target':held_goal,
  'heldout_target_from_preregistered_matrix':exact_expected,
  'heldout_exact_rows':exact_rows,'heldout_exact_match':all(exact_rows),
  'heldout_inserted_after_training':heldout_nodes_before>training_nodes_before
    and heldout_edges_before>=training_edges_before,
  'training_quanta_added':train_quanta,'heldout_quanta_added':heldout_quanta,
  'training_wall_ns':train_wall_ns,'heldout_wall_ns':held_wall_ns,
  'source_stable':before==frozen()}
 return result

def main():
 args=sys.argv[1:]
 if args==['--lock']:
  if LOCK.exists() or OUT.exists():raise SystemExit('refusing to overwrite source lock/capture')
  stale=build_is_stale(str(ROOT))
  if stale:raise SystemExit('stale native engine: '+'; '.join(stale))
  LOCK.write_text(json.dumps({'schema':'GenInferRelationTransferV2Lock','sources':frozen(),
   'cases':cases(),'matrices':MATRICES,'train_points':TRAIN_POINTS,'heldout_points':HELD_POINTS,
   'dim_types':DIM_TYPES,'expected_transfer':'training-acquired exact matrix on disjoint held-out signature'},
   indent=2,sort_keys=True)+'\n')
  print(LOCK.relative_to(ROOT));return 0
 if args!=['--run']:raise SystemExit('usage: --lock or --run')
 lock=json.loads(LOCK.read_text())
 if frozen()!=lock['sources']:raise SystemExit('source/native drift from lock')
 rows=[]
 for case in lock['cases']:
  row=run_case(case);rows.append(row)
 if frozen()!=lock['sources']:raise SystemExit('source/native drift during evaluation')
 OUT.write_text(json.dumps({'schema':'GenInferRelationTransferV2Results','lock_sha256':sha(LOCK),
  'captured_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'host':platform.platform(),
  'source_manifest':frozen(),'cases':rows},indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'case_count':len(rows),
  'source_stable':all(row['source_stable'] for row in rows)},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
