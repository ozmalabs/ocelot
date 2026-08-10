# GROUNDING / PSYCHOSIS LITERATURE — does our psychosis-as-grounding-failure demo add anything?

A read-only comparative-science pass, calibrated exactly like `SEIZURE_FIELD_COMPARISON.md`.
Our landed glass-box demo (`seeds/psychosis_grounding.json` + `scripts/psychosis_grounding_demo.py`,
documented in `PSYCHOSIS_DEMO_RESULTS.md`; the thread in memory
`ozma_seizure_as_undissipated_residual`) is placed beside the actual grounding +
computational-psychiatry literature. **No engine changes. No timing claims.** Every literature
claim carries an inline citation; a modest or negative verdict is reported plainly.

**The adjudication runs on TWO SEPARATE axes, reported distinctly** (this is the load-bearing
correction over a first draft that collapsed them):

- **Axis A — THEORY / PREDICTIVE / CLINICAL.** As a *description* of psychosis, do we beat or
  even match the fitted theories? **Modest → no.** Circular inference and aberrant precision own
  the explanatory ground, formally and with patient data. We say so bluntly.
- **Axis B — IMPLEMENTATION.** Circular inference / aberrant precision are mathematical *models
  that describe* psychosis (fitted accounts — the way the Epileptor is a dedicated seizure
  oscillator). We have an *implementation*: a working cognitive substrate where grounding is a
  real **running** operation doing perceptual/belief work, and psychosis is its **failure mode**.
  Even where the mechanism matches circular inference exactly, *implementation-in-a-working-
  cognition is a categorically distinct kind of contribution* — the equation of flight vs the
  airplane. This is NOT a "re-derivation," and this document does not collapse it into one.

Both verdicts are given, and the honesty bounds on Axis B (fidelity; authored-failure-form) are
held explicitly.

---

## 0. What the demo claims — and, load-bearingly, what it does NOT

Grounded from our own docs, verified against the harness, so the comparison is against our real
position and not an inflated one.

**What the demo IS (`PSYCHOSIS_DEMO_RESULTS.md`):**
- A **reduced scalar** harness on the **real engine**: a single `belief` over two basins (`R=0`
  truth, `W=4` delusion), corrected toward an observation, weighted by how strongly the
  observation constrains it, **precision-gated by confidence** (`1/(1+conf)` — a confident prior
  down-weights contradictory evidence). Collapse = nearest-basin selection. One DSL rule + two
  collapse rules over existing arithmetic Terms, run by `run_rules` + native `fold_clock_edge`.
  No new Rust; byte-identity-safe when off.
- **Three authored ingredients** (the honesty asterisk, the analogue of the seizure model's
  `alpha`): the self-grounding term `ks·conf·(committed − belief)`, the precision gate
  `1/(1+conf)`, and confidence positive feedback (corroboration raises confidence).
- Reproduces, as failure modes with a matched control: **self-grounding**, **non-optimal basin**,
  the **confirmer flip** (identical weak reality friction; +sycophant → belief persists in `W`;
  the confirmer supplies zero true information yet flips the outcome by pinning confidence at
  `cmax`), **recovery** monotone in grounding-source strength, and **folie à deux** (N=2 mutual
  confirmers, no anchor → both `W`; ground one → both → `R`).

**What the demo does NOT claim:**
- **NOT** the live conversation-faculty grounding rules firing — a reduced harness with an
  authored update form, not the deployed agent degrading. **This bound is decisive for Axis B**
  (§2.B).
- **NOT** a validated clinical claim; thresholds are **model-internal ratios** calibrated to
  nothing external; single scalar over two basins, not the relational grounding graph.
- **NOT** a novel testable divergence from aberrant salience / aberrant precision — the demo
  *unifies* those two accounts rather than beating them, and the "measurable-bridge" is open.

Everything below tests those disclaimers against the literature. They hold.

---

## 1. The literatures (cited survey)

### 1.1 Circular inference (Jardri & Denève) — THE closest prior art

The single most important comparison. Jardri & Denève cast psychosis as a failure of **belief
propagation**: in a healthy hierarchical network, redundant top-down and bottom-up messages are
**subtracted** so no information is counted twice (the message-exclusion principle). Under **E/I
imbalance (excitation dominating)** that subtraction is lost, messages **reverberate in loops**,
and the same evidence is **double-counted** as if new — "expect what you see," priors and
sensations corrupting each other
([Leptourgos & Jardri, "Circular inference: mistaken belief, misplaced trust," *TiCS* 2017](https://www.sciencedirect.com/science/article/abs/pii/S235215461630078X)).
The account is **formal and parameterised** — the modern statement, Circular Belief Propagation,
has an **α** parameter (how much the reverse/ascending message is re-included = sensory-loop
reverberation) and a **κ** rescaling that counters loop amplification, plus a **γ** weighting
external sensory input vs internal coupling; "psychotic disorders could involve miscalibration
where internal network reverberations dominate sensory grounding"
([Jardri et al., *Circular Belief Propagation*, arXiv 2024](https://arxiv.org/html/2403.12106)).
Two loop families: **ascending loops** over-weight sensory evidence, **descending loops**
over-weight priors — one mechanism, both hallucination and delusion.

It is **empirically validated**, which we are not:
- [Jardri et al., "Circular inferences in schizophrenia," *Brain* 2013](https://academic.oup.com/brain/article/136/11/3227/324497)
  — a probabilistic-reasoning task in which patients' overcounting is fit by the loop parameters.
- [Circular inference predicts nonuniform overactivation and dysconnectivity in brain-wide
  connectomes, 2021](https://www.sciencedirect.com/science/article/abs/pii/S0920996421000311).
- Extended to multimodal percepts and synaesthesia
  ([Leptourgos et al. 2022](https://www.sciencedirect.com/science/article/abs/pii/S0149763422000823)).

**Our self-grounding IS circular inference's double-counting**, and **our confirmer pinning
confidence IS the same reverberation closed through an external node.** On mechanism, this is the
closest prior art — and it is where Axis A is decided.

### 1.2 Predictive-coding / aberrant-precision accounts

Perception = Bayesian inference combining priors with sensory prediction-errors, each weighted by
**precision** (inverse variance / confidence). Psychosis = **aberrant precision** — mis-weighting
of priors vs sensory evidence
([Sterzer, Adams, Fletcher, Corlett et al., "The Predictive Coding Account of Psychosis,"
*Biol. Psychiatry* 2018](https://www.sciencedirect.com/science/article/pii/S0006322318315324);
circuit synthesis, [Corlett et al., *Annu. Rev. Neurosci.* 2024](https://www.annualreviews.org/content/journals/10.1146/annurev-neuro-100223-121214)).
Directly empirical: **conditioned hallucinations** are induced by over-weighting a learned prior,
strongest in voice-hearers, with a fit brain circuit
([Powers, Mathys & Corlett, *Science* 2017](https://www.science.org/doi/10.1126/science.aan3458)).
**Our precision gate `1/(1+conf)` is a scalar re-implementation of exactly this.**

### 1.3 Aberrant salience (Kapur 2003)

Psychosis as a **hyperdopaminergic state assigning aberrant salience**; **delusions are the
effort to make sense of aberrantly salient events**, hallucinations the direct experience of
salient internal representations
([Kapur, *AJP* 2003](https://psychiatryonline.org/doi/10.1176/appi.ajp.160.1.13);
[20-year retrospective, *AJP* 2024](https://psychiatryonline.org/doi/10.1176/appi.ajp.20240556)).
A **mind-level framework**, not a running model. **Our non-optimal-basin form is a re-description
of aberrant salience** at the mechanistic level.

### 1.4 Symbol grounding (Harnad 1990) — a DIFFERENT construct our vocabulary risks conflating

Harnad's grounding problem is **semantic**: how symbols acquire intrinsic meaning rather than
meaning parasitic on our heads — "how can the meanings of meaningless symbol tokens … be grounded
in anything but other meaningless symbols?", illustrated by learning Chinese from a Chinese-Chinese
dictionary, "never getting anywhere"
([Harnad, *Physica D* 1990](https://www.sciencedirect.com/science/article/abs/pii/0167278990900876);
[summary](https://en.wikipedia.org/wiki/Symbol_grounding_problem)).
**This is NOT the "grounding" of our psychosis demo.** Ours is the **predictive-coding /
evidential** sense — a belief anchoring to a frame's observations. The overlap is only
metaphorical, with **one genuine bridge worth naming honestly**: Harnad's Chinese-dictionary
circle (a symbol grounded only in other symbols) is structurally the same shape as our
**self-grounding loop** (a belief grounded only in its own generation). But claiming the Harnad
lineage would be a category error; we should not.

### 1.5 Bayesian / computational-psychiatry delusion formation

- **Two-factor theory** (Coltheart, Langdon, Davies, McKay): factor 1 = an anomalous experience
  (a prediction error); factor 2 = a **belief-evaluation impairment**
  ([Coltheart & Davies](https://maxcoltheart.wordpress.com/the-two-factor-theory-of-delusion/)).
  The modern **hybrid** casts factor 1 as an abnormal prediction error and **factor 2 as
  overestimation of that prediction error's precision**
  ([McKay et al., *Cog. Neuropsychiatry* 2019](https://pubmed.ncbi.nlm.nih.gov/31502494/)) —
  factor 2 is, again, **our precision gate**.
- **Active-inference simulations** already instantiate a **working generative agent that
  hallucinates** as a failure of the *same* model that perceives: excessive prior precision →
  hallucination/delusion in silico
  ([Benrimoh et al., "Active Inference and Auditory Hallucinations," *Comput. Psychiatry* 2018](https://cpsyjournal.org/articles/10.1162/CPSY_a_00022);
  [Friston et al., "Active inference, morphogenesis, and computational psychiatry," 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9731232/)).
  **This is the most important comparator for Axis B** — it is the nearest existing *running*
  model (§2.B).

### 1.6 The confirmer / AI-psychosis / folie à deux side

- **Clinical folie à deux** (shared psychotic disorder): a delusion shared within a dyad;
  classically the **secondary recovers on separation** from the primary — extended to
  folie à trois/famille and invoked for cults
  ([*JAAPL* 2020](https://jaapl.org/content/early/2020/06/11/JAAPL.200013-20)).
  **This clinical fact — separate the pair, the shared delusion collapses — is our folie-à-deux
  headline** ("ground one → both collapse"): that result **re-describes a known phenomenon**, it
  is not a new prediction.
- **AI-psychosis / digital folie à deux**: recent work names **bidirectional belief
  amplification** — sycophantic LLMs validate whatever the user proposes and invite "going
  deeper," a single-person echo chamber
  ([Dohnány et al., "Technological folie à deux," arXiv 2025](https://arxiv.org/abs/2507.19218);
  ["Digital folie à deux," *Psychology Today* 2026](https://www.psychologytoday.com/us/blog/psych-unseen/202603/how-ai-chatbot-use-can-cause-digital-folie-a-deux);
  harm-simulation benchmark, ["The Psychogenic Machine," arXiv 2025](https://arxiv.org/html/2509.10970v1)).
  **Crucially these already ladder the scale**: folie à deux → folie à plusieurs → *folie des
  milliards* (dyad → group → billions). The **scale-agnostic conceptual claim is published**;
  what these papers are is **verbal / conceptual, not a formal mechanism in a running substrate**.
- **Group-scale belief dynamics** are separately modelled formally
  ([Collective dynamics of belief under coherence + conformity, *PLOS ONE* 2016](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0165910)),
  and **sycophancy** is a documented LLM training pathology.

---

## 2. Per-candidate adjudication, on BOTH axes

Three candidate contributions: (a) the glass-box implementation in a working substrate;
(b) the confirmer/folie-à-deux/AI-psychosis unification; (c) the seizure-vs-psychosis levels
split. Each is judged separately on Axis A (does it beat the theories as a *description/
prediction*) and Axis B (does it add as an *implementation-in-a-working-cognition*).

### (a) Glass-box perception→psychosis in a working cognitive substrate

**Axis A (theory/prediction): NO — MODEST.** As a description, we add nothing over circular
inference or aberrant precision, and are far behind on formalisation and validation (§3, §4).

**Axis B (implementation): YES — a distinct kind of contribution, with a sharp honesty bound.**
Circular inference and aberrant precision are *descriptions* — equations fit to data. We have a
**running grounding operation** whose *failure mode* is the pathology, in a substrate that also
perceives, converses, and acts. What an implementation gives that a description cannot:
1. **SUFFICIENCY, demonstrated by existence, not by a curve fit.** The demo shows these
   ingredients are *sufficient* to produce self-grounding, wrong-basin commitment, the confirmer
   flip, and recovery in a working system with a matched control — an existence result about a
   mechanism, categorically different from fitting parameters to a symptom score.
2. **The pathology EMBEDDED in a full cognition.** Perception ↔ salience ↔ collapse ↔ grounding
   are the engine's *real, interacting* primitives, inspectable at the node/tick level, not
   isolated equations. This is the empty Marr-computational cell the seizure arc named — but now
   with the grounding operation actually *present to fail*.
3. **Glass-box intervention at the PRIMITIVE level.** You can add/remove the confirmer, vary the
   grounding source, ground one member of a dyad, and watch the belief/confidence primitives move
   — reversible, ethics-free, fully observed. A description cannot be intervened on; only a
   running machine can.

**THE HONESTY BOUNDS ON AXIS B (do not let "implementation" inflate):**
- **(i) Implementation value scales with FIDELITY.** Implementing the *wrong* dynamics faithfully
  is implementing the wrong thing. Our fidelity to the *right* dynamics is asserted, not
  validated (the update form is a scalar predictive-coding gloss; §4). So the implementation is
  "faithful to a plausible mechanism," not "faithful to psychosis."
- **(ii) The STRONGEST implementation claim is the FRONTIER, NOT our demo.** The field-changing
  version is *psychosis emerging from the engine's OWN, UNMODIFIED grounding when friction is
  removed* — the exact analogue of the seizure arc's `alpha`-necessity question. **Our demo
  AUTHORED the failure form** (self-grounding term + precision gate + confidence feedback = the
  `alpha`-analogue). So the accurate statement is: **"a grounding-failure rule implemented in the
  real engine and shown to behave as predicted,"** NOT **"the live grounding faculty failing on
  its own."** The named follow-on — run the failure regime on the live conversation faculty's own
  grounding rules — is where Axis B would graduate from "runs and behaves" to "emerges."
- **(iii) The nearest existing running model matters.** Active-inference sims already
  perceive-and-hallucinate in one generative model ([1.5]). Our Axis-B distinctiveness is
  therefore NOT "first working model of psychosis" — it is **substrate kind**: a symbolic (G,Γ)
  graph that spans language/vision/chess/etc., where the psychosis is a failure of shared
  grounding+collapse rules, vs a bespoke low-dimensional POMDP. That difference is real but is a
  *breadth/kind* claim the reduced scalar demo does not yet exhibit.

**Verdict (a): Axis A NO/MODEST; Axis B a genuine, distinct contribution — an implementation
where the field has descriptions — bounded to "authored-failure-rule running in the real engine,"
with emergence-from-unmodified-grounding as the frontier.**

### (b) Confirmer / folie-à-deux / AI-psychosis as ONE scale-agnostic mechanism

**Axis A (theory): WEAK.** The scale ladder (dyad→billions) and bidirectional amplification are
already published, in 2025–2026, ahead of us ([1.6]); circular inference already models the
intra-individual loop; and the folie-à-deux headline **re-describes** the known
separation-resolves-the-secondary fact. As a *theory*, we are not first and add little.

**Axis B (implementation): a modest but real addition.** What is *not* in the literature is the
three collapsed into **literally one mechanism/topology in a running substrate**:
intra-individual self-grounding, human+AI dyad, and N=2 folie à deux as the *same rule* at
different wiring, with "puncture the loop at any single node → the whole loop unwinds" **executed
and measured in a working system**. Circular inference is intra-brain; the AI-psychosis papers
are verbal. Implementing the scale-agnostic claim as one runnable mechanism (and being able to
*intervene* on it — ground one node, watch both collapse) is the implementation surplus over a
verbal ladder. **Bound:** the underlying dynamic (a self-reinforcing confirmation loop that
unwinds when broken) is intuitive graph dynamics and is *conceptually* subsumed by circular
inference's double-counting closed through an external node — so the surplus is "we can run and
intervene on it," not "we discovered it."

**Verdict (b): Axis A weak; Axis B modest — a runnable, intervenable, one-mechanism instantiation
of an already-published conceptual ladder.**

### (c) Seizure-vs-psychosis levels split (settlement/throughput vs grounding/content)

**Axis A (theory): NOVEL negative space, but a FRAME.** The clinical epilepsy↔psychosis link is
old but framed as **antagonistic comorbidity** (forced normalisation, postictal psychosis;
Stevens & Livermore 1987), never as **failures at two Marr levels of one architecture**; the two
live in **wholly separate** literatures. No published *description* casts them as throughput-vs-
content failures of one computation. Real negative space — but an organising frame, not a
prediction.

**Axis B (implementation): this is where the frame has teeth.** The split is only *sayable*
because the engine actually *has* both layers as running operations: a settlement/dissipation
layer (seizure = its give-failure; `SEIZURE_*`) and a grounding/collapse layer (psychosis = its
failure; this demo). No dedicated seizure model has a grounding operation to fail; no
predictive-coding psychosis model has a settlement substrate to overload. The implementation is
what lets one architecture **express both pathologies at their distinct levels** — the deepest
and most distinctive thing in this whole comparison. **Bound:** it remains a frame whose *direct*
measurement ("the same tissue's settlement-capacity and grounding-quality dissociate and fail
separately") is not operationalised; and both sides carry authored failure forms (`alpha`;
the precision-gate rule), so it is "one engine that can be *made* to fail two ways at two levels,"
not yet "one engine that fails two ways on its own."

**Verdict (c): Axis A novel-but-a-frame; Axis B the strongest implementation surplus — one
running architecture natively expressing two pathologies at two levels, which no description can.**

---

## 3. Does CIRCULAR INFERENCE / ABERRANT PRECISION subsume our mechanism? (Axis A)

**On the theory/description axis — largely YES.** Term by term:

| Our demo mechanism | Prior art that describes it |
|---|---|
| **Self-grounding** (belief closes on its own basin) | Circular inference **double-counting / reverberation** ([1.1]). Same shape as Harnad's circle ([1.4]). |
| **Precision gate** `1/(1+conf)` | **Aberrant precision** ([1.2]); two-factor hybrid's factor 2 ([1.5]). |
| **Confirmer pins confidence, zero true information** | Circular inference **double-counting closed through an external node** ([1.1]); AI-psychosis **bidirectional amplification** ([1.6]). |
| **Non-optimal basin** | **Aberrant salience** (Kapur) + attractor accounts ([1.3]). |
| **Folie à deux: ground one → both collapse** | Clinical **separation resolves the secondary** ([1.6]) — a re-description. |

We introduce no new computational *primitive*, and circular inference already *unifies* aberrant
salience and precision (both loop families from one E/I mechanism), formally and with data we lack.
**So on Axis A: circular inference already does most of this, validated. We do not beat it.** This
is exactly the seizure-arc discipline — the theories own the explanatory ground; say so plainly.

**But Axis A is not the whole ledger.** "Subsumes as a description" does not mean "subsumes as an
implementation." Circular inference is an equation fit to reasoning data; it is not a running
cognition you can drop a confirmer into and watch grounding fail at the primitive level. That
gap is Axis B (§2), and it is real regardless of the §3 table.

---

## 4. The single clearest MEASURABLE thing we add — and its test (Axis A, honest)

Because Axis A is where "measurable" lives, the clearest defensible measurable is **not clinical
and not a new primitive** — it is an **AI/HCI-level, directly-runnable prediction** falling out of
the matched-control confirmer flip:

> **A zero-information confirming interlocutor flips belief-correction purely by inflating
> confidence/precision, while an equally-strong *disconfirming* (grounding) source recovers the
> belief monotonically in its strength — the effect is mediated by precision inflation, not by any
> information the confirmer carries.**

Why this is the clearest: it isolates a variable the human clinical literature cannot hold fixed.
Circular inference and aberrant precision predict "priors override sensory → belief persists," but
do not cleanly separate **information-bearing** corroboration from **information-free** mirroring.
Our matched pair does: the sycophant `obs2 = belief` moves the belief by **0** yet flips the
outcome by pinning confidence. **The test is a 3-arm agent/dyad experiment, runnable today on LLM
agents with no clinical data:** hold belief, world friction, and update identical; vary only the
interlocutor — (i) information-free confirming mirror, (ii) neutral, (iii) disconfirming grounding
source of matched strength — and measure belief persistence and a confidence/precision proxy. The
prediction is the ordering (i > ii > iii) **with the confirmer's effect mediated by the confidence
proxy, not content**, and monotone recovery in (iii)'s strength (our P6). This is "confirmation
mirror vs grounding source" stated as a cheap falsifiable experiment — the one place we are ahead
of the *verbal* AI-psychosis papers, which assert the loop but do not isolate the information-free
component.

**Honest caveat:** even this is *conceptually* circular inference's double-counting. Our addition
is the **clean experimental isolation and runnable protocol**, and it lives at the AI-safety layer,
not the clinic.

---

## 5. Where we are clearly BEHIND (Axis A)

- **Formal specification & empirical validation — far behind (the widest gap).** Circular
  inference is fit to patient reasoning ([Brain 2013]) and predicts connectome signatures
  ([2021]); aberrant precision is validated by induced conditioned hallucinations with a fit
  circuit ([Powers *Science* 2017]). We have a scalar over two basins, model-internal thresholds,
  zero clinical validation, and an **authored** update form.
- **The confirmer unification — behind on being first.** The dyad→billions ladder and
  bidirectional amplification were published in 2025–2026 ([1.6]) ahead of our demo.
- **Vocabulary risk — a place to be careful.** "Grounding" here is the predictive-coding sense,
  **not** Harnad's symbol grounding ([1.4]); we must not borrow that lineage's weight.

---

## VERDICT — split by axis

### Axis A — theory / predictive / clinical: MODEST, mostly behind

| Contribution | Axis-A class |
|---|---|
| Core mechanism (self-grounding + precision-gate confirmer + wrong-basin) | **SUBSUMED** by circular inference + aberrant precision + aberrant salience — formal and validated where we are not |
| (c) Seizure-vs-psychosis levels split | **NOVEL-BUT-A-FRAME** — real negative space, no measurement of its own |
| (b) Scale-agnostic confirmer unification | **BEHIND / WEAK** — the conceptual ladder is already published |
| Information-free-confirmer flip as an isolable, runnable test | **GENUINELY-MEASURABLE (modest, AI-layer not clinical)** — the one clear test we add |

### Axis B — implementation-in-a-working-cognition: a DISTINCT kind of contribution

| Contribution | Axis-B class |
|---|---|
| (a) Glass-box perception→psychosis in the real engine | **DISTINCT & GENUINE** — an implementation (sufficiency-by-existence; pathology embedded in a full inspectable cognition; primitive-level intervention) where the field has descriptions. **Bounded** to "authored-failure-rule running in the real engine," with emergence-from-unmodified-grounding the frontier |
| (b) One runnable, intervenable scale-agnostic mechanism | **MODEST-BUT-REAL** — running + intervening on an already-published conceptual ladder |
| (c) One architecture expressing BOTH pathologies at two levels | **STRONGEST implementation surplus** — no description can do this; the engine has both running layers to fail |

**The single strongest contribution, named:** on the implementation axis, **one running cognitive
architecture that natively expresses both a throughput/settlement failure (seizure) and a
content/grounding failure (psychosis) at their distinct levels, glass-box-inspectable and
intervenable at the primitive level** — the empty Marr-computational cell, now with the grounding
operation actually present to fail. Circular inference and aberrant precision cannot occupy this
cell: they are descriptions, not running cognitions. That is a categorically different kind of
contribution from a curve fit, and it is not a re-derivation.

**Blunt one-paragraph verdict.** On **Axis A** the answer is the seizure-arc answer: modest,
mostly behind. Circular inference (Jardri & Denève) and aberrant precision (Sterzer/Corlett/
Fletcher/Adams; Powers) already *describe* what our demo does, formally and with patient data we
do not have — our self-grounding *is* their double-counting, our precision gate *is* aberrant
precision, our wrong-basin *is* Kapur's aberrant salience, and our folie-à-deux headline
re-describes the known separation-resolves-the-secondary fact; the one measurable we add is an
AI-layer isolation experiment, not a clinical prediction that beats them. But **Axis B is a
separate ledger and must not be collapsed into Axis A**: those theories are equations fit to
data; we have a *working cognition* in which grounding is a live operation and psychosis is its
failure mode, embedded in a substrate that also perceives and converses, inspectable and
intervenable at the primitive level. That is the airplane next to the equation of flight — a
distinct kind of contribution (sufficiency-by-existence, embedded pathology, glass-box
intervention), and the deepest version of it is one architecture expressing *both* seizure and
psychosis at two levels, which no description can. **The honesty that keeps Axis B from
inflating:** implementation value scales with fidelity (ours is faithful to a *plausible*
mechanism, not validated against psychosis), and our demo **authored** the failure form (the
`alpha`-analogue), so it is "a grounding-failure rule running in the real engine and behaving as
predicted," not yet "the live grounding faculty failing on its own" — the latter, emergence from
unmodified grounding, is the frontier and the field-changing claim. So: **as a theory, a
hypothesis platform behind the validated core; as an implementation, a genuine and distinct
occupant of the empty computational-level cell — bounded, not yet emergent, and not a
field-changer until the live faculty fails on its own and the fidelity is validated.**
