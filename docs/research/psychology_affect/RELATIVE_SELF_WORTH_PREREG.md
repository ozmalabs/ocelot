# Relative self-worth — log-weighted social comparison — PREREG

**Task**: a three-part correction from the user to `held_self_worth`'s
design across this turn:

1. *"none of it should be numbers from nowhere. The relative weight is
   between a fictional random midpoint and is log scaled - the same as
   all other weights in ocelot."* — pointed at Γ's own
   `runners/dsl/src/grammar.rs`: `weight` is a Term, `selection ∝ exp(w)`,
   default `1.0`. The core-loop convention.
2. *"critically they should be weighted to other nodes - the default
   doesn't exist, you have to make it up."* — the "fictional midpoint"
   is not a constant, it is CONSTRUCTED (Festinger 1954, *A Theory of
   Social Comparison Processes*), and when phrased "check how people do
   this," the user named the mechanism directly: *"you measure yourself
   by what you observe - this is a massive problem now in the social
   media era where you see the highlight reels of other people, so you
   feel less by comparison."*
3. *"your self worth can drop without dropping - if you assume the
   standard person is 'better' - your self worth just dropped."* —
   self-worth is comparative (Stouffer et al. 1949, relative deprivation),
   so moving the COMPARISON BASELINE moves felt self-worth with zero
   change to one's own track record.

## 1. The mechanism this codebase already has for exactly this shape

`LOGODDS_GENERATOR_PREREG.md` (this repo, already built, `seeds/can_native_
reimplementation.json`'s `Coactivation.evidence_confirm/disconfirm`):

```
log_odds = ln( (confirm_count + 1) / (disconfirm_count + 1) )
```

Confirmed by direct probe before registering (not assumed): zero
observations → `ln(1/1) = 0.0` — a genuinely CONSTRUCTED, symmetric,
fictional midpoint (the Laplace `+1` on each side IS "making it up" when
nothing real exists — one invented pseudo-observation per side, exactly
regularizing, never biasing). Fed a skewed sample (8 positive, 1 negative
— a highlight-reel-shaped observation set) → `1.504`, strictly positive:
believing "everyone I've observed is doing great" reads as a real,
unbounded, compounding LOG deviation from neutral, matching the "easily
conclude you are the worst or best" framing from earlier this arc. This
rung reuses this EXACT formula, not a new one — the same Terms
(`Log`/`Div`/`Plus`), the same Laplace-smoothing justification already
registered in `LOGODDS_GENERATOR_PREREG.md` §2.

## 2. Design

**`PeerComparisonContext`** — one per (resident, domain), linked from the
domain's own `self_worth:<domain>` Concept via `has_peer_comparison`.
**`PeerObservation{outcome: "did_well"|"did_poorly"}`** — 0+, mechanically
recorded (`record_peer_observation`) whenever this resident observes/hears
about ANOTHER resident's outcome in that domain — a real, separate
evidence CHANNEL from the resident's own incidents
(`record_incident_outcome`, unchanged).

**New rule, `compute_relative_self_worth`** (`seeds/peer_comparison.json`):
recomputed live (a stable-fixpoint recompute, mirroring
`can_native_update_3state`'s own "refire only while stale" idiom, not a
one-shot mint) as observations/state change:

```
peer_confirm    = Count(PeerObservations with outcome == "did_well")
peer_disconfirm = Count(PeerObservations with outcome == "did_poorly")
peer_log_odds   = Log(Div(peer_confirm + 1, peer_disconfirm + 1))
relative_self_worth = domain_concept.state - peer_log_odds
```

`relative_self_worth`, NOT the raw domain `state`, is what feeds
`SelfPattern.held_self_worth` going forward — the appraisal that decides
shame/guilt/pride/embarrassment reads how you stack up, not your absolute
state in a vacuum. Zero new Rust — `Log`/`Div`/`Plus`/`Minus`/`Count`/
`Filter`/`Neighbours`/`Attr` all pre-existed, confirmed by the LOGODDS
rung already having used the transcendental one (`Log`).

## 3. Predictions

1. **Zero peer observations → `peer_log_odds=0.0`, `relative_self_worth
   == domain state`** — the fictional midpoint is genuinely neutral, not
   silently biased.
2. **A highlight-reel-skewed observation sample (many "did_well", few
   "did_poorly") pushes `peer_log_odds` positive**, confirmed at the exact
   magnitude the direct probe already measured (`8:1 → 1.504`).
3. **Self-worth can drop without a single incident of the resident's
   own** — holding the domain Concept's `state` completely fixed, adding
   ONLY peer observations (no `record_incident_outcome` calls at all)
   strictly LOWERS `relative_self_worth`. This is the direct, falsifiable
   test of the user's own claim.
4. **The reverse also holds** — observing peers doing POORLY (a
   comparison group you outperform) RAISES `relative_self_worth` above
   the domain's own raw state, with zero change to one's own track
   record — the same mechanism, opposite direction, confirming this is a
   genuine bidirectional comparison effect, not a one-way penalty bolted
   on to match the user's specific example.
5. **End to end**: feeding `relative_self_worth` (rather than raw domain
   state) into the full `run_rule_dispute` pipeline's `SelfPattern`
   changes `attribution_locus`/`emotion` outcomes exactly where the two
   diverge (a resident whose OWN state is positive but whose peer-skewed
   `relative_self_worth` is negative appraises differently than the same
   resident would have under the old, comparison-free mechanism).

## 4. Scope boundaries

- Does NOT wire a live, biased observation-generating channel (e.g. real
  bigville gossip, which this session's much earlier arc already showed
  exhibits its own retelling distortion, Allport & Postman 1947) — real
  `PeerObservation` recording from actual gossip/witnessing is a real,
  separate, named follow-on; this rung supplies the comparison MECHANISM,
  test/demo data is documented synthetic input, same honesty class as
  every prior rung in this arc.
- Does not model WHO the compared-against peers are individually (no
  per-peer identity, weighting by closeness, or credibility of the
  observation source) — a flat count of positive/negative observations,
  the same resolution `LOGODDS_GENERATOR_PREREG.md`'s own `Coactivation`
  counters already use. Weighting individual observations by source
  credibility (a stranger's claim vs. a close friend's) is a real,
  named, smaller follow-on, not attempted here.
- `domain state` (the resident's own absolute belief) keeps its EXISTING
  meaning and update mechanism (`record_incident_outcome`, projection,
  persistence, plasticity) entirely unchanged — this rung adds a SECOND,
  independent quantity (`relative_self_worth`) that combines it with the
  peer baseline, it does not replace or edit the domain Concept mechanism
  itself.
