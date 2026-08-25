# Minting at aperture — the correction, and what it requires

## The correction

I argued that a projected (low-aperture) decode must not MINT, because "an observer minting from
what it cannot resolve is inventing detail". That was wrong, and it conflated two different things.

**Minting from an unresolved residual is the only thing a limited observer can do.** Thunder is
observed; its cause is below aperture; so you mint a generator for it and call it a god. That is the
sd loop running correctly at low resolution — and it is productive, not defective: the storm god is
an honest entity *at that aperture*, and it later REFINES into meteorology rather than being deleted.
Refusing to mint what you cannot resolve is not rigour, it is paralysis. No social being works that
way, because other minds are permanently below aperture — theory of mind IS minting a model of
something you cannot directly observe.

What I was actually objecting to is different, and the distinction is what the mint CLAIMS:

| grain | residual is | mint asserts | verdict |
|---|---|---|---|
| observation | EVIDENCE the world supplied | *"something causes this; call it X"* — a revisable hypothesis | **correct, necessary** |
| target | a DEMAND nobody supplied | *"I have this capability"* | wishful thinking (`theory_residual_concern`) |

"Thor causes thunder" does not change what you can attempt. "I have radar because I need radar"
does. Same operation, different claim.

## What that requires, and what is missing

If coarse mints are legitimate, then a coarse mint must be **distinguishable from a fine one** —
otherwise refinement is impossible to express and testimony is impossible to weigh.

Measured across the tree: **182 mint sites, and not one records the resolution it was minted at.**

| resolution-ish attribute | sites |
|---|---|
| `epoch` | 16 |
| `confidence` | 8 |
| `dim_types` | 1 |
| `depth` | 1 |
| **aperture / resolution / grain** | **0** |

`sd_mint_quantum` itself records `capability_keys`, `closest_held_shape`, `from_observation`,
`induced`, `is_axis`, `residual_predicates`, `source` — good provenance, no resolution.

Three consequences follow, and the third is why this blocks the social build:

1. **Refinement cannot be expressed as refinement.** A finer observation of the same thing can only
   contradict the coarse entry or duplicate it. "The storm god" → "a pressure gradient" has no
   representation as *the same entity at a finer aperture*, which is what it actually is.
2. **A held entity cannot say why it is coarse** — whether it is coarse because that is all the
   observer could resolve, or fine because that is genuinely all there is.
3. **Testimony carries no resolution.** If A tells B something A minted at low aperture, B has no way
   to know it is coarse. In a social simulation that is how a coarse guess launders into a fine fact
   as it passes between agents, with nothing anywhere recording that it happened.

## The build

**Mints carry the aperture they were minted at.** Then:

* refinement becomes a TRANSFORM along the aperture axis — which is `CLAUDE.md`'s own INTENSIVE
  direction (*"refinement / depth — betweenness; its unreachable limit is the continuum"*), the axis
  it already names as orthogonal to the extensive frontier. Minting at low aperture and refining
  later is movement along it, not a contradiction to be resolved;
* a projected decode MAY mint, freely, and what it mints inherits the observer's aperture — which is
  already the right number, because `THEORY_AS_SHAPE_RESULTS.md` measured that a shape's generality
  equals the spread of what it was minted from. Here it is additionally bounded by what the observer
  could resolve at all: **you cannot mint finer than your grain**;
* and testimony can be weighed, because a received entity states the resolution it was formed at.

The aperture value is already computable with no new Rust — the projection composes from `MapList` /
`ZipWith` / `In` / `IfThenElse` over the `dim_types` vocabulary that real codebooks already populate
(`val` 789, `pred` 263, `idx` 263 across the corpus).

**Not yet built.** This records the correction and the measurement. What it does not do is add the
attribute, decide where it is written (the mint rules are 182 sites, so a shared idiom matters more
than any one of them), or test that a refinement transform actually composes along it.
