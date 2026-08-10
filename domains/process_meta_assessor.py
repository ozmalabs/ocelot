"""process_meta_assessor — a PROCESS-LEVEL meta-assessor the agent composes
graph-resident, the next fixer it identified when it assessed its own research
loop.

WHY (machine-verified, commit e45bee08). domains/meta_monitor.py is a SINGLE-
process spinning detector: one EFFORT signal and one PAYOFF signal over a window,
flagging `effort_without_payoff` when effort rises while payoff stays flat. Fed
this session's 5-iteration research loop it returned `get_meta_issues() == []` for
the WRONG reasons:
  (1) effort_rise = 4 (iter 1..5) << effort_min_rise = 20 (the dial is scaled for
      "322 features minted", not "5 iterations"), so the spinning test never armed;
  (2) it CONFLATED the recognition PROBE with PAYOFF: it scored the loop as
      "improving" because a WER-margin moved (-8 -> -4) while the recognition probe
      stayed BELOW unigram the whole run — the loop never actually recognised, but
      a different number moving made the single payoff channel look healthy.

The agent's own three-part fix, the thing THIS module builds:
  • ITERATION GRAIN — the unit of the research loop is an iteration, not "322
    feature-mints"; the window is iterations.
  • TWO PAYOFF CHANNELS — a PROBE channel (the speech outcome: recognition vs
    unigram) and a FIXER channel (a new capability that made the LOOP more
    autonomous). These are different things; conflating them is bug (2). The probe
    can stay flat while fixers compound — that is real progress, not spinning.
  • FRONTIER-AWARENESS — an iteration that picks a level DOWNSTREAM of the current
    frontier is spending effort below where the bottleneck is (the loop kept
    picking recognition-level fixes while perception/units was the frontier).

THE ASSESSOR (graph-resident; the recognition_graph / order_n_postulates pattern).
A research loop is GRAPH STATE: a ResearchLoopRoot carrying the dials (target,
frontier level) and a chain of Iteration nodes (one per iteration) linked
`follows`, each carrying effort, probe_payoff, fixer_payoff, pick_level/pick_rank.
The root links to its first + last iteration so the window-aggregate Rules can read
both endpoints. The four judgements are general graph Rules — composed Term-trees,
native eval, ZERO session-specific constants (no `if iter == 5`):

  DOMAIN_SPINNING  (window-level, on the root)
      effort rose across the window AND the probe channel stayed BELOW its target
      across the whole window  ->  effort_without_payoff ON THE PROBE CHANNEL.
      This is the conflation fix: judged on the probe alone, never the fixer. Old
      meta_monitor MISSED this (scored "improving").

  FIXER_PROGRESS   (window-level, on the root)
      fixer channel rose across the window  ->  flag NOTHING (the loop is
      compounding real capability; that IS the payoff). A separate channel so
      fixer progress can NEVER mask probe spinning and probe spinning can NEVER
      hide fixer progress.

  BELOW_FRONTIER   (per-iteration)
      an iteration whose pick_rank is DOWNSTREAM of the root's frontier_rank
      (pick_rank > frontier_rank — larger rank = further downstream)  ->  flag
      below-frontier effort. General over the rank ordering, no per-iter constant.

  FIX_THE_OUTCOME  (per-iteration)
      an iteration that added +0 fixer_payoff (no capability) AND whose change did
      NOT move its source (moved_source == 0)  ->  flag the outcome-detour: effort
      spent papering over a symptom rather than fixing the cause.

The DECISIONS live in the Terms; the Python here is the loop-graph I/O adapter
(record an iteration, wire the chain, read back flags) — mechanical translation,
no conditionals over graph state driving behaviour, per the architecture rule.

HONEST about what is live vs stubbed (see docs/process_meta_assessor.md):
  • effort / probe_payoff / fixer_payoff / pick_rank / frontier_rank are signals
    the WORLD ADAPTER reports — for the session-history demo they are the recorded
    numbers; in a live loop they come from perception_self_assessment (probe +
    frontier) and the loop's own capability count (fixer). The RULES are general
    regardless of where the numbers come from.
  • FIX_THE_OUTCOME's "did not move the source" reads a `moved_source` flag on the
    iteration. Wiring it automatically needs the measurement-feedback edges
    (domains/measurement_feedback.py) that say which source a change targeted and
    whether that source moved; until those are wired the adapter sets the flag from
    the recorded outcome. The RULE is live; the automatic source-movement signal is
    the stub.

See [[ozma_meta_monitor]] / [[ozma_self_measurement_compresses_research]] /
[[ozma_meta_abilities_are_leverage]] / [[ozma_concepts_in_gamma]] /
[[ozma_entity_not_program]].
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate_rs import (Attr, Lit, Var, Gt, Gte, Lt, Lte, Eq, And, Or, Not,
                          IfThenElse)

_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "process_meta_assessor.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def _native(substrate):
    return substrate._inner if hasattr(substrate, "_inner") else substrate


# --------------------------------------------------------------------------
# the loop graph (world-adapter I/O — mechanical, no decisions)
# --------------------------------------------------------------------------

def _root(substrate):
    for n in substrate.nodes("ResearchLoopRoot"):
        return n
    # Dials (probe target, frontier rank, the spinning bands) are SEEDED data on
    # the root, never Python constants.
    return substrate.add_node("ResearchLoopRoot",
                              {"origin": "process_meta_assessor",
                               **_load_seed().get("research_loop_root", {})})


def _ensure_productions(substrate):
    for prod in (
        {"src": {"type": "ResearchLoopRoot", "var": "a"}, "edge_type": "first_iter",
         "tgt": {"type": "Iteration", "var": "b"}},
        {"src": {"type": "ResearchLoopRoot", "var": "a"}, "edge_type": "last_iter",
         "tgt": {"type": "Iteration", "var": "b"}},
        {"src": {"type": "ResearchLoopRoot", "var": "a"}, "edge_type": "has_iter",
         "tgt": {"type": "Iteration", "var": "b"}},
        {"src": {"type": "Iteration", "var": "a"}, "edge_type": "follows",
         "tgt": {"type": "Iteration", "var": "b"}},
    ):
        try:
            substrate.add_production({**prod,
                                      "provenance": "process_meta_assessor"})
        except Exception:
            pass


def set_frontier(substrate, frontier_level: str, frontier_rank: float) -> None:
    """Set the loop's CURRENT frontier — the level where the real bottleneck is —
    as graph data on the root. `frontier_rank` is the position in the pipeline's
    upstream->downstream ordering (smaller = more upstream). BELOW_FRONTIER fires on
    iterations whose pick_rank is strictly greater (further downstream). In a live
    loop this comes from perception_self_assessment's frontier flag; here the
    adapter sets it. Mechanical."""
    root = _root(substrate)
    substrate.set_attr(root, "frontier_level", str(frontier_level))
    substrate.set_attr(root, "frontier_rank", float(frontier_rank))


def record_iteration(substrate, label: str, effort: float,
                     probe_payoff: float, fixer_payoff: float,
                     pick_level: str = "", pick_rank: float = 0.0,
                     moved_source: int = 1) -> "object":
    """Append one iteration of the research loop to the loop graph: an Iteration
    node carrying the iteration's signals, linked `follows` to the previous one and
    `has_iter` from the root, with the root's first_iter / last_iter endpoints
    maintained so the window-aggregate Rules can read both ends.

    Signals (reported by the world adapter — see module docstring for live vs stub):
      effort        cumulative build-work at this iteration.
      probe_payoff  the SPEECH outcome (e.g. recognition margin over unigram, pts).
      fixer_payoff  cumulative loop-autonomy capabilities gained.
      pick_level    name of the pipeline level this iteration's fix targeted.
      pick_rank     that level's upstream->downstream rank (for BELOW_FRONTIER).
      moved_source  1 if this iteration's change moved the source it targeted, 0 if
                    it papered over a symptom (for FIX_THE_OUTCOME).
    Returns the Iteration node. Mechanical — no decisions."""
    _ensure_productions(substrate)
    root = _root(substrate)
    prev = None
    for n in substrate.neighbours(root, "last_iter"):
        prev = n
        break
    it = substrate.add_node("Iteration", {
        "origin": "process_meta_assessor",
        "label": str(label),
        "effort": float(effort),
        "probe_payoff": float(probe_payoff),
        "fixer_payoff": float(fixer_payoff),
        "pick_level": str(pick_level),
        "pick_rank": float(pick_rank),
        "moved_source": int(moved_source),
        "below_frontier": 0,
        "fix_the_outcome": 0,
        "iter_eval_pending": 1,
    })
    try:
        substrate.add_edge(root, "has_iter", it)
    except Exception:
        pass
    if prev is None:
        try:
            substrate.add_edge(root, "first_iter", it)
        except Exception:
            pass
    else:
        # fixer DELTA across this single step (mechanical; the Rule reads it).
        prev_fix = float(substrate.node(prev)["attrs"].get("fixer_payoff", 0.0))
        substrate.set_attr(it, "fixer_delta", float(fixer_payoff) - prev_fix)
        try:
            substrate.add_edge(it, "follows", prev)
        except Exception:
            pass
        # move last_iter pointer: drop the old, add the new.
        try:
            substrate.remove_edge(root, "last_iter", prev)
        except Exception:
            pass
    try:
        substrate.add_edge(root, "last_iter", it)
    except Exception:
        pass
    # iter-1 has no predecessor, so its fixer_delta is its own value above zero.
    if prev is None:
        substrate.set_attr(it, "fixer_delta", float(fixer_payoff))
    substrate.set_attr(root, "loop_eval_pending", 1)
    return it


# --------------------------------------------------------------------------
# AUTO-WIRED FEEDS — the live loop state, read off the agent's own graph, so the
# assessor WATCHES the real loop instead of hand-set numbers (Step 1 of the brief).
# Each of these is a mechanical world<->graph read: it pulls a number the loop's own
# components already computed (perception_self_assessment / gap_prioritiser /
# measurement_feedback) and hands it to record_iteration. No decision here.
# --------------------------------------------------------------------------

def frontier_rank_from_perception(substrate, default_rank: float = 999.0) -> tuple:
    """frontier_rank <- perception_self_assessment's LIVE frontier flag.

    MIGRATED (architecture rule, [[ozma_concepts_in_gamma]]): the flag->rank DECISION
    is no longer the `if flag == 'perception'` Python conditional that used to live
    here — it is now a graph Rule (perception_self_assessment.set_frontier_rank_from_flag)
    that reads the PerceptionSelfRoot's own `frontier` flag and both rank dials and
    writes `frontier_rank` natively (IfThenElse / Eq / Attr). This function is now a
    mechanical world<->graph READ-BACK: it installs + fires that Rule (re-arming its
    pending flag), then reads the rank the Rule wrote off the root. No decision here.
    Returns (frontier_level, frontier_rank). When perception_self_assessment is not
    present at all, falls back to the unknown default."""
    try:
        from domains import perception_self_assessment as psa
    except Exception:
        return ("none", default_rank)
    roots = list(substrate.nodes("PerceptionSelfRoot"))
    if not roots:
        return ("none", default_rank)
    root = roots[0]
    info = psa.install_frontier_rank_rule(substrate)
    substrate.set_attr(root, "frontier_rank_pending", 1)
    rank = psa.agent_set_frontier_rank(substrate, info["rule_index"])
    flag = psa.get_frontier(substrate)
    level = "perception_units" if flag == "perception" else "none"
    return (level, float(rank))


def pick_rank_from_axis(capability_keys) -> tuple:
    """pick_rank <- the picked gap's pipeline LEVEL. Reuses the ranker's OWN
    capability->level map (gap_prioritiser.axis_pipeline_level), so the assessor's
    notion of 'where the pick sits' is exactly the ranker's. Returns
    (pick_level, pick_rank). Mechanical."""
    try:
        from domains.gap_prioritiser import axis_pipeline_level
    except Exception:
        return ("recognition", 5.0)
    return axis_pipeline_level(capability_keys)


def moved_source_from_feedback(substrate, attempted_key: str) -> int:
    """moved_source <- measurement_feedback. Reads the latest MeasurementOutcome the
    iteration's build recorded for `attempted_key`: 1 if it beat its baseline (the
    source metric it targeted moved), 0 if not. Mechanical read of the empirical
    record the probe already wrote — no decision."""
    latest = None
    latest_id = -1
    for n in substrate.nodes("MeasurementOutcome"):
        a = substrate.node(n)["attrs"]
        if str(a.get("attempted_key", "")).lower() != attempted_key.lower():
            continue
        # node ids are monotonic; take the most recent record for this key
        nid = n if isinstance(n, int) else latest_id + 1
        if nid >= latest_id:
            latest_id, latest = nid, a
    if latest is None:
        return 1   # no measurement recorded -> assume the build moved its source
    return 1 if latest.get("beats_baseline") else 0


def record_iteration_auto(substrate, label: str, effort: float,
                          probe_payoff: float, fixer_payoff: float,
                          pick_capability_keys, attempted_key: str = "") -> "object":
    """Record one iteration with the assessor's feeds AUTO-WIRED from the live loop:
      frontier on the root  <- perception_self_assessment flag (set here too),
      pick_rank             <- gap_prioritiser's level map for the picked axis,
      moved_source          <- measurement_feedback's outcome for attempted_key.
    This is the completed stub: the assessor now reads the loop's REAL state. Returns
    the Iteration node."""
    f_level, f_rank = frontier_rank_from_perception(substrate)
    set_frontier(substrate, f_level, f_rank)
    p_level, p_rank = pick_rank_from_axis(pick_capability_keys)
    moved = moved_source_from_feedback(substrate, attempted_key) if attempted_key else 1
    return record_iteration(substrate, label, effort, probe_payoff, fixer_payoff,
                            pick_level=p_level, pick_rank=p_rank, moved_source=moved)


# --------------------------------------------------------------------------
# the assessor — general graph Rules (composed Term-trees, native eval)
# --------------------------------------------------------------------------

def install_domain_spinning_rule(substrate) -> dict:
    """DOMAIN_SPINNING (window-level). The PROBE channel is spinning iff effort rose
    across the window AND the probe stayed BELOW its target across the WHOLE window
    (first AND last below target). Judged on the PROBE alone — the conflation fix —
    so a moving fixer can never make it look healthy. Reads the root's first_iter +
    last_iter endpoints. Sets loop_issue. General: bands + target are seeded dials,
    no session constant."""
    nat = _native(substrate)
    R, F, L = Var("R"), Var("F"), Var("L")
    effort_rose = Gt(a=Attr(L, "effort"),
                     b=Attr(F, "effort"))   # last effort > first effort
    first_below = Lt(a=Attr(F, "probe_payoff"), b=Attr(R, "probe_target"))
    last_below = Lt(a=Attr(L, "probe_payoff"), b=Attr(R, "probe_target"))
    below_throughout = And(items=(first_below, last_below))
    spinning = And(items=(effort_rose, below_throughout))
    issue_next = IfThenElse(spinning, Lit("domain_spinning"), Lit("none"))
    rule = {
        "name": "assess_domain_spinning",
        "match": [["R", "first_iter", "F"], ["R", "last_iter", "L"]],
        "where": Eq(a=Attr(R, "loop_eval_pending"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "R", "loop_issue", {"__term__": issue_next.to_dict()}],
        ],
    }
    return {"root": _root(substrate), "rule_index": nat.add_rule(rule)}


def install_fixer_progress_rule(substrate) -> dict:
    """FIXER_PROGRESS (window-level). The FIXER channel rose across the window
    (last fixer > first fixer) -> the loop is compounding real capability; record
    `fixer_progressing` = 1 so the agent reads that fixer progress is REAL and must
    NOT be flagged as spinning. A separate channel from the probe — the whole point
    of two channels. General."""
    nat = _native(substrate)
    R, F, L = Var("R"), Var("F"), Var("L")
    fixer_rose = Gt(a=Attr(L, "fixer_payoff"), b=Attr(F, "fixer_payoff"))
    prog_next = IfThenElse(fixer_rose, Lit(1), Lit(0))
    rule = {
        "name": "assess_fixer_progress",
        "match": [["R", "first_iter", "F"], ["R", "last_iter", "L"]],
        "where": Eq(a=Attr(R, "loop_eval_pending"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "R", "fixer_progressing",
             {"__term__": prog_next.to_dict()}],
            ["set_attr", "R", "loop_eval_pending", 0],
        ],
    }
    return {"rule_index": nat.add_rule(rule)}


def install_below_frontier_rule(substrate) -> dict:
    """BELOW_FRONTIER (per-iteration). An iteration whose pick_rank is strictly
    DOWNSTREAM of the root's frontier_rank (pick_rank > frontier_rank) spent effort
    below where the bottleneck is -> set the iteration's `below_frontier` = 1.
    Reads both the root (frontier_rank) and the iteration (pick_rank) via the
    has_iter match. General over the rank ordering — no per-iteration constant."""
    nat = _native(substrate)
    R, I = Var("R"), Var("I")
    downstream = Gt(a=Attr(I, "pick_rank"), b=Attr(R, "frontier_rank"))
    flag_next = IfThenElse(downstream, Lit(1), Lit(0))
    rule = {
        "name": "assess_below_frontier",
        "match": [["R", "has_iter", "I"]],
        "where": Eq(a=Attr(I, "iter_eval_pending"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "I", "below_frontier",
             {"__term__": flag_next.to_dict()}],
        ],
    }
    return {"rule_index": nat.add_rule(rule)}


def install_fix_the_outcome_rule(substrate) -> dict:
    """FIX_THE_OUTCOME (per-iteration). An iteration that added +0 fixer capability
    (fixer_delta <= the flat band) AND whose change did NOT move its source
    (moved_source == 0) is a detour that papered over a symptom -> set
    `fix_the_outcome` = 1 and clear the iteration's pending flag. General: the band
    is a seeded dial; moved_source is a reported signal (live vs stub: see
    docstring)."""
    nat = _native(substrate)
    R, I = Var("R"), Var("I")
    no_fixer = Lte(a=Attr(I, "fixer_delta"), b=Attr(R, "fixer_flat_band"))
    didnt_move = Eq(a=Attr(I, "moved_source"), b=Lit(0))
    detour = And(items=(no_fixer, didnt_move))
    flag_next = IfThenElse(detour, Lit(1), Lit(0))
    rule = {
        "name": "assess_fix_the_outcome",
        "match": [["R", "has_iter", "I"]],
        "where": Eq(a=Attr(I, "iter_eval_pending"), b=Lit(1)).to_dict(),
        "effects": [
            ["set_attr", "I", "fix_the_outcome",
             {"__term__": flag_next.to_dict()}],
            ["set_attr", "I", "iter_eval_pending", 0],
        ],
    }
    return {"rule_index": nat.add_rule(rule)}


def install_all_rules(substrate) -> dict:
    """Install the four assessor Rules. Returns their indices."""
    ds = install_domain_spinning_rule(substrate)
    fp = install_fixer_progress_rule(substrate)
    bf = install_below_frontier_rule(substrate)
    fo = install_fix_the_outcome_rule(substrate)
    return {"root": ds["root"],
            "domain_spinning": ds["rule_index"],
            "fixer_progress": fp["rule_index"],
            "below_frontier": bf["rule_index"],
            "fix_the_outcome": fo["rule_index"]}


def agent_assess(substrate, rules: dict, max_iters: int = 200) -> dict:
    """Fire the four assessor Rules over the loop graph until their pending flags
    clear, then read back the verdicts. The DECISIONS were the Rules'; this just
    drives them and reads state. Returns the structured report (see get_issues)."""
    nat = _native(substrate)
    root = _root(substrate)
    # window-level (root pending) — domain_spinning then fixer_progress (the latter
    # clears loop_eval_pending).
    for _ in range(max_iters):
        if substrate.node(root)["attrs"].get("loop_eval_pending") != 1:
            break
        nat.apply_rule_once(rules["domain_spinning"])
        nat.apply_rule_once(rules["fixer_progress"])
    # per-iteration (iter pending) — below_frontier then fix_the_outcome.
    for _ in range(max_iters):
        pending = [i for i in substrate.neighbours(root, "has_iter")
                   if substrate.node(i)["attrs"].get("iter_eval_pending") == 1]
        if not pending:
            break
        nat.apply_rule_once(rules["below_frontier"])
        nat.apply_rule_once(rules["fix_the_outcome"])
    return get_issues(substrate)


# --------------------------------------------------------------------------
# read-back (mechanical query)
# --------------------------------------------------------------------------

def get_issues(substrate) -> dict:
    """What the assessor currently flags, as the agent reads it:
      {loop_issue, fixer_progressing, iterations: [{label, below_frontier,
       fix_the_outcome, ...}]}. Decisions were the Rules'; this is a pure query."""
    root = _root(substrate)
    a = substrate.node(root)["attrs"]
    iters = []
    for i in substrate.neighbours(root, "has_iter"):
        ia = substrate.node(i)["attrs"]
        iters.append({
            "label": ia.get("label"),
            "effort": ia.get("effort"),
            "probe_payoff": ia.get("probe_payoff"),
            "fixer_payoff": ia.get("fixer_payoff"),
            "fixer_delta": ia.get("fixer_delta"),
            "pick_level": ia.get("pick_level"),
            "pick_rank": ia.get("pick_rank"),
            "moved_source": ia.get("moved_source"),
            "below_frontier": ia.get("below_frontier"),
            "fix_the_outcome": ia.get("fix_the_outcome"),
        })
    iters.sort(key=lambda d: (d.get("effort") if d.get("effort") is not None
                              else 0.0))
    return {
        "loop_issue": a.get("loop_issue", "none"),
        "fixer_progressing": a.get("fixer_progressing", 0),
        "frontier_level": a.get("frontier_level"),
        "frontier_rank": a.get("frontier_rank"),
        "probe_target": a.get("probe_target"),
        "iterations": iters,
        "flagged_iterations": {
            "below_frontier": [d["label"] for d in iters
                               if d.get("below_frontier") == 1],
            "fix_the_outcome": [d["label"] for d in iters
                                if d.get("fix_the_outcome") == 1],
        },
    }


__all__ = ["set_frontier", "record_iteration", "record_iteration_auto",
           "frontier_rank_from_perception", "pick_rank_from_axis",
           "moved_source_from_feedback",
           "install_domain_spinning_rule", "install_fixer_progress_rule",
           "install_below_frontier_rule", "install_fix_the_outcome_rule",
           "install_all_rules", "agent_assess", "get_issues"]
