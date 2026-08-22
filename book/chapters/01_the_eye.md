# 1 · The Eye

*Draft. Sources: `docs/research/vision/THE_EYE.md`, `VISION_PROTOCOL.md`, and
the runs cited inline. Figures: EYE-1…EYE-8, C1…C5. Register per
`BOOK_VOICE.md`.*

---

Held still on an unchanging scene, this eye goes blind in about twenty ticks.
Not dimmed, not degraded — blind in a specific and measurable way: the count of
things it has to report falls to zero and stays there. Nothing is broken. Every
cell is alive and firing. There is simply nothing left for a detector of change
to detect, because nothing is changing.

**This chapter builds an eye whose every constant falls out of a measured
quantity rather than being chosen; whose motion is load-bearing rather than
decorative; and whose dimensions — time, depth, depth from many eyes — are
*discovered* from the relations between frames rather than stored as
coordinates.** It also builds one thing that does not work, and the reason it
does not work is arithmetic rather than tuning, which is why the line was
retired instead of retried.

That blindness is the right place to start, because it is not a flaw to be
engineered around. It is the constraint that explains the rest of the design.
An eye that only reports change must move, or it has nothing to say. Once it
moves, everything else in this chapter follows.

It also fixes what kind of thing this eye is. **It does not transmit an image.**
There is no absolute picture being sent onward and no privileged zero against
which brightness is measured. What the eye maintains is a relational state it
has constructed, and what it propagates is the *failure of that state to explain
the photons arriving* — the residual, again, at the front of the system rather
than the back. Reference here is **generated, not assumed**, and it is
continuously reconstructed; the eye's own resting level is derived per cell from
that cell's activity (§1.2) rather than imported from anywhere.

Which is why zero activity after adaptation is not a perceptual origin. It is a
legitimate value of an instantiated signal dimension, and the difference is not
pedantry: an eye with an absolute zero has somewhere to fall back to, and this
one does not. It has only what it currently predicts and what it currently
fails to predict.

---

## 1.1 What this is, and what it is not

This is an **eye**: a retina, an oculomotor system, and the early dimensional
inference an eye feeds. It is not a visual cortex.

It is also not a camera, and that is the more consequential of the two, because
nobody thinks a camera is controversial.

Machine vision begins from a rectangular array of RGB values, updated frame by
frame. Not because anyone argued for it — because that is how cameras work, how
every library expects to be handed a picture, and how it has been done for
decades. Nearly everything downstream exists to recover structure from that
format: fixed edge kernels, corner detectors, blurs, all of it reconstructing
what the format discarded on the way in.

This eye was built by refusing that. The substrate has one loop — decode against
what you hold, act on the residual — and the constraint applied here was that
sight must go through it rather than around it. What survived was not a better
array of pixels. It was integer photon packets with wavelengths; populations of
receptors, each with its own adaptation state; opponent channels synthesised
only once every receptor in a column has settled; and an output that reports
*change* rather than a picture. The earlier RGB eye still exists in the tree,
marked deprecated, for callers that need the old behaviour.

That was not an improvement to the old eye. It is a different object, and the
difference only became visible once the format was no longer allowed to be
assumed.

The scoping matters more than it might appear, and it is worth being blunt
about why. "Vision" is a word that promises the whole visual system, and a
chapter promising that would have to treat this chapter's largest negative
result as a missing section — an embarrassment, a gap where the good part
should be. Scoped as an organ, the same result sits *inside* the chapter as
what it actually is: a bounded finding about which mechanisms can and cannot
produce form selectivity from this input, established across five
pre-registered attempts and closed with a measured cause.

The founding thesis of the work was that *a genuine eye implementation that
works is deliverable and valuable by itself*. This is that, and the boundary is
stated in advance rather than discovered when the reader notices something
missing.

Two consequences of the scoping run through everything below. First, everything
the eye does stays inside the integer, in-frame class: an observed frame's
coordinates are the lattice, and the real-valued structures — a rotation by a
real angle, a scale ratio, continuous perspective — live in the maps *between*
frames.¹ Second, where a continuous structure genuinely would be needed, it is
named as deferred rather than faked.

> ¹ This is the frame invariant, which chapter 2 states properly. For now the
> working form is enough: *is this number IN a frame, or BETWEEN two?* In-frame
> ⇒ integer. Between ⇒ it may be real.

---

## 1.2 Every constant falls out

The retina has a handful of numbers in it. Not one of them was chosen to hit a
target.

That claim is easy to make and easy to fake, so it is worth fixing what would
make it false before looking at what makes it true. There are three categories
of constant in a system like this, and **only the first is evidence**:

1. A constant that **fell out** of a natural process — you can point at the
   process, and the number is what it already implied.
2. A constant that was **put in as a constant** — a value someone picked
   because it worked. These fail on distribution shift, and they fail
   loudly, which at least makes them findable.
3. A constant that was **put in as architecture** — a signature that exactly
   one rule is solely responsible for producing. This is the worst of the
   three, because it is silently unfalsifiable: the system reproduces the
   published number, and it reproduces it for no reason but that a rule was
   written to.

The eye contains examples of all three. Category 1 is what follows in this
section. Category 2 appears once, was measured, and was retracted (§1.8).
Category 3 is a hazard this chapter returns to twice, because it is the failure
mode that looks most like success.

### The receptor takes a logarithm, and invariance comes free

Weber's law says that the just-noticeable difference in a stimulus is
proportional to the stimulus. Which is to say: what perception tracks is a
*ratio*, and a ratio under a logarithm is a difference. So a receptor that
takes the log of its photon count is not a receptor with a nonlinearity added
to it — it is a receptor that has been told what Weber's law already says.

The consequence is illumination invariance, and it is worth being precise about
what "invariance" is measured against. Take a reference illumination and two others,
one and two decades brighter; measure how much the eye's response pattern
differs between them; and
compare that difference against the difference between two genuinely *different
scenes* at the same illumination. That second quantity is the floor — the
difference the measure reports when there is a real difference to report.

The log receptor sits at **0.44% of that floor**, against a pre-registered
threshold of 10%. The linear receptor sits at **100%** — a total mismatch. Both
arms, twelve seeds, one run [EYE-2].

The second number is doing more work than the first. A measure reporting
near-zero for the log arm alone would be consistent with invariance and equally
consistent with the measure being inert — with an instrument that reports
near-zero for everything put in front of it. The gate was written as a
conjunction for exactly that reason: the log arm must fall below the threshold
*and* the linear arm must rise above it. It is the linear arm that turns the
first number into a result.

The same fact appears a second way, on its own axes. Plot drive against the
logarithm of intensity across four decades and fit a slope. The prediction,
stated before the run, was 1.000 ± 0.05. The measurement is **0.9991**
[EYE-3]. And the per-decade steps — the drive added by each tenfold increase in
light — are 2.2936, 2.3017, 2.3025, 2.3026, converging on ln 10 = 2.3026. The
linear receptor's slope on the same axes is 91,150; it is not encoding a ratio
at all.

Nothing here was fitted. The receptor was given a logarithm because Weber's law
*is* a logarithm; the slope of 0.9991 is what that already implied, measured
afterwards to check that it was true.

### The threshold comes from the noise floor

A change detector needs to know what counts as a change. The obvious move is to
pick a threshold, tune it until the output looks right, and move on — a
category-2 constant, with all the fragility that implies.

The eye instead reads its threshold off the physics of light. Photon arrival is
a counting process, so its noise scales as the square root of the count: at
intensity `I`, fluctuations of order `√(I/n_max)` are what an unchanging world
already produces. A cell that fires when `|ΔI|` exceeds that is firing when the
change exceeds what noise alone would explain — no more, and no less.

There is a small gift in the composition. The detector runs on the *log* signal,
and a threshold on a log difference is a threshold on a ratio. So the change
detector is Weber-normalised without anyone normalising it: bright regions and
dim regions get the same fractional sensitivity, because that is what taking the
log already did.

### The setpoint comes from the cell itself

Each cell adapts toward a target. The obvious move is to import one from the
literature, and that is precisely what was tried, and it is precisely what
failed — see §1.8, where a value imported from a model whose frame this eye does
not share killed cells in two layers before it was caught.

The replacement derives the target per cell from that cell's *own* endogenous
activity: whatever it does when nothing is being shown to it is what it adapts
back toward. The measured value averages 0.146 across the population.

Two honest notes about that number, both of which belong in the text rather than
a footnote. It is individual *by construction* — each cell derives its own — but
near-uniform *in fact*, because every cell in this retina sees the same wave
field. That is a real limitation of the current instrument, not a property of the
principle. And it will reappear in §1.4 as one of two independently derived
timescales, which is the point at which it stops being a housekeeping parameter
and becomes evidence.

### Structure before sight: the waves

Before an eye has ever seen anything, a real retina is not quiet. It generates
travelling waves of spontaneous activity, and those waves are thought to be how
the early visual system organises itself in the absence of input.

This retina does the same, from ignition and propagation rules with no imposed
geometry — and the structure is measurable rather than asserted: entropy of
**0.195** against **0.000** for the same random number stream without the
propagation rules. Same randomness, different structure; the difference is the
rules.

What the waves *are*, measured properly, turns out to be the most consequential
fact in this chapter, and it is deferred to §1.5 because it only becomes
consequential once something tries to learn from them.

### Centre-surround, from a zero start

Lateral inhibition — a centre that excites and a surround that suppresses — is
the retina's signature computation, and it is old enough and canonical enough
that building one in would be entirely unremarkable.

It was not built in. The lateral gains start at **zero**, and what develops
under competition among cells reaches a centre-surround index of **1.0839**
across eight seeds, spread 4.3 × 10⁻³ — where 0 is a pure centre with no
surround at all and 1.0 is a balanced difference-of-Gaussians. It arrives at
**108.4%** of that range [EYE-6].

Two published readings of centre-surround then come out of the same run, and
neither is a parameter of this retina.

**Miller's reading** — that the ON-to-ON and ON-to-OFF spatial dependences
should differ — holds: σ_ON,ON = 1.627 against σ_ON,OFF = 3.264, a ratio of
2.007, difference 1.637 with interval [1.508, 1.767].

**Atick and Redlich's predictive-coding account** makes a sharper prediction,
because it is about how the surround should *change*: as the signal-to-noise
ratio falls, the total gain should weaken and the surround should broaden. Both
directions hold. Replay the same movie at two noise levels and total gain falls
from 0.7748 to 0.6447, while the far-ring share rises from 0.3332 to 0.3932.
The theory said which way both would move, in advance, and neither is something
this retina can be turned to.

And before any of that was believed, the instrument was checked. The run
includes an analytic control split that *must* score exactly zero if the
measure is sound. It scores **4.4 × 10⁻¹⁶** across eight seeds — floating-point
zero. The floor was measured, not assumed, which given §1.8's ledger was not a
formality.

---

## 1.3 The eye has to move

Return to the blindness.

A detector that reports only change is, on a static scene, a detector that
reports nothing. This is not a design defect to be patched at the next layer;
it is what "change detector" means. There are two ways out. Either the scene
moves, or the eye does.

Real eyes take the second option, continuously and involuntarily. Even during
what feels like steady fixation, the eye drifts — a small, meandering,
unwilled motion that keeps the retinal image sliding across the receptors. Its
statistics are known: the drift is *persistent* at short timescales and
*anti-persistent* at long ones, so it explores locally while staying put
globally. Engbert's measurements put the two scaling exponents around 1.38 and
0.79.

This eye's drift is a self-avoiding walk, and it reproduces the crossover:
short-lag exponent **1.1553** [1.1445, 1.1662], long-lag **0.7590** [0.7244,
0.7935] [EYE-4]. Above one at short lag, below one at long lag, which is the
shape of the published result.

That is a reproduction, and reproductions are cheap. The figure earns its place
through what sits underneath it: an **ablation**. Remove the self-avoiding term
and the short-lag exponent barely moves — 1.1553 to 1.1944 — while the long-lag
exponent crosses back over one, 0.7590 to **1.1301**. Without self-avoidance the
walk stops anti-correlating at long lag and becomes ordinary diffusion. The
crossover is carried by that term specifically.

### The failure mode is the real tell

Normal function is cheap to fake. A mechanism that produces the right output
under ordinary conditions has told you very little, because a great many
mechanisms produce the right output under ordinary conditions. A *failure mode*
is a claim about what a mechanism drives — about what stops working when you
remove it, and in what specific way.

So: stabilise the image. Cancel the drift, so the retinal image no longer
slides. In a real visual system the result is Troxler fading — a stabilised
image fades from perception within seconds, and the effect is one of the more
robust demonstrations in the field.

It replicates: eight seeds out of eight, sign test p = 0.0078, contrast
difference **0.1338** [0.1301, 0.1383] between the drifting and stabilised arms
[EYE-1]. The drifting arm keeps most of its contrast — 0.131 against 0.167 at the
start. The stabilised arm falls to 0.0003.

The result is in the *content*, not the p-value.

**First, what it fades to.** The stabilised sheet's mean response converges on
its own endogenous setpoint — the μ_endo of §1.2, the value each cell derived
from itself. Contrast does not decay because the signal is being lost; contrast
goes to zero because every cell arrives at its own resting value and the sheet
becomes *uniform*. A uniform sheet has no contrast. The fade is a consequence of
the adaptation mechanism reaching its target, not a decay term someone added.

That is perception as an equalisation process rather than a reconstruction. The
sheet is not producing a picture and then losing it; it is holding a relational
state against incoming photon relations, and when those relations stop changing
the state has nothing left to correct. Motion, edges, occlusion and novelty are
then all the same kind of thing — graph change — rather than features computed
frame by frame.

**Second, the control.** All of that would be equally consistent with the sheet
simply dying. It does not: 100% of cells in the stabilised arm are alive at the
end, by the run's own liveness criterion. A dead sheet cannot counterfeit a fade
to setpoint, and this is the check that separates the two.

**Third, and this is the part that makes it evidence rather than a
demonstration**: the fade requires two timescales, and they were derived
independently and never tuned against each other. The drift timescale, τ ≈ 3,
comes out of the self-avoiding walk. The adaptation timescale, τ ≈ 160, comes
out of the endogenous setpoint. They differ by a factor of 53. Nobody chose that
ratio; it is what two separately motivated mechanisms happened to imply, and the
fade exists in the gap between them.

One honest bound. This fade is *retinal*. The biological locus of Troxler
fading is multi-level — retinal transient and sustained channels plus cortical
filling-in — and this eye reproduces one contribution, not the whole phenomenon.
What that makes the eye is an *instrument* for weighting those contributions
against each other, which is a more useful thing to have than a claim about
which one wins.

### A second failure mode, and an independent convergence

Deprivation gives another. Rearing under diffuse, unstructured light is worse
for the developing visual system than rearing in the dark — a result that
sounds backwards until you have the mechanism. It reproduces here (−0.1458), and
the mechanism is stated rather than hand-waved: the learning rule converges
toward the leading principal component of whatever it is shown, and unstructured
noise has no leading principal component. Structure-free drive does not merely
fail to build structure; it actively dissolves structure that is already there.

And a convergence from outside this project, which is worth a paragraph because
it arrived independently. Event cameras — sensors that report per-pixel
brightness changes rather than frames — hit exactly the blindness this chapter
opened with, and the field's answer was to *move the sensor*: a wedge prism, a
deliberate jitter, anything to generate events on a static scene. An
engineering community with no interest in fixational drift reinvented the
microsaccade because the constraint made them. That is the strongest kind of
external support: not agreement with the conclusion, but independent arrival at
the same necessity.

Two existing figures make the point directly. Held on an unchanging scene, the
change count falls from 300 to **0** by tick 20 [C4]. And the work the eye does
per tick tracks surprise: it drains to nothing on a static scene, rises through
motion, drains again [C3]. Compute follows change, because change is all there
is to compute.

---

## 1.4 The dimensions of sight are discovered

Here the chapter turns from a retina to what a retina can be made to yield.

The claim is that time, depth, and depth-from-many-eyes are not coordinates this
eye was given. They are **inferred dimensions** — the eye mints them when the
data cannot be explained without them, and refuses to mint them when it can.

The refusals are the evidence. A mechanism that finds depth in a depth-ful scene
has demonstrated very little if it also finds depth in a flat one.

### Time is the exponent of a transition

Take a moving pattern across several frames. If a single transformation carries
frame *t* to frame *t+1*, and applying it again gives *t+2*, and again *t+3*,
then the whole sequence is an *orbit*: one generator, applied a whole number of
times. The index — how many times you applied it — is time.

Which locates time precisely: **it is not in any frame.** No single snapshot
contains it. It lives in the map between frames, and it is an integer because
applying a transformation a fractional number of times is not something the
observation supports.

It is worth being blunt about what that means, because chapter 14 makes it a
commitment and this is the measurement behind it. **The eye was not given time.
It inferred one.** No observation it received carried a temporal coordinate —
succession is a relation *between* observations, and a relation between things
is not a property of any one of them. So the axis had to be constructed, and the
machinery that constructed it was not a clock or a timer: it was the eye's
general dimension-inference machinery, the same operation that mints depth.

Which orders two capabilities that are usually treated as separate. A system
that cannot infer does not have a slow or poor sense of time. It has none —
succession happens to it, and nothing represents that succession. Time is
downstream of inference, and this experiment is where that stops being a
philosophical position and becomes a thing you can switch off and measure: mint
with ordered frames, nothing with shuffled ones.

Measured, ordered motion mints a time axis and compresses: description length
28 → 7. The minted axis then predicts a frame the eye was never shown —
applying the generator seven times reproduces the seventh frame exactly.

And the refusals:

- **Shuffled frames mint nothing**, 0 out of 400 at the longest window. Without
  temporal order there is no single generator, and the eye does not invent one.
- **Accelerating motion** yields no time axis either — and this is the subtler
  case. The frames *are* pairwise translates; each one is a shift of the last.
  But they are not a single generator applied repeatedly, because the shift
  changes. The eye correctly declines to call a sequence of different steps one
  step repeated.

### Depth is a residual nothing flat explains

Drag a scene with real depth past a moving eye and near surfaces sweep faster
than far ones. No single flat transformation explains the result — whatever
generator accounts for the near surface leaves the far one wrong, and vice
versa. That unexplained remainder *is* depth: the eye orders the field by
velocity and mints a depth dimension, compressing 36 → 13 [EYE-5].

The control is what matters. **A flat scene mints nothing.** So does a
multi-coloured scene at a single velocity — many regions, many distinct
surfaces, no depth. Depth comes from velocity *variation*, never from the mere
presence of separable regions. A flat plane that minted a depth dimension would
be hallucinating, and this is the measurement that says it doesn't.

Four frozen multi-depth scenes give four different, correct orderings. 400
shuffles of a depth-ful scene give zero spurious mints. And the minted dimension
predicts an unseen view, each surface moving at its own velocity.

This is *monocular* depth. It needs one moving eye, which this eye has. It needs
no second eye and no cortex, because the three-dimensional world was never in a
still image to begin with — it is in the relations between frames.

### Eyes and ticks are the same resource

Now the result that generalised further than it was built to.

Take the same operation and feed it N eyes at a single instant instead of one
eye across ticks. The unchanged term mints the same dimension, in the same
order. **The source diff is empty** — not "a small change", not "a new code
path": nothing was modified, and stereo works.

That is a claim about what a frame *is*. An eye is a spatial viewpoint; a tick
is a temporal one; both are frames to be related, and the machinery that relates
frames does not care which kind it was handed.

The controls survive the transfer intact. One disparity across many surfaces
mints nothing, at N=2 and at N=3. Zero disparity — a scene at infinity — mints
nothing. 400 shuffles mint nothing. And two further properties fall out:

- **It was built for N, never for 2.** The eye count is read from the graph
  itself; there is no literal `2` anywhere in the path. This is not tidiness. A
  hardcoded count is a constant in the architecture — a category-3 constant from
  §1.2 — and the way to prove it is absent is to run at N=3 and check it works.
  It does. And **N=3 rejects configurations N=2 accepts**, which is what more
  baselines are *for*.
- **Motion and stereo are held additively, not chosen between.** They are two
  generators for one dimension. Stereo grounds in a single tick where motion
  needs six — depth *now*, from one instant — and more baselines make it more
  precise. You never pick parallax or stereopsis; you ground one dimension with
  both, weighted by how much evidence each has.

That last point is a principle this eye embodies throughout, and it is worth
naming: **for every "which mechanism?" question here, the answer has been
both.** Motion and stereo. Retinal and cortical. Transient and sustained. What
governs is consistency among co-present mechanisms, not selection of a single
winner.

---

## 1.5 The cortex: a diagnosed dead end

Everything so far worked. This did not, and the difference between "did not
work" and "does not work, for this reason" is the whole content of this section.

The goal was orientation selectivity — cells that respond to edges at a
particular angle, the canonical first step of visual cortex — learned from the
retinal waves of §1.2 by Hebbian competition. Five pre-registered rungs.

The headline result is null: the effect measures **−0.0118**, with an interval
of [−0.0234, −0.0003] that excludes the smallest effect worth caring about by a
factor of 2.5. Not "we could not detect it." The interval sits on the wrong
side of zero.

Five ways a null like that can be an artefact were each closed by measurement:
a blind probe, a dead arm, an inherited floor, an inert manipulation, and
drive being mistaken for selectivity. What remains is a real null, and then the
question that matters: *why*.

### The waves are not what three rungs assumed

Three rungs had shared a premise — that the wave ensemble carries no
orientation, so no orientation can be learned from it. Measured properly, that
premise is half true, and the half that is false relocates the problem entirely
[EYE-7].

**Globally, the ensemble is isotropic**, and this was measured for the first
time rather than assumed: orientation anisotropy of **0.021** [0.014, 0.029],
sitting essentially on the floor set by a control of isotropic disks (0.0008)
and nowhere near the ceiling set by oriented bars (0.953). No orientation is
preferred across the field as a whole. That half is confirmed.

**Locally, every front is oriented.** Coherence within a single receptive field
measures **0.781** [0.773, 0.789] — far above the disks floor of 0.464 and most
of the way to the bars ideal of 1.0. Of course it is: the waves are travelling
*fronts*, and a front has a direction where it passes.

So the structure is present. The inference three rungs had drawn — no
orientation in the input, therefore none can be learned — does not follow.

### The reason is arithmetic

The learning rule converges to the leading eigenvector of the input covariance.
So the question "can this rule learn orientation from these waves?" has an
answer that is computable rather than debatable: look at the eigenvector.

It is a blob. Alignment with the DC component: **0.983**. Orientation index:
**0.086** [0.066, 0.106] [EYE-8]. The thing the rule will converge to is a
centre-weighted, sign-uniform blob carrying almost no orientation at all.

And underneath it, a tie. The second and third eigenvalues have ratio
**1.0907** [1.0668, 1.1145] — near-degenerate. Remove the DC component and what
remains is two directions of nearly equal weight, so which one a cell settles
into is a coin flip. Not a weak preference. A coin flip.

That is arithmetic, not a tuning failure. The rule fits second-order statistics;
the orientation in these waves is local and sign-varying and is not *in* the
second-order statistics. No learning rate rescues it, because no learning rate
changes what the leading eigenvector is.

To be sure the failure belonged to the input rather than to a missing piece, the
missing piece was **built** — the lateral layer and settling loop of the
published model this line was following, in rules, with no new constants — and
tested. There is no learning rate at which that rule is both convergent and
load-bearing: where it settles it does nothing, and where it does something it
does not settle. Going back to the primary source closed it: the published
model's orientation comes from neither its stimulus nor its learning rule but
from its settling steps, and even those are a tolerance criterion rather than a
demonstrated convergence.

### What the null redirected the work to

Here is the part that makes this a finding rather than a defeat.

The dead end was specifically the dead end of *static, second-order,
single-frame* vision — of trying to extract form from what one image contains.
And the three-dimensional world was never in one image. It is in the relations
*between* frames, and those this substrate can discover, which is exactly what
§1.4 measured.

Biology, read after rather than before, agrees: the motion pathway is early and
central, and the static form pathway was the wrong place for a from-scratch
system to start.

A null that relocates the work is worth more than a pass that confirms a plan.
This one cost five rungs and bought a redirection.

---

## 1.6 What it costs to run

An eye that cannot run at a useful size is a demonstration rather than an organ,
so the cost was measured rather than estimated.

The headline is that **the wall is the boundary, not the arithmetic**. Between
75% and 82% of a tick was spent crossing between the host language and the
engine — marshalling, not computing. The engine itself accounted for 18–25%.
Bulking the boundary gave 5.06×, and pushing predicates down into the engine
gave a further 4.29× on the dominant rule. A foveal sheet of roughly 150,000
cells went from 1317 ms per tick to **137.8 ms**.

Two things fall out of that, and both are more useful than the speedup.

**A GPU cannot help here.** It would target at most a quarter of the budget,
and the part it would target is enumeration over a graph rather than dense
float arithmetic. This is not a claim that the work is unaccelerable; it is a
claim about where the time actually is, which is the question people usually
skip.

**The scaling shape matters more than the constant.** Fitted against the number
of cells, the graph path grows with exponent 1.838 and the accelerated path with
**1.072** [C1]. The claim is the slope: the difference between a cost growing
faster than the retina and one growing with it.

And a separate measurement that reads as a small win and is not [C2]. Cost
against cells looks similar with and without pruning — 2.032 against 1.825. But
cost against *tick index*, at fixed size, does not: unpruned, each tick costs
more than the last, cumulative exponent 2.266; pruned, it is flat at 0.775. The
first panel is a modest improvement. The second is the difference between an eye
that can look for a long time and one that cannot.

One ceiling stands regardless of engineering, and it belongs here rather than in
a footnote. The settling operator used by cortical-sheet models has a spectral
radius that approaches one as the sheet grows, so a large sheet settles
arbitrarily slowly no matter how fast each step is made. That is a property of
the operator, not of this implementation — and notably, the published model that
uses it never demonstrated convergence at scale either.

---

## 1.7 Coda: a law of physics from pixels

What an eye is *for* is not seeing. It is finding out what is out there.

Point this eye at an object falling. Track it. The generic order-*N* machinery
asks whether the trajectory is explained by a constant, or a constant rate of
change, or a constant rate of change of that — and mints the lowest order that
fits. On a falling object it mints **order 2: uniform acceleration**, with no
gravitational constant anywhere in the seed. The eye is not told that things
fall. It is shown things falling, and the law is the shortest description of
what it saw.

The witness for "order *k* genuinely fits" is worth its own paragraph, because
the first version of it was wrong in an instructive way. The original test was
exact finite-difference equality — the *k*-th difference is exactly constant —
which is correct on synthetic data and floors immediately on real video, where
nothing is ever exactly anything. The replacement is a description-length
comparison: a robust median plus its residual must cost *strictly fewer bits*
than the raw stream. That closed the gap between synthetic and real footage, and
it is the same criterion the whole substrate uses for deciding that something is
real rather than noise.

Which is a principle worth stating plainly, because it governs more than this
coda: **noise does not exist — there are only signals you have not grounded.**
The discrimination is never "is this signal or noise", a question with no
observer-independent answer. It is "does treating it as structure cost fewer
bits than treating it as data", a question with a computable one. What does not
compress is grounded at enumeration, provisionally, and left alone. Nothing is
ever asserted to be incompressible.

The line continues toward mass: a robot that pushes objects discovers inertial
mass as impulse over velocity change, watches objects fall under one constant,
and should find the two quantities are the same thing seen through two different
frames — a motor frame and a perceptual one. That is the frame invariant in its
most physical form, and it is in progress rather than landed.

---

## 1.8 The ledger

Five retractions, each with the measurement that forced it. They are here rather
than in an appendix because they are the reason to believe the rest.

1. **"Biology emerged" (stage 1).** It did not. The kernels were designed and
   the measure that certified them passed noise. Both halves wrong at once,
   which is the combination that survives longest.
2. **The deprivation asymmetry (rung 1).** Confounded. What was measured was
   noise disrupting a running wave program, not experience degrading tuning. It
   survived six attempts to break it — because all six shared one design error,
   which is the thing repetition cannot catch.
3. **The experience headline (rung 2).** On the real source, the "normal"
   condition *reverses* below the dark condition. And the runner that produced
   the original number was never committed, so the number cannot be attributed
   to any code. **An uncommitted runner means the result is not a result** —
   this is where that rule comes from.
4. **The drift was decorative.** It reproduced Engbert's published signature to
   two decimal places while driving *nothing*: its only consumer was the ruler
   that measured it. The number was right and meant nothing, until it was wired
   into the image — after which everything in §1.3 and §1.4 depended on it. This
   is the chapter's antagonist, and it is a category-3 constant in the wild: a
   signature that exactly one rule was solely responsible for.
5. **An imported setpoint.** A value of 0.024, taken from a published model
   whose frame this eye does not share, killed cells in two layers. Replaced by
   the derived per-cell setpoint of §1.2 — which is how μ_endo came to exist at
   all.

And the finding underneath the five, which generalises past vision entirely.
Sixteen instruments in this arc turned out to be inert: a measure that passed
noise; a dead cell scoring a flawless floor; a stocked library reading empty off
a wrong dictionary key; a walk whose only consumer was its ruler; a benchmark
with ten tests that had never once run.

**Not one of the sixteen was caught by a test going red.** Every one was caught
by somebody looking at a result and finding it too clean. Which is the working
discipline this chapter leaves with: verify the fact before you fix the gate;
positive-control the reader and not only the arm; and believe a claim only where
it fails in the places it must.

---

## 1.9 What would falsify this

Stated as specifically as the results allow.

- **The constants.** If a measured constant here can be shown to have been
  chosen — if some value can be moved and the published number recovered by
  retuning — that constant moves from category 1 to category 2 and the section
  it appears in weakens accordingly. The invariance and Weber results are the
  most exposed, since both rest on a receptor choice made in advance.
- **The drift.** If the crossover survives ablation of the self-avoiding term
  in a corrected implementation, then the term is not what carries it and §1.3's
  central claim fails.
- **The dimensions.** A single case where a flat scene, a single-velocity
  multi-colour scene, a zero-disparity scene, or a shuffled sequence mints a
  dimension would break §1.4 — not weaken it. The claims there are refusals, and
  refusals are falsified by one counterexample.
- **The stereo generalisation.** If the empty source diff turns out to depend on
  a shared assumption specific to these scene generators, "eyes and ticks are
  the same resource" narrows to "eyes and ticks are the same resource for scenes
  like these", which is a much smaller claim.
- **The cortex null.** If some rule in the Hebbian class produces orientation
  selectivity from a wave ensemble with this covariance structure, then §1.5's
  cause is wrong even though its measurement stands. The cause is the claim, and
  it is the falsifiable part.
- **The Troxler result.** If the fade can be produced with the two timescales
  collapsed to one, the "independently derived, never tuned to each other"
  argument fails and the result drops back to a reproduction.

None of these would be surprising to find. The retina here is small, its
population is uniform in fact if not by construction, and its input is
synthetic in every experiment except the ones that say otherwise.

---

*Ends. Next: chapter 2, the frame invariant — which §1.1's footnote deferred,
and which §1.4 has now spent an entire section demonstrating.*
