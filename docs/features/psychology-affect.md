# Psychology / affect

A graph-native emotion, mood, and developmental-psychology architecture:
core affect (blocks 196000–204000 of the burned-seed ledger), mood as a
slower momentum layer over it, attachment/developmental experiments (Harlow,
the marshmallow delay-of-gratification test), a grounding-failure model of
psychosis, and clinical-adjacent modeling (seizures) held to the same
skeptical standard as everything else.

## The standing discipline: situate, don't overclaim

The load-bearing methodological point, stated directly in the framework's
own literature review: **every one of the seven load-bearing affect ideas
this project uses is canonical, well-supported affective/decision science**
— emotions as evolved value-regulators, emotion as the enabler of decision
(not its enemy), eudaimonia vs. hedonia, self-transcendence, multi-level
selection, learning-progress curiosity, and a state/mechanism-based
psychiatric taxonomy. Two have near-exact architectural precedents in prior
AI work. **The project is re-deriving known affective science on a new
substrate, not discovering it** — the honestly-bounded contribution is the
mechanistic, graph-native, knob-turnable instantiation, plus a couple of
clean unifying framings. The same posture applies to
`docs/research/engine_substrate/COGNITION_IS_PHYSICS_LITERATURE.md`, a
companion document holding the project's broader "cognition is physics, in
a different frame" thesis to the same standard.

## Mood as a two-layer control problem

A representative design move (`MOOD_MOMENTUM_SCOPING.md`): the naive framing
"add mood to the emotion core" smuggles a premise — that mood is one thing,
either a running average or a slow set-point. The literature-grounded
answer is that it's neither alone: mood is a **momentum + set-point** layer
that sits slower than the fast affect core it modulates, not a replacement
for it. This is one instance of a repeated pattern across the psychology
threads: an intuitive one-node addition gets checked against the actual
science before being built, and is usually replaced by a small structural
correction (two coupled layers, not one new scalar) rather than a bigger
mechanism.

## Developmental and grounding-failure threads

- **Harlow / attachment** and **the marshmallow test** — classic
  developmental-psychology paradigms rebuilt as graph experiments, testing
  whether the agent's affect/goal machinery reproduces the qualitative
  finding (not fitting a curve to a number).
- **Developmental safety ontology** and **the developmental-emotion line**
  (the source of the "frustrated/angry snapping" work, an explosive-episode
  model after Ross Greene's "kids do well if they can") — building up
  emotional regulation capability in a staged, developmentally-ordered way,
  the same discipline the speech/audio arc follows.
- **Psychosis as a grounding failure mode** and **narcissism as a
  thermodynamic/basin-energy model** — both held to the seizure-model
  discipline: a unification earns its keep by compression (MDL), not by
  claiming a novel mechanism, and both got an honest comparative-literature
  pass asking "does our demo add anything beyond restating known science
  mechanistically."
- **Seizure modeling** — the most clinically-adjacent thread, treated with
  the same register: "skeptical reviewer, not advocate."

## Where the code lives

- Seeds: `seeds/core_emotions.json` and the affect/mood/developmental seed
  family it anchors.
- Gates: `tests/test_core_emotions_migrated.py`,
  `tests/test_mood_r1*_migrated.py`, `tests/test_harlow*_migrated.py`,
  `tests/test_arousal_wot_migrated.py`, and neighbors.

## For the full history

`docs/research/psychology_affect/` holds the `SEIZURE_*`, `MOOD_*`,
`MODULATORS_*`, `GROUNDING_*`, `HARLOW_*`, `MARSHMALLOW_*`, `AROUSAL_*`,
`WINDOW_KNOB_*`, `SNAP_*`, `PSYCHOSIS_*`, `DEVELOPMENTAL_*`, and
`EMOTION_FRAMEWORK_LITERATURE.md` documents. See that folder's `INDEX.md`.
