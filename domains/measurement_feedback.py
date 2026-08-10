"""measurement_feedback — the autopoietic loop's measurement FEEDS BACK into the
gap-graph, so the agent's own ranker re-points itself.

THE PROBLEM this closes (iteration 1's honest residual). The agent picked
cross-speaker clustering by its a-priori compression-payoff (payoff 6 vs LPC's 2),
built it, and MEASURED it CAPPED by the blurry front-end: label-free purity 0.441 <
raw-spectrum 0.483 (did not beat baseline), mirroring the sound-graph LOSO filter
0.335 << spectrum 0.649. The orchestrator OBSERVED that this points at the LPC /
front-end gap — but nothing in the GRAPH recorded it, so the agent's own ranker
could never re-pick. The loop self-corrected only in the human's notes, not in the
agent's reality. This module makes the self-correction REAL: it encodes the capped
measurement as graph state the ranking Term reads, and EXTENDS that Term so a gap
which UNBLOCKS a high-payoff gap inherits its payoff.

THE FEEDBACK (world<->graph adapter role — the permitted Python: translate an
external measurement RESULT into substrate mutations, NO decision over graph state):

  1. record_outcome — mint a MeasurementOutcome node carrying the empirical result
     the probe produced (what was attempted, its gain vs baseline, and — when the
     gain is non-positive and the probe attributes the cap to the front-end — which
     capability axis it is BLOCKED_BY). This is pure I/O translation: the probe
     computed the numbers; this writes them as a node + a `blocked_by` edge from the
     capped axis to the axis that would unblock it.

  2. the ranking Term is EXTENDED (domains/gap_prioritiser via the constructors
     below) so an axis's EFFECTIVE payoff = its own payoff PLUS the payoff of every
     axis it unblocks (the axes with an incoming `blocked_by` edge to it). Still a
     graph Term-tree (Plus / Sum / InNeighbours / Count / Neighbours / Times / Minus
     / Argmax) — no new primitive; InNeighbours, Sum, Plus all verified in term.rs.

So after the feedback, LPC's effective payoff = its own 2 + clustering's 6 (LPC
unblocks clustering) = 8 > clustering's own 6 — IF the measurement genuinely wrote
the blocked_by edge. Whether that makes LPC WIN is then the agent's Term's verdict,
not ours: the self-correction test. We encode the evidence; the graph re-ranks.

WHY blocked_by is evidence, not a decision. The probe's OWN verdict branch (purity
above random but NOT above the spectrum baseline) IS the cap-attribution: the
clusterer works, the front-end limits it. record_outcome reads that branch's result
(a number comparison the probe already made) and translates it to an edge. There is
no conditional here that decides what the agent should pursue — the Argmax over the
EXTENDED score Term does, natively. This is the same I/O role build_axis_env plays.

See gap_prioritiser (the base ranking Term), cross_speaker_clustering (the capped
build), sound_graph (the front-end the LPC gap improves), [[ozma_concepts_in_gamma]]
/ [[ozma_self_measurement_compresses_research]] / [[ozma_curiosity_drive]].
"""
from __future__ import annotations

from domains import gap_prioritiser as gp
from domains.gap_prioritiser import (AXIS_TYPE, AXIS_FLAG, UNIFIES_EDGE,
                                     ORDER_ATTR, ORDER_K, _Pred,
                                     _V, _Lit, _Attr, _Nb, _Count, _Times,
                                     _Minus, _Argmax, _NodesWhere, payoff_term)

# axis -> axis: "I am blocked_by THAT axis" (THAT axis must close first). The
# measurement writes it; the ranker reads its INCOMING form to find what an axis
# unblocks.
BLOCKED_BY_EDGE = "blocked_by"
OUTCOME_TYPE = "MeasurementOutcome"
# The "attempted -> diminishing -> move on" signal the loop lacked (iteration 3).
# An axis that was BUILT and MEASURED, did NOT beat baseline, AND whose blocker (if
# any) is already closed, has nothing more the loop can extract by re-picking it. The
# measurement writes attempted_marginal=1 on the axis; the ranking Term subtracts a
# dominating penalty so the Argmax advances to the next UN-exhausted gap. Without this
# the ranker re-picks the same already-built gap forever (verified live, iter-3 doc).
ATTEMPTED_MARGINAL_ATTR = "attempted_marginal"
EXHAUST_PENALTY = ORDER_K * 1000   # dominates payoff*K so an exhausted axis sinks


# ---------------------------------------------------------------------------
# Graph-resident Term constructors — the EXTENDED ranking (the agent's reasoning,
# evaluated natively). Adds the unblock-inheritance to gap_prioritiser's base
# payoff/score, keeping everything a Term-tree.
# ---------------------------------------------------------------------------

def _InNb(node, e):
    return {"type": "InNeighbours", "node": node, "edge_type": e, "any_type": False}


def _Sum(source, var, value):
    return {"type": "Sum", "source": source, "var_name": var, "value": value}


def _Plus(items):
    return {"type": "Plus", "items": list(items)}


def unblock_bonus_term(axis_var: str = "x") -> dict:
    """Σ over the axes THIS axis unblocks (its incoming `blocked_by` neighbours) of
    each blocked axis's own payoff. = how much down-stream compression closing this
    axis would release. A graph Term-tree (Sum / InNeighbours / Count / Neighbours).

      bonus(axis) = Σ_{a : a blocked_by axis}  Count(Neighbours(a, "unifies"))
    """
    blocked = _InNb(_V(axis_var), BLOCKED_BY_EDGE)
    return _Sum(blocked, "a", _Count(_Nb(_V("a"), UNIFIES_EDGE)))


def effective_payoff_term(axis_var: str = "x") -> dict:
    """own payoff + unblock bonus — the compression an axis discharges DIRECTLY plus
    the compression it RELEASES by unblocking others. A graph Term-tree."""
    return _Plus([payoff_term(axis_var), unblock_bonus_term(axis_var)])


def exhaust_penalty_term(axis_var: str = "x",
                         penalty: int = EXHAUST_PENALTY) -> dict:
    """attempted_marginal * PENALTY — a dominating cost for an axis the loop already
    BUILT + MEASURED with no payoff and no open unblocking path. attempted_marginal
    is 0 (unset) for every fresh axis, so this term is a no-op for them; for an
    exhausted axis it subtracts PENALTY (>> payoff*K), sinking it below every
    un-attempted gap. A graph Term-tree — the move-on DECISION lives in the Term."""
    return _Times([_Attr(_V(axis_var), ATTEMPTED_MARGINAL_ATTR), _Lit(penalty)])


def effective_score_term(axis_var: str = "x", k: int = ORDER_K) -> dict:
    """effective_payoff * K - min_order - exhaust_penalty — the base score Term with
    own-payoff replaced by EFFECTIVE payoff (own + unblocked), MINUS the
    attempted-marginal penalty so an already-built-and-exhausted axis drops out of
    the running. Same scalar shape; the shallower-order tie-break still only breaks
    ties among live axes. A graph Term-tree."""
    return _Minus(
        _Minus(_Times([effective_payoff_term(axis_var), _Lit(k)]),
               _Attr(_V(axis_var), ORDER_ATTR)),
        exhaust_penalty_term(axis_var))


def effective_pick_term(k: int = ORDER_K) -> dict:
    """pick = Argmax over the CapabilityAxis nodes of EFFECTIVE score. The whole
    re-ranking DECISION with measurement feedback folded in, as a Term the agent
    owns and evaluates natively."""
    return _Argmax(_NodesWhere(AXIS_TYPE, AXIS_FLAG, _Lit(1.0)), "x",
                   effective_score_term("x", k))


# ---------------------------------------------------------------------------
# The FEEDBACK adapter — translate a measurement RESULT into graph state. Pure
# world<->graph I/O: the probe computed the numbers + made the comparison; this
# only writes them as a node + a blocked_by edge. No decision over graph state.
# ---------------------------------------------------------------------------

def _find_axis(substrate, key_substr: str):
    """Locate the CapabilityAxis whose capability_keys contain a substring (e.g.
    'cross-speaker-clustering', 'all-pole'). Mechanical lookup over the axes
    build_axis_env minted — no decision."""
    key = key_substr.lower()
    for ax in substrate.nodes(AXIS_TYPE):
        a = substrate.node(ax)["attrs"]
        keys = [str(x).lower() for x in a.get("capability_keys", [])]
        if any(key in kk for kk in keys):
            return ax
    return None


def _mint_blocker_axis(substrate, key: str, capability_keys, grounded_in,
                       min_order: int = 1):
    """Mint a CapabilityAxis the MEASUREMENT implicates as the blocker, when the
    a-priori synthesis did not produce it. This is I/O translation of an EMPIRICAL
    result: the measurement is direct evidence the gap is real (stronger evidence
    than the a-priori unification count), and it NAMES the blocker (the front-end /
    LPC). The axis is grounded by `unifies` edges to the held postulate Concepts the
    measurement attributes the block to, so its OWN payoff is the real count of those
    postulates — not invented. Returns the axis id.

    HONESTY (flagged in the node's `provenance`): this axis is measurement-derived,
    NOT order-N-synthesised. See the iteration-2 doc — at the current tree the
    harvested all-pole shape does not fire on source_filter_theory, so the LPC axis
    is absent from the synthesis; the measurement supplies it instead."""
    ax = substrate.add_node(AXIS_TYPE, {
        AXIS_FLAG: 1.0,
        "axis_sig": sorted({str(k).lower() for k in capability_keys}),
        "capability_keys": list(capability_keys),
        "attempted_marginal": 0.0,
        ORDER_ATTR: float(min_order),
        "gap_text": f"front-end capability the measurement implicates: {key}",
        "origin": "measurement_feedback",
        "provenance": "measurement_derived_axis (NOT order_n synthesised)",
        "composed_by": "world_adapter",
    })
    try:
        substrate.add_production({
            "src": {"type": AXIS_TYPE, "var": "a"}, "edge_type": UNIFIES_EDGE,
            "tgt": {"type": "Concept", "var": "b"},
            "provenance": "measurement_feedback:unifies"})
    except Exception:
        pass
    for cname in grounded_in:
        for c in substrate.nodes("Concept"):
            if substrate.node(c)["attrs"].get("name") == cname:
                try:
                    substrate.add_edge(ax, UNIFIES_EDGE, c, {})
                except Exception:
                    pass
                break
    return ax


def record_outcome(substrate, *, attempted_key: str, blocked_by_key: str,
                   gain_vs_baseline: float, baseline: float, achieved: float,
                   floor: float, metric: str, attribution: str,
                   blocker_capability_keys=None, blocker_grounded_in=None) -> dict:
    """Translate the iteration's measurement result into the gap-graph.

    Writes a MeasurementOutcome node (the empirical record) and — because the probe
    reported a NON-POSITIVE gain attributed to the front-end — a `blocked_by` edge
    from the attempted axis to the axis that would unblock it. Idempotent on the
    (attempted, blocked_by) pair. Returns {outcome, attempted_axis, blocking_axis,
    edge_written}.

    The numbers/comparison are the PROBE's (it already decided 'works but capped');
    this is the mechanical write-back, the world adapter's job."""
    gp.build_axis_env(substrate)   # ensure the axes exist to attach to (mechanical)
    attempted = _find_axis(substrate, attempted_key)
    blocking = _find_axis(substrate, blocked_by_key)
    # If the synthesis did not produce the blocker the measurement names, mint it
    # from the measurement evidence (flagged measurement_derived; grounded in the
    # held postulates the block is attributed to).
    minted_blocker = False
    if blocking is None and blocker_capability_keys:
        blocking = _mint_blocker_axis(
            substrate, blocked_by_key, blocker_capability_keys,
            blocker_grounded_in or [])
        minted_blocker = True

    outcome = substrate.add_node(OUTCOME_TYPE, {
        "attempted_key": attempted_key,
        "blocked_by_key": blocked_by_key,
        "metric": metric,
        "achieved": float(achieved),
        "baseline": float(baseline),
        "floor": float(floor),
        "gain_vs_baseline": float(gain_vs_baseline),
        "works_above_floor": bool(achieved > floor),
        "beats_baseline": bool(gain_vs_baseline > 0.0),
        "attribution": attribution,
        "origin": "measurement_feedback",
        "composed_by": "world_adapter",
    })

    edge_written = False
    if attempted is not None and blocking is not None and gain_vs_baseline <= 0.0:
        # admissible edge: axis -> axis (the precondition relation).
        try:
            substrate.add_production({
                "src": {"type": AXIS_TYPE, "var": "a"},
                "edge_type": BLOCKED_BY_EDGE,
                "tgt": {"type": AXIS_TYPE, "var": "b"},
                "provenance": "measurement_feedback:blocked_by"})
        except Exception:
            pass
        already = blocking in substrate.neighbours(attempted, BLOCKED_BY_EDGE)
        if not already:
            try:
                substrate.add_edge(attempted, BLOCKED_BY_EDGE, blocking, {})
                edge_written = True
            except Exception:
                edge_written = False
        # link the outcome to the axes it concerns (provenance, not a decision).
        for ed, tgt in (("about_axis", attempted), ("implicates_axis", blocking)):
            try:
                substrate.add_production({
                    "src": {"type": OUTCOME_TYPE, "var": "a"}, "edge_type": ed,
                    "tgt": {"type": AXIS_TYPE, "var": "b"},
                    "provenance": f"measurement_feedback:{ed}"})
                substrate.add_edge(outcome, ed, tgt, {})
            except Exception:
                pass

    return {"outcome": outcome, "attempted_axis": attempted,
            "blocking_axis": blocking, "edge_written": edge_written,
            "minted_blocker": minted_blocker}


def mark_attempted_marginal(substrate, *, attempted_key: str, achieved: float,
                            baseline: float, floor: float, n_attempts: int,
                            metric: str, note: str) -> dict:
    """The "attempted -> diminishing -> move on" write-back (iteration 3's loop-gap
    fix). When an axis was BUILT and MEASURED across one-or-more iterations, runs
    above floor but does NOT beat baseline, and has no OPEN unblocking path left
    (its blocker, if any, is already closed), there is nothing more the loop can
    extract by re-picking it. This sets attempted_marginal=1 on the axis so the
    ranking Term's exhaust-penalty sinks it below the next un-attempted gap.

    This is the same world<->graph I/O role record_outcome plays: the probe already
    computed 'built, ran, did not beat baseline across N attempts'; this translates
    that to the move-on attr + a MeasurementOutcome record. The DECISION to advance
    is the Argmax over the penalised score Term, not Python. Returns the axis id."""
    gp.build_axis_env(substrate)
    ax = _find_axis(substrate, attempted_key)
    out = substrate.add_node(OUTCOME_TYPE, {
        "attempted_key": attempted_key, "metric": metric,
        "achieved": float(achieved), "baseline": float(baseline),
        "floor": float(floor), "n_attempts": int(n_attempts),
        "works_above_floor": bool(achieved > floor),
        "beats_baseline": bool(achieved > baseline),
        "verdict": "attempted_marginal_move_on", "note": note,
        "origin": "measurement_feedback", "composed_by": "world_adapter",
    })
    if ax is not None:
        substrate.set_attr(ax, ATTEMPTED_MARGINAL_ATTR, 1.0)
        try:
            substrate.add_production({
                "src": {"type": OUTCOME_TYPE, "var": "a"},
                "edge_type": "about_axis",
                "tgt": {"type": AXIS_TYPE, "var": "b"},
                "provenance": "measurement_feedback:about_axis"})
            substrate.add_edge(out, "about_axis", ax, {})
        except Exception:
            pass
    return {"outcome": out, "axis": ax}


# ---------------------------------------------------------------------------
# Re-rank with the feedback (native Term evaluation) + enact the new pick.
# ---------------------------------------------------------------------------

def rerank_with_feedback(substrate, k: int = ORDER_K) -> list[dict]:
    """Rank every CapabilityAxis by the EXTENDED score Term (own + unblocked payoff),
    evaluated natively (substrate.evaluate — the agent's reality), best first. Reports
    own_payoff, unblock_bonus, effective_payoff, effective_score per axis so the
    re-direction is auditable. Numbers come out of the graph Term, not Python."""
    gp.build_axis_env(substrate)
    rows = []
    for ax in substrate.nodes(AXIS_TYPE):
        if substrate.node(ax)["attrs"].get(AXIS_FLAG) != 1.0:
            continue
        a = substrate.node(ax)["attrs"]
        own = int(substrate.evaluate(_Pred(payoff_term("x")), {"x": ax}))
        bonus = int(substrate.evaluate(_Pred(unblock_bonus_term("x")), {"x": ax}))
        eff = int(substrate.evaluate(_Pred(effective_payoff_term("x")), {"x": ax}))
        score = int(substrate.evaluate(_Pred(effective_score_term("x", k)),
                                       {"x": ax}))
        rows.append({
            "capability_keys": list(a.get("capability_keys", [])),
            "own_payoff": own, "unblock_bonus": bonus,
            "effective_payoff": eff, "min_order": int(a.get(ORDER_ATTR, 99)),
            "effective_score": score, "axis_id": ax,
        })
    rows.sort(key=lambda r: -r["effective_score"])
    return rows


def pick_with_feedback(substrate, k: int = ORDER_K) -> dict | None:
    """Enact the re-ranked PICK in the graph: install a Rule whose effect evaluates
    the EXTENDED Argmax Term natively and writes the winner onto a FrontierRoot, fire
    it, read the chosen axis back, record a FrontierChoice (origin=measurement_feedback).
    The DECISION is the Term the Rule evaluates — Python only fires it + reads back."""
    nat = substrate._inner if hasattr(substrate, "_inner") else substrate
    rows = rerank_with_feedback(substrate, k)
    if not rows:
        return None
    root = next((n for n in substrate.nodes("FrontierRoot")), None)
    if root is None:
        root = substrate.add_node("FrontierRoot",
                                  {"origin": "measurement_feedback", "pick_pending": 1})
    else:
        substrate.set_attr(root, "pick_pending", 1)
    try:
        substrate.add_production({
            "src": {"type": "FrontierRoot", "var": "a"}, "edge_type": "self",
            "tgt": {"type": "FrontierRoot", "var": "b"},
            "provenance": "measurement_feedback:self"})
        substrate.add_edge(root, "self", root, {})
    except Exception:
        pass
    rule = {
        "name": "pick_frontier_gap_with_feedback",
        "match": [["R", "self", "R"]],
        "where": _Lit(True),
        "effects": [
            ["set_attr", "R", "picked_axis", {"__term__": effective_pick_term(k)}],
            ["set_attr", "R", "pick_pending", 0],
        ],
    }
    ri = nat.add_rule(rule)
    for _ in range(8):
        if substrate.node(root)["attrs"].get("pick_pending") != 1:
            break
        nat.apply_rule_once(ri)
    picked = substrate.node(root)["attrs"].get("picked_axis")
    if picked is None:
        return None
    win = next((r for r in rows if r["axis_id"] == picked), rows[0])
    runner = next((r for r in rows if r["axis_id"] != picked), None)
    out = dict(win)
    out["criterion"] = ("EFFECTIVE compression payoff = own payoff + payoff of every "
                        "axis this one UNBLOCKS (incoming blocked_by edges written "
                        "from the capped measurement); pick = Argmax over "
                        "CapabilityAxis of effective_payoff*K - order — a graph Term")
    out["runner_up_keys"] = runner["capability_keys"] if runner else []
    out["runner_up_score"] = runner["effective_score"] if runner else 0
    try:
        substrate.add_node("FrontierChoice", {
            "origin": "measurement_feedback",
            "criterion": out["criterion"],
            "capability_keys": list(out["capability_keys"]),
            "own_payoff": out["own_payoff"], "unblock_bonus": out["unblock_bonus"],
            "effective_payoff": out["effective_payoff"],
            "effective_score": out["effective_score"],
            "picked_axis": picked, "composed_by": "agent",
            "decision_in": "graph_term",
        })
    except Exception:
        pass
    return out


__all__ = ["BLOCKED_BY_EDGE", "OUTCOME_TYPE", "ATTEMPTED_MARGINAL_ATTR",
           "unblock_bonus_term", "effective_payoff_term", "exhaust_penalty_term",
           "effective_score_term", "effective_pick_term",
           "record_outcome", "mark_attempted_marginal",
           "rerank_with_feedback", "pick_with_feedback"]
