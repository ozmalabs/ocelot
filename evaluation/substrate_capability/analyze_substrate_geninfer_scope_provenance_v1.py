#!/usr/bin/env python3
"""Analyze the locked GenInfer scope-provenance enforcement probe."""
import hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/substrate_geninfer_scope_provenance_v1_lock_20261003.json'
CAPTURE=ROOT/'evaluation/reports/substrate_geninfer_scope_provenance_v1_20261003.json'
OUT=ROOT/'evaluation/reports/substrate_geninfer_scope_provenance_v1_analysis_20261003.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAPTURE.read_text());rows=data['cases'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('capture does not bind to lock')
 if data.get('source_manifest')!=lock['sources']:errors.append('source manifest mismatch')
 expected={x['id']:x for x in lock['cases']};actual={r.get('case',{}).get('id'):r for r in rows}
 if len(rows)!=36 or len(actual)!=36 or set(actual)!=set(expected):errors.append('case set mismatch')
 if len({r.get('pid') for r in rows})!=36:errors.append('workers not isolated by process')
 summary={}
 for state in ('valid','missing','contradictory'):
  cell=[r for r in rows if r.get('scope_record_state')==state]
  summary[state]={'cases':len(cell),'diagnostic_candidates':sorted(set(r.get('diagnostic_checked') for r in cell)),
   'target_acquisitions':sum(bool(r.get('output',{}).get('target_generator_present')) for r in cell),
   'exact_outputs':sum(bool(r.get('output',{}).get('oracle_exact')) for r in cell),
   'statuses':sorted(set(str(r.get('output',{}).get('status')) for r in cell)),
   'median_closure_wall_ms':sorted(r['closure_wall_ns'] for r in cell)[len(cell)//2]/1e6 if cell else None}
  for r in cell:
   if not r.get('source_stable'):errors.append(f"{r['case']['id']}: source drift")
   if r.get('diagnostic_checked')!=2400 or not r.get('diagnostic_unchanged'):errors.append(f"{r['case']['id']}: diagnostic mismatch")
   if r.get('part_scope_id')!=r.get('scope_id') or r.get('observation_scope_id')!=r.get('scope_id'):errors.append(f"{r['case']['id']}: scope token mismatch")
   if not r.get('output',{}).get('oracle_exact'):errors.append(f"{r['case']['id']}: fixture oracle invalid")
 if any(summary[x]['target_acquisitions']!=12 for x in summary):errors.append('runtime response differed by scope record state')
 gates=not errors
 report={'schema':'GenInferScopeProvenanceV1Analysis','generated_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  'gates_pass':gates,'errors':errors,'summary':summary,'interpretation':
  'The probe passed as a measurement: scope record state did not alter inference. The native path appears to enforce scope_id matching, not FrameScope record provenance.'}
 OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'analysis':OUT.relative_to(ROOT).as_posix(),'gates_pass':gates,'errors':len(errors),'summary':summary},sort_keys=True))
 return 0 if gates else 1
if __name__=='__main__':sys.exit(main())
