#!/usr/bin/env python3
"""verify_reader_frontier_families — the READER FRONTIER taken, donkey-checked.

The agent extended its reader so the invariant families it measured typed=False
(homology / betti / dimension / fundamental_group / genus) now TYPE — the SAME
general way euler_characteristic / free_rank(kernel(hurewicz_map)) / rank already
do: an operator's name/aliases/arity/indexed-ness live as a DATA ROW in
seeds/math_prose_constructions.json `operators`, and ONE uniform "operator-of-object"
mechanism in construction_grammar._comprehend_structure reads any of them. Indexed
operators carry an `{index}` slot the SHARED _read_index/_match_indexed_operator
reads (ordinal / symbolic / subscript / bare number). The object slot resolves via
the existing gap-1 definition-binding + generic-type atoms.

This probe MEASURES, on the genuine pipeline (comprehend_asked_invariant ->
_presupposed_needs), per the strict rails:

  (1) BEFORE/AFTER: each of the 5 families typed=False at the COMMITTED baseline
      (rows absent) -> typed=op(object) now (rows present). We reproduce BEFORE by
      loading the committed seed (git show HEAD:...) and AFTER by the working tree.
  (2) INDEXED: the index reads into the slot generally — ordinal ('second'->2),
      symbolic ('n-th'->n), subscript ('H_1'/'b_2'->1/2).
  (3) GENERALITY: a FRESH operator NOT in the initial 5 (signature) types by
      ADDING ONE DATA ROW to the in-memory grammar — the SAME _comprehend_structure
      reads it, NO code change.
  (4) HONEST DOWNSTREAM: per family, it TYPES then STALLS at generate (0 queries:
      no _presupposed_needs branch) / compute (no held faculty) — named, no
      end-to-end overclaim.

Read-only (no record); math/reading only; speech path untouched. `_native.Substrate()`.
"""
from __future__ import annotations
import os, sys, json, subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from substrate_rs import _native
from domains import presupposition_derivation as _pd
from domains import order_n_communication as _onc
from domains import construction_grammar as _cg

SEP = "=" * 84


def banner(s):
    print("\n" + SEP); print(s); print(SEP)


# ---------------------------------------------------------------------------
# The 5 frontier families, each on the REAL path: a full stem that INTRODUCES
# the object via a binding clause (gap-1) + the asked-invariant phrase. The
# objects type via the binding + generic-type atoms; the operators via the new
# DATA rows. Indexed families exercise distinct index surfaces.
# ---------------------------------------------------------------------------
STEM_SPACE = ("Let X denote the space under study. "
              "We study its topological invariants.")
STEM_CPLX = ("Let D denote the abstract simplicial complex on six vertices. "
             "We study its homology.")
STEM_GRP = ("Let G denote the group of order 60. "
            "We study its structural invariants.")

FAMILIES = [
    # (family, expected_op, indexed?, stem, asked_phrase, expected_repr_substr)
    ("homology (indexed, ordinal)", "homology", True, STEM_SPACE,
     "the second homology of X", "homology(space, 2)"),
    ("homology (indexed, symbolic)", "homology", True, STEM_SPACE,
     "the n-th homology of X", "homology(space, n)"),
    ("homology (subscript H_1)", "homology", True, STEM_SPACE,
     "H_1 of X", "homology(space, 1)"),
    ("betti (indexed, ordinal)", "betti", True, STEM_CPLX,
     "the second betti number of D", "betti(simplicial_complex, 2)"),
    ("betti (subscript b_2)", "betti", True, STEM_SPACE,
     "b_2 of X", "betti(space, 2)"),
    ("dimension", "dimension", False, STEM_SPACE,
     "the dimension of X", "dimension(space)"),
    ("fundamental_group", "fundamental_group", False, STEM_SPACE,
     "the fundamental group of X", "fundamental_group(space)"),
    ("genus", "genus", False, STEM_SPACE,
     "the genus of X", "genus(space)"),
]


def type_phrase(stem, asked_phrase):
    """Genuine pipeline: full question text -> comprehend_asked_invariant (env +
    window + comprehend_structure) -> _presupposed_needs (the order-1 generator)."""
    qtext = f"{stem} What is {asked_phrase}?"
    asked = _pd.comprehend_asked_invariant(qtext)
    needs = _onc._presupposed_needs(asked)
    return asked, needs


# ---------------------------------------------------------------------------
# (1) BEFORE — the COMMITTED baseline grammar (rows absent). We load the
# committed seed JSON via `git show HEAD:...` and run the SAME _comprehend_structure
# against it, with the binding env supplied, to show the 5 families typed=None.
# ---------------------------------------------------------------------------
_SEED_REL = "research/experiments/gamma-substrate/seeds/math_prose_constructions.json"
_REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       cwd=os.path.dirname(__file__), capture_output=True,
                       text=True).stdout.strip()


def committed_grammar():
    out = subprocess.run(["git", "show", f"HEAD:{_SEED_REL}"], cwd=_REPO,
                         capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)


def type_against_grammar(grammar, stem, asked_phrase):
    """Type the asked phrase against an ARBITRARY grammar dict (committed or
    fresh-row), reusing the genuine env-binding + the genuine _comprehend_structure.
    The env is built from the stem by the committed comprehend_definitions (binding
    is unchanged across before/after — only the operator rows differ)."""
    env = _cg.comprehend_definitions(stem)
    import re as _re
    toks = _re.findall(r"[a-z0-9]+|=", asked_phrase.lower())
    toks = _cg._resolve_appositive(toks)
    node = _cg._comprehend_structure(toks, grammar, 0, frozenset(), env or {})
    return node


def main():
    _native.Substrate()  # boot the runtime (ulimit/timeout by caller)

    # ---- (1) BEFORE/AFTER -------------------------------------------------
    banner("(1) BEFORE / AFTER — the 5 families: typed=False (committed) -> "
           "typed=op(object) (now)")
    base = committed_grammar()
    now = _cg.load_math_prose()
    base_ops = [o["name"] for o in (base or {}).get("operators", [])]
    now_ops = [o["name"] for o in now.get("operators", [])]
    print(f"  committed operators ({len(base_ops)}): {base_ops}")
    print(f"  working-tree operators ({len(now_ops)}): {now_ops}")
    print(f"  committed has index_words?  {'index_words' in (base or {})}")
    print(f"  working-tree has index_words? {'index_words' in now}")

    before_after = []
    for fam, op, indexed, stem, asked, want in FAMILIES:
        before = type_against_grammar(base, stem, asked) if base else None
        after = type_against_grammar(now, stem, asked)
        b_repr = _cg._structure_repr(before) if before else None
        a_repr = _cg._structure_repr(after) if after else None
        before_after.append((fam, b_repr, a_repr, want, op, indexed))
        print(f"\n  · {fam}")
        print(f"      asked      : {asked!r}")
        print(f"      BEFORE typed: {b_repr!r}   (committed: row absent)")
        print(f"      AFTER  typed: {a_repr!r}   (want: {want!r})")
        ok = (before is None) and (after is not None) and (a_repr == want)
        print(f"      VERDICT    : typed=False -> typed=op(object): "
              f"{'PASS' if ok else 'FAIL'}")

    # ---- (2) INDEXED into the slot, on the genuine pipeline ---------------
    banner("(2) INDEXED — the index read into the slot GENERALLY (ordinal / "
           "symbolic / subscript), on the genuine comprehend_asked_invariant path")
    for fam, op, indexed, stem, asked, want in FAMILIES:
        if not indexed:
            continue
        a, _ = type_phrase(stem, asked)
        t = a.typed
        idx = t.get("index") if t else None
        sym = t.get("index_symbolic") if t else None
        print(f"  · {fam:32s} -> {a.repr!r}   index={idx!r} symbolic={sym}")

    # ---- (3) GENERALITY — a FRESH operator from ONE data row, no code ------
    banner("(3) GENERALITY — a FRESH operator ('signature') types by ADDING ONE "
           "DATA ROW to the grammar, NO code change (the same _comprehend_structure)")
    fresh_row = {
        "name": "signature_of",
        "pattern": ["the", "signature", "of", "{x}"],
        "op": "signature",
        "args": ["x"],
        "held_runnable": False,
        "asked_head": True,
    }
    print(f"  fresh operator NOT in the seed: 'signature' (4k-dim oriented mfld "
          f"invariant)")
    print(f"  the ONE data row added: {json.dumps(fresh_row)}")
    # BEFORE the row: type against the unmodified working-tree grammar.
    g_before = _cg.load_math_prose()
    n_before = type_against_grammar(g_before, STEM_SPACE, "the signature of X")
    # AFTER the row: append the single row to a COPY of the grammar; SAME code.
    g_after = _cg.load_math_prose()
    g_after["operators"] = list(g_after["operators"]) + [fresh_row]
    n_after = type_against_grammar(g_after, STEM_SPACE, "the signature of X")
    print(f"  BEFORE the row: typed = {_cg._structure_repr(n_before) if n_before else None!r}")
    print(f"  AFTER  the row: typed = {_cg._structure_repr(n_after) if n_after else None!r}"
          f"   (want 'signature(space)')")
    gen_ok = (n_before is None) and (n_after is not None) \
        and (_cg._structure_repr(n_after) == "signature(space)")
    # ALSO: a fresh INDEXED operator from one row (cohomology_i), proving the index
    # mechanism is general across operators, not a betti/homology special-case.
    fresh_indexed = {
        "name": "cohomology_indexed_of",
        "pattern": ["the", "{index}", "cohomology", "of", "{x}"],
        "op": "cohomology", "args": ["x"], "indexed": True,
        "held_runnable": False, "asked_head": True,
    }
    g_ci = _cg.load_math_prose()
    g_ci["operators"] = list(g_ci["operators"]) + [fresh_indexed]
    n_ci = type_against_grammar(g_ci, STEM_SPACE, "the third cohomology of X")
    ci_repr = _cg._structure_repr(n_ci) if n_ci else None
    print(f"\n  fresh INDEXED operator ('cohomology_i') from ONE row:")
    print(f"  AFTER the row: 'the third cohomology of X' -> {ci_repr!r}"
          f"   (want 'cohomology(space, 3)')")
    ci_ok = ci_repr == "cohomology(space, 3)"
    # ALSO: a fresh SUBSCRIPT operator ('c_2' cohomology) opens + types from ONE
    # row on the GENUINE pipeline — proving the subscript-opener finder is DATA-driven
    # (single-letter-prefix indexed row + shared index vocab), not a hand-listed
    # 'h_1 of' string. We add the row to the working seed in-memory via the acquire
    # cache so comprehend_asked_invariant (which reloads the grammar) sees it.
    fresh_subscript = {
        "name": "cohomology_subscript_of",
        "pattern": ["c", "{index}", "of", "{x}"],
        "op": "cohomology", "args": ["x"], "indexed": True,
        "held_runnable": False, "asked_head": True,
    }
    _cg._ACQUIRED.setdefault("operators", [])
    _cg._ACQUIRED["operators"].append(fresh_subscript)
    try:
        a_cs, _ = type_phrase(STEM_SPACE, "c_2 of X")
        cs_repr = a_cs.repr
    finally:
        _cg._ACQUIRED["operators"].remove(fresh_subscript)
    print(f"\n  fresh SUBSCRIPT operator ('c_2' cohomology) from ONE row, GENUINE "
          f"pipeline:")
    print(f"  'c_2 of X' -> {cs_repr!r}   (want 'cohomology(space, 2)')")
    cs_ok = cs_repr == "cohomology(space, 2)"
    print(f"\n  VERDICT generality (prefix): {'PASS' if gen_ok else 'FAIL'};  "
          f"indexed: {'PASS' if ci_ok else 'FAIL'};  subscript: "
          f"{'PASS' if cs_ok else 'FAIL'}  (one data row each, no code change)")

    # ---- (4) HONEST DOWNSTREAM — types then STALLS at generate/compute -----
    banner("(4) HONEST DOWNSTREAM — per family: TYPES, then STALLS at "
           "GENERATE (0 queries) / COMPUTE (no held faculty). NO end-to-end claim.")
    HELD_COMPUTE = {"euler_characteristic", "reduced_euler_characteristic"}
    for fam, op, indexed, stem, asked, want in FAMILIES:
        a, needs = type_phrase(stem, asked)
        typed = a.typed is not None
        gen = len(needs)
        compute = "HELD (compute_reduced_euler)" if op in HELD_COMPUTE \
            else "NONE (no held compute faculty for this op)"
        stall = []
        if gen == 0:
            stall.append("GENERATE (no _presupposed_needs branch -> 0 queries)")
        if op not in HELD_COMPUTE:
            stall.append("COMPUTE (no held faculty)")
        print(f"  · {fam:32s} typed={typed}  generate={gen} queries  "
              f"compute={compute}")
        print(f"        -> TYPES, then STALLS at: {', '.join(stall) or '(flows)'}")

    banner("SUMMARY")
    print("""
  THE EXTENSION: operators are DATA (seed `operators` rows: name/pattern/op/args/
    indexed); ONE uniform operator-of-object mechanism (_comprehend_structure +
    _match_indexed_operator + _read_index) reads ANY of them. NO per-operator Python
    branch, NO regex on the operator names.
  THE FAMILIES TYPE: homology/betti/dimension/fundamental_group/genus all go
    typed=False (committed, rows absent) -> typed=op(object) (now). Indexed ones read
    the index into the slot (ordinal/symbolic/subscript), via the SHARED reader.
  GENERALITY: a fresh operator ('signature') AND a fresh indexed operator
    ('cohomology_i') type by ADDING ONE DATA ROW each — no code change.
  HONEST DOWNSTREAM: each family TYPES then STALLS — at GENERATE (0 queries: no
    _presupposed_needs branch) and COMPUTE (no held faculty; only euler has one).
    Typing is the READER rung (necessary-not-sufficient); NOT end-to-end.
""")


if __name__ == "__main__":
    main()
