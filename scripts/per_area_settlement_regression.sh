#!/usr/bin/env bash
# BLOCK 186000 — the CROSS-DOMAIN regression list this rung reports against.
#
# Named explicitly, never a `-k` substring selector (this tree is 0-for-6 on
# substring selectors; `-k vision` alone collects test_adoption.py and
# `..._provisional_sense_...`). Run BEFORE and AFTER; the comparison is the SET
# OF FAILING NODE IDS, never a count.
#
# Coverage rationale: `run_rules` is the hottest path in the tree, so the list
# spans the engine core, the cognitive-task scheduler (the area machinery this
# rung makes executable), the seizure/psychosis pathology dials that ride on
# the scheduler, the reading/pipeline path, the whole vision stack, and the
# non-vision cognition (composer / shape-decode / conversation / navigation).
cd "$(dirname "$0")/.." || exit 1
exec python -W ignore -m pytest -q --tb=no -rf -p no:cacheprovider \
  tests/test_cognitive_tasks_migrated.py \
  tests/test_cortices_tick.py \
  tests/test_seizure_dynamics_migrated.py \
  tests/test_psychosis_grounding_migrated.py \
  tests/test_observe_pipeline_migrated.py \
  tests/test_engine_provenance_migrated.py \
  tests/test_failure_baseline_migrated.py \
  tests/test_dirty_index_migrated.py \
  tests/test_eye_accel_migrated.py \
  tests/test_async_carve_migrated.py \
  tests/test_async_motion_migrated.py \
  tests/test_2d_motion_salience_migrated.py \
  tests/test_2d_retina_migrated.py \
  tests/test_retinal_onset_migrated.py \
  tests/test_residual_salience_event_migrated.py \
  tests/test_two_eyes_migrated.py \
  tests/test_vision_migrated.py \
  tests/test_vision_lateral_migrated.py \
  tests/test_vision_compose_migrated.py \
  tests/test_vision_onoff_migrated.py \
  tests/test_vision_dorsal_migrated.py \
  tests/test_vision_maps_migrated.py \
  tests/test_vision_waves_migrated.py \
  tests/test_vision_change_migrated.py \
  tests/test_vision_growth_migrated.py \
  tests/test_composer_driver_migrated.py \
  tests/test_dimension_inference_migrated.py \
  tests/test_transform_decode_migrated.py \
  tests/test_quanta_navigation_migrated.py \
  tests/test_gap_awareness_migrated.py \
  tests/test_elaboration_migrated.py \
  tests/test_topic_route_selfheal_migrated.py \
  tests/test_self_gaps_surfacing_migrated.py \
  tests/test_information_commit_gate_migrated.py \
  "$@"
