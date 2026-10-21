# Cognition aperture adapter contract v1

An Observer aperture is a typed view over an observer-owned source epoch. Adapters retain source references and never rewrite source evidence. Chosen frames may guide a funded probe; forced frames are constraints and cannot be relaxed. Every temporary frame/probe lease records its prior value and restores it on approval denial, success, timeout, cancellation, or epoch invalidation. Unknown value-of-information is unresolved, not positive evidence.

| Adapter | Source representation | Typed dimension | Owner and units | Direction and invalidation |
|---|---|---|---|---|
| Reading | `reading` plus verifier provenance | `observer:reading` | observer; exact candidate key | source → frame; invalidate on reading/verifier epoch |
| Dwell | `dwell`/tick budget | `observer:dwell` | observer; integer ticks | source → frame; invalidate on budget epoch |
| Finite-difference order | numeric Shape order `k` | `observer:difference_order` | observer and source Shape; integer order | source → frame; invalidate on Shape source epoch |
| Qualia aperture | typed `QualiaDimension` projection | `observer:qualia:<dimension>` | observer; source dimension's declared quantum | reversible projection; invalidate on qualia source epoch |
| ShapeDecode scope | codebook/source scope | `observer:decode_scope` | observer and codebook owner; stable key | source → frame; invalidate on codebook epoch |
| Manifold mask | future-manifold retained/lost/escape fields | `observer:manifold_mask` | observer and manifold owner; explicit cell mask | source → frame; invalidate on manifold version |

Frame identity includes observer, frame key, source epoch and the selected adapter dimensions. Missing values remain missing; no adapter fills them from a sibling observer. Projection of evidence and held hypotheses uses the same frame function. Physiological floors and host-forced limits remain hard constraints even if a selected frame would otherwise narrow or widen the view.

The `cognition_aperture` seed projects six explicit `CognitionApertureSource` adapter IDs to these dimension identities (QualiaAperture retains its source dimension suffix). A source linked to its concrete Observer can activate the P4 probe gate only when its owner matches that Observer and its authority is chosen. The legacy `aperture_frame` behavior is unchanged when the P4 funding flag is absent; under the flag, projection and verdict require a funding authorization whose epoch still matches the Observer's linked network mode.

Questioning accepts only a chosen frame whose linked source says `voi_status=positive` and carries a nonmissing `voi_evidence_id`, plus an available budget request and matching source epoch. Unknown VOI keeps the Observer guarded and produces no request. Each authorized probe has one request and one shared-budget debit. To avoid concurrent requests racing the budget matcher, at most one P4 aperture probe request is admitted per network-mode epoch; competing observers keep independent frame and source state, and the unselected request is denied for that epoch. Budget denial and stale epochs produce no probe. A terminal keep/drop verdict clears the temporary funded flag; a complete-view diagnostic is evaluation-only and cannot be passed back into the agent's decision graph.
