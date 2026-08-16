# Self-complexity-weighted domain coupling — PREREG

**Task**: user, auditing this arc's constants: *"Check for other scalars
built in recently - they all need to be weighted."* `mint_domain_self_
worth`'s `coupling_weight=0.6` is a hand-picked linear constant, used for
EVERY new domain regardless of the resident's own held structure — a
"number from nowhere," exactly the pattern `RELATIVE_SELF_WORTH_PREREG.md`
already corrected for the comparison baseline. This document applies the
same correction here.

## 1. Theoretical grounding

**Linville (1985, "Self-Complexity and Affective Extremity: Don't Put All
Your Eggs in One Cognitive Basket," *Social Cognition*; 1987,
"Self-Complexity as a Cognitive Buffer against Stress-Related Illness and
Depression," *JPSP*)**: the more differentiated a person's self-concept
already is (more independent self-aspects/domains they hold), the more a
new domain's outcome is BUFFERED from affecting the global self — someone
with few differentiated domains has everything fused to their global
self-worth; someone with many has each domain more independent. This is a
real, precise, "weighted to other nodes" quantity: the coupling strength
for a NEW domain should be relative to how many domains this resident has
ALREADY differentiated, not a flat constant applied to everyone equally.

## 2. Design

`coupling_weight = base_coupling / (existing_domain_count + 1)` —
Laplace-style harmonic decay (the SAME "+1, made up when absent" shape as
every other constructed-midpoint quantity in this arc): zero existing
domains → full `base_coupling` (an undifferentiated resident's first new
domain fuses completely with global, matching the ORIGINAL, un-audited
0.6 value exactly — this rung does not change behavior for a resident's
FIRST domain); each additional differentiated domain HALVES-then-further-
shrinks the next domain's coupling. `existing_domain_count` is a real,
observed graph quantity (`Count` over the resident's own Microtheory's
`self_worth:*` Concepts, excluding the global `self_worth` Concept
itself) — not invented, mechanically queried exactly as
`mint_domain_self_worth`'s own idempotency check already queries by name.

**A genuine, honest interaction with an already-found engine property**:
`DOMAIN_SELF_WORTH_PROJECTION_RESULTS.md` §2 point 5 already measured a
hard THRESHOLD (not a dial) in the 3-state discrete CAN update — below
`coupling_weight≈0.366` (at `temperature=1.5`), a domain Concept lands
NEUTRAL, not weakly-projected. `base_coupling=0.6` crosses that threshold
at `existing_domain_count=0` (`0.6/1=0.6`) but falls BELOW it at
`existing_domain_count≥1` (`0.6/2=0.3`) — meaning self-complexity
buffering, under THIS engine's existing discrete mechanism, is a SHARP
step (one existing domain is enough to fully decouple the next one's
projection), not Linville's own presumably-graded original finding. This
is registered here BEFORE building, not discovered and smoothed over
afterward — the discrete threshold is inherited, unmodified, engine
behavior; this rung does not attempt to make it graded.

**Computed in Python, not a new graph rule**: this is a genuine
architectural judgment call, stated explicitly. `mint_domain_self_worth`
already mechanically QUERIES the graph (by name, for idempotency) before
constructing anything — extending that same query to also COUNT existing
domains and compute the resulting scalar via ordinary arithmetic
(`base/n+1`) is the same class of operation `worlds/bigville_can_beliefs
.py`'s own `true_edge_j`/`quantize_j` already perform in Python (mechanical
arithmetic on an observed/drawn value, not a branching DECISION over graph
state) — CAN edge weights are set once at mint time throughout this whole
CAN arc, never live-recomputed by a rule, and this rung does not change
that convention.

## 3. Predictions

1. **A resident's FIRST domain is unaffected** — `coupling_weight` at
   `existing_domain_count=0` is exactly `0.6`, byte-identical to the
   pre-audit behavior; `DOMAIN_SELF_WORTH_PROJECTION_RESULTS.md`'s own
   registered projection prediction (a new domain mirrors the global
   state) still holds for a resident's first domain.
2. **A resident's SECOND domain projects more weakly, and — given the
   already-known threshold — lands NEUTRAL rather than mirroring global**,
   confirming the sharp, not graded, step this engine's existing discrete
   mechanism produces.
3. **A resident with MANY existing domains' new domains all land
   neutral** — self-complexity buffering, once triggered, does not
   require an ever-larger domain count to sustain (a genuine, checked
   consequence of the threshold being crossed once and staying crossed
   as the denominator only grows).
4. **This changes NOTHING about already-minted domains** — re-minting
   (idempotent lookup) an EXISTING domain Concept does not recompute or
   perturb its already-established (possibly drifted) coupling or state;
   only a genuinely NEW domain's initial coupling is affected.

## 4. Scope boundaries

- Does not make the CAN discrete threshold graded — an honest, named
  property of the pre-existing engine mechanism, not addressed here.
- Does not weight coupling by domain SIMILARITY (e.g. "public_speaking"
  and "debate" plausibly should buffer each other less than "public_
  speaking" and "cooking") — Linville's own theory is about sheer COUNT
  of differentiated domains, not their semantic relatedness; a
  similarity-weighted version is a real, separate, named follow-on.
- `belief_plasticity`/`alpha` and `audience_gain` remain named,
  un-fixed "numbers from nowhere" from this same audit — not addressed
  in this document.
