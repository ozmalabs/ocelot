"""VERDICT COMPARATOR — the gate.

`VISION_VERDICT_PREREG.md`. Written INDEPENDENTLY of the runner rather than as
assertions over its output.

Covers, in order: §9 inertness; the architecture rule (the DECISION and the
ABSTENTION are the seed's, not the adapter's); that the tie `Count` the source
rung retracted is GONE rather than merely unused; that each verdict computes
what it claims, checked against an independent implementation; that V0 is the
incumbent's score exactly; **the proposal layer is identical across arms**,
which is the whole premise of the rung; the refusal is ALIVE and its control is
not a tautology; two dead-instrument controls; and a provenance self-audit
pinned to BOTH ENDPOINTS (§12.3).
"""
from __future__ import annotations

import json
import math
import os
import random
import subprocess
import tempfile

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "vision_verdict_comparator.json")

#: This rung's OWN commit range, BOTH ENDPOINTS FIXED (§12.3). The lower bound
#: is the BRANCH BASE: the seed, adapter and runner land WITH the
#: pre-registration so the diff is auditable before any number is taken, and
#: these gates claim things about the WHOLE rung.
#: `tests/test_provenance_endpoint_guard_migrated.py` FAILS any range ending at
#: HEAD, so both are pinned shas and HEAD appears only in a reachability check.
BASE_SHA = "7018fb48"
PREREG_SHA = "59cebc76"
RUNG_SHA = "f900de0e"

OWNED = {
    "research/experiments/gamma-substrate/VISION_VERDICT_PREREG.md",
    "research/experiments/gamma-substrate/VISION_VERDICT_RESULTS.md",
    "research/experiments/gamma-substrate/seeds/vision_verdict_comparator.json",
    "research/experiments/gamma-substrate/domains/verdict_comparator_world.py",
    "research/experiments/gamma-substrate/scripts/verdict_comparator_measure.py",
    "research/experiments/gamma-substrate/scripts/verdict_comparator_analyse.py",
    "research/experiments/gamma-substrate/tests/test_verdict_comparator_migrated.py",
    "research/experiments/gamma-substrate/results/verdict_comparator_pilot.json",
    "research/experiments/gamma-substrate/results/verdict_rows_SHA256SUMS.txt",
    "research/experiments/gamma-substrate/results/verdict_comparator_c3.json",
    "research/experiments/gamma-substrate/results/verdict_comparator_video.json",
    "research/experiments/gamma-substrate/results/verdict_analysis_c3.json",
    "research/experiments/gamma-substrate/results/verdict_analysis_video.json",
}


def _vw():
    from domains import verdict_comparator_world as vw
    return vw


def _seed():
    with open(SEED_PATH) as fh:
        return json.load(fh)


def _frame(seed, n=24):
    rs = np.random.RandomState(seed)
    return rs.randint(0, 256, (n, n)).astype(float)


def _setup(verdict, base, probe, *, manifest=None, seed=1):
    """Hold `base`'s 16 regions, present `probe`'s 16 regions plus the two
    independent noise draws the refusal floor needs."""
    vw = _vw()
    qb, gb = vw.quantize(base), np.asarray(base, float)
    qp, gp = vw.quantize(probe), np.asarray(probe, float)
    origins = vw.region_origins()
    cb = [(qb[r:r + vw.REGION, c:c + vw.REGION],
           gb[r:r + vw.REGION, c:c + vw.REGION]) for r, c in origins]
    w = vw.VerdictWorld(verdict, manifest=manifest)
    rng = random.Random(seed)
    order = list(range(16))
    rng.shuffle(order)
    w.hold(cb, order)
    qpp, gpp = vw.pad_edge(qp, vw.RHO), vw.pad_edge(gp, vw.RHO)
    for i, o in enumerate(origins):
        w.present(vw.orbit_windows(qpp, gpp, o, vw.RHO), truth=i,
                  tag=f"A1|{i}", kind="A1")
    for label, sd in (("G2c", 11), ("G2t", 22)):
        r2 = np.random.RandomState(sd)
        nq = r2.randint(0, vw.K_LEVELS, (24, 24))
        ng = r2.randint(0, 256, (24, 24)).astype(float)
        nqp, ngp = vw.pad_edge(nq, vw.RHO), vw.pad_edge(ng, vw.RHO)
        for i, o in enumerate(origins):
            w.present(vw.orbit_windows(nqp, ngp, o, vw.RHO), truth=i,
                      tag=f"{label}|{i}", kind=label)
    w.run()
    return w, w.read()


def _acc(rows, kind="A1"):
    sel = [r for r in rows if r["kind"] == kind]
    return sum(1 for r in sel if r["said_idx"] == r["truth"]) / len(sel)


# --------------------------------------------------------------------------- #
#  §9 — the seed is inert until a measurement arms it
# --------------------------------------------------------------------------- #
def test_seed_ships_off_by_default():
    raw = _seed()
    params = [n for n in raw["nodes"] if n["type"] == "VerdictParams"]
    assert len(params) == 1
    assert params[0]["attrs"]["verdict"] == "", \
        "the seed must ship a verdict that matches NO arm"


def test_seed_is_not_in_the_default_boot_set():
    from substrate.boot_core import boot_core
    s, _ag = boot_core()
    assert not list(s.nodes("VerdictParams")), \
        "this seed must not be boot-loaded — committed results would move"


def test_every_score_rule_is_guarded_on_the_armed_verdict():
    """Exactly one arm can be live per substrate, or the arms are not arms."""
    raw = _seed()
    scored = [r for r in raw["rules"]
              if r["name"].startswith(("vd_score_", "vd_identify_"))]
    assert len(scored) == 8, f"expected 4 score + 4 identify, got {len(scored)}"
    for rule in scored:
        blob = json.dumps(rule["where"])
        assert "VerdictParams" in blob and "verdict" in blob, \
            f"{rule['name']} is not guarded on the armed verdict"


# --------------------------------------------------------------------------- #
#  The architecture rule — the DECISION and the ABSTENTION are the seed's
# --------------------------------------------------------------------------- #
def test_the_decision_lives_in_the_seed():
    raw = _seed()
    for name in ("vd_identify_hamming", "vd_identify_ssdq",
                 "vd_identify_ssdg", "vd_identify_ncc"):
        rule = next(r for r in raw["rules"] if r["name"] == name)
        assert "Argmax" in json.dumps(rule["effects"]), \
            f"{name} does not decide with an Argmax"


def test_the_abstention_lives_in_the_seed_and_writes_NO_constant():
    """§13: the refusal floor is the system's own MEASURED noise floor. If a
    number appears in this rule, the threshold was chosen, not measured."""
    raw = _seed()
    rule = next(r for r in raw["rules"] if r["name"] == "vd_refuse")
    blob = json.dumps(rule["effects"])
    assert "IfThenElse" in blob and "G2c" in blob
    lits = [v for v in _all_lit_values(rule["effects"])
            if isinstance(v, (int, float)) and not isinstance(v, bool)]
    # The ONLY numeric literal admissible here is the MaxOver `default`
    # sentinel, which is not a threshold: it is the value when the source is
    # empty, and it is never compared against a real score.
    assert set(lits) <= {-1.0e18}, \
        f"vd_refuse writes a numeric threshold: {lits} — that is a magic number"


def _all_lit_values(obj):
    out = []
    if isinstance(obj, dict):
        if obj.get("type") == "Lit":
            out.append(obj.get("value"))
        for v in obj.values():
            out.extend(_all_lit_values(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_all_lit_values(v))
    return out


#: `read()` is the ONE function this adapter's own docstring licenses to touch
#: the graph ("Mechanical read-back"), so it is the ONE exemption.
#:
#: THE OTHER FOUR ARE GONE, AND THAT IS A STRENGTHENING, NOT AN EDIT OF
#: SOMEONE'S ALLOWLIST. `encode`, `unit_centered`, `ref_score` and `ref_choice`
#: were exempt because the incumbent predicate was a SUBSTRING of `ast.dump`
#: over a whole `if` SUBTREE, which flags conditionals that merely sit near a
#: read. Measured after the rewrite: with NO exemptions at all, the only
#: conditions that trace to a graph read in this file are the two inside
#: `read()` (lines 403 and 412). The four names hid nothing, so dropping them
#: removes four places a future decision could land unseen.
_GRAPH_EXEMPT = frozenset({"read"})


def test_adapter_takes_no_branch_on_graph_state():
    """The adapter may read the graph only in `read()`, and only to copy
    attributes out. No conditional anywhere may consult a graph attribute.

    THIS GATE WAS TOTALLY DEAD AND IS NOW ALIVE BY CONSTRUCTION.
    Its predicate was::

        if "node(" in ast.dump(node) or "get_attr" in ast.dump(node)

    **`node(` cannot occur in `ast.dump` output for any program** -- `ast.dump`
    renders `s.node(x)` as ``Attribute(..., attr='node')``, never as `node(`.
    Verified by construction against `s.node(x)`, `a.get_attr(b)`, `node(1)`
    and `x.node`: all four are `False`. And `get_attr` -- the half that COULD
    match -- appears nowhere in `verdict_comparator_world.py`, so neither
    disjunct had ever been able to fire on the file this gate audits. It
    carried a five-name exemption list, which means its author believed it did.

    The replacement checks the invariant the docstring states rather than a
    spelling of it: **no path runs from a graph read to a condition**, with
    transitive closure over bindings (so `v = s.node(x)["attrs"]["a"]` then
    `if v > 0` is seen -- the exact spelling that walked through the paint
    gate), and every TEST POSITION the grammar has as the sink (`if`, ternary,
    `while`, `assert`, comprehension guard -- four of which the incumbent
    `ast.If`/`ast.IfExp` enumeration was blind to).

    Aliveness is established in
    `tests/test_gate_audit_migrated.py::test_a_graph_read_reaching_a_condition_is_SEEN`
    and its negative control, by planting each spelling and reverting."""
    import sys
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from gate_audit import graph_decision_findings
    src = open(os.path.join(ROOT, "domains", "verdict_comparator_world.py")).read()
    bad = graph_decision_findings(src, _GRAPH_EXEMPT)
    assert not bad, "adapter branches on graph state:\n" + "\n".join(
        f"  {fn}:{ln}  {expr}    <- {chain}" for fn, ln, expr, chain in bad)


def test_the_retracted_tie_count_is_GONE_not_merely_unused():
    """The source rung's §5 retracted `icg_ntied`: it counts tied ORBIT MEMBERS,
    is 1 by construction at rho=0, and is computed by the very Argmax it
    diagnoses. A diagnostic must not be computed by the component it checks, so
    this seed must compute NO tie statistic at all.

    THE SELECTOR IS THE RULES, NOT THE FILE (§12: a selector that matches by
    substring is not a selector). The first version of this test searched the
    whole manifest and FAILED on the word "icg_ntied" inside the seed's own
    DESCRIPTION, where it appears to explain why the count was removed. The fact
    was verified first -- no rule computes a tie count -- and only then was the
    gate narrowed to what the claim is actually about (§12.3's order)."""
    raw = _seed()
    for rule in raw["rules"]:
        body = json.dumps({"where": rule.get("where"),
                           "effects": rule["effects"]})
        assert "ntied" not in body and "n_tied" not in body, \
            f"{rule['name']} computes a tie statistic"
        for eff in rule["effects"]:
            key = str(eff[2]) if len(eff) > 2 else ""
            assert "tied" not in key, f"{rule['name']} writes a tie statistic"


# --------------------------------------------------------------------------- #
#  Each verdict computes what it CLAIMS — against an independent implementation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("verdict", ["hamming", "ssdq", "ssdg", "ncc"])
def test_graph_score_equals_the_outside_reference_exactly(verdict):
    """The identity -||p-c||^2 = 2<p,c> - ||p||^2 - ||c||^2 that lets the seed
    score with ONE Dot is EXACT. If the graph and an independent Python
    implementation ever disagree, every number this rung takes is void."""
    base = _frame(70901)
    _w, rows = _setup(verdict, base, base)
    scored = [r for r in rows if r["graph_max"] is not None]
    assert scored
    for r in scored:
        assert abs(float(r["graph_max"]) - float(r["ref_max"])) < 1e-6, \
            f"{verdict}: graph {r['graph_max']} != reference {r['ref_max']}"


def test_V0_is_the_incumbent_score_exactly():
    """V0 must be the published Q2 arm byte-for-byte, or the control is not a
    control. Both compute `covered_count` over the identical relation system."""
    vw = _vw()
    from domains import invariant_comparator_world as iw
    tile = _frame(70902, 6)
    q = vw.quantize(tile)
    assert vw.sig_of(q) == iw.sig_of(q), \
        "V0's encoding has drifted from the incumbent's"


def test_ncc_is_invariant_to_an_affine_luminance_map_and_the_others_are_not():
    """THE MECHANISM CLAIM, stated as a discriminating test. An affine map
    a*p+b with a>0 is the identity-PRESERVING nuisance of natural video; NCC
    quotients it exactly, and the three other arms do not."""
    vw = _vw()
    rs = np.random.RandomState(70903)
    tile = rs.randint(0, 200, (6, 6)).astype(float)
    bright = np.clip(tile * 1.3 + 20.0, 0, 255)
    a = vw.encode(vw.quantize(tile), tile)
    b = vw.encode(vw.quantize(bright), bright)
    ncc = vw.ref_score(a, b, "ncc")
    assert ncc > 0.999, f"NCC is not affine-invariant: {ncc}"
    assert vw.ref_score(a, b, "ssdg") < -1.0, "SSD-grey ignored the gain change"
    assert vw.ref_score(a, b, "hamming") < 36.0, "Hamming ignored the gain change"


def test_a_flat_tile_is_flagged_and_scores_no_evidence_not_a_division():
    """§1.1: an absence off a guarded division is evidence of a lookup, not a
    measurement. A zero-variance tile has NO correlation, and must say so."""
    vw = _vw()
    flat = np.full((6, 6), 128.0)
    other = np.random.RandomState(70904).randint(0, 256, (6, 6)).astype(float)
    e_flat = vw.encode(vw.quantize(flat), flat)
    e_other = vw.encode(vw.quantize(other), other)
    assert e_flat["nflat"] == 1.0, "a flat tile was not flagged"
    assert e_other["nflat"] == 0.0
    assert vw.ref_score(e_flat, e_other, "ncc") == 0.0, \
        "a degenerate tile produced evidence it does not have"


# --------------------------------------------------------------------------- #
#  THE PREMISE OF THE RUNG — the proposal layer is identical across arms
# --------------------------------------------------------------------------- #
def test_the_candidate_set_is_IDENTICAL_across_all_four_arms():
    """"Hold the proposal fixed, vary only the verdict" is the whole design. It
    is CHECKED here, not asserted: the orbit geometry, the codebook and the
    seeded insertion order are functions of the inputs alone, so the hash of the
    candidate set must not depend on which arm consumes it."""
    import importlib.util as iu
    spec = iu.spec_from_file_location(
        "vcm", os.path.join(ROOT, "scripts", "verdict_comparator_measure.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    vw = _vw()
    base = _frame(70905)
    qb, gb = vw.quantize(base), np.asarray(base, float)
    origins = list(vw.region_origins())
    probes = m.c3_probes(qb, gb, 0, 70000)
    hashes = {v: m.check_proposal_identity(qb, gb, origins, probes, 70000)
              for v in vw.VERDICTS}
    assert len(set(hashes.values())) == 1, \
        f"the candidate set DIFFERS across arms: {hashes}"


def test_rho_is_the_measured_knee_and_is_held_fixed():
    assert _vw().RHO == 2, "rho must stay at the measured knee for this rung"
    assert len(_vw().orbit_offsets(2)) == 25


# --------------------------------------------------------------------------- #
#  REFUSAL — alive, and its control is NOT a tautology
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("verdict", ["hamming", "ssdq", "ssdg", "ncc"])
def test_refusal_is_ALIVE_answers_signal_and_declines_independent_noise(verdict):
    """A verdict that discriminates better by becoming more willing to answer
    has bought accuracy with false confidence. G2c DEFINES the floor, so it is
    excluded from the control -- the honest test is G2t, an INDEPENDENT draw
    that did not define it, against A1, which must be answered."""
    base = _frame(70906)
    _w, rows = _setup(verdict, base, base)
    a1 = [r for r in rows if r["kind"] == "A1"]
    g2t = [r for r in rows if r["kind"] == "G2t"]
    ref_a1 = sum(1 for r in a1 if r["refused"]) / len(a1)
    ref_g2t = sum(1 for r in g2t if r["refused"]) / len(g2t)
    assert ref_a1 < 0.5, f"{verdict}: refuses the identical frame ({ref_a1})"
    assert ref_g2t > 0.5, f"{verdict}: answers pure noise ({ref_g2t})"
    assert ref_g2t > ref_a1, f"{verdict}: refusal carries no signal"


def test_the_refusal_control_is_not_the_tautology_it_could_have_been():
    """G2c and G2t must be DIFFERENT draws. If they were the same, 'noise does
    not exceed the max over noise' would be true by construction and the control
    would be dead."""
    import importlib.util as iu
    spec = iu.spec_from_file_location(
        "vcm", os.path.join(ROOT, "scripts", "verdict_comparator_measure.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    vw = _vw()
    base = _frame(70907)
    qb, gb = vw.quantize(base), np.asarray(base, float)
    probes = m.c3_probes(qb, gb, 0, 70000)
    g2c = next(p for p in probes if p[1] == "G2c")
    g2t = next(p for p in probes if p[1] == "G2t")
    assert not np.array_equal(g2c[2], g2t[2]), \
        "the calibration and test noise draws are identical — a dead control"


# --------------------------------------------------------------------------- #
#  DEAD-INSTRUMENT CONTROLS — a gate only ever seen to pass has not been tested
# --------------------------------------------------------------------------- #
def _inverted_manifest(verdict):
    """The seed with the CANDIDATE-level `Argmax` replaced by `Argmin`: the held
    region that explains the observation WORST. Structurally identical
    otherwise, so what changes is the decision and nothing else."""
    from substrate.seed_loader import load_manifest_file
    raw = _seed()
    n = 0
    for rule in raw["rules"]:
        if rule["name"] != f"vd_identify_{verdict}":
            continue
        for eff in rule["effects"]:
            if len(eff) > 3 and isinstance(eff[3], dict):
                node = eff[3].get("__term__", {}).get("node")
                if isinstance(node, dict) and node.get("type") == "Argmax":
                    node["type"] = "Argmin"
                    n += 1
    assert n == 1, f"the inversion did not apply ({n} sites) — an inert control"
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(raw, fh)
        path = fh.name
    try:
        return load_manifest_file(path)
    finally:
        os.unlink(path)


@pytest.mark.parametrize("verdict", ["hamming", "ncc"])
def test_inverting_the_decision_turns_this_gate_RED(verdict):
    """POSITIVE CONTROL FOR THE GATE ITSELF (§12.3). The inversion is asserted
    to have APPLIED at exactly one site, so an inert control cannot masquerade
    as a passing one."""
    base = _frame(70908)
    _w, rows = _setup(verdict, base, base, manifest=_inverted_manifest(verdict))
    assert all(r["said"] is not None for r in rows), \
        "the inverted seed did not fire at all — the control is inert, not red"
    assert _acc(rows) < 1.0, \
        "the ceiling PASSED under an inverted decision — it is not a gate"


@pytest.mark.parametrize("verdict", ["hamming", "ssdq", "ssdg", "ncc"])
def test_the_ceiling_is_reachable_on_an_identical_frame(verdict):
    """§1: a floor is satisfied by DEATH; only the ceiling carries the gate."""
    base = _frame(70909)
    _w, rows = _setup(verdict, base, base)
    assert _acc(rows) >= 0.9, f"{verdict}: ceiling not reached ({_acc(rows)})"


@pytest.mark.parametrize("verdict", ["hamming", "ssdq", "ssdg", "ncc"])
def test_the_arm_is_alive_on_noise_not_collapsed_onto_one_answer(verdict):
    base = _frame(70910)
    _w, rows = _setup(verdict, base, base)
    g2t = [r for r in rows if r["kind"] == "G2t"]
    assert len({r["said"] for r in g2t}) >= 3, \
        f"{verdict}: answered noise with almost no variety — may be dead"


def test_a_truncated_aperture_is_LOUD_not_silent():
    """THE DEFECT THIS RUNG FOUND IN ITS OWN CONFIRMATORY DATA.

    `pad_edge(src, rho)` is only enough when the probe origin is NOT displaced.
    At d>0 the trailing-edge windows run past the padded array and numpy
    SILENTLY returns a short tile, so a 36-cell norm gets compared against a
    30-cell one. It was invisible to the incumbent's `covered_count` (a set
    overlap just contributes fewer tuples and both sides agree on a wrong
    number) and visible here only because this rung checks the graph against an
    independent reference on every trial.

    A guard that has never been ABLE to fire is not a guard, so this test drives
    the exact under-padded configuration and requires it to RAISE."""
    vw = _vw()
    q = vw.quantize(_frame(70911))
    g = np.asarray(_frame(70911), float)
    # UNDER-padded on purpose: pad by rho while displacing the origin by 2.
    qpad, gpad = vw.pad_edge(q, vw.RHO), vw.pad_edge(g, vw.RHO)
    origins = vw.region_origins()
    r0, c0 = origins[-1]
    with pytest.raises(ValueError, match="TRUNCATED APERTURE"):
        vw.orbit_windows(qpad, gpad, (r0, c0 + 2), vw.RHO)
    # Correctly padded: rho + the displacement. Every tile is full size.
    pad = vw.RHO + 2
    qpad2, gpad2 = vw.pad_edge(q, pad), vw.pad_edge(g, pad)
    for _j, qt, gt in vw.orbit_windows(qpad2, gpad2, (r0, c0 + 2), vw.RHO, pad=pad):
        assert qt.shape == (vw.REGION, vw.REGION)
        assert gt.shape == (vw.REGION, vw.REGION)


def test_zero_displacement_padding_is_unchanged_by_the_fix():
    """§9: the fix must be a NO-OP wherever the displacement is zero, which is
    every video probe. `pad = rho + 0 == rho`, so C1/C2 are byte-unchanged."""
    vw = _vw()
    q = vw.quantize(_frame(70912))
    g = np.asarray(_frame(70912), float)
    qpad, gpad = vw.pad_edge(q, vw.RHO), vw.pad_edge(g, vw.RHO)
    o = vw.region_origins()[5]
    a = vw.orbit_windows(qpad, gpad, o, vw.RHO)
    b = vw.orbit_windows(qpad, gpad, o, vw.RHO, pad=vw.RHO)
    assert len(a) == len(b) == 25
    for (_ja, qa, ga), (_jb, qb, gb) in zip(a, b):
        assert np.array_equal(qa, qb) and np.array_equal(ga, gb)


def test_otsu_has_no_free_parameter_and_finds_a_planted_split():
    """§13: the cut rule must be determined by the data, not chosen by me."""
    import importlib.util as iu
    spec = iu.spec_from_file_location(
        "vcm", os.path.join(ROOT, "scripts", "verdict_comparator_measure.py"))
    m = iu.module_from_spec(spec)
    spec.loader.exec_module(m)
    xs = [2.0] * 47 + [50.0] * 3
    thr, nlo, nhi, mlo, mhi = m.otsu_threshold(xs)
    assert 2.0 < thr < 50.0 and nlo == 47 and nhi == 3
    assert abs(mlo - 2.0) < 1e-9 and abs(mhi - 50.0) < 1e-9


# --------------------------------------------------------------------------- #
#  §12.3 — PROVENANCE, PINNED TO BOTH ENDPOINTS
# --------------------------------------------------------------------------- #
def _git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


_UNPINNED = RUNG_SHA.startswith("RUNG_SHA")


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
    files = _git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/").split()
    seeds = [f for f in files if "/seeds/" in f]
    assert seeds == ["research/experiments/gamma-substrate/seeds/"
                     "vision_verdict_comparator.json"], \
        f"this rung edited a seed it does not own: {seeds}"


@pytest.mark.skipif(_UNPINNED, reason="RUNG_SHA not yet pinned")
def test_the_pinned_shas_are_reachable():
    """A reachability question — and reachability, unlike a diff range,
    correctly resolves against the moving branch."""
    for sha in (BASE_SHA, PREREG_SHA, RUNG_SHA):
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                       cwd=ROOT, check=True)
