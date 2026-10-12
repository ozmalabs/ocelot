#!/usr/bin/env python3
"""Tranche 5: real-judge self-repair panel.

For each unrouted instruction verb: the agent files an instruction gap, the
human promotes it once (NL steering), and the agent then runs up to 3
self-authored cue-set-edit experiments (real child replay, corrected judge),
re-promoted after each refutation (the human-gated retry). Records per
attempt: proposed route, verdict, adoption; at the end whether the PARENT
handles the instruction, and the VariationCredit derived from the real
verdicts. Budgeted: one fresh full-seed agent per verb.
"""
import hashlib, json, os, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")   # never teach() into the real seeds dir
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
OUT = ROOT / ("evaluation/reports/real_judge_repair_panel_v1_4_explore_20261008.json" if "--explore" in sys.argv else "evaluation/reports/real_judge_repair_panel_v1_4_conditioned_20261008.json")
EXPLORE = "--explore" in sys.argv
VERBS = ["condense", "summarise", "summarise_guarded", "condense_guarded", "tabulate", "shorten", "alphabetise", "paraphrase"]
ERR = "ERROR: no communicative response could be generated."


def srs_id(x):
    import substrate_rs as srs
    return srs.NodeID(int(x))


GUARD = {"summarise_guarded": ("summarise", "Summarise yourself."), "condense_guarded": ("condense", "Summarise yourself.")}


def run_verb(verb):
    guard_turn = None
    if verb in GUARD:
        verb, guard_turn = GUARD[verb]
    import test_agent_authors_new_rule_migrated as T
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit"))
    if EXPLORE:
        for n in a.s.nodes("VariationOp"):
            if a.s.node(n)["attrs"].get("name") == "cue_set_edit":
                a.s.set_attr(n, "explore_unscored", 1)
    rec = {"verb": verb + ("+guard" if guard_turn else ""), "attempts": []}
    a.converse("Hello.", speech_act="greeting")
    if guard_turn:   # an unflagged turn the override must not break (regression guard)
        rec["guard_before"] = a.converse(guard_turn, speech_act="request")
    floor = a.converse(f"{verb.capitalize()} the data.", speech_act="request")
    rec["gap_filed"] = "filed it as a gap" in (floor or "").lower()
    if not rec["gap_filed"]:
        rec["skip"] = f"not an unhandled instruction: {floor!r}"
        return rec
    steer = a.converse(f"Work on the {verb} data gap.", speech_act="request")
    prom = jd._steer_tick(a)
    if not (prom and prom[0].get("ok")):
        rec["skip"] = f"promote failed: {steer!r} {prom}"
        return rec
    sc = str(prom[0]["self_concern"])
    runs = Path(tempfile.mkdtemp(prefix=f"rj-{verb}-"))
    for k in range(4):
        jd._concern_tick(a)
        exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
                and a.s.node(e)["attrs"].get("status") == "requested"]
        if len(exps) != 1:
            rec["attempts"].append({"k": k, "no_experiment": len(exps)}); break
        exp = exps[0]
        d = next(iter(a.inner.neighbours(exp, "has_delta")))
        da = a.s.node(d)["attrs"]
        t0 = time.time()
        st = T._dispatch_until(a, runs / str(k), exp)
        a.comprehend(); a.inner.run_rules()
        at = a.s.node(exp)["attrs"]
        rf.close_experiment_loop(a)
        rec["attempts"].append({"k": k, "op": da.get("variation_op"), "route": da.get("cue_route"),
                                "status": st, "outcome": at.get("outcome"),
                                "adopted": bool(a.s.node(exp)["attrs"].get("adopted")), "child_s": time.time() - t0})
        if at.get("outcome") == "supported":
            break
        # NO human retry: the agent's own irr_request_retry rule decides; the
        # daemon hook (inside _concern_tick at the top of the next attempt)
        # executes it. Record what the graph decided.
        sca = a.s.node(srs_id(sc))["attrs"]
        rec["attempts"][-1]["agent_requested_retry"] = sca.get("retry_requested") == 1
        rec["attempts"][-1]["retry_count"] = sca.get("retry_count")
        if sca.get("retry_requested") != 1:
            break
    if guard_turn:
        rec["guard_after"] = a.converse(guard_turn, speech_act="request")
    reply = a.converse(f"{verb.capitalize()} the data.", speech_act="request")
    mid = a._last_turn_inbound
    rec["final_reply"] = reply
    rec["final_handled"] = (a.s.node(mid)["attrs"].get("instruction_outcome") == "handled" and reply.strip() != ERR
                            and "gap" not in (reply or "").lower())
    if guard_turn:
        rec["guard_preserved"] = rec.get("guard_after") == rec.get("guard_before")
    rec["credits"] = {f"{x.get('op')}|{x.get('kind')}": [x.get("trials"), x.get("supports")]
                      for x in (a.s.node(n)["attrs"] for n in a.s.nodes("VariationCredit"))}
    return rec


def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    t0 = time.time(); rows = []
    for v in VERBS:
        r = run_verb(v); rows.append(r)
        print(json.dumps({k: r.get(k) for k in ("verb", "gap_filed", "skip", "attempts", "final_handled", "credits")}, default=str)[:900], flush=True)
    tested = [r for r in rows if r.get("gap_filed") and not r.get("skip")]
    summ = {"verbs": len(VERBS), "gap_filed": sum(bool(r.get("gap_filed")) for r in rows), "tested": len(tested),
            "repaired": sum(bool(r.get("final_handled")) for r in tested),
            "first_attempt_supported": sum(1 for r in tested if r["attempts"] and r["attempts"][0].get("outcome") == "supported"),
            "refuted_attempts": sum(1 for r in tested for x in r["attempts"] if x.get("outcome") == "refuted"),
            "guards_preserved": sum(1 for r in tested if r.get("guard_preserved")),
            "guarded_cases": sum(1 for r in tested if "guard_preserved" in r),
            "false_adoptions": sum(1 for r in tested for x in r["attempts"] if x.get("adopted") and x.get("outcome") != "supported")
                               + sum(1 for r in tested if any(x.get("adopted") for x in r["attempts"]) and not r.get("final_handled")),
            "elapsed_s": time.time() - t0}
    rep = {"schema": "RealJudgeRepairPanelV1_4", "summary": summ, "rows": rows,
           "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps(summ, indent=1))

main()
