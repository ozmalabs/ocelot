# Grammar widening depth study v1 preregistration (2026-10-03)

## Question

Across the five frozen additive and five frozen product panels, does extending
the Neg/Eq/And grammar with the task-relevant arithmetic primitive recover an
exact model, and how does maximum term size affect cost and recovery?

## Design

Replay the training examples and 32 probe inputs in workers 0–4 from the
source-locked model-adequacy audit v1.1. Run two independent synthesis arms
per panel: Neg/Eq/And/Plus for additive, and Neg/Eq/And/Times for product.
Use maximum sizes 7 and 9, no constants, at most 128 hypotheses, and a 12 s
per-arm timeout. Keep each arm in a fresh native Substrate. The harness knows
which arithmetic primitive to add; primitive selection is supplied task
information, not an outcome of the learner.

Score every returned candidate on the disjoint fractional 1,296-point grid
from v1.1. Record synthesis wall and process CPU time, explored candidates,
returned candidate count, halt reason, and exact-candidate count. Preserve
partial results after timeout. Do not count selecting the relevant primitive
as substrate work; report it as externally supplied information. No results
are pooled with the exploratory worker-0 pilot.

## Analysis gates

Independently bind the source lock and capture, verify all ten panel inputs
against the prior immutable lock, recompute each candidate's 1,296-point
score, verify arm settings and panel coverage, and report per-task/per-size
exact recovery and timeout counts plus cost medians. This is a descriptive
search-cost/recovery study. It does not test an autonomous grammar-selection
policy, transfer beyond these two relations, or general tractability.

## Frozen sources

The runner, analyzer, protocol, v1.1 panel lock, current synthesizer/native
source and build fingerprint, and all training/probe inputs are hashed before
capture. The analyzer must not alter or regenerate the selected panels.
