# Literature grounding — the cognitive cycle, the developmental cascade, and the Axiom-2→3 wall

A research pass (2026-06-27) situating the jabberwock's converged framing against established work, so the
Axiom-3 build stands on the literature rather than rediscovering it. Four clusters; they converge on ONE next
build, ONE failure mode, and ONE operational test.

## What we found (the framing being grounded)
- **The cognitive cycle:** cheap order-(n−x) recognition by default → ESCALATE up an N-rung ladder of costlier
  recognisers, each gated by a confidence/margin signal, each paid only on the uncertain tail. Top rungs =
  TRACE IT OUT (motor analysis-by-synthesis) and SOUND IT OUT (sequential part decomposition).
- **Development = compilation:** compile escalation outcomes DOWN into the cheap rung; escalation fraction falls
  over experience (we measured 51%→8% on familiar material at held accuracy). Child→competence→expert.
- **Axioms 0–3** grade a skill: 0 exists / 1 iterates (child) / 2 iterates-with-purpose (competence) /
  3 nomological (expert = a universal PROGRAM/law over any instance, able to model others).
- **The wall (scale-confirmed):** an EXEMPLAR-BANK compile reaches Axiom-2 (novel items of FAMILIAR categories,
  8% escalation) but COLLAPSES on novel categories (59%, back to child). It caches APPEARANCE, not the law.
- **Next build, as we named it:** "compile the PROGRAM, not the answers."

## Cluster 1 — escalation is a known, near-optimal architecture (WaldBoost / VOC)
- Our cascade = **WaldBoost** (Šochman & Matas, CVPR 2005): they proved the **SPRT** (Wald 1945; Wald–Wolfowitz
  optimality) gives the **shortest average decision time** for a target FP/FN rate — exactly a confidence-gated
  rung ladder. Viola–Jones (2001) is the ancestor.
- The general objective is **Value of Computation** (Russell & Wefald 1991): escalate iff expected error
  reduction > cost; stop when VOC ≤ 0. Framed as **resource-rational analysis** (Lieder & Griffiths, BBS 2020).
- **Actionable:** stop hand-setting per-rung thresholds — set each gate from the **SPRT bound implied by target
  tail-error** (A,B from α,β), order rungs by cost-adjusted discriminative power. Our near-dead-weight top rungs
  are the EXPECTED result (most mass exits early); prune any rung whose VOC on its residual tail < its cost
  (Saberian & Vasconcelos 2010; Xu et al. 2012).
- **Our genuine novelty:** the rungs are *qualitatively heterogeneous re-enactment modalities* (motor AbS,
  sequential decomposition), not more boosted features — closer to strategy/algorithm selection than a
  homogeneous classifier cascade. And we measure *gate calibration* directly, which the cascade literature assumes.

## Cluster 2 — the wall is the DEFINING property of instance memory; the crossing is schema-by-alignment
- Our compile-down = **Anderson's ACT-R knowledge compilation** (1982): declarative→proceduralization→
  procedural ≈ child→competence→expert. Fitts & Posner (1967) cognitive/associative/autonomous = our axioms.
- **Why the wall is not a bug:** our exemplar-bank-caches-appearance result IS **Logan's instance theory of
  automatization** (1988) — automaticity = retrieving stored instances; transfer is similarity-gated and
  item-specific, *provably no generalization to untrained items*. **Shiffrin & Schneider (1977):** automaticity
  develops only under CONSISTENT mapping (familiar category = consistent → automatizes; novel category = varied
  → re-escalates). Our Axiom-2 ceiling is the theory's defining property, not our design flaw.
- **The crossing mechanism (Axiom-2→3):** **Gick & Holyoak (1983)** — one instance gives no transfer; aligning
  **≥2 analogs** induces a **schema** (shared relations kept, surface discarded) that transfers to
  surface-dissimilar novel cases. Realised as **Gobet templates** (chunks with slots) or **ACT-R productions**
  (fire on conditions, not appearances).
- **The developmental signature that a LAW was reached: OVERGENERALIZATION** (U-shaped past-tense curve, Pinker
  & Marcus) — producing a wrong-but-rule-consistent output proves a generative rule exists, not a lookup.
- **Actionable:** don't cache single appearances — when escalation resolves a case, **align it against the
  nearest prior resolved case and store only the shared generative trace (the program), not the pixels**;
  confirm success by watching for overgeneralization to never-seen categories.

## Cluster 3 (load-bearing) — "compile the program not the answers" IS amortized inference / wake-sleep
The correspondence is exact, not metaphorical:

| Ours | Established mechanism |
|---|---|
| Trace-out AbS / sound-it-out (slow escalation) | Slow inference / program search (DreamCoder *wake*) |
| Cheap recogniser (fast rung) | Amortized recognition / proposal network |
| Compile-down (escalation→cheap rung) | **Sleep / amortization phase** |
| Resolved (image, motor-program) pairs | Sleep-phase replays + fantasies (image, trace) |

- **Inference compilation** (Le, Baydin & Wood 2017): run the generative model FORWARD to draw (trace,
  observation) pairs, train a net to emit q(latent|obs) by forward-KL — training data is free and unlimited
  because the model generates it. **Wake-sleep** (Hinton, Dayan, Frey & Neal 1995): the SLEEP phase dreams
  (obs, true-latent) pairs and trains the recognition net by ordinary supervised inversion. **VAE** folds both
  into one ELBO. **DreamCoder** (Ellis et al. 2021): wake-sleep program induction = neural-guided program search
  + a learned **library of reusable primitives** + a recognition net trained on **replays + fantasies**.
- **Does program-compilation cross the novel-category wall? YES, within a seeded primitive medium — exactly our
  case.** Appearance learners collapse cross-domain (Matching/Prototypical/MAML drop to 51–62% mini-ImageNet→CUB;
  *plain fine-tuning* beats them — Chen et al. 2019; BSCD-FSL below random on distant domains — Guo 2020 = the
  Axiom-2 ceiling, confirmed). The PROGRAM path clears it on OUR domain: **GNS** (Feinman & Lake, ICLR 2021)
  generates *novel character concepts* by sampling the program prior; SCAN→MLC: flat seq2seq **0.08–1.2%** on a
  novel composition vs **99.95%** when rule-extraction is the objective (Lake 2019; Lake & Baroni, Nature 2023).
  **Caveat (honest):** "novel category" = recombination of GIVEN stroke primitives (novel scripts from a stroke
  law) — none learn a brand-new primitive medium zero-shot.
- **Failure mode to avoid — the amortization gap** (Cremer et al. 2018): an over-expressive recognition net
  overfits and generalises WORSE off-distribution → **Axiom-2 in disguise**. Mitigate: forward-KL on broad
  fantasies, regularise the net, and **keep escalation live as the importance-sampling backstop**.
- **THE concrete recipe:** train the cheap rung as an inference-compilation net **image → generative motor
  program (strokes / sub-strokes / deformation params)** on two streams — **replays** (the real (image, program)
  pairs the AbS escalations resolve) + **fantasies** (sample programs from the stroke library, render, train on
  (render, program)). Objective = maximise log q(program | image) (forward-KL, mass-covering). **Keep escalation
  as the backstop:** when the predicted program re-renders with high residual, escalate, resolve, feed the new
  pair back as a replay. That is wake-sleep with replay+fantasy — it compiles the LAW, not the appearances.

## Cluster 4 — figurative→literal = similarity-vs-rule; the law's mark is invariance-under-intervention
- **Similarity is provably under-constraining** (Murphy & Medin 1985): any two things share unboundedly many
  features; only a theory picks which matter — so a resemblance cache is *intrinsically* unable to warrant the
  universal quantifier (it silently softens "all"→"most"). **Exemplar models** (Nosofsky 1986) interpolate well
  but cannot extrapolate to a category with no stored support = our exact finding.
- **Rules generalise over a VARIABLE to ANY instance outside the training space** (Marcus, *The Algebraic Mind*
  2001; Fodor & Pylyshyn 1988). This IS figurative(instance-bound similarity)→literal(variable-bound universal).
  **Honesty caveat:** rule/similarity may be a continuum (Seidenberg's "quasiregularity" 2014; Kirov–Cotterell
  2018) — the defensible claim is not "similarity can never be a law" but "**similarity gives no WARRANT for the
  universal quantifier**" (no guarantee of invariance).
- **The mark of a real LAW** (Woodward; Hempel–Oppenheim 1948 D-N model): **invariance under intervention** +
  counterfactual support. A regularity breaks under intervention; a law does not.
- **"Model others arbitrarily" = simulation theory** (Goldman 2006) **+ generative invertibility:** only a
  re-runnable generative program can be re-parameterized to a never-instantiated config (another writer's style)
  and run forward. A cache has nothing to re-parameterize. Gentner (1983): true transfer carries RELATIONAL
  structure, not surface features.
- **THE operational Axiom-3 test** (mechanically checkable): the cheap rung "holds the law" iff —
  1. it classifies **NOVEL categories synthesized to satisfy the law but lying outside the training manifold**
     (sample new stroke programs far from any exemplar — extrapolation, not interpolation);
  2. its boundary is **invariant under interventions on law-irrelevant factors** (scale, stroke-width, rotation,
     instance noise) where a cache drifts;
  3. **generativity/simulation probe:** it can *generate* a fresh valid instance of a one-shot novel category AND
     *recognise another writer's* stylistic variant by re-parameterizing the same generative model.
  Pass 1+2+3 = literal / law / Axiom-3. Pass only familiar-category novel items = figurative / Axiom-2.

## The convergent conclusion (all four clusters agree)
The next build is **wake-sleep amortized inference of the generative program**: a fast `image→program`
recognition net (the cheap rung), trained on **AbS-escalation replays + stroke-library fantasies** (forward-KL),
with **escalation kept live as the importance-sampling backstop**, gates set from **SPRT/target-error** bounds,
compiling **shared structure across ≥2 aligned resolutions** (not single appearances). Success is **not** a higher
accuracy number alone — it is passing the **invariance + generativity Axiom-3 test** (novel-script extrapolation,
intervention-invariance, generate-and-model-another-writer), and the **developmental signature of
overgeneralization**. This is the literal compile the law demanded; the exemplar bank was the figurative one.
Honest ceiling: it crosses the wall within the seeded stroke-primitive medium, not to brand-new primitives.

### Key sources
WaldBoost (Šochman & Matas 2005); SPRT (Wald 1945; Wald–Wolfowitz); Value of Computation (Russell & Wefald
1991); resource-rational (Lieder & Griffiths 2020); ACT-R compilation (Anderson 1982); Fitts & Posner (1967);
instance theory (Logan 1988); consistent/varied mapping (Shiffrin & Schneider 1977); schema induction (Gick &
Holyoak 1983); templates (Gobet & Simon 1998); overregularization (Pinker & Marcus); inference compilation (Le,
Baydin & Wood 2017); wake-sleep / Helmholtz (Hinton, Dayan, Frey & Neal 1995); reweighted wake-sleep
(Bornschein & Bengio 2015); VAE (Kingma & Welling 2014); BPL (Lake, Salakhutdinov & Tenenbaum 2015); DreamCoder
(Ellis et al. 2021); GNS (Feinman & Lake 2021); cross-domain FSL collapse (Chen et al. 2019; Guo et al. 2020);
amortization gap (Cremer, Li & Duvenaud 2018); SCAN/MLC (Lake & Baroni 2018, 2023; Lake 2019); similarity
under-constraint (Murphy & Medin 1985); exemplar GCM (Nosofsky 1986); the algebraic mind (Marcus 2001); Fodor &
Pylyshyn (1988); quasiregularity (Seidenberg 2014); D-N law (Hempel & Oppenheim 1948); invariance (Woodward);
simulation theory (Goldman 2006); structure-mapping (Gentner 1983); symbol grounding (Harnad 1990).
