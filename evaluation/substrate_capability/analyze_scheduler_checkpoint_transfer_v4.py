#!/usr/bin/env python3
"""Independent acceptance checks for the two-family scheduler transfer replay."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'evaluation/reports/scheduler_checkpoint_transfer_v4_20261004.json'
OUT=ROOT/'evaluation/reports/scheduler_checkpoint_transfer_v4_analysis_20261004.json'
def main():
 raw=json.loads(RAW.read_text());errors=[];family_rows=[]
 expected={'can_productive_coactivation_incremental_retraction','retinal_percept_synthesis_predicate_retraction'}
 for family in raw.get('families',[]):
  rows=family.get('states',[]);phase={int(r['phase']):r for r in rows}
  if len(rows)!=2 or set(phase)!={0,1}:errors.append(f"{family.get('family')}: expected exactly two ordered states")
  for r in rows:
   keys=('graph_roundtrip','rules_roundtrip','scheduler_roundtrip','global_exact','per_rule_exact','graph_after_exact','rules_after_exact','scheduler_after_exact')
   if not all(r.get(k) is True for k in keys):errors.append(f"{family.get('family')} phase {r.get('phase')}: mismatch in {[k for k in keys if r.get(k) is not True]}")
  if 0 in phase and phase[0]['entry_dirty_rule_count']<=0:errors.append(f"{family.get('family')}: fresh dirty-state control missing")
  if 1 in phase and phase[1]['entry_cursor_count']<=0:errors.append(f"{family.get('family')}: populated cursor-state control missing")
  if family.get('family')=='can_productive_coactivation_incremental_retraction' and 1 in phase:
   if not phase[1].get('edge_delete_versions_by_type_count',0):errors.append('CAN family: per-edge deletion-version control missing')
  if family.get('family')=='retinal_percept_synthesis_predicate_retraction' and 1 in phase and phase[1]['entry_dirty_node_count']<=0:errors.append('retinal family: nonempty dirty-node control missing')
  family_rows.append({'family':family.get('family'),'state_count':len(rows),'all_exact':not any(e.startswith(str(family.get('family'))+':') for e in errors),'phases':rows})
 checks={'source_stable':raw.get('source_stable') is True,'two_independent_families':{x.get('family') for x in raw.get('families',[])}==expected,'four_states':sum(len(x.get('states',[])) for x in raw.get('families',[]))==4,'all_graph_rule_scheduler_and_counter_checks':not errors,'per_edge_delete_state_nonempty':any(any(r.get('edge_delete_versions_by_type_count',0)>0 for r in x.get('states',[])) for x in raw.get('families',[])),'dirty_nodes_nonempty':any(any(r.get('entry_dirty_node_count',0)>0 for r in x.get('states',[])) for x in raw.get('families',[])),'dirty_and_cursor_state_covered':all(any(r.get('entry_dirty_rule_count',0)>0 for r in x.get('states',[])) and any(r.get('entry_cursor_count',0)>0 for r in x.get('states',[])) for x in raw.get('families',[]))}
 result={'schema':'SchedulerCheckpointTransferV4Analysis','checks':checks,'passed':all(checks.values()),'errors':errors,'families':family_rows,'claim_limit':'two small synthetic workload families and four call-entry states; no natural-task prevalence, scaling, or learning claim'}
 OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'errors':errors}));return 0 if result['passed'] else 2
if __name__=='__main__':raise SystemExit(main())
