# "You can still escalate effectively nothing" — verification against the
# real conflict literature

**Task**: user, after the zero-severity fix: *"you can still escalate
effectively nothing - research and ensure this behaviour matches. (i.e.
finding something to argue about)"*. Distinct from the bug
`DISPUTE_SEVERITY_AS_RESIDUAL_RESULTS.md` fixed (a dispute over LITERALLY
nothing — identical beliefs, zero residual — could still escalate, which is
now structurally impossible). This is about a dispute over ALMOST nothing —
a trivial, minor, genuinely-existing residual — still escalating when the
relational/social context is fraught. **Exploratory-then-confirmatory,
stated honestly**: the probe below ran BEFORE this document, prompted
directly by the user's own framing; what follows registers it as a
locked-in, tested behavior rather than presenting it as blind prediction.

## 1. The probe

The smallest possible NONZERO residual `StructSim` can produce over a
3-slot predication tuple is `1/3` (one slot differs, two agree) —
about as minor a factual quibble as a real disagreement can be (e.g. "one
dollar" vs "two dollars" on an otherwise identical claim). Tested the SAME
trivial quibble across relational contexts:

```
trivial disagreement (tiny factual quibble), rival + 5 witnesses: 0.333 -> escalate
SAME trivial disagreement, close friends + private:               0.333 -> defuse
SAME trivial disagreement, strangers + private (no audience):     0.333 -> escalate
```

The topic never changes. Only the relationship and audience change. The
outcome flips.

## 2. Does this match real behavior? Yes — this is a well-documented
   phenomenon, not an artifact

- **Coser, L. (1956), *The Functions of Social Conflict*** — the
  foundational distinction between REALISTIC conflict (genuinely about the
  disputed object) and NON-REALISTIC conflict, where "the object of
  conflict... is not occasioned by the specific object... conflict here is
  not means to an end but an end in itself" — tension seeking release
  attaches to whatever pretext is available. This is the precise, named
  phenomenon: when relational tension already exists, the SPECIFIC issue is
  substitutable — almost any real disagreement, however small, can carry it.
- **Simmel, G. (1908), *Conflict*** — Coser's own source: conflict is a
  form of *sociation* whose antagonism can attach to essentially any
  content once the relational precondition exists.
- **Gottman, J. (1994), *What Predicts Divorce*** — empirically, the large
  majority (Gottman's own figure: ~69%) of recurring marital conflicts are
  "perpetual problems" that resurface through trivial, seemingly arbitrary
  triggers (a specific chore, a tone of voice) — the trigger's own
  magnitude is a poor predictor of whether it escalates; the couple's
  underlying relational state is the real driver.
- **Retzinger, S. (1991), *Violent Emotions: Shame and Rage in Marital
  Quarrels*** — the most directly relevant citation: couples escalate over
  objectively minor triggers through unacknowledged SHAME-RAGE spirals —
  directly connecting to `RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_RESULTS.md`'s
  own finding that an escalated dispute IS a shame-producing correction
  style. The two mechanisms this session built are not just compatible —
  they describe the same phenomenon from two different literatures,
  independently.

**The user's own framing — "finding something to argue about" — is the
correct informal name for Coser's "non-realistic conflict."** The
mechanism's behavior (trivial residual + fraught relationship → escalate;
same trivial residual + secure relationship → defuse) is exactly what this
literature predicts, not an unintended side effect of the pressure formula.

## 3. The line this draws, precisely

- **Zero residual (identical beliefs) → structurally cannot escalate** —
  fixed in `dispute_severity_from_beliefs.json`: there is no pretext
  available at all, because there is no disagreement at all. Confirmed
  correct and unchanged by this verification.
- **Any nonzero residual, however small → CAN escalate, given enough
  relational/audience tension** — confirmed here as CORRECT, literature-
  matching behavior, not a bug to fix. The mechanism does not, and should
  not, scale the minimum escalatable severity up with relationship quality
  in the opposite direction (i.e. "friends need a bigger issue to fight
  about" is not modeled as a hard floor — it falls out of the SAME
  `(1-closeness)` suppression term already registered in
  `RULE_DISPUTE_ESCALATION_PREREG.md` Sec2, not a new mechanism).

## 4. Locked in as a standing regression

`tests/test_dispute_severity_from_beliefs.py` gains 2 new tests:
`test_minimal_nonzero_residual_still_escalates_under_relational_tension`
and `test_same_minimal_residual_defuses_under_secure_relationship` — so a
future change that "fixes" trivial disputes to never escalate (mistaking
this for the same class of defect as the zero-severity bug) breaks a named,
literature-cited regression instead of silently regressing.

## 5. Honesty notes

**Does establish**: the mechanism's behavior on trivial-but-real
disagreements matches a well-documented, independently-converging
psychological/sociological literature (Coser, Simmel, Gottman, Retzinger),
and connects directly to this session's own shame/guilt bridge finding.

**Does NOT establish**: that `1/3` is the "correct" minimum quantum for a
real trivial dispute, or that `StructSim`'s exact-atom-match granularity
(no partial credit for near-miss content) is the right resolution for this
phenomenon in general — an honest limitation of the reused primitive,
already named in `DISPUTE_SEVERITY_AS_RESIDUAL_RESULTS.md` Sec4, not
revisited here. Nothing about WHY relational tension exists in the first
place (that's the `band_code`/CAN belief-network machinery, upstream and
unchanged).

## 6. Files

- `docs/research/psychology_affect/TRIVIAL_DISPUTE_ESCALATION_VERIFICATION.md` (this file)
- `tests/test_dispute_severity_from_beliefs.py` (+2 tests, 12/12)
