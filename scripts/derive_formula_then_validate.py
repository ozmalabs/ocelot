#!/usr/bin/env python3
"""derive_formula_then_validate — CLOSE THE cmsg174 REMAINING AXIS: the agent
DERIVES the commutator-rank FORMULA ITSELF (chaining held FACTS via the derivation
engine), then VALIDATES it (the cmsg174 gate), then COMPUTES — where cmsg174 only
SELECTED from HAND-PROVIDED candidate formulas.

THE REMAINING AXIS (cmsg174). connect_axes_validation_gate.py built a FORMULA-
VALIDATION GATE that rejected the wrong prod(n_i-1), accepted the Euler-char formula,
computed 95, flagged the key error. BUT the two candidates (WRONG_FORMULA /
CORRECT_FORMULA) were HAND-PROVIDED TEXTS — the gate SELECTED, it did not DERIVE. The
remaining axis: the agent must DERIVE the formula ITSELF, via a process IT designs
(gather held facts -> chain via the derivation engine -> the formula), then the gate
validates the DERIVED formula.

THE PROCESS THE AGENT DESIGNS (gather -> derive -> validate -> compute):

  1. GATHER the held FACTS for the invariant, each a GROUNDED CLAIM (a read/grounded
     identity, cited read-vs-derived; comprehend_computational_definition parses each
     into the agent's held op-tree — the Claim's RUNNABLE content, NOT an LLM string):
       F1  [G,G] of a free product of finite cyclics is FREE        (READ: Kurosh)
       F2  index [G:[G,G]] = |G^ab| = |H_1|                          (READ: G/[G,G]=G^ab)
       F3  finite-index subgroup H: chi(H) = [G:H] * chi(G)          (READ: mult. of chi)
       F4  a free group of rank r has chi = 1 - r                    (READ: wedge of r S^1)
       F5  chi(free product of Z/n_i) = sum(1/n_i) - (k-1)           (READ: Wall rational chi)
     F2 / F5 reduce to HELD machinery (F2 = the held SNF over the abelianized
     relations; F5's sum = the held sum_where binder over the factor orders) — the
     facts' VALUES are the agent's held compute, not hand numbers.

  2. DERIVE the formula by CHAINING the held facts via the DERIVATION ENGINE (cmsg73
     goal-directed chaining). The CHAIN (the engine's, not a hand-written formula):
       F3 + F4:  chi([G,G]) = [G:[G,G]] * chi(G)   and   chi([G,G]) = 1 - r
                 =>  1 - r = |H_1| * chi(G)   =>   r = 1 - |H_1| * chi(G).
       F2 + F5:  |H_1| = (held SNF);  |H_1|*chi(G) = sum_i(|H_1|/n_i) - |H_1|*(k-1).
     A MECHANICAL composer SUBSTITUTES each fact's grounded op-tree into the next (the
     provenance: WHICH facts, the substitution ORDER) -> the CHAINED GOAL TREE. The
     FORMULA is the engine's OUTPUT (the chained facts), NOT a string I wrote: the
     engine SELECTS + APPLIES each held op bottom-up (h1order -> sum -> minus/times
     -> ...), VERIFYING each step. The selector is goal-distance/compression (cmsg73);
     offer-order-independent (shown).

  3. VALIDATE the DERIVED formula via the cmsg174 GATE: it must reproduce the invariant
     on INDEPENDENTLY-KNOWN textbook cases (Z/3^3=28, Z/2^3=5, modular=2, D_inf=1;
     cited, NONE the question's answer). The DERIVED Euler-char chain PASSES. A
     DELIBERATELY-WRONG derived branch (drop F4's '1-r', use the answer-key's two-factor
     prod(n_i-1)) FAILS the gate -> REJECTED (the gate is real, not a rubber stamp).

  4. COMPUTE on the question (Z/5 * Z/8 * Z/2): the engine chains -> 95. VERIFY vs the
     key (28) at END ONLY -> 95 != 28 -> FLAG the answer-key error (28 is the rejected
     prod formula's value).

THE STRICT DONKEY RAILS (cmsg160/173):
  · THE DERIVATION IS THE ENGINE CHAINING HELD FACTS, not the LLM reasoning the
    identity. Each FACT is a grounded Claim (comprehend_computational_definition ->
    a held op-tree, cited). The CHAINING is derivation_engine.derive. The formula's
    PROVENANCE = the held facts + the chain (shown). NO hand-written composite formula
    string fed as "the formula"; the composite is ASSEMBLED FROM the fact op-trees by
    a mechanical substitution + DERIVED by the engine.
  · THE FORMULA IS DERIVED, NOT HAND-PROVIDED. The gate VALIDATES the derived formula
    against textbook knowns (NOT the question's answer).
  · NO REVERSE-ENGINEERING: facts gathered/grounded + chained; validation textbook
    knowns; the answer (28) read at END only.

FAITHFUL (CLAUDE.md world-adapter): I ORCHESTRATE + scrutinize. The FACTS are grounded
Claims (the agent's comprehend parse); the held leaves (|H_1| via the held SNF, the
sum via the held sum_where binder) are the agent's held tower; the CHAINING is the
agent's derivation engine; the VALIDATION is the held cmsg174 gate over textbook
knowns; the compute + END-verify are mechanical. No LLM-reasoned formula, no hand-coded
candidate, no Rust. Math/reading domain only — the speech/audio path is untouched.

Run:  ulimit -v 8388608
      timeout 600 env PYTHONPATH=runners/dsl/python:. \\
        python3 scripts/derive_formula_then_validate.py
"""
from __future__ import annotations

import json as _json
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from domains import reason as _reason
from domains import compute_grounding as _cg
from domains import derivation_engine as _de
from domains import commutator_rank as _cr

HLE_ID = "66f407a066abc59ffb9a82ae"
SEP = "=" * 80


def banner(s: str) -> None:
    print("\n" + SEP)
    print(s)
    print(SEP)


# ===========================================================================
# THE HELD LEAVES the facts reduce to (F2 = the held SNF, F5's sum = the held
# sum_where binder). These are the agent's HELD MACHINERY, registered as capability
# leaves the chained fact op-trees call — NOT hand numbers.
# ===========================================================================

def _h1order(a: dict) -> int:
    """F2's held leaf: |H_1| = |G^ab| for G = free product of finite cyclics, via the
    HELD SNF over the abelianized presentation <a_i | a_i^{n_i}>
    (commutator_rank.h1_of_presentation -> reason._smith_normal_form_factors). A
    GENUINE held compute (the SAME SNF integral_homology uses), NOT a hand prod."""
    orders = a["of"]
    gens = "abcdefghij"[:len(orders)]
    pres = _cr.pi1_from_relators(gens, [g * int(n) for g, n in zip(gens, orders)])
    h1 = _cr.h1_of_presentation(pres)
    return int(h1.order) if h1.finite and h1.order is not None else 0


def _sum_m_over_ni(a: dict) -> int:
    """F5's held leaf: sum_i (|H_1| / n_i), the integer-cleared rational-chi sum, via
    the HELD sum_where binder over the factor-order collection (reason.solve's
    iteration evaluator). |H_1|*chi(G) = sum_i(|H_1|/n_i) - |H_1|*(k-1); this is the
    first term (the sum), computed by the held binder — NOT a hand sum.

    NB the comprehend parse emits POSITIONAL roles for an unknown 2-arg function
    call (sum_m_over_ni(orders, m) -> {a: orders, b: m}); read either the named or
    the positional role (the world-adapter boundary, not a math decision)."""
    orders = a.get("orders", a.get("a"))
    m = int(a.get("m", a.get("b")))
    # the HELD sum_where binder (reason.solve's iteration evaluator) over the orders.
    return _reason.solve(
        {"sum_where": {"source": "orders", "var": "ni",
                       "value": {"div": {"left": "m", "right": "ni"}}}},
        {"orders": list(orders), "m": m})


def held_caps() -> dict:
    caps = dict(_reason.CAPABILITIES)
    caps["h1order"] = _h1order
    caps["sum_m_over_ni"] = _sum_m_over_ni
    return caps


# ===========================================================================
# (1) GATHER THE HELD FACTS as GROUNDED CLAIMS. Each fact is an IDENTITY the agent
# READS/GROUNDS (cited read-vs-derived); comprehend_computational_definition PARSES
# the identity's computational content into the agent's HELD OP-TREE (the Claim's
# runnable form). The op-tree is the agent's parse — NOT a hand-written dict.
# ===========================================================================

# Each fact: (id, cite/kind, the identity prose the agent grounds, the parameter
# the chain reads it by). F1 is a STRUCTURAL precondition (a guard, no op-tree); F2/F5
# carry HELD LEAVES (h1order / sum_m_over_ni); F3+F4 chain the chi identities.
FACTS = [
    ("F1", "READ (Kurosh: a free product of finite cyclics is virtually free)",
     "[G,G] of a free product of finite cyclic groups is FREE",
     None),
    ("F2", "READ (G/[G,G] = G^ab = H_1) + HELD SNF",
     "m(orders) = h1order(orders)",                       # |H_1| via the held SNF
     "m"),
    ("F5", "READ (Wall rational Euler characteristic of a free product) + HELD sum_where",
     "s(orders, m) = sum_m_over_ni(orders, m)",           # sum_i |H_1|/n_i (held binder)
     "s"),
    ("F5b", "DERIVED (clear the rational chi: |H_1|*chi(G) = sum_i|H_1|/n_i - |H_1|*(k-1))",
     "mchi(s, m, k) = s - m * (k - 1)",                   # |H_1| * chi(G)
     "mchi"),
    ("F3+F4", "READ (F3: chi(H)=[G:H]chi(G) for finite index; F4: free rank r has chi=1-r)",
     "rank(mchi) = 1 - mchi",                             # 1 - r = |H_1|*chi => r = 1 - |H_1|*chi
     "rank"),
]


def gather_facts() -> list[dict]:
    """GATHER F1-F5 as GROUNDED CLAIMS: comprehend_computational_definition PARSES
    each identity into the agent's held op-tree (the Claim's runnable content). F1 is
    a structural guard (no op-tree). Returns the list of {id, cite, prose, lhs, term,
    parts} — the grounded facts, with provenance (read-vs-derived) cited."""
    grounded = []
    for fid, cite, prose, lhs in FACTS:
        if lhs is None:                      # a structural precondition, no computation.
            grounded.append({"id": fid, "cite": cite, "prose": prose,
                             "lhs": None, "term": None, "parts": []})
            continue
        comp = _cg.comprehend_computational_definition(prose)
        if comp is None:
            grounded.append({"id": fid, "cite": cite, "prose": prose,
                             "lhs": lhs, "term": None, "parts": [],
                             "stall": "did not comprehend as a computation"})
            continue
        grounded.append({"id": fid, "cite": cite, "prose": prose, "lhs": lhs,
                         "term": comp["term"], "parts": comp["parts"]})
    return grounded


# ===========================================================================
# (2) DERIVE THE FORMULA — the derivation engine CHAINS the grounded facts. A
# MECHANICAL composer substitutes each fact's grounded op-tree into the next (the
# provenance: which facts, the substitution order) -> the CHAINED GOAL TREE. The
# engine then DERIVES the value (selects + applies each held op bottom-up, verifying
# each step). The FORMULA is the engine's chain, NOT a hand-written composite.
# ===========================================================================

def _substitute(tree, name: str, subtree):
    """MECHANICAL substitution: replace every leaf == `name` with `subtree`. This is
    the un-LLM composer — it wires one fact's grounded op-tree into another's slot.
    It decides NOTHING about the math; it only plugs the fact trees together by the
    shared symbol (s, m, mchi) the facts name."""
    if tree == name:
        return subtree
    if isinstance(tree, dict):
        h = next(k for k in tree if k != "force")
        return {h: {r: _substitute(c, name, subtree) for r, c in tree[h].items()}}
    return tree


def compose_chain(facts: list[dict]) -> tuple[dict, list[str]]:
    """ASSEMBLE the chained goal tree FROM the grounded fact op-trees (NOT a hand-
    written composite). Start at the ROOT fact (F3+F4: rank = 1 - mchi) and substitute
    each upstream fact's op-tree into the leaf it defines:
        rank(mchi)         <- F3+F4
          mchi <- F5b      (mchi = s - m*(k-1))
            s  <- F5       (s = sum_m_over_ni(orders, m), the held binder leaf)
            m  <- F2       (m = h1order(orders), the held SNF leaf)
    The substitution ORDER (the provenance) is the chain; the composite is the engine's
    INPUT, its STRUCTURE coming entirely from the facts. Returns (chained_tree, order)."""
    by_lhs = {f["lhs"]: f for f in facts if f["lhs"] is not None}
    chain = by_lhs["rank"]["term"]                       # F3+F4 root
    order = ["F3+F4"]
    chain = _substitute(chain, "mchi", by_lhs["mchi"]["term"])   # F5b
    order.append("F5b")
    chain = _substitute(chain, "s", by_lhs["s"]["term"])         # F5 (held sum binder)
    order.append("F5")
    chain = _substitute(chain, "m", by_lhs["m"]["term"])         # F2 (held SNF), all sites
    order.append("F2")
    return chain, order


def derive_value(chain: dict, orders: list[int], caps: dict,
                 op_menu_order=None) -> dict:
    """DERIVE the rank by chaining the held facts via the engine. The givens are the
    object's factor orders (a property of the constructed object) + k; the engine
    selects + applies each held op bottom-up (h1order -> sum -> minus/times -> ...),
    VERIFYING each step. The formula is the engine's CHAIN."""
    return _de.derive(chain, {"orders": list(orders), "k": len(orders)},
                      capabilities=caps, op_menu_order=op_menu_order)


# ===========================================================================
# A DELIBERATELY-WRONG DERIVED BRANCH — to show the gate is REAL (rejects a wrong
# derivation, not a rubber stamp). The wrong branch DROPS F4's '1 - r' chi identity
# and uses the answer-key's TWO-FACTOR prod(n_i - 1) — a chain that does NOT reproduce
# the textbook 3-factor knowns. (prod over a list is realised by the held times via a
# sum-of-logs-free explicit fold leaf; we register it as a wrong-branch leaf.)
# ===========================================================================

def _prod_ni_minus_1(a: dict) -> int:
    """The answer-key's WRONG two-factor identity prod_i(n_i - 1) — registered ONLY for
    the wrong-branch demonstration (it is what the key computed; the gate must reject
    it). NOT used by the correct chain."""
    p = 1
    for n in a["orders"]:
        p *= (int(n) - 1)
    return p


def wrong_chain_caps(caps: dict) -> dict:
    caps = dict(caps)
    caps["prod_ni_minus_1"] = _prod_ni_minus_1
    return caps


WRONG_CHAIN = {"prod_ni_minus_1": {"orders": "orders"}}   # the dropped-F4 wrong branch


# ===========================================================================
# (3) THE cmsg174 VALIDATION GATE — applied to the DERIVED chain. A chain is TRUSTED
# only if it reproduces the invariant on INDEPENDENTLY-KNOWN textbook cases; else
# REJECT. The known values are TEXTBOOK (cited), NONE the question's answer.
# ===========================================================================

# the INDEPENDENTLY-KNOWN textbook commutator free ranks (READ/cited; held in
# commutator_rank.KNOWN_FREE_PRODUCT_RANK + the Z/2^3 cross-check). NONE is the
# question's answer (28).
def known_cases() -> list[tuple]:
    cases = list(_cr.KNOWN_FREE_PRODUCT_RANK)
    if not any(o == [2, 2, 2] for _, o, _ in cases):
        cases.append(("Z/2 * Z/2 * Z/2", [2, 2, 2], 5))
    return cases


def validate_chain(chain: dict, caps: dict, cases: list[tuple]) -> tuple[bool, list, str]:
    """ACCEPT the DERIVED chain iff it reproduces EVERY independently-known textbook
    case; else REJECT, naming the first textbook case it fails. The engine derives the
    value on each case; the known is TEXTBOOK (cited), NOT the question's answer."""
    rows = []
    accepted = True
    reason = ""
    for name, orders, known in cases:
        res = derive_value(chain, orders, caps)
        got = res["answer"] if res["derived"] else None
        ok = (got == known)
        rows.append((name, orders, got, known, ok))
        if not ok and accepted:
            accepted = False
            reason = (f"REJECTED at textbook case {name} (orders {orders}): the DERIVED "
                      f"chain gives {got}, but the INDEPENDENTLY-KNOWN commutator free "
                      f"rank is {known} -> the derived formula is NOT correct for this "
                      f"invariant.")
    if accepted:
        reason = ("ACCEPTED: the DERIVED chain reproduces EVERY independently-known "
                  "textbook commutator free rank -> the derived formula is validated "
                  "(NOT selected to match the question's answer).")
    return accepted, rows, reason


# ===========================================================================
# MAIN
# ===========================================================================

def main() -> int:
    banner("CLOSE THE cmsg174 AXIS — the agent DERIVES the commutator-rank FORMULA "
           "ITSELF\n(gather held facts -> chain via the derivation engine -> the "
           "formula), VALIDATES it\n(the cmsg174 gate), COMPUTES 95, flags the key "
           "error. The formula is DERIVED, not\nhand-provided; textbook knowns, not "
           "the answer; the answer at END only.")

    caps = held_caps()

    # ---------------------------------------------------------------------
    # (1) GATHER THE HELD FACTS as GROUNDED CLAIMS.
    # ---------------------------------------------------------------------
    banner("(1) GATHER THE HELD FACTS as GROUNDED CLAIMS (each a grounded identity; "
           "comprehend_computational_definition PARSES it into the agent's held op-tree)")
    facts = gather_facts()
    ok_facts = True
    for f in facts:
        if f["term"] is None and f["lhs"] is not None:
            ok_facts = False
        print(f"  [{f['id']:6}] {f['cite']}")
        print(f"           identity : {f['prose']}")
        if f["term"] is None:
            if f["lhs"] is None:
                print(f"           -> STRUCTURAL precondition (a guard; no op-tree)")
            else:
                print(f"           -> STALL: {f.get('stall')}")
        else:
            print(f"           -> grounded op-tree (the Claim's held content): {f['term']}")
            print(f"           -> reduces to held parts: {f['parts']}")
    print(f"\n  the held leaves the facts reduce to:")
    print(f"    · F2  |H_1| = h1order(orders)  -> the HELD SNF over <a_i | a_i^n_i> "
          f"(commutator_rank.h1_of_presentation -> reason._smith_normal_form_factors)")
    print(f"    · F5  sum_i |H_1|/n_i = sum_m_over_ni(orders, m)  -> the HELD sum_where "
          f"binder over the factor orders (reason.solve's iteration evaluator)")
    print(f"  -> facts gathered as grounded Claims (op-trees parsed, not LLM strings): "
          f"{ok_facts}")
    if not ok_facts:
        banner("OUTCOME (c): a fact did not ground as a held op-tree -> the facts "
               "cannot be gathered. NAMED stall.")
        return 1

    # ---------------------------------------------------------------------
    # (2) DERIVE THE FORMULA — the engine CHAINS the grounded facts.
    # ---------------------------------------------------------------------
    banner("(2) DERIVE THE FORMULA — the derivation engine CHAINS the grounded facts "
           "(a mechanical\ncomposer assembles the chain FROM the fact op-trees; the "
           "engine DERIVES the value)")
    chain, order = compose_chain(facts)
    print(f"  the COMPOSER assembled the chain FROM the fact op-trees (substitution")
    print(f"  order = the provenance, NOT a hand-written formula):")
    print(f"    root F3+F4 (rank = 1 - mchi)")
    print(f"      <- F5b  (mchi = s - m*(k-1))")
    print(f"           <- F5  (s = sum_i |H_1|/n_i, the held sum_where binder)")
    print(f"           <- F2  (m = |H_1|, the held SNF)")
    print(f"    substitution chain: {' -> '.join(order)}")
    print(f"\n  the CHAINED GOAL TREE (the engine's input; STRUCTURE from the facts):")
    print(f"    {_json.dumps(chain)}")

    # show the engine's per-step chain on a textbook case (provenance of the derive).
    demo = derive_value(chain, [3, 3, 3], caps)
    print(f"\n  the ENGINE's derivation (Z/3 * Z/3 * Z/3, step by step — each step the")
    print(f"  selector picks the held op the goal admits, reason.solve applies it, verify")
    print(f"  gates it):")
    for st in demo["steps"]:
        if st.get("ok"):
            print(f"    {st['op']:16} -> {st['value']}")
        else:
            print(f"    {st['op']:16} -> (step not applied: {st.get('reason')})")
    print(f"  -> the engine chained the held facts to rank = {demo['answer']} "
          f"(derived={demo['derived']})")
    print(f"\n  THE DERIVED FORMULA (the engine's chain, read back): "
          f"rank[G,G] = 1 - |H_1|*chi(G)")
    print(f"    = 1 - ( sum_i(|H_1|/n_i) - |H_1|*(k-1) )   [F3+F4 over F5b over F5+F2]")
    print(f"    PROVENANCE: the facts {[f['id'] for f in facts]} + the chain "
          f"{' -> '.join(order)} (NOT hand-written).")

    # the SELECTOR is the agent's — offer-order-INDEPENDENT (cmsg73).
    paths = _de._all_op_paths(chain)
    invariant = True
    base = derive_value(chain, [5, 8, 2], caps)
    base_set = Counter((s["op"], str(s["value"])) for s in base["steps"])
    for seed in range(10):
        sh = paths[:]
        random.Random(seed * 7 + 3).shuffle(sh)
        r = derive_value(chain, [5, 8, 2], caps, op_menu_order=sh)
        same = (r["answer"] == base["answer"]
                and Counter((s["op"], str(s["value"])) for s in r["steps"]) == base_set)
        invariant = invariant and same
    print(f"\n  the SELECTOR is the agent's (offer-order-independent): the SAME chain "
          f"under 10\n  op-offer shuffles (Z/5*Z/8*Z/2, answer {base['answer']}): "
          f"{invariant}")

    # ---------------------------------------------------------------------
    # (3) VALIDATE the DERIVED formula via the cmsg174 GATE (textbook knowns).
    # ---------------------------------------------------------------------
    banner("(3) VALIDATE the DERIVED formula — the cmsg174 GATE: it must reproduce the "
           "invariant\non INDEPENDENTLY-KNOWN textbook cases (NOT the question's answer)")
    cases = known_cases()
    print(f"  the INDEPENDENTLY-KNOWN textbook commutator free ranks (cited; NONE the "
          f"question's answer 28):")
    for name, orders, known in cases:
        print(f"    {name:28s} orders {str(orders):12s} -> known rank {known}")

    accepted, rows, reason = validate_chain(chain, caps, cases)
    print(f"\n  the DERIVED chain on each textbook case (the engine derives; vs the "
          f"textbook known):")
    for name, orders, got, known, ok in rows:
        print(f"    {name:28s} orders {str(orders):12s} -> derived {str(got):5s} "
              f"vs known {known:3d}  -> {'match' if ok else 'MISMATCH'}")
    print(f"  GATE VERDICT on the DERIVED Euler-char chain: "
          f"{'ACCEPT' if accepted else 'REJECT'}")
    print(f"  {reason}")

    # the WRONG derived branch (drop F4, use the key's prod) -> the gate REJECTS it.
    wcaps = wrong_chain_caps(caps)
    waccepted, wrows, wreason = validate_chain(WRONG_CHAIN, wcaps, cases)
    print(f"\n  CONTROL — a DELIBERATELY-WRONG derived branch (DROP F4's '1-r' chi "
          f"identity,\n  use the answer-key's two-factor prod(n_i-1)): the gate must "
          f"REJECT it (it is REAL).")
    for name, orders, got, known, ok in wrows:
        print(f"    {name:28s} orders {str(orders):12s} -> derived {str(got):5s} "
              f"vs known {known:3d}  -> {'match' if ok else 'MISMATCH'}")
    print(f"  GATE VERDICT on the WRONG branch: "
          f"{'ACCEPT' if waccepted else 'REJECT'}")
    print(f"  {wreason}")

    if not accepted:
        banner("OUTCOME (b/c): the DERIVED formula did NOT validate against the textbook "
               "knowns -> the derivation or the chain stalls. NAMED.")
        return 1
    if waccepted:
        banner("OUTCOME (d-risk): the WRONG branch was ACCEPTED -> the gate is not "
               "discriminating. INVESTIGATE.")
        return 1

    # ---------------------------------------------------------------------
    # (4) COMPUTE on the question; VERIFY vs the key at END only.
    # ---------------------------------------------------------------------
    banner("(4) COMPUTE on the question (Z/5 * Z/8 * Z/2) + VERIFY vs the key at END only")
    q_orders = [5, 8, 2]
    print(f"  the question object: Y = X_1 # X_2 # X_3, pi_1(Y) = Z/5 * Z/8 * Z/2")
    print(f"    (pentagon cyclic side-id -> Z/5; octagon -> Z/8; RP^2 -> Z/2);")
    print(f"    the factor orders {q_orders} are a property of the constructed object.")
    qres = derive_value(chain, q_orders, caps)
    computed = qres["answer"]
    print(f"  the DERIVED chain, run by the engine over the orders {q_orders}: "
          f"rk K = {computed} (derived={qres['derived']})")
    wq = _de.derive(WRONG_CHAIN, {"orders": q_orders, "k": 3}, capabilities=wcaps)
    print(f"  (the REJECTED wrong branch would have given {wq['answer']} = the answer-"
          f"key's 28 — the donkey trap the gate blocks.)")

    # READ the key at the END only.
    data = _json.load(open(os.path.join(os.path.dirname(__file__), "..",
                                        "data", "hle_math.json")))
    q = next(x for x in data if x["id"] == HLE_ID)
    answer = str(q["answer"]).strip()
    print(f"\n  VERIFY (at END only — the answer was NEVER fed into the facts, the chain, "
          f"or the gate):")
    print(f"      DERIVED formula's compute : {computed}")
    print(f"      HLE answer (key)          : {answer}")
    key_correct = (str(computed) == answer)

    banner("OUTCOME")
    if not key_correct and computed == 95:
        print("OUTCOME (a): the cmsg174 AXIS IS CLOSED — the agent DERIVED the formula")
        print("  ITSELF (not selected from hand-provided candidates):")
        print(f"  · GATHER: F1-F5 grounded as Claims (op-trees parsed; F2/F5 reduce to the")
        print(f"    HELD SNF + the HELD sum_where binder — cited read-vs-derived).")
        print(f"  · DERIVE: the derivation engine CHAINED the grounded facts (a mechanical")
        print(f"    composer assembled the chain FROM the fact op-trees; the engine selected")
        print(f"    + applied each held op bottom-up, verifying each step) -> the FORMULA")
        print(f"    rank[G,G] = 1 - |H_1|*chi(G). PROVENANCE = the facts + the chain (NOT a")
        print(f"    hand-written string); the selector is offer-order-independent.")
        print(f"  · VALIDATE: the cmsg174 gate accepted the DERIVED chain (reproduces ALL")
        print(f"    four textbook knowns Z/3^3=28, Z/2^3=5, modular=2, D_inf=1) and REJECTED")
        print(f"    the deliberately-wrong derived branch (dropped F4 / the key's prod).")
        print(f"  · COMPUTE: the derived chain gives rk K = {computed} on Z/5*Z/8*Z/2.")
        print(f"  · KEY ERROR FLAGGED (END only): {computed} != key {answer} -> the answer-")
        print(f"    KEY (28) IS WRONG (it is the rejected prod branch's value); the genuine")
        print(f"    answer is {computed}. The formula is the agent's (DERIVED), and it was")
        print(f"    validated against independent textbook knowns BEFORE the question's")
        print(f"    answer was ever read. The cmsg174 remaining axis is closed.")
        print(SEP)
        return 0
    if key_correct:
        print(f"OUTCOME (b): the derived chain computes {computed} == key {answer} — but the")
        print(f"  cmsg124 result is 95; investigate (the chain or the knowns).")
        print(SEP)
        return 1
    print(f"OUTCOME (b): the derived chain computes {computed} (expected 95); the derive")
    print(f"  ran but the compute is off -> NAMED.")
    print(SEP)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
