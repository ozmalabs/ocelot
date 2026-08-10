"""THE HELD-PREDICTION / DECAY / DEMOTION LOOP ON THE REAL DOOM EYE (block 200000).

Gates the 196000 staleness_decay + 198000 demotion_hierarchy loop wired onto the
REAL Doom path (photon_eye GraphEye over VizDoom E1M1 frames, the 181000 path),
self-contained on a COMMITTED fixture (tests/fixtures/doom_held_prediction/
frames.npz — real downsampled E1M1 luma + depth). VizDoom-free, deterministic.

The test RUNS the measure (able to fail on: the decoupling not transferring to
real Doom, moving latency not flat/low/integer, the loop degrading onset or
carve recovery, the work-count not tracking surprise, demotion deleting a trace,
a float in the decay bookkeeping, or a non-byte-identical default-off).

  G1  DECOUPLING on real Doom: STATIC density climbs with dwell WHILE MOVING
      latency stays flat & low as an INTEGER tick-count; gated Pareto-dominates
      both fixed-lr controls (the headline), and the registered 2x clauses hold
      on this fixture (c4 marginal ~2.05x — see RESULTS).
  G2  scene recovery preserved: per-epoch onset set BYTE-IDENTICAL, carve set
      identical, loop ON vs the current fixed-lr eye.
  G3  compute proportional to surprise: work-count drains on the static hold,
      spikes on the real pan, re-drains; << N cells re-processed on stable ticks.
  G4  demote, never delete: stale HierTraces demote FRESH->GIST, node count
      constant, re-observe promotes back and recovers detail.
  G5  integer-native decay bookkeeping; default-OFF byte-identity (loop inert
      with no params node -> the current Doom eye is unchanged).

Prereg: VISION_DOOM_HELD_PREDICTION_PREREG.md. Cost is INTEGER counts (no
wall-clock claim). NO Rust, NO new seed — the loop is the existing sd_*/dh_*
rules; this rung is the mechanical measure-adapter.
"""
import importlib
import os

import pytest

M = importlib.import_module("scripts.doom_held_prediction_measure")


@pytest.fixture(scope="module")
def res():
    assert os.path.exists(M.FIXTURE), "committed Doom fixture missing"
    f0, motion, depth, labels = M.load_fixture()
    return M.compute_criteria(f0, motion, depth, labels, seed=M.SEED)


def test_G1a_static_density_climbs(res):
    assert res["criteria"]["G1a_static_density_climbs"], res["density_asymptote"]
    a = res["density_asymptote"]
    # gated denoises the static real-Doom geometry with dwell (density = 1/error)
    assert a["gated"] < 0.5 * res["density_start_gated"]


def test_G1b_moving_latency_flat_low_integer(res):
    assert res["criteria"]["G1b_moving_latency_flat_low_integer"], \
        res["latency_moving"]["gated"]
    # ticks-to-adopt is a small INTEGER, flat (does not grow with dwell)
    assert res["latency_max_gated"] <= 3.0
    assert abs(res["latency_slope_gated"]) < 0.5
    assert res["all_integer_latency"]


def test_G1c_decoupling_dominates(res):
    # THE HEADLINE, robust: gated Pareto-dominates BOTH fixed-lr controls
    # (best density AND near-best latency) while the controls split axes.
    assert res["criteria"]["G1c_pareto_dominates"], {
        "asym": res["density_asymptote"], "meanL": res["mean_latency"]}
    a, L = res["density_asymptote"], res["mean_latency"]
    assert a["gated"] <= a["lr_low"] and a["gated"] <= a["lr_high"]
    assert L["gated"] <= L["lr_low"]
    assert L["lr_low"] > L["lr_high"]          # lr_low is the slow one
    assert a["lr_high"] > a["lr_low"]          # lr_high is the noisy one
    # the registered 2x clauses also hold on this fixture (c4 marginal ~2.05x)
    assert res["criteria"]["G1c_decoupling_dominates"], res["g1c_clauses"]
    assert res["lr_high_over_gated_density"] > 1.9


def test_G2_scene_recovery_preserved(res):
    # the loop is ADDITIVE: it must not perturb the eye's onset or carve output
    assert res["criteria"]["G2a_onset_preserved"], "onset stream perturbed"
    assert res["criteria"]["G2b_carve_preserved"], \
        (res["carve_gated"], res["carve_fixed"])


def test_G3_compute_proportional_to_surprise(res):
    assert res["criteria"]["G3a_work_drains_spikes_redrains"], {
        "plateau": res["work_plateau"], "motion_peak": res["work_motion_peak"]}
    assert res["criteria"]["G3b_fewer_cells_than_every_frame"], {
        "plateau": res["work_plateau"], "N": res["N"]}
    # stabilising scene -> far fewer cells re-processed than the every-frame eye
    assert res["work_plateau"] <= 0.25 * res["N"]
    assert res["work_motion_peak"] >= 20


def test_G4_demote_not_delete(res):
    assert res["criteria"]["G4_demote_not_delete"], res["demotion"]
    d = res["demotion"]
    # freshness decays -> tier steps down, but the node is NEVER deleted
    assert d["node_count_constant"]
    assert d["n_seeded"] == d["n_end"]
    assert d["promoted_recovered"]


def test_G5a_integer_native(res):
    assert res["criteria"]["G5a_integer_native"], res["integer_audit"]
    assert res["integer_audit"]["noninteger_cells"] == 0


def test_G5b_default_off_byte_identical(res):
    assert res["criteria"]["G5b_default_off_byte_identical"], res["default_off"]
    # with NO HeldDecayParams node the loop is inert; the current Doom eye's
    # held value field is byte-identical
    assert res["default_off"]["byte_identical"]
    assert res["default_off"]["n_decayparams_when_off"] == 0


def test_no_new_rust_no_new_seed():
    # the loop is the EXISTING sd_*/dh_* rules; this rung adds no seed of its own
    root = M.ROOT
    for name in ("staleness_decay", "demotion_hierarchy", "held_surface"):
        assert os.path.exists(os.path.join(root, "seeds", f"{name}.json"))
    # no seed file authored by this block
    assert not os.path.exists(os.path.join(root, "seeds", "doom_held_prediction.json"))
