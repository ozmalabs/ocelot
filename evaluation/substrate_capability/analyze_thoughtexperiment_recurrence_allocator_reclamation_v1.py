#!/usr/bin/env python3
"""Analyze allocator and PSS stages for recurrence branch release."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_allocator_reclamation_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_allocator_reclamation_v1_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_allocator_reclamation_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock['sources']:errors.append('source snapshot mismatch')
 if len(rows)!=6 or len({r['pid'] for r in rows})!=6:errors.append('expected six fresh workers')
 if {(r['backend'],r['repeat']) for r in rows}!={(b,i) for b in lock['backends'] for i in range(lock['repeats'])}:errors.append('cell coverage mismatch')
 for r in rows:
  if not r['sources_stable'] or r['size']!=lock['size']:errors.append('source or size mismatch')
  if not r['branch_and_inner_references_deleted']:errors.append('branch release missing')
  if not all(r[k] for k in ('fault_only_guard_removed','removed_fault_rule','restored_authored_where','primary_unchanged')):errors.append('repair/isolation gate failed')
  if r['offer_count']!=1 or r['fixedpoint_progress']!=0:errors.append('recurrence outcome gate failed')
  if r['malloc_trim_return']!=1:errors.append('malloc_trim did not succeed')
 stages=('baseline','sampled_peak','after_release_before_trim','after_malloc_trim')
 for stage in stages:
  for k in ('Pss','Rss','glibc_inuse_bytes','glibc_free_arena_bytes'):
   if any(k not in r[stage] for r in rows):errors.append(f'missing {stage}.{k}')
 summary=[]
 for b in lock['backends']:
  cell=[r for r in rows if r['backend']==b]
  summary.append({'backend':b,'repeats':len(cell),'median':{stage:{k:statistics.median(r[stage][k] for r in cell) for k in ('Pss','Rss','glibc_inuse_bytes','glibc_free_arena_bytes')} for stage in stages},
   'median_inuse_delta_from_baseline_mib':statistics.median((r['after_release_before_trim']['glibc_inuse_bytes']-r['baseline']['glibc_inuse_bytes'])/1048576 for r in cell),
   'median_pss_delta_from_baseline_mib':statistics.median((r['after_release_before_trim']['Pss']-r['baseline']['Pss'])/1048576 for r in cell)})
 out={'schema':'ThoughtexperimentRecurrenceAllocatorReclamationV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
