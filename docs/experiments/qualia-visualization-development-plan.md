# Qualia visualization experiment — development plan

## Aim

Extend the initial aperture probe so it tests a reconstruction sequence from an
object cue through episode retrieval to an internal visual scene. The main
question is whether visual feature access changes with observer aperture while
the object concept and semantic knowledge stay available.

## Plan

1. **Separate cue, memory, and image.** Keep the `apple` concept sparse. Store
   arbitrary episode-specific visual details on a separate visual-memory node
   associated with that cue. The projector must read the memory through the
   existing `concept_signature` and observer-aperture mechanism.
2. **Make reconstruction observable.** Record an imagined-scene node and an
   ordered series of feature states (hue, stem orientation, bite location,
   lighting, contour). Keep the source memory distinct from the generated trace.
3. **Compare matched conditions.** Include direct perception, full-resolution
   visualization, coarse visualization, absent visualization, and a semantic
   control. Every condition retains the same apple concept. The absent and
   semantic conditions can still report the category, but have no visual
   feature coordinates to place in an imagined scene.
4. **Measure detail recovery and coverage separately.** Score feature accuracy
   only where a condition emits a feature value; also report how many of the
   arbitrary episode details it emits. This distinguishes a coarse but
   informative image from no visual output.
5. **Run the fixed exploratory battery.** Use the same eight predeclared
   episode codes as the initial probe so the next result can be compared
   directly. Save the per-episode traces and aggregate scores in JSON.
6. **State the evidence boundary.** This run tests graph-resident memory
   retrieval, aperture filtering, and scene-trace construction. It does not
   establish subjective imagery, and the scene-building transition remains
   adapter-driven rather than a graph-authored recurrent cognitive rule.

## Predictions

- Perception and full visualization recover all stored episode details.
- Coarse visualization emits fewer feature coordinates; values that remain
  available are correct at the represented resolution.
- Absent visualization and the semantic control emit no episode-specific
  visual features, while retaining access to the apple category.
- If the absent condition emits visual details, inspect for leakage from the
  memory or from nonvisual attributes before interpreting the result.

## Execution record

The original probe violated step 1: its apple `Concept` carried both the cue
and all target details. The revised run will move those details to a separate
`VisualMemory` node and link the cue to that memory. This is an exploratory
development run, not a preregistered confirmatory study.

### Run 1 — memory separated from cue

Executed with `python3 -m domains.qualia_visualization_world`. The cue is an
apple/fruit concept with no episode-specific visual fields; each randomized
episode is a separate `VisualMemory` linked from the cue. The runner projects
the memory through each Observer and writes a scene plus five ordered feature
states for every episode/condition.

| Condition | Correct details | Available details | Coverage |
|---|---:|---:|---:|
| Perception | 40/40 | 40/40 | 100% |
| Full imagery | 40/40 | 40/40 | 100% |
| Coarse imagery | 6/40 | 6/40 | 15% |
| Imagery absent | 0/40 | 0/40 | 0% |
| Semantic control | 0/40 | 0/40 | 0% |

Every available detail was correct. The category remained known in all eight
episodes for all conditions. The graph held 8 memory nodes, 40 imagined-scene
nodes, and 200 ordered feature-state nodes. With quantum 2, only the six
episode values whose coordinate was nonzero after coarse quantization remained
available; the other values collapsed to the omitted zero coordinate.

This repairs cue/memory leakage and makes the projected scene trace inspectable.
The traces are still emitted by the Python world adapter after it reads
`concept_signature`; they do not yet demonstrate that a graph-authored
recurrent rule can construct the scene. The probe also measures retrieval from
an encoded episode, rather than invention of details from a generic apple
concept. That remains the next development step.
