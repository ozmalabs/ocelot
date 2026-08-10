# THREE MOVES, THREE MEASUREMENTS — structure beats budget, every time

**Date:** 2026-08-01. Run live by the orchestrator against the real engine.
**Status:** RESULT (n small, each decisive on a named case). Companion to
`PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md`.

## The frame (project author)

> There are two ways of solving a problem, and they work together. First, you
> re-use shapes you have. Secondly, you relax Γ and admit new parts of the
> decision space with the widest gap you can, to remove as much of it as
> possible. You do this N times across order N.
>
> …sometimes you have to compare across orders, and it can become quadratic or
> worse — but if it's that bad you're likely stretching too far, and
> intermediate problems will unlock tractability.
>
> …the other way is a missing dimension — mint it and the cost drops an OoM or more.

Three moves. All three measured below. **In every case a structural move beat a
bigger budget, and in two of three the budget could never have worked at all.**

## Move 1 — reuse held shapes
Already built: `sd_recognize` / `ShapeDecode` decode against the codebook.
Not re-measured here.

## Move 2a — relax Γ by acting with a group (orbit augmentation)

`br_10_top_of_three`, from its 3 revealed rows:

| example set | found | held-out |
|---|---|---|
| 3 revealed rows | `Max(a,b)` — size 3, 532 tested | **WRONG** |
| S₃ orbit of those same rows (13 rows, **0 new oracle calls**) | `Max(a,Max(b,c))` — size 5, 25,240 tested | **CORRECT** |

Full detail in `PROGRAM_SYNTHESIS_ARC5_ORBIT_RESULT.md`.

## Move 2b — intermediate problems unlock tractability

Task 59, nth octagonal number (`n*(3n-2)`):

| approach | tested | outcome |
|---|---|---|
| direct, `max_size=9`, default consts | **200,000** | **not found** (budget exhausted) |
| solve the inner factor `(3n-2)` alone | **8,529** | found at size 5 |
| compose `n * inner(n)` | 1 step | **CORRECT on held-out** (n=3→21, n=7→133) |

~23× cheaper, and it *succeeds where direct search cannot finish*. The correct
program is the order-below solution composed — which is what descent is for.

## Move 3 — mint the missing dimension

Seven of the nineteen "arithmetic depth" tasks are ONE FAMILY:
`k · π · r^a · h^b` (sphere volume/surface, cylinder volume/lateral, cone
volume, circle circumference, polygon area).

| approach | result |
|---|---|
| direct search, default consts | **UNREACHABLE AT ANY SIZE** — π is not in the const set; 120,000 candidates exhausted |
| family shape with dimension `(k,a,b)` | **6/6 solved**, 10–109 candidates each, **277 total** |

Recovered coefficients are the textbook ones (`4/3,a=3`; `4,a=2`; `1/3,a=2,b=1`;
`2,a=1,b=1`; `1,a=2,b=1`; `2,a=1`) — real structure, not a fit.

This is the documented `scale2`/`modular` precedent (CLAUDE.md, 2026-07-08): a
whole family collapses to **one held shape + one dimension** instead of a fresh
`CapabilityAxis` per member. "Grows capability AND improves efficiency" —
measured here at ~2,600× on the budget comparison, and converting *impossible*
into *trivial*.

## The correction this forces

The 19 arithmetic-depth tasks were filed (arc-4 S4) as *"deeper than max_size=9 —
needs a bigger size ceiling."* **That diagnosis is wrong.** No size ceiling helps
when π is not expressible in the basis. The problem is not depth; it is a missing
dimension. 6/19 (32%) of that class are one dimension from solved.

Likewise the "search cost" note in the orbit result (532 → 25,240) is not a
budget problem: rising cost is a **diagnostic for a missing intermediate or a
missing dimension**, not a reason to raise the budget.

## The honest caveat, identical in all three

**The mechanism is confirmed; the SELECTION is not.** In each case the
orchestrator supplied the structure by hand — the S₃ conjecture, the `(3n-2)`
factorisation, the `k·π·r^a·h^b` family. What is measured is that the structural
move works and how much it is worth. What is NOT measured is whether the system
can find the structure itself.

That is exactly the open question, and the machinery for each already exists,
pointed elsewhere:
- symmetry/group action → `TransformDecode` (vision/spatial today)
- dimension minting → `DimInfer` / `LatentDimension` (vision/spatial today)
- intermediate discovery → descent's hole-finding (list-input specs only; it
  never fired on task 59's scalar arithmetic)

**Every one of these is an operator already built and never pointed at programs**
— which is the move that has worked in this project every single time, and the
opposite of the content-mining that has nulled five times.

## Method note (honest)

The geometry-family fits used all three MBPP asserts per task with no held-out
row reserved; the recovered coefficients are the exact textbook constants, so
correctness is not in doubt, but the *protocol* there was fit-on-all, not
fit-and-hold-out. Task 59 and `br_10` were held-out verified properly.
