# Purpose — a competent man, not a completed task

**This project is not goal-seeking. It is goal-USING.** A task, a benchmark, a
battery score is a TARGET, in the archery sense — something to aim at so the
aim can be measured and corrected — not a thing this project exists to
achieve. Landing a task is evidence a capability works; it is never the point
of building the capability. If a rung ever optimises the number at the cost of
the understanding behind it, that rung has the purpose backwards, regardless
of what the number says.

**The measure of success is Heinlein's competent man** ("a human being should
be able to change a diaper, plan an invasion, butcher a hog, conn a ship,
design a building, write a sonnet, balance accounts, build a wall, set a bone,
comfort the dying, take orders, give orders, cooperate, act alone, solve
equations, analyze a new problem, pitch manure, program a computer, cook a
tasty meal, fight efficiently, die gallantly. Specialization is for insects.")
— an agent whose competence GENERALISES across bodies, domains and problem
shapes, not one that has been fitted to any single one of them. This is why a
capability landing in one body and then being *independently re-derived* in
another (the F-16/humanoid collapse above; the sd loop itself moving from
vision to audio to ink to flight) counts for more here than the same body
scoring higher on its own benchmark — the first is evidence of a general
competence, the second is evidence of a better fit to one target.

**Consequence for how every rung in this file should be read and written:**
a null that localises the cause and generalises the lesson is a better outcome
than a pass that does not (this is why nulls are reported as headline findings
throughout this file, not buried); a benchmark score is always reported next
to what it does and does not establish about the underlying capability
(**"synthetic-proven mechanism ≠ benchmark value, report both"**, already a
standing rule below); and the SHAPES-not-numbers rule above is this same
principle one level down — a held, transferable shape is competence, a
fitted number is a score.

# Architecture rule — the agent is Rust

**The agent is a graph, running in Rust. Python is only the world
adapter.** Do not write Python agent code — no reasoning, no decisions,
no agent state, no agent loop. If you find yourself reaching for Python
to do anything other than translate external I/O into substrate
mutations, stop — you are writing the wrong thing.

This file overrides any contrary habit. Read it before you write code.

## The split

```
┌─────────────────────────────────────────────────────────┐
│  RUST AGENT RUNTIME                                     │
│  (substrate_rs — the binary / lib that IS the agent)    │
│  ───────────────────────────────────────────────────    │
│  • Substrate (G, Γ, C): typed graph + productions       │
│  • DSL evaluator: Term-trees → values                   │
│  • Rule engine: match + where + effects, fixed-point    │
│  • Reflex loop: stimulus → response, tick scheduling    │
│  • Save / load: graph_to_dict / graph_from_dict         │
│  • Audio / speech / video / codec primitives            │
│  • The agent's reasoning AS GRAPH DATA: Rules, Concepts,│
│    Microtheories, Frames, Reflexes, Productions         │
└─────────────────────────────────────────────────────────┘
                        ▲                    ▲
                        │ events             │ events
                        │                    │
              ┌─────────┴────────┐  ┌────────┴────────┐
              │  ChatWorld (Py)  │  │  AudioWorld(Py) │
              │  text in / out   │  │  bytes → ingest │
              └──────────────────┘  └─────────────────┘
                        ▲                    ▲
                        │                    │
                  external I/O          mic / file
```

**Rust runs the graph.** Match Rules, evaluate Term-trees, fire
Reflexes, schedule ticks, serialise / deserialise the graph, run
primitive operations (FFT / cochlea / IDCT / FIR / etc.).

**Python translates external I/O.** Read bytes from a file or socket,
write nodes/edges into the substrate, call `substrate.tick()`, read
graph state, write bytes back out. Each world adapter is ~50–100 lines.

That's the whole architecture.

## What Python is allowed to do

A world adapter does exactly two things:

1. **Ingest** — convert external events to substrate mutations
   (text → Message + Mention nodes; audio bytes → AudioBuffer +
   AcousticSign chain via `ingest_speech`; video frames → Image
   nodes; etc.). Mechanical translation. No conditionals over
   graph state. Use the substrate's primitives directly:
   `substrate.add_node(...)`, `substrate.add_edge(...)`.

2. **Emit** — read graph state back out and translate to external
   output (read outbound Messages → text; read generated speech
   → audio bytes; etc.). Pure mechanical query.

Between ingest and emit, call `substrate.tick()` and let the Rust
agent do its work.

A thin I/O-boundary classifier is permitted (e.g. `if text.endswith("?")
return "question"`) when it is genuinely converting an opaque external
form into the smallest graph token, AND there's no Rust primitive that
can do the job. Prefer a Rust primitive when possible.

## What Python is NOT allowed to do

Hard NO:

- **Run the Python rule engine.** `graph_rewrite.run`, `gr._match`,
  `gr._apply`. Rules run in Rust via `substrate.tick()` / `run_rules()`.
  New code must not call any Python rule engine.
- **Implement agent decisions.** Any `if`/`else` that reads graph
  state and decides what to do next is a Rule, not Python. Write
  the Rule as graph data.
- **Maintain agent state.** No Python dicts on the agent that hold
  "agent's concept index" or "agent's rule list" or anything similar.
  State lives in the substrate. Python may cache for performance,
  but the substrate is the source of truth.
- **Wrap the agent's reasoning in Python helpers.** No
  `recognise_X(agent, ...)`, no `revise_Y(agent, id, value)`, no
  `decide_Z(agent, ...)`. These are Rules.
- **Construct the agent at runtime.** The agent is a graph; loading
  the seed manifests initialises it (`boot_core`). The `CuriousAgent`
  Python class and its ~13K lines of construction/orchestration have
  been DELETED — do not resurrect that pattern (a default library is a
  seed manifest the Rust loader installs, never Python that builds it).

## When a new primitive is needed → Rust

Sometimes the existing DSL truly can't express something. Then:

1. **Add a new DSL Term in Rust** (`runners/dsl/src/term.rs` and the
   relevant variant + evaluator). The Term is a graph-resident
   primitive the agent can compose.
2. **Add a graph operation in Rust** (`runners/dsl/src/substrate.rs`
   or the engine module) when you need a new admissible mutation.
3. **Expose via PyO3** (`runners/dsl/src/py.rs`) so a world adapter
   can invoke it — the call from Python should be one line that
   hands off to Rust, not a Python implementation.

The pattern is: primitive in Rust, composition in graph. Never
"primitive in Python." Never "composition in Python." Never
"reasoning in Python."

## Seeds are modular with dependencies

The agent's "seed" — every Concept, Production, Rule, Reflex,
Microtheory, Frame the agent boots with — is **not monolithic**. A
seed is a named, versioned unit of graph data with explicit
dependencies on other seeds. An agent declares the seeds it wants;
the loader resolves the dependency closure and installs them in
topological order.

This means an agent that only does chat doesn't carry the chess
rules, the doom motor primitives, or the lever-physics laws.
Different agents = different seed sets. The same Rust runtime
serves all of them.

### What a seed looks like

A seed is a graph-resident manifest + data:

```
Seed { id: "conversation", version: "1.0.0" }
  ├── depends_on → Seed { id: "psychology" }
  ├── depends_on → Seed { id: "relations" }
  └── contains  → Production / Concept / Rule / Reflex nodes
```

Loading order is determined by walking `depends_on` edges
topologically. Conflicts (same Concept name, divergent
Productions) surface as load errors — the agent refuses to boot
with an incoherent seed set rather than silently producing
inconsistent behaviour.

### How a seed gets shipped

Each seed is a JSON or binary blob the Rust runtime can read
(`graph_to_dict` / `graph_from_dict` format) plus its manifest.
Seed authors are responsible for keeping their seed self-contained
under its declared dependencies — installing it on top of its
dependency closure must produce a valid graph.

### Teaching the agent → seeds (the `teach` facility)

When the agent is taught something — a lesson, a fact, a concept, a
rule — it must persist, or every boot starts from zero. Do NOT
hand-author a seed JSON per item (the way `rule_authoring_lessons.json`
was first made by hand). Use the ONE recurring facility:

```python
from domains.teach import teach

teach(agent, "TaughtHint",
      {"topic": "rule_fixpoint_idempotence", "answer": "..."})
```

`teach(agent, type, attrs, *, category=None, categorise=None)` does
three things: (1) adds the node to the LIVE graph (the agent holds it
now); (2) decides which seed it belongs in; (3) appends it to that
seed manifest (`seeds/<category>.json`, created if absent), so a fresh
`load_all_seeds` boots with it. Re-teaching the same `(type, attrs)`
is a no-op (idempotent).

The SAVE is mechanical host I/O — admissible adapter work. WHICH
category (which seed) is the AGENT'S call, in its own terms: with no
explicit `category`, `teach` runs the item through the agent's own
meta-shape classifier (`categorise_by_shape`, the same
`ABSTRACT_PRINCIPLES → META_SHAPES` mapping its `analogical_thinking`
faculty uses) and files it under the shape it sees the thing as
(`prediction_minus_observation`, `feedback_control`, …). If nothing
matches, it falls back to the item's own `domain`/`topic`, never
forcing a shape onto something shapeless. Teaching and
self-categorising are one motion — the agent files its own knowledge
under its own categories.

The agent's categories are itself: ask it via `drive()` — "how are you
organised?" reads its microtheories (how it IS); "what shape are you?"
reads its seven meta-shapes with sub-shapes where appropriate (how it
is SHAPED), both through the `self_organisation` / `self_shape`
reflective faculties. `teach` files by the latter.

### What stays out of seeds

World adapters are NOT seeds. A seed is graph data the agent
boots with; a world adapter is the Python (or other host) layer
that translates external I/O after the agent is running. The
adapter chooses which seeds the agent loads, but isn't itself a
seed.

### First seeds (rough scope)

- **core**: the substrate's base productions, the `Unknown` /
  `Concept` / `Microtheory` / `Frame` / `Rule` node types,
  the meta-grammar. Every agent depends on this.
- **conversation**: speech-act taxonomy (Searle), adjacency
  pairs (Sacks-Schegloff-Jefferson), Gricean maxims, repair
  kinds, conversational signs. Depends on core.
- **intent**: Intent / Unknown / Mention types + the rule set
  that builds an Intent for each Message (intent_from_claim,
  intent_from_no_claim, expects_response propagation, etc.).
  Depends on conversation.
- **referent-resolution**: lexical Concept match + Mention →
  refers_to → Concept propagation. Depends on intent.
- **pronoun-resolution**: first/second person rules. Depends on
  referent-resolution.
- **anaphora**: it/this/that rules. Depends on referent-resolution.
- **speech-bridge**: AcousticSign as Mention + denotes→refers_to
  rule. Depends on intent + audio.
- **audio**: cochlea / gammatone / STFT / A1 productions.
  Depends on core.
- **speech**: AcousticSign / Lexicon / Utterance productions +
  ingest_speech-compatible types. Depends on audio + core.
- **psychology**: mental-state vocabulary, ToM concepts. Depends
  on core.
- **relations**: foundational binary semantic relations
  (uses / has / runs_on / is_a / depends_on / ...). Depends on
  core.
- **chess** / **doom** / **walker** / **lever** / **vision** /
  **conway** etc. — each its own seed, none depended on by the
  others, each loadable in isolation.

A "text-only chat agent" seed set: core + conversation + intent
+ referent-resolution + pronoun-resolution + anaphora +
psychology + relations.

A "voice-only chat agent" seed set: same, plus audio + speech
+ speech-bridge, and drop the explicit text-mention seeding
(it's covered by the speech bridge).

A "research agent" seed set: same as voice, plus chess + doom
+ ... whatever experiments are running.

The runtime doesn't care which set is loaded — it just executes
whatever graph data is present.

## Migration is COMPLETE (2026-06-18, commit 56529c6d)

This rule is no longer aspirational — it is the enforced reality.
**`domains/curious_agent.py` is DELETED.** The Python `CuriousAgent`
class is gone, and with it the parity gate (`test_migration_parity`,
green 25/25 on its final run — seed-boot ≡ CuriousAgent) and the
one-off capture tooling.

The whole agent — perception, intent, conversation, render, teaching,
the Frame layer, goals, planning, spatial routing, the
communicate-action faculty, AND the self-growing **Γ_meta substrate**
(Γ_dynamic grown from observation, gated by a meta-grammar on the
agent's own Rust substrate) — now runs **graph-native on the
seed-booted `WorldAdapter`** (`substrate/world_adapter.py` over
`substrate/boot_core.py`): boot seeds → ingest → `tick()` /
`run_rules()` → query. Zero Python agent logic. The agent is the
graph, running in Rust.

The regression bench is now the **migrated test suite** (598 tests
green under `pytest -k migrated` as of 2026-07-02,
`tests/test_*_migrated.py` + the in-place-migrated benches), not a
Python-vs-graph comparison.

## Composer + driver migrated; dynamic quantization IS the core loop (2026-07-02, commit 28454782)

The two Python-resident cognition centres that had re-accreted after
the CuriousAgent deletion are gone:

- **The self-build composer** (`reflective_faculty.py`'s beam search)
  is the Rust **`ShapeDecode`** Term — the DEQUANTIZATION op: a
  goal/observation is DECODED against the held ShapeSignature codebook;
  parts compete, the assignment emerges, the residual is the unmatched
  span. `compose_design_for_goal` and `induce_concern` are the SAME op
  at two points of one loop. `wild_objects` selects the
  object-slot-wildcarded coverage semantics (induce path); default is
  literal (composer path).
- **Order-N growth is DYNAMIC QUANTIZATION as graph rules**
  (`seeds/shape_decode_loop.json`: `sd_decode` / `sd_recognize` /
  `sd_mint_quantum` / `sd_redecode`): a residual mints a
  CapabilityAxis quantum; `codebook_epoch` re-arms decode when the
  codebook grows. **The `run_rules` fixpoint IS the
  decode → grow → re-decode loop.** No Python iteration.
- **`ground_concern`'s 7-way dispatch** is data
  (`seeds/composer_dispatch.json`: ComposerCue priorities + a
  `composer_pick` Program); Python does a name-keyed registry lookup on
  the Term's verdict. The seven `_compose_*_rule` builders stay Python
  (legal: they only assemble Rule JSON). `cascade_decide`'s ladder is
  `seeds/escalation_rungs.json`.
- **The question driver** (`question_driver.py`) is
  `seeds/question_driving.json`: kind-dispatch is the
  `qd_bind_resolver` JOIN (Goal ⨝ Resolver via the Agent hub),
  decompose/fold-up/gap-guard/contrast are rules, gap depth is a node
  attr, and the `question_pursue` Reflex ships as seed data via the
  **`"reflexes"` manifest key** (new: `load_seed_manifest` installs
  Reflex nodes + stimulus_term subgraphs; `fire_reflexes` discovers
  seed-loaded Reflexes). `QuestionDriver` is now
  mint → ingest → pump → read-off; the executor
  (`_question_pursue_advance`) follows the `_enact_advance` precedent —
  it evaluates bound Terms and applies results, never branches.

Parity was gated on captured fixtures
(`tests/fixtures/composer_driver_parity/`, dumped from the OLD code
before the rewire) + `tests/test_composer_driver_migrated.py`,
including the end-to-end gate: partial cover → mint EXACTLY ONE
quantum → codebook grows → re-decode → recognized.

**Quanta navigation LANDED (2026-07-02, commit b5c7bffb) — same
reframe, spatial.** The map is a persistent observation BELIEF
(unknown = absence, first-class; ls20's whole-map-on-load is the
degenerate case), and `SpaceQuantum` boxes are decoded from it PER
BODY SHAPE (config-space erosion, `body_key` — 1×1 vs 2×2 route
differently over ONE belief), FOVEATED (decode only in focus,
incremental reuse), N-DIMENSIONAL with per-dimension resolution and
per-dimension residual splits — "flood does not occur per pixel, it
occurs at quanta; a remainder goes to more detail; quanta are dynamic
PER DIMENSION." Rust `space_quantize`
(`runners/dsl/src/space_quantize.rs`; py.rs is a one-line handoff) +
`seeds/quanta_navigation.json` (14 qf_* rules: epoch-gated Bellman
flood over portals, N-dim hop via the ControlResponse chain,
multi-source frontier-seek exploration, stale/retire lifecycles as
rules, msp CLOSED → mint-Hypothesis live at quantum grain). Adapters
(`spatial_sense`/`maze_run`/`arc_run`) opt in via `nav_repr="quanta"`;
cell mode byte-identical to its pre-change baseline. Gates:
`tests/test_quanta_navigation_migrated.py` 8/8 (partial-maze memory,
3D, two-body, per-dim split, foveation); bench 606 green. Honest
residuals recorded in the commit (out-of-focus quanta not retained,
projects_to minimap folding reserved, ndim≤3 unrolled in seed rules,
pocket_escape not yet replaced by qf_closed). `slide_flood` (py.rs)
remains the legacy cell-mode flood — and remains the documented
example of logic that should NOT live in the binding layer.

**Transformation = quantum change in a specific dimension — LANDED
(2026-07-02, commits 518706ed rung 1 + 65f94b70 rung 2).** A transform
(rotate/recolour/translate/speaker-shift) is not an operator class —
it is the object's quantum stepping along ONE dimension; ACTION
unifies with it. The sd loop's growth ladder is now Occam-ordered and
complete, in one `run_rules` fixpoint:

1. exact recognize (`sd_recognize`, literal decode — the old
   wild-object coverage is RETIRED: it was an unconstrained transform
   that conflated consistent substitution with incoherent novelty);
2. transform in the existing basis (`TransformDecode` →
   `sd_transform_decode`/`sd_recognize_transformed`: ONE uniform delta
   per transformed dim, predicate slot never transformable, identity
   flagged; Transform{dim,delta} minted as graph data);
3. INFER THE DIMENSION (`DimInfer` → `sd_infer_dimension`/
   `sd_recognize_dim`: a residual COUPLED across observed dims —
   "rotating a flat 2D rectangle in Z gives an XY change you can't
   replicate without Z" — decodes against a held DimensionGenerator
   codebook (rotation90/reflections, coord_dims + params as data,
   dim_types says which slots are coordinates), generator + residual
   deltas compose, and a LatentDimension node is MINTED: the dimension
   set itself is dynamic — quanta OF dimensions);
4. mint novelty (`sd_mint_quantum`, only after BOTH rungs fail).

Gates: transform 9/9, dimension-inference 7/7 (rotated tromino zero-
mint; scrambled mints exactly one; rung-order Occam), composer/driver
7/7 on the honestly-updated fixture. Bench 622 green. LatentDimension
is the hook 2D-of-3D minimap folding (`projects_to`) hangs off.

**Handwriting as dynamic quantization — LANDED (2026-07-02, in
c0288920).** Ink is decoded with a graph-resident stroke codebook; the
pickle inventories are superseded. `StrokeQuantize` (Rust,
`strokes.rs`) quantizes a pen path into the ladder's OWN format: `seg`
relations (signed relative-turn + normalized-length quanta —
rotation/translation/scale-INVARIANT shape) plus pose as SEPARATE
single-slot relations (`pose_x`/`pose_y`/`pose_o`/`pose_s`), so every
similarity transform is a RUNG-1 per-dimension quantum delta (a
rotated stroke = `pose_o +k`, read off by the unchanged
`TransformDecode` — codebook entries store full signatures at
`canonical_pose`). `TransformDecode`'s dimension pooling was
generalized to `(predicate, slot)` (two-tier: global merge first for
byte-compat, per-predicate split on numeric conflict; symbolic
substitution stays a GLOBAL rename check — splitting it would rescue
the scrambled nulls). Stroke boundaries EMERGE via segmentation-by-
recognition: a Hyp/LatEdge span lattice over arc-length knots decoded
by the UNCHANGED grain-agnostic `vit_step`/`vit_backtrace` (the speech
9f1fc077 precedent made ink-ready; both static pre-cut segmenters are
superseded for recognition). OOV spans flow into the sd loop —
`sd_mint_quantum` + `grow_stroke_quantum` + `codebook_epoch` — and
re-decode recognizes the minted quantum. **The writer's physical
limits become IMPLIED dimensions** (`seeds/writer_dimensions.json`):
per-stroke Transform pose deltas that COHERE across one hand's output
pool into a minted `WriterStyle` (rung 2 at the writer grain — the
ink twin of the speech speaker dimension; two simulated hands mint
distinct orientation-bin styles, no cross-writer pollution). Gates:
`tests/test_ink_decode_migrated.py` 14/14 (invariance; rung-1 zero-
mint transform reading; boundaries-emerge headline; OOV mints exactly
one then recognizes after epoch bump; noise null; no-Python-decision
source audit; two-hands writer dimensions). Bench 636 green. Known
engine gotcha found en route: two same-type incoming edges on one node
can break `run_rules` matching for that edge type (repro'd; the
writer shortcut edge uses a distinct type `wrote_transform`).

**The Omniglot arc (runs 1-10, 2026-07-02/03) — GENERATION AND READING
ARE ONE MODEL; AbS IS THE DEFAULT.** Ten gated runs on real ink
(`scripts/jabberwock_omniglot_dynamic_quantization.py`, logs in
`results/`), every hypothesis measured behind a protected control:
one-shot 20-way trajectory 2.5 → 3.8 → 33.8 (CHARACTER COMPOSITION =
the same sd loop one level up: strokeq + relative-pose relations,
c1b83669) → 33.8 → 26.2 (probe: finer base grain FRAGMENTS —
detail belongs in refinement children, 5f6ba026/a6fe069b) → 33.8 →
30.0/30.0/30.0 (probes: partial-credit metrics and rel2 higher-order
relations all lose — STRICTNESS IS THE SIGNAL; rel2 broke the ties
and they broke WRONG, 97d54623/e6a467e8) → **37.5 (AbS: `StrokeRender`
is `StrokeQuantize`'s exact inverse — round-trip proven — and reading
= propose-by-quantized-index, RENDER, compare via held DtwTo/
PointSetDist, held Argmin; the frame-instability residual DISSOLVED
rather than patched, 42855d5f)**. Only architecture moved the
frontier; metric surgery never did. Measured next bottleneck:
proposal recall (coverage@5 = 53.8%; re-rank converts ~70% when the
true exemplar is present) — variable-K dwell scheduling per the
VARIABLE-APERTURE-RADAR frame (2026-07-03: matched filter = AbS,
ambiguity function = per-dimension quanta as a conserved budget,
search/track = foveation + VOC escalation; import the resource
geometry, not the signal algebra). Empirical facts the arc
established: real strokes occupy ~5-7 quantized classes (identity
lives in ARRANGEMENT); real writers are style FAMILIES, not one
slant; `native.evaluate()` returns TUPLES not lists (an
isinstance(list) filter silently disabled child-minting — check
every read-back).

**RUN 15 CORRECTION (f0fae1fe) — the powered gate corrected the arc
itself.** At n=400 (10 alphabets, Wilson CIs) the honest ceiling is
**26.8% [22.6, 31.3]** — the 4-alphabet eval was an easy subset, and
EVERY post-composition delta above (AbS +3.7, dwell +1.3, appearance
+2.5, rel2 −3.8, substroke −1.2) was 1-3 episodes of noise: all arms
inside each other's CIs; rel2 (run 9's "loser") numerically top at
power. What survives CI-separated: **COMPOSITION (+21pp over
multiset)** — arrangement is real and huge; coverage@5 ~54%; a 5%
proposal-blind tail; the saturation facts; the exact
control-reproduction chain (the machinery is deterministic — the eval
SET was the error). Both fork branches (substroke run 14,
junction-blend run 15) null under power: the representation-grain
corridor is exhausted; the next lever is a different featureset.
STANDING RULES minted: (a) POWER THE GATE BEFORE THE ENDGAME — deltas
within ~3× the per-episode step are not results; (b) synthetic-proven
mechanism ≠ benchmark value, report both; (c) eval-subset coverage is
part of every claim.

**RUN 16 RECONCILIATION (7743c2de) — the run-15 terminus was
comparator-conditional and DISSOLVES.** The earlier ~81% arc
(omniglot_one_shot/recognition_graph, 2026-06-23/24: fused
ShapeContext+TPS+SmoothDeform on RAW points + parse marginalization,
training-free, held-Argmax, matched protocol) and the powered 26.8%
were BOTH real — the difference was the VERDICT COMPARATOR.
Transplant: SC+TPS at full dwell on the powered protocol = **73.5%
[67.0, 79.1]** (+51.5pp, CI-separated; per-compare ~2.3ms, CHEAPER
than the weak render path). THE SYNTHESIS: earned quanta are the
LEARNING/PROPOSAL layer (codebook growth, composition +21pp,
transforms, writer dims); strong continuous geometry is the VERDICT
layer — "bins propose, continuous decides," measured. Run-11's
"widening hurts" inverts under a strong verdict (full dwell beats
shortlist +25.5pp — proposal recall ~53%@5 binds again and is a real
lever). Standing: 73.5%; named remaining levers: proposal recall/
width, tuned fusion weights, parse marginalization, full-n
confirmation. (The 83.3% Gemma-arc number discounts: 10-way, n≤40,
borrowed net deciding.)

## BASE-AS-DIMENSION + the frame/continuum invariant (2026-07-08) — "non-integer math is CROSS-FRAME, never IN-frame"

Two new dimension generators landed on the rung-2 `DimInfer`
pipeline: `scale2` (multiplicative ×2^k — a log-scale base) and
`modular` (cyclic Z_n step with wrap). What they demonstrate: **a
"base" (log / scale / cycle) is NOT hand-set per-frame config — it is a
`DimensionGenerator` that `DimInfer` selects and `sd_recognize_dim`
mints as a `latent:<gen>` `LatentDimension`. A base IS a dimension.**
The sd loop's `has_transform`-edge guard makes it mint-once and
terminate under codebook growth (Rust `shape_decode.rs::dim_infer_tests`
+ `tests/test_dimension_inference_migrated.py`; seed
`shape_decode_loop.json`). A ratio (×2) or a cycle wrap becomes the
additive integer `k` rung 1 already reads for free, so a whole
scale / cycle FAMILY collapses to one held shape + one dimension instead
of a fresh `CapabilityAxis` per member (grows capability AND improves
efficiency).

The governing invariant this crystallised — it binds every future line
of work in this tree:

- **In-frame is INTEGER.** A grounded/observed frame's coordinates are
  the integer lattice. `shape_decode.rs::coord_ints` returning `None`
  on a `Float` slot is CORRECT and load-bearing, NOT a gap — do not
  "add continuous coordinates." Observation is stepped by construction
  (sampling / quantization is what grounding IS).
- **Non-integer math is CROSS-FRAME.** All real-valued structure —
  rotation by a real angle, real scale ratios, π, Fourier
  (spatial↔spectral), log (linear↔log), the SC+TPS / DTW verdict
  metrics, renderings — lives in the MAP between frames (a generator /
  `Transform` / base / comparator / rendering), NEVER in a frame's
  coordinates. The continuum sits in `Hom(frame, frame)`, not in any
  object. "Bins propose, continuous decides" IS this: the continuous
  verdict is a cross-frame comparison of observed vs rendered candidate.
- **Continuity is INTENSIONAL only.** A continuous quantity is a RULE
  you APPLY (π applied; a Cauchy-sequence generator), never an observed
  datum. A cross-frame map may carry a continuous parameter
  intensionally; its observable is always the stepped (integer-`k`)
  rendering extensionally. Identifiability guard: pin a continuous
  parameter only to observational resolution — never encode precision
  the steps cannot support (MDL). "You can apply π, but any given
  circle is stepped."
- **Two orthogonal unbounded axes.** The graph has an EXTENSIVE
  unbounded direction (the frontier — unknown = absence, first-class;
  countable, ℕ; "there is always one more step outward") and,
  ORTHOGONALLY, an INTENSIVE one (refinement / depth — betweenness; its
  unreachable limit is the continuum, 𝔠). You CANNOT reach a continuum
  by extending the discrete frontier (a countable union of countable
  steps stays countable); only refinement-to-the-limit is uncountable,
  so the continuum necessarily sits on a SEPARATE dimension. Both are
  unbounded for the SAME reason (unknowability) and both are intensional
  — never stored complete (you store the finite observed part + the
  fact that it does not end).
- **The decision procedure for every number you write:** *is this value
  IN a frame, or BETWEEN frames?* In-frame ⇒ it MUST be integer (a float
  there is a category error / bug). Between-frames ⇒ it MAY be real (a
  float in a map / metric / rendering is correct). This one test
  generalises the two facts already in the code — `coord_ints` refuses
  floats, and the SC+TPS / DTW verdict is continuous.

Consequence for refinement-depth (dyadic): it is therefore NOT a
`DimensionGenerator` (design proof in `runners/dsl/DYADIC_DEPTH_DESIGN.md`
— the count-preserving `x→2x` reading is a byte-identical `scale2`
alias; the count-MULTIPLYING subdivision violates `build_candidate`'s
equal-count contract). Its home is the `space_quantize` flood ladder as
a first-class CROSS-FRAME (coarse→fine) axis whose limit is the
continuum — `SpaceQuantum.depth` + `refines` edges + a
`qf_refine_residual` rule, co-designed with the flood ladder's existing
residual→refine contract. Deferred for review, NOT bolted on.

## THE AGENT FIXES ITSELF WHERE IT IS GRAPH-NATIVE (2026-07-08) — "self-repair ⟺ graph-native; Python is the blind spot"

Directive: *"get the jabberwock to fix itself where at all possible."* The
sharp boundary that makes it precise: **the agent can self-repair exactly where
its cognition is graph-native.** Its self-improvement machinery operates on
graph data — adopt/ablate seed rules (Experiment→judge→adopt), acquire missing
concepts (teacher / grounding), propose Rust Terms (rung-4). It CANNOT edit the
Python front end (e.g. `comprehend_text`'s dispatch ladder), because that is not
graph it can see or vary. So **every piece moved Python→graph becomes
self-repairable** — that is the real payoff of the migration. Bootstrapping
asymmetry: a human/coding-agent moves logic Python→graph (the agent can't do
that to itself); the agent then repairs/improves it within the graph.

First landing under this directive — the **"moon bug"** (`"What do you know
about the moon?"` → `"I am Jabberwock."`) fixed by the split:

- **Possessive self-reference is UNDERSTOOD by the graph, not string-matched
  (2026-07-09, conversation_topic_route v1.1.0).** "How does YOUR collapse
  function work?" was grounding "your collapse" as an external topic. The fix is
  NOT a Python `head in SELF_WORDS` check (twice attempted, twice rejected — that
  is a routing decision masquerading as parse) but a GUARD the route rule reads
  from what the graph RESOLVED: a mention that `refers_to` a second-person
  Concept (`your`/`yours`) AND has a `next_mention` (it determines a following
  noun) is a possessive self-reference → the possessed nominal is about the
  agent → the route defers to the reflexive self path. "what do you know about
  the moon" has no such possessive ("you" is the subject; "moon" follows "the"),
  so the moon route is unaffected. The discriminator (possessive-self vs
  subject-self+external-object) lives in referent resolution + mention adjacency
  the RULE inspects — the graph deciding from what it understood, verified live.
- **Routing is now the graph's decision (migrate).** `comprehend_text` (Python)
  routed ANY question with a second-person self-cue (`you`/`your`) to a
  self/meta faculty, discarding a genuine external topic. The adapter now writes
  the parse's external **object/oblique** nominal onto the Message as
  `comp_topic` + a `topic_pending` marker (`world_adapter._external_topic_nominal`
  — NEVER the self-word subject; only for reflexive questions, so every
  already-working non-reflexive path is byte-unchanged), and the rule
  `route_question_to_topic` (`seeds/conversation_topic_route.json`) DECIDES the
  turn is about that external topic and mints `Goal{kind:answer_topic}`. A
  genuinely self-referential question (`"What are you?"`) writes no `comp_topic`
  (`topic_pending` absent → `None` in the DSL), so the rule never fires and the
  self/meta path is untouched.
- **Knowledge gaps self-heal (selflearn).** The adapter renders the answer from
  the graph's decision via `answer_about(concept)`, and on a MISS grounds the
  topic through the agent's OWN self-teacher chain (`ground_unknowns` →
  dictionary/wiki, which memoises under `taught_<form>` — exactly what
  `answer_about` reads back) then re-answers. The agent fixing its own knowledge
  gap, no Python decision — `ground_unknowns` is the documented per-word teacher
  I/O loop (the teacher decides meaning; the adapter is only the loop). When
  grounding can't reach a topic, an honest floor reply invites the human to
  teach it (the human-gated close) — it does NOT auto-file a concern per unknown
  fact (that would flood the self-improvement pipeline).
- **Capability/self gaps → the human-gated self-improvement seam (selfimprove),
  already standing.** An explicit self-directed instruction
  (`improve`/`fix`/`learn`/…) files a `SelfConcern{status:'noted'}` gated by the
  agent's own comprehension confidence (`seeds/conversation_self_concern.json`);
  a human promote turns it into a `StandingConcern{status:'pending'}` the
  self-improvement pipeline runs. Knowledge gaps close via self-heal; capability
  gaps enter this gated loop.
- **Self-account gaps (gap_awareness v1.3.0).** When the agent UNDERSTANDS a
  question is about its own faculty ("how does your collapse function work" —
  routed self by the possessive guard, not external) but holds no account, the
  reflexive path hits the honest self floor; the adapter records that outcome
  mechanically (`self_account_unresolved` + the faculty asked about) and
  `note_self_account_gap` files a `SelfConcern{kind:'self_account'}`. A
  self-question it can't answer becomes a gap it FINDS about ITSELF (verified
  live: "your imagination"/"your attention" filed as self_account gaps),
  surfaced and promotable — not a dead-end shrug. The gap content is the faculty
  named CLEANLY: `_topic_facts` strips a leading possessive determiner
  (your/yours/my/… — the same morphosyntactic normalisation as the article
  strip, NOT routing), so it files "reasoning", not "your reasoning".
- **The agent ANSWERS its core faculties (self_processes v1.0.0 → collapse /
  imagining / attending added, grounded in the real architecture).** A
  `SelfProcess{process, aliases, account, source}` node the agent HOLDS is found
  by `find_self_process` (comprehend_text, manner branch) and rendered by
  `run_self_process`, so "how does your collapse function work" answers from the
  held account (the collapse loop) instead of the honest floor — and files no
  gap. Only faculties with NO held account (e.g. "reasoning") still file a
  self_account gap. Live-verified after adding SelfProcess reconciliation:
  `_reconcile_seed_typed_nodes` (generalised from `_reconcile_seed_concepts`)
  installs missing top-level-seed `SelfProcess` accounts (by `process`) on
  resume — else the new accounts, being nodes, would not load on the checkpointed
  daemon. Gate: `test_accounted_self_faculty_is_answered` +
  `test_unaccounted_self_faculty_files_a_clean_self_gap`.

Gate: `tests/test_topic_route_selfheal_migrated.py` 4/4 (routes to topic not
self; self-heals via teacher and persists the grounding; self-referential and
manner questions unchanged — no `answer_topic` goal). Conversation/comprehension
migrated suite green (93 passed).

> **RETRACTED (2026-07-21) — the sentence that stood here was a COUNT-SHAPED
> BASELINE, and it was false.** It read: *"the only bench failures anywhere are the
> pre-existing missing-`chess`/vision optional-dep errors."* Measured
> (`VISION_GATE_SCOPE_B_RESULTS.md` §3.1): with `chess` installed and `data/`
> symlinked there are **ZERO collection errors and 53 genuinely red files / 144 red
> node ids**. The claim was **environment-conditional and was quoted without its
> condition** for ~10 days, and because it characterised the reds instead of
> ENUMERATING them, every later rung could honestly "hold the baseline" while it
> grew. **A BASELINE MUST BE A LIST OF NODE IDS, NEVER A COUNT OR A
> CHARACTERISATION — a count can be held; a list has to be read.** The list is
> `results/failure_baseline.json`, gated by
> `tests/test_failure_baseline_migrated.py`; see `VISION_BASELINE_LIST_RESULTS.md`.
> **Do not replace this paragraph with a number.**

## THE AGENT FINDS ITS OWN GAPS (2026-07-09) — "fix what it can; else find the gap, explicitly or implicitly, over NL"

Directive: *"the jabberwock should be able to fix these itself. if it can't, it
should at least find the gap — explicitly or implicitly — via a natural language
interface. help it build that for itself, graph-native."* (Prompted by two
conversational residuals — no elaboration on "tell me more"; a proper noun
dropped from a topic phrase.) A first attempt PATCHED these in the adapter with
Python cue-sets / parse-repair heuristics and was correctly REVERTED — that is
agent logic, forbidden here. The right build is a **gap-awareness faculty**
where every decision is a rule and the adapter only records facts / renders:

- **Implicit detection (rule).** `_answer_topic_reply` MECHANICALLY records the
  factual outcome of an answer attempt on the `answer_topic` Goal
  (`outcome="resolved"|"unresolved"` — a datum, not a decision). The rule
  `note_unresolved_topic_gap` (`seeds/gap_awareness.json`) DECIDES an unresolved
  topic is a knowledge gap and files a `SelfConcern{source:"implicit",
  kind:"knowledge"}` (once, via a `gap_noted` guard). "arc agi v3 ls20" now
  becomes a filed gap the agent is aware of, not just an honest shrug.
- **Explicit report over NL (rule + held Concepts).** Deficiency cues
  (cannot/fail/repeat/gap/limitation/stuck/unable/struggle/weakness/broken/wrong)
  are seeded as `Concept` nodes; `note_reported_gap` fires when a received
  interlocutor utterance has a Mention resolving (intent seed's
  `Mention -refers_to-> Concept`) to a deficiency concept AND to a self-word
  concept — filing `SelfConcern{source:"explicit_report"}` + a confirming reply.
  Recognition is graph-native (held Concepts + the referent rule), NOT a Python
  keyword set. "You cannot elaborate…" → files a gap.
- **Surfacing over NL (reflective reader + lexicon data).** `_run_self_gaps`
  (`domains/reflective_faculty.py`, registered in `_DISPATCH`) READS the
  `SelfConcern` nodes and formats them; `seeds/question_targets.json` routes
  "what gaps/limitations/weaknesses do you have", "what can't you do" to it.
  "What gaps do you have?" now lists them grouped by source instead of "I am
  Jabberwock."
- **Precedence (mechanical).** A self/meta query must not be hijacked by the
  topic router; `_write_comprehension_to_graph` defers (writes no `comp_topic`)
  when the front end already set `dispatch.path=="meta"` AND the extracted topic
  head is itself a self-word — reconciling two parse outputs, not a new decision.
- **Repair = the existing human-gated spine.** Gaps ARE `SelfConcern` nodes, so
  `promote_self_concern` → `StandingConcern` → experiment/adopt already applies.

The honest boundary this realises: a knowledge gap self-heals via grounding; a
graph-native gap can be experimented on and adopted; **the parse mis-tag ("arc")
is a Python-layer gap the agent can only FIND and FILE, never self-repair** —
surfacing it IS the correct behaviour there ("if it can't fix it, at least find
it"). Also landed: `_reconcile_seed_concepts` (`scripts/jabberwock_daemon.py`) —
`_reconcile_seed_rules` is rules-only, and gap_awareness is the first seed
shipping Concept nodes its rules depend on, so a resumed daemon idempotently
find-or-creates missing top-level-seed Concepts by name (else `note_reported_gap`
can't match after resume). Gates: `tests/test_gap_awareness_migrated.py`,
`tests/test_self_gaps_surfacing_migrated.py`, `test_self_concern_promote_migrated`
(concept-reconcile); conversation/self migrated suite green (115 passed), only
the pre-existing missing-`chess`/vision optional-dep errors elsewhere. Live loop
verified on the daemon. Known residual (NOT patched in Python): gaps aren't
deduped by content in the surfacing list.

## THREE RESIDUALS THROUGH THE GAP PIPELINE (2026-07-09) — "the jabberwock in full control"

Directive: *"address all three via this pipeline — the point is the jabberwock
should be in full control."* The three conversational residuals were routed
through the agent's own gap/self-improvement machinery rather than hand-patched:

- **Dedup (graph-native rule guard).** Both gap-minting rules
  (`seeds/gap_awareness.json`) carry a content-dedup `where` guard (`Not Exists`
  a `SelfConcern` whose content equals this gap's, via `NodesOfType`), so each
  distinct gap is filed once. The rule declines to re-file — the agent's own
  decision, not a Python filter.
- **Elaboration (graph-native progressive disclosure, `seeds/conversation_elaborate.json`).**
  A `request_detail_for_current_topic` rule mints a `DetailRequest` for the
  current topic; a mechanical dispatch (`fetch_dispatch.scan_and_ingest_detail`
  → `topic_grounding.topic_detail`) ingests the article body as a `DetailChunk`
  chain (topic `-detail_head->`/`-next_detail->`, exactly like fetch_dispatch's
  Mention chain — mechanical I/O); `serve_next_detail_chunk` serves the NEXT
  unserved chunk (served-marker + `InNeighbours next_detail` predecessor check —
  NO arithmetic cursor) one per continuation cue, `elaboration_exhausted` closes
  honestly, and `resolve_anaphor_to_current_topic` gained a `Not(cue)` exclusion
  so "tell me more" reaches the serve rule instead of re-serving the summary.
  Continuation cues (more/elaborate/continue/further/else/expand) are held
  Concepts. The serve DECISION + progression live in rules; the adapter only
  ingests chunks and renders (its only change was ONE line registering the seed).
  Verified live: successive "tell me more" walk moon → geophysics → phases →
  history.
- **Parse mis-tag ("arc" dropped) — the blind-spot handled correctly.** Routed
  through the pipeline as a FINDABLE gap (ungroundable mis-parse → implicit gap;
  "wrong"/"broken" deficiency concepts → explicit report), but the POS-tagger fix
  itself is a Python-layer gap the agent can only find/file/surface — surfacing
  it IS the right behaviour. NOT patched in Python.

**The enabling operational fix — rule-body refresh on resume
(`scripts/jabberwock_daemon.py`).** `_reconcile_seed_rules` was add-only by name,
so a checkpoint-resumed daemon silently ran STALE bodies of EDITED rules (this is
why dedup + the elaboration precedence didn't take live until fixed — they were
edits to existing rules, green on fresh boot). It now REFRESHES a changed rule
(tombstone via `remove_rule` + reinstall from file) — gated to `_REFRESHABLE_SEEDS`
(the migration seeds, whose hand-authored standard-Term rules round-trip cleanly
through `_canon_rule_body`; the exotic-Term rule zoo stays install-only so it is
never churned) and leak-free (refresh fires only on a real canonical-body diff).
This is the "edit a seed rule, restart, it applies" workflow. Gates:
`test_self_concern_promote_migrated` (refresh + leak-free idempotency),
`tests/test_elaboration_migrated.py` 5/5, `test_gap_awareness_migrated`
(dedup); broad conversation/self/topic migrated bench green, only the
pre-existing missing-`chess`/vision optional-dep errors.

**The agent retracts its own LEGACY duplicates (2026-07-09, gap_awareness v1.2.0).**
The dedup guard only prevents NEW dupes; gaps filed before it existed stayed
duplicated. Rather than a Python cleanup, the agent retires them ITSELF via
`retire_duplicate_gap` — batch-safe with NO node-id: the survivor is `Argmin`
over the same-content active gaps (returns exactly one element from a fixed
snapshot within a pass), and a gap is retired (`status='retired'` + `del_edge
has_self_concern`) iff it is not identity-`Eq` to that survivor (`Eq` compares
`Value::Node` by id). Scoped to `source in {implicit, explicit_report}` (the
auto-found gaps) so the human-gated conversation concerns (the promote flow) are
never auto-retired; the surfacing reader skips `status=='retired'`. It runs in
the agent's own `run_rules` fixpoint — verified live: the daemon retired its own
duplicate `zzqqwx` / reported gaps on resume, keeping one of each. Gate:
`test_gap_awareness_migrated::test_agent_retires_legacy_duplicate_gaps`.

**What still exists in Python — and is allowed:**

- `substrate/world_adapter.py` — the host layer. Big, but every method
  is mechanical I/O or fires a seeded Term/Rule (no decisions). This is
  THE world adapter.
- `domains/*.py` — world adapters (chat/audio/vision/chess world I/O),
  seed/Term BUILDERS that emit graph data (e.g. `spatial_routing` Term
  builders, `worlds.chess_world`), and pure capability classes
  (`ToolBox`, the teacher classes, `GraphEye`). No agent decisions.
  `reflective_faculty.py` and `question_driver.py` are now in this
  class too (post-28454782): builders, mechanical readers, and thin
  shims over ShapeDecode / the seeded rule loops — the beam search,
  the 7-way dispatch, the kind-dispatch recursion, and `_gap_depth`
  are gone from Python.
- The Python `substrate.Substrate` / `TypedGraph` — used by world
  adapters + tests to BUILD external world graphs the agent ingests.
  No agent runs on it; the agent runs on the Rust `substrate_rs`.
- `tools/*` — one-off authoring/capture scripts that EMIT seed
  manifests (deletable; not agent runtime).

**Every new commit still obeys the rule:** add Rust + graph data, OR
keep Python to a thin world adapter / seed builder, OR remove
deprecated Python. No new agent decision logic in Python, ever.

CAUTION (learned the hard way): a linter / stray working-tree edit can
silently delete adapter methods. The migrated bench is the guard — run
`pytest tests/ -k migrated` before trusting a green-looking working
tree.

## Self-correction prompts

If you catch yourself writing Python that violates this rule, stop:

- You're writing an `if`/`else` that decides what to add to the graph.
- You're calling `gr.make_rule` / `gr.run` / `_match` / `_apply` in
  new code (these are Python; new rules get installed at the Rust
  level when the seeder runs).
- You're adding a method on a Python class that holds agent state.
- You're adding a Python file under `domains/` that contains
  decisions (conditionals over graph state) — only world adapters
  belong there, and only as mechanical translators.

The fix is the same every time: put the decision in the Rust
runtime or in graph data. Extend Rust if and only if the existing
DSL cannot express what the graph form requires.

## What good Python code looks like under this rule

```python
# ChatWorld — a world adapter. ~80 lines, no decisions.
class ChatWorld:
    def __init__(self, substrate):
        self.s = substrate

    def add_inbound(self, text: str) -> NodeID:
        mid = self.s.add_node("Message", {"text": text})
        self.s.add_edge(mid, "sent_by", self.interlocutor_id)
        # Tokenise — mechanical text-to-graph translation.
        for word in text.lower().split():
            clean = word.strip(".,?!;:")
            if not clean:
                continue
            mn = self.s.add_node("Mention", {"text": clean})
            self.s.add_edge(mid, "has_mention", mn)
        # Hand off to the Rust agent.
        self.s.tick()
        return mid

    def outbound(self) -> str | None:
        # Walk the graph for unsent outbound Messages.
        for m in self.s.nodes("Message"):
            if self.s.node(m)["attrs"].get("from") == "agent":
                if not self._has_been_sent(m):
                    self._mark_sent(m)
                    return self.s.node(m)["attrs"]["text"]
        return None
```

No decisions, no rule engines, no Python state, no agent logic.
Translate, tick, translate back.

## Reminder

The architecture rule is not a style preference — it is the project.
A Python-resident reasoning system is a different project, one that
has been built many times before and is not interesting. The thing
worth building here is the graph-resident, Rust-runtime one. Do not
let convenience turn the project into the other one.

If you are about to write Python agent code, do not.
## The optional-dep note — CONDITIONED AND RETRACTED, 2026-07-21

Three places in this file used to close a status line with *"the only bench failures
anywhere are the pre-existing missing-`chess`/vision optional-dep errors."* All three are
now retracted in place. This note is the measurement behind those retractions, and it
carries its conditions because **the original defect was a claim quoted without one.**

**Collection errors, one engine, one moment:**

| condition | collected | collection errors |
|---|---|---|
| `chess` **INSTALLED** (1.11.2), `data/` absent | 8347 | **0** |
| `chess` **BLOCKED**, `data/` absent | 8208 | **5** |

The five are all `import chess as pc`: `test_chess`, `test_cross_world_migrated`,
`test_discovery_migrated`, `test_meta_curiosity_and_t3_migrated`,
`test_multi_agent_migrated`. **The vision half of the old claim is stale twice over —
those are SKIPS now, not errors.**

**COLLECTION ERRORS AND ASSERTION FAILURES ARE DISJOINT POPULATIONS**, and the old
wording conflated them. The red count is itself condition-dependent, which is exactly why
it must not be quoted bare:

| condition | red files | red node ids |
|---|---|---|
| `data/` **symlinked** | ~53 | 144–145 |
| `data/` **absent** | 147 | **565** (reproduced exactly on a second sweep) |

Both stand under their conditions. A rung that sized a prediction from the first figure
while measuring under the second missed by 3.4×.

**DO NOT USE THIS NOTE TO DISMISS A RED.** The defect was never the count — it was that a
status line was reusable as an excuse. The enumerated baseline is
`results/failure_baseline.json`, gated by `tests/test_failure_baseline_migrated.py`.
A historical record is never converted; a standing claim always is.

## SHAPES, NOT NUMBERS — new work composes with the sd loop and the admissibility grammar, it does not reinvent them (2026-08-06/07, F-16 + humanoid retrospectives)

**The rule, stated for reuse** (`docs/regime_pareto_frontier_prereg.md`, "The
session in one line — match SHAPES, not numbers"): *"The tree is a shape
matcher, and every defect found today was somewhere a number had been put where
a shape belonged."* This is not a one-off finding — it was measured
**independently, in two different embodiments, in the same week**, and it
generalises past both.

**Two generative primitives already exist in the substrate for exactly this.**
Both are core, not optional, not domain-specific:

1. **The sd loop** (see "DYNAMIC QUANTIZATION IS THE CORE LOOP" above) —
   `ShapeDecode` / `ShapeSignature` / `sd_recognize` / `sd_mint_quantum`:
   decode an observation against a held, growable codebook; mint a quantum
   only when the residual will not fit. This is how the tree represents a
   *quantity that changes*, including the order-0/order-1/order-N viability
   ladder (reflex / held-ratio / search) that the F-16 arc built directly
   inside `shape_decode.rs` rather than as a separate one-off.
2. **The admissibility grammar (Γ)** — part of the substrate's original
   `(G, Γ, C)` foundation (`runners/dsl/src/grammar.rs`, `checker.rs`):
   `Production{src-pattern, edge_type, tgt-pattern, where-clause, weight}`
   generatively decides what edge is *allowed to exist*; `admissible_moves`
   returns `(type, attrs, weight)` for selection. This is how the tree
   represents *what a system may do*, as a generated set, not a filtered one.

**The measured failure mode, three times over, is the same failure mode:** a
new subsystem invents a scalar knob (a rate, a floor, a threshold, a fixed
weight) or a rule that writes graph state directly (bypassing `check_edge`)
instead of decoding against a codebook or generating from a grammar.

- **F-16 (`docs/regime_pareto_frontier_prereg.md`, Blocks CD–CQ).** The
  learning-rate machinery regressed without terminating: *"1/n asserts
  stationarity → declare a floor 0.05 → a flat floor costs quiet regimes →
  declare a surprise factor 2.0 → surprise needs a reference → an EMA → the
  EMA needs a rate → ... 1/n. Each rate needs a rate."* Measured across the
  tree: **60 count-divided (`1/n`) learners across 8 embodied seeds, and not
  one of them inside the sd-loop, shape-codebook, spatial-quanta or
  conversation faculties** — "the faculties that match shapes never needed a
  number. The ones that match numbers are where every defect lives." The
  motor-program's slope collapse had to be **hand-written as a bespoke rule
  when it is rung 2 of a ladder that already exists** — "everything the sd
  loop gives shapes for free — recognise, transform, infer, mint — the motor
  path reimplements or does without."
- **Humanoid (`HUMANOID_DECOMPOSITION_CONTINUATION.md`).** `HumanoidComposer`
  sums nine cost terms unconditionally and minimises greedily; the deciding
  path has **no Γ productions at all**, and rule effects write via
  `graph.insert_edge` directly, bypassing `check_edge` entirely (the `gated`
  flag is reserved and unbuilt). *"The entire premise of admissibility grammar
  is that we don't have to choose a single fixpoint."* This doc names the
  F-16 finding explicitly as **the same collapse, independently measured, in
  the other body** — and warns that set-valued selection alone does not fix
  it if the generated response set itself has holes ("a gate whose middle
  region is empty is a delay line" — the fix is in what the grammar can
  *generate*, not in replacing the selector).
- **Bigville (`BIGVILLE_ADMISSIBILITY_GRAMMAR.md`, design-only, not yet
  built).** A third independent occurrence: violence is **15 rules across 4
  seeds**, a full subsystem rivalling the economy in engineering weight, and
  **none of the four violence seeds declares a single grammar production**
  (`"productions": []`, measured in all four) — a richly modelled *behaviour*
  where the substrate's own shape (admissible-by-default conduct;
  inadmissibility as the rare marked residual) says it should be a
  **generated absence**, not a bespoke subsystem per transgression.

**The standing design rule, for every new subsystem from here on:** before
adding a rate, a threshold, a fixed weight, or a rule whose effects write
graph state directly, ask which of the two primitives the thing actually is —
*a quantity that changes* (sd loop: decode / recognise / transform / infer /
mint) or *a set of allowed moves* (Γ: a production, not a filter on one). If
it is neither, that is worth stating explicitly, because on the measured
record so far it usually has been one of the two and the number was standing
in for a shape nobody had looked for yet. **A scalar knob is not a simplification
of this — it is the unpaid debt**, and per the F-16 regress it does not stay
paid off: each ad hoc rate eventually needs its own rate.

**Status, honestly:** the sd loop's order ladder is *built* (F-16, live in
`shape_decode.rs`). The humanoid's Γ-refounding and bigville's
admissibility-grammar refactor are both **named, not built** — this section
is a standing rule for new work, not a claim that every existing subsystem
already complies. Do not read "the rule is stated" as "the rule is enforced
everywhere"; the enumerated non-compliant sites above are exactly that —
enumerated, not fixed.
