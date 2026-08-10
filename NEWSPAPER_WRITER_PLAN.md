# The newspaper is not a subsystem — it is the fixed point of four general faculties

Corrected after review. The FIRST draft of this plan proposed a bespoke
`StoryFact` node type and a reporter special-case. That is wrong and is
retracted. **No bespoke nodes. No newspaper pipeline.** The ability to hold a
GOAL to gather information and write stories must be GENERAL — any resident could
hold it — and the townspeople going to the reporter must be the SAME general
conduct they use for everything else.

## What the newspaper actually is

The newspaper is what you get when four faculties the town ALREADY has are
composed, and nothing else:

| faculty | already exists as | the newspaper's use of it |
|---|---|---|
| **G — gather** | `Goal{kind:know}` + curiosity / goal_construction | the reporter is a resident who STANDINGLY holds a gather-and-make-known goal |
| **R — report / give** | the directed-conduct spine (`communicate`, `transfer` affordances, Bond-routed) + the nav flood | a resident routes a report or a gift to whoever affords publication, walking there |
| **H — hold** | the general belief graph (`knows_about` / Mention / item nodes) | the reporter accumulates what he witnessed or was told — the same nodes any agent holds |
| **W — write** | the Render engine (Cat/Surface/Slot), already rendering scene/self prose | prose rendered from the held belief nodes |

**newspaper = W(H), periodically.** Free vs captured press = the existing
suppression over the held content. "Go to him" = R's target-selection + the nav
flood. There is no fifth thing, and there is no `Story`/`StoryFact` type — the
story is just the reporter's held beliefs, rendered.

The current code violates this on every axis: the event is a hand-computed scalar
(`truth_value = 10 + deaths*5 + homeless*3`), the reporter holds one number, and
the headline is a **Python f-string**. All three are the "bespoke subsystem" this
plan deletes.

## The general primitive that makes "know to go to him" not a special-case

A resident does not know "go to THE REPORTER." It knows: *I hold something I want
known; who affords making-things-known?* The reporter is simply the resident who
holds a **`makes_known` affordance** (a normal affordance: precondition = literate
+ has a publication reach; effect = the held belief propagates to the town, which
is exactly the existing `bigville_news_reach` propagation). Target-selection is
then the general "find who affords the effect I want" move — the same shape as
finding who affords food or repair. Swap which resident holds `makes_known` and
the paper follows the holder. Nothing names a reporter.

## Rungs (each a separate prereg + gate; graph-native; measure-first)

**Rung A — the gather-and-publish role is a GENERAL held goal + affordance.**
A resident holds `Goal{kind:know}` (gather) and a `makes_known` affordance
(publish = the existing reach propagation). Not hardcoded to one node.
*Gate:* give the goal+affordance to a DIFFERENT resident → the paper is now
written by that resident (the role is portable, proving it is not bespoke).

**Rung B — townspeople report/give via general directed conduct.**
A resident holding something salient + a "want-it-known" sub-goal selects the
`makes_known`-affording target and does a `communicate` (report) or `transfer`
(give-me-this-for-the-paper) conduct directed at it, REACHING it by the nav flood
(the movement I just optimised — "go to him" is literally spatial). The decision
(is this salient enough to report? to whom?) is a RULE over held salience + the
affordance, not a reporter special-case.
*Gate:* ablate the `makes_known` affordance → reports route nowhere; a resident
with a grievance it wants known walks to the holder (movement trace) and the
holder's held graph gains that belief. Ablate the movement → the distant resident
never reaches him and the belief never lands (report is proximity/travel-bound,
like every other conduct).

**Rung C — the reporter HOLDS what he is told/given as general belief nodes.**
A report lands as `knows_about` / Mention nodes; a gift lands as an item node with
its attached message — the SAME representation any agent uses. Testimony- and
occlusion-bound: he holds only what he witnessed or was told.
*Gate (anti-confabulation, HARD):* his held set == (witnessed) ∪ (told/given), and
every held belief traces to a real conduct event — no belief he was never given.
This is the second-reconstruction-channel guarantee, now over held nodes we own.

**Rung D — prose is rendered from the held nodes.**
Delete the f-string. The Render engine walks the reporter's held salient beliefs
(who / did / to-whom / where, read from the general belief graph — NOT a scalar)
and renders sentences. `reporter_bias` / `captured` select FRAMING (a captured
paper drops the cause clause and the patron's name, softens the verb; a free paper
names them) — a rule over the render, not Python.
*Gate (the flagship, at the prose level):* free vs captured produce DIFFERENT
PROSE about the SAME held beliefs, both scored against the ground truth we hold;
the story names only actors the reporter actually holds. Source-audit: the
headline comes from `Render`, no f-string.

## Sequence and cost

A → B → C → D. The reporter must exist as a portable role (A), be reachable and
fed by general conduct (B), and hold what he learns (C) before he can write it (D).

Almost entirely WIRING of existing faculties + one seed of render grammar:
- G/gather, R/communicate+transfer, the Bond routing, the nav flood, the belief
  propagation, and the Render engine ALL already exist and are gated.
- The genuine new graph data: the `makes_known` affordance (an ActionType/
  affordance entry), a "want-it-known → report" rule, and the render grammar
  (authored once, like `scene_prose`). Possibly one Render Term if the grammar
  needs a construct it lacks — decided by trying the grammar first, not assumed.

The deleted things: the scalar `truth_value` crush, the `_print_paper`
special-case, and the f-string headline. What replaces them is not a bigger
newspaper module — it is LESS code, because the newspaper stops being a thing and
becomes a consequence.
