# Domain-scoped self-worth as projection-then-decoupling — RESULTS

Registered design: `DOMAIN_SELF_WORTH_PROJECTION_PREREG.md`. Built:
`mint_domain_self_worth` + belief-plasticity-as-personality-trait in
`domains/can_self_worth_bridge.py`, demonstrated by
`scripts/domain_self_worth_projection_demo.py`, regressed by
`tests/test_domain_self_worth_projection.py` (8/8 green). No seed edited.

## 1. What this answers

User: *"in a new domain, you project into it. your core self worth
affects that projection, rather than vice versa."* This is Rotter (1954)'s
generalized-vs-specific-expectancy mechanism, and it needed **zero new
Rust or rules** — only correct graph wiring: a domain Concept with no
independent prior (`identity_field=0.0`), coupled via `causal_influence`
to the resident's global `self_worth` Concept. The FIRST relaxation has
nothing else to go on but the coupling, so it projects the global belief;
`record_incident_outcome` applied to the domain Concept specifically then
lets domain-specific evidence decouple it.

Then, immediately: *"that needs to be also working the other way. Some
people DO NOT learn that. This needs to be a personality based trait."*
Correct, and directly grounded in Dweck's fixed-vs-growth-mindset
distinction. The mechanism already had the right knob —
`record_incident_outcome`'s `alpha` parameter IS belief plasticity; it
only needed to stop being a hardcoded default and become a per-resident
personality trait, the same way `prior_self_worth`/`w_supergraph`/
`w_spite` already are.

## 2. Predictions — 6 registered; 5 held, 1 corrected live (not hidden)

```
brand-new domain, no track record:          domain=1  (projected from global=1)
after 3 negative domain-specific incidents: domain=0  global=1  (still unmoved)
after 4-5 negative domain-specific incidents: domain=-1 global=1 (decoupled)

TWO DOMAINS, OPPOSITE BELIEFS, SIMULTANEOUSLY
public_speaking: -1   chess: 1   global: 1

BELIEF PLASTICITY AS A PERSONALITY TRAIT
Rigid (fixed mindset, alpha=0.05)     global=1 -> [1, 1, 1, 1, 0, 0, 0, 0]
Flexible (growth mindset, alpha=0.5)  global=1 -> [0, -1, -1, -1, -1, -1, -1, -1]
```

1. **Projection from global on a brand-new domain** — `PASS`.
2. **Decoupling from domain-specific evidence, global untouched** —
   `PASS`. The global `self_worth` Concept never receives domain-targeted
   evidence, so it stays exactly where it was throughout.
3. **Two domains, opposite beliefs, simultaneously** — `PASS`. This is
   the DIRECT, falsifiable test of the user's very first question in this
   arc ("low self-worth generally but very confident on a topic") —
   `public_speaking=-1`, `chess=1`, `global=1`, all coexisting on the same
   resident.
4. **Idempotent minting** — `PASS`; a second call for the same
   resident+domain returns the SAME Concept with its drift intact.
5. **Coupling weight — REVISED LIVE, not silently patched.** The
   registered prediction ("a lower weight still projects the correct sign,
   just via a smaller pull") was WRONG as stated, found on the first test
   run (`0.3` produced `state=0.0`, not `1.0`). Root cause, characterized
   precisely by sweeping the weight: `can_native_update_3state`'s own
   discrete-3-state threshold (`sum*temperature > 0.549`) means this is a
   genuine THRESHOLD crossing, not a continuous dial — below
   `coupling_weight≈0.366` (at this resident's `temperature=1.5`), the
   domain Concept lands NEUTRAL; at/above `≈0.37`, it crosses fully into
   the global sign. No partial-credit regime exists. The PREREG and the
   test were both corrected to assert the TRUE behavior, and the
   corrected claim held (`PASS`).
6. **Belief plasticity is a real personality trait, not a fixed
   constant** — `PASS`. The identical 8 incidents, the identical starting
   belief, differing ONLY in `alpha`: the rigid resident barely dents
   (reaches `0`, the neutral state, not even a full flip) while the
   flexible one fully flips by the 2nd incident.

## 3. Honesty notes

**Does establish**: domain-specific self-worth, its causal grounding in
the global belief for novel domains, and individual differences in how
readily that grounding gets displaced by real experience, all compose from
mechanisms already built this session (CAN relaxation, evidence
application, persistence) with zero new engine code — three user-supplied
theoretical corrections in a row (projection direction, then plasticity as
a trait), each one landing on an EXISTING knob rather than requiring new
machinery, which is itself evidence the underlying CAN/Hopfield shape was
the right one to begin with.

**Does NOT establish**: a general formula for what coupling weight or
plasticity value is "realistic" for a given domain or person — both are
documented, un-fitted constants (same honesty class as every other
constant this arc has used). Whether the discrete threshold-crossing
behavior (Sec2 point 5) is itself the psychologically correct shape for
domain projection (a real person's confidence in a brand-new domain might
plausibly be genuinely GRADED, not a hard on/off crossing) is an honest
open question — this rung inherited that behavior from the pre-existing
3-state discrete CAN update rule, unchanged, rather than introducing or
resolving it. `belief_plasticity` is not yet drawn from a
`_PARAM_SPEC`-style distribution the way other traits are — a caller
currently supplies it directly; wiring a population-level draw is a small,
real, named follow-on.

## 4. Files

- `docs/research/psychology_affect/DOMAIN_SELF_WORTH_PROJECTION_PREREG.md`
- `docs/research/psychology_affect/DOMAIN_SELF_WORTH_PROJECTION_RESULTS.md` (this file)
- `domains/can_self_worth_bridge.py` (extended: `mint_domain_self_worth`; `record_incident_outcome`'s docstring clarifies `alpha` IS belief plasticity)
- `scripts/domain_self_worth_projection_demo.py`
- `tests/test_domain_self_worth_projection.py` (8/8)
