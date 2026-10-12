#!/usr/bin/env python3
"""Independent scorer for the full-seed DimInfer codebook ablation."""
import hashlib,json,statistics
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_diminfer_nonlinear_geometry_distribution_v2_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/diminfer_nonlinear_geometry_distribution_v2_lock_20260926.json'
FAMILIES={'rotation90':['rotation90'],'reflection_r':['reflection_r'],'reflection_c':['reflection_c'],'scale2':['scale2'],'cycle4':['cycle4'],'rotation90_cycle4':['rotation90','cycle4'],'reflection_r_cycle4':['reflection_r','cycle4'],'rotation90_scale2':['rotation90','scale2']}
GEOMETRY_SEED=20260927
def make_geometries():
 import random
 rng=random.Random(GEOMETRY_SEED); chosen=set();out={}
 lattice=[(r,c) for r in range(4) for c in range(4)]
 while len(out)<24:
  pts=tuple(sorted(rng.sample(lattice,6)))
  if pts in chosen:continue
  if 0 not in {r for r,c in pts} or 3 not in {r for r,c in pts}:continue
  if len({r for r,c in pts})<3 or len({c for r,c in pts})<3:continue
  noncollinear=any((pts[j][0]-pts[i][0])*(pts[k][1]-pts[i][1])-(pts[j][1]-pts[i][1])*(pts[k][0]-pts[i][0])!=0 for i in range(6) for j in range(i+1,6) for k in range(j+1,6))
  if not noncollinear:continue
  chosen.add(pts);out[f'geom_{len(out):02d}']=list(pts)
 return out
GEOMETRIES=make_geometries()
REPS=(1,2,3)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def step(ps,n):
 if n=='rotation90':
  mr=min(r for r,c in ps);mc=min(c for r,c in ps);mx=max(r-mr for r,c in ps);return [(c-mc,mx-(r-mr)) for r,c in ps]
 if n=='reflection_r':
  mx=max(r for r,c in ps);return [(mx-r,c) for r,c in ps]
 if n=='reflection_c':
  mx=max(c for r,c in ps);return [(r,mx-c) for r,c in ps]
 if n=='scale2':
  mr=min(r for r,c in ps);mc=min(c for r,c in ps);return [(2*(r-mr),2*(c-mc)) for r,c in ps]
 if n=='cycle4':return [((r+1)%4,c) for r,c in ps]
 raise ValueError(n)
def apply(ps,seq):
 x=list(ps)
 for n in seq:x=step(x,n)
 return x
def route(arm):
 ts=arm.get('transforms') or []
 if not ts:return {'names':[],'ks':[],'source':None,'record_present':False,'residuals':[],'dims':[],'deltas':[],'has_residual':False}
 t=ts[0];names=t.get('generators') or ([t['generator']] if t.get('generator') else [])
 ks=t.get('ks') or ([t['k']] if t.get('k') is not None else [])
 residuals=t.get('transforms') or [];dims=t.get('dims') or [];deltas=t.get('deltas') or []
 return {'names':names,'ks':ks,'source':t.get('source'),'record_present':True,'residuals':residuals,'dims':dims,'deltas':deltas,'has_residual':bool(residuals or dims or deltas),'transform_record':t}
def main():
 raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());workers=raw['workers'];checks={
 'protocol_tag':raw.get('protocol')=='SUBSTRATE_DIMINFER_NONLINEAR_GEOMETRY_DISTRIBUTION_V2',
 'raw_lock_equal':raw.get('locked_inputs')==lock.get('locked_inputs'),
 'reproduced_geometry_design':len(GEOMETRIES)==24 and raw.get('design',{}).get('geometries')=={k:[list(p) for p in v] for k,v in GEOMETRIES.items()} and lock.get('design',{}).get('geometries')=={k:[list(p) for p in v] for k,v in GEOMETRIES.items()} and raw.get('design',{}).get('geometry_seed')==lock.get('design',{}).get('geometry_seed')==GEOMETRY_SEED and raw.get('design',{}).get('families')==lock.get('design',{}).get('families')==FAMILIES and raw.get('design',{}).get('geometry_count')==lock.get('design',{}).get('geometry_count')==24 and raw.get('design',{}).get('replicates')==lock.get('design',{}).get('replicates')==list(REPS) and raw.get('design',{}).get('gen_infer_enabled') is False and lock.get('design',{}).get('arm_pair')==['intact','remove_expected_generator(s)'],
 'raw_lock_hash':raw.get('lock_sha256')==sha(LOCK),
 'worker_count_576':len(workers)==576 and raw.get('worker_count')==576,
 'no_worker_failures':not raw.get('worker_failures'),
 'unique_pids':len({x.get('pid') for x in workers})==576,
 'cell_balance':len({(x.get('family'),x.get('geometry'),x.get('replicate')) for x in workers})==576 and len(GEOMETRIES)==24 and all(sum((x.get('family'),x.get('geometry'))==(f,g) for x in workers)==3 for f in FAMILIES for g in GEOMETRIES),
 'locked_source_stability':all(x.get('source_inputs_start')==lock['locked_inputs']==x.get('source_inputs_end') for x in workers),
 'runner_hash':lock['locked_inputs']['files_sha256']['scripts/substrate_diminfer_nonlinear_geometry_distribution_v2.py']==sha(ROOT/'scripts/substrate_diminfer_nonlinear_geometry_distribution_v2.py'),
 'locked_analyzer_hash':lock['locked_inputs']['files_sha256']['scripts/analyze_substrate_diminfer_nonlinear_geometry_distribution_v2.py']==sha(ROOT/'scripts/analyze_substrate_diminfer_nonlinear_geometry_distribution_v2.py'),
 }
 inputs=True;disabled=True;ablations=True;routes=[];paired=[]
 for w in workers:
  seq=FAMILIES[w['family']];pts=GEOMETRIES[w['geometry']];target=apply(pts,seq)
  expected_base=[[f'p{i}',r,c,'red'] for i,(r,c) in enumerate(pts)];expected_target=[[f'p{i}',r,c,'red'] for i,(r,c) in enumerate(target)]
  inputs &= w.get('expected_generators')==seq and w.get('expected_target')==[list(p) for p in target]
  for arm_name in ('intact','ablated'):
   arm=w[arm_name]
   inputs &= arm.get('base')==expected_base and arm.get('target')==expected_target
   disabled &= arm.get('gen_infer_enabled') in (0,0.0)
   exact_route=route(arm)
   ok=exact_route['names']==seq and exact_route['ks']==[1]*len(seq) and not exact_route.get('has_residual') and arm.get('target')==expected_target
   routes.append({'family':w['family'],'geometry':w['geometry'],'replicate':w['replicate'],'arm':arm_name,'status':arm.get('status'),'route':exact_route,'expected_route':ok,'quanta_delta':arm.get('quanta_delta'),'wall_ns':arm.get('closure_wall_ns')})
   if arm_name=='intact':
    inv={x.get('name') for x in arm['generators_before']};ablations &= set(seq)<=inv and not arm.get('actually_removed')
   else:
    ablations &= sorted(arm.get('actually_removed',[]))==sorted(seq) and not set(seq)&{x.get('name') for x in arm['generators_after']}
  paired.append({'family':w['family'],'geometry':w['geometry'],'replicate':w['replicate'],'intact':w['intact']['closure_wall_ns'],'ablated':w['ablated']['closure_wall_ns'],'intact_quanta':w['intact']['quanta_delta'],'ablated_quanta':w['ablated']['quanta_delta']})
 checks['independent_input_reconstruction']=bool(inputs)
 # Treat geometry as the sampling unit; replicate semantics must agree within each family/geometry/arm.
 by_geo={}
 for z in routes:
  k=(z['family'],z['geometry'],z['arm'])
  semantic=(z['status'],tuple(z['route']['names']),tuple(z['route']['ks']),z['route']['source'],z['route']['has_residual'],json.dumps(z['route']['residuals'],sort_keys=True),json.dumps(z['route']['dims'],sort_keys=True),json.dumps(z['route']['deltas'],sort_keys=True),z['quanta_delta'])
  by_geo.setdefault(k,set()).add(semantic)
 checks['replicate_semantic_determinism']=len(by_geo)==8*24*2 and all(len(v)==1 for v in by_geo.values())
 checks['geninfer_disabled_both_arms']=bool(disabled)
 checks['exact_requested_ablation']=bool(ablations)
 intact=[x for x in routes if x['arm']=='intact'];abl=[x for x in routes if x['arm']=='ablated']
 checks['complete_arm_records']=len(intact)==576 and len(abl)==576 and all(x['wall_ns'] and x['status'] for x in routes)
 def route_class(x,seq):
  r=x['route'];names=r['names'];ks=r['ks'];residual=r['has_residual']
  if names==seq and ks==[1]*len(seq):return 'intended_with_residual' if residual else 'intended_exact'
  if names and len(names)<len(seq) and names==seq[:len(names)] and ks==[1]*len(names) and residual:return 'intended_prefix_with_residual'
  if names and names==seq:return 'intended_generators_other_k_with_residual' if residual else 'intended_generators_other_k'
  if names:return 'alternate_with_residual' if residual else 'alternate_exact'
  if r['record_present']:return 'rung1_residual_only' if residual else 'generatorless_transform_record'
  return 'no_transform_record'
 summaries=[]
 for f,seq in FAMILIES.items():
  ip=[x for x in intact if x['family']==f];ap=[x for x in abl if x['family']==f]
  pairs=[x for x in paired if x['family']==f]
  summaries.append({'family':f,'expected_generators':seq,'intact_n':len(ip),'intact_route_classes':dict(Counter(route_class(x,seq) for x in ip)),'ablated_n':len(ap),'ablated_route_classes':dict(Counter(route_class(x,seq) for x in ap)),'intact_statuses':dict(Counter(x['status'] for x in ip)),'ablated_statuses':dict(Counter(x['status'] for x in ap)),'intact_quanta_delta':dict(Counter(x['quanta_delta'] for x in ip)),'ablated_quanta_delta':dict(Counter(x['quanta_delta'] for x in ap)),'median_intact_ms':statistics.median(x['wall_ns'] for x in ip)/1e6,'median_ablated_ms':statistics.median(x['wall_ns'] for x in ap)/1e6,'median_paired_intact_minus_ablated_ms':statistics.median((x['intact']-x['ablated'])/1e6 for x in pairs)})
 out={'schema_version':1,'raw_sha256':sha(RAW),'lock_sha256':sha(LOCK),'analyzer_sha256':sha(Path(__file__)),'checks':checks,'passed':all(checks.values()),'summary_by_family':summaries,'routes':routes,'paired_costs':paired,'interpretation_boundary':'selected seeded 2-D operators/compositions only; ablation tests held-codebook dependence, not induction'}
 dest=ROOT/'evaluation/reports/substrate_diminfer_nonlinear_geometry_distribution_v2_1_analysis_20260926.json';dest.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':str(dest),'passed':out['passed'],'failed':[k for k,v in checks.items() if not v],'summary_by_family':summaries},indent=2))
if __name__=='__main__':main()
