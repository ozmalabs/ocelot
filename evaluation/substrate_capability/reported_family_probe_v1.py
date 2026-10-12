#!/usr/bin/env python3
"""Tranche 6: do the NON-cue families produce real-judge verdicts on reported
concerns? For each reported deficiency text: file it as the agent's
SelfConcern{kind:'reported'}, promote it, let the agent's own pipeline author
an Experiment, dispatch to the real child (corrected judge), and record the
family picked, whether its builder built a variant, the verdict, adoption,
and the credit. Real-judge feasibility, n=1 per text."""
import hashlib, json, os, sys, tempfile, time
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests"), str(ROOT / "scripts")]
OUT = ROOT / "evaluation/reports/reported_family_probe_v1_20261008.json"
TEXTS = ["you reform the topic too eagerly, test whether the threshold is too low",
         "you treat every user persona the same: test a profile shape for them",
         "you trust that speaker too much, test and recalibrate reliability",
         "your reply to greetings is a hardcoded floor, test the literal"]


def run(text):
    import test_agent_authors_new_rule_migrated as T
    jd, rf = T.jd, T.rf
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    rf._ensure_seed_chain(a.s, a.inner, a.agent, ("variation_ops", "variation_credit"))
    a.converse("Hello.", speech_act="greeting"); a.converse("What do you know about the moon?", speech_act="question")
    sc = a.s.add_node("SelfConcern", {"kind": "reported", "status": "noted", "source": "explicit", "content": text})
    a.inner.add_edge_unchecked(a.agent, "has_self_concern", sc)
    p = jd.promote_self_concern(a, str(sc.value))
    rec = {"text": text, "pipeline": p.get("pipeline")}
    if p.get("pipeline") != "experiment":
        return rec
    jd._concern_tick(a)
    exps = [e for e in a.s.nodes("Experiment") if a.s.node(e)["attrs"].get("game") == "conversation"
            and a.s.node(e)["attrs"].get("status") == "requested"]
    rec["experiments"] = len(exps)
    if len(exps) != 1:
        return rec
    exp = exps[0]; d = next(iter(a.inner.neighbours(exp, "has_delta"))); da = a.s.node(d)["attrs"]
    rec["variation_op"] = da.get("variation_op")
    rec["delta_keys"] = sorted(k for k, v in da.items() if v not in (None, "", "[]", 0))
    t0 = time.time(); rec["dispatch"] = T._dispatch_until(a, Path(tempfile.mkdtemp(prefix="rfp-")), exp)
    a.comprehend(); a.inner.run_rules(); rf.close_experiment_loop(a)
    at = a.s.node(exp)["attrs"]
    rec.update({"outcome": at.get("outcome"), "adopted": bool(at.get("adopted")), "regressions": at.get("regressions"),
                "child_s": time.time() - t0, "error": at.get("error")})
    rec["credits"] = {f"{x.get('op')}|{x.get('kind')}": [x.get("trials"), x.get("supports")]
                      for x in (a.s.node(n)["attrs"] for n in a.s.nodes("VariationCredit"))}
    return rec


def main():
    if OUT.exists(): raise SystemExit("refusing to overwrite")
    rows = []
    for t in TEXTS:
        r = run(t); rows.append(r); print(json.dumps(r, default=str)[:700], flush=True)
    OUT.write_text(json.dumps({"schema": "ReportedFamilyProbeV1", "rows": rows,
        "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest()},
        indent=1, sort_keys=True, default=str) + "\n")

main()
