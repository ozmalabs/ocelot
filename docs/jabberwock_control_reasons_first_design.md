# The jabberwock's design — a control is "a button that does stuff": reason FIRST from grounded priors

Creator's steer (2026-06-26), deepening the control generalisation: "a control is a button that does stuff. its
function is implied by its location and/or shape/colour/label/design, which helps to build a POSIT about what it
does. the actual function can be learned by teaching (high weight depending on source) or observation (higher
weight). it should ALREADY KNOW this or ground it trivially from the wikipedia teacher on disk. it should also
support other types of controls (rotary switches, mice, joysticks, ...). it is an entity that REASONS FIRST and
acts from priors, NOT a brute-force game-playing machine."

VERIFIED the priors are already grounded — the on-disk Wikipedia teacher returns, at zero API cost:
Push-button "a switch mechanism to control some aspect of a machine"; Joystick "an input device ... reports its
angle"; Game controller "an input device used with video games"; Rotary switch "operated by rotation ... when
more than 2 positions are needed"; Switch "connect/disconnect a path". The KINDS of controls and what they do
are grounded knowledge.

The jabberwock's design (the old press-and-fit learner is demoted to ONE channel; everything else is wired or
grounded):

## 1. Control kind -> a function-space prior (grounded, not brute-forced)
A `Control` is a first-class node the moment perception finds an interactive entity. Its KIND is recovered by
`categorise_by_shape` over appearance (aspect ratio, circular-with-detent vs stick-on-pivot vs labelled-rectangle
vs slider-track), and `wiki_teacher` is consulted FIRST to bind it: Push-button / Joystick / Rotary switch /
Lever / Dial. Each gloss is parsed into a `ControlKind` node carrying `effect_family` + arity — button -> discrete
act (2-state); joystick -> continuous direction (2-DoF angle); rotary -> discrete mode-select (N>2); lever ->
1-DoF range; mouse -> relative pointer. The kind pins the OperationPrimitive family before anything is touched.

## 2. POSIT function FIRST from cues (inference_first), before pressing
Within the family, cues specialise the posit: `read_label` projects "ROTATE"/"FIRE"/"OPEN" through
`learned_lexicon` onto a verb -> OperationPrimitive (label = strongest cue); `shape_sense` + `colour_meaning`
add priors (red -> destructive/stop, green -> go/confirm, arrow-glyph -> directional change_location); spatial
convention adds role (bottom-centre d-pad -> navigation, corner -> meta/menu). Each cue emits a
`FunctionPosit{control, primitive, params, value, confidence, source}`; a BIND rule mints these as Frame
expectations -> a believed function with a Beta BEFORE any press.

## 3. CONFIRM by evidence, weighted (reconcile by value, confidence, SOURCE)
appearance-prior posits enter at LOW weight; `teach` updates scale by `agent_source_vocabulary` source-trust (a
creator-teaching beats a wiki gloss); OBSERVATION — the old "fit the effect" learner, now demoted to the
OBSERVATION CHANNEL — enters at the HIGHEST weight, so a single watched effect overrides label+colour+wiki when
they disagree. Beta accumulates per `(control, primitive)`; `beta_evidence_threshold` decides when it's settled.
Ordering: observation > teaching > appearance-prior.

## 4. REASON FIRST, not brute-force
`select_operator` reads the settled posit and acts on frame 1 (rotate-button -> emit
`transform_attribute(rotate)`; joystick -> descend the nav gradient as continuous change_location). Brute-force
pressing is GATED to fire ONLY where confidence is under threshold OR two cue-channels conflict — exploration
becomes targeted disambiguation, not a sweep. (This is the difference between an entity that reasons and a
game-playing machine.)

## 5. Uniform coverage
Tetris ROTATE button = button + label "ROTATE" -> transform_attribute(rotate), confirmed by watching the piece
turn. Joystick = kind -> continuous-direction prior, no label needed; the old learned displacement-vector becomes
the observation REFINEMENT of an already-correct posit (navigation works before calibration completes). Adventure
verb ("OPEN"/"TAKE") = button + label -> signal/select on the referent — same posit->confirm path, lexicon
lifting.

## Wired vs new + bench order
- WIRED: wiki grounding, label/shape/colour reading, spatial convention, Beta + source-weighting, reconcile,
  OperationPrimitives + select_operator, the old fit-the-effect learner (re-pointed as the observation channel).
- GENUINELY NEW: a `ControlKind` prior table (graph DATA, authored once by grounding the wiki glosses — a seed,
  not code), a small set of cue->posit RULES (label / colour / shape / spatial, each emitting a FunctionPosit),
  and the BIND wiring that mints posits as expectations. NO new Rust primitive (enact / select_operator /
  reconcile already exist).
- BENCH ORDER: (1) ground the kinds; assert each ControlKind carries the right effect_family (donkey=0, wiki-
  only); (2) POSIT — a red labelled "ROTATE" button yields the rotate posit with NO press; (3) CONFIRM weighting
  — a wrong label is overridden by ONE observed frame; (4) REASON-FIRST — presses-to-correct-action drops to ~1
  vs the press-everything baseline's N; (5) UNIFORMITY — same pipeline green on Tetris-rotate, joystick-nav, and
  an adventure verb in one harness.
