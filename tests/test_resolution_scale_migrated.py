"""Gates for the resolution-scale rung (`VISION_RESOLUTION_SCALE_PREREG.md`).

Every gate here is POSITIVE-CONTROLLED where it can be: the standing lesson is
that *a gate that has never been ABLE to fail has not been tested*. The
region-name gate therefore asserts BOTH that the new parse is right AND that
the OLD parse was wrong on the same input -- so the test demonstrably
discriminates.
"""
from __future__ import annotations

import importlib.util
import os
import random
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains import verdict_comparator_world as vw  # noqa: E402


def _analyse():
    p = os.path.join(ROOT, "scripts", "resolution_scale_analyse.py")
    spec = importlib.util.spec_from_file_location("rsa", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --------------------------------------------------------------- name width
def _old_said_parse(said):
    """The PRE-FIX parse, kept verbatim so the fix can be shown to matter."""
    return int(said[1:3]) if isinstance(said, str) and said.startswith("r") else None


def _old_ans_parse(ans):
    return (int(ans[1:3]) if isinstance(ans, str) and len(ans) == 3
            and ans[0] == "r" and ans[1:3].isdigit() else None)


def _new_said_parse(said):
    return (int(said[1:]) if isinstance(said, str) and said.startswith("r")
            and said[1:].isdigit() else None)


def _new_ans_parse(ans):
    return (int(ans[1:]) if isinstance(ans, str) and ans[:1] == "r"
            and ans[1:].isdigit() else None)


def test_name_width_is_byte_identical_below_100_regions():
    """The fix MUST NOT move any landed number: below 100 entries the width is
    still 2, so every name is the string the incumbent wrote."""
    for n in (1, 2, 16, 64, 99):
        width = max(2, len(str(max(n - 1, 0))))
        assert width == 2, f"n={n} width={width}"
        for i in range(n):
            assert f"r{i:0{width}d}" == f"r{i:02d}"


def test_name_width_widens_above_100_regions():
    """PRECISION CORRECTION to the pre-registration, which said the parse
    breaks at ">=100 regions". It breaks when the max INDEX reaches 100, i.e.
    at n > 100: a 100-region codebook is indexed 0..99 and is still safe. The
    144-region configuration is past the threshold either way, so no measured
    quantity depends on this, but the threshold is stated correctly here."""
    assert max(2, len(str(99))) == 2          # n=100 -> indices 0..99 -> safe
    for n, want in ((101, 3), (144, 3), (1001, 4)):
        assert max(2, len(str(max(n - 1, 0)))) == want


def test_old_parse_is_WRONG_at_three_digits_and_new_parse_is_RIGHT():
    """POSITIVE CONTROL. Without this the width gate could pass vacuously."""
    # r143 under the old 2-char field reads as region 14 -- silently, no error.
    assert _old_said_parse("r143") == 14          # the defect, reproduced
    assert _new_said_parse("r143") == 143         # the fix
    # the answer parse was worse: it required len == 3 EXACTLY, so every
    # 3-digit answer returned None -- i.e. "no answer" for the whole run.
    assert _old_ans_parse("r143") is None         # the defect, reproduced
    assert _new_ans_parse("r143") == 143          # the fix
    # and both parses must still reject the abstention token.
    assert _old_ans_parse("refused") is None
    assert _new_ans_parse("refused") is None
    # below 100 the two parses agree exactly -- that is the byte-identity claim.
    for i in range(100):
        s = f"r{i:02d}"
        assert _old_said_parse(s) == _new_said_parse(s)
        assert _old_ans_parse(s) == _new_ans_parse(s)


def test_world_writes_widened_names_and_reads_them_back():
    """End-to-end at 144 regions: the graph's choice must parse back to the
    reference's choice. This is the configuration that first reaches the bug."""
    grid, region = 72, 6
    vw.GRID, vw.REGION, vw.N_CELLS = grid, region, region * region
    rng = np.random.RandomState(79000)
    frame = rng.randint(0, 256, (grid, grid)).astype(float)
    q, g = vw.quantize(frame), frame
    origins = list(vw.region_origins(shape=(grid, grid), region=region))
    assert len(origins) == 144
    codebook = [(q[r:r + region, c:c + region], g[r:r + region, c:c + region])
                for r, c in origins]
    order = list(range(len(origins)))
    random.Random(79000).shuffle(order)
    w = vw.VerdictWorld("ncc")
    w.hold(codebook, order)
    names = [w.s.node(n)["attrs"]["name"] for n in w.s.nodes("VdSignature")]
    assert any(len(nm) == 4 for nm in names), "no 3-digit name was written"
    qp, gp = vw.pad_edge(q, vw.RHO), vw.pad_edge(g, vw.RHO)
    for i, (r0, c0) in enumerate(origins[:8]):
        orbit = vw.orbit_windows(qp, gp, (r0, c0), vw.RHO, region=region,
                                 pad=vw.RHO)
        w.present(orbit, truth=i, tag=f"A1|{i}", kind="A1")
    w.run()
    rows = w.read()
    assert len(rows) == 8
    for r in rows:
        assert r["said_idx"] is not None, "graph answer failed to parse"
        assert r["said_idx"] == r["ref_idx"], "graph disagrees with reference"
    vw.GRID, vw.REGION, vw.N_CELLS = 24, 6, 36     # restore the incumbent


# ------------------------------------------------------------------- axes
def test_the_two_axes_are_actually_different_configurations():
    """SCALE varies region COUNT at fixed cells; GRAIN varies CELLS at fixed
    count. If a refactor ever collapsed them this rung would be meaningless."""
    spec = importlib.util.spec_from_file_location(
        "rsm", os.path.join(ROOT, "scripts", "resolution_scale_measure.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    by = {c: (g, r, a) for c, g, r, a in m.CONFIGS}
    scale = [by[c] for c in ("B", "S48", "S72")]
    grain = [by[c] for c in ("B", "G48", "G72")]
    # scale: cells/region constant, region count strictly increasing
    assert len({r * r for _g, r, _a in scale}) == 1
    counts = [(g // r) ** 2 for g, r, _a in scale]
    assert counts == sorted(counts) and len(set(counts)) == 3
    # grain: region count constant, cells/region strictly increasing
    assert len({(g // r) ** 2 for g, r, _a in grain}) == 1
    cells = [r * r for _g, r, _a in grain]
    assert cells == sorted(cells) and len(set(cells)) == 3
    # and they share exactly one configuration: the origin
    assert set(scale) & set(grain) == {by["B"]}


# ------------------------------------------------------- effective-n method
def test_icc_decomposition_separates_blocked_from_independent():
    """POSITIVE CONTROL for the effective-n instrument itself. Blocked data
    must yield high ICC and n_eff far below n; independent data must yield
    ICC near zero and n_eff near n. Without this the gate could report
    anything and nobody would know."""
    rsa = _analyse()
    rng = np.random.RandomState(79001)
    blk = [t // 10 for t in range(50)]
    # BLOCKED: each block has its own mean, tiny within-block noise.
    offs = [0.0, 0.3, -0.25, 0.15, -0.1]
    blocked = [offs[b] + rng.normal(0, 0.005) for b in blk]
    d1 = rsa.icc_decompose(blocked, blk)
    assert d1["icc"] > 0.9, d1
    assert d1["n_eff"] < 10, d1
    # INDEPENDENT: one distribution, no block structure.
    indep = list(rng.normal(0, 0.1, 50))
    d2 = rsa.icc_decompose(indep, blk)
    assert abs(d2["icc"]) < 0.4, d2
    assert d2["n_eff"] > 25, d2
    # the instrument must ORDER them correctly -- that is what G2 relies on
    assert d1["n_eff"] < d2["n_eff"]
    assert d1["spread_ratio"] > d2["spread_ratio"]


def test_effective_n_is_bounded_by_n():
    rsa = _analyse()
    blk = [t // 10 for t in range(50)]
    flat = [0.5] * 50
    d = rsa.icc_decompose(flat, blk)
    # a perfectly constant series has no variance anywhere; the instrument
    # must not silently return a fabricated n_eff above n.
    assert (not np.isfinite(d["n_eff"])) or d["n_eff"] <= 50 + 1e-9


# ------------------------------------------------------------ results shape
@pytest.mark.parametrize("cid", ["C1", "C2"])
def test_committed_results_carry_provenance_and_both_axes(cid):
    p = os.path.join(ROOT, "results", "resolution_scale_all.json")
    if not os.path.exists(p):
        pytest.skip("confirmatory run not present in this tree")
    import json
    d = json.load(open(p))
    assert d["prereg"] == "VISION_RESOLUTION_SCALE_PREREG.md"
    assert d["provenance"].startswith("engine ")
    axes = {c["axis"] for c in d["configs"]}
    assert {"scale", "grain", "origin"} <= axes
    for cfg in ("B", "S48", "S72", "G48", "G72"):
        k = f"{cid}|{cfg}"
        assert k in d["cells"], k
        c = d["cells"][k]
        # cost must be RECORDED per configuration, counted (G4)
        assert c["cell_comparisons_per_probe"] > 0
        assert c["graph_run_ms_mean"] > 0
        assert "loadavg" in c
