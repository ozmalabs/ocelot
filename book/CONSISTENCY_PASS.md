# Consistency pass — full draft, first sweep

**Scope:** all 23 chapter files (~45,000 words), checked mechanically and by
reading. Chapters were drafted out of reading order, and the theory changed
underneath several of them, so this pass was a prerequisite for anything else.

## What was checked mechanically

| check | result |
|---|---|
| section numbering monotonic within each chapter | clean (no out-of-order, no mixed prefixes after the §14.x and §9.2a/§15.4a insertions) |
| internal `§N.M` references resolve to a real section | clean |
| cross-chapter "chapter N" references resolve to a real chapter | clean |
| every capability chapter closes on falsifiers | clean; the three without them are front matter, prologue and epilogue, correctly |
| every chapter carries a source note | clean except the front matter, which is a reader's note rather than a sourced claim |
| stale phrasings from before the theory revisions | two hits, both correct usage — chapter 14 names the weak form of the time claim *in order to reject it*, and chapter 16 describes the retracted Stage A conclusion *as history* |

## What was fixed

**Three recurrence gaps against `BOOK_PLAN.md`.** The plan claims specific
cross-chapter recurrences are the book's real argument; three were asserted in
the plan and absent from the text.

- **Chapter 1 never named the propose/decide split.** The additive depth
  generators *are* its first appearance, and the chapter described them without
  saying so. Now named where they land, pointing forward to chapters 2, 5, 6 and
  8 — with the honest note that nothing there was built to demonstrate the
  split.
- **Chapter 13 never named the appraisal template.** A resident deciding
  anything runs the same rule as chapter 10's marshmallow child and chapter 12's
  intent control. Now stated as *one rule doing developmental, clinical and
  civic work* — a town being that rule a hundred times over with different held
  values.
- **Chapter 8's frame-invariant tie was implicit.** It said "a language is a
  frame" without invoking chapter 2's test. Now applied in its literal form.

**Three miscounts.**

- *"Fourteen capabilities"* (introduction and chapter 14) → **ten**. The
  capability chapters are 1 and 5–13.
- *"Seventeen chapters earlier"* (chapter 19, on where the free-will position
  comes from) → the commitments are Part V's, five chapters earlier. Reworded to
  name them instead of counting: a standpoint axiom and a determinism
  proposition, neither written with free will in view.
- *"Four hundred pages"* (epilogue) → **nineteen chapters**. At ~45,000 words
  the page figure was inflated by more than double, in the one passage where
  overstatement would be least forgivable.

**One overclaim.** Chapter 1 said the propose/decide split "arrives without
being designed for". Softened to what is defensible: nothing was built to
demonstrate it, and the sentence describes what the two depth generators already
do.

**One naming inconsistency.** Stage A was named in the epilogue and described
anonymously in chapters 15 and 16, so a reader could not connect three accounts
of the same artefact. Named in all three.

## What was checked by reading, and found sound

- **The drift is told once and referenced twice**, not told three times: the
  front matter gives it in full as the book's opening argument, chapter 1's
  ledger carries it as retraction 4, chapter 16 references it under
  positive-control. Same for the sixteen inert instruments.
- **Stage A is consistently *falsified*** in all three places, with the
  retracted duplicate-concept conclusion described as history in the one place
  it appears.
- **No chapter claims the humanoid walks.** Chapter 9 states the DAG position
  (walking two stages up), the current status (stage ordinal 3, zero clinical
  milestones), and the explicit denial.
- **Numbers shared across chapters agree**: +51.5pp and 73.5% (chapters 2 and
  5), 44 of 55 (chapters 3 and 15), the violence productions count (chapters 13
  and 15), the mirror-image regime failure (chapters 9 and 17).

## Known and deliberate

- **Part VII has no measurements**, and says so in three places rather than one.
  That is repetition by design: each chapter has to be readable alone by someone
  who will not read the other two.
- **Chapter 12 opens on a mechanism rather than a scene**, breaking the voice
  contract's usual opening. Deliberate, and stated in `BOOK_VOICE.md` — a vivid
  opening on that subject is the failure the source line spent fifteen
  preregistrations avoiding.
- **Chapter 10's posture paragraph comes before its claim.** Also deliberate:
  the posture *is* the claim's bound, and putting it second would read as a
  retreat.

## Not yet done

- No line edit. This pass was structural and factual.
- Figures are referenced by ID in the text; no chapter has been laid out with
  its figures in place, so figure/prose adjacency is unverified.
- The per-chapter data figures for chapters 5–13 do not exist yet, so several
  `[FIG]` references in those chapters point at figures still to be drawn.
