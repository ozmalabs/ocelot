# Admiration + gratitude — RESULTS

Registered design: `ADMIRATION_GRATITUDE_PREREG.md`. **The bug fix and
all 6 predictions confirmed.** A second real bug, found only by testing
before finalizing, is reported in Sec3 — not smoothed over.

## 1. Live run (`scripts/admiration_gratitude_demo.py`)

```
=== Bug fix: repeated positive incidents never crystallize Hate ===
crystallized_this_call(Hate)=False admiration_crystallized_this_call=True route=admiration gratitude_debt=2.0000
Hate nodes: 0, Admiration nodes: 1

=== Prediction 3: controllability gates admiration's routing ===
uncontrollable positive pattern: route=none admiration_ef=0.0000

=== Prediction 4: gratitude_debt accumulates on every positive incident ===
incident 0: gratitude_debt=1.0000 admiration_crystallized_this_call=False
incident 1: gratitude_debt=2.0000 admiration_crystallized_this_call=True
incident 2: gratitude_debt=3.0000 admiration_crystallized_this_call=False

=== Prediction 5: gratitude_debt amplifies admiration alpha (arousal held equal) ===
zero gratitude_debt: effective_admiration_alpha=0.6000 (expect base_alpha*(1+arousal)=0.6000)
gratitude_debt=1.0:  effective_admiration_alpha=1.2000 (expect base_alpha*(1+arousal)*(1+debt)=1.2000)

=== Prediction 6: per-target isolation ===
Kim (unaffected by Jo's admiration): gratitude_debt=0.0000 admiration_crystallized_this_call=False
```

## 2. The Sec0 bug fix, confirmed live

Verified directly (`scripts/admiration_gratitude_demo.py`'s own first
block): repeated POSITIVE incidents that, before this rung, wrongly
crystallized into a `Hate` node with `consequence_route:"removal"` now
correctly crystallize into `Admiration` instead — `Hate nodes: 0,
Admiration nodes: 1`. `test_negative_pattern_still_crystallizes_hate`
confirms the negative case is unaffected: a genuinely negative pattern
still crystallizes into `Hate`, never `Admiration`.

## 3. Predictions

1. **Bug fix**: `crystallized_this_call` (Hate) never fires for a
   positive pattern — `PASS`.
2. **Admiration crystallizes instead**, using the same threshold ladder
   — `PASS`.
3. **Controllability gates routing**: an uncontrollable positive pattern
   crystallizes but routes to `"none"` — `PASS`. `admiration_for`
   receives zero evidence (`admiration_ef=0.0000`).
4. **`gratitude_debt` accumulates on every positive incident**,
   independent of locus or crystallization — `PASS`. `1.0000 → 2.0000 →
   3.0000` across three incidents, including one (`incident 2`) that
   does NOT crystallize.
5. **`gratitude_debt` amplifies `admiration_for`'s crystallizing alpha**
   — `PASS`, isolated from arousal (`0.6000` at zero debt matches
   `base_alpha*(1+arousal)` exactly; `1.2000` at `debt=1.0` matches the
   full two-channel formula).
6. **Per-target isolation** — `PASS`. Kim's own `gratitude_debt` and
   crystallization status are completely unaffected by Jo's prior
   admiration.

## 3. A second real bug, found and fixed before finalizing

The first live check of `effective_admiration_alpha` at `gratitude_
debt=0` produced `1.2` where `0.6` was expected — `gratitude_debt=1`
gave the SAME `1.2`, as if the zero-debt run had already read
`debt=1.0`. Root cause, found directly: `gratitude_debt`, UNLIKE
`resentment_debt`, increments on the SAME `global_other` incident that
can crystallize its own consequence (`resentment_debt`'s own increment
is gated OFF on `global_other`, so it never faces this — it only
increments on the disconfirming `specific_act` incidents that do NOT
crystallize). Reading `gratitude_debt` fresh after `run_rules()`
therefore picked up THIS incident's own just-applied contribution,
violating the read-before/update-after convention every other coupling
in this arc uses. Fixed by snapshotting `gratitude_debt_before` at the
SAME point `hate_count_before`/`admiration_count_before` already
snapshot (before the first `run_rules()` call), and using that snapshot
— not a fresh post-run read — for the alpha formula. The RETURNED
`gratitude_debt` field still reports the post-incident value (consistent
with how `confirm_streak`/`resentment_debt` are already reported
post-incident) — only the alpha computation needed the earlier snapshot.

## 4. Honesty notes

**Does establish**: Weiner's controllability dimension and OCC's
Attribution branch are now symmetric across both signs — hate/pity for
negative patterns, admiration/none for positive ones, sharing one
crystallization ladder, one arousal-amplification formula, and one
never-decaying debt-ledger design (`resentment_debt`/`gratitude_debt`).
Found and fixed TWO real bugs in the process (the sign-blind gate; the
gratitude_debt ordering hazard), both confirmed live before shipping,
neither discovered by any prior test in this arc.

**Does NOT establish**: any positive-pattern analogue of the resentment
RESET mechanism (a disconfirming negative act discounted under arousal)
— named, deferred. Does NOT scale `gratitude_debt`'s per-incident
contribution to the act's own significance (a fixed `+1.0` per positive
incident, documented simplification). Does NOT model any downstream
reciprocity behavior.

## 5. Files

- `docs/research/psychology_affect/ADMIRATION_GRATITUDE_PREREG.md`
- `docs/research/psychology_affect/ADMIRATION_GRATITUDE_RESULTS.md` (this file)
- `domains/hate_attribution.py` (edited: admiration/gratitude wiring, the gratitude_debt ordering fix)
- `scripts/_build_hate_attribution_seed.py` (edited: `crystallize_hate`'s sign guard, new `crystallize_admiration` rule, `gratitude_debt` term, v1.7.0)
- `seeds/hate_attribution.json` (regenerated)
- `scripts/admiration_gratitude_demo.py` (new)
- `tests/test_admiration_gratitude.py` (10/10, new)
- `tests/test_hate_threshold_lower_bound_coupling.py` (3 tests updated to stage a coherent negative pattern, matching the corrected sign-aware gate; 5/5 still green)
