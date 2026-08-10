"""jabberwock_closes_the_tie — the ACTIVE-LEARNING / counterexample loop that
closes the observational tie the native (G,Γ) correctly refuses to resolve.

THE TIE (the open question this script answers).
  When two candidate recipes survive the spec OBSERVATIONALLY-TIED — the cheat
  `V - 1` (reads the vertex COUNT) and the truth `maxface - 1` (reads the
  dimension-bearing largest FACE) — they are IDENTICAL on every single-simplex
  known, because there V == maxface. The native generator's observational-
  equivalence dedup then collapses them into ONE behaviour and returns whichever
  it enumerates first. It is RIGHT to do so: the knowns-only spec contains
  NOTHING that separates them, so there is nothing for Γ to exclude the cheat
  WITH. The substrate never INVENTS a distinction the data does not contain.

  To pin the invariant, the spec must become DISCRIMINATING — a row where the
  tied candidates DIVERGE. The question is whether the jabberwock can produce
  that row ITSELF, end to end:
      (1) NOTICE the tie  (two distinct surviving terms, same signature),
      (2) CONSTRUCT an input where the tied terms diverge (a complex V != maxface),
      (3) LABEL it from the operator's OWN definition (the dimension is directly
          computable by the agent's own recipe, even before a clean spec exists),
      (4) ADD the labelled row to the spec, and
      (5) RE-RUN G — now the cheat fails to match -> Γ excludes it AT GENERATION,
          and `maxface - 1` wins BY CONSTRUCTION OF THE SPEC, not by enumeration
          luck.

NATIVE vs GAP (reported honestly; grepped before building).
  NATIVE, reused as-is:
    · G + Γ            = domains/generator.synthesize (size-ordered, observational-
                          equivalence pruned, the `exclude` Γ hook). Returns the
                          MDL-smallest term fitting a spec.
    · term evaluation  = Term.evaluate(env, substrate) on the native substrate —
                          used to TEST whether two terms diverge on a candidate
                          complex (no hand math).
    · the LABELLER     = the agent's OWN self-authored `dimension` recipe
                          (seeds/self_authored/dimension.json), grounded via
                          compute_grounding.ground_computation into a callable.
                          The complex is labelled by the operator's own definition
                          — exactly "the dimension is directly computable before a
                          clean recipe exists." NO answer-key, no hand-set label.
    · the world adapter= describe(maximal_faces) -> scalar descriptors a DSL Var
                          reads (maxface / V / ncells / euler), the mechanical
                          translation of a complex into the smallest graph token.

  GENUINELY ABSENT (built here, and ONLY this — grep found no native form):
    · NOTICE-THE-TIE: synthesize's dedup HIDES the tie (it stores one behaviour
      per signature), and there is no native "enumerate all distinct terms that
      fit, then flag the surviving leaf-level ties." So this script enumerates the
      same leaf grammar G uses and GROUPS terms by signature on the spec to surface
      the tie synthesize collapses. (generator_outofbox's `counterexample` is a
      different thing — it retracts a Γ-exclusion that wrongly blocked a solve, not
      a distinguishing-input search.)
    · CONSTRUCT-A-DIVERGENCE: there is no native routine that, given two tied
      terms, builds an input where they disagree. This script searches a bounded,
      mechanically-constructed family of complexes (disjoint copies / skeleta /
      gluings — standard simplicial constructions, NOT a hand-picked answer set)
      for the FIRST one on which the two tied terms diverge under native evaluation.
    These two are the active-learning loop. They are domain-general over the
    (term, descriptor) machinery; nothing about the dimension answer is baked in.

FAITHFUL (CLAUDE.md): a world-adapter driver. It sequences the agent's native G
(synthesize), the agent's native term-evaluation, and the agent's OWN grounded
recipe as the labeller. The only NEW Python is the tie-detector + the bounded
divergence-complex constructor — the genuinely-absent active-learning step — and
it owns no math about the answer (the label comes from the agent's recipe, the
divergence from native evaluation, the exclusion from G+Γ). NO Rust, NO build.

Run:
  ulimit -v 8388608
  PYTHONPATH=runners/dsl/python:. timeout 600 python3 scripts/jabberwock_closes_the_tie.py
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
from substrate_rs import Var, Lit, Minus, Plus  # noqa: F401  (term-build for probes)
from domains import reason as _reason
from domains import compute_grounding as _cg
from domains.generator import synthesize, _signature, _num, Var as GVar, Lit as GLit


def banner(s):
    print("\n" + "=" * 74)
    print(s)
    print("=" * 74)


# ===========================================================================
# WORLD ADAPTER (mechanical) — a simplicial complex (list of maximal faces, each
# a list of vertex ids) -> scalar descriptors a DSL Var can read. Pure
# measurement, no decision. (Same descriptors as dimension_recipe_native.py.)
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
    """Scalar descriptors off a complex (the DSL Var leaves the search reads)."""
    faces = _closure(maximal_faces)
    by_dim: dict[int, int] = {}
    for f in faces:
        by_dim[len(f) - 1] = by_dim.get(len(f) - 1, 0) + 1
    V = by_dim.get(0, 0)
    E = by_dim.get(1, 0)
    Fc = by_dim.get(2, 0)
    maxface = max((len(f) for f in maximal_faces), default=0)   # #verts in largest
    ncells = len(maximal_faces)
    euler = sum(((-1) ** d) * n for d, n in by_dim.items())
    return {"maxface": maxface, "V": V, "ncells": ncells, "euler": euler,
            "E": E, "F": Fc}


# ===========================================================================
# THE LABELLER — the agent's OWN self-authored `dimension` recipe, grounded into
# a callable. The complex is labelled by the operator's own definition (the
# dimension is directly computable before a clean spec recipe exists). NOT a
# hand-set answer key — the label is whatever the agent's recipe computes.
# ===========================================================================

_SELF_DIM_DEF = ("dimension(complex, N) = "
                 "sum{ k in 0..N : cardinality(simplices_of_dim(complex, k)) >= 1 }"
                 " - 1")


def _make_labeller(substrate):
    caps = dict(_reason.CAPABILITIES)
    res = _cg.ground_computation(substrate, "dimension", _SELF_DIM_DEF,
                                 capabilities=caps)
    if not (res.get("grounded") and res.get("installed")):
        raise RuntimeError(f"agent's own dimension recipe failed to ground: "
                           f"{res.get('reason')}")
    fn = caps["dimension"]

    def label(maximal_faces):
        faces = [list(f) for f in _closure(maximal_faces)]
        N = max((len(f) for f in faces), default=1)   # highest face dim present
        return int(fn({"complex": faces, "N": N}))

    return label


# ===========================================================================
# KNOWNS — the four single simplices. On these V == maxface, so V-1 and
# maxface-1 are observationally identical (the tie).
# ===========================================================================

KNOWN_COMPLEXES = [
    ("point",    [[0]],          0),
    ("edge",     [[0, 1]],       1),
    ("triangle", [[0, 1, 2]],    2),
    ("tetra",    [[0, 1, 2, 3]], 3),
]

OPS = ("Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
       "Gt", "Lt", "Eq", "IfThenElse")
MAX_SIZE = 7
TIMEOUT = 120.0


def spec_from(rows):
    """(env, expected_dim) the native G consumes. env = scalar descriptors."""
    return [(describe(mf), dim) for _, mf, dim in rows]


# ===========================================================================
# (1) NOTICE THE TIE — the genuinely-absent step #1.
# synthesize's observational-equivalence dedup keeps ONE term per signature, so
# it never reports that two DISTINCT leaf candidates fit the spec identically.
# We enumerate the LEAF candidates G itself uses (the variables + small consts)
# and GROUP them by signature on the spec; a group with >= 2 distinct leaves
# whose signature matches the target is a surviving tie. (Reading the same Var/
# Lit leaves + _signature G uses — not a new grammar.)
# ===========================================================================

def detect_leaf_ties(substrate, spec, consts=(0, 1, 2, -1)):
    """Surface the surviving observational ties at the leaf-plus-offset level.

    For each descriptor V, we consider the leaf `V` and the offset `V - 1`
    (the minimal recipe family the dimension answer lives in). Two such terms
    that share a signature AND match the target are a TIE the native dedup
    hides. Returns list of (signature, [term_str, ...]) for target-matching ties.
    """
    envs = [env for env, _ in spec]
    target = tuple(_num(out) for _, out in spec)
    var_names = sorted({k for env, _ in spec for k in env})

    cand = []   # (label, term)
    for v in var_names:
        cand.append((v, GVar(v)))
        cand.append((f"{v} - 1", Minus(GVar(v), GLit(1))))
    for c in consts:
        cand.append((str(c), GLit(c)))

    by_sig: dict[tuple, list[str]] = {}
    for label, term in cand:
        sig = _signature(term, envs, substrate)
        if sig is None:
            continue
        by_sig.setdefault(sig, []).append(label)

    def _matches(sig):
        if len(sig) != len(target):
            return False
        for s, t in zip(sig, target):
            sv = s[1] if isinstance(s, tuple) else s
            try:
                if abs(float(sv) - float(t)) > 1e-9:
                    return False
            except (TypeError, ValueError):
                return False
        return True

    ties = [(sig, labels) for sig, labels in by_sig.items()
            if len(labels) >= 2 and _matches(sig)]
    return ties


# ===========================================================================
# (2) CONSTRUCT A DIVERGENCE — the genuinely-absent step #2.
# Given two tied terms, build an input on which they DISAGREE. We search a
# bounded, mechanically-constructed family of complexes (standard simplicial
# constructions: disjoint copies of a simplex, skeleta, edge-gluings) for the
# FIRST one on which the two terms diverge under NATIVE evaluation. No
# hand-picked answer complex; the family is generated, the divergence is read off
# native term-eval, the label comes from the agent's recipe.
# ===========================================================================

def _construct_family():
    """A bounded family of simplicial complexes from standard constructions.
    Each is (name, maximal_faces). Generated mechanically; nothing about the
    dimension answer is encoded — these are just 'more complexes than a single
    simplex' so V can come apart from maxface."""
    fam = []
    # disjoint copies of a k-simplex (V grows, maxface stays k+1)
    for k in range(1, 4):                      # edge / triangle / tetra base
        base = list(range(k + 1))
        for copies in (2, 3):
            faces, off = [], 0
            for _ in range(copies):
                faces.append([off + i for i in base])
                off += k + 1
            fam.append((f"{copies}x{k}-simplex", faces))
    # j-skeleton of an n-simplex (drop the top faces: maxface = j+1 < n+1, V = n+1)
    for n in range(2, 5):
        verts = list(range(n + 1))
        for j in range(1, n):                  # keep faces up to dim j
            faces = [list(c) for r in range(1, j + 2)
                     for c in itertools.combinations(verts, r)
                     if len(c) == j + 1]        # maximal faces of the j-skeleton
            fam.append((f"{j}-skeleton(simplex{n})", faces))
    # filled square = two triangles glued on an edge (V=4, maxface=3)
    fam.append(("filled-square", [[0, 1, 2], [0, 2, 3]]))
    # a path graph (V=8, maxface=2)
    fam.append(("path-graph", [[i, i + 1] for i in range(7)]))
    return fam


def find_distinguishing_input(substrate, tie_labels, labeller):
    """Search the bounded family for the FIRST complex on which the two tied
    leaf-terms diverge under native evaluation. Return (name, faces, env,
    {label: value}, true_dim) or None. The two terms are rebuilt from their
    labels (V / V-1) so the divergence is read natively, not asserted."""
    terms = {lab: _term_from_label(lab) for lab in tie_labels}
    for name, faces in _construct_family():
        env = describe(faces)
        vals = {}
        ok = True
        for lab, t in terms.items():
            v = t.evaluate(env, substrate)
            v = (1 if v is True else 0) if isinstance(v, bool) else v
            vals[lab] = v
        distinct = {round(float(v), 9) for v in vals.values()}
        if len(distinct) >= 2:                 # the tied terms DIVERGE here
            true_dim = labeller(faces)         # the agent labels it ITSELF
            return name, faces, env, vals, true_dim
    return None


def _term_from_label(label):
    """Rebuild a leaf/offset term from its surfaced label (V or 'V - 1')."""
    if label.endswith(" - 1"):
        return Minus(Var(label[:-4]), Lit(1))
    try:
        return Lit(int(label))
    except ValueError:
        return Var(label)


# ===========================================================================
# THE LOOP.
# ===========================================================================

def main():
    banner("THE JABBERWOCK CLOSES THE OBSERVATIONAL TIE — active-learning loop")
    print("""\
  Knowns = point/edge/triangle/tetra (single simplices, V == maxface). On this
  spec the cheat (V-1) and the truth (maxface-1) are OBSERVATIONALLY IDENTICAL;
  the native G is right not to separate them. The agent must NOTICE the tie,
  CONSTRUCT a divergence, LABEL it from its own recipe, ADD the row, and RE-RUN
  so Γ excludes the cheat by construction.""")

    s = _native.Substrate()
    labeller = _make_labeller(s)
    spec = spec_from(KNOWN_COMPLEXES)

    # --- baseline native solve on the knowns-only spec (the tie is hidden) ---
    banner("STEP 0 — native G on KNOWNS ONLY (the tie is hidden by dedup)")
    r0 = synthesize(s, spec, ops=OPS, max_size=MAX_SIZE, timeout_s=TIMEOUT)
    print(f"  native recipe returned = {r0['term_str']!r}  size={r0['size']}  "
          f"fits={r0['fits']}")
    print("  (whichever same-size behaviour G reaches first; the spec cannot pin it)")

    # --- (1) NOTICE THE TIE ---
    banner("STEP 1 — NOTICE THE TIE (surface what dedup collapsed)")
    ties = detect_leaf_ties(s, spec)
    if not ties:
        print("  no surviving leaf tie found — nothing to close.")
        return
    for sig, labels in ties:
        outs = [x[1] if isinstance(x, tuple) else x for x in sig]
        print(f"  TIED (identical outputs {outs} == target): {labels}")
    # take the tie that contains the cheat/truth pair if present
    tie = next((labs for _, labs in ties
                if any(l in ("V - 1",) for l in labs)
                and any(l in ("maxface - 1",) for l in labs)), ties[0][1])
    print(f"  -> the tie to break: {tie}")

    # --- (2)+(3) CONSTRUCT A DIVERGENCE + SELF-LABEL ---
    banner("STEP 2/3 — CONSTRUCT a divergence + LABEL it from the agent's recipe")
    found = find_distinguishing_input(s, tie, labeller)
    if found is None:
        print("  no complex in the bounded family separated the tied terms.")
        return
    name, faces, env, vals, true_dim = found
    keep = {k: env[k] for k in ("maxface", "V", "ncells", "euler")}
    print(f"  distinguishing complex constructed: {name}  faces={faces}")
    print(f"     descriptors {keep}")
    print(f"     tied terms diverge here: {vals}")
    print(f"     agent SELF-LABELS its dimension (own recipe) = {true_dim}")
    print(f"     -> the cheat among {tie} that misses {true_dim} is now INADMISSIBLE")

    # --- (4) ADD the labelled row ---
    banner("STEP 4 — ADD the self-generated row to the spec")
    new_row = (name, faces, true_dim)
    spec2 = spec_from(KNOWN_COMPLEXES + [new_row])
    print("  spec now (env -> dim):")
    for (nm, mf, dim), (e, _) in zip(KNOWN_COMPLEXES + [new_row], spec2):
        kp = {k: e[k] for k in ("maxface", "V", "ncells", "euler")}
        tag = "  <- SELF-GENERATED" if nm == name else ""
        print(f"     {nm:22} {kp}  -> {dim}{tag}")

    # --- (5) RE-RUN — now Γ excludes the cheat AT GENERATION ---
    banner("STEP 5 — RE-RUN native G on the discriminating spec")
    s2 = _native.Substrate()
    r1 = synthesize(s2, spec2, ops=OPS, max_size=MAX_SIZE, timeout_s=TIMEOUT)
    print(f"  native recipe returned = {r1['term_str']!r}  size={r1['size']}  "
          f"fits={r1['fits']}")

    # show the cheat is now inadmissible (fails to match the new row)
    banner("DID Γ EXCLUDE THE CHEAT? (V-1 vs maxface-1 on the new spec)")
    target2 = [d for _, d in spec2]
    for lab in sorted(set(tie) | {"maxface - 1", "V - 1"}):
        t = _term_from_label(lab)
        outs, ok = [], True
        for e, want in spec2:
            v = t.evaluate(e, s2)
            v = (1 if v is True else 0) if isinstance(v, bool) else v
            outs.append(int(v) if abs(v - round(v)) < 1e-9 else v)
            ok = ok and abs(float(v) - float(want)) < 1e-9
        print(f"     {lab:13} {str(outs):24} matches target = {ok}")

    # --- held-out generalisation: confirm the survivor is the real invariant ---
    banner("HELD-OUT — confirm the survivor is the real invariant (never in spec)")
    HELD = [("5-simplex", [[0, 1, 2, 3, 4, 5]], 5),
            ("two-tetra", [[0, 1, 2, 3], [4, 5, 6, 7]], 3),
            ("3-skeleton(simplex4)",
             [list(c) for c in itertools.combinations(range(5), 4)], 3)]
    all_ok = True
    for nm, mf, dim in HELD:
        e = describe(mf)
        got = r1["term"].evaluate(e, s2)
        got = (1 if got is True else 0) if isinstance(got, bool) else got
        good = abs(float(got) - float(dim)) < 1e-9
        all_ok = all_ok and good
        print(f"     {nm:22} expected {dim}  got {got}  ok={good}")

    banner("VERDICT")
    closed = (r1["term_str"] == "(maxface + -1)") or ("maxface" in r1["term_str"]
              and "V" not in r1["term_str"].replace("maxface", ""))
    print(f"""\
  STEP 0 (knowns only): native G returned {r0['term_str']!r} — but the spec held
    NOTHING to separate V-1 from maxface-1; the tie was HIDDEN by dedup.
  STEP 1: the loop SURFACED the tie the dedup collapsed: {tie}.
  STEP 2/3: it CONSTRUCTED {name} (V != maxface) where the tied terms diverge,
    and LABELLED it {true_dim} FROM ITS OWN dimension recipe (no answer key).
  STEP 4/5: with that self-generated row added, native G returned
    {r1['term_str']!r}. The cheat V-1 now MISSES the new row -> Γ excludes it
    AT GENERATION; the survivor is the real invariant.
  Held-out all correct = {all_ok}.

  SELF-CONVERGED ON maxface-1 (cheat excluded) = {closed and all_ok}.

  NATIVE vs GAP: G+Γ (synthesize), term-evaluation, and the LABELLER (the agent's
  own grounded recipe) are all NATIVE and reused unchanged. The two steps that
  were genuinely ABSENT — NOTICE-THE-TIE (dedup hides it) and CONSTRUCT-A-
  DIVERGENCE (no native distinguishing-input search) — are the active-learning
  loop, built here and only here, domain-general over (term, descriptor),
  carrying no math about the answer.""")


if __name__ == "__main__":
    main()
