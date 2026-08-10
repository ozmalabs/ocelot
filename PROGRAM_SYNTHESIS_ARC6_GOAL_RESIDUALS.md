# ARC 6 — MEASURED CEILINGS, GRAPH-RESIDENT

**Date:** 2026-08-03
**Status:** BUILT AND MEASURED. GR1–GR4 each reported explicitly below.
**Artifact:** `results/arc6_goal_residuals.json`
**Seeds:** `seeds/goal_residuals.json` (new, v1.0.0);
`seeds/program_synthesis.json` v1.11.0 → **v1.12.0**
**Engine:** `48da7257f35d3046e9bd18952b817a51d9f7ffbc19b08f52965bc07c5c429929`,
archived out of tree at
`~/ozma-engine-archive/_native.abi3.so.48da7257…` (prereg A1.1). **This is
NOT the `8311d4356082…` the rung was briefed with — see §7, it matters.**

> ### ⚠ CORRECTION 2026-08-03 — THE ENGINE ABOVE WAS THE WRONG ONE, AND ONE OF
> ### THIS DOCUMENT'S FINDINGS IS NOW REVERSED
>
> **Everything below §7 was measured on a tree whose binary did not match its
> own committed source.** The gitignored `_native.abi3.so` had been overwritten
> with arm A's `48da7257f35d…` and the value-layer adapter edits had been
> reverted out of the working tree — prereg **A1.1**'s registered hazard,
> realised. §7 correctly *recorded* the discrepancy; what it could not know is
> that the discrepancy was **repairable**, not a fact about the world.
>
> The tree is now **coherent**: engine
> `8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0` (arm C's
> binary, restored from the out-of-tree archive) with the matching adapter
> source, verified live —
> `add_node({"lst":[1,2,3],"tup":(1,2,3)})` reads back **list and tuple
> distinctly**.
>
> **What this document said:** §7 — *"The row-verdict residual is **LIVE, not
> stale**. Its condition (`value_layer_list_eq_tuple == "1"`) is measured true
> *in this process* … The tempting write-up — 'arc C superseded it, so it
> lapsed' — would have been a claim about a different engine."*
>
> **Why it changed:** that reasoning was right *for the tree it stood in*, and
> the tree was wrong. On the coherent engine `probe_facts` measures
> `value_layer_list_eq_tuple == "0"`, the condition is falsified, and
> `gr_condition_lapse` lapses the residual. **The row-verdict residual is now
> legitimately STALE AS SHIPPED.**
>
> **That is a result, not damage.** GR2 was built to make a refutation stop
> being charged once its mechanism is repaired, and it did exactly that —
> live, unprompted, on a world change staged for an entirely different reason.
> Nobody wrote a lapse demo for it; the mechanism found the falsification by
> itself. It is the first time the residual layer has corrected the record
> rather than merely holding it.
>
> **What is corrected below, and where:** §5's GR2 table (`stale = 0` for all
> six no longer holds), §5's GR4 numbers (36 → **48**), §7 in full. Corrections
> are marked in place; **nothing above is deleted or silently rewritten**. The
> full account is **§10** and `PROGRAM_SYNTHESIS_ARC6_COHERENCE.md`.
>
> **What is NOT corrected:** GR1, GR3, and the whole of §1–§4. The collapse
> readings are byte-identical under both engines (`arc6_goal_residuals.json` →
> `GR1_collapse_live` vs `superseded_measurement_48da7257.GR1_collapse_live`);
> the signature design, the ingest and the Python-decision audit never touched
> the value layer.

---

## 0. The problem, and the shape of the fix

Arc 6 measured five ceilings and killed three seams. **Every one of those
results existed only in markdown.** They were absorbed by the human
orchestrator, not by the substrate — and per `CLAUDE.md`'s self-repair
boundary (*"the agent can self-repair exactly where its cognition is
graph-native … it CANNOT edit the Python front end, because that is not graph
it can see or vary"*), prose is exactly the blind spot the agent cannot act
on. A goal-selection collapse would re-propose a refuted seam, confidently,
with no memory.

The principle: **pursuing an unreachable goal is legitimate and productive —
that is how residuals get made. What is not legitimate is being wrong where
the residual is already held.** Non-repetition should be architecture, not
discipline.

The sd loop already does this shape for shape-decoding (residual → mint
quantum → `codebook_epoch` → re-decode, made mint-once by the `has_transform`
guard). This is the same move for goals.

---

## 1. The design, and the signature-matching trade-off

### 1.1 The crux: how is a goal signature matched?

This is the whole design, and both failure modes are already on the record in
this project:

- **Too specific** and every residual is a per-goal lookup key that never
  fires. This is exactly how Seam D failed: one `PropertyAtom` per residual
  task scored **36/36** on the population it was authored from and **0/36**
  the moment its own atom was removed (`results/arc6_d_loo.json`,
  `headline.leave_one_out`). Its atoms reached **one** foreign task in 257
  (`m3_cross_task_firing.tasks_with_a_FOREIGN_cue_match_ids: [266]`).
- **Too loose** and it suppresses reachable goals. Seam C's own instrument
  demonstrated the failure mode in miniature: the `relation_all` keyword
  variant "recognised" **245 of 257** tasks, and the cherry-picked cue set's
  first pass matched `turn` inside `reTURNs` for 29 of its 31 claimed ids —
  *"My own cherry-picked instrument reproduced the exact substring-collision
  failure it was built to expose."*

**The decision: a CLOSED-VOCABULARY STRUCTURED SIGNATURE with explicit
wildcards.** Three dimensions, each drawn from a fixed token set:

| dimension | what it names | tokens |
|---|---|---|
| `sig_seam` | the mechanism the goal proposes to build | `import_oracle`, `ir_retarget`, `shape_codebook`, `property_atom`, `enum_op_table`, `row_verdict` |
| `sig_lever` | which layer of the pipeline it changes | `proposal`, `execution`, `verdict`, `detection`, `representation` |
| `sig_target` | over which population the ceiling was measured | `mbpp_test_257`, `mbpp_live_unreached_53`, `mbpp_s4_residual_60`, `mbpp_residual_36`, `mbpp_arc4_104` |

**The match rule:** a residual matches a candidate iff, for **every dimension
the RESIDUAL declares**, the candidate agrees. A dimension the residual leaves
unset is a **wildcard**.

**The asymmetry, stated because it is a real choice:** only the *residual* may
wildcard. An **absent** dimension on the *candidate* is disagreement, not a
wildcard — a goal that has not said what population it targets is not yet
"where the residual is held", and the correct direction of caution is to let
it be pursued. (Gated:
`test_gr4_the_new_weight_term_is_identically_zero_without_a_signature`.)

### 1.2 Why this is not either failure mode

**Specificity becomes an authored, auditable property** — how many dimensions
a residual pins — rather than an emergent property of string overlap. The
dial is visible in the graph and testable in both positions
(`test_gr1_an_undeclared_dimension_is_a_wildcard` widens a residual by
clearing `sig_target` and shows the look-alike become chargeable).

**The anti-Seam-D guard is mechanical, and it is seam D's own instrument.**
`arc6_bc_ceiling.json`'s key test asks whether a cue is a
`verbatim_prompt_substring_of_len_ge_12`. The same question is asked of this
vocabulary, over the MBPP fixture, in
`test_no_signature_token_is_a_verbatim_prompt_substring`. Plus: every
signature value on every residual must be a token in the `SignatureVocab`
nodes the seed itself carries
(`test_signature_vocabulary_is_CLOSED_and_graph_resident`) — a residual cannot
smuggle in free text.

**Discrimination is gated LOO-style.** For each of the six residuals, a
candidate built from its own signature must be charged by it, and no two
residuals share a signature tuple
(`test_gr1_every_residual_discriminates_its_own_signature_from_every_other`).

### 1.3 What a residual holds

`GoalResidual{rid, sig_seam, sig_lever, sig_target, reach_class,
reach_class_factor, ceiling_honest_n/ids, ceiling_cherry_n/ids,
ceiling_reductio_n/ids, denominator_n, mechanism, mechanism_source_path,
weight, weight_formula, evidence_artifact, evidence_artifact_sha256,
evidence_engine_sha256 | evidence_engine_line, stale}`, plus one or more
`ResidualCondition` via a `holds_under` edge.

**Honest AND cherry-picked are both held**, because the gap between them is
itself the information — the registered granularity trap. Seam A carries
**5 / 27 / 60** as three separate numbers
(`test_the_honest_and_the_cherry_picked_ceiling_are_BOTH_held`), so the
inflation cannot be flattened into one figure later.

**The weight** is
`RESIDUAL_SCALE(100) × reach_class_factor × (1 − honest_n / denominator_n)`.
Two authored constants (declared as `ResidualPolicy` and `ReachClass` graph
data, tunable), one measured factor: how much of its own denominator the
honest ceiling failed to reach. A residual that reached everything weighs
nothing. This is the same shape as `ps_move_w_gap` / `ps_move_w_arity` /
`ps_move_w_mdl` — every coefficient is graph data.

**Aggregation is MAX, not sum.** Near-duplicate residuals describing one
refutation must not compound into a de-facto veto.

---

## 2. What was hooked, and why

**`ps_move_select`** (`seeds/program_synthesis.json`). Not a new mechanism.

It is this project's canonical weighted collapse — its own comment says so:
*"WEIGHTED COLLAPSE: Argmax over every candidate MoveCandidate … by weight =
ps_move_w_gap\*gap + ps_move_w_arity\*arity_gap − ps_move_w_mdl\*mdl_bits —
coefficients read from the GOAL's own attrs (graph data … tunable without code
or rule changes)."* Decisive for this rung: **it already separates POOL
MEMBERSHIP from WEIGHT.** Refutation and the `gap > 0` earns-its-keep gate are
`Filter`/`where` predicates; the ranking is the Argmax value. A held residual
belongs on the weight side of that line, and it was put there and nowhere
else.

| changed | not changed |
|---|---|
| `ps_move_mark` +1 effect: stamps `ps_move_w_residual` (1.0) | `ps_move_select.where` |
| `ps_move_select` weight: `… − ps_move_w_residual × PENALTY(mc)`, substituted in all **five** Argmax expressions so no two selected facts come from different rankings | `ps_move_select.match` |
| | the Argmax **source** (the candidate pool) |
| | every other rule, node, edge and production in the seed |

Mechanically gated: `test_gr4_the_synthesis_seed_diff_is_confined_to_two_rules`
diffs against the committed manifest and asserts `where` and `match` are
byte-identical; `test_gr3_the_penalty_is_not_a_pool_filter` asserts
`GoalResidual` appears in every Argmax **value** and in **no** Argmax source
and in no `where`. *That is the difference between a weight and a veto, made
structural rather than promised.*

`PENALTY(mc)` is
`IfThenElse(Exists matching non-stale residual, max weight, 0.0)`. It is
computed **inline**, not read from an attr, so the selection can never depend
on whether an audit stamp has been written yet in the fixpoint.
(`Times(w, null)` evaluates to `w` in this engine — measured — which is why
the zero is an explicit branch and not a null.)

The audit read-out lives in the residual seed, not the synthesis seed:
`gr_move_penalty` / `gr_move_penalty_clear` stamp `residual_penalty` on each
candidate (both directions, so "no penalty" is a written `0.0` rather than an
absent attr), and `gr_move_sel_audit` copies the winner's charge onto the goal
as `ps_move_sel_residual_penalty`.

### What was considered and rejected

- **A new goal-selection rule.** Rejected: the brief says do not invent a
  parallel mechanism, and `ps_move_select` already has the exact shape.
- **`seeds/escalation_rungs.json` / `cascade_pick`.** Its collapse is an
  `Argmin(level)` over a fixed rung ladder gated by `Lt(margin, threshold)` —
  a *sequencing* decision with no candidate-specific weight to add a term to.
  Wrong shape.
- **`ShapeDecode`.** It is the decode op, not the goal collapse; the
  residual/`codebook_epoch` loop it drives is the *precedent* this rung
  copies, not the hook.

---

## 3. What was ingested — from the JSON, not the prose

Six residuals, all six clean, `not_ingested_path_misses: []`. Every number is
resolved from a dotted path into a results artifact; every prose field is a
verbatim copy of a string at a dotted path
(`test_every_ingested_number_is_traceable_to_a_path_in_its_artifact`
re-resolves each independently of the seed).

| rid | seam / lever / target | honest | cherry | denom | reach class | weight | evidence engine |
|---|---|---|---|---|---|---|---|
| `arc6.seam_a.import_oracle` | import_oracle / execution / live_unreached_53 | **5** | 27 (reductio 60) | 53 | operator_blocked | 63.40 | `5c1b472fe674…` |
| `arc6.seam_b.ir_retarget` | ir_retarget / proposal / test_257 | **0** | 83 | 257 | operator_blocked | 70.00 | `5c1b472fe674…` |
| `arc6.seam_c.shape_codebook` | shape_codebook / detection / test_257 | **0** | 1 | 257 | operator_blocked | 70.00 | `5c1b472fe674…` |
| `arc6.seam_d.property_atom` | property_atom / verdict / residual_36 | **0** | 36 | 36 | operator_blocked | 70.00 | `5c1b472fe674…` |
| `arc6.structural.enum_op_table` | enum_op_table / proposal / s4_residual_60 | **6** | 42 | 60 | operator_blocked | 63.00 | `5c1b472fe674…` |
| `arc6.verdict.row_verdict_seed_only` | row_verdict / verdict / test_257 | **4** | 15 | 15 | operator_blocked | 51.33 | `48da7257f35d` (line) |

Every honest/cherry figure is a **paired id list** on the node, never a bare
count. Extras carried where the artifact has them: seam A's blocker split over
the live-unreached 53 (`budget 7 / missing_dimension 4 /
missing_structural_primitive 42`); seam B's levels 1, 1b, 2b and its
`refuted_as_coincidental_fit: [224]`; seam C's `direct_load` seed-load shape
(17 nodes, 0 edges, 0 recognised), `verdict_counts {spurious: 252}` and
`codebook_carries_a_synthesis_payload: false`; seam D's LOO lost ids, the
single foreign cue match, and the arc-4 denominators; the structural
residual's B0/B3 id lists, `inflation_B0_to_B3: 4.2`, and the measured
`missing_dimension_ids: []`.

**The reachability class is measured, not asserted.** Arc 5 closed six
π-geometry tasks by minting a dimension; the structural ceiling measured
**zero of 42** as dimension-blocked
(`dimension_vs_operator.missing_dimension_ids: []`, `n: 0`), which is *why*
that residual is `operator_blocked`. Both facts ride on the node and are gated
(`test_the_reachability_class_is_recorded_and_the_measured_zero_is_kept`).

### Deliberately left out, for lacking a measured source

Recorded as data in `deliberately_not_ingested`, not as prose:

1. **"only 39/257 tasks have the `f(int)→int` signature; 218 excluded before
   semantics apply"** — stated in the prereg §1; **no path in
   `results/arc6_bc_ceiling.json` carries 39 or 218 as a signature count.**
   Left out. The artifact's own B levels (0 / 1 / 3 / 5 / 4 / 83) are ingested
   instead.
2. **"35 of 36 atoms carried a verbatim prompt substring"** — the artifact
   carries **no `verbatim` key at any path**. Left out. What it does carry —
   LOO 0/36, exactly one foreign cue match, zero foreign *applicable* atoms —
   is ingested and says the same thing from measurement.
3. **"HS1 failed, 0 of 10 converted"** (prereg A2) — `results/arc6_tier0.json`
   was not in this rung's ingest set. Left out rather than sourced from a
   seventh artifact after the fact; the structural residual carries no
   conversion claim it cannot source.
4. **`results/arc6_valuelayer.json` mints no residual.** It is a *success*,
   not a refutation. It is used the other way round — as the evidence that the
   row-verdict residual's condition *can* lapse. §7 explains why, measured in
   this tree, it has not.

---

## 4. The condition is load-bearing

A residual without its condition is precisely the failure `CLAUDE.md`
retracts: a claim quoted without its condition, which stood false for ten
days. **A residual that cannot lapse is a lie with a long half-life.**

Every residual carries at least one `ResidualCondition`
(`test_gr2_every_residual_carries_at_least_one_condition`), and staleness is
recomputed each pass by two mutually-exclusive rules — `gr_condition_lapse`
and `gr_condition_hold`. It is **not latched**: a one-way lapse would itself
be an unrevisable claim.

Three condition kinds, all live graph reads:

- **`shape_count`** — `Count(ShapeSignature where kind == v) == expected`.
- **`payload_count`** — the same, additionally requiring a non-null
  `keywords`.
- **`fact_equals`** — a named `ResidualFact{name, value}`, measured live by
  `probe_facts` (mechanical I/O: it *reports* what is true, the rule decides
  what follows).

**Seam C's null is conditional, and its condition is written down.** It nulled
because the math codebook is six `kind=math` `ShapeSignature` nodes, **0
edges**, and **no synthesis payload** — *"Even a genuine recognition supplies
only a LABEL … A label with no payload cannot change what the enumerator
does."* Both halves are conditions on the node. Note the type is
`ShapeSignature`, not `MetaShape` — there are indeed zero `MetaShape` nodes in
that file, but the codebook the ceiling measured is the 17 `ShapeSignature`
nodes (6 math / 11 faculty), and that is what the condition counts.

**Staleness is not falsity.** It means the measurement no longer describes the
world and must be re-made before it may be used again. That is deliberately
conservative: adding a seventh payload-less math shape does not by itself
revive seam C's recognition, but it does mean the recorded ceiling was
measured against a codebook that no longer exists.

---

## 5. GR1–GR4

### GR1 — **PASS**

A goal matching a held residual is measurably down-weighted in the existing
collapse, demonstrated live, both directions. All four scenes are the *same*
rule, the *same* coefficients, and the *same* two candidates; the only
variable is what the agent holds.

| scene | winner | A charged | B charged |
|---|---|---|---|
| control — no residual held | **A** (gap 100 > 60) | — | — |
| residual held (`enum_op_table` / `proposal` / `s4_residual_60`) | **B** | **63.0** | **0.0** |
| not-a-veto — A's gap raised to 200 | **A** | 63.0 (still charged) | 0.0 |
| unsignatured candidates (what the pipeline mints today) | **A** | 0.0 | 0.0 |

- **It fires.** A's own signature matches the held structural residual; A is
  charged that residual's measured weight (63.0 = 100 × 0.7 × (1 − 6/60), with
  6 and 60 read out of `arc6_structural_ceiling.json`), and the collapse flips
  to B.
- **It does not fire on a look-alike.** B declares the *same* seam and the
  *same* lever and differs only in the population — and is charged **0.0**,
  in the same scene in which A is charged 63.0 (a matcher stuck at zero would
  otherwise pass the negative half).
- **It is a weight, not a veto.** Raise A's gap and A wins again *while still
  being charged*. Winning despite a residual is the point; winning because the
  residual was ignored is not.
- **It is inert where nothing is held.** Every `MoveCandidate`
  `domains/prog_moves.py` mints is unsignatured, so the new term is exactly
  `0.0` for all of them — asserted as arithmetic on the Term, not as a hope
  (`test_gr4_the_new_weight_term_is_identically_zero_without_a_signature`
  evaluates `PENALTY` to `0.0`, then flips the same Term non-zero by adding a
  signature).

Gates: seven `test_gr1_*` tests, all green.

### GR2 — **PASS**

A residual whose condition is falsified lapses, demonstrated live by
falsifying seam C's condition. Three independent falsifications, each
affecting **only** the residual whose condition it breaks:

> **CORRECTED 2026-08-03 (coherence).** The first row of this table no longer
> holds. On the coherent engine the row-verdict residual is **stale as
> shipped** — five live, one lapsed — and the last two rows are correspondingly
> re-read: the value-layer fact measures `0`, not `1`, so the demonstration
> runs in the other direction (restore the fact → the residual un-lapses;
> falsify it again → it lapses). Both directions are still exercised in one
> scene, and every other row is unchanged and re-verified. Measured:
> `results/arc6_goal_residuals.json` → `GR2_condition_lapse_live`. Gate:
> `test_gr2_all_conditions_hold_in_the_shipped_world` now pins the exact
> stale MAP (never a count), and `test_gr2_HEADLINE_seam_c_lapses_…` now
> asserts a before/after DELTA rather than "all others are 0.0" — strictly
> stronger, since it also catches an un-lapse. See §10.

| action | result |
|---|---|
| as shipped | all six residuals live (`stale = 0`) |
| add one `kind=math` `ShapeSignature` (the registered demo) | **seam C stale**, five others untouched |
| give one existing math shape a `keywords` payload (count unchanged at 6) | **seam C stale** |
| restore the population | **seam C live again** (the un-lapse direction) |
| flip the measured `value_layer_list_eq_tuple` fact to `0` | **row-verdict residual stale**, five others untouched |
| bare graph (no codebook, no facts) | all six stale — a residual whose evidence cannot be verified is not usable |

And the two mechanisms joined: once seam C is stale, a goal on that seam is no
longer charged and the collapse **reverts** to it
(`test_gr2_a_LAPSED_residual_stops_down_weighting_the_collapse`).

One ordering fact, recorded rather than smoothed over: a lapse settles in the
`run_rules` fixpoint, and a goal that has *already* passed the rung is not
re-decided (`ps_move_select` moves the status off `moves_scan`). Staleness
changes what the **next** collapse reads. A decision already taken is not
retroactively unmade.

Gates: seven `test_gr2_*` tests, all green.

### GR3 — **PASS**

No Python decisions; matching and weighting are Rules/Terms.

- `domains/goal_residual_ingest.py` passes the standing source audit (no
  `argmin`/`argmax`, no `min`/`max(key=)`, no sort over a score).
- **Stronger, and specific to this module:** it never reads the graph. It does
  not import `substrate_rs`, never calls `.evaluate(`, never calls
  `run_rules`, and its only substrate contact is `add_node` / `node` inside
  `probe_facts`/`install_facts` — asserted mechanically, so it *cannot*
  contain a hidden decision over graph state.
- `grep -rln --include=*.py sig_seam domains/` returns exactly one file (the
  ingest adapter, which only names the attrs). The matcher, the staleness
  check and the penalty are Terms in `seeds/goal_residuals.json`.
- **Zero new `TermNode` variants** — the whole mechanism composes `Argmax`,
  `IfThenElse`, `Count`, `Filter`, `NodesOfType`, `Exists`, `Neighbours`,
  `Pick`, `Eq`, `Not`, `And`, `Or`, `Attr`, `Lit`, all pre-existing. Same
  mechanical price audit tier 0 registered as HS3.
- **The rules are verified to FIRE**, not merely to exist — an unknown op name
  is a silent no-op in this engine, so every GR1/GR2 gate above is a live
  invocation.

Gates: five `test_gr3_*`/audit tests, all green.

### GR4 — **PASS, with the bar's number corrected**

> **CORRECTED 2026-08-03 (coherence) — THE ORIGINAL BAR WAS RIGHT ALL ALONG.**
> The paragraph below reasoned correctly inside a wrong frame: it was the
> *tree*, not the bar, that was wrong. On the coherent engine
> `8311d4356082…` the registered **48** is exactly what the pipeline measures.
> Re-measured for this correction, pre-patch **and** post-patch on the same
> engine:
>
> | arm | seed | engine | pass | accepted |
> |---|---|---|---|---|
> | pre-patch (`arc6_verdict_gr_baseline_8311d435.json`) | v1.11.0, `5302b959daf2` | `8311d4356082` | **48** | 95 |
> | patched (`arc6_verdict_gr4_gate.json`) | v1.12.0, `4e866340eb50` | `8311d4356082` | **48** | 95 |
> | **patched − pre-patch** | | | **`lost: []`, `gained: []`** | `[]` / `[]` |
>
> **The bar is still "unchanged", not "48".** The 48 is not adopted from the
> patched run; it is the pre-patch seed rerun on this engine, and the patched
> seed reproduces it exactly. The 12 ids separating it from the old 36 are
> precisely `results/arc6_valuelayer.json` → `arms.C_minus_B.pass_gained`
> (`161, 249, 257, 272, 290, 393, 413, 418, 436, 450, 457, 460`) — the value
> layer's own gains, nothing this rung did, and the gate now asserts that
> decomposition arithmetically so the re-pin cannot be reused to absorb a
> future gain. See §10.

**The bar was registered as "the 48 current pass ids". This tree measures 36,
and 36 is what "current" means here.** See §7. The measurement:

- **Live MBPP, full 257-task runnable split, patched seed:** the pass id list
  is **byte-identical to the pre-change list** — 36 ids, and byte-identical to
  arms **A** and **B** of `results/arc6_valuelayer.json`. `lost: []`,
  `gained: []`. (`test_gr4_the_live_mbpp_pass_ids_are_unchanged`, 44 s,
  green.)
- **Structural:** the synthesis-seed diff is confined to `ps_move_mark` and
  `ps_move_select`; `where`, `match`, and every node/edge/production are
  byte-identical to the committed manifest.
- **Arithmetic:** the added term evaluates to exactly `0.0` for every
  unsignatured candidate.
- **Bench:** `tests/test_prog_moves_migrated.py` (28), the arc-4/arc-5 named
  regression sweep it drives (492 node ids), `test_exact_first`,
  `test_verdict_discrimination`, `test_budget_isolation`, `test_retrieval`,
  `test_reject_informs_repair`, `test_prog_property`,
  `test_prog_synthesis_battery`, `test_prog_synthesis_selfimprove` — **198 green** across the seven
  pin files after the reconciliation in §6, and the goal-residual suite
  itself **31/31 green**.

---

## 6. Reds: what moved, what did not, and what was already red

**Seven seed-version pins** asserted `program_synthesis.json` `version ==
"1.11.0"`. The version bump to `1.12.0` is correct (a real seed change without
a version bump is worse than the pin churn), so the pins were **reconciled,
each with a dated in-line note naming this rung** — the sanctioned "only tests
change; drifted pins are reconciled in the improvement direction with dated
notes". Files: `test_prog_moves`, `test_exact_first`,
`test_verdict_discrimination`, `test_budget_isolation`, `test_retrieval`,
`test_reject_informs_repair`, `test_prog_property`. **No behavioural
assertion was touched anywhere.**

**Pre-existing reds this rung did NOT cause and does NOT absorb**, established
by re-running with the pre-patch seed restored:

- `tests/test_arc6_valuelayer_migrated.py` — **29 red.** This file gates the
  list/tuple value layer, which is **not present in this tree** (§7). Red
  before this rung; red identically after.
- `tests/test_arc6_tier0_migrated.py::test_no_python_decision_was_added` —
  red *before* this rung, on `M domains/prog_moves.py` already dirty in the
  working tree. The gate asserts `git status --porcelain domains seeds` is
  empty, so it goes red for any later rung that touches either directory by
  design. **Not edited**: narrowing it to accommodate this rung would be
  absorbing a gate, and it is not this rung's gate to move.
- The named sweep's two known out-of-scope pins
  (`test_descent_widening_migrated`, `test_mbpp_baseline_migrated`, both
  `'sum_of_two' == 'range_sum_spine'`) are in the sweep's own
  `_KNOWN_OUT_OF_SCOPE_FAILURES` and are unchanged.

---

## 7. THE PREMISE CORRECTION — the engine is not the one this rung was briefed with

> **SUPERSEDED 2026-08-03 (coherence). READ §10 FIRST.** This section is
> preserved verbatim as the record of what was measured and believed on the
> incoherent tree. Its *measurements* were honest and reproducible; its
> *conclusion* — that the brief's engine and its 48 were "false in this
> worktree" — inverted cause and effect. The brief was describing the tree that
> should have existed; the worktree had lost its binary. Two claims below are
> now reversed: **"GR4's bar is the 36"** (it is the 48) and **"The row-verdict
> residual is LIVE, not stale"** (it is stale). Everything else in this section
> stands, including the archived-binary note, which is what made the repair
> possible at all.

The brief stated *"Current engine is `8311d4356082…`"* and registered GR4 as
*"the 48 current pass ids"*. **Both are false in this worktree, and the
discrepancy is recorded rather than absorbed.**

Measured, before any change was made:

| | this tree | `arc6_valuelayer.json` arm A | arm B | arm C |
|---|---|---|---|---|
| engine sha256 | `48da7257f35d…` | `48da7257f35d…` | `8311d43560…` | `8311d43560…` |
| pass ids | **36** | 36 | 36 | 48 |
| accepted ids | 82 | 82 | 82 | 95 |

The live pass list and accepted list are **set-equal to arm A's**, and the
value layer is demonstrably absent — `s.add_node("X", {"lst":[1,2,3],
"tup":(1,2,3)})` reads **both back as `tuple`**. The twelve ids arm C gained
(`161, 249, 257, 272, 290, 393, 413, 418, 436, 450, 457, 460`) are exactly the
set difference. `engine_provenance` reports `source_match: "own"` and
`stale_rust: []`, so the Rust *source* in this tree is the pre-value-layer
source too: this is **A1.1's registered hazard realised** — *"`_native.abi3.so`
is a single gitignored file that every build overwrites"* — and the arm-C
binary is not on this machine's path.

Consequences, all of them registered rather than papered over:

- **GR4's bar is the 36**, held as a list in
  `tests/test_goal_residual_migrated.py::BASELINE_PASS_IDS`, never as a count.
- **The row-verdict residual is LIVE, not stale.** Its condition
  (`value_layer_list_eq_tuple == "1"`) is measured true *in this process*, so
  the mechanism correctly reports that the refutation still applies here. The
  tempting write-up — "arc C superseded it, so it lapsed" — would have been a
  claim about a different engine. The gate asserts the measurement and would
  fail loudly, with instructions, if the value layer ever changes underneath
  it.
- The engine actually used was archived out of tree before anything was run
  (`~/ozma-engine-archive/_native.abi3.so.48da7257…`).

---

## 8. Files

| file | what |
|---|---|
| `seeds/goal_residuals.json` | **new.** 33 nodes (16 `SignatureVocab`, 3 `ReachClass`, 1 `ResidualPolicy`, 6 `GoalResidual`, 7 `ResidualCondition`), 7 `holds_under` edges, 1 production, 5 `gr_*` rules |
| `seeds/program_synthesis.json` | v1.11.0 → v1.12.0; `ps_move_mark` +1 effect, `ps_move_select` weight term |
| `domains/goal_residual_ingest.py` | the mechanical ingest adapter — spec table of dotted paths, `build_residuals`, `probe_facts` / `install_facts`, `DELIBERATELY_NOT_INGESTED` |
| `tools/build_goal_residual_seed.py` | emits the seed (vocab + ingested residuals + rules); regeneration is gated byte-identical |
| `tools/patch_ps_move_select_residual.py` | the surgical `ps_move_select` weight substitution, re-runnable |
| `scripts/arc6_goal_residuals_report.py` | writes the results artifact, including the GR1/GR2 scenes measured live |
| `tests/test_goal_residual_migrated.py` | 31 gates (30 fast + 1 `slow` live MBPP) |
| `results/arc6_goal_residuals.json` | the artifact |
| `results/arc6_verdict_gr_baseline.json` | GR4's **before** snapshot — full 257-task split, pre-patch seed, 36 pass ids |
| `results/arc6_verdict_gr4_gate.json` | GR4's **after** snapshot — same split, patched seed, the same 36 |
| `domains/seed_registry.py` | +1 `REGISTRY.register` |

---

## 9. Honest residuals of this rung

- **The six arc-6 residuals are at a coarser grain than any candidate the live
  synthesis pipeline currently mints.** `ps_move_select` is wired and
  demonstrated, and the matcher is grain-agnostic (any node carrying `sig_*`
  attrs enters), but nothing in `domains/prog_moves.py` stamps a signature
  today — so in a normal MBPP run the mechanism is inert by construction. That
  is the correct state for a no-regression rung, and it is also the honest
  limit of the claim: **arc-planning goals are not yet minted as graph data,
  so there is no live arc-grain collapse for these six to steer.** Minting
  them is the obvious next rung and was deliberately not smuggled into this
  one.
- **`RESIDUAL_SCALE = 100` and the three `reach_class` factors are authored**,
  not measured. They are graph data (`ResidualPolicy`, `ReachClass`) and
  tunable without touching a rule, and the write-up says so rather than
  dressing them as findings.
- **A residual's `stale` flag is recomputed, but nothing re-measures.** The
  mechanism can tell you a ceiling no longer describes the world; it cannot
  re-run the ceiling. Closing that loop (stale residual → mint a
  re-measurement goal) is the same shape as `codebook_epoch` re-arming decode,
  and is not built here.
- **`fact_equals` conditions on artifact presence check the file, not its
  content sha** in the shipped facts (the sha comparison is supported by
  `probe_facts(expected_shas=…)` but not wired by default). A re-measurement
  that overwrote an artifact in place would not lapse those four residuals.
  Named, not fixed.
- **Not absorbed, per the brief:** `sorted`-on-strings, `Eq(0.0, False)`, the
  `inputs_json` boundary. None were touched.

---

## 10. CORRECTION, 2026-08-03 — THE TREE WAS MADE COHERENT, AND THE ROW-VERDICT RESIDUAL LAPSED BY ITSELF

Full account: `PROGRAM_SYNTHESIS_ARC6_COHERENCE.md`. This section states, in
this document's own terms, **what it said, what it says now, and why**.

### 10.1 What changed in the world

The rung was built and measured against engine `48da7257f35d…` **with the
value-layer adapter patch toggled off** — a tree whose gitignored binary did
not match its own committed source. §7 recorded the discrepancy accurately and
drew the wrong lesson from it: it treated a *damaged* tree as the *reference*
tree.

The tree has since been made coherent (not by this rung, and not rebuilt):
engine `8311d4356082acf4f70fab61a6e943d3dcecbd404d6e90c4f72ccc9486936df0`
restored from the out-of-tree archive — the binary the value-layer results were
actually measured on — plus the value-layer adapter edits in
`domains/prog_synthesis.py`, `prog_moves.py`, `prog_retrieval.py` restored from
HEAD. Verified live, in-process:
`add_node({"lst":[1,2,3],"tup":(1,2,3)})` reads back **`list` and `tuple`
distinctly**. `tests/test_arc6_valuelayer_migrated.py` is **35/35**.

### 10.2 The reversal, stated plainly

| | §7 said (engine `48da7257f35d`) | now measured (engine `8311d4356082`) |
|---|---|---|
| `value_layer_list_eq_tuple` | `"1"` | **`"0"`** |
| `arc6.verdict.row_verdict_seed_only` | **LIVE** | **STALE** |
| GR4 baseline pass ids | 36 | **48** (the registered bar) |
| the other five residuals | live | live, unchanged |
| GR1 collapse readings | 63.0 / 0.0, B wins, not-a-veto | **byte-identical** |

**The lapse is the mechanism working, and it is the first unprompted one.**
Every GR2 demonstration in §5 was *staged* — a fixture shape added, a payload
written, a fact hand-flipped. This one was not. A condition was falsified by a
change made for an entirely unrelated reason (restoring an engine), and the
residual went stale on its own in the next `run_rules` fixpoint. §4 said *"a
residual that cannot lapse is a lie with a long half-life"*; this one could,
and did.

**It also means the refutation the residual holds no longer applies.** The
row-verdict ceiling (`arc6_verdict_pricing.json`: NO-GO, 12 of 15 false
accepts) was measured under list/tuple collapse. That collapse is gone, and
per §4 **staleness is not falsity** — it means the measurement no longer
describes the world and must be re-made before it may be used again. It is not
re-made here; nothing in this arc re-prices the row verdict.

### 10.3 The six red gates, and what each one was

All six were **wrong-world pins**. **None was a defect in the residual
mechanism.** Five were pinned to the incoherent tree; the sixth was pinned to a
reference point that its own commit destroyed.

| gate | why red | disposition |
|---|---|---|
| `test_gr2_the_value_layer_fact_condition_lapses_the_row_verdict_residual` | its own failure message: *"this tree's value layer no longer collapses list and tuple — the residual SHOULD then be stale; update this gate"* | **the gate's instruction followed.** Re-oriented: stale as shipped, then un-lapse → lapse, both directions in one scene |
| `test_gr2_all_conditions_hold_in_the_shipped_world` | one residual legitimately stale | re-pinned to the exact stale **MAP** of rids (never a count); still fails loudly if any *other* residual lapses |
| `test_gr2_HEADLINE_seam_c_lapses_when_the_math_codebook_is_populated` | seam C's lapse **passed**; the "every other residual is 0.0" clause tripped on the pre-existing lapse | re-stated as a before/after **DELTA** — strictly stronger, since it now also catches an un-lapse |
| `test_gr1_every_residual_discriminates_its_own_signature_from_every_other` | a *consequence*: a stale residual correctly charges nothing | **scope preserved, not narrowed.** The scene now runs twice — once with all six live (full LOO coverage retained) and once as shipped (staleness gating asserted too) |
| `test_gr4_the_live_mbpp_pass_ids_are_unchanged` | pinned 36; coherent tree measures 48, `lost: []` | re-pinned against a **freshly measured pre-patch baseline on this engine**, not against the patched run |
| `test_gr4_the_synthesis_seed_diff_is_confined_to_two_rules` | **not an engine issue.** It diffs the working tree against `HEAD`; committing the rung (`921b8967d3`) made `HEAD` contain the change, so `changed == []` | re-pointed to a fixed pre-rung commit (`d4177b30ab`, seed v1.11.0) so the confinement claim stops self-nullifying on commit |

`tests/test_goal_residual_migrated.py` is **31/31**. No assertion was widened;
no coverage was dropped. Two gates are now stronger than they were.

### 10.4 What was re-measured, and under which sha

- `results/arc6_goal_residuals.json` — regenerated on `8311d4356082`, with
  `engine_sha256` recorded at top level. The prior reading is kept **verbatim**
  under `superseded_measurement_48da7257` with its own engine sha and
  `why_superseded`; it is not deleted and not overwritten in place.
- `results/arc6_verdict_gr_baseline_8311d435.json` — **new.** The pre-patch
  seed (v1.11.0, sha `5302b959daf2`) rerun on the coherent engine: **48 pass /
  95 accepted**, set-equal to arm C of `results/arc6_valuelayer.json`. This is
  what makes GR4's bar "unchanged" rather than "48".
- `results/arc6_verdict_gr4_gate.json` — regenerated by the gate itself on the
  coherent engine: the same 48 / 95. `lost: []`, `gained: []` against the
  pre-patch arm, on both the pass list and the accepted list.
- `results/arc6_verdict_gr_baseline.json` (the `48da7257` snapshot) is **left
  untouched** — it is a valid measurement under a condition that no longer
  holds, and a historical record is never converted.

### 10.5 Standing consequence

**A results document must name the engine it ran on AND assert it, not merely
record it.** §7 named `48da7257f35d…` correctly and still reached a false
conclusion, because naming a sha proves only which binary ran — not that it was
the *right* binary for the committed source. `engine_provenance` already
computes the answer (`source_match`), and in this rung it reported `"own"`
against a *pre-value-layer Rust source* that matched the pre-value-layer
binary — internally consistent, externally wrong. **The check that would have
caught this is a behavioural probe of the semantics the rung depends on**
(`probe_facts`' list/tuple read-back), which this rung already had and used as
a *condition* rather than as a *precondition*.
