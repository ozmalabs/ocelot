#!/usr/bin/env python3
"""Gate million-node recurrence branch cancellation and survivor semantics."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_cancel_scale_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_cancel_scale_v1_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_cancel_scale_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock['sources']:errors.append('source snapshot mismatch')
 if len(rows)!=6 or len({r['pid'] for r in rows})!=6:errors.append('expected six fresh workers')
 if {(r['backend'],r['repeat']) for r in rows}!={(b,i) for b in lock['backends'] for i in range(lock['repeats'])}:errors.append('backend/repeat coverage mismatch')
 stages=('host_baseline','all_branches_patched_live','half_cancelled','survivors_finished_and_released')
 for r in rows:
  if r['noise_nodes']!=lock['size'] or r['fanout']!=lock['fanout'] or r['candidate_count']!=lock['candidate_count']:errors.append('size/candidate/fanout mismatch')
  if r['cancelled_count']!=lock['cancel_count'] or len(r['cancelled_stages'])!=lock['cancel_count']:errors.append('cancel count mismatch')
  if not all(x['removed'] and x['restored'] and x['branch_reference_present'] and x['inner_reference_present'] for x in r['cancelled_stages']):errors.append('cancelled branch was not patched/live')
  if len(r['survivor_results'])!=lock['fanout']-lock['cancel_count'] or not all(x['valid'] and len(x['offer_counts'])==lock['candidate_count'] and all(v==1 for v in x['offer_counts']) and x['fixedpoint_progress']==0 for x in r['survivor_results']):errors.append('survivor semantic gate failed')
  if not r['host_unchanged'] or not r['sources_stable']:errors.append('host isolation or source stability failed')
  if any(k not in r['stages_bytes'] for k in stages):errors.append('memory stage missing')
 summary=[]
 for backend in lock['backends']:
  cell=[r for r in rows if r['backend']==backend]
  summary.append({'backend':backend,'repeats':len(cell),'median_wall_ms':statistics.median(r['wall_ms'] for r in cell),
   'median_peak_delta_pss_mib':statistics.median(r['sampled_peak_bytes']['Pss']/1048576-r['stages_bytes']['host_baseline']['Pss']/1048576 for r in cell),
   'median_pss_delta_mib_by_stage':{s:statistics.median((r['stages_bytes'][s]['Pss']-r['stages_bytes']['host_baseline']['Pss'])/1048576 for r in cell) for s in stages},
   'median_rss_delta_mib_by_stage':{s:statistics.median((r['stages_bytes'][s]['Rss']-r['stages_bytes']['host_baseline']['Rss'])/1048576 for r in cell) for s in stages},
   'median_samples':statistics.median(r['sample_count'] for r in cell)})
 result={'schema':'ThoughtexperimentRecurrenceCancelScaleV1Analysis','gates_pass':not errors,'errors':errors,'summary':summary}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
