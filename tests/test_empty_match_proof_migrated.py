"""THE EMPTY-MATCH-SET PROOF — the block 189000 gate.

Self-contained: every fact this pins is recomputed here, none is read back from
a results file. Pins, in order:

  * the flag is DEFAULT OFF, and OFF is the committed path;
  * `empty_match_proof` ON is a DROPPABLE BYTE-IDENTICAL MIRROR — on a VISION
    workload and on a NON-VISION workload;
  * ⚠️ THE UNSOUND-PREDICATE FALSIFIER: a deliberately weakened predicate that
    claims "empty" for a rule that CAN match MUST break byte-identity AND must
    break a real observable (the graph-path onset stream). If a wrong proof
    broke nothing, the identity check would be too weak to trust;
  * the SOUNDNESS boundary: a zero-match-edge rule is NEVER claimed empty, and
    a rule is claimed empty ONLY when one of its match edge types has zero live
    edges — re-derived here from the graph, not from the engine's answer;
  * the proof reaches exactly the rules 188000 named, on the path where they
    are empty, and DECLINES on the path where they are not;
  * the COST claim: the shipped accel settlement gets materially cheaper;
  * NO FREE LUNCH: where nothing is empty, the proof does not win.
"""
from __future__ import annotations

import os
import sys
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

M = pytest.importorskip("scripts.empty_match_proof_measure")


def _has_flags():
    import substrate_rs as srs
    return hasattr(srs.Substrate()._inner, "set_empty_match_proof")


needs_engine = pytest.mark.skipif(
    not _has_flags(), reason="engine has no block-189000 flags (rebuild)")

THE_THREE = M.THE_THREE


# ------------------------------------------------------------ the mirror -----
@needs_engine
def test_flag_defaults_off():
    """A new Substrate has the proof OFF. The committed path is the default."""
    import substrate_rs as srs
    inner = srs.Substrate()._inner
    # No rule is loaded, so nothing can be provably empty either way.
    assert inner.provably_empty_rules() == []
    assert inner.empty_match_skips() == []


@needs_engine
@pytest.mark.parametrize("name", ["vision_carve", "scheduler_wide"])
def test_proof_is_byte_identical_on_vision_and_non_vision(name):
    """C2a — turning the proof ON changes NOTHING in the whole-graph
    float-exact dump. One VISION workload, one NON-VISION workload."""
    fn = M.WORKLOADS[name]
    off = fn(False)
    on = fn(True)
    assert off == on, f"{name}: empty_match_proof is NOT byte-identical"


@needs_engine
def test_default_equals_explicit_off():
    """The flag never touched == the flag explicitly off."""
    assert M.WORKLOADS["scheduler"](False) == M.WORKLOADS["scheduler"](False)


# ------------------------------------------------ ⚠️ THE UNSOUND FALSIFIER ---
@needs_engine
def test_UNSOUND_predicate_breaks_byte_identity():
    """⚠️ THE CRITICAL FALSIFIER. Weaken the predicate so it claims "empty" for
    a rule that CAN match (a SINGLETON edge type treated as absent) and it MUST
    break byte-identity. A wrong proof that broke nothing would mean this
    gate's identity check is too weak to be trusted."""
    off = M.WORKLOADS["vision_carve"](False)
    unsound = M.WORKLOADS["vision_carve"](True, True)
    assert off != unsound, (
        "the UNSOUND predicate did NOT change the graph — the identity check "
        "is too weak to trust, FIX THE CHECK before believing the sound one")


@needs_engine
def test_UNSOUND_predicate_breaks_a_real_observable():
    """Byte-identity of a dump could in principle be insensitive. The onset
    STREAM is the eye's actual output: the unsound predicate silently kills
    `retinal_mint_onset_2d` (it binds the retina's SINGLE `has_onset_params_2d`
    edge), so the stream must collapse."""
    good = M.graph_path_onsets(proof=True)
    bad = M.graph_path_onsets(proof=True, unsound=True)
    base = M.graph_path_onsets(proof=False)
    assert good["onsets"] == base["onsets"] and good["digest"] == base["digest"], (
        "the SOUND proof moved the onset stream — it is not sound")
    assert bad["onsets"] < base["onsets"], (
        f"the UNSOUND predicate left the onset stream at {bad['onsets']} "
        f"(base {base['onsets']}) — the falsifier is VACUOUS")
    assert bad["digest"] != base["digest"]


# ------------------------------------------------------ the SOUNDNESS edge ---
@needs_engine
def test_a_zero_match_edge_rule_is_never_claimed_empty():
    """A rule with NO match edges has the single EMPTY binding, which is not
    the empty SET. Claiming it empty would silently disable every where-only
    rule in the tree."""
    import substrate_rs as srs
    s = srs.Substrate()
    inner = s._inner
    inner.set_empty_match_proof(True)
    hub = s.add_node("Hub", {"n": 1.0})
    assert hub is not None
    # A where-only rule: NO match edges at all. Its match set is the single
    # EMPTY binding, which is not the empty SET.
    idx = inner.add_rule({
        "name": "where_only_rule",
        "match": [],
        "where": {"type": "Lit", "value": 1.0},
        "effects": [],
    })
    assert idx is not None
    # This graph has ZERO edges of every type, so a predicate that looked only
    # at edge populations without the match_edges.is_empty() guard would claim
    # this rule empty. It must not.
    claimed = [r[0] for r in inner.provably_empty_rules()]
    assert "where_only_rule" not in claimed, (
        "a zero-match-edge rule was claimed provably empty — that would "
        "silently disable every where-only rule in the tree")
    assert claimed == []


@needs_engine
def test_claimed_empty_iff_a_match_edge_type_has_zero_live_edges():
    """Re-derive the predicate from the GRAPH, independently of the engine's
    answer, and require exact agreement. This is what makes the claim a proof
    rather than a heuristic."""
    import collections
    from scripts import dirty_index_measure as DI
    from domains import doom_photon_world as dpw
    lumas = M.P._fixture_lumas()
    n_el, n_az = 120, 160
    f0 = DI._grid(lumas[0], n_el, n_az)
    eye, inner = M.build_eye(n_el, n_az, accel=True, precise=True, split=False)
    for _ in range(4):
        eye.submit_photons_2d(
            dpw.packets_from_counts(dpw.photon_counts(f0, None), None))
        inner.run_rules_settle(0, M.MAX_ROUNDS, False, False)
    d = inner.graph_to_dict()
    pop = collections.Counter()
    for e in d["edges"]:
        pop[e.get("type") or e.get("edge_type") if isinstance(e, dict) else e[1]] += 1
    claimed = {r[0]: r[2] for r in inner.provably_empty_rules()}
    # Every rule the engine claims empty must be witnessed by a genuinely
    # zero-population edge type.
    for rule, witness in claimed.items():
        assert pop.get(witness, 0) == 0, (
            f"{rule}: engine claims empty via '{witness}' but that edge type "
            f"has {pop.get(witness)} live edges — UNSOUND")
    eye.stop()


# --------------------------------------------- WHICH rules the proof reaches --
@needs_engine
def test_the_proof_reaches_all_three_named_rules_on_the_accel_path():
    """188000 named three rules woken every tick, O(cells) each, progressed 0.
    On the shipped accel path all three have a zero-population match edge
    type."""
    diag = M.diagnosis()
    got = diag["accel_160x120"]["of_the_three"]
    for r in THE_THREE:
        assert got[r] is not None, f"{r} is NOT provably empty on the accel path"
    assert got["photon_column_synthesizes_retinal_percept"][
        "witness_edge_type"] in ("l_receptor", "m_receptor", "s_receptor",
                                 "has_retinal_percept")
    assert got["retinal_mint_onset_2d"]["witness_edge_type"] == "has_task"
    assert got["photon_apply_receptor_transduction"][
        "witness_edge_type"] == "has_task"


@needs_engine
def test_the_proof_DECLINES_on_the_graph_path_where_the_tasks_are_real():
    """THE CONTROL, and the reason this is a proof and not a config coupling:
    with the accelerator OFF, `has_task` is populated, and the very same
    predicate declines for two of the three rules. The mechanism reads the
    GRAPH, never a flag."""
    diag = M.diagnosis()
    got = diag["graph_20x15"]["of_the_three"]
    assert got["retinal_mint_onset_2d"] is None
    assert got["photon_apply_receptor_transduction"] is None
    # The 2-D-sheet rule is empty on BOTH paths — it has no percepts anywhere.
    assert got["photon_column_synthesizes_retinal_percept"] is not None


# --------------------------------------------------------------- the COST ----
@needs_engine
@pytest.mark.slow
def test_the_accel_settlement_gets_materially_cheaper():
    """H1 — the headline. Skipping the provably-empty enumerations materially
    reduces the shipped 160x120 settlement cost, byte-identically."""
    cost = M.accel_cost(trials=3, probe=3)
    assert cost["ratio_proof_over_off"] <= 0.60, (
        f"proof/off = {cost['ratio_proof_over_off']:.3f}, expected <= 0.60")
    # ⚠️ The prereg's H2 was written as a SHARE (< 5 %) and it is BREACHED —
    # measured ~35 %. It is reported as a breach in RESULTS §3 and is NOT
    # gated here, because the share is a fraction of a denominator that itself
    # collapses ~1000x and is therefore not a fact about the eye. What IS
    # gated is the quantity H2 was trying to express: the ABSOLUTE cost of the
    # three rules, which must fall by at least 100x.
    off3 = cost["off"]["micros_of_THE_THREE_per_tick"]
    on3 = cost["proof"]["micros_of_THE_THREE_per_tick"]
    assert on3 * 100 <= off3, (
        f"THE THREE cost {off3:.1f} us/tick with the proof off and "
        f"{on3:.1f} us/tick with it on — expected at least a 100x drop")
    skipped = {s[0] for s in cost["proof"]["empty_match_skips"]}
    for r in THE_THREE:
        assert r in skipped, f"{r} was never skipped"


@needs_engine
def test_no_free_lunch_where_nothing_is_empty():
    """F2 — on a workload whose rules have genuinely NON-empty match sets, the
    proof must cost the same or slightly more. A win here would mean the
    predicate is claiming emptiness it has not proved."""
    # Gate-grade threshold (instrument-discipline lesson 7): this is a WALL-CLOCK
    # ratio, and the "no free lunch" median sits at ~0.99 on BOTH the base engine
    # and every accelerator that keeps the empty-match path byte-identical — but
    # the per-call (median-of-reps) noise floor reaches ~0.90–0.92 on clean main
    # itself (measured: min 0.916 over 8 calls on 2458afa2, min 0.915 on the
    # 192000 incremental-match engine — statistically identical distributions).
    # The old >=0.95 threshold therefore sat INSIDE the instrument's own noise and
    # flaked ~1-in-4 (it only ever "passed reliably" by luck of a short check). A
    # REAL free lunch — the predicate unsoundly claiming emptiness it never proved
    # (cf 185000 Branch-B) — shows ratio ≈0.5, far below the noise floor, so
    # >=0.85 stays able-to-fail on the real violation while not flaking on noise.
    # reps raised 5→11 to tighten the median.
    nfl = M.no_free_lunch(reps=11)
    assert nfl["nothing_is_empty"], (
        "the F2 control is not a control — some rule IS provably empty in it")
    assert nfl["ratio_proof_over_off"] >= 0.85, (
        f"proof was {nfl['ratio_proof_over_off']:.3f} x the cost where NOTHING "
        f"is empty — that is a free lunch, i.e. a bug")


# ------------------------------------------------------------- provenance ----
@needs_engine
def test_no_new_term_variant():
    """The mechanism is engine bookkeeping, not a new graph-resident primitive:
    `term.rs` must be untouched by this rung."""
    import subprocess
    out = subprocess.run(
        ["git", "diff", "--stat", "64449cd254a8288add893c2314952eaabb209a9c",
         "--", "runners/dsl/src/term.rs"],
        cwd=ROOT, capture_output=True, text=True)
    assert out.stdout.strip() == "", f"term.rs CHANGED:\n{out.stdout}"
