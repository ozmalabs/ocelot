#!/usr/bin/env python3
"""Tranche 7: knob_edit on a knob-sensitive corpus, with the agent's own
retry opted in for reported concerns (InstructionRetryPolicy.concern_kinds +=
'reported', a data edit on this probe's agent only). A shadow-read agent hears
reform-eliciting turns, a reported concern names over-eager reform, and the
agent's own pipeline authors knob experiments judged on reform marks
(control vs variant, independent boots). Records each attempt's knob, verdict,
adoption, and whether a held reply changed afterwards. n=1 feasibility."""
import hashlib, json, os, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
OUT = ROOT / "evaluation/reports/knob_retry_probe_v1_20261008.json"
TEXT = "you reform the topic too eagerly, test whether the threshold is too low"
CORPUS = [("Hello.", "greeting"), ("What do you know about the moon?", "question"),
          ("The horse raced past the barn fell.", "statement"),
          ("The committee, which had been convened after the report that the auditors, who were themselves under review, had submitted was leaked, decided that the policy should proceed.", "statement"),
          ("The old man the boats.", "statement")]


def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    import test_agent_authors_new_rule_migrated as T
    import convo_child_run as C
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    t00 = time.time()
    a = WorldAdapter(seeds=(), shadow_read=True); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit", "instruction_repair_retry"))
    for n in a.s.nodes("InstructionRetryPolicy"):
        a.s.set_attr(n, "concern_kinds", ["instruction", "reported"])
    replies_before = [a.converse(t, speech_act=sa) for t, sa in CORPUS]
    reforms_before = C._count_reform_marks(a)
    sc = a.s.add_node("SelfConcern", {"kind": "reported", "status": "noted", "source": "explicit", "content": TEXT})
    a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
    p = jd.promote_self_concern(a, str(sc.value))
    rec = {"text": TEXT, "pipeline": p.get("pipeline"), "attempts": [], "reforms_parent_before": reforms_before}
    runs = Path(tempfile.mkdtemp(prefix="krp-"))
    for k in range(4):
        jd._concern_tick(a)
        exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
                and a.s.node(e)["attrs"].get("status") == "requested"]
        if len(exps) != 1:
            rec["attempts"].append({"k": k, "no_experiment": len(exps)}); break
        exp = exps[0]; d = next(iter(a.inner.neighbours(exp, "has_delta"))); da = a.s.node(d)["attrs"]
        t0 = time.time(); st = T._dispatch_until(a, runs / str(k), exp)
        a.comprehend(); a.inner.run_rules(); rf.close_experiment_loop(a)
        at = a.s.node(exp)["attrs"]
        rec["attempts"].append({"k": k, "op": da.get("variation_op"), "knob": da.get("knob_attr"),
                                "old": da.get("knob_old_value"), "new": da.get("knob_new_value"), "status": st,
                                "control_reforms": at.get("control_reforms"), "variant_reforms": at.get("variant_reforms"),
                                "regressions": at.get("regressions"), "outcome": at.get("outcome"),
                                "adopted": bool(at.get("adopted")), "child_s": time.time() - t0})
        if at.get("outcome") == "supported":
            break
        sca = a.s.node(sc)["attrs"]
        rec["attempts"][-1]["agent_requested_retry"] = sca.get("retry_requested") == 1
        if sca.get("retry_requested") != 1:
            break
    budget = [a.s.node(n)["attrs"] for n in a.s.nodes("ApertureBudget") if a.s.node(n)["attrs"].get("register") == "conversational"]
    rec["parent_budget_after"] = {k: v for k, v in (budget[0] if budget else {}).items() if k.startswith("reform_")}
    r0 = C._count_reform_marks(a)
    replies_after = [a.converse(t, speech_act=sa) for t, sa in CORPUS]
    rec["parent_reforms_on_rehear"] = C._count_reform_marks(a) - r0
    rec["replies_changed"] = [i for i, (x, y) in enumerate(zip(replies_before, replies_after)) if x != y]
    rec["credits"] = {f"{x.get('op')}|{x.get('kind')}": [x.get("trials"), x.get("supports")]
                      for x in (a.s.node(n)["attrs"] for n in a.s.nodes("VariationCredit"))}
    rec["elapsed_s"] = time.time() - t00
    print(json.dumps(rec, default=str), flush=True)
    OUT.write_text(json.dumps({"schema": "KnobRetryProbeV1", "corpus": CORPUS, "row": rec,
        "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()},
        indent=1, sort_keys=True, default=str) + "\n")

main()
