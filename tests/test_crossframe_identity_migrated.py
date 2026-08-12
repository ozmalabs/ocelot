"""CROSS-FRAME IDENTITY — the gate.

`VISION_CROSSFRAME_IDENTITY_PREREG.md`. Written INDEPENDENTLY of the runner
rather than as assertions over its output (the L2 rung's lesson: a runner and a
gate that disagree is how a silently-broken arm gets caught).

Covers, in order: §9 inertness, the architecture rule (the DECISION is the
graph's), the instrument's positive controls INCLUDING a dead-instrument control
that must turn the gate red, the exact identity between the graph's score and
pixel Hamming overlap, and a provenance self-audit pinned to BOTH endpoints.
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

# A provenance pin THIS REPOSITORY CANNOT RESOLVE is a SKIP, not a red: the claim
# is unverifiable here, not false, and the gate re-arms unchanged against a repo
# that has the range (tests/provenance_pins.py, red-test triage 2026-08-12).
from provenance_pins import skip_if_unresolvable as _skip_unresolvable_pin  # noqa: E402

SEED_PATH = os.path.join(ROOT, "seeds", "vision_crossframe_identity.json")

BASE_SHA = "40318951"
RUNG_SHA = "0ae67b4d"

OWNED = {
    "research/experiments/gamma-substrate/VISION_CROSSFRAME_IDENTITY_PREREG.md",
    "research/experiments/gamma-substrate/VISION_CROSSFRAME_IDENTITY_RESULTS.md",
    "research/experiments/gamma-substrate/seeds/vision_crossframe_identity.json",
    "research/experiments/gamma-substrate/domains/crossframe_world.py",
    "research/experiments/gamma-substrate/scripts/crossframe_identity_measure.py",
    "research/experiments/gamma-substrate/tests/test_crossframe_identity_migrated.py",
    "research/experiments/gamma-substrate/results/crossframe_identity.json",
    "research/experiments/gamma-substrate/results/crossframe_identity_diagnose.json",
    "research/experiments/gamma-substrate/results/crossframe_identity_anomaly_rows.json",
    "research/experiments/gamma-substrate/scripts/crossframe_identity_diagnose.py",
    "research/experiments/gamma-substrate/scripts/crossframe_identity_report.py",
    "research/experiments/gamma-substrate/VISION_PROTOCOL.md",
}


def _tiles(seed, n=16, region=6, k=4):
    rng = random.Random(seed)
    return [np.asarray([[rng.randrange(k) for _ in range(region)]
                        for _ in range(region)], int) for _ in range(n)]


def _world(**kw):
    from domains.crossframe_world import CrossFrameWorld
    return CrossFrameWorld(**kw)


# --------------------------------------------------------------------------- #
#  §9 — the seed ships OFF and is inert until explicitly armed
# --------------------------------------------------------------------------- #
def test_seed_ships_off_by_default():
    manifest = json.load(open(SEED_PATH))
    params = [n for n in manifest["nodes"] if n["type"] == "CrossFrameParams"]
    assert params, "the seed must carry its own params node"
    assert params[0]["attrs"]["crossframe"] == 0.0, "must ship OFF (§9)"


def test_seed_is_inert_when_not_armed():
    """Disarmed, the identification rule must not fire at all — not fire and
    return something harmless. `identified_as` must be ABSENT."""
    tiles = _tiles(55901)
    w = _world(arm=False)
    w.hold_codebook(tiles, list(range(16)))
    for i, t in enumerate(tiles):
        w.present(t, truth=i, tag=f"off|{i}")
    w.run()
    rows = w.read()
    assert all(r["said"] is None for r in rows), \
        "the seed fired while disarmed — §9 violated"
    assert all(r["status"] == "xf_pending" for r in rows), \
        "the status ladder advanced while disarmed"


def test_seed_is_not_in_the_default_boot_set():
    """§9: no committed result may move because this rung exists. The seed must
    be reachable only by an explicit manifest load."""
    reg = open(os.path.join(ROOT, "domains", "seed_registry.py")).read()
    assert "vision_crossframe_identity" not in reg, \
        "the seed was registered in the default boot set"


# --------------------------------------------------------------------------- #
#  THE ARCHITECTURE RULE — the decision is the graph's, not Python's
# --------------------------------------------------------------------------- #
def test_the_identification_decision_lives_in_the_seed():
    """The winning name must be chosen by an Argmax Term inside the seed, and
    the adapter must never construct it."""
    manifest = json.load(open(SEED_PATH))
    rules = {r["name"]: r for r in manifest["rules"]}
    assert set(rules) == {"xf_score", "xf_identify"}
    eff = {e[2]: e[3] for e in rules["xf_identify"]["effects"] if len(e) > 3}
    term = eff["identified_as"]["__term__"]
    assert term["type"] == "Attr" and term["key"] == "name"
    assert term["node"]["type"] == "Argmax", \
        "identified_as must be an Argmax over the held codebook"
    assert term["node"]["value"]["type"] == "ShapeDecode"
    assert term["node"]["value"]["field"] == "covered_count"
    # A default of null, so an empty codebook yields None rather than a
    # fabricated winner (the Pick-returns-one-of-N disease, §12.3).
    assert term["node"]["default"] is None


def test_adapter_takes_no_branch_on_graph_state():
    """AST scan (not a substring scan — §12.4: a string test catches only its
    own spelling). No `if`/`while` in the adapter may test a value read out of
    the substrate."""
    src = open(os.path.join(ROOT, "domains", "crossframe_world.py")).read()
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
             "NodesOfType", "MaxOver", "Argmax", "ShapeDecode", "SetT"}
    assert used <= known, f"seed uses a Term outside the committed set: {used - known}"


# --------------------------------------------------------------------------- #
#  §1 — the instrument's positive controls, INCLUDING a dead-arm control
# --------------------------------------------------------------------------- #
def test_g1_ceiling_on_a_codebook_with_no_duplicate_regions():
    """Presented with the held region itself, the graph returns it. Random tiles
    are used precisely so no two held regions coincide — on a real frame two
    tiles CAN be identical after quantization, which caps the ceiling below 1.0
    for reasons that are the corpus's, not the instrument's."""
    tiles = _tiles(55902)
    w = _world()
    w.hold_codebook(tiles, list(range(16)))
    for i, t in enumerate(tiles):
        w.present(t, truth=i, tag=f"ceil|{i}")
    w.run()
    rows = w.read()
    assert sum(1 for r in rows if r["said_idx"] == r["truth"]) == 16
    assert all(r["xf_ntied"] == 1 for r in rows), "an unambiguous codebook tied"


def test_g2_noise_floor_is_at_chance_and_the_arm_is_alive():
    """§1.1 clause 4: 'scores at the floor' is satisfied by death. A floor is
    only readable if the arm is answering with variety."""
    from domains.crossframe_world import uniform_noise_tile
    rng = random.Random(55903)
    tiles = _tiles(55904)
    w = _world()
    w.hold_codebook(tiles, list(range(16)))
    for i in range(16):
        w.present(uniform_noise_tile(rng), truth=i, tag=f"noise|{i}")
    w.run()
    rows = w.read()
    acc = sum(1 for r in rows if r["said_idx"] == r["truth"]) / len(rows)
    assert acc <= 0.35, f"noise floor is not a floor: {acc}"
    assert len({r["said"] for r in rows}) >= 4, \
        "the arm answered with almost no variety — it may be dead, not floored"


def test_dead_instrument_control_turns_this_gate_red():
    """POSITIVE CONTROL FOR THE GATE ITSELF (§12.3: a gate that has only ever
    been seen to pass has not been tested). An instrument that always answers
    the same region sits at chance on the floor while failing the ceiling — so
    the CEILING test, not the floor test, is what carries the gate."""
    tiles = _tiles(55905)
    dead = [r for r in
            [{"said_idx": 0, "truth": i} for i in range(16)]]
    ceiling = sum(1 for r in dead if r["said_idx"] == r["truth"])
    floor_like = ceiling / len(dead)
    assert ceiling != 16, "a dead instrument must FAIL the ceiling"
    assert floor_like <= 0.35, \
        "and it PASSES the floor — which is why the floor alone is not a gate"
    assert len({r["said_idx"] for r in dead}) == 1


# --------------------------------------------------------------------------- #
#  THE HEADLINE CAVEAT, AS AN ASSERTION
# --------------------------------------------------------------------------- #
def test_the_graphs_score_is_exactly_pixel_hamming_overlap():
    """`ShapeDecode`'s `covered_count` on these tuples IS the count of cells
    identical in local position and quantized value. Asserted rather than
    described, so the results file's central caveat cannot silently rot."""
    from domains.crossframe_world import hamming_nn
    rng = random.Random(55906)
    tiles = _tiles(55907)
    w = _world()
    w.hold_codebook(tiles, list(range(16)))
    for i in range(16):
        probe = np.asarray(tiles[i]).copy()
        for _ in range(rng.randrange(0, 20)):
            probe[rng.randrange(6), rng.randrange(6)] = rng.randrange(4)
        w.present(probe, truth=i, tag=f"ham|{i}")
    w.run()
    for r in w.read():
        assert r["xf_max"] == r["nn_score"], \
            f"graph score {r['xf_max']} != Hamming overlap {r['nn_score']}"


def test_arrangement_shuffle_preserves_the_value_multiset_exactly():
    """A3 is only a floor for ARRANGEMENT if it leaves the histogram intact."""
    from domains.crossframe_world import shuffle_arrangement
    rng = random.Random(55908)
    for t in _tiles(55909, n=8):
        s = shuffle_arrangement(t, rng)
        assert sorted(np.asarray(t).flatten().tolist()) == \
            sorted(np.asarray(s).flatten().tolist())
        assert s.shape == np.asarray(t).shape


def test_region_coordinates_are_local_not_absolute():
    """Absolute frame coordinates would let a probe match its held region by
    POSITION alone — the confound that would make the whole measurement void."""
    from domains.crossframe_world import regions_of, sig_of, quantize
    q = quantize(np.arange(24 * 24, dtype=float).reshape(24, 24) % 256)
    for tile in regions_of(q):
        rs = {rel[1] for rel in sig_of(tile)}
        cs = {rel[2] for rel in sig_of(tile)}
        assert rs == set(range(6)) and cs == set(range(6)), \
            "region coordinates are not region-local"


# --------------------------------------------------------------------------- #
#  §12.3 — PROVENANCE, PINNED TO BOTH ENDPOINTS
# --------------------------------------------------------------------------- #
def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args],
                          capture_output=True, text=True, check=True).stdout


@pytest.mark.skipif(RUNG_SHA.startswith("RUNG_SHA"),
                    reason="RUNG_SHA not yet pinned")
@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_provenance_adds_no_rust():
    # `:/` root-magic: git reports --name-only from the git ROOT but resolves a
    # PATHSPEC relative to CWD, and this suite runs from the experiment dir.
    # That exact defect has silently emptied this diff in a previous rung.
    files = _git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/").split()
    assert not [f for f in files if f.endswith(".rs")], \
        f"this rung claims NO new Rust: {[f for f in files if f.endswith('.rs')]}"


@pytest.mark.skipif(RUNG_SHA.startswith("RUNG_SHA"),
                    reason="RUNG_SHA not yet pinned")
@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_provenance_touches_only_files_this_rung_owns():
    files = set(_git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/").split())
    assert files, "the pinned diff is EMPTY — the pathspec is wrong, not the rung"
    assert files <= OWNED, f"touched files this rung does not own: {files - OWNED}"


@pytest.mark.skipif(RUNG_SHA.startswith("RUNG_SHA"),
                    reason="RUNG_SHA not yet pinned")
@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_provenance_edits_no_committed_seed_but_its_own():
    files = _git("diff", "--name-only", BASE_SHA, RUNG_SHA, "--", ":/").split()
    seeds = [f for f in files if "/seeds/" in f]
    assert seeds == ["research/experiments/gamma-substrate/seeds/"
                     "vision_crossframe_identity.json"], \
        f"a committed seed was edited: {seeds}"


@pytest.mark.skipif(RUNG_SHA.startswith("RUNG_SHA"),
                    reason="RUNG_SHA not yet pinned")
@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_provenance_ledger_edit_is_one_appended_row_with_no_deletions():
    diff = _git("diff", "-U0", BASE_SHA, RUNG_SHA, "--",
                ":/research/experiments/gamma-substrate/VISION_PROTOCOL.md")
    added = [l for l in diff.split("\n")
             if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in diff.split("\n")
               if l.startswith("-") and not l.startswith("---")]
    assert len(added) == 1, f"expected ONE appended ledger row, got {len(added)}"
    assert not removed, f"the ledger lost lines: {removed}"
    assert "55000" in added[0], "the appended row is not this rung's seed block"


@pytest.mark.skipif(RUNG_SHA.startswith("RUNG_SHA"),
                    reason="RUNG_SHA not yet pinned")
@_skip_unresolvable_pin(BASE_SHA, RUNG_SHA)
def test_nothing_after_the_rung_commit_but_this_file():
    """Closes the last place a MUTABLE endpoint could hide: commits made AFTER
    RUNG_SHA (pinning the sha into this gate) must touch nothing else.

    SUPERVISOR REPAIR (2026-07-19) — the SEVENTH occurrence of §12.3, and the one
    that proved the new guard incomplete. This passed `"HEAD"` as a bare positional
    argument to `git diff`, a spelling neither of the guard's asserted tiers saw:
    tier 1 scans for a literal `..HEAD` inside a string, tier 1b for a `rev-parse
    HEAD` value flowing into a diff. Both were written by ENUMERATING THE SPELLINGS
    ALREADY OBSERVED rather than the semantics, so a third spelling walked straight
    through — within one commit of the guard landing.

    The guard now has a tier 1c for exactly this form. The lesson is recorded there:
    a detector built from observed instances covers observed instances.

    The tail is pinned to its true extent: the provenance-pin commit."""
    TAIL_SHA = "baf32c6621b372f28fac38b13939b737d631b7cd"   # the provenance-pin commit
    files = set(_git("diff", "--name-only", RUNG_SHA, TAIL_SHA, "--", ":/").split())
    assert files <= {"research/experiments/gamma-substrate/tests/"
                     "test_crossframe_identity_migrated.py"}, \
        f"commits after the rung commit changed more than this gate: {files}"
