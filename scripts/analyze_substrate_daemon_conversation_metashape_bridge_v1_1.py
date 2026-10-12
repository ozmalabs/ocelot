#!/usr/bin/env python3
"""Adjudicate the preregistered daemon conversation/MetaShape route capture."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'evaluation/reports/substrate_daemon_conversation_metashape_bridge_v1_1_20260926.json'
LOCK=ROOT/'evaluation/substrate_capability/daemon_conversation_metashape_bridge_v1_1_lock_20260926.json'
OUT=ROOT/'evaluation/reports/substrate_daemon_conversation_metashape_bridge_v1_1_analysis_20260926.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    raw=json.loads(RAW.read_text());lock=json.loads(LOCK.read_text());turns=raw['turns']
    boot_capture=json.loads((ROOT/'evaluation/reports/substrate_induction_runtime_activation_census_v2_20260926.json').read_text())
    full_arm=next(c for c in boot_capture['cases'] if c['arm']=='daemon_full')
    gates={
      'four_locked_turns_completed':len(turns)==4 and [t['text'] for t in turns]==lock['locked_utterances'],
      'source_lock_matches_capture':raw['lock_sha256']==sha(LOCK) and raw['protocol_sha256']==sha(ROOT/'docs/research/engine_substrate/SUBSTRATE_DAEMON_CONVERSATION_METASHAPE_BRIDGE_V1_1_AMENDMENT_20260926.md') and all(len(h)==64 for h in raw['source_sha256'].values()),
      'daemon_full_seed_profile_has_expected_partial_load':raw['seed_load']['loaded']==729 and raw['seed_load']['total']==740 and len(raw['seed_load']['failed'])==11,
      'meta_shape_growth_path_present':full_arm['before']['meta_shape_growth_loaded'] and full_arm['before']['shape_decode_loop_loaded'],
      'persistence_guard_active':raw['seed_persistence_disabled'] is True,
      'no_shape_observation_or_meta_shape_delta':all(t['count_delta']['ShapeObservation']==0 and t['count_delta']['MetaShape']==0 for t in turns),
      'no_teach_hint_or_teacher_evidence_delta':all(t['count_delta']['TaughtHint']==0 and t['count_delta']['TeacherEvidence']==0 for t in turns),
      'turns_returned_replies':all(isinstance(t['reply'],str) and bool(t['reply'].strip()) for t in turns),
    }
    ms=[t['elapsed_ms'] for t in turns]
    out={'schema_version':1,'run_id':raw['run_id'],'gates':gates,'admitted':all(gates.values()),
         'observed':{'boot_elapsed_ms':raw['boot_elapsed_ms'],'turn_elapsed_ms':ms,'turn_count_deltas':[t['count_delta'] for t in turns],'baseline_counts':raw['baseline']['counts'],'failed_seed_count':len(raw['seed_load']['failed'])},
         'interpretation':'The source-locked full-profile public-conversation probe completed four turns with persistence disabled. None added ShapeObservation, MetaShape, TaughtHint, or TeacherEvidence nodes. The measured ordinary conversation route did not reach the MetaShape observation/growth path on this fixed utterance sequence. Timings are one process and one short authored sequence; v1 call-traced timings are excluded.',
         'limitations':['One full boot and four fixed authored turns, not natural interaction prevalence.','No external teacher or explicit TeacherRequest was supplied.','The 11 full-boot seed failures are present in raw capture.','Single-run timing is descriptive only.']}
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({'output':str(OUT),'admitted':out['admitted'],'gates':gates},indent=2));return 0 if out['admitted'] else 1
if __name__=='__main__':raise SystemExit(main())
