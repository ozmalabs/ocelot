# NaturalProofs reading-path rung-entry panel v1 preregistration

Date: 2026-09-27  
Status: protocol frozen before the 64-task panel; one-record and four-record feasibility pilots are exploratory and excluded from confirmatory counts.  
Question: how often does a fixed outcome-blind stream of held-out mathematical statement text enter the production reflective-faculty dimension decode/mint path during conversation processing?

## Task frame and access boundary

Use all 64 IDs in `evaluation/reports/naturalproofs_rung_stream_frame_v1_20260927.json`, in its stored hash-rank order. The selector uses record IDs only; no model/substrate result affects eligibility or rank. Each task is one NaturalProofs test-shard statement body, passed unchanged as `WorldAdapter.converse(statement, speech_act="statement", speaker="user")`. The title and proof target are not passed as conversation input or used by the runner to choose, score, or summarize a task. Do not ask the substrate to prove the statement. This panel measures reading-path induction entry, not theorem-solving accuracy.

Source audit: `domains/naturalproofs_local.py::_files` and `_load` index all JSONL splits and preserve top-level proof targets. The production definition reader calls `naturalproofs_local.definition` and returns its text field; the audited production tree contains no `naturalproofs_local.proof_for` callsite. The runner itself reads only `text` from each selected test row. The raw corpus and all runtime source are locked. If review finds a route from the input to proof-target retrieval, the run must be labeled an access-contaminated entry pilot and cannot support clean held-out claims.

## Runtime condition

Two fresh worker processes run the same fixed schedule on independent graph instances. Each loads the full seed runtime with `WorldAdapter(seeds=(), shadow_read=False, deep_ingest=False)` followed by `substrate.boot_all.load_all_seeds`. This is the repository's full-runtime evaluation profile with optional shadow reading disabled; it is not the bare `WorldAdapter` core-seed default. Tasks run sequentially on the same graph within a worker so later-task measurements include the actual structural carryover from earlier selected inputs. Preserve each task even if conversation parsing fails or returns no reply.

## Cold-start handling

The first conversation can lazily author the conceptualizer faculty through `conceptualizer.ensure_conceptualizer_rules` -> `reflective_faculty.induce_concern(name_hint="conceptualizer_live")`. Treat this one-time first-use event as setup, not evidence that the theorem statement naturally triggered a new dimension. Report its wall/CPU and graph deltas separately. The primary residual-driven task-entry rate uses tasks 2–64 as its denominator; any later `conceptualizer_live` re-entry remains reported as a protocol anomaly, not silently removed.

## Passive measurements

Immediately before and after every request, the runner reads counts/IDs for `NativeReflectiveFacultyReceipt` nodes with cluster `reflective_faculty.concern_decode_settlement`, all `Observation` nodes, `CapabilityAxis` nodes, and transform nodes/edges. It calls no induction or ProblemShape observer and writes no instrumentation into the substrate graph. Record per task: frozen sample ID and statement hash, source/process lock state, call error, reply-present bit (never reply text), wall/CPU time, graph node/edge counts, receipt-ID delta and receipt `native_steps`, new Observation IDs and status/key/covered_by, new CapabilityAxis IDs/names, new transform IDs, and unrelated Observation deltas separately.

The receipt does not link directly to its Observation. Therefore report concern receipt entry counts separately from all new Observation outcome counts. Attribute a per-receipt status only if the task interval has exactly one new concern receipt and exactly one new candidate Observation; otherwise label the mapping ambiguous and retain both raw sets. `CapabilityAxis` is an overloaded node type in this runtime: report raw node-count deltas by `kind` and classify them separately from reflective-faculty induction. Store only a SHA-256 token hash, not the surface token. Count a rung mint only when a newly created Observation has a graph-native `minted` edge to the axis; an `induced` attribute is a second corroborating label. Count transforms from the Observation's `has_transform` edge and `recognized_transformed` status. Do not infer induction from a type-only delta.

Primary measures:

- post-cold-start entry incidence: tasks 2–64 with at least one new concern receipt / 63;
- all-task entry incidence including setup: tasks 1–64 with at least one receipt / 64;
- receipt count, `native_steps`, and wall/CPU cost per task;
- status distribution (`recognized`, `recognized_transformed`, `minted`, other/missing) among unambiguously linked observations;
- new-axis mint incidence and whether it occurs in the first-use setup or a later task;
- failures, zero-entry tasks, ambiguous receipt/Observation mappings, and missing replies.

Do not use exact response text against the proof target or promote receipt frequency to success rate.

## Gates and source lock

Both workers must have distinct PIDs, load the expected full seed runtime, process all 64 sample IDs in exact order, preserve a row for every task, and match the complete pre/post runtime source lock. The independent analyzer recomputes the selection frame from its hashes/IDs, verifies statement hashes against the frozen test shard, checks worker source stability and schedule parity, recomputes all entry/outcome denominators, and confirms the observation collector did not add task-graph instrumentation nodes. Any source drift, omitted task, or undeclared task mutation invalidates the confirmatory status.

Lock Python runtime source, native Rust source and extension, all seeds, domains, substrate modules, world adapters, scripts, relevant corpus/reference assets (`data/naturalproofs`, `data/slabs`, and `data/corpus`), the selector, frozen frame, protocol, runner, and analyzer. Record environment versions and process RSS. No tests are added or run as part of this evaluation.

## Interpretation boundary

The population is one title-disjoint NaturalProofs test-shard sample and the operating condition is a full-runtime, shadow-reading-disabled conversation route. This estimates entry incidence for these statement stimuli on this configuration only. It does not establish natural human-task prevalence, comprehension quality, proof-generation accuracy, learning benefit, default core-only behavior, or general capability. A second task family and independent answer-oracle panel remain required before cross-family capability claims.
