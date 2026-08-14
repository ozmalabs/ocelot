"""ABUSIVE-DYNAMICS R5 -- LEAVING/RECOVERY gate (block 295000).

Two arms sharing IDENTICAL induction (both reproduce R1's bond-strengthening,
R2/R3's window-narrowing/anchor-tracking, and R4's escape-freeze inside ONE
composed substrate) and differing ONLY in the recovery phase: a NO-SUPPORT
control (the failable control -- the trap must persist) vs a SUPPORT arm
(one mechanical world event, `introduce_support()`, at the phase boundary).
Pre-registration: ABUSIVE_R5_RECOVERY_PREREG.md. Full-power result (N=200):
results/abusive_r5_recovery.json. This gate re-runs a modest N for
CI-separation on three of the four headline metrics (bond/window/escape --
the anchor-distance metric is DISCLOSED in the prereg, Sec. 3.3, as a
likely null at these timescales and is measured/reported here, not gated
to a predicted direction), plus the BINDING ethics gates from Part C of
ABUSIVE_RELATIONSHIPS_SCOPING.md (byte-identical restore; no reward/
punishment source audit), the no-spontaneous-recovery control, glass-box,
and discipline.
"""
import math
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.abusive_r5_recovery_run import (             # noqa: E402
    run_arm, g_headline, g_control, glass_box_reconstruct, ethics_restore_demo,
    source_audit, discipline, SEED_BASE)

N_GATE = 40  # modest N for the test; the headline N=200 lives in results/


@pytest.fixture(scope="module")
def arms():
    return dict(
        support=run_arm("support", seed_base=SEED_BASE, n=N_GATE),
        no_support=run_arm("no_support", seed_base=SEED_BASE, n=N_GATE))


@pytest.fixture(scope="module")
def headline(arms):
    return g_headline(arms)


@pytest.fixture(scope="module")
def control(arms):
    return g_control(arms)


# --------------------------------------------------- G-headline (scientific) ----
def test_g_headline_bond_weakens_under_support(headline):
    """FAILABLE CONTROL: if the bond does NOT weaken more under outside
    support than under no support, the extinction mechanism (as modelled)
    is wrong -- reported straight either way."""
    assert headline["g1_bond_support_below_nosupport"], (
        f"support arm's recovery-phase bond must be CI-separated BELOW "
        f"the no-support arm's -- {headline}")


def test_g_headline_window_widens_under_support(headline):
    """FAILABLE CONTROL: if the window does NOT widen more under outside
    support, R3's own widen path (exercised here for the first time from
    an already-narrowed start) is not being reached."""
    assert headline["g2_window_support_above_nosupport"], (
        f"support arm's recovery-phase half_width must be CI-separated "
        f"ABOVE the no-support arm's -- {headline}")


def test_g_headline_escape_resumes_under_support(headline):
    """FAILABLE CONTROL: if escape-attempt behaviour does NOT resume more
    under outside support, the second contingency-evidence channel is not
    reaching r4_choose's Argmax."""
    assert headline["g4_escape_support_above_nosupport"], (
        f"support arm's recovery-phase attempt_rate must be CI-separated "
        f"ABOVE the no-support arm's -- {headline}")


def test_g_headline_anchor_distance_measured_honestly(arms):
    """The fourth headline metric (mean abuser-tracking distance) is
    DISCLOSED in ABUSIVE_R5_RECOVERY_PREREG.md Sec. 3.3, BEFORE this gate
    was ever run, as unlikely to separate at these timescales -- both arms'
    entrainment pulls the victim toward the fixed-calm outside source at
    the SAME gain the abuser's own, much-larger-magnitude excursions use,
    so the residual effect is smaller than these sample sizes resolve
    (R3's own confirmatory effect was already only ~12%). This test does
    NOT assert a predicted direction (there isn't one) -- it asserts the
    metric is genuinely COMPUTED off the graph (well-formed, finite CIs)
    so the honest null is measured and reported, not silently dropped."""
    for arm in ("support", "no_support"):
        ci = arms[arm]["recovery_mean_anchor_distance"]
        assert ci["n"] == N_GATE
        assert math.isfinite(ci["mean"])
        assert ci["ci_lo"] <= ci["mean"] <= ci["ci_hi"]


def test_g_headline_n_of_4_is_at_least_three(headline):
    """The overall claim is a documented PARTIAL pass (3/4), not a full
    pass -- asserted explicitly so a regression that drops g1/g2/g4 below
    3-of-4 is caught, without pretending the anchor-distance null isn't
    there."""
    assert headline["n_of_4_pass"] >= 3, headline
    assert headline["headline_partial"] or headline["headline_pass"]


# ------------------------------------------------------------------ G-control ----
def test_g_control_no_spontaneous_recovery(control):
    """The no-support arm must NOT recover on bond/window/escape without
    outside support -- if it does, the 'outside support is necessary'
    claim is wrong. Constructed so it COULD fail: r5_bond_extinguish runs
    UNCONDITIONALLY in both arms, and nothing in R1-R4's own machinery
    prevents spontaneous widening."""
    assert control["control_held"], control


# --------------------------------------------------------------- G-glass-box ----
def test_g_glass_box_reconstructs_from_graph():
    """The bond, window, priors, and contingency belief all reconstruct
    from graph_to_dict alone, including the also_attended_by edge."""
    gb = glass_box_reconstruct()
    assert gb["reconstructed_from"] == "graph_to_dict"
    assert gb["bonded_to_edges"] == 1
    assert gb["attended_by_edges"] == 1
    assert gb["also_attended_by_edges"] == 1
    assert gb["half_width"] > 5.0          # widened past the induction floor
    assert gb["contingency_prior"] > 0.3   # above the attempt/stay breakeven
    assert gb["chosen_action"] == 1.0      # resumed attempting


# ------------------------------------------------------------------ G-ethics ----
def test_g_ethics_induce_measure_restore_byte_identical():
    """Part C.1, BINDING: induce -> measure -> RESTORE byte-identically. The
    minimal 90-tick single-anchor induction must actually move bond, window,
    AND contingency simultaneously (else the gate is vacuous), and the
    restored graph must be byte-identical to the pre-induction checkpoint
    AND non-oriented (identical to the pre-induction state, never merely
    'close')."""
    e = ethics_restore_demo()
    assert e["induction_moved_bond"], "the harm-analog must actually move the bond"
    assert e["induction_moved_window"], "the induction must actually narrow the window"
    assert e["induction_moved_contingency"], "the induction must actually move contingency_prior"
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
    assert a["reads_off_graph"], (
        "the bond must be READ off the graph, never computed in Python")


# --------------------------------------------------------------- G-discipline ----
def test_g_discipline_own_engine_default_off_no_rust():
    """Own engine (source_match == own); seed self_load_only (default-OFF);
    depends only on the four already-built R1-R4 seeds; exactly two new
    rules (the smallest composition that could add a decay term and a
    second evidence channel, per the prereg's own Sec. 2.3)."""
    d = discipline()
    assert d["provenance_source_match"] == "own", d["provenance_source_match"]
    assert d["seed_self_load_only"] is True
    assert d["seed_depends_on"] == [
        "traumatic_bond_r1", "abusive_r2_cycle_limit",
        "abusive_r3_coercive_control", "abusive_r4_learned_helplessness"]
    assert set(d["rule_names"]) == {"r5_bond_extinguish", "r5_contingency_restore"}
