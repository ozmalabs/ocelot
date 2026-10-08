"""MINTING AT APERTURE — gate for seeds/aperture_minting.json and the WP1 mint
provenance in seeds/shape_decode_loop.json (v1.10.0).

RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md WP1; MINTING_AT_APERTURE.md.

Pinned claims:
  * every sd-loop mint records the aperture it was minted at;
  * an observer that opted in mints a CapabilityAxis from a residual it could
    only partly resolve, and the axis carries that observer's aperture;
  * a finer mint of the same thing is linked to the coarser one as a
    REFINEMENT along the aperture axis, exactly — not by similarity;
  * negative controls: different content, equal aperture, flag absent.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains import reflective_faculty as rf  # noqa: E402

DT = ["pred", "val", "obj"]
THUNDER = [["rumbles", "sky", "thunder"], ["flashes", "sky", "lightning"]]
TIDE = [["rises", "sea", "tide"], ["falls", "sea", "ebb"]]


def _world(observers):
    """`observers`: list of (name, resolves, percept_signature, opt_in)."""
    s, ag = boot_core()
    load_seeds_into(s, ag, ["aperture_minting"])
    native = rf._native_eval2(s)
    out = {}
    for name, resolves, sig, opt in observers:
        attrs = {"name": name, "resolves": resolves, "ap_scope_n": 0.0, "ap_gen": 0.0}
        if opt:
            attrs["mint_at_aperture"] = 1
        o = s.add_node("Observer", attrs)
        sh = s.add_node("ShapeSignature", {"name": f"{name}_sees", "kind": "world",
                                           "signature": sig, "dim_types": DT})
        s.add_edge(o, "perceives", sh)
        out[name] = o
    native.run_rules()
    return s, out


def _axes(s, source="aperture_mint"):
    return [(n, s.node(n)["attrs"]) for n in s.nodes("CapabilityAxis")
            if s.node(n)["attrs"].get("source") == source]


def _refines(s, f):
    return list(s.neighbours(f, "refines_at_aperture"))


def test_sd_loop_mint_records_its_aperture():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    dt = ["pred", "coord:r", "coord:c", "val"]
    sig = [["blob", 0, 0, "q"], ["blob", 3, 5, "q"], ["blob", 7, 1, "z"]]
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": sig, "key": ["wp1"], "status": "decoded",
                                     "residual": sig, "decoded_epoch": ep, "dim_types": dt})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    minted = list(s.neighbours(obs, "minted"))
    assert minted, s.node(obs)["attrs"].get("status")
    a = s.node(minted[0])["attrs"]
    assert list(a["minted_aperture"]) == dt          # full resolution of its own frame
    assert list(a["minted_dim_types"]) == dt
    assert json.dumps(a["minted_from_signature"]) == json.dumps(sig)
    assert "minted_epoch" in a


def test_coarse_observer_mints_at_its_own_aperture():
    s, obs = _world([("ancient", ["pred"], THUNDER, True)])
    axes = _axes(s)
    assert len(axes) == 1
    a = axes[0][1]
    assert list(a["minted_aperture"]) == ["pred"]
    assert a["minted_by_observer"] == "ancient"
    # it claims only what it resolved: every unresolved slot is the collapse constant
    for rel in a["minted_from_signature"]:
        assert list(rel[1:]) == ["\u00b7", "\u00b7"]


def test_no_opt_in_no_mint():
    s, _ = _world([("ancient", ["pred"], THUNDER, False)])
    assert _axes(s) == []


def test_finer_mint_REFINES_the_coarse_one():
    s, _ = _world([("ancient", ["pred"], THUNDER, True),
                   ("meteorologist", ["pred", "val", "obj"], THUNDER, True)])
    axes = {a["minted_by_observer"]: n for n, a in _axes(s)}
    assert set(axes) == {"ancient", "meteorologist"}
    assert _refines(s, axes["meteorologist"]) == [axes["ancient"]]
    assert _refines(s, axes["ancient"]) == []           # refinement is directed


def test_intermediate_grain_chains():
    s, _ = _world([("ancient", ["pred"], THUNDER, True),
                   ("sailor", ["pred", "val"], THUNDER, True),
                   ("meteorologist", ["pred", "val", "obj"], THUNDER, True)])
    axes = {a["minted_by_observer"]: n for n, a in _axes(s)}
    assert _refines(s, axes["sailor"]) == [axes["ancient"]]
    assert set(_refines(s, axes["meteorologist"])) == {axes["ancient"], axes["sailor"]}


def test_different_content_does_not_refine():
    s, _ = _world([("ancient", ["pred"], TIDE, True),
                   ("meteorologist", ["pred", "val", "obj"], THUNDER, True)])
    axes = {a["minted_by_observer"]: n for n, a in _axes(s)}
    assert _refines(s, axes["meteorologist"]) == []


def test_equal_aperture_shares_one_axis_and_does_not_self_refine():
    s, _ = _world([("a", ["pred"], THUNDER, True), ("b", ["pred"], THUNDER, True)])
    axes = _axes(s)
    assert len(axes) == 1, "content-keyed: same aperture + same residual is one axis"
    assert _refines(s, axes[0][0]) == []


def test_a_fully_explained_percept_mints_nothing():
    s, obs = _world([("ancient", ["pred"], THUNDER, True)])
    # second world: the same observer already HOLDS the shape it perceives
    s, ag = boot_core()
    load_seeds_into(s, ag, ["aperture_minting"])
    native = rf._native_eval2(s)
    o = s.add_node("Observer", {"name": "ancient", "resolves": ["pred"], "ap_scope_n": 0.0,
                                "ap_gen": 0.0, "mint_at_aperture": 1})
    held = s.add_node("ShapeSignature", {"name": "known_storm", "kind": "world",
                                         "signature": THUNDER, "dim_types": DT})
    seen = s.add_node("ShapeSignature", {"name": "storm_now", "kind": "world",
                                         "signature": [["rumbles", "cloud", "boom"], ["flashes", "cloud", "bolt"]],
                                         "dim_types": DT})
    s.add_edge(o, "holds_part", held)
    s.add_edge(o, "perceives", seen)
    native.run_rules()
    assert _axes(s) == [], "at this aperture the storm is already explained"
