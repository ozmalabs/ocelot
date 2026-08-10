# Dual-process core

The engine has an opt-in `dual_process` cognitive cycle. System 1 and System 2
are scheduling and control regimes over one graph, not separate minds or
literal anatomical modules.

## Runtime protocol

1. Settle only rules authored as `latency_class: hard_realtime`.
2. Graph rules compare fast and deliberative controller forecasts and either
   produce a `SystemOneCommit` or mint
   `SystemTwoEscalation{status: requested}`.
3. Every escalation must link through `recruits_task_set` to one or more
   `SystemTwoTaskSet` nodes whose `area` attributes name the admitted rule
   areas. An unscoped request remains pending.
4. The native scheduler gives each scoped request a separate fair budget. It
   changes exactly one request to the transient `admitted` execution token,
   settles only that request's non-hard-real-time areas, then changes a
   quiescent request to `serviced` (or yields a budget-saturated request back
   to `requested`) before admitting the next. Concurrent requests therefore
   neither open a union of areas nor observe one another as admitted.
5. A bounded hard-real-time motor fold follows successful System 2 settlement,
   so an executive result can become a same-tick motor bundle without reopening
   any soft area.
6. Deferred rules keep their dirty bits. No residual is discarded and the
   temporary scheduler mask is restored before the cycle returns.

The explicit legacy cycle plans are unchanged. The ordinary/default and
background-agent entry points automatically select this protocol when the
graph holds an enabled `DualProcessPolicy`; agents without that policy retain
unrestricted legacy settlement. Domains can also enter it explicitly by
creating a `DualProcessContext` and calling `dual_process_tick()` (or native
`run_cycle("dual_process")`).

## System 1

`seeds/dual_process_core.json` provides domain-neutral arbitration. A candidate
is eligible only when it is:

- current for the context epoch;
- explicitly grounded;
- reliable enough for the held policy;
- inside an externally measured predictive basin; and
- in the `ready` state.

Candidate evidence is integrated once per epoch with a graph-held leaky
accumulator. Eligible candidates compete by a graph-computed value:

`default value + accumulated evidence + affective urgency/valence + consolidation strength`

The affect input is the canonical agent-held `AffectiveState`, shared with PSI
through `DualProcessContext -uses_affective_state-> AffectiveState`. The legacy
`SystemOneAffect` silo is no longer used.

The score margin between the best candidate and its rivals produces
`decision_confidence`. Exact ties still use `ArgminRefusal`; near ties within
the policy's `conflict_margin` recruit System 2 rather than being hidden by
insertion order. Low winner reliability or a small evidence margin therefore
lowers confidence continuously.

## System 2 recruitment

The context holds a System 2 forecast:

- `system_two_expected_utility`;
- `system_two_reliability`;
- `system_two_latency`; and
- `system_two_effort`.

The leading System 1 candidate supplies its value and reliability. Novelty,
uncertainty, and prediction error add graded prospective value to deliberation;
latency and effort subtract cost. Their difference is mapped to a bounded
`system_two_weight` in `[0,1]`. System 2 is recruited when that weight crosses
the held threshold, when confidence is too low, for near/exact conflict, or
when no grounded in-basin default exists. This is an explicit graph-resident
arbitration calculation rather than a host switch or three independent novelty
thresholds.

## Compilation back to instinct

A verified `SystemTwoOutcome` links to the candidate it updates. Successful
experience computes outcome prediction error and incrementally changes:

- bounded `consolidation_strength`;
- `predicted_value`;
- `experience_count`; and
- a decaying `eligibility_trace`.

One success cannot create a full habit. Failed, devalued, extinguished, and
reversed outcomes weaken consolidation without deleting its history. Domains
with ephemeral per-tick candidates must fold these stable attributes into a
persistent policy/control node and initialise the next candidate from it.

If the outcome also links to a `ReflexNet`, the existing native `net_collapse`
teaching seam remains available. The rule graph supplies the teaching signal;
no Python optimizer or host decision is introduced.

## Biological interpretation

This is an engineering analogue, not a claim that two literal anatomical
systems exist. The supportable correspondence is:

- recurrent sensorimotor and corticostriatal competition supplies the cheap
  default;
- affective state changes valuation and urgency;
- graded conflict, confidence, controller reliability, prospective benefit,
  and control cost arbitrate access to a scoped recurrent workspace; and
- prediction-error-weighted repeated experience consolidates effortful
  behaviour into a cheaper habitual path, with extinction and reversal.

The correspondences are engineering hypotheses, not claims of one-to-one brain
regions. The architecture preserves one substrate and one learning economy
while making the fast/slow resource boundary explicit and testable.
