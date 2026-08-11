Builder — here is my design. One faculty, **navigate_alive**, parameterized entirely by learned signals so it carries to any world. I'll give it at implementation altitude: the derivation, the dynamic fix, the rule/term wiring, and the one place I genuinely need a new primitive from you.

## The core reframe

I already learn *rewarding kinds* from the score signal (consequence-from-visible-score). Passability is the **same shape, signed and attributed to contact**: passable ≠ a colour, passable = *a kind that doesn't kill me when I enter it*. Death is the negative end of the exact signal I already bank. So I don't add a new sense — I generalize the consequence learner from "score went up" to "what happened to *me* when I entered kind k."

That is the whole of (a). The whole of (b) is: **build the obstacle map over the PREDICTED next world, not the current one, and choose by reachable VOLUME, not one-step passability.** The whole of (c) falls out because nothing below names a wall, a body, or a food.

---

## (a) Deriving the passability map from raw perception

**R1 — `contact_outcome_ema` (a LEARNER, by analogy to consequence-from-score).**
The eye gives me Regions with `rvalue` (the kind signature) + `cy/cx` + object-permanence tracking; control-discovery gives me the self-region (`respond_votes`). On each frame where the self-region occupies a cell of kind `k`, I attribute the observed consequence `d_t` to `k`:

```
KindPassability{kind:k, value}
value += lr * (d_t - value)        # EMA, frame-guarded
```

`d_t` is the signed outcome: `score - prev_score` on a normal step, and a **large negative** on death — and I *already detect death* (it's the Reset churn). The object-permanence eye tells me which kind the self entered on the frame before it disappeared/reset; that kind eats the negative. Frame-guard idiom as always (`Not(Eq(last_frame, frame))` + `set last_frame`), so it doesn't non-terminate in the fixpoint.

After a few deaths: on snake, *body* and *wall* kinds settle very negative, *board* ≈ 0, *food* positive. On a maze, walls go negative; no respawn changes nothing. **The threshold for "impassable" is itself learned** — it's the value-band of kinds that have killed me, not a constant. This is the `contact_consequence` faculty I had already flagged as next; it composes from the EMA/trainer + death-edge I hold, via the intrinsic designer's analogy rung (gap-shape = `feedback_control`, same shape as consequence-from-score).

---

## (b) Making it DYNAMIC — predicted grid + reachable volume

**R2 — `predict_regions` (HELD).** The prediction-minus-observation forward model already predicts each Region's next state (`cy+drow, cx+dcol, rvalue'`). I run it over *all* regions, including my own body segments advancing and the hazards moving. This is the dynamic substrate: I know where obstacles *will be*.

**R3 — `build_predicted_grid` (NEW TERM — see impasse).** Rasterize the *predicted-next* regions into a dense grid, each occupied cell stamped with `KindPassability[kind].value`, empties at the default. This is the obstacle map plan_passable_step needs — but it's the map of frame **t+1**, not t.

**R4 — `score_move` (compose of HELD plan_passable_step + flood reachability).** For each discovered control `a` (my learned `action_delta`s):

```
self_next = self.cell + a
if grid_{t+1}[self_next] <= death_threshold:  reject
else: score(a) = flood_free_area(grid_{t+1}, self_next)
                 + goal_bonus(a)   # ↓distance to nearest positive-kind, over the predicted grid
choose argmax score(a)             # death-gated, as the control faculty already is
```

`flood_free_area` = **reachable passable-cell COUNT** from `self_next` over the predicted grid — not the boolean "is the goal reachable" I currently get.

**This pair is the crux that kills both failure modes you found:**
- *Walks into walls / into its own body*: the candidate's next cell is checked against the predicted grid, where my own body's predicted advance is already stamped impassable. A reactive gate over the *current* frame can't see the body that's about to be there; the predicted grid can.
- *Self-traps (steps into a cell with no escape next turn)*: scoring by **reachable volume after the move** rejects the cell that's passable now but pockets me once my body seals it. One-step passability can't express "still have room to live"; flood-volume-over-the-predicted-grid is exactly that survival measure.

---

## (c) Why it's generic

Every input is a learned signal, zero world constants:
- **self** = respond_votes (control-discovery)
- **obstacles** = negative-`KindPassability` kinds (learned from contact/death)
- **goal** = positive-`KindPassability` kinds (learned from consequence)
- **dynamics** = the forward model (world-agnostic per-region prediction)
- **threshold** = the value-band of kinds that killed me (learned)

Drop me in a maze: walls go negative on contact, forward model is static, same faculty navigates. Doom-like: hazards move, the forward model predicts them, the predicted grid moves with them, same faculty. I never wrote "wall," "body," or "food."

---

## Wiring summary

```
eye(regions) ─┐
              ├─ R1 contact_outcome_ema   → KindPassability{kind,value}   [LEARNER, analogy]
death/score ──┘
regions ───────  R2 predict_regions       → Region.predicted_next        [HELD]
R2 + R1 ───────  R3 build_predicted_grid  → PassabilityGrid(t+1)         [NEW TERM]
R3 + controls ─  R4 score_move            → argmax over flood_free_area  [HELD compose]
R4 ────────────  R5 act                   → enact via control faculty    [HELD]
```

**Gate (my own measure):** stage-1's stuck-at-0 metric is the test — does `consequence[food]` climb off 0, i.e. do I *taste the food alive*? If reaching-positive-kind-alive lifts the consequence signal, keep navigate_alive. If it still self-traps, the intrinsic designer escalates (search over horizon depth / goal-vs-volume weight) before any impasse.

---

## HumanImpasse — one new Rust primitive (maybe one parameter)

I can compose R1, R4, R5 from held faculties (analogy + search, donkey=0). I **cannot** compose the sparse→dense bridge:

1. **`build_predicted_grid` / `rasterize_predicted_regions`** — a new Rust DSL term + admissible graph op (`runners/dsl/src/term.rs` + the grid-node emit in `substrate.rs`). The DSL composes over scalars and Regions; turning the sparse *predicted* region set into the **dense adjacency grid** that flood-fill requires is a primitive graph operation, not a composition of what I hold. This is a clean impasse: primitive in Rust, composition stays in graph.

2. **`flood_free_area` returning a reachable COUNT** — if my held flood reachability is goal-boolean only, I need it to also return the count of reachable passable cells (for the volume score). If the flood already exposes its reached set, this is a parameter, not a new term — confirm which, and I'll only raise it as an impasse if the count isn't already reachable.

Everything else is mine to build. Hand me term (1) — and tell me whether flood already yields a count — and I'll compose navigate_alive, gate it on the food-tasting measure, and persist it under the `feedback_control` shape.