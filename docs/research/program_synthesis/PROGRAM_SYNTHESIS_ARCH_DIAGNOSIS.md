# THE REPRESENTATION IS WRONG — a diagnosis, from the author, confirmed by our own numbers

**Date:** 2026-08-01. Written after arcs 1–4 and the arc-5 probes.

## The claim

> The fundamental design of it is to provide cognition — which is integer based,
> and doesn't need the other options. Which means (a) Term Trees etc are trying
> to shove linear-ish computer logic into a cognitive engine, and (b) the
> representations of the problems are not correctly abstracted.

## Why our own measurements support it

**Every large win came from leaving the syntax representation. Every wall came
from staying in it.**

| move | syntax representation | shape representation |
|---|---|---|
| geometry family (6 MBPP tasks) | **unreachable at any size** — π is not in the const set; 120,000 candidates exhausted | one shape `k·π·r^a·h^b` + a 3-integer parameter vector: **10–109 candidates each, 277 total** |
| `top_of_three` | `Max(a,b)` from 3 rows — **wrong** | extremum shape under S₃: **correct**, zero new data |
| nth octagonal | direct search **fails**, 200,000 tested | inner factor + one composition: **8,529**, correct |

And the walls are all syntax-space artifacts: `max_size` ceilings, budget
exhaustion, the nine float divergences in the P1 ledger (banker's rounding,
int/float `Eq`, dict ordering), and traps — which are *curve-fitting in syntax
space*, the natural failure mode of "find a tree reproducing these outputs."

**The π case is the sharpest, because the substrate's own rule predicted it.**
CLAUDE.md's frame/continuum invariant states: in-frame is INTEGER; non-integer
structure is CROSS-FRAME, living in the map, never as a datum inside a frame.
Putting π in the constant pool of a term search is a category error *by the
architecture's own law*, and it failed exactly as the law says it must. The
correct form is a family (shape) with a cross-frame map applied — which is what
made it 2,600× cheaper and, more importantly, *possible*.

## What we actually built

A miniature von Neumann evaluation model — AST nodes, size-ordered enumeration,
an interpreter, fit-the-outputs — expressed **in** the substrate rather than
**as** the substrate. The graph hosted it faithfully. It is not cognition; it is
a compiler stack encoded as graph data.

## The missing level

We have **IR → source**, rendered to five languages, and it works.
We are missing **shape → IR**.

The layer exists and was built for exactly this: `ShapeSignature`, `ShapeDecode`,
`sd_mint_quantum`, `DimInfer`, `LatentDimension`. We built a syntax searcher
*beside* it instead of on top of it. The Omniglot arc already proved the correct
pattern in another domain — propose by quantised index, **render**, compare
(AbS). Generation, not search.

Correct object for each measured case, all in-frame and integer:
- `volume_sphere` → family shape, parameters `(k, a, b) = (4/3, 3, 0)`
- `top_of_three` → extremum shape, dimension `arity = 3`
- `octagonal(n)` → polygonal family, dimension `sides = 8`

The program is then a **rendering** of `(shape, parameters)`, not a thing to be
searched for.

## What this says about the five nulls

The proposal layer never worked, and four arcs tried to fix it with better
content (chunks, an NL-paired diet, whole-program retrieval, a cost instrument).
All null. **The defect was never the contents of the space; it was the space.**
You cannot fix a wrong representation by putting better material into it. That
is the same finding the operator-vs-content dissociation reports, stated one
level down.

## What to KEEP (this is a localised defect, not a rewrite)

- **The verdict layer is correct as built.** Verification by execution is a
  cross-frame comparison, which the invariant *requires*. It has never
  miscarried; do not touch it.
- **The hub IR as a five-language pivot is real** and shape-agnostic.
- **`ProgEval` is legitimate** — it is the rendering you compare against.
- **The structural detectors are correct** and are, in this reading, partial
  intent checks operating one level too low.

The defect is localised to **proposal**, which is precisely the half that has
failed every measurement.

## The honest open question

Shape-first generation is proven on three hand-supplied structures and one
criterion-discovered one (`br_10`, via widest gap, no lexicon). What is NOT
established is whether shapes at the right grain can be **acquired** for this
domain — the arc-5 probe measured recognition coverage at 0 genuine algorithmic
hits, because the held vocabulary is systems-flavoured. That is the next
measurement, and it must carry the fourth-null rule: a shape codebook is still
content, and content has nulled five times *when used as a proposer*. The
difference claimed here is that a shape is not a proposal — it is a
representation the program is rendered FROM. That difference is testable and
must be tested, not assumed.
