# Functional substrate establishment plan

**Status:** active execution plan; bounded synthetic Stage 2 scheduling and
notification-mechanism gates have passed, while natural-task locality and
stages 0–7 acceptance evidence remain open. This
plan turns the evidence limits in
[`TRACTABILITY_SUBSTRATE_ASSESSMENT.md`](TRACTABILITY_SUBSTRATE_ASSESSMENT.md)
into an ordered programme for establishing what the substrate can do
functionally, under which workload conditions, and at what cost. It complements
the broader
[`SUBSTRATE_CAPABILITY_AND_TRACTABILITY_MEASUREMENT_PLAN.md`](SUBSTRATE_CAPABILITY_AND_TRACTABILITY_MEASUREMENT_PLAN.md),
which remains the canonical measurement schema and evidence catalogue.

## Objective and claim boundary

Establish a reproducible, source-current functional envelope for selected
substrate operations by connecting each task outcome to its actual execution
path, correctness oracle, structural conditions, resource cost, and failure
behavior. “Functional” means an authored task completes through the declared
substrate path and produces an independently checkable result; it does not mean
general intelligence, universal tractability, or production readiness.

The final deliverable is a capability-and-tractability map with three explicit
states per claim: demonstrated within envelope, refused/unsupported outside
envelope, or unknown. No unknown value is imputed as zero. Existing reports are
provisional until their source/build/workload hashes are confirmed against the
current checkout.

## Execution sequence

| Stage | Work and gate | Exit evidence |
|---|---|---|
| 0. Baseline and ownership | Refresh the callable-path inventory; classify each path as default, opt-in, diagnostic, or stale; name state owners and independent correctness oracles. Reuse the existing capability map rather than rebuilding it. | Current source/build hashes; resolved entrypoints and owners; test-to-path relevance audit; explicit unknowns and stale evidence list. |
| 1. Closure contract | Define fresh-name/mint effects for a restricted rule subset. Specify termination assumptions and a round/size/resource bound, or explicitly reject the rule set from bounded mode. | Accepted/rejected rule fixtures, analyzer/construction checks, fixpoint oracle, bounded-run tests, and a theorem/claim limited to the supported subset. |
| 2. Structural locality | On at least two preregistered representative workloads, define frame, boundary state, cut objective, and hierarchy construction/update. Compare partitioned execution to full-graph execution after repeated mutations. | Frame and separator distributions, cross-frame dependency recall, cut-maintenance cost, failure cases, and exact result/state parity. If small cuts are absent, stop assuming locality and revise the tractability model. |
| 3. Bounded inference | Revalidate CAN exact inference and refusal thresholds on current source; measure decomposition cost, width, factor arity/domain size, memory, and scaling. Add another inference family only if it can reuse the validated decomposition contract. | Exact agreement with exhaustive/independent oracles within the declared envelope; explicit refusal outside; width/node scaling curves and no silent approximation. |
| 4. Recognition and transform | Select high-value rung 1–2 paths; document algorithms and enforce declared frame/pattern limits, with measured fallback or refusal beyond them. Include adversarial patterns. | Correctness/parity tests, cost curves, worst-case controls, and explicit supported-envelope metadata for each path. |
| 5. Induction economics | Separately instrument residual incidence, rung transitions, candidates/depth, CPU/memory, mint rate, and later reuse on a preregistered ordinary/novel/adversarial distribution. | Distribution and tail-cost results separating held-structure application from acquisition; timeout/refusal behavior. Do not convert “rare in sample” into a guarantee. |
| 6. End-to-end CPU envelope | Combine only validated operations in frozen authored workloads. Attribute wall/CPU time, allocations/RSS, rule work, mutation, inference, and startup; vary topology, rule density, locality, mutation, cache state, and input size. | Reproducible hardware/software/workload profile; quality and resource curves; controlled baseline and ablations; no extrapolated node-scale or simulator-cadence claims. |
| 7. Matched external comparison | Compare against concrete small CPU LLM and other relevant baselines on identical task inputs and quality criteria. Include acquisition/training, prompt/context, retries, energy/cost, latency, and deployment amortisation. | Frozen matched protocol, repeated trials/uncertainty, raw records and exclusions; capability-specific conclusions rather than a global cost-superiority claim. |

Stages 0–5 establish the bounded functional substrate claims. Stages 6–7
establish operational scale and comparative economics and are required before
any broad efficiency or practical-advantage claim. Stages 1 and 2 are the
critical early falsification gates: failure to bound closure or find useful
locality must change the claim, not trigger a search for friendlier examples.

## Cross-stage controls

- Freeze task families, sample selection, source/build identity, and success
  criteria before confirmatory measurements.
- Keep a full-graph/full-recompute oracle wherever an optimized or partitioned
  execution path is tested; compare complete semantic state, not only headline
  outputs.
- Report cold and warm startup separately from steady-state operation, and
  distinguish measured engine time from simulator or external-service cadence.
- Include instrumentation overhead controls and preserve raw per-run records.
- Make resource caps and refusal semantics explicit; a timeout is not a correct
  answer, and a refusal is not a successful solve.
- Keep domain-specific, experimental, and opt-in mechanisms labeled as such.
- Do not modify default scheduling, inference, or mint behavior solely to make a
  benchmark pass; first preregister the semantic contract and parity oracle.

## Current execution evidence (2026-09-26)

The Stage 0 capability-map mirror check was rerun against the current working
tree with `.venv/bin/python scripts/build_substrate_capability_map.py --check`.
It passes with 16 inventory rows, 77 resolved source links, 44 linked test
references, 197 linked runners/analyzers, and no unresolved source links,
missing evidence, or validation errors (JSON SHA-256
`9e9ee2a2cba94418c8cc8b772cdfb0e8f8eb1f9e2c18009b253137b16a78b7a6`). This
validates inventory structure and link resolution only. It does not establish
that linked tests exercise their named paths, that historical reports match
the current source/build, or that owner/activation classifications are
complete; those remain Stage 0 audit work.

Stage 2's current synthetic scheduler slice is recorded in
[`SUBSTRATE_SCOPED_NOTIFICATION_REQUEUE_ATTRIBUTION_RESULTS_20260926.md`](SUBSTRATE_SCOPED_NOTIFICATION_REQUEUE_ATTRIBUTION_RESULTS_20260926.md).
The independent raw-turn analysis passes its source/build fingerprints,
counter conservation, and exact event/full projection gates across 12
chain/tree/star cells. At 64 frames, all have 256 median event turns, 128
no-progress turns, 128 self-requeues, and zero duplicate suppressions; the
star requires 14,123 candidate tests and 106,927 term evaluations, compared
with 2,591 and 18,515 for the chain. This narrows the synthetic scheduler
optimization target but does not establish natural-frame locality or safe
notification coalescing. The follow-up guarded self-requeue intervention is
recorded in
[`SUBSTRATE_SCOPED_SELF_REQUEUE_SUPPRESSION_RESULTS_20260926.md`](SUBSTRATE_SCOPED_SELF_REQUEUE_SUPPRESSION_RESULTS_20260926.md):
an opt-in harness suppresses self-enqueue only when the exact one-hop ownership
set is stable around local closure. All 60 scale cases preserve notifications
and exact full projections; a rule-authored ownership-insertion control retains
the self-requeue and processes the new member. At 64 frames, event turns halve
on chain/tree/star, while candidate work falls by about 29%, 27%, and 5%,
respectively. The default scheduler is unchanged. Stage 1 bounded-closure
evidence and natural-task partition evidence remain open. A Stage 1 source audit
also corrected two finite-key closure-checker false-acceptance paths: edge
labels no longer count as bound endpoints, and an empty-attribute `AddEdge`
cannot be admitted when it could overwrite attributes on an initial edge of
that type. The new native collision probe confirms one state-changing progress
step with no edge-count increase. The checker now takes the complete initial
node-ID inventory, counts isolated nodes, and rejects duplicate IDs, omitted
edge endpoints, and duplicate/malformed edge facts. Ten self-check fixtures
and five focused tests pass; refreshed native loader and interacting-rule
replays are within the bound. The fragment analysis now states a finite-
progress proposition with explicit initial-graph, insertion-only, and native
effect assumptions: at most `R + E(N+R)^2 - M` progressing applications.
This is an abstract progress theorem, not proof of scheduler access recall or
that `fixed_point` equals the intended least closure. The full Stage 1 exit
gate therefore remains open.

## Immediate next work

### Thoughtexperiment fanout release and capability boundary (2026-10-03)

The predecessor-dependent fanout v1.1 gate is complete: 216 source-locked
workers and 14 independent checks pass across frame count/topology, candidate
fanout, noise-node scale, and both branch backends. The test proves substrate
outcome-guided selection from evaluator-supplied candidates, exact scoped
closure/oracle parity, isolation until revision-checked residual return, and
atomic stale rejection. It does not prove candidate generation, learned frame
discovery, or self-improvement. Corrected `mallinfo2` measurements show that
live allocator use returns to baseline after branch release even when PSS stays
elevated; full results are in
[`THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_V1_1_RESULTS_20261003.md`](THOUGHTEXPERIMENT_PREDECESSOR_FANOUT_V1_1_RESULTS_20261003.md).

The outcome-blind four-family panel has since been repeated on current sources:
all 104 held-out candidate instances were scored once, orders were frozen
before held-out evaluation, and the independent analysis passed 7/7 checks.
Experience ranking improves on frozen ranking but trails default order and
same-target memoization, with materially higher acquisition cost. Candidate
generation still uses a fixed edit vocabulary. The multi-edge identity-aware
guard passes a current-source replay: actor+verb identity preserves both
distinct held-out outputs while the relation-only control suppresses one. The
target and identity cue remain supplied. A current-source site-extraction
sweep confirms the singleton/pair/full-set count formula through 256 fields
(32,897 attribute sites, 44 ms median), with constant/computed fields
excluded. The crossed full-composer gate now covers 2–32 fields and 0–10,000
unrelated nodes: 45/45 trials select the supplied actor+verb guard, with 530
candidate sites and 17.77 ms median at 32 fields/10,000 nodes. The numeric
residual cue panel also passes 13/13 cases: four opposite-vector examples
produce held-out repairs, eight ordinary controls abstain, and one absent-target
control derives a cue but emits no proposal. No action-pair codebook is supplied
to the candidate branch, but the vector-opposition formula and cue remain
authored. A first supervised induction run through `domains.generator.synthesize`
found a fitting predicate in all five random draws, but only one generalized
exactly to 1,296 disjoint fractional cases. Four x-only hypotheses produce
180 false positives each; the one exact hypothesis costs 1.19 s versus
5–68 ms for underfit hypotheses. A coverage-directed replication includes
x-only/y-only separating negatives and generalizes exactly in all five workers;
median search is 1.14 s over 6,587–10,638 explored terms. The design comparison
is small and nonpaired. The cross-stage integration now embeds those frozen
Terms in native residual rules and crosses five Terms with 13 task cases:
20/20 positive cues and held-out repairs pass, 0/40 ordinary negative cues,
and all 65 branch isolation/return checks pass. The operator/cue mapping and
training labels remain authored. An order-balanced active-query replication
then identified an exact singleton in 150/150 paired blocks, versus 111/150
for sequential randomized querying, using medians of 3 versus 4.5 labels.
Those blocks are nested within only five training panels and operate inside
supplied 9–10 member version spaces; they do not resynthesize after
counterexamples. An out-of-grammar diagnostic found that both policies can
terminate with false singleton hypotheses or empty version spaces. Entropy
reduction is therefore not a model-adequacy test. See the
[active-query results](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_1_RESULTS_20261003.md)
and [model-misspecification results](NUMERIC_OPPOSITION_MODEL_MISSPECIFICATION_V1_1_RESULTS_20261003.md).

The counterexample-guided resynthesis gate now completes that loop on the same
five panels: all five rebuilt to an exact singleton on the disjoint fractional
holdout after two or three oracle labels, across 16 total synthesis rounds
(8.48 s median per round). Independent replay passes. The full protocol,
source lock, capture, and analysis are in the
[counterexample-guided results](NUMERIC_OPPOSITION_CEGIS_V1_RESULTS_20261003.md).
This is positive evidence
for iterative resynthesis when the target is expressible in the supplied
grammar, with substantial repeated search cost. A paired adequacy follow-up
shows the boundary: with an XOR-of-axis-oppositions target outside that grammar,
four of five workers reached false singletons and one returned an empty space;
all five in-grammar controls solved exactly. See the
[model-adequacy results](NUMERIC_OPPOSITION_CEGIS_MODEL_ADEQUACY_V1_RESULTS_20261003.md).
The grammar-expansion follow-up now tests that policy. At size cap 9, adding
`Not` still produced no exact holdouts; size 11 admitted the target syntax but
one resynthesis remained insufficient. Continuing against a frozen reserve
pool and resynthesizing on each new counterexample produced exact holdout
behavior in all five workers. Post-capture scoring found exact candidates after
4–9 added labels (median 6), but the policy used the full 12-label budget in
all five because it had no valid stopping signal. The operator and expansion
rule were authored. See the
[grammar-expansion results](NUMERIC_OPPOSITION_CEGIS_GRAMMAR_EXPANSION_V1_RESULTS_20261003.md).
The retrospective stopping replay now compares one through six consecutive
agreement labels. Four of five workers remained false at thresholds 2–4; one
remained false at threshold 5. Threshold 6 was exact on all five holdouts but
saved only four of 60 possible labels. This is a small, post-hoc tradeoff, not
a validated stopping rule. See the
[stopping replay results](NUMERIC_OPPOSITION_CEGIS_STOP_RULE_V1_RESULTS_20261003.md).
The first prospective three-family panel now gives a mixed transfer result:
absolute-value and additive equality generalized exactly in 5/5 workers each;
XOR generalized in 1/5, with four search timeouts after the shared operator
ladder expanded to `Plus`. The additive holdout was corrected to include both
classes before interpretation. The [cross-family results](STRUCTURAL_INDUCTION_CROSS_FAMILY_V1_RESULTS_20261003.md)
record the valid capture. This indicates useful transfer across two numeric
relations under the frozen policy, alongside a search-order/resource failure
on the third. Next freeze an improved stopping and expansion policy using
development tasks, then evaluate it on unrelated confirmatory families and a
non-numeric task without changing primitives after seeing holdouts. These
remain synthetic results, not
natural-task locality or autonomous acquisition; process RSS is coarse. Then
repeat scaling with independently generated task rules and peak/live memory
accounting. Separately, extend the validated fanout
harness beyond 10,539 nodes and measure repeated/concurrent branches under a
memory cap. Substrate-owned evaluation and choice are partly demonstrated;
proposal acquisition and measurable improvement remain open. See the
current-source [identity results](THOUGHTEXPERIMENT_SUBSTRATE_EDGE_ATTRIBUTE_IDENTITY_CURRENT_SOURCE_RESULTS_20261003.md), [site-scaling results](EDGE_IDENTITY_SITE_SCALING_CURRENT_SOURCE_V1_1_RESULTS_20261003.md), [numeric cue results](RESIDUAL_TO_COMPOSER_NUMERIC_CUE_V1_RESULTS_20261003.md), [random relation-learning results](NUMERIC_OPPOSITION_RELATION_LEARNING_V1_RESULTS_20261003.md), [coverage-directed relation-learning results](NUMERIC_OPPOSITION_RELATION_LEARNING_V1_1_RESULTS_20261003.md), [learned-Term integration results](LEARNED_NUMERIC_CUE_COMPOSER_INTEGRATION_V1_RESULTS_20261003.md), [four-family selection results](THOUGHTEXPERIMENT_BLINDED_PROPOSAL_UTILITY_V1_3_RESULTS_20261003.md), [grammar-expansion results](NUMERIC_OPPOSITION_CEGIS_GRAMMAR_EXPANSION_V1_RESULTS_20261003.md), and [cross-family induction results](STRUCTURAL_INDUCTION_CROSS_FAMILY_V1_RESULTS_20261003.md).

### Fresh string-composition PBE (2026-10-03)

A new, prelocked 18-task suite tested six two-stage string compositions. The
independent audit passed all 126 oracle rows and replayed main outcomes
exactly. Main solved 1/18 heldouts, retrieval bypass 0/18, and the 500k-candidate
escalation 2/18; each arm still had two accepted false programs. Five strata
had no exact pass in any arm. This adds a current fresh-task observation beyond
the older list/string fixtures and shows that route scaling recovers little
while spending more candidates. See the
[fresh string-composition report](STRING_COMPOSITION_FRESH_PBE_V1_RESULTS_20261003.md). A separate direct-execution audit supplied the six intended ASTs and got 18/18 exact tasks over 126 rows with zero evaluator errors. The independent replay passed. This separates native execution support from the current P4 candidate-acquisition/selection failure on this suite; it is not a learning success. See the [native execution audit](STRING_COMPOSITION_NATIVE_EXECUTION_AUDIT_V1_RESULTS_20261003.md). Retrospective stage attribution shows recognition 18/18; the main route retrieved three exemplars (two false accepts) and capped enumeration on 15/15 remaining tasks. Raising the no-retrieval cap to 500k returned five candidates, only two exact, while 14 tasks remained gaps and two were accepted incorrectly. Candidate streams are not logged, so next instrument candidate-level traces and independently audit verification. See the [stage attribution](STRING_COMPOSITION_P4_STAGE_ATTRIBUTION_V1_20261003.md). A preregistered stress sample scored every accepted artifact on 50 new strings per task: 258/600 rows correct (43%), and only 2/12 artifacts exact on all 50. The artifacts are duplicated across arms and cover only two families, so this is a verifier-risk diagnostic rather than an independent capability estimate. Expand validation before treating small-heldout exactness as generalization; candidate-level trace instrumentation remains open. A bounded exhaustive audit then scored all accepted programs over 41,790 inputs (strings up to length five over task-specific five- or four-symbol alphabets): the two escalated token-reversal candidates were exact on 1,365/1,365 inputs each; all ten casefold-count artifacts failed, with 0–46.9% accuracy over 3,906 inputs each. This is a finite-domain result, not a Unicode/unbounded proof. See the [bounded exhaustive audit](STRING_COMPOSITION_BOUNDED_EXHAUSTIVE_V1_RESULTS_20261003.md). See the [accepted-program stress results](STRING_COMPOSITION_ACCEPTED_PROGRAM_STRESS_V1_RESULTS_20261003.md). Prefix analysis flags 8/12 artifacts by two independently generated validation rows and all ten observed non-exact artifacts by row 14; the ten include repeats of only three unique candidate programs. This supports adaptive, larger validation in the benchmark but is not a production threshold estimate.

### List PBE source-current replay (2026-10-03)

The 30-task list-PBE composition suite was replayed on current source and
native build under the original three arms. All 90 task/arm outcomes, statuses,
and constructions match the earlier amended report exactly. Each arm remains
at 14/30 exact holdout passes, two accepted false programs, and 14 gaps; the
current accepted-IR analyzer independently audited 48 stored IRs. The result
confirms stability across source drift on this suite, not broader transfer or
natural-task capability. See the [source-current replay report](SUBSTRATE_LIST_PBE_CURRENT_SOURCE_REPLAY_RESULTS_20261003.md).

### Current-map call-path triage refresh (2026-09-29)

The static capability-map test-link triage now has a selectable output path,
so current evidence is written separately rather than overwriting the
historical 2026-09-28 report. Against the current map it covers **26 rows / 65
functional test links**, with **45** files containing candidate direct
callable-name matches and **20** without. The refreshed inventory mirror
passes with no unresolved source links, missing evidence, or validation
errors. A scoped manual review now classifies conversation/production and
language links, distinguishing component evidence, adjacent mechanisms, and
an unrelated handwriting experiment. A second pass manually traced all three
native cognitive-runtime links through the extension API and measurement
harness: those tests exercise `run_cycle` and `run_cognitive_tasks` behind the
Rust boundary without directly naming the Rust entrypoint symbols. The scoped
audit now covers ten links; details are in
[`SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md`](SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md).
The focused native-runtime linked test batch passes **59/59** on the current
tree. This validates those tests, not every native-runtime capability-map
entrypoint or the remaining 55 linked tests.
This is Stage 0 progress only: direct-name hits still require reachability
review, the remaining capability/test links are unaudited, and no map row is
promoted to fully audited coverage. Conversation cognition/production and
functional substrate establishment remain concurrent workstreams.

### Capability-map mirror revalidation (2026-09-29)

After the current source changes, the Markdown-source inventory was regenerated
into its JSON mirror and `.venv/bin/python
scripts/build_substrate_capability_map.py --check` passes: **26** inventory
rows, **224** resolved source links, **65**
linked test references, **245** result-linked runners, no unresolved source
links, no missing evidence, and no validation errors. The current map JSON
SHA-256 is
`8c53b3888c06c5afe357a023d2f1567b496e2b434edd576f76cdb77bc7482941`.
This refresh establishes inventory/link integrity only; it does not upgrade
call-path reachability, test relevance, report/source provenance, or any
functional capability claim. Stage 0 audit and Stage 2 natural/authored-task
locality remain open, concurrently with conversational cognition and
production work.

Stage 0's existing capability map and JSON mirror currently validate with no
unresolved source/evidence links; the inventory remains explicitly in progress
and historical reports still require per-claim source/build review. Stage 2
now has bounded synthetic topology, cross-frame dependency, owner-notification,
and scheduler-cost evidence. The guarded intervention reduces repeated stable-
owner turns without changing notifications or full-state results in the
measured fixtures, but star fanout remains costly and no default integration is
authorized. This does not establish locality in natural or authored task
frames, or scheduler completeness. The next concrete Stage 2 work is to inspect
real scoped call sites for the same owner-saturation/invalidation contract;
that audit finds the CAN helper directly runs one owner's native fixpoint and
does not use a caller-managed notification queue, so this experiment has no
immediate production integration seam. Next derive partitions from a structural
census and compare them with authored workload dependencies.
Keep Stage 1 closure assumptions as a parallel prerequisite, not an inferred
consequence of scoped scheduling results. CAN exact inference remains bounded
to measured low-width families; no substrate-wide termination, tractability,
or resource guarantee follows from the current evidence.

### Stage 0 test-link relevance triage (2026-09-28)

Added `scripts/audit_substrate_test_refs.py` to statically compare Python AST
call names in capability-map test links against that row's audited callable
names. The first pass found five `tests/evaluation/` links that validate P2/P0A
protocols, not the substrate call paths; the map builder now classifies these
separately and preserves them as evaluation evidence. On the refreshed map it
processes 16 capability rows and 39 linked functional-test files; 32 files
contain at least one matching call name. The planning/action row now correctly
has no functional-test link (its three P2 references are protocol-only). This
is only triage: same-name calls do not establish runtime reachability to the
named Rust path, and files without a match may exercise it indirectly through
helpers, fixtures, or seed loading. No map row is upgraded to audited coverage.
The seven functional links without a name match have now been manually
classified: five do exercise a relevant integration path through wrappers or
native Term dispatch; one vision test covers a sibling graph-authored mechanism
rather than the listed primitives; one synthesis battery is mixed result
validation/live re-verification. The remaining manual audit is to inspect the
32 name-matched files for actual call reachability and narrow cross-row links.
See the [manual path audit](SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260928.md)
and machine-readable triage:
[`substrate_test_reference_triage_20260928.json`](../../../evaluation/reports/substrate_test_reference_triage_20260928.json).

### Stage 2 locality evidence audit (2026-09-26)

Existing authored evidence narrows, but does not close, the structural-locality
gate. Bigville's v3.1 replay derives 100 five-Concept components from runtime
`causal_influence`; its dynamic-link follow-up injects ring, star, and random
cross-frame links and preserves exact event/full parity over seven checkpoints
and three fresh-process replicates per topology. This is useful mutation and
connectivity evidence, but the partitions are frozen before link insertion and
caller code supplies dirty-frame notifications. The conversation access trace
is a second rule family with paired trace parity, but only 14 of 46 possible
static writer-reader pairs are observed in its small samples; it does not
supply a validated frame partition. Conversation connected-frame stress is an
important counterexample: shared mutable candidate state breaks scoped/full
parity at N≥2, so this representation cannot be treated as a locality success.

Stage 2 therefore remains open. The next experiment should use two frozen
workloads (Bigville as the positive authored case; conversation as a negative/
repair case), derive candidate dependency graphs from measured execution
reads/writes plus ownership, and compare runtime/authored cuts against balanced
and min-fill baselines. Include repeated insertion, retraction, and reweighting
of boundary links; compare complete partitioned state against monolithic
closure at every checkpoint, with a deliberately omitted-boundary sensitivity
control. Record dependency recall, cut/boundary sizes, partition-maintenance
and closure costs, and refuse partitions where shared mutable state lacks a
sound ownership/boundary contract. Existing Bigville results may seed
development but must not be relabeled confirmatory evidence: freeze the
extraction and parity protocol before rerunning either workload.

The extraction, baselines, mutations, refusal rule, and parity gates are now
frozen in [`SUBSTRATE_AUTHORED_CUT_DEPENDENCY_COMPARISON_PREREG_20260926.md`](SUBSTRATE_AUTHORED_CUT_DEPENDENCY_COMPARISON_PREREG_20260926.md).
This completes protocol design only; the runner, independent analyzer, input
lock, and confirmatory captures remain to be produced before Stage 2 can
advance.

### Concurrent source-current regression check (2026-09-29)

While the conversational language-neutral/Phase 8 runner suite passed **51/51**,
the native CAN and solver-dispatch regression batch passed **24/24** with
`.venv/bin/pytest -q tests/test_can_native_reimplementation.py
tests/test_solver_dispatch_migrated.py`. This confirms those checked code paths
still pass their existing functional tests on the current tree; it does not
validate every capability-map entrypoint or advance Stage 0 audit completion.
Stage 2 authored-task locality and all untested/uncertified functional claims
remain open. The two workstreams were verified concurrently, not serially
substituted.

The Stage 0 manual test-path audit also now covers the two linked native
fixpoint tests: one directly verifies recursive edge closure to a zero-work
second pass, and the other verifies instrumented native mutation-effect arms.
Both pass **2/2**. This advances path classification for those fixtures only;
the tests do not prove unrestricted termination, scheduler completeness, or
the adapter wrapper path. See
[`SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md`](SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md).
It now also directly audits the mapped solver-decomposition success/refusal
integration through the authored-statement adapter (**2 focused tests pass**).
That validates a bounded synthetic width-gate path, not natural locality or
automatic partitioning; Stage 2 remains open.
The source-current mirror now carries **245** result-linked runners and **195**
result documents (up from 241 and 193 in the prior refresh), with 26 rows,
224 resolved source links, 65 linked test refs, and no unresolved links,
missing evidence, or validation errors. This refresh followed the new Phase 8
target and test-path audit records; it does not promote any functional
capability claim.

### Stage 0 linked-test path review refresh (2026-09-29)

The scoped manual path audit now covers **14/65** linked test files. The
additional map link, `tests/test_fb_pipe.py`, is an explicit negative control:
inspection confirms it tests the Python shared-memory framebuffer writer and
does not exercise Rust `pipeline_runtime`, matching the capability-map row's
own evidence-boundary warning. It therefore adds no neural/operation-pipeline
coverage claim. The inventory and its 65 links remain intact; Stage 0 audit
completion and Stage 2 natural/authored-task locality remain open. This
substrate increment accompanies, rather than replaces, the source-current
conversational nominal-reference and Phase 7/8 checks recorded in the
conversational plan.

The linked solver-dispatch path review has also advanced to **15/65** files:
`test_solve_decompose_chains_from_solve_deduction` passed against three real
deduction schemas, a measured sparse-vs-overcoupled min-fill comparison, and
the live `solve_decompose` resolver path. This is bounded authored-task
integration evidence only; it does not establish natural partition discovery
or broad task-locality. Both the Stage 0 review and the separate conversational
cognition gates remain active concurrently.

The mapped rule-dependency/settlement link `tests/test_per_area_settlement_migrated.py`
is now reviewed and passes **17/17**. It directly covers opt-in native
`run_rules_settle` alongside global fixpoint parity, carried finite-budget
residuals, quiet-area no-work, and a selected vision workload. The entrypoint
remains default-off and has no committed production caller, so this advances
mechanism-path evidence only. Stage 0 manual review is now **16/65** linked
tests; production integration and broader scheduler guarantees remain open.

The episodic authored-rule test link is now also audited and passes **16/16**:
its live tick path verifies graph-resident event binding, provenance handling,
overlap marking, retrieval, replay, and working-memory gates. The newly added
cue-key index hint preserves tested same-cue collision marks and distinct-cue
non-overlap. This does not cover the separate Rust `MemoryFaculty` API or
natural memory utility. Stage 0 manual path review is now **17/65** linked
tests; the broader substrate gates remain open.

The `episodic_mark_overlapping_cues_for_conservative_completion` rule now
uses an engine-supported exact-key `IndexJoinHint`. The isolated N=128
unique-cue diagnostic fell **3,998→74 μs** with exact non-overlap behavior;
the single-key collision path remained **17.5 ms** and marked all 128 members,
so repeated-key grouping remains quadratic. This is a bounded native indexed-
join result, not general tractability evidence. Two fresh 74-event Phase 7
profiles retained identical observations and passed all six 150-MiB checks,
but their max conversation times (**210.96 / 183.97 ms**) remain over target.
The resource/latency gates and broader Stage 0/2 substrate gates remain open.

**Typed cue-overlap population (2026-09-29):** Seed 1.1.3 now distinguishes
generic stored episodes, typed episodic-working-memory traces, and the subset
with non-empty cue keys eligible for overlap comparison. This excludes legacy
message Episodes and unkeyed traces from an irrelevant/missing-key pair join
without removing them from memory. The episodic suite passes **18/18**; the
combined engine join-index and episodic mechanism batch passes **23/23**. A
fresh 74-event run reduced overlap-rule cost from **255.9 ms to 419 μs total**;
two current Phase 7 runs retain exact observations, pass all six 150-MiB
assertions at ~107 MiB, but still exceed the latency target (**202.68 /
204.86 ms**). This is concrete indexed-rule progress, not general substrate
tractability; Stage 0/2 and strict cognition-latency gates remain open.

The concurrent Stage 0 linked-test review also inspected and reran
`tests/test_vision_kernels.py` (**19/19**). Its native-extension integration
covers graph-backed image/kernel bridges, DSL-visible attributes, selected
convolution responses, provenance/pipeline chaining, and pooling/thresholding;
it does not establish WorldAdapter ingestion, all mapped vision primitives, or
task-level perception quality. The manually reviewed Stage 0 test-path count
is now **18/65**. This audit increment accompanies the still-open conversational
latency/comparative gates; it does not substitute for them.

The concurrent Stage 0 review next inspected and reran
`tests/test_curious_agent_vision_graph_migrated.py` (**1 passed, 7 skipped**).
The passing check covers only lazy no-frame behavior; all seven frame-dependent
tests skipped because optional `cv2` is unavailable. Stage 0 manual linked-test
review is now **19/65**, with those seven integration checks explicitly
unverified. This audit continues alongside the conversational gates.

The next concurrent Stage 0 path review inspected and reran
`tests/test_vision_change_migrated.py` (**5/5**). It covers the graph-authored
change-detection rung and sustained-channel control; it does not validate the
native `temporal_diff` primitive or general perception quality. Manual linked
test-path review is now **20/65**, while the conversational gates remain open.

### Full-seed conversation-path hotspot triage (2026-09-29)

An opt-in scale-audit pass on the late-corpus `defer_permission` turn
identified `curiosity_targets_ambivalent_nodes` as the largest single rule
workload (**347,765 Term evaluations**), followed by
`default_mode_mint_episode_context` (**91,698**). The same turn recorded
1,952,011 Term evaluations and 238,475 candidate tests overall. This maps a
concrete full-seed substrate hotspot encountered by the conversation workload;
it does not prove the rule is semantically overbroad or general tractability.
Audit its intended Microtheory/Concept scope and establish exact behavior
parity before changing candidate enumeration. Conversational and substrate
gates remain concurrent.

An adjacency snapshot immediately before that late turn found **10,810**
`Concept` nodes and **206** `Microtheory` nodes with `has_concept` members.
Across the 30 largest microtheories printed by the probe, their member Concepts
had no `state` attribute, while all had acquired `is_ambivalent`. This is
consistent with the rule's explicit source comment that absent state reads as
zero/ambivalent; it is therefore a real broad semantic classification, not
merely a stale candidate counter. Before narrowing the rule to state-bearing
CAN Concepts, decide whether unknown content Concepts are intended to count as
ambivalent and construct parity fixtures for both unknown-state and settled-
state cases. No scope change is made on this audit alone.

The current native `IndexJoinHint` only probes exact attribute equality, while
this rule requires both `abs(state) < 0.05` and `is_ambivalent != 1`; its
required `Microtheory -has_concept-> Concept` match also enumerates one binding
per membership edge. Therefore an equality join hint cannot preserve the
tested missing-state behavior or remove duplicate Concept bindings. A
semantics-preserving speedup needs a native candidate primitive for a
distinct-node existential / indexed complement (including missing attrs), or
an equivalent dirty-candidate mechanism, with parity tests for multiple
Microtheory parents, absent state, near-zero state, and settled state. Add an
explicit lifecycle test for later state changes before optimizing: the shipped
rule is idempotent after setting `is_ambivalent=1`, so its marker may not track
a subsequently changed `state`. Keep this as an engine substrate task; do not
approximate it in Python or narrow the rule by seed-name convention.

### Concurrent cognition optimization status (2026-09-29)

The functional-substrate work remains active alongside the conversational
manifold work; the latter does not replace this plan. Stage 0 manual linked-test
review is now **21/65**: `tests/test_agent_tools.py` passed 20/20, covering its
explicitly installed demo ToolBox/frame route, not default tool registration,
host-I/O containment, or a route census (see the [path audit](SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md)).
No map row was promoted by the conversational Argmax experiment. Its Rust
unit-test binary was linked with the installed Python 3.13 library and loader
path; all **56/56** `term::tests` pass. This validates local Term/cache
semantics, not production Phase 7/8 cost or substrate tractability. Continue
Stage 0 test-path review and the separately scoped Stage 1/2 functional
evidence work in parallel.

### Concurrent conversation/release-path evidence (2026-09-29)

The cognition path added a declarative literal equality probe to native
`IndexJoinHint` and measured four fresh, semantically identical 74-event
connected Phase 7 runs. Three maxima are below 150 ms, one is above; all four
resource assertion sets pass. This remains conversation-specific evidence and does not
close any substrate tractability or capability-map gate. The Stage 0 audit
also reviewed `tests/test_conversation_loop.py` and advances to **22/65**
manually reviewed linked tests. Its initial **13/14** result exposed the
reflective-release ordering mismatch; the source path now prioritizes the
supported `self_model_rule` receipt over unresolved-topic fallback, and the
full test passes **14/14**. This closes only that selected conversation path,
not any substrate tractability or capability-map gate. Both streams remain
active independently. See the [path audit](SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md)
and [cognition execution plan](../psychology_affect/CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

Final source-bound verification uses engine `a5aa1ea0812e`; its provenance
checks pass **9/10** (one expected skip), and the source-current conversation
suite passes **14/14**. Two additional connected Phase 7 runs retain identical
normalized observations and pass the 150-MiB checks; one of two maxima exceeds
150 ms. The matched Phase 8 v5 run preserves its prior semantic metrics and is
0/74 over 150 ms, while comparative evaluation remains blocked. These remain
conversation-path and release-path observations, not functional-substrate
acceptance evidence.

The concurrent Stage 0 review also completed the mapped context/identity path:
`tests/test_context_model.py` passes **5/5**. This supports only the listed
context-model and interlocutor-feed component route; Stage 0 manual review is
now **23/65** linked files, as recorded in the [path audit](SUBSTRATE_TEST_PATH_RELEVANCE_AUDIT_20260929.md).
Separately, current-tree conversational memory/learning scores remain 5/5 in
each supplemental probe dimension; that result is explicitly not counted as
substrate functional acceptance. Both tracks continue concurrently, with the
substrate Stage 0/1/2 gates still open.

The capability-map-linked conceptualizer test was also extended to call
`conceptualize_reply()` directly; all **12/12** cases pass. This improves
verified cognition-component coverage but does not establish universal live
release or promote a substrate-map capability. The manual Stage 0 review is
now **24/65** linked test files; Stage 0/1/2 remain concurrent and open.
The paired `test_conceptualized_converse.py` live route suite also passes,
yielding **20/20** for the direct entrypoint plus selected live consumers; this
is not a capability-map promotion or a proof of universal production release.

The next Stage 0 linked test, `tests/test_language.py`, was manually traced
through native lexical graph construction, authored Merge rules, and semantic
readback, then rerun at **13/13**. This establishes direct test-to-path
relevance for selected lexical/compositional language functionality, not the
full capability row; the manual Stage 0 review is now **25/65** linked tests.
In parallel, the conversation path removed a redundant scratch-graph rebuild
between lexical recognition and Merge. Its selected-path and full connected
74-event evidence is recorded in the [conversational execution plan](../psychology_affect/CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md)
and does not count as substrate functional acceptance. Both workstreams and
all their separate gates remain active.

### Source-current capability-map check (2026-09-29)

Revalidated the Markdown inventory/mirror after the latest source changes with
`.venv/bin/python scripts/build_substrate_capability_map.py --check`. The
check reports **27** inventory rows, **229** resolved source links, **65**
linked test references, and **281** result-linked runners. There are no
unresolved source links, missing evidence, or validation errors; the current
JSON mirror SHA-256 is
`539a4d5af25f09d165c30ef4b09154ba6b40e745fd9c5e04def4c2a72448db38`. Two
rows still have no linked test: visual image ingestion/frame-scoped settling
and planning/action selection. This confirms map/mirror integrity only; it
does not establish callable-path reachability or test relevance. The manual
Stage 0 review remains **25/65**, and Stage 0/1/2 functional acceptance stays
open concurrently with the conversational cognition/production gates.

### Numeric active-query gate (2026-10-03)

The supervised numeric-relation follow-up now closes a bounded active-query
gate. Five generated version spaces contain 9–10 hypotheses, and the exact
target is present in every pool. Maximum entropy identifies an exact survivor
in every worker with a median of two oracle labels; fixed-first takes one and
seeded-random takes four. All three policies end with exact survivors on the
1,296-case fractional grid and 13-case navigation transfer panel. Thus this
design shows no query-count advantage for maximum entropy, and its selector
cost is higher (3.13 ms median versus 0.066 ms fixed-first and 0.14 ms random).
The known relation, grammar, and locally simulated oracle are harness-defined;
the result does not test broad hypothesis discovery or real oracle economics.
Next increase version-space ambiguity and add adversarial observational aliases
and out-of-grammar controls, then repeat across independently authored relation
and task families. The full source lock, capture, and independent analysis are
linked in [active-query results](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_RESULTS_20261003.md).


### Order-balanced query-selection result (2026-10-03)

V1.1 repeats the generated-hypothesis active-query gate with 30 paired random input orders per worker, avoiding the v1 fixed-first arm's hand-ordered candidate list. Its independent analyzer also regenerates and matches all five hypothesis pools from the frozen training and unlabeled inputs. Max entropy identifies a unique exact survivor in 150/150 blocks, while sequential random order does so in 111/150; median per-worker call savings are 0–2. Median selection latency remains higher for entropy (3.74 ms versus 0.40 ms sequential). Because the oracle is a locally computed rule and all workers share one authored relation family, the evidence supports only a bounded query-selection advantage. Next evaluate candidate model misspecification, aliasing, richer version spaces, and independent relation/task families, then measure acquisition and integration cost end to end. See [v1.1 results](NUMERIC_OPPOSITION_ACTIVE_QUERY_V1_1_RESULTS_20261003.md) and the [source lock](../../../evaluation/substrate_capability/numeric_opposition_active_query_v1_1_lock_20261003.json).
