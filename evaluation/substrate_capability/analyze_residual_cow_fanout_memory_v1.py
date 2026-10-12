#!/usr/bin/env python3
"""Analyze residual-workflow fanout, semantic, and process-memory captures."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/residual_cow_fanout_memory_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/residual_cow_fanout_memory_v1_20261002.json'
OUT=ROOT/'evaluation/reports/residual_cow_fanout_memory_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock['sources']:errors.append('source snapshot mismatch')
 required={(b,f,r) for b in lock['backends'] for f in lock['fanouts'] for r in range(lock['repeats'])}
 seen={(r['backend'],r['fanout'],r['repeat']) for r in rows}
 if seen!=required:errors.append('cell coverage mismatch')
 if len({r['pid'] for r in rows})!=len(rows):errors.append('workers were not fresh processes')
 for r in rows:
  if not r['source_stable']:errors.append('source drift')
  if not all(r['outcomes'].values()):errors.append(f"semantic outcome failed {r['backend']}/{r['fanout']}/{r['repeat']}")
  if [r['outcomes']['host_graph_counts_after'][0]-r['outcomes']['host_graph_counts_before'][0],
      r['outcomes']['host_graph_counts_after'][1]-r['outcomes']['host_graph_counts_before'][1]]!=[41,2]:
   errors.append(f"returned graph residual has unexpected size {r['backend']}/{r['fanout']}/{r['repeat']}")
 summary={'cells':len(rows),'by_cell':[]}
 for backend in lock['backends']:
  for fanout in lock['fanouts']:
   cell=[r for r in rows if r['backend']==backend and r['fanout']==fanout]
   base='host_baseline';post='all_branches_validated_and_packaged';drop='unreturned_branches_dropped'
   summary['by_cell'].append({'backend':backend,'fanout':fanout,'repeats':len(cell),
    'median_current_pss_delta_kib':{stage:statistics.median((r['memory_bytes'][stage]['Pss']-r['memory_bytes'][base]['Pss'])/1024 for r in cell) for stage in ("branches_forked","candidate_generated",post,"one_residual_returned",drop)},
    'median_current_rss_delta_kib':{stage:statistics.median((r['memory_bytes'][stage]['Rss']-r['memory_bytes'][base]['Rss'])/1024 for r in cell) for stage in ("branches_forked","candidate_generated",post,"one_residual_returned",drop)},
    'median_fork_ms_per_branch':statistics.median(statistics.median(r['timing_ns']['forks']) for r in cell)/1e6,
    'median_candidate_ms_per_branch':statistics.median(statistics.median(r['timing_ns']['candidate_operation']) for r in cell)/1e6,
    'median_peak_rss_kib':statistics.median(r['peak_rss_kb'] for r in cell)})
 result={'schema':'ResidualCowFanoutMemoryV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
