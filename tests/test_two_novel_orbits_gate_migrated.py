"""Two-novel-orbits gate (`TWO_NOVEL_ORBITS_GATE_PREREG.md` /
`TWO_NOVEL_ORBITS_GATE_RESULTS.md`).

CLOSES A NAMED METHODOLOGY GAP, quoted verbatim from
`docs/research/engine_substrate/DEDUP_ADOPTION_SWEEP_RESULTS.md`:

    "the real methodology gap this rung found -- no existing test in the
    tree presents two novel orbits to one graph, which is exactly why both
    the stall and the loop survived every prior gate."

That rung found (and fixed, `seeds/shape_decode_loop.json` v1.8.0 -> v1.9.0,
commit `dcea7ad`) two defects that ONLY show up when a second or third
genuinely novel orbit is presented to a graph that already holds a discovery
from a first orbit:

  * THE STALL (pre-fix): a type-coarse `Not Exists ... kind == "linear"`
    guard capped the whole graph at one discovered linear generator for its
    entire life. A second/third novel orbit reached neither a generator nor
    a quantum -- it terminated at `status == "decoded"` and was silently
    dropped, no error.
  * THE LOOP (a since-abandoned first-attempt fix): swapping in
    `add_node_if_absent` with no per-observation termination guard drove
    `codebook_epoch` from 1 to 20,001 in a SINGLE `run_rules` call (87.4s).

Every existing gate in `tests/test_gen_infer_migrated.py` boots a FRESH
graph per orbit (`_run` -> `_boot`), so neither defect was ever reachable by
a committed test. This file is the missing class: it presents multiple
genuinely novel orbits to ONE graph, in ONE session, and asserts (a) no
observation is silently dropped (the stall class), (b) epoch/wall-clock
growth stays orders of magnitude below the pre-fix-attempt blowup (the loop
class), and (c) the dedup direction is correct both ways (novel mints,
repeat doesn't re-mint, no name collision). A second grain
(`ShapeSignature`/`vq_grow_quantum`, `seeds/vision_sdloop.json`) gets the
same test SHAPE per the PREREG's AR5 (`MetaShape` was considered and ruled
out -- its fix needs a new Rust field, out of this task's scope).
"""
from __future__ import annotations

import json
import time

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


# --------------------------------------------------------------------------- #
#  Grain 1: DimensionGenerator (linear generators) + LatentDimension
#  (seeds/shape_decode_loop.json, DEDUP_ADOPTION_SWEEP_RESULTS.md AR4.1/AR4.2)
# --------------------------------------------------------------------------- #
DT = ["pred", "coord:r", "coord:c", "val"]
BASE = [["cell", 0, 0, "red"], ["cell", 1, 0, "red"],
        ["cell", 2, 0, "red"], ["cell", 2, 1, "red"]]

SHEAR_A = [1, 0, 1, 1]
SHEAR_B = [1, 1, 0, 1]
UNIMOD = [2, 1, 1, 1]           # == SHEAR_A composed with SHEAR_B


def _lin(M, base=BASE):
    rs = [c[1] for c in base]; cs = [c[2] for c in base]
    mr, mc = min(rs), min(cs); out = []
    for _, r, c, v in base:
        r0, c0 = r - mr, c - mc
        out.append(["cell", M[0] * r0 + M[1] * c0, M[2] * r0 + M[3] * c0, v])
    return out


def _boot_gen():
    """ONE graph for the whole scenario -- deliberately NOT re-booted per orbit."""
    s, ag = boot_core()
    native = rf._native_eval2(s)
    rf._ensure_shape_decode_loop(s, native, ag)
    s.set_attr(ag, "gen_infer_enabled", 1.0)
    s.add_node("ShapeSignature", {"name": "base_L", "signature": json.dumps(BASE),
               "kind": "faculty", "faculty": "base_L", "dim_types": DT})
    return s, ag, native


def _present(s, ag, native, M, key):
    """Present one orbit as a fresh Observation on the SAME graph. Returns
    (status, epoch_after, wall_seconds, sorted linear-generator matrices)."""
    ep_before = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    o = s.add_node("Observation", {"signature": _lin(M), "key": [key], "status": "decoded",
                    "residual": _lin(M), "decoded_epoch": ep_before, "dim_types": DT})
    s.add_edge(ag, "observed", o)
    t0 = time.time()
    native.run_rules()
    dt = time.time() - t0
    ep_after = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    status = s.node(o)["attrs"].get("status")
    lingens = sorted(tuple(s.node(n)["attrs"].get("matrix"))
                      for n in s.nodes("DimensionGenerator")
                      if s.node(n)["attrs"].get("kind") == "linear")
    return status, ep_after, dt, lingens


# --------------------------------------------------------------------------- #
#  AR1/AR2/AR3/AR4 -- the primary scenario: four orbits, one graph
# --------------------------------------------------------------------------- #
def test_four_orbits_one_graph_no_stall_bounded_growth_correct_dedup():
    s, ag, native = _boot_gen()
    ep0 = s.node(ag)["attrs"].get("codebook_epoch") or 0.0

    total_t0 = time.time()
    statuses = []
    epochs = [ep0]
    wall_times = []
    for key, M in (("A", SHEAR_A), ("B", SHEAR_B), ("U", UNIMOD), ("A2", SHEAR_A)):
        status, ep_after, dt, lingens = _present(s, ag, native, M, "orbit_%s" % key)
        statuses.append(status)
        epochs.append(ep_after)
        wall_times.append(dt)

        # --- AR2: the STALL assertion, checked AFTER EVERY orbit, not just at
        # the end -- a stall on orbit 2 or 3 must not be able to hide behind a
        # later orbit's success.
        assert status == "recognized_transformed", (
            "orbit %r must resolve to recognized_transformed, not silently "
            "drop to an unexplained terminal status (the pre-fix stall): got %r"
            % (key, status))

        # --- AR3: the LOOP assertion, per-call -- bounded WAY below the
        # measured 87.4s / 20,000-epoch pre-fix-attempt blowup.
        assert dt < 3.0, (
            "one run_rules() call took %.3fs -- the pre-fix-attempt loop took "
            "87.4s per call; this bound is 29x smaller and cannot be satisfied "
            "by a regression to that state" % dt)

    total_dt = time.time() - total_t0

    # --- AR3, whole-scenario bounds.
    assert total_dt < 10.0, "the whole 4-orbit scenario took %.3fs (bound 10s)" % total_dt
    epoch_growth = epochs[-1] - epochs[0]
    assert epoch_growth <= 4, (
        "codebook_epoch grew by %r across 4 orbits -- measured correct behaviour is "
        "+2 (one bump per genuine generator mint, zero for the composed orbit and "
        "the repeat); the pre-fix-attempt loop grew it by 20,000 IN A SINGLE CALL, "
        "four orders of magnitude above this bound" % epoch_growth)

    # --- AR4: the dedup-direction assertions -- exactly 2 generators, not 3
    # (no spurious mint for the orbit explainable as composition) and not 1
    # (the pre-fix cap).
    gens = {s.node(n)["attrs"].get("name"): tuple(s.node(n)["attrs"].get("matrix"))
            for n in s.nodes("DimensionGenerator")
            if s.node(n)["attrs"].get("kind") == "linear"}
    assert len(gens) == 2, (
        "expected exactly 2 distinct linear generators (SHEAR_A, SHEAR_B) after "
        "4 orbits including one composition and one repeat; got %d: %r"
        % (len(gens), gens))
    assert set(gens.values()) == {tuple(SHEAR_A), tuple(SHEAR_B)}, gens

    # --- AR4: the two generator NAMES must be DISTINCT -- this is the direct
    # regression check for the load_generators name-shadowing bug
    # (DEDUP_ADOPTION_SWEEP_RESULTS.md 4.2.3): under the pre-correction-2 state
    # (base-shape-derived names) both would collide on "genlin_base_L" and
    # last-write-wins would silently drop the first -- exactly what the final
    # "A2" (repeat of SHEAR_A) step below is placed to catch.
    assert len(set(gens.keys())) == 2, "generator names collided: %r" % gens
    assert gens.get("genlin_[1,0,1,1]") == tuple(SHEAR_A)
    assert gens.get("genlin_[1,1,0,1]") == tuple(SHEAR_B)

    # --- The orbit-4 repeat must STILL explain against the FIRST-minted
    # generator (name-shadowing would make this the one that fails, not orbit
    # 1 itself, per the exact live sequence DEDUP_ADOPTION_SWEEP_RESULTS.md
    # measured: "a repeat of orbit 1 then failed to be explained").
    assert statuses[-1] == "recognized_transformed"

    # --- AR4: exactly 3 distinct LatentDimension names -- 2 individual
    # generators + 1 composition; the repeat must NOT mint a 4th (AR4.1's
    # add_node_if_absent fix).
    lds = sorted({s.node(n)["attrs"].get("name") for n in s.nodes("LatentDimension")})
    assert lds == [
        "latent:genlin_[1,0,1,1]",
        "latent:genlin_[1,0,1,1]+genlin_[1,1,0,1]",
        "latent:genlin_[1,1,0,1]",
    ], lds


def test_second_novel_orbit_does_not_stall_even_isolated():
    """A tighter isolation of the exact pre-fix defect: present ONLY two
    distinct novel orbits (no composition, no repeat) and confirm BOTH
    resolve. This is the minimal reproduction of DEDUP_ADOPTION_SWEEP_RESULTS.md
    4.2.1's "orbit 2 and 3 mint nothing" finding -- checked here with just
    orbit 2, so a partial fix that happens to handle orbit 3 specially (it
    does not, but the assertion should not depend on that) still gets caught."""
    s, ag, native = _boot_gen()
    status1, _, _, lingens1 = _present(s, ag, native, SHEAR_A, "iso_A")
    assert status1 == "recognized_transformed"
    assert lingens1 == [tuple(SHEAR_A)]

    status2, _, _, lingens2 = _present(s, ag, native, SHEAR_B, "iso_B")
    assert status2 == "recognized_transformed", (
        "the SECOND novel orbit in one graph must resolve -- this is exactly "
        "the pre-fix stall (DEDUP_ADOPTION_SWEEP_RESULTS.md 4.2.1: orbit 2 "
        "terminated at status=='decoded' and was silently dropped)")
    assert lingens2 == [tuple(SHEAR_A), tuple(SHEAR_B)], (
        "the second orbit must mint its OWN generator, distinct from the first")


def test_repeat_orbit_after_two_mints_does_not_triple_mint():
    """Dedup direction, isolated: after two DISTINCT generators are minted,
    re-presenting either one must recognize, not mint a third."""
    s, ag, native = _boot_gen()
    _present(s, ag, native, SHEAR_A, "d_A")
    _present(s, ag, native, SHEAR_B, "d_B")
    status, _, _, lingens = _present(s, ag, native, SHEAR_A, "d_A_repeat")
    assert status == "recognized_transformed"
    assert len(lingens) == 2, "a repeat must not mint a third generator: %r" % lingens
    status2, _, _, lingens2 = _present(s, ag, native, SHEAR_B, "d_B_repeat")
    assert status2 == "recognized_transformed"
    assert len(lingens2) == 2, "a repeat must not mint a third generator: %r" % lingens2


# --------------------------------------------------------------------------- #
#  AR5 -- generalisation to a second grain: ShapeSignature / vq_grow_quantum
#  (seeds/vision_sdloop.json, domains/sdloop_vision.py). MetaShape was
#  considered (PREREG) and ruled out -- its fix needs a new Rust field.
# --------------------------------------------------------------------------- #
np = pytest.importorskip("numpy")

import domains.sdloop_vision as SV  # noqa: E402
from substrate.boot_core import load_seeds_into  # noqa: E402

# Three STRUCTURALLY distinct shapes (different cell counts, not orientations
# of one shape) so no orbit-law rotation/reflection folding applies -- each
# must be genuinely novel to the codebook.
_TROMINO = [["on", 0, 0], ["on", 0, 1], ["on", 1, 0]]
_SQUARE = [["on", 0, 0], ["on", 0, 1], ["on", 1, 0], ["on", 1, 1]]
_LINE3 = [["on", 0, 0], ["on", 0, 1], ["on", 0, 2]]


def _boot_vq():
    s, ag = boot_core()
    native = rf._native_eval2(s)
    load_seeds_into(s, ag, ["vision_sdloop"])
    if s.node(ag)["attrs"].get("codebook_epoch") is None:
        s.set_attr(ag, "codebook_epoch", 0.0)
    return s, ag, native


def test_three_novel_shapes_one_graph_mint_distinctly_bounded_growth():
    s, ag, native = _boot_vq()
    ep0 = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    mints0 = SV.codebook_state(s)["mints"]

    total_t0 = time.time()
    running_mints = mints0
    for key, sig in (("tromino", _TROMINO), ("square", _SQUARE), ("line3", _LINE3)):
        t0 = time.time()
        o = SV.ingest(s, ag, sig, key)
        native.run_rules()
        dt = time.time() - t0
        assert dt < 3.0, "one run_rules() call took %.3fs at the vq grain (bound 3s)" % dt

        cs = SV.codebook_state(s)
        # --- AR2-shaped assertion at this grain: each structurally-novel
        # shape must increase the mint count by exactly 1 -- a silent drop
        # would show up here as a smaller-than-expected running total. (The
        # observation's own terminal `status` reads "recognized" even for a
        # brand-new shape -- vq_grow_quantum installs the codebook entry and
        # bumps the epoch in the SAME rule firing, so the observation
        # immediately re-recognizes itself; `mints` -- the CapabilityAxis
        # count -- is the correct novelty signal, per PREREG AR5.)
        assert cs["mints"] == running_mints + 1, (
            "shape %r did not cause a mint (stall at the vq grain): mints %d -> %d"
            % (key, running_mints, cs["mints"]))
        running_mints = cs["mints"]

    total_dt = time.time() - total_t0
    assert total_dt < 10.0, "the 3-shape vq scenario took %.3fs (bound 10s)" % total_dt
    assert running_mints == mints0 + 3, "all three structurally-distinct shapes must mint"

    ep1 = s.node(ag)["attrs"].get("codebook_epoch") or 0.0
    assert ep1 - ep0 <= 6, (
        "codebook_epoch grew by %r across 3 novel shapes (bound 6, generous over "
        "the measured +3)" % (ep1 - ep0))

    # --- dedup direction: a repeat of the FIRST shape under a fresh, unique
    # key (the adapter's own discipline) must recognize, not re-mint.
    o_repeat = SV.ingest(s, ag, _TROMINO, "tromino_repeat_key")
    native.run_rules()
    r = SV.read_outcome(s, o_repeat)
    cs_after = SV.codebook_state(s)
    assert cs_after["mints"] == running_mints, (
        "a repeat of an already-seen shape (new key) must NOT increase mints: "
        "%d -> %d" % (running_mints, cs_after["mints"]))
    assert r["covered_by"] == "tromino", r
