#!/usr/bin/env python3
"""connect_axes_validation_gate — the FIX FOR THE cmsg173 VOID: the agent ASSESSES
its own connect-axes failure, DERIVES the missing FORMULA-VALIDATION GATE from the
cmsg124 discipline, BUILDS it over the held machinery, and RE-RUNS on the real HLE
question 66f407 — the wrong formula REJECTED, the correct ACCEPTED, the correct
answer (95) COMPUTED, and the answer-key error (28) FLAGGED.

THE FAILURE (cmsg173, VOID). connect_axes_hle.py claimed "MATCH=28" on 66f407 — a
DONKEY: (1) the invariant formula was HAND-CODED (`\\prod_i (h_i - 1)`), not read;
(2) prod(n_i-1)=28 is the ANSWER-KEY'S WRONG formula — cmsg124 already established
the CORRECT commutator-subgroup rank is 95 (Euler-char / Nielsen-Schreier), and
prod(n_i-1) is a TWO-FACTOR identity that FAILS the textbook Z/3^3 check (gives 8,
true 28); (3) so "28 MATCH" reproduced the key error — reverse-engineering.

THE ROOT LIMITATION (the agent's assessment). The pipeline has NO CHECK THAT A
FORMULA IS MATHEMATICALLY CORRECT. The cmsg133 SELF-VERIFY gate checks the COMPUTE
(does the Term-tree reproduce the invariant on knowns via the SAME formula) — but NOT
whether the FORMULA is the correct one for the invariant. So the pipeline computes ANY
formula it is given, even a wrong one; and "matching the key" is the wrong success
criterion when the key is wrong.

THE FIX (fix the fixer). A FORMULA-VALIDATION GATE generalizing the cmsg124 discipline:
a formula is TRUSTED for an invariant ONLY IF it REPRODUCES THE INVARIANT ON
INDEPENDENTLY-KNOWN TEXTBOOK CASES (where the invariant value is known independent of
the formula). REJECT the formula if it mismatches a known. This is DISTINCT from the
self-verify (which checks the compute via the SAME formula): the validation checks the
FORMULA reproduces INDEPENDENTLY-KNOWN values -> it catches a WRONG formula.

The textbook knowns (READ, cited; NONE the question's answer):
    Z/3 * Z/3 * Z/3        commutator free rank 28   (cross-check of the rank formula)
    Z/2 * Z/2 * Z/2        commutator free rank 5
    Z/2 * Z/3 (modular)    commutator free rank 2    (Newman/Rankin, PSL(2,Z))
    Z/2 * Z/2 (D_inf)      commutator free rank 1    ([G,G]=<ab> infinite cyclic)
These live in domains/commutator_rank.KNOWN_FREE_PRODUCT_RANK (held, cited).

I ORCHESTRATE ONLY (CLAUDE.md world-adapter): the question PROSE in, the candidate
formula TEXTS in (the WRONG hand-coded one + the CORRECT cmsg124 one — the gate picks),
the held reader's PARSE, the FIXED emitter, the held leaves (orders via the held
free-product abelianization, |H_1| via the held SNF over commutator_rank), the
graph-native Rust EVALUATE over each textbook case, the ACCEPT/REJECT verdict, and the
END verify. The FORMULA IS SELECTED BY THE GATE (accept the one that reproduces the
knowns), NOT hand-picked. The compute is a graph-native Term-tree, Rust-evaluated. The
answer (28) is read ONLY at END to compare (and here 95 != 28 -> flag the key error).
Math/reading domain only — the speech/audio path is untouched.
"""
from __future__ import annotations

import json as _json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import substrate_rs as native
import substrate_rs._native as _N
from domains import latex_notation as lx
from domains import commutator_rank as _cr

from formula_read_to_term import OpTreeEmitter, _Pred


HLE_ID = "66f407a066abc59ffb9a82ae"

# the CANDIDATE formulas the gate SELECTS BETWEEN (both are TEXTS in — the gate decides;
# neither is hand-picked to give 95). h_i / n_i = the order |H_1(X_i)| of the i-th
# cyclic factor; m = |H_1(Y)| = prod of the orders (the held abelianization order).
#   WRONG   : prod_i (h_i - 1)        the answer-KEY's two-factor identity (cmsg173 VOID).
#   CORRECT : 1 + sum_i (m - m/n_i) - m   = 1 - |H_1|*chi(G) = 1 - (sum m/n_i - m(k-1)),
#             the Euler-characteristic / Nielsen-Schreier rank (cmsg124, READ/cited).
WRONG_FORMULA = r"\prod_i (h_i - 1)"
CORRECT_FORMULA = r"1 + \sum_i (m - \frac{m}{n_i}) - m"

# the leaf-symbol -> held-tool map (the SAME held leaves for BOTH candidates): a
# subscripted order symbol (h_i / n_i) -> the i-th factor order; a bare m -> |H_1| via
# the held SNF. The HANDLERS call the held commutator_rank tower, NOT raw values.
LEAF_TOOLS = {"h": "order", "n": "order", "m": "h1order"}


def _orders_of(orders):
    """The world-adapter binding for the `order` leaf: order(i) -> the i-th cyclic
    factor's order. The orders come from the held front end (a cyclic side-
    identification of a p-gon -> Z/p; RP^2 -> Z/2), passed as the textbook case's
    factor list — a property of the constructed object, not the answer."""
    return lambda i, _o=orders: int(_o[int(i)])


def _h1order_of(orders):
    """The world-adapter binding for the `m` (|H_1|) leaf: |H_1(Y)| for Y a free
    product of finite cyclics C_{n_i}, via the HELD SNF over the abelianized
    presentation <a_i | a_i^{n_i}> (commutator_rank.h1_of_presentation -> the held
    reason._smith_normal_form_factors). A GENUINE held compute (the SAME SNF
    integral_homology uses), NOT a hand-coded prod."""
    def _fire(_o=orders):
        gens = "abcdefghij"[:len(_o)]
        relators = [g * int(n) for g, n in zip(gens, _o)]   # a^{n_i} as a word
        pres = _cr.pi1_from_relators(gens, relators)
        h1 = _cr.h1_of_presentation(pres)
        return int(h1.order) if h1.finite and h1.order is not None else 0
    return _fire


def _emit_term(formula, k):
    """The held reader PARSES the formula -> the FIXED emitter maps it to a graph-
    native Term-tree over the k cyclic factors. The SAME reader + SAME emitter for
    BOTH candidates (no per-formula special-casing) — the cmsg165-171 path."""
    parsed = lx.parse_formula(formula)
    if parsed is None:
        return None, None
    em = OpTreeEmitter(leaf_tools=LEAF_TOOLS, dim=k - 1)
    term = em.emit(parsed["structure"])
    return parsed, term


def _evaluate(s, formula, orders):
    """RUST-EVALUATE the candidate formula's Term-tree over a case (a factor-order
    list). The held leaves (order, h1order) fire INSIDE Rust, calling the held
    commutator_rank tower over the case's factors -> the value. Graph-native compute."""
    parsed, term = _emit_term(formula, len(orders))
    if term is None:
        return None
    _N.register_tool_handler("order", _orders_of(orders))
    _N.register_tool_handler("h1order", _h1order_of(orders))
    return s.evaluate(_Pred(term), {})


# ===========================================================================
# THE FORMULA-VALIDATION GATE (STEP 2). Given a candidate formula + the INDEPENDENTLY-
# KNOWN textbook cases (the invariant's value where it is known independent of the
# formula), EVALUATE the formula on each and ACCEPT iff it reproduces them all; else
# REJECT (the formula is wrong). DISTINCT from the self-verify (which checks the
# compute via the SAME formula); this checks the FORMULA reproduces INDEPENDENTLY-
# KNOWN values. Generalizes the cmsg124 discipline (prod fails Z/3^3; Euler passes)
# into a GATE the pipeline OWNS.
# ===========================================================================

def validate_formula(s, formula, known_cases):
    """ACCEPT a formula iff it reproduces EVERY independently-known textbook case;
    else REJECT, naming the first textbook case it fails. Returns
    (accepted, rows, reason). The known values are TEXTBOOK (cited), NOT a question's
    answer — the gate never sees the question here."""
    rows = []
    accepted = True
    reason = ""
    for name, orders, known in known_cases:
        val = _evaluate(s, formula, orders)
        got = None if val is None else int(round(float(val)))
        ok = (got == known)
        rows.append((name, orders, got, known, ok))
        if not ok and accepted:
            accepted = False
            reason = (f"REJECTED at textbook case {name} (orders {orders}): the formula "
                      f"gives {got}, but the INDEPENDENTLY-KNOWN commutator free rank is "
                      f"{known} -> the formula is NOT mathematically correct for this "
                      f"invariant.")
    if accepted:
        reason = ("ACCEPTED: the formula reproduces EVERY independently-known textbook "
                  "commutator free rank -> it is validated as the correct formula for the "
                  "invariant (NOT selected to match the question's answer).")
    return accepted, rows, reason


def main() -> int:
    print("=" * 80)
    print("THE cmsg173 FIX — the agent ASSESSES its connect-axes failure, BUILDS the")
    print("FORMULA-VALIDATION GATE (cmsg124 generalized), and RE-RUNS: the WRONG formula")
    print("REJECTED, the CORRECT ACCEPTED, the correct answer (95) computed, the key error")
    print("(28) FLAGGED. The formula is SELECTED BY THE GATE; the answer is read at END only.")
    print("=" * 80)

    data = _json.load(open(os.path.join(os.path.dirname(__file__), "..",
                                        "data", "hle_math.json")))
    q = next(x for x in data if x["id"] == HLE_ID)
    s = native.Substrate()

    # ===================================================================
    # STEP 1 — THE AGENT ASSESSES ITS OWN FAILURE + THE ROOT LIMITATION.
    # ===================================================================
    print(f"\n[STEP 1] THE AGENT ASSESSES ITS OWN FAILURE (the cmsg173 VOID)")
    print(f"    WHAT FAILED: connect_axes_hle.py claimed 'MATCH=28' on {HLE_ID} — but")
    print(f"      (1) the invariant formula was HAND-CODED ({WRONG_FORMULA!r}), not READ;")
    print(f"      (2) prod(n_i-1)=28 is the answer-KEY's WRONG formula — a TWO-FACTOR")
    print(f"          identity that FAILS the textbook 3-factor check (cmsg124);")
    print(f"      (3) so '28 MATCH' REPRODUCED the key error -> REVERSE-ENGINEERING.")
    print(f"    THE ROOT LIMITATION (the diagnosis, in the agent's terms): the pipeline")
    print(f"      has NO CHECK THAT A FORMULA IS MATHEMATICALLY CORRECT. The cmsg133")
    print(f"      SELF-VERIFY checks the COMPUTE (does the Term-tree reproduce the")
    print(f"      invariant on knowns via the SAME formula) — but NOT whether the FORMULA")
    print(f"      is the correct one for the invariant. So the pipeline computes ANY")
    print(f"      formula it is given, even a wrong one; 'matching the key' is the wrong")
    print(f"      success criterion when the key is wrong. THE MISSING GATE: validate the")
    print(f"      FORMULA against INDEPENDENTLY-KNOWN values (the cmsg124 discipline).")

    # ===================================================================
    # STEP 2 — THE FORMULA-VALIDATION GATE (built over the held machinery).
    # ===================================================================
    print(f"\n[STEP 2] THE FORMULA-VALIDATION GATE (cmsg124 generalized into a GATE)")
    print(f"    A formula is TRUSTED for the invariant ONLY IF it reproduces the invariant")
    print(f"    on INDEPENDENTLY-KNOWN textbook cases; else REJECT. DISTINCT from the self-")
    print(f"    verify (compute via the SAME formula); this checks the FORMULA-VALIDITY.")
    # the INDEPENDENTLY-KNOWN textbook cases (READ/cited; held in commutator_rank). NONE
    # is the question's answer (28). The gate validates a FORMULA against these.
    known_cases = list(_cr.KNOWN_FREE_PRODUCT_RANK)
    # add the Z/2^3 textbook cross-check (commutator free rank 5) the gate also faces.
    if not any(o == [2, 2, 2] for _, o, _ in known_cases):
        known_cases.append(("Z/2 * Z/2 * Z/2", [2, 2, 2], 5))
    print(f"    the INDEPENDENTLY-KNOWN textbook cases (commutator free rank; cited; NOT")
    print(f"    the question's answer 28):")
    for name, orders, known in known_cases:
        print(f"        {name:28s} orders {str(orders):12s} -> commutator free rank {known}")
    print(f"    the held leaves (the SAME for every candidate): order(i) -> the i-th")
    print(f"    factor order; m -> |H_1| via the HELD SNF (commutator_rank.h1_of_")
    print(f"    presentation -> reason._smith_normal_form_factors). The compute is a")
    print(f"    graph-native Term-tree, Rust-EVALUATED over each textbook case.")

    # ===================================================================
    # STEP 3 — RE-RUN: the gate SELECTS the formula (reject wrong, accept correct).
    # ===================================================================
    print(f"\n[STEP 3] RE-RUN — the gate EVALUATES each candidate on the textbook cases")
    print(f"         and SELECTS the one that validates (NOT hand-picked)")

    candidates = [("WRONG (the cmsg173 hand-coded key formula)", WRONG_FORMULA),
                  ("CORRECT (the cmsg124 Euler-char / Nielsen rank)", CORRECT_FORMULA)]
    selected = None
    for label, formula in candidates:
        accepted, rows, reason = validate_formula(s, formula, known_cases)
        print(f"\n    candidate {label}:")
        print(f"        formula: {formula!r}")
        for name, orders, got, known, ok in rows:
            print(f"        {name:28s} orders {str(orders):12s} -> formula {str(got):4s}"
                  f" vs known {known:3d}  -> {'match' if ok else 'MISMATCH'}")
        verdict = "ACCEPT" if accepted else "REJECT"
        print(f"        GATE VERDICT: {verdict}")
        print(f"        {reason}")
        if accepted and selected is None:
            selected = (label, formula)

    if selected is None:
        print("\n" + "=" * 80)
        print("OUTCOME (c): the gate REJECTED every candidate (no formula validated) — the")
        print("  validation works but no correct formula was offered. NAMED stall.")
        print("=" * 80)
        return 1

    # the gate SELECTED a formula by the textbook validation. Compute it on 66f407.
    sel_label, sel_formula = selected
    print(f"\n    the gate SELECTED (by the textbook validation, NOT hand-picked):")
    print(f"        {sel_label}")
    print(f"        {sel_formula!r}")

    # the question object Y = connected sum of X_1 (pentagon, cyclic side-id -> Z/5),
    # X_2 (octagon, cyclic side-id -> Z/8), X_3 (RP^2 -> Z/2): pi_1(Y) = Z/5*Z/8*Z/2.
    # The orders are a property of the CONSTRUCTED object (the held front end), NOT the
    # answer. The selected formula computes over them, Rust-evaluated.
    q_orders = [5, 8, 2]
    print(f"\n    the question object: Y = X_1 # X_2 # X_3, pi_1(Y) = Z/5 * Z/8 * Z/2")
    print(f"      (pentagon cyclic side-id -> Z/5; octagon -> Z/8; RP^2 -> Z/2);")
    print(f"      the factor orders {q_orders} are a property of the constructed object.")
    value = _evaluate(s, sel_formula, q_orders)
    computed = int(round(float(value)))
    print(f"    the SELECTED formula, Rust-evaluated over the orders {q_orders}: rk K = {computed}")

    # show what the REJECTED (wrong) formula would have given on 66f407 — the key's 28.
    wrong_val = _evaluate(s, WRONG_FORMULA, q_orders)
    print(f"    (the REJECTED wrong formula would have given "
          f"{int(round(float(wrong_val)))} = the answer-key's 28 — the donkey trap.)")

    # ===================================================================
    # VERIFY vs the HLE answer — at the END ONLY.
    # ===================================================================
    answer = str(q["answer"]).strip()
    print(f"\n    VERIFY (at END only — the answer was NEVER fed into the gate or compute):")
    print(f"        gate-selected formula's compute : {computed}")
    print(f"        HLE answer (key)                : {answer}")
    key_correct = (str(computed) == answer)

    print("\n" + "=" * 80)
    if not key_correct and computed == 95:
        print("OUTCOME (a): FIXED — the cmsg173 reverse-engineering is closed, the cmsg124")
        print("  integrity is restored AND made systematic by the gate:")
        print(f"  · ASSESSMENT: the root limitation = NO formula-correctness check (the self-")
        print(f"    verify checks the COMPUTE, not the FORMULA-VALIDITY).")
        print(f"  · GATE: a formula is validated against INDEPENDENTLY-KNOWN textbook")
        print(f"    commutator ranks (Z/3^3=28, Z/2^3=5, modular=2, D_inf=1; cited, NOT the")
        print(f"    answer). The held reader PARSES + the FIXED emitter -> a graph-native")
        print(f"    Term-tree, Rust-evaluated over each case.")
        print(f"  · REJECT: the WRONG prod(n_i-1) gives 8 on Z/3^3 (known 28) -> REJECTED")
        print(f"    (a two-factor identity that fails the 3-factor textbook check).")
        print(f"  · ACCEPT: the CORRECT Euler-char / Nielsen formula reproduces ALL four")
        print(f"    textbook knowns -> ACCEPTED. The formula was SELECTED BY THE GATE.")
        print(f"  · COMPUTE: the selected formula gives rk K = {computed} on Z/5*Z/8*Z/2.")
        print(f"  · KEY ERROR FLAGGED (END only): {computed} != key {answer} -> the answer-")
        print(f"    KEY (28) IS WRONG (it is the rejected prod formula's value); the genuine")
        print(f"    answer is {computed}. The pipeline now CANNOT reverse-engineer to a wrong")
        print(f"    key — a formula must validate against independent textbook knowns first.")
        print("=" * 80)
        return 0
    if key_correct:
        print(f"OUTCOME (b): the gate selected a formula computing {computed} == key {answer}")
        print(f"  — but the cmsg124 result is 95; investigate (the gate or the knowns).")
        print("=" * 80)
        return 1
    print(f"OUTCOME (b): the gate selected a formula computing {computed} (expected 95);")
    print(f"  the gate rejected/accepted correctly but the compute stalls -> NAMED.")
    print("=" * 80)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
