# Log-time, order-N future-manifold projection

Status: design contract for the successor to the completed dense v5 control.
The v5 result is immutable and must not be relabelled as evidence for this
projector.

The projection is temporally foveated. Its initial anchors are action ticks
`1, 2, 4, 8, ...`; horizon budget counts evaluated anchors/refinements, not a
fixed dense physical horizon. Every interval between anchors must carry a
conservative certificate for all intervening integer ticks. Endpoint samples
alone are never a certificate.

Projection begins at shape order 0 and raises order only inside an interval
whose enclosure overlaps a protected bound. Order 1 is the manifold-shape
first difference (the non-physical “momentum” of available futures), order 2
is its curvature, and order N is the Nth discrete shape difference. These are
properties of the projected future manifold, not of the plant. An order may
be used only when its coefficient and next-order remainder enclosure are
derived from the held graph A-B-S model; missing support fails closed.

For the current learned motor model, context transition is affine and actuator
position is bounded-rate piecewise affine. Context jumps at logarithmic
anchors can therefore use deterministic affine powers; actuator position has
an exact clamped jump. Consequence output may be affine or quadratic in that
context, so interval affine/quadratic arithmetic must propagate the state
enclosure into each protected residual. A shape-order Taylor enclosure is
accepted only when it contains that model interval. This prevents a polynomial
fit from granting itself authority.

For each dyadic interval:

1. Evaluate its logarithmic endpoint and the lowest supported shape order.
2. If the full residual enclosure is within every protected bound, certify the
   interval without adding temporal samples.
3. If a protected loss is certain, subdivide only enough to locate the earliest
   decisive tick, then stop.
4. If the enclosure is ambiguous, raise shape order while supported and while
   doing so tightens the remainder. If order no longer helps, bisect that
   interval and repeat.
5. If order, refinement, information, or computation budget is exhausted with
   ambiguity remaining, fail closed.

The choice among increasing horizon, increasing local temporal width, and
increasing shape order/information is the time–width–information triangle. The
projector spends the least deterministic increment that can reduce the active
ambiguity; stable tie order is: lower added information, fewer new time
anchors, lower order, earlier interval.

Required audit includes anchor ticks, maximum order used, per-interval order,
refinement count, maximum enclosure width, remainder bound, certified and
ambiguous intervals, earliest decisive tick, retained cells/links, model
support hash, resolution reason, and all budgets. Gate-off must bypass this
machinery exactly.

Before an F-16 comparison, exact dense model trajectories over small horizons
must lie inside every emitted interval enclosure. Tests must include an
intermediate loss followed by endpoint recovery, an order escalation without
time refinement, a local refinement without global refinement, unsupported
higher order, non-finite coefficients, topology loss, deterministic replay,
and gate-off identity.
