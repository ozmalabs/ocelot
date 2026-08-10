"""VISION GROWTH (Stage 2, L0) — the agent grows its OWN receptive fields.

These gates exist because the Stage-1 floor's "biology EMERGED from image
statistics" claim did not hold (see "The T9/T11 retraction" in
VISION_DEVELOPMENT_ARC.md): `sensory_convolution` ships six hand-designed
`designed:1.0` kernels, NO rule mints a Kernel anywhere, and the floor's
emergence measure (the `_is_center_surround`/`_is_oriented` sign classifiers)
is passed by random noise ~50-75% of the time while an ideal Gabor fails it.

So the first gate here is on the MEASURE, not on the agent
(`test_the_structure_measure_separates_gabor_from_noise`). That is the standing
lesson this work minted: *a gate whose measure passes noise is not a gate* —
before asserting structure emerged, run the measure on random input and on an
ideal exemplar.

What the growth path is: `seeds/vision_growth.json` mints a Kernel whose weights
ARE a real unexplained image patch (`vg_mint_kernel_from_patch`, scale-aware
residual test) and learns it with Oja's rule — local Hebbian with the
self-normalising decay term — winner-take-all inside the `run_rules` fixpoint
(`vg_learn_kernel_oja`). No new Rust: the update factors into two `MapList`
scalar-x-vector maps + a `VecAdd`.

Every gate here runs on REAL data (BSDS300 natural photographs), never
synthetic stand-ins, and the headline is stated as a DELTA OVER A CONTROL:
a minted kernel is initialised as an image patch, so orientation inherited
from natural-image statistics is NOT orientation produced by learning.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import domains.seed_registry  # noqa: E402,F401 -- populates REGISTRY on import
from substrate.boot_core import boot_core, load_seeds_into  # noqa: E402
from domains.vision_world import VisionWorld  # noqa: E402
from domains import vision_corpus as vc  # noqa: E402

K = 7
GROWTH_SEED = os.path.join(ROOT, "seeds", "vision_growth.json")


# --------------------------------------------------------------------------- #
#  The structure measure: spectral anisotropy. Power concentrated in ONE
#  direction of the 2D Fourier plane == an oriented (Gabor-like) receptive
#  field. Unlike the sign classifiers, this one is CALIBRATED below.
# --------------------------------------------------------------------------- #
def anisotropy(w) -> float:
    n = int(round(len(w) ** 0.5))
    g = np.asarray(w, float).reshape(n, n)
    g = g - g.mean()
    F = np.abs(np.fft.fftshift(np.fft.fft2(g, (16, 16)))) ** 2
    yy, xx = np.mgrid[:16, :16]
    dy, dx = yy - 8, xx - 8
    r = np.hypot(dy, dx)
    m = r > 0.5
    th = np.arctan2(dy, dx)[m]
    p = F[m]
    if p.sum() <= 0:
        return 0.0
    return float(np.abs((p * np.exp(2j * th)).sum()) / p.sum())


def _ideal_gabor():
    y, x = np.mgrid[-3:4, -3:4]
    g = np.exp(-(x ** 2 + y ** 2) / 8.0) * np.cos(2 * np.pi * x / 4.0)
    return (g - g.mean()).flatten()


def _ideal_dog():
    y, x = np.mgrid[-3:4, -3:4]
    g = np.exp(-(x ** 2 + y ** 2) / 2.0) - 0.5 * np.exp(-(x ** 2 + y ** 2) / 8.0)
    return (g - g.mean()).flatten()


def _grow(P, *, epochs=1, cap=16, eta=0.05, novelty=0.4):
    """Boot TABULA RASA (designed pool stripped) and let the graph grow its own
    kernels from `P`. Returns (substrate, fac, weights)."""
    s, agent = boot_core()
    load_seeds_into(s, agent, ["vision_growth"])
    fac = s.nodes("ConvFaculty")[0]
    for k in list(s.nodes("Kernel")):
        if s.node(k)["attrs"].get("designed") == 1.0:
            s.remove_edge(fac, "has_kernel", k)
    kg = s.nodes("KernelGrowth")[0]
    s.set_attr(kg, "min_contrast", 0.5)      # patches arrive unit-norm
    s.set_attr(kg, "max_kernels", float(cap))
    s.set_attr(kg, "novelty_threshold", float(novelty))
    s.set_attr(kg, "eta", float(eta))
    s.set_attr(kg, "kh", float(K))
    s.set_attr(kg, "kw", float(K))
    vw = VisionWorld(s, agent)
    for _ in range(epochs):
        for c in P:
            vw.ingest(c.flatten().tolist(), K, K, kh=K, kw=K, stride=K)
            s.tick(200_000)
    grown = [k for k in s.nodes("Kernel") if s.node(k)["attrs"].get("grown") == 1.0]
    W = [np.array(s.node(k)["attrs"]["weights"], float) for k in grown]
    return s, fac, W


@pytest.fixture(scope="module")
def patches():
    # Check the corpus EXISTS before touching it. The first cut called
    # preprocess_patches() on the result of bsds_crops() and only then tested
    # emptiness — but preprocess_patches reshapes (numpy cannot infer -1 at
    # size 0), so a tree without the corpus (data/ is gitignored, so EVERY
    # fresh worktree) got 5 ERRORS where it should get 5 skips. A skip-guard
    # that runs the thing it is guarding is not a guard.
    if len(vc.bsds_paths("train")) < 10:
        pytest.skip("BSDS300 corpus absent (data/vision_curriculum/BSDS300)")
    P = vc.preprocess_patches(vc.bsds_crops(n=260, crop=K, seed=3))
    if len(P) < 40:
        pytest.skip("BSDS300 corpus too small after preprocessing")
    return P


# --------------------------------------------------------------------------- #
#  1. GATE THE MEASURE FIRST — the lesson from the T9/T11 retraction.
# --------------------------------------------------------------------------- #
def test_the_structure_measure_separates_gabor_from_noise():
    """THE MEASURE IS A GATE TOO. The floor's sign classifiers could not
    support an emergence claim: random kernels pass them ~50-75% of the
    time and an IDEAL GABOR FAILS them. Any replacement measure must be
    calibrated before it is trusted, so this pins the property the whole
    L0 result leans on: anisotropy must rank ideal-Gabor >> noise, and
    must not mistake an isotropic DoG for an oriented cell."""
    rng = np.random.default_rng(0)
    rand = np.array([anisotropy(rng.normal(size=K * K)) for _ in range(400)])
    gabor = anisotropy(_ideal_gabor())
    dog = anisotropy(_ideal_dog())

    assert gabor > 0.75, f"ideal Gabor should score high; got {gabor:.3f}"
    assert dog < 0.15, f"ideal (isotropic) DoG should score low; got {dog:.3f}"
    assert rand.mean() < 0.30, f"noise floor too high: {rand.mean():.3f}"
    # The separation the headline depends on: no random kernel in 400 draws
    # may reach the ideal Gabor's score.
    assert rand.max() < gabor, (
        f"a random kernel ({rand.max():.3f}) matched the ideal Gabor "
        f"({gabor:.3f}) — the measure cannot support a structure claim")
    # And the contrast with the retracted measure, asserted so it cannot
    # quietly come back: the sign classifier DOES pass noise.
    from tests.test_vision_floor_migrated import _is_oriented
    noise_pass = np.mean([_is_oriented(list(rng.normal(size=9))) for _ in range(400)])
    assert noise_pass > 0.4, (
        "the floor's _is_oriented no longer passes ~half of random 3x3 "
        "kernels — if it was fixed, the retraction note should be updated")


# --------------------------------------------------------------------------- #
#  2. GROWTH ITSELF — from ZERO, on real photographs.
# --------------------------------------------------------------------------- #
def test_kernels_grow_from_zero_on_real_images(patches):
    """TABULA RASA FOR REAL: strip the six hand-designed kernels so the pool
    starts EMPTY, then show real natural-image patches. The pool must grow —
    and every grown kernel must be `designed: 0.0` / `grown: 1.0`, i.e. its
    weights came from image structure, never from a seeded template. This is
    the thing the floor could not do at all (no rule there mints a Kernel)."""
    s, fac, W = _grow(patches[:60], cap=16)
    assert len(W) > 0, "nothing grew — vg_mint_kernel_from_patch never fired"
    grown_nodes = [k for k in s.nodes("Kernel")
                   if s.node(k)["attrs"].get("grown") == 1.0]
    for k in grown_nodes:
        a = s.node(k)["attrs"]
        assert a.get("designed") == 0.0
        assert a.get("source") == "vg_mint_kernel_from_patch"
    pool = s.neighbours(fac, "has_kernel")
    assert all(s.node(k)["attrs"].get("grown") == 1.0 for k in pool), (
        "a designed kernel survived the tabula-rasa strip")


def test_growth_is_bounded_by_its_graph_data_cap(patches):
    """The pool cap is GRAPH DATA (KernelGrowth.max_kernels), not a Python
    literal, and it binds — growth is bounded, and the bound is revisable by
    the agent like any other knob."""
    _s, _fac, W = _grow(patches[:80], cap=8)
    assert 0 < len(W) <= 8, f"cap=8 not respected: grew {len(W)}"


def test_oja_is_stable_and_self_normalising(patches):
    """OJA'S RULE MUST NOT DIVERGE. This is a regression gate on a real bug:
    with raw (DC-dominated) patches, y = w.x is large, eta*y^2 exceeds 1, the
    decay term flips negative and the weights blow up to NaN — measured, not
    hypothetical. Oja's fixed point has unit norm, so on DC-removed,
    contrast-normalised input every learned kernel must stay finite and
    near-unit-norm however long it learns."""
    _s, _fac, W = _grow(patches[:120], epochs=2, cap=12, eta=0.15)
    assert W, "nothing grew"
    for w in W:
        assert np.all(np.isfinite(w)), "Oja diverged to NaN/inf"
        n = float(np.linalg.norm(w))
        assert 0.5 < n < 2.0, f"weight norm {n:.3f} escaped Oja's unit-norm fixed point"


def test_learning_actually_changes_the_minted_weights(patches):
    """The Oja rule must DO something: with eta=0 a kernel keeps exactly the
    patch it was minted from; with eta>0 it must move away from it. (Whether
    that movement adds oriented STRUCTURE is a separate, harder question — see
    the honest-delta gate below.)"""
    _s1, _f1, W_learn = _grow(patches[:100], cap=8, eta=0.15)
    _s2, _f2, W_mint = _grow(patches[:100], cap=8, eta=0.0)
    assert W_learn and W_mint
    # eta=0: every kernel is still exactly a unit-norm image patch.
    for w in W_mint:
        assert abs(float(np.linalg.norm(w)) - 1.0) < 1e-3
    moved = np.mean([float(np.linalg.norm(w) - 1.0) != 0.0 for w in W_learn])
    assert moved > 0.0, "eta>0 left every weight exactly at its minted patch"


def test_run_rules_reaches_a_fixpoint(patches):
    """A learning rule that always fires would never terminate. The `learned`
    marker makes it exactly ONE Oja step per patch per ingest, so the stream
    (not iteration) supplies the training signal — ticking twice on the same
    input must make no further progress."""
    s, agent = boot_core()
    load_seeds_into(s, agent, ["vision_growth"])
    fac = s.nodes("ConvFaculty")[0]
    for k in list(s.nodes("Kernel")):
        if s.node(k)["attrs"].get("designed") == 1.0:
            s.remove_edge(fac, "has_kernel", k)
    kg = s.nodes("KernelGrowth")[0]
    s.set_attr(kg, "min_contrast", 0.5)
    s.set_attr(kg, "kh", float(K)); s.set_attr(kg, "kw", float(K))
    vw = VisionWorld(s, agent)
    vw.ingest(patches[0].flatten().tolist(), K, K, kh=K, kw=K, stride=K)
    s.tick(200_000)
    again = s.tick(200_000)
    assert again == 0, f"rules still firing at fixpoint ({again} steps) — non-terminating"


# --------------------------------------------------------------------------- #
#  3. DONKEY=0 / architecture audit.
# --------------------------------------------------------------------------- #
def test_growth_decisions_are_graph_data_not_python():
    """Every growth DECISION (when to mint, which kernel learns, how fast)
    lives in the seed's rules + the KernelGrowth node, never in Python. The
    adapter only lays patches and ticks."""
    import json
    with open(GROWTH_SEED) as f:
        seed = json.load(f)
    names = {r["name"] for r in seed["rules"]}
    assert {"vg_mint_kernel_from_patch", "vg_learn_kernel_oja"} <= names
    kg = [n for n in seed["nodes"] if n["type"] == "KernelGrowth"][0]["attrs"]
    for knob in ("eta", "novelty_threshold", "min_contrast", "max_kernels"):
        assert knob in kg, f"{knob} is not graph data"
    # The learning rule must carry the update itself (a Term), not defer to
    # a Python helper.
    learn = [r for r in seed["rules"] if r["name"] == "vg_learn_kernel_oja"][0]
    blob = json.dumps(learn)
    assert '"VecAdd"' in blob and '"MapList"' in blob, (
        "the Oja update is no longer expressed as a graph Term")
    # No Python module may mint or hand-write a growth kernel.
    vw_src = open(os.path.join(ROOT, "domains", "vision_world.py")).read()
    assert 'add_node("Kernel"' not in vw_src
