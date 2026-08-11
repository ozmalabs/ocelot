# RAVANA convergence audit — independent arrival, or an earlier fork in the same design space?

**Status: investigation complete, docs-only, no code changed.** Read-only pass
over a fresh clone of `codeberg.org/oxiverse/ravana` (HEAD
`4153b02b9b2584dddd16854b09abc912a568915c`, 2026-08-08) plus this repo's own
current mechanisms and ten files fetched from the creator's private
`ozmalabs/internal` prehistory repository.

## 0. One-paragraph honest answer

**No evidence of direct connection was found, and the creator's own account
makes a lineage search moot on top of that: there is no committed "semiotic
graphs + Model" draft to have been drawn on — the idea never left ideation and
was never checked into any repo.** What the source-level read establishes
instead is a structural claim, not a lineage claim: RAVANA occupies a design
point the creator's own thinking evidently passed through and discarded — a
typed concept graph paired with a kept neural component — while OCELOT is the
graph-only branch of that same fork (CLAUDE.md: *"the agent is graph, running
in Rust"*, zero neural decision-making anywhere in the loop). Reading RAVANA's
actual source (not its README) narrows that gap further than the README's own
framing suggests: RAVANA's neural decoder, precisely characterized in §2.5
and §3.4 below, does no reasoning — every decision (what to say, whether to
abstain, what to explore, when to sleep) is made by hand-written Python
*before* the decoder is ever called. What is genuinely different is not
"graph vs. no graph" — it is *what decides inside the graph's Python host*:
RAVANA's decisions are imperative conditionals over dozens of hardcoded
scalar constants (thresholds, EMA rates, additive weights); OCELOT's
decisions are a generative Rust rule-fixpoint over graph-resident data. Both
projects independently name the same problems (typed concept graph, gap
detection, fail-closed abstention, curiosity, consolidation) — this is a real
architectural convergence, corroborated at the level the creator's own
`ecosystem_convergence_2026.md` methodology treats as evidence: independent
arrival at overlapping structure from separate directions — but on the actual
decision-making mechanism the two projects remain far apart, in exactly the
direction CLAUDE.md's own standing culture would predict.

## 1. Method

1. Cloned RAVANA (`git clone --depth 200`), read source directly — not the
   README's gloss — in `ravana_ml/` (ConceptGraph, free energy, curiosity),
   `ravana/` (chat engine, chain walker, monitor/abstention, web learning),
   and `ravana-v2/` (the GRACE governor and its 20 "phase" modules).
2. Verified every architectural claim empirically where possible (e.g.
   whether the Governor pipeline is actually wired into the live chat
   engine, rather than trusting the README's description of it).
3. Searched RAVANA's full commit history, README, docs, and source tree for
   any mention of the creator, "ozma," "ocelot," "jabberwock," "graphic
   equalisation," or "admissibility grammar."
4. Fetched and grep-triaged the ten internal-repo prehistory files named in
   the brief, searching for the same convergence vocabulary and for any
   direct reference to RAVANA/oxiverse/Codeberg/the RAVANA author's name.
5. Re-read this repo's *own current* gap-detection, sd-loop, and
   admissibility-grammar mechanisms (not CLAUDE.md's prose about them, which
   this project's own standing culture treats as potentially stale — see
   CLAUDE.md's "optional-dep note" retraction) to ground every comparison
   claim in file:line.

## 2. RAVANA's actual architecture, read from source

### 2.1 What RAVANA is, structurally

590 of ~595 tracked source files are `.py`; the remaining files are docs,
JSON, and one `.tex` paper draft — no Rust, C, or other systems language
appears anywhere in the tree. This confirms the README's "no LLM, no
pretrained chat model, CPU-native" framing holds at the file-composition
level: RAVANA is a from-scratch numpy/scipy Python cognitive architecture,
not a wrapper over a frontier model.

Repository metadata (Codeberg API, `repos/oxiverse/ravana`): created
2026-05-24, 1 star, 0 forks, 863 total commits as of the 2026-08-11 snapshot
used for this audit — an actively developed but very young (~11-week-old),
essentially single-author project (see §5).

### 2.2 ConceptGraph — an unconstrained typed graph, not an admissibility grammar

`ravana_ml/src/ravana_ml/graph.py` (4,268 lines). `ConceptNode`
(`graph.py:43-148`) carries a 64-D `vector`, a `core_vector` identity anchor,
activation/salience/confidence/`contradiction_count` scalars, and hierarchy
fields (`level`, `parent`, `children`). `ConceptEdge`
(`graph.py:151-200+`) is typed by a `relation_type` string against a fixed
lookup table, `RELATION_DEFAULT_WEIGHTS` (`graph.py:153-166`, 12 entries:
`semantic: 0.5`, `causal: 0.7`, `analogical: 0.7`, `antonym: 0.9`, …) and a
parallel `RELATION_DEFAULT_EDGE_TYPES` table (`graph.py:169-176`).

`ConceptGraph.add_edge` (`graph.py:1498-1582`) is the single write path. It
accepts **any** `relation_type` string; if the string is not in the default
table it silently falls back to `weight=0.5, edge_type="excitatory"`
(`graph.py:1540-1546`). There is no check anywhere in `add_edge` of what
node *types* a given relation may legally connect, no analogue of a
production rule, and no rejection path for an inadmissible edge — the only
guard is a same-node self-loop rejection (`graph.py:1510-1521`) and a
capacity-triggered `_prune_weakest_edges()` once `max_edges` is exceeded
(`graph.py:1578-1580`). This is a **conventional weighted associative graph
with a convenience default-lookup table**, not a Γ-style admissibility
grammar (compare OCELOT's `Production{src, edge_type, tgt, where, weight}` +
`check_edge` gate, `runners/dsl/src/grammar.rs` / `checker.rs`, cited in
CLAUDE.md's "SHAPES, NOT NUMBERS" section) — any edge type between any two
nodes is always constructible; nothing in the substrate itself decides what
may exist.

### 2.3 The "20-phase GRACE governor" — a development-history label, not a runtime pipeline, and a PID-style scalar regulator underneath

The README's headline claim — *"orchestrates cognition with a 20-phase GRACE
governor (phases A–P)"* — does not describe how the live chat engine runs.
`ravana-v2/src/ravana_grace/core/__init__.py:8-73` labels each import with a
`# Phase X` comment (Phase A: Governor/Resolution/Identity/State; Phase B:
Adaptation; … Phase P: dialogue system) — this is a **chronological
development-order label** for 20-odd Python classes added incrementally
(directly the same genre of label as this repo's own dated CLAUDE.md rungs),
not a dispatch sequence any code executes per turn.

RAVANA's own `docs/ARCHITECTURE.md` states this explicitly: *"The GRACE
governor (`Governor` in `ravana_grace.core.governor`) is NOT used by the chat
engine — instead, the chat engine uses individual GRACE modules
independently. The full Governor pipeline (20 phases, A–P) is designed for
standalone research use."* This is verified empirically: `scripts/
ravana_chat.py:50-56` imports `VADEmotionEngine`, `IdentityEngine`,
`MeaningEngine`, `DualProcessController`, `GlobalWorkspace`, `MetaCognition`,
`SleepConsolidation` individually — `Governor` never appears in the live
entrypoint's import list.

The `Governor` class itself (`ravana-v2/src/ravana_grace/core/governor.py`,
743 lines), where it *is* used (the standalone research harness), is a
PID/clamp-style regulator over two scalars — `dissonance` (D) and `identity`
(I) — dispatching one of five `RegulationMode` enum values via an if/elif
threshold ladder (`_detect_mode`, `governor.py:346-371`: `crisis_threshold=
0.90`, `resolution_threshold=0.60`, `exploration_threshold=0.25`, …), then
applying hard clamps (`max_dissonance=0.95`, `min_dissonance=0.15`,
`governor.py:28-29`), a hand-set asymmetric "center-seeking force"
(`k=0.06` pulling down / `k=0.15` pushing up, `governor.py:704-706`), and a
quadratic "boundary pressure" falloff between hardcoded `soft=0.75` /
`hard=0.95` limits (`governor.py:532-538`). `GovernorConfig`
(`governor.py:24-57`) declares roughly twenty independent hand-tuned scalar
constants. This is imperative threshold-and-clamp control, not a generative
rule/grammar system — every one of these numbers is a fixed knob a human
set, not a value decoded against a codebook or generated from a production.

### 2.4 Gap detection / curiosity — five named signals, but the "learning progress" signal is not two-timescale

`ravana/src/ravana/learn/curiosity.py`'s `CuriosityEngine` (202 lines)
names five signals in its docstring (`curiosity.py:13-18`): prediction error
(Friston), information gap (Loewenstein), cognitive dissonance/contradiction,
novelty, and learning progress (Oudeyer). In the actual implementation:

- **Prediction error** and **learning progress** are the *same* single
  exponential moving average: `update_prediction_error`
  (`curiosity.py:41-47`) computes `smoothed = (1-alpha)*old_pe + alpha*error`
  with a hardcoded `alpha=0.3`, and `pe_deltas[concept] = old_pe - smoothed`
  is directly assigned as `learning_progress[concept]`
  (`curiosity.py:46-47`). This is a **single-timescale** EMA delta, not a
  two-timescale fast/slow differential.
- Candidate topic weights in `select_topics` (`curiosity.py:80-139`) are
  hand-set: impossible queries get a flat weight `5.0`
  (`curiosity.py:91`), high-PE concepts get `3.0 * min(1.0, pe)`
  (`curiosity.py:98`), contradiction pairs get `3.0`/`2.5`
  (`curiosity.py:103,107`), dormant/unvisited concepts get
  `0.5 + dormant_ratio*0.5` (`curiosity.py:116-117`), and an
  `epsilon=0.35` (`curiosity.py:120`) gates flat random exploration. A
  diversity penalty decays prior selections by `0.2 ** recency`
  (`curiosity.py:164`) with a `selection_cooldown=10`
  (`curiosity.py:33`).

`ravana_ml/src/ravana_ml/free_energy.py`'s `FreeEnergyAccumulator` (90
lines) sums five channels (`semantic`, `linguistic`, `episodic`,
`contradiction`, `abstraction`) into one scalar `free_energy` property
(`free_energy.py:17-23`), each channel updated by a hand-set multiplicative
constant (`error * salience` with `salience=0.3` default,
`free_energy.py:35-36`; `error * 0.1` for linguistic,
`free_energy.py:39-40`; `count * 0.5` for contradiction,
`free_energy.py:47-48`), decayed at a flat `rate=0.1`
(`free_energy.py:59-64`), and gated by a hardcoded
`needs_sleep(threshold=10.0)` (`free_energy.py:73-74`).

### 2.5 The neural decoder's actual boundary — pure surface realization, downstream of every decision

This is the crux the coordinating session asked to be pinned down precisely,
because it bears directly on whether RAVANA genuinely parallels or diverges
from OCELOT's "the agent is graph; neural/Python is only translation"
commitment.

`ravana_ml/src/ravana_ml/nn/neural_decoder.py`'s `NeuralDecoder`
(`neural_decoder.py:1-90` docstring) is a GRU + `ConceptAttentionHead` +
linear projection to vocabulary logits, gated at generation time by a
`BasalGangliaGate` for Go/NoGo word selection, trained via **local
predictive-coding/Hebbian updates — explicitly no backprop**
(`neural_decoder.py:21-24`). Its input is a conditioning context of
graph-walk concept embeddings; its output is one word at a time.

RAVANA's own `docs/ARCHITECTURE.md` turn-level flow (lines ~140-175 of that
file) states the order precisely, and it is confirmed by the code:

```
[1] brain-repair prepasses
[2] intent/coherence/gate/monitor  ── abstention / free-energy check ──
    ├─ if unknown / low-confidence ─► honest abstention, HERE, BEFORE generation
[3] graph walk (chain_walker.py) over the typed ConceptGraph  ── DECIDES what to say
[4] neural decoder                                            ── RENDERS words
[5] surface_realizer + syntactic assembly                      ── final NL text
[6] web_learning (background)                                  ── if a gap was detected
```

Two facts pin this down precisely:

- **Abstention is decided before the decoder is ever called**, from
  graph/heuristic signals, never from decoder confidence or logits. The
  `ood_abstain` gate consulted at `ravana/src/ravana/chat/engine_graph.py:
  983-1008` and `response_gen.py:1018-1019` compares an *attribute
  encoder* probe vector against the *graph* vector (`ood_abstain(attr_enc,
  gvec)`), not anything the decoder produces. `chat/monitor_gate.py`
  (112 lines) is a separate, purely lexical post-hoc detector for
  "fluent-tautological" text (word-list membership in `_METAWORDS` /
  `_GLUE` / `_CONTENT_VERBS`, `monitor_gate.py:24-56`) — a regression gate
  over generated *text*, still not a decoder-confidence signal.
- **What to say is decided by `chain_walker.py`**, which imports and applies
  a chain of Python heuristic gating functions over graph edges —
  `relevance_suppression_dual`, `degree_suppression`, `recency_modulation`,
  `task_relevance_gate`, `post_hoc_relevance_filter`,
  `rlm_confidence_modulation`, `valence_modulation`, `dominance_modulation`,
  `edge_strength_suppression`, `repetition_penalty`,
  `dormant_edge_modulation`, `self_penalty_gate`, `sigmoid_gate`
  (`chain_walker.py:24-32`) — before the decoder ever runs. These are
  imperative Python functions with their own hand-tuned scalar parameters
  (same genre as §2.3-2.4's constants), not graph-grammar productions and
  not neural weights.

**Conclusion on the boundary:** the decoder does no reasoning anywhere in
this pipeline. It is a strict downstream surface realizer, exactly as
OCELOT's own architecture rule would require of any neural component it
kept. The place RAVANA diverges from OCELOT is not "neural vs. no neural in
the loop" — it is that RAVANA's *decision* layer (the thing upstream of the
decoder) is imperative Python over hardcoded scalars, not a graph-resident
generative rule/grammar system. See §6.3 for what this means for the
"kept the Model" framing.

### 2.6 Sleep consolidation — a genuinely rich, staged mechanism

`ravana-v2/src/ravana_grace/core/sleep.py` (1,848 lines) implements a
7-stage `SleepStage` enum (`AWAKE → TOPOLOGY_ANALYSIS → PATTERN_COMPRESSION
→ ABSTRACTION_COMPRESSION → CONTRADICTION_RESOLUTION → MODEL_UPDATE →
INTEGRATION`, `sleep.py:19-26`), four `DreamPerturbationType`s
(counterfactual reversal, emotional flip, failure oversampling, symbolic
recombination, `sleep.py:29-33`), a protected `tier_0_identifiers` list
(`sleep.py:60-65`) exempt from perturbation, and rollback protection keyed
on a `coherence_drop_threshold` (`sleep.py:58-59`). Roughly fifteen
hand-tuned scalar parameters govern it (`pressure_threshold=0.2`,
`counterfactual_rate=0.20`, `failure_oversample_factor=1.5`, …,
`SleepConfig`, `sleep.py:38-65`). This module is genuinely well-designed and
does not exist in OCELOT in this form — see §6.1.

## 3. Comparison against OCELOT's actual current mechanisms

### 3.1 Graph substrate: unconstrained associative graph vs. admissibility grammar

RAVANA's `ConceptGraph.add_edge` (§2.2) admits any `(source, target,
relation_type)` triple unconditionally, defaulting unknown relation types to
`weight=0.5`. OCELOT's Rust substrate gates every edge write through a
`Production{src-pattern, edge_type, tgt-pattern, where-clause, weight}`
grammar (`runners/dsl/src/grammar.rs`, `checker.rs`, `check_edge` —
referenced in CLAUDE.md's "SHAPES, NOT NUMBERS" section, itself citing the
humanoid arc's finding that bypassing `check_edge` via direct
`graph.insert_edge` writes is a *named defect*, not a design choice). The
two systems solve the same problem — "what may this typed graph contain" —
with opposite answers: RAVANA's answer is "anything, with a convenience
default"; OCELOT's answer is "only what a production generates."

### 3.2 Gap detection: RAVANA's five signals vs. OCELOT's gap-kind rules — and a place OCELOT is ahead

OCELOT's `seeds/gap_awareness.json` (v1.6.0, 1,411 lines) distinguishes gap
**kinds** entirely as graph rules: `knowledge` (an `answer_topic` Goal whose
`outcome` attr is `unresolved`, rule `note_unresolved_topic_gap`,
`gap_awareness.json:134-265`), `reported` (an interlocutor Mention resolving
to both a deficiency Concept — `cannot`/`fail`/`gap`/… — and a self-word
Concept, rule `note_reported_gap`, `gap_awareness.json:267-548`),
`instruction` (an unhandled instruction Message, rule
`note_unhandled_instruction_gap`, `gap_awareness.json:550-837`),
`self_account` (a reflexive self-question with no held account, rule
`note_self_account_gap`, `gap_awareness.json:839-955`), and `reply_fix`
(upload/attachment handling gaps, `gap_awareness.json:956-1258`). Every gate
condition (dedup, mint-once) is a graph `Not(Exists(...))` predicate — zero
Python `if`/`else` decides *whether* a gap is a gap; the Python adapter only
records facts (`outcome='resolved'|'unresolved'` — a datum) that rules read.
Deduplication is itself a rule: `retire_duplicate_gap`
(`gap_awareness.json:1259-1410`) uses `Argmin` over same-content
`SelfConcern` nodes to keep exactly one survivor per content, batch-safe,
with no node-id special-casing — contrast RAVANA's `_apply_diversity_penalty`
(`curiosity.py:157-166`), an imperative Python loop applying an exponential
recency penalty.

This is a genuine difference in *kind*, not just wiring: RAVANA's five
signals select **what to go explore next** (a curiosity/topic-selection
problem, feeding an autonomous background web-learning loop,
`scripts/ravana_learn.py`); OCELOT's five kinds classify **what already
failed during a turn** (a self-repair/gap-filing problem, feeding the
human-gated `promote_self_concern` spine, `scripts/jabberwock_daemon.py:
2150`). Neither subsumes the other outright — see §6.2 for the asymmetry
this implies is worth closing.

**Where OCELOT is measurably ahead on the shared piece (learning progress):**
`seeds/learning_progress_curiosity.json` (v1.0.0, 403 lines, integer-only,
`self_load_only` opt-in) implements the Oudeyer/Schmidhuber-canonical
**two-timescale** learning-progress differential — `fast_res` (`fast_div=3`)
and `slow_res` (`slow_div=20`) integer EMAs of the same residual, with
`learning_progress = slow_res − fast_res`
(`learning_progress_curiosity.json:127-160`, rules `lp_fast`/`lp_slow`/
`lp_progress`) — specifically because a single-EMA prediction-error signal
(exactly RAVANA's `update_prediction_error`, §2.4) is the textbook "noisy
TV" trap (Pathak ICM 2017 / Burda RND 2018): it cannot distinguish
structured-but-unresolved surprise from irreducible stochastic noise. This
is not asserted but **measured and gated**
(`docs/research/vision/VISION_LEARNING_PROGRESS_RESULTS.md`, §G1): on a
16-draw ensemble with one learnable and one noisy stimulus, the gated
two-timescale signal leaves the noisy item (interest `480→130`) while
attention concentrates on the learnable one (late share `0.78` vs. `0.22`);
a raw-surprise falsifier run with the *same rules, one knob flipped*
reproduces the trap exactly (`1008→999`, does not decay). RAVANA's
single-EMA `pe_deltas`/`learning_progress` (§2.4) has no analogous fast/slow
split and is, on this evidence, vulnerable to the same trap its own
docstring cites Oudeyer to justify avoiding.

### 3.3 Residual/novelty detection: RAVANA's ad hoc mint vs. OCELOT's sd-loop growth ladder

RAVANA has no unified residual-handling mechanism — novelty is one of five
flat-weighted curiosity signals (§2.4); there is no growth ladder that tries
cheaper explanations (recognize, then transform, then infer a new dimension)
before minting something new. OCELOT's sd loop
(`runners/dsl/src/shape_decode.rs`, `seeds/shape_decode_loop.json`,
`docs/features/dynamic-quantization.md`) is Occam-ordered: exact recognize →
transform in the existing basis → infer a new dimension → mint novelty, only
after the first three fail (`dynamic-quantization.md:47-63`). This is the
"decode against a codebook" primitive named in CLAUDE.md's "SHAPES, NOT
NUMBERS" section; RAVANA's novelty handling has no equivalent — it is a flat
membership check plus a hardcoded weight (§2.4).

### 3.4 The neural-decision boundary, compared directly

Per §2.5, RAVANA's decoder makes no decisions; every decision upstream of it
is imperative Python over hardcoded scalars. OCELOT has **no neural
component in the decision path at all** — CLAUDE.md's architecture rule
forbids it categorically, and the substrate's decisions are Rust rule
matches over graph data, not Python conditionals. So on the narrow axis of
"does anything statistical decide," RAVANA and OCELOT are aligned (neither
lets a neural net decide); on the axis of "does anything graph-generative
decide, or does hand-written imperative code with hardcoded numbers decide,"
they diverge sharply — RAVANA's decision layer is closer in *kind* to a
conventional rule-based chatbot's heuristics than to either a learned model
or a generative grammar.

## 4. Comparison against the creator's own theoretical prehistory

Per the coordinating session's correction mid-task: **there is no specific
prior document to compare RAVANA against for lineage purposes.** The
creator's own account is that an early "semiotic graphs + Model" direction
was explored in ideation, never checked into any repo, and the notes (if
any were ever written down) are not known to exist. This section therefore
reports what the fetched prehistory documents actually say on their own
terms — as an *independent-convergence* comparison, not a lineage search —
and flags the one place a genuine prior gap-naming was found.

- **`formal_foundations.md`** (fetched from `ozmalabs/internal`,
  `research/docs/formal_foundations.md`) is an early "Ozma" AGI-case
  document, structurally from a stage where the architecture was still an
  LLM-prompted model wrapped in a tool "shim" (`formal_foundations.md:
  290-296`) — materially earlier than OCELOT's current graph-native Rust
  runtime. Its §"Properties Claimed Necessary by AGI Literature" numbers
  five gaps against Ozma's then-current design; gap 3 reads in full:
  *"Intrinsic Motivation / Curiosity — Status: NOT ADDRESSED. The model
  reasons when prompted. It does not spontaneously generate goals or
  explore without input. … Gap: Ozma does not currently have intrinsic
  motivation. The architecture does not preclude it … but it is not
  implemented."* (`formal_foundations.md:300-306`). This is a genuine,
  dated (document captured pre-2026-04-25 per the file's own header
  context) self-identified gap in the creator's own then-current design —
  and it is precisely the gap RAVANA's `CuriosityEngine` fills, in an
  independently-authored codebase, roughly a month later (RAVANA repo
  created 2026-05-24, §2.1). No text in `formal_foundations.md` names
  RAVANA, curiosity-driven concept-graph architectures generally, or any
  external project; this is a match of *problem statement*, not of
  solution or citation.
- **`agti_comparison.md`** (dated 2026-04-23 in its own header, predating
  RAVANA's repo creation by roughly a month) is a systematic architecture
  comparison — ACT-R, Soar, HTM, Sparse Distributed Memory, AIXI, the Hutter
  Prize compression approach, Stanford's Generative Agents, neurosymbolic
  taxonomies, and whole-brain emulation (`agti_comparison.md:16-190`) — of
  exactly the genre this audit is now performing for RAVANA. It does not
  and could not mention RAVANA (predates it); no free-energy/active-inference
  architecture or curiosity-driven-learning system is named as a comparison
  target in it.
- **`paper1-cut.md`** and **`typed_graph_substrate_foundation.md`** contain
  the theory's own formal Friston/free-energy correspondence (Theorem A +
  D, `paper1-cut.md:47-49`) — a derivation showing the paper's typed-graph-
  plus-weighted-productions substrate is a structurally-optimal realization
  of variational free-energy minimization, not an additive scalar
  bookkeeping device. This is a different sense of "free energy" than
  RAVANA's `FreeEnergyAccumulator` (§2.4): the theory treats it as a
  quantity a substrate-with-grammar is proven to minimize under stated
  conditions; RAVANA implements it as five hand-weighted additive channels
  with a hardcoded sleep-trigger threshold. Both cite Friston; the internal
  document's treatment is closer to Friston's own formalism than RAVANA's
  additive-scalar implementation is (see §6.3 for the CLAUDE.md
  "SHAPES, NOT NUMBERS" read on this).
- **`methodology_prior_work.md`** is unrelated in subject (prior art for the
  methodology of naming unnamed assumptions — Kuhn, Bourdieu, Foucault,
  Quine, Dijkstra, …) — checked per the brief, contains no architectural
  comparison content and no mention of RAVANA or any concept-graph/curiosity
  system.
- **`ecosystem_convergence_2026.md`** (9.6KB, snapshot dated 2026-04-25) is
  the creator's own prior methodology for exactly this kind of exercise —
  tracking independent external convergence as corroborating evidence — but
  its survey population is GitHub coordinator-pattern agent frameworks
  (Claude Code, opencode, AutoGPT, LangGraph, …), a different comparison
  set entirely; RAVANA is not mentioned and would not fit its selection
  criterion (>5K GitHub stars; RAVANA has 1).
- `gamma_collapsed_draft.md`, `gamma_as_variable_draft.md`,
  `abstract_s0_gamma_draft.md`, `ozma_paper.md`, `foundation.md`,
  `paper1-cut.md`, and the `graphs_paper_1_core.md` /
  `graphs_paper_2_implications.md` / `graphs_paper_3_trajectory.md` trilogy
  were grep-triaged for "concept graph," "curiosity," "free energy,"
  "abstain," "prediction error," "novelty," and "contradiction." "Concept
  graph" appears twice in `graphs_paper_1_core.md` and once in
  `graphs_paper_2_implications.md`, but in a different, unrelated sense —
  the shared graph a compilation stack's source/IR/assembly/microcode
  levels are all views of (`graphs_paper_1_core.md:624`), not a proper-noun
  architectural component. This is a coincidental vocabulary overlap, not a
  structural match, using this project's own classification convention
  (`THEORY_CONVERGENCE_AUDIT.md`'s COINCIDENTAL/EXCLUDED bucket).

## 5. The direct-connection search

**Both directions checked; nothing found.**

- **RAVANA → creator.** `git log --all --format='%an <%ae>'` over the full
  depth-200 clone returns exactly three identities: `Likhith Sai Seemala
  <likhith@oxiverse.com>`, `Likhithsai2580 <semalalikithsai@gmail.com>`
  (same person, two commit identities), and `Hermes Auditor
  <audit@oxiverse.com>` (an automated docs-audit bot account, per its own
  commit messages). No `CONTRIBUTORS`, `AUTHORS`, `ACKNOWLEDGMENTS`, or
  `CITATION` file exists in the tree. A repo-wide, case-insensitive grep for
  `parslow|ozma|ocelot|jabberwock|graphic equali[sz]ation|admissibility
  grammar|oxiverse` across every `.py`/`.md`/`.txt`/`.toml` file returns
  hits only for `oxiverse` — and every one of those is RAVANA's own
  self-reference (its product name, its license name, its own domain-seeded
  test fixtures for "oxiverse" as a *topic the agent is taught about*, e.g.
  `tests/unit/test_sm_grounding_gate.py:76-79`). None reference this
  project, this repo, or the creator.
- **Creator → RAVANA.** All ten internal-repo files fetched (§4, plus the
  three `graphs_paper_*` trilogy files) were grepped for
  `ravana|oxiverse|codeberg|likhith|seemala|intentforge` — zero hits across
  all of them.
- **The lineage question is moot by the creator's own account, independent
  of this search.** Per the coordinating session's mid-task correction: the
  "semiotic graphs + Model" direction never went past initial ideation, was
  never committed to any repository, and the creator does not know whether
  notes on it exist anywhere. There is nothing for RAVANA to have drawn on
  even if a connection existed — this search's clean result and the
  creator's own account independently point the same way, for different
  reasons.

**Conclusion: independent convergence, not lineage.** Both the empirical
search (clean in both directions) and the creator's own testimony (nothing
committed to find) rule out direct textual influence. What remains is the
structural relationship characterized in §6.3.

## 6. Concrete, scoped inspiration/recommendations

None of the below are built. Each is sized precisely enough that a future
rung could act on it directly, or explicitly declined with a reason.

### 6.1 Sleep-cycle consolidation — genuinely absent in OCELOT, worth a small seed

A repo-wide check (`docs/research/psychology_affect/`'s 27 documents,
CLAUDE.md, `seeds/*.json` filenames) turns up no dedicated
consolidation-during-idle mechanism analogous to RAVANA's `sleep.py`
(§2.6) — the two incidental "sleep" hits in `psychology_affect/` are
unrelated (arousal/Harlow content, not consolidation). OCELOT's closest
relatives are the sd loop's `codebook_epoch` re-arm (growth happens as a
side effect of decode, not on an idle/tick trigger) and
`learning_progress_curiosity.json`'s decay atom (attention-level, not
graph-restructuring).

**Scoped recommendation:** a `seeds/sleep_consolidation.json` triggered by
an idle-tick condition (no inbound Message for N ticks, or an explicit
`consolidate` Reflex) that runs a *bounded* set of existing primitives in
sequence — `codebook_epoch` re-arm, `retire_duplicate_gap`-style dedup
sweep generalized across node types, and a stale-edge prune keyed off the
existing `staleness_decay` atom (`196000`, already used by
`learning_progress_curiosity.json`) — rather than inventing new machinery.
The smallest useful version is "run the sd loop's own re-decode fixpoint
plus a staleness-decay-gated prune, on an idle trigger, as one Reflex" — no
new Rust Term needed on the evidence gathered here.

### 6.2 Wire `learning_progress_curiosity`'s interest signal into gap-awareness's topic selection

Per §3.2, OCELOT's gap-awareness pipeline is reactive (fires on an actual
conversational miss, `note_unresolved_topic_gap`) and its self-heal
(`ground_unknowns`, `substrate/world_adapter.py:4798`) is a per-word
teacher loop triggered by that same in-turn miss — there is no autonomous,
unprompted "go pick something to explore" loop analogous to RAVANA's
`scripts/ravana_learn.py` background mode. OCELOT already has the harder
half of this problem solved and measured (`learning_progress_curiosity.json`
§3.2) — what is missing is the *consumer*: nothing currently reads the
`interest`/`attended` attrs it computes to select an autonomous grounding
target the way RAVANA's `select_topics` does.

**Scoped recommendation:** a graph rule that, when an `AttentionItem` with
`attended=1.0` (already computed by `lp_attend`,
`learning_progress_curiosity.json:246-272`) has no corresponding grounded
Concept, mints a `SelfConcern{kind:'knowledge', source:'implicit'}` — the
exact same node shape `note_unresolved_topic_gap` already mints — feeding
the identical `promote_self_concern` spine. This reuses every existing
primitive; the only new piece is the trigger condition linking
`learning_progress_curiosity`'s (currently vision-only-wired) attention
signal to gap-awareness's (currently conversation-only-wired) topic
minting.

### 6.3 The free-energy-scalar disagreement — characterized, not adopted

RAVANA's `FreeEnergyAccumulator` (§2.4) is architecturally central to it —
it gates `needs_sleep`, feeds `compute_urgency`, and is cited as the
mechanism behind the README's headline claim that "confident-wrong is
treated as high free-energy that would poison the graph." Read from source,
it is five additively-combined channels, each with its own hand-set
multiplicative constant, decayed at a flat rate, compared against a flat
threshold. This is exactly the pattern CLAUDE.md's "SHAPES, NOT NUMBERS"
section names as the recurring, independently-measured failure mode across
the F-16, humanoid, and bigville arcs: *"a new subsystem invents a scalar
knob … instead of decoding against a codebook or generating from a
grammar."* The same pattern recurs in `curiosity.py`'s weights, `sleep.py`'s
`SleepConfig`, and `governor.py`'s `GovernorConfig` (§2.3-2.4, §2.6) — this
is not a one-off in RAVANA, it is the dominant idiom of its decision layer.

This is a genuine, precisely-characterized **disagreement**, not a gap to
close by importing RAVANA's mechanism. The internal repo's own formal
treatment of free energy (`paper1-cut.md:47-49`, §4) is the alternative
CLAUDE.md's culture already commits to: free energy as a *proven* property
of a substrate-with-grammar under stated conditions, not an accumulated
scalar with hand-set weights. RAVANA's own design principle #2 ("No fixed
thresholds where a distribution exists — gates are data-derived,"
README.md) states an intention that its `governor.py`/`free_energy.py`
implementation does not, on this reading, consistently satisfy — most of
its "data-derived" gates are in fact fixed constants (`crisis_threshold=
0.90`, `needs_sleep(threshold=10.0)`, etc.). Whether RAVANA's later
commits (863 total, this audit read a snapshot) move further toward or
away from that stated principle is not established by this single-commit
read and is flagged as uncertainty §7.4.

**Nothing here is recommended for adoption.** The one place OCELOT's own
learning-progress work (§3.2) already demonstrates a shape-based
alternative to a scalar prediction-error knob — and measurably outperforms
the scalar approach on the exact failure mode (noisy-TV) the scalar
approach is vulnerable to — is itself the strongest evidence for declining
to import RAVANA's free-energy accumulator.

### 6.4 Distinct gap-kind naming — partially present, worth widening rather than importing wholesale

Per §3.2, OCELOT's `gap_awareness.json` already distinguishes gap kinds as
graph rules (knowledge/reported/instruction/self_account/reply_fix), and
this is a genuinely finer, more principled triage than RAVANA's five
flat-weighted curiosity signals in one respect (each OCELOT kind has its own
match/where predicate, not a shared scalar-weighted candidate list) and
coarser in another (RAVANA has an explicit `contradiction_map` structure;
OCELOT's `gap_awareness.json` has no rule that mints a gap specifically from
two graph-resident facts about the same entity being mutually inconsistent
— OCELOT's contradiction-adjacent seeds, e.g. `logic_nonclassical.json`,
`epistemic_access.json`, address contradiction as a *reasoning* topic, not
as a *gap-detection trigger*).

**Scoped recommendation:** a `note_contradiction_gap` rule alongside the
existing five in `gap_awareness.json` — matching two edges from the same
source node with incompatible target values on the same predicate (the
sd loop's own residual-detection machinery, §3.3, is the natural home for
"incompatible" here, since a contradiction is exactly a residual that
recognition-then-transform cannot resolve) — would close this specific,
narrow gap without importing RAVANA's `contradiction_map`/weighted-candidate
architecture wholesale.

## 7. Remaining uncertainty

1. **Snapshot currency.** This audit reads RAVANA at one commit
   (`4153b02b9b2584dddd16854b09abc912a568915c`, 2026-08-08) of an
   863-commit, actively-developed repository (commits observed at roughly
   daily-to-multiple-per-day cadence in the visible window). Architectural
   claims here — particularly the Governor-not-wired-in finding (§2.3) and
   the free-energy-scalar characterization (§6.3) — could change in later
   commits not read.
2. **Depth-limited git history.** The clone used `--depth 200`; the
   earliest commit visible locally is 2026-07-14, while the Codeberg API
   reports repo creation on 2026-05-24 and 863 total commits. The
   direct-connection author search (§5) covers the full API-reported
   history via `git log --all` on this shallow clone, which Git resolves
   against the *available* history — a full unshallow clone was not
   performed, so a citation added and later removed within the unfetched
   ~5-week window (2026-05-24 to 2026-07-14) cannot be fully ruled out,
   though it would be an unusual editorial pattern to add and retract such
   a reference without leaving any trace in docs, tests, or the current
   README.
3. **"Learning progress" wiring scope.** `learning_progress_curiosity.json`
   is confirmed live-measured and gated for the *vision* domain
   (`VISION_LEARNING_PROGRESS_RESULTS.md`, `VISION_ACTIVE_EXPLORATION_
   RESULTS.md`). Whether its `CuriosityHub`/`AttentionItem` structure is
   presently reachable from conversational gap-awareness at all (as
   opposed to only vision-frontier exploration) was not verified beyond
   the seed file and results docs read here — §6.2's recommendation
   assumes it is not currently wired to conversation, based on no
   `gap_awareness.json` reference to `CuriosityHub`/`AttentionItem`
   appearing in the file read in full, but this is an absence-of-evidence
   finding, not an exhaustively verified absence across the whole tree.
4. **Whether RAVANA's design principle #2 ("no fixed thresholds where a
   distribution exists") is honored more consistently elsewhere in the
   codebase than the specific files read here.** §6.3's characterization is
   drawn from `free_energy.py`, `curiosity.py`, `governor.py`, and
   `sleep.py` — a substantial but not exhaustive sample of RAVANA's ~590
   Python files. Other modules not read in this pass may implement
   data-derived gating more consistent with the stated principle.
5. **The creator's recollection of the "semiotic graphs + Model" direction**
   is relayed secondhand (via the coordinating session, not a document this
   agent read directly) and is explicitly uncertain even in its own
   telling ("possibly never written down at all, or lost"). Section 0 and
   §6.3 characterize RAVANA's position *relative to OCELOT's actual
   current architecture*, which is verifiable; the claim that this
   specifically retraces an early, discarded OCELOT-side direction rests on
   testimony this audit could not independently corroborate against a
   document, by the creator's own account of why no such document exists.
