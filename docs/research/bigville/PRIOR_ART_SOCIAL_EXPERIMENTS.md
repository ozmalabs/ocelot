# PRIOR ART — social / developmental / affective experiments, mapped across BOTH camps

**Status:** search-grounded prior-art map. RESEARCH ONLY — no build, no measurement, no numbers,
no `seed_claim`, no engine touched. Written to be attacked: every citation below was checked via
live search on 2026-07-28; a fabricated or hallucinated citation is a firing offence, so
unverified items are flagged as such rather than reconstructed from priors.

**SEARCH AVAILABILITY (tested as the FIRST action, per instrument discipline).** `WebSearch` was
LIVE and used for every claim in this doc; `WebFetch` was LIVE and used to read specific abstracts
(the co-regulation preprint arXiv:2605.07524 and the LLM-temporal-discounting preprint
arXiv:2606.05194 were read directly, not paraphrased from a results snippet). No claim in this doc
is made from priors alone. Confidence is labelled per claim with its source tier:

- **[HIGH]** — full text / abstract read (WebFetch), OR corroborated across ≥2 independent search
  sources including the primary venue, OR already verified in a companion grounding doc.
- **[MEDIUM]** — title / authors / venue confirmed in search, findings from search summary or a
  single source, full text not independently read.
- **[LOW]** — a single search snippet only; existence plausible but not corroborated. Explicitly
  the weakest tier; do not build on it without re-verifying.
- **[NONE-FOUND]** — an ABSENCE claim. Absence claims are weak by construction (search cannot prove
  a negative); every one below means "not found in the searches run," never "does not exist."

**How this doc relates to what the repo already grounded (extend, don't duplicate).** Three
companion docs already stand and were re-read before writing this one:
- `SOCIETY_EXPERIMENTS_SURVEY.md` — verified the economic-game and Cluster-2 developmental targets
  (Trust/Berg, Public Goods/Fehr–Gächter, Axelrod, Ultimatum, Generative Agents, Melting Pot,
  Concordia, Asch/Milgram; Harlow D1/D2, Ainsworth D3, Seligman D4). This doc DOES NOT re-derive
  those; it cites them and adds ONE thing the survey did not check: the **developmental-robotics
  attachment literature** (the survey wrote "NO open code, expected" for Harlow — true for a
  literal port, but it did not search the robot-caregiver line, which is a real and relevant camp).
- `GLASS_BOX_SOCIETY_SCOPING.md` §9 — prior art for the society line (Park, MARL emergent-comms,
  Axelrod, Ostrom, Hamilton/Fehr–Gächter/Schelling). Reconciled in Rung 3.
- `MOOD_MOMENTUM_SCOPING.md` §1, §6 — already search-verified the mood-dynamics literature
  (Eldar/Niv 2016, Eldar & Niv 2015, Niv/Daw/Dayan 2007, Nettle & Bateson 2012, Russell 2003,
  Bower 1981). Reconciled in Rung 2; this doc adds the non-Eldar computational mood-dynamics
  strands and does NOT restate the Eldar model's equations (they are in that doc).

**Where the grounding docs are THIN and this doc updates them:**
- The survey's "no prior art, expected" verdict for Harlow is **too strong** — it holds for a
  literal LLM/code port but MISSES the developmental-robotics caregiver-attachment tradition
  (Rung 1). Corrected here.
- Neither grounding doc covers the **marshmallow / delay-of-gratification** line at all — it is a
  net-new section (Rung 4), including the reliability-prior critique that is the crux.
- Neither grounding doc covers **arousal / window of tolerance / co-regulation** — net-new (Rung 5),
  and the one where the field's coverage is most uneven.

---

## THE TWO CAMPS (framing for every rung)

Every rung below is scored against two prior-art camps. They are genuinely different research
programs, and the honest positioning is that they are **ahead of us on different axes**, not behind.

**Camp A — trained / black-box LLM-agent replication (and RL).** Give a pretrained model an
endowment, a persona, and a scenario prompt; read out its behaviour; compare to the human study.
Exemplars: Horton, Filippas & Manning's *homo silicus* [HIGH]; Aher, Arriaga & Kalai's multi-human
simulation [HIGH]; Park et al.'s Generative Agents [HIGH]. **Strength:** astonishing BREADTH — one
model reproduces the aggregate behavioural signature of dozens of human studies with near-zero
per-study engineering, and often gets the direction and rough magnitude right. **Weaknesses,
honestly:** the "why" is confabulated post-hoc natural-language (the model narrates a reason it did
not compute); it is EXPENSIVE (per-step API calls); the persona lives distributed in a net you
cannot read or cleanly ablate; and it inherits training-set contamination (many of these classic
studies are IN the training corpus, so "reproduction" can be recall).

**Camp B — classical connectionist / RL + developmental robotics + computational affective
science.** Build one bespoke mechanistic model per phenomenon: a coupled-oscillator dyad, an
arousal-homeostasis robot, an RL discounting agent, an active-inference co-regulation model.
Exemplars per rung below. **Strength:** MECHANISTIC and inspectable — the model IS the explanation,
and the parameters are causal knobs. **Weaknesses, honestly:** bespoke (one model per phenomenon,
little shared substrate), often not embodied/behaving end-to-end, and rarely run as
seed-varied population experiments.

**The substrate's actual differentiator — a DIFFERENT axis, not "we win."** We do not claim to beat
Camp A on behavioural breadth (we cannot yet — see the honesty section). The differentiator is
**one unified, mechanistic, glass-box, cheap substrate** that (a) expresses many of these
phenomena as configurations of ONE small operation set rather than one model each, (b) reads the
"why" off graph data instead of confabulating it, (c) runs without a per-step LLM, and (d) enables
**causally-clean experiments neither camp runs**: settable priors as an independent variable, the
marshmallow *dissolution* (separating temperament from the reliability-prior — a confound humans
cannot remove), and watching an arousal window narrow/widen mechanically. Per rung, the novelty
claim is stated honestly, INCLUDING "already done — we add inspectability, not novelty" where that
is the truth.

---

## RUNG 1 — Harlow wire/cloth attachment (contact-comfort > feeding)

**The human/primate result — [HIGH].** Harlow, H.F. (1958), *"The Nature of Love,"* American
Psychologist 13:673–685. Infant rhesus macaques preferred a cloth surrogate that gave no milk over
a wire surrogate that did, clung to the cloth mother, and fled TO it as a secure base under fright:
contact comfort > feeding; attachment is a primary drive, not derived from nourishment. Corroborated
across multiple sources and the survey's own verification.

**Camp A (LLM/RL): [NONE-FOUND].** No LLM or RL replication of the wire/cloth choice located — and
this absence is EXPECTED and correct: it is an embodied primate-development study with no verbal
protocol to prompt. The survey's verdict here holds. Do not invent one.

**Camp B (developmental robotics) — [HIGH] that a real, directly-relevant tradition EXISTS; the
survey MISSED it.** There is a sustained developmental-robotics line modelling caregiver attachment
mechanistically:
- **Hiolle & Cañamero and colleagues (University of Hertfordshire / Portsmouth).** An arousal-based
  architecture on a Sony AIBO robot exploring a play mat: novel percepts raise an internal *arousal*
  variable; high arousal triggers calls for attention to a human caregiver, who can comfort (lower
  arousal) or leave the robot to cope. The caregiver's responsiveness shapes what the robot learns —
  an explicit infant-caregiver attachment analogue. Key verified references:
  - Hiolle, Cañamero, Davila-Ross & Bard, *"Eliciting Caregiving Behavior in Dyadic Human-Robot
    Attachment-Like Interactions,"* **ACM Transactions on Interactive Intelligent Systems (TiiS)
    2012** (DOI 10.1145/2133366.2133369). [HIGH — venue/DOI corroborated across ACM, Herts, Portsmouth
    records.]
  - Hiolle, Lewis & Cañamero (2014), *"Arousal Regulation and Affective Adaptation to Human
    Responsiveness by a Robot that Explores and Learns a Novel Environment,"* **Frontiers in
    Neurorobotics**, PubMed 24860492. [HIGH — PubMed record confirmed.]
  - An earlier attachment-architecture paper, *"Attachment Bonds for Human-Like Robots,"*
    **International Journal of Humanoid Robotics (2006)** (World Scientific,
    S0219843606000771). [MEDIUM — record confirmed; authorship line consistent with the Cañamero
    group but not independently re-read.]
- **Broader developmental-robotics affect programs — real, but NOT a Harlow attachment replication
  ([HIGH] they exist; [HIGH] they are a different target).** Minoru Asada's *cognitive developmental
  robotics* (Asada et al. 2009, *"Cognitive Developmental Robotics: A Survey,"* IEEE Trans.
  Autonomous Mental Development) and his conceptual empathy-development model (emotional contagion →
  envy/schadenfreude with self/other differentiation); Angelo Cangelosi's developmental-robotics /
  iCub work (Cangelosi 2018, *"From Babies to Robots,"* Child Development Perspectives; Cangelosi &
  Asada eds., *Cognitive Robotics*, MIT Press 2022). **Honest note:** these are real, verified
  researchers and programs, but their affect work is emotional-contagion / empathy / vocalization
  development — NOT the contact-comfort-vs-feeding attachment choice. The task named "Asada /
  Cangelosi lines"; the accurate finding is that the *attachment-to-caregiver* replication belongs to
  the **Hiolle–Cañamero** line specifically, while Asada/Cangelosi are the adjacent affect-development
  camp. Attributing a Harlow replication to Asada or Cangelosi would be a fabrication; I do not.

**Verdict — does a genuine computational replication exist?** **Partially, and more than the survey
said.** A literal wire/cloth *choice* replication: not found. But a mechanistic
**arousal-based infant-caregiver attachment model that reproduces the FUNCTIONAL core** (seek the
caregiver under distress; the caregiver as a secure base regulating exploration; comfort as a
primary regulatory input) **does exist and is gated in the robotics literature** (Hiolle–Cañamero).
So the honest framing is NOT "nobody has modelled attachment" — it is "the functional
attachment-regulation loop has been modelled in developmental robotics; the specific
contact-comfort-OVER-feeding *adjudication* has not been run as a controlled mechanism comparison."

**Our delta (honest).** NOT "first to model attachment" — that would be false given Hiolle–Cañamero.
The genuine deltas are: (1) **the mechanism ADJUDICATION the monkey study could only infer** —
building contact-comfort-as-primary-drive vs cupboard-love-secondary-reinforcement as two seed
configurations and reading which reproduces clinging + flee-to-comfort (the robotics line assumes
the arousal-comfort loop; it does not pit it against a feeding-association account); (2) **glass-box
inspectability** — the bond, the drive, the comfort-input are readable nodes/attrs, not a robot's
distributed control state; (3) **seed-varied population** — attachment styles as a distribution over
drive weights (the survey's D1b lineage), which the single-robot studies do not run. This is
"already partly done (the regulation loop) — we add adjudication + inspectability + population,"
not "novel from scratch."

---

## RUNG 2 — Mood as momentum (+ set-point alternatives)

**Reconciliation with `MOOD_MOMENTUM_SCOPING.md` — that doc already search-verified the core.** The
scoping doc verified against PMC full text: Eldar, Rutledge, Dolan & Niv (2016), *"Mood as
Representation of Momentum,"* TICS 20(1):15–24 (mood ≈ leaky EMA of signed RPE; additive perceptual
feedback; adaptive under autocorrelated returns; high feedback gain → bipolar-like oscillation)
[HIGH]; the set-point alternatives Niv/Daw/Dayan 2007 (average-reward baseline / tonic dopamine)
[HIGH on RL], Nettle & Bateson 2012 (behavioural-ecology mood) [MEDIUM-HIGH], Russell 2003 (core
affect as slow baseline) [HIGH]; the clinical extreme Eldar & Niv 2015, *Nat. Commun.* 6:6149
(positive-feedback mood instability) [HIGH]; and Bower 1981 (mood-congruent cognition) [HIGH]. This
doc does NOT restate those; it treats them as the verified backbone.

**Camp A (LLM/RL) — [MEDIUM].** The mood-as-momentum model is itself an RL/computational-neuroscience
model, so the "trained camp" here is the reward-learning literature, and it is where the model was
BORN — this is a rung where Camp B is the incumbent, not Camp A. No LLM-agent "mood" replication with
a human number was searched for or found here; that is a genuine gap in this map (see open
questions), not an asserted absence.

**Camp B — OTHER computational mood-dynamics models beyond Eldar (the value this doc adds).** The
Eldar line is not the only formal mood-dynamics account:
- **Bipolar/cyclothymia as feedback-gain / oscillator instability.** The Eldar & Niv 2015 result
  frames bipolar dynamics as a positive-feedback runaway (mood → perception → surprise → mood),
  which is a control-loop-gain account of oscillation [HIGH, via the mood doc]. There is a broader
  dynamical-systems tradition modelling mood disorders as nonlinear oscillators / bistable systems
  (e.g., the general "mood as a damped or self-sustaining oscillator" framing that recurs in
  computational psychiatry) — **[LOW as a specific-citation claim: I did not run a dedicated search
  for a named bipolar-oscillator model in this pass, so I will not cite a specific paper I have not
  verified.** Flagged as an open item.]
- **Set-point / homeostatic baseline as a distinct quantity.** Reconfirmed via the mood doc:
  average-reward RL (a *level*) is a genuinely different variable from momentum (a *derivative*),
  which is what makes the "both, with a discriminating double-dissociation" design (that doc's R4)
  a real test rather than a fudge.

**Verdict — does a genuine computational replication exist?** **YES — this rung is the one where a
strong mechanistic prior-art model already exists (Eldar/Niv), and the repo has already engaged it
(blocks 236000/237000: MOOD R1 honest null, R1b regime-flip near-miss).** We are not first here and
must not claim to be.

**Our delta (honest).** NOT the mood-momentum idea (Eldar's) and NOT the set-point idea
(Niv/Daw/Dayan's). The genuine deltas: (1) **implementing BOTH layers on ONE shared substrate** as
reused decay/blend atoms rather than a bespoke model, with the double-dissociation as a falsifiable
"both" test; (2) **glass-box readout** — `Mood.momentum/setpoint/gain` as readable attrs and the
`biases_appraisal` edge visible, so a swing is watched forming rather than fit; (3) **the disorder
demo as a sibling of the same machinery** (gain sweep → emergent oscillation), continuous with the
substrate's other disorder glass-boxes. And the honest caveat the repo already recorded: the R1
null showed the fast layer may already track drift, so even our *mechanism* claim is under
empirical pressure — this is a rung where the field is ahead and our contribution is unification +
inspectability, not a new phenomenon.

---

## RUNG 3 — Trust Game / cooperation / glass-box society

**Reconciliation — `SOCIETY_EXPERIMENTS_SURVEY.md` already verified this rung in depth.** Cited, not
re-derived. Verified there: human baselines Berg, Dickhaut & McCabe (1995) Trust Game [HIGH],
Fehr & Gächter (2002) altruistic punishment [HIGH], Axelrod (1984) evolution of cooperation [HIGH],
Güth et al. (1982) Ultimatum [HIGH]; LLM baselines Xie et al. (NeurIPS 2024, trust) [HIGH], the
public-goods LLM papers [HIGH-ish], the Donor-Game cultural-evolution paper (2412.10270) [HIGH];
open harnesses Axelrod-Python (MIT) [HIGH], Melting Pot (Apache-2.0) [HIGH], Concordia (Apache-2.0)
[HIGH], Generative Agents (Apache-2.0) [HIGH].

**Camp A — additional verification the task asked for (done here):**
- **Horton, Filippas & Manning (2023), *"Large Language Models as Simulated Economic Agents: What
  Can We Learn from Homo Silicus?"* NBER Working Paper 31122 / arXiv:2301.07543. [HIGH — NBER + SSRN +
  arXiv records all confirmed.]** Argues LLMs are implicit computational models of humans; replicates
  behavioural-econ scenarios (Charness–Rabin, Kahneman et al., endowment effects) with qualitatively
  human-like results. This is the canonical "trained camp reproduces many human studies cheaply-ish"
  citation and the strongest single statement of Camp A's breadth.
- **Aher, Arriaga & Kalai (2023), *"Using Large Language Models to Simulate Multiple Humans and
  Replicate Human Subject Studies,"* arXiv:2208.10264, ICML 2023. [HIGH — verified in the survey.]**
  Replicates Ultimatum, a Milgram-style study, Wisdom-of-Crowds, Garden-Path.
- **Park et al. (2023), Generative Agents, UIST 2023. [HIGH.]** Emergent coordination (info
  diffusion, a party spreads) among 25 memory/reflection/planning agents. The north-star RIVAL, not
  a human-baseline replication (no human number).
- **DeepMind Melting Pot [HIGH]** (MARL social-dilemma substrate suite, Apache-2.0) and **DeepMind
  Concordia [HIGH]** (LLM game-master society library, Apache-2.0) — both confirmed in the survey as
  real, open, agent-agnostic environments we can drop seeded (G,Γ) agents into.

**Camp B — classical.** Axelrod (iterated PD, TFT) [HIGH]; Ostrom, *Governing the Commons* (1990)
[HIGH]; Hamilton (kin/spite), Fehr–Gächter (costly punishment), Schelling (focal points) — the
game-theoretic scaffolding the glass-box society doc already lists. Nowak's five rules for the
evolution of cooperation sits here too as the standard synthesis [MEDIUM — named from standard
knowledge, not re-verified this pass].

**Verdict — does a genuine replication exist?** **YES, abundantly, in BOTH camps.** This is the rung
where the field is MOST ahead: human baselines are decades old, LLM replications are numerous and
recent, and open harnesses exist. We are unambiguously not first.

**Our delta (honest).** NOT reproducing the aggregate cooperation numbers (both camps do that
already). The genuine deltas: (1) **the "why" is mechanical, not confabulated** — the return/punish
decision is a rule reading a visible trust/reciprocity/anger attr, versus the LLM camp's post-hoc
BDI narration; (2) **seed as a clean independent variable** — honest/spite/psychopath modulators move
the return rate CI-separably, causally SET rather than correlated out of a black box; (3) **cheap** —
no per-step LLM; (4) **the deception-is-real gate** (stated ≠ held intent as a readable graph gap)
that neither the human nor LLM version can read directly. This is "behavioural reproduction already
done — we add mechanism, causal-clean IV, cost, and a deception readout," explicitly not novelty on
the behaviour.

---

## RUNG 4 — Delay of gratification / marshmallow (and the reliability-prior dissolution)

**The human results — [HIGH], including the two that matter most for us.**
- **Original:** Mischel's marshmallow paradigm (1970s); Shoda, Mischel & Peake (1990) linked
  preschool delay to later outcomes. [HIGH — canonical.]
- **The reliability-prior critique (THE crux for our differentiator) — [HIGH].** Kidd, Palmeri &
  Aslin (2013), *"Rational snacking: Young children's decision-making on the marshmallow task is
  moderated by beliefs about environmental reliability,"* **Cognition 126(1):109–114.** Children
  (M≈4;6, N=28) first experienced a reliable or unreliable adult; those in the *reliable* condition
  waited far longer than those in the *unreliable* condition (reported group means ≈12 min vs ≈3 min
  of a 15-min cap). Interpretation: waiting is partly a RATIONAL decision about environmental
  reliability, not solely a self-control trait. [HIGH — corroborated across ScienceDirect, the
  archived PDF, and multiple summaries incl. the reported means.] An extension study
  (S0022096519303662, *Journal of Experimental Child Psychology*) reproduces the reliability effect
  direction [MEDIUM].
- **The replication that shrank the trait story — [HIGH].** Watts, Duncan & Quan (2018),
  *"Revisiting the Marshmallow Test: A Conceptual Replication…,"* **Psychological Science.** Larger,
  more diverse sample: an extra minute of delay at age 4 predicted only ~0.1 SD achievement at 15 —
  about HALF the original bivariate association, and reduced by roughly two-thirds once family
  background / early cognitive ability / home environment were controlled. Interpretation: much of
  the "willpower predicts success" story is confounded with background/cognitive capacity. [HIGH —
  Sage record + APS + NYU + a direct-comparison follow-up (PubMed 31850833) all corroborate.]

**Camp A (LLM) — [MEDIUM], and interestingly NEGATIVE.** LLMs handle intertemporal choice poorly:
- **Rios-Sialer et al. (2026), *"Temporal Preference Concepts and their Functions in a Large Language
  Model,"* arXiv:2606.05194. [HIGH — abstract read via WebFetch.]** Unintervened LLMs discount the
  future *several times less steeply* than humans, and the preference is *unstable across contexts*;
  the authors locate temporal-preference circuits and steer them (mechanistic interpretability).
- A related preprint, arXiv:2509.09704, *"Temporal Preferences in Language Models for Long-Horizon
  Assistance"* [LOW — title/snippet only, not read], and a search summary reporting LLM discount
  rates off human indifference points by 100–400× [LOW — snippet, source not pinned]. I flag these
  as under-verified rather than assert their numbers.
- **No LLM "marshmallow test" per se** — i.e., no LLM study I found that manipulates the
  *reliability prior* the way Kidd did. [NONE-FOUND — an absence, weak by construction.]

**Camp B (RL / computational) — [HIGH] that the discounting machinery is classic; [MEDIUM] on the
self-control-specific models.** Delay of gratification maps directly onto temporal-difference RL and
delay discounting:
- Hyperbolic discounting predicts the preference-reversal that IS the self-control failure
  (smaller-sooner preferred only when both rewards are proximal) — the standard behavioural-economics
  account [HIGH]. RL treatments include Fedus et al. (2019), *"Hyperbolic Discounting and Learning
  over Multiple Horizons,"* arXiv:1902.06865 [MEDIUM — record confirmed], and RL with non-exponential
  discounting (arXiv:2209.13413) [MEDIUM].
- Precommitment as an RL mechanism: Kurth-Nelson & Redish, *"A Reinforcement Learning Model of
  Precommitment in Decision Making,"* **Frontiers in Behavioral Neuroscience (2010)** [MEDIUM —
  title/venue confirmed]. Delay-of-gratification-as-choice (Rachlin/Ainslie tradition) sits behind
  all of this [MEDIUM — standard-knowledge, not re-verified this pass].

**Verdict — does a genuine replication exist, and has anyone SEPARATED temperament from the
reliability-prior?** The *behaviour* (discounting, preference reversal, precommitment) is thoroughly
modelled in RL [HIGH]. The *reliability-prior finding itself* (Kidd 2013) is a human experimental
result about beliefs, and **I found NO computational model that cleanly SEPARATES a stable
temperament parameter from an inferred environmental-reliability prior and varies each independently
— i.e., no model that does computationally what Kidd's between-subjects manipulation does, but with
the trait held fixed and the prior swept, or vice versa. [NONE-FOUND — absence, weak by
construction, but this is a genuinely thin area and the searches were targeted.]** This is the
sharpest "clean experiment neither camp runs" on the whole map: in humans, temperament and the
reliability-prior are CONFOUNDED (you cannot give the same child two different life-histories); a
substrate can hold the discount/patience seed fixed and set the reliability prior as an explicit,
readable node, or vice versa — dissolving the confound the original paradigm cannot touch.

**Our delta (honest).** NOT the discounting math (RL owns it) and NOT the reliability insight
(Kidd's). The genuine delta is **the dissolution experiment**: set temperament and
environmental-reliability as two orthogonal, readable knobs and show the "waited longer" outcome
decomposes into (patience-seed × inferred-reliability), reproducing Kidd's reliable-vs-unreliable
split as a prior manipulation with temperament held constant — and reproducing the "trait predicts
outcome shrinks under controls" Watts result as the reliability-prior doing the work the trait was
credited for. That is a causally-clean identification neither the human study (confounded) nor the
LLM camp (no reliability manipulation, and poor discounting to begin with) has run. Honest bound:
this is a mechanism/plausibility claim, not a developmental-psychology validation.

---

## RUNG 5 — Arousal / window of tolerance + co-regulation (the least-sure rung)

This is the rung the task flagged as least certain to have prior art. Searched hard. The honest
finding is **split**: the CLINICAL construct (window of tolerance) has NO formal computational model,
but the UNDERLYING mechanism (dyadic arousal coupling / co-regulation) has a real, verified modelling
tradition. Both halves matter.

**The clinical constructs — real but VERBAL, not computational — [HIGH] on existence, [NONE-FOUND]
on a formal model.**
- **Window of tolerance:** Dan Siegel (1999) — the optimal arousal zone between hyperarousal
  (panic/fight-flight) and hypoarousal (numbing/collapse). [HIGH — attribution corroborated across
  multiple clinical sources.] It is a conceptual/clinical framework; **no formal computational or
  mathematical implementation of "the window" was found. [NONE-FOUND.]**
- **Polyvagal theory:** Porges (2011) — a hierarchical autonomic model (ventral-vagal social
  engagement / sympathetic mobilization / dorsal-vagal immobilization) with "neuroception" of
  safety. [HIGH — existence and content corroborated, incl. a 2025 Frontiers review.] It is a
  neuro-anatomical/verbal theory; **no computational polyvagal model was found. [NONE-FOUND.]** The
  closest adjacent computational work is the *Arousal-Regulated Filter* (bioRxiv 2025.03.31.646280) —
  norepinephrine-gain modulation of feedforward vs recurrent dynamics for neural state estimation
  [MEDIUM — single preprint] — but that is a single-agent neural-gain model, NOT polyvagal and NOT
  co-regulatory.

**The mechanism DOES have prior art — dyadic arousal coupling / co-regulation — [HIGH] this tradition
exists.** This is the key correction to any assumption that co-regulation is un-modelled:
- **Coupled-oscillator / dynamical-systems co-regulation (the strongest classical line).**
  Butner, Diamond & Hicks (2007), *"Attachment style and two forms of affect coregulation between
  romantic partners,"* **Personal Relationships** [HIGH]; the coupled linear/damped oscillator (CLO)
  model (Butner, Amazeen & Mulvey) distinguishing co-regulation from co-dysregulation [MEDIUM];
  Reed and colleagues, *"Dynamical systems modeling of physiological coregulation in dyadic
  interactions,"* **Biological Psychology / Int. J. Psychophysiology (2013)** (PubMed 23107993,
  S0167876012006290) — a system of differential equations fit to couples' heart-rate/respiration
  time series, with explicit self-regulation and co-regulation parameters [HIGH on existence; author
  order not independently pinned]; Butler & Randall (2013), *"Emotional Coregulation in Close
  Relationships,"* **Emotion Review** — the review that frames coregulation as a dyadic oscillating
  arousal system maintaining an optimal state [HIGH]. **Note:** "maintaining an optimal emotional
  state via oscillating arousal/dampening" is essentially a formalized window-of-tolerance idea —
  so the mechanism behind the window HAS been modelled, just not under that name.
- **Developmental-robotics arousal + caregiver (bridges to Rung 1).** Hiolle & Cañamero's
  arousal-based robot (above) IS an inter-agent arousal-regulation model: the caregiver's comfort
  lowers the robot's arousal — a mechanistic co-regulation loop [HIGH].
- **Active-inference co-regulation (the most recent, and the closest to a two-agent mechanistic
  model) — [HIGH], abstract read.** Tsubamoto & Horii (2026), *"Dynamic Representational Synchrony
  through Collective Predictive Coding: A Computational Model of Parent-Infant Homeostatic
  Co-Regulation,"* arXiv:2605.07524. Parent and infant agents modelled with asymmetric sensory
  access (parent sees external cues; infant senses its own viscera), agreeing on homeostatic
  regulatory actions through a shared communicative variable (POMDP active interoceptive inference +
  a Metropolis-Hastings naming game); representational synchrony emerges before their internal models
  converge. This is a genuine two-agent homeostatic co-regulation model. [HIGH on existence/content;
  it is a preprint — MEDIUM on standing/impact.]

**Verdict — does a mechanistic co-regulation-as-inter-agent-arousal-coupling model exist, or is it a
gap?** **It EXISTS — this is NOT a clean gap, and it would be wrong (and easily falsified) to claim
co-regulation is un-modelled.** The coupled-oscillator dyad tradition, the arousal-caregiver robot,
and the active-inference parent-infant model all model inter-agent arousal coupling mechanistically.
**What is genuinely thin / [NONE-FOUND]:** (1) the *window of tolerance* as a named, formal,
watch-it-narrow-and-widen computational construct; (2) polyvagal theory as a computational model;
(3) a model that unifies the SINGLE-agent arousal window with the TWO-agent co-regulation loop in one
mechanistic, inspectable substrate and treats "window width" as a readable, manipulable parameter.
So: mechanism — already modelled (concede clearly); the specific clinical framing and the
single↔dyad unification with an inspectable window — thin, and a real opening.

**Our delta (honest).** NOT "first to model co-regulation" — that would be false (Butner/Reed,
Hiolle–Cañamero, Tsubamoto–Horii). The genuine deltas: (1) **the window of tolerance as an explicit,
readable parameter you can watch narrow (trauma/dysregulation) and widen (co-regulation) mechanically**
— the clinical construct rendered as a glass-box knob rather than a metaphor; (2) **unifying the
single-agent arousal regulator and the two-agent coupling on ONE substrate** rather than a bespoke
oscillator per study; (3) **glass-box readout of who is regulating whom** — the coupling as visible
edges/attrs, not inferred from cross-correlation of physiological time series (the classical method's
main limitation). This is the rung with the most honest room for a distinct contribution, PROVIDED
we concede the coregulation-mechanism prior art up front.

---

## WHERE THE FIELD IS GENUINELY AHEAD OF US (honest, not boosterish)

- **Behavioural reproduction breadth belongs to Camp A.** The LLM camp (Horton *homo silicus*, Aher
  et al., and the growing "LLM social simulation" literature) reproduces the aggregate behavioural
  signature of a large and growing set of human studies — economic games, conformity, obedience,
  fairness — with near-zero per-study engineering. **We do not beat them on this axis and should not
  claim to.** One pretrained model covers dozens of studies; our substrate covers what we have
  hand-built seeds for. On raw coverage of "reproduces human study X," they are ahead, today.
- **Cooperation / economic games (Rung 3) are saturated in both camps.** Human baselines are decades
  old, LLM replications are numerous, open harnesses exist. Our contribution there is mechanism +
  cost + causal-clean IV, not novelty of the behaviour.
- **Mood dynamics (Rung 2) has a strong incumbent model (Eldar/Niv), and our own R1 came back a
  null on the pinned config.** The mechanism is not ours and its adaptive value is under empirical
  pressure in our own hands. Honest.
- **Co-regulation mechanism (Rung 5) is already modelled** by the coupled-oscillator and
  active-inference lines. We add framing + unification + inspectability, not the mechanism.
- **The discounting math (Rung 4) is owned by RL.** Hyperbolic discounting and preference reversal
  are textbook. We add the confound-dissolution experiment, not the discounting.

The honest summary: **on "can you reproduce human behaviour," the trained camp is ahead on breadth
and the classical camp is ahead on any single well-studied mechanism. Our axis is orthogonal — one
unified, inspectable, cheap substrate that runs the causally-clean experiments neither camp runs.**
If we ever frame it as "we beat LLMs at reproducing studies," we will be wrong and correctly
attacked.

---

## PER-RUNG NOVELTY LEDGER (what is genuinely novel for us vs already-done)

| Rung | Already done (concede) | Genuinely novel-for-us (honest) |
|---|---|---|
| 1 Harlow | Arousal-based infant-caregiver attachment loop (Hiolle–Cañamero robotics) | Mechanism *adjudication* (comfort-drive vs cupboard-love); glass-box bond/drive; seed-varied attachment-style population |
| 2 Mood | Mood-as-momentum + set-point models (Eldar/Niv; Niv/Daw/Dayan) | Both layers on ONE substrate w/ double-dissociation; readable gain/momentum; disorder-demo sibling. (Our R1 null: even mechanism is contested) |
| 3 Trust/society | Human baselines + many LLM replications + open harnesses | Mechanical (not confabulated) "why"; seed as clean IV; cheap (no per-step LLM); deception-is-real gate |
| 4 Marshmallow | Discounting/preference-reversal/precommitment (RL); reliability-prior finding (Kidd) | **The dissolution** — separating temperament from the reliability-prior as orthogonal readable knobs (a confound humans cannot remove) |
| 5 Arousal/co-reg | Dyadic arousal coupling (coupled-oscillator; active-inference CPC; arousal-robot) | Window-of-tolerance as a readable, watch-it-narrow/widen knob; single↔dyad unification on one substrate; inspectable who-regulates-whom |

The pattern: on **behaviour** we are rarely novel; on **causally-clean, inspectable mechanism
experiments** we have a real and defensible line — sharpest at Rung 4 (the marshmallow dissolution)
and Rung 5 (the window as a knob), softest at Rung 3 (saturated) and Rung 2 (strong incumbent +
our own null).

---

## CONSOLIDATED VERIFIED-CITATION LIST (with confidence + source tier)

**Human / primate baselines**
- Harlow, H.F. (1958), *"The Nature of Love,"* American Psychologist 13:673–685. [HIGH]
- Mischel marshmallow paradigm (1970s); Shoda, Mischel & Peake (1990), delay→outcomes. [HIGH]
- Kidd, Palmeri & Aslin (2013), *"Rational snacking…,"* Cognition 126(1):109–114. [HIGH]
- Watts, Duncan & Quan (2018), *"Revisiting the Marshmallow Test…,"* Psychological Science. [HIGH]
- Berg, Dickhaut & McCabe (1995), Trust Game, Games & Economic Behavior 10(1):122–142. [HIGH, via survey]
- Fehr & Gächter (2002), altruistic punishment, Nature 415:137–140. [HIGH, via survey]
- Güth, Schmittberger & Schwarze (1982), Ultimatum, JEBO 3(4):367–388. [HIGH, via survey]
- Axelrod (1984), *The Evolution of Cooperation*; Ostrom (1990), *Governing the Commons*. [HIGH]
- Siegel (1999), window of tolerance; Porges (2011), polyvagal theory. [HIGH on existence]

**Computational mood dynamics** (verified in `MOOD_MOMENTUM_SCOPING.md`)
- Eldar, Rutledge, Dolan & Niv (2016), TICS 20(1):15–24. [HIGH]
- Eldar & Niv (2015), Nat. Commun. 6:6149. [HIGH]
- Niv, Daw, Dayan & Joel (2007), Psychopharmacology 191:507–520. [HIGH on RL]
- Nettle & Bateson (2012), Current Biology 22(17):R712–R721. [MEDIUM-HIGH]
- Russell (2003), Psychological Review 110(1):145–172. [HIGH on definition]
- Bower (1981), American Psychologist 36(2):129–148. [HIGH on effect]

**LLM-agent / trained camp**
- Horton, Filippas & Manning (2023), *Homo Silicus*, NBER w31122 / arXiv:2301.07543. [HIGH]
- Aher, Arriaga & Kalai (2023), arXiv:2208.10264, ICML 2023. [HIGH, via survey]
- Park et al. (2023), Generative Agents, UIST 2023. [HIGH, via survey]
- Xie et al. (2024), LLM Trust Behavior, NeurIPS 2024 / arXiv:2402.04559. [HIGH, via survey]
- Rios-Sialer et al. (2026), *Temporal Preference Concepts…in an LLM*, arXiv:2606.05194. [HIGH, abstract read]
- DeepMind Melting Pot (Apache-2.0); DeepMind Concordia (arXiv:2312.03664, Apache-2.0). [HIGH, via survey]

**Developmental robotics / affective computing (Camp B)**
- Hiolle, Cañamero et al. (2012), *"Eliciting Caregiving Behavior…,"* ACM TiiS, DOI 10.1145/2133366.2133369. [HIGH]
- Hiolle, Lewis & Cañamero (2014), *"Arousal Regulation…,"* Frontiers in Neurorobotics, PubMed 24860492. [HIGH]
- *"Attachment Bonds for Human-Like Robots"* (2006), Int. J. Humanoid Robotics, S0219843606000771. [MEDIUM]
- Asada et al. (2009), *"Cognitive Developmental Robotics: A Survey,"* IEEE TAMD. [HIGH — different target: empathy/contagion, not Harlow]
- Cangelosi (2018), *"From Babies to Robots,"* Child Development Perspectives; Cangelosi & Asada eds., *Cognitive Robotics*, MIT Press (2022). [HIGH — different target]

**Co-regulation / dyadic arousal coupling (Camp B)**
- Butner, Diamond & Hicks (2007), *"Attachment style and two forms of affect coregulation…,"* Personal Relationships. [HIGH]
- Reed et al. (2013), *"Dynamical systems modeling of physiological coregulation in dyadic interactions,"* Biological Psychology, PubMed 23107993. [HIGH on existence; author order unpinned]
- Butler & Randall (2013), *"Emotional Coregulation in Close Relationships,"* Emotion Review. [HIGH]
- Tsubamoto & Horii (2026), *"Dynamic Representational Synchrony through Collective Predictive Coding…,"* arXiv:2605.07524. [HIGH, abstract read]

**RL discounting / self-control (Camp B)**
- Fedus et al. (2019), *"Hyperbolic Discounting and Learning over Multiple Horizons,"* arXiv:1902.06865. [MEDIUM]
- RL with non-exponential discounting, arXiv:2209.13413. [MEDIUM]
- Kurth-Nelson & Redish (2010), *"A Reinforcement Learning Model of Precommitment…,"* Front. Behav. Neurosci. [MEDIUM]
- Arousal-Regulated Filter, bioRxiv 2025.03.31.646280. [MEDIUM — single-agent, not polyvagal]

---

## OPEN QUESTIONS / THIN EVIDENCE (what search could not resolve)

- **[NONE-FOUND, weak] No LLM/RL replication of the Harlow wire/cloth *choice*** — expected for an
  embodied study; do not invent one. The functional attachment loop IS modelled (Hiolle–Cañamero).
- **[NONE-FOUND, weak] No computational model that SEPARATES marshmallow temperament from the
  reliability-prior.** This is the sharpest opening on the map but also the claim most dependent on an
  absence — re-verify with a dedicated search before any pre-registration leans on "nobody has done
  this."
- **[LOW] LLM temporal-discounting magnitudes** (the 100–400×-off figure; arXiv:2509.09704 findings)
  are from snippets not read in full. The one paper I read (arXiv:2606.05194) says LLMs discount
  *less* steeply than humans and inconsistently — directionally clear, magnitudes not pinned.
- **[LOW] Named bipolar/cyclothymia oscillator models beyond Eldar & Niv** — I did not run a
  dedicated search this pass; do not cite a specific one until verified. The Eldar feedback-gain
  account is the only verified bipolar-dynamics model here.
- **[NONE-FOUND, weak but targeted] No formal computational model of the *window of tolerance* or of
  *polyvagal theory*** — both are verbal/clinical. The nearest computational neighbours are the
  single-agent Arousal-Regulated Filter (norepinephrine gain) and the dyadic coupled-oscillator
  co-regulation models. A unified single↔dyad inspectable-window model is the thin spot; confirm the
  absence with more searches before claiming primacy.
- **Author/attribution details to pin before any citation is load-bearing:** the exact author order
  of Reed et al. (2013); the exact authorship of the 2006 "Attachment Bonds for Human-Like Robots";
  the standing/peer-review status of the two 2026 arXiv preprints (2605.07524, 2606.05194). Existence
  is confirmed; final bibliographic detail is not.
- **Training-contamination caveat for Camp A (methodological, not a citation gap):** many of these
  classic studies are in LLM training corpora, so an LLM "replication" may be partial recall rather
  than simulation. This strengthens the glass-box positioning but is asserted from reasoning, not a
  cited measurement — flagged as such.

---

**Bottom line.** The field is ahead of us on *behavioural reproduction* — Camp A on breadth, Camp B
on any single well-studied mechanism — and we should never claim otherwise. Every rung here has real
prior art in at least one camp, and two rungs (Trust/society, Co-regulation mechanism) are frankly
saturated. Our defensible line is a DIFFERENT axis: one unified, mechanistic, glass-box, cheap
substrate running the causally-clean experiments neither camp runs — sharpest at the marshmallow
*dissolution* (Rung 4) and the window-of-tolerance-as-a-knob (Rung 5), where the prior art is
genuinely thin, and softest at Rungs 2 and 3, where honesty demands we claim inspectability and
cost, not novelty.
