#!/usr/bin/env python3
"""Gate recurrence cancellation and summarize glibc/PSS lifecycle accounting."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_cancel_allocator_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_cancel_allocator_v1_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_cancel_allocator_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock['sources']:errors.append('source snapshot mismatch')
 if len(rows)!=6 or len({r['pid'] for r in rows})!=6:errors.append('expected six fresh workers')
 if {(r['backend'],r['repeat']) for r in rows}!={(b,i) for b in lock['backends'] for i in range(lock['repeats'])}:errors.append('cell coverage mismatch')
 for r in rows:
  if not r['sources_stable'] or not r['host_unchanged']:errors.append('source or isolation gate failed')
  if len(r['survivor_results'])!=4 or not all(x['valid'] and len(x['offer_counts'])==64 and all(y==1 for y in x['offer_counts']) and x['fixedpoint_progress']==0 for x in r['survivor_results']):errors.append('survivor semantic gate failed')
  st=r['allocator_lifecycle_stages']
  if set(st)!={'host_baseline','after_half_cancelled','after_all_released_before_trim','malloc_trim_return','after_malloc_trim'}:errors.append('allocator checkpoints missing')
  if st.get('malloc_trim_return')!=1:errors.append('malloc_trim failed')
 for stage in ('host_baseline','after_half_cancelled','after_all_released_before_trim','after_malloc_trim'):
  for key in ('Pss','glibc_inuse_bytes','glibc_free_arena_bytes'):
   if any(key not in r['allocator_lifecycle_stages'][stage] for r in rows):errors.append(f'missing {stage}.{key}')
 summary=[]
 for b in lock['backends']:
  cell=[r for r in rows if r['backend']==b]
  summary.append({'backend':b,'repeats':3,'median':{s:{k:statistics.median(r['allocator_lifecycle_stages'][s][k] for r in cell) for k in ('Pss','glibc_inuse_bytes','glibc_free_arena_bytes')} for s in ('host_baseline','after_half_cancelled','after_all_released_before_trim','after_malloc_trim')},
   'median_post_release_inuse_delta_mib':statistics.median((r['allocator_lifecycle_stages']['after_all_released_before_trim']['glibc_inuse_bytes']-r['allocator_lifecycle_stages']['host_baseline']['glibc_inuse_bytes'])/1048576 for r in cell),
   'median_post_release_pss_delta_mib':statistics.median((r['allocator_lifecycle_stages']['after_all_released_before_trim']['Pss']-r['allocator_lifecycle_stages']['host_baseline']['Pss'])/1048576 for r in cell),
   'median_post_release_free_arena_delta_mib':statistics.median((r['allocator_lifecycle_stages']['after_all_released_before_trim']['glibc_free_arena_bytes']-r['allocator_lifecycle_stages']['host_baseline']['glibc_free_arena_bytes'])/1048576 for r in cell)})
 out={'schema':'ThoughtexperimentRecurrenceCancelAllocatorV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
