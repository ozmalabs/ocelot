"""RUNG 2's STIMULUS — the cache is pinned, and the READER has a positive control.

Rung 2 (the experience rung, the arc's headline) shipped with no committed runner and
no cached stimulus, so its `normal` arm could not be re-run. `scripts/rung2_rerun.py`
is the runner; `tests/fixtures/vision_rung2/sesame_16x16.npz` is the stimulus. These
tests pin both, so a third party gets the SAME frames without a live server.

THE BUG THAT MAKES THE LAST TEST HERE NECESSARY (VISION_PROTOCOL.md §12):
`JellyfinWorld.catalog()` returns dicts keyed lowercase `name`/`type`/`id`. An absence
check read capital `Name`; `.get('Name','')` returns `''` and CANNOT raise, so all 137
items silently missed and a stocked library was reported as EMPTY — and rung 2's source
was declared gone. **An absence claim off a soft accessor is evidence of a LOOKUP, not
of ABSENCE.** `test_soft_accessor_absence_is_not_evidence_of_absence` reproduces the
dead instrument on a fixture, so the failure mode itself is pinned rather than
remembered.

No live server is touched here: these run offline against the committed cache.
"""
from __future__ import annotations

import os

import numpy as np
import pytest

from scripts.rung2_cache_stimulus import (CACHE, EPISODES, SERIES_ID, START_S,
                                          EVERY, SIZE, PER_EP, frames_hash)

# The content hash of the committed cache, decoded 2026-07-17 from the 10 pinned
# episodes. If this moves, the stimulus moved, and every rung-2 number moved with it.
EXPECTED_SHA16 = "4bc2c256fb55bc3d"

pytestmark = pytest.mark.skipif(not os.path.exists(CACHE),
                                reason="rung-2 stimulus cache not present")


def _frames():
    from scripts.rung2_cache_stimulus import load
    return load()


def test_the_pin_is_complete_enough_to_redecode():
    """Everything a third party needs to rebuild this cache is IN THE FILE."""
    assert SERIES_ID == "a6152b4a3b12f70779d1cb6364fa97e6"
    assert len(EPISODES) == 10
    assert all(len(eid) == 32 for eid, _ in EPISODES)     # jellyfin item ids
    assert (START_S, EVERY, SIZE, PER_EP) == (300, 6, 16, 600)


def test_cache_hashes_to_the_committed_stimulus():
    """The committed frames are the frames the numbers were measured on."""
    f = _frames()
    assert f.shape == (10, 600, 16, 16)
    assert f.dtype == np.float32
    assert frames_hash(f) == EXPECTED_SHA16


def test_frames_are_real_video_not_a_blank():
    f = _frames()
    assert 0.0 <= f.min() and f.max() <= 1.0
    assert f.std() > 0.05                                  # not a flat fill


def test_the_stimulus_is_TEMPORALLY_CORRELATED():
    """THE PROPERTY THE `normal` ARM RESTS ON, and the one the BSDS300
    substitution destroyed.

    Rung 2 is about spatioTEMPORAL structure. `bsds_crops` draws each frame as an
    INDEPENDENT random crop from a random photograph — spatially natural but
    temporally decorrelated, which is closer to the `sutured` arm than to video.
    Real video's adjacent frames are ~0.9 correlated. If this ever drops to ~0,
    the arm has silently become a shuffled-stream arm again.
    """
    f = _frames()
    cs = []
    for ep in range(f.shape[0]):
        a = f[ep].reshape(f.shape[1], -1)
        cs += [np.corrcoef(a[i], a[i + 1])[0, 1] for i in range(0, 599, 20)]
    assert float(np.nanmean(cs)) > 0.7


def test_video_window_is_contiguous_and_per_seed():
    """Contiguity preserves the temporal structure; per-seed variation preserves
    the independence that "SEED is the unit of analysis" requires."""
    from scripts.rung2_rerun import video_window, PHASE2
    w = video_window(1900)
    assert w.shape == (PHASE2, 16, 16)
    f = _frames()
    ep = 1900 % f.shape[0]
    # the window is a literal contiguous slice of one episode, not a resample
    starts = [s for s in range(f.shape[1] - PHASE2 + 1)
              if np.array_equal(f[ep, s:s + PHASE2], w)]
    assert starts, "window is not a contiguous slice of its episode"
    assert not np.array_equal(video_window(1900), video_window(1901))
    assert np.array_equal(video_window(1900), video_window(1900))   # deterministic


def test_soft_accessor_absence_is_not_evidence_of_absence():
    """PROTOCOL §12, pinned: the dead instrument that lost rung 2's corpus.

    `.get()` on the WRONG key returns a default and cannot raise, so a filtered
    enumeration over a STOCKED catalogue returns empty — indistinguishable from an
    empty library. Before reporting anything missing, prove the probe can SEE a
    thing known to be present.
    """
    catalogue = [{"name": "Sesame Street", "type": "Series", "id": "a" * 32},
                 {"name": "Bluey", "type": "Series", "id": "b" * 32}]

    # The dead instrument — the exact shape of the false-absence claim.
    assert [i for i in catalogue if "sesame" in i.get("Name", "").lower()] == []
    # The live one, on the same catalogue.
    assert len([i for i in catalogue if "sesame" in i.get("name", "").lower()]) == 1
