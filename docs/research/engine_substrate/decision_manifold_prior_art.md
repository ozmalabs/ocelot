# Decision manifolds and recovery — what extant systems actually do

**Status: RESEARCH NOTE. No code, no runs.**  Prompted by the owner after the
containment work stalled: *"the problem is that we are trying to be precise.
What we need to do is guess.  Not randomly."*  Written from knowledge and
**not re-verified against primary sources**; every citation is marked, and
confidence is separated from consensus.  Where this note is wrong it should be
corrected against the sources, not against its own plausibility.

---

## 1. The manifold has a standard name and a standard construction

**Control allocation** (Durham, *Constrained Control Allocation*, J. Guidance
Control & Dynamics, 1993; Bodson, 2002; Johansen & Fossen survey, Automatica
2013 — `[unverified]` on years) solves exactly the problem this line has been
circling: given a DESIRED generalised force/moment and a set of effectors with
LIMITS, find the effector settings that produce it.

Its central object is the **attainable moment set (AMS)**: the image of the
effector box (each effector between its limits) under the control-effectiveness
matrix `B`.  It is a convex polytope in moment space.

**This IS "the manifold of possibilities", constructed rather than sampled.**
What this line built axis-by-axis — reach per objective, sections 41-43 — is
the AMS projected onto one coordinate at a time.  The standard object is the
SET, and the standard question is *is the desired moment inside it*, which is
containment stated once rather than three times.

**What that buys, and it is the thing sections 38-40 wanted:** the goal is a
point in moment space, the AMS is the manifold, and "goal outside manifold" is
a single geometric test rather than a per-axis conjunction.

## 2. After damage, real systems RE-IDENTIFY, they do not ATTRIBUTE

Reconfigurable / self-repairing flight control (NASA IFCS, the various
self-repairing-flight-control programmes; Ward & Barron; Boskovic & Mehra —
`[unverified]`) handles effector failure by **re-estimating `B` online** and
re-allocating.  The allocator then uses whatever authority remains, without
anyone deciding which surface broke.

**This independently confirms the hardest-won finding of this session.**  Six
instruments failed to attribute a residual to an effector (§15-29), and the
retraction concluded attribution was neither recoverable nor necessary.  The
deployed practice agrees: identify the MAP, not the culprit.  Attribution is
for the accident investigation.

## 3. Recovery is a LIBRARY OF COARSE MANEUVERS WITH KNOWN BASINS

**LQR-trees and funnel libraries** (Tedrake et al., *LQR-Trees*, IJRR 2010;
Majumdar & Tedrake on funnel libraries, IJRR 2017 — `[unverified]` on years)
precompute a set of maneuvers, each with a conservative inner estimate of its
region of attraction — its "funnel".  At runtime you do not optimise; you find
a funnel that CONTAINS your current state and execute that maneuver.

**That is the corner set done right, and the difference is exactly the one this
line keeps failing on.**  The corners here are scored against each other on six
axes by Pareto dominance.  A funnel library selects by CONTAINMENT — is my
state in this maneuver's basin — which needs no comparison between maneuvers at
all, and degrades to "no funnel contains me" rather than to a false winner.

Consensus that funnels work; contested how well they scale to high dimensions.

## 4. The strongest precedent for "guess, not randomly": Auto-GCAS

The F-16 **Automatic Ground Collision Avoidance System** (deployed 2014,
credited with multiple saves — `[unverified]` on count) is worth studying
closely because it is deliberately, aggressively imprecise:

* it predicts the trajectory with a SIMPLIFIED model, not the true dynamics;
* it compares that prediction against a coarse terrain profile;
* when they intersect it fires ONE canned recovery — roll wings level, 5g pull;
* and its entire design goal is **timeliness with nuisance-free operation**,
  not accuracy.

It does not identify what went wrong, does not choose among options, and does
not model the pilot.  It answers one question — *am I about to hit the ground
if I keep doing this* — and has one answer.

**The lesson for this line is uncomfortable and direct.**  Blocks A-Q have
pursued: the right fault taxonomy, the right per-axis pricing, the right
attribution, the right trigger.  Auto-GCAS has none of those and works.  Its
precision budget is spent entirely on WHEN, and none on WHAT.

## 5. Envelope estimation — the closest match to what was half-built here

Adaptive flight-envelope estimation after damage (Tang, Atkins & Kumar;
NASA/Michigan work on maneuvering-envelope estimation — `[unverified]`)
computes a REDUCED safe envelope online from the damaged model and then
constrains guidance to stay inside it.  Two layers, cleanly separated:

* an ENVELOPE that shrinks when the aircraft is damaged (physics, no
  preference);
* a GUIDANCE layer that plans within it (preference, no physics).

That is precisely the manifold/goal split of §38-40, in a deployed lineage, and
it is evidence the split is right even though this line's implementation of it
failed three times.

## 6. What to take, concretely

1. **Build the AMS, not per-axis reach.**  One convex set in moment space;
   containment is one test.  A coarse polytope or even a box is standard
   practice — the literature's own approximations are crude on purpose.
2. **Select recoveries by CONTAINMENT, not by scoring.**  A corner is eligible
   if the state is in its basin.  Drop the six-axis Pareto comparison, which
   has produced a constant winner under four different pricings (§27).
3. **Spend the precision budget on TIMING.**  Auto-GCAS is the proof that a
   coarse answer delivered in time beats a precise one delivered late, and the
   trigger is the half this line has never got working.
4. **Re-identify the map after damage; never attribute.**  Already the measured
   conclusion here, and it is also the deployed practice.
5. **Accept conservative inner approximations.**  Funnels are deliberately
   under-estimates.  This line has instead sought exact per-axis reach and
   spent three sections on unit errors in it (§41-43).

## 7. Honest limits of this note

Every reference is from memory and **none was re-verified**; years, venues and
attributions should be checked before any of it is cited as fact.  The
strongest claims here are structural (control allocation's AMS; funnel
selection by containment; Auto-GCAS's design philosophy) and I would expect
those to survive checking.  The weakest are the specific programme names and
dates.

None of this is evidence about THIS plant.  It is a map of what has worked
elsewhere, offered because the owner asked for inspiration rather than for
another measurement — and it should be treated as a source of hypotheses to
prereg, not as a result.

---

## 8. CORRECTION — the lesson is not "be coarse", it is "our library is DYNAMIC"

Owner: *"Our problem is not precise and late - we can get that.  We also have a
huge and rich set of data and inferred axes.  Our library is the same - it's
just that we have a dynamic library, and we can combine and infer moves where
they don't exist."*

**Section 4 drew the wrong lesson from Auto-GCAS.**  Auto-GCAS is coarse
because it is a FIXED-FUNCTION safety net with exactly one move: coarseness is
forced on it by having nothing to compose from.  Precision is not this system's
binding constraint — it has the data and it has the axes — so prescribing
coarseness here would discard its only structural advantage.

**The funnel-library analogy holds, and the difference is the whole point.**
LQR-trees and funnel libraries are PRECOMPUTED: a fixed set of maneuvers with
fixed basins, and at runtime you look one up.  This system's library can
**grow, transform and compose**, and every mechanism for that is already built
and tested on other domains:

| funnel library | here | already built as |
|---|---|---|
| look up a maneuver whose basin contains the state | recognise | `sd_recognize` |
| — (not available) | the same move shifted along a dimension | `TransformDecode` / `sd_transform_decode` |
| — (not available) | a move implied by a residual coupled across dims | `DimInfer` / `sd_infer_dimension` |
| — (not available) | mint a genuinely new move | `sd_mint_quantum` |
| hand-authored library | compose a move from effector primitives | `MotorCompose` |

**And this exposes the real defect, which is not scoring and not triggering.**
`MotorCompose` generates motor programs.  The sd loop grows a shape codebook,
mints dimensions, and re-decodes under codebook growth.  `space_quantize`
refines quanta per dimension.  Every representation in this tree is generated —
**except the corners, which are five literal Python functions with hardcoded
`keeps=(...)` tuples.**

That is why every attempt to fix the frontier has failed in the same shape.
Four pricings each produced a constant winner (§27); the option set does not
respond to the model (§32); containment bounding a FIXED menu just filtered it
down to the most-surrendering member (block Q).  **A fixed library cannot be
repaired by a better selection rule.**  The corner set is the last
hand-authored representation in a system whose entire thesis is that
representations are grown.

## 9. What that makes the actual next rung

Not a better trigger, not a better price, not a containment bound on five
literals.  **Corners generated the way programs and shapes already are:**

* a corner IS a composed motor program plus a declared objective set, and
  `MotorCompose` already builds the first half from effector primitives;
* the objective half is what the containment reading bounds — which objectives
  are still reachable is exactly what should be handed to a generator, rather
  than used to veto a fixed list;
* growth follows the sd loop's own Occam ladder — recognise an existing corner,
  else transform one along a dimension, else infer one from a coupled residual,
  else mint;
* and selection is by CONTAINMENT (§3), not by dominance, so a grown library
  needs no cross-corner comparison and degrades to "nothing covers this" rather
  than to a false winner.

The measured facts that support this are already in hand: the sd loop mints
exactly one quantum per fault episode and recognises the repeats (§17); the
difference shape detects a moved plant at ~90x (§28); containment reads
correctly on the axes whose units are right (§43).  What has never been tried
is letting those three drive a GENERATOR instead of a filter.
