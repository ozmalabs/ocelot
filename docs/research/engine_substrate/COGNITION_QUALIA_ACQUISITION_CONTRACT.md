# Episode-grounded qualia acquisition contract v1

Status: semantic freeze for P7.02–P7.E3. This contract defines what episode evidence can authorize. It does not claim that acquisition rules exist yet, and it does not redefine the existing qualia codebook, typed cognition signatures, numeric Shape signatures, similarity recall, or observer aperture.

## 1. Episode evidence and ownership

An `ExperienceEpisode` is an owner-scoped, append-only sequence of measured events. Its stable identity is `(owner_agent, episode_id, source_epoch)`. Each `ExperienceEvent` has a stable event ID, sequence index, source ID and epoch, timestamp when available, typed observed feature references, and an evidence status. An `ExperienceAction` references the actual requested/emitted action and its sink receipt; an `ExperienceOutcome` references the subsequent measured result and any observer/verifier receipt. The episode retains original events and links; projections never replace the source.

The ingestion boundary may supply observable nonlinguistic features, action identity, task/context identifiers, and measured outcomes. It must not supply a target dimension name, target distinction label, hidden answer, expected class, reference solution, answer-conditioned hint, or a precomputed “correct axis.” A later human label may be attached as a separate asserted annotation. It is never an induction feature, witness, verifier, or positive-evidence substitute.

Every event, action, outcome, projection and receipt carries the same owner and the source/model/frame epoch it observes. Cross-owner evidence cannot combine. Duplicate event/outcome IDs are idempotent. A changed or deleted source invalidates its projections and pending acquisition requests; it does not erase the immutable historical event. Imagined, inferred, asserted, stale, missing or unreceipted outcomes cannot count as observed support.

## 2. Distinguishing finer grain from a new dimension

For each recurring outcome residual, the graph first tests whether existing dimensions explain it at their declared grain. A finer-grain proposal is admissible only for an existing observed dimension, within that dimension's frozen bounds, and only when its finer values predict a consequence on episodes not used to select the grain. It cannot invent a coordinate absent from the observations.

A new dimension is a candidate only when all admissible existing dimensions and grain refinements leave a repeated, outcome-relevant distinction unresolved, and the episode stream contains a typed observed feature that separates the outcomes. Equal source values remain equal at every grain; no aperture operation can make them different. If there is no observed separating feature, the result is `UNSUPPORTED`/unknown, not a guessed axis.

Acquisition preserves the source feature family and units. It cannot merge lexical, numeric, temporal, relational, phenomenal or Shape coordinates by token coincidence. Candidate identity includes owner, source family, event window, feature definition, model/frame epoch and evidence set. A probe-relative collision retains alternatives; `None` or an opaque evaluator result never enters identity or deduplication.

## 3. Recurrence, validation, revision and retirement

The frozen minimum to propose a distinction is three independently identified observed outcome episodes with the same candidate feature/outcome relation. Replays of one outcome do not increase support. The candidate remains `PROPOSED`; it does not enter standing qualia or recognition until it predicts the distinguishing outcome in two fresh episodes from different episode IDs and contexts. Candidate creation and validation episodes are disjoint. Positive evidence names every supporting event/outcome reference and its receipts.

Contradictory observations are retained as separate witnesses. A negative outcome against an adopted distinction moves it to `CONTESTED`; it does not overwrite the prior support or automatically flip the axis meaning. Revision is another owner-scoped, funded proposal that must pass two fresh validations. When evidence expires, source epochs change, or the proposal fails its validation budget, the candidate becomes `RETIRED` with its reason and witnesses preserved. A retired or contested axis cannot silently remain active in standing recognition.

Significance is context-sensitive and derived from witnessed consequences (for example, a measured cost, success, failure or safety consequence), not a hard-coded valence or ungrounded scalar. A current episode may carry a `live_significance` overlay. Only repeated, validated evidence may update a standing significance estimate. The live overlay and standing estimate remain separate graph facts, each with source references, epoch, context and uncertainty. Significance never turns an unverified distinction into a verified one.

## 4. Funding and terminal states

Any proposal, finer-grain sweep, fresh validation or revision is funded before computation. A request identity is `(owner, operation, source_epoch, frame_epoch, candidate_key)`, has at most one debit, and ends in exactly one of `COMPLETED`, `UNSUPPORTED`, `TIMEOUT`, `FAILED`, `STALE`, or `DENIED`. Bounds are: at most 32 live candidate distinctions per owner/context, at most 200 event references examined per request, at most 8 grain values per existing axis, and at most 2 fresh validation episodes per candidate before a terminal decision. A retry after expiry receives a new request ID and cannot reuse stale work as current evidence.

Budgets limit work and graph growth; they never lower the three-episode recurrence threshold, the two-episode fresh validation threshold, or the source/receipt requirement. Interruption leaves a resumable request with its debit/progress identity; restart cannot debit it twice. An expired or stale lease terminates unknown and preserves prior evidence.

All decisions (candidate selection, grain refinement, axis proposal, adoption, contesting and retirement) are Rust graph-rule decisions. Python may ingest actual world events, tick under the declared bound and read off graph outcomes. Python cannot choose a feature, rank candidate axes, repair a failure, calculate a target label, or insert a candidate dimension.

## 5. Frozen acceptance scenarios

| Acceptance | World/control construction | Required graph outcome |
|---|---|---|
| `test_no_target_axis_in_inputs` | Same episodes are presented with no dimension/answer labels; labels may be attached afterward as asserted annotations. | Agent input graph contains no target axis, class, hidden answer or solution. The selected candidate is supported only by event/outcome evidence. |
| `test_finer_grain_cannot_fake_missing_dimension` | Existing dimensions are equal on two episodes at their finest declared values; a separately observed feature predicts different outcomes. Sweep all allowed grains. | No refinement separates equal coordinates. A new candidate may be proposed only from the observed feature; without it, the result stays unknown. |
| `test_acquired_axis_has_episode_witnesses` | Three distinct source-bound episodes provide recurrence; two held-back contexts provide validation. | Candidate retains all three witness IDs; it is not standing before both fresh validations pass; every receipt/owner/epoch matches. |
| `test_negative_evidence_can_revise` | A previously validated distinction receives a contradictory measured outcome, followed by fresh validation. | Old and new witnesses coexist; status becomes contested before revision; a revised axis requires fresh validation and cannot rewrite history. |

Required controls: label-shuffled episodes, exposure-only episodes without outcome, same feature with orthogonal outcomes, duplicate IDs, stale owner/source/receipt, missing coordinates, interrupted/restarted funding, and deletion of a source. All must preserve unknown or contested outcomes as specified; none can produce standing support.

P7's later registered evaluation remains the one in the linear plan: 200 acquired-distinction episodes in each independently coded tool/contact and social request/repair world, with 100 label-shuffled, exposure-only and orthogonal controls per family. The proposed transfer threshold (at least 20 percentage points over frozen space under identical experience and compute) and zero source/grounding leaks remain unchanged. This contract does not promote those proposed criteria to a result.
