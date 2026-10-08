# Monolithic scheduler work v1 preregistration

Date: 2026-09-26

## Question

Do opt-in counters exactly account for rule-vector work in the monolithic fixpoint scheduler's external-input polling, short-circuit fixed-point probe, dirty-vector scan, and selected-rule list, and how do these counts scale with the number of loaded rules?

## Instrumented work

The scale audit records entered monolithic passes, full live-rule slots visited by the `reads_external` polling loop, dirty slots examined by the fixed-point probe, dirty-vector slots scanned while selecting the next pass, and selected rules. It also accumulates elapsed wall time from before external polling through fixed-point/dirty selection; this scheduler-planning interval excludes deferred queue drains, rule matching/application, and later execution of selected rules. When auditing is disabled, the existing `.any` fixed-point iterator remains in use; the counted loop is selected only with auditing enabled and preserves the same order and short-circuit predicate.

## Workload

Three fresh-process replications at each `R={1,8,32,128}` install R active rules with one absent positive edge pattern and no effects. The first call settles all initially dirty rules without progress. A second call on the same substrate exercises the already-clean fixed-point fast path. Each phase is run in plain and audit-on arms on independently constructed but identical substrates.

For the first call, expected scheduler counts are one pass, R external-poll slots, one fixed-point probe slot (the first dirty rule), R dirty-vector slots, and R selected rules. For the second call, expected counts are one pass, R external-poll slots, R fixed-point probe slots, zero dirty-vector slots, and zero selected rules. In both phases, scheduler pass count must equal `passes_completed`; progress remains zero and state projections remain identical. The first-call matcher performs R rule enumerations; the warm fixed-point call performs none.

## Limits

This isolates scheduler slot counts and plan time for one monolithic no-match rule family. It does not measure scoped/event scheduler loops, queue maintenance, matcher costs on positive or dense patterns, active external-input rules, or natural rule-count distributions. Scheduler-planning wall time includes the audit gate and counters and is descriptive; exact slot counts are the primary result. This does not by itself establish tractability of full closure or learned frame scheduling.
