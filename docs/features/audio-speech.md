# Audio / speech

The single largest research thread by document count outside vision: a
~60-iteration "autopoietic loop" (`docs/research/agent_loop/`) plus roughly
150 supporting documents (`docs/research/audio_speech/`) building speech
perception and language acquisition from scratch — no pretrained speech,
language, or vision model in the decision path ("donkey=0"; pretrained
tools, where used at all, appear only as removable bootstrap scaffolds or
eval-only scorers).

## The two claims

1. **A capability claim.** The agent learns grounded word meaning from real
   children's programming, and learns speech structure from real audio,
   from scratch, faster than realtime, on a consumer CPU — without the
   pretrained encoders or GPU training a comparable recognizer would use.
   This is a research prototype at small scale (a handful of grounded
   words); the claim is about the method and cost profile, not about
   matching a deployed recognizer's raw accuracy.
2. **A developmental claim.** The *way* it gets there tracks the canonical
   stages of child language acquisition, in the canonical order, hitting
   the canonical problems and solving them the canonical way — without that
   order being imposed in advance. Stages traversed: production before
   perception (perceive by inverting your own babble — motor theory);
   perceptual narrowing to the ambient sound distribution before word
   recognition (Werker/Kuhl); the meaning problem (isolated sound-form
   recognition is a dead end; a deliberate literature check caught and
   corrected a wrong turn here); word learning under referential ambiguity
   — the "gavagai" problem (cross-situational statistics + joint
   attention); meaning reshaping perception (referential meaning preserves
   acoustically-weak contrasts pure sound-learning would discard);
   communication as a two-mind problem (model the listener, repair
   misunderstanding); grounding in real multimodal footage (bind word to
   object at ostensive moments, using the agent's own earned vision, not a
   pretrained vision net); and the repetition law (vocabulary grows through
   depth of genuine repetition, the mechanistic reason toddler media is so
   repetitive — rediscovered independently, not imported from the
   literature).

## The self-directed research loop

The bulk of `docs/research/agent_loop/` (54 numbered iteration documents,
`agent_loop_iteration2.md` through the high-40s, plus the `jabberwock_*`
design-consideration documents) is not a curated summary — it is the
literal working log of the agent's own synthesize → pick → build → measure
loop, applied to its cross-speaker recognition wall. Representative
frontier, late in the arc: iteration 48 found that a single per-node
reliability weight is too coarse (a node can be confidently wrong on one
specific contrast, e.g. b/d, while averaging well, diluting that contrast's
signal); iteration 49's fix gives each (cue × order) node its *own*
admissibility sub-graph — a per-(word, contrast) reliability, so a node can
abstain on exactly the contrasts it isn't good at rather than dragging down
every prediction with its average. The recognizer's combine step is
literally `score(w) = Π gated_i(w)` — a graph `Times` over per-node `Plus`
blends toward a flat prior, all as Term-tree evaluation, not Python
arithmetic.

Recurring cross-cutting techniques across the loop, if you're scanning for a
specific lever: LOSO (leave-one-speaker-out) as the standing cross-speaker
metric; DTW-based recognition as the single biggest cross-speaker jump
found; order-N (the same dynamic-quantization mechanism as vision) applied
to formant trajectories, frequency, and interpolation; and
analysis-by-synthesis (propose, render via a forward model, compare) as the
recurring architecture, mirroring vision's Omniglot result that generation
and reading are one model.

## Native migration

The hearing pipeline's cognition — fusion decisions, back-off logic, the
whole recognition path — has been migrated off Python into native Rust
Term-trees. The `native_*.md` documents (`native_backoff.md`,
`native_collapse_core.md`, `native_cutover.md`, `native_fusion.md`,
`native_migration_design.md`) are filed under
`docs/research/engine_substrate/` rather than here, alongside the rest of
the Python→Rust migration story (`docs/features/engine-substrate.md`) —
even though two of them (`native_fusion.md`, `native_migration_design.md`)
are specifically about the hearing pipeline, the migration mechanics they
document are the same cross-cutting pattern as every other native-Term
cutover in the tree, so they're grouped with their migration siblings
rather than split off by subject domain.

## Where the code lives

- Rust: `runners/dsl/src/audio_primitives.rs`, `cochlear_nucleus.rs`,
  `auditory_cortex.rs`, plus the `substrate_rs.speech`/`.audio` Python
  binding modules.
- Seeds: `seeds/speech.json` (per `CLAUDE.md`'s seed-dependency list —
  depends on `audio` + `core`).
- World adapters: `domains/self_directed_speech_world.py` and the speech/
  audio-facing `domains/*` files.
- Gates: the speech- and audio-tagged `tests/test_*_migrated.py` files.

## For the full history

Read the numbered `docs/research/agent_loop/agent_loop_iteration*.md`
series in order for the live research process, or
`docs/research/audio_speech/speech_development_note.md` for the
synthesized progress note this section draws from. The full corpus
(LOSO experiment logs, stage-by-stage curriculum documents, the Whisper/
Parakeet teardown-as-data studies, the cipher-recovery credibility ladder
that shares this arc's structure-recovery machinery) is indexed at
`docs/research/audio_speech/INDEX.md`.
