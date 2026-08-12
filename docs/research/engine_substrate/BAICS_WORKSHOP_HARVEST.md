# BAICS workshop harvest — triaged, not summarised

**Status: HARVEST/TRIAGE. No code, no seeds, no tests, no builds in this
document.** One new file; nothing else in the repository is touched. Written
2026-08-12, in the style of `RULES_AS_SHAPE_DESIGN_SPIKE.md` §15 (external-paper
triage) and calibrated against `RAVANA_CONVERGENCE_AUDIT.md`'s honesty
standard (report the null as plainly as the hit).

**Source, and one correction to the brief before anything else.** The brief
that reached me described BAICS as "AAAI-affiliated" and asked me to confirm
this from the page rather than assume it. **I did, and it is wrong: BAICS —
"Bridging AI and Cognitive Science" — is an ICLR workshop, not an AAAI one.**
The page itself states it plainly: `<h4><a href="https://iclr.cc/Conferences/2020">
International Conference on Learning Representations (ICLR)</a></h4>`, held
2020-04-26. The site (`baicsworkshop.github.io`) documents exactly one edition
— **43 papers total**, program IDs `baics_0` through `baics_42`, every one with
a title, an author list, and a PDF link, and **zero abstracts anywhere on the
HTML pages** (confirmed: the per-paper `/program/baics_N.html` pages carry only
title/authors/track/PDF-link; the abstract lives only inside each PDF). A web
search for later editions (2021/2022/2023) under this name returned nothing —
see §4 for what this does and does not establish about completeness.

## One paragraph, up front

**43 papers reviewed. One landed in Tier 1.** The single most useful thing
found: **"Relaxed Graph Matching for Analogical Reasoning" (Segert, Tepper,
Turek, Cohen — Princeton Neuroscience Institute / Intel Labs) is a *third*,
independently-arrived-at instance of exactly the operation this project's
`AntiUnifyWitness` + `Substitute` pipeline already implements and just
demonstrated working on real corpus rules** (`RULE_REFERENCE_LAYER_SIZING_RESULTS.md`'s
2×2 parallelogram) — "extract the structure-preserving map between a known
pair, apply it to transfer a solution to a new pair" — but arrived at via a
**completely different formalism**: a continuous relaxation of an NP-hard
graph-matching/quadratic-assignment problem, solved by gradient descent per
query pair, rather than symbolic anti-unification over term trees. It is the
third SMT-grounded paper this project's own research thread has now reviewed
this week (after DeepGAR and MarT in the design spike's §15) to converge on
this exact operation from a different direction, and it offers a genuinely
different (not merely repeated) answer to the same "this doesn't scale to a
brute-force pairwise scan forever" concern DeepGAR was cited for. **Beyond
that one paper, the honest finding is a null: this workshop's papers mostly do
not bear on this project's specific active threads.** BAICS 2020 is a broad
brain-inspired-AI workshop — vision neuroscience, RL/curiosity, language
acquisition, developmental cognition, memory architectures, active inference —
and the large majority of it (28 of 43 papers) has no connection to
shape-math, analogical transfer, subsumption lattices, program/library
learning, or any of the five confirmed `SHAPE_AUDIT.md` patterns. Fourteen
more are adjacent enough to name (cognitive architectures, ToM, memory
systems, compositional generalization) without being actionable. That ratio —
1 direct hit, 14 adjacent, 28 unrelated, out of 43 — is itself the honest
shape of "harvest a general cognitive-science workshop for a specific,
narrow, actively-building research thread," and is reported as such rather
than stretched.

---

## Tier 1 — directly harvestable

### "Relaxed Graph Matching for Analogical Reasoning" — Segert, Tepper, Turek, Cohen (ICLR 2020 BAICS, Research Track Spotlight)

No arXiv ID is given anywhere in the paper or its references; it is a
4-page-plus-supplement workshop paper only, not published elsewhere as far as
this review found. PDF read in full (`/pdf/BAICS_4.pdf`, 6 pages incl.
references and two supplement sections).

**What it actually does, grounded in the method section.** It formalises
analogy **explicitly following Gentner (1983) Structure-Mapping Theory** —
cited directly, same grounding as DeepGAR and MarT in the design spike's §15
— as a graph-matching problem: given source graph `G1 = (V1, E1)` and target
graph `G2 = (V2, E2)`, find `F: V1 → V2` that preserves adjacency as closely
as possible. The violation count is

```
N(F) = ||Q_F A2 Q_F^T − A1||_1
```

where `Q_F` is the quasi-permutation matrix of `F` — and the paper states
directly, citing Loiola et al. 2007, that **minimising `N` is NP-hard** (it is
a quadratic assignment problem). Their move — and this is the paper's actual
contribution, not the SMT framing, which is standard — is to **relax the
discrete quasi-permutation matrix `Q_F` to a continuous row-stochastic matrix
`P`**, giving a differentiable loss `L_X(P | A1, A2) = ||P A2 P^T − A1||_1`
over the polytope of row-stochastic matrices consistent with any given "Marked
Points" (a priori known correspondences — exactly the fixed dimension `Q` in
this project's own RR4 parallelogram: a subset of the mapping is given, the
rest is solved for). `P` is parametrised by a small neural network and
optimised **per query pair, by gradient descent — explicitly not a
train/test paradigm** ("we solve each matching problem online," their own
footnote 3). A second variant substitutes the raw adjacency matrix for the
**successor representation** `SR_G = (1 − γ Ā_G)^{-1}` (Dayan 1993), which
they report "performs better in practice." Once `P` is solved, a valid
discrete mapping is recovered by row-wise argmax.

**Validation, read precisely — illustrative, not benchmarked, and the paper
does not claim otherwise.** Three case studies, none with an ML-style
accuracy/F1 number against a competing method:

1. **Tower of Hanoi, within-family transfer** — same graph, different
   start/goal states; the algorithm maps a solved path from one goal to a
   valid path to the other. This is structurally the closest thing in the
   whole batch to RR4's own within-family parallelogram completion.
2. **Farmer/Goat → Missionaries/Cannibals, cross-family transfer,
   replicating a documented human-cognition asymmetry.** Citing Holyoak &
   Thagard (1989): children who solve the simpler Farmer/Goat puzzle first
   transfer successfully to Missionaries/Cannibals, but not the reverse. The
   algorithm reproduces this asymmetry quantitatively: of 768 possible
   shortest solution paths, **only 4.7% map to valid Missionaries/Cannibals
   solutions when transferred in the harder-to-easier direction.** This is a
   real, precise number, but it is a **cognitive-plausibility replication**,
   not a benchmark score — it is being read against human developmental data,
   not against a competing algorithm's accuracy.
3. **Recursive/self-similar structure discovery by self-coarsening.** The
   `n`-disk Hanoi state graph is built from the `n−1`-disk graph by replacing
   each node with a clique of 3. Matching the larger graph onto the smaller
   one (rather than onto a same-size target) **recovers this recursive
   structure directly** — the algorithm reveals that groups of 3 nodes in the
   big graph collapse onto single nodes of the small one. The authors name
   "a more systematic treatment of graphs with recursive or self-similar
   structure" explicitly as unaddressed future work, not a delivered
   capability — this is one hand-picked illustration, not a general
   recursion-detection algorithm.

The paper explicitly contrasts itself with Li et al. 2019's graph-similarity
learning (a GNN producing a **scalar** similarity, no explicit
correspondence) — naming, in its own words, precisely the MAC-vs-FAC
distinction this project's design spike already diagnosed as the rule layer's
core defect: a scalar verdict with no structural correspondence underneath it
versus an explicit node-wise map.

**What this would mean for this codebase, if harvested — sized honestly in
three parts, matching §15's own DeepGAR/MarT/Tiered-Identicality framing:**

1. **A genuine second answer to the same NP-hardness/scale question §15.2
   raised for DeepGAR — not needed now, standing answer for when scale
   changes, and a different cost profile.** RR4 ran `AntiUnifyWitness`
   directly, pairwise, over all 2,851–2,934 corpus recognisers and found it
   fast enough to just do (§4.4 of the sizing results: "~1 min each" for the
   corpus sweep). This paper's relaxation is a genuinely different answer to
   the same eventual problem DeepGAR was named for — but with a different
   trade: DeepGAR trains one embedding space up front (13× cheaper than the
   next baseline, amortised across many queries) whereas this paper's
   relaxation needs **no training data or labels at all**, but is solved
   fresh, by gradient descent, **per query pair** — cheaper to stand up,
   not amortised. If a future rung ever needs "which of two proposal
   mechanisms to try first when brute-force pairwise `AntiUnifyWitness`
   stops being free," this is a second, cheaper-to-bootstrap option worth
   knowing about alongside DeepGAR's embedding-index answer — `[unverified]`
   against this repo's own codebooks, per the same standing caveat §15.2
   carries.
2. **Independent confirmation, not new content, on the "marked points"
   structure.** A subset of the correspondence given a priori, the rest
   solved for, is exactly the shape of RR4's fixed dimension `Q` (the
   binding var, held constant across the parallelogram) versus the free
   dimension `P` (what is solved for, `where.a.items.0.key`). This doesn't
   add a mechanism — it's the same convergence §15.4 already named for
   DeepGAR's Tiered Identicality, one more data point that the algebra this
   project already built independently matches externally-published
   formalisations of the same operation.
3. **The weakest and most honest of the three: a citation to reach for, not
   a mechanism to build, for the order-N/recursive-structure question that
   is still `[unverified]` in this project's own design spike.** §7.2 item 4
   of `RULES_AS_SHAPE_DESIGN_SPIKE.md` flags `sd_infer_dimension` at rule
   grain as "`[unverified]` whether this rung ever fires usefully," and
   `order_n_shape_matching_grounding.md`'s own prescription (quoted in the
   spike's §4.2) is "Order-N as a FIXPOINT of the agent's own shape-matcher
   applied to its own outputs." This paper's third case study is a real,
   if singular and hand-picked, external demonstration that matching a
   structure against a *coarsened version of itself* is a genuine way to
   surface recursive structure in the SMT literature — worth citing the
   next time that specific open question is picked back up, precisely
   because it is external grounding for an idea this project has so far
   only stated as a research-doc prescription, never built or tested. It is
   not a general algorithm, has one illustration, and should not be sized
   as more than that.

**What a future rung sizing this would need to check first, in one sentence,
per the constraint on this document:** whether `AntiUnifyWitness`'s exact,
symbolic pairwise sweep genuinely stops being affordable at some corpus size
this project is likely to reach (RR4's own honest scope note: "190 files
carry the shape; how many would actually go red under a real build is
unmeasured" — the same "don't measure a rejected option" discipline applies
here before reaching for a relaxation this project has no present need for).

---

## Tier 2 — adjacent, worth knowing about, not actionable

Fourteen papers. Abstracts read (fetched from the PDF, page 1) for the first
six; the remaining eight are judged from title + the enumeration context
alone, per the instruction not to deep-read every paper.

- **"Cognitive Architectures for Introspecting Deep Reinforcement Learning
  Agents"** (Mitsopoulos, Somers, Lebiere, Thomson — CMU / Army Cyber
  Institute). Uses ACT-R's declarative-memory / instance-based-learning
  module to give a human-interpretable account of an RL agent's decisions in
  a gridworld. Adjacent to this project's self-account/gap-awareness threads
  (CLAUDE.md's "THE AGENT FIXES ITSELF" sections) in spirit — interpretable
  process accounts of an agent's own decisions — but the mechanism (a
  separate symbolic cognitive architecture running alongside a DRL agent) has
  no contact with this project's graph-native single-substrate design.
- **"Deep Learning Needs a Prefrontal Cortex"** (Russin, O'Reilly, Bengio).
  A position/survey paper connecting PFC executive-function neuroscience
  (planning, rule-learning, controlled processing, abstract/out-of-distribution
  reasoning) to deep learning's known gaps. No method to harvest; relevant
  only as a framing document, peripherally to the F-16/`decision_making_spike.md`
  executive-control thread.
- **"Product Kanerva Machines: Factorized Bayesian Memory"** (Marblestone,
  Wu, Wayne — DeepMind). A hierarchical, factorised Bayesian slot memory
  (product of independent Kanerva Machines) that discovers sparse,
  combinatorial allocation patterns and factorises images by object,
  unsupervised. Memory-architecture-adjacent to the sd loop's codebook
  concept, but the mechanism (Bayesian posterior inference over a Gaussian
  storage matrix) is a different family entirely from decode-against-codebook
  with a residual-driven mint.
- **"Modeling Conversation Context by Adapting Cognitive Architectures"**
  (Santhanam, Shaikh — UNC Charlotte). Augments seq2seq dialogue generation
  with long-term/working memory per the "Standard Model of Cognition"
  (Newell/Sun), plus an attention-like action-selection step to pick salient
  history. Adjacent to the conversation seed family by subject only; the
  mechanism is a memory-augmented seq2seq net, nothing shape-matching-shaped.
- **"Toward Human-like Object Naming in Artificial Neural Systems"** (Eisape,
  Levy, Tenenbaum, Zaslavsky — MIT). Derives optimal container-naming systems
  from an Information-Bottleneck (rate-distortion) analysis over CORnet-S
  image-classifier layers, and shows deeper layers better predict human
  cross-linguistic naming (Dutch/French). Adjacent to the lexical-grounding /
  `teach()` thread by subject (word meaning as compression over a
  representation space) but the IB rate-distortion formalism has no contact
  with this project's decode/residual/mint loop.
- **"Levels of Analysis for Machine Learning"** (Hamrick, Mohamed —
  DeepMind). Argues for adopting Marr's computational/algorithmic/
  implementation levels as a shared vocabulary for ML debates, with worked
  case studies. No mechanism to harvest; noted because it is a genuine
  conceptual cousin of CLAUDE.md's own "is this value IN a frame or BETWEEN
  frames?" discipline (a levels-of-analysis distinction one level more
  general) — worth knowing the vocabulary exists in the literature, not
  worth citing as grounding for anything specific.
- **"Theory of Mind with Guilt Aversion Facilitates Cooperative
  Reinforcement Learning"** (Nguyen, Venkatesh, Tran). ToM + guilt-aversion
  reward shaping for cooperative multi-agent RL. Matches this project's
  psychology-seed/ToM-concepts thread by subject only.
- **"Mental models for neural models"** (Owen Lewis, single author). A
  philosophy-of-cognitive-science piece on what it would mean for a neural
  network to have a "mental model." Conceptually adjacent to the
  `self_processes`/self-account faculty question CLAUDE.md documents, no
  mechanism.
- **"Deep Active Inference for Autonomous Robot Navigation"** (Catal,
  Verbelen, De Boom, Dhoedt, Wauthier). Active-inference (variational
  free-energy) navigation. Adjacent to the quanta-navigation thread by
  subject (spatial control) but a different mechanism family (free-energy
  minimisation vs. the sd-loop's flood/decode over `SpaceQuantum`); closer
  in spirit to `decision_making_spike.md`'s risk-ladder thread than to the
  shape-math thread this review is centred on.
- **"Weakly-Supervised Trajectory Segmentation for Learning Reusable
  Skills"** (Mahmoudieh, Darrell, Pathak). Segments unlabelled trajectories
  into reusable skill primitives. Adjacent to the program-synthesis
  chunk-mining thread by subject (unsupervised segmentation into reusable
  parts) but for continuous robot trajectories, not program/rule structure.
- **"On Systematic Generalization of Sequence to Sequence Models"** (Kagitha).
  Compositional-generalization failure modes in seq2seq. Adjacent to the
  analogical-transfer thread by subject (does structure trained on one
  composition transfer to a novel one) but no shared mechanism.
- **"Brain-like replay for continual learning with artificial neural
  networks"** (van de Ven, Siegelmann, Tolias). Biologically-inspired replay
  to avoid catastrophic forgetting. Adjacent to the sd loop's
  recognise-vs-mint boundary by subject (when does new experience overwrite
  vs. extend held structure) but a different mechanism (generative replay of
  past activations, not a growable discrete codebook).
- **"Causal Learning by a Robot with Semantic-Episodic Memory in an Aesop's
  Fable Experiment"** (Bhat). A robot learns a causal rule (water
  displacement) via semantic-episodic memory integration. Adjacent to
  psychology/relations seeds by subject only; single-author, thin
  workshop-length treatment.
- **"Attention Driven Dynamic Memory Maps"** (Sahni, Bansal, Isbell).
  Attention-gated addressable memory for navigation-adjacent tasks. Loosely
  adjacent to spatial-quanta / dynamic-memory-addressing by subject, no
  shared mechanism with the sd loop or `space_quantize`.

---

## Tier 3 — not relevant (28 papers)

Reviewed by title (and, where a title was genuinely ambiguous against this
project's threads, the abstract) and set aside without individual write-up,
per the instruction not to force relevance. Subject areas covered, so the
sweep can be confirmed exhaustive rather than selective:

- **Vision / neuroscience-of-vision modelling** (7): "From heuristic to
  optimal models in naturalistic visual search"; "Global-Local Network for
  Learning Depth Via Interaction"; "What can human minimal videos tell us
  about dynamic recognition models?"; "Convolutional Neural Networks as a
  Model of Visual Activity in The Brain"; "CognitiveCNN: Mimicking Human
  Cognitive Models to resolve Texture-Shape Bias"; "Model Zoology and Neural
  Taskonomy for Better Characterizing Mouse Visual Cortex"; "Learning robust
  visual representations using data augmentation invariance."
- **Attention / visual-search / perception modelling** (2): "The perceptual
  boost of visual attention is task-dependent in naturalistic settings";
  "Towards modeling the developmental variability of human attention."
- **RL / curiosity / world-model learning, embodied** (6): "Reinforcement
  Learning through Active Inference"; "Probabilistic Successor Features
  Allow for Flexible Behaviour"; "Towards Curiosity-Driven Learning of
  Physical Dynamics"; "Exploring Exploration: Comparing Children with RL
  agents in Unified Environments"; "Active World Model Learning in
  Agent-rich Environments with Progress Curiosity"; "Curiosity Increases
  Equality in Competitive Resource Allocation."
- **Language / linguistics modelling, not structure-mapping** (5): "Entropy
  Minimization In Emergent Languages"; "Learning Hierarchical Syntactic
  Transformations with Encoder-Decoder Networks"; "Can neural network
  language models understand spatial perspective?"; "Analyzing acoustic word
  embeddings"; "On Memory in Human and Artificial Language Processing
  Systems."
- **Developmental / physical-world learning** (2): "Learning Intuitive
  Physics Through Objects"; "Coarse-to-Fine Curriculum Learning for
  Classification."
- **Situated / grounded language, not analogy** (1): "Ecological Semantics:
  Programming Environments for Situated Language Understanding."
- **Generative / creative / evaluative models** (3): "Toward A Neuro-Inspired
  Creative Decoder"; "A Neuro-AI Interface for Evaluating Generative
  Adversarial Networks"; "Public Self-consciousness for Endowing Consistent
  Persona to Dialogue Agents."
- **Network science of trained models** (1): "What does a pruned deep neural
  network 'forget'?"
- **Neuroscience of sleep/consolidation** (1): "Simulated sleep helps to
  generalize knowledge in a spiking network trained with spike-timing
  dependent plasticity" — grouped alone because its mechanism (synaptic
  consolidation during simulated sleep) has no analogue anywhere in this
  project's architecture.

(Bucket counts: 7 + 2 + 6 + 5 + 2 + 1 + 3 + 1 + 1 = 28, matching the header.)

---

## What this review does NOT establish

1. **It does not establish that BAICS 2020 is the whole of BAICS.** The
   workshop's own description frames it as one edition of an ongoing
   cross-conference effort ("Bridging AI and Cognitive Science" as a general
   aim, not a 2020-specific one), and a slide deck at
   `baicsworkshop.github.io/slides/BAICS_49.pdf` exists with an ID past the
   43-paper range reviewed here (`baics_0`–`baics_42`) — plausibly an
   invited-talk deck rather than a submitted paper, but not opened, so
   `[unverified]`. A targeted web search for 2021/2022/2023 editions under
   the BAICS name returned nothing (see search below), which is evidence of
   absence but not proof of it — workshops sometimes rebrand or move without
   a forwarding link. **Treat "43 papers" as the complete population of
   *this* site's *2020* edition, not as a claim that no other BAICS-adjacent
   workshop papers exist anywhere.**
2. **Abstracts were read from the PDFs directly for exactly 7 of 43 papers**
   (the Tier 1 paper in full, six page-1 abstract reads for the strongest
   Tier 2 candidates). The remaining 36 were triaged from title and the
   enumeration order/session/track metadata alone. A title-only triage can
   miss a paper whose abstract reveals a closer connection than its title
   suggests — this is the same risk `SHAPE_AUDIT.md` §9 names for its own
   grep-shaped blind spots, applied here to titles instead of grep hits.
3. **The Tier 1 paper's own validation is illustrative, not benchmarked**,
   and this document says so throughout rather than only here: no F1,
   accuracy, or runtime comparison against a competing method exists in the
   paper (contrast DeepGAR's +15% F1 / 13× speed, already reviewed in the
   design spike). The 4.7% reverse-transfer number is a cognitive-plausibility
   replication of a 1989 human-subjects finding, not a machine-learning
   result, and should not be quoted as if it were.
4. **No mechanism named in this document was tested against this repo's own
   codebooks, rules, or seeds.** Every "what this would mean for this
   codebase" claim is `[unverified]` in exactly the sense the design spike's
   own confidence-flagging convention uses that word — read from the
   external paper's stated method, not run.
5. **Tier 2 and Tier 3 judgements are triage, not review.** A paper placed
   in Tier 2 with one or two sentences, or in a Tier 3 subject bucket with
   no sentences at all, received exactly the depth the task specified —
   this is not a claim that a deeper read of any Tier 2/3 paper would find
   nothing; it is a claim that, at the depth actually applied, nothing
   surfaced that bears on a specific mechanism this project is building.

**Search performed for §edition-completeness:** `WebSearch` for
`"Bridging AI and Cognitive Science" BAICS workshop 2021 OR 2022 OR 2023`
returned only 2020-edition and general-audience results (the ICLR 2020
program page, the `#BAICS2020` Twitter/X account, an unrelated 2021 arXiv
survey that happens to share phrasing in its title, and unrelated
same-acronym-space AI/cognition workshops at other venues) — no distinct
later BAICS edition surfaced.
