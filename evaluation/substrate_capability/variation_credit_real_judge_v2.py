#!/usr/bin/env python3
"""Tranche 9: preregistered real-verdict variation-credit gate v2 (one arm x
stream per process; --gate aggregates). See
docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V2_PREREG_20261008.md.
One agent per arm processes a stream of instruction gaps with a misordered
prior (reply_ablation.priority=8 < cue_set_edit 10); OFF = use_credit 0,
ON = use_credit 1. Real child replays, agent-initiated retries only."""
import hashlib, json, os, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
REP = ROOT / "evaluation/reports"
STREAMS = {"S1": ("data", ["condense", "tabulate", "shorten", "alphabetise", "paraphrase", "abridge"]),
           "S2": ("list", ["itemise", "transpose", "collate", "annotate", "reorder", "condense"])}
ARMS = {"A": {"use_credit": 0}, "B": {"use_credit": 1},
        "C": {"use_credit": 1, "credit_internal_exempt": 1, "exclude_inconclusive": 1}}
part = lambda arm, st: REP / f"variation_credit_real_judge_v2_{arm}_{st}_20261008.json"
GATE_OUT = REP / "variation_credit_real_judge_v2_gate_20261008.json"
ERR = "ERROR: no communicative response could be generated."


def run_arm(arm, stream):
    policy = ARMS[arm]; obj, VERBS = STREAMS[stream]
    import test_agent_authors_new_rule_migrated as T
    import substrate_rs as srs
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit", "instruction_repair_retry"))
    for n in a.s.nodes("VariationOp"):
        if a.s.node(n)["attrs"].get("name") == "reply_ablation":
            a.s.set_attr(n, "priority", 8)
    for n in a.s.nodes("VariationPolicy"):
        a.s.set_attr(n, "exclude_refuted", 1)
        for k_, v_ in policy.items():
            a.s.set_attr(n, k_, v_)
    a.converse("Hello.", speech_act="greeting")
    runs = Path(tempfile.mkdtemp(prefix=f"vcrj2-{arm}{stream}-"))
    rows = []
    for verb in VERBS:
        rec = {"verb": verb, "attempts": []}
        floor = a.converse(f"{verb.capitalize()} the {obj}.", speech_act="request")
        rec["gap_filed"] = "filed it as a gap" in (floor or "").lower()
        if not rec["gap_filed"]:
            rec["skip"] = floor; rows.append(rec); continue
        a.converse(f"Work on the {verb} {obj} gap.", speech_act="request")
        prom = jd._steer_tick(a)
        if not (prom and prom[0].get("ok")):
            rec["skip"] = f"promote failed {prom}"; rows.append(rec); continue
        sc = srs.NodeID(int(prom[0]["self_concern"]))
        for k in range(4):
            jd._concern_tick(a)
            exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
                    and a.s.node(e)["attrs"].get("status") == "requested"]
            if len(exps) != 1:
                rec["attempts"].append({"k": k, "no_experiment": len(exps)}); break
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
        reply = a.converse(f"{verb.capitalize()} the {obj}.", speech_act="request")
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
            "false_adoptions": sum(1 for x in real if x.get("adopted") and x.get("outcome") != "supported")
                               + sum(1 for r in rows if any(x.get("adopted") for x in r["attempts"]) and not r.get("final_handled")),
            "ops": [x.get("op") for x in real], "outcomes": [x.get("outcome") for x in real]}
    return {"arm": arm, "stream": stream, "policy": policy, "rows": rows, "summary": summ}


def main():
    if "--gate" in sys.argv:
        if GATE_OUT.exists(): raise SystemExit("refusing to overwrite")
        parts = {(a_, s_): json.loads(part(a_, s_).read_text()) for a_ in ARMS for s_ in STREAMS}
        pooled = {a_: {k: sum(parts[(a_, s_)]["summary"][k] for s_ in STREAMS)
                       for k in ("experiments", "handled", "first_pick_cue", "false_adoptions")} for a_ in ARMS}
        A, B, C = pooled["A"], pooled["B"], pooled["C"]
        g = {"G1_replication_B_gt_A_handled": B["handled"] > A["handled"],
             "G2_C_handled_ge_B": C["handled"] >= B["handled"],
             "G3_C_experiments_le_B": C["experiments"] <= B["experiments"],
             "G4_no_false_adoptions_B_C": B["false_adoptions"] == 0 and C["false_adoptions"] == 0}
        g["pass"] = all(g.values())
        per = {f"{a_}_{s_}": parts[(a_, s_)]["summary"] for a_ in ARMS for s_ in STREAMS}
        print("POOLED", json.dumps(pooled)); print("GATE", json.dumps(g))
        GATE_OUT.write_text(json.dumps({"schema": "VariationCreditRealJudgeV2Gate", "pooled": pooled, "per_run": per, "gate": g,
            "prereg": "docs/research/engine_substrate/SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V2_PREREG_20261008.md"},
            indent=1, sort_keys=True, default=str) + "\n")
        return
    arm, stream = sys.argv[1], sys.argv[2]
    out = part(arm, stream)
    if out.exists(): raise SystemExit("refusing to overwrite")
    t0 = time.time()
    r = run_arm(arm, stream); print("SUMMARY", json.dumps(r["summary"]), flush=True)
    r.update({"schema": "VariationCreditRealJudgeV2Part", "elapsed_s": time.time() - t0,
              "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()})
    out.write_text(json.dumps(r, indent=1, sort_keys=True, default=str) + "\n")

main()
