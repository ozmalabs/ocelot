#!/usr/bin/env python3
"""Analyze isolated-frame closures against the locked shared-codebook capture."""
from __future__ import annotations
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/geninfer_frame_isolation_v1_1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/geninfer_frame_isolation_v1_1_20261003.json'
BASE=ROOT/'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_20261003.json'
BASE_ANALYSIS=ROOT/'evaluation/reports/substrate_geninfer_multipart_codebook_scaling_v1_analysis_20261003.json'
OUT=ROOT/'evaluation/reports/geninfer_frame_isolation_v1_1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());base=json.loads(BASE.read_text());basea=json.loads(BASE_ANALYSIS.read_text());groups=data.get('groups',[]);errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('capture does not bind to lock')
 if data.get('source_manifest')!=lock.get('sources'):errors.append('source manifest mismatch')
 if not basea.get('gates_pass'):errors.append('shared baseline analysis does not pass')
 if base['captured_utc']!=lock.get('baseline_capture_utc') or len(base.get('cases',[]))!=lock.get('baseline_case_count'):
  errors.append('baseline capture identity differs from lock')
 if base.get('source_manifest',{}).get('native_sha256')!=lock['sources'].get('native_sha256'):
  errors.append('shared baseline and isolated condition use different native binaries')
 exp={(k,r) for k in lock['frame_counts'] for r in lock['repeats']}
 got={(g.get('k'),g.get('repeat')) for g in groups}
 if len(groups)!=15 or got!=exp:errors.append('group set mismatch')
 pids=[f.get('pid') for g in groups for f in g['frames']]
 if len(pids)!=len(set(pids)):errors.append('isolated frames did not use distinct processes')
 baserows={(x['case']['frame_count'],x['case']['repeat']):x for x in base.get('cases',[])}
 paired=[]
 for g in groups:
  k=g['k'];rep=g['repeat'];gid=(k,rep);shared=baserows.get(gid)
  if shared is None:errors.append(f'K{k} r{rep}: no shared baseline');continue
  if len(g['frames'])!=k:errors.append(f'K{k} r{rep}: isolated frame count mismatch')
  if len({f.get('frame') for f in g['frames']})!=k:errors.append(f'K{k} r{rep}: duplicate/missing frame IDs')
  for f in g['frames']:
   j=f['frame'];m=lock['maps'][j%len(lock['maps'])]
   if f.get('matrix')!=m or not f.get('oracle_exact'):errors.append(f'K{k} r{rep} frame {j}: oracle mismatch')
   if f.get('status')!='recognized_transformed':errors.append(f'K{k} r{rep} frame {j}: status mismatch')
   if f.get('eligible_part_count')!=1 or f.get('expected_candidate_checks')!=2400:errors.append(f'K{k} r{rep} frame {j}: isolated scope mismatch')
   if not any(x.get('matrix')==m for x in f.get('linear_generators',[])):errors.append(f'K{k} r{rep} frame {j}: target generator absent')
   if not any(x.get('base')==f'frame{j}_base' for x in f.get('receipts',[])):errors.append(f'K{k} r{rep} frame {j}: receipt lacks its base')
   if not f.get('source_stable'):errors.append(f'K{k} r{rep} frame {j}: source drift')
   for key in ('closure_wall_ns','closure_cpu_ns','hwm_before_kib','hwm_after_kib','hwm_delta_kib','nodes_before','nodes_after','edges_after'):
    if not isinstance(f.get(key),int) or f[key]<0:errors.append(f'K{k} r{rep} frame {j}: invalid {key}')
  if shared.get('case',{}).get('frame_count')!=k or shared.get('case',{}).get('repeat')!=rep:
   errors.append(f'K{k} r{rep}: shared baseline identity mismatch')
  if len(shared.get('outputs',[]))!=k or not all(x.get('oracle_exact') for x in shared.get('outputs',[])):
   errors.append(f'K{k} r{rep}: shared baseline outputs invalid')
  local_wall=sum(f['closure_wall_ns'] for f in g['frames']);local_cpu=sum(f['closure_cpu_ns'] for f in g['frames'])
  if g.get('isolated_total_wall_ns')!=local_wall or g.get('isolated_total_cpu_ns')!=local_cpu:
   errors.append(f'K{k} r{rep}: isolated sum mismatch')
  if g.get('isolated_peak_delta_kib')!=max(f['hwm_delta_kib'] for f in g['frames']):
   errors.append(f'K{k} r{rep}: isolated RSS summary mismatch')
  paired.append({'k':k,'repeat':rep,'shared_wall_ns':shared['closure_wall_ns'],'isolated_wall_ns':local_wall,
   'shared_cpu_ns':shared['closure_cpu_ns'],'isolated_cpu_ns':local_cpu,
   'shared_over_isolated':shared['closure_wall_ns']/local_wall,
   'shared_hwm_delta_kib':shared['hwm_delta_kib'],'isolated_max_hwm_delta_kib':g['isolated_peak_delta_kib'],
   'shared_candidate_checks':shared['initial_candidate_checks_total'],'isolated_candidate_checks':k*2400})
 current=[]
 for rel,dig in lock['sources']['source_sha256'].items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=dig:current.append(rel)
 native=Path(lock['sources']['native_path'])
 if not native.exists() or sha(native)!=lock['sources']['native_sha256']:current.append('native_binary')
 for rel,dig in lock['sources']['baseline_artifacts_sha256'].items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=dig:current.append(rel)
 if current:errors.append('current source/baseline differs from lock: '+', '.join(current))
 by_k={}
 for k in lock['frame_counts']:
  cell=[x for x in paired if x['k']==k]
  by_k[str(k)]={'runs':len(cell),'median_shared_closure_ms':statistics.median(x['shared_wall_ns'] for x in cell)/1e6,
   'median_isolated_total_closure_ms':statistics.median(x['isolated_wall_ns'] for x in cell)/1e6,
   'median_shared_over_isolated':statistics.median(x['shared_over_isolated'] for x in cell),
   'median_shared_hwm_delta_kib':statistics.median(x['shared_hwm_delta_kib'] for x in cell),
   'median_isolated_per_frame_hwm_delta_kib':statistics.median(f['hwm_delta_kib'] for g in groups if g['k']==k for f in g['frames']),
   'shared_candidate_checks_per_rep':k*k*2400,'isolated_candidate_checks_per_rep':k*2400}
 summary={'groups':len(groups),'isolated_frames':sum(len(g['frames']) for g in groups),'paired_exact_frames':sum(len(g['frames']) for g in groups),
  'by_frame_count':by_k,'total_closure_scope':'native run_rules settle only; boot, process startup, data construction excluded'}
 report={'schema':'GenInferFrameIsolationV1_1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'gates_pass':not errors,'errors':errors,'input_hashes':{'lock_sha256':sha(LOCK),'capture_sha256':sha(CAPTURE),
  'baseline_capture_sha256':sha(BASE),'baseline_analysis_sha256':sha(BASE_ANALYSIS)},'summary':summary,'paired':paired}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':report['gates_pass'],'errors':errors,'summary':summary},sort_keys=True))
 return int(bool(errors))
if __name__=='__main__':raise SystemExit(main())
