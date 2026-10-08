#!/usr/bin/env python3
"""Tranche 2 gate 2: real-judge feasibility for outcome-credited variation.

Replaces the authored world of the v1 adoption gate with the production
experiment path for ONE concern kind. A full-corpus agent records two real
conversation turns; a human flag files a reply_fix SelfConcern; Experiments
for two candidate families are dispatched to the REAL child process
(scripts/convo_child_run.py, paired-control replay) and judged by the
composer's judge shape over the child's own result. variation_credit is
loaded, so the graph rules credit each REAL verdict.

Candidates (both are reply_ablation-family deltas the composer can author):
  fix    -- remove_rules=[reply_self_identity]  (the flagged reply's rule)
  break  -- remove_rules=[reply_to_adjacency_pair]  (breaks the unflagged turn)
Reports: real child outcomes, the credits derived from them, whether the
pick for a fresh same-kind concern reflects them, and wall time per trial.
This is a feasibility capture (n=1 per candidate), not a gate measurement.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "tests")]
OUT = ROOT / "evaluation/reports/variation_credit_real_judge_feasibility_v1_20261007.json"


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    import test_convo_experiment_migrated as T
    from domains.experiment_dispatch import mint_experiment
    from domains import reflective_faculty as rf
    from substrate.world_adapter import WorldAdapter  # noqa: F401
    t0 = time.time()
    agent = T.agent.__wrapped__() if hasattr(T.agent, "__wrapped__") else None
    if agent is None:
        from substrate.boot_all import load_all_seeds
        agent = WorldAdapter(seeds=())
        load_all_seeds(agent)
    boot_s = time.time() - t0
    rf._ensure_seed_chain(agent.s, agent.inner, agent.agent, ("variation_ops", "variation_credit"))
    turn = T._have_two_turns(agent)
    concern = T._flag(agent, turn)
    key = f"promoted_self_concern_{concern}"
    agent.s.add_node("StandingConcern", {"name": key, "kind": "reply_fix"})
    agent.inner.add_rule(T._probe_judge_rule("credit_probe"))
    pick_before = rf._pick_variation_op(agent, ["test", "replay", "send", "judge", "adopt"], "fresh_reply_fix")
    trials = []
    runs = Path(tempfile.mkdtemp(prefix="vc-real-"))
    for label, op, rm in (("fix", "reply_ablation", ["reply_self_identity"]),
                          ("break", "structural_edit", ["reply_to_adjacency_pair"])):
        exp = mint_experiment(agent, f"{label} candidate", "conversation", remove_rules=rm)
        delta = next(iter(agent.inner.neighbours(exp, "has_delta")))
        agent.s.set_attr(delta, "variation_op", op)
        agent.s.set_attr(delta, "concern_key", key)
        ts = time.time()
        status = T._dispatch_until(agent, runs, exp)
        agent.comprehend()
        agent.inner.run_rules()
        ea, da = agent.s.node(exp)["attrs"], agent.s.node(delta)["attrs"]
        run = next((r for r in agent.inner.neighbours(exp, "produced") if agent.s.has_node(r)), None)
        ra = agent.s.node(run)["attrs"] if run is not None else {}
        trials.append({"label": label, "op": op, "remove_rules": rm, "status": status, "outcome": ea.get("outcome"),
                       "score": ra.get("score"), "regressions": ea.get("regressions"), "credited": da.get("credited"),
                       "judged_outcome": da.get("judged_outcome"), "seconds": time.time() - ts})
        print(trials[-1], flush=True)
    credits = {f"{a.get('op')}|{a.get('kind')}": [a.get("trials"), a.get("supports")]
               for a in (agent.s.node(n)["attrs"] for n in agent.s.nodes("VariationCredit"))}
    agent.s.add_node("StandingConcern", {"name": "fresh_reply_fix_2", "kind": "reply_fix"})
    pick_after = rf._pick_variation_op(agent, ["test", "replay", "send", "judge", "adopt", "structure"], "fresh_reply_fix_2")
    rep = {"schema": "VariationCreditRealJudgeFeasibilityV1", "boot_seconds": boot_s,
           "native_sha256": hashlib.sha256((ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so").read_bytes()).hexdigest(),
           "trials": trials, "credits": credits, "pick_before": pick_before, "pick_after": pick_after,
           "checks": {"both_dispatched_done": all(t["status"] == "done" for t in trials),
                      "real_verdicts_credited": all(t["credited"] == 1 for t in trials),
                      "fix_supported": trials[0]["outcome"] == "supported",
                      "break_refuted": trials[1]["outcome"] == "refuted"}}
    OUT.write_text(json.dumps(rep, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({k: rep[k] for k in ("credits", "pick_before", "pick_after", "checks")}, indent=1))


if __name__ == "__main__":
    main()
