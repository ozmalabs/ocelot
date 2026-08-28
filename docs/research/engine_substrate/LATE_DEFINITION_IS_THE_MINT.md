# Late definition is the mint, not the mistake — and it has a mechanical check

**2026-08-28.** Written after a review found `well-formedness` used from line 261 of paper 01 and
defined for the first time at line 806, in the conclusion, with paper 01 citing "the later papers"
for it and paper 01a citing "the companion paper" — a circular forward/back reference with the
definiens at neither end.

## Two things the finding conflated

**As process, the circularity is necessary.** A definition cannot precede the work it summarises. If
the term could have been defined up front it would already have been in the codebook, and would not
have needed inducing. The concept operates first, unnamed, doing work; the residual of that work
accumulates; and the definition is minted when the shape it has been holding becomes stateable. That
is the sd loop — recognise, accumulate residual, mint — running on the corpus rather than on ink or
audio. The 500 lines of use before the definition are *evidence the concept was new*, not evidence of
carelessness.

**As artefact, the reviewer is still right.** A reader is not retracing the discovery, and a paper is
written in the order of justification rather than the order of induction. So the definition belongs
early in the document even though it was reached late in the work. Both hold; neither excuses the
other.

## The predictable defect class

If concepts are minted from use, then *terms used heavily and defined late or never* is a
**predictable** defect class for work done this way. It should be checked deliberately rather than
waited for.

## The check, and what it found

Mechanical: count uses of each load-bearing term across the corpus, and count `\begin{definition}[…]`
titles containing it.

| term | uses | definitions | verdict |
|---|---|---|---|
| frame | 1036 | 3 | fixed today (`def:frame`) |
| dimension | 264 | 5 | fine |
| **grounding** | **122** | **0** | **worse than well-formedness — 122 uses, and the falsifiability structure is stated per grounding** |
| boundary | 118 | 1 | fine |
| collapse | 104 | 1 | fine |
| manifold | 95 | 2 | fine |
| quantum | 90 | 0 | two distinct senses (physics, sd-loop); check separately |
| residual | 87 | 1 | fine |
| instantiat* | 86 | 0 | covered by `def:represented-dimension`; ergonomic |
| runner | 78 | 0 | characterised by `prop:rule-runner`; borderline |
| horizon | 73 | 1 | fine |
| **aperture** | **56** | **0** | **fixed today (`def:aperture`)** |
| narrativium | 55 | 2 | fine |
| resolution | 53 | 1 | fine |
| well-formed | 28 | 1 | fixed today |
| grain | 23 | 0 | synonym of resolution; ergonomic |

**So well-formedness was not a one-off.** `aperture` had the identical defect at 56 uses, and
`grounding` a worse one at 122 — a term on which the entire contingent/compulsory distinction and the
per-grounding falsifiability structure rest, defined nowhere in eight papers.

Both now defined in paper 01: `def:aperture` in `sec:interface` (the three components as properties
of one edge — existence, grain, extent) and `def:grounding` before `sec:discrete-sufficiency`.

## Standing rule

Run the count before circulating a draft. A term above ~50 uses with no definition is a defect
regardless of how well understood it feels to the author — feeling well understood is exactly what
being minted from use produces, and is why the author is the last person who will notice.
