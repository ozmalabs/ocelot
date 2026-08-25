# One loop, many grains — what a session of measurement suggests

Not a theory of intelligence. A set of things measured in this tree over one session, which turn out
to be the same operation with different parameters, and which between them account for perception,
theory-formation, aspiration, superstition and wishful thinking.

## The loop

    decode against what you hold  ->  residual  ->  mint  ->  re-decode

Five parameters, every one of them measured here rather than posited:

| parameter | what it is | measured |
|---|---|---|
| **residual** | what your model does not cover | everywhere; `ShapeDecode`'s own output field |
| **aperture** | the resolution you see at | a smooth axis 0.00 → 1.00, one sixth per differing leaf, set by the SPREAD of what you generalised over |
| **range** | what you hold | agent-relative and binding: the same target reads 0.33 to one codebook and 0.00 to another |
| **claim** | what the mint asserts | explanation vs aspiration vs capability — different licences |
| **check** | evidence, afterwards | present or absent; its absence is the pathology |

## The same operation at two grains

| grain | the residual is | the mint yields | unchecked, it becomes |
|---|---|---|---|
| observation | EVIDENCE the world supplied | an explanation — *"something causes this, call it X"* | superstition |
| target | a DEMAND nobody supplied | an aspiration — *"I will have this"* | wishful thinking |

Both mints are legitimate. Thunder is observed, its cause is below aperture, so you mint a generator
and call it a god — and that entity is honest *at that aperture*, later refining into meteorology
rather than being deleted. Equally, "I will have radar" is a posit that drives the work of getting
it; self-efficacy is causally productive, and an agent that refuses to hold what it cannot yet do
attempts nothing.

**So wishful thinking is not a separate faculty. It is this loop with the check missing.** That is
not an analogy — it is what the mutation test showed: adding the wishful mint back to
`theory_residual_concern` turned the same seed into a wishful-thinking agent, and the only thing
distinguishing them was whether the mint had to be evidenced. Pathology as a missing check rather
than a different mechanism is a much cheaper theory, and it is the one the code supports.

## Which reframes what was built

`seeds/theory_residual_concern.json` was described as PREVENTING wishful thinking. That was the wrong
label. It **represents** it: a `SelfConcern{capability_gap}` is a wishful thought held honestly —
*"I want this and do not have it"* — carrying its own status, and revisable.

And it is load-bearing rather than filed and forgotten. Measured: **19 seeds mint concerns, 7 read
them**, `cognitive_scheduler` with 4 rules, `conversation_steering` with 3, plus `residual_promote`,
`arc_goals` and `program_synthesis`. The aspiration drives scheduling and steering. The loop from
*want* to *attempt* to *evidence* is already closed here.

## The one thing missing, and why it is the same thing

A coarse mint and a fine one are currently indistinguishable: **182 mint sites, none recording the
resolution they were minted at** (`epoch` 16, `confidence` 8, `dim_types` 1, `depth` 1, aperture 0).

That single gap breaks all three of the above at once:

* an explanation cannot be REFINED, only contradicted — "storm god" → "pressure gradient" has no
  representation as the same entity at finer aperture;
* an aspiration cannot say how vaguely it was conceived;
* and testimony carries no resolution, so in a social simulation **a coarse guess launders into a
  fine fact** as it passes between agents, with nothing recording that it happened.

`CLAUDE.md` already names the axis this belongs on — the INTENSIVE direction, *"refinement / depth —
betweenness; its unreachable limit is the continuum"*, explicitly orthogonal to the extensive
frontier. Minting coarse and refining later is movement along it. Nothing currently moves along it
because nothing records where it started.

## A third outcome: the check that PASSES on bad grounding

The two-grain table above is incomplete. *"I can predict the weather from tea leaves"* is neither an
explanation nor an aspiration — it is a **capability claim that got GROUNDED**. The check ran and
passed, on bad evidence. So a check is not binary; it returns false positives, and what governs that
is confidence, self-rating and understanding.

Those turn out to be aperture. **Spurious grounding is coverage that holds at your resolution and
not at a finer one.** Measured — same architecture, same want, same held parts, differing only in
what the observer resolves:

| observer | barometer | tea_leaves |
|---|---|---|
| meteorologist (resolves the read-object) | grounds | covered 1 — **does not ground** |
| mystic (cannot resolve WHAT is read) | grounds | covered 2 — **GROUNDS** |

The mystic is not lying and not wishing. At that aperture a barometer and tea leaves are genuinely
indistinguishable — both read something and yield a forecast — so the grounding is VALID AT THAT
RESOLUTION. Telling the mystic to check harder is incoherent: not resolving it is what aperture
means.

So the completed table is:

| grain | residual | mint | failure mode |
|---|---|---|---|
| observation | evidence | explanation | superstition — **no check** |
| target | demand | aspiration | wishful thinking — **no check** |
| target | demand | **capability** | spurious grounding — **check PASSES, at too coarse an aperture** |

The third is the dangerous one, because it is indistinguishable from success from the inside.

## Aperture is a SHAPE, not a scalar

This section previously treated aperture as a fraction (0.00 → 1.00). That is wrong, and the tea-leaf
experiment failed once before it was corrected: a UNIFORM aperture measures nothing, because what an
observer resolves is not uniform. A doctor resolves anatomy finely and engines coarsely. What you
can resolve is itself STRUCTURED — a function over the shape space, which is to say a shape, and
therefore decodable, holdable, mintable and learned by the same loop as everything else.

The consequence is not cosmetic. **A scalar acuity totally orders observers; a shaped aperture does
not.** Modelled as `predicate -> resolved slots`:

| pair | A ⊒ B | B ⊒ A | relation |
|---|---|---|---|
| meteorologist vs mystic | False | False | **INCOMPARABLE** |
| meteorologist vs novice | True | False | A strictly finer |
| mystic vs novice | True | False | A strictly finer |

### "Incomparable" was the wrong verdict — they compare by SHAPE MATCH, and the residual is the point

The subsumption table above collapses a shape to a boolean, which is the exact move this entire
document argues against, made one paragraph after arguing it. Two apertures are not incomparable.
They are compared the same way as everything else: **decode one against the other and read the
residual.**

| A (the goal) | B (held) | covered | residual — what A resolves that B cannot |
|---|---|---|---|
| meteorologist | mystic | 3 | `[["resolves","reads","object"]]` |
| meteorologist | novice | 2 | `[["resolves","reads","object"], ["resolves","yields","object"]]` |
| mystic | meteorologist | 3 | `[["resolves","feels","object"]]` |
| mystic | novice | 2 | `[["resolves","yields","object"], ["resolves","feels","object"]]` |
| novice | meteorologist | 2 | **`[]`** |
| novice | mystic | 2 | **`[]`** |

Three things follow.

**Subsumption is the DEGENERATE case, not the alternative.** The novice's residual against both
others is empty — that is what "strictly below" means, read off the same operation. The boolean test
was never a different comparison, only an impoverished reading of this one.

**The pair that does not rank still yields a residual each way**, and each names the blind spot
exactly: the mystic cannot resolve WHAT is read, the meteorologist cannot resolve what is FELT.
Nothing is lost by refusing to rank them; the informative answer was underneath the verdict the whole
time.

**And the meteorologist-against-mystic residual IS the tea-leaf failure.** It is literally
`resolves(reads, object)` — precisely the distinction whose absence let the mystic ground weather
prediction on tea leaves. So comparing two apertures **predicts where the other agent will ground
falsely, in advance and specifically.** For a social simulation that is the difference between
modelling disagreement and merely permitting it: you can compute what another mind will get wrong,
and what you would have to teach it. **The residual IS the curriculum.**

## KNOWING THAT, WITHOUT KNOWING WHAT — a blind spot's existence is detectable even when its content is not

A probe run here concluded *"every aperture looks complete from inside"*. **That was false, and the
probe was rigged**: it modelled self-perception as an aperture intersected with itself, which returns
everything by construction. It measured its own assumption. The claim is retracted, and it is worth
retracting loudly, because the true statement is both more useful and already what the substrate
does.

**You can understand that there are things you do not understand, and accept them, without being
able to resolve them.** The two halves have different requirements:

* **resolving WHAT is missing** needs the distinction you lack — unavailable, by definition;
* **detecting THAT something is missing** needs only that your decode failed to cover — and coverage
  is a property of the decode, not of the thing you failed to decode.

That second one is exactly what a residual IS here, and it is why `unknown = absence, first-class`
is load-bearing rather than a slogan. The mechanism for honest ignorance already exists; the earlier
probe simply could not see it, having defined it away.

Measured on five weather episodes, same world, three observers:

| observer | episode-kinds told apart | failures it can OBSERVE | can it ATTRIBUTE the failure |
|---|---|---|---|
| meteorologist (resolves the read-object) | 5 of 5 | **2 of 5** | yes — `leaf 1/3 right`, `pressure 2/2 right` |
| mystic (cannot resolve WHAT is read) | 4 of 5 | **2 of 5** | **no** — one bucket, `3/5 right` |

**The mystic counts its own failures exactly as accurately as the expert.** Nothing about its
aperture prevents it noticing that its forecasts are wrong two times in five. What its aperture
prevents is saying which sign was responsible, because attribution requires the very distinction it
lacks. So `MINTING_AT_APERTURE.md`'s storm-god is not the whole picture: an agent at low aperture can
hold *"my model of thunder is incomplete"* alongside the god, and the two are not in tension.

### Three levels, and the third is the dangerous one

Detecting a residual is not free either — it requires the DISCONFIRMING SIGNAL to be above aperture,
which is a weaker requirement than resolving the residual but still a requirement. Adding a third
observer that cannot resolve the outcome-object:

| level | what it needs | observer | failures observed |
|---|---|---|---|
| **resolves** the residual | the discriminating distinction | meteorologist | 2 |
| **detects** it, cannot resolve it | the failure signal above aperture | mystic | 2 |
| **blind** — no residual exists for it | — | zealot | **0** |

The zealot does not resolve `outcome`, so prediction and result are the same thing to it and nothing
ever disagrees. **Its theory is unfalsifiable not because it is defended but because the
disconfirming signal is below its aperture.** That is a mechanically different pathology from the
mystic's, and it is the only one of the three where honest humility is unavailable rather than
merely unexercised — there is nothing to be humble about, from inside.

Which sharpens the spurious-grounding row of the table above. The mystic's tea-leaf grounding is a
check passing at too coarse an aperture, and the mystic *can* accumulate evidence against it. The
zealot's cannot be checked at all. Telling either to "check harder" is incoherent, but for different
reasons, and only one of them can be reached by supplying more episodes.

### Why this matters for the build rather than only for the account

An unresolvable-but-detected residual is a first-class, holdable thing — which is what
`SelfConcern{capability_gap}` already is. So the honest-ignorance case needs no new mechanism: it is
the same concern-opening path as `theory_residual_concern`, with the content being *"something here I
cannot decode"* rather than a named missing part. What it does need is the aperture attribute this
document already identified as missing at all 182 mint sites — because *"I could not resolve this"*
and *"there was nothing more to resolve"* are the same empty residual without it.

## Honest bounds

Every number above is from this tree, mostly on small hand-made fixtures. The aperture axis was
measured on six variants of one shape; range on three codebooks and two targets; the claim/grain
distinction is a design argument supported by one seed and its mutation test, not a result. None of
this shows the loop is sufficient for anything, only that these five parameters are real here,
independent, and account for more phenomena together than any of them does alone.

The three-level table is five episodes and three hand-specified apertures — it demonstrates that the
levels are mechanically distinct and that the middle one is reachable, not how common any of them
is. Its own predecessor was a rigged probe that survived long enough to be written down, which is the
better argument for reading every one of these tables for what it constructed rather than what it
concluded: **the self-estimate probe reported a clean result and the result was an artefact of its
own setup.** It was caught by an outside correction, not by anything internal to the measurement.
