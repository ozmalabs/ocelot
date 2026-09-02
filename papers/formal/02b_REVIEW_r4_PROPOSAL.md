# Review of `02b_seldon_manifolds_social_and_psychological_application.tex` (draft-2026-09-02.1, r4) — proposal for fixes

Second pass. Scope: the whole file (364 lines, 5 pp), its log and aux,
the r3 review and what r4 did with it, and 02 r26 / 01 r279 / 09 r92 for
what it attributes. Line numbers are r4. Nothing applied.

Compile: 0 warnings, 0 overfull, 6 bibitems all cited and sorted, no `??`,
`SM-`/`GE-` refs resolve, by-name check clean, no implementation
identifiers. r4 did everything r3 asked: the evidence-standard paragraph
with "reproducible from the record or withdrawn"; `sec:record` names the
three lines and gives no count; the five numbers given their meaning
(the 53/8 tally, the anchors, 0.245 vs 0.256, the inversion arms, the
degenerate intervals); the tags sentence; item 8 to a scope note; item 3
re-marked; item 5 flagged untested; the naming sentence; the title; the
bibliography sorted. **What remains is one misattribution and one scope
note in the old form.**

No other paper cites 02b's labels.

---

## A. The "transform the composition treats as free" is the adaptability paper's, not Graphic Equalisation's

`rem:negative` l.241–243: "uniform inversion folds to a rotation the
composition already treats as free — a transform in the basis the
composition holds, **in Graphic Equalisation's sense**". Falsifier 5
(l.311–313) repeats "a rotation the composition treats as free". A
transform in the held basis, applied before minting, is rung two of the
adaptability paper's ladder (`AD-sec:ladder`: recognise; transform in the
held basis; infer a dimension; mint). 01 has no such rung; its nearest
result is minting as grammar extension (`GE-cor:mint-is-grammar`), which
is rung four. **Fix:** `\externaldocument[AD-]{09_adaptability}`; l.242 →
"a transform in the basis the composition holds, the second rung of the
adaptability paper's ladder (its Section~\ref{AD-sec:ladder})"; falsifier
5 gets the same reference once. Add "the adaptability paper" to the box's
naming sentence.

---

## B. Scope note in the old form

l.324–327: "Reproduction is not evidence about organisms. No claim below
the level of the substrate is made anywhere above, and a reader who finds
one has found an error rather than a result — which is a fact about what
this paper says rather than a commitment that could be settled against
it." The set's form is the first two sentences. Drop the clause after the
dash.

---

## C. Smaller

1. `rem:ethics` l.133: "arousal moves $63 \rightarrow 347 \rightarrow 63$"
   — no unit. "in the substrate's arousal units" once, so the reader does
   not look for a scale.
2. l.34 "the applied companion to the Seldon grounding" — 01's table calls
   this paper "the applied paper"; the box is describing itself, so
   either is fine, but "applied paper" keeps one form across the set.
3. `\begin{thebibliography}{9}` fine for six entries.

---

## What is right and should not be touched

- The abstract and `sec:scope`: "nothing here is evidence about children
  or monkeys"; *reproduced* vs *available from the machinery without
  being put there*; the evidence-standard paragraph as adopted.
- The Harlow table with its two estimands separated and the degenerate
  intervals explained.
- `rem:dissolution` with its null controls and the pointer at 02's
  two-field construction; `rem:rational-impatience`; `rem:priority`.
- `sec:inversion` and `rem:negative` (with A applied): the negative
  diagnosed and converted into the commitment of item 5.
- `sec:discipline`'s last paragraph.
- `sec:record` as rewritten: provenance without counts.

---

## Suggested order

1. **A** — one external document, two refs, one name.
2. **B**, **C**.
