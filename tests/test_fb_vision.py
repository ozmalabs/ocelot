"""test_fb_vision — the shared-memory framebuffer vision primitive
(`runners/dsl/src/framebuffer.rs` + `Substrate.fb_attach`/`fb_detach`/
`fb_sample`), exercised end-to-end against a REAL POSIX shm object a
Python writer (`tests/fb_writer.py`) fills in, per CLAUDE.md's design:
"live vision on shared memory" — a continuously-updated pixel buffer
the RUST runtime samples at its own tick pace, not discrete screenshots
shuttled through Python.

`region_grouping` is the ONLY seed loaded: it's the generic
`WorldInstance -[within]-> Region` / `WorldInstance -[has_region]->
Region` Γ productions that admit `segment`/`fb_sample`'s membership
edges (see `tests/test_browser_world.py`'s docstring for the same
requirement on `segment`; `fb_sample` mints/updates the SAME
`WorldInstance`/Region node shapes and reuses the SAME
`Substrate::segment_and_track` machinery, so it needs the same Γ).

Covers:
  (a) fb_attach validates the header (rejects bad magic, accepts good)
  (b) a static frame's fb_sample yields a Region whose grid bbox
      matches the painted rectangle
  (c) the writer MOVES the rectangle -> the next sample tracks it as
      the SAME Region node id (the cross-frame identity assertion —
      the actual point of reusing `segment_and_track`)
  (d) an unchanged frame_seq short-circuits to `unchanged: True`
      without re-segmenting
  (e) torn-write resilience: documents why a fully deterministic
      Python-driven torn-write proof isn't practical here (GIL +
      process-level timing), and instead proves fb_sample doesn't
      crash and stays internally consistent under a racing writer —
      the DETERMINISTIC torn-write proof lives at the Rust level
      (`framebuffer::tests::seqlock_read_races_writer_and_stays_honest`)
  (f) the Term form (`TermNode::FbFrameSeq`): installs a trivial rule
      gated on it via `add_rule` and shows it does NOT fire — this is
      the HONEST, documented current boundary (see
      `TermNode::FbFrameSeq`'s doc comment in term.rs): the rule
      engine's `where`-clause `EvalCtx` isn't threaded with a
      `framebuffers` reference yet, so `FbFrameSeq` always evaluates to
      `None` there today. The Term's WORKING form (real frame_seq
      values, when a caller DOES thread `.with_framebuffers(...)`) is
      proven at the Rust level
      (`term::tests::fb_frame_seq_term_reads_current_seq_when_threaded`)
      — there's no Python-facing hook to build a custom `EvalCtx`, so
      that half can't be re-proven from Python; this file proves the
      half that IS reachable from Python honestly.
"""
from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402

from tests.fb_writer import FbWriter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGION_GROUPING_SEED = os.path.join(ROOT, "seeds", "region_grouping.json")

BG = (30, 30, 30)      # BGR background
RECT = (200, 40, 90)   # BGR rectangle colour — distinct from bg


def _fresh():
    """A core-booted WorldAdapter carrying ONLY the region_grouping seed
    (the generic WorldInstance->Region Γ productions fb_sample's
    has_region/within edges need to admit) — deterministic, no
    cross-seed interference."""
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(REGION_GROUPING_SEED)), None)
    return wa


def _mk_game(wa):
    return wa.s.add_node("WorldInstance", {"world_type": "Game", "frame": 0.0})


def _shm_name(tag: str) -> str:
    return f"/jbw_fb_test_{tag}_{os.getpid()}"


def _region_nodes(wa):
    """Every Region node's (id, minr, minc, maxr, maxc, rvalue, is_ground)."""
    out = []
    for nid in wa.inner.nodes("Region"):
        a = wa.inner.node(nid)["attrs"]
        out.append({
            "id": nid,
            "minr": int(a["minr"]), "minc": int(a["minc"]),
            "maxr": int(a["maxr"]), "maxc": int(a["maxc"]),
            "rvalue": a["rvalue"], "is_ground": a.get("is_ground"),
        })
    return out


def _non_ground_regions(wa):
    return [r for r in _region_nodes(wa) if not r["is_ground"]]


# --------------------------------------------------------------------------
# (a) attach validation
# --------------------------------------------------------------------------

def test_fb_attach_rejects_bad_magic():
    wa = _fresh()
    name = _shm_name("badmagic")
    w = FbWriter(name, width=8, height=8)
    fb_id = None
    try:
        # Corrupt the magic bytes directly.
        w._mmap[0:4] = (0xDEADBEEF).to_bytes(4, "little")
        with pytest.raises(ValueError, match="magic"):
            wa.inner.fb_attach(name)
    finally:
        w.close()


def test_fb_attach_rejects_missing_object():
    wa = _fresh()
    with pytest.raises(ValueError):
        wa.inner.fb_attach(_shm_name("does_not_exist"))


def test_fb_attach_succeeds_and_detach_roundtrips():
    wa = _fresh()
    name = _shm_name("attach_ok")
    w = FbWriter(name, width=8, height=8)
    fb_id = None
    try:
        fb_id = wa.inner.fb_attach(name)
        assert isinstance(fb_id, int) and fb_id > 0
        assert wa.inner.fb_detach(fb_id) is True
        # Detaching again is a harmless no-op, not an error.
        assert wa.inner.fb_detach(fb_id) is False
    finally:
        w.close()


# --------------------------------------------------------------------------
# (b) static-frame sample -> Region bbox matches the painted rectangle
# --------------------------------------------------------------------------

def test_fb_sample_static_frame_region_bbox_matches_rect():
    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("static")
    # 16x16 px frame, 8x8 grid -> 2px/cell. Rectangle at px (4,4) size 4x4
    # -> grid cells (2..4, 2..4) i.e. minr=minc=2, maxr=maxc=3.
    w = FbWriter(name, width=16, height=16)
    fb_id = None
    try:
        w.write_frame(bytes(w.solid_frame(BG, rect=(4, 4, 4, 4), rect_bgr=RECT)))
        fb_id = wa.inner.fb_attach(name)
        result = wa.inner.fb_sample(fb_id, game, 8, 8)

        assert result["unchanged"] is False
        assert result["frame_seq"] == 1
        assert result["grid_w"] == 8 and result["grid_h"] == 8

        figures = _non_ground_regions(wa)
        assert len(figures) == 1, f"expected exactly 1 non-ground region, got {figures}"
        r = figures[0]
        assert (r["minr"], r["minc"], r["maxr"], r["maxc"]) == (2, 2, 3, 3), r
    finally:
        if fb_id is not None:
            wa.inner.fb_detach(fb_id)
        w.close()


# --------------------------------------------------------------------------
# (c) cross-frame identity: moving the rectangle keeps the SAME Region id
# --------------------------------------------------------------------------

def test_fb_sample_tracks_moving_rect_as_same_region_identity():
    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("moving")
    w = FbWriter(name, width=16, height=16)
    fb_id = None
    try:
        w.write_frame(bytes(w.solid_frame(BG, rect=(4, 4, 4, 4), rect_bgr=RECT)))
        fb_id = wa.inner.fb_attach(name)
        wa.inner.fb_sample(fb_id, game, 8, 8)
        before = _non_ground_regions(wa)
        assert len(before) == 1
        before_id = before[0]["id"]

        # Move the rectangle 2px right (1 grid cell at 2px/cell).
        w.write_frame(bytes(w.solid_frame(BG, rect=(6, 4, 4, 4), rect_bgr=RECT)))
        result2 = wa.inner.fb_sample(fb_id, game, 8, 8)
        assert result2["unchanged"] is False
        assert result2["frame_seq"] == 2

        after = _non_ground_regions(wa)
        assert len(after) == 1, f"rect move should still be exactly 1 figure region: {after}"
        after_id = after[0]["id"]

        # THE cross-frame identity assertion: same Region node, not a
        # birth+death pair.
        assert str(before_id) == str(after_id), (
            f"moving the rectangle should track it as the SAME region "
            f"identity, got before={before_id} after={after_id}"
        )
        # And it actually moved (new bbox reflects the shift).
        assert (after[0]["minc"], after[0]["maxc"]) == (3, 4), after[0]
    finally:
        if fb_id is not None:
            wa.inner.fb_detach(fb_id)
        w.close()


# --------------------------------------------------------------------------
# (d) unchanged frame_seq -> fast-path, no re-segmentation
# --------------------------------------------------------------------------

def test_fb_sample_unchanged_frame_seq_is_fast_path():
    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("unchanged")
    w = FbWriter(name, width=16, height=16)
    fb_id = None
    try:
        w.write_frame(bytes(w.solid_frame(BG, rect=(4, 4, 4, 4), rect_bgr=RECT)))
        fb_id = wa.inner.fb_attach(name)
        first = wa.inner.fb_sample(fb_id, game, 8, 8)
        assert first["unchanged"] is False
        region_count_after_first = len(wa.inner.nodes("Region"))

        # No new frame written -> frame_seq unchanged -> fast path.
        second = wa.inner.fb_sample(fb_id, game, 8, 8)
        assert second["unchanged"] is True
        assert second["frame_seq"] == first["frame_seq"]
        # No re-segmentation means no new/lost Region nodes either.
        assert len(wa.inner.nodes("Region")) == region_count_after_first
    finally:
        if fb_id is not None:
            wa.inner.fb_detach(fb_id)
        w.close()


# --------------------------------------------------------------------------
# (e) torn-write resilience — best-effort from Python; the deterministic
# proof is the Rust-level concurrent unit test (see module docstring).
# --------------------------------------------------------------------------

def test_fb_sample_survives_a_racing_writer_without_crashing():
    """Not a proof of the seqlock's torn-write MATH (that's
    `framebuffer::tests::seqlock_read_races_writer_and_stays_honest`,
    which controls both sides' timing precisely and inspects raw
    bytes). From Python, across a process boundary, we can't force a
    specific interleaving or observe raw torn bytes without reaching
    into the same unsafe machinery the Rust test already covers. What
    IS meaningfully testable here: a writer thread hammering the shm
    object with new frames while `fb_sample` repeatedly samples must
    (1) never crash/panic across the PyO3 boundary, (2) always return
    a well-formed result dict, and (3) report a monotonically
    non-decreasing frame_seq (the seqlock's `torn: true` fallback still
    returns SOME internally-well-typed frame, never garbage that
    corrupts the graph state)."""
    import threading

    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("torn")
    w = FbWriter(name, width=16, height=16)
    fb_id = None
    try:
        w.write_frame(bytes(w.solid_frame(BG, rect=(4, 4, 4, 4), rect_bgr=RECT)))
        fb_id = wa.inner.fb_attach(name)

        stop = threading.Event()

        def hammer():
            x = 4
            direction = 1
            while not stop.is_set():
                x = max(0, min(x + direction, 10))
                if x in (0, 10):
                    direction = -direction
                try:
                    w.write_frame(bytes(w.solid_frame(BG, rect=(x, 4, 4, 4), rect_bgr=RECT)))
                except ValueError:
                    # Writer/reader closed mid-loop at test teardown.
                    break

        t = threading.Thread(target=hammer, daemon=True)
        t.start()
        try:
            last_seq = -1
            for _ in range(200):
                result = wa.inner.fb_sample(fb_id, game, 8, 8)
                assert isinstance(result, dict)
                assert set(result) >= {"fb_id", "frame_seq", "unchanged", "torn", "grid_w", "grid_h"}
                assert result["frame_seq"] >= last_seq
                last_seq = result["frame_seq"]
        finally:
            stop.set()
            t.join(timeout=2)
    finally:
        if fb_id is not None:
            wa.inner.fb_detach(fb_id)
        w.close()


# --------------------------------------------------------------------------
# (f) the Term form — the wall is CLOSED: FbFrameSeq is now threaded
# through the rule engine's where-clause path (`rewrite::extend_each`
# builds its `EvalCtx` with `.with_framebuffers(...)`, and
# `Substrate::run_rules`/`try_incremental_match`/`apply_rule_once` all
# pass `Some(&self.framebuffers)`), so a rule gated on it fires for
# real now. This used to document a boundary
# (`test_fb_frame_seq_term_installs_but_where_clause_never_fires_today`,
# asserting the witness stayed unmarked); it now asserts the closed
# state instead. The Rust-level proof that the TERM ITSELF is correct
# when threaded still lives in
# term::tests::fb_frame_seq_term_reads_current_seq_when_threaded; the
# full engine-level proof (gating + no-churn + a live writer) lives in
# tests/test_rule_driven_look.py.
# --------------------------------------------------------------------------

def test_fb_frame_seq_term_gates_where_clause_and_fires():
    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("term")
    w = FbWriter(name, width=8, height=8)
    fb_id = None
    try:
        w.write_frame(bytes(w.solid_frame(BG, rect=(2, 2, 2, 2), rect_bgr=RECT)))
        fb_id = wa.inner.fb_attach(name)

        witness_t = wa.s.add_node("WorldInstance", {"world_type": "FbWitness", "seen": 0.0})
        # Unchecked structural edge (no Γ production needed for a
        # bespoke edge type here — this is test scaffolding to bind a
        # match variable, not a claim the graph makes) so the rule has
        # something to match on and `set_attr` has a node to target.
        wa.inner.add_edge_unchecked(game, "has_witness", witness_t)

        # where: FbFrameSeq(Lit(fb_id)) > Lit(0)  -- "some frame exists"
        rule_dict = {
            "name": "fb_witness_marks_when_frame_exists",
            "match": [["g", "has_witness", "w"]],
            "where": {
                "type": "Gt",
                "a": {"type": "FbFrameSeq", "fb": {"type": "Lit", "value": fb_id}},
                "b": {"type": "Lit", "value": 0},
            },
            "effects": [
                ["set_attr", "w", "seen", 1.0],
            ],
        }
        wa.inner.add_rule(rule_dict)

        wa.inner.run_rules(1000)

        # THE POINT: the framebuffer genuinely has a frame (frame_seq=1
        # > 0), FbFrameSeq now evaluates against the LIVE attached
        # handle inside the rule engine's where-clause (EvalCtx.
        # framebuffers IS threaded there now), so the witness gets
        # marked.
        witness_after = wa.inner.node(witness_t)["attrs"]
        assert witness_after.get("seen") == 1.0, (
            "FbFrameSeq is threaded into the rule engine's where-clause "
            "path now (rewrite::extend_each + Substrate::run_rules) -- "
            "the witness must be marked once the attached frame exists"
        )
    finally:
        if fb_id is not None:
            wa.inner.fb_detach(fb_id)
        w.close()
