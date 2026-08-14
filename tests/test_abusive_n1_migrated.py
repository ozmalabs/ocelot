"""ABUSIVE-DYNAMICS N1 -- THE TWO-FACED ABUSER + THE CREDIBILITY-ASYMMETRY
LOOP gate (block 298000).

Three arms sharing IDENTICAL abuser dynamics (snap_frustration's
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, driven
by the SAME constant tension trickle in every arm) -- BASELINE (the loop:
victim attended_by the abuser, every network node reads only the abuser's
stated face), PRIVATE_FACE_CONTROL (identical victim dyad, but one network
node reads the abuser's true held state directly instead), and
NON_DYSREGULATED_CONTROL (the victim is simply never attended_by the
abuser) -- measuring the network's belief-gap (cred_abuser - cred_victim)
and the victim's window `half_width`.

Pre-registration: ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md. Full-power result
(N=200): results/abusive_n1_credibility_loop.json. This gate re-runs a
modest N for CI-separation, plus the two BINDING ethics gates from Part D of
ABUSIVE_RELATIONSHIPS_NETWORK.md (byte-identical restore; no reward/
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

from scripts.abusive_n1_credibility_loop_run import (         # noqa: E402
    run_arm, separated, not_favouring_abuser, glass_box_reconstruct,
    ethics_restore_demo, source_audit, discipline, SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        baseline=run_arm("baseline", seed_base=SEED_BASE, n=N_GATE),
        private_face_control=run_arm("private_face_control", seed_base=SEED_BASE, n=N_GATE),
        non_dysregulated_control=run_arm("non_dysregulated_control", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_loop_entraps_vs_private_face_control(arms):
    """FAILABLE CONTROL A1: the baseline arm's belief-gap must be
    CI-separated ABOVE the private-face insider's belief-gap -- if the
    insider is entrapped just as much as the rest of the network, the
    credibility-asymmetry mechanism (as modelled) is wrong."""
    base = arms["baseline"]["final_belief_gap"]
    insider = arms["private_face_control"]["final_insider_belief_gap"]
    assert separated(base, insider), (
        f"baseline belief-gap CI {base} must separate above the private-face "
        f"insider's {insider} -- both share the identical abuser driver and "
        f"victim dyad, so nothing prevents the insider from entrapping too")


def test_g_headline_loop_entraps_vs_non_dysregulated_control(arms):
    """FAILABLE CONTROL A2: the baseline arm's belief-gap must be
    CI-separated ABOVE the non-dysregulated control's belief-gap -- if a
    victim who never dysregulates is discounted just as much as one who
    does, the mechanism (as modelled) is wrong."""
    base = arms["baseline"]["final_belief_gap"]
    ndc = arms["non_dysregulated_control"]["final_belief_gap"]
    assert separated(base, ndc), (
        f"baseline belief-gap CI {base} must separate above the "
        f"non-dysregulated control's {ndc} -- both share the identical "
        f"abuser driver, so nothing prevents the control from being "
        f"discounted just as much")


def test_g_headline_private_face_control_does_not_favour_abuser(arms):
    """FAILABLE CONTROL A3: the private-face insider's belief-gap must NOT
    favour the abuser (CI upper bound <= 0) -- an uncorrupted observable of
    the abuser's TRUE held state must not reward its credibility."""
    insider = arms["private_face_control"]["final_insider_belief_gap"]
    assert not_favouring_abuser(insider), (
        f"private-face insider's belief-gap {insider} must not favour the "
        f"abuser (CI upper bound must be <= 0)")


def test_g_headline_non_dysregulated_control_does_not_favour_abuser(arms):
    """FAILABLE CONTROL A4: a victim who never dysregulates must not be
    disbelieved relative to the abuser (CI upper bound <= 0) despite the
    abuser's identical charm broadcast."""
    ndc = arms["non_dysregulated_control"]["final_belief_gap"]
    assert not_favouring_abuser(ndc), (
        f"non-dysregulated control's belief-gap {ndc} must not favour the "
        f"abuser (CI upper bound must be <= 0)")


def test_g_headline_window_holds_with_non_dysregulated_control(arms):
    """FAILABLE CONTROL B: the non-dysregulated control's window must be
    CI-separated ABOVE (wider than) the baseline arm's."""
    base = arms["baseline"]["final_half_width"]
    ndc = arms["non_dysregulated_control"]["final_half_width"]
    assert separated(ndc, base), (
        f"non-dysregulated control final half_width CI {ndc} must separate "
        f"above the baseline arm's {base}")


def test_g_headline_same_abuser_driver_across_all_arms(arms):
    """DISCIPLINE: the three arms differ ONLY in victim coupling / network
    observation topology -- the abuser's own snap dynamics must be
    statistically indistinguishable (overlapping CIs) across all arms."""
    snaps = {a: arms[a]["final_snap_count"] for a in arms}
    for a in arms:
        for b in arms:
            if a == b:
                continue
            assert not separated(snaps[a], snaps[b]), (
                f"abuser snap_count must not differ systematically between "
                f"{a} and {b} -- the only manipulated variable is the "
                f"victim's coupling / network observation topology")
        assert arms[a]["n"] == N_GATE


def test_g_headline_private_face_outsiders_replicate_baseline(arms):
    """DISCIPLINE: the four outsider nodes in private_face_control must
    replicate the baseline arm's belief-gap -- the ONLY manipulated
    variable within that arm is the ONE insider's observation edge."""
    base = arms["baseline"]["final_belief_gap"]
    outsiders = arms["private_face_control"]["final_outsider_belief_gap"]
    assert not separated(base, outsiders) and not separated(outsiders, base), (
        "the four outsider nodes must replicate baseline's belief-gap -- "
        "they are wired identically")


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The dyad coupling, the abuser's stated-face gap, the victim's
    entrained arousal/window, and every network node's credibility belief
    all reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["attended_by_edges"] == 1
    assert gb["observes_stated_edges"] == 4
    assert gb["observes_held_edges"] == 1
    assert gb["observes_victim_edges"] == 5
    assert gb["n_network_nodes"] == 5
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["victim_half_width"], float)
    assert gb["abuser_stated_charm"] == pytest.approx(1.0)
    assert len(gb["network_node_belief_gaps"]) == 5
    # exactly one insider (observes_private=1) among the five nodes
    assert sorted(gb["network_node_observes_private"]) == [0.0, 0.0, 0.0, 0.0, 1.0]
    # the insider's belief-gap must be the minimum (most negative / least
    # favourable to the abuser) among the five
    assert gb["network_node_belief_gaps"][0] < gb["network_node_belief_gaps"][1]


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction (one incident cycle, baseline arm) must actually move the
    abuser, the victim, AND at least one network node's belief-gap (else
    the gate is vacuous), and the restored graph must be byte-identical to
    the pre-induction checkpoint AND non-oriented (identical to the
    pre-induction state, never merely 'close')."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["induction_moved_belief_gap"], "the network must actually update its belief"
    assert e["induced_state"]["victim_half_width"] < e["pre_induction_state"]["victim_half_width"], (
        "one unsupported incident cycle must narrow the victim's window")
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface (rule names + the attr keys the new rules
    actually read/write)."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the belief/window state must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the already-built snap_frustration + arousal_window_coreg;
    exactly FOUR new rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["snap_frustration", "arousal_window_coreg"]
    assert set(d["rule_names"]) == {
        "n1_victim_entrainment", "n1_abuser_stated_charm",
        "n1_network_credibility_stated", "n1_network_credibility_private"}
    assert d["n_new_rules"] == 4
