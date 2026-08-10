# PREREG — block 326000: episodic memory with appraisal, decay, reconsolidation (C3)

`BIGVILLE_COGNITIVE_CAPABILITIES_PLAN.md` C3. Events become **appraised, decaying
memories** that drive mood and re-appraise on recall. Grounded in Tulving (episodic
memory — a contextual + emotional trace of a particular event), OCC/appraisal theory
(emotion = appraisal of an event against the agent's goals), ACT-R base-level activation
(memory strength decays with time, boosts on retrieval), and memory reconsolidation (a
recalled trace is re-encoded, possibly altered).

## The mechanism (`bigville_memory.json`)

- **`mem_appraise`** — an agent that perceives an `Event{topic, valence}` mints an
  `EpisodicTrace{appraisal, activation:1}`. The **appraisal is goal-relative (OCC)**:
  `valence · relevance`, where relevance is high if the event's topic is what the agent
  **cares about**, low otherwise. Two agents with different concerns appraise the *same*
  event differently.
- **`mem_decay`** — on each metabolic-pulse epoch, a trace's `activation` decays
  geometrically (`activation · retention`), once per epoch (an ACT-R base-level proxy).
- **`mem_recall`** — recalling a trace **boosts its activation** and **re-appraises it**
  (reconsolidation): `appraisal ← appraisal·(1−r) + context_target·r` — the memory is
  re-encoded toward the emotional context of the recall.
- **`mem_mood`** — the agent's **mood = the appraisal of its most active trace** (an Argmax
  over its own traces by activation), or neutral if none is above threshold. Mood tracks
  what is currently *salient*, not merely the latest event.

## Gates (pass/fail, pre-registered) — signatures, not tuned numbers

1. **G-forgetting-curve (HEADLINE):** a fresh trace's activation **decays monotonically**
   across pulses; **recall reboosts** it (the ACT-R rise-and-decay signature).
2. **G-mood-from-active-traces (HEADLINE):** mood equals the dominant *active* trace's
   appraisal; when that trace decays below threshold, mood returns toward neutral, and a
   newer salient trace takes over mood — mood is not just "the last event."
3. **G-appraisal-is-goal-relative (OCC):** the same event yields a **stronger** appraisal
   in an agent who cares about its topic than in one who does not.
4. **G-reconsolidation-changes-the-trace:** recalling a trace in a new context **changes its
   stored appraisal** — the memory is not immutable.
5. **G-no-decay-collapses-it (falsifier):** with `retention = 1` (no decay) an ancient
   trace stays fully active and dominates mood forever — the forgetting signature is gone.
6. **G-no-python-decision (source audit):** appraise/decay/recall/mood are the seed rules;
   mood is an Argmax collapse in the seed; the adapter presents events, pulses time
   (a world-fact metabolic epoch), arms recall, and reads.

## Scope / honesty
- Appraisal/activation/mood are the agent's **own held state**; the metabolic-pulse epoch
  is a world-fact (time passes for a body). Mood = the dominant active trace's appraisal is
  a salience proxy for a weighted sum over active traces (the DSL has no sum-over-node-set);
  a true aggregate is a later refinement, as with C1's arousal.
- Decay applies once per epoch and does not compound missed epochs (single-pulse steps in
  the demonstrator); a continuous power-law is a refinement.
- OCC here is the goal-congruence × relevance core; the full OCC branching (praise/blame,
  prospect-based) is deferred. Disposition drift from repeated re-appraisal (facets change
  with memory) is noted for a follow-on.
- Isolated demonstrator (`self_load_only`); no Rust; `.so` untouched (`a8a9012c`).
