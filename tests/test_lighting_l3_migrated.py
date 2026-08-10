"""ADVANCED LIGHTING RUNG L3 — GLOBAL ILLUMINANT INFERENCE — the GATE.

Pre-registration: VISION_LIGHTING_L3_PREREG.md (committed BEFORE the run at
d6c35a1f). Results: VISION_LIGHTING_L3_RESULTS.md; pinned raw
results/lighting_l3_measure.json.

WRITTEN INDEPENDENTLY OF THE RUNNER, NOT AS ASSERTIONS OVER ITS OUTPUT. That is
not stylistic: rung L2's arm F was a dead arm (it shuffled a scene and never
passed it) and was caught precisely BECAUSE the gate rebuilt the world itself
and disagreed with the runner. Every test below boots its own graph.

THE PRE-REGISTERED HEADLINE RULE FAILED AND IS GATED AT ITS MEASURED VALUE
(test_A_BOUND_*): predicted <=3/1300, measured 5/1300. It is pinned so it cannot
drift into an unexamined pass, exactly as L2 pinned its own failed floor.
"""
from __future__ import annotations

import ast
import json
import os
import random

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(HERE, "seeds", "vision_lighting_l3.json")

pytest.importorskip("substrate_rs", reason="needs the Rust engine")

import scripts.lighting_l3_measure as M  # noqa: E402
from domains import lighting_l3_world as l3w  # noqa: E402


# ---------------------------------------------------------------------------
# helpers — each test builds its OWN world.
# ---------------------------------------------------------------------------
def _seed():
    with open(SEED_PATH) as f:
        return json.load(f)


def _rule(name):
    for r in _seed()["rules"]:
        if r["name"] == name:
            return r
    raise AssertionError(f"rule {name} missing from the seed")


def _literals(obj, out=None):
    """Every numeric literal anywhere in the seed's Term trees."""
    out = [] if out is None else out
    if isinstance(obj, dict):
        if obj.get("type") == "Lit" and isinstance(obj.get("value"), (int, float)) \
                and not isinstance(obj.get("value"), bool):
            out.append(float(obj["value"]))
        for v in obj.values():
            _literals(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _literals(v, out)
    return out


def _walk(obj, pred, out=None):
    out = [] if out is None else out
    if isinstance(obj, dict):
        if pred(obj):
            out.append(obj)
        for v in obj.values():
            _walk(v, pred, out)
    elif isinstance(obj, list):
        for v in obj:
            _walk(v, pred, out)
    return out


def _noise_scene(sd, n=13):
    rng = random.Random(sd)
    return [{"name": f"n{i}", "rL": rng.randint(0, 120),
             "rM": rng.randint(0, 120), "rS": rng.randint(0, 120)}
            for i in range(n)]


def _run_noise(sd):
    noise = _noise_scene(sd)
    s, _ag = M._boot()
    ref, test, _ = M._build(s, test_refl=noise, ref_refl=M._reflectances(),
                            gains=M._field(len(noise), (1.008,) * 3))
    return s, ref, test


def _leak(sd):
    """(l3 claims, l2 claims) on ONE noise scene. l2 IS the pooling ablation."""
    s, _ref, test = _run_noise(sd)
    c3 = c2 = 0
    for nid in test["surface_ids"]:
        r = l3w.recognition(s, nid)
        c3 += r["l3_recognized"]; c2 += r["l2_recognized"]
    return c3, c2


NOISE_SEEDS = range(M.NOISE_BASE, M.NOISE_BASE + M.NOISE_N)


# ---------------------------------------------------------------------------
# STRUCTURE — the seed itself (§13, process rules 3 and 4)
# ---------------------------------------------------------------------------
def test_this_rung_adds_NO_new_constant():
    """The literal set must be L2's own: {0.0, 0.5, 1.0, 1.0e9}.

    A new number here would be a magic number (§13) — the bound is L1's
    inherited ONE LATTICE STEP and the envelope's scene extent N is COUNTED
    FROM THE DATA, never written down.
    """
    assert set(_literals(_seed())) == {0.0, 0.5, 1.0, 1.0e9}


def test_no_new_rust_is_required():
    """Every Term type used must already exist in the engine's JSON reader."""
    with open(os.path.join(HERE, "runners", "dsl", "src", "jsonio.rs")) as f:
        src = f.read()
    # ONLY the rules' Term trees. The seed's `nodes` entries also carry a
    # "type" key (the NODE type, e.g. LightingL3Params) — the first version of
    # this test walked those too and reported the params node as a missing
    # Term. Recorded in VISION_LIGHTING_L3_RESULTS.md as an instrument defect.
    used = {t["type"] for t in _walk(_seed()["rules"], lambda o: "type" in o
                                     and isinstance(o.get("type"), str))}
    for t in used:
        assert f'"{t}" =>' in src, f"Term {t} is not held — this rung would need Rust"


def test_Times_is_never_the_empty_product_a_b_form(  ):
    """Process rule 4: `Times`/`Plus`/`Max` take an `items` LIST.

    The a/b form parses to an EMPTY operand list and an EMPTY PRODUCT IS 1,
    which turned T3's invariant into Eq(1,1) — a universal container with a
    flawless score. This is positive-controlled in the results doc.
    """
    for t in _walk(_seed(), lambda o: o.get("type") in ("Times", "Plus", "Max")):
        assert "items" in t and isinstance(t["items"], list) and t["items"], t
        assert "a" not in t and "b" not in t, t


def test_the_flag_is_absence_tolerant_and_never_PickUnique():
    """Process rule 3: a params node is read with MaxOver(default), never
    PickUnique — which returns None on an absent node and silently changes
    behaviour instead of reading as OFF."""
    seed = _seed()
    assert not _walk(seed, lambda o: o.get("type") == "PickUnique")
    reads = _walk(seed, lambda o: o.get("type") == "MaxOver"
                  and o.get("source", {}).get("node_type") == "LightingL3Params")
    assert reads, "the flag must be read at all"
    for r in reads:
        assert "default" in r, "an absent params node must read as OFF, not as None"


def test_the_seed_ships_the_flag_OFF_by_default():
    """§9 — a default of 0 makes every committed result byte-identical."""
    params = [n for n in _seed()["nodes"] if n["type"] == "LightingL3Params"]
    assert params and all(p["attrs"]["lighting_l3"] == 0.0 for p in params)


def test_L3_is_L2_plus_EXACTLY_ONE_conjunct():
    """THE STRUCTURAL CLAIM THE ABLATION RESTS ON (§13.2).

    `l3_recognize` must be `l2_recognize`'s where-clause plus exactly the
    corroboration conjunct. That is what makes L2's own arm — read off the SAME
    graph in the SAME tick — the EXACT pooling ablation, and what guarantees L3
    can only SUBTRACT claims from L2 and never widen an invariance class.
    """
    with open(os.path.join(HERE, "seeds", "vision_lighting_l2.json")) as f:
        l2 = json.load(f)
    l2_rec = next(r for r in l2["rules"] if r["name"] == "l2_recognize")
    l3_rec = _rule("l3_recognize")
    # The two rules necessarily read DIFFERENT flags (each seed gates on its
    # own params node), so the comparison is made modulo the flag conjunct —
    # which is itself asserted to be the only other difference.
    def _drop_flag(terms, params):
        rest = [t for t in terms if params not in json.dumps(t)]
        assert len(rest) == len(terms) - 1, f"expected exactly one {params} read"
        return rest

    l2_terms = _drop_flag(l2_rec["where"]["items"], "LightingL2Params")
    l3_terms = _drop_flag(l3_rec["where"]["items"], "LightingL3Params")
    assert len(l3_terms) == len(l2_terms) + 1
    # the ONE addition is the corroboration read, and nothing else differs
    extra = [t for t in l3_terms if t not in l2_terms]
    assert len(extra) == 1, extra
    assert "l3_corr" in json.dumps(extra[0]), extra[0]
    assert [t for t in l2_terms if t not in l3_terms] == []


def test_the_pool_is_GLOBAL_over_the_frames_locales():
    """The scene estimate must fold over the FRAME's locales (a hub-scoped
    Neighbours, §12.1), not over a global NodesOfType grab, and must be an
    Argmin over a MaxOver — the Chebyshev center, not a mean."""
    pool = _rule("l3_pool")
    argmins = _walk(pool["effects"], lambda o: o.get("type") == "Argmin")
    assert argmins, "the pool must be decided by the held Argmin"
    for am in argmins:
        assert am["source"]["type"] == "Neighbours"
        assert am["source"]["edge_type"] == "has_locale"
        assert _walk(am["value"], lambda o: o.get("type") == "MaxOver")
    assert not _walk(pool, lambda o: o.get("type") in ("Sum", "Prod")), \
        "a mean would be dragged by the very outlier corroboration must catch"


# ---------------------------------------------------------------------------
# A — THE HEADLINE, PINNED AT ITS MEASURED (FAILING) VALUE
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_A_BOUND_the_leak_SHRINKS_but_FAILS_its_pre_registered_rule():
    """THE PRE-REGISTERED RULE WAS <=3/1300. MEASURED 5/1300 — IT FAILS.

    Pinned at the measured value, not the convenient one. The reduction half of
    the rule (strictly fewer than the ablation) DOES hold and is asserted
    separately below, so the partial result is recorded as exactly that.
    """
    l3 = sum(_leak(sd)[0] for sd in NOISE_SEEDS)
    assert l3 == 5, f"the pinned residual leak moved: {l3}"
    assert l3 > 3, "this rung FAILED its own pre-registered rule; do not silently pass it"


@pytest.mark.slow
def test_A_the_leak_IS_strictly_reduced_by_pooling():
    """The half of the rule that HOLDS: strictly fewer than with pooling off."""
    l3 = sum(_leak(sd)[0] for sd in NOISE_SEEDS)
    l2 = sum(_leak(sd)[1] for sd in NOISE_SEEDS)
    assert l3 < l2 and (l3, l2) == (5, 12)


# ---------------------------------------------------------------------------
# THE DIAGNOSIS — the residual leak is the ANCHOR OF THE ANCHOR
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_BOUND_the_pools_OWN_CENTER_is_SELF_CORROBORATING():
    """WHY THE LEAK DOES NOT CLOSE, gated as a structural fact.

    The scene estimate Ghat IS some locale's own ghat, so THAT locale's
    deviation from it is exactly 0 and it corroborates unconditionally. On
    noise it is the ONLY locale that corroborates — so the white-patch
    assumption is not eliminated, it is pushed up one level, from every locale
    to exactly ONE per scene. That is L3's honest residual and the next rung's
    problem.
    """
    for sd in (45584, 45607, 45612, 45619, 45654, 45573, 45581, 45600):
        s, _ref, test = _run_noise(sd)
        est = l3w.scene_estimate(s, test)
        corr = {i for i in range(13)
                if l3w.locale_estimate(s, test, i)["corr"] > 0.5}
        center = {i for i in range(13)
                  if all(abs(l3w.locale_estimate(s, test, i)["g" + c]
                             - est["G" + c]) < 1e-12 for c in ("L", "M", "S"))}
        assert corr and corr <= center, (sd, corr, center)


@pytest.mark.slow
def test_BOUND_every_surviving_leak_is_still_at_residual_EXACTLY_zero():
    """The surviving leaks are the SAME architectural mode L2 diagnosed — a
    surface that IS its locale's maximum, rendered onto itself exactly — not a
    new statistical tail."""
    n = 0
    for sd in NOISE_SEEDS:
        s, _ref, test = _run_noise(sd)
        for nid in test["surface_ids"]:
            r = l3w.recognition(s, nid)
            if r["l3_recognized"] == 1:
                n += 1
                assert abs(r["l3_resid"]) < 1e-12, (sd, r)
    assert n == 5


@pytest.mark.slow
def test_corroboration_refuses_nearly_every_noise_locale():
    """The mechanism's WORK, quantified: ~1 of 13 locales survives on noise."""
    tot = sum(l3w.n_corroborated_locales(*_run_noise(sd)[::2]) for sd in
              list(NOISE_SEEDS)[:30])
    assert tot / 30 < 2.0


# ---------------------------------------------------------------------------
# B — NO REGRESSION: THE CONJUNCTION (process rule 5 — the arm that must redden)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rhos", M.HEADLINE)
def test_B_no_regression_under_the_spatially_varying_fields(rhos):
    """L2's crossing must SURVIVE corroboration: 12/12, 0 false, at each field.

    THIS IS THE ARM A REFUSE-EVERYTHING BUILD MUST REDDEN. The floors do not —
    that has now been demonstrated three times in this arc.
    """
    n = len(M._reflectances())
    s, ref, test, _ = M._run(M._field(n, rhos))
    sc = M._score(s, ref, test)
    assert sc["l3"]["correct"] == 12 and sc["l3"]["false"] == 0
    assert sc["corroborated_locales"] == 13


@pytest.mark.parametrize("g", M.UNIFORM)
def test_B_no_regression_at_the_uniform_gains(g):
    """T3's and L1's own regime must be untouched — 12/12, 0 false."""
    n = len(M._reflectances())
    s, ref, test, _ = M._run([g] * n)
    sc = M._score(s, ref, test)
    assert sc["l3"]["correct"] == 12 and sc["l3"]["false"] == 0
    assert sc["l1"]["correct"] == 12


def test_B_prime_the_disagreement_set_is_EMPTY_on_the_headline():
    """B′: corroboration must cost the crossing NOTHING."""
    n = len(M._reflectances())
    for rhos in M.HEADLINE:
        s, ref, test, _ = M._run(M._field(n, rhos))
        sc = M._score(s, ref, test)
        assert sc["disagree_l2_admits_l3_refuses"] == 0
        assert sc["disagree_were_correct"] == 0


@pytest.mark.slow
def test_B_prime_the_disagreement_set_is_NON_EMPTY_on_noise():
    """B′: and it must actually DO something where the leak is (§13.2 — a
    mechanism that moves nothing downstream is decorative)."""
    d = sum(l2 - l3 for l3, l2 in (_leak(sd) for sd in NOISE_SEEDS))
    assert d == 7 and d > 0


# ---------------------------------------------------------------------------
# C — discrimination (declared IN ADVANCE to be NOT a gate on its own)
# ---------------------------------------------------------------------------
def test_C_discrimination_is_exact_zero_NOT_A_GATE_ON_ITS_OWN():
    """Pre-registered as WEAK: a refuse-everything build passes this. Kept
    because it must hold, reported as one conjunct and never as the gate."""
    n = len(M._reflectances())
    for rhos in M.HEADLINE:
        s, ref, test, _ = M._run(M._field(n, rhos))
        assert M._score(s, ref, test)["l3"]["false"] == 0


# ---------------------------------------------------------------------------
# D — POOLING IS LOAD-BEARING (§13.2)
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_D_pooling_is_LOAD_BEARING_the_leak_RETURNS_when_ablated():
    """Ablate the pooling — which is L2's own arm on the SAME graph, this rule
    minus one conjunct — and the leak must come back."""
    l2 = sum(_leak(sd)[1] for sd in NOISE_SEEDS)
    assert l2 >= 10 and l2 == 12


def test_D_the_ablation_arm_is_ALIVE(  ):
    """§1.1 clause 4 — an ablation that is merely DEAD proves nothing. Under the
    fields L2 scores full marks, so its collapse on noise is a real contrast."""
    n = len(M._reflectances())
    s, ref, test, _ = M._run(M._field(n, (1.008,) * 3))
    assert M._score(s, ref, test)["l2"]["correct"] == 12


# ---------------------------------------------------------------------------
# E — THE V4 DISSOCIATION
# ---------------------------------------------------------------------------
def test_E_v4_CONSTANCY_is_ABOLISHED_by_the_lesion():
    """With the constancy stage lesioned (ĝ ≡ 1) the same materials under a
    changed illuminant are no longer recognized, while the intact arm holds."""
    n = len(M._reflectances())
    les = intact = 0
    for rhos in M.HEADLINE:
        s, ref, test, _ = M._run(M._field(n, rhos))
        sc = M._score(s, ref, test)
        les += sc["l3_lesioned"]["correct"]; intact += sc["l3"]["correct"]
    assert les == 0 and intact == 60


def test_E_v4_DISCRIMINATION_SURVIVES_the_lesion():
    """THE HALF THAT MAKES IT A DISSOCIATION AND NOT A DEAD ARM (§1.1 cl. 4).

    At the REFERENCE illuminant the lesioned arm must still tell the distinct
    materials apart. If it failed here too, the lesion would simply have killed
    the mechanism and the 'abolition' above would be worthless.
    """
    n = len(M._reflectances())
    s, ref, test, _ = M._run([M.REF_GAIN] * n)
    sc = M._score(s, ref, test)
    assert sc["l3_lesioned"]["correct"] == 12 and sc["l3_lesioned"]["false"] == 0


# ---------------------------------------------------------------------------
# F / G / H — floors, candidate counts, cost
# ---------------------------------------------------------------------------
@pytest.mark.slow
def test_F_out_of_class_fast_varying_is_refused():
    """A field that changes at EVERY adjacency is out of class: <=25%, 0 false."""
    c = f = tot = 0
    for sd in range(M.OUTCLASS_BASE, M.OUTCLASS_BASE + M.OUTCLASS_N):
        rng = random.Random(sd)
        refl = M._reflectances()
        rng.shuffle(refl)
        s, ref, test, _ = M._run(M._alternating(len(refl), M.OUTCLASS_AMP),
                                 reflectances=refl)
        sc = M._score(s, ref, test)
        c += sc["l3"]["correct"]; f += sc["l3"]["false"]; tot += sc["n"]
    assert f == 0 and c / tot <= 0.25 and (c, tot) == (3, 240)


def test_F_a_novel_material_is_never_claimed():
    """A material with ONE patch never reaches m_min, so no identity is minted
    and it must be refused rather than force-matched."""
    n = len(M._reflectances())
    for rhos in M.HEADLINE:
        s, ref, test, _ = M._run(M._field(n, rhos))
        assert M._score(s, ref, test)["novel_claimed_l3"] == 0


def test_G_the_candidate_count_INSIDE_the_bound_is_reported(  ):
    """Process rule 7 / rung L1b's lesson: report the COUNT, not just the
    winner. A landed rung's bound turned out never to bind, invisibly."""
    n = len(M._reflectances())
    for rhos in M.HEADLINE:
        s, ref, test, _ = M._run(M._field(n, rhos))
        sc = M._score(s, ref, test)
        assert sc["ncand"]["max"] == 1, "the bound must be doing the discriminating"


def test_H_the_cost_on_the_headline_is_ZERO():
    """H, reported: corroboration refuses no CORRECT row in the crossing."""
    n = len(M._reflectances())
    lost = 0
    for rhos in M.HEADLINE:
        s, ref, test, _ = M._run(M._field(n, rhos))
        lost += M._score(s, ref, test)["disagree_were_correct"]
    assert lost == 0


# ---------------------------------------------------------------------------
# X — §9 off-day
# ---------------------------------------------------------------------------
def test_X_off_day_the_seed_is_completely_inert():
    """Flag at its default 0 ⇒ no l3_*/l3l_* attribute is written anywhere and
    T3/L1/L2 are unmoved."""
    n = len(M._reflectances())
    s, ref, test, _ = M._run(M._field(n, (1.008,) * 3), flag_l3=0.0)
    for nid in test["surface_ids"]:
        a = s.node(nid)["attrs"]
        assert float(a.get("l3_recognized", 0.0)) == 0.0
        assert float(a.get("l3l_recognized", 0.0)) == 0.0
        assert a.get("l3_status", "") == ""
    assert M._score(s, ref, test)["l2"]["correct"] == 12


def test_X_the_seed_is_not_boot_loaded():
    """It must be opt-in: a default boot must not install it."""
    from substrate.boot_core import boot_core
    s, _ag = boot_core()
    assert not s.nodes("LightingL3Params")


# ---------------------------------------------------------------------------
# §0 / CLAUDE.md — no Python decision in the adapter
# ---------------------------------------------------------------------------
def test_no_python_decision_in_the_adapter():
    """AST audit, not a substring scan (L1b's own test was caught by its `->`).

    The adapter may contain NO conditional at all: every decision — the
    estimate, the pool, the corroboration, the verdict, the refusals, the
    lesion — is a seed RULE.
    """
    path = os.path.join(HERE, "domains", "lighting_l3_world.py")
    with open(path) as f:
        tree = ast.parse(f.read())
    bad = [n for n in ast.walk(tree)
           if isinstance(n, (ast.If, ast.IfExp, ast.Compare))]
    # the only admissible comparisons are the mechanical readback counters
    for n in bad:
        assert isinstance(n, ast.Compare), f"a branch in the adapter: line {n.lineno}"
        src = ast.dump(n)
        assert "l3_corr" in src or "0.5" in src, f"line {n.lineno}: {src}"
