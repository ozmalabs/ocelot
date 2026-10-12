#!/usr/bin/env python3
"""Independent semantic/provenance gate and summary for recurrence scale capture."""
import hashlib,json,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
LOCK=ROOT/'evaluation/substrate_capability/thoughtexperiment_recurrence_repair_scale_v1_lock_20261002.json'
CAP=ROOT/'evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_20261002.json'
OUT=ROOT/'evaluation/reports/thoughtexperiment_recurrence_repair_scale_v1_analysis_20261002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 lock=json.loads(LOCK.read_text());data=json.loads(CAP.read_text());rows=data['rows'];errors=[]
 if data.get('lock_sha256')!=sha(LOCK):errors.append('lock hash mismatch')
 if data.get('sources')!=lock['sources']:errors.append('capture source snapshot mismatch')
 if len(rows)!=6 or len({r['pid'] for r in rows})!=6:errors.append('expected six unique fresh worker processes')
 if {(r['backend'],r['replicate']) for r in rows}!={(b,r) for b in lock['backends'] for r in range(lock['repeats'])}:errors.append('backend/repeat coverage mismatch')
 for r in rows:
  if r.get('size')!=lock['size']:errors.append(f"size mismatch {r.get('backend')}/{r.get('replicate')}")
  if not r['sources_stable']:errors.append(f"source drift {r['backend']}/{r['replicate']}")
  sem=('fault_only_guard_removed','removed_fault_rule','restored_authored_where','primary_revision_unchanged','primary_counts_unchanged','primary_rules_unchanged')
  if not all(r[k] for k in sem):errors.append(f"semantic/isolation failure {r['backend']}/{r['replicate']}")
  if r['offer_count']!=1 or r['fixedpoint_progress']!=0:errors.append(f"task outcome failure {r['backend']}/{r['replicate']}")
  for k in ('Pss','Rss','Private_Dirty'):
   if k not in r['baseline_bytes'] or k not in r['peak_bytes'] or k not in r['after_drop_bytes']:errors.append(f"missing memory sample {k}")
 grouped=[]
 for b in lock['backends']:
  cell=[r for r in rows if r['backend']==b]
  grouped.append({'backend':b,'repeats':len(cell),'median_peak_delta_mib':{k:statistics.median(r['peak_delta_bytes'][k]/(1024*1024) for r in cell) for k in ('Pss','Rss','Private_Dirty')},
   'median_after_drop_delta_mib':{k:statistics.median((r['after_drop_bytes'][k]-r['baseline_bytes'][k])/(1024*1024) for r in cell) for k in ('Pss','Rss','Private_Dirty')},
   'median_rehearsal_ms':statistics.median(r['duration_ms'] for r in cell),'median_sampler_count':statistics.median(r['sample_count'] for r in cell)})
 outcomes={(r['backend'],r['replicate']):(tuple(r['closure_progress']),r['offer_count'],r['fixedpoint_progress']) for r in rows}
 parity=all(outcomes[('full_copy',rep)]==outcomes[('shared_pages',rep)] for rep in range(lock['repeats']))
 if not parity:errors.append('backend outcome parity failed')
 result={'schema':'ThoughtexperimentRecurrenceRepairScaleV1Analysis','gates_pass':not errors,'errors':errors,'backend_outcome_parity':parity,'summary':grouped}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result,indent=2,sort_keys=True));return int(bool(errors))
if __name__=='__main__':sys.exit(main())
