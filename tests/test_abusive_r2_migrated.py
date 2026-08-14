"""ABUSIVE-DYNAMICS R2 -- THE CYCLE OF ABUSE as a LIMIT CYCLE, gate
(block 286000).

Two arms sharing IDENTICAL machinery -- a CYCLE arm (a constant, jittered
per-tick tension trickle onto the abuser's leaky-integrate-fire relaxation
oscillator, block 242000, unmodified) vs a CONSTANT_REGULATION control (no
driver at all) -- measuring the victim's entrained arousal oscillation
amplitude (`std` over ticks, `arousal_window_coreg`, block 239000,
unmodified, coupled via one `attended_by` edge + one small composition
rule, `seeds/abusive_r2_cycle_limit.json`). Pre-registration:
ABUSIVE_R2_CYCLE_LIMIT_PREREG.md. Full-power result (N=200):
results/abusive_r2_cycle_limit.json. This gate re-runs a modest N for
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

from scripts.abusive_r2_cycle_limit_run import (              # noqa: E402
    run_arm, separated, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        cycle=run_arm("cycle", seed_base=SEED_BASE, n=N_GATE),
        constant_regulation=run_arm("constant_regulation", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_cycle_oscillates_more_than_constant_regulation(arms):
    """FAILABLE CONTROL: if the cycle arm does not oscillate distinguishably
    more than the constant-regulation control, the limit-cycle claim (as
    modelled) is wrong -- reported straight either way."""
    cyc = arms["cycle"]["std"]
    ctl = arms["constant_regulation"]["std"]
    assert separated(cyc, ctl), (
        f"cycle-arm victim arousal std CI {cyc} must separate above the "
        f"constant-regulation control {ctl} -- nothing in the world adapter "
        f"prevents the control from oscillating too")


def test_g_headline_control_is_a_genuine_fixed_point(arms):
    """The constant-regulation control (no incident driver at all) must show
    NO cycle -- a fixed point inside the window, per
    ABUSIVE_RELATIONSHIPS_SCOPING.md Part E, R2's own wording."""
    ctl = arms["constant_regulation"]["std"]
    assert ctl["mean"] == pytest.approx(0.0, abs=1e-9)
    assert arms["constant_regulation"]["final_snap_count"]["mean"] == 0.0


def test_g_headline_cycle_arm_actually_snaps_repeatedly(arms):
    """The cycle arm's oscillation is BACKED by repeated incidents (not a
    one-off excursion) -- the abuser snaps more than once in every episode."""
    assert arms["cycle"]["final_snap_count"]["mean"] > 1.0
    assert arms["cycle"]["n_episodes_with_snaps"] == N_GATE


def test_g_headline_same_arm_count(arms):
    for arm in arms.values():
        assert arm["n"] == N_GATE


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The dyad coupling, the abuser's incident state, and the victim's
    entrained arousal all reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["attended_by_edges"] == 1
    assert gb["abuser_snap_count"] > 1.0
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["victim_half_width"], float)


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part C.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction must actually move BOTH agents' state (else the gate is
    vacuous), and the restored graph must be byte-identical to the
    pre-induction checkpoint AND non-oriented (identical to the
    pre-induction state, never merely 'close')."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part C.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (the one new rule's name + the attr keys it
    actually reads/writes)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the oscillation must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the already-built snap_frustration + arousal_window_coreg;
    exactly ONE new rule (the smallest possible composition, per the
    engine-behaviour finding in ABUSIVE_R2_CYCLE_LIMIT_PREREG.md Sec. 3.0)."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["snap_frustration", "arousal_window_coreg"]
    assert d["rule_names"] == ["r2_victim_entrainment_via_frustration"]
    assert d["n_new_rules"] == 1
