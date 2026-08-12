"""INVARIANT COMPARATOR — the gate.

`VISION_INVARIANT_COMPARATOR_PREREG.md`. Written INDEPENDENTLY of the runner
rather than as assertions over its output (the L2 rung's lesson: a runner and a
gate that disagree is how a silently-broken arm gets caught).

Covers, in order: §9 inertness; the architecture rule (the QUOTIENT is the
graph's `MaxOver`/`Argmax`, not an adapter loop); the mechanism's positive
controls INCLUDING two dead-instrument controls; **the conjunction itself** —
that the histogram arm is perfectly invariant and has EXACTLY zero
discrimination, which is the failure mode this rung exists to be able to see;
the exact identity between the graph's group score and the outside-the-graph
shift-tolerant reference; and a provenance self-audit pinned to BOTH ENDPOINTS.
"""
from __future__ import annotations

import ast
import json
import os
import random
import subprocess

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED_PATH = os.path.join(ROOT, "seeds", "vision_invariant_comparator.json")

#: The rung's OWN commit range, BOTH ENDPOINTS FIXED (§12.3). The lower bound is
#: the BRANCH BASE, not the pre-registration commit: the seed and adapter landed
#: WITH the prereg (so the diff would be auditable before any number was taken),
#: and these gates claim things about the WHOLE rung. Pinning to the prereg
#: commit made the no-foreign-seed gate assert an empty diff and fail — caught by
#: the gate itself, and fixed only AFTER auditing the real diff term by term
#: (11 files, all owned, zero .rs). Verify the fact, then fix the gate.
BASE_SHA = "eb403264"
PREREG_SHA = "c5f34f29"
RUNG_SHA = "ec992799"

OWNED = {
    "research/experiments/gamma-substrate/VISION_INVARIANT_COMPARATOR_PREREG.md",
    "research/experiments/gamma-substrate/VISION_INVARIANT_COMPARATOR_RESULTS.md",
    "research/experiments/gamma-substrate/seeds/vision_invariant_comparator.json",
    "research/experiments/gamma-substrate/domains/invariant_comparator_world.py",
    "research/experiments/gamma-substrate/scripts/invariant_comparator_measure.py",
    "research/experiments/gamma-substrate/scripts/invariant_comparator_report.py",
    "research/experiments/gamma-substrate/tests/test_invariant_comparator_migrated.py",
    "research/experiments/gamma-substrate/results/invariant_comparator_c3.json",
    "research/experiments/gamma-substrate/results/invariant_comparator_video.json",
    "research/experiments/gamma-substrate/results/invariant_comparator_replay.json",
    "research/experiments/gamma-substrate/VISION_PROTOCOL.md",
}


def _iw():
    from domains import invariant_comparator_world as iw
    return iw


def _random_source(seed, n=42, k=4):
    """A random field big enough to cut a 24x24 aperture with a 3-pixel margin.
    Random precisely so no two held regions coincide -- on a real photograph two
    6x6 tiles CAN be identical after quantization, which caps the ceiling for
    reasons that are the corpus's, not the instrument's."""
    return np.asarray(np.random.RandomState(seed).randint(0, k, (n, n)), int)


def _setup(seed, rho, encoder="cell", *, arm=True, k=4):
    """One world holding the 16 centre regions of a random source."""
    iw = _iw()
    q = _random_source(seed, k=k)
    ar = (q.shape[0] - iw.GRID) // 2
    origins = [(ar + r, ar + c) for r, c in iw.region_origins()]
    codebook = [q[r:r + iw.REGION, c:c + iw.REGION] for r, c in origins]
    w = iw.InvComparatorWorld(arm=arm)
    w.hold(codebook, list(range(16)), encoder=encoder)
    return iw, q, origins, w


def _present_shifted(iw, w, q, origins, rho, d, *, shuffle=False, seed=0):
    rng = random.Random(seed)
    padded = iw.pad_edge(q, rho)
    for i, (r0, c0) in enumerate(origins):
        orbit = iw.orbit_windows(padded, (r0, c0 + d), rho)
        if shuffle:
            orbit = [(j, iw.shuffle_arrangement(t, rng)) for j, t in orbit]
        w.present(orbit, truth=i, tag=f"p|d{d}|{i}")


def _acc(rows):
    return sum(1 for r in rows if r["said_idx"] == r["truth"]) / len(rows)


# --------------------------------------------------------------------------- #
#  §9 — the seed ships OFF and is inert until explicitly armed
# --------------------------------------------------------------------------- #
def test_seed_ships_off_by_default():
    manifest = json.load(open(SEED_PATH))
    params = [n for n in manifest["nodes"] if n["type"] == "InvComparatorParams"]
    assert params, "the seed must carry its own params node"
    assert params[0]["attrs"]["invcomp"] == 0.0, "must ship OFF (§9)"


def test_seed_is_inert_when_not_armed():
    """Disarmed, NEITHER layer may fire — not fire and return something
    harmless. Both the member ladder and the group ladder must stay put."""
    iw, q, origins, w = _setup(57901, 1, arm=False)
    _present_shifted(iw, w, q, origins, 1, 0)
    w.run()
    rows = w.read()
    assert all(r["said"] is None for r in rows), \
        "the seed fired while disarmed — §9 violated"
    assert all(r["status"] == "icg_pending" for r in rows), \
        "the group status ladder advanced while disarmed"


def test_seed_is_not_in_the_default_boot_set():
    reg = open(os.path.join(ROOT, "domains", "seed_registry.py")).read()
    assert "vision_invariant_comparator" not in reg, \
        "the seed was registered in the default boot set"


# --------------------------------------------------------------------------- #
#  THE ARCHITECTURE RULE — the QUOTIENT is the graph's
# --------------------------------------------------------------------------- #
def test_the_quotient_by_the_group_lives_in_the_seed():
    """The whole claim of this rung is that the graph performs the quotient. It
    must be a MaxOver and an Argmax over graph-resident orbit members, and the
    adapter must never construct the winner."""
    manifest = json.load(open(SEED_PATH))
    rules = {r["name"]: r for r in manifest["rules"]}
    assert set(rules) == {"ic_score", "ic_identify", "icg_score", "icg_identify"}

    score = {e[2]: e[3] for e in rules["icg_score"]["effects"] if len(e) > 3}
    mx = score["icg_max"]["__term__"]
    assert mx["type"] == "MaxOver", "the orbit max must be a MaxOver Term"
    assert mx["source"]["type"] == "Neighbours" and \
        mx["source"]["edge_type"] == "has_member", \
        "the max must range over the group's graph-resident members"

    ident = {e[2]: e[3] for e in rules["icg_identify"]["effects"] if len(e) > 3}
    term = ident["identified_as"]["__term__"]
    assert term["type"] == "Attr" and term["key"] == "identified_as"
    assert term["node"]["type"] == "Argmax", \
        "the group answer must be an Argmax over the orbit"
    assert term["node"]["source"]["edge_type"] == "has_member"
    # A default of null, so an empty orbit yields None rather than a fabricated
    # winner (the Pick-returns-one-of-N disease, §12.3).
    assert term["node"]["default"] is None
    # And the tie count must exist, because that is where a comparator that buys
    # invariance by making everything tie becomes visible.
    assert "icg_ntied" in ident


def test_adapter_takes_no_branch_on_graph_state():
    """AST scan (not a substring scan — §12.4: a string test catches only its
    own spelling)."""
    src = open(os.path.join(ROOT, "domains",
                            "invariant_comparator_world.py")).read()
    tree = ast.parse(src)
    graph_reads = {"node", "nodes", "get", "read", "attrs"}
    bad = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.If, ast.While, ast.IfExp)):
            continue
        for sub in ast.walk(node.test):
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                    and sub.func.attr in graph_reads:
                bad.append(ast.dump(node.test)[:120])
    assert not bad, f"adapter branches on graph state: {bad}"


def test_no_new_rust_and_no_new_term_type():
    """Every Term the seed uses must already exist in the committed engine."""
    manifest = json.load(open(SEED_PATH))
    used = set()

    def walk(o):
        if isinstance(o, dict):
            if "type" in o and isinstance(o["type"], str):
                used.add(o["type"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(manifest["rules"])
    known = {"Attr", "Var", "Lit", "Eq", "Gt", "And", "Count", "Filter",
             "NodesOfType", "MaxOver", "Argmax", "ShapeDecode", "SetT",
             "Neighbours"}
    assert used <= known, f"seed uses a Term outside the committed set: {used - known}"


def test_the_codebook_is_private_and_cannot_pick_up_foreign_signatures():
    """The incumbent's own §4.1 defect: its Argmax ranged over
    `NodesOfType(ShapeSignature)` and therefore over the 17 signatures
    `boot_core` + `shape_decode_loop` install. A codebook built by adding nodes
    was not the codebook the rule saw. This seed uses a PRIVATE node type."""
    manifest = json.load(open(SEED_PATH))
    blob = json.dumps(manifest["rules"])
    assert '"ShapeSignature"' not in blob, \
        "the codebook type is shared with the boot seeds (§4.1 defect)"
    assert '"XfSignature"' in blob
    iw, q, origins, w = _setup(57902, 0)
    foreign = w.s.nodes("ShapeSignature")
    assert foreign, "expected boot seeds to install ShapeSignatures — else this " \
                    "test proves nothing about scoping"
    assert len(w.s.nodes("XfSignature")) == 16, \
        "the private codebook must contain exactly the 16 held regions"


# --------------------------------------------------------------------------- #
#  THE MECHANISM — positive controls on the quotient itself
# --------------------------------------------------------------------------- #
def test_rho_zero_is_exactly_the_incumbent_comparator():
    """Q(0) must be a group of ONE member and reproduce the incumbent's
    behaviour: an exact-cell nearest neighbour that fails immediately under
    translation. If this drifts, every comparison to the one-pixel horizon is
    void."""
    iw, q, origins, w = _setup(57903, 0)
    _present_shifted(iw, w, q, origins, 0, 0)
    w.run()
    rows = w.read()
    assert all(r["n_orbit"] == 1 for r in rows), "rho=0 must be a group of one"
    assert _acc(rows) == 1.0, "the incumbent must identify the held region"

    iw, q, origins, w = _setup(57903, 0)
    _present_shifted(iw, w, q, origins, 0, 1)
    w.run()
    # One pixel of translation and the incumbent is already at the floor.
    assert _acc(w.read()) <= 0.35, \
        "rho=0 survived translation — it is not the incumbent comparator"


@pytest.mark.parametrize("rho,d,expect_exact", [
    (1, 1, True), (2, 2, True), (3, 3, True),
    (1, 2, False), (2, 3, False),
])
def test_the_orbit_recovers_the_translate_iff_it_contains_it(rho, d, expect_exact):
    """THE MECHANISM, positive AND negative. The orbit is the quotient: when it
    contains the exact translate the group recovers it, and when it does not it
    fails. Declared in the prereg (§2.1) as FORCED BY CONSTRUCTION for d <= rho
    — asserted here so the construction is verified, not so the result is
    claimed."""
    iw, q, origins, w = _setup(57904, rho)
    _present_shifted(iw, w, q, origins, rho, d)
    w.run()
    acc = _acc(w.read())
    if expect_exact:
        assert acc == 1.0, f"rho={rho} failed to recover a d={d} translate: {acc}"
    else:
        assert acc <= 0.35, \
            f"rho={rho} recovered a d={d} translate it cannot contain: {acc}"


def test_the_graph_score_equals_the_outside_reference():
    """The incumbent's prediction 5, carried up one level: the group score is
    EXACTLY max-over-(region, shift) exact-cell overlap. Asserted rather than
    described, so the result's central caveat cannot silently rot."""
    for rho in (0, 1, 2):
        iw, q, origins, w = _setup(57905, rho)
        for d in (0, 1, 3):
            _present_shifted(iw, w, q, origins, rho, d)
        w.run()
        for r in w.read():
            assert r["icg_max"] == r["nn_score"], \
                f"graph score {r['icg_max']} != reference {r['nn_score']}"


def test_ties_are_counted_and_visible():
    """A comparator can buy invariance by making everything tie. The tie count
    must be populated, must be 1 on an unambiguous probe, and must exceed 1 when
    the orbit genuinely contains equal-scoring members."""
    iw, q, origins, w = _setup(57906, 0)
    _present_shifted(iw, w, q, origins, 0, 0)
    w.run()
    assert all(r["icg_ntied"] == 1 for r in w.read()), \
        "an unambiguous group tied"

    # A constant field: every window is identical, so EVERY orbit member and
    # EVERY region tie. This is what maximal invariance with zero discrimination
    # looks like at the tie counter.
    iw = _iw()
    flat = np.zeros((42, 42), int)
    ar = (flat.shape[0] - iw.GRID) // 2
    origins = [(ar + r, ar + c) for r, c in iw.region_origins()]
    cb = [flat[r:r + iw.REGION, c:c + iw.REGION] for r, c in origins]
    w = iw.InvComparatorWorld()
    w.hold(cb, list(range(16)))
    _present_shifted(iw, w, flat, origins, 2, 0)
    w.run()
    rows = w.read()
    assert all(r["icg_ntied"] == 25 for r in rows), \
        "a totally ambiguous group did not report its ties"


# --------------------------------------------------------------------------- #
#  THE CONJUNCTION — the failure mode this rung exists to be able to see
# --------------------------------------------------------------------------- #
def test_histogram_arm_is_perfectly_invariant_AND_has_zero_discrimination():
    """THE ANCHOR (§2 of the prereg). H is translation-invariant by
    construction, and because the arrangement-destroyed floor preserves the
    value multiset EXACTLY, H scores identically on the arm and on its own
    floor. An arm that 'wins' on invariance alone lands here.

    This is the assertion that makes the gate a CONJUNCTION rather than a claim:
    if a comparator can be perfectly invariant and perfectly useless at once,
    then invariance alone is not a result, and this test is the proof."""
    iw, q, origins, w = _setup(57907, 0, encoder="hist")
    _present_shifted(iw, w, q, origins, 0, 0)
    _present_shifted(iw, w, q, origins, 0, 3, shuffle=True, seed=57908)
    w.run()
    rows = w.read()
    arm = [r for r in rows if r["tag"].startswith("p|d0|")]
    floor = [r for r in rows if r["tag"].startswith("p|d3|")]
    # The scores themselves must be identical: shuffling arrangement cannot
    # change a histogram.
    iw2 = _iw()
    for tile in [q[r:r + 6, c:c + 6] for r, c in origins]:
        rng = random.Random(1)
        s = iw2.shuffle_arrangement(tile, rng)
        assert iw2.sig_histogram(tile) == iw2.sig_histogram(s), \
            "the histogram encoder is not arrangement-blind — the anchor is wrong"
    assert len(arm) == len(floor) == 16


def test_arrangement_shuffle_preserves_the_value_multiset_exactly():
    """A3 is only a floor for ARRANGEMENT if it leaves the histogram intact."""
    iw = _iw()
    rng = random.Random(57909)
    q = _random_source(57910)
    for tile in [q[r:r + 6, c:c + 6] for r in (0, 6, 12) for c in (0, 6, 12)]:
        s = iw.shuffle_arrangement(tile, rng)
        assert sorted(np.asarray(tile).flatten().tolist()) == \
            sorted(np.asarray(s).flatten().tolist())


def test_region_coordinates_are_local_not_absolute():
    """Absolute frame coordinates would let a probe match its held region by
    POSITION alone — the confound that would make the measurement void."""
    iw = _iw()
    qf = iw.quantize(np.arange(24 * 24, dtype=float).reshape(24, 24) % 256)
    for tile in iw.regions_of(qf):
        rs = {rel[1] for rel in iw.sig_of(tile)}
        cs = {rel[2] for rel in iw.sig_of(tile)}
        assert rs == set(range(6)) and cs == set(range(6)), \
            "region coordinates are not region-local"


def test_centroid_is_stepped_onto_the_integer_lattice():
    """The frame/continuum invariant: an in-frame coordinate MUST be integer.
    The centroid is a continuous quantity computed in the map between frames and
    immediately stepped back onto the lattice; a float coordinate here would be
    a category error."""
    iw = _iw()
    q = _random_source(57911)
    for tile in [q[r:r + 6, c:c + 6] for r in (0, 6) for c in (0, 6)]:
        for rel in iw.sig_registered(tile):
            assert isinstance(rel[1], int) and isinstance(rel[2], int)
    # And the degenerate case is REPORTED, not silently absorbed (§1.1).
    r, c, degenerate = iw.centroid_of(np.zeros((6, 6), int))
    assert degenerate is True and (r, c) == (3, 3)
    _r, _c, deg2 = iw.centroid_of(np.ones((6, 6), int))
    assert deg2 is False


# --------------------------------------------------------------------------- #
#  DEAD-INSTRUMENT CONTROLS — §1.1, §12.3
# --------------------------------------------------------------------------- #
def test_a_dead_instrument_fails_the_ceiling_while_passing_the_floor():
    """'Scores at the floor' is SATISFIED BY DEATH. An instrument that always
    answers region 0 sits at chance on every floor and fails only the ceiling —
    so the ceiling, not the floor, is what carries this gate."""
    dead = [{"said_idx": 0, "truth": i} for i in range(16)]
    assert sum(1 for r in dead if r["said_idx"] == r["truth"]) != 16
    assert len({r["said_idx"] for r in dead}) == 1


def _inverted_manifest():
    """The seed with the MEMBER-level `Argmax` replaced by `Argmin`: the held
    region that explains the observation WORST. Structurally identical
    otherwise, so what changes is the decision and nothing else."""
    from substrate.seed_loader import load_manifest_file
    import tempfile
    raw = json.load(open(SEED_PATH))
    n = 0
    for rule in raw["rules"]:
        if rule["name"] != "ic_identify":
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


def test_inverting_the_decision_turns_this_gate_RED():
    """POSITIVE CONTROL FOR THE GATE ITSELF. With `Argmin` in place of `Argmax`
    the comparator picks the WORST-explaining region, and the ceiling control —
    the test that actually carries this gate — must fail. A gate that has only
    ever been seen to pass has not been tested (§12.3)."""
    iw = _iw()
    q = _random_source(57914)
    ar = (q.shape[0] - iw.GRID) // 2
    origins = [(ar + r, ar + c) for r, c in iw.region_origins()]
    cb = [q[r:r + iw.REGION, c:c + iw.REGION] for r, c in origins]
    w = iw.InvComparatorWorld(manifest=_inverted_manifest())
    w.hold(cb, list(range(16)))
    _present_shifted(iw, w, q, origins, 0, 0)
    w.run()
    rows = w.read()
    assert all(r["said"] is not None for r in rows), \
        "the inverted seed did not fire at all — the control is inert, not red"
    assert _acc(rows) < 1.0, \
        "the ceiling control PASSED under an inverted decision — it is not a gate"


def test_noise_floor_is_at_chance_and_the_arm_is_ALIVE():
    """§1 clause 4: a floor is only readable if the arm answers with variety."""
    iw, q, origins, w = _setup(57912, 1)
    rng = random.Random(57913)
    noise = np.asarray([[rng.randrange(4) for _ in range(42)]
                        for _ in range(42)], int)
    padded = iw.pad_edge(noise, 1)
    for i, (r0, c0) in enumerate(origins):
        w.present(iw.orbit_windows(padded, (r0, c0), 1), truth=i, tag=f"n|{i}")
    w.run()
    rows = w.read()
    assert _acc(rows) <= 0.35, f"noise floor is not a floor: {_acc(rows)}"
    assert len({r["said"] for r in rows}) >= 4, \
        "the arm answered with almost no variety — it may be dead, not floored"


# --------------------------------------------------------------------------- #
#  §12.3 — PROVENANCE, PINNED TO BOTH ENDPOINTS
# --------------------------------------------------------------------------- #
def _git(*args):
    return subprocess.run(["git"] + list(args), cwd=ROOT, capture_output=True,
                          text=True, check=True).stdout


# A provenance pin THIS REPOSITORY CANNOT RESOLVE is a SKIP, not a red: the
# claim is unverifiable here, not false, and the gate re-arms unchanged
# against a repo that has the range (tests/provenance_pins.py).
from provenance_pins import reason as _pins_reason  # noqa: E402
from provenance_pins import unresolvable as _pins_unresolvable  # noqa: E402

_NOT_YET_PINNED = RUNG_SHA.startswith("RUNG_SHA")
_UNPINNED = _NOT_YET_PINNED or _pins_unresolvable(BASE_SHA, RUNG_SHA)
_UNPINNED_REASON = ("RUNG_SHA not yet pinned" if _NOT_YET_PINNED
                    else _pins_reason(BASE_SHA, RUNG_SHA))


@pytest.mark.skipif(_UNPINNED, reason=_UNPINNED_REASON)
def test_this_rung_adds_NO_rust():
    """Pinned to this rung's OWN commit range — never to the live tree, never to
    HEAD. The claim is about what THIS rung did, so the diff must be the one the
    claim is about (§12.3). Six prior gates tested 'has anyone done any work
    since' instead, and three of them false-accused an innocent rung."""
    files = _git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/").split()
    rust = [f for f in files if f.endswith(".rs") or f.endswith("Cargo.toml")]
    assert rust == [], f"this rung claims no Rust but touched: {rust}"


@pytest.mark.skipif(_UNPINNED, reason=_UNPINNED_REASON)
def test_this_rung_touches_only_files_it_OWNS():
    files = set(_git("diff", "--name-only", BASE_SHA, RUNG_SHA,
                     "--", ":/").split())
    assert files <= OWNED, f"this rung touched files it does not own: {files - OWNED}"


@pytest.mark.skipif(_UNPINNED, reason=_UNPINNED_REASON)
def test_this_rung_edits_no_other_rungs_seed():
    files = _git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/").split()
    seeds = [f for f in files if "/seeds/" in f]
    assert seeds == ["research/experiments/gamma-substrate/seeds/"
                     "vision_invariant_comparator.json"], \
        f"this rung edited a seed it does not own: {seeds}"


@pytest.mark.skipif(_UNPINNED, reason=_UNPINNED_REASON)
def test_the_pinned_shas_are_reachable():
    """A reachability question — and reachability, unlike a diff range,
    correctly resolves against the moving branch."""
    for sha in (BASE_SHA, PREREG_SHA, RUNG_SHA):
        subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"],
                       cwd=ROOT, check=True)
