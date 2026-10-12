#!/usr/bin/env python3
"""Tranche 21: endemic RSI on the PRODUCTION path.

Tranche 20 measured endemic self-improvement with the harness calling
WorldAdapter.converse(text, speech_act="request") and the daemon's hooks
directly. The production daemon does neither:
  * a chat turn is `_ingest_daemon_chat_turn` -> ingest_turn(classified speech
    act), then the tick loop's comprehend / settle / release_graph_selected_
    response;
  * host work (steer, concern, dispatch, close) runs only when the graph's
    supervisory scheduler mints a HostActionRequest
    (`_execute_host_action_requests`);
  * it boots the `conversation` seed profile, not a full boot.

This harness reproduces exactly that loop in-process: the daemon's own
DaemonState, tick-loop body, and host-action executor, on the conversation
profile, with shadow read on or off. No direct hook calls.

Stream: `requests` (the tranche-20 natural request fixture) or `persona` (User
1's turns of persona_chat_20). For every turn it records the released reply.
After the stream, the same turns are replayed through the production path on
the post-run agent and on a fresh boot, so a behaviour change is measured
where production would see it.

Writes evaluation/reports/endemic_rsi_daemon_v1_<stream>_<shadow>_20261010.json.
Usage: <this> <requests|persona> <shadow|plain> [n_turns]
"""
import collections, json, os, re, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
ERR = "ERROR: no communicative response could be generated."
IDLE_WAIT_S = 240
# tranche 23: real imperatives, retested after the stream on both agents -- a
# correction of the shallow reader must not stop these being taken as goals
CONTROL_IMPERATIVES = ["Bake the cake.", "Write the book.", "Paint the fence.", "Open the door.",
                       "Plant the tree.", "Clean the kitchen."]


def boot(shadow, promote=None):
    import jabberwock_daemon as jd
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_profiles import load_conversation_seed_profile
    a = WorldAdapter(seeds=())
    rep = load_conversation_seed_profile(a)
    assert rep.get("selection_complete") and not rep.get("failed"), rep.get("failed")
    a.shadow_read = shadow
    a.deep_ingest = shadow
    a.turn_path = "production"
    jd._ensure_supervisory_scheduler(a)
    if promote is None:
        promote = os.environ.get("ERSI_SELF_PROMOTION") != "0"
    if not promote:     # the off arm (a human must promote), and the fresh-boot baseline
        for n in a.s.nodes("SelfPromotionPolicy"):
            a.s.set_attr(n, "enabled", 0)
    if os.environ.get("ERSI_REOPEN") == "0":    # tranche 24 chain-off arm: no reopen on a new capability
        for n in a.s.nodes("InstructionRetryPolicy"):
            a.s.set_attr(n, "max_reopens", 0)
    st = jd.DaemonState(a, "seeds")
    st.runs_dir = tempfile.mkdtemp(prefix="ersid-")
    return st


def one_cycle(st):
    """The body of jabberwock_daemon.tick_loop for one wake-up, plus its host-action execution."""
    import jabberwock_daemon as jd
    import substrate_rs as srs
    a = st.adapter
    with jd.AGENT_LOCK:
        budget, quantum = jd._async_cycle_budget(a)
        if quantum is None:
            a.tick()
        else:
            n = a.tick(max_steps=quantum)
            jd._record_async_cycle_consumption(a, budget, quantum, n)
        done = {}
        if st.pending_turns:
            a.comprehend()
            a.settle_post_comprehension_authority(list(st.pending_turns))
            for tid in list(st.pending_turns):
                reply = a.release_graph_selected_response(srs.NodeID(tid))
                status = "reply_released" if reply is not None else a.graph_turn_reply_outcome(tid)
                if status in ("expected", "unrepresented", "reply_ready"):
                    continue
                if status == "explicit_error":
                    reply = a.graph_turn_reply(tid)
                a.record_turn_outcome(tid, status)
                done[tid] = (status, reply)
                st.pending_turns.pop(tid, None)
        jd._execute_host_action_requests(st)
    return done


def say(st, text, max_cycles=60):
    import jabberwock_daemon as jd
    with jd.AGENT_LOCK:
        tid = jd._ingest_daemon_chat_turn(st, text)
    for _ in range(max_cycles):
        done = one_cycle(st)
        if tid in done:
            return done[tid]
    return ("timeout", None)


def busy(st):
    s = st.adapter.s
    for n in s.nodes("Experiment"):
        at = s.node(n)["attrs"]
        if at.get("status") in ("requested", "running") and at.get("outcome") is None \
                and str(at.get("axis_tag") or "").startswith("promoted_self_concern_"):
            return True
    for n in s.nodes("StandingConcern"):
        at = s.node(n)["attrs"]
        if at.get("status") == "pending" and at.get("source") == "conversation_promoted":
            return True
    for n in s.nodes("SelfConcern"):
        at = s.node(n)["attrs"]
        if (at.get("promote_requested") == 1.0 and at.get("status") == "noted") or at.get("retry_requested") == 1:
            return True
    return False


def settle(st):
    """Idle ticks, as a running daemon would have between turns, until the loop is idle."""
    t0 = time.time()
    cycles = 0
    while time.time() - t0 < IDLE_WAIT_S:
        one_cycle(st)
        cycles += 1
        if cycles >= 3 and not busy(st):
            break
        time.sleep(0.2)
    return cycles


def classify(reply):
    r = (reply or "").strip()
    if not r or r == ERR:
        return "error_or_none"
    if "hold no faculty" in r.lower() or "filed it as a gap" in r.lower():
        return "gap_floor"
    if r.startswith("I took on the goal to") or "is deferred" in r:
        return "goal_take"
    return "other"


def stream_turns(kind, n):
    if kind == "requests":
        reqs = json.loads((ROOT / "evaluation/fixtures/endemic_requests_v1.json").read_text())["requests"]
        return [r["text"] for r in reqs][:n]
    d = json.loads((ROOT / "data/corpus/persona_chat_20.json").read_text())
    out = [t for dlg in d for spk, t in dlg["turns"] if spk == "User 1"]
    return out[:n]


def snapshot(st):
    s = st.adapter.s
    concerns = collections.Counter(str(s.node(n)["attrs"].get("kind")) for n in s.nodes("SelfConcern"))
    exps = []
    for n in s.nodes("Experiment"):
        at = s.node(n)["attrs"]
        if not str(at.get("axis_tag") or "").startswith("promoted_self_concern_"):
            continue
        ds = list(st.adapter.inner.neighbours(n, "has_delta"))
        da = s.node(ds[0])["attrs"] if ds else {}
        exps.append({"axis": at.get("axis_tag"), "status": at.get("status"), "outcome": at.get("outcome"),
                     "adopted": bool(at.get("adopted")), "op": da.get("variation_op"),
                     "abstained": bool(da.get("variant_abstained")), "route": da.get("cue_route"),
                     "rule": da.get("act_rule_varied"), "error": str(at.get("error") or "")[:200],
                     "quality_delta": at.get("quality_delta"), "quality_drops": at.get("quality_drops"),
                     "quality_gains": at.get("quality_gains")})
    adoptions = [{k: s.node(n)["attrs"].get(k) for k in ("rule_removed", "rule_added", "cue_concept_added",
                                                         "cue_route", "knob_attr", "experiment_id")}
                 for n in s.nodes("Adoption")]
    self_promoted = sum(1 for n in s.nodes("SelfConcern") if s.node(n)["attrs"].get("promoted_by") == "self")
    actions = collections.Counter(str(s.node(n)["attrs"].get("action")) for n in s.nodes("HostActionRequest"))
    # tranche 24: reopened concerns, and adoptions built on an earlier adoption's
    # own rule (a second-order generalisation carries "_generalised__" in its name)
    reopened = [{"concern": int(n.value), "kind": s.node(n)["attrs"].get("kind"),
                 "reopen_count": s.node(n)["attrs"].get("reopen_count")}
                for n in s.nodes("SelfConcern") if s.node(n)["attrs"].get("reopen_count")]
    chained = [ad["rule_added"] for ad in adoptions if "_generalised__" in str(ad.get("rule_added") or "")]
    return {"concerns_by_kind": dict(concerns), "self_promoted": self_promoted, "experiments": exps,
            "adoptions": adoptions, "host_actions": dict(actions), "reopened": reopened,
            "chained_adoptions": chained}


def main():
    import faulthandler, signal
    faulthandler.register(signal.SIGUSR1, all_threads=True)
    kind, shadow_arm = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 6
    arm = "_off" if os.environ.get("ERSI_SELF_PROMOTION") == "0" else ""
    arm += "_noreopen" if os.environ.get("ERSI_REOPEN") == "0" else ""
    label = os.environ.get("ERSI_LABEL", "")
    out = ROOT / (f"evaluation/reports/endemic_rsi_daemon_v1_{kind}_{shadow_arm}{'' if n >= 10**6 else f'_n{n}'}"
                  f"{arm}{('_' + label) if label else ''}_20261010.json")
    if out.exists():
        raise SystemExit("refusing to overwrite")
    shadow = shadow_arm == "shadow"
    turns = stream_turns(kind, n)
    st = boot(shadow)
    t0 = time.time()
    rows = []
    say(st, "Hello.")
    for i, text in enumerate(turns):
        status, reply = say(st, text)
        cycles = settle(st)
        rows.append({"i": i, "text": text, "status": status, "reply": (reply or "")[:200],
                     "class": classify(reply), "settle_cycles": cycles})
        print(json.dumps(rows[-1])[:300], flush=True)
    print("STREAM_DONE", flush=True)
    live = snapshot(st)
    out.with_suffix(".live.json").write_text(json.dumps({"rows": rows, "live": live}, indent=1, default=str) + "\n")
    print("LIVE", json.dumps(live, default=str)[:3000], flush=True)
    # behaviour where production sees it: the same turns, production path, post-run agent vs fresh boot
    from domains import reply_quality as rq
    after_replies = [(say(st, t, max_cycles=15)[1] or "") for t in turns]
    after = [classify(r) for r in after_replies]
    controls_after = [classify(say(st, t, max_cycles=15)[1]) for t in CONTROL_IMPERATIVES]
    # tranche 23: the baseline must not improve itself during its own retest
    # (say() runs the host-action loop) -- before this, the fresh boot could
    # self-promote and adopt mid-retest, understating every post-run gain
    fresh = boot(shadow, promote=False)
    say(fresh, "Hello.")
    before_replies = [(say(fresh, t, max_cycles=15)[1] or "") for t in turns]
    before = [classify(r) for r in before_replies]
    controls_before = [classify(say(fresh, t, max_cycles=15)[1]) for t in CONTROL_IMPERATIVES]
    fresh_adoptions = len(fresh.adapter.s.nodes("Adoption"))
    # P0 (open-ended plan): ReplyQuality v1, report-only, on both retests
    q_after = [rq.assess(t, r) for t, r in zip(turns, after_replies)]
    q_before = [rq.assess(t, r) for t, r in zip(turns, before_replies)]
    quality = {
        "post_run": rq.summarise([q["score"] for q in q_after]),
        "fresh_boot": rq.summarise([q["score"] for q in q_before]),
        "changed_turns": rq.summarise([qa["score"] for qa, qb, a, b in zip(q_after, q_before, after_replies, before_replies)
                                       if a != b]),
        "changed_turns_before": rq.summarise([qb["score"] for qa, qb, a, b in zip(q_after, q_before, after_replies,
                                                                                   before_replies) if a != b]),
        "drops": sum(1 for qa, qb in zip(q_after, q_before) if qa["score"] < qb["score"]),
        "gains": sum(1 for qa, qb in zip(q_after, q_before) if qa["score"] > qb["score"]),
        "transitions": dict(collections.Counter(f"{qb['reason']} => {qa['reason']}"
                                                for qa, qb, a, b in zip(q_after, q_before, after_replies, before_replies)
                                                if a != b)),
    }
    summ = {
        "turns": len(turns), "elapsed_s": round(time.time() - t0, 1),
        "first_pass": dict(collections.Counter(r["class"] for r in rows)),
        "retest_post_run": dict(collections.Counter(after)),
        "retest_fresh_boot": dict(collections.Counter(before)),
        "changed_turns": sum(1 for x, y in zip(after, before) if x != y),
        "to_error": sum(1 for x, y in zip(after, before) if x == "error_or_none" and y != "error_or_none"),
        "controls_post_run": dict(zip(CONTROL_IMPERATIVES, controls_after)),
        "controls_fresh_boot": dict(zip(CONTROL_IMPERATIVES, controls_before)),
        "fresh_boot_adoptions": fresh_adoptions,
        "reply_quality": quality,
        **{k: v for k, v in live.items() if k != "experiments"},
        "experiments_n": len(live["experiments"]),
        "experiments_by_op_outcome": dict(collections.Counter(
            f"{x['op']}:{x['outcome'] or x['status']}" for x in live["experiments"])),
    }
    print("SUMMARY", json.dumps(summ), flush=True)
    out.write_text(json.dumps({"schema": "EndemicRSIDaemonV1", "stream": kind, "shadow": shadow, "rows": rows,
                               "experiments": live["experiments"], "retest_post_run": after,
                               "retest_fresh_boot": before,
                               "retest_post_run_replies": [r[:300] for r in after_replies],
                               "retest_fresh_boot_replies": [r[:300] for r in before_replies],
                               "retest_post_run_quality": q_after, "retest_fresh_boot_quality": q_before,
                               "summary": summ}, indent=1, default=str) + "\n")


if __name__ == "__main__":
    main()
