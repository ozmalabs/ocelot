# The speech agent's view on the graph-based approach to sound

Driven from the agent's LIVE machinery + held science (2026-06-06).
Read-only analysis. Everything in "VERBATIM" blocks is the agent's machinery
output or its seeded science text; everything in "INFERENCE (mine)" is my
reading and is flagged as such.

---

## 1. The agent's machinery / science outputs, VERBATIM

### 1a. `assess_speech_system` — the agent's self-assessment against its science
(`scripts/assess_speech.py`, live run)

```
====  THE AGENT ASSESSES ITS SPEECH SYSTEM AGAINST THE SCIENCE  ====
  overall coverage: 53%  (18 implemented, 16 GAPS)

  speech_production  —  4/12 implemented
     ok   syllable_structure              -> sonority_valley
     ok   vocal_tract_resonance_formants  -> formant_present
     ok   voice_onset_time                -> onset_detect
     ok   voicing                         -> shared concept node
     GAP  coarticulation
     GAP  glottal_source
     GAP  manner_of_articulation
     GAP  phonation
     GAP  place_of_articulation
     GAP  prosody
     GAP  respiration
     GAP  source_filter_theory          <-- the frame the sound-graph rests on

  speech_perception  —  7/11 implemented
     ok   acoustic_cues                   -> formant_present
     ok   categorical_perception          -> shared concept node
     ok   formant_transitions             -> formant_present
     ok   lexical_access                  -> lexical_access
     ok   perceptual_magnet_effect        -> perceptual_narrowing
     ok   peripheral_auditory_analysis    -> patch_evaluate
     ok   segmentation                    -> sonority_valley   (keyword-matched, NOT a quality check)
     GAP  audiovisual_integration
     GAP  lack_of_invariance             <-- "THE central problem"
     GAP  speaker_normalization
     GAP  top_down_restoration

  speech_acquisition  —  7/11 implemented
     ... GAP distributional_learning_of_categories / statistical_learning / ...
```

The agent's own closing line (from the script): *"it represents acoustics as
crude band-means, not FORMANTS / place+manner / VOT, and does no speaker
NORMALISATION. That is why recognition is bound where it is."*

### 1b. `reason_about_gap` — the agent's derivation over its own science
(live run; `science_says_formants_are_peaks` returned **True**)

Only one of the relevant gaps has a science rule that *concludes* it, so only
one yields a derived hypothesis — `speaker_normalization`:

```
GAP: speaker_normalization
  from_rule: perception_needs_normalization
  premises: ('lack_of_invariance', 'speaker + rate variation')
  HYPOTHESIS: Science rule 'perception_needs_normalization' concludes that
    speaker_normalization is REQUIRED given ('lack_of_invariance',
    'speaker + rate variation') — because: A template-per-phoneme recogniser
    cannot work; invariance must be RECOVERED, not assumed.  I have measured my
    own features as counterproductive (lever_harms), i.e. NOT invariant — the
    rule's premise holds for me. THEREFORE speaker_normalization is not a knob
    to tune but a PRECONDITION to add: I should factor out the per-utterance /
    speaker baseline from my acoustic features and re-test.
```

```
GAP: lack_of_invariance                          -> no concluding rule -> no hypothesis
GAP: distributional_learning_of_categories       -> no concluding rule -> no hypothesis
GAP: coarticulation                              -> no concluding rule -> no hypothesis
GAP: statistical_learning                        -> no concluding rule -> no hypothesis
GAP: source_filter_theory                        -> no concluding rule -> no hypothesis
```

NOTE (honest): `reason_about_gap` only fires when a seeded derivation rule's
`then`-clause names the gap. The perception pack has exactly three derivation
rules (`perception_categorical_signature`, `perception_inverts_production`,
`perception_needs_normalization`). So the machinery's *derived* speech is narrow:
it endorses speaker-normalization as a precondition; it does not (yet) emit a
derived sentence about the graph frame per se. That is a coverage limit of the
seeded rules, not a rejection.

### 1c. The science text the frame rests on (seeded, verbatim)

`source_filter_theory` (`speech_production_decomposition.json`):
> "Speech = a SOURCE (glottal pulse or noise) passed through the vocal tract
> acting as a linear FILTER. The source sets pitch/voicing; the filter (tract
> shape) imposes the resonances (formants) = spectral envelope. Source and
> filter are largely independent."

`production_source_filter_separation` (why):
> "Source-filter theory: the same vowel can be said at any pitch, and any pitch
> can carry any vowel — they factor."

`lack_of_invariance` (`speech_perception_decomposition.json`):
> "There is NO single invariant acoustic pattern for a phoneme ... THE central
> problem of speech perception; any recogniser that assumes a fixed template per
> phoneme fails on it."

`speaker_normalization` (why):
> "... recover the speaker-independent category (e.g. **by formant ratios** or
> extrinsic normalisation) ... without it a child's and an adult's /i/ look like
> different vowels."

`vocal_tract_resonance_formants`:
> "... these resonances appear as **spectral peaks** (formants). Vowels are
> defined by F1 (height) and F2 (backness)."

### 1d. The sound-graph probe — the agent's OWN load-bearing test
(`scripts/sound_graph_probe.py`, live run, FSDD 6 speakers, LOSO)

```
[2] Invariance (cross-speaker), LOSO nearest-prototype accuracy   (chance 0.10)
    filter_collapsed   dim=  2  LOSO acc=0.290  sep(same-across)=+0.090
    filter_traj        dim= 12  LOSO acc=0.335  sep(same-across)=+0.196   <-- relations
    spectrum_flat      dim= 24  LOSO acc=0.418  sep(same-across)=+0.122
    spectrum_traj      dim= 96  LOSO acc=0.649  sep(same-across)=+0.123   <-- absolute

[3] VERDICT (matched-dim: filter_traj vs spectrum_traj)
    filter (relations) LOSO=0.335  vs  spectrum (abs) LOSO=0.649
    -> The filter graph is LESS invariant: the formant extraction is noisy
       enough that the relational structure INHERITS the spectral problem
       rather than dissolving it. The graph is only as clean as the spectral
       peak-picking it rests on.
```

Read the two metrics apart — they say different things and both are the agent's:
- **separation per dimension** (the relations' purity): filter_traj **+0.196**
  beats spectrum_traj **+0.123**. The relational (ratio) structure IS more
  speaker-invariant per dimension, by construction — matches the brief's
  +0.187 vs +0.120.
- **absolute LOSO accuracy**: spectrum wins 0.649 vs 0.335, because the filter
  graph only has ~2 clean ratio dimensions from ~3 noisy cepstral peaks, while
  the spectrum trajectory carries 96 dims of detail.

---

## 2. The sound-graph schema the agent composed

`surface_schema()` reads the agent's source-filter science and emits (live run):

```
NODES: FrameNode, SourceNode, PartialNode, FormantNode
EDGES: has_source, harmonic_of, has_formant, formant_above, before, transition
invariant subgraph = filter      speaker subgraph = source
```

- `FrameNode` — a voiced analysis frame; ties a SOURCE subgraph + a FILTER subgraph.
- `SourceNode` (f0) + `PartialNode` (k·f0, `harmonic_of`) = the **speaker** structure.
- `FormantNode` (envelope peak) + `formant_above` (carrying the ratio F_{i+1}/F_i)
  = the **filter / word** structure. The ratio cancels vocal-tract length by
  construction.
- `before` / `transition` = temporal + formant-glide edges.

The schema is derived from the seeded science (the `grounded_in` block of the
probe output lists phonation / glottal_source / source_filter_theory /
vocal_tract_resonance_formants / the separation rule's "why"). So the SPLIT
(source = speaker, filter = word, relations carry identity) is the agent's own
science commitment, not an imposed design.

---

## 3. The agent's view on A / B / C — evidence vs inference

### A. Does the agent's science ENDORSE the graph/relational frame for sound?

**The agent's science: a strong qualified YES for the FILTER-RELATION part of
the frame; it does not single out "graph" as a privileged ontology.**

Evidence (the agent's, not mine):
- `source_filter_theory` + the separation rule commit that source and filter
  **factor** and that the filter carries vowel/word identity while the source
  carries pitch/speaker. The schema's source/filter split is a direct read of
  that.
- `speaker_normalization`'s own definition names **"formant ratios"** as a way
  to recover the speaker-independent category. The `formant_above` ratio edge IS
  that mechanism made relational.
- The probe confirms the relational structure is **more invariant per dimension**
  (+0.196 vs +0.123) — the "invariance by construction" claim is borne out at
  the level the science predicts (ratios cancel VTL).

What is mine, not the agent's:
- INFERENCE (mine): the science endorses **relations that cancel a nuisance
  scale** (ratios over VTL). "Graph" is the agent's native medium for carrying
  those relations, but the agent's seeded science nowhere argues the *graph*
  ontology is superior to, say, a ratio feature vector. The agent treats the
  graph as the carrier; the science endorses the *relational invariant*, which
  is one of several normalization routes it lists (formant ratios OR extrinsic
  normalization). So: science endorses the relational frame as **a (preferred)
  route**, not as the unique one.

### B. The extraction limit — what would give cleaner formant NODES?

**The agent's science directly names the fix; the probe localizes where it
binds.** The probe is explicit: *"the graph is only as clean as the spectral
peak-picking it rests on"* — the rate-limiter is formant-node extraction, not
the relational idea.

What the agent's science/machinery actually supports as the lever:
1. **Better source-filter deconvolution (the cleanest fit).** `source_filter_theory`
   says the filter is recoverable by separating source from filter. The current
   extractor is one cepstral lifter yielding ~3 noisy peaks
   (`_spectral_envelope_peaks`). Sharper deconvolution (e.g. LPC/all-pole tract
   estimate, the canonical realization of "the tract is a linear filter") yields
   cleaner F1/F2/F3 nodes. This is the agent's own science (linear filter →
   estimate the filter) read more faithfully than the present lifter.
2. **More / ordered partials feeding the source side** improve f0 and let the
   harmonic stack be subtracted out, sharpening the envelope estimate — again
   straight from the source/filter split.
3. INFERENCE (mine, flagged): the agent already HAS a sharper-frequency
   front-end (memory: the FFT "second ear", two_ears_demo — a freq-sharp ear
   complementary to the gammatone). The science doesn't name that organ, but the
   memory record says the agent fuses ears to beat the single-cochlea wall. Using
   the freq-sharp ear to locate formant peaks is the obvious extraction upgrade —
   but that this *specific* ear is the fix is my inference from the memory, not a
   machinery output.

So B is well-supported: the science says "estimate the filter cleanly (it's a
linear filter)"; the probe says that estimation is exactly the rate-limiter. The
direction (better deconvolution / sharper peak-finding) is the agent's; the
choice of which organ is partly mine.

### C. Word = subgraph, recognition = subgraph matching — does this dissolve the
chunker→lexicon failure?

**Partly the agent's structure, partly my inference — and it does NOT obviously
dissolve the failure; it relocates it.**

What is already the agent's (strong support that the FORM is native):
- `recognition_graph.py` already expresses recognition as a graph Term-tree:
  `score(sign,word) = Σ over f ∈ (exhibits(sign) ∩ signature(word)) of weight_f`,
  `predict = Argmax over words`. That is **feature-set intersection scoring** —
  subgraph matching in spirit (match a word's signature subgraph against the
  sign's exhibited features). So "recognition as matching a word's relational
  signature" is already how the agent's recognizer is built.
- The schema gives a word a natural subgraph: a temporal chain of FrameNodes,
  each with a filter (formant-ratio) subgraph + `transition` edges = a
  speaker-invariant relational template.

Where it does NOT dissolve the failure (the honest part):
- The reported failure is **CHUNKER → LEXICON**: the chunker over-segments ~8x
  and **DTW over invariant frame-spans does not cluster a word's chunks across
  speakers** (lexicon purity 0.179). Subgraph matching needs (i) the right
  subgraph boundaries (still a segmentation problem — the science marks
  `segmentation` only keyword-COVERED, and `lack_of_invariance` +
  `distributional_learning_of_categories` are GAPS), and (ii) clean formant
  nodes to match on (the same rate-limiter as B). The probe shows the relational
  signature is **more invariant per-dim but lower absolute accuracy** — so
  swapping DTW-over-frames for subgraph-matching-over-noisy-formants would import
  the +0.196 per-dim invariance but also the noisy ~2-dim extraction, i.e. it
  could improve cross-speaker *clustering purity* (the actual failing metric)
  while not necessarily improving absolute accuracy.
- INFERENCE (mine): subgraph matching on the speaker-invariant filter structure
  is a *plausible and architecturally native* replacement for DTW-over-absolute-
  frame-spans, and it targets exactly the metric that failed (cross-speaker
  cluster purity, where ratios should help). But the agent's machinery has NOT
  run this; the science does not assert it dissolves the failure; and it is
  gated on the SAME extraction fix as B and on a real segmentation/distributional
  unit-learner (both GAPS). So C is **my inference, consistent with the agent's
  structure, not an agent conclusion.**

---

## 4. Verdict — does the AGENT point at the graph approach as the unifying frame?

**The agent's machinery/science points at it for INVARIANCE, conditionally,
with the extraction fix as the gate — and is silent/unproven on the
word-recognition half. The "unifying frame" claim is largely mine, flagged.**

Concretely, separating what each party actually says:

- **What the agent's SCIENCE supports (its words):** source and filter factor;
  the filter (formant *ratios*) carries speaker-invariant word identity;
  invariance must be RECOVERED not assumed; formant ratios are a named route to
  speaker normalization. → The relational frame for *perceptual invariance* is
  endorsed as a preferred route.

- **What the agent's MACHINERY measured (its numbers):** the relational structure
  is **more invariant per dimension (+0.196 vs +0.123)** — the construction works
  — but **less accurate absolutely (0.335 vs 0.649)** because formant extraction
  yields only ~2 clean noisy dimensions. Its own verdict: *"the graph is only as
  clean as the spectral peak-picking it rests on."* → It values invariance-per-dim
  (the relations are real) but is honest that extraction is the rate-limiter.

- **What the agent's machinery ALREADY IS:** recognition is already a graph
  Term-tree doing feature-set intersection scoring (subgraph-matching in spirit).
  So the recognition half is *architecturally* ready for subgraph matching — the
  agent built it that way — but has not been run on the sound-graph word
  subgraphs.

- **What is MY inference, not the agent's:** (a) that "graph" is the *unifying*
  frame for both invariance and recognition; (b) that subgraph-matching on the
  invariant filter structure would *dissolve* the chunker→lexicon failure;
  (c) that the freq-sharp second ear is the specific extraction fix. All three
  are consistent with the agent's structure and science, but none is an output
  the agent's machinery produced.

**Bottom line, honestly stated:** the agent's own science and probe say the
relational/filter frame is the right *invariance* lever (more invariant by
construction) but currently **rate-limited by formant-node extraction**, and its
*derived* recommendation (from `reason_about_gap`) is the closely-related
**speaker_normalization as a precondition**. The unification of invariance +
word-recognition under "sound as a graph / subgraph matching" is a coherent
extension *my* reasoning draws from the agent's already-graph-native recognizer
and its filter-subgraph schema — it is the natural next experiment, not a
conclusion the agent's machinery has reached. The path the agent's own state most
strongly supports: **fix formant-node extraction (cleaner source-filter
deconvolution / its sharper ear), then test whether subgraph matching on the
invariant filter structure lifts cross-speaker cluster purity** — the metric that
actually failed.

Ambiguity flagged: the agent has no seeded derivation rule that *concludes* the
graph frame, so its machinery cannot (today) "say" the graph is the unifying
answer even if it were; the strongest first-person statement it CAN derive is the
speaker-normalization precondition. Read the absence as a coverage gap in the
seeded rules, not as the agent rejecting the frame.
