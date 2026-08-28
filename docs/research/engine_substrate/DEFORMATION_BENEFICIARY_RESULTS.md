# Whose manifold does this deformation serve — built, in the order the correction demanded

`COMMUNICATION_DEFORMATION_ALIGNMENT.md` closed on a gap and a corrected prerequisite: the substrate
confirms the papers' structural claim (communication and manipulation are one operation, no second
primitive) and cannot represent the axis the ethics sits on — and the obvious fix was wrong, because
**forced deformation is the ordinary container relation and most of it has no author.** Gravity
serves nobody, and a field that must be filled for gravity gets filled with noise.

So: the goal-bearing test first, the two fields only where it passes.
`seeds/deformation_beneficiary.json` v1.0.0, four rules, all mutation-gated.

## 1. The goal-bearing test

A frame bears goals iff it holds a **tube** — `future_manifold_target` plus bounds, a represented
preference over its own continuations. Structural, not a whitelist of goal-shaped node types: it is
the same field the manifold audit reads and `feasible_selection` breaks ties on. Gravity holds no
tube.

Where the origin is not goal-bearing, the seed records that it **declined to ask** — the beneficiary
fields stay absent rather than being filled with a `None` a later reader could mistake for "nobody,
measured". That distinction is the whole reason for the ordering.

## 2. The two fields — and only one of them is declared

* `presents_as` — what the deformation **claims** to serve. Supplied.
* `serves_actor` / `serves_origin` — whom it **actually** serves. Not declared: **measured**, by
  auditing the deformed continuation against each frame's own tube. *A deformation serves whoever's
  tube it keeps you inside.* No new notion of benefit, and nothing the author can assert.

| origin | continuation | presents_as | goal_bearing | well-formed | serves_actor | serves_origin | diverges |
|---|---|---|---|---|---|---|---|
| gravity (no tube) | either | acted_on | 0 | **0** | **absent** | **absent** | **absent** |
| author | toward reader | acted_on | 1 | 1 | **1** | 0 | 0 |
| author | toward author | acted_on | 1 | 1 | 0 | **1** | **1** |
| author | toward author | **origin** | 1 | 1 | 0 | **1** | **absent** |

**Rows 3 and 4 are the point.** Identical deformation, identical measured service — it serves the
origin either way. They differ only in what is claimed, and only the mismatched one flags. Truth buys
no exemption at the content level because the divergence is *between* claim and service, not inside
either; and an honestly-declared self-serving deformation is not flagged, because there is no
misrepresentation to find. One field could not express this.

## 3. Without a future manifold you cannot know, because you cannot see where you are going

This is not a remark about the build — it is what the build measures, and it is the sharpest result
here.

`serves_*` is computed **by** `FutureManifoldProjection`. Remove the manifold and the field is not
weakly determined, it is **uncomputable**: whom a deformation serves is a fact about where a
continuation *takes* you, and there is no present-state answer to it. An agent without a future
manifold is therefore not bad at detecting manipulation. It is structurally unable to pose the
question.

One deformation, audited from different horizons. It sits in the reader's own tube for three ticks
and delivers them to the author's by the eighth:

| horizon | 2 | 3 | **4** | 6 | 8 |
|---|---|---|---|---|---|
| `serves_actor` | **1** | **1** | **0** | 0 | 0 |
| reads as | serving me | serving me | **not serving me** | not serving me | not serving me |

**Whether a deformation "serves me" is not a property of the deformation.** It is a property of how
far the observer can see. Capture is indistinguishable from help at a short enough horizon — not
because the observer is careless, but because the discriminating evidence lies past its horizon.

### And this closes a loop with the aperture arc

`AROUSAL_HORIZON_RESULTS.md` derived the planning horizon from the window of tolerance: a narrower
window yields a shorter horizon. Composed with the table above, **stress makes an agent manipulable
structurally** — not by making it gullible or credulous, but by shortening the horizon over which
service is measurable at all. The dysregulated agent is not failing to check. It is checking
correctly over a range too short to contain the answer.

That is a prediction the two seeds make jointly and which has **not** been run as one composed
experiment; each half is measured separately here and in the horizon results.

## 4. Three ways to be moved, and the horizon defends against one

The instrument above measures a **continuation** against a **tube**. Two consequences follow that it
cannot see, and they are the more common cases.

| | what is deformed | detectable by | measured |
|---|---|---|---|
| **A** | the continuation — you are taken where your tube excludes | **a long enough horizon** | 1,1 → 0,0,0 as horizon grows |
| **B** | **the tube** — what you are aiming at is replaced | **not by any horizon** | `serves_actor = 1` at 2, 4, 6, 8 |
| **C** | (B, audited against the tube held *before*) | **retained history** | `0` at every horizon |

**B is invisible by construction, not by oversight.** An audit measures a continuation against a
tube; move the tube and the measure moves with it. More foresight does not touch it. An agent so
moved is not mistaken — by its own current lights it is correct, and it is selecting exactly what it
now aims at.

**And no actor is required for the harm.** Row A at short horizon is already a decision against one's
own interest with nobody arranging it: the capture reads as help because the discriminating evidence
lies past the horizon, and a *forced* deformation — the authorless container relation — takes you out
of your tube just as effectively as an authored one. The beneficiary question is malformed there
(§1), which does not make the outcome any less against your interest. **Self-harming choice needs no
manipulator; it needs only a horizon shorter than the consequence.**

Where an actor *is* present, this says something sharper about why the target so often cannot report
it. Deforming the content is detectable at the content level. Deforming the continuation is
detectable with enough horizon. **Deforming the aim, or the admissibility grammar that decides which
options are even proposed, leaves nothing to detect in the present** — the selector runs correctly on
altered inputs, and `feasible_selection`'s own `withheld_minimal` is empty in that case, because an
option removed from admissibility was never a candidate to withhold. Unawareness is then the expected
state rather than a failure of attention.

**What defends against it is memory, not foresight.** Row C recovers the move only because the prior
tube was retained to compare against. That is the theory's own retention — *"what is free is only the
not-yet-forgetting"* — and it gives the forgetting a specific cost: discard your own prior aim and
you lose the only instrument that detects having been re-aimed.

**Not built.** Nothing in this seed retains a prior tube or watches the admissibility grammar for
change; row C is produced by handing the audit the old target by hand. A `prior_target` with a rule
that flags divergence between held and prior aim is the obvious shape, and the harder half —
detecting a change in Γ itself — is not obviously the same shape and is not attempted here.

## 5. The drain has no bound, because the stopping condition is what was removed

The halt in this substrate **is** the residual: a residual opens a concern, and a concern is what
makes an agent re-examine. Control the tube and no residual is produced, at any displacement.

Twelve rounds, each step dragging the agent further from its original aim:

| | round 1 | 2 | 4 | 12 | halted |
|---|---|---|---|---|---|
| **aim fixed** | serves me | **not serving me** | not | not | **round 2** |
| **aim tracks the position** | serves me | serves me | serves me | serves me | **never** — drift 7.2 and rising |

Gated out to displacement **5000** with the same verdict. **This is not a large bound; it is the
absence of one.** Nothing in the loop is a function of the drift, because tolerance is measured
relative to the aim and the aim moves with the position, so measured error is structurally zero
however far the agent has been taken. The halt was not overcome — it was removed, and the agent
continues to select correctly by its own current lights the entire time.

Same for the admissibility route, and more quietly: an option removed from Γ is never proposed, so it
never appears as withheld (`feasible_selection`'s `withheld_minimal` is empty), and there is no trace
of the alternative that would have served them.

### Detection is not defence

Worth keeping separate, because the fixed-aim arm makes it plain: that agent **knows** it is not
being served from round 2 onward, and is still displaced by 7.2 at round 12. The residual buys the
*possibility* of correction — a concern to act on — not correction. Knowing does not stop the drag;
it only makes the drag reportable.

### What is and is not claimed here

The measured quantities are the verdict and the displacement. **Narrativium proper was not
measured** — `counting_narrativium_by_dimension` was not run, and no measure over reachable
deformation is computed in this fixture. What is shown is narrower and sufficient for the mechanism:
each round is a realised expenditure, no internal signal terminates the sequence, and the agent's own
audit certifies every step. Whether the expenditure is *unbounded* in the narrativium sense is a
stronger claim than this fixture supports, and the reason to expect it is structural rather than
measured — there is no term in the loop that grows with the drift.

## Honest bounds

* **The horizon buys the negative, not the beneficiary.** `serves_origin` stays 0 at every horizon in
  the capture fixture, because retention is all-or-nothing over the audited range and the capture
  spends its early ticks outside the author's tube too. Seeing further tells the reader *this is not
  serving me*; identifying *whom* it serves needs an audit over the segment where that frame
  benefits, which this does not do. Gated as a limitation rather than left to be discovered.
* **This computes a comparison, not a verdict.** A clinician's frame and a con artist's can both land
  in the diverging cell. The rule is named for what it measures (`claim_diverges`), and the substrate
  is not the thing that tells them apart.
* One dimension, four-to-eight tick horizons, hand-built tubes, deterministic. The goal-bearing test
  is sound for frames that use the manifold contract and says nothing about frames that represent
  preference some other way — of which this tree has several.

Gates: `tests/test_deformation_beneficiary_migrated.py` 7/7; all four rules mutation-tested, every
drop failing at least two tests.
