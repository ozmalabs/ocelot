#!/usr/bin/env python3
"""Per-rule native work attribution for the global/scoped vision fold."""
from __future__ import annotations
import copy,hashlib,json,platform,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
OUT=ROOT/'evaluation/reports/substrate_vision_global_fold_attribution_20260925.json';PROTOCOL=ROOT/'docs/research/engine_substrate/SUBSTRATE_VISION_GLOBAL_FOLD_ATTRIBUTION_PREREG_20260925.md';SCALE_RAW=ROOT/'evaluation/reports/substrate_vision_global_fold_scale_20260925.json';SEED_DOC=ROOT/'seeds/vision_settle.json';CAP=1024

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def scoped_doc(doc):
 m=copy.deepcopy(doc);found=0
 def visit(x):
  nonlocal found
  if isinstance(x,dict):
   if x.get('type')=='NodesOfType' and x.get('node_type')=='SUnit':found+=1;return {'type':'Neighbours','node':{'type':'Var','name':'r'},'edge_type':'has_sunit','any_type':False}
   return {k:visit(v) for k,v in x.items()}
  if isinstance(x,list):return [visit(v) for v in x]
  return x
 for r in m.get('rules',[]):
  if r.get('name')=='st_settle':r['name']='st_settle_root_scoped_benchmark';r['where']=visit(r.get('where'));r['effects']=visit(r.get('effects'))
 if found!=2:raise RuntimeError(f'expected 2 SUnit folds, got {found}')
 return m

def arm(seed,n,scoped,doc):
 import substrate.boot_core as boot_core
 from substrate.seed_loader import manifest_for as original
 import scripts.settle_lib as sl, scripts.rung8_lib as r8
 side=max(16,2*n+int(r8.RF));dims=(r8.H,r8.W,sl.H,sl.W,sl.lattice_centres.__kwdefaults__['h'],sl.lattice_centres.__kwdefaults__['w'])
 r8.H=r8.W=sl.H=sl.W=side;sl.lattice_centres.__kwdefaults__['h']=sl.lattice_centres.__kwdefaults__['w']=side
 if scoped:
  d=scoped_doc(doc)
  def wrapped(sid):return d if sid=='vision_settle' else original(sid)
  boot_core.manifest_for=wrapped
 try:w,units,edges=sl.build_sheet(seed=seed,n_side=n,channels='degenerate',connectivity=8,settle=1.0,bubble=0.0)
 finally:
  if scoped:boot_core.manifest_for=original
  r8.H,r8.W,sl.H,sl.W,sl.lattice_centres.__kwdefaults__['h'],sl.lattice_centres.__kwdefaults__['w']=dims
 inn=w.s._inner;root=w.retina;rules=inn.export_rules();target='st_settle_root_scoped_benchmark' if scoped else 'st_settle';keep={i for i,r in enumerate(rules) if r['name'] in (target,'st_commit')}
 if len(keep)!=2:raise RuntimeError(f'missing selected rules: {keep}')
 for i in range(len(rules)):
  if i not in keep:inn.remove_rule(i)
 rng=np.random.Generator(np.random.PCG64(seed+9000));aff=rng.random(len(units),dtype=np.float64);step=float(inn.node(root)['attrs'].get('step',0.0))
 for u,a in zip(units,aff):inn.set_attr(u,'aff',float(a));inn.set_attr(u,'aff_step',step);inn.set_attr(u,'act',0.0);inn.set_attr(u,'act_next',-1.0)
 inn.scale_audit_set_enabled(False);inn.scale_audit_set_per_rule_enabled(False);inn.scale_audit_reset();inn.scale_audit_per_rule_reset();inn.scale_audit_set_enabled(True);inn.scale_audit_set_per_rule_enabled(True)
 progress=int(inn.run_rules(CAP));global_counts=dict(inn.scale_audit_snapshot());names={int(x[0]):str(x[1]) for x in inn.rule_access_sets()};per=[{'rule_index':int(i),'rule_name':names.get(int(i),f'rule_{i}'),'metric':str(m),'count':int(c)} for i,m,c in inn.scale_audit_per_rule_snapshot()]
 inn.scale_audit_set_per_rule_enabled(False);inn.scale_audit_set_enabled(False)
 acts=np.asarray([float(inn.node(u)['attrs'].get('act',0.0)) for u in units])
 selected=[x for x in per if x['rule_name']==target]
 return {'seed':seed,'n_side':n,'n_units':len(units),'n_edges':edges,'retina_side':side,'graph_nodes':len(inn.nodes()),'variant':'scoped' if scoped else 'global','rule_name':target,'progress':progress,'activations':acts.tolist(),'global_counters':global_counts,'per_rule_counters':per,'selected_rule_counters':selected}

def main():
 from domains.engine_provenance import engine_preamble,engine_provenance
 engine_preamble()
 from substrate.seed_loader import manifest_for
 from substrate_rs import _native
 base=json.loads(SCALE_RAW.read_text());doc=manifest_for('vision_settle');rows=[]
 for n in (2,4,8,16):
  for scoped in (False,True):
   a=arm(4101,n,scoped,doc);baseline=next(c for c in base['pairs'] if c['seed']==4101 and c['n_side']==n);b=next(x for x in baseline['arms'] if x['variant']==a['variant'])
   a['matches_uninstrumented']={'progress':a['progress']==b['progress'],'activations':a['activations']==b['activations']};rows.append(a);print(f"AUDITED n={n} variant={a['variant']} progress={a['progress']} matches={a['matches_uninstrumented']}",flush=True)
 result={'run_id':'vision-global-fold-attribution-20260925-v1','arms':rows,'checks':{'eight_arms':len(rows)==8,'matches_uninstrumented':all(a['matches_uninstrumented']['progress'] and a['matches_uninstrumented']['activations'] for a in rows)},'provenance':{'python':sys.version,'platform':platform.platform(),'runner_sha256':sha(Path(__file__)),'protocol_sha256':sha(PROTOCOL),'seed_sha256':sha(SEED_DOC),'scale_raw_sha256':sha(SCALE_RAW),'native_extension_path':str(Path(_native.__file__).resolve()),'native_extension_sha256':sha(Path(_native.__file__).resolve()),'engine_provenance':engine_provenance(),'source_sha256':{n:sha(ROOT/'runners/dsl/src'/n) for n in ('rewrite.rs','substrate.rs','term.rs','py.rs','scale_audit.rs')}}}
 result['pass']=all(result['checks'].values());OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':result['checks'],'pass':result['pass']},indent=2))
 if not result['pass']:raise SystemExit('attributed and uninstrumented run mismatch')
if __name__=='__main__':main()
