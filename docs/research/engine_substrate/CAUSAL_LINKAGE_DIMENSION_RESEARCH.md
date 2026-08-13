# Causal linkage as a quantized dimension — a design-research spike

**Status: RESEARCH SPIKE. No code, no seeds, no tests, no builds in this
document.** Exactly one file was added to the tree (this one). Matching the
register of `CROSS_DOMAIN_SHAPE_SPIKE.md` and `SHAPE_TYPE_VOCABULARY_SPIKE.md`:
literature is checked, not recalled; source claims carry `file:line`; a
concrete design is picked and defended at the end, not left as a menu.

**Charter, verbatim, from the project's creator**, in response to today's
`implies(antecedent, consequent)` boolean-predicate rung
(`DEDUCTION_GENERALIZATION_RESULTS.md`):

> "I think part of the problem here is implication is a fixed term - It seems
> more like an edge with a quantized weight from a dimension of causal linkage
> (or something) - workshop this."

and, when pressed to ground the workshop in real evidence rather than
intuition:

> "Do research to find out how it should work and how it works for people -
> we use simple word descriptions, but that's not how things are HELD.
> Critically, we are not here to be small and safe - we are building things
> that have never been done, so 'safer' is almost always the wrong bet."

The second instruction is a real constraint on this document's own final
section, not decoration: where the evidence supports a fork, this document
leans toward the design the evidence still supports even when it is more
work, more novel, or harder to defend than the field's own conventional
answer — and says so explicitly rather than retreating to the safe synthesis
out of caution. Where the safe answer is genuinely what the evidence shows,
this document says that plainly too, for one specific sub-question (§5), and
explains why that is not a cop-out.

**Confidence convention**, matching the prior two spikes: claims verified by
reading source in this tree carry `file:line`. Literature claims carry the
source actually fetched and read; where only an abstract, a fetched summary,
or a secondary description was reachable rather than the full paper, that is
stated plainly, and the claim is downgraded rather than dressed up.
Paywalled/binary-PDF fetches that returned nothing usable are named as such,
not silently dropped. Nothing below is asserted without one of these two
groundings.

---

## 0. The four answers, up front

1. **How do people hold causal/conditional knowledge?** Not as one thing.
   There are two well-separated literatures the charter's own framing
   correctly keeps apart — *causal cognition* (how strength/structure is
   learned and judged) and *conditional reasoning* (what "if P then Q"
   means and how its truth/probability is judged) — and each has real,
   contested internal debate. The strongest single finding, replicated
   across three decades and directly on-point for the charter's intuition:
   people's probability judgment of "if P then Q" tracks the **conditional
   probability P(Q|P)**, not the truth-functional material conditional of
   classical logic (§2.5). On causal strength specifically, the field's own
   best normative account (Griffiths & Tenenbaum's *causal support*) is a
   **continuous log-odds quantity** (§2.3), and the strongest *associative*
   account (Rescorla-Wagner) is a **continuously-updated weight** (§2.4) —
   both point away from a fixed boolean, and neither hands you a discrete
   representation for free.
2. **Is there real precedent for QUANTIZED (not continuous) causal strength
   specifically?** Weak-to-moderate, and this document says so honestly
   rather than manufacturing a precedent. The strongest cognitive finding
   found is not a theory of quantization but an empirical fact that
   *behaves* like one: people's raw causal judgments are **measurably
   bimodal/categorical much of the time**, with graded responses appearing
   specifically under low confidence (O'Neill, Henne, Bello, Pearson & De
   Brigard 2022, §3.1). On the AI side there is now real, recent,
   identifiability-proven precedent for **discrete latent causal
   variables** as a representation choice (Zhang, Wang & Gu 2026, §3.2) —
   built for a different reason (interpretability/statistical
   identifiability) but structurally exactly the move this project already
   makes everywhere else.
3. **Unify or layer?** The literature does not hand down a schema verdict —
   no cited source is making a claim about graph node/edge kinds. What it
   does establish is a real, well-evidenced **functional split between two
   processing modes** (dual-process accounts, §4.2) that nonetheless
   **communicate and shade into each other rather than being hermetically
   sealed** (§4.1's Ramsey-test/intervention connection; Boroditsky's
   consolidation finding reused from the prior spike). This is the same
   shape `CROSS_DOMAIN_SHAPE_SPIKE.md` §7.2 already found for physical vs.
   symbolic domains, and it resolves the same way here: **unify at the edge
   kind, layer at the rung** — one relation kind (`implies`/causal linkage),
   parameterized by an Occam-ordered strength dimension, with today's
   boolean `implies` sitting at the dimension's **ceiling quantum**, not as
   a separate primitive (§4.3, §6).
4. **What should the quantization basis be?** Not a pick from the four
   options as posed — the research shows two of them are the *same* map
   read from opposite ends. Griffiths & Tenenbaum's causal support is a
   **log-odds** (Bayesian log-likelihood-ratio) quantity computed *from*
   raw **event counts**; "evidential count" and "discretized log-odds" are
   not competing bases, they are the **in-frame observation** and the
   **cross-frame generator** of one relation, exactly the shape this
   project's own `scale2`/`modular` `DimensionGenerator`s already are
   (§497-564 of `CLAUDE.md`, quoted in full in §5). The recommendation is a
   new `DimensionGenerator{kind:"logodds"}` — count-in, log-odds-map,
   integer-`k`-out — and it is defended in §6-7 as the concrete design.

---

## 1. Method

1. `CLAUDE.md` in full, with direct attention to `SHAPE IS ACQUISITION, RULE
   IS EXECUTION` (`:993-1138`) and `BASE-AS-DIMENSION + the frame/continuum
   invariant` (`:497-564`).
2. `docs/research/engine_substrate/DEDUCTION_GENERALIZATION_PREREG.md` +
   `_RESULTS.md` — the rung this document is workshopping a correction to.
3. `docs/research/engine_substrate/CROSS_DOMAIN_SHAPE_SPIKE.md` and
   `SHAPE_TYPE_VOCABULARY_SPIKE.md` in full, for register and because
   §7.1-7.2 of the first is the direct structural precedent this document
   reuses in §4.3.
4. `seeds/inference_knowledge.json` (all 8 `ShapeSignature` schemas, read in
   full — quoted in §6.1) and `seeds/logic_foundation.json`/
   `seeds/logic_propositional_predicate.json` (confirmed still inert,
   `match: None`, out of scope, matching the deduction rung's own finding).
5. The Rust: `runners/dsl/src/shape_decode.rs`'s `Generator` struct
   (`:389-410`), `apply_generator_once`'s dispatch (`:822-847`), and
   `seeds/shape_decode_loop.json`'s `sd_infer_dimension`/`sd_recognize_dim`
   rule comments (the authoritative, currently-true description of how
   `DimInfer`/`LatentDimension`/`Transform{dim,delta}` actually work,
   including the v1.4.0/v1.5.0 `scale2`/`modular` additions this document
   leans on directly).
6. The in-flight correction worktree
   (`/home/matt/ozmadev/ocelot-worktrees/deduction-general-reader-correction`,
   branch `deduction-general-reader-correction`, uncommitted as of this
   read): its `DEDUCTION_GENERAL_READER_CORRECTION_PREREG.md` confirms
   `implies` is *also* already a general reading construction
   (`seeds/reading_constructions.json local_id 48`:
   `signature:[["IF"],["THEN"]]`, `predication:"implies"`,
   `ground_template:{"pred":"implies","mode":"pair"}`), not only the
   `knowledge_logical` schema from today's landed rung — i.e. "implies" is
   fixed and boolean in **two** places, not one, which sharpens rather than
   changes the charter's concern. **No `DEDUCTION_GENERAL_READER_CORRECTION_
   RESULTS.md` exists yet at the time of this reading** — that correction is
   in progress, uncommitted, and this document does not depend on its
   outcome (it is about the reading-mechanism plumbing, not the strength
   representation this document addresses).
7. Only then the literature (§2-4), via WebSearch/WebFetch — real papers,
   fetched where reachable, marked `[unverified beyond abstract/summary]`
   where not.

---

## 2. Part 1 — how humans actually hold causal/conditional knowledge

### 2.1 Structural causal models (Pearl) — a normative theory first, a cognitive theory only by import

Pearl's causal Bayes nets / structural causal models (Pearl, *Causality:
Models, Reasoning, and Inference*, 2000/2009) define causal strength via
structural equations and license interventions via the do-calculus. Pearl
himself received the 2010 Rumelhart Prize for the framework's cognitive-
science contributions, but **the framework's own origin and primary
justification is computational/normative — a calculus for what a rational
agent's causal beliefs and interventions *should* satisfy** — and the
claim that it also describes the *actual* representation in a human head is
a separate, later, and more contested import, made explicitly by
psychologists rather than by Pearl's own foundational work.

The clearest statement of that import is Steven Sloman's *Causal Models: How
People Think about the World and Its Alternatives* (Oxford, 2005): the book's
stated purpose is to propose causal Bayes nets **as** psychological theories
of mental representation, not merely as a normative yardstick — "the mental
representations in working memory... [are] something like the structural
element of a Causal Bayes Net." This is a genuine claim about cognitive
architecture, and it has been tested directly.

**The test result is mixed, and the mixed part matters.** Rottman & Hastie,
"Reasoning about causal relationships: Inferences on causal networks"
(*Psychological Bulletin* 140(1), 2014) — a large tutorial-plus-review
comparing normative Bayes-net predictions against decades of behavioral
data across chain/common-cause/common-effect network structures — found
systematic, replicated **violations of the Markov assumption** and
inadequate "explaining away," i.e. exactly the structural properties a
Bayes-net representation predicts and human judgment does not reliably
honor. **Confidence: high** that this review exists and reports these
violations (read via search-result synthesis of the PMC-indexed abstract and
its own framing; the full PMC text was not fetched word-for-word, so
specific numeric effect sizes are `[unverified]`).

**What this establishes and what it does not, stated precisely per this
project's own house rule** (`CLAUDE.md`'s "synthetic-proven mechanism ≠
benchmark value, report both"): Pearl's SCM/do-calculus is an excellent,
well-established **normative/computational-level** account of what causal
reasoning should compute. It is a **contested, partially-falsified**
account of the actual on-line cognitive representation — real, systematic
deviations exist. Both of these are true at once and are not in tension;
conflating them is the exact error the charter's research prompt warned
against ("check which claim each source is actually making").

### 2.2 Cheng's causal power theory — strength as an inferred latent, not a raw statistic

Cheng, "From covariation to causation: A causal power theory" (*Psychological
Review* 104(2), 1997, pp. 367-405) proposes that people do not represent
causal strength as the raw observable contingency (covariation) between
cause and effect — they infer an unobservable **causal power** *p*, a
context-independent property of the candidate cause, via a specific
normalization of the contingency by the effect's base rate. Novick & Cheng
(2004) extended this to interactive/conjunctive causes.

**Two live comment papers sharpen exactly what kind of claim this is,**
both read in full:

- Luhmann & Ahn, "The meaning and computation of causal power: Comment on
  Cheng (1997) and Novick and Cheng (2004)" (*Psychological Review*
  112(3), 2005) — fetched and read. Cheng's own words, as quoted there:
  people's goal is "to induce the unobservable causal power of a candidate
  cause in the distal world from observable events" (Buehner et al. 2003,
  p. 1120) — an **explicit cognitive-representation claim**, not merely a
  normative one. Luhmann & Ahn's own critique is structural, not merely
  empirical: "if all requisite assumptions are satisfied... causal power
  should always be either 0 or 1" — i.e. under Cheng's own idealizing
  assumptions the *theory itself* degenerates to a boolean, and the graded
  computation only earns its keep once those assumptions (independence of
  alternative causes, no interaction) are relaxed, which they argue happens
  essentially always in the real world. **This is directly relevant**: even
  the field's own graded-strength theory has a boolean degenerate case at
  its idealized center, and the graded machinery exists specifically to
  handle deviation from that idealization — which is closer to the shape
  this document ultimately recommends (§6-7) than to either pure extreme.
- A second, separate comment (PubMed 16060761, title consistent with "The
  power PC theory and causal powers: comment on Cheng (1997) and Novick and
  Cheng (2004)") was located but not fetched in full; its existence
  confirms the theory's cognitive-representation claim was contested from
  multiple directions, `[unverified beyond title/PubMed listing]`.

**Confidence: high** on the Cheng/Luhmann & Ahn content (fetched and read
the comment in full); **medium** on the second comment (title only).

### 2.3 Griffiths & Tenenbaum — structure vs. strength, and causal support as log-odds

Griffiths & Tenenbaum, "Structure and strength in causal induction"
(*Cognitive Psychology* 51(4), 2005) make a distinction load-bearing for
this whole document: **causal structure** (does a link exist at all?) and
**causal strength** (how strong is it, given that it exists?) are different
questions with different rational-analysis answers, and conflating them —
which most prior covariation models, including a naive reading of Cheng's
power PC theory, implicitly do — mispredicts human judgment in cases where
the two dissociate. Their own proposed measure for the structure question,
**causal support**, is formalized as a **Bayesian log-likelihood-ratio**
(log odds) comparing a graph hypothesis with the causal edge present against
one without it, marginalizing over strength parameters. Griffiths &
Tenenbaum, "Theory-based causal induction" (*Psychological Review* 116(4),
2009) generalizes this into a fuller theory-based Bayesian framework for
causal structure learning.

**Why this is the single most load-bearing citation for §5-6 below**: this
is the field's own best normative account of exactly the "existence vs.
degree" distinction the charter's fork (§4) turns on, and it is
**continuous and log-scaled by construction** — a real-valued log-odds, not
an integer, not a raw probability, and not a boolean. Any design that wants
a quantized causal-strength dimension has to answer, honestly, what happens
to this continuous quantity at the interface — which is exactly the
question this project's own `BASE-AS-DIMENSION` section (§5) was written to
answer for a different case (log2-scale) and generalizes cleanly to this
one.

**Confidence: high** on the causal-support formalization (consistent
description across the PMC-indexed abstract, the NIPS 2000 structure-
learning precursor, and the Cognitive Psychology paper's own listed
abstract framing); the full derivation was not re-worked from the fetched
text, so the exact functional form is reported as "a Bayesian log-odds
measure," not reproduced equation-by-equation.

### 2.4 Rescorla-Wagner and associative learning — the strongest case for "not a symbolic predicate at all"

Rescorla & Wagner's 1972 model of Pavlovian conditioning represents a
cause-effect (CS-US) link as a single scalar **associative strength** V,
updated trial-by-trial by a continuous error-correction rule:
`V(k+1) = V(k) + α(λ − V(k))`, where λ is the asymptotic strength the outcome
supports and α a learning-rate parameter. A 2023 review, "The Rescorla-Wagner
model, prediction error, and fear learning" (framed, per its own PubMed
listing, as "the culmination of Hume's theory of causation"), traces this
directly to Hume's associationist account of causal judgment: causation as
learned contingency, not perceived necessary connection, held as a
continuously-adjusted weight rather than a discrete symbolic fact.

**This is genuinely the strongest available reading of "that's not how
things are held"** in the charter's own words: under this account there is
no symbolic `implies` predicate anywhere in the mechanism at all — causal
belief just *is* a real-valued weight, full stop, with no privileged
boolean readout built into the representation. Two things temper how far
that reading can be pushed, both important for an honest verdict:

1. Rescorla-Wagner is a model of a specific, narrow experimental paradigm
   (Pavlovian conditioning: blocking, overshadowing, conditioned inhibition)
   — it was never proposed as a general theory of propositional/linguistic
   conditional reasoning ("if P then Q" over abstract predicates), and
   nothing in the literature surveyed here extends it to that domain
   directly. Applying it to the charter's actual target (a graph-resident
   `implies` edge over symbolic predicates, populated partly by *reading
   prose*, per `DEDUCTION_GENERALIZATION_RESULTS.md`'s live fish/swim
   demonstration) is an analogy across domains, not a direct transplant —
   the same caution `CROSS_DOMAIN_SHAPE_SPIKE.md` §3.4/§4.2 already
   establishes about forcing one container across domains that need
   different ones.
2. Even within its own domain, V is **continuous**, not quantized — it is
   the single cleanest "continuous associative weight" account found in
   this entire search, and it offers **zero precedent for discreteness**.
   Anyone citing Rescorla-Wagner as support for *quantized* causal strength
   would be citing it for the opposite of what it says.

**Confidence: high** on the model's mechanics and its Hume framing (multiple
consistent sources including a dedicated Scholarpedia article and the 2023
review's own framing); **medium** on the review's exact argument structure
(title/abstract-level only, full text not fetched).

### 2.5 Conditionals specifically — the well-replicated P(if P then Q) = P(Q|P) finding, and where it does and does not extend

This is a **separate literature from causal cognition** (§2.1-2.4), and the
charter's research brief was correct to insist they not be conflated: this
literature asks what "if P then Q" *means* and how its truth/probability is
judged, independent of whether P causes Q in the world (a conditional can be
definitional, mathematical, or arbitrary, with no causal content at all).

**The finding, checked directly rather than recalled.** Evans, Handley &
Over, "Conditionals and conditional probability" (*JEP:LMC* 29(2), 2003) and
the broader program formalized in Evans & Over, *If: Supposition,
Pragmatics, and Dual Processes* (Oxford, 2004) test three competing
hypotheses for what number people give when asked "how probable is 'if P
then Q'?": (a) the material conditional's probability, `1 − P(P∧¬Q)`; (b)
the conditional probability `P(Q|P)`; (c) the conjunction `P(P∧Q)`. The
review "The probability of conditionals: A review" (*Psychonomic Bulletin &
Review*, 2021, fetched via search-result synthesis after a login-wall
redirect blocked direct full-text access — `[unverified beyond the fetched
summary]`) and the earlier Oberauer & Wilhelm "meaning(s) of conditionals"
paper (fetched and read in a scanned/degraded form — the full text was not
cleanly extractable, but the abstract-level content was legible) both
converge on the same verdict: **(b) wins, decisively, across a large
replicated literature** — "the conditional probability hypothesis... is
inconsistent with the claim that causal conditionals are material
conditionals of elementary logic." This mechanism is formalized
psychologically as the **Ramsey test**: suppose P, then read off your
degree of belief in Q under that supposition (Ramsey, 1929/1990's
"General propositions and causality," the origin of the move — not
independently re-verified here, cited as the standard attribution given by
every source above).

**This is real, directly-relevant, well-replicated evidential support for
the creator's stated intuition**, and this document reports it as such
rather than hedging it into background noise: the dominant psychological
account of how people evaluate an "if P then Q" statement's *probability*
is not a fixed boolean at all, it is a **conditional-probability read-off**
— structurally the same operation, one level up, as this project's own sd
loop reading off a graded shape-fit rather than a hard match.

**What this finding does NOT establish, stated precisely (this is the part
easy to over-claim):**

1. **It is a finding about probability *judgments* of conditionals, not
   about conditional *inference*.** A different, also well-studied task —
   given "if P then Q" and "P," do you draw "Q" (modus ponens), or given
   "not-Q," do you draw "not-P" (modus tollens)? — is governed by a
   partially separate empirical literature, and the search performed here
   surfaced a genuinely conflicting claim: a search-result synthesis
   reported that "large-scale meta-analyses on conditional **inferences**
   [i.e. the endorsement-rate task, not the probability-judgment task]
   established that the mental model theory provides a better account of
   the data than... probabilistic accounts." **This document does not
   resolve that apparent tension** — it may reflect two genuinely different
   tasks each best modeled by a different theory (probability-of-the-
   conditional vs. willingness-to-draw-an-inference-from-it), which is
   itself informative (§4), or it may reflect competing camps each citing
   their own preferred meta-analysis. Flagged honestly as `[unverified,
   requires primary-source reading beyond this spike's scope]` rather than
   silently resolved in either direction.
2. **Johnson-Laird & Byrne's mental-models theory of conditionals**
   (*Psychological Review* 109(4), 2002) is not thereby refuted — it is a
   real, still-defended, still-actively-revised competitor (Mental Models
   Global Laboratory's own "critics" page, read via search synthesis, frames
   this as an ongoing live debate, not a settled one), and at least one
   critique found (Douven & Verbrugge, "Suppositions, extensionality, and
   conditionals," fetched via search listing only) argues the mental-model
   theory's own extensional semantics is *equivalent* to the material
   conditional it was built to move away from — i.e. the two theories may
   be less far apart, or the boundary between them less clean, than either
   camp's own framing suggests. `[unverified beyond title/abstract]`.
3. **Nothing in this literature is making a claim about a graph-resident
   node/edge SCHEMA.** This is psychology of judgment and reasoning, not
   knowledge-representation design; §6-7 below is where this document does
   that translation, and it is this document's own contribution, not a
   result lifted from a citable source.

**Confidence: high** on the P(if)=P(Q|P) headline finding (converging,
independently-worded description across four separate fetched/searched
sources: Evans et al. 2003, Evans & Over 2004, Oberauer & Wilhelm, and the
2021 review); **medium-low** on the modus-ponens/mental-model-wins claim
(single search-synthesis sentence, not independently verified against a
primary source, explicitly flagged as unresolved above rather than adopted).

### 2.6 Dual-process accounts — the strongest resolution candidate for §4

Sloman, "The empirical case for two systems of reasoning" (*Psychological
Bulletin* 119(1), 1996) proposes System 1 as **associative, automatic, fast**
and System 2 as **rule-based, deliberate, flexible, slow**, and argues both
can be active on the *same* problem simultaneously, sometimes producing
conflicting outputs a person can feel the conflict between (his own
canonical illustration: knowing a coin-flip sequence is fair (rule-based)
while still feeling HTHTHT is "less random" than HHHHHH (associative)).
Evans (dual-process reviews, TICS-era work) and Kahneman's *Thinking, Fast
and Slow* popularize the same split for judgment generally.

Directly for causal/conditional reasoning: search-result synthesis reports
that fast, associative (System 1) processing can still yield *normatively
correct* causal conclusions in some cases — i.e. the two systems are not
"associative-and-wrong vs. rule-based-and-right," they are two different
*mechanisms* that can converge or diverge on the same answer. A cited
critique (search-listed, not fetched in full) notes "slack in the
distinction" Sloman draws — the two-system split is influential but not
unanimously accepted as a clean architectural fact, `[unverified beyond
listing]`.

**Why this section is the load-bearing one for §4's fork.** If causal/
conditional cognition really runs on two distinct mechanisms — one fast,
graded, associative (closest to Rescorla-Wagner, §2.4); one slow,
deliberate, propositional (closest to the mental-logic / classical-deduction
end of §2.5) — that is a real empirical basis for keeping *something*
distinct at the processing level. But Sloman's own account (and the coin-
flip example specifically) is explicit that **both systems can be looking
at the same underlying content, from the same underlying evidence, and
disagree** — which is a claim about two *readouts*, not necessarily about
two independently-stored *facts*. That distinction is exactly what decides
§4.

**Confidence: medium-high** on the Sloman 1996 framing and its general
uptake (consistent across multiple independent search syntheses,
recognizable as standard textbook content); **medium-low** on the specific
"fast thinking can be normatively causal-correct" claim (single search
synthesis sentence, not independently verified against Sloman's primary
text).

### 2.7 Verdict on Q1

Reading §2.1-2.6 together, stated as plainly as the evidence supports:

1. **Causal-strength cognition and conditional-truth/probability cognition
   are real, separate literatures, correctly kept apart by the charter, and
   they agree on one thing: neither hands you a fixed boolean.** Causal
   power (§2.2) is an inferred latent that degenerates to boolean only under
   idealizing assumptions the field's own critics say rarely hold. Causal
   support (§2.3) is continuous log-odds by construction. Associative
   strength (§2.4) is a continuously-updated real number with no boolean
   readout built in at all. Conditional-probability judgment (§2.5) tracks
   a continuous conditional probability, not a truth-functional predicate.
2. **The pushback the material also demands:** the material conditional/
   classical-deduction end is not simply "wrong" or unsupported — it is the
   idealized limit Cheng's own theory collapses to (§2.2), it is one live
   pole of an unsettled mental-models-vs-suppositional debate that a
   meta-analysis apparently favors for the *inference* task specifically
   even while losing the *probability-judgment* task (§2.5, point 1), and
   it is a real, distinct processing mode under every dual-process account
   surveyed (§2.6). **A design that deletes the boolean/categorical case
   entirely would be contradicted by real evidence, not merely
   conservative.**
3. **The synthesis dual-process theory offers, and that this document
   adopts going into §4:** not "one is right and one is wrong," and not
   "they are unrelated" — two functionally real mechanisms that can operate
   on shared underlying content and can diverge in their readout. That is
   a *shape*, not a binary, and it is the same shape
   `CROSS_DOMAIN_SHAPE_SPIKE.md` §7.2 already found and corrected toward for
   a completely different pairing (physical vs. symbolic domains) — which
   is why §4.3 below reuses that document's own resolution move rather than
   re-deriving one from scratch.

---

## 3. Part 2 — is there real precedent for QUANTIZED causal strength?

### 3.1 Cognitive science: categorical judgment as an empirical fact, not (yet) a theory of quantization

The most directly relevant finding located is O'Neill, Henne, Bello, Pearson
& De Brigard, "Confidence and gradation in causal judgment" (*Cognition*
223, 2022, paper 105036) — read via a converging, detailed search-result
synthesis (the ScienceDirect abstract page itself 403'd; the finding is
reported consistently enough across independent search queries to trust at
**medium-high** confidence, `[not independently fetched in full]`). Their
result: when asked to rate causal strength on a continuous scale, human
judgments are **empirically multimodal** — heavily clustered at the
endpoints (effectively categorical: "yes it caused it" / "no it didn't") —
**with genuinely graded, in-between responses appearing specifically when
confidence is low.** Two candidate explanations were pitted against each
other: a *confidence* account (gradation reflects uncertainty about whether
a link exists) and a *strength* account (gradation reflects a genuinely
graded causal fact); the confidence account was the better-supported one in
their first experiment.

Separately, Cheng's own theory (§2.2) has always included a real
**categorical typology**, not a single strength scalar: *generative*
(facilitating) causes vs. *preventive* causes are modeled as structurally
distinct entities, not as a sign-flip on one shared continuum, and Cheng &
Novick (1991), "Causes versus enabling conditions," draws a further
categorical line between a CAUSE and an ENABLING CONDITION that, per the
search summary, "cannot be made in terms of necessity or sufficiency" alone
— i.e. even within a strength-oriented theory, some of the distinctions
that matter are **kind-distinctions**, not degree-distinctions. This maps
directly onto this project's own already-existing `inference_knowledge.json`
split between `knowledge_enabling` / `knowledge_causal` / `knowledge_goal`
`kind`s (§6.1) — a categorical typology this project independently landed,
for an unrelated reason, that the cognitive-science literature also
independently maintains.

**Honest verdict on quantization specifically, stated as the negative
finding it partly is:** neither of the two clusters above is a *theory of
quantized causal strength* in the sense the charter is asking about (a
strength dimension with discrete, ordered levels, the way pitch or a Likert
scale is discrete). The O'Neill et al. finding is a fact about the *response
distribution* people give (bimodal, not smooth) — it is evidence that a
purely continuous representation does not obviously explain the data, and
that something clusters responses toward extremes, but it does not itself
propose or test a quantized underlying representation, and confidence-driven
gradation is at least as compatible with "a continuous latent read out
through a categorical decision threshold" as with "a genuinely discrete
latent." **This document reports that as a real, useful negative finding
per its own instructions, rather than stretching it into more than it
shows.**

### 3.2 AI/ML: discrete causal representation learning — real, recent, structurally on-point

Zhang, Wang & Gu, "Discrete Causal Representation Learning" (arXiv
2603.25017, 2026 — fetched, abstract confirmed verbatim: *"Causal
representation learning seeks to uncover causal relationships among
high-level latent variables from low-level, entangled, and noisy
observations"*) is real, recent, and squarely on-point: it models a
**directed acyclic graph among discrete (categorical) latent causal
variables**, linked to observed data via a sparse bipartite measurement
graph, and proves **identifiability** — both the measurement graph and the
latent causal graph are recoverable from the observed distribution alone
under stated conditions, without relying on an uninterpretable deep net.
Its own stated motivation is direct: existing causal representation learning
either uses deep nets (uninterpretable, no formal guarantees) or imposes
"restrictive assumptions like linearity, continuous-only observations" — the
paper's whole contribution is showing that **going discrete is not merely
tolerable, it is what buys the identifiability guarantee**, on real
mixed-type (educational-assessment and image) data.

Schölkopf et al., "Toward Causal Representation Learning" (*Proceedings of
the IEEE*, 2021 — its "sparse mechanism hypothesis" is the broader framework
this 2026 paper extends) is the standard, oft-cited survey establishing the
field's general premise: causal variables should be *learned as latents*
distinct from raw observations, with independent causal mechanisms
composing over them. `[the sparse-mechanism-hypothesis framing is reported
at survey-summary level, not independently verified against primary text]`.

**Why this matters more than the cognitive-science half for this specific
question:** the field asking "should causal latents be discrete or
continuous" is a live, current, technically rigorous field, and the answer
it has converged toward — at least for one strong, identifiability-motivated
argument — is **discrete, for principled reasons, not merely
convenience**. This is real precedent, on the AI/ML side, for exactly the
representational move the charter's intuition wants. It was **not**
motivated by cognitive plausibility (it is a statistics/identifiability
argument), which is worth being honest about — it supports "quantized
causal representations are a legitimate, working design," not "quantized
causal representations are how brains do it."

### 3.3 Verdict on Q2

**Weak-to-moderate precedent, reported honestly rather than inflated.**
Cognitive science offers a categorical *typology* (generative/preventive/
enabling, §2.2/§3.1) that this project already independently has, plus a
2022 empirical finding that raw judgment is measurably non-continuous in its
*response distribution* — real, but short of a positive theory of
quantized *representation*. AI/ML offers a genuine, recent, principled case
for discrete latent causal variables — real design precedent, but explicitly
a statistical-identifiability argument, not a cognitive-plausibility one.
**Neither literature hands this project a ready-made "yes, quantize it, here
is how" answer** — which is exactly why §5-7 below is this document's own
design contribution, grounded in the evidence but not copied from it, and
why the charter's instruction to be ambitious rather than safe is doing real
work here rather than being rhetorical throat-clearing.

---

## 4. Part 3 — the fork: unify, or layer?

### 4.1 What favors UNIFY

1. **The Ramsey test (§2.5) is, on at least one serious philosophical
   reading, the SAME operation as a causal intervention.** A paper located
   in this search — Andreas, "A Ramsey Test Analysis of Causation for
   Causal Models" — argues explicitly that "Halpern and Pearl's causal
   model semantics may be regarded as containing a fully worked out version
   of the Ramsey Test." If evaluating a conditional's truth/probability
   (suppose P, read off belief in Q) is mechanically the same move as
   evaluating a causal claim under intervention (do(P), read off P(Q)),
   then conditional evaluation and causal-strength evaluation are not two
   representations that happen to resemble each other — they may be **one
   mechanism read from two linguistic surface forms.** `Confidence:
   medium` — this is a philosophy-of-causation paper making a formal
   semantic argument, not a psychological result about what representation
   people actually build; it supports unification as *coherent*, not as
   *empirically confirmed in human subjects*.
2. **Cheng's own power theory degenerates to boolean at its idealized
   center** (§2.2) — evidence that "graded strength" and "boolean
   implication" are not two different kinds of thing in that theory, they
   are the *same* quantity under different conditions (independence
   satisfied vs. violated). That is an argument *for* one relation kind
   with a parameter, not for two kinds.
3. **This project's own prior spike already found and corrected toward
   exactly this shape, for a different pairing.**
   `CROSS_DOMAIN_SHAPE_SPIKE.md` §7.2's headline, quoted directly because it
   is the load-bearing precedent this document reuses: *"Two things are not
   either identical or unrelated: they can be related by a transform, and
   the finding is the transform's parameter, not the endpoints... the
   question is not 'shared encoding or co-presentation binding,' it is
   'what governs which one a system lands on.'"* Read `implies` for the
   binary-encoding pole and `knowledge_causal` for the co-presentation pole
   in that document's own table, and the fork in this document's charter is
   structurally the identical question, one grain over.

### 4.2 What favors LAYER

1. **Dual-process accounts (§2.6) are a real, if contested, claim about
   TWO DISTINCT MECHANISMS, not one mechanism with a knob.** Sloman's own
   illustration (feeling a fair coin-flip sequence as "less random" while
   knowing it is not) is a case where the associative and rule-based
   systems produce *conflicting outputs from the same input*, which is
   harder to explain if they are the same underlying relation merely read
   at different points along one dimension — a single graded quantity does
   not normally disagree with itself.
2. **The apparent inference-task/probability-task split (§2.5, point 1)**
   — if genuinely real rather than an artifact of competing camps citing
   competing meta-analyses — would be direct evidence that different tasks
   recruit different representations of the *same* conditional content,
   which is closer to "two kinds that share a strength-like field" than to
   "one kind, one dimension." This document flagged this as unresolved in
   §2.5 and does not treat it as settled here either.
3. **`inference_knowledge.json`'s own existing categorical `kind` split**
   (`knowledge_enabling`/`knowledge_elaborative`/`knowledge_partwhole`/
   `knowledge_goal`/`knowledge_causal`, `seeds/inference_knowledge.json:1`)
   plus the already-landed sixth kind `knowledge_logical`
   (`DEDUCTION_GENERALIZATION_RESULTS.md` §2) is itself evidence that this
   project already treats "what kind of knowledge licenses this inference"
   as a categorical label the decode discriminates on — mirroring Cheng &
   Novick's cause-vs-enabling-condition categorical line (§3.1) — and *that
   part of the schema is working and should not be disturbed by a
   unification move aimed at strength specifically.*

### 4.3 Verdict — reusing `CROSS_DOMAIN_SHAPE_SPIKE.md`'s own resolution move

Read side by side, §4.1 and §4.2 are not actually in conflict — they are
answering two different sub-questions that the charter's single "unify or
layer" phrasing conflates, exactly the way the physical-vs-symbolic
question conflated encoding and pool in the prior spike (`§7.1`: *"unify
the vocabulary, keep the families apart"*).

- **§4.1's evidence bears on the STRENGTH FIELD**: is causal strength and
  logical certainty the same *kind of quantity*, at different points? Yes —
  Cheng's degenerate-boolean-limit and the Ramsey-test/intervention
  correspondence both say: same quantity, different point.
- **§4.2's evidence bears on the KNOWLEDGE-SOURCE / DISCRIMINATIVE KIND**:
  is a fragility-enabling-condition fact the same *category* of thing as a
  causal-power fact as a proof-grade deduction? No — dual-process
  mechanisms are genuinely distinct, and the project's own working
  `knowledge_*` taxonomy already discriminates on exactly this axis, for a
  reason unrelated to strength at all (which schema licenses the mint).

**So: unify the strength dimension, keep the kind taxonomy.** Concretely:
one relation kind carries a strength/certainty parameter that ranges,
Occam-ordered, from weak associative evidence up to proof-grade certainty
(§4.1's case for unification, applied narrowly to *this one field*); the
existing `kind` label (`knowledge_causal` vs. `knowledge_logical` vs.
`knowledge_enabling` etc.) stays exactly as it is, doing exactly the
discriminative job it already does (§4.2's case, left untouched). This is
not a compromise reached by splitting the difference — it is what happens
when the charter's single question is correctly read as two questions with
two different answers, the same diagnostic move `CROSS_DOMAIN_SHAPE_SPIKE.md`
made explicit as its own corrected §7.2.

---

## 5. Part 4 — the quantization basis, read against this project's own frame/continuum invariant

The charter names four candidate bases. Read against §2-4's evidence and
against `CLAUDE.md`'s own already-landed invariant, two of the four turn out
to be the SAME map read from its two ends, one is a different axis
entirely (not a strength axis at all), and one earns the recommendation.

**`CLAUDE.md:497-564`, quoted directly because it is the deciding
constraint, not merely background**:

> "**In-frame is INTEGER.**... **Non-integer math is CROSS-FRAME.** All
> real-valued structure... lives in the MAP between frames (a generator /
> `Transform` / base / comparator / rendering), NEVER in a frame's
> coordinates... **Continuity is INTENSIONAL only.** A continuous quantity
> is a RULE you APPLY... never an observed datum... **The decision
> procedure for every number you write:** *is this value IN a frame, or
> BETWEEN frames?* In-frame ⇒ it MUST be integer... Between-frames ⇒ it MAY
> be real."

This is not a stylistic preference this document is importing from outside
— it is the specific, already-battle-tested rule that resolved the
`scale2`/`modular` `DimensionGenerator` design (a log-scale "base" and a
cyclic "phase" are each a legitimate `DimensionGenerator`, not hand-set
config, `shape_decode.rs::apply_generator_once:822-847`), and this
document's job in this section is to run causal strength through the exact
same test, not invent a new one.

**Candidate 1 — evidential count/frequency.** Naturally integer (a count of
co-occurrence observations *is* an in-frame datum: this many times X
happened, this many times Y followed). Rescorla-Wagner's own trial-by-trial
formulation (§2.4) is, read at the *event* level rather than the
asymptotic-weight level, literally a sequence of discrete trials — the
raw material is already integer. **Verdict: this is a real in-frame
quantity, correctly integer, and belongs IN the graph as data — but it is
not itself a strength SCALE, it is the observation the scale is computed
from.**

**Candidate 2 — ordinal source-rank (proof > law > correlation > heuristic).**
This is real and this document recommends keeping it — but per §4.3's own
finding, it is not actually a strength axis at all, it is the **kind/
provenance** taxonomy `inference_knowledge.json` already has
(`knowledge_logical` vs. `knowledge_causal` vs. `knowledge_enabling`, §6.1)
wearing a different name. Folding it INTO the strength quantization would
re-commit exactly the conflation §4.3 just resolved. **Verdict: correct
axis, wrong bucket — it stays a categorical `kind`/`coherence` field, not a
strength quantum.**

**Candidate 3 — discretized log-odds/Bayesian posterior.** This is
Griffiths & Tenenbaum's causal support (§2.3), the field's own best
normative account of causal strength, and it is continuous by construction.
Per the frame/continuum invariant, a continuous quantity like this is not
disqualified — it is **relocated**: it cannot be an in-frame integer
attribute on an edge, but it is exactly the kind of thing a
`DimensionGenerator`'s cross-frame MAP is for, the same role `scale2`'s
×2^k warp and `modular`'s mod-n wrap already play.

**The resolution, and why candidates 1 and 3 are not actually competing
options:** causal support is a log-likelihood-RATIO computed FROM event
counts. Candidate 1 (count) is the in-frame observation; candidate 3
(log-odds) is what you get by APPLYING a real-valued map to a sequence of
those observations. This is not an analogy to `scale2` — it is the
identical shape: `scale2` takes an integer step `k` and applies a real-
valued map (×2^k) to render a stepped shape; a `logodds` generator would
take an integer evidence-count-step `k` and apply a real-valued map
(a log-likelihood-ratio update) to render a stepped causal-strength
reading. **The "evidential count vs. discretized log-odds" fork the
charter posed is not a fork — it is one cross-frame relation, and asking
"which one is the basis" is asking whether the input or the output of a
`DimensionGenerator` is "the" basis, which is not well-posed once the
generator exists.**

**The safe answer, and why it is not what this document recommends
(the point where the charter's "we are not here to be small and safe"
instruction is actually load-bearing, not rhetorical):** the conventional
move — the one every cited AI paper in §3.2 and every cited cognitive
theory in §2.1-2.4 actually makes — is to store causal strength as a
**raw float** on the edge: a probability, a log-odds, a power estimate,
whatever the theory computes, written down as-is. That is what Pearl's
structural equations hold, what Cheng's power *p* is, what Griffiths &
Tenenbaum's causal support is, what Rescorla-Wagner's V is, what the 2026
discrete-causal-representation paper's own *measurement* layer still is
even though its *latent* layer is discrete. **None of the literature
surveyed hands this project a ready-made quantized answer** (§3.3's
verdict) — building one is this project inventing something the field
has not, using a constraint (in-frame-integer) the field does not share
and was never asked to satisfy. That is exactly the "safer bet" the
creator's own instruction says to reject when the evidence still supports
the more ambitious move — and §6-7 makes the case that it does.

---

## 6. Grounding the design in what already exists

### 6.1 `inference_knowledge.json` today — read in full, not summarized

All 8 `ShapeSignature` schemas in `seeds/inference_knowledge.json` were read
directly (`:1-140`, quoted in the tool-use record above). The load-bearing
facts for this design:

- **Every schema is a `ShapeSignature` node** (the same node TYPE the whole
  sd-loop codebook pool uses — `SHAPE_TYPE_VOCABULARY_SPIKE.md`'s own
  "type = pool, kind = label within a pool" rule, reused verbatim by the
  already-landed `knowledge_logical` addition per
  `DEDUCTION_GENERALIZATION_RESULTS.md` §2). A causal-strength addition
  that stays inside this pool, as a new attribute rather than a new node
  type or a new pool, is the path every prior addition to this seed already
  took.
- **The two existing `knowledge_causal` schemas carry NO strength
  information at all today** — `physical_displacement_rise` and
  `physical_addition_overflow` (`seeds/inference_knowledge.json:93-114`)
  each supply only a structural `signature` (verb-pair patterns like
  `["physical_effect","drop","rise"]`) and `"supplies": {"relation":
  "cause"}` — a bare presence/absence relation, no strength field, no
  count, no confidence. **This is the same "fixed boolean" complaint the
  charter raised about `implies`, already present one schema-kind over,
  independently of today's deduction rung** — the charter's intuition
  generalizes further than its own framing named.
- **`knowledge_logical`'s new schema** (`logical_bird_can_fly`,
  `DEDUCTION_GENERALIZATION_RESULTS.md` §2) is a single-antecedent
  structural pattern decoded by the unmodified `ShapeDecode`/`Covers`
  machinery — genuinely categorical by construction (a `Covers` check is a
  yes/no structural match, `term.rs:3757-3785` per `CROSS_DOMAIN_SHAPE_
  SPIKE.md` §4.1's own read of that function), and per the correction
  worktree (§1.6), the SAME `implies` predicate is *also* the general
  reading construction's own predication for parsed conditional prose.
  **This machinery does not need to be rebuilt** — §7 below keeps it, as
  the ceiling case.

### 6.2 The `DimInfer`/`LatentDimension`/`Transform{dim,delta}` machinery — what it actually does, read from source

`seeds/shape_decode_loop.json`'s own module description (fetched and read in
full) states the pipeline this design plugs into: a residual decode ->
`sd_transform_decode` (rung 1: same shape, per-dimension delta) ->
`sd_infer_dimension` (rung 2: a MISSING dimension, selected from a held
`DimensionGenerator` codebook, mints a `LatentDimension{name:"latent:
<generator>", generator, k}` node) -> `sd_mint_quantum` (rung 3: genuine
novelty, only after both prior rungs fail). The `scale2` and `modular`
generators (v1.4.0/v1.5.0, same file) are the direct precedent this design
reuses: `scale2` is *"a MULTIPLICATIVE warp whose integer step k is a
LOG2-SCALE quantum"* — real-valued ×2^k math lives entirely inside
`scale_pow2_once`, never stored as a float; `modular` is the same shape for
a cyclic (mod-n) warp. **A `logodds` generator, mapping an integer evidence
step `k` to a real-valued log-likelihood-ratio update via
`apply_generator_once`'s existing dispatch shape (`shape_decode.rs:836-838`
is exactly where a fourth arm would sit, alongside `"scale2" =>
scale_pow2_once(...)`), is not a new kind of thing for this codebase — it
is the fourth instance of a pattern the third instance (`modular`) already
generalized from the second (`scale2`).**

---

## 7. FINAL RECOMMENDATION

**One concrete design, defended, not a menu.**

**7.1 The relation.** Keep `implies` (and its underlying `ShapeSignature{
kind:"knowledge_logical"}` schema, and the general `conditional` reading
construction it shares with `seeds/reading_constructions.json local_id 48`)
exactly as already built. Do not delete it, do not replace it, do not widen
its own `Covers`-based structural matching into something graded — per
§2.2/§2.7, a categorical, proof-grade case is real and evidenced, not a
design mistake to be dissolved. **Add, alongside it, a new
`LatentDimension` — `latent:causal_strength` — generated by a new
`DimensionGenerator{kind:"logodds"}`**, following §6.2's `scale2`/`modular`
precedent exactly: `coord_dims` naming the strength-bearing slot(s) on a
`knowledge_causal`/`knowledge_enabling` schema's `supplies`, `params`
unused (log-odds has no coordinate-remap matrix the way rotation/scale do —
this is a genuinely new generator *shape*, closer to a 1-D warp than to a
2-D coordinate map, and the honest residual named in §8 is exactly this: it
is not yet proven that `apply_generator_once`'s current signature, built for
coordinate remaps, is the right shape for a 1-D evidence-accumulation
generator without being tried).

**7.2 The unify/layer answer, stated without hedging.** UNIFY the strength
field, per §4.3: a `knowledge_causal` schema and a `knowledge_logical`
schema are decoded through the SAME `ShapeSignature` pool they already
share, and both can now carry a `has_latent_dimension` edge to
`latent:causal_strength` at a `Transform{dim:"latent:causal_strength",
delta:k}` step. **`knowledge_logical`'s existing boolean behavior is
recovered, not lost, as the CEILING quantum** — a proof-grade / structurally-
proven implication is causal-strength evidence at its maximum representable
`k`, exactly the way Cheng's own power theory degenerates to a clean 0/1 at
its idealized limit (§2.2) and exactly the way a rung-1 exact `sd_recognize`
match is the zero-residual limit of the same ladder every other grain in
this codebase already uses. LAYER the kind taxonomy, per §4.3: `kind`
(`knowledge_causal`/`knowledge_logical`/`knowledge_enabling`/...) stays
exactly as-is, untouched, doing the discriminative job it already does —
this design adds a field, it does not restructure the existing pool.

**7.3 The quantization basis, stated without hedging.** `logodds`, with
**integer evidence-observation count as the in-frame datum and log-
likelihood-ratio (Griffiths & Tenenbaum's causal support, §2.3) as the
cross-frame map**, per §5's finding that these are not competing candidates
but the two ends of one relation. Concretely: each observed
antecedent-then-consequent co-occurrence (or its absence, per Griffiths &
Tenenbaum's own base-rate-normalized formulation) increments an integer
count attribute held in-frame on the `knowledge_causal` `ShapeSignature`
node (or, per Rescorla-Wagner's trial-level reading, on a per-trial
`Observation` the schema aggregates over — this is the specific open
sub-question named in §8, not resolved here); `DimInfer`'s `logodds`
generator computes the log-likelihood-ratio from that count exactly the way
`scale_pow2_once` computes ×2^k from an integer `k`, and mints/steps the
integer `k` on the `Transform` node the same way every existing generator
already does. **Source-rank (proof > law > correlation > heuristic) is
explicitly NOT part of this dimension** — per §5, it stays where it already
lives, as the `kind`/`coherence` categorical field.

**7.4 Why this is the ambitious answer and not the safe one, stated
directly per the creator's own instruction.** The safe design — the one
every cited source in §2-3 would hand you without complaint — is a raw
float `strength` attribute on a causal edge. This project's own already-
proven, already-landed frame/continuum invariant (§5, `CLAUDE.md:497-564`)
forbids that, and the honest cost of following it here is real: it requires
inventing a `DimensionGenerator` shape (`logodds`) that is not a coordinate
remap like every existing generator, has no cited precedent for its exact
Rust signature, and needs its own design pass before it can be built — none
of which this document is claiming is free or already solved. **That cost
is the ambitious bet the creator's instruction asked for**: applying an
architectural commitment this project made for a completely different
reason (spatial/visual quantization) to a domain (epistemic/causal
strength) no cited source in cognitive science or AI has quantized this
way, because the field's own reason for going discrete elsewhere (§3.2's
identifiability argument) is not this project's reason (§5's frame
discipline) — two independent paths arriving at "discretize it," for
different reasons, which is exactly the kind of convergence
`CROSS_DOMAIN_SHAPE_SPIKE.md`'s own §9-10 treats as evidence a shape is
real rather than accidental.

---

## 8. What this document does NOT establish — named honestly, for a follow-on spike

1. **The `logodds` generator's exact Rust shape is not designed here.**
   `apply_generator_once` (`shape_decode.rs:836-847`) dispatches on
   `coord_dims`/`params`/`matrix`/`offset` — a signature built for
   coordinate-space remaps (rotate/scale/reflect/wrap). Whether a 1-D
   evidence-accumulation warp fits that signature cleanly, needs a new
   `Generator` field (an accumulator, not a fixed matrix), or needs a
   different Term entirely is an open engineering question this research
   document is explicitly not answering — naming it is the correct move
   per this document's own charter, building it is not.
2. **Where the integer evidence count actually lives is not decided.**
   §7.3 named two candidates (an aggregate counter on the
   `ShapeSignature` node itself, vs. per-trial `Observation` nodes the
   generator aggregates over at decode time) without picking between them;
   Rescorla-Wagner's own trial-level formulation (§2.4) argues for the
   latter, but this project's existing `knowledge_*` schemas are all
   currently authored as static seed data, not accumulated from live
   trials, and reconciling those two facts is real design work.
3. **The apparent inference-task/probability-task split named in §2.5 point
   1 was flagged, not resolved.** If mental-models theory genuinely wins
   the modus-ponens-endorsement task while the suppositional/probabilistic
   theory wins the probability-judgment task, that is a *second* fork this
   design does not currently address — it may mean `implies`'s existing
   `Covers`-based structural matching (§6.1, the inference/deduction side)
   and the new `logodds` dimension (the probability/strength side) are
   *already* the right split for exactly this reason, which would be a
   pleasing confirmation, but this document did not verify the primary
   meta-analyses closely enough to claim that confirmation rather than
   merely notice the possible match.
4. **No live measurement was run.** Per this task's own framing (RESEARCH,
   not build), nothing in §7 has been tried against real graph data — the
   design is grounded in read source and read literature, not in a run.
   The natural next rung, if this document's recommendation is picked up,
   is a PREREG for exactly `logodds`, sized the way
   `RULE_REFERENCE_LAYER_SIZING_RESULTS.md` sized the rule-mirroring
   question before building it: measure how many existing/plausible
   `knowledge_causal` observations would actually populate the count field
   before committing to the generator's shape.
5. **Confidence ledger, honestly totaled.** High-confidence citations:
   Cheng 1997 + Luhmann & Ahn 2005 (§2.2, fetched/read), Griffiths &
   Tenenbaum's causal-support framing (§2.3, converging sources),
   Rescorla-Wagner mechanics (§2.4, converging sources), the P(if)=P(Q|P)
   finding (§2.5, four converging sources), the `CROSS_DOMAIN_SHAPE_SPIKE.md`
   §7.2 precedent (§4.1/§4.3, directly read in this tree). Medium-to-low
   confidence, named as such throughout rather than smoothed over: the
   Rottman & Hastie Markov-violation specifics (§2.1), the second Cheng
   comment paper (§2.2), the O'Neill et al. 2022 finding (§3.1, search-
   synthesis only, direct fetch blocked), the Ramsey-test/Halpern-Pearl
   correspondence (§4.1, one philosophy paper), and the modus-ponens/
   mental-model-wins claim (§2.5 point 1, single unverified sentence).

---

**Worktree:** `/home/matt/ozmadev/ocelot-worktrees/causal-linkage-dimension-research`
**Branch:** `causal-linkage-dimension-research`
**Base:** `main` @ `080bc88` (`Merge blob-edge-analogy-extension: _pair_witness wired into blob-edge minting, GO`)

Not merged into `main`. This is a research document only — no code, no
seeds, no schema changes were made or proposed as diffs; §7's design is a
recommendation for a follow-on build rung, not a build.
