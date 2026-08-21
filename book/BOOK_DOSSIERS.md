# BOOK_DOSSIERS — per-chapter claim and evidence

**Status: the working brief for each chapter.** What the chapter argues, the
measured evidence behind it, and the honest gaps. For *where the material
lives*, see `BOOK_SOURCES.md`; for structure, `BOOK_PLAN.md`; for register,
`BOOK_VOICE.md`.

**Numbering note.** Dossiers keep their original **source numbers** (01–23) —
these are the paper/artefact identities, and the preprints stay citable under
them. The book's own chapter numbers are 1–19; the mapping table is in
`BOOK_PLAN.md` § "The trim". Both numbers appear here so neither is lost.

| dossier | book chapter |
|---|---|
| 01, 05 | 14 — The law, and one machine that obeys it |
| 06 | 3 — Shape and Rule |
| 07 | 2 — The frame invariant |
| 08 | 4 — Dynamic quantisation |
| 09, 13 | 1 — The Eye (+ physics coda) |
| 10 | 5 — One-shot characters |
| 11 | 6 — Speech and word meaning |
| 12 | 7 — Space as a belief |
| 14 | 8 — Constructions propose, execution decides |
| 15 | 9 — One sensorimotor core, six bodies |
| 16, 17 | 10 — Emotion, and what it is for |
| 18 | 11 — When grounding fails |
| 19 | 12 — Coercive control |
| 20 | 13 — The town |
| 21 | 15 — A number where a shape belonged |
| 22 | 16 — Preregistration as an engineering method |
| 02 | 17 — Seldon manifolds |
| 03, 04 | 18 — Narrative momentum and narrativium |
| 23 | 19 — The open problem |

---

# Dossiers — Dynamics (sources 01, 05 → chapter 14)

Both written. As chapters they need subtraction, not new material: proofs and
conformance lists to an appendix, the axioms kept as boxes, and 05's "what
implementation taught the theory" rewritten as the eleven-point story it
already is rather than a numbered list.

---

# Dossiers — Cognition (sources 06–08 → chapters 2–4)

## 06 — Shape and Rule: graph dynamics as a theory of cognition (THEORY)

**Thesis, one line:** *Rule is how a graph runs; Shape is how a graph grows.*
Paper 01's `P → C` dynamic gives execution and nothing else — a graph whose Γ
and `r` are fixed can realise continuations forever without ever acquiring a
new one. Cognition is the closure of that dynamic under *self-extension*: the
graph decodes each observation against a held codebook, and the part that will
not fit — the **residual**, already a primitive in paper 01 — is the only
admissible signal for extending `r` and Γ.

Why this is the right cognition paper rather than a generic "graphs are minds"
claim: it makes four falsifiable commitments, all of them already measured.

1. **Residual is the sole growth channel.** A recogniser that always answers
   can never produce a residual, and a grain with no residual can never grow.
   Measured, not asserted: the agent's own meta-shape recogniser broke **44 of
   55 pairwise contests alphabetically by the shape's own name**, and deleting
   the tiebreak — not adding a mint rule — is what made growth reachable at
   all (`engine_substrate/META_SHAPE_FIRST_CLASS_RESULTS.md`).
2. **Growth is Occam-ordered, not one-shot.** recognise → transform in the
   existing basis → infer a new dimension → mint novelty, each rung tried only
   after the one above fails (`shape_decode.rs`; `seeds/shape_decode_loop.json`).
   A rotated tromino mints zero; a scrambled one mints exactly one.
3. **The two axes are independent and both are necessary.** Structural
   (shape) and name-keyword (rule-identity) selection over the agent's own rule
   corpus differ in exactly the predicted direction on both sides of a
   hand-verified oracle — 11/12 vs 0/12 and 12/12 vs 0/12, N=40, pre-registered
   floor of 5 (`RULE_SIGNATURE_SLICE_RESULTS.md`). Neither subsumes the other.
4. **Acquisition is transfer, not accumulation.** Three real corpus rules form
   a 2×2 parallelogram; one anti-unification over two corners derives the
   transform, substitution applies it to the third, and the completed corner is
   a rule absent from all 2,851 corpus recognisers that fires correctly when
   installed. **318 such parallelograms exist; 200/200 sampled transfers are
   lossless** (`RULE_REFERENCE_LAYER_SIZING_RESULTS.md`).

**Dependencies:** 01 (residual, Γ, collapse). Should be readable without 02–04.

**Honest boundary the paper must carry:** this is a *substrate* claim about
what makes growth possible, not a claim that the resulting system is a general
intelligence. State plainly that 38 of the 40 confirmed non-compliant sites in
`SHAPE_AUDIT.md` are still non-compliant, including a live `CapabilityAxis`
identity-collision bug.

## 07 — The frame invariant: in-frame integer, cross-frame continuum (THEORY, short)

**Thesis:** paper 01 states discrete sufficiency as a hypothesis. This paper
closes it with an operational decision procedure: *is this value IN a frame, or
BETWEEN frames?* In-frame coordinates are the integer lattice (sampling **is**
what grounding is); every real-valued structure — rotation by a real angle,
scale ratios, π, Fourier, log, comparison metrics, renderings — lives in the
map between frames, in `Hom(frame, frame)`, never in any object's coordinates.
Continuity is intensional only: a rule you apply, never an observed datum.

Second commitment, equally sharp: **two orthogonal unbounded axes** — the
extensive frontier (countable; unknown = absence, first-class) and the
intensive refinement axis (whose unreachable limit is the continuum). You
cannot reach a continuum by extending the discrete frontier, so the continuum
necessarily sits on a separate dimension.

**Why it earns a paper rather than a section:** it is load-bearing for every
capability paper below (each one cites it to justify why its representation is
integer and its verdict is not), it produced a design *refusal* on record
(dyadic refinement depth is **not** a dimension generator —
`runners/dsl/DYADIC_DEPTH_DESIGN.md`), and it has a clean empirical face:
"bins propose, continuous decides" is this invariant, measured at +51.5pp,
CI-separated (see C2).

**Dependencies:** 01. Cited by 08 and every C-paper.

## 08 — Dynamic quantisation: a constructive realisation of shape acquisition (IMPLEMENTATION)

The paper-05 counterpart for paper 06. Without it every capability paper
re-explains the loop from scratch.

Contents: `ShapeDecode` as the dequantisation operator; codebook as graph
data; the four-rung ladder (`TransformDecode`, `DimInfer`, mint) with the
dimension-generator codebook (rotation/reflection, log-scale ×2^k, modular
wrap) as *data* rather than cases; **the `run_rules` fixpoint IS the
decode → grow → re-decode loop** — no host-language iteration anywhere;
grain-agnosticism demonstrated by the same loader serving pixels, strokes,
statements, space and meta-shapes; epoch-gating as the termination argument.

Includes the negative engineering results, which are as useful as the design:
unconditional rule mirroring is a measured NO-GO (190 at-risk files, up to
51,769 mirror nodes for one rule, +2,557 nodes per checkpoint cycle with no
convergence), and dedup was never the reason to build any of it.

**Dependencies:** 06, 07, 05 (executor semantics).

---

# Dossiers — the capabilities (sources 09–20 → chapters 1, 5–13)

One template for all of them, so the series reads as a series: *(i)* what the
capability is, *(ii)* the graph-resident mechanism, cited to seeds and Rust,
*(iii)* the measured result with power and intervals, *(iv)* the nulls and
retractions, kept. Each paper is an instance of 08 applied to a different
observation stream — the point of the series is that the loop does not change.

## `09 — The Eye` — the flagship

**Not a "vision" paper.** The unit is an organ: a retina, an oculomotor
system, and the early dimensional inference an eye feeds. That scoping was the
founding thesis of the arc — *"a genuine eye implementation that works is
deliverable and valuable by itself"* — and it is what makes the paper
defensible where a "vision" paper would not be, because it lets the strongest
negative result in the tree sit inside the paper's scope instead of being an
embarrassment outside it: **this is an eye, and it is explicitly not a visual
cortex.** The synthesis document is already written and is close to a draft:
`docs/research/vision/THE_EYE.md` (302 lines, every claim, bound and retraction
in place); `VISION_PROTOCOL.md` is the binding-rules and burned-seed ledger it
cites.

**Claim 1 — every constant falls out of a measured quantity.** No float was
chosen to hit a target. The log receptor because Weber's law *is* a log of a
ratio (Weber–Fechner 0.9991; illumination invariance 0.44% vs 100%, ~1000×);
the adaptation setpoint from each cell's own endogenous activity (`μ_endo`
0.1459, derived per cell); the change threshold from the photon shot-noise
floor `|ΔI| > √(I/n_max)`, which on the log signal is Weber-normalised for
free; centre-surround *emerged* from Oja competition at a **zero** init
(CS 1.0839, σ_ON,ON 1.627 vs σ_ON,OFF 3.264); structure from retinal waves at
entropy 0.195 vs 0.000 under the same RNG. The one constant ever *imported*
(GCAL's `μ = 0.024`, from a frame this system does not have) killed cells in
two layers and was retracted.

**Claim 2 — the eye moves, and the motion is load-bearing.** Fixational drift
as a self-avoiding walk (α_short 1.1553 > 1 > α_long 0.7590, against Engbert's
0.79±0.11). This is also the paper's sharpest methodological anecdote: the
drift reproduced a published signature to two decimals **while driving
nothing** — its only consumer was the ruler that measured it — until it was
wired into the image. The field's own convergence is worth a paragraph: event
cameras independently reinvented the microsaccade, because a pure change
detector must move to see a static world.

**Claim 3 — the dimensions of sight are discovered, not stored.** This is
paper 07 with measurements attached, and it is the part of the eye that is
architecture rather than biology-replication:

- **Time** is the exponent of the transition generator carrying `frame(t) →
  frame(t+1)`. Time is not in any frame — it lives in `Hom(frame, frame)`.
  Ordered motion mints `latent:time` and compresses (MDL 28→7); the minted axis
  predicts the unseen frame `G⁷(f0)` exactly; **shuffled input mints nothing,
  0/400**; accelerating input correctly yields `time_none`.
- **Depth** is the temporal residual no single flat generator explains — near
  sweeps faster than far — so `latent:depth` orders the field by velocity
  (MDL 36→13). Monocular: it needs one *moving* eye, which the eye has. **The
  decisive control is that a flat scene mints nothing**, and neither does a
  multi-colour scene at one velocity: depth comes from velocity *variation*,
  never from region presence. A flat plane minting depth would be
  hallucination; it doesn't.
- **Stereo** is the *same operation on simultaneous frames*. `DepthInfer`
  generalised across frame-source **with an empty source diff** — fed N eyes at
  one instant instead of one eye over ticks, the unchanged Term mints the same
  dimension. **Eyes and ticks are the same resource, proven in code.** Built for
  N and never for 2 (the eye count falls out of `Count(Eye hubs)`; no literal
  anywhere), and **N=3 rejects what N=2 hallucinates**. Motion and stereo are
  then two admissible generators for one dimension, held additively — you never
  choose parallax *or* stereopsis.

**Claim 4 — failure modes are the real tell.** Normal function is cheap to
fake; a failure mode is a claim about what a mechanism *drives*. **Troxler
fading replicates 8/8, p=0.0078** — a stabilised image fades to the setpoint
*while 100% alive*, a drifting one does not — and the content of that result is
two **independently derived** timescales (`τ_drift = 3` from the walk,
`τ_adapt = 160` from `μ_endo`) landing 53× apart with neither tuned to the
other. **Lid-suture worse than dark reproduces** (−0.1458), for a stated
reason: Oja converges to the leading PC of whatever it is shown, and noise has
no leading PC. Sibling replications (McCollough, crowding, border ownership)
have their own document families and are the natural companion section.

**Claim 5 — the cortex is a diagnosed dead end, not a gap.** Five
pre-registered rungs, an H1 null whose CI excludes the SESOI by 2.5×, five
artifact routes each closed by measurement, and an *arithmetic* cause rather
than a tuning failure: the input covariance's leading eigenvector is a DC blob,
and removing DC leaves a degenerate oriented pair, so preferred orientation is
a coin flip. Oja fits second-order statistics and orientation is not in them.
The missing cortical layer was **built** to test whether GCAL's actual
mechanism rescues it; there is no η at which the learning rule is both
convergent and load-bearing, and GCAL was verified from the primary source
(its orientation comes from its settling steps, and even those are a tolerance
predicate, not demonstrated convergence). **The redirection is the arc's real
finding: the 3D world was never in a still image — it is in the relations
between frames, and those the substrate can discover.** Biology agrees; dorsal
is early and central, and the static ventral path was the wrong place to start.

**Claim 6 — the scaling wall is the boundary, not the arithmetic.** Linear
curve, no cache cliff; the memory-bus hypothesis is refuted. 75–82% of a tick
was the host↔Rust FFI; bulking the boundary gave 5.06× and inverted the budget,
predicate pushdown a further 4.29× on the dominant rule — fovea (~150k cells)
1317 → 137.8 ms. A GPU cannot help: it targets ≤25% of the budget and that part
is enumeration, not float math.

**The honesty ledger is a section, not a footnote.** Five retractions kept in
place with the measurement that forced each, and — the most transferable
finding — **sixteen inert instruments found in one arc, not one of them caught
by a gate going red.** Every one was caught by someone noticing a result was
too clean. That belongs in this paper *and* is the empirical core of 19.

**If length forces a split**, the line is organ vs dimensional stack: claims
1, 2, 4, 5, 6 are "The Eye"; claim 3 becomes **"Eyes and ticks are the same
resource"** — a single-thesis paper on frame-source generality, with the empty
diff, the N-not-2 construction, and the anti-hallucination controls as its
whole argument. Prefer one paper; that split is the fallback, not the plan.

## `10 — One-shot character recognition`

The second flagship, and the one that faces a benchmark. Publish after 09,
because 09 establishes that dimensions are discovered and 10 establishes what
decides between candidates.

- Composition is the real effect: **+21pp over a multiset baseline,
  CI-separated** — identity lives in arrangement, not in the parts (real
  strokes occupy only ~5–7 quantised classes).
- **Run 15 corrected the arc itself:** at n=400 with Wilson intervals the
  honest ceiling was 26.8% [22.6, 31.3], and every post-composition delta
  claimed earlier (AbS +3.7, dwell +1.3, appearance +2.5) was 1–3 episodes of
  noise. The 4-alphabet eval had been an easy subset.
- **Run 16 then dissolved that terminus:** the difference was the verdict
  comparator, not the representation. Strong continuous geometry at full dwell
  on the powered protocol = **73.5% [67.0, 79.1], +51.5pp** — and cheaper per
  comparison than the weak path it replaced.
- The synthesis, which is paper 07 with numbers on it: **earned quanta are the
  proposal layer; continuous geometry is the verdict layer.**

A paper that reports its own 3.4× sizing miss and its own eval-subset error is
more credible than one that reports 73.5% alone. Lead with that.

## `11 — Speech and word meaning from scratch`

Two separable claims, and the paper must keep them separable. **Capability:**
grounded word meaning learned from real children's programming and speech
structure from real audio, faster than realtime on a consumer CPU, with no
pretrained model in the decision path. **Developmental:** the traversal order
matches the canonical stages of child language acquisition — production before
perception, perceptual narrowing before word recognition, cross-situational
statistics under referential ambiguity, meaning reshaping perception — without
that order being imposed. Scope honestly: a handful of grounded words; the
claim is about method and cost profile, not recogniser accuracy.

Note the structural rhyme with 09 for the reader: perception by inverting your
own production is analysis-by-synthesis, the same operation as 10's
propose-render-compare and 09's generator-orbit prediction.

## `12 — Space as a belief, not a map`

Unknown is absence, first-class, never a default zero; quanta decoded per body
shape (a 1×1 and a 2×2 agent route differently over one belief); foveated and
incremental; N-dimensional with per-dimension resolution and per-dimension
residual splits. Understanding-before-winning is the framing and it is
measured: surprise drops 1.0 → 0.0 exactly at the cycle every station is
modelled, in lockstep with model accuracy rising to 1.0.

## `13 — A law of physics from pixels`

The eye's downstream, and a clean short paper of its own
(`docs/research/vision/physics_perception/`, 20 documents). The generic order-N
loop mints an **order-2 generator — uniform acceleration — from a tracked
object's trajectory, with no seeded gravity constant.** The witness matters as
much as the result: exact finite-difference equality floors on any real, noisy
video, so it was replaced by an MDL comparison (robust median plus residual
must cost strictly fewer bits than the raw stream), which is what closed the
gap between synthetic and real footage. `GALILEO_EQUIVALENCE_*` extends it to
mass — a robot discovering inertial mass by `impulse/Δv` and watching objects
fall under one constant should find the two are the same quantity seen through
two different motor/perceptual frames. That is paper 07's cross-frame thesis in
its most physical form.

## `14 — Constructions propose, execution decides`

Program synthesis: the sd loop one level up, at statement grain. One hub IR
over five frames (Python, Rust, Lua, x86-64, LLVM IR); a pure fueled
interpreter as the verdict; propose → order (bigram Viterbi) → splice →
evaluate → CEGIS → enumerate → accept-or-gap, every step a rule in the
fixpoint. This is the **third independent instance of the propose/decide
split** (after 09's additive generators and 10's bins-propose-continuous-
decides) — say so explicitly; the recurrence is the contribution.

## `15 — One sensorimotor core, six bodies`

The strongest evidence for the project's own success criterion: a capability
that generalises across bodies beats a capability that scores higher in one.
One body-agnostic core (`seeds/embodied_sensorimotor_core.json`) driving a
humanoid, an F-16 and X-15 in JSBSim, a helicopter autorotation, wheeled racing
bodies and a Crazyflie drone. Headline finding: an F-16 seeking a fixed point
that does not exist and a humanoid sitting in one it should have left are
**mirror images of one missing capability** — which reframes regime selection
as a Pareto frontier, measured, with the honest result that full-dwell
selection beats a shortlisted one.

## `16 — Emotion as mechanism`

**Not a chapter about feelings — a chapter about a control architecture that
turns out to need them.** Posture first, stated in the opening paragraph and
never walked back: every load-bearing affect idea used here is canonical
affective science, and the contribution is the *mechanistic, graph-native,
knob-turnable instantiation*, not the discovery. This project is re-deriving
known science on a new substrate, and says so
(`psychology_affect/EMOTION_FRAMEWORK_LITERATURE.md`).

What makes it a chapter rather than a survey is that the emotions are **grown,
not enumerated**. The thread builds hate, contempt, envy, resentment,
admiration and gratitude, the self-conscious emotions, and passion — each as a
*coupling* between existing atoms (arousal, appraisal, attribution, bond,
window-of-tolerance) rather than as a new node type per emotion. The hate
family alone is seven documents of coupling work: attribution, stability,
threshold lower bound, resentment, reset, pity/ToM. That is the admissibility
lesson at psychological grain — a taxonomy generated from a small basis instead
of a subsystem per feeling.

Load-bearing pieces for the chapter:

- **Mood is momentum plus set-point over the fast core**, not a scalar bolted
  on and not a running average — the literature-checked structural correction
  that replaced an intuitive one-node addition (`MOOD_MOMENTUM_SCOPING.md`,
  `MOOD_R1`/`R1B`/`R1C`).
- **Self-worth as a held quantity with three faces** — persistent, relative,
  domain-projected — plus self-efficacy and `ATTRIBUTION_LOCUS_AS_RESIDUAL`,
  which is the book's spine appearing inside a person: *where you locate a
  cause is what your model could not absorb.*
- **A retirement, kept**: `AROUSAL_CHANNEL_RETIREMENT` — a channel removed
  rather than defended, the affect thread's own instance of the Part VI
  discipline.
- The chapter's antagonist: an emotion added as a *label* on a node instead of
  a coupling between existing ones. Same defect as dossier 21's (book ch. 15), in a different
  vocabulary.

## `17 — Attachment, and the ability to wait`

Developmental psychology as a *causal-dissolution* instrument, which is the
honest thing a simulation can offer that a human study cannot.

**Harlow (`HARLOW_D1`, `D1B`).** The infant is not a bespoke attachment model —
it rides the real drive system (`contact_comfort`, `hunger`, `distress`), the
real regulator, and the real appraisal Argmax. **Drive weights are equal, 1/1:
the preference is not a weight thumb.** Contact wins because contact is needed
continuously and alone buffers the threat channel. N=200 infants per condition,
pre-registered before any number, results committed. A chapter that shows a
famous result emerging from a value economy nobody tuned for it is worth more
than one that reproduces the curve.

**The marshmallow test (`MARSHMALLOW_DELAY`).** The headline is not "the agent
waits." It is that the substrate **separates temperament from the
reliability-prior — the causally clean dissolution the human experiment cannot
run**, both main effects CI-separated, the confound exhibited in *both*
directions, N=60 per cohort with bootstrap intervals, every number matching the
pre-registered analytic grid. The doc states its own bound in bold and the
chapter must carry it verbatim: **this is a capability demonstration, not an
empirical claim about real children.**

The wait/take choice is one graph rule — an Argmax over two Appraisals — and
that same template is reused, unmodified, as dossier 19's intent control (book ch. 12). Say so;
the reuse is the argument.

## `18 — When grounding fails`

The clinical-adjacent chapter, and the one that most needs its register held.
Every claim in it is **mechanism and plausibility, never validated clinical
claim**, and the source documents already say so in their own verdict lines.

**Psychosis as a grounding failure mode.** Grounding is a predictive-coding
pull; run the *existing* collapse/grounding machinery in a failure regime and
it reproduces both native forms — self-grounding and non-optimal-basin — plus
the "AI psychosis" confirmer mechanism, with a matched control, **no new
mechanism, no new Rust**, 8/8 gated, every pre-registered prediction holding
monotonically. The chapter's honesty beat is the doc's own: this is not a claim
that the live agent went psychotic, and the authored ingredient is named rather
than hidden.

**Seizures** (`SEIZURE_ENGINE`, `SEIZURE_MODEL_V2`, plus a field comparison and
a data dive) are the same move in a different failure regime, and the pairing
is the chapter's real point: **a substrate that only ever works is unfalsifiable
as a model of anything.** Sibling grounding studies (narcissism, savant) sit
here as scoped literature work, flagged as such.

Where this chapter earns its place in the book: it is the psychological
counterpart of dossier 09's Troxler result (book ch. 1). *Normal function is cheap to fake; a
failure mode is a claim about what a mechanism drives.*

## `19 — Coercive control`

**The most serious chapter in the book, and the one whose protocol matters as
much as its results.** A fifteen-rung line — dyad (R1–R7), network (N1–N4),
intent (U0–U2), visibility (V1) — every rung pre-registered with a failable
control, every rung ethics-gated *before* it ran, across five scoping documents
written and locked in order. Clinical, anti-sensational register throughout.
Grounded in the author's own in-vivo trauma and foster-care experience, and
modelling **mechanism, not moral labels** — stated once, plainly, and then the
chapter behaves that way.

**The ethics protocol is quoted in full, not summarised**, because it is a
contribution in its own right and because a book chapter on this subject
without it would be indefensible: (1) induce → measure → **restore**,
byte-identical and checkpoint-verified as a gate; (2) no reward, no punishment
anywhere, source-audited for shaping tokens as a per-rung gate; (3) induce the
least the gate needs, every run ending settled and non-oriented; (4) same
mechanism, opposite thermodynamics — the real dynamic accumulates irreversible
harm in a person, the model induces and reverses a transient graph state,
harming no one. Each prereg also carries the *honest fork* — reversibility
stance versus strict-experientialist stance — openly rather than smuggling a
position.

**The finding all fifteen rungs elaborate** was measured by a *different* line,
before this one existed, and was not built for it: a regulating other placed
**on** the source of dysregulation "couples the wrong way and never returns"
(`AROUSAL_WOT`, the developmental line). Everything else is that finding pointed
at successively darker, more socially embedded configurations — with the
falsification bar that **no rung may invent a bespoke "abuse mechanism"**: reuse
of existing atoms is a pre-registered requirement, and the line closes with
**zero new Rust and zero new Python decision logic across all fifteen rungs.**

Four results the chapter turns on:

- **N4 — the finding in reverse:** what it takes to make the coupling work the
  right way again. A chapter on this subject needs its recovery rung and this
  line has one, measured on the same machinery.
- **R6/R7 — the barrier and the return:** a decision can be **entirely correct
  about controllability and still land on "stay,"** and a genuinely recovered
  trajectory is not protected from a later pull back. This is the chapter's
  most humane finding and it comes out of a value economy, not a narrative
  assumption.
- **U0–U2 — does the loop need intent? No.** And the sub-story is the book's
  method in miniature: scoping it properly surfaced that N1's own "deliberate
  two-faced presenter" rule was an **unconditional broadcast with no Argmax** —
  so N1 had never been a positive example of intent at all, and U1/U2 alone
  could only have tested structure. **U0 was added specifically to close that
  gap** — a glass-box, Argmax-scored example of concealment chosen because it
  serves a goal (r = 0.76 [0.762, 0.763], goal-blind control 100% degenerate) —
  *before* the intent question could honestly be asked. Then U1 and U2 show the
  identical pattern arising with no hidden true value and no chosen deception.
- **V1 — the credibility engine responds to what evidence reaches it, not to
  what happened.** Hold the harm identical and change only whether it leaves a
  discrete, victim-independent trace, and the outcome changes.

## `20 — The town`

Bigville: a village with an economy, a labour market, land, prices, a council,
a legislature, a court, bylaws, sentencing, a jail, a church, a school, a
newspaper, gossip, drama, and a hundred residents who each carry the dossier 16
affect machinery. **~202 documents**, and the chapter's job is to resist
inventorying them. Pick the spine: *what does a mind among minds compute that a
mind alone does not?*

- **Network effects as the answer.** Gossip and news are belief propagation;
  reputation and credibility are held quantities that respond to evidence
  reaching them; trust is a bond term. Ch. 19's network rungs run on exactly
  this machinery — the town is what makes that line's social embedding real
  rather than stipulated.
- **Desire paths** (merged in here; they were separately scoped early on): heterogeneous route
  valuation plus terrain wear gives accumulation and persistence, and desire
  paths are the **pre-registered falsifiable prediction**. This is
  population-scale Narrative Momentum, and it is the chapter that hands Part
  VII its empirical face.
- **The honest structural finding**, and the chapter's antagonist: violence is
  **15 rules across 4 seeds** and **all four declare `"productions": []`** — a
  richly modelled behaviour built as a bespoke subsystem where the substrate's
  own shape says it should be a *generated absence*. Ch. 21 is where that gets
  its general treatment; here it is a concrete, uncomfortable example.
- **Glass-box society** (`GLASS_BOX_SOCIETY_SCOPING.md`, `GLASS_BOX_R1`) and the
  prior-art survey (`PRIOR_ART_SOCIAL_EXPERIMENTS.md`,
  `SOCIETY_EXPERIMENTS_SURVEY.md`) are what keep this from reading as a game:
  the point of a town whose every decision is inspectable is that social
  findings become *mechanistically auditable* rather than merely simulated.

**Two constraints the chapter must respect.** Bigville is a **separate
repository** (`ozmalabs/bigville`) and its data is cited as external. And the
tree's only existing "narrativium" computation sums a per-tick term over ticks,
which paper 04 forbids — say so, in this chapter, where a reader can see why it
matters.

---

# Dossiers — how to believe any of it (sources 21–22 → chapters 15–16)

## `21 — A number where a shape belonged` (audit / design-rule chapter)

The most transferable single finding in the tree, and it was measured
independently in three unrelated embodiments in one week. The failure mode:
a subsystem invents a scalar knob instead of decoding against a codebook or
generating from a grammar — and the knob does not stay paid off ("1/n asserts
stationarity → declare a floor → a floor costs quiet regimes → declare a
surprise factor → surprise needs a reference → an EMA → the EMA needs a rate →
… 1/n. Each rate needs a rate.").

Enumerated, not characterised: 60 count-divided learners across 8 embodied
seeds, **none** inside the shape-matching faculties; 159 of 634 rule-carrying
seeds minting edges through zero Γ productions; a whole violence subsystem —
15 rules across 4 seeds — where all four declare `"productions": []`; 40
confirmed audit sites out of ~150 examined, with two sweep-reported findings
checked, found wrong, and kept in the record as the method's own error rate.

09's constants ledger is the same rule at the other end: *magic numbers fall
out of natural processes, they do not go in*, with the three-way distinction
that makes it operational — a constant that **fell out** is evidence; one
**put in as a constant** fails on distribution shift; one **put in as
architecture** (a signature exactly one rule is solely responsible for) is
silently unfalsifiable and is the worst of the three.

## `22 — Preregistration as an engineering method` (method chapter)

The credibility substrate for everything above, and genuinely unusual as a
publishable object: ~1,700 paired PREREG/RESULTS documents in which the
prediction is fixed before the measurement, and the standing rules that were
minted *by* being violated —

- **power the gate before the endgame**: deltas within ~3× the per-episode step
  are not results (minted by run 15 invalidating five of its own prior deltas);
- **a baseline is a list of node ids, never a count or a characterisation** — a
  count can be held while the thing it counts grows, and one status line was
  quoted without its condition for ten days before this was noticed;
- **an uncommitted runner means the result is not a result** (09's retraction 3);
- **positive-control the reader, not just the arm** — sixteen inert instruments
  in one arc, zero caught by a red gate;
- **synthetic-proven mechanism ≠ benchmark value, report both**;
- retract in place, keep the retraction, never silently edit.

Include the convergence audits (`THEORY_CONVERGENCE_AUDIT.md`,
`RAVANA_CONVERGENCE_AUDIT.md`) as the method's strongest use: the only evidence
that moves a cross-domain theory is the same structure being independently
re-derived by unrelated engineering that was not aiming at it.

---

# Dossier — the unbuilt frontier (source 23 → chapter 19)

`23 — A Constructive Realisation of Seldon Manifolds` is the obvious paper-05
analogue for paper 02, and it **cannot be written yet**. Reachability
`N_{W:G}(X,T) = μ_X(R^T_{W:G}(X))` needs a deformation metric over an
admissible action set. Both halves exist natively and **no code path joins
them**: `future_manifold.rs` audits one candidate trajectory against one target
tube (every call site is single-candidate), and `Substrate::admissible_moves`
enumerates a Γ-admissible weighted target set, used only for weighted selection
(`GRAPHIC_EQUALISATION_V22_SUBSTRATE_GAP.md` §4). Until composed, 02's central
claims are not false here — they are **not expressible**.

**This is the highest-leverage build in the tree for the paper programme**, and
it is small: compose the two, then 02 and 04 both acquire an empirical face.

---

