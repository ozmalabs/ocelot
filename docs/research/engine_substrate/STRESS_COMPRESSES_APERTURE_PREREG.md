# STRESS COMPRESSES APERTURE — pre-registration (block 366000)

Base sha at prereg: `3da4e0c`. Committed before any confirmatory measurement.
Measure will be `scripts/stress_aperture_measure.py` → `results/stress_aperture/results.json`.

## 0. The claim

`arousal_window_coreg` already narrows the **window of tolerance** under dysregulation. The claim
here is that stress narrows a second thing, on a different axis: **what the agent can RESOLVE**.

That is now expressible. `future_manifold.rs` takes a per-dimension aperture mask
(`policy.future_manifold_resolved_dims`), and an unresolved dimension is counted as *unassessed* —
`information_loss`, not `loss`. So a compressed aperture makes an agent **measurably stupid in the
exact technical sense built two rungs ago**: not wrong, unable to tell.

## 1. Why this is not merely "stress reduces performance"

The interesting content is the *shape* of the deficit, and it makes a crossover prediction against
the obvious alternative:

| | more exposure / stronger evidence | co-regulation (restore the window) |
|---|---|---|
| **compressed aperture** | **inert** | **recovers** |
| **reduced gain** (the alternative) | recovers | inert |

If stress merely lowered a learning or grounding gain, more evidence compensates — that is what a
gain is. If stress compresses aperture, **no amount of evidence compensates, because the distinction
is not resolvable at any exposure.** You cannot average your way to a difference you cannot see.

This is the same shape as `APERTURE_AETIOLOGY_CROSSOVER_RESULTS.md`, with a *physiological* cause in
place of a negotiated frame — and it is the clinically familiar observation that reasoning with a
dysregulated person does not work while co-regulation does, arrived at mechanically rather than
imported.

## 2. What this rung measures, and what it does NOT

**MEASURED (manifold half).** A `dysregulated` agent's projection audit:

* `information_loss > 0` while `loss == 0` — unassessed, not failed;
* `resolved == false`, `retained_width == 0`;
* `feasible_selection` yields the STUPID signature — non-empty `unestablished`, empty `feasible`,
  empty `withheld_minimal` (not stubborn), non-empty candidate family (not ignorant);
* raising evidence strength does not change any of the above;
* returning arousal to the window restores all of them.

**NOT MEASURED, and named rather than implied (learning half).** `learning_progress_curiosity`
gates curiosity and attention on `learning_progress = residual_prev − residual` — a *difference of
residuals*. The structural argument is that a residual which cannot be **established** has no
difference to take, so a compressed aperture should not slow the learning signal but **remove** it.

That argument is not run here. The learning seed's residual is a held-surface temporal surprise, not
the manifold residual, and wiring one to the other is real work that would have to be done honestly
rather than asserted. **Recorded as a named prediction with its reason, not as a result.** Anyone
reading this section should treat the learning claim as unbuilt.

## 3. The build

`seeds/stress_aperture.json` (to build): one rule. An `AffectiveState` with `dysregulated == 1`
compresses its agent's `future_manifold_resolved_dims`; returning to the window restores it. Inert
without the affective state — a graph that never loads it is unchanged.

Compression is **not a new scalar**: which dimensions survive is read from graph data
(`AffectiveState.stress_resolves`), the same way `observer_aperture` reads `Observer.resolves`. A
hand-tuned "stress factor" would be exactly the scalar-standing-in-for-a-shape defect `CLAUDE.md`
names, and would also make the result unfalsifiable by construction.

## 4. Gates and their failable controls

**G-stupid-not-wrong.** Compressed ⇒ `information_loss > 0` AND `loss == 0`. **FAILS IF** compression
registers as loss — that would mean the agent believes it saw a failure it could not see, which is a
worse bug than the one being fixed.

**G-evidence-is-inert.** Raising the evidence strength across its full range leaves every compressed
verdict unchanged. **FAILS IF** any strength recovers it — that would show compression is
attenuation, i.e. a gain, and the whole distinction collapses.

**G-regulation-recovers.** Returning arousal to the window restores `resolved`, empties
`unestablished`, and re-populates `feasible`. Positive control: without it, "nothing helps" would
pass trivially for an agent that is simply broken.

**G-not-the-other-two.** Compressed ⇒ `withheld_minimal` empty and the candidate family non-empty.
Distinguishes this from stubbornness and ignorance, which present identically from outside.

**G-byte-identity.** Absent the seed, or with the agent regulated, the audit is identical to no
aperture mask at all.

## 5. Honest bounds, registered in advance

One fixture, hand-set dimension masks, deterministic arms — n=1 by construction, no CI, no cohort.
`arousal_window_coreg` carries its own standing caveat (an authored affect model, not a clinical
one) and this inherits it in full. Nothing here is a claim about human stress physiology; it is a
claim about what this substrate can represent and how the representations compose.

The load-bearing weakness, stated now: **the compression is stipulated, not derived.** Nothing in
the substrate explains *why* stress should compress this particular set of dimensions — the rule
applies a mask the fixture supplies. Demonstrating that dysregulation compresses aperture is
therefore a demonstration that the two subsystems COMPOSE, not evidence that they do so in nature.


---

## ADDENDUM (block 366500) — the learning half, registered before measuring

§2 recorded the learning claim as unbuilt. It is now being measured, so its predictions are
registered here first, at base sha `6bf8687`, before `seeds/learning_aperture_gate.json` exists.

**Reading the seed changed the prediction, and the new one is worse.** §2 guessed that a compressed
aperture would leave `learning_progress` *undefined*. It will not. `lp_residual` computes
`residual = |obs − held|`, so an observation the agent cannot resolve arrives looking like what it
already predicted, and the residual is **zero**. Zero is not "I could not tell". Zero is the signal
for **"I have mastered this"**.

So the registered prediction is not that stress removes the learning signal. It is that stress
**forges** it:

* **P1** — compressed ⇒ `residual == 0`, `learning_progress == 0`, `attended == 0`. The item is
  dropped from attention *as if learned*.
* **P2** — a genuinely MASTERED item (`obs_true == held`, agent regulated) produces the **same
  values on every learning field**. The two are indistinguishable in the learning signal.
* **P3** — they are distinguishable only by whether the observation was ESTABLISHED, which nothing
  in `learning_progress_curiosity` currently records.
* **P4** — more exposure does not recover the compressed arm, matching the manifold result.
* **P5** — a regulated agent on the learnable item attends (positive control).

**This is the same defect as `loss ≡ information_loss`, one layer up**, and it is live in a shipped
seed rather than hypothetical: *residual-zero-because-mastered* and *residual-zero-because-blind*
are the same number today.

**FAILS IF** the compressed arm's residual is non-zero (then the channel is not really gated), or if
P2's arms differ on any learning field (then the signal already distinguishes them and there is no
defect to report), or if exposure recovers the compressed arm (then it is a gain, not an aperture).

Wiring: the gate mirrors `abg_gate_observation` exactly — an observation reaches the learner only if
its dimension is resolved, membership read from graph data (`In(item.obs_dim, aff.stress_resolves_dims)`),
never a tuned coefficient. Third occurrence of one shape, deliberately kept identical.

Bound, restated: as with the manifold half, the compression is **stipulated**. This measures whether
the subsystems compose and what the composition exposes, not why stress compresses anything.
