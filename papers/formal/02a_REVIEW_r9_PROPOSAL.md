# Review of `02a_seldon_manifolds_psychological_grounding.tex` (draft-2026-09-02.1, r9) — proposal for fixes

Scope: the whole file (711 lines, 11 pp), its log, 02 (r25 in progress) and
01 (r278) for what it attributes to them. Line numbers are r9. Nothing
applied.

Compile: 0 undefined, 0 font warnings, one 1.15pt overfull in a bibitem.
All 63 citations resolve. The psychology was spot-checked and holds: Miall
2007 (138/134 ms), Blakemore/Kilteni attenuation, Scholz–Schöner UCM,
Todorov–Jordan minimal intervention (and the caution that it permits
magnification is correct), Simon 1956 conjunctive aspiration, Warren 1984
and Warren–Whang 1987 body-scaled boundaries, Hasson temporal receptive
windows, Snider 2015 depth ≈ 3, Huys 2012/2015, Momennejad 2017, Gobet–Simon
six boards, the far-transfer meta-analyses, the hippocampal-amnesia dispute.
This is the best-evidenced paper in the set and the honest-limits section is
a model. The findings are cross-reference hygiene, one misplaced theoretical
remark, and falsifiers that omit the paper's own measured prediction.

---

## A. The paper's one measured prediction is not in the falsifier list

`sec:horizon` l.217–223: "This section is the one place in this programme
where the frame-relativity is *measured* rather than inherited … the axiom
predicts that a system built of many frames should exhibit many horizons
rather than one, and that is a claim about brains which could have come out
otherwise. It does not." That is the paper's headline empirical result and
01 r278 points at this paper as the place Axiom −1 carries risk
(`rem:not-observer-talk`). There is no falsifier for it.

**Fix.** Add `[shape]` **Horizon is plural within one agent.** Fails if
integration windows and predictive horizons across cortical regions
collapse to one value, or if a single horizon suffices to model
within-agent prediction across timescales (Hasson; Brunec–Momennejad).

Also missing, each stated in the body as a prediction or a component:
- `[detail]` **Salience tracks fit, not magnitude** (`rem:salience` l.185–198
  says what an experiment would have to settle — allocation *by* fit rather
  than correlation with it; state that as the test).
- `[detail]` **Search is shallow and stops reflexively** (`sec:search`):
  fails if fitted planning depth is not bounded at a few steps or pruning
  is cost-sensitive where it is made counterproductive.
- `[detail]` **Blind spots are not introspectively auditable**
  (`sec:other`): fails if a frame can be shown to enumerate its own missing
  dimensions from inside.
- `[detail]` **The dimension set grows** (`sec:other`): fails if perceptual
  learning never separates previously fused dimensions.

And l.217 "the one place in this programme where the frame-relativity is
measured" overclaims now: 01 r278's `rem:empirical-instance` reports a
measurement (time as an inferred dimension) and this paper's own
`sec:body` is measured. → "one of the places".

---

## B. `rem:salience` theorises in a grounding paper, and duplicates `sec:body`

l.170–199. The remark's first two-thirds (l.171–192) is a theoretical claim
— "*An aperture is a shape, not a size*"; salience is allocated by fit;
things past the horizon "are never presented to the aperture at all" —
introduced here for the first time in the set. The scope section says this
paper "asks only whether one particular substrate implements anything of
that shape"; this remark instead extends the shape. And the one measurement
it rests on (Warren–Whang, the doorway ratio) is the same measurement
`sec:body` l.238 presents 60 lines later as the paper's strongest support,
so the doorway is cited twice for two different points.

**Fix.** Keep in 02a only the grounding half: the doorway measurement and
the honest limit (l.194–198, "Nothing here shows that salience is
*allocated by* fit rather than merely correlating with it"). Move the
theoretical half (l.171–192) to 02, as a remark following `rem:aperture`
("An aperture is a shape") — that is where "aperture is not one dial"
already lives, and 02 r25 is where the claim belongs. Deferred to the 02
side; 02a then cites it with an `SM-` ref. Place what remains of
`rem:salience` *after* `sec:body`, so the doorway is introduced once.

---

## C. Cross-references and naming

1. **"The theory paper" ×7, "Graphic Equalisation" ×1, "the substrate paper"
   ×1**, none declared beyond the box's "*Seldon Manifolds — Theory*". Add
   the naming sentence the other groundings now carry (Graphic
   Equalisation; the Seldon paper — 01's table calls it *Seldon*; use
   that), with the "inherits their definitions…" clause.
2. **`xr-hyper`.** `\externaldocument[SM-]{02_seldon_manifolds_theory_referenced}`
   and `[GE-]{01_…}`. Targets, all present in the current aux:
   l.102 acceptable region → `SM-def:acceptable`, `SM-prop:min-intervention`;
   l.162 resolution/horizon → `SM-def:resolution`, `SM-hyp:adaptive-resolution`;
   l.218 founding axiom → `GE-ax:no-view`; l.230 frame-relativity →
   `SM-rem:aperture`; l.312 blind spot as distinct deficit →
   `SM-rem:two-deficits`, `SM-def:blind-spot`; l.322 dimension set →
   `SM-def:dimension`; l.337 optional machinery →
   `SM-rem:optional-machinery`; l.348 per-agent axes → `SM-rem:aperture`.
   `sec:region`'s "correction only on departure" can also point at 02's new
   `SM-cor:trap-antecedent` for the case where the region alone is not
   enough — the trap is exactly what `rem:mip-cautions` is circling.
3. **Soaring.** 02 r25 promotes the glider case to `sec:onedim` and calls it
   "the closest operational instance of this whole assembly". 02a's
   `sec:expertise` (within-frame forecasting, anticipation from advance
   kinematics) is the psychological side of the same instance. One sentence
   and an `SM-sec:onedim` ref would join them.

---

## D. Falsifiability section hygiene

1. **"On the tags" paragraph (l.356–364)** is the pre-harmonisation text
   ("The substrate paper has carried these marks for some time…"). Replace
   with 01's sentence verbatim and cut the history.
2. **Scope note l.382** "counting it as a commitment inflated the list by
   one" — narrated drafting. Cut the clause.
3. The list uses `itemize`; every other paper uses `enumerate`. Harmonise.

---

## E. Claims that overreach or lack a citation

1. l.311–313 "and **rules out** any mechanism in which a frame audits its own
   dimension set from inside." Three findings of failure (Rozenblit–Keil,
   Simons–Chabris, Keysar) show that people *do not*, not that a frame
   *cannot*. The impossibility is 01's `prop:runner-opaque`; cite it and
   say the psychology is consistent with it and offers no counterexample.
2. l.350–351 "imagery vividness and richness of future simulation covary
   rather than dissociating" — the only uncited empirical claim in the
   paper. Cite (D'Argembeau & Van der Linden 2006, *Consciousness and
   Cognition* 15(2):342–350, is the standard source) or drop.
3. Abstract l.53–55 "does not survive its best-powered test" vs `rem:clt`
   l.210–212 "in serious dispute rather than … refuted". Align the abstract
   to the body: "did not survive its best-powered test and is in dispute".
4. `rem:clt` l.210–211 "both critical papers are preprints" — check whether
   the CLIMR registered report (Calderon et al.) and Maier et al. have since
   appeared in journals; if either has, update the bibitem and the
   sentence.
5. l.103–104 "the implementation is measured twice over" — the second
   (`todorov2002`) is derived, not measured, as the next paragraph itself
   says. → "once measured and once derived".

---

## F. Mechanical

- Overfull 1.15pt at the `blakemore1999` bibitem: a `\sloppypar` around the
  bibliography or a line break in the title.
- `\texorpdfstring` on the `\date` dashes.
- Two bibitems carry "et al." *inside* the author list (`mellers2014`,
  `muller2010`) — complete the lists.
- `et al.` → `et~al.` in labels, as elsewhere.
- `definition`/`proposition` environments declared and unused; harmless.

---

## What is right and should not be touched

- `sec:scope`'s framing (grounding, not validation; unflattering findings
  are measurements of an implementation) and `sec:limits` entire — the
  four "what the evidence does not support" paragraphs, including the
  amnesia dispute presented as unresolved and the affective-forecasting
  reframing offered as a reading.
- `rem:mip-cautions` (minimal ≠ minimum; offline backward pass ≠
  receding horizon) and `rem:thresholds` (reference point, safety-first and
  scalar aspiration are not regions; risk homeostasis failed by collapsing
  a field to a scalar).
- `rem:clt`: refusing to lean on construal level theory after the
  registered replication, and saying why the timing result is used instead.
- `rem:random-boards`: correcting a control the paper could have leaned on.

---

## Suggested order

1. **A** — five falsifiers, one overclaim fixed.
2. **C** — naming and `xr-hyper` (mechanical; also makes B's move citable).
3. **B** — split `rem:salience`; 02a side now, 02 side deferred.
4. **D**, **E**, **F**.
