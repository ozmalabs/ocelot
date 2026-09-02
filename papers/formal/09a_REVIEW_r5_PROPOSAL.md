# Review of `09a_adaptability_implementation.tex` (draft-2026-09-02.1, r5) — proposal for fixes

Scope: the whole file (197 lines, 4 pp), its log, and — because every
sentence in it is a report from the record — the record itself, re-run on
2 September 2026 for every count. Line numbers are r5. Nothing applied.

Compile: 0 warnings, 0 overfull, no citations. No implementation
identifiers. The stance (the algebra is native, the faculty is not; the
parallelogram result is about the corpus, not the agent; the 96%
retraction is the principal result) is right and is the set's clearest
statement of the self-repair boundary. **The findings: one of the three
neighbouring-operation counts is wrong in a way that strengthens the
paper; the reading-arc section describes a gate the reviewer could not
locate; two record caveats are missing; and the abstract overclaims
"at scale".**

---

## A. The counts, re-run today

| claim | paper | record / tree today | status |
|---|---|---|---|
| rules across seed manifests | 3,843 / 805 | 3,843 / 805 | matches |
| witness-retaining anti-unification in the faculty module | 7 | 7 | matches |
| faculty module length | 1,241 lines | 1,241 | matches |
| witness-retaining anti-unification in seed rules | 0 | 0 | matches |
| recognisers in the corpus | 2,851 | 2,851 | matches |
| parallelogram families / sampled transfers | 318 / 200 of 200 | 318 / 200/200 | matches |
| concept-grain bridge | 142 × 137; 8,575 → 321; 8,253 withdrawn; 39.6%; 78 corroborated | all match | matches |
| synthesis null | 54 of 257, both arms, identical set | matches | matches |
| **"coverage in twelve seed files, unification in eleven, substitution in three"** (l.110–111) | 12 / 11 / 3 | **coverage 12 (plus 6 of an open-coverage variant); unification 0; substitution 0** | **wrong in two of three** |

The eleven files counted as "unification" contain the **witness-discarding
anti-unification** term, not unification; the three counted as
"substitution" contain the substring only, and no seed rule invokes the
substitution term at all. So the rule layer holds *coverage* and the
*classical lgg that throws away its witness* — and holds neither the
witness-retaining form, nor substitution, nor unification.

That is a sharper finding than the one printed, and it is exactly the
companion's `sec:prior` sentence: "an lgg that throws away its witness
cannot adapt anything." **Fix:** correct the sentence to the measured
census and say what it shows — the vocabulary in the rule layer is the
classical one; the two operations that carry a transform (witness and its
re-application) are the two that no rule invokes. Falsifier 1 then
extends naturally: fails on any seed rule invoking witness-retaining
anti-unification *or* substitution.

Counts must be generated, not hand-held (01's and 06's rule). A
`09a.counts.tex` written by a script — rules, manifests, recognisers,
per-term seed-file census, faculty-module occurrences and length — read
at a named commit and date, with the stamp in the text. The paper says
"every count below was obtained by running a command against the tree";
make that true at every revision.

---

## B. Two record caveats the paper omits

1. **`rem:parallelogram`.** The record states: only **one** of the 318
   transfers was verified *behaviourally* (installed and fired on the
   missing cell); the other 199 sampled measure the *algebra* — lossless,
   well-defined, novel — not that the derived rule fires. The paper's
   l.56–57 ("the result is a rule … which, installed, fires correctly")
   is true of the one; l.59–60 lets a reader take 200/200 as 200
   installations. Say: one verified behaviourally, 200 of 200 verified
   algebraically. Falsifier 3 is then stated against the right claim.
2. **`rem:retraction`.** The record states: the 321 survivors were **not
   hand-verified** — the 8,253 are withdrawn for a stated mechanical
   reason; nobody has read the 321 and confirmed each. l.74–75 "the
   corrected number is the one this paper stands behind" should carry
   that: the paper stands behind the *withdrawal*, and behind 321 as an
   upper bound with 78 corroborated. Falsifier 5 already points the right
   way; add "or if reading the 321 finds a material fraction spurious".

---

## C. `sec:reading` — the gate could not be located

l.126–154 describe: a web adapter presenting a retrieved document as a
typed graph; navigation of a preprint archive; grounding the abstract to
a *subject* with "grounded-to-primitive was false" recorded; a body pass
parsing claim-bearing environments and grounding each claim through the
construction grammar (genus + differentia, recursively, with a *depth*);
un-held constructions detected and queued; and (`rem:reading-status`)
"five tests cover it, two of them confirming that the grounding seed is
load-bearing and loads only through the loader."

Checked in the tree: a local preprint-archive adapter and a web adapter
both exist and match the description of the retrieval path. A
construction-grammar module exists. **No test file exercising the
preprint adapter, and no test asserting a grounding depth or a
grounded-to-primitive outcome, was found.** The one five-test file whose
description resembles "a blocked read is a gap the agent files on itself,
seed load-bearing, installs idempotently through the loader" is the
*program-source* reading gap (uploaded code whose read path is blocked),
not scientific-paper reading. If those are the five tests, the section
has conflated two arcs; if they are not, the five need naming in the
review record so a reader of the record can find them.

**Fix.** Either (a) locate the five tests and the source-recorded arc,
name them in this review record (not in the paper), and keep the section
at "built and gated, unmeasured"; or (b) if they are the program-read
tests, rewrite `sec:reading` to report the paper-reading path as *built,
not gated, not measured*, and move the "gated" sentence to a one-line
mention of the program-read gap as a third instance of the seam. The
paper's own principle (l.148–149: "reports it at that status rather than
at the one the machinery invites") decides which.

---

## D. Abstract and framing

1. l.34: "built, **has run at scale**, and has been measured". `sec:not`
   l.114–116 says the parallelogram result "was demonstrated in analysis
   scripts rather than as agent behaviour". A corpus census in analysis
   scripts is not the operation running at scale. Replace with "built,
   measured on the agent's own corpus, and corrected against itself".
2. l.91: "stated elsewhere in [this programme]" — the self-repair
   boundary. Name where: the assessment paper (06, `AS-` reference if a
   prefix is assigned) or say it is a standing rule of the programme's
   record.
3. l.53–54: "the companion sets out the lineage" — resolve to
   `AD-sec:prior`; l.99 "the companion's ladder" → `AD-sec:ladder`; l.172
   "the companion states its general form" → `AD-rem:plural`. Add
   `\externaldocument[AD-]{09_adaptability}` and compile after 09.
4. Naming sentence in the box (the adaptability paper; Graphic
   Equalisation; the assessment paper) with the "inherits…" clause; 01's
   evidence-standard sentence once (every figure here is from the
   pre-registered record, not circulated).

---

## E. Falsifiers

1. No `[shape]`/`[detail]` definition. Add 01's sentence verbatim.
2. Item 4 ("The parallelogram result is about the corpus, not the agent …
   a reader who extracts one has found an error rather than a result") is
   the scope-note shape the set moves out of lists. Move to
   `\noindent\emph{Scope note (not a falsifier).}` after the list.
3. Item 1: extend to substitution (A) and state the revision the count
   was taken at via the generated stamp.
4. Item 3: restate against the algebraic claim (B.1): fails if a sampled
   transfer is lossy, ill-defined, or reproduces a corpus recogniser —
   and, separately, `[detail]`: fails if a transfer that passes the
   algebra, installed, does not fire on its cell.
5. Add `[detail]` for `sec:reading` once C is settled: fails if the body
   pass grounds no claim to primitive on a paper whose claims rest only on
   held constructions.

---

## F. Mechanical

- `\texorpdfstring` on the `\date` dashes; `\title` uses `---` (fine in
  text; check the PDF bookmark).
- `sec:contrast` l.163: "with the difference measured at zero repeatedly"
  — the record's phrasing is that both harnesses produced the
  byte-identical 54-id list; say "byte-identical result sets", which is
  the stronger and the true statement.

---

## What is right and should not be touched

- `rem:selfrepair`: "the system's ability to acquire competences it was
  not given is itself a competence it cannot acquire … the faculty most in
  need of that treatment is the one that cannot receive it."
- `sec:not`'s three "it is not"s, especially "what would be required is a
  rule surface over an algebra that already evaluates".
- `sec:contrast`: "being graph-resident is what makes a faculty improvable
  by the system carrying it, and it is not what makes a faculty work."
- The 96% retraction reported as the principal result.

---

## Suggested order

1. **A** — the census corrected and generated.
2. **B** — the two record caveats.
3. **C** — the reading gate located or the section downgraded.
4. **D**, **E**, **F**.
