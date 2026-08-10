# How does the brain process code — and what does that imply for a graph-native program-synthesis architecture?

**Research spike, literature only. 2026-08-01.**
No code was changed. This document is the sole artefact.

> **Merge note.** Two spike tracks wrote into this file concurrently. §8.1–8.2, §8.3(1)–(3),
> §8.4–8.6 and §9 are the first track's; §0–§7, §8.0, §8.2b, §8.3(4)–(6)+(0), §8.4b–8.4c, §9b and
> §10 are the second's. Where they disagreed the disagreement is recorded rather than smoothed
> over — see §1.1 (the grade on "code is not language"), §1.4b (the 2024 multivariate reversal
> that prompted the regrade), §5.5 (Prat et al. downgraded [B] → [C] with a retraction noted in
> §8.4b), and the ~1,900-vs-~3,000 gated-check discrepancy flagged in §8.0.

---

## 0. How to read this document

### 0.1 Scope

Seven questions were asked (language network vs elsewhere; working memory / executive
control; mental simulation; expertise; code vs NL vs math/logic; identifiers; production),
followed by a synthesis section mapping robust findings onto design consequences for the
jabberwock program-synthesis architecture, *including the findings that contradict it*.

### 0.2 Evidence grades used throughout

The programming-neuroscience literature is **small, underpowered, and methodologically
heterogeneous**. Typical n is 11–31. There is essentially no direct replication culture.
This document therefore tags every claim:

| Grade | Meaning |
|---|---|
| **[A]** | Multiple independent labs, converging methods, n adequate, or a preregistered/large-scale design. Safe to build on. |
| **[B]** | One strong study (good design, localizer-based or MVPA, n ≥ 15) with at least partial independent support. Build on with a hedge. |
| **[C]** | Single study, small n (< 20), whole-brain group analysis without functional localizers, or reverse-inference-heavy interpretation. Treat as a hypothesis. |
| **[D]** | Contested, failed to replicate, or an accepted null presented as a positive finding. Do not build on. |

### 0.3 The one methodological fact that explains most of the field's disagreement

**Different baselines produce different answers, and almost every apparent contradiction in
this literature reduces to a baseline choice.** Specifically:

- **Siegmund's line (Passau/Magdeburg/Chemnitz)** contrasts *code comprehension* against
  *syntax-error hunting on the same code*. Both conditions involve reading identifiers and
  keywords, so that shared load is subtracted out — but the contrast is a *whole-brain group
  analysis* interpreted via **reverse inference from Brodmann areas to cognitive processes**
  ("BA44 is a language area, therefore language is involved"). Reverse inference is the known
  weak link: BA44/BA21 are also multiple-demand and sequence-processing regions.
- **Fedorenko's line (MIT)** uses **individual-subject functional localizers**: each
  participant's *own* language network and *own* multiple-demand network are identified with
  independent tasks, then the code response is read out of those regions. Baseline is a
  content-matched **sentence** condition and a nonword condition. This method is far more
  conservative about attributing activity to "the language network," and it is the reason MIT
  reports near-zero language involvement where Passau reports BA21/44/47.
- **Bedny's line (Johns Hopkins)** uses whole-brain plus MVPA against a *scrambled-code*
  control and finds a **left-lateralized** fronto-parietal code network overlapping formal
  logic.

When you see "the field disagrees," the first question to ask is: *localizer or group
analysis? what was subtracted?* Almost always that settles it.

---

## 1. Is code processed by the language network, or elsewhere?

### 1.1 The short answer as of 2026

**Comprehension of short code snippets is carried primarily by the domain-general
multiple-demand (MD) / fronto-parietal executive system. [A]** Every study agrees on this,
across labs, methods and baselines, with large effects (β ≈ 1.0–2.2).

**The popular corollary — "and NOT by the language network" — must be graded lower, at [B], and
it has been complicated since 2024 by the very labs that established it.** Three conditions have
to travel with it, and in practice they never do:

1. **It is a UNIVARIATE claim.** Multivariately, the picture reverses (§1.4b).
2. **In Ivanova's Python experiment the language network DID respond significantly above the
   nonword floor (β = 0.78, p < 0.001).** The strong "not language" reading rests on the
   **ScratchJr null (β = 0.15, p = 0.29, n = 19)** — the condition where text was stripped out.
   That is a plausible inference (Python's response reflects reading, not code structure), but it
   is an inference **from an underpowered null with no equivalence test**.
3. **The two 2020 papers agree only on the NEGATIVE claim and disagree on nearly every positive
   one** — logic-vs-MD, laterality, which network is the story. The eLife editor's own note is
   that they "replicated each other" specifically on the language null.

**Where the language network is best falsified is IDENTIFIER SEMANTICS (§6). Where it is least
falsified is early structural/surface processing (§1.4b, §5.7).**

**Also unresolved as of 2026: whether "MD" is even the right unit** — Kean et al. (2026) report
that *deductive* reasoning draws on regions distinct from **both** the language network **and**
MD (§5.3b).

### 1.2 The primary evidence

**Ivanova, Srikant, Sueoka, Kean, Dhamala, O'Reilly, Bers & Fedorenko (2020), "Comprehension
of computer code relies primarily on domain-general executive brain regions", *eLife* 9:e58906.**
<https://elifesciences.org/articles/58906> **[A]**

- Two fMRI experiments. Experiment 1: **n = 24**, Python, 72 problems (math and string
  manipulation × sequential / for-loop / if-statement structures). Experiment 2: **n = 19**,
  ScratchJr (graphical), 24 problems at three difficulty levels. Individual-subject language
  and MD localizers.
- **MD system:** code > content-matched sentence problems (Python β = 1.03, p < 0.001;
  ScratchJr β = 1.38, p < 0.001); code > nonword control (Python β = 2.17; ScratchJr β = 1.23).
  **Bilateral** — "neither Python nor ScratchJr problems showed a left-hemisphere bias."
- **Language system:** Python code elicited a response *substantially weaker* than
  content-matched sentences (β = 0.98 for the sentence advantage, p < 0.001). ScratchJr code
  produced **no** significant response above the nonword control (β = 0.15, p = 0.29).
- **The identifier manipulation is the decisive one for our purposes.** They contrasted
  Python code with **English identifiers vs Japanese identifiers** (non-comprehensible to the
  monolingual English participants). Effect of identifier language on the language network:
  **β = 0.03, p = 0.84 — nothing.** The authors conclude the language system's (weak) Python
  response "was not driven by semantically transparent identifiers."
- Authors' own caveats: participants had only a few years of experience; stimuli were "short
  and only included a few basic elements of control flow"; no functions, objects, or
  multi-component programs. Exploratory proficiency correlations were all non-significant
  (small-n caveat).
- The same result set was later re-presented to the software-engineering community as
  Srikant et al. (2023), "Program Comprehension Does Not Primarily Rely On the Language
  Centers of the Human Brain", arXiv:2304.12373 — **this is not an independent replication,
  it is the same 43 participants repackaged.** Anyone citing both as two data points is
  double-counting.

**Liu, Kim, Wilson & Bedny (2020), "Computer code comprehension shares neural resources with
formal logical inference in the fronto-parietal network", *eLife* 9:e59340.**
<https://elifesciences.org/articles/59340> **[B]**

- **n = 15 expert programmers** (mean 11 years' experience, 5.7 years Python) — a genuinely
  expert sample, unlike Ivanova's.
- Real Python code vs scrambled "fake code" recruited a **left-lateralized** network: lateral
  PFC (mid/inferior frontal gyri, inferior frontal sulcus — mainly BA44/BA46), parietal cortex
  (IPS, angular and supramarginal gyri, BA7), and posterior MTG (p < 0.01 FWER).
- **MVPA: `for` vs `if` functions decodable** at PFC 64.7%, IPS 67.4%, pMTG 68.4% (all
  p < 0.001); early visual cortex 55.7% (p = 0.015 — i.e. a small visual confound exists but
  is far below the fronto-parietal effect).
- **Code overlapped most with formal logic** (logic > math > language), significantly more
  than with any other task tested.
- **Language network:** minimal. Overlap only in parts of IFG and posterior STS/MTG, "on
  average low," varying considerably across participants — **only half the participants showed
  above-chance overlap.**
- **The genuinely surprising result:** code was strongly **left-lateralized**, and the
  *lateralization index of code correlated with the lateralization index of language across
  individuals, R² = 0.658, p < 0.001* — even though the two barely overlapped functionally.
  Something organizes code and language onto the same hemisphere without them sharing tissue.
  This is unexplained and is a live research question.
- Authors' caveat: n = 15 is small, and differences from Ivanova "should be interpreted with
  caution and replicated."

**Note the tension between the two 2020 papers: Ivanova found code BILATERAL in MD; Liu found
it LEFT-LATERALIZED. [D] on lateralization specifically.** The likely reconcilers are sample
expertise (Liu's were experts, Ivanova's were not), the control condition (scrambled code vs
content-matched sentences), and stimulus modality. Do not treat "code is left-lateralized" or
"code is bilateral" as settled.

**Liu, Y.-F. & Bedny, M. (2025), "Learning to program 'recycles' preexisting frontoparietal
population codes of logical algorithms", *Journal of Neuroscience* 45(45):e0314252025.**
<https://pmc.ncbi.nlm.nih.gov/articles/PMC12590113/> **[B] — and the most architecturally
interesting paper in this literature.**

- **n = 22** programming-naive college students, scanned **before and after** a one-semester
  Python course. Longitudinal within-subject. Pseudocode (plain English) at PRE; Python code
  and pseudocode at POST.
- `for` vs `if` algorithms were decodable from fronto-parietal cortex **BEFORE any programming
  instruction**, from plain-English pseudocode: IPS p = 4.9 × 10⁻⁵, PFC p = 2.0 × 10⁻⁶. After
  instruction, the same distinction was decodable from Python: IPS p = 1.8 × 10⁻⁴,
  PFC p = 9.2 × 10⁻⁵.
- **Representational similarity between PRE-pseudocode and POST-code was significant**
  (IPS Kendall's τ = 0.0162, p = 6.9 × 10⁻⁴; PFC τ = 0.0196, p = 5 × 10⁻⁴) — *the same neural
  populations encode the algorithm before and after learning the language it is written in.*
- Language-network overlap: Dice 0.17–0.18, **even though the pseudocode was plain English.**
- Left-lateralized (LI −0.56 to −0.61).
- Honest limitations the authors state: τ effects are numerically tiny; beginner-level Python
  may preferentially engage recycled representations; **"no clear evidence of representational
  change"** — one semester may be too short to see the circuit specialize.

**Interpretation, stated carefully:** learning to program did not build a code representation.
It attached a notation to a **pre-existing, language-independent representation of control
constructs.** The construct vocabulary is prior; the syntax is a skin.

### 1.3 The Siegmund line, and why it looks like it disagrees

**Siegmund, Kästner, Apel, Parnin, Bethmann, Leich, Saake & Brechmann (2014), "Understanding
understanding source code with functional magnetic resonance imaging", *ICSE 2014*.**
<https://www.cs.cmu.edu/~ckaestne/pdf/icse14_fmri.pdf> **[C]**

- **n = 17.** Java snippets of 23 standard first-semester algorithms; task = determine the
  program's output. Control = find three injected syntax errors in the *same* snippets
  ("located without understanding the execution of the program — they merely require some kind
  of pattern matching").
- Result: five left-hemisphere clusters — **BA6, BA21, BA40, BA44, BA47**.
- **Read this result carefully. BA6 (middle frontal gyrus) and BA40 (inferior parietal lobule)
  ARE multiple-demand regions.** The authors themselves interpret them as *working memory
  (phonological loop), division of attention, and problem solving*, and explicitly cite
  Wisconsin Card Sorting and Raven's Progressive Matrices as the comparison tasks. Two of
  Siegmund's five clusters are the MD system under a different vocabulary. The disagreement
  with MIT is narrower than it is usually reported.
- Only **BA21, BA44, BA47** carry the "language" claim, and the authors' interpretive move is
  explicit reverse inference plus an argument from **artificial grammar learning**: "artificial
  languages are based on formal grammars and limited sets of symbols... we *conjecture* that
  one part of program comprehension likely involves language processing." That is a conjecture
  in the paper's own words.
- **A detail that is almost always omitted when this study is cited, and which matters
  enormously here: Siegmund et al. deliberately OBFUSCATED the identifiers.** From the paper:
  "To avoid influences due to domain knowledge and possible brain activation caused by memory
  retrieval, we obfuscated identifier names, so that participants needed bottom-up
  comprehension... the variable `result` does not give a hint about its content... but only
  about its purpose." So whatever BA21/44/47 are doing in Siegmund's data, **it is not
  identifier semantics** — it is keyword/token-level reading plus structured-sequence
  processing. That is *consistent* with Ivanova's English-vs-Japanese null, not in conflict
  with it.

**Siegmund, Peitek, Parnin, Apel, Hofmeister, Kästner, Begel, Bethmann & Brechmann (2017),
"Measuring Neural Efficiency of Program Comprehension", *FSE 2017*, 140–150.**
<https://www.infosun.fim.uni-passau.de/publications/docs/SPP+17.pdf> **[C], with an important
internal null**

- **n = 11** (14 datasets after 3 repeat sessions). Replicated the 2014 activation pattern
  (BA6, 21, 40, 44 left; BA39 bilateral).
- **Main positive result:** comprehension *based on semantic cues* (top-down, primed, familiar
  snippets) produced **lower activation in all areas** than bottom-up comprehension — "neural
  efficiency." Response times were matched by design, so this is not a time-on-task artefact.
  BA39 (angular gyrus) flipped sign: **deactivated** during semantic-cue comprehension,
  activated during bottom-up.
- **The null nobody cites: the beacon manipulation did nothing.** Four conditions crossed
  beacons (present/absent) × layout (pretty/disrupted). "Overall, we found no significant
  differences." The authors' own discussion offers three explanations, the third of which is
  worth quoting because it is unusually candid: participants' expertise was too low to have
  plans, *or* "programming plans are embedded in the same neural circuits as comprehension so
  we cannot see differences," *or* **"the theory is simply wrong."**
- They also flag no memory-retrieval signature during semantic-cue comprehension — i.e. **no
  neural evidence of schema retrieval where plan theory predicts it.**

**Peitek, Apel, Parnin, Brechmann & Siegmund (2021), "Program Comprehension and Code
Complexity Metrics: An fMRI Study", *ICSE 2021*, 524–536 (ACM SIGSOFT Distinguished Paper).**
Replication package: <https://github.com/brains-on-code/fMRI-complexity-metrics-icse2021> **[C]**

- **n = 19.** 41 code-complexity metrics regressed against activation in four regions.
- Best correlations: **Halstead vs BA6 r ≈ 0.60**; **BRANCH (control-flow branching) vs BA21
  r ≈ 0.56**. The authors' own summary is that complexity metrics explain programmers'
  cognition "to a limited degree." Note that ~0.6 on n = 19 across 41 candidate metrics × 4
  regions is a multiple-comparisons-shaped result; treat the specific metric rankings as
  exploratory.
- The BRANCH → BA21 association is nonetheless *interesting* and converges with Srikant et al.
  (below): the temporal "language-ish" region tracks **control-flow structure**, not identifier
  meaning.
- **The most important number in this paper is a NULL, and it is discussed in §3.3:**
  **McCabe cyclomatic complexity — the count of independent execution paths — correlates with
  BOLD at τ ≈ .04–.09 across all four regions, i.e. essentially zero**, while **DepDegree (a
  data-flow dependency measure) reaches τ = .32–.41.** The authors: *"Simple control-flow metrics
  (e.g. number of branches) predict cognitive load better than more complex control-flow metrics
  (e.g. McCabe)"*, and McCabe correlates with neither response time nor correctness.

### 1.4 What EXACTLY does the language network contribute? The best current answer

The most informative study is not a localization study at all — it is a decoding study.

**Srikant, Lipkin, Ivanova, Fedorenko & O'Reilly (2022), "Convergent Representations of
Computer Programs in Human and Artificial Neural Networks", *NeurIPS 2022*, 18834–18849.**
<https://proceedings.neurips.cc/paper_files/paper/2022/hash/77b5aaf2826c95c98e5eb4ab830073de-Abstract-Conference.html>
**[B] — the load-bearing paper for our architecture question.**

Re-analysis of the Ivanova et al. Python fMRI data, decoding *code properties* from each brain
system, plus alignment of brain representations with code-model representations (CodeBERTa,
CodeTransformer, XLNet, code2vec, bag-of-words, and a "Token Projection" random-embedding
baseline that captures *token presence only*).

Findings, in order of relevance to us:

1. **The MD system preferentially encodes DYNAMIC / runtime-analysis properties** —
   significantly better than the Language system does, and significantly better than it
   encodes *static* properties. Quoting the paper: "the MD system decodes the dynamic analysis
   property better than the Language system... [and] significantly better than the static
   analysis property."
2. **The Language system significantly encodes STATIC and CONTROL-FLOW properties** — i.e.
   syntactic/structural facts about the program. So the language network is not idle; it is
   carrying *structure*, not *meaning-of-names*.
3. **Variable-name language (English vs Japanese identifiers) was the ONE property that could
   not be decoded from either system**, consistent with Ivanova et al.'s univariate null.
4. **A large sobering caveat the authors state plainly:** for both MD and Language, the
   brain→code-model mappings largely **do not significantly exceed the token-projection
   baseline**, i.e. "the information being decoded from brain activations in these two regions
   is driven at least by the information conveyed by tokens in the programs." Only in the
   *property-specific* analysis does MD show a profile matching complex models rather than
   token-level ones. Read the headline as *directionally* right and *magnitudinally* modest.
5. Their own design recommendation, which is worth noting because it is the same conclusion we
   reached empirically: "modeling **dynamic runtime information** as well as static code
   structure should be explored" — i.e. static language modelling of code is insufficient.

**So: the honest answer to "what does the language network contribute?"**

| Candidate contribution | Verdict |
|---|---|
| Identifier / lexical semantics | **Not supported.** English-vs-Japanese null in both univariate (β = 0.03, p = 0.84) and MVPA analyses; Siegmund obtained his "language" clusters *with obfuscated identifiers*. **[B] for the null** |
| Syntactic / structural sequence processing | **Weakly supported.** LS decodes control-flow and static-analysis properties (Srikant 2022); BRANCH ↔ BA21 (Peitek 2021); BA44 is a structured-sequence region. But effects hover near token-level baselines. **[C]** |
| Token-level surface reading | **Supported and probably the bulk of it.** **[B]** |
| Semantic integration / prediction (language-*like*, not necessarily language-*network*) | **Emerging.** See §1.5. **[C]** |
| Nothing at all | **Too strong.** ScratchJr null is consistent with "nothing for non-textual code"; the Python result is small but non-zero. |

### 1.4b THE UNDER-CITED REVERSAL: multivariately, language cortex carries code structure — and
carries it EARLIER

**Liu, Y.-F., Wilson, C. & Bedny, M. (2024), "Contribution of the language network to the
comprehension of Python programming code", *Brain and Language* 251:105392.**
<https://doi.org/10.1016/j.bandl.2024.105392> **[B] — the most important paper in this dispute
since 2020, and it is systematically under-cited, including by people quoting its own authors'
2020 result.**

- A linear SVM **decoded `for` from `if` in lateral temporal LANGUAGE cortex — with HIGHER
  accuracy than anywhere else in the brain.**
- Decoding was **not** driven by the surface words `for`/`if`, but by **compositional program
  properties**.
- **Language cortex responded EARLIER than fronto-parietal regions.**
- Proposed account: the language network forms an initial **"surface meaning"** representation
  that feeds the reasoning network.

**Univariate weakness is not representational absence.** A region can carry decodable, structured
information about code while showing a small mean BOLD response — that is a routine dissociation
in the MVPA literature, not an exotic one. **This does not overturn §1.1's MD result; it
overturns the strong form of the corollary.** The honest 2026 statement is:

> Code comprehension is *carried* by fronto-parietal executive cortex. The language network is
> *not idle* — it appears to compute an early surface-structural representation that the
> reasoning network consumes. What it demonstrably does NOT do is process identifier meanings, or
> evaluate whether the program is correct.

*(This same paper is why the parallel spike track and this one initially graded §1.1 differently.
The reconciliation above is the merged position.)*

### 1.5 The contrary evidence — take it seriously

Three findings push back on the clean "MD not language" story. None of them overturn it, but
an honest review has to put them on the table.

**Bergum, Maurer, Peitek, Bader, Mecklinger, Demberg, Siegmund & Apel (2026), "Fixation-related
potentials reveal that confusing program code elicits a late frontal positivity",
*Scientific Reports* 16:16833 (arXiv:2412.10099).** <https://arxiv.org/abs/2412.10099> **[C]**
- EEG fixation-related potentials during naturalistic code reading. "Atoms of confusion"
  (code that is correct but violates programmer intuition) elicited a **late frontal positivity
  ~400–700 ms** after first fixation on the atom.
- The authors explicitly liken this to the ERP response to **"unexpected but plausible words in
  sentence context"** and argue for "similar neurocognitive mechanisms... semantic integration
  and situation model updating."
- Caveat: n and effect sizes are not in the abstract; a late frontal positivity is *not*
  diagnostic of the language network (frontal positivities are heavily associated with
  domain-general conflict/updating). This is suggestive of **predictive processing over code**,
  which is a different and weaker claim than "the language network processes code."

**"Dual neural foundations of coding cognition: Language comprehension scaffolds initial
learning before mathematical systems engage" (2026), *NeuroImage / Elsevier*, PII
S105381192600368X.** <https://www.sciencedirect.com/science/article/pii/S105381192600368X>
**[C/D]**
- **n = 29 coding-naive adults.** Claim: coding "robustly engaged core language regions,
  including Wernicke's area and the angular gyrus, with activation patterns **statistically
  indistinguishable** from those during natural language comprehension," while *also* recruiting
  math-associated regions (right DLPFC, parietal, sensorimotor). Temporally: early phase
  overlaps language, late phase shifts to fronto-parietal executive.
- **Full citation, verified late in this spike: Huang, X., Yang, W. & Looi, C.K. (2026),
  *NeuroImage* 338:122053, PMID 42285449. The method is fNIRS, not fMRI.**
- **Four reasons to hold it at arm's length, and the first is the one people get wrong:**
  (i) **it is a within-session early/late contrast, NOT a training study — do not cite it as
  longitudinal**; (ii) **fNIRS cannot functionally resolve the language network** — "Wernicke's
  area" here is an atlas label, not that participant's language network; (iii) "statistically
  indistinguishable" is an **underpowered null read as identity**, with no equivalence test —
  precisely the inference our own standing rules forbid ("deltas within noise are not results");
  (iv) it **directly contradicts Ivanova et al. on the SAME ScratchJr paradigm** (β = 0.15,
  p = 0.29), where the method asymmetry favours Ivanova.
- **And Liu & Bedny (2025) — fMRI, genuinely longitudinal, across a real Python course — finds
  the REASONING substrate present from the start.** Both cannot be straightforwardly right.
  **Do not build on this paper.**

**Prat, Madhyastha, Mottarella & Kuo (2020), "Relating Natural Language Aptitude to Individual
Differences in Learning Programming Languages", *Scientific Reports* 10:3817.**
**[C] — see §5.5, where this is examined properly and DOWNGRADED.**
- Usually cited as "language aptitude beats math aptitude for learning to program." **The paper's
  own numbers do not support the headline:** fluid reasoning (34% averaged unique variance) is
  roughly **twice** language aptitude (17%) and topped two of three models; the zero-order
  correlations for language and numeracy are **near-identical** (.56/.52, .54/.54, .45/.42); and
  "math aptitude" was **8 items of a health/risk numeracy scale**, not a mathematical-reasoning
  test.
- **The follow-ups point away from it:** Kuo et al. (2022, n = 80) — acquired declarative
  knowledge dominated; Graafsma et al. (2023, **n = 282**) — math latent β = .493 vs language
  latent β = .057; Finke et al. (2022, **n = 132, pre-registered**) — figural reasoning, not
  arithmetic, not language; **Hartmann et al. (2024) — the one experimental transfer test is
  NULL.**
- **This is a conditions-stripped claim that has propagated widely, including into the first
  draft of this document.**

**Endres, Karas, Hu, Kovelman & Weimer (2021), "Relating Reading, Visualization, and Coding for
New Programmers: A Neuroimaging Study", *ICSE 2021*.** <https://arxiv.org/abs/2102.12376> **[C]**
- **n = 31 novices, fNIRS.** Coding, prose reading and mental rotation were "mentally distinct
  for novices," and **the neural distance between prose and coding was greater than between
  spatial visualization and coding.** Novices showed more activation in spatial-ability regions
  than experts in prior work.
- **This directly contradicts the "language scaffolds early learning" claim above**, in the
  same population (novices). Two studies, opposite directions, both n ≈ 30, both single-shot.
  The honest state is **unresolved [D]**, and anyone asserting either direction is
  over-reading.

### 1.6 The meta-analysis

**Ikutani, Itoh & Kubo (2021), "The neural bases of program comprehension: a coordinate-based
fMRI meta-analysis", bioRxiv 2021.04.15.439937.**
<https://www.biorxiv.org/content/10.1101/2021.04.15.439937v1.full> **[C] — and it comes down on
the LANGUAGE side, so it belongs in §1.5 as much as here.**

- **7 studies, 9 contrasts, 61 peaks, mean n = 19.5 ± 5.6.**
- Three consistent clusters: **left IFG pars triangularis, left posterior MTG, right middle
  frontal gyrus.**
- Conclusion: program comprehension "**mainly recycles the language-related networks**."
- **Two reasons to hold it loosely.** (i) Pooling **7 studies at mean n ≈ 20** is badly
  underpowered for ALE, and it remains a **preprint** — I found no journal version. (ii) It
  **did not recover the left parietal regions (angular gyrus / IPL) that Siegmund, Liu, Ivanova
  AND Peitek all report** — a conspicuous miss for a method whose job is to find convergence.
- Note the cluster set straddles the divide anyway: left IFG + pMTG are what Siegmund and Liu
  both report, and **right MFG is squarely MD**. Calling that "recycling the language network"
  is an interpretive choice, not a result.

**The field's split is genuinely 4-vs-4.** Language side: Siegmund (2014, 2017), Ikutani (2021
eNeuro, 2021 meta-analysis), Prat (2020). MD/fronto-parietal side: Ivanova (2020), Liu & Bedny
(2020, 2025), Floyd (2017), Krueger (2020). **The most likely moderator is TASK — output
prediction/execution vs syntactic inspection vs code review — and no one has varied it
systematically.** The second is localizer choice: Liu et al. localised language/math/logic
*relative to each other*, which by construction suppresses shared regions.

---

## 2. Working memory and executive control: what the MD system does for code

### 2.1 What the MD system is

The multiple-demand network is a **bilateral fronto-parietal (plus insular and
medial-frontal) system**: middle frontal gyrus, inferior frontal sulcus, anterior insula,
intraparietal sulcus, supplementary motor area, anterior cingulate. It responds to *difficulty
across domains* — working memory, attention, cognitive control, novel problem solving — and its
activity indexes fluid intelligence. Canonical statements: **Duncan (2010), "The multiple-demand
(MD) system of the primate brain: mental programs for intelligent behaviour", *Trends in
Cognitive Sciences* 14(4):172–179**; **Assem, Blank, Mineroff, Ademoglu & Fedorenko (2020),
"Activity in the fronto-parietal Multiple-Demand network is robustly associated with individual
differences in working memory and fluid intelligence", *Cortex* 131:1–16.** **[A]**

Duncan's framing is the one worth importing: the MD system assembles and executes **"mental
programs"** — it decomposes a task into sub-goals, holds the currently relevant sub-goal, binds
the currently relevant content to it, and steps through. **"Goal neglect"** after frontal damage
— failing to apply a rule you can state perfectly well — is the signature deficit. This is,
almost literally, an interpreter with a control stack.

### 2.2 The dissociation from language is itself well-established

**Diachek, Blank, Siegelman, Affourtit & Fedorenko (2020), "The domain-general multiple demand
(MD) network does not support core aspects of language comprehension: a large-scale fMRI
investigation", *Journal of Neuroscience* 40(23):4536–4550.**
<https://www.jneurosci.org/content/40/23/4536> **[A]**
The MD network is engaged by *task demands layered on top of* comprehension (button presses,
memory probes, judgements), but **during naturalistic comprehension of even syntactically
complex language it is not engaged.** This matters for us in a specific way: it means the
MD/language dissociation is not an artefact of code studies — it is a general property of the
brain, established on large samples in the language domain first.

### 2.3 What MD is doing for code specifically

- **Variable/state tracking.** Siegmund et al. (2014) attribute BA6/BA40 to verbal-numeric
  working memory — "participants had to keep the values of variables that the source code was
  manipulating in mind... when loops were part of the source code, participants had to keep the
  values of several loop iterations in mind." **[C]** (interpretive, but the most natural read).
- **Runtime/dynamic properties.** Srikant et al. (2022) is the direct evidence: MD decodes
  dynamic-analysis properties better than the language system and better than it decodes static
  properties. **[B]**
- **Algorithm identity.** Liu & Bedny (2020, 2025): `for` vs `if` decodable from IPS/PFC at
  ~65–68%, and decodable *before instruction* from pseudocode. **[B]**
- **Difficulty scaling.** Ivanova et al.: MD response scaled with ScratchJr difficulty level;
  Peitek et al. (2021): Halstead ↔ BA6 r ≈ 0.60. **[C]**

### 2.4 Capacity limits and chunking in programmers — honestly, this is thin

There is no good *neuro* work on working-memory capacity limits specific to code. The
behavioural/cognitive-load literature is mostly indirect:

- **Issever, Catalbas & Duran (2023), "Examining Factors Influencing Cognitive Load of Computer
  Programmers", *Brain Sciences* 13(8):1132.** <https://pmc.ncbi.nlm.nih.gov/articles/PMC10452396/>
  **n = 216** (EMIP eye-tracking dataset), canonical correlation r = 0.581, p < 0.001. Largest
  contributors to cognitive load: **age (18.0%)** and — a genuinely interesting finding —
  **linguistic distance from the programmer's native language to English (15.4%)**; gender
  negligible (0.26%). It does *not* measure working memory directly; eye-movement features are
  a proxy. **[C]**
- **Peitek, Bergum, Rekrut, Mucke, Nadig, Parnin, Siegmund & Apel (2022), "Correlates of
  Programmer Efficacy and Their Link to Experience: A Combined EEG and Eye-Tracking Study",
  *FSE 2022*** (arXiv:2303.07071). <https://arxiv.org/abs/2303.07071> **n = 37**, up to 32 Java
  snippets. **"Programmers with high efficacy read source code more targeted and with lower
  cognitive load."** And: **"commonly used experience levels do not predict programmer efficacy
  well"** — self-estimation and learning eagerness predicted better than years of experience.
  **[B]** — this is a well-designed study with a useful and slightly deflationary result.
- The generic "4 ± 1 chunks" capacity claim is imported from mainstream WM research
  (Cowan), not established on code. Cognitive-Driven Development and similar frameworks assume
  it. **Do not treat "programmers chunk into 7±2 / 4±1 code units" as an established
  code-specific finding — it is an analogy. [D]**

**Design-relevant summary of §2:** the brain's code engine is the same fronto-parietal machinery
that runs Raven's matrices and holds sub-goals. Its known signature is *stepping through a
program with state*, not *retrieving a library*.

---

## 3. Mental simulation and execution ("tracing")

**This is the closest analogue to our ProgEval verdict layer, so the honest state of evidence
matters more here than anywhere else. Summary up front: the BEHAVIOURAL evidence for tracing is
good but is almost entirely about CS1 novices and is strongly TASK-CONDITIONAL; the NEURAL
evidence for step-by-step simulation is ONE decoding result, and every DIRECT manipulation of
execution structure has come out NULL.**

### 3.1 Behavioural evidence that programmers trace

**Lister, Adams, Fitzgerald, Fone, Hamer, Lindholm, McCartney, Moström, Sanders, Seppälä, Simon
& Thomas (2004), "A multi-national study of reading and tracing skills in novice programmers",
*ITiCSE-WGR / SIGCSE Bulletin* 36(4):119–150.**
<https://cseweb.ucsd.edu/~bsimon/pubs/papers/2004iticseworkinggroupfinal.pdf> **[B]**
**n = 941 contributed data; 556 received all 12 MCQs; 7 countries; 37 think-alouds; 56 students'
"doodles" analysed.** The headline association (Table 4.2), % correct by doodle type:
Synchronized Trace **77%** (n = 73), Trace **75%** (n = 215), Odd Trace 78% (n = 23), Position
64%, Number 70%, **Blank page 50%** (n = 256), Underlined 52%.
**Evidence quality: observational and NON-CAUSAL.** The doodle→correctness association is
confounded by ability (better students both trace *and* answer correctly). One institution
supplied > half the performance data.

**Lopez, Whalley, Robbins & Lister (2008), "Relationships between reading, tracing and writing
skills in introductory programming", *ICER '08*, 101–112.**
<https://doi.org/10.1145/1404520.1404531> — stepwise regression: **tracing iterative code +
"explain in plain English" accounted for ~46% of the variance in code-writing performance.**
Proposes a skill hierarchy: constructs → explain/Parsons/trace → write. **[B]**
Replication status is genuinely mixed and worth stating precisely:
- **Venables, Tan & Lister (2009), *ICER '09*** — *partial*. "Broadly consistent," **but**
  "student performance on explaining code was hard to characterize, and the strength of the
  relationship between explaining and code writing is particularly sensitive to the specific
  questions asked." **The tracing→writing link replicates better than the explaining→writing
  link.**
- **Lister, Fidge & Teague (2009), *ITiCSE '09*** — **the strongest replication**: new
  institution, **Python** (previous work was Java/C++), non-parametric analysis. "Students who
  cannot trace code usually cannot explain code, and… students who perform reasonably well at
  code writing have usually acquired the ability to both trace and explain."

**Cunningham, Blanchard, Ericson & Guzdial (2017), "Using Tracing and Sketching to Solve
Programming Problems", *ICER '17*, 164–172.**
<https://www.gvu.gatech.edu/sites/default/files/related_project_files/p164-cunningham.pdf>
**[B] — and the most important qualification in this whole section.**
- **n = 159 attended, 135 analysed, sketch-coded on a random subset of 65.** Replicated the
  core: Trace **82.1%** (n = 95) vs **Blank 60.7%** (n = 135).
- Sketching rate varied 44% → 95% across problems, tracking the number of variable states —
  "students have some idea when it is a good idea to sketch."
- **The task-conditionality result: on code-FIXING problems, sketchers scored LOWER than
  non-sketchers; on ordering/writing problems, Blank averaged 77.7% (n = 165) — higher than most
  sketch categories.** Tracing helped enormously on *output prediction* (up to ~50 pp on the
  three-variable problem) and hurt or was irrelevant elsewhere.
- **Incomplete traces performed no better than no sketching at all.**
- Failed to replicate two of Lister's categories: "Odd Trace" was Lister's *best* (78%) and this
  study's *worst* (55.6%, n = 9); **Synchronized Traces were not observed at all.**

**Xie, Nelson & Ko (2018), "An Explicit Strategy to Scaffold Novice Program Tracing",
*SIGCSE '18*, 344–349.**
<https://faculty.washington.edu/ajko/papers/Xie2018TracingStrategies.pdf> **[C] — the only
randomised intervention.** **n = 24** (11 control / 13 strategy), ~5 min of instruction in
line-by-line "memory table" tracing. Significant on Problem 4 (nested if/else, multiple
variables): **p = 0.021, common-language effect size 71%**; total score ~15% higher with 46%
less variability. **Confound the authors flag themselves: the CONTROL group had significantly
higher programming self-efficacy (p < 0.01).** They write "Replication is necessary."
Qualitative mechanism note: high performers "**write down intermediate values rather than try to
remember them**."

**Why novice tracing fails.** **Vainio & Sajaniemi (2007), *ITiCSE '07*, 236–240** —
qualitative; four failure modes, the first of which is mechanistically interesting:
**single-value tracing** (keeping only one "memory slot," the most recently modified value),
confusing function with structure, inability to use external representations, inability to raise
abstraction level. **Hassan & Zilles (2023), *SIGCSE '23*** — **n = 15** think-alouds; the
cleanest evidence that **tracing is UNDER-DEPLOYED rather than merely badly executed**: several
struggling students explained correctly *after the interviewer merely suggested tracing*, and
others succeeded once the interviewer *supplied a discriminating input*. This directly echoes
**Perkins & Martin (1986), "Fragile knowledge and neglected strategies in novice programmers"** —
"partial, hard to access, and often misused" knowledge that general strategic prompting
resolves. Thirty-seven years apart, same finding.

### 3.2 Working memory during mental execution — the most mechanistically direct study

**Crichton, Agrawala & Hanrahan (2021), "The Role of Working Memory in Program Tracing",
*CHI 2021*.** <https://arxiv.org/abs/2101.06305> **[B]**

- Four controlled experiments (Exp 1 n = 15; later experiments use a restricted-focus-viewer
  interface as a mouse-based proxy for foveation).
- **People hold ~7 variable/value pairs**, and **errors are predominantly SWAPS of
  variable↔value associations, not forgetting** — replicating Campbell & Charness's
  mental-arithmetic result in the programming domain. **This is a binding-failure account, not a
  capacity-decay account.**
- **Two strategies, roughly 50/50: *linear* (top-down, line-by-line) and *on-demand* (start at
  the bottom and trace UPWARD along data dependencies).** On straight-line code the on-demand
  strategy produced *more* WM errors; with functions the two were equivalent.
- Limitations the authors state: integers only, single-digit arithmetic, **immutable variables
  only** (i.e. the case where simulation is *easiest* — no in-place mutation), MTurk sample.

Note how well this dovetails with §4.5's Rist/Détienne result: **backward-from-the-goal along
data dependencies is the same strategy that appears when a schema is unavailable.**

### 3.3 Neural evidence for simulation — one positive decoding result, and a wall of nulls

**THE POSITIVE RESULT.** **Srikant, Lipkin, Ivanova, Fedorenko & O'Reilly (2022), NeurIPS.**
The "dynamic property" they decoded is literally **runtime steps — the number of instructions
executed.** Result: the **MD system decodes runtime steps significantly better than the Language
system does, AND significantly better than it decodes static (token/AST-node count) properties**
(paired t-tests, p < 0.05 FDR). A multi-system partial regression showed MD encodes information
**orthogonal to low-level visual features**. **[B]**
**Caveats that must travel with it:** this is *decoding*, not parametric BOLD scaling; n = 24,
single dataset, **no independent replication**; and the authors' own limitation — the stimuli
were "short snippets of procedural code with limited program properties."

**THE NULLS, which are collectively more informative than the positive result.**

1. **Ivanova et al. (2020) manipulated control-flow structure directly and found nothing.** MD
   responses did **not** vary meaningfully across sequential vs for-loop vs if-conditional
   problems (only a slight sequential effect, β = −0.20, p = 0.002). **[B null]**
2. **Peitek et al. (2021) is the decisive one. McCabe cyclomatic complexity — the number of
   independent execution paths — correlates with BOLD at τ = .04 (BA6), .09 (BA21), .07 (BA39),
   −.04 (BA44/45). Essentially zero everywhere, and no correlation with response time or
   correctness either. Meanwhile DepDegree — a DATA-FLOW dependency measure — reaches
   τ = .32/.41/.36/.22.** **[B]**
   **If comprehension were dominated by mentally running the program, path-count complexity
   should be the BEST predictor of neural load. It is the WORST. What predicts load is
   DATA-DEPENDENCY TRACKING.** This converges exactly with Crichton's swap-error finding: the
   bottleneck is *binding values to variables*, not *stepping through control flow*.
3. **Medeiros et al. (2021), *Sensors* 21(7):2338** (n = 26, EEG) report **mental-effort
   saturation as code complexity increases**, and that classic complexity metrics "do not
   accurately represent the mental effort involved." **[C]**

**Bottom line, stated plainly: there is NO published study that parametrically manipulates the
number of execution steps or loop iterations and shows monotonic MD scaling. The one supporting
result is a decoding analysis; every direct manipulation is null. This is the single
most-wanted missing experiment for our purposes.**

### 3.4 Spatial / motor / DMN "simulation" signatures — no embodied simulation found

**Huang, Liu, Krueger, Santander, Hu, Leach & Weimer (2019), "Distilling Neural Representations
of Data Structure Manipulation using fMRI and fNIRS", *ICSE '19*** (Distinguished Paper).
<https://web.eecs.umich.edu/~weimerw/p/weimer-icse2019-preprint.pdf> **[B] — n = 76, the largest
neuroimaging study in software engineering.**

- Tasks: list / array / tree manipulation vs **mental rotation** (the canonical spatial probe).
- **Code > Mental rotation yielded NO significant activations after FDR.**
- **Mental rotation > Code** revealed robust **default-mode-network** activation (bilateral
  PCC/BA31, mPFC, sgACC, left AG/TPJ, pSTS/MTG) — and the DMN is, as the authors note, "heavily
  implicated in various types of mental simulation."
- **"95% of voxels were statistically indistinguishable between Mental and Tree tasks."**

**Read this carefully, because it cuts against the intuitive story.** Data-structure manipulation
and mental rotation are neurally near-identical — but **where they differ, MENTAL ROTATION
recruits the simulation-associated network MORE than code does.** There is **no clean
demonstration of embodied/motor simulation during code comprehension anywhere in this
literature.**

### 3.5 Eye-tracking: do experts read in execution order?

**Busjahn, Bednarik, Begel, Crosby, Paterson, Schulte, Sharif & Tamm (2015), "Eye Movements in
Code Reading: Relaxing the Linear Order", *ICPC 2015*, 255–265.**
<https://researchonline.gcu.ac.uk/ws/files/24953094/ICPC2015_authors_version.pdf> **[C]**

- **n = 14 novices (101 code trials) + 6 professionals (21 trials).** Needleman–Wunsch alignment
  of gaze against two model orders: **Story Order** (top-to-bottom) vs **Execution Order**.
- Linearity: novices ~80% on natural language, ~70% on code; **experts ~60% on code.** Saccade
  length novices 1.86° vs experts 3.12° (U = 105, p < 0.001); element coverage novices 52.4% vs
  experts 41.3% (U = 84, p < 0.01).
- Dynamic N-W scores (novice / expert): Story Order **−12.82 / −113.62**; Execution Order
  **8.68 / −46.50**. Authors: "The Execution Order model better explains the experts' reading
  approach… **experts tend to trace at least parts of the code**. For novices… neither model is
  predominant."
- **THE CONFOUND, which the authors state themselves: the two groups read DIFFERENT PROGRAMS.**
  Novice stimuli were mostly straight-line, so story and execution order nearly coincide (mean
  N-W similarity between the two model sequences: **−1 for novice programs vs −71 for expert
  programs**). **This is expertise confounded with stimulus complexity.** Expert n = 6, 21
  trials; fixation-to-line mapping succeeded for only **72.7% of expert code** (the noisiest
  data in the study).
- **Replication:** Peachock, Iovino & Sharif (2017), HCII, is a direct C++ replication whose
  **results could not be retrieved in this spike — do not assume it confirmed Busjahn.**

**Honest verdict: what is well supported is the weaker claim — code is read markedly less
linearly than prose, and linearity DECREASES with expertise. The specific execution-order
attribution rests on one small study with a stimulus confound and is effectively unreplicated.**

### 3.6 Notional machines — the pedagogy side

**Sorva (2013), "Notional Machines and Introductory Programming Education", *ACM TOCE* 13(2),
Art. 8.** <https://dl.acm.org/doi/10.1145/2483710.2483713> — the definitive survey (307
citations), synthesising misconceptions, mental-models theory, phenomenography and threshold
concepts around the notional machine ("an abstract computer for executing programs of a
particular kind"). Origin: **du Boulay (1986), "Some difficulties of learning to program",
*JECR* 2(1):57–73**; du Boulay, O'Shea & Monk (1981), "The black box inside the glass box."

**Two claims from Sorva worth carrying into design:** (a) the notional machine should be an
*explicit* object, not an implicit one; (b) **some paradigms need MULTIPLE notional machines at
different abstraction levels** — i.e. "the" execution model is not unique. That second point is
a direct pedagogical statement of our own P7-A recursive-descent grain ladder.

Related: **Sajaniemi (2002), "Roles of variables"**, IEEE HCC — **nine roles cover 99% of
variables** in novice-level programs (fixed value, stepper, most-recent holder, most-wanted
holder, gatherer, transformation, follower, one-way flag, temporary). Roles describe **the
dynamic pattern of successive values a variable takes** — a compressed abstraction *over*
execution, i.e. exactly the "raise the abstraction level" capacity Vainio & Sajaniemi found
novices lack. Teaching interventions report benefits but with modest effect sizes on a small
base — **suggestive, not established [C]**.

### 3.7 Related: what the brain does during DEBUGGING

**Castelhano, Duarte, Ferreira, Durães, Madeira & Castelo-Branco (2018/19), "The role of the
insula in intuitive expert bug detection in computer code", *Brain Imaging and Behavior*.**
<https://doi.org/10.1007/s11682-018-9885-1> **[C]** — professional programmers; the **insula /
salience network** was engaged in bug monitoring, and **insula activity at the moment of bug
SUSPICION predicted subsequent detection precision**, with top-down modulation from ACC and
BA10.

**This is the only result in the entire review that looks like a "verdict" signal** — an
error-monitoring system whose early activity predicts whether a fault will actually be
confirmed. Small, single-site, not replicated, but it is the nearest neural analogue to a screen
that rejects candidates before they consume budget.

---

## 4. Expertise: chunking, plans, schemas — and whether proposal is retrieval or search

**This is the section that bears most directly on our three nulls, so it is the longest.**

### 4.1 The classic claim

**Soloway & Ehrlich (1984), "Empirical Studies of Programming Knowledge", *IEEE TSE*
SE-10(5):595–609.** <https://dl.acm.org/doi/10.1109/TSE.1984.5010283> — two knowledge types:
**programming plans** (stereotypic action fragments: Counter_Variable Plan, Running_Total_Loop
Plan) and **rules of programming discourse** (composition conventions). Method: fill-in-the-blank
on *plan-like* vs *unplan-like* Pascal programs.

The cleanest published numbers are in the CogSci-1983 precursor, **Soloway, Ehrlich & Gold,
"Reading a Program Is Like Reading a Story (Well, Almost)"**
(<https://escholarship.org/uc/item/0zg6b8gv>): **N = 93**, between-subjects, advanced
programmers. Plan-like program: **37 correct / 10 incorrect (79%)**. Unplan-like:
**3 correct / 41 incorrect (6.8%)**. **χ²(1) = 47.7, p < .001.** Reading time longer for the
unplan-like version, F(1,91) = 4.60, p < .05.

**That is a huge effect — and the design confounds item with condition (a single program
pair).** The famous "experts fall to novice level on unplan-like code" interaction is in the
1984 TSE paper, whose per-cell values were not verifiable in this spike. **[B] for the effect,
[C] for its interpretation as evidence of stored plans.**

Companion literature: **Brooks (1983)**, IJMMS 18:543–554, top-down hypothesis-driven
comprehension with **beacons** as recognition triggers; **Pennington (1987)**, *Cognitive
Psychology* 19:295–341, the counterweight — after reading, experts answered **control-flow**
questions faster and more accurately than data-flow or function questions, and recognition
priming followed control structure, i.e. a bottom-up **program model** precedes the
**situation model**; **Détienne (1990)**, "Expert Programming Knowledge: A Schema-Based
Approach" (<https://arxiv.org/abs/cs/0702003>), 269 production rules / 47 general rules for
schema activation; **von Mayrhauser & Vans (1995)**, *Software Engineering Journal* 10:171–182,
the integrated metamodel (Top-Down + Program Model + Situation Model + Knowledge Base with
switching) — built on **think-aloud protocols from a handful of industrial maintainers**, not
controlled experiments. **[C]**

Détienne's own conclusion is the honest one and is usually dropped when she is cited:
*"Empirical data support the schema-based approach... However data also support the
control-based approach"* — which knowledge gets used depends on task, notation, and subject.

### 4.2 How plan/schema theory actually held up: notation-conditional, never robustly replicated

**Gilmore & Green (1988), "Programming Plans and Programming Expertise", *Quarterly Journal of
Experimental Psychology* A 40(3):423–442.**
<https://journals.sagepub.com/doi/10.1080/02724988843000005> **[B] — the most damaging result.**
Perceptual cues highlighting plan structure were given to experienced **Pascal** and **BASIC**
programmers. Pascal programmers benefited **only** on plan-related tasks. **BASIC programmers
showed no benefit in any condition.** Their conclusion: *"the actual content of programming
plans does not generalise across different languages."* Plans are therefore **not** the deep
structure of programming problems — they are an artefact of what a given notation makes easy.

Converging:
- **Davies (1990)** IJMMS; **Davies (1991)**, *Cognitive Science* 15(4) — plans track the
  programmer's *learning history and notation*.
- **Widowski & Eyferth (1986)** (via Détienne) — experts shift to **bottom-up** processing on
  unusual programs. The "unplan-like collapse" is partly a *strategy switch*, not a failure.
- **Rist (1986)** — "when programs are complex, plan use decreases."
- Green's **match–mismatch** hypothesis held for textual notations but **not** for Petri nets,
  with smaller-than-predicted effects (Green, Petre & Bellamy 1991; Moher et al. 1993; see
  Blackwell, Whitley, Good & Petre, <https://www.cl.cam.ac.uk/~afb21/publications/aire.pdf>).
- **Beacons**, the best-designed test: **Crosby, Scholtz & Wiedenbeck (2002), "The Roles Beacons
  Play in Comprehension for Novice and Expert Programmers", *PPIG 14*, 58–73.**
  <https://www.ppig.org/files/2002-PPIG-14th-crosby.pdf> Exp1 (n = 45): expertise
  F(2,336) = 3.37, p ≤ .05, but **line × expertise interaction n.s.** Exp2 (n = 30): correctness
  **not** different between intermediate (63%) and advanced (66%) — only reaction time,
  F(1,168) = 16.62. Exp3 (n = 19, eye-tracking): experienced readers concentrated fixations on
  *complex statements*. Their verdict: **"Beacons may be in the eye of the beholder."** Beacons
  are identified post hoc by expert intuition, which the authors flag as a methodological
  problem across the entire beacon literature.
- **No modern replication of the Soloway–Ehrlich paradigm surfaced.** Wyrich, Bogner & Wagner
  (2022/23), "40 Years of Designing Code Comprehension Experiments: A Systematic Mapping Study",
  *ACM Computing Surveys* (<https://arxiv.org/abs/2206.11102>) maps **95 experiments,
  1979–2019**, and finds the design landscape heterogeneous and deficient. Heinonen et al.
  (<https://arxiv.org/abs/2212.07763>) find "a lack of a shared knowledge base and poorly
  defined constructs."

**Verdict: plan theory was never decisively refuted and never robustly replicated across
languages. It is a language-conditional effect from a small number of labs with 1980s
materials. [C], trending [D] for the strong "stored plan library" reading.**

And recall §1.3: **Siegmund et al. (FSE 2017) went looking for the neural signature of plan
retrieval and found nothing** — no memory-retrieval signature during semantic-cue
comprehension, no beacon effect, and the authors themselves listed *"the theory is simply
wrong"* as a live explanation.

### 4.3 Chunking: the Chase–Simon analogy is *half wrong*, and the half that is wrong matters

**McKeithen, Reitman, Rueter & Hirtle (1981), "Knowledge organization and skill differences in
computer programmers", *Cognitive Psychology* 13:307–325.**
<https://www.sciencedirect.com/science/article/pii/0010028581900128> — the enduring result is
about **organisation** (beginners show natural-language associations among ALGOL-W keywords;
experts show highly *similar* programming-based hierarchies), not a clean scrambled-recall
null.

**The strong form — "experts have no advantage on scrambled material" — is empirically false,
in chess and in programming. [A]**

**Sala & Gobet (2017), "Experts' memory superiority for domain-specific random material
generalizes across fields of expertise: A meta-analysis", *Memory & Cognition*.**
<https://pmc.ncbi.nlm.nih.gov/articles/PMC5323477/> — **24 studies, 28 effect sizes, 903
participants.** Overall **r̄ = .41, 95% CI [.29, .51]**; after trim-and-fill correction for
publication bias **r̄ = .29 [.17, .41]**. By domain: music .69, games .42, **programming .36**,
sports .30. Six programming studies included (Adelson 1981; Barfield 1986; Bateson et al. 1987;
Guerin & Matthews 1990; Magliaro & Burton 1986; Schmidt 1986), **all showing an expert
advantage on randomized code.**

**This is the best-powered evidence in the entire report and it points at MANY SMALL CHUNKS,
not a few large schemas.** Random material destroys high-level structure but leaves small
fragments intact by chance; an advantage that survives scrambling is an advantage carried by
fine-grained, low-level units. Template/chunk theory survives; "expert = holder of a library of
big plans" does not.

### 4.4 Neuro evidence on expertise — one positive, one positive-but-fragile, one null

**Ikutani, Kubo, Nishida, Hata, Matsumoto, Ikeda & Nishimoto (2021), "Expert Programmers Have
Fine-Tuned Cortical Representations of Source Code", *eNeuro* 8(1):ENEURO.0405-20.2020.**
<https://pmc.ncbi.nlm.nih.gov/articles/PMC7877476/> **[C]**
**n = 30** (10 expert / 10 middle / 10 novice by AtCoder competitive-programming rating; only
**2 female**), 72 Java snippets, 4 functional categories (chance 25%) and 11 subcategories
(chance 9.72%), whole-brain searchlight linear SVM. Category decoding significant broadly;
**subcategory decoding survived only in left superior temporal / supramarginal cortex.** Seven
regions showed both significant decoding and correlation with behavioural performance — peak
bilateral IFG pars triangularis (**r = 0.789** right, 0.671 left), left IPL (0.698), left
MTG/ITG (0.635), right SFG (0.675). Expertise validity check: AtCoder rating vs in-scanner
performance r = 0.722, p = 7×10⁻⁶.
**Authors' own limitation: 10 per group is underpowered for between-group tests.** Strong
within-subject decoding, weak between-group expertise claim. Unreplicated.

**Floyd, Santander & Weimer (2017), "Decoding the Representation of Code in the Brain: An fMRI
Study of Code Review and Expertise", *ICSE 2017*, 175–186.** **[C]**
**n = 29.** Classifiers distinguished code comprehension, code review and prose review — code
vs prose at **79% balanced accuracy (p < 0.001)**; code/prose *reading* near-perfectly separable
(r = 0.99). Headline: **the classifier's ability to separate code comprehension from prose
predicted expertise NEGATIVELY, r = −0.44, p = 0.016** — more expert developers' code and prose
processing were *less* neurally distinguishable, i.e. code becomes *more* language-like with
expertise.
*(Verification note: two independent sweeps in this spike disagreed on retrievability — one
could reach only a secondary summary and flagged the numbers as unverified; the other reached
primary-source figures. The figures above are from the second. Publisher paywalls blocked direct
confirmation here. Treat the numbers as probable, not certain.)*
**The replication failed.** **Fucci, Girardi, Novielli, Quaranta & Lanubile (2019), "A
replication study on code comprehension and expertise using lightweight biometric sensors",
*ICPC 2019*.** <https://doi.org/10.1109/ICPC.2019.00050> — **n = 28**; code-vs-prose
classification succeeded and *improved* (87% balanced accuracy from heart-rate signals) but the
**expertise effect did not replicate: τ = 0.16, p = 0.31.**
The claim is a correlation over 29 subjects between a derived classifier statistic and an
experience measure — fragile by construction, and the one attempt to reproduce the expertise
half failed. The same group's fNIRS follow-up (Endres et al., ICSE 2021, n = 31 novices) is
directionally consistent but is not an independent replication.

**Ivanova et al. (2020) is the null:** *"We correlated responses within each system with
independently obtained proficiency scores... No correlations were significant... However, due
to a relatively low number of participants (N = 24 and N = 19), these results should be
interpreted with caution."*

**So the honest state of expertise neuroscience is: one fine-tuning claim (n = 30, 10/group,
admittedly underpowered), one code-becomes-prose-like claim (n = 29, unverified numbers, never
replicated), one explicit null (n = 24/19). Nothing here is safe to build on. [D] collectively.**

(A 2026 EEG preprint, Rekrut et al., <https://arxiv.org/abs/2606.30879>, n = 37, classifies
expert vs novice at 91.8% within-subject but only **58.8% three-class leave-one-subject-out** —
the cross-subject number is the honest one, and it is a non-peer-reviewed preprint.)

### 4.5 THE KEY QUESTION: is expert proposal retrieval-based or search-based?

**Answer: retrieval-first, search-on-residual — and, crucially, the switch is empirically
visible in the generation order. [B]**

The sharpest single finding is **Rist (1989), "Schema Creation in Programming", *Cognitive
Science* 13:389–414** (10 novices × 8 Pascal programs, longitudinal protocols): when a schema
**is** available, the plan is emitted **forward, in schema/execution order, top-down**; when it
is **not**, the programmer works **backward from the "focus"** — the line that directly achieves
the goal — and expands outward. Détienne (*HCI* 10(2–3):129–170, 1995,
<https://arxiv.org/abs/cs/0612008>) states the criterion explicitly: *"when the programmers know
all the required abstract and detailed schemas, then the plans are developed in a top-down and
forward manner... When a schema cannot be retrieved... plans are developed in a bottom-up and
backward manner."*

**Retrieval side:** the plan-like/unplan-like collapse; Détienne's 269 activation rules;
Adelson & Soloway (1985) — experts go top-down/breadth-first **on familiar problems**; beacons
for experienced readers.

**Search side:** **Guindon (1990), "Designing the Design Process: Exploiting Opportunistic
Thoughts", *HCI* 5:305–344** — verbal protocols of **three** professional designers (n = 3;
suggestive only): top-down decomposition breaks down early, decisions interleave across
abstraction levels, requirements are *discovered mid-solution*. **Robertson et al. (INTERACT'90)**
— experienced readers' code reading is non-linear: **11% of reading activity was direction
switches, 17% went backwards.** **Littman, Pinto, Letovsky & Soloway (1986)** and
**Détienne (1984/1986)** — experts fall back on **symbolic/concrete mental simulation** exactly
when textual cues are absent and when checking **unforeseen plan interactions**.

### 4.6 And retrieved schemas demonstrably HURT — this is the finding that matches our data

- **Détienne (1984)** observed the negative case directly: experts **fail to detect bugs when
  they strongly expect a particular value and never verify it against the code** — strongest
  when reading their own code. **[C]**
- **Sergeyuk, Titov, Golubev & Bryksin (2023), "Overcoming the Mental Set Effect in Programming
  Problem Solving"** <https://arxiv.org/abs/2307.06673> — 129 Python developers screened,
  **57 (44%) showed a mental set** (Luchins paradigm, idiomatic vs habitual solutions). Both
  de-fixation interventions **failed**: only 2 participants spontaneously switched strategy; no
  response-time de-automatization (H(2) = 1.403, p = .496); interventions rated unhelpful
  (M = 0.97/5). Small, null-intervention, single study — **but the 44% prevalence figure is the
  useful part.** **[C]**
- **The chess analogue is the better-powered one and is worth importing carefully.**
  **Bilalić, McLeod & Gobet (2008), "Why good thoughts block better ones", *Cognition*
  108(3):652–661** — having found a familiar solution, expert players *reported* searching for
  better ones while their **eye movements stayed on features of the first solution**:
  attentional capture, not lazy stopping. **[B]**
  **Sheridan & Reingold (2013), *PLOS ONE* 8(10):e75796** (n = 34; 17 experts, mean Elo 2223) is
  the independent boundary-condition study: when the familiar move was **advantageous but
  suboptimal**, **8 of 17 experts and 8 of 17 novices chose it — expertise gave NO protection**;
  when the familiar move was an outright **blunder**, experts escaped. **[B]**

**Read that last result across to synthesis and it is almost exactly our Arc 3 failure mode:
retrieval-based proposal is safe only when the verification signal is strong enough to reject a
plausible-but-wrong retrieved candidate. When the retrieved candidate is *wrong but not
obviously wrong*, expertise does not save you — only a hard verdict does.**

### 4.7 Evidence-quality table for §4

| Claim | Status |
|---|---|
| Experts do better on plan-like than unplan-like code | Large (χ² = 47.7, N = 93) but **single item pair, one lab, Pascal only** **[B/C]** |
| Plans are language-general deep structure | **Failed to generalise** — no effect in BASIC (Gilmore & Green 1988); notation-dependent **[D]** |
| Beacons drive expert comprehension | Partial; **absent in novices**; correctness differences often n.s.; beacons chosen post hoc **[C]** |
| Neural signature of plan retrieval during top-down comprehension | **Not found** (Siegmund et al. FSE 2017, n = 11) **[C null]** |
| Experts show no recall advantage on *scrambled* code | **FALSE.** Meta-analytic r̄ = .41 → .29 corrected; programming r̄ = .36 **[A]** |
| Expertise fine-tunes cortical code representations | One study, n = 30, 10/group, authors admit underpowered **[C]** |
| With expertise, code review becomes *less* like prose review | One study, n = 29 (r = −0.44, p = .016); **the one replication attempt FAILED** (Fucci 2019, n = 28, τ = 0.16, p = .31) **[D]** |
| Expertise modulates MD/language engagement | **Null** at n = 24/19, with explicit caution **[C null]** |
| Expert proposal = retrieval when schema available, backward search otherwise | Converging protocol evidence, **all small-n, no controlled replication** **[B]** |
| Retrieved schemas cause fixation/blindness | Thin in programming (44% prevalence, failed interventions); **well-established in chess** **[B]** |

**Not independently verifiable in this spike — do not quote as certain:** Soloway & Ehrlich 1984
TSE per-cell values; Gilmore & Green 1988 sample size; Wiedenbeck 1986 beacon-recall percentages
(secondary source only); Fakhoury et al. 2018 n and effect sizes; the program-comprehension ALE
meta-analysis's study/foci counts.

---

## 5. Code vs natural language vs math/logic

### 5.1 The clearest single result: code overlaps FORMAL LOGIC most, language least

**Liu, Kim, Wilson & Bedny (2020), *eLife* 9:e59340** ran the comparison directly, in **n = 15
expert programmers**, with code, formal logic, mathematics, a generic executive control task
(MSIT) and sentence comprehension in the same subjects.

**Overlap ordering: formal logic > math > MSIT ≈ language.** Code's overlap with logic was
"significantly higher than with all other tasks." MVPA distinguished `for` from `if`: PFC 64.7%,
IPS 67.4%, pMTG 68.4% (all p < 0.001). **[B]**

**One methodological caveat that must travel with this result:** Liu et al. localized
language/math/logic *relative to each other*, which by construction **suppresses regions they
share**. The ordering is real; the absolute "language overlap ≈ zero" reading is partly an
artefact of that design choice.

### 5.2 The lesion evidence — the strongest argument, and it is not an imaging argument

**Fedorenko & Varley (2016), "Language and thought are not the same thing: evidence from
neuroimaging and neurological patients", *Annals of the NY Academy of Sciences* 1369(1):132–153.**
<https://pmc.ncbi.nlm.nih.gov/articles/PMC4874898/> **[A]**

Patients with **global aphasia** — severe loss of language comprehension and production —
retain:

- **Arithmetic with structure.** Three severely aphasic patients "solved mathematical problems
  involving addition, subtraction, multiplication, and division; small and large numbers; whole
  numbers and fractions; and expressions with **brackets**," retaining knowledge of **embedded
  bracket structure** and of **order-significance in non-commutative operations** — despite
  agrammatic language.
- **Causal and formal reasoning** (Varley & Siegal).
- **Chess.** Severely aphasic patients "continue to play chess."
- **Theory of mind, music, navigation.**

**This is the most decisive evidence in the whole review, and it is worth stating in our own
terms: a person who has lost the language network can still parse a bracketed expression, respect
operator non-commutativity, and play chess. Structured symbolic computation does not run on the
language network.** If code comprehension needed language, these patients would lose it.

### 5.3 The math network

**Amalric & Dehaene (2016), "Origins of the brain networks for advanced mathematics in expert
mathematicians", *PNAS* 113(18):4909–4917.**
<https://www.unicog.org/publications/Amalric%20Dehaene%20fMRI%20of%20math%20and%20language%20in%20professional%20mathematicians%20PNAS%202016%20plus%20SI.pdf>
**[B]**

- **n = 15 professional mathematicians** vs **n = 15 non-mathematical academics** of equal
  standing (literature, history, philosophy, linguistics, arts). 72 spoken math statements
  (analysis / algebra / topology / geometry) + 18 general-knowledge, each true / false /
  meaningless, matched for word count and duration.
- Math network: **bilateral IPS, bilateral inferior temporal (incl. visual number-form areas),
  bilateral superior/dorsolateral/mesial prefrontal, cerebellum** — all four math domains.
- **The language result, precisely.** Using seven per-subject language ROIs from an independent
  sentence localizer: *"if anything, mathematics called less upon those language areas than did
  general semantic reasoning."* Whole-brain: "near-complete spatial separation." A small overlap
  in left dorsal BA44 appeared **only in smoothed group images, not in single-subject results**.
  aMTG and AG/pSTS were **systematically deactivated** during math reflection.
- **The difficulty control is the paper's strongest feature:** the contrast **easy math >
  difficult non-math** recovered the same sites.
- **Two caveats worth carrying.** (i) The authors' own: mathematicians vs controls "may still
  differ on dimensions such as IQ, musical talent, hobbies," so *"our conclusions rest primarily
  on within-subject comparisons"*; and the design **"[does] not exclude a transient role for
  these areas in the acquisition of mathematical concepts in children."** (ii) It is a PNAS
  **Inaugural Article, "Contributed by" Dehaene** — the author-selected-reviewer track, not
  ordinary peer review.

**Amalric & Dehaene (2019), "A distinct cortical network for mathematical knowledge in the human
brain", *NeuroImage* 189:19–31** — **n = 14** (mathematicians only). Two decisive additions:
- **Difficulty explicitly ruled out**: IPS beta vs accuracy R = 0.074 (n.s.), vs RT R = −0.35
  (n.s.). "The math-responsive network activates independently of problem difficulty."
- **The language ROIs tracked SYNTACTIC COMPLEXITY, not math content**: language-ROI beta
  correlated with **number of grammatical morphemes at R = 0.64, p = 2×10⁻⁹** (R = 0.55 within
  math statements alone). Geometry statements, syntactically the most complex, drove *all* the
  apparent "language" activation. In Experiment 2, with syntax fully equated, the 7 language ROIs
  showed **no differences between categories** (all Fs(1,88) < 1.32, n.s.).
- This also **disconfirms the recursion hypothesis directly**: rote algebraic identities — the
  most recursive-looking stimuli — produced no activation in temporal pole, TPJ, or IFGorb.

**Is it contested? Yes, on three fronts. [C] for the strong reading.**
1. **Domain-generality.** The math network's coordinates substantially coincide with the
   multiple-demand system — **Fedorenko, Duncan & Kanwisher (2013), *PNAS* 110(41):16616–16621**:
   *"the same sets of voxels are engaged across tasks ranging from arithmetic to storing
   information in working memory."* The easy-math > hard-non-math contrast is a genuine answer,
   but not a decisive one.
2. **Ansari (2016), *PNAS* 113(18):4887–4889** — grants the finding, presses that language may
   matter for *acquisition*; plasticity findings are correlational; visuospatial ability may
   mediate.
3. **The lab's own training study partly undercuts the framework.** **Amalric, Roveyaz & Dehaene
   (2023), *PNAS* 120(6):e2213430120** — *"short videos do not suffice to induce a meaningful
   lasting change in the brain's math-responsive network"*; newly taught content activated
   **episodic-memory** regions, not the math network.

**Independent convergence from outside Dehaene's lab:** Li, Xu & Liu, arXiv:2406.14358 — logical-
mathematical symbol processing overlaps **spatial cognition (Dice 0.255)** far more than
**language (Dice 0.113)**, a 2.7× ratio, with MVPA agreeing. *Preprint; Neurosynth meta-analysis
is coarse.* **[C]**

### 5.3b Logic and algebra dissociate from language — with the difficulty confound running the
right way

**Monti, Parsons & Osherson (2009), "The boundaries of language and thought in deductive
inference", *PNAS* 106(30):12554–12559** — **n = 15.** Identical materials judged under two
tasks (validity vs grammaticality), so linguistic encoding is subtracted on both sides. **Logic
was the HARDER task** (75% vs 89.6% accuracy, t(14) = 4.39, p < 0.001) — which makes the
dissociation hard to attribute to effort. Logic inference → **BA 10p (rostrolateral PFC), medial
BA 8**; *"in striking contrast, logic inference produced no activation in the language areas."*
On BA47, where both contrasts land, **the peaks are ~2 cm apart** (linguistic −42,26,−2; logic
−46,44,−14) — the apparent overlap is a coarse-anatomy artefact. **[B]**
*Author's own hedge, worth keeping:* "it is possible that LOT coincides with the 'logical form'
(LF) of natural language sentences."

**Monti, Parsons & Osherson (2012), "Thought beyond language: neural dissociation of algebra and
natural language", *Psychological Science* 23(8):914–922** — **n = 21**, with the elegant move of
writing algebra **out in words** ("X minus Y is greater than Z") so reading demands are equated.
Again **algebra was harder** (78.1% vs 84.1%). Algebraic equivalence produced **"no significant
activation in any of the perisylvian language regions"** — instead bilateral hIPS, SPL, IPL,
precuneus. Perisylvian regions were often **less active during algebra than during mere
reading**. Deliberately narrow scope: *"beyond initial reading and comprehension of stimuli,
the neural substrate of language does not intervene in algebraic reasoning."* **[B]**

**Fedorenko, Behr & Kanwisher (2011), *PNAS* 108(39):16428–16433** — the selectivity result.
48 unique participants but **only 11–15 per non-linguistic task.** Of 63 ROI × task tests,
**exactly one survived correction.** **But the under-cited caveat matters:** at a liberal
p < 0.05 uncorrected threshold, overlap in **posterior LIFG appeared in 85% of subjects** for
language + verbal WM. **Per-task n = 11–15 makes these nulls weak as nulls;** what rescues them
is that the comparison is *relative magnitude*, not bare absence. **[B]**

**Newest (2026), and it may under-specify everything above:** **Kean, Fung, Jaggers, Chen, Rule,
Benn, Tenenbaum, Piantadosi, Varley & Fedorenko (2026), "Evidence from formal logical reasoning
reveals that the language of thought is not natural language", *PNAS* 123(28):e2520095123** —
fMRI + aphasia. *"The language brain network is not engaged during logical reasoning, and
patients with severe aphasia exhibit intact performance on logic tasks. Instead, **inductive**
reasoning recruits the domain-general multiple demand network… whereas **deductive** reasoning
draws on brain regions that are distinct from both the language and the multiple demand
networks."* **Sample sizes not verifiable in this spike (403). If it holds, "code recruits MD" is
under-specified — MD may not be the right unit.** **[C]**

### 5.3c Code vs math lateralization — unresolved

Ivanova et al. observed that math and logic drive MD with a **left-lateralized** profile, whereas
their Python code response was **bilateral** — so "code is math" is not the conclusion either.
Liu & Bedny found code **left-lateralized**. **[D] — unresolved.**

### 5.4 Is code a language? What the field predicted, and what happened

**Fedorenko, Ivanova, Dhamala & Bers (2019), "The Language of Programming: A Cognitive
Perspective", *Trends in Cognitive Sciences* 23(7):525–528** — the position piece that framed
the question, and which described the neuroimaging work as "in their infancy." The 2020 data
came back **against** the strong language reading.

**The best current statement of the general principle** is **Fedorenko, Piantadosi & Gibson
(2024), "Language is primarily a tool for communication rather than thought", *Nature*
630:575–586**, with **Fedorenko, Ivanova & Regev (2024), "The language network as a natural kind
within the broader landscape of the human brain", *Nature Reviews Neuroscience***. *(Citations
verified from the EvLab publication list; full texts paywalled, so the characterisations here are
from the abstracts and the lab's own framing.)*

**One nuance from that same lab that blocks a tempting move.** **Shain, Kean, Casto, Lipkin,
Affourtit, Siegelman, Mollica & Fedorenko (2024), "Distributed sensitivity to syntax and semantics
throughout the language network", *Journal of Cognitive Neuroscience* 36(7):1427–1471** — the
language network does **not** decompose into a syntax module and a semantics module; sensitivity
to both is distributed throughout it. **So you cannot "borrow just the syntax part" of the
language stack.** If you recruit it, you recruit a combinatorial lexico-syntactic system whose
lexical half is exactly the part the identifier evidence says is unhelpful (§6).

### 5.5 The "language aptitude predicts programming" claim — and why it does not survive contact
with its own paper

**Prat, Madhyastha, Mottarella & Kuo (2020), *Scientific Reports* 10:3817.**
<https://pmc.ncbi.nlm.nih.gov/articles/PMC7051953/> **[C], NOT [B] — I graded this too generously
earlier in this document and am correcting it here.**

**n = 42 recruited, 36 analysed; effective per-model df imply n = 33 / 28 / 28.** Ten 45-minute
Codecademy "Learn Python" sessions (7.5 h total). Language aptitude = **MLAT** (a full
metalinguistic battery). "Math aptitude" = **8 items from the Rasch-Based Numeracy Scale — a
risk/health numeracy instrument, not a mathematical-reasoning test.**

Unique variance from stepwise regression:

| Outcome | Top predictor | Language | Numeracy |
|---|---|---|---|
| Learning **rate** | language **43.1%** | 43.1% | 6.1% |
| Programming **accuracy** | **fluid reasoning 50.1%** | 8.7% | — |
| **Declarative knowledge** | **fluid reasoning 30.9%** | (MLAT not retained) | — |
| Averaged | **general cognitive ability 34%** | **17%** | 2% |

**Three corrections to how this is usually cited — including in earlier drafts of this document:**

1. **Fluid reasoning (34%), not language aptitude (17%), is the paper's strongest predictor**, and
   it topped two of the three models outright. The "language beats math ~2×" framing has the 2×
   pointing the wrong way: it is *fluid reasoning ≈ 2 × language*.
2. **The zero-order correlations are near-identical.** Learning rate: MLAT r(34) = .56 vs numeracy
   r(29) = .52. Programming accuracy: **.54 vs .54.** Declarative: .45 vs .42. **Numeracy was a
   large, significant bivariate predictor of every outcome.** The 17-vs-2 gap is a
   *unique-variance-after-competition* artefact between collinear predictors of unequal
   reliability, at n ≈ 28–33, **with no cross-validation, shrinkage, or holdout** — and numeracy
   entered stepwise with ~5 fewer participants.
3. **95% CIs of roughly [.28, .75] and [.21, .73] overlap almost entirely, and no study in this
   literature formally tests the DIFFERENCE between the language and math coefficients** — which
   is the test the headline claim actually requires.

**Replication status: none — no direct replication has been attempted.** But the follow-ups point
away from it:

- **Kuo, Mottarella, Haile & Prat (2022), SoftCOM** — **n = 80**, sixteen sessions: *"post-module
  declarative assessments explained the most variance in each of our seven learning outcomes."*
  **Acquired knowledge dominated**, not aptitude.
- **Graafsma, Robidoux, Nickels, Roberts, Polito, Zhu & Marinus (2023), *Journal of Cognitive
  Psychology*** — **n = 282**, tests administered *before* instruction. SEM: **algorithmic/math
  latent → outcome β = .493 (p = .041); language latent → outcome β = .057 (p = .797).** Grammar
  learning **BF₁₀ = 0.341, favouring the null.** **A directional contradiction of Prat at ~8× the
  n.** *(Be even-handed: their two latents correlate r = .736 — the mirror image of Prat's
  variance-competition problem — and the outcome measure's α = .29–.55 is poor. A vocabulary
  measure did survive, BF₁₀ = 7.98.)*
- **Finke, Kemény, Sommer, Krnjic, Arendasy, Slany & Landerl (2022), *Computer Science
  Education*** — **n = 132, PRE-REGISTERED.** **Figural reasoning and visualization** uniquely
  predicted computational thinking; **arithmetic did not.** Supports neither framing — it supports
  **fluid/spatial reasoning**, exactly what topped two of Prat's own models.
- **The one experimental test of the mechanism is NULL.** **Hartmann, Bergum, Gorgosch, Peitek,
  Apel & Siegmund (2024), arXiv:2402.01657** — teaching an artificial language first vs a Git
  control: language-learning strategies *were* activated, but *"we did not find a significant
  benefit for programming competency."* **This removes the pedagogical inference most often drawn
  from Prat.**
- **A better-supported alternative account:** **Bergersen & Gustafsson (2011), *Journal of
  Individual Differences* 32(4):201–209** — n = 65 professional developers; the effect of working
  memory on programming skill was **fully mediated through programming knowledge.**

**No n > 100 MLAT × programming study exists; no meta-analysis of programming-aptitude predictors
exists.**

### 5.5b The ERP evidence — code syntax IS processed as structure, but a P600 is not a
language-network signature

**Kuo & Prat (2024), "Computer programmers show distinct, expertise-dependent brain responses to
violations in form and meaning when reading code", *Scientific Reports* 14:5807.**
<https://www.nature.com/articles/s41598-024-56090-6> **[B] — the best-designed study on code
syntax in existence.**

160 Python lines, **2 × 2 crossing FORM and MEANING**, RSVP:
`for animal in pets:` (well-formed) / `for fruit in pets:` (implausible) /
`for "animal" in pets:` (invalid) / both.
- Form violations → **P600** (500–800 ms), b = **2.97 μV** [2.58, 3.36], t(488) = 14.84,
  p < 0.001.
- Meaning violations → **N400** (300–500 ms), b = **−1.71 μV** [−2.11, −1.32], t(488) = −8.58,
  p < 0.001.
- **Expertise interaction for SYNTAX ONLY**: higher Python expertise → larger P600, b = 1.04,
  t(488) = 5.18, p < 0.001. **No expertise interaction for the N400.** No LAN/ELAN. The authors'
  term: **"grammaticalization."**
- **n discrepancy across sources: 62 recruited, 45 analysed per the PMC methods (expert 27 /
  novice 18). Flagged, not resolved.**

**Two things must travel with this result.**
1. **The authors' own disclaimer:** the findings *"do not provide evidence that code
   comprehension relies on the **same** neural substrates as language comprehension."*
2. **The P600 is NOT diagnostic of the language network.** It is elicited by musical-syntactic
   violations, arithmetic violations, number-sequence violations, spelling errors — and, directly
   relevant, by **implicit artificial-grammar structural violations** (Silva et al. 2017).
   **So the ERP result and the localizer fMRI results are NOT in conflict**: a domain-general
   structured-sequence system would produce exactly this pattern.

Same caution applies to Bergum et al. (2026, §1.5): a **frontal** positivity is more consistent
with P3a/novelty than with the centroparietal P600 of syntactic reanalysis, so **the language
analogy there is looser than the abstract implies.**

### 5.5c Artificial grammar and Broca's area — the analogy Siegmund leaned on, examined

Siegmund et al. (2014) grounded their language interpretation in artificial-grammar learning,
where formal-grammar judgements engage BA44/45. The literature is real — and its own authors read
it as **domain-general**.

**Petersson, Folia & Hagoort (2012), *Brain and Language* 120(2):83–95** — n = 32, implicit
learning of a **regular (finite-state) grammar over 5 days**, with chunk-strength-matched
violations. NG > G → bilateral IFG centred on **BA 44/45** (p_FWE < 0.001), overlapping natural
syntax in the same subjects. **Their conclusion, verbatim:** *"the left inferior frontal region is
a **generic on-line sequence processor** that unifies information from various sources in an
incremental and recursive manner, whether there are any requirements for syntactic movement or
the processing of nested structures or not."* Causal support: rTMS over BA44/45 (Uddén et al.
2008). **[B]**

**But the strongest counterweight is from inside the same institute.** **Uddén & Männel (2018),
*Oxford Handbook of Psycholinguistics*, ch. 33** — GingerALE meta-analysis over 7 AGL studies:
under a conservative FDR assumption **only bilateral frontal operculum survives**, AGL shows
substantially more right-hemisphere involvement than natural syntax, and — a real dissociation —
**in finite-state AGL studies not a single peak lands in left posterior superior/middle temporal
gyrus**, one of the two most robust natural-syntax regions.

**And the "BA44 computes hierarchy" claim is conditions-stripped.** Friederici et al. (2006,
*PNAS*) is the source (n = 37 analysed; the critical BA44 peak at p < 0.01 while frontal-operculum
peaks are p < 0.001; **a single marginal Grammar × Violation interaction, F(1,34) = 4.96, p < .05,
is the entire load-bearing statistic**; the DTI half of the title rests on **n = 4**). The AⁿBⁿ
stimuli cued A vs B **by vowel class**, so "count the i/e syllables, count the o/u syllables,
compare" solves every item with zero item-to-item dependency. **Friederici's own co-author
concedes the point:** Fitch & Friederici (2012) — *"a system's ability to recognize the stringset
generated by AⁿBⁿ tells us one thing, and one thing only: that the system is supra-regular."*
**Musso et al. (2003)** should not be leaned on either: n = 8 per experiment, all "impossible"
rules are positional/counting rules, and **subjects learned the impossible language nearly as
well** (91.6% vs 97%). **[D] for the strong hierarchy claim.**

**Bottom line for code syntax: the decisive experiment has never been run.** No study has combined
**(a) individual-subject functional language localizers** with **(b) a manipulation of code
syntactic well-formedness holding semantics constant.** Kuo & Prat have (b) without (a); Ivanova
has (a) without (b). And note that **Siegmund's 2014 control task was syntax-error finding —
a design that SUBTRACTS syntax out**, so it is not evidence that code syntax engages language
regions; if anything it shows syntax-only processing produces *less* activation there.

### 5.6 The strongest single contrastive control against "code is a language"

**Malik-Moraleda, Taliaferro, Shannon et al. & Fedorenko (2023), "Constructed languages are
processed by the same brain mechanisms as natural languages", *PNAS*.** **[B]**
Esperanto, Klingon, Na'vi, Dothraki and High Valyrian **do** robustly engage the language network.

**The network is not fussy about a language being natural, evolved, or widely spoken — yet code
reportedly does not engage it. That asymmetry is harder to explain away as a stimulus artefact
than any single code study, and it is the best argument on the "code is not a language" side.**

### 5.7 What transfers from NL machinery and what does not — the defensible 2026 answer

| Mechanism | Transfers to code? | Grade |
|---|---|---|
| **Token-level surface reading** | **Yes**, and probably most of the language-network signal that exists | **[B]** |
| **Structured-sequence processing** (BA44/45, frontal operculum) | **Yes — but it is DOMAIN-GENERAL on its own discoverers' reading.** Indexed by the P600 (b = 2.97 μV, expertise-modulated) | **[B]** |
| **Prediction / surprisal over a symbol stream** | **Suggestively yes** (Bergum 2026; Kuo & Prat's expertise-sharpened P600). Frontal distribution ≠ language network | **[C]** |
| **An early "surface meaning" stage in lateral temporal language cortex** | **Possibly — and this is the live challenge to the consensus.** Liu, Wilson & Bedny (2024) decoded `for` vs `if` from language cortex *better than anywhere else*, not from surface words, and **earlier than fronto-parietal cortex** | **[B]** |
| **Left-hemisphere lateralization bias** | **Yes, correlated with language laterality across individuals (R² = 0.658).** Mechanism unknown; possibly ontogenetic scaffolding rather than neural reuse | **[C]** |
| **Lexical SEMANTICS of identifiers** | **No** — Δβ = 0.03, p = 0.84 with Japanese identifiers; undecodable in MVPA. The cleanest result in the code literature | **[B] for the null** |
| **Perisylvian sentence-level combinatorics** | **No** — math and algebra/logic both spare it, with difficulty confounds running the *wrong* way | **[A]** |
| **Reasoning / evaluation of correctness** | **No** — MD/logic territory throughout; global aphasics retain bracketed arithmetic, operator order, chess | **[A]** |
| **The pedagogical inference (teach a language, get a programmer)** | **No — the one experimental test is null** (Hartmann 2024) | **[B]** |

**One-line summary: the SURFACE and the SEQUENCE MACHINERY transfer; the LEXICAL SEMANTICS does
not; the REASONING never did. And the sequence machinery that transfers is domain-general — it is
not "borrowing language."**

**What actually predicts programming learning, on the best evidence: fluid/figural reasoning**
(top predictor in two of three Prat models; the sole survivor in the only pre-registered
replication, Finke n = 132), **then acquired domain knowledge** (Kuo n = 80; Bergersen &
Gustafsson n = 65, full mediation). **Not "language aptitude," and not "math aptitude" as usually
measured.**

---

## 6. Identifiers and naming

### 6.1 The premise of the question does not survive contact with the literature

The spike brief assumed identifier semantics is "the one place language-network involvement in
code is best attested." **It is not.** It is, if anything, the place the language-network story
is *most cleanly falsified*, and the behavioural story is *most cleanly supported*. These are
two different claims and the literature separates them sharply.

**Neural: the direct test is null. [B]**
Ivanova et al. (2020) contrasted Python with **English vs Japanese identifiers** (meaningless to
the monolingual sample), with individually-localized language regions: **β = 0.03, p = 0.84**;
no effect of Japanese knowledge (β = 0.03, p = 0.93); no interaction. Srikant et al. (2022)
confirmed it in MVPA: **"variable language" was the one property that could not be decoded from
either the MD or the Language system.**

**The positive case is one ROI attribution in an n = 11 study whose own identifier manipulation
was null.** Siegmund et al. (FSE 2017) used a genuine meaningful-vs-obfuscated contrast
(`arrayAverage`/`reversedWord` vs Caesar-scrambled `ayyaoAwyyaky`/`mgqakyy`) and reported BA21
(p < 0.01), BA40 (p < 0.015), BA44 (p < 0.01) for bottom-up > syntax-error. The claim "BA21 does
word-level semantics of program tokens" is made **by citation to the natural-language
literature, not by localizer.** And their RQ3 verdict, boxed in the paper, is: *"Neither beacons
nor program layout seem to significantly affect the program comprehension process."*

Peitek et al. (2021) is worth one further note in the same direction: **vocabulary size (N)
loaded on BA6 (premotor / working memory, r ≈ 0.41), not on the putative lexical-semantic
BA21.** The headline the authors give is *"textual size drives programmers' attention, and
vocabulary size burdens programmers' working memory"* — a **capacity** story, not a
**semantics** story.

Related but weaker: **Fakhoury, Ma, Arnaoudova & Adesope (2018), "The effect of poor source code
lexicon and readability on developers' cognitive load", *ICPC 2018*** (Distinguished Paper),
<https://doi.org/10.1145/3196321.3196347> — fNIRS + eye tracking; **linguistic antipatterns
significantly increase cognitive load**, while readability metrics alone did not capture it.
Full text closed; n and effect sizes unverified here. **[C]**

### 6.2 Behaviourally, naming matters — a lot, and for an instructive reason

| Study | n | Finding |
|---|---|---|
| **Lawrie, Feild, Binkley & Morrell (2006), "What's in a name? A study of identifiers", *ICPC 2006*** | **>100** | Single letters / abbreviations / full words. **Full words ≥ abbreviations > single letters** for description quality and confidence. |
| **Lawrie, Morrell, Feild & Binkley (2007), "Effective identifier names for comprehension and memory", *ISSE* 3(4):303–318.** <https://doi.org/10.1007/s11334-007-0031-2> | journal ext. | Adds **recall**: better names improve *memory for the code*, not just immediate comprehension. |
| **Binkley, Davis, Lawrie, Maletic, Morrell & Sharif (2012), "The impact of identifier style on effort and comprehension", *EMSE* 18(2):219–276.** <https://doi.org/10.1007/s10664-012-9201-4> | eye-tracked | camelCase → higher accuracy; under_score → faster. **Style effects are real but small relative to experience and training.** |
| **Hofmeister, Siegmund & Holt (2017/2019), "Shorter identifier names take longer to comprehend", *SANER 2017* / *EMSE* 24(1):417–443.** <https://doi.org/10.1007/s10664-018-9621-x> | — | **Words fastest**; abbreviations and single letters slower — the **reverse** of a visual-length account. This isolates lexical access from visual span. |
| **Avidan & Feitelson (2017), "Effects of variable names on comprehension", *ICPC 2017*** | **n = 9** | **Parameter names matter more than local-variable names.** But **in 3 of 6 methods no significant difference — because the *original* production names were poor or misleading.** Underpowered; suggestive only. |
| **Schankin, Berger, Holt, Hofmeister, Riedel & Beigl (2018), "Descriptive compound identifier names improve source code comprehension", *ICPC 2018*.** <https://doi.org/10.1145/3196321.3196332> | **n = 88** | Descriptive compound names → **~14% faster** semantic-defect finding. **Two moderators that matter enormously: the benefit VANISHED for syntax-error search (shallow task), and appeared only for MORE EXPERIENCED developers.** |
| **Feitelson, Mizrahi, Noy, Ben Shabat, Eliyahu & Sheffer (2022), "How developers choose names", *IEEE TSE* 48(1).** <https://arxiv.org/abs/2103.07487> | **n = 334** | **Median probability two developers pick the same name = 6.9%.** Yet a given name is usually understood by the majority. |

### 6.3 What actually matters, in order of evidential strength

1. **Word-ness beats length, and length is not the mechanism.** *Shorter names are slower*
   (Hofmeister). **[B]**
2. **Task depth gates the effect.** Benefit for semantic defects, none for syntax errors
   (Schankin). Siegmund's beacon null is plausibly the same fact — their semantic-cues task was
   arguably recognition rather than comprehension, which they concede in Threats to Validity.
   **[B]**
3. **Expertise gates the effect, and gates it POSITIVELY.** Benefit only for experienced
   developers (Schankin); style effects dominated by training (Binkley). **The naive "novices
   need good names most" prediction is inverted in the data.** **[B]**
4. **Consistency/correctness beats richness.** Misleading original names erased the advantage
   over single letters (Avidan & Feitelson); linguistic antipatterns raise load (Fakhoury).
   **A wrong descriptive name can be worse than no name.** **[B]**
5. **Domain knowledge is largely uncontrolled.** Feitelson's 6.9% agreement means *"a meaningful
   identifier" is not a controlled stimulus* — nearly every study confounds name semantics with
   the reader's domain familiarity. No study cleanly dissociates them. **[A] as a methodological
   critique.**
6. **Typographic style is the weakest lever**, dominated by prior training. **[B]**

### 6.4 The reconciliation

**Identifier semantics is a HUMAN-FACING affordance, not a computational substrate of
comprehension.** It reduces the cost of arriving at an understanding you could also reach by
tracing — and the reduction only materialises when the task is deep enough to need
understanding *and* the reader is expert enough to exploit the cue. That is exactly the
"neural efficiency" pattern Siegmund found: cues **lower load**; they do not **add capability**.

---

## 7. Production: writing code rather than reading it

**Report honestly: this literature is one study, one reanalysis of that study, and zero
independent replications.**

### 7.1 The one direct neuroimaging study

**Krueger, Huang, Liu, Santander, Weimer & Leach (2020), "Neurological Divide: An fMRI Study of
Prose and Code Writing", *ICSE 2020*.** <https://dl.acm.org/doi/10.1145/3377811.3380348> ·
PDF <https://yuhuang-lab.github.io/paper/huang-icse2020.pdf> **[C]**

- **n = 30 recruited, 24 usable** after motion/noise exclusion. 27 undergraduates + 3 graduates,
  mean **5.2 semesters** of CS coursework — i.e. **novices**. All native English, right-handed.
- Genuinely impressive apparatus: an **fMRI-safe 101-key QWERTY keyboard** (metal and control
  logic removed, 3D-printed replacements, shielded 30-ft wires through an RF waveguide) with a
  live syntax-highlighting editor — real typing, not button boxes.
- 2 × 2: {code, prose} × {Fill-in-the-Blank 30 s, Long Response 60 s}. FDR q < 0.05,
  ≥ 20-voxel clusters.
- **Code > Prose overall** (2.4 ≤ t ≤ 6.2): left postcentral/superior parietal (BA5) into BA4/6;
  right diffuse lateral prefrontal (BA9–10); lateral temporo-occipital/temporoparietal
  (BA18–19, 39–40); bilateral anterior insula (BA13); SMA and cingulate.
- **Long Response Code vs Prose is the clean dissociation:** prose production →
  **left MTG/STG (BA21–22)** and left IFG (BA44); code production → **right-lateralized**
  superior parietal lobule/precuneus (BA7), right temporoparietal (BA19, 39), ventral
  occipito-temporal.
- **Fill-in-the-Blank code > prose** engaged dorsal premotor / pre-SMA, frontal eye fields, and
  the dorsal attention network. Authors' reading: *"the production of even a single element of
  code may require more careful, top-down control to effectively plan and produce a
  context-relevant answer."*
- **Expertise was not tested.** No demographic/psychological correlate survived FDR.

### 7.2 The reanalysis that softens it — under-cited

**Karas, Jahn, Weimer & Huang (2021), "Connecting the Dots: Rethinking the Relationship between
Code and Prose Writing with Functional Connectivity", *ESEC/FSE 2021*, 767–779.**
<https://yuhuang-lab.github.io/paper/huang-fse21.pdf> **[C]**

Seed-based functional connectivity on the *same archival dataset*. **Code > Prose: left IFG
(BA44, Broca's) ↔ right inferior temporal gyrus (BA37, the Number Form Area)** — MNI 50,−44,−8;
k = 428; peak t = 5.89; p < 0.001 **voxel-wise uncorrected**. Their boxed conclusion: *"Unlike
previous work that found code and prose writing to be distinct, we find a significant functional
connection between Broca's area … and … the Number Form Area."* Also: RSPL connectivity was
**stronger for prose than code**, partially inverting Krueger's modular reading.

**So the single production result's headline is analysis-method-dependent.** Localization says
"distinct"; connectivity says "Broca's talks to the number-form region." Neither is replicated.
**[D] on the "code writing is neurally distinct from prose writing" claim as a settled fact.**

### 7.3 The cognitive/psych model of production is settled, and it is NOT plan-then-translate

This literature is much older, much better, and answers the question decisively.

- **Guindon (1990), "Knowledge exploited by experts during software system design", *IJMMS*
  33(3):279–304.** <https://doi.org/10.1016/S0020-7373(05)80120-8> — think-aloud protocols of
  expert designers. Design is **opportunistic**: designers shift abstraction levels
  unpredictably, drift between requirements/solution/evaluation, and **discover requirements
  while generating partial solutions.** Companion: Guindon (1990), *HCI* 5(2–3):305–344.
- **Visser (1990), "More or less following a plan during design: opportunistic deviations in
  specification", *IJMMS* 33(3):247–278.** <https://doi.org/10.1016/S0020-7373(05)80119-1> —
  **the reconciling result, and the one to cite if citing only one:** an expert working *with an
  explicit hierarchical plan* **still deviates opportunistically** whenever a deviation is
  locally cheaper (data at hand, cost of switching). **The plan is real; the execution is
  opportunistic.** **[B]**
- **Davies (1990, 1991)** — plans/schemas are genuine knowledge structures, but *strategy* is
  jointly determined by notation, external representation and expertise. Expert **strategy** is
  opportunistic even where expert **knowledge** is schematic.
- The prose-writing analogue, **Hayes & Flower (1980)** planning–translating–reviewing, moved
  the same way in later revisions: the three processes are **recursive and interleaved**, not
  sequential stages.

**Settled answer: opportunistic and interleaved, with schema-driven content. Schemas are the
knowledge level; opportunism is the control level. These are not competing claims.**

### 7.4 The gap that matters most

Krueger et al. themselves concede (§7.3 of their paper) that their tasks "cover the act of
writing but not *explicit planning*." **So the single imaging study of production measured the
translation phase — while 35 years of protocol analysis located all the interesting behaviour in
the planning phase.** There is, as of 2026, **no neuroimaging of program planning/decomposition
at all.** Any claim in our synthesis about "how the brain decomposes a spec" is therefore an
extrapolation from MD-system theory, not a measured fact. Flagged as such below.

---

## 8. Implications for a graph-native synthesis architecture

*Written by the orchestrator after both spike tracks landed, against the measured
arc-1/2/3 results. Confidence tags carry over from the sections above.*

### 8.0 The measured context, with the numbers read back from the tree

From `PROGRAM_SYNTHESIS_ARC_SUMMARY.md`, `PROGRAM_SYNTHESIS_ARC2_SUMMARY.md` and
`PROGRAM_SYNTHESIS_ARC3_SUMMARY.md` in this directory, so the mapping below is against real
figures rather than a paraphrase:

| Fact | Figure |
|---|---|
| Internal battery trajectory | .520 → .616 (stall fixed **in the rules**) → .640; **no step CI-separated**; claims carried by paired identity lists |
| MBPP zero-shot (STRESS) | **0.42%** [0.07, 2.32] |
| MBPP arc 2 (paired NL-mined content diet) | **7.00%** [4.48, 10.80], n = 257 |
| MBPP arc 3 (whole-program retrieval + adaptation + screen) | **8.17%** [5.41, 12.17] |
| Arc 1 H6 | +3.2 pp, CI spans zero; **entire delta = 4 spine ids**; enumerator carried 63/77 accepts |
| Arc 1 H7c | +3.2 pp CI-spans-zero, **the SAME four spine ids**; chunk rung-1 accepts **0**; enumerator 78/99 accepts |
| Arc 2 HQ3 | **−0.39 pp**, CI [−5.01, +4.22]. **FULL's 18 passes are a strict SUBSET of CONTENT-STRIPPED's 19** — content bought **zero exclusive passes and cost exactly one.** All 24 of FULL's `gapped:exhausted` rows (a class **absent** from CONTENT-STRIPPED, 0/257) carry a cued construction |
| Arc 3 HR1 | net_passes = 2 (3 gains, **1 regression**), CI [−3.97, +5.55]; task 17 = a retrieved trap preempting a correct enumerator solution |
| Arc 3 trap mass | **55.6–60.0%** of revealed-row-passing candidates fail their held-out row |
| Arc 3 retrieval oracle ceiling | **12/257 = 4.67%** — the maximum any as-is/permute retrieval could reach |
| Where the mass actually is (arc 2 FULL) | `gapped:enumerate_failed` **55.3%** + `accepted_holdout_fail` **26.8%** = **82.1%** of outcomes |
| Spec recognition | **99.6%** on MBPP; HQ2's verdict verbatim: *"recognition was never the bottleneck"* |

**RECONCILED (orchestrator, 2026-08-01): both figures were wrong — they were remembered, not
counted. Measured: `pytest --collect-only` over the 27 arc-1/2/3 synthesis suites collects
**832 test node ids**. The defensible claim is therefore: *the verdict layer has never produced
a wrong accept that a gate caught, across 832 gated node ids and three powered batteries
(125 + 257 + 257 tasks × multiple arms).* Do not quote "~1,900" or "~3,000" — neither was ever
derived. This is the same failure mode CLAUDE.md's 2026-07-21 retraction names: a remembered
count standing in for a counted list.**

### 8.1 The convergence: the literature independently predicts our three nulls

We ran three preregistered arcs installing progressively better *proposal content*
(shape chunks; NL-paired mined chunks + triggers + bigrams; whole-program retrieval).
All three returned null-to-marginal deltas at power, each with a measured **trap
cost** — arc 2's "decoy tax" (a cued wrong proposal spends the attempt budget before
search runs) and arc 3's trap preempting a correct enumerate pass.

Three independent findings above say this is what *should* have happened:

1. **Soloway & Ehrlich [B]** — under plan/structure conflict, **66% of wrong answers
   were the plan-like answer**, and advanced programmers were statistically
   indistinguishable from novices. The plan channel does not merely fail to help; it
   produces *confident, structured wrongness*. That is our decoy tax, in humans.
2. **Pennington [B]** — reading builds the **program model** (control flow first;
   function/purpose *worst*, 34% error). The functional/purpose layer appeared only
   **after a modification task**, at which point the error ordering **inverted**.
   Abstraction is a **residue of acting on code**, not an input to reading it. Our
   arcs installed abstraction as an input. That is the shape of the mistake.
3. **Adelson [B]** — abstraction trades detail access for compression; on
   concrete-detail questions novices *outperform* experts. An eager abstractor is
   net-negative when the task needs the detail. Synthesis needs the detail.

**Consequence, stated as a standing architectural rule:**
> **A language/plan-derived candidate is never an answer. It is at most an
> escalation trigger or a proposal that must survive execution.**

Our verdict layer (ProgEval + held-out rows) already enforces this and has never
miscarried in ~3,000 gated checks. The correct use of the language stack is therefore
*upstream* (structuring the spec, grounding vocabulary, deciding where to look) and
*downstream* (explaining, naming), **never** as the thing that decides correctness.

### 8.2 Where the language stack legitimately does work — and where it must not

The neural evidence is blunter than the project's premise — but **less blunt than my first
draft of this section claimed, and the correction is instructive.** I originally wrote here
that comprehension is carried by MD "**not the language network [A]**". That is the
conditions-stripped popular form. Per §1.1–1.5 as finally merged: the **MD-carries-it** half is
[A]; the **not-language** half is **[B]**, and it rests on Ivanova's *ScratchJr* null
(β = 0.15, p = 0.29, n = 19) — in *Python* the language network responded well above the
nonword floor (β = 0.78, p < 0.001). And Liu, Wilson & Bedny (2024) decoded `for` vs `if`
from **lateral temporal language cortex better than from anywhere else in the brain**, and
*earlier* than fronto-parietal cortex: **univariate weakness is not representational absence.**
The honest position is §1.4's: the language network computes an early surface-structural
representation the reasoning network consumes; what it demonstrably does *not* do is process
identifier meanings or evaluate correctness. (I let a memorable slogan outrun its condition —
the exact defect CLAUDE.md's retraction rule exists to catch.)

With that correction in force: **[A]** for MD carrying comprehension, **[B]** for the language
network not carrying it (Ivanova 2020; Srikant 2022 MVPA; contrary evidence in §1.5). And the
one place we *assumed* language contributes — identifier semantics — is where the
neural story is **most cleanly falsified [B]**: English-vs-Japanese identifiers,
β = 0.03, p = 0.84; "variable language" was the single property decodable from
*neither* system. Peitek's vocabulary effect loaded on **BA6 working memory**, not
lexical semantics: a **capacity** story, not a **semantics** story.

So "code is a language, so reuse the language stack" needs sharpening to survive
contact with the evidence:

| Use the language stack for | Evidence | Our machinery |
|---|---|---|
| Turning a **spec** (real prose) into structured roles/goals | specs *are* natural language — uncontested | `comprehend_text`, verb frames, referent resolution |
| **Grounding unknown spec vocabulary** ("prime", "palindrome") | behavioural, not neural; the term must become *usable*, not merely recited | `ground_unknowns` → teacher → `taught_*`; `Concept.definition` |
| **Explaining / naming** produced code | production is right-lateralized parietal, prose is left MTG/IFG [C] — different systems, so treat naming as a separate, cheap, non-load-bearing pass | RenderRules, elaboration chain |
| **NOT** for deciding what the program is | Soloway 66%; Ivanova null | — |
| **NOT** for identifier-semantics-driven proposal | β = 0.03, p = 0.84 | — |

The honest reframe: **the spec is language; the program is not.** Comprehension of
the *request* is a language problem; comprehension and construction of the *code* is
an MD/executive problem — which in our substrate means search, simulation, and the
graph fixpoint. This is a good match to where our capability already measurably lives.

### 8.2b Six further findings from the second track, and what each implies

These complement §8.1–8.2 rather than repeating them.

**F-A — The construct vocabulary PRE-EXISTS the notation. [B]** Liu & Bedny (2025): `for` vs
`if` decodable from IPS/PFC **before any programming instruction**, from plain-English
pseudocode; PRE→POST representational similarity significant; **"no clear evidence of
representational change"** after a semester. **Implication: our construct codebook's payoff is
NOTATION-INDEPENDENCE, not capability** — one held shape serving python/rust/lua/LLVM, which is
exactly what P2/P5 delivered and which *did* pay. **Stop expecting codebook growth to move a
benchmark; expect it to move CROSS-FRAME TRANSFER, and measure it there.** *Supported-by our
three nulls — they are what this predicts.*

**F-B — Retrieved candidates cause fixation, and expertise does NOT protect against a
plausible-but-wrong retrieval. [B]** Sheridan & Reingold (2013): with an advantageous-but-
**suboptimal** familiar move, **8/17 experts and 8/17 novices chose it — no expertise
advantage**; only outright **blunders** were escaped. Bilalić (2008): eye movements stay on the
first solution's features while the player believes he is still searching. Sergeyuk (2023): 44%
mental-set prevalence in Python developers, and **both de-fixation interventions failed.**
**Implication, and it is the sharpest one in the document: the literature says do NOT try to
de-bias the proposer — that is the intervention that failed in humans. Make the verdict strong
enough to reject the plausible wrong candidate.** Our `accepted_holdout_fail` = 26.8% and trap
mass 55.6–60% *are* the suboptimal-but-plausible regime, definitionally. **The answer is more
discriminating rows, not a better ranker.** *Strongly supported-by arc 2's decoy tax and arc 3's
task-17 preemption.*

**F-C — Expert memory advantage SURVIVES SCRAMBLING: it is many small chunks, not a few large
plans. [A — best-powered result in this review]** Sala & Gobet (2017) meta-analysis: 24 studies,
903 participants, r̄ = .41 → **.29 after trim-and-fill**; **programming r̄ = .36**, all six
programming studies positive. **Implication: this CONTRADICTS the direction of the arc-3
escalation.** We went *up* in grain (idioms → whole programs); the best-powered human evidence
puts expert code memory at the *fine* end, and our own **4.67% retrieval oracle ceiling** is the
same fact in our data. **We could have predicted that ceiling before running the arc.**
*Caveat against over-reading: the Omniglot arc's finer-grain probe FRAGMENTED and lost 7.6 pp.
The grain corridor has now been probed at three points and all three are null-or-negative on
benchmark value.*

**F-D — MD preferentially encodes RUNTIME STEPS; the language system encodes static/structural
properties. [B] — but every DIRECT manipulation is null. [B null]** Srikant et al. (2022): the
"dynamic property" is literally **the number of instructions executed**, and MD decodes it
significantly better than the language system does *and* better than it decodes static
properties. The authors' own recommendation — *"modeling dynamic runtime information as well as
static code structure should be explored"* — is "execution decides," written independently.
**But: Ivanova's direct control-flow manipulation was null; Peitek's McCabe (execution-path
count) correlates with BOLD at τ ≈ .04–.09, essentially zero, and with neither response time nor
correctness; Medeiros reports effort SATURATING.** *Supported-by our verdict-layer result;
tempered by the fact that no one has ever shown neural load scaling with trace length.*

**F-E — Human comprehension load is driven by DATA-DEPENDENCY TRACKING, not execution-path count,
and the failure mode is SWAPS. [B] — the most actionable NEW finding here.**
Peitek (2021): **DepDegree τ = .32–.41 vs McCabe τ = .04–.09.** Crichton (2021): ~7 variable/value
pairs held; **errors are predominantly variable↔value SWAPS, not forgetting**; and the "on-demand"
strategy traces **backward along data dependencies**. Vainio & Sajaniemi (2007): novice failure is
**single-value tracing** — one live slot.
**Two independent literatures converge on the same rule: when you cannot retrieve, go BACKWARD
from the goal along DATA DEPENDENCIES.** That is Crichton's on-demand strategy and it is Rist's
focal expansion (§8.3(2)) arriving from a completely different direction — which materially
raises confidence in that recommendation.
**Concrete consequence for our ledger: P7-B's known blocker "acc-dependent fold bodies are
invisible to init-pinned derived rows" is a DATA-DEPENDENCY blocker, and F-E says that is the
class that matters most.** Promoting it is justified on external evidence, not just internal
tidiness.

**F-F — Semantic cues LOWER COST; they do not ADD CAPABILITY. [B]** Siegmund (FSE 2017):
semantic-cue comprehension showed **lower activation in all regions at matched response times**
— while the **beacon manipulation itself was null**. Crosby (2002): correctness 63% (intermediate)
vs 66% (advanced) — **n.s.**; only reaction time separated them. Schankin (2018, n = 88): ~14%
faster, but **only for semantic-defect tasks and only for experienced developers**.
**Implication: every human result on beacons, plans and names is a LATENCY result. Our arcs
measured ACCURACY and found nulls — which is exactly what this predicts.** If held content has
value, the instrument is **attempts-to-accept / fuel / time-to-accept**, not pass rate.
**Flagged as the most likely just-so story in this document** (see §8.4b): "the effect is real,
you measured the wrong thing" is what a dying hypothesis says. Only a **preregistered cost-metric
bar, taken as a null if it nulls**, makes this legitimate rather than motivated reasoning with a
citation attached.

### 8.3 The mechanisms worth building (ranked by expected value)

**(1) The annotation/bind layer — Letovsky + Brooks [B], and it is graph-shaped.**
Comprehension is complete when every implementation entity is **bound** to a goal it
realizes. Ported: `realizes` edges from `Goal`/sub-goal nodes to IR nodes; per-node
bind status (unbound / singly / multiply bound); **unbound code** = an implicit gap;
**dangling goal** = a different gap kind; **multiply-bound** = a delocalized plan, a
first-class warning (Letovsky & Soloway: local-cue comprehension there "systematically
produces wrong conclusions"). This gives a **termination test for reading and for
synthesis that is neither a token budget nor a confidence score**, and it feeds the
existing `SelfConcern` → `StandingConcern` spine we already proved closes. We do not
have this today. It is the cheapest genuinely new capability in the spike.

**(2) Focal expansion — Rist [B] — a proposal shape that is neither retrieval nor
blind search.** Locate the **focal line** that directly realizes the goal
(`total = total + x` for a running total), then expand **backward** to its
prerequisites (initialize, guard, output). Schema present → forward generation;
**no schema → backward from the focus.** Our descent already builds skeletons with
holes; focal expansion says *which* hole to open first and in what order, derived
from the goal rather than from a stored template. It degrades gracefully in exactly
the direction our data prefers (toward search).

**(3) Abstraction as residue of modification — Pennington's inversion [B].** Do not
mine abstractions from static reading (we did; it nulled three times). Derive the
functional layer from the **diff between pre- and post-modification execution
behaviour** — i.e. from programs the agent *solved and then perturbed*, observing
what changed. Then test whether that representation transfers. This is a genuinely
different experiment from arcs 1–3, not a fourth re-run of the same one, and the
human evidence specifically predicts it should work where static mining did not.

**(4) Budget isolation for cued proposals — a cue is speculative and must NEVER consume the
enumerator's budget. — HIGH EV, and the single most defensible recommendation in the document.**
*Supported-by:* F-B (Bilalić's attentional capture; Sheridan & Reingold's no-expertise-protection;
**Sergeyuk's failed de-biasing interventions**, which say fix the budget rather than the
proposer); arc 2's 24 `gapped:exhausted` rows all carrying a cued construction, a class **absent
from CONTENT-STRIPPED (0/257)**; arc 3's task-17 preemption. *Concretely:* a separate small
budget for cued proposals that cannot preempt the enumerator, and arc 3's screen generalised from
`NOT_SLACK`-scoped to always-on. *Contradicted-by:* nothing — and it is the one axis across three
arcs that already produced a durable attributable win.

**(5) Strengthen the VERDICT layer's discriminating power rather than the proposer. — HIGH EV.**
*Supported-by:* the arc's central fact; `accepted_holdout_fail` 26.8%; trap mass 55.6–60%;
F-B, F-D. *Concretely:* row generation/strengthening, property checks, and **differential
execution across the four frames we already have** — python/rust/lua/LLVM with **zero measured
toolchain disagreements** is an under-used oracle sitting in the tree. The highest-leverage single
move is converting `accepted_holdout_fail` into `rejected_before_accept`. *Weak external echo:*
Castelhano et al.'s insula result — an early error-monitoring signal whose activity at the moment
of *bug suspicion* predicted subsequent detection precision — is the only neural analogue of a
pre-accept screen anywhere in this literature **[C]**.

**(6) Re-measure held content on a COST instrument, once, with a preregistered bar. — MEDIUM EV,
HIGH INFORMATION.** *Supported-by:* F-F. *Contradicted-by:* our three accuracy nulls — which is
the point: this is a **different instrument**, not a fourth run at the same one. If it nulls,
held content is closed as a capability lever and scoped permanently to cross-frame transfer (F-A)
and human-facing rendering (§8.2). **Take the null if it comes.**

**(0) The thing that is actually binding, ranked outside this list because it needs no spike to
justify: close the SEARCH-REACH gap.** `gapped:enumerate_failed` is **55.3% of all outcomes** —
nothing else in the ledger is close — and the named residuals are concrete (`append` write-back
22 occurrences; comprehensions 18; `map`/lambda 15; no `Mod`/floor). **The neuroscience has
essentially nothing to say about this, which is itself a finding: the literature reviewed here
bears on PROPOSAL and VERDICT, while our binding constraint is OPERATOR COVERAGE and ENUMERATOR
REACH.** On expected pass-rate movement this is first, and **this spike should not displace it.**

### 8.4 The one existing asset the spike revealed

The substrate already contains a closed **propose-from-NL → verify-by-execution**
loop that nobody wired to the code arcs: `construction_grammar.extract_function` +
`comprehend_recursive` (order-N compositional slot recursion) → candidate formal
functions → `scripts/oeis_extract_verify.py` selects among them **against real OEIS
ground-truth values**. That is our architecture's exact shape, on prose, already
working — but with a tiny vocabulary (10 clauses, 5 member forms, 4 aggregators,
4 filters) and **never powered or measured** (no results artifact).

Per §8.2 this is the *legitimate* use of the language stack: the spec is language, and
execution decides. It is also the natural home for the `Concept.definition → Term`
compiler that would make "prime"/"palindrome" *usable* rather than recitable.

### 8.4b Findings that CONTRADICT our architecture, or my reading of it

Listed deliberately, because a review that only finds support is not a review.

1. **The arc-3 grain escalation ran the wrong way relative to F-C.** The best-powered result in
   this document says expert code memory is many small chunks; we escalated to whole programs.
   Our own 4.67% oracle ceiling is the same fact, and was predictable in advance.
2. **RETRACTED WITHIN THIS DOCUMENT.** An earlier draft listed Prat et al. (2020) here as
   "real evidence pointing the other way." **On inspection of the paper's own numbers it does not
   support its headline** (fluid reasoning ≈ 2× language aptitude; near-identical zero-order
   correlations; "math aptitude" = 8 health-numeracy items), and three larger follow-ups —
   Graafsma **n = 282**, Finke **n = 132 pre-registered**, and Hartmann's **null** transfer
   experiment — point away from it. See §5.5. **What survives as genuine counter-evidence is
   Kuo & Prat (2024)'s expertise-modulated P600 — but a P600 is not a language-network
   signature** (it is elicited by music, arithmetic, and artificial-grammar violations), so it is
   compatible with a domain-general sequence processor.
2b. **The real contradiction is Liu, Wilson & Bedny (2024) — and it is stronger than anything
   Prat offered.** `for` vs `if` decodes from **lateral temporal LANGUAGE cortex better than from
   anywhere else in the brain**, not from surface words, and **earlier than fronto-parietal
   cortex**. **Design consequence, stated honestly: if the language network computes an early
   surface-structural representation that the reasoning network consumes, then our language stack
   MIGHT have a legitimate role — but it is a STRUCTURAL/PARSE role, not a semantic one, and it is
   upstream of the verdict.** In our terms that is the construction-bigram/lattice layer and the
   IR lift, both of which we already have. **It is still not an argument for routing Concepts or
   identifier meanings into synthesis.**
3. **Floyd et al. (2017) contradicts our design instinct.** If code becomes *more* prose-like with
   expertise (r = −0.44, p = 0.016, n = 29), a mature system should recruit *more* language
   machinery, not less. **The one replication attempt failed** (Fucci 2019, n = 28, τ = 0.16,
   p = 0.31) — hence [D] — but if it is true, our direction is wrong.
4. **The only ALE meta-analysis in the field comes down on the LANGUAGE side.** Ikutani, Itoh &
   Kubo (2021): 7 studies, mean n ≈ 20, preprint, and it fails to recover left parietal regions
   that four separate studies report — but it is the only synthesis that exists, and it disagrees
   with §1's conclusion.
5. **The 2026 "Dual neural foundations" paper claims early language involvement in learning.**
   Graded [C/D] because "statistically indistinguishable" is an accepted null dressed as a
   finding and it uses atlas labels not localizers — **but the full text was unreachable (403),
   so that grade is partly inference from an abstract.** Endres et al. (n = 31, fNIRS) points the
   opposite way in the same population. **Unresolved.**
6. **Ivanova's stimuli were tiny** — "short, only a few basic elements of control flow," no
   functions, no objects, no multi-component programs. **Every claim resting on that dataset is
   about SNIPPET-SCALE comprehension.** Whether the language network is recruited for
   multi-function, named-abstraction-heavy programs is untested — and that is the regime real
   synthesis lives in.
7. **F-F's reframe is the most likely place this document is fooling itself** (see below).

### 8.4c Just-so-story flags

Marking every place the mapping is rhetorically satisfying and evidentially weak:

- **"MD = our verdict layer" is an ANALOGY, not a measurement.** Duncan's own "mental programs"
  phrasing invites the interpreter metaphor; it has never been tested as a computational claim
  about program execution.
- **"Bins propose, continuous decides" and "MD encodes dynamic, LS encodes static" are NOT the
  same claim.** One is proposal-vs-verdict; the other is which system carries which property
  type. The parallelism is pleasing and must not be allowed to do argumentative work.
- **Reverse inference is endemic in the SE half of this literature and this document has partly
  inherited it.** Every "BA21 = word semantics" statement in §1.3 and §6.1 is an
  atlas-plus-citation attribution — exactly what functional localizers exist to prevent.
- **No study anywhere manipulated execution-step count or trace length.** "MD load scales with
  trace length" — the closest neural analogue of ProgEval fuel — is **unmeasured**, and the
  nearest direct tests are **null**. Peitek's Halstead ↔ BA6 r ≈ 0.60 is a *static* metric,
  n = 19, selected from 41 candidates against 4 regions.
- **Liu & Bedny's recycling result is about `for` vs `if` in beginner Python.** Extending it to
  "the construct codebook is innate" is an extrapolation the authors explicitly decline.
- **Section 8.2's clean "the spec is language; the program is not" is a slogan.** It happens to
  fit the evidence, and it is also exactly the kind of memorable formulation that survives past
  the point where it is true. Hold it to the falsifiers below.
- **n across this whole literature is 6–76, mostly 11–30.** Our own standing rule — *deltas
  within ~3× the per-episode step are not results* — would disqualify a large fraction of what is
  cited above if applied to it.

### 8.5 What would falsify the recommendations here

- If the annotation layer's gaps do not correlate with actual synthesis failures, it
  is bookkeeping, not comprehension — measure the correlation before trusting it.
- If focal expansion's hole ordering does not beat the current descent ordering on a
  powered gate, Rist's finding does not transfer to a machine with different memory
  constraints — a real possibility, since the human result is partly about *working
  memory*, which we do not share.
- If modification-derived abstraction nulls too, then proposal content is not merely
  mis-derived in this architecture but **structurally unpayable at this scale**, and
  the honest conclusion is that capability belongs entirely to search + verdict +
  spec comprehension. That would be a fourth null and should end the proposal-content
  line rather than motivate a fifth.

### 8.6 Standing methodological caveat

Almost every classic result above is **n = 6 to n = 139, from the 1980s, rarely
formally replicated**, and the one modern powered check in the vicinity (Fowler 2022,
n = 612) went against the strong form of a related claim. The modern fMRI work is
better controlled but small (n = 11–62). **Treat the mechanisms as implementable
hypotheses; do not size a prediction from any effect size in this document.** Our own
R0-style measured ceilings remain the only legitimate basis for a bar.

---

## 9. Bibliography

**Neuroimaging — code comprehension**
- Ivanova, Srikant, Sueoka, Kean, Dhamala, O'Reilly, Bers & Fedorenko (2020). Comprehension of computer code relies primarily on domain-general executive brain regions. *eLife* 9:e58906. <https://elifesciences.org/articles/58906> **[A]**
- Srikant, Lipkin, Ivanova, Fedorenko & O'Reilly (2022). Convergent representations of computer programs in human and artificial neural networks. *NeurIPS*. <https://arxiv.org/abs/2205.11470> **[A/B]**
- Liu, Kim, Chatterjee, Weimer, Fedorenko et al. — longitudinal code-learning fMRI (see §1). **[B]**
- Siegmund, Kästner, Apel, Parnin, Bethmann, Leich, Saake & Brechmann (2014). Understanding understanding source code with functional MRI. *ICSE*. <https://dl.acm.org/doi/10.1145/2568225.2568252> **[B]**
- Siegmund, Peitek, Parnin, Apel, Hofmeister, Kästner, Begel, Bethmann & Brechmann (2017). Measuring neural efficiency of program comprehension. *ESEC/FSE*. **[B/C]**
- Peitek, Apel, Parnin, Brechmann & Siegmund (2021). Program comprehension and code complexity metrics: an fMRI study. *ICSE*. <https://arxiv.org/abs/2101.05128> **[B]**
- Floyd, Santander & Weimer (2017). Decoding the representation of code in the brain: an fMRI study of code review and expertise. *ICSE*. **[B]**
- Krueger, Huang, Liu, Santander, Weimer & Leach (2020). Neurological divide: an fMRI study of prose and code writing. *ICSE*. <https://dl.acm.org/doi/10.1145/3377811.3380348> **[C]**
- Kuo & Prat (2024). Expertise-dependent responses to form and meaning violations in code. *Scientific Reports*, N=62. **[B]**
- Amalric & Dehaene (2016). Origins of the brain networks for advanced mathematics in expert mathematicians. *PNAS* 113(18):4909–4917. **[A]**
- Fedorenko, Behr & Kanwisher (2011). Functional specificity for high-level linguistic processing in the human brain. *PNAS*. **[A]**

**Behavioural — plans, schemas, chunking, comprehension models**
- Soloway & Ehrlich (1984). Empirical studies of programming knowledge. *IEEE TSE* SE-10(5):595–609. <https://dl.acm.org/doi/10.1109/TSE.1984.5010283> **[B]**
- Soloway, Ehrlich & Gold (1983). Reading a program is like reading a story (well, almost). *CogSci*. <https://escholarship.org/uc/item/0zg6b8gv> **[B]**
- Pennington (1987). Stimulus structures and mental representations in expert comprehension of computer programs. *Cognitive Psychology* 19:295–341. **[B]**
- Brooks (1983). Towards a theory of the comprehension of computer programs. *IJMMS* 18:543–554. **[B]**
- Letovsky (1986/87). Cognitive processes in program comprehension. *ESP / JSS*. **[B]**
- Letovsky & Soloway (1986). Delocalized plans and program comprehension. *IEEE Software*. **[B]**
- Rist (1989). Schema creation in programming. *Cognitive Science* 13:389–414. **[B]**
- Adelson (1984). When novices surpass experts: the difficulty of a task may increase with expertise. *JEP:LMC* 10(3):483–495. **[B]**
- Shneiderman (1976/77). Exploratory experiments in programmer behavior; measuring computer program quality and comprehension. **[B]**
- McKeithen, Reitman, Rueter & Hirtle (1981). Knowledge organization and skill differences in computer programmers. *Cognitive Psychology* 13:307–325. **[B]**
- Gilmore & Green (1988). Programming plans and programming expertise. *QJEP* 40A:423–442. **[B]**
- Détienne (2001). *Software Design — Cognitive Aspects*. Springer. **[B]**
- Fowler et al. (2022). Reevaluating the relationship between explaining and doing (n=612). **[A/B]** — the modern powered check.

*Confidence tags: **[A]** replicated / well-powered / multi-lab · **[B]** single credible study or consistent small-n line · **[C]** single small study, unreplicated, or contested interpretation.*

---

### 9b. Additional verified sources (second track)

**Code — the reversal and the longitudinal evidence**
- **Liu, Y.-F., Wilson, C. & Bedny, M. (2024). Contribution of the language network to the comprehension of Python programming code. *Brain and Language* 251:105392.** <https://doi.org/10.1016/j.bandl.2024.105392> **[B] — the under-cited reversal; see §1.4b.**
- **Liu, Y.-F. & Bedny, M. (2025). Learning to program "recycles" preexisting frontoparietal population codes of logical algorithms. *Journal of Neuroscience* 45(45):e0314252025.** <https://pmc.ncbi.nlm.nih.gov/articles/PMC12590113/> **[B]**
- Liu, Kim, Wilson & Bedny (2020). *eLife* 9:e59340. <https://elifesciences.org/articles/59340> **[B]**
- Srikant, Lipkin, Ivanova, Fedorenko & O'Reilly (2022). NeurIPS. <https://proceedings.neurips.cc/paper_files/paper/2022/hash/77b5aaf2826c95c98e5eb4ab830073de-Abstract-Conference.html> **[B]**
- **Huang, X., Yang, W. & Looi, C.K. (2026). Dual neural foundations of coding cognition. *NeuroImage* 338:122053.** PMID 42285449 **[C/D] — fNIRS, within-session, not longitudinal.**
- **Bergum, Peitek, Rekrut, Siegmund & Apel (2026). On the Influence of the Baseline in Neuroimaging Experiments on Program Comprehension. *ACM TOSEM* 35(3).** <https://doi.org/10.1145/3744739> — **the field's disagreements track baseline choice almost exactly.**
- Bergum, Maurer, Peitek, Bader, Mecklinger, Demberg, Siegmund & Apel (2026). Fixation-related potentials… late frontal positivity. *Scientific Reports* 16:16833. <https://arxiv.org/abs/2412.10099> **[C]**
- Ikutani, Itoh & Kubo (2021). The neural bases of program comprehension: a coordinate-based fMRI meta-analysis. bioRxiv 2021.04.15.439937 — 7 studies, mean n ≈ 20, still a preprint **[C]**
- Peitek, Bergum, Rekrut, Mucke, Nadig, Parnin, Siegmund & Apel (2022). Correlates of programmer efficacy… *FSE 2022*. <https://arxiv.org/abs/2303.07071> — n = 37 **[B]**
- Fucci, Girardi, Novielli, Quaranta & Lanubile (2019). A replication study… *ICPC 2019*. <https://doi.org/10.1109/ICPC.2019.00050> — **the failed expertise replication** **[B]**
- Huang, Liu, Krueger, Santander, Hu, Leach & Weimer (2019). Distilling neural representations of data structure manipulation… *ICSE 2019*. <https://web.eecs.umich.edu/~weimerw/p/weimer-icse2019-preprint.pdf> — **n = 76** **[B]**
- Karas, Jahn, Weimer & Huang (2021). Connecting the Dots… *ESEC/FSE 2021*. <https://yuhuang-lab.github.io/paper/huang-fse21.pdf> **[C]**
- Endres, Karas, Hu, Kovelman & Weimer (2021). Relating Reading, Visualization, and Coding… *ICSE 2021*. <https://arxiv.org/abs/2102.12376> **[C]**
- Castelhano, Duarte, Ferreira, Durães, Madeira & Castelo-Branco (2018). The role of the insula in intuitive expert bug detection. *Brain Imaging and Behavior*. <https://doi.org/10.1007/s11682-018-9885-1> **[C]**
- Ikutani et al. (2021). Expert programmers have fine-tuned cortical representations of source code. *eNeuro* 8(1). <https://pmc.ncbi.nlm.nih.gov/articles/PMC7877476/> **[C]**

**Math, logic, formal grammar**
- Amalric & Dehaene (2016). *PNAS* 113(18):4909–4917 — n = 15 + 15 **[B]**; Amalric & Dehaene (2019). *NeuroImage* 189:19–31 — n = 14, **language ROIs track morpheme count R = 0.64** **[B]**
- Amalric, Roveyaz & Dehaene (2023). *PNAS* 120(6):e2213430120 — **short videos do not change the math network**
- Ansari (2016). *PNAS* 113(18):4887–4889 — the developmental critique
- Fedorenko, Duncan & Kanwisher (2013). *PNAS* 110(41):16616–16621 — the domain-generality objection
- Monti, Parsons & Osherson (2009). *PNAS* 106(30):12554–12559 — n = 15 **[B]**; (2012). *Psychological Science* 23(8):914–922 — n = 21 **[B]**
- Fedorenko, Behr & Kanwisher (2011). *PNAS* 108(39):16428–16433 — **per-task n = 11–15** **[B]**
- **Varley, Klessinger, Romanowski & Siegal (2005). Agrammatic but numerate. *PNAS* 102(9):3519–3524** — **n = 3**; bracket expressions 45/52/43 of 64 with serial-order errors of 4/1/2, against picture naming of 0/60 **[B]**
- Fedorenko & Varley (2016). *Ann NY Acad Sci* 1369(1):132–153. <https://pmc.ncbi.nlm.nih.gov/articles/PMC4874898/> **[A]**
- **Counterweight — group lesion studies find ASSOCIATIONS at larger n:** Baldo & Dronkers (2007) n = 68; **Baldo, Bunge, Wilson & Dronkers (2010), *Brain & Lang* 113:59–64, n = 107 VLSM**
- **Kean et al. (2026). Evidence from formal logical reasoning… *PNAS* 123(28):e2520095123** — deductive reasoning distinct from **both** language and MD; **n unverified (403)** **[C]**
- **Malik-Moraleda, Taliaferro, Shannon et al. & Fedorenko (2023). Constructed languages are processed by the same brain mechanisms as natural languages. *PNAS*** — **the strongest contrastive control** **[B]**
- Shain, Kean, Casto, Lipkin, Affourtit, Siegelman, Mollica & Fedorenko (2024). Distributed sensitivity to syntax and semantics throughout the language network. *J Cogn Neurosci* 36(7):1427–1471 — **you cannot borrow "just the syntax part."**
- Petersson, Folia & Hagoort (2012). *Brain and Language* 120(2):83–95 — n = 32; **"a generic on-line sequence processor"** **[B]**
- Uddén & Männel (2018). *Oxford Handbook of Psycholinguistics*, ch. 33 — the AGL meta-analysis counterweight **[B]**
- Friederici, Bahlmann, Heim, Schubotz & Anwander (2006). *PNAS* 103(7):2458–2463 — n = 37; **single marginal interaction F(1,34) = 4.96**; DTI on n = 4 **[C]**
- Fitch & Friederici (2012). *Phil Trans R Soc B* 367:1933–1955 — **the AⁿBⁿ counting concession**
- Musso et al. (2003). *Nature Neuroscience* 6(7):774–781 — n = 8/experiment; **subjects learned the "impossible" language nearly as well** **[D]**
- **Kuo & Prat (2024). *Scientific Reports* 14:5807** — 2×2 form × meaning in code; **P600 b = 2.97 μV, N400 b = −1.71 μV, expertise × syntax t(488) = 5.18** **[B]**

**Aptitude and learning**
- Prat, Madhyastha, Mottarella & Kuo (2020). *Scientific Reports* 10:3817 — **[C], downgraded in §5.5**
- Kuo, Mottarella, Haile & Prat (2022). SoftCOM — n = 80; acquired knowledge dominates
- **Graafsma, Robidoux, Nickels, Roberts, Polito, Zhu & Marinus (2023). *J Cognitive Psychology*** — **n = 282**; math latent β = .493 vs language latent β = .057
- **Finke, Kemény, Sommer, Krnjic, Arendasy, Slany & Landerl (2022). *Computer Science Education*** — **n = 132, pre-registered**; figural reasoning, not arithmetic
- **Hartmann, Bergum, Gorgosch, Peitek, Apel & Siegmund (2024). arXiv:2402.01657** — **the null transfer experiment**
- Bergersen & Gustafsson (2011). *J Individual Differences* 32(4):201–209 — n = 65; WM fully mediated by knowledge

**Tracing, simulation, notional machines**
- Lister et al. (2004). *ITiCSE-WGR* — n = 941/556 **[B]**; Lopez, Whalley, Robbins & Lister (2008). *ICER* **[B]**; Lister, Fidge & Teague (2009). *ITiCSE* — the strongest replication
- **Cunningham, Blanchard, Ericson & Guzdial (2017). *ICER* — tracing HURTS on code-fixing** **[B]**
- Xie, Nelson & Ko (2018). *SIGCSE* — n = 24, the only randomised intervention, with a self-efficacy confound **[C]**
- **Crichton, Agrawala & Hanrahan (2021). The Role of Working Memory in Program Tracing. *CHI*.** <https://arxiv.org/abs/2101.06305> — **~7 pairs, SWAP errors, backward on-demand strategy** **[B]**
- Hassan & Zilles (2023). *SIGCSE* — tracing is under-deployed, not merely mis-executed **[C]**
- Busjahn et al. (2015). *ICPC* — execution order, **n = 6 experts, stimulus-complexity confound** **[C]**
- Sorva (2013). Notional Machines. *ACM TOCE* 13(2), Art. 8 **[A as a survey]**; du Boulay (1986). *JECR* 2(1):57–73
- Sajaniemi (2002). Roles of variables. *IEEE HCC*
- Medeiros et al. (2021). *Sensors* 21(7):2338 — **effort saturates** **[C]**

**Expertise, chunking, fixation**
- **Sala & Gobet (2017). Experts' memory superiority for domain-specific random material generalizes across fields of expertise. *Memory & Cognition*.** <https://pmc.ncbi.nlm.nih.gov/articles/PMC5323477/> — **24 studies, 903 participants, programming r̄ = .36** **[A]**
- **Bilalić, McLeod & Gobet (2008). Why good thoughts block better ones. *Cognition* 108(3):652–661** **[B]**
- **Sheridan & Reingold (2013). *PLOS ONE* 8(10):e75796** — **8/17 experts and 8/17 novices chose the suboptimal familiar move** **[B]**
- Sergeyuk, Titov, Golubev & Bryksin (2023). arXiv:2307.06673 — **44% mental-set prevalence; both interventions failed** **[C]**
- Rist (1989). Schema creation in programming. *Cognitive Science* 13:389–414 — **forward on retrieval, backward from focus on search** **[B]**
- Crosby, Scholtz & Wiedenbeck (2002). *PPIG 14*:58–73 — **"beacons may be in the eye of the beholder"** **[C]**
- Détienne (1990). <https://arxiv.org/abs/cs/0702003>; Détienne (1995). *HCI* 10(2–3):129–170. <https://arxiv.org/abs/cs/0612008>
- Guindon (1990). *IJMMS* 33(3):279–304 and *HCI* 5:305–344; **Visser (1990). *IJMMS* 33(3):247–278 — the plan is real, the execution is opportunistic** **[B]**
- Wyrich, Bogner & Wagner (2023). 40 Years of Designing Code Comprehension Experiments. *ACM CSUR*. <https://doi.org/10.1145/3626522> — 95 experiments, 1979–2019

**Identifiers**
- Lawrie, Morrell, Feild & Binkley (2007). *ISSE* 3(4):303–318; Binkley et al. (2012). *EMSE* 18(2):219–276; **Hofmeister, Siegmund & Holt (2019). *EMSE* 24(1):417–443 — shorter names are SLOWER**; **Schankin et al. (2018). *ICPC* — n = 88, ~14%, gated on task depth and expertise**; **Feitelson et al. (2022). *IEEE TSE* 48(1) — 6.9% naming agreement**; Avidan & Feitelson (2017). *ICPC* — n = 9; Fakhoury, Ma, Arnaoudova & Adesope (2018). *ICPC*

---

## 10. The experiments that do not exist, and would settle this

Recorded because the gaps are as informative as the findings:

1. **No study manipulates execution-step count or loop-iteration count and tests MD scaling.**
   This is the direct neural test of the ProgEval analogy, and every proxy for it is null
   (Ivanova's control-flow contrast; Peitek's McCabe τ ≈ .04–.09).
2. **No study combines individual-subject language localizers with a code syntax × semantics
   manipulation.** Kuo & Prat have the design; Ivanova has the localizers; nobody has both. Until
   then "code syntax engages the language network" is an inference across two incompatible method
   families.
3. **No causal evidence for code at all** — no lesion, aphasia, or TMS study of code
   comprehension exists.
4. **No neuroimaging of blind programmers**, despite Bedny's lab doing both blindness plasticity
   and code, and despite occipital cortex in congenital blindness taking on both language and
   symbolic-math functions. An obvious, well-motivated missing experiment.
5. **No neuroimaging of program PLANNING/decomposition** — the one production study measured
   translation and says so.
6. **Two research communities barely cite each other**: cognitive neuroscience (strong
   localizers, toy stimuli) and software engineering (realistic code, anatomical reverse
   inference). The only meta-analysis sits on the fault line and inherits the SE side's methods.

**Three claims in this literature are conditions-stripped quotations, and all three appear in
popular summaries without their conditions** — a failure mode this project has a standing rule
about:
- **"Code is not language"** — conditional on *univariate* analysis and on the ScratchJr null
  (p = 0.29, n = 19); reversed multivariately (§1.4b).
- **"Language aptitude beats math aptitude"** — conditional on stepwise unique variance with an
  8-item health-numeracy scale; the zero-order correlations are near-identical (§5.5).
- **"BA44 computes hierarchy"** — conditional on AⁿBⁿ not being solvable by counting, which the
  stimuli did not exclude (§5.5c).

---

## 11. Late corrections (2026-08-01, post-merge)

A fourth spike track (code vs math vs language networks) landed after §§1–10 were merged.
Its findings correct three things in this document and add one methodological warning that
bears directly on this repo's standing rules. Recorded here rather than silently edited in,
so the correction is auditable.

**C1 — Fedorenko et al. (2019) is mis-cited across this literature, including by us.**
It is a four-author *forum piece* (Bers is the fourth author) that made **no directional
prediction**; it explicitly proposed a framework for generating hypotheses. Any sentence
that treats it as having predicted "code is/isn't language" is reading a position into a
prospectus.

**C2 — the Prat et al. (2020) "language aptitude beats math aptitude" numbers.** The actual
figures are **17% vs 2% unique variance (≈8.5×, not ≈2×)** — but the **zero-order
correlations are statistically indistinguishable** (.56/.52, .54/.54, .45/.42). The
headline gap is a **stepwise-regression artifact at n ≈ 28–33 between collinear predictors
of unequal reliability**, not a difference in predictive validity. §4's downgrade of this
claim to **[C]** stands and is, if anything, generous.

**C3 — "code is not language" is weaker than its citation record, and the weakness is
structural.** It rests on an **underpowered null** (ScratchJr, β = 0.15, p = 0.29, n = 19)
**with no equivalence test**, has **never been independently replicated outside the
Fedorenko/Bedny orbit**, and has been complicated *by those same labs* since 2024
(Liu, Wilson & Bedny decoded `for` vs `if` **best-in-brain** from lateral temporal language
cortex, *earlier* than fronto-parietal). This is the same correction §8.2 already applies
to my own [A]-grading error; C3 says the underlying literature is weaker still. **The
strongest evidence in the whole area is not the code-vs-language contrast at all — it is
the math/logic dissociations** (Monti 2009/2012; Amalric & Dehaene 2019), because there the
**difficulty confound runs the wrong way** (the formal task was *harder* yet produced
*less* perisylvian activation), and because language-area activation tracked **grammatical
morpheme count (R = 0.64)** rather than math content.

**C4 — the methodological warning, and it is one of ours.** Bergum et al. (2026, TOSEM)
shows **baseline choice materially determines results** in program-comprehension
neuroimaging, and the field's central disagreements track baseline choice almost exactly.
That is precisely the failure mode CLAUDE.md's 2026-07-21 retraction names: **a claim held
without its condition.** Three separate claims in this literature are conditions-stripped
quotations (itemised in the track's §7). It is the same defect this document already
committed once (§8.2) and this repo already committed once (the optional-dep note). Treat
"code is not language" the way we now treat "the only bench failures are optional-dep
errors": **never quote it without its baseline.**

**Coverage gaps that could not be closed** (flagged, not papered over): Kean et al. (2026,
PNAS) sample sizes; Huang et al. (2026, *Cognitive Development*) scoping review; the exact
analysed n for Kuo & Prat 2024 (sources disagree: 45 vs 62); and a 2026 PNAS developmental
math-network paper (every route returned 403). The WebSearch budget was exhausted mid-track;
everything after that point came via direct fetch, PubMed/arXiv APIs, and local PDF reads.

**Net effect on §8's recommendations: none reverse.** C1–C3 weaken the *anti*-language
evidence, which if anything softens §8.2's "not where we assumed" framing — but §8.2's
operative conclusions were never derived from the anti-language claim. They rest on
(i) the identifier-semantics null, which is a *direct* test and survives, (ii) Soloway's
plan-shaped-wrongness result, and (iii) our own four measured nulls. C4 is the one that
should change behaviour: it is a standing-rules matter, not a finding.
