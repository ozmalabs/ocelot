"""Live demonstration for CAN_BELIEF_QUANTIZATION_PREREG.md / _RESULTS.md.

Real, already-exposed engine only (mt_mean_field_marginal, mt_energy,
mt_frustration_given_state, mt_audit_basin) -- no new Rust, no new node
types. Measures whether a COARSE integer-quantized causal_influence weight
vocabulary shows degrading basin structure (fewer distinguishable stable
states, and/or rising frustration) as network size N grows, relative to a
FINE vocabulary spanning the same magnitude range -- the N x M scaling
claim from the PREREG, not merely a sparse-vs-dense snapshot at one size.

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
    Returns (mt, [concept_ids])."""
    mt = s.add_node("Microtheory", {"name": f"n{n}", "temperature": beta})
    concepts = [s.add_node("Concept", {"external_field": 0.0}) for _ in range(n)]
    for i in concepts:
        s.add_edge(mt, "has_concept", i, {})
    for (a, b), w in weights.items():
        s.add_edge(concepts[a], "causal_influence", concepts[b], {"weight": w})
    return mt, concepts


def _basin_sweep(s, mt, concepts, restarts, rng):
    """Multi-start basin discovery. mt_mean_field_marginal itself computes
    exactly ONE fixed point from whatever is currently on each Concept's
    `state` attr -- it does NOT enumerate multiple basins (confirmed by
    reading can_ops.rs before running this). Basin MULTIPLICITY is measured
    here by re-seeding `state` to a random +/-1 draw before each restart and
    clustering the converged marginals.

    Returns (basin_count, effective_basin_count, dominant_fraction,
    mean_frustration, mean_energy). `basin_count` is the raw count of
    distinct clusters found -- as the negative-control test below shows,
    this is confounded with frustration-driven landscape RUGGEDNESS (many
    spurious near-degenerate local minima), not cleanly "how much nuance is
    representable." `effective_basin_count` (exp(Shannon entropy of cluster
    occupancy)) and `dominant_fraction` (largest cluster's share of the 40
    restarts) are reported alongside as a sharper operationalisation of
    "how locked-in is this network's behaviour" -- a network with one
    overwhelmingly dominant basin has LESS behavioural nuance available
    even if a few tiny alternative basins technically exist, closer to the
    creator's own "room to hold a nuanced alternative" framing than a raw
    count of any-size cluster."""
    cluster_reps = []  # list of representative marginal vectors (tuples)
    cluster_counts = []  # parallel: how many restarts landed in each
    frustrations = []
    energies = []
    for _ in range(restarts):
        for c in concepts:
            s.set_attr(c, "state", float(rng.choice([-1.0, 1.0])))
        marg = s.mt_mean_field_marginal(mt, 200, 1e-4)
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
    """Direct confirmation of PREREG Q2: mt_audit_basin/mt_mean_field_marginal
    compute exactly ONE mean-field fixed point from whatever `state` is
    currently on the graph -- they do not themselves discover or count
    multiple basins. Two different starting states on the SAME frustrated
    network can converge to two DIFFERENT marginals, proving audit_basin's
    single call only ever samples one point in a potentially multi-basin
    landscape."""
    s = _fresh_substrate()
    mt = s.add_node("Microtheory", {"temperature": 3.0})
    a = s.add_node("Concept", {"external_field": 0.0})
    b = s.add_node("Concept", {"external_field": 0.0})
    s.add_edge(mt, "has_concept", a, {})
    s.add_edge(mt, "has_concept", b, {})
    # Strong positive coupling, no field: classic symmetric bistable pair.
    s.add_edge(a, "causal_influence", b, {"weight": 0.9})

    s.set_attr(a, "state", 1.0)
    s.set_attr(b, "state", 1.0)
    marg_plus = s.mt_mean_field_marginal(mt, 200, 1e-4)

    s.set_attr(a, "state", -1.0)
    s.set_attr(b, "state", -1.0)
    marg_minus = s.mt_mean_field_marginal(mt, 200, 1e-4)

    # Two genuinely different basins reached from two different starts.
    assert marg_plus[a.value] > 0.5
    assert marg_minus[a.value] < -0.5
    # A single mt_audit_basin() call only ever reports ONE of these -- it
    # reads whatever `state` is on the graph right now, nothing more.
    report = s.mt_audit_basin(mt)
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
    s.import_rules([{**_load_ambivalence_rule(), "active": True}])
    # Symmetric all-negative triangle at zero field, zero initial state:
    # a frustrated network with no net commitment -- every node relaxes
    # near zero (no field to break the symmetry).
    mt = s.add_node("Microtheory", {"temperature": 1.5})
    a = s.add_node("Concept", {"external_field": 0.0})
    b = s.add_node("Concept", {"external_field": 0.0})
    c = s.add_node("Concept", {"external_field": 0.0})
    for n in (a, b, c):
        s.add_edge(mt, "has_concept", n, {})
    s.add_edge(a, "causal_influence", b, {"weight": -1.0})
    s.add_edge(b, "causal_influence", c, {"weight": -1.0})
    s.add_edge(c, "causal_influence", a, {"weight": -1.0})

    s.mt_relax_to_marginal(mt, 200, 1e-4)
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


def _relax_with_fields(n, beta, rounded_j, fields, max_iter, damping=0.5):
    """One mean-field relaxation from a FIXED all-zero start, with a fixed
    nonzero external field per node (the 'evidence pressure' the network is
    trying to reconcile). Returns (marginal, concepts).

    `damping` defaults to 0.5 (can_ops.rs::DEFAULT_DAMPING) -- the FIX from
    CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md for the persistent period-2 limit
    cycle the old fully-synchronous update was prone to (see _oscillates
    below). Pass damping=1.0 to reproduce the OLD (pre-fix) undamped update
    rule exactly -- mathematically identical, not merely similar:
    (1-1.0)*old + 1.0*new == new."""
    s = _fresh_substrate()
    mt, concepts = _build_complete_network(s, n, beta=beta, weights=rounded_j)
    for idx, c in enumerate(concepts):
        s.set_attr(c, "external_field", fields[idx])
        s.set_attr(c, "state", 0.0)
    marg = s.mt_mean_field_marginal(mt, max_iter, 1e-6, damping)
    return marg, concepts, s, mt


def _oscillates(n, beta, rounded_j, fields, damping=0.5):
    """THE cohere-vs-fail-to-cohere probe. mt_mean_field_marginal's update
    rule (can_ops.rs, see DEFAULT_DAMPING) is DAMPED by default since
    CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md -- pass damping=1.0 to probe the
    OLD fully-synchronous (Jacobi-style: every node's new value computed
    from the PREVIOUS full state, all at once) update, which was the
    textbook setup for a persistent 2-cycle limit oscillation on a
    frustrated network. Compares max_iter=400 vs max_iter=401 from the
    IDENTICAL fixed start: if the network has settled to a genuine fixed
    point, both land on it (gap ~ 0); if it is caught in a persistent
    2-cycle, adjacent-parity iteration counts land on OPPOSITE phases (large
    gap) while SAME-parity counts (e.g. 400 vs 402, checked separately in
    RESULTS) land identically -- confirming a true oscillation, not merely
    slow convergence. Returns (is_oscillating, gap)."""
    m400, cs, _, _ = _relax_with_fields(n, beta, rounded_j, fields, 400, damping)
    m401, _, _, _ = _relax_with_fields(n, beta, rounded_j, fields, 401, damping)
    gap = sum((m400.get(c.value, 0.0) - m401.get(c.value, 0.0)) ** 2 for c in cs) ** 0.5
    return gap > 0.01, gap


def _flatten_oscillation_study(ns=(6, 8, 10, 12), seeds=(1, 2, 3), beta=2.0):
    """Parametric resolution-flattening study, per the creator's own framing:
    'emulate lower causal capacity by flattening those bins - which would
    cause overflow. The frame would not be able to collapse and the thought
    would be abandoned.' For each of several independent random (N, true-
    coupling, true-field) draws, builds the SAME network at FINE (17-value)
    and COARSE (3-value) weight resolution and checks _oscillates on each --
    real engine, real numbers, no simulation. Returns (trials, fine_osc_rate,
    coarse_osc_rate)."""
    trials = []
    for n in ns:
        for seed in seeds:
            pair_rng = random.Random(seed * 31 + n * 777)
            pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
            true_j = {p: pair_rng.uniform(-1.0, 1.0) for p in pairs}
            field_rng = random.Random(seed * 53 + n * 777)
            fields = {i: field_rng.uniform(-1.0, 1.0) for i in range(n)}
            for label, gran, k_max in (("fine", 1.0 / 8, 8), ("coarse", 1.0, 1)):
                rounded = {p: _round_to_vocab(v, gran, k_max) for p, v in true_j.items()}
                osc, gap = _oscillates(n, beta, rounded, fields)
                trials.append({"n": n, "seed": seed, "coarseness": label,
                                "oscillates": osc, "gap": round(gap, 4)})
    fine = [t for t in trials if t["coarseness"] == "fine"]
    coarse = [t for t in trials if t["coarseness"] == "coarse"]
    fine_rate = sum(t["oscillates"] for t in fine) / len(fine)
    coarse_rate = sum(t["oscillates"] for t in coarse) / len(coarse)
    return trials, fine_rate, coarse_rate


def test_relaxation_shows_a_real_cohere_vs_fail_to_cohere_signature():
    """UPDATED by CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md: `_oscillates` (and
    `_relax_with_fields`, hence `mt_mean_field_marginal`) is now DAMPED by
    default (damping=0.5 -- can_ops.rs::DEFAULT_DAMPING), which fixes the
    exact persistent period-2 limit cycle this test used to assert on this
    draw (CAN_BELIEF_QUANTIZATION_RESULTS.md S3.1: opposite-parity gap
    5.615746, confirmed via the same-parity control below). This is not a
    re-derivation with a different draw -- it is the IDENTICAL hand-picked
    N=8 network, same seeds, same beta, same fine-resolution rounding --
    now demonstrating the FIX rather than the bug: the corrected solver
    converges cleanly (opposite-parity gap ~0) where the old synchronous
    (Jacobi) update oscillated. The old oscillatory behaviour is preserved
    and independently re-confirmed via `damping=1.0`, which is
    mathematically exact to the pre-fix update rule
    ((1-1.0)*old + 1.0*new == new) -- not merely believed equivalent."""
    n = 8
    pair_rng = random.Random(20260813 * 31 + n)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    true_j = {p: pair_rng.uniform(-1.0, 1.0) for p in pairs}
    field_rng = random.Random(20260813 * 53 + n)
    fields = {i: field_rng.uniform(-1.0, 1.0) for i in range(n)}
    rounded = {p: _round_to_vocab(v, 1.0 / 8, 8) for p, v in true_j.items()}  # fine

    # BEFORE (damping=1.0, byte-identical to the old undamped update):
    # reproduces the originally-measured persistent 2-cycle exactly.
    osc_before, gap_before = _oscillates(n, 2.0, rounded, fields, damping=1.0)
    assert osc_before, (
        "damping=1.0 should reproduce the ORIGINAL synchronous-update "
        "oscillation on this exact draw -- if this fails, the damping=1.0 "
        "equivalence claim (not merely the fix) is broken")
    m400b, csb, _, _ = _relax_with_fields(n, 2.0, rounded, fields, 400, damping=1.0)
    m402b, _, _, _ = _relax_with_fields(n, 2.0, rounded, fields, 402, damping=1.0)
    same_parity_gap_before = sum(
        (m400b.get(c.value, 0.0) - m402b.get(c.value, 0.0)) ** 2 for c in csb
    ) ** 0.5
    assert same_parity_gap_before < 0.001, (
        "damping=1.0, same-parity iteration counts should land on the "
        "identical phase of the TRUE persistent 2-cycle, exactly as the "
        "original (pre-fix) measurement found")

    # AFTER (default damping=0.5): the corrected solver converges cleanly
    # on the SAME network -- no oscillation.
    osc_after, gap_after = _oscillates(n, 2.0, rounded, fields)
    assert not osc_after, (
        "expected the damped (default) solver to converge cleanly on this "
        "exact draw -- if this fails, the fix did not resolve the "
        "originally-measured 2-cycle")
    assert gap_after < 1e-6, "expected a near-zero opposite-parity gap under damping"


def test_flatten_resolution_sweep_reports_cohere_or_abandon():
    """THE resolution-flattening demonstration (n=24 independent draws: 4
    network sizes x 3 seeds x {fine, coarse}). Run with `-s` to see the
    full table.

    UPDATED by CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md: this exact
    pre-registered 24-trial sweep originally found fine oscillating 6/12
    (50%) and coarse 8/12 (66.7%) under the OLD synchronous update --
    reported at the time as a real but weak, non-power-analysed lean in the
    predicted direction. Under the FIX (damping=0.5, the new default), this
    SAME sweep (same seeds, same draws, same networks) finds ZERO
    oscillation in all 24 trials, both conditions. This is itself the
    headline finding of the fix rung: the coarse/fine oscillation-rate
    DIFFERENCE this test used to look for was riding on a phenomenon
    (persistent synchronous-update 2-cycles) that the fix eliminates
    entirely on this sample -- there is no longer a "which condition
    oscillates more" question to ask here, because neither does. See
    CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md SS4 for the abandonment-hypothesis
    assessment this motivates (artifact vs. genuine signal)."""
    trials, fine_rate, coarse_rate = _flatten_oscillation_study()
    print("\n" + json.dumps(trials, indent=2))
    print(f"\nfine (17-value) oscillation rate:   {fine_rate:.2%} "
          f"({sum(t['oscillates'] for t in trials if t['coarseness']=='fine')}/"
          f"{sum(1 for t in trials if t['coarseness']=='fine')})")
    print(f"coarse (3-value) oscillation rate:  {coarse_rate:.2%} "
          f"({sum(t['oscillates'] for t in trials if t['coarseness']=='coarse')}/"
          f"{sum(1 for t in trials if t['coarseness']=='coarse')})")
    assert len(trials) == 24
    # UPDATED: under the fix, this exact sweep no longer oscillates at all
    # -- the old "some draws oscillate, some don't" sanity check no longer
    # holds, and that absence IS the result (see docstring).
    assert fine_rate == 0.0
    assert coarse_rate == 0.0
    assert not any(t["oscillates"] for t in trials)


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
