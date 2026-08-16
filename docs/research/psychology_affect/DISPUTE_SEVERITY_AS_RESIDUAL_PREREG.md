# Dispute severity as a residual between two held beliefs — PREREG

**Task**: user, on reviewing the rule-dispute mechanism: *"A dispute is the
residual between two held beliefs."* Correct, and a real defect:
`rule_dispute_escalation.json`'s `issue_severity` was a hand-set scalar
(0.2, 0.9, ...) fed in by the caller — exactly the anti-pattern CLAUDE.md's
own "SHAPES, NOT NUMBERS" section names: *"a new subsystem invents a scalar
knob... instead of decoding against a codebook."* This rung replaces it
with a genuinely COMPUTED residual.

## 1. The fix

`StructSim(a, b)` (`runners/dsl/src/term.rs::struct_sim_value`, pre-existing,
zero new Rust) already computes a graded structural similarity over
predication tuples — position-wise exact match on atoms, averaged, with
coverage discount on length mismatch. Confirmed empirically before
registering this design (not assumed):

```
StructSim(["pays_pot","free_parking",True], ["pays_pot","free_parking",False]) = 0.667
StructSim(["is_a","cat","mammal"],           ["is_a","cat","mammal"])          = 1.0
```

`issue_severity := 1.0 - StructSim(claim.pred, truth.pred)` — a claim that
flatly contradicts the rule on the outcome slot but agrees on subject/
predicate gets a MODERATE residual (0.333), not the previous demo's
hand-picked 0.9; two identical beliefs get residual 0.0 — **a dispute over
nothing produces no dispute, structurally, not by a caller remembering to
pass 0.0.**

## 2. Design

**Strictly additive** (matches the prior bridge's own discipline): a NEW
seed, `seeds/dispute_severity_from_beliefs.json`, depending on
`rule_dispute_escalation` — neither that seed nor
`self_conscious_emotions.json` is edited.

- `HeldBelief{pred}` — a predication triple `[relation, arg0, arg1]` as a
  native graph-list value (confirmed node attrs accept this directly, not
  just scalars).
- `BeliefDisagreement{band_code, audience_gain}` — the social-context
  wrapper: `-claims-> HeldBelief` (what the disputant asserts), `-truth->
  HeldBelief` (the rulebook-grounded ground truth), `-has_witness->
  WitnessPresence` (0+, reusing the existing type verbatim).
- Rule 1 mints a `DisputeContext{issue_severity: 1-StructSim(...),
  band_code, audience_gain}` (copying the social fields, computing severity)
  plus its own `RuleDisputeSignal`, reusing `rule_dispute_escalation`'s
  OWN `has_signal` production unchanged.
- Rule 2 carries each `WitnessPresence` over to the new `DisputeContext`,
  mirroring the dispute→self-conscious bridge's own per-witness pattern
  exactly (same dedup idiom).

`band_code`/`audience_gain`/witnesses stay caller-supplied data — the
user's claim is specifically about the ISSUE (what's being disputed), not
who is disputing it or who is watching, which were already correctly
scoped as external context in the prior rung.

## 3. Predictions

1. **Identical beliefs → no dispute is minted at all.** Two structurally
   identical predications (`StructSim=1.0`) produce NO `DisputeContext` —
   `BeliefDisagreement` stays unbridged. **Revised live, not as
   registered**: the first run of this rung found `issue_severity=0.0`
   alone does NOT floor `rule_dispute_escalation`'s own pressure formula at
   `<=0` — its audience/closeness terms are additive and independent of
   severity, so 3 strangers' ambient audience pressure alone pushed a
   completely nonexistent disagreement to `escalate`. Fixed by gating the
   bridge itself (`StructSim<1.0`) on a genuine residual existing, rather
   than relying on `rule_dispute_escalation`'s own formula to self-floor
   (it was never designed to, and is correctly left unedited).
2. **Full contradiction on the outcome slot alone → moderate residual, not
   maximal.** A claim/truth pair that shares relation+subject but flips the
   outcome (the Free Parking case) produces `issue_severity≈0.333`, NOT the
   old demo's hand-picked 0.9 — a real, measured value the mechanism
   computes, not a number chosen to make the demo escalate.
3. **A claim that shares NOTHING with the truth (wrong relation, wrong
   subject, wrong outcome) produces the highest residual** — confirms the
   residual is graded (more disagreement = higher severity), not binary.
4. **End-to-end**: feeding a computed, non-cherry-picked residual through
   the UNCHANGED `rule_dispute_escalation` → `self_conscious_emotions`
   bridge chain still produces sensible, non-degenerate outcomes (not every
   real disagreement collapses to `none`/`defuse` just because the computed
   severity is lower than the old hand-picked value).

## 4. Scope boundaries

- Does not change how `attribution_locus` is decided (still supplied data,
  per both prior rungs) — this rung is scoped to `issue_severity` only,
  the specific claim the user made.
- Does not build the NLP path that would produce `HeldBelief.pred` from
  real text (that's `cognitive_rule_frames.py`'s `read_rule_document` +
  a genuine claim-extraction step, unbuilt) — `HeldBelief` nodes are
  supplied as data (predication triples), exactly as `DisputeContext`'s
  other fields always have been.
- `StructSim`'s position-wise atom comparison is exact-match only (no
  semantic near-miss credit, e.g. "the pot" vs "the money" score 0, not
  partial) — an honest limitation of the reused primitive, not patched
  here.
