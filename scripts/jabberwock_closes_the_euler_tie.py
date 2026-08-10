"""jabberwock_closes_the_euler_tie — the active-learning / counterexample loop
(reused from jabberwock_closes_the_tie.py) on a HARDER operator than dimension:
the EULER CHARACTERISTIC χ of a simplicial complex.

WHY HARDER THAN DIMENSION (the point of this script).
  For `dimension`, the slow DEFINITION (sum over k of [some k-simplex exists] − 1)
  is almost the RECIPE (maxface − 1): definition ≈ recipe, so the labeller is
  barely an oracle. For χ the two are GENUINELY COMPUTATIONALLY DISTINCT:

    · SLOW DEFINITION (the labeller / oracle) —
        χ(K) = Σ_{k=0..N} (−1)^k · |{k-simplices of K}|
      a brute STRUCTURAL computation: it must ENUMERATE THE WHOLE SIMPLICIAL
      CLOSURE of K (every face of every maximal face — the 2-skeleton of a
      7-simplex has 56 maximal faces but 92 closure faces the oracle must
      visit), bin them BY DIMENSION, and form the alternating sum. Grounded
      here from the agent's OWN held topology primitives (simplices_of_dim,
      cardinality, neg_one_pow, sum over a range) via ground_computation — NOT
      an answer key.

    · INVENTED RECIPE (what G+Γ must synthesize) —
        χ = V − E + F
      a CLOSED FORM over three CHEAP precomputed scalar descriptors. It reads
      three numbers and does two adds; it never enumerates a face, never sums
      over k, never looks at the closure. (Exact for complexes of dimension ≤ 2,
      which is the regime the knowns + the constructed family live in — a solid
      3-simplex would need a −T term the descriptor set does not carry, so the
      family is kept ≤ 2-dimensional and the recipe is the EXACT invariant
      there.)

  THE NON-CIRCULAR PROOF: the labeller runs a different algorithm on a different
  data structure (the full closure, summed by dimension) from the recipe (three
  scalar reads). The recipe is checked AGAINST the oracle on self-constructed
  inputs; it is never told the recipe.

THE TIE (and why naive knowns admit cheats).
  KNOWNS = point / edge / triangle (single simplices, dim ≤ 2). Each is
  contractible, so χ = 1 for ALL of them. On this spec the truth (V − E + F) is
  OBSERVATIONALLY TIED with cheap cheats that also output 1 everywhere — most
  sharply `ncells` (one maximal face each → 1) and the literal `1`. The native
  G, ordering by MDL size, returns the size-1 cheat `ncells` (or `1`); the
  size-5 truth is unreachable because nothing in the knowns separates them. G is
  RIGHT to do so — the spec contains no discriminator.

THE LOOP (active learning; CEGIS over native G+Γ).
  Because the truth is size 5 with SEVERAL smaller cheats between it and the
  knowns (not the single V−1 vs maxface−1 pair of the dimension case), one
  divergence row is not enough. The loop iterates:
      (1) SYNTHESIZE — native G returns the MDL-smallest recipe fitting the spec.
      (2) CONSTRUCT-A-DIVERGENCE — search a bounded, mechanically-generated
          family of complexes for the FIRST one where the returned recipe
          DISAGREES with the slow oracle (read off NATIVE term-evaluation vs the
          grounded χ). This is the counterexample.
      (3) SELF-LABEL it with the SLOW DEFINITION (the grounded χ recipe), not the
          invented recipe — the agent labels its own constructed input.
      (4) ADD the labelled row; Γ now EXCLUDES the falsified recipe at generation.
      (5) RE-RUN. Repeat until the synthesized recipe agrees with the oracle on
          the whole family — it has converged to the real invariant.

NATIVE vs GAP (reported honestly; same split as jabberwock_closes_the_tie.py).
  NATIVE, reused unchanged:
    · G + Γ            = domains.generator.synthesize (size-ordered, observational-
                          equivalence pruned). The MDL-smallest fitter.
    · term evaluation  = Term.evaluate(env, substrate) — used to read the recipe's
                          output on a candidate complex (no hand math).
    · the LABELLER     = the agent's OWN χ recipe, grounded via
                          compute_grounding.ground_computation from its held
                          topology primitives. The oracle, computationally
                          distinct from the recipe (proof above).
    · the world adapter= describe(maximal_faces) → {V,E,F,ncells,maxface}, the
                          mechanical complex→scalar-token translation. NOTE: it
                          does NOT expose `euler` — that would be reading the
                          answer; the recipe must be REBUILT from V,E,F.
  GENUINELY ABSENT (the active-learning step, the only new Python):
    · CONSTRUCT-A-DIVERGENCE / the CEGIS driver — there is no native routine that,
      given a synthesized recipe, builds an input where it diverges from the
      oracle and feeds the labelled divergence back. Built here, domain-general
      over (recipe-term, descriptor, oracle); carries NO math about χ (the label
      comes from the grounded oracle, the divergence from native evaluation, the
      exclusion from G+Γ size-ordering on the grown spec).

FAITHFUL (CLAUDE.md): a world-adapter driver sequencing native G, native term-
evaluation, and the agent's own grounded recipe as the labeller. No Rust, no
build, no parent_teacher, no _native beyond _native.Substrate(). Changes left
unstaged.

Run:
  ulimit -v 8388608
  PYTHONPATH=runners/dsl/python:. timeout 600 python3 scripts/jabberwock_closes_the_euler_tie.py
"""

from __future__ import annotations

import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "runners", "dsl", "python"))

from substrate_rs import _native
from domains import reason as _reason
from domains import compute_grounding as _cg
from domains.generator import synthesize


def banner(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


# ===========================================================================
# WORLD ADAPTER (mechanical) — a simplicial complex (list of maximal faces) ->
# scalar descriptors a DSL Var can read. Pure measurement, no decision. It does
# NOT expose `euler`: the recipe must be REBUILT from V/E/F (else it would read
# the answer the oracle computes).
# ===========================================================================

def _closure(maximal_faces):
    """ALL non-empty faces of all maximal faces (the simplicial closure)."""
    faces = set()
    for mf in maximal_faces:
        mf = tuple(sorted(mf))
        for r in range(1, len(mf) + 1):
            for c in itertools.combinations(mf, r):
                faces.add(c)
    return faces


def describe(maximal_faces):
    """Scalar descriptors off a complex (the DSL Var leaves the search reads).
    V/E/F = #0/1/2-simplices; ncells = #maximal faces; maxface = #verts in the
    largest. NO `euler` (that is the answer)."""
    faces = _closure(maximal_faces)
    by_dim: dict[int, int] = {}
    for f in faces:
        by_dim[len(f) - 1] = by_dim.get(len(f) - 1, 0) + 1
    return {"V": by_dim.get(0, 0), "E": by_dim.get(1, 0), "F": by_dim.get(2, 0),
            "ncells": len(maximal_faces),
            "maxface": max((len(f) for f in maximal_faces), default=0)}


# ===========================================================================
# THE LABELLER — the agent's OWN χ recipe, grounded into a callable. χ is
# computed by the SLOW DEFINITION (alternating sum over the full closure, binned
# by dimension), which is COMPUTATIONALLY DISTINCT from the V−E+F recipe G must
# invent. NOT an answer key — the label is whatever the grounded recipe computes.
# ===========================================================================

_SELF_EULER_DEF = (
    "euler(complex, N) = "
    "sum{ k in 0..N : neg_one_pow(k) * cardinality(simplices_of_dim(complex, k)) }")


def _make_labeller(substrate):
    caps = dict(_reason.CAPABILITIES)
    res = _cg.ground_computation(substrate, "euler", _SELF_EULER_DEF,
                                 capabilities=caps)
    if not (res.get("grounded") and res.get("installed")):
        raise RuntimeError("agent's own euler recipe failed to ground: "
                           f"{res.get('reason')}")
    fn = caps["euler"]
    print(f"  grounded χ from held primitives: {sorted(res.get('parts', []))}")

    def label(maximal_faces):
        faces = [list(f) for f in _closure(maximal_faces)]
        N = max((len(f) for f in faces), default=1)
        return int(fn({"complex": faces, "N": N}))

    return label


# ===========================================================================
# KNOWNS — single simplices, dim <= 2. Each is contractible -> χ = 1, and each
# has ncells == 1, so `ncells` / `1` / V−E+F are observationally TIED.
# ===========================================================================

KNOWN_COMPLEXES = [
    ("point",    [[0]]),
    ("edge",     [[0, 1]]),
    ("triangle", [[0, 1, 2]]),
]

# ===========================================================================
# THE DIVERGENCE FAMILY — a bounded, mechanically-generated set of dim<=2
# simplicial complexes from STANDARD constructions (disjoint copies, glued
# pairs, skeleta, loops). Nothing about χ is encoded; these are just "more than a
# single simplex" so V/E/F/ncells come apart. NO solid 3-simplex (would need a
# −T term the descriptors lack), keeping V−E+F the exact invariant.
# ===========================================================================

def _family():
    fam = []
    # disjoint copies of a k-simplex, k in {1,2} (dim<=2): ncells grows, χ = copies
    for k in (1, 2):
        base = list(range(k + 1))
        for copies in (2, 3):
            faces, off = [], 0
            for _ in range(copies):
                faces.append([off + i for i in base])
                off += k + 1
            fam.append((f"{copies}x{k}-simplex", faces))
    fam.append(("hollow-triangle", [[0, 1], [1, 2], [0, 2]]))          # S^1, χ=0
    fam.append(("square-loop", [[0, 1], [1, 2], [2, 3], [3, 0]]))      # S^1, χ=0
    fam.append(("filled-square", [[0, 1, 2], [0, 2, 3]]))              # disk, χ=1
    fam.append(("two-tri-share-edge", [[0, 1, 2], [1, 2, 3]]))        # disk, χ=1
    fam.append(("hollow-tetra-S2",
                [list(c) for c in itertools.combinations(range(4), 3)]))  # S^2, χ=2
    fam.append(("two-edges-share-v", [[0, 1], [1, 2]]))                # path, χ=1
    fam.append(("path-graph7", [[i, i + 1] for i in range(7)]))        # tree, χ=1
    fam.append(("star5", [[0, i] for i in range(1, 6)]))               # tree, χ=1
    fam.append(("triangle-with-tail", [[0, 1, 2], [2, 3]]))           # χ=1
    return fam


# ===========================================================================
# (2) CONSTRUCT A DIVERGENCE — given the synthesized recipe, find the FIRST
# family complex on which it DISAGREES with the slow oracle (native term-eval vs
# grounded χ). The genuinely-absent active-learning step.
# ===========================================================================

def find_counterexample(substrate, recipe_term, labeller, used_names):
    for name, faces in _family():
        if name in used_names:
            continue
        env = describe(faces)
        got = recipe_term.evaluate(env, substrate)
        got = (1 if got is True else 0) if isinstance(got, bool) else got
        true_chi = labeller(faces)                       # SLOW oracle labels it
        if abs(float(got) - float(true_chi)) > 1e-9:
            return name, faces, env, got, true_chi
    return None


# ===========================================================================
# THE LOOP (CEGIS over native G+Γ).
# ===========================================================================

OPS = ("Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
       "Gt", "Lt", "Eq", "IfThenElse")
MAX_SIZE = 7
TIMEOUT = 120.0
MAX_ROUNDS = 12


def spec_from(rows, labeller):
    return [(describe(mf), labeller(mf)) for _, mf in rows]


def main():
    banner("THE JABBERWOCK CLOSES THE EULER-χ TIE — active-learning on a HARD op")
    print("""\
  Operator = Euler characteristic χ. The LABELLER is the SLOW DEFINITION
  (alternating sum over the FULL CLOSURE binned by dimension), grounded from the
  agent's own topology primitives — COMPUTATIONALLY DISTINCT from the recipe
  V−E+F (three scalar reads, no closure, no sum over k). Knowns = point/edge/
  triangle (all χ=1, all ncells=1): the truth is TIED with cheap cheats. The loop
  must construct divergences, self-label them with the oracle, and converge.""")

    s = _native.Substrate()
    banner("GROUND THE ORACLE (the agent's own χ, the slow definition)")
    labeller = _make_labeller(s)

    # show the labeller is a real oracle: knowns are an observational tie
    banner("STEP 0 — native G on KNOWNS ONLY (the tie: χ=1 == ncells == 1)")
    rows = list(KNOWN_COMPLEXES)
    spec0 = spec_from(rows, labeller)
    for (nm, mf), (e, chi) in zip(rows, spec0):
        print(f"     {nm:10} {e}  -> χ={chi}")
    r0 = synthesize(s, spec0, ops=OPS, max_size=MAX_SIZE, timeout_s=TIMEOUT)
    print(f"  native MDL recipe = {r0['term_str']!r}  size={r0['size']}  "
          f"fits={r0['fits']}   <- a CHEAT; the spec cannot pin V−E+F")

    # --- the CEGIS active-learning loop ---
    banner("THE LOOP — synthesize -> construct a divergence -> self-label -> re-run")
    history = []
    converged = False
    for rnd in range(MAX_ROUNDS):
        spec = spec_from(rows, labeller)
        r = synthesize(s, spec, ops=OPS, max_size=MAX_SIZE, timeout_s=TIMEOUT)
        if not r["fits"]:
            print(f"  round {rnd}: NO FIT (halt={r['halt_reason']}) — broke here.")
            break
        ce = find_counterexample(s, r["term"], labeller,
                                 used_names={nm for nm, _ in rows})
        if ce is None:
            print(f"  round {rnd}: recipe {r['term_str']!r} (size {r['size']}) "
                  f"AGREES with the oracle on the whole family -> CONVERGED.")
            converged = True
            history.append((rnd, r["term_str"], r["size"], None))
            break
        name, faces, env, got, true_chi = ce
        print(f"  round {rnd}: recipe {r['term_str']!r} (size {r['size']}) "
              f"-> counterexample {name}: recipe says {got}, ORACLE says "
              f"{true_chi}")
        print(f"            {env}  -> self-label χ={true_chi}; Γ now excludes "
              f"this recipe")
        rows.append((name, faces))
        history.append((rnd, r["term_str"], r["size"], name))

    # --- final recipe ---
    spec_final = spec_from(rows, labeller)
    r_final = synthesize(s, spec_final, ops=OPS, max_size=MAX_SIZE,
                         timeout_s=TIMEOUT)

    banner("THE INVENTED RECIPE vs THE SLOW ORACLE (non-circularity)")
    print(f"  invented recipe (G+Γ over cheap descriptors) = {r_final['term_str']!r}")
    print(f"  slow oracle (the labeller, grounded)         = "
          f"χ = Σ_k (−1)^k·|k-simplices|  over the FULL CLOSURE")
    big = [list(c) for c in itertools.combinations(range(8), 3)]   # 2-skel(simp7)
    print(f"  distinctness: on 2-skeleton(7-simplex) the oracle enumerates "
          f"{len(_closure(big))} closure faces + an alternating sum;")
    print(f"                the recipe reads 3 scalars {describe(big)} and does "
          f"two adds. DIFFERENT algorithm, DIFFERENT data structure.")

    # --- held-out generalisation: never-in-spec dim<=2 complexes ---
    banner("HELD-OUT — confirm the survivor is the real invariant (never in spec)")
    HELD = [
        ("4x2-simplex", [[3 * i, 3 * i + 1, 3 * i + 2] for i in range(4)]),  # χ=4
        ("pentagon-loop", [[i, (i + 1) % 5] for i in range(5)]),            # S^1 χ=0
        ("annulus(2 tri ring)",
         [[0, 1, 3], [1, 3, 4], [1, 2, 4], [2, 4, 5], [2, 0, 5], [0, 5, 3]]),
        ("wedge-2-triangles", [[0, 1, 2], [2, 3, 4]]),                      # χ=1
    ]
    all_ok = True
    for nm, mf in HELD:
        e = describe(mf)
        got = r_final["term"].evaluate(e, s)
        got = (1 if got is True else 0) if isinstance(got, bool) else got
        tru = labeller(mf)
        ok = abs(float(got) - float(tru)) < 1e-9
        all_ok = all_ok and ok
        print(f"     {nm:22} recipe={got:>3}  oracle χ={tru:>3}  ok={ok}")

    banner("VERDICT")
    is_euler = r_final["term_str"] in ("(V + (F - E))", "(V + (F + neg(E)))",
                                       "((V - E) + F)", "(F + (V - E))")
    rounds = sum(1 for h in history if h[3] is not None)
    cheats = [h[1] for h in history if h[3] is not None]
    print(f"""\
  OPERATOR: Euler characteristic χ of a simplicial complex (dim ≤ 2 regime).
  LABELLER (slow def): χ = Σ_k (−1)^k·|k-simplices| over the FULL closure, binned
    by dimension — grounded from the agent's own topology primitives. The RECIPE
    G invents is V−E+F (three scalar reads). They are COMPUTATIONALLY DISTINCT
    (different algorithm + data structure); the non-circular proof above.
  STEP 0 (knowns only): native MDL recipe = {r0['term_str']!r} — a CHEAT, because
    χ=1==ncells==1 on every single simplex; the spec held nothing to separate it.
  DISCRIMINATING ROUNDS: {rounds}. Cheats discriminated, in order: {cheats}.
  FINAL invented recipe = {r_final['term_str']!r}.
  Held-out all correct = {all_ok}.

  SELF-CONVERGED ON THE EULER RECIPE (cheats excluded) = {converged and is_euler and all_ok}.

  HONEST NOTES:
    · The recipe V−E+F is the EXACT χ only for dim ≤ 2 complexes (a solid
      k-simplex needs the −T… terms the {{V,E,F}} descriptor set does not carry).
      The knowns + family are kept dim ≤ 2, so the recipe is the real invariant
      THERE; the descriptor set, not the loop, is the ceiling. If you want the
      general χ, extend describe() with #3-cells etc. — the loop is unchanged.
    · Reused as-is: G+Γ (synthesize), term-eval, the grounded oracle. The only new
      Python is the divergence-constructor + CEGIS driver (the genuinely-absent
      active-learning step), carrying no math about χ.""")


if __name__ == "__main__":
    main()
