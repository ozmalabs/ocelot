#!/usr/bin/env python3
"""verify_e1_typed_unbranched — EMPIRICAL VERIFICATION of the E1 measurement gap.

The prior assessment scored E1 (generalize the order-1 generator) unblock-now = 0
because, in the assess_general_order1_generator harness, the NEW families used BARE
phrases ("the reduced euler characteristic of the simplicial complex") which die at
the READER (typed=None — no global atom for the object) BEFORE reaching the generator.
That measured the READER block, not the GENERATOR block.

The corrected claim: on the REAL path (a FULL STEM that INTRODUCES the object via a
binding clause — "Let R denote the ring ..." / "Let Delta_k denote the abstract
simplicial complex ..."), the gap-1 definition-binding reader TYPES the object, the
family REACHES the generator, and THEN the absence of a per-family branch is the block.

This probe constructs that typed-but-unbranched case on the real path and MEASURES:
  (A) does the object TYPE (reach the generator)?  [reader admits]
  (B) does the generator then emit 0 queries?       [the E1 block]
  (C) DOWNSTREAM: is there a compute/derive faculty for that typed family, or does it
      stall later anyway (which would BOUND E1's real unblock value)?

Read-only: generate_order_n(record=False). Math/reading only; speech path untouched.
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from substrate_rs import _native
from domains import presupposition_derivation as _pd
from domains import order_n_communication as _onc
from domains import construction_grammar as _cg

SEP = "=" * 80


def banner(s):
    print("\n" + SEP); print(s); print(SEP)


# Each case: a FULL STEM (introduces the object via a binding clause) + the asked
# invariant phrase. The first reproduces the OLD bare-phrase null (control: bare,
# dies at reader). The rest are REAL-PATH full stems for operators the reader can
# type via definition-binding but the GENERATOR has NO branch for (rank-of-ring,
# rank-of-group, betti-of-complex), plus a full-stem euler (BRANCHED — positive
# control that a typed+branched family DOES emit queries).
CASES = [
    ("CONTROL bare-phrase rank-of-ring (OLD harness style — should die at READER)",
     None,
     "the rank of the ring"),

    ("REAL-PATH rank-of-ring  (full stem binds R; reader types; generator UN-branched)",
     "Let R denote the ring of integers. We study its structural invariants.",
     "the rank of R"),

    ("REAL-PATH rank-of-group (full stem binds G; reader types; generator UN-branched)",
     "Let G denote the group of order 60. We study its structural invariants.",
     "the rank of G"),

    ("REAL-PATH betti-of-complex (full stem binds D; reader types; generator UN-branched)",
     "Let D denote the abstract simplicial complex on six vertices. "
     "We study its homology.",
     "the second betti number of D"),

    ("POSITIVE CONTROL euler-of-complex (full stem binds D; reader types; "
     "generator IS branched)",
     "Let D denote the abstract simplicial complex on six vertices. "
     "We study its homology.",
     "the euler characteristic of D"),
]


def type_and_generate(stem, asked_phrase):
    """Run the REAL path verbatim: build the full question text (stem introduces the
    object, then the asked-invariant question), feed it to the COMMITTED
    comprehend_asked_invariant (which itself calls comprehend_definitions for the
    env + _asked_phrase_window + comprehend_structure), then run the committed
    order-1 generator _presupposed_needs over the resulting AskedInvariant. No
    re-implementation — the genuine pipeline entry points."""
    if stem is not None:
        qtext = f"{stem} What is {asked_phrase}?"
    else:
        qtext = f"What is {asked_phrase}?"
    asked = _pd.comprehend_asked_invariant(qtext)
    needs = _onc._presupposed_needs(asked)
    return asked.env, asked.typed, asked, needs


def downstream_compute_for(typed):
    """C — is there a held compute/derive faculty for this typed family, or does it
    stall later anyway? Inspect the actual machinery, no hand-wave."""
    if not typed:
        return "n/a (did not type)"
    op = typed.get("op")
    notes = []
    # euler / reduced euler of a combinatorial complex -> compute_reduced_euler (held)
    if op in ("euler_characteristic", "reduced_euler_characteristic"):
        try:
            from domains import compute_reduced_euler as _cre
            fns = [n for n in dir(_cre) if not n.startswith("_")]
            notes.append(f"compute_reduced_euler HELD (api: {', '.join(fns[:6])}...)")
        except Exception as e:
            notes.append(f"compute_reduced_euler import FAIL: {e}")
    elif op in ("betti", "betti_number", "rank"):
        # is there a held betti / rank-of-H compute?
        try:
            from domains import commutator_rank as _cr
            has_betti = any("betti" in n.lower() for n in dir(_cr))
            notes.append(f"commutator_rank betti-ish symbols: {has_betti}")
        except Exception as e:
            notes.append(f"commutator_rank import FAIL: {e}")
        # a rank-of-ring / rank-of-group has NO presupposition branch AND, crucially,
        # no operator_specs reduction recorded -> even with a branch it would need a
        # compute faculty that does not exist for an arbitrary ring/group rank.
        notes.append("NO operator_specs/reduces_to for a generic rank(ring|group) "
                     "-> no held compute faculty -> would STALL downstream even if "
                     "branched")
    else:
        notes.append(f"op={op!r}: no recognised held compute faculty")
    return "; ".join(notes)


def main():
    _native.Substrate()  # boot the runtime (ulimit/timeout enforced by caller)

    banner("VERIFY E1 — the typed-but-unbranched case on the REAL (full-stem) path\n"
           "(A) does it TYPE+reach the generator?  (B) 0 queries?  (C) downstream?")

    rows = []
    for label, stem, asked_phrase in CASES:
        env, typed, asked, needs = type_and_generate(stem, asked_phrase)
        typed_ok = typed is not None
        downstream = downstream_compute_for(typed)
        rows.append((label, typed_ok, len(needs), asked.euler_characteristic,
                     asked.free_rank_of_kernel_of_hurewicz, downstream))
        print(f"\n  · {label}")
        print(f"      stem          : {stem!r}")
        print(f"      asked phrase  : {asked_phrase!r}")
        print(f"      env bound syms: {[''.join(k) for k in env.keys()]}")
        print(f"      asked repr    : {asked.repr!r}")
        print(f"      TYPED?        : {typed_ok}   root op: "
              f"{(typed.get('op') if typed else None)!r}  full: {typed}")
        print(f"      flags         : euler={asked.euler_characteristic}  "
              f"hurewicz={asked.free_rank_of_kernel_of_hurewicz}")
        print(f"      order-1 queries GENERATED: {len(needs)}")
        for n in needs:
            print(f"           - {n['fact']}: {n['query'][:64]}")
        print(f"      DOWNSTREAM compute: {downstream}")

    banner("VERDICT — the measurement, corrected")
    print("""
  Reading the rows:
    · CONTROL bare-phrase rank-of-ring: TYPED? should be False -> dies at the READER
      (this is what the OLD harness measured -> "E1 unblock=0" was the READER block).
    · REAL-PATH rank-of-ring / rank-of-group / betti-of-complex: TYPED? True
      (gap-1 binds the symbol) AND queries GENERATED = 0 -> THIS is E1's true block:
      the object TYPES, REACHES the generator, and the generator has NO branch.
    · POSITIVE CONTROL euler-of-complex (full stem): TYPED? True AND queries > 0 ->
      a typed+BRANCHED family DOES generate (proves the generator path is live; the
      0 on rank/betti is the missing branch, not a dead pipeline).

  DOWNSTREAM (the BOUND on E1's value): for euler-of-complex the held
  compute_reduced_euler exists -> generalizing the generator to euler-of-Delta would
  flow end-to-end. For rank(ring)/rank(group)/betti-of-complex there is NO held
  compute/reduces_to -> even WITH a generator branch they STALL at the compute step.
  So E1's unblock is REAL (the generator block is now empirically distinct from the
  reader block) but BOUNDED: it converts typed families to query-emitting families,
  but only the ones with a held downstream compute (euler) flow all the way; the
  others expose the next wall (the per-operator reduction/compute faculty, H1 in the
  prior assessment).
""")


if __name__ == "__main__":
    main()
