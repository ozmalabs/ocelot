"""ABUSIVE-DYNAMICS U2 -- SELF-SERVING SELF-ACCOUNT, SINCERELY HELD, NO
STATED-VS-HELD SPLIT, gate (block 306000).

Two arms sharing IDENTICAL abuser/victim dyad dynamics (snap_frustration's
leaky-integrate-fire relaxation oscillator, block 242000, UNMODIFIED, and
arousal_window_coreg, block 239000, UNMODIFIED, both restated/reused
self-contained in seeds/abusive_u2_self_account.json -- see that seed's own
provenance for why it does NOT depend on abusive_n1_credibility_loop.json
directly) -- MINIMIZED (minimization_discount < 1.0) and ZERO_DISCOUNT
(minimization_discount == 1.0, the failable control) -- measuring the
network's belief-gap (cred_abuser - cred_victim). There is NO stated!=held
divergence node anywhere in this rung's graph: SelfAccount.magnitude IS what
the abuser sincerely believes and reports, computed once by a declared,
undirected discount constant, never a chosen narrative.

Pre-registration: ABUSIVE_U2_SELF_ACCOUNT_PREREG.md. Full-power result
(N=200): results/abusive_u2_self_account.json. This gate re-runs a modest N
for CI-separation, plus the two BINDING ethics gates from Part D of
ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md (byte-identical restore; no
reward/punishment source audit), glass-box and discipline.
"""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.abusive_u2_self_account_run import (              # noqa: E402
    run_arm, separated, ci_separated_above_zero, not_favouring_abuser,
    glass_box_reconstruct, ethics_restore_demo, source_audit, discipline,
    SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        minimized=run_arm("minimized", seed_base=SEED_BASE, n=N_GATE),
        zero_discount=run_arm("zero_discount", seed_base=SEED_BASE, n=N_GATE))


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_minimized_entraps_with_sincere_self_account(arms):
    """HEADLINE A: the minimized arm's belief-gap must be CI-separated ABOVE
    ZERO -- the network's belief favours the abuser even though the abuser's
    self-account is SINCERE, computed once by a fixed discount, never a
    chosen narrative and never a second, separately-tracked "true" value
    withheld from the network."""
    mn = arms["minimized"]["final_belief_gap"]
    assert ci_separated_above_zero(mn), (
        f"minimized belief-gap CI {mn} must clear zero -- sincere "
        f"minimization alone, with no knowledge-gap construct, must "
        f"reproduce the loop")


def test_g_headline_zero_discount_control_does_not_favour_abuser(arms):
    """FAILABLE CONTROL B: the zero-discount arm's belief-gap CI upper bound
    must be <= 0 -- an abuser with fully accurate, undistorted self-
    perception, still sincerely reporting it, must NOT be believed over the
    victim. If it does, minimization specifically is not the driver."""
    zd = arms["zero_discount"]["final_belief_gap"]
    assert not_favouring_abuser(zd), (
        f"zero-discount belief-gap CI {zd} must not favour the abuser -- "
        f"if it does, the victim-side instability discount alone is doing "
        f"the work, not minimization")


def test_g_headline_minimized_separates_above_zero_discount(arms):
    """Comparative check: the minimized arm's belief-gap must be CI-separated
    above the zero-discount control's -- the ONLY manipulated variable
    between the two arms is minimization_discount, so nothing else could be
    producing the difference."""
    mn = arms["minimized"]["final_belief_gap"]
    zd = arms["zero_discount"]["final_belief_gap"]
    assert separated(mn, zd), (
        f"minimized belief-gap CI {mn} must separate above the "
        f"zero-discount control's {zd}")


def test_g_headline_same_driver_across_both_arms(arms):
    """DISCIPLINE: the two arms differ ONLY in minimization_discount -- the
    abuser's own snap dynamics and the victim's own dysregulation trajectory
    must be statistically indistinguishable (overlapping CIs) across both
    arms."""
    mn = arms["minimized"]
    zd = arms["zero_discount"]
    assert not separated(mn["final_snap_count"], zd["final_snap_count"]), (
        "abuser snap_count must not differ systematically between arms -- "
        "the only manipulated variable is minimization_discount")
    assert not separated(zd["final_snap_count"], mn["final_snap_count"])
    assert not separated(mn["dysreg_frac"], zd["dysreg_frac"]), (
        "victim dysreg_frac must not differ systematically between arms")
    assert not separated(zd["dysreg_frac"], mn["dysreg_frac"])
    assert mn["n"] == N_GATE
    assert zd["n"] == N_GATE


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The dyad coupling, the SelfAccount's magnitude (no stated face at
    all -- a single, sincerely-held value), and every network node's
    credibility belief all reconstruct from graph_to_dict alone."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["attended_by_edges"] == 1
    assert gb["has_self_account_edges"] == 1
    assert gb["observes_self_account_edges"] == 5
    assert gb["observes_victim_edges"] == 5
    assert gb["n_network_nodes"] == 5
    assert isinstance(gb["victim_arousal"], float)
    assert isinstance(gb["victim_half_width"], float)
    assert isinstance(gb["self_account_magnitude"], float)
    assert gb["self_account_minimization_discount"] == 0.3
    assert len(gb["network_node_belief_gaps"]) == 5
    assert len(gb["network_node_seen_mild"]) == 5
    assert len(gb["network_node_seen_severe"]) == 5
    # no insider/outsider split in U2 -- every node is wired identically, so
    # every node's belief_gap must be identical (no per-node topology variation)
    assert len(set(gb["network_node_belief_gaps"])) == 1


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part D.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    induction (one 90-tick incident cycle, minimized arm -- N1's/U0's own
    established minimum, reused unchanged since U2 has no phase schedule)
    must actually move the abuser, the self-account, the victim, NARROW the
    victim's window, AND move at least one network node's belief-gap (else
    the gate is vacuous), and the restored graph must be byte-identical to
    the pre-induction checkpoint AND non-oriented."""
    e = ethics_restore_demo()
    assert e["induction_moved_abuser"], "the tension trickle must actually move the abuser's frustration"
    assert e["induction_moved_self_account"], "the self-account magnitude must actually move"
    assert e["induction_moved_victim"], "entrainment must actually move the victim's arousal"
    assert e["induction_moved_belief_gap"], "the network must actually update its belief"
    assert e["induced_state"]["victim_half_width"] < e["pre_induction_state"]["victim_half_width"], (
        "the induction window must narrow the victim's window (non-vacuous "
        "on the window-narrowing front)")
    assert e["byte_identical"], "graph_from_dict(checkpoint) must be byte-identical"
    assert e["restore_non_oriented"], "the restored mind must equal the pre-induction state"


def test_g_ethics_no_reward_or_punishment_source_audit():
    """Part D.2, BINDING: NO reward / punishment signal anywhere -- neither a
    Python rule-engine call nor any of the literal banned shaping tokens
    (`reward_signal` / `punish` / `reinforce` / `backprop` / `gradient`) on
    the graph's decision surface."""
    a = source_audit()
    assert a["clean"], a
    assert a["forbidden_engine_hits"] == []
    assert a["forbidden_shaping_hits"] == []
    assert a["reads_off_graph"], (
        "the belief / window / self-account state must be READ off the "
        "graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on snap_frustration/arousal_window_coreg (NEVER
    abusive_n1_credibility_loop directly -- see the seed's own provenance for
    why); exactly THREE new rules."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == ["snap_frustration", "arousal_window_coreg"]
    assert set(d["rule_names"]) == {
        "u2_victim_entrainment", "u2_self_account", "u2_network_credibility"}
    assert d["n_new_rules"] == 3
