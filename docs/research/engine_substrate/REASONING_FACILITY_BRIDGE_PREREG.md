# Bridging deduction, analogy and CAN — three candidate bridges, registered before any code change

**Status: PREREG.** No seed/domain code has been written yet. Matching
`CAN_CONCEPT_REIMPLEMENTATION_SPIKE.md`'s own methodology precisely: mapping
claims are registered here, verified against real code before being relied
on, and the smallest real bridge the investigation finds buildable is built
in a follow-on RESULTS doc — not the other way around.

**Charter, precisely.** *"Back to the general concept of reasoning and
solving"* → *"both"*: this rung is the FIRST half (wiring three independently
built, independently working reasoning facilities together); a sibling rung
(combinatorial solver / treewidth / Bethe-BP, `can_ops.rs`/`shape_decode.rs`)
is the second, explicitly out of scope here.

**Worktree:** `/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/reasoning-bridge`,
branch `reasoning-facility-bridge`, base `main @ 19fdddf` (verified via
`git log --oneline -1 main` before branching; re-checked against the task's
own quoted tip, unchanged).

**Confidence convention**, matching the arc's own standing discipline: a
claim verified by reading source in THIS tree carries `file:line`. A claim
backed by an actual run carries **[RUN]** with real output. Nothing below is
asserted without one of the two.

---

## 0. The three facilities, as they exist today — read, not assumed

1. **Deduction** (`domains/propositional_deduction.py`,
   `domains/inference_generation.py`, `seeds/inference_logical.json`). A held
   implication `P⇒Q` is a `ShapeSignature{kind:"knowledge_logical"}` node.
   `detect_implication_gaps`/`resolve_implication_gap`
   (`inference_generation.py:943-1003`) decode a stated fact against the
   codebook and mint the consequent via
   `situation_model_reader.ingest_predication` — genuine modus ponens (and,
   since `DEDUCTION_EXTENSION_RESULTS.md`, modus tollens + conjunction) over
   **`SmEntity`** nodes: open-vocabulary, name-keyed, persistent across a
   read (`situation_model_reader.py:264-282`, `_entity`). `resolve_
   implication_gap` returns `{"minted", "gap":{"entity":name,...},
   "supplies":{"relation":"is_a","attr":...}}` — entity name + derived attr
   name are both plain strings, directly available to a caller
   (`inference_generation.py:966-1003`).

2. **Analogy** (`domains/analogical_thinking.py`,
   `seeds/blob_edge_concept_correspondence.json`, `runners/dsl/src/term.rs`
   `TransferDecode`, `seeds/mechanism_index.json`). Two independent
   mechanisms, both over **`Concept`** nodes:
   - `_pair_witness`/`record_pair_correspondence`
     (`analogical_thinking.py:414-461`, `540-575`) mints a `BlobEdge`
     correspondence between two Concepts whose `AntiUnifyWitness` template
     shares real evidence, built from a **fixed-arity relation vector**
     (`_concept_shape_vector`, `:388-411`) read off each Concept's
     `name`/`category`/`definition` TEXT slots against a held
     `FunctionalRole`/`ShapePrinciple`/`MetaShape` keyword vocabulary
     (`_concept_reading`, `:202-229`).
   - `TransferDecode` (`term.rs:1281-1310`) + `seeds/mechanism_index.json`
     recognizes a goal's meta-shape and re-instantiates a held `Mechanism`'s
     abstract `steps` with the goal's own fillers — a **procedure** transfer,
     not a structure comparison; only 2 `Mechanism` nodes exist today
     (`spatial_foveation`, `homeostatic_regulation`).

3. **CAN** (`seeds/can_native_reimplementation.json`,
   `seeds/can_decay_identity.json`, `worlds/bigville_can_beliefs.py`,
   `runners/dsl/src/can_ops.rs`). A belief network is a **`Microtheory`**
   `-has_concept->` **`Concept`** pool, each Concept carrying quantized
   `state∈{-1,0,+1}`, `external_field`, `identity_field`,
   `causal_influence` edges to other Concepts in the SAME Mt. Evidence
   arrives at a Concept via the EXISTING, already-shipped primitive
   `concept_apply_evidence(concept, evidence, alpha)` → `h_i ← h_i +
   α·evidence` (`can_ops.rs:863-871`, PyO3 binding `py.rs:2596-2610`,
   already called by `worlds/bigville_can_beliefs.apply_scenario_evidence`,
   `:212-217`, with `alpha=0.6`). `worlds/bigville_can_beliefs.
   build_resident_can_mt` (`:134-176`) mints ONE resident's real network:
   `Microtheory{name: f"{resident_name}_beliefs"}`, 5 `Concept{name: topic}`
   nodes (`trust_mayor`, `claim_credible`, `world_safe`, `self_worth`,
   `debtor_trustworthy` — plain lowercase-underscore strings, the SAME
   string convention `propositional_deduction._norm_attr` produces),
   real per-resident `causal_influence` weights drawn from
   `seeds/bigville_cast100.json`'s 100 real residents.

**The three facilities share one substrate, one graph engine, and (per §0
above) TWO of the three even share the SAME string-naming convention for
their own domain vocabulary — but nothing today reads a fact out of one and
writes it into another.** Confirmed by grep: zero cross-references among
`propositional_deduction.py`/`inference_generation.py`,
`analogical_thinking.py`, and `can_native_reimplementation.json`/
`bigville_can_beliefs.py`.

---

## 1. Candidate 1 — Deduction → CAN evidence

**Question, falsifiable:** does the entity a derived fact is about (an
`SmEntity`) have, or could cleanly get, a corresponding CAN `Concept` node
whose evidence a derived fact should update?

**Prediction A (node-type boundary):** `SmEntity` and `Concept` are
DISJOINT, unrelated node populations with zero existing linking mechanism —
confirmed by reading `situation_model_reader.py` in full (SmEntity: open
name pool, minted on demand by `_entity`, `:264-282`) against every
`Concept`-minting site in `domains/*.py` (358 grep hits, spanning
acoustic/vision/CAN/meta-shape/lexicon uses — `Concept` the node TYPE is
badly overloaded across the whole tree, per `SHAPE_TYPE_VOCABULARY_SPIKE.md`'s
already-landed finding that node type is the only real partition and `Concept`
crosses many unrelated pools). **If true**, a GENERAL bridge (any SmEntity →
its CAN concept) needs real entity-resolution work; a NARROW bridge is only
possible under an explicit naming convention.

**Prediction B (a naming convention already exists to exploit):**
`worlds/bigville_can_beliefs.build_resident_can_mt` mints
`Microtheory{name: f"{resident_name}_beliefs"}` and `Concept{name: <topic>}`
with topics (`world_safe`, `trust_mayor`, ...) in the EXACT lowercase-
underscore string shape `propositional_deduction._norm_attr` already
normalizes attr names into. **If true**, a THIN bridge — find the Mt by
`f"{entity_name}_beliefs"`, find the Concept by `name==attr` inside it, call
the EXISTING `concept_apply_evidence` — is buildable with ZERO new Rust and
ZERO edits to either facility's own internals, at the cost of being a
NAMING-CONVENTION bridge (works only when the deduction-side entity name and
a CAN-network owner's name coincide), not a general entity-resolution
solution.

**GO bar:** [RUN] a derived fact ("Avery is calm" → MP → `is_a(avery,
world_safe)`) applied through the bridge measurably moves a real CAN
Concept's `external_field`/discrete `state` in the confirmed direction,
different from the no-bridge baseline, on a real network built by the
UNMODIFIED `build_resident_can_mt`.

**What this does NOT establish, registered in advance:** whether any
STANDING caller ever produces both an SmEntity and a same-named CAN network
today (checked: `worlds/bigville_can_beliefs.py`/`bigville_world.py` never
call `situation_model_reader`/`inference_generation` — confirmed by grep,
§0.3). If so, this is a real, working, but not-yet-exercised bridge, exactly
the honest shape `BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md` §8 point 2 already
reported for its own site.

---

## 2. Candidate 2 — Analogical correspondence → CAN hypothesis

**Question, falsifiable, two parts.**

**(2a) Is a `BlobEdge`/`TransferDecode` output a clean seed for a NEW
`knowledge_logical` schema or `causal_influence` coupling?** Structurally: a
`BlobEdge` names a `transform_key` (a canonicalised witness — WHAT stays
fixed between two Concepts) linked `links_a`/`links_b` to two real Concept
nodes. Turning that into an implication hypothesis needs a DIRECTION (which
Concept is antecedent, which is consequent) `BlobEdge`'s own undirected
correspondence does not carry — a real, if small, representational gap,
checked not assumed.

**(2b) The theory-limits doc's own open Q4: does a real populated
`causal_influence` network exhibit LOW-RANK (shared-generator) structure, as
opposed to mere value-alphabet compression?**
(`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §6.4-6.5, ranked item 4 of 5,
explicitly named as blocked for lack of "a real, populated `causal_influence`
network" to test against.) **That network now exists**: `seeds/
bigville_cast100.json` has 100 real residents; `build_resident_can_mt` is
unmodified, callable per-resident, real weights. **Prediction:** the 5×5
per-resident coupling matrices, stacked, do NOT exhibit true low rank in the
Q4 §6.4 sense (a small number of shared latent generators explaining most
coupling variance) — because `STRUCTURAL_EDGES`
(`bigville_can_beliefs.py:61-67`) is a FIXED 5-edge topological template with
only a SMALL per-resident nuance term (`_NUANCE_CLIP=0.15` around a
population mean), which is closer to "one shared structural generator plus
noise" (a rank-1-ish signal) than to a rich multi-generator low-rank
structure — testable directly, not asserted.

**GO bar:** [RUN] build N≥30 real resident networks, extract the (weight)
edge vectors, compute the actual rank/eigenvalue spectrum (via the
implied dense coupling matrix per resident, or the across-resident
edge-value covariance — whichever is the correct object per §6.4's own
definition, resolved in the investigation not asserted here) and report the
real numbers.

**What building an actual bridge needs, sized in advance if (2a)'s gap is
real:** a DIRECTION-INFERENCE step (which endpoint of a `BlobEdge` is
antecedent) — either a new, small Python function reading an existing
asymmetric signal (e.g. `_pair_witness`'s own `name_shared` count as a weak
prior) or new representational work (a directed variant of `BlobEdge`) — not
committed to either without checking `_pair_witness`'s actual output
structure first.

---

## 3. Candidate 3 — CAN coherence → fact

**Question, falsifiable:** does a CAN Concept's settled `state` have a clean
path to becoming a stated predication `ingest_predication` can read the same
way it reads text-derived facts?

**Prediction:** YES, cleanly, because (a) `Resident{name}` sits one hop from
the Mt (`has_belief_mt`) supplying a ready-made entity name (the SAME
`f"{name}_beliefs"` convention candidate 1 uses in reverse), (b) `Concept{name}`
is already the exact attr-name string `ingest_predication`'s `is_a` relation
expects, and (c) `_negate_attr`'s `not_`-prefix convention
(`propositional_deduction.py:310-328`, already mechanically derived for
modus tollens) is the READY-MADE representation for a settled `state==-1`
Concept, requiring no new naming scheme: `state==+1 → is_a(resident,
concept_name)`; `state==-1 → is_a(resident, "not_"+concept_name)`;
`state==0 → no fact (undifferentiated, nothing to assert)`.

**GO bar:** [RUN] a CAN network settled (via the native discrete update or
`mt_relax_to_marginal`) to a real, non-trivial state, converted to
predications via the bridge, ingested via the UNMODIFIED
`ingest_predication`, and a held `knowledge_logical` implication (candidate
1's OR a fresh one) fires a DIFFERENT downstream consequent than it would
starting from an empty situation model — a genuine round-trip, CAN → fact →
deduction → new derived fact.

---

## 4. What will decide which bridge(s) get built

Per the task's own instruction: build the smallest bridge the investigation
finds BOTH genuinely useful and cleanly buildable — possibly only one of the
three, possibly a partial version. Candidates 1 and 3 are, on the reading
above, mechanically symmetric (same naming convention, opposite direction)
and both look buildable with existing primitives and zero new Rust; if both
GO bars are met, BOTH are built (a round-trip demo — CAN settles → fact →
deduction fires → applied back as new CAN evidence — is a strictly stronger,
more informative demonstration than either alone, and costs little more once
the naming-convention plumbing exists). Candidate 2's bridge proper (2a) is
gated on a real, checked design gap (direction inference); if it is not
cleanly closeable within this rung's scope, it is named and sized, not
forced — but 2b (the low-rank measurement) is run regardless, since the task
explicitly asks for it and it needs no bridge to be built to answer.

---

## 5. Regression scope

Files this rung may ADD to (new module(s), new test file(s), new docs) but
will NOT edit the internals of: `domains/propositional_deduction.py`,
`domains/inference_generation.py`, `domains/situation_model_reader.py`,
`domains/analogical_thinking.py`, `seeds/inference_logical.json`,
`seeds/can_native_reimplementation.json`, `seeds/can_decay_identity.json`,
`worlds/bigville_can_beliefs.py`, `runners/dsl/src/can_ops.rs`,
`runners/dsl/src/term.rs`. A `git diff --stat` restricted to this list must
be empty at RESULTS time. Regression suite: `tests/test_deduction_
generalization.py`, `tests/test_deduction_extension.py`,
`tests/test_inference_generation.py`, `tests/test_blob_edge_analogy_
extension.py`, `tests/test_analogical_relative_ranking.py`,
`tests/test_can_native_reimplementation.py`,
`tests/test_bigville_can_integration.py`, `tests/test_can_identity_nudge_
final.py` — run before and after, paired failing-node-id lists if anything
shared regresses.
