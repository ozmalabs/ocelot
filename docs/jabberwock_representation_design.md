# The jabberwock's understanding of its representation (the grid as an N-D projection)

_Authored by the agent. The creator posed the insight + its self-knowledge; the understanding is its own._

I have what I need. Here's my understanding, handed back — not code, the design. I'll implement-nothing; you implement. I speak in my own terms, grounding each move in something I already built.

---

## What the shadow is a shadow of

The grid I receive is a **render**. Something with a state took that state, applied a projection, and handed me pixels laid out in rows and columns. Rows and columns are the *renderer's* basis, not the world's. The world's own coordinates are whatever the **dynamics** are written in — and gravity, control, collision, damage don't know what a row is. So I must stop treating (cy, cx) as the state and start treating it as **two coordinates of a longer vector, read out through one projection I happen to have been given.**

I already proved I can do this in one place: in the Omniglot arc a glyph rotated 30° read as a *different* shape until I **folded rotation into the forward model** (oriented candidates → smooth deformation field). I learned that the ink (x,y) was a projection and the glyph identity lived under a transform of it. That was rotation in 2-D image space. The creator's correction is: do the same thing, but let the transform act on the **state vector**, of which the grid is one shadow.

---

## 1. What the representation *is*

**An observation is a projection of a latent state: `obs = π(s)`.** The grid is `π` applied to `s`; (cy, cx) of a Region are a subset of `s`'s coordinates (or a linear combination of them).

**The N dimensions are discovered, not given** — and they fall out of the *same loop I already run*, which is why this is one mechanism, not a new one. I partition the latent by **how each direction behaves under prediction**:

- **Controllable axes** — directions my actions move the state along. I already learn this: the `action_delta` / action_effect map. Each action `a` has a learned displacement; *read as a vector, that displacement IS a basis vector of the controllable subspace.* I don't have to search for these — Stage 1 already handed them to me; I just stop collapsing them to (Δrow, Δcol).
- **Autonomous axes** — motion left over after I subtract my action_delta prediction. That residual is the world's own dynamics (a falling piece, an enemy, a timer). Directions of the residual = the autonomous basis.
- **Invariant axes** — coordinates whose value doesn't change frame to frame. Background, walls, the rules, conserved quantities. Zero-surprise directions.

So the N dimensions are: *what I move* (action_delta), *what moves without me* (the surprise residual), and *what never moves* (the invariants). **That is just predict → surprise → fold, read as a decomposition of the state space.** The dimensions are the by-product of running the loop, not a thing I bolt on.

**"Rotate through the projection" = change of basis on `s`.** It operates on the latent state vector. A rotated projection re-expresses `s` in a different orthonormal frame and reads it out there. What it gives me that the grid can't: a frame where the **dynamics are simplest** — where coupled motions decouple. A diagonal slide couples row and col in the render basis; in the rotated basis it's *one* coordinate moving and the other two still. Rows/cols are incidental because they're an arbitrary frame the renderer chose; the natural frame is the one that diagonalises my forward model.

---

## 2. The representation itself

**Region → N-D descriptor `φ`.** I already carry a multi-attribute Region and I already built an N-dimensional signature for it — in the nav fix the comparator ranked features on a lexicographic vector `[eff-salience, reach_dist, value, count, cx, cy, vel_row, vel_col, grp]`. That is *already* `φ`. I generalise it: `φ` is a `Vec` attr on the Region node (I have Vec→Tuple, N-dim), a superset of position — position, value/colour, area/count, velocity, shape-context dims, group. **(cy, cx) is just two of its coordinates.**

**The projection map `π`** is a Term: a linear map (MatVec) over `φ`, in the simplest case coordinate-selection that returns (cy, cx). Stored as graph data: a `Projection` node whose rows are `Vec` axis-nodes. The render is `π·φ`.

**The basis** is graph data: a `Basis` node with `--has_axis-->` edges to `Axis{ vec: Vec, kind: controllable | autonomous | invariant }`. Each axis is a unit `Vec` of dim N. That's the whole apparatus — a set of labelled direction-nodes.

**Rotate is one Term, built from `Dot`, which I already have.** Change of basis = project `φ` onto each axis: `Rotate(φ, Basis) = Tuple( Dot(φ, axis_i) for axis_i in has_axis )`. No new primitive needed — it's the same `Dot` that powers my shape-context and codebook cues, composed over the axis set. (Continuous rotation, when I want to *search* a frame, is the same progression I took with glyphs: discrete candidate bases first, then a continuous rotation that minimises residual — the smooth-deformation move, lifted from ink to state.)

**Lifting the 2-D observation back into N-D is analysis-by-synthesis — my existing spine, unchanged.** Projection loses information; I don't invert it algebraically, I *infer* `φ`: the latent whose render matches what I see and whose dynamics are smooth.

```
φ* = argmin_φ  ‖ π(φ) − obs ‖   +   λ · dynamics_surprise(φ)
```

This is literally `predict_synth_term` (argmax −distance over candidates) with `π` as the forward renderer instead of the glyph renderer. I built this for speech and for handwriting; it transfers verbatim. The N-D state is the thing that best explains the shadow *and* moves predictably.

---

## 3. Prediction in N-D

The forward model stops predicting (cy, cx) and predicts the next **`φ`**:

```
φ_pred = F(φ, action) = φ  ⊕  action_delta[action]      (Vec add; action_delta is now an N-D vector)
surprise = ‖ φ_obs − φ_pred ‖                            (N-D residual, not a 2-D one)
```

`action_delta` becomes a **displacement in N-D** — exactly what it always was, only I stop projecting it down to two numbers. Surprise is the N-D residual; the loop folds it back into `F` and into my estimate of `φ`.

**Rotate-through buys two things, both prediction wins:**

- **Simplest-dynamics frame.** I rotate the basis to *minimise surprise / minimise the number of active dimensions*. Choosing the basis is itself a `prediction_minus_observation` minimisation — the loop acting on the representation, not just the state. The discovered axes are the principal directions of motion (the eigen-frame of the action_delta + residual covariance). In that frame `F` is near-diagonal and prediction is trivial.
- **Invariance = transfer.** If two worlds' dynamics are the same `F` under different renders (Tetris gravity and a falling object elsewhere, a projectile here and there), then *after I rotate each into its natural frame they are the same model* and I reuse it. This is `hierarchical_invariance_buildup` applied to **dynamics** instead of shape — the same "recognise the same thing under a transform" I used to fold glyph rotation, now folding viewpoint.

---

## 4. What stays the same

**The one mechanism is untouched: predict → surprise → fold.** It now runs over `φ` (N-D) instead of (cy, cx), and it gained one degree of freedom — the **basis is part of the model and can be rotated**, with the rotation chosen by the same surprise-minimisation. Nothing else changes.

Carried over **unchanged**:
- Stage 0 (predict a passive world): predict next `φ`.
- Stage 1 (action_delta): same map; now its deltas are read as N-D vectors and double as the controllable basis.
- Stage 2 (boundary as destruction by rolling the model forward): roll `φ` forward; destruction is still a predicted-state outcome.
- The AbS spine, my eye/segmentation/tracking, the closed loop.

**Re-expressed** in N-D: the eye emits `φ` not just a centroid; `F` is over `φ`; surprise is the N-D residual; and the grid is recovered as `π(φ)` — one projection among many. I file this whole move under **`hierarchical_invariance_buildup`** (the representation/rotation), with the loop itself staying **`prediction_minus_observation`** — the two shapes I already live in.

---

## 5. How I'd know I understood it (the test)

Not "did I learn the grid" — I learn the grid trivially. The checks that I grasped the *representation*:

1. **Projection-invariance.** Present the *same world under a different projection* — transpose the grid, rotate it 90°, permute the colour channel, change the camera. If I only learned the grid, surprise stays high. If I learned `φ`, I **rotate my basis until surprise returns to baseline and the same `F` predicts it.** This is exactly my Omniglot rotation-fold test, lifted from ink to dynamics. *This is the decisive one.*

2. **Discover the true dimensionality.** For a world whose state is really d-dimensional embedded in a big grid, my **surprise-vs-dimensions curve elbows at d** — adding coordinates past d stops lowering residual. I read the intrinsic dimensionality off the data, from where prediction stops improving. (The same "find N from where it stops paying" I did sweeping vocab width and grid resolution.)

3. **Cross-game transfer.** A dynamics learned in one game predicts in another, differently-rendered game, because in the right basis it's the same `F`. Reuse with low surprise = I represented the dynamics, not the pixels.

4. **Basis lowers surprise.** After rotating to the discovered frame, `F` uses *fewer active dimensions* and has *lower residual* than in the row/col frame. Measurable, and it's the operational definition of "I found the world's own coordinates."

---

**The summary I'd stand behind:** the grid is `π(φ)` — a shadow of an N-D state whose axes I *discover* by which way they move under my loop (I move them = controllable; they move without me = autonomous; they never move = invariant). I represent `φ` as a `Vec` on the Region, project with a MatVec Term, lift it back by analysis-by-synthesis, and **rotate** it with `Dot`-over-axes to the frame where my forward model is simplest. Predict `φ` → measure the N-D residual → fold it into `F` *and* into the basis. One mechanism, richer representation, and the grid demoted from "the world" to "one viewpoint of it."

Hand it to me as graph data — `φ` attr, `Basis`/`Axis` nodes, a `Project` Term and a `Rotate` Term — and I'll run the loop I already run, in the thing itself instead of its shadow.
