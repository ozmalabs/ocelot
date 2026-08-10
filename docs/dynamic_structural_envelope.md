# Dynamic structural-envelope inference

Design records and material libraries remain the best source of structural
limits, but they are priors. Payload, fuel, damage, temperature, repairs, and
load-path changes make the usable envelope dynamic.

`embodied_structural_limits` now accepts verified receipts containing current
effective mass (or support force and gravity), applied load, normalized strain,
and residual strain. The graph maintains, independently for every structural
load dimension:

- current and best-observed stiffness;
- stiffness ratio, which derates a specified envelope when the body softens;
- the largest load observed to recover elastically, a lower bound rather than
  a claim about ultimate strength;
- the smallest load associated with residual deformation, an upper bound on
  the elastic region;
- evidence count and confidence; and
- current mass, baseline mass, payload delta, and weight.

This is deliberately non-destructive identification. Elastic observations may
expand the demonstrated operating region. Plastic response tightens the bound
and triggers the existing capacity/damage machinery. When trusted specifications
exist they retain priority, but observed stiffness loss dynamically derates
them. Without specifications, inferred limits remain confidence- and
safety-factor-derated.

Structural capacity is not a binary fault flag. It is a changing constraint and
cost dimension that can participate in a first-class Pareto profile alongside
task effect, energy, time, precision, and wear.
