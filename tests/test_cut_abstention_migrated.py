"""GRAPH-RESIDENT ABSTENTION ON A DISCONTINUED PRIOR — the gates.

`VISION_CUT_ABSTENTION_PREREG.md`. These are the checks that must be able to
FAIL, per the standing lesson that a gate which has never been able to fail has
not been tested: each one is written so that deleting the thing it protects
turns it red, and the two that could be satisfied vacuously carry an explicit
non-vacuity assertion beside them.

Not in `scripts/rung7_vision_bench.sh`'s explicit file list — that oracle stays
at 222.
"""
from __future__ import annotations

import json
import os
import random
import re

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "vision_cut_abstention.json")


def _mk(armed, frames, *, verdict="ncc"):
    from domains import verdict_comparator_world as vw
    from domains.cut_abstention_world import CutAbstentionWorld
    w = CutAbstentionWorld(verdict, armed)
    w.hold_sequence(frames)
    return w, vw


def _cut_sequence(n=12, cut_at=6, seed=73001):
    """A sequence that is near-static, then DISCONTINUOUS at one step."""
    rng = np.random.RandomState(seed)
    a = rng.randint(0, 256, (24, 24)).astype(float)
    b = rng.randint(0, 256, (24, 24)).astype(float)
    return [np.clip((a if t <= cut_at else b) + rng.normal(0, 1.0, a.shape),
                    0, 255) for t in range(n)]


def _present_probe(w, vw, frames, t, d, span):
    qs = [vw.quantize(f) for f in frames]
    gs = list(frames)
    origins = list(vw.region_origins())
    codebook = [(qs[t][r:r + vw.REGION, c:c + vw.REGION],
                 gs[t][r:r + vw.REGION, c:c + vw.REGION]) for r, c in origins]
    order = list(range(16))
    random.Random(73002).shuffle(order)
    w.hold(codebook, order)
    tj = min(t + d, len(frames) - 1)
    qp, gp = vw.pad_edge(qs[tj], vw.RHO), vw.pad_edge(gs[tj], vw.RHO)
    for i, (r0, c0) in enumerate(origins):
        orbit = vw.orbit_windows(qp, gp, (r0, c0), vw.RHO, pad=vw.RHO)
        w.present(orbit, truth=i, tag=f"A1|d{d}|{i}", kind="A1", span=span)


# --- §13: THE THRESHOLD FALLS OUT ------------------------------------------ #
def test_no_numeric_threshold_is_written_anywhere_in_the_seed():
    """The §13 claim, checked rather than asserted: the ONLY numeric literals
    the seed's rules may carry are structural (0/1 counts, the exponent 2, the
    -1 sentinel of an empty upper class, the 1.0 that turns a correlation into
    a residual). No motion magnitude, no percentile, no cutoff."""
    seed = json.load(open(SEED))
    lits = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Lit" and isinstance(o.get("value"), (int, float)) \
                    and not isinstance(o.get("value"), bool):
                lits.append(float(o["value"]))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(seed["rules"])
    allowed = {0.0, 1.0, 2.0, -1.0}
    assert set(lits) <= allowed, f"non-structural numeric literal in the seed: {sorted(set(lits) - allowed)}"
    # NON-VACUITY: the walker must actually be finding literals, or this gate
    # passes on an empty set and proves nothing.
    assert len(lits) >= 5, "the literal walker found almost nothing — it is broken"


def test_the_threshold_is_a_value_the_data_supplied():
    """`ca_otsu` must take the threshold from a FrameStep's own `mag`. If the
    rule were changed to write a constant this fails."""
    seed = json.load(open(SEED))
    rule = next(r for r in seed["rules"] if r["name"] == "ca_otsu")
    eff = next(e for e in rule["effects"] if e[2] == "cut_threshold")
    term = eff[3]["__term__"]
    assert term["type"] == "Attr" and term["key"] == "mag"
    assert term["node"]["type"] == "Argmax"


def test_in_graph_otsu_reproduces_the_numpy_partition_on_the_real_corpora():
    """The in-graph Otsu and the committed numpy Otsu must agree on WHICH
    steps are cuts. Runs on the committed motion arrays, so it needs no video.
    """
    from domains import reflective_faculty as rf
    from substrate.boot_core import boot_core
    src = os.path.join(ROOT, "results", "verdict_comparator_video.json")
    if not os.path.exists(src):
        pytest.skip("verdict_comparator_video.json absent")
    meas = json.load(open(src))
    seed = json.load(open(SEED))
    rule = next(r for r in seed["rules"] if r["name"] == "ca_otsu")
    otsu = next(e for e in rule["effects"] if e[2] == "cut_threshold")[3]["__term__"]
    n_checked = 0
    for cid, m in meas["motion"].items():
        step = m["step"]
        s, ag = boot_core()
        native = rf._native_eval2(s)
        for t, x in enumerate(step):
            s.add_node("FrameStep", {"t": t, "mag": float(x)})
        g = float(native.evaluate(otsu, {}))
        p = m["otsu_threshold"]
        assert {t for t, x in enumerate(step) if x > g} == \
               {t for t, x in enumerate(step) if x > p}, cid
        n_checked += 1
    assert n_checked == 2, "expected both corpora"


# --- the mechanism ---------------------------------------------------------- #
def test_the_graph_computes_the_motion_and_marks_the_discontinuity():
    frames = _cut_sequence()
    w, _vw = _mk("mag", frames)
    w.run()
    sr = w.step_readout()
    ref = [float(np.mean(np.abs(frames[t + 1] - frames[t])))
           for t in range(len(frames) - 1)]
    got = [s["mag"] for s in sr["steps"]]
    assert got == pytest.approx(ref, abs=1e-9), "graph motion != numpy motion"
    assert [s["t"] for s in sr["steps"] if s["is_cut"]] == [6]


def test_a_probe_spanning_the_cut_is_refused_and_one_outside_it_is_not():
    frames = _cut_sequence()
    for d, span, expect in ((8, range(0, 8), True), (3, range(0, 3), False)):
        w, vw = _mk("mag", frames)
        _present_probe(w, vw, frames, 0, d, span)
        w.run()
        rows = [r for r in w.read() if r["kind"] == "A1"]
        refused_by_rule = [r for r in rows
                           if r["abstain_reason"] == "prior_invalidated"]
        assert bool(refused_by_rule) is expect, (d, len(refused_by_rule))
        if expect:
            assert all(r["answer"] == "refused" for r in refused_by_rule)


def test_the_abstention_leaves_a_trace_the_existing_scanner_finds():
    """The observability defect: `VISION_REDUNDANCY_RESULTS.md` ARM 4 found the
    marker inventory EMPTY in all 26 runs. The inventory is taken with the
    redundancy rung's OWN regex, unchanged."""
    frames = _cut_sequence()
    w, vw = _mk("mag", frames)
    _present_probe(w, vw, frames, 0, 8, range(0, 8))
    w.run()
    inv = w.marker_inventory()
    assert inv.get("type:Refusal", 0) > 0, inv
    # and the node carries WHY, not merely THAT
    ref = [w.s.node(n)["attrs"] for n in w.s.nodes("Refusal")]
    assert all(a.get("reason") == "prior_invalidated" for a in ref)
    assert all(a.get("statistic") == "mag" for a in ref)


def test_inert_is_byte_identical_off_the_marked_steps():
    """§9. The seed LOADED BUT INERT must leave every row untouched, and the
    ARMED run must leave every row whose span was not marked untouched."""
    frames = _cut_sequence()
    fields = ("tag", "kind", "truth", "said", "answer", "refused", "graph_max",
              "noise_floor", "status", "ref_idx", "ref_max", "true_score",
              "true_is_max")
    out = {}
    for armed in ("", "mag"):
        w, vw = _mk(armed, frames)
        # BOTH in one substrate: d=8 spans the cut and MUST move, d=3 spans no
        # cut and MUST NOT. Testing only the second would pass on a rule that
        # never fires at all.
        _present_probe(w, vw, frames, 0, 3, range(0, 3))
        _present_probe(w, vw, frames, 0, 8, range(0, 8))
        w.run()
        out[armed] = w.read()
    a, b = out[""], out["mag"]
    assert len(a) == len(b) and len(a) > 0
    n_same = n_moved = 0
    for x, y in zip(a, b):
        if y.get("spans_marked", 0):
            n_moved += 1
            continue
        assert [x[f] for f in fields] == [y[f] for f in fields], x["tag"]
        n_same += 1
    # NON-VACUITY on both sides: something was protected AND something moved.
    assert n_same > 0 and n_moved > 0, (n_same, n_moved)


def test_a_constant_sequence_marks_nothing():
    """The degenerate end of arm 4: with every step identical, no candidate
    split has a non-empty upper class, the threshold stays 0.0 and `mag > 0.0`
    is false everywhere. The rule declines to invent a cut here."""
    f = np.full((24, 24), 128.0)
    w, _vw = _mk("mag", [f.copy() for _ in range(10)])
    w.run()
    assert w.step_readout()["n_cut"] == 0


# --- the architecture rule -------------------------------------------------- #
def test_the_adapter_takes_no_decision_over_graph_state():
    """A source audit in the ink rung's form. The adapter may translate; it may
    not branch on what the graph holds. In particular it must never read
    `is_cut`, `cut_threshold` or `mag` to decide anything, and must not compute
    a motion or a threshold itself."""
    src = open(os.path.join(ROOT, "domains", "cut_abstention_world.py")).read()
    body = "\n".join(ln for ln in src.split("\n")
                     if not ln.strip().startswith("#"))
    # strip docstrings — prose naming these words is not code reading them
    body = re.sub(r'"""(?:.|\n)*?"""', "", body)
    for forbidden in ("np.mean", "np.abs", "otsu", "threshold >",
                      "if is_cut", "np.diff"):
        assert forbidden not in body, f"adapter computes/branches on {forbidden!r}"
    # `is_cut` / `cut_threshold` may appear ONLY in the read-back methods and
    # in the initial attribute dict `hold_sequence` writes. Anywhere else --
    # and in particular inside `present`, which decides what goes into the
    # graph -- would be the adapter reading the graph's verdict and acting on
    # it, which is the thing this whole rung claims not to do.
    allowed_methods = {"read", "step_readout", "hold_sequence"}
    cur = None
    for ln in body.split("\n"):
        m = re.match(r"    def (\w+)\(", ln)
        if m:
            cur = m.group(1)
        if "is_cut" in ln or "cut_threshold" in ln:
            assert cur in allowed_methods, f"{cur}: {ln}"
    # NON-VACUITY: if the names vanished from the adapter entirely this gate
    # would pass while protecting nothing.
    assert "is_cut" in body and "cut_threshold" in body


# --------------------------------------------------------------------------- #
#  §12.3 — PROVENANCE, PINNED TO BOTH ENDPOINTS
# --------------------------------------------------------------------------- #
import subprocess  # noqa: E402

#: This rung's OWN commit range, BOTH ENDPOINTS FIXED (§12.3). A claim of the
#: form "this rung added no Rust" is about THIS RUNG'S DIFF; tested against a
#: mutable tree it would instead test whether anyone has done any work since,
#: and would eventually make a false accusation against an innocent rung.
#: `tests/test_provenance_endpoint_guard_migrated.py` FAILS any range ending at
#: HEAD, so both are pinned shas and HEAD appears only in a reachability check.
BASE_SHA = "212212e3"
PREREG_SHA = "9f0bc789"
RUNG_SHA = "3df3945f"

OWNED = {
    "research/experiments/gamma-substrate/VISION_CUT_ABSTENTION_PREREG.md",
    "research/experiments/gamma-substrate/VISION_CUT_ABSTENTION_RESULTS.md",
    "research/experiments/gamma-substrate/seeds/vision_cut_abstention.json",
    "research/experiments/gamma-substrate/domains/cut_abstention_world.py",
    "research/experiments/gamma-substrate/scripts/cut_abstention_measure.py",
    "research/experiments/gamma-substrate/scripts/cut_abstention_analyse.py",
    "research/experiments/gamma-substrate/scripts/cut_abstention_diagnose.py",
    "research/experiments/gamma-substrate/tests/test_cut_abstention_migrated.py",
    "research/experiments/gamma-substrate/results/cut_abstention_video.json",
    "research/experiments/gamma-substrate/results/cut_abstention_stress.json",
    "research/experiments/gamma-substrate/results/cut_abstention_diagnose.json",
    "research/experiments/gamma-substrate/results/cut_abstention_analysis.json",
    "research/experiments/gamma-substrate/results/cut_rows_SHA256SUMS.txt",
}

_UNPINNED = RUNG_SHA.startswith("RUNG_SHA")


def _git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


@pytest.mark.skipif(_UNPINNED, reason="RUNG_SHA not yet pinned")
def test_this_rung_adds_NO_rust():
    files = _git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/").split()
    rust = [f for f in files if f.endswith(".rs") or f.endswith("Cargo.toml")]
    assert rust == [], f"this rung claims no Rust but touched: {rust}"


@pytest.mark.skipif(_UNPINNED, reason="RUNG_SHA not yet pinned")
def test_this_rung_touches_only_files_it_OWNS():
    files = set(_git("diff", "--name-only", BASE_SHA, RUNG_SHA,
                     "--", ":/").split())
    assert files <= OWNED, f"this rung touched files it does not own: {files - OWNED}"


@pytest.mark.skipif(_UNPINNED, reason="RUNG_SHA not yet pinned")
def test_this_rung_edits_no_other_rungs_seed():
    """The seed this rung adds is its OWN. Every other rung's seed -- and in
    particular `vision_verdict_comparator.json`, whose V3 is the baseline every
    increment here is measured against -- must be untouched, or the baseline is
    not the published one."""
    files = _git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/").split()
    seeds = [f for f in files if "/seeds/" in f]
    assert seeds == ["research/experiments/gamma-substrate/seeds/"
                     "vision_cut_abstention.json"], \
        f"this rung edited a seed it does not own: {seeds}"


@pytest.mark.skipif(_UNPINNED, reason="RUNG_SHA not yet pinned")
def test_the_pinned_shas_are_reachable():
    for sha in (BASE_SHA, PREREG_SHA, RUNG_SHA):
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                       cwd=ROOT, check=True)


def test_the_seed_is_not_in_the_default_boot_set():
    """§9. Loading the core seeds must not bring this rung's machinery with
    them, or every existing result silently acquires an abstention layer."""
    from substrate.boot_core import boot_core
    s, _ag = boot_core()
    assert not list(s.nodes("CutParams"))
    assert not list(s.nodes("FrameStep"))


def test_the_seed_ships_inert():
    seed = json.load(open(SEED))
    params = [n for n in seed["nodes"] if n["type"] == "CutParams"]
    assert len(params) == 1
    assert params[0]["attrs"]["armed"] == "", \
        "the seed must ship armed='' -- matching no arm"
