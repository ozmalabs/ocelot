"""cegis_faculty — THE COUNTEREXAMPLE-GUIDED SYNTHESIS FACULTY (the permanent
home of the descriptor-grounding + CEGIS active-learning loop).

This promotes the loop proved in scripts/jabberwock_closes_the_euler_tie.py and
scripts/jabberwock_lifts_the_euler_descriptor_ceiling.py from a one-off script
into a held faculty, structured like the other domains/*.py faculties (cf.
faculty_template.py: a frozen-core mechanism + thin params).

TWO PARTS, one shape each:

  (1) THE GENERAL CEGIS CORE — `cegis_synthesize(...)`, DOMAIN-AGNOSTIC over
      (descriptors, oracle, input-family). It carries NO operator-specific math.
      The loop:
          SYNTHESIZE  — native G+Γ (domains.generator.synthesize) returns the
                        MDL-smallest recipe over the DESCRIPTORS fitting the spec.
          CONSTRUCT-A-DIVERGENCE — search the self-constructed input family for
                        the FIRST input where the surviving recipe DISAGREES with
                        the ORACLE (native Term.evaluate vs the grounded oracle).
          SELF-LABEL  — label that divergence with the ORACLE (not the recipe).
          ADD the row — Γ now excludes the falsified recipe at generation.
          RE-SYNTHESIZE — repeat until the recipe agrees with the oracle on the
                        whole family (CONVERGED to the real invariant).
      The only thing this brings that native G+Γ lacks is the active-learning
      driver (construct-a-divergence + feed-the-labelled-row-back). It is
      general over any (descriptors, oracle, input-family): no χ, no topology.

  (2) THE DESCRIPTOR-GROUNDING HELPER — `ground_cell_count_descriptors(...)`, the
      simplicial-complex INSTANCE of a grounded descriptor family. The hand-listed
      {V, E, F} is just k = 0, 1, 2 of ONE parametric family
          cell_count(complex, k) = cardinality(simplices_of_dim(complex, k))
      whose BOTH operands are the agent's OWN held topology primitives (reason.py:
      simplices_of_dim, cardinality). The family is GROUNDED via the SAME
      compute_grounding.ground_computation the oracle uses — for k = 0..maxdim — so
      the descriptors are grounded, not hand-listed. The 3-cell count the {V,E,F}
      set was missing FALLS OUT of the agent's own composition the moment the
      family runs to a dimension-3 complex.

      The matching ORACLE — the agent's own slow χ (the alternating sum over the
      full closure, binned by dimension) — is grounded the same way by
      `ground_euler_oracle(...)`. χ is computationally DISTINCT from the recipe
      (different algorithm + data structure): the non-circular proof.

NATIVE vs GAP (the honest split, unchanged from the scripts):
  NATIVE, reused as-is:
    · G + Γ            = domains.generator.synthesize (size-ordered, observational-
                          equivalence pruned). The MDL-smallest fitter.
    · term evaluation  = Term.evaluate(env, substrate).
    · grounding        = compute_grounding.ground_computation over the agent's own
                          held primitives (reason.CAPABILITIES). Grounds BOTH the
                          descriptors and the oracle.
  GENUINELY ABSENT (the only thing this module builds):
    · the CEGIS driver — construct-a-divergence + feed-the-labelled-row-back. It is
      domain-general over (descriptors, oracle, input-family); carries no math
      about any specific operator.

FAITHFUL (CLAUDE.md): a world-adapter-style driver sequencing native G, native
term-evaluation, and the agent's own grounded oracle/descriptors. No Rust, no
build, no parent_teacher, no _native beyond _native.Substrate() (which the caller
owns — this module takes a substrate handle).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Sequence, Tuple

from domains import reason as _reason
from domains import compute_grounding as _cg
from domains.generator import synthesize


# ===========================================================================
# PART 1 — THE GENERAL CEGIS CORE.
#
# Domain-agnostic over:
#   describe : input -> {descriptor_name: scalar}   (the DSL Var leaves G reads)
#   oracle   : input -> number                      (the slow self-label)
#   family   : () -> iterable[(name, input)]         (the self-constructed inputs)
#   knowns   : iterable[(name, input)]               (the seed spec rows)
# It carries NO operator-specific math: the label comes from the oracle, the
# divergence from native term-evaluation, the exclusion from G+Γ size-ordering on
# the grown spec.
# ===========================================================================

Describe = Callable[[Any], dict]
Oracle = Callable[[Any], Any]
Family = Callable[[], Sequence[Tuple[str, Any]]]


def _as_number(v: Any) -> float:
    """Native Term.evaluate returns Python bools for comparisons; fold to 0/1."""
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    return float(v)


@dataclass
class CegisRound:
    rnd: int
    term_str: Optional[str]
    size: Optional[int]
    counterexample: Optional[str]   # name of the divergence found, or None at convergence


@dataclass
class CegisResult:
    """The result of a CEGIS run."""
    final_term: Any = None                       # the surviving native Term
    final_term_str: Optional[str] = None
    final_size: Optional[int] = None
    converged: bool = False                       # agrees with the oracle on the whole family
    fits: bool = False                            # the final synthesis fitted its spec
    step0_term_str: Optional[str] = None          # the knowns-only cheat
    rounds: List[CegisRound] = field(default_factory=list)
    discriminated: List[str] = field(default_factory=list)   # cheat recipes excluded, in order
    rows: List[Tuple[str, Any]] = field(default_factory=list)  # the grown spec (name, input)

    def evaluate(self, describe: Describe, inp: Any, substrate) -> float:
        """Read the final recipe's numeric output on an input (folding bools)."""
        return _as_number(self.final_term.evaluate(describe(inp), substrate))

    def uses(self, descriptor_name: str) -> bool:
        return bool(self.final_term_str) and descriptor_name in self.final_term_str


def find_counterexample(substrate, recipe_term, describe: Describe, oracle: Oracle,
                        family: Family, used_names: set) -> Optional[tuple]:
    """CONSTRUCT-A-DIVERGENCE: the first family input on which the synthesized
    recipe DISAGREES with the slow oracle (native term-eval vs grounded oracle).
    Returns (name, input, env, recipe_out, oracle_label) or None if it agrees
    everywhere (convergence)."""
    for name, inp in family():
        if name in used_names:
            continue
        env = describe(inp)
        got = _as_number(recipe_term.evaluate(env, substrate))
        label = _as_number(oracle(inp))
        if abs(got - label) > 1e-9:
            return name, inp, env, got, label
    return None


def cegis_synthesize(
    substrate,
    describe: Describe,
    oracle: Oracle,
    family: Family,
    knowns: Sequence[Tuple[str, Any]],
    *,
    ops: Sequence[str],
    max_size: int = 9,
    timeout_s: float = 240.0,
    max_rounds: int = 16,
    verbose: bool = False,
) -> CegisResult:
    """THE GENERAL CEGIS LOOP over native G+Γ.

    SYNTHESIZE (native G+Γ over the descriptors) -> CONSTRUCT-A-DIVERGENCE (a
    self-constructed input where the survivor diverges from the oracle) ->
    SELF-LABEL it with the oracle -> ADD the row -> RE-SYNTHESIZE, until the
    recipe agrees with the oracle on the whole family.

    Domain-agnostic: `describe` maps an input to scalar descriptors (the Var
    leaves), `oracle` is the slow self-label, `family` yields self-constructed
    inputs, `knowns` seed the spec. No operator-specific math lives here.
    """
    def _spec(rows):
        return [(describe(inp), _as_number(oracle(inp))) for _, inp in rows]

    rows = list(knowns)
    result = CegisResult(rows=rows)

    # STEP 0 — native G on the knowns only (exhibit the observational tie).
    spec0 = _spec(rows)
    r0 = synthesize(substrate, spec0, ops=ops, max_size=max_size, timeout_s=timeout_s)
    result.step0_term_str = r0.get("term_str")
    if verbose:
        print(f"  step 0 (knowns only): native MDL recipe = {r0.get('term_str')!r} "
              f"size={r0.get('size')} fits={r0.get('fits')}")

    # THE LOOP.
    for rnd in range(max_rounds):
        spec = _spec(rows)
        r = synthesize(substrate, spec, ops=ops, max_size=max_size, timeout_s=timeout_s)
        if not r["fits"]:
            if verbose:
                print(f"  round {rnd}: NO FIT (halt={r['halt_reason']})")
            result.rounds.append(CegisRound(rnd, None, None, None))
            break
        ce = find_counterexample(substrate, r["term"], describe, oracle, family,
                                 used_names={nm for nm, _ in rows})
        if ce is None:
            if verbose:
                print(f"  round {rnd}: recipe {r['term_str']!r} (size {r['size']}) "
                      f"AGREES with the oracle on the whole family -> CONVERGED.")
            result.converged = True
            result.rounds.append(CegisRound(rnd, r["term_str"], r["size"], None))
            break
        name, inp, env, got, label = ce
        if verbose:
            print(f"  round {rnd}: recipe {r['term_str']!r} (size {r['size']}) "
                  f"-> counterexample {name}: recipe says {got}, ORACLE says {label}")
        result.discriminated.append(r["term_str"])
        rows.append((name, inp))
        result.rounds.append(CegisRound(rnd, r["term_str"], r["size"], name))

    # FINAL synthesis on the grown spec — the converged recipe.
    spec_final = _spec(rows)
    r_final = synthesize(substrate, spec_final, ops=ops, max_size=max_size,
                         timeout_s=timeout_s)
    result.final_term = r_final.get("term")
    result.final_term_str = r_final.get("term_str")
    result.final_size = r_final.get("size")
    result.fits = bool(r_final.get("fits"))
    result.rows = rows
    return result


# ===========================================================================
# PART 2 — THE DESCRIPTOR-GROUNDING HELPER (the simplicial-complex instance).
#
# The descriptors are GROUNDED from held primitives, not hand-listed:
#   cell_count(complex, k) = cardinality(simplices_of_dim(complex, k))
# grounded via the SAME compute_grounding.ground_computation the oracle uses, for
# k = 0..maxdim. {V,E,F} = k=0,1,2; the missing 3-cell count falls out of the same
# family the moment the world reaches dimension 3.
# ===========================================================================

# A simplicial complex is given as a list of MAXIMAL faces (each a list of vertex
# ids). The closure (all sub-faces) is the shared structure the oracle and the
# descriptors both read.

def closure(maximal_faces: Sequence[Sequence[int]]) -> set:
    """ALL non-empty faces of all maximal faces (the simplicial closure)."""
    faces = set()
    for mf in maximal_faces:
        mf = tuple(sorted(mf))
        for r in range(1, len(mf) + 1):
            for c in itertools.combinations(mf, r):
                faces.add(c)
    return faces


def maxdim(maximal_faces: Sequence[Sequence[int]]) -> int:
    return max((len(mf) - 1 for mf in maximal_faces), default=0)


_CELL_COUNT_DEF = (
    "cell_count(complex, k) = cardinality(simplices_of_dim(complex, k))")

_EULER_DEF = (
    "euler(complex, N) = "
    "sum{ k in 0..N : neg_one_pow(k) * cardinality(simplices_of_dim(complex, k)) }")


def ground_cell_count(substrate, *, verbose: bool = False) -> Callable[[Sequence, int], int]:
    """Ground the agent's OWN cell_count(complex, k) descriptor from its held
    primitives (cardinality ∘ simplices_of_dim) and return a callable
    cell_count(maximal_faces, k) -> int. ONE grounding serves every k (k is an
    argument), so this invents the WHOLE family c0..c_maxdim, incl. the c3 the
    {V,E,F} set was missing."""
    caps = dict(_reason.CAPABILITIES)
    res = _cg.ground_computation(substrate, "cell_count", _CELL_COUNT_DEF,
                                 capabilities=caps)
    if not (res.get("grounded") and res.get("installed")):
        raise RuntimeError("agent's own cell_count descriptor failed to ground: "
                           f"{res.get('reason')}")
    fn = caps["cell_count"]
    if verbose:
        print(f"  grounded descriptor family cell_count(·,k) from held primitives: "
              f"{sorted(res.get('parts', []))}")

    def cell_count(maximal_faces: Sequence[Sequence[int]], k: int) -> int:
        faces = [list(f) for f in closure(maximal_faces)]
        return int(fn({"complex": faces, "k": k}))

    return cell_count


def ground_euler_oracle(substrate, *, verbose: bool = False) -> Callable[[Sequence], int]:
    """Ground the agent's OWN slow χ (alternating sum over the full closure, binned
    by dimension) from held primitives. The ORACLE — computationally distinct from
    the V−E+F… recipe (different algorithm + data structure)."""
    caps = dict(_reason.CAPABILITIES)
    res = _cg.ground_computation(substrate, "euler", _EULER_DEF, capabilities=caps)
    if not (res.get("grounded") and res.get("installed")):
        raise RuntimeError("agent's own euler recipe failed to ground: "
                           f"{res.get('reason')}")
    fn = caps["euler"]
    if verbose:
        print(f"  grounded χ oracle from held primitives: {sorted(res.get('parts', []))}")

    def euler(maximal_faces: Sequence[Sequence[int]]) -> int:
        faces = [list(f) for f in closure(maximal_faces)]
        N = max((len(f) for f in faces), default=1)
        return int(fn({"complex": faces, "N": N}))

    return euler


def ground_cell_count_descriptors(
    substrate, complexes: Sequence[Sequence[Sequence[int]]], *, verbose: bool = False,
) -> Tuple[Describe, List[str]]:
    """Build a grounded `describe` over the cell_count family for a world of
    complexes. The family runs k = 0..maxdim (maxdim MEASURED across `complexes`,
    not hand-counted), and INFORMATION-FREE descriptors (constant over the whole
    world) are pruned mechanically. Returns (describe, descriptor_names).

    describe does NOT expose `euler` — the recipe must be REBUILT from the cell
    counts (else it would read the answer the oracle computes)."""
    cell_count = ground_cell_count(substrate, verbose=verbose)
    n_desc = max(maxdim(mf) for mf in complexes) + 1
    # Prune information-free descriptors: a count constant across the world carries
    # zero discriminative information, so it is not a useful Var leaf. A mechanical
    # information test, not a hand-pick of k's.
    cols = {k: [cell_count(mf, k) for mf in complexes] for k in range(n_desc)}
    ks = [k for k in range(n_desc) if len(set(cols[k])) > 1]
    if verbose:
        dropped = [k for k in range(n_desc) if k not in ks]
        if dropped:
            print(f"  dropped information-free descriptors: {[f'c{k}' for k in dropped]}")
        print(f"  descriptor leaves: {[f'c{k}' for k in ks]} "
              f"(c0=V, c1=E, c2=F, c3=#3-cells, …)")

    names = [f"c{k}" for k in ks]

    def describe(maximal_faces: Sequence[Sequence[int]]) -> dict:
        return {f"c{k}": cell_count(maximal_faces, k) for k in ks}

    return describe, names


__all__ = [
    # Part 1 — the general CEGIS core
    "CegisResult", "CegisRound", "cegis_synthesize", "find_counterexample",
    "Describe", "Oracle", "Family",
    # Part 2 — the simplicial-complex descriptor/oracle instance
    "closure", "maxdim", "ground_cell_count", "ground_euler_oracle",
    "ground_cell_count_descriptors",
]
