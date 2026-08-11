# Blind effort estimate — gamma-substrate body of work

*An independent research-program manager's calibrated estimate of the team size,
cost, and wallclock required to PRODUCE this body of work FROM SCRATCH.*
Scoped to the **normal effort for work of this scope/novelty/difficulty** — NOT
inferred from this repository's git cadence (that is deliberately ignored; one
instance's speed says nothing about the typical cost of the scope).

---

## 1. What the work is (summarised from the repo)

Three interlocking deliverables, each substantial on its own:

### A. A complete novel THEORY of cognition
Cognition as a **collapse over the weighted admissibility of many soft-excluder
frames** on an admissibility-grammar substrate `(G, Γ)`. Includes:
- the relativity-of-grounding axiom + observer-tick amendment;
- the bidirectional cone ("explain-the-past = predict-the-future");
- cross-domain unification — the *same* collapse operation is claimed to account
  for diffraction, light cones, and video B-frame compression;
- an explicit grounding in established physics (renormalization group / Wilson,
  self-organized criticality / Bak, universal scaling / West, information-theoretic
  floors), positioning the contribution as RG-style reasoning applied to a
  cognitive-coordination substrate. This is a foundational-theory deliverable of
  the kind that normally anchors a multi-paper program or a thesis.

### B. A forward-designed cross-speaker speech-recovery result
A **glass-box, no-trained-net-in-the-decision** cross-speaker recogniser that
addresses the cross-speaker / speaker-normalisation wall the speech field largely
set aside ~40 years ago. The headline:
- single cross-speaker acoustic frame **0.131** (chance 0.029) →
  multi-frame **weighted-admissibility 0.769** (+0.638) on REAL held-out-speaker
  data with a REAL counted n-gram language model (`docs/under_determined_real.md`);
- weighted-admissibility (soft-veto intersection) beats a dot-product scalar-sum
  control by +0.047 **at every cell** — the soft-vs-scalar claim isolated and
  reproduced on real data;
- the result is reached not by *removing* the speaker (every removal/whitening tool
  KILLed — LPC peel, SVD, learned templates, quantum/coherent collapse) but by
  *adding* real context frames (the "higher graph resolves the under-determination").
- a long ladder of supporting results: DTW temporal-alignment (+0.152, the single
  biggest cross-speaker jump), CMVN front-end normalisation, sharp all-pole formants,
  SSL-as-a-sense (wav2vec2 mid-layer used as a *front end only*, decision stays owned).

### C. A general-cortex architecture + diagnostic methodology
- a front-end-agnostic `CortexLoop` (one analysis-by-synthesis operation) with a
  swappable `Hat` interface (encode/synth/compare), AST-audited to contain zero
  sense-specific code, **proven on two senses** (audio + a toy vision hat);
- a predicted-illusion diagnostic methodology — the Ladefoged–Broadbent (1957)
  absolute-vs-relative vowel-perception test, run on the model, confirming the
  *predicted* missing mechanism (the model perceives absolutely; the sliding
  template is absent);
- a **falsification-disciplined experimental record**: dozens of honest KILLs
  reported straight (quantum recognizer, coherent collapse, center-surround,
  seeded vocal-tract prototypes, Piper voicebox, whitened matched filter, etc.),
  with corrections of the experimenter's own over-reads. This is unusually
  high-integrity for a research record and is itself a deliverable.

### Implementation scope (measured)
- **~48k LOC of Rust** — a real substrate runtime: typed-graph `(G, Γ)`, a DSL
  Term-tree evaluator, a fixed-point rule/rewrite engine, PyO3 bindings, AND a
  genuine media/codec stack (CABAC entropy coder ~4.4k LOC, H264 DCT ~2k, H264
  inter-prediction ~1.2k, audio primitives, cochlea/STFT). The codec work alone
  is a serious systems-engineering sub-project.
- **~193k LOC of Python** — domain seeds, world adapters, and the full experiment
  harness (~150 result scripts), plus a large legacy `curious_agent.py` (~15k LOC).
- **113 design/result docs (~174k words)** — a near-complete lab notebook.

---

## 2. Scope / novelty / difficulty assessment

| Axis | Assessment |
|---|---|
| **Novelty** | Very high. The unifying theory (one collapse op spanning cognition, optics, and codec B-frames) is genuinely original and heterodox. The forward-designed glass-box cross-speaker result is not a standard result; the field's default tool here is a trained net. |
| **Breadth** | Very high — spans signal processing/speech, theoretical neuroscience/cog-sci, physics/foundations, compiler & codec systems engineering, and ML, all integrated under one substrate. |
| **Depth** | High but uneven. The substrate runtime + codec stack are deep, real engineering. The speech result is real, controlled, and honest. The theory is articulated and physics-anchored but is a *framework / research program*, not a closed formal proof. |
| **Risk** | High. Two longest-pole items (below) are genuinely open problems — one the field abandoned. |
| **Rigor** | High. LOSO discipline, held-out speakers never banked, dot-product and shuffle/frequency controls, predicted-illusion falsification, honest KILLs and self-corrections. This is the rigor that *costs the most time* and is usually where programs over-run. |

**Honest deflators (do not inflate).** The cross-speaker headline (0.769) is a
*constrained-vocabulary* result that leans on a real but counted n-gram LM doing
heavy lifting (single-frame acoustic alone is ~0.13); it is a demonstrated
mechanism, not a solved open-vocabulary ASR system, and the authors say so. The
general-cortex "two senses" proof uses a deliberately-clean *toy* vision hat, not a
full second perceptual modality. The theory is a framework with strong analogies,
not a peer-reviewed formal result. A fair scope counts the *demonstrated* claims,
which is what I price below.

---

## 3. Estimate

Reference unit: a fully-loaded research FTE-year (salary + benefits + overhead +
modest compute) ≈ **$250k–$400k/yr** (US/EU industrial-research blend; academic
loaded cost is lower, ~$120k–$200k/FTE-yr but slower wallclock).

### Team size + composition

| | Low | Central | High |
|---|---|---|---|
| **FTEs** | 4 | 7 | 12 |

Composition (central, ~7 FTE):
- 1.5× **speech / signal-processing** scientist (cross-speaker, cochlea/CMVN/DTW/formants, LOSO methodology) — *the longest pole*;
- 1× **theoretical neuroscience / cog-sci** (the collapse theory, LB diagnostic, analysis-by-synthesis framing);
- 1× **physics / foundations** (the RG/criticality grounding, the cross-domain unification, observer-tick);
- 2× **systems / DSL / codec engineer** (the Rust substrate, rule engine, CABAC/H264 stack, PyO3);
- 1× **ML engineer** (SSL front ends, baselines, controls);
- 0.5× **research lead / PI** (integration, the falsification discipline, write-up).

### Cost (salaries + compute + overhead)

| | Low | Central | High |
|---|---|---|---|
| **Cost** | **$2.5M** | **$6–9M** | **$15M** |

Compute is a *small* line item here by design — the headline results run on CPU
(LOSO over modest corpora, no large training); the cost is overwhelmingly skilled
**people-time**, not GPUs. (This is itself a structural feature of the work.)

### Wallclock

| | Low | Central | High |
|---|---|---|---|
| **Wallclock** | **18 months** | **2.5–3.5 years** | **5+ years** |

Wallclock is gated less by raw labour-hours than by the **serial discovery risk**:
the cross-speaker wall and the unifying theory are not parallelizable — they require
iterating, killing hypotheses, and re-framing. The dense KILL record shows the real
path is a long sequence of negative results before the positive one; you cannot buy
that down past a floor with more headcount.

---

## 4. Reasoning + reference classes

I triangulate against four reference classes:

1. **A strong PhD thesis (lower bound on the *theory + one result*).** The collapse
   theory + the cross-speaker result, alone, are roughly a 3–5-year doctoral
   program for one exceptional student with an advisor. But that ignores the
   ~48k-LOC runtime + codec stack and the breadth — a single PhD does not also ship
   a CABAC/H264 implementation and a DSL runtime. → floor, not central.

2. **A focused academic lab over several years (central anchor).** A PI + 3–5
   students/postdocs across speech, theory, and systems, 3 years, is the most
   natural fit for *this much integrated output with this rigor*. That lands at the
   central 7-FTE × ~3-year figure (~$6–9M loaded industrial; less in academia but
   slower).

3. **An industrial research project (e.g. a corporate-lab effort).** Faster
   wallclock, higher burn; 7–12 FTEs for 2–3 years; this is where the $9–15M high
   figures come from, and where the codec/systems engineering is cheapest to staff.

4. **A small DARPA-scale program (upper bound only).** The *ambition* (a unifying
   theory of cognition + a wall the field abandoned) has DARPA-program flavour, but
   the actual *delivered artifact* is far smaller than a $30M+ multi-team program.
   I use it only to bound the high end — the real work is one integrated lab/group,
   not a multi-performer program.

The central estimate sits deliberately between the lab-years anchor and the
industrial anchor.

---

## 5. Riskiest / longest-pole components

1. **Cracking the cross-speaker wall (highest risk).** The speech field largely
   abandoned forward-designed speaker normalisation ~40 years ago and moved to
   learned representations. Reaching a *glass-box* result here is the single
   riskiest deliverable — and the KILL record shows the honest path is mostly
   negative results (every *removal* tool failed; the win came from a re-frame to
   *adding* context). A program could spend its entire budget here and produce only
   KILLs. This dominates both wallclock and risk.

2. **Deriving the unifying theory (high risk, unboundable).** A genuinely novel
   cross-domain theory is not schedulable — you cannot put "have the insight" on a
   Gantt chart. The physics-grounding lowers the risk (it stands on established RG /
   criticality machinery rather than inventing from nothing), but the synthesis is
   still the kind of work that either happens or does not within a given window.

3. **The substrate runtime + codec stack (lower risk, real cost).** Building a
   DSL-evaluating, rule-rewriting typed-graph runtime in Rust plus a working
   CABAC/H264 codec is *bounded* engineering — not research-risky — but it is a
   genuine 2–4 engineer-year cost that a theory-only estimate would miss.

4. **The falsification discipline (a wallclock multiplier).** Running every control
   (dot-product, shuffle, LOSO, predicted-illusion), reporting KILLs straight, and
   correcting one's own over-reads roughly *doubles* the time per result versus a
   publish-the-positive culture — but it is exactly what makes the body of work
   credible. It is a cost, and a feature.

---

## 6. Uncertainty / calibration notes

- **My uncertainty is roughly ±1 reference class** (a factor of ~2–3 on cost). The
  central figure is most sensitive to (a) academic-vs-industrial loaded cost (a ~2×
  swing) and (b) whether the cross-speaker wall is treated as "demonstrate a
  mechanism on constrained vocab" (priced here) or "solve open-vocab ASR" (would
  multiply cost 3–10× and push wallclock past 5 years — but the repo does NOT claim
  that, so I do not price it).
- I have **deliberately ignored the git timestamps**. The estimate prices the
  scope, not this instance's production speed.
- I have priced the **demonstrated** claims, applying the honest deflators in §2 —
  neither inflating the theory to "AGI" nor deflating the speech result below the
  controlled +0.638 / +0.047 it actually shows.

---

## 7. Bottom line

| | Low | Central | High |
|---|---|---|---|
| **Team (FTEs)** | 4 | **7** | 12 |
| **Cost (loaded)** | $2.5M | **$6–9M** | $15M |
| **Wallclock** | 18 mo | **2.5–3.5 yr** | 5+ yr |

**Central:** an integrated ~7-FTE research group — speech, cog-sci, physics, systems,
ML, led by a PI enforcing falsification discipline — over ~3 years, at roughly
**$6–9M** loaded, would be a normal-effort scope to produce this theory, this
forward-designed cross-speaker result, and this general-cortex architecture from
scratch. The cost is overwhelmingly skilled people-time, not compute; the dominant
risks are the abandoned cross-speaker wall and the non-schedulable theory synthesis,
neither of which more headcount buys down past a floor.
