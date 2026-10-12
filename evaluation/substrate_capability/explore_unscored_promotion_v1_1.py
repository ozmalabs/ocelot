#!/usr/bin/env python3
"""Tranche 12: preregistered explore_unscored promotion gate v1.1 (clean rerun: v1 ran while seeds/experiment_conclusions.json was truncated by a disk-full event; same prereg) (one arm x
stream per process; --gate aggregates). See
docs/research/engine_substrate/SUBSTRATE_EXPLORE_UNSCORED_PROMOTION_V1_PREREG_20261009.md.
Production default boot (no variation_credit), cue_set_edit.explore_unscored
absent vs 1. Real child replays, agent-initiated retries only. An attempt
closed 'abstained' before dispatch is recorded and the agent's own retry is
followed (no human retry)."""
import hashlib, json, os, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
REP = ROOT / "evaluation/reports"
STREAMS = {"Z": ("Please {v} the notes.", "Work on the {v} notes gap.", ["sort", "tag", "trim", "dub", "snip", "sift"]),
           "O": ("Please {v} the notes.", "Work on the {v} notes gap.", ["mend", "buff", "flag", "sum", "fold", "group"])}
ARMS = {"default": {}, "explore": {"explore_unscored": 1}}
part = lambda arm, st: REP / f"explore_unscored_promotion_v1_1_{arm}_{st}_20261009.json"
GATE_OUT = REP / "explore_unscored_promotion_v1_1_gate_20261009.json"
ERR = "ERROR: no communicative response could be generated."


def run_arm(arm, stream):
    policy = ARMS[arm]; FRAME, STEER, VERBS = STREAMS[stream]
    import test_agent_authors_new_rule_migrated as T
    import substrate_rs as srs
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == "cue_set_edit":
            for k_, v_ in policy.items():
                a.s.set_attr(n, k_, v_)
    a.converse("Hello.", speech_act="greeting")
    runs = Path(tempfile.mkdtemp(prefix=f"eup11-{arm}{stream}-"))
    rows = []
    for verb in VERBS:
        rec = {"verb": verb, "attempts": []}
        floor = a.converse(FRAME.format(v=verb), speech_act="request")
        rec["gap_filed"] = "filed it as a gap" in (floor or "").lower()
        if not rec["gap_filed"]:
            rec["skip"] = floor; rows.append(rec); continue
        a.converse(STEER.format(v=verb), speech_act="request")
        prom = jd._steer_tick(a)
        if not (prom and prom[0].get("ok")):
            rec["skip"] = f"promote failed {prom}"; rows.append(rec); continue
        sc = srs.NodeID(int(prom[0]["self_concern"]))
        for k in range(4):
            jd._concern_tick(a)
            exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
                    and a.s.node(e)["attrs"].get("status") == "requested"]
            if len(exps) != 1:
                rec["attempts"].append({"k": k, "no_experiment": len(exps)})
                a.inner.run_rules()
                if a.s.node(sc)["attrs"].get("retry_requested") == 1:
                    continue
                break
            exp = exps[0]; d = next(iter(a.inner.neighbours(exp, "has_delta"))); da = a.s.node(d)["attrs"]
            t0 = time.time(); st = T._dispatch_until(a, runs / f"{verb}-{k}", exp)
            a.comprehend(); a.inner.run_rules(); rf.close_experiment_loop(a)
            at = a.s.node(exp)["attrs"]
            rec["attempts"].append({"k": k, "op": da.get("variation_op"), "route": da.get("cue_route"), "status": st,
                                    "outcome": at.get("outcome"), "regressions": at.get("regressions"),
                                    "adopted": bool(at.get("adopted")), "child_s": time.time() - t0})
            if at.get("outcome") == "supported":
                break
            if a.s.node(sc)["attrs"].get("retry_requested") != 1:
                break
        reply = a.converse(FRAME.format(v=verb), speech_act="request")
        mid = a._last_turn_inbound
        rec["final_reply"] = reply
        rec["final_handled"] = (a.s.node(mid)["attrs"].get("instruction_outcome") == "handled" and reply.strip() != ERR
                                and "gap" not in (reply or "").lower())
        rec["credits"] = {f"{x.get('op')}|{x.get('kind')}": [x.get("trials"), x.get("supports")]
                          for x in (a.s.node(n)["attrs"] for n in a.s.nodes("VariationCredit"))}
        rows.append(rec); print(json.dumps(rec, default=str)[:900], flush=True)
    real = [x for r in rows for x in r["attempts"] if "op" in x]
    summ = {"experiments": len(real),
            "handled": sum(1 for r in rows if r.get("final_handled")),
            "first_pick_cue": sum(1 for r in rows if r["attempts"] and r["attempts"][0].get("op") == "cue_set_edit"),
            "skipped": [r["verb"] for r in rows if r.get("skip")],
            "false_adoptions": sum(1 for x in real if x.get("adopted") and x.get("outcome") != "supported")
                               + sum(1 for r in rows if any(x.get("adopted") for x in r["attempts"]) and not r.get("final_handled")),
            "ops": [x.get("op") for x in real], "outcomes": [x.get("outcome") for x in real]}
    import shutil; shutil.rmtree(runs, ignore_errors=True)   # child run dirs are GBs (final_graph.json)
    return {"arm": arm, "stream": stream, "policy": policy, "rows": rows, "summary": summ}


def main():
    if "--gate" in sys.argv:
        if GATE_OUT.exists(): raise SystemExit("refusing to overwrite")
        parts = {(a_, s_): json.loads(part(a_, s_).read_text()) for a_ in ARMS for s_ in STREAMS}
        pooled = {a_: {k: sum(parts[(a_, s_)]["summary"][k] for s_ in STREAMS)
                       for k in ("experiments", "handled", "first_pick_cue", "false_adoptions")} for a_ in ARMS}
        P = {(a_, s_): parts[(a_, s_)]["summary"] for a_ in ARMS for s_ in STREAMS}
        g = {"E1_Z_explore_gt_default": P[("explore", "Z")]["handled"] > P[("default", "Z")]["handled"],
             "E2_O_explore_ge_default": P[("explore", "O")]["handled"] >= P[("default", "O")]["handled"],
             "E3_no_false_adoption_explore": all(P[("explore", s_)]["false_adoptions"] == 0 for s_ in STREAMS),
             "E4_O_bounded_extra_cost": P[("explore", "O")]["experiments"] <= P[("default", "O")]["experiments"] + 2}
        g["pass"] = all(g.values())
        per = {f"{a_}_{s_}": parts[(a_, s_)]["summary"] for a_ in ARMS for s_ in STREAMS}
        print("POOLED", json.dumps(pooled)); print("GATE", json.dumps(g))
        GATE_OUT.write_text(json.dumps({"schema": "ExploreUnscoredPromotionV1_1Gate", "pooled": pooled, "per_run": per, "gate": g,
            "prereg": "docs/research/engine_substrate/SUBSTRATE_EXPLORE_UNSCORED_PROMOTION_V1_PREREG_20261009.md"},
            indent=1, sort_keys=True, default=str) + "\n")
        return
    arm, stream = sys.argv[1], sys.argv[2]
    out = part(arm, stream)
    if out.exists(): raise SystemExit("refusing to overwrite")
    t0 = time.time()
    r = run_arm(arm, stream); print("SUMMARY", json.dumps(r["summary"]), flush=True)
    r.update({"schema": "ExploreUnscoredPromotionV1_1Part", "elapsed_s": time.time() - t0,
              "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()})
    out.write_text(json.dumps(r, indent=1, sort_keys=True, default=str) + "\n")

main()
