"""Drive THIS agent's OWN meta-cognitive machinery on the research-loop PROCESS
run this session — not a human opinion of it.

The session's autopoietic loop ran 5 iterations:
  synthesize gaps -> rank -> pick -> build-from-science -> measure -> self-correct
  -> fix-the-fixer.

Two KINDS of payoff appeared each iteration and the human asked us to keep them
distinct:
  - DOMAIN payoff  : the speech outcome (recognition vs unigram). The PROBE.
  - FIXER payoff   : a new capability that made the LOOP itself more autonomous
                     (the prioritiser, feedback/re-rank, diversification,
                     harvest-precision). These COMPOUND.

The meta_monitor watches a SINGLE process with one EFFORT and one PAYOFF over a
window, and flags `effort_without_payoff` when effort rises while payoff stays
flat. So we register TWO processes and let the SAME rule judge each:

  research_loop_domain : effort = cumulative build-work; payoff = domain outcome
                         (recognition margin over unigram, in points; negative =
                         below unigram).
  research_loop_fixer  : effort = cumulative build-work; payoff = cumulative
                         capability/autonomy gained.

Effort per iter is the human's coarse build-work units; payoff is the human's
recorded outcome. The MACHINE makes the verdict (the detect_meta_issue rule),
not us.

Run:  python scripts/assess_research_loop.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from substrate_rs import Substrate
from domains import meta_monitor as mm


# --- the session history, as effort/payoff signals -------------------------
# Per-iteration cumulative EFFORT (coarse build-work units — each iteration
# added a build) and the two PAYOFF series.
#
# DOMAIN payoff: recognition margin over unigram, in points. Stayed BELOW
# unigram all 5 iters (the human's record), so all negative; iter-4 closed some
# of the gap upstream (purity/WER improved) but recognition still under unigram.
#
# FIXER payoff: cumulative count of autonomy-capabilities the loop bootstrapped
# into itself (prioritiser -> +feedback -> +diversification -> +harvest-precision).
# iter-4 added no fixer (a domain coarsen-grain step); iter-5's first move (the
# specificity GATE) was a fix-the-OUTCOME slip = NO capability, then the
# harvest-precision fix landed = +1 real capability.

ITERS = [
    # (label, cum_effort, domain_payoff_pts, fixer_payoff_count, note)
    ("iter-1", 1.0, -8.0, 1.0, "cross-speaker clustering (capped) + ADDED gap-prioritiser (fixer)"),
    ("iter-2", 2.0, -6.0, 2.0, "feedback/re-rank ADDED (fixer); LPC built (+42% LOSO, still <unigram)"),
    ("iter-3", 3.0, -6.0, 3.0, "diversification/exhaust ADDED (fixer); chunking = honest negative"),
    ("iter-4", 4.0, -4.0, 3.0, "coarsen-grain: purity .29->.59, WER 6.6->4.2 upstream; recog STILL <unigram; NO fixer"),
    ("iter-5", 5.0, -4.0, 4.0, "fix-the-outcome GATE (wasted, +0 capability) then harvest-precision fix (54->6% promiscuity) = +1 fixer"),
]


def build():
    s = Substrate()
    mm.install_meta_issue_rule(s)
    iss_rule = mm.install_meta_issue_rule(s)["rule_index"]
    inv_rule = mm.install_investigation_rule(s)["rule_index"]

    mm.register_process(s, "research_loop_domain",
                        effort_label="cumulative build-work (iterations)",
                        payoff_label="recognition margin over unigram (pts; <0 = below)")
    mm.register_process(s, "research_loop_fixer",
                        effort_label="cumulative build-work (iterations)",
                        payoff_label="cumulative loop-autonomy capabilities gained")
    return s, iss_rule, inv_rule


def run():
    s, iss_rule, inv_rule = build()

    # The window is 5 (seed default) — exactly this session's 5 iterations, so a
    # full window lands on the final iter and the rule can judge the whole run.
    print(f"meta_monitor window = {mm._window(s)} (session ran {len(ITERS)} iters)\n")

    for label, eff, dom, fix, note in ITERS:
        mm.report(s, "research_loop_domain", eff, dom)
        mm.report(s, "research_loop_fixer", eff, fix)
        print(f"{label}: effort={eff}  domain_payoff={dom:+.1f}pt  "
              f"fixer_payoff={fix:.0f}cap")
        print(f"        {note}")

    print("\n--- firing detect_meta_issue rule (the agent's own judgement) ---")
    issues = mm.agent_check_meta(s, iss_rule)

    # Read back the full per-process state the rule computed.
    root = mm._root(s)
    report = {}
    for p in s.neighbours(root, "watches"):
        a = s.node(p)["attrs"]
        report[a["name"]] = {
            "effort_rise": a.get("effort_rise"),
            "payoff_change": a.get("payoff_change"),
            "window_full": a.get("window_full"),
            "meta_issue": a.get("meta_issue"),
            "effort_history": a.get("effort_history"),
            "payoff_history": a.get("payoff_history"),
        }

    print("\n=== MACHINERY OUTPUT (verbatim get_meta_issues) ===")
    print(json.dumps(issues, indent=2))
    print("\n=== per-process state the rule computed ===")
    print(json.dumps(report, indent=2))

    # Dials the rule judged against (from the seed) — so the verdict is legible.
    rt = s.node(root)["attrs"]
    dials = {k: rt.get(k) for k in
             ("window", "effort_min_rise", "payoff_flat_band", "payoff_improve_band")}
    print("\n=== dials (seeds/meta_monitor.json) the rule used ===")
    print(json.dumps(dials, indent=2))

    return issues, report, dials


if __name__ == "__main__":
    run()
