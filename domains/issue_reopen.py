"""issue_reopen — THE REOPEN DECISION as a GRAPH DECISION, the twin of
should_continue run the OTHER way. stopping_policy STOPS by SUFFICIENCY and
deliberately leaves the low-salience gaps UNFIXED (gap_prioritization.run_cycle's
`left` set -- the DEFERRED agenda). This module lets the jabberwock DECIDE WHEN TO
REOPEN one of those deferred gaps and PASS IT THROUGH into the running session.

THE DECISION IS ONE GRAPH PROGRAM (seeds/issue_reopen.json), the twin of
should_continue:

  should_reopen(g) = IfThenElse(
                       Gt( g.norm_salience,          # the gap's CURRENT (re-measured)
                           ReopenPolicy.threshold ), #   salience, read IN the graph
                       1.0,        # REOPEN
                       0.0 )       # stay DEFERRED

The gap node is bound as env var `g`; both the gap-attr read AND the threshold read
live inside the graph (the threshold via an Argmin over ReopenPolicy by priority,
exactly as should_continue reads SufficiencyPolicy). It is evaluated in Rust; Python
passes only the gap id and reads the Program's 1.0/0.0 output -- it never compares
salience to a threshold in Python, never counts ticks, never carries a flag.

HYSTERESIS (a STATED policy, honest -- not an accident). ReopenPolicy.threshold
(graph data) is DISTINCT from and >= SufficiencyPolicy.threshold. So a gap DEFERRED at
a low salience does NOT immediately reopen: reopen is a strictly HIGHER bar than
un-defer. Between the two thresholds is a dead-band -- a gap whose re-measured
salience drifts up ABOVE the sufficiency floor yet stays BELOW the reopen bar does not
reopen; it reopens only once re-measurement lifts it above the (higher) reopen bar.
Issues do not thrash across the stop boundary. The salience RE-MEASUREMENT is the
normaliser's boundary I/O (the gap_prioritization salience_normalize graph Program);
the reopen threshold is graph-data POLICY, tunable.

PASS-THROUGH is a genuine LIVE-graph hand-off, NOT a print. A reopened gap is
PROMOTED to a `ReopenedConcern` node with active=1, edged from the agent hub
(has_concern). The LIVE loop consumes it: the seeded `reopened_concern_pursue` Reflex
(shipped via the seed's "reflexes" key) has stimulus "an active ReopenedConcern
exists", so it TRIPS inside the running adapter's fire_reflexes -- the running session
SEES the reopened issue, and its response marks it pursued. The reopened gap re-enters
the LIVE session, not the batch queue.

DISCIPLINE (CLAUDE.md). The REOPEN verdict is the should_reopen Program (Rust); Python
reads the boolean. The salience re-measurement + the pass-through node/edge mint are
mechanical boundary I/O (add_node/add_edge). The two thresholds are stated POLICIES
(graph data). No hardcoded reopen, no tick-count, no threshold literal in Python.
donkey=0.
"""
from __future__ import annotations

from typing import Any, Optional

from domains import gap_prioritization as gp
from domains import reflective_faculty as rf


# the reopened-issue node type the LIVE loop consumes + the hub edge that attaches it.
REOPENED_CONCERN = "ReopenedConcern"
HAS_CONCERN = "has_concern"
# the edge from a reopened concern to the DEFERRED gap it re-surfaces, so the live
# executor recovers the real gap node to dispatch (not a stringified id).
TARGETS_GAP = "targets_gap"
# the reflex whose stimulus trips on an active ReopenedConcern (seed "reflexes" key).
REOPEN_REFLEX = "reopened_concern_pursue"


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
# THE LIVE-LOOP ACT — the I/O boundary the running session's fire_reflexes invokes
# when the reopened-concern reflex trips. Shaped EXACTLY like _question_pursue_advance
# / _enact_advance: for each active ReopenedConcern the running loop surfaces, it
# reads the gap the concern TARGETS + that gap's kind, DISPATCHES the gap to the
# kind-keyed driver (gap_prioritization._DRIVER_REGISTRY -- the SAME
# performance/understanding diagnose->select->#2->apply path enact_in_order uses),
# and RESOLVES the concern (resolved=1, gap fixed=1) IFF the driver's fix
# #2-verifies. Mechanical enactment: it EVALUATES the bound driver result + APPLIES
# it; it NEVER branches on graph state to decide the repair -- the diagnose/select
# DECISIONS are the graph Programs inside the driver, the routing is the registry
# keyed on the gap's kind (the twin of enact_in_order), and the resolve is gated on
# the driver's OWN #2 verdict (the graph's verification, not a Python decision --
# exactly as the drivers gate `applied` on `accepted`). The seeded reflex's stimulus
# is gated on `resolved`, so a CLOSED concern no longer trips: the loop's inbox of
# UNRESOLVED concerns drains without re-running a done fix. `active` is retained as
# the pass-through liveness marker.
# ===========================================================================
def _reopened_concern_pursue_advance(adapter) -> None:
    """The reopened_concern_pursue reflex's RESPONSE. Walk active ReopenedConcern
    nodes; for each, stamp pursued=1.0 (the loop took it up -- provenance), recover
    the DEFERRED gap it targets (the targets_gap edge, not a stringified id), look up
    the driver bound to the gap's KIND in gap_prioritization._DRIVER_REGISTRY (a
    lookup, not a branch -- the twin of question_pursue's resolver-name lookup and of
    enact_in_order's kind dispatch), and CALL it: the driver runs its own two graph
    Programs, #2-verifies, and applies the fix iff accepted. Then CLOSE the concern
    (resolved=1) and mark the gap fixed=1 iff the driver's #2 accepted the fix. No
    if/else over graph state decides the repair -- the repair decisions are the
    driver's graph Programs; this only sequences + marshals + reads the #2 boolean,
    like _question_pursue_advance."""
    from domains import gap_prioritization as gp
    sub, native, _ = _resolve(adapter)
    for c in sub.nodes(REOPENED_CONCERN):
        at = sub.node(c)["attrs"]
        if float(at.get("active", 0.0)) <= 0.0:
            continue
        if float(at.get("resolved", 0.0)) > 0.0:
            continue                                 # already closed -- the loop drained it
        try:
            sub.set_attr(c, "pursued", 1.0)          # provenance: the loop took it up
        except Exception:
            pass
        targets = native.neighbours(c, TARGETS_GAP) if native is not None else []
        if not targets:
            continue                                 # no bound gap -- honest no-op
        gap = targets[0]
        kind = sub.node(gap)["attrs"].get("kind")
        driver = gp._DRIVER_REGISTRY.get(kind)
        if driver is None:
            continue                                 # no driver for this kind -- honest no-op
        rec = driver(adapter, gap)                    # diagnose->select->#2->apply (graph)
        if bool(rec.get("accepted")):                 # the driver's OWN #2 verdict
            # CLOSE the concern: resolved=1 (the loop CLEANED it) + the gap fixed=1.
            # The reflex stimulus is gated on `resolved`, so a closed concern no longer
            # trips -- the inbox of UNRESOLVED concerns drains (active is retained as the
            # pass-through liveness marker). A rejected fix leaves resolved unset: the
            # concern stays OPEN and the loop keeps pursuing it.
            for node, key, val in ((c, "resolved", 1.0), (gap, "fixed", 1.0)):
                try:
                    sub.set_attr(node, key, val)
                except Exception:
                    pass


# ===========================================================================
# SEED — the should_reopen Program + the ReopenPolicy threshold node + the
# reopened-concern Reflex. Idempotent load (guarded on should_reopen being present),
# the SAME pattern stopping_policy._ensure_seed uses. Also registers the reflex's
# live-loop response so fire_reflexes can invoke it. Loading vocabulary + wiring a
# response callable is admissible adapter work, not a decision.
# ===========================================================================
def _ensure_seed(agent) -> None:
    sub, native, ag_node = _resolve(agent)
    # register the live-loop response (idempotent -- overwrites the same key).
    reg = getattr(agent, "register_reflex_response", None)
    if reg is not None:
        reg(REOPEN_REFLEX, _reopened_concern_pursue_advance)
    if rf._load_program(sub, "should_reopen") is not None:
        return
    from substrate.seed_loader import manifest_for
    native.load_seed_manifest(manifest_for("issue_reopen"), ag_node)


# ===========================================================================
# SALIENCE RE-MEASUREMENT — boundary I/O. Re-run the EXISTING gap_prioritization
# salience_normalize graph Program to recompute the gap's norm_salience from its
# CURRENT raw salience. This is the perceiver/normaliser's boundary op (the same
# graph Program the scheduling cycle used) -- not a reopen decision.
# ===========================================================================
def remeasure_salience(agent, gap) -> Optional[float]:
    """Re-measure a deferred gap's normalized salience via the gap_prioritization
    salience_normalize graph Program (Rust). Writes back + returns norm_salience.
    Boundary I/O -- the reopen DECISION is should_reopen, not this."""
    return gp.normalize_salience(agent, gap)


# ===========================================================================
# THE DECISION — evaluate the should_reopen Program (Rust) for ONE deferred gap.
# Python binds the gap id as env `g` and reads the Program's 1.0/0.0 output; it does
# not decide. NO Python salience-vs-threshold compare, NO count, NO threshold literal.
# ===========================================================================
def should_reopen(agent, gap) -> bool:
    """The REOPEN decision on a deferred gap, as the graph's verdict: True == REOPEN
    (the gap's CURRENT norm_salience exceeds the ReopenPolicy threshold), False ==
    stay DEFERRED. Evaluates the seeded should_reopen Program in Rust with the gap
    bound as env `g` and reads its 1.0/0.0 output -- the gap-attr read, the
    threshold read, and the Gt comparison ALL live in the graph."""
    _ensure_seed(agent)
    sub, native, _ = _resolve(agent)
    prog = rf._load_program(sub, "should_reopen")
    if prog is None:
        return False
    val = native.evaluate(prog, {"g": gap})
    try:
        # the Program emits 1.0 (REOPEN) / 0.0 (DEFERRED); decode that boolean. This
        # compares the Program's OWN output, NOT salience -- the salience-vs-threshold
        # comparison lives inside the graph Program, never here.
        return float(val) > 0.0
    except Exception:
        return False


# ===========================================================================
# PASS-THROUGH — promote a reopened gap into the RUNNING session as a live
# ReopenedConcern node, edged from the agent hub, that the running loop consumes.
# Mechanical mint (add_node/add_edge). NOT a print/log -- the seeded reflex's
# stimulus trips on this node in the live fire_reflexes.
# ===========================================================================
def reopen(agent, gap) -> Any:
    """PROMOTE a reopened deferred gap into the running session: mint a
    ReopenedConcern node (active=1) carrying the gap's identity + re-measured
    salience, edge it from the agent hub (has_concern), and re-arm the underlying gap
    (deferred=0, reopened=1, fixed=0, in_agenda=1) so the scheduling cycle would
    re-drive it too. Returns the live concern node id. This is the hand-off the
    running loop SEES -- the seeded reopened_concern_pursue Reflex trips on it."""
    _ensure_seed(agent)
    sub, native, ag_node = _resolve(agent)
    at = sub.node(gap)["attrs"]
    concern = sub.add_node(REOPENED_CONCERN, {
        "active": 1.0,
        "gap": str(gap),
        "kind": at.get("kind"),
        "faculty": at.get("faculty") or at.get("stage"),
        "norm_salience": at.get("norm_salience"),
    })
    try:
        native.add_edge_unchecked(ag_node, HAS_CONCERN, concern)
    except Exception:
        pass
    # bind the concern to the DEFERRED gap it re-surfaces, so the live executor
    # recovers the real gap node to dispatch to the kind-keyed driver.
    try:
        native.add_edge_unchecked(concern, TARGETS_GAP, gap)
    except Exception:
        pass
    # re-arm the deferred gap so the batch cycle would also pick it up again.
    for key, v in (("deferred", 0.0), ("reopened", 1.0),
                   ("fixed", 0.0), ("in_agenda", 1.0), ("ordered", 0.0)):
        try:
            sub.set_attr(gap, key, v)
        except Exception:
            pass
    return concern


# ===========================================================================
# THE REOPEN CYCLE — over the DEFERRED `left` set (gap_prioritization's un-fixed
# remainder), the SAME should_reopen Program decides EACH gap; the reopened ones are
# passed through to the running session. Python only marshals the deferred set; the
# per-gap DECISION is the graph Program's.
# ===========================================================================
def reopen_deferred(agent, left: list, *, remeasure: bool = False) -> dict:
    """Walk the DEFERRED set (`left` from run_cycle) and, per gap, evaluate the
    should_reopen Program: REOPEN (pass through to the running session) iff its
    CURRENT norm_salience clears the reopen bar, else leave it DEFERRED.

    `remeasure=True` first re-measures each gap's norm_salience via the
    salience_normalize graph Program (boundary I/O) -- use it when the raw salience
    changed and the normalized value must be refreshed before the decision.

    Returns {reopened, concerns, still_deferred}: `reopened` are the gap ids passed
    through, `concerns` the live ReopenedConcern node ids the running loop now sees,
    `still_deferred` the gaps left deferred. The ORDER is marshaling; each gap's
    reopen/defer verdict is the graph Program's."""
    _ensure_seed(agent)
    reopened: list = []
    concerns: list = []
    still: list = []
    for g in left:
        if remeasure:
            remeasure_salience(agent, g)
        if should_reopen(agent, g):
            concerns.append(reopen(agent, g))
            reopened.append(g)
        else:
            still.append(g)
    return {"reopened": reopened, "concerns": concerns, "still_deferred": still}


# ===========================================================================
# LIVE-LOOP VIEW — mechanical reads for verification/the ledger. `active_concerns`
# queries the ReopenedConcern nodes the running loop consumes.
# ===========================================================================
def active_concerns(agent) -> list:
    """The live ReopenedConcern nodes currently active (the running loop's inbox).
    Mechanical read."""
    sub = getattr(agent, "s", agent)
    out = []
    for c in sub.nodes(REOPENED_CONCERN):
        if float(sub.node(c)["attrs"].get("active", 0.0)) > 0.0:
            out.append(c)
    return out


def open_concerns(agent) -> list:
    """The live ReopenedConcern nodes still OPEN (active and NOT yet resolved) -- the
    running loop's UNRESOLVED inbox, which the gated reflex still trips on. Mechanical
    read."""
    sub = getattr(agent, "s", agent)
    out = []
    for c in sub.nodes(REOPENED_CONCERN):
        at = sub.node(c)["attrs"]
        if float(at.get("active", 0.0)) > 0.0 and float(at.get("resolved", 0.0)) <= 0.0:
            out.append(c)
    return out


def resolved_concerns(agent) -> list:
    """The ReopenedConcern nodes the running loop CLEANED (resolved=1). Mechanical
    read for the ledger."""
    sub = getattr(agent, "s", agent)
    return [c for c in sub.nodes(REOPENED_CONCERN)
            if float(sub.node(c)["attrs"].get("resolved", 0.0)) > 0.0]


def concern_view(agent, concerns: list) -> list:
    """Printable view of live concerns: [{gap, kind, faculty, norm_salience,
    pursued}, ...]. Mechanical read-back for the ledger."""
    sub = getattr(agent, "s", agent)
    view = []
    for c in concerns:
        at = sub.node(c)["attrs"]
        view.append({
            "concern": str(c),
            "gap": at.get("gap"),
            "kind": at.get("kind"),
            "faculty": at.get("faculty"),
            "norm_salience": at.get("norm_salience"),
            "pursued": at.get("pursued"),
            "resolved": at.get("resolved"),
        })
    return view


# ===========================================================================
# POLICY read/tune — the reopen threshold is graph data (a stated POLICY), DISTINCT
# from the sufficiency threshold (hysteresis). Reading/writing it is boundary I/O.
# ===========================================================================
def _policy_node(agent) -> Optional[Any]:
    sub = getattr(agent, "s", agent)
    for n in sub.nodes("ReopenPolicy"):
        return n
    return None


def reopen_threshold(agent) -> Optional[float]:
    """Read the current reopen threshold off the ReopenPolicy node (graph data).
    Mechanical read for the ledger."""
    _ensure_seed(agent)
    sub = getattr(agent, "s", agent)
    n = _policy_node(agent)
    if n is None:
        return None
    try:
        return float(sub.node(n)["attrs"].get("threshold"))
    except Exception:
        return None


def set_reopen_threshold(agent, threshold: float) -> None:
    """Tune the reopen POLICY: write the ReopenPolicy node's threshold attr (graph
    data). Keep it >= the sufficiency threshold to preserve the hysteresis dead-band.
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
    "REOPENED_CONCERN", "HAS_CONCERN", "TARGETS_GAP", "REOPEN_REFLEX",
    "remeasure_salience", "should_reopen", "reopen", "reopen_deferred",
    "active_concerns", "open_concerns", "resolved_concerns", "concern_view",
    "reopen_threshold", "set_reopen_threshold",
    "_reopened_concern_pursue_advance", "_ensure_seed",
]
