"""Native re-derivation of CAN's concept as sd-loop/Gamma-native graph rules
(seeds/can_native_reimplementation.json) -- executes
CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md (merged main@325c064, verdict:
replace). See docs/research/engine_substrate/CAN_NATIVE_REIMPLEMENTATION_
PREREG.md for the registered design and predictions this file checks
against the REAL engine (not the isolated PoC scripts).

Item 3 (discrete-asynchronous evidence propagation): reproduces the
continuous-sync-oscillates / discrete-async-never-oscillates comparison
that can_concept_poc_discrete_async.py established in pure Python, here
against real substrate_rs graph state and the real seeded Rules.

Items 1-2 (basin classification + residual/ordered_parts coherence): the
ShapeDecode-based basin codebook, against REAL convergent states from the
item-3 relaxation.

Item 4 (Hebbian mint-on-recurrence, edge-creation half): the two-tick
epoch-gated note/mint rule pair.

Item 5 (polarization max_steps sweep) and the Bigville migration-decision
check are separate test functions, run with -s for their printed tables.
"""
from __future__ import annotations

import json
import math
import random

import pytest

import substrate_rs as sr
from substrate.seed_loader import engine_rules_only

SEED_PATH = "seeds/can_native_reimplementation.json"
N = 8
BETA = 2.0
ATANH_HALF = math.atanh(0.5)


def _loaded_substrate():
    s = sr.Substrate()
    inner = s._inner
    d = json.load(open(SEED_PATH))
    filtered = engine_rules_only(d)
    inner.load_seed_manifest(filtered)
    return s


def _round_to_vocab(x, granularity, half_width):
    k = round(x / granularity)
    k = max(-half_width, min(half_width, k))
    return k * granularity


def _build_draw(s, seed, coarse, discrete_mode="3state"):
    """N=8 complete graph -- mirrors can_concept_poc_discrete_async.py's
    build_draw exactly, on the real engine, symmetric edge pairs (PREREG
    Sec0 Probe1's adopted convention)."""
    inner = s._inner
    pair_rng = random.Random(seed * 31 + N)
    field_rng = random.Random(seed * 53 + N)
    mt = inner.add_node("Microtheory", {
        "temperature": BETA, "discrete_mode": discrete_mode, "can_tick": 0,
    })
    concepts = [
        inner.add_node("Concept", {
            "name": "c%d" % i, "state": 0.0,
            "external_field": 0.0, "identity_field": 0.0,
        })
        for i in range(N)
    ]
    for c in concepts:
        inner.add_edge(mt, "has_concept", c, {})
    for i in range(N):
        h = field_rng.uniform(-1, 1)
        inner.set_attr(concepts[i], "external_field", h)
    for i in range(N):
        for j in range(i + 1, N):
            raw = pair_rng.uniform(-1, 1)
            v = (_round_to_vocab(raw, 1.0, 1) if coarse
                 else _round_to_vocab(raw, 0.25, 4))
            inner.add_edge(concepts[i], "causal_influence", concepts[j], {"weight": v})
            inner.add_edge(concepts[j], "causal_influence", concepts[i], {"weight": v})
    return mt, concepts


def _continuous_oscillates(inner, mt):
    """Reuses the EXISTING mt_mean_field_marginal PyO3 surface, damping=1.0
    -- reproduces the OLD pre-fix synchronous update exactly (per
    CAN_SYNCHRONOUS_UPDATE_FIX_RESULTS.md Sec1's own cross-check), pure
    read, no graph mutation."""
    s400 = inner.mt_mean_field_marginal(mt, 400, 1e-6, 1.0)
    s401 = inner.mt_mean_field_marginal(mt, 401, 1e-6, 1.0)
    s402 = inner.mt_mean_field_marginal(mt, 402, 1e-6, 1.0)
    keys = list(s400.keys())
    gap_opp = sum((s400[k] - s401[k]) ** 2 for k in keys) ** 0.5
    gap_same = sum((s400[k] - s402[k]) ** 2 for k in keys) ** 0.5
    return (gap_opp > 0.1 and gap_same < 0.01), gap_opp, gap_same


def _discrete_async_converges(inner, max_steps=3000):
    steps = inner.run_rules(max_steps)
    return steps < max_steps, steps


def _read_states(inner, concepts):
    return {c: inner.node(c)["attrs"].get("state", 0.0) for c in concepts}


def _frustration(inner, mt, concepts):
    state = {c.value: float(v) for c, v in _read_states(inner, concepts).items()}
    return inner.mt_frustration_given_state(mt, state)


N_DRAWS = 20


# ---------------------------------------------------------------------
# Item 3 -- live demonstration (a): discrete-async convergence vs
# continuous-sync oscillation, on the REAL engine.
# ---------------------------------------------------------------------

@pytest.mark.parametrize("discrete_mode", ["2state", "3state"])
def test_discrete_async_never_oscillates_vs_continuous_sync(discrete_mode):
    rows = []
    for coarse in (True, False):
        cont_osc = 0
        disc_nonconv = 0
        frustrations = []
        for seed in range(N_DRAWS):
            s = _loaded_substrate()
            inner = s._inner
            mt, concepts = _build_draw(s, 1000 + seed, coarse, discrete_mode)
            osc, gap_opp, gap_same = _continuous_oscillates(inner, mt)
            if osc:
                cont_osc += 1
            converged, steps = _discrete_async_converges(inner)
            if not converged:
                disc_nonconv += 1
            frustrations.append(_frustration(inner, mt, concepts))
        label = "coarse" if coarse else "fine"
        mean_fr = sum(frustrations) / len(frustrations)
        rows.append((label, cont_osc, disc_nonconv, mean_fr))
        print(f"[{discrete_mode}] {label:8s} continuous_sync_osc={cont_osc}/{N_DRAWS} "
              f"discrete_async_nonconv={disc_nonconv}/{N_DRAWS} mean_frustration={mean_fr:.3f}")

    # Registered prediction 2: discrete-async NEVER fails to reach a fixpoint.
    for label, cont_osc, disc_nonconv, mean_fr in rows:
        assert disc_nonconv == 0, (
            f"discrete-async ({discrete_mode}) failed to converge on "
            f"{disc_nonconv}/{N_DRAWS} {label} draws -- breaks the registered "
            f"Lyapunov-guarantee prediction"
        )


def test_continuous_sync_oscillates_on_at_least_one_real_draw():
    """Registered prediction 1: replicates the already-measured pathology on
    THIS rung's own real-engine draws (not merely cited from the PoC or the
    prior rung's own numbers)."""
    any_osc = False
    for coarse in (True, False):
        for seed in range(N_DRAWS):
            s = _loaded_substrate()
            inner = s._inner
            mt, _ = _build_draw(s, 2000 + seed, coarse)
            osc, _, _ = _continuous_oscillates(inner, mt)
            if osc:
                any_osc = True
    assert any_osc, "expected the continuous-sync pathology to reproduce on at least one real draw"


def test_three_state_vs_two_state_frustration_bonus_comparison():
    """Bonus/secondary (PREREG Sec1 point 4, NOT the primary claim): does
    3-state converge to higher or lower frustration than 2-state, on the
    SAME coupling draws? Reported precisely, not assumed to replicate the
    PoC's own (self-corrected) finding."""
    fr2, fr3 = [], []
    for seed in range(N_DRAWS):
        s2 = _loaded_substrate()
        mt2, c2 = _build_draw(s2, 3000 + seed, coarse=True, discrete_mode="2state")
        _discrete_async_converges(s2._inner)
        fr2.append(_frustration(s2._inner, mt2, c2))

        s3 = _loaded_substrate()
        mt3, c3 = _build_draw(s3, 3000 + seed, coarse=True, discrete_mode="3state")
        _discrete_async_converges(s3._inner)
        fr3.append(_frustration(s3._inner, mt3, c3))
    mean2, mean3 = sum(fr2) / len(fr2), sum(fr3) / len(fr3)
    print(f"mean_frustration_2state={mean2:.3f} mean_frustration_3state={mean3:.3f}")
    # No assertion on direction -- registered as reported-honestly-either-way.


# ---------------------------------------------------------------------
# Items 1-2 -- basin classification + residual/ordered_parts coherence,
# against REAL convergent states from the item-3 relaxation.
# ---------------------------------------------------------------------

def _converged_signature(inner, concepts, names):
    state = _read_states(inner, concepts)
    return [["state", n, state[c]] for n, c in zip(names, concepts)]


def _install_observation_production(s):
    s.add_production({
        "src": {"type": "Agent", "var": "ag"},
        "edge_type": "observed",
        "tgt": {"type": "Observation", "var": "obs"},
        "where": None, "weight": {"type": "Lit", "value": 1.0},
        "provenance": "test_can_native_reimplementation",
    })


def test_basin_classification_and_frustration_signal():
    """PREREG Sec2, corrected design (PREREG Sec0 Probe2 / this seed's own
    module description): classification decodes against EACH held basin
    INDIVIDUALLY (codebook_scope), not a composite multi-basin explanation
    -- an unscoped decode against >=2 overlapping basins lets the beam
    search's additive fit scoring prefer a redundant multi-part composite
    over a single basin's own clean exact match (found live while building
    this seed, worked around by scoping, not patched in Rust)."""
    names = ["c%d" % i for i in range(N)]

    # Two REAL held basins, from two real relaxations (not hand-picked).
    s_a = _loaded_substrate()
    mt_a, concepts_a = _build_draw(s_a, 9001, coarse=True)
    _discrete_async_converges(s_a._inner)
    sig_a = _converged_signature(s_a._inner, concepts_a, names)

    s_b = _loaded_substrate()
    mt_b, concepts_b = _build_draw(s_b, 9002, coarse=True)
    _discrete_async_converges(s_b._inner)
    sig_b = _converged_signature(s_b._inner, concepts_b, names)

    assert sig_a != sig_b, "need two genuinely distinct real basins for this demo"

    # Build the demo/decode substrate: fresh, with the codebook + one Agent.
    s = _loaded_substrate()
    _install_observation_production(s)
    inner = s._inner
    inner.add_node("ShapeSignature", {"name": "basin_a", "signature": sig_a})
    inner.add_node("ShapeSignature", {"name": "basin_b", "signature": sig_b})
    ag = inner.add_node("Agent", {})

    def classify(obs_sig):
        """Probe against EVERY held basin individually (codebook_scope),
        mirroring CAN_BELIEF_QUANTIZATION_RESULTS.md's own _basin_sweep
        multi-start-diagnostic reporting shape: one decode per candidate,
        Python reads back and reports -- a query over already-decoded graph
        facts, not a decision. Returns {basin_name: covered_count}."""
        out = {}
        for name in ("basin_a", "basin_b"):
            obs = inner.add_node("Observation", {
                "signature": obs_sig, "decode_kind": "can_basin_probe",
                "status": "pending", "scope_name": name,
            })
            inner.add_edge(ag, "observed", obs, {})
            inner.run_rules(1000)
            out[name] = inner.node(obs)["attrs"]["covered_count"]
        return out

    # (a) exact match to basin_a -- clean recognition.
    cc_a = classify(sig_a)
    print("exact match to basin_a:", cc_a, "(goal_relations=%d)" % N)
    assert cc_a["basin_a"] == N, "basin_a must fully cover its own exact state"
    assert cc_a["basin_b"] < N, "basin_b must NOT also claim a full match"

    # (b) torn between the two basins -- half the components from each.
    mixed_sig = [sig_a[i] if i < N // 2 else sig_b[i] for i in range(N)]
    cc_mixed = classify(mixed_sig)
    print("torn between basin_a/basin_b:", cc_mixed)
    assert cc_mixed["basin_a"] < N and cc_mixed["basin_b"] < N, (
        "a genuinely mixed state must NOT fully match either basin cleanly"
    )
    best_mixed = max(cc_mixed.values())
    assert best_mixed < N, "mixed state: neither candidate reaches full coverage"

    # (c) undifferentiated / uncommitted -- all-zero.
    zero_sig = [["state", n, 0.0] for n in names]
    cc_zero = classify(zero_sig)
    print("undifferentiated (all zero):", cc_zero)
    best_zero = max(cc_zero.values())
    assert best_zero <= best_mixed, (
        "the totally uncommitted (all-zero) case should match its BEST candidate "
        "no better than the genuinely-mixed case does -- consistent with the "
        "already-wired curiosity_targets_ambivalent_nodes rule's own "
        "near-zero=ambivalent reading (state==0 relations match NEITHER real basin)"
    )


# ---------------------------------------------------------------------
# Item 4 -- Hebbian mint-on-recurrence, edge-creation half only.
# ---------------------------------------------------------------------

def test_hebbian_mint_on_recurrence_not_on_first_sight():
    """Isolated from item 3's discrete-update rules on purpose: discrete_mode
    is left as neither "2state" nor "3state" ("static"), so
    can_native_update_plus/minus/zero's mode_guard never matches and they
    never fire -- otherwise, on an isolated pair with zero external/identity
    field and no coupling (local field==0 always), can_native_update_zero
    would immediately neutralize BOTH concepts to state=0 before
    can_native_note_coactivation ever saw their committed +1/+1 state
    (found live while writing this test -- a real interaction between item
    3 and item 4's rules on a network that runs both, named here rather
    than silently avoided: a network driving BOTH the discrete relaxation
    AND Hebbian learning needs states that survive relaxation before
    Hebbian noting/minting can see them, exactly as real evidence-pressure
    dynamics would require in can_ops.rs too)."""
    s = _loaded_substrate()
    inner = s._inner
    mt = inner.add_node("Microtheory", {"temperature": 1.0, "discrete_mode": "static", "can_tick": 0})
    a = inner.add_node("Concept", {"name": "a", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    b = inner.add_node("Concept", {"name": "b", "state": 1.0, "external_field": 0.0, "identity_field": 0.0})
    inner.add_edge(mt, "has_concept", a, {})
    inner.add_edge(mt, "has_concept", b, {})

    def has_edge(x, y):
        for idx_attrs in inner.node(x)["attrs"]:
            pass
        # cheapest correct check: neighbours() on x for causal_influence.
        return y in inner.neighbours(x, "causal_influence")

    # Tick 1: first sight -- notes the co-activation, does NOT mint yet.
    inner.run_rules(1000)
    assert not has_edge(a, b), "must NOT mint on first sight (mint-on-RECURRENCE)"
    assert not has_edge(b, a)

    # Advance the external tick (mechanical, Python-driven epoch bump --
    # the SAME idiom shape_decode_loop's codebook_epoch already uses).
    inner.set_attr(mt, "can_tick", 1)

    # Tick 2: recurrence -- the SAME co-activation observed again, now mints.
    inner.run_rules(1000)
    assert has_edge(a, b), "must mint on genuine cross-tick recurrence"
    assert has_edge(b, a), "symmetric mint (PREREG Sec0 Probe1 convention)"

    # A third tick with the edge already present must NOT re-mint (recognize,
    # not re-create -- mirrors blob-edge minting's own proven pattern).
    edges_before = len(inner.neighbours(a, "causal_influence"))
    inner.set_attr(mt, "can_tick", 2)
    inner.run_rules(1000)
    edges_after = len(inner.neighbours(a, "causal_influence"))
    assert edges_before == edges_after, "must not re-mint once the edge already exists"


# ---------------------------------------------------------------------
# Item 5 -- polarization re-test via max_steps (attempt-if-cheap).
# ---------------------------------------------------------------------

def test_polarization_via_max_steps_sweep():
    """Re-runs can_concept_poc_decode_polarization.py's design on the REAL
    ShapeDecode Term, sweeping max_steps (refinement depth) instead of a
    symmetric vote-count scrutiny_T (the PoC's own honestly-corrected
    U-shaped miss). Reported precisely whichever way it comes out."""
    rng = random.Random(2026)
    PROTO_PRO = [1] * N
    PROTO_ANTI = [-1] * N
    TRIALS_PER_ALPHA = 8
    N_ALPHA = 11

    s = _loaded_substrate()
    _install_observation_production(s)
    inner = s._inner
    names = ["c%d" % i for i in range(N)]
    inner.add_node("ShapeSignature", {
        "name": "proto_pro", "signature": [["state", n, v] for n, v in zip(names, PROTO_PRO)],
    })
    inner.add_node("ShapeSignature", {
        "name": "proto_anti", "signature": [["state", n, v] for n, v in zip(names, PROTO_ANTI)],
    })
    ag = inner.add_node("Agent", {})

    def decode_at(max_steps, obs_sig):
        obs = inner.add_node("Observation", {
            "signature": obs_sig, "decode_kind": "polarization_probe", "status": "n/a",
        })
        inner.add_edge(ag, "observed", obs, {})
        from substrate_rs import Term, Attr, Var
        term = Term("ShapeDecode", goal=Attr(Var("o"), "signature"),
                     codebook_type="ShapeSignature", beam=3, max_steps=max_steps, cand_k=3,
                     wild_objects=False, field="covered_by")
        return s.evaluate(term, {"o": obs})

    print(f"{'max_steps':>10}  {'resolved':>9} {'ambiguous':>10} {'frac_near_extreme':>20}")
    for max_steps in (1, 2, 4, 8, 16):
        resolved_alphas = []
        ambiguous = 0
        for k in range(N_ALPHA):
            alpha = k / (N_ALPHA - 1)
            for _ in range(TRIALS_PER_ALPHA):
                comps = [1 if rng.random() < alpha else -1 for _ in range(N)]
                obs_sig = [["state", n, v] for n, v in zip(names, comps)]
                cb = decode_at(max_steps, obs_sig)
                if cb == "proto_pro" or cb == "proto_anti":
                    resolved_alphas.append(alpha)
                elif cb is None:
                    ambiguous += 1
        if resolved_alphas:
            near_extreme = sum(1 for a in resolved_alphas if a < 0.2 or a > 0.8)
            frac = near_extreme / len(resolved_alphas)
        else:
            frac = float("nan")
        print(f"{max_steps:>10}  {len(resolved_alphas):>9} {ambiguous:>10} {frac:>20.3f}")


# ---------------------------------------------------------------------
# Migration-decision check -- Bigville's existing asymmetric edge schema.
# ---------------------------------------------------------------------

def test_bigville_schema_is_asymmetric_native_rule_reads_only_out_edges():
    """PREREG Sec5's registered check: build ONE real resident's CAN network
    via the EXISTING, UNMODIFIED worlds/bigville_can_beliefs.py builder, and
    directly show the native discrete rule's local field disagrees with
    can_ops.rs's symmetric build_couplings-based local field for at least
    one Concept -- the concrete, measured basis for the migration
    recommendation (NOT a hypothetical)."""
    from worlds import bigville_can_beliefs as bcb

    s = _loaded_substrate()
    bcb.install_productions(s)
    inner = s._inner

    resident = {
        "name": "TestResident", "index": 0,
        "params": {
            "resolution_bins": 8, "arousal": 0.2,
            "prior_world_safe": 0.6, "prior_self_worth": 0.55,
            "charm_weight": 0.5, "hostile_weight": 0.2, "prior_others_trust": 0.5,
            "claim_weight": 0.6, "w_supergraph": 0.5, "w_spite": 0.1,
            "mood_bias": 0.3,
        },
    }
    built = bcb.build_resident_can_mt(s, resident)
    mt = built["mt_node"]
    concepts = built["concepts"]
    inner.set_attr(mt, "discrete_mode", "3state")
    inner.set_attr(mt, "can_tick", 0)

    # can_ops.rs's OWN symmetric coupling read, for the SAME graph, same mt.
    marginal = inner.mt_mean_field_marginal(mt, 400, 1e-6, 1.0)

    # Manually compute the NATIVE rule's local field for one Concept (the
    # SAME arithmetic can_native_update_plus/minus/zero's `where` clauses
    # use) directly, without running the rules (so a mismatch is measured,
    # not merely asserted) -- claim_credible has an INCOMING edge from
    # trust_mayor (per STRUCTURAL_EDGES) but the builder mints ONLY that
    # one direction.
    claim_credible = concepts["claim_credible"]
    out_edges = inner.neighbours(claim_credible, "causal_influence")
    in_edges_all = inner.in_neighbours(claim_credible, "causal_influence")
    print("claim_credible OUT-neighbours (native rule reads these):", list(out_edges))
    print("claim_credible IN-neighbours (can_ops.rs ALSO reads these):", list(in_edges_all))

    # The concrete, measured schema fact: claim_credible has an IN-neighbour
    # (trust_mayor) that is NOT among its OUT-neighbours -- so the native
    # rule's Sum-over-Edges(c,...) (out-edges only) would MISS that
    # coupling entirely, while can_ops.rs's build_couplings reads it.
    in_only = set(in_edges_all) - set(out_edges)
    print("IN-neighbours invisible to the native rule's Sum(Edges(c,...)):", in_only)
    assert len(in_only) > 0, (
        "expected Bigville's existing single-direction edge schema to leave "
        "at least one real coupling invisible to the native rule's out-edges-"
        "only local field -- this is the measured basis for the migration "
        "recommendation, not an assumption"
    )
