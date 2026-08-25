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

## Honest bounds

Every number above is from this tree, mostly on small hand-made fixtures. The aperture axis was
measured on six variants of one shape; range on three codebooks and two targets; the claim/grain
distinction is a design argument supported by one seed and its mutation test, not a result. None of
this shows the loop is sufficient for anything, only that these five parameters are real here,
independent, and account for more phenomena together than any of them does alone.
