"""Gates for simultaneous top-down Doom room/corridor confabulation (162000)."""
from __future__ import annotations

import json
import os
import shutil

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402
from domains import doom_map_ingest as dm  # noqa: E402
from domains import doom_prior_readout as pr  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP_SEED = os.path.join(ROOT, "seeds", "doom_ingraph_map.json")
PRIOR_SEED = os.path.join(ROOT, "seeds", "doom_predictive_priors.json")
WAD = "/home/matt/.local/share/Steam/steamapps/common/Ultimate Doom/base/DOOM.WAD"


def _fresh(enabled=True):
    wa = WorldAdapter(seeds=())
    for path in (MAP_SEED, PRIOR_SEED):
        wa.inner.load_seed_manifest(json.load(open(path)), None)
    game = wa.s.add_node("WorldInstance", {
        "world_type": "Game", "map_mode": "doom", "predictive_map": 1.0 if enabled else 0.0,
        "body_w": 1.0, "flood_epoch": 0.0,
    })
    return wa, game


def _tick(wa, game, epoch, observations):
    for pose, src in observations:
        o = wa.s.add_node("ObsCell", {"pose": list(pose), "src": src})
        wa.inner.add_edge_unchecked(game, "observed", o)
    pr.stamp_observation_epoch(wa, game, epoch)
    dm.accumulate(wa, game, epoch=epoch)
    return pr.read_snapshot(wa, game, epoch)


def _predicted_cells(snapshot):
    out = set()
    for p in snapshot["predictions"]:
        for x in range(p["lo"][0], p["hi"][0] + 1):
            for y in range(p["lo"][1], p["hi"][1] + 1):
                out.add((x, y))
    return out


def test_partial_room_confabulates_complete_unseen_perimeter():
    wa, game = _fresh()
    free = [((x, y), "depth_free") for x in range(1, 4) for y in range(1, 4)]
    s = _tick(wa, game, 1, free)
    assert any(h["schema"] == "room" for h in s["hypotheses"])
    expected = (
        {(0, y) for y in range(0, 5)} | {(4, y) for y in range(0, 5)}
        | {(x, 0) for x in range(1, 4)} | {(x, 4) for x in range(1, 4)}
    )
    assert expected <= _predicted_cells(s)
    assert all(p not in s["cells"] for p in expected), "confabulation must not pre-fill observed belief"


def test_one_seen_corridor_wall_confabulates_the_opposite_wall():
    wa, game = _fresh()
    obs = ([((1, y), "depth_free") for y in range(1, 5)]
           + [((0, y), "depth_wall") for y in range(1, 5)])
    s = _tick(wa, game, 1, obs)
    assert any(h["schema"] == "corridor" for h in s["hypotheses"])
    pred = _predicted_cells(s)
    assert {(0, y) for y in range(1, 5)} <= pred       # seen/supporting side
    assert {(2, y) for y in range(1, 5)} <= pred       # wholly unseen opposite side
    assert all((2, y) not in s["cells"] for y in range(1, 5))


def test_transposing_corridor_transposes_the_confabulated_walls():
    wa, game = _fresh()
    obs = ([((x, 1), "depth_free") for x in range(1, 5)]
           + [((x, 0), "depth_wall") for x in range(1, 5)])
    s = _tick(wa, game, 1, obs)
    pred = _predicted_cells(s)
    assert {(x, 0) for x in range(1, 5)} <= pred
    assert {(x, 2) for x in range(1, 5)} <= pred


@pytest.mark.parametrize(
    "src,result,observed,residuals",
    [("depth_wall", "confirmed", 1.0, 0), ("depth_free", "corrected", 0.0, 1)],
)
def test_later_observation_confirms_or_corrects_graph_prediction(src, result, observed, residuals):
    wa, game = _fresh()
    _tick(wa, game, 1, [((1, y), "depth_free") for y in range(1, 5)])
    s = _tick(wa, game, 2, [((0, 2), src)])
    at = [x for x in s["outcomes"] if x["observation_epoch"] == 2 and x["pose"] == (0, 2)]
    assert len(at) == 1 and at[0]["result"] == result
    now_res = [r for r in s["residuals"] if r["observation_epoch"] == 2 and r["pose"] == (0, 2)]
    assert len(now_res) == residuals
    assert s["cells"][(0, 2)] == observed, "bottom-up observation, never prior, owns has_cell"


def test_predictive_flag_off_is_inert():
    wa, game = _fresh(enabled=False)
    s = _tick(wa, game, 1, [((x, y), "depth_free") for x in range(3) for y in range(3)])
    assert not s["hypotheses"] and not s["predictions"]


def test_python_is_readout_not_cognition():
    man = json.load(open(PRIOR_SEED))
    names = {r["name"] for r in man["rules"]}
    assert {"dpp_project_room", "dpp_project_corridor_dim0", "dpp_project_corridor_dim1"} <= names
    assert {"dpp_confirm_wall", "dpp_correct_wall_to_free"} <= names
    src = open(os.path.join(ROOT, "domains", "doom_prior_readout.py")).read()
    assert 'add_edge_unchecked(game, "has_cell"' not in src
    assert 'add_edge_unchecked(game, "has_prediction"' not in src
    assert 'add_node("MapPrediction"' not in src
    assert 'add_node("MapResidual"' not in src


def test_two_panel_renderer_has_declared_colours_and_dimensions():
    snap = {
        "epoch": 1, "cells": {(0, 0): 0.0, (1, 0): 1.0}, "quanta": [],
        "hypotheses": [{"schema": "corridor", "lo": (0, 0), "hi": (1, 0), "epoch": 1}],
        "predictions": [{"lo": (0, 1), "hi": (1, 1), "epoch": 1,
                         "schema": "corridor", "role": "parallel_wall", "value": 1.0}],
        "outcomes": [], "residuals": [],
    }
    frame = pr.compose_frame(np.zeros((240, 320, 3), np.uint8), snap, (-1, 2, -1, 2))
    assert frame.shape == (240, 640, 3)
    right = frame[:, 320:]
    colours = {tuple(v) for v in right.reshape(-1, 3)}
    assert pr.PRIOR_RGB in colours
    assert pr.OBS_FREE_RGB in colours and pr.OBS_WALL_RGB in colours


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg absent")
def test_short_video_encodes_all_two_panel_frames(tmp_path):
    snap = {
        "epoch": 1, "cells": {(0, 0): 0.0}, "quanta": [], "hypotheses": [],
        "predictions": [{"lo": (1, 0), "hi": (1, 2), "epoch": 1,
                         "schema": "corridor", "role": "parallel_wall", "value": 1.0}],
        "outcomes": [], "residuals": [],
    }
    out = tmp_path / "priors.mp4"
    meta = pr.encode_video([np.zeros((240, 320, 3), np.uint8)] * 3, [snap] * 3, str(out), fps=5)
    assert meta["width"] == 640 and meta["height"] == 240 and meta["frames"] == 3
    assert out.exists() and out.stat().st_size > 0


@pytest.mark.skipif(not os.path.exists(WAD) or shutil.which("ffmpeg") is None,
                    reason="VizDoom/WAD/ffmpeg absent")
def test_E1M1_builds_and_tests_assumptions_while_preserving_grounded_map(tmp_path):
    pytest.importorskip("vizdoom")
    from scripts import doom_predictive_priors_run as run
    s = run.run(frames=24, seed=1234, fps=8, outdir=str(tmp_path))
    assert s["tested_predictions"] > 0
    assert s["confirmed_predictions"] > 0 and s["corrected_predictions"] > 0
    assert s["final_confabulated_cells"] > 0 and s["final_spatial_hypotheses"] > 0
    assert s["M2_trajectory_consistency"] == 1.0 and s["M2_walls_on_walked_cells"] == 0
    assert s["video"]["width"] == 640 and s["video"]["height"] == 240
    assert s["video"]["frames"] == 24 and os.path.exists(os.path.join(ROOT, s["video"]["path"]))
