"""test_attention_authoring — the JABBERWOCK AUTHORS its own when-to-look
rule from a framed concern (companion to tests/test_rule_driven_look.py,
which proves the underlying Rust primitives / hand-installed rule SHAPE
works; this file proves the agent can COMPOSE that same shape itself).

Per CLAUDE.md's discipline: this file never hand-installs the look-rule — it
only frames a concern (induce_concern) and drives the composer (ground_concern
-> the NEW `_compose_attention_rule` in domains/reflective_faculty.py,
dispatched via the NEW 'watch' RelationCue + ComposerCue). The match wiring
(fb_id / grid dims / which game) is mirrored onto the graph mechanically by
worlds/fb_eye.py.attach_eye — a world adapter, not a decision.

Skips the whole file if /dev/shm isn't writable, same requirement
tests/test_rule_driven_look.py has.
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

from substrate.world_adapter import WorldAdapter        # noqa: E402
from substrate.seed_loader import manifest_for           # noqa: E402
from domains.reflective_faculty import induce_concern, ground_concern  # noqa: E402
import worlds.fb_eye as fb_eye                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGION_GROUPING_SEED = os.path.join(ROOT, "seeds", "region_grouping.json")
FB_PIPE = os.path.join(ROOT, "scripts", "fb_pipe.py")
GRID_W, GRID_H = 32, 24


def _fresh():
    """Same minimal fixture tests/test_rule_driven_look.py uses (the generic
    WorldInstance->Region productions fb_sample's has_region/within edges
    need) PLUS the RelationCue lexicon ground_concern reads from."""
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(REGION_GROUPING_SEED)), None)
    wa.inner.load_seed_manifest(manifest_for("relation_vocabulary"), wa.agent)
    return wa


def _non_ground_regions(wa):
    out = []
    for nid in wa.inner.nodes("Region"):
        a = wa.inner.node(nid)["attrs"]
        if a.get("is_ground"):
            continue
        out.append({"id": nid, "minr": int(a["minr"]), "minc": int(a["minc"]),
                    "maxr": int(a["maxr"]), "maxc": int(a["maxc"])})
    return out


def _shm_name(tag: str) -> str:
    return f"/jbw_fb_authors_attention_test_{tag}_{os.getpid()}"


def _wait_for_attach(wa, name, grid_w=GRID_W, grid_h=GRID_H, timeout_s=8.0):
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            return fb_eye.attach_eye(wa, name, grid_w, grid_h)
        except ValueError:
            time.sleep(0.05)
    raise TimeoutError(f"fb_attach({name!r}) never succeeded within {timeout_s}s")


# ---------------------------------------------------------------------------
# 1 — the wall: before this change, no held cue for watch/observe/look/
#     perceive/attend/notice existed. Confirm the NEW cue is what closes it.
# ---------------------------------------------------------------------------
def test_watch_relation_cue_loads():
    wa = _fresh()
    cues = {at["name"]: at for at in (wa.s.node(n)["attrs"] for n in wa.s.nodes("RelationCue"))}
    assert "attention_watch" in cues
    assert json.loads(cues["attention_watch"]["relation"]) == ["watch", "FRAME", "when", "NEW"]


# ---------------------------------------------------------------------------
# 2+3+4+5: the full authoring + rule-driven-tracking + no-churn + save/load
#     loop, all through induce_concern -> ground_concern (no hand-installed
#     rule anywhere in this test).
# ---------------------------------------------------------------------------
def test_agent_authors_and_drives_the_look_rule_end_to_end(tmp_path):
    wa = _fresh()
    name = _shm_name("main")
    proc = subprocess.Popen(
        [sys.executable, FB_PIPE, "--test-pattern", "--name", name,
         "--width", str(GRID_W), "--height", str(GRID_H)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    fb_id = None
    wa2 = None
    fb_id2 = None
    try:
        fb_id, game, trigger = _wait_for_attach(wa, name)

        # STAGE A — frame ONLY the concern; the composer authors the rule.
        # (rule_count captured AFTER induce_concern, which itself lazily boots
        # the shape_decode_loop seed — its sd_* rules must not be counted as
        # part of what the ATTENTION composer specifically authored.)
        ind = induce_concern(wa, [["watch", "FRAME", "when", "NEW"]], name_hint="attention_concern_test")
        key = ind.get("capability_key")
        assert ind.get("minted") is True and key is not None

        before_rules = wa.inner.rule_count()
        g = ground_concern(wa, [key])
        assert g.get("grounded") is True, g.get("wall")
        assert g.get("path") == "compose_attention_rule"
        after_rules = wa.inner.rule_count()
        assert after_rules - before_rules == 1, "exactly one look-rule authored"
        assert g["rule"]["match"] == [["t", "wants_look", "g"]]
        assert g["rule"]["effects"][0][0] == "fb_sample"
        assert g["rule"]["effects"][1] == [
            "set_attr", "g", "last_looked_seq",
            {"__term__": {"type": "FbFrameSeq",
                          "fb": {"type": "Attr", "node": {"type": "Var", "name": "t"}, "key": "fb_id"}}}]

        # STAGE B — purely rule-driven tracking: only run_rules() from here on,
        # never wa.inner.fb_sample(...).
        samples, ids_seen, bboxes_seen = [], set(), set()
        attempts = 0
        while len(samples) < 5 and attempts < 800:
            attempts += 1
            steps = wa.inner.run_rules(1000)
            if steps > 0:
                figs = _non_ground_regions(wa)
                if len(figs) == 1:
                    samples.append(figs[0])
                    ids_seen.add(str(figs[0]["id"]))
                    bboxes_seen.add((figs[0]["minr"], figs[0]["minc"], figs[0]["maxr"], figs[0]["maxc"]))
            time.sleep(0.02)
        assert len(samples) >= 5, f"only {len(samples)} rule-driven samples within budget"
        assert len(ids_seen) == 1, f"expected ONE persistent Region identity, got {ids_seen}"
        assert len(bboxes_seen) >= 2, "expected the tracked bbox to move across samples"

        # STAGE C — stop the writer; the gate must close (no churn).
        proc.terminate()
        proc.wait(timeout=5)
        wa.inner.run_rules(1000)
        region_count_after_settle = len(wa.inner.nodes("Region"))
        for _ in range(5):
            steps = wa.inner.run_rules(1000)
            assert steps == 0, f"gate must stay closed once the writer stopped, progressed {steps}"
        assert len(wa.inner.nodes("Region")) == region_count_after_settle

        # STAGE D — the authored rule (fb_sample effect included) survives save/load.
        save_path = str(tmp_path / "attention_rule_checkpoint.json")
        rc_before = wa.inner.rule_count()
        wa.save(save_path)
        wa2 = WorldAdapter.load(save_path)
        assert wa2.inner.rule_count() == rc_before
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if fb_id is not None:
            fb_eye.detach_eye(wa, fb_id)
        if fb_id2 is not None and wa2 is not None:
            fb_eye.detach_eye(wa2, fb_id2)
        try:
            os.unlink(os.path.join("/dev/shm", name.lstrip("/")))
        except FileNotFoundError:
            pass
