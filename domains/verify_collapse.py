"""verify_collapse — the math layer's VERIFY-AGAINST-KNOWN, DELEGATED UP to the
native manifold-confidence-interval-collapse (scripts/native_collapse.py).

THE RECOGNISED UNITY (what this module rests on)
================================================
The agent has TWO confidence-collapse mechanisms that are the SAME mechanism:

  (A) NATIVE, graded — scripts/native_collapse.py: a candidate manifold whose
      log-weights `lw = BETA*agree + seq_lp` are written as GRAPH DATA (one Cand
      node per hypothesis hung off a ManRoot by a `cand` edge); the softmax
      confidence is a graph Term-tree evaluated IN RUST:
          mx   = MaxOver_c  lw(c)                  (T_MAX_LW)
          Z    = Sum_c       exp(lw(c) - mx)       (T_Z)
          conf = exp(lw(truth) - mx) / Z           (T_CONF)
      As revealed evidence accumulates, the confidence interval CONTRACTS onto the
      admissible submanifold (the agreeing candidates). A PARTIAL contraction =
      graded confidence.

  (B) DEGENERATE, binary — domains/{acquire,elevator,...}.py's verify-against-known:
      a grounded op REPRODUCES the known values or it does NOT. For each known case
      the guard computes `got` and compares to `want`; one mismatch => verified=False,
      all-match => verified=True. A point pass/fail.

(B) IS the degenerate case of (A). Read the verify as a collapse:
  · the REVEALED SEQUENCE       = the known (case -> want) constraints, revealed one
                                   at a time (b_0(S^2), b_1(S^2), b_2(S^2), ...);
  · the AGREE KERNEL            = `1.0 if got==want else 0.0` — the agent's OWN
                                   `_hard_agree` (opaque-symbol equality), exactly
                                   the HARD Γ-prune the native loop already uses;
  · the MANIFOLD               = the candidate grounded op vs a NULL hypothesis that
                                   agrees with NOTHING (the "doesn't reproduce" twin);
  · the COLLAPSE               = lw accumulates BETA per matched known value; the
                                   softmax confidence contracts toward the candidate;
  · the BINARY VERDICT         = full agreement => conf -> 1 (admitted, a POINT
                                   collapse); ANY mismatch => the prefix BREAKS and
                                   conf collapses toward the null (pruned).
  · GRADED CONFIDENCE          = a PARTIAL collapse: the candidate agrees with SOME
                                   known values but not all (e.g. AHSS rank-5 fixed,
                                   1-of-2 torsion classes killed) => a confidence
                                   STRICTLY BETWEEN 0 and 1 — the native payoff the
                                   binary verify could not express.
  · a WALL                     = a NON-collapse: a known value the candidate cannot
                                   produce (no constraint reaches it) leaves the
                                   interval un-contracted — the missing input.

THE UNIFICATION (delegate domains -> native — the architecture-faithful direction)
==================================================================================
This module replaces the Python `for want: if got!=want: return False` verify with
ONE call into the NATIVE collapse: write the candidate's per-known-value AGREEMENT
into the graph as a Cand manifold (candidate + null twin), let the NATIVE Term-trees
(T_MAX_LW / T_Z / T_CONF — evaluated in Rust) run, and READ the collapsed confidence.

  · The BINARY verify becomes `collapse_confidence(...) >= 1.0 - eps` — the degenerate
    point-collapse, the SAME verified result the Python verify returned.
  · The GRADED confidence (a partial collapse) is returned ALONGSIDE, so a verify that
    used to be a flat pass/fail now reports HOW FAR the interval contracted.

NO RE-IMPLEMENTATION: the collapse arithmetic (max/softmax/confidence) is NOT done in
Python here — it is the native Term-trees in scripts/native_collapse.py, evaluated by
the Rust runtime via the EXISTING substrate API (add_node / add_edge_unchecked /
set_attr / evaluate). Python here is the world-adapter: it translates the known
(got, want) pairs into the agree-counts that become the manifold's `lw`, ticks the
native evaluator, and reads the collapsed confidence back. No PyO3 binding is added —
the native collapse is already reachable through the existing API (it is precisely
what native_collapse.native_manifold uses).

DONKEY: the only arithmetic is the agree-count (an integer count of matched known
values) and the native softmax; no fit, no gradient, no tuned parameter. BETA is the
native loop's own constant.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Callable, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
_DSLPY = os.path.join(ROOT, "runners", "dsl", "python")
if _DSLPY not in sys.path:
    sys.path.insert(0, _DSLPY)

# THE NATIVE COLLAPSE — imported, NOT re-implemented. These are the graph Term-trees
# evaluated by the Rust runtime (the manifold softmax + confidence).
from scripts.native_collapse import (  # noqa: E402
    BETA, T_MAX_LW, T_Z, T_CONF,
)
from substrate_rs import Substrate  # noqa: E402  (the native-collapse world adapter)


# A dedicated native-collapse substrate. The manifold is a FRESH scratch scaffold
# per verify (native_collapse builds a fresh ManRoot every collapse), so the verify
# does NOT need the domain's grounding substrate — it needs the NATIVE evaluator.
# This module owns ONE Substrate that runs the native collapse Term-trees in Rust;
# it holds NO agent state (every manifold is built + torn down per call). This is
# the world-adapter for the native collapse: it translates the known (got, want)
# pairs into the graph manifold, ticks the native evaluator, reads the collapse.
_NATIVE = Substrate()


def _native_substrate():
    """The native-collapse evaluator (a wrapper Substrate that runs T_MAX_LW / T_Z
    / T_CONF in Rust). Shared across verifies; each call builds + reads its own
    fresh ManRoot, so there is no cross-verify state."""
    return _NATIVE


# ==========================================================================
# THE AGREE KERNEL — the agent's OWN hard symbol-equality (mirrors
# collapse_engine._hard_agree). A revealed known value either matches (1.0) or
# breaks the prefix (0.0). Opaque comparison; no domain knowledge.
# ==========================================================================

def _agree(got, want) -> float:
    """1.0 on a match, 0.0 on a mismatch — the HARD Γ-prune the native loop uses.
    Integer-cast the topology/number values (Betti/Euler are counts) so a float vs
    int 'got' still compares by value; fall back to raw equality otherwise."""
    try:
        return 1.0 if int(got) == int(want) else 0.0
    except (TypeError, ValueError):
        return 1.0 if got == want else 0.0


# ==========================================================================
# THE NATIVE COLLAPSE, AS A VERIFY — write the candidate manifold to the graph,
# evaluate the native softmax/confidence Term-trees in Rust, read the collapse.
# ==========================================================================

def collapse_confidence(agreements: list[float], *, substrate=None) -> dict[str, Any]:
    """Run the NATIVE manifold collapse over the candidate's per-known-value
    AGREEMENTS and return the collapsed confidence on the candidate hypothesis.

    `agreements` is the revealed sequence: one entry per known (case -> want)
    constraint, 1.0 if the grounded op reproduced it, 0.0 if it broke. This is the
    same `agree` the native loop accumulates (BETA*agree). We build a TWO-member
    manifold IN THE GRAPH whose two members are the SATISFIED vs the still-OPEN
    constraint mass — the confidence interval contracting onto the admissible
    submanifold AS A FRACTION OF THE CONSTRAINTS:

      · the CANDIDATE (admissible)  : lw = BETA * (#agreeing known values, up to the
                         first break) — the mass on the satisfied constraints (the
                         prefix-break is the native left-to-right Γ-prune, exactly
                         collapse_engine.manifold's inner loop);
      · the OPEN twin (residual)    : lw = BETA * (#still-open constraints =
                         n_known - agree_count) — the mass still on the un-collapsed
                         interval. As constraints are satisfied this mass shrinks and
                         the candidate's confidence rises; the two are equal (conf
                         0.5) at half, so a PARTIAL collapse reads a GENUINELY GRADED
                         confidence (not the saturating cand-vs-null degenerate).

    Then the NATIVE Term-trees evaluate the softmax confidence on the candidate:
        mx   = T_MAX_LW   (MaxOver the cand edges of Attr lw)
        Z    = T_Z        (Sum exp(lw - mx))
        conf = T_CONF     (exp(lw_cand - mx) / Z)
    ALL evaluated by the Rust runtime via substrate.evaluate — no Python softmax.
    conf = sigmoid(BETA*(agree - open)) — the native softmax of the two members.

    Returns {confidence, agree_count, n_known, collapsed_root}. A FULL collapse
    (every known value reproduced -> open=0) drives confidence -> 1 (the binary
    PASS, the POINT collapse); a PARTIAL collapse (some reproduced, some open) leaves
    confidence strictly between 0 and 1 (GRADED — rising with the satisfied
    fraction); zero agreement (all open) -> confidence 0.5 then below (a wall / the
    binary FAIL — the interval did not contract onto the candidate)."""
    n_known = len(agreements)
    # PREFIX agreement up to the first break — the native left-to-right Γ-prune
    # (collapse_engine.manifold breaks the agree accumulation at the first 0.0).
    agree_count = 0
    for a in agreements:
        if a <= 0.0:
            break
        agree_count += 1
    open_count = n_known - agree_count        # constraints still on the open interval

    s = substrate if substrate is not None else _native_substrate()

    # Build the manifold AS GRAPH DATA (the native scaffold: ManRoot + Cand edges).
    # The two members are the SATISFIED mass (candidate) vs the still-OPEN mass.
    root = s.add_node("VManRoot", {})
    cand = s.add_node("Cand", {"lw": float(BETA * agree_count)})
    null = s.add_node("Cand", {"lw": float(BETA * open_count)})
    s.add_edge_unchecked(root, "cand", cand)
    s.add_edge_unchecked(root, "cand", null)

    # Evaluate the NATIVE collapse Term-trees IN RUST (no Python softmax).
    mx = float(s.evaluate(T_MAX_LW, {"r": root}))
    Z = float(s.evaluate(T_Z, {"r": root, "mx": mx}))
    conf = float(s.evaluate(T_CONF, {"c": cand, "mx": mx, "Z": Z}))

    # tear down the scratch manifold (no cross-verify state on the shared substrate).
    try:
        s.remove_node(cand)
        s.remove_node(null)
        s.remove_node(root)
    except Exception:                                # noqa: BLE001
        pass

    return {"confidence": conf, "agree_count": agree_count, "n_known": n_known,
            "collapsed_root": root, "cand_node": cand}


def verify_by_collapse(agreements: list[float], *, substrate=None,
                       reason_ok: str = "", reason_partial: str = "",
                       eps: float = 1e-9) -> dict[str, Any]:
    """The verify-against-known guard AS the native collapse — the degenerate
    binary verdict PLUS the graded confidence the binary form could not express.

    `agreements` : the revealed known-value agreements (1.0 match / 0.0 break),
                   one per known (case -> want) constraint.

    Returns the SAME shape the Python verify returned — {verified, reason} — so it
    is a drop-in for elevator/acquire's `verify` hook, AUGMENTED with:
      · confidence  : the native collapsed confidence on the candidate (the GRADED
                      readout — how far the interval contracted; the native payoff);
      · collapsed   : did the interval FULLY contract — the candidate reproduced
                      EVERY revealed known value (the admissible submanifold reached)?
      · partial     : did it contract PARTWAY — some-but-not-all reproduced (graded)?
      · wall        : did it NOT contract at all — no known value reproduced?

    `verified` is the binary degenerate verdict: a FULL contraction onto the
    admissible submanifold = the candidate agrees with EVERY revealed constraint
    (agree_count == n_known) — the SAME boolean the `int(got)!=int(want)` verify
    produced (one mismatch breaks it), now the POINT-COLLAPSE special case of the
    native graded collapse. The `confidence` is the graded contraction the native
    softmax reads (BETA-scaled, so it SATURATES near 1 once a few constraints agree
    — the binary verdict is therefore the FULL-PREFIX test, with confidence the
    continuous readout BENEATH it)."""
    c = collapse_confidence(agreements, substrate=substrate)
    conf = c["confidence"]
    n_known = c["n_known"]
    agree_count = c["agree_count"]
    # FULL collapse onto the admissible submanifold: the candidate reproduced EVERY
    # revealed known value (no prefix break). This IS the binary verify's pass. With
    # NO known values the collapse is vacuously full (the weak "no falsifiable guard"
    # pass the old verify returned).
    full = (agree_count == n_known)
    none_agree = (n_known > 0 and agree_count == 0)
    partial = (not full) and (not none_agree)

    if full:
        reason = reason_ok or (
            f"NATIVE COLLAPSE: confidence -> {conf:.6f} (POINT collapse onto the "
            f"candidate — all {c['n_known']} known values reproduced; the binary "
            f"PASS is this degenerate full contraction)")
    elif partial:
        reason = reason_partial or (
            f"NATIVE PARTIAL COLLAPSE: confidence {conf:.6f} — the candidate "
            f"reproduced {c['agree_count']}/{c['n_known']} known values then BROKE; "
            f"the confidence interval contracted PARTWAY (graded, not a binary "
            f"pass/fail — the native payoff)")
    else:
        reason = (
            f"NATIVE NON-COLLAPSE: confidence {conf:.6f} — the candidate reproduced "
            f"NO known value; the interval did not contract onto it (a wall / the "
            f"binary FAIL as a non-collapse)")

    return {"verified": bool(full), "confidence": conf,
            "collapsed": bool(full), "partial": bool(partial),
            "wall": bool(none_agree),
            "agree_count": c["agree_count"], "n_known": c["n_known"],
            "reason": reason}


# ==========================================================================
# THE ADAPTER — wrap a domain's known-value cases as a COLLAPSE verify. The
# domain supplies, per known case, the (got, want) it would have compared with
# `int(got)!=int(want)`; we turn those into the revealed agreement sequence and
# DELEGATE to the native collapse. This is the drop-in for the elevator/acquire
# `verify(name, caps)` hook.
# ==========================================================================

def make_collapse_verifier(cases: Callable[[str, dict], list[tuple]],
                           *, name_label: Optional[str] = None
                           ) -> Callable[[str, dict], dict[str, Any]]:
    """Build a `verify(name, caps)` that DELEGATES to the native collapse.

    `cases(name, caps)` returns a list of (label, got, want) the guard would have
    checked with `int(got)!=int(want)`. We map each to an agreement (1.0/0.0) — the
    revealed known-value sequence — and run the NATIVE collapse over it. The
    returned dict is the verify result (binary `verified` + graded `confidence` +
    the partial/wall flags).

    This is the unification: the domain still owns WHICH known values to check
    (its falsifiable ground truth); the COLLAPSE (the confidence contraction that
    decides verified) is the ONE native mechanism, not a Python pass/fail loop."""
    def _verify(name: str, caps: dict) -> dict[str, Any]:
        try:
            checks = cases(name, caps)
        except Exception as e:                       # noqa: BLE001
            return {"verified": False, "confidence": 0.0, "collapsed": False,
                    "partial": False, "wall": True,
                    "reason": f"verify cases error: {e}"}
        agreements = [_agree(got, want) for (_lbl, got, want) in checks]
        out = verify_by_collapse(agreements)
        # prepend the failing case to the reason when not a full collapse (parity
        # with the old guard's "b_k(label)=got != known want" diagnostic).
        if not out["collapsed"] and checks:
            ac = out["agree_count"]
            if ac < len(checks):
                lbl, got, want = checks[ac]
                out["reason"] = (f"{name_label or name}: {lbl}={got} != known "
                                 f"{want}  |  " + out["reason"])
        return out
    return _verify


__all__ = [
    "collapse_confidence", "verify_by_collapse", "make_collapse_verifier",
]
