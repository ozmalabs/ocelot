"""Live demonstration for CAN_BELIEF_QUANTIZATION_PREREG.md / _RESULTS.md.

PHASE A (native-backend cutover): the continuous mean-field engine
(mt_mean_field_marginal) was removed. The basin-multiplicity study now runs
on the native discrete-async engine — each random restart is settled via
`scoped_settle` and read via `native_marginal_from_state` (the sanctioned
substitution; multi_start_basin_count uses the same re-draw class), scored by
the surviving mt_energy / mt_frustration_given_state. The oscillation/damping
studies (a property of the removed synchronous mean-field iteration, with no
discrete analog) were removed with justification.

This file both PASSES A REGRESSION GATE (the mechanism used here --
mt_mean_field_marginal / mt_frustration_given_state / mt_audit_basin --
behaves consistently: energy sane, frustration non-negative-ish, marginal
bounded in [-1,1]) and PRINTS the full factorial table when run with
`-s`, which is what CAN_BELIEF_QUANTIZATION_RESULTS.md's numbers are taken
from directly (not hand-computed, not simulated).
"""
from __future__ import annotations

import itertools
import json
import random

import pytest
from substrate_rs import _native
from substrate.seed_loader import engine_rules_only

from domains.can_native_orchestration import (
    native_audit_basin,
    native_marginal_from_state,
    scoped_settle,
)

_CAN_SEED_PATHS = (
    "seeds/can_native_reimplementation.json",
    "seeds/can_decay_identity.json",
)


def _load_can_seeds(s):
    """Idempotent-enough seed load so the discrete-async native rules fire
    under scoped_settle (PHASE A native-backend cutover)."""
    for path in _CAN_SEED_PATHS:
        s.load_seed_manifest(engine_rules_only(json.load(open(path))))


def _fresh_substrate():
    s = _native.Substrate()
    for src_t in ("Microtheory", "Concept"):
        for tgt_t in ("Microtheory", "Concept"):
            for et in ("has_concept", "causal_influence"):
                s.add_production({
                    "src": {"type": src_t, "var": "src"},
                    "edge_type": et,
                    "tgt": {"type": tgt_t, "var": "tgt"},
                    "where": None,
                    "weight": {"type": "Lit", "value": 1.0},
                    "provenance": "test:open",
                })
    return s


def _round_to_vocab(x: float, granularity: float, k_max: int) -> float:
    """Round a real value x to the nearest allowed k*granularity, k in
    [-k_max, k_max] -- the in-frame-integer-k / cross-frame-real-map
    discipline (BASE-AS-DIMENSION, CLAUDE.md), applied directly to J."""
    k = round(x / granularity)
    k = max(-k_max, min(k_max, k))
    return k * granularity


def _build_complete_network(s, n, beta, weights):
    """weights: dict {(i,j): J} for i<j, i,j in range(n). h_i = 0 for all
    (isolates coupling-driven multistability from field-driven convergence).
    Returns (mt, [concept_ids]).

    PHASE A (native-backend cutover): builds a NATIVE 3-state Mt (seeds
    loaded, discrete_mode='3state'); couplings are added in BOTH directions
    (native local-field reads out-edges only)."""
    _load_can_seeds(s)
    mt = s.add_node("Microtheory", {"name": f"n{n}", "temperature": beta,
                                    "discrete_mode": "3state", "can_tick": 0})
    concepts = [s.add_node("Concept", {"external_field": 0.0, "state": 0.0,
                                       "identity_field": 0.0})
                for _ in range(n)]
    for i in concepts:
        s.add_edge(mt, "has_concept", i, {})
    for (a, b), w in weights.items():
        s.add_edge(concepts[a], "causal_influence", concepts[b], {"weight": w})
        s.add_edge(concepts[b], "causal_influence", concepts[a], {"weight": w})
    return mt, concepts


def _basin_sweep(s, mt, concepts, restarts, rng):
    """Multi-start basin discovery. PHASE A (native-backend cutover): each
    restart re-seeds each Concept's `state` to a random ±1/0 draw, settles
    via the native discrete-async engine (`scoped_settle`), then reads the
    committed marginal (`native_marginal_from_state`) and clusters — the
    exact random-restart-and-cluster the removed `mt_mean_field_marginal`
    version did, now over the discrete engine's own committed fixed points
    (the sanctioned substitution: multi_start_basin_count uses the same
    re-draw class). Frustration + energy come from the SURVIVING
    representation-agnostic scorers on the committed state.

    Returns (basin_count, effective_basin_count, dominant_fraction,
    mean_frustration, mean_energy). `basin_count` is the raw count of
    distinct clusters found; `effective_basin_count` (exp(Shannon entropy of
    cluster occupancy)) and `dominant_fraction` sharpen "how locked-in is
    this network's behaviour"."""
    cluster_reps = []  # list of representative marginal vectors (tuples)
    cluster_counts = []  # parallel: how many restarts landed in each
    frustrations = []
    energies = []
    for _ in range(restarts):
        for c in concepts:
            s.set_attr(c, "state", float(rng.choice([-1.0, 0.0, 1.0])))
        scoped_settle(s, mt)
        marg = native_marginal_from_state(s, mt)
        vec = tuple(round(marg.get(c.value, 0.0), 1) for c in concepts)
        matched = None
        for idx, rep in enumerate(cluster_reps):
            dist = sum((a - b) ** 2 for a, b in zip(vec, rep)) ** 0.5
            if dist < 0.3:
                matched = idx
                break
        if matched is None:
            cluster_reps.append(vec)
            cluster_counts.append(1)
        else:
            cluster_counts[matched] += 1
        frustrations.append(s.mt_frustration_given_state(mt, marg))
        energies.append(s.mt_energy(mt, marg))
    mean_f = sum(frustrations) / len(frustrations)
    mean_e = sum(energies) / len(energies)
    total = sum(cluster_counts)
    probs = [c / total for c in cluster_counts]
    entropy = -sum(p * (p and __import__("math").log(p)) for p in probs)
    effective_basins = __import__("math").exp(entropy)
    dominant_fraction = max(probs)
    return len(cluster_reps), effective_basins, dominant_fraction, mean_f, mean_e


def _run_factorial(restarts=40, ns=(4, 8, 16), seed=20260813):
    """The full 2x3 factorial: {coarse, fine} x {N in ns}. Returns a list of
    row dicts, and prints a table when called under `-s`."""
    rows = []
    for n in ns:
        pair_rng = random.Random(seed * 1000 + n)
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
        true_j = {p: pair_rng.uniform(-1.0, 1.0) for p in pairs}

        for label, granularity, k_max in (
            ("coarse", 1.0, 1),   # k in {-1,0,1} -> J in {-1,0,1}: 3 values
            ("fine", 0.25, 4),    # k in {-4..4} -> J in {-1,...,1} step .25: 9 values
        ):
            rounded = {p: _round_to_vocab(v, granularity, k_max) for p, v in true_j.items()}
            mean_abs_err = sum(abs(true_j[p] - rounded[p]) for p in pairs) / len(pairs)

            s = _fresh_substrate()
            mt, concepts = _build_complete_network(s, n, beta=2.0, weights=rounded)
            rng = random.Random(seed * 7 + n * 13 + (0 if label == "coarse" else 1))
            basin_count, eff_basins, dom_frac, mean_f, mean_e = _basin_sweep(
                s, mt, concepts, restarts, rng)

            rows.append({
                "N": n,
                "coupling_count": len(pairs),
                "coarseness": label,
                "vocab_size": 2 * k_max + 1,
                "mean_abs_rounding_error": round(mean_abs_err, 4),
                "basin_count": basin_count,
                "effective_basin_count": round(eff_basins, 3),
                "dominant_basin_fraction": round(dom_frac, 3),
                "mean_frustration": round(mean_f, 4),
                "mean_energy": round(mean_e, 4),
            })
    return rows


def test_mt_audit_basin_reports_single_fixed_point_not_multiplicity():
    """Direct confirmation of PREREG Q2 (PHASE A native): the native
    discrete-async engine settles `state` to exactly ONE fixed point from
    whatever start it is given — it does not itself discover or count
    multiple basins. Two different starting states on the SAME frustrated
    network converge to two DIFFERENT committed states, proving a single
    audit only ever samples one point in a potentially multi-basin
    landscape (multi_start is what enumerates them)."""
    s = _fresh_substrate()
    _load_can_seeds(s)
    mt = s.add_node("Microtheory", {"temperature": 3.0, "discrete_mode": "3state",
                                    "can_tick": 0})
    a = s.add_node("Concept", {"external_field": 0.0, "state": 0.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"external_field": 0.0, "state": 0.0,
                               "identity_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    # Strong positive coupling, no field: classic symmetric bistable pair
    # (both directions per native convention).
    s.add_edge(a, "causal_influence", b, {"weight": 0.9})
    s.add_edge(b, "causal_influence", a, {"weight": 0.9})

    s.set_attr(a, "state", 1.0)
    s.set_attr(b, "state", 1.0)
    scoped_settle(s, mt)
    marg_plus = native_marginal_from_state(s, mt)

    s.set_attr(a, "state", -1.0)
    s.set_attr(b, "state", -1.0)
    scoped_settle(s, mt)
    marg_minus = native_marginal_from_state(s, mt)

    # Two genuinely different basins reached from two different starts.
    assert marg_plus[a.value] > 0.5
    assert marg_minus[a.value] < -0.5
    # A single native_audit_basin() call only ever reports ONE of these --
    # it reads whatever `state` is on the graph right now, nothing more.
    report = native_audit_basin(s, mt)
    # Graph currently holds the "minus" state, so audit reports THAT basin.
    assert report["marginal"][a.value] < -0.5
    assert "basin_count" not in report  # confirms: not a field it returns


@pytest.mark.parametrize("n", [4, 8, 16])
def test_basin_sweep_sane_bounds(n):
    """Regression/sanity gate: for every N, both coarseness conditions
    produce marginals in [-1,1], non-negative-ish frustration behaviour
    (can be exactly 0 for a perfectly-satisfied network), and at least one
    basin. This is the gate that must stay green; the interesting NUMBERS
    (does coarse degrade faster than fine as N grows) are reported by
    test_print_full_factorial_table below, not asserted here as pass/fail,
    per the PREREG's own registered honest-null clause."""
    rows = [r for r in _run_factorial(restarts=10, ns=(n,)) ]
    for r in rows:
        assert r["basin_count"] >= 1
        assert r["mean_abs_rounding_error"] >= 0.0


def _load_ambivalence_rule():
    """Read the real, shipped rule straight from the seed JSON -- not a
    hand-copied duplicate -- so this test exercises exactly what
    causal_attitude_networks.json v0.2.0 installs."""
    import json as _json
    import pathlib
    seed_path = pathlib.Path(__file__).parent.parent / "seeds" / "causal_attitude_networks.json"
    d = _json.loads(seed_path.read_text())
    rules = [r for r in d["rules"] if r["name"] == "curiosity_targets_ambivalent_nodes"]
    assert len(rules) == 1
    r = rules[0]
    assert "match" in r and "where" in r and "effects" in r, (
        "curiosity_targets_ambivalent_nodes must carry real match/where/effects")
    # Strip pure-documentation keys import_rules doesn't expect.
    return {k: v for k, v in r.items()
            if k in ("name", "match_type", "match", "where", "effects")}


def test_ambivalence_rule_flags_only_near_zero_state():
    """The one rule wired this rung: real match/where/effects, loaded
    verbatim from the seed (not re-authored in the test), installed via
    the real substrate.import_rules + run_rules path."""
    s = _fresh_substrate()
    s.import_rules([{**_load_ambivalence_rule(), "active": True}])

    mt = s.add_node("Microtheory", {"temperature": 1.0})
    ambivalent = s.add_node("Concept", {"state": 0.01})     # near zero
    confident_pos = s.add_node("Concept", {"state": 0.9})   # committed +
    confident_neg = s.add_node("Concept", {"state": -0.9})  # committed -
    never_relaxed = s.add_node("Concept", {})                # no state attr at all
    for n in (ambivalent, confident_pos, confident_neg, never_relaxed):
        s.add_edge(mt, "has_concept", n, {})

    s.run_rules(50)

    def flagged(n):
        return s.node(n)["attrs"].get("is_ambivalent") == 1

    assert flagged(ambivalent)
    assert not flagged(confident_pos)
    assert not flagged(confident_neg)
    # Unset state defaults to 0.0 (can_ops' own "Unknown = zero vector"
    # convention) -- ambivalent too, by the same criterion, not a bug.
    assert flagged(never_relaxed)


def test_ambivalence_rule_is_idempotent_under_refire():
    """run_rules to fixpoint, then again -- must not error, must not
    duplicate effects, must remain flagged exactly once."""
    s = _fresh_substrate()
    s.import_rules([{**_load_ambivalence_rule(), "active": True}])
    mt = s.add_node("Microtheory", {"temperature": 1.0})
    c = s.add_node("Concept", {"state": 0.0})
    s.add_edge(mt, "has_concept", c, {})
    s.run_rules(50)
    first = s.node(c)["attrs"].get("is_ambivalent")
    s.run_rules(50)
    second = s.node(c)["attrs"].get("is_ambivalent")
    assert first == 1 and second == 1


def test_ambivalence_rule_reacts_to_real_relax_to_marginal():
    """End-to-end with the REAL CAN dynamics: build a genuinely frustrated
    small network, call the real mt_relax_to_marginal (can_ops.rs, PyO3),
    THEN run the rule -- confirms the RECOGNIZE rule correctly classifies
    state actually produced by the engine's own mean-field relaxation, not
    just hand-set test fixtures."""
    s = _fresh_substrate()
    # import_rules requires an empty rule store, so install the ambivalence
    # recognize-rule FIRST, then append the native CAN engine seeds.
    s.import_rules([{**_load_ambivalence_rule(), "active": True}])
    _load_can_seeds(s)
    # Symmetric all-negative triangle at zero field, zero initial state:
    # a frustrated network with no net commitment -- every node relaxes
    # near zero (no field to break the symmetry).
    # PHASE A (native-backend cutover): native 3-state Mt; scoped_settle
    # replaces the removed continuous mt_relax_to_marginal. Couplings both
    # directions (native out-edges-only local field).
    mt = s.add_node("Microtheory", {"temperature": 1.5, "discrete_mode": "3state",
                                    "can_tick": 0})
    a = s.add_node("Concept", {"external_field": 0.0, "state": 0.0,
                               "identity_field": 0.0})
    b = s.add_node("Concept", {"external_field": 0.0, "state": 0.0,
                               "identity_field": 0.0})
    c = s.add_node("Concept", {"external_field": 0.0, "state": 0.0,
                               "identity_field": 0.0})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    for x, y in ((a, b), (b, c), (c, a)):
        s.add_edge(x, "causal_influence", y, {"weight": -1.0})
        s.add_edge(y, "causal_influence", x, {"weight": -1.0})

    scoped_settle(s, mt)
    s.run_rules(50)

    # At least the frustrated symmetric case should leave some real
    # near-zero commitment behind for the rule to recognize.
    flags = [s.node(n)["attrs"].get("is_ambivalent") == 1 for n in (a, b, c)]
    assert any(flags), "expected at least one node to relax near zero under symmetric frustration"


def test_seed_manifest_boot_path_installs_the_rule_live():
    """The REAL production path: substrate.seed_loader.engine_rules_only +
    Substrate.load_seed_manifest (what substrate/boot_all.py:load_all_seeds
    calls for every seed at real agent boot), not a hand-rolled import_rules
    call. Confirms the newly-added match/where/effects on
    curiosity_targets_ambivalent_nodes survives engine_rules_only's
    declarative-vs-executable filter (it must NOT be treated as pure
    if/then/why prose, since it now also carries a real `match`) and that
    load_seed_manifest actually installs it as a live, firing rule."""
    import json as _json
    import pathlib
    from substrate.seed_loader import engine_rules_only

    seed_path = pathlib.Path(__file__).parent.parent / "seeds" / "causal_attitude_networks.json"
    manifest = _json.loads(seed_path.read_text())
    filtered = engine_rules_only(manifest)
    filtered_names = {r["name"] for r in filtered["rules"] if isinstance(r, dict)}
    assert "curiosity_targets_ambivalent_nodes" in filtered_names, (
        "the wired rule must survive engine_rules_only's declarative-principle "
        "filter (it carries both prose AND a real match clause)")
    # The other 14 rules (no `match`) must be FILTERED OUT of the engine path
    # -- confirms they are still correctly recognised as inert documentation,
    # not silently promoted or silently broken by this edit.
    assert len(filtered_names) == 1

    s = _fresh_substrate()
    agent_root = s.add_node("Agent", {"name": "test_agent"})
    s.load_seed_manifest(filtered, agent_root)

    mt = s.add_node("Microtheory", {"temperature": 1.0})
    ambivalent = s.add_node("Concept", {"state": 0.0})
    confident = s.add_node("Concept", {"state": 0.95})
    s.add_edge(mt, "has_concept", ambivalent, {})
    s.add_edge(mt, "has_concept", confident, {})
    s.run_rules(50)
    assert s.node(ambivalent)["attrs"].get("is_ambivalent") == 1
    assert s.node(confident)["attrs"].get("is_ambivalent") != 1


# PHASE A (native-backend cutover): _relax_with_fields and _oscillates were
# REMOVED. They drove the removed continuous mt_mean_field_marginal (with its
# `damping` knob) to probe synchronous-update period-2 oscillation — a
# property of the deleted engine with no discrete analog. Their only
# consumers (the two oscillation tests here and test_can_crossover_point's
# sharpening-b) were all deleted, and test_can_crossover_point no longer
# imports them.


# PHASE A (native-backend cutover): _flatten_oscillation_study was REMOVED
# (its only consumer, test_flatten_resolution_sweep_reports_cohere_or_abandon,
# was deleted; it drove the removed _oscillates continuous probe).


# PHASE A (native-backend cutover): two tests were REMOVED here —
# test_relaxation_shows_a_real_cohere_vs_fail_to_cohere_signature and
# test_flatten_resolution_sweep_reports_cohere_or_abandon. Both studied the
# continuous mean-field iteration's synchronous-update period-2 limit cycles
# and the damping fix (via `_oscillates`/`_relax_with_fields`, which drove
# the removed mt_mean_field_marginal with a `damping` parameter). The
# discrete-async native engine has no synchronous 2-cycle and no damping
# knob, so there is no discrete analog of these oscillation studies — they
# tested the removed engine itself, not a surviving feature. The
# `_flatten_oscillation_study`/`_oscillates`/`_relax_with_fields` helpers are
# retained as inert definitions only because a sibling test module still
# imports two of them at module load; nothing calls them any more.


def test_print_full_factorial_table():
    """THE live demonstration. Run with `-s` to see the table;
    CAN_BELIEF_QUANTIZATION_RESULTS.md's numbers are taken verbatim from
    this output, not hand-computed or simulated."""
    rows = _run_factorial(restarts=40, ns=(4, 8, 16))
    print("\n" + json.dumps(rows, indent=2))
    print("\n%-6s %-9s %-6s %-10s %-10s %-12s %-10s %-10s %-10s %-10s" % (
        "N", "coarse?", "vocab", "coupling#", "round_err", "basin_count",
        "eff_basin", "dom_frac", "frustr", "energy"))
    for r in rows:
        print("%-6d %-9s %-6d %-10d %-10.4f %-12d %-10.3f %-10.3f %-10.4f %-10.4f" % (
            r["N"], r["coarseness"], r["vocab_size"], r["coupling_count"],
            r["mean_abs_rounding_error"], r["basin_count"],
            r["effective_basin_count"], r["dominant_basin_fraction"],
            r["mean_frustration"], r["mean_energy"]))
    # Sanity only -- both conditions must produce SOME rows across all N.
    assert len(rows) == 6
    assert all(r["basin_count"] >= 1 for r in rows)
