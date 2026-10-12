# Chained endemic self-improvement v1: preregistration (2026-10-10, tranche 24)

## Claim under test

An improvement the agent adopts changes what its improver can do next, and the agent notices this and acts on it without a human. Specifically, after an adoption the agent reopens a concern on which every variation had abstained, and fixes it.

## Motivation (measured before the claim)

In tranche 23's production run, concern 24965 ("statements with no `language_statement_act`") abstained: no held arbitration/reply pair was one guard away. The agent then adopted `defer_response_assertion…__interaction_relation_none_generalised`. Rebuilt afterwards, the builder succeeded: the new pair was one guard (`language_statement_act`) from the class. The loop never asked again, for three reasons:
- `variation_pick` excluded an abstained family forever;
- no rule reopened an abstained concern;
- in production a retry executed only if another concern happened to be pending.

## Change

`scripts/gen_reopen_on_new_capability.py`:
- **`self_optimisation` v1.6.0** stamps `abstain_epoch` (the count of Adoptions) on an abstention.
- **`variation_ops` v1.21.0** makes an abstention exclude its family only at its own epoch.
- **`instruction_repair_retry` v1.4.0** adds `irr_reopen_on_new_capability`: a promoted `unanswered`/`comprehension` concern whose every experiment abstained at an older epoch is marked for retry, at most once per epoch and at most `max_reopens` = 2 times.
- **`cognitive_scheduler` v1.0.3** requests the `concern` host action while a retry is marked.
- The `disposition_generalise` and `deep_reader_correct` builders now read the live StandingConcern of a re-promoted concern, not its retired predecessor.

## Setup

- **Harness:** `endemic_rsi_daemon_v1.py persona shadow 120`, `ERSI_LABEL=t24`.
- **Arms:**
  - `on`;
  - `noreopen` (`ERSI_REOPEN=0`: `max_reopens` = 0, everything else the same);
  - `off` (self-promotion off).
- **Retest:** post-run and fresh boot, as in v2. The fresh baseline is booted with promotion off.

## Gates

| Gate | Condition |
|---|---|
| C1 chain | `on`: at least one concern reopened by the agent, and at least one adoption from an experiment on a reopened concern whose source rule is an earlier adoption's rule (a rule name ending `_generalised` used as the generalisation source) |
| C2 gain over no-chain | `on` post-run error/none < `noreopen` post-run error/none |
| C3 no harm | `on`: 0 turns from non-error (fresh) to error (post-run); the 6 control imperatives keep their fresh-boot class |
| C4 attribution | `off`: 0 adoptions; `noreopen`: 0 reopened concerns |
| C5 integrity | 0 machinery adoptions |
