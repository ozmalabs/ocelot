#!/usr/bin/env python3
"""Independent checks and cost analysis for explicit GenInfer scope."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_explicit_scope_v1_3_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/substrate_geninfer_explicit_scope_v1_3_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_explicit_scope_v1_3_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def median(values):return statistics.median(values)
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('cases',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('capture does not bind to lock')
 if data.get('source_manifest')!=lock.get('sources'):errors.append('source manifest mismatch')
 expected={x['id']:x for x in lock['cases']};actual={r.get('case',{}).get('id'):r for r in rows}
 if len(rows)!=69 or len(actual)!=69 or set(actual)!=set(expected):errors.append('case set mismatch')
 if len({r.get('pid') for r in rows})!=len(rows):errors.append('workers did not run in distinct processes')
 for ident,r in actual.items():
  c=expected[ident];kind=c['kind']
  if r.get('case')!=c:errors.append(f'{ident}: case mismatch')
  if not r.get('source_stable'):errors.append(f'{ident}: source/native drift')
  checks=r.get('diagnostic_checks',[]);outs=r.get('outputs',[]);members=r.get('scope_membership',[])
  if len(checks)!=len(outs) or len(outs)!=len(members):errors.append(f'{ident}: frame record count mismatch')
  if not all(x.get('state_unchanged') for x in checks):errors.append(f'{ident}: direct diagnostic changed graph structure')
  for key in ('closure_wall_ns','closure_cpu_ns','hwm_before_kib','hwm_after_kib','hwm_delta_kib','closure_work','nodes_before','nodes_after','edges_after'):
   if not isinstance(r.get(key),int) or r[key]<0:errors.append(f'{ident}: invalid {key}')
  if kind=='positive':
   k=c['k'];mode=c['mode'];expected_each=2400*k if mode in ('unscoped_global','explicit_global') else 2400
   if any(x.get('checked')!=expected_each for x in checks):errors.append(f'{ident}: candidate checks per frame mismatch')
   if sum(x.get('checked',-1) for x in checks)!=k*expected_each:errors.append(f'{ident}: candidate checks total mismatch')
   if len(outs)!=k:errors.append(f'{ident}: output count mismatch')
   for j,out in enumerate(outs):
    m=lock['maps'][j%len(lock['maps'])]
    if out.get('matrix')!=m or out.get('status')!='recognized_transformed' or not out.get('oracle_exact'):
     errors.append(f'{ident}: frame {j} exact recognition failed')
    if not out.get('target_generator_present'):errors.append(f'{ident}: frame {j} target generator absent')
    if not any(t.get('base')==f'frame{j}_base' for t in out.get('receipts',[])):
     errors.append(f'{ident}: frame {j} receipt did not name its base')
   for j,member in enumerate(members):
    if not member.get('members_agree') or not member.get('provenance_sha256') or len(member['provenance_sha256'])!=64:
     errors.append(f'{ident}: frame {j} scope membership/provenance invalid')
    if mode=='unscoped_global':
     if member.get('part_scope_id_attr') is not None or member.get('obs_scope_id_attr') is not None:
      errors.append(f'{ident}: unscoped legacy control unexpectedly has scoped attrs')
    elif member.get('part_scope_id_attr')!=member.get('scope_id') or member.get('obs_scope_id_attr')!=member.get('scope_id'):
     errors.append(f'{ident}: explicit scope token differs across record/part/observation')
  else:
   if len(checks)!=1 or checks[0].get('checked')!=0:errors.append(f'{ident}: required-scope control did not fail closed')
   if len(outs)!=1 or outs[0].get('target_generator_present'):errors.append(f'{ident}: missing/mismatched scope minted target generator')
   if not members or not members[0].get('provenance_sha256'):errors.append(f'{ident}: control provenance receipt absent')
 current=[]
 for rel,digest in lock['sources']['source_sha256'].items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=digest:current.append(rel)
 native=Path(lock['sources']['native_path'])
 if not native.exists() or sha(native)!=lock['sources']['native_sha256']:current.append('native_binary')
 manifest=ROOT/'runners/dsl/python/substrate_rs/_native.build.json'
 if not manifest.exists() or sha(manifest)!=lock['sources']['native_build_manifest_sha256']:current.append('native_build_manifest')
 if current:errors.append('current inputs differ from lock: '+', '.join(current))
 positives=[r for r in rows if r['case']['kind']=='positive'];controls=[r for r in rows if r['case']['kind']!='positive']
 by_mode={}
 for mode in lock['modes']:
  mode_rows=[r for r in positives if r['case']['mode']==mode];by_k={}
  for k in lock['frame_counts']:
   cell=[r for r in mode_rows if r['case']['k']==k]
   by_k[str(k)]={'runs':len(cell),'candidate_checks_each_query':(k*2400 if mode in ('unscoped_global','explicit_global') else 2400),
    'candidate_checks_total_per_run':sum(x['initial_candidate_checks_total'] for x in cell)//len(cell) if cell else None,
    'median_closure_wall_ms':median(r['closure_wall_ns'] for r in cell)/1e6,
    'median_closure_cpu_ms':median(r['closure_cpu_ns'] for r in cell)/1e6,
    'median_hwm_delta_kib':median(r['hwm_delta_kib'] for r in cell)}
  by_mode[mode]=by_k
 paired=[]
 for k in lock['frame_counts']:
  for rep in lock['repeats']:
   items={(r['case']['mode']):r for r in positives if r['case']['k']==k and r['case']['repeat']==rep}
   if set(items)!=set(lock['modes']):continue
   paired.append({'k':k,'repeat':rep,
    'unscoped_ns':items['unscoped_global']['closure_wall_ns'],
    'explicit_global_ns':items['explicit_global']['closure_wall_ns'],
    'frame_scoped_ns':items['frame_scoped']['closure_wall_ns'],
    'unscoped_over_scoped':items['unscoped_global']['closure_wall_ns']/items['frame_scoped']['closure_wall_ns'],
    'explicit_global_over_scoped':items['explicit_global']['closure_wall_ns']/items['frame_scoped']['closure_wall_ns']})
 summary={'cases':len(rows),'positive_cases':len(positives),'scope_controls':len(controls),
  'exact_positive_observations':sum(sum(bool(o['oracle_exact']) for o in r['outputs']) for r in positives),
  'scope_control_target_acquisitions':sum(bool(o['target_generator_present']) for r in controls for o in r['outputs']),
  'by_mode_and_k':by_mode,'paired_costs':paired}
 report={'schema':'GenInferExplicitScopeV1_3Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'gates_pass':not errors,'errors':errors,'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE)},'summary':summary}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':report['gates_pass'],'errors':errors,'summary':summary},sort_keys=True))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
