"""stopping_policy — THE STOP DECISION as a GRAPH DECISION. The last step of the
self-improvement loop that was still a Python drain.

The jabberwock already runs the whole loop as graph decisions: PERCEIVE its gaps
(#1) -> PRIORITIZE them most-salient-first (gap_prioritization: the gap_priority
Argmax Program) -> DIAGNOSE + SELECT + VERIFY + APPLY each fix (the perf /
understanding drivers). The ONE step not yet a real agent decision was TERMINATION:
gap_prioritization.run_cycle simply drained the whole ordered agenda (a Python
for-loop over every gap). This module makes STOPPING the agent's OWN graph decision.

PRINCIPLE — SUFFICIENCY, not completion (the substrate's own stance: "sufficient at
~90%, then move on; yeah yeah, the rest"). There is NO win condition. The agent STOPS
when what REMAINS is not salient enough to be worth fixing, deliberately leaving
low-salience gaps UNFIXED. This is the competent-man sufficiency, not "fix
everything".

THE DECISION IS ONE GRAPH PROGRAM (seeds/stopping_policy.json), the twin of
perf_diagnose / gap_priority:

  should_continue  =  IfThenElse(
                        Gt( MaxOver(unfixed agenda gaps, by norm_salience, default -1),
                            SufficiencyPolicy.threshold ),
                        1.0,        # CONTINUE
                        0.0 )       # STOP

It reads the REMAINING agenda's TOP salience -- MaxOver the still-unfixed agenda gaps
(Filter CapabilityGap where in_agenda==1 And Not fixed==1) by their norm_salience,
default -1 when the agenda is empty -- and compares it to the SufficiencyPolicy
threshold (graph data, tunable) via Gt: CONTINUE iff max_remaining_salience >
sufficiency_threshold, else STOP. The verdict is the Program's output, evaluated in
Rust; Python only reads the boolean and breaks the loop.

The stop point MOVES with the salience DATA, NOT a count: RAISE a left gap's salience
above the threshold and the SAME Program CONTINUES and fixes it; LOWER it and the SAME
Program STOPS and leaves it. Two runs with the SAME number of gaps but different
salience distributions stop after DIFFERENT counts.

DISCIPLINE (CLAUDE.md). The STOP verdict is the should_continue Program (Rust). There
is NO Python `while gaps:`, no count-based termination, no threshold literal in
Python -- the loop guard READS the Program's boolean and breaks; it never decides. The
salience MEASUREMENT is the perceivers' boundary I/O; the sufficiency threshold is a
stated POLICY (graph data, tunable) -- NOT a universal 'good enough'. The per-gap
fixing is the already-built drivers, called as-is. donkey=0.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import reflective_faculty as rf


# the attr that marks a gap already fixed this cycle (so should_continue scopes to the
# STILL-unfixed remainder). Absent == not-fixed (the Program's Not(Eq(..,1)) treats a
# missing attr as unfixed) -- we set it explicitly for clarity + read-back.
FIXED = "fixed"


def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = rf._agent_root_node(sub)
    return sub, native, ag_node


# ===========================================================================
# SEED — the should_continue Program + the SufficiencyPolicy threshold node.
# Idempotent load (guarded on should_continue being present), the SAME pattern
# gap_prioritization._ensure_seed uses. Loading vocabulary is admissible adapter
# work, not a decision.
# ===========================================================================
def _ensure_seed(agent) -> None:
    """Idempotently ensure the stopping-policy Program + SufficiencyPolicy node are
    held (seeds/stopping_policy.json). Guarded on should_continue being present, so a
    boot that already auto-loaded the seed never double-loads."""
    sub, native, ag_node = _resolve(agent)
    if rf._load_program(sub, "should_continue") is not None:
        return
    from substrate.seed_loader import manifest_for
    native.load_seed_manifest(manifest_for("stopping_policy"), ag_node)


# ===========================================================================
# THE DECISION — evaluate the should_continue Program (Rust). Python reads the
# boolean; it does not decide.
# ===========================================================================
def should_continue(agent) -> bool:
    """The STOP decision, as the graph's verdict: True == CONTINUE (the top remaining
    normalized salience exceeds the sufficiency threshold), False == STOP (leave the
    sub-threshold gaps unfixed). Evaluates the seeded should_continue Program in Rust
    and reads its 1.0/0.0 output -- NO Python comparison, NO threshold literal, NO
    count. When no unfixed agenda gap remains the Program's MaxOver default (-1) makes
    it STOP (a clean resting point)."""
    _ensure_seed(agent)
    sub, native, _ = _resolve(agent)
    prog = rf._load_program(sub, "should_continue")
    if prog is None:
        return False
    val = native.evaluate(prog, {})
    try:
        # the Program emits exactly 1.0 (CONTINUE) / 0.0 (STOP); decode that boolean.
        # NOTE: this compares the Program's OWN 0/1 output, NOT salience -- the
        # salience-vs-threshold comparison lives inside the graph Program, never here.
        return float(val) > 0.0
    except Exception:
        return False


def mark_fixed(agent, gap) -> None:
    """Mark a gap fixed this cycle so should_continue scopes to the remainder.
    Mechanical boundary write."""
    sub = getattr(agent, "s", agent)
    try:
        sub.set_attr(gap, FIXED, 1.0)
    except Exception:
        pass


def reset_fixed(agent, gaps: list) -> None:
    """Clear the fixed marks so the agenda can be re-driven (e.g. after a salience
    change, to show the SAME Program stop at a different point). Mechanical."""
    sub = getattr(agent, "s", agent)
    for g in gaps:
        try:
            sub.set_attr(g, FIXED, 0.0)
        except Exception:
            pass


# ===========================================================================
# POLICY read/tune — the sufficiency threshold is graph data (a stated POLICY),
# tunable. Reading/writing it is mechanical boundary I/O.
# ===========================================================================
def _policy_node(agent) -> Optional[Any]:
    sub = getattr(agent, "s", agent)
    for n in sub.nodes("SufficiencyPolicy"):
        return n
    return None


def sufficiency_threshold(agent) -> Optional[float]:
    """Read the current sufficiency threshold off the SufficiencyPolicy node (graph
    data). Mechanical read for the ledger."""
    _ensure_seed(agent)
    sub = getattr(agent, "s", agent)
    n = _policy_node(agent)
    if n is None:
        return None
    try:
        return float(sub.node(n)["attrs"].get("threshold"))
    except Exception:
        return None


def set_sufficiency_threshold(agent, threshold: float) -> None:
    """Tune the sufficiency POLICY: write the SufficiencyPolicy node's threshold
    attr (graph data). This is POLICY tuning -- the agent's stated stance on how much
    residual is 'good enough to leave' -- NOT a decision, NOT a universal metric.
    Mechanical boundary write."""
    _ensure_seed(agent)
    sub = getattr(agent, "s", agent)
    n = _policy_node(agent)
    if n is None:
        return
    try:
        sub.set_attr(n, "threshold", float(threshold))
    except Exception:
        pass


__all__ = [
    "FIXED",
    "should_continue", "mark_fixed", "reset_fixed",
    "sufficiency_threshold", "set_sufficiency_threshold",
    "_ensure_seed",
]
