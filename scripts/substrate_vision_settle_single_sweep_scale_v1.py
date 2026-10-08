#!/usr/bin/env python3
"""Measure one batched vision_settle application over full sheet sizes."""
from __future__ import annotations
import copy,hashlib,json,os,platform,random,statistics,subprocess,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'runners/dsl/python'))
PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_PREREG_20260927.md'
AMENDMENT=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_SETTLE_SINGLE_SWEEP_SCALE_V1_1_AMENDMENT_20260927.md'
SEED_DOC=ROOT/'seeds/vision_settle.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_settle_single_sweep_scale_v1_lock_20260927.json'
OUT=ROOT/'evaluation/reports/substrate_vision_settle_single_sweep_scale_v1_20260927.json'
ANALYZER=ROOT/'scripts/analyze_substrate_vision_settle_single_sweep_scale_v1.py'
SIZES=(3,4,6,8,10);SEEDS=(11,29,47);TIMING_REPEATS=5
RUST=('py.rs','scale_audit.rs','rewrite.rs','substrate.rs','graph_rules.rs','term.rs')
WORKLOAD_SOURCES=('scripts/settle_lib.py','scripts/rung8_lib.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def source_closure():
 paths=set()
 for folder in (ROOT/'domains',ROOT/'substrate',ROOT/'runners/dsl/python'):
  paths.update(p for p in folder.rglob('*.py') if '__pycache__' not in p.parts)
 for folder in (ROOT/'seeds',): paths.update(folder.rglob('*.json'))
 return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
def lock_inputs():
 from substrate_rs import _native
 from domains.engine_provenance import engine_provenance
 return {'protocol_sha256':sha(PROTOCOL),'amendment_sha256':sha(AMENDMENT),'runner_sha256':sha(__file__),'analyzer_sha256':sha(ANALYZER),'source_closure_sha256':source_closure(),
  'workload_source_sha256':{x:sha(ROOT/x) for x in WORKLOAD_SOURCES},'engine_provenance':engine_provenance(),
  'seed_sha256':sha(SEED_DOC),'rust_sha256':{x:sha(ROOT/'runners/dsl/src'/x) for x in RUST},
  'native_extension_sha256':sha(Path(_native.__file__).resolve()),
  'native_build_manifest_sha256':sha(ROOT/'runners/dsl/python/substrate_rs/_native.build.json'),
  'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
def scoped_manifest(doc):
 found=0
 def visit(x):
  nonlocal found
  if isinstance(x,dict):
   if x.get('type')=='NodesOfType' and x.get('node_type')=='SUnit':
    found+=1;return {'type':'Neighbours','node':{'type':'Var','name':'r'},'edge_type':'has_sunit','any_type':False}
   return {k:visit(v) for k,v in x.items()}
  if isinstance(x,list):return [visit(v) for v in x]
  return x
 m=copy.deepcopy(doc)
 for rule in m.get('rules',[]):
  if rule.get('name')=='st_settle':
   rule['name']='st_settle_root_scoped_benchmark'
   rule['where']=visit(rule.get('where'));rule['effects']=visit(rule.get('effects'))
 if found!=2:raise RuntimeError(f'expected two global source occurrences, found {found}')
 return m
def one_case(n_side,seed,variant,doc):
 import substrate.boot_core as boot_core
 from substrate.seed_loader import manifest_for as original_manifest_for
 from scripts.settle_lib import build_sheet
 scoped=variant=='root_scoped'
 if scoped:
  clone=scoped_manifest(doc)
  def wrapped(seed_id):return clone if seed_id=='vision_settle' else original_manifest_for(seed_id)
  boot_core.manifest_for=wrapped
 try:w,units,_=build_sheet(seed=seed,n_side=n_side,channels='degenerate',connectivity=8,settle=1.0,bubble=0.0)
 finally:
  if scoped:boot_core.manifest_for=original_manifest_for
 inner=w.s._inner;root=w.retina
 roots=inner.nodes('Retina')
 if roots!=[root]:raise RuntimeError(f'expected one Retina root, got {roots}')
 members=set(inner.neighbours(root,'has_sunit'))
 if members!=set(units) or len(units)!=n_side*n_side:raise RuntimeError('sheet root membership or size mismatch')
 coords=[(float(inner.node(u)['attrs']['cy']),float(inner.node(u)['attrs']['cx'])) for u in units]
 rows=sorted({y for y,_ in coords});cols=sorted({x for _,x in coords})
 if len(rows)!=n_side or len(cols)!=n_side or coords!=[(y,x) for y in rows for x in cols]:raise RuntimeError('builder unit order is not the registered row-major lattice')
 names=('st_settle_root_scoped_benchmark' if scoped else 'st_settle','st_commit')
 rules=inner.export_rules();indices={r['name']:i for i,r in enumerate(rules) if r['name'] in names}
 if set(indices)!=set(names):raise RuntimeError(f'missing selected rules: {indices}')
 keep=set(indices.values())
 removed=sum(bool(inner.remove_rule(i)) for i in range(len(rules)) if i not in keep)
 rng=np.random.Generator(np.random.PCG64(seed+9000));N=len(units)
 aff=rng.random(N,dtype=np.float64);act=rng.random(N,dtype=np.float64)
 step=float(inner.node(root)['attrs'].get('step',0.0))
 for u,a,x in zip(units,aff,act):
  inner.set_attr(u,'aff',float(a));inner.set_attr(u,'aff_step',step);inner.set_attr(u,'act',float(x));inner.set_attr(u,'act_next',-1.0)
 idx=indices[names[0]]
 inner.scale_audit_reset();inner.scale_audit_per_rule_reset();inner.scale_audit_set_enabled(True);inner.scale_audit_set_per_rule_enabled(True)
 try:progress=bool(inner.apply_rule_batch(idx))
 finally:inner.scale_audit_set_per_rule_enabled(False);inner.scale_audit_set_enabled(False)
 audit={str(k):int(v) for k,v in inner.scale_audit_snapshot()}
 per_rule=[[int(i),str(m),int(v)] for i,m,v in inner.scale_audit_per_rule_snapshot()]
 per_clause=[[int(i),int(pos),int(v)] for i,pos,v in inner.scale_audit_match_clause_snapshot()]
 out=np.array([float(inner.node(u)['attrs'].get('act_next',0.0)) for u in units],dtype=np.float64)
 timing=[]
 for _ in range(TIMING_REPEATS):
  for u in units:inner.set_attr(u,'act_next',-1.0)
  t0=time.perf_counter_ns();inner.apply_rule_batch(idx);timing.append(time.perf_counter_ns()-t0)
 graph=inner.graph_to_dict();ids=[int(u.value if hasattr(u,'value') else u) for u in units]
 row_index={y:i for i,y in enumerate(rows)};frame_of={uid:row_index[coords[i][0]] for i,uid in enumerate(ids)}
 all_edges=[e for e in graph.get('edges',[])];cut=[];local_cut=0
 for e in all_edges:
  s=int(e['src']);t=int(e['tgt']);fs=frame_of.get(s);ft=frame_of.get(t)
  if fs!=ft and (fs is not None or ft is not None):
   cut.append(e)
   if e['type']=='sunit_neighbour' and fs is not None and ft is not None:local_cut+=1
 return {'n_side':n_side,'seed':seed,'variant':variant,'unit_count':N,'whole_graph_nodes':len(graph.get('nodes',[])),'whole_graph_edges':len(all_edges),
  'root_membership_count':len(members),'retained_rule_names':list(names),'removed_other_rules':removed,'rule_index':idx,'one_batch_application_progress':progress,
  'act_before':act.tolist(),'aff':aff.tolist(),'act_next':out.tolist(),'act_next_sha256':hashlib.sha256(out.tobytes()).hexdigest(),'audit_global':audit,'audit_per_rule':per_rule,'audit_per_clause':per_clause,
  'audit_disabled_apply_ns':timing,'audit_disabled_apply_ns_median':int(statistics.median(timing)),'row_frame_count':len(rows),'row_coordinates':rows,'units_per_row_frame':n_side,
  'runtime_typed_edge_cut_incidence_count':len(cut),'runtime_typed_edge_cut_edge_type_counts':dict(sorted(__import__('collections').Counter(e['type'] for e in cut).items())),
  'local_neighbor_cross_row_edge_count':local_cut,'global_fold_cross_row_dependency_incidence_count':N*(N-n_side),
  'global_fold_dependency_treewidth':N-1}
def worker(rep):
 started=lock_inputs();doc=json.loads(SEED_DOC.read_text());rows=[]
 for n in SIZES:
  for seed in SEEDS:
   pair=[one_case(n,seed,v,doc) for v in ('global','root_scoped')]
   rows.append({'n_side':n,'seed':seed,'arms':pair,'paired_act_next_equal':pair[0]['act_next']==pair[1]['act_next']})
 return {'replicate':rep,'pid':os.getpid(),'worker_started_inputs':started,'worker_finished_inputs':lock_inputs(),'cases':rows}
def main():
 if sys.argv[1:]==['--lock']:
  LOCK.parent.mkdir(parents=True,exist_ok=True);LOCK.write_text(json.dumps({'locked_inputs':lock_inputs()},indent=2,sort_keys=True)+'\n');print(LOCK);return
 if len(sys.argv)==3 and sys.argv[1]=='--worker':print(json.dumps(worker(int(sys.argv[2])),sort_keys=True));return
 locked=lock_inputs()
 if not LOCK.exists() or json.loads(LOCK.read_text())['locked_inputs']!=locked:raise SystemExit('missing or stale source lock')
 env=dict(os.environ);env.setdefault('OZMA_NO_LLM','1');env.setdefault('OZMA_SEED_PERSIST_DISABLED','1')
 jobs=[0,1,2];random.Random(20260927).shuffle(jobs);runs=[]
 for rep in jobs:
  p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',str(rep)],cwd=ROOT,env=env,text=True,capture_output=True,check=True);runs.append(json.loads(p.stdout))
 post=lock_inputs();checks={'three_distinct_fresh_pids':len({r['pid'] for r in runs})==3,
  'source_stable_all_workers_and_postrun':post==locked and all(r['worker_started_inputs']==locked==r['worker_finished_inputs'] for r in runs),
  'native_engine_matches_source':locked['engine_provenance'].get('source_match') in ('own','shared') and not locked['engine_provenance'].get('stale_rust'),
  'same_worker_case_matrix':all([(c['n_side'],c['seed']) for c in r['cases']]==[(n,s) for n in SIZES for s in SEEDS] for r in runs),
  'paired_one_sweep_outputs_equal':all(c['paired_act_next_equal'] for r in runs for c in r['cases']),
  'all_sheets_have_exact_root_membership':all(a['unit_count']==a['root_membership_count']==a['n_side']**2 for r in runs for c in r['cases'] for a in c['arms']),
  'only_expected_rules_retained':all(set(a['retained_rule_names'])==({'st_settle','st_commit'} if a['variant']=='global' else {'st_settle_root_scoped_benchmark','st_commit'}) for r in runs for c in r['cases'] for a in c['arms']),
  'all_batch_applications_progress':all(a['one_batch_application_progress'] for r in runs for c in r['cases'] for a in c['arms']),
  'candidate_counts_reproduce_across_workers':len({json.dumps([(c['n_side'],c['seed'],[(a['variant'],a['audit_global'],a['audit_per_rule']) for a in c['arms']]) for c in r['cases']],sort_keys=True) for r in runs})==1}
 payload={'schema_version':1,'run_id':'vision-settle-single-sweep-scale-v1-20260927','locked_inputs':locked,'post_run_inputs':post,'lock_sha256':sha(LOCK),
  'environment':{'python':sys.version,'platform':platform.platform()},'schedule':jobs,'checks':checks,'pass':all(checks.values()),'runs':runs,
  'claim_boundary':'Three source-locked fresh workers measure one batched st_settle application on full one-sheet graphs for five sizes and three seeds, paired with a root-scoped clone. This excludes graph build, commit, iterative settling, task quality, and learned frame discovery. Row frames are protocol-declared; global-factor cross-row dependencies are derived from the verified rule signature.'}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT),'checks':checks,'replicates':len(runs)},indent=2))
 if not payload['pass']:raise SystemExit('vision one-sweep scale gate failed')
if __name__=='__main__':main()
