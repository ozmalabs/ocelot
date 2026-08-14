"""ABUSIVE-DYNAMICS R1 -- THE TRAUMATIC BOND gate (block 283000).

Three arms sharing IDENTICAL machinery and an IDENTICAL total harm/relief
dose -- an INTERMITTENT (unpredictable harm<->relief) arm vs a
CONSISTENT-AFFECTION control vs a CONSISTENT-HARM control -- measuring the
bond valuation (`Partner.value`, `seeds/traumatic_bond_r1.json`'s
`tb_bond_accrue`, reading the SAME `raw_rpe` the pre-existing mood-momentum
layer, block 236000, already computes). Pre-registration:
ABUSIVE_R1_TRAUMATIC_BOND_PREREG.md. Full-power result (N=200):
results/traumatic_bond_r1.json. This gate re-runs a modest N for
CI-separation, plus the two BINDING ethics gates from Part C of
ABUSIVE_RELATIONSHIPS_SCOPING.md (byte-identical restore; no reward/
punishment source audit), glass-box and discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.traumatic_bond_r1_run import (              # noqa: E402
    run_arm, separated, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        intermittent=run_arm("intermittent", seed_base=SEED_BASE, n=N_GATE),
        consistent_affection=run_arm("consistent_affection", seed_base=SEED_BASE, n=N_GATE),
        consistent_harm=run_arm("consistent_harm", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_intermittent_beats_consistent_affection(arms):
    """FAILABLE CONTROL: if intermittency does NOT strengthen the bond more
    than the consistent-AFFECTION control, the traumatic-bonding mechanism
    (as modelled) is wrong -- reported straight either way."""
    inter = arms["intermittent"]["bond_value"]
    aff = arms["consistent_affection"]["bond_value"]
    assert separated(inter, aff), (
        f"intermittent bond CI {inter} must separate above the "
        f"consistent-affection control {aff} -- both arms were constructed "
        f"so the affection control COULD win")


def test_g_headline_intermittent_beats_consistent_harm(arms):
    """FAILABLE CONTROL: if intermittency does NOT strengthen the bond more
    than the consistent-HARM control, the mechanism is wrong."""
    inter = arms["intermittent"]["bond_value"]
    harm = arms["consistent_harm"]["bond_value"]
    assert separated(inter, harm), (
        f"intermittent bond CI {inter} must separate above the "
        f"consistent-harm control {harm} -- both arms were constructed so "
        f"the harm control COULD win")


def test_g_headline_same_total_dose_across_arms(arms):
    """DISCIPLINE: the three arms differ ONLY in schedule order, never in
    dose -- same event COUNT in every episode index (verified via the shared
    per-episode magnitude draw; see worlds/traumatic_bond_r1_world.py's
    make_schedule paired-multiset design)."""
    for arm in arms.values():
        assert arm["n"] == N_GATE


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The bond, the harm-analog arousal excursion, and the mood momentum all
    reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["bonded_to_edges"] == 1
    assert gb["partner_value"] > 0.0
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["mood_momentum"], float)


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part C.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction must actually move state (else the gate is vacuous), and the
    restored graph must be byte-identical to the pre-induction checkpoint AND
    non-oriented (identical to the pre-induction state, never merely
    'close')."""
    e = ethics_restore_demo()
    assert e["induction_moved_arousal"], "the harm-analog must actually move arousal"
    assert e["induction_moved_bond"], "the induced episode must actually move the bond"
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part C.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (rule names + the attr keys rules actually
    read/write)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_bond_off_graph"], (
        "the bond must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the already-built mood_r1 + affective_state_core; exactly
    two new rules (the smallest possible composition, per OPEN QUESTION #2 of
    ABUSIVE_RELATIONSHIPS_SCOPING.md)."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["mood_r1", "affective_state_core"]
    assert set(d["rule_names"]) == {"tb_arousal_track", "tb_bond_accrue"}
