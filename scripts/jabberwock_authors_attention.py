"""jabberwock_authors_attention — the agent AUTHORS its own WHEN-TO-LOOK rule.

Prior state: the Rust primitives (FbFrameSeq in a where-clause, the FbSample
effect) exist and tests/test_rule_driven_look.py proves the SHAPE works — but
that test HAND-INSTALLS the look-rule via `ext.add_rule` (host code choosing
when to look). CLAUDE.md forbids that: perception timing must be something
the agent's OWN rules decide, authored the way every other jabberwock_authors_*
script drives it (induce_concern -> ground_concern -> the composer registry).

This script frames ONLY the concern ("I watch the frame when it's new") and
reads back what the agent authored — no rule text written here. The composer
it drives is `_compose_attention_rule` (new in domains/reflective_faculty.py),
dispatched via the new 'watch' RelationCue + ComposerCue (no held cue for
watch/observe/look/perceive/attend/notice existed before this change — a
proven wall, not a re-label of an existing composer; see
seeds/composer_dispatch.json's description for the check).

The match wiring (`?t -wants_look-> ?g`, the fb_id/grid dims) comes from graph
context a world adapter mirrors mechanically (worlds/fb_eye.py.attach_eye) —
whoever attaches a framebuffer stamps a LookTrigger node; the agent's authored
rule reads that context, it is never host-supplied into the rule itself.

Run (needs /dev/shm): PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_authors_attention.py
"""
from __future__ import annotations
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

FB_PIPE = os.path.join(ROOT, "scripts", "fb_pipe.py")
REGION_GROUPING_SEED = os.path.join(ROOT, "seeds", "region_grouping.json")
GRID_W, GRID_H = 32, 24


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def _non_ground_regions(wa):
    out = []
    for nid in wa.inner.nodes("Region"):
        a = wa.inner.node(nid)["attrs"]
        if a.get("is_ground"):
            continue
        out.append({"id": nid, "minr": int(a["minr"]), "minc": int(a["minc"]),
                    "maxr": int(a["maxr"]), "maxc": int(a["maxc"])})
    return out


def main():
    import json
    from substrate.world_adapter import WorldAdapter
    from domains.reflective_faculty import induce_concern, ground_concern
    import worlds.fb_eye as fb_eye

    overall = True
    print("=" * 92)
    print("THE JABBERWOCK AUTHORS ITS OWN WHEN-TO-LOOK RULE — I only frame the concern")
    print("=" * 92)

    from substrate.seed_loader import manifest_for

    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(REGION_GROUPING_SEED)), None)
    # the RelationCue lexicon (relation_vocabulary.json) -- ground_concern's held
    # vocabulary read; not auto-loaded by the minimal region_grouping-only fixture
    # (mirrors tests/test_experiment_composer.py's own `_fresh_agent_with_lexicon`).
    wa.inner.load_seed_manifest(manifest_for("relation_vocabulary"), wa.agent)

    # STAGE 0 — a REAL subprocess writer feeding a moving rectangle into shm
    # (host I/O, per CLAUDE.md — "which shm object exists" is external process
    # state, not an agent decision).
    name = f"/jbw_fb_authors_attention_{os.getpid()}"
    proc = subprocess.Popen(
        [sys.executable, FB_PIPE, "--test-pattern", "--name", name,
         "--width", str(GRID_W), "--height", str(GRID_H)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    fb_id = None
    try:
        deadline = time.monotonic() + 8.0
        game = trigger = None
        while time.monotonic() < deadline:
            try:
                fb_id, game, trigger = fb_eye.attach_eye(wa, name, GRID_W, GRID_H)
                break
            except ValueError:
                time.sleep(0.05)
        ok0 = _pass(fb_id is not None, "attached the shm eye + stamped LookTrigger/game graph context")
        overall &= ok0
        print(f"\n  [stage0] fb_id={fb_id}  game={game}  trigger={trigger}")

        # STAGE 1 — WALL FIRST (proven, not asserted): no held cue for watch/observe/
        # look/perceive/attend/notice existed prior to this change (checked directly
        # against seeds/relation_vocabulary.json — 39 prior cues, none of them). Frame
        # the concern; each clause LEADS with the cue word (induce_concern GOTCHA).
        obs = [["watch", "FRAME", "when", "NEW"]]
        ind = induce_concern(wa, obs, name_hint="attention_concern")
        key = ind.get("capability_key")
        print(f"\n  [induce_concern] minted={ind.get('minted')}  key={key!r}")
        ok1 = _pass(bool(ind.get("minted")) and key is not None,
                    "induce_concern minted a CapabilityAxis from the framed concern")
        overall &= ok1

        before_rules = wa.inner.rule_count()
        g = ground_concern(wa, [key]) if key else {}
        after_rules = wa.inner.rule_count()
        print(f"\n  [ground_concern] grounded={g.get('grounded')}  path={g.get('path')}")
        if g.get("wall"):
            print(f"     WALL (honest): {g.get('wall')}")
        ok2 = _pass(g.get("grounded") is True and g.get("path") == "compose_attention_rule",
                    "ground_concern picked the NEW 'attention' composer and it grounded")
        overall &= ok2
        ok3 = _pass(after_rules - before_rules == 1,
                    f"the composer installed exactly 1 live rule (rule_count {before_rules} -> {after_rules})")
        overall &= ok3
        if g.get("rule"):
            print(f"\n     ---- authored rule {g['rule']['name']!r} ----")
            print("     match:", g["rule"]["match"])
            print("     where:", g["rule"]["where"])
            print("     effects:", g["rule"]["effects"])

        # STAGE 2 — purely rule-driven tracking: ONLY wa.inner.run_rules() from here on.
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
        print(f"\n  [stage2] {len(samples)} rule-driven samples, {len(ids_seen)} distinct Region id(s), "
              f"{len(bboxes_seen)} distinct bbox(es) — ZERO host fb_sample calls")
        ok4 = _pass(len(samples) >= 5, "the AUTHORED rule fired enough times on its own")
        overall &= ok4
        ok5 = _pass(len(ids_seen) == 1, "the moving rectangle tracks as ONE persistent Region identity")
        overall &= ok5
        ok6 = _pass(len(bboxes_seen) >= 2, "the tracked bbox actually moved across samples")
        overall &= ok6

        # STAGE 3 — stop the writer; the gate must close (no churn).
        proc.terminate()
        proc.wait(timeout=5)
        wa.inner.run_rules(1000)
        region_count = len(wa.inner.nodes("Region"))
        churned = False
        for _ in range(5):
            steps = wa.inner.run_rules(1000)
            if steps != 0:
                churned = True
        ok7 = _pass(not churned and len(wa.inner.nodes("Region")) == region_count,
                    "once the writer stops, the where-clause gate closes (no per-tick churn)")
        overall &= ok7

        # STAGE 4 — survives save/load.
        import tempfile
        save_path = os.path.join(tempfile.gettempdir(), f"attention_rule_checkpoint_{os.getpid()}.json")
        rc_before = wa.inner.rule_count()
        wa.save(save_path)
        wa2 = WorldAdapter.load(save_path)
        ok8 = _pass(wa2.inner.rule_count() == rc_before, "the authored look-rule survives a save/load checkpoint")
        overall &= ok8
        try:
            os.unlink(save_path)
        except OSError:
            pass

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
        try:
            os.unlink(os.path.join("/dev/shm", name.lstrip("/")))
        except FileNotFoundError:
            pass

    print("=" * 92)
    if overall:
        print("  ALL STAGES PASS. The jabberwock AUTHORED its own when-to-look rule from a framed")
        print("  concern (a NEW attention composer, driven the same way as every other jabberwock_")
        print("  authors_* faculty) — zero host fb_sample calls, tracking survives, gate closes, saves.")
    else:
        print("  Some stages FAILED (see [FAIL] lines above) — honest report, not papered over.")
    return 0 if overall else 1


if __name__ == "__main__":
    if not os.path.isdir("/dev/shm") or not os.access("/dev/shm", os.W_OK):
        print("SKIP: no writable /dev/shm on this platform")
        raise SystemExit(0)
    raise SystemExit(main())
