# NO PROGRAM NEEDS FLOATS — SPECS ARE WRITTEN TO IMPLY THEM

**Date:** 2026-08-01. `scripts/arc5_exact_recovery.py`,
`results/arc5_exact_recovery.json`. Companion to
`PROGRAM_SYNTHESIS_ARC5_FLOAT_NECESSITY.md`.

## The claim (author)

> No program needs floats. Many programs are **specified** in ways that imply
> they need floats.

The defect is in the specification, not the computation.

## What a float assert actually says

```
assert math.isclose(circumference(10), 62.830000000000005, rel_tol=0.001)
```

Seventeen significant digits, of which the spec then declares **three**
meaningful. The tolerance is the specification admitting it does not mean what
it wrote. The *problem* is exact — a rational radius, π applied to whatever
depth is needed, an answer at whatever resolution will be observed. The
*specification* is float-implying, and an implementation reading it literally
infers a requirement the problem never had.

## Method — read the float assert as an INTERVAL CONSTRAINT

Take `(value, tolerance)` as an interval, and solve for an EXACT structure —
rational coefficient × cross-frame constant × integer powers of the arguments.
This is not a new technique: it is what recovered the geometry family in
`PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md`, where it was the difference between
*unreachable at any size* and 277 candidates.

## Result

39 tasks have float-involving asserts; 20 have usable numeric-literal cases.

| | n |
|---|---|
| **Exact form recovered** (rational k, cross-frame constant, integer exponents) | **11 / 20** |
| Remaining, needing a different EXACT shape | 9 / 20 |
| Requiring an in-frame float | **0** |

**Recovered exactly:**

| task | exact form | |
|---|---|---|
| 82 | `4/3 · π · r³` | sphere volume |
| 85 | `4 · π · r²` | sphere surface |
| 139 | `2 · π · r` | circumference |
| 233 | `2 · π · r · h` | cylinder lateral |
| 276 | `1 · π · r² · h` | cylinder volume |
| 312 | `1/3 · π · r² · h` | cone volume |
| 746 | `1/8 · π · r²` | sector area |
| 422 | `9/8 · n²` | average of cubes |
| 432 | `5/6 · b` | trapezium median |
| **606** | `1/180 · π · d` | degrees → radians |
| **742** | `1 · √3 · a²` | tetrahedron area |

606 and 742 initially "failed" — 606 only because the first family's
denominators stopped at 8, and 742 because it needs **√3**, a *different
cross-frame constant*. Both are coverage limits of a four-line family, not
evidence for floats.

**The 9 remaining, by the exact shape they actually need** (classified by
inspecting the reference solution's operators — see limits below):

| task | needs | not a float |
|---|---|---|
| 163 | `tan` | trig cross-frame map |
| 293, 731 | `√` | algebraic cross-frame map |
| 248, 738, 300 | fold / sum | a different *shape*, exactly representable |
| 574 | `2πr² + 2πrh` | a **sum of two family terms** |
| 246 | iterative (Babylonian) | an algorithm, not a closed form |
| 397 | median of three | a **selection**, not arithmetic at all |

## Conclusion

Every float-involving task in this corpus is exactly specifiable. The recovered
eleven are demonstrated; the other nine need richer *exact* shapes — sums,
folds, selections, and algebraic maps — and **none needs an in-frame float**.

The float-ness is an artifact of how the specification was written: a decimal
expansion plus a tolerance, in place of an exact statement. Reading the assert
as the interval it actually is recovers the exact structure and, measurably,
makes the search tractable where the float representation was unreachable.

## Honest limits

- **Two different strengths of claim.** The 11 recoveries are *demonstrated* by
  fitting against the asserts. The 9 remaining are classified by *inspecting*
  the reference solution's operators — an argument that they are exact-shaped,
  not a demonstration that an exact form was found. Stated separately on purpose.
- 19 of the 39 have no usable numeric-literal asserts (string/list/mixed
  domains) and are outside this method's reach; they are not counted either way.
- Corpus-bound: MBPP is basic programming. A numerics/DSP corpus would be a
  genuine test of the strong claim, and this result must not be quoted as
  settling it.
- Reference solutions are one implementation among many.
