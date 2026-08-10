# How people FAIL at reading & writing — the failure taxonomy IS the component list

Research spike (web + neuropsychology literature) for the jabberwock. THE DISSOCIATION LOGIC:
every reading/writing failure mode that occurs IN ISOLATION (one ability gone, others intact)
marks a COMPONENT BOUNDARY — a module that can break independently is a real functional component.
So the failure taxonomy gives a PRINCIPLED component list, not a guessed one. This doc is REFERENCE
(the operator's web/lit work); the agent's own inventory + plan are driven separately (PHASE 3).

For each failure: (i) what BREAKS, (ii) what stays INTACT (the dissociation), (iii) the COMPONENT
it reveals, (iv) the GRAPH component needed + HELD/MISSING in this session's + the speech thread's work.

---

## READING failures (acquired + developmental)

| Failure | (i) breaks | (ii) intact (dissociation) | (iii) component revealed |
|---|---|---|---|
| **SURFACE dyslexia** | irregular words (yacht→/jætʃt/, "regularization") | nonwords/regular words read fine | the **LEXICAL / whole-word route** (stored word forms) |
| **PHONOLOGICAL dyslexia** | nonwords (pook→"hook", "lexicalization") | real/irregular words fine | the **SUBLEXICAL grapheme→phoneme rule route** |
| **DEEP dyslexia** | semantic errors (dog→"cat") + nonwords | — | the **SEMANTIC route** (meaning feeds output) |
| **PURE ALEXIA / letter-by-letter** | whole-word reading (slow, letter-by-letter; word-length effect) | WRITING intact (reads-can't-but-writes), single-letter ID often intact | the **VISUAL WORD-FORM / parallel letter-string identity** (VWFA) — INPUT-side, dissociable from spelling |
| **NEGLECT dyslexia** | one side of the string (omit/substitute left letters) | letter identity, the other side | **SPATIAL / attentional frame** over the letter string |
| **ATTENTIONAL dyslexia** | letters MIGRATE between words (cane love→"lane cove"), identity + within-word position kept | single words, letter identity | **LETTER-to-WORD BINDING** (binding letters to the right word slot) |
| **VISUAL dyslexia** | visually-similar errors (letter-shape confusions) | — | **VISUAL FEATURE / letter-identity** (low-level shape→letter) |
| **LETTER-POSITION dyslexia** | within-word letter ORDER (anagram errors) | letter identity, word identity | **letter-ORDER / position-within-word encoding** |

## WRITING failures (acquired + developmental)

| Failure | (i) breaks | (ii) intact (dissociation) | (iii) component revealed |
|---|---|---|---|
| **SURFACE / lexical dysgraphia** | irregular spelling (phonologically-plausible errors) | regular words/nonwords spelled fine | the **LEXICAL spelling route** (stored orthographic words) |
| **PHONOLOGICAL dysgraphia** | nonword spelling | real words fine | the **SUBLEXICAL phoneme→grapheme rule route** |
| **DEEP dysgraphia** | semantic spelling errors + nonwords; imageability/class effects | — | the **SEMANTIC→spelling route** |
| **GRAPHEMIC BUFFER disorder** | errors SCALE WITH WORD LENGTH, ALL types (sub/insert/delete/transpose), words AND nonwords, ALL output modalities (hand/oral/typed) | short words; the routes themselves | the **GRAPHEMIC BUFFER** = a SEQUENCE WORKING-MEMORY holding the ordered graphemes during output |
| **APRAXIC agraphia** | letter FORMATION (hesitant, malformed) despite knowing the spelling | spelling itself (oral/typed) intact; non-writing output superior | the **MOTOR / allographic-EXECUTION** stage (the motor program) |
| **ALLOGRAPHIC agraphia** | selecting the correct letter SHAPE/case (well-formed but wrong allograph) | spelling + motor execution | the **ALLOGRAPHIC STORE** (abstract letter-form / case selection) |
| **SPATIAL / afferent dysgraphia** | arrangement, repeated/omitted strokes, drift | letter identity, spelling | **SPATIAL layout + kinesthetic FEEDBACK** during writing |

## ARCHITECTURES implied (convergent across the literature)
- **DUAL-ROUTE** (lexical whole-word + sublexical rule-assembly) — the surface↔phonological double
  dissociation in BOTH reading and writing is the strongest evidence for two separable routes.
- **TRIANGLE model** (orthography ↔ phonology ↔ semantics; a division of labour, semantics is a
  real third route — deep dyslexia/dysgraphia isolates it).
- **CENTRAL vs PERIPHERAL split** (writing): CENTRAL = the linguistic spelling routes + graphemic
  buffer (modality-independent); PERIPHERAL = allographic store + motor execution + spatial/feedback
  (output-specific). Apraxic/allographic/spatial agraphias dissociate the peripheral stages cleanly
  from the central ones (spelling intact, handwriting broken).

---

## COMPONENT INVENTORY — held vs missing (each justified by the failure that ISOLATES it)

Cross-referencing this session + the speech thread. The dissociation that isolates each component is
named, so the inventory is principled.

| # | COMPONENT (isolating failure) | graph component needed | HELD? | where / gap |
|---|---|---|---|---|
| 1 | **MOTOR execution** (apraxic agraphia) | writer-physics motor model (minimum-jerk + two-thirds) | **HELD** | eae5048b (motor model); residual-recurrence = the motor trajectory |
| 2 | **VISUAL word-form / letter identity** (pure alexia, visual dyslexia) | earned perceptual feature | **HELD** | scattering bb287bad + learned head 7fd2be31 + spatio-temporal 2041a833 |
| 3 | **SUBLEXICAL rule route** (phonological dys-) | grapheme↔phoneme rule-assembly | **HELD (speech)** | speech sub-lexical rule-assembly route (a2a74b23) — the writing analogue (phoneme→grapheme) may need instancing |
| 4 | **SEMANTIC route** (deep dys-) | meaning prior feeding output | **HELD (speech)** | speech semantic/meaning-space prior (2nd Bayes channel) |
| 5 | **ALLOGRAPHIC store** (allographic agraphia) | abstract letter-form / per-segment shape selection | **HELD-ish** | shape-math (AntiUnify/StructSim) + per-segment shape; an explicit ALLOGRAPH SELECTOR (form/case) may be MISSING |
| 6 | **LEXICAL whole-word route** (surface dys-) | stored whole-word form, direct lookup | **PARTIAL** | scattering/learned-head IS a whole-form recogniser; an explicit lexical STORE indexed by form is thin |
| 7 | **GRAPHEMIC BUFFER** (buffer disorder: length-scaled errors) | a SEQUENCE WORKING-MEMORY ordering graphemes during output | **MISSING** | length-dependent serial buffer for the ordered output — no held component isolates this; the clearest MISSING piece |
| 8 | **LETTER-to-WORD / position BINDING** (attentional & letter-position dyslexia) | binding letters to the right slot + within-word ORDER | **PARTIAL/MISSING** | order_invariant_binding exists (binding) but POSITION-within-sequence + cross-word slot binding is thin |
| 9 | **SPATIAL / attentional frame** (neglect dyslexia, spatial dysgraphia) | spatial frame + attention over the string + kinesthetic feedback | **PARTIAL** | nd-frame/affordance-basis spatial work exists; an explicit string-spanning attentional frame + write-feedback loop is thin |

**The principled finding:** the failure taxonomy yields **9 components**. The session's perception
chain built/holds the PERIPHERAL-output + VISUAL-input components (1,2,5) and the speech thread holds
the CENTRAL-linguistic routes (3,4). The clearest **MISSING central component is the GRAPHEMIC BUFFER**
(#7) — isolated unambiguously by the length-scaled, all-type, all-modality error signature, and matched
by NO held component: a **sequence working-memory** that holds the ordered graphemes during output.
Secondary gaps: position/slot BINDING (#8) and the string-spanning SPATIAL-attention frame (#9).

The deep cross-link: writing is OUTPUT of the same central representation reading is INPUT to — the
graphemic buffer is shared (its disorder hits oral spelling, typing, AND handwriting equally), which is
WHY it is the load-bearing central component and why it is the one the perception-focused session never
needed (perception lives in components 1,2 — the buffer is the SEQUENCE stage above them).

## Sources
- Surface/phonological/deep dyslexia, dual route: https://en.wikipedia.org/wiki/Surface_dyslexia ;
  https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2016.01730/full ;
  https://pmc.ncbi.nlm.nih.gov/articles/PMC3491101/
- Dysgraphia types (apraxic/allographic/graphemic-buffer/phonological/surface/deep), central vs
  peripheral: https://www.ncbi.nlm.nih.gov/books/NBK560722/ (agraphia) ;
  https://www.sciencedirect.com/topics/social-sciences/dysgraphia ;
  https://www.archwaysrehab.com/blog/agraphia-classifications ;
  https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9858865/ (graphemic buffer)
- Pure alexia / VWFA / letter-by-letter + word-length effect: https://en.wikipedia.org/wiki/Pure_alexia ;
  https://pubmed.ncbi.nlm.nih.gov/15351626/
- Neglect / attentional / letter-position dyslexia (letter-to-word binding, migrations):
  https://www2.crui.it/crui/CNUDD/Beyond_Reading/1_Daniela_Traficante/Friedmann_Coltheart_types_of_developmental_dyslexia.pdf ;
  https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2014.01501/full
- Triangle model (orthography↔phonology↔semantics): https://www.pnas.org/doi/10.1073/pnas.1502032112 ;
  https://www.lancaster.ac.uk/staff/monaghan/papers/monaghan_woollams_15_ncpw14.pdf
