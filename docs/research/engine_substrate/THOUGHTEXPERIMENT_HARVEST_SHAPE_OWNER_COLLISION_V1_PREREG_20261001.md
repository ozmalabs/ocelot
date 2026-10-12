# Harvest-shape owner-collision exposure v1 preregistration

**Question.** Does the current full-seed `harvest_shapes()` result select any concept name whose `_owning_mt_map()` attribution is ambiguous across distinct Microtheories?

## Method and gates

In three fresh workers, full-boot the seed corpus using the standard adapter/loader. Group `has_concept`/`has_rule` ownership edges by target node name and identify names with more than one distinct source Microtheory. Run `domains.implication_harvester.harvest_shapes()` once on that booted graph. Report every shape's kind/source name/source Microtheory, then the intersection between selected shape source names and ambiguous names, including all candidate owner IDs/names. Require distinct PIDs, stable source/seed fingerprints, deterministic shape signatures and ambiguity intersection, and report all seed load failures.

## Interpretation limits

This is a current-corpus exposure check. A nonempty intersection shows that an ambiguity-sensitive owner lookup supplies metadata to a currently selected shape; it does not yet prove receipt adoption changes the full shape result. An empty intersection means this helper's current chosen donors avoid these collisions, not that future or task-generated donor selections will. The panel collects no timing evidence.
