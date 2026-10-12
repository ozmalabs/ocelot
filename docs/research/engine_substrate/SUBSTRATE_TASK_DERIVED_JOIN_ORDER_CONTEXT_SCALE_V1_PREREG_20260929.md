# Task-derived join-order context-scale replay v1 preregistration

**Lock date:** 2026-09-29, before confirmatory capture.  
**Status:** Development pilot completed; pilot influenced context levels and is
excluded from confirmatory estimates.  
**Question:** Does the native cardinality-based rule installer select orders
with low exact matcher work when a frozen task graph contains increasing
numbers of irrelevant but structurally plausible goal/event pairs?

## Frozen task and context intervention

Use the ten-event `phase3_common_ground_stress.v1` task and the current
`discourse_goal_select` rule through the v1 common-ground identity replay
harness. Preserve the original explicit six `for_goal` fixture links, the task
identity oracle, all event closures, and complete graph digest. Before rule
installation, add 0, 8, or 32 isolated decoy `DiscourseState` components. Each
decoy component has one proposed active Goal, one `request` origin event, and
one `selection` event with a later event index. It has no `for_goal` edge and
is disconnected from the task state. Decoys must remain inert and must not
change the two-goal identity oracle.

Cross all 24 authored permutations of the four production match clauses with
three fresh-process replicates at each decoy count (216 workers total). Keep
the current native installer active and record its installed-order readback;
the requested order is not treated as the installed order. Measure native
per-rule and per-clause candidate tests over all ten event closures. Report
installation order, exact candidate work, fixed-point status, task/common-
ground oracles, graph digests, and per-checkpoint candidate conservation.

## Development pilot disclosure

Before this preregistration, a one-process exploratory pilot at 0, 4, 8, 16,
and 32 decoys and a 24-order one-process sweep at 0 and 8 decoys were run. At
zero decoys, the one-replicate sweep ranged 36–139 candidate tests (median
59); at eight it ranged 49–59 (median 54). All pilot task oracles and fixed
points passed, and each context size had one terminal graph digest. A requested
source order (`0123`) incurred 106 tests at zero decoys and 49 at eight. These
exploratory observations selected the context levels and are not confirmatory
evidence. The confirmatory capture uses fresh child processes and is analyzed
independently.

## Gates and limits

- Exactly 216 unique `(decoy_count, permutation, replicate)` cells and fresh
  PIDs; all locked inputs identical before, during, and after capture.
- Every worker adds exactly the requested number of disconnected decoy
  components, produces ten fixed points, passes task and common-ground
  oracles, and has no decoy Goal transition.
- Every read-back order is a permutation of the four original clauses;
  candidate counts attributed by clause sum to the target-rule candidate-test
  count at each checkpoint.
- Full terminal graph digests agree across all permutations and replicates
  within each decoy-count context. Digests are not expected to match across
  context sizes because decoy nodes are part of the graph.
- Report candidate-work range and median by decoy count, by installed order,
  and for the requested source order. Installation work is not inferred from
  candidate work, and no latency claim is made from audit-enabled timing.

This is a controlled matcher-context stress test on one authored task and one
four-clause rule. Decoys are synthetic and disconnected; the result is not a
natural-task prevalence estimate, general join optimizer result, production
identity claim, or proof of tractability.
