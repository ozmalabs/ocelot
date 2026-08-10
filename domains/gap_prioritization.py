"""gap_prioritization — THE SCHEDULING LAYER. The jabberwock already DRIVES its
fixes on BOTH dimensions -- efficiency (domains/performance_self_improvement.py)
and understanding (domains/understanding_self_improvement.py): perceive a gap ->
DIAGNOSE its shape (graph) -> SELECT the fix (graph) -> VERIFY (#2) -> APPLY. But
when MULTIPLE gaps are perceived at once it did NOT yet DECIDE which to fix FIRST.
This module adds that decision -- and, crucially, the ORDER comes OUT of the graph,
not from a hardcoded Python order.

PRINCIPLE (the substrate's own currency). Salience = residual = surprise ("explore
the under-compressed"). The gap with the biggest MEASURED residual is fixed first.
Each perceived CapabilityGap already CARRIES a measured salience its #1 collapse
minted:
  · an EFFICIENCY gap -> the latency-excess (cold_ms - warm; a ~1.4s one-time init
    is HUGE salience -- performance_self_improvement.perceive_performance_gap sets
    it);
  · an UNDERSTANDING gap -> the defect-severity (1 - min error-feature;
    understanding_self_improvement.perceive_understanding_gaps sets it).

Cross-domain the raw magnitudes are NOT comparable (ms vs a 0..1 severity), so they
are NORMALIZED per the agent's POLICY -- SaliencePolicyWeight nodes carrying a
per-kind weight (graph data, tunable, seeds/gap_prioritization.json). This is a
stated POLICY (how many ms of latency-excess trade for one unit of understanding
defect), NOT a false-universal metric -- said plainly.

THE CYCLE (each step is either a mechanical boundary op OR a graph decision; never a
Python sort that bakes the policy into Python):

  1. PERCEIVE the gaps -- run the two EXISTING perceivers (efficiency +
     understanding); each mints CapabilityGaps carrying a MEASURED raw salience.
     Mark each as an agenda member (in_agenda=1, ordered=0) -- mechanical marshaling.

  2. NORMALIZE per POLICY -- the graph-resident `salience_normalize` Program
     (Times(raw, policy_weight_for_kind); the weight is read from the matching
     SaliencePolicyWeight by an Argmin-over-Filter-by-kind, the SAME shape
     perf_fix_pick uses) evaluated in Rust. The WEIGHTS are graph data (the policy);
     the arithmetic is a Rust Term. Python passes the gap's raw salience + kind and
     writes back `norm_salience`.

  3. PRIORITIZE as a GRAPH DECISION (the crux -- NOT hardcoded order). The
     graph-resident `gap_priority` Program is an Argmax over the still-unordered
     agenda gaps (Filter CapabilityGap where in_agenda==1 And Not ordered==1) by
     their normalized salience -- it returns the MOST-salient gap. Applied
     REPEATEDLY (Python marks the picked gap `ordered` and re-evaluates) the Program
     EMITS the whole order, most-salient-first. The ORDER is the Program's output
     over the salience DATA: boost an understanding gap's salience above the
     efficiency gap's and the SAME Program yields a DIFFERENT order. Python never
     sorts the gaps -- it only reads the graph's pick and sequences the enactment.

  4. FIX IN THE DECIDED ORDER -- for each gap in the graph-decided order, dispatch
     to the EXISTING driver (performance_self_improvement for a perf gap,
     understanding_self_improvement for an understanding gap) via a name-keyed
     registry keyed on the gap's `kind` (the twin of research_agenda._FILLER_REGISTRY
     -- mechanical marshaling, not a decision). Each driver diagnoses+selects (graph)
     and #2-VERIFIES its fix. The AGENDA is the graph's; the fixers are the
     already-built ones.

DISCIPLINE (CLAUDE.md). The ORDERING is the `gap_priority` Program (Rust-evaluated),
applied repeatedly -- there is NO `sorted(gaps, key=...)`, no `.sort()` over gaps, no
'efficiency-first' literal. The salience MEASUREMENT is the perceivers' boundary I/O;
the normalization WEIGHTS are graph-data POLICY (stated, not universal). The per-gap
fixing is the already-built drivers, called as-is. The driver only PERCEIVES (reuse),
NORMALIZES (graph Program), reads the graph's ORDER, and SEQUENCES the enactment.
donkey=0.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from domains import performance_self_improvement as psi
from domains import reflective_faculty as rf
from domains import stopping_policy as sp
from domains import understanding_self_improvement as usi


# ---------------------------------------------------------------------------
# resolve — the same duck-typing the sibling faculties use.
# ---------------------------------------------------------------------------
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    ag_node = getattr(agent, "agent", None)
    if ag_node is None:
        ag_node = rf._agent_root_node(sub)
    return sub, native, ag_node


PERFORMANCE = psi.PERFORMANCE          # "performance"
UNDERSTANDING = usi.UNDERSTANDING      # "understanding"


# ===========================================================================
# SEED — the two graph Programs (salience_normalize + gap_priority) + the
# SaliencePolicyWeight policy nodes. Idempotent load (guarded on gap_priority).
# ===========================================================================
def _ensure_seed(agent) -> None:
    """Idempotently ensure the gap-prioritization Programs + SaliencePolicyWeight
    nodes are held (seeds/gap_prioritization.json). Guarded on gap_priority being
    present, so a boot that already auto-loaded the seed never double-loads. Loading
    vocabulary is admissible adapter work, not a decision."""
    sub, native, ag_node = _resolve(agent)
    if rf._load_program(sub, "gap_priority") is not None:
        return
    from substrate.seed_loader import manifest_for
    native.load_seed_manifest(manifest_for("gap_prioritization"), ag_node)


# ===========================================================================
# (1) PERCEIVE — run the two EXISTING perceivers; collect the gaps they mint;
# mark each an agenda member. The gap DECISION + the salience MEASUREMENT are the
# perceivers'; this only marshals the queue.
# ===========================================================================
def _gap_attrs(agent, gap) -> dict:
    sub = getattr(agent, "s", agent)
    return dict(gap) if isinstance(gap, dict) else dict(sub.node(gap)["attrs"])


def _set(agent, gap, key, value) -> None:
    sub = getattr(agent, "s", agent)
    try:
        sub.set_attr(gap, key, value)
    except Exception:
        pass


def perceive_gaps(agent) -> list:
    """PERCEIVE the multi-dimensional gap queue from the agent's OWN perceivers:

      · the EFFICIENCY perceiver (performance_self_improvement) -> one perf gap
        carrying salience = latency-excess (cold_ms - warm);
      · the UNDERSTANDING perceiver (understanding_self_improvement) -> two
        understanding gaps, each carrying salience = defect-severity.

    Marks each minted gap an agenda member (in_agenda=1, ordered=0) so the
    gap_priority Program scopes to exactly these. Returns the agenda gap ids. The
    salience is ALREADY on each gap (the perceivers measured it); nothing here
    decides or scores."""
    _ensure_seed(agent)
    agenda: list = []
    pperc = psi.perceive_performance_gap(agent)
    if pperc.get("gap") is not None:
        agenda.append(pperc["gap"])
    uperc = usi.perceive_understanding_gaps(agent)
    for g in (uperc.get("gaps") or []):
        agenda.append(g)
    for g in agenda:
        _set(agent, g, "in_agenda", 1.0)
        _set(agent, g, "ordered", 0.0)
    return agenda


def gap_salience(agent, gap) -> tuple:
    """Read a gap's measured (kind, raw_salience) off its attrs. Mechanical."""
    at = _gap_attrs(agent, gap)
    return at.get("kind"), at.get("salience")


# ===========================================================================
# (2) NORMALIZE — the graph-resident salience_normalize Program (Times(raw,
# policy_weight_for_kind)) evaluated in Rust. The weight is POLICY (graph data);
# Python passes the gap's raw salience + kind and writes back norm_salience.
# ===========================================================================
def normalize_salience(agent, gap) -> Optional[float]:
    """Normalize a gap's raw measured salience by the agent's POLICY weight for its
    kind, via the graph-resident salience_normalize Program (Rust). Writes back the
    gap's `norm_salience` attr and returns it. No Python weighting -- the weight is
    the SaliencePolicyWeight the Program reads; the multiply is the Program's Times."""
    _ensure_seed(agent)
    sub, native, _ = _resolve(agent)
    kind, raw = gap_salience(agent, gap)
    if kind is None or raw is None:
        return None
    prog = rf._load_program(sub, "salience_normalize")
    if prog is None:
        return None
    val = native.evaluate(prog, {"raw": float(raw), "kind": str(kind)})
    try:
        norm = float(val)
    except Exception:
        return None
    _set(agent, gap, "norm_salience", norm)
    return norm


def normalize_all(agent, gaps: list) -> dict:
    """Normalize every agenda gap's salience (graph Program). Returns
    {gap: norm_salience}. Mechanical marshaling over the graph decision."""
    return {g: normalize_salience(agent, g) for g in gaps}


# ===========================================================================
# (3) PRIORITIZE — THE GRAPH DECISION. The gap_priority Program (Argmax over the
# unordered agenda gaps by normalized salience) is applied REPEATEDLY: each pick is
# the graph's, Python only marks the picked gap `ordered` and re-evaluates. The
# ORDER is the sequence of the Program's picks. NO Python sort.
# ===========================================================================
def _pick_most_salient(agent) -> Optional[Any]:
    """Evaluate the gap_priority Program ONCE: the MOST-salient still-unordered
    agenda gap (or None when the agenda is drained). The pick is the Program's
    Argmax output in Rust -- not a Python max/sort."""
    _ensure_seed(agent)
    sub, native, _ = _resolve(agent)
    prog = rf._load_program(sub, "gap_priority")
    if prog is None:
        return None
    val = native.evaluate(prog, {})
    if val is None:
        return None
    return val


def prioritize(agent, gaps: list, *, max_iters: int = 256) -> list:
    """ORDER the agenda most-salient-first -- the ORDER coming OUT of the graph.

    Repeatedly evaluate the graph-resident gap_priority Program (Argmax by
    normalized salience over the still-unordered agenda gaps); each returned node is
    the graph's pick. Python appends it to the order and marks it `ordered` so the
    NEXT evaluation excludes it -- then re-evaluates. The loop ends when the Program
    returns None (agenda drained). The sequence of picks IS the order.

    This is NOT a Python-side ranking: no comparator, no ordering key, no policy
    baked into Python. Every position in the order is a separate graph decision (a
    separate Argmax over the current salience data). Boosting a gap's salience
    changes which node each Argmax returns -- so the SAME Program yields a DIFFERENT
    order. Python only sequences.

    `gaps` is passed so the caller's agenda is what gets ordered (they were marked
    in_agenda by perceive_gaps); the return preserves node identity."""
    normalize_all(agent, gaps)
    order: list = []
    seen: set = set()
    for _ in range(max_iters):
        pick = _pick_most_salient(agent)
        if pick is None:
            break
        if pick in seen:                       # safety: never loop on a stuck pick
            _set(agent, pick, "ordered", 1.0)
            continue
        seen.add(pick)
        order.append(pick)
        _set(agent, pick, "ordered", 1.0)      # exclude from the next Argmax
    return order


def reset_order(agent, gaps: list) -> None:
    """Clear the `ordered` marks so the agenda can be re-prioritized (e.g. after a
    salience boost, to show the SAME Program reorder). Mechanical."""
    for g in gaps:
        _set(agent, g, "ordered", 0.0)


def order_view(agent, order: list) -> list:
    """A printable view of a graph-decided order: [(kind, raw_salience,
    norm_salience, faculty/stage), ...]. Mechanical read-back for the ledger."""
    view = []
    for g in order:
        at = _gap_attrs(agent, g)
        view.append({
            "gap": str(g),
            "kind": at.get("kind"),
            "salience": at.get("salience"),
            "norm_salience": at.get("norm_salience"),
            "label": at.get("faculty") or at.get("stage"),
        })
    return view


# ===========================================================================
# (4) FIX IN THE DECIDED ORDER — dispatch each gap, in the graph order, to its
# EXISTING driver (keyed on kind). A name-keyed registry (the twin of
# research_agenda._FILLER_REGISTRY): mechanical marshaling, not a decision. Each
# driver #2-verifies its own fix.
# ===========================================================================
def _enact_performance(agent, gap) -> dict:
    """Fix a PERFORMANCE gap via the EXISTING efficiency driver: read the gap's
    perceived cold/warm, run its two graph Programs (diagnose+select), #2-verify the
    selected fix, and apply it iff accepted. Calls performance_self_improvement
    as-is."""
    cold, warm = psi.gap_cold_warm(agent, gap)
    verdict = psi.diagnose_and_select(agent, cold, warm)
    fix = verdict.get("fix")
    verify = psi.verify_fix(agent, fix, cold, warm) if fix else None
    accepted = bool(verify and verify.get("accepted"))
    applied = psi.apply_fix(agent, fix) if (fix and accepted) else None
    return {"kind": PERFORMANCE, "diagnosis": verdict, "fix": fix,
            "verify": verify, "accepted": accepted, "applied": applied}


def _enact_understanding(agent, gap) -> dict:
    """Fix an UNDERSTANDING gap via the EXISTING understanding driver: read the gap's
    measured error-features, run its two graph Programs (diagnose+select), #2-verify
    the selected fix, and apply it iff accepted. Calls understanding_self_improvement
    as-is."""
    hn, sf = usi.gap_error_features(agent, gap)
    verdict = usi.diagnose_and_select(agent, hn, sf)
    shape, fix = verdict.get("shape"), verdict.get("fix")
    verify = usi.verify_fix_cleans(agent, fix, shape) if (fix and shape) else None
    accepted = bool(verify and verify.get("accepted"))
    applied = usi.apply_fix(agent, fix) if (fix and accepted) else None
    return {"kind": UNDERSTANDING, "diagnosis": verdict, "shape": shape, "fix": fix,
            "verify": verify, "accepted": accepted, "applied": applied}


_DRIVER_REGISTRY: dict[str, Callable[[Any, Any], dict]] = {
    # name-keyed marshaling -- the twin of research_agenda._FILLER_REGISTRY. The
    # gap's kind (set by its perceiver) names the driver; this maps the name to the
    # already-built driver call. A mechanical lookup, NOT a decision (and NOT the
    # order: the order is the graph Program's).
    PERFORMANCE: _enact_performance,
    UNDERSTANDING: _enact_understanding,
}


def enact_in_order(agent, order: list) -> list:
    """Fix the gaps in the GRAPH-DECIDED order, dispatching each to its existing
    driver (keyed on kind). Returns the enactment ledger, one record per gap, IN
    ORDER -- so the enactment order == the graph order. Each record carries the
    driver's #2 verdict. Python only sequences; the drivers do the fixing."""
    ledger: list = []
    for g in order:
        kind, _raw = gap_salience(agent, g)
        driver = _DRIVER_REGISTRY.get(kind)
        if driver is None:
            ledger.append({"gap": g, "gap_str": str(g),
                           "kind": kind, "note": f"no driver for kind {kind!r}"})
            continue
        rec = driver(agent, g)
        rec["gap"] = g
        rec["gap_str"] = str(g)
        ledger.append(rec)
    return ledger


# ===========================================================================
# (5) FIX-IN-ORDER, STOPPING BY SUFFICIENCY — the SAME graph-order enactment, but
# the agent DECIDES WHEN TO STOP. Before each fix (and before the first) the seeded
# should_continue Program is evaluated in Rust: CONTINUE iff the top remaining
# normalized salience exceeds the SufficiencyPolicy threshold, else STOP -- leaving
# the sub-threshold gaps UNFIXED (competent-man sufficiency, not completion). Python
# only READS the boolean and breaks; it never counts, never `while gaps:`, never
# carries a threshold. The stop point MOVES with the salience DATA, not a count.
# ===========================================================================
def enact_in_order_with_stopping(agent, order: list) -> tuple:
    """Fix the gaps in the GRAPH-DECIDED order, but STOP when the graph's
    should_continue Program says the remainder is not salient enough to be worth
    fixing. Returns (ledger, left):

      · ledger -- one record per FIXED gap, IN ORDER (each with its driver #2 verdict);
      · left   -- the gap ids LEFT UNFIXED (the sufficiency remainder), in order.

    Before enacting each gap, evaluate should_continue (Rust). If it returns STOP, the
    current gap and everything after it are LEFT UNFIXED and the loop breaks -- the
    sub-threshold gaps are deliberately not fixed. Otherwise enact via the existing
    driver and MARK the gap fixed so the NEXT should_continue scopes to the strictly
    smaller remainder. The TERMINATION is the graph Program's; Python sequences +
    marshals."""
    ledger: list = []
    idx = 0
    for i, g in enumerate(order):
        if not sp.should_continue(agent):
            idx = i                                # STOP: leave g.. unfixed
            break
        kind, _raw = gap_salience(agent, g)
        driver = _DRIVER_REGISTRY.get(kind)
        if driver is None:
            rec = {"gap": g, "gap_str": str(g), "kind": kind,
                   "note": f"no driver for kind {kind!r}"}
        else:
            rec = driver(agent, g)
            rec["gap"] = g
            rec["gap_str"] = str(g)
        ledger.append(rec)
        sp.mark_fixed(agent, g)                    # exclude from the next should_continue
        idx = i + 1
    left = list(order[idx:])
    return ledger, left


# ===========================================================================
# THE CYCLE — perceive -> normalize (graph) -> prioritize (graph order) ->
# fix-in-order UNTIL the graph says STOP (sufficiency). The agent SCHEDULES its own
# fixes AND decides when what remains is not worth fixing.
# ===========================================================================
def run_cycle(agent) -> dict:
    """The whole SCHEDULING cycle, end to end:

      PERCEIVE   the multi-dimensional gap queue (efficiency + understanding
                 perceivers; each gap carries a MEASURED salience)
        -> NORMALIZE per POLICY  (the salience_normalize graph Program, in Rust)
        -> PRIORITIZE            (the gap_priority Argmax Program, applied repeatedly
                                  -- the ORDER comes OUT of the graph)
        -> FIX IN ORDER UNTIL STOP  (dispatch each gap, in the graph order, to its
                                  existing driver, which #2-verifies -- but STOP when
                                  the should_continue Program decides the remainder is
                                  not salient enough to be worth fixing, leaving the
                                  sub-threshold gaps UNFIXED: sufficiency, not
                                  completion)

    Returns the full ledger {agenda, order, enacted, left, stopped}. The DECISIONS
    (normalize, order, diagnose, select, STOP) are the graph's; the driver only
    sequences + marshals. `left` is the deliberately-unfixed remainder; `stopped` is
    True iff the graph STOPPED before draining the whole order (sufficiency reached)."""
    agenda = perceive_gaps(agent)
    norms = normalize_all(agent, agenda)
    order = prioritize(agent, agenda)
    view = order_view(agent, order)
    enacted, left = enact_in_order_with_stopping(agent, order)
    return {"agenda": agenda, "norms": norms, "order": order,
            "order_view": view, "enacted": enacted,
            "left": left, "left_view": order_view(agent, left),
            "stopped": bool(left),
            "sufficiency_threshold": sp.sufficiency_threshold(agent)}


__all__ = [
    "PERFORMANCE", "UNDERSTANDING",
    "perceive_gaps", "gap_salience",
    "normalize_salience", "normalize_all",
    "prioritize", "reset_order", "order_view",
    "enact_in_order", "enact_in_order_with_stopping", "run_cycle",
    "_DRIVER_REGISTRY",
]
