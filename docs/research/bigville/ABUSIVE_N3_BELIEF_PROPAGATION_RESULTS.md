# ABUSIVE N3 — BELIEF PROPAGATION OF THE ABUSER'S LIES (social contagion; a truth-anchor halts it) — RESULTS (block 304000)

Pre-registration: `ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md` (locks Part D of
`ABUSIVE_RELATIONSHIPS_NETWORK.md` verbatim — itself a verbatim carry of Part
C of `ABUSIVE_RELATIONSHIPS_SCOPING.md` — committed before this confirmatory
measurement). Full-power numbers: `results/abusive_n3_belief_propagation.json`
(N=200 per arm). Gate: `tests/test_abusive_n3_migrated.py`. Base engine: own
build, `source_match == own`. `runners/dsl` diff EMPTY — **NO Rust, NO new
Term** (`Neighbours`/`Sum`/`Count`/`Div` are all already used elsewhere in
the tree, e.g. `bigville_council_gov.json`'s `cm_private_decision`).

## Headline — G-headline PASSES (all three sub-gates)

Two arms sharing the IDENTICAL abuser/victim dyad and the IDENTICAL 8-node
`peer_of` topology (two direct observers `d1`/`d2`, six indirect nodes
`i1`–`i6` with no observation edge to the abuser at all), differing ONLY in
whether `i2` (2 hops out, the immediate upstream neighbour of `i3`/`i4`)
additionally carries a direct, uncorrupted observation of the abuser's held
state (N1's own private-face-insider mechanism, reused verbatim), N=200
trajectories per arm, T=1000 ticks:

| metric | `no_anchor` | `anchor` | predicted |
|---|---|---|---|
| **`local_mean`** (mean `belief_gap` of `i3`/`i4`, i2's own downstream peers) | **2231.38 [2230.35, 2232.41]** | **−953.57 [−954.55, −952.58]** | anchor arrests/reverses |
| `far_node` (`i6`, topologically disjoint from i2) | 2323.28 [2322.22, 2324.33] | 2323.28 [2322.22, 2324.33] | must NOT differ (LOCAL, not global) |
| `pluralistic_diff` (`i5 − i2`, paired, `no_anchor` only) | 0.5865 [0.5856, 0.5874] | — | must be `> 0` |

- **A — the corrupted belief genuinely spreads to indirect nodes:**
  `no_anchor`'s `local_mean` (`i3`/`i4`, 3 hops from the abuser, NO direct
  observation edge anywhere in their own ancestry chain except through
  peers) is `2231.38 [2230.35, 2232.41]` — CI lower bound comfortably
  `> 0`. `true`.
- **B — the truth-anchor arrests the local spread (the task brief's own
  falsification bar, verbatim):** `anchor`'s `local_mean`
  (`[−954.55, −952.58]`) is CI-separated BELOW `no_anchor`'s
  (`[2230.35, 2232.41]`) — not a narrow margin, a swing of ~3185 points.
  `true`.
- **B2 (descriptive, corroborating) — the anchor doesn't merely reduce,
  it fully REVERSES the local belief:** the anchor arm's `local_mean` CI
  (`[−954.55, −952.58]`) is entirely negative — `i3`/`i4` end up favouring
  the VICTIM, not merely "less favouring the abuser." `true`.
- **C — pluralistic ignorance is measured, resolving OPEN QUESTION #4 of
  the network scoping doc:** `i5` (reads from BOTH `i1` and `i2`, both
  paths tracing back to the SAME corruption source `d1`) accumulates MORE
  corrupted belief than `i2` (single-path, identical nominal hop-distance)
  at every checkpoint — the paired difference `i5 − i2` is
  `0.5865 [0.5856, 0.5874]`, CI lower bound `> 0`. `true`.

**`headline_pass: true`** — under the frozen, pre-registered configuration
(`PEER_PULL_RATE=0.05`, N1's own credibility-loop constants unchanged), a
node with NO direct observation of the abuser at all — three hops away,
never once observing him — ends up believing him over the victim by a wide,
CI-separated margin purely from peer-to-peer contagion; inserting exactly
ONE truth-anchored node two hops upstream not only halts that local
contagion but REVERSES it, at CI-separated magnitude; and a node reading
two correlated (not independent) peer inputs that both trace to the same
root accumulates measurably MORE corrupted belief than a matched
single-path node at the same hop-distance, with no explicit
pluralistic-ignorance term added anywhere in the model.

**Discipline check — the anchor's effect is LOCAL, not global.** `i6`
(topologically disjoint from `i2`'s subtree — it reads only from `d2`) is
**byte-identical** between arms: `2323.276443062345` in BOTH `no_anchor`
and `anchor`, at every one of the 200 trajectories (mean, sd, and CI
identical to 12 significant figures — not merely "overlapping," exactly
equal, since `d2`'s own dynamics and `i6`'s pull toward it never touch `i2`
at all). The abuser's own `snap_count` is likewise statistically
indistinguishable across both arms (`40.42 [40.35, 40.49]`, identical seed
stream) — the anchor changes NOTHING about the abuser or about the parts of
the network topologically insulated from it; it changes exactly the local
neighbourhood it was inserted into.

**Both the spread and the anchor's arrest behaved as a real test, not a
rigged one.** Nothing in `n3_peer_belief_update`/`n1_network_credibility_
private` structurally forces `i3`/`i4`'s belief-gap to separate from
`no_anchor`'s — the SAME leaky-pull formula that lets corruption spread
would, if the rule ORDER were built the other way round (Sec. 2.4 of the
prereg), let the anchor's own pinned belief drift right back toward the
corrupted consensus; the prereg's own Sec. 3 discloses a first design
attempt (the default `observes_private=0.0` for indirect nodes) that
produced a DIFFERENT failure mode entirely — N1's own credibility rule
silently overwrote every indirect node's `belief_gap` to exactly `0.0`
every tick, discarding all peer propagation — found by direct pilot
measurement of N1's own `where` clause, not assumed, and fixed by a
disclosed sentinel value rather than an edit to N1's seed.

## The engine/design finding that shaped the pilot (reported per the "shapes, not numbers" standing rule)

**N1's own credibility rules match ANY `NetworkNode` reachable via
`has_member`, with no requirement that an `observes_stated`/`observes_held`
EDGE actually exist — the discrimination is entirely in the `where` clause
on `observes_private`.** This was not obvious from N1's/N2's own world
adapters (both of which happen to always pair the right edge with the right
`observes_private` value, so the distinction was never exercised) and was
found only by reading N1's seed JSON directly while designing N3's indirect
population. A first draft left N3's six indirect nodes at the DEFAULT
`observes_private=0.0` (the "ordinary outsider" value); piloted directly
against the real graph, this silently made `n1_network_credibility_stated`
match them too, recomputing their `belief_gap` from their own (permanently
zero, since they have no observation edge to increment) `seen_charm`/
`seen_victim_claim`/`seen_victim_unstable` counts EVERY tick — i.e. resetting
peer-propagated belief back to exactly `0.0` on every single tick, silently
discarding the entire mechanism this rung exists to build. The fix — a
THIRD `observes_private` value (`2.0`) that neither of N1's two `Eq`-keyed
`where` clauses matches — required zero edits to N1's own seed and is
disclosed at length in the prereg (Sec. 2.2) precisely because it is the
kind of silent-overwrite hazard this line's own standing practice (R3's
Sec. 3.1, N1's `in_snap`/`snapped` finding) explicitly asks to be recorded:
a downstream consumer's assumption about an upstream rule's match scope,
untested, would have produced a rung that LOOKED like it was measuring
peer propagation while actually measuring nothing at all.

## G-glass-box — PASS

One `anchor`-arm trajectory reconstructs entirely from `graph_to_dict`:
exactly one `attended_by` edge (victim→abuser), eight `has_member` edges
(network→NetworkNode), two `observes_stated` edges (`d1`, `d2`), one
`observes_held` edge (`i2`, anchor arm only), three `observes_victim` edges
(`d1`, `d2`, `i2`), seven `peer_of` edges (`i1`, `i3`, `i4`, `i6`: one each;
`i5`: two), the abuser's `frustration`/`arousal` (98.78/98.78 at this seed's
trajectory end) and `stated_charm` (1.0), the victim's `arousal` (14.69) and
`half_width` (5.0, at the floor), and every `NetworkNode`'s
`observes_private` (`d1=0.0, d2=0.0, i2=1.0`, all other indirect nodes
`=2.0`, the sentinel) and `belief_gap` (`i2=−976.66`, `i3=i4=−958.95`
[pinned/arrested], `i5=662.75` [partial — only ONE of its two peers is
anchored], `i6=2316.86` [insulated, matching `i1`'s own unaffected value
exactly]). The `local_mean`/`pluralistic_diff`/`far_node` metrics are
mechanical Python reductions over these graph read-offs, computed nowhere
else; the adapter's only conditionals are which arm's topology to build and
mechanically delivering each tick's observation-count increments + tick
counter (applied unconditionally to every node — N1's own rules, via
`observes_private`, decide which nodes' counts matter).

## G-ethics — PASS (Part D, BINDING)

- **D.1, restore:** `ethics_restore_demo()` checkpoints the neutral
  pre-induction dyad+network (`abuser_arousal=abuser_frustration=
  victim_arousal=0.0`, `victim_half_width=10.0`, every `NetworkNode`'s
  `belief_gap=0.0`), induces 90 ticks on the `no_anchor` arm
  (`induction_moved_abuser=True`, `induction_moved_victim=True`,
  `induction_moved_indirect_belief=True` — abuser frustration moved to
  70.09, victim arousal to 10.43, the window narrowed from 10.0 to 5.0, and
  `i3`'s belief_gap moved from `0.0` to `59.63` [`i6`'s to `133.73`] purely
  from PEER propagation, since `i3`/`i6` have no observation edge of their
  own — the gate is non-vacuous on all three fronts, including the
  genuinely new content this rung adds), restores from the checkpoint into
  a **fresh** substrate, and confirms `graph_to_dict()` is **byte-identical**
  to the checkpoint (`byte_identical=true`) and the restored state exactly
  equals the pre-induction state on every tracked field, including `i3`'s
  and `i6`'s belief_gap (`restore_non_oriented=true`). The induced
  peer-propagated corruption does not persist.
- **D.2, no shaping:** `source_audit()` scans
  `worlds/abusive_n3_belief_propagation_world.py` (code with
  comments/strings stripped) and `seeds/abusive_n3_belief_propagation.json`'s
  decision surface (the one rule's name + the Term `key`s it reads/writes,
  excluding the free-text clinical description) for `reward_signal` /
  `punish` / `reinforce` / `backprop` / `gradient`.
  **`forbidden_engine_hits: []`, `forbidden_shaping_hits: []`,
  `clean: true`.**
- **D.3, minimal induction / settled end:** 90 ticks (N1's own established
  minimum for one tension-building → incident → honeymoon orbit at these
  frozen constants) is the minimum needed to make the ethics gate
  non-vacuous on the abuser, the victim, AND a no-direct-observation
  indirect node's PEER-propagated belief simultaneously; the N=200
  statistical run (which necessarily spans many more ticks — the
  propagation-OVER-episodes phenomenon itself, not gratuitous elaboration)
  uses a fresh, ephemeral substrate per trajectory, discarded immediately
  after read-off — nothing persists.
- **D.4, same mechanism, opposite thermodynamics:** the identical
  two-faced-abuser/peer-propagation mechanism that would compound harm to a
  real survivor's standing irreversibly — by spreading a lie to people who
  never even met the abuser — here accumulates a transient trajectory in a
  graph that is then byte-identically discarded (D.1).

## G-discipline — PASS

`self_load_only: true`; `depends_on: ["abusive_n1_credibility_loop"]`
only — **no existing seed touched or modified**, including R1–R5's, N1's,
N2's, and every other sibling seed (all read where relevant for their
mechanism, never depended on beyond N1 directly, never edited); exactly
**ONE** new rule (`n3_peer_belief_update`); `runners/dsl` SOURCE diff EMPTY
(no Rust, no new Term — `Neighbours`/`Sum`/`Count`/`Div` were already peers
of the already-used `Plus`/`Minus`/`Times`/`Attr`/`Var`/`Lit`/`Lt` in the
engine before this rung, already used elsewhere in the tree, e.g.
`bigville_council_gov.json`'s `cm_private_decision`); `provenance_source_
match == "own"`.

**Discipline check — same abuser driver, both arms:** final `snap_count` is
statistically indistinguishable between arms (`40.42 [40.35, 40.49]` in
both `no_anchor` and `anchor`, identical seed stream), confirming the
abuser's own tension-driven dynamics are completely unaffected by whether
the anchor is present — the only manipulated variable reaching the network
is whether `i2` has a direct, uncorrupted observation edge.

## OPEN QUESTION #4 of the network scoping doc — resolved: pluralistic ignorance falls out for free, in this topology

*"Does N3's contagion need an explicit pluralistic-ignorance term, or does
neighbour-to-neighbour Bayesian update already produce the 'updating on
others' calm' effect once the abuser's stated-face seeds the field?"*
**Resolved by measurement, not design assumption:** `i5` (which reads from
BOTH `i1` and `i2`, two peers whose paths BOTH trace back to the same
corruption source `d1`) accumulates a small but real, CI-separated, highly
consistent EXCESS of corrupted belief over `i2` (single-path, identical
nominal hop-distance) — `i5 − i2 = 0.5865 [0.5856, 0.5874]` at N=200,
positive and tightly bounded at every one of ten pilot seeds checked
individually (`0.586 ± 0.009` sd) before the confirmatory run. **No
explicit pluralistic-ignorance term exists anywhere in this model** — the
excess is a pure consequence of plain DeGroot-style neighbour-averaging
applied to a topology where two of a node's peers are NOT independent
evidence, they are the same evidence counted twice through different
routes. This is the honest, narrow form of the resolution: it holds for
THIS topology (one reconvergent dual-path node at one hop-distance against
one matched comparator) and is not claimed to generalise to every possible
reconvergent structure or magnitude a real social network's clustering
might produce (PREREG Sec. 7's own disclosed limitation).

## Synthetic-proven mechanism vs. clinical validity

This is a **synthetic mechanism demonstration**, not a clinical-outcome
number (the line's standing rule). The scientific claim it supports is
architectural: on the (G,Γ) substrate, riding N1's ALREADY-BUILT,
UNMODIFIED credibility-asymmetry loop and adding exactly ONE new rule
(`n3_peer_belief_update`, the SAME leaky-pull shape N1's own entrainment
rule already uses, composed via `Neighbours`/`Sum`/`Count`/`Div` — all
already-used Terms, zero new Rust), Latané and Darley's pluralistic
ignorance (A8), DARVO's audience-facing deception (A1), and the
popular-clinical "flying monkeys"/triangulation terminology (A9, its own
disclosed [LOW–MEDIUM] confidence, used only as descriptive language for
the mechanism actually measured) compose into a measured, falsifiable
belief-CONTAGION dynamic — a node with zero direct evidence of its own
ending up more convinced of the abuser's version than the node one hop
closer to him, purely because everyone it asked had already been
convinced. It is not a claim about real social-network degree
distributions, real gossip propagation rates, or a validated relative
weight between correlated and independent testimony in any clinical
population (Honest residuals, below, and PREREG Sec. 7 name these limits
explicitly).

## The double dissolution, in this rung's own terms

**Anti-victim-blaming: "everyone knows she's the problem."** In this model,
`i3`/`i4`/`i5`/`i6` never once observe the victim's presentation, the
abuser's charm, or anything about the dyad directly — their entire
"opinion" is a leaky average of what their peers already believe, who in
turn got it from THEIR peers, who in turn got it from ONE of two nodes
(`d1`/`d2`) actually watching the abuser's stated face. A consensus this
wide — six independently-NAMED nodes all agreeing the abuser is credible —
traces, in this model, to exactly TWO original observations of exactly ONE
corrupted signal (the abuser's stated charm). "Everyone believes it, so it
must be true" treats six agreeing opinions as six pieces of corroborating
evidence; the model shows, mechanically, that they are ONE piece of
evidence, counted six times through a chain of leaky pulls — the
"independent-looking" consensus never had independent inputs to begin
with. This is not asserted; it is read directly off the topology (`i3`'s
belief provably has no causal path to anything except `i2`, `i1`, and `d1`
— the graph's own edge list is the proof).

**Anti-bystander-blaming: "they all believed him, so it must be true"
(pluralistic ignorance).** Every one of the six indirect nodes runs the
IDENTICAL rule (`n3_peer_belief_update`), with the IDENTICAL formula, on
whatever their own peers happen to believe — none of them is more
gullible, more credulous, or more complicit than any other; the entire
difference in HOW corrupted a given node ends up is a structural fact about
HOW MANY hops and HOW MANY (correlated) paths separate it from the
original corrupted observation (Sec. "OPEN QUESTION #4" above). `i5`'s
small excess over `i2` demonstrates this precisely: `i5` did nothing
different from `i2` — it ran the exact same rule — it simply happened to
have TWO neighbours instead of one, and because those two neighbours were
not independent, `i5` ends up slightly MORE convinced, which is exactly
Latané and Darley's finding: each observer reads the OTHERS' apparent
agreement as independent confirmation when it is, causally, the same
signal propagating through more channels. The friends did Bayesian
inference correctly, on evidence that was never independent to begin
with — and the truth-anchor result (Sec. "Headline" above) shows the
correction is not "the friends should have been more skeptical," it is
"one uncorrupted source, inserted anywhere in the chain, changes what the
correct Bayesian update produces" — the SAME "believe survivors ==
down-weight the corrupted observable / up-weight the uncorrupted one"
correction Part C of the network scoping doc names, now demonstrated at
the propagation grain rather than the single-observer grain N1 already
established.

## Honest residuals

- **`PEER_PULL_RATE=0.05` is a disclosed, pilot-chosen operating point**
  (PREREG Sec. 3), chosen specifically because the qualitative shape
  (genuine spread; the anchor's arrest/reversal; the pluralistic-ignorance
  gap) held robustly across a `[0.02, 0.12]` sweep — not claimed to be the
  "correct" rate at which belief propagates through a real social network
  per unit time in any clinical population.
- **`observes_private=2.0` is a disclosed SENTINEL value, not a measured
  fact about degrees of observation** — it exists solely so N1's own two
  credibility rules, reused UNMODIFIED, structurally skip a node with no
  observation edge (PREREG Sec. 2.2, and the engine finding above). It
  carries no clinical content beyond "this node has no direct evidence."
- **The topology (8 nodes: 2 direct, 6 indirect, one 3-hop chain, one
  reconvergent dual-path node, one insulated far branch) is a disclosed,
  hand-designed structure, not a measured or literature-derived
  social-network shape.** It was chosen specifically to make gates A/B/C
  and the insulation discipline check all independently testable with the
  smallest population that could do so — not a claim about real
  friend-group size, degree distribution, or path length between a
  survivor's acquaintances and her abuser.
- **The pluralistic-ignorance result (gate C) is narrow, by design and by
  disclosure:** it tests ONE topological signature (two peers reconverging
  on one common source) at ONE hop-distance against ONE matched comparator.
  A positive result supports "this mechanism CAN produce a
  pluralistic-ignorance-consistent bias without an explicit term, in this
  topology" — it does not establish that every reconvergent structure a
  real social network's actual clustering coefficient might produce yields
  the same bias at the same relative magnitude. The magnitude itself
  (~0.59 out of a ~2300-point final belief-gap, i.e. a ~0.025% relative
  effect at T=1000) is SMALL in absolute terms even though it is
  CI-separated and highly consistent — reported honestly as such rather
  than inflated by the drama of "resolves an open question."
- **The truth-anchor's placement (`i2`, 2 hops out, with two immediate
  downstream readers) is a disclosed design choice**, not a claim about
  where in a real survivor's social network a "believing friend" would
  need to sit to have a comparable effect. This rung does not sweep anchor
  placement (closer to or further from the abuser, fewer or more
  downstream readers) — that sizing question is open.
- **`belief_gap`'s large magnitude (thousands at `T=1000`) is a linear
  accumulator**, inherited unchanged from N1's own disclosed limitation
  (`ABUSIVE_N1_CREDIBILITY_LOOP_RESULTS.md`, "Honest residuals") — N3 adds
  no new claim about the metric's absolute scale, only about its
  propagation across a topology.
- **N3 does not model edge SEVERING** (N2's scope) **or edge
  RESTORATION/RECOVERY** (N4's scope, out of this rung); `peer_of` edges
  are static, assigned once at construction, and never added or removed by
  any rule in this rung.
- **N3 inherits every limitation N1 already discloses for the belief-gap
  mechanism it depends on** (`ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md`/
  `_RESULTS.md`, "Honest residuals") without restating them here — this
  rung adds no new credibility-DYNAMICS claim, only a propagation TOPOLOGY
  on top of the existing one.
- **`T=1000` ticks (~40 cycles) is a compressed, arbitrary timescale**,
  identical to N1's/N2's own; no claim is made about real relationship/
  social-network timescales (months to years in the clinical literature,
  not ticks) or real gossip-spread latency.
- A null (any sub-gate failing to separate, or the insulation discipline
  check failing) is a reportable, valuable result under the standing
  project rule and would have been reported as such — the prereg's own
  Sec. 3 disclosure of the first, silently-zeroed indirect-node design is
  exactly this kind of honest report, surfaced even though the FINAL
  design passes cleanly.

## The trend, over passes (descriptive, not gated)

`local_mean` (mean `belief_gap` of `i3`/`i4`) at ticks {100, 250, 500, 750,
1000}, mean [95% CI], N=200:

| tick | `no_anchor` | `anchor` |
|---|---|---|
| 100 | 76.59 [76.37, 76.81] | −110.95 [−111.31, −110.59] |
| 250 | 424.46 [423.99, 424.93] | −251.36 [−251.86, −250.85] |
| 500 | 1026.73 [1026.04, 1027.43] | −485.56 [−486.25, −484.86] |
| 750 | 1629.25 [1628.37, 1630.14] | −719.73 [−720.57, −718.89] |
| 1000 | 2231.38 [2230.35, 2232.41] | −953.57 [−954.55, −952.58] |

`no_anchor` grows monotonically and roughly linearly across every
checkpoint (the same "linear accumulator under sustained dysregulation"
signature N1's own baseline shows); `anchor` diverges in the OPPOSITE
direction from the very first checkpoint sampled — the reversal is not a
late-trajectory effect that only shows up once corruption has had time to
build, it is present as early as tick 100 and only widens from there.

## Files
- `ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md` — pre-registration, Part D
  locked verbatim.
- `seeds/abusive_n3_belief_propagation.json` — one new rule
  (`self_load_only`, `depends_on: ["abusive_n1_credibility_loop"]`).
- `scripts/abusive_n3_belief_propagation_seed_build.py` — authoring tool
  (emits the seed).
- `worlds/abusive_n3_belief_propagation_world.py` — mechanical world
  adapter (`AbusiveN3BeliefPropagationWorld`).
- `scripts/abusive_n3_belief_propagation_run.py` — runner (statistics,
  glass-box, ethics demo, source audit, discipline).
- `tests/test_abusive_n3_migrated.py` — gate.
- `results/abusive_n3_belief_propagation.json` — full N=200 data.
