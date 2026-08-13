"""Two-novel-orbits gate, THIRD GRAIN (`TWO_NOVEL_ORBITS_THIRD_GRAIN_PREREG.md`
/ `TWO_NOVEL_ORBITS_THIRD_GRAIN_RESULTS.md`).

Direct continuation of `tests/test_two_novel_orbits_gate_migrated.py` (which
closes the methodology gap named in `DEDUP_ADOPTION_SWEEP_RESULTS.md` for
the `DimensionGenerator`/`LatentDimension` grain, primary, and the
`ShapeSignature`/`vq_grow_quantum` grain, AR5). That gate's own RESULTS doc
named a THIRD grain and set it aside as a follow-on:

    "Third grain considered and set aside, per the PREREG:
    `prog_chunk_growth`'s `code_write_construction` codebook (`ckg_mint`).
    Its naming law is a strictly-increasing count discriminator
    (`ckt_<snake(head)>_q<count>`), not content-derived, so it is not
    exposed to the SAME collision mechanism either -- but confirming that
    (or finding otherwise) would require constructing a second
    genuinely-distinct `synthesize_from_request` fixture whose extracted
    `chunk_rels` differ in KIND ..."

This file is that fixture + that confirmation. It presents TWO
structurally-distinct novel code chunks (a multi-statement WINDOW chunk --
`_boot_selfteach`'s own `COMBINE_TMPL`, verbatim -- and a single COMPOUND
statement chunk, `GUARD_TMPL`, a `ProgIfStmt`, new here) to ONE graph, in
ONE session, and asserts the same four classes the primary gate does: no
stall on the second (differently-KINDED) novel item (AR2), bounded
epoch/wall-clock growth (AR3), correct dedup both directions -- distinct
mints, no re-mint on repeat, no name collision (AR4) -- mirroring
`test_two_novel_orbits_gate_migrated.py`'s own test shapes rather than
inventing new assertion styles.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs as srs  # noqa: E402

from domains import prog_chunk_growth as pcg  # noqa: E402
from domains import prog_synthesis as psy  # noqa: E402


def _term_live(term, env) -> bool:
    s = srs.Substrate()
    try:
        s._inner.evaluate(term, env)
        return True
    except ValueError as e:
        if "UnknownTermType" in str(e):
            return False
        raise


if not _term_live({"type": "ProgEval",
                   "prog": {"type": "ProgSeq", "stmts": []},
                   "env": None, "oracles": None, "fuel": 5, "field": ""}, {}):
    pytest.skip("ProgEval not present in the installed substrate_rs binary "
                "-- rebuild runners/dsl. Honest skip.",
                allow_module_level=True)


# --------------------------------------------------------------------------- #
#  Fixture 1: verbatim from tests/test_prog_chunks_migrated.py's
#  `_boot_selfteach` -- a flat 2-statement WINDOW chunk.
# --------------------------------------------------------------------------- #
COMBINE_REQ = "write a function combine that yields the combine of a and b"
COMBINE_ROWS = [({"a": 1, "b": 2}, 3), ({"a": 4, "b": 5}, 9), ({"a": 0, "b": 0}, 0)]
COMBINE_TMPL = {
    "desc": "returns a and b combined", "mode": "code_write_stmts",
    "args": ["a", "b"],
    "stmts": [{"type": "ProgReturn", "value": {"type": "Var", "name": "t"}},
              {"type": "ProgAssignVar", "name": "t",
               "value": {"type": "Plus", "items": [
                   {"type": "Var", "name": "a"}, {"type": "Var", "name": "b"}]}}]}

# --------------------------------------------------------------------------- #
#  Fixture 2: a genuinely DIFFERENT KIND of chunk -- a single COMPOUND
#  statement (a `ProgIfStmt`), reached via `chunk_candidates`'s OTHER
#  branch (`_is_compound`, not `_WINDOW_SIZES`) -- different `chunk_rels`
#  shape, not just different content in the SAME shape (see PREREG for the
#  `chunk_candidates` reading that establishes this).
# --------------------------------------------------------------------------- #
GUARD_REQ = "write a function guardpos that yields pos or nonpos for v"
GUARD_ROWS = [({"v": 5}, "pos"), ({"v": -1}, "nonpos"), ({"v": 0}, "nonpos")]
GUARD_TMPL = {
    "desc": "returns pos or nonpos by sign", "mode": "code_write_stmts",
    "args": ["v"],
    "stmts": [{"type": "ProgIfStmt",
               "cond": {"type": "Gt", "a": {"type": "Var", "name": "v"},
                        "b": {"type": "Lit", "value": 0}},
               "then": {"type": "ProgReturn",
                        "value": {"type": "Lit", "value": "pos"}},
               "orelse": {"type": "ProgReturn",
                          "value": {"type": "Lit", "value": "nonpos"}}}]}

_NAME_TAUGHT = re.compile(r"^ckt_[a-z0-9_]+_q[0-9]+$")


def _boot():
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    psy.ensure_program_synthesis(s, s._inner, ag)
    return s, ag


def _boot_two_orbit():
    """ONE graph for the whole scenario -- deliberately NOT re-booted per
    orbit. Boards BOTH spine templates up front (each its own unique
    trigger token so synthesize_from_request's rung-1 codebook match is
    unambiguous), mirroring `_boot_selfteach`'s single-template setup."""
    s, ag = _boot()
    pcg.ensure_chunk_growth(s, s._inner, ag)
    s.add_node("ShapeSignature", {
        "name": "gate_combine_spine", "kind": "code_write_construction",
        "signature": json.dumps([["COMBINE"]]), "trigger_tokens": ["COMBINE"],
        "spine": 1.0, "ground_template": json.dumps(COMBINE_TMPL)})
    s.add_node("ShapeSignature", {
        "name": "gate_guard_spine", "kind": "code_write_construction",
        "signature": json.dumps([["GUARDPOS"]]), "trigger_tokens": ["GUARDPOS"],
        "spine": 1.0, "ground_template": json.dumps(GUARD_TMPL)})
    return s, ag


def _present(s, ag, req, rows):
    """Present one orbit as a fresh synthesize_from_request accept + chunk
    pump on the SAME graph. Returns (accept_status, dt, entries,
    obs_statuses)."""
    t0 = time.time()
    r = psy.synthesize_from_request(s, ag, req, rows)
    pcg.chunk_pump(s, ag)
    dt = time.time() - t0
    entries = pcg.held_chunk_entries(s)
    obs = pcg.read_chunk_observations(s)
    return r["status"], dt, entries, sorted(o["status"] for o in obs)


# --------------------------------------------------------------------------- #
#  Sanity: the two fixtures' extracted chunk_rels really do differ in KIND
#  (guards the fixture construction itself, not just the dedup outcome).
# --------------------------------------------------------------------------- #
def test_fixtures_extract_genuinely_different_kind_of_chunk():
    s1, ag1 = _boot_two_orbit()
    r1 = psy.synthesize_from_request(s1, ag1, COMBINE_REQ, COMBINE_ROWS)
    assert r1["status"] == "accepted"
    ir1 = json.loads(s1.node(r1["program"])["attrs"]["program"])
    cands1 = pcg.chunk_candidates(ir1)
    assert len(cands1) == 1, "COMBINE must yield exactly one candidate chunk"
    assert cands1[0]["n_stmts"] == 2
    assert set(cands1[0]["labels"]) == {"ProgReturn", "ProgAssignVar"}

    s2, ag2 = _boot_two_orbit()
    r2 = psy.synthesize_from_request(s2, ag2, GUARD_REQ, GUARD_ROWS)
    assert r2["status"] == "accepted"
    ir2 = json.loads(s2.node(r2["program"])["attrs"]["program"])
    cands2 = pcg.chunk_candidates(ir2)
    assert len(cands2) == 1, "GUARD must yield exactly one candidate chunk"
    assert cands2[0]["n_stmts"] == 1
    assert cands2[0]["labels"] == ["ProgIfStmt"]

    # The KIND difference, made explicit: different STATEMENT COUNT in the
    # relation system (COMBINE's ckstmt rows span i=0..1, a flat sequence;
    # GUARD's spans only i=0, a lone compound) AND GUARD's leaf paths
    # descend into the compound's OWN block fields (.cond/.then/.orelse)
    # -- a shape COMBINE's flat window never has at all.
    ckstmt_is_1 = {r[1] for r in cands1[0]["rels"] if r[0] == "ckstmt"}
    ckstmt_is_2 = {r[1] for r in cands2[0]["rels"] if r[0] == "ckstmt"}
    assert ckstmt_is_1 == {0, 1}, ckstmt_is_1
    assert ckstmt_is_2 == {0}, ckstmt_is_2
    paths1 = {r[2] for r in cands1[0]["rels"] if r[0] == "ck"}
    paths2 = {r[2] for r in cands2[0]["rels"] if r[0] == "ck"}
    assert not any(p.startswith("cond") or p.startswith("then")
                   or p.startswith("orelse") for p in paths1), (
        "COMBINE (a flat window) must never carry a compound-statement "
        "block path -- if it did, the two fixtures would not differ in "
        "kind: %r" % paths1)
    assert any(p.startswith("cond") or p.startswith("then")
               or p.startswith("orelse") for p in paths2), (
        "GUARD's chunk_rels must show the nested compound-statement shape "
        "COMBINE's flat window never has: %r" % paths2)


# --------------------------------------------------------------------------- #
#  AR1/AR2/AR3/AR4 -- the primary scenario: two novel chunks, one graph
# --------------------------------------------------------------------------- #
def test_two_novel_chunks_one_graph_no_stall_bounded_growth_correct_dedup():
    s, ag = _boot_two_orbit()
    ep0 = s.node(ag)["attrs"].get("write_codebook_epoch") or 0.0

    total_t0 = time.time()
    statuses = []
    entry_counts = []
    obs_status_snapshots = []
    wall_times = []
    for key, req, rows in (("A_combine", COMBINE_REQ, COMBINE_ROWS),
                            ("B_guard", GUARD_REQ, GUARD_ROWS),
                            ("A_combine_repeat", COMBINE_REQ, COMBINE_ROWS),
                            ("B_guard_repeat", GUARD_REQ, GUARD_ROWS)):
        status, dt, entries, obs_statuses = _present(s, ag, req, rows)
        statuses.append(status)
        entry_counts.append(len(entries))
        obs_status_snapshots.append(obs_statuses)
        wall_times.append(dt)

        # --- AR2: the accept itself must succeed every time (a synthesis
        # failure would mask the chunk-grain question entirely).
        assert status == "accepted", "orbit %r must be accepted: got %r" % (key, status)
        # --- AR2: the STALL assertion at this grain -- no observation is
        # left "pending" (uncovered, unminted) after the pump.
        assert "pending" not in obs_statuses, (
            "orbit %r left a prog_chunk observation stuck 'pending' -- "
            "the silent-drop stall at this grain: %r" % (key, obs_statuses))

        # --- AR3: the LOOP assertion, per-step.
        assert dt < 3.0, (
            "one accept+pump for orbit %r took %.3fs (bound 3s)" % (key, dt))

    total_dt = time.time() - total_t0

    # --- AR3, whole-scenario bounds.
    assert total_dt < 10.0, "the whole 2-chunk scenario took %.3fs (bound 10s)" % total_dt
    ep1 = s.node(ag)["attrs"].get("write_codebook_epoch") or 0.0
    epoch_growth = ep1 - ep0
    assert epoch_growth <= 4, (
        "write_codebook_epoch grew by %r across 2 novel chunks + 2 repeats "
        "-- measured correct behaviour is +2 (one bump per genuine mint, "
        "zero for either repeat)" % epoch_growth)

    # --- AR2 (stronger, end-of-scenario view): entries went 1 -> 2 -> 2 -> 2,
    # never stalling at 1 (the second, differently-KINDED chunk must mint)
    # and never exceeding 2 (a repeat must not re-mint).
    assert entry_counts == [1, 2, 2, 2], (
        "entry-count trajectory across the 4 steps must be [1, 2, 2, 2] "
        "(mint, mint, recognize, recognize): got %r" % entry_counts)

    # --- AR4: exactly 2 self-taught entries, one per distinct chunk_key.
    entries = pcg.held_chunk_entries(s)
    self_taught = [e for e in entries if e["provenance"] == "self_taught"]
    assert len(self_taught) == 2, (
        "expected exactly 2 distinct self-taught chunk entries (COMBINE's "
        "window chunk, GUARD's compound chunk); got %d: %r"
        % (len(self_taught), self_taught))
    keys = {e["chunk_key"] for e in self_taught}
    assert len(keys) == 2, "the two entries' chunk_key must be distinct: %r" % keys

    # --- AR4: names distinct -- the direct regression check this rung
    # exists to run (see PREREG AR5 for why the naming law makes this
    # near-certain, and the fixture is built to exercise it, not dodge it).
    names = {e["name"] for e in self_taught}
    assert len(names) == 2, "self-taught entry names collided: %r" % names
    for e in self_taught:
        assert _NAME_TAUGHT.match(e["name"]), e["name"]
        assert len(e["name"]) <= 40

    # --- AR4: both repeats must RECOGNIZE (not re-mint), each covered_by
    # its OWN first mint, never cross-covered.
    name_by_chunk_key = {e["chunk_key"]: e["name"] for e in self_taught}
    obs = pcg.read_chunk_observations(s)
    recognized = [o for o in obs if o["status"] == "recognized"]
    assert len(recognized) == 2, "expected exactly 2 recognized (repeat) observations: %r" % obs
    for o in recognized:
        assert o["covered_by"] == name_by_chunk_key.get(o["chunk_key"]), (
            "a repeat's covered_by must point at its OWN chunk's mint, not "
            "the other chunk's: %r vs %r" % (o, name_by_chunk_key))


def test_second_novel_chunk_does_not_stall_even_isolated():
    """A tighter isolation of the exact stall shape the primary gate's own
    `test_second_novel_orbit_does_not_stall_even_isolated` checks, one grain
    over: present ONLY two distinct novel chunks (no repeats) and confirm
    BOTH mint. If the second, differently-KINDED chunk were blocked by a
    coarse `kind == 'code_write_construction'` guard (the exact shape of the
    ALREADY-FIXED `DimensionGenerator` bug), this is where it would show."""
    s, ag = _boot_two_orbit()
    status1, _, entries1, obs1 = _present(s, ag, COMBINE_REQ, COMBINE_ROWS)
    assert status1 == "accepted"
    assert len(entries1) == 1
    assert obs1 == ["minted"]

    status2, _, entries2, obs2 = _present(s, ag, GUARD_REQ, GUARD_ROWS)
    assert status2 == "accepted", (
        "the SECOND, differently-KINDED novel chunk's accept must succeed")
    assert len(entries2) == 2, (
        "the second chunk must mint its OWN entry, distinct from the "
        "first -- got %d entries: %r" % (len(entries2), entries2))
    assert obs2 == ["minted", "minted"], (
        "both chunk observations must reach 'minted', never left "
        "'pending' (the stall this test isolates): %r" % obs2)


def test_repeat_chunk_after_two_mints_does_not_triple_mint():
    """Dedup direction, isolated: after two DISTINCT chunks are minted,
    re-presenting either one must recognize, not mint a third -- one grain
    over from the primary gate's own
    `test_repeat_orbit_after_two_mints_does_not_triple_mint`."""
    s, ag = _boot_two_orbit()
    _present(s, ag, COMBINE_REQ, COMBINE_ROWS)
    _present(s, ag, GUARD_REQ, GUARD_ROWS)

    status, _, entries, obs = _present(s, ag, COMBINE_REQ, COMBINE_ROWS)
    assert status == "accepted"
    assert len(entries) == 2, "a repeat must not mint a third entry: %r" % entries
    assert sorted(obs) == ["minted", "minted", "recognized"]

    status2, _, entries2, obs2 = _present(s, ag, GUARD_REQ, GUARD_ROWS)
    assert status2 == "accepted"
    assert len(entries2) == 2, "a repeat must not mint a third entry: %r" % entries2
    assert sorted(obs2) == ["minted", "minted", "recognized", "recognized"]
