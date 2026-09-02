# Review of `02b_seldon_manifolds_social_and_psychological_application.tex` (draft-2026-09-02.1, r3) — proposal for fixes

Scope: the whole file (309 lines, 5 pp), its log, and the repo's own
result records for the four experiments it reports. Line numbers are r3.
Nothing applied.

Compile: 0 warnings, 0 overfull, all six citations resolve and are correct
(Harlow 1958, Seligman–Maier 1967, Yin 1969, Thompson 1980, Kidd et al.
2013, Watts et al. 2018). No implementation identifiers in the text. The
numbers were traced to the record: Harlow (`HARLOW_D1`/`D1B` results),
delay (`MARSHMALLOW_DELAY` results), helplessness (`ABUSIVE_R4`), face
inversion (`VISION_FACE_INVERSION`, pre-registered, 4/4 arms). The
interval arithmetic in the Harlow table checks (sd 0.039, n = 200 →
±0.0054; the binomial alternative → [0.741, 0.853], "about ten times
wider" is right). The paper is short, careful, and its negative result is
its best section. The findings are about evidence standing, one
misdescribed population, and a few unexplained numbers.

---

## A. "Reproducible or withdrawn" is a promise the reader cannot act on

l.69–73: "Each records the commit it ran against and the seed it ran with,
so a claim below is either reproducible or withdrawn. And each carries a
*source audit* … reported with the run and reproduced in the results
tables." l.215–217: "a claim … is not one a reader should take on trust."

The record these point at is the programme's implementation record, which
is not circulated with the papers. So the commits, seeds and audits are
reproducible *by the programme* and not by a reader — exactly the situation
01 r278's `sec:scope` now names in one sentence ("a pre-registered
implementation record which is likewise not circulated with these papers,
and it is a claim a reader may decline to credit on exactly the same
terms"). 02b makes the same kind of claim four times and never says it.

**Fix.** Adopt 01's sentence in `sec:scope` (adapted: this paper is
*entirely* such a record), and rephrase "reproducible or withdrawn" to
"reproducible from the record or withdrawn". Keep the source-audit
discipline paragraph — it is the right thing to enforce — but say the
audits are reported in the record, not "in the results tables" (the paper
has no audit table).

---

## B. `sec:record` describes the wrong population

l.231–234: the four experiments "are drawn from a larger body of
pre-registered runs in the same substrate — at the time of writing, one
hundred and five pre-registrations and seventy-one result documents,
covering social conduct, institutional decision, bond formation and the
dynamics of coercive relationships."

Those counts (105 / 71) are exactly the *social-simulation line's* counts.
But only one of the four experiments (learned helplessness) comes from
that line; contact comfort and delay come from the affect line, and face
inversion from the vision line. The programme-wide counts are several
times larger. So the sentence names a population the four were mostly
*not* drawn from, and it is a count-shaped claim the set's own rule
forbids holding bare (a count can be held while the list beneath it
changes).

**Fix.** Either name the three lines the four came from, without counts
("the affect, social-simulation and vision lines of the programme's
record, each pre-registered"), or keep the counts only for the line they
belong to and say the other three experiments come from elsewhere. The
paragraph's real point — "a result is reported when it has been written up
against a pre-registration, not when it exists" — survives either way and
is worth keeping verbatim.

---

## C. Numbers stated without their meaning

1. l.102–103 "A glass-box readout taken from the graph rather than from
   behaviour gives cloth proximity **53 against wire 8** at equal bond
   strength." No unit, no scale, no definition of "proximity". Say what is
   counted (ticks adjacent? distance units?) or drop the numbers and keep
   the qualitative point that the graph readout agrees with the behaviour.
2. l.146 "the **deterministic anchors** are 5 and 25." The term is the
   record's, not the paper's. Define once: the wait produced by the
   noise-free run at that cell, against which the n = 60 spread is
   reported.
3. l.185–186 "belief and arousal move under induction (**0.500 → 0.245**;
   0.0 → −9.25)" while the table two lines up gives non-contingent belief
   **0.256** [0.253, 0.259]. The record says 0.245 is the deterministic
   trace and 0.256 the n = 200 mean. The paper gives both without saying
   so; a reader sees a mismatch. One clause: "(the deterministic trace;
   the n = 200 mean is in the table)".
4. l.194–200 (inversion arms): "an inversion-cost arm returns a differential
   of exactly zero" — of what? Say the measure (recognition rate upright
   minus inverted, configural and part-based). "A floor arm confirms both
   states are reachable" — which states? The record's arm table says; one
   phrase each.
5. l.85–86: three of the six Harlow/helplessness table cells are
   degenerate intervals ([1.000, 1.000], [0.000, 0.000]). Fine to report,
   but say once that a degenerate interval means zero between-subject
   variance at that n, not a claim of certainty.

---

## D. Falsifiability section

1. **No tags definition.** Every other paper now carries 01's
   `[shape]`/`[detail]` sentence verbatim before its list; 02b uses the
   marks with no definition. Add it.
2. **Item 8 is a scope note, not a commitment.** "Reproduction is not
   evidence about organisms … a reader who finds one has found an error
   rather than a result" — 01b and 02a just moved exactly this shape out
   of their lists ("falsified by a misreading is a fact about a reader,
   not a result"). Do the same: a scope note after the list, and the list
   goes to seven.
3. **Item 3 "Impatience does not require a deficit"** is `[shape]` and
   says it "would be settled against by its non-replication". A
   non-replication of one arm in this substrate costs a mechanism, not the
   grounding's reach; `[detail]`. Item 2 (non-identifiability) is the
   `[shape]` one and is correctly marked.
4. **Item 5's falsifier is a prediction the paper has not run**: "fails if
   adding a privileged upright frame does not restore the inversion cost".
   That is the right commitment and should be flagged as *not yet tested*
   — say so in the item, as 02 does for its class-indexed entries ("states
   what would be risked rather than what currently is").

---

## E. Naming, cross-references, mechanical

1. Draft box names only the grounding companion; body says "the theory
   paper" (l.57) and "the grounding companion". Add the naming sentence
   (Graphic Equalisation; *Seldon*; the Seldon grounding) with the
   "inherits their definitions…" clause, as 02a now has.
2. `xr-hyper` is barely needed — the paper cites no companion result by
   number — but `sec:inversion`'s "the composition already treats [a
   rotation] as free" is 01's rung-1 transform claim and could point at
   Graphic Equalisation by name; and `rem:dissolution`'s two-factor
   design is the applied form of 02's two-fields result
   (`SM-def:trap`'s cost/capacity split). One sentence each, optional.
3. Title/subtitle name two of the four experiments ("Contact Comfort,
   Delay of Gratification, and What a Substrate Produces…"). Either add
   the other two or make it "Four Classical Experiments, and What a
   Substrate Produces Without Being Fitted To It".
4. `\texorpdfstring` on the `\date` dashes; `thebibliography{9}` fine for
   six; `et al.` → `et~al.` in two labels.
5. Bibliography is not alphabetical (Seligman, Yin, Thompson, Harlow,
   Kidd, Watts). Sort.

---

## What is right and should not be touched

- The abstract's and scope's insistence that "nothing here is evidence
  about children or monkeys" and the distinction between *reproduced* and
  *available from the machinery without being put there*.
- `rem:ethics`: a simulation of a deprivation protocol carrying a
  byte-identical-restoration gate, with the honest limit that restoration
  "establishes that nothing persisted, not that nothing happened".
- `rem:priority`: the confound is Kidd's and Watts's; what is claimed is
  that it falls out of machinery carrying no term for self-control.
- The face-inversion negative, diagnosed (uniform inversion folds to a
  rotation the composition treats as free) and converted into a
  commitment about what adding the missing frame should do.
- `sec:discipline`'s last paragraph: "It establishes that the model is
  the thing being reported, which is a different and lower bar, and one
  that a great deal of published simulation work does not clear."

---

## Suggested order

1. **A** and **B** — evidence standing and the population sentence; these
   are the two places a reader would lose trust.
2. **C** — five numbers given their meaning.
3. **D** — tags sentence; item 8 to a scope note; two re-marks.
4. **E**.
