#!/usr/bin/env python3
"""Analyze allocator-live bytes separately from residual-workflow PSS/RSS."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_allocator_reclamation_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/residual_cow_allocator_reclamation_v1_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_allocator_reclamation_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock['sources']:errors.append('source snapshot mismatch')
 required={(b,r) for b in lock['backends'] for r in range(lock['repeats'])}
 if {(r['backend'],r['repeat']) for r in rows}!=required:errors.append('worker grid mismatch')
 if len({r['pid'] for r in rows})!=len(rows):errors.append('workers not fresh processes')
 for r in rows:
  if not (r['source_stable'] and r['allocator_wrapper_source_stable']):errors.append('source drift')
  if r['allocator_sample_count']!=6:errors.append('wrong allocator stage count')
  if not all(r['outcomes'].values()):errors.append(f"semantic gate failed {r['backend']}/{r['repeat']}")
  final=r['memory_bytes']['unreturned_branches_dropped']
  if not all(k in final for k in ('glibc_inuse_bytes','post_trim_Pss','post_trim_Rss','malloc_trim_return')):
   errors.append(f"missing allocator/trim sample {r['backend']}/{r['repeat']}")
 summary={'workers':len(rows),'fanout':lock['fanout'],'host_nodes':lock['host_nodes'],'by_backend':{}}
 for backend in lock['backends']:
  rs=[r for r in rows if r['backend']==backend]
  stages=('host_baseline','all_branches_validated_and_packaged','one_residual_returned','unreturned_branches_dropped')
  summary['by_backend'][backend]={'median_glibc_inuse_mib':{s:statistics.median(r['memory_bytes'][s]['glibc_inuse_bytes'] for r in rs)/1048576 for s in stages},
   'median_glibc_inuse_delta_live_to_drop_mib':statistics.median((r['memory_bytes']['unreturned_branches_dropped']['glibc_inuse_bytes']-r['memory_bytes']['all_branches_validated_and_packaged']['glibc_inuse_bytes'])/1048576 for r in rs),
   'median_glibc_free_arena_after_drop_mib':statistics.median(r['memory_bytes']['unreturned_branches_dropped']['glibc_free_arena_bytes'] for r in rs)/1048576,
   'median_pss_delta_before_trim_mib':statistics.median((r['memory_bytes']['unreturned_branches_dropped']['Pss']-r['memory_bytes']['host_baseline']['Pss'])/1048576 for r in rs),
   'median_pss_delta_after_trim_mib':statistics.median((r['memory_bytes']['unreturned_branches_dropped']['post_trim_Pss']-r['memory_bytes']['host_baseline']['Pss'])/1048576 for r in rs),
   'median_rss_delta_after_trim_mib':statistics.median((r['memory_bytes']['unreturned_branches_dropped']['post_trim_Rss']-r['memory_bytes']['host_baseline']['Rss'])/1048576 for r in rs),
   'malloc_trim_return_values':sorted({r['memory_bytes']['unreturned_branches_dropped']['malloc_trim_return'] for r in rs})}
 result={'schema':'ResidualCowAllocatorReclamationV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
