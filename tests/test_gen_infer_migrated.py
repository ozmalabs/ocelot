"""GEN-MINT gate — the generator-inference DELTA on `DimInfer`
(`VISION_GENMINT_PREREG.md` / `VISION_GENMINT_RESULTS.md`, seeds 25000-25999).

At the point the held `DimensionGenerator` codebook is exhausted, the sd loop
can INFER a NEW general integer-linear generator FROM THE ORBIT (the `GenInfer`
Rust Term, `runners/dsl/src/shape_decode.rs`), MINT it as graph data
(`DimensionGenerator{kind:"linear", matrix}`, applied by `apply_linear_once`),
and re-decode — collapsing the orbit to one generator. Gated OFF by default on
`agent.gen_infer_enabled` (§9): the held path and the novelty path are
byte-identical unless the flag is set.

Fixtures mirror `scripts/genmint_measure.py`. The base is an asymmetric
L-tetromino whose shear/unimodular images land on cell sets no held
rotation/reflection/scale/cycle image or rung-1 delta reaches, and whose only
setwise linear self-map is the (excluded) identity.
"""
from __future__ import annotations

import json

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from domains import reflective_faculty as rf


def _gen_infer_live() -> bool:
    s, ag = boot_core()
    try:
        s._inner.evaluate(
            {"type": "GenInfer",
             "goal": {"type": "Lit", "value": [["cell", 0, 0, "x"]]}}, {})
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _gen_infer_live():
    pytest.skip("GenInfer Term not yet landed in the installed substrate_rs wheel",
                allow_module_level=True)


DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]


def _lin(M, base=BASE):
    rs = [c[1] for c in base]; cs = [c[2] for c in base]
    mr, mc = min(rs), min(cs); out = []
    for _, r, c, v in base:
        r0, c0 = r - mr, c - mc
        out.append(["cell", M[0] * r0 + M[1] * c0, M[2] * r0 + M[3] * c0, v])
    return out


def _boot(enabled):
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    if enabled:
        s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def _run(enabled, goal):
    s, ag, native = _boot(enabled)
    ax0 = len(list(s.nodes("CapabilityAxis")))
    ep = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    obs = s.add_node("Observation", {"signature": goal, "key": ["probe"],
                     "status": "decoded", "residual": goal, "decoded_epoch": ep,
                     "dim_types": DT})
    s.add_edge(ag, "observed", obs)
    native.run_rules()
    at = s.node(obs)["attrs"]
    lingens = [tuple(s.node(n)["attrs"].get("matrix"))
               for n in s.nodes("DimensionGenerator")
               if s.node(n)["attrs"].get("kind") == "linear"]
    return at.get("status"), len(list(s.nodes("CapabilityAxis"))) - ax0, lingens


SHEAR_A = [1, 0, 1, 1]
SHEAR_B = [1, 1, 0, 1]
UNIMOD = [2, 1, 1, 1]


# --- §9: OFF is byte-identical — a held-out shear falls to a flat quantum ---
def test_off_by_default_shear_mints_a_quantum_not_a_generator():
    status, quanta, lingens = _run(False, _lin(SHEAR_A))
    assert status == "minted"
    assert quanta == 1
    assert lingens == [], "with gen-mint OFF no generator may be minted (§9)"


# --- H_discovery: the multi-held-out §13.1 control — different generator per orbit ---
def test_multi_held_out_mints_the_correct_DIFFERENT_generator_and_collapses():
    seen = {}
    for M in (SHEAR_A, SHEAR_B, UNIMOD):
        status, quanta, lingens = _run(True, _lin(M))
        assert status == "recognized_transformed", f"orbit {M} must collapse to recognition"
        assert quanta == 0, "the orbit collapses to a generator, not a quantum"
        assert lingens == [tuple(M)], f"must mint exactly the inferred map {M}, got {lingens}"
        seen[tuple(M)] = lingens
    assert len(seen) == 3, "the FROZEN machinery must mint three DIFFERENT correct generators"


# --- H_floor (the gate): provably-structureless value-noise NEVER mints ---
def test_value_noise_never_mints_a_generator():
    palette = ["blue", "green", "yellow", "purple", "orange", "cyan", "magenta",
               "black", "white", "brown", "pink", "gray"]
    import random
    for i in range(40):  # the full n=400 sweep lives in the runner; 40 here keeps CI cheap
        random.seed(25000 + i)
        cols = random.sample(palette, 4)
        goal = [["cell", c[1], c[2], cols[j]] for j, c in enumerate(BASE)]
        _, _, lingens = _run(True, goal)
        assert lingens == [], f"value-noise (seed {25000+i}) must NEVER mint a generator"


# --- H_occam: a held transform is SELECTED upstream, no spurious mint ---
def test_held_rotation_is_selected_not_minted():
    ROT = [["cell", 0, 2, "red"], ["cell", 0, 1, "red"],
           ["cell", 0, 0, "red"], ["cell", 1, 0, "red"]]
    status, quanta, lingens = _run(True, ROT)
    assert status == "recognized_transformed"
    assert lingens == [], "a HELD rotation must be selected upstream, minting no new generator (Occam)"


# --- H_nonlinear: the transform the minter FAILS on, correctly (→ quantum) ---
def test_nonlinear_warp_is_correctly_refused():
    quad = []
    for _, r, c, v in BASE:
        quad.append(["cell", r, c + r * r, v])
    status, quanta, lingens = _run(True, quad)
    assert lingens == [], "a genuine nonlinear warp is outside the linear seed — refuse, do not hallucinate"
    assert status == "minted"


# --- the Term itself: exact one-shot identification + the noise null ---
def test_geninfer_term_identifies_the_map_and_nulls_on_noise():
    s, ag = boot_core()
    native = s._inner
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    goal = _lin(UNIMOD)
    exp = native.evaluate({"type": "GenInfer", "goal": {"type": "Lit", "value": goal},
                           "max_dims": 2, "field": "explained"}, {})
    mat = native.evaluate({"type": "GenInfer", "goal": {"type": "Lit", "value": goal},
                           "max_dims": 2, "field": "matrix"}, {})
    assert exp is True and tuple(mat) == tuple(UNIMOD)
    noise = [["cell", 0, 0, "blue"], ["cell", 1, 0, "green"],
             ["cell", 2, 0, "yellow"], ["cell", 2, 1, "purple"]]
    exp_n = native.evaluate({"type": "GenInfer", "goal": {"type": "Lit", "value": noise},
                             "max_dims": 2, "field": "explained"}, {})
    assert exp_n is False, "no integer-linear map fits value-incoherent noise"


# --- representation wall: a data-'linear' generator is INERT without the arm... ---
# (that is proven on the UNEXTENDED engine in scripts/genmint_pilot.py; here we
#  assert the POSITIVE: with apply_linear_once present, a data-defined matrix DOES
#  drive a decode — the wall is removed exactly by making the transform data.)
def test_data_defined_linear_generator_now_drives_a_decode():
    s, ag = boot_core()
    native = s._inner
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    s.add_node("DimensionGenerator", {"name": "shearX", "kind": "linear",
               "coord_dims": [1, 2], "matrix": [1, 0, 1, 1], "params": [1, 2, 3]})
    exp = native.evaluate({"type": "DimInfer", "goal": {"type": "Lit", "value": _lin(SHEAR_A)},
                           "max_dims": 2, "field": "explained"}, {})
    assert exp is True, "a matrix carried purely as graph DATA now explains the orbit via apply_linear_once"
