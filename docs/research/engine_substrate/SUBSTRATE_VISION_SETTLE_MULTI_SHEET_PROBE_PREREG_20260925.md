# Vision settling multi-sheet coupling probe — preregistration

**Evidence type:** native runtime semantic probe on a minimal graph; not a performance benchmark or full vision-world run.

## Question and frozen fixture

Does the authored `st_settle` rule's global `NodesOfType(SUnit)` activation mean couple two distinct world-rooted sheets in one Substrate graph?

Load only the unchanged `st_settle` rule from `seeds/vision_settle.json`. Add one `SettleParams(settle=1)` node and two `World(step=0)` roots, A and B. Each world owns two SUnits through `has_sunit`; the two units within each world form a symmetric `sunit_neighbour` pair. All four units have `aff=0`, `aff_step=0`, and `act_next=0`. Sheet A always starts with `act=[1,1]`. Run two paired native graphs, changing only sheet B's initial `act`: arm 0 uses `[0,0]`; arm 1 uses `[1,1]`. Run the native rule closure under a 10,000 progress cap and read the two A `act_next` values.

## Registered expectation and checks

If the fold is global across all SUnits, mean-neighbor(A)=1 in both arms, while mean-sheet is 0.5 in arm 0 and 1.0 in arm 1; therefore A `act_next` should be 0.5 and 0.0 respectively. The run passes only if both arms execute the rule, both A values match those predictions within 1e-7, and changing B changes A. Preserve all raw values and provenance.

## Claim boundary

This isolates whether the current AST respects the `World` root; it does not use a full retina/cortical builder, test multiple parameter nodes, test convergence of `st_commit`, or measure performance. It establishes a semantic cross-sheet read only for the registered two-pair fixture.
