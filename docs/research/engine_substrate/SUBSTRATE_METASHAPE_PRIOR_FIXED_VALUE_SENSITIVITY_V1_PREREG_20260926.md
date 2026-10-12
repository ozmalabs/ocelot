# MetaShape fixed-value and prior sensitivity sweep v1 preregistration (2026-09-26)

## Question

For the three multi-schema families that minted support-2 MetaShapes in the v1 panel, how does the recognition ladder classify repeated holdouts as fixed values change, a fixed relation is omitted, an extra relation is added, or the item type changes?

## Locked procedure

Load the `meta_shape_growth` dependency closure. Disable real seed persistence. Train the same two-example pairs for all four panel families in the original protocol, in the same order. Record all newly minted shapes. Then submit the existing positive holdout once per family. Finally submit these controls in this fixed order for each family:

- FrameBinding (`count=7` is fixed): `count ∈ {9,10,-1,0}`; then omit `count`; then add `unexpected_slot="noise"`; then use type `FrameBindingDistractor` with the positive values.
- MotionRule (`order=1` is fixed, but the existing `spatial_dynamics` prior is known to absorb this family): `order ∈ {2,3,0,-1}`; then omit `order`; then add `unexpected_slot="noise"`; then use type `MotionRuleDistractor` with the positive values.
- ResourceTransfer (`status=complete` is fixed): `status ∈ {failed,pending,unavailable,unknown}`; then omit `status`; then add `unexpected_slot="noise"`; then use type `ResourceTransferDistractor` with the positive values.
- GoalTrace (`terminal=false` is fixed): `terminal ∈ {true,unknown,done,1}`; then omit `terminal`; then add `unexpected_slot="noise"`; then use type `GoalTraceDistractor` with the positive values.

Record `status`, `covered_by`, residual and new MetaShape mints for each observation. Keep `recognized`, `recognized_prior`, `residual`, and any other status distinct. Do not change seeds, prior principles, scoring, or the acceptance definitions after observing output.

## Reporting gates and scope

Admission gates concern source/input lock integrity, complete seed loading, persistence isolation, exact case counts, and complete outputs only. Capability outcomes are descriptive rung-specific counts; this panel has no all-or-nothing accuracy threshold. It measures one fixed four-schema corpus and does not estimate natural semantic error or usefulness.
