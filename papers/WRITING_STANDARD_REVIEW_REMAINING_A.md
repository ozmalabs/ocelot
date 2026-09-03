# WRITING_STANDARD Review — Cluster A (Remaining)

**Scope.** A read-only review against `papers/WRITING_STANDARD.md` (the shared
communication standard) of three formal sources:

- `formal/01s_graphic_equalisation_statement.tex` — *The Law of Graphic Equalisation — Statement*
- `formal/01d_graphic_equalisation_born_recovery.tex` — *The Law of Graphic Equalisation — Born Recovery*
- `formal/02b_seldon_manifolds_social_and_psychological_application.tex` — *Seldon Manifolds — Social and Psychological Application*

This is a **WRITING_STANDARD** review — reader/claim/path coherence, commitment
posture, register, reference economy, novelty posture — **not** a content or
truth peer review. Content correctness is only touched where a prose claim
plainly exceeds its own stated scope.

**01s is a generated file.** Its header states, and `papers/README.md` confirms,
that `01s.spec` + the long paper (`01_law_of_graphic_equalisation_theory_referenced.tex`)
are the sources of truth and the `.tex` is built by `tools/build_statement.py`.
The pulled theorem/definition/proposition/falsifier blocks originate in the long
paper; the connecting prose originates in `01s.spec`. **Every 01s recommendation
below is therefore routed to a source location** — a `01s.spec` line for
connecting prose, or a long-paper label for pulled material — never to the
generated `.tex`. For the reader's convenience each item gives both the current
generated `.tex` line range (what a reader sees today) and the source line/label
to edit.

### Exact current revisions (as read this session)

| file | title-block draft | footer / notice | provenance tag |
|---|---|---|---|
| `01s_..._statement.tex` (generated) | `draft-2026-09-02.1` · statement | `draft-2026-09-02.1 / statement / from long r280` | built from long r280 |
| `01s.spec` (source) | `draft-2026-09-02.1` · statement | — | `@source` long paper |
| `01d_..._born_recovery.tex` | `draft-2026-09-02.1` · document revision 3 | `draft-2026-09-02.1 r3` | r3 |
| `02b_..._application.tex` | `draft-2026-09-02.1` · document revision 5 | `draft-2026-09-02.1 r5` | r5 |

Draft strings are internally consistent within each file (title block = notice =
footer). No cross-file draft-uniformity check is in this review's scope; the
cluster-wide bump is governed by `tools/check_draft_consistency.py` per
`papers/README.md`.

---

## Executive verdict per paper

**01s — Statement. PASS, strong.** This is among the most disciplined prose in
the set against the standard. The framing box is explicit about what is asserted
vs. argued and *why* (the removals are the long paper's work), which is the exact
"committed hard, held soft" posture the standard wants. The section-opening
connecting prose consistently states each section's one job first and creates the
need the pulled blocks then settle. No apologies, no novelty theatre — the ledger
and the "only claim is the arrangement" posture are model-grade. Findings are
narrow: two P2 optional polish items on connecting prose, and one P2
verification item on the omitted-falsifier list staying in sync. No P0/P1.

**01d — Born Recovery. PASS.** The claim-before-mechanism ordering is exemplary:
"recover, not derive" is stated in the abstract, given its own named remark
(`rem:recover`), and held as the governing verb throughout. The two positive
findings are stated up front and the residuals are enumerated rather than buried.
Reference economy is good — reconstruction theorems are cited where they supply
uniqueness, not as decoration. Findings: one P1 (a scope-coherence wrinkle where
the abstract's "only claim is the arrangement" sits beside sharper in-body
forcing language that is correctly hedged but not obviously the *same* claim as
the abstract), and two P2 polish/economy items.

**02b — Social and Psychological Application. PASS, strong.** The reader-first
payoff is excellent: the abstract leads with "one of the four does not reproduce"
and names the negative as the most informative result — a textbook use of the
standard's "use failure as motion" rule. The substrate-vs-organism scope
discipline is stated once, enforced structurally, and not re-disclaimed to death.
The `[shape]`/`[detail]` falsifier tagging is well-formed. Findings: one P1
(a single scope-guard sentence in §1 that is dense enough to blur the very
distinction it is protecting) and two P2 items.

---

## 01s — Statement

Routing key: **spec** = edit `01s.spec`; **long** = edit the named label's block
in `01_law_of_graphic_equalisation_theory_referenced.tex`; the generated `.tex`
line range is given only to locate the current text.

### Strengths to preserve (do not weaken in any edit)

- **S1 — The framing box (`.tex` 51–68; source: `01s.spec` 11–28).** "What is
  missing here is not detail but *argument*" and "Calling this a short form would
  describe it by its length instead of by what it does" is precisely the
  standard's *Contribution check* and *committed-hard/held-soft* posture done
  well: it states the document's job, its boundary, and why the omission is not a
  weakness, without a single hedge-word. Preserve verbatim.
- **S2 — Ledger posture (`.tex` 159–183; source: `tab:ledger` in long paper +
  spec 66–69 lead-in).** "named entries, not a count" and the Admitted/Taken to
  follow/Postulated columns implement *Attribution/novelty* honestly. This is the
  opposite of novelty theatre and should be kept.
- **S3 — Falsifiability lead sentence (`.tex` 547–551; source: spec 183–187).**
  "The substrate risks little by design and the groundings carry the risk"
  states the exposure boundary in one line before the enumeration — a strong
  *Path check* opener.
- **S4 — Section-opener discipline throughout.** Every `\section` opens with a
  one-sentence statement of that section's job (substrate 78–81, determinism
  186–189, frames 217–219, identity 297–299, economics 319–323, refusal 381–384,
  time 434–436, carvings 513–517). This is the standard's "give every section
  one job and say that job early" satisfied at document scale.

### Findings

**P2 — Optional. `.tex` 264–266 // source `01s.spec` 98–100.**
Quote: "*a disclosure that moves a gate changes the first, and that is where an
information hazard is located here rather than treated as a class of its own.*"
- Rule: *Narrative — keep every promise short-range* / *Path check*.
- Diagnosis: The sentence raises "information hazard" as a forward promise and
  the next three pulled blocks (`def:capability`, `def:info-hazard`,
  `prop:hazard-threshold`) settle it — so the promise *is* short-range and paid.
  The only friction is that "changes the first" refers back to "what its gates
  admit" two clauses earlier; a reader mid-paragraph must hold the antecedent.
- Direct-violation vs optional: **optional**. The promise is paid; this is
  clause-length ergonomics only.
- Smallest repair (in `01s.spec`): replace "changes the first" with "changes what
  the gates admit" so the referent is local. Verification: the sentence stands
  alone without back-reference.

**P2 — Optional. `.tex` 494 // source `01s.spec` 159.**
Quote: "*The account forbids very little, and what it does forbid is one thing
recurring rather than a list.*"
- Rule: *Sentence/clause — keep the causal path short* / *Continuation check*.
- Diagnosis: Strong claim-first opener for the prohibition section, well placed.
  It sits *between* `prop:runner-recursion` and `prop:prohibition` (the
  section header for "Primitives, and the single prohibition" is at 469 and
  contains the primitive blocks first). A reader arriving at 494 has just left
  the runner-recursion material; the transition relation from that block to this
  sentence is "and, stepping back, here is the single thing forbidden" — currently
  implicit.
- Direct-violation vs optional: **optional**. The relation is inferable.
- Smallest repair (in `01s.spec` at 159): prepend a three-word relation cue,
  e.g. "*Stepping back:*" or "*Across all of it,*". Verification: *Coherence
  check* — the paragraph transition can now be named (summation).

**P2 — Verification test (not a defect). `.tex` 586 // source `01s.spec` 213–221
(the `@falsifier` list) and long-paper falsifier titles.**
Quote: "*Not carried in this statement:* A held program is one write;
Partial-order sufficiency; Globally-async/locally-sync; Externalising lengthens
the interval before a crossing is legible; No free lunch; Description length is
constitutive, not merely a method."
- Rule: *Contribution check* / *Reference check* — the omission must "stay
  checkable in this document."
- Diagnosis: This hand-maintained "Not carried" list is the mechanism by which
  the statement keeps its own omissions honest — a genuine strength. But it is
  connecting prose (spec-authored, "not synchronised", per the box at `.tex` 66),
  so it can drift from the long paper's actual falsifier set as the long paper
  gains or renames commitments. Nothing in the build guarantees this list equals
  (long-paper falsifiers) − (pulled falsifiers).
- Direct-violation vs optional: **not a current violation** — as read, the list
  is plausible and the mechanism is exactly what the standard asks for.
- Verification test: cross-check the six titles here against the long paper's
  full falsifier titles minus the 27 `@falsifier` entries pulled in the spec
  (lines 189–216). If any long-paper falsifier is neither pulled nor listed here,
  it has become a silent omission — the one failure mode this sentence exists to
  prevent. Route any fix to `01s.spec` (the list) or the long paper (the source
  titles), never the generated `.tex`.

**Note on pulled blocks.** The theorem/definition/proposition prose (e.g.
`prop:economics` at `.tex` 324, `prop:runner-opaque` at 358, the falsifier
enumeration at 552–585) reads as strong committed-hard/held-soft prose, but it is
**generated from the long paper** and out of this cluster's editable scope. No
recommendation is made against it here; any WRITING_STANDARD concern with pulled
text belongs to a review of the long paper (paper 01), routed to its labels.

---

## 01d — Born Recovery

### Strengths to preserve

- **S1 — Verb discipline (abstract `.tex` 48–51; `rem:recover` 108–121; §2 head
  102–105).** "The honest verb throughout is *recover*, not *derive*" is stated
  in the abstract, named as a remark, and enforced in every rating. This is the
  standard's *Commitment check* and "prefer *recover* to *derive* where a known
  result is reproduced" (Attribution section) done to the letter. Do not soften.
- **S2 — Claim sized before mechanism (§2 `sec:claim` 101–125).** "The only real
  claim is the *arrangement*" precedes the axiom mapping, and the rating scheme
  (solid/earned/plausible/contingent, defined at 155–159) is introduced before it
  is used. Reader-first, dependency-ordered.
- **S3 — Ratings-as-invitation (`.tex` 254–259).** "*a reader who upgrades one of
  them is disagreeing with a rating, which is the intended form of the
  disagreement*" — this converts a soft spot into a falsifiable handle, exactly
  the standard's "a boundary they can use to disagree with it."
- **S4 — Residuals enumerated, not buried (`sec:residuals` 335–367).** The five
  open items, including "the one posit the recovery rests on" (linearity),
  satisfy "use failure, residual, and retraction as motion" and "do not hide
  nulls in appendices."

### Findings

**P1 — Direct (coherence, document scale). Abstract 71–73 vs body 108–121 /
234–261 / `rem:misframing` 300–316.**
Quotes: abstract — "*The only claim made here is the arrangement; each component
is individually known, and the uniqueness is supplied by the cited theorems.*"
Body (`prop:crux` region, 234–241) — "*That two separate reconstructions' crux
axioms are both already-present substrate structure ... is the substantive
positive finding of this note.*"
- Rule: *Path check* / *Coherence check* — "Can a new reader state the opening
  claim ... without reconstructing missing links?"
- Diagnosis: The abstract says the *only* claim is the arrangement. The body then
  presents two "findings" (Prop `opt` at 180–186 and Prop `crux` at 224–232) and
  calls the second the "substantive positive finding." A careful reader reconciles
  these — the "finding" *is* that the arrangement holds natively — but the words
  "only claim is the arrangement" and "substantive positive finding" are not
  obviously the same claim on first read, and the abstract does not name the two
  findings it later foregrounds. The abstract's own second half (52–66) *does*
  enumerate the two findings, so the tension is between the abstract's last
  sentence (73) and its own middle. This is a real link the reader must build.
- Direct-violation vs optional: **direct** but low-cost — it is a coherence gap,
  not a false claim.
- Smallest repair: in the final abstract sentence (72–73), tie the two together
  explicitly, e.g. "*The only claim is the arrangement — that the two crux axioms
  above are already-present substrate structure; each component is individually
  known, and the uniqueness is supplied by the cited theorems.*" Verification:
  a reader can now state the opening claim and see it is the same object the body
  calls the positive finding.

**P2 — Optional (reference economy). `.tex` 122–125 (end of §1) and 316–321
(end of `rem:misframing`).**
Quote (122–125): "*Complex over real is then not a gap to be closed by a forcing
argument but the signature of a contingent selection, self-located exactly as the
number of spatial dimensions is.*" This same "self-located exactly as the number
of spatial dimensions" analogy recurs at `rem:recover` (114–116), `prop:contingent`
(287–292), and `rem:misframing`.
- Rule: *Reference check* / "Establish a small set of load-bearing terms, re-use
  them consistently" — the flip side is not re-establishing the same analogy four
  times.
- Diagnosis: The spatial-dimensions analogy is load-bearing and correctly
  re-used, but it is *re-explained* (not merely referenced) at least three times.
  The standard permits re-introduction "when the reader has travelled far enough";
  here the recurrences are close together (§2, §5 twice), so the later ones read
  as restatement rather than earned re-introduction.
- Direct-violation vs optional: **optional**.
- Smallest repair: at the second and third occurrences, compress to the bare
  analogy ("as with the number of spatial dimensions") and drop the re-explanation,
  letting the first statement (114–116) carry it. Verification: *Reference check*
  — each later mention points back rather than re-arguing.

**P2 — Optional (sentence path). `.tex` 264–266 (opening of `sec:complex`).**
Quote: "*Local tomography is the axiom that selects complex Hilbert space over
real, and it is where a forcing argument would have to sit.*"
- Rule: *Sentence/clause — agent, action, consequence visible*.
- Diagnosis: Strong claim-first opener. The following table (267–276) resolves it
  well. Minor: "where a forcing argument would have to sit" is a spatial metaphor
  for a logical location; it pays off two paragraphs later at `rem:misframing`
  ("*Why forcing is the wrong question*"), so the promise is short-range and kept.
  No change needed to the relation; flagged only to confirm it is *not* a defect.
- Direct-violation vs optional: **optional / no action** — recorded so a later
  editor does not "fix" a working forward-reference.

---

## 02b — Social and Psychological Application

### Strengths to preserve

- **S1 — Reader-first payoff, failure as motion (abstract 51–64; `sec:inversion`
  225–256; `rem:negative` 243–255).** "*one of the four does not reproduce*" leads
  the abstract, and the negative is named "the most informative of them." §5 then
  delivers a *diagnosed* boundary ("no privileged upright frame to be costly to
  leave") with a forward commitment (the falsifier at 305–316). This is the
  standard's "use failure, residual, and retraction as motion" at its best. Do
  not let any edit demote the negative.
- **S2 — Scope discipline stated once (abstract 62–64; `sec:scope` 66–92; scope
  note 361–363).** "*Nothing here is evidence about children or monkeys*" and
  "*The results below are about a substrate and not about people*" fix the claim
  boundary early and it is "not re-disclaimed at each section" (89–92) — the
  standard's *Tone check* (no ceremonial padding) and *Commitment check* together.
- **S3 — Estimand honesty (`sec:harlow` 108–124).** The paragraph distinguishing
  the between-subject mean interval from a binomial proportion interval, and the
  explicit reading of degenerate `[1.000,1.000]` intervals as "zero
  between-subject variance ... not a claim of certainty", is *Commitment check*
  done rigorously: it names exactly what the number does and does not say.
- **S4 — "Agrees with the literature, which is the point" (`rem:priority`
  189–199).** Leading with what is established and sizing the contribution as
  "smaller and different in kind" is model *Attribution/novelty* posture.

### Findings

**P1 — Direct (coherence, sentence/paragraph scale). `sec:scope` 84–89.**
Quote: "*What is offered here is a pre-registered implementation record which is
not circulated with these papers, and it is a claim a reader may decline to credit
on exactly the terms Graphic Equalisation sets for the same case. The commits, the
seeds and the audits make each claim below reproducible by the programme and not by
a reader holding only this paper; a reader who declines to credit them is declining
on terms this paper accepts rather than disputes.*"
- Rule: *Sentence/clause — prefer shorter causal paths; split when a sentence has
  several logical steps* / *Coherence check*.
- Diagnosis: This is the passage that protects the paper's entire epistemic
  standing (reproducible-by-the-programme, not by a lone reader), so it must be
  the clearest paragraph in the paper. As written it packs four moves into two
  long sentences: (a) the record exists but is not circulated; (b) a reader may
  decline to credit it; (c) commits/seeds/audits make it reproducible by the
  programme; (d) declining is on terms the paper accepts. The doubled
  "decline to credit ... declining ... accepts rather than disputes" makes the
  reader re-parse who is conceding what. The distinction being protected (available
  to the programme vs. to a lone reader) is exactly the one the density blurs.
- Direct-violation vs optional: **direct** — a load-bearing claim whose path is
  harder to retrace than it should be.
- Smallest repair: split into three sentences on the three moves: (1) what the
  record is and that it is not circulated; (2) what the commits/seeds/audits buy
  (reproducibility by the programme); (3) the one-clause consequence for a lone
  reader. Verification: *Continuation check* + *Coherence check* — each sentence's
  relation to the next is nameable (existence → mechanism → consequence).

**P2 — Optional (register/economy). `sec:scope` 89–92.**
Quote: "*One standard governs the whole of that, and this paper is entirely such a
report. ... it names no implementation identifiers, and it is not re-disclaimed at
each section below.*"
- Rule: *Register discipline* (formal) / *Tone check*.
- Diagnosis: The "not re-disclaimed at each section" promise is good and kept.
  The phrase "One standard governs the whole of that" is slightly ceremonial and
  its antecedent ("that") reaches back across the previous dense paragraph — the
  same passage flagged in the P1 above.
- Direct-violation vs optional: **optional**, and partly resolved if the P1 split
  is made.
- Smallest repair: name the antecedent ("*One standard governs record, commits and
  audits alike*") or fold this sentence into the repaired P1 block. Verification:
  the antecedent of "that" is local.

**P2 — Optional (path, section transition). Between `sec:discipline` (257–272)
and `sec:record` (273–288).**
Quote (end of §7, 270–272): "*It establishes that the model is the thing being
reported, which is a different and lower bar, and one that a great deal of
published simulation work does not clear.*" Quote (open of §8, 274–277): "*Four
experiments are reported here in full, and they come from three different lines of
the same substrate's record rather than from one.*"
- Rule: *Section and paragraph — the section boundary must say what is now held
  and what is needed next.*
- Diagnosis: §7 closes on the audit's epistemic bar; §8 opens on provenance/line
  count. The relation (from "the runs are honestly reported" to "and they were
  selected from a larger record") is a shift of topic the boundary does not name.
  It is inferable but not signposted.
- Direct-violation vs optional: **optional**.
- Smallest repair: one bridging clause at the head of §8, e.g. "*Given that
  discipline, the provenance of the four is worth stating:*". Verification:
  *Coherence check* — the transition relation is now nameable (scope/extension).

---

## Cross-paper / cluster coherence

- **C1 — Shared falsifier grammar is consistent.** 01d (369–376) and 02b (289–298)
  use the identical `[shape]`/`[detail]` convention with the same gloss ("a
  `[detail]` failing is a revision ... a `[shape]` failing costs *range*"). 01s
  carries the same tags in its pulled enumeration. This is good cluster-level
  reference economy — the tag is defined once per paper and used consistently.
  **Recommendation:** none; preserve. Only note: the gloss paragraph is repeated
  near-verbatim in 01d and 02b. That repetition is defensible (each paper must
  stand alone), so it is **not** flagged as a defect.
- **C2 — Shared "recover, not derive" posture.** 01d's verb discipline and 01s's
  ledger both refuse to overclaim ("recover" / "arrangement" / "named entries, not
  a count"). 02b extends the same posture to empirical reproduction ("a fact about
  the substrate's entailments and not additional evidence for the psychology").
  The three are coherent in stance; a reader moving across them meets one
  consistent novelty posture. Preserve.
- **C3 — "count vs list" motif is used identically.** 02b `sec:record` 284–287
  ("*a count is a thing that can be held while the list beneath it changes*") and
  01s's ledger ("named entries, not a count") apply the same principle (which also
  appears in `CLAUDE.md` as a standing rule). This cross-paper consistency is a
  strength; no action.
- **C4 — Cross-references are structural, not decorative.** Spot-checked: 01d's
  reliance on `PH-prop:born`/`gleason1957` (285–292) and 02b's reliance on
  `AD-sec:ladder` (247, 313) each carry a conceptual step (the uniqueness of the
  squared modulus; the "inversion folds to a free rotation" diagnosis), satisfying
  the standard's "explain a reference only when it carries a structural step."
  No over-citation found in the connecting prose of any of the three.

---

## Consolidated ledger

| ID | Paper | Priority | Kind | Current `.tex` locus | Route (source) | Rule | Status |
|---|---|---|---|---|---|---|---|
| 01s-1 | 01s | P2 | optional | 264–266 | `01s.spec` 98–100 | short-range promise / clause | back-reference clarity |
| 01s-2 | 01s | P2 | optional | 494 | `01s.spec` 159 | transition relation | add summation cue |
| 01s-3 | 01s | P2 | verification | 586 | `01s.spec` 213–221 + long titles | contribution/omission checkable | sync-check, not a defect |
| 01d-1 | 01d | **P1** | direct | abstract 71–73 vs body 180–186/224–241 | edit 01d directly | path/coherence | tie "only claim" to the named finding |
| 01d-2 | 01d | P2 | optional | 114–116/287–292/300–316 | edit 01d directly | reference economy | compress repeated analogy |
| 01d-3 | 01d | P2 | no-action | 264–266 | — | sentence path | working forward-ref; do not "fix" |
| 02b-1 | 02b | **P1** | direct | 84–89 | edit 02b directly | short causal path / coherence | split 4-move passage |
| 02b-2 | 02b | P2 | optional | 89–92 | edit 02b directly | register/tone | localise "that"; maybe fold into 02b-1 |
| 02b-3 | 02b | P2 | optional | 270–277 | edit 02b directly | section boundary | add bridging clause to §8 |

No P0 findings in any paper. Two P1 findings (01d-1, 02b-1), both coherence — no
false claims, no commitment failures, no apologies, no novelty theatre found in
any of the three.

---

## Verification block

**Files read in full this session:**
- `CLAUDE.md` (repo root)
- `papers/WRITING_STANDARD.md`
- `papers/README.md`
- `papers/formal/01s_graphic_equalisation_statement.tex` (generated, 608 lines)
- `papers/formal/01s.spec` (source of truth for 01s connecting prose + pulls, 224 lines)
- `papers/formal/01d_graphic_equalisation_born_recovery.tex` (462 lines)
- `papers/formal/02b_seldon_manifolds_social_and_psychological_application.tex` (367 lines)

**Companion/context consulted only to validate specific dependencies (not fully
reviewed):** the `papers/formal/` directory listing (to confirm 01s is generated
and to read exact revision/footer strings); line-anchor greps within the three
assigned sources and `01s.spec` to fix citation ranges. No other paper was
opened for review; the long paper (01) and physics/mind/Narrativium/Seldon
companions were referenced by label only, per the routing rule, and not read.

**Routing confirmation (01s):** 01s is generated; all 01s recommendations are
routed to `01s.spec` (connecting prose) or to long-paper labels (pulled blocks).
No recommendation asks for an edit to the generated `01s_..._statement.tex`.

**Confirmations:**
- Report-only: **confirmed** — no TeX, PDF, AUX, LOG, counts, README, standard,
  experiment, draft, or other-report file was modified. The only file written is
  this report, `papers/WRITING_STANDARD_REVIEW_REMAINING_A.md`.
- No network: **confirmed** — no web or external calls made.
- No compile: **confirmed** — no `pdflatex`, no `build_statement.py`, no build of
  any kind was run.
- No commit / no push: **confirmed** — no git operations performed.
- Defects: none invented; every finding cites a current line range and a concise
  quote, names a WRITING_STANDARD rule, and gives the smallest repair or a
  verification test. Substantial guide-compliant strengths are recorded per paper
  so they are not weakened by later edits.
