# Encyclopedic seeds — the jabberwock reads its own prose (next migration campaign)

## The precise finding (investigated 2026-06-19)

Of the 245 seed manifests on disk:
- **10** carry NATIVE `match`/`effects` rules (the migrated core: intent,
  decision_core, conversation_reply, …) — these fire under `run_rules()`/`tick()`.
- **146** carry LEGACY PROSE rules in two old domain-installer schemas:
  - **115** `{name, head, body}` — a framing + a prose FACT
    (e.g. head="Jabberwock considers historical transformation",
    body="agriculture ~10,000 BCE enabled settled populations, surplus, …").
  - **31** `{name, if, then, why [, soundness_category, cites_prior_work]}` —
    natural-language REASONING PRINCIPLES (e.g. if="instructions are decomposed
    into independent stages" then="throughput approaches 1 instr/cycle").
- **89** carry no rules (knowledge-only).

**State:** ZERO of the 146 legacy-rule seeds are registered/bootable. The Rust
`load_seed_manifest` does NOT silently skip their rules — it **rejects** them
(`bad seed rule JSON: missing or non-array 'match'`), so a legacy seed can't load
at all through it. They are dark: 146 encyclopedias the agent never reads.

**Why a schema-converter is the wrong tool:** the legacy rules are PROSE, not
graph patterns. `match`/`effects` rewrites match typed triples and add edges;
prose ("agriculture enabled settled populations") has no triples to match. You
can't translate the format — you have to UNDERSTAND the content.

## The approach (the creator's steer: "the jabberwock can read prose")

Don't write a Python parser — have the AGENT read its own encyclopedia. The
reading faculty already exists (and is a world adapter per CLAUDE.md — it
sequences the agent's own graph-resident machinery, owns no reasoning):

- **`domains/read_and_ground.py`** — `read_and_ground(substrate, concept, conversation)`:
  GAP (low coherence) → READ the definition → COMPREHEND with the construction
  grammar → GROUND via `built_from` edges over held concepts, recursing toward
  the seeded primitives → RE-COHERE. The general read→comprehend→ground loop.
  Grounds the `head/body` FACTS (the body's concepts → grounded built_from).
- **`domains/ground_reductions.py`** — reads a STATEMENT, comprehends its LOGICAL
  STRUCTURE as an IMPLICATION (antecedent predicate ⇒ consequent value), grounds
  the antecedent by composing held primitives. This is EXACTLY the `if/then/why`
  shape — the 31 principle-seeds ground through this path.
- **`domains/prose_to_operation.py`** — reads full-text prose → extracts the
  OPERATIONAL RULE (the transformation a construction defines), not just the
  genus. For principles that define an operation, not just an implication.

So the conversion = a **read-and-ground campaign**: for each of the 146 seeds,
the jabberwock reads its prose rules (the text is already in the seed — no
external fetch needed) and grounds them into graph-native form — `head/body` →
grounded concepts + `built_from`; `if/then/why` → a grounded Implication
(antecedent⇒consequent over held concepts). The grounded seeds then register +
boot, and their reasoning is graph-resident (and, where grounded to a predicate,
can FIRE).

## First slice — DONE (2026-06-19, the faculty runs + the grounding seed)

The first slice landed: the reading faculty RUNS graph-native on the seed-booted
WorldAdapter and grounds encyclopedic prose end-to-end.

- **`read_and_ground` runs on the seed-booted agent** — no CuriousAgent
  dependency. It comprehends a definition ("X is a `<genus>` …") via the
  construction grammar, writes the `built_from` edge, and recurses toward the
  seeded primitives. Verified by feeding the prose through a mechanical `_Reader`
  (`_definition_feed` = the seed's own text; decides nothing).
- **The precise blocker, found + fixed graph-natively.** Comprehension produced
  the genus but the `built_from` Concept->Concept edge was INADMISSIBLE (Type-2:
  'Concept' not in the edge vocabulary) and `ground_concept`'s `try/except`
  silently dropped it — so the concept never bottomed out at a primitive. The
  old CuriousAgent opened those Γ productions at construction
  (`grounded_representation.open_grounding_productions`). The fix is a **new
  `grounding` seed** (`seeds/grounding.json`, registered) carrying the 5
  productions as graph data (Concept->{built_from,depends_on,grounds,genls} +
  Microtheory-has_concept->Concept). Loaded through the Rust loader — no Python
  setup call.
- **End-to-end proof:** with the `grounding` seed booted, `recognition` grounds
  to the seeded `perception` primitive and `mistrust` to `belief`
  (grounded=True, primitive in the cone); without it the SAME prose comprehends
  the genus but stalls (grounded=False, no primitive) — the seed is the
  load-bearing difference. Migrated twin: `tests/test_read_and_ground_migrated.py`
  (5 tests). Migrated bench green at 566.

**The remaining campaign gap (characterized, NOT yet closed):** the everyday
encyclopedic concepts don't yet bottom out at the seeded primitive base — the
bedrock is math/relations/psychology, not everyday ontology (`agriculture ->
practice -> activity -> process` never reaches a seeded primitive). And the
`if/then` principles do NOT parse against `comprehend_theorem`'s math-theorem
grammar (honest residual: "a theorem-form to acquire as a construction"). So the
146 need (a) an everyday-ontology bedrock the cone can reach, and (b) general
(non-math) statement constructions for the principles. Both are the multi-session
body of the campaign — the faculty + the admissibility are now proven to work.

## Second slice — DONE (2026-06-19, the dictionary closes the bedrock gap)

The first slice's remaining gap was: everyday concepts don't bottom out at the
seeded primitive base (math/relations/psychology), so `agriculture` never
grounds. Creator's steer: **"if only it had a dictionary."** It does — WordNet —
and it was already built but unwired. Wired now:

- **`seeds/lexical_ontology_roots.json` (the BEDROCK, registered).** WordNet's
  unique-beginners (entity / abstraction / physical_entity /
  psychological_feature / attribute / object / group) as basis-primitive
  Concepts + is-a (`built_from`) edges mirroring WordNet hypernymy, so every
  lexical-genus chain bottoms out at the single root `entity`. Was in a
  high-level authoring schema the Rust loader IGNORED (its nodes never
  installed); rewritten to the low-level `nodes`/`edges` manifest the loader
  consumes. `depends_on grounding` (its `built_from` edges need the opened Γ
  productions from the first slice).
- **`domains/wordnet_genus.py` (the dictionary reader).** Added
  `hypernym_chain(word)` — walks WordNet's hypernym POINTERS from the dominant
  sense (sense-CONSISTENT: carries the synset, so `act` stays the action sense,
  never hops to `legal_document`) — and `ChainReader`, which stages that ladder
  as a `_definition_feed` the agent reads. Mechanical: WordNet names the
  pointers; no meaning decision. Keys both surface forms (space + underscore) so
  the descent doesn't desync when the grounding underscore-normalises a
  multi-word genus.

**Result:** everyday nouns ground to `entity` graph-natively. Naive per-word
re-lookup (`read_definition` each link) hops senses and ~20% wander past all 7
roots (11/14); the sense-consistent `ChainReader` grounds the lot (24/24 on the
spot-check). Migrated twin `tests/test_lexical_genus_descent_migrated.py` (7).

**Multi-word lemmas — fixed (creator's catch: "it should have this
comprehension — perhaps it is the wiring/duplication").** `body_of_water` was
grounding as the head `body` because the genus tokenizer
(`construction_grammar.extract_definition`, the working-sentence `re.findall`)
dropped underscores and then split the spaced phrase on `of` (a differentia
marker). But a WordNet lemma is ONE lexical unit — and the acquired-construction
tokenizer ALREADY kept `_`. So the comprehension was present; the genus path was
the inconsistent/duplicated one. Fix: the reader keeps the WordNet lemma's
underscore form, and the genus tokenizer keeps `_` inside a token
(`[A-Za-z0-9'_-]+`). Underscores only ever appear in lexicalised compounds, so
this is a consistency alignment, not a prose-parsing change. `river` / `ocean`
(via `body_of_water`) now ground.

**Remaining campaign body:** the `if/then` principles still need general
(non-math) statement constructions (`comprehend_theorem` residuals on them), and
then the campaign runs over the 146. The bedrock + the descent + multi-word
lexical units are now proven.

## The campaign — RAN over all 146 (2026-06-19)

`scripts/encyclopedic_grounding_campaign.py` (a world-adapter driver — it
sequences the agent's faculties, decides nothing). For each of the 146
unregistered legacy prose-rule seeds it reads the prose (1163 rules), extracts
content words, and grounds each distinct word once (global dedup) through BOTH
dictionaries into ONE shared graph.

**Result: 4685 / 7780 distinct words grounded (60%) across 146 encyclopedias in
250s** (per-seed median 70%, min 48% `pom_mind_body`, max 83% `nutrition`).
Output: `var/encyclopedic_campaign_report.json` (per-seed coverage + frontier) +
`var/encyclopedic_grounded_graph.json` (the grounded graph — the now-reachable
encyclopedic vocabulary).

**Two dictionaries.** WordNet hypernym ladder first (`ChainReader`, ~1ms); when
WordNet has no noun chain, the on-disk Wikipedia lead (`wiki_local`, ~25-240ms):
e.g. `enzyme` → "a biological macromolecule" → `protein` → `macromolecule` →
`molecule` → … → `entity`. WordNet alone grounded ~54%; the Wikipedia fallback
lifted it to 60%.

**The slowness bug (creator's catch: "we have wikipedia on disk").** The reader's
Wikipedia fallback (`web_world.wikipedia_*`) tried the on-disk dump first but then
fell through to the NETWORK on a local miss — a nonsense/absent title cost
~1-20s of HTTP retries (the whole stall). Fix: `web_world.set_local_only(True)`
(default off — live callers unaffected) makes the on-disk 20231101.en dump
AUTHORITATIVE: a local miss is a definitive miss, no network. Groundable words
are ~1ms (WordNet) / ~25-240ms (local wiki); the campaign went from >1h-stall to
4min.

**Adjective bridge wired (coverage 60% → 66%).** The frontier was ~22%
adjectives; `_adjective_bridge_noun` now takes an adjective with no noun ladder
to its nominalization NOUN (attribute it's a value of, then a derivationally-
related noun) and `hypernym_chain` starts its pointer-walk there:
`accurate`→`accuracy`→`quality`→`attribute`→…→`entity`. Re-run:
**5101/7780 (66%)**, per-seed median 77%. Frontier down to 2679.

**Lemmatisation + verb/adverb bridges (coverage 66% → 72%).** `_bridge_to_noun`
now unifies four WordNet-named hops so a non-noun still climbs to a noun ladder:
morphy lemmatises an inflected noun (`enzymes`→`enzyme`); an adjective →
nominalisation noun; an adverb → pertainym adjective → noun (`accurately`→
`accurate`→`accuracy`); a verb (or its morphy lemma `accepts`→`accept`) →
derivationally-related noun (`observe`→`detection`, `achieve`→`achievement`).
Re-run: **5601/7780 (72%)**, per-seed median **84%** (min 69%, max 95%), frontier
2179.

**The agent's morpheme decomposition wired in (coverage 72% → 83%).** The earlier
compound split was a Python regex (orthographic cue only). Now each token is also
decomposed by the agent's OWN shape-based faculty
(`domains/morpheme_decomposition`): it recognises known morphemes in the SHAPE,
the reading chosen by its compression selector (graph-resident Argmin), so an
UN-marked compound (`actionspace`→action·space, `hashmap`→hash·map) grounds as its
parts; a form it has read as a unit (`filesystem`, `understand`) stays whole. The
orthographic cue (`addEdge`→add·edge) stays as the high-confidence signal.
Re-run: **5591/6731 (83%)**, per-seed median **91%** (min 82%, max 100%), frontier
1140 — the decomposition both grounds compound parts AND removes junk compounds
from the denominator (7780→6731 distinct tokens). The decision is the agent's, not
a regex.

**Adjective bridge extended (83% → 85%).** Frontier adjectives WordNet couldn't
bridge directly now ground: a PERTAINYM noun (`administrative`→`administration`),
an adjective→derivational-VERB→noun (`adaptive`→`adapt`→`adaptation`), and
MORPHOLOGICAL de-suffixing to a held noun (`additional`→`addition`,
`adversarial`→`adversary` — not even a WordNet adjective). Each suffix transform
is accepted only when the stem is a real noun, so it never misfires; a whole class
grounds (`national`/`structural`/`financial`/`creative`/`musical`). Re-run:
**5693/6731 (85%)**, per-seed median **92%**, frontier 1038.

**Frontier reduction — "it isn't irreducible, try harder" (85% → 87%).** Four
reducible classes found + closed: (1) FUNCTION WORDS (`again`/`always`/`already`)
out of the denominator (expanded stoplist); (2) `-ly` ADVERBS via morphology
(`adversarially`→`adversarial`→`adversary`) when WordNet has no adverb synset;
(3) DISAMBIGUATION pages — high-precision read of the first sense's abbreviation
EXPANSION (`admin`→`administration`), not an arbitrary sense; (4) THE BIG ONE — a
HYBRID reader (`wordnet_genus.HybridChainReader`): the word's sense-consistent
chain PLUS lazy WordNet for the SUB-GENERA a Wikipedia lead names, so a
WordNet-miss word grounds through its wiki lead AND that lead's genus chains to
bedrock instead of dead-ending (`anycast`→"… methodology"→entity;
`admin`→`administration`→entity). Re-run: **5824/6694 (87%)**, per-seed median
**94%** (min 86%, max 100%), frontier 870.

**The agent reads its prose for EPONYMS + ACRONYMS (the named residual).** Two
more "read the prose" faculties, same world-adapter shape as
forward_segmentation / morpheme_decomposition (the prose statistic parameterises;
read_and_ground grounds):
- `domains/eponym_grounding` — a technical eponym ('Ackermann function',
  "Anfinsen's dogma") is a name in no dictionary; its SHAPE in the prose (a
  Capitalized name modifying a technical concept) says it denotes the PERSON it is
  named after, so it grounds AS a person (-> entity). 13 detected
  (ackermann/anfinsen/kalman/nyquist/…), filtered to non-dictionary proper names.
- `domains/acronym_context` — a technical acronym is expanded BY CONTEXT: read
  Wikipedia's disambiguation senses, pick the one whose words overlap the
  acronym's PROSE context ('AAC' in audio prose -> 'Advanced Audio Coding' ->
  'coding'), ground via the head noun. HIGH-PRECISION (min context-overlap +
  groundable head): a wrong-domain sense is REFUSED, not grounded. 8 expanded
  (aac/tcp/mqtt/poodle/asil/…); most technical senses simply aren't in the local
  20231101 dump.
Campaign with both: **5837/6694 (87%)**, frontier 857. The residual is now the
genuinely irreducible tail — acronyms whose domain expansion is in NO accessible
source, plus tokenizer stragglers.

**Frontier (2179 ungrounded) — the honest boundary, now ~89% not-in-WordNet.**
Acronyms (`aac`/`abi`/`aci`), CODE IDENTIFIERS (`addedge`/`addnode`/`actionspec`),
and hyphenated technical compounds (`accept-encoding`/`action-space`/
`acquire-all-or-none`). These are not dictionary words — the residual is a
TOKENISER concern (filtering code/identifiers out of prose, or splitting
compounds), not a dictionary gap. The lowest seeds are the abstract domains
(`pom_mind_body` 69%, `quantum_mechanics` 75%) — dense technical jargon.

**Still open (the reasoning layer):** this campaign grounds the VOCABULARY (the
concepts the prose mentions → reachable built_from graph). The rules' LOGICAL
form (head/body + if/then as implications) still needs general statement
constructions — `comprehend_theorem` only parses the math register. Grounding the
vocabulary is the prerequisite; grounding the implications is the next phase.

## Scope + status (a dedicated effort, like the Γ_meta core)

- **Prereq:** verify/migrate the reading faculty onto the seed-booted
  WorldAdapter. `read_and_ground` takes `(substrate, concept, conversation)` and
  is substrate-based, but NO migrated test exercises it — its status on the
  seed-booted agent (construction grammar seed present? the `conversation`/reader
  channel? `grounded_representation.ground_concept` as a Rust-substrate mutation?)
  is unverified. First slice: boot the agent + read+ground ONE encyclopedic
  seed's prose, end to end, with a migrated twin.
- **Then:** run the campaign over the 146 (the agent reading its own
  encyclopedia), per-seed, banking grounded seeds; register them; the reasoning
  layer comes alive.
- This is multi-session (146 encyclopedias × read+ground+verify), the natural
  successor to the CuriousAgent burn — the agent now reads to GROUND, not just to
  load. It also feeds the [[self-subsetting]] goal: grounded encyclopedic
  knowledge is reachable graph data, so a domain-subset agent's closure is exact.
