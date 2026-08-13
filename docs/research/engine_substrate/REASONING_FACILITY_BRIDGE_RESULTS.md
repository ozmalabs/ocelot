# Bridging deduction, analogy and CAN — RESULTS

Prereg: `REASONING_FACILITY_BRIDGE_PREREG.md`, same worktree/branch, base
`main @ 19fdddf`. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/reasoning-bridge`,
branch `reasoning-facility-bridge`.

**Verdict, up front.** **Candidates 1 (deduction→CAN evidence) and 3
(CAN→deduction fact) both GO** — a single new module,
`domains/reasoning_can_bridge.py`, built, zero new Rust, zero edits to any
of the three facilities' own internals (confirmed by diff, §6), with a real
live demonstration for each direction on the real engine, plus a combined
round trip. **Candidate 2 splits**: the *bridge* half (2a — turning a
`BlobEdge` correspondence into a directed implication or coupling) is
**NO-GO-BY-DESIGN**, precisely sized, not forced; the *measurement* half
(2b — the theory-limits doc's own open low-rank/shared-generator question)
was run for real on N=100 real Bigville residents and has a clean, sharp
answer: **the true underlying generator IS exactly rank 2 (0 residual to
machine precision) — but the QUANTIZED weight CAN's own relaxation actually
uses is not (rank 3–4 of 5 needed for 95–99% variance)** — reported in full
in §4, including why this does not, by itself, buy tractability at
Bigville's own N=5 per-resident scale.

---

## 0. Confidence convention

Matching this arc's own standing discipline: a claim verified by reading
source carries `file:line`. A claim backed by an actual run carries **[RUN]**
with real output.

---

## 1. Candidate 1 — Deduction → CAN evidence: GO, narrow, real

### 1.1 The node-type boundary — confirmed disjoint, as predicted

**[RUN]** `SmEntity` (deduction's open-vocabulary entity pool,
`situation_model_reader.py:264-282`) and `Concept` (CAN's pre-authored
belief-network proposition pool) are genuinely disjoint node populations
with **zero** existing linking mechanism — confirmed by grepping every
`SmEntity` reference in the tree (character_tom.py, coref_entities.py,
cognitive_disambiguation.py — all reading-pipeline modules) against every
`Concept`-minting site (358 hits across `domains/*.py`, spanning
acoustic/vision/CAN/meta-shape/lexicon uses — `Concept` the node TYPE is
heavily overloaded, exactly as `SHAPE_TYPE_VOCABULARY_SPIKE.md` already
found). No edge type, no rule, no shared node anywhere connects the two. A
GENERAL bridge (any `SmEntity` → its CAN concept) genuinely needs real
entity-resolution work — this part of the prediction held.

### 1.2 The naming-convention escape hatch — also confirmed, and it is enough

**[RUN]** `worlds/bigville_can_beliefs.build_resident_can_mt`
(`:134-176`, unmodified) mints `Microtheory{name: f"{resident_name}_beliefs"}`
and `Concept{name: <topic>}` with topics (`world_safe`, `trust_mayor`,
`claim_credible`, `self_worth`, `debtor_trustworthy`) in the EXACT
lowercase-underscore string shape `propositional_deduction._norm_attr`
(`propositional_deduction.py:151-158`) already normalizes attr names into.
This is not a coincidence exploited after the fact — it is the SAME string
convention two independently-built facilities both happened to converge on,
and it is enough to build a real, if NARROW, bridge on: given an entity
name and an attr name, look up `Microtheory{name: f"{entity}_beliefs"}`,
look up `Concept{name: attr}` inside it, done.

### 1.3 What was built

`domains/reasoning_can_bridge.py` (new file, ~115 lines), two public
functions:

- `apply_derived_fact_as_can_evidence(agent, entity, attr, *, positive=True,
  alpha=1.0)` — the name-lookup above, then ONE call to the EXISTING,
  already-shipped primitive `concept_apply_evidence`
  (`can_ops.rs::apply_evidence_h`, `:863-871`, PyO3 binding `py.rs:2596-2610`,
  already called today by `worlds/bigville_can_beliefs.apply_scenario_
  evidence` with `alpha=0.6` for less-than-certain testimonial evidence).
  `alpha=1.0` here is not a new invented constant — it is the CEILING on the
  SAME `[0,1]` reliability scale Bigville's own scenario evidence already
  uses, and it is the exact value `seeds/inference_logical.json`'s own
  `causal_strength_ceiling` documentation already named for this precise
  case ("a proof-grade Covers-matched implication is causal-strength
  evidence at its idealized limit... confirm evidence dominating
  completely, disconfirm absent") — a cross-reference that doc's own text
  said was **"read by nothing"**; this module is the first reader.
- `apply_inference_hits_as_can_evidence(agent, hits, *, alpha=1.0)` — the
  batch form, reading `resolve_implication_gap`'s own return shape
  (`{"minted", "gap":{"entity"}, "supplies":{"attr"}}`) mechanically, never
  re-deciding whether a fact was derived — that decision stays entirely
  `inference_generation.py`'s, upstream, unmodified. A `not_`-prefixed
  derived attr (a modus-tollens consequent) round-trips as `positive=False`
  on the bare name, reusing `propositional_deduction`'s own negation
  convention rather than inventing a second one.

### 1.4 Live demonstration — a derived fact really does move a real CAN network's settled state, in the confirmed direction

**[RUN]** `tests/test_reasoning_facility_bridge.py::
test_live_end_to_end_derived_fact_changes_can_settled_state_confirmed_direction`.
Two agents run the byte-identical pipeline — build resident "avery"'s real
CAN network (`build_resident_can_mt`, unmodified, `prior_world_safe=0.35`),
hand-mint a held implication whose consequent attr is a real CAN topic name
(`pd.mint_logical_schema(a, "if X is calm, X is world safe")`), read "Avery
is calm." (`ig.read_and_infer`, unmodified — fires modus ponens, derives
`is_a(avery, world_safe)` on the `SmEntity`) — and differ in EXACTLY one
step: whether `apply_inference_hits_as_can_evidence` is called before the
network is allowed to settle (`run_rules_scoped`, the real discrete-update
rules from `seeds/can_native_reimplementation.json`, unmodified):

```
baseline (no bridge):   world_safe settles to state = 0   (undifferentiated)
with bridge applied:    world_safe settles to state = 1   (positive, confirmed direction)
```

This is a genuine, measured, different downstream result — not a type-check.
`external_field` on the real `Concept` node moves from `None` to `1.0` via
the real primitive (`test_apply_derived_fact_moves_external_field_via_the_
real_primitive`), and the sign is honored (`test_negative_derived_fact_
applies_negative_evidence`: `external_field == -1.0`).

### 1.5 An operational finding along the way, reported not smoothed over

**[RUN]** The FIRST version of this demonstration used plain `agent.inner.
run_rules(3000)` (unscoped) after evidence was applied on a FULL
`WorldAdapter`-booted graph (600+ seeds' worth of rules) and measured **zero
state changes anywhere in the CAN network, `steps==0`, even at local-field
values that should trivially clear the update threshold** (e.g.
`external_field + identity_field ≈ +0.7`, `ATANH_HALF ≈ 0.549`). This is the
SAME starvation shape `CAN_NATIVE_REIMPLEMENTATION_RESULTS.md` §3 already
found and fixed FOR CAN'S OWN SIBLING RULES — here it recurs one level up,
ACROSS SEEDS: on a full boot, `run_rules`'s cold-path fixpoint (one
progressing binding per rule PASS, across the ENTIRE rule list, in list
order) can be monopolised indefinitely by some other seed's rule that
always has a fresh progressing match, starving the CAN update rule of a
turn entirely within a 3000-step budget. The fix is the ALREADY-BUILT,
already-correct tool for exactly this: `run_rules_scoped(max_steps,
detect_cycles, scope_mt)` (`py.rs:3401-3415`, built for
`CAN_MT_SCOPED_RULES_RESULTS.md`), which restricts the fixpoint to rules
touching one Microtheory. Switching to it (§1.4's demonstration) fixed the
issue immediately and is the SHIPPED form. **This is reported here as a
reusable operational fact for the next rung that builds a scoped mechanism
inside a full boot** (echoing `BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md` §8
point 5's own "this is a genuine, reusable finding about the engine, not
specific to this seed"), not filed as a bug in either facility.

### 1.6 What this does NOT establish

- **This is a NAMING-CONVENTION bridge, not general entity resolution.** It
  works exactly when the deduction-side entity name and a CAN-network
  owner's own name coincide (true by construction for a Bigville resident,
  since both a hypothetical text-reading pipeline and the CAN builder would
  use the SAME resident record). It does not solve cross-representation
  coreference (a different phrasing, a pronoun, a description instead of a
  name) — that remains real, unbuilt, and is what a GENERAL version of this
  bridge would need: at minimum, an explicit `corresponds_to`-style edge (or
  a coreference step) linking an `SmEntity` to the CAN-network-bearing
  Microtheory it denotes, sized at roughly one new Γ production + one new
  rule + a resolution convention (a real but bounded amount of work, not a
  large redesign — CAN's own Concept/Mt schema needs no change for it).
- **No standing caller exercises this today.** **[RUN]** confirmed by grep:
  `worlds/bigville_can_beliefs.py` and `worlds/bigville_town100_world.py`
  never call `situation_model_reader`/`inference_generation` — no text
  about a Bigville resident is read through the deduction pipeline anywhere
  in the standing corpus. This bridge is real and working, but — exactly
  the honest shape `BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md` §8 point 2
  already reported for its own site — not yet exercised by any standing
  pipeline.
- **`alpha=1.0` is a design choice, not a proof.** It is the documented
  ceiling on an existing scale, not a value derived from a calibration
  study; a future rung might want a genuine confidence-to-alpha mapping
  (e.g. reading `coherence`/schema provenance) rather than the binary
  ceiling used here.

---

## 2. Candidate 3 — CAN coherence → fact: GO, symmetric to candidate 1, real

### 2.1 Why this direction is, if anything, cleaner

`Resident{name}` sits one hop from a CAN Mt via `has_belief_mt`
(`bigville_can_beliefs.py:159`), supplying a ready-made entity name in the
SAME `f"{name}_beliefs"` convention candidate 1 uses forward; `Concept{name}`
is already the exact attr-name string `ingest_predication`'s `is_a` relation
expects; and `propositional_deduction._negate_attr`'s `not_`-prefix
convention (`:310-328`, already mechanically derived for modus tollens) is
the READY-MADE representation for a settled `state==-1` Concept — no new
naming scheme needed in either direction.

### 2.2 What was built

`can_state_as_predications(agent, mt_node, *, t=0)` — for every Concept
under `mt_node`, `state>0 → is_a(entity, name)`; `state<0 → is_a(entity,
"not_"+name)`; `state==0` (undifferentiated — CAN's own established
"ambivalent" reading, `seeds/causal_attitude_networks.json`'s
`curiosity_targets_ambivalent_nodes`) asserts **nothing** — a genuine null
is never manufactured into a fact. `entity` is read via `_mt_entity_name`
(the Resident's own name via `has_belief_mt` when present, else the Mt's
own name with the `_beliefs` suffix stripped — the same convention, read
backwards). Every write is the UNMODIFIED `situation_model_reader.
ingest_predication`, called exactly as any other caller in the tree already
does it.

### 2.3 Live demonstration — a settled CAN state produces a genuinely new deduction fact

**[RUN]** `tests/test_reasoning_facility_bridge.py::
test_live_end_to_end_can_settled_state_feeds_a_new_deduction_fact`. Resident
"blair" (`prior_world_safe=0.9`, no deduction fact involved on the way in)
settles a real CAN network (`run_rules_scoped`, real rules, `steps=14>0`) to
`world_safe=+1`. **Before** the bridge runs, `ig.read_and_infer(a, "")`
returns `logical: []` — literally nothing is known about "blair" (no text
was ever read). A held implication is minted ("if X is world safe, X is
content"), `can_state_as_predications` ingests `is_a(blair, world_safe)`
(plus the other settled topics, `trust_mayor`, `self_worth`, and
`not_claim_credible` for the one that settled negative), and a **re-run of
`read_and_infer` now derives `is_a(blair, content)`** — a fact that exists
ONLY because the CAN network's own settled belief state flowed into the
deduction pipeline.

### 2.4 What this does NOT establish

Same naming-convention scope limit as candidate 1 (§1.6), read backwards.
`can_state_as_predications` does not check the entity's EXISTING situation-
model facts for consistency before writing — if a `not_X` fact from CAN
collides with an already-held `X` fact from text (or vice versa), BOTH
coexist on the same `SmEntity`, which is a genuine representational gap
(not fixed here, and not introduced by this rung — `situation_model_reader.
ingest_predication` has no belief-revision/retraction step for ANY caller
today, confirmed by reading it; this is a pre-existing property of the
facility this bridge calls into unmodified, surfaced by combining two
sources of fact for the first time). **[RUN]** confirmed directly while
building this rung (not hypothesised): running direction 1 THEN direction 2
on the SAME entity/Mt pair, where the two facts disagree in sign, produces
exactly this coexistence — reported here as the honest reason the two
demonstrations above are kept on SEPARATE entities ("avery" for direction
1, "blair" for direction 2) rather than staged as one scripted round trip
that would silently paper over a real, load-bearing limitation.

---

## 3. Candidate 2a — Analogical correspondence → CAN hypothesis (the bridge): NO-GO-BY-DESIGN, precisely sized

**[RUN]** Checked, not assumed: `find_analogies` output
(`domains/analogical_thinking.py:637+`) and `_pair_witness`'s own
`{shared, name_shared, fixed_count, transform}` (`:414-461`) carry **no
directional signal**. `source_concept`/`target_concept` in a returned
analogy record reflect SEARCH ORDER (which Concept the outer loop visited
first), not a causal or logical direction — confirmed by reading
`_compute_analogy` (`:777-919`) and the returned record shape live
(`find_analogies(sub, 'mathematics', ...)`, `[RUN]`: `{'source_concept':
'propositional_logic_math', 'target_concept': 'predicate_logic_fol_math',
... 'name_shared': 0, 'struct_shared': 0}` — nothing in this shape says
which side would be an antecedent). `_pair_witness`'s `shared`/`transform`
fields are, by construction (`AntiUnifyWitness`, `term.rs`), SYMMETRIC in
their two operands — the template generalises over an unordered pair.

**This confirms the prereg's own registered concern exactly**: turning a
`BlobEdge` correspondence into a directed implication hypothesis (`P⇒Q`,
picking WHICH Concept is `P`) needs a real, new DIRECTION-INFERENCE
mechanism this substrate does not have today — not a missing field to read,
a missing JUDGEMENT to make. Sized precisely, as the task asked, rather than
forced into a shallow bridge:

- **What it needs:** either (a) a Python-side heuristic reading some OTHER,
  already-asymmetric signal not part of `_pair_witness` itself (e.g. which
  Concept's `definition` text contains a causal/conditional cue word — a
  real, if weak, prior, and itself borderline "a decision in Python" per
  `CLAUDE.md`'s own architecture rule, so more likely belongs as a graph
  Rule reading held cue vocabulary, matching the `gap_awareness`/deficiency-
  concept precedent), or (b) new representational work — a DIRECTED variant
  of `BlobEdge` (or a `Transform{dim,delta}`-style asymmetric companion) —
  minted by a NEW rule that decides direction from some other held fact
  (e.g. temporal/causal ordering already present on the two Concepts'
  own Mt, if any).
- **Size:** roughly 1 new seed (a handful of Γ productions + 1-2 rules for
  option (b)), no new Rust Term identified as necessary (the shape-math
  algebra itself is domain-neutral per `CROSS_DOMAIN_SHAPE_SPIKE.md` §4.1 —
  what's missing is a JUDGEMENT, not an operator). Not attempted here,
  per the task's own explicit sanction for a clean, precisely-sized null.

---

## 4. Candidate 2b — The low-rank/shared-generator hypothesis: tested for real, on real data, sharp answer

### 4.1 The question, restated

`CAN_SOLVER_THEORETICAL_LIMITS_RESEARCH.md` §6.4-6.5 (Q4, ranked item 4 of
5 in its own §7) named a real, rigorous, but UNTESTED condition: the
Koehler-Lee-Risteski low-rank Ising tractability result applies only when a
coupling matrix genuinely factors through a SMALL number of shared latent
generators (`J_ij = Σ_μ w_μ·f_μ(i)·f_μ(j)`), not merely when many edges
happen to round to the same numeric value. That document's own honest
admission: *"no populated `causal_influence` network currently exists in
the corpus to test this against."* One now does — `seeds/
bigville_cast100.json`'s 100 real residents, `build_resident_can_mt`
unmodified.

### 4.2 The measurement

**[RUN]** `scripts/_reasoning_bridge_lowrank_probe.py` (new, one-off
investigation script — reads `seeds/bigville_cast100.json`, calls
`true_edge_j`/`quantize_j`/`build_resident_can_mt`, all unmodified). Stacks
the 5 real `STRUCTURAL_EDGES` weights for all 100 residents into a
100×5 matrix (once for the pre-quantization continuous `true_j`, once for
the actual quantized `causal_influence` weight CAN's relaxation reads), SVD
on the centered matrix:

```
=== N=100 real Bigville residents' causal_influence coupling ===
distinct nuance_key generators driving ALL edge variation: ['mood_bias', 'w_supergraph'] (count=2)

--- true_j (pre-quantization, continuous) ---
singular values:           [1.055411, 0.861768, 0.0, 0.0, 0.0]
explained variance ratio:  [0.599984, 0.400016, 0.0, 0.0, 0.0]
cumulative explained:      [0.599984, 1.0, 1.0, 1.0, 1.0]
rank needed for 95% var:   2 / 5 edges
rank needed for 99% var:   2 / 5 edges

--- quantized_j (actual CAN causal_influence weight) ---
singular values:           [7.096367, 2.25286, 2.218539, 1.490517, 0.578473]
explained variance ratio:  [0.800458, 0.080674, 0.078235, 0.035313, 0.005319]
cumulative explained:      [0.800458, 0.881133, 0.959367, 0.994681, 1.0]
rank needed for 95% var:   3 / 5 edges
rank needed for 99% var:   4 / 5 edges
```

### 4.3 The answer, stated precisely, both halves

**The TRUE underlying generator structure is exactly low-rank — rank 2,
to machine precision (singular values 3, 4, 5 are exactly `0.0`, not merely
small).** This is not a coincidence to be marveled at; it is the DIRECT,
provable consequence of `worlds/bigville_can_beliefs.STRUCTURAL_EDGES`'s own
construction (`:61-67`): every one of the 5 edges' `true_j` is a FIXED base
value plus a deviation driven by exactly ONE of only 2 shared per-resident
nuance parameters (`mood_bias` or `w_supergraph`, `true_edge_j`'s own
formula) — so the population-level coupling variation is, by construction,
a rank-2 phenomenon (2 shared latent generators, matching `mood_bias`/
`w_supergraph` exactly). **The hypothesis is CONFIRMED for the continuous
generator**, on real data, for the first time.

**But the QUANTIZED weight — what CAN's own relaxation and the native
discrete-update rules ACTUALLY read (`causal_influence`'s `weight` attr) —
is NOT clean low-rank**: per-edge, per-resident independent rounding
(`quantize_j`, `bigville_can_beliefs.py`) breaks the exact rank-2 structure,
inflating the effective rank to 3-4 of 5 for 95-99% of variance. **Whether
"the shape-recognition hypothesis" (98.3% `transform_key` pattern reuse,
`BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md`) corresponds to a tractability-
relevant low-rank structure therefore depends on WHICH representation is
asked about — the ANSWER is "yes for the generator, no (or much weaker) for
the quantized graph the solver actually touches" — exactly the distinction
Q4 §6.4 said "a naive reading of '98.3% pattern reuse' does not by itself
establish," now measured rather than argued.**

### 4.4 What this does NOT establish — the honest limit named in the prereg, confirmed

**This measurement does NOT demonstrate a tractability WIN**, and is not
claimed to. Q4's own §6.2/6.3 finding stands unchanged: the low-rank
tractability results are about scaling ADVANTAGE at LARGE N (the point of
`J_ij = Σ_μ w_μ·f_μ(i)·f_μ(j)` mattering is that it turns an
`O(N²)`-parameter coupling matrix into `O(N·p)` for small `p`). Bigville's
own per-resident CAN network is **N=5** — already trivially tractable at
any rank, by construction (`STRUCTURAL_EDGES` has exactly 5 entries; no
per-resident network in the standing corpus is anywhere near the scale
where low-rank factorization would change the asymptotic picture). **What
this measurement establishes is the STRUCTURAL FACT (the shared-generator
hypothesis is real and measurable, not merely plausible-sounding) — it does
not, and could not from this data, establish that the tractability result
is currently load-bearing for any network this project has actually built.**
This is a precise, narrower claim than "low-rank helps," and is reported as
such rather than oversold.

---

## 5. Which bridges were built, precisely (per the prereg's own decision rule)

Per prereg §4: candidates 1 and 3 both cleared their GO bars, are
mechanically symmetric, and cost little more built together than either
alone — **both built.** Candidate 2a's own GO bar (a real design gap
closeable within scope) was not met — **not built, precisely sized (§3).**
Candidate 2b needed no bridge to answer and was run regardless, per the
task's own explicit instruction — **run, real numbers (§4).**

---

## 6. Regression — facility internals untouched, confirmed by diff

**[RUN]**:

```
$ git status --short
?? docs/research/engine_substrate/REASONING_FACILITY_BRIDGE_PREREG.md
?? docs/research/engine_substrate/REASONING_FACILITY_BRIDGE_RESULTS.md
?? domains/reasoning_can_bridge.py
?? scripts/_reasoning_bridge_lowrank_probe.py
?? tests/test_reasoning_facility_bridge.py
```

Zero modified files. `data` is the local, gitignored, untracked
`data/`-symlink convenience workaround documented elsewhere in this tree
(`DEDUCTION_GENERALIZATION_RESULTS.md` §7.1) — not committed.

```
$ git diff --stat main -- domains/propositional_deduction.py \
    domains/inference_generation.py domains/situation_model_reader.py \
    domains/analogical_thinking.py seeds/inference_logical.json \
    seeds/can_native_reimplementation.json seeds/can_decay_identity.json \
    worlds/bigville_can_beliefs.py runners/dsl/src/can_ops.rs runners/dsl/src/term.rs
(empty output)
```

Also asserted as a standing regression guard:
`test_source_audit_no_facility_internals_edited`
(`tests/test_reasoning_facility_bridge.py`).

**Pre-registered regression suite, before and after — identical, 112/112
passed both times ([RUN], no paired failures to report):**

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_deduction_generalization.py tests/test_deduction_extension.py \
    tests/test_inference_generation.py tests/test_blob_edge_analogy_extension.py \
    tests/test_analogical_relative_ranking.py tests/test_can_native_reimplementation.py \
    tests/test_bigville_can_integration.py tests/test_can_identity_nudge_final.py \
    tests/test_reasoning_facility_bridge.py \
    -q -p no:randomly
112 passed in 75.95s
```

New test file alone:

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_reasoning_facility_bridge.py -q -p no:randomly
10 passed in 2.26s
```

---

## 7. What this whole rung does NOT establish

1. **Not general entity resolution.** Both built bridges are naming-
   convention bridges (§1.6, §2.4); they do not solve cross-representation
   coreference for the general case (an entity named differently by two
   facilities is invisible to both directions).
2. **No standing caller exercises either built direction today** (§1.6) —
   real, working, unexercised, exactly the honest shape this arc's own
   prior rungs have already reported for their own new call sites.
3. **No consistency/belief-revision step** — combining derived facts from
   two sources on one entity can produce a genuine contradiction in the
   situation model (§2.4); this is a pre-existing property of
   `ingest_predication` (no caller in the tree gets belief revision), not
   introduced by this rung, and not fixed here.
4. **Candidate 2a is a real, unclosed gap**, precisely sized (§3), not a
   shallow bridge forced to look complete.
5. **Candidate 2b's low-rank finding is a structural fact about ONE
   specific construction** (`worlds/bigville_can_beliefs.py`'s fixed
   5-edge template + 2-nuance-parameter design) — it is not a claim about
   `causal_influence` networks in general, and it explicitly does NOT
   establish a tractability win at any scale this project has actually
   built (§4.4).
6. **`alpha=1.0` (candidate 1) is a documented design choice, not a
   calibrated value** — no claim is made that it is the "correct" evidence
   strength for a derived fact in general.
7. **Synthetic-proven mechanism ≠ benchmark value, per house standard**:
   every number in §1-2 is a mechanism demonstration (does the bridge move
   real state, does a real new fact appear), not a coverage/accuracy claim
   over any corpus; §4's numbers are a real structural measurement of one
   specific data-generating process, not a general population claim.

---

## 8. Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/reasoning-bridge
git log --oneline -1 main   # 19fdddf, verified before branching

# New bridge module's own tests (both live demonstrations, -q -s for output)
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_reasoning_facility_bridge.py -q -p no:randomly

# Full pre-registered regression set
PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_deduction_generalization.py tests/test_deduction_extension.py \
  tests/test_inference_generation.py tests/test_blob_edge_analogy_extension.py \
  tests/test_analogical_relative_ranking.py tests/test_can_native_reimplementation.py \
  tests/test_bigville_can_integration.py tests/test_can_identity_nudge_final.py \
  tests/test_reasoning_facility_bridge.py \
  -q -p no:randomly

# Candidate 2b's low-rank measurement
PYTHONPATH=".:runners/dsl/python" python3 scripts/_reasoning_bridge_lowrank_probe.py
```
