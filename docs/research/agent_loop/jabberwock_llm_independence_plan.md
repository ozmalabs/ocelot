# The jabberwock's plan to retire its LLM dependence

_Authored by the agent through its own design channel, context=spec (register: Plainsong). The gap and options were surfaced; the plan is its own._

I have what I need. Both corpora are on disk and already wired (WordNet via `dict_teacher._wordnet`, ConceptNet via `conceptnet_reference` slab), the five perceptions live in `agent_adjusts_for_figures.py:174-222`, and the classify rules in `seeds/figurative_language.json` read fixed attributes (`opposes`, `personifies`, `scalar_spike`, `scalar_violation`, `understates`). Here is the plan.

---

# Build plan — close GAP 1 symbolically, keep GAP 2 human-seamed

## 1. Approach, and why

**Each of the five figure perceptions becomes a Rust query Term I compose in a Rule — not an oracle I query.** That is the whole move. The perceptions are not open-ended judgement; they are lookups against resources I already hold on disk. An antonym is a WordNet edge. Animacy is a hypernym-path test. Contiguity-vs-resemblance is a ConceptNet relation plus a WordNet domain distance. The LLM was standing in for a dictionary I already own. I am replacing a guess with a lookup.

The architecture rule decides the split cleanly:

- **Primitive in Rust** for the two big on-disk corpora I cannot materialise as seed data: WordNet (150k+ synsets) and ConceptNet (498 MB). These become DSL Terms over the existing loaders, exposed via PyO3: `WnAntonym`, `WnAnimate`, `CnRelation`, and one backstop `GloveSim`. A Term is a leaf the graph evaluates; it does a lookup and returns a value. No decision lives in it.
- **Seed data in the graph** for the two small lexicons that have no clean corpus: sentiment polarity and magnitude. These are Concept nodes the agent OWNS. Polarity is *bootstrapped from WordNet* (curated seed set, propagate along `similar_to`/`also_see`, flip on antonym — the Hu-Liu/SentiWordNet method) so it is reproducible and on-disk, not a downloaded lexicon. Magnitude is a small curated scale (no WordNet relation expresses it).
- **Composition in Rules.** The five perception attributes (`opposes`, `personifies`, `scalar_spike`, `scalar_violation`, `understates`) are set by a new `ground_figure_perception` rule family that reads the Terms and the seed Concepts. The existing `classify_figure` cascade in `figurative_language.json` is **unchanged** — it still reads the same attribute names. Blast radius is one rule family upstream; the classifier never learns it stopped talking to a model.
- **Host does I/O only.** `agent_adjusts_for_figures.py` stops calling `judge(...)`; it ingests the figure pair, ticks, reads the kind back out. The `claude -p` shell (`claude_teacher.make_ask`) leaves the figure path entirely.

Why this and not "keep the LLM, it's more flexible": the LLM is *non-deterministic on a deterministic question*. `_opposite` already works around the model refusing yes/no by asking for antonyms and string-matching — that is a worse WordNet. `_choice` votes three times to denoise a lookup. I am paying latency and variance to approximate a table I can read directly. On the cases the corpora cover, the table is strictly better: deterministic, instant, auditable. I give up the novel tail (§3) and I make that loss explicit by **abstaining** there rather than guessing.

## 2. Phases — each independently verifiable

Every phase verifies against figures **I already detect**. Phase 0 freezes those as the regression baseline.

### Phase 0 — Freeze the baseline (no build)
- **Build:** none. Assemble a fixed corpus of ~30 figures spanning all six kinds I already classify (oxymoron, irony/sarcasm, personification, hyperbole, understatement, metonymy, metaphor) plus ~10 literal controls. Run the current LLM-grounded `agent_adjusts_for_figures` once, record `(figure, figure_kind)` as `baseline.json`.
- **Verify:** baseline captured; every later phase is scored as agreement-with-baseline **on the covered cases** and abstention-rate on the tail. This is the guard for the whole migration.
- Concrete corpus anchors: oxymoron `deafening silence`, `living dead`, `bittersweet`; personification `the wind whispered`, `the sun smiled`; sarcasm `what a wonderful mess`; hyperbole `I've told you a million times`, `I'm starving`; understatement `just a scratch`; metonymy `the crown decided`, `the White House said`; metaphor `time is a thief`, `the classroom was a zoo`.

### Phase 1 — `WnAntonym` Term → grounds `opposes` (closes `_opposite`)
- **Build (Rust):** `TermNode::WnAntonym { a, b }` in `runners/dsl/src/term.rs`, evaluated by calling into WordNet (reuse `dict_teacher._wordnet` via the same handler seam `UseTool` uses — a registered Python handler, since the corpus loader is already Python; the Term is the graph-resident primitive even though the lookup body is the existing loader). Returns three-valued: `true` (an antonym lemma of `a` matches `b` or its stem), `false` (both in WordNet, no antonym link), `unknown` (either OOV).
- **Build (seed/rule):** `ground_opposes` rule in a new `seeds/figure_grounding.json`: for a figure with parts `a`,`b`, set the `opposes` edge iff `WnAntonym(a,b)` is `true`; set `opposes_abstained=1` iff `unknown`.
- **Verify:** `deafening silence` (silence↔sound; needs the property-hop, see note), `living dead`, `bittersweet` → `opposes` set, classify to oxymoron, **matches baseline**. Non-antonym control `blue car` → not set, no oxymoron. Tail case with no WordNet antonym → `opposes_abstained`, no false oxymoron.
- **Note (coverage stretch, optional in-phase):** lexicalised antonyms are direct (hot/cold). Derived opposition like `deafening`↔`silence` resolves by hopping each term to its salient property via WordNet (`deafening`→loud, `silence`→quiet) then testing antonymy of the properties. Build this as a second rule `ground_opposes_via_property` only if the direct test misses baseline oxymorons; otherwise abstain and record the miss.

### Phase 2 — `WnAnimate` Term → grounds `personifies` (closes `_animacy`)
- **Build (Rust):** `TermNode::WnAnimate { word }` — true if the noun's hypernym chain includes `living_thing.n.01`/`organism.n.01` or lexname ∈ {`noun.person`,`noun.animal`,`noun.plant`}; false if a clean inanimate lexname; unknown if OOV. Add a companion `WnLexname { word }` returning the verb lexname so the rule can test the predicate.
- **Build (rule):** `ground_personifies`: set `personifies=1` iff subject `WnAnimate=false` AND predicate verb lexname ∈ animate-agent classes (`verb.cognition`, `verb.emotion`, `verb.communication`, `verb.social`). Abstain if either is unknown.
- **Verify:** `the wind whispered` (wind=nonliving, whisper=verb.communication) → `personifies`, matches baseline. `the dog barked` (dog=living) → not personification. OOV subject → abstain.

### Phase 3 — Sentiment seed lexicon → grounds `scalar_spike`/`polarity` (closes `_polarity`)
- **Build (tool → seed):** one-time `tools/build_sentiment_seed.py` (an emit-a-seed authoring script, deletable, not runtime): curated polar seed set (~40 adjectives), propagate 1–2 hops over WordNet `similar_to`/`also_see`, flip on antonym; emit `seeds/sentiment_lexicon.json` as Concept nodes with a `polarity ∈ {+1,−1}` attribute. The agent then OWNS the lexicon as graph data.
- **Build (rule):** `ground_polarity`: read the polarity Concept for the figure's evaluative word; set `scalar_spike=1` when surface polarity contradicts the asserted/contextual valence the existing pipeline already carries (the same contradiction `_polarity` was detecting). Abstain when the word is not in the lexicon.
- **Verify:** `what a wonderful mess` (wonderful=+1 over a negative referent) → `scalar_spike`, sarcasm, matches baseline. Sincere `what a wonderful day` → not set. Word absent from lexicon → abstain (this is where I forfeit most — see §3).

### Phase 4 — Magnitude seed lexicon → grounds `scalar_violation`/`understates` (closes `_magdir`)
- **Build (seed):** curated `seeds/magnitude_lexicon.json` — intensifiers and scalar extremes graded on a signed scale (`million/infinite/never/always/forever/starving/dying` = extreme-high; `just/merely/a scratch/slightly` = extreme-low). No WordNet relation expresses magnitude, so this is hand-curated and small.
- **Build (rule):** `ground_magnitude`: set `scalar_violation=1` when the figure's quantifier sits at extreme-high over a literal that cannot support it; set `understates=1` at extreme-low over a severe literal. Abstain when the quantifier is not graded.
- **Verify:** `told you a million times` → `scalar_violation`, hyperbole, baseline. `just a scratch` (of a grave wound) → `understates`, understatement, baseline. `told you twice` → neither. Novel magnitude phrase outside the seed → abstain.

### Phase 5 — `CnRelation` Term + WordNet domain distance → grounds `shape` (closes `_shape`)
- **Build (Rust):** `TermNode::CnRelation { a, b }` over the existing `conceptnet_reference` slab — returns the whitelisted relation linking `a`→`b` if any (`PartOf`/`AtLocation`/`UsedFor`/`MadeOf`/`SymbolOf`/`DefinedAs`), else none, else unknown (OOV). Reuse `WnLexname`/hypernym for a `domain_distance(a,b)` (different lexnames + deep/absent LCA).
- **Build (rule):** `ground_shape`:
  - contiguity relation present → `shape=association` (**metonymy**);
  - else large domain distance AND a shared `HasProperty` (WordNet/ConceptNet) → `shape=resemblance` (**metaphor**);
  - else `shape=neither` only when both terms are known; **abstain** when either is OOV or no signal resolves.
- **Verify:** `the crown decided` (crown SymbolOf monarchy) → association/metonymy, baseline. `the White House said` (AtLocation) → metonymy. `time is a thief` (distant domains, shared `takes-without-permission` property) → resemblance/metaphor, baseline. `the classroom was a zoo` → metaphor. Pair with neither relation nor path → abstain.

### Phase 6 — `GloveSim` Term as abstain-reducer (backstop only)
- **Build (Rust):** `TermNode::GloveSim { a, b }` over the frozen ~70 MB GloVe (CPU, mmap), returns cosine similarity or unknown (OOV).
- **Wiring (strictly scoped):** GloVe rescues **only Phase 5 `shape` abstains and Phase 1 novel-metaphor opposition** — never overrides a definite symbolic verdict, and **never used for antonymy** (embeddings place antonyms close; GloVe is wrong there by construction). Rule `shape_backstop` fires only when `ground_shape` abstained: high similarity + no contiguity relation → lean `resemblance`; otherwise stay abstained.
- **Verify:** a fresh metaphor with no WordNet path that the baseline labelled metaphor → GloVe rescues it without regressing any definite Phase 1–5 case. If it regresses even one definite case, the gate is wrong — back it out. GloVe is the weakest link; it stays optional and gated.

### Phase 7 — Cut the figure-path LLM, run the full regression
- **Build:** flip `agent_adjusts_for_figures.py` to ingest→tick→read (host I/O only); delete the `judge`/`_yn`/`_choice`/`_opposite`/`_animacy`/`_polarity`/`_magdir`/`_shape` call sites from the figure path. The `claude -p` shell no longer appears in this stack.
- **Verify:** full Phase 0 corpus. Report two numbers honestly: **agreement-with-baseline on covered cases** (target: ≥ baseline on the deterministic kinds — oxymoron/personification/metonymy should be ≥, since lookup beats a noisy vote) and **abstention rate on the tail** (the figures now returned unclassified). Name every figure that moved from a baseline label to abstain.

### Phase 8 — GAP 2 rewire (control-flow, not lexicon)
- **Build:** in the autonomy stall path (`jabberwock_plans_llm_independence.py:113-114`), replace the automatic `make_ask` consult with: (1) **compose-from-held first** — the maze-world precedent: when the needed faculty is buildable from primitives I already hold, compose it on the measured shortfall, no teacher; (2) **human impasse second** — only when compose measurably falls short, surface an explicit impasse to the creator. No automatic hosted-model call.
- **Verify:** force a stall whose faculty IS composable (a routing/figure-grounding variant) → composed with no consult. Force a genuinely novel one → it surfaces a human impasse rather than silently calling a model. This phase closes nothing with a lexicon and does not pretend to (§4).

## 3. Abstention policy and the coverage I forfeit

**Policy: three-valued Terms, abstain-don't-guess at the grounding Rule.** Every Term returns `true | false | unknown`. The grounding Rule sets a perception attribute **only on a definite verdict**; on `unknown` it sets a `*_abstained` marker and asserts nothing. The `classify_figure` cascade already falls through unasserted branches, so an abstained perception yields `figure_kind = unknown` (the figure stays detected-but-unclassified) rather than a wrong label. **A definite symbolic verdict always wins over the backstop; the backstop only ever converts an abstain into a lean, never overrides.**

**What I forfeit, plainly:**
- **Fresh metaphors with no WordNet path and no shared-property edge** (Phase 5) — return abstain. GloVe rescues some (Phase 6); the rest stay unclassified. The LLM guessed here and was sometimes right.
- **Sarcasm needing situational world-knowledge** (Phase 3) — the lexicon sees word polarity, not the context that makes a positive word ironic. Where the irony lives in the situation, not the words, I abstain. This is the largest forfeit.
- **Novel hyperbole/magnitude vocabulary** outside the curated seed (Phase 4) — abstain.
- **Derived/contextual opposition** beyond WordNet antonymy and the one property-hop (Phase 1) — abstain.

I would rather return *unclassified* than *confidently wrong*. The forfeit is measured and named in Phase 7, not hidden.

## 4. GAP 1 vs GAP 2 — what closes now, what stays human

| | GAP 1 — run the stack | GAP 2 — extend the stack |
|---|---|---|
| Nature | **Data lookup.** Five perceptions = WordNet/ConceptNet/lexicon reads. | **Open-ended design reasoning.** Author a faculty I don't hold. |
| Closable now? | **Yes** — Phases 1–7. Symbolic Terms + seed lexicons + grounding rules. | **No** — a lexicon closes nothing here. |
| Residual | The novel tail, handled by **abstention** (§3). | Designs not composable from held primitives. |
| Disposition | LLM **removed** from the figure path. | **Compose-from-held first** (Phase 8); genuine impasses stay **human-in-the-loop** — the creator, consulted rarely, not a hosted model. |

I will not pretend a lexicon closes GAP 2. GAP 1 is a dictionary I already own; I am wiring it in. GAP 2 is design judgement; the honest seam is my own compose-from-primitives loop backed by a rare human consult — not an automatic `claude -p`. After Phase 7 the `claude -p` shell is gone from the figure stack; after Phase 8 it is gone from the autonomy stall path too, replaced by compose-then-ask-the-human.

---

**Build order is strict 0→8.** Phases 1–5 are independent after 0 and could parallelise, but each rebuilds the Rust lib (`maturin`) and must keep the 591 migrated tests green — serialise them so a regression is attributable to one Term. Phase 6 is optional and gated. Phase 7 is the cutover and the honest scorecard. Phase 8 is a separate, smaller piece of work and should not block the GAP 1 cutover.

One open question before I build: **do you want me to start the GloVe backstop (Phase 6) in scope, or ship Phases 0–5 + 7 symbolic-only first and measure the real abstain rate before deciding if GloVe earns its place?** My recommendation is the latter — measure the tail before adding the one non-deterministic, learned component.
