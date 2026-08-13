# How coarse is coarse, really? — population-distribution grounding for the
# causal-strength quantization resolution parameter

**Status: RESEARCH SPIKE. No code, no seeds, no tests, no schema changes in
this document.** Exactly one file was added to the tree (this one). This is
not a PREREG for an experiment run in this rung — no live measurement is
taken here, nothing in the substrate is touched — so it does not carry a
separate `_PREREG.md` the way `CAN_BELIEF_QUANTIZATION_RESULTS.md` does; it
is a pure literature-grounding document, matching the register of
`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` (no code, no seeds, literature
checked not recalled) but feeding a *future* rung's PREREG rather than
reporting on one already run.

**Charter, verbatim, from the project's creator**, quoted in full because it
sets the exact scope of what this document is and is not allowed to
conclude:

> "quantisation was always dynamic. - but I would be interested to see if we
> can get an understanding of how this exists across the population so we
> can have an idea for the distribution - this would help shape the
> prereg"

Read precisely: the crossover-point experiment itself (where coarse-vs-fine
resolution stops being efficient and starts costing representational
accuracy, as N/required-distinctions grows) is **not** designed here. This
document's only job is to find out what a REALISTIC range of human
reasoning-granularity variation looks like, quantitatively, from real
literature, so that future PREREG can pick resolution-level test parameters
that are grounded rather than invented. Where the literature does not
support a specific number, this document says so and reports the
best-justified range with its reasoning shown, per this project's own
standing "power the gate before the endgame" / "synthetic-proven mechanism ≠
benchmark value, report both" house rules (`CLAUDE.md`, and
`CAN_BELIEF_QUANTIZATION_RESULTS.md` throughout).

**Confidence convention**, matching the prior two spikes: claims from a
source actually fetched and read carry that source's citation with the
numbers reported. Where only a search-result synthesis was reachable
(WebFetch blocked by a paywall, cert failure, or binary-PDF non-extraction —
all of which happened repeatedly during this research and are named
explicitly below rather than silently worked around), that is flagged
`[search-synthesis only]` and downgraded accordingly, never dressed up as a
direct read.

---

## 0. The headline answer, up front

**No existing psychometric instrument directly measures "how many
distinguishable causal-strength bins a person spontaneously uses."** That
construct does not have a dedicated literature. But five adjacent
literatures were checked, each holds up as real, and together they
triangulate a range rather than handing over a single number:

1. **CRT (Frederick 2005) has the best real population data of the five** —
   multiple large samples (N=3,428 combined across 35 studies; N=2,137;
   N=142) with actual score distributions reported, not just group-mean
   comparisons — but it is a 0–3 ordinal *pass/fail-per-item* score, not a
   resolution/bin-count measure, and its own distribution shape is **not
   stable across populations**: it swings from floor-heavy (mode = 0,
   general/naive population) to ceiling-heavy (mode = 3, educated/exposed
   population) depending on prior exposure and education, a >3× swing in
   mean score across real subgroups of the *same* instrument (§2).
2. **NCS (Cacioppo & Petty 1982) is a genuine miss for this purpose, and
   this document says so rather than forcing it** — real, high reliability
   (α≈0.90–0.94), but **no published population-norm table (no mean, no SD,
   no percentiles) was found anywhere in the literature searched** — it is
   used exclusively as a within-study continuous individual-difference
   measure, and it measures *preference* for effortful thought, not
   *representational capacity* (§3).
3. **Emotional granularity (Barrett et al.) is the closest CONSTRUCT match**
   (differentiated vs. coarse categorical representation of a graded
   internal space is exactly this project's target shape) **and real
   quantitative distributional numbers exist** — but from small
   experience-sampling studies (N≈40–150), reported as an ICC-based index
   whose population spread is real and substantial (one dataset: mean
   ICC-r −0.59, SD 0.27, 10th/90th percentile −0.91/−0.24) but is not
   itself expressed as a bin count (§4).
4. **Numeracy scales (Berlin Numeracy Test, Lipkus) are the sharpest
   methodological lesson in this whole document**: the SAME underlying
   construct, measured by two different item sets, produces two wildly
   different apparent "population distributions" — near-uniform spread
   across 0–4 (BNT, deliberately calibrated) vs. severe ceiling/negative
   skew with the *lowest observed score already at 45% correct* (Lipkus,
   miscalibrated for educated samples) — i.e. **the apparent shape of a
   "resolution" distribution is, empirically, largely an artifact of where
   the test's own difficulty is pitched, not a fixed fact about the
   population being measured** (§5).
5. **The single most directly relevant finding is Miller (1956) + Preston &
   Colman (2000), independently converging** — real, replicated,
   quantitative literature on exactly "how many discriminable levels can a
   person reliably use on one dimension": Miller's absolute-judgment
   channel-capacity result (≈2–3 bits ≈ 4–8 alternatives) and Preston &
   Colman's empirical optimum for Likert-type reliability/validity/
   discriminating-power (best psychometrics at 7 categories, degrading past
   ~10) land in the **same narrow band, from two unrelated methodologies
   three decades apart** (§6).
6. **Synthesis (§7)**: the honest range this document can defend, with its
   reasoning shown rather than invented, is **roughly 3–9 reliably
   discriminable levels for a single individual on a single occasion along
   one dimension**, centered near 7, PLUS large between-person/between-
   context variation on top of that (CRT's >3× exposure-driven swing; the
   near-full-range ICC spread in emotional granularity) that a fixed
   per-person bin count would not capture. §8 turns this into concrete
   PREREG parameters.

---

## 1. Method

1. `CLAUDE.md` read in full (already available in this session's context),
   specifically "BASE-AS-DIMENSION + the frame/continuum invariant" and
   "SHAPES, NOT NUMBERS."
2. `docs/research/engine_substrate/CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`
   read in full — the prior spike establishing causal strength as a
   quantized `DimensionGenerator` dimension.
3. `docs/research/engine_substrate/CAN_BELIEF_QUANTIZATION_RESULTS.md` (and
   noted its `_PREREG.md` sibling) read in full — the live 2×3 factorial
   that measured coarse-vs-fine representational error and basin structure
   directly on this project's own CAN engine, and the honest null it
   reported (the naive "coarse → fewer discriminable states" intuition
   reversed at small-to-medium N on that specific design).
4. Five literatures checked via WebSearch + WebFetch, per the charter's own
   five numbered research questions (§2–6 below map 1:1 onto them).
   WebFetch failures are named explicitly where they occurred (several
   ScienceDirect/PubMed/Wiley/PNAS pages 403'd or cert-failed; several PDFs
   returned only binary stream data, not extractable text) rather than
   silently substituted with unlabelled search synthesis.
5. No live measurement, no code, no seed data. This document's own
   contribution is the synthesis in §7–8, not a result lifted from a single
   citable source.

---

## 2. Q1 — Cognitive Reflection Test (CRT) population score distributions

### 2.1 The original instrument and its best-attested combined-sample number

Frederick, "Cognitive Reflection and Decision Making" (*Journal of Economic
Perspectives* 19(4), 2005) is the 3-item test (bat-and-ball, widgets,
lily-pads), each item cueing a fast, wrong, intuitive answer that must be
overridden. The most-repeated summary statistic in the subsequent literature
— found consistently across the familiarity/exposure papers checked below —
is a **combined sample of 3,428 participants across 35 separate studies**,
mean score **1.24** (range of individual study means **0.57 to 2.18**), with
**17% of participants answering all three correctly**. `[medium-high
confidence — consistent figure across two independently fetched PMC
sources, not the original 2005 paper's own text directly]`.

### 2.2 Real, large-sample distributions with per-score breakdowns

Two sources were fetched directly (not search-synthesis) and yielded actual
per-score percentages, not just means:

- **Stieger & Reips (2016), fetched via PMC5018679** ("A limitation of the
  Cognitive Reflection Test: familiarity"), **N = 2,137** (analyzable
  sample; 2,272 recruited, age-stratified, M age 39.8, SD 17.7, 56.6%
  women). Score by prior-exposure status: **naïve participants M = 1.21, SD
  = 1.06**; **experienced participants M = 1.65, SD = 1.11** (Cohen's d =
  0.41). By education × exposure: university-degree/experienced M = 1.99,
  SD = 0.64 (near-ceiling, low variance); university-degree/naïve M = 1.55,
  SD = 1.07; apprenticeship/naïve M = 1.06, SD = 1.03 (near-floor). **The
  paper's own headline finding, stated as a distributional fact**:
  approximately **one-third of higher-educated experienced participants
  scored 3/3, while one-third of lower-educated naïve participants scored
  0/3** — i.e. the same 3-item instrument produces distributions ranging
  from strongly floor-heavy to strongly ceiling-heavy depending on which
  real subgroup is sampled, not one stable population shape.
- **Haigh (2016), N = 142, via search-result synthesis of the same PMC
  source** `[search-synthesis, not independently re-verified against
  Haigh's own primary text]`: overall M = 1.93, SD = 1.17, with per-score
  percentages **0: 19.0%, 1: 14.8%, 2: 20.4%, 3: 45.8%** — a genuinely
  U-shaped/ceiling-leaning distribution in this sample, not the skewed-low
  shape Frederick's combined sample shows. Split by exposure: prior-exposure
  subgroup (n=73) M = 2.36, SD = 0.96, **61.6% scored 3/3**; no-exposure
  subgroup (n=69) M = 1.48, SD = 1.21, roughly flat across 0/1/2/3
  (30.4/20.3/20.3/29.0%). Chandler et al. (2014), cited in the same source,
  report a strong correlation between prior study participation and CRT
  score, **r = .79** `[search-synthesis]`.

### 2.3 Verdict on shape

**Not simply "roughly uniform" and not simply "bimodal" — the honest
answer is population-conditional, and that conditionality is itself the
finding.** In a general/naive/less-educated sampling frame the distribution
is right-skewed with the mode at 0 (Stieger & Reips' apprenticeship/naïve
cell, Frederick's own combined 1.24 mean). In an educated/exposed sampling
frame it is left-skewed with the mode at 3 (Stieger & Reips' university/
experienced cell, Haigh's exposed subgroup at 61.6% perfect). **A
population that mixes both subgroups without controlling for education/
exposure will show an apparent BIMODAL-LEANING shape** not because
individual cognition is bimodal, but because it is a **mixture of two
differently-resourced subpopulations** — floor-clustered novices and
ceiling-clustered experts — pooled into one histogram. This maps directly
onto this project's own resource-matching framing (`CLAUDE.md`'s "'simple'
people are perfectly happy and arguably better at what they can do... not a
value judgement, a resource-matching account"): apparent population
multimodality here is a mixture-of-regimes artifact, not evidence that any
one person's reasoning is intrinsically bimodal. Floor/ceiling effects were
severe enough in some samples that Primi, Morsanyi, Chiesi, Donati & Hamilton
(2016) built a longer, IRT-calibrated replacement specifically because "more
than 50% of university student respondents scored 0" on the original 3-item
test in some of their samples `[search-synthesis]` — the same
test-calibration-drives-apparent-shape lesson §5 makes sharply with the
numeracy scales.

### 2.4 The CRT↔misinformation link (Pennycook & Rand)

Confirmed as a real, quantitative, replicated finding, though the exact
correlation coefficients were not extractable from the fetched PDF (binary
stream only) and are reported here at the level the search synthesis could
support: **CRT score is negatively correlated with belief in FALSE
headlines and uncorrelated with belief in TRUE headlines** (the "lazy, not
biased" asymmetry — CRT predicts discernment specifically, not generic
skepticism), and negatively correlated with willingness to SHARE both true
and false headlines. Pennycook & Rand (2018, "Lazy, not biased") used N =
3,446 (two MTurk studies combined); the later COVID-19 misinformation study
(Pennycook, McPhetres, Zhang, Lu & Rand, 2020, *Psychological Science*)
reports an interaction F(1, 25582) = 34.95, p < .0001 for accuracy
discernment and F(1, 25582) = 4.98, p = .026 for sharing discernment —
**N on the order of 25,000+** in the analysis sample, a genuinely
large-scale, real, replicated result. `[medium-high confidence on the
existence and direction of the effect — converging across three
independent search-result syntheses of different papers in the same
research program; exact correlation coefficients not independently
re-derived from primary text]`.

**What this does and does not establish for this project's purpose**: this
is the strongest existing empirical LINK between something CRT-shaped
("propensity to override a fast, coarse, wrong answer") and real-world
belief discrimination (susceptibility to low-quality claims) — directly
on-point for the charter's own interest in coarse-belief mechanisms
(`CAN_BELIEF_QUANTIZATION_RESULTS.md` §1's five citations). It does **not**
establish that CRT measures REPRESENTATIONAL RESOLUTION (how many bins a
belief network can hold) — it measures a specific override behavior on
three narrow items, and the mapping from "override propensity" to "network
resolution" is this document's own inference, exactly as
`CAN_BELIEF_QUANTIZATION_RESULTS.md` §1 already flagged for its own five
citations ("none of them is itself a theory of NETWORK
quantization/resolution").

---

## 3. Q2 — Need for Cognition Scale (NCS) population norms

**Checked and honestly does not fit as a population-norm anchor.** Coelho,
Hanel & Wolf's NCS-6 validation (2020, fetched via PMC7545655) used real,
substantial samples — **US N = 821, UK N = 476 (Study 1); UK N = 299 (Study
2)** — and reports strong reliabilities (**NCS-18: α = .94 US / .91 UK;
NCS-6: α = .90 US / .86 UK**), confirming the scale is real and
well-behaved psychometrically. **But no mean, SD, or percentile table for
the actual NCS total score was found anywhere in the sources checked** —
not in this validation paper, not in the original Cacioppo, Petty & Kao
(1984) 18-item derivation (search-confirmed to contain no normative table
either), not in any subsequent cross-cultural adaptation (the NCS-18/NCS-6
have been validated across Australia, Germany, Greece, Spain, Taiwan,
Portugal, Netherlands, Brazil, and US-Hispanic samples per the search
synthesis, but every hit found discusses factor structure and invariance,
never a normative distribution). **This is the honest, load-bearing
methodological fact about NCS for this project's purpose**: it is used
exclusively as a within-study continuous individual-difference measure,
never norm-referenced — there is no "the population NCS distribution looks
like X" claim anywhere in this literature to anchor a bin-count parameter
to.

**Construct-fit problem, independent of the missing norms**: NCS measures
*motivation/preference* to engage in effortful cognition ("subjective
preference," per the CRT-comparison literature checked in §2.4's
neighborhood), not *capacity* or *representational resolution*. CRT and NCS
are correlated but explicitly treated as distinct constructs in the
literature searched — "the CRT measures objective performance while NFC
measures subjective preference for cognitive effort" `[search-synthesis]`.
A person can be highly motivated to think hard (high NCS) while still
holding a coarse causal representation, or hold a fine one with low
motivation to deploy it effortfully — the constructs are orthogonal in
principle even where correlated in practice. **Per the charter's own
explicit instruction not to force a poor fit, NCS is reported here as a
real but unusable anchor for this specific purpose**, not stretched into
one.

---

## 4. Q3 — Emotional granularity (Barrett et al.) quantitative population data

This is the construct closest in SHAPE to what this project is modeling —
differentiated vs. coarse categorical representation of a graded internal
space — and, unlike NCS, real quantitative distributional numbers exist,
though from smaller samples than CRT's.

### 4.1 The metric and one directly-fetched dataset

Granularity/differentiation is operationalized as an **intraclass
correlation (ICC)** of same-valence emotion ratings across measurement
occasions — high ICC (ratings of "sad," "anxious," "angry" etc. moving in
lockstep) = LOW granularity; low ICC = HIGH granularity (the person's
"sad" and "anxious" genuinely diverge). Wang et al. (2020, fetched via
PMC7684205, "Individual Differences in Negative Emotion Differentiation
Predict Resting-State Spontaneous Emotional Regulatory Processes"), **N =
40** (25 women, 15 men, ages 18–26): a **Negative Emotion Differentiation
(NED) index** (defined as `1 − ICC`, Fisher r-to-z transformed) computed
per participant from ICCs across 20 stimulus images, with the underlying
raw **ICC values ranging 0.43 to 0.97** across participants, mapping to a
final NED index **range −1.01 to 0.54, mean −0.004, SD 0.39**. No
statement in the paper characterizes the distribution's shape (normal,
skewed, bimodal) — this was checked directly and confirmed absent, not
merely unfound.

### 4.2 A second, larger-spread dataset (search-synthesis only)

A separate search surfaced a specific, real-looking statistic — **average
ICC-r for negative emotions = −0.59 (SD = 0.27), with 10th/90th percentiles
at −0.91 and −0.24** — attributed to work in the Erbas/Dejonckheere/Kuppens
research cluster (the exact source paper could not be pinned down; two
candidate PDFs fetched for this document returned only binary stream data,
not extractable text — named honestly rather than silently attributed).
`[flagged: real-looking, specific, but source attribution unconfirmed —
report at low-medium confidence]`. If accurate, this describes a spread
covering roughly **two-thirds of the full possible ICC range** between the
10th and 90th percentile of a real sample — i.e. very large, real,
measured between-person variation in how differentiated people's emotion
reports are, on a construct this project considers the closest existing
analogue to "belief-network resolution."

### 4.3 Developmental trajectory (context for "resolution is not fixed")

Nook, Sasse, Lambert, McLaughlin & Somerville (2018, *Psychological
Science*, "The Nonlinear Development of Emotion Differentiation: Granular
Emotional Experience Is Low in Adolescence") — confirmed real via multiple
independent sources — found emotion differentiation follows a **nonlinear**
developmental trajectory: **falling from childhood to adolescence, then
rising from adolescence to adulthood.** This is directly useful context for
this project's own "resolution is dynamic, not fixed" framing: even within
ONE person, the SAME construct's resolution changes over developmental
time, non-monotonically, which is additional real-world precedent (distinct
from the CRT exposure/education finding in §2.3) that "resolution" is not a
static per-person trait to be looked up once.

### 4.4 Verdict on Q3

**Real, quantitative, directly on-construct — but thin on population
scale.** Where CRT has samples in the thousands with clean per-score
percentages, emotional-granularity studies checked here run N≈40–150
(experience-sampling designs are expensive per participant, which caps
sample size structurally, not incidentally). The ICC metric is also not
itself a bin count — it is a continuous covariation statistic, and turning
"ICC = 0.6" into "N discriminable bins" is not a mapping this literature
provides or that this document invents. What IS usable: the *magnitude* of
real between-person spread (§4.1's SD=0.39 on a roughly [−1,1]-bounded
index; §4.2's near-full-range 10th–90th percentile spread if that figure
holds up) is independent, construct-relevant evidence that human
representational granularity varies A LOT across a real population — larger
in relative terms than, say, a typical IQ or Big-Five trait spread — which
is a fact worth carrying into §8's parameter choice even without a bin-count
translation.

---

## 5. Q4 — Numeracy / graph literacy scale distributions

### 5.1 Berlin Numeracy Test (BNT, Cokely, Galesic, Schulz, Ghazal & Garcia-
Retamero, 2012) — deliberately calibrated to spread the population

**Real numbers, from the search synthesis of the fetched-but-non-extractable
primary PDF plus a corroborating ResearchGate figure caption**: mean score
**48.8% correct** on the population-level scoring, closely matching the
theoretically ideal 50% for a well-calibrated discriminating test; one
validation-sample statistic reports **mean 2.6/4 (SD = 1.13)** on the raw
0–4 item scale. Quartile breakdown from one cited study: **Quartile 1:
12.2%, Quartile 2: 26.5%, Quartile 3: 18.4%, Quartile 4: 42.9%** (39% "low
numeracy," 61% "high numeracy" by this quartile grouping) — a real spread
across the full range, **by design**: the paper's own stated contribution is
constructing items difficult enough to avoid the ceiling effect the older
Lipkus scale suffers from (§5.2).

### 5.2 Lipkus et al. (2001) numeracy scale — the same construct, a different
calibration, a wildly different apparent shape

**Real numbers, found in the same search pass**: in educated samples, the
11-item Lipkus scale shows "dramatic negative skew" — **the LOWEST observed
score in the cited sample was already 5/11 (45% correct)**, and **both mean
and median sit close to the ceiling (88% and 91% correct respectively)**.
Nobody in that sample scored in the bottom 40% of the possible range at
all.

### 5.3 Verdict — the sharpest methodological lesson in this document

**Same underlying numeracy construct, two different item sets, two
completely different "population distributions."** BNT's designers
deliberately pitched item difficulty to spread scores across the full
range (near-uniform, by the paper's own stated goal and the measured 48.8%
population mean); Lipkus's earlier, easier items compress essentially the
entire educated-sample population into the top half of the scale. **This is
direct, real, measured evidence that the apparent shape of a "resolution"
or "capacity" distribution is substantially an artifact of where the
measurement instrument's own difficulty/granularity is pitched, not a fixed
fact about the underlying population.** This is the single most important
transferable warning for this project's own future crossover-point PREREG
(§8): if the resolution-level test conditions are pitched wrong (too easy,
everyone ceilings; too hard, everyone floors), the measured "distribution"
will describe the TEST, not the population, exactly as it does for Lipkus
vs. BNT here.

---

## 6. Q5 — Directly-measured discriminable-level counts: absolute judgment
and optimal Likert-category research

This is, per the charter's own framing, potentially the most directly
relevant question of the five, and it delivered the cleanest, most
convergent real numbers in this document.

### 6.1 Miller (1956) — channel capacity for one-dimensional absolute
judgment

George Miller, "The Magical Number Seven, Plus or Minus Two: Some Limits on
Our Capacity for Processing Information" (*Psychological Review* 63(2),
1956) — one of the most cited papers in psychology, confirmed via multiple
independent sources including the Wikipedia summary page and the original
text hosted at `psychclassics.yorku.ca`. **The specific, quantitative
finding**: across a range of one-dimensional absolute-judgment tasks
(distinguishing tones by pitch alone, loudness alone, etc., with no other
cue available), performance is "nearly perfect up to five or six different
stimuli," then degrades as more categories are added, asymptoting at a
**channel capacity of approximately 2 to 3 bits of information** — which
corresponds directly to **the ability to reliably distinguish between four
and eight alternatives on a single dimension.** `[medium-high confidence on
the headline "2-3 bits / 4-8 alternatives" figure, converging across
multiple independent sources; the original paper's own per-modality table
(pitch ≈X bits, loudness ≈Y bits, etc.) was not independently re-extracted
from primary text in this pass — the WebFetch on Wikipedia specifically
could not surface it]`. Miller's own further point — that adding MORE
DIMENSIONS to a judgment (not just refining one) allows total information
transmitted to increase well past this ceiling — is directly relevant
context for why this project's own multi-dimensional/coordinate structure
(the frame/continuum invariant's own per-dimension resolution) is the right
shape rather than trying to push more distinctions into a single scalar
dimension.

### 6.2 Preston & Colman (2000) — empirically optimal Likert-type category
count

Preston & Colman, "Optimal number of response categories in rating scales:
reliability, validity, discriminating power, and respondent preferences"
(*Acta Psychologica* 104, 2000). Confirmed real via multiple independent
listings (ScienceDirect, Semantic Scholar, a hosted full PDF at
rangevoting.org — the WebFetch on that PDF itself failed on binary-stream
extraction, so this is reported at search-synthesis grain). **Design**: 149
respondents rated real service experiences on scales differing ONLY in
number of response categories, from **2 up to 11**, plus a 101-point format.
**Finding**: reliability, validity, and discriminating power were
**significantly poorer for 2-, 3-, and 4-point scales**, rose steadily with
more categories **up to about 7**, where the **best overall psychometric
performance was found**; **test-retest reliability declined again for
scales with more than 10 categories.** Respondent PREFERENCE (a separate
measure from psychometric performance) peaked at 10 points, closely
followed by 7 and 9 — i.e. people like more options than actually produce
the most reliable data from them. `[medium confidence — consistent,
detailed search-synthesis across three independent listings of the same
paper; not independently re-verified against extracted primary text in this
pass]`.

### 6.3 Verdict on Q5 — genuine convergence, from two unrelated
methodologies

**This is the strongest, most directly load-bearing finding in this
document.** Miller's result is a psychophysical/information-theoretic
measure of raw perceptual/judgment channel capacity, three decades before
Preston & Colman's result, which is an empirical psychometric optimization
over real Likert-type survey reliability. They are unrelated methodologies,
unrelated eras, unrelated dependent variables (raw absolute-judgment
accuracy vs. survey-scale reliability/validity coefficients), and they land
in the **same narrow band**: reliable single-dimension discrimination tops
out around **4–8 (Miller)** and **best psychometric performance is at
exactly 7 (Preston & Colman)**, with **both showing degradation past
roughly 10.** This is real, quantitative, directly-on-construct evidence
for "how many discriminable levels a typical human can reliably use on ONE
graded dimension" — the closest thing in this whole document to a direct
answer to the charter's own Q5 framing.

**What this does NOT establish**: neither result is about CAUSAL or
EVIDENTIAL strength specifically — Miller's tasks are raw sensory
absolute-judgment (tone pitch, line length), and Preston & Colman's is
generic survey-response reliability (service ratings). Applying either to
"causal-strength bins" specifically is an analogy across domains, the exact
caution this project's own prior spike (`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`
§2.4, point 1) already raised for Rescorla-Wagner. It is, however, a MUCH
closer analogy than Rescorla-Wagner's Pavlovian-conditioning transplant,
because both Miller's and Preston & Colman's tasks are already
GENERAL-PURPOSE, domain-agnostic measures of graded-scale discrimination —
not tied to any one content domain — which is closer to what a substrate-
level "resolution" parameter is actually supposed to characterize.

---

## 7. Cross-question synthesis — what a realistic bin-count range looks like

Read together, §2–6 do NOT hand this project a single number, and this
document does not manufacture one where the evidence does not support it.
What they DO establish, laid out precisely:

1. **No existing instrument measures "causal-strength bin count" directly.**
   This confirms the charter's own suspicion implicitly — the crossover-
   point PREREG is exploring genuinely uncharted territory for this specific
   construct, not replicating an existing psychometric result.
2. **The single-dimension discriminable-level literature (Miller 1956;
   Preston & Colman 2000, §6) is the best-fitting PROXY**, precisely
   because it is domain-general rather than tied to one content area, and
   it converges tightly: **≈4–8 reliably discriminable levels, best
   psychometric performance at 7, real degradation past ≈10.** This is
   the most defensible anchor for "how many bins should a SINGLE resolved
   dimension realistically support, for one person, on one occasion."
3. **Real, substantial, well-evidenced variation exists ACROSS people and
   ACROSS context/exposure, on top of that single-occasion number** — and
   this variation is large, not a minor correction term:
   - CRT (§2): the SAME 3-item instrument produces mean scores ranging from
     ≈1.0 (floor-heavy, low-education/naïve) to ≈2.4–2.7 (ceiling-heavy,
     high-education/exposed) — roughly a **2.5× swing** in the same
     3-point-max instrument depending on which real subgroup is sampled.
   - Emotional granularity (§4): individual ICC values spanning **0.43 to
     0.97** in one small direct sample, and a possibly-real 10th/90th
     percentile span of **−0.91 to −0.24** in a second (source
     attribution unconfirmed) — either way, a spread covering most of the
     metric's plausible range.
   - Numeracy (§5): whether a population LOOKS spread-out or ceiling-
     clustered on the identical underlying construct depends heavily on
     which specific test items are used — a warning about calibration, not
     about the population itself, but directly relevant to how the future
     PREREG should be built.
4. **Population shape is domain/context-conditional, not a fixed universal
   curve** — CRT shows right-skew-with-floor-mode in general/naive samples
   and left-skew-with-ceiling-mode in educated/exposed samples of the SAME
   test; a population that pools sub-groups differing in prior
   exposure/training will show an apparent bimodal-leaning mixture even
   though no single individual's cognition is bimodal (§2.3). This is a
   real, evidenced instance of exactly this project's own resource-matching
   framing: different regimes (novice vs. expert, low-exposure vs.
   high-exposure) are not points on one smooth curve, they are genuinely
   different resourcing states, each internally coherent.

---

## 8. Parameters for the crossover-point PREREG

Stated as concrete, justified suggestions, with the reasoning shown, not as
invented precision:

1. **Resolution-level range to test: roughly 2 to 12 bins per dimension**,
   anchored as follows — the LOW end (2–3) covers the CRT-style
   floor/coarse-vocabulary regime already tested directly in
   `CAN_BELIEF_QUANTIZATION_RESULTS.md` §3 (its own "coarse" condition used
   `J ∈ {-1,0,+1}`, 3 values); the MIDDLE of the range (4–8, centering on
   7) is anchored directly to Miller (1956) and Preston & Colman (2000)'s
   convergent "reliably discriminable single-dimension" finding (§6); the
   HIGH end (9–12) deliberately extends slightly PAST both cited ceilings
   (Miller's practical ceiling and Preston & Colman's measured post-10
   reliability decline) specifically to let the crossover experiment
   observe whether pushing resolution past the point real humans can use
   it reliably produces a measurable representational or computational cost
   in the substrate too — i.e. the range should straddle the known human
   ceiling, not stop just short of it, so a genuine "too fine to be useful"
   regime is actually inside the tested window. **This is a design
   recommendation reasoned from the cited numbers, not a number the
   literature itself hands over — stated as such.**
2. **Do not expect, or design around, a single unimodal population curve.**
   §7 point 4's finding is directly actionable: if the crossover PREREG
   samples or simulates a "population" of belief networks with varying
   resolution needs, it should explicitly consider a MIXTURE design (e.g.
   distinct low-exposure/coarse-need and high-exposure/fine-need
   subpopulations, each internally coherent) rather than assuming one
   smooth distribution — this is what the real CRT literature actually
   looks like once education/exposure subgroups are examined separately
   (§2.2–2.3), and it is a closer match to this project's own explicit
   "simple things can and do exist, resource-matched, not deficient"
   framing than a single bell curve would be.
3. **Anchor a "coarse" test condition to 2–3 bins and a "fine" test
   condition to 7 bins, not higher**, if the crossover PREREG wants its two
   endpoint conditions to correspond to real, evidenced human regimes rather
   than arbitrary round numbers — 2–3 matches CRT's own floor behavior and
   `CAN_BELIEF_QUANTIZATION_RESULTS.md`'s own already-tested coarse
   vocabulary; 7 matches Preston & Colman's measured psychometric optimum
   directly. (`CAN_BELIEF_QUANTIZATION_RESULTS.md`'s own "fine" condition
   used 9 values — close to, but one above, this literature's own optimum;
   worth noting as a minor retrospective miscalibration if that comparison
   is reused, not a large one.)
4. **If the PREREG wants a percentile-anchored "how much between-person
   spread should the simulated population span" parameter**, the best-
   evidenced real number available is CRT's own **≈2.5× swing in mean
   score** between real floor-heavy and ceiling-heavy subgroups of one
   instrument (§2.2) — this is offered as the single most defensible
   real-world magnitude for "how large a spread in effective resolution use
   is plausible across a real population," used as an order-of-magnitude
   anchor, not a precise transfer coefficient (the underlying instruments
   are different enough — 3-item pass/fail CRT vs. a continuous bin-count
   parameter — that no exact numeric transfer is defensible; the MAGNITUDE
   of the swing is the transferable fact, not its precise value).
5. **Explicitly test whether apparent "population resolution distribution"
   is a property of the AGENT population or an artifact of the TEST/task
   calibration**, per §5.3's numeracy-scale lesson — i.e. build (or at
   minimum discuss) at least two different task-difficulty calibrations for
   whatever operationalizes "resolution demand" in the crossover PREREG,
   the same way BNT vs. Lipkus inadvertently demonstrated for numeracy, so
   a finding of "the population looks coarse" or "the population looks
   fine" can be checked against whether that is a fact about the population
   or a fact about where the test's own difficulty was pitched.
6. **What NOT to build the PREREG around**: NCS (§3) — real reliability, no
   population norms, wrong construct (motivation, not capacity); a
   single-number confident population mean for "the" causal-strength bin
   count (no such number exists in the literature, and manufacturing one
   would misrepresent every source checked in this document). If asked for
   a single point estimate anyway, the best-justified one from this
   document's own synthesis is **≈7, per §6.3's convergent Miller/Preston-
   Colman finding**, reported with LOW-to-MEDIUM confidence and the
   explicit caveat that neither source measured causal/evidential
   reasoning specifically.

---

## 9. What this document does NOT establish

1. **No literature source directly measures "causal-strength bin count"
   as this project defines it.** Every number in §2–6 is a proxy, and this
   document's own synthesis (§7–8) is where the translation to a bin-count
   parameter happens — it is this document's contribution, not a result
   lifted from a citable source, exactly as `CAUSAL_LINKAGE_DIMENSION_
   RESEARCH.md` §3.3 and `CAN_BELIEF_QUANTIZATION_RESULTS.md` §1 both found
   for their own respective literature searches.
2. **Several sources could not be independently re-verified against primary
   text** in this pass — repeated and named honestly rather than smoothed
   over: Preston & Colman (2000) itself (rangevoting.org PDF fetch returned
   only binary stream data; the ERIC-hosted secondary source on the same
   topic also failed to extract); the Miller (1956) per-modality bit table
   (Wikipedia fetch did not surface it, and the original-text sources found
   were not independently fetched in this pass); the §4.2 ICC statistic
   (−0.59, SD 0.27, 10th/90th −0.91/−0.24) — real-looking and specific, but
   its exact source paper was not conclusively pinned down, two candidate
   PDFs fetched for this purpose both returned unextractable binary
   content; the Pennycook & Rand exact correlation coefficients (only the
   interaction F-statistics and directional findings were recoverable, not
   the underlying correlation magnitudes); the PNAS 2024 "Cognitive
   reflection is a distinct and measurable trait" paper (403 Forbidden,
   not fetched at all — flagged as an unreached source rather than
   silently dropped, since it plausibly bears on CRT/NCS discriminant
   validity and heritability, a question this document did not resolve).
3. **This document does not test, measure, or simulate anything.** Every
   number above is drawn from an already-published human-subjects study
   unrelated to this project's own substrate. Whether human causal-belief
   granularity actually behaves the way any of these proxy constructs do is
   an assumption this document is transparent about making, not a
   conclusion it independently verified.
4. **The §8 parameter suggestions are this document's own reasoned
   translation of §2–7's real numbers into a test design, not a
   literature-derived requirement.** A different, equally well-justified
   translation of the same evidence could reasonably choose a somewhat
   different range; §8 shows its reasoning specifically so that choice is
   auditable and revisable, not so it reads as the literature's own
   verdict.
5. **No connection was attempted here to the `logodds`
   `DimensionGenerator` design from `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md`
   §7, or to the specific bin-count design already tested in
   `CAN_BELIEF_QUANTIZATION_RESULTS.md`'s 2×3 factorial** beyond the direct
   numeric comparisons already drawn in §8 points 1 and 3 above — a full
   reconciliation of this document's suggested range against those two
   prior rungs' own already-built machinery is future-PREREG work, not
   this document's.

---

**Worktree:**
`/home/matt/ozmadev/ocelot-worktrees/causal-granularity-population-distribution-research`
**Branch:** `causal-granularity-population-distribution-research`
**Base:** `main` @ `04845d7` (`Merge can-belief-quantization: retarget to
messy-testimony/network-resolution, GO on the bounded slice`)

Not merged into `main`. This is a research document only — no code, no
seeds, no schema changes were made or proposed as diffs. Its only output is
the range and reasoning in §8, offered as grounding for a future crossover-
point PREREG, not as that PREREG itself.
