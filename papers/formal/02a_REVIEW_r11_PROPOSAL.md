# Review of `02a_seldon_manifolds_psychological_grounding.tex` (draft-2026-09-02.1, r11) — proposal for fixes

Second pass. Scope: the whole file (742 lines, 12 pp), its log and aux,
the r9 review and what r10–r11 did with it, and 02 r26 / 01 r279 for the
results it cites. Line numbers are r11. Nothing applied.

Compile: 0 warnings, 0 overfull, 66 bibitems all cited, no `??`, all
`SM-`/`GE-` refs resolve, by-name check clean. r10–r11 did everything r9
asked: the five falsifiers including the paper's headline measured
prediction; "one of the places"; `rem:salience` reduced to its grounding
half with the theoretical half moved to 02 and cited by number;
`xr-hyper` to 02 and 01 at nine sites; the trap corollary and the soaring
section joined; the "rules out" overclaim corrected to 01's proposition;
D'Argembeau cited; the abstract aligned with `rem:clt`; the registered
report's journal appearance noted; "once measured and once derived"; the
overfull box; `\texorpdfstring`; the author lists completed; `enumerate`.
The psychology holds on re-reading. **This is the cleanest paper in the
set after two passes. What remains is one narration sentence, one scope
note in the old form, one author list with an ellipsis, and one reading
in `sec:limits` that could carry a falsifier.**

One of 02a's labels is cited by another paper via `SG-` (`sec:scope`, by
01 r279); 02 r27 will add `sec:body`. Both must survive.

---

## A. The preamble's "single pass" sentence

l.369–372: "The marks were assigned in a single pass under the rule just
stated, and are the least-audited judgement in this document — a reader
who thinks one is marked in the flattering direction is disagreeing with a
fast call, not an argued position." The same sentence being dropped from
01a, 01b, 01c and 02 this round. Keep 01's definition sentence (l.365–369,
verbatim); delete the rest; the list follows directly.

---

## B. Scope note in the old form

l.402–405: "… It sits outside the list because a misreading is a fact
about a reader rather than a result about the world." The set's scope
notes (08 r2, 09 r92, 10 r5, 01b r40) carry the first sentence only. Trim
to "This paper would be over-claiming if any section were read as
evidence that a nervous system holds a Seldon manifold, or as validation
of a construct that does not require it."

---

## C. One reading that could carry a falsifier

`sec:limits` l.347–353: "Forecasting error is on magnitude, not structure
— and this is a reframing … A manifold whose shape is right and whose
field magnitudes are miscalibrated is what this describes. That is a
legitimate reading and it is still a reading, offered as such." The
Moeck et al. daily-life result (people predict *which* events will make
them feel better or worse while erring on absolute levels) is exactly the
discriminating shape. Add `[detail]` **Affective forecasting errs on
magnitude, not on structure**: fails if, in daily-life measurement, people
misorder which events will make them feel better or worse as often as they
misjudge how much — which would make the manifold's shape wrong and not
only its field magnitudes. The reading stays a reading in the body; the
list is where it becomes a commitment.

---

## D. Smaller

1. `calderon2026` (l.425): "Sofia Calderon, Erik Mac Giolla, Karl Ask,
   \ldots, and Timothy J. Luke" — an ellipsis inside the author list. The
   CLIMR registered report has on the order of a hundred authors; the
   set's form for long lists is the first few authors and `et~al.` in the
   entry as well as the label (09 r92's Zhou entry). Use that.
2. l.191–192 "the registered report **has since** appeared in a
   peer-reviewed journal, while the bias-corrected re-analysis remains a
   preprint" — "has since" reads as drafting narration; "appeared in a
   peer-reviewed journal in 2026, while … remains a preprint" says the same
   as a fact about the literature.
3. `definition` and `proposition` environments are declared and unused
   (l.12–13). Harmless; remove or leave.
4. l.66 "The construct it grounds was built as engineering, to forecast"
   — fine.

---

## What is right and should not be touched

- `sec:scope`'s grounding-not-validation framing.
- `sec:motor` and `rem:motor-limits`: the forward model as a delay
  compensator, and the refusal to bridge to a deliberative horizon.
- `sec:region` with `rem:mip-cautions` (minimal ≠ minimum; offline
  backward pass ≠ receding horizon; the trap corollary), and
  `sec:satisficing` with `rem:thresholds`.
- `rem:clt`: the construal-level result declined after the registered
  replication, with the dispute reported as a dispute.
- `sec:horizon` (frame-relativity measured within one skull) and
  `sec:body`.
- `rem:sr`: the successor representation as closer to a manifold with
  fields than tree search is, with its caveat.
- `sec:expertise` and `rem:random-boards`.
- `sec:limits` entire.

---

## Suggested order

1. **A**, **B** — two deletions.
2. **C** — one falsifier.
3. **D**.
