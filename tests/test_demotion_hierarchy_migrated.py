"""THE DEMOTION HIERARCHY gate (seed block 198000) — decay DEMOTES, it does not
DELETE. Built on 196000's staleness_decay atom.

Reads the measured criteria and pins the mechanism-level claims:
  * G1  DEMOTION: as freshness decays without refresh, tier steps FRESH->GIST->
        LATENT, the stored representation COARSENS (bits shed), and freshness->0
        leaves a LATENT trace (present, node exists) — NOT deletion.
  * G2  PROMOTE-ON-REFRESH: demote to latent, re-observe -> promotes to FRESH
        and RECOVERS full detail (reversible recall).
  * G3  ORDER-N-DELETION SEPARATENESS: the decay/demote atom contains NO
        del_node; only the separate, flag-gated, latent-gated dh_delete_latent
        does. The delete-on-decay FALSIFIER (deletion wired into the atom)
        DIVERGES — a to-be-promoted trace is gone.
  * G4  PAYOFF: at matched storage budget the hierarchy RETAINS MORE
        retrievable/promotable content than a flat keep-or-delete baseline
        (graceful degradation). Fidelity-sum tradeoff is REPORTED, not gated.
  * integer-native decay/tier/demote bookkeeping; default-OFF byte-identity.

The test RUNS the measure (able to fail on a non-monotone demotion, a node
deleted at freshness 0, a non-recovering promote, a non-diverging falsifier, a
hierarchy that does not out-retain flat, a float in the bookkeeping, or a
non-byte-identical default-off). Prereg: VISION_DEMOTION_HIERARCHY_PREREG.md.
"""
import importlib

import pytest

M = importlib.import_module("scripts.demotion_hierarchy_measure")


@pytest.fixture(scope="module")
def res():
    return M.main()


def test_G1_demotion_coarsens_never_deletes(res):
    c = res["criteria"]
    assert c["g1_tier_monotone_down"], res["g1_curve"]
    assert c["g1_reaches_all_tiers"], res["g1_curve"]
    assert c["g1_bits_shed"], res["g1_curve"]
    assert c["g1_coarsens"], res["g1_curve"]
    # THE HEADLINE: freshness->0 leaves a LATENT trace, not an empty cell.
    assert c["g1_zero_is_latent_not_deleted"], res["g1_curve"]
    zero = [r for r in res["g1_curve"] if r["freshness"] == 0]
    assert zero and all(r["present"] == 1 and r["exists"] and r["tier"] == 0
                        for r in zero)


def test_G2_promote_recovers_detail(res):
    c = res["criteria"]
    assert c["g2_demoted_to_latent"], res["g2_cycle"]
    assert c["g2_promoted_to_fresh"], res["g2_cycle"]
    assert c["g2_detail_recovered"], res["g2_summary"]
    assert c["g2_freshness_reset"]
    assert res["g2_summary"]["recovered"] == res["detail"]


def test_G3_deletion_is_a_separate_faculty(res):
    c = res["criteria"]
    assert c["g3a_atom_has_no_delete"], res["g3"]["audit"]
    assert c["g3a_only_delete_faculty_deletes"]
    assert c["g3a_delete_gated_flag_and_latent"], res["g3"]["audit"]
    # the delete atom is order 9 (a high-order faculty), not the decay atom
    assert res["g3"]["audit"]["delete_rule_order"] >= 5


def test_G3_delete_on_decay_falsifier_diverges(res):
    c = res["criteria"]
    assert c["g3b_hierarchy_promotes"], res["g3"]["hierarchy"]
    assert c["g3b_falsifier_loses_trace"], res["g3"]["falsifier"]
    assert c["g3b_diverges"], (res["g3"]["hierarchy"], res["g3"]["falsifier"])
    # demotion != deletion is load-bearing: same scenario, opposite outcome
    assert res["g3"]["hierarchy"]["recovered_detail"] == res["detail"]
    assert res["g3"]["falsifier"]["recovered_detail"] is None


def test_G4_hierarchy_retains_more_at_matched_budget(res):
    c = res["criteria"]
    assert c["g4_hier_retains_more"], res["g4"]["headline"]
    assert c["g4_dominates_across_sweep"], res["g4"]["sweep"]
    assert c["g4_strict_somewhere"]
    h = res["g4"]["headline"]
    # graceful degradation: many more traces kept retrievable/promotable
    assert h["hier_retrievable"] > h["flat_retrievable"]


def test_G4_fidelity_tradeoff_reported_not_gated(res):
    # honest reported nuance: at matched budget flat concentrates its bits into
    # few full-detail copies, so fidelity-SUM ties/favours flat even though the
    # hierarchy retains 3.5x more promotable traces. Reported, not a gate.
    h = res["g4"]["headline"]
    assert "hier_recall_fidelity" in h and "flat_recall_fidelity" in h
    assert h["budget_flat_gets_all"] >= h["budget_hier_gets_all"]


def test_integer_native(res):
    ia = res["integer_audit"]
    assert res["criteria"]["integer_native"], ia["offenders"]
    assert ia["offender_count"] == 0
    # the demote atom uses Ashr (LOD shed) not Div/Times
    assert "Ashr" in ia["report"]["dh_demote"]


def test_default_off_byte_identical(res):
    c = res["criteria"]
    assert c["default_off_byte_identical"], res["default_off"]
    assert c["default_off_no_trace_created"]
