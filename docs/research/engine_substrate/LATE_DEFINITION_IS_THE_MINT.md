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

## The forcing mechanism is compression, and it is measurable

The author's account of how `well-formedness` arrived: it was *vibes-based* — an unquantified
recognition that could be applied consistently but not stated — and enough revisions made it
quantifiable. *"It needed to exist and forced itself into existence by compression."*

That is a mechanism claim, not a metaphor, and it predicts something checkable. If the concept was
forced by compression, the corpus should contain **repeated partial restatements** of the same
reasoning at the sites that needed it, in the period before the definition existed.

Measured across the eight papers, searching for the *reasoning* rather than the term:

```
  01:108  ... does no work.
  01:134  ... does no work in it.
 01a:249  nothing held that does no work, the same well-formedness the
          companion paper's cost result turns on.
  01:297  holds no structure doing no work for it: each retained distinction
          earns the cost of its retention ...          <- the definition, 2026-08-28
  01:299  rarely need to write against the standing structure, so cost
          approaches zero.
```

Eight occurrences of the reasoning family, across four distinct sites, before the definition existed.

**And the important detail is that every one of them is partial.** No site restates the whole shape;
each states the face it needs — *does no work* here, *nothing held that does no work* there, *rarely
needs to write* somewhere else. That is the signature, and it is sharper than "repeated
restatement": you cannot restate the whole thing each time, because you do not have the whole thing
yet. You pay for the fragment the local argument requires. The definition arrives when the fragments
are noticed to be one shape.

Which is exactly the sd loop's decode step at corpus grain: partial coverage against a codebook, the
residual being the unmatched span, and a mint when the residual will not fit any held entry.

### A prediction that needed correcting

I predicted that a compression-forced definition should be *shorter* than the restatements it
replaces. Measured, that is wrong: the definition is 84 words and the fragments total roughly the
same. The gain is not length.

The corrected version: **a compression-forced definition is *complete* where the fragments were
partial, at comparable cost.** What compression buys is the whole shape for the price of the pieces,
not fewer words. An imposed definition, by contrast, adds length without replacing anything, because
there were no fragments for it to consolidate.

### Two tests for whether a minted concept is real

1. **Fragment test.** Before the definition, the corpus should hold several partial statements of the
   reasoning at sites that independently needed it. If the definition arrives with no fragments
   behind it, it was imposed rather than minted.
2. **Removal test.** *"It needed to exist"* is checkable: delete the concept and count what breaks. A
   minted concept takes several arguments with it, because they were leaning on it before it had a
   name. An imposed one takes nothing.

`well-formedness` passes both: eight fragments across four sites, and removing it costs the cost
result in 01, the synchrony-convention argument in 01a, and the carvings section's entire mechanism.

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

**So well-formedness was not a one-off.** Note also that usage count is a *proxy* for the real
signal and not the signal itself: the thing to look for is scattered partial restatement of one
shape, which is what the fragment test above detects. A term used 122 times with one clear statement
is fine; a term used twenty times whose justification is rewritten in pieces at each site is overdue. `aperture` had the identical defect at 56 uses, and
`grounding` a worse one at 122 — a term on which the entire contingent/compulsory distinction and the
per-grounding falsifiability structure rest, defined nowhere in eight papers.

Both now defined in paper 01: `def:aperture` in `sec:interface` (the three components as properties
of one edge — existence, grain, extent) and `def:grounding` before `sec:discrete-sufficiency`.

## Standing rule

Run the count before circulating a draft. A term above ~50 uses with no definition is a defect
regardless of how well understood it feels to the author — feeling well understood is exactly what
being minted from use produces, and is why the author is the last person who will notice.
