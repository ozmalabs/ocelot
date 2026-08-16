# Hate → pity via a Theory-of-Mind understanding of the other — RESULTS

Registered design: `HATE_PITY_TOM_UNDERSTANDING_PREREG.md`. **All 4
predictions confirmed.**

## 1. Live run (`scripts/hate_pity_tom_understanding_demo.py`)

```
=== Prediction 1: no understanding at all -> routes to removal ===
consequence_route=removal removal_ef=0.5400 pity_ef=0.0000 controllability_ef=0.0000

=== Prediction 2: exculpatory understanding before crystallization -> routes to pity ===
consequence_route=pity removal_ef=0.0000 pity_ef=0.3000 controllability_ef=-0.6000

=== Prediction 3: boundary -- zero controllability (no info) routes to removal ===
controllability_for external_field before crystallization: 0.0000
consequence_route=removal

=== Prediction 4: per-target isolation ===
Kim (no understanding, unaffected by Jo's): consequence_route=removal
Jo (own exculpatory understanding): consequence_route=pity
```

## 2. Predictions

1. **No understanding at all routes to removal** — `PASS`, byte-
   identical to this arc's behavior before this rung (`removal_ef=0.54`,
   matching `HATE_RESENTMENT_PASSION_COUPLING_RESULTS.md`'s own
   arousal-only figures at this parameter point; `pity_ef=0.0`).
2. **Sufficient exculpatory understanding routes to pity instead** —
   `PASS`. `removal_desire_for` receives ZERO evidence
   (`removal_ef=0.0000`); `pity_for` receives it instead
   (`pity_ef=0.3000`, unamplified `base_alpha`, per design).
3. **The routing matches the sign test exactly at the boundary** —
   `PASS`. `controllability_for` untouched (`0.0000`) still routes to
   `removal` — Ross 1977's Fundamental Attribution Error default,
   confirmed as the literal `>=0` boundary case, not merely the
   comfortably-positive case.
4. **Per-target isolation holds** — `PASS`. Kim, with no understanding
   recorded, routes to `removal` in the SAME substrate where Jo's own
   accumulated understanding routes Jo to `pity` — Jo's ToM belief about
   Jo's own target never touches Kim's independent routing.

## 3. Honesty notes

**Does establish**: Weiner's third attribution dimension —
controllability — is now built alongside the already-landed locus and
stability dimensions, completing the model this arc has been
constructing piece by piece since `ATTRIBUTION_LOCUS_AS_RESIDUAL_
PREREG.md`. The controllability read is genuinely the resident's OWN
Theory-of-Mind belief about the target (`controllability_for:<target>`,
a real, if minimal, per-(resident,target) CAN belief) — the first
resident-of-resident ToM CONTENT in bigville, confirmed by investigation
before building rather than assumed (this arc's three pre-existing ToM
systems — narrative-character false-belief tracking, ToM vocabulary
scaffolding, and the agent's own conversational-partner tracker — none
modeled a specific other resident's circumstances). Hate's own stability
(`confirm_streak`, crystallization) is completely unaffected by
understanding — the pattern is still recognized as real and stable; only
its motivational OUTCOME branches, exactly matching Weiner's own claim
that the three dimensions are orthogonal.

**Does NOT establish**: any re-routing of an ALREADY-crystallized hate —
understanding arriving after crystallization has no effect, a named,
deferred follow-on. Does NOT couple pity to arousal or resentment_debt
(a deliberate scope decision: pity is not a passion channel in Weiner's
model). Does NOT model any downstream behavioral consequence of holding
pity (e.g., increased helping, which Weiner's own original 1980 study
measured) — scoped exactly to the routing decision.

## 4. Files

- `docs/research/psychology_affect/HATE_PITY_TOM_UNDERSTANDING_PREREG.md`
- `docs/research/psychology_affect/HATE_PITY_TOM_UNDERSTANDING_RESULTS.md` (this file)
- `domains/hate_attribution.py` (edited: `pity_for`/`controllability_for` Concepts, `record_understanding_incident`, `consequence_route` dispatch)
- `scripts/_build_hate_attribution_seed.py` (edited: `_consequence_route_term`, `tracks_pity`/`tracks_controllability` productions, v1.6.0)
- `seeds/hate_attribution.json` (regenerated)
- `scripts/hate_pity_tom_understanding_demo.py` (new)
- `tests/test_hate_pity_tom_understanding.py` (6/6, new)
