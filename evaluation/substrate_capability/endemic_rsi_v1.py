#!/usr/bin/env python3
"""Tranche 20: ENDEMIC recursive self-improvement, measured.

No steer turns and no hand-filed concerns. The stream is natural requests
derived from persona_chat_8938 (scripts/gen_endemic_requests.py ->
evaluation/fixtures/endemic_requests_v1.json): verbs people actually use in
conversation, each with the object they most often take in the corpus. The
agent's own rules file the gaps; self_promotion promotes them; the experiment
pipeline varies, replays, judges and adopts. The harness only feeds turns
and runs the daemon's own hooks in the daemon's order (steer, concern,
dispatch, close), exactly as a running daemon would on idle ticks.

Arms (one per process):
  off     SelfPromotionPolicy.enabled = 0 (the pre-tranche-20 agent: a human must promote)
  on      self-promotion, the held cue_route_pick as committed
  credit  self-promotion + route credit: cue_route_pick ranks candidate routes by
          the success rate of the route over the agent's own judged cue
          experiments (VariationOp{cue_set_edit}.route_credit=1, variation_ops v1.18.0)

After the stream, a RETEST pass replays every request: handled = the turn's
instruction_outcome is 'handled', the reply is not the error floor and does not
file a gap. Writes evaluation/reports/endemic_rsi_v1_<arm>_20261010.json.
Usage: <this> <arm> [n_requests|all] [label]
"""
import json, os, shutil, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
REQS = ROOT / "evaluation/fixtures/endemic_requests_v1.json"
ERR = "ERROR: no communicative response could be generated."
MAX_CYCLES = 10


def handled(a, reply):
    mid = a._last_turn_inbound
    at = a.s.node(mid)["attrs"] if mid is not None else {}
    r = (reply or "").strip()
    return (at.get("instruction_outcome") == "handled" and r != ERR
            and "filed it as a gap" not in r.lower() and "hold no faculty" not in r.lower())


def idle(a):
    s = a.s
    if any(s.node(n)["attrs"].get("status") == "pending" for n in s.nodes("StandingConcern")):
        return False
    if any(s.node(n)["attrs"].get("status") in ("requested", "running") and s.node(n)["attrs"].get("outcome") is None
           for n in s.nodes("Experiment")):
        return False
    for n in s.nodes("SelfConcern"):
        at = s.node(n)["attrs"]
        if (at.get("promote_requested") == 1.0 and at.get("status") == "noted") or at.get("retry_requested") == 1:
            return False
    return True


def run(arm, n_req):
    import test_agent_authors_new_rule_migrated as T
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=(), shadow_read=True)
    if os.environ.get("ERSI_PROFILE") == "conversation":   # the daemon's default production profile
        from substrate.boot_profiles import load_conversation_seed_profile
        load_conversation_seed_profile(a)
    else:
        load_all_seeds(a)
    for n in a.s.nodes("SelfPromotionPolicy"):
        a.s.set_attr(n, "enabled", 0 if arm == "off" else 1)
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == "cue_set_edit":
            a.s.set_attr(n, "route_credit", 1 if arm == "credit" else 0)
    if not list(a.s.nodes("SelfPromotionPolicy")):
        raise SystemExit("self_promotion seed not loaded")
    reqs = json.loads(REQS.read_text())["requests"][:n_req]
    a.converse("Hello.", speech_act="greeting")
    runs = Path(tempfile.mkdtemp(prefix=f"ersi-{arm}-"))
    rows, t_start = [], time.time()
    for i, req in enumerate(reqs):
        reply = a.converse(req["text"], speech_act="request") or ""
        rec = {"i": i, "verb": req["verb"], "text": req["text"], "first_reply": reply[:160],
               "gap_filed": "filed it as a gap" in reply.lower(), "handled_first": handled(a, reply), "experiments": []}
        a.inner.run_rules()
        for cyc in range(MAX_CYCLES):
            jd._steer_tick(a)
            jd._concern_tick(a)
            exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
                    and a.s.node(e)["attrs"].get("status") == "requested"]
            for exp in exps:
                deltas = list(a.inner.neighbours(exp, "has_delta"))
                da = a.s.node(deltas[0])["attrs"] if deltas else {}
                t0 = time.time()
                st = T._dispatch_until(a, runs / f"{i}-{cyc}", exp)
                a.comprehend(); a.inner.run_rules(); rf.close_experiment_loop(a)
                at = a.s.node(exp)["attrs"]
                rec["experiments"].append({"cycle": cyc, "axis": at.get("axis_tag"), "op": da.get("variation_op"),
                                           "route": da.get("cue_route"), "verb": da.get("cue_concept_added"),
                                           "status": st, "outcome": at.get("outcome"),
                                           "adopted": bool(at.get("adopted")), "child_s": round(time.time() - t0, 1)})
                shutil.rmtree(runs / f"{i}-{cyc}", ignore_errors=True)
            a.inner.run_rules()
            if not exps and idle(a):
                break
        rec["self_promoted"] = sum(1 for n in a.s.nodes("SelfConcern")
                                   if a.s.node(n)["attrs"].get("promoted_by") == "self")
        rows.append(rec)
        print(json.dumps(rec, default=str)[:700], flush=True)
    shutil.rmtree(runs, ignore_errors=True)
    retest = []
    for req in reqs:
        reply = a.converse(req["text"], speech_act="request") or ""
        retest.append({"verb": req["verb"], "handled": handled(a, reply), "reply": reply[:160]})
    exps = [x for r in rows for x in r["experiments"]]
    adoptions = [x for x in exps if x["adopted"]]
    adoption_records = []
    for n in a.s.nodes("Adoption"):
        at = a.s.node(n)["attrs"]
        rec = {k: at.get(k) for k in ("rule_removed", "rule_added", "cue_concept_added", "cue_route", "knob_attr",
                                      "knob_old_value", "knob_new_value", "experiment_id")}
        for rn in (at.get("rule_removed"), at.get("rule_added")):
            if rn:
                den, why = rf._rule_denylisted(a.s, rn)
                rec["machinery"] = rec.get("machinery", False) or ("machinery" in why)
        adoption_records.append(rec)
    summ = {
        "requests": len(rows), "gaps_filed": sum(r["gap_filed"] for r in rows),
        "self_promoted": rows[-1]["self_promoted"] if rows else 0,
        "experiments": len(exps), "supported": sum(1 for x in exps if x["outcome"] == "supported"),
        "adoptions": len(adoptions),
        "false_adoptions": sum(1 for x in adoptions if x["outcome"] != "supported"),
        "handled_first_pass": sum(r["handled_first"] for r in rows),
        "handled_retest": sum(x["handled"] for x in retest),
        "fixed": sum(1 for r, x in zip(rows, retest) if x["handled"] and not r["handled_first"]),
        "broken": sum(1 for r, x in zip(rows, retest) if r["handled_first"] and not x["handled"]),
        "elapsed_s": round(time.time() - t_start, 1),
        "adoption_records": adoption_records,
        "machinery_adoptions": sum(1 for x in adoption_records if x.get("machinery")),
    }
    # learning curve: experiments spent per newly-fixed verb, by quarter of the stream
    q = max(1, len(rows) // 4)
    curve = []
    for k in range(0, len(rows), q):
        blk = list(zip(rows[k:k + q], retest[k:k + q]))
        fixed = sum(1 for r, x in blk if x["handled"] and not r["handled_first"])
        ex = sum(len(r["experiments"]) for r, _ in blk)
        first_ok = sum(1 for r, _ in blk if r["experiments"] and r["experiments"][0]["outcome"] == "supported")
        tried = sum(1 for r, _ in blk if r["experiments"])
        curve.append({"block": k // q, "requests": len(blk), "fixed": fixed, "experiments": ex,
                      "experiments_per_fix": round(ex / fixed, 3) if fixed else None,
                      "first_try_supported": first_ok, "verbs_tried": tried})
    summ["curve"] = curve
    return {"arm": arm, "rows": rows, "retest": retest, "summary": summ}


def main():
    arm = sys.argv[1]
    n_req = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "all" else 10 ** 6
    tag = ("" if n_req >= 10 ** 6 else f"_n{n_req}") + (f"_{sys.argv[3]}" if len(sys.argv) > 3 else "")
    out = ROOT / f"evaluation/reports/endemic_rsi_v1_{arm}{tag}_20261010.json"
    if out.exists():
        raise SystemExit("refusing to overwrite")
    r = run(arm, n_req)
    print("SUMMARY", json.dumps(r["summary"]), flush=True)
    r["schema"] = "EndemicRSIV1"
    out.write_text(json.dumps(r, indent=1, sort_keys=True, default=str) + "\n")


if __name__ == "__main__":
    main()
