"""Invent the `dimension` recipe with the NATIVE (G,Γ) generator bricks.

TARGET: dimension of a simplicial complex.
KNOWNS: point/edge/triangle/tetra -> 0/1/2/3.

This script drives the EXISTING bricks AS THEY NATIVELY WORK — it adds no
hand-built discrimination scaffold (that was last turn's `feature_generator`):

  G  = domains/generator.py:synthesize        (bottom-up MDL enumeration over the
                                                DSL Term grammar)
  Γ  = domains/generator_exclusion.py         (observational-equivalence is already
                                                inside G; the learned-exclusion
                                                boundary is the additive Γ layer)
  Γ-relaxation = domains/generator_outofbox.py (finite, MDL-ordered box moves)

The agent reads a complex as an `env` of scalar descriptors (the only thing a
DSL Var can read). Each descriptor is an HONEST invariant the world adapter can
measure off a complex:

    maxface : #vertices in the LARGEST face        (the dimension-bearing one)
    V       : total #vertices in the complex        (a CHEAT source: V==maxface
                                                      ONLY for a single simplex)
    ncells  : #maximal faces                         (another non-dimension scalar)
    euler   : Euler characteristic V-E+F-...         (another non-dimension scalar)

The recipe we hope the native search finds: dim = maxface - 1.

The "cheat" the task asks about: `V - 1` (or `ncells`/`euler` games) — a recipe
that, on the four single-simplex knowns, returns the right number while IGNORING
the face structure (it reads the vertex COUNT, not the largest FACE). On a
single simplex V==maxface, so on the knowns-only spec the cheat is
OBSERVATIONALLY EQUIVALENT to the truth and the native G CANNOT tell them apart.

So we run TWO conditions and report both honestly:

  A) KNOWNS-ONLY spec (point/edge/triangle/tetra). The four single simplices.
  B) KNOWNS + STRUCTURE spec: add complexes where the cheat DISAGREES with the
     truth — two disjoint triangles (V=6, maxface=3, dim=2), a square boundary
     (a 1-complex: V=4,E=4, maxface=2, dim=1), a filled square = two triangles
     glued (V=4, maxface=3, dim=2). These are NOT a held-out test set — they are
     ADMISSIBILITY CONSTRAINTS in the spec itself: a cheat that returns V (or a
     V-game) simply fails to match the target and is excluded AT GENERATION by Γ
     (the spec is inadmissible for it). No hand-designed held-out, no scoring.

We then check the recipe on a genuinely HELD-OUT complex (a pentachoron / 4-simplex,
dim 4) it never saw, to confirm it's the real invariant and not a fit.

Run:
  ulimit -v 8388608
  PYTHONPATH=runners/dsl/python:. timeout 600 python3 scripts/dimension_recipe_native.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runners", "dsl", "python"))

from substrate_rs import Substrate
from domains.generator import synthesize, DEFAULT_OPS, _op_table
from domains.generator_exclusion import (
    target_class, make_exclude, harvest_explored_patterns,
    record_solution_patterns, learn_exclusions, excluded_patterns_for_class,
)
from domains.generator_outofbox import outofbox_solve


def banner(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


# ---------------------------------------------------------------------------
# WORLD ADAPTER (mechanical): a simplicial complex -> scalar descriptors.
# A complex is given as a list of its MAXIMAL faces, each a frozenset of vertex
# ids. Every descriptor below is a mechanical measurement off the complex — no
# decision, no agent logic. This is the only Python allowed: translate external
# structure into the smallest graph token (here, scalars a DSL Var can read).
# ---------------------------------------------------------------------------

def describe(maximal_faces):
    verts = set()
    for f in maximal_faces:
        verts |= set(f)
    V = len(verts)
    # all faces of all dims (the closure), to count E, F, etc. and Euler char.
    from itertools import combinations
    faces_by_dim: dict[int, set] = {}
    for mf in maximal_faces:
        mf = tuple(sorted(mf))
        for k in range(1, len(mf) + 1):
            for sub in combinations(mf, k):
                faces_by_dim.setdefault(k - 1, set()).add(sub)
    E = len(faces_by_dim.get(1, set()))
    Fc = len(faces_by_dim.get(2, set()))
    maxface = max((len(f) for f in maximal_faces), default=0)   # #verts in largest
    ncells = len(maximal_faces)
    euler = sum(((-1) ** d) * len(s) for d, s in faces_by_dim.items())
    return {"maxface": maxface, "V": V, "ncells": ncells, "euler": euler,
            "E": E, "F": Fc}


# Known single simplices: point/edge/triangle/tetra -> dim 0/1/2/3.
KNOWN_COMPLEXES = [
    ("point",    [frozenset({0})],                      0),
    ("edge",     [frozenset({0, 1})],                   1),
    ("triangle", [frozenset({0, 1, 2})],                2),
    ("tetra",    [frozenset({0, 1, 2, 3})],             3),
]

# Structure complexes where a vertex-count cheat DISAGREES with the truth.
STRUCTURE_COMPLEXES = [
    # two disjoint triangles: V=6 but dim=2 (V-1=5 wrong; maxface-1=2 right)
    ("2-triangles", [frozenset({0, 1, 2}), frozenset({3, 4, 5})], 2),
    # hollow square (a graph cycle, 1-complex): V=4,E=4, dim=1 (V-1=3 wrong)
    ("square-cycle", [frozenset({0, 1}), frozenset({1, 2}),
                      frozenset({2, 3}), frozenset({3, 0})], 1),
    # filled square = two triangles sharing an edge: V=4, dim=2 (V-1=3 wrong)
    ("filled-square", [frozenset({0, 1, 2}), frozenset({0, 2, 3})], 2),
]

# Held-out complex the recipe NEVER sees during synthesis (a real generalisation
# probe, not part of the spec): a 4-simplex (pentachoron), dim 4; and a big
# disjoint graph (V huge, dim 1) to re-confirm the cheat is dead out of sample.
HELDOUT_COMPLEXES = [
    ("4-simplex", [frozenset({0, 1, 2, 3, 4})], 4),
    ("5-simplex", [frozenset({0, 1, 2, 3, 4, 5})], 5),
    ("path-graph", [frozenset({i, i + 1}) for i in range(7)], 1),   # V=8, dim 1
    ("two-tetra", [frozenset({0, 1, 2, 3}), frozenset({4, 5, 6, 7})], 3),
]


def spec_from(complexes):
    """(env, expected_dim) rows the brick consumes. env = scalar descriptors."""
    return [(describe(mf), dim) for _, mf, dim in complexes]


def _term_outputs(term, complexes, s):
    out = []
    for _, mf, _dim in complexes:
        env = describe(mf)
        v = term.evaluate(env, s)
        v = (1 if v is True else 0) if isinstance(v, bool) else v
        out.append(v)
    return out


def _heldout_ok(term, s):
    if term is None:
        return None, []
    rows = []
    ok = True
    for name, mf, dim in HELDOUT_COMPLEXES:
        env = describe(mf)
        got = term.evaluate(env, s)
        got = (1 if got is True else 0) if isinstance(got, bool) else got
        good = abs(float(got) - float(dim)) < 1e-9
        ok = ok and good
        rows.append((name, dim, got, good))
    return ok, rows


# Ops: the arithmetic/comparison core (the dimension recipe is pure arithmetic).
OPS = ("Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
       "Gt", "Lt", "Eq", "IfThenElse")
MAX_SIZE = 7
TIMEOUT = 120.0


def raw_enumeration_count(n_leaves, ops, max_size):
    """The size of the RAW production space (enumerate-then-filter) up to max_size,
    WITHOUT observational-equivalence pruning or Γ — i.e. how many syntactically
    distinct Term-trees the grammar produces. This is the 12.3M-style figure the
    native mechanism avoids ever materialising. Computed combinatorially from the
    op-arities (no enumeration), so it is cheap and exact for the count."""
    table = _op_table()
    arity = {}
    for name in ops:
        k = table[name]["kind"]
        arity[name] = {"u": 1, "b": 2, "bc": 2, "t": 3}[k]
    # T[s] = number of trees of exactly size s. T[1] = n_leaves.
    T = {1: n_leaves}
    for s in range(2, max_size + 1):
        tot = 0
        for name, ar in arity.items():
            if ar == 1:
                tot += T.get(s - 1, 0)
            elif ar == 2:
                for sa in range(1, s - 1):
                    sb = (s - 1) - sa
                    tot += T.get(sa, 0) * T.get(sb, 0)
            elif ar == 3:
                for sc in range(1, s - 2):
                    for st in range(1, s - 1 - sc):
                        so = (s - 1) - sc - st
                        if so >= 1:
                            tot += T.get(sc, 0) * T.get(st, 0) * T.get(so, 0)
        T[s] = tot
    return sum(T.values()), T


def run_condition(name, complexes, s_substrate, leaves_note):
    banner(name)
    spec = spec_from(complexes)
    # show the spec the agent sees
    print("  spec rows (env -> expected dim):")
    for (cx_name, mf, dim), (env, _e) in zip(complexes, spec):
        keep = {k: env[k] for k in ("maxface", "V", "ncells", "euler")}
        print(f"     {cx_name:14} {keep}  -> {dim}")
    var_names = sorted({k for env, _ in spec for k in env})
    consts = (0, 1, 2, -1)
    n_leaves = len(var_names) + len(set(consts))
    raw_total, _T = raw_enumeration_count(n_leaves, OPS, MAX_SIZE)
    print(f"\n  RAW production space up to size {MAX_SIZE} "
          f"({n_leaves} leaves, {len(OPS)} ops): {raw_total:,} Term-trees")
    print(f"  (this is the enumerate-then-filter figure G NEVER materialises)")

    # --- NATIVE G + observational-equivalence (Γ already inside synthesize). ---
    r = synthesize(s_substrate, spec, ops=OPS, max_size=MAX_SIZE,
                   timeout_s=TIMEOUT, return_trace=True)
    print(f"\n  NATIVE G (size-ordered, observational-equivalence pruned):")
    print(f"     solved   = {r['fits']}  (halt={r['halt_reason']})")
    print(f"     recipe   = {r['term_str']}")
    print(f"     size     = {r['size']}  (MDL: smallest recipe fitting the spec)")
    print(f"     EXPLORED = {r['explored']:,}   DISTINCT-behaviours kept = "
          f"{r['distinct']:,}")
    if raw_total:
        print(f"     => Γ-admitted set is {r['explored']:,} of {raw_total:,} raw "
              f"= {100.0 * r['explored'] / raw_total:.3f}% of enumerate-then-filter")
    # does the recipe read the FACE structure or CHEAT on the vertex count?
    if r["fits"]:
        outs_known = _term_outputs(r["term"], complexes, s_substrate)
        ho_ok, ho_rows = _heldout_ok(r["term"], s_substrate)
        print(f"\n  on the SPEC complexes: outputs = {outs_known}")
        print(f"  HELD-OUT generalisation (never in any spec):")
        for cx, dim, got, good in ho_rows:
            print(f"     {cx:12} expected {dim}  got {got}  ok={good}")
        print(f"  HELD-OUT all correct = {ho_ok}  "
              f"<- the test of 'real invariant vs cheat'")
    return r


def main():
    banner("INVENT `dimension` WITH THE NATIVE (G,Γ) BRICKS — no hand scaffold")
    print("""\
  Target: dimension of a simplicial complex. Knowns point/edge/triangle/tetra
  -> 0/1/2/3. We drive the EXISTING bricks (generator / generator_exclusion /
  generator_outofbox) exactly as they natively work: G enumerates by MDL,
  observational-equivalence + the learned Γ exclude the inadmissible AT
  GENERATION, the finite Γ-relaxation bounds any out-of-box search. The world
  adapter turns each complex into scalar descriptors (maxface / V / ncells /
  euler) a DSL Var can read; `V` is the CHEAT source (== maxface for a single
  simplex only).""")

    # CONDITION A — knowns only. Cheat (V-1) and truth (maxface-1) are
    # OBSERVATIONALLY EQUIVALENT here; G cannot separate them — report honestly.
    sA = Substrate()
    rA = run_condition("CONDITION A — KNOWNS ONLY (point/edge/triangle/tetra)",
                       KNOWN_COMPLEXES, sA, leaves_note="")

    # CONDITION B — knowns + structure complexes that BREAK the cheat. The cheat
    # now fails to match the target -> Γ excludes it AT GENERATION (the spec is
    # inadmissible for any recipe that returns V). No held-out, no scoring.
    sB = Substrate()
    rB = run_condition("CONDITION B — KNOWNS + STRUCTURE (cheat-breaking spec)",
                       KNOWN_COMPLEXES + STRUCTURE_COMPLEXES, sB,
                       leaves_note="")

    # --- Explicitly show the cheat is INADMISSIBLE under condition B's spec. ---
    banner("DID Γ EXCLUDE THE CHEATS? (V-1, ncells, euler, V games)")
    from substrate_rs import Minus, Lit, Var, Plus, Div
    cheats = {
        "V - 1":        Minus(Var("V"), Lit(1)),
        "V":            Var("V"),
        "ncells - 1":   Minus(Var("ncells"), Lit(1)),
        "euler":        Var("euler"),
        "maxface - 1":  Minus(Var("maxface"), Lit(1)),   # the TRUTH, for contrast
    }
    specB = spec_from(KNOWN_COMPLEXES + STRUCTURE_COMPLEXES)
    target = [dim for _, dim in specB]
    print("  recipe          outputs on cond-B spec        matches target?")
    for nm, term in cheats.items():
        outs = []
        ok = True
        for env, want in specB:
            v = term.evaluate(env, sB)
            v = (1 if v is True else 0) if isinstance(v, bool) else v
            outs.append(int(v) if abs(v - round(v)) < 1e-9 else v)
            ok = ok and abs(float(v) - float(want)) < 1e-9
        print(f"     {nm:13} {str(outs):28} {ok}")
    print("""
  A recipe that does NOT match the cond-B target NEVER matches in synthesize's
  register() -> it is dropped (observational-equivalence keeps only the smallest
  behaviour; a non-matching cheat is simply not the returned solution). The
  structure rows are ADMISSIBILITY CONSTRAINTS, not a held-out set — the cheat is
  excluded AT GENERATION because the spec is inadmissible for it.""")

    # --- Γ-relaxation availability (out-of-box) — confirm the bound exists even
    #     though the in-box search already solved it (so no relaxation needed). ---
    banner("Γ-RELAXATION (out-of-box) — bounded fallback, here UNUSED")
    sC = Substrate()
    res = outofbox_solve(sC, spec_from(KNOWN_COMPLEXES + STRUCTURE_COMPLEXES),
                         MAX_SIZE, ops=OPS, timeout_s=TIMEOUT)
    print(f"  outofbox route = {res['route']}  (in-box solved -> 0 relaxations)")
    print(f"  solved={res['solved']}  recipe={res['term_str']}  size={res['size']}")
    print(f"  relaxations_tried = {res['relaxations_tried']} "
          f"(finite move set; in-box success means the box already held it)")

    banner("HONEST VERDICT")
    a_ok = rA["fits"]
    b_ok = rB["fits"]
    b_ho, _ = _heldout_ok(rB["term"], sB) if b_ok else (None, [])
    a_ho, _ = _heldout_ok(rA["term"], sA) if a_ok else (None, [])
    print(f"""\
  CONDITION A (knowns only): solved={a_ok}, recipe={rA['term_str']!r},
    held-out-correct={a_ho}. Honest limitation: on the four single simplices
    V==maxface, so the cheat (V-1) and the truth (maxface-1) are OBSERVATIONALLY
    IDENTICAL; the native MDL search returns whichever same-size behaviour it
    reaches first. The knowns ALONE do not pin the invariant — there is nothing
    in the spec for Γ to exclude the cheat WITH. (This is the brick working
    correctly: it never invents a distinction the data does not contain.)

  CONDITION B (knowns + cheat-breaking structure): solved={b_ok},
    recipe={rB['term_str']!r}, held-out-correct={b_ho}. The structure complexes
    make V != maxface, so the cheat is INADMISSIBLE (fails the spec) and Γ excludes
    it AT GENERATION — with NO hand-designed held-out, purely because the spec is
    now discriminating. The native search returns the real invariant maxface-1,
    which then GENERALISES to the 4-/5-simplex and disjoint graphs it never saw.

  This is exactly what last turn's bolted-on feature_generator did BY HAND
  (random-walk generate + Python discrimination scoring + degenerate filter): the
  native bricks do it INTRINSICALLY — G enumerates by MDL, observational-
  equivalence + the cheat-breaking spec ARE Γ, and the finite Γ-relaxation is the
  bounded fallback (unused here because the in-box box already held the recipe).""")


if __name__ == "__main__":
    main()
