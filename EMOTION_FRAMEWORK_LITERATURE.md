# The Emotion Framework — an honest literature situating

**Purpose.** Situate the project's emotion / affective-science framework (built and
gated across blocks 196000–204000) against the established literature. The
project's standing rule is *understand and situate honestly, never overclaim
novelty* — so the goal here is to find where each piece is ALREADY established,
name the key references, and pin exactly what (if anything) is distinctive in the
specific combination. The short version, stated up front so nothing below reads as
a novelty pitch: **every one of the seven load-bearing ideas is canonical and
well-supported affective/decision science, and two of them have near-exact
architectural precedents in AI.** Emotions as evolved value-regulators, emotion as
the enabler of decision, eudaimonia ≠ hedonia, self-transcendence, multi-level
selection, learning-progress curiosity, a state/mechanism-based psychiatric
taxonomy, and nature/nurture as a heritability decomposition are all established —
several for 25–60 years. We are re-deriving known affective science on a new
substrate, not discovering it. The contribution, honestly bounded, is the
mechanistic, graph-native, knob-turnable *instantiation* plus a couple of clean
unifying framings — not new science.

Companion to `COGNITION_IS_PHYSICS_LITERATURE.md`, same standard, same posture.
Framework details: `VISION_CORE_EMOTIONS_RESULTS.md` (204000),
`VISION_DISORDER_GLASSBOX_RESULTS.md` (199000), `SUBSTRATE_DISORDER_MAP.md`.

---

## 1. The framework, stated precisely (no strawman)

As the project holds it, in seven pieces:

1. **Emotions are the net layer's DECISION FUNCTION — a value-regulator, not
   cognition.** The low-cost "emotional" decisions must be made by fast order-0
   nets, not deliberation, or the system is paralysed by indecision. Emotion is the
   **REGRESS-BREAKER**: the meta-decision "decide now or deliberate more?" cannot
   itself be deliberated (a halting/self-reference regress), so a non-deliberative
   layer must cut by fiat.
2. **Each emotion is an APPRAISAL → ACTION-TENDENCY pattern over a shared signal
   economy** (surprise, salience, precision, learning-progress, value), read off on
   valence × arousal axes.
3. **Each emotion's value function has a REFERENCE FRAME = a level of selection** —
   individual (fear/hunger/joy/curiosity), social (guilt/pride, over self+other
   models), and SUPERGRAPH (fulfilment). "Meaning" emotions are those whose value is
   defined a level *up* from the self.
4. **FULFILMENT = the supergraph-value emotion** — contribution to the
   collective/lineage's success; distinct from happiness; explains
   individually-"irrational" behaviour (having children); dissociates from happiness
   on supergraph-costly acts (the parenthood paradox).
5. **Curiosity gated by LEARNING PROGRESS (not raw surprise)** fixes the noisy-TV
   trap; the same mechanism is "leave the unresolved" and the anti-obsession decay.
6. **Disorders = mis-set emotion parameters.** Decay-side (obsession =
   self-refreshing loop / won't-demote; PTSD = won't-decay threat) and value-side
   (psychopathy = the supergraph-value knob at ~0 — intact cognitive empathy, absent
   valuation; depression = value suppressed across frames; mania = inflated).
   **CLASSIFY BY STATE (the knob), not OBSERVATION (symptom clusters)**: the
   behavioural "factors" are shadows of the state-knobs.
7. **Nature/nurture is a DISTRIBUTION over knob-plasticities** (seed vs accumulated
   edits), not a dichotomy.

The binding headline: *emotions are the value-regulating decision layer of a
bounded agent; each is a value function at a level of selection; the whole family —
plus its disorders — are settings of one shared integer signal economy.*

---

## 2. Prior-art map — where each piece is already established

For each field: key references and EXACTLY what they already establish. The
consistent finding is that the **components are canonical**; our pieces re-derive
them, and two have direct AI-architecture precedents.

### 2.1 Emotion as the enabler of decision / the regress-breaker (piece 1) — the closest prior art, and it is 1967

This is the single most important thing to get right, because piece 1 is the
project's boldest-sounding claim and it is **almost exactly Herbert Simon's 1967
thesis**, restated many times since.

- **Herbert A. Simon, "Motivational and Emotional Controls of Cognition,"
  *Psychological Review* 74(1):29–39 (1967)**
  (<https://cs.uwaterloo.ca/~jhoey/teaching/cs886-affect/papers/Simon1967.pdf>).
  Simon's argument: the CNS is a *serial* processor serving an organism with
  *multiple goals* in an unpredictable environment, and this design requires (a)
  goal-terminating mechanisms and (b) **an interrupt system with the properties
  usually ascribed to emotion**, so the processor can respond to urgent needs in
  real time. That IS piece 1 — "a non-deliberative layer must cut, or the agent is
  paralysed" — stated 59 years ago. Our "regress-breaker" is Simon's "interrupt."
- **Damasio, *Descartes' Error* (1994)** (somatic-marker hypothesis;
  <https://en.wikipedia.org/wiki/Descartes'_Error>) and Bechara, Damasio, Damasio &
  Anderson (1994, Iowa Gambling Task): VMPFC patients with flattened affect are
  *worse*, not better, at practical decisions — they perseverate, cannot choose.
  Emotion supplies a somatic value-signal that makes decision *possible*. The
  project's `total_value = happiness + fulfilment` the agent acts on is explicitly a
  somatic marker (`VISION_CORE_EMOTIONS_RESULTS.md` §4). Note the field's current
  posture: the somatic-marker hypothesis is "a decisive correction, not a final
  theory" — cite it as the establishing correction, not as settled mechanism.
- **Kahneman, *Thinking, Fast and Slow* (2011):** a fast, affect-laden System 1
  that gates a slow, effortful System 2. The "fast net decides, deliberation is the
  exception" split is dual-process orthodoxy.
- **Metareasoning / bounded rationality — the regress made formal.** Russell &
  Wefald, *Do the Right Thing: Studies in Limited Rationality* (MIT Press, 1991) and
  "Principles of Metareasoning" (*Artif. Intell.* 49, 1991)
  (<http://iiif.library.cmu.edu/file/Newell_box00014_fld01011_doc0001/Newell_box00014_fld01011_doc0001.pdf>);
  Zilberstein, "Metareasoning and Bounded Rationality" (2008). These establish
  precisely the "you cannot deliberate about whether to deliberate, all the way
  down" regress and the need to *bottom it out* — bounded optimality's whole reason
  for existing. Simon's bounded rationality (1955/1957) is the root. The project's
  "the meta-decision cannot itself be deliberated (halting regress)" is this
  literature's founding problem; emotion-as-the-fiat-cut is Simon's answer to it.

**Verdict on piece 1: fully established.** The strong, specific claim — "a bounded
serial/limited agent MUST have a non-deliberative affective interrupt that cuts the
deliberation regress, or it is paralysed" — is Simon 1967, reinforced by Damasio,
dual-process theory, and the metareasoning literature. We re-derive it; we do not
originate it.

### 2.2 Appraisal → action-tendency over valence×arousal (piece 2) — textbook affective science

- **Appraisal theory:** Magda Arnold (1960) originated appraisal; **Richard
  Lazarus, *Emotion and Adaptation* (1991)** made it the dominant framework;
  **Klaus Scherer's Component Process Model** (Scherer 2001; Scherer & Moors, "The
  Emotion Process," *Annu. Rev. Psychol.* 2019,
  <https://ppw.kuleuven.be/okp/_pdf/Scherer2019TEPEA.pdf>) decomposes emotion into
  sequential appraisal checks driving action tendencies and expression — an emotion
  IS a configuration of appraisal outputs. That is exactly "each emotion is a
  configuration of the signal economy."
- **Action tendencies:** **Nico Frijda, *The Emotions* (1986)** — every emotion is
  a readiness to act in a particular way (the "law of situational meaning" → action
  readiness). The project's Tendency column (ORIENT/AVOID/APPROACH/…) is Frijda's
  action tendencies verbatim.
- **The circumplex:** **James Russell, "A Circumplex Model of Affect,"
  *JPSP* 39(6):1161–1178 (1980)** — affect maps onto valence × arousal. The
  project's read-off of valence (sign of governing progress/value) and arousal
  (magnitude of governing surprise/precision) is Russell's circumplex.
- **Basic emotions:** **Paul Ekman** (basic-emotion theory; discrete
  cross-culturally recognised families). The 11-emotion roster (surprise, fear,
  anger, disgust, joy, sadness, …) is standard basic/appraisal taxonomy.

**Verdict on piece 2: canonical.** Appraisal → action tendency, on a valence×arousal
circumplex, is the mainstream architecture of emotion. The project's own results
doc says so plainly (`VISION_CORE_EMOTIONS_RESULTS.md` §0).

### 2.3 Adaptationist / evolutionary emotion — emotions as evolved value-regulators (pieces 1–3)

- **Tooby & Cosmides, "The Evolutionary Psychology of the Emotions and Their
  Relationship to Internal Regulatory Variables"** (in Lewis, Haviland-Jones &
  Barrett, eds., *Handbook of Emotions*, 2008; and "Evolutionary Psychology and the
  Emotions," <https://cognitionandculture.net/wp-content/uploads/10.1.1.140.7434.pdf>):
  **an emotion is a superordinate program that evolved to coordinate the many
  subprograms (attention, perception, memory, physiology, action) toward solving a
  recurrent adaptive problem.** This is piece 1+2 nearly word-for-word: emotion as a
  regulatory/coordinating program over a shared economy, keyed by "internal
  regulatory variables" (their term for the project's shared signals).
- **Randolph Nesse, *Good Reasons for Bad Feelings* (2019)** and Nesse & Ellsworth
  (2009): emotions are evolved responses that are *useful in the situations that
  selected them* (the "smoke-detector principle" for defensive emotions). Negative
  emotions are value-regulators, not defects — the exact posture behind the
  project's "understanding, not judgment" disorder framing.
- **Tinbergen's four questions (1963) / Mayr's proximate–ultimate distinction:**
  the discipline that lets one say an emotion has an *ultimate* value function
  (fitness at some level) realised by a *proximate* mechanism (the appraisal rule).
  The project's "value function = level of selection" lives on this distinction.

**Verdict on piece 3's ancestry: established.** "Emotions are evolved
value/coordination programs keyed to adaptive problems" is Tooby–Cosmides + Nesse.

### 2.4 Reference frame = level of selection; fulfilment = supergraph value (pieces 3–4)

- **Inclusive fitness / kin selection:** **W. D. Hamilton (1964),** "The genetical
  evolution of social behaviour" — value can be defined over copies of one's genes
  in *others*; altruism toward kin is individually costly, supergraph-beneficial.
  The parenthood case is Hamilton's home turf.
- **Multi-level / group selection:** **Sober & Wilson, *Unto Others: The Evolution
  and Psychology of Unselfish Behavior* (Harvard, 1998)**
  (<https://www.goodreads.com/book/show/134244>); **D. S. Wilson & E. O. Wilson,
  "Rethinking the Theoretical Foundation of Sociobiology,"** *Q. Rev. Biol.* 82(4)
  (2007); E. O. Wilson's superorganism / eusociality work. This field IS "value at a
  higher level of selection than the individual" — the project's SUPERGRAPH frame.
- **The "hive switch" and collective emotion:** **Jonathan Haidt, *The Righteous
  Mind* (2012)** — humans are "90% chimp, 10% bee," with a group-transcendent "hive
  switch"; **Émile Durkheim, *The Elementary Forms of Religious Life* (1912)** —
  *collective effervescence*, emotion generated at and for the group level. These
  are the felt-emotion correlates of a supergraph-level value function.
- **Warm-glow giving:** **James Andreoni, "Impure Altruism and Donations to Public
  Goods: A Theory of Warm-Glow Giving," *Economic Journal* 100(401):464–477 (1990)**
  (<https://academic.oup.com/ej/article-abstract/100/401/464/5190270>) — a private
  utility from *the act of contributing* itself, distinct from the individual payoff.
  That is fulfilment-as-a-distinct-signal in economics.
- **The parenthood paradox (piece 4's signature dissociation):**
  **Nelson, Kushlev & Lyubomirsky, "In Defense of Parenthood: Children Are
  Associated With More Joy Than Misery," *Psychological Science* 24(1) (2013)**
  (<https://pubmed.ncbi.nlm.nih.gov/23201970/>) and Nelson et al., "Parents Reap What
  They Sow: Child-Centrism and Parental Well-Being" (2013); the day-reconstruction
  method they use is **Kahneman, Krueger, Schkade, Schwarz & Stone, *Science* (2004).**
  The robust finding: parenthood tends to *lower* moment-to-moment hedonic affect
  while *raising* meaning/life-evaluation. That IS the project's G3 cross (happiness
  falls, fulfilment rises on a supergraph-costly act). Note honestly: the empirical
  literature is *mixed and moderated* (Nelson et al. 2014 "pains and pleasures";
  Bhargava, Kassam & Loewenstein 2013 reassessment) — the hedonic/eudaimonic
  *dissociation* is the well-supported part, not a simple "parents are unhappy."

**Verdict on pieces 3–4: canonical, from three independent fields** (evolutionary
biology, moral/social psychology, welfare economics). "A value function defined a
level up from the self, dissociable from individual hedonic value" is Hamilton +
Sober–Wilson + Andreoni + the parenthood-paradox literature.

### 2.5 Eudaimonia ≠ hedonia (piece 4, the well-being axis)

- **Aristotle, *Nicomachean Ethics*** — *eudaimonia* (flourishing / living well)
  vs mere pleasure; the 2,300-year-old root.
- **Ryan & Deci, Self-Determination Theory**; **Ryan, Huta & Deci, "Living Well: A
  Self-Determination Theory Perspective on Eudaimonia," *J. Happiness Stud.* 9 (2008)**
  (<https://link.springer.com/article/10.1007/s10902-006-9023-4>) — eudaimonic
  living as intrinsic-goal pursuit / need satisfaction, distinct from hedonic
  balance.
- **Carol Ryff, "Happiness Is Everything, or Is It?" *JPSP* 57 (1989)** — the
  six-factor model of *psychological* well-being (PWB), operationally distinct from
  *subjective* well-being (SWB); **Alan Waterman (1993)** — personal expressiveness
  (eudaimonia) vs hedonic enjoyment, empirically separable.
- **Baumeister, Vohs, Aaker & Garbinsky, "Some Key Differences Between a Happy Life
  and a Meaningful Life," *J. Positive Psychology* 8(6) (2013)** — happiness and
  meaningfulness dissociate; meaning correlates with giving/contributing even when
  it lowers happiness. A direct empirical statement of piece 4.

**Verdict: fully established, and old.** Fulfilment ≠ happiness is Aristotle,
formalised by Ryff/Ryan-Deci/Waterman and dissociated empirically by Baumeister.

### 2.6 Self-transcendence / meaning (piece 4's "meaning is a level up")

- **Viktor Frankl,** logotherapy / *Man's Search for Meaning* — "will to meaning";
  he coined **self-transcendence** as reaching beyond the self toward a cause or
  another person.
- **Abraham Maslow (1969),** "The Farther Reaches of Human Nature" — added
  *self-transcendence* above self-actualisation as the apex need.
- **Erik Erikson** — *generativity vs stagnation*: mature well-being from investing
  in the next generation (the developmental face of the parenthood/supergraph case).
- **Steger et al., "The Meaning in Life Questionnaire," *J. Counseling Psychology*
  53 (2006)** (<https://singteach.nie.edu.sg/wp-content/uploads/2021/12/Steger-et-al-2006_The-meaning-in-life-questionnaire.pdf>);
  **Baumeister, *Meanings of Life* (1991).** Meaning operationalised and measured.

**Verdict: established.** "Meaning = orientation to something larger than the self"
is Frankl/Maslow/Erikson, measured by Steger/Baumeister.

### 2.7 Learning-progress curiosity + the noisy TV (piece 5)

- **Jürgen Schmidhuber** — curiosity as *compression progress* / *learning
  progress*, from 1991 ("A Possibility for Implementing Curiosity and Boredom…") to
  "Driven by Compression Progress" (2009,
  <https://link.springer.com/chapter/10.1007/978-3-642-02565-5_4>) and the 2010
  Formal Theory of Fun & Creativity. Intrinsic reward = *improvement* in the model,
  not raw error — which is exactly why it does not chase irreducible noise.
- **Oudeyer, Kaplan & Hafner, "Intrinsic Motivation Systems for Autonomous Mental
  Development" (Intelligent Adaptive Curiosity, IAC), *IEEE Trans. Evol. Comput.*
  11(2) (2007)** — reward = *reduction in prediction error over time* (learning
  progress); explicitly avoids both the fully predictable and the fully
  unpredictable (noise). The canonical statement of piece 5.
- **The noisy-TV problem:** **Pathak et al., ICM (2017)** used prediction error and
  was shown vulnerable to stochastic traps; **Burda et al., "Large-Scale Study of
  Curiosity-Driven Learning" / RND (2018)** named and demonstrated the noisy-TV
  failure of raw-surprise curiosity. Learning-progress/IAC is the standard fix — the
  project's exact claim (surprise → curiosity's noisy-TV trap; learning-progress →
  the cut).

**Verdict: canonical in intrinsic-motivation RL.** "Gate curiosity on learning
progress, not surprise, to escape the noisy TV" is Schmidhuber + Oudeyer-Kaplan, and
the noisy-TV framing is Burda et al. We re-derive it as an integer graph rule.

### 2.8 Disorders as mis-set parameters; state- vs symptom-based taxonomy (piece 6)

- **RDoC — Insel et al., "Research Domain Criteria (RDoC): Toward a New
  Classification Framework for Research on Mental Disorders," *Am. J. Psychiatry*
  167(7):748–751 (2010)** (<https://www.researchgate.net/publication/44901922>);
  Cuthbert & Insel (2013). NIMH's program to classify psychopathology by
  **dimensional, transdiagnostic mechanisms** rather than DSM symptom categories —
  i.e., *classify by the underlying state/mechanism, not the symptom cluster.* That
  is piece 6's headline. Report it precisely: RDoC is the aspiration/framework;
  it does not (yet) hand you turnable mechanistic knobs.
- **Computational / predictive-processing psychiatry:** **Kapur, "Psychosis as a
  State of Aberrant Salience," *Am. J. Psychiatry* 160 (2003);** Friston, Corlett,
  Adams, Fletcher & Frith — symptoms as **mis-set precision** on priors vs
  prediction errors. The project's freshness=precision, and "a mis-set half-life is a
  mis-set precision," is this literature (`VISION_DISORDER_GLASSBOX_RESULTS.md` §5,
  which cites Kapur and Friston/Corlett/Adams directly). PTSD-as-extinction-failure
  is the standard fear-conditioning account (Milad & Quirk); rumination as
  perseverative self-focus is Nolen-Hoeksema.
- **Psychopathy factor structure & the value/cognition split:** **Hare PCL-R**
  (Factor 1 affective/interpersonal vs Factor 2 lifestyle/antisocial — the
  "behavioural factors" the project says are shadows of the state); **R. J. R. Blair,
  Violence Inhibition Mechanism** — an intact-cognition, deficient-affect account;
  **Paul Frick, callous-unemotional traits.** Decisively for piece 6's psychopathy
  model: **Meffert, Gazzola, den Boer, Bartels & Keysers, "Reduced Spontaneous but
  Relatively Normal Deliberate Vicarious Representations in Psychopathy," *Brain*
  136(8):2550–2562 (2013)** (<https://academic.oup.com/brain/article/136/8/2550/432196>)
  — psychopaths' vicarious/empathic activation is *reduced spontaneously but
  restored when instructed to empathise*. That is EXACTLY the project's "reads others
  via intact cognitive empathy but does not VALUE them" — the empathy machinery is
  present; the automatic valuation (the `w_supergraph` knob) is down. This is the
  single closest empirical match to any of the project's disorder knobs.

**Verdict: established, with one caveat.** The mechanism-over-symptom stance is
RDoC; disorders-as-mis-set-precision is computational psychiatry; the
intact-cognition/absent-valuation psychopathy split is Blair + Meffert et al. We
re-derive all of it. The caveat (below) is whether making the knob *actually
turnable and reversible in a running artifact* is worth anything beyond the theory —
that is the artifact question, not a taxonomy novelty.

### 2.9 Nature/nurture as a heritability decomposition (piece 7)

- **Quantitative / behavioural genetics:** heritability (h²) is a
  **population-level proportion of phenotypic variance** attributable to genetic
  variance — Fisher (1918), Falconer; **Turkheimer's "Three Laws of Behavior
  Genetics" (2000)** (everything is heritable; shared-environment effect is small;
  much is neither). Crucially: heritability is *population- and
  environment-dependent*, not an individual constant — the standard corrective the
  project's "distribution over plasticities, not a dichotomy" echoes.
- **Diathesis-stress** (genetic vulnerability × environmental stress; the
  Generation-Scotland validation and the broader model) and **gene×environment
  interaction / differential susceptibility (Belsky)** — the effect of a genotype
  depends on environment, and vice versa. **Caspi et al. (2002/2003),
  MAOA/5-HTTLPR × maltreatment,** the canonical GxE demonstrations; epigenetics as
  the molecular interface.

**Verdict: established, and the project's framing is the mainstream one.**
"Nature/nurture is a continuous variance/interaction decomposition, not a
dichotomy" is behavioural-genetics 101. The project's seed-vs-edits split is a
particular (in-silico, individual) *realisation* of this — see §3(d).

### 2.10 The closest whole-architecture prior art — emotions as modulator parameters of a cognitive agent

Two AI cognitive architectures already build "emotions as knobs/parameters that
modulate a cognitive economy," which is the project's pieces 1+2+6 as an
*engineered system*, and both predate this work by ~20 years:

- **Dietrich Dörner's PSI theory** and **Joscha Bach's MicroPsi**
  (Bach, *Principles of Synthetic Intelligence: PSI* (OUP, 2009); "The MicroPsi
  Agent Architecture,"
  <https://www.researchgate.net/publication/2861286_The_MicroPsi_Agent_Architecture>):
  emotions are **not separate modules but global configuration/modulation
  parameters** of perception, action-selection, memory and planning (arousal,
  resolution level, selection threshold, securing rate), driven by a small set of
  drives (existence, certainty, competence, affiliation). Dörner showed in
  simulation that **agents without emotional modulation systematically fail in
  complex environments** — which is the project's piece 1 ("paralysed without the
  affective cut") demonstrated in an AI architecture decades ago.
- **OCC appraisal model (Ortony, Clore & Collins, *The Cognitive Structure of
  Emotions*, 1988)** and computational-appraisal agents (**Gratch & Marsella, EMA**;
  Soar/LIDA emotion work; Picard's *Affective Computing*, 1997) — emotions
  synthesised from appraisal variables to drive behaviour in artificial agents.

**This is the honest ceiling for the architecture claim:** "emotions are functional
control parameters of a cognitive agent, and an agent lacking them is
decision-impaired" is Dörner/Bach (and, for appraisal-driven agents, OCC/EMA). The
project's version is integer, graph-native, and shares its atoms with perception and
disorders — but the *architectural idea* is not new.

---

## 3. Honest novelty assessment — what, if anything, is distinctive

Evaluated critically, discounting where not actually novel.

**(a) The reference-frame-PER-EMOTION principle (each value function = a level of
selection; "meaning" emotions are defined a level up).**
*A crisp synthesis, not a new claim.* Every conjunct exists: multi-level selection
already partitions individual vs group value (Sober–Wilson); social/moral emotions
are already theorised as group-serving (Haidt; Tooby–Cosmides on the social
emotions); Hamilton already defines value over kin. Stating it as a *clean uniform
rule* — "each emotion's value function is indexed by a reference frame = a level of
selection, and the 'meaning' emotions are exactly those whose frame is above the
self" — is a genuinely tidy unifying sentence, and I did not find it stated in
exactly that compressed form. But it is organisation of established facts, not a new
mechanism. Verdict: **useful framing, precedented in MLS + evolutionary
social-emotion theory; do not call it novel.**

**(b) The ONE-ECONOMY unification (decay / curiosity / emotion / disorder as knobs
on the SAME integer signal economy).**
*The unification itself is FEP's; the shared-integer-atoms realisation is the
distinctive engineering.* The strong form of "perception, action, emotion, and
psychiatry are all settings of one quantity" is already the Free Energy Principle /
active inference (variational free energy; precision-weighting), and
predictive-processing psychiatry already unifies disorders as mis-set precision on
that one quantity — the very literature §2.8 cites. So the *unification* is not new.
What is genuinely uncommon is the *literalness*: the emotion rules reuse the exact
196000 freshness atom, the 202000 learning-progress backward-difference, and the
202000 value atom — the same integer nodes, no new module, no new Rust Term
(`VISION_CORE_EMOTIONS_RESULTS.md` §7). "The same atoms, byte-for-byte, serve
perception AND emotion AND the disorder knob" is a real engineering distinctive.
Verdict: **the unifying thesis is FEP's; the shared-atom integer instantiation is a
distinctive build, not a distinctive theory.**

**(c) The STATE-based disorder taxonomy operationalised as turnable, reversible
knobs (vs RDoC as an aspiration).**
*Taxonomy = RDoC + computational psychiatry; the reversible glass-box knob is an
artifact contribution.* "Classify by mechanism/state, not symptom" is RDoC
verbatim; "disorder = mis-set precision parameter" is Friston/Corlett/Kapur. Neither
is novel here. The one thing the project adds that the literature does *not* hand you
is a **glass-box**: a single named graph-resident knob you turn to make the symptom
emerge and turn back to make it resolve, byte-identically
(`VISION_DISORDER_GLASSBOX_RESULTS.md` §4 pure-knob reversibility). RDoC is a
research *framework*; computational-psychiatry models *fit* parameters to data. A
*mechanistically reversible, byte-identity-gated demonstration* of "turn the knob →
symptom → turn it back → health" is a demonstration the theory papers do not stage.
But — exactly as with the cognition-is-physics artifact — this is a contribution of
*demonstration*, not of *taxonomy or mechanism*, and the knobs are **authored,
model-internal, and clinically unvalidated** (the project says so itself:
`SUBSTRATE_DISORDER_MAP.md` "T1 asterisk," `VISION_DISORDER_GLASSBOX_RESULTS.md` §5
honest scope). Verdict: **not a taxonomy novelty; a modestly distinctive artifact,
clinically unvalidated.**

**(d) Nature/nurture as a directly-MEASURABLE seed-vs-edits decomposition.**
*Cute and exact in-silico, but not the same construct as heritability, and modest.*
Behavioural genetics already decomposes phenotypic *variance* into genetic and
environmental components. The project's twist is that, being a synthetic agent whose
seed you authored, you can read the seed parameters vs the accumulated edits
*for the individual, exactly* — where heritability is only ever a *population*
proportion and cannot be assigned to an individual. That individual-level,
exact decomposition is conceptually clean and impossible in real behavioural
genetics. But it is "distinctive" only because it is a built artifact where you own
the ground truth — it does not measure the same thing h² measures, and it makes no
empirical claim about humans. Verdict: **a neat property of the artifact, not a
contribution to genetics; do not overstate it.**

**(e) The graph-native, gated, knob-reversible ARTIFACT (a working demo vs a
theory).**
*The most defensible distinctive contribution — and, as in the physics doc, it is an
artifact, not a theory.* What the project has that Simon, Damasio, Tooby–Cosmides,
Nesse, Schmidhuber, RDoC, and even Dörner/Bach do not is a **single running
substrate** in which (i) the 11-emotion appraisal→tendency set,
(ii) learning-progress curiosity, (iii) the decay-side and value-side disorder
knobs, and (iv) the supergraph/fulfilment frame are the *same integer economy*,
default-OFF, byte-identity-gated, with minimal-pair discriminators (flip one
attribute → the emotion crosses the recognised boundary) and pure-knob reversibility
(`VISION_CORE_EMOTIONS_RESULTS.md` §2, §5; glass-box §4). MicroPsi is the closest
prior artifact and is genuinely comparable — but it is float-valued, module-flavoured,
and does not share atoms with a perception stack or gate on byte-identity. The
distinctive is **conviction and reuse**: one checkable economy staging emotion,
curiosity, and psychopathology together. Verdict: **real, but it is a demonstration
of established science on a distinctive substrate — not new affective science.**

**One thing the project already gets right and must keep saying:** every results doc
here leads with "re-derive, not invent," names qualia as out of scope (functional
regulator only), and marks the social-emotion gap (guilt/shame need the ToM
machinery, unbuilt) — `VISION_CORE_EMOTIONS_RESULTS.md` §0, §9. That honesty is
correct and should not be softened.

---

## 4. Honest verdict

**The emotion framework is a re-derivation of well-established affective, decision,
and psychiatric science, delivered on a distinctive integer graph-native substrate
with two clean unifying framings and a genuinely useful knob-turnable artifact — it
is not new affective science, and must not be presented as one.** Piece by piece:
emotion-as-the-decision-enabler/regress-breaker is **Herbert Simon (1967)**,
reinforced by **Damasio**, dual-process theory, and the **Russell–Wefald**
metareasoning literature; appraisal→action-tendency on valence×arousal is
**Lazarus / Scherer / Frijda / Russell / Ekman**; emotions-as-evolved-value-regulators
is **Tooby–Cosmides and Nesse**; the reference-frame/supergraph and fulfilment
pieces are **Hamilton, Sober–Wilson, Haidt, Andreoni**, with the parenthood
dissociation from **Nelson–Kushlev–Lyubomirsky / Baumeister**; eudaimonia≠hedonia is
**Aristotle → Ryan-Deci / Ryff / Waterman**; self-transcendence is
**Frankl / Maslow / Erikson / Steger**; learning-progress curiosity and the noisy-TV
fix are **Schmidhuber and Oudeyer–Kaplan** (noisy-TV named by **Burda et al.**);
the state-over-symptom taxonomy is **RDoC (Insel)** with disorders-as-mis-set-precision
from **Kapur / Friston / Corlett** and the psychopathy value/cognition split from
**Blair and Meffert et al. (2013)**; and nature/nurture-as-decomposition is
**quantitative/behavioural genetics (Fisher, Turkheimer, diathesis-stress, GxE)**.
Most decisively for the "is the *architecture* new?" question: **Dörner's PSI /
Bach's MicroPsi already build emotions as modulator parameters of a cognitive agent
and already show that an agent without them is decision-impaired.** There is **no
single named theory for the full seven-piece synthesis** — but every piece, and even
the "emotions are knobs on a cognitive architecture" architecture, is prior work.

Where the contribution actually is, stated without flattery: **(1)** two crisp
unifying *framings* — "each emotion's value function is a level of selection" and
"decay/curiosity/emotion/disorder are settings of one shared integer economy" — both
of which organise established facts rather than add new ones (the first precedented
in multi-level selection, the second in the FEP); **(2)** a literal shared-atom,
integer, graph-native *instantiation* in which the SAME nodes serve perception,
emotion, and the disorder knobs, with no new module or Term — an uncommon build, not
a new science; and **(3)** a *default-OFF, byte-identity-gated, knob-reversible
artifact* — the 11-emotion appraisal set with minimal-pair discriminators, the
hedonic/eudaimonic cross, and the reversible glass-box disorder knobs — whose value
is conviction and reuse, and whose knobs are authored, model-internal, and
clinically unvalidated. All three are contributions of *framing, instantiation, and
demonstration*, not of the underlying affective science. The correct posture toward
the headline ("emotions are the value-regulating decision layer of a bounded agent")
is the humble one: it is true, it is important, and it was established by others —
from Simon in 1967 to Tooby–Cosmides to Dörner/Bach — and the project's job was to
build a substrate on which it is *manifestly, checkably, reversibly* instantiated. To
that narrow end the artifact is real; beyond it, we re-derive.
