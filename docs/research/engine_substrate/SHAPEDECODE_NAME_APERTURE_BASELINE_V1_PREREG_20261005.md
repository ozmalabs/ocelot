# ShapeDecode name-aperture baseline v1 — preregistration

**Status:** protocol fixed before capture. **Scope:** current scan implementation only; no index is enabled and no speedup is claimed.

## Question

How does current ShapeDecode work scale when the cross-frame identity seed scores a codebook candidate through a singleton `codebook_scope`? The evaluator currently calls `load_parts` before applying the name aperture, so each helper call may parse the full typed population even though it retains one name.

## Workload and arms

Use `domains/crossframe_world.py` and the shipped `vision_crossframe_identity` plus `shape_decode_loop` rules. A deterministic one-observation fixture contains 16 held target signatures and 0/16/48/112 additional distractors (authored additions 16/32/64/128). The cross-frame world boots 17 existing ShapeSignature nodes, so the expected *effective typed populations* are 33/49/81/145; the worker records the exact count and analysis checks it. The target is exactly one held signature; distractors use a distinct predicate. Each native helper path remains unchanged. Run three fresh-process replicates per size in separate traced and untraced workers (24 workers total), with sizes and trace states shuffled by a fixed seed. Each worker builds one graph and runs one closure.

## Measures and acceptance

Record source/build hashes before and after each worker, PID, graph/codebook sizes, rule closure wall and CPU time, peak RSS, closure work count, exact selected name, and raw native work-trace rows. In traced workers, independently sum ShapeDecode population-node visits, parsed parts, helper calls, and candidate work by helper subject ID; require zero dropped trace events. Traced and untraced workers must agree on winner and coarse closure work. All sizes must select the exact target `r00`; every worker must report the same graph-independent oracle outcome. Report per-cell median and range; do not pool traced timing with untraced timing or interpret operation counts as CPU time.

This baseline does not test indexing, natural frame locality, generic ShapeDecode correctness, or hardware-independent asymptotics. A later indexed-name arm requires its own preregistration and must preserve case folding, string representation, duplicate-name order/overwrite, absent/empty scope, malformed-entry behavior, and graph mutation/fork/restore semantics.

## Amendment v1.1 — effective population labels

The initial execution exposed that the protocol's size labels omitted the 17 ShapeSignature nodes already installed by `boot_core` and `shape_decode_loop`. The measured worker graph correctly included them. The original lock, capture, and analysis are retained as `*_pre_amendment_*` audit artifacts; this amended lock and rerun make the effective population explicit. The design, helper path, workload additions, replicate count, and acceptance criteria are unchanged. The amendment changes only the population labels and adds an explicit effective-size check.
