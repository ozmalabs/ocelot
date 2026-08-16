# Relative self-worth — log-weighted social comparison — RESULTS

Registered design: `RELATIVE_SELF_WORTH_PREREG.md`. Built:
`seeds/peer_comparison.json` (via `scripts/_build_peer_comparison_seed.py`),
`mint_peer_comparison_context`/`record_peer_observation`/
`read_relative_self_worth` in `domains/can_self_worth_bridge.py`, wired
into `domains/rule_dispute_full_pipeline.py`, demonstrated by
`scripts/relative_self_worth_demo.py`, regressed by
`tests/test_relative_self_worth.py` (8/8 green).

## 1. What this answers

Three corrections from the user, in sequence: (1) *"none of it should be
numbers from nowhere... log scaled - the same as all other weights in
ocelot"* — pointed at Γ's own `selection ∝ exp(w)` convention
(`runners/dsl/src/grammar.rs`); (2) *"weighted to other nodes - the
default doesn't exist, you have to make it up"* — Festinger (1954) social
comparison, with the "made up" midpoint identified as EXACTLY the
Laplace-smoothing this codebase already uses (`LOGODDS_GENERATOR_PREREG
.md`'s `ln((confirm+1)/(disconfirm+1))`, zero data → `ln(1/1)=0`, a
genuinely constructed, not asserted, neutral point); (3) *"your self worth
can drop without dropping - if you assume the standard person is 'better'
- your self worth just dropped"* — relative deprivation (Stouffer et al.
1949): felt self-worth is comparative, so the comparison BASELINE moving
is sufficient, with zero change to one's own track record.

## 2. What this is

`relative_self_worth = domain_concept.state - peer_log_odds`,
`peer_log_odds` computed via the SAME formula `LOGODDS_GENERATOR_PREREG
.md` already registered, applied to a NEW `PeerObservation` accumulator
(0+ `"did_well"`/`"did_poorly"` records per resident+domain) instead of
`Coactivation`'s confirm/disconfirm counts. `relative_self_worth`, not raw
`state`, now feeds `SelfPattern.held_self_worth` in the full pipeline.
Nothing about the domain Concept's own update mechanism (projection,
persistence, plasticity, `record_incident_outcome`) is touched —
`peer_comparison` is a second, independent, strictly additive evidence
channel.

## 3. Predictions — all 5 registered, all 5 held

```
ZERO OBSERVATIONS
own state: 1   relative_self_worth: 1

THE HIGHLIGHT REEL (8 peers doing well, 1 struggling)
own state (UNCHANGED): 1
relative_self_worth (DROPPED): -0.504

THE REVERSE (8 peers struggling, 1 doing well)
own state (UNCHANGED): 1
relative_self_worth (RISEN): 2.504

END TO END: peer skew recorded BEFORE the resident's own first dispute
no peer skew:   specific_act  guilt
with peer skew: global_self   shame
```

1. **Zero observations → genuinely neutral midpoint** — `PASS`,
   `relative_self_worth == state` exactly.
2. **Highlight-reel skew → strictly positive `peer_log_odds`**, at the
   exact magnitude the direct probe measured (`8:1 → 1.504`) — `PASS`.
3. **The user's own claim, directly tested: self-worth drops with ZERO
   change to the resident's own track record** — `PASS`. `state` stays at
   `1` throughout (no `record_incident_outcome` call at all in this test);
   `relative_self_worth` alone drops from `1` to `-0.504`.
4. **The reverse holds too** — `PASS`, confirming a genuine bidirectional
   comparison effect (observing peers struggle RAISES relative
   self-worth above one's own raw state), not a one-way penalty fitted to
   match a single example.
5. **End to end, the load-bearing integration test**: the SAME resident,
   the SAME first-ever dispute, produces `guilt` with no prior peer data
   and `shame` when 8 highlight-reel-shaped observations were recorded
   FIRST — `PASS`. Bob has done nothing of his own yet in either run; only
   what he'd heard about OTHERS changes how his own first mistake reads.

No null. Every registered prediction held on the first run.

## 4. Honesty notes

**Does establish**: self-worth is now genuinely comparative, not
absolute, reusing the exact log-odds mechanism this codebase already
built and registered for a different purpose (`Coactivation` evidence) —
zero new Rust, zero new formula, the SAME `Log`/`Div`/`Plus`/`Minus`/
`Count`/`Filter` Terms. The "fictional midpoint" is not a hand-picked
constant anywhere in this build — it falls out of Laplace smoothing
applied to zero real data, which is what "making it up" means made
precise.

**Does NOT establish**: a live, biased observation-GENERATING channel —
`record_peer_observation` is called with caller-supplied `peer_did_well`
data in every test/demo here (documented synthetic input, same honesty
class as every prior rung). Wiring this to REAL bigville gossip (which
this session's much earlier arc already showed exhibits its own retelling
distortion, Allport & Postman 1947 — a plausible, real source of exactly
the observation-channel bias this rung's mechanism responds to) is a
real, separate, named follow-on, not attempted here. Individual peer
credibility/closeness weighting (a stranger's claim vs. a close friend's)
is not modeled — a flat count, matching `Coactivation`'s own resolution.
Whether `Log`'s magnitude (rather than just its sign) is the
psychologically correct scale for this effect is inherited, unexamined,
from the pre-existing `LOGODDS_GENERATOR_PREREG.md` formula — reused
deliberately, not re-derived.

## 5. Files

- `docs/research/psychology_affect/RELATIVE_SELF_WORTH_PREREG.md`
- `docs/research/psychology_affect/RELATIVE_SELF_WORTH_RESULTS.md` (this file)
- `scripts/_build_peer_comparison_seed.py`
- `seeds/peer_comparison.json`
- `domains/can_self_worth_bridge.py` (extended: 4 new functions)
- `domains/rule_dispute_full_pipeline.py` (edited: sources `SelfPattern.held_self_worth` from `read_relative_self_worth`, not raw state)
- `scripts/relative_self_worth_demo.py`
- `tests/test_relative_self_worth.py` (8/8)
