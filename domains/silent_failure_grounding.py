"""silent_failure_grounding — the SILENT-FAILURE GROUNDING CHECK: the named final brick of
'the assistant out of the loop'.

THE INSIGHT — why this check is DIFFERENT from the rest of the stack
================================================================================
A SILENT failure is INTERNALLY CONSISTENT and produces NO internal surprise (the Dvorak
case: max localized surprise -0.000). It is wrong ONLY against world ground-truth the agent
lacks. So the existing INTERNAL stack STRUCTURALLY cannot catch it:

  · self_check_hat:  weight = uncertainty x stakes.  A silent failure has conf ~ 1 ->
    surprise ~ 0 -> uncertainty ~ 0 -> weight ~ 0 -> GLANCE.  A LOUDER internal check
    cannot help: there is NO internal signal to hear.  (Verified in self_check_hat's own
    control row: high-stakes + clean = weight 0.000, does NOT fire.)
  · autonomous_curation:  the loop is DRIVEN by localized surprise (MaxOver of per-dim
    surprise).  A silent failure exposes NO dimension the prediction-error points at
    (max_surprise < floor) -> the loop BOTTOMS OUT.

THE FIX — fire on STAKES ALONE, measure EMPIRICALLY against the WORLD
================================================================================
The grounding check is the NEW channel the internal stack lacks:

  1. FIRE-ON-STAKES        — a HIGH-STAKES conclusion fires the grounding check REGARDLESS
     (the stakes channel)    of surprise.  Native Term T_STAKES_FIRE = Gt(stakes, floor) —
                              it does NOT read uncertainty/surprise at all (that is the whole
                              point: a silent failure has none).  This plugs into the
                              self_check_hat at the STAKES channel — fire-on-stakes, not
                              fire-on-weight.
  2. EMPIRICAL GROUNDING    — MEASURE the conclusion against the WORLD / ground truth using
     (against the WORLD)      the agent's OWN machinery: the Stage-4 forward/inverse round-
                              trip (speak W -> hear -> recognise -> ?= W), a held-out test,
                              or a COMPUTABLE quantity the claim can be checked against.  This
                              is EMPIRICAL / EXTERNAL — NOT the internal do-contrast
                              (meta_monitor), because only WORLD-CONTACT reveals an
                              internally-consistent-but-externally-wrong claim.
  3. CONTRADICTION -> REOPEN — if the measured value CONTRADICTS the claim (native Term
                              T_CONTRADICTION = Gt(|measured - claimed|, tol)) -> REOPEN.
                              Otherwise the world AGREES -> the silent claim is grounded,
                              COMMIT.
  4. BANK (optional)        — a grounding-caught silent failure can be banked as a shape
                              (autonomous_curation) for the skeptic — but keyed on the
                              EXTERNAL measurement, not on a (nonexistent) localized surprise.

WHERE THE COGNITION LIVES (composed from the agent's OWN graph-resident pieces)
================================================================================
  · T_STAKES_FIRE / T_CONTRADICTION / T_DELTA   — NATIVE Term-trees (Gt / Abs / Minus /
    IfThenElse), evaluated IN RUST by substrate.evaluate.  No Python `if` decides whether to
    fire or whether the world contradicts the claim — a graph Term does.
  · the EMPIRICAL MEASUREMENT itself             — the agent's OWN world-machinery handed in
    as a `world_measure` callable: the Stage-4 round-trip (scripts.stage4_grounding.run_loop /
    an inverse.recognise), a held-out test, or any computable check.  This is the ONLY world-
    I/O — exactly the kind the hat / meta_monitor already take.  It returns a measured value
    AGAINST GROUND TRUTH the agent can reach.
  · the HONEST BOTTOM-OUT                        — when NO `world_measure` is available (the
    agent has no world-access to that ground truth), the check NAMES it: 'needs world-contact
    / acquisition I lack' — it does NOT fake a pass.  This is the residual-of-the-residual.

DONKEY / ARCHITECTURE AUDIT
================================================================================
  · ADDITIVE — a NEW module only.  self_check_hat.py / autonomous_curation.py /
    generative_skeptic.py / meta_monitor.py / the Stage-4 harnesses READ as references, NOT
    modified.  CortexLoop / solve_for_n.py / cortex_loop.py UNTOUCHED.
    order_n_postulates.py / speech_science.py NOT touched.
  · NO net, NO .fit, NO gradient, NO sweep, NO loss/optimiser.  The check is a REAL
    MEASUREMENT against the world (the agent's round-trip / held-out / computable quantity),
    NOT a heuristic.  The fire + contradiction decisions are native Term-trees.
  · NATIVE where the cognition lives.  Python here is world-adapter glue only: marshal the
    claim's numbers onto a graph node, RUN the agent's own world-measure callable (world-I/O),
    evaluate the native Terms.  Exactly what self_check_hat.run_do_contrast already does — but
    the measurement is EMPIRICAL/EXTERNAL, not the internal do-contrast.
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate_rs import (
    Attr, Lit, Var, Gt, Abs, Minus, IfThenElse, Max, Min, Div,
)

# the agent's OWN weighted self-check — we extend it at the STAKES channel, not modify it.
import domains.self_check_hat as HAT
# the agent's OWN failure-banking — a grounding-caught silent failure can be banked.
import domains.autonomous_curation as AC

_SEED_PATH = (Path(__file__).resolve().parent.parent / "seeds"
              / "silent_failure_grounding.json")


# ===========================================================================
#  THE NATIVE TERM-TREES — the grounding check's cognition, as graph Term-trees.
#  They name NO domain and hold NO state: pure stakes-fire + world-contradiction
#  arithmetic over a `GroundCheck` node's attrs.
# ===========================================================================

_G = Var("G")  # the GroundCheck node carrying the claim + measurement numbers

# FIRE ON STAKES ALONE — the NEW channel.  Does NOT read surprise/uncertainty at all:
# a high-stakes conclusion fires the grounding check REGARDLESS of how confident it feels.
# This is exactly what the internal weight = uncertainty x stakes cannot reach on a silent
# failure (uncertainty ~ 0 -> weight ~ 0).  Native Gt -> IfThenElse, Rust-evaluated.
T_STAKES_FIRE = IfThenElse(
    Gt(a=Attr(_G, "stakes"), b=Attr(_G, "stakes_floor")), Lit(1.0), Lit(0.0))

# DELTA between the claim and the WORLD measurement, as a fraction of the claim's scale.
# claimed / measured are values on the SAME scale (e.g. round-trip accuracy the claim
# asserts vs the round-trip accuracy the world realised; a computed quantity vs the claim).
_EPS = Lit(1e-9)
T_ABS_DELTA = Abs(Minus(Attr(_G, "measured"), Attr(_G, "claimed")))
# relative delta = |measured - claimed| / max(|claimed|, eps)  (native, in [0, inf))
T_REL_DELTA = Div(T_ABS_DELTA,
                  Max(items=(Abs(Attr(_G, "claimed")), _EPS)))

# CONTRADICTION — the world DISAGREES with the claim beyond tolerance.  Native:
# the measured value departs from the claimed value by more than `tol` (relative).
# 1.0 => the world contradicts the silent claim -> REOPEN;  0.0 => the world agrees.
T_CONTRADICTION = IfThenElse(
    Gt(a=T_REL_DELTA, b=Attr(_G, "tol")), Lit(1.0), Lit(0.0))


def _load_seed() -> dict:
    if _SEED_PATH.exists():
        with _SEED_PATH.open() as f:
            return json.load(f)
    return {}


def _root(s):
    for n in s.nodes("GroundingRoot"):
        return n
    dials = _load_seed().get("grounding_root", {})
    return s.add_node("GroundingRoot", {"origin": "silent_failure_grounding", **dials})


def stakes_floor(s) -> float:
    return float(s.node(_root(s))["attrs"].get("stakes_floor", 0.70))


def default_tol(s) -> float:
    return float(s.node(_root(s))["attrs"].get("tol", 0.15))


# ===========================================================================
#  THE GROUNDING CHECK.  Pure marshal + native eval + the agent's own world-measure.
#  The decisions (fire / contradiction) are Terms; the measurement is EMPIRICAL.
# ===========================================================================

def gate_on_stakes(s, *, name: str, claimed: float, stakes: float,
                   tol: float | None = None) -> dict:
    """Decide FIRE-ON-STAKES natively.  A `GroundCheck` node carries the claim's stakes
    (and claimed value + tolerance); T_STAKES_FIRE fires iff stakes > stakes_floor — it does
    NOT read surprise/uncertainty, which is exactly why it catches a SILENT failure the
    weight = uncertainty x stakes channel misses.  Returns {check_node, fire, stakes, ...}.
    """
    root = _root(s)
    tol = default_tol(s) if tol is None else float(tol)
    g = s.add_node("GroundCheck", {
        "origin": "silent_failure_grounding", "name": name,
        "claimed": float(claimed), "measured": float(claimed),  # measured filled in later
        "stakes": float(stakes),
        "stakes_floor": stakes_floor(s),
        "tol": float(tol),
    })
    try:
        s.add_production({"src": {"type": "GroundingRoot", "var": "a"},
                          "edge_type": "grounds", "tgt": {"type": "GroundCheck", "var": "b"},
                          "provenance": "silent_failure_grounding:grounds"})
    except Exception:
        pass
    try:
        s.add_edge(root, "grounds", g)
    except Exception:
        pass

    fire = float(s.evaluate(T_STAKES_FIRE, {"G": g})) >= 0.5
    s.set_attr(g, "fire", 1.0 if fire else 0.0)
    return {"check_node": g, "name": name, "claimed": float(claimed),
            "stakes": float(stakes), "stakes_floor": stakes_floor(s),
            "tol": float(tol), "fire": fire}


def ground_against_world(s, gate: dict, world_measure) -> dict:
    """The EMPIRICAL grounding measurement — the heart of the check.  Run the agent's OWN
    world-machinery (`world_measure`, a thin callable: the Stage-4 round-trip, a held-out
    test, or a computable quantity) to obtain the value the WORLD realises for this claim,
    then let the native T_CONTRADICTION Term decide whether the world DISAGREES with the
    claim beyond tolerance.

    `world_measure` is the ONLY world-I/O — it returns a float on the SAME scale as the
    claim (e.g. the round-trip accuracy the claim asserts vs the accuracy the world
    realised; the computed finger-travel reduction vs the claimed one).  This is EMPIRICAL /
    EXTERNAL, NOT the internal do-contrast: only world-contact reveals an internally-
    consistent-but-externally-wrong claim.

    Returns {measured, claimed, abs_delta, rel_delta, contradiction (bool), reason}.
    If world_measure is None -> the agent has NO world-access to this ground truth -> the
    check BOTTOMS OUT HONESTLY (does not fake a pass).
    """
    g = gate["check_node"]
    if world_measure is None:
        s.set_attr(g, "grounded", 0.0)
        return {"measured": None, "claimed": gate["claimed"], "abs_delta": None,
                "rel_delta": None, "contradiction": None, "grounded": False,
                "reason": ("NEEDS WORLD-CONTACT / ACQUISITION I LACK: no machinery to "
                           "empirically measure this claim's ground truth (no round-trip, "
                           "held-out test, or computable quantity reaches it). The check "
                           "does NOT fake a pass — it names the residual-of-the-residual.")}

    measured = float(world_measure())  # <-- the WORLD-I/O: the agent's own measurement
    s.set_attr(g, "measured", measured)
    abs_delta = float(s.evaluate(T_ABS_DELTA, {"G": g}))
    rel_delta = float(s.evaluate(T_REL_DELTA, {"G": g}))
    contradiction = float(s.evaluate(T_CONTRADICTION, {"G": g})) >= 0.5
    s.set_attr(g, "abs_delta", abs_delta)
    s.set_attr(g, "rel_delta", rel_delta)
    s.set_attr(g, "grounded", 1.0)
    s.set_attr(g, "contradiction", 1.0 if contradiction else 0.0)
    reason = (f"WORLD measured {measured:.4f} vs claimed {gate['claimed']:.4f} "
              f"(rel delta {rel_delta:.3f} {'>' if contradiction else '<='} tol "
              f"{gate['tol']:.3f}) -> "
              f"{'CONTRADICTS the claim' if contradiction else 'world AGREES'}")
    return {"measured": measured, "claimed": gate["claimed"], "abs_delta": abs_delta,
            "rel_delta": rel_delta, "contradiction": contradiction, "grounded": True,
            "reason": reason}


def resolve(s, gate: dict, grounding: dict) -> dict:
    """BOUNDED resolution from the stakes-fire + the EMPIRICAL grounding result.

      · fired on stakes + the WORLD CONTRADICTS the claim   -> REOPEN  (the silent failure
        the internal stack could not feel, caught against ground truth).
      · fired on stakes + the WORLD AGREES                  -> COMMIT  (the silent claim is
        GROUNDED — the world confirms it).
      · fired on stakes + NO world-access                   -> UNGROUNDED  (the honest
        residual-of-the-residual: 'needs world-contact / acquisition I lack'; NOT a pass).
      · did not fire (low stakes)                           -> GLANCE / COMMIT.
    """
    g = gate["check_node"]
    if not gate["fire"]:
        s.set_attr(g, "resolution", "COMMIT")
        return {"name": gate["name"], "fired": False, "decision": "COMMIT",
                "reason": "low stakes: grounding check not warranted (glance)"}
    if not grounding["grounded"]:
        s.set_attr(g, "resolution", "UNGROUNDED")
        return {"name": gate["name"], "fired": True, "decision": "UNGROUNDED",
                "contradiction": None, "reason": grounding["reason"]}
    if grounding["contradiction"]:
        s.set_attr(g, "resolution", "REOPEN")
        return {"name": gate["name"], "fired": True, "decision": "REOPEN",
                "contradiction": True, "reason": grounding["reason"]}
    s.set_attr(g, "resolution", "COMMIT")
    return {"name": gate["name"], "fired": True, "decision": "COMMIT",
            "contradiction": False,
            "reason": "world AGREES: the silent claim is GROUNDED -> commit"}


def grounding_check(s, *, name: str, conclusion_text: str, claimed: float, stakes: float,
                    world_measure=None, tol: float | None = None,
                    bank_on_catch: bool = False) -> dict:
    """The whole SILENT-FAILURE GROUNDING CHECK in one call:

      FIRE-ON-STAKES (native, regardless of surprise) ->
      EMPIRICAL world measurement (the agent's own round-trip / held-out / computable check) ->
      CONTRADICTION (native) -> REOPEN  | world AGREES -> COMMIT  | no world-access -> UNGROUNDED.

    Optionally BANK a grounding-caught silent failure as a shape (autonomous_curation), keyed
    on the EXTERNAL measurement (a `world_contradiction` Dim whose realised support is the
    measured value) — NOT on a localized surprise the silent failure does not have.

    Returns the full trace {gate, grounding, resolution, bank}.
    """
    gate = gate_on_stakes(s, name=name, claimed=claimed, stakes=stakes, tol=tol)
    grounding = {"grounded": False, "contradiction": None, "measured": None,
                 "claimed": float(claimed), "rel_delta": None,
                 "reason": "not fired (low stakes)"}
    if gate["fire"]:
        grounding = ground_against_world(s, gate, world_measure)
    res = resolve(s, gate, grounding)

    bank = {"banked": False, "reason": "not requested or no contradiction to bank"}
    if (bank_on_catch and res["decision"] == "REOPEN"
            and grounding.get("contradiction")):
        bank = _bank_grounded_failure(s, name, conclusion_text, grounding)
    return {"gate": gate, "grounding": grounding, "resolution": res, "bank": bank}


def _bank_grounded_failure(s, name: str, conclusion_text: str, grounding: dict) -> dict:
    """Bank a grounding-CAUGHT silent failure as a shape for the skeptic — keyed on the
    EXTERNAL world-measurement, not a localized surprise.  We marshal the conclusion as a
    Conclusion with ONE 'world_contradiction' Dim whose claimed = the asserted value and
    realised = the WORLD-measured value (so the do-contrast collapse IS the empirical
    contradiction), then hand it to autonomous_curation's bank.  The collapse is REAL (the
    world disagreed), so the shape is grounded, not spurious.
    """
    measured = float(grounding["measured"])
    claimed = float(grounding["claimed"])
    dims = [{
        "name": "world_contradiction",
        "claimed": max(abs(claimed), 1e-3),
        "realised": min(abs(measured), max(abs(claimed), 1e-3)),
        "tokens": conclusion_text,
    }]
    det = AC.detect(s, conclusion_text, dims, name=name)
    # the resolution is the EMPIRICAL contradiction (the world realised << the claim):
    # frame it as the meta-monitor's 'lever_harms' so bank accepts it as a real miss.
    res = {"weak_link": "world_contradiction", "weak_link_tokens": conclusion_text,
           "payoff_with": claimed, "payoff_without": measured,
           "delta": measured - claimed, "meta_verdict": "lever_harms"}
    bk = AC.bank(s, det, res,
                 shape_name=f"grounded__{name}__world_contradiction")
    return bk


__all__ = ["gate_on_stakes", "ground_against_world", "resolve", "grounding_check",
           "stakes_floor", "default_tol",
           "T_STAKES_FIRE", "T_CONTRADICTION", "T_ABS_DELTA", "T_REL_DELTA"]
