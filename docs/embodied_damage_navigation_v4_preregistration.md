# Checkpointed damage adaptation v4 preregistration

Status: frozen before execution.

V4 implements the next step identified after v3: graph-held model
metaplasticity. Normal adaptation remains immediate. On the first surprising
receipt for an action model, the graph checkpoints its consolidated intercepts
and history coefficients. The adapting model and stable checkpoint then make
parallel predictions on later uses of that action.

After two prequential validation receipts, the graph resolves the comparison
only if one model has at least a five-percent cumulative squared-error
advantage. If the adapting model wins, adaptation is retained. If the stable
checkpoint wins, its parameters replace the changed parameters. Each action
model gets one checkpoint episode, preventing oscillatory reopen/promotion
cycles. Python records these decisions but does not calculate them.

The already executed v3 matrix was the sole development set for this
mechanism. The final form preserved v3's 12/18 wins and body-positive medians,
while validating 58 changed models and rolling back 20 inferior updates.
Those figures are engineering evidence only.

The machine-readable v4 protocol fixes six new dynamics/fault/goal
combinations across all three bodies. It retains every v3 gate and adds
non-vacuity gates requiring checkpoint activity and valid receipt-backed
rollback decisions. The primary claim still requires at least 10/18 wins,
pooled median paired advantage of at least `0.05`, and positive median paired
advantage separately in every morphology.
