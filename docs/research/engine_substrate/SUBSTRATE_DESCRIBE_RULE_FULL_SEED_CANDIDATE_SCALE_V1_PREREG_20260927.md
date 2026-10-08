# Describe-rule full-seed candidate scale v1 preregistration (2026-09-27)

## Question

Does the linear Concept-population work measured for the isolated three-rule matcher persist when those exact source-generated rules execute over a full-seed graph with its 206 Microtheories and thousands of existing Concept memberships? How do selected work counts respond independently to more Scene/Percept input and to additional negative Concept members?

## Design

Run eight fresh full-seed workers: two replicates of a 2×2 design. Scene factor is 1 or 4 Scenes, each with the same three Percepts (meter, static, mover). Extra Concept factor is 0 or 4,096 negative distractor Concepts attached to a dedicated Microtheory. Each worker boots `load_all_seeds`, invokes `scripts.arc_self_report.build_describe_faculty` to install the real six-rule faculty, verifies exactly one existing target Concept for each of the three audited labels, then deactivates every rule except `recognise_a_counter`, `recognise_a_thing_that_stays_put`, and `recognise_a_thing_that_moves_itself`. The full seed graph remains resident; only closure is restricted to the three target rules for clean attribution. A noise Microtheory is present in all four conditions, with zero or 4,096 attached distractors.

Run full closure with native global/per-rule scale audits enabled. Record full-seed boot failures/loads, faculty construction cost, base and manipulated Scene/Percept/Microtheory/Concept populations, active rule set, fixed-point report, exact classifications, rule candidate/Term counts, wall/CPU/RSS, and locked source/native hashes. The 2×2 schedule and graph construction are fixed in the runner.

## Gates

- Eight unique fresh workers, two per cell; every full runtime/native input hash matches the lock before and after each worker.
- Full boot and faculty construction complete; exactly the three target recognition rules remain active at measurement time.
- Exactly one target Concept per audited label; every Scene Percept receives its correct one `is_a` edge, no other target-label edge appears, and no distractor Concept is classified.
- Rule closure reports fixed point with no budget exhaustion.
- Report per-rule candidate/Term counts for all cells. Compare the Concept and Scene factors and their interaction; do not impose a prior growth law or timing pass threshold.
- Preserve each worker payload; any missing cell or invalid semantic/source gate blocks the corresponding inference.

## Limits

This is a full-seed graph with only three recognition rules active during measurement, not end-to-end full-seed closure or a live conversation. It tests whether pre-existing graph populations change these rules' measured matching work, while suppressing interactions from other active rules. The distractors are synthetic negatives. Two replicates per cell do not estimate natural task distributions or rare variability. Audited timing is not baseline request latency.
