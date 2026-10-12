#!/usr/bin/env python3
"""Repeated bounded-work scaling of global and Retina-scoped vision folds."""
from __future__ import annotations
import copy,hashlib,json,platform,sys,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
SEED_DOC=ROOT/'seeds/vision_settle.json';PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_GLOBAL_FOLD_SCALE_V1_1_AMENDMENT_20260925.md';OUT=ROOT/'evaluation/reports/substrate_vision_global_fold_scale_20260925.json';CAP=1024

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def root_source():return {'type':'Neighbours','node':{'type':'Var','name':'r'},'edge_type':'has_sunit','any_type':False}
def scoped_doc(doc):
 m=copy.deepcopy(doc);found=0
 def visit(x):
  nonlocal found
  if isinstance(x,dict):
   if x.get('type')=='NodesOfType' and x.get('node_type')=='SUnit':found+=1;return root_source()
   return {k:visit(v) for k,v in x.items()}
  if isinstance(x,list):return [visit(v) for v in x]
  return x
 for r in m.get('rules',[]):
  if r.get('name')=='st_settle':r['name']='st_settle_root_scoped_benchmark';r['where']=visit(r.get('where'));r['effects']=visit(r.get('effects'))
 if found!=2:raise RuntimeError(f'expected two SUnit folds, got {found}')
 return m

def arm(seed,n,scoped,doc):
 import substrate.boot_core as boot_core
 from substrate.seed_loader import manifest_for as original
 import scripts.settle_lib as settle_lib
 import scripts.rung8_lib as rung8_lib
 build_sheet=settle_lib.build_sheet
 retina_side=max(16,2*n+int(rung8_lib.RF))
 old_dims=(rung8_lib.H,rung8_lib.W,settle_lib.H,settle_lib.W,settle_lib.lattice_centres.__kwdefaults__['h'],settle_lib.lattice_centres.__kwdefaults__['w'])
 rung8_lib.H=rung8_lib.W=settle_lib.H=settle_lib.W=retina_side
 settle_lib.lattice_centres.__kwdefaults__['h']=settle_lib.lattice_centres.__kwdefaults__['w']=retina_side
 if scoped:
  d=scoped_doc(doc)
  def wrapped(sid):return d if sid=='vision_settle' else original(sid)
  boot_core.manifest_for=wrapped
 try:w,units,edges=build_sheet(seed=seed,n_side=n,channels='degenerate',connectivity=8,settle=1.0,bubble=0.0)
 finally:
  if scoped:boot_core.manifest_for=original
  rung8_lib.H,rung8_lib.W,settle_lib.H,settle_lib.W,settle_lib.lattice_centres.__kwdefaults__['h'],settle_lib.lattice_centres.__kwdefaults__['w']=old_dims
 inn=w.s._inner;root=w.retina
 owned=set(inn.neighbours(root,'has_sunit'))
 if set(units)!=owned:raise RuntimeError('Retina ownership mismatch')
 rules=inn.export_rules();target='st_settle_root_scoped_benchmark' if scoped else 'st_settle';keep={i for i,r in enumerate(rules) if r['name'] in (target,'st_commit')}
 if len(keep)!=2:raise RuntimeError(f'missing rules {target}: {keep}')
 for i in range(len(rules)):
  if i not in keep:inn.remove_rule(i)
 rng=np.random.Generator(np.random.PCG64(seed+9000));aff=rng.random(len(units),dtype=np.float64);step=float(inn.node(root)['attrs'].get('step',0.0))
 for u,a in zip(units,aff):inn.set_attr(u,'aff',float(a));inn.set_attr(u,'aff_step',step);inn.set_attr(u,'act',0.0);inn.set_attr(u,'act_next',-1.0)
 t=time.perf_counter();progress=int(inn.run_rules(CAP));elapsed=time.perf_counter()-t
 acts=np.asarray([float(inn.node(u)['attrs'].get('act',0.0)) for u in units]);pred=[]
 for u,a in zip(units,aff):
  ns=inn.neighbours(u,'sunit_neighbour');local=float(np.mean([float(inn.node(v)['attrs'].get('act',0.0)) for v in ns])) if ns else 0.0
  pred.append(max(float(a)+local-float(np.mean(acts)),0.0))
 return {'seed':seed,'n_side':n,'n_units':len(units),'n_edges':edges,'retina_side':retina_side,'graph_nodes':len(inn.nodes()),'variant':'scoped' if scoped else 'global','progress':progress,'budget':CAP,'budget_exit':progress>=CAP,'seconds':elapsed,'seconds_per_progress':elapsed/progress if progress else None,'max_equation_residual':float(np.max(np.abs(np.asarray(pred)-acts))),'activations':acts.tolist(),'activation_sha256':hashlib.sha256(acts.tobytes()).hexdigest()}

def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 from substrate.seed_loader import manifest_for
 from substrate_rs import _native
 doc=manifest_for('vision_settle');pairs=[]
 for ix,seed in enumerate((4101,7301,10703)):
  for n in (2,4,8,16):
   order=(False,True) if ix%2==0 else (True,False);aa=[]
   for sc in order:
    a=arm(seed,n,sc,doc);aa.append(a);print(f"DONE seed={seed} n={n} variant={a['variant']} progress={a['progress']} seconds={a['seconds']:.4f}",flush=True)
   pairs.append({'seed':seed,'n_side':n,'arms':aa})
 result={'run_id':'vision-global-fold-scale-20260925-v1','pairs':pairs,'checks':{'24_arms':len(pairs)*2==24,'paired_shapes':all(c['arms'][0]['n_units']==c['arms'][1]['n_units'] and c['arms'][0]['n_edges']==c['arms'][1]['n_edges'] for c in pairs),'paired_progress':all(c['arms'][0]['progress']==c['arms'][1]['progress'] for c in pairs),'paired_activation_exact':all(c['arms'][0]['activations']==c['arms'][1]['activations'] for c in pairs),'positive_progress_under_cap':all(0<a['progress']<=CAP for c in pairs for a in c['arms']),'finite_residuals':all(np.isfinite(a['max_equation_residual']) for c in pairs for a in c['arms'])},'provenance':{'python':sys.version,'platform':platform.platform(),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(PROTOCOL),'seed_sha256':sha(SEED_DOC),'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'source_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in ('rewrite.rs','substrate.rs','term.rs','py.rs')}}}
 result['pass']=all(result['checks'].values());OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':result['checks'],'pass':result['pass']},indent=2))
 if not result['pass']:raise SystemExit('vision fold scaling parity gate failed')
if __name__=='__main__':main()
