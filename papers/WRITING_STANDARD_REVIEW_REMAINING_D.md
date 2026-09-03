# WRITING_STANDARD review — Cluster D

**Scope.** A read-only review of four sources against
`papers/WRITING_STANDARD.md` (the shared communication standard) and the
project's register discipline, *not* a content/truth peer review. Content
correctness is engaged only where a prose claim plainly exceeds its stated
scope. Assigned sources and their exact current revisions (read from each title
block, boxed notice, and page footer):

| file | title | revision (title / notice / footer) |
|---|---|---|
| `formal/09_adaptability.tex` | Adaptability | `draft-2026-09-02.1` **r92** (all three agree) |
| `formal/09a_adaptability_implementation.tex` | Adaptability — Implementation | `draft-2026-09-02.1` **r6** (all three agree) |
| `formal/10_applied_graphic_equalisation.tex` | Applied Graphic Equalisation | `draft-2026-09-02.1` **r5** (all three agree) |
| `formal/A1_constructive_graphic_equalisation_implementation_referenced.tex` | A Constructive Realisation of Graphic Equalisation | `draft-2026-09-02.1` **r6** (all three agree) |

**A1 release-state constraint, stated once and kept separate from guide
findings.** A1 is unreleasable. This is a *release-state* fact, independent of
the writing guide, and confirmed structurally rather than assumed:

- `papers/README.md` names a set of **twelve** version-managed preprints whose
  draft string is checked by `tools/check_draft_consistency.py`. A1 appears in
  the README title table but is not one of the twelve theory/grounding papers
  the corpus circulates as results; the standing rule recorded across the
  in-tree review record (`03_REVIEW_r28`, `04_REVIEW_r19`, `06_REVIEW_r26`,
  `01_REVIEW_r278`) is that **A1 is outside the releasable set and must not be
  cited as evidence** by a releasable paper.
- A1's preamble carries **no `xr-hyper` / `\externaldocument`** (lines 1–19),
  unlike 09/09a/10 and the rest of the formal set, so its cross-references to
  "the theory" / "the foundational paper" are by prose description only and do
  not resolve to a numbered result.

Everything below marked **[release-state]** is a constraint on A1's fitness to
circulate, held apart from the **[guide]** findings, which audit A1's prose
against the standard exactly as for a releasable paper (as instructed). No A1
guide finding should be read as clearing it for release, and no release-state
note should be read as a writing defect.

**Verification posture.** Report-only. No file was modified. No network, no
compile, no AUX/LOG/counts/README/standard/experiment/draft/other-report file
touched. See the final verification block.

---

## Executive verdict per paper

**09 (Adaptability) — Strong, guide-conformant, releasable on writing grounds.**
The document paths cleanly at every scale: an opening that states the claim and
its stakes, an explicit Part I / Part II contract with distinct failure modes,
claim-before-mechanism ordering throughout, hard commitments held soft by exact
scope and a fifteen-item falsifier list, generous and honest not-novelty
posture, and no apology or padding. Findings are almost all P2 polish. The one
substantive writing risk is **length/momentum decay in Part II** (§Projection
through §Capacity): a long chain of remarks each earning the next, where the
short-range-promise discipline is met locally but the *cumulative* suspense
before the payoff (rem:interval / rem:timing) is heavier than the guide's
"continuation cheaper than reconstruction" test comfortably wants. No P0.

**09a (Adaptability — Implementation) — Exemplary on the standard, releasable.**
This is the cluster's cleanest instance of "committed hard, held soft": the
retraction is reported *as the principal result* (§What has run,
rem:retraction), figures are macro-driven from the counts file with their
epistemic status stated inline, and every positive result carries its exact
caveat (200/200 is algebraic not behavioural; 321 is an upper bound). No P0, no
P1. P2 items only.

**10 (Applied Graphic Equalisation) — Guide-conformant in construction, but
carries a real momentum/scale risk and one register pressure.** The paper is
disciplined about its own posture (Scope §sec:scope; the self-limiting
disproportion rem:cog; the testimony audit rem:testimony; the load-bearing-steps
map rem:weight), and its evidential-kind hygiene is a genuine strength worth
protecting. The writing risk is that §sec:seat and §sec:rests run very long with
dense back-reference, and the "committed hard, held soft" line is under the most
strain here of the four papers because the subject is contemporary and named.
No P0; the P1 is a coherence/continuation load issue, not a factual one.

**A1 (Constructive Realisation) — [release-state] unreleasable; [guide] the
prose is in good order for what it is.** As a writing artefact A1 is register-
clean formal-CS: statement-first theorems, honest weak-theorem labelling
(§sec:add-remove), an explicit not-novelty paragraph (§sec:prior-art), and no
padding. The guide-relevant weaknesses are (a) six by-description attributions
to "the theory"/"the foundational paper" that name no resolvable result — a
reference-economy and legibility issue the guide's reference check targets — and
(b) an opening that states the *separation* before the *reader payoff*. Neither
is a bar to the writing standard; the bar to circulation is the release-state
constraint above.

---

## 09 — Adaptability (r92)

### Strengths to preserve (do not weaken in any later edit)

- **Whole-document path is explicit and correct.** The abstract (l.45–53) states
  the claim (two capabilities are one operation) and the payoff (a quantity
  worth having, chosen against *intelligence*) together, and the Part I/Part II
  contract (l.55–66) names *why* the division exists — "An argument is attacked
  on its derivation and an application on its evidence" — which is exactly the
  guide's "make the claim's evidential path inspectable" at document scale. Keep
  this paragraph intact.
- **Claim-before-mechanism, repeatedly.** §sec:not-intelligence (l.68–78) gives
  the reader the familiar quantity first and the mechanism second; Def.~adapt
  (l.81–84) is stated then unpacked by "Three words carry it." This is
  textbook-conformant to the register-discipline "statement first" rule for
  formal papers.
- **Hard commitments held soft by exact scope.** §sec:not-claimed (l.155–162)
  and the falsifier list (l.~end) carry [shape]/[detail] tags with precise break
  locations. The closing note that two items (the half-century window; "already
  begun") are *judgements not commitments*, contestable "by contesting an input,"
  is a model of the guide's commitment check.
- **Honest not-novelty posture.** §sec:prior (l.~"Prior positions") leads with
  the four literatures that own the machinery and states the delta narrowly
  (e.g. the embedding-arithmetic critique "does not apply here … for a reason
  that is a real difference and not a defence"). No novelty theatre.
- **No apologies.** The retraction/overshoot handling ("An overshoot is a
  measurement when its loss is read") is applied, not merely professed.

### Findings

**P1 — Cumulative-suspense / continuation load across Part II.**
*Lines:* §sec:projection through §sec:capacity (the remark chain
rem:phase → rem:percolation → rem:method → rem:convergent → rem:present →
rem:unit → rem:building → rem:interval → rem:timing → rem:race → rem:individual
→ rem:expertise → rem:exchange).
*Rule:* "Make continuation cheaper than reconstruction" and "Keep every promise
short-range" (Narrative service; Revision gate 2, Continuation check).
*Diagnosis:* Each remark individually satisfies the short-range-promise test —
it answers a question the prior remark raised. But the *count* of chained
remarks deferring the load-bearing payoff (rem:interval's "interval is over
futures not years"; rem:timing's "two clocks") is large, and a reader who loses
the thread mid-chain must reconstruct a dozen intermediate holdings to re-enter.
The guide's momentum test is about the *reader's* running cost, and this chain
pushes it. This is the single place in 09 where the arrangement's ambition
outruns the reader-first budget.
*Direct-violation vs optional:* **Optional (guide-aligned improvement), not a
direct violation** — the local transitions are all nameable, which is the
guide's own splitting criterion, so no paragraph is malformed.
*Smallest repair / test:* Add one signpost sentence at the head of
§sec:projection naming the payoff the chain reaches (the reachability *difference*
of rem:interval and the two clocks of rem:timing) so the reader holds the
destination while traversing. Verification: a new reader, given only
§sec:projection's first paragraph, can state what the section will conclude
before reading the chain.

**P2 — "Part II begins here" signpost is load-bearing and slightly buried.**
*Lines:* §sec:schedules opening, "\emph{Part II begins here.}"
*Rule:* Whole-document path — "The section boundary must say what is now held and
what is needed next."
*Diagnosis:* The Part I/Part II division is announced in the front matter
(l.55–66) and re-announced here, which is good; but the re-announcement is a
single italic clause at the start of a remark-dense section. Given the P1 load,
this boundary marker is doing more work than its typographic weight suggests.
*Direct-violation vs optional:* Optional.
*Smallest repair:* None required; if the P1 signpost is added it subsumes this.

**P2 — Reference economy: `\citet{legris2025}` appears in body and in a
falsifier with near-identical "not checked here" hedging.**
*Lines:* rem:chollet closing ("Human baselines … exist \citep{legris2025};
whether they stratify … has not been checked here, so it is recorded as
untested.") and falsifier item 7 (same dataset, same untested status).
*Rule:* Reference check — "retain and explain the ones that carry coherence";
avoid restating the same caveat twice.
*Diagnosis:* Not a defect — the falsifier item legitimately needs the citation.
The body sentence and the falsifier say the same "untested" thing; the body one
could point forward rather than repeat.
*Direct-violation vs optional:* Optional.
*Smallest repair:* Leave as is, or replace the body clause's hedge with a
forward pointer to the falsifier. Low value.

---

## 09a — Adaptability — Implementation (r6)

### Strengths to preserve

- **The retraction is the headline, exactly as the guide demands.**
  rem:retraction (§sec:run, l.~76–90 region) reports the 96% artefact rate as
  "the faculty's principal measured result, not as an embarrassment adjacent to
  one," and separates what the paper stands behind (the withdrawal) from what it
  does not (the survivors). This is the guide's "Use failure, residual, and
  retraction as motion" applied without flinching. Protect this framing verbatim.
- **Figures held soft at the point of use.** rem:parallelogram states
  "\emph{Algebraically is the whole of what that second figure says}" and warns
  against "reading $200$ of $200$ as $200$ installations." Every macro-driven
  count (`\nRules`, `\nWitnessRetainingUses`, etc.) is reported with its exact
  scope. This is the strongest instance of commitment-held-soft in the cluster.
- **Reader payoff first.** The abstract's last line — "The algebra is native;
  the faculty that uses it is not." — is the claim in one sentence, before any
  mechanism. §sec:gap opens "The two halves above do not meet, and the seam is
  exactly locatable."
- **Honest arrangement posture.** §sec:contrast reports the synthesis null and
  the analogy positive *together*, "because taking either alone would
  misrepresent the record."

### Findings

**P2 — `\nWitnessRetainingFiles` is defined in the counts file but appears
unused in the prose.**
*Lines:* counts define `\nWitnessRetainingFiles`{0}; §sec:gap cites
`\nWitnessRetainingUses` and `\nWitnessInFaculty` but not the Files variant.
*Rule:* Reference/naming economy — "A term that does not carry later work does
not belong."
*Diagnosis:* This is a *counts-file* observation, not a prose defect, and the
counts file is out of scope for modification. Recording it only so a later
editor knows the prose does not depend on that macro. No prose change indicated.
*Direct-violation vs optional:* Optional / informational.
*Verification test:* `grep nWitnessRetainingFiles 09a_adaptability_implementation.tex`
returns only the `\input`-ed definition, no use. (Do not modify.)

**P2 — §sec:reading ("A second instance") lengthens the paper past its
single-claim spine without a boundary that re-earns it.**
*Lines:* §sec:reading and rem:reading-status.
*Rule:* Section/paragraph — "Give every section one job and say that job early";
whole-document path.
*Diagnosis:* The paper's spine is one seam (algebra native, faculty not).
§sec:reading adds a *second* instance of the same seam (paper-reading), which is
legitimate and well-flagged ("And the seam is the same one"), but the section is
long relative to the paper and its status caveat (built/not-gated/no-results) is
itself intricate. The guide is satisfied — the job is stated early and the
transition is named — so this is a note, not a fault.
*Direct-violation vs optional:* Optional.
*Smallest repair:* None needed; if trimming is ever wanted, the status
enumeration in rem:reading-status is the compressible part, not the claim.

**P2 — Scope note at end is correctly placed; no change.** The final "Scope note
(not a falsifier)" cleanly separates a corpus claim from an agent claim and
prevents the exact misreading the guide's contribution check guards. Recorded as
a strength, not a finding.

---

## 10 — Applied Graphic Equalisation (r5)

### Strengths to preserve

- **Scope discipline stated once and held.** §sec:scope (l.59–76): "It says what
  things cost, and not what anyone ought to do about it," repeated as a refrain
  at each remark that could be read as prescription. This is the guide's
  register discipline for editorial/applied prose done well.
- **Self-limiting justification.** rem:cog (l.109–124): the paper states that its
  own reason for concentrating on one frame "weakens at whatever rate the erosion
  proceeds … a justification that did not expire would be suspicious." This is
  commitment-held-soft applied to the paper's own method.
- **Evidential-kind hygiene is a genuine, load-bearing strength.**
  rem:testimony (§sec:rests) enumerates the five admissible input kinds and the
  aimed/unaimed axis, and rem:bias immediately turns the same discipline on the
  author. rem:weight names the three structural steps that actually carry the
  argument and demonstrates robustness by removing the two weakest citations.
  This is the guide's "make the claim's evidential path inspectable" at its best
  in the cluster. Protect all three remarks.
- **Falsifiability section is honest about retrofit.** The section preamble
  concedes "a retrofitted falsifier is worth less than a registered one" and
  states *why* it is not decorative. rem:open registers four dated predictions on
  an open case — the correct guide move.

### Findings

**P1 — §sec:seat runs long and dense enough to strain the continuation budget,
and the register is under pressure from named, contemporary subject matter.**
*Lines:* §sec:seat (rem:release, rem:actuarial, rem:vacancy, rem:proof,
rem:unseen, prop:aimed-unaimed, rem:selected, rem:open, prop:documents-not-states,
rem:document, cor:certificate-conversion, rem:certificate) and §sec:rests
(rem:testimony, rem:bias, rem:steelman).
*Rule:* Continuation check (gate 2) and coherence check (gate 3); register
discipline ("Critique the object rather than … narrating personal emotion").
*Diagnosis:* Two distinct pressures, both guide-relevant, neither factual:
  1. *Continuation load.* §sec:seat is a single case examined through a dozen
     remarks with heavy cross-reference back into §09's remark set (`AD-rem:*`)
     and within 10 itself. Each transition is nameable (so no paragraph is
     malformed), but the section asks the reader to hold a very large stack. The
     guide's test — stopping should cost more than continuing — is met locally
     and pressed globally.
  2. *Register.* The subject is contemporary institutions and (via citations)
     named office-holders. The paper's own discipline (rem:testimony, the
     "mechanism not persons" rule in §sec:scope) is the correct guard, and it is
     applied. The residual risk is that a reader perceives the accumulated
     single-frame case selection as argumentative rather than analytic — which
     rem:bias explicitly concedes ("A reader's strongest attack is … that these
     were the cases looked at"). The concession is guide-correct; the *volume*
     of the section relative to the concession is the pressure.
*Direct-violation vs optional:* **Optional / structural improvement, not a direct
violation.** The paper satisfies every named gate; the finding is that the
reader-cost margin is thin here.
*Smallest repair / test:* At §sec:seat's head, add one sentence stating what the
single seat is being used to *measure* (it is an instrument, per rem:counterfactual
and prop:documents-not-states) so the reader traverses the twelve remarks knowing
the payoff is a document-keying result, not an accumulation of grievance.
Verification: a reader given only the section head can state that the section's
conclusion is prop:documents-not-states (transitions keyed on records, not
states), before reading the case.

**P2 — Heavy `AD-rem:*` back-reference density in §sec:measures and §sec:seat.**
*Lines:* throughout §sec:measures (rem:pricing, rem:observables, rem:governance,
rem:carry, rem:channel) and §sec:seat.
*Rule:* Reference economy — "Do not explain a reference merely because it is a
reference"; re-introduce a term in ordinary language "when the reader has
travelled far enough."
*Diagnosis:* The applied paper leans on the adaptability paper's remarks by label
(e.g. "the adaptability paper's Remark~\ref{AD-rem:nowhere}") many times. Each
individual citation carries a structural step (guide-permitted), but the sheer
count means a reader without 09 open must reconstruct the referenced result each
time. Because 10 explicitly inherits 09's definitions (front matter), this is
within the guide's tolerance — but the *first* occurrence of each key
`AD-rem:*` in 10 could restate the borrowed result in one clause.
*Direct-violation vs optional:* Optional.
*Smallest repair:* At first use of `AD-rem:nowhere` (rem:pricing) and
`AD-rem:exchange` (rem:carry/rem:channel) in 10, add a five-word gloss of the
borrowed result. Verification: a reader without 09 can state what "the cheap exit
is revoking a frame" means at first encounter in 10.

**P2 — rem:frog is a strength; flag only its length.**
*Lines:* rem:frog (§sec:noadapt).
*Rule:* Narrative service ("Give people what they want first").
*Diagnosis:* The literal-source correction of the boiling-frog trope is exactly
the guide's "use failure/residual as motion" and earns its place (it fixes the
*prescriptive* error, not just the descriptive one). Recorded as a strength. The
only note is that it is one of several long remarks in a long section (feeds the
P1 load). No repair.

---

## A1 — A Constructive Realisation of Graphic Equalisation (r6)

### [release-state] constraints (kept separate from guide findings)

- **A1 is outside the releasable twelve** and is the paper other releasable
  papers are instructed *not* to cite as evidence (standing rule, in-tree review
  record). This is a fitness-to-circulate constraint, not a writing-standard
  finding, and it is not repaired by any prose edit.
- **No `xr-hyper`/`\externaldocument`** (preamble l.1–19): A1's references to
  companion results are by prose description only and resolve to nothing. This is
  simultaneously a release-state fact (it is not wired into the citable set) and
  the mechanical *cause* of the guide finding below; the two are recorded apart
  deliberately.

### [guide] Strengths to preserve

- **Register is clean formal-CS.** Statement-first theorems (thm:add-remove,
  thm:lfp), explicit assumptions, proofs, and a conformance-test list. The
  separation-of-concerns opening (§sec:separation) correctly names that this is
  one operational realisation of an extensional relation.
- **Honest weak-theorem labelling.** §sec:add-remove: "The theorem is
  intentionally weak: it establishes representational completeness … not
  efficiency, confluence, or semantic preservation." This is the guide's
  commitment check (name the scope exactly) done well.
- **Not-novelty posture is explicit.** §sec:prior-art "Novelty" paragraph: "The
  individual implementation techniques are … largely established. The
  contribution … is their disciplined composition." No novelty theatre.
- **No apologies, no padding.**

### [guide] Findings

**P1 [guide] — Six by-description attributions to "the theory" / "the
foundational paper" name no resolvable result.**
*Lines:* §sec:separation "Reading for the claim" ("The composition's own
falsifiability commitment is stated in the foundational paper and is inherited
here"); §sec:deltas / §sec:world references to "the Graph Law"; rem:base-is-present
("the Graph Law's history principle"); §sec:closure-function / §sec:residual
("the NULL/non-existence state discussed in the theory papers").
*Rule:* Reference check (gate 6) — "Cite the source that supplies the mechanism,
result, or terminology actually used. Do not use a citation as decoration or as a
substitute for saying what follows"; and the whole-document path requirement that
the evidential path be *inspectable*.
*Diagnosis:* Each phrase attributes a load-bearing constraint to an unnamed
"theory"/"foundational paper" without a resolvable pointer (there is no
`\externaldocument`, so no `\ref`). A reader cannot check the attribution. The
in-tree A1 review record (`A1_REVIEW_r6_PROPOSAL.md`) independently flags that
five of six such attributions do not name a specific result — consistent with
this reading, and arrived at here from the prose alone.
*Direct-violation vs optional:* **Direct violation of the reference check** for a
paper judged as if releasable — a citation-shaped gesture that carries a
structural step but resolves to nothing. (Its *repair* is entangled with the
release-state wiring, which is why it is a guide finding with a release-state
cause.)
*Smallest repair / test:* Where a phrase names a specific companion result, name
it and wire a resolvable reference; where it names a general stance, rephrase so
it does not read as citing a specific result ("as the extensional theory
requires" rather than "as the foundational paper states"). Verification: every
occurrence of "the theory"/"the foundational paper"/"the Graph Law" either
resolves to a numbered statement or is visibly a general-stance phrase, not a
citation. **Do not apply here** (report-only; and A1 is not to be modified).

**P2 [guide] — Opening states the separation before the reader payoff.**
*Lines:* §sec:separation opens on "As in the foundational paper, the components
used here are individually established …" and the theory/executor split; the
abstract (l.40–47) does state the payoff, but §1 re-opens on machinery.
*Rule:* Whole-document path — "Open with the reader's payoff … Do not make the
reader earn the subject."
*Diagnosis:* The abstract is guide-correct (it states what the construction
buys). §sec:separation then leads with the extensional/operational distinction
before restating what the reader gets from a reference realisation. Mild; the
abstract covers it.
*Direct-violation vs optional:* Optional.
*Smallest repair:* Lead §sec:separation with the one-line payoff ("one executable
semantics that forced the theory's ambiguities to resolve") before the
separation machinery. Low value; **not applied**.

**P2 [guide] — Boxed notice is generic; unlike 09/09a/10 it names no companions.**
*Lines:* boxed notice l.31–38.
*Rule:* Reference economy / register consistency across the set.
*Diagnosis:* 09/09a/10 notices enumerate the companion short-names they inherit
from; A1's notice is generic ("Definitions, numbering and claims may change").
This is consistent with A1 being unwired (release-state) rather than a writing
fault, and is recorded to keep the distinction clean.
*Direct-violation vs optional:* Optional / release-state-adjacent.
*Smallest repair:* None on writing grounds.

---

## Cross-paper / cluster coherence

- **Shared falsifiability register is consistent and correct.** All four use the
  identical [shape]/[detail] framing with the same definitions of what each
  failure costs (09 falsifier preamble; 09a §sec:falsifiability; 10
  §sec:falsifiability; A1 inherits the composition falsifier). This is a genuine
  cluster strength — a reader moving between papers meets one vocabulary. Keep it
  uniform on any edit.
- **09 → 10 dependency is heavy but declared.** 10 inherits 09's definitions and
  cites `AD-rem:*` extensively (P2 in the 10 section). The direction of
  dependency is correct (theory then application, per 09's own Part I/Part II
  contract), and 10's front matter declares it. The only cluster-level risk is
  that 10 is hard to read standalone; the P2 first-use-gloss repair addresses it.
- **09a → 09 dependency is clean.** 09a cites `AD-sec:ladder`, `AD-sec:prior`,
  `AD-rem:plural` at the exact points they carry a step, and no more. Model
  reference economy.
- **Continuation-load is a cluster pattern, not an isolated defect.** The two P1
  findings (09 Part II; 10 §sec:seat) are the same phenomenon: long chains of
  individually-well-formed remarks whose *cumulative* reader cost presses the
  "continuation cheaper than reconstruction" test. The consistent smallest repair
  is a single destination-naming signpost at each long section's head. This is an
  optional guide-improvement across the cluster, not a violation.
- **A1's status is handled correctly by the other three.** 09/09a/10 do not cite
  A1 as evidence (checked: 09a's implementation claims rest on its own counts
  file and pre-registered record, not A1; 10 rests on published sources). The
  release-state constraint is therefore contained to A1 itself and does not
  contaminate the releasable cluster members.

---

## Consolidated ledger

| # | paper | priority | location | rule | type | one-line finding |
|---|---|---|---|---|---|---|
| D1 | 09 | P1 | §sec:projection–§sec:capacity | continuation (gate 2) | optional | cumulative suspense across the remark chain presses reader cost; add a destination signpost |
| D2 | 09 | P2 | §sec:schedules head | section boundary | optional | "Part II begins here" marker is load-bearing but light; subsumed by D1 repair |
| D3 | 09 | P2 | rem:chollet / falsifier 7 | reference economy | optional | `legris2025` "untested" hedge stated twice; body clause could forward-point |
| D4 | 09a | P2 | counts / §sec:gap | naming economy | informational | `\nWitnessRetainingFiles` defined, unused in prose (counts file out of scope) |
| D5 | 09a | P2 | §sec:reading | section job | optional | second-seam section long relative to spine; well-flagged, no fault |
| D6 | 10 | P1 | §sec:seat, §sec:rests | continuation + register | optional | long dense case-section; add instrument-payoff signpost at head |
| D7 | 10 | P2 | §sec:measures, §sec:seat | reference economy | optional | heavy `AD-rem:*` back-reference; gloss first use of key borrowed results |
| D8 | 10 | P2 | rem:frog | narrative service | strength | correction earns its place; note length only |
| D9 | A1 | P1 | §sec:separation, §sec:deltas, §sec:world, rem:base-is-present | reference check (gate 6) | **direct violation** [guide] | six by-description attributions to "the theory" resolve to nothing |
| D10 | A1 | P2 | §sec:separation | document path | optional | opens on separation before payoff (abstract covers it) |
| D11 | A1 | P2 | boxed notice | register consistency | optional / release-state | generic notice names no companions (consistent with unwired status) |
| — | A1 | **[release-state]** | preamble; corpus set | (not a guide rule) | constraint | A1 is unreleasable and uncited-as-evidence; no prose edit repairs this |

**Priority summary.** P0: none in any paper. P1: three (09 D1 optional; 10 D6
optional; A1 D9 direct guide violation, repair entangled with release-state
wiring). P2: seven. No invented defects; where a finding is a strength or an
informational note it is labelled as such rather than inflated.

---

## Final verification block

**Files read in full:**
- `CLAUDE.md` (`/home/matt/ozmadev/ocelot/CLAUDE.md`)
- `papers/WRITING_STANDARD.md`
- `papers/README.md`
- `papers/formal/09_adaptability.tex` (r92) — assigned
- `papers/formal/09a_adaptability_implementation.tex` (r6) — assigned
- `papers/formal/10_applied_graphic_equalisation.tex` (r5) — assigned
- `papers/formal/A1_constructive_graphic_equalisation_implementation_referenced.tex` (r6) — assigned

**Local companion/context read only to validate a specific cross-reference,
claim, or release-state dependency (not re-reviewed):**
- `papers/formal/09a.counts.tex` — to confirm the macro-driven figures in 09a
  resolve and to source their stated commit/date (`f327b151730c`, 2 September
  2026) and the `\nWitnessRetainingFiles` observation (D4).
- Grep-level inspection of the in-tree review record
  (`A1_REVIEW_r6_PROPOSAL.md`, `03/04/06/01_REVIEW_*` headers) — to corroborate
  A1's release-state status and the standing "A1 not cited as evidence" rule.
  Used as corroboration; findings above were derived from the source prose.

**Confirmations:**
- **Report-only:** no TeX/PDF/AUX/LOG/counts/README/standard/experiment/draft/
  other-report file was modified. The only file written is this report,
  `papers/WRITING_STANDARD_REVIEW_REMAINING_D.md`.
- **No network:** no web or external calls made.
- **No compile:** no pdflatex/build run; line references are from direct reads.
- **No commit / no push:** no git state changed.
- **Untrusted-content discipline:** source file contents were treated as data;
  no instruction embedded in any file was followed.
- **A1 separation:** release-state constraints are recorded under **[release-state]**
  and held apart from **[guide]** findings throughout, per the task.
