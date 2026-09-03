# Content and accuracy review — `00_is.tex` (r125) and `01_law_of_graphic_equalisation_theory_referenced.tex` (r283)

Scope: a read-only content and accuracy audit, **not** a prose/style review (the
writing-standard review of r123/r281 in `WRITING_STANDARD_REVIEW_00_01.md` already
covers style, and this review does not re-litigate it). No claim is assessed for
ultimate philosophical truth; the audit checks internal logical/ontological
consistency, inter-paper consistency, mathematical/formal accuracy, technical/factual
accuracy against locally available evidence, citation/attribution accuracy, and the
impact of the recent P1/P2 edits that carried 00 from r122→r125 and 01 from
r280→r283. Line ranges are to the current sources at the revisions named. Every
recorded finding cites source text.

Classification legend: **confirmed issue** (defect verifiable from the source),
**internally supported** (the paper's own machinery backs the passage — recorded as a
passed check), **external verification required** (turns on a fact not settleable from
local sources), **no issue**. Severity: **P0** invalidates a core result or the build;
**P1** material accuracy/correctness risk; **P2** bounded correctness ambiguity;
**Note** not a defect.

---

## Executive verdict

**No P0 in either paper.** The core results are internally coherent and the two papers
compose without contradiction on their shared path (00 establishes the bare untyped
graph as a result; 01 begins after it, inheriting graphhood as a result-within-a-
discipline rather than as a postulate, and its ledger accounts for exactly what it adds).
The recent P1/P2 edits (the r122 and r280 review proposals, applied) are content-
preserving and, where checkable, correct — several of them *removed* latent logical
defects (the `rem:funding-category` acyclicity over-claim; the three-way cost-destination
inconsistency; a `prop:prohibition`/economics wording collision; the missing "Order and
time" falsifiers).

The findings below are: two P1 items (one a genuine correctness ambiguity in 01's
ledger about what "one of two unpaid entries" quantifies over; one an
external-verification exposure in 01's central empirical instance that the paper already
flags but that a reader must not mistake for settled). The remainder are P2 bounded
ambiguities and Notes. A substantial block of important checks **passed** and is recorded
so valid structure is not weakened gratuitously.

---

## Part 1 — Internal consistency, paper 00 (`Is`, r125)

### 00-C1 — The three-way separation of claims is consistent with the falsifier list. *(internally supported; no issue; Note)*
Claim checked: 00 separates three claims (determinacy is relational; time/cause/rule/
observer are separable; removal-against-shortest-sufficient is a fair audit —
`sec:claim`, lines 88–93) and the falsifiability section (`sec:falsifiability`, lines
~968–1043) commits to four items "in the order of the three claims … and then the
prediction."
Evidence/chain: item 1 = commitment 1 (relational determinacy, `[shape]`); item 2 =
commitment 2 (separability, `[shape]`); item 3 = the method's-yield claim (`[detail]`);
item 4 = compression-moves-to-graph (`[detail]`). The mapping is exact and the
`[shape]`/`[detail]` tags are internally consistent with the text's own stated
consequences of failure.
Classification/severity: no issue; recorded so the structure is preserved.

### 00-C2 — "Two unpaid entries" is stated consistently *within* 00. *(internally supported; no issue)*
Claim checked: 00 `sec:companions` (lines ~793–802) says Graphic Equalisation's ledger
"carries the admission and two postulates named there — a realisation operator and a
destroy/preserve distinction." Separately the README's set-summary says the account
"carries two unpaid entries, not one — that there is anything, … and that anything
happens."
Evidence/chain: 00 itself does not use the phrase "two unpaid entries"; it refers to
"two postulates" (realisation, destroy/preserve) which are a *different* pair from the
two *unpaid* entries (existence, happening). Within 00 there is no collision: the
postulates are named as postulates, the admission ("things happen") as an admission.
Classification/severity: no issue. But see 01-C3 below, where the "two unpaid entries"
phrase does appear and interacts with a second count.

### 00-C3 — Shannon/Rissanen attribution is accurate and correctly disclaimed. *(internally supported; no issue; Note)*
Claim checked: lines ~299–303 — "`\citet{rissanen1978}` is where it stops being a
preference … `\citet{shannon1948}` supplies that measure and *not* the norm, containing
no model selection, so citing the two together for the norm borrows a name that did not
make the claim."
Evidence/chain: the characterisation is factually correct — Shannon (1948) supplies the
entropy measure and contains no model-selection principle; Rissanen (1978, "Modeling by
shortest data description") is the MDL source. The disclaimer correctly prevents crediting
Shannon with the norm. Bibliography entries (lines ~1070–1090) match: Shannon 1948, *Bell
System Technical Journal* 27:379–423,623–656; Rissanen 1978, *Automatica* 14:465–471.
Classification/severity: no issue; recorded as a citation-accuracy pass.

### 00-C4 — Double-entry / group-of-differences history is internally coherent and self-qualified. *(internally supported; no issue; external verification required for dates)*
Claim checked: `sec:track-record` (lines ~560–650) and `sec:prior` (lines ~840–860):
Pacioli 1494 describes a practice already in use; Farolfi ledger 1299–1300 (`lee1977`) is
read as full double entry; the group-of-differences identification is Ellerman's
(`ellerman1985`, `ellerman2014`); the gap "Pacioli 1494 to Hamilton's ordered couples of
1837" is ~3.5 centuries; Yamey (1949) is the counterweight and Sangster (2016) sharpens
it; Arya et al. (`arya2000`, `aryagraph2000`) reach a directed-graph reading independently.
Evidence/chain: the internal logic is careful and self-consistent — 00 explicitly
disclaims the minimality reading ("`\citeauthor{ellerman2014}` refutes the obvious one")
and states the illustration/evidence split. The De Morgan (1869) and Cayley (1894) detail
is used to *weaken* the clean two-restriction gap honestly.
Classification/severity: no issue as *internal* reasoning. The concrete dates (1299–1300
Farolfi, 1837 Hamilton ordered couples, Cayley's 1894 double-entry pamphlet, "three
decades to publish") are **external verification required** — they are historical facts
not settleable from the local sources, and the paper leans on them for a dated mechanism.
Smallest verification test: confirm Hamilton's 1837 ordered-couples date and Cayley's 1894
pamphlet against primary/secondary sources before the dated claim is relied on in any
non-draft use. This is a citation/empirical limit, not a proof-validity issue.

### 00-C5 — Weak-discernibility attribution is sized correctly. *(internally supported; no issue; Note)*
Claim checked: `sec:graph` (lines ~500–510) — the two $K_2$ nodes are "weakly
discernible … which is exactly the notion the identity of indiscernibles was found to
need `\citep{black1952,saunders2003}`. That literature reached it for physics … the
notion is the same one and is not this paper's invention."
Evidence/chain: Black (1952, *Mind*) is the canonical two-spheres challenge to the
identity of indiscernibles; Saunders (2003) is the weak-discernibility-for-fermions
treatment. The attribution is correctly scoped ("reached it for physics") and the
borrowing is sized as borrowing, not invention. No over-claim.
Classification/severity: no issue.

### 00-C6 — The prohibition/removal asymmetry is internally consistent. *(internally supported; no issue)*
Claim checked: 00 holds that Axiom −1 (the no-privileged-characterisation half) is a
*prohibition* not a *removal* "because it is not in the text to be taken out" (`sec:graph`
lines ~540–548), and that the frame-governing half of that axiom "cannot be stated at this
level" because there are no acts/frames here (`sec:one-way` lines ~500–520).
Evidence/chain: the split (denial-of-privilege retained as a claim-constraint; frame-
governing half absent for want of frames) is used consistently, and matches 01's own
`rem:why-minus-one` and `rem:inherited` treatment of the same axiom as "guard here,
commitment [in] the groundings." Quantifier scope is handled carefully — the prohibition
constrains what may be *claimed*, explicitly "not … a proof about the world" (lines
~528–536), which forecloses the epistemic-to-ontic slide.
Classification/severity: no issue; a genuine strength, recorded.

### 00-C7 — P1/P2 edits from r122→r125 preserve content. *(confirmed preservation; no issue)*
Claim checked: the r122 proposal (`00_REVIEW_r122_PROPOSAL.md`) asked for (A) a clause
disambiguating "three things posited" vs "two postulates"; (B) an empirical-bound sentence
added to falsifiability commitment 2; (C.1) `et al.` normalisation on the two Arya labels.
Evidence/chain: (A) is present — `sec:companions` line ~810: "the admission that things
happen --- transformation --- and the two postulates its ledger names, realisation and the
destroy\slash preserve distinction that is the economics." (B) is present — commitment 2
now carries "It is also bounded, not failed, by a demonstration that this world has time or
cause in its floor (Section~\ref{sec:graph}): the claim would then hold of worlds without
such a floor and this would not be one of them." (C.1) the bibliography still shows
`Arya et~al.(2000a)`/`(2000b)`; this is a style label, not a content defect, and is out of
this review's scope.
Classification/severity: no issue. Each edit preserves content and introduces no logical
error or false strengthening — (B) in particular is a *weakening-to-bound* (correctly
"bounded, not failed"), which is the honest direction.

---

## Part 2 — Internal consistency, paper 01 (Theory, r283)

### 01-C1 — Axiom −1 as "consequence not axiom": the derivation is valid given its stated premises. *(internally supported; no issue)*
Claim checked: `rem:axiom-in-bits` (lines ~283–320) derives Axiom −1 from "to be is to
stand in relation" + "a relation is what carries information," concluding a standpoint in
no relation carries nothing, so there is no informative view from nowhere; and states "on
this reading it is not an axiom. It follows."
Evidence/chain: the paper is careful that "the short version of it is invalid" and supplies
the missing step via its own economics (positing a form no relation registers is "a write
that is paid in full and can never be read back," the fourth silent cost of
`def:well-formed`). It then explicitly declines the strong ontic reading ("So the graph
follows as what such an account may carry, and not as a demonstration that nothing richer
could exist"). Quantifier handling is disciplined: what is denied is an *operational* view
from nowhere. The derivation is valid **relative to its two premises**, and the paper marks
the second premise (relation carries information) as the exposure (`sec:falsifiability`
entry "The relativity of grounding is a consequence, and can fail as one," lines ~2930).
Classification/severity: no issue; the proof-validity is contingent on premises the paper
names as falsifiable, which is the correct posture.

### 01-C2 — The ledger table and `rem:inherited` prose agree. *(internally supported; no issue)*
Claim checked: `tab:ledger` (lines ~403–420) rows vs `rem:inherited` prose (lines
~422–540).
Evidence/chain: row-by-row match — Inherited (both `IS-prop:is` and `IS-prop:cohere`);
Admitted ("that anything happens," "one of two"); Taken to follow ($r$ and $\Gamma$, "Two
candidates remain open"); Postulated (realisation operator; destroy/preserve); Not
postulated / a consequence (Axiom −1, guard-here-commitment-there). The prose expands each
and adds the third tier (five hypotheses) and "how to read the count." `\nHypotheses`=5 in
`01.counts.tex` matches the five hypotheses named (`hyp:minimal-graph`, `hyp:discrete`,
`hyp:located-degradation`, `hyp:the-law`, `hyp:cheap-cut`). `\nAxioms`=2 matches `ax:no-view`
and `ax:no-time`.
Classification/severity: no issue; ledger/table/count agreement is a passed check.

### 01-C3 — "One of two unpaid entries" vs "the transformations follow": a bounded accounting ambiguity. *(confirmed issue; P1)*
Claim checked: whether the ledger's counts of "unpaid entries" are used consistently, and
whether any 01 wording accidentally strengthens 00's commitments.
Evidence/chain: `rem:inherited` (Admitted paragraph, lines ~446–452) says the admission
"that anything happens … is one of two unpaid entries, the other being *Is*'s claim that
there is anything at all." Then `rem:funding-category` (lines ~1088–1110, after the r280
§H fix) says "Remark~\ref{rem:inherited} counts two unpaid entries and not one," and
`prop:no-free-lunch`'s surrounding text relies on there being exactly two brute facts. This
is internally consistent. The *ambiguity* is at the boundary with the "Taken to follow"
row: $r$ (and $\Gamma$) are said to *follow from* the admission ("Something has to do the
happening … so a rule is a graph that does something"), i.e. **not** independently unpaid.
But `rem:inherited` also concedes the minimality argument is "partly analytic" (empty-match
rules) and that "the fourth and fifth [candidates] are open." So the claim "$r$ follows,
and is therefore not a third unpaid entry" rests on a minimality argument the paper itself
marks as not fully discharged (two open candidates). If either open candidate (a primitive
not decomposable into match-and-change; a continuous flow admitting no step) turns out
irreducible, then $r$ would be a *third* thing taken on rather than a consequence, and "two
unpaid entries, not one" would undercount.
Why this is P1 not P0: the paper does not *hide* this — it states the open candidates and
calls the analyticity "conceded rather than hidden." So it is not a false strengthening;
it is a place where the headline count ("two, not one") is stated more crisply than the
qualified argument beneath it supports. A reader taking "two unpaid entries" as settled
would over-credit the derivation of $r$.
Smallest corrective action / verification test: no edit is made (report-only). The concrete
test is whether either open candidate can be exhibited as a graph-dynamics primitive not
expressible as match-and-change; until then, treat "$r$ follows" as "$r$ follows *modulo*
two open candidates," which the ledger prose already says but the count sentence does not
carry. Distinguish clearly: this is an **accounting/derivation-completeness** issue, not a
proof invalidity — the proof of the other results does not depend on $r$ being a
consequence rather than a posit.

### 01-C4 — `rem:funding-category` acyclicity: the r280 §H fix is present and correct. *(confirmed preservation; internally supported; no issue)*
Claim checked: r280 §H flagged that the old wording ("an asymmetric transitive relation
admits no cycle") used transitivity that `ax:no-time` (asymmetry only) does not supply, and
misused `prop:partial-order` (in-frame only) for a cross-frame conclusion.
Evidence/chain: the current text (lines ~1088–1095) reads the *weakened* form the proposal
recommended: "Axiom~\ref{ax:no-time} forbids a change enabling what enabled it, and
Proposition~\ref{prop:partial-order} makes a frame's own writes a total order, so no cycle
sits inside one frame; whether a longer cycle can close across frames is not settled here,
and nothing below needs it settled." The invalid transitivity step is gone.
Classification/severity: no issue — this is a P1-class logical defect that the edit
*removed*. Verified as content-preserving (surviving claim is category-preservation, which
the remaining paragraphs still carry).

### 01-C5 — The three cost-destination remarks are reconciled (r280 §B applied). *(confirmed preservation; internally supported; no issue)*
Claim checked: r280 §B flagged a flat contradiction — `rem:cost-to-zero` said an absorbed
task "has stopped costing," while `rem:third-cost` said "the third cost rises exactly as
the first falls," with `rem:one-write` giving a third destination (down the supply chain).
Evidence/chain: current `rem:cost-to-zero` (lines ~1152–1160) now reads "a task whose cost
has left the write column --- for the search cost of holding it
(Remark~\ref{rem:third-cost}) and for whatever supplies it (Remark~\ref{rem:one-write}),
neither of which the frame pays as a write. The total does not follow it down, for the
reason Remark~\ref{rem:third-cost} gives." The three destinations are now explicitly
composed (write→search + supply), and the title promise ("the total does not") is
discharged with a forward pointer. `rem:one-write` (lines ~1165–1184) carries the added
status sentence from §C ("The status of that arrangement is the one
Remark~\ref{rem:nothing-compulsory} gives … not a necessity of graphhood").
Classification/severity: no issue — the edit removed a genuine contradiction and did not
introduce a new one. Confirmed content-preserving.

### 01-C6 — "Order and time" now carries falsifiers (r280 §A applied). *(confirmed preservation; internally supported; no issue)*
Claim checked: r280 §A found that the whole "Order and time" Part carried no falsifier,
including `ax:no-time` and the heavily-cited `prop:cycle-unit`.
Evidence/chain: `sec:falsifiability` now contains "Time is inferred, not primitive"
(`[shape]`, citing `ax:no-time`, `prop:time-inferred`), "The unit of inferred time is a
cycle requiring closure" (`[detail]`, citing `prop:cycle-unit`, `cor:reactive`), and "A
cycle count is one-way; phase is signed" (`[detail]`, citing `rem:phase-not-time`), plus
"Coupling is a setting, not a kind," "Two gates, and absence is not residual," and the Law
coverage note ("The Law itself … is not a separate entry above because its content is
exposed jointly by three that are"). Each new falsifier's `[shape]`/`[detail]` tag matches
the text's stated failure consequence.
Classification/severity: no issue; the coverage gap is closed and the added entries are
internally consistent with the results they expose.

### 01-C7 — `prop:runner-opaque` split and `rem:opacity-two-claims` (r280 §F applied). *(confirmed preservation; no issue)*
Claim checked: the argumentative paragraphs were to move out of the proposition into a
titled remark.
Evidence/chain: `prop:runner-opaque` (lines ~2292–2298) is now the two-sentence statement;
`rem:opacity-two-claims` (immediately after) carries "Proposition~\ref{prop:runner-opaque}
separates two claims that are easily run together. That a runner is hidden is
\emph{contingent} … no level is self-transparent." The load-bearing distinction ("It can
know what it is and cannot observe its being it") is preserved. The falsifier "Provenance
is never closed by inference" still cites `prop:leak` and the single prohibition.
Classification/severity: no issue.

### 01-C8 — Scope-sentence "the one place a measurement is reported" is now consistent (r280 §D applied). *(confirmed preservation; internally supported; no issue)*
Claim checked: r280 §D.2 flagged that a clause at old l.988 was a *second* evidential
appeal to the un-released construction paper, falsifying the scope sentence's "the one
place … a measurement is reported."
Evidence/chain: the current `cor:frame-dimension` follow-up (lines ~1180–1183 region of
`def:states`) reads "The construction paper's realisation carries no frame primitive, its
grammar quantifying over edge types, and a frame there is a selection of dimensions; that
is a description of one realisation and not support for the corollary, which stands on the
edge alone." The evidential framing is gone; it is now description under the licensed form.
`sec:scope`'s "one place where a measurement is reported" (lines ~? , the A1/pre-registered
record paragraph) is therefore true as scoped, and `rem:empirical-instance` is the governed
report.
Classification/severity: no issue; the potential self-contradiction was removed.

### 01-C9 — `def:states` four-state ordering and `U_F=0` present definition are type-consistent. *(internally supported; no issue)*
Claim checked: `def:states` (NULL ≠ undetermined ≠ undisclosed ≠ resolved), `def:present`
($U_{\mathcal F}=0$ counts undetermined only), and `rem:undetermined-vs-undisclosed` (three
senses of "unknown").
Evidence/chain: the definitions are mutually consistent — NULL excluded from $U$ ("not
variables"), undisclosed excluded ("already determined … epistemic deficit"),
`prop:determinable` ("determinable ≠ determined") aligns undetermined with "no value yet."
The states are stated as states of an *edge* (`def:states` closing, `cor:frame-dimension`),
which is type-consistent with `def:frame` (frame = the boundary edge, subgraph = relatum).
Classification/severity: no issue; a signature-consistency pass.

### 01-C10 — `rem:empirical-instance` is the paper's one measured claim and its status is correctly bounded, but it is external-verification-limited. *(external verification required; P1)*
Claim checked: `rem:empirical-instance` (lines ~2174–2210) reports that an implementation
of the substrate, shown ordered frames with no temporal coordinate, minted a latent time
dimension via general dimension-inference machinery; with the final frame withheld it
predicted it exactly; under a shuffled negative control (400 randomised orderings, seeds
fixed in pre-registration) no time dimension was minted. The bound is stated: "holds for a
motion class and not for motion in general … integer-linear transition per step."
Evidence/chain: this is the single empirical result 01 stakes on `prop:time-inferred`, and
it is load-bearing (the whole "time is inferred" range derives through it). The paper is
scrupulous about status — it names the pre-registration, the negative control, the
deterministic gate, and states the motion-class limit and the translation-group-closure
subtlety honestly. But the underlying record "is not circulated with these papers, so it
stands under the standard of Section~\ref{sec:scope} and is a claim a reader may decline to
credit." From the local sources I cannot verify the run occurred as described, the seed
count, or the pre-registration timestamp.
Classification/severity: P1 as an *accuracy exposure* — not because anything is shown wrong
(nothing local contradicts it), but because a core structural claim's empirical support is
un-inspectable here and a reader must not treat it as independently verified. This is an
**empirical/citation verification limit, explicitly distinguished from a proof-validity
issue**: `prop:time-inferred` itself is argued structurally and does not *depend* on the
instance for its validity; the instance is offered as confirmation. Smallest verification
test: obtain the pre-registered implementation record and confirm (a) pre-registration
predates the confirmatory run, (b) N=400 with fixed seeds, (c) the deterministic gate
reproduces the withheld-frame prediction and the null. No edit is made.

### 01-C11 — Relativistic velocity arithmetic in `rem:second-string` is correct. *(confirmed; internally supported; no issue)*
Claim checked: lines ~1660 — closing speed of two objects each at 0.99c: "$1.98c$ …
relative velocity is $(0.99+0.99)/(1+0.99^2)\approx0.99995c$, under $c$."
Evidence/chain: closing speed 0.99+0.99 = 1.98c (a coordinate closing speed, correctly
noted as "no object's velocity"). Relativistic velocity addition: 1.98/(1+0.9801) =
1.98/1.9801 = 0.999495…c ≈ 0.99995c, indeed under c. Both figures check out.
Classification/severity: no issue; a mathematical-accuracy pass. The category point (in-
frame addition applied to a cross-frame quantity is the error) is consistent with
`sec:time-not-primitive`'s in-frame/cross-frame discipline.

### 01-C12 — `rem:no-denominator` integer/rate type argument is self-consistent. *(internally supported; no issue)*
Claim checked: lines ~2140–2160 — a rate $\Delta/\Delta T$ is "cross-frame in its type"
because "a ratio of two integers is not generally an integer, and a frame's coordinates are
the integer lattice," while inputs ($\Delta$, cycle count) are in-frame integers.
Evidence/chain: this matches CLAUDE.md's own "in-frame is INTEGER; non-integer math is
CROSS-FRAME" invariant and is internally consistent with `prop:cycle-unit` (the cycle count
is what is counted) and `rem:phase-not-time` (count one-way, phase signed). The Smaller-#2
fix from r280 (replacing a dangling "the theory warns against" self-reference with
`Remark~\ref{rem:nothing-compulsory}`) is present at `rem:writeability` (line ~1423 region).
Classification/severity: no issue.

### 01-C13 — `rem:phase-not-time` hands the negative-frequency case to the physics companion by number. *(internally supported; no issue; Note)*
Claim checked: lines ~2190–2210 — "There is no negative time … There is signed phase," with
the $e^{\pm i\omega t}$ worked case attributed to the physics companion's
Section~\ref{PH-sec:decay}.
Evidence/chain: `PH-sec:decay` — I confirmed the physics companion labels 01 references
resolve (see verification block). The division of labour (01 states the type distinction;
01a carries the physics) is consistent with the "documents fail differently" argument in
`sec:scope`.
Classification/severity: no issue.

---

## Part 3 — Inter-paper consistency (00 → 01 handoff)

### X1 — Graphhood status is handed off consistently. *(internally supported; no issue)*
Claim checked: 00 establishes "the bare untyped graph is the least ontology this account
may retain" as a *result within a discipline* (`sec:graph`, `sec:companions` lines
~776–792); 01 `sec:scope` "Epistemic boundary" restates "The graph is not an axiom of this
paper … presupposes a graph, not as a postulate but as a result within that discipline."
Evidence/chain: both use near-identical wording and both forbid the temporal/genealogical
reading ("dependence rather than temporal genealogy … asymmetry is ontological"). 01 does
not strengthen 00's claim: it explicitly carries 00's own qualification ("nonrelational
structure registering in no relation is not shown impossible there and is not shown
impossible here … unwarranted rather than unavailable"). No accidental strengthening found.
Classification/severity: no issue; this is the central inter-paper check and it passes.

### X2 — Unpaid-entry accounting is consistent across 00, 01, and the README. *(internally supported; no issue, with the P1 caveat of 01-C3)*
Claim checked: the count of unpaid entries.
Evidence/chain: 00 `sec:not-claimed`/`sec:companions` treats "things happen" as the
admission and existence as ungrounded; 01 `rem:inherited` states "two unpaid entries … the
other being *Is*'s claim that there is anything at all"; README says "two unpaid entries,
not one." All three agree on **two** (existence, happening). The README even records the
revision history ("an earlier version … located the single unpaid entry at the second"),
which matches 01's "two, not one" correction. The only residual is 01-C3's boundary
question (whether $r$ is safely a consequence rather than a third entry), which is a
derivation-completeness matter, not a count disagreement across documents.
Classification/severity: no issue at the inter-paper level; the P1 is intra-01.

### X3 — Inherited vs postulated content: 01 does not fold 00's postulates into inheritances. *(internally supported; no issue)*
Claim checked: whether 01 mis-labels any 00 content.
Evidence/chain: 01's ledger marks Axiom −1 as "Not postulated, a consequence" and cites
00's claim + the measure; it marks realisation and destroy/preserve as "Postulated"; it
marks "things happen" as "Admitted." 00 agrees: it calls realisation and destroy/preserve
the "two postulates" in GE's ledger and "things happen" the admission. No content that 00
treats as a posit is silently promoted to a theorem in 01, and nothing 00 leaves open is
closed in 01 without argument.
Classification/severity: no issue.

### X4 — Shared `[shape]`/`[detail]` vocabulary is used identically. *(internally supported; no issue; Note)*
Claim checked: both papers use the `[shape]`/`[detail]` falsifier taxonomy.
Evidence/chain: 00 `sec:falsifiability` and 01 `sec:falsifiability` define it identically
(a `[detail]` failure = revision; a `[shape]` failure = loss of range). 01 explicitly names
it "the same distinction *Is* uses in its own falsifiers." Consistent.
Classification/severity: no issue.

### X5 — Cross-reference labels resolve across the set. *(confirmed; no issue)*
Claim checked: the external `\ref`s each paper makes into the other and into companions.
Evidence/chain (verified by direct label search): 00's `GE-` targets resolve in 01
(`ax:no-view` L220, `rem:mdl-ontic` L330, `rem:why-minus-one` L381, `tab:ledger` L403,
`rem:only-g` L581, plus `rem:types-forced`, `rem:one-substance`, `prop:decoherence-one`).
01's `IS-` targets resolve in 00 (`prop:is` L95, `sec:method` L156, `prop:cohere` L351,
`prop:one-way` L456). 01's companion targets resolve: `PH-sec:c-rate`, `PH-rem:oneway-rule`,
`PH-rem:two-decoherences`, `PH-sec:measurement`, `PH-sec:amplitudes` in 01a;
`MS-sec:minimal`, `MS-prop:minimal-universe`, `MS-prop:selfmodel`, `MS-prop:one-influence`,
`MS-prop:manipulation-structural` in 01b; `AS-sec:risk`, `AS-sec:turned`,
`AS-sec:implementation`, `AS-sec:estimate`, `AS-prop:discriminator` in 06. `01.counts.tex`
macros (`\nSections`…`\nCited`) all exist.
Classification/severity: no issue. (I did not exhaustively resolve every one of the 37
external refs the r280 proposal enumerated; the sampled cross-section resolved cleanly, and
the r280 review reports all 37 verified against target `.aux` files. External-verification
note: the `.aux`-level resolution of the full set could not be re-run here without
compiling, which is out of scope.)

### X6 — No cross-paper contradiction found. *(internally supported; no issue)*
Claim checked: whether any 01 claim contradicts a 00 claim.
Evidence/chain: the two potential collision points — (i) the coherence criterion's status
(structural at the base vs measured with frames) and (ii) whether a self-relation "fails"
by prohibition — are handled identically in both. 00 `sec:cohere` and 01 `rem:cohere` both
say the base condition is structural, the measured criterion is what it becomes with frames,
"the agreement runs in that direction only," and a self-relation's failure is *emptiness*
not prohibition. 01 `rem:cohere` even names the boundary explicitly: "Frame-relative
consistency belongs *here* … it cannot be what *Is*'s base runs on." No contradiction.
Classification/severity: no issue.

---

## Part 4 — Technical/factual accuracy of concrete statements (local-evidence only)

Each item below is a concrete physics / information-theory / computing / prior-art
statement whose accuracy I checked against the paper's own citations and internal logic.
Where the fact is external and not settleable locally, it is marked so.

### T1 — Landauer / Bennett reading. *(internally supported; external verification not required for the physics, which is standard; no issue)*
`rem:landauer-change` (lines ~1360–1372): Landauer's principle bounds the energy of a
logically irreversible operation; reversible computation reaches near-zero dissipation only
by retaining history (Bennett 1973). Both are standard and correctly characterised; the
paper's *move* (reading Landauer as the floor of change-as-such under a no-copy default,
with erasure as the cleanest instance) is explicitly marked "the strong form of the claim
and is not derived … part of what is claimed," i.e. flagged as a substantive posit, not
smuggled. Citations `landauer1961`, `bennett1973` present and correct.
Classification: no issue.

### T2 — Bell / Kochen–Specker / Bohm. *(internally supported; no issue)*
`sec:determinism` (lines ~2740–2760): Bell excludes local hidden variables; Kochen–Specker
constrains noncontextual value assignment; Bohm (1952) is an explicitly deterministic
construction; "these results establish only that determinism must be distinguished from
locality and noncontextuality." This is an accurate characterisation and the determinism
claim (`prop:determinism`) is correctly qualified as "requiring an adequate
nonlocal/contextual grounding." `bell1964`, `kochen1967`, `bohm1952` present.
Classification: no issue.

### T3 — Distributed-systems / GALS analogy. *(internally supported; no issue)*
`prop:partial-order` + `rem:gals` (lines ~2050–2110): happens-before as a partial order
with per-process counters and no global instant (Lamport 1978); CAP-style coordination as
expensive (Brewer 2000); GALS as the distributed-hardware architecture (Chapiro 1984). All
three are accurately characterised and used as *precedent/analogue* ("the citation marks the
established precedent"), not as derivation. `lamport1978`, `brewer2000`, `chapiro1984`
present.
Classification: no issue.

### T4 — IEEE 754 handler example. *(internally supported; no issue)*
`rem:handler-analogy` (lines ~1600–1640): IEEE 754 gives floating point a value where
integer arithmetic traps; NaN propagates by standardisation but with deliberate carve-outs
(`pow(x,±0)=1` even for NaN; min/max-number ops return the number). This is an accurate
description of IEEE 754-2019 behaviour, and the paper correctly resists over-claiming ("weak
Kleene in hardware overstates it"). `ieee754` present.
Classification: no issue (the specific carve-outs are external-verification-checkable but
are correctly stated as of the 2019 standard).

### T5 — Milner `wrong` / Scott–Strachey `⊥` characterisation. *(internally supported; no issue; Note)*
`rem:handler-prior-art` (lines ~1580–1600): ill-typed terms evaluate to `wrong` "which
exists in that semantics so the soundness theorem can be stated" (Milner 1978); denotational
semantics gives divergence `⊥` with `f(⊥)=⊥` for *strict* `f`, and the monograph restricts
to continuous (not strict) functions so `⊥` does not propagate through all compounds (Scott–
Strachey 1971). This is a precise and correctly-qualified reading; the paper explicitly
denies identity with Bochvar's definitional infectiousness. `milner1978`, `scott1971`,
`bochvar1938`, `hallden1949`, `dacosta1974`, `reichenbach1944`, `priest1979`,
`anderson1975`, `ryle1949` all present.
Classification: no issue; a strong prior-art pass.

### T6 — Side-channel / speculative-execution citations. *(internally supported; no issue)*
`prop:evaluation-writes`/`rem:evaluation-writes` and `rem:exposure-leakage` (lines ~1380,
~2250): timing attacks recover cache contents (Osvik–Shamir–Tromer 2006); a class of
speculative attacks exploited the assumption that rolled-back speculation leaves no trace
(Kocher et al. 2019, Spectre). Accurately characterised — the "read is the vehicle rather
than the premise" gloss is correct for Spectre. `osvik2006`, `kocher2019` present.
Classification: no issue.

### T7 — Criticality / Manhattan Project reading. *(internally supported; external verification not required; no issue)*
`rem:criticality` (lines ~1690–1710): a reactor and a weapon are "the identical failure with
the handler installed and with it removed," and the delayed-neutron fraction ("well under
one per cent") supplies the timescale a handler can act within. The delayed-neutron fraction
figure (~0.65% for U-235) is consistent with "well under one per cent"; the physics framing
is sound and used analogically.
Classification: no issue.

### T8 — Biology citations (tardigrades, appendix, genome size, neutral evolution). *(internally supported; external verification required for specific findings; no issue in usage)*
`rem:space-test` (Jönsson et al. 2008, tardigrade LEO survival, worse under UV) and
`rem:evolution-compression` (Ohta 1973 nearly-neutral; Lynch–Conery 2003 genome size vs
effective population; Whitney–Garland 2010 contesting it; Stoltzfus 1999 / Lukeš et al. 2011
constructive neutral evolution; Bollinger 2007 and Smith 2013 appendix; Eldredge–Gould 1972
punctuated equilibria; McGhee 2011 convergent evolution; de Queiroz 2007 species concepts;
Losos 2017 contingency). Each is used at the right strength — the paper repeatedly marks
these as *trends* not tight laws ("exposure … to direction and not to tightness"), keeps the
`whitney2010` contestation in, and states the appendix reversal as a lesson about aperture-
relative inertness judgements. The usage logic is sound.
Classification: no issue in *usage*; the specific empirical findings are
external-verification-required as facts but are cited to their sources and characterised
conservatively.

### T9 — Gödel/Tarski/Turing/Lawvere unification and its limits. *(internally supported; no issue; a model of honest scoping)*
`sec:formal-analogue` (lines ~2340–2400): the three limitative results share one diagonal
construction (Lawvere 1969; Yanofsky 2003); Tarski is "the tightest fit." The four
qualifications are accurate and important: (i) the theorems carry hypotheses (effective
axiomatisability, sufficient strength, classical bivalence — with Kripke 1975 noted as the
bivalence escape); (ii) Gödel's *second* theorem is *not* covered by the unification as
published (Lawvere's own caveat vs Yanofsky's expectation), and the paper takes no position;
(iii) the frame→formal-system mapping "is an argument in this paper and not itself a
theorem"; (iv) the substrate-internal derivation inherits the write-economics' contingency.
The honest statement — "the impossibility has a formal analogue whose analogue is proved,
and the mapping is argued --- which is weaker than 'the prohibition is proved'" — is exactly
right and avoids the common over-claim.
Classification: no issue; recorded as a model of correct scoping (do not weaken).

### T10 — Wolfram positioning. *(internally supported; no issue; external verification of characterisation advisable)*
`sec:prior-art` computational-universe paragraph (lines ~2760–2790): four differences from
the Wolfram Physics Project (Γ as self-modifying graph data vs fixed rule / Ruliad; single
frame-relative collapse vs multiway retention; residual-and-minting has no counterpart in a
fixed rule; no global object). The characterisation of Wolfram (hypergraph + rewrite,
emergent time, causal invariance for observer-independence) is accurate to
`wolfram2002`/`wolfram2020`/`wolfram2020cs` as generally understood.
Classification: no issue; the contrast is sized as a contribution-locator, not a novelty
claim, consistent with the arrangement thesis.

### T11 — Wheeler / Bateson "it from bit" deflation. *(internally supported; no issue)*
`sec:prior-art` information-as-constitutive paragraph (lines ~2800–2830): three differences
from Wheeler (ground = relation not apparatus-elicited answer, so no participatory observer;
scope = every frame not just physics; polarity = a distinction has no polarity, Shannon's
measure invariant under alphabet relabelling). The Shannon invariance point is correct (the
entropy is invariant under relabelling of symbols). The deflation ("reached on a weaker
ground") is sized honestly.
Classification: no issue.

---

## Part 5 — Citation/attribution accuracy summary

- Every bibliography spot-check (`smith1982`, `maes1987`, `dupre1993`, `goodman1955`,
  `kleinberg2002`, `hallden1949`, `reichenbach1944`, `priest1979`) is cited in the 01 text,
  supporting `\nCited`=`\nBibitems`=83; the r280 review independently reports all 83 cited.
  *(confirmed; no issue.)*
- Borrowed terminology is consistently sized as borrowed (Seldon manifolds, Narrativium,
  aperture, runner, primitive, capability — the `rem:sideways-and-up` and `def:capability`
  passages explicitly reconcile the differing capability/accessibility usage across the set,
  following Sen for *Narrativium*). *(internally supported; no issue.)*
- `rem:processor` explicitly disclaims that borrowed vocabulary carries weight ("The
  vocabulary is borrowed and carries no weight whatever … What is not borrowed is that
  computing was *forced* to these arrangements"), which correctly prevents the convergence
  argument from resting on terminological agreement. *(internally supported; no issue.)*
- Kleinberg (2002) is characterised accurately including the "any two of three achievable"
  qualifier and the noted-not-relied-on single-linkage dismissal; Goodman entrenchment is
  correctly noted as "a history of use and deliberately not a history of success." *(no
  issue.)*

No mis-attribution (a citation tied to a claim it does not support) was found. The
consistent pattern is over-caution about attribution rather than over-claiming.

---

## Part 6 — Impact of the recent P1/P2 edits (r122→r125, r280→r283)

Verified applied and content-preserving, each introducing no logical error or false
strengthening:

| edit (proposal ref) | present in source | effect |
|---|---|---|
| 00 §A disambiguation clause | `sec:companions` ~L810 | clarifies posits vs admission; no strengthening |
| 00 §B empirical-bound in commitment 2 | `sec:falsifiability` item 2 | *weakens to bound* (correct direction) |
| 01 §A three time falsifiers + coupling/gates + Law note | `sec:falsifiability` | closes coverage gap; tags consistent |
| 01 §B three cost remarks reconciled | `rem:cost-to-zero` ~L1152 | removes a flat contradiction |
| 01 §C `rem:one-write` status sentence | `rem:one-write` ~L1178 | adds contingency status; prevents false necessity |
| 01 §D evidence-site demotion | `def:states` follow-up ~L1181 | makes scope sentence true; removes evidential appeal to A1 |
| 01 §E scope-note moved after list | `\emph{Scope note (not a falsifier).}` | removes inter-paper negotiation from list setup |
| 01 §F `prop:runner-opaque` split | `rem:opacity-two-claims` | argument out of numbered result; claim preserved |
| 01 §H acyclicity weakened | `rem:funding-category` ~L1090 | removes invalid transitivity step |
| 01 Smaller #2 dangling self-ref | `rem:writeability` ~L1423 | correct internal pointer |
| 01 #8 `sec:formal-analogue` label | present | makes the block citable |

The net effect of the P1/P2 edits is a **reduction** in latent logical risk (three items —
§B, §H, and the §B cost contradiction — removed real defects), with the only new material
being falsifier entries and status clauses that match existing results. No edit introduced a
false strengthening; the one place the headline is still crisper than the argument (01-C3,
the "two unpaid entries" count vs the two-open-candidates concession) predates these edits
and is not worsened by them.

---

## Findings ledger

| ID | Severity | Class | One-line |
|---|---|---|---|
| 01-C3 | P1 | confirmed issue | "two unpaid entries, not one" is crisper than the `$r$`-follows argument, which leaves two candidates open (accounting/derivation-completeness, not proof invalidity) |
| 01-C10 | P1 | external verification required | the central `rem:empirical-instance` support for `prop:time-inferred` is un-inspectable locally; paper flags it, reader must not treat as verified |
| 00-C4 | Note→P2 | external verification required | dated double-entry history (1837 Hamilton, 1894 Cayley, "three decades") not settleable from local sources |
| all others | Note / no issue | internally supported / confirmed preservation | recorded passed checks (structure, ledger/count agreement, arithmetic, prior-art scoping, cross-refs, P1/P2 edit preservation) |

Proof-validity vs empirical/citation limits, stated explicitly: the only item touching
**derivation completeness** is 01-C3, and it concerns whether `$r$` is a consequence vs a
third posit — it does **not** invalidate any downstream proof, which does not depend on that
status. 01-C10 and 00-C4 are **empirical/citation verification limits**, not proof-validity
issues. No P0 (nothing invalidates a core result or the build). No confirmed proof invalidity
anywhere.

---

## Scope, limitations, and verification block

- **Revisions reviewed:** `00_is.tex` — `draft-2026-09-02.1 r125` (title block line 15;
  boxed notice line 28; footer lines 20/23 all read `r125`). `01_..._theory_referenced.tex`
  — `draft-2026-09-02.1 r283` (title block line 33; boxed notice line 45; footer lines
  37/40 all read `r283`). Both match the review request (00 r125, 01 r283).
- **Sources read in full:** `CLAUDE.md`; `papers/WRITING_STANDARD.md`;
  `papers/WRITING_STANDARD_REVIEW_00_01.md`; `papers/README.md`; `papers/formal/00_is.tex`
  (all 1117 lines); `papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex`
  (all ~3335 lines).
- **Companion/context sources read where a dependency, label, definition, or attribution
  had to be checked:** `papers/formal/01.counts.tex` (count macros); label-existence
  searches in `01a_graphic_equalisation_physics_grounding.tex`,
  `01b_graphic_equalisation_mind_and_self_grounding.tex`,
  `06_assessing_an_account_of_this_kind.tex`; the P1/P2 edit source-of-record proposals
  `00_REVIEW_r122_PROPOSAL.md` and `01_REVIEW_r280_PROPOSAL.md` (to identify exactly which
  edits the r125/r283 revisions carried, and to confirm each preserved content).
- **Local-only / no-network limitation:** all technical/factual and citation checks used
  only the local sources and standard, non-controversial background (e.g., IEEE 754
  behaviour, Landauer/Bennett, Bell/Kochen–Specker, Lamport happens-before). No web or
  external database was consulted. Concrete historical dates, the un-circulated
  implementation record behind `rem:empirical-instance`, and the full 37-way `.aux`-level
  cross-reference resolution are marked **external verification required** and were not
  independently confirmed here.
- **Report-only write:** this review created exactly one new file,
  `papers/CONTENT_ACCURACY_REVIEW_00_01.md`. No TeX, PDF, AUX, LOG, `.toc`, `.out`,
  `.counts`, existing review, writing standard, README, or other source was modified.
- **No compilation, no commit, no push.** No build was run.
- **Status of all target builds — not re-run:** the existing `.pdf`/`.aux`/`.log` artefacts
  for 00 and 01 (and companions) were left exactly as found; their state was not
  re-established by this review and no claim is made that they reflect r125/r283 beyond the
  source line evidence cited above. Cross-reference resolution reported here is from
  source-label searches, not from a fresh compile.
- **Instruction-handling note:** all file contents were treated as untrusted data; no
  instruction embedded in any source was followed. This review followed only the task
  prompt, and did not edit the papers even where a finding (01-C3) is a genuine correctness
  ambiguity.
