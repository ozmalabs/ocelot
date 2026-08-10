# The base vocabulary of embodied-agent affordances — a grounding pass

**Status:** design/science document. No code. Grounds the *complete, spanning,
minimal-ish basis* of admissible action TYPES (affordances) an embodied agent
in a physical + social world has. Each type is later realised as a
STRIPS-style schema — **precondition (= affordance condition) + effect
(= world-state rewrite) + base weight** — that domain worlds specialise.

The architect proposed four (`extract_resource`, `give`, `build`, `write`) and
"probably others." This answers "probably others" from a **basis**, not a
guessed list.

---

## 0. The frame: an affordance IS a precondition, a decision IS a collapse over the afforded set

Gibson: *"The affordances of the environment are what it offers the animal, what
it provides or furnishes, either for good or ill"* — affordances are objective
properties of the **agent–environment system**, action-possibilities relative to
the agent's own capabilities (Gibson 1979, *The Ecological Approach to Visual
Perception*, ch. 8). This maps exactly onto our runtime:

- An **affordance = the precondition** of an action schema. The action is
  "offered" (admissible) in a state **iff** the required graph structure is
  present. "Is `extract_resource` afforded?" ≡ "does the current graph satisfy
  its precondition?"
- The **effect = the world-state rewrite** the action performs (STRIPS
  add/delete over graph elements).
- The agent's **decision = a collapse over the afforded set**, weighted by base
  salience × norm microtheories.

This is precisely the STRIPS/PDDL action-schema shape (Fikes & Nilsson 1971;
PDDL, McDermott et al. 1998): an operator ⟨params, precondition, add-list,
delete-list⟩; applicable iff precondition holds in `s`; yields
`s' = (s \ Del) ∪ Add`; all unmentioned atoms unchanged. So the engineering
representation and the ecological-psychology definition of an affordance are the
**same object**, which is why this vocabulary can be both principled and directly
implementable.

---

## 1. The basis argument — why a *small* set spans *all* embodied action

The temptation is a thesaurus (fish, mine, chop, forge, bake, weave, sell,
barter, whisper, shout, post, punch, stab, feed, rest, …). That is not a basis.
A basis is obtained by asking **what an action can actually rewrite in the
graph**, and **whose thing it rewrites**. Two orthogonal axes generate the set:

### Axis A — the EFFECT CLASS (what graph element changes)

Every admissible action is a graph rewrite of exactly one of a *closed* small
set of element classes. This is the spanning claim:

| Effect class | Graph element rewritten |
|---|---|
| **Position** | a spatial/location edge on the actor itself |
| **Existence** | node create / destroy (goods, artifacts, buildings, corpses) |
| **Configuration** | an object node's attributes/state (open, on, bent) — node persists |
| **Possession** | an ownership/holding edge between agent and object |
| **Information** | an information node / sign / message + its channel edges |
| **Vital/goal state** | an *agent* node's internal attributes or goal progress |

There is no seventh: an embodied action either moves you, changes what exists,
reconfigures a persistent thing, moves who-owns-what, moves information, or
changes an agent's internal/goal state. This closure is corroborated
independently by four literatures that each carve the space and land on
overlapping cuts (§2).

### Axis B — the ONTOLOGICAL TARGET (whose/what thing is acted on)

Gibson's own taxonomy of what the world affords is a target partition
(Gibson 1979, ch. 8, as reviewed in the ecological-psychology literature):

- **surfaces / layout** → afford *locomotion and support* (and obstacles);
- **substances** → afford *nutrition and manufacture*;
- **detached objects** → afford *manipulation and tool-use*;
- **other animals / people** → afford *interaction* — "the whole spectrum of
  social significance," for good **or ill**.

**Why both axes are needed (the non-redundancy engine).** Effect class alone
under-cuts: "change an agent-node's vital attribute" is ONE effect class but
covers eating a meal (target = self, neutral), and stabbing a rival (target =
other, heavily norm-suppressed). The **precondition and the base weight differ
categorically by target even when the effect algebra is identical.** So the
basis is: *for each effect class, split by target only where the target flips
the admissibility condition or the norm weight.* That yields the table in §3 —
larger than the effect classes (6) but far smaller than a verb thesaurus,
and every split is justified, not decorative.

**What gets FOLDED (specialisation, not new primitives).** The architect's
instinct is right: `extract_resource` is ONE type parameterised by *source*
(fish ← water, ore ← rock, wood ← tree). Likewise:

- fish / mine / chop / forage / hunt → **`extract_resource`** (source param).
  These share precondition (co-located source with stock + capability) and
  effect (decrement source, mint raw good). Anthropology treats them as one
  tier — the *extractive/foraging* mode of subsistence — not distinct kinds.
- forge / bake / weave / assemble / construct → **`transform`** (recipe param).
  Same precondition (hold inputs + recipe/skill) and effect (consume inputs,
  mint artifact/building/food). Gibson's "substances afford **manufacture**";
  the anthropological *production/crafting/construction* tier.
- speak / write / post / signal → **`communicate`** (channel param:
  ephemeral / durable / broadcast). `write` is `communicate` with a *durable*
  channel that mints a persistent Sign node.
- give / take / trade → the possession primitive **`transfer`** (direction +
  consent params); see §4 for why `trade` is arguably composite.

**What is kept SEPARATE (and why).** `move`, `extract`, `transform`,
`manipulate`, `transfer`, `communicate`, `ingest`, `rest/wait`, and
agent-directed `harm`/`help` each occupy a distinct (effect-class × target)
cell with a distinct precondition and/or distinct base weight. Collapsing any
pair loses a real admissibility or norm distinction (proof by cases is the
table itself).

---

## 2. The four literatures that independently carve this space

The confidence that the §3 set is *spanning and minimal* comes from convergence:
four unrelated research programmes partition "what an agent can do" and land on
the same cuts.

**(1) Ecological psychology — Gibson.** The target taxonomy above
(surfaces→locomotion, substances→nutrition/manufacture, objects→manipulation,
animals/people→interaction "for good or ill"). Gives us the *target axis* and
puts **harm inside the vocabulary by construction**: *"a knife affords cutting
if manipulated in one manner, but affords being cut in another"* — the same
object affords help and injury; violence is not an exception bolted on, it is
the ill-valence pole of ordinary object/agent affordances. This is a claim about
*membership*, not permanence: harm belongs in the basis, but like every other
type it is offered only when its precondition holds (an agent in range) — it is
*available*, not standing.
(Gibson 1979; review: *Human interaction with the physical world: a brief review
of studies on affordances*, Cambridge, 2024.)

**(2) Linguistic action primitives — three convergent inventories.**

- **NSM semantic primes** (Wierzbicka; Goddard) — ~65 universal "atoms of
  meaning" claimed translatable into every language. The *Actions, events,
  movement* category is exactly **DO, HAPPEN, MOVE, TOUCH**; the *Speech*
  category is **SAY, WORDS, TRUE**; possession is the prime **(IS) MINE**;
  life/death primes **LIVE, DIE**. (nsm-approach.net; Wikipedia,
  *Natural semantic metalanguage*.) This is the strongest evidence for an
  *irreducible* core: MOVE, DO (generic causation/action), TOUCH (contact
  manipulation), SAY (communication), MINE (possession). **Honest gap:** NSM has
  **no** prime for *eat*, *make*, *give*, *hit* — these are "semantic molecules"
  built from primes, not primitives. So NSM would say `ingest`, `transform`,
  `transfer`, `attack` are *composite*. We keep them anyway because they are
  primitive as **affordances** (distinct precondition+effect+weight), even if
  decomposable as **word meanings**. That granularity mismatch is a real
  cross-literature disagreement, flagged in §6.

- **Jackendoff, conceptual semantics** (Jackendoff 1983, *Semantics and
  Cognition*; 1990, *Semantic Structures*). Five semantic functions —
  **GO, BE, STAY, LET, CAUSE** — over categories Event/State/Thing/Path/Place.
  GO = motion (`move`, and possessional GO = `transfer`); STAY/BE = remain
  (`rest/wait`); CAUSE = an agent bringing about a state (`transform`, `build`,
  `attack`); the possessional field reuses GO for transfer of ownership. This
  gives us the *effect algebra* (motion / stasis / caused-change) and, crucially,
  the insight that **possession transfer is spatial motion in an abstract field**
  — so `transfer` and `move` share deep structure but split on target field.

- **VerbNet / FrameNet / Levin.** Levin (1993) verb classes; VerbNet (Kipper et
  al.) ~273 classes over ~8,500 verbs; FrameNet (Fillmore) ~1,024 frames with a
  subsumption hierarchy. The high-level cuts corroborate every type: *Verbs of
  Motion* (7 Levin classes) → `move`; *Verbs of Creation/Transformation* and
  *put/remove* → `transform`/`manipulate`; *Verbs of Possession / Giving* →
  `transfer` (FrameNet **Giving**, **Getting**, **Commerce**); *Verbs of
  Communication* → `communicate` (FrameNet **Communication**); FrameNet
  **Ingestion** → `ingest`; **Cause_harm / Attack** → `harm`; **Assistance** →
  `help`; and FrameNet's linking frames **Intentionally_act / Transitive_action /
  Intentionally_affect** sit at the top as the generic "DO" (Jackendoff CAUSE /
  NSM DO) that all the others specialise. The existence of a broad-coverage,
  hierarchical verb lexicon that bottoms out in these classes is direct evidence
  the set is spanning.

**(3) Anthropology / economics — the subsistence + exchange tiers.** The
canonical activity split: **extraction (foraging/hunting/fishing/mining) →
production/crafting/construction → exchange → communication**. Crucially, Mauss
(1925, *The Gift*) establishes that **exchange is not one thing**: the obligation
triad (to give, to receive, to reciprocate) makes **gift** and **market/barter**
distinct modes — gift creates a social bond and expects delayed, non-equivalent
return; barter/trade is balanced, equivalent, often anonymous. This is why
`transfer` must carry a *consent/reciprocity* parameter (unilateral gift vs
bilateral trade vs non-consensual taking), not collapse to one "exchange."
(Mauss 1925; Sahlins' reciprocity continuum; *Reciprocity (cultural
anthropology)*, Wikipedia.)

**(4) Core knowledge — the infant action-parsing categories** (Spelke & Kinzler
2007, *Core knowledge*, Dev. Sci.; Spelke 2022, *What Babies Know*). Infants have
a dedicated core system representing **agents and their goal-directed actions**,
separate from the object/physics system: agents "need not be cohesive or continuous
… infants represent agents' actions as directed towards goals through means that
are flexible and efficient." A distinct social-cognition system represents people
engaging one another. The developmental staircase — goal-directed → intentional →
rational → *social* agency — and the evaluative primitives **help vs hinder**
(Hamlin, Wynn & Bloom infant studies; Hamlin 2023, *Mind & Language*, response to
Spelke) establish that **agent-directed action (help/harm) is a psychologically
primitive category humans parse from birth**, not a late composite. This is the
firmest ground for keeping `help`/`harm` as first-class affordance types (§4).

---

## 3. THE BASE VOCABULARY

Base weight is a **prior salience**, not a gate: every type is *admissible* when
its precondition holds; norm microtheories then modulate the weight. "Violence is
admissible but low-weight" = `harm` has a low base prior, not a missing entry.
`(self)`, `(env)`, `(obj)`, `(other)`, `(info)` mark the ontological target.

| # | ActionType | Precondition class (affordance condition) | Effect class (world rewrite) | Base weight | Grounding |
|---|---|---|---|---|---|
| 1 | **move** *(env: self-position)* | a traversable path/surface adjacent to the actor affords locomotion | change the actor's own location edge | neutral | Gibson (surfaces afford locomotion); Jackendoff GO; NSM MOVE; Levin motion classes |
| 2 | **extract_resource** *(env)* | actor co-located with a *source* node holding stock, + required capability/tool | decrement source stock; **mint** a raw-good node held by actor | neutral (norm-weighted on over-harvest / ownership of source) | Gibson (substances afford nutrition/manufacture); anthropology extractive tier; VerbNet gather/mine |
| 3 | **transform** *(env/obj → existence)* — *architect's `build`* | actor holds the required input goods + a recipe/skill | **consume** inputs; **mint** an artifact / building / food / tool node | neutral | Gibson (substances afford **manufacture**); production/crafting tier; Jackendoff CAUSE; FrameNet Creating/Building |
| 4 | **manipulate / use** *(obj: configuration)* | a manipulable object co-located; actor has contact/capability | change the object's **attributes/state** (open/close, on/off, push, load) — node persists | neutral | Gibson (objects afford manipulation & tool-use); NSM TOUCH; VerbNet put/remove & change-of-state; IF `open/push/turn` |
| 5 | **transfer** *(possession)* — *architect's `give` + take + trade* | a transferable object held (out) or present-and-available (in); a recipient/counterparty agent present for directed transfer | rewrite the **ownership/holding edge**; params: *out* (give), *in-consented* (receive), *in-unconsented* (take/theft), *bilateral* (trade) | give/reciprocate **high** (pro-social); trade neutral; take-from-owner **low** (theft) | Mauss gift triad; Sahlins reciprocity; Jackendoff possessional GO; NSM (IS)MINE; FrameNet Giving/Getting/Commerce |
| 6 | **communicate** *(info)* — *architect's `write`, + speak/post* | actor holds a content/message node; channel available (addressee present for *ephemeral*; surface for *durable*; public board for *broadcast*) | **mint** a Sign/Message node + channel edges to recipient(s)/public; `write` = durable channel (persistent Sign) | neutral (norm-weighted: lying / slander **low**) | NSM SAY/WORDS/TRUE; Gibson (people afford social significance); FrameNet Communication; Jackendoff info-as-possession metaphor |
| 7 | **ingest / consume** *(self: vital state)* | actor holds/co-located with a consumable + (optionally) an active need/drive | **consume** the item; change actor's **internal vital attributes** (energy, hunger, health) | neutral | Gibson (substances afford **nutrition**); FrameNet Ingestion; core-knowledge self-maintenance (NOT an NSM prime — see §6) |
| 8 | **rest / wait** *(self: null action)* | **always afforded** (the null precondition) | pass time; optionally recover internal state; **no world rewrite** | neutral | Jackendoff STAY/BE; planning no-op / `wait`; The Sims needs-recovery; the collapse model **requires** an admissible "do nothing" |
| 9 | **harm / attack** *(other: vital state)* | another agent present within range; (optional) weapon/capability | reduce target's vital state / destroy target's holdings; may combine with transfer (rob) or existence (kill) | **LOW** base prior, norm-suppressed — *available* when the precondition holds, not always-on | Gibson (animals afford "for good or **ill**"; knife cuts or is-cut); core-knowledge help/**hinder** (Hamlin); FrameNet Cause_harm/Attack; IF `attack/kill` |
| 10 | **help / aid** *(other: vital/goal state)* | another agent present + actor holds a resource/capability the other's goal needs | improve target's vital state or **advance the target's goal** | **HIGH** (pro-social) | core-knowledge **help** vs hinder (Hamlin, Wynn & Bloom); Spelke social-agent system; FrameNet Assistance |
| 11 | **attend / inspect** *(info: epistemic action)* | perceivable structure present in the actor's field | **mint/refine observation** nodes in the actor's *own* graph; no external rewrite | neutral | Gibson (perception is *active* exploration / information pickup); infant selective looking; this project's active foveation/gaze |

**Effect-class span check** (every row lands in exactly one §1-Axis-A class):
position → 1; existence → 2, 3 (and 9 when lethal); configuration → 4;
possession → 5; information → 6, 11; vital/goal → 7, 8 (self), 9, 10 (other).
All six classes covered; no row falls outside. **Spanning.**

**Non-redundancy check:** no two rows share (precondition class ∧ effect class ∧
target ∧ base-weight). The closest pairs — (7 ingest / 9 harm) both rewrite a
vital attribute — split on *target* (self vs other) and *weight* (neutral vs
suppressed), which is exactly the Axis-B justification. **Minimal-ish.**

---

## 4. Precondition/effect as the admissibility structure (STRIPS-style schemas)

Read each as ⟨precondition ⇒ (add / delete)⟩ over graph elements. Illustrative,
target-level, not domain-parameterised:

```
move(actor, dst):
  pre:  loc(actor, src) ∧ adjacent(src, dst) ∧ traversable(dst)
  del:  loc(actor, src)
  add:  loc(actor, dst)

extract_resource(actor, source):
  pre:  loc(actor, L) ∧ loc(source, L) ∧ stock(source) > 0 ∧ capable(actor, source.kind)
  del:  stock(source)=k
  add:  stock(source)=k-1 ∧ holds(actor, new RawGood(source.yield))

transform(actor, recipe):
  pre:  ∀ i ∈ recipe.inputs: holds(actor, i) ∧ knows(actor, recipe)
  del:  holds(actor, i) for each input
  add:  holds(actor, new Artifact(recipe.output))       # or Building at loc

transfer(actor, obj, other, mode):                       # give | take | trade
  pre:  holds(A, obj) ∧ present(A, B)                     # A=source of obj per mode
        ∧ (mode=trade ⇒ agreed(A,B, obj, counter))
  del:  owns(A, obj)   [ + owns(B, counter) if trade ]
  add:  owns(B, obj)   [ + owns(A, counter) if trade ]
  #  weight(give)=+  weight(trade)=0  weight(take|¬consent(B))=−  (theft)

communicate(actor, content, channel, audience):          # speak | write | post
  pre:  holds(actor, content) ∧ channel_available(channel, audience)
  add:  new Sign(content) ∧ conveys(Sign→audience|board)
        ∧ (channel=durable ⇒ persistent(Sign))           # 'write'

ingest(actor, item):
  pre:  holds(actor, item) ∧ consumable(item)
  del:  exists(item)
  add:  Δ vital(actor, item.nutrition)

rest(actor):
  pre:  ⊤                                                 # always afforded (null action)
  add:  Δ vital(actor, +recovery)                         # no external rewrite

harm(actor, target):
  pre:  present(actor, target) [ ∧ holds(actor, weapon) ]
  del:  vital(target)=v          [ ∨ exists(target) if lethal ]
  add:  vital(target)=v-d        # weight = low prior, norm-suppressed

help(actor, target):
  pre:  present(actor, target) ∧ (holds(actor, r) ∧ needs(target.goal, r))
  add:  advance(target.goal) ∨ Δ vital(target, +)        # weight = high

attend(actor, region):
  pre:  perceivable(region, actor)
  add:  Observation nodes in actor's own graph            # epistemic; no world del/add
```

The precondition **is** the affordance query ("offer this action?"); the
add/delete **is** the effect. Base weight rides alongside as the collapse prior.

---

## 5. Honest gaps, disagreements, and judgment calls

- **Biggest judgment call — `harm`/`help` as first-class primitives vs
  composites.** By the *effect algebra* alone they are not primitive: `harm` =
  `transform`/`manipulate` with an *agent* patient (destroy/degrade); `help` =
  "perform any action toward another's goal." NSM would decompose both. **I keep
  them first-class** because (a) core-knowledge research (Spelke; Hamlin) shows
  humans parse *help vs hinder* as a **primitive social-evaluation category from
  infancy**, and (b) their precondition (patient is an *agent*) and base weight
  (strongly signed) differ categorically from every environment/object action.
  The project's own stance — violence must be *available, not omitted* — requires
  `harm` to be an entry in the basis, so decomposing it away would be wrong for
  this system even if defensible in lexical semantics. (*Available*, not
  *standing*: it is a normal precondition-gated affordance, offered only when
  another agent is in range; the "always-present" reading was a sim
  simplification, not a principle.) This is the call I'm least certain about and
  the one most worth a second opinion.

- **`trade` is probably a composite, not a primitive.** Barter = *agreement* +
  two coordinated `transfer`s. I fold it into `transfer` as the *bilateral*
  mode rather than a separate type, but a case exists for a distinct `trade`
  once contracts/negotiation exist (the `agreed(A,B,…)` precondition is itself a
  multi-turn `communicate` protocol). Mauss's whole point is that gift ≠ trade,
  so the *parameter* is load-bearing even if the type is one. Flagged.

- **`attend/inspect` — action or perception?** Perception is continuous
  (always-on), but *active* looking/turning/examining is an action with a cost
  and a precondition, and Gibson insists perception is active exploration. I
  include it as an epistemic action (effect = own-graph observation) but mark it
  borderline; in a system where perception ticks every frame, `attend` is the
  *deliberate re-foveation* subset, not all perceiving.

- **`manipulate/use` overlaps `transfer` and `transform` at the edges.**
  pick-up/put-down could be modelled as `manipulate` (change object config:
  held/not-held) OR as `transfer` to/from self-inventory. I put persistent-state
  changes (open, operate, push) under `manipulate` and ownership changes under
  `transfer`; the pick-up boundary is a modelling choice, not a fact.

- **NSM vs affordance granularity (the core disagreement).** NSM's ~65 primes say
  `ingest`, `transform`, `transfer`, `attack` are *molecules*, not atoms — only
  MOVE, DO, TOUCH, SAY, MINE, LIVE/DIE are primitive at the *word-meaning* level.
  I diverge deliberately: this vocabulary is a basis of **affordances**
  (precondition+effect+weight distinctness), not of **word meanings**. A thing
  can be a semantic molecule yet an affordance atom. Both literatures are right
  about different objects.

- **Sources I could not fully verify and how I treated them.** *The Sims* "smart
  object / advertising affordance" model is real and well-attested as design
  corroboration (Tirrell 2012, *Dumb People, Smart Objects*, Philosophy of
  Computer Games; and the needs/affordance-broadcast mechanism is widely
  documented), but I could **not** verify a specific canonical author/paper for
  the original mechanism, so I cite it only as secondary engineering
  corroboration, not as scientific ground. Woodward (1998, infant reach-encodes-
  goal) is extremely well established but I did not pull the primary here — the
  help/hinder and goal-directed-action claims are carried by the *verified*
  Spelke & Kinzler (2007) and Hamlin (2023) citations instead. Jericho reports
  150–300 *action templates* per IF game (verified via Microsoft Research /
  Hausknecht et al. 2020) — that is a template count, not a primitive count, and
  is cited only as evidence that human-authored worlds bottom out in a *small*
  verb set under many templates.

- **Deliberately excluded as composites** (buildable later from the basis, not
  primitives): `claim/mark` (= `communicate` a declaration, or `transfer` from
  world); `join/bond/befriend` (= repeated `give`/`communicate` — Maussian bond
  accretion); `follow/flee` (= goal-directed `move` w.r.t. an agent);
  `store/drop` (= `transfer` to a location/container); `destroy` (= `harm`/
  `transform` with null output). None earns a row.

---

## 6. Recommended build order

**MINIMAL FIRST SET (8) — start here.** Covers all six effect classes, both
valences, the self/other/env/info targets, and every one of the architect's
four:

1. `move` 2. `extract_resource` 3. `transform` (build) 4. `transfer`
(give/take) 5. `communicate` (say/write) 6. `ingest` (consume)
7. `rest/wait` (the mandatory null action for the collapse) 8. `harm` (attack —
low-weight, and *available* only when an agent is in range — not always-on).

This is spanning: with these eight an agent can go somewhere, get raw materials,
make things, move goods between agents, talk/write, maintain itself, choose to do
nothing, and act against another. That is a complete embodied life at coarse
grain, and every domain world so far (chat/chess/doom/walker/lever) specialises a
subset.

**DEFER (add when a world needs the distinction):**

9. `help/aid` — add when multi-agent cooperation/norms are studied (its
pro-social weight is the mirror of `harm`; both wanted before any social-norm
experiment). 10. `manipulate/use` — add when worlds have stateful objects
(doors, levers, machines) distinct from goods. 11. `attend/inspect` — add when
active perception has a cost worth deciding over. `trade` as a first-class
negotiated type — add when contracts/negotiation protocols exist.

**Weights are priors, not gates; availability is precondition-gated, not
standing** (restated because it's load-bearing): ship every type *in the basis*,
but each is *offered only when its precondition holds* — `harm` is available when
an agent is in range, not permanently on the menu. Then let norm microtheories
move the weights. `harm` being *representable at all* is the point — an agent
that cannot represent violence cannot represent a norm against it — but
representable-and-available is not the same as always-standing (that conflation
was a sim simplification).

---

## Sources

Ecological psychology / affordances:
- [Gibson, *The Ecological Approach to Visual Perception*, ch. 8 "The Theory of Affordances" (1979)](https://cs.brown.edu/courses/cs137/2017/readings/Gibson-AFF.pdf)
- [Human interaction with the physical world: a brief review of studies on affordances (Cambridge, 2024)](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/77211DA1205F288D6A8C1E42F9445606/S2732527X24000130a.pdf/human_interaction_with_the_physical_world_a_brief_review_of_studies_on_affordances.pdf)

Linguistic action primitives:
- [Natural Semantic Metalanguage — Wikipedia](https://en.wikipedia.org/wiki/Natural_semantic_metalanguage)
- [NSM prime category "Actions, events, movement" — nsm-approach.net](https://nsm-approach.net/archives/category/nsm-toolkit/semantic-primes/actions-events-movement)
- [Jackendoff, *Conceptual Structure* (functions GO/BE/STAY/LET/CAUSE) — cogweb summary](http://cogweb.ucla.edu/CogSci/Jackendoff.html)
- [Conceptual semantics — Wikipedia](https://en.wikipedia.org/wiki/Conceptual_semantics)
- [VerbNet (Colorado)](https://verbs.colorado.edu/verbnet/index.html)
- [FrameNet's Frames vs. Levin's Verb Classes (ResearchGate)](https://www.researchgate.net/publication/230876709_FrameNet's_Frames_vs_Levin's_Verb_Classes)

Anthropology / exchange:
- [Mauss, *The Gift* (1925) — Wikipedia summary of the obligation triad](https://en.wikipedia.org/wiki/The_Gift_(essay))
- [Reciprocity (cultural anthropology) — Wikipedia](https://en.wikipedia.org/wiki/Reciprocity_(cultural_anthropology))

Core knowledge / infant action understanding:
- [Spelke & Kinzler, "Core knowledge," *Developmental Science* (2007)](https://www.harvardlds.org/wp-content/uploads/2017/01/SpelkeKinzler07-1.pdf)
- [Hamlin, "Core morality? Or merely core agents and social beings?" *Mind & Language* (2023)](https://onlinelibrary.wiley.com/doi/10.1111/mila.12487)

AI / agent action ontologies (engineering corroboration):
- [STRIPS/PDDL action-schema precondition+effect (Introduction to AI Planning, arXiv 2412.11642)](https://arxiv.org/pdf/2412.11642)
- [Jericho / interactive-fiction action templates — Microsoft Research](https://www.microsoft.com/en-us/research/blog/by-making-text-based-games-more-accessible-to-rl-agents-jericho-framework-opens-up-exciting-natural-language-challenges/)
- [Tirrell, "Dumb People, Smart Objects: The Sims" (Philosophy of Computer Games, 2012)](https://www.gamephilosophy.org/wp-content/uploads/confmanuscripts/pcg2012/Tirrell%202012%20-Dumb-People-Smart-Objects-The-Sims-and-the-Distributed-Self.pdf)
