"""Gate for LIGHTING / APPEARANCE INVARIANCE (FRONTIER T3).

VISION_LIGHTING_PREREG.md / VISION_LIGHTING_RESULTS.md. Every decision under test is
a vision_lighting seed RULE (li_frame_stats / li_inclass / li_mint / li_recognize /
li_raw_recognize); this file only builds frames and reads attrs (PROTOCOL §0).

The floors are the point (§1.1): an "invariance" that merges everything is a
universal container and is DISQUALIFYING. This suite therefore gates the refusals
(different material, out-of-class illuminant, noise) as hard as the invariance, and
pins the two honest BOUNDS (global-scale ambiguity; the exact-arithmetic /
resolution limit) so they cannot be silently widened later.
"""
from __future__ import annotations
import random

import pytest

from domains.engine_provenance import engine_preamble
engine_preamble()

import domains.seed_registry  # noqa: E402,F401
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import lighting_world as lw  # noqa: E402

MATERIALS = [
    {"name": "a", "rL": 10, "rM": 20, "rS": 30},
    {"name": "b", "rL": 40, "rM": 15, "rS": 25},
    {"name": "c", "rL": 12, "rM": 44, "rS": 8},
    {"name": "d", "rL": 33, "rM": 9, "rS": 41},
    {"name": "e", "rL": 21, "rM": 37, "rS": 14},
    {"name": "f", "rL": 6, "rM": 28, "rS": 36},
]
NOVEL = {"name": "NOVEL", "rL": 7, "rM": 33, "rS": 19}
TEST_GAINS = [(2, 2, 2), (3, 2, 4), (5, 7, 3)]


def _refl(include_novel=True):
    out = [dict(m) for m in MATERIALS for _ in range(2)]
    if include_novel:
        out.append(dict(NOVEL))
    return out


def _boot():
    s, ag = boot_core()
    load_seeds_into(s, ag, ["vision_lighting"])
    return s, ag


def _pair(gain, *, flag=1.0, include_novel=True, reflectances=None, link=True):
    refl = _refl(include_novel) if reflectances is None else reflectances
    s, ag = _boot()
    ref = lw.add_frame(s, reflectances=refl, gain=(1, 1, 1), is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=gain, start_sidx=1000)
    if link:
        lw.link_reference(s, test, ref)
    lw.set_flag(s, lighting=flag)
    lw.tick(s)
    return s, ref, test


def _expected_key(s, ref, name):
    for nid, meta in zip(ref["surface_ids"], ref["meta"]):
        if meta["name"] == name:
            return int(lw.surf_attr(s, nid, "sidx"))
    return -1


# --- the mint ------------------------------------------------------------------
def test_mdl_mint_yields_one_identity_per_material():
    """m_min=2 FALLS OUT of d=3 — six materials at two patches each mint six."""
    s, ref, test = _pair((3, 2, 4), include_novel=False)
    assert lw.n_identities(s) == len(MATERIALS)
    assert all(i["members"] == 2 for i in lw.identities(s))


def test_a_single_patch_material_is_never_minted():
    """One patch => members=1 < m_min: below the MDL gate, nothing is minted."""
    s, ref, test = _pair((3, 2, 4), include_novel=True)
    assert lw.n_identities(s) == len(MATERIALS)   # the NOVEL single patch adds none


# --- the discovered illuminant --------------------------------------------------
@pytest.mark.parametrize("gain", TEST_GAINS)
def test_diagonal_illuminant_is_discovered_and_its_gain_recovered(gain):
    """li_inclass discovers the map and records it as an EXACT (numer,denom) pair —
    the ratio is cross-frame and is never divided into a float."""
    s, ref, test = _pair(gain, include_novel=False)
    assert lw.frame_attr(s, test, "illum_inclass") == 1.0
    ill = lw.illuminants(s)
    assert len(ill) == 1
    g = ill[0]
    for k, ch in enumerate("LMS"):
        assert g[f"g{ch}_num"] == g[f"g{ch}_den"] * gain[k]


# --- INVARIANCE (entailed by the algebra; a broken build would still fail it) ----
@pytest.mark.parametrize("gain", TEST_GAINS)
def test_same_material_under_a_changed_illuminant_is_ONE_identity(gain):
    s, ref, test = _pair(gain, include_novel=False)
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        r = lw.recognition(s, nid)
        assert r["lit_recognized"] == 1, meta
        assert r["lit_id"] == _expected_key(s, ref, meta["name"]), meta


# --- DISCRIMINATION exact-0: the §1.1 universal-container crux -------------------
@pytest.mark.parametrize("gain", TEST_GAINS)
def test_discrimination_is_EXACT_ZERO(gain):
    """A different material must stay a different identity. An 'invariance' that
    merges everything is a universal container and is DISQUALIFYING."""
    s, ref, test = _pair(gain, include_novel=False)
    cross = 0
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        r = lw.recognition(s, nid)
        if r["lit_recognized"] == 1 and r["lit_id"] != _expected_key(s, ref,
                                                                    meta["name"]):
            cross += 1
    assert cross == 0


def test_the_universal_container_regression_is_pinned():
    """REGRESSION PIN. `Times` takes an `items` LIST; written as a/b it parses to an
    EMPTY PRODUCT, and an empty product is 1 — so the anchor-relative test became
    Eq(1,1) and EVERY surface matched EVERY identity while invariance scored a
    flawless 36/36. The defect was invisible to the invariance arm and was caught
    only by the floor. This test fails if the identity assignment ever degenerates
    to 'all surfaces share one id' again."""
    s, ref, test = _pair((3, 2, 4), include_novel=False)
    ids = {lw.recognition(s, n)["lit_id"] for n in test["surface_ids"]}
    assert len(ids) == len(MATERIALS)


# --- ILLUMINANT-FACTORED vs the RAW baseline ------------------------------------
@pytest.mark.parametrize("gain", TEST_GAINS)
def test_discounting_is_load_bearing_against_the_raw_baseline(gain):
    """The untangling-style control: the RAW (undiscounted) code CONFUSES every
    lit/unlit pair while the discounted code recovers all of them."""
    s, ref, test = _pair(gain, include_novel=False)
    raw = sum(lw.recognition(s, n)["raw_recognized"] for n in test["surface_ids"])
    lit = sum(lw.recognition(s, n)["lit_recognized"] for n in test["surface_ids"])
    assert raw == 0
    assert lit == len(test["surface_ids"])


def test_the_raw_baseline_is_ALIVE(dummy=None):
    """§1.1 clause 4: a control that never fires is DEAD, not a good floor. Under the
    IDENTITY illuminant the raw baseline must succeed — it fails under a gain because
    the gain moved the values, not because the rule is inert."""
    s, ref, test = _pair((1, 1, 1), include_novel=False)
    raw = sum(lw.recognition(s, n)["raw_recognized"] for n in test["surface_ids"])
    assert raw == len(test["surface_ids"])


# --- FLOORS ---------------------------------------------------------------------
@pytest.mark.parametrize("gain", TEST_GAINS)
def test_a_different_material_is_REFUSED_not_force_matched(gain):
    s, ref, test = _pair(gain, include_novel=True)
    for nid, meta in zip(test["surface_ids"], test["meta"]):
        if meta["name"] == NOVEL["name"]:
            assert lw.recognition(s, nid)["lit_recognized"] == 0


def test_an_out_of_class_illuminant_is_REFUSED():
    """A SPATIALLY-VARYING (per-surface) illuminant is outside the diagonal class.
    The mechanism must refuse — never normalise it into a false identity. This is
    the arm that separates an invariance from a blind normaliser."""
    refl = _refl(include_novel=False)
    for i in range(5):
        rng = random.Random(45200 + i)
        gains = [(rng.randint(2, 6), rng.randint(2, 6), rng.randint(2, 6))
                 for _ in refl]
        s, ag = _boot()
        ref = lw.add_frame(s, reflectances=refl, gain=(1, 1, 1), is_reference=True,
                           start_sidx=0)
        test = lw.add_frame(s, reflectances=refl, gain=gains, start_sidx=1000)
        lw.link_reference(s, test, ref)
        lw.set_flag(s, lighting=1.0)
        lw.tick(s)
        assert lw.frame_attr(s, test, "illum_inclass") == 0.0
        assert lw.n_illuminants(s) == 0
        assert all(lw.surf_attr(s, n, "lit_recognized") == 0.0
                   for n in test["surface_ids"])


def test_noise_mints_nothing_and_claims_nothing():
    for i in range(10):
        rng = random.Random(45000 + i)
        refl = [{"name": f"n{j}", "rL": rng.randint(1, 99), "rM": rng.randint(1, 99),
                 "rS": rng.randint(1, 99)} for j in range(13)]
        s, ref, test = _pair((3, 2, 4), reflectances=refl)
        assert lw.n_identities(s) == 0
        assert all(lw.surf_attr(s, n, "lit_recognized") == 0.0
                   for n in test["surface_ids"])


# --- §13.2 load-bearing + §9 off-day --------------------------------------------
def test_the_flag_is_load_bearing():
    on_s, _, on_t = _pair((3, 2, 4), flag=1.0)
    off_s, _, off_t = _pair((3, 2, 4), flag=0.0)
    assert lw.n_identities(on_s) > 0 and lw.n_identities(off_s) == 0
    assert max(lw.surf_attr(on_s, n, "lit_recognized")
               for n in on_t["surface_ids"]) == 1.0
    assert max(lw.surf_attr(off_s, n, "lit_recognized")
               for n in off_t["surface_ids"]) == 0.0


def test_offday_default_is_inert():
    """§9: the flag's DEFAULT is 0 and the seed must be completely inert at it."""
    refl = _refl()
    s, ag = _boot()
    ref = lw.add_frame(s, reflectances=refl, gain=(1, 1, 1), is_reference=True,
                       start_sidx=0)
    test = lw.add_frame(s, reflectances=refl, gain=(3, 2, 4), start_sidx=1000)
    lw.link_reference(s, test, ref)
    lw.tick(s)   # flag never written
    assert lw.n_identities(s) == 0
    assert lw.n_illuminants(s) == 0
    assert lw.frame_attr(s, test, "stats_done") == 0.0
    assert all(lw.surf_attr(s, n, "lit_recognized") == 0.0
               for n in test["surface_ids"])


def test_the_seed_ships_the_flag_OFF():
    s, ag = _boot()
    params = list(s.nodes("LightingParams"))
    assert params
    assert all(float(s.node(p)["attrs"]["lighting"]) == 0.0 for p in params)


# --- the two HONEST BOUNDS, pinned so they cannot be silently widened ------------
def test_BOUND_global_scale_is_intrinsically_ambiguous():
    """Scaling EVERY reflectance is indistinguishable from a dimmer illuminant. This
    is the class's intrinsic ill-posedness and the CORRECT behaviour — pinned, not
    fixed."""
    refl = _refl(include_novel=False)
    scaled = [{**m, "rL": m["rL"] * 2, "rM": m["rM"] * 2, "rS": m["rS"] * 2}
              for m in refl]
    s1, _, t1 = _pair((3, 2, 4), reflectances=refl)
    s2, _, t2 = _pair((3, 2, 4), reflectances=scaled)
    assert ([lw.recognition(s1, n)["lit_recognized"] for n in t1["surface_ids"]]
            == [lw.recognition(s2, n)["lit_recognized"] for n in t2["surface_ids"]])


def test_BOUND_a_real_valued_gain_is_REFUSED_not_mis_matched():
    """THE NARROWING BOUND, pinned honestly. The comparison is EXACT integer
    cross-multiplication, so a real-valued gain (rendered through round()) breaks the
    order-statistic equality and li_inclass REFUSES. The crossing is therefore over
    the EXACT-RENDERING (integer-ratio) diagonal sub-class, NOT every diagonal map.
    The failure is CONSERVATIVE — a refusal, never a false identity — and NO
    tolerance is added to widen it (§5)."""
    refl = _refl(include_novel=False)
    s, ag = _boot()
    ref = lw.add_frame(s, reflectances=refl, gain=(1, 1, 1), is_reference=True,
                       start_sidx=0)
    frame = s.add_node("LightFrame", {
        "is_reference": 0.0, "stats_done": 0.0, "illum_inclass": 0.0,
        "aL": 0.0, "aM": 0.0, "aS": 0.0, "sL": 0.0, "sM": 0.0, "sS": 0.0})
    surfaces = []
    for i, m in enumerate(refl):
        n = s.add_node("ObjSurface", {
            "cL": float(round(m["rL"] * 2.5)), "cM": float(round(m["rM"] * 2.5)),
            "cS": float(round(m["rS"] * 2.5)), "sidx": float(1000 + i),
            "lit_recognized": 0.0, "lit_id": -1.0,
            "raw_recognized": 0.0, "raw_id": -1.0})
        s.add_edge_unchecked(frame, "has_surface", n)
        surfaces.append(n)
    s.add_edge_unchecked(frame, "compares_to", ref["frame"])
    lw.set_flag(s, lighting=1.0)
    lw.tick(s)
    assert float(s.node(frame)["attrs"]["illum_inclass"]) == 0.0
    # conservative: refused, NOT force-matched
    assert all(lw.surf_attr(s, n, "lit_recognized") == 0.0 for n in surfaces)


# --- §0 / CLAUDE.md: no Python decisions ----------------------------------------
def test_no_python_decision_in_the_adapter():
    """The adapter must contain no conditional over graph state — every decision is
    a seed rule. (Source audit, the precedent of the ink/category rungs.)"""
    import inspect
    from domains import lighting_world
    src = inspect.getsource(lighting_world)
    for banned in ("lit_recognized ==", "illum_inclass >", "if lw.", "n_identities >"):
        assert banned not in src, banned
