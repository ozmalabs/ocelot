# DWARF FORTRESS MECHANICS TO LIFT INTO BIGVILLE

Bigville is already Dwarf-Fortress-shaped: per-agent simulation, glass-box history,
emergent social dynamics, decisions as the agent's own weighted choice. This is a
curated list of DF mechanics worth lifting, each judged by the same lens as the
fact/frame pass: **world-fact** (the engine may enforce) vs **human-frame** (agents
recognize) vs **decision** (a collapse), and whether bigville already has it. Sources
are the DF wiki pages fetched directly (URLs inline; verified content, July 2026).

## What bigville already shares with DF (do NOT re-lift)

Affect/grief/co-regulation/window (≈ DF thoughts→stress→breaks), directed Bonds
(≈ relationships/grudges), skill-by-doing with friction (≈ skills), hunger/sleep/energy
drives that mint goals (≈ needs, but only a *few*), health→death and violence any agent
can do (≈ the body layer), evidence + prosecution (≈ justice, partial), witnessed-vs-told
provenance (≈ witnesses), the inn/travellers/foreign-news (≈ caravan, partial), the
per-agent nightly journal (≈ the thought log, partial). The lifts below are the pieces
bigville *lacks or under-builds*, ranked by value × fit.

---

## TOP LIFTS

### 1. The Needs → Focus → Thought → Stress spine (the beating heart of DF's agent model)
DF's core loop, and the single richest lift.
- **Needs** ([Need](https://dwarffortresswiki.org/index.php/Need)): a *taxonomy* of drives
  (pray, socialize, make merry, admire art, be with family, craft, martial training, …),
  each of which, when unmet, **damages FOCUS**, and when satisfied **improves it** — and
  "better focus leads to better results from work — essentially a boost to all skills."
  Unmet needs spawn **personal-fulfillment jobs** (low-priority *Listen to Poetry*, or
  high-priority *Pray to Lorsïth!*) that compete with productive work. **Diversity**
  matters — repetition dulls, variety satisfies.
- **Thoughts** ([Thought](https://dwarffortresswiki.org/index.php/Thought)): every
  circumstance "evokes specific emotions based on their personality" → a happy/bad/neutral
  thought; a *single experience produces many thoughts* as it is **re-lived through
  memories**; accumulated thoughts drive **stress**.
- **Personality facets** ([Personality trait](https://dwarffortresswiki.org/index.php/Personality_trait)):
  0–100 per facet; facets "determine whether certain actions may give a good or bad
  thought," influence relationships (facets differing by >60 create friction), and
  **memories change facets over time.**
- **Stress** ([Stress](https://dwarffortresswiki.org/index.php/Stress)): sustained bad
  thoughts → tantrums / depression / oblivious stumbling → *harrowed* → **insanity**;
  reducers include bedrooms, a dining room, **meaningful work**, praying, performances.

**Why lift:** this IS bigville's native loop (drive → goal → collapse; residual → depth),
just far more textured. Bigville has affect (arousal/valence/grief) but only ~two drives
and no **focus-as-competence-multiplier**, no **needs taxonomy**, no **per-event
decaying-thought log keyed on personality facets**. Lifting it gives: (a) a general
`Need` type (each unmet need mints a fulfilment goal, generalising `need_drive_goal`);
(b) `focus` as a skill multiplier that unmet needs erode; (c) an `Event → Thought{emotion,
strength, decay}` log whose *sign is the agent's own facets* — literally the "value Term
reads the agent's own held params" from the collapse principle; (d) stress → break →
(bigville already has `viol_act`, so breaks can turn violent) the **tantrum spiral** the
sim half-has. Facets-change-with-memory closes a growth loop bigville lacks.
*Category: world-fact (affect in a body) + glass-box (the thought log deepens the journal).*

### 2. Strange moods → named artifacts with recognized value + history
DF's most beloved emergent-story engine, and it lands squarely on the recognition thesis.
- **Strange mood** ([Strange mood](https://dwarffortresswiki.org/index.php/Strange_mood)):
  periodically an agent is **seized by an idea for a legendary artifact** and pursues it
  "to the exclusion of all else — will not stop to eat, drink, or sleep"; if they can't
  begin within months they **go insane and die.** Mood types (Fey / Secretive / Possessed
  / Fell / Macabre) colour it; the mood **demands specific materials.**
- **Artifact** ([Artifact](https://dwarffortresswiki.org/index.php/Artifact)): a unique,
  *named* object of unsurpassable quality — "the ultimate expression of a dwarf's desires,
  fears, memories and hopes in art-form"; one per dwarf per life; it can be "traded,
  stolen, sold or warred over, and may transfer between civilizations." Quality tiers:
  ☼MASTERWORK☼ / ≡EXCEPTIONAL≡ / *SUPERIOR* / +FINE+ / xTATTEREDx.

**Why lift:** an artifact's worth is **recognized/social, not intrinsic** — it is a
*human-frame* by the pass's own definition, and it *circulates and is coveted*. This ties
three threads together: the **recognition** work (value = recognition, and a coveted
artifact becomes something to claim/steal/tax), **case-reconstruction** (objects with
provenance/history), and the **generative faculties** (the substrate already mints named
things with history — headlines, journals). Build: a `creation_drive` that, when it fires,
has the agent mint a named `Artifact{quality, provenance-of-its-maker's-held-state}` — the
artifact literally encodes the maker's dominant thoughts/needs at the moment (glass-box) —
and a recognized `value` that other agents grant, making it coveted. *Category: world-fact
(the object exists) + human-frame (its value is recognized).* HIGH — very DF, very on-theme.

### 3. Justice depth: witnesses → case → interrogation → conspiracy (+ deception)
Deepens the court exactly where the governance plan is headed.
- **Justice/Interrogation** ([Interrogation](https://dwarffortresswiki.org/index.php/Interrogation)):
  a crime opens a **case** with an injured party, a status (*Unsolved*), and the
  **witnesses who reported it**; the sheriff/captain can **interrogate** suspects or
  **convict**; there are **cold cases** and an **intelligence tab** for uncovering
  **conspiracies**. Justice only exists once a sheriff/captain office is filled — and (from
  the earlier research) mandate infractions auto-punish but *murder requires a conviction*.

**Why lift:** bigville has evidence + prosecution but not the **case → witness →
interrogation → conspiracy** layer, nor **false identity / deception** (a criminal hiding
who they are). This threads through everything bigville is strong at: witnessed-vs-told
provenance (`hold`), ToM and deception (`drama_social`), and the recognition-gated court
(the pass). Build: a `Case` object accreting witness testimony (each a held belief with
provenance), an `interrogate` decision (a collapse that may extract a confession or expose
a co-conspirator edge), and identity/disguise so a witness can be *wrong*. Wrongful
conviction falls out for free — and is a feature, not a bug, in a glass-box sim.
*Category: mixed (harm = world-fact; case/verdict/authority = human-frame, recognition-gated).*

### 4. Nobles' demands + mandates: recognized status → entitlements + binding orders
Integrates directly with the governance plan (R1 office-as-claim).
- **Nobles** ([Noble](https://dwarffortresswiki.org/index.php/Noble)): office-holders
  "elevated to a position of rule"; **some offices are automatically ELECTED by the
  citizenry** (the mayor), "mostly outside of the player's control"; higher office-holders
  "can make **demands** and set legally-binding **mandates**, which, if not met, will upset
  them" and they **punish** dwarves. A mayor gives a happiness bonus (dwarves "yell at or
  cry on someone in charge"). Fortress **wealth attracts the monarch** — and invaders.

**Why lift:** two on-theme pieces. (a) **Status → material entitlements + mandates**, which
the pass says must be *recognized*: a mandate binds only recognizers and is punished only
by a recognizing enforcer (this is exactly R3/R4 of the governance plan). (b) The
**citizenry-elects-the-mayor** mechanic is a *recognition mechanism DF already ships* — it
validates R1 (office as something the town confers, not a seeded edge). And **wealth
attracts the monarch/invaders** is Olson's roving bandit in game form: a prosperous,
weakly-defended town is a target — the hook that connects the DF lift to the recognition
work. *Category: human-frame (recognition-gated), with wealth-as-magnet a world-fact pull.*

### 5. Caravan + diplomat/liaison: a recurring negotiated external relationship
Extends the wider world (Giantville) already half-built.
- **Diplomat** ([Diplomat](https://dwarffortresswiki.org/index.php/Diplomat)): once a
  fortress has a baron, diplomats from other civs arrive with the caravan and **attend a
  meeting with your leader** (the *Conduct Meeting* job, done in an office) to discuss the
  situation; **if the leader is killed/replaced/absent/moody, the diplomat leaves
  "unhappy"** — souring relations (toward sieges).

**Why lift:** bigville has one-shot travellers and foreign news; DF adds a **recurring,
negotiated, memory-bearing** external relationship (trade agreements, next-year requests,
alliance/war) that **requires a recognized leader to negotiate with** — no recognized
office, no diplomacy (another R1 payoff). Inter-town war then becomes the outward form of
the same recognition dynamics. *Category: mixed (movement/goods = world-fact; the treaty =
human-frame).* MEDIUM-HIGH.

---

## SECONDARY DEEPENERS

- **Quality tiers on made goods** (the ☼MASTERWORK☼…xTATTEREDx bar on every DF page):
  goods currently have no quality in `bigville_trades`. Add maker-skill-driven quality →
  price/desirability/mood. Cheap, deepens the economy, feeds #1 (a masterwork admired =
  a good thought) and #2 (artifacts are the top of this ladder).
- **Worship as a NEED** ([Need](https://dwarffortresswiki.org/index.php/Need) lists
  *Pray to Lorsïth!* as a high-priority need): make church attendance driven by a prayer
  **need** (deepening the emergent congregation from a disposition into a drive), with
  multiple deities/spheres and temples that require value.
- **Meaningful work / family / art as stress reducers** ([Stress](https://dwarffortresswiki.org/index.php/Stress)):
  wire "meaningful work satisfies" and "being with family / seeing art heals" into the
  affect layer (part of #1).
- **Medical granularity** (known DF system; page not fetched this session): specific wounds
  by body part, infection, recovery, permanent disability, doctor skill. A world-fact
  body-layer deepener; deferred.

---

## The unifying insight

DF's **Needs → Thought → Stress** spine *is* bigville's drives → goals → collapse loop —
so lift #1 is a texture upgrade to the native engine, not a foreign graft. And the other
lifts are **the same migration the governance plan already scoped**: an artifact's value,
a noble's mandate, a court's authority, a treaty — every one is a *human-frame* the pass
says must be **recognized and enacted by agents, never fired on a status attr.** DF even
ships two of our answers: the **citizenry elects the mayor** (recognition, not a seeded
edge) and **wealth attracts the monarch/invaders** (Olson's roving bandit). So the
recommended order folds the DF lifts into the existing plan:

1. **Lift #1 (Needs/Thought/Stress)** first — standalone, high value, upgrades the core loop
   the whole sim runs on; no dependency on the recognition work.
2. **Lift #3 (justice depth)** and **#4 (mandates)** ride the governance plan's R1/R3 —
   build them *as* the recognition-gated court/authority, not on top of the forced one.
3. **Lift #2 (artifacts)** as the flagship emergent-story object once needs/thoughts exist
   (an artifact encodes the maker's held thoughts) and recognition exists (its value is
   granted) — it sits at the intersection and is the most "DF" thing bigville could gain.
4. **#5 (caravan/diplomacy)** extends Giantville once a recognized leadership exists.

Source pages (fetched via curl, dwarffortresswiki.org, verified July 2026):
[Need](https://dwarffortresswiki.org/index.php/Need) ·
[Thought](https://dwarffortresswiki.org/index.php/Thought) ·
[Personality trait](https://dwarffortresswiki.org/index.php/Personality_trait) ·
[Stress](https://dwarffortresswiki.org/index.php/Stress) ·
[Strange mood](https://dwarffortresswiki.org/index.php/Strange_mood) ·
[Artifact](https://dwarffortresswiki.org/index.php/Artifact) ·
[Interrogation](https://dwarffortresswiki.org/index.php/Interrogation) ·
[Noble](https://dwarffortresswiki.org/index.php/Noble) ·
[Diplomat](https://dwarffortresswiki.org/index.php/Diplomat).
