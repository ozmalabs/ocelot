# Self-efficacy — RESULTS

Registered design: `SELF_EFFICACY_PREREG.md`. **All 5 predictions
confirmed.**

## 1. Live run (`scripts/self_efficacy_demo.py`)

```
=== Predictions 1/2/3: success raises, failure lowers, persistence flips ===
success 0: efficacy=0.3000 disposition=persist
success 1: efficacy=0.6000 disposition=persist
success 2: efficacy=0.9000 disposition=persist
failure 0: efficacy=0.6000 disposition=persist
failure 1: efficacy=0.3000 disposition=persist
failure 2: efficacy=0.0000 disposition=persist
failure 3: efficacy=-0.3000 disposition=avoid
failure 4: efficacy=-0.6000 disposition=avoid
failure 5: efficacy=-0.9000 disposition=avoid

=== Prediction 4: no cross-domain generalization ===
monopoly efficacy (unaffected by chess history): 0.0000

=== Prediction 5: sync wires the confirmed-dead AffectiveState.competence field ===
before sync: 0.0000
after sync: -0.9000 (returned: -0.9000)
```

## 2. Predictions

1. **Repeated success raises `self_efficacy_for`** — `PASS`. `0.3000 →
   0.6000 → 0.9000`.
2. **Failure lowers it, same Concept, opposite sign** — `PASS`.
   `0.9000 → 0.6000 → 0.3000 → 0.0000 → -0.3000 → ...`.
3. **Persistence/avoidance flips with the sign** — `PASS`. The
   disposition stays `"persist"` through `efficacy=0.0000` (the
   registered inclusive boundary) and flips to `"avoid"` at the FIRST
   negative value (`-0.3000`), exactly at the threshold.
4. **No cross-domain generalization** — `PASS`. `monopoly` reads exactly
   `0.0000` despite `chess` having accumulated substantial negative
   history on the same resident — confirmed structurally too:
   `test_mint_domain_self_efficacy_has_no_coupling_edges` verifies zero
   `causal_influence` edges exist at all (unlike `self_worth`'s own
   domain Concepts).
5. **`sync_competence_to_affective_state` wires the confirmed-dead
   field** — `PASS`. `AffectiveState.competence` reads `0.0000` before
   sync (the dead default `doom_dual_process_ingest.py` leaves it at)
   and exactly `-0.9000` — matching the efficacy Concept's own current
   value — after.

## 3. Honesty notes

**Does establish**: a genuinely different behavioral primitive from
everything else in this arc — self-efficacy drives a PERSISTENCE-VS-
AVOIDANCE disposition, not mood or attribution. Deliberately built FRESH
and UNCOUPLED per domain (confirmed via a structural test, not just
behavioral), a real design contrast with `self_worth`'s own coupled,
generalized-expectancy structure — the two Bandura/Rotter theories
disagree on task-specificity, and this rung's implementation reflects
that disagreement rather than reusing `self_worth`'s pattern by default.
Closes the confirmed-dead `AffectiveState.competence` field with a real,
evidence-driven value for the first time.

**Does NOT establish**: any integration with PSI's own `ModulatorState`/
leading-drive competition (`psi_select_initial_leading_drive`/
`psi_switch_leading_drive`) — the sync is a direct, mechanical write to
the schema field, not an attempt to make self-efficacy participate in
drive selection. A real, larger, deferred integration. Does NOT couple
self-efficacy to arousal or a debt-style ledger — Bandura's theory gives
no basis for a passion channel here, by design.

## 4. Files

- `docs/research/psychology_affect/SELF_EFFICACY_PREREG.md`
- `docs/research/psychology_affect/SELF_EFFICACY_RESULTS.md` (this file)
- `domains/self_efficacy.py` (new)
- `scripts/self_efficacy_demo.py` (new)
- `tests/test_self_efficacy.py` (9/9, new)
