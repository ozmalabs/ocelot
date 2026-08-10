# Bigville dual-process conduct architecture — check against the science

**What this is.** An adjudication of a proposed upgrade to the substrate's
core decision/conduct architecture against the cognitive-science, decision-
neuroscience, and criminology literatures. Design/analysis only — no code, no
seeds. The creator's ask, verbatim: *"check this against scientific literature
and see if we have gone far enough or we are on track."*

**Discipline of this document.** Every citation below was verified against a
primary source or its abstract during this pass (web-search log in this
session). Where I state a finding I mark it **[SETTLED]**, **[CONTESTED]**, or
**[MODELING CHOICE]** (a design decision the science neither confirms nor
refutes — legitimate, but not a "finding" to lean on). I have tried hard to
find where the model is *wrong or incomplete*, not just to confirm it. The
bottom-line verdict is in §V.

Nothing here was tuned to reach a flattering conclusion. Two of the model's
four falsifiable signatures are, on my reading, **not cleanly falsifiable as
stated** (§I.4, §II).

**The primary claim this document adjudicates (the creator's sharpened frame).**
The "two separate systems **of different kind**" phrasing was a strawman. The
real thesis is **one principle, two implementations**: a **single order-N
decode/collapse principle**, realised by **two implementations with genuinely
different response characteristics** — so "not different in *kind*" (one
principle) **and** "two systems" (two implementations) are **both true at once.**
Concretely, on the substrate's native order-N decode/collapse:

- **"System 1" = Order 0, implemented as a NET** (connectionist: fast, parallel,
  cached, associative, pattern-completing, low-capacity, always-on — a
  "self-editable instinct"). The held/cached first decode, the fast path.
- **"System 2" = Order N, implemented as SYMBOLIC decode/rewrite** (slow, serial,
  effortful, compositional, working-memory-bound). Higher-order refinement of
  the *same* decode.
- **residual/surprise** triggers climbing the order ladder (up);
  **"override"** = a higher-order term correcting the order-0 estimate;
  **"internalisation"** = the correction *compiled back into the order-0 net/
  codebook* (sd-loop growth) so order-0 later answers directly (down).

This is the substrate's "collapse is neurosymbolic — ONE loop": order-0 =
connectionist pole, order-N = symbolic pole, one collapse loop, distinct
response profiles per pole. **The closest formal statement in the literature is
model-free vs model-based reinforcement learning** (§V.2.2). §V is written around
this reconciled claim and is the load-bearing part of the document; §§I–VII
assess the component mechanisms and feed the §V verdict.

---

## 0. The model under test (restated, each claim tagged)

Two **separate** systems with **bidirectional feedback + control** (explicitly
*not* a continuum, *not* isolated modules):

- **M1 — S1 is a fast cached connectionist "instinct/net" layer** that handles
  most conduct with no deliberation.
- **M2 — S2 is a slow symbolic value-ranking (Argmax) that satisfices** — it
  scores a few weighted contenders and takes good-enough, not every option.
- **M3 — S1→S2 hand-off is triggered by S1's own conflict/surprise
  (prediction-error) signal** (the "wait"), i.e. deliberation is *recruited*,
  not always-on.
- **M4 — S2→S1 acute = override/veto** (the "no!").
- **M5 — S2→S1 chronic = S2 edits/retrains S1** → automatization →
  internalization (norms compiled into instinct; a "civilizing process" at the
  individual level).
- **M6 — weighting prunes:** norms/consequences/an admissibility grammar set
  option weights; low-weight options are unscored ("don't evaluate what can't
  win").
- **M7 — violence sits on both paths:** impulsive/reactive (S1 fires it
  directly, unconsidered — the common case) vs planned/proactive (S2 selects
  it, considered but rare/low-weight); *considering* and *doing* violence are
  decoupled.
- **Signatures claimed:** (a) "yes… wait… no!"; (b) an automation curve
  (override strengthens / S2-firing decays as restraint internalizes);
  (c) impulsive-vs-planned readable in the trace (did S2 fire?); (d) S2-
  override-rate is a per-agent trait.

The short version of the verdict, up front: **M3, M4, M5, M6, M7 are each
strongly supported by a *different* mature literature. The "two separate systems
*of different kind*" reading is the part the field has spent fifteen years
dismantling — and the creator's reframe (*one order-N principle, two
implementations with different response characteristics*) lands the substrate on
the *winning* side of that argument.** The build should be **one order-N
collapse principle realised by two coupled implementations** — a connectionist
order-0 net and a symbolic order-N rewriter — arbitrated up by residual/
uncertainty and trained down by override-plus-replay. That is **model-free /
model-based reinforcement learning** (§V.2.2). "S1/S2" name the two
implementations; "different in kind" is the strawman. §V defends this in full.

---

## I. Dual-process theory — current status (2020s)

### I.1 The canonical statement — [SETTLED that it exists; CONTESTED as ontology]

Kahneman's *Thinking, Fast and Slow* (2011) popularised System 1 (fast,
automatic, intuitive) vs System 2 (slow, deliberate, effortful). The
**scientifically serious** form is Evans & Stanovich (2013), *"Dual-Process
Theories of Higher Cognition: Advancing the Debate"* (Perspectives on
Psychological Science 8:223–241). Crucially, they **retreated from the
"two systems" language** to **"Type 1 / Type 2 processing,"** and pared the
*defining* features down to just two:

- **Type 2 loads working memory and enables mental simulation / hypothetical
  decoupling; Type 1 does not and is autonomous.** Speed, consciousness,
  evolutionary age, etc. are *correlates*, not defining features.

Their preferred architecture is **default-interventionist**: autonomous Type 1
yields a default response that Type 2 *may* intervene on. **This is essentially
the model under test's M3+M4.** So the model is aligned with the *strongest
surviving* form of dual-process theory, not the pop-science form.

### I.2 The serious critiques — [CONTESTED, and the model must absorb this]

Three critiques matter and the model does not get to ignore them:

- **Keren & Schul (2009), *"Two Is Not Always Better Than One"*** (Perspectives
  on Psych Sci 4:533–550): the two-system distinction is under-specified and
  the empirical criteria don't cleanly separate the systems.
- **Melnikoff & Bargh (2018), *"The Mythical Number Two"*** (Trends in
  Cognitive Sciences 22:280–293): the "type" features (automatic/controlled,
  conscious/unconscious, efficient/inefficient, intentional/unintentional) are
  assumed to **co-occur in two bundles, and this bundling has essentially never
  been tested** — and where tested it fails (e.g. processing can be unconscious
  *and* intentional). They argue the typology "thwarts scientific progress."
- **Kruglanski & Gigerenzer (2011)** and the **unimodel** (Kruglanski's 2013
  commentary *"Only One?"*): intuitive and deliberate judgments run on **common
  inferential principles**; the apparent "two" is one rule-based system
  operating under different resource constraints.

The field's own reconciler, **De Neys (2021), *"On Dual- and Single-Process
Models of Thinking"*** (Perspectives on Psych Sci 16:1412–1427), argues the
**strict serial two-stage story is dead** and that the interesting action is in
how intuitions themselves already carry logical/normative content.

**Honest reading for the build:** "**Two separate systems**" as an *ontological
claim* is **not** the 2020s consensus — the consensus, to the extent there is
one, is that the *labels* are heuristic and the *featural bundling* is false.
**But** the specific thing the model actually needs — **a fast autonomous
default process and a slower working-memory-loading process that can intervene
on it** — is exactly what Evans & Stanovich defend as the *surviving* core, and
what Melnikoff/Bargh's critique does **not** touch (their target is the feature-
bundling, not the existence of processes at two timescales). So the model is
defensible **if it is stated as a two-*timescale, two-representation* control
loop, not as "two systems each defined by a bundle of correlated properties."**
See §V for the precise reframing.

### I.3 Parallel-competitive vs default-interventionist — [MODELING CHOICE, lean parallel]

Two architectures compete: **serial default-interventionist** (S1 first, S2
maybe intervenes — Evans/Stanovich, Kahneman) vs **parallel-competitive** (both
run concurrently and compete — Sloman 1996; Epstein). The model's "S1 emits
candidates AND a conflict signal, THEN S2 escalates" reads as **serial**. The
evidence in §II (De Neys) favours **at least partially parallel**: the conflict
signal that triggers S2 is itself computed by an intuition that already
"knows" the logical answer. **Recommendation:** the model should treat the
hand-off as *parallel-with-precision-gated-commitment*, not a clean serial
baton-pass. This is not fatal — it is the difference between "S1 finishes then
calls S2" and "S1 and a logical intuition both fire, their disagreement is the
trigger." The latter is more defensible and, conveniently, is what a
prediction-error substrate already does (§IV).

### I.4 Signature (c) "did S2 fire?" readable in trace — [PARTLY CONTESTED]

The claim that *impulsive vs planned is cleanly readable by "did S2 fire"*
assumes a **binary S2-on/off** the literature increasingly denies (I.2, II).
De Neys' work shows S2-ish conflict detection can occur **without** a full
deliberate override — people *detect* conflict, feel less confident, and still
give the intuitive answer. So a trace may show **"S2 partially engaged and lost"**
— which is neither clean-impulsive nor clean-planned. The signature survives as
a **graded** readout (how much deliberate machinery engaged), not a **boolean**.
Flag this in the build: log a *scalar* S2-engagement, not a bit.

---

## II. What triggers deliberation (S1→S2) — [SETTLED, and the model's strongest claim]

This is where the model is **most strongly supported**, and it is worth saying
so plainly.

- **Botvinick, Braver, Barch, Carter & Cohen (2001), *"Conflict Monitoring and
  Cognitive Control"*** (Psychological Review 108:624–652) + the update
  **Botvinick, Cohen & Carter (2004)** (TiCS 8:539–546): the **dorsal anterior
  cingulate cortex monitors response conflict and recruits control** (dlPFC).
  This is a **mechanistic, neurally-grounded instantiation of exactly M3**:
  conflict → escalate control. Largely corroborated over two decades. **[SETTLED]**
- **De Neys (2012; 2014; and the "logical intuitions" program)**: reasoners are
  **not blind to conflict** — they show ACC activation, lowered confidence, and
  longer latencies on conflict problems *even when they give the biased answer*.
  Conflict/prediction-error is a **real, measured** escalation signal. **[SETTLED
  that conflict is detected; CONTESTED how automatically it converts to override]**
- **Thompson's Feeling-of-Rightness + meta-reasoning (Thompson, Prowse Turner &
  Pennycook 2011; Ackerman & Thompson 2017, *"Meta-Reasoning,"* TiCS 21:607–617):**
  a **metacognitive signal** (low FOR, low answer-fluency) is what actually
  *triggers* rethinking. This is the model's "surprise" made precise: **it is
  not raw prediction-error but a metacognitive assessment of it** that gates S2.

**Verdict on M3:** *"deliberation is triggered by S1's own conflict/prediction-
error, not always-on"* is **the single best-supported claim in the model.**
One refinement the science demands: the trigger is a **metacognitive** function
of conflict (FOR / precision), not conflict magnitude raw. The substrate's
`surprise` currency is the right primitive; it should be **precision-weighted /
compared to an expected-conflict baseline** before it escalates, or the agent
will over-deliberate in chronically noisy contexts (exactly the identifiability
concern §IV raises).

---

## III. Override / inhibition (S2→S1 acute) — [SETTLED mechanism; CONTESTED "veto"]

- **Aron and colleagues (Aron, Robbins & Poldrack 2004/2014, TiCS): the right
  inferior frontal cortex + pre-SMA + subthalamic nucleus implement response
  inhibition** (the stop-signal / "braking" network). A rapid **stop** exists,
  is localisable, and is measurable (stop-signal reaction time). **[SETTLED]**
  This is a real M4.
- **The strong "veto" framing is contested.** Libet's **"free won't"** (a
  conscious veto in a ~150 ms window) is **[CONTESTED]** — the readiness-
  potential interpretation has been undercut (Schurger et al. 2012: the RP may
  be stochastic accumulation, not a decision), and "conscious veto" is not
  established. **The build should implement override as "an inhibitory process
  that can interrupt a prepared response," which is settled, and NOT as "a
  conscious top-down veto," which is not.** The distinction matters: the former
  is a race between go and stop (fits drift-diffusion, §V.1); the latter smuggles
  a homunculus.

**Verdict on M4:** sound as a *mechanism* (a stop process that can abort a
prepared S1 action). Drop any "conscious veto" connotation. Model it as a
**second accumulator racing the first** (Boucher et al. 2007 interactive-race
model) rather than a supervisor issuing a "no!". The "no!" is the *outcome* of a
race, not a command.

---

## IV. Automatization / internalization (S2→S1 chronic) — [SETTLED, and under-exploited by the model]

This is the model's most *original and defensible* move, and the literature is
richer here than the model currently uses.

- **Shiffrin & Schneider (1977):** the foundational **controlled → automatic**
  transition with practice under consistent mapping. **[SETTLED]**
- **Anderson (1982), *"Acquisition of Cognitive Skill"*** (Psych Review
  89:369–406) → **ACT-R production compilation / proceduralization**: knowledge
  starts declarative (interpreted slowly by general procedures = S2-like) and
  **compiles into dedicated production rules** that fire fast and directly =
  S1-like. **This is *precisely* M5 — "S2 compiles into S1" — and it is a
  fifty-year-old, computationally explicit, empirically validated account.**
  **[SETTLED]** The substrate's "nets = self-editable instincts / cache layer"
  framing is essentially production compilation; the model is on very firm
  ground and should cite ACT-R as its mechanistic parent.
- **Logan (1988), instance theory of automatization:** automaticity = a shift
  from *algorithmic computation* to *memory retrieval of past instances*. A
  second, complementary mechanism for the same transition. **[SETTLED]** Note:
  Logan's account is **not** "S2 rewrites S1's weights" — it is "accumulate
  instances until retrieval outruns computation." The model's "S2 retrains S1"
  is **one** valid mechanism (proceduralization); **instance-accumulation is
  another** and does not require S2 to author anything. The build should not
  assume all automatization is S2-authored — much of it is just S1 caching its
  own outcomes.
- **Wood & Neal (2007), *"A New Look at Habits and the Habit–Goal Interface"***
  (Psych Review 114:843–863): habits are **context-cued, goal-independent**
  dispositions. Key nuance for M5: once compiled, the habit **runs from the cue,
  not from the goal that trained it** — so internalised norms can fire even when
  the deliberate goal is absent or reversed (the dark side: bad habits,
  compulsions). The model's "internalisation" should inherit this: a compiled
  norm is **cue-triggered and can misfire out of context** — that is a feature
  to exploit (it makes "the civilising process" and its pathologies the same
  mechanism), not a bug to hide.
- **Norm internalisation proper — Bicchieri (2006, *The Grammar of Society*)
  and Gintis (2003, gene-culture internalisation):** norms become internal
  *preferences* (you don't cheat even when unobserved). This is the **social**
  target M5 names ("civilizing process at the individual level" — the phrase
  echoes Norbert Elias, worth citing as the sociological source). Bicchieri adds
  a discipline the model should adopt: internalised norms are **conditional**
  (on empirical + normative expectations), so the compiled S1 response should
  carry its **triggering conditions**, not be an unconditional reflex.

**Verdict on M5:** **strongly supported and arguably the model's best idea**,
with two corrections: (1) automatization has (at least) two mechanisms —
S2-authored **proceduralization** *and* self-caching **instance-accumulation**;
don't collapse them into "S2 retrains S1." (2) Compiled habits are
**cue-bound and context-conditional** (Wood/Neal, Bicchieri) — carry the
conditions into the cache, or you get a rigid reflex, not an internalised norm.

---

## V-pre. Satisficing + option pruning (M2, M6) — [MIXED: satisficing SETTLED, "unscored" CONTESTED]

- **Simon (1955/1956), satisficing / bounded rationality:** agents evaluate
  options against an aspiration level and take the first "good enough."
  **[SETTLED]** as a description of much real choice. M2 is well-founded.
- **BUT the decision *neuroscience* says something subtly different from "don't
  score what can't win."** The dominant mechanistic model is **evidence
  accumulation / the drift-diffusion model (Ratcliff 1978; Ratcliff & McKoon
  2008)** and, for value, the **attentional drift-diffusion model (Krajbich,
  Armel & Rangel 2010).** In these models the decision **accumulates noisy
  evidence over a set of contenders until a threshold is hit** — it does *not*
  exhaustively "score all options," which supports M2 — **but low-value options
  are not "unscored"; they are *weakly sampled and lose the race early.*** The
  difference is real: "pruned before evaluation" vs "evaluated briefly and
  dominated." **[CONTESTED which one]**
- The thing that genuinely *pre-prunes* is the **consideration set** (Roberts &
  Lattin 1991; Hauser & Wernerfelt 1990; Shocker et al. 1991): people form a
  small set of candidates **before** deliberate comparison, and options outside
  it are **never** evaluated. **This is the correct literature for M6** — and it
  is exactly "don't evaluate what can't win," but the mechanism is **a fast
  recall/availability filter (S1) that builds the consideration set**, not S2
  refusing to score. **[SETTLED that consideration sets exist and pre-filter]**

**Verdict on M2/M6:** satisficing is sound; "low-weight options unscored" is
sound **if** you locate the pruning in **consideration-set formation (an S1
availability/weight filter that emits the contenders)**, not in S2 declining to
evaluate. This actually *fits the model's own M1* ("S1 emits candidates"): the
weights prune by controlling **what S1 proposes**, and S2 satisfices over the
proposed set. State it that way and both M2 and M6 are defensible. The "admissibility
grammar sets weights → low-weight options never enter the contender set" is a
**clean, literature-consistent** formulation. Do **not** claim S2 "sees and
refuses" low-weight options — S2 mostly **never sees them** (they were filtered
upstream), which is the stronger and better-supported claim anyway.

---

## VI. Reactive vs proactive aggression (M7) — [SETTLED, and the model gets this right]

The model's "violence on both paths" maps **cleanly** onto the best-validated
distinction in aggression science.

- **Dodge (and Crick & Dodge 1994, social-information-processing):** the
  **reactive/proactive** distinction. Reactive = hostile, impulsive, affect-
  driven response to perceived provocation/threat. Proactive = instrumental,
  planned, goal-directed, low-affect. **[SETTLED]** distinction; **Raine et al.
  (2006)** operationalised it (Reactive–Proactive Aggression Questionnaire, RPQ),
  validated in youth and adults.
- **Neurobiology confirms the two-path structure the model asserts:**
  - **Reactive aggression = failure of prefrontal (vmPFC) regulation over
    bottom-up amygdala/limbic threat signals** (Blair's model; Coccaro; and the
    systematic reviews returned in search: anger provocation *increases* limbic
    and *decreases* medial-PFC–amygdala connectivity in reactive violent
    offenders). Serotonergic modulation of impulsive aggression is well
    established. **This is M7's impulsive path = S1 fires, weak S2 override —
    exactly.** **[SETTLED in broad strokes]**
  - **Proactive aggression = goal-directed, low-arousal, associated with
    callous-unemotional/psychopathic traits and impaired prediction-error /
    stimulus-reinforcement signalling.** **This is M7's planned path = S2
    deliberately selects a low-weight option.** **[SETTLED distinction; specific
    circuitry still active research]**
- **"Most violence is reactive/impulsive, premeditated is rarer" — [MOSTLY
  SETTLED, with a caveat].** The reactive/impulsive subtype is the more common
  clinical and forensic presentation, and the affective-vs-predatory split is
  old and robust. The caveat: **the two are not cleanly separable in real
  people** — many violent acts are *mixed* (reactive core, some instrumental
  framing), and the RPQ factors correlate. So M7's crisp binary is a **modeling
  idealisation**; reality is a **2-D space (reactive load × proactive load)**,
  not two boxes. **[CONTESTED that any act is purely one]**

**Verdict on M7:** **the strongest domain-grounding in the model.** The claim
that considering and doing violence are decoupled, that impulsive violence is
done *without* deliberation and is the common case, and that a violence-prone
agent is "S1 trained toward violence and/or weak S2 override" is **a faithful
restatement of the reactive/proactive neuroscience.** One correction: represent
aggression as a **2-D reactive×proactive load**, allowing mixed acts, rather
than a hard S1/S2 dichotomy — the falsifiable trace signature (b) should then
predict a *distribution*, not two clusters.

---

## VII. Trait variation & development (signature d) — [SETTLED, strong support]

- **Gottfredson & Hirschi (1990), *A General Theory of Crime*:** **low
  self-control** — impulsivity, preference for the immediate, low deliberation —
  is a **stable individual trait** set early and predicting crime across
  domains. **This is literally "S2-override-rate as a per-agent trait" (signature
  d).** **[SETTLED that self-control is a stable, predictive individual
  difference; CONTESTED that it explains *all* crime / is fully stable by age
  10 — the strong version is criticised]**. So signature (d) is well-founded;
  don't adopt Gottfredson–Hirschi's *strong* stability/generality claim.
- **Steinberg (2008), dual-systems model of adolescent risk-taking**
  (+ Shulman et al. 2016 reaffirmation): risk-taking peaks in adolescence
  because a **fast socioemotional/incentive system (ventral striatum, vmPFC)
  matures earlier** than the **slow cognitive-control system (lateral PFC)** —
  a **developmental *imbalance* between exactly two timescale-separated
  systems.** **This is the model's architecture, developmentally instantiated,
  and it is a mainstream, heavily-cited theory.** **[SETTLED as a model;
  CONTESTED in details — Pfeifer & Allen and others argue the two-system
  imbalance is too coarse, and the statistical tests are weak — see "Mind the
  Gap," Casey et al.]** Net: Steinberg is **strong external validation that a
  two-timescale control-imbalance model is a productive, publishable framing** —
  and simultaneously a warning that reviewers will push on whether "two systems"
  is doing real work vs a single maturing control gain.
- **Rothbart's effortful control** (temperament): a measurable early-emerging
  disposition to inhibit a dominant response and enact a subdominant one —
  **the developmental substrate of signature (d)**, and it **strengthens with
  maturation**, matching the model's "override strengthens as restraint
  internalises" (signature b). **[SETTLED]**

**Verdict on signatures (b) and (d):** both are well-grounded. Override-as-trait
= self-control/effortful-control (settled). Override-strengthening-with-
internalisation = the developmental maturation of control + proceduralisation
(settled). The **automation curve (b)** is the one genuinely novel *quantitative*
prediction the model makes — and it is testable against the developmental slopes
Steinberg/Shulman actually measured. That is a real opportunity: **fit the
model's internalisation curve to published adolescent control-maturation
trajectories** as a convergent-validity check (in the spirit of the Bigville
"reproduce quantitative laws" north-star).

---

## V. VERDICT — have we gone far enough / on track / what's missing?

### V.1 What the model is missing or over-simplifies

Seven gaps, in rough priority:

1. **Emotion is in BOTH systems, and S2 is itself motivated/biased — not a
   neutral optimiser.** The model puts affect in S1 and a clean Argmax in S2.
   The science refuses this:
   - **Damasio's somatic-marker hypothesis** (Descartes' Error, 1994): affective
     "markers" **bias deliberate choice itself** — reasoning without affect is
     *impaired*, not purer (vmPFC patients). **[INFLUENTIAL but CONTESTED — Dunn,
     Dalgleish & Lawrence (2006) is the standard critique; treat as a hypothesis,
     not a fact].** Implication: S2's value weights **are** partly affective; the
     Argmax is affectively initialised, not affect-free.
   - **Kunda (1990), *"The Case for Motivated Reasoning"*** (Psych Bulletin
     108:480–498): deliberation is **directional** — S2 constructs justifications
     for a preferred conclusion. **[SETTLED]** So S2-override is not always
     "the rational correction of an S1 impulse"; sometimes S2 **rationalises**
     the S1 impulse. The model's clean "S2 = the civilised corrector" is
     **naive**; S2 can launder S1. This is important for a *social* sim: elites
     rationalising self-interest is S2-motivated-reasoning, not S2-override.
   **Minimal fix:** give S2's value function an affective prior (somatic marker)
   and a *directional* bias term (motivated reasoning), so S2 can either correct
   *or* rationalise S1. Without this the sim's deliberators will be implausibly
   virtuous.

2. **The hand-off is messier than clean serial escalation (see I.3, II).**
   Parallel-competitive with metacognitive gating, not S1-then-S2 baton-pass.

3. **Goals/motivation as a third driver, not derivable from S1 vs S2.** Both
   the aggression and adolescent literatures separate an **incentive/approach**
   system from the S1/S2 *control* axis (Steinberg's socioemotional system is
   not "S1 the cache" — it is a *reward* system). The model folds motivation into
   S1; a social sim needs an explicit **incentive/valuation** driver orthogonal
   to the fast/slow control axis. (This also matches the substrate's existing
   emotion/regulator/supergraph layer — wire the control loop *to* it, don't
   re-derive it.)

4. **"Effortful/costly S2" rests partly on ego depletion, which is [CONTESTED].**
   If the model assumes deliberation draws on a *depletable resource* (a natural
   reading of "S2 is expensive, so we cache"), note: **Hagger et al. (2016)
   multi-lab RRR found ~zero ego-depletion effect**; the limited-resource model
   of willpower is now a textbook cautionary tale (Inzlicht). **Do not build a
   depleting willpower meter.** The defensible cost of S2 is **opportunity/time
   cost + working-memory capacity limits** (real), not a draining fuel tank.
   The substrate already prices *time-cost* natively — use that, not depletion.

5. **Individual cognitive style beyond override-rate.** **Need for Cognition**
   (Cacioppo & Petty 1982) is a validated trait for *how readily one engages
   S2 at all* — distinct from *how well one inhibits* (self-control). Two knobs,
   not one: **propensity to deliberate** vs **capacity to override**. Signature
   (d) currently conflates them.

6. **Signature (c) should be a scalar, not a bit (I.4);** signature (a)'s
   "yes…wait…no!" is a *serial caricature* of what is often a *parallel race*
   (III) — keep it as a readout, don't hard-code the three-step sequence as the
   mechanism.

7. **Purely-reactive vs purely-proactive is an idealisation (VI);** model
   aggression as 2-D load.

### V.2 THE PRIMARY CLAIM — one order-graded mechanism, S1/S2 are its Order-0 / Order-N regimes

The creator's sharpened thesis: **S1 and S2 are not different in kind; they are
the same decode at different orders. "System 2 is really System N; System 1 is
Order 0, the fast path."** Deliberation = higher-order refinement of the *same*
decode; the trigger is the order-0 residual; the outcome compiles back into the
order-0 codebook. Does modern cognitive science support **a single graded
(depth/precision/evidence) mechanism over two systems of different kind?**

**The honest answer: the graded-single-mechanism view is the *stronger* and
*ascendant* position, the two-different-kinds view is a specific rearguard claim
that survives on exactly one property (autonomy), and the substrate is already
built as the graded mechanism.** Detail:

**Support for a single graded mechanism (converging from four independent
literatures):**

1. **The unimodel — degree, not kind [directly on point].** Kruglanski &
   Gigerenzer (2011); Kruglanski (2013). The unimodel's *entire thesis* is that
   processes "previously assumed to qualitatively differ" are **one parametric
   process** whose behaviour is set by continuous parameters (task difficulty,
   motivation, cognitive capacity) — *"the more difficult the task, the more
   processing motivation/capacity required."* **This is the creator's claim in
   the persuasion/judgment literature almost verbatim: same machine, more
   iterations/depth.** [The unimodel is itself CONTESTED — dual-process
   defenders reply that qualitative-difference evidence remains — but it is a
   serious, published single-process account, not a fringe view.]
2. **Graded quality of representation — Cleeremans' radical plasticity thesis
   (2008, 2011).** Consciousness and *availability to cognitive control* are a
   **graded continuum over "quality of representation"** (stability, strength),
   accompanied by learned **metarepresentations**. Map: **order-N = a
   metarepresentation over the order-0 decode; "quality/depth of representation"
   IS the grading variable; and control-availability rising with quality =
   escalation rising with residual-driven refinement.** This is arguably the
   *best* neuroscience-of-consciousness analogue to "S2 = higher order of the
   same decode," and it makes the creator's "compiles back into the fast path"
   claim native (learning installs the metarepresentation). [Cleeremans is a
   respected but not consensus theory of consciousness — flag as INFLUENTIAL,
   contested at the hard-problem level, but the *graded-representation*
   empirics are mainstream.]
3. **Evidence accumulation as graded depth — Ratcliff diffusion (1978; Ratcliff
   & McKoon 2008); attentional DDM (Krajbich & Rangel 2010).** A decision is
   **one** accumulator integrating evidence to a threshold; "fast intuition" vs
   "slow deliberation" is **the same process run for fewer vs more integration
   steps** (lower vs higher boundary / more evidence). **This is the single
   best-quantified instance of "slower = more iterations of the same machine,
   not a different machine" — exactly the creator's Order-0→Order-N picture.**
   [SETTLED as the dominant model of simple decisions; its *generalisation* to
   all of "deliberation" is a MODELING extrapolation.]
4. **Predictive processing / active inference (Clark 2013, *"Whatever next?"*
   BBS 36:181–204; Friston free-energy).** One hierarchical generative model
   minimising precision-weighted prediction error; **precision allocation to
   high-level inference IS "effort/deliberation."** Bellini-Leite (2022,
   Frontiers 13:805386) explicitly maps Type 1→embodied PP, Type 2→symbolic,
   and names the open **"unity problem."** [Active, CONTESTED — dual-process
   defenders don't concede dissolution; FEP itself is charged with
   unfalsifiability. But it is the field's leading *unifying* candidate.]
5. **The dual-process critics themselves point at the continuum.** Melnikoff &
   Bargh (2018) and De Neys (2021) argue the *typology* fails precisely because
   the "two" don't cleave cleanly — the data look like **one graded space**, not
   two boxes. So the strongest *critiques* of two-systems are **support** for
   single-graded.

**The honest counter-case — where "different in kind" genuinely survives:**

- **Evans & Stanovich (2013) pared the defining features to two, and one of
  them is graded but the other is categorical.** Feature 1, **working-memory
  loading / hypothetical decoupling**, is a *graded* quantity (more decoupling =
  more Type-2-ish) — this **supports** the graded view and is, notably, close to
  "compute more orders." **But Feature 2, the *autonomy* of Type 1 — that fast
  processes fire whether or not you want them to, and run to completion without
  monitoring — is a *categorical* property, not obviously a point on a
  continuum.** This is the **one place the "different in kind" claim has real
  teeth [CONTESTED, but the strongest surviving pro-duality argument]:** you can
  make order-0 *deeper*, but autonomy says order-0 **fires unbidden** and can
  produce a committed response *before* any higher order is computed. A pure
  depth-continuum has to explain **automaticity/obligatoriness** (Stroop-type
  capture, habit intrusion) as an emergent property of high-prior-precision
  order-0, not wave it away.
- **The model-free / model-based RL distinction (Daw et al. 2011; Daw, Niv &
  Dayan 2005) is a genuine two-*algorithm* claim, not a depth continuum** — and
  under the *pure* single-graded reading that was a challenge. **Under the
  reconciled "one principle, two implementations" reading it is not a challenge
  at all — it is the exact formal statement of the claim** (§V.2.2): one value/
  reward *principle*, two *implementations* (cached model-free ≈ the net/order-0;
  model-based planning ≈ symbolic/order-N) with distinct response characteristics
  that *arbitrate*. The substrate's own "nets = model-free cache; symbolic
  rewrite = model-based" language is not a concession to defend against — it **is**
  the model. [The reality of a *clean* MF/MB split is itself CONTESTED — Collins
  & Cockburn 2020; Kool et al. — see §V.2.2.]

**Verdict on the primary claim (single graded principle):** **scientifically
defensible and on the ascendant side of the debate** — supported by the
unimodel, graded-representation, evidence-accumulation, and PP literatures, and
reinforced (not threatened) by the dual-process *critics*. It is a materially
stronger position than "two systems of different kind," the version the field
spent fifteen years dismantling.

### V.2.1 Does the RECONCILED claim survive "the mythical number two" better than either pole?

The creator's reconciliation — **one order-N principle, two implementations
(connectionist net at order-0, symbolic rewrite at order-N) with distinct
response characteristics** — is, on my reading, **the strongest of the three
positions, and it survives the "number two" critique specifically because that
critique targets a claim the reconciliation does not make.**

- **What Melnikoff & Bargh (2018) and Keren & Schul (2009) actually kill** is the
  **feature-bundle typology**: the assumption that a fixed bundle of properties
  (unconscious+automatic+efficient+unintentional) co-occurs and cleaves reality
  into two *kinds*. Their evidence is that the features **dissociate** (something
  can be unconscious yet intentional, etc.).
- **The reconciled claim does not assert a feature bundle or two kinds.** It
  asserts **one principle** (so: *not* different in kind — this is the exact
  thing the critics want) realised by **two implementations** whose **response
  characteristics** (speed, capacity, seriality, compositionality, autonomy)
  differ **because of the implementation, not because they are different
  species of thought.** That is a claim about *mechanism/realisation*, which
  Melnikoff & Bargh explicitly leave standing — their target is the *typology*,
  not the existence of processes with different profiles.
- **It also rescues the real Evans–Stanovich contrasts as implementation
  differences rather than kind differences.** Type-1 autonomy/low-capacity and
  Type-2 compositional/WM-boundedness are **exactly what a cached parallel net
  vs a serial symbolic rewriter would show** — so the defensible empirical core
  of dual-process theory is *preserved and explained*, while the indefensible
  "two kinds" ontology is *dropped*. This is a better outcome than either pure
  pole: the pure single-graded pole struggled to explain **autonomy** (§V.2,
  Evans–Stanovich counter-case); the pure two-systems pole dies to the number-two
  critique. **The reconciliation keeps autonomy (it's a property of the net
  implementation) and keeps one-principle (kills the kinds).** **[This is a
  defensible synthesis, not a settled consensus — no single citation endorses
  exactly this phrasing; it is the honest best-fit reading across the
  literatures. MODELING CHOICE, well-grounded.]**

**The build recommendation is therefore sharper than "one loop, labels":** build
**one order-N collapse principle with two coupled implementations** — a
connectionist order-0 net and a symbolic order-N rewriter — that **arbitrate**
(residual/uncertainty-gated, up) and **train each other** (override + compile-
down). The substrate is *already* this: `surprise = prediction-error` is native,
the held surface **is** the prediction and a new frame is the order-0 residual,
the collapse loop is *already* "symbolic rewrite + connectionist descent, one
loop" (memory: *collapse became neurosymbolic*), and the sd loop (decode →
residual → grow codebook → re-decode) **is** the escalate-and-compile cycle.

### V.2.2 The formal analog to build against — model-free / model-based RL

**The creator's "one principle, two implementations, arbitrate + retrain-down"
is, almost line for line, the model-free / model-based reinforcement-learning
framework.** This is the frame to build against, and it is a mature,
computationally explicit, neurally-grounded literature — a large upgrade over
citing "System 1/2" prose.

- **Same principle, two implementations — Daw, Niv & Dayan (2005), *"Uncertainty-
  based competition…"* (Nature Neuroscience 8:1704–1711).** One **value/reward**
  principle; **two controllers**: a **model-free** cached value estimator (cheap,
  fast, inflexible — dorsolateral striatum ≈ the net, order-0) and a **model-
  based** planner (expensive, slow, flexible — prefrontal ≈ symbolic, order-N).
  **This is exactly "one principle, two implementations with different response
  characteristics." [SETTLED as the field's organising framework.]**
- **Arbitration = the residual/uncertainty gate (claim b, made formal).** Daw
  et al. (2005): the two controllers are arbitrated **by relative uncertainty** —
  whichever is currently more reliable gets control. Kool, Cushman & Gershman
  (2017), *"Cost-Benefit Arbitration…"*: arbitration is a **cost–benefit** trade
  (deploy the expensive model-based system only when its accuracy gain beats its
  compute cost). **This is precisely "climb the order ladder when the order-0
  residual/uncertainty is high enough to be worth the cost" — and it supplies
  the *cost* term the model needs (§V.3 knob 1: precision/uncertainty gate).**
  [Arbitration *exists* is SETTLED; the *exact* arbitration rule — pure
  uncertainty vs cost-benefit vs reliability — is CONTESTED and active.]
- **Retrain-down = replay/consolidation (claim c, made formal).** Mattar & Daw
  (2018), *"Prioritized memory access explains planning and hippocampal replay"*
  (Nature Neuroscience 21:1609–1617): the model-based system, via prioritised
  **replay**, **trains the model-free cache** — offline planning writes its
  results into the fast estimator. **This is "the symbolic order-N outcome
  compiles into the net" as a formal, published mechanism, and it converges with
  ACT-R production compilation (§IV) and Cleeremans' learned metarepresentations
  from two independent directions.** [SETTLED that MB experience shapes MF
  values; the replay-as-training account is well-supported, still developing.]
- **The neuroscience of the two implementations — Balleine & Dickinson (1998);
  Dolan & Dayan (2013), *"Goals and Habits in the Brain"* (Neuron 80:312–325).**
  **Goal-directed (model-based, prefrontal/dorsomedial striatum) vs habitual
  (model-free, dorsolateral striatum)** control, dissociated behaviourally
  (outcome-devaluation) and neurally. Habit = the order-0 net after
  over-training; goal-directed = order-N. **[SETTLED as one of the more robust
  dual-control findings in behavioural neuroscience — note this is where the
  "two implementations" claim is *most* empirically secure.]**

**So: is our model = model-free/model-based RL? Essentially yes**, with the
substrate's order-N/collapse vocabulary substituted for MF/MB, and this is a
*strength* — it means the model inherits a quantitative, testable framework
(arbitration equations, devaluation signatures, replay dynamics) instead of
prose. Two honest caveats:

1. **The clean MF/MB split is itself CONTESTED.** Collins & Cockburn (2020),
   *"Beyond Dichotomies in Reinforcement Learning"* (Nature Reviews Neuroscience
   21:576–586): the dichotomy is a useful lens but **over-mapped** — real
   behaviour is a mix, working memory contaminates the estimates, and "pure MF"
   vs "pure MB" is rarely observed. Kool et al. show people arbitrate flexibly
   and often under-use model-based control. **Implication for the build:** treat
   net-vs-symbolic as **two ends of a populated continuum of implementations
   that blend**, not a hard binary — which is *exactly* the "one principle"
   half of the reconciliation, so the caveat reinforces the frame rather than
   breaking it.
2. **The arbitration mechanism is unsettled** (uncertainty vs cost-benefit vs
   reliability-based, e.g. Lee, Shimojo & O'Doherty 2014). The build should make
   the arbitration rule an **explicit, swappable component** (a measured knob),
   not a hardcoded threshold — and can then *contribute* to this open question
   rather than merely consuming it.

### V.2.3 Is "deliberation compiles into the net" (retrain-down) faithful?

**Yes — this is one of the better-supported claims in the model, converging from
three literatures.** (i) **Model-based→model-free replay** (Mattar & Daw 2018):
planning results are written into the cached estimator via prioritised replay/
consolidation. (ii) **ACT-R proceduralisation** (Anderson 1982): interpreted
declarative/symbolic knowledge compiles into fast productions. (iii) **Instance
theory** (Logan 1988) and **Cleeremans** learned metarepresentations. The honest
correction (unchanged from §IV/§V.2.4): **there are two down-routes** —
symbolic-*authored* proceduralisation/replay **and** the net **self-caching its
own outcomes** — and not all codebook growth is order-N-authored. Also note the
**dark side is the same mechanism**: over-trained compile-down produces
**habits that fire from the cue even when the goal is gone / reversed** (Wood &
Neal; outcome-devaluation insensitivity, Balleine & Dickinson) — for a social
sim this is a feature (compulsions, "civilising process" *and* its pathologies
share one mechanism), not a bug.

**Building the "two systems" as one graded-and-arbitrated pair is not a
regression — but building them as two *kind-distinct* modules would be.** The
reconciliation is the right target: one principle, two implementations, coupled
by residual-up arbitration and override-plus-replay-down.

### V.2.4 Assessing the three specific order-N claims

**(a) "Deliberation = higher-order refinement of the SAME decode."**
**WELL-SUPPORTED as the leading view; the reconciled frame sharpens it.**
Support: unimodel (same parametric process), evidence-accumulation (same
accumulator, more steps), Cleeremans (higher-order metarepresentation over the
same first-order state), PP (higher levels of one hierarchy). The
**implementation gap** — that order-0 (net/model-free) is a *different
computation* from order-N (symbolic/model-based), not a shallow slice of it — is
**not a defeater under the "one principle, two implementations" reading; it is
the point** (§V.2.2). The reconciliation that makes claim (a) exactly faithful:
**order-0 is a cache/codebook lookup of a previously-compiled higher-order
result** — "the same decode" *historically* (computed at high order once,
model-based), a cheap lookup *now* (model-free). That is precisely the sd-loop's
codebook (order-0 reads it; order-N recomputes on a miss) **and** precisely
model-based→model-free replay (Mattar & Daw 2018). So claim (a) is faithful
**as: same principle, order-0 = compiled/cached, order-N = live recompute —
not "a few live iterations of the high-order computation."** State which you
mean; the former is the defensible, RL-backed one.

**(b) "Triggered by residual / prediction-error / conflict."**
**THE BEST-SUPPORTED CLAIM in the whole model [SETTLED].** Botvinick conflict
monitoring (ACC recruits control on conflict), De Neys (conflict detected as
prediction-error-like signal), Thompson/Ackerman Feeling-of-Rightness (low
fluency/high conflict triggers rethinking), PP (large precision-weighted
prediction error recruits higher levels). One refinement (unchanged from §II):
the trigger is a **metacognitive/precision-weighted** function of the residual,
not the raw residual — compare to an expected-residual baseline or the agent
over-deliberates in chronically noisy contexts.

**(c) "The outcome compiles back into the fast path (automatisation = fast path
absorbing the correction)."** **WELL-SUPPORTED [SETTLED as a phenomenon], with
a two-mechanism correction (as in §IV).** Anderson's ACT-R production
compilation is *literally* "higher-order interpreted knowledge compiles into a
fast direct production"; Logan's instance theory is "accumulate results until
lookup beats computation"; Cleeremans is "learn the metarepresentation."
**Correction:** automatisation has (at least) two routes — **higher-order-
authored proceduralisation** *and* **self-caching instance accumulation** —
and the second does *not* require order-N to author anything (order-0 caches its
own outcomes). The sd-loop already does the caching route (grow the codebook
from the residual); don't assume all codebook growth is order-N-authored.

### V.2.5 Is "order" the right grading variable?

This is the one place the creator's frame should be **held loosely**, because
the literature offers **four candidate graded quantities and they are not
identical**:

| Grading variable | Literature | What it captures | Fit to substrate |
|---|---|---|---|
| **Representational order/depth** (the model's choice) | Cleeremans (metarepresentation); hierarchical PP | how many levels of "decode about the decode" | native (order-N terms) |
| **Precision / gain** | Clark, Friston | *confidence-weighting* of errors — a multiplier, orthogonal to depth | native (`surprise` weighting) |
| **Evidence / integration time** | Ratcliff DDM; Krajbich | how *long* one accumulates before committing | native (more re-decode iterations) |
| **Working-memory load / decoupling** | Evans & Stanovich (a *defining* feature) | how much hypothetical simulation is held | partial |

**Honest assessment:** these are **correlated but distinct** — you can have deep
order at low precision (elaborate but unconfident), or high precision at order-0
(a fast, dead-certain reflex). **"Order" alone is under-specified as the single
knob.** The most defensible position, and the one the substrate can actually
implement, is **two coupled knobs: depth (order-N) × precision (the residual/
surprise weighting that gates whether to climb).** Precision is what *decides
when to spend depth* (claim b), and depth is *what the spending buys* (claim a).
Evidence/integration-time is then an *emergent readout* (more depth = more
iterations = slower), not a third independent knob, and WM-load is the
*capacity ceiling* on how much depth you can hold (a per-agent trait — §VII).
**Recommendation: keep "order" as the depth axis but pair it explicitly with
"precision" as the escalation gate.** Reporting "S2 fired" then means "the
precision gate opened and depth > 0 was computed," which is measurable and
matches both Botvinick (precision/conflict gate) and Cleeremans (depth/quality)
without over-committing to a single variable the science says is really two.

### V.3 BOTTOM LINE

**Status: ON TRACK on the frame; SOUND-BUT-INCOMPLETE on the content. The
reconciled claim — *one order-N principle, two implementations (connectionist
net at order-0, symbolic rewrite at order-N), coupled by residual/uncertainty
arbitration up and override-plus-replay retrain down* — is the correct target,
is stronger than either pole, and equals model-free/model-based RL. It needs
three specific additions to be faithful.**

- **Is "one principle, two implementations, coupled up+down" on track?** **Yes,
  and it is the strongest of the three framings.** It keeps the one thing the
  critics demand (not different in *kind* — one principle, killing the feature-
  bundle typology of Melnikoff & Bargh / Keren & Schul) **and** keeps the one
  thing the dual-process defenders are right about (Type-1 autonomy, low
  capacity, non-compositionality — now explained as *implementation* properties
  of a cached net, not as a different species of thought). Neither pure pole
  does both. (§V.2.1)
- **Build against model-free / model-based RL — it is the formal statement of
  the model.** One value principle, two controllers (MF cache ≈ net/order-0, MB
  planner ≈ symbolic/order-N; Daw, Niv & Dayan 2005), **uncertainty/cost-benefit
  arbitration** = the residual gate (Kool et al. 2017), **MB→MF replay** =
  compile-down (Mattar & Daw 2018), **habitual vs goal-directed** neuroscience =
  the two implementations (Balleine & Dickinson; Dolan & Dayan 2013). This buys
  a quantitative, testable framework (devaluation signatures, arbitration
  equations, replay dynamics) instead of "S1/S2" prose. (§V.2.2) Honest caveats:
  the clean MF/MB split is [CONTESTED — Collins & Cockburn 2020] (so treat
  net↔symbolic as a *blended* continuum of implementations, which is the
  one-principle half anyway) and the [CONTESTED] arbitration rule should be a
  **swappable, measured knob**, not a hardcoded threshold.
- **Faithfulness of the three specific claims:** (a) deliberation = higher-order
  refinement — **faithful, sharpened**: order-0 = compiled/cached (model-free
  now), order-N = live recompute (model-based); not "a few live iterations."
  (b) triggered by residual/PE/conflict — **best-supported claim of all**
  [SETTLED: Botvinick, De Neys, Thompson, Daw arbitration]; refine to a
  metacognitive/uncertainty-weighted gate, not raw residual. (c) compile-back
  into the net — **well-supported** [SETTLED: MB→MF replay + ACT-R + Logan +
  Cleeremans]; correction: two down-routes (symbolic-authored replay AND net
  self-caching), and the same mechanism yields habit *pathologies*
  (devaluation-insensitive cue-firing).
- **Gone far enough? Not quite — three minimal faithful additions:**
  1. **Grade on two coupled knobs: depth (order-N) × precision/uncertainty (the
     arbitration gate).** "Order" alone is under-specified; uncertainty *decides
     when to spend depth* (and supplies the cost term), depth is *what it buys*;
     evidence/time is an emergent readout, WM-load the capacity ceiling.
     (§V.2.5)
  2. **Emotion and bias live at every order, not only order-0.** The order-N
     value function carries an **affective prior** (somatic marker) and a
     **directional/motivated-reasoning** term, so higher-order deliberation can
     **rationalise** the order-0 impulse as well as correct it (Kunda [SETTLED];
     Damasio [contested]). Without this the sim's deliberators are implausibly
     virtuous. (§V.1.1)
  3. **Locate pruning in order-0 candidate-emission (consideration sets), not
     order-N "refusing to score"; log order-N engagement as a *scalar* not a
     bit; drop any depletable-willpower cost (use time/WM/compute cost — ego
     depletion is [CONTESTED/failed-replication]); split "propensity to
     deliberate" (need-for-cognition) from "capacity to override"
     (self-control).** (§V-pre, §V.1.4–6)
- **The clean distinction the creator asked for:**
  - *"S1/S2 differ in degree not kind"* — **TRUE at the level of principle** (one
    order-N/value principle) and **the consensus-aligned reading**; the
    "different *kind*" typology is the strawman the field dismantled.
  - *"…but the implementation is different (order-0 is nets, different response
    characteristics)"* — **ALSO TRUE**, and it is what preserves the real
    Evans–Stanovich contrasts and matches the habit/goal-directed neuroscience.
    Both halves hold; that is the synthesis.
  - *"The residual-triggered, higher-order-refinement, compile-back control loop
    is real"* — **TRUE, well-supported, and = model-free/model-based RL.**

**One sentence for the creator:** you are on track and the picture is now precise
and scientifically strong — **build it as model-free/model-based RL**: one value/
order-N principle, two implementations (a cached connectionist order-0 net and a
symbolic order-N rewriter) with genuinely different response characteristics,
arbitrated up by uncertainty/residual and trained down by override-plus-replay —
and the only real work left is (i) making order-0 explicitly a *compiled/cached*
result (not live shallow iteration), (ii) grading on uncertainty/precision as
well as depth and making arbitration a measured swappable knob, and (iii) letting
emotion and motivated reasoning ride *up* into the higher orders so deliberators
can rationalise, not only restrain.

---

## Appendix A — claim-by-claim scorecard

| # | Claim | Best-supporting literature | Status | Correction needed |
|---|---|---|---|---|
| M1 | S1 = fast cached connectionist default | Shiffrin&Schneider; Logan; Evans/Stanovich Type 1 | SETTLED as *process*; CONTESTED as *system* | it's a regime, not a module |
| M2 | S2 = symbolic satisficing Argmax | Simon; Ratcliff DDM | SETTLED (satisficing) | decisions accumulate over a set, not "score all" — already fine |
| M3 | S1→S2 triggered by conflict/PE | Botvinick ACC; De Neys; Thompson FOR | **SETTLED (strongest claim)** | trigger is metacognitive/precision-weighted, not raw conflict |
| M4 | S2→S1 acute override/veto | Aron inhibition; Boucher race model | SETTLED (inhibition); CONTESTED (conscious "veto"/Libet) | model as go/stop race, drop homunculus |
| M5 | S2→S1 chronic = compile into habit | Anderson ACT-R; Logan; Wood&Neal; Bicchieri; Gintis | **SETTLED (best idea)** | two mechanisms (proceduralise + self-cache); habits are cue-bound & conditional |
| M6 | low-weight options pruned/unscored | consideration sets (Roberts&Lattin; Hauser) | SETTLED (as pre-filter) | pruning is in S1 contender-emission, not S2 refusal |
| M7 | violence on both paths, mostly reactive | Dodge; Raine RPQ; Blair amygdala-vmPFC | **SETTLED distinction** | 2-D reactive×proactive load, not 2 boxes |
| Sig a | "yes…wait…no!" | serial DPT caricature; but see parallel race | partial | keep as readout, mechanism is parallel |
| Sig b | automation curve | Steinberg/Shulman slopes; Rothbart; ACT-R | SETTLED direction | fit to published maturation trajectories (convergent validity) |
| Sig c | impulsive vs planned in trace | De Neys graded engagement | partial | log scalar S2-engagement, not a bit |
| Sig d | override-rate = trait | Gottfredson&Hirschi; Rothbart eff. control; need-for-cognition | SETTLED | split propensity-to-deliberate from capacity-to-override |
| Frame | "two systems of different KIND" | Evans/Stanovich (retreated); Melnikoff&Bargh; Kruglanski; De Neys 2021 | strawman — REJECT this reading | not the real claim |
| Frame′ | ONE principle, TWO implementations (net order-0 / symbolic order-N), coupled up+down | Daw Niv Dayan 2005; Dolan&Dayan 2013; Balleine&Dickinson; Mattar&Daw 2018; Cleeremans | **the correct target; = model-free/model-based RL** | grade on precision too; arbitration = measured knob; MF/MB clean split contested (Collins&Cockburn) |
| Single principle | degree not kind / graded | unimodel (Kruglanski); Cleeremans; Ratcliff DDM | SETTLED-ish, ascendant | pair depth with precision |
| Deep | PP/active-inference unification | Clark 2013; Friston; Bellini-Leite 2022 | active/CONTESTED but substrate-native | S1/S2 = order-0/order-N regime read-offs |

## Appendix B — references (all verified this pass)

- Anderson, J.R. (1982). Acquisition of cognitive skill. *Psychological Review* 89:369–406. (ACT-R proceduralisation / production compilation.)
- Aron, A.R., Robbins, T.W., Poldrack, R.A. (2004; update 2014). Inhibition and the right inferior frontal cortex. *Trends in Cognitive Sciences*.
- Bellini-Leite, S.C. (2022). Dual Process Theory: Embodied and Predictive; Symbolic and Classical. *Frontiers in Psychology* 13:805386.
- Bicchieri, C. (2006). *The Grammar of Society: The Nature and Dynamics of Social Norms.* Cambridge UP.
- Botvinick, M.M., Braver, T.S., Barch, D.M., Carter, C.S., Cohen, J.D. (2001). Conflict monitoring and cognitive control. *Psychological Review* 108:624–652. + Botvinick, Cohen, Carter (2004), *TiCS* 8:539–546.
- Boucher, L., Palmeri, T., Logan, G., Schall, J. (2007). Inhibitory control in mind and brain: an interactive race model. *Psychological Review*.
- Cacioppo, J.T., Petty, R.E. (1982). The need for cognition. *J. Personality & Social Psychology* 42:116–131.
- Balleine, B.W., Dickinson, A. (1998). Goal-directed instrumental action: contingency and incentive learning and their cortical substrates. *Neuropharmacology* 37:407–419.
- Clark, A. (2013). Whatever next? Predictive brains, situated agents, and the future of cognitive science. *Behavioral and Brain Sciences* 36:181–204.
- Cleeremans, A. (2008). Consciousness: the radical plasticity thesis. *Progress in Brain Research* 168:19–33. Cleeremans, A. (2011). The radical plasticity thesis: how the brain learns to be conscious. *Frontiers in Psychology* 2:86.
- Collins, A.G.E., Cockburn, J. (2020). Beyond dichotomies in reinforcement learning. *Nature Reviews Neuroscience* 21:576–586.
- Daw, N.D., Niv, Y., Dayan, P. (2005). Uncertainty-based competition between prefrontal and dorsolateral striatal systems for behavioral control. *Nature Neuroscience* 8:1704–1711. Daw, N.D., Gershman, S.J., Seymour, B., Dayan, P., Dolan, R.J. (2011). Model-based influences on humans' choices and striatal prediction errors. *Neuron* 69:1204–1215.
- Dolan, R.J., Dayan, P. (2013). Goals and habits in the brain. *Neuron* 80:312–325.
- Crick, N.R., Dodge, K.A. (1994). A reformulated social information-processing model. *Psychological Bulletin* 115:74–101.
- Damasio, A. (1994). *Descartes' Error* (somatic marker hypothesis). Critique: Dunn, Dalgleish & Lawrence (2006), *Neuroscience & Biobehavioral Reviews* 30:239–271.
- De Neys, W. (2012). Bias and conflict: a case for logical intuitions. *Perspectives on Psychological Science* 7:28–38. De Neys (2014), *Thinking & Reasoning* 20:169–187. De Neys (2021). On Dual- and Single-Process Models of Thinking. *Perspectives on Psych Sci* 16:1412–1427.
- Evans, J.St.B.T., Stanovich, K.E. (2013). Dual-Process Theories of Higher Cognition: Advancing the Debate. *Perspectives on Psychological Science* 8:223–241.
- Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience* 11:127–138.
- Gintis, H. (2003). The hitchhiker's guide to altruism: gene-culture coevolution and the internalization of norms. *J. Theoretical Biology* 220:407–418.
- Gottfredson, M., Hirschi, T. (1990). *A General Theory of Crime.* Stanford UP.
- Hagger, M.S., et al. (2016). A multilab preregistered replication of the ego-depletion effect. *Perspectives on Psychological Science* 11:546–573. (Null; see also Inzlicht commentary.)
- Hauser, J.R., Wernerfelt, B. (1990). An evaluation cost model of consideration sets. *J. Consumer Research* 16:393–408. Roberts, J., Lattin, J. (1991). Development and testing of a model of consideration set composition. *J. Marketing Research*.
- Kahneman, D. (2011). *Thinking, Fast and Slow.* Farrar, Straus & Giroux.
- Keren, G., Schul, Y. (2009). Two is not always better than one. *Perspectives on Psychological Science* 4:533–550.
- Krajbich, I., Armel, C., Rangel, A. (2010). Visual fixations and the computation of value in simple choice (attentional DDM). *Nature Neuroscience* 13:1292–1298.
- Kool, W., Cushman, F.A., Gershman, S.J. (2017). Cost-benefit arbitration between multiple reinforcement-learning systems. *Psychological Science* 28:1321–1333. (See also Kool, Gershman, Cushman 2016, PLoS Comp Biol, "When does model-based control pay off?")
- Kruglanski, A.W., Gigerenzer, G. (2011). Intuitive and deliberate judgments are based on common principles. *Psychological Review* 118:97–109. Kruglanski (2013), "Only One?" commentary, *Perspectives on Psych Sci* 8:242–247.
- Kunda, Z. (1990). The case for motivated reasoning. *Psychological Bulletin* 108:480–498.
- Lee, S.W., Shimojo, S., O'Doherty, J.P. (2014). Neural computations underlying arbitration between model-based and model-free learning. *Neuron* 81:687–699.
- Logan, G.D. (1988). Toward an instance theory of automatization. *Psychological Review* 95:492–527.
- Mattar, M.G., Daw, N.D. (2018). Prioritized memory access explains planning and hippocampal replay. *Nature Neuroscience* 21:1609–1617.
- Melnikoff, D.E., Bargh, J.A. (2018). The mythical number two. *Trends in Cognitive Sciences* 22:280–293.
- Raine, A., et al. (2006). The reactive–proactive aggression questionnaire (RPQ). *Aggressive Behavior* 32:159–171.
- Ratcliff, R. (1978). A theory of memory retrieval. *Psychological Review* 85:59–108. Ratcliff, R., McKoon, G. (2008). The diffusion decision model. *Neural Computation* 20:873–922.
- Rothbart, M.K., Bates, J.E. (2006). Temperament (effortful control). In *Handbook of Child Psychology.*
- Shiffrin, R.M., Schneider, W. (1977). Controlled and automatic human information processing. *Psychological Review* 84:127–190.
- Simon, H.A. (1955). A behavioral model of rational choice. *Quarterly J. Economics* 69:99–118. (Satisficing / bounded rationality.)
- Steinberg, L. (2008). A dual systems model of adolescent risk-taking. *Developmental Psychobiology / Developmental Review* 28:78–106. Shulman, E.P., et al. (2016). The dual systems model: review, reappraisal, and reaffirmation. *Developmental Cognitive Neuroscience* 17:103–117.
- Thompson, V.A., Prowse Turner, J.A., Pennycook, G. (2011). Intuition, reason, and metacognition. *Cognitive Psychology* 63:107–140. Ackerman, R., Thompson, V.A. (2017). Meta-Reasoning: monitoring and control of thinking and reasoning. *Trends in Cognitive Sciences* 21:607–617.
- Wood, W., Neal, D.T. (2007). A new look at habits and the habit–goal interface. *Psychological Review* 114:843–863.
- (Contested/flagged) Libet, B. (1985) "free won't"; reinterpreted by Schurger, Sitt & Dehaene (2012), *PNAS* 109:E2904 (readiness potential as stochastic accumulation).
- (Sociological source for "civilizing process") Elias, N. (1939/2000). *The Civilizing Process.*
