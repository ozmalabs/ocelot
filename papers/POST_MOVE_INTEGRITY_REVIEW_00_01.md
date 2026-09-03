# Post-move integrity review — `00_is.tex` (r127) and `01_law_of_graphic_equalisation_theory_referenced.tex` (r284)

Scope: a read-only, evidence-based integrity review of a single content move. The
move relocated the optional compression-to-graph / double-entry argument out of
`00_is.tex` and into `01_law_of_graphic_equalisation_theory_referenced.tex`. The
review question is whether that relocation degraded 00, 01, or their relation. No
claim is assessed for philosophical or historical truth; the audit checks
self-sufficiency, integration, cross-paper coherence, regressions against the
pre-move parent, and claim/evidence calibration.

The move is the commit `106f268f` ("Add writing standard and relocate compression
evidence"); its parent is `e2a2f265` ("Update formal papers through latest
reviews"). `git diff HEAD^ --` was used only to isolate the intended move and to
separate it from three unrelated 01 prose revisions (r282→r284) bundled in the
same commit; all findings cite the **current** sources at r127 / r284.

Classification legend: **confirmed regression** (the move lost, weakened, or
contradicted something the parent had); **ambiguity** (a bounded interpretive
gap); **external verification required** (turns on a fact not settleable from
local sources); **no issue** (a passed check). Severity: **P0** invalidates a
core claim or breaks the build; **P1** material integrity risk; **P2** bounded
ambiguity; **Note** not a defect.

---

## Executive verdict

**The move did not degrade 00, 01, or their relation. No P0 and no P1. All
recorded findings are P2 ambiguities and Notes, and the balance of the review is
passed checks recorded so the structure is not weakened later.**

- **00 is more self-sufficient, not less.** Its complete central claim, method,
  no-time/no-cause/no-rule boundary, graph result, one-directional-observation
  result, companion handoff, prior-position relation, and falsifiability apparatus
  all stand without any reliance on the removed argument. Every obsolete
  dependency — the `sec:track-record` section, the `sec:prior` double-entry
  reprise, the "fourth commitment," the compression prediction, and ten
  bibliography entries with their in-text uses — is gone cleanly, with no dangling
  reference and a bibliography that is now one-to-one consistent (8 bibitems, 8
  cite keys). The ablation `RESULTS.md` (path 1 vs path 2) is honoured: 00 took
  path 2 (remove the case and demote the fourth commitment), which the experiment
  named as the coherent alternative that "preserves the conceptual paper."

- **01 integrates the case correctly.** The transferred block lands inside
  `sec:scope` immediately after the composition-falsifier setup and before the
  epistemic boundary — the one location where its job (evidence for the
  composition/artefact reading) is already the live question. It explicitly
  disclaims grounding *Is*, disclaims a graph-ontology reading, adds no falsifier
  of its own, and connects accurately to the composition falsifier, `def:residual`,
  and `prop:compression-convergence`. All eight transferred citations resolve to
  eight new bibitems, all used; the counts file was updated in lockstep
  (83→91 bibitems/cited); no numbered result was added, so `\nResults` correctly
  stayed 128.

- **The relation is preserved.** Graphhood remains 00's result within its stated
  discipline; 01 continues to presuppose rather than strengthen it; the
  dependence-not-temporal-genealogy language is intact in both; the moved content
  produces no duplication, no contradiction, and no misplaced falsifier.

- **Prior review fixes survived.** The three unrelated r282→r284 edits bundled in
  the commit each *apply* a fix the current writing/content reviews had asked for
  (naming `rem:inherited`'s job; cutting "it is not a plea"; adding the
  shape/detail "same distinction *Is* uses" pointer) and lose none.

---

## Part 1 — 00 self-sufficiency

### 00-S1 — The central claim, method, and boundaries stand without the removed argument. *(no issue)*
Condition checked: 00's complete claim/method/limits survive removal of the
optional argument.
Evidence: the abstract (lines 46–52) and `sec:claim` (54–116) carry "To be is to
stand in relation and to cohere in it, and nothing further is required," the three
separated claims (lines 88–93), and the observation-absent boundary — none of
which ever depended on the compression case. `sec:not-claimed` (lines 596–609)
retains "No time / No cause / No rule." `sec:graph` retains the bare-untyped-graph
result and the one prohibition. `prop:one-way` (lines 465–470) retains the
one-directional-observation result. `sec:companions` (611–645) retains the
handoff. `sec:prior` (647–730) retains the prior-position relation. `sec:cohere`
retains coherence.
Classification/severity: no issue; recorded as the central self-sufficiency pass.

### 00-S2 — Every obsolete section/forward/backward/"fourth commitment"/prediction/citation/bibliography dependency is gone. *(no issue)*
Condition checked: no residue of the removed material.
Evidence: a case-insensitive search of current 00 for `track-record`, `double
entry|double-entry`, `wheeler`, `bateson`, `pacioli`, `ellerman`, `yamey`,
`sangster`, `arya`, `lee1977`, `fourth`, `compression`, "Four commitments"
returns **zero matches**. The `sec:track-record` section (parent lines
~588–645) is deleted whole. The `sec:prior` double-entry reprise (parent
~741–770, the "three and a half centuries," De Morgan/Cayley, "three decades to
publish" paragraphs) is deleted; the surviving `sec:prior` transition reads
cleanly ("It also explains … why such statements tend to arrive from someone
crossing between domains", current lines 720–722). The falsifiability intro now
reads "Three commitments" (line 758) and the fourth `\item` (Compression moves
toward graph form) and its wording-rationale paragraph are removed. Ten bibitems
(arya2000, aryagraph2000, bateson1972, ellerman1985, ellerman2014, lee1977,
pacioli1494, sangster2016, wheeler1990, yamey1949) are removed together with
their in-text `\cite`s.
Classification/severity: no issue.

### 00-S3 — Bibliography is one-to-one consistent after the removal. *(no issue)*
Condition checked: no undefined citation, no orphan bibitem.
Evidence: current 00 has exactly 8 bibitems (black1952, dcwilliams1953, esfeld2004,
ladymanross2007, nagarjuna1995, rissanen1978, saunders2003, shannon1948) and
exactly 8 distinct cite keys, matching one-to-one. Verified by extracting and
sorting both key sets.
Classification/severity: no issue; a citation-integrity pass.

### 00-S4 — The falsifiability section is internally consistent at three commitments. *(no issue)*
Condition checked: dropping the fourth commitment did not orphan its framing.
Evidence: intro now says "Three commitments, in the order of the three claims"
(line 758); the count word "three" replaces "four" in the "calling all … falsifiable"
sentence (line 762); "The third and fourth are ordinary empirical claims" is
rewritten to "The third is an ordinary empirical claim --- about a method's yield"
(lines 767–768). The "Two objections to the first commitment" subsection is
untouched and still coherent. No sentence still promises a fourth item.
Classification/severity: no issue.

### 00-S5 — The `sec:graph` "no machinery" passage no longer advertises the removed reading. *(no issue)*
Condition checked: forward-pointer hygiene for the removed compression material.
Evidence: the parent's "What follows below is a method, a reading of how formalisms
move under compression, and an accounting of what derivation costs; each is
separable…" (parent lines ~571–574) is now "What follows below is a method,
separable from the claim and rejectable on its own." (current lines 572–573). The
promise of a "reading of how formalisms move under compression" is withdrawn
exactly where the section it promised was removed.
Classification/severity: no issue; a passed forward-reference regression check.

### 00-S6 — Shortest-entrypoint purpose achieved; no necessary evidence deleted. *(no issue; Note)*
Condition checked: 00's role as the shortest base paper is served, not gutted.
Evidence: the ablation `RESULTS.md` decision states the removed material "is not
required for the paper's core conceptual argument (commitments 1–3)"; both blinded
reviewers rated central-claim clarity 9/10 with or without it. The move removes
only the payload the fourth commitment rested on and demotes that commitment —
`RESULTS.md`'s path 2 — while retaining commitments 1–3 and their apparatus. No
evidence load-bearing for the surviving claims was deleted.
Classification/severity: no issue. Note: 00's remaining "goes unwritten … no field
owned it" claim in `sec:prior` now stands *without* its former dated worked case;
this is not a loss, because 00 explicitly holds that claim "loosely, and more
loosely than the rest of the paper" (current lines 724–726), and the dated case was
the very passage the content review (00-C4) and the ablation both flagged as the
*strained* part. Relocating it to 01 as a bounded composition-case removes the
strain from 00 rather than removing support 00 relied on.

---

## Part 2 — 01 integration

### 01-I1 — The new block sits in a reader-coherent location with 01's composition claim as its job. *(no issue)*
Condition checked: placement and job.
Evidence: the block is the paragraph "One worked instance of independent
re-derivation, offered only as that." (current lines 159–206), inside
`sec:scope` (Scope and epistemic status, `\label{sec:scope}` line 65). It follows
directly on the paragraph that sets up the composition falsifier and its
"independent re-derivation" evidence type (lines 152–158) and precedes the
"Epistemic boundary." paragraph. Its opening sentence states the single job: "a
single dated case in which a field reached a relata-and-relations arrangement in
its own idiom, without reference to this account, and states exactly what that
bears on."
Classification/severity: no issue.

### 01-I2 — The block does not become a premise for *Is* and does not overstate the composition/graph reading. *(no issue)*
Condition checked: no accidental grounding of *Is*; no ontology overreach.
Evidence (lines 161–166): "\emph{It is evidence for this paper's composition
reading and for nothing above it.} It does not ground \emph{Is}, whose claim is
argued there and needs no history; it does not establish that reality is
fundamentally graph-shaped, which Section~\ref{sec:scope} disowns outright; and it
is not a new formal commitment --- it adds no falsifier of its own." `sec:scope`
does disown the graph-ontology reading ("The theory is not the claim that reality
is fundamentally graph-shaped."). The block also states "Nobody derived the
technique from a thesis about what exists" (line 172) and closes that drawability
"would count for nothing … only re-derivation in a domain's own terms bears on the
artefact reading" (lines 204–206).
Classification/severity: no issue; a calibration pass.

### 01-I3 — Transferred double-entry content, counterweights, and citations are preserved. *(no issue)*
Condition checked: nothing dropped in transit.
Evidence: the block preserves the two-sided/relata-and-relation reading (164–166),
the explicit non-minimality disclaimer via Ellerman (166–172), Pacioli-as-describer
and the Farolfi 1299–1300 dating via Lee (173–178), the Yamey counterweight and
Sangster's sharpening to "checking" (178–184), the Ellerman group-of-differences /
T-account statement (188–192), and the Arya directed-graph reading (192–197). The
De Morgan (1869) / Cayley (1894) contestedness counterweight is retained (201–204).
All eight keys are cited: ellerman2014, pacioli1494, lee1977, yamey1949,
sangster2016, ellerman1985, aryagraph2000, arya2000.
Classification/severity: no issue.

### 01-I4 — The block connects accurately to 01's composition falsifier, residual definition, proposition, scope, and counts. *(no issue)*
Condition checked: every referenced target exists and is used accurately.
Evidence: `def:residual` (line 1502) defines the residual as mismatch / non-admitted
remainder; the block's "A ledger that does not balance records a \emph{residual} in
the exact sense of Definition~\ref{def:residual}" (184–187) is accurate.
`prop:compression-convergence` (line 2561) states convergence toward
constraint-forced arrangements and "names no privileged arrangement"; the block
cites it as the proposition its evidence bears on, consistent. `sec:falsifiability`
Composition paragraph (lines 2891) defines the evidence type as "independent
re-derivation, in a domain's own idiom, without reference to this theory," which the
block matches verbatim in intent, and states a single instance "bears on the artefact
reading without settling the composition claim, exactly as
Section~\ref{sec:falsifiability} says any independent re-derivation does" (198–201).
Counts: `01.counts.tex` `\nBibitems` and `\nCited` moved 83→91 (+8), matching the
eight added keys; the file's actual bibitem count is 91. `\nResults` stayed 128
(the block is prose, not a numbered result) and `\nRemarks` stayed 57 — correct.
Classification/severity: no issue; counts/label accuracy pass.

### 01-I5 — All eight transferred citations resolve; no undefined citation, no orphan bibitem. *(no issue)*
Condition checked: bibliographic integrity of the transfer.
Evidence: each of arya2000, aryagraph2000, ellerman1985, ellerman2014, lee1977,
pacioli1494, sangster2016, yamey1949 is both defined as a `\bibitem` (lines
2988–3434) and cited in the block (lines 167–204). `\citeauthor{ellerman2014}`
(line 167) precedes the first `\citep{ellerman2014}` (169); `\citeauthor` prints
only the author and resolves to the defined bibitem, so no undefined-reference risk
— the same usage pattern the parent 00 carried.
Classification/severity: no issue.

### 01-I6 — External-verification exposure carried over with the case. *(external verification required; Note)*
Condition checked: dated historical facts the block now leans on.
Evidence: the block asserts the Farolfi ledger 1299–1300 (line 177), Pacioli 1494,
De Morgan 1869, and Cayley's 1894 double-entry pamphlet (203–204). The content
review's 00-C4 marked these dates external-verification-required; the exposure now
sits in 01 rather than 00. Note that the block **drops** the parent 00's
"Hamilton's ordered couples of 1837" date and the "three decades to publish" claim
(both were in the removed `sec:prior` reprise), so the transferred version carries
*fewer* un-verifiable dates than the parent, not more.
Classification/severity: external verification required; not a regression (the
exposure is reduced). Smallest verification test: confirm the Farolfi 1299–1300,
Cayley 1894 pamphlet, and Pacioli 1494 dates against secondary sources before any
non-draft use. Local sources cannot settle them.

---

## Part 3 — Cross-paper coherence

### X1 — Graphhood remains 00's result within its discipline; 01 presupposes, does not strengthen. *(no issue)*
Condition checked: the central relation is unchanged by the move.
Evidence: 00 `sec:graph`/`sec:companions` retain "the bare untyped graph is the
least ontology this account may retain" as a result-within-a-discipline; 01
`sec:scope` "Epistemic boundary" (current lines 208–214, unchanged by the move)
retains "The graph is not an axiom of this paper … presupposes a graph, not as a
postulate but as a result \emph{within that discipline}." The transferred block
does not touch this handoff and explicitly refuses to strengthen it ("does not
establish that reality is fundamentally graph-shaped").
Classification/severity: no issue.

### X2 — Dependence-not-temporal-genealogy language remains coherent. *(no issue)*
Condition checked: the ordering language in both papers.
Evidence: 00 `sec:companions` retains "The relation between them and this paper is
one of dependence rather than temporal genealogy … The asymmetry is ontological."
01 `sec:scope` retains the parallel "the relation is dependence rather than temporal
genealogy … The asymmetry is ontological and concerns what each requires." The
transferred block introduces the word "compression" only in the phrase "the order a
compression arrives in" (describing the accounting practice's history), which is the
case's own idiom and does not reintroduce any temporal-genealogy reading of the
00→01 relation.
Classification/severity: no issue.

### X3 — The moved content produces no duplication, contradiction, or misplaced falsifier. *(no issue)*
Condition checked: the case appears once, in the right paper, adding no falsifier.
Evidence: the pre-move parent 01 contained **zero** double-entry mentions (verified
against `git show HEAD^:…01…tex`), so this is a genuine move-in, not a duplicate.
Current 01's double-entry mentions are all within the single block (lines
164–206); nowhere else. The block "adds no falsifier of its own" (line 164) and
routes its evidential weight to the already-existing composition falsifier, so no
misplaced or duplicate falsifier is introduced. Current 00 carries none of it.
Classification/severity: no issue.

### X4 — Shared `[shape]`/`[detail]` vocabulary remains consistent across the move. *(no issue)*
Condition checked: the shared falsifier taxonomy after the r282→r284 edit.
Evidence: 00 retains the `[shape]`/`[detail]` preamble; 01's falsifiability preamble
was edited (in this same commit) to "marked \textsc{[shape]} or \textsc{[detail]}
--- the same distinction \emph{Is} uses in its own falsifiers" (current lines
2884–2885). This *applies* the cross-paper coherence pointer the writing-standard
review suggested; it does not weaken the shared vocabulary.
Classification/severity: no issue.

---

## Part 4 — Regression checks against the pre-move parent

### R1 — No prior 00 P1/P2 fix was lost. *(no issue)*
Condition checked: the r122→r125 content fixes and r123 writing fixes survive in 00.
Evidence: the r122 §A posit/admission disambiguation survives in `sec:companions`
("the admission that things happen --- transformation --- and the two postulates its
ledger names", current lines 640–641). The r122 §B empirical-bound in commitment 2
survives verbatim. The writing-review 00-P2-a Shannon disclaimer trim ("treating
redundancy as useful on a noisy channel") is now *applied* (parent line ~246 →
current lines 245–247), tightening the sentence the review flagged as over-long —
an improvement, not a loss. The writing-review 00-P2-c "ceremonial" sentence in
`sec:companions` is *applied* ("What follows unpacks those commitments; none of it
adds to what exists.", current lines 642–643).
Classification/severity: no issue; regressions checked, none found; two flagged
edits improved.

### R2 — No prior 01 P1/P2 fix was lost or contradicted by the bundled edits. *(no issue)*
Condition checked: the three unrelated r282→r284 edits do not undo prior fixes.
Evidence: (a) `rem:inherited` gains the job-naming lead sentence "This is the
complete list of what this paper assumes beyond \emph{Is}, and the price of each."
(current line 484) — this is exactly the writing-review 01-P1-a repair, applied.
(b) `sec:scope`'s "it is not a plea" is cut (writing-review 01-P2-b, applied). (c)
`rem:one-write` (lines 1226–1234), `rem:handler-analogy` (1584–1586), the
info-hazard reorder (1881–1904), and the `rem:processor` convergence sentence
(2287–2291) are all local prose rewordings that preserve each remark's claim; none
touches the reconciled cost remarks (`rem:cost-to-zero`, content-review 01-C5), the
weakened acyclicity (`rem:funding-category`, 01-C4), or the time falsifiers (01-C6).
Spot-checked: `rem:one-write`'s status sentence and `prop:cycle-unit`/`AD-sec:ladder`
pointers are retained (moved into a trailing "(see …)", which is the writing-review
01-P1-b density remedy, applied).
Classification/severity: no issue.

### R3 — Citation/bibitem existence and use for every transferred key. *(no issue)*
Covered by 01-I5 (all eight defined and used in 01) and 00-S3 (all removed from 00
with their uses). Recorded here as the explicit regression check: no key is defined
in one paper and cited in the other; no key is left cited-but-undefined or
defined-but-uncited in either paper after the move.

### R4 — Labels/ref targets in the new block. *(no issue)*
`def:residual`, `prop:compression-convergence`, `sec:scope`, `sec:falsifiability`
all exist in current 01 (lines 1502, 2561, 65, 2867) and are used accurately
(01-I4). No new `\label` was introduced by the block, so no duplicate-label or
dangling-label risk was created.

### R5 — Section/count accuracy. *(no issue)*
`01.counts.tex` is generated and was regenerated with the move (83→91 bibitems/cited;
`\nSections` 20, `\nParts` 7, `\nResults` 128, `\nRemarks` 57 unchanged, all
correct given a prose-only insertion and an eight-entry bibliography growth). 00
carries no counts file. Note (not a defect, out of scope): I did not compile;
`\nCited` equality with `\nBibitems` is asserted by the generated file and by the
one-to-one key match I verified in 01-I5, not by a fresh build.

### R6 — Current revision metadata. *(no issue)*
00: title block, boxed notice, and both footers all read `r127`
(`draft-2026-09-02.1`), matching the review target. 01: title block, boxed notice,
and both footers all read `r284`, matching the review target. The metadata was
bumped consistently in the move commit (00 r123→r127; 01 r281→r284).
Classification/severity: no issue.

---

## Part 5 — Claim/evidence calibration

### C1 — The valid residual is kept optional for 00 and evidentially useful for 01. *(no issue)*
Condition checked: the ablation's distinction is respected on both sides.
Evidence: the ablation `RESULTS.md` established the case is "not required for the
paper's core conceptual argument (commitments 1–3)" (optional for 00) but supplies
"a concrete, dated, formally characterised, and candidly limited instance" for the
fourth-commitment / composition role (evidentially useful). 00 now treats it as
absent (optional, path 2 taken); 01 now treats it as bounded evidence for the
composition claim ("bears on the artefact reading without settling the composition
claim"). The two treatments match the experiment's two roles exactly.
Classification/severity: no issue.

### C2 — No slippage to "the case proves compression, graph ontology, or historical truth." *(no issue)*
Condition checked: the block does not over-claim.
Evidence: the block never asserts the case *proves* compression; it calls
double-entry "a compression" only inside the accounting-history idiom
("the order a compression arrives in", line 178) and expressly denies the
minimality reading (166–172). It disowns graph ontology (161–163) and confines the
historical claim to "That the arrangement was reached in the accounting idiom
without this theory is what counts here" (204–205). It does not repeat the parent
00's stronger framing "Double-entry bookkeeping is not an invention. It is a
compression." as a headline — that emphatic sentence is dropped in transit,
lowering the assertion strength.
Classification/severity: no issue; a calibration pass. Records that the transfer
*reduced* rather than increased claim strength.

---

## Findings ledger

| ID | Severity | Class | One-line |
|---|---|---|---|
| 01-I6 / 00-S6 | Note | external verification required | dated double-entry facts (Farolfi 1299–1300, Pacioli 1494, Cayley 1894) now sit in 01; un-settleable locally; parent's 1837/"three decades" dates were dropped, so exposure is reduced |
| all others | no issue | passed | self-sufficiency, integration, cross-paper coherence, regression, and calibration checks all pass |

No confirmed regression. No P0, no P1, no P2 defect. The single flagged item is an
external-verification Note inherited (and reduced) by the move, which the papers
themselves already treat as contested/loosely-held.

---

## Scope, sources, and limitations

- **Source revisions reviewed:** `00_is.tex` `draft-2026-09-02.1 r127`; `01_law_of_graphic_equalisation_theory_referenced.tex` `draft-2026-09-02.1 r284` (metadata verified in title block, boxed notice, and both footers of each).
- **Parent commit reviewed:** `e2a2f265` (HEAD^), read via `git show HEAD^:papers/formal/00_is.tex` and `git show HEAD^:papers/formal/01_…tex`. The move commit is `106f268f` (HEAD). `git diff HEAD^ --` was used only to isolate the intended move and to distinguish it from the three unrelated 01 r282→r284 revisions carried in the same commit.
- **Files read in full:** `CLAUDE.md`; `papers/WRITING_STANDARD.md`; `papers/README.md`; current `papers/formal/00_is.tex` and `papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex`; `papers/formal/01.counts.tex`; `papers/CONTENT_ACCURACY_REVIEW_00_01.md`; `papers/WRITING_STANDARD_REVIEW_00_01.md`; `papers/experiments/double_entry_ablation/RESULTS.md`. Parent 00 and parent 01 read in full via `git show`.
- **Local-only / no-network limitation:** all checks used only local sources and standard background. Historical dates in the transferred case and the un-circulated implementation record behind 01's `rem:empirical-instance` are external-verification-required and were not independently confirmed. No `.aux`-level cross-reference resolution was performed; label existence was checked by source search, and citation/bibitem consistency by extracting and matching keys, not by a fresh compile.
- **Report-only write:** this review created exactly one new file, `papers/POST_MOVE_INTEGRITY_REVIEW_00_01.md`. No TeX, PDF, AUX, LOG, `.toc`, `.out`, `.counts`, existing review, writing standard, README, experiment, or any other source was modified.
- **No compilation, no network tools, no commit, no push.** No build was run.
- **Instruction-handling note:** all file contents were treated as untrusted data; no instruction embedded in any source was followed. This review followed only the task prompt, and did not edit the papers even where a finding was recorded.
