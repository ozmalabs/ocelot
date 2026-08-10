"""RUNG 5 — TWO EYES → SUPER-RESOLUTION by MULTI-LOOK DE-ALIASING.

The gate for `VISION_TWO_EYES_PREREG.md` (block 175000). Two low-resolution
photon eyes offset by a KNOWN sub-receptor amount, viewing ONE flat textured
surface, recover a spatial harmonic ABOVE either eye's receptor-Nyquist that
NEITHER can represent alone — NOT stereo (the surface is flat), MULTI-LOOK
DE-ALIASING. The FUSION is graph-native (the `multilook_superres` Rust kernel +
the `retinal_mint_superres` rule); Python is mechanical I/O only.

Pinned here:
  1. THE KERNEL de-aliases — offset samples reconstruct a supra-Nyquist harmonic
     a single eye cannot, and ZERO offset (the falsifier) does not.
  2. THE GRAPH-NATIVE PATH mints a `SuperResolvedField`; the OFF gate is silent
     (byte-identity: absent a `SuperresParams` node the rule cannot fire).
  3. THE SPATIAL HEADLINE on two real `GraphEye`s — fusion beats a single eye AND
     naive 2× stacking; zero-offset shows NO gain.
  4. THE TEMPORAL HEADLINE — the identical kernel with positions as TIMES; two
     eyes on INDEPENDENT async clocks super-resolve (space-offset ≡ time-offset).
  5. PROVENANCE — the number came from this tree's own (or a source-identical
     shared) engine.
  6. DEFAULT `GraphEye` loads no super-resolution machinery (additive / OFF).
"""
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import substrate_rs as srs  # noqa: E402

from domains.engine_provenance import engine_provenance  # noqa: E402
from domains.two_eye_superres import SuperResFuser, sample_eye  # noqa: E402
from scripts.two_eye_superres_measure import (  # noqa: E402
    spatial_arm, temporal_arm, supported_nyquist)

BLOCK = 175000


def _kernel(payload):
    """Run the multilook_superres kernel directly and return the reconstruction
    (list of n_fine floats), the pure-kernel harness used across the vision
    bench."""
    s = srs.Substrate()
    t = s.add_node("CognitiveTask", {
        "status": "requested", "kind": "multilook_superres",
        "payload": [float(v) for v in payload],
        "input_epoch": 1, "logical_time": 0, "area": "global"})
    s._inner.run_cognitive_tasks(1)
    out = list(s.node(t)["attrs"]["output"])
    assert int(out[0]) == payload[0]        # n_fine echoed
    return out[1:]


def _pack(positions, values, *, n_fine, period, ridge, k_max):
    p = [float(n_fine), float(period), float(ridge), float(k_max), float(len(positions))]
    for x, y in zip(positions, values):
        p.extend([float(x), float(y)])
    return p


def test_kernel_dealiases_with_offset_and_not_with_zero_offset():
    # A band-limited signal whose ONLY content is a harmonic k0=6 above one eye's
    # Nyquist (N/2=4). One eye (N=8 integer samples) cannot represent it; an
    # offset second eye interleaves the phase that de-aliases it.
    N, k0, P, n_fine = 8, 6, 8.0, 64
    sig = lambda x: 0.5 + 0.4 * math.cos(2 * math.pi * k0 * x / P + 0.3)
    fine = np.arange(n_fine) * P / n_fine
    gt = np.array([sig(x) for x in fine])

    xa = [float(i) for i in range(N)]
    ya = [sig(x) for x in xa]
    xb5 = [float(i) + 0.5 for i in range(N)]
    yb5 = [sig(x) for x in xb5]

    # single eye: distinct=8 -> Nyquist 4 -> no k0 basis -> cannot represent it.
    r_single = _kernel(_pack(xa, ya, n_fine=n_fine, period=P, ridge=1e-6, k_max=4))
    # fused offset: distinct=16 -> Nyquist 8 -> recovers k0.
    r_off = _kernel(_pack(xa + xb5, ya + yb5, n_fine=n_fine, period=P, ridge=1e-6, k_max=8))
    # zero offset: eye B coincident -> distinct still 8 -> Nyquist 4 -> no gain.
    r_zero = _kernel(_pack(xa + xa, ya + ya, n_fine=n_fine, period=P, ridge=1e-6, k_max=4))

    e_single = float(np.mean((np.array(r_single) - gt) ** 2))
    e_off = float(np.mean((np.array(r_off) - gt) ** 2))
    e_zero = float(np.mean((np.array(r_zero) - gt) ** 2))

    assert e_off < e_single / 100.0            # de-aliasing: fusion resolves k0
    assert e_zero == pytest.approx(e_single, rel=1e-6)   # THE FALSIFIER: no gain


def test_graph_native_fusion_mints_field_and_off_gate_is_silent():
    N, P = 8, 8.0
    sig = lambda x: 0.5 + 0.4 * math.cos(2 * math.pi * 6 * x / P)
    xa = [float(i) for i in range(N)]
    ya = [sig(x) for x in xa]

    on = SuperResFuser(enabled=True)
    recon = on.fuse(xa, ya, n_fine=32, period=P, ridge=1e-6, k_max=4)
    assert recon is not None and len(recon) == 32
    # The reconstruction lives in the graph as a SuperResolvedField node.
    fields = list(on.substrate.nodes("SuperResolvedField"))
    assert len(fields) == 1

    off = SuperResFuser(enabled=False)
    assert off.fuse(xa, ya, n_fine=32, period=P, ridge=1e-6, k_max=4) is None
    assert not list(off.substrate.nodes("SuperResolvedField"))


def test_spatial_headline_fusion_beats_single_and_naive_zero_offset_no_gain():
    rng = np.random.default_rng(BLOCK)
    r = spatial_arm(rng)
    # Criterion 1: fusion beats a single eye.
    assert r["gain_fused_over_single"] > 4.0
    # Criterion 2: fusion beats naive 2× stacking (more pixels, no new look).
    assert r["gain_fused_over_naive2x"] > 2.0
    # Criterion 3 — THE FALSIFIER: two identical eyes (δ=0) show no gain.
    assert 0.8 <= r["gain_zero_over_single"] <= 1.25
    # Criterion 4: a target only the fused pair resolves.
    assert r["k0_relerr_fused"] < 0.20
    assert r["k0_relerr_single"] > 0.60
    # The offset is what turns N distinct positions into 2N.
    assert r["single_nyquist_harmonic"] < r["k0"] < r["fused_nyquist_harmonic"]


def test_temporal_async_two_clocks_superresolve():
    rng = np.random.default_rng(BLOCK + 1)
    r = temporal_arm(rng)
    # The two eyes are on INDEPENDENT async clocks — they share NO tick.
    clocks = r["independent_async_clocks"]
    assert clocks["shared_tick"] == []
    assert set(clocks["clockA"]).isdisjoint(clocks["clockB_async"])
    # Criterion 5: the async union beats one clock (same kernel, positions=TIME).
    assert r["gain_fused_over_single"] > 4.0
    # Criterion 6 — temporal falsifier: clocks in phase show no gain.
    assert 0.8 <= r["gain_zero_over_single"] <= 1.25


def test_supported_nyquist_counts_distinct_positions():
    # Zero offset gives NO new distinct positions -> same Nyquist as one eye.
    xa = [float(i) for i in range(8)]
    assert supported_nyquist(xa, 8) == 4
    assert supported_nyquist(xa + xa, 8) == 4                 # duplicates: no gain
    assert supported_nyquist(xa + [i + 0.5 for i in range(8)], 8) == 8  # offset: 2×


def test_engine_provenance_is_own_or_shared():
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p


def test_default_graph_eye_loads_no_superres_machinery():
    # The super-resolution seed/kernel are ADDITIVE and OFF by default: a plain
    # GraphEye carries no SuperresParams / SuperResolvedField / superres task.
    _pos, _act = sample_eye(lambda x: 100.0, n_az=8, offset=0.0)
    # sample_eye builds+stops an eye; assert the default build never minted the
    # super-resolution node types by constructing a fresh default substrate.
    from domains.photon_eye import GraphEye
    eye = GraphEye(n_az=8, context={"synchronous": True}).build()
    assert not list(eye.substrate.nodes("SuperresParams"))
    assert not list(eye.substrate.nodes("SuperResolvedField"))
    eye.stop()
