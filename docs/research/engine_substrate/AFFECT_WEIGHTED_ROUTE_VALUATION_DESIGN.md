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

## 3. Weighted, and sometimes dominant

The critical structural point, and the reason "tie-break" is the wrong frame:

**The felt term carries a weight, and the weight varies. At high weight it dominates.** A
route can be chosen almost entirely on how it feels — the longer way round to avoid the
underpass, the scenic detour, the street avoided since something happened there. Distance
loses outright, and no tie is involved.

So affect is not a last-resort arbiter invoked when reason is silent. It is a term in the
valuation at all times, whose visibility happens to peak when the other terms cancel. That
is why ties were where we found it: **ties are the diagnostic, not the phenomenon.**

## 4. What ocelot has today — measured

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

## 5. The proposal

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

## 6. Cheap probes, before anything is built

1. **Can a navigation rule read `EmotionParams` at all?** Measured above: no seed reference
   exists, but the dependency closure may still permit it. Establish whether
   `quanta_navigation` can match an affect node without a new dependency edge. Minutes.
2. **Does a hand-set `portal.cost` asymmetry break the observed ties?** Set an artificial
   per-portal cost on one of the tied routing fixtures and re-run the `refuse_all` probe.
   If ties vanish, the channel is sufficient and no new machinery is needed. This is the
   single highest-value experiment here and it requires no new code.
3. **Does route quality move?** The open question from `TIE_CONSEQUENTIALITY_RESULTS.md`:
   the routing tests assert specific routes and currently pass, so enumeration order
   produces acceptable answers on those fixtures. Whether a *different* deciding rule
   produces better, worse, or merely different routes is unmeasured, and probe 2 would
   begin to answer it.

## 7. What would falsify this

- **If `portal.cost` cannot express the effect** — e.g. the flood requires non-negative
  costs and the interesting dispositional effects are attractive rather than repulsive —
  the insertion point is wrong even if the theory is right.
- **If disposition is too slow-moving to differentiate portals within one route decision**,
  it can weight a whole route but not choose between adjacent hops, and the term belongs at
  a coarser grain than the flood.
- **If affect-weighted routing degrades the routing fixtures**, then enumeration order is
  doing something better than a principled term would, which would be a genuinely
  interesting result and should be reported rather than tuned away.

## 8. What is not claimed

- That affect is the *only* missing term. Effort appraisal covers the measured human
  factors; familiarity, fluency and risk are plausibly separate and untested here.
- That any of this improves routing. Nothing has been built or measured beyond §4's
  structural probe. The human evidence establishes the *shape*; it establishes nothing
  about this substrate's behaviour.
- That the human residual is *entirely* affective. Some is doubtless unmodelled
  micro-state. The claim is that the residual is unrepresented state rather than
  ontological randomness, and that affect is a large, identifiable, and — for this
  substrate — already-represented part of it.
