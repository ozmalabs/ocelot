# Cognition build Phase 5 — Faculty depth preregistration

**Protocol:** `cognition_p5_heldout_v1`
**Status:** H0 and F1 implementation recorded; per-item evaluation specifications, runner freeze and held-out draw remain pending.
**Entry merge:** `9def1187f42f74489e4c2833c0bbae34e63df584` (P4 merged onto the committed `main` base in the isolated continuation branch).
**P4 freeze:** `199583ca6c4fe861dae90dd5814d3f0ad3b9f5ed`.
**P4 result/H4 record:** [`COGNITION_BUILD_P4_RESULTS.md`](COGNITION_BUILD_P4_RESULTS.md).

## P5.H0 — Entry evidence and scope

Phase 4 is executed. Its registered synthetic panel reports D2/D3 conformance PASS (200/200 parity streams; 100/100 collision controls), D1 PASS on regular temporal sequences (200/200 versus 0/200; all 100 unsupported controls refused), E1/E2 PASS for supplied-model fixtures (80/80 feasible candidates versus 0/80), and D5 PASS in both generated transfer families (100% solve in both arms with 50% fewer exact checks on recall-on). C5 FAILS its primary gain criterion: both arms resolve 92/200 hidden residuals (46%), with zero paired gains; same-epoch funding and forced-frame invariants pass. The inherited gate retains three RED files, one timeout and one fully skipped test, with no new failures against baseline. These outcomes and hashes are detailed in the P4 results ledger.

### Supported interfaces and limitations

| P4 evidence | P5 use | Boundary |
|---|---|---|
| Native bounded `RecallNearest`, exact typed descriptors and receipt-gated settlement | Candidate prefilter where owner, source, schema, frame and epoch match | A nearest/remembered candidate is never proof of task success. D5's work savings cover only graph-role and numeric-sequence generated families. |
| Verified local numeric-Shape source and exact Shape outcome evidence | Reuse candidates in their verified source domain | Other domain sources and verifier receipts are unavailable. Fall back to local generation and the domain's exact verifier. |
| C5 same-epoch funded probe and forced-frame invariants | Preserve funding and authorization checks when a probe is explicitly requested | C5 showed no incremental resolution over legacy ApertureFrame (46% vs 46%). P5 must not assume positive VOI or improved information access. |
| Native `FutureManifoldProjection` and provenance-linked zero-residual receipts for supplied models | Use projections as bounded imagined candidates, with model epoch and candidate identity attached | E1/E2 showed no refinement requests and used supplied synthetic models. A projection is not observed success; stale or unsupported models return unknown. |
| Graph-owned ThoughtManifold control and shared projector for current numeric inputs | Reuse bounded detached trajectory and projection interfaces | Static lexical/relation extraction and candidate segment generation remain adapter responsibilities; no broader live-stream claim. |
| Funded regular-frame TimeInfer with explicit windows/seals | No P5 task depends on temporal escalation | Irregular streams remain refused; hardware-specific event producers were not evaluated. |
| Default/conversation isolation and cognition-on-only experimental seeds | Keep all new P5 policies disabled outside explicit cognition-on activation | No new P5 seed enters CORE or default boot. |

### Fallback and safety contract

When recall is absent, stale, ambiguous, incomplete, cross-domain without a registered mapping, or lacks a matching exact verifier receipt, the system generates a local candidate or opens the existing explicitly funded executor. P5 planning may rank model-supported candidates, but every candidate remains imagined until a current observation/action receipt verifies the exact goal-relevant outcome. A failed or missing P4 C5 benefit cannot authorize a probe or action. G3 must withhold stopped actions at the external/native sink; graph status alone does not count as inhibition. Every P5 decision, temporary policy enablement and funded operation must preserve model/source epochs, provenance, one request/one debit accounting and terminal restoration.

### Native migration boundaries

Python may translate source data into graph events and format readouts. The graph owns ToM projection and recursive belief updates, evidence-backed reappraisal, stop/withhold authorization, planner frontier and candidate arbitration, decomposition completion witnesses, and detached rotation-buffer lifecycle. Native Terms are added only when existing terms cannot express a bounded required operation; their schema and all dispatch/serialization/rewrite arms are frozen before implementation. Existing P4 projector terms remain the common projection path. P5 does not use Python-side search, inference, scoring, or settlement decisions.

### Carryovers and order

| Carryover | Owner | Completion evidence |
|---|---|---|
| P1 advisory `ImaginedCandidate` has no downstream consumer | P5.E4.1 specifies bounded planner/re-open identity; P5.E4.3 consumes it through System-2 arbitration and retains imagined provenance until a real receipt | One-time consumption, current goal/model revalidation, no grounding before receipt, and G3 stop authorization at the sink |
| P1 `child_mean_saturation` is diagnostic only | P5.A2.1 specifies required-key/epoch witness; P5.A2.2 settles parent and impasse only from complete, current child evidence | Partial, empty, overlapping or stale children never complete the parent; completion is idempotent |
| P3 Family-A repeat-cost hypothesis failed | Remains failed in P3 results; no P5 retuning or reclassification | P5 H2 reports its own items only and keeps P3 evidence unchanged |
| P3 temporal rung deferred | P4.D1 now covers regular measured windows; irregular sampling remains explicitly unsupported | No P5 claim depends on irregular temporal inference |

The execution order is F1.1 → F1.2 → F2.1 → F2.2 → F2.3. G2, G3, E3, A2 and D6 start only after their item specifications; G3 is a hard prerequisite for E4 action arbitration, while E3 supplies optional causal models to E4. E4 planning cannot authorize emission until G3 is implemented and tested. All eight P5 evaluation items (F1, F2, G2, G3, E3, E4, A2, D6) remain in scope; none is omitted because an outcome is inconvenient.

## P5.F1.1 — Attributed-state view contract

The shared view is a provenance-preserving projection, not a shared belief store and not a new truth layer. Each projected row has a stable `view_id`, `source_kind`, `source_node`, `source_epoch` (including an explicit unknown marker), `holder`, optional `target`, `content_ref`, `modality`, and `epistemic_kind`. Rows remain separate when content or holder differs; disagreement is represented by coexisting rows. The projection may add `projects_source` and `uses_vocabulary` lineage edges, but does not edit source records. `TomViewPolicy.enabled` is registered disabled by default; F1.2 must not activate it in CORE/default boot.

The four source forms are mapped as follows:

| Source form | Holder / target | Content and modality | Epistemic kind and boundary |
|---|---|---|---|
| `character_tom` nested `SmEntity` | `belief_holder` / target parsed from the nested proposition when available | source entity plus `flavor` and proposition | `attributed`; character belief-world content is not actual-world truth |
| psychology seed | no holder or target on its own | vocabulary concept reference only | vocabulary-only; it creates no attributed-state row without a separate live state source |
| interlocutor model | observing agent / modeled `Party` | feature estimate or self-report assertion reference | estimates are the agent's `estimate` of the party; the interlocutor's `Assertion` separately records `world_assertion` by its speaker and does not certify truth |
| Bigville resident agency attribution | resident / target resident | `controllability_for:<target>` Concept and its owning Microtheory | `attributed`; resident-owned `regard_for`, `desire_for`, `removal_desire_for`, and `pity_for` are own affect/motivation and must not enter this view as beliefs about the target |

Epoch is copied from a source's explicit revision/version field if present; absent source epochs remain explicitly unknown and must not be fabricated from wall time or a different owner's clock. Revisions produce a fresh projection identity for that source epoch and leave the prior projection/provenance intact. A vocabulary reference can annotate a live state row but cannot supply its holder, target, modality, or epoch. F1.1's contract tests exercise fixtures; F1.2 separately verifies the native graph projection path.

The migration preserves the existing `tom_meta_shape` observation behavior and its two domain-specific translators. The shared attributed-state view does not make unrelated domain corpora structurally identical, and retired Python psychology functions remain retired.

## P5.F1 implementation record

F1.1 contract fixtures and F1.2's generated `tom_unified_view` seed are implemented. The native rule projects standardized `TomAttributedStateSource` graph events only when `TomViewPolicy.enabled=1`, retains source identity/epoch/owner and a `projects_tom_source` edge, and marks superseded epochs stale. The policy seed has no dependencies and is disabled by default. Domain runtime hooks remain explicit adapter work; the current acceptance supplies standardized source events and does not claim automatic ingestion from all four source stores. Psychology vocabulary alone is deliberately not a source event. The F1 item evaluation and held-out performance criterion remain pending.

## Held-out decision criteria (inherited from the detailed plan)

The registered panel uses 200 paired instances per primary family and 100 adverse/control instances per item. The frozen criteria are: F1 ≥95% exact view conformance with zero belief-to-truth leaks and no lost source assertions; F2 ≥80% exact query accuracy and ≥20-point gain with corrected p<.01 and zero actual-world overwrites; G2 ≥20-point gain in evidence-supported appraisal with corrected p<.01 and zero source edits/unsupported interpretations; G3 100% timely stop withholding, ≥95% valid go emissions and zero duplicate emissions; E3 ≥95% oracle agreement on identifiable finite models and unknown on nonidentified cases with no live-graph mutation; E4 ≥20-point observed solve gain for depth 2–8 tasks with corrected p<.01 and zero unsafe emissions, false grounding or bound violations; A2 100% valid completion decisions and zero premature settlement; D6 ≥95% exact shape verification with zero detached grounding and actual transform-work reporting. Item specifications must freeze generators, arms, null/timeout rules, work counters and exclusions before H1. Holm correction applies over each phase's primary superiority tests at family-wise α=.01.
