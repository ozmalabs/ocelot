"""test_rule_driven_look — the JABBERWOCK triggers its own shm eye
sample, from a RULE, not the host.

Prior state (see `runners/dsl/src/framebuffer.rs` + `Substrate.fb_sample`):
the shm eye was host-invoked only — Python had to call
`substrate.fb_sample(fb_id, game, w, h)` itself every tick. That's a
host decision about "when to look," which CLAUDE.md forbids ("perception
must be something the AGENT'S RULES decide to do").

This file drives the closed loop end to end, purely through
`add_rule` + `run_rules()`:

  1. `add_rule` installs a "look rule": `?t -[wants_look]-> ?g`, gated
     by a `where`-clause on `FbFrameSeq(fb) > Attr(?g, "last_looked_seq")`
     (the Term primitive a prior session wired read-only into `evaluate`
     but never threaded into the rule engine's matcher — this session's
     fix), with two effects: `fb_sample` (the new perception-as-action
     effect kind) then `set_attr` advancing the watermark.
  2. A real subprocess writer (`scripts/fb_pipe.py --test-pattern`, the
     SAME harness `tests/test_live_eye.py` drives) feeds a moving
     rectangle into a POSIX shm object.
  3. The test calls ONLY `wa.inner.run_rules(...)` in its polling loop —
     never `wa.inner.fb_sample(...)` — and asserts Regions appear and
     track the moving rectangle as one persistent identity anyway.
  4. Once the writer stops, further `run_rules()` calls must stop
     progressing (the where-clause gate closes once the watermark
     catches up to the now-static `frame_seq`) — no per-tick churn.
  5. The look-rule (fb_sample effect included) must survive a
     `WorldAdapter.save`/`load` checkpoint cycle and keep working.

Skips the whole file if `/dev/shm` isn't writable, same requirement
`tests/test_fb_vision.py` / `tests/test_live_eye.py` have.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time

import pytest

pytest.importorskip("substrate_rs")

if not os.path.isdir("/dev/shm") or not os.access("/dev/shm", os.W_OK):
    pytest.skip("no writable /dev/shm on this platform -- POSIX shm unavailable",
                allow_module_level=True)

from substrate.world_adapter import WorldAdapter  # noqa: E402
from substrate_rs import ext  # noqa: E402
from substrate_rs.ext import FbSample, SetAttr  # noqa: E402
from substrate_rs import Attr, FbFrameSeq, Gt, Lit, Var  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGION_GROUPING_SEED = os.path.join(ROOT, "seeds", "region_grouping.json")
FB_PIPE = os.path.join(ROOT, "scripts", "fb_pipe.py")

# Small-but-nontrivial: meaningful segmentation, fast to sample/tick.
GRID_W, GRID_H = 32, 24


def _fresh():
    """A core-booted WorldAdapter carrying ONLY the region_grouping seed
    (the generic WorldInstance->Region Γ productions `fb_sample`'s
    has_region/within edges need to admit) -- mirrors
    tests/test_live_eye.py's fixture exactly."""
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(REGION_GROUPING_SEED)), None)
    return wa


def _mk_game(wa):
    return wa.s.add_node(
        "WorldInstance",
        {"world_type": "Game", "frame": 0.0, "last_looked_seq": -1.0},
    )


def _install_look_rule(wa, fb_id, game_nid, grid_w, grid_h):
    """The canonical "look rule" shape a driver should use to let the
    jabberwock author its own perception timing:

        match:  ?t -[wants_look]-> ?g
        where:  FbFrameSeq(fb) > Attr(?g, "last_looked_seq")
        effect: fb_sample(fb, ?g, grid_w, grid_h)
                set_attr(?g, "last_looked_seq", FbFrameSeq(fb))

    The `where` gate + trailing watermark `set_attr` together give the
    rule exactly-once-per-new-frame semantics: it fires the instant
    frame_seq advances past what `?g` last looked at, then immediately
    closes itself until the NEXT frame -- no per-tick churn on a
    stalled/paused writer.

    Returns (rule_idx, trigger_nid).
    """
    trigger = wa.s.add_node("LookTrigger", {})
    wa.inner.add_edge_unchecked(trigger, "wants_look", game_nid)
    where = Gt(FbFrameSeq(Lit(fb_id)), Attr(Var("g"), "last_looked_seq"))
    effects = [
        FbSample(fb_id, "g", grid_w, grid_h),
        SetAttr("g", "last_looked_seq", FbFrameSeq(Lit(fb_id))),
    ]
    idx = ext.add_rule(
        wa.inner, "look_when_frame_advances",
        match_edges=[("t", "wants_look", "g")],
        effects=effects, where=where,
    )
    return idx, trigger


def _non_ground_regions(wa):
    out = []
    for nid in wa.inner.nodes("Region"):
        a = wa.inner.node(nid)["attrs"]
        if a.get("is_ground"):
            continue
        out.append({
            "id": nid,
            "minr": int(a["minr"]), "minc": int(a["minc"]),
            "maxr": int(a["maxr"]), "maxc": int(a["maxc"]),
        })
    return out


def _shm_name(tag: str) -> str:
    return f"/jbw_fb_rule_look_test_{tag}_{os.getpid()}"


def _wait_for_attach(wa, name, timeout_s=8.0):
    """Poll fb_attach until the writer subprocess has created the shm
    object. `fb_attach` stays host I/O -- "which shm object currently
    exists" is external process state, not an agent decision; ONLY the
    per-tick "sample it now" decision moves into the rule (via
    Effect::FbSample)."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            return wa.inner.fb_attach(name)
        except ValueError:
            time.sleep(0.05)
    raise TimeoutError(f"fb_attach({name!r}) never succeeded within {timeout_s}s")


# --------------------------------------------------------------------------
# (1)+(2)+(3)+(4): purely rule-driven tracking, then no-churn once stopped.
# --------------------------------------------------------------------------

def test_rule_driven_look_tracks_moving_rect_without_host_fb_sample_call():
    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("moving")
    proc = subprocess.Popen(
        [sys.executable, FB_PIPE, "--test-pattern", "--name", name,
         "--width", str(GRID_W), "--height", str(GRID_H)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    fb_id = None
    try:
        fb_id = _wait_for_attach(wa, name)
        _install_look_rule(wa, fb_id, game, GRID_W, GRID_H)

        # THE POINT: from here on, only wa.inner.run_rules(...) is
        # called. No wa.inner.fb_sample(...) anywhere in this loop --
        # every sample must come from the rule's own Effect::FbSample.
        samples = []
        ids_seen = set()
        bboxes_seen = set()
        attempts = 0
        while len(samples) < 5 and attempts < 800:
            attempts += 1
            steps = wa.inner.run_rules(1000)
            if steps > 0:
                figures = _non_ground_regions(wa)
                if len(figures) == 1:
                    samples.append(figures[0])
                    ids_seen.add(str(figures[0]["id"]))
                    bboxes_seen.add((figures[0]["minr"], figures[0]["minc"],
                                      figures[0]["maxr"], figures[0]["maxc"]))
            time.sleep(0.02)

        assert len(samples) >= 5, (
            f"only observed {len(samples)} rule-driven samples within the "
            f"attempt budget -- the rule never fired enough times"
        )
        # THE cross-frame identity assertion: one persistent Region node,
        # not a birth+death pair per frame, produced with zero host
        # fb_sample calls.
        assert len(ids_seen) == 1, (
            f"the moving rectangle should track as ONE persistent Region "
            f"identity across rule-driven samples, got distinct ids {ids_seen}"
        )
        assert len(bboxes_seen) >= 2, (
            f"expected the tracked rectangle's bbox to move across "
            f"rule-driven samples, got only {bboxes_seen}"
        )

        # --- (4): stop the writer; the gate must close (no churn). ---
        proc.terminate()
        proc.wait(timeout=5)

        # Drain whatever frame was in flight when we stopped it.
        wa.inner.run_rules(1000)
        region_count_after_settle = len(wa.inner.nodes("Region"))

        # No further writes are possible -- every subsequent run_rules
        # call must find the where-clause gate closed (0 progressing
        # steps), and Region count must not move.
        for _ in range(5):
            steps = wa.inner.run_rules(1000)
            assert steps == 0, (
                f"gate must stay closed once the writer has stopped "
                f"(no churn), but run_rules progressed {steps} steps"
            )
        assert len(wa.inner.nodes("Region")) == region_count_after_settle
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if fb_id is not None:
            try:
                wa.inner.fb_detach(fb_id)
            except Exception:  # noqa: BLE001 -- best-effort teardown
                pass
        try:
            os.unlink(os.path.join("/dev/shm", name.lstrip("/")))
        except FileNotFoundError:
            pass


# --------------------------------------------------------------------------
# (5): the look-rule (fb_sample effect included) survives a checkpoint.
# --------------------------------------------------------------------------

def test_rule_driven_look_survives_save_load(tmp_path):
    wa = _fresh()
    game = _mk_game(wa)
    name = _shm_name("checkpoint")
    proc = subprocess.Popen(
        [sys.executable, FB_PIPE, "--test-pattern", "--name", name,
         "--width", str(GRID_W), "--height", str(GRID_H)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    fb_id = None
    fb_id2 = None
    wa2 = None
    save_path = str(tmp_path / "rule_look_checkpoint.json")
    try:
        fb_id = _wait_for_attach(wa, name)
        _install_look_rule(wa, fb_id, game, GRID_W, GRID_H)

        # Let it fire at least once before checkpointing.
        deadline = time.monotonic() + 8.0
        fired = False
        while time.monotonic() < deadline:
            if wa.inner.run_rules(1000) > 0:
                fired = True
                break
            time.sleep(0.02)
        assert fired, "look rule never fired before checkpoint"
        region_count_before = len(wa.inner.nodes("Region"))
        assert region_count_before > 0

        wa.save(save_path)

        # WorldAdapter.load builds a FRESH substrate/rule-store (its own
        # next_fb_id counter starts at 1, same as `wa`'s did), then
        # replays export_rules()'s captured rule store via import_rules
        # -- the fb_sample effect's literal fb_id survives that codec
        # untouched, so re-attaching the SAME shm name reproduces it.
        wa2 = WorldAdapter.load(save_path)
        assert wa2.inner.rule_count() == wa.inner.rule_count()
        fb_id2 = wa2.inner.fb_attach(name)
        assert fb_id2 == fb_id, (
            "a fresh substrate's first fb_attach must reproduce the same "
            "fb_id the checkpointed rule's fb_sample effect was authored "
            "against"
        )

        # Purely rule-driven again post-import: no host fb_sample call.
        deadline = time.monotonic() + 8.0
        fired2 = False
        while time.monotonic() < deadline:
            if wa2.inner.run_rules(1000) > 0:
                fired2 = True
                break
            time.sleep(0.02)
        assert fired2, "imported look rule never fired"
        assert len(wa2.inner.nodes("Region")) > 0, (
            "the imported rule's fb_sample effect must still mint/update "
            "Region state after a save/load round trip"
        )
    finally:
        for p in (proc,):
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=5)
        for handle_wa, handle_id in ((wa, fb_id), (wa2, fb_id2)):
            if handle_wa is not None and handle_id is not None:
                try:
                    handle_wa.inner.fb_detach(handle_id)
                except Exception:  # noqa: BLE001 -- best-effort teardown
                    pass
        try:
            os.unlink(os.path.join("/dev/shm", name.lstrip("/")))
        except FileNotFoundError:
            pass
