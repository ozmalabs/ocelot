# Communication as deformation — what the substrate confirms, and the axis it does not have

Against `d90df44` (*Truth buys no exemption: communication and manipulation are one operation, and
the substrate shows it*) and `af65293` (*a borrowed name is a decode against a held codebook, or it
is a mint*), both 2026-08-28.

**One claim is confirmed by measurement made before the paper stated it. The other names a
discriminator this substrate cannot currently represent at all.**

## Confirmed, and independently: no second primitive

> *"what does **manipulation** need to do that **communication** does not? Structurally, nothing.
> Both are deformation of another frame's fields — altering what continuations cost for it — and the
> substrate has no second primitive for the disreputable case."*

`seeds/aperture_frame.json` measured exactly this, for a different reason, before the claim was
written. Its three modes — **chosen**, **forced**, **negotiated** — are not three mechanisms. They
share one projection, one meet, one decode, and `APERTURE_PATHOLOGIES.md` records the measurement
directly: the modes **decode identically** and differ only in **recourse**. A forced frame and a
negotiated one produce the same `covered` / `residual`; what differs is who may lift it.

So the substrate does not merely lack a second primitive for the disreputable case — it was built
with a place for one and did not need it. That is a stronger form of the paper's claim than an
argument, and it is the reason `APERTURE_PATHOLOGIES.md` §2's folie à deux is *silent*: nothing in
the mechanism distinguishes a shared frame that helps from one that harms.

## Not represented: whose manifold the deformation serves

> *"Manipulation is not the false quadrant. It is the quadrant where the deformation serves the
> author's goals while presenting as serving the reader's… the whole of the ethical load sits on
> intent and on whose goals are being optimised."*

Measured in the tree: **`beneficiary` exists only as a thematic role** — a parsing notion in
`seeds/thematic_roles.json`, i.e. who benefits from an action *described in a sentence*. Exactly
**one** rule anywhere references it (`actor_goals.json::mint_actor_goal_recipient`), and it mints a
goal recipient from that role. Nothing represents whose manifold a *deformation* serves.

So the axis the paper puts the entire ethical load on has, in this substrate, no representation. Not
a weak one — none.

## Why this matters more than it looks: recourse ≠ beneficiary

The natural move is to suppose `aperture_frame`'s modes already encode it — that *forced* is the
manipulative case and *negotiated* the legitimate one. **They are orthogonal, and conflating them
would be a real error:**

| | serves the observer | serves the imposer |
|---|---|---|
| **forced** | a clinician limiting a patient's exposure | coercion |
| **negotiated** | genuine common ground | a pact that harms both parties equally |
| **chosen** | attention | `APERTURE_PATHOLOGIES.md` §1's motivated inattention — self-serving, self-imposed |

The bottom-right cell is already measured: §1's motivated inattention is an agent **choosing** the
frames under which it is never wrong. Freely chosen, and serving the chooser at the cost of its own
accuracy. Consent does not make it benign, which is the paper's point arriving from the other
direction.

## Consequence, stated as a gap rather than a plan

For the social direction this is the binding limitation. The substrate can currently represent
*that* one frame deforms another and *who may lift it*, and cannot represent *whom the deformation
serves*. Every pathology in `APERTURE_PATHOLOGIES.md` is therefore describable and none is
**judgeable** — which is the correct state for a mechanism paper and the wrong one for a social
simulation that wants to model exploitation as distinct from teaching.

Naming what it would take, without building it: a represented beneficiary on the deformation itself,
not on the sentence describing it — and, per the paper, a second field for what the deformation
*presents* itself as serving, since manipulation is precisely the divergence between the two. One
field cannot express it; the mismatch is the phenomenon.

## Also aligned, and already built: decode-or-mint

> *"Borrow from a source the reader has read and the name is a **decode against a held codebook** —
> recognition… Borrow from a source the reader has not read and the name is a **mint**."*

This is `ShapeDecode` / `sd_mint_quantum` applied to the papers' own naming, and it is the same pair
the tree runs on the sd loop's four-rung ladder. Worth recording as convergence rather than
influence: the reach argument reaches for the substrate's own operation to reason about the
substrate's reception, and the operation was already there to be reached for.
