# SEIZURE FIELD COMPARISON — does our model add to the field *measurably*?

A read-only comparative-science pass: our landed glass-box engine seizure
capability (`seeds/seizure_dynamics.json` + `scripts/seizure_engine_lattice.py`,
documented in `SEIZURE_ENGINE_RESULTS.md`, `SEIZURE_SCIENCE.md`,
`SEIZURE_MODEL_V2_RESULTS.md`, `SEIZURE_DATA_DIVE.md`) placed beside the
state of the art in computational epilepsy. **No engine changes. No timing
claims.** Every literature claim carries an inline citation; a modest or
negative verdict on any axis is reported plainly.

The question is not "is our model interesting" — it is **does it add anything
the field does not already have, and is that addition MEASURABLE (is there a
test that could distinguish it)?** The bulk of the honest answer is *no, we are
behind or merely reframing*; a narrow part is *yes*. This document locates the
narrow part exactly and prices the rest.

---

## 0. What we claim — and, load-bearingly, what we DON'T

Grounding, so the comparison is against our real position and not an inflated one.

**What the model IS (from our own docs, verified against the code):**
- A **reduced, homogeneous** `CognitiveArea` lattice (41×41), uniform
  nearest-neighbour coupling, **harness-driven async clock**. The settlement is
  the real (G,Γ) engine (`run_rules` + `fold_clock_edge` over a DSL rule); the
  clock is I/O (`SEIZURE_ENGINE_RESULTS.md`).
- The seizure **emerges** (genuine positive-feedback-vs-dissipation bistability;
  `alpha=0` never seizes at any give; `give=1` never seizes) and is **byte-
  identity-safe when off** (dedicated test; the rule matches only
  `sz_managed_by`-edged areas the normal scheduler never has).
- Predictions extracted read-only: **P1** decay-rate persist/die separator
  (explicitly distinct from critical slowing down); **P2** abort>onset
  hysteresis; **P3** desync aborts by magnitude not timing; **P4** recruitment
  vs diffusion have opposite signs (v2); **P5** high-degree hubs are the onset
  locus (v2, modest); **P6** one escalation term → seizure (spreads) or
  hallucination (stationary) (v2, exploratory).

**What we DON'T claim (the caveats that gate every cell below):**
- The escalation term `alpha` was **ADDED for the capability, not derived** —
  the engine as built is convergent and *cannot seize*. Functional necessity is
  open (`SEIZURE_SCIENCE.md` Thread 3: **PLAUSIBLE-BUT-UNFORCED**).
- Thresholds (give\*≈0.5375) are **model-internal ratios, not neural units**.
- Faithfulness to the source paper is **bracketing, not a fit** (front speed
  brackets 0.48 mm/s; standing rank-1 0.73–0.87 vs the paper's 0.94).
- **Not validated against real data.** The one near-term-testable prediction
  (P1) needs request-gated both-class data; the open-data pilot is an *honest
  underpowered null* (`SEIZURE_DATA_DIVE.md`).
- P5 is modest (one grid step); P6 is exploratory.

The source paper: Rossi, Wykes, Kullmann & Carandini, "Focal cortical seizures
start as standing waves and propagate respecting homotopy in the connectome,"
[PMC5550430](https://pmc.ncbi.nlm.nih.gov/articles/PMC5550430/) — its OWN open
question (what makes a standing wave persist vs die) is what P1 answers.

---

## Thread 1 — SOTA catalog (cited)

Computational epilepsy is organised along a **level-of-abstraction axis**. The
catalog runs coarse-grained-phenomenological → mesoscale-mechanistic →
fine-grained-biophysical, then the statistical (CSD) and the computational-level
(predictive-coding) frames.

### 1. The Epileptor + its bifurcation taxonomy — *phenomenological*

Jirsa, Stacey, Quilichini, Ivanov & Bernard, "On the nature of seizure
dynamics," *Brain* 2014
([OUP](https://academic.oup.com/brain/article/137/8/2210/2847958);
[PubMed](https://pubmed.ncbi.nlm.nih.gov/24919973/)). A five-variable model on
three timescales built from "first principles of dynamics," deliberately
abstracting away synapses and ions. Its central result: **seizure onset is a
saddle-node bifurcation and offset a homoclinic bifurcation**, which necessitate
two measurable signatures — a **DC/baseline shift at onset** and **logarithmic
interspike-interval scaling near termination** — confirmed in vitro (mouse),
in human focal seizures across syndromes, and in zebrafish. **Contribution:** a
bifurcation-grounded, falsifiable, circuit-independent account that became the
seed of a whole program. **Limit:** mechanism-agnostic by construction — it
captures invariant *dynamics*, not physiological *cause*. **Saggio et al. 2020**
extended this to **16 seizure "dynamotypes"** (4 onset × 4 offset bifurcations)
on a low-dimensional map ([eLife](https://elifesciences.org/articles/55632)),
validated on >2,000 focal seizures from 120 patients across 7 centres — the
field's first objective, theory-derived seizure taxonomy; but it captures brain-
*state* dynamics, showing **no correlation with pathology or localization**.

### 2. The Virtual Epileptic Patient (VEP) — *personalized network of phenomenological nodes*

Jirsa et al., "The Virtual Epileptic Patient," *NeuroImage* 2017
([PubMed](https://pubmed.ncbi.nlm.nih.gov/27477535/);
[ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1053811916300891)).
Epileptor nodes on the patient's own diffusion-MRI connectome — a "digital twin"
for **in-silico surgical planning** (which tissue to resect). Later cast as
Bayesian inference of the epileptogenic-zone network
([Wang et al. 2023, *Sci. Transl. Med.*](https://www.science.org/doi/10.1126/scitranslmed.abp8982)).
**This is the field's clinical-translation flagship and the strongest-validated
line — yet validation is still primarily retrospective:** Makhalova et al. 2022
*Epilepsia* report **precision 64%, recall 44%** vs clinical EZ (precision 77% in
seizure-free patients) on 53 patients
([Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/epi.17310)); Wang 2023
reports EZN precision **~0.6** retrospectively. The decisive prospective test is
the **EPINOV** randomized controlled trial
([NCT03643016](https://clinicaltrials.gov/study/NCT03643016); ~356 drug-resistant
focal-epilepsy patients, ~11 centres, primary endpoint Engel-I seizure freedom at
12 months). **As of mid-2026 the primary-endpoint results are not yet published**
— so even the flagship is "prospectively tested, not yet proven."

### 3. Neural mass models — *mesoscale, mechanistic*

A cortical column collapses to a few ODEs for population membrane potential /
firing rate, with **physiological synaptic gains and time constants**
([Wendling et al. 2016 review](https://pubmed.ncbi.nlm.nih.gov/25843066/)). The
ancestor is **Jansen–Rit 1995**
([Springer](https://link.springer.com/article/10.1007/BF00199471)) — three
subpopulations reproducing EEG-like waveforms and evoked potentials, and
epileptiform spiking under parameter change. **Wendling et al. 2002**
([PubMed](https://pubmed.ncbi.nlm.nih.gov/12028360/)) added a second, faster
inhibitory loop and showed the interictal→ictal transition to **fast gamma
onset activity is produced by impaired dendritic GABA-A,slow inhibition** —
turning "impaired inhibition" into a testable mechanistic hypothesis, validated
by direct qualitative comparison against human SEEG. The **Liley model** (2002)
is a spatially continuous E/I mean-field accounting for the alpha rhythm and
anaesthetic action ([chapter](https://link.springer.com/chapter/10.1007/978-3-642-54593-1_14)).
**Contribution:** a small, physiologically interpretable parameter set where a
bifurcation maps to a clinical EEG transition. **Limit:** lumped/degenerate
parameters; a single mass is a point (no spatial spread without coupling).

### 4. Neural field models — *spatially extended mean-field*

Activity is a continuous field over cortex (± thalamus) governed by
integro-differential / damped-wave equations with distance-dependent
connectivity and axonal delays. Foundational: **Amari 1977**
([Springer](https://link.springer.com/article/10.1007/BF00337259)) — localized
"bumps," travelling waves, oscillatory patterns from lateral-inhibition
connectivity. **Robinson, Rennie & Rowe 2002**
([PubMed](https://pubmed.ncbi.nlm.nih.gov/12005890/)) — a corticothalamic
continuum whose **linear instabilities at EEG spectral peaks evolve into limit
cycles corresponding to petit-mal and grand-mal seizures**, while the same model
reproduces normal arousal spectra. **González-Ramírez, Cash & Kramer 2015**
([PLOS Comput Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004065))
— a field with slow adaptation generating pre-termination travelling
reverberations, **fitted to high-density LFP from 3 human patients** (the most
directly data-constrained field model here). **Contribution:** unifies normal
rhythms and multiple seizure types in one bifurcation diagram; explains
macroscopic travelling wavefronts a point mass cannot. **Limit:** continuum
averaging discards microcircuit heterogeneity.

### 5. Network / graph models of seizure spread — *connectome-based*

Regions are nodes carrying a mass/Epileptor unit coupled through a patient-
specific structural connectome; "epileptogenic zone" and "hub" become
quantifiable. Anchor: **Proix, Bartolomei, Guye & Jirsa 2017**, *Brain*
(*not* J Neurosci — a common miscite)
([PubMed](https://pubmed.ncbi.nlm.nih.gov/28364550/)) — Epileptor-on-connectome
+ linear stability analysis predicts propagation across 15 patients, validated
against SEEG and surgical outcome; **honest limit: patient-specific connectivity
did not reliably beat generic structural information in that cohort.** The
signal-based counterpart is the **Epileptogenicity Index**
([Bartolomei et al. 2008, *Brain*](https://academic.oup.com/brain/article/131/7/1818/388570)).
This family is the precursor to, and now overlaps, the VEP.

### 6. Mean-field corticothalamic models of spike-wave / absence — *mesoscale*

Physiologically-based continuum of cortical E/I, thalamic relay, and reticular
populations closed into corticothalamic loops with explicit delays; seizures are
loop instabilities. **Robinson 2002** (above); **Breakspear et al. 2006**
([OUP](https://academic.oup.com/cercor/article/16/9/1296/276340)) maps the global
bifurcation set and argues **absence and tonic–clonic seizures are predicted and
interrelated by one bifurcation diagram** — the first unifying dynamical account
of primary generalized seizures. **Roberts & Robinson 2008**
([PubMed](https://pubmed.ncbi.nlm.nih.gov/18407293/)) separates axonal-loop vs
cellular delays behind the ~3 Hz spike-wave rhythm. **Validation:** against
rodent-genetic and human spike-wave spectra, not per-patient fitting.

### 7. Critical-slowing-down (CSD) pre-ictal biomarker — *statistical signature, genuinely contested*

Treats the epileptic brain as a system near a bifurcation and imports generic
early-warning theory (rising autocorrelation/variance) at the signal level.
**Kramer et al. 2012, *PNAS*** ([PMC3529091](https://pmc.ncbi.nlm.nih.gov/articles/PMC3529091/))
— seizure *termination* shows slowing, rising correlation, and flickering
(bistable fold of limit cycles); status epilepticus = repeatedly failing to cross
the transition. **Maturana et al. 2020, *Nat. Commun.*** (human iEEG only, 14
patients — no dog data) ([DOI](https://www.nature.com/articles/s41467-020-15908-3))
— autocorrelation/variance fluctuate on circadian/multidien cycles with seizures
on the rising phase; forecasting sensitivity 84% retro / 77% prospective. The
cyclic-risk substrate is real: **Baud et al. 2018** multidien interictal cycles
([Nat. Commun.](https://www.nature.com/articles/s41467-017-02577-y)). **BUT
contested:** **Wilkat, Rings & Lehnertz 2019, *Chaos*** (28 subjects, surrogate-
controlled) found **no evidence for critical slowing down before seizures — in
many cases the dynamics sped up**
([AIP](https://pubs.aip.org/aip/cha/article-abstract/29/9/091104/341751);
[arXiv](https://arxiv.org/abs/1908.08973)). **Status:** long-timescale
susceptibility cycles are real and partly forecastable; a reliable *per-seizure*
short-horizon CSD alarm is disputed. **This debate is the backdrop for our P1.**

### 8. Predictive-coding / free-energy models of epilepsy — *the empty computational-level cell*

**Headline negative result (bounded by search):** across many phrasings there is
**no established free-energy / active-inference / aberrant-precision *theory of
epilepsy*.** The mature precision-imbalance disease accounts target
**schizophrenia/psychosis and autism**, not epilepsy. What *does* exist is
distinct and must not be conflated:
- **DCM *of* seizures** (Cooray, Sengupta, Douglas & Friston)
  ([PMC4692455](https://pmc.ncbi.nlm.nih.gov/articles/PMC4692455/)) fits a
  neural-mass generative model to ictal data by Bayesian belief updating.
- **Omidvarnia, Pedersen, Rosch, Friston & Jackson 2017** frames *interictal*
  connectivity disruption as **aberrant precision control**
  ([PMC5486238](https://pmc.ncbi.nlm.nih.gov/articles/PMC5486238/)) — but
  explicitly *"we are not trying to explain the generation of seizures"*; it is a
  **DCM data-analysis** of interictal resting connectivity, not a generative
  seizure model, and does not model normal cognition.
- **Rosch et al. 2018** DCM of zebrafish seizures
  ([PLOS Comput Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1006375))
  — again a **neural-mass** generative model inverted by Bayesian inference.

**The load-bearing distinction:** in all of these, variational free energy is the
**model-fitting objective the *experimenter* minimizes to invert a model of
data** — *not* the claim that the *brain* minimizes free energy and epilepsy is a
disorder of that inference. The Marr-**computational** level ("what is being
computed, and why") is essentially **empty for epilepsy**. This is the cell our
model uniquely occupies.

### 9. Biophysical detailed models — *fine-grained (Marr implementation level)*

Conductance-based HH networks and ion-concentration dynamics. **Traub**
multi-compartment CA3 / thalamocortical models generate synchronized
epileptiform bursts under GABA-A block
([J. Neurosci.](https://www.jneurosci.org/content/20/6/2086)). The
**Cressman–Ullah–Barreto–Schiff** line adds Na⁺/K⁺ dynamics, pumps, and glial
buffering ([PubMed](https://pubmed.ncbi.nlm.nih.gov/19169801/)). **Wei, Ullah &
Schiff 2014** unify **spikes, seizures, spreading depression, and the anoxic
"wave of death"** on one continuum parameterized by extracellular K⁺ and O₂, with
cell volume as the order parameter separating seizure from spreading depression
([PMC4145176](https://pmc.ncbi.nlm.nih.gov/articles/PMC4145176/)). **Validation:**
against slice / single-unit phenomenology, not human forecasting. These explain
*mechanism* best and *predict patient timing* worst.

---

## Thread 2 — Comparison matrix

### 2a. The primary axis — Marr level (where the field is crowded, and where it is empty)

| Marr level | What lives here | Occupied by |
|---|---|---|
| **Computational** ("what/why is computed; the seizure as failure of a function") | a system that *computes something* and whose seizure is that computation's failure mode | **empty for epilepsy** (FEP applied to psychosis/autism, not seizures — §8). **← OUR CELL** |
| **Algorithmic / dynamical** (state-variable dynamics, bifurcations) | Epileptor, dynamotypes, neural mass/field, mean-field, network spread | **crowded, validated, decades deep** |
| **Implementation** (biophysics: ions, conductances) | Traub, Wei–Ullah–Schiff | **crowded, mechanistically deep** |

The single sharpest statement of our position: **the field is rich at the
dynamical and implementation levels and empty at the computational level; we are
the only entry with genuine computational-level content (a substrate that
perceives, whose give-failure is the seizure) — and we are weak precisely where
the field is strong.**

### 2b. Concrete axes

| Axis | Epileptor / VEP | Neural mass / field / mean-field | Biophysical (HH / ion) | CSD biomarker | **OUR (G,Γ) model** |
|---|---|---|---|---|---|
| **Mechanistic level** | phenomenological (+ personalized network) | mesoscale, physiological | fine-grained, biophysical | statistical signature | **computational + graph-engine implementation** |
| **Links to COGNITION?** | **no** — dedicated seizure oscillator, computes nothing | **no** — dedicated oscillators | **no** | **no** | **YES** — same async-settlement substrate that perceives; seizure = its give-failure |
| **Glass-box observability grain** | state variables (aggregate) | population variables | membrane / ion (fine, but not "the computation") | none (a readout) | **per-node/tick residual = the actual computational primitive** |
| **Predictions made** | DC-shift, ISI log-scaling, dynamotypes; VEP: resection targets | onset-mechanism (e.g. dendritic GABA); spike-wave; travelling waves | seizure↔SD boundary; K⁺/O₂ thresholds | rising autocorr/variance (contested) | **P1 decay-rate separator (≠CSD); P2 hysteresis; P4 recruitment≠diffusion; P5 hubs; P6 one-term seizure+hallucination** |
| **Validation status** | **strongest in field** (cross-species signatures; VEP retro ~0.6; EPINOV RCT, results pending) | qualitative-to-fitted vs SEEG/LFP (some human fits, e.g. 3-patient field) | slice / single-unit | **contested** (Maturana + / Wilkat −) | **none** (synthetic; honest underpowered null; request-gated data) |
| **Biophysical realism** | low (phenomenological) | medium (physiological params) | **high** | n/a | **low** (reduced homogeneous lattice, model-internal units) |

The matrix reads cleanly: **we lead on exactly two cells — links-to-cognition and
observability-of-the-computational-primitive — and trail on validation and
biophysical realism.** Everything else is a wash or a reframe.

---

## Thread 3 — Where we add: per-candidate adjudication (novel? measurable?)

Each candidate is judged on **two** independent tests: **NOVEL** (does the
literature already contain it?) and **MEASURABLE** (is there a test that could
distinguish it from prior art?).

### (a) COGNITION-UNIFICATION — the seizure as the give-failure of the substrate that also perceives

**NOVEL: YES, in the strong sense — but as a *frame*, it is close to negative
space rather than a filled cell.** The *conceptual* framing "seizure as a
pathological attractor of the same substrate that normally computes" is
published: Milton's dynamical-diseases view
([PubMed](https://pubmed.ncbi.nlm.nih.gov/12769430/)); attractor-dynamics reviews
naming seizures "pathological attractors" of the memory/perception substrate
([arXiv 2025](https://arxiv.org/html/2505.01098v1);
[Rosch et al., *Adv. Sci.* 2025](https://advanced.onlinelibrary.wiley.com/doi/10.1002/advs.202411829));
seizure-as-failure-of-self-organized-criticality
([Meisel et al. 2012](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002312)).
The nearest *mechanical* analog — a network that performs a task then collapses
into runaway synchronous oscillation — lives in **machine learning, not
neuroscience** (reservoir "runaway excitation,"
[arXiv 2026](https://arxiv.org/html/2603.29597)), and is framed as an engineering
pathology to suppress, never as a model of epilepsy with a percept/recovery
narrative. **No published model instantiates a substrate that perceives, seizes,
and recovers.** Every dedicated seizure model (Epileptor, VEP, neural mass/field)
computes nothing cognitive; every cognition model that mentions seizures does so
by analogy, not as one running model.

**MEASURABLE: WEAKLY / INDIRECTLY.** The unification *itself* is a conceptual
claim; its own direct test ("the same parameter governs both perceptual-inference
quality and seizure threshold in the same tissue") is not operationalized by us
and is hard to design. Its measurable *yield* is candidate (c)/P6 — the one-term
seizure↔hallucination prediction — plus the softer expectation that seizure
susceptibility should co-vary with cognitive/perceptual load, not just with
anatomy/E-I. **Verdict: NOVEL-BUT-MOSTLY-A-FRAME.** It is a genuine gap in the
literature (the empty computational-level cell), and it is the deepest thing we
bring, but on its own it is closer to NOVEL-BUT-UNTESTABLE than to a measurable
addition. It earns its keep by *enabling* (b) and (c), not by a test of its own.

### (b) P1 — a decay-rate persist/die separator, DISTINCT from critical slowing down

**NOVEL: YES — genuine negative space for the specific operationalization, with
one caveat that must be foregrounded.** The caveat: **"recovery rate / relaxation
time / return time" is not an alternative to CSD — it is the *mechanism* of
CSD.** Autocorrelation and variance are proxies for a slowing recovery rate;
measuring recovery rate directly (e.g.
[Veraart et al. 2012, *Nature*](https://www.nature.com/articles/nature10723)) is
the *purest* CSD indicator, not a rival. A reviewer can therefore argue "decay
rate is just the CSD mechanism," and our write-up must pre-empt that. **Our claim
survives on two points where the literature is genuinely empty:**
1. The measured quantity is the decay rate of the **onset transient's own
   amplitude** (how fast the standing wave sheds activity), used to forecast
   **persist-vs-die of an already-started event** — not the pre-perturbation
   return-time of a resting system approaching a bifurcation. The nearest
   persist-vs-terminate work uses state-space geometry or *onset time*, not a
   transient decay rate
   ([Koppert et al. 2016](https://arxiv.org/abs/1610.00262);
   [Cell Reports 2020](https://www.cell.com/cell-reports/fulltext/S2211-1247(20)30129-7)).
2. **Our model has NO slow variable**, so it *cannot* exhibit the classic
   rising-autocorrelation signature and offers decay rate as the separator
   *precisely where CSD's signature cannot exist*. The general dynamical-systems
   literature supports the plausibility of relaxation-rate trends that are not
   the classic CSD alarm (slow transitions give no CSD warning;
   [O'Regan et al. 2020](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8086860/)),
   but no one has operationalized a decay-rate-of-onset-transient seizure
   separator offered *as an alternative to* autocorrelation.

**MEASURABLE: YES — near-term, on the right modality (though the data is gated).**
Per `SEIZURE_DATA_DIVE.md`: the residual maps to a real observable (above-order-0
= above-baseline prediction-error activity, e.g. high-gamma-envelope-minus-
baseline). The clean test needs a recording labelling BOTH persist and die
onsets with a time-resolved trace — no spatial resolution, no intervention. That
dataset (Rossi's own calcium data, or the Schevon/Merricks microelectrode ictal
data) is **request/DUA-gated, not open-download**, and the scalp-EEG pilot we
*could* run was an honest underpowered null (direction-consistent, p≈0.19–0.38,
CSD-confounded). **Verdict: GENUINELY-NOVEL-AND-TESTABLE.** This is the single
clearest measurable thing we add. The test that would confirm it: *in
calcium/LFP recordings of onset standing waves, the early amplitude-decay rate
predicts persist-vs-die over and above the wave's spatial profile AND over and
above lag-1 autocorrelation (the CSD confound must be controlled).*

### (c) P6 — one escalation term → seizure OR hallucination (the aberrant-precision link)

**NOVEL: YES — genuine negative space for the single-term derivation.** The two
halves each have strong, *separate* literatures; the unification of them from one
term is unpublished. The aberrant-precision account of hallucination is
well-established but never extended to seizure
([Sterzer et al. 2018](https://www.sciencedirect.com/science/article/pii/S1364661318302821);
Powers/Corlett). The clinical epilepsy↔psychosis link (forced normalization,
postictal psychosis) is old but modelled only as **antagonism / mutual
suppression** — the *opposite* framing from ours
([Stevens & Livermore 1987](https://www.sciencedirect.com/science/article/abs/pii/0278584687900170)).
The closest *computational* precedent is neural-field theory — geometric
hallucinations via a Turing instability
([Ermentrout & Cowan 1979](https://link.springer.com/article/10.1007/BF00336965))
and seizure-like waves via an oscillatory instability of the *same* formalism
([field seizure model 2017](https://link.springer.com/article/10.1007/s10827-017-0642-z))
— but these are **two different papers / two different bifurcations**, the
control parameter is diffusive excitability (not precision/prediction-error
escalation), and the switch is Turing-vs-oscillatory, not "spreads laterally vs
points at source without spreading." **No published model derives both a seizure
and a hallucination from one escalation term as two coupling settings.**

**MEASURABLE: IN PRINCIPLE, but hard, and exploratory in-model.** In-model the
two regimes are already measurably distinct (spreading traveling wave, rank-1
drops to 0.42, whole-lattice recruitment vs stationary self-sustained pattern,
rank-1 0.965, locked to onset footprint — `SEIZURE_MODEL_V2_RESULTS.md`). A
real-world test would be a cross-domain prediction — that the same precision/
error-escalation signature underlies both an ictal spread and a hallucinatory
percept, distinguished by lateral coupling — which is a genuine but difficult
experimental program with no near-term open-data path. **Verdict:
NOVEL-AND-TESTABLE-IN-PRINCIPLE but exploratory** — a real conceptual novelty
(it fills negative space) whose measurability is currently confined to the model.

---

## Thread 4 — Where we're behind (stated plainly)

We do **not** beat the field on the axes that matter most for a validated
seizure model. Bluntly:

- **Dynamical fidelity — behind.** The Epileptor's onset/offset bifurcation
  signatures (DC shift, ISI log-scaling) are *validated across species*
  ([Brain 2014](https://academic.oup.com/brain/article/137/8/2210/2847958)) and
  its taxonomy fits 2,000+ human seizures
  ([eLife 2020](https://elifesciences.org/articles/55632)). Our faithfulness is
  bracketing, not a fit (standing rank-1 0.73–0.87 vs the paper's 0.94; speed
  brackets 0.48 mm/s with two free scale params). **They fit; we bracket.**
- **Biophysical realism — behind, and not even trying.** Neural mass models carry
  decades of physiological grounding
  ([Wendling 2002](https://pubmed.ncbi.nlm.nih.gov/12028360/)); HH/ion-
  concentration models place seizure on a mechanistic continuum with spreading
  depression from first-principles ion dynamics
  ([Wei–Ullah–Schiff 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4145176/)).
  Our lattice is homogeneous with model-internal units and no ions, synapses, or
  conductances. **They have biophysics; we have a functional gloss.**
- **Clinical validation — far behind (the widest gap).** The VEP is in a
  prospective randomized surgical trial
  ([EPINOV, NCT03643016](https://clinicaltrials.gov/study/NCT03643016)) with
  retrospective precision ~0.6
  ([Makhalova 2022](https://onlinelibrary.wiley.com/doi/abs/10.1111/epi.17310)).
  We have **zero patient contact**, one honest underpowered null on open scalp
  EEG, and a near-term test that needs gated data. **This is the axis where the
  distance is largest and least arguable.**

---

## VERDICT — do we add to the field *measurably*?

**Yes, but narrowly — and mostly we don't.** The honest classification:

| Contribution | Class |
|---|---|
| (a) Cognition-unification (empty computational-level cell; seizure = give-failure of the perceiving substrate) | **NOVEL-BUT-MOSTLY-A-FRAME** — genuine negative space, deepest thing we bring, but not measurable on its own; earns its keep by enabling (b)/(c) |
| (b) P1 decay-rate persist/die separator, distinct from CSD | **GENUINELY-NOVEL-AND-TESTABLE** — the one clear measurable addition (caveat: must control the CSD/recovery-rate confound; clean data is gated) |
| (c) P6 one-term seizure↔hallucination | **GENUINELY-NOVEL, TESTABLE-IN-PRINCIPLE (exploratory)** — fills negative space; real-world test is a hard cross-domain program |
| Dynamical fidelity, biophysical realism, clinical validation | **BEHIND** — no addition; we trail validated, decades-deep work |
| Bistability/hysteresis (P2), desync-abort (P3), hub-onset (P5), recruitment sign (P4) | **REFRAME-OF-EXISTING** — corroborate documented findings (Kramer bistability; coordinated-reset; hub-onset; connectivity), useful as consistency checks but not additions |

**The blunt one-paragraph verdict.** On the axes the field actually competes on —
dynamical fidelity, biophysical realism, and clinical validation — we add
**nothing**: the Epileptor/VEP line is validated across species and in a
prospective RCT, neural-mass and HH/ion models carry the biophysics we don't
have, and most of our other predictions (P2–P5) are reframes that *corroborate*
existing findings rather than extend them. We add measurably in exactly **one**
place: **P1**, a falsifiable, morphology-independent, CSD-distinct decay-rate
separator that answers the source paper's own open question and is testable at
the right modality — genuinely novel and genuinely measurable, though its clean
test needs request-gated data and its distinction from CSD must be defended
carefully (recovery-rate *is* CSD's mechanism; our claim survives only because
our model has no slow variable and reads the onset transient's own decay). The
deeper novelty — **cognition-unification**, occupying the empty computational-
level cell no seizure model fills — is real but is a frame, not yet a measurement;
its one concrete testable consequence (P6, the one-term seizure↔hallucination
link) is genuine negative space but exploratory. So: **we are a hypothesis
platform that adds one testable prediction and one novel frame to a field whose
validated core we do not touch.** That is a modest, real, and honestly-bounded
contribution — not a field-changer, and specifically not a substitute for the
dynamical, biophysical, and clinical work we sit behind.
