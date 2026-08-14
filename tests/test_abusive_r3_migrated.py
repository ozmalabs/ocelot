"""ABUSIVE-DYNAMICS R3 -- COERCIVE CONTROL gate (block 289000).

Two arms sharing IDENTICAL abuser dynamics (snap_frustration's leaky-
integrate-fire relaxation oscillator, block 242000, UNMODIFIED, driven by
the SAME constant tension trickle in both arms) -- a SINGLE_ANCHOR arm
(victim attended_by the abuser ONLY) vs an OUTSIDE_REGULATOR control (victim
ALSO connected, via `also_attended_by`, to a fixed-calm, always-regulated
outside source) -- measuring window-narrowing (the victim's WindowOfTolerance
`half_width`) and the safety-anchor inversion (how closely the victim's
entrained arousal tracks the abuser's, over the trajectory).
Pre-registration: ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md. Full-power result
(N=200): results/abusive_r3_coercive_control.json. This gate re-runs a
modest N for CI-separation, plus the two BINDING ethics gates from Part C of
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

from scripts.abusive_r3_coercive_control_run import (         # noqa: E402
    run_arm, separated, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        single_anchor=run_arm("single_anchor", seed_base=SEED_BASE, n=N_GATE),
        outside_regulator=run_arm("outside_regulator", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_window_holds_with_outside_regulator(arms):
    """FAILABLE CONTROL: the outside-regulator arm's window must be
    CI-separated ABOVE (wider than) the single-anchor arm's -- if the
    outside-regulator arm narrows just as much, the mechanism (as modelled)
    is wrong."""
    sa = arms["single_anchor"]["final_half_width"]
    orr = arms["outside_regulator"]["final_half_width"]
    assert separated(orr, sa), (
        f"outside-regulator final half_width CI {orr} must separate above "
        f"the single-anchor arm's {sa} -- both arms share the identical "
        f"abuser driver, so nothing prevents the control from narrowing too")


def test_g_headline_window_narrows_in_single_anchor(arms):
    """The single-anchor arm's window must actually narrow toward its floor
    -- reproducing R2's own disclosed residual (Sec. 7 of
    ABUSIVE_R2_CYCLE_LIMIT_PREREG.md) as R3's headline mechanism, not merely
    failing to widen."""
    sa = arms["single_anchor"]["final_half_width"]
    assert sa["mean"] < 10.0  # below the initial half_width (10.0)


def test_g_headline_anchor_not_inverted_with_outside_regulator(arms):
    """FAILABLE CONTROL: the outside-regulator arm's victim must track the
    abuser's arousal LESS closely (a CI-separated HIGHER mean |victim -
    abuser| distance) than the single-anchor arm's victim -- if the
    outside-regulator arm's victim tracks the abuser just as closely, the
    anchor has inverted onto the abuser DESPITE the outside source, and the
    mechanism (as modelled) is wrong."""
    sa = arms["single_anchor"]["abuser_proximity"]
    orr = arms["outside_regulator"]["abuser_proximity"]
    assert separated(orr, sa), (
        f"outside-regulator abuser-tracking-distance CI {orr} must separate "
        f"above the single-anchor arm's {sa} -- both arms share the "
        f"identical abuser driver, so nothing prevents the control's victim "
        f"from tracking the abuser just as closely")


def test_g_headline_same_abuser_driver_across_arms(arms):
    """DISCIPLINE: the two arms differ ONLY in whether the outside regulator
    is structurally present -- the abuser's own snap dynamics (driven by the
    identical tension trickle) must be statistically indistinguishable
    (overlapping CIs) across arms."""
    sa_snaps = arms["single_anchor"]["final_snap_count"]
    orr_snaps = arms["outside_regulator"]["final_snap_count"]
    assert not separated(sa_snaps, orr_snaps) and not separated(orr_snaps, sa_snaps), (
        "the abuser's snap count must not differ systematically by arm -- "
        "the only manipulated variable is the outside regulator's presence")
    for arm in arms.values():
        assert arm["n"] == N_GATE


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The dyad/triad coupling, the abuser's incident state, the victim's
    entrained arousal/window/priors, and the outside regulator's fixed
    arousal all reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["attended_by_edges"] == 1
    assert gb["also_attended_by_edges"] == 1
    assert gb["abuser_snap_count"] > 1.0
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["victim_half_width"], float)
    assert isinstance(gb["victim_others_trust"], float)
    assert isinstance(gb["victim_self_worth"], float)
    assert gb["outside_arousal"] == pytest.approx(0.0)


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part C.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction (one incident cycle, single-anchor arm) must actually move
    both agents' state (else the gate is vacuous, and the window must
    actually narrow off its initial value), and the restored graph must be
    byte-identical to the pre-induction checkpoint AND non-oriented
    (identical to the pre-induction state, never merely 'close')."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["induced_state"]["victim_half_width"] < e["pre_induction_state"]["victim_half_width"], (
        "one unsupported incident cycle must narrow the victim's window")
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part C.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (rule names + the attr keys the new rules
    actually read/write)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the window/anchor state must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the already-built snap_frustration + arousal_window_coreg;
    exactly FIVE new rules (the smallest possible composition found, per the
    engine-behaviour finding in ABUSIVE_R3_COERCIVE_CONTROL_PREREG.md
    Sec. 3: two entrainment rules gated by role/arm facts, one edge-type
    substitution of arousal_window_coreg's own mark_coreg_support, and two
    counter-delta prior-tracking rules)."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["snap_frustration", "arousal_window_coreg"]
    assert set(d["rule_names"]) == {
        "r3_victim_entrainment_solo", "r3_victim_entrainment_dyad",
        "r3_mark_coreg_support_outside",
        "r3_prior_track_narrow", "r3_prior_track_widen"}
    assert d["n_new_rules"] == 5
