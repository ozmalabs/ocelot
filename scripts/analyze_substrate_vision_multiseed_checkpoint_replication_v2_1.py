#!/usr/bin/env python3
"""Validate the v2.1 fresh-seed visual checkpoint adaptation capture."""
import hashlib,json,statistics
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts'),str(ROOT/'runners/dsl/python')]
MANIFEST=ROOT/'evaluation/reports/vision_multiseed_checkpoint_replication_v2_1_20260929.json'
LOCK=ROOT/'evaluation/substrate_capability/vision_multiseed_checkpoint_replication_v2_1_lock_20260929.json'
OUT=ROOT/'evaluation/reports/vision_multiseed_checkpoint_replication_v2_1_analysis_20260929.json'
SEEDS=(20260938,20260939,20260940);CAP=1_600_000
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 data=json.loads(MANIFEST.read_text());lock=json.loads(LOCK.read_text())['locked_inputs'];records=data.get('seeds',{});rows=[];integrity=True
 for seed in SEEDS:
  record=records.get(str(seed))
  if not record:integrity=False;continue
  cp_path=ROOT/record['checkpoint_file'];cp=json.loads(cp_path.read_text());graph_sha=hashlib.sha256(json.dumps(cp['graph'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
  # The source builder uses base.graph_digest's 12-decimal float canonicalizer.
  from scripts.substrate_vision_shared_substrate_multisheet_task_pilot_v1_4 import graph_digest
  graph_sha=graph_digest(cp['graph'])
  work=cp.get('adaptation_work',[]);terms=cp.get('adaptation_termination_counts',{})
  dev_delta=[b-a for a,b in zip(cp.get('development_start_steps',[]),cp.get('development_end_steps',[]))]
  valid=(cp.get('seed')==seed and cp.get('scope')=='root_scoped'
    and sha(cp_path)==record.get('checkpoint_file_sha256')
    and graph_sha==cp.get('prepared_graph_sha256')==record.get('prepared_graph_sha256')
    # The builder records development_end_steps after the later paired
    # adaptation phase too: 3,000 development calls + 2,000 presentations × 10.
    and dev_delta==[23000.0,23000.0] and cp.get('development_requested_steps')==[3000,3000]
    and min(cp.get('calibration_gain_max_abs',[]),default=0)>.01
    and all(v>0 for v in cp.get('retinal_channel_activity_after_adaptation',{}).values())
    and cp.get('adaptation_presentations')==2000 and len(work)==2000
    and sum(terms.values())==2000 and all(x['termination'] in ('fixed_point','repeated_graph_state') for x in work)
    and max((x['progress'] for x in work),default=CAP+1)<=CAP
    and all(x['attempts'] and x['attempts'][-1]['status']==x['termination'] for x in work))
  integrity &= valid
  rows.append({'seed':seed,'checkpoint_file':record['checkpoint_file'],'checkpoint_sha256':record['checkpoint_file_sha256'],
    'prepared_graph_sha256':graph_sha,'valid':valid,'development_step_deltas':dev_delta,
    'calibration_gain_max_abs':cp.get('calibration_gain_max_abs'),'channel_activity':cp.get('retinal_channel_activity_after_adaptation'),
    'adaptation_termination_counts':terms,'adaptation_progress_total':cp.get('adaptation_progress_total'),
    'adaptation_progress_max':cp.get('adaptation_progress_max'),'adaptation_presentations':len(work)})
 checks={'expected_seed_set':set(records)=={str(s) for s in SEEDS},
  'capture_matches_lock':data.get('locked_inputs')==lock,
  'source_stable':data.get('source_stable') is True,
  'checkpoint_metadata_and_graphs_valid':integrity,
  'per_seed_checkpoint_files_match_lock_record':len(rows)==3 and all(r['valid'] for r in rows)}
 out={'run_id':data.get('run_id'),'checks':checks,'passed_checks':sum(checks.values()),'total_checks':len(checks),
  'pass':all(checks.values()),'seeds':rows,
  'claim_boundary':'Three fresh independently initialized/adapted root-scoped checkpoints, using the v2.0 adaptation procedure. This validates checkpoint construction and stability inputs; it does not yet measure visual task outcomes.'}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'output':str(OUT.relative_to(ROOT)),'checks':checks,'passed_checks':out['passed_checks'],'total_checks':len(checks),
  'seeds':[{'seed':r['seed'],'valid':r['valid'],'progress_total':r['adaptation_progress_total'],'progress_max':r['adaptation_progress_max']} for r in rows]},indent=2))
 if not out['pass']:raise SystemExit('v2.1 checkpoint validation failed')
if __name__=='__main__':main()
