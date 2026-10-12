#!/usr/bin/env python3
"""Gate recurrence repair semantics and explicit branch release measurements."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_repair_scale_v1_1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_1_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock['sources']:errors.append('capture source snapshot mismatch')
 if len(rows)!=6 or len({r['pid'] for r in rows})!=6:errors.append('expected six unique fresh workers')
 if {(r['backend'],r['replicate']) for r in rows}!={(b,i) for b in lock['backends'] for i in range(lock['repeats'])}:errors.append('backend/repeat coverage mismatch')
 for r in rows:
  if r['size']!=lock['size'] or not r['sources_stable']:errors.append('size or source gate failed')
  if not r['branch_and_inner_references_deleted']:errors.append('branch release code gate failed')
  sem=('fault_only_guard_removed','removed_fault_rule','restored_authored_where','primary_revision_unchanged','primary_counts_unchanged','primary_rules_unchanged')
  if not all(r[k] for k in sem) or r['offer_count']!=1 or r['fixedpoint_progress']!=0:errors.append(f"semantic/isolation failure {r['backend']}/{r['replicate']}")
  for key in ('Pss','Rss','Private_Dirty'):
   if key not in r['baseline_bytes'] or key not in r['peak_bytes'] or key not in r['after_drop_bytes']:errors.append(f'missing {key} sample')
 parity=all((next(x for x in rows if x['backend']=='full_copy' and x['replicate']==i)['closure_progress'],next(x for x in rows if x['backend']=='full_copy' and x['replicate']==i)['offer_count'],next(x for x in rows if x['backend']=='full_copy' and x['replicate']==i)['fixedpoint_progress'])==(next(x for x in rows if x['backend']=='shared_pages' and x['replicate']==i)['closure_progress'],next(x for x in rows if x['backend']=='shared_pages' and x['replicate']==i)['offer_count'],next(x for x in rows if x['backend']=='shared_pages' and x['replicate']==i)['fixedpoint_progress']) for i in range(lock['repeats']))
 if not parity:errors.append('backend outcome parity failed')
 summary=[]
 for b in lock['backends']:
  cell=[r for r in rows if r['backend']==b]
  summary.append({'backend':b,'repeats':len(cell),'median_peak_delta_mib':{k:statistics.median(r['peak_delta_bytes'][k]/1048576 for r in cell) for k in ('Pss','Rss','Private_Dirty')},
   'median_after_release_delta_mib':{k:statistics.median((r['after_drop_bytes'][k]-r['baseline_bytes'][k]) /1048576 for r in cell) for k in ('Pss','Rss','Private_Dirty')},
   'median_rehearsal_ms':statistics.median(r['duration_ms'] for r in cell),'median_sampler_count':statistics.median(r['sample_count'] for r in cell)})
 result={'schema':'ThoughtexperimentRecurrenceRepairScaleV1_1Analysis','gates_pass':not errors,'errors':errors,'backend_outcome_parity':parity,'summary':summary}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
