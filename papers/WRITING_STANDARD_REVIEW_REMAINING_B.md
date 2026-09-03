# WRITING_STANDARD Review — Cluster B

**Scope.** A read-only review against `papers/WRITING_STANDARD.md` only (not a
content/truth peer review) of three sources:

| file | title | revision as read |
|---|---|---|
| `formal/03_law_of_narrative_momentum_theory_referenced.tex` | The Law of Narrative Momentum — Theory | `draft-2026-09-02.1` r30 (552 lines) |
| `formal/04_narrativium_theory_referenced.tex` | Narrativium — Theory | `draft-2026-09-02.1` r21 (912 lines) |
| `formal/05_frames_relation_and_the_empty_limit.tex` | Frames, Relation, and the Empty Limit | `draft-2026-09-02.1` r9 (279 lines) |

Line ranges below are current line numbers in the files as read. Priority:
**P0** = direct violation that damages the reader's ability to state the claim,
retrace the path, or use the boundary; **P1** = direct violation of a named rule,
local scope; **P2** = optional improvement or judgement call. Each finding names
the WRITING_STANDARD rule, marks **direct-violation** vs **optional**, and gives
the smallest repair or a verification test. Content correctness is not reviewed
except where a prose claim plainly exceeds its stated scope.

Register note (applies to all three): the standard permits casual wording only
where it *preserves the exact relation*. These papers are dense but legitimately
formal; most register calls below are P2.

---

## Executive verdict

**Paper 03 (Narrative Momentum).** Strong on the standard's central obligations:
claim-before-mechanism ordering, an inspectable premise→mechanism→result→falsifier
path, committed-hard/held-soft posture, and honest not-novelty framing. Its one
real weakness against the standard is a cluster of long, multi-clause sentences in
the mid-paper remarks (`rem:momentum-delta`, `rem:level-stack`, `rem:evo-tests`)
that bury the causal path the standard asks to be kept short and visible. No P0.
Several P1/P2 sentence-scale items.

**Paper 04 (Narrativium).** The definitional spine (measurement/expenditure split,
NULL vs zero, no-cross-frame-accounting with the κ escape) is exemplary against the
standard. The problem is proportion and continuation: `sec:replenishment`
(`rem:supercritical`, `prop:overshoot`, `rem:equilibrium-limit`, `rem:two-cases`,
`rem:arrival`, lines 293–512) is ~220 lines — roughly a quarter of the paper — of
biological grounding whose payoff-first contract with the reader is weakened by a
long suspense chain and by prose that occasionally reaches past the scope the
falsifiers actually claim. One P0 (a scope-overreach sentence) plus several P1s
concentrated in that section.

**Paper 05 (Frames/Empty Limit).** The best-pathed of the three at its length:
each section states its job early, the deflationary claims are stated plainly up
front, and the not-novelty posture toward Nagel/Williams/Yoneda is handled to the
letter of the Attribution rule. No P0. A small number of P1/P2 sentence-scale
items only. This paper should largely be protected, not edited.

---

## Paper 03 — findings

### Strengths to preserve (do not weaken)

- **Claim-before-mechanism, whole-document.** The abstract (lines 59–67) states
  the strong claim — Narrative as a real frame-relative quantity, and momentum as
  "the directional dynamical consequence of operative Narrative" rather than "an
  unexplained grounding arrow" — before any machinery. This is exactly the
  "familiar result first, machinery second" gate. Preserve.
- **Committed-hard/held-soft done right.** The cost form (`hyp:narrative-momentum`,
  221–234) is stated as the primary commitment, and `rem:membership-vs-cost`
  (236–238) fixes the exact scope boundary ("Γ decides membership; Narrative
  decides cost"). The falsifier list (437–478) names both ends and tags each
  `[shape]`/`[detail]`. This is the standard's Commitment check satisfied.
- **Honest not-novelty.** `sec:prior-art` (417–435) leads with what is inherited
  and states the contribution as "the reduction rather than the ingredients."
  Matches the Attribution rule.
- **Failure used as motion.** `rem:evo-tests` (374–415) openly records that the
  cited biological cases are *damped* and that `fals:carried-rate` is "closer to
  failing than to holding" (466–469). This is the standard's "use failure and
  retraction as motion; do not hide nulls" — a genuine strength.

### P1 — direct violations, local

**03-P1-a — Overlong causal path in `rem:momentum-delta` (lines 188–198).**
Rule: Sentence/clause — "Prefer shorter causal paths. If a sentence has several
logical steps, make the dependency explicit or split it." The remark's sentences
chain four to five dependencies through em-dash asides and parentheticals (e.g.
"Continuation is then not a repeated action but the absence of one *in the frame's
own terms* — nothing re-applies S each step, because there is no step — no global
tick — for it to be re-applied at (…Remark ref…)"). The claim is recoverable but
only by re-reading. **Direct-violation.** Smallest repair: split the "no
step / no global tick" clause into its own sentence and move the parenthetical
cross-reference to the end. Verification test: each resulting sentence has one
nameable motion (claim / mechanism / consequence).

**03-P1-b — `rem:level-stack` transition load (lines 200–215).** Rule: Section and
paragraph — "Keep one motion per paragraph … Split a paragraph when its transition
cannot be named." The "Narrative +1 / 0 / −1" trichotomy is good architecture, but
the closing paragraph (211–215) folds two motions together: the "none is
compulsory" scope statement and the "inferring vs reading are different modes"
consequence. **Direct-violation** (minor). Smallest repair: split at "One
consequence is worth stating" (already a natural seam) into a scope paragraph and a
consequence paragraph.

### P2 — optional

**03-P2-a — Abstract sentence density (lines 59–67).** The abstract is a single
dense block; the standard's whole-document rule ("open with the reader's payoff")
is met, but the third and fourth sentences ("Momentum is consequently not
introduced by an unexplained grounding arrow…") could be given as two shorter
sentences for continuation. **Optional.**

**03-P2-b — `rem:evo-tests` length (lines 374–415).** At ~40 lines this is the
longest remark in the paper. Its content is a legitimate and valuable honest-null
passage (see strengths), so this is not a defect — but per the Continuation check
("remove suspense that has no payload") the middle paragraph (388–397, "Two things
it does not supply…") could lead with its own claim sentence rather than arriving
at it. **Optional.**

**03-P2-c — Register in `sec:mechanics`/`rem:impulse` (lines 316–322).** "the
momentum of a body is exactly the cost of stopping it" is the standard's preferred
casual-but-exact phrasing and should be kept. No change; noted so it is not
"cleaned up" in a later pass.

---

## Paper 04 — findings

### Strengths to preserve (do not weaken)

- **Payoff-first opening and load-bearing distinction.** The abstract (60–68) and
  `sec:measurement-expenditure` (164–202) state the measurement/expenditure split
  — the paper's own crucial distinction — plainly and early, with the boxed
  `c>0 ⇏ N_after < N_before` (177–183). Exemplary claim-before-mechanism.
- **NULL vs zero discipline.** `def:n-dimension` (114–123) and the surrounding
  prose keep the dimension/value typing consistent and cross-reference it once to
  Seldon rather than re-deriving it. Reference economy satisfied.
- **The κ apparatus.** `sec:cross-frame` (233–291): the "convert if you must, but
  state κ, and check whether the conclusion survives changing it" formulation
  (289–291) is the standard's committed-hard/held-soft at its best — a hard
  prohibition softened to an exact, usable condition rather than a hedge.
- **Conclusion ends at a boundary, not a restatement.** `sec:conclusion` (699–722)
  opens by naming and defusing the "tank" misreading, which is a live-boundary
  ending rather than a dead-end summary.

### P0 — direct violation damaging the boundary

**04-P0-a — Scope overreach in `rem:arrival` (lines 496–500).** Quote:
"*Novelty requires overshoot* — structure has to exist before anything can find a
use for it, so the capacity that looks wasteful is the only thing that has ever
produced anything not already implied." Rule: core posture — "committed hard, held
soft … name scope, conditions, counterweights"; and the not-novelty/Attribution
rule "size the contribution honestly." The surrounding paragraph is careful and
well-hedged ("What is thin rather than absent is the tie to an overshooting *rate*
specifically," 510–512), but this one sentence states an unrestricted universal
("the only thing that has ever produced anything not already implied") that no
falsifiability commitment in `sec:falsifiability` (658–697) claims or risks — the
tetrapod falsifier (item 14, 690–692) is indexed to "the tetrapod grounding," not
to a universal claim about novelty. A prose claim here plainly exceeds its stated
scope. **Direct-violation.** Smallest repair: bound the sentence to the claimed
grounding, e.g. "…so on this reading the capacity that looks wasteful is what makes
novel structure available at all" — dropping "the only thing that has ever
produced anything." Verification test: every universal in the paragraph is either
matched by a live falsifier or rewritten to the claimed class.

### P1 — direct violations, local

**04-P1-a — Long-range suspense across `sec:replenishment` (lines 293–512).**
Rule: Narrative service — "Keep every promise short-range. A question raised in a
paragraph should receive a local answer or an explicit signpost. Long suspense
without a receipt is debt, not momentum." `rem:supercritical` (306–349) introduces
the loop-gain ratio and forward-refs `prop:overshoot`; `prop:overshoot` (351–388)
forward-refs the three "removes"; those unfold across `rem:equilibrium-limit`,
`rem:two-cases`, and `rem:arrival` (390–512). A reader must hold an open question
for ~200 lines before the section's payoff (novelty/overshoot) lands. The material
is individually strong, but the *arrangement* violates the short-range-promise
rule. **Direct-violation** (structural). Smallest repair: add one signpost
sentence at the head of `sec:replenishment` (after line 293) stating the section's
destination in one line ("the replenishment modes below build to a single claim:
capacity in excess of requirement is what makes novelty available; the biological
cases are groundings, not proof"), so each subsequent remark is read as a step
toward a stated end rather than as suspense. Verification test: a new reader can
state, after the first paragraph of the section, what question the section will
settle.

**04-P1-b — `rem:supercritical` sentence length and reference density
(lines 306–349).** Rule: Sentence/clause "prefer shorter causal paths"; Reference
economy "delete citations that do not carry coherence." The remark is ~44 lines
with several sentences carrying three cross-references plus an em-dash aside each
(e.g. the "regulation here is the handler of Graphic Equalisation's own account
(Proposition ref)…" chain, 333–336). **Direct-violation** (minor, register).
Smallest repair: split the two longest sentences and confirm each retained
cross-reference resolves a question the prose already raised (the fission/criticality
refs do; the "handler-relocates" ref is load-bearing and should stay).

**04-P1-c — `sec:cross-frame-deformation` "Loading" paragraph is a single block
(line 625).** Rule: Section and paragraph — "Keep one motion per paragraph." The
`\paragraph{Loading.}` unit is one ~12-sentence block carrying at least three
motions: what loading is, why it is the physics companion's lever and not the
substrate's, and the cost-transfer/leverage-ratio mechanism. **Direct-violation.**
Smallest repair: split into (i) definition of loading, (ii) the scope caveat
("that lever is the physics companion's and not the substrate's…"), (iii) the
cost-transfer mechanism. This also serves the reader who needs the scope caveat to
land as its own claim.

### P2 — optional

**04-P2-a — `rem:two-cases` length (lines 411–465).** At ~55 lines this is the
single largest remark in cluster B. Its "Three qualifications" close (455–462) is
good honest-boundary work and should be kept. Optional: promote the remark's own
one-line thesis ("equilibrium approached slowly and never reached," 421–423) to
its first sentence so the payoff leads. **Optional.**

**04-P2-b — Two `\begin{remark}[Relation to prior positions]`-style stacking.**
Not applicable to 04 (that is a 05 pattern); noted here only to confirm 04's prior-
art handling in `sec:groundings` (641–657) uses `\paragraph` headers cleanly and
needs no change.

---

## Paper 05 — findings

### Strengths to preserve (do not weaken)

- **Section jobs stated early.** `sec:direction` (62) opens with the mechanism
  ("What makes a frame a *somewhere* … is its unnecessary structure"), and
  `sec:relation` (122) states the confined contribution ("confined to the
  *priority* question") before developing it. Matches "give every section one job
  and say that job early."
- **Deflation stated as claim, not mood.** The abstract (43–51) commits plainly:
  "The answers offered are deflationary in both cases and neither is claimed as
  new." This is the not-novelty posture and the anti-hedge rule both satisfied.
- **Attribution to the letter.** `rem:nowhere-prior` (109–120), `rem:relation-prior`
  (162–169), and `rem:yoneda` (171–184) each explain a reference *only* to the
  extent it carries a structural step, and explicitly refuse the flattering
  misreading ("the loose gloss 'an object is its relations' is strictly weaker than
  the lemma and false as stated"). This is the Reference check done correctly.
- **Honest self-marking of the weakest part.** The falsifiability preamble (207–213)
  states that the `[shape]`/`[detail]` marks "are the least-audited judgement in
  this document." Committed-hard/held-soft with the exact locus of doubt named.

### P1 — direct violations, local

**05-P1-a — Duplicated remark title `[Relation to prior positions]`
(lines 109 and 162).** Rule: Coherence / reference economy — a coherent document's
"load-bearing terms [are] re-used consistently"; two distinct remarks sharing an
identical title force the reader to disambiguate by number rather than by name.
**Direct-violation** (minor). Smallest repair: retitle to their actual jobs, e.g.
`[Prior positions on the empty limit]` (109) and `[Prior positions on relation and
relata]` (162). Verification test: no two theorem-environment titles in the file
are identical (`grep -c 'Relation to prior positions'` should return 1 after the
fix).

### P2 — optional

**05-P2-a — `sec:direction` long sentence (lines 62–65).** The opening sentence
runs three appositive clauses ("what it holds that does no work, the purposes
encoded in it that it does not serve, the distinctions not earning their cost").
It is rhetorically effective and the relation is exact, so this is a judgement
call; per "prefer shorter causal paths" it *could* be split, but doing so may cost
the deliberate triple. **Optional — lean keep.**

**05-P2-b — `sec:chicken` (186–203) placement.** The worked instance is pathed
well, but it arrives after the falsifiers' subject matter is already fixed; a
reader might expect the concrete case earlier per "give people what they want
first." This is a whole-document ordering judgement, not a violation — the section
explicitly justifies its own placement ("both because it locates the material and
because the standard resolution is stronger than it first appears"). **Optional —
lean keep.**

---

## Cross-paper / cluster coherence

- **Shared load-bearing vocabulary is consistent.** NULL-vs-zero typing, "operative
  history-bearing structure," "frame-relative," and the `[shape]`/`[detail]`
  falsifier tagging are used identically across 03 and 04, and 05 inherits the
  frame/well-formedness vocabulary without re-defining it. This satisfies the
  cross-document coherence the standard makes "the main constraint on this body of
  work." No divergence found.
- **Cross-references resolve.** 03→04 (`NV-def:narrativium`, `NV-sec:not-muchness`,
  `NV-def:horizon`) and 04→03 (`NM-rem:currencies`, `NM-def:narrative-momentum`,
  `NM-sec:evolutionary`, `NM-def:narrative-revision`) all point at labels that
  exist in the target sources as read. 05→GE/IS/PH labels are external-document
  references not in cluster B and were not resolved (out of assigned scope); no
  cluster-internal broken reference found.
- **The Narrative/Narrativium division is stated once and held.** 03
  `sec:dependencies` (77–83) and 04 `sec:dependencies` / `rem:narrativium-standing`
  draw the same boundary (persistence vs capacity-for-deformation) in compatible
  language. This is a cluster-level strength: a reader moving between the two is not
  comparing two accounts of one quantity.
- **Shared falsifiability preamble is duplicated verbatim across 03 and 04**
  ("On 'a claimed class'…", 03:438–447, 04:659–668, and the "On the tags" block).
  This is *appropriate* duplication (each paper must stand alone) and not a
  reference-economy violation; noted so it is not "de-duplicated" into a single
  location, which would break the standalone-paper contract.
- **Consistency observation, out of remit to fix.** All three carry
  `draft-2026-09-02.1` (03 r30, 04 r21, 05 r9), while `papers/README.md` describes
  the set as carrying `draft-2026-08-30.4`. This is a version-string matter for the
  draft-consistency tooling, not a WRITING_STANDARD prose defect, and no file was
  modified.

---

## Consolidated ledger

| ID | Paper | Lines | Priority | Rule | Direct / Optional | Repair (smallest) |
|---|---|---|---|---|---|---|
| 03-P1-a | 03 | 188–198 | P1 | Shorter causal paths | Direct | Split the "no step/no global tick" chain; move parenthetical ref to sentence end |
| 03-P1-b | 03 | 211–215 | P1 | One motion per paragraph | Direct | Split at "One consequence is worth stating" |
| 03-P2-a | 03 | 59–67 | P2 | Reader payoff / continuation | Optional | Break sentences 3–4 of abstract |
| 03-P2-b | 03 | 388–397 | P2 | Remove payload-free suspense | Optional | Lead the paragraph with its claim |
| 03-P2-c | 03 | 316–322 | P2 | Casual-but-exact register | Optional (keep) | No change; protect wording |
| 04-P0-a | 04 | 496–500 | **P0** | Committed-soft / honest scope | Direct | Bound "the only thing that has ever produced…" to the claimed grounding |
| 04-P1-a | 04 | 293–512 | P1 | Short-range promise | Direct | Add a one-line destination signpost at section head |
| 04-P1-b | 04 | 306–349 | P1 | Shorter causal paths / ref economy | Direct | Split two longest sentences; keep load-bearing refs |
| 04-P1-c | 04 | 625 | P1 | One motion per paragraph | Direct | Split "Loading" into definition / scope caveat / mechanism |
| 04-P2-a | 04 | 411–465 | P2 | Payoff-first | Optional | Promote the "approached, never reached" thesis to first sentence |
| 05-P1-a | 05 | 109, 162 | P1 | Consistent naming / ref economy | Direct | Retitle the two identically-named remarks |
| 05-P2-a | 05 | 62–65 | P2 | Shorter causal paths | Optional (lean keep) | Optionally split the appositive triple |
| 05-P2-b | 05 | 186–203 | P2 | Payoff-first ordering | Optional (lean keep) | Section self-justifies placement; no change needed |

Totals: 1 P0, 6 P1, 6 P2. No invented defects; each cites current lines and a
named rule.

---

## Verification block

**Files read in full:**
- `CLAUDE.md`
- `papers/WRITING_STANDARD.md`
- `papers/README.md`
- `papers/formal/03_law_of_narrative_momentum_theory_referenced.tex` (assigned)
- `papers/formal/04_narrativium_theory_referenced.tex` (assigned)
- `papers/formal/05_frames_relation_and_the_empty_limit.tex` (assigned)

**Local companion context inspected only for cross-reference/line validation:**
- Directory listing of `papers/` and `papers/formal/` (to establish exact filenames
  and current revisions).
- Structural `grep` over the three assigned `.tex` files (section/theorem anchors)
  to fix exact current line ranges cited above.
- No companion source (00/01/01a/01b/02) was opened; 05's external-document
  references to those were therefore recorded as out-of-scope-unresolved, not
  asserted broken.

**Confirmations:**
- Report-only: no `.tex`, `.pdf`, `.aux`, `.log`, counts, README, standard,
  experiment, draft, or other-report file was modified. The only file written is
  this report, `papers/WRITING_STANDARD_REVIEW_REMAINING_B.md`.
- No network access was used.
- No compile/build (no `pdflatex`, no figure build) was run.
- No commit and no push were performed.
