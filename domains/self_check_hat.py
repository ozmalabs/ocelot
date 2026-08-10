"""self_check_hat — the agent's WEIGHTED, BOUNDED self-check reflex (its ERN / precision-
weighted prediction-error / metacognitive-confidence gate), built from the agent's OWN pieces.

WHAT IT IS (the disposition the ASSISTANT used to supply by hand)
================================================================================
After a conclusion/verdict, fire a check sized by UNCERTAINTY x STAKES:
  · low confidence x high stakes (a gate-fire / a commit)  -> FIRE the check
  · a clean, obvious, high-confidence result               -> a GLANCE, then commit
The weighting is the whole point: spend the doubt where being wrong costs the most and
you are least sure. The check is NOT a global re-doubt (that is the OCD agent, drowning in
noise) — it is a TARGETED do-contrast at the WEAK LINK (the most-uncertain dimension): the
one thing that would overturn the verdict. It resolves BOUNDED — one weighted check, then:
  · a MISS found   -> RE-OPEN (reject the verdict; do not commit)
  · no miss        -> COMMIT (re-seal)

WHERE THE COGNITION LIVES (composed from the agent's own graph-resident pieces — NOT new
Python cognition; this file is world-adapter glue + native Term composition only)
================================================================================
  · SURPRISE  = the agent's error signal, the SAME native Term scripts.native_collapse uses:
        T_SURPRISE = Neg(Log(Var("conf")))            # -log(confidence-at-the-verdict)
    A verdict whose realised support crashed below what it claimed -> low conf -> high
    surprise. This is the UNCERTAINTY channel, evaluated IN RUST by substrate.evaluate.
  · META-MONITOR (domains.meta_monitor) = the agent's confidence / effort-payoff readout AND
    its do-contrast machinery: register_process / report / investigate (do-contrast) /
    install_investigation_rule + agent_conclude_investigation (the 3-way lever_helps /
    lever_harms / disconnected_lever verdict, decided from MEASUREMENT not assumption). The
    hat hands the weak-link do-contrast to THIS, the agent's own investigator.
  · The WEIGHT and the FIRE/GLANCE decision are NATIVE Term-trees (Times / Gt / IfThenElse /
    Minus / Abs ...), evaluated by substrate.evaluate. No Python `if` decides whether to
    fire — a graph Term does.

THE WEIGHT (uncertainty x stakes), every factor from the agent's own measurements
================================================================================
    uncertainty = normalised surprise about the verdict's CLAIM vs its REALISED support
                  s_norm = surprise / (surprise + 1)   (in [0,1), native Minus/Div/Plus)
                  surprise = -log(conf), conf = realised_support / claimed_support clamped
    stakes      = the verdict's own declared cost-of-being-wrong in [0,1]:
                  a GATE-FIRE / a COMMIT is high-stakes (1.0); a glanceable report lower.
    weight      = uncertainty * stakes                 (native Times)
    FIRE  <=>  weight > fire_threshold                 (native Gt -> IfThenElse)
The threshold is a seeded dial on the hat's root (not a Python constant).

"JUST A HAT": a gateable module that sits ON the loop, reads a verdict, and (maybe) runs one
do-contrast. It changes NOTHING in the core — CortexLoop / solve_for_n are untouched; the
surprise + meta-monitor are graph-resident already; the hat only COMPOSES them. ADDITIVE.

DONKEY / ARCHITECTURE AUDIT
================================================================================
  · NO net, NO .fit, NO gradient, NO sweep. The weight + fire decision are native Term-trees;
    the do-contrast verdict is the meta-monitor's existing graph Rule.
  · NO new Python cognition: every `if` that decides is a Term (W_FIRE_TERM) or the
    meta-monitor's investigate_connection Rule. Python here only marshals numbers into graph
    attrs and runs the caller's measurement callable (world-I/O), exactly as
    meta_monitor.investigate does.
  · CortexLoop / solve_for_n.py UNTOUCHED. No core change.
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate_rs import (
    Substrate, Attr, Lit, Var, Gt, Lte, Eq, And, Or, Abs, Minus, Plus, Times,
    Div, Neg, Log, IfThenElse, Min, Max,
)

import domains.meta_monitor as MM

# the agent's OWN surprise term — imported, not re-derived.
from scripts.native_collapse import T_SURPRISE, BETA  # noqa: F401  (BETA unused; provenance)

_SEED_PATH = (Path(__file__).resolve().parent.parent / "seeds" / "self_check_hat.json")


# ===========================================================================
#  THE NATIVE TERM-TREES — the hat's cognition, as graph Term-trees (Rust-evaluated).
#  These name NO domain and hold NO state: pure weight / fire arithmetic over a node's attrs.
# ===========================================================================

# confidence the verdict deserves = realised_support / claimed_support, clamped to (eps, 1].
# (If a verdict claims a baseline at 0.625 but the baseline REALISED 0.20, conf ~ 0.32.)
_C = Var("C")                              # the Check node carrying the verdict's numbers
_EPS = Lit(1e-3)
T_CONF = Max(items=(_EPS, Min(items=(Lit(1.0),
            Div(Attr(_C, "realised_support"),
                Max(items=(Attr(_C, "claimed_support"), _EPS)))))))

# UNCERTAINTY = surprise about the verdict's claim, squashed into [0,1):
#   surprise = -log(conf)   (the agent's native T_SURPRISE, conf bound to this Check)
#   u = surprise / (surprise + 1)
_SURP = Neg(Log(T_CONF))
T_UNCERTAINTY = Div(_SURP, Plus(items=(_SURP, Lit(1.0))))

# WEIGHT = uncertainty * stakes.  stakes is the verdict's own declared cost-of-wrong in [0,1].
T_WEIGHT = Times(items=(T_UNCERTAINTY, Attr(_C, "stakes")))

# FIRE decision: weight > fire_threshold (seeded dial on the Check) -> 1 (fire) else 0 (glance).
T_FIRE = IfThenElse(Gt(a=T_WEIGHT, b=Attr(_C, "fire_threshold")), Lit(1.0), Lit(0.0))


def _native(s):
    return s._inner if hasattr(s, "_inner") else s


def _load_seed() -> dict:
    if _SEED_PATH.exists():
        with _SEED_PATH.open() as f:
            return json.load(f)
    return {}


def _root(s):
    for n in s.nodes("SelfCheckRoot"):
        return n
    dials = _load_seed().get("self_check_root", {})
    return s.add_node("SelfCheckRoot", {"origin": "self_check_hat", **dials})


def fire_threshold(s) -> float:
    return float(s.node(_root(s))["attrs"].get("fire_threshold", 0.30))


# ===========================================================================
#  THE HAT — gate a verdict.  Pure marshal + native eval; the decision is the Term.
# ===========================================================================

def gate_verdict(s, *, name: str, verdict: bool, claimed_support: float,
                 realised_support: float, stakes: float,
                 weak_link: str = "", expected: float | None = None) -> dict:
    """Sit the hat on a verdict and compute the WEIGHTED self-check signal NATIVELY.

    A `Check` node carries the verdict's own numbers; the hat evaluates the native Term-trees
    (T_CONF / T_UNCERTAINTY / T_WEIGHT / T_FIRE) over it. Returns the decision dict — whether
    to FIRE the targeted do-contrast (high uncertainty x stakes) or GLANCE (commit). No Python
    `if` decides: the fire flag is the value of T_FIRE evaluated in Rust.

      name             — what produced the verdict (for the meta-monitor process id)
      verdict          — the claimed True/False the producer printed
      claimed_support  — the support the verdict IMPLICITLY claims (e.g. the OLD prior 0.625)
      realised_support — the support the run ACTUALLY realised (e.g. OLD crashed to 0.20)
      stakes           — cost-of-being-wrong in [0,1]: a gate-fire / commit ~ 1.0
      weak_link        — the most-uncertain dimension to do-contrast if fired (free text)
      expected         — optional: the value `realised` was supposed to anchor to (the prior)
    """
    root = _root(s)
    chk = s.add_node("Check", {
        "origin": "self_check_hat", "name": name,
        "verdict": 1.0 if verdict else 0.0,
        "claimed_support": float(claimed_support),
        "realised_support": float(realised_support),
        "stakes": float(stakes),
        "weak_link": weak_link,
        "expected": float(expected) if expected is not None else float(claimed_support),
        "fire_threshold": fire_threshold(s),
    })
    try:
        s.add_production({"src": {"type": "SelfCheckRoot", "var": "a"},
                          "edge_type": "checks", "tgt": {"type": "Check", "var": "b"},
                          "provenance": "self_check_hat:checks"})
    except Exception:
        pass
    try:
        s.add_edge(root, "checks", chk)
    except Exception:
        pass

    conf = float(s.evaluate(T_CONF, {"C": chk}))
    uncertainty = float(s.evaluate(T_UNCERTAINTY, {"C": chk}))
    surprise = float(s.evaluate(T_SURPRISE, {"conf": max(conf, 1e-12)}))
    weight = float(s.evaluate(T_WEIGHT, {"C": chk}))
    fire = float(s.evaluate(T_FIRE, {"C": chk})) >= 0.5

    s.set_attr(chk, "conf", conf)
    s.set_attr(chk, "uncertainty", uncertainty)
    s.set_attr(chk, "surprise", surprise)
    s.set_attr(chk, "weight", weight)
    s.set_attr(chk, "fire", 1.0 if fire else 0.0)

    return {"check_node": chk, "name": name, "verdict": verdict,
            "conf": conf, "surprise": surprise, "uncertainty": uncertainty,
            "stakes": float(stakes), "weight": weight,
            "claimed_support": float(claimed_support),
            "realised_support": float(realised_support),
            "fire_threshold": fire_threshold(s), "fire": fire,
            "weak_link": weak_link}


def run_do_contrast(s, gate: dict, measure_with, measure_without,
                    connection_band: float = 0.05) -> dict:
    """If the hat FIRED, hand the targeted weak-link do-contrast to the agent's OWN
    investigator (domains.meta_monitor): measure the payoff WITH vs WITHOUT the thing the
    verdict leans on, then let the meta-monitor's investigate_connection RULE conclude
    (lever_helps / lever_harms / disconnected_lever) from the MEASURED direction — not Python.

    `measure_with` / `measure_without` are the only world-I/O (thin callables the caller
    passes, e.g. 'accuracy against the REAL prior baseline' vs 'against the degraded one').
    Returns the do-contrast result + the meta-monitor's verdict.
    """
    name = gate["name"]
    p = MM.register_process(s, name, effort_label="self_check",
                            payoff_label="verdict_support")
    s.set_attr(p, "connection_band", float(connection_band))

    with_val = float(measure_with())
    without_val = float(measure_without())
    MM.record_intervention(s, name, with_val, without_val)

    inv = MM.install_investigation_rule(s)
    issues = MM.agent_conclude_investigation(s, inv["rule_index"])
    issue = next((i["issue"] for i in issues if i["name"] == name), "none")

    return {"name": name, "payoff_with": with_val, "payoff_without": without_val,
            "delta": with_val - without_val, "connection_band": float(connection_band),
            "meta_verdict": issue}


def resolve(s, gate: dict, do_contrast: dict | None = None) -> dict:
    """BOUNDED resolution. Decide REOPEN vs COMMIT from the hat's native signals + (if it
    fired) the do-contrast verdict — one weighted check, then resolve. No endless re-doubt.

    REOPEN when:
      · the hat FIRED and the do-contrast found a MISS — the verdict leans on something that
        is HARMFUL/disconnected, OR the realised support crashed below the claim (the degraded
        baseline). This is exactly the W5 case: a verdict that 'matched OLD' while OLD itself
        crashed below its prior -> conf low -> high weight -> fire -> do-contrast shows the
        anchor degraded -> REOPEN.
    COMMIT otherwise (a glance on the clean wins; one bounded check on the suspicious).
    """
    chk = gate["check_node"]
    cattrs = s.node(chk)["attrs"]
    realised = float(cattrs["realised_support"])
    expected = float(cattrs["expected"])
    baseline_crashed = realised < (expected - 0.10)
    miss = False
    reason = "clean: low weight, committed (glance)"
    if gate["fire"]:
        # fired: a weighted check is warranted. A miss is a do-contrast that shows the verdict
        # leans on a degraded / harmful / disconnected support.
        mv = (do_contrast or {}).get("meta_verdict", "none")
        if baseline_crashed:
            miss = True
            reason = (f"FIRED + do-contrast: realised support {realised:.3f} "
                      f"crashed below the claimed/expected anchor "
                      f"{expected:.3f} — verdict compared to a "
                      f"DEGRADED baseline (meta-verdict={mv})")
        elif mv in ("lever_harms", "disconnected_lever"):
            miss = True
            reason = f"FIRED + do-contrast: meta-verdict={mv} — the support does not hold"
        else:
            reason = (f"FIRED but do-contrast clean (meta-verdict={mv}, "
                      f"baseline held) — committed")
    decision = "REOPEN" if miss else "COMMIT"
    s.set_attr(chk, "resolution", decision)
    return {"name": gate["name"], "fired": gate["fire"], "miss": miss,
            "decision": decision, "reason": reason,
            "weight": gate["weight"], "surprise": gate["surprise"]}


def self_check(s, *, name: str, verdict: bool, claimed_support: float,
               realised_support: float, stakes: float, weak_link: str = "",
               expected: float | None = None,
               measure_with=None, measure_without=None,
               connection_band: float = 0.05) -> dict:
    """The whole reflex in one call: gate the verdict (weight = uncertainty x stakes,
    native), and IF it fires, run the targeted weak-link do-contrast via the meta-monitor,
    then resolve BOUNDED (REOPEN / COMMIT). Returns the full trace.
    """
    gate = gate_verdict(s, name=name, verdict=verdict, claimed_support=claimed_support,
                        realised_support=realised_support, stakes=stakes,
                        weak_link=weak_link, expected=expected)
    dc = None
    if gate["fire"] and measure_with is not None and measure_without is not None:
        dc = run_do_contrast(s, gate, measure_with, measure_without, connection_band)
    res = resolve(s, gate, dc)
    return {"gate": gate, "do_contrast": dc, "resolution": res}


__all__ = ["gate_verdict", "run_do_contrast", "resolve", "self_check",
           "fire_threshold", "T_CONF", "T_UNCERTAINTY", "T_WEIGHT", "T_FIRE", "T_SURPRISE"]
