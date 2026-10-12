# Default MetaShape filing runtime probe v1.1 — preregistered amendment

**Status: registered after v1, before v1.1 measurement.** V1 established that
the default adapter held zero MetaShapes, so the observed all-`None` outcome
could not distinguish an unavailable vocabulary from a classifier that declines
these items. V1 remains preserved as the default-boot arm.

## Added question

For the exact same helper inputs and order, what categories does
`categorise_by_shape` return when `shape_vocabulary` is explicitly loaded into a
fresh adapter before the helpers run?

## Fixed method

- Use a new runner/analyzer version; do not overwrite v1 artifacts.
- Same persistence guard, helper calls, order, capture fields, source digests,
  and two fresh-process replication as v1.
- Load exactly `seeds/shape_vocabulary.json` via `manifest_for("shape_vocabulary")`
  into the fresh adapter before calling any helpers. Load no other optional seed.
- Compare every v1.1 item `(helper, type, attrs)` with the paired v1 default-boot
  item in order. Report result frequencies and item-level changes; do not label
  any predicted category correct or incorrect.
- Preserve both results even if vocabulary loading fails, items diverge, or the
  capture does not replicate.

## Admissibility

Require persistence disabled, unchanged seed-tree digests, all helper calls
completed, expected item identity/order versus v1, exact fresh-process
replication, and source/native identity. The intended contrast is availability
of the seeded MetaShape vocabulary on these helper inputs only.

## Boundary

This remains a direct helper invocation, not a production frequency estimate,
independent semantic evaluation, or representative task distribution. It
identifies output sensitivity to loading the shape vocabulary; it does not
establish filing utility.
