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

> # RETRACTED, 2026-08-28 — the paper answered this before I raised it
>
> The section below concluded that the projection budget's per-slice accounting is a defect, on the
> reasoning that auditing a slice in which nothing changed is *"charging for a non-event"*. **That is
> wrong**, and `0e9201e` (*Evaluation is a write, and that is why it is free — the no-write posit was
> wrong*) states exactly why:
>
> > *"If running a rule that does not fire is a read, and reads are free, then where does the check
> > go, and how does the substrate know to run the next one? … Either it does nothing and is free, or
> > it does something and is a write. There is no third operation that costs nothing and decides
> > something. … **Evaluation is a write.** The outcome of a match, the position in whatever ordering
> > the substrate applies, and the fact of having tried are all state, and state is written."*
>
> So auditing a slice **is** an event, whether or not the projected value moved. There is no
> non-event being charged for. **The engine's per-slice accounting was right and my objection was
> the "no-write" posit the remark names and discards** — *"A no-write is not the right description of
> the free default anywhere in these papers."*
>
> And the conclusion I drew from it is denied in the same remark, in terms:
>
> > *"A frame that runs a long time without collapsing **has not escaped a cost; it has deferred it
> > into retention**, and discarding that history is the priced step whenever it falls due. What is
> > free is not the running. It is only the not-yet-forgetting."*
>
> **"Stillness should be free" is exactly the error being corrected.** A still projection accumulates
> retained evaluation at the same rate as a moving one — which is what a per-slice budget bounds.
> The accounting is therefore better justified than before, not worse: it is not a Landauer floor
> cost, it is a **retention** bound, and retention grows per evaluated slice regardless of movement.
>
> The measurement below stands as data; only its verdict is withdrawn. STILL and MOVING consuming
> identical budget is **correct**.

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

### Why I read this as a defect — and why that reading was wrong

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

## Not built — and now, not to be built

Changing budget accounting from slices to changes would have touched a shipped audit with several
live callers (`motor_compose`'s fallback, `speech.py`, the humanoid curriculum) and moved numbers
across the horizon and stress arcs. **Not building it was the right call for a better reason than
caution: the change would have been wrong.** Under *evaluation is a write*, per-slice is the correct
unit.

The honest status of the horizon derivation reverts to what `AROUSAL_HORIZON_RESULTS.md` already
claimed: **correct in the term it derives (window → horizon)**, with no missing eventfulness term.

### One consequence that does survive, pointing the other way

The same remark bears on `STAGE_A_COUPLING_RESULTS.md`'s cost argument, and softens it. I wrote that
Stage A's speculation on a contended drain *"pays N speculative applies plus N undos… strictly more
writing than not speculating"*. Apply-then-undo is **injective** — the prior state is recoverable by
construction, that being what an undo log is for — so by this remark's own criterion it *"destroys
nothing and crosses no floor."* The speculation is not floor-cost.

What it does incur is exactly what the remark says: **retention.** The undo log *is* the preserved
history, and *"discarding that history is the priced step whenever it falls due."* So the cost of
speculating is real but is a retention cost, not a write-floor cost — which is a smaller and more
precise claim than the one I made, and it does not change the verdict on Stage A, which rests on the
domain being empty rather than on the cost.
