# Live self-report task-dimension frame scale v1: preregistration

Date: 2026-09-27

## Question

How do full-request execution work and reported task coverage change as the self-organisation faculty receives larger held-area frames? Does the existing prose surface preserve the full inventory or cap its report?

## Intervention and workload

Each fresh worker loads the full seed set and issues the live request `report your organisation`. Before the request, the harness replaces the Agent's cached self-organisation area list with 4, 8, 12, 16, or 24 controlled dimensions. Each dimension is represented by a named Microtheory and one Concept, with `Agent --holds_area--> Microtheory --has_concept--> Concept`. The inventory JSON and declared count match those graph objects. Names are `frame_probe_area_01` through `frame_probe_area_N`; these labels make the intervention and expected answer machine-checkable.

For every size, run two fresh-process replicates in each of two arms: untraced, and with native aggregate/per-rule counters plus runtime access tracing. Total: 20 workers. Capture the reflection's structured area list, public reply, Goal lifecycle, semantic graph, frame edge cut, candidate/Term work, access events, request CPU/wall time, and process peak RSS.

The frame root and membership links are created by the harness. This tests execution with an explicit operational frame; it is not a test of frame discovery or cheap-cut learning.

## Gates

1. Twenty distinct workers cover all size × replicate × arm cells; source fingerprints are stable from lock through each worker and driver completion.
2. Every request uses `self_report` and resolves exactly one Goal through selection, execution, and action result; the Goal is closed and inactive.
3. The structured reflective result contains all N dimensions in order. The public reply must exactly report the first `min(N,12)` dimensions and no other dimension. This directly measures the existing output cap.
4. Each dimension has exactly two frame nodes and one internal `has_concept` edge; exactly one `holds_area` incidence per dimension crosses to the shared Agent root; no frame Concept receives an `is_a` classification.
5. Audited and untraced pairs have identical reply, Goal, semantic graph digest, and graph sizes.
6. Graph size changes exactly by two nodes and two edges per added dimension, relative to one constant post-seed graph.
7. Untraced workers have empty audit data. Audited access traces have zero drops and reconcile with retained rows.
8. Candidate and Term totals reconcile with uniquely attributed rule/clause and Term-kind totals; ambiguous IDs are not uniquely attributed. Work and graph outputs repeat exactly within each size.

## Interpretation boundary

Two replicates per cell support deterministic operation-count comparison and descriptive timings, not a timing-complexity estimate. The generated area names and shared-root graph are controlled synthetic task state. The frame boundary is supplied by the harness. This experiment cannot establish naturally occurring frame distributions, learned separators, execution factorization by the engine, semantic validity of arbitrary new areas, or general capability.
