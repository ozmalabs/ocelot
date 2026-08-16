# ToM meta-shape: attributed mental state — PREREG

**Task**: user, "unify the tom system" → after the retirement/naming rung
landed, user selected the largest of three options for the deferred
third piece: **live recognize/decode convergence**, not a static label.
This document registers the exact design, verified against the real,
already-landed sd-loop infrastructure before writing predictions —
following this arc's own "measure before finalizing" discipline.

## 0. What this is not, corrected mid-investigation

An earlier probe misdiagnosed `msg_recognize_prior`'s behavior as an
engine-level type-coercion bug (a synthetic test value,
`"mindcontent_controllability"`, was swallowed into an EXISTING
meta-shape, `feedback_control`). Direct verification found the real
cause: the value contains the substring `"control"`, which genuinely
matches an existing `ShapePrinciple` ("regulate", keywords include
`'control'`) — `RecogniseShape`'s own documented behavior
(`domains/teach.py`'s `categorise_by_shape`, the reference caller: "a
collection takes the structural path, where a keyword matching a
relation PREDICATE outranks any amount of prose evidence"). This was
CORRECT, working recognition, not a bug — the test vocabulary was
accidentally colliding with real English, not the infrastructure
misbehaving. Retracted before it went further; no engine code needs
fixing. This section stands so the retraction is on the record, not
silently dropped.

## 1. Theoretical grounding

- **Person Identity Nodes (Bruce & Young 1986)**: perceptual front-ends
  (face/voice recognition) feed an abstract, amodal hub where everything
  else attaches — name, biography, trait impressions, relationship
  history, and mentalizing content (what you believe someone believes or
  wants). Mentalizing is differentiated from other person-node content by
  CONTENT TYPE, not by a separate STRUCTURE — the same content-typed-
  attachment shape `bigville_theory_of_mind.py`'s own `<aspect>_for:
  <target>` convention already uses.
- **The structural claim this rung tests**: `character_tom.py`'s nested
  belief-world (a narrative reader modeling a STORY CHARACTER's belief)
  and bigville's `controllability_for:<target>` (a resident modeling
  ANOTHER RESIDENT's agency) are DIFFERENT implementations — different
  node types, zero shared attribute keys, confirmed by direct
  investigation before this rung began — but the SAME abstract relation:
  a mental state attributed to a mind other than the reasoner's own. The
  claim under test is whether the substrate's OWN shape-matcher
  (`meta_shape_growth.json`'s sd-loop ladder,
  `META_SHAPE_FIRST_CLASS_RESULTS.md`'s already-landed infrastructure)
  can discover and recognize that kinship from real instance data, with
  ZERO new Rust and ZERO new rules — the exact test CLAUDE.md's own
  "SHAPES, NOT NUMBERS" section calls the strongest form of evidence: a
  capability landing in one body, independently re-derived in another.

## 2. Design

**Reuses 100% of already-landed infrastructure** (confirmed by direct
investigation, not assumed): `domains/meta_shape.py`'s `observe(agent,
type_, attrs)` — mechanical ingest, zero decisions — and
`seeds/meta_shape_growth.json`'s already-tested 11-rule ladder
(`msg_decode → msg_recognize/msg_transform_decode/msg_infer_dimension →
msg_recognize_prior → msg_residual → msg_mint_shape → msg_redecode`).
Zero new Rust, zero new seed rules.

**Two small, mechanical translator functions** (`domains/
tom_meta_shape.py`, new) project each domain's REAL data into a shared
relation vocabulary — the ONLY new code this rung adds:

```
attributed_mental_state_signature(attributor, target, content_kind) -> dict
    {"attributor": attributor, "target": target, "content_kind": content_kind}

character_tom_mental_state_signature(belief_holder, flavor)
    = attributed_mental_state_signature("reader", belief_holder, flavor)
    -- belief_holder/flavor are character_tom.py's OWN real attrs
       (_nested_entity's belief_holder, flavor fields)

resident_tom_mental_state_signature(target, aspect)
    = attributed_mental_state_signature("resident", target, aspect)
    -- target/aspect mirror bigville_theory_of_mind.mint_resident_tom_
       belief's own (aspect, target) parameters
```

`meta_shape.observe(agent, "AttributedMentalState", signature)` writes
the `ShapeObservation` and hands off to the existing rule ladder — no new
call pattern, the SAME one `teach()` already uses for arbitrary items.

**Verified live before registering** (this arc's own discipline): a
character_tom-shaped observation (`attributor="reader", target="sally",
content_kind="belief"`) submitted to a fresh agent lands `residual` (no
existing MetaShape covers it). A bigville-shaped observation
(`attributor="resident", target="alex", content_kind="agency_
attribution"`) submitted SECOND, to the SAME agent, mints exactly ONE new
MetaShape (`support=2`, name `ms_attributor_content_kind_is_a_target`,
signature `is_a=attributedmentalstate` FIXED, `attributor`/`target`/
`content_kind` WILDCARDED) — and is itself immediately recognized under
it. The FIRST (character_tom-shaped) observation is THEN re-recognized
under the SAME new MetaShape by `msg_redecode`'s re-arm.

## 3. Predictions

1. **A character_tom-shaped observation, submitted alone, lands
   `residual`** — no pre-existing MetaShape covers "attributed mental
   state" content.
2. **A bigville-shaped observation, submitted second on the same agent,
   mints exactly ONE new MetaShape** whose generalized signature fixes
   the shared `is_a` predicate and wildcards `attributor`/`target`/
   `content_kind` (the predicates that genuinely differ per domain) — and
   is itself recognized under it immediately.
3. **The first (character_tom-shaped) observation is retroactively
   recognized under the SAME newly-minted MetaShape** — the two
   independent embodiments converge on one shape neither singly implied.
4. **An unrelated observation (no shared `is_a=attributedmentalstate`
   predicate) is NOT pulled into the new MetaShape** — stays `residual`,
   confirming the mint is specific, not a catch-all.
5. **Reproducible**: submitting the same two signatures to a FRESH agent
   mints the SAME MetaShape name deterministically (mechanically derived
   from the sorted predicate list, not randomized).

## 4. Scope boundaries

- Does not wire this into `hate_attribution.py`'s or `character_tom.py`'s
  own runtime flow — this is an EXPLICIT registration action (matching
  `teach()`'s own explicit-invocation precedent), not something that
  fires automatically on every belief update. Auto-wiring is a real,
  separate, deferred follow-on.
- Does not attempt to register EVERY target-scoped Concept
  (`regard_for`/`desire_for`/etc.) under this meta-shape — only
  `controllability_for`, per `bigville_theory_of_mind.py`'s own already-
  drawn distinction (ToM belief vs. the resident's own affect).
- The vocabulary choice (`attributor`/`target`/`content_kind`) is a
  design decision, not independently derived — chosen to be genuinely
  shared across both domains' real semantics while avoiding accidental
  collision with `shape_vocabulary.json`'s existing keyword lists
  (checked directly, not assumed — the Sec0 retraction is exactly this
  check catching a real collision on the first vocabulary choice).
