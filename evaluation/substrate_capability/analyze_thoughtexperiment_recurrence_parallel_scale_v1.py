#!/usr/bin/env python3
"""Gate one-million-node recurrence branch waves and summarize throughput."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_parallel_scale_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_parallel_scale_v1_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_parallel_scale_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sig(w):return (tuple(w['offer_counts']),tuple(w['closure_progress']),w['fixedpoint_progress'],w['restored_authored_where'])
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock['sources']:errors.append('source snapshot mismatch')
 if len(rows)!=6 or len({r['pid'] for r in rows})!=6:errors.append('expected six fresh workers')
 if {(r['backend'],r['replicate']) for r in rows}!={(b,i) for b in lock['backends'] for i in range(lock['repeats'])}:errors.append('backend/repeat coverage mismatch')
 for r in rows:
  if r['noise_nodes']!=lock['size'] or r['task_candidate_count']!=lock['candidate_count']:errors.append('task scale mismatch')
  if not r['sources_stable'] or not r['primary_unchanged']:errors.append(f"source/primary isolation failed {r['backend']}/{r['replicate']}")
  if set(r['results'])!={'sequential','concurrent'}:errors.append('execution modes missing')
  for mode,w in r['results'].items():
   if w['valid_branches']!=lock['fanout'] or len(w['branch_results'])!=lock['fanout']:errors.append(f"incomplete branches {r['backend']}/{r['replicate']}/{mode}")
   if not all(x['valid'] and len(x['offer_counts'])==lock['candidate_count'] and all(v==1 for v in x['offer_counts']) and x['fixedpoint_progress']==0 for x in w['branch_results']):errors.append(f"branch oracle failed {r['backend']}/{r['replicate']}/{mode}")
 paired={(r['backend'],r['replicate']):r for r in rows}
 for backend in lock['backends']:
  for rep in range(lock['repeats']):
   row=paired[(backend,rep)]
   if [sig(x) for x in row['results']['sequential']['branch_results']] != [sig(x) for x in row['results']['concurrent']['branch_results']]:errors.append('mode semantic parity failure')
 for rep in range(lock['repeats']):
  a,b=paired[('full_copy',rep)],paired[('shared_pages',rep)]
  for mode in ('sequential','concurrent'):
   sa=sorted(sig(x) for x in a['results'][mode]['branch_results']);sb=sorted(sig(x) for x in b['results'][mode]['branch_results'])
   if sa!=sb:errors.append('backend semantic parity failure')
 summary=[]
 for backend in lock['backends']:
  cell=[r for r in rows if r['backend']==backend]
  for mode in ('sequential','concurrent'):
   vals=[r['results'][mode] for r in cell]
   summary.append({'backend':backend,'mode':mode,'fanout':lock['fanout'],'repeats':len(vals),
    'median_wall_ms':statistics.median(v['wall_ms'] for v in vals),
    'median_experiments_per_second':statistics.median(v['experiments_per_second'] for v in vals),
    'median_peak_delta_pss_mib':statistics.median(v['peak_delta_bytes']['Pss']/1048576 for v in vals),
    'median_peak_delta_rss_mib':statistics.median(v['peak_delta_bytes']['Rss']/1048576 for v in vals),
    'median_sampler_count':statistics.median(v['samples'] for v in vals)})
 speed={b:statistics.median(r['results']['sequential']['wall_ms'] for r in rows if r['backend']==b)/statistics.median(r['results']['concurrent']['wall_ms'] for r in rows if r['backend']==b) for b in lock['backends']}
 result={'schema':'ThoughtexperimentRecurrenceParallelScaleV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary,'concurrent_speedup_vs_sequential':speed}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
