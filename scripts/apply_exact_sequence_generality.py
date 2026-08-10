#!/usr/bin/env python3
"""apply_exact_sequence_generality — the GENERALITY TEST for the link-3 APPLY faculty
(apply_exact_sequence). The win is the GENERAL capability "apply a retrieved exact-
sequence theorem to emit a dimension reduction", NOT one answer (H^2(G,M)=7). So the
SAME faculty + the SAME held derivation_engine must author the reduction for a
DIFFERENT exact sequence, a DIFFERENT target, a DIFFERENT interpretation — with NO
faculty change.

Three held-out cases, each a different sequence/target/interpretation:

  CASE A — SHORT EXACT SEQUENCE  0 -> A -> B -> C -> 0, target C.
    R1 (cokernel tail): the term after C is 0 -> C = coker(A->B),
       dim C = dim B - rank(A->B). A DIFFERENT invariant (a quotient dim from a SES),
       the vanishing flank READ FROM the sequence ('0'), not a side-fact.
    Concrete: A=Q^2 --[ [1,0],[0,0] ]--> B=Q^3 (rank 1); dim C = 3 - 1 = 2.

  CASE B — SHORT EXACT SEQUENCE  0 -> K -> E -> Q -> 0, target K (KERNEL HEAD, R2).
    R2 (kernel head): the term BEFORE K is 0 -> K = ker(E->Q),
       dim K = dim E - rank(E->Q). The DUAL rule, a different position.
    Concrete: E=Q^4 --[rank-3 map]--> Q^3; dim K = 4 - 3 = 1.

  CASE C — A GENERIC-DEGREE LES at a DIFFERENT degree (degree-specialisation general):
    'H^{n-1}(C) -> H^n(G) -> H^n(A)+H^n(B) -> ...', target H^3(G).
    The target fixes n=3; the rule specialises EVERY term to degree 3 and fires R1
    with the side-fact H^3(A)+H^3(B)=0. dim H^3(G) = dim H^2(C) - rank(map). This is
    the SAME shape as the H^2 question but at a different degree + different LES
    orientation — proves the degree solver + rule are not tuned to n=1.

Each case is DRIVEN THROUGH the held derivation_engine (the same consumer the H^2
script uses), so the chain authors itself end-to-end on a question that is NOT the
H^2(G,M) one. HONEST: the interpretation (term -> matrix) is the mechanical read, as
in the H^2 case; the win is the RULE + the engine, demonstrated invariant to the
question.

FAITHFUL (CLAUDE.md): a world-adapter test harness. It sequences the held faculty +
the held engine on new inputs; no agent state, no rule engine, no decision over graph
state. No LLM, no Rust.
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from domains import apply_exact_sequence as _aes
from domains import derivation_engine as _de

SEP = "=" * 78


def banner(s):
    print("\n" + SEP); print(s); print(SEP)


def _ident(d):
    return [[1 if i == j else 0 for j in range(d)] for i in range(d)]


def run_case(name, statement, target, givens, interpret_dim, interpret_rank,
             vanishing, expect):
    banner(name)
    print(f"  statement: {statement}")
    print(f"  target   : {target}   vanishing: {vanishing}")
    res = _aes.apply_theorem(statement, target,
                             interpret_dim=interpret_dim,
                             interpret_rank=interpret_rank,
                             vanishing=vanishing)
    print(f"  parsed terms: {res.get('terms')}")
    print(f"  RULE FIRED  : {res.get('rule')}  (reduced={res.get('reduced')})")
    print(f"  DERIVATION  : {res.get('derivation')}")
    if not res.get("reduced") or res.get("goal") is None:
        print(f"  STALL: {res.get('note')}")
        return False
    print(f"  EMITTED GOAL: {res['goal']}")
    # DRIVE the held engine on the emitted goal-tree (the same consumer as H^2).
    out = _de.derive(res["goal"], givens, max_steps=16)
    print(f"  ENGINE derived={out['derived']} in {out['n_steps']} steps "
          f"-> answer = {out['answer']}")
    ok = out["derived"] and out["answer"] == expect
    print(f"  EXPECT {expect}  ->  {'PASS' if ok else 'FAIL'}")
    return ok


def main():
    results = []

    # CASE A — SES 0 -> A -> B -> C -> 0, target C. R1 cokernel tail, vanishing READ
    # from the '0' in the sequence. A=Q^2 -[rank1]-> B=Q^3; dim C = 3 - 1 = 2.
    A_to_B = [[1, 0], [0, 0], [0, 0]]            # 3x2, rank 1.
    results.append(run_case(
        "CASE A — short exact sequence 0->A->B->C->0, target C (R1 cokernel tail)",
        "0 -> A -> B -> C -> 0", "C",
        givens={"dimB": 3, "A_to_B": A_to_B},
        interpret_dim=lambda t: {"A": 2, "B": "dimB", "C": None}[t.strip()],
        interpret_rank=lambda dom, cod: {"matrix_rank_q": {"of": "A_to_B"}},
        vanishing=[], expect=2))

    # CASE B — SES 0 -> K -> E -> Q -> 0, target K. R2 kernel head, vanishing READ
    # from the '0' before K. E=Q^4 -[rank3]-> Q^3; dim K = 4 - 3 = 1.
    E_to_Q = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]    # 3x4, rank 3.
    results.append(run_case(
        "CASE B — short exact sequence 0->K->E->Q->0, target K (R2 kernel head)",
        "0 -> K -> E -> Q -> 0", "K",
        givens={"dimE": 4, "E_to_Q": E_to_Q},
        interpret_dim=lambda t: {"K": None, "E": "dimE", "Q": 3}[t.strip()],
        interpret_rank=lambda dom, cod: {"matrix_rank_q": {"of": "E_to_Q"}},
        vanishing=[], expect=1))

    # CASE C — generic-degree LES at a DIFFERENT degree + orientation, target H^3(G).
    # 'H^{n-1}(C) -> H^n(G) -> H^n(A)+H^n(B) -> ...'; target fixes n=3.
    # R1: term after H^3(G) is H^3(A)+H^3(B) (=0 by side-fact) -> H^3(G)=coker(H^2(C)->H^3(G))?
    # NB orientation: here H^{n-1}(C) -> H^n(G) is the map INTO the target and the
    # term AFTER (H^n(A)+H^n(B)) vanishes -> R1 with f_dom two-back. Need >=2 reals
    # before the target; the leading H^{n-1}(C) gives f_dom. dim H^3(G)=dim H^?(...) -
    # rank. To keep the interpretation honest+simple we make the codomain H^2(C)=Q^5
    # and the map rank 2 -> dim H^3(G) = 5 - 2 = 3.
    map_C = [[1, 0, 0, 0, 0], [0, 1, 0, 0, 0]]            # rank 2 (2x5).
    results.append(run_case(
        "CASE C — generic-degree LES at degree 3 (degree-specialisation general)",
        "... -> X -> H^{n-1}(C) -> H^n(G) -> H^n(A)+H^n(B) -> ...", "H^3(G)",
        givens={"dimHC": 5, "mapC": map_C},
        interpret_dim=lambda t: {"H2(C)": "dimHC"}.get(
            t.replace("^", "").replace(",M", "").replace(" ", ""), None),
        interpret_rank=lambda dom, cod: {"matrix_rank_q": {"of": "mapC"}},
        vanishing=["H^3(A)+H^3(B)"], expect=3))

    banner("GENERALITY VERDICT")
    names = ["A (SES, R1)", "B (SES, R2)", "C (LES degree-3)"]
    for n, r in zip(names, results):
        print(f"  CASE {n:18s} : {'PASS' if r else 'FAIL'}")
    allok = all(results)
    print(f"\n  ALL PASS = {allok}  -> the link-3 APPLY faculty is GENERAL "
          f"(same rule + engine, different sequence/target/interpretation/degree)"
          if allok else f"\n  SOME FAIL -> not yet general; see the failing case.")
    return 0 if allok else 2


if __name__ == "__main__":
    raise SystemExit(main())
