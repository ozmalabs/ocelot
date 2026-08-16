# Hate passion × resentment-debt coupling — PREREG

**Task**: user, immediately after `HATE_RESET_RESENTMENT_COUPLING_
RESULTS.md` landed: *"couple the passion/removal alpha to resentment
residue too."* `removal_desire_for`'s alpha at crystallization
(`HATE_PASSION_COUPLING_PREREG.md`, v1.1.0) is currently amplified by
raw `TargetArousal.level` only. This rung adds a SECOND, independent
amplifier: the accumulated resentment carried across every prior
`specific_act` this target has ever received, not just momentary arousal.

## 1. Theoretical grounding

- **McCullough, Fincham & Tsang (2003), "Forgiveness, Forbearance, and
  Time: The Temporal Unfolding of Transgression-Related Interpersonal
  Motivations," *Journal of Personality and Social Psychology*** —
  unforgiveness (sustained avoidance/revenge motivation after a
  transgression) does not decay the way ordinary negative affect does;
  where simple anger fades with time, UNRESOLVED grievance — resentment
  that survived a nominal act of forgiveness — persists and continues to
  feed later retaliatory motivation. This is the direct grounding for
  treating accumulated resentment as its OWN standing quantity, not
  merely a byproduct of momentary arousal (`TargetArousal`, which DOES
  decay, `SHARED_AROUSAL_EXCITATION_TRANSFER_PREREG.md`).
- **Nolen-Hoeksema (1991), "Responses to Depression and Their Effects on
  the Duration of Depressive Episodes," *Journal of Abnormal
  Psychology*** — rumination on unresolved negative events prolongs and
  intensifies their motivational aftermath; each `specific_act` that
  leaves a resentment residue (`HATE_RESET_RESENTMENT_COUPLING_PREREG.md`)
  is exactly such an unresolved event, and its residue is the SAME
  quantity this rung treats as accumulating "unfinished business" that
  strengthens the eventual removal motivation once hate does crystallize.
- **A "final straw" effect, made concrete**: this rung predicts that two
  targets who arrive at IDENTICAL crystallizing incidents, with identical
  momentary arousal, differ in how strongly the removal motive fires
  depending on how much unresolved resentment they each accumulated along
  the way — a real, common interpersonal-conflict pattern (repeated
  "forgiven" slights culminating in a disproportionately strong reaction
  to the incident that finally crystallizes the judgment).

## 2. Design

**`TargetPattern.resentment_debt`** (new attr, init `0.0`) — a
MONOTONICALLY ACCUMULATING ledger, never decremented (per McCullough et
al.'s own finding that unforgiveness does not simply fade with time,
unlike momentary arousal): every `specific_act` that leaves a resentment
residue (`HATE_RESET_RESENTMENT_COUPLING_PREREG.md` Sec2) ALSO adds that
SAME residue amount to `resentment_debt`:

```
resentment_debt <- resentment_debt + residue     [residue = confirm_streak * arousal_level/(1+arousal_level), the SAME quantity the reset coupling already computes]
```

Computed inside the SAME `derive_hate_attribution` Rule (one more `Plus`
effect on the `specific_act` branch) — zero new Rust, zero new Python
decisions, zero new independently-fitted constant (the residue formula is
reused verbatim from `v1.4.0`).

**The crystallizing incident's `removal_desire_for` alpha is now
amplified by BOTH channels, multiplicatively**:

```
effective_removal_alpha = base_alpha * (1 + arousal_level) * (1 + resentment_debt)   [both READ at the same pre-incident point the arousal-only version already reads at]
```

At `resentment_debt == 0` (no `specific_act` ever left a residue for this
target) this is EXACTLY `v1.1.0`'s original formula — a strict
generalization, not a redefinition.

## 3. Predictions

1. **At zero resentment_debt, `effective_removal_alpha` is unchanged**
   from the arousal-only formula — backward compatibility.
2. **A history WITH accumulated `resentment_debt` produces a HIGHER
   `effective_removal_alpha` at crystallization than an otherwise-
   identical history with none**, holding crystallization-time arousal
   equal — isolating `resentment_debt`'s own, independent contribution.
3. **The formula matches exactly**:
   `effective_removal_alpha == base_alpha*(1+arousal_level)*(1+
   resentment_debt)`.
4. **`resentment_debt` accumulates across MULTIPLE `specific_act`
   incidents** (monotonically, never decreasing), and per-target
   isolation holds — target A's accumulated resentment does not touch
   target B's own `resentment_debt` or `effective_removal_alpha`.

## 4. Scope boundaries

- `resentment_debt` does NOT decay — a deliberate reading of McCullough
  et al.'s own finding (unforgiveness persists where ordinary affect
  fades), not an oversight; a future rung could register a SEPARATE,
  much slower decay if warranted, but this rung does not add one.
- Does not couple `resentment_debt` back into `confirm_streak`'s own
  growth or the crystallization threshold itself — scoped exactly to
  `removal_desire_for`'s alpha, per the user's own instruction.
- Multiplicative composition with the arousal term (rather than a third
  additive term) is a design choice, not independently validated against
  data beyond the two citations' structural claims — same honesty class
  as every other functional-form choice in this arc.
