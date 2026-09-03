# Writing-standard review — `00_is.tex` (r123) and `01_law_of_graphic_equalisation_theory_referenced.tex` (r281)

Scope: a read-only review against `papers/WRITING_STANDARD.md` (with `book/BOOK_VOICE.md`
and `papers/README.md` as register companions), not a general peer review. No claim is
assessed for truth; only whether the prose meets the binding communication standard for
formal papers. Line ranges are to the current sources at the revisions named above.

---

## Executive verdict

**00 (`Is`, r123).** Meets the standard to a high degree and is close to a model application
of it. The claim is stated first and plainly (`sec:claim`), the one place to disagree is named
and pushed to the top rather than buried (`\emph{The disagreement belongs here and not several
pages later.}`), the method is committed-hard-held-soft with an explicit asymmetric outcome, the
not-novelty posture is honest, and the falsifiers distinguish kinds of claim rather than flattening
them. The defects are local: one governing-idea payoff that is split across two very dense abstract
sentences, a few sentences whose causal path is longer than the standard's sentence-level rule
allows, and one reference (`shannon1948`/`rissanen1978` pairing) that is correctly disclaimed but
whose disclaimer runs long enough to compete with the point it supports. No P0. Two P1s, both about
sentence-level path length and one paragraph transition; the rest are P2 optional edits.

**01 (Theory, r281).** Meets the standard's *substance* — reader-first ordering at the document
scale, the claim/mechanism distinction, honest arrangement posture, hard-held-soft commitments with
an unusually disciplined falsifier list — but strains the standard's *continuation* and *coherence*
gates at the paragraph and remark scale. The paper is a self-described reference work
(`sec:scope`, "Level of the claims"/"What kind of document this is"), and its own economics is
invoked to justify the length; that defence is legitimate under the standard's register discipline.
The genuine writing-standard failures are (a) several remarks that open on machinery before naming
the job the remark does, against the "say that job early" rule, and (b) a recurring
back-reference density (`Remark~\ref{...}` chains) that raises the cost of continuation above the
cost of reconstruction for a first-time reader — the exact inversion the standard forbids. These are
real but bounded, and none conceals a claim. No P0. Several P1s concentrated in Part III (economics/
residual) and the ledger remark; the balance are P2.

The two papers share a path (00 is the base, 01 begins after it and inherits graphhood as a result),
and that shared path is mostly handled well — 01's `sec:scope` "Epistemic boundary" and ledger are
faithful to 00 — with one cross-paper coherence snag noted in the final section.

---

## Paper 00 — `Is` (r123)

### P1 — direct, but minor

**00-P1-a. Governing payoff split across two dense abstract sentences.**
Lines 52–58 (abstract). The abstract's load-bearing sentences run:

> "Observation is not primitive here, and it is not derived here either --- it is \emph{absent}, and
> the companions derive it, in accounts that posit what deriving it takes. So what merely stands in
> relation cannot observe, and, where nothing contains it, cannot be observed either, only modelled,
> and nothing in this account waits on anything looking."

Diagnosis: against *"Sentence and clause — prefer shorter causal paths; if a sentence has several
logical steps, make the dependency explicit or split it."* The second sentence chains four steps
(cannot observe → where nothing contains it → cannot be observed → only modelled → nothing waits)
through nested commas, and the reader must hold the "where nothing contains it" condition across the
whole chain. The claim is legible on a second pass but not on the first, which is exactly the
continuation cost the standard's Path check targets in the opening.
Minimal repair/test: split at "So what merely stands in relation cannot observe." Test: a new reader
should be able to restate the abstract's claim after one read; if the "observed/modelled" distinction
requires re-reading, the split is warranted. This is a direct violation of a sentence-level rule but
low-severity because the surrounding sentences carry the claim.

**00-P1-b. Unnamed transition into `\subsection*{One operation, applied to what came bundled}`.**
Lines ~322–335. The subsection pivots from "remove a posited entity" to "decline an inherited
restriction" with the opener *"The operation is stated above as removing posited structure ... but its
more productive target is different, and is the same operation pointed the other way."* The relation
is stated, which is good, but the paragraph that follows raises "trivial and consequential ... and are
both" before the reader has been given the yield limit that makes the pairing safe; the limit ("severe
... returns nothing on almost every attempt") arrives a paragraph later.
Diagnosis: against *"Keep every promise short-range — a question raised in a paragraph should receive a
local answer or an explicit signpost."* The "trivial and consequential" claim opens a question (is this
a machine for producing results?) whose answer is deferred one paragraph.
Minimal repair/test: add a half-clause signpost at the "are both" sentence pointing forward ("the limit
that keeps this from being a recipe is stated next"), or move the one-sentence yield statement up.
Test: can a reader state, at the end of the first paragraph, why the operation is not a results
machine? Currently not until the second.

### P2 — optional edits

**00-P2-a. Reference disclaimer longer than the point it guards.**
Lines ~299–303 (Shannon/Rissanen). *"\citet{shannon1948} supplies that measure and \emph{not} the
norm, containing no model selection and treating redundancy as useful on a noisy channel, so citing
the two together for the norm borrows a name that did not make the claim."* This is exactly the
standard's *"Reference check — retain and explain the ones that carry coherence"*; the disclaimer does
carry a structural step (it prevents the reader crediting Shannon with the norm). It is admissible.
Optional: the clause "treating redundancy as useful on a noisy channel" is the one piece not needed to
make the point and could go, tightening the sentence to its load-bearing half. Not a violation.

**00-P2-b. `sec:one-way` "no view from anywhere" repetition.**
Lines ~470–520. The section states "no view from nowhere, and no view from anywhere either" and the
surrounding paragraphs re-derive the same conclusion (frame needs someone else's instantiation) three
times in slightly different words. Against *"one motion per paragraph."* The repetitions are doing
mild reinforcement of a genuinely counterintuitive point, so this is optional rather than a violation;
if trimmed, keep the "for want of anything doing the viewing" formulation, which is the sharpest.

**00-P2-c. Casual-register opportunity taken well; one place it is not.**
`sec:track-record` and `sec:prior` use the standard's licensed casual moves cleanly ("the dumbest one
available: what is there?"). By contrast `sec:companions` line ~? ("What those commit to together is
then unpacked at length, and the unpacking is not further claims about what exists.") is ceremonial
where a plainer "what follows unpacks those commitments; none of it adds to what exists" would carry the
same relation. Optional, per *"keep the most casual wording that preserves the exact relation."*

### What 00 does that the standard explicitly asks for (recorded so it is not "improved" away)

- Claim first, disagreement-point named and elevated (`sec:claim`, lines ~78–96): textbook
  application of *"Withhold mechanism, never the claim"* and *"the disagreement belongs here."*
- The verbs paragraph (lines ~155–168) pre-empts the tense/sequence misreading — this is the standard's
  *"Introduce a term before relying on it"* applied to the metatheory's own vocabulary.
- Falsifiability (`sec:falsifiability`) refuses to call the conceptual commitment "falsifiable" and
  says why (borrowed credential) — a direct instance of *"Do not replace a commitment with a mood of
  caution"* held from the honest side.

---

## Paper 01 — Theory (r281)

### P1 — direct

**01-P1-a. Ledger remark opens on machinery, not its job.**
`rem:inherited`, lines ~470–545 (the long `\begin{remark}[What this paper postulates over \emph{Is}]`).
The remark is the paper's accounting spine, but it opens: *"The ledger is Table~\ref{tab:ledger}. The
prose after it is why each entry sits where it does ..."* then immediately runs into a defence of naming
vs counting before the reader knows what the entries *are*. The job ("here is everything 01 adds to 00,
and what each addition cost") is inferable but not stated early.
Diagnosis: against *"Give every section one job and say that job early"* and the paragraph rule
*"start from what the reader already holds."* A reader arriving from 00 holds "00's claim plus the
admission that things happen"; the remark could name that as its subject in the first sentence.
Minimal repair/test: lead with one sentence naming the remark's job ("This is the complete list of what
01 assumes beyond `Is`, and the price of each"), then the table, then the naming-vs-counting note. Test:
Path check — can a reader state what the remark establishes from its first two sentences? Currently the
first two sentences are about how to read the table, not what it says.

**01-P1-b. Back-reference density inverts the continuation cost in Part III.**
`sec:interface` economics remarks, especially `rem:one-write` (lines ~1160–1195), `rem:third-cost`
(~1290–1320), and `rem:aperture-purchased` (~1240–1285). Representative:

> "the prepayment of Remark~\ref{rem:cost-to-zero} in mechanism. From the time side it is one cycle,
> however much change it does (Proposition~\ref{prop:cycle-unit}); from the recognition side it is the
> first rung of the adaptability paper's ladder (its Section~\ref{AD-sec:ladder}) ..."

Diagnosis: against the governing obligation *"Make continuation cheaper than reconstruction"* and the
Continuation check. Three or more cross-references in a single sentence force the reader either to hold
several unresolved pointers or to leave the page; both raise the cost of the next step above the cost of
reconstructing the argument locally. The individual references each carry a real structural step (this is
not decoration, so it is not a Reference-check violation), but their *density* is the defect — the prose
stops pathing and starts indexing.
Minimal repair/test: for each such sentence, keep the one reference that supplies the mechanism the
sentence turns on and demote the others to a trailing "(see also …)" or drop them where the companion
paper already carries the point. Test: read each remark cold and ask whether a first-time reader can take
the next step without following a reference; where the answer is no, one reference is load-bearing and the
rest are optional.

**01-P1-c. `rem:handler-analogy` states its own hedge before its content.**
Lines ~1560–1600. Opens: *"The mechanism for that indexing settles what would otherwise look like a
family of competing answers, and the useful way to see it is by analogy with exceptions --- an analogy,
because the substrate fixes far less than the analogy suggests."* The double-caveat ("an analogy, because
…") lands before the analogy itself, so the reader is warned off a picture they have not yet been given.
Diagnosis: against *"start a paragraph from what the reader already holds; end by changing what they
hold"* — the paragraph starts by qualifying an object not yet in hand.
Minimal repair/test: give the analogy first ("A frame that rejects a write raises; the failure goes up
until something handles it"), then the boundary ("read it as an analogy: the substrate fixes only that an
inadmissible write yields no continuation in that frame"). Test: Coherence check — the transition into the
paragraph should be nameable as "example," and currently it is "scope-before-example."

**01-P1-d. `sec:crossings` result-first promise is kept, but the supporting order raises a local
suspense the standard discourages.**
Lines ~1690–1720. The section correctly states its result first (*"Its result, stated first."* →
information hazard is a signed capability change) — this is good and standard-compliant. But the very
next paragraph ("The same machinery qualifies what an information hazard is …") reopens the definition
before `Definition~\ref{def:info-hazard}` is reached, so the reader holds a stated result and a "we will
now qualify it" without the definition between them.
Diagnosis: borderline; against *"Long suspense without a receipt is debt."* Short-range here (the
definition follows within the page), so this is the mild end.
Minimal repair/test: move `def:info-hazard` up to immediately follow "stated first," then let the
qualifying paragraphs run. Test: is there any point between the stated result and the definition where the
reader is asked to hold the result unresolved for more than a paragraph? Currently one.

### P2 — optional edits

**01-P2-a. Abstract's second paragraph buries a strong plain claim in a subordinate clause.**
Lines ~64–66: *"several things ordinarily treated as background turn out to be constructed rather than
given --- a privileged standpoint from which to measure, and time itself, among them."* The claim (time
is constructed) is the reader's payoff and is delivered as an aside ("among them"). Per *"Open with the
reader's payoff,"* this could be promoted to its own sentence. Optional because the abstract's first
sentence already states the composition claim, which is the paper's primary payoff.

**01-P2-b. "What kind of document this is" is well-argued but slightly over-defends.**
`sec:scope`, lines ~200–235. The length-defence ("A normal paper reports a result inside an established
framework … installation is paid in pages") is exactly the register discipline the standard licenses for a
framework-installing document, and it is not a violation. However the paragraph *"That is this account's
own economics applied to its own reception, and it is not a plea."* protests slightly against an objection
not yet raised. Per *"Delete apologies and ceremonial padding"* — this is not apology, but "it is not a
plea" is the kind of pre-emptive self-defence the Tone check would flag. Optional: cut "and it is not a
plea"; the argument stands without it.

**01-P2-c. `rem:processor` "how much weight this carries" digression.**
Lines ~2360–2410. The remark's core (engineers were forced to these arrangements; the convergence is
about constraints, not vocabulary) is strong and standard-compliant. The middle passage separating
"vocabulary is borrowed and carries no weight" from "what is not borrowed" is doing real work but is
stated twice (once abstractly, once in the four "nobody wanted" cases). Optional trim per *"one motion per
paragraph"*; keep the four concrete cases, which are the payoff, and compress the abstract statement above
them.

**01-P2-d. Falsifiability list — the "counted four times" note is a model; one entry could name its job
earlier.**
`sec:falsifiability`, the four-references-one-risk note (lines ~2790–2800) is an exemplary application of
*"Check both ends of every claimed gradient"* and honest arrangement. Optional: the `[detail]`/`[shape]`
preamble (lines ~2660–2668) repeats verbatim the same paragraph that appears in 00's falsifiability and in
01's own `rem:inherited` neighbourhood; a reader reading the set encounters it three times. Since the papers
are explicitly not assumed to be read linearly (`sec:scope`), the repetition is defensible; if trimmed
anywhere, trim the third instance, not the first.

### What 01 does that the standard explicitly asks for (recorded so it is not "improved" away)

- Reader-first at document scale: `sec:scope` gives the claim (composition), the not-novelty posture, the
  epistemic boundary, and the falsifier of the whole before any machinery. Direct application of *"Give the
  reader the familiar result or question first; give the machinery that makes it necessary second."*
- Claim/mechanism distinction held throughout: e.g. `prop:no-free-lunch` states the claim as an observed
  universal and explicitly refuses the prohibition form, naming why (*"stating it as a prohibition would
  give it a quantifier over all frames that no one can discharge"*). This is *"committed hard, held soft"*
  done exactly.
- Not-novelty / attribution: `sec:prior-art` and the Wolfram and Wheeler paragraphs lead with what is
  established and size the delta precisely — *"Lead with what is established, borrowed, or shared."*
- Falsifiers named with scope, counterweight, and the shape/detail cost distinction — the standard's
  Commitment check is satisfied unusually thoroughly.

---

## Cross-paper coherence (shared path 00 → 01)

The papers share one path: 00 establishes the bare untyped graph as "the least ontology this account may
retain," and 01 begins after it, inheriting graphhood *as a result within that discipline* rather than as
a postulate. That handoff is executed well and consistently:

- 00 `sec:companions` (lines ~? ) and 01 `sec:scope` "Epistemic boundary" state the dependence-not-genealogy
  relation in near-identical terms, and both explicitly forbid the temporal reading. This is coherent and
  is the standard's *"Arrange sections so that each answers a question raised by the preceding"* operating
  across documents.
- 00's ledger admission ("two unpaid entries, not one") matches 01's `tab:ledger` and `rem:inherited`
  ("one of two unpaid entries, the other being `Is`'s claim that there is anything at all"). The count is
  consistent across both sources.

**One cross-paper snag (P2, coherence).** Both papers carry the identical `[shape]`/`[detail]` preamble
paragraph (00 `sec:falsifiability` line ~902; 01 `sec:falsifiability` lines ~2660–2668) and both carry the
"idealisation is a frame, named and restorable" argument (00 `sec:method`; 01 `rem:idealising`, which
correctly attributes it to *Is* `sec:method`). 01's attribution is exemplary — it points to 00 rather than
restating as its own. The residual snag is only that the shared `[shape]`/`[detail]` paragraph appears
verbatim in both without either naming it as shared vocabulary the way 01 names the idealisation argument.
For a reader moving 00 → 01 this is a mild redundancy rather than an incoherence; the fix, if wanted, is a
one-clause pointer in 01 ("the shape/detail distinction *Is* uses in its own falsifiers") mirroring how
`rem:idealising` handles the idealisation criterion. This resolves rather than creates a coherence problem
and is optional.

No cross-paper contradiction was found. The shared path improves coherence more than it costs.

---

## Verification block

- **Files read in full:** `papers/WRITING_STANDARD.md`; `book/BOOK_VOICE.md`; `papers/README.md`;
  `papers/formal/00_is.tex` (all 1117 lines); `papers/formal/01_law_of_graphic_equalisation_theory_referenced.tex`
  (all 3335 lines). `CLAUDE.md` was located and searched (not read in full: 69 KB, and its content is an
  engineering/project guide, not prose-writing directive material beyond the "competent man" ethos already
  carried in `BOOK_VOICE.md`); the search confirmed it contributes no additional writing-standard rule.
- **Document revisions at review time:** `00_is.tex` — `draft-2026-09-02.1 r123` (title block line 15,
  boxed notice line 28, footer lines 20/23). `01_..._theory_referenced.tex` — `draft-2026-09-02.1 r281`
  (title block line 33, boxed notice line 45, footer lines 37/40). Revisions match the review request
  (00 r123, 01 r281).
- **Report location:** `papers/WRITING_STANDARD_REVIEW_00_01.md` (new file, created by this review).
- **Read-only confirmation:** No TeX, PDF, AUX, LOG, `.counts`, or existing review file was modified. No
  compile was run. No commit was made. No existing `WRITING_STANDARD_REVIEW*` file existed prior to this
  one (verified by directory listing). Line ranges are given to the current sources; where a range is
  marked with `~` it is approximate to the paragraph, and the quoted snippets are verbatim from the current
  revisions for exact location.
- **Method note:** The review evaluates against named rules in `WRITING_STANDARD.md` (Governing idea; The
  core posture; Coherence is scaffolded and pathed — whole document / section and paragraph / sentence and
  clause; Narrative is a service to the reader; Attribution, references, and novelty; Register discipline;
  Revision gates). No defect was recorded that is not tied to one of those rules, and optional edits are
  distinguished from direct violations throughout.
