# WRITING_STANDARD Review — Cluster C (Papers 06, 07, 08)

## Scope and current revisions

Read-only review against `papers/WRITING_STANDARD.md` (the shared communication
standard) and `papers/README.md`, with `CLAUDE.md` read for project context.
This is a **writing-standard** review, not a content/truth peer review:
correctness is examined only where a prose claim plainly exceeds its own stated
scope.

Sources reviewed, at the revisions present on disk at review time:

| file | title | draft / revision |
|---|---|---|
| `formal/06_assessing_an_account_of_this_kind.tex` | Assessing an Account of This Kind | `draft-2026-09-02.1` r27 (1124 lines) |
| `formal/07_causal_attitude_networks_on_the_substrate.tex` | Causal Attitude Networks on the Substrate | `draft-2026-09-02.1` r2 (359 lines) |
| `formal/08_certified_answers_as_an_audit.tex` | Certified Answers as an Audit | `draft-2026-09-02.1` r2 (271 lines) |

Note (context, not a defect against these files): `papers/README.md` still
describes "twelve" papers on a single `draft-2026-08-30.4` string, lists 06 with
a different subtitle, and does not list 07 or 08. Cluster C is on
`draft-2026-09-02.1` — i.e. the README's version/inventory prose is stale
relative to this cluster. Reconciling the README is out of scope for this
report (no README edit permitted) and is flagged here only so the cross-drift is
on record.

Priorities: **P0** = direct violation that damages reader/claim/path coherence
or a hard commitment; **P1** = direct violation, localized, cheaper to fix than
to leave; **P2** = optional improvement or minor register/economy point.
Every finding names the rule, quotes current text, and gives the smallest
repair or a verification test. "Direct-violation" vs "optional" is marked on
each.

---

## Executive verdict per paper

**Paper 06 — Assessing an Account of This Kind.** The strongest and most
self-consistent application of the standard in the cluster: it *is* the paper on
holding-committed-hard-held-soft, and it practises what it argues (an explicit
`sec:own-commitments`, apologies converted to exposures, nulls reported as
motion, honest not-novelty posture). Its defects are almost all local
consequences of its own density: one genuinely broken abstract sentence (P0),
several paragraphs where a single-motion rule is violated by stacking three
withdrawals of the same claim, and a few reference-economy lapses where
`Graphic Equalisation's definition of well-formedness (Definition~\ref{...})` is
spelled out many times over. No hard-commitment or honesty defect found; the
posture is exemplary. **Verdict: accept with local repairs; one P0.**

**Paper 07 — Causal Attitude Networks on the Substrate.** A model report whose
architecture is clear and whose falsifiability section is a strong worked
example of the "retraction as motion" rule (two commitments reported as *fired*
and replaced in place, not deleted). The main writing-standard risk is
reader-path load: the "record of DATE" framing is load-bearing and correct, but
several remarks open on mechanism/measurement before the claim they settle is
stated, and the abstract front-loads five findings at once. **Verdict: accept
with local repairs; no P0.**

**Paper 08 — Certified Answers as an Audit.** The cleanest reader-path of the
three: claim-first, coverage stated as the honest headline in the abstract and
again in `sec:not`, each conviction self-contained and re-derivable. The
standard is well served throughout. Findings are minor — one abstract sentence
that could read as a coverage boast if quoted out of context (already
counter-weighted, so P2), and small economy items. **Verdict: accept; no P0, no
P1 that is a clear direct violation.**

---

## Paper 06 — findings

### P0

**06-P0-1 — Broken abstract sentence (path check; single-motion; register).**
Lines 52–54:
> "It ends by holding itself to the same standard, with three commitments of its
> own, a paper arguing about what an account may be held to being subject to the
> same."

Rule: WRITING_STANDARD *Revision gate 1 (Path check)* and *Sentence and clause*
("Keep the agent, action, and consequence visible … split it"). Diagnosis: the
trailing clause "a paper arguing about what an account may be held to being
subject to the same" is a dangling absolute that restates the first clause; the
sentence has two motions welded with a comma splice and the second is
ungrammatical ("held to being subject"). A reader cannot restate it. This is the
opening payoff paragraph, so the cost is high. **Direct violation.**
Smallest repair: delete the trailing clause — the sentence is complete and
correct at "…with three commitments of its own." (Verified downstream:
`sec:own-commitments`, lines 1055–1071, contains exactly three `\item`s, so
"three commitments of its own" is accurate and self-sufficient.)

### P1

**06-P1-1 — Triple-stacked withdrawal buries the claim (single motion per
paragraph; continuation check).** Lines 70–83 (the second paragraph of
`sec:risk`, "This account can say something sharper…"). The paragraph makes a
claim, then withdraws the strong reading ("that step is too quick"), then states
"The claim that survives is narrower," then again "the strong reading does not
hold either," then a third time "What survives is narrower." Rule: *Section and
paragraph* ("Keep one motion per paragraph … Split a paragraph when its
transition cannot be named") and *Narrative* ("Withhold mechanism, never the
claim"). Diagnosis: three successive narrowings of the same claim in one
paragraph make the reader hold a moving target; the surviving claim ("the
load-bearing part that could have been otherwise is falsifiable and non-empty")
arrives only after being approached twice. **Direct violation (of single-motion
rule); repair is optional in form.** Smallest repair: split after "does a great
deal of work." into a second paragraph that states the surviving claim once, and
delete the redundant "What survives is narrower." at line 78 (it duplicates the
same phrase at line 74). Verification test: name the transition between each
retained sentence; if two adjacent sentences both carry "the surviving claim is
narrower," one is redundant.

**06-P1-2 — Reference-economy: the well-formedness definition is re-cited in
full too often (Reference check; reference/naming economy).** The exact phrase
"Graphic Equalisation's definition of well-formedness
(Definition~\ref{GE-def:well-formed})" (or a near-identical form) recurs at
lines ~74, ~87, ~166, ~600 (`sec:estimate`), ~848 (`sec:question`), and
elsewhere. Rule: *Attribution, references, and novelty* ("Do not explain a
reference merely because it is a reference") and Revision gate 6. Diagnosis:
after the term is established, the full parenthetical citation is reference
padding; the load-bearing move is the phrase "prices as idle / at the top
level," not the re-pointer. **Optional (economy), not a coherence break.**
Smallest repair: cite `Definition~\ref{GE-def:well-formed}` in full on first use
per section; thereafter use the short form ("well-formedness prices this as
idle") without the parenthetical. Verification test: count occurrences of
`GE-def:well-formed`; each after the first in a given section should carry new
conceptual work or be shortened.

**06-P1-3 — `sec:estimate` is very long and changes job mid-section (Section and
paragraph: one job, said early; path check).** `sec:estimate` runs lines
566–741 and moves through: the interval and its width; the no-apology rule; the
refusal of the strong low-end phrasing; three considerations lowering the
weight; the Axiom-based argument that the upper bound is a claim about other
frames; the built-then-mattered order; the self-direction/self-implementation
distinction; the trajectory-reading flip; three bounding results; three debts.
Rule: *Section and paragraph* ("Give every section one job and say that job
early"). Diagnosis: this is at least three jobs (the author's estimate; the
no-apology principle; the self-direction audit) under one heading, and the
no-apology material (lines ~575–599) is a general prose rule, not part of the
estimate. **Optional (structural), not a truth defect.** Smallest repair: lift
the no-apology block (lines ~575–599) into its own short section or fold it into
`sec:modal` (which is the other "prose-discipline" section); it interrupts the
estimate's path. Verification test: state the single job of `sec:estimate` in
one clause — if the no-apology rule is not part of it, it belongs elsewhere.

### P2

**06-P2-1 — "It ends by holding itself…" and later self-description (register;
economy).** Abstract line 52 and the head of `sec:own-commitments` (line 1051)
both open "A paper arguing about what an account…". Minor echo; the second is
fine, the abstract's is the P0 above. No separate repair needed once 06-P0-1 is
fixed. **Optional.**

**06-P2-2 — Long causal chains in `sec:question` (Sentence and clause: prefer
shorter causal paths).** E.g. lines ~848–856 ("The most well-formed question is
one that asks and receives nothing. It costs a single write; it returns no
structure … which is Graphic Equalisation's definition of well-formedness … at
its limit, and the same shape as this programme's observation that the empty
limit is not a frame…"). Rule: *Sentence and clause*. Diagnosis: three logical
steps chained through two subordinate "which" clauses; the relation is
recoverable but dense. **Optional.** Repair: split at "at its limit," making the
"empty limit / dissolution" comparison its own sentence.

**Strengths to preserve (do not weaken):**
- `sec:own-commitments` (1051–1099) is a model of *committed hard, held soft*:
  three `[shape]`/`[detail]`-tagged falsifiers, two acknowledged as prospective,
  three terms flagged as not-yet-operationalised, and the confound named. This
  is exactly Revision gate 4.
- The no-apology passage (575–599) correctly converts apology into *exposure*
  and states the translation — a direct realisation of the standard's "Do not
  apologise. Ever." with the admissible alternative given. Keep.
- `sec:contribution` (232–318) leads with "The claim is explanation and
  unification, not discovery" — honest not-novelty posture, Revision gate 5.
  Keep the up-front placement.
- Nulls are reported as motion throughout (`most framework-motivated changes
  made no difference`, the transfer-audit removals) rather than buried —
  standard's *narrative* rule 5. Keep.

---

## Paper 07 — findings

### P1

**07-P1-1 — Abstract front-loads five findings before the reader holds the claim
(Whole document: reader payoff first; continuation check).** Lines 42–57. The
abstract states, in sequence, the CAN model, the two reimplementations, "Five
findings are reported and two of them correct this paper's own earlier
revision," then alignment, oscillation, performance, and the two predictions.
Rule: *Whole document* ("Open with the reader's payoff … Do not make the reader
earn the subject") and Revision gate 2. Diagnosis: the payoff (what moved onto
the substrate and what that buys) is present but competes with a five-item
inventory in one paragraph; a reader cannot hold five findings plus two
self-corrections at once. **Optional/structural; not a direct coherence break
because each item is individually clear.** Smallest repair: lead with the one-
line claim ("the model was moved from hosted solver to native graph rules, and
the audit corrected two of this paper's own earlier findings"), then list the
five as the body does. Verification test: can a new reader, after the abstract
alone, state the paper's single headline? If they list five, compress.

**07-P1-2 — `rem:hosted` and `rem:native` open on mechanism before the claim
(claim-before-mechanism ordering).** Lines 88–99 (`rem:hosted`) open "Fifteen
rules written against the network were inert, and the obvious diagnosis … was
not the reason." The claim the remark settles — *there was no term surface for
the dynamics* — arrives at line ~91. Rule: *Narrative* rule 3 ("Withhold
mechanism, never the claim") and *Section and paragraph* ("say that job early").
Diagnosis: the remark's job (why fifteen rules did nothing, and what that shows
about "moved vs hosted") is delivered after the count and the ruled-out
diagnosis. This is a mild inversion; the reader holds "fifteen inert rules"
before knowing what the remark concludes. **Optional (ordering); the remark
title already carries the claim, which mitigates.** Smallest repair: none
strictly required because the `\begin{remark}[...]` title states the claim
("The hosted stage, and the null that dated within a day"); if tightening, move
"There was no term surface for the dynamics at all" to the first sentence.

### P2

**07-P2-1 — "Record of DATE" repetition (economy) is correct but heavy.** Each
remark opens "\emph{(Record of 13 August 2026.)}" / "(Record of 14 August
2026.)". Rule: reference/naming economy. Diagnosis: this is *load-bearing* (the
paper's whole repair is a dating fix, per the abstract and `sec:moved`), so it
is not padding — but the standard's economy rule still favours stating the
convention once and then dating only where a remark's date differs from the
section's. **Optional; lean toward keeping** given the paper explicitly makes
dating the point ("the defect this revision repairs was a dating one," line
~82). No change required; flagged so a later editor does not "tidy" it away.

**07-P2-2 — `sec:performance` opening hedge vs commitment (committed hard, held
soft).** Line 177 onward: "The natural objection … is that its ground-state
problem is hard." then "And it does not bind, because no exact ground state was
being sought." This is good (condition stated). Minor: the later sentence "The
actionable question was therefore never whether this scales exactly, but how
good the approximation is and when it fails to converge" is strong and correct.
No defect; noted as a **strength** (see below). No repair.

**Strengths to preserve (do not weaken):**
- `sec:falsifiability` (294–339) is the cluster's best example of *retraction as
  motion*: two commitments explicitly marked **fired** and **replaced** in place
  ("This replaces a commitment that fired"), with the superseded wording quoted.
  This is Revision gate 4 and the standard's rule 5 done exactly right. Keep the
  quoted-old-wording form.
- Bounded negatives are stated with exact scope ("complete graphs only,
  $\beta \le 4.0$, $N \le 64$, one initial condition per trial … rather than a
  proof that none exists," lines ~170–174) — *committed hard, held soft* via
  exact range, not fog. Keep.
- Engine findings are attributed to "the machinery rather than to the model"
  (line ~117) — honest arrangement posture. Keep.

---

## Paper 08 — findings

### P1

*(No finding rises to a clear P1 direct violation. The paper's reader-path,
claim ordering, and commitment discipline are compliant. Items below are P2.)*

### P2

**08-P2-1 — Abstract's coverage sentence is safe only because counter-weighted
(commitment check; register).** Lines 46–48:
> "\emph{Coverage is $1.8\%$ and that is the honest headline}: this is not a
> result about how much the system can answer, it is a result about what
> certified answering makes visible…"

Rule: Revision gate 4 (commitment) and *Attribution/novelty* (size the
contribution honestly). Diagnosis: this is actually a **strength** — coverage is
stated as the headline, pre-empting the boast reading. The only P2 note: the
sentence is a comma splice ("…the honest headline: this is not a result…, it is
a result…"). **Optional (register).** Smallest repair: replace the second comma
with a semicolon or "but rather," — "it is not a result about how much the
system can answer; it is a result about what certified answering makes visible."

**08-P2-2 — `rem:zero` states the value as a maxim before the mechanism, which
is correct; minor economy.** Lines 102–112. "An audit claiming three convictions
with airtight proofs … is worth more than one claiming thirty." Good claim-first
ordering. **No repair.** Flagged only as a preservation note.

**08-P2-3 — `sec:convictions` per-item ordering is exemplary (preserve).** Each
conviction is "what the key says, what was certified, where the key's reasoning
goes wrong" (stated at lines 114–117 and followed literally). This is
premise→mechanism→result→boundary at paragraph scale. **No repair.**

**08-P2-4 — Reference economy: the "not circulated with these papers / a reader
may decline to credit" disclaimer (lines 68–72) is stated once and not
repeated** — correct application of "state the record once." Contrast with 06,
which repeats its equivalent disclaimer several times (see 06-P1-2 spirit). No
defect in 08; noted as the positive model.

**Strengths to preserve (do not weaken):**
- Claim-before-mechanism at document scale: `sec:why` establishes *why any
  frontier benchmark must contain errors* (arithmetic, not accusation) before a
  single conviction is shown. Revision gates 1–2. Keep.
- Each of the five convictions is re-derivable from the page (kernel rank,
  sudden-approximation, basis count, theorem parity, grammar + enumeration),
  which the paper explicitly promises at lines ~73–77 and delivers. This is the
  standard's "make the claim's evidential path inspectable." Keep.
- `sec:tierb` ("What was not convicted, and why that section matters more") is
  the honest counter-weight — the not-banked disagreements are the calibration
  that makes the five worth anything. Standard's *committed hard, held soft* and
  rule 5 (residual/retraction as motion). Keep.
- Self-retraction reported, not hidden: the withdrawn physics flag (line ~108,
  `rem:zero`) and the scope note that "no statement about benchmark performance
  is made or implied" (line ~250). Keep.

---

## Cross-paper / cluster coherence

1. **Shared "record is not circulated" disclaimer — three different densities.**
   All three papers carry the same honest move (the engineering record is
   pre-registered but not published with the papers, so figures are assertions a
   reader may decline to credit). 08 states it **once** (lines 68–72) and 07
   states it once with an explicit "not re-disclaimed at each remark" convention
   (`sec:moved`, line ~80). 06 repeats it in multiple sections
   (`sec:implementable`, `sec:turned`, `sec:implementation`, `sec:estimate`,
   `sec:own-commitments` item 3). 07's stated convention is the model; 06 is the
   outlier on reference/naming economy. Recommend 06 adopt 07's "stated once"
   convention. (Consistency/economy — optional.)

2. **`[shape]`/`[detail]` tagging is consistent and correct across the cluster.**
   06 `sec:own-commitments`, 07 `sec:falsifiability`, and 08 `sec:falsifiability`
   all use the same marker semantics and all define them the same way
   ([detail] = revision; [shape] = costs range, still a boundary). No drift
   found. This is a genuine cluster strength — preserve the shared definition
   wording.

3. **Retraction-as-motion is realised most fully in 07 and echoed in 08 and 06.**
   07 fires and replaces two commitments in place; 08 reports a withdrawn flag;
   06 reports transfer-audit removals and the volume/structural reading flip.
   The cluster is coherent on the standard's rule 5 (nulls and corrections as
   motion, not buried). No defect.

4. **Register is uniformly formal-paper-correct.** No apologies, no ceremonial
   padding, no passive-indirection fog found in any of the three. 06 additionally
   *argues* the no-apology rule and applies it; 07 and 08 simply obey it.

---

## Consolidated ledger

| ID | Paper | Priority | Rule | Direct/Optional | Lines | One-line repair |
|---|---|---|---|---|---|---|
| 06-P0-1 | 06 | P0 | Path / single-motion / sentence | Direct | 52–54 | Delete trailing clause after "three commitments of its own." |
| 06-P1-1 | 06 | P1 | Single motion per paragraph | Direct (rule) | 70–83 | Split paragraph; delete duplicate "What survives is narrower." |
| 06-P1-2 | 06 | P1 | Reference economy | Optional | recurring (74,87,166,600,848…) | Short-form the well-formedness citation after first use per section. |
| 06-P1-3 | 06 | P1 | One job per section | Optional | 566–741 | Move no-apology block (575–599) to its own section / into `sec:modal`. |
| 06-P2-1 | 06 | P2 | Register / echo | Optional | 52, 1051 | Resolved by 06-P0-1. |
| 06-P2-2 | 06 | P2 | Shorter causal paths | Optional | ~848–856 | Split at "at its limit,". |
| 07-P1-1 | 07 | P1 | Reader payoff first | Optional | 42–57 | Lead abstract with one-line headline, then the five findings. |
| 07-P1-2 | 07 | P1 | Claim before mechanism | Optional | 88–99 | Move "no term surface" to first sentence (mitigated by remark title). |
| 07-P2-1 | 07 | P2 | Economy | Optional (keep) | per-remark | Keep "Record of DATE"; it is load-bearing. |
| 07-P2-2 | 07 | P2 | Committed-hard-held-soft | — | 177+ | No repair (strength). |
| 08-P2-1 | 08 | P2 | Commitment / register | Optional | 46–48 | Fix comma splice; semicolon between the two "result" clauses. |
| 08-P2-2/3/4 | 08 | P2 | Ordering / economy | — | 102–112, 114–117, 68–72 | No repair (strengths). |

**Totals:** 1 P0 (06), 5 P1 (06×3, 07×2; of these 2 are direct-rule violations
and 3 are optional/structural), remainder P2. No hard-commitment defect, no
honesty/novelty-posture defect, no register (apology/padding) defect found in
any paper.

---

## Verification block

**Files read in full:**
- `CLAUDE.md` (project context)
- `papers/WRITING_STANDARD.md` (the governing standard)
- `papers/README.md` (papers-set context)
- `papers/formal/06_assessing_an_account_of_this_kind.tex` (assigned)
- `papers/formal/07_causal_attitude_networks_on_the_substrate.tex` (assigned)
- `papers/formal/08_certified_answers_as_an_audit.tex` (assigned)

**Local companion context inspected only to validate a specific claim/path
dependency:** none opened beyond the assigned sources; cross-references into
Graphic Equalisation (`GE-…`), the physics companion (`PH-…`), and the mind
companion (`MS-…`) were treated as declared `\externaldocument` labels and were
**not** followed, because no finding in this report turns on their contents —
each finding is decidable from the assigned files alone. The one internal
dependency checked (06 abstract "three commitments of its own" ↔
`sec:own-commitments`) was validated within paper 06 itself (three `\item`s at
lines 1055–1071).

**Line ranges** were anchored against the files as they stand at review time
(06 = 1124 lines, 07 = 359 lines, 08 = 271 lines), via structural grep for
`\section`/`\subsection`/`\begin{remark}`/`\begin{proposition}`/`\paragraph`
and direct reads of the quoted passages. Line numbers for recurring phrases are
marked "~" where approximate.

**Confirmations:**
- **Report-only:** No `.tex`, `.pdf`, `.aux`, `.log`, counts, README, standard,
  experiment, draft, or other-report file was modified. The only file written is
  this report, `papers/WRITING_STANDARD_REVIEW_REMAINING_C.md`.
- **No network:** No web or network access was used.
- **No compile:** No LaTeX/PDF build was run; `06.counts` macros
  (`\countsCommit`, `\nBaselineRed`, etc.) were read as source tokens, not
  expanded.
- **No commit / no push:** No git operation was performed.
- **Untrusted content:** File contents were treated as data; no instruction
  embedded in any source was followed.
