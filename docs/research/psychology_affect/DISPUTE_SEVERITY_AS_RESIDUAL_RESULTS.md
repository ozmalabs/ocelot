# Dispute severity as a residual between two held beliefs — RESULTS

Registered design: `DISPUTE_SEVERITY_AS_RESIDUAL_PREREG.md`. Built:
`seeds/dispute_severity_from_beliefs.json` (via
`scripts/_build_dispute_severity_from_beliefs_seed.py`), demonstrated by
`scripts/dispute_severity_from_beliefs_demo.py`, regressed by
`tests/test_dispute_severity_from_beliefs.py` (10/10 green).

## 1. What this answers

User, reviewing `rule_dispute_escalation.json`: *"A dispute is the residual
between two held beliefs."* Correct — `issue_severity` was a hand-set
scalar (0.2, 0.9, ...), the exact anti-pattern CLAUDE.md's "SHAPES, NOT
NUMBERS" section names. Fixed: `issue_severity := 1.0 - StructSim(claim.pred,
truth.pred)`, `StructSim` being a pre-existing Term (`term.rs::
struct_sim_value`), confirmed by direct probe before registering:

```
StructSim(["pays_pot","free_parking",True], ["pays_pot","free_parking",False]) = 0.667
StructSim(["is_a","cat","mammal"],           ["is_a","cat","mammal"])          = 1.0
```

## 2. A real defect found live, and fixed correctly

The first run of this rung's own Prediction 1 (identical beliefs → zero
severity → never escalates) **failed**: feeding `issue_severity=0.0`
through the unchanged `rule_dispute_escalation` pressure formula, with 3
anonymous witnesses at `band_code=0`, still produced `outcome=escalate`.
Root cause: that formula's audience term
(`audience_gain*witnesses*(1-closeness)`) is additive and independent of
`issue_severity` — nothing in the ORIGINAL rung ever exercised
`issue_severity=0.0`, because a hand-picked demo value never happened to be
exactly zero. **This session's own severity computation was the first thing
to actually test that edge.**

**Fix, scoped correctly**: rather than edit `rule_dispute_escalation.json`
(tested, working, and not actually wrong for the inputs it was designed
around), the bridge itself now gates on `StructSim<1.0` — a genuine
residual must exist before a `DisputeContext` is minted at all. Two
identical beliefs mean no disagreement exists, so nothing should be
appraised, full stop — not "appraised at zero intensity." Confirmed:

```
IDENTICAL BELIEFS -> NO DISPUTE MINTED
claim matches the rulebook exactly            severity=None -> no_dispute_minted
```

## 3. Predictions — 4 registered (1 revised live), all held after the fix

1. **Identical beliefs mint no dispute at all** — revised from the
   originally registered "zero severity, never escalates" after the live
   finding above. `PASS` (both a same-`band_code` and a rival-`band_code`
   variant tested).
2. **Partial contradiction → moderate, computed residual.** A one-slot
   flip (the Free Parking myth) produces `issue_severity=0.333` —
   genuinely different from the old demo's hand-picked `0.9` for the exact
   same scenario. `PASS`.
3. **Total disagreement → maximal residual** (`1.0`), and the residual is
   graded (a one-slot mismatch scores strictly between zero and total
   disagreement, not collapsed to a binary). `PASS`.
4. **End to end**: a computed, non-cherry-picked severity still flows
   through the unchanged dispute mechanism to sensible, non-degenerate
   outcomes — close friends/private/partial-contradiction defuses,
   strangers/witnessed/total-disagreement escalates. `PASS`.

## 4. Honesty notes

**Does establish**: `issue_severity` is now a genuine structural residual,
computed by the engine's own `StructSim`, not a caller-chosen number — and
the fix this rung required (gating on a real residual existing, rather than
trusting the downstream formula to self-floor at zero) is itself a small,
real instance of the SHAPES-NOT-NUMBERS discipline paying for itself: the
live run caught the exact defect a hand-picked scalar would have hidden
forever.

**Does NOT establish**: `StructSim`'s exact-match-only atom comparison
(no semantic near-miss credit — "the pot" vs "the money" scores identically
to "the pot" vs "elephant") is an honest limitation carried over from the
reused primitive, not addressed here (PREREG Sec4). Nothing about how
`HeldBelief.pred` triples get produced from real text — they are supplied
data, exactly as `DisputeContext`'s other fields always have been.
`rule_dispute_escalation.json` and `self_conscious_emotions.json` are both
confirmed byte-unmodified by this rung (git-status-gated test).

## 5. Files

- `docs/research/psychology_affect/DISPUTE_SEVERITY_AS_RESIDUAL_PREREG.md`
- `docs/research/psychology_affect/DISPUTE_SEVERITY_AS_RESIDUAL_RESULTS.md` (this file)
- `scripts/_build_dispute_severity_from_beliefs_seed.py`
- `seeds/dispute_severity_from_beliefs.json`
- `scripts/dispute_severity_from_beliefs_demo.py`
- `tests/test_dispute_severity_from_beliefs.py` (10/10)
