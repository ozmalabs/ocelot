# Compensation rule-order and simultaneous-transition probe v1

## Question

Do explicit positive/negative compensation rules converge to the same state under reversed insertion order when one frame changes positive→negative while another changes negative→positive in one closure pass?

## Design

- Three independent fresh workers; each runs four fresh cells: `compensating_attr` and `retractable_edge`, each with `positive_first` and `compensator_first` rule insertion order.
- Each cell contains three independent matched frames with resource revisions `r0=0`, `r1=1`, `r2=0`. The file-backed `UseTool` callback reads the revision named by graph state and logs frame/revision/value.
- Positive effects are either `set_attr_if_different(accepted,1)` or add an `accepted` edge. Negative compensation effects are either `set_attr_if_different(accepted,0)` or delete that edge.
- Phase A settles all-negative r0. Phase B changes frame 0 to r1 and settles, establishing a positive prior result. Phase C updates frame 0 to r2 and frame 1 to r1 before one closure call: one prior positive becomes negative while another frame becomes positive simultaneously; frame 2 remains negative.
- Record phase progress, callback events, final per-frame revision/marker projection, rule order, and source/native fingerprints.

## Gates

All 3 workers complete all 4 cells with identical locked inputs. Phase B must make frame 0 positive only. Phase C must yield frame 0 negative, frame 1 positive, frame 2 negative. Within each effect representation, final projections must match across the two rule insertion orders and across all workers. This directly tests the compensation rules; it does not assume the engine automatically undoes effects.

## Limits

Three frames, one shared match pattern, one callback and two rules per cell. No rule-order claim extends to arbitrary overlapping effects, stateful callbacks, concurrency, or automatic truth maintenance. Callback counts describe work but are not a complexity bound.
