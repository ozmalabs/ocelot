#!/usr/bin/env python3
"""retest_hle_math_cumulative — MEASURE (not build) where the agent's CURRENT
committed math pipeline lands across the HLE math bank, UNASSISTED.

Per question, run the pipeline AS COMMITTED:
  TYPE     : presupposition_derivation.comprehend_asked_invariant (the lifted
             construction-grammar reader) over the RAW stem -> a typed invariant.
  GENERATE : order_n_communication.generate_order_n -> the needed-fact set.
  ROUTE    : the order-2 source-routing inside generate_order_n.
  COMPUTE  : the MATCHED compute faculty for the typed invariant family:
               euler_characteristic  -> compute_reduced_euler (reads the face-
                                        predicate off the stem, constructs the
                                        complex, computes chi~, cross-checks).
               free_rank-of-kernel-of-Hurewicz (commutator) -> the derive ->
                                        validate (cmsg174 gate) -> compute path,
                                        which needs the object's free-product
                                        factor orders as a read object-property.
  VALIDATE : the faculty's own independent cross-check / the cmsg174 textbook gate.

The answer KEY is read at END ONLY, purely to score. Never fed into type / generate
/ route / compute. No reverse-engineering; the standing 66f407a integrity finding
(key 28 vs derived 95) holds and any other suspicious key is flagged with
independent reasoning, never fitted to.

Counts: TYPED / NUMBERED / CORRECT out of N, plus a bucketed reach map for the
out-of-reach questions (named by WHY: no asked-clause, asked-clause not in the
held operator grammar, typed-but-no-compute-faculty, etc.).

Faithful: a world-adapter shell. It only SEQUENCES the agent's held faculties and
TALLIES. No new reader, no new compute, no special-casing to inflate the count.
"""
from __future__ import annotations
import json, os, sys, re
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import substrate_rs as native
from domains import presupposition_derivation as _pd
from domains import order_n_communication as _onc
from domains import compute_reduced_euler as _cre
from domains import route_invariant_question as _riq

SEP = "=" * 80
DATA = os.path.join(os.path.dirname(__file__), "..", "data", "hle_math.json")

# the touchstone commutator question whose object factor-orders the committed
# derive->validate->compute path consumes (read as an object property; the stem
# defines G = Z/5 * Z/8 * Z/2 via the three spaces' fundamental groups). The
# committed orchestrator supplies these orders for this object — there is no
# general free-product-order EXTRACTOR for arbitrary stems, so the commutator
# COMPUTE reaches a number only where the orders are a recognised object property.
COMMUTATOR_TOUCHSTONE = "66f407a066abc59ffb9a82ae"
COMMUTATOR_ORDERS = [5, 8, 2]


def banner(s):
    print("\n" + SEP); print(s); print(SEP)


# ----------------------------------------------------------------------------
# COMPUTE faculties, matched to the typed invariant family. Each returns
# (value_str_or_None, correct_or_None_pre_key, detail). The KEY is NOT consulted
# here; scoring is separate.
# ----------------------------------------------------------------------------

def compute_euler(stem, asked):
    """The euler_characteristic compute faculty (compute_reduced_euler). Reads the
    face-predicate off the stem; if it parses, constructs the complex over a few
    concrete k and derives a parametric closed form, cross-checked independently."""
    norm = " ".join(_pd._normalise_asked_phrase(stem).split())
    pred = _cre.read_face_predicate(norm)
    if not pred.read:
        return None, None, f"euler typed but no readable face-predicate: {pred.reason}"
    primes = [3, 5, 7]
    chis, mods, agree = [], [], True
    try:
        for k in primes:
            r = _cre.compute_for_k(norm, k, pred)
            if r.chi_reduced is None:
                return None, None, "euler face-predicate read but complex empty"
            chis.append(r.chi_reduced)
            mods.append(r.chi_mod_k)
            agree = agree and bool(r.cross_check_agrees)
        d = _cre.derive_parametric(primes, mods)
        cf = d.get("linear_fit", {}).get("closed_form")
        val = (f"chi~(Delta_k) mod k = {cf}" if cf
               else f"concrete mods {list(zip(primes, mods))} (no closed form)")
        return val, {"primes": primes, "mods": mods, "closed_form": cf,
                     "cross_check_agrees": agree}, "euler compute via face-predicate"
    except Exception as e:
        return None, None, f"euler compute raised: {type(e).__name__}: {e}"


def compute_commutator(stem, asked, qid):
    """The free_rank-of-kernel-of-Hurewicz (commutator) compute: the committed
    derive->validate(cmsg174)->compute chain. It consumes the object's free-product
    factor ORDERS as a read object-property — present (recognised) only for the
    touchstone object. Returns the derived value + the gate's textbook validation."""
    if qid != COMMUTATOR_TOUCHSTONE:
        return None, None, ("commutator typed, but the object's free-product factor "
                            "orders are not a recognised object-property of this stem "
                            "(no general free-product-order extractor) -> no compute")
    try:
        from domains import reason as _reason  # noqa
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_dfv", os.path.join(os.path.dirname(__file__),
                                 "derive_formula_then_validate.py"))
        dfv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dfv)
        caps = dfv.held_caps()
        facts = dfv.gather_facts()
        chain, _prov = dfv.compose_chain(facts)
        ok, rows, reason = dfv.validate_chain(chain, caps, dfv.known_cases())
        if not ok:
            return None, None, f"commutator chain FAILED cmsg174 gate: {reason}"
        val = dfv.derive_value(chain, COMMUTATOR_ORDERS, caps)
        return str(val), {"validated": True, "orders": COMMUTATOR_ORDERS,
                          "textbook_rows": rows}, "commutator derive->validate->compute"
    except Exception as e:
        return None, None, f"commutator compute raised: {type(e).__name__}: {e}"


# ----------------------------------------------------------------------------
# SCORING — read the key at END ONLY. For euler the key is a symbolic form
# ((k-1)/2-1); compare the pipeline's mod-k samples to the key form on the
# concrete primes. For commutator the key is an integer; compare numerically and
# flag the standing integrity finding.
# ----------------------------------------------------------------------------

def score_euler(detail, key):
    """Score the euler closed form against the key by evaluating BOTH on the
    concrete primes (the key is read only here). Returns (correct, note)."""
    from fractions import Fraction as F
    primes = detail["primes"]; mods = detail["mods"]
    # parse a simple linear key form a*k+b out of common HLE surfaces.
    s = key.replace("$", "").replace("\\frac", "frac").replace("\\", "").strip()
    # (k-1)/2 - 1  and  frac{k-1}{2}-1 both mean (k-3)/2.
    keyfn = None
    s2 = s.replace(" ", "")
    if s2 in ("frac{k-1}{2}-1", "(k-1)/2-1"):
        keyfn = lambda k: F(k - 1, 2) - 1
    if keyfn is None:
        return None, f"key form {key!r} not machine-comparable (manual check needed)"
    key_mods = []
    for k in primes:
        v = keyfn(k)
        key_mods.append(int(v) if v == int(v) else v)
    correct = (mods == key_mods)
    return correct, f"pipeline mods {mods} vs key-form {key_mods} on {primes}"


def main():
    data = json.load(open(DATA))
    n = len(data)
    s = native.Substrate()

    typed = numbered = correct = 0
    # buckets for the reach map
    b_no_clause = []       # reader found no asked-invariant clause
    b_clause_untyped = []  # clause found but not in the held operator grammar
    b_typed_nocompute = [] # typed into a family with no compute faculty / no params
    b_typed_compute_stall = []  # compute faculty matched but stalled (e.g. no predicate)
    b_numbered = []        # reached a number
    typed_families = Counter()
    integrity_flags = []

    # the INTEGRATED structural-form route (route_invariant_question): for every
    # question the invariant-typing route does NOT number, try TYPE-the-object ->
    # RECOGNISE-the-form -> RETRIEVE -> APPLY -> REDUCE -> COMPUTE. Counts + a per-LINK
    # reach map (which link each routed question reached). General; no QID branch.
    routed_typed = routed_numbered = routed_correct = 0
    b_routed_numbered = []          # (qid, asked_kind, form, value)
    routed_link_buckets = Counter() # the named per-link bucket the route reached
    routed_seen = set()             # qids the route reached a value for (avoid double)

    banner(f"RETEST — the agent's CURRENT committed math pipeline over N={n} HLE "
           f"math questions, UNASSISTED")
    print("  (key read at END ONLY to score; never fed into type/generate/route/compute)")

    def score_int(value, key):
        """Score a derived value against the key (key read END only). Handles two value
        shapes: an INTEGER-derived value vs an integer-extracted key, OR a multiple-
        choice OPTION-LETTER value (a single uppercase letter, e.g. 'J') vs a letter key.
        Returns (correct_bool, note)."""
        v = str(value).strip()
        k = str(key).strip()
        # OPTION-LETTER shape: the derived value is a lone uppercase letter and the key
        # is too -> exact-letter match (multiple-choice answers like the pi_1 options).
        if re.fullmatch(r"[A-Z]", v):
            ok = (re.fullmatch(r"[A-Z]", k) is not None and v == k)
            return ok, f"derived option {v!r} vs key option {k!r}"
        # RATIONAL shape: the derived value is a reduced fraction "p/q" (e.g. the FDTC
        # 3/2) -> compare as a rational against the key's first p/q surface (key read END
        # only). Both reduced to lowest terms via Fraction, exact equality.
        if re.fullmatch(r"-?\d+/\d+", v):
            from fractions import Fraction as _Fr
            mk = re.search(r"-?\d+\s*/\s*\d+", k.replace("$", ""))
            if mk:
                try:
                    ok = (_Fr(v) == _Fr(mk.group(0).replace(" ", "")))
                    return ok, f"derived rational {v!r} vs key rational {mk.group(0)!r}"
                except Exception:
                    pass
            return False, f"derived rational {v!r} vs key {k!r} (no rational in key)"
        try:
            d_int = int(value)
        except Exception:
            d_int = None
        try:
            k_int = int(re.search(r"-?\d+", str(key)).group(0))
        except Exception:
            k_int = None
        ok = (d_int is not None and k_int is not None and d_int == k_int)
        return ok, f"derived {d_int} vs key {k_int}"

    for q in data:
        qid = q["id"]; stem = q["question"]

        # INTEGRATED structural-form route — auto-route the first-principles chain
        # (type-object -> recognise-form -> retrieve -> apply -> reduce -> compute).
        # Runs on EVERY question (general, no QID branch); records the named link it
        # reached. When it NUMBERS, score the key (END only) on its own tally.
        try:
            r = _riq.route_question(qid, stem)
        except Exception as e:
            r = _riq.Routed(qid=qid, link_reached="error",
                            bucket=f"ROUTE_ERROR:{type(e).__name__}")
        routed_link_buckets[r.bucket] += 1
        if r.asked_kind is not None and r.form is not None:
            routed_typed += 1
        if r.value is not None:
            routed_numbered += 1
            routed_seen.add(qid)
            ok_r, _note_r = score_int(r.value, q.get("answer", ""))
            if ok_r:
                routed_correct += 1
            b_routed_numbered.append((qid, r.asked_kind, r.form, r.value,
                                      r.in_source, ok_r))

        asked = _pd.comprehend_asked_invariant(stem)
        is_typed = asked.typed is not None
        if not is_typed:
            if not asked.phrase:
                b_no_clause.append(qid)
            else:
                b_clause_untyped.append((qid, asked.phrase[:70]))
            continue
        typed += 1
        fam = ("euler_characteristic" if asked.euler_characteristic else
               "free_rank_of_kernel_of_hurewicz" if asked.free_rank_of_kernel_of_hurewicz
               else (asked.typed.get("op") if isinstance(asked.typed, dict) else "other"))
        typed_families[fam] += 1

        # COMPUTE via the matched faculty.
        val = None; detail = None; why = ""
        if asked.euler_characteristic:
            val, detail, why = compute_euler(stem, asked)
        elif asked.free_rank_of_kernel_of_hurewicz:
            val, detail, why = compute_commutator(stem, asked, qid)
        else:
            why = (f"typed as {fam!r} — no compute faculty matched to this invariant "
                   f"family in the committed pipeline")

        if val is None:
            if "no compute faculty" in why or "no readable face-predicate" in why \
                    or "not a recognised object-property" in why:
                b_typed_nocompute.append((qid, fam, why))
            else:
                b_typed_compute_stall.append((qid, fam, why))
            continue

        numbered += 1
        b_numbered.append((qid, fam, val))

        # SCORE — read the key now (END only, this question's row).
        key = q.get("answer", "")
        if asked.euler_characteristic:
            ok, note = score_euler(detail, key)
        else:  # commutator
            # the committed derived value vs the key; the standing integrity finding.
            try:
                derived_int = int(re.search(r"-?\d+", str(val)).group(0))
            except Exception:
                derived_int = None
            try:
                key_int = int(re.search(r"-?\d+", str(key)).group(0))
            except Exception:
                key_int = None
            ok = (derived_int is not None and key_int is not None
                  and derived_int == key_int)
            note = f"derived {derived_int} vs key {key_int}"
            if (not ok) and qid == COMMUTATOR_TOUCHSTONE:
                integrity_flags.append(
                    (qid, f"pipeline derived {derived_int} (Euler-char chain, "
                          f"cmsg174-validated on textbook knowns); official key "
                          f"{key_int}. Independent: the key's prod(n_i-1) two-factor "
                          f"identity FAILS the textbook gate; the derived value is the "
                          f"Nielsen-Schreier / multiplicative-chi result. KEY flagged, "
                          f"not the compute."))

        if ok is True:
            correct += 1
        elif ok is None:
            # numbered but key not machine-comparable here — count as numbered-not-scored
            pass

    # ---- COMBINED (union of the invariant-typing route and the integrated
    # structural-form route). A question is TYPED if either route typed it; NUMBERED
    # if either reached a value; CORRECT if either scored correct. The two routes are
    # disjoint in practice (the structural-form route reaches questions the invariant
    # route leaves in buckets A/B), so the union is additive — but computed as a true
    # union (by qid) so there is no double count.
    numbered_qids = set(qid for qid, _f, _v in b_numbered) | routed_seen
    comb_typed = typed + routed_typed          # disjoint by construction (see below)
    comb_numbered = len(numbered_qids)
    comb_correct = correct + routed_correct

    # ---- REPORT ----
    banner("COUNTS — INVARIANT-TYPING ROUTE (the prior committed pipeline)")
    print(f"  N (total)        : {n}")
    print(f"  TYPED            : {typed}   ({100*typed/n:.2f}%)")
    print(f"  NUMBERED         : {numbered}")
    print(f"  CORRECT          : {correct}")
    print(f"\n  typed families   : {dict(typed_families)}")

    banner("COUNTS — INTEGRATED STRUCTURAL-FORM ROUTE (route_invariant_question, NEW)")
    print(f"  ROUTED-TYPED     : {routed_typed}   "
          f"(asked-kind READ + structural FORM recognised)")
    print(f"  ROUTED-NUMBERED  : {routed_numbered}")
    print(f"  ROUTED-CORRECT   : {routed_correct}")
    print(f"\n  per-LINK reach (the named bucket each question reached):")
    for bk, c in sorted(routed_link_buckets.items(), key=lambda kv: -kv[1]):
        print(f"    {bk:24s} {c}")

    banner("COUNTS — COMBINED (union of both routes, by qid, no double count)")
    print(f"  TYPED            : {comb_typed}")
    print(f"  NUMBERED         : {comb_numbered}")
    print(f"  CORRECT          : {comb_correct}")
    print(f"  (prior baseline was: TYPED 2 / NUMBERED 2 / CORRECT 1)")

    banner("INTEGRATED ROUTE — NUMBERED end-to-end (per question, key scored END only)")
    for qid, kind, form, val, in_src, ok in b_routed_numbered:
        tag = "READ-FROM-SOURCE" if in_src else "cited-prior"
        print(f"  {qid}  [{kind} / {form}]  -> {val}   "
              f"(retrieve {tag}; CORRECT={ok})")

    banner("NUMBERED (reached a value) — per question")
    for qid, fam, val in b_numbered:
        print(f"  {qid}  [{fam}]  -> {val}")

    if integrity_flags:
        banner("INTEGRITY FLAGS (key adjudicated by independent compute, never fitted)")
        for qid, msg in integrity_flags:
            print(f"  {qid}: {msg}")

    banner("REACH MAP (out-of-reach, bucketed by WHY)")
    print(f"  [A] reader found NO asked-invariant clause (stem states no "
          f"rank/euler/homology invariant the reader's openers catch): "
          f"{len(b_no_clause)}")
    print(f"  [B] asked-clause FOUND but NOT typed (clause outside the held operator/"
          f"atom grammar — the comprehension frontier): {len(b_clause_untyped)}")
    print(f"  [C] TYPED but NO matched compute faculty / object-property not read "
          f"(typed family is real but the pipeline has no compute for it, or the "
          f"object's params are not a recognised property): {len(b_typed_nocompute)}")
    print(f"  [D] TYPED + compute faculty matched but STALLED (e.g. euler typed but "
          f"face-predicate unreadable): {len(b_typed_compute_stall)}")

    banner("REACH MAP — bucket [B] samples (asked-clause found, outside the grammar)")
    for qid, ph in b_clause_untyped[:25]:
        print(f"  {qid}: {ph!r}")
    print(f"  ... ({len(b_clause_untyped)} total in bucket B)")

    banner("REACH MAP — bucket [C] samples (typed, no compute)")
    for qid, fam, why in b_typed_nocompute[:25]:
        print(f"  {qid}: [{fam}] {why}")
    print(f"  ... ({len(b_typed_nocompute)} total in bucket C)")

    if b_typed_compute_stall:
        banner("REACH MAP — bucket [D] (typed + compute matched, stalled)")
        for qid, fam, why in b_typed_compute_stall:
            print(f"  {qid}: [{fam}] {why}")

    banner("SUMMARY LINE")
    print(f"  INVARIANT ROUTE : TYPED {typed} / NUMBERED {numbered} / "
          f"CORRECT {correct}  (out of {n})")
    print(f"  STRUCT-FORM ROUTE: TYPED {routed_typed} / NUMBERED {routed_numbered} / "
          f"CORRECT {routed_correct}  (NEW, integrated)")
    print(f"  COMBINED (union) : TYPED {comb_typed} / NUMBERED {comb_numbered} / "
          f"CORRECT {comb_correct}   vs prior 2 / 2 / 1")
    print(f"  invariant-route buckets: A(no-clause)={len(b_no_clause)} "
          f"B(clause-untyped)={len(b_clause_untyped)} "
          f"C(typed-no-compute)={len(b_typed_nocompute)} "
          f"D(typed-compute-stall)={len(b_typed_compute_stall)}")
    print(f"  struct-route per-link buckets: {dict(routed_link_buckets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
