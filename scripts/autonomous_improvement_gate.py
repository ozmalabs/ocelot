#!/usr/bin/env python3
"""autonomous_improvement_gate — proves (or honestly disproves) that the
self-improvement cycle closes AUTONOMOUSLY, inside the daemon's own tick loop,
on the agent's REAL gaps, with ZERO human framing mid-loop.

Per CLAUDE.md's audit (see the commit this file lands in): the composer
machinery that authors the experiment/judge/adopt rule triad
(`domains.reflective_faculty._compose_experiment_rule`), the dispatch
mechanism (`domains.experiment_dispatch.scan_and_dispatch`), and the
close/adopt mechanism (`domains.reflective_faculty.close_experiment_loop`)
already existed and were already agent-authored / mechanical -- but nothing
wired them together inside `scripts/jabberwock_daemon.py`'s own tick loop, and
the concern that seeds the mint rule (`induce_concern`'s structured
observation) was only ever typed by a human driver script. This gate:

  1. Boots the agent EXACTLY as the daemon boots it (`jabberwock_daemon.boot`,
     `--seeds full`, a fresh checkpoint directory so it takes the real
     fresh-boot code path, not a resume).
  2. Runs a bounded loop of `tick()` calls interleaved with ONLY the daemon's
     own mechanical hooks: `_world_tick` (a standing offline-ARC episode,
     agent-driven throughout), `_concern_tick` (grounds the SEEDED standing
     concern -- graph data, not typed here), `_dispatch_tick` (spawn/ingest
     experiment children), `_close_tick` (teach the verdict + adopt).
  3. NEVER calls `induce_concern`, `ground_concern`, or hand-mints any
     Experiment/CapabilityAxis/Goal itself -- every mutation after boot comes
     from `tick()`/`run_rules()` or one of the four hooks above, exactly the
     surface a real running daemon offers.
  4. Watches graph state each iteration and logs a tick-by-tick timeline of
     which link in the chain fired (the deliverable).
  5. Asserts the full chain closed: a CapabilityAxis minted from the seeded
     standing concern -> an Experiment minted by the agent's OWN
     `author_experiment_from_residual_*` rule (verified via the `tested_by`
     edge that ONLY that rule's effects write) -> a child dispatched and
     completed -> an outcome written by the agent's OWN
     `judge_experiment_outcome_*` rule (verified via the `analysed` edge) ->
     EITHER adoption (`adopted=True`) OR a taught conclusion
     (`taught=True`) -- an inconclusive/refuted outcome that gets taught
     ALSO PASSES; the point is the cycle closed without a human, not that
     improvement happened on cue.

If a link genuinely cannot fire autonomously, this script says so precisely
(which link, why) rather than faking a pass.

Run:
    PYTHONPATH=runners/dsl/python:.:scripts python3 \\
        scripts/autonomous_improvement_gate.py [--max-ticks N] [--wall-budget SECS]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT), str(ROOT / "runners" / "dsl" / "python"), str(ROOT / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import jabberwock_daemon as jd                          # noqa: E402
import domains.reflective_faculty as rf                 # noqa: E402
from domains.experiment_dispatch import _INFLIGHT        # noqa: E402


def _nid(n) -> str:
    return str(n)


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def run_gate(max_ticks: int, wall_budget_s: float, world_every: int, concern_every: int,
             dispatch_every: int, close_every: int, world_actions: int,
             runs_dir: Path, ckpt_dir: Path, seeds: str = "full") -> int:
    timeline: list[str] = []

    def log_event(tick_n: int, msg: str) -> None:
        line = f"  tick {tick_n:5d} | {msg}"
        timeline.append(line)
        print(line, flush=True)

    print("=" * 96)
    print("AUTONOMOUS IMPROVEMENT GATE -- daemon-shaped boot, mechanical hooks only, zero human")
    print("framing after boot. See module docstring for exactly what is / isn't allowed to fire.")
    print("=" * 96)

    # -- 1. Boot EXACTLY as the daemon boots (fresh --seeds full: an empty ckpt-dir guarantees
    #    the fresh-boot code path in jabberwock_daemon.boot, never a resume). --------------------
    t_boot0 = time.time()
    adapter, booted_from = jd.boot(ckpt_dir, seeds)
    print(f"\nboot: booted_from={booted_from!r}, {adapter.s.node_count()} nodes, "
          f"{time.time() - t_boot0:.1f}s")
    okboot = _pass(booted_from == "seeds", "fresh --seeds full boot (not a checkpoint resume)")

    # -- 2. Standing-world setup (same one-time setup the daemon does when --world-every>0). ----
    world_ctx = jd._setup_world_ctx(adapter, world_actions) if world_every > 0 else None
    if world_every > 0:
        _pass(world_ctx is not None, "standing-world (offline ARC) setup available")

    _INFLIGHT.clear()   # this process may share the module with a prior run/import

    # -- 3. Snapshot pre-loop state (nothing hand-minted; these must ALL come from hooks/rules). -
    def _standing_concerns():
        return {n: adapter.s.node(n)["attrs"].get("status") for n in adapter.s.nodes("StandingConcern")}

    def _axes():
        out = {}
        for n in adapter.s.nodes("CapabilityAxis"):
            at = adapter.s.node(n)["attrs"]
            out[n] = {"induced": bool(at.get("induced")), "capability_keys": at.get("capability_keys")}
        return out

    def _experiments():
        out = {}
        for n in adapter.s.nodes("Experiment"):
            at = adapter.s.node(n)["attrs"]
            tested_by = any(True for a in adapter.s.nodes("CapabilityAxis")
                             if n in list(adapter.inner.neighbours(a, "tested_by")))
            analysed = bool(list(adapter.inner.neighbours(n, "analysed")))
            out[n] = {"status": at.get("status"), "outcome": at.get("outcome"),
                      "conclusion_ready": bool(at.get("conclusion_ready")),
                      "adopt_ready": bool(at.get("adopt_ready")), "adopted": bool(at.get("adopted")),
                      "adopt_denied": bool(at.get("adopt_denied")), "taught": bool(at.get("taught")),
                      "axis_tag": at.get("axis_tag"), "tested_by_axis": tested_by, "analysed": analysed}
        return out

    prev_concerns = _standing_concerns()
    prev_axes = _axes()
    prev_exps = _experiments()
    print(f"\npre-loop: StandingConcern={len(prev_concerns)} CapabilityAxis={len(prev_axes)} "
          f"Experiment={len(prev_exps)}")

    # -- 4. THE LOOP -- tick() interleaved with ONLY the daemon's own mechanical hooks. ----------
    print("\n" + "-" * 96)
    print("TICK-BY-TICK TIMELINE (only entries where something changed)")
    print("-" * 96)
    t0 = time.time()
    tick_n = 0
    fully_closed = False
    while tick_n < max_ticks and (time.time() - t0) < wall_budget_s:
        adapter.tick()
        tick_n += 1

        if world_ctx is not None and world_every > 0 and tick_n % world_every == 0:
            jd._world_tick(adapter, world_ctx)
        if concern_every > 0 and tick_n % concern_every == 0:
            jd._concern_tick(adapter)
        if dispatch_every > 0 and tick_n % dispatch_every == 0:
            jd._dispatch_tick(adapter, str(runs_dir))
        if close_every > 0 and tick_n % close_every == 0:
            jd._close_tick(adapter)

        # -- diff against previous snapshot; log only real transitions --
        cur_concerns = _standing_concerns()
        for n, status in cur_concerns.items():
            if prev_concerns.get(n) != status:
                log_event(tick_n, f"StandingConcern {_nid(n)} status -> {status!r} "
                                   "(_concern_tick: induce_concern/ground_concern)")
        prev_concerns = cur_concerns

        cur_axes = _axes()
        for n, info in cur_axes.items():
            # ONLY log induced=True axes tied to our own standing concern's grounding path --
            # the substrate's shared shape_decode_loop seed also mints plain (non-induced)
            # CapabilityAxis nodes as ordinary ARC gameplay bookkeeping (gap_prioritiser etc.);
            # those are real but not part of THIS chain, and logging every one floods the
            # timeline into noise.
            if n not in prev_axes and info["induced"]:
                log_event(tick_n, f"CapabilityAxis {_nid(n)} MINTED (induced=True, a genuine "
                                   f"residual) keys={info['capability_keys']} "
                                   "(sd_mint_quantum rule, via _concern_tick's induce_concern)")
        prev_axes = cur_axes

        cur_exps = _experiments()
        for n, info in cur_exps.items():
            old = prev_exps.get(n)
            if old is None:
                log_event(tick_n, f"Experiment {_nid(n)} MINTED status={info['status']!r} "
                                   f"axis_tag={info['axis_tag']!r} tested_by_axis={info['tested_by_axis']} "
                                   "(author_experiment_from_residual_* rule fired -- the "
                                   "'tested_by' edge only that rule's own effects write)")
                continue
            for k in ("status", "outcome", "conclusion_ready", "adopt_ready", "adopted",
                      "adopt_denied", "taught", "analysed"):
                if old.get(k) != info.get(k):
                    log_event(tick_n, f"Experiment {_nid(n)}.{k} -> {info.get(k)!r}"
                                       + (" (judge_experiment_outcome_* rule)" if k in
                                          ("outcome", "conclusion_ready", "analysed") else
                                          " (mark_adopt_ready_* rule)" if k == "adopt_ready" else
                                          " (perform_adoptions / _close_tick)" if k in
                                          ("adopted", "adopt_denied") else
                                          " (close_experiment_loop / teach)" if k == "taught" else ""))
        prev_exps = cur_exps

        fully_closed = any(
            (info["adopted"] or (info["taught"] and info["outcome"] in
             ("supported", "refuted", "inconclusive")))
            for info in cur_exps.values())
        if fully_closed:
            break
        time.sleep(0.2)

    elapsed = time.time() - t0
    print("-" * 96)
    print(f"\nloop ended after {tick_n} ticks, {elapsed:.1f}s "
          f"(fully_closed={fully_closed})")

    # -- 5. THE GATE -- verify the full chain, link by link. -------------------------------------
    print("\n" + "-" * 96)
    print("LINK-BY-LINK GATE")
    print("-" * 96)
    overall = True

    concern_processed = any(s == "processed" for s in prev_concerns.values())
    overall &= _pass(concern_processed,
                     "_concern_tick grounded the seeded StandingConcern (induce_concern/ground_concern "
                     "fired autonomously from graph data, no human text)")

    minted_axes = [n for n, info in prev_axes.items() if info["induced"]]
    overall &= _pass(bool(minted_axes),
                     "a CapabilityAxis was MINTED (a genuine residual: no held term-shape covered "
                     "the standing concern's structure on this fresh agent) -- not host-supplied")

    minted_exps = [n for n, info in prev_exps.items() if info["tested_by_axis"]]
    overall &= _pass(bool(minted_exps),
                     "an Experiment was minted BY THE AGENT'S OWN author_experiment_from_residual_* "
                     "rule (verified via the axis 'tested_by' edge that rule's effects alone write "
                     "-- never host code)")

    dispatched = [n for n, info in prev_exps.items() if info["status"] in ("running", "done", "failed")]
    overall &= _pass(bool(dispatched),
                     "_dispatch_tick spawned a real child process for a requested Experiment "
                     "(status left 'requested')")

    completed = [n for n, info in prev_exps.items() if info["status"] in ("done", "failed")]
    overall &= _pass(bool(completed),
                     "the dispatched child completed and its Run/RunObservation trace was ingested "
                     "back into the parent")

    judged = [n for n, info in prev_exps.items() if info["analysed"] and info["outcome"] is not None]
    overall &= _pass(bool(judged),
                     "the outcome was written BY THE AGENT'S OWN judge_experiment_outcome_* rule "
                     "(verified via the 'analysed' edge that rule's effects alone write)")

    closed = [n for n, info in prev_exps.items()
              if info["adopted"] or (info["taught"] and info["outcome"] in
                                      ("supported", "refuted", "inconclusive"))]
    overall &= _pass(bool(closed),
                     "the loop CLOSED: either the variant was adopted into the parent (outcome "
                     "'supported' + provenance allowed), or the verdict was taught as self-knowledge "
                     "(any outcome, including refuted/inconclusive -- a non-cherry-picked honest close, "
                     "not just improvement-on-cue)")

    print("\n" + "=" * 96)
    if overall:
        print("GATE PASSES: the full self-improvement cycle closed autonomously -- boot, tick(), and")
        print("the daemon's own mechanical hooks only. No induce_concern/ground_concern/hand-minted")
        print("Experiment/CapabilityAxis/Goal call happened after boot in this process.")
    else:
        print("GATE FAILS: see [FAIL] lines above -- the precise link that did not fire autonomously,")
        print("honestly reported (not papered over, not faked).")
    print("=" * 96)

    for n, info in prev_exps.items():
        print(f"\nfinal Experiment {_nid(n)}: {json.dumps(info, default=str)}")

    return 0 if overall else 1


# close_experiment_loop's teach() persists REAL self-knowledge into this seed by
# design (so it survives a reboot) -- guarded the same way tests/test_self_delta.py
# guards it, so a one-off CLI run of this gate doesn't leave test-run debris in a
# checked-in seed. Pass --no-guard-conclusions to disable (e.g. when deliberately
# running this against a real, persistent daemon-style agent whose taught
# conclusions you WANT to keep).
_CONCLUSIONS_SEED = ROOT / "seeds" / "experiment_conclusions.json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-ticks", type=int, default=4000)
    ap.add_argument("--wall-budget", type=float, default=240.0, help="seconds")
    ap.add_argument("--world-every", type=int, default=20)
    ap.add_argument("--world-actions", type=int, default=6)
    ap.add_argument("--concern-every", type=int, default=5)
    ap.add_argument("--dispatch-every", type=int, default=1)
    ap.add_argument("--close-every", type=int, default=5)
    ap.add_argument("--seeds", default="full", choices=["full", "chat"])
    ap.add_argument("--keep-runs", action="store_true",
                    help="don't delete the runs-dir/ckpt-dir on exit (default: cleaned up)")
    ap.add_argument("--no-guard-conclusions", action="store_true",
                    help="don't snapshot/restore seeds/experiment_conclusions.json (default: guarded, "
                         "since the gate genuinely teaches real conclusions into it)")
    args = ap.parse_args()

    stamp = time.strftime("%Y%m%dT%H%M%S")
    runs_dir = ROOT / "runs" / "autonomous_improvement_gate" / stamp
    runs_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir = Path(tempfile.mkdtemp(prefix="jbw_gate_ckpt_"))

    guard = not args.no_guard_conclusions
    before = None
    existed = _CONCLUSIONS_SEED.exists()
    if guard and existed:
        before = _CONCLUSIONS_SEED.read_text()

    try:
        return run_gate(args.max_ticks, args.wall_budget, args.world_every, args.concern_every,
                        args.dispatch_every, args.close_every, args.world_actions,
                        runs_dir, ckpt_dir, args.seeds)
    finally:
        if guard:
            if before is not None:
                _CONCLUSIONS_SEED.write_text(before)
            elif not existed and _CONCLUSIONS_SEED.exists():
                _CONCLUSIONS_SEED.unlink()
        if not args.keep_runs:
            shutil.rmtree(ckpt_dir, ignore_errors=True)
            shutil.rmtree(runs_dir, ignore_errors=True)
        else:
            print(f"\n(kept: runs_dir={runs_dir}  ckpt_dir={ckpt_dir})")


if __name__ == "__main__":
    raise SystemExit(main())
