"""THE STREAM — a bounded budget spent by SALIENCE x SCALE: the migrated gate
(VISION_STREAM_PREREG.md).

Deterministic. Pins the headline claims that perception spends a BOUNDED budget
ordered by salience x scale, via ONE water-filling seed rule
(stream_resolve_salient) with NO new Rust and NO preemption threshold (§13):

  * COARSE-FIRST  — large/coarse (high-residual) structure streams in first; fine
    detail is left at render grain under a partial budget.
  * BUDGET-ALLOCATION — the budget goes to the salient region (water-filling),
    which a residual-blind uniform spend leaves unseen.
  * PREEMPTION / TUNNEL — a majority-mass 'spear' drains the budget; the periphery
    is left at render grain ("you see very little else"), and NOT so without it.
  * BOUNDED SPEND — refinements == min(budget, N_positive) exactly; flat in N at
    fixed budget.
  * FLOOR — a structureless field invents no tunnel; the zero-residual field spends
    nothing.
  * §9 — the seed is inert with the flag OFF (default).

The 100-seed confirmatory floor lives in scripts/stream_measure.py (slow); a small
floor is exercised here.
"""
from domains.engine_provenance import engine_preamble
engine_preamble()

import random  # noqa: E402

import domains.seed_registry  # noqa: E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import stream_world as sw  # noqa: E402
from scripts.stream_measure import (  # noqa: E402
    arm_coarse_first, arm_budget_allocation, arm_preemption, arm_compute,
    arm_offday, tunnel, _stream, _boot)


def test_coarse_first_streams_large_structure_first():
    r = arm_coarse_first()
    assert r["pass"], r
    assert r["order"][:3] == [0, 1, 2]            # coarse resolved in residual order
    assert r["resolved_residuals"] == [30, 25, 20]
    assert r["inversions"] == 0                    # order monotone in residual


def test_budget_goes_to_the_salient_region():
    r = arm_budget_allocation()
    assert r["pass"], r
    assert r["salient_order"] == 0                 # salient resolved FIRST
    assert r["uniform_leaves_salient"]             # residual-blind spend misses it


def test_spear_preempts_to_a_tunnel_and_not_without():
    r = arm_preemption()
    assert r["pass"], r
    assert r["tunnel_with_spear"] is True
    assert r["periphery_resolved_with_spear"] == 0     # "you see very little else"
    assert r["periphery_resolved_without_spear"] > 0   # the contrast
    assert r["no_tunnel_without_spear"] is True


def test_spend_is_bounded_by_the_budget():
    r = arm_compute()
    assert r["c1_ok"], r["c1_bounded_spend"]       # spent == min(B, N_pos) exactly
    assert r["c2_ok"], r["c2_fixed_budget_flat"]   # flat in N at fixed budget
    for case in r["c1_bounded_spend"]:
        assert case["spent"] == min(case["budget"], case["n_positive"])


def test_flag_off_is_inert():
    r = arm_offday()
    assert r["pass"], r
    assert r["spent"] == 0
    assert all(o < 0 for o in r["order"])


def test_floor_invents_no_tunnel_from_noise():
    # F1 — a zero-residual field spends nothing (no hallucinated salience).
    s, _ = _boot()
    zero = [dict(rrow=r, rcol=c, scale=0, residual=0) for r in range(6) for c in range(6)]
    hz = _stream(s, 6, zero)
    assert sw.read_spent(s, hz) == 0
    # F2 — 8 random iid-noise fields invent no tunnel.
    B = 4
    for k in range(8):
        rng = random.Random(33000 + k)
        regions = [dict(rrow=r, rcol=c, scale=0, residual=rng.randint(1, 10))
                   for r in range(10) for c in range(10)]
        s2, _ = _boot()
        h = _stream(s2, B, regions)
        order = sw.read_order(s2, h)
        spent = sw.read_spent(s2, h)
        assert not tunnel(regions, order, spent, B)
        # F3 — order is residual-monotone: each resolved residual >= the next.
        res = [regions[i]["residual"] for i in sw.resolved_indices(s2, h)]
        assert res == sorted(res, reverse=True)
