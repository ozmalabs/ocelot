# Voice-Expansion Curriculum (self-run, donkey=0)

A curriculum the Jabberwock runs ENTIRELY ITSELF (the existing standing study
loop) to expand its **voice** — `domains/language_production.LanguageProduction`,
the reverse-comprehension generator that speaks its recount/analysis prose. The
voice's limits, measured during the recount work, are all data-driven and
therefore curriculum-expandable without an LLM.

## The voice limits this curriculum targets (measured, not assumed)

1. **Morphology is regular-only.** English production inflects with a plain
   `+ed`/`+d` rule (`recount_faculty._past_surface`) and a tiny irregular list;
   English is NOT in `morphology_reference._DEFAULT_INGEST` (`{es, ja}`), so the
   voice says "goed"/"childs" shapes rather than "went"/"children". Grounding
   real inflected surfaces (`morphology_reference.ingest_inflection`, so the
   production self-monitor round-trips them) fixes this.
2. **Vocabulary is only what is grounded.** The voice can only say a concept
   whose `LexEntry{concept,surface}` is grounded (via the teacher /
   `make_stub_teacher(extra_lexicon)` / a read). Its default lexicon is tiny.
3. **Grammar/constructions are only what the comprehension stack grounded.** The
   voice reverses the grounded `Grammar`/`Production` set; reading varied
   sentences grounds more constructions for it to reverse.
4. (Structural, NOT curriculum — code fixes: one lexical item per role; the
   proper-noun capitaliser works per whitespace-word not hyphen-sub-word. Named
   here so the curriculum does not pretend to fix them.)

## Downloaded reference material (`data/voice_curriculum/`)

- `unimorph_eng.tsv` — UniMorph English, 652,477 rows `lemma <TAB> form <TAB>
  features` (e.g. `go went V;PST`, `child children N;PL`). The morphology table.
- `freq_10k.txt` — the 9,884 most-frequent English words, frequency-ordered.
  The vocabulary PRIORITY (ground the common words first).
- `example_sentences.txt` — 20,000 Tatoeba English sentences. Varied real
  constructions to read + ground.
- WordNet (already available via `dictionary_lexicon.warm_wordnet`) supplies POS
  + senses for the vocabulary module — no download needed.

## The three modules (each a set of `StudyLesson`s over a dataset chunk)

### Module M — Morphology
Ground inflected surfaces from `unimorph_eng.tsv` via `ingest_inflection`, in
FREQUENCY ORDER (join UniMorph lemmas against `freq_10k.txt`; ground the top-N
lemmas' PST / PST-PTCP / PRS-PTCP / N;PL / comparative-superlative forms first).
Growth measure: the voice emits "went"/"brought"/"sang"/"children"/"better" with
the production self-monitor `accepted=True` (was UNACCEPTED / regularised).

### Module V — Vocabulary
Ground `LexEntry{concept,surface,pos}` for the top-frequency content words
(nouns/verbs/adjectives from `freq_10k.txt`, POS + citation via WordNet), through
the `extra_lexicon` / stub-teacher path the voice already grounds from. Growth
measure: count of distinct `LexEntry` the voice holds rises from its tiny default
into the thousands; a produce goal naming a newly-grounded word is `accepted`.

### Module C — Constructions
The agent READS `example_sentences.txt` in chunks through the SAME
`read_and_comprehend` / `LanguageWorld` path that already grounds grammar, so the
comprehension stack grounds more `Production`/`Grammar` the voice can reverse.
Growth measure: distinct grounded `Production`/`Grammar` count rises; a produce
goal exercising a newly-grounded construction is `accepted`.

## Self-run mechanism (the agent runs it, not a human)

- `curriculum_study.install_curriculum("Voice Expansion", lessons, source=...)`
  mints one `Curriculum` + one `StudyLesson{status:'queued', text_path, kind}`
  per dataset chunk (`kind in {morphology, vocabulary, construction}`).
- `curriculum_study.study_tick` is the standing loop. TODAY it hard-dispatches to
  `code_curriculum.learn_from_lesson` (code shapes). The build adds a
  **voice-lesson processor** `learn_voice_from_lesson(agent, text, kind)` and
  routes each lesson to it by the lesson's `kind` (a graph attr the pick reads,
  NOT a Python content sniff): morphology→`ingest_inflection` over the chunk,
  vocabulary→ground `LexEntry` for the chunk's words (WordNet POS), construction→
  `read_and_comprehend` the chunk. All grounding is the agent's own
  mechanical world-adapter path; the lesson SEQUENCE + reopen-on-growth
  lifecycle are the existing seed rules (`study_lesson_*`), unchanged.
- The daemon `--study-every` cadence advances one lesson per tick, autonomously.
  Reopen: as the voice grows (a `voice_codebook_epoch` bumped on new
  LexEntry/inflection/Production — the write-codebook-epoch analogue), a lesson
  blocked on a missing prerequisite re-arms via the existing
  `study_lesson_reopen_on_growth` law, applied to the voice epoch.

## Verification (the build must show, donkey=0)
1. BEFORE: enumerate the voice's grounded LexEntry / inflection / Production
   counts and 3 concrete failures ("goed", a word it cannot say, a construction).
2. Run the study loop autonomously for the queued lessons (no human input, no
   per-lesson hand call — `study_tick` in a loop / the daemon cadence).
3. AFTER: the counts rose materially; the 3 failures now succeed
   (`produce` self-monitor `accepted=True`); a full recount of a real article
   shows richer surface (correct irregular past, a previously-ungroundable word).
4. donkey=0 throughout; the lesson SEQUENCING + growth decisions are seed rules
   (ablation: removing the reopen rule stops re-arming), not Python.
