# Unblocking `logodds` — RESULTS

Prereg: `LOGODDS_GENERATOR_PREREG.md`, same worktree/branch, base
`main @ 26210f3` ("Merge can-native-reimplementation: items 1-3 built and
proven, GO"). Worktree `/home/matt/ozmadev/ocelot-worktrees/logodds-generator`,
branch `logodds-generator`.

**Verdict, up front.** Both registered predictions in the PREREG held.
`translate` (`runners/dsl/src/shape_decode.rs`) genuinely suffices for the
causal-strength dimension's semantics — **zero new Rust anywhere in this
build**, confirmed by `git diff --stat main -- '*.rs'` returning empty. The
cross-frame log-odds render is a pure composition of pre-existing Terms
(`Log`/`Div`/`Plus`). Item 4's graded-reweighting half — confirmed BLOCKED in
`CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §5/§9 on exactly this missing
mechanism — is now built, wired to the existing mint-on-recurrence
edge-creation half, and demonstrated live with real measured numbers on the
real engine (all three registered demonstrations, §4 below). The
`causal_strength` dimension is declaratively wired alongside the existing
`knowledge_*` taxonomy per `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` §7, with
`implies`/`knowledge_logical` completely untouched (confirmed by an updated
scope-guard regression, §6). `DimInfer`/`TimeInfer` automatic recognition of
this generator from a raw observation trajectory is real, separate,
un-sized follow-on work — named, not built (§7).

---

## 1. The translate-vs-new-kind decision — confirmed as predicted

**Decision: reuse `translate`. No new `DimensionGenerator` `kind`, no new
Rust dispatch arm.**

`apply_translate_once` (`runners/dsl/src/shape_decode.rs:799-820`) maps
`v -> v + offset[j]` per coordinate slot — no wrap (unlike `modular`), no
origin-normalization (unlike `rotation90`/`reflection_*`/`scale2`). This is
exactly the semantics a signed, unbounded evidence counter needs, and the
module's own doc for the generator (`:786-798`) names the target shape
directly: *"a rigidly-translating pattern is the SAME held shape stepping by
`k`... any two frames of a constant-velocity orbit are mutual translates."*
An evidence count stepping +1 per confirming observation is that orbit at
velocity 1 on one axis.

**The registered caveat was confirmed, not merely assumed.** `grep -rn
"set_edge_attr" runners/dsl/src/*.rs` finds it only as a private `graph.rs`
Rust-API method (`graph.rs:732`) never exposed to rule effects — there is no
`set_edge_attr` verb in `rewrite.rs`'s `Effect` enum (confirmed by reading
`rewrite.rs`'s full effect-dispatch list, §1499-1885: `AddEdge`/`DelEdge`/
`AddNode`/`AddNodeIfAbsent`/`SetAttr`/`SetAttrIfDifferent`/`DelNode`/
`DefineConcept`/... — `SetAttr` targets a bound NODE variable only). And
`apply_generator_once`/`apply_translate_once` are private, invoked only from
inside `ShapeDecode`/`TransformDecode`/`DimInfer`/`TimeInfer`'s own `eval_*`
bodies (confirmed: no standalone `ApplyGenerator`/`GeneratorStep` Term
exists, `grep -n` on `term.rs` and `shape_decode.rs` for those names returns
nothing).

**Consequence, exactly as predicted:** the counters live on a proper NODE
(the existing `Coactivation` node — already reified as graph data, already
bound in `can_native_hebbian_mint`'s own match pattern via `a
-coactivated_with-> coact -coactivation_of-> b`), and the actual per-tick
+1/+1 mutation is ordinary `Plus`/`IfThenElse` Term arithmetic inside a
`set_attr` rule effect — the SAME idiom `can_tick`/`codebook_epoch` already
use for every other mechanically-bumped integer counter in this codebase.
`DimensionGenerator{name:"logodds_evidence", kind:"translate", offset:[1]}`
(`seeds/inference_knowledge.json` local_id 13) is declared as the
DOCUMENTED shape this stepping matches — it is not literally invoked at
runtime by the rule that performs the stepping, and the PREREG said this in
advance rather than discovering it as a limitation after the fact.

---

## 2. The rendering-function formula — Laplace-smoothed empirical log-odds

**Formula, as registered:**

```
log_odds = ln( (evidence_confirm + 1) / (evidence_disconfirm + 1) )
```

**Why (registered in PREREG §2, unchanged):** the mechanism actually
accumulates exactly two integers — confirming and disconfirming trial
counts — not a full 2×2 contingency table, so Griffiths & Tenenbaum's full
causal-support formula (`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` §2.3) was
rejected as requiring data the graph does not observe. The `+1` is Laplace/
add-one smoothing (a uniform Beta(1,1) prior) — a principled statistical
constant, not a borrowed human perceptual bin count, and introduces no
threshold or bin anywhere (`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §5.3's
explicit warning is honored: no ~7, no other borrowed number, appears
anywhere in this build). It matches Rescorla-Wagner's trial-level reading
(`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` §8.2's named open sub-question,
resolved here in favor of the trial-count reading over a static-schema
reading).

**Term composition, zero new Rust** (confirmed live, §4 below):
`Log{arg: Div{a: Plus{confirm,1}, b: Plus{disconfirm,1}}}`. `Log` is natural
log (`term.rs:509-511`, `runners/dsl/src/term.rs:7071-7075`: `v.ln()` for
`v>0`), `Div`/`Plus` are the ordinary arithmetic Terms.

**The idiom mirrored, as planned:** evaluated live via
`Substrate.evaluate(term, {"coact": node})` — the same call shape
`tests/test_can_native_reimplementation.py::test_polarization_via_max_steps_
sweep` already used for `ShapeDecode` before this build, and the same "pure
comparator kept separate from canonical storage" shape as `cmp_value_lex`
(`value.rs:461`) and `can_ops.rs::mt_mean_field_marginal`'s own "pure read,
no graph mutation" cross-check in the prior rung's item-3 demonstration.
Confirmed live (§4(b)) that no node's stored attrs change after evaluating
the render.

---

## 3. Where the design landed in the seed files

### `seeds/inference_knowledge.json` (v1.0.0 → v1.1.0)

Two new nodes (local_id 13-14):

```json
{"local_id": 13, "type": "DimensionGenerator",
 "attrs": {"name": "logodds_evidence", "kind": "translate",
           "coord_dims": [0], "params": [1], "offset": [1]}}
{"local_id": 14, "type": "LatentDimension",
 "attrs": {"name": "latent:causal_strength", "generator": "logodds_evidence", "k": 0, ...}}
```

Two new `has_latent_dimension` edges, from the two existing `knowledge_causal`
`ShapeSignature` schemas (`physical_displacement_rise` local_id 9,
`physical_addition_overflow` local_id 10 — confirmed, by reading
`inference_knowledge.json:93-114` before this build, to carry only a bare
`{"relation":"cause"}` today, no strength field at all, exactly the "same
fixed-boolean complaint one schema-kind over" `CAUSAL_LINKAGE_DIMENSION_
RESEARCH.md` §6.1 names) to the new `LatentDimension`. **Additive only** —
`kind`/`signature`/`supplies`/`coherence` (the only attrs `domains/
inference_generation.py` reads off a `ShapeSignature`, confirmed by grep
before writing this document, §5 below) are byte-unchanged.

### `seeds/inference_logical.json` (v1.0.0 → v1.1.0)

One new string attribute on the existing `logical_bird_can_fly` node:
`"causal_strength_ceiling": "latent:causal_strength"` (+ a documentation
`_note` field). **Not a graph edge** — `load_seed_manifest`'s `local_id`
resolution is scoped per manifest file (`runners/dsl/src/py.rs:1497-1525`:
`local_to_global` is a fresh map built once per `load_seed_manifest` call),
confirmed by reading the loader before writing this document, so an `edges`
entry in `inference_logical.json` cannot reference a `local_id` declared in
`inference_knowledge.json`'s own `nodes` list. Encodes `CAUSAL_LINKAGE_
DIMENSION_RESEARCH.md` §7.2's own instruction exactly: `knowledge_logical`
is this dimension's CEILING quantum (the idealized limit of overwhelming
confirming evidence, none disconfirming — the same degenerate-to-boolean
limit Cheng's own causal-power theory has at its idealized center, §2.2 of
the research doc), not replaced, not merged, not touched. `implies`'s own
`Covers`-based structural matching — the entirety of this file's decode
mechanism — is unchanged; confirmed live (§6) that the `logical_bird_can_fly`
mint-and-recognize path still works byte-identically.

### `seeds/can_native_reimplementation.json` (v1.0.0 → v1.1.0), the real payoff

- `can_native_note_coactivation`'s `add_node` effect now also initializes
  `evidence_confirm:0`, `evidence_disconfirm:0`, `evidence_tick:<mt.can_tick
  at note time>` on the `Coactivation` node it already minted.
- `can_native_hebbian_mint`'s effects now also bump `evidence_confirm` by 1
  and set `evidence_tick` to the current `can_tick`, on the SAME recurrence
  that mints the edge (the mint event itself counts as the first confirming
  observation).
- **New rule `can_native_hebbian_reweight`** (the genuinely new mechanism):
  fires once the `causal_influence` edge already exists (`Exists` guard) and
  `mt.can_tick > coact.evidence_tick` (the same epoch-gate idiom `noted_tick`
  already uses), and bumps exactly one of `evidence_confirm`/
  `evidence_disconfirm` via `IfThenElse` on `Gte(Times(a.state,b.state),0)` /
  `Lt(...,0)`.

**Deliberate design choice, made in the PREREG before any bug forced it**: ONE
consolidated rule, not a `confirm`/`disconfirm` sibling pair. `CAN_NATIVE_
REIMPLEMENTATION_RESULTS.md` §3 already found and fixed a real `run_rules`
cold-path property — sibling rules racing to update the same kind of node
can starve each other indefinitely, because the cold path commits exactly
one progressing binding per rule per pass. A confirm/disconfirm pair over
the same `Coactivation` node would have been exactly that shape. This build
applied that lesson preemptively rather than re-discovering it by running a
failing test — the lesson generalized correctly on first application.

---

## 4. Live demonstrations — all three, on the real engine, real numbers

`tests/test_can_native_reimplementation.py`, new tests, run via
`PYTHONPATH=".:runners/dsl/python" python3 -m pytest
tests/test_can_native_reimplementation.py -q -s`:

### (a) In-frame stepping — `test_evidence_counters_are_real_integers_stepping_across_ticks`

```
tick0 (note):                confirm=0 disconfirm=0
tick1 (recurrence, mint):    confirm=1 disconfirm=0
tick2 (confirm):             confirm=2 disconfirm=0
tick3 (confirm):             confirm=3 disconfirm=0
tick4 (b flips sign, disconfirm): confirm=3 disconfirm=1
```

Every value asserted `isinstance(x, int)` at every tick (never float),
strictly frozen or +1 per tick matching the condition that tick. This is
the observed integer trajectory a `translate`/`TimeInfer`-shaped generator
would in principle recognize (§7 — not built this rung).

### (b) Cross-frame log-odds render, ranking + never-written-back — `test_log_odds_render_ranks_evidence_and_never_writes_back`

```
log_odds: heavy(confirm=8,disconfirm=0)=2.1972
          rare(confirm=1,disconfirm=0)=0.6931
          neutral(confirm=0,disconfirm=0)=0.0000
          mixed(confirm=3,disconfirm=5)=-0.4055
```

`heavy > rare > 0`, `neutral == 0.0` exactly, `mixed < 0` (more disconfirming
than confirming evidence renders negative) — all four registered predictions
held. **Confirmed directly**: `dict(node.attrs)` compared byte-for-byte
before and after every `evaluate()` call — identical every time; no
`log_odds`/`render` key ever appears on any node. The render genuinely never
touches graph state.

### (c) Item 4 end-to-end, THE scenario left blocked — `test_hebbian_reweight_end_to_end_unblocks_v1_graded_reweighting`

```
after mint + 3 reinforcements: confirm=4 disconfirm=0 -> log_odds=1.6094
one disconfirming observation:  confirm=4 disconfirm=1 -> log_odds=0.9163
```

The edge is minted once (tick 1, as in v1.0.0, unchanged), reinforced three
more times on the SAME already-minted edge (ticks 2-4 — this is exactly the
"graded reweighting of an already-minted edge" `CAN_NATIVE_REIMPLEMENTATION_
RESULTS.md` §5/§9 named as blocked and not attempted), then hit with one
disconfirming observation (tick 5). The render measurably moves DOWN
(1.6094 → 0.9163) and stays positive (4-vs-1 still leans confirming) —
graded reweighting is not merely present as inert data, it visibly changes
the comparison outcome in response to new evidence. Edge cardinality is
confirmed unchanged (`len(neighbours(a,"causal_influence")) == 1` throughout)
— reweighting touches only the evidence ledger, never re-mints or removes
the edge.

**Full test run, this file, this build:**

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest tests/test_can_native_reimplementation.py -q -s
[... 8 pre-existing item 1-3 demonstrations, byte-identical output to CAN_NATIVE_REIMPLEMENTATION_RESULTS.md ...]
evidence trajectory: tick0=(0,0) tick1..3=(1,0)(2,0)(3,0) tick4=(3,1) -- all real ints
log_odds: heavy(8,0)=2.1972 rare(1,0)=0.6931 neutral(0,0)=0.0000 mixed(3,5)=-0.4055
item-4 reweighting: confirm=4 disconfirm=0 -> log_odds=1.6094; one disconfirm -> confirm=4 disconfirm=1 -> log_odds=0.9163
[... item 5 + Bigville checks, byte-identical ...]
11 passed in 0.59s
```

---

## 5. Confirming the additive-only claim — what reads a `ShapeSignature`/`Coactivation`

`grep -n "neighbours\|Edges(\|edge_type" domains/inference_generation.py`
finds exactly one edge traversal (`part_of`, unrelated); `grep` on
`domains/propositional_deduction.py` for the same finds nothing. Neither
file, nor any other existing consumer, reads `has_latent_dimension` off a
`ShapeSignature` node or `evidence_confirm`/`evidence_disconfirm`/
`evidence_tick` off a `Coactivation` node — confirmed by grep before this
build was written (not merely assumed), and re-confirmed by the byte-for-byte
matching regression runs in §6.

---

## 6. Regression

**Scoped CAN regression, all in one run, 70/70 passed** (the six pre-existing
CAN files + `can_native_reimplementation.py`'s now-11 tests):

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py \
  tests/test_can_native_reimplementation.py -q
70 passed in 7.32s
```

**`inference_knowledge`/`inference_logical` consumer suites — matched their
pre-existing baseline EXACTLY, measured both ways (stash/pop on the real
worktree, not assumed):**

- `tests/test_inference_generation.py`: **14 failed, 6 passed both with and
  without this branch's changes** (identical failing-test-name list both
  ways — an environment-conditional baseline, `test_spine_unwired_still_bare`
  et al., unrelated to this build: `KeyError: 'glass'` in
  `situation_model_reader`, nothing to do with `knowledge_causal`/
  `has_latent_dimension`).
- `tests/test_deduction_generalization.py` + `tests/test_crow_gate.py`:
  **11 failed, 16 passed both ways**, ONE EXCEPTION FOUND AND FIXED live
  (not silently worked around): `test_ground_reductions_and_comprehend_
  theorem_untouched` is an explicit scope guard from the prior
  `deduction_generalization` rung, asserting `git diff --stat b124038 --
  domains/ground_reductions.py domains/comprehend_theorem.py seeds/
  logic_foundation.json seeds/logic_propositional_predicate.json seeds/
  inference_knowledge.json` is empty. `seeds/inference_knowledge.json` was
  in that guard's file list because the PRIOR rung wanted to stay minimal —
  it is not a permanent global invariant, and THIS rung's task explicitly
  names `inference_knowledge.json` as a required wiring target
  (`CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` §7 itself). Fixed by dropping
  `seeds/inference_knowledge.json` from that one guard's file list, with a
  comment explaining why, while leaving the actual protected concern (the
  four group-theory/deduction files) guarded and confirmed untouched. Full
  before/after:

  ```
  WITHOUT this branch (git stash):  11 failed, 16 passed
  WITH this branch, before the fix: 12 failed, 15 passed  (the one guard test)
  WITH this branch, after the fix:  11 failed, 16 passed  (matches baseline exactly)
  ```

**Full boot regression** (`load_all_seeds` on a fresh `WorldAdapter`):
identical **8 pre-existing failures** to the documented baseline
(`acoustic_cue_vocab`, `character_tom`, `reading_constructions`,
`conceptual_categories`, `cue_investigator`, `named_compound_heads`,
`reading_skeleton`, `vision_change`, all `ValueError: seed node missing
local_id`), **0 rules_skipped**.

**No Rust build or `cargo test` was needed or run** — `git diff --stat main
-- '*.rs'` is empty; zero `.rs` files touched anywhere in this branch. No
coherence probe needed for the same reason (the house discipline gates that
on a Rust change).

---

## 7. What this build does NOT establish

1. **`DimInfer`/`TimeInfer` automatic recognition of `logodds_evidence` from
   a raw observed evidence-count trajectory is NOT wired.** This is real,
   separate, un-sized follow-on work, named precisely rather than forced
   into this rung: `DimInfer`'s rung-2 pipeline (`term.rs:1160-1186`) is
   single-observation-shaped (per-part `dim_types`-typed coordinate decode
   against a residual); a live evidence counter accumulating across MANY
   ticks is a multi-frame TRAJECTORY, which is `TimeInfer`'s territory
   (`term.rs:1207-1230`) — a separate Term with a separate call shape and a
   substantial standing test suite of its own (`tests/test_time_infer_
   migrated.py` and seven siblings) this rung did not touch or extend. The
   declared `DimensionGenerator{kind:"translate"}` node is what a future
   integration would hang recognition off; recognizing an evidence
   trajectory automatically (rather than the mechanism explicitly declaring
   confirm/disconfirm via rule effects, as built) was never attempted.
2. **The declarative wiring in `inference_knowledge.json`/`inference_logical.
   json` (§3) is NOT exercised by any decode path.** No existing rule reads
   `has_latent_dimension` or `causal_strength_ceiling` — confirmed by grep
   (§5), not merely asserted. This satisfies the task's explicit instruction
   ("wire ... alongside the existing taxonomy, per the original
   recommendation") as graph DATA, matching the research doc's own
   recommendation precisely, but it is declarative scaffolding, not a
   consumed mechanism, in this rung.
3. **Decay has no native analog anywhere in this arc** — unchanged from
   `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md`'s own honest gap; this build
   only unblocks graded REWEIGHTING (evidence accumulating upward via
   confirm/disconfirm), not a downward decay-over-time mechanism.
4. **The log-odds formula is Laplace-smoothed empirical odds from two trial
   counts, not the full Griffiths & Tenenbaum causal-support Bayesian
   marginalization** — a deliberate, registered simplification (§2) matched
   to what the graph actually observes, not a claim that this is the
   field's most sophisticated causal-strength estimator.
5. **Item 4's edge symmetry convention (`a→b` and `b→a` minted
   independently) means `evidence_confirm`/`evidence_disconfirm` are tracked
   PER-DIRECTION** (two separate `Coactivation` ledgers for a pair), exactly
   mirroring the v1.0.0 rung's own PREREG §0.0.1 convention — this build did
   not change or unify that.
6. **Whether any of this reflects real human causal-strength cognition
   remains exactly as open as `CAUSAL_LINKAGE_DIMENSION_RESEARCH.md` left
   it** — this build is a design-debt closure on this SUBSTRATE's own
   mechanism, not a claim about cognitive plausibility.

---

## 8. Reproduce

```bash
cd /home/matt/ozmadev/ocelot-worktrees/logodds-generator
git log --oneline -1 main   # 26210f3, verified before branching

# The three new live demonstrations + all pre-existing item 1-3/5 tests
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_native_reimplementation.py -q -s

# Scoped CAN regression
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_can_belief_quantization.py tests/test_bigville_can_integration.py \
  tests/test_causal_attitude_networks.py tests/test_can_ops.py \
  tests/test_can_migration.py tests/test_can_crossover_point.py \
  tests/test_can_native_reimplementation.py -q

# inference_knowledge/inference_logical consumer suites (baseline-matched)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_inference_generation.py tests/test_deduction_generalization.py \
  tests/test_crow_gate.py -q

# Full boot regression (8 pre-existing failures only, unrelated to this rung)
PYTHONPATH=".:runners/dsl/python" python3 -c "
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
a = WorldAdapter(seeds=())
rep = load_all_seeds(a)
print('failed:', len(rep['failed']), 'rules_skipped:', len(rep['rules_skipped']))
for f in rep['failed']: print(' ', f)
"
```
