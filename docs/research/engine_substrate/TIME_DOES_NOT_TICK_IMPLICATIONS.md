# "Time doesn't tick, it changes" — what the 2026-08-28 revision costs this tree

The papers moved again. Read against the tree, three things: one of my quotes is stale, one of my
arguments is unaffected, and **one measurement says a recent build is charging for non-events**.

## What actually changed on time

The axiom itself is unchanged in substance — *"What the substrate has is change: realised
collapses… A time dimension exists only where a frame instantiates one to represent that order"* —
but the collapse sentence was sharpened, and the sharpening is the operative part:

> *"A collapse is a **local realisation** — a rule writing a delta — and it is the only kind of event
> the substrate has (its synchrony or asynchrony with other collapses is set by coupling). **Between
> writes nothing happens: an unwritten frame produces no change, so it takes no new position in the
> order the changes carry, and no time passes for it.**"*

Two further edits matter here: *"asynchronous"* was **removed** from the definition of collapse and
made a coupling property; and momentum was restated — the standing thing is **structure**, and
*"a delta is a write **to** that structure, not the structure itself"*.

Separately, and worth flagging because earlier work cited it: **the "no direct self-alteration"
falsifier is gone.** The proposition now reads *"A graph changes itself and its subgraphs directly.
Self-change is real — the round-trip picture of earlier drafts was too strong."*

## Housekeeping against the tree

* `STAGE_A_REASSESSED_AGAINST_V23.md` quoted *"a collapse is a local asynchronous write and the only
  event"*. **That sentence no longer exists.** Corrected in place. The argument it supported —
  synchrony must come from a coupling, so a drain-wide immutable base is synchrony without one — is
  **unaffected**, because that is what the new wording says more directly.
* That document does **not** rely on the retracted self-alteration proposition (checked, zero
  references), so nothing else there needs withdrawing.

## The measurement: the projection budget counts slices, not changes

`arousal_horizon` derives an agent's planning horizon as a **capacity** — a resource, therefore a
cost. The theory's cost falsifier is *"Cost is the write"*, and the sharpened axiom says an unwritten
frame produces no change and takes no new position. So a projection that **never changes** should not
cost the same as one that changes at every slice.

Measured — two candidates, identical slice count, different change count:

| budget | candidate | horizon | resolved | `information_loss` |
|---|---|---|---|---|
| 2 | STILL (0 changes) | 2 | 0 | 4 |
| 2 | MOVING (5 changes) | 2 | 0 | 4 |
| 3 | STILL | 3 | 0 | 3 |
| 3 | MOVING | 3 | 0 | 3 |
| 6 | STILL | 6 | 1 | 0 |
| 6 | MOVING | 6 | 1 | 0 |

**Identical in every cell.** The audit consumes one unit of budget per represented time slice,
whether or not anything happened in it.

### Why this is a defect rather than a convention

Represented time is legitimate — the axiom explicitly permits a frame to instantiate one. What is
not legitimate is charging a **cost** against it. `future_manifold_projection_budget` is used as a
resource (that is exactly what `arousal_horizon` derives), so under *"cost is the write"* it should
be consumed by changes, not by slices.

The consequence is concrete and inverts an intuition the horizon work was resting on: **stillness
should be free.** A regulated agent whose projected arousal is flat is having no events at all, and
should be able to project much further on the same capacity than one whose arousal is climbing.
Today it gets exactly the same horizon. So `AROUSAL_HORIZON_RESULTS.md`'s monotone table is right
about the window and silent about this second, independent term — the *eventfulness* of what is being
projected.

## Not built

Changing budget accounting from slices to changes touches a shipped audit with several live callers
(`motor_compose`'s fallback path, `speech.py`, the humanoid curriculum), and it would move numbers in
`AROUSAL_HORIZON_RESULTS.md` and the stress arc. It is recorded here as a measured consequence with
its fixture, not acted on. The honest status of the horizon derivation is therefore: **correct in the
term it derives (window → horizon), incomplete in a term the theory says exists (changes, not
slices).**
