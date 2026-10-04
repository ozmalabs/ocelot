# Mary’s Room with the eye and qualia system — bounded analogue (PREREGISTRATION)

## Question and scope

Given an explicit physical theory of a fixed chromatic patch, can the theory
predict the opponent coordinates that the eye computes when the patch is
released? Does the eye then mint a color category whose coordinates appear in a
qualia-space signature?

This is a runnable system analogue of Mary’s epistemic transition. It tests
physical prediction and sensory-grounded representation in the implementation.
It cannot establish phenomenal experience, and a new graph coordinate by itself
is not evidence for metaphysical qualia.

## Existing machinery

- `domains/colour_identity_world.py` supplies cone-response cells mechanically.
- `seeds/vision_colour_identity.json` computes integer opponent coordinates,
  mints repeated color values as categories, and assigns category signs.
- `domains/analogy_search.py::concept_signature` reads a graph node’s attributes
  into the shared signature space. For a `ColourCategory`, this exposes its
  `crg` and `cby` as `attr:` coordinates. This is a descriptive readout; the
  color category is not itself evidence of experience.
- `seeds/qualia_space.json` supplies the declared dimension schema.

The theory baseline is the known cone response plus the opponent equations
`crg = cL-cM`, `cby = cS-(cL+cM)`. It is computed without making any eye/region
nodes. This is an explicit physical-theory baseline, not a claim that the
substrate independently derived the equations.

## Fixed stimuli

- Chromatic release: 12 repeated cells at `(cL,cM,cS) = (15,5,20)`, predicting
  opponent value `(10,0)`.
- Achromatic floor: 12 repeated cells at `(10,10,20)`, opponent value `(0,0)`.

No parameters are swept. No stochastic seeds are used.

## Arms

Each arm gets a fresh substrate with the color-identity and qualia-space seeds.

1. **Before release:** no visual region/cell is installed. Record zero categories
   and the physical-theory prediction `(10,0)`.
2. **After release:** deliver the chromatic stimulus through the color identity
   rules with identity enabled. Record each region’s computed opponent value,
   minted categories, and `concept_signature` for each category.
3. **Achromatic floor:** deliver the achromatic stimulus with identity enabled.
   It may mint a neutral `(0,0)` category, but it must not produce a chromatic
   coordinate.
4. **Achromatopsia control:** deliver the chromatic stimulus with identity
   enabled and the graph-resident achromatopsia flag enabled. The opponent signal
   should remain computed while category minting is suppressed.

## Decision rule

Pass only if all hold:

- Before release there are no eye regions or color categories.
- The chromatic arm computes `(10,0)` for all 12 cells and mints exactly one
  category at `(10,0)`.
- The independent physical-theory prediction exactly matches that eye output.
- The post-release category has a nonempty shared-space signature.
- The achromatic arm computes/mints only neutral `(0,0)`.
- The achromatopsia arm computes `(10,0)` for all 12 cells and mints no category.

Report all raw coordinates, category attrs, signatures, and engine provenance.
A failure of any condition is a negative result for this bounded analogue.

## Interpretation boundary

A pass shows that the eye’s computed chromatic representation is predictable from
the declared physical equations and is exposed through the shared signature
reader after sensory input. It does not show that the physical theory lacks
information about the sensory state, and it does not resolve Mary’s Room as a
philosophical argument.

## Run discipline

The engine provenance check must pass before measurement. This preregistration
must be committed before the confirmatory invocation. Record the complete runner
output and the engine identity with the results.
