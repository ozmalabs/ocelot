# Self-complexity-weighted domain coupling — RESULTS

Registered design: `SELF_COMPLEXITY_COUPLING_PREREG.md`. Built: `can_self_
worth_bridge.py::mint_domain_self_worth`'s `coupling_weight` is now
computed (`base_coupling / (existing_domain_count + 1)`), not a flat
constant. Regressed by `tests/test_self_complexity_coupling.py` (5/5
green), with 2 pre-existing tests updated to the now-correct behavior.

## 1. What this answers

User, auditing this arc's constants: *"Check for other scalars built in
recently - they all need to be weighted."* `coupling_weight=0.6` was the
clearest offender: a flat constant applied to EVERY new domain regardless
of the resident's own held structure. Fixed by weighting it against a
REAL, observed graph quantity — how many domains this resident has
already differentiated — per Linville (1985, 1987)'s self-complexity
buffering: more differentiated self-aspects buffer a new one from fusing
tightly with the global self.

## 2. A real, honest interaction with an already-found engine property

`existing_domain_count=0` (a resident's first domain) gets full
`base_coupling=0.6`, byte-identical to pre-audit behavior. But
`existing_domain_count=1` (a SECOND domain) gets `0.6/2=0.3` — which
`DOMAIN_SELF_WORTH_PROJECTION_RESULTS.md` already measured is BELOW this
engine's discrete-3-state threshold (`≈0.366` at `temperature=1.5`). So
under the ACTUAL, unmodified engine mechanism, self-complexity buffering
is a SHARP STEP here, not Linville's presumably graded original finding —
registered as a prediction before building, not discovered and smoothed
over. **Two pre-existing tests broke on this exact, predicted
consequence** — `test_two_domains_hold_opposite_beliefs_simultaneously`
(renamed `..._independent_...`) and `test_a_different_domain_is_
unaffected_by_disputes_elsewhere` both asserted a second domain would
project global `1.0`; under the corrected mechanism it correctly lands
`0.0`. Both updated to assert the true, predicted behavior — not reverted,
not the coupling formula weakened to keep the old assertions passing.

## 3. Predictions — all 4 registered, all 4 held

1. **First domain unaffected** — `PASS`, exactly `0.6/1=0.6`, above
   threshold, full projection.
2. **Second domain couples more weakly and lands neutral** — `PASS`,
   `0.6/2=0.3`, below threshold.
3. **Buffering persists as more domains accumulate** — `PASS`; a 5th
   domain (`existing_domain_count=4`, `coupling_weight=0.6/5=0.12`) still
   lands neutral, the denominator only grows.
4. **Re-minting an existing domain does not perturb it** — `PASS`; minting
   a SECOND domain in between two lookups of the FIRST does not recompute
   or reset the first domain's own already-established coupling/state.

No null.

## 4. Honesty notes

**Does establish**: coupling strength is now a real, graph-observed
quantity (domain count), not a hand-picked constant — and the fix
immediately surfaced a genuine, previously-latent property of this
codebase's existing discrete CAN mechanism (the hard threshold) that two
prior tests' assumptions had never been checked against, because
`coupling_weight` had never varied before this rung.

**Does NOT establish**: that the SHARP step (vs. Linville's presumably
graded original effect) is the psychologically correct shape — an
inherited, unmodified engine property, named explicitly, not addressed
here (`SELF_COMPLEXITY_COUPLING_PREREG.md` Sec4). Domain-SIMILARITY
weighting (public speaking and debate plausibly buffer each other less
than public speaking and cooking) is not modeled — Linville's own theory
is about sheer count, not semantic relatedness; a named, separate
follow-on. `belief_plasticity`/`alpha` and `audience_gain`, both flagged
in the same audit, remain un-fixed "numbers from nowhere" — not addressed
in this rung.

## 5. Files

- `docs/research/psychology_affect/SELF_COMPLEXITY_COUPLING_PREREG.md`
- `docs/research/psychology_affect/SELF_COMPLEXITY_COUPLING_RESULTS.md` (this file)
- `domains/can_self_worth_bridge.py` (edited: `mint_domain_self_worth`'s `coupling_weight` -> `base_coupling`, computed via `_existing_domain_self_worth_count`)
- `tests/test_self_complexity_coupling.py` (5/5, new)
- `tests/test_domain_self_worth_projection.py` (edited: 1 test renamed + corrected to the true behavior)
- `tests/test_rule_dispute_full_pipeline.py` (edited: 1 test corrected to the true behavior)
