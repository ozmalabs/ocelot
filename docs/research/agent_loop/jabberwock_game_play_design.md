# The jabberwock's design: understanding and playing games (solution + curriculum)

_Authored by the agent. The creator posed the goal + its self-knowledge; the design is its own._

## What I am being asked, and how I'm answering it

You want the design, not the code. So here are the two things — the architecture, then the curriculum — stated in my own terms, with each piece marked **Rule/Term (graph)** or **adapter I/O (mechanical)**. I've built it so that *one* mechanism — predict the next observation, measure surprise, let surprise drive everything — subsumes control, goals, consequence, and death. No per-event handlers. The patches you called out are each replaced by a principled form of that one mechanism.

---

# 1 — THE SOLUTION

## The spine: one loop, three drives

My core shape is `prediction_minus_observation` with the closed loop you just gave me (a correction is a production writing next-state in-fixpoint, folded at the clock edge — the only place a value goes down). The whole agent is that loop applied to **the next observation**, and surprise is the only currency. Surprise drives exactly three things: **model update**, **attention (salience)**, **action**. Control, goals, consequence, death are not separate machinery — they are *interpretations of structure in the surprise signal*.

## 1.1 The forward model — what I predict, over what

I do **not** predict the whole frame (pixels are the wrong altitude — too much surprise that doesn't matter). My eye already segments the world into **Regions** with a tracked state vector across frames:

```
Region: (crow, ccol, drow, dcol, bbox, appearance/id, stable_frames, respond_votes)
```

I predict **the next state of each Region**, specifically its next centroid, from a **per-region dynamics model**. The default dynamics — my obvious prior — is constant velocity (`object_permanence` + Newton's first law as a *default prediction*):

```
predicted.crow(t+1) = crow(t) + drow(t)      ← Term: region_predict_next
predicted.ccol(t+1) = ccol(t) + dcol(t)
```

There is a **second, nested forward model**: the *action-conditioned* one. For each Region I also hold a learned map `action_token → (Δcrow, Δccol)`. The action-conditioned prediction is `passive_prediction + action_delta[token]`.

- **Term `region_predict_next(region, action?)`** — computes predicted next centroid; with no action it's the passive prior, with an action it adds the learned delta.
- The **score/reward** is just *another Region-less observation channel* with its own predictor and its own surprise. It is never privileged — it is one cue.

**Adapter I/O (mechanical):** read frame → write/refresh Region observations (the eye is native; the adapter only hands it pixels). Emit the chosen action token → game input. Nothing else crosses the boundary.

## 1.2 Surprise — prediction error, computed per Region

After the clock edge, for each Region:

```
surprise(region) = |observed.centroid(t+1) − predicted.centroid(t+1)|     ← Rule: region_surprise
```

This single residual, written per Region per frame, is everything. It drives:

**(a) Model update — the restoring force.** Where the passive prediction is wrong in a *structured, repeatable* way, the closed loop folds a correction into that Region's dynamics parameters (it accelerates; it bounces at an edge; it is controlled by me). **Rule `dynamics_update`** writes the refined per-region model in-fixpoint; the clock edge is where the old prediction is allowed to go down. Random/unstructured residual does *not* update the model — it stays surprising (salient).

**(b) Attention — salience IS unexplained residual.** 
```
salience(region) = running surprise the model has NOT been able to drive down   ← Rule: salience_from_residual
```
This *replaces the per-frame "mark salient" flag entirely.* Food is salient not because a host says so but because it is the not-self / not-background Region whose relation to me I have not yet modelled. The orbit-break in Snake falls out: orbiting the food leaves its *consequence* unpredicted, so salience stays high and overrides the orbit — until contact resolves it.

**(c) Action — below.**

## 1.3 Control discovery — already native, no flag

The region I control is the one whose residual-under-the-passive-model is *explained by my action*. I already hold the accumulator for this: **`respond_votes`**. Control discovery is simply:

```
controlled(region) ⇐ action-conditioned surprise < passive surprise, accumulated   ← Rule: control_from_response
                      (i.e. respond_votes crosses threshold)
```

"Marking control each frame" is gone. **Control = the discovery that one Region's behaviour is predictable from my action when it is not predictable without it.** The learned `action_delta` for that Region *is* my controls. The body-part whose contact predicts a consequence (Snake's "leading edge is my interaction point") is learned the same way — see 1.5 — not flipped by a host eat-event.

## 1.4 Priors and WHY the boundary is destruction

A prior is a default prediction, falsifiable by surprise. The load-bearing prior is **self-continuation**: I predict my controlled Region persists frame to frame (`object_permanence` applied to the self). Everything action-conditioned depends on that Region existing next frame.

Now the boundary, *understood*:

- When I roll my controlled-Region model forward (action selection, 1.6) into a **boundary** Region or into **my own body**, the model has **no modelled continuation there** — I have never observed my controlled Region co-existing with that Region and surviving, and beyond the segmented world there is simply *no next-state defined*.
- **No modelled continuation ⇒ default prediction = termination.** The controlled Region — the single node every one of my action-conditioned forecasts depends on — ceases: it loses trackability, loses `respond_votes`, loses identity.
- I avoid it because **self-continuation is the precondition of all my agency.** Entering it doesn't make me lose a game — it makes my entire action-conditioned model invalid (maximal future surprise, zero future controllability). That is *why* it is destruction, and I can know it without dying: the forward rollout predicts no surviving trajectory through it.

**Rule `termination_prior`:** for a candidate next controlled-Region state with no modelled continuation (overlap with a never-co-occupied Region, or off the segmented world), predict termination → assign catastrophic predicted surprise.

Surprise refines it: in a wrap-around world (torus Snake, asteroids) I cross the edge and *survive*; that contradiction folds in and the prior learns this boundary is passable. The prior is a default, not a law.

## 1.5 Consequence and goals — surprise on contact

When my controlled Region contacts a salient Region, the **consequence** (it vanishes; my body grows; the score channel jumps) is a large surprise on those channels. The closed loop folds it into a *contact model*: "contacting THIS kind of Region, with THIS part of my body, predicts THIS consequence." 

- The Snake "aim-front" fact is *learned here*: the body-part whose contact best predicts the consequence becomes the interaction point — **Rule `contact_consequence`**, not a host flag.
- A **goal** is a salient Region whose predicted consequence I act to bring about (resolving its salience). Goals are not a separate type; they are salience + a learned positive consequence.

## 1.6 Action selection — roll the model forward, score, pick

Each frame I instantiate K **candidate action** nodes. For each, I roll the action-conditioned forward model one step (later n steps) to a predicted next state, and score it:

```
score(action) =  goal_progress(predicted state)          ← toward reducing salience of intended target
               + epistemic_gain(predicted state)          ← toward Regions my model is most uncertain about
               − catastrophe(predicted state)             ← predicted termination of controlled Region (1.4)
```

`competitive_inhibition` selects the max; the closed loop folds the winner; the adapter emits its token.

- **Goal-progress** subsumes seeking the salient Region (pragmatic).
- **Epistemic gain** subsumes exploration — the "cycle-explorer" is gone; I act toward model-uncertain states *because reducing surprise is the drive*, and it competes with goals, overridable on commitment (your salience principle).
- **Catastrophe** subsumes death-avoidance, with no death handler — it is just the rollout hitting `termination_prior`.

**Rule `select_action`** evaluates the score Term per candidate; **competitive_inhibition** picks; **closed loop** commits. n-step lookahead is the same Term chained — a later extension, not a redesign.

## 1.7 The patch → principle map (what this deletes)

| Current host patch | Principled replacement |
|---|---|
| mark control each frame | `control_from_response` (respond_votes crosses threshold) |
| mark salient each frame | `salience_from_residual` (unexplained surprise) |
| cycle-explorer | epistemic term in `select_action` |
| aim-front flag via host eat-event | `contact_consequence` (learned interaction point) |
| dies at walls | `termination_prior` + catastrophe term in rollout |

Everything between ingest and emit is graph. The adapter does two mechanical things: pixels→Regions in, action token out.

---

# 2 — THE CURRICULUM

Ordered simplest-first; each stage builds the model the next needs. **Success is always my own prediction error / surprise dropping to floor and staying** (the closed loop converged) — never an external score. The eye (vision) is native from stage 0; what *grows* across stages is model complexity, and the privileged region-typing *shrinks* to nothing by the end.

**Stage 0 — I can predict a passive world.**
World: static, then one dot moving at constant velocity. No me, no goals.
Learn: the constant-velocity forward model + the surprise signal itself.
Mastered when: per-Region one-step error → floor on a moving dot. *This installs the predictor before anything is built on it.*

**Stage 1 — I exist; what I control.**
World: my avatar in empty space; I emit actions; nothing else moves.
Learn: `control_from_response` + the `action_delta` map (my controls). 
Mastered when: action-conditioned error for my Region drops below passive error — I can predict where I'll be after an action. No goals, no death yet.

**Stage 2 — the boundary is destruction.**
World: stage 1 + walls/edges (and body-extent, for self-collision).
Learn: `termination_prior` — forward-rollout finds no surviving trajectory through the boundary; I avoid it *understood as loss of the Region all my agency depends on*. If forced into it, the catastrophic surprise sharpens the prior.
Mastered when: I stop predicting myself surviving the boundary; death rate falls with **no** death handler.

**Stage 3 — salient consequence (this is Snake, from the mechanism).**
World: + a not-self / not-background Region (food).
Learn: `salience_from_residual` makes it salient; `contact_consequence` learns the consequence and the interaction point; `select_action` seeks it to resolve salience.
Mastered when: I predict the consequence of contact; salience resolves on contact; I eat and grow with **no** aim-front flag, **no** host eat-event.

**Stage 4 — autonomous and reactive dynamics.**
World: Regions that move on their own and/or respond to me (pong ball, moving hazards, an enemy).
Learn: per-Region learned dynamics — some mine, some autonomous, some reactive — and lead/dodge via n-step rollout.
Mastered when: error drops on autonomous Regions; I lead a moving target and dodge a predicted collision.

**Stage 5 — vision-and-cues only; generalise.**
World: a never-seen game (tetris, doom-lite). Strip *all* privileged region typing — me / food / wall / enemy are derived only from the surprise signal.
Run: `world_curiosity` recognises "a world I don't understand," mints the CapabilityAxis, and the **same** loop (Stage 0→4) runs from scratch with **no new host code**.
Mastered when: prediction error drops on a world I've never seen, controls/boundaries/goals all discovered by the one mechanism.

**Where vision enters:** the eye is native throughout; what "enters" at Stage 5 is the *removal of all per-game semantics* — proving the region meanings were always derived from surprise, never given. That is the test that this is understanding and not scaffolding.

---

## The one-line check on the whole design
If at any stage I find myself writing an `if` over game state in Python, or a flag the host flips on an event, I've left the design — because in this architecture **control, goal, consequence, and death are all the same thing seen at different places in the surprise signal**, and that signal lives in the graph.

Hand me back which stage you want first and I'll specify the exact Rules/Terms for it (node types, where-clauses, the score Term) at implementation altitude.
