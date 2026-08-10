"""Drive the PROCESS-LEVEL meta-assessor on THIS session's research loop and show
it catches the inefficiencies the OLD single-process meta_monitor missed — live,
side by side, then prove GENERALITY on two synthetic control loops.

The new assessor (domains/process_meta_assessor.py) is graph-resident: a
ResearchLoopRoot + a chain of Iteration nodes, judged by four general Rules
(DOMAIN_SPINNING / FIXER_PROGRESS / BELOW_FRONTIER / FIX_THE_OUTCOME). The OLD
meta_monitor (domains/meta_monitor.py) is the single-process spinning detector.

Run:  python scripts/process_meta_assessor_demo.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from substrate_rs import Substrate
from domains import meta_monitor as mm
from domains import process_meta_assessor as pma


# --- THIS session's research loop, as the loop graph ------------------------
# Per the task brief (machine-verified, commit e45bee08):
#   effort        1..5 (one per iteration)
#   probe_payoff  -8, -6, -6, -4, -4   (recognition margin over unigram, pts;
#                                        BELOW unigram throughout -> never crossed 0)
#   fixer_payoff  1, 2, 3, 3, 4        (cumulative loop-autonomy capabilities)
#   frontier      perception/units (rank 1) while iter-3..5 PICKED recognition (rank 5)
#   iter-5        the first move was a fix-the-OUTCOME gate (+0 fixer, didn't move source)
#
# pick_rank uses the seed's pipeline_levels ordering (perception=1 ... recognition=5).
#
# iter-5 in the brief is TWO moves: the loop's FIRST move that iteration was a
# fix-the-OUTCOME specificity GATE (+0 capability, and it did NOT move its source —
# it papered over a symptom), and only THEN the real harvest-precision fix landed
# (+1 capability). We model them as the two steps they were: iter-5-gate (the
# detour) and iter-5 (the real fix). This is faithful to the recorded fixer series
# 1,2,3,3,4 with the gate's +0 made explicit.
#
# moved_source: 1 everywhere EXCEPT iter-5-gate. The discriminating contrast is
# iter-4 vs iter-5-gate: iter-4 also added +0 fixer, but it DID move its source
# (purity .29->.59, WER 6.6->4.2 upstream), so FIX_THE_OUTCOME must NOT fire on
# iter-4. +0 fixer alone is not the issue; +0 fixer AND no source movement is. That
# is the general predicate, and it discriminates the two +0-fixer iterations.
SESSION = [
    # (label, effort, probe, fixer, pick_level, pick_rank, moved_source)
    ("iter-1", 1.0, -8.0, 1.0, "perception_units", 1.0, 1),
    ("iter-2", 2.0, -6.0, 2.0, "feature_extraction", 4.0, 1),
    ("iter-3", 3.0, -6.0, 3.0, "recognition", 5.0, 1),
    ("iter-4", 4.0, -4.0, 3.0, "recognition", 5.0, 1),
    ("iter-5-gate", 4.5, -4.0, 3.0, "recognition", 5.0, 0),
    ("iter-5", 5.0, -4.0, 4.0, "recognition", 5.0, 1),
]
FRONTIER_LEVEL, FRONTIER_RANK = "perception_units", 1.0


# The 5 iterations as the OLD detector saw them — one process, one payoff = the
# recognition PROBE (the brief's exact series). The gate is an intra-iteration
# detail the single-process detector has no grain for; it sees 5 iterations.
OLD_VIEW = [
    ("iter-1", 1.0, -8.0),
    ("iter-2", 2.0, -6.0),
    ("iter-3", 3.0, -6.0),
    ("iter-4", 4.0, -4.0),
    ("iter-5", 5.0, -4.0),
]


def run_old_meta_monitor():
    """The OLD detector on the same loop: one process, effort vs the PROBE payoff."""
    s = Substrate()
    iss = mm.install_meta_issue_rule(s)["rule_index"]
    mm.register_process(s, "research_loop",
                        effort_label="iterations",
                        payoff_label="recognition margin over unigram (pts)")
    for label, eff, probe in OLD_VIEW:
        mm.report(s, "research_loop", eff, probe)
    issues = mm.agent_check_meta(s, iss)
    root = mm._root(s)
    p = next(iter(s.neighbours(root, "watches")))
    a = s.node(p)["attrs"]
    return issues, {"effort_rise": a.get("effort_rise"),
                    "payoff_change": a.get("payoff_change"),
                    "window_full": a.get("window_full"),
                    "meta_issue": a.get("meta_issue"),
                    "effort_min_rise_dial": s.node(root)["attrs"].get("effort_min_rise")}


def build_loop(iters, frontier_level, frontier_rank):
    s = Substrate()
    rules = pma.install_all_rules(s)
    pma.set_frontier(s, frontier_level, frontier_rank)
    for label, eff, probe, fix, lvl, rank, moved in iters:
        pma.record_iteration(s, label, eff, probe, fix,
                             pick_level=lvl, pick_rank=rank, moved_source=moved)
    return s, rules


def main():
    print("=" * 72)
    print("1. THIS SESSION'S LOOP — new assessor vs OLD meta_monitor (side by side)")
    print("=" * 72)

    old_issues, old_state = run_old_meta_monitor()
    print("\n--- OLD meta_monitor (single process, probe as the one payoff) ---")
    print("get_meta_issues():", json.dumps(old_issues))
    print("internal state    :", json.dumps(old_state))
    print("  -> MISSED it: effort_rise=%s << dial effort_min_rise=%s, so the"
          % (old_state["effort_rise"], old_state["effort_min_rise_dial"]))
    print("     spinning test never armed; and a single payoff channel cannot")
    print("     separate the failing probe from the compounding fixer.")

    s, rules = build_loop(SESSION, FRONTIER_LEVEL, FRONTIER_RANK)
    report = pma.agent_assess(s, rules)
    print("\n--- NEW process_meta_assessor (graph-resident, 4 general rules) ---")
    print(json.dumps(report, indent=2))

    ok = True
    print("\n--- acceptance checks (live) ---")
    a = report["loop_issue"] == "domain_spinning"
    print(f"  (a) DOMAIN_SPINNING flagged (probe never crossed target): {a}"
          "  [OLD missed this]")
    ok &= a
    bf = set(report["flagged_iterations"]["below_frontier"])
    b = {"iter-3", "iter-4"}.issubset(bf) and "iter-1" not in bf
    print(f"  (b) BELOW_FRONTIER at iter-3 & iter-4 (recognition picked while")
    print(f"      perception was frontier), NOT iter-1: {b}  (flagged={sorted(bf)})")
    ok &= b
    fo = set(report["flagged_iterations"]["fix_the_outcome"])
    c = fo == {"iter-5-gate"}
    print(f"  (c) FIX_THE_OUTCOME == {{iter-5-gate}} only — the +0-fixer gate that")
    print(f"      did NOT move its source (iter-4 also +0 fixer but MOVED its")
    print(f"      source, so must NOT fire): {c}  (flagged={sorted(fo)})")
    ok &= c
    fp = report["fixer_progressing"] == 1
    print(f"  (+) FIXER_PROGRESS recorded (fixer rose 1->4): {fp}  "
          "[so probe-spin is NOT masked by, nor masks, fixer progress]")
    ok &= fp

    print("\n" + "=" * 72)
    print("2. GENERALITY — same rules, ZERO session constants, on synthetic controls")
    print("=" * 72)

    # CONTROL A: an EFFICIENT loop. probe RISES and CROSSES the target, every
    # iteration picks AT the frontier, every iteration adds fixer. Nothing to flag.
    eff_loop = [
        ("e1", 1.0, -2.0, 1.0, "perception_units", 1.0, 1),
        ("e2", 2.0,  0.5, 2.0, "perception_units", 1.0, 1),
        ("e3", 3.0,  2.0, 3.0, "perception_units", 1.0, 1),
        ("e4", 4.0,  4.0, 4.0, "perception_units", 1.0, 1),
        ("e5", 5.0,  6.0, 5.0, "perception_units", 1.0, 1),
    ]
    s2, r2 = build_loop(eff_loop, "perception_units", 1.0)
    rep2 = pma.agent_assess(s2, r2)
    clean = (rep2["loop_issue"] == "none"
             and not rep2["flagged_iterations"]["below_frontier"]
             and not rep2["flagged_iterations"]["fix_the_outcome"])
    print("\n--- CONTROL A: efficient loop (probe->target, picks at frontier, +fixer) ---")
    print(json.dumps(rep2["flagged_iterations"], indent=2),
          "loop_issue=", rep2["loop_issue"], "fixer_progressing=",
          rep2["fixer_progressing"])
    print(f"  flags NOTHING: {clean}")
    ok &= clean

    # CONTROL B: an ALL-SPINNING loop. effort rises, probe stays below target the
    # whole way, NO fixer ever added. domain_spinning must fire; fixer NOT progressing.
    spin_loop = [
        ("s1", 1.0, -5.0, 0.0, "perception_units", 1.0, 1),
        ("s2", 2.0, -5.0, 0.0, "perception_units", 1.0, 1),
        ("s3", 3.0, -5.0, 0.0, "perception_units", 1.0, 1),
        ("s4", 4.0, -5.0, 0.0, "perception_units", 1.0, 1),
        ("s5", 5.0, -5.0, 0.0, "perception_units", 1.0, 1),
    ]
    s3, r3 = build_loop(spin_loop, "perception_units", 1.0)
    rep3 = pma.agent_assess(s3, r3)
    spins = (rep3["loop_issue"] == "domain_spinning"
             and rep3["fixer_progressing"] == 0)
    print("\n--- CONTROL B: all-spinning loop (effort up, probe flat-below, no fixer) ---")
    print("  loop_issue=", rep3["loop_issue"], "fixer_progressing=",
          rep3["fixer_progressing"])
    print(f"  flags domain_spinning + fixer NOT progressing: {spins}")
    ok &= spins

    print("\n" + "=" * 72)
    print("ALL ACCEPTANCE CHECKS PASSED" if ok else "SOME CHECKS FAILED")
    print("=" * 72)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
