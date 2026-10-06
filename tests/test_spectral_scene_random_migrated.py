"""Amendment A1 apparatus addition: spectral_scene.random_mondrian / neutral_mondrian.

Geometry / reflectance oracles only: no GraphEye, no seeds, no exposure.
The base-commit prefix test proves the addition is additive (every pre-A1
line of domains/spectral_scene.py is unchanged, so existing behaviour is
byte-identical).
"""
from __future__ import annotations

import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains import spectral_forward as sf  # noqa: E402
from domains import spectral_scene as ss  # noqa: E402

BASE_COMMIT = "3460f381"          # HEAD when A1 was prepared (pre-addition file)
BATTERY_SEEDS = tuple(range(101, 117))
MANY_SEEDS = tuple(range(0, 200)) + BATTERY_SEEDS
NAMES = sf.reflectance_names()
WHITE = NAMES[18]
NEUTRALS = NAMES[18:24]


def _four_connected_oracle(mask):
    # independent oracle: label connected components by repeated dilation
    if not mask.any():
        return False
    r, c = np.argwhere(mask)[0]
    reach = np.zeros_like(mask)
    reach[r, c] = True
    while True:
        grow = reach.copy()
        grow[1:, :] |= reach[:-1, :]
        grow[:-1, :] |= reach[1:, :]
        grow[:, 1:] |= reach[:, :-1]
        grow[:, :-1] |= reach[:, 1:]
        grow &= mask
        if (grow == reach).all():
            return bool((reach == mask).all())
        reach = grow


def _overwrite_oracle(scene):
    lab = np.zeros((scene.n_el, scene.n_az), dtype=int)
    for pid, _refl, c0, r0, w, h in scene.rects:
        lab[r0:r0 + h, c0:c0 + w] = pid
    return lab


def test_existing_file_is_a_byte_prefix_of_base_commit():
    base = subprocess.run(["git", "show", f"{BASE_COMMIT}:domains/spectral_scene.py"],
                          cwd=ROOT, check=True, capture_output=True, text=True).stdout
    with open(os.path.join(ROOT, "domains", "spectral_scene.py")) as f:
        now = f.read()
    assert now.startswith(base)


@pytest.mark.parametrize("fn", [ss.random_mondrian, ss.neutral_mondrian])
def test_deterministic(fn):
    for s in BATTERY_SEEDS:
        a, b = fn(s), fn(s)
        assert a == b
        assert np.array_equal(a.label_map(), b.label_map())


def test_independent_layouts():
    scenes = [ss.random_mondrian(s) for s in BATTERY_SEEDS]
    maps = {sc.label_map().tobytes() for sc in scenes}
    refl_sets = {frozenset(r[1] for r in sc.rects) for sc in scenes}
    assert len(maps) == 16 and len(refl_sets) == 16
    assert len({len(sc.rects) for sc in scenes}) > 1        # patch count varies
    assert len({sc.background for sc in scenes}) > 1        # background varies
    # no fixed gutters: some layout has two different patches 4-adjacent
    abut = 0
    for sc in scenes:
        lab = sc.label_map()
        h = (lab[:, 1:] != lab[:, :-1]) & (lab[:, 1:] > 0) & (lab[:, :-1] > 0)
        v = (lab[1:, :] != lab[:-1, :]) & (lab[1:, :] > 0) & (lab[:-1, :] > 0)
        abut += int(h.any() or v.any())
    assert abut >= 8


@pytest.mark.parametrize("seed", MANY_SEEDS)
def test_random_mondrian_constraints(seed):
    sc = ss.random_mondrian(seed)
    n = len(sc.rects)
    assert 6 <= n <= 12
    assert sc.patch_ids() == list(range(1, n + 1))
    for _pid, refl, c0, r0, w, h in sc.rects:
        assert 3 <= w <= 7 and 3 <= h <= 7
        assert 0 <= c0 and c0 + w <= sc.n_az and 0 <= r0 and r0 + h <= sc.n_el
        assert refl in NAMES
    refls = [r[1] for r in sc.rects]
    assert len(set(refls)) == n                         # without replacement
    assert sc.background in NEUTRALS
    assert sc.background not in refls                   # equal-to-background redrawn
    assert (WHITE in refls) == (seed % 2 == 0)          # white iff seed even
    if seed % 2 == 0:
        assert sc.background != WHITE
    lab = sc.label_map()
    assert np.array_equal(lab, _overwrite_oracle(sc))   # later rects overwrite
    for pid in range(0, n + 1):
        assert _four_connected_oracle(lab == pid), (seed, pid)


@pytest.mark.parametrize("seed", MANY_SEEDS)
def test_neutral_mondrian_constraints_and_same_geometry(seed):
    room, rel = ss.neutral_mondrian(seed), ss.random_mondrian(seed)
    assert [r[:1] + r[2:] for r in room.rects] == [r[:1] + r[2:] for r in rel.rects]
    assert np.array_equal(room.label_map(), rel.label_map())
    assert room.background in NEUTRALS
    for r in room.rects:
        assert r[1] in NEUTRALS and r[1] != room.background


def test_odd_seeds_can_have_white_background_and_anchor_varies():
    bgs = {ss.random_mondrian(s).background for s in BATTERY_SEEDS if s % 2}
    assert len(bgs) > 1
    # brightest-surface identity (expected L+M under E) varies across layouts
    brightest = set()
    for s in BATTERY_SEEDS:
        sc = ss.random_mondrian(s)
        ec = ss.expected_catches(sc, "E", 100.0)["lm"]
        lab = sc.label_map()
        ys = {pid: float(ec[lab == pid].mean()) for pid in [0] + sc.patch_ids()}
        brightest.add(str(sc.reflectance_of(max(ys, key=ys.get))))
    assert len(brightest) > 1


def test_scene_oracles_accept_random_scenes():
    sc = ss.random_mondrian(101)
    rep = ss.patch_report(sc, "E", 100.0)
    assert [r["patch_id"] for r in rep] == [0] + sc.patch_ids()
    ec = ss.expected_catches(sc, "D65", 1000.0)
    assert ec["lm"].shape == (sc.n_el, sc.n_az)


def test_bad_sheet_rejected():
    with pytest.raises(ValueError):
        ss.random_mondrian(1, n_az=6, n_el=16)
