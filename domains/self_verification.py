"""self_verification — the NOT-FOOLING-ITSELF faculty.

THE DISCIPLINE, MADE INTERNAL. Every fix in this session was guarded by hand:
build a DISCRIMINATIVE CONTROL (a case that fails if the fix is fake/overfit),
check NO-REGRESSION, and trust the result only if it is GROUNDED (its support
reaches an external anchor, not a confident ungrounded basin). Concrete
examples the developer enforced by hand: the "game_theory stays anchored"
control that proved a degree-normalization was real structure and not a tuned
threshold; refusing to inflate microtheory tokens to force a pass; refusing a
de-shadow fix that would flip a control. This module makes that discipline the
agent's OWN internal reflex, so when the self-improvement loop proposes a fix,
the agent catches itself fooling itself BEFORE accepting.

WHAT THIS IS. Given a CLAIM (a proposed change + its claimed measurable
effect, as a graph node), the faculty:

  1. MINTS A DISCRIMINATIVE CONTROL — a `ControlProbe` node: the adversarial /
     held-out / ambiguous case the claim must SURVIVE. The probe is
     constructed so that a FAKE/overfit claim fails it (or the probe fails to
     discriminate). Discrimination is measured the way collapse_engine's
     SHUFFLE-CONTROL proves real sequential structure: run the control on the
     claimed mechanism (must PASS) AND on a KNOWN-FAKE twin (must FAIL). A
     control the fake also passes has no teeth — it does not discriminate.

  2. CHECKS NO-REGRESSION — the claim's mechanism must still hold on the
     previously-holding cases.

  3. GATES ON GROUNDING-REACHABILITY — via domains/grounding_reach (the REAL
     agent-installed `ReachableFrom(node,'grounded_in')` Term): the claim's
     support must reach an external anchor (Sensor/Teacher/Consequence/
     Reality). A low-residual, confident, but UNGROUNDED basin is exactly the
     confidently-wrong shape residual alone can't see (seeds/grounding_anchors
     .json), so it is rejected even when it "looks right".

  ACCEPT iff the control DISCRIMINATES (would fail if the claim were fake) AND
  no-regression AND grounded. Else REJECT with the reason.

WHAT IS GRAPH-NATIVE (the decision). The accept/reject is NOT a Python
if/else. The host mints the Claim + ControlProbe nodes and RUNS the probe (the
measurement INSTRUMENT — the same admissible host role native_collapse.py
draws: reading a measurement is the experimenter's instrument, not the agent's
cognition). It writes the measured facts onto the graph nodes as attrs. The
DECISION is then a graph-resident `Rule` over the `Claim -has_control->
ControlProbe` join whose `where`/effect Term-tree ANDs the three gates and
writes `verdict` — evaluated by `substrate.tick()` IN RUST (term.rs `And`/
`Not`/`Gt`/`IfThenElse`). Python reads `verdict` back and assembles the reason
string mechanically from the Rust-computed gate attrs; it never re-decides.

HONEST SCOPE. This verifies claims whose control it can CONSTRUCT and RUN —
behavioral / measurable claims (a classifier holds on a held-out item; a fix
keeps an anchored node anchored; a saturated axis is or isn't grounded). It is
NOT a general theorem-prover: a claim whose control cannot be run cannot be
verified, and a control with no discriminative power is rejected as such
(vacuous control => not discriminating => reject), never waved through.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Sequence

from domains.grounding_reach import ensure_grounding_edges, grounding_reach

# The one rule id the verdict gate installs (idempotent — one per substrate).
_GATE_RULE_ID = "self_verify_gate"


# ---------------------------------------------------------------------------
# resolve (substrate, native) — the same duck typing grounding_reach.py uses,
# kept local so this module carries no coupling to files under concurrent edit.
# ---------------------------------------------------------------------------
def _resolve(agent):
    sub = getattr(agent, "s", agent)
    native = getattr(agent, "inner", None)
    if native is None:
        native = getattr(sub, "_inner", sub)
    return sub, native


def _add_edge_unchecked(native, src, edge_type, tgt) -> None:
    try:
        native.add_edge_unchecked(src, edge_type, tgt)
    except TypeError:
        native.add_edge_unchecked(src, edge_type, tgt, {})


# ---------------------------------------------------------------------------
# THE CLAIM the faculty verifies. A claim is submitted with a runnable control:
# the mechanism (the proposed fix, as a case->pass callable), the discriminative
# control cases it must survive, and a KNOWN-FAKE twin used to prove the control
# has teeth. ground_support builds the claim's support subgraph and returns the
# node whose grounding is checked (None => ungrounded, which the gate rejects).
# ---------------------------------------------------------------------------
@dataclass
class Claim:
    text: str
    mechanism: Callable[[Any], bool]            # the proposed fix: case -> passes?
    control_cases: Sequence[Any]                # held-out / adversarial / ambiguous
    fake_twin: Callable[[Any], bool]            # a KNOWN-FAKE mechanism (proves teeth)
    prior_cases: Sequence[Any] = field(default_factory=tuple)  # no-regression set
    ground_support: Optional[Callable[[Any], Any]] = None      # (sub) -> support node


# ---------------------------------------------------------------------------
# TERM-DICT builders — the verdict gate as graph-resident term-trees (the JSON
# term form a Rule node carries; NOT substrate_rs.Term objects). Every boolean
# reads an attr coerced through Plus(attr, 0) so a missing attr never errors.
# ---------------------------------------------------------------------------
def _attr(var: str, key: str) -> dict:
    return {"type": "Attr", "node": {"type": "Var", "name": var}, "key": key}


def _bool(var: str, key: str) -> dict:
    """attr > 0.5  — the graph-native truthiness of a 1.0/0.0 flag."""
    return {"type": "Gt",
            "a": {"type": "Plus", "items": [_attr(var, key), {"type": "Lit", "value": 0}]},
            "b": {"type": "Lit", "value": 0.5}}


def _ite(cond: dict, then_v: float, other_v: float) -> dict:
    return {"type": "IfThenElse", "cond": cond,
            "then": {"type": "Lit", "value": then_v},
            "other": {"type": "Lit", "value": other_v}}


# discriminates = real_pass AND NOT twin_pass  (control separates real from fake)
_DISCRIMINATES = {"type": "And", "items": [
    _bool("probe", "real_pass"),
    {"type": "Not", "arg": _bool("probe", "twin_pass")},
]}
# the full verdict: discriminates AND no_regression AND grounded, all in Rust.
_VERDICT_COND = {"type": "And", "items": [
    _DISCRIMINATES,
    _bool("claim", "no_regression"),
    _bool("claim", "grounded"),
]}


def _ensure_gate_rule(sub, native):
    """Install the verdict gate as a graph-resident Rule ONCE (idempotent by
    id). The Rule matches every `Claim -has_control-> ControlProbe` join and
    writes the Rust-computed gate booleans + `verdict` onto the Claim. The
    DECISION lives in this term-tree, fired by tick() — not in Python."""
    rule_node = None
    for r in sub.nodes("Rule"):
        if sub.node(r)["attrs"].get("id") == _GATE_RULE_ID:
            rule_node = r
            break
    if rule_node is None:
        rule_node = sub.add_node("Rule", {
            "id": _GATE_RULE_ID,
            "match": [["claim", "has_control", "probe"]],
            "where": None,
            "effect": [
                ["set_attr", "claim", "g_discriminates", {"__term__": _ite(_DISCRIMINATES, 1.0, 0.0)}],
                ["set_attr", "claim", "g_no_regression", {"__term__": _ite(_bool("claim", "no_regression"), 1.0, 0.0)}],
                ["set_attr", "claim", "g_grounded", {"__term__": _ite(_bool("claim", "grounded"), 1.0, 0.0)}],
                ["set_attr", "claim", "verdict", {"__term__": _ite(_VERDICT_COND, 1.0, 0.0)}],
            ],
        })

    # A graph-resident Rule is not automatically part of the native rewrite
    # vector. Register the verdict rule explicitly, translating the graph
    # schema's singular `effect` field to add_rule's `effects` argument. Without
    # this bridge, WorldAdapter.tick() has no gate to execute and the missing
    # g_* attrs read back as false even when the measured controls all pass.
    registered = any(
        row.get("name") == _GATE_RULE_ID
        for row in native.export_rules()
        if isinstance(row, dict)
    )
    if not registered:
        attrs = sub.node(rule_node)["attrs"]
        native.add_rule({
            "name": _GATE_RULE_ID,
            "match": attrs.get("match", []),
            "where": attrs.get("where"),
            "effects": attrs.get("effect", []),
        })
    return rule_node


# ---------------------------------------------------------------------------
# THE FACULTY — mint Claim + ControlProbe, RUN the probe (instrument), GATE in
# Rust. Returns the verdict + a mechanically-assembled reason (read back from
# the Rust-computed gate attrs; no Python re-decision).
# ---------------------------------------------------------------------------
def verify_claim(agent, claim: Claim) -> dict[str, Any]:
    sub, native = _resolve(agent)

    # 1. MINT the Claim + its discriminative ControlProbe as graph nodes.
    claim_node = sub.add_node("VClaim", {"text": claim.text})
    n_ctrl = len(list(claim.control_cases))
    probe = sub.add_node("ControlProbe", {
        "n_control_cases": float(n_ctrl),
        "n_prior_cases": float(len(list(claim.prior_cases))),
    })
    _add_edge_unchecked(native, claim_node, "has_control", probe)

    # 2. RUN the probe — the measurement INSTRUMENT (admissible host role).
    #    real_pass : the claimed mechanism SURVIVES every control case.
    #    twin_pass : a KNOWN-FAKE twin ALSO survives — if so the control has no
    #                teeth (does not discriminate). A vacuous control (no cases)
    #                makes twin_pass vacuously True => not discriminating.
    real_pass = 1.0 if (n_ctrl > 0 and all(bool(claim.mechanism(c)) for c in claim.control_cases)) else 0.0
    twin_pass = 1.0 if all(bool(claim.fake_twin(c)) for c in claim.control_cases) else 0.0
    no_reg = 1.0 if all(bool(claim.mechanism(c)) for c in claim.prior_cases) else 0.0

    # grounding: build the claim's support subgraph, mint anchor edges from the
    # EXISTING signals it carries, and ask the REAL ReachableFrom Term.
    anchors: list = []
    grounded = 0.0
    if claim.ground_support is not None:
        support = claim.ground_support(sub)
        if support is not None and sub.has_node(support):
            _add_edge_unchecked(native, claim_node, "supported_by", support)
            ensure_grounding_edges(agent)
            gr = grounding_reach(agent, support)
            anchors = gr["anchors"]
            grounded = 1.0 if gr["reached"] else 0.0

    sub.set_attr(probe, "real_pass", real_pass)
    sub.set_attr(probe, "twin_pass", twin_pass)
    sub.set_attr(claim_node, "no_regression", no_reg)
    sub.set_attr(claim_node, "grounded", grounded)

    # 3. GATE — the Rust rule ANDs the three gates and writes `verdict`.
    _ensure_gate_rule(sub, native)
    sub.tick()

    at = sub.node(claim_node)["attrs"]
    verdict = float(at.get("verdict", 0.0))
    g_disc = float(at.get("g_discriminates", 0.0)) >= 0.5
    g_noreg = float(at.get("g_no_regression", 0.0)) >= 0.5
    g_ground = float(at.get("g_grounded", 0.0)) >= 0.5
    accepted = verdict >= 0.5

    reason = _reason(accepted, g_disc, g_noreg, g_ground,
                     real_pass >= 0.5, twin_pass >= 0.5, n_ctrl, anchors)

    return {
        "accepted": accepted,
        "verdict": verdict,
        "reason": reason,
        "discriminates": g_disc,
        "no_regression": g_noreg,
        "grounded": g_ground,
        "real_pass": real_pass >= 0.5,
        "twin_pass": twin_pass >= 0.5,
        "anchors": anchors,
        "claim_node": claim_node,
        "probe_node": probe,
    }


def _reason(accepted, disc, noreg, ground, real_pass, twin_pass, n_ctrl, anchors) -> str:
    """Mechanical readback of the Rust-computed gate booleans — assembles the
    human-readable reason. NOT a decision: `accepted` already came from the
    Rust `verdict` attr; this only describes which gate it tripped on."""
    if accepted:
        return (f"ACCEPTED: control discriminates (mechanism survives {n_ctrl} held-out "
                f"case(s); the known-fake twin FAILS it), no regression, grounded in "
                f"{anchors or ['<anchor>']}.")
    fails: list = []
    if not disc:
        if n_ctrl == 0:
            fails.append("control is VACUOUS (no cases) — cannot discriminate")
        elif not real_pass:
            fails.append("control does NOT survive the mechanism (held-out/ambiguous case "
                         "fails — a tuned/overfit pass, not real structure)")
        elif twin_pass:
            fails.append("control has NO teeth — a known-fake twin passes it too "
                         "(does not discriminate)")
        else:
            fails.append("control does not discriminate")
    if not noreg:
        fails.append("REGRESSION — the change breaks a previously-holding case")
    if not ground:
        fails.append("UNGROUNDED — support reaches no external anchor "
                     "(a confident ungrounded basin, not grounded structure)")
    return "REJECTED: " + "; ".join(fails) + "."


__all__ = ["Claim", "verify_claim"]
