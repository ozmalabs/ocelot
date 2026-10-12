# RatioInduce cost pilot v1.1 amendment — 2026-09-26

The initial v1 launch is retained in `substrate_ratioinduce_cost_pilot_v1_20260926.json` and failed all 11 cells. Inspection showed the harness registered an empty `ShapeSignature.signature`; `load_parts` consequently supplied no typed coordinate schema, so the direct operator correctly returned inapplicable. This was a fixture/setup failure, not evidence about operator scaling.

Before rerun, v1.1 changes the fixture codebook signature to one nonempty typed relation and keeps the same factor levels, population generator, metrics, call timing, and acceptance rules. The corrected runner is `scripts/substrate_ratioinduce_cost_pilot_v1_1.py`; its output is a new raw record and explicitly identifies this amendment. The failed v1 record is not overwritten or pooled with v1.1.
