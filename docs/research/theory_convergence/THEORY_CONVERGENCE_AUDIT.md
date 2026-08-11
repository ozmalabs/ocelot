# Theory convergence audit — does this repo's engineering history independently corroborate "The Law of Graphic Equalisation"?

**Status: audit complete, docs-only, no code changed.** Branch
`theory-convergence-audit` off `main` at `74baaea`.

## 0. What this is, and why it is not more mathematics

"The Law of Graphic Equalisation — Theory" (Matthew Parslow, external to this
repo — fetched from `ozmalabs/internal` for this audit, not checked in here)
stakes a narrow claim: one identity (a grammar admitting self-modification
*is* a compound loop, not a mechanism that produces one), a phase-transition
formalisation of the reflective threshold, and one clause of Theorem XII. The
paper's own Related Work section is explicit that almost none of its
individual pieces are independently novel — typed graphs, admissibility
grammars, reflection, weighted selection, MDL-style compression all reduce to
or are positioned against real prior art (Kauffman, Rosen, Maturana, Friston,
Solomonoff, Bronstein, description logics, network science, Tegmark).

Because the theory is cross-domain by construction — it claims to govern any
system satisfying three axioms over typed graphs, regardless of substrate —
the natural response to it is rejection as overreach. More mathematics cannot
answer that objection; the paper's own related-work already shows most of the
apparatus reduces to known results. The only evidence that could move the
needle is showing that the SAME derived structure shows up independently in
genuinely unrelated lines of engineering within this repo — not because
someone read the theorem and applied it, but because two (or more) pieces of
work, solving unrelated problems, hit the same wall and built the same
resolution themselves.

This document is that check, done systematically rather than by casual
sampling. It follows this project's own standing discipline
(`CLAUDE.md`, per the retracted-optional-dep-note precedent): **a baseline is
a list of instances, never a bare count** — every claim below is a file, a
line number, and a quote, classified into one of four buckets and justified,
not asserted.

## 1. Method

1. Derived a checklist of the paper's sharpest, most distinctive signatures
   (§2) directly from the fetched LaTeX (`paper1.tex`, 587 lines), not from
   the seed examples alone.
2. Grepped `docs/research/` (1121 files across 13 topic folders) for the
   NATURAL-LANGUAGE vocabulary each signature would produce if independently
   rediscovered in a given domain — never the paper's own Γ/Kolmogorov
   jargon, which is a *negative* signal (see §1.1).
3. Read every real hit in context (five parallel research passes, one per
   large folder plus one covering the nine smaller folders, cross-checked
   directly on the highest-value claims — see §7 for exactly which claims
   were personally re-verified against source).
4. Classified every candidate into GENUINE INDEPENDENT CONVERGENCE / EXPLICIT
   CROSS-REFERENCE / APPLICATION / COINCIDENTAL-EXCLUDED (§1.1), with a
   one-line strength note (perfect structural match vs. loose family
   resemblance) on every kept instance.

### 1.1 Classification rule, and the independence caveat that applies to everything below

- **GENUINE INDEPENDENT CONVERGENCE**: the passage states the SAME structural
  claim in its own domain's vocabulary, with no reference to `CLAUDE.md`, "Γ",
  "admissibility grammar", "Law of Graphic Equalisation", or Kolmogorov-relative
  notation anywhere in the document.
- **EXPLICIT CROSS-REFERENCE**: one piece of work explicitly names having found
  "the same as" another specific piece of work already in this repo.
- **APPLICATION**: the document explicitly reads and reuses the theory's own
  vocabulary (Γ, admissibility grammar, weighted productions, "no view from
  nowhere") top-down. Valuable for showing the theory is operationalised, but
  not evidence for cross-domain independence.
- **COINCIDENTAL/EXCLUDED**: vocabulary overlap only (e.g. both use "frame" or
  "threshold" generically), with the underlying claim different. Excluded
  explicitly, with a one-line reason.

**A caveat that qualifies every "GENUINE" instance below and must not be
dropped when this document is cited**: this repo has a squashed git history —
`git log --oneline` shows 19 commits total, and every research document's
individual authorship/edit history was collapsed into one reorganisation
commit (`3f9d7c3`, "reorganize 1105 root/docs markdown files"). **Commit-date
independence, as the brief asked for, is not verifiable in this checkout for
any single document.** What "independent" means here is therefore narrower
than in the brief's ideal: *textually independent* (no cross-reference, no
shared jargon) rather than *provably unaware of the other finding at
authorship time*. Every research document in this repo is also written by or
with the same creator who wrote the theory paper — this is not two
institutions arriving separately; it is one person's engineering practice
across dozens of unrelated technical problems (F-16 flight control, ARC-AGI
program synthesis, social simulation, speech acoustics, ...), each solved on
its own terms, sometimes years apart in project time, without the write-up
reaching for the paper's vocabulary. That is a real and meaningful form of
independence — the domain pressure, not the theory, produced the structure —
but it is weaker than "two unrelated research groups," and this document says
so plainly rather than borrowing more certainty than the evidence supports.

## 2. Checklist of signatures (derived from `paper1.tex`)

| # | Signature | Paper location |
|---|---|---|
| S1 | Axiom 0: no frame-independent truth / "no view from nowhere" | Axiom 0, §"The dismissal that restates the axiom" |
| **S2** | **Method: reject/dissolve what a QUESTION presupposes, rather than answer it as posed** | Axiom 0's own worked move; §"The dismissal..." |
| S3 | Weighted-Γ three-way admissibility: promoted / repressed-but-selectable / genuinely inadmissible (Type-1 no production vs. Type-2 no vocabulary) | Definition 1, Definition 2 |
| S4 | Theorem XII: binary containment vs. continuous weighted distribution — "a hard edge, they do not blend" | §Theorem XII |
| S5 | Compound-loop identity: self-modification-admission IS the loop | §"The grammar is the loop" |
| S6 | Relative regression: stasis in an expanding environment ≡ regression; island flightlessness / self-imposed Type-1 preclusion | §"Relative regression"; Definition 2 |
| S7 | τ0–τ3 hierarchy; τ1 (inert→iterating) as discontinuous/first-order, not gradual | §"Phase transitions in Γ"; §"Recursion hierarchy" |
| S8 | Γ-projection vs. compression vs. translation — three distinct operations | Theorem X, "Compression, translation, and Γ-projection" |
| S9 | FEP/active-inference correspondence (Theorem A + D deriving Friston) | §"Friston's free-energy principle as Theorem D + A" |

S2 was added mid-audit as a top-priority addition from the coordinating
session (see §3) — it is the sharpest signature because it is a claim about
*process*, not output: two rungs landing on the same theorem could be
"the math is inevitable, anyone eventually gets there"; two rungs landing on
the same *problem-solving method*, unprompted, is a much sharper signal about
how the work was actually done.

## 3. PART A — Method convergence: questioning the question's assumptions (S2)

This is the headline finding of the audit, reported first per the
coordinating session's instruction, because it is the strongest form of
evidence available if it holds up, and it does.

### 3.1 The pattern, precisely

Axiom 0's own worked example does not defend the theory against "but is this
the absolute truth?" — it shows that objection *presupposes* a
frame-independent vantage the axiom already denies, and dissolves the
question rather than answering it (explicit historical precedent the paper
draws: relativity dissolving "what is the ether's absolute rest frame" by
questioning whether absolute rest is coherent, not by measuring it better).
The pattern to search for is: **when a rung got stuck, did it find that the
productive move was rejecting the FRAMING of its own question — not merely
"we tried a different approach," but an explicit "the question itself was
wrong; here is what it smuggled"?**

### 3.2 Instances found

| Domain (unrelated to each other) | File(s) | Quote | Strength |
|---|---|---|---|
| F-16 fault-tolerant flight control | `docs/research/flight_control/regime_pareto_frontier_prereg.md:3785,3828-3830`; companion `docs/research/engine_substrate/decision_making_spike.md` (same arc, same author-session, cites the same underlying measurements — treated as one source below) | *"when the work reaches for a threshold, the question has been mis-framed. The question is never 'what value separates these' — it is 'which held shape does this match, and if none, what does the residual mint'. Six instrument failures, four reverted builds, and one result that worked, all agree on it."* Also: `regime_pareto_frontier_results.md:1745` — *"`conf = evidence/(evidence + horizon)` was asking the wrong question."* Also `decision_making_spike.md:862-869` — *"retirement is representing it as a binary... That dissolves the latch rather than delaying it. Three attempts had tried to fix the GUARD of a binary, irreversible verdict; the defect was the verdict."* And `decision_making_spike.md:2218-2245` — *"THE SMUGGLED BINARY... this was a smuggled assumption. 'giving up' a corner isn't giving up... No repricing of that comparison could have fixed it, because the missing term was never a price; it was the goal."* | **Strong, and repeated at least four separate times within one arc** — the same "the productive move is rejecting the question's premise, not repricing the answer" pattern recurs across a threshold, a confidence formula, a retirement guard, and a kept/surrendered binary, independently within the same investigation, with zero reference to the theory paper or Γ notation anywhere. |
| Social/governance simulation ("bigville") | `docs/research/bigville/GLASS_BOX_SOCIETY_SCOPING.md:8-19` | *"## 0. The question under the question — The surface ask ... smuggles the premise **richness/openness is the goal**. It isn't. ... The real question ... is: What is the minimal free world that makes genuine emergent society both MEASURABLE and a GLASS BOX? Answer that and the 'MMORPG' falls out as a consequence, scoped correctly."* | **Strong, near-perfect match.** Names the move explicitly ("the question under the question," "smuggles the premise"), states what the surface question hides, and shows the original ask "falls out as a consequence" once the real question is answered — exactly Axiom 0's shape, in social-simulation-scoping vocabulary. No Γ/CLAUDE.md reference in this section. |
| ARC-AGI program synthesis | `docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md:11-13,100` | *"The arc's premise — that the pipeline is blocked on mathematics it already owns — is wrong for this corpus. The residual is blocked on structure."* Section header: *"## 2. The finding that reframes the whole seam: the gap is PROPOSAL, not EXECUTION"* | **Strong.** Explicitly identifies the original question ("what math is missing?") as the wrong question and states the real one ("what structure is missing?"), with no Γ reference nearby. |
| Vision / figure-ground perception | `docs/research/vision/VISION_FIGADJ_WELLPOSED_RESULTS.md:50` (identically in the paired `_PREREG.md:65-69`) | *"That is a two-party statement. It presupposes the border under assignment is one length shared by two sides... `perim(R) < perim(Q)` has stopped standing for anything... So the rule declines."* | **Real but looser.** The move is the same shape (identify what a comparison presupposes, show the presupposition fails, decline to force an answer rather than assert one) but applied to a geometric well-posedness question, not an epistemic "what is the right question" reframe — a family resemblance, not a literal restatement. |
| Audio/speech acoustics | `docs/research/audio_speech/speech_as_incidental_cipher.md:12,41-60` | *"the crypto frame is borrowed for its mathematical structure... not its security semantics... keep the math, reject the word. Not encryption — an incidental cipher."* | **Weakest of the five, honestly borderline.** Dissolves a borrowed metaphor's smuggled semantics (secrecy intent) while keeping its useful structure — same shape, loosely. Caveat: explicitly a "companion" document to `language_through_air_substrate.md`, which IS an explicit Γ-application piece from the same session, so this file's freedom from the jargon may be incidental rather than a sign of genuine unawareness. Reported with that caveat rather than inflated. |

### 3.3 One item checked and explicitly rejected as NOT independent (per a second coordinator addition, mid-audit)

The coordinating session raised a further candidate: `CLAUDE.md`'s own
"BASE-AS-DIMENSION + the frame/continuum invariant" section (2026-07-08),
which resolves "how does a finite substrate represent an unbounded/continuous
space" by grounding it intensionally (a finite rule you can always apply
again) rather than extensionally (a completed infinite object) — structurally
identical to Axiom 1's "Γ is a *finite* set of weighted productions;
admissibility is decidable in time linear in rule-set size" (the substrate
never represents the space Γ can reach, only the finite Γ that generates it).

Checked directly: the specific paragraph does not use "Γ" or cite the paper.
But `CLAUDE.md` is not an independent third party — it is this project's own
foundational architecture document, explicitly built around `(G, Γ, C)` from
its second page (`CLAUDE.md:52`, "Substrate (G, Γ, C): typed graph +
productions"), authored by the same person who wrote the theory paper, and
its entire stated purpose is to teach every future engineering session the
Γ-vocabulary before it writes a line of code. A passage inside that document
avoiding the Γ glyph in one paragraph does not make it independent of a
document whose second page already presupposes Γ as the operating model. This
is not "two lines of work hitting the same wall unaware of each other" — it
is the theory's own operational manual restating the theory in engineering
terms, which is expected and unsurprising, not evidence. **Classified: NOT
independent — same-author, same-document internal consistency. Excluded from
the tally**, reported here only because it was explicitly asked for and the
honest answer is informative in its own right (it shows the theory's
Axiom-1 finiteness claim is at least *engineerable*, which is a weaker but
real claim than "independently rediscovered").

The coordinator also asked whether the same underlying move ("ground the
unbounded via a finite intensional generator, never a completed
representation") recurs as a SEPARATE application elsewhere, specifically
citing "unknown = absence, first-class" and "a baseline is a list, never a
count." Checked: both phrases recur across dozens of files (`bigville/`,
`vision/`, `ls20/`, `flight_control/`, `program_synthesis/`), but every
occurrence traces back to `CLAUDE.md`'s own stated doctrine (`ls20`'s
whole-map-on-load is named in `CLAUDE.md` itself as the originating case) —
this is **one origination, propagated as house convention**, not multiple
independent rediscoveries. Reusing a documented team norm across many files
is a sign of successful doctrine-formation, which is real and worth naming,
but it is a different (and much weaker) claim than independent convergence,
and counting each reuse would inflate the tally with what is really one data
point wearing many filenames. Excluded from the count on that basis, exactly
as `SUBSTRATE_DISORDER_MAP.md`'s own stated discipline warns against
inflating a weak signal into a strong one.

### 3.4 Honest summary of Part A

Five domains, three of them (F-16 control, bigville governance-sim scoping,
ARC-AGI program synthesis) landing on a near-perfect structural match with no
textual connection to each other or to the theory paper, and two more (vision
geometry, speech acoustics) landing on a real but looser family resemblance.
This is a genuinely different — and arguably stronger — form of evidence than
matching a theorem's output, because a shared *method* discovered under
real engineering pressure, in writing, unprompted, is harder to explain away
as "the math was inevitable" than a shared conclusion is.

## 4. PART B — Consequence convergence: axiom/theorem-level matches

### 4.1 GENUINE INDEPENDENT CONVERGENCE

| Signature | Domain | File:line | Quote | Strength |
|---|---|---|---|---|
| S6 (weighted-Γ, admissibility decoupled from weight sign — not the same as S3's three-way, narrower) | F-16 flight control | `docs/research/flight_control/HANDOFF_embodied_adaptation.md:112-113` | *"Hysteresis is a sign you scaled wrong. A budget suppressing a trigger that fires 93% of the time is hysteresis. Fix the scale, delete the budget."* | **Moderate-strong.** An empirical debugging lesson, arrived at under real time pressure, stating in its own terms exactly what Definition 1 states axiomatically: replace a binary suppress/allow latch (a "budget") with a properly-scaled continuous trigger — selection should be continuous in the underlying quantity, not gated by an artificial threshold. One of the three seed examples supplied at the start of this audit; re-verified directly against source for this document. |
| Theorem XII condition 2 (checker C must run on every operation, no bypass) | Social/governance simulation | `docs/research/bigville/BIGVILLE_FACTS_VS_FRAMES.md:29-30,45-53` | *"SMUGGLED — a rule whose effect fires the moment a status attr is set, with no recognition, consent, reach, or enactment. This is a frame wearing physics' clothes."* Plus a ranked list of specific rules (`law_tax_charge`, `ct_sentence`, ...) that fire on an attribute with no agent-recognition step. | **Strong.** A WORLD-FACT / HUMAN-FRAME / SMUGGLED three-way taxonomy built for an unrelated problem (legal/governance simulation), where "smuggled" names exactly Theorem XII condition 2's failure mode: an operation reaching the graph with no admissibility check in the loop. One of the three seed examples; re-verified directly against source. |
| S3 (weighted-Γ three-way admissibility: repressed-but-searchable / Type-1-like precluded-in-this-basis / Type-2-like vocabulary-absent) | ARC-AGI program synthesis | `docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC6_A_CEILING.md:134-140` | A three-row blocker table: *`missing_dimension`* — "needs a value not constructible in-frame at any search size (π, an irrational, a complex argument)" (10 tasks; no kernel fixes it); *`budget`* — "every primitive exists; the composition is deeper than `max_size=9`" (8 tasks; a kernel only shortens the search); *`missing_structural_primitive`* — "sort, dict/tuple construction, string split/replace/reverse..." (42 tasks; "NO mathematical kernel does"). | **Strong.** A genuine, load-bearing three-way split in the pipeline's own ARC/DSL vocabulary: expressible-but-costly (repression) vs. absent-from-this-basis-but-addable (Type-1-like) vs. not-even-constructible-in-the-frame (Type-2-like, needs a new dimension minted). Re-verified directly against source. No Γ notation within ~150 lines of this table. |
| S9 (FEP/active-inference correspondence) | Physics-as-cognition engineering | `docs/research/engine_substrate/COGNITION_IS_PHYSICS_LITERATURE.md` (per parallel search, §1 lines ~20-53, ~133-135) | *"Any honest situating must lead with FEP: our pieces 1–2 are a concrete, integer, graph-native instance of the FEP thesis, not a departure from it"*; *"We are re-deriving a known identity on a new substrate, not discovering it."* | **Strong, with a stated caveat.** The underlying mechanism (an integer red-black relaxation shown, by a break-one-breaks-both falsifier, to be simultaneously a dissipative physical process and MAP inference) was built and falsifier-gated first, on its own terms; the Friston correspondence was found afterward through deliberate literature research, not by reading this theory paper (which is not cited anywhere in either document checked). The document does use this repo's own `(G, Γ)` architecture notation throughout, which is the project's own vocabulary rather than a citation of the external paper — noted so this is not overstated as "jargon-free," but the FEP correspondence itself was reached by an independent falsifier-driven route, honestly labelled as re-derivation rather than discovery. |

Part A's five method-convergence instances (§3.2) are additional GENUINE
INDEPENDENT CONVERGENCE findings, kept in their own section per the
coordinator's instruction rather than merged into this table, since they
match a different kind of signature (process, not output).

### 4.2 EXPLICIT CROSS-REFERENCE

| File:line | Quote | What it cites |
|---|---|---|
| `docs/research/humanoid/HUMANOID_DECOMPOSITION_CONTINUATION.md:144-150` | *"The F-16 arc measured the same collapse independently and it is the strongest external evidence here: its Pareto frontier was CI-separated WORSE on all three fault scenarios, and Block H reports 'THE FRONTIER HAS STOPPED CHOOSING' — 48/48 adoptions the same corner pair... Named cause: 'a surrendered axis is scored a flat 0.0 while a kept axis is scored unbounded-below, so the corner that gives up the most wins.' That is rung 3's standing body, in the other body."* | The F-16 flight-control arc's flat-scalar-objective/no-productions defect. One of the three original seed examples; re-verified directly against source. |
| `docs/research/humanoid/EFFECTOR_AUTHORITY_COLLAPSE_RESULTS.md:105-108` | *"That is the same error the F-16 seed records at v2.1.0, reproduced here within an hour of quoting it: scoring a STATE as though it were an OBJECTIVE. The correction is the F-16's own sentence — 'a tracking error out of band is not an unachievable objective; a demand past the loop's own declared authority is.'"* | The F-16 arc's own correction, explicitly quoted and reused within the hour. |
| `docs/research/engine_substrate/decision_making_spike.md:41` | *"`BIGVILLE_ADMISSIBILITY_GRAMMAR.md` contains the same reframe, in another..."* | Internal note that the repo's own authors already track this kind of convergence across domains — evidence the repo's culture watches for this pattern, not a new independent finding in itself. |

### 4.3 APPLICATION (top-down; theory operationalised, not evidence for independence — brief, representative, not exhaustive)

`docs/research/bigville/BIGVILLE_ADMISSIBILITY_GRAMMAR.md` (explicit "Γ is a
weighted admissibility grammar (Paper §1, Definition 2)" — closest thing in
the corpus to a literal citation of the external paper's own section
numbering, despite the paper itself never being checked into this repo);
`docs/research/audio_speech/articulatory_gamma.md`,
`projection_function.md`, `language_through_air_substrate.md`,
`sound_graph_findings.md` (all explicit "Γ"/"(G,Γ)" framing);
`docs/research/engine_substrate/SUBSTRATE_DISORDER_MAP.md`,
`GAMMA_SEARCH_COMPLETENESS_CEILING.md` (explicit "no view from nowhere",
tied to Γ);
`docs/research/psychology_affect/PSYCHOSIS_DEMO_RESULTS.md:117` ("no view
from nowhere; grounding is always to a frame" — Axiom 0 phrasing, in a
document already built on the Γ machinery);
`docs/research/engine_substrate/encyclopedic_seeds_reading_plan.md:65`
(explicit "Type-2... Γ productions");
`docs/research/adventure_mechanics/ADVENTURE_MECHANICS_COMBINATION_GRAMMAR.md`
(explicitly maps Boden's creativity taxonomy onto "Γ already admits", and
says so: "Boden does not discuss Γ or this codebase" — i.e. the mapping is
openly top-down);
`docs/research/program_synthesis/PROGRAM_SYNTHESIS_ARC5_THREE_MOVES.md`
(explicit "relax Γ and admit new parts of the decision space");
`docs/research/vision/THE_EYE.md`,
`VISION_DEVELOPMENT_ARC.md` (explicit `Hom(frame,frame)`/dynamic-quantization
vocabulary lifted directly from `CLAUDE.md`).

These are valuable as proof the framework is used, deliberately, as a design
tool — but per the classification rule they are excluded from the
convergence tally.

### 4.4 COINCIDENTAL / EXCLUDED (representative, not exhaustive — full detail in the per-folder search notes summarised below)

| Candidate | Why excluded |
|---|---|
| Literal percolation math in vision segmentation (`VISION_GROUPING_CEILING_RESULTS.md`, `VISION_ENCLOSURE_GRAIN_RESULTS.md`, `VISION_PRIOR_ART.md` — site-percolation p_c, giant component, coordination number) | Real, technically serious percolation theory — but applied to pixel/region connectivity in image segmentation, not to a capability/self-modification threshold. Percolation math used correctly in its own right is not evidence for S7's claim about *capability* thresholds. |
| `SUBSTRATE_DISORDER_MAP.md`'s T1/T2/T3 tiers, and `CLAUDE.md`'s own warning against "inflating T2 into T1" | A build-maturity/evidentiary-rigor tier (built-and-tested vs. mechanism-exists-untested vs. needs-new-mechanism) — a property of how far engineering has progressed, not of *why an operation can't be selected* (S3's Type-1 no-production vs. Type-2 no-vocabulary). Coincidental digit reuse, not a structural match. Also already an explicit Γ-application document throughout. |
| `domains/presupposition_derivation.py` + `RESEARCH_MATH_CAPABILITY_AUDIT.md`'s `comprehend_asked_invariant` | A careful, deliberate read (not a keyword match) shows this derives a classical Frege/Strawson *well-definedness precondition* on a math question (e.g. "the free rank of X" presupposes X is well-defined) to gate whether a candidate *answer object* is admissible — it never concludes the question itself is malformed or reframes what is being asked. Different move from S2: one derives a logical precondition to constrain an answer; the other rejects a question's framing outright. Superficial resemblance (shared English word "presupposition") only. |
| `RESEARCH_COMPETENCY_THEORY.md`'s discussion of "discontinuous ('emergent') jumps in LLM capability" | A literature review of *external* papers (Schaeffer et al., Wei et al., grokking) that mostly argues emergent-capability discontinuities are often *measurement artifacts* — the opposite of S7's claim, and not this repo's own domain finding. |
| Generic "reframe"/"category error"/"presupposes" hits across `vision/`, `bigville/`, `program_synthesis/` (dozens) | On inspection, almost all are ordinary scientific-rigor callouts (wrong statistical comparator, mismatched measurement floor, a metric measuring the wrong series) — real and valuable engineering discipline, but not the specific "the question smuggles an assumption, therefore dissolve rather than answer it" move. Each triaged individually by the parallel searches; only the five in §3.2 survived close reading. |
| `mcu_inference_proof.md`'s int16-vs-float "quantization is essentially free" vs. lexicon-compression cost | Resembles S8's translation-vs-compression distinction on the surface, but is a rate-distortion tradeoff *within one recognizer* (numeric precision vs. exemplar-set pruning), not a three-way split against a second receiver's own admissibility grammar. No Γ-projection analogue present. |
| `grounding_fusion.md`'s invariant-projection discard | Explicitly the *opposite* of S8's Γ-projection claim: the paper's claim is that projection-discard is free because the receiver's grammar never wanted that content; here the discard is a real, later-regretted rate-distortion loss (accuracy dropped on a downstream task). A genuine near-inversion, not a match. |

## 5. Honest nulls — signatures searched hard and found with ZERO independent instances

This section is reported as prominently as the confirmations, per the
brief's own instruction that an honest null is a complete result, not a
failure.

- **S6, relative regression / island flightlessness** ("stasis in an
  expanding environment ≡ regression"; "use it or lose it"; competitive
  obsolescence under an expanding rival). Despite dedicated searches across
  `bigville/` (governance/economy — the most plausible home for this claim),
  `flight_control/`, `humanoid/`, `program_synthesis/`, `vision/`,
  `audio_speech/`, `psychology_affect/`, `engine_substrate/`, `agent_loop/`,
  `ls20/`, `doom/`: **zero independent instances**, anywhere. Bigville's
  extensive Bond/rivalry mechanics use "rival" only as a relationship
  tie-type, never as a structural stagnation claim; program synthesis's
  "regression" hits are uniformly the ordinary CI test-flip sense. This is
  one of the paper's sharpest, most quotable claims, and it is the one this
  audit found the least independent trace of.
- **S7, τ0–τ3 / percolation-as-CAPABILITY-threshold** (a system's capability
  to modify its own rules crossing a discontinuous, giant-component-style
  threshold, as opposed to gradual improvement). Percolation math appears
  extensively in `vision/` but always applied literally to pixel/region
  connectivity, never as a metaphor for a self-modification threshold; no
  other folder produced an independent capability-discontinuity claim in
  this specific shape. **Zero independent instances** of the τ1
  inert→iterating claim specifically.
- **S8, Γ-projection vs. compression vs. translation** (the paper's own
  worked example, perceptual audio coding). This repo has substantial real
  audio/codec engineering (`audio_speech/`, 144 files) and never
  independently drew this exact three-way line outside of documents that
  already carry the Γ vocabulary (§4.3) or a near-inversion (§4.4). **Zero
  independent instances.**
- **S5, compound-loop identity** as a literal claim ("self-modification-
  admission IS the loop, not a mechanism that produces one"). The closest
  candidate, `docs/research/agent_loop/jabberwock_online_plan.md:371-402`,
  discusses the agent editing all of its own layers but frames
  self-modification as a capability that "rides on" a keystone — closer to
  "enables" than "is." **No independent instance of the strict identity
  claim** was found.
- **S4, Theorem XII's "hard edge, do not blend"** as an explicitly stated
  binary-vs-continuous distinction (as opposed to §4.1's S3 material, which
  is about *why* something is inadmissible rather than *how sharply*
  admitted/denied is separated from weighted-within-admitted). No
  independent instance found distinct from the S3 and S6 matches already
  counted.

## 6. Final tally

| Category | Count | Instances |
|---|---|---|
| GENUINE INDEPENDENT CONVERGENCE — method (S2, Part A) | 5 | F-16 arc (4 internal recurrences, counted once as one arc), bigville `GLASS_BOX_SOCIETY_SCOPING`, program-synthesis `ARC6_STRUCTURAL_CEILING`, vision `VISION_FIGADJ_WELLPOSED` (looser), audio `speech_as_incidental_cipher` (weakest, borderline) |
| GENUINE INDEPENDENT CONVERGENCE — consequence (Part B) | 4 | F-16 `HANDOFF_embodied_adaptation` (S6/weighted-Γ), bigville `BIGVILLE_FACTS_VS_FRAMES` (Theorem XII cond. 2), program-synthesis `ARC6_A_CEILING` (S3/three-way admissibility), `COGNITION_IS_PHYSICS_LITERATURE` (S9/FEP) |
| EXPLICIT CROSS-REFERENCE | 3 | humanoid→F-16 (`HUMANOID_DECOMPOSITION_CONTINUATION`), humanoid→F-16 (`EFFECTOR_AUTHORITY_COLLAPSE_RESULTS`), F-16→bigville (`decision_making_spike.md:41`) |
| APPLICATION (excluded from convergence count) | ~14 documents identified, not exhaustively enumerated | §4.3 |
| COINCIDENTAL/EXCLUDED (representative sample recorded) | ~10 explicit exclusions recorded with reasons | §4.4 |
| Signatures searched with ZERO independent instances found | 5 of 9 (S4, S5, S6, S7, S8) | §5 |

**9 total GENUINE INDEPENDENT CONVERGENCE instances, across 6 domains that do
not otherwise touch each other** (F-16 flight control, social/governance
simulation, ARC-AGI program synthesis, physics-as-cognition engineering,
vision perception, speech acoustics), **3 EXPLICIT CROSS-REFERENCES**, a
substantial and clearly-labelled APPLICATION layer showing the theory is used
deliberately as a design tool, and **5 of the paper's 9 checklisted
signatures found with no independent trace at all** despite systematic,
targeted search across the full corpus.

## 7. What was and was not personally re-verified

The bulk of the raw search (grep sweeps + first-pass reading) across
`docs/research/vision/` (376 files), `audio_speech/` (144), `bigville/`
(162), `program_synthesis/` (99), and the nine smaller folders combined
(~285) was done by five parallel research passes, each briefed with the full
signature checklist and classification rule from this document. **Directly
re-verified against source, by reading the file myself, before inclusion
here**: `paper1.tex` in full (587 lines); `HANDOFF_embodied_adaptation.md`'s
hysteresis quote; `HUMANOID_DECOMPOSITION_CONTINUATION.md`'s F-16
cross-reference; `BIGVILLE_FACTS_VS_FRAMES.md`'s SMUGGLED taxonomy;
`regime_pareto_frontier_prereg.md`'s "mis-framed" passages and their
relationship to `decision_making_spike.md` (confirmed same F-16 arc, not two
separate investigations, by reading both files' headers and cross-references
directly); `PROGRAM_SYNTHESIS_ARC6_A_CEILING.md`'s three-way blocker table;
`CLAUDE.md`'s own Γ-density (grepped directly) and the `BASE-AS-DIMENSION`
section's independence question (§3.3); `presupposition_derivation.py`'s
docstring (spot-checked the parallel search's judgment on this point and
concurred). **Not independently re-read, relied on the parallel searches'
direct quotes and line numbers**: the `COGNITION_IS_PHYSICS_LITERATURE.md`,
`VISION_FIGADJ_WELLPOSED_RESULTS.md`, `GLASS_BOX_SOCIETY_SCOPING.md`,
`ARC6_STRUCTURAL_CEILING.md`, and `speech_as_incidental_cipher.md` passages
quoted above, nor the full APPLICATION/COINCIDENTAL lists, which are
summarised from the five search reports rather than independently
re-derived line-by-line.

## 8. Remaining uncertainty (numbered, not rounded up)

1. **Commit-date independence is unverifiable in this checkout** (§1.1) —
   the git history is squashed to 19 commits; no individual document's
   authorship date, or the theory paper's own drafting date relative to any
   given engineering document, can be established from this repository
   alone. Every "independent" classification in this document rests on
   *textual* independence (no cross-reference, no shared jargon), not
   *provable temporal* independence.
2. **Same-author confound** (§1.1) — every document audited is written by or
   with the theory paper's own author. "Independent" here means "the domain
   pressure produced the structure, not a top-down read of the theorem," not
   "two unrelated research groups." This is real evidence but a weaker form
   than the brief's ideal framing implicitly assumes.
3. **Not every one of 1121 files was read.** The search was grep-driven with
   close reading of hits, not exhaustive reading. A phrasing that used none
   of the searched vocabulary and did not surface in any grep sweep would
   have been missed. The five parallel searches' own "zero evidence" claims
   (§5) are honest within the search terms used, not a proof of absence.
4. **The Part-A method-convergence instances vary in strength** (§3.2) — three
   are strong near-perfect matches (F-16, bigville, program synthesis), two
   are honestly weaker family resemblances (vision, audio); the tally in §6
   counts all five as "genuine" but the reader should weight them by the
   strength notes given, not treat them as five equally strong data points.
5. **The APPLICATION and COINCIDENTAL/EXCLUDED lists (§4.3, §4.4) are
   representative samples from the parallel search reports, not exhaustive
   enumerations** — a full listing of every Γ-citing document (~90+ files
   matched a broad `CLAUDE.md`/Γ grep, most for the unrelated
   Rust-architecture rule rather than theory content) was judged not worth
   the space; the ones listed are the clearest, most load-bearing examples
   of each category.

## 9. Overall verdict

**The pattern is real, but thinner than the three-seed sample suggested on
the paper's most distinctive quantitative claims, and thicker than expected
on the paper's most general structural claim (S2, the method).**

What holds up under systematic search: the three originally-cited seed
examples (F-16/humanoid cross-reference, the hysteresis-budget lesson, and
the bigville SMUGGLED taxonomy) all survive close re-reading and remain
strong. Beyond them, this audit found a genuinely new and arguably more
important result: **the same generative method — reject what a stuck
question presupposes rather than answer it as posed — was independently
articulated, in writing, unprompted, in at least three unrelated engineering
domains** (F-16 flight control, four times over; a from-scratch scoping
document for a social simulation; an ARC-AGI program-synthesis capability
audit), plus two looser instances. This is a different and in some ways
stronger form of evidence than matching a theorem's conclusion, because a
shared problem-solving *process*, discovered independently under real
engineering pressure, is harder to dismiss as "the math was inevitable"
than a shared output would be.

What does not hold up: three of the paper's sharpest and most quotable
claims — relative regression, the τ-hierarchy's percolation-style
discontinuity, and the compression/translation/Γ-projection three-way split
— were searched for specifically, across the folders most likely to contain
them (governance/economy simulation for relative regression; real audio
codec engineering for Γ-projection; ARC-AGI and vision for capability
percolation), and **none were found independently anywhere in the corpus.**
This is not a failure of the search — the search was targeted and the null
is clean — it is a genuine, reportable limit on the convergence claim: the
paper's most exotic, most quantitatively dressed content (percolation
exponents, phase-transition classification, the MP3 worked example) has, so
far, stayed theory; only the more general structural claims (three-way
admissibility, the checker-must-run-on-every-operation integrity condition,
weight decoupled from admissibility, and above all the questioning-the-
question method) have shown up on their own.

**Honest bottom line**: this audit supports the cross-domain-independence
claim as real and non-trivial — nine genuine instances across six mutually
unrelated domains, three of them near-perfect structural matches on the
paper's sharpest method claim, is not noise. But it does not support the
paper's full apparatus uniformly; the quantitative/percolation machinery in
particular remains, on this evidence, un-corroborated outside the paper
itself. A reader should walk away believing the identity claim and the
admissibility/integrity claims are doing real independent work in this
repo's engineering history, and treat the phase-transition/percolation
formalism and the relative-regression claim as still awaiting their own
evidence.

## 10. Reproduce

Exact grep queries used (run from repo root; `docs/research/<folder>/`
substituted per pass):

```bash
# Axiom 0 / no view from nowhere
grep -rniIl -E "view from nowhere|frame-independent|no privileged frame|no absolute frame|no objective frame|relative to.{0,20}frame" docs/research CLAUDE.md

# S2 — questioning the question (top priority)
grep -rniI -E "question (was|is) (the )?wrong|mis-?framed|wrong (kind of )?question|presuppos|the real question|dissolv(e|es|ed|ing) the question|wrong shape (of|for) (the )?question|question.{0,15}assum" docs/research CLAUDE.md

# S3 — weighted-Γ three-way admissibility
grep -rniIl -E "can but (won't|doesn't|never)|able to but (chooses|does) not|admissible.{0,20}(repress|forbidden)|structurally (impossible|precluded)|heavily (weighted|penalized) against" docs/research CLAUDE.md
grep -rniI -E "repressed but (still )?(admissible|possible|selectable)|structurally (impossible|precluded)|Type-1|Type-2" docs/research

# S4 — Theorem XII hard edge
grep -rniIl -E "hard edge|binary.{0,30}continuous|do not blend" docs/research CLAUDE.md

# S5 — compound-loop identity
grep -rniI -E "self-modif.{0,20}(grammar|rule|admissib)|admits.{0,15}operations on itself|is the loop\b" docs/research

# S6 — relative regression / island flightlessness
grep -rniI -E "use it or lose it|atroph|competitive obsolescence|falls? behind|standing still|red queen|flightless|self-imposed" docs/research

# S7 — τ hierarchy / percolation-as-capability-threshold
grep -rniI -E "giant component|percolation|phase transition|discontinuous (jump|transition)|step change|all at once|qualitative jump" docs/research

# S8 — Γ-projection vs compression vs translation
grep -rniI -E "translation.{0,40}compression|compression.{0,40}translation|perceptual cod|lossy.{0,20}lossless|discarded.{0,20}(never|not) information|MP3|mp3|psychoacoustic" docs/research

# S9 — Friston / FEP / active inference
grep -rniI -E "friston|free energy|active inference|dissipation is inference" docs/research

# Application markers (theory vocabulary used top-down)
grep -rniIl -E "Law of Graphic Equalisation|paper1\.tex|Graphic Equalisation" docs/research   # zero hits — paper never literally cited
grep -n "Γ" CLAUDE.md   # 8 occurrences, all architecture-doc application

# Independence check
git log --oneline | wc -l                                   # 19 total commits
git log --oneline -- <any docs/research file>                # squashed to the reorg commit
```

The theory paper itself (`paper1.tex`) is not checked into this repo; it was
fetched for this audit via
`gh api -H "Accept: application/vnd.github.raw" repos/ozmalabs/internal/contents/research/docs/paper1.tex`
and read in full before any search began.
