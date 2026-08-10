# NO MBPP TASK NEEDS AN IN-FRAME FLOAT — measured

**Date:** 2026-08-01. `scripts/arc5_float_necessity_audit.py`, rows in
`results/arc5_float_necessity.json`. Reads test-split reference `code` for
MEASUREMENT only (the arc-2 blocker-histogram allowance); nothing feeds a
codebook, cue table, or learning path.

## The claim under test

The substrate's frame invariant (CLAUDE.md, 2026-07-08): **in-frame is INTEGER;
non-integer structure is CROSS-FRAME**, living in the map (`Hom(frame, frame)`),
never as a datum inside a frame. The author's stronger claim: floating point is
thermodynamically indefensible and was a mistake to universalise — brains cannot
and do not do it.

Arc-2 Q1 nonetheless widened `ProgEval` to floats and paid **nine
divergence-ledger items** for it (banker's rounding, int/float `Eq`, dict
ordering, …). This measures whether that purchase was necessary.

## Result

| | n | % of float tasks |
|---|---|---|
| MBPP tasks whose asserts involve a float **at all** | **39 / 427** | (9.1% of corpus) |
| — rational parameters + a cross-frame map (π, √, ÷, ^) | 27 | 69.2% |
| — float appears only in the OUTPUT (the comparison) | 8 | 20.5% |
| — "irreducible float literal" | 4 | 10.3% |
| **Tasks requiring a genuine IN-FRAME float** | **0** | **0%** |

### The four "irreducible" cases are the finding

Tasks 139, 233, 276, 574 — the only non-rational float literals in the entire
corpus — all carry the **same literal: `3.1415`**.

```
139: perimeter      = 2*3.1415*r
233: lateralsurface = 2*3.1415*r*h
276: volume         = 3.1415*r*r*h
574: surfacearea    = ((2*3.1415*r*r) + (2*3.1415*r*h))
```

`3.1415` is a **hand-truncated π** (error 9.27e-05). It is not an irreducible
in-frame quantity; it is a *cross-frame constant written badly*. Correctly
represented, it belongs in the map — which is exactly where these tasks put it
when we solved them: three of these four are members of the `k·π·r^a·h^b`
family solved with **rational `k` and integer exponents**
(`PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md`).

### Every float literal in the corpus is a small rational

The complete inventory of float literals across all 427 reference solutions:

| literal | count | as a rational |
|---|---|---|
| `255.0` | 3 | 255 |
| `2.0` | 1 | 2 |
| `1.0` | 1 | 1 |
| `0.5` | 1 | 1/2 |

Not one irrational value. The cross-frame maps actually invoked are
`pi` (8), `sqrt` (3), `round` (3), `tan` (1), `pow` (1) — all legitimately maps.

## What this means

1. **The invariant was right and the arc worked against it.** Nine divergence
   items were paid for a capability that **zero tasks require**. The correct
   in-frame representation is integer/rational; π, √ and friends belong in
   `Hom(frame, frame)`, applied — never stored as a datum.
2. **The tasks we filed as "needs float support" needed rationals.** The
   float-heaviest family in the corpus (sphere/cylinder/cone/circle) is solved
   by `(k, a, b)` with `k` rational and `a, b` small integers — measured at
   277 candidates total, versus **unreachable at any size** in the float-literal
   syntax representation.
3. **91% of the corpus never touches a float at all.** The numeric domain this
   engine actually needs is integers, small rationals, and a handful of named
   cross-frame constants.
4. It is consistent with the thermodynamic argument rather than a test of it:
   the precision floats carry (≈15–16 significant digits) is absent from every
   input and unused in every output here — the identifiability guard the
   invariant already states ("never encode precision the steps cannot support").

## Honest limits

- **This is MBPP.** It is a basic-programming corpus; a numerics or signal-
  processing corpus would very likely contain genuine in-frame reals, and this
  result must not be quoted as "no program needs floats." It says: *no task in
  this benchmark does*, and the one place the corpus looks like it needs one, it
  is a mis-written constant.
- The classifier is syntactic (AST literals + names + ops). A float arising
  from a computation whose *structure* is rational is classed
  `float_only_in_output`; that is the intended reading, but it is a
  classification choice, stated here rather than buried.
- Reference solutions are one implementation among many; a different solution to
  the same task could introduce a float. The claim is about the tasks' numeric
  requirements as the corpus itself exhibits them.
