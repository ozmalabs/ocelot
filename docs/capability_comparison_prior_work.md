# The Jabberwock vs. prior work — a cited capability sweep

**Purpose.** Compare the Jabberwock's *integrated feature profile* — not any single
capability in isolation — against the nearest existing systems, and identify what,
if anything, has no demonstrated precedent.

**Method.** Six parallel literature agents (web search + primary-source fetch),
run 2026-07-12, ~30+ sources across six comparator clusters:
(1) OpenCog / Hyperon; (2) cognitive architectures (Soar, ACT-R, CLARION, Sigma,
LIDA); (3) NARS / Gödel machine + PowerPlay / developmental robotics;
(4) DreamCoder / Voyager / recent 2023–25 lifelong-learning + unified-loop search;
(5) computational cognitive-neuropsychology lesion modeling; (6) analysis-by-
synthesis efficiency + cognitive-load-as-measured-compute.

**Two standing caveats, applied throughout.**
1. *"Not found" is bounded by this sweep* (~30 sources), not a proof of nonexistence,
   in a fast-moving area.
2. *The comparison is asymmetric on evidence.* The external cousins are cited,
   demonstrated, and often clinically scored. The Jabberwock's own claims (that its
   self-repair is genuine plasticity, that the AbS ~20–30% figure holds, that its
   speech-disorder grounding is clinically validated) were **not** independently
   verified by this sweep and must be sourced to the project's own gate evidence, not
   asserted with the same confidence as the external literature. Some 2025–2026 arXiv
   IDs below were agent-reported; those the agents independently re-verified are
   marked **[verified]**, the rest should be checked before external citation.

---

## The Jabberwock's 12-feature profile

1. **Substrate** — a typed graph (G, Γ, C) running in Rust; the agent *is* graph data
   (rules, concepts, microtheories, frames are all nodes/edges).
2. **Symbolic reasoning** — rules/microtheories/frames the agent authors, adopts, and
   **ablates** as graph data.
3. **Self-editing** — an Experiment→judge→adopt loop with tunable-parameter knobs and
   **human-gated** promotion of self-improvements.
4. **Self-extending** — the agent proposes its own **new low-level runtime primitives**
   (new Rust DSL terms), sandbox-validated, then human-gated install.
5. **Learning = collapse** — ONE fixed-point loop (`run_rules`) does BOTH discrete
   structural rewriting AND continuous weight descent, driven by ONE surprise signal
   (prediction − observation). Online, local, no backprop, no external optimizer.
6. **Dynamic quantization** — perception decodes against EARNED codebooks that GROW; a
   residual mints a new quantum; recognition and learning are one decode-grow-redecode
   loop.
7. **Multimodal perception + production** — handwriting, vision, language, speech, each
   via its own quantized signature, all sharing ONE self-training reflex/"primal" layer.
8. **Primal layer** — small self-trained reflex nets as a cheap cache, gated by a
   GROUNDED basin (decode residual, external to the net), deferring novel inputs to full
   cognition.
9. **Curiosity / intrinsic motivation** (compression-based).
10. **Introspection / self-model** — answers questions about its own faculties, finds and
    files its own capability gaps.
11. **No pretrained corpus** — bootstraps from a seed of meta-skills; learns online on
    commodity hardware; the whole mind persists as JSON.
12. **Instrumented model for psychology** — toggle a grounded mechanism, read a quantified
    cognitive-load / error / latency effect straight off the substrate's own compute, get
    results that track human data. Includes replicating specific disabilities by targeted
    lesioning, and modeling compensation via self-repair. Concrete instances: turning
    analysis-by-synthesis on → ~20–30% cognitive-load reduction; grounded speech disorders.

---

## The two closest cousins overall

- **Sigma** (Paul Rosenbloom) — closest on the *learning-unification and shared-multimodal-
  representation* axis. The only system where one operation (summary-product over a factor
  graph) does symbolic reasoning + probabilistic inference + gradient descent, online, with
  no separate backprop phase, over one substrate spanning speech/vision/language.
- **OpenCog Hyperon** (Ben Goertzel) — closest on the *homoiconic self-rewriting substrate*
  axis. AtomSpace is a typed metagraph in Rust where code and data are one space.

Neither does the whole thing, and each falls short in a documented way.

---

## Feature-by-feature matrix

Verdict = closest system's level (HAS / PARTIAL / NONE), judged against the Jabberwock's
(strict) version of the feature.

| # | Feature | Closest system | Verdict | Note |
|---|---------|----------------|---------|------|
| 1 | Typed-graph substrate; agent *is* graph data | Hyperon; Sigma; ACT-R | **HAS** | Hyperon's homoiconic metagraph strongest |
| 2 | Authors/adopts/**ablates** own rules | CLARION (RER) | **HAS** | CLARION adds *and* removes vs. a criterion; others add-only |
| 3 | Experiment→judge→adopt, **human-gated** | CLARION (auto) | **PARTIAL** | judge shape exists; the human gate is unmatched |
| 4 | Self-extends its own **runtime primitives** | Gödel machine (theory) | **NONE runs it** | unanimous no across 84 architectures + Hyperon + DreamCoder + NARS |
| 5 | ONE loop: discrete rewrite **+** continuous descent, one surprise, online, no backprop | Sigma | **NO MATCH** | Sigma is the only contender and explicitly falls short |
| 6 | Dynamic quantization: earned codebooks that **grow** | DreamCoder; R-IAC; LIDA | **PARTIAL** | all separate-phase / geometric; none same-loop grow-and-descend |
| 7 | Multimodal via **shared** quantization + one reflex layer | Sigma | **PARTIAL** | Sigma shares a representation; no handwriting, no reflex layer |
| 8 | Primal layer: self-trained reflex cache, grounded-basin gated | (fast/slow splits) | **NO ANALOG** | everyone has a fast/slow split; none a basin-gated trained cache |
| 9 | Curiosity / intrinsic motivation | CLARION; Sigma; Schmidhuber; Oudeyer | **HAS** | the most *shared* feature; real overlap |
| 10 | Introspection / self-model, finds own gaps | Soar (impasse); CLARION (MCS); NARS | **HAS/PARTIAL** | real overlap; Jabberwock files persistent `SelfConcern` nodes |
| 11 | No pretrained corpus; online; commodity HW; persists as JSON | NARS (AIKR); dev-robotics | **PARTIAL** | no one serializes the whole mind; field trends *toward* pretraining |
| 12 | Instrumented psychology: toggle→measure load; disability + compensation | connectionist lesion / 2025 LLM-aphasia; ACT-R toggle | **NO MATCH for the conjunction** | halves exist separately; never combined |

---

## The features with no found precedent — the actual distinctiveness

Four cells came back empty across all six clusters. These are where the claim to
something genuinely new lives.

### #5 — the unified collapse loop (the crux)

No published system does discrete structural rewriting **and** continuous weight descent
in one online, backprop-free, surprise-driven fixed point. After a dedicated wide search
(constructive nets, GWR/neural-gas, structural-plasticity reservoirs, growing-MoE,
growing-codebook VQ, active-inference structure learning) the field bifurcates cleanly:

- **Unify-by-continuous-relaxation** (Firefly NAD; "Growing Neural Networks," arXiv:2501.18012,
  2025) — one backward pass, but structure is a *continuous/differentiable relaxation*,
  still needs backprop, still offline. Not discrete, not online, not backprop-free.
- **Discrete-growth-plus-a-separate-weight-mechanism** (GWR family, neurogenesis models,
  self-motivated growing nets) — truly discrete online growth, but a *second* continuous-
  weight mechanism, usually backprop. Two update rules, not one.
- **Sigma** is the sharpest near-miss: one message-passing operation does symbolic +
  probabilistic + gradient-descent computation online, backprop-phase-free for its
  distributional learning. But *Rosenbloom himself* states the strong unification "fails to
  be supported by work to date," calls it "algorithmic rather than semantic elegance,"
  neural weight learning needed a *separate* 2017 target-prop/backprop bolt-on, and **Sigma
  has no structure learning at all** — so the discrete-rewriting half is not in its loop.
- **Active inference structure learning** is the strongest *conceptual* cousin — expansion,
  Bayesian model reduction, and belief/parameter update all minimize one variational free-
  energy functional. But implementations split expansion from reduction *temporally* (Friston
  analogizes reduction to synaptic downscaling "during sleep"); the "descent" is variational
  message-passing on beliefs, not weight-space descent; demos are toy. That a **2026 review
  paper argues *for* the unified view** is itself evidence the community does not consider it
  a demonstrated running system.

So the exact claim — *one fixed-point loop, discrete rewriting AND continuous descent, one
surprise signal, online, no backprop, no external optimizer, not alternating phases* — has
**no published match** this sweep surfaced.

### #4 — self-extending its own primitives, *and running*

Unanimous NONE across the classical architectures (Kotseruba & Tsotsos's 74-page survey of
84 architectures contains no runtime-primitive self-extension; Sigma's designers explicitly
*refuse* it as "architecturally corrosive"), Hyperon (grounded atoms registered by human
developers against a fixed instruction set), DreamCoder (abstraction is *closed* under the
seed DSL — it names fragments of existing primitives, never invents new primitive semantics),
and NARS (inviolate meta-level: "cannot modify its own law of thought").

Only the **Gödel machine** even *proposes* it — and it was **never realized**: only toy
proofs-of-concept (Steunebrink & Schmidhuber, AGI 2011), whose own authors state proof search
"becomes intractable for larger programs," with Gödel incompleteness as a structural ceiling.
Per Schmidhuber's own writing, "no full implementation has been created." **PowerPlay** is the
runnable relaxation but on toy tasks only (2D classification; single-photo foveation, ~8h/PC).

The precise contrast: the Jabberwock's rung-4 self-extension **sidesteps the Gödel machine's
fatal requirement** — prove global optimality *before* rewriting — by using **sandbox-
validation + human-gated install** instead of a formal proof. An engineering gate rather than
a theorem. That is *exactly why it can run where the Gödel machine cannot*, and it is honest
about the trade: it buys practicality by giving up the "provably optimal" guarantee that made
the Gödel machine unrunnable. A working realization of an idea that had no working instance.

### #8 — the primal layer

No analog anywhere. Every architecture has *some* fast/slow split (CLARION implicit-vs-
explicit; LIDA alarm/automatized modes; Soar elaboration-vs-impasse; Sigma nested reactive/
deliberative/reflective loops) — all rated PARTIAL — but none is a **self-trained reflex net
gated by a grounded decode-residual basin** that explicitly defers out-of-distribution inputs
to full cognition.

### #12 — the instrumented-psychology platform (including the AbS result)

**The two halves are each real; nobody combines them.**

- *The disability half is mature and clinical.* Connectionist cognitive-neuropsychology
  lesioning (Hinton & Shallice 1991; Plaut & Shallice 1993; the DRC model, Coltheart et al.
  2001; the triangle model; semantic-dementia "SD-squared," Woollams et al. 2007; Dell et al.
  1997 fitting 21/23 aphasics) is a genuine tradition, and it jumped into LLMs in ~the last
  year: clinically-scored aphasia (WAB/AQ), Broca-vs-Wernicke phenotypes from MoE-expert
  ablation, and **BLUM** validating LLM perturbation profiles against **410 real stroke
  patients'** lesion-symptom maps (p < 10⁻²³).
- *The toggle half exists* — e.g. Juvina, Taatgen & Dickison (2007) ablate one ACT-R
  inhibition mechanism in the Stroop task and read a measured RT delta against 53 humans.
- *But the conjunction is empty.* Load is **always fit to human RT / NASA-TLX**, never read
  off the model's own compute; every study is single-task, single-modality; compensation
  exists in only two places (Plaut 1996; the 2025 MoE-aphasia rehab paper) and is a *discrete
  experimenter-run retrain*, not always-on self-repair. **No general, multimodal, lesionable
  agent that also models compensation was found.**

**The AbS ~20–30% number specifically is novel, not a replication.** The efficiency prediction
of analysis-by-synthesis is old and explicit — Halle & Stevens stated it in 1962 ("the
necessity of synthesizing a large number of comparison signals can be eliminated by a
preliminary analysis"), most sharply Poeppel et al. 2007 ("a quick reduction of the total
search space") — but it is **quantified nowhere**. Every primary source states it
qualitatively ("small number of trials," "much faster"). The only "20–30% cognitive-load"
figures in the literature are unrelated HCI/NASA-TLX UX studies with zero AbS content. So the
number puts a figure on a 60-year-old qualitative prediction, measured off the substrate's own
compute — a genuine contribution, to be sourced to the project's own measurement, never
presented as literature-backed.

The clean differentiator for #12 as a whole: **load = a directly countable substrate quantity
(rule firings / ticks / decode steps / effort-dial spend) read off the running system, with no
human-data fit in the loop.** All prior load modeling either uses subjective/RT quantities or
counts compute *in order to fit* humans (resource-rational planning-depth). The Jabberwock
inverts the relationship: the substrate's own compute *is* the dependent variable.

---

## Where it genuinely overlaps (honest credit)

Not everything is unique, and the fair report says so:

- **Graph substrate** — Hyperon (AtomSpace), Sigma (factor graph), ACT-R (chunks + productions).
- **Runtime rule authoring** — Soar chunking, ACT-R production compilation, CLARION RER, LIDA schemes.
- **Add-and-ablate rules** — CLARION's Rule-Extraction-Refinement.
- **Curiosity / intrinsic motivation** — CLARION (explicit drive), Sigma (surprise = pre/post-
  learning distribution shift), Schmidhuber (compression progress), Oudeyer (learning progress).
- **Self-gap detection** — Soar impasse, CLARION metacognitive subsystem, NARS `SELF`.
- **Fast/slow split** — all five architectures, partially.
- **No-pretrained-corpus philosophy** — NARS's AIKR is the canonical statement; developmental
  robotics is from-scratch on real robots.
- **Online belief revision without a global optimizer** — NARS truth-value revision is the best
  real-world analog to the "no external optimizer" property.

---

## Bottom line

Per feature, several systems beat the Jabberwock outright (LLMs at language; vision nets at
vision; DreamCoder at program synthesis; the aphasia-LLM work at clinically-scored deficits).
The distinctiveness is **not** any one feature. It is the *combination*, which this sweep could
not find demonstrated anywhere:

> one unified symbolic + connectionist collapse loop, self-extending its own *running*
> primitives, a basin-gated primal layer, multimodal through one growing codebook, usable as a
> toggle-and-measure psychology instrument that also models compensation.

The negative results — no unified-loop precedent (#5), no *running* self-extension of primitives
(#4), no primal-layer analog (#8), no toggle-and-measure-compute-as-load instrument and no
general multimodal lesionable+compensating agent (#12), and the never-quantified AbS efficiency
prediction — are publishable *claims* if the Jabberwock's own side is documented against its
gate evidence. Read them as "not found in this sweep," bounded by ~30 sources in a fast-moving
area, not as certainty.

---

## References by cluster

*IDs the sweep independently re-verified are marked **[verified]**; the rest — especially
2025–2026 arXiv IDs — should be checked before external citation.*

### OpenCog / Hyperon
- Goertzel et al., "OpenCog Hyperon: A Framework for AGI at the Human Level and Beyond,"
  arXiv:2310.18318 (Oct 2023).
- trueagi-io/hyperon-experimental (Rust codebase); docs/minimal-metta.md.
- "Reflective Metagraph Rewriting as a Foundation for an AGI Language," arXiv:2112.08272 (Dec 2021).
- OpenCog wiki: MOSES, Pattern Miner, OpenPsi.
- Goertzel et al., "A Neural-Symbolic Humanlike Arm Controller for Sophia the Robot,"
  arXiv:2010.13983 (Oct 2020).
- "Toward a Formal Model of Cognitive Synergy," arXiv:1703.04361 (2017).
- ActPC-Chem, arXiv:2412.16547 (Dec 2024) — *self-labeled exploratory*.
- opencog/atomspace-storage (persistence).

### Cognitive architectures
- Kotseruba & Tsotsos, "40 Years of Cognitive Architectures," *AI Review* 53:17–94 (2020),
  DOI 10.1007/s10462-018-9646-y (arXiv:1610.08602).
- Soar: Laird, *The Soar Cognitive Architecture* (MIT Press, 2012); Laird, Rosenbloom & Newell,
  "Chunking in Soar," *Machine Learning* 1:11–46 (1986); Laird, arXiv:2205.03854 (2022);
  Nason & Laird, *Cognitive Systems Research* 6(1):51–59 (2005).
- ACT-R: Anderson & Lebiere, *The Atomic Components of Thought* (1998); Bothell, *ACT-R 7.x
  Reference Manual*; Taatgen & Lee, *Human Factors* 45(1):61–76 (2003); Anderson & Schooler,
  *Psychological Science* 2(6):396–408 (1991); Fu & Anderson, *JEP:General* 135(2):184–206 (2006).
- CLARION: Sun, *A Tutorial on CLARION* (2003); Sun, Merrill & Peterson, *Cognitive Science*
  25:203–244 (2001); Sun, *Anatomy of the Mind* (Oxford UP, 2016).
- Sigma: Rosenbloom, Demski, Han & Ustun, "Learning via Gradient Descent in Sigma," ICCM (2013);
  Rosenbloom, Demski & Ustun, "Rethinking Sigma's Graphical Architecture," AGI (2016);
  "Toward a Neural-Symbolic Sigma," ICCM (2017); Rosenbloom, "Lessons from Mapping Sigma onto
  the Standard Model of the Mind," AAAI FS (2017).
- LIDA: Franklin & Ramamurthy, ICCM (2006); Kugele & Franklin, "Learning in LIDA" (2021);
  Franklin, Madl, D'Mello & Snaider, *IEEE TAMD* 6(1):19–41 (2014).
- Laird, Lebiere, Rosenbloom et al., arXiv:2506.07807 (2025).

### NARS / Gödel machine + PowerPlay / developmental robotics
- Wang, "The Logic of Intelligence," AGI/Springer (2007); "Insufficient Knowledge and
  Resources" (AIKR, 2009); "NAL Specification" (2009); "Self in NARS," *Frontiers in Robotics
  & AI* 5:20 (2018); Wang, Hahm & Hammer, "A Model of Unified Perception and Cognition,"
  *Frontiers in AI* (2022). OpenNARS (Java v3.0.4, 2020); ONA (C, P. Hammer).
- Schmidhuber, "Gödel Machines," arXiv:cs/0309048 (2003→2006); "PowerPlay," arXiv:1112.5309
  (2011); "First Experiments with PowerPlay," arXiv:1210.8385 (2012); "Driven by Compression
  Progress," arXiv:0812.4360 (2008); "Formal Theory of Creativity, Fun, and Intrinsic
  Motivation," *IEEE TAMD* (2010); Steunebrink & Schmidhuber, "A Family of Gödel Machine
  Implementations," AGI (2011).
- Oudeyer, Kaplan & Hafner, "Intrinsic Motivation Systems for Autonomous Mental Development,"
  *IEEE TEC* 11(2) (2007); R-IAC, *IEEE TAMD* 1(3) (2009); SAGG-RIAC, arXiv:1301.4862 (2013);
  Moulin-Frier, Nguyen & Oudeyer, *Frontiers in Psychology* 4:1006 (2013).

### DreamCoder / Voyager / recent
- Ellis et al., "DreamCoder," PLDI 2021 / arXiv:2006.08381 (2020).
- Wang et al., "Voyager: An Open-Ended Embodied Agent with LLMs," arXiv:2305.16291 (2023).
- LILO, ICLR 2024 / arXiv:2310.19791.
- "Growing Neural Networks: Dynamic Evolution through Gradient Descent," *Proc. Roy. Soc. A*
  (2025) / arXiv:2501.18012.
- Zheng et al., lifelong-LLM-agent roadmap, arXiv:2501.07278; KnowSelf, arXiv:2504.03553.
- Neacsu et al., active-inference structure-learning review, *Minds & Machines* (2026).

### Cognitive-neuropsychology lesion modeling
- Hinton & Shallice, *Psychological Review* 98(1):74–95 (1991).
- Plaut & Shallice, *Cognitive Neuropsychology* 10(5):377–500 (1993).
- Coltheart, Rastle, Perry, Langdon & Ziegler (DRC), *Psychological Review* 108(1):204–256 (2001);
  Nickels et al., *Cognitive Neuropsychology* 25(2):165–193 (2008).
- Plaut, McClelland, Seidenberg & Patterson, *Psychological Review* 103(1):56–115 (1996).
- Woollams, Lambon Ralph, Plaut & Patterson ("SD-squared"), *Psychological Review*
  114(2):316–339 (2007).
- Rogers et al., *Psychological Review* 111(1):205–235 (2004).
- Farah & McClelland, *JEP:General* 120(4):339–357 (1991).
- Mozer & Behrmann, *J. Cognitive Neuroscience* 2(2):96–123 (1990).
- Dell, Schwartz, Martin, Saffran & Gagnon, *Psychological Review* 104(4):801–838 (1997).
- Salvucci, Chavez & Lee (ACT-R aging), *Proc. CogSci* 26:1197–1202 (2004).
- Plaut, "Relearning after Damage… Toward a Theory of Rehabilitation," *Brain and Language*
  52(1) (1996).
- Eliasmith et al. (Spaun), *Science* 338:1202–1205 (2012).
- LLM-aphasia (2025–26, agent-reported): Wang et al., "MoE-Based Functional Lesions for
  Simulating and Rehabilitating Aphasia," arXiv:2508.04749 **[verified]**;
  Fridriksson et al. (BLUM), arXiv:2602.04074 **[verified]**;
  Roll et al., "Artificial Aphasias in Lesioned Language Models," arXiv:2605.16222 **[verified]**;
  Wang et al., "Component-Level Lesioning…," arXiv:2601.19723 **[verified]**.

### Analysis-by-synthesis + cognitive-load-as-compute
- Halle & Stevens, "Speech recognition: A model and a program for research," *IRE Trans. Info.
  Theory* 8(2):155–159 (1962).
- Liberman & Mattingly, "The motor theory of speech perception revised," *Cognition* 21:1–36 (1985).
- Poeppel, Idsardi & van Wassenhove, *Phil. Trans. R. Soc. B* 363(1493):1071–1086 (2007/2008).
- Yuille & Kersten, "Vision as Bayesian inference: analysis by synthesis?," *TICS* 10(7):301–308 (2006).
- Rao & Ballard, "Predictive coding in the visual cortex," *Nature Neuroscience* 2(1):79–87 (1999).
- Friston, "The free-energy principle: a unified brain theory?," *Nat. Rev. Neurosci.* 11:127–138 (2010).
- Juvina, Taatgen & Dickison (ACT-R Stroop toggle), *Proc. CogSci* 29:1133–1138 (2007).
- Lieder & Griffiths, "Resource-rational analysis," *Behavioral and Brain Sciences* 43:e1 (2020).
- Yildirim, Kulkarni, Freiwald & Tenenbaum, "Efficient and robust analysis-by-synthesis in
  vision," CogSci (2015); Yildirim et al., "Efficient inverse graphics in biological face
  processing," *Science Advances* 6:eaax5979 (2020).
- Kulkarni et al., "Picture: A probabilistic programming language for scene perception," CVPR (2015).
