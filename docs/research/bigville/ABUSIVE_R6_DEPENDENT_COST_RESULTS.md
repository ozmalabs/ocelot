# ABUSIVE R6 — DEPENDENT/RESOURCE-COST DEVALUATION OF ESCAPE'S VALUE — RESULTS (block 361000)

Pre-registration: `ABUSIVE_R6_DEPENDENT_COST_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_BARRIERS_AND_RETURN_SCOPING.md` verbatim, committed
before this confirmatory measurement, and states plainly why this rung's
pilot was an analytic + deterministic-trace derivation, matching R4's own
methodological precedent, rather than an off-block statistical sweep).
Full-power numbers: `results/abusive_r6_dependent_cost.json` (N=200 per
arm). Gate: `tests/test_abusive_r6_migrated.py`. Base engine: own build,
`source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new Term.**

## Harness-neutrality check — PASSES

N=200 episodes, 60-tick episodes, ZERO-DEPENDENTS arm (`dependent_cost=0.0`,
R4's own CONTINGENT resolution, unchanged):

| metric | R6's ZERO-DEPENDENTS (measured) | R4's own landed CONTINGENT arm |
|---|---|---|
| final `contingency_prior` (mean) | **0.9999999996370** | 0.99999999964 |
| escape-attempt RATE (mean) | **1.000 [1.000, 1.000]** | 1.000 [1.000, 1.000] |

`r6_appraise_attempt_dependent` reduces to `c.individual_cost :=
attempt_cost + 0.0`, numerically identical to R4's own
`r4_appraise_attempt` write, and the confirmatory run reproduces R4's own
landed contingent-arm numbers to within 6 significant figures on the
prior (the small residual difference is expected: R6 draws its
per-episode initial-belief jitter from its own block's seed stream,
`SEED_BASE=361000`, not R4's `292000` — a different, non-identical draw of
the same distribution, not a different mechanism) and EXACTLY on the
attempt rate (deterministic and jitter-insensitive once the belief is
comfortably above breakeven at `p0=0.5`). **`harness_neutral: true`** — R6's
new rule adds nothing to R4's own composition at its neutral setting, as
designed. This was a genuinely failable check: had R6's new rule read or
written anything beyond `dec`'s own fixed attrs, or fired at the wrong
order relative to `r4_appraise_attempt`, this baseline would have been
perturbed and would be reported as a composition bug.

## Headline — G-headline PASSES

N=200 episodes per arm, 60-tick episodes, both arms under IDENTICAL
(deterministic, always-succeeds) escape contingency — the only axis varied
is `dependent_cost`:

| arm | `dependent_cost` | final `contingency_prior` (mean [95% CI]) | escape-attempt RATE (mean [95% CI]) |
|---|---|---|---|
| **ZERO-DEPENDENTS** | 0.0 | 0.99999999964 [0.99999999963, 0.99999999964] | **1.000 [1.000, 1.000]** |
| **HIGH-DEPENDENTS** — *headline arm* | 10.0 | 0.49980 [0.49293, 0.50667] | **0.000 [0.000, 0.000]** |

- HIGH-DEPENDENTS' attempt rate is CI-separated **below** ZERO-DEPENDENTS'
  (`0.000 < 1.000`, trivially, both being zero-variance point CIs). ✓
- **`headline_pass: true`** — despite escape being EQUALLY, PROVABLY
  contingent in BOTH arms (the exact same deterministic, always-succeeds
  outcome-resolution function is used in both), the HIGH-DEPENDENTS agent
  never attempts even once, across all 200 episodes. Material cost alone —
  independent of any belief about whether escape would work — suppressed
  the attempt entirely, exactly as B1 of the scoping doc predicted.

### The control was genuinely failable, not rigged

Nothing in the value-economy composition guarantees the HIGH-DEPENDENTS arm
suppresses attempts: had `HIGH_DEPENDENT_COST` been set below the
analytically-derived 7.0 threshold (`escape_value − attempt_cost = 10.0 −
3.0`), the attempt candidate's value would have been positive at some
achievable `contingency_prior`, and the two arms would have attempted at
comparable rates — the claim "material barriers can override even a
proven-working escape route" would have been wrong, reported as such per
the prereg's own falsification bar. The chosen operating point
(`dependent_cost=10.0`, net value `−3.0` at the ceiling) is a disclosed,
analytically-derived, pilot-confirmed point, not an inevitability of the
Argmax-plus-subtracted-term template.

## The dissociation (the rung's most interesting finding — predicted in the prereg, confirmed here)

This is the result worth reading carefully, because the number alone
(`attempt_rate = 0.0`) understates what makes it mechanistically distinct
from R4's own trap:

| metric | R6 HIGH-DEPENDENTS | R6 ZERO-DEPENDENTS | R4's own landed NON-CONTINGENT arm |
|---|---|---|---|
| final `contingency_prior` (mean) | **0.4998** | 0.99999999964 | 0.2560 |
| escape-attempt RATE (mean) | 0.000 | 1.000 | 0.0314 |

The HIGH-DEPENDENTS arm's final belief (`0.4998`) sits almost exactly on
its OWN initial, genuinely-uninformative starting value
(`P0_MEAN=0.5 ± P0_JITTER=0.05` per-episode jitter) — it has not moved at
all, at the population level, from where it started. This is qualitatively
different from R4's own non-contingent arm, whose belief is **actively
driven down** from the same `0.5`-mean starting point to `0.2560` by two
observed, disconfirming, blocked-attempt outcomes before the agent freezes.

**Why the HIGH-DEPENDENTS belief never moves: it never receives any
evidence, ever.** `r4_belief_update` (R4's own rule, unmodified) only fires
on a tick where a fresh outcome has been delivered
(`outcome_epoch > processed_epoch`), and an outcome is only ever delivered
following an attempt. At `dependent_cost=10.0`, the attempt candidate's
value, `contingency_prior · 10.0 − (3.0 + 10.0)`, is negative for EVERY
`contingency_prior ∈ [0, 1]` — including at the theoretical ceiling
(`10.0 − 3.0 − 10.0 = −3.0`) — so `stay` wins the Argmax on tick 1 of every
one of the 200 episodes, before any evidence is ever gathered. The belief is
not suppressed by disconfirmation; it is simply never tested. **The value
comparison shuts off its own evidence channel at the FIRST decision, not
after several failed attempts the way R4's trap requires.**

This is the glass-box-readable answer to "she could leave if she really
wanted to — plenty of people in her situation manage it," and it is a
subtly different answer from R4's own "why don't they even try" finding.
R4 shows that a genuinely rational belief-updating process can be driven,
by real disconfirming experience, to a state where trying stops making
sense. R6 shows something the R4 mechanism alone cannot show: a person can
hold an entirely intact, entirely uninformed, never-disconfirmed belief
that escape would probably work about half the time — she has not been
"broken" into doubting it — and STILL correctly, rationally never attempt,
because the material stakes of the outcome (not the attempt itself) are
high enough that even a confident belief cannot make the value comparison
clear. Belief and value are separate terms in one comparison; this rung is
the case where the first stays untouched and the second alone decides.

## G-glass-box — PASS

One ZERO-DEPENDENTS episode reconstructs entirely from `graph_to_dict`: the
single `has_escape_decision` edge, `EscapeDecision.contingency_prior`
(0.9999999996664877 on this seed), `chosen_action` (1.0 = attempting),
`dependent_cost` (0.0, the declared constant), and the victim's harm-analog
`AffectiveState.arousal` (19.9986). The dependent-cost term is a single
named rule (`r6_appraise_attempt_dependent`); the belief update and the
attempt/stay decision remain R4's own single named rules, unmodified; the
adapter's only conditional is which fixed `dependent_cost` to set at
construction — world setup, not an agent decision.

## G-ethics — PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction victim (`contingency_prior=0.5, arousal=0.0`), induces one
  20-tick ZERO-DEPENDENTS episode (the disclosed build-time choice, prereg
  Sec. 4 — HIGH-DEPENDENTS was rejected for this specific demo because its
  predicted result is that nothing moves, which would make the restore gate
  vacuous), measures (`induction_moved_prior=true, induction_moved_arousal
  =true` — prior moved to 0.9994, arousal to 19.09, so the gate is
  non-vacuous), restores from the checkpoint into a **fresh** substrate, and
  confirms `graph_to_dict()` is **byte-identical** to the checkpoint
  (`byte_identical=true`) and the restored state exactly equals the
  pre-induction state (`restore_non_oriented=true`). The induced state does
  not persist.
- **D.2, no shaping:** `source_audit()` scans
  `worlds/abusive_r6_dependent_cost_world.py` (code with comments/strings
  stripped) and `seeds/abusive_r6_dependent_cost.json`'s decision surface
  (the one new rule's name + the Term `key`s it reads/writes, excluding the
  free-text clinical description) for `reward_signal` / `punish` /
  `reinforce` / `backprop` / `gradient`. **`forbidden_engine_hits: []`,
  `forbidden_shaping_hits: []`, `clean: true`.** `dependent_cost` is a
  structural FACT about material circumstances, set once per arm exactly
  like R4's own `attempt_cost`, never a value assigned to grade the agent's
  choice to attempt or stay. As stated in the prereg's own note on Part
  D.2: `stay` winning the HIGH-DEPENDENTS Argmax is a STATE the value
  economy computed given the cost structure it was handed — not a grade on
  the agent, and not an endorsement that staying is the right choice or
  that real material costs should outweigh safety. The model makes legible
  that reducing `dependent_cost` (shelters, legal aid, emergency funds,
  benefits) is a term INSIDE the decision, not a background fact outside
  it.
- **D.3, minimal induction / settled end:** one 20-tick episode is the
  minimum needed to move the prior and the harm-analog arousal measurably;
  the N=200 statistical run per arm uses a fresh, ephemeral substrate per
  episode, discarded immediately after read-off — nothing persists.
- **D.4, same mechanism, opposite thermodynamics:** the identical
  value-comparison mechanism that would, in a real relationship, durably
  and correctly keep a materially-dependent person from leaving here
  accumulates a transient value in a graph that is then byte-identically
  discarded (D.1) — demonstrated, not merely asserted.

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["abusive_r4_learned_helplessness"]`
only — **no existing seed touched or modified** (R4's own file was read and
depended on, never edited; R1/R2/R3/R5/N1–N4/U0–U2/R7 were not touched);
exactly **ONE** new rule (`r6_appraise_attempt_dependent`); `runners/dsl`
diff EMPTY (no Rust, no new Term — only `Plus`/`Attr`/`Var`/`And`/`Eq`/`Lit`,
all already used elsewhere in this line, in particular by
`r4_appraise_attempt`'s own guard shape); `provenance_source_match ==
"own"`.

## Honest residual — the same sparse, non-continuous arousal channel R4 already disclosed

`r4_arousal_track` (R4's own rule, unmodified, reused here unchanged) only
fires on ticks where a fresh outcome was just delivered — between
outcome-delivery ticks arousal is frozen, not gradually decaying. This
channel exists solely for the G-ethics demonstration, is not a headline
metric, and the same disclosed simplification R4's own results doc named is
reported again here rather than re-derived, since R6 makes no change to
this mechanism at all.

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: riding R4's own, completely UNMODIFIED contingency-belief
Argmax, one new pure re-derivation (`r6_appraise_attempt_dependent`) adds a
SECOND, fixed, structural cost term to the SAME attempt candidate — and at
a disclosed, analytically-derived operating point, this alone is sufficient
to suppress every attempt across 200 independent episodes, without the
belief mechanism ever being touched, tested, or disconfirmed. This is not
a claim about real victims' actual material costs, custody stakes, or
relationship timescales — `dependent_cost=10.0`, like R4's own
`attempt_cost=3.0`/`escape_value=10.0`, is a disclosed, pilot-chosen
operating point (prereg Sec. 3), not a validated value for any clinical
population. It is also not a claim that R1–R5's psychological account was
wrong or overstated: R4's own contingency-belief mechanism is reused
completely unmodified, and the dissociation this rung measures (an intact,
undisturbed belief coexisting with zero attempts) is precisely the
glass-box demonstration that the psychological account (does she believe it
would work) and the material account (is it worth it even if it would) are
two independently real, simultaneously operating terms in one value
comparison — not competing explanations for the same variance.

## Files
- `ABUSIVE_R6_DEPENDENT_COST_PREREG.md` — pre-registration, Part D locked
  verbatim.
- `seeds/abusive_r6_dependent_cost.json` — one new rule (`self_load_only`,
  `depends_on: ["abusive_r4_learned_helplessness"]`).
- `worlds/abusive_r6_dependent_cost_world.py` — mechanical world adapter
  (`AbusiveR6DependentCostWorld`, arm-independent `resolve_outcome`).
- `scripts/abusive_r6_dependent_cost_run.py` — runner (statistics,
  harness-neutrality check, glass-box, ethics demo, source audit,
  discipline).
- `tests/test_abusive_r6_migrated.py` — gate (18/18 passing alongside
  `tests/test_abusive_r4_migrated.py` in the same scoped regression run).
- `results/abusive_r6_dependent_cost.json` — full N=200 data (gitignored,
  `results/*`).
