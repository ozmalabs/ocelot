"""RUNG L2 — SPATIALLY-VARYING ILLUMINANT (RETINEX) — the gate.

Pins VISION_LIGHTING_L2_RESULTS.md. Every decision under test is a
`vision_lighting_l2` seed RULE; the adapter is mechanical I/O only.

The gate pins the NEGATIVES as hard as the positives — the noise floor's
measured 13/1300 (which FAILS the pre-registered exact-0), its diagnosis, the
bound being HUGGED at exactly 1.0, and the shadow-edge probe REFUTING the
brief's expectation — so none of them can drift into an unexamined pass.
"""
from __future__ import annotations

import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble()

import domains.seed_registry  # noqa: F401,E402
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_world as lw  # noqa: E402
from domains import lighting_l2_world as l2w  # noqa: E402

CH = ("L", "M", "S")
LATTICE_STEP = 1.0

MATERIALS = [
    {"name": "a", "rL": 10, "rM": 20, "rS": 30},
    {"name": "b", "rL": 40, "rM": 15, "rS": 25},
    {"name": "c", "rL": 12, "rM": 44, "rS": 8},
    {"name": "d", "rL": 33, "rM": 9, "rS": 41},
    {"name": "e", "rL": 21, "rM": 37, "rS": 14},
    {"name": "f", "rL": 6, "rM": 28, "rS": 36},
]
NOVEL = {"name": "NOVEL", "rL": 7, "rM": 33, "rS": 19}
HEADLINE = [(1.006,) * 3, (1.008,) * 3, (1.010,) * 3, (1.012,) * 3,
            (1.006, 1.008, 1.010)]
UNIFORM = [(1.5,) * 3, (2.5,) * 3, (3.3,) * 3, (7.5,) * 3, (1.5, 2.5, 3.3),
           (2.0,) * 3, (3.0,) * 3, (4.0,) * 3]


def _refl(novel=True):
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if novel:
        out.append(dict(NOVEL))
    return out


def _field(n, rhos, g0=2.0):
    return [tuple(g0 * (rhos[k] ** x) for k in range(3)) for x in range(n)]


def _run(gains, *, reflectances=None, ref_reflectances=None, radius=1,
         flag=1.0, flag_l1=1.0, flag_l2=1.0):
    refl = _refl() if reflectances is None else reflectances
    rrefl = refl if ref_reflectances is None else ref_reflectances
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting", "vision_lighting_l1",
                            "vision_lighting_l2"])
    ref = l2w.add_frame(s, reflectances=rrefl, gain=(1.0,) * 3,
                        is_reference=True, start_sidx=0, radius=radius)
    test = l2w.add_frame(s, reflectances=refl, gain=gains, start_sidx=1000,
                         radius=radius)
    l2w.link_reference(s, test, ref)
    lw.set_flag(s, lighting=flag)
    lw.set_flag_l1(s, lighting_l1=flag_l1)
    l2w.set_flag(s, lighting_l2=flag_l2)
    l2w.tick(s)
    return s, ref, test


def _tally(s, ref, test, pfx="l2_"):
    exp = {}
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        exp.setdefault(meta["name"], int(lw.surf_attr(s, nid, "sidx")))
    c = f = r = 0
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] == NOVEL["name"]:
            continue
        R = l2w.recognition(s, nid)
        e = exp.get(meta["name"], -1)
        if R[pfx + "recognized"] == 1 and R[pfx + "id"] == e:
            c += 1
        elif R[pfx + "recognized"] == 1:
            f += 1
        else:
            r += 1
    return c, f, r


# --------------------------------------------------------------------------
# ARM A — the headline: spatially-varying invariance, where T3 and L1 refuse.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rhos", HEADLINE)
def test_a_spatially_varying_field_is_recognized(rhos):
    n = len(_refl())
    s, ref, test = _run(_field(n, rhos))
    c, f, r = _tally(s, ref, test)
    assert (c, f, r) == (12, 0, 0), f"rho={rhos}"


@pytest.mark.parametrize("rhos", HEADLINE)
def test_a_prime_T3_and_L1_REFUSE_the_same_field_on_the_same_graph(rhos):
    """The contrast that makes L2 a rung and not a re-run: BOTH prior arms are
    read off the SAME graph in the SAME tick, and both score ZERO."""
    n = len(_refl())
    s, ref, test = _run(_field(n, rhos))
    assert _tally(s, ref, test, "lit_")[0] == 0
    assert _tally(s, ref, test, "l1_")[0] == 0


def test_the_headline_total_is_sixty_out_of_sixty():
    n = len(_refl())
    tot_c = tot_f = 0
    for rhos in HEADLINE:
        s, ref, test = _run(_field(n, rhos))
        c, f, _ = _tally(s, ref, test)
        tot_c += c
        tot_f += f
    assert (tot_c, tot_f) == (60, 0)


# --------------------------------------------------------------------------
# ARM B — discrimination exact-0 (the §1.1 crux).
# --------------------------------------------------------------------------
def test_b_discrimination_is_exact_zero():
    """NOTE (§1.1, and L1's own control proved it): this test does NOT catch a
    refuse-everything build — a mechanism that refuses everything scores a
    PERFECT discrimination floor. `test_d_no_regression_*` is the arm that
    catches it. Neither floor alone is a gate; the CONJUNCTION is."""
    n = len(_refl())
    for rhos in HEADLINE:
        s, ref, test = _run(_field(n, rhos))
        assert _tally(s, ref, test)[1] == 0


# --------------------------------------------------------------------------
# ARM C — the spatial ratios are LOAD-BEARING (§13.2), and the arm is ALIVE.
# --------------------------------------------------------------------------
def test_c_ablating_the_local_ratio_collapses_the_arm():
    """The global-anchor ablation, computed on the SAME graph: the ONLY change
    is where the anchor comes from."""
    n = len(_refl())
    tot = 0
    for rhos in HEADLINE:
        s, ref, test = _run(_field(n, rhos))
        tot += _tally(s, ref, test, "l2g_")[0]
    assert tot <= 15, f"ablation scored {tot}/60 — the local ratio is decorative"
    assert tot == 10


def test_c_the_ablation_arm_is_ALIVE_at_a_uniform_gain():
    """§1.1 clause 4 — a DEAD ablation arm scores a perfect collapse and means
    nothing. Under a uniform gain the global anchor IS the right anchor."""
    n = len(_refl())
    tot = 0
    for g in UNIFORM:
        s, ref, test = _run([g] * n)
        tot += _tally(s, ref, test, "l2g_")[0]
    assert tot == 96


# --------------------------------------------------------------------------
# ARM D — NO REGRESSION: THE CONJUNCTION (process rule 5).
# --------------------------------------------------------------------------
@pytest.mark.parametrize("gain", UNIFORM)
def test_d_no_regression_uniform_gains_still_work(gain):
    """THE ARM A REFUSE-EVERYTHING BUILD FAILS. It is the only one of the four
    floors that does — the discrimination, noise and out-of-class floors are all
    PASSED by a build that never claims anything."""
    n = len(_refl())
    s, ref, test = _run([gain] * n)
    assert _tally(s, ref, test) == (12, 0, 0)


def test_d_T3_and_L1_committed_numbers_are_unmoved_with_L2_on():
    """L2 writes only l2_*/l2g_*; T3's and L1's arms must be untouched."""
    n = len(_refl())
    s, ref, test = _run([(3.0,) * 3] * n)
    assert _tally(s, ref, test, "lit_")[0] == 12
    assert _tally(s, ref, test, "l1_")[0] == 12


def test_l2_never_writes_a_T3_or_L1_attribute():
    n = len(_refl())
    s, _ref, test = _run(_field(n, (1.008,) * 3))
    seed = os.path.join(ROOT, "seeds", "vision_lighting_l2.json")
    body = open(seed).read()
    for forbidden in ('"lit_recognized"', '"lit_id"', '"l1_recognized"',
                      '"l1_id"', '"l1_resid"', '"illum_inclass"'):
        assert forbidden not in body, forbidden


# --------------------------------------------------------------------------
# ARM E — the NOISE floor, AND THE NEGATIVE IT MEASURED.
# --------------------------------------------------------------------------
def test_e1_noise_against_an_EMPTY_codebook_is_a_DEAD_ARM_and_is_discounted():
    """The pre-registered noise floor scores 0/130 — and it is WORTHLESS: 13
    random triples are all distinct, so `li_mint` mints NOTHING and every
    surface is refused against an EMPTY codebook (§1.1 clause 4). Pinned so the
    dead arm cannot be quoted as a floor."""
    claimed = codebook = 0
    for sd in range(45440, 45450):
        rng = random.Random(sd)
        noise = [{"name": f"n{i}", "rL": rng.randint(0, 120),
                  "rM": rng.randint(0, 120), "rS": rng.randint(0, 120)}
                 for i in range(13)]
        s, _ref, test = _run(_field(13, (1.008,) * 3), reflectances=noise)
        codebook += l2w.n_identities(s)
        for nid in test["surface_ids"]:
            claimed += l2w.recognition(s, nid)["l2_recognized"]
    assert claimed == 0
    assert codebook == 0, "the arm is only 'clean' because nothing was minted"


def test_BOUND_e2_the_noise_floor_is_NOT_exact_zero_against_a_LIVE_codebook():
    """THE MEASURED NEGATIVE (VISION_LIGHTING_L2_RESULTS.md). With the reference
    frame carrying the six real materials — so the codebook is LIVE — 13 of 1300
    noise surfaces CLAIM a held identity. The pre-registered decision rule for
    arm E was 'exactly 0'. **IT FAILS, and it is pinned at its measured value.**
    """
    claimed = 0
    for sd in range(45440, 45540):
        rng = random.Random(sd)
        noise = [{"name": f"n{i}", "rL": rng.randint(0, 120),
                  "rM": rng.randint(0, 120), "rS": rng.randint(0, 120)}
                 for i in range(13)]
        s, _ref, test = _run(_field(13, (1.008,) * 3), reflectances=noise,
                             ref_reflectances=_refl())
        for nid in test["surface_ids"]:
            claimed += l2w.recognition(s, nid)["l2_recognized"]
    assert claimed == 13


def test_BOUND_the_noise_false_positives_ARE_the_localized_white_patch_assumption():
    """THE DIAGNOSIS, pinned. 12 of the 13 false claims are surfaces that ARE
    their own locale's MAXIMUM on all three channels — so `ĝ = a_loc/pa_loc`
    renders the reference locale's own maximum prototype onto them EXACTLY, at
    residual 0.0. This is T3/L1's declared WHITE-PATCH assumption, localized,
    with a measured cost of ~1% on random input. It is a property of the
    mechanism, not a bug in it — and it is why the assumption is declared."""
    locmax_hits = zero_resid = total = 0
    for sd in range(45440, 45540):
        rng = random.Random(sd)
        noise = [{"name": f"n{i}", "rL": rng.randint(0, 120),
                  "rM": rng.randint(0, 120), "rS": rng.randint(0, 120)}
                 for i in range(13)]
        s, _ref, test = _run(_field(13, (1.008,) * 3), reflectances=noise,
                             ref_reflectances=_refl())
        for i, nid in enumerate(test["surface_ids"]):
            R = l2w.recognition(s, nid)
            if not R["l2_recognized"]:
                continue
            total += 1
            zero_resid += (R["l2_resid"] == 0.0)
            locmax_hits += all(
                R["c" + ch] == l2w.locale_attr(s, test, i, "l2_a" + ch)
                for ch in CH)
    assert (total, locmax_hits, zero_resid) == (13, 12, 12)


# --------------------------------------------------------------------------
# ARM F / G — out-of-class and novel-material floors.
# --------------------------------------------------------------------------
def test_f_a_fast_varying_field_is_refused_with_zero_false_ids():
    """The genuinely out-of-class field: the illuminant changes at EVERY
    adjacency, so no local ratio can discount it. The codebook is LIVE here (6
    identities), so this is a floor on the merits, not a dead arm.

    The pre-registered rule was `0 false` AND `<= 25% recognized`. Measured over
    the full block: **5/240 recognized (2.1%), 0 false** — it PASSES, and the
    small non-zero recall is pinned rather than rounded to a convenient 0.

    NOTE: the first version of the runner's arm F shuffled the scene and then
    NEVER PASSED IT, so all 20 seeds ran the IDENTICAL layout and the seed block
    did nothing (§1 — an arm that cannot vary). It read 0/240. This gate
    disagreeing with the runner is what caught it."""
    n = len(_refl())
    correct = false = 0
    for sd in range(45540, 45550):
        rng = random.Random(sd)
        refl = _refl()
        rng.shuffle(refl)
        gains = [tuple([2.0 * (1.10 if x % 2 else 1.0)] * 3) for x in range(n)]
        s, ref, test = _run(gains, reflectances=refl)
        assert l2w.n_identities(s) == 6, "codebook must be LIVE for this floor"
        c, f, _ = _tally(s, ref, test)
        correct += c
        false += f
    assert false == 0
    assert correct == 3           # 3/120 over the first half of the block


def test_g_a_never_minted_material_is_refused():
    n = len(_refl())
    for rhos in HEADLINE:
        s, _ref, test = _run(_field(n, rhos))
        nid = test["surface_ids"][-1]          # the NOVEL surface
        R = l2w.recognition(s, nid)
        assert R["l2_recognized"] == 0
        assert R["l2_status"] == "l2_refused", "a refusal must be a POSITIVE datum"


# --------------------------------------------------------------------------
# ARM H — the candidate count INSIDE the bound (process rule 7).
# --------------------------------------------------------------------------
def test_h_exactly_one_candidate_lies_inside_the_bound():
    """Rung L1b measured a landed rung whose bound NEVER BOUND (≥2 candidates
    inside it in 63/63 of its headline regime), invisible because only the
    winner's residual was reported. L2 reports the COUNT: it is 1 for every
    admitted row, so the bound IS discriminative here and the silent-`Argmin`
    hazard does NOT reproduce."""
    n = len(_refl())
    for rhos in HEADLINE:
        s, _ref, test = _run(_field(n, rhos))
        for nid in test["surface_ids"]:
            R = l2w.recognition(s, nid)
            if R["l2_recognized"]:
                assert R["l2_ncand"] == 1


def test_BOUND_the_bound_is_HUGGED_not_comfortable():
    """Pre-registered proviso 3, CONFIRMED. L1's residuals ran 0.500–0.568
    against the same bound of 1.0; L2's reach EXACTLY 1.0 at every headline
    condition. The admissible field slope is therefore exactly the
    lattice-step-over-dynamic-range quantity, with no slack."""
    n = len(_refl())
    for rhos in HEADLINE:
        s, _ref, test = _run(_field(n, rhos))
        res = [l2w.recognition(s, nid)["l2_resid"]
               for nid in test["surface_ids"]
               if l2w.recognition(s, nid)["l2_recognized"]]
        assert max(res) == pytest.approx(1.0)


# --------------------------------------------------------------------------
# THE FAILURE BOUNDARY — arm A CAN fail, and the failure is CONSERVATIVE.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("rho,expected_correct", [(1.014, 11), (1.015, 7),
                                                  (1.020, 6), (1.050, 1)])
def test_BOUND_a_steeper_field_DEGRADES_and_the_failure_is_REFUSAL(rho, expected_correct):
    """§13.1 — the headline arm sits ONE STEP below this boundary, so it could
    have failed. It degrades by REFUSING, never by claiming a wrong identity."""
    n = len(_refl())
    s, ref, test = _run(_field(n, (rho,) * 3))
    c, f, _ = _tally(s, ref, test)
    assert c == expected_correct
    assert f == 0, "the failure mode must stay CONSERVATIVE"


# --------------------------------------------------------------------------
# THE SHADOW EDGE — the brief's expectation, REFUTED and pinned.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("jump", [1.5, 2.0, 3.0])
def test_BOUND_a_shadow_EDGE_is_NOT_refused_only_the_edge_locales_are(jump):
    """PRE-REGISTERED PROVISO 2, CONFIRMED. A discontinuous field is out-of-class
    for a GLOBAL mechanism and NOT for a LOCAL one: 10/12 correct, 0 false, and
    exactly the two surfaces whose locale STRADDLES the discontinuity refused.
    **This does NOT solve L4** — L2 recovers identities on both sides without
    ever knowing an edge was a shadow. Attribution is untouched."""
    n = len(_refl())
    gains = [tuple([2.0 * (jump if x >= n // 2 else 1.0)] * 3) for x in range(n)]
    s, ref, test = _run(gains)
    c, f, r = _tally(s, ref, test)
    assert (c, f, r) == (10, 0, 2)


# --------------------------------------------------------------------------
# l2_slowvar — the REPORTED discovery, and its measured over-conservatism.
# --------------------------------------------------------------------------
def test_slowvar_DISCOVERS_a_fast_field_non_circularly():
    n = len(_refl())
    gains = [tuple([2.0 * (1.10 if x % 2 else 1.0)] * 3) for x in range(n)]
    s, _ref, test = _run(gains)
    assert l2w.n_slowvar_locales(s, test) <= 1


def test_BOUND_slowvar_is_STRICTLY_MORE_CONSERVATIVE_than_the_verdict():
    """PREREG AMENDMENT 1, pinned at its measured value: at ρ=1.010 the
    slow-variation clause passes 5 of 13 locales while the exact verdict is
    12/12 correct. That is why it is REPORTED and does not gate — a
    necessary-condition pre-filter tighter than the exact test it precedes only
    discards rows the exact test correctly accepts."""
    n = len(_refl())
    s, ref, test = _run(_field(n, (1.010,) * 3))
    assert l2w.n_slowvar_locales(s, test) == 5
    assert _tally(s, ref, test) == (12, 0, 0)


def test_slowvar_gates_NOTHING_in_the_seed():
    """Source-level: the recognition rules must not read l2_slowvar."""
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds",
                                       "vision_lighting_l2.json")))
    for rule in seed["rules"]:
        if rule["name"] in ("l2_recognize", "l2_refuse",
                            "l2_recognize_globalanchor"):
            assert "l2_slowvar" not in json.dumps(rule["where"])


# --------------------------------------------------------------------------
# §9 / §13 / §0 hygiene.
# --------------------------------------------------------------------------
def test_x_the_flag_is_OFF_by_default_and_the_seed_is_inert():
    n = len(_refl())
    s, ref, test = _run(_field(n, (1.008,) * 3), flag_l2=0.0)
    for nid in test["surface_ids"]:
        a = s.node(nid)["attrs"]
        assert float(a.get("l2_recognized", 0.0)) == 0.0
        assert float(a.get("l2g_recognized", 0.0)) == 0.0
        assert a.get("l2_status", "") == ""
    assert _tally(s, ref, test, "lit_")[0] == 0  # T3 refuses the field, as before


def test_the_flag_is_absence_tolerant_and_never_PickUnique():
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds",
                                       "vision_lighting_l2.json")))
    # The RULES, not the prose — the description legitimately says the words
    # "never PickUnique" (§12's substring-selector lesson, in miniature).
    assert "PickUnique" not in json.dumps(seed["rules"])
    for rule in seed["rules"]:
        assert '"LightingL2Params"' in json.dumps(rule["where"])
        assert '"default"' in json.dumps(rule["where"])


def test_this_rung_adds_NO_new_constant():
    """§13. The seed's entire numeric literal set must be the flag comparison,
    the inherited lattice step, its half, and the empty-codebook sentinel."""
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds",
                                       "vision_lighting_l2.json")))
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
    assert lits == {0.0, 0.5, 1.0, 1.0e9}, sorted(lits)


def test_the_universal_container_regression_is_pinned():
    """T3's central failure: `Times` takes an `items` LIST, and the a/b form
    parses to an EMPTY PRODUCT = 1, making the invariant `Eq(1,1)` — a universal
    container with a FLAWLESS invariance score. Every `Times` in this seed must
    carry `items`."""
    import json
    seed = json.load(open(os.path.join(ROOT, "seeds",
                                       "vision_lighting_l2.json")))
    n = 0

    def walk(x):
        nonlocal n
        if isinstance(x, dict):
            if x.get("type") in ("Times", "Plus", "Max"):
                assert "items" in x and len(x["items"]) >= 2, x
                n += 1
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(seed["rules"])
    assert n > 0


def test_no_python_decision_in_the_adapter():
    """§0 / CLAUDE.md — audited on the AST, not by substring (L1b's lesson: the
    first substring version of this test was caught by its own `->` annotation).
    The adapter may not branch on graph state."""
    import ast
    src = open(os.path.join(ROOT, "domains", "lighting_l2_world.py")).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        assert not isinstance(node, (ast.If, ast.IfExp)), ast.dump(node)[:120]
    # no L2 recognition attribute may be COMPARED against anything in Python
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            seg = ast.get_source_segment(src, node) or ""
            assert "l2_recognized" not in seg and "l2_id" not in seg, seg
