# Affect-weighted route valuation — what should replace enumeration order

**Status: design note with a measured starting point. No code written.** This is the
missing half of `TIE_CONSEQUENTIALITY_RESULTS.md`, which established that routing depends
on tie-breaking and that the deciding rule is unwritten, but not what should decide
instead.

## 0. The claim, in one line

**Route choice is a weighted valuation in which felt cost is a term — not a distance
calculation with a tie-break bolted on.** Ties are simply where the felt term becomes
visible, because that is where the other terms cancel.

That reframing is the whole content of this note, and it changes what should be built.

---

## 1. What humans actually do

Measured on choices between **equal-length** routes
([PLOS One](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0124404)):

| factor | selection rate | effect size |
|---|---|---|
| straight initial segment | 58–67% | d = .69–.88 |
| flat rather than mountainous | 60–63% | d = .54–.79 |
| southern rather than northern | 52% (diagonals only) | d = .46 |

Three properties of that data matter here.

**It is not deterministic.** With all three factors aligned, selection reaches only
**73–77%**. Priors bias; they do not decide.

**The factors combine additively with no interaction.** Three independent heuristics have
no reason to behave that way. Three contributions to *one* felt quantity do.

**The "southern" factor is a representational artefact, and that is the tell.** Brunyé's
north-is-up(hill) account holds that north is misread as uphill via map convention, and it
survives inversion: the same southern preference appears in Sofia, where the south is
mountainous and the north is flat, as in New England where the reverse is true
([Memory & Cognition](https://link.springer.com/article/10.3758/MC.38.6.700),
[JEP](https://www.sciencedirect.com/science/article/abs/pii/S0272494412000291)). It tracks
the drawing convention, not the terrain.

So all three are the same currency: **anticipated effort, appraised**. Straight is easier
than winding, flat than mountainous, and north *feels* uphill whether or not it is.

## 2. The residual is not noise

Drift-diffusion models call the unexplained variance noise. That is a variance term over
**unmeasured state**, not a claim that anything is ontologically random. Given the exact
state, the choice is determined; the state is simply not observable to the experimenter.

What is in the residual is substantially **affect**. The cleanest evidence is a lesion
result: patients with ventromedial prefrontal damage retain reasoning and lose affective
marking, and the specific deficit that appears is an **inability to break ties** — Damasio's
*"to know but not to feel"*, a patient who "wasn't getting a feeling that one choice was
better than the other and as a result couldn't decide"
([somatic marker hypothesis](https://en.wikipedia.org/wiki/Somatic_marker_hypothesis),
[Damasio](https://pubmed.ncbi.nlm.nih.gov/8941953/)). Remove the feeling and you get
Buridan's ass, experimentally.

Two mechanisms sit under this and are worth keeping apart: **somatic marking** (affect
proper) and **processing fluency** (the easier-to-process option is preferred without
anything that feels like emotion). Both are felt, both prior-driven, both deterministic
given state. The second is the cheaper one for a substrate to compute.

**This is v22's own vocabulary.** The theory requires determinism *given fixed represented
state*, and holds that a quantity producing no distinguishable residual is not observable
in that frame. Human tie-breaking is deterministic given brain state and appears stochastic
only because that state is unrepresented in the observer's frame. What DDM calls noise is
**the residual of an unrepresented frame** — precisely the thing this substrate exists to
make representable.

## 3. The everyday proof, which needs no tie at all

**I will drive the longer route to avoid stop/start traffic.**

That one sentence does more work than the experimental literature above, because there is
no tie in it. The chosen route is strictly longer, so distance-minimisation is not being
*tie-broken*, it is being **overruled**. Every measurement in this repo located the missing
term at ties, because ties are where it becomes visible; this is the same term operating in
the clear.

It settles three things at once:

- **Distance is not the objective.** A model that minimises distance and consults something
  else only on exact ties cannot produce this choice at all.
- **The deciding quantity is felt, not geometric.** Stop/start is not necessarily slower.
  What is worse about it is attention load, jerk, and irritation — an appraisal, not a
  measurement of the road.
- **The weight can exceed the geometric term.** Which is §4's claim, demonstrated by a
  commuter rather than argued from effect sizes.

A sceptic can rename the felt term "non-distance cost" — fuel, attention, time-variance —
and the design consequence is unchanged: **the substrate needs a represented term that is
not geometry.** The affective reading is the stronger one because the preference varies
between people in ways that do not track any objective cost, and because most drivers
cannot state the exchange rate they are applying. But nothing below depends on winning that
argument.

## 4. Weighted, and sometimes dominant

The critical structural point, and the reason "tie-break" is the wrong frame:

**The felt term carries a weight, and the weight varies. At high weight it dominates.** A
route can be chosen almost entirely on how it feels — the longer way round to avoid the
underpass, the scenic detour, the street avoided since something happened there. Distance
loses outright, and no tie is involved.

So affect is not a last-resort arbiter invoked when reason is silent. It is a term in the
valuation at all times, whose visibility happens to peak when the other terms cancel. That
is why ties were where we found it: **ties are the diagnostic, not the phenomenon.**

## 5. What ocelot has today — measured

`seeds/quanta_navigation.json`, 14 rules, `depends_on: [navigation_modes, affordance_basis]`:

| probed for | occurrences |
|---|---|
| `Emotion`, `emotion`, `mood`, `valence`, `arousal`, `affect`, `disposition`, `feel`, `preference` | **0 each** |

Navigation cannot see disposition at all. But the channel it would use already exists:
`qf_relax` relaxes `qdist` through `EdgeAttr(⟨Q, portal, R⟩, "cost")` — a **per-portal cost
attribute inside the Bellman flood**. Three rules read `.cost` (`qf_relax`, `qf_hop_route`,
`qf_stale_on_block_portal`).

Meanwhile the affect machinery exists and is unconnected to it: `core_emotions.json`,
`affective_state_core.json`, `mood_r1.json`, `affect_coupling.json`, `EmotionParams` —
the affect-coupling arc landed in the commit immediately preceding this work.

**So the substrate already has both halves and no wire between them.**

## 6. The proposal

Feed a disposition-weighted term into `portal.cost`, rather than adding a bespoke
navigation heuristic or a tie-break rule.

Consequences, in the order they matter:

1. **Ties resolve by feel, by weight, without a tie-break mechanism existing.** If two
   portals differ in felt cost they no longer tie. The `TIE_CONSEQUENTIALITY` failure mode
   dissolves rather than being patched.
2. **Weight is represented, so domination is expressible.** A high weight lets affect
   overrule distance — the longer route away from the bad place — which a least-angle or
   fewest-turns heuristic structurally cannot say.
3. **Individual differences fall out.** Different `EmotionParams`, different route, each
   internally consistent. Not engineered; a consequence.
4. **It is one mechanism, not a spatial special case.** The same term is available wherever
   a valuation ranks options.
5. **It is v22-conformant.** Disposition is represented graph state, so selection stays
   deterministic given represented state — no hidden executor randomness, which v22
   forbids outright.

The substrate should **not** copy the human residual. Humans have irreducible-in-practice
variability; priors-plus-disposition gives determinism *and* inspectability, which is
better than the thing being modelled, not worse.

## 7. Cheaper mechanisms, one per layer — and the revision they force

Humans are the *most expensive* solution to this problem. Simpler organisms solve it too,
and as the organism simplifies the tie-break **migrates outward**, away from valuation.

| organism | mechanism | where the tie-break lives |
|---|---|---|
| human | affect-weighted valuation | internal representation |
| ant colony | pheromone autocatalysis | the environment |
| woodlouse | bilaterally asymmetrical leg movements | the body |
| *E. coli* | run-and-tumble on a temporal derivative | nowhere — alternatives are never represented |

***E. coli* never faces the tie.** It is too short to sense a spatial gradient, so it
cannot compare two directions because it cannot perceive two directions
([PubMed](https://pubmed.ncbi.nlm.nih.gov/22169400/)). It runs, holds a ~3–4 s memory in
receptor methylation, and suppresses the next tumble when things improve
([PLOS Comp Biol](https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1000735)).
The comparison is performed *by moving through the world*.

**The woodlouse stores it in its legs.** Turn alternation — forced left, then right — is
explained by BALM, bilaterally asymmetrical leg movements arising mechanically from
negotiating the curve
([Springer](https://link.springer.com/content/pdf/10.3758/BF03200018.pdf)). The memory of
the last turn is body state, not representation. **A different body therefore breaks ties
differently with no representational difference at all** — which is this project's
"same capability, two bodies" thesis arriving from biology, at zero cognitive cost.

**The ant colony stores it in the world.** On Deneubourg's double bridge, each ant chooses
probabilistically on pheromone and deposits more; positive feedback amplifies an initial
random fluctuation through a pitchfork bifurcation and the colony converges on one
arbitrary branch
([Argentine ant trail rules](https://www.diva-portal.org/smash/get/diva2:552388/FULLTEXT01.pdf)).
No individual decides. The individual is stochastic; the colony is decisive.

**The revision this forces.** §6 proposed the human mechanism for a problem sitting near
the bottom of the ladder. v22's own layering — graph ⊂ world-modelling ⊂ predictive ⊂
deliberative — predicts a cheaper answer at each lower rung, and biology supplies exactly
one per rung. Two of them are directly available here:

- **Bacterial**: do not select among tied portals at all. Act, and re-flood on residual.
  This *is* v22's boundary semantics already — observation is input, and error is exposed
  by realised mismatch rather than prevented by a pre-check. *E. coli* cannot pre-check; it
  must act to sample.
- **Stigmergic**: accumulate traversal cost on portals. CLAUDE.md already records that the
  map is *"a persistent observation BELIEF"*, so the world-resident surface exists. Same
  insertion point as §6, far cheaper source term, and no new dependency between navigation
  and the affect seeds.

## 8. Why the felt term is optional at the substrate and required at the target

The felt term is **optional for graphhood** — a rock has none, and *E. coli* routes without
one. It is **required for what this substrate is for**, and the sharpest statement of why is
social:

> A full social simulation means some people use the paths, and some cut them.

Heterogeneous disposition is not a decoration on the simulation; it is the phenomenon.
Route choice that is uniform across residents produces a town where nobody has a
character, and — more importantly — **produces the wrong infrastructure**.

The two mechanisms compose, and neither suffices alone:

- **Stigmergy alone** gives homogeneous convergence. Every agent identical, one trail, the
  double-bridge result.
- **Disposition alone** gives heterogeneity with no accumulation. Some cut, some do not,
  and nothing persists.
- **Together** they give **desire paths**: the impatient cut the corner, the cut is
  recorded as reduced cost, the reduced cost recruits the less impatient, and a path exists
  that no one planned. The infrastructure is an emergent readout of the population's
  distribution of disposition.

This is formalised precedent, not speculation. Helbing, Keltsch and Molnár's active walker
model ([Nature 388:47–50](https://www.nature.com/articles/40353),
[Phys. Rev. E 56:2527](https://link.aps.org/doi/10.1103/PhysRevE.56.2527)) reproduces
observed large-scale trail geometry from exactly this feedback — walkers seek comfort and
avoid detours, trails attract walkers, walkers improve trails. And it carries the detail
that makes the heterogeneity claim concrete: **ants produce dendritic trail systems while
pedestrians produce minimal-detour systems.** Same stigmergic mechanism, different agents,
different emergent geometry.

**This gives the design a falsifiable prediction rather than only a rationale.** A bigville
with heterogeneous dispositions and stigmergic cost should produce desire paths: shortcuts
at corners, disused formal routes, and a trail geometry that shifts if the disposition
distribution shifts. If it produces uniform routing, or paths that never form, the
composition is wrong.

### The test bed exists, and it is measured

> **CORRECTED TWICE — the site named below is dead code, and the first fix went into the
> wrong backend.** See `DESIRE_PATH_PRECONDITION_RESULTS.md`. (1) Every statement below about
> `bigville_move_nav.json` truly describes that JSON, but **those rules never execute**:
> bigville's `load_seed_manifest` retains manifests *"without executing an external rule
> engine"*, `settle()` is a documented no-op, and no test imports the move world. "Every
> resident routes identically" holds there because nobody routes at all — a static read of
> seed JSON reported as a property of a running system. (2) Bigville has pluggable backends;
> `cheap` is the default game-AI one and routing belongs to the **ocelot** backend. The wire
> landed in `seeds/bigville_actor_decision.json::oa_choose_option`, whose `Plus(score, Lit 0.0)`
> was the same empty slot as `mv_relax`'s `Lit 1`, and whose affordances already carried an
> unread per-terrain `stamina_multiplier` (path 0.65 < grass 1.00 < tree 2.00 < water 4.00).
> Selection is now `score - gain * stamina_multiplier * (1 - stamina_reserve)`: zero at full
> reserve, so rested residents are unchanged, and cut-across thresholds spread 0.0 → 8.1 with
> depletion where they were uniformly 0.0. The rule is validated by execution on ocelot's Rust
> engine, 30/30 against the Python fallback.

Bigville was extracted from this repo in `5065fb8` but lives at `~/ozmadev/bigville` — 184
seeds, including `bigville_loop_reputation.json`, `bigville_drama_social.json` and
`bigville_stress.json`, all of which earlier notes in this repo recorded as lost. It also
carries movement: `bigville_move_nav.json` (3 rules) and `bigville_move_energy.json`.

Measured there, and it is the same defect this document is about:

- **`mv_relax` floods with a hardcoded hop cost of `Lit 1`.** Every edge costs exactly one,
  for every resident: `gdist = neighbour.gdist + 0 + 1`.
- **`mv_pick_hop` is an `Argmin`** over `Neighbours(cur, "adj")` by `gdist`. On a lattice
  with uniform cost that ties constantly, and enumeration order decides — the identical
  finding to `TIE_CONSEQUENTIALITY_RESULTS.md`, now in the social simulation.
- **Per-resident attributes that should differentiate already exist and vary**: `energy`,
  `hunger`, `energy_cost`, `weight`, `slow_on`, `budget_flat`.
- **None of them reach `gdist`.** Only three rules touch it, all in the nav seed.

So a tired, hungry, heavy resident pays exactly what a fresh one pays, and **every resident
routes identically**. The desire path is not unimplemented; it is *structurally impossible*,
because nothing can make one resident's shortcut cheaper than another's. The energy
grounding is spent by moving (`mv_deplete`) and gates whether you may move
(`mv_energy_budget`) but never influences *which way* you go.

The missing wire is one multiplication: a per-resident factor on the hop cost. That is the
same `Lit`-where-a-quantity-belongs defect as `rule_episode_from_message`'s
`salience: 1.0`, in a different seed, with the inputs already present.

**This also corrects an earlier claim in this repo.** The gap review recorded the social
capital and spoons groundings as extracted and effectively lost, surviving only as prose.
They are not lost; they are in a sibling repository, with the conferral-shaped reputation
model and the allostatic-load stress model both intact.

## 9. Cheap probes, in order

**Stigmergic first.** It is the cheapest mechanism on the §7 ladder that still resolves
ties, it needs no new dependency between navigation and the affect seeds, and it exercises
the same `portal.cost` channel the affective version would use. If it works, it establishes
the channel is sufficient *before* anything argues about disposition.

1. **Does a hand-set `portal.cost` asymmetry break the observed ties?** Set an artificial
   per-portal cost on one tied routing fixture and re-run the `refuse_all` probe. If the
   ties vanish, the channel carries a tie-break and no new machinery is required. **No new
   code.** This is the gate for everything below it.
2. **Does traversal accumulation produce a trail?** Increment (or decrement) `portal.cost`
   on traversal and run a repeated-navigation fixture. The double-bridge prediction is
   convergence onto one of two equal routes; the null is that costs accumulate without
   changing any route, which would mean the flood is insensitive at the magnitudes
   involved. Needs a rule, not an engine change.
3. **Is the felt cost additive?** The §10 falsifier that matters most. Test whether a
   superlinear penalty — ten stops worse than twice five — can be expressed through
   `qf_relax`'s `Plus` at all. If it cannot, the insertion point moves to route-scoring
   grain and probes 1–2 remain valid while §6 does not.
4. **Can a navigation rule read `EmotionParams`?** Only once 1–3 have established the
   channel works. No seed reference exists today; whether the dependency closure permits
   the match without a new edge is unmeasured. Minutes, but pointless before the channel is
   proven.
5. **Does route quality move?** The open question from `TIE_CONSEQUENTIALITY_RESULTS.md`.
   The routing tests assert specific routes and pass, so enumeration order produces
   acceptable answers on those fixtures; whether a principled rule produces better, worse,
   or merely different routes is unmeasured. Probes 1–2 begin to answer it.

## 10. What would falsify this

- **If `portal.cost` cannot express the effect** — e.g. the flood requires non-negative
  costs and the interesting dispositional effects are attractive rather than repulsive —
  the insertion point is wrong even if the theory is right.
- **If the felt cost is not additive, the flood cannot carry it.** `qf_relax` accumulates
  `portal.cost` through `Plus`, and Bellman/Dijkstra relaxation requires additive,
  non-negative edge costs for its optimality guarantee. Stop/start count is plausibly
  additive per junction, but the *felt* quantity may well be superlinear — ten stops worse
  than twice five — or a gestalt property of the whole route rather than a sum over hops.
  **This is the most likely failure mode of the proposal**, and it is a stronger objection
  than the sign problem above: a superlinear cost does not merely mis-rank routes, it
  invalidates the flood's optimality. If it holds, the felt term belongs at route-scoring
  grain rather than inside the relaxation, and the insertion point moves.
- **If disposition is too slow-moving to differentiate portals within one route decision**,
  it can weight a whole route but not choose between adjacent hops, and the term belongs at
  a coarser grain than the flood.
- **If affect-weighted routing degrades the routing fixtures**, then enumeration order is
  doing something better than a principled term would, which would be a genuinely
  interesting result and should be reported rather than tuned away.

## 11. What is not claimed

- That affect is the *only* missing term. Effort appraisal covers the measured human
  factors; familiarity, fluency and risk are plausibly separate and untested here.
- That any of this improves routing. Nothing has been built or measured beyond §4's
  structural probe. The human evidence establishes the *shape*; it establishes nothing
  about this substrate's behaviour.
- That the human residual is *entirely* affective. Some is doubtless unmodelled
  micro-state. The claim is that the residual is unrepresented state rather than
  ontological randomness, and that affect is a large, identifiable, and — for this
  substrate — already-represented part of it.
