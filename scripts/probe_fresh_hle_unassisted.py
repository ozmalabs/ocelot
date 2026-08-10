#!/usr/bin/env python3
"""probe_fresh_hle_unassisted — run the AGENT'S OWN committed math pipeline,
UNASSISTED, on a FRESH HLE question it picks by TOPIC (Euler-characteristic
invariant), COLD. The shell supplies ONLY the raw question stem + the boot; the
agent's machinery does every step:

  read raw stem -> TYPE the invariant (presupposition_derivation, the general
  reader) -> GENERATE the facts it needs (order_n_communication order-1) ->
  ROUTE each to its source (order-2) -> CONTROL (order-N) -> DERIVE (the
  derivation engine, via the orchestrator) -> VALIDATE (cmsg174 gate) ->
  COMPUTE.

The answer key is read at END ONLY, to score — never fed into any step.

FAITHFUL: a world-adapter shell. No invariant hand-typed, no fact curated, no
formula hand-coded, no hint, no answer peeked before END. The reader types the
invariant off the raw stem; order_n_communication generates+routes; the
derivation engine chains. Math/reading only; speech path untouched.
"""
from __future__ import annotations
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import substrate_rs as native
from domains import presupposition_derivation as _pd
from domains import order_n_communication as _onc

# The FRESH question, picked by TOPIC (reduced Euler characteristic of an
# abstract simplicial complex). NOT the touchstone 66f407a... the pipeline was
# built on; NOT 671579. Chosen cold by topic, not by a known/easy answer.
QID = "66f6f048b40ada5ac3b91cf8"
SEP = "=" * 80


def banner(s):
    print("\n" + SEP); print(s); print(SEP)


def main():
    data = json.load(open(os.path.join(os.path.dirname(__file__), "..",
                                       "data", "hle_math.json")))
    q = next(x for x in data if x["id"] == QID)
    stem = q["question"]

    banner("THE QUESTION (fresh, cold, by topic — reduced Euler characteristic)")
    print(f"  id      : {QID}")
    print(f"  subject : {q.get('raw_subject')}")
    print(f"  type    : {q.get('answer_type')}")
    print(f"  RAW STEM (the agent reads this verbatim — no paraphrase):")
    for line in stem.splitlines():
        print(f"    | {line}")

    # ---- STEP 1: TYPE THE INVARIANT (the agent's general reader). ----
    banner("STEP 1 — the agent TYPES the invariant (presupposition_derivation, "
           "the general reader)\nover the RAW stem (no hand-isolation of the asked "
           "invariant)")
    asked = _pd.comprehend_asked_invariant(stem)
    print(f"  normalised asked phrase : {asked.phrase!r}")
    print(f"  typed structure         : {asked.typed}")
    print(f"  rendered repr           : {asked.repr!r}")
    print(f"  is euler_characteristic : {asked.euler_characteristic}")
    print(f"  is free_rank-of-ker-Hur : {asked.free_rank_of_kernel_of_hurewicz}")
    print(f"  reader's reason         : {asked.reason}")

    typed_ok = (asked.typed is not None)
    if not typed_ok:
        banner("STALL AT STEP 1 (TYPE) — the general reader did NOT type the asked "
               "invariant.\nThe comprehension frontier: the construction it could not "
               "comprehend is named above.")

    # ---- STEP 2-4: GENERATE -> ROUTE -> CONTROL (order_n_communication). ----
    banner("STEP 2-4 — the agent GENERATES the facts (order-1) -> ROUTES each to its "
           "source\n(order-2) -> CONTROL (order-N), via order_n_communication over the "
           "RAW stem")
    s = native.Substrate()
    gen = _onc.generate_order_n(s, stem, about=QID, max_order=3, record=True)
    fact_set = gen["fact_set"]
    print(f"  GENERATED fact-set size : {len(fact_set)}")
    if not fact_set:
        print("  -> the order-1 QUERY lift generated NO queries: the reader did not")
        print("     type the invariant into a tree whose operators presuppose any of")
        print("     the agent's held facts (no euler/Hurewicz operator read off the")
        print("     typed tree). The generate step produced an EMPTY fact-set.")
    for i, f in enumerate(fact_set):
        print(f"\n  --- generated fact #{i} ---")
        print(f"    order-1 QUERY    : {f['query']}")
        print(f"    needed fact      : {f['fact_name']}")
        print(f"    fact prose       : {f['fact_prose']}")
        print(f"    query provenance : {f['query_provenance']}")
        print(f"    order-2 ROUTE    : type={f['route_type']}")
        print(f"      source         : {f['route_source']}")
        print(f"      source Mt      : {f['source_mt']}  faculty={f['source_faculty']}")
        print(f"      graph path     : {f['source_graph_path']}")
        print(f"    order-N CONTROL  : band={f['control_band']} decision="
              f"{f['control_decision']} gettable={f['gettable']}")

    # ---- STEP 5: DERIVE the presupposition/constraint (the engine). ----
    banner("STEP 5 — the agent DERIVES via the derivation engine "
           "(presupposition_derivation.derive_presuppositions chains the routed facts)")
    deriv = _pd.derive_presuppositions(stem)
    print(f"  derived presuppositions : {len(deriv['presuppositions'])}")
    for p in deriv["presuppositions"]:
        print(f"    - {p['label']} (property={p['property']}, "
              f"derived_value={p.get('derived_value')})")
    print(f"  undrivable (residuals)  : {deriv['undrivable']}")
    for d in deriv.get("derivations", []):
        if d.chain:
            print(f"\n  derivation chain ({d.property}):")
            for st in d.chain:
                print(f"    [{st['step']}] {st['fact']}")
        if d.note:
            print(f"    note: {d.note}")

    # ---- The HONEST GAP assessment (no number forced). ----
    banner("ASSESSMENT — where the unassisted pipeline reaches on THIS fresh question")
    print(f"  typed the invariant?          : {typed_ok}  "
          f"(euler_char={asked.euler_characteristic})")
    print(f"  generated a needed-fact set?  : {len(fact_set) > 0}")
    print(f"  derived a usable formula/      ")
    print(f"    constraint that COMPUTES the  ")
    print(f"    asked number?               : "
          f"{len(deriv['presuppositions']) > 0 and bool(fact_set)}")

    # NOTE: the derive_formula_then_validate orchestrator + the FACTS table are
    # HARD-WIRED to the commutator-free-rank-of-free-products invariant (F1-F5
    # about [G,G] of free products of cyclics, the held SNF leaf). They DO NOT
    # cover a reduced-Euler-characteristic-of-a-simplicial-complex COMPUTE. The
    # pipeline's COMPUTE faculty for this invariant is therefore the open gap —
    # surfaced honestly below, not hand-coded.

    # READ THE KEY AT END ONLY (to score — never fed into any step above).
    banner("END — read the key (to SCORE only; never fed into any step)")
    print(f"  HLE key (answer) : {q.get('answer')!r}")
    print(f"  the agent's pipeline computed value : "
          f"{'<none — see gap above>'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
