"""QUALIA DIMENSION COMPENSATION — gates for the charter's falsifiable core.

Pre-reg: docs/research/psychology_affect/QUALIA_DIMENSION_COMPENSATION_PREREG.md
         (block 298000).
Charter: docs/research/theory_convergence/QUALIA_SPACE_VARIATION_CHARTER.md §4.
Rides on the Stage-1 generalised APERTURE (domains/analogy_search.
concept_signature(..., observer=...) consulting _observer_aperture, reusing
seeds/observer_aperture.json).

The claim: when a felt AXIS is absent, the GRAIN of the remaining axes can expand
to MOSTLY compensate — a dimension-lacking agent is near-normal on discriminations
RECONSTRUCTABLE from correlated structure on the remaining axes, but fails on a
discrimination ORTHOGONAL to every remaining axis AT ANY GRAIN (aperture cannot
manufacture a dimension = the aphantasia shape). If a finer grain ever recovers
the orthogonal discrimination, the charter is FALSIFIED.

These gates pin, in order:
  (a) GENERALISATION DEFAULT==TODAY — observer=None is byte-identical to the
      pre-Stage-1 (no-aperture) dynamical read, re-asserted on a couple of
      signatures (the Stage-1 guard this experiment inherits);
  (b) FULL discriminates the orthogonal pair; BOTH dark agents do NOT;
  (c) APERTURE-INVARIANT residual — sweep the compensated agent's commitment
      grain fine -> finer, the orthogonal discrimination NEVER recovers;
  (d) COMPENSATION REAL + MEANINGFUL — DARK-COMPENSATED discriminates >=1
      reconstructable pair DARK-UNCOMPENSATED misses, and the recovery needed a
      grain finer than global (not already visible globally);
  (e) ORTHOGONALITY BY CONSTRUCTION — removing sharpness (dark) makes the
      orthogonal pair's two signatures byte-EQUAL.
"""
from __future__ import annotations

import pathlib

import pytest

pytest.importorskip("substrate_rs")

import domains.analogy_search as asr                     # noqa: E402
import domains.qualia_aperture_world as world            # noqa: E402

ROOT = pathlib.Path(asr.__file__).resolve().parent.parent


def _dyn(sig):
    """Just the dynamical field coordinates of a signature."""
    return frozenset(t for t in sig if t[1] == "field")


# --------------------------------------------------------------------------- #
# (a) GENERALISATION DEFAULT==TODAY — observer=None byte-identical to the
#     pre-Stage-1 no-aperture dynamical read (the guard).
# --------------------------------------------------------------------------- #
def _dynamical_no_aperture(s, node, schema, overlay):
    """The dynamical axes computed the PRE-CHANGE way: global quantum, no gate.
    This is literally the pre-Stage-1 `_dynamical_relations` body."""
    attrs = s.node(node)["attrs"]
    out = []
    for dim, attr_name, quantum, half_width, is_overlay in schema["field_axes"]:
        if is_overlay and not overlay:
            continue
        raw = attrs.get(attr_name)
        if raw is None:
            continue
        k = asr._round_to_vocab(raw, quantum, half_width)
        if k is None:
            continue
        out.append((dim, "field", k))
    return frozenset(out)


def test_generalisation_default_is_today_byte_identical():
    s, _ag = world._substrate()
    mt = world._mt(s, "default_today")
    schema = asr._qualia_schema(s)
    # a sharpness-bearing, committed concept + a differently-shaped one
    star = world._concept(s, mt, "star", category="shape", sharpness=1.0,
                          identity_field=0.8, state=1.0, external_field=0.6)
    cloud = world._concept(s, mt, "cloud", category="shape", sharpness=-1.0,
                           identity_field=-0.7, state=-1.0)
    for c in (star, cloud):
        for overlay in (False, True):
            got = _dyn(asr.concept_signature(s, c, observer=None, overlay=overlay))
            want = _dynamical_no_aperture(s, c, schema, overlay)
            assert got == want, (s.node(c)["attrs"]["name"], overlay, got, want)


# --------------------------------------------------------------------------- #
# (b) FULL discriminates the orthogonal pair; BOTH dark agents do NOT.
# --------------------------------------------------------------------------- #
def test_full_discriminates_orthogonal_both_dark_do_not():
    w = world.build()
    s = w["s"]
    _n, oa, ob = w["orth"]
    assert world._discriminable(s, oa, ob, w["full"]), \
        "FULL must discriminate the orthogonal pair (its sharpness coordinate differs)"
    assert not world._discriminable(s, oa, ob, w["dark_comp"]), \
        "DARK-COMPENSATED must NOT discriminate the orthogonal pair"
    assert not world._discriminable(s, oa, ob, w["dark_unc"]), \
        "DARK-UNCOMPENSATED must NOT discriminate the orthogonal pair"


# --------------------------------------------------------------------------- #
# (c) APERTURE-INVARIANT residual — sweep fine -> finer, orthogonal never
#     recovers (the charter's falsifiable core).
# --------------------------------------------------------------------------- #
def test_orthogonal_discrimination_aperture_invariant():
    w = world.build()
    s = w["s"]
    _n, oa, ob = w["orth"]
    obs = w["dark_comp"]
    # sweep the compensated agent's commitment grain fine -> finer (well past the
    # fine grain the experiment uses); the existence gate (sharpness dark) held.
    for q in [0.10, 0.05, 0.02, 0.01, 0.005]:
        s.set_attr(obs, "grain", {world.DIM_COMMITMENT: q})
        assert not world._discriminable(s, oa, ob, obs), (
            "orthogonal discrimination RECOVERED at commitment grain %r — "
            "CHARTER FALSIFIED (aperture manufactured a dimension)" % q)


# --------------------------------------------------------------------------- #
# (d) COMPENSATION REAL + MEANINGFUL — DARK-COMPENSATED reconstructs >=1 pair
#     DARK-UNCOMPENSATED misses, and it needed a grain finer than global.
# --------------------------------------------------------------------------- #
def test_compensation_real_and_meaningful():
    w = world.build()
    s = w["s"]
    recon = w["recon"]
    comp, unc = w["dark_comp"], w["dark_unc"]
    comp_hits = {n for n, a, b in recon if world._discriminable(s, a, b, comp)}
    unc_hits = {n for n, a, b in recon if world._discriminable(s, a, b, unc)}
    # REAL: compensated strictly beats uncompensated on reconstructable pairs
    gained = comp_hits - unc_hits
    assert gained, ("DARK-COMPENSATED discriminated no reconstructable pair that "
                    "DARK-UNCOMPENSATED missed — compensation not demonstrated")
    # MEANINGFUL: at GLOBAL grain (0.25) the compensated agent gets NONE of them,
    # so the recovery required the finer grain (not already visible globally).
    s.set_attr(comp, "grain", {world.DIM_COMMITMENT: 0.25})
    global_hits = {n for n, a, b in recon if world._discriminable(s, a, b, comp)}
    assert not global_hits, ("reconstructable pairs were discriminable at GLOBAL "
                             "grain — compensation is TRIVIAL, not meaningful")
    # and DARK-UNCOMPENSATED (global grain) indeed gets none
    assert not unc_hits


# --------------------------------------------------------------------------- #
# (e) ORTHOGONALITY BY CONSTRUCTION — dark makes the two O-signatures byte-EQUAL.
# --------------------------------------------------------------------------- #
def test_orthogonal_pair_byte_equal_when_dark():
    w = world.build()
    s = w["s"]
    _n, oa, ob = w["orth"]
    # FULL: the two signatures DIFFER (only on the sharpness coordinate).
    fa = asr.concept_signature(s, oa, observer=w["full"])
    fb = asr.concept_signature(s, ob, observer=w["full"])
    assert fa != fb
    diff = (fa ^ fb)
    assert all(t[0] == world.DIM_SHARPNESS for t in diff), \
        "the FULL signatures must differ on ONLY the sharpness axis (orthogonality)"
    # a DARK agent: the two signatures are BYTE-EQUAL (sharpness was the only
    # separator and it is gone) — at BOTH dark agents.
    for obs in (w["dark_comp"], w["dark_unc"]):
        da = asr.concept_signature(s, oa, observer=obs)
        db = asr.concept_signature(s, ob, observer=obs)
        assert da == db, "dark ⇒ orthogonal pair must be byte-EQUAL"


# --------------------------------------------------------------------------- #
# End-to-end: the whole run reports CONFIRMED with the pre-registered numbers.
# --------------------------------------------------------------------------- #
def test_run_reports_confirmed_with_preregistered_rates():
    r = world.run(verbose=False)
    assert r["verdict"] == "CONFIRMED"
    assert r["orthogonal_ever_recovered"] is False
    assert r["compensation_real"] is True
    assert r["compensation_meaningful"] is True
    base = r["base_rates"]
    assert base["FULL"]["reconstructable_rate"] == [3, 3]
    assert base["FULL"]["orthogonal_rate"] == 1
    assert base["DARK-COMPENSATED"]["reconstructable_rate"] == [3, 3]
    assert base["DARK-COMPENSATED"]["orthogonal_rate"] == 0
    assert base["DARK-UNCOMPENSATED"]["reconstructable_rate"] == [0, 3]
    assert base["DARK-UNCOMPENSATED"]["orthogonal_rate"] == 0
    # every swept grain leaves the orthogonal discrimination FAILED
    assert all(row["orthogonal_rate"] == 0
               for row in r["grain_sweep_dark_compensated"])
