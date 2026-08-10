#!/usr/bin/env bash
# RUNG 7's NAMED vision bench selector.
#
# `-k vision` is NOT a definition: pytest's -k substring-matches the whole node
# ID, so it collects test_adoption.py, test_audio.py and
# test_meaning_inference_migrated.py's `..._provisional_sense_...` tests
# (pro-VISION-al). That is a sufficient cause for one suite reporting several
# different "baselines". This is the EXPLICIT FILE LIST rung 7 reports against.
cd "$(dirname "$0")/.." || exit 1
exec python -W ignore -m pytest -q \
  tests/test_vision_lateral_migrated.py \
  tests/test_vision_compose_migrated.py \
  tests/test_vision_onoff_migrated.py \
  tests/test_vision_two_eyes_migrated.py \
  tests/test_vision_complex_migrated.py \
  tests/test_vision_dorsal_migrated.py \
  tests/test_vision_maps_migrated.py \
  tests/test_vision_waves_migrated.py \
  tests/test_vision_change_migrated.py \
  tests/test_vision_setpoint_migrated.py \
  tests/test_vision_floor_migrated.py \
  tests/test_vision_growth_migrated.py \
  tests/test_vision_curriculum_migrated.py \
  tests/test_vision_migrated.py \
  tests/test_vision_graph_eye.py \
  tests/test_vision_kernels.py \
  tests/test_vision_hierarchy_and_learning.py \
  tests/test_curious_agent_vision_graph_migrated.py \
  tests/test_fb_vision.py \
  tests/test_engine_provenance_migrated.py \
  tests/test_paint_migrated.py \
  "$@"
