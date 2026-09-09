"""Interpolation is lower grain, not a different machine — tests.

See docs/research/psychology_affect/INTERPOLATION_IS_GRAIN_PREREG.md and
scripts/interpolation_is_grain_measure.py. Measured on the real CAN field
dynamics: interpolation and retrieval are the same convergent-field read at
different resolution (grain) and commit-vs-continuous mode — degree, not kind.
"""

import sys

sys.path.insert(0, "runners/dsl/python")
sys.path.insert(0, ".")

from scripts import interpolation_is_grain_measure as m  # noqa: E402


# ---- part 1: 1-hop graded superposition + grain ------------------------

def test_one_hop_graded_monotone():
    p1 = m.part1_one_hop_graded()
    assert p1["fine"] == [1.0, 2.0, 3.0, 4.0]
    assert p1["monotone"] is True


def test_grain_collapses_gradient_to_present_absent():
    p1 = m.part1_one_hop_graded()
    assert p1["coarse_collapsed"] is True  # coarse grain => retrieval mode
    assert p1["holds"] is True


# ---- part 2: multi-hop reach -------------------------------------------

def test_multihop_reach_no_direct_edge():
    p2 = m.part2_multihop_reach()
    assert p2["steps"] > 0            # relaxation actually fired
    assert abs(p2["target_state"]) > 0.0  # target with no direct cue edge lit
    assert p2["holds"] is True


# ---- part 3: discrete commit saturates (the bounded part) --------------

def test_multihop_discrete_saturates():
    """The discrete 3-state commit is winner-take-all: identical state for
    1..4 supporting paths. This is the mode/parameter that saturates — NOT a
    substrate limit. Asserted so the boundary is pinned honestly."""
    p3 = m.part3_multihop_discrete()
    assert p3["saturates"] is True
    assert len(set(p3["states"])) == 1


# ---- part 4: continuous read recovers graded multi-hop -----------------

def test_multihop_continuous_graded():
    p4 = m.part4_multihop_continuous()
    acts = p4["acts"]
    assert all(acts[i] < acts[i + 1] for i in range(3)), acts  # monotone
    assert p4["spread"] > 0.05
    assert p4["holds"] is True


# ---- overall verdict ----------------------------------------------------

def test_verdict_supported():
    """parts 1,2,4 hold and part 3 saturates as predicted => the claim
    'interpolation is just lower grain / different parameters' is SUPPORTED."""
    out = m.main()
    assert out["supported"] is True


# ---- default == today ---------------------------------------------------

def test_default_equals_today_so_unchanged():
    """The continuous read (part 4) is a pure Python read — no seed/rule/Rust
    change. Assert the native lib md5 is the frozen baseline."""
    import hashlib
    import os
    so = "runners/dsl/python/substrate_rs/_native.abi3.so"
    if not os.path.exists(so):
        return  # nothing to check in this env
    md5 = hashlib.md5(open(so, "rb").read()).hexdigest()
    assert md5 == "7efe75eba05b006cafd15dbb4b7da246", md5
