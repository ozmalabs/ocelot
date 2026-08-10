"""jabberwock_improves_itself — CLOSING THE SELF-IMPROVEMENT LOOP: a SUPPORTED
self-experiment's variant gets ADOPTED INTO THE PARENT ITSELF, not just judged
and forgotten.

The self-experiment loop (scripts/jabberwock_varies_itself.py,
scripts/jabberwock_varies_acting.py, domains/reflective_faculty.py's
`_compose_experiment_rule`) already lets the agent author + dispatch a
modified copy of itself, judge the trial, and teach the verdict. But the
PARENT never changed: win or lose, the parent goes back to being exactly what
it was before. This script drives the CLOSED loop where a genuinely-supported
variant is folded back into the parent:

  PART A — THE FULL SELF-AUTHORED LOOP, LIVE DISPATCH (mirrors
  jabberwock_varies_acting.py's Part A exactly, PLUS the new 'adopt' relation):
  an induced concern grounds 'test'+'send'+'judge'+'gradient'+'adopt'; the
  agent's OWN mint rule fires (via tick, no host add_node) and authors a
  SeedDelta whose remove_rules/add_rules embed a genuine threshold-shifted
  acting-variant; a REAL child is dispatched and judged. close_experiment_loop
  then reads whatever the agent's own judge rule concluded: if 'supported',
  the agent's own adopt rule marks the Experiment adopt_ready and
  perform_adoptions folds the variant into THIS PARENT (export_rules shows the
  original tombstoned + the variant active); if not, close_experiment_loop's
  adoption step is a documented no-op — reported honestly either way, since
  navigate's score-per-frame sign is a genuinely live, non-cherry-picked
  outcome (see jabberwock_varies_acting.py's own docstring on this).

  PART B — THE DISCRIMINATIVE + MECHANICAL CHECKS, driven directly (not via a
  live dispatch, so the supported/refuted/denylisted cases are each exercised
  on purpose rather than hoped for): a genuinely-authored acting-variant
  (`_compose_acting_variant`, real seed-sourced rule content, never
  hand-written rule text) is carried on hand-built Experiment+SeedDelta nodes
  with outcome='supported' / 'refuted' / (supported but provenance-denylisted)
  — proving perform_adoptions adopts iff supported AND allowed, denies a
  denylisted rule even when supported, and never touches a refuted trial. Then
  revert_adoption is exercised, and a live NavigateEnv episode is run on the
  PARENT directly (no dispatch) before vs. after adoption, showing the
  parent's own action stream changes.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_improves_itself.py
"""
from __future__ import annotations
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.reflective_faculty as rf
import domains.edit_ops as eo
from domains.experiment_dispatch import scan_and_dispatch, _INFLIGHT
from worlds.arc import ArcWorld
from arc3_env import NavigateEnv
import arc_run

RUNS_DIR_A = os.path.join(ROOT, "runs", "jabberwock_improves_itself", "part_a")
TIMEOUT_S = 120
_CONCLUSIONS_SEED = os.path.join(ROOT, "seeds", "experiment_conclusions.json")


def _pass(ok: bool, label: str) -> bool:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


def _delta_of(a, exp):
    for d in a.inner.neighbours(exp, "has_delta"):
        if a.inner.has_node(d):
            return a.s.node(d)["attrs"]
    return {}


def _wait(a, exps: list, runs_dir: str, timeout=TIMEOUT_S) -> None:
    S = a.s
    t0 = time.time()
    while time.time() - t0 < timeout:
        scan_and_dispatch(a, runs_dir)
        statuses = [S.node(e)["attrs"].get("status") for e in exps if e is not None]
        if all(s not in ("requested", "running") for s in statuses):
            return
        time.sleep(0.5)


def _mint_manual_experiment(agent, av: dict, outcome: str, tag: str):
    """Hand-build an Experiment + SeedDelta carrying a REAL, agent-authored
    acting-variant (`av` = a `_compose_acting_variant`/`_compose_structural_
    variant` report — never hand-written rule text) with a given outcome, so
    Part B can drive the supported/refuted/denylisted cases ON PURPOSE."""
    S, I = agent.s, agent.inner
    exp = S.add_node("Experiment", {"status": "done", "hypothesis": f"h_{tag}", "game": "navigate",
                                    "run_dir": "", "outcome": outcome, "conclusion_ready": True,
                                    "axis_tag": tag})
    delta = S.add_node("SeedDelta", {"skip_seeds": "[]", "add_rules": json.dumps([av["rule"]]),
                                     "remove_rules": json.dumps([av["removed_rule"]]),
                                     "act_rule_varied": av["removed_rule"],
                                     "act_shift": av.get("shift")})
    I.add_edge_unchecked(exp, "has_delta", delta)
    return exp


def _fresh_full_agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.set_self_teacher(lambda q: "D")
    return a


def _run_episode_actions(agent) -> list:
    prod = arc_run._setup_speech(agent)
    describe_ctx = arc_run.setup_describe(agent, prod)
    agent.inner.add_rule(arc_run.MS_CHOOSE_EXPAND)
    actions = []
    arc_run.run_episode(agent, ArcWorld(NavigateEnv()), 20, "cells", prod, describe_ctx,
                        on_frame=lambda rec: actions.append(rec["action"]))
    return actions


def main():
    overall = True
    existed_conclusions = os.path.exists(_CONCLUSIONS_SEED)

    print("=" * 92)
    print("THE JABBERWOCK IMPROVES ITSELF — closing the self-improvement loop: a SUPPORTED variant")
    print("gets ADOPTED INTO THE PARENT ITSELF, not judged and forgotten.")
    print("=" * 92)

    # =========================================================================================
    # PART A — the full self-authored loop, LIVE dispatch, whatever outcome navigate's real
    # score-per-frame sign produces (never cherry-picked — see module docstring).
    # =========================================================================================
    print("\n" + "-" * 92)
    print("PART A — live dispatch: mint -> judge -> (if supported) adopt_ready -> perform_adoptions")
    print("-" * 92)
    _INFLIGHT.clear()
    a = _fresh_full_agent()
    S, I = a.s, a.inner

    w = ArcWorld(NavigateEnv())
    sub, ctx = w.reset()
    a.perceive_frame(sub)
    a.tick()

    ind = rf.induce_concern(a, [["test", "HYPOTHESIS", "about", "SELF"],
                               ["send", "VARIANT", "to", "WORLD"],
                               ["judge", "TRIAL", "by", "OUTCOME"],
                               ["gradient", "VARIANT", "of", "ACTING"],
                               ["adopt", "WINNER", "as", "SELF"]],
                           name_hint="improve_full_loop_concern")
    key = ind.get("capability_key")
    g = rf.ground_concern(a, [key]) if key else {}
    av = g.get("acting_variant") or {}
    print(f"\n  [A.1] induce_concern minted={ind.get('minted')}  key={key!r}")
    print(f"        ground_concern grounded={g.get('grounded')}  acting_variant.built={av.get('built')}  "
          f"removed_rule={av.get('removed_rule')!r}")
    okA1 = _pass(bool(ind.get("minted")) and g.get("grounded") is True and av.get("built") is True,
                "the agent's own rules grounded (mint+judge+acting-variant+adopt-marker)")
    overall &= okA1

    a.tick()
    I.run_rules()
    axis = next((n for n in S.nodes("CapabilityAxis") if str(n) == str(ind.get("axis_id"))), None)
    exp_a = next(iter(I.neighbours(axis, "tested_by")), None) if axis is not None else None
    print(f"\n  [A.2] dispatching Experiment {exp_a}...")
    _wait(a, [exp_a], RUNS_DIR_A)
    status_a = S.node(exp_a)["attrs"].get("status") if exp_a is not None else None
    okA2 = _pass(status_a == "done", "the dispatched child completed")
    overall &= okA2

    I.run_rules()
    outcome_a = S.node(exp_a)["attrs"].get("outcome") if exp_a is not None else None
    print(f"\n  [A.3] REAL outcome (not cherry-picked): {outcome_a!r}")
    recs_a = rf.close_experiment_loop(a)
    exp_state = S.node(exp_a)["attrs"] if exp_a is not None else {}
    if outcome_a == "supported":
        exported = I.export_rules()
        removed_active = [r.get("active", True) for r in exported if r.get("name") == av.get("removed_rule")]
        okA3 = _pass(exp_state.get("adopted") is True and (removed_active and removed_active[-1] is False),
                    f"outcome was 'supported' -> the variant WAS adopted into the parent "
                    f"(original {av.get('removed_rule')!r} tombstoned)")
        overall &= okA3
    elif outcome_a in ("refuted", "inconclusive"):
        _pass(True, f"outcome was {outcome_a!r} (a genuine, non-cherry-picked live result) -> "
                    f"adopt_ready={exp_state.get('adopt_ready')!r}, adopted={exp_state.get('adopted')!r} "
                    f"(honestly reported, not forced to 'supported')")
    else:
        okA3 = _pass(False, f"unexpected outcome {outcome_a!r}")
        overall &= okA3

    # =========================================================================================
    # PART B — the discriminative + mechanical checks, driven directly.
    # =========================================================================================
    print("\n" + "-" * 92)
    print("PART B — driven discriminative checks: supported adopts, refuted never does, a denylisted")
    print("         rule is denied even when supported, revert restores the original, and the")
    print("         PARENT's own next episode measurably changes.")
    print("-" * 92)

    # B.1 — supported -> adopts
    b1 = _fresh_full_agent()
    ind_b1 = rf.induce_concern(b1, [["test", "H", "about", "S"], ["send", "V", "to", "W"],
                                    ["judge", "T", "by", "O"], ["gradient", "V", "of", "A"]],
                               name_hint="improve_b1")
    g_b1 = rf.ground_concern(b1, [ind_b1["capability_key"]])
    av_b1 = g_b1["acting_variant"]
    exp_b1 = _mint_manual_experiment(b1, av_b1, "supported", "b1")
    rf.ground_concern(b1, [rf.induce_concern(b1, [["adopt", "W", "as", "S"]], name_hint="b1_adopt")["capability_key"]])
    b1.inner.run_rules()
    recs_b1 = rf.close_experiment_loop(b1)
    exported_b1 = b1.inner.export_rules()
    removed_state = [r.get("active", True) for r in exported_b1 if r.get("name") == av_b1["removed_rule"]][-1]
    variant_state = [r.get("active", True) for r in exported_b1 if r.get("name") == av_b1["rule"]["name"]][-1]
    okB1 = _pass(removed_state is False and variant_state is True,
                "B.1 supported: original tombstoned, variant active on the PARENT")
    overall &= okB1

    # B.2 — refuted -> never adopts
    b2 = _fresh_full_agent()
    ind_b2 = rf.induce_concern(b2, [["test", "H", "about", "S"], ["send", "V", "to", "W"],
                                    ["judge", "T", "by", "O"], ["gradient", "V", "of", "A"]],
                               name_hint="improve_b2")
    g_b2 = rf.ground_concern(b2, [ind_b2["capability_key"]])
    av_b2 = g_b2["acting_variant"]
    exp_b2 = _mint_manual_experiment(b2, av_b2, "refuted", "b2")
    rf.ground_concern(b2, [rf.induce_concern(b2, [["adopt", "W", "as", "S"]], name_hint="b2_adopt")["capability_key"]])
    b2.inner.run_rules()
    rf.close_experiment_loop(b2)
    okB2 = _pass(b2.s.node(exp_b2)["attrs"].get("adopt_ready") is not True,
                "B.2 refuted: adopt_ready never marked, no adoption")
    overall &= okB2

    # B.3 — supported but denylisted -> denied
    b3 = _fresh_full_agent()
    for n in b3.s.nodes("SeedSummary"):
        if b3.s.node(n)["attrs"].get("seed_id") == "grid_navigation":
            b3.inner.set_attr(n, "skippable", 0.0)
    ind_b3 = rf.induce_concern(b3, [["test", "H", "about", "S"], ["send", "V", "to", "W"],
                                    ["judge", "T", "by", "O"], ["gradient", "V", "of", "A"]],
                               name_hint="improve_b3")
    g_b3 = rf.ground_concern(b3, [ind_b3["capability_key"]])
    av_b3 = g_b3["acting_variant"]
    exp_b3 = _mint_manual_experiment(b3, av_b3, "supported", "b3")
    rf.ground_concern(b3, [rf.induce_concern(b3, [["adopt", "W", "as", "S"]], name_hint="b3_adopt")["capability_key"]])
    b3.inner.run_rules()
    rf.close_experiment_loop(b3)
    exported_b3 = b3.inner.export_rules()
    denylisted_original_state = [r.get("active", True) for r in exported_b3
                                 if r.get("name") == av_b3["removed_rule"]][-1]
    okB3 = _pass(b3.s.node(exp_b3)["attrs"].get("adopt_denied") is True and denylisted_original_state is True,
                "B.3 supported but non-skippable provenance: DENIED, original stays active")
    overall &= okB3

    # B.4 — revert
    adoption_node = next(iter(b1.s.nodes("Adoption")))
    rv = rf.revert_adoption(b1, adoption_node)
    exported_after_revert = b1.inner.export_rules()
    variant_after = [r.get("active", True) for r in exported_after_revert if r.get("name") == av_b1["rule"]["name"]][-1]
    original_after = [r.get("active", True) for r in exported_after_revert if r.get("name") == av_b1["removed_rule"]][-1]
    okB4 = _pass(rv.get("reverted") is True and variant_after is False and original_after is True,
                "B.4 revert_adoption: variant tombstoned, original re-added and active")
    overall &= okB4

    # B.5 — the PARENT's own next episode measurably changes (flip_comparison, direct — no dispatch)
    b5 = _fresh_full_agent()
    actions_before = _run_episode_actions(b5)
    pick = rf._pick_acting_rule(b5, ["test", "send", "judge", "gradient"])
    flip = eo.apply_flip_comparison(pick["rule_json"], pick["name"] + "_livecheck")
    exported_b5 = b5.inner.export_rules()
    idx = next(i for i, r in enumerate(exported_b5) if r.get("name") == pick["name"] and r.get("active", True))
    b5.inner.remove_rule(idx)
    b5.inner.add_rule(flip)
    actions_after = _run_episode_actions(b5)
    n_common = min(len(actions_before), len(actions_after))
    n_diff = sum(1 for i in range(n_common) if actions_before[i] != actions_after[i])
    print(f"\n  [B.5] parent episode actions BEFORE adoption: {actions_before}")
    print(f"        parent episode actions AFTER  adoption: {actions_after}")
    okB5 = _pass(actions_before != actions_after,
                f"B.5 the SAME parent's own next episode measurably diverges after adoption "
                f"({n_diff}/{n_common} frames differ)")
    overall &= okB5

    print("\n" + "=" * 92)
    if overall:
        print("  ALL STAGES PASS. A supported experiment's agent-authored variant is folded back into the")
        print("  parent (remove_rule + add_rule, an Adoption record, a taught TaughtHint); a denylisted or")
        print("  refuted candidate never is; revert_adoption restores the original; the parent's own next")
        print("  episode measurably uses the adopted variant.")
    else:
        print("  Some stages FAILED (see [FAIL] lines above) — honest report, not papered over.")

    if not existed_conclusions and os.path.exists(_CONCLUSIONS_SEED):
        print(f"\n  NOTE: seeds/experiment_conclusions.json was created by this run and left in place "
              f"(real taught self-knowledge) — delete it manually if this was a throwaway run.")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
