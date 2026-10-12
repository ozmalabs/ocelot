#!/usr/bin/env python3
"""Per-K post-hoc summary bound to the v1 cross-frame capture and lock."""
import hashlib,json,statistics,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_cross_frame_v1_lock_20261003.json'
CAP=ROOT/'evaluation/reports/substrate_geninfer_cross_frame_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_cross_frame_v1_1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def med(x):return statistics.median(x)
def main():
 lock=json.loads(LOCK.read_text());raw=json.loads(CAP.read_text());errors=[]
 if raw.get('lock_sha256')!=sha(LOCK):errors.append('raw capture lock digest mismatch')
 if raw.get('source_manifest')!=lock.get('sources'):errors.append('raw source manifest differs from lock')
 rows=raw.get('cases',[]);groups={}
 for condition in lock['conditions']:
  groups[condition]={}
  for k in lock['frame_counts']:
   cell=[r for r in rows if r['case']['condition']==condition and r['case']['k']==k]
   vals={mode:[] for mode in ('global','scoped')};acq={mode:[] for mode in vals};checks={mode:[] for mode in vals}
   for r in cell:
    for a in r['arms']:
     mode='scoped' if a['scoped'] else 'global';vals[mode].append(a['closure_wall_ns']);acq[mode].append(int(a['target_generator_present']));checks[mode].append(a['checked'])
   if len(cell)!=3:errors.append(f'{condition}/K{k}: expected 3 repeats, got {len(cell)}')
   global_ms=med(vals['global'])/1e6 if vals['global'] else None;scoped_ms=med(vals['scoped'])/1e6 if vals['scoped'] else None
   groups[condition][str(k)]={'repeats':len(cell),'global_median_closure_wall_ms':global_ms,
    'scoped_median_closure_wall_ms':scoped_ms,'global_over_scoped':global_ms/scoped_ms if scoped_ms else None,
    'global_acquisitions':sum(acq['global']),'scoped_acquisitions':sum(acq['scoped']),
    'global_candidate_checks_each_query':sorted(set(checks['global'])),'scoped_candidate_checks_each_query':sorted(set(checks['scoped']))}
 report={'schema':'GenInferCrossFrameV1_1PosthocAnalysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'gates_pass':not errors,'errors':errors,'input_sha256':{'lock':sha(LOCK),'capture':sha(CAP)},'by_condition_and_k':groups}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':not errors,'errors':errors,'by_condition_and_k':groups},sort_keys=True))
if __name__=='__main__':main()
