# Stage A — non-mutating proposal construction, and the merge relation it needed

**Status: implemented behind a flag, default OFF, and FALSIFIED by the full bench (§5f). It is
byte-identical on four workloads and wrong on a fifth, for a reason no write-set compatibility
relation can detect. The flag should not be enabled and the approach needs read sets.** This executes Stage A of `DECISION_LAYER_PREREG.md` and reports
against the measurements that prereg fixed in advance.

## 0. Result in one line

Stage A derives every binding of a drain against one immutable base and applies the resulting
proposals at a single boundary. Getting there needed two things the prereg did not anticipate:
a proposal must carry a conditional effect's **condition** rather than the answer that condition
happened to have during derivation, and a drain must be checked for **joint applicability**
before its proposals are treated as independent.

**Read §5c and §5d before reusing any of this.** Three separate defects in this rung — the
original flattening of `AddNodeIfAbsent`, a plausible-looking refinement of the merge relation,
and an unsound version of that relation that missed 35 of 49 known divergences — **passed every
suite in both modes**. What caught each of them was a purpose-built falsifier or a direct
soundness measurement. The bench cannot certify this change; that is the most transferable thing
the rung established.

> **CORRECTION, same session, before any downstream use.** The first version of this document
> concluded the opposite: that Stage A produced a duplicate-concept regression, that same-round
> visibility "was the dedup", and that *"the merge-incompatibility relation Stage A explicitly
> deferred is not optional."* **That was wrong, and it was wrong because the defect was mine,
> not the stage's.** `capture()` reconstructed the forward delta from the undo log, and
> `AddNodeIfAbsent` and `AddNode` both emit `UndoStep::AddedNode` — so a *conditional* insert
> was silently flattened into an unconditional one. All three `Concept`-minting rules in the
> corpus use `add_node_if_absent`. With the condition preserved and re-checked at commit, the
> delta is empty. The wrong conclusion is left here rather than edited away because it is the
> more instructive half: a plausible architectural verdict ("the theory's deferred machinery is
> load-bearing") was reached from what was actually a one-line loss of information in an
> instrument.

## 1. Two prereg assumptions that measurement falsified before any code was written

**(a) The prereg cited an applier the engine does not run.** §A.1 names `rewrite.rs:2196-2207`
as *the* mutate-during-derivation site. There are **two** appliers. An instrument placed at the
prereg's own citation recorded **zero** events on a workload `scale_audit` said had **401**.
The live one is the drain loop in `Substrate` (`substrate.rs`), which the prereg never
mentions. A Stage A built to the document's citation would have rebuilt a path that does not
execute — and would have passed its own tests.

**(b) The correctness premise is false as stated.** Bindings are all collected *before* any
apply, so enumeration already reads an unmutated graph. Measuring the rest — whole-graph
fingerprint before the speculative apply, again after the undo:

```
probes checked : 401        (matches scale_audit's count exactly: full coverage)
probes dirty   : 0
dirty rules    : []
```

**Apply-then-undo is wasteful, not wrong.** And it is exact for a structural reason rather
than by luck: `UndoStep::NodeDeleted` is the one step undo cannot reverse, and a firing that
deletes a node *reports progress*, so it is never the firing that gets rolled back.

So Stage A cannot be justified as a correctness fix. What remains is the proposal-as-value
(which Stage B needs) and the removal of wasted work.

## 2. What actually mutates during derivation

Narrower than the prereg claimed, and never named in it: the drain applies **every**
progressing binding without breaking, so binding N+1's effect terms evaluate against binding
N's committed writes.

Measured population — rules committing ≥2 bindings in one drain:

```
multi-binding drains : 27
distinct rules       : 11        (prereg NO-GO is >20 — not triggered)
```

| bindings | rule |
|---|---|
| 6316 | `curiosity_targets_ambivalent_nodes` |
| 64 | `bind_boot_anomaly_evidence` |
| 15 | `slang_variant_bind_denotes` |
| 13 | `wire_word_faculty` |
| 11 | `rule_mention_resolves_to_concept` |
| 11 | `rule_intent_about_mentioned_concept` |
| 8 | `assess_compromised_boot` |
| 7 | `retire_duplicate_gap` |
| 5 | `reply_to_adjacency_pair` |
| 5 | `rule_intent_from_no_claim` |
| 4 | `comprehend_familiar` |

## 3. What was built

`runners/dsl/src/stage_a.rs`: a `Proposal` of resolved `Write`s, `capture()` and `commit()`,
wired into the drain behind `stage_a_enable`.

The delta carrier is `UndoStep`, exactly as §A.2 predicted — *"closer to keeping something
already built than to building it."* `undo` is in application order, so walking it **forwards**
while reading the graph as it currently stands reconstructs what the firing did: the inverse of
the inverse. The engine had already computed the forward delta on the probe path and thrown it
away.

Writes are **concrete** — Terms already evaluated — so replay cannot observe the graph it lands
on. That is what makes it a proposal rather than a deferred re-execution. Nodes minted inside a
firing are referenced by proposal-local `Slot`, because the derivation-time NodeID is freed by
the undo and may be reissued.

**The exclusion is principled, not convenient.** Deriving against one base means undoing the
*progressing* firings too, and undo cannot restore a deleted node. Rules whose effects can
delete a node therefore keep the committed semantics and are **counted, never silently
skipped** — 1,015 drains excluded on this workload, 44 such rules in the seed corpus, all
pruning/retirement.

```
proposals derived : 6,654
writes captured   : 7,132
drains excluded   : 1,015
```

## 4. The gates

**Regression (non-negotiable, §A.3.1).** Rust lib suite **787 passed, 0 failed** with the flag
off, and the Python guard slice **60 passed** (gap-awareness, elaboration, topic-route/self-heal,
quanta navigation, dimension inference, transform decode — 14m32s). (The doctest target fails on three pre-existing `E0425` doctests — `auditory_cortex`,
`ink_topology`, `h265_transcode_driver` — in modules this work never touched.)

**Byte-identity with the flag off.** Two independent processes, identical: 24,597 nodes /
22,345 edges, identical row multisets, and `stage_a_stats` reports zero activity.

**A second instrument error, recorded because it reached this document.** The node types in
the two tables below were first reported as `C` and `S`. Those are not types — the analysis
script indexed `p[0][0]` on a row whose `p[0]` is already the type string, so it printed the
first CHARACTER. The real types are `Concept` and `SystemModel`. The row *counts* and the
delta were unaffected; only the labels were wrong, and they were wrong in a way that reads
perfectly plausibly, which is why it survived until a follow-up query returned zero nodes of
type `C`.

**A measurement trap worth recording.** The first three attempts at this gate all reported
"UNSTABLE", including one using the engine's own `state_fingerprint`. The baseline is
deterministic; the *instrument* was not. Cause: nodes of type `SystemModel` record `ts` (wall-clock)
and `runtime_s`, so no whole-graph hash can ever be run-stable. Excluding those two keys, off==off
is exact. **A side finding that outlives this rung: opt-in cycle detection compares whole-graph
fingerprints, so any rule writing a timestamp defeats it — a cycle can never be detected in a
graph that records the time.**

**Semantic delta (§A.3.2): none.**

```
nodes off/on : 24597 / 24597
edges off/on : 22345 / 22345
off vs on    : IDENTICAL
```

Stage A is genuinely doing the work rather than silently inert — 6,656 proposals, 7,134 writes,
1,015 drains excluded — and the graph it produces is indistinguishable from the committed
engine's.

Before the conditionality fix the delta was three rows: 1 × `Concept{name: friend,
familiar: 1.0}` became 2 × `Concept{name: friend}` with no `familiar`. That is what a flattened
`AddNodeIfAbsent` looks like from the outside, and it is recorded here because it is the
falsifier that found the bug.

**Suite gate in BOTH modes.** The 60-test Python slice passes with `OZMA_STAGE_A=1` as well as
without (14m30s each). The env default was verified to actually arm the mode — 6,493 proposals
with it set, 0 without — because a suite that passes because the flag never engaged is the
inert-instrument failure this session has already hit twice.

## 5. The load-bearing idea: a proposal carries conditions, not answers

`AddNodeIfAbsent` asks a question **about the graph the write lands on**. Answering it while
deriving — against a base that does not yet contain the sibling proposals about to be applied —
answers a different question. So the proposal carries the dedup key set and the check runs at
commit, with the effect's own subset semantics.

That generalises past this one effect, and it is the actual content of "non-mutating proposal
construction": a proposal is not a record of what happened during a speculative apply, it is a
description of what should happen when applied. Any effect whose behaviour depends on graph
state at write time has to keep that dependence.

`SetAttrIfDifferent` (238 uses) was checked against the same argument and is **safe to flatten**
for a different reason: its condition affects only whether progress and an undo step are
recorded, not the resulting value, so replaying it as an unconditional write reaches the same
state.

## 5b. Cross-workload measurement — and the NO-GO fires

The conversation result alone was thin, so Stage A was measured on four workloads, and the
prereg's actual NO-GO quantity was measured rather than proxied.

**First, the proxy is not the gate.** The at-risk instrument counts rules committing ≥2
bindings in one drain — an UPPER BOUND, since two bindings may touch disjoint state. Quoting it
as the gate's quantity would be the same category error as quoting a tie *count* as a defect
count. So `stage_a` gained a **compare mode**: derive every binding against the base, undo, then
run the committed path and diff the two write lists, recording divergences **by rule name**. The
committed result is what stays in the graph, so compare mode changes no behaviour.

At-risk (upper bound) vs actually diverging, embodied: **33 → 13.**

| workload | compared drains | diverged | diverging rules |
|---|---|---|---|
| conversation | 412,571 | 187 | 8 |
| spatial (ls20 + quanta) | 484,647 | 351 | 3 |
| ARC | 14,734 | **0** | 0 |
| embodied | 81,956 | 49 | 13 |
| **total** | **993,908** | **587** | **24 distinct** |

**24 > 20. `DECISION_LAYER_PREREG.md` §A.4's second NO-GO is triggered on its own stated
quantity — "more than 20 rules whose behaviour changes" — and Stage A therefore does not
proceed to being enabled.** The prereg's remedy for exactly this case is that the change "is a
seed-corpus migration wearing an engine change's clothes, and it needs its own prereg".

**The evidence under the gate, reported next to it rather than instead of it.** Divergence is
0.0591% of drains, and *nothing observable moved anywhere*:

- conversation graph **byte-identical** (24,597 nodes / 22,345 edges) — despite 8 rules
  diverging on that very workload;
- spatial 25/25 in both modes; ARC identical 24-node-id failure set; embodied identical
  1-node-id failure set.

That combination is the interesting finding: **write lists differ per drain while the fixpoint
converges to the same graph.** A divergence in one pass is absorbed by a later one — the
`run_rules` fixpoint is, on these workloads, confluent with respect to this change. Drain-level
divergence is not fixpoint-level divergence, and only the latter is behaviour.

So the gate fires on a real quantity, and the rationale behind the gate — that this is really a
seed-corpus migration — is *not* borne out by any observable. Both stand. The gate is honoured
anyway: it was written before the numbers were known, which is the whole point of writing it
then, and 24 rules across four workloads is a genuine reach into the seed corpus even if the
fixpoint currently absorbs it. What it needs is its own prereg naming those 24 rules, not a
judgement call made now with the answer in hand.

## 5c. The residual, explained — and it is not benign

A divergence count is not a verdict; it is a residual to decode. `stage_a` gained a sample
capture (up to three worked examples per diverging rule, both write lists verbatim), and the
587 divergences resolve into **exactly two shapes**.

**Shape 1 — idempotent superset (16 of 21 samples).** Stage A emits MORE than committed: more
firings (`2 vs 1`), or more writes within a firing (`[AddEdge, AddEdge, SetAttr]` vs
`[AddEdge, SetAttr]`). The committed path suppresses writes a sibling binding already made,
because it recomputes progress with those writes visible. Stage A recomputes progress against
the base, so it re-emits them. **The repeats land idempotently** — an edge that already exists,
an attr already at that value — so the graph is unaffected. This shape is genuinely benign, and
it is most of the residual.

**Shape 2 — intra-drain accumulation (5 of 21 samples). This one is real.** The tell is a value
sequence:

```
committed : SetAttr node 893 key 2715 -> 2.0, 3.0, 4.0, 5.0
stage_a   : SetAttr node 893 key 2715 -> 1.0            (only)
```

These rules **fold over their own binding set**: each binding reads what the previous one wrote
and adds to it. Same pattern in `ept_extend_path_with_compatible_verified_transition`
(`Int(1)` vs `Int(2),(3),(4)`) and `adaptive_control_assign_discounted_credit` (`2.0` vs `3.0`).
Deriving every binding against one base makes them all compute the same increment.

**It does not converge.** Minimal reproduction — one counter node, N items, one rule that marks
an item seen and increments the total:

```
items= 5   OFF total=5.0   steps=1      ON total=1.0   steps=1      TOTAL DIFFERS
items=20   OFF total=20.0  steps=1      ON total=1.0   steps=1      TOTAL DIFFERS
```

The `seen` guard means each binding fires exactly once, so there is no later pass for the
fixpoint to accumulate in. **Stage A silently under-counts every fold-over-bindings rule**, and
`steps` is identical, so nothing in the iteration profile signals it.

### Why every gate above still passed

This is the part worth keeping. The conversation graph was byte-identical, four suites'
outcomes were identical, and suite-level iteration counters matched to the digit
(epochs 351 = 351) — because **no exercised test asserts an accumulated total**. The defect is
real, non-converging, and *invisible to the entire bench*. A regression suite agreeing in both
modes was not evidence of semantic neutrality; it was evidence about what the suite measures.

### What this vindicates, and on what grounds

The first version of this document concluded that the theory's deferred machinery was not
optional. That conclusion was **retracted** because the evidence for it — duplicate concepts —
turned out to be a bug in `capture()` flattening `AddNodeIfAbsent`. The conclusion is now
reinstated on **different and firmer grounds**: an accumulator is a genuine *dependency between
bindings*, and Stage A erases it. That is precisely what "monotone positive accumulation" and
stratification exist to represent. The instinct was right; the first reason for it was not, and
the distinction matters because a right answer held for a wrong reason cannot be checked.

**Consequence for the NO-GO.** The gate fired on 24 rules and is honoured — but the count was
never the point. The population that matters is the fold-over-bindings subset, and identifying
*which* of the 24 accumulate is the concrete next measurement, not a broader sweep.

## 5d. The merge incompatibility relation — built, and it makes Stage A sound

The residual named its own fix. Shape 2 is two proposals disagreeing about one location because
each was derived blind to the other; that is **exactly the merge incompatibility relation** v22
asks for, and it does not need the static analysis §5c used to find it.

`stage_a::conflicts` asks whether a drain's independently derived proposals write the same place
twice. If they do, the set is not jointly applicable and the drain **falls back to the committed
sequential path**. The engine declines to treat the bindings as independent rather than silently
getting them wrong. Detecting it on the derived proposals beats detecting it on the rule: it asks
what the bindings actually did on this graph, not what the rule might do on some graph.

The drain now derives the whole binding set against the untouched base, undoes, checks joint
applicability, and either commits the set at one boundary or defers to the sequential path.

**Result — the shape-2 falsifier is closed:**

```
items= 5   OFF total=5.0   ON total=5.0    SAME TOTAL
items=20   OFF total=20.0  ON total=20.0   SAME TOTAL
```

| workload | proposals | conflict fallbacks | del_node exclusions | outcomes |
|---|---|---|---|---|
| conversation | — | — | — | graph **byte-identical** |
| spatial | 976,924 | 350 | 77,023 | failure set identical |
| ARC | 39 | 0 | 494 | failure set identical |
| embodied | 1,793 | 14 | 3,649 | failure set identical |

Rust lib suite 787/787. The guard is doing real work rather than being vacuous — 350 fallbacks
on spatial against the 351 drains compare mode had measured as diverging.

### The relation was UNSOUND on attributes, and a close number hid it

`350 fallbacks` against `351 diverged drains` looked like agreement. It was not: the two sets
are not nested, and reading a near-equal pair as containment is exactly the mistake this
document keeps finding elsewhere. Measured directly — diverged drains the guard did NOT flag,
i.e. cases Stage A would have committed while wrong:

| workload | diverged | **unsound** |
|---|---|---|
| spatial | 351 | 1 (`qf_mint_hyp`) |
| embodied | 49 | **35** |
| ARC | 0 | 0 |

The attribute-keyed relation caught 14 of 49 on embodied. The 35 it missed are the
"2 firings vs 1" shape: a binding that progresses against the base but would NOT have progressed
once a sibling's writes landed. Its extra writes need not touch the same *attribute* as anything
else, so an attribute check cannot see it — while the graph gains work the committed engine never
did. **Every suite still reported identical failure sets throughout**, because none of them assert
those outcomes. Third time in this rung that suite agreement was evidence about the suite.

**The sound relation is pairwise NODE disjointness.** What those cases share is a node: the
bindings of a drain fan out from a hub and every proposal touches it. Two proposals touching any
node in common are not independent, because either one's writes may change whether the other still
applies. Freshly minted nodes are private to their proposal and are excluded.

| workload | diverged | unsound | proposals committed | fallbacks |
|---|---|---|---|---|
| spatial | 351 | **0** | 976,924 | 351 |
| embodied | 49 | **0** | 1,793 | 85 |
| ARC | 0 | **0** | 39 | 0 |

Sound on ~580,000 compared drains, and **not vacuous** — a relation that refused everything would
also score zero unsound, so coverage is reported next to it. On spatial the fallback count now
equals the divergence count exactly; on embodied it is conservative by design (85 ≥ 49).

Conversation graph byte-identical (24,599 nodes / 22,345 edges). Rust lib suite 787/787.

### A wrong refinement, caught by keeping the falsifier

The relation keys on **location alone**. The obvious refinement — conflict only when the same
location gets a *different* value, since identical writes are an idempotent repeat — was
implemented, and it **broke the accumulator falsifier immediately** (20 → 1 again).

The reason is worth keeping: in a fold, every binding reads the same stale base, so they all
compute the **same** value. Identical values are the *symptom* of the accumulator, not evidence
against it. The benign idempotent-superset shape and the harmful fold are **indistinguishable by
value equality**, so the relation must stay on location. It costs conservatism — 350 fallbacks on
spatial where some were benign — and conservatism is the correct trade for a relation whose job
is to refuse when it cannot tell.

This near-miss survived only because the minimal repro from §5c was kept and re-run after the
refinement. A suite-level gate would not have caught it: all four workloads still reported
identical outcomes with the broken relation in place.

## 5e. How the full-bench result will be read — fixed BEFORE it landed

The full migrated bench is running in both modes (`-k migrated -n 6`; `-n auto` has been
measured to OOM this box). Written now, with the run in flight and the answer unknown, because
this rung has already produced three defects that every suite passed — so the temptation to read
whatever comes back as confirmation is the specific risk here.

- **Identical failure sets.** This is the WEAKEST of the three outcomes, not the strongest. It
  would establish that Stage A changes nothing the bench asserts. It would NOT establish
  semantic equivalence: the original `AddNodeIfAbsent` flattening, the broken value-aware
  relation, and the unsound attribute-keyed relation each produced identical failure sets on
  every workload tried, while being wrong. The correct claim would be "no bench-visible
  difference across ~8000 tests", and that is a statement about coverage.
- **ON has failures OFF does not.** Stage A is wrong on a path the targeted workloads never
  exercised. The failing node ids are the enumeration, and each is a falsifier to reproduce
  minimally — the accumulator repro is the template.
- **OFF has failures ON does not.** Not a win. It means the committed engine depends on
  same-round visibility somewhere the guard now refuses, and the guard's conservatism has cost
  real behaviour. That needs the same investigation as the opposite case.

**What no outcome licenses: flipping the default.** The prereg's NO-GO (24 rules diverging,
>20) is triggered and stands on its own terms. A green bench removes one objection; it does not
retire a gate that was written before the numbers were known.

## 5f. FULL BENCH: Stage A is falsified, and the compatibility relation is structurally insufficient

Both modes, `-k migrated -n 6`, same tree, same selection:

| mode | failed | passed | errors | unique entries | wall |
|---|---|---|---|---|---|
| OFF | 149 | 7847 | 498 | 282 | 3:05:59 |
| ON | **151** | 7845 | 498 | **284** | 3:10:13 |

**FAILURE SETS DIFFER.** Two tests fail only with Stage A on, both in
`tests/test_parallax_efference_migrated.py`, and both reproduce in isolation (OFF 7 passed;
ON 2 failed, 5 passed):

```
test_armed_is_load_bearing_and_refuses_the_chosen_fixation
test_dead_control_arming_on_the_estimated_dominant_does_NOT_move
```

The assertion: the dominant vector still matches, but a motion object of extent **108 collapses
to 3**.

### The cause, and why the guard could never have caught it

`seeds/vision_motion_group.json::mo_flood`:

```
match:   [["field", "has_cell", "R"]]
effect:  set_attr R mlabel = Attr(Argmin(Filter(Neighbours(R, ...))))
```

Label propagation. Committed, cell N reads labels that earlier cells **in the same drain**
already wrote, so a flood crosses the field in one drain. Under Stage A every cell reads the
base, so it advances exactly **one hop per pass**. `mo_mint` counts cells sharing a label, so an
under-propagated flood mints a 3-cell object where the committed engine mints 108.

Now the structural point:

- each proposal WRITES a different cell's `mlabel` — the proposals are **write-disjoint**;
- each proposal READS its neighbours' `mlabel` — the proposals are **read-dependent**.

`stage_a::conflicts` compares **write sets**. It is blind to a read-write dependency by
construction, and no refinement of a write-set relation can see one. The three earlier workloads
passed because their assertions tolerate slower propagation; this file's do not, because
`mo_mint` snapshots the flood mid-way.

**So the relation is not merely conservative-in-the-wrong-places — it is incomplete in kind.** A
sound compatibility relation needs each proposal's READ set, and `capture()` records only writes.
Obtaining read sets means instrumenting every graph read during effect-term evaluation, which is
a substantially larger change than anything in this rung and touches the hottest path in the
engine.

### Re-confirmed against the current relation

The full bench ran on the binary built BEFORE the write-set relation was strengthened to node
disjointness (`.so` timestamped after the run finished), so the falsification was initially
measured against the weaker relation. Re-run afterwards on the current binary:

```
2 failed, 5 passed in 777.20s
  test_armed_is_load_bearing_and_refuses_the_chosen_fixation
  test_dead_control_arming_on_the_estimated_dominant_does_NOT_move
```

**Identical failures.** As expected but now measured: node disjointness is still a *write-set*
relation, and `mo_flood`'s proposals each write a different cell while reading their neighbours.
No strengthening of a write-set relation reaches this.

### What this settles

- **Stage A as built is falsified.** Not by the count of diverging rules, but by a concrete
  observable: a wrong object extent, reproducible in 8 minutes.
- **The prereg's NO-GO is vindicated in substance, not just in letter.** It fired at 24 rules;
  the reason it should have fired is this.
- **Floods are not a corner case in this substrate.** `mo_flood`, `qf_relax`, `mv_relax` are the
  same shape, and label/distance propagation is how this engine does spatial reasoning. Any
  scheme that derives a drain against a frozen base slows every flood to one hop per pass.
- **The four-workload sweep was not enough, and said so at the time.** §5e recorded before the
  run that identical failure sets would be the weakest outcome. The run did not even deliver
  that.

## 5g. THE FALSIFIER IS CLOSED — by REFUSING the rules, not by deciding them

§5f settled that `stage_a::conflicts` "is incomplete in kind": it compares write sets, `mo_flood`'s
proposals are write-disjoint and read-dependent, and **no refinement of a write-set relation can
see one**. That stands. What it does not follow from is the remedy §5f then reached for — "a sound
compatibility relation needs each proposal's READ set", requiring instrumentation of every graph
read during effect evaluation, "the hottest path in the engine".

**Stage A does not have to DECIDE these rules. It only has to REFUSE them** — and refusing needs no
instrumentation at all, because the dependency is already visible in the rule's own Term tree.

`rule_is_derivable` now excludes, in addition to node deletion, **any rule whose own READ set and
WRITE set intersect** — using `RewriteRule::derive_access`'s existing static, over-approximated
sets rather than a fresh walk. (A first cut hand-rolled the walk over effect args only, and was
strictly weaker: it missed a WHERE-CLAUSE read of a key an effect writes, which is just as much a
read-write dependency, because under Stage A every binding evaluates its guard against the base
too. It also ignored `reads_any`/`writes_any`, the conservative "reads something opaque" flags,
either of which means the sets cannot be trusted.)

**§5f's "read sets require instrumenting the hottest path" is true of PER-PROPOSAL read sets, and
this engine already carries a PER-RULE one for free.** `derive_access` computes `read_set` /
`write_set` for the batch-apply and write-set-dirtying slice, on every rule the engine installs.
Nothing had connected it to Stage A.

Both divergence shapes reduce to that one predicate:

| shape | reads the key it writes | example |
|---|---|---|
| PROPAGATION (§5f) | off ANOTHER node — a neighbour, another bound var | `mo_flood`, `qf_relax` |
| FOLD (§5c, "this one is real") | off the SAME node, across bindings | `adaptive_control_assign_discounted_credit`, `ept_extend_path_with_compatible_verified_transition` |

**The refusal is much broader than first reported, and the number is worth having exactly.** An
earlier draft of this section said 14.7% of seed rules. That figure counted only reads inside
EFFECT ARGS; the engine's own `read_set` also includes the WHERE clause, and a guard that reads the
key an effect writes is just as much a dependency. Recounted against the predicate as implemented:

| | rules | share |
|---|---|---|
| genuine read-write dependency | 1637 | **43.5%** |
| opaque read only (`reads_any`: `TypeOf`, `AttrByName`, `EvalSubgraph`, `any_type` walks) | 34 | 0.9% |
| **refused** | **1643** | **43.7%** |
| still available to Stage B | 2121 | 56.3% |

Two things follow, and the second is the more interesting.

**The refusal is not conservatism.** Under 1% of it is "the read set cannot be trusted"; over 99%
is a dependency actually present in the rule. Tightening the analysis would buy almost nothing.

**Nearly half this substrate's rules read what they write** — which is §5f's own claim ("floods are
not a corner case in this substrate; label/distance propagation is how this engine does spatial
reasoning") stated as a measurement rather than an impression. 30 seeds are refused ENTIRELY,
including `vision_eye` (27/27), `embodied_adaptation`, `aerial_adaptation`, `capability_graph` and
`vision_waves`. **Stage B would be blind to those subsystems**, and that is the real price of
Stage A, not the runtime overhead — which §6 already measured at nothing.

Every rule this document names that lives in a seed is among the refused, all four checked
explicitly.

*The rule figures above are a static mirror of the predicate computed from the seed JSON, not the
engine's own count; the drain figures below are the engine's, read from `stage_a_stats()`.*
The intersection is taken over ALL key kinds, not just attributes, because the same argument
applies to structure: **95 seed rules (2.5%) MATCH and ADD the same edge type**, which is
transitive closure, and under Stage A each binding reads the base — one hop per pass, the flood's
failure exactly. Widening from attributes-only to the full intersection costs 1.3 points of
runtime refusal and covers that shape.

What matters at runtime is DRAINS, not rules, and `stage_a_stats()` reports it:

| predicate | drains refused | still speculated |
|---|---|---|
| attribute keys only | 9.6% | 90.4% |
| **full read/write intersection** | **10.9%** | **89.1%** |

(motion + boundary settle on a supersampled disc, 2052 drains.)

**The result — both halves, and the second is the one that matters more.**

The PROPAGATION half had a visible falsifier:

```
tests/test_parallax_efference_migrated.py
  Stage A OFF : 7 passed          (unchanged)
  Stage A ON  : 7 passed          (was 2 failed, 5 passed — §5f's reproduction)
```

The FOLD half had none, by §5c's own account — *"Stage A silently under-counts
every fold-over-bindings rule, and `steps` is identical, so nothing in the iteration profile
signals it."* §5c's minimal reproduction, re-run:

| items | OFF total | ON total, §5c as recorded | ON total, now |
|---|---|---|---|
| 5 | 5.0 | **1.0** | **5.0** |
| 20 | 20.0 | **1.0** | **20.0** |
| 50 | 50.0 | — | **50.0** |

A fix for propagation alone would have closed the red test and left this exactly as it was, with
nothing to notice it by. It is gated at all three sizes, asserted against `n` directly rather than
against the OFF run, so a fixture that quietly stopped counting in BOTH modes could not pass.

*A correction made while building this.* The first predicate excluded the FOLD shape as "plain
counters, already caught by the write-set relation". That was wrong, and it is the larger half —
FOLD is 12.6% of seed rules against PROPAGATION's 3.2%, and §5c is explicit that it is the shape
that does not converge. A refusal that covered only propagation would have closed the visible
falsifier and left the silent under-count in place.

**COMPARE MODE, THE DIRECT CHECK.** The falsifier passing says the red test went green; it does
not say the divergences are gone. Compare mode derives each drain BOTH ways and diffs the write
lists, and §5c recorded 587 divergences across its workloads. Re-run against the refusal:

| workload | compared drains | diverged | unsound |
|---|---|---|---|
| motion + boundary, flood ON | 20 | **1** | 0 |
| conversation + intent | 25 | **0** | 0 |

The single survivor is `bt_chain_collinear`, and it is §5c's **shape 1, the idempotent superset**:
39,424 writes against the committed path's 19,712, exactly 2x, the same edge emitted twice. Its
match is symmetric — it binds `(x, y)` and `(y, x)` — so the committed path suppresses the second
because the edge already exists, while Stage A derives both against the base.

**"Benign" is a claim about the GRAPH, not the write list, so it was checked on the graph.** Same
workload, both modes, order-independent digest over all nodes and edges:

```
OFF: steps=23  nodes=2034  edges=7886  digest=34368dffec963478
ON : steps=23  nodes=2034  edges=7886  digest=34368dffec963478   (1828 proposals, 224 excluded)
IDENTICAL
```

Identical fixpoint, identical graph, with Stage A genuinely active — 1828 proposals, so the
comparison is not vacuous. Gated by `test_the_settled_graph_is_identical_in_both_modes`, which
asserts `proposals > 0` before the digests are allowed to count.

**THE FULL BENCH, BOTH MODES — §5a's own bar.** Run twice; the first attempt is discarded and the
reason is worth more than the numbers.

**Attempt 1 (discarded).** Both passes ran against a MOVING BINARY: the engine `.so` was rebuilt
during both windows, and seven unrelated commits landed inside the OFF window. It reported
OFF 139 failed / ON 131 failed — **Stage A ON with FEWER failures than OFF**, twenty items failing
only in OFF. Stage A cannot fix tests, so that asymmetry was tree drift and nothing else. It also
carried a live trap: three humanoid tests failed only under ON, which reads exactly like a Stage A
regression, and they were files being edited mid-run. This is §5f's own footnote happening a second
time ("the full bench ran on the binary built BEFORE the write-set relation was strengthened").

**Attempt 2 (the result).** A detached worktree pinned at `597dcff` with its own engine, isolated
from the live tree. The harness fingerprints the engine before and after EVERY pass and refuses to
compare if it moved:

```
engine 4522ef6bb22b6d4c at all four measurement points — start and end of both passes
OFF: 456 failed, 8126 passed, 306 skipped, 347 errors, 788 node ids   (3:02:09)
ON : 455 failed, 8127 passed, 306 skipped, 347 errors, 787 node ids   (3:01:21)

only with Stage A ON  (would be a regression):  NONE
only with Stage A OFF (cannot be caused by it): test_full_racing_migrated::
                                                test_short_closed_loop_run_is_graph_authored_and_bounded
```

**No test fails under Stage A that passes without it.** The single asymmetric test was re-run in
isolation, four times per mode, and passes 4/4 in BOTH — an xdist flake, not an effect.

**What this run does NOT establish.** The absolute red count is inflated and is NOT this tree's
baseline: the worktree carries only the 45 TRACKED entries of `results/` against the live tree's
1212, so ~1167 untracked artifacts are missing and the arc / mbpp / prog_descent suites error on
`FileNotFoundError`. That inflation applies EQUALLY to both passes, which is why the comparison
survives it — but 788 red node ids here must never be quoted against
`results/failure_baseline.json`, and a baseline-grade absolute figure would need the artifacts
present. Recorded rather than corrected, because the question this run existed to answer is the
DIFFERENCE, and the difference is clean.

**HONEST LIMITS, all three structural rather than incidental:**

- ~~**Does not see a CROSS-RULE dependency.**~~ **WITHDRAWN — measured, and the phrasing was
  confused.** A drain IS one rule (`attempt_one_rule(&mut self, rule_idx)`), and Stage A's staging
  is scoped inside it, so "rule A and rule B in the same drain" does not name anything: B's drain
  begins after A's has committed. Stage A removes INTRA-drain, SAME-rule visibility and nothing
  else, which is exactly why a per-rule predicate suffices. Gated by
  `test_cross_rule_dependence_is_not_a_stage_a_hazard` — B reads precisely what A writes, both
  modes agree (`k=25/25, done=25/25, steps=2`).

  **The first probe of this was INERT and nearly produced a wrong conclusion.** It wrote both rules
  the natural way, with idempotence guards — and an idempotence guard reads the key it writes, so
  BOTH rules were refused, Stage A never ran, and the modes agreed vacuously at
  `proposals=0, excluded=138`. **An agreement measured with zero proposals says nothing about
  Stage A at all.** The fixture had to separate read from write across NODES to be derivable. That
  trap now has its own gate (`test_a_probe_that_means_to_exercise_stage_a_must_actually_do_so`),
  because it will recur: the ordinary way to write an idempotent rule is the way that gets refused.

- **Sufficient, not complete.** The predicate is syntactic and per-rule. It refuses on the
  intersection of two OVER-APPROXIMATED sets, so it declines rules whose reads and writes could
  never actually meet on the same node.
- ~~**Term-resident rules only**, per `mv_relax`.~~ **WITHDRAWN — the premise was false.**
  `mv_relax` does not live in `substrate.rs`; it appears there only inside a COMMENT, and the
  name occurs in no `.json` and no `.py` anywhere in the tree. This document named it as one of
  three rules of the flood shape, and that reference is stale. The check applies to every rule the
  engine installs, because `derive_access` runs on all of them.
- **Conservative by construction.** A rule that reads its written key on a node no other binding
  can touch is refused anyway. 14.7% is an upper bound on the real dependency rate, not a
  measurement of it.

**The flag still stays OFF by default** — this changes what Stage A *would* do when enabled, not
whether it is enabled. §5a's bar for flipping the default is unchanged and is not met by this.

## 5a. Why the flag still stays off

Not because of a measured defect — there isn't one now — but because the evidence is one
conversational workload plus a 60-test slice, and this repo's own tie census showed engine
behaviour spanning orders of magnitude *between* workloads. Flipping an engine default on that
basis is the error the census exists to prevent. What would justify it: the same
both-modes-identical comparison across ARC, ls20, quanta and the embodied paths, and the full
migrated bench.

By the prereg's letter no NO-GO fired: 11 rules at risk (under 20), the delta enumerable (and
now empty), and the 787 green.

## 6. Honest limits

- **One workload, plus one slice.** Conversation (five utterances) and 60 migrated tests. The 11-rule population and the 401
  probes are properties of that workload; ARC, ls20, quanta and the embodied paths are
  unmeasured, and the tie census already showed these figures span orders of magnitude between
  workloads.
- **Fixpoint iteration counts (§A.3.3): measured, and unchanged** — embodied suite epochs
  351/351, rule enumerations identical, `graph_writes` identical, probe rollbacks −0.2%. At
  suite granularity Stage A costs nothing; it is also too coarse to see 49 diverged drains in
  81,956, so it neither confirms nor refutes anything about the diverging population.
- **Superseded note.** The prereg asks whether removing
  apply-then-undo reduces wasted passes. This implementation *adds* undos — progressing firings
  are now undone and replayed — so per-pass work rises by construction. Now that the graph is
  provably identical in both modes, the comparison is at least well-posed (it was not while the
  two modes converged to different graphs), but it has not been run.
- **`Proposal` is not yet a selectable set.** It is derived and immediately committed in order.
  Stage B needs a family over *subsets* with joint admissibility; this supplies the candidate
  objects, not the selection.
- **Only the `Substrate` drain has Stage A wired, and it is not the only applier.**
  `rewrite::run_rules_opts` is reachable from `graph_rules.rs`, and
  `rewrite::run_rules_opts_scoped` is a separate function called from `substrate.rs`. Both still
  use the committed apply-then-maybe-undo path per binding. This is the same
  more-than-one-applier fact that §1(a) caught the prereg on, and it applies to this
  implementation too: Stage A covers the path the measured workloads run, not every path.

## 7. Reproduce

```bash
bash scripts/engine_build.sh
python3 <scratchpad>/probe_exactness.py      # 401 checked, 0 dirty
python3 <scratchpad>/same_round.py           # 11 rules, NO-GO not triggered
python3 <scratchpad>/dump_graph.py off out1.json   # separate processes
python3 <scratchpad>/dump_graph.py on  out3.json
cargo test --release --lib                   # 787 passed
```
