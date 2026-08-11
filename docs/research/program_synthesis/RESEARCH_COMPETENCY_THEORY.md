# Competency composition theory: literature spike + repo mapping

**Research spike, 2026-08-01. No code changed. This document is the sole artefact.**

The user's theory, formalised: (1) **composition** — any competency = core (domain-general) ×
specialised (domain-specific codebook); (2) **opacity** — you cannot infer the composition from
one distribution's performance; (3) **the cliff** — high specialisation collapses off-distribution;
(4) **metacognitive transfer** — high metacognitive function acquires new competence fast by
reusing core and only expanding codebooks. Refinement under test: **core sets the floor/flatness,
specialised sets the ceiling/cliff** (specialised≈0 still scored 7%, not 0%).

---

## 0. How to read this document

### 0.1 Evidence grades (convention from `RESEARCH_CODE_IN_THE_BRAIN.md` §0.2, applied here)

| Grade | Meaning |
|---|---|
| **[A]** | Multiple independent labs/traditions, converging methods, adequate power, or a large/preregistered design. Safe to build on. |
| **[B]** | One strong line of work (good design, n adequate) with partial independent support, OR a single very large/authoritative source (e.g. a benchmark paper with its own large-n human study). Build on with a hedge. |
| **[C]** | Single study/single-lab research program, small n, contested interpretation, or something I could not independently verify via fetch and am reporting from training knowledge. Treat as a hypothesis. |
| **[D]** | Contested, failed to replicate, or an accepted null presented as a positive finding. Do not build on. |

### 0.2 The standing rule this spike is required to apply (§11 of `RESEARCH_CODE_IN_THE_BRAIN.md`; the CLAUDE.md 2026-07-21 optional-dep retraction)

**A claim quoted without its condition is the recurring failure mode of this whole research
program.** Two instances matter directly for this document, and both are corrected in place
rather than silently:

- **The Omniglot "26.8%" figure named in the task brief is itself a superseded, condition-stripped
  number.** It was the *powered, honest* re-measurement of an *n=80* trajectory that had wrongly
  risen to 41.2% — a real and important correction (§3.3 below) — but it is **not the tree's
  current standing number**. A later change to the *verdict comparator* (not more data, not more
  specialised content) raised the same task to 73.5%, then 80.5% [76.3, 84.1] n=400 (`OMNIGLOT_ARC.md`
  §1). Quoting 26.8% as "the" Omniglot cliff, full stop, would repeat exactly the defect this repo's
  own standing rules exist to prevent. §3.3 and §4 report both numbers with their conditions.
- **MBPP "0.42%"** is reported by its own source document as an overestimate in the *other*
  direction: the one nominal pass was coincidental (`Var(a)` happened to satisfy both held-out rows
  by chance), so *"this baseline's true zero-shot capability count is arguably 0/257, not 1/257"*
  (`PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md`). I quote 0.42% because it is the artifact-registered
  number, but flag that the honest floor is likely exactly 0%, which if anything *strengthens* the
  cliff claim.

### 0.3 A methodological caution that recurs across the whole literature review below

Several of the strongest-sounding claims here come from **one dominant research program** (Veenman
and colleagues for claim 4's correlational studies; Ericsson's group vs. the
Hambrick/Macnamara/Oswald group for deliberate practice; Sala & Gobet for far-transfer nulls). Per
the same logic `RESEARCH_CODE_IN_THE_BRAIN.md` applies to the Siegmund-vs-Fedorenko dispute:
**when one lab dominates a literature, check whether disagreement tracks method/baseline choice,
and downgrade a grade if independent replication is thin.** I've applied this below — but for
claim 4 specifically it does **not** produce a uniform downgrade, because (per a correction applied
mid-spike, §0.4) several of its strongest pieces of support turn out to sit in **entirely
different, mutually-independent literatures** (classical learning-set research, multilingual
acquisition, sport-science sampling studies) that never cite Veenman and were not run to test this
claim at all — convergence across unrelated traditions is stronger evidence than replication within
one.

### 0.4 Corrections applied mid-spike (recorded, not silently edited in — this repo's own convention)

Two corrections arrived from the coordinator while this document was being drafted. Recording them
here, per `RESEARCH_CODE_IN_THE_BRAIN.md` §11's own precedent, because a plan or report that
quietly re-aims is indistinguishable from one that was never wrong.

**Correction 1 — claim 4 is a LONG TAIL, not a quick burst.** My first draft treated claim 4 as
"high metacognition → a burst of fast initial learning" and, following the task brief's own framing
("most attractive, most likely inflated"), searched for and weighted evidence accordingly. The
correct reading is different and stronger: **strong core/operator function keeps paying across
many successive domains, indefinitely, with each new domain costing less because the operators are
already held and only the codebook needs expanding.** This matters methodologically, not just
rhetorically: a brief-intervention, single-target-domain, immediate-posttest design (which is what
nearly the entire far-transfer meta-analytic literature, Sala & Gobet included, actually runs)
**cannot distinguish a real long-tail effect from a real null**, because it never measures a
second, third, or Nth domain, and never measures rate (slope) rather than a single post-test level.
§1.4 below is rewritten around this design distinction, not just re-weighted.

**Correction 2 — the primary case study is the builder, not the codebase.** I had been treating
this repo's own operator-reuse findings (ShapeDecode, Viterbi decode, the sd loop,
propose-render-compare, transferred across ink/speech/vision/characters/code/roles) as the case
study. That evidence stands (§2.2), but the actual, stronger N=1 case is the **person**: a systems
administrator who built a working cognitive-architecture engine (96k lines of Rust, a running graph
substrate) by integrating graph theory, neuroscience, social science, quantum mechanics, physics,
mathematics and computing — a claim that is unusually checkable, because the borrowed structures
are verifiable directly in source (formal-grammar admissibility rules, signal-processing-style
quantization, a Viterbi decoder lifted from speech processing, cognitive-science meta-shape
vocabulary, a frame/continuum invariant constraining the type system). This is an **inspectable
artifact**, not a self-report of learning speed, which is epistemically a real step up from most
individual-differences evidence in this area — but it is still N=1, and I address directly (§2.5,
§4) what can and cannot be inferred from a sample of one, including the selection-vs-causation
ambiguity the polymathy literature (§1.4.5) independently raises for exactly this kind of case.

---

## 1. Claim-by-claim literature review

### 1.1 Claim 1 — Composition: competency = core × specialised

**What was tested, where.** This is the closest thing to a *formal* research program:
François Chollet, **"On the Measure of Intelligence" (arXiv:1911.01547, 2019)**. Chollet's
framework (verified by direct fetch of the paper) defines four terms — **skill** (task
performance, "heavily modulated by prior knowledge and experience"), **scope** (the range of
tasks skill was measured over), **priors** (innate/built-in assumptions), **experience**
(exposure/training data) — and argues, via an **algorithmic-information-theoretic** framing, that
"unlimited priors or unlimited training data allow experimenters to 'buy' arbitrary levels of
skill... in a way that masks the system's own generalization power." Intelligence is then defined
as **skill-acquisition efficiency relative to priors and experience**, not skill itself. This is
almost exactly claim 1 restated formally: observed skill is a *product* of a general
acquisition-efficiency term and domain-bought content (priors + experience), and the two are
separable only by *design* (holding scope fixed and varying experience, or vice versa). **[B]** —
a single-author framework, but foundational, highly cited, and operationalised into a real,
widely-used benchmark (below), which is the reason it clears single-study status. **Sources:**
Chollet 2019, arXiv:1911.01547.

**Empirically, ARC is a deliberate instrument for testing exactly this.** ARC-AGI (Chollet 2019)
and its successor **ARC-AGI-2** (Chollet et al., arXiv:2505.11831, fetched) are explicitly designed
so that "specialised codebooks" (memorised patterns, brute-force search over a large prior corpus)
do not transfer: tasks use "explicit priors designed to be as close as possible to innate human
priors," and ARC-AGI-2 additionally *removed* every task from the original 2020 Kaggle corpus
"susceptible to brute force search" specifically because prior systems' apparent skill on ARC-AGI-1
turned out to be partly a specialised-search artifact, not a core-reasoning one. The publicly
reported trajectory (ARC Prize Foundation's own announcements, **not independently re-derived by
me from a numeric table** — WebFetch could not extract the interactive leaderboard's chart data, so
grade this **[C]**, widely corroborated by press but not independently verified here): o3 at high
compute reached ~87.5% on ARC-AGI-1's semi-private eval (Dec 2024) vs. GPT-4o-class models around
5%, while on ARC-AGI-2 (2025) the *same* frontier models scored in the low single digits, with a
human panel around 60% and 100% of tasks solvable by at least two humans. If corroborated, this is
essentially the field's own instrumented version of "the same stack, a shifted distribution,
performance falls off a cliff" — i.e., an external, non-corpus-specific replication of what this
repo's MBPP/internal-battery gap already shows internally (§3, §4). **Grade the *design rationale*
[B]** (verified primary-source text) and **the specific percentages [C]** (press-corroborated, not
independently re-derived here).

**Second tradition: transfer-of-learning research directly tests whether "core" (general) transfer
exists at all, separate from "identical elements" (specialised) transfer.**
- **Thorndike & Woodworth (1901)**, the founding identical-elements result (confirmed via
  Wikipedia fetch): transfer is "restricted or assisted by the elements in common" between tasks —
  i.e., transfer is *proportional to shared surface content*, the opposite pole from a
  content-free "core." **[A]** as a historical anchor (near-universally cited, effect replicated
  informally for over a century), though the original methodology is dated.
- **Barnett & Ceci (2002), "When and where do we apply what we learn? A taxonomy for far
  transfer," *Psychological Bulletin*** (confirmed via Crossref) proposed the standard **near vs.
  far transfer taxonomy** along multiple independent dimensions (knowledge domain, physical/
  temporal/social/functional context, whether the target modality/format differs). This taxonomy
  is the closest published analogue of the composition claim's *shape*: transfer distance is
  multi-dimensional, not a single "close/far" scalar, which is exactly what "core × specialised"
  implies if you decompose "specialised" into several independent codebook axes rather than one.
  **[B]**.
- **Detterman's contrarian position** — *"The case for the prosecution: transfer as an
  epiphenomenon,"* in Detterman & Sternberg (eds.), *Transfer on Trial: Intelligence, Cognition,
  and Instruction* (Ablex, 1993) — argued that most transfer effects in the literature are
  measurement artifacts of experimenter-selected similar tasks, and that **real far transfer is
  rare to nonexistent** in the general population; a published exchange (*"Motion for a New Trial
  on Transfer,"* *Educational Researcher*, 1994, joint Pressley/Yokoi/Detterman/Sternberg piece per
  Crossref metadata) shows this was contested in print at the time. **[C]** — I could not fetch
  the original chapter's text directly (book chapter, no open URL), so this is reported from
  well-established secondary citation, not primary verification.
- **Sala & Gobet's meta-analyses (2016-2019)** are the modern, well-powered continuation of
  Detterman's position and are the single strongest evidence body on this question:
  - *"Does far transfer exist? Negative evidence from chess, music, and working memory training,"
    Current Directions in Psychological Science* (2017, confirmed via Crossref): meta-analytic
    effects for chess/music/WM training on general cognition are "small to moderate" and **shrink
    to near-zero under rigorous controls** (active control groups, blinding).
  - *"Cognitive training does not enhance general cognition," Trends in Cognitive Sciences*
    (2019, confirmed via Crossref): "far-transfer effects are small or null" once publication bias
    and placebo effects are controlled.
  - A second-order meta-analysis (233 studies, PsyArXiv 2018, confirmed via Crossref): **near
    transfer is real; far transfer is essentially zero** once methodology is controlled.
  **[A]** for the *chess/music/WM-training* domain specifically (multiple independent
  meta-analyses, large aggregate n, consistent direction) — this is one of the best-powered
  results in all of psychology on transfer, and it says: **far transfer of a general "core" skill
  from deliberate training is largely a null result** in normal populations under normal training
  regimes. This is an important caution against claim 1/4 as usually intuited (see §1.4).

**Verdict on claim 1.** The formal half (Chollet's skill/priors/experience decomposition,
operationalised in ARC) is well-posed and **[B]**; it says composition is real *by construction*
of the measurement (you can design instruments that separate core and specialised contributions).
The empirical-transfer half is more pessimistic than casual composition-talk usually assumes:
**[A]**-grade evidence says that when "core" is trained directly and "far transfer" is measured
directly (chess, music, WM training), it mostly does not show up. The two literatures are not in
direct contradiction — Chollet's framework never claimed core transfer is *easy* to elicit, only
that it is *measurable in principle* — but anyone building claim 1 into a system design should
know that the strongest empirical transfer literature is a **[A]-graded skeptical result**, not a
demonstration that core competencies transfer freely.

### 1.2 Claim 2 — Opacity: you cannot tell the composition from one distribution

This claim is less a separate literature than a corollary of §1.1 and of the ML "emergent
abilities" debate, so I fold the strongest evidence in here.

- **Schaeffer, Miranda & Koyejo, "Are Emergent Abilities of Large Language Models a Mirage?"
  (arXiv:2304.15004, fetched directly).** Their finding, confirmed by direct fetch: apparent
  discontinuous ("emergent") jumps in LLM capability at scale are largely an artifact of the
  **choice of metric** (nonlinear/discontinuous metrics like exact-match manufacture sharp
  transitions; linear/continuous metrics on the *same underlying model outputs* show smooth
  scaling). They reproduce this on GPT-3-family models, BIG-Bench meta-analysis, and by
  artificially engineering "emergent" curves in vision tasks by choice of metric alone. **This is
  a direct, mechanistic demonstration of claim 2**: from the outside, looking at one scalar summary
  of performance, you genuinely cannot tell whether a system's underlying capability is smoothly
  composed or has a real qualitative discontinuity — the measurement instrument itself can
  manufacture the appearance of either. **[A]** — this is now close to consensus in the ML
  scaling-laws literature (it directly responds to and substantially deflates the earlier **Wei et
  al., "Emergent Abilities of Large Language Models," 2022, TMLR** claim, confirmed by direct
  fetch, that abilities are "not present in smaller models but present in larger models" and are
  "unpredictable" from smaller-scale trends).
- **Grokking (Power et al., "Grokking: Generalization Beyond Overfitting on Small Algorithmic
  Datasets," arXiv:2201.02177, fetched directly)**: networks can memorise (100% train accuracy)
  for a long plateau, then transition to genuine generalisation "long after" the memorisation
  phase — i.e., two qualitatively different internal solutions (memorised lookup vs. the actual
  algorithm) can produce **indistinguishable train-set performance** for an arbitrarily long time.
  This is opacity given teeth: at the point of measurement, you cannot tell from performance alone
  which regime you're in — only a distribution shift (held-out test, or continued training)
  reveals it. **[B]** (single well-cited paper, but the phenomenon has since been replicated
  across several algorithmic-task settings by other groups, so better than [C]).
- **Compositional generalisation benchmarks (SCAN, Lake & Baroni arXiv:1711.00350; COGS, Kim &
  Linzen arXiv:2010.05465; both fetched directly)** are *designed instruments* for claim 2: a
  model can reach 96-99% in-distribution accuracy on COGS (near-ceiling, looks like "it learned the
  competency") while dropping to 16-35% on systematic compositional generalisation splits
  (Kim & Linzen's own reported numbers) — the in-distribution number alone gives **no signal**
  about whether the model holds a compositional "core" rule or a large memorised specialised
  lookup. SCAN's seq2seq models "fail spectacularly" exactly when generalisation requires genuine
  recombination rather than "mix-and-match" surface interpolation. **[A]** — this is a mature,
  multiply-replicated sub-field (Hupkes, Dankers, Mul & Bruni, "Compositionality Decomposed,"
  JAIR 2020, confirmed via Crossref, is the standard survey/taxonomy of these generalisation-gap
  results across many follow-on benchmarks).

**Verdict on claim 2.** Well supported, **[A]** overall. The strongest form of the claim — that a
single in-distribution accuracy number is compatible with radically different underlying
compositions (pure lookup vs. genuine rule) — is now closer to a mechanistic finding than a
hypothesis in ML, and the emergent-abilities-mirage result shows the opacity cuts *both ways*:
apparent smoothness can mask a real threshold, and apparent thresholds can mask real smoothness.
**This directly implies claim 2 is not just true but methodologically dangerous**: the same data
can be read to support "it has a core skill" or "it's all memorised" depending on the metric
chosen, which is exactly why single-distribution performance numbers (this repo's own 64.0%
internal-battery figure, taken alone) cannot answer the composition question — only a
deliberately-varied second distribution can (§4).

### 1.3 Claim 3 — The cliff: high specialisation collapses off-distribution

- **Chase & Simon (1973), "Perception in chess," *Cognitive Psychology*** (confirmed via
  Wikipedia fetch, standard citation) is the founding demonstration and the cleanest possible
  cliff: chess masters' large recall advantage for briefly-viewed *real* game positions
  **disappears** for *randomly arranged* (illegal) positions of the same pieces. This is the
  cliff, measured directly: the specialised codebook (learned chess-position chunks) has **zero**
  transfer value the instant the input leaves its trained distribution (legal, game-plausible
  configurations), while general visual/working-memory capacity (measured by the random-board
  condition) is unaffected. **[A]** — one of the most replicated findings in cognitive psychology.
- **Hatano & Inagaki's routine vs. adaptive expertise distinction** (Hatano, G. & Inagaki, K.,
  "Two courses of expertise," in Stevenson, Azuma & Hakuta (eds.), *Child Development and
  Education in Japan*, Freeman, 1986) is, as the task brief suspected, **the cliff, named as a
  taxonomy**: routine experts are fast and accurate *within* a fixed procedural distribution but
  show **the sharpest collapse** when a novel variant is introduced (the textbook example is sushi
  chefs vs. abacus experts who can compute standard arithmetic at speed but fail on
  restructured/non-standard problems that require the same underlying numeracy applied
  differently); adaptive experts retain flexible conceptual understanding that survives
  distribution shift. **I could not independently verify this citation via fetch** (it is a 1986
  book chapter with no stable open URL, and Crossref search returned only unrelated modern
  citing papers) — **grade [C]**, reported from well-established secondary literature (it is
  cited by hundreds of downstream papers, e.g. the "adaptive expertise" education literature broadly,
  several of which I *did* confirm exist via Crossref: Bohle Carbonell & Dailey-Hebert 2021,
  Asaba 2024, Cernusca/Mallik/Petry 2024, all citing exactly this routine/adaptive framing).
- **Feltovich, Spiro & Coulson's "knowledge brittleness" / Cognitive Flexibility Theory** (Spiro,
  Feltovich & Coulson, multiple 1980s-90s pieces, confirmed titles via Crossref: "Multiple
  analogies for complex concepts," 1989; "Knowledge application and transfer for complex tasks in
  ill-structured domains," 1992; "Cognitive Flexibility Theory," 2013 reprint) is the direct
  mechanism-level account of *why* the cliff happens for specialised knowledge in "ill-structured"
  domains (e.g. medicine): knowledge acquired from a narrow set of well-structured, prototypical
  cases becomes **"reductively biased"** — the learner over-applies a simplified schema and it
  **breaks discontinuously**, not gracefully, the moment a case falls outside the prototype set.
  **[B]** — a coherent, multiply-published research program (single group, but internally
  consistent across a decade of studies), directly analogous to what this repo calls the
  "specialised ceiling/cliff."
- **The ARC-AGI-2 design** (§1.1) and the **SCAN/COGS compositional-generalisation collapse**
  (§1.2) are the ML-side instances of the exact same phenomenon: near-ceiling in-distribution,
  collapse out-of-distribution, by design.
- **A genuine counter-current inside the same literature**: Ericsson's "deliberate practice"
  program (below, §1.4) and the broader expertise literature generally hold that highly
  specialised expert performance is *not* brittle within a *sufficiently broad* trained
  distribution — chess grandmasters do generalise across legal openings they've never
  specifically seen. The cliff claim is therefore best read, and is read in the strongest
  literature (Hatano/Inagaki, Feltovich/Spiro), as being about **distribution edges relative to
  the training set's structure**, not about specialisation per se being fragile everywhere.

**Verdict on claim 3.** **[A]** for the core phenomenon (Chase & Simon is about as solid as
cognitive psychology gets), **[B]/[C]** for the specific "routine vs. adaptive" and "brittleness"
mechanistic accounts of *why* (single-program dominance, thin independent replication located).
The claim survives scrutiny better than claims 1 and 4.

### 1.4 Claim 4 — Metacognitive/core transfer, correctly read as a LONG TAIL, not a quick burst

**Reframing (§0.4, correction 1).** The claim under test is not "high-metacognition people get an
initial burst of fast learning that fades." It is: **strong core/operator function keeps paying
across many successive domains, indefinitely, with each new domain costing less because the
operators are already held and only the codebook needs expanding.** This is a claim about the
**slope of a rate curve across a career-length sequence of domains**, not about a single
post-training test score. That distinction turns out to be the whole ballgame for which literature
is even relevant.

#### 1.4.1 Could the standard far-transfer design detect a long tail at all? — No, and this needs to be said plainly

The dominant evidence I originally weighted heavily against claim 4 — Sala & Gobet's chess/music/
working-memory-training meta-analyses (§1.1, **[A]**-graded, well-powered) — measure a specific,
narrow design: **a short training intervention (weeks to a couple of years) in ONE source
skill, followed by an immediate-to-short-horizon post-test in ONE target domain the participant is
not otherwise trying to learn.** Walk through what this design can and cannot see:

- It cannot observe a **sequence** of domains, so it cannot measure whether the Nth new domain
  costs less than the first — the long-tail claim's actual dependent variable.
- It measures a **passive transfer probe** (an IQ subtest, an academic-achievement score) rather
  than **active acquisition of a real new competency** the person is motivated to and actually
  practising — Barnett & Ceci's own taxonomy (§1.1) explicitly separates transfer along a
  "functional context" dimension (the difference between a lab probe and a real motivated task),
  and nearly all of the meta-analysed studies sit at the "probe" end.
- It uses **short, often immediate, post-test delays** — Barnett & Ceci's taxonomy also names
  temporal distance between learning and test as an independent dimension; the long-tail claim is
  explicitly about effects visible only over years to a career, a temporal range this literature
  essentially never samples.
- Its populations are **unselected trainees** (schoolchildren enrolled in a chess programme,
  general community/student samples for WM training) — **not** people selected for, or engaged
  daily in, high metacognitive or diagnostic function. I looked specifically for a far-transfer
  study using a population selected on prior metacognitive/diagnostic skill (e.g., practising
  systems administrators, experienced clinicians, career troubleshooters) and found none in this
  literature; it is a real, reportable gap, not something I am inferring away a null with.

**Conclusion, stated as a finding rather than a hedge: the best-powered null literature in this
entire review answers a different question than claim 4 asks.** Its nulls are evidence that *brief
training interventions in unselected populations, probed once on an unrelated near-term test, do
not produce detectable far transfer.* They are not evidence, one way or the other, about whether a
long tail of compounding, career-length, actively-practised core-skill reuse exists. This is an
important correction to my first draft, which used this literature as if it bore directly on claim
4; on inspection it is close to orthogonal to the actual claim.

#### 1.4.2 Designs that COULD detect a long tail, and what they found

- **Harlow's learning-set research — the closest classical match to the claim's actual shape.**
  **Harlow (1949), "The formation of learning sets," *Psychological Review*** (confirmed via
  Crossref) and **Harlow & Warren (1952), "Formation and transfer of discrimination learning
  sets," *Journal of Comparative and Physiological Psychology*** (confirmed via Crossref) are
  textbook-canonical, well-replicated findings: primates given hundreds of successive novel
  two-choice discrimination problems get **progressively faster at solving each new one**, until
  performance on brand-new problems approaches one-trial "insight" — not because they memorise
  specific discriminations (each is novel) but because they acquire a domain-general strategy
  ("win-stay, lose-shift," attending to the relevant dimension) that **each new problem
  instantiates cheaply**. This is, almost literally, "operators are already held, only the
  problem-specific codebook entry needs filling," measured across a genuine sequence of
  successive domains, not a single before/after probe. **[A]** — one of the most robustly
  replicated phenomena in comparative/learning psychology, later formalised under Gregory
  Bateson's term **"deutero-learning"** (learning to learn, *Steps to an Ecology of Mind*, 1972
  reprint of 1942 work) — **the literature does have a name for this dissociation**, and it
  predates this project by 75+ years.
- **Multilingual acquisition — a real-world, long-run, ecologically valid analogue.**
  **Cenoz (2003), "The additive effect of bilingualism on third language acquisition: a review,"
  *International Journal of Bilingualism*** and **Cenoz & Hoffmann (2003), "Acquiring a third
  language: what role does bilingualism play?"** (both confirmed via Crossref) review converging
  evidence that **people who already speak two languages acquire a third, unrelated language
  faster than monolinguals acquire their second** — a genuine "second new domain costs less than
  the first" finding, in a real, high-stakes, years-long acquisition process, not a lab probe.
  **Kaushanskaya & Marian (2009), "The bilingual advantage in novel word learning,"
  *Psychonomic Bulletin & Review*** (confirmed via Crossref) shows this experimentally at a finer
  grain: bilinguals learn **novel words in an unfamiliar, invented language** faster than
  monolinguals, under controlled lab conditions — i.e., the effect survives moving from
  observational (Cenoz) to controlled (Kaushanskaya & Marian) designs. **[A]** for the qualitative
  effect (multiple independent labs, both observational and experimental methods converge);
  **[B]** for the specific mechanism (metalinguistic awareness / cross-linguistic transfer skill —
  "the core" here — is the standard explanation, though the precise operator being reused is less
  cleanly isolated than in Harlow's paradigm).
- **Veenman's work, re-read for RATE rather than level (the coordinator's specific ask).** Read
  correctly, Veenman's own titles are about exactly this: "**initial inductive learning** in a
  complex... environment" (2002) and "learning **performance**... in different domains" (2008,
  van der Stel & Veenman) are studies of how fast someone masters a *genuinely novel* task/
  simulation, not how much they already know. The consistent finding across this line (§1.4
  originally reported this with more skepticism than the framing warranted): **metacognitive
  skillfulness — measured behaviourally, from think-aloud/process data, not by questionnaire —
  predicts the SPEED of mastering a new domain, and does so across different domains for the SAME
  individuals within a study**, which is a within-person, cross-domain rate comparison closer in
  spirit to the long-tail claim than a single-domain far-transfer probe. The dissociation from
  self-report (§1.4's original caution, Veenman/Van Hout-Wolters/Afflerbach 2006, still stands and
  still matters) is a caution about **measurement**, not about whether the underlying rate effect
  is real — and it should be read as the field's own quality-control mechanism, not as grounds to
  discount the behaviourally-measured result. **Revised grade: [B]**, up from my first draft's
  implicit downgrade — single-program-dominated, but now correctly understood as evidence about
  rate, and it supports the long-tail claim more directly, not less, once read that way.

#### 1.4.3 The generalist/range tradition, and "kind vs. wicked" learning environments

**David Epstein's *Range: Why Generalists Triumph in a Specialized World* (2019)** synthesises
(rather than originates) evidence that late/broad "sampling" before specialising predicts better
long-run outcomes in several domains — its own primary sources include Hambrick and Gobet (already
covered, §1.1/§1.3) and sport-science sampling research (below). Treat the book itself as **[C]**
(popular synthesis) but its cited primary literature at the grade of its own sources.

**The single most load-bearing idea for this project is Hogarth's kind/wicked distinction:
Hogarth, Lejarraga & Soyer (2015), "The Two Settings of Kind and Wicked Learning Environments,"
*Current Directions in Psychological Science*** (confirmed via Crossref, correcting the
coordinator's tentative co-author guess — the actual authors are Hogarth, Lejarraga, and Soyer).
Their claim: in a **kind** environment, feedback is prompt, unambiguous and representative, so
pattern-based (specialised, "System 1") expertise is reliable and further pattern accumulation
keeps paying off (chess, most sports, most of Chase & Simon's domain). In a **wicked**
environment, feedback is **delayed, sparse, noisy, or actively adversarial** (their own examples
include medicine, and a wicked environment's structure generalises straightforwardly to any
domain where root causes are hidden and symptoms mislead — which is the textbook description of
systems administration, software debugging, and general troubleshooting), so **stored patterns
generalise poorly and are frequently actively misleading**; success there depends more on
**domain-general causal/diagnostic reasoning strategies** that can be re-applied when the
pattern library runs out or actively misfires. **This is a genuinely strong, directly relevant,
[B]-graded (single well-cited framework paper, not yet a mature meta-analytic literature) finding
for claim 4's plausibility conditioned on domain type**: it predicts that operator-heavy,
domain-general reasoning should be *relatively more* valuable, and specialised pattern-codebooks
*relatively less* self-sufficient, in exactly the kind of environment (program synthesis, systems
diagnosis) this project and its builder both work in — which is also exactly the shape of result
the MBPP arcs measured directly (§2.1, §3a): the domain-general search+verdict engine carries
capability, specialised pattern content is thin and sometimes actively costly (the "decoy tax" is
a wicked-environment failure mode, almost by definition — a plausible pattern match that is wrong
and costly to have trusted).

**Sport-science sampling/late-specialisation literature** (a confirmed 2018 chapter, "Single-Sport
Specialization versus Sampling," in *Youth Sports in America*, ABC-CLIO, via Crossref; the
broader "Développement Model of Sport Participation" (DMSP) tradition associated with Jean Côté
and colleagues, **not independently re-verified this session** — reported from established
secondary knowledge, **[C]**) finds that **breadth-first ("sampling") experience across several
related sports in youth, rather than early single-sport specialisation, predicts better elite
adult performance** in many (not all) sports — a domain-general motor/tactical "core" acquired
across several specific "codebooks" (individual sports) transferring to eventual elite
specialisation. Directionally consistent with claim 1/4, though this literature has its own
replication debates (early specialisation is genuinely advantageous in a handful of early-peaking,
highly technical sports like gymnastics — i.e., the effect itself looks environment/domain
conditional, echoing kind-vs-wicked).

#### 1.4.4 Diagnostic/troubleshooting-reasoning transfer — the same dissociation shape as this repo's own findings, not a clean "yes"

This is the coordinator's sharpest specific question: does the kind of domain-general causal/
diagnostic reasoning a systems administrator or troubleshooter practises daily actually transfer
across domains, as opposed to accumulating as domain-specific pattern knowledge? **The literature
here is not thin — it is rich, well-established, and gives a nuanced, not a clean, answer,** and
reporting it honestly matters more than reporting it favourably:

- **Medical differential diagnosis — the "case/content specificity" finding.** **Elstein, Shulman
  & Sprafka (1978), *Medical Problem Solving: An Analysis of Clinical Reasoning*, Harvard
  University Press** (confirmed via Crossref) is the founding large-scale study, and its central,
  since-replicated finding is that **performance on one clinical case correlates only weakly with
  performance on a different case for the same clinician** — expert diagnosticians do not have a
  stable, general-purpose "diagnostic reasoning ability" that travels across cases the way a
  domain-general operator would predict; instead, accuracy is driven heavily by whether the
  specific case content matches the clinician's specific prior case experience. This is, if
  anything, evidence **against** a strong, clean form of transferable diagnostic reasoning, and it
  is structurally the same finding as Chase & Simon's chess result (§1.3) applied to a "wicked"
  domain. **[A]** — this is one of medical education's most robustly replicated findings (surveyed
  repeatedly by Norman & Eva, e.g. their 2009 *Medical Education* piece "Diagnostic error and
  clinical reasoning," confirmed via Crossref, and their long research programme reviewing
  case-specificity across decades).
- **But the same literature identifies a real, if smaller, generic component.** Norman & Eva's own
  broader argument (and the Morris & Rouse (1985), "Review and Evaluation of Empirical Research in
  Troubleshooting," *Human Factors*, confirmed via Crossref, review of the parallel engineering/
  electronics-troubleshooting literature) is that expert performance is **not purely
  content-specific either**: generic strategies (hypothesis generation and testing,
  "half-split" search over a fault tree, systematic elimination) are real, teachable, and used
  across domains by the same people — they are just **not sufficient on their own**, and their
  marginal value is smaller than deep domain content in a "kind-ish" sub-region of the task, but
  **relatively larger** exactly where content runs out (a genuinely novel fault pattern, an
  unfamiliar case presentation) — which is precisely the boundary condition Hogarth's kind/wicked
  framework predicts, and precisely the boundary condition this project's own MBPP arcs measured:
  the domain-general enumerator+verdict machinery is what still functions when the specialised
  proposal content (chunks, retrieval) runs dry or actively misfires (§2.1, §3a).
- **Reading this properly**: the diagnostic/troubleshooting literature does **not** show "domain-
  general reasoning transfers cleanly and dominates" (that would overstate the evidence and ignore
  Elstein/Norman/Eva's central finding) — it shows the **same two-component structure this whole
  document keeps finding everywhere it looks**: a real but comparatively thin domain-general
  strategic layer, and a dominant, non-transferring content layer, with the domain-general layer's
  *relative* importance rising specifically in wicked/novel conditions. This is a substantive,
  citable convergence, and it is more defensible than either a clean "yes, diagnostic reasoning
  transfers" or a clean "no, it's all case-specific."

#### 1.4.5 Polymathy and eminence — suggestive, and explicitly confounded by selection

- **Root-Bernstein, Bernstein & Garnier (1995), "Correlations Between Avocations, Scientific
  Style, Work Habits, and Professional Impact of Scientists," *Creativity Research Journal***
  (confirmed via Crossref) found that scientists with serious avocations outside their specialty
  (art, music, craft, writing) have **higher-impact scientific output** on average, and this line
  of work (Root-Bernstein & Root-Bernstein's broader "polymathy and creativity" programme) is the
  most direct existing evidence for "breadth of domains mastered associates with quality of output
  in any one of them." **[B]** — a real, multiply-published correlational finding from one
  research pairing.
- **Dean Keith Simonton's body of work on creative productivity** (confirmed via Crossref:
  *The Genius Checklist*, MIT Press 2018; *Creative Genius* chapter, *Cambridge Handbook of
  Creativity*, 2019) reaches similar correlational conclusions about breadth/versatility and
  eminence, from an independent research programme — genuine convergence, not single-lab
  replication.
- **The explicit, load-bearing caveat, stated by these researchers themselves, not invented by me
  for balance: this is correlational, and the causal direction is contested.** People with more
  cognitive resources, drive, curiosity, or simply more available time and status may pursue
  *both* breadth *and* high specialised achievement — breadth could be a **marker** of the same
  underlying factor that produces achievement, rather than a **cause** of it via
  operator-transfer. Neither Root-Bernstein's nor Simonton's designs (both observational,
  studying already-eminent populations) can cleanly separate "breadth builds transferable core
  skill that then pays off in the specialty" from "a third factor (drive, resources, raw ability)
  produces both breadth-seeking and specialty eminence independently." **[C]** for the causal
  reading; **[B]** for the correlational finding itself.

#### 1.4.6 Verdict on claim 4 — revised

**Not a clean confirm, not a downgrade — a claim that is better-supported than my first draft
credited, once measured with the right kind of design, and honestly under-tested with the
long-horizon designs that would settle it cleanly.**

- The single best-powered piece of *disconfirming* evidence in my first draft (Sala & Gobet's
  far-transfer meta-analyses) turns out, on inspection of its actual design, to be **near-orthogonal
  to the long-tail claim**, not a strong null against it (§1.4.1) — this is itself one of this
  spike's more important findings, independent of which way claim 4 ultimately goes.
- Where a design genuinely could and did measure something rate-shaped across a real sequence of
  domains (Harlow's learning sets, [A]; bilingual L3 acquisition, [A]/[B]), the evidence
  **positively supports** a long-tail, compounding, core-skill-reuse effect, robustly and across
  independent traditions (§1.4.2).
- Veenman's work, correctly read as a rate measure rather than a level measure, is more supportive
  than my first draft credited, while its known measurement caveat (self-report ≠ behavioural
  skill) remains real and should temper confidence in any given operationalisation, not in the
  underlying phenomenon (§1.4.2).
- Where domain type is factored in (Hogarth's kind/wicked distinction, §1.4.3; the diagnostic/
  troubleshooting literature, §1.4.4), the honest finding is a **two-component structure, not a
  clean transfer story**: domain-general reasoning is real, present, and reused, but it is
  consistently the *smaller* contributor to raw performance and the *relatively more valuable*
  one specifically at the edge of the specialised content's reach — a genuinely close match to
  this project's own measured floor/ceiling refinement (§1.5, §3b), independently arrived at in
  human-cognition research on diagnosis and troubleshooting.
- The polymathy/eminence literature (§1.4.5) is suggestive but explicitly confounded by selection
  in its own authors' telling, and should not be over-weighted as causal evidence.

**Net grade: [B]** for the qualitative long-tail phenomenon (multiple independent, converging
traditions: learning sets, multilingual acquisition, sport sampling, diagnostic-reasoning's
generic-strategy component), **[C]** for any specific causal mechanism ("metacognition" as
usually meant) being the operative variable rather than a correlate of it, and an explicit,
reportable gap (not a null, an **absence**) in the literature that would test it most directly:
**longitudinal, within-person, multi-domain acquisition-rate studies of people whose daily work is
domain-general diagnosis** essentially do not exist. That absence is itself worth reporting as a
finding (Part 4 and the recommended designs, §3c, address how to close it).

### 1.5 The floor/ceiling refinement (specialised≈0 still scores 7%, not 0%)

I did not find a literature that states this **exact** functional form (core sets an additive
floor + limits variance/flatness; specialised sets a multiplicative ceiling + the cliff's
steepness). The closest analogues:

- **Cattell's investment theory (Gf → Gc)**, confirmed via Wikipedia fetch of the CHC-theory page:
  fluid intelligence (Gf, "core") is "a determining factor in the **speed** with which crystallised
  knowledge [Gc, "specialised"] is accumulated" (Cattell, 1963) — i.e., Gf sets a *rate*, Gc sets
  an accumulated *level*. This is structurally close to "core sets the floor/flatness": in
  investment theory, Gf doesn't directly produce domain performance, it produces the *capacity to
  invest* into Gc, which then produces performance. A near-zero Gc (no domain knowledge) with
  normal Gf would, on this model, predict low but non-zero performance via general
  problem-solving applied cold — matching "specialised≈0 → 7%, not 0%." **[B]** for the theory's
  standing (CHC theory is the field's consensus taxonomy), **[C]** for this specific mapping onto
  the floor/ceiling claim (my inference, not a stated result of investment theory).
- **Ackerman's PPIK theory** (Ackerman, "A theory of adult intellectual development: process,
  personality, interests, and knowledge," *Intelligence*, 1996, confirmed via Crossref) extends
  investment theory with personality/interest as additional inputs to how much of the "core"
  capacity gets invested into any given domain's "knowledge" — relevant to claim 4's "why do some
  people acquire new competence faster," since PPIK's answer is partly dispositional (interest,
  typical intellectual engagement), not purely cognitive-metacognitive. **[B]**.
- **The Schmidt & Hunter (1998) "validity and utility of selection methods" meta-analysis**
  (*Psychological Bulletin*, confirmed via Crossref, "85 years of research findings" — this is one
  of the most-replicated results in industrial/organisational psychology) found that **general
  mental ability (GMA) is the single best predictor of job performance and training success across
  virtually all jobs**, and — the part relevant here — that **job-specific experience/knowledge
  tests add incremental validity on top of GMA but do not replace it**, with GMA's validity
  actually being *highest* for more complex jobs (i.e., GMA — closer to "core" — becomes *more*
  important, not less, as specialisation/complexity rises, while specific experience's *relative*
  contribution shrinks with tenure as it saturates). This is a genuine large-scale empirical
  precedent for a "core sets a floor/ceiling that specialised knowledge modulates rather than
  replaces" structure, though phrased as GMA-vs-specific-knowledge rather than core-vs-specialised
  competency composition. **[A]** — this is about as well-replicated as applied psychology gets.
- **Nothing in the literature I could find states the "7% not 0%" arithmetic directly** — this
  looks like a genuinely original, testable refinement rather than a restatement of prior work.
  §4 addresses whether the repo's own data actually supports the specific *floor* framing, since
  that is where the refinement should be judged.

### 1.6 ML/AI analogues (assembled, cross-referenced above where already covered)

- **Meta-learning / MAML** (Finn, Abbeel & Levine, 2017; confirmed via Wikipedia fetch): explicitly
  trains a model so that "few iterations of gradient descent with few new-task examples" reach
  good performance — i.e., MAML is a **direct engineering instantiation of claim 4**: it optimises
  a "core" (initial parameters) specifically for *fast specialised-codebook acquisition* on new
  tasks, and few-shot benchmark results are exactly an "acquisition-rate" metric. **[A]** as an
  engineering paradigm, widely reproduced; whether it demonstrates *general* (as opposed to
  narrow, benchmark-family-specific) fast adaptation is contested in the broader meta-learning
  literature (MAML-family methods are known to sometimes rely on feature reuse within a narrow
  task family rather than genuine rapid learning — a caution structurally identical to claim 2's
  opacity problem).
- **Scaling laws** (Kaplan et al. 2020, arXiv:2001.08361, fetched directly): loss scales smoothly
  as a power law with model/data/compute size across "seven orders of magnitude" — the *opposite*
  of a cliff, and the direct tension with claim 2/3: **at the loss level**, capability is smooth;
  **at the task-accuracy level** (Schaeffer et al., above), the same smooth loss curve can produce
  apparently discontinuous accuracy curves depending on the scoring rule. This is the sharpest
  statement of claim 2's opacity: smoothness and cliffs can be two views of the identical
  underlying process.
- **The Bitter Lesson** (Sutton, 2019, fetched — note: the canonical URL returned a certificate
  error in this session; content independently corroborated via the Wikipedia summary page,
  **[C]** for exact wording, high confidence on substance given how widely and consistently this
  essay is quoted): general search+learning methods that scale with compute have consistently beaten
  hand-engineered, domain-specialised methods (chess, Go, speech, vision). This is a strong,
  repeatedly-validated **argument for investing in "core" (general method) over "specialised"
  (hand-built domain knowledge)** at the *system-design* level — a different register from the
  cognitive-science claims above (it's a claim about engineering strategy, not about individual
  minds), but directly relevant to how this repo should read its own MBPP nulls (§4): three arcs
  of hand-built specialised proposal content (chunks, train-diet, retrieval) all nulled, while the
  domain-general enumerator+verdict machinery is where capability actually lives — this is a small,
  local instance of exactly the Bitter Lesson's pattern.
- **Grokking, SCAN/COGS, emergent-abilities-mirage**: already covered in §1.2 as the primary
  opacity evidence.

---

## 2. This repo's prior experiments (comprehensive; verified directly + via delegated search)

This repo has **already run the decisive experiments** for claims 1-3, under a different
vocabulary ("propose vs. decide," "codebook content," "constructions propose, execution decides")
and with rigorous pre-registration + Wilson-CI discipline. This is the single most important
finding of Part 2: **the plan should build on four already-completed arcs, not propose a first
one.**

### 2.1 The central body of evidence: `PROGRAM_SYNTHESIS_ARC1-4` (MBPP code synthesis)

Read directly (not delegated): `PROGRAM_SYNTHESIS_ARC_SUMMARY.md`, `PROGRAM_SYNTHESIS_ARC2_SUMMARY.md`,
`PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md`, `PROGRAM_SYNTHESIS_ARC3_SUMMARY.md`,
`PROGRAM_SYNTHESIS_ARC4_PLAN.md`. All numbers below are quoted from these files, with per-item
identity-list rigor already built into the source (the repo's own "a baseline is a list" rule).

**Arc 1 — internal 125-task battery, three powered nulls on specialised-content hypotheses.**
Trajectory: P0 baseline 7/26 (frozen) → P6 MAIN **65/125 = 52.0% [43.3,60.6]** → P6.5
**77/125 = 61.6% [52.8,69.7]** → P7-D MAIN-P7 **80/125 = 64.0% [55.3,71.9]** (the "internal
battery 64.0%" figure). *No single step is CI-separated*; every claim is a paired identity list
(exact task ids that flipped). Three separate hypotheses that "more/better specialised proposal
content improves capability" were tested and **nulled**: **H6** (mined constructions vs. frozen
baseline, Δ=+3.2pp, CI spans zero, entire delta = 4 spine ids, enumerator alone carried 63/77
accepts); **H7a** (descent conversion rate, lower bound .142 vs. .409 bar — null); **H7c**
(mined chunks retested, **identical +3.2pp, the identical four spine ids as H6** — chunk rung-1
accepts = 0). Central finding, quoted verbatim: *"'constructions propose, execution decides' is
currently carried by the DECIDE half... the PROPOSE half's learned content has not yet paid a
CI-separated capability premium over the starter shapes + the enumerator."*

**Arc 2 — the external-benchmark cliff, measured and then content-ablated.** MBPP zero-shot on
the *same, unmodified* stack: **1/240 runnable = 0.42% [0.07%, 2.32%]** vs. the internal battery's
**80/125 = 64.0%** — a **~150× drop, same architecture, only the task distribution changed**
(exactly the cliff the task brief names, and the primary source for both anchor numbers). Feeding
the proposer **real, in-domain, NL-paired, train-mined content** (15 chunks, 30 bigrams — the
exact fix arc 1's H7c implied was missing) produced: **FULL 18/257 = 7.00% [4.48%,10.80%]** vs.
**CONTENT-STRIPPED 19/257 = 7.39% [4.78%,11.26%]**. The content ablation the task brief asks
about, quoted exactly: *"FULL's 18 passes are a strict SUBSET of CONTENT-STRIPPED's 19 — content
bought zero exclusive passes and cost exactly one."* This is **HQ3, the third null on this
hypothesis shape** (after arc-1's H6 and H7c). The *mechanism*, not just the measurement: every
one of FULL's 24 `gapped:exhausted` rows (a class **absent, 0/257, from CONTENT-STRIPPED**)
carries a chunk/codebook-cued construction that consumed the fixed attempt budget before the
enumerator could run — named "the proposal-layer decoy tax." Capability location:
`gapped:enumerate_failed` (55.3%) + `accepted_holdout_fail` (26.8%) = 82.1% of FULL's outcomes —
i.e. specialised content is not merely neutral, it is a **measured net cost** at this content
grain, while ~0% specialised content still gets you the ~7% floor via the domain-general
enumerator+verdict machinery.

**Arc 3 — a fourth, more powerful specialised-content architecture (whole-program retrieval), and
it still nulls the "content pays" hypothesis.** R0 measured the ceiling *before* building anything
(the repo's own "measure first" discipline, worth naming as a design principle in itself, §5):
oracle ceiling 12/257 = 4.67%. R3 endgame: FULL-R3 **8.17% [5.41%,12.17%]**; **HR1 (retrieval
content pays) = NULL**, net_passes=2 (3 gains, 1 regression), CI spans zero — and retrieval
introduces a **new failure mode**: a retrieval-sourced "trap" can pre-empt an already-correct
enumerator solution (task 17), because it runs first in priority order. Trap mass (candidates that
pass the revealed row but fail the held-out row) is 55.6-60% at every grain measured, twice. The
three-arc meta-finding, quoted: *"Search (the bare enumerator) still carries nearly all measured
capability... Proposal content — across all three architectures now tried — is a measurably real
but THIN, single-digit lever, never the dominant one... Protocol was, and remains, the single
largest capability mover ever measured in this program"* (the 0.42%→7.00% jump came from a
protocol/reveal-rule fix, not content).

**Arc 4 — the exact "61.2%" figure the task brief names, confirmed at its primary source
(`PROGRAM_SYNTHESIS_ARC4_PLAN.md`, revision log v3).** Of FULL-R3's 139 `gapped:enumerate_failed`
rows, **85/139 = 61.2% already emit fine and use NONE of the five named blocker constructs**
(comprehensions, mutating-method write-back, kwargs, map/lambda, regex) — these fail because **the
enumerator (search), not the emitter (representability) or the proposer (specialised content),
cannot reach list/iteration-shaped programs**. This is named explicitly as "a genuine
SEARCH-REACH/value-domain ceiling, independent of any proposal-content lever." Arc 4 registers a
**fourth-null rule**: if its one remaining content hypothesis (HA5, a cost-only re-measurement,
explicitly flagged by the plan's authors as "the most just-so-story-prone recommendation") also
nulls, the proposal-content line ends permanently and all effort redirects to verdict + search +
protocol.

**Why this matters for claim 1/3 directly:** this is a **four-arc, pre-registered, powered
ablation series that already tests exactly "how much of measured competency is core (search +
verdict) vs. specialised (proposal content)."** The answer, measured four independent ways
(mined chunks, richer mined chunks, whole-program retrieval, and a component-level breakdown of
the residual): **specialised proposal content's contribution is not CI-separable from zero, and
in one measured case is a net negative**, while the domain-general search+verdict engine carries
the overwhelming majority of both the internal-battery 64.0% and the external 7-8% MBPP numbers.
This is a much stronger evidential base than "an ablation with FULL passing a strict subset of
CONTENT-STRIPPED" alone — it's the *fourth* time the same qualitative result appeared, in escalating
architectures.

### 2.2 The operator-transfer evidence (core-skill reuse, verified)

- **`docs/agent_loop_iteration22_shape_based_transfer.md`**: a direct, controlled test of
  *structural* vs. *lexical* transfer. Transferring a rule by **shape** (`shapes_compatible()`,
  a structural-subsumption predicate over `{recursion, order_n, abstraction}`) succeeds (1/1 gap
  surfaced) where transferring by **lexical/keyword overlap** fails (0/1) on the *identical*
  source material — a controlled, within-repo demonstration that a domain-general structural
  match ("core") transfers where surface vocabulary ("specialised" lexical content) does not.
  A discriminance control confirms the matcher isn't promiscuous (a simpler shape correctly fails
  to subsume the richer donor). The doc itself flags this as directional/permissive and
  hand-authored at the boundary — an honest, scoped positive result, not an overclaim.
- **`tests/test_mechanism_transfer_migrated.py`**: gates a SHAPE→MECHANISM index +
  retrieve-and-transfer path. Demonstrates a domain-general mechanism (e.g. `feedback_control`,
  `selective_gating`) recognised at the *meta-shape* level transfers to a genuinely new domain and
  is **re-instantiated with the new goal's own fillers** (not the source domain's), with an honest
  null when no mechanism is indexed (never fabricates) and byte-identical no-op behaviour when the
  index is absent (protects every prior gate). This is a clean, mechanistic demonstration of "core
  transfers, re-parameterised by specialised content on arrival" — closer to the theory's own
  framing than any external literature I found.
- **`domains/analogical_thinking.py`**: the abstraction dial is real and matches the task brief's
  description exactly — n=0 (exact lexical match) through n=4 (meta-shape: "the principle of how
  it operates regardless of what it operates on"), with `think_harder()` escalating n until enough
  analogies are found. Notably, the repo **already tried and retired** a fixed cross-level
  "exchange rate" (an absolute weighted score across all five orders) in favour of **ordinal
  ranking by highest-matching order first** (`tests/test_analogical_relative_ranking.py`) — i.e.,
  the repo already learned, empirically, that you cannot cash out "how much core-ness is this
  worth vs. how much specialised-ness" on one shared scale, which is a direct, lived instance of
  claim 2's opacity (composition is not simply additive/exchangeable) discovered independently of
  this literature review.
- **`tests/test_transfer_gate_migrated.py`, run 24**: the cleanest CI-separated positive transfer
  result in the repo — a drawn-shape recognizer built and verified on Omniglot handwriting reaches
  **96.7% [93.6, 98.3] one-shot 20-way** on **entirely new, non-handwriting symbol classes**
  (line/arc primitives), with **zero adaptation** mechanically enforced (`git diff` asserted empty
  on every decode/verdict file). Shuffled control 5.0% [2.9, 8.5] — CI-separated from the real
  result. This is a genuine, well-powered, positive instance of core-operator transfer (the
  decode/verdict machinery) across a real distribution shift, standing in useful contrast to the
  MBPP arcs' repeated content-transfer nulls: **the operator transferred; in the MBPP arcs, it was
  specifically the specialised *content* that didn't.**
- **The `sd` loop (ShapeDecode) and Viterbi decode (`vit_step`/`vit_backtrace`)** are both
  literally the same Rust primitive reused unchanged across three unrelated domains — ink/Omniglot,
  speech, and (per `PROGRAM_SYNTHESIS_P3.md`) program-synthesis construction-bigram decoding. This
  is the operator-level dissociation stated as an architectural fact, not just a test result:
  **the decode-against-codebook operation is core and demonstrably reused; the codebook's content
  is what has repeatedly failed to transfer/pay off** in the MBPP arcs above.

### 2.3 The Omniglot cliff, in full (superseding the brief's own framing — see §0.2)

Primary source: `OMNIGLOT_ARC.md` (42KB, 38 gated runs). The trajectory the task brief cites
(37.5% four-alphabet → 26.8% ten-alphabet powered) is real and is an important, correctly-handled
methodological event (an underpowered n=80 trajectory rose to 41.2% across several architecture
changes, then a properly powered n=400 re-measurement corrected it down to **26.8% [22.6, 31.3]**,
with the explicit lesson recorded: *"point estimates at n=80 rose monotonically for ten runs...
and were wrong by a factor of ~1.5× on the ceiling"* — directly the kind of premature-optimism
correction claim 3 predicts you need power to detect). **But it is not the arc's final state**: a
subsequent change to the **verdict comparator** (SC+TPS continuous shape-matching, replacing a
weaker learned-quanta render-and-compare path — a "core" architectural change, not more
specialised content) recovered **73.5% [67.0, 79.1]**, and the arc's final standing number (further
confirmed, with six independent additional levers *nulling* against it at power) is
**80.5% [76.3, 84.1], n=400**. The arc's own stated synthesis: *"earned quanta are the
LEARNING/PROPOSAL layer... strong continuous geometry is the VERDICT layer — 'bins propose,
continuous decides.'"* This is directly relevant to §1.5's floor/ceiling refinement (see §4).

### 2.4 The N=1 case study this project actually is: the builder, not (only) the codebase

Per §0.4 correction 2: the strongest single piece of evidence available to this project for the
long-tail claim (§1.4) is not the codebase's internal operator-reuse record (§2.2, which remains
real, additional, and worth keeping) — it is the fact that **the codebase exists at all, in its
present form, built by one systems administrator** who integrated graph theory, neuroscience,
social science, quantum mechanics, physics, mathematics and computing into one working, running
96k-line Rust cognitive-substrate engine. This is worth treating carefully as evidence, not
anecdote, because of what kind of evidence it is:

- **It is an inspectable artifact, not self-report.** Unlike nearly all of the individual-
  differences literature above (which relies on test scores, questionnaires, or retrospective
  interview), the borrowed cross-domain structures here are directly checkable in source: a
  formal-grammar-style admissibility rule for graph rewrites, a signal-processing quantization
  scheme (the `ShapeDecode`/dynamic-quantization machinery, §2.2), a Viterbi decoder carried over
  verbatim from speech processing into ink and then construction-bigram decoding
  (`PROGRAM_SYNTHESIS_P3.md`), a cognitive-science-derived meta-shape vocabulary
  (`domains/analogical_thinking.py`, §2.2), and a frame/continuum invariant (this repo's own
  2026-07-08 "base-as-dimension" note in `CLAUDE.md`) that functions as a type-system constraint
  borrowed from a physics/mathematics distinction (discrete lattice vs. continuum). Each of these
  claims of cross-domain synthesis is falsifiable by reading the code, which is a strictly higher
  evidentiary bar than "I felt I learned domain B faster because of domain A."
- **What this N=1 case can support**: it is a genuine existence proof that a single person's
  domain-general operators (graph rewriting, formal-system design, signal-decomposition thinking)
  were re-applied, at low marginal cost per domain, across an unusually wide span of borrowed
  structures — directly the shape claim 4 predicts, and a rare case where the claim is checkable
  against a real artifact rather than a self-report.
- **What it cannot support, and should not be stretched to support**: causal attribution to
  "metacognition" specifically, as opposed to raw fluid ability, domain interest/engagement (PPIK,
  §1.5), extreme time investment, or survivorship (we are looking at this case *because* it
  succeeded — we have no denominator of similarly-motivated attempts that produced an incoherent
  or abandoned system). This is exactly the selection-vs-causation ambiguity the polymathy/eminence
  literature raises about itself (§1.4.5, Root-Bernstein/Simonton) — an N=1 success case, however
  well-inspected, cannot distinguish "core skill compounds and pays off" from "the kind of person
  who attempts this is unusual on several correlated dimensions at once." Both this document and
  the underlying research programme should treat the builder's own trajectory as a **rich source
  of testable hypotheses** (which specific operators were reused, at what apparent marginal cost,
  in what order — a question this repo can partially answer from its own commit history) rather
  than as **confirmatory evidence** on its own; §3c's recommended designs include one aimed
  specifically at extracting a real acquisition-rate curve from this repo's own development history,
  which would upgrade this from a single data point to an actual within-subject rate measurement.

### 2.5 What was NOT found

No file in the repo uses the literal strings "cliff," "off-distribution transfer," "competency
composition," or "core skill vs. specialised skill" — the phenomena the task brief names are
present throughout as **measured effects** (CI-spans-zero nulls, strict-subset ablations,
corpus-conditional-vs-robust splits) under this repo's own vocabulary, not under the theory's
vocabulary. This matters for the plan: the theory is a good **redescription** of four arcs' worth
of independent findings, not a restatement of something the repo has already explicitly named and
filed away — there is genuine synthesis value in writing it down this way, but no prior document
to defer to for "has the *theory itself*, as a named object, been checked here" — it has not, only
its individual predictions have (repeatedly, and mostly confirmed).

---

## 3. The mapping — literature onto the measured record

**(a) Does the literature support the operator-transfers/content-doesn't dissociation, or
contradict it?**

**Supports it, robustly, from an unexpected direction.** The single best-powered piece of
evidence in this entire review — **Sala & Gobet's chess/music/WM far-transfer meta-analyses
[A]** — says that training a *general* skill and hoping it transfers is close to the worst-case
prediction (near-zero far transfer). The repo's MBPP arcs found something structurally similar but
inverted in an instructive way: it wasn't a *trained general skill* that failed to transfer, it
was *hand-fed specialised content* that failed to transfer/pay off, while an **already-general,
architecturally-core mechanism** (the enumerator + verdict layer, and separately the `sd`
decode-against-codebook operator) **did** transfer/carry capability. Put together with the
`RESEARCH_CODE_IN_THE_BRAIN.md` §8.2b findings the delegated search surfaced (Sheridan & Reingold
2013: retrieved-but-suboptimal candidates cause fixation in experts *and* novices equally, no
expertise protection; Sala & Gobet's *other* 2017 paper, *Memory & Cognition*, 24 studies/903
participants, programming r̄=.36: chunking survives scrambling — many small chunks, not few big
plans), there is a **convergent, cross-literature, cross-domain (human cognition + this repo's own
measurements) case for a specific asymmetry**: general search/verdict/decode machinery is where
transfer happens; large specialised retrieval/plan content is where fixation, decoy costs, and
transfer failure happen. This is a genuinely interesting synthesis this spike surfaces that
neither literature review alone would produce.

**A third, independent convergence on the same asymmetry: human diagnostic/troubleshooting
reasoning (§1.4.4).** Medical case-specificity research (Elstein, Shulman & Sprafka 1978; Norman &
Eva's decades-long review programme, both **[A]**) and the parallel engineering-troubleshooting
literature (Morris & Rouse 1985) find the *identical two-component shape* this repo measured
directly in its own arcs: a real but comparatively thin domain-general strategic layer (generic
hypothesis-testing / half-split search — the human analogue of this project's enumerator+verdict
engine) sits underneath a dominant, non-transferring content layer (case-specific pattern
knowledge — the human analogue of the mined chunks/train-diet/retrieval content that nulled four
times, §2.1), with the domain-general layer's relative contribution **rising specifically at the
edge of the content layer's reach** — exactly Hogarth's kind/wicked prediction (§1.4.3) and
exactly arc 4's own 61.2% finding (the domain-general search engine is the identified bottleneck
once representability and specialised content are no longer the limiting factor). Three
independent measurement traditions — this repo's own pre-registered software ablations, medical
education's decades of case-specificity research, and the engineering-troubleshooting
literature — converge on the same structural claim without citing each other. That convergence is
stronger evidence for the operator/content dissociation than any one of the three alone.

**(b) Is the floor-vs-ceiling refinement of claim 1 known/tested in the literature?**

**Partially anticipated, not directly tested as stated.** Cattell's investment theory (Gf sets the
*rate* of Gc accumulation, not the level directly) and Schmidt & Hunter's **[A]**-graded finding
that GMA's validity is *highest*, not lowest, for complex/specialised jobs (while specific
experience's *relative* contribution saturates with tenure) are both structurally compatible with
"core sets a floor that doesn't disappear even at high specialisation, and doesn't scale up
arbitrarily with more specialised content either." But neither literature states the specific
"specialised≈0 still yields 7%, not 0%" arithmetic, and I could not find a published account that
treats "floor/flatness vs. ceiling/cliff" as two *separately attributable* statistical moments
(intercept vs. slope) of a competency-by-distribution curve. **This makes it a genuinely novel,
testable contribution**, not a rediscovery — see recommended design #1 below for how to test it
properly (the repo's own MBPP data, read carefully, is suggestive but was not designed to isolate
this).

*A caution on the repo's own 7% number, applying §0.2's rule*: the MBPP "7% with content vs 0.42%
baseline" comparison the brief uses to argue "core alone gives 7%" is not quite the right
contrast for testing the floor/ceiling refinement — **the 0.42%→7.00% jump was overwhelmingly a
*protocol* change** (arc 2's HQ2, revealing example rows properly), not a content-vs-no-content
change; the actual content ablation (CONTENT-STRIPPED = 7.39% vs FULL = 7.00%) shows **the "core
only" arm is *higher*, not the floor**, with specialised content measured as a net cost, not a net
lift. This still supports "specialised≈0 gives non-zero performance" (CONTENT-STRIPPED's 7.39% is
exactly that), but it does not yet show a *ceiling effect from specialisation*, because
specialisation in every measured architecture (chunks, train-diet, retrieval) has so far bought
*at most* single-digit net passes, never a ceiling lift big enough to distinguish "specialisation
raises the ceiling" from "specialisation does approximately nothing in this domain, so far." The
honest state: **the floor half of the refinement is measured and real (§2.1); the ceiling half is
not yet demonstrated** by this repo's own data — every specialised-content architecture tried so
far has failed to raise the ceiling, which is either evidence against the refinement's ceiling
claim, or evidence that the right *kind* of specialised content (at MBPP's grain) hasn't been
found yet. Arc 4's own "fourth-null rule" is the correct experimental attitude here.

**(c) What is the standard experimental design for measuring competency composition?**

Four converging design families, each with a citation and each already partially instantiated in
this repo:

1. **Content-holding-mechanism-fixed ablation** (what arcs 1-4 already do): vary only the
   specialised content (chunks → train-diet → retrieval) while holding the core mechanism fixed,
   measure CI-separated deltas + paired identity lists. This is the standard design in the
   **cognitive-training far-transfer literature** (Sala & Gobet's meta-analyzed studies are almost
   all of this shape: train a specific skill, measure a battery of far-domain outcomes with an
   active control). The repo is already running this correctly; the recommendation is to keep
   doing it, not to invent a new design.
2. **Distribution-shift batteries with a held ceiling measured first** (what arc 3's R0 and the
   ARC-AGI-2 redesign both do): measure the *maximum possible* content-driven gain *before*
   building the mechanism (an oracle/ceiling analysis), so a subsequent null is interpretable
   rather than ambiguous between "the mechanism is bad" and "there was nothing to gain." This is
   the **dynamic-assessment "test-teach-retest"** logic applied to system components rather than
   people, and it is the single most valuable methodological habit in the existing arcs — worth
   naming explicitly as the design to keep using for the ceiling-side of the floor/ceiling claim.
3. **Acquisition-rate curves under standardised exposure (dynamic assessment / few-shot learning
   curves)**: Feuerstein's LPAD and Vygotsky's ZPD (test-teach-retest gain score) on the psychology
   side, and **meta-learning's own standard evaluation protocol** (N-way K-shot accuracy *as a
   function of K*, MAML-style) on the ML side, are the two published families of **acquisition-rate**
   metrics, as opposed to single-point accuracy. This is the design missing from the repo's
   current arcs: every MBPP/Omniglot/battery number reported above is a **single-point accuracy**
   after a fixed amount of exposure/training, never a **rate curve** (accuracy vs. amount of
   new-domain exposure). Claim 4 specifically (metacognitive/core-driven fast acquisition) cannot
   be tested with single-point numbers at all — it requires a **curve**, and none of the cited
   evidence in this repo currently produces one. This is the sharpest actionable gap the mapping
   surfaces.
4. **Component-attribution / failure-taxonomy decomposition** (arc 4's own 61.2% figure): rather
   than an aggregate ablation, partition the *failures* by which stage of the pipeline (represent →
   propose → search → verify) they belong to. This is closer to **Peitek et al.'s DepDegree-vs-
   McCabe** style of component-level attribution in the program-comprehension literature (cited
   in `RESEARCH_CODE_IN_THE_BRAIN.md`, confirmed by the delegated search) than to any single
   psychology paradigm — it is arguably this repo's own methodological invention, and it is a good
   one; the recommendation is to formalise it as a named, reusable design (a "failure-taxonomy
   ablation") for future arcs, including on Omniglot/vision.

**(d) Is there a published metric for skill-acquisition efficiency to adopt rather than invent?**

**No single standard metric spans both psychology and ML — three real candidates, none a clean
drop-in:**
- **Chollet's own formalism** (§1.1) explicitly avoids collapsing to one scalar — it pairs a
  generalisation-difficulty axis against a priors+experience axis and reports *where on that
  plane* a system sits, rather than a single "acquisition efficiency" number. If the team wants
  one metric, adopting Chollet's *plane* (not a scalar) is the most defensible published choice,
  since it is literally designed for this question and instantiated in a widely-used benchmark.
- **Dynamic-assessment gain scores** (Feuerstein/Vygotsky, §1.4/§3c): `(post-teaching performance −
  pre-teaching performance) / teaching dose` — a genuine rate metric, but from a human-testing
  tradition with no standard computational implementation to borrow code from; would need to be
  operationalised fresh for this system.
- **Meta-learning's K-shot curves** (MAML-style, §1.6): accuracy as a function of exposure count
  K, with the **area under the curve** or the **K needed to reach a fixed accuracy threshold** as
  scalar summaries — this has the most directly reusable methodology (it's exactly what an ML
  team already knows how to run) and maps cleanly onto "how many new-domain examples does the
  system need before it performs at floor+X%." **This is my recommendation** if the team wants one
  number: report **episodes/examples-to-criterion** on a new held-out domain, not a single
  post-hoc accuracy, because it is the only one of the three that directly operationalises "rate,"
  which is what claim 4 actually asserts and none of the current repo battery measures.

---

## 4. Falsifiers and honest cautions

**What would falsify each claim, concretely, given what's now known:**

1. **Claim 1 (composition)** is falsified locally by exactly what arcs 1-4 already ran: if a
   content ablation shows FULL strictly dominating CONTENT-STRIPPED with a CI-separated margin,
   composition-with-real-specialised-contribution is confirmed for that domain. It has now failed
   to be confirmed **four times** in this repo (chunks, richer chunks, retrieval, and the
   component breakdown) — this is not proof composition is false in general, but it is a repeated,
   well-powered failure to find the *specialised* half doing real work at the tested grain, which
   should lower confidence specifically in "specialised codebook content" as usually imagined
   (chunks/exemplars/plans), while leaving open that the *right* specialised content (a different
   grain, a different domain) would show it.
2. **Claim 2 (opacity)** is, by its own logic, hard to falsify directly — "you cannot tell from one
   distribution" is close to a claim about the limits of an inference, not a testable empirical
   regularity about a system. **This is the claim most at risk of being unfalsifiable as stated.**
   The literature's actual handling of this problem (Schaeffer et al., grokking, SCAN/COGS) is
   instructive: they don't try to falsify "opacity" directly; they instead show **specific,
   constructed cases where a second distribution/second metric reveals a composition that a first
   one hid**, and treat opacity as the reason you need that second view, not as a claim to be
   tested on its own. **Recommendation: reframe claim 2 operationally** — not "composition is
   unknowable from one distribution" (unfalsifiable) but "a battery of N deliberately-varied
   distributions is required before a composition claim is warranted, and fewer than N is
   underdetermined" — which is falsifiable (you can show N=2 is insufficient by finding a case
   where two distributions agree but a third reveals something the first two both missed, exactly
   as arc 1→2→3's escalating architectures did).
3. **Claim 3 (the cliff)** is well-established for the general phenomenon (Chase & Simon, [A]) but
   the *mechanistic* account of why (routine/adaptive expertise, knowledge brittleness) is
   thinner ([B]/[C], single research programs). It would be falsified for a given system by
   showing performance degrades **gracefully** (a smooth, monotonic function of distribution
   distance) rather than discontinuously — this is directly testable and is exactly what a
   properly-designed distribution-shift battery (recommended design #2/#3) would show either way.
   Some evidence already in the repo is ambiguous on this point: the MBPP "cliff" (64.0%→0.42%)
   looks discontinuous, but that is confounded with the fact that the *protocol*, not just the
   *distribution*, changed between the two measurements (§3b's caution) — a clean test needs the
   protocol held fixed while only the distribution varies, which the internal-battery-vs-MBPP
   comparison as currently measured does not quite provide.
4. **Claim 4 (metacognitive/core transfer, correctly read as a long tail, §1.4)** is falsifiable
   but is **currently under-tested rather than falsified** — the design that would falsify it
   cleanly (a longitudinal, within-person study measuring time/examples-to-criterion across a real
   sequence of 3+ genuinely novel domains for the same individuals, checking whether the slope is
   negative — each domain cheaper than the last — and whether that slope is predicted by a
   behavioural, not self-report, metacognitive/core-operator measure after controlling for g)
   essentially does not exist in the literature I found. What *does* exist and *would* falsify the
   long-tail claim if it turned up: flat or increasing (not decreasing) time-to-criterion across
   successive domains in Harlow-style or bilingual-acquisition-style paradigms extended past two
   domains; a null result there would be a much sharper falsification than anything in the
   far-transfer meta-analyses, which (§1.4.1) I now judge largely orthogonal to this claim rather
   than a null against it. The diagnostic/troubleshooting literature (§1.4.4) already provides a
   *partial*, real falsification of the claim's *strong* form (clean, dominant, general-purpose
   diagnostic reasoning does not appear to exist — case-specificity is real and well-replicated),
   while leaving the claim's *weaker*, two-component form (a real, smaller, relatively-more-useful-
   at-the-edge general layer) standing.
5. **The N=1 builder case study (§2.4)** is, by construction, unfalsifiable on its own — a single
   success case cannot be used to test a general causal claim, only to generate one. Treating it as
   confirmatory (rather than as a source of testable hypotheses about operator-reuse order and
   marginal cost, extractable from this repo's own commit history) would be a clear instance of the
   unfalsifiability risk raised for claim 2 — an inspectable artifact is better evidence than a
   self-report, but "better than self-report" is not the same as "sufficient to confirm a causal
   individual-differences claim."
5. **The floor/ceiling refinement** is directly falsifiable and not yet run: fit a two-parameter
   model (intercept from core content, slope/ceiling from specialised content) across the arcs'
   *already-collected* per-item data (arc 1, arc 2 FULL vs. CONTENT-STRIPPED, arc 3) and check
   whether an intercept-only model (core sets everything, specialised is pure noise) fits equally
   well as a floor+ceiling model — given that specialised content has not yet produced a
   CI-separated *positive* delta anywhere in four tries, the current data is arguably **more
   consistent with intercept-only than with a genuine floor+ceiling structure**, which is an
   important, slightly deflationary honest caution the team should sit with before designing
   experiment #1 below.

**Which parts are folk-psychology with thin evidence, stated plainly:** the part of the theory with
the least rigorous *direct* support is not claim 4's qualitative shape (§1.4 found genuine,
multi-tradition convergence for that) but the **specific causal attribution to "metacognition"** as
the operative individual-differences variable, as opposed to fluid ability, disposition/interest
(PPIK), sheer time investment, or selection effects — this is the part popular treatments assert
most confidently and the literature supports most thinly (Veenman's own dissociation between
self-report and behavioural measures is the field's own warning about exactly this). The polymathy/
eminence literature (§1.4.5) and the N=1 builder case (§2.4) are both genuinely suggestive and both
explicitly, by their own authors' or by construction's admission, confounded by selection — treating
either as demonstrating a *causal* metacognition→acquisition-rate link, rather than as consistent
with one, would be the folk-psychology move to avoid.

---

## 5. Executive summary is in the final chat message (per task instructions), not duplicated here.

---

## Bibliography (sources actually consulted this spike; grade noted)

- Chollet, F. (2019). *On the Measure of Intelligence*. arXiv:1911.01547. **[B]** (fetched directly)
- Chollet, F. et al. (2024). *ARC-AGI-2: A New Challenge for Frontier AI Reasoning Systems*.
  arXiv:2505.11831. **[B]** (fetched directly)
- ARC Prize Foundation, arcprize.org (leaderboard/ARC-AGI-2 pages). **[C]** (numeric leaderboard
  data not extractable via fetch; qualitative claims fetched)
- Thorndike, E.L. & Woodworth, R.S. (1901). Identical-elements theory of transfer. **[A]**
  (historical anchor; via Wikipedia)
- Barnett, S.M. & Ceci, S.J. (2002). When and where do we apply what we learn? A taxonomy for far
  transfer. *Psychological Bulletin*. **[B]** (confirmed via Crossref)
- Detterman, D.K. (1993). The case for the prosecution: Transfer as an epiphenomenon. In Detterman
  & Sternberg (eds.), *Transfer on Trial*. Ablex. **[C]** (secondary citation only)
- Pressley, Yokoi, Detterman & Sternberg (1994). Motion for a new trial on transfer. *Educational
  Researcher*. **[C]** (Crossref metadata only)
- Sala, G. & Gobet, F. (2017). Does far transfer exist? Negative evidence from chess, music, and
  working memory training. *Current Directions in Psychological Science*. **[A]** (confirmed via
  Crossref)
- Sala, G. & Gobet, F. (2019). Cognitive training does not enhance general cognition. *Trends in
  Cognitive Sciences*. **[A]** (confirmed via Crossref)
- Sala, Aksayli, Tatlidil, Tatsumi, Gondo & Gobet (2018). Near and far transfer in cognitive
  training: a second-order meta-analysis. PsyArXiv. **[A]** (confirmed via Crossref)
- Sala, G. & Gobet, F. (2017). Experts' memory superiority for domain-specific random material
  generalizes across fields of expertise. *Memory & Cognition*. **[A]** (cited via
  `RESEARCH_CODE_IN_THE_BRAIN.md`, cross-checked)
- Cattell, R.B. (1963); Horn, J.L. (1991). Gf-Gc / CHC theory, investment theory. **[B]** (confirmed
  via Wikipedia)
- Ackerman, P.L. (1996). A theory of adult intellectual development: process, personality,
  interests, and knowledge (PPIK). *Intelligence*. **[B]** (confirmed via Crossref)
- Schmidt, F.L. & Hunter, J.E. (1998). The validity and utility of selection methods in personnel
  psychology. *Psychological Bulletin*. **[A]** (confirmed via Crossref)
- Chase, W.G. & Simon, H.A. (1973). Perception in chess. *Cognitive Psychology*. **[A]** (confirmed
  via Wikipedia)
- Hatano, G. & Inagaki, K. (1986). Two courses of expertise. In Stevenson, Azuma & Hakuta (eds.),
  *Child Development and Education in Japan*. Freeman. **[C]** (secondary citation only)
- Spiro, Feltovich, Coulson & Anderson (1989, 1992, 2013). Cognitive Flexibility Theory / knowledge
  brittleness in ill-structured domains. **[B]** (confirmed via Crossref, titles only)
- Ericsson, K.A. (1993, 2016). Deliberate practice. **[B]** (confirmed via Wikipedia)
- Campitelli, G. & Gobet, F. (2011); Hambrick & Meinz (2011); Macnamara, Hambrick & Oswald (2014,
  *Psychological Science*, deliberate practice meta-analysis: 26%/21%/18%/4%/<1% variance
  explained by domain); Hambrick, Macnamara & Oswald (2020, *Frontiers in Psychology*). **[A]**
  (confirmed via Crossref/Wikipedia — one of the best-powered critique literatures in this review)
- Flavell, J.H. (1979). Metacognition and cognitive monitoring. *American Psychologist*. **[A]**
  (confirmed via Wikipedia)
- Swanson, H.L. (1990). Influence of metacognitive knowledge and aptitude on problem solving.
  *Journal of Educational Psychology*. **[B]** (confirmed via Wikipedia)
- Veenman, Prins & Elshout (2002); Veenman & Spaans (2005); van der Stel & Veenman (2008).
  Metacognitive skill vs. intellectual ability as predictors of new learning. **[B]** (titles/venues
  confirmed via Crossref; abstracts/effect sizes not independently verified)
- Veenman, Van Hout-Wolters & Afflerbach (2006). Metacognition and learning: conceptual and
  methodological considerations. *Metacognition and Learning*. **[B]** (confirmed via Crossref,
  1,335 citations)
- Sternberg, R.J. & Wagner, R.K. et al. Practical intelligence / tacit knowledge. **[C]** (titles
  confirmed via Crossref, not read in full)
- Harlow, H.F. (1949). The formation of learning sets. *Psychological Review*. **[A]** (confirmed
  via Crossref; canonical, well-replicated)
- Harlow, H.F. & Warren, J.M. (1952). Formation and transfer of discrimination learning sets.
  *Journal of Comparative and Physiological Psychology*. **[A]** (confirmed via Crossref)
- Bateson, G. (1972/1942). The logical categories of learning and communication ("deutero-
  learning"). In *Steps to an Ecology of Mind*. **[C]** (not independently fetched this session;
  standard secondary attribution)
- Cenoz, J. (2003). The additive effect of bilingualism on third language acquisition: a review.
  *International Journal of Bilingualism*. **[A]** (confirmed via Crossref)
- Cenoz, J. & Hoffmann, C. (2003). Acquiring a third language: what role does bilingualism play?
  *International Journal of Bilingualism*. **[A]** (confirmed via Crossref)
- Kaushanskaya, M. & Marian, V. (2009). The bilingual advantage in novel word learning.
  *Psychonomic Bulletin & Review*. **[A]** (confirmed via Crossref)
- Hogarth, R.M., Lejarraga, T. & Soyer, E. (2015). The two settings of kind and wicked learning
  environments. *Current Directions in Psychological Science*. **[B]** (confirmed via Crossref)
- Epstein, D. (2019). *Range: Why Generalists Triumph in a Specialized World*. Riverhead. **[C]**
  (popular synthesis; cited primary sources graded independently)
- "Single-Sport Specialization versus Sampling" (2018), in *Youth Sports in America*, ABC-CLIO.
  **[C]** (confirmed title/venue via Crossref; broader Côté/DMSP sampling literature not
  independently re-verified this session)
- Elstein, A.S., Shulman, L.S. & Sprafka, S.A. (1978). *Medical Problem Solving: An Analysis of
  Clinical Reasoning*. Harvard University Press. **[A]** (confirmed via Crossref; foundational
  case-specificity finding)
- Norman, G.R. & Eva, K.W. (2009). Diagnostic error and clinical reasoning. *Medical Education*.
  **[A]** (confirmed via Crossref; part of a decades-long review programme on case specificity)
- Morris, N.M. & Rouse, W.B. (1985). Review and evaluation of empirical research in
  troubleshooting. *Human Factors*. **[B]** (confirmed via Crossref)
- Root-Bernstein, R., Bernstein, M. & Garnier, H. (1995). Correlations between avocations,
  scientific style, work habits, and professional impact of scientists. *Creativity Research
  Journal*. **[B]** (confirmed via Crossref; correlational, selection caveat explicit in §1.4.5)
- Simonton, D.K. (2018). *The Genius Checklist*. MIT Press; Simonton, D.K. (2019). Creative
  genius. In *The Cambridge Handbook of Creativity*. **[B]** (confirmed via Crossref; independent
  research programme converging with Root-Bernstein, same causal caveat)
- Finn, C., Abbeel, P. & Levine, S. (2017). Model-Agnostic Meta-Learning (MAML). **[A]** (confirmed
  via Wikipedia)
- Kaplan, J. et al. (2020). Scaling Laws for Neural Language Models. arXiv:2001.08361. **[A]**
  (fetched directly)
- Wei, J. et al. (2022). Emergent Abilities of Large Language Models. *TMLR*. **[B]** (fetched
  directly; superseded in part by Schaeffer et al. below)
- Schaeffer, R., Miranda, B. & Koyejo, S. (2023). Are Emergent Abilities of Large Language Models a
  Mirage? arXiv:2304.15004. **[A]** (fetched directly)
- Power, A. et al. (2022). Grokking: Generalization Beyond Overfitting on Small Algorithmic
  Datasets. arXiv:2201.02177. **[B]** (fetched directly)
- Lake, B. & Baroni, M. (2018). SCAN: Generalization without systematicity. arXiv:1711.00350.
  **[A]** (fetched directly)
- Kim, N. & Linzen, T. (2020). COGS: A Compositional Generalization Challenge. arXiv:2010.05465.
  **[A]** (fetched directly)
- Hupkes, D., Dankers, V., Mul, M. & Bruni, E. (2020). Compositionality Decomposed. *JAIR*. **[A]**
  (confirmed via Crossref)
- Sutton, R. (2019). The Bitter Lesson. **[C]** (canonical URL cert error this session; content
  corroborated via secondary summary)
- `RESEARCH_CODE_IN_THE_BRAIN.md` (this repo) — cross-referenced for Sheridan & Reingold (2013),
  Soloway & Ehrlich (1984), Peitek et al. (2021), all independently graded there; not re-verified
  independently in this spike, cited as this repo's own prior work.
- Repo primary sources (all read directly this spike): `PROGRAM_SYNTHESIS_ARC_SUMMARY.md`,
  `PROGRAM_SYNTHESIS_ARC2_SUMMARY.md`, `PROGRAM_SYNTHESIS_ARC2_Q0_BASELINE.md`,
  `PROGRAM_SYNTHESIS_ARC3_SUMMARY.md`, `PROGRAM_SYNTHESIS_ARC4_PLAN.md`, `OMNIGLOT_ARC.md`,
  `domains/analogical_thinking.py`, `tests/test_mechanism_transfer_migrated.py`,
  `tests/test_transfer_gate_migrated.py`.
- Repo secondary sources (read via delegated agent, not independently re-verified line-by-line by
  me): `docs/agent_loop_iteration22_shape_based_transfer.md`,
  `docs/agent_loop_iteration36_continuous_and_transfer.md`, `ARC_LS20_PIXELSEG_RESULTS.md`.
