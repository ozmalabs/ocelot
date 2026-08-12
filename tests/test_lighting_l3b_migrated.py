"""GATE for ADVANCED LIGHTING RUNG L3b — THE ANCHOR OF THE ANCHOR.

Pre-registration VISION_LIGHTING_L3B_PREREG.md (committed BEFORE the run at
6842c2cd, §3); results VISION_LIGHTING_L3B_RESULTS.md; pinned raw
results/lighting_l3b_measure.json.

EVERY HEADLINE NUMBER IS PINNED AT ITS **MEASURED VALUE**, not at its
pre-registered inequality. That is L3's lesson, learned the hard way: arm A is a
FLOOR, and **a refuse-everything build scores a perfect floor** (§1.1, confirmed
SIX times in this arc). An inequality-only assertion would have passed on a
build that recognizes nothing. Pinning the exact value is what makes the
positive controls able to redden the gate.

The gate is DEMONSTRATED RED under three independently injected defects
(recorded in the results doc): REFUSE-EVERYTHING, ADMIT-EVERYTHING and the
`Times` EMPTY-PRODUCT trap. Neither floor alone is a gate; the CONJUNCTION is.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A provenance pin THIS REPOSITORY CANNOT RESOLVE is a SKIP, not a red: the claim
# is unverifiable here, not false, and the gate re-arms unchanged against a repo
# that has the range (tests/provenance_pins.py, red-test triage 2026-08-12).
from provenance_pins import skip_if_unresolvable as _skip_unresolvable_pin  # noqa: E402

RESULTS = os.path.join(HERE, "results", "lighting_l3b_measure.json")
SEED = os.path.join(HERE, "seeds", "vision_lighting_l3b.json")
ADAPTER = os.path.join(HERE, "domains", "lighting_l3b_world.py")
PROVENANCE = os.path.join(HERE, "results", "lighting_l3b_provenance.json")

# The base this rung was cut from (§11). BOTH ENDPOINTS OF THE PROVENANCE DIFF
# ARE FIXED: this constant and the rung's OWN commit recorded in the pin file.
# NEVER base->working-tree, NEVER base->HEAD (HEAD moves the moment anything
# merges — that exact defect has bitten three rungs), NEVER a repo-wide
# untracked scan.
BASE_SHA = "b7c3eaeb18c6a4abb0e13e3c28597acb44d52dce"


@pytest.fixture(scope="module")
def res():
    with open(RESULTS) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def seed():
    with open(SEED) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# ARM A — THE HEADLINE. The leak under LEAVE-ONE-OUT.
# ---------------------------------------------------------------------------
def test_A_the_leak_CLOSES_under_leave_one_out(res):
    """A: 0/1300. PINNED AT THE MEASURED VALUE, not at the '<= 1/1300' rule.

    A floor of 0 is exactly what a refuse-everything build scores, which is why
    this assertion is worthless on its own and is never reported without arm B
    (60/60 + 96/96) and arm B' (a non-empty disagreement on noise and an EMPTY
    one on the headline) beside it.
    """
    A = res["A_leak_and_ablation"]
    assert A["surfaces"] == 1300
    assert A["A_leak_LEAVE_ONE_OUT"] == 0
    assert A["A_rate"] == 0.0
    assert A["seeds"] == [52000, 52099]


def test_A_prime_the_ABLATION_restores_the_leak(res):
    """A': L3's own self-including pool, read off the SAME graph in the SAME
    tick, leaks 6/1300. The ablation is not a second experiment — it is
    `l3b_recognize` with the corroboration conjunct swapped back (§13.2)."""
    A = res["A_leak_and_ablation"]
    assert A["A_prime_leak_SELF_INCLUDING_pool_ABLATION"] == 6
    assert A["A_prime_leak_SELF_INCLUDING_pool_ABLATION"] > A["A_leak_LEAVE_ONE_OUT"]


def test_the_noise_arm_is_NOT_DEAD(res):
    """§1.1 clause 4: a DEAD arm scores a perfect floor. The codebook must be
    LIVE — six minted identities — or arm A means nothing."""
    A = res["A_leak_and_ablation"]
    assert A["codebook_size"] == 6
    assert A["DEAD_ARM"] is False


# ---------------------------------------------------------------------------
# ARM B — NO REGRESSION, THE CONJUNCTION. This is what a refuse-everything
# build cannot pass.
# ---------------------------------------------------------------------------
def test_B_no_regression_the_CONJUNCTION(res):
    B = res["B_no_regression"]
    assert B["L3b_correct_under_fields"] == 60 and B["n_fields"] == 60
    assert B["L3b_correct_uniform"] == 96 and B["n_uniform"] == 96
    assert B["false_under_fields"] == 0
    assert B["false_uniform"] == 0


def test_B_L3_and_L2_and_T3_and_L1_are_UNMOVED(res):
    """The sibling arms read off the SAME graph must be byte-identical to their
    own landed numbers. T3's 36/96 is T3's OWN recorded uniform baseline (it
    handles only the gains its exact-integer idiom reaches) — reproduced here,
    not improved and not damaged."""
    B = res["B_no_regression"]
    assert B["L3_correct_under_fields"] == 60
    assert B["L2_correct_under_fields"] == 60
    assert B["L3_correct_uniform"] == 96
    assert B["L1_correct_uniform"] == 96
    assert B["T3_correct_uniform"] == 36


def test_B_prime_DISAGREEMENT_both_directions(res):
    """B': the disagreement set must be NON-EMPTY on noise (else L3b is a no-op
    that only ever agrees with L3) and EMPTY on the headline (else it bought the
    leak closure with the crossing). BOTH directions are asserted — this is the
    arm a refuse-everything build reddens."""
    A = res["A_leak_and_ablation"]
    B = res["B_no_regression"]
    assert A["B_prime_disagreement_on_noise"] == 6
    assert A["B_prime_disagreement_on_noise"] > 0
    assert B["B_prime_disagreement_on_headline"] == 0


# ---------------------------------------------------------------------------
# ARM C — DISCRIMINATION. Declared WEAK in advance (§7): a refuse-everything
# build scores it perfectly and it stays GREEN under the injected defects.
# ---------------------------------------------------------------------------
def test_C_discrimination_is_exact_zero(res):
    B = res["B_no_regression"]
    F = res["F_outclass_floor"]
    assert B["false_under_fields"] == 0
    assert B["false_uniform"] == 0
    assert F["false"] == 0


# ---------------------------------------------------------------------------
# ARM R1 — THE CIRCULARITY, EXHIBITED ON THE GRAPH RATHER THAN ASSERTED.
# ---------------------------------------------------------------------------
def test_R1_the_chebyshev_centre_deviation_is_EXACTLY_ZERO(res):
    """R1 (declared ENTAILED): in EVERY ONE of the 100 noise scenes there is a
    locale whose deviation from L3's SELF-INCLUDING pool is EXACTLY 0.0.

    That is the audit's central claim — `Ĝ` IS some locale's own `ĝ`, so the
    pool's own centre cannot be refused by the corroboration it defines — and it
    is READ OFF THE GRAPH (`l3b_dev_cheb`, written by the `l3b_dev` RULE), not
    inferred from which rows were admitted."""
    A = res["A_leak_and_ablation"]
    assert A["R1_scenes_with_a_zero_dev_cheb_locale"] == 100
    assert A["R1_of_scenes"] == 100


def test_R1_holds_on_the_headline_fields_too(res):
    """The circularity is not a noise artefact: EXACTLY ONE locale sits at
    dev_cheb == 0.0 on every one of the five headline fields."""
    B = res["B_no_regression"]
    for f in B["headline_fields"]:
        assert f["n_dev_cheb_exactly_zero"] == 1


# ---------------------------------------------------------------------------
# ARM R2 — THE REGRESS. Leave-one-out certifies each locale; NOTHING certifies
# the SET.
# ---------------------------------------------------------------------------
def test_R2_mutual_corroboration_CANNOT_certify_the_SET(res):
    """R2 (RISKED): with every reflectance scaled by kappa = 2.0, all 13 locales
    corroborate UNANIMOUSLY while the recovered illuminant estimate is 4.0
    against a TRUE gain of 2.0 — wrong by exactly kappa, with ZERO false
    identities. Mutual corroboration only ever compares locales to EACH OTHER,
    so it is blind to a scale every locale shares.

    THIS ARM COULD HAVE FAILED: the deviation grows with kappa (7.75 at 2.0,
    13.18 at 4.0 against an envelope of 14.0), so a mechanism that saw the scale
    would have refused here."""
    R = res["R2_regress_exhibited"]
    assert R["HEADLINE_kappa"] == 2.0
    assert R["HEADLINE_corroborated"] == 13
    assert R["HEADLINE_n_locales"] == 13
    assert R["HEADLINE_false"] == 0
    ghat, true_gain = R["HEADLINE_ghat_vs_true"]
    assert ghat == 4.0 and true_gain == 2.0
    assert abs(ghat / true_gain - 2.0) < 1e-9   # wrong by EXACTLY kappa


def test_R2_holds_across_the_whole_kappa_sweep(res):
    """Every kappa corroborates 13/13 with a recovered ghat of exactly
    kappa x the true gain. The regress is not a single lucky point."""
    R = res["R2_regress_exhibited"]
    for o in R["per_kappa"]:
        assert o["corroborated_l3b"] == o["n_locales"] == 13
        assert o["l3b_false"] == 0
        assert abs(o["ghat_locale0"]["gL"] - o["kappa"] * 2.0) <= 0.11


# ---------------------------------------------------------------------------
# ARM R3 — LEAVE-ONE-OUT'S OWN RESIDUAL, reported honestly.
# ---------------------------------------------------------------------------
def test_R3_the_TWIN_residual_is_reported(res):
    """R3: 12 corroborated locales (of 1300) still sit at dev_loo EXACTLY 0.0 —
    two locales sharing an estimate, so leave-one-out can return `ĝ_i` after
    all. The hole is REAL and, at n=100, UNEXERCISED: none of the 12 produced a
    leak (arm A is 0). Pinned so it cannot drift unexamined."""
    A = res["A_leak_and_ablation"]
    assert A["R3_corroborated_locales_with_dev_loo_exactly_zero"] == 12
    assert A["A_leak_LEAVE_ONE_OUT"] == 0


# ---------------------------------------------------------------------------
# ARM F / G — floor and the bound's candidate count (process rule 7).
# ---------------------------------------------------------------------------
def test_F_out_of_class_floor(res):
    F = res["F_outclass_floor"]
    assert F["seeds"] == [52100, 52119]
    assert F["surfaces"] == 240
    assert F["correct"] == 3
    assert F["false"] == 0
    assert F["recognized_frac"] <= 0.25


def test_G_the_candidate_count_INSIDE_the_bound_is_reported(res):
    """Process rule 7: report the CANDIDATE COUNT inside any bound. L1b's hazard
    — a landed bound that never bound, invisible because only the winner's
    residual was reported — does not reproduce: every admitted row on every
    headline field has EXACTLY ONE candidate inside the bound."""
    B = res["B_no_regression"]
    for f in B["headline_fields"]:
        assert f["ncand"]["min"] == 1
        assert f["ncand"]["median"] == 1
        assert f["ncand"]["max"] == 1


# ---------------------------------------------------------------------------
# ARM X — §9 OFF-DAY.
# ---------------------------------------------------------------------------
def test_X_off_day_the_seed_is_INERT(res):
    X = res["X_off_day"]
    assert X["l3b_attrs_written_when_off"] == []
    assert X["L3_correct_under_field_flag_off"] == 12
    assert X["L2_correct_under_field_flag_off"] == 12
    assert X["T3_correct_at_gain3_flag_off"] == 12
    assert X["L1_correct_at_gain3_flag_off"] == 12
    assert X["L3_correct_at_gain3_flag_off"] == 12


def test_the_flag_ships_OFF_by_default(seed):
    params = [n for n in seed["nodes"] if n["type"] == "LightingL3bParams"]
    assert len(params) == 1
    assert params[0]["attrs"]["lighting_l3b"] == 0.0
    assert seed["depends_on"] == ["vision_lighting_l3"]


# ---------------------------------------------------------------------------
# COMPOSITION — no new Rust, no new constant, absence-tolerant config read.
# ---------------------------------------------------------------------------
def test_this_rung_adds_NO_new_constant(seed):
    """The numeric literal set must be IDENTICAL to L2's and L3's:
    {0.0, 0.5, 1.0, 1.0e9}. Anything else is a magic number going IN (§13)."""
    lits = set()

    def walk(x):
        if isinstance(x, dict):
            if x.get("type") == "Lit" and isinstance(x.get("value"), (int, float)):
                lits.add(float(x["value"]))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(seed["rules"])
    assert lits == {0.0, 0.5, 1.0, 1.0e9}


def test_the_config_read_is_ABSENCE_TOLERANT_never_PickUnique(seed):
    """Process rule 3 / §12.3: the flag is read via MaxOver with an explicit
    default so an ABSENT params node reads as OFF. PickUnique returns None on an
    absent node, silently changing behaviour instead."""
    blob = json.dumps(seed["rules"])
    assert "PickUnique" not in blob
    for rule in seed["rules"]:
        w = json.dumps(rule["where"])
        assert '"LightingL3bParams"' in w
        assert '"MaxOver"' in w
        assert '"default"' in w


def test_the_Times_trap_is_avoided_every_Times_and_Plus_takes_ITEMS(seed):
    """Process rule 4: `Times`/`Plus`/`Max` take an `items` LIST. The a/b form
    parses to an EMPTY operand list, and AN EMPTY PRODUCT IS 1 — which once
    turned an invariant into Eq(1,1), a universal container with a flawless
    score. Positive-controlled in the results doc."""
    bad = []

    def walk(x):
        if isinstance(x, dict):
            if x.get("type") in ("Times", "Plus", "Max"):
                if "items" not in x or not isinstance(x["items"], list) \
                        or len(x["items"]) == 0:
                    bad.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(seed["rules"])
    assert bad == []


def test_L3b_is_L3_with_EXACTLY_ONE_SWAPPED_conjunct():
    """The structural claim that makes L3's own arm the ABLATION (§13.2):
    `l3b_recognize`'s where-clause is `l3_recognize`'s with the corroboration
    conjunct swapped (l3_corr -> l3b_corr) and NOTHING ELSE changed, modulo each
    seed's own flag read (each gates on its OWN params node)."""
    with open(SEED) as f:
        l3b = json.load(f)
    with open(os.path.join(HERE, "seeds", "vision_lighting_l3.json")) as f:
        l3 = json.load(f)

    def rule(s, name):
        return next(r for r in s["rules"] if r["name"] == name)

    a = rule(l3b, "l3b_recognize")
    b = rule(l3, "l3_recognize")
    assert a["match"] == b["match"]

    def conjuncts(r):
        return [json.dumps(c, sort_keys=True) for c in r["where"]["items"]]

    ca, cb = conjuncts(a), conjuncts(b)
    assert len(ca) == len(cb)
    diff = [(x, y) for x, y in zip(ca, cb) if x != y]
    # Exactly TWO differences: the flag read (each seed gates on its own params
    # node) and the corroboration conjunct (l3_corr -> l3b_corr).
    assert len(diff) == 2
    flag_a, flag_b = diff[0]
    assert "LightingL3bParams" in flag_a and "LightingL3Params" in flag_b
    corr_a, corr_b = diff[1]
    assert "l3b_corr" in corr_a and "l3_corr" in corr_b
    # and the swap is the ONLY textual change in that conjunct
    assert corr_a.replace("l3b_corr", "l3_corr") == corr_b


def test_the_leave_one_out_EXCLUSION_is_the_mechanism(seed):
    """The rung IS the exclusion. `l3b_pool_loo` must fold over a Filter whose
    predicate is Not(Eq(var, loc)) — `Eq` compares Value::Node BY ID
    (runners/dsl/src/value.rs:225), so the locale being certified is excluded
    from its own pool and can NEVER be its own certifier."""
    pool = next(r for r in seed["rules"] if r["name"] == "l3b_pool_loo")
    blob = json.dumps(pool)
    assert '"Filter"' in blob
    assert '"Not"' in blob and '"Eq"' in blob
    # the Argmin and the MaxOver must BOTH range over a Filter, not over the
    # raw Neighbours set — otherwise self-membership is back.
    for eff in pool["effects"]:
        if eff[1].startswith("l3b_G"):
            t = json.dumps(eff[2])
            assert '"Argmin"' in t and '"MaxOver"' in t
            assert t.count('"Filter"') >= 2


def test_no_new_rust_is_required(seed):
    """Every Term this rung uses must ALREADY EXIST in the engine."""
    held = {
        "Var", "Lit", "Attr", "Gt", "Lt", "Lte", "Eq", "Minus", "Div", "Abs",
        "Not", "Times", "Plus", "Max", "And", "NodesOfType", "Neighbours",
        "Count", "Filter", "MaxOver", "MinOver", "Argmin",
    }
    seen = set()

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("type"), str):
                seen.add(x["type"])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(seed["rules"])
    assert seen <= held, f"unheld Terms: {sorted(seen - held)}"


# ---------------------------------------------------------------------------
# §0 / CLAUDE.md — NO PYTHON DECISION IN THE ADAPTER (source-audited on the AST)
# ---------------------------------------------------------------------------
def test_no_python_decision_in_the_adapter():
    """The adapter may translate and read back. It may NOT decide. Audited on
    the AST rather than by grep (§12.1: the ninth inert instrument was a grep).

    The only comprehension-level conditionals permitted are the mechanical
    counters that tally corroborated locales, and the single `radius`
    passthrough — neither reads a percept."""
    with open(ADAPTER) as f:
        tree = ast.parse(f.read())
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp)):
            seg = ast.get_source_segment(open(ADAPTER).read(), node) or ""
            offenders.append(seg.strip().splitlines()[0])
    # `radius is None` (a passthrough) is the only If in the module.
    assert len(offenders) == 1, offenders
    assert "radius is None" in offenders[0]


def test_every_decision_is_a_SEED_RULE(seed):
    """The pool, the deviations, the corroboration, the verdict and the two
    refusals are all RULES — six of them, named."""
    names = [r["name"] for r in seed["rules"]]
    assert names == ["l3b_pool_loo", "l3b_dev", "l3b_corroborate",
                     "l3b_recognize", "l3b_refuse_uncorroborated",
                     "l3b_refuse_bound"]


def test_the_envelope_is_L3s_OWN_inherited_unchanged(seed):
    """§5: the envelope was NOT widened to accommodate leave-one-out's larger
    deviations. It is L3's N*LS + HS + HS with N counted from the data."""
    corr = next(r for r in seed["rules"] if r["name"] == "l3b_corroborate")
    blob = json.dumps(corr)
    assert '"l3_n_loc"' in blob          # N read from the DATA
    with open(os.path.join(HERE, "seeds", "vision_lighting_l3.json")) as f:
        l3 = json.load(f)
    l3corr = next(r for r in l3["rules"] if r["name"] == "l3_corroborate")

    def envelopes(r):
        out = []

        def walk(x):
            if isinstance(x, dict):
                if x.get("type") == "Plus":
                    out.append(json.dumps(x, sort_keys=True))
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)

        walk(r["where"])
        return sorted(set(out))

    assert envelopes(corr) == envelopes(l3corr)


# ---------------------------------------------------------------------------
# §10 PROVENANCE — the diff is pinned to a range with BOTH ENDPOINTS FIXED.
# ---------------------------------------------------------------------------
def _git(*args):
    return subprocess.run(["git", "-C", HERE, *args], capture_output=True,
                          text=True, check=True).stdout.strip()


@pytest.fixture(scope="module")
def pin():
    assert os.path.exists(PROVENANCE), (
        "the provenance pin file is MISSING — the §10 claim cannot be made "
        "against a mutable tree")
    with open(PROVENANCE) as f:
        return json.load(f)


@_skip_unresolvable_pin(BASE_SHA)
def test_the_provenance_pin_is_well_formed_and_REACHABLE(pin):
    assert pin["base_sha"] == BASE_SHA
    rung = pin["rung_commit_sha"]
    assert len(rung) == 40
    # the pinned commit must actually be an ancestor of this branch — a pin
    # naming an unreachable commit would be a fabricated provenance claim.
    subprocess.run(["git", "-C", HERE, "merge-base", "--is-ancestor", rung,
                    "HEAD"], check=True)
    subprocess.run(["git", "-C", HERE, "merge-base", "--is-ancestor", BASE_SHA,
                    "HEAD"], check=True)


@_skip_unresolvable_pin(BASE_SHA)
def test_this_rung_adds_NO_Rust(pin):
    """§10.1 rule 4: the shared engine build is legitimate ONLY because this
    rung adds no Rust. The diff is `BASE_SHA..<this rung's own commit>` —
    BOTH ENDPOINTS FIXED, TRACKED FILES ONLY. Never base->working-tree, never
    base->HEAD (HEAD moves the moment anything merges), never a repo-wide
    untracked scan."""
    rng = f"{BASE_SHA}..{pin['rung_commit_sha']}"
    changed = _git("diff", "--name-only", rng, "--").splitlines()
    rust = [p for p in changed if p.endswith(".rs")]
    assert rust == [], f"this rung claims NO Rust but touched: {rust}"


@_skip_unresolvable_pin(BASE_SHA)
def test_the_tail_after_the_pin_adds_no_Rust_and_no_seed(pin):
    """SUPPLEMENTARY to the pinned claim above, and strictly additive: the only
    commit after the pinned rung commit is the one adding the pin file itself,
    so verify that tail introduces no `.rs` and touches no earlier lighting seed.
    The PRIMARY provenance claim remains the fixed range BASE_SHA..rung_commit_sha;
    this only closes the tail.

    SUPERVISOR REPAIR (2026-07-19). The upper endpoint was `HEAD`, which made this
    a claim about EVERY FUTURE COMMIT rather than about this rung's tail — so the
    first later rung to add Rust (INK × VENTRAL's `EnclosedCount`) turned it red
    and falsely accused L3b. L3b's underlying claim is TRUE and unchanged: it adds
    no Rust and edits no earlier lighting seed. Note that this file's OWN pin
    (`results/lighting_l3b_provenance.json`) already states the principle —
    "NOT base->HEAD (HEAD moves the moment anything merges)" — which this sibling
    test then violated. Stating a rule is not the same as being gated by it.

    The tail is now pinned to its true extent: exactly one commit, the pin commit."""
    tail_end = "66a7431fd991082940237ab307e85e611f279058"   # the pin-file commit
    changed = _git("diff", "--name-only",
                   f"{pin['rung_commit_sha']}..{tail_end}", "--").splitlines()
    assert [p for p in changed if p.endswith(".rs")] == []
    assert [p for p in changed if p.startswith(
        "research/experiments/gamma-substrate/seeds/")] == []


@_skip_unresolvable_pin(BASE_SHA)
def test_this_rung_edits_NO_committed_seed_of_an_earlier_lighting_rung(pin):
    """T3's, L1's, L1b's, L2's and L3's seeds must stay BYTE-IDENTICAL (§9)."""
    rng = f"{BASE_SHA}..{pin['rung_commit_sha']}"
    changed = _git("diff", "--name-only", rng, "--").splitlines()
    forbidden = [p for p in changed if p.startswith(
        "research/experiments/gamma-substrate/seeds/vision_lighting")
        and not p.endswith("vision_lighting_l3b.json")]
    assert forbidden == [], f"an earlier rung's seed was edited: {forbidden}"
