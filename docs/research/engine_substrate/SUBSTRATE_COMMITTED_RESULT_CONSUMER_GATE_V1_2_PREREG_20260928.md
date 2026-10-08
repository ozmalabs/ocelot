# Committed-result consumer gate v1.2

## Question

Can a graph rule refuse proposal outputs while any revision stage is incomplete or uncommitted, then consume the result after a commit marker changes?

## Protocol

Use three fresh workers, N=2/8/32/64, unique and tied maxima. Create proposals with independently known scores and a target initialized at committed revision 0 with stale selection text. Add revision 1. A consumer rule requires `max_revision`, `count_revision`, `decision_revision`, and `resolved_revision` all equal the revision node's revision before copying `selected_label` into `consumed_label`. First update only the maximum stamp and settle. Then set all three stage stamps/current selection but leave commit at 0 and settle. Finally add a commit event; a commit rule requires all stage stamps equal 1 and writes `resolved_revision=1`; settle and check consumption. The unique arm's selected label is the unique max; the tied arm's label is the empty sentinel.

## Gates

No consumption occurs with incomplete stamps. No consumption occurs when stage stamps are complete but the committed revision is old. After commit, `resolved_revision` becomes 1 and consumer output equals the independently computed unique label or tie sentinel. All closures reach fixed point; counts reproduce across workers ignoring timing fields. The commit rule must reject an incomplete stamp set and accept a complete one.

## v1.2 amendment

The v1 and v1.1 captures are exploratory: v1 failed while iterating mapping keys as checkpoint records; v1.1 included elapsed-time fields in an integer-work replication gate. v1.2 uses an explicit cell/checkpoint signature that excludes elapsed time and `_ns` fields, with new protocol, runner, analyzer, and lock paths. Only v1.2 is confirmatory.

## Limits

This is a controlled graph-rule guard on one output field. It does not prove every production consumer follows the contract, enforce access control on direct graph reads, or test process persistence/concurrent commits. Empty string is the local no-selection sentinel. No complexity claim follows.
