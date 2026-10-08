#!/usr/bin/env python3
"""Independent gates and summary for shared-codebook multipart scaling."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_multipart_codebook_scaling_v1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data.get('cases',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('capture does not bind to lock')
 if data.get('source_manifest')!=lock.get('sources'):errors.append('source manifest mismatch')
 expected={x['id']:x for x in lock['cases']};actual={r.get('case',{}).get('id'):r for r in rows}
 if len(rows)!=15 or len(actual)!=15 or set(expected)!=set(actual):errors.append('case set mismatch')
 if len({r.get('pid') for r in rows})!=len(rows):errors.append('workers did not use distinct processes')
 for ident,r in actual.items():
  c=expected[ident];k=c['frame_count']
  if r.get('case')!=c:errors.append(f'{ident}: case differs from lock')
  if not r.get('source_stable'):errors.append(f'{ident}: source drift')
  if not r.get('diagnostic_state_unchanged'):errors.append(f'{ident}: direct diagnostic mutated graph structure')
  if len(r.get('eligible_parts_before_closure',[]))!=k:errors.append(f'{ident}: eligible frame part count mismatch')
  if len(r.get('eligible_shape_parts_after_closure',[]))!=k:errors.append(f'{ident}: eligible codebook part count changed')
  if len(r.get('initial_candidate_checks_by_frame',[]))!=k:errors.append(f'{ident}: diagnostic query count mismatch')
  checks=r.get('initial_candidate_checks_by_frame',[])
  if any(x.get('checked')!=k*2400 for x in checks):errors.append(f'{ident}: per-query candidate volume mismatch')
  if r.get('initial_candidate_checks_total')!=k*k*2400:errors.append(f'{ident}: aggregate candidate volume mismatch')
  if r.get('candidate_checks_expected_per_part')!=2400:errors.append(f'{ident}: per-part bound mismatch')
  outs=r.get('outputs',[])
  if len(outs)!=k:errors.append(f'{ident}: output count mismatch')
  gens=r.get('linear_generators_after_closure',[])
  for out in outs:
   j=out['frame'];m=lock['maps'][j%len(lock['maps'])]
   if out.get('matrix')!=m or not out.get('oracle_exact'):errors.append(f'{ident}: frame {j} oracle mismatch')
   if out.get('status')!='recognized_transformed':errors.append(f'{ident}: frame {j} did not settle transformed')
   if not any(t.get('base')==f'frame{j}_base' and t.get('generator')==f'genlin_{m}' for t in out.get('receipts',[])):
    # The repr uses commas without spaces; Python's list string includes spaces,
    # so verify by exact matrix against the generator inventory as fallback.
    target=next((g.get('name') for g in gens if g.get('matrix')==m),None)
    if not any(t.get('base')==f'frame{j}_base' and t.get('generator')==target for t in out.get('receipts',[])):
     errors.append(f'{ident}: frame {j} receipt misses own base/generator')
  for key in ('closure_wall_ns','closure_cpu_ns','hwm_before_kib','hwm_after_kib','hwm_delta_kib','closure_work','graph_nodes','graph_edges'):
   if not isinstance(r.get(key),int) or r[key]<0:errors.append(f'{ident}: invalid {key}')
 current=[]
 for rel,digest in lock['sources']['source_sha256'].items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=digest:current.append(rel)
 native=Path(lock['sources']['native_path'])
 if not native.exists() or sha(native)!=lock['sources']['native_sha256']:current.append('native_binary')
 if current:errors.append('current files differ from lock: '+', '.join(current))
 by_k={}
 for k in lock['frame_counts']:
  cell=[r for r in rows if r['case']['frame_count']==k];one=statistics.median(r['closure_wall_ns'] for r in rows if r['case']['frame_count']==1)
  by_k[str(k)]={'runs':len(cell),'candidate_checks_each_query':k*2400,'aggregate_diagnostic_candidate_checks':k*k*2400,
   'median_closure_wall_ms':statistics.median(r['closure_wall_ns'] for r in cell)/1e6,
   'median_closure_cpu_ms':statistics.median(r['closure_cpu_ns'] for r in cell)/1e6,
   'median_hwm_delta_kib':statistics.median(r['hwm_delta_kib'] for r in cell),
   'median_graph_nodes':statistics.median(r['graph_nodes'] for r in cell),
   'relative_to_k1_linear_closure':statistics.median(r['closure_wall_ns'] for r in cell)/(one*k)}
 summary={'cases':len(rows),'frames_all_exact':sum(sum(bool(o.get('oracle_exact')) for o in r['outputs']) for r in rows),
  'observations_total':sum(len(r['outputs']) for r in rows),'diagnostic_candidate_checks_total':sum(r['initial_candidate_checks_total'] for r in rows),
  'unique_generators_at_k16':len({tuple(g['matrix']) for r in rows if r['case']['frame_count']==16 for g in r['linear_generators_after_closure']}),
  'by_frame_count':by_k}
 report={'schema':'GenInferMultipartCodebookScalingV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'gates_pass':not errors,'errors':errors,'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE)},'summary':summary}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':report['gates_pass'],'errors':errors,'summary':summary},sort_keys=True))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
