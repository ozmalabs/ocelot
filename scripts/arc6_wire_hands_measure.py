#!/usr/bin/env python3
"""Measure A11/WH1-WH3 — WIRING THE HANDS TO THE ORDER-N COLLAPSE.

MEASUREMENT ONLY.  Nothing here decides anything about the agent: it boots,
runs the fixpoint, hands the graph's own orders to the adapter, and READS the
graph back.  Every number in the artifact is a read-off and the engine that
produced it is stamped — a number from an unknown binary is not a measurement
(prereg A1.1).

THE CONTROL IS THE POINT, AND IT RUNS IN THE SAME PROCESS ON THE SAME ENGINE.
`ax_dispatch` at `HEAD` binds `arc_sel_agid`; `ax_dispatch` in this worktree
binds `SEL_AGID()`.  Rather than compare against a number quoted from another
rung's write-up, this script loads **`git show HEAD:seeds/arc_executor.json`**
into a second substrate and runs the identical scene through it.  The two arms
then differ by the seed and by nothing else — not by the binary, not by the
worktree, not by the day.

Run:  OZMA_NO_LLM=1 python scripts/arc6_wire_hands_measure.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"),
           os.path.join(ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import substrate_rs as srs  # noqa: E402

from domains import arc_executor as axe  # noqa: E402
from domains import arc_goal_ingest as agi  # noqa: E402
from domains import arc_magnitude_ingest as ami  # noqa: E402
from domains import goal_residual_ingest as gri  # noqa: E402
from domains.engine_provenance import provenance_stamp  # noqa: E402
from substrate.seed_loader import manifest_for, normalize_declarative  # noqa: E402

OUT = os.path.join(ROOT, "results", "arc6_wire_hands.json")
RID = "arc6.verdict.row_verdict_seed_only"
AGID = "arc.remeasure." + RID
BLOCKER = "arc.supply.arc6.seam_a.import_oracle.missing_structural_primitive"

FULL = ("program_synthesis", "goal_residuals", "arc_goals", "arc_magnitude",
        "arc_executor")
NO_MAG = ("program_synthesis", "goal_residuals", "arc_goals", "arc_executor")


# =========================================================================== #
#  Boot.  `seed_variant="head"` installs the PRE-CHANGE executor seed, read
#  straight out of git — the paired control, same process, same engine.
# =========================================================================== #
def _head_executor_manifest() -> dict:
    prefix = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                            capture_output=True, text=True).stdout.strip()
    blob = subprocess.run(
        ["git", "-C", ROOT, "show", "HEAD:" + prefix + "seeds/arc_executor.json"],
        capture_output=True, text=True, check=True).stdout
    return normalize_declarative(json.loads(blob))


def boot(seeds=FULL, ladder=True, seed_variant="worktree"):
    s = srs.Substrate()
    ag = s.add_node("Agent", {})
    cls = s.add_node("Agent", {"is_class": True})
    s._inner.add_edge_unchecked(ag, "is_a", cls)
    for sid in seeds:
        if sid == "arc_executor" and seed_variant == "head":
            s._inner.load_seed_manifest(_head_executor_manifest(), ag)
        else:
            s._inner.load_seed_manifest(manifest_for(sid), ag)
    s._inner.load_seed_manifest(manifest_for("math_capability_shapes"), ag)
    #  Assert the engine, do not merely record it.
    probe = s.add_node("ExecEngineProbe", {"lst": [1, 2, 3], "tup": (1, 2, 3)})
    pa = s.node(probe)["attrs"]
    assert pa["lst"] != pa["tup"], "VALUE LAYER ABSENT — stop, do not re-pin"
    gri.install_facts(s, gri.probe_facts(s))
    agi.set_measure_epoch(s, 0)
    if "arc_magnitude" in seeds:
        ami.resolve_attrition_keys(s)
        if ladder:
            ami.install_tier_ladder(s, ami.probe_tier_ladder())
    return s, ag


def _agenda(s):
    return [n for n in s.nodes("ArcAgenda")][0]


def _goal(s, agid=AGID):
    for n in s.nodes("ArcGoal"):
        if s.node(n)["attrs"].get("agid") == agid:
            return n
    return None


def _res(s, rid=RID):
    for n in s.nodes("GoalResidual"):
        if s.node(n)["attrs"].get("rid") == rid:
            return n
    return None


def _orders(s):
    return [dict(s.node(n)["attrs"]) for n in s.nodes("ExecOrder")]


def _order_row(o):
    return {k: o.get(k) for k in
            ("agid", "runner", "status", "selected_by", "selected_value",
             "order1_sel_agid", "orderN_sel_agid", "ordered_epoch",
             "ran_epoch", "artifact", "outcome")}


def _state(s, label):
    r, g = _res(s), _goal(s)
    at = s.node(_agenda(s))["attrs"]
    return {
        "label": label,
        "measure_epoch": agi.measure_epoch(s),
        "pool": axe.pool(s),
        "pool_n": len(axe.pool(s)),
        "arc_sel_agid": at.get("arc_sel_agid"),
        "arc_sel_value": at.get("arc_sel_value"),
        "arc_sel_margin": at.get("arc_sel_margin"),
        "mg_sel_agid": at.get("mg_sel_agid"),
        "mg_sel_value": at.get("mg_sel_value"),
        "mg_sel_margin": at.get("mg_sel_margin"),
        "the_two_collapses_agree": at.get("arc_sel_agid") == at.get("mg_sel_agid"),
        "remeasure_goal_status": None if g is None else s.node(g)["attrs"].get("status"),
        "remeasure_goal_retired_because":
            None if g is None else s.node(g)["attrs"].get("retired_because"),
        "source_residual_stale": None if r is None else s.node(r)["attrs"].get("stale"),
        "orders": [_order_row(o) for o in _orders(s)],
        "open_questions": list(agi.questions(s)),
        "n_open_questions": len([q for q in agi.questions(s)
                                 if q.get("status") == "open"]),
    }


# =========================================================================== #
#  WH1 — THE STAMP SWAP IS BEHAVIOURALLY VISIBLE
# =========================================================================== #
def wh1_stamp_swap():
    """Four arms, one process, one engine.  Nobody replies to anything in any
    of them — the scene is the SHIPPED BOOT and nothing else."""
    arms = {}

    def arm(name, seeds, ladder, variant):
        s, _ = boot(seeds, ladder=ladder, seed_variant=variant)
        s._inner.run_rules()
        at = s.node(_agenda(s))["attrs"]
        before = {
            "arc_sel_agid": at.get("arc_sel_agid"),
            "arc_sel_value": at.get("arc_sel_value"),
            "mg_sel_agid": at.get("mg_sel_agid"),
            "mg_sel_value": at.get("mg_sel_value"),
            "mg_sel_orderN_headroom_n": at.get("mg_sel_orderN_headroom_n"),
            "mg_sel_order1_headroom_n": at.get("mg_sel_order1_headroom_n"),
            "the_two_collapses_agree":
                at.get("arc_sel_agid") == at.get("mg_sel_agid"),
        }
        armed = axe.arm(s)
        s._inner.run_rules()
        rows = [_order_row(o) for o in _orders(s)]
        arms[name] = {
            "seeds": list(seeds), "tier_ladder": ladder,
            "executor_seed": variant,
            "executor_seed_version": (
                _head_executor_manifest() if variant == "head"
                else manifest_for("arc_executor")).get("version"),
            "selection": before,
            "armed": armed,
            "orders": rows,
            "acted_on": [r["agid"] for r in rows],
            "human_replies": 0,
        }

    arm("A_orderN_wired_ladder_installed", FULL, True, "worktree")
    arm("B_CONTROL_HEAD_seed_same_scene", FULL, True, "head")
    arm("C_orderN_wired_NO_tier_ladder", FULL, False, "worktree")
    arm("D_orderN_wired_arc_magnitude_ABSENT", NO_MAG, True, "worktree")

    a, b = arms["A_orderN_wired_ladder_installed"], \
        arms["B_CONTROL_HEAD_seed_same_scene"]
    acted = a["acted_on"]
    order1_winner = a["selection"]["arc_sel_agid"]
    orderN_winner = a["selection"]["mg_sel_agid"]
    return {
        "arms": arms,
        "the_executor_acted_on": acted,
        "order_1_would_have_chosen": order1_winner,
        "order_N_chose": orderN_winner,
        "acted_on_a_goal_order_1_did_NOT_choose":
            acted == [orderN_winner] and orderN_winner != order1_winner,
        "the_HEAD_seed_in_the_SAME_scene_acted_on": b["acted_on"],
        "no_human_reply_in_any_arm": all(v["human_replies"] == 0
                                         for v in arms.values()),
        "verdict": "PASS" if (
            acted == [orderN_winner]
            and orderN_winner != order1_winner
            and b["acted_on"] == []
            and arms["C_orderN_wired_NO_tier_ladder"]["acted_on"] == []
            and arms["D_orderN_wired_arc_magnitude_ABSENT"]["acted_on"] == []
        ) else "FAIL",
        "_reading": (
            "Arm A is the swap: the order-1 collapse names the 42-task blocker "
            "and the executor orders the ORDER-N winner instead, stamped "
            "selected_by=order_n_mg_select, with NO human reply anywhere in the "
            "scene.  Arm B is the same scene through HEAD's own seed and mints "
            "NOTHING -- so the difference is the seed, not the day.  Arms C and "
            "D are the two ways the divergence can be absent: without the "
            "measured tier ladder the two collapses AGREE (so this is the "
            "LADDER's divergence, exactly as AG-5 SS8.9 measured it), and "
            "without arc_magnitude at all the fallback restores the order-1 "
            "wiring byte-for-byte.  All three non-A arms refuse for the SAME "
            "structural reason: the winner they hold has no ExecClass."),
    }


# =========================================================================== #
#  WH2 — THE LOOP ACTS WITHOUT BEING ASKED
# =========================================================================== #
def wh2_loop(max_iters=6, seeds=FULL, ladder=True, seed_variant="worktree",
             tag_prefix="wh2", answer_questions=False):
    """AG-5's EX5 loop, with ONE thing changed: nobody answers anything.

    `ex5_the_loop` in `scripts/arc6_executor_measure.py` replies to every open
    question each iteration, and AG-5 measured that the reply is what let the
    loop act at all (its SS8.3: an unconditioned answer penalises the region it
    is about, which is what dropped the blocker below the re-measurement goal).
    Here `answer_questions` defaults to **False** — the world is silent."""
    s, _ = boot(seeds, ladder=ladder, seed_variant=seed_variant)
    trace, executions = [], []
    stop_reason = "max_iters"
    replies_sent = 0

    for i in range(max_iters):
        s._inner.run_rules()
        step = {"iteration": i}
        step.update(_state(s, "plan"))
        if answer_questions:
            for n in s.nodes("ArcQuestion"):
                a = s.node(n)["attrs"]
                if a.get("answered") == 1.0 or a.get("status") != "open":
                    continue
                agi.attach_reply(s, n, "I do not know either; use your judgement.")
                replies_sent += 1
            s._inner.run_rules()
        step["armed"] = axe.arm(s)
        s._inner.run_rules()
        pending = axe.pending_orders(s)
        step["pending_orders"] = [s.node(n)["attrs"].get("agid") for n in pending]
        if not pending:
            step["dispatched"] = False
            step["why_nothing_dispatched"] = _why_no_dispatch(s)
            trace.append(step)
            stop_reason = "no_executable_goal_was_selected"
            break
        step["dispatched"] = True
        step["before_execution"] = _state(s, "pre_exec")
        for n in pending:
            rec = axe.run_order(s, n, tag="%s_i%d_e%s"
                                % (tag_prefix, i, agi.measure_epoch(s)))
            executions.append({k: rec.get(k) for k in
                               ("agid", "runner", "status", "artifact",
                                "artifact_sha256", "elapsed_seconds",
                                "ran_at_epoch", "epoch_after", "engine_sha256",
                                "protected_files_restored_byte_identical")})
            step["execution"] = executions[-1]
        axe.refresh_evidence_facts(s)
        s._inner.run_rules()
        step["after_execution"] = _state(s, "post_exec")
        trace.append(step)

    return s, {
        "world_answers_questions": bool(answer_questions),
        "human_replies_sent": replies_sent,
        "executor_seed": seed_variant,
        "tier_ladder": ladder,
        "seeds": list(seeds),
        "trace": trace,
        "executions": executions,
        "n_executions": len(executions),
        "stop_reason": stop_reason,
    }


def _why_no_dispatch(s):
    at = s.node(_agenda(s))["attrs"]
    #  Which stamp the SHIPPED rule reads, read the same way the rule reads it.
    followed = ("order_1_ag_select" if at.get("mg_sel_agid") is None
                else "order_n_mg_select")
    sel = (at.get("arc_sel_agid") if at.get("mg_sel_agid") is None
           else at.get("mg_sel_agid"))
    g = _goal(s, sel) if sel else None
    kind = None if g is None else s.node(g)["attrs"].get("kind")
    classes = [c[0] for c in axe.exec_classes(s)]
    return {
        "collapse_the_rule_follows": followed,
        "its_winner": sel,
        "winner_kind": kind,
        "winner_status": None if g is None else s.node(g)["attrs"].get("status"),
        "exec_classes_available": classes,
        "kind_is_routable": kind in classes,
        "arc_sel_agid": at.get("arc_sel_agid"),
        "mg_sel_agid": at.get("mg_sel_agid"),
        "n_open_questions": len([q for q in agi.questions(s)
                                 if q.get("status") == "open"]),
    }


def wh2_report(loop_n, loop_1):
    """The bar: did the loop reach the executable goal with NOBODY in it?"""
    acted = [e["agid"] for e in loop_n["executions"]]
    return {
        "ORDER_N_no_ask": {
            "human_replies_sent": loop_n["human_replies_sent"],
            "executions": acted,
            "n_executions": loop_n["n_executions"],
            "stop_reason": loop_n["stop_reason"],
            "iterations": len(loop_n["trace"]),
        },
        "CONTROL_HEAD_seed_no_ask": {
            "human_replies_sent": loop_1["human_replies_sent"],
            "executions": [e["agid"] for e in loop_1["executions"]],
            "n_executions": loop_1["n_executions"],
            "stop_reason": loop_1["stop_reason"],
            "iterations": len(loop_1["trace"]),
        },
        "reached_the_executable_goal_with_NO_human_reply":
            acted == [AGID] and loop_n["human_replies_sent"] == 0,
        "the_HEAD_wiring_reached_it_with_no_reply":
            bool(loop_1["executions"]),
        "verdict": "PASS" if (acted == [AGID]
                              and loop_n["human_replies_sent"] == 0
                              and not loop_1["executions"]) else "FAIL",
    }


# =========================================================================== #
#  WH3 — NO REGRESSION.  Suites + the 48 paired ids.
# =========================================================================== #
def wh3_no_regression(run_suites=True):
    suites = ("test_arc_executor_migrated", "test_arc_goals_migrated",
              "test_goal_residual_migrated", "test_arc6_valuelayer_migrated",
              "test_arc_magnitude_migrated")
    out = {}
    if run_suites:
        env = dict(os.environ)
        env["COLUMNS"] = "250"
        env["PYTHONPATH"] = os.pathsep.join(
            [os.path.join(ROOT, "runners", "dsl", "python"), ROOT,
             env.get("PYTHONPATH", "")]).rstrip(os.pathsep)
        for name in suites:
            r = subprocess.run(
                [sys.executable, "-m", "pytest",
                 os.path.join(ROOT, "tests", name + ".py"),
                 "--confcutdir=" + ROOT, "-q", "-p", "no:randomly", "-rf"],
                capture_output=True, text=True, cwd=ROOT, env=env)
            tail = [l for l in r.stdout.strip().splitlines()
                    if " passed" in l or " failed" in l]
            line = tail[-1] if tail else r.stdout[-300:]
            failed_ids = sorted(re.findall(r"^FAILED [^:]+::(\S+)", r.stdout,
                                           re.M))
            p = re.search(r"(\d+) passed", line)
            f = re.search(r"(\d+) failed", line)
            out[name] = {"passed": int(p.group(1)) if p else None,
                         "failed": int(f.group(1)) if f else 0,
                         "failed_ids": failed_ids, "line": line}
    gr4 = os.path.join(ROOT, "results", "arc6_verdict_gr4_gate.json")
    doc = json.load(open(gr4)) if os.path.exists(gr4) else {}
    out["live_mbpp_pass_ids"] = {
        "n": len(doc.get("pass_ids", [])) or None,
        "ids": doc.get("pass_ids"),
        "n_accepted": len(doc.get("accepted_ids", [])) or None,
        "engine": (doc.get("engine_provenance") or {}).get("short"),
        "source": "results/arc6_verdict_gr4_gate.json, rewritten live by "
                  "test_goal_residual_migrated::test_gr4_the_live_mbpp_pass_"
                  "ids_are_unchanged during this run",
    }
    return out


# =========================================================================== #
def main():
    t0 = time.time()
    run_suites = "--no-suites" not in sys.argv
    wh1 = wh1_stamp_swap()
    s_n, loop_n = wh2_loop(seeds=FULL, ladder=True, seed_variant="worktree",
                           tag_prefix="wh2n")
    _s1, loop_1 = wh2_loop(seeds=FULL, ladder=True, seed_variant="head",
                           tag_prefix="wh2head")
    wh2 = wh2_report(loop_n, loop_1)

    h = hashlib.sha256()
    with open(os.path.join(ROOT, "seeds", "arc_executor.json"), "rb") as fh:
        h.update(fh.read())
    rec = {
        "_README": (
            "A11 / WH1-WH3 — WIRING THE HANDS TO THE ORDER-N COLLAPSE.  The "
            "bars were registered in PROGRAM_SYNTHESIS_ARC6_PREREG.md amendment "
            "A11 BEFORE this change.  Every arm ran in ONE process on ONE "
            "engine, and the pre-change control is HEAD's own "
            "seeds/arc_executor.json loaded from git into a second substrate — "
            "so the arms differ by the seed and by nothing else."),
        "measured_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine_provenance": provenance_stamp(),
        "seed_sha256": h.hexdigest(),
        "seed_version": manifest_for("arc_executor").get("version"),
        "WH1_the_stamp_swap_is_behaviourally_visible": wh1,
        "WH2_the_loop_acts_without_being_asked": wh2,
        "WH2_trace_order_N_no_ask": loop_n,
        "WH2_trace_CONTROL_head_seed_no_ask": loop_1,
        "WH3_no_regression": wh3_no_regression(run_suites),
        "elapsed_seconds": None,
    }
    rec["elapsed_seconds"] = round(time.time() - t0, 2)
    with open(OUT, "w") as fh:
        json.dump(rec, fh, indent=2, sort_keys=False, default=str)
    print("wrote", OUT, "in %.1fs" % rec["elapsed_seconds"])
    print("WH1", wh1["verdict"], "| acted on:", wh1["the_executor_acted_on"],
          "| order-1 wanted:", wh1["order_1_would_have_chosen"])
    print("WH2", wh2["verdict"], "|", json.dumps(wh2["ORDER_N_no_ask"]))
    print("WH2 control |", json.dumps(wh2["CONTROL_HEAD_seed_no_ask"]))
    for k, v in rec["WH3_no_regression"].items():
        if isinstance(v, dict) and "passed" in v:
            print("%-40s %s" % (k, v["line"]))


if __name__ == "__main__":
    main()
