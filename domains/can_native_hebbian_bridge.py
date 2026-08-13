"""Native Hebbian bridge — thin, mechanical query layer over the graded
coupling-strength signal seeds/can_native_reimplementation.json's own
mint-on-recurrence + reweight rules already materialize (evidence_confirm/
evidence_disconfirm/evidence_tick integers on the Coactivation ledger node,
LOGODDS_GENERATOR_RESULTS.md).

CAN_HEBBIAN_MATERIALIZATION_PREREG.md / _RESULTS.md: mt_hebbian_update_J's
three Python callers (domains/insight_detection.py::consolidate_insight,
domains/insight_propagation.py::propagate_insight,
domains/self_improvement_loop.py::maybe_hebbian) never read a stored weight
value back — every one of them only ever consumes the RETURNED edge count,
for truthy control flow ("did anything change, should I re-relax") and
telemetry. This module gives a future, coordinated migration rung (NOT this
one — editing those three files is explicitly out of scope here) a drop-in
analog: a mechanical count of Coactivation ledger entries touched this tick
(the native return-value equivalent of "edges updated") and an on-demand
log-odds render (the native graded-strength read, evaluated fresh, per
LOGODDS_GENERATOR_RESULTS.md Sec2's own proven "never write the render back"
pattern — the frame/continuum invariant: the render is a CROSS-FRAME
comparison, the evidence counts are the only IN-frame stored state).

Every function here is a pure query or a pure render over ALREADY-DECODED
graph state — no `if`/`else` deciding what to mutate, matching the
world-adapter "Emit" role CLAUDE.md carves out. The actual decision of
WHETHER to mint/reweight (the policy gate) lives in the graph, in
seeds/can_native_reimplementation.json's own
Or(mt_allows-equivalent-switch, plasticity_override>0) predicate on
can_native_hebbian_mint/can_native_hebbian_reweight — this module never
re-implements or overrides that gate; it only reads what the gate already
decided.
"""
from __future__ import annotations

from typing import Any


def _log_odds_term() -> dict:
    """Log(Div(Plus(evidence_confirm,1), Plus(evidence_disconfirm,1))) —
    the SAME Laplace-smoothed empirical log-odds formula
    LOGODDS_GENERATOR_RESULTS.md Sec2 registered and
    tests/test_can_native_reimplementation.py's own _log_odds_term()
    builds, reproduced here as a plain dict Term (the domains/ convention:
    no domains/*.py imports substrate_rs.Term; every one composes
    JSON-shaped dict Terms directly) so callers outside the test suite can
    reuse the formula without re-deriving it."""
    return {
        "type": "Log",
        "arg": {
            "type": "Div",
            "a": {"type": "Plus", "items": [
                {"type": "Attr", "node": {"type": "Var", "name": "coact"},
                 "key": "evidence_confirm"},
                {"type": "Lit", "value": 1},
            ]},
            "b": {"type": "Plus", "items": [
                {"type": "Attr", "node": {"type": "Var", "name": "coact"},
                 "key": "evidence_disconfirm"},
                {"type": "Lit", "value": 1},
            ]},
        },
    }


def find_coactivation(substrate, a, b) -> Any | None:
    """Mechanical traversal for the Coactivation ledger node anchoring the
    a->b evidence record — the SAME a-coactivated_with->coact-
    coactivation_of->b walk can_native_hebbian_mint/can_native_hebbian_
    reweight's own match pattern uses. Pure query; returns None if no
    co-activation has ever been noted for this ordered pair. Ledgers are
    tracked PER-DIRECTION (LOGODDS_GENERATOR_RESULTS.md Sec7 point 5,
    unchanged here) — find_coactivation(s, a, b) and
    find_coactivation(s, b, a) are two distinct nodes once both have
    fired."""
    for co in substrate.neighbours(a, "coactivated_with"):
        if b in substrate.neighbours(co, "coactivation_of"):
            return co
    return None


def causal_strength(substrate, coact) -> float:
    """On-demand cross-frame log-odds render for one Coactivation ledger
    node — evaluated live via Substrate.evaluate, NEVER stored on any node
    (frame/continuum invariant, LOGODDS_GENERATOR_RESULTS.md Sec2/Sec4(b),
    unmodified here). Positive = net confirming evidence, negative = net
    disconfirming, 0.0 = no evidence either way."""
    return float(substrate.evaluate(_log_odds_term(), {"coact": coact}))


def causal_strength_between(substrate, a, b) -> float | None:
    """causal_strength for the pair's own (a->b) Coactivation ledger, or
    None if the pair has never co-activated (no ledger exists yet)."""
    coact = find_coactivation(substrate, a, b)
    if coact is None:
        return None
    return causal_strength(substrate, coact)


def hebbian_signal(substrate, a, b) -> dict[str, Any] | None:
    """The full native-analog signal for one direction of a pair,
    mirroring what a caller of the continuous mt_hebbian_update_J might
    want to inspect: whether the causal_influence edge exists, the raw
    in-frame evidence counts, and the on-demand graded render. Returns
    None if no co-activation ledger exists for this direction at all
    (never co-activated)."""
    coact = find_coactivation(substrate, a, b)
    if coact is None:
        return None
    attrs = substrate.node(coact)["attrs"]
    edge_exists = b in substrate.neighbours(a, "causal_influence")
    return {
        "edge_exists": edge_exists,
        "evidence_confirm": int(attrs["evidence_confirm"]),
        "evidence_disconfirm": int(attrs["evidence_disconfirm"]),
        "evidence_tick": int(attrs["evidence_tick"]),
        "causal_strength": causal_strength(substrate, coact),
    }


def hebbian_ledger_entries_touched_this_tick(substrate, mt) -> int:
    """Mechanical count of this Mt's Coactivation ledger entries (one per
    direction per co-activated pair, per-direction convention unchanged)
    that were genuinely MINTED-INTO or REWEIGHTED this tick — the native
    drop-in analog of mt_hebbian_update_J's own returned "edges updated"
    int, which every one of its three Python callers (confirmed by direct
    read) uses ONLY as a truthy/count control-flow + telemetry signal,
    never as a stored coupling-strength value (CAN_HEBBIAN_
    MATERIALIZATION_PREREG.md Sec1 / _RESULTS.md Sec1).

    A ledger entry counts iff evidence_tick == the Mt's current can_tick
    AND it carries at least one unit of evidence (evidence_confirm +
    evidence_disconfirm > 0). The second clause is load-bearing, not
    decorative: can_native_note_coactivation initialises a FRESH ledger
    with evidence_tick == mt.can_tick == the tick it was first noted on
    (both counters still 0) -- without the evidence>0 clause, a pair's
    very first sighting would look identical to a real mint/reweight
    event on the SAME tick it happened to be noted. Requiring nonzero
    evidence is a pure re-read of what the mint/reweight rules already
    wrote (they are the only effects that ever increment either counter);
    this function never decides anything, it only counts what the
    graph's own (policy-gated) rules already did.

    A pure query over already-decoded ledger state — the mint/reweight
    RULES alone decide whether evidence_tick advances (policy-gated in
    the graph, per seeds/can_native_reimplementation.json's own Or(...)
    predicate)."""
    current_tick = substrate.node(mt)["attrs"].get("can_tick")
    if current_tick is None:
        return 0
    touched = 0
    for c in substrate.neighbours(mt, "has_concept"):
        for co in substrate.neighbours(c, "coactivated_with"):
            attrs = substrate.node(co)["attrs"]
            if attrs.get("evidence_tick") != current_tick:
                continue
            if int(attrs.get("evidence_confirm", 0)) + int(attrs.get("evidence_disconfirm", 0)) > 0:
                touched += 1
    return touched


__all__ = [
    "find_coactivation",
    "causal_strength",
    "causal_strength_between",
    "hebbian_signal",
    "hebbian_ledger_entries_touched_this_tick",
]
