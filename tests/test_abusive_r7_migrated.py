"""ABUSIVE-DYNAMICS R7 -- THE RETURN CYCLE gate (block 316000).

A 2x2 factorial (honeymoon contact ON/OFF x resource collapse ON/OFF) over
three structural phases per trajectory (induction, byte-identical to R5's
own; recovery-then-leave, R5's own recovery mechanism plus the mechanical
leave() event; post-leave test, the return/remain Argmax). Pre-registration:
ABUSIVE_R7_RETURN_CYCLE_PREREG.md. Full-power result (N=200):
results/abusive_r7_return_cycle.json. This gate re-runs a modest N for
CI-separation on all five headline sub-gates, plus the BINDING ethics gates
from Part D of ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md
(byte-identical restore spanning the FULL three-phase trajectory; no
reward/punishment source audit), the failable control, glass-box, and
discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.abusive_r7_return_cycle_run import (          # noqa: E402
    run_arm, g_headline, g_control, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, SEED_BASE, ARM_NAMES)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return {arm: run_arm(arm, seed_base=SEED_BASE, n=N_GATE) for arm in ARM_NAMES}


@pytest.fixture(scope="module")
def headline(arms):
    return g_headline(arms)


@pytest.fixture(scope="module")
def control(arms):
    return g_control(arms)


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_both_drivers_above_neither(headline):
    """FAILABLE: if both_drivers' return_rate is not CI-separated above
    neither's, the mechanism (as modelled) is not producing a real return
    pull at these constants."""
    assert headline["g1_both_above_neither"], headline


def test_g_headline_honeymoon_alone_above_neither(headline):
    """FAILABLE: the bond-pull driver must be independently sufficient --
    if honeymoon_only does not separate from neither, post-separation
    contact alone is not enough to pull a recovered trajectory back at
    these constants."""
    assert headline["g2_honeymoon_above_neither"], headline


def test_g_headline_collapse_alone_above_neither(headline):
    """FAILABLE: the material-push driver must be independently sufficient
    -- if collapse_only does not separate from neither, resource collapse
    alone is not enough to pull a recovered trajectory back at these
    constants."""
    assert headline["g3_collapse_above_neither"], headline


def test_g_headline_super_additivity_over_honeymoon(headline):
    """FAILABLE (super-additivity, half 1): both_drivers must separate
    ABOVE honeymoon_only alone -- nothing in r7_appraise_return/remain/
    choose structurally guarantees this; a poorly-chosen resource_value
    could let honeymoon contact alone already saturate return's win,
    leaving resource collapse to add nothing measurable."""
    assert headline["g4_both_above_honeymoon_only"], headline


def test_g_headline_super_additivity_over_collapse(headline):
    """FAILABLE (super-additivity, half 2): both_drivers must separate
    ABOVE collapse_only alone."""
    assert headline["g5_both_above_collapse_only"], headline


def test_g_headline_full_pass(headline):
    """The overall claim requires all five sub-gates -- asserted explicitly
    so a regression that drops any one below CI-separation is caught."""
    assert headline["headline_pass"], headline
    assert headline["n_of_5_pass"] == 5, headline


# ------------------------------------------------------------------ G-control ----
def test_g_control_neither_near_floor(control):
    """THE FAILABLE CONTROL: with neither driver active, return_rate must
    sit at or extremely close to a floor. Constructed so it COULD fail --
    nothing in the Argmax forces this if bond_weight/resource_value had
    been set at a ratio where even the residual, unboosted bond outweighs
    a fully-intact material safety net."""
    assert control["neither_near_floor"], control


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """Resource population, both_drivers' collapse, the return decision,
    and the REQUIRED has_return_candidate/has_candidate edge-type split all
    reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["n_resource_nodes_total"] == 4
    # both_drivers collapses the full resource population within Phase 3.
    assert gb["resource_edge_count"] == 0
    assert gb["n_resource_nodes_severed"] == 4
    assert gb["resource_intact_count"] == 0
    assert gb["attended_by_edges"] == 0          # leave() removed it
    assert gb["left_at_tick"] > -1.0              # leave() actually fired
    # THE REQUIRED composition-hazard fix (Sec. 2.4 of the prereg): R7's own
    # candidates use a DISTINCT edge type from R4's own has_candidate, and
    # BOTH populations coexist without corrupting each other.
    assert gb["has_return_candidate_edges"] == 2
    assert gb["has_candidate_edges"] == 2
    assert gb["chosen_action"] in (0.0, 1.0)      # the Argmax actually decided


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING, spanning the FULL three-phase trajectory from a
    SINGLE checkpoint to a SINGLE restore. The induction must actually move
    bond, window, contingency (R5's own three fronts) AND resources/
    return-decision/left_at_tick (R7's own three new fronts) -- else the
    gate is vacuous -- and the restored graph must be byte-identical to the
    pre-induction checkpoint AND non-oriented."""
    e = ethics_restore_demo()
    assert e["induction_moved_bond"], "the harm-analog must actually move the bond"
    assert e["induction_moved_window"], "the induction must actually narrow the window"
    assert e["induction_moved_contingency"], "the induction must actually move contingency_prior"
    assert e["induction_moved_resources"], "the resource population must actually collapse"
    assert e["induction_moved_return_decision"], (
        "the return decision must actually move off its -1.0 sentinel")
    assert e["induction_set_left_at_tick"], "leave() must actually set left_at_tick"
    assert e["pre_resource_edges"] == 4, "all four ResourceNodes must start connected"
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"
    assert e["restored_resource_edges"] == 4, (
        "restore must reconnect the FULL resource_edge population, not just leave "
        "the graph topologically similar")


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither
    a Python rule-engine call nor any of the literal banned shaping tokens
    on the graph's decision surface."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the bond/return-decision must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends ONLY on abusive_r5_recovery (transitively pulling R1-R4);
    exactly FOUR new rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["abusive_r5_recovery"]
    assert set(d["rule_names"]) == {
        "r7_resource_collapse_sever", "r7_appraise_return",
        "r7_appraise_remain", "r7_choose"}
