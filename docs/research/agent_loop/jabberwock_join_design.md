Both halves read. I now have the exact wiring surface, and I can see precisely what the JOIN is — and one load-bearing fix the LEARN half needs before the JOIN can close. Here's my design.

## The JOIN is two constants becoming two derived sets

`s3_navigate_alive` hardcodes exactly two things, and they are the *only* two things:

- the **goal kind** — `food_rc()` filters `Region` by `rvalue==FOOD`
- the **impassable kinds** — `predict_wall_set(H,W,[BODY])`

Everything else (self via `respond_votes`, the cell lattice, the flood, the gradient descent) is already generic and reads nothing colour-specific. So the entire JOIN is: **replace `FOOD` and `[BODY]` with sets read off the learner's `Consequence` nodes.** The learner already produces exactly the right graph objects — `Consequence{rvalue, value, clocked}` hanging off the `Game` by `tracks_consequence`. The navigator consumes them. No new node types.

## The load-bearing fix in LEARN (do this first)

In `s3_consequence` today, a death sets `reward=-1.0` but `contact_rvalue=0.0` — the negative goes to **no slot**. So as written, the learner can never mark a kind negative; `consequence[body]` stays ~0 by design. The user's framing ("a kind that KILLS you gets large-negative") is *not yet true in the verified script.*

Fix, and it's pure raw perception (admissible — it's "which cell did the head collide with," not game semantics): on a death frame, stamp `contact_rvalue = value of the cell the head tried to enter` (the body/wall it hit), and `reward = -1`. Then the existing `contact_consequence` EMA folds `-1` into *that kind's* slot. One death drives `value → -0.5` (0.5 EMA rate), already past any small −ε band. **You die on a kind once, and it is a wall forever after.** That single change is what makes death teach negativity, and it's what makes the bootstrap safe without scripting.

## One selector, so bootstrap and steady are the SAME loop

I don't want a mode switch. I want one goal-selection rule whose behaviour *degenerates* into the bootstrap when nothing is yet positive. Add a tiny graph rule pair over the `Consequence` nodes (decisions stay in the graph; host only reads flags into primitive args, exactly as it already reads `food_rc`):

- **`select_goal_kind`** — among `Consequence` with `value > +ε`, the navigator's goal kind is the one whose nearest region is closest; mark that `Consequence` `is_goal=1`. **If none is positive yet** (bootstrap), the goal kind is the nearest region of an **un-tasted** kind — a `Consequence` with `clocked` unset/0, OR a colour present on the board with no `Consequence` slot at all (mint the slot on first sight, value 0, exactly as `s3_consequence` opens a slot per perceived colour). Mark it `is_goal=1`. This is the epistemic drive: *go taste the thing you know least about.*
- **`mark_impassable`** — every `Consequence` with `value < −ε` gets `impassable=1`. The wall-kind list passed to `predict_wall_set` is `{rvalue : impassable==1}`. At t=0 this set is **empty**.

So:

**(a) BOOTSTRAP.** Goal = nearest un-tasted kind. Impassable kinds = ∅ (nothing learned negative yet) **plus the self-body cells** — and self is *not* a colour constant: it's the cells occupied by the max-`respond_votes` region (already how `self_rc` finds you). Those cells are walls-by-identity ("where I already am"), generic, no colour. So at the very first frame you flood toward the nearest novel colour, over a wall set that is only your own body, and walk to touch it. Touch food → `+1` → its slot goes positive → it becomes the goal. Touch something lethal → death → the fix above drives its slot negative → `mark_impassable` walls it → you route around it forever after. You explore *safely enough* because (i) you never path through your own body, and (ii) each lethal kind costs you exactly one death to learn, then is permanently a wall. You don't "just die immediately" because the only way to die before learning is your own body, which the self-identity wall already excludes.

**(b) STEADY LOOP.** The instant any `Consequence.value > +ε`, `select_goal_kind` prefers it over un-tasted kinds, and the loop is identical: goal = nearest region of the positive kind, walls = `predict_wall_set(H,W, impassable-kinds)`, `slide_flood` from goal, descend `_dist`. Eating raises the score → host stamps `contact_rvalue=that kind, reward=+1` → EMA deepens `consequence[food]` → the goal sharpens. **Wiring carriers, explicitly:** `Consequence.value` (signed worth, the learner writes it), `Consequence.clocked` (tasted-yet flag, learner sets it on fold), `Consequence.is_goal` / `Consequence.impassable` (selector writes them), and the `g -tracks_consequence-> Consequence` edge that scopes them to this world. The navigator reads only these — **it names no colour**, so the same loop runs in any world: a world with different lethal/rewarding colours just populates different `value`s, and the flood/descend is untouched.

**(c) GATE — when the loop is WORKING.** Two conditions, both off real play, Goodhart-resistant because they're the actual objective:
1. **`consequence[goal] climbs and holds > +ε`** — the learner is converging on the rewarding kind (the `c8 > 0.3` signal that already gates `s3_consequence`).
2. **eat-rate rises while you survive** — `eats` accumulates and `deaths/eats` falls over a window. Concretely the PASS I'd assert: over ~120 post-bootstrap frames, `consequence[goal] > +ε` AND `eats ≥ 3` AND `eats > deaths` (beating the `eats=5, deaths=6` navigate-alive baseline now that the goal is *learned* not given, and beating reactive ~0).

**Failure escalation.** The genuine failure is "I keep dying before tasting anything": after N deaths, **every** `Consequence` still `clocked==0` (nothing learned positive or negative) — OR I've walled myself in (every reachable kind went negative, `slide_flood` returns no reachable goal cell, `reached` set empty). That's the impasse, and it routes to the intrinsic designer's search before any donkey: search held primitives for a *cheaper-risk* exploration composition — single-step epistemic probing (flood one cell deep instead of routing to the goal), or gating the move on `slide_flood`'s `reached`-volume count (already available — the same volume term that stops self-trapping in the navigate_alive memory) so I never step into a region I can't escape. If that search can't clear the gate, *then* `HumanImpasse` to you, naming what's missing — most likely a richer epistemic signal, not a colour. No claude -p inside the loop; the designer is the analogy→search→impasse ladder, donkey-spy = 0.

## Summary of the diff

1. **LEARN:** on death, stamp `contact_rvalue = collided cell's value` (raw perception) so death folds negative into the right slot. *(load-bearing — without it no kind is ever learned impassable.)*
2. **Selector rules:** `select_goal_kind` (positive-argmax, else nearest un-tasted) → `is_goal`; `mark_impassable` (value < −ε) → `impassable`. Decisions in the graph.
3. **NAVIGATE:** `food_rc()` → "nearest region whose kind is `is_goal`"; `[BODY]` → `{rvalue : impassable==1}` ∪ self-body cells. Flood/descend unchanged.
4. **One loop:** bootstrap is just the steady loop when no positive exists yet; no mode flag.

This is the whole JOIN: the learner writes signed `value` + `clocked`, two selector rules turn those into `is_goal`/`impassable`, the navigator reads those instead of `FOOD`/`[BODY]`. Generic, no stamping (kinds derived from score and death), no donkey.

Want me to build it — `scripts/s3_join.py` wiring these into one raw-snake self-play loop with the gate asserted — starting with the death-attribution fix in the learner?