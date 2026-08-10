# iter-21 — JABBERWOCK acquires the missing `re_represent` shape itself

The deepest autopoietic close attempted: **diagnose → acquire → harvest → derive.**
The agent diagnoses a breadth gap in its OWN shape-library (iter-20), ACQUIRES the
matching general domain from its world, runs its OWN harvester over the enriched
breadth, and re-runs iter-19's perceptual derivation to see whether the newly
acquired shape lets it derive a relational representation it could not derive before.

Reproduce:
- `python scripts/jabberwock_breadth_audit.py`        (Step 1, the diagnosis)
- `python scripts/jabberwock_perceptual_shape.py`     (iter-19 baseline)
- `python scripts/jabberwock_acquires_shape.py`       (Steps 4–6, this iteration)

NO-DONKEY: the only authored thing is the mechanical I/O that translates general
encyclopedia knowledge into the agent's node format (`domains/invariant_representation.py`,
the same boundary `install_mathematics_seed` performs). The `re_represent` shape and
the derivation are the agent's OWN harvester / synthesize_gaps output, reported
verbatim below.

---

## (1) The agent's `re_represent` gloss (Step 1, verbatim from the breadth-audit)

The breadth-audit classified the agent's 181 harvested shapes by structural ROLE.
Verbatim:

```
  shapes harvested: 181   unclassified: 164

    [preserve] cancel         =    6 shapes
    [preserve] separate       =    4 shapes
    [preserve] partition      =    6 shapes
    [preserve] parameterize   =    2 shapes
    [preserve] forward_invert =    1 shapes
    [change  ] re_represent   =    0 shapes   <<< EMPTY (breadth gap)
                 (describe the object by the RELATIONS among its parts — a
                  configuration / structure / graph, an invariant-by-construction
                  representation, not its absolute values)

  side totals:
    preserve   = 19
    change     = 0   <<< ENTIRE SIDE EMPTY

  >>> EMPTY ROLES (breadth gaps): ['re_represent']
  >>> EMPTY SIDES               : ['change']
```

Frame-convergence over the perceptual frame (verbatim):

```
  frame: surface_feature_representation_frame
    gaps surfaced        : 4
    distinct sides       : 1  (['preserve'])
    >>> BREADTH-LIMITED: all gaps converge on side 'preserve' — the complementary
        side is UNREACHABLE with the current library.
```

The agent's statement of the missing shape-KIND (the gloss above) is what selects
the acquisition: **describe the object by the RELATIONS among its parts — a
configuration / structure / graph, an invariant-by-construction representation, not
its absolute values.**

---

## (2) The acquired domain + ingested concepts (general, cited)

The gloss selects the general mathematical theory of characterising an object by the
invariant relations among its parts: **invariant theory** and **Klein's Erlangen
program**. Fetched authoritative, general sources:

- Erlangen program — https://en.wikipedia.org/wiki/Erlangen_program — "a method of
  characterizing geometries based on group theory"; a geometry is the study of the
  properties of figures INVARIANT under a transformation group; "lengths, angles and
  areas are preserved with respect to the Euclidean group ... while only the
  incidence structure and the cross-ratio are preserved under the most general
  projective transformations."
- Invariant theory — https://en.wikipedia.org/wiki/Invariant_theory — studies
  "polynomial functions that do not change (are invariant) under the transformations
  from a given linear group"; the invariants characterise the object independent of
  its coordinate representation.

Ingested as a new Microtheory `invariant_representation`
(`domains/invariant_representation.py`), in the agent's exact seed format
(`name`/`definition`/`why`/`origin` Concepts under the Mt via `has_concept`; Rules
with `if_clauses`/`then_clauses`/`why`/`origin` via `has_rule` — identical to
`install_mathematics_seed`):

- Concept `erlangen_program` — geometry characterised by a transformation group;
  properties invariant under the group.
- Concept `invariant_under_a_group` — a quantity unchanged under the group action;
  invariants characterise the object independent of its coordinate system.
- Concept `cross_ratio_relation` — the canonical projective invariant; a relation
  among four points preserved under transformation though each absolute position
  changes.
- Concept `structural_relational_description` — represent an object by the relations
  among its parts (relative arrangement / configuration / incidence structure),
  invariant under the global transformations that change every part's absolute
  coordinates.
- Rule `characterize_by_invariant_relations_among_parts` — if object instances are
  related by a transformation group that shifts and scales the absolute coordinates
  of every part, **then** represent the object by the invariant relations among its
  parts (its relative arrangement / configuration / structure), preserved under the
  group and invariant by construction, rather than by the parts' absolute coordinate
  values.

All four concepts + the rule are general invariant theory in the source's own terms.
None is a speech/audio shape; none names the perceptual frame ("speech", "speaker",
"formant", "gammatone" do not appear).

---

## (3) The harvested shape (Step 4, VERBATIM — the agent's harvester output)

The agent's own implication-harvester (`harvest_shapes_combined`, via the rule-walker
`harvest_shapes_from_rules`) ran over the enriched breadth and abstracted a shape
that the breadth-audit classifies as `re_represent` (side = change). Verbatim:

```
  shapes harvested: 182

  RE_REPRESENT SHAPE (verbatim, the agent's harvest):
    name        : rule_derived__characterize_by_invariant_relations_among_parts
    kind        : rule_derived
    domain      : invariant_representation
    match_mode  : all
    consequence : represent the object by the invariant RELATIONS among its parts
                  — its relative arrangement / configuration / structure — which is
                  preserved under the transformation group and is invariant by
                  construction, rather than by the parts' absolute coordinate values
    match_keys  : ['object', 'instances', 'related', 'transformation', 'group',
                   'shifts', 'scales', 'absolute']
    name_keys   : ['represent', 'object', 'invariant', 'relations', 'among',
                   'parts', 'relative', 'arrangement']
    match_patterns: ['\bobject\b', '\binstances\b', '\brelated\b',
                     '\btransformation\b', '\bgroup\b', '\bshifts\b',
                     '\bscales\b', '\babsolute\b']
```

**Yes** — the agent's harvester abstracted a change-side shape from the general
domain. The consequence is the Rule's `then`-clause verbatim; the `match_keys` /
`match_patterns` are the content words of the Rule's antecedent, extracted by the
rule-walker (`_keywords_from_clause`). I did not author the shape; the rule-walker
produced it from the ingested general rule.

---

## (4) Breadth-audit re_represent now non-empty? (Step 5, verbatim)

```
    [preserve] cancel         =    6 shapes
    [preserve] separate       =    4 shapes
    [preserve] partition      =    7 shapes
    [preserve] parameterize   =    2 shapes
    [preserve] forward_invert =    1 shapes
    [change  ] re_represent   =    1 shapes

  side totals: {'preserve': 20, 'change': 1}
  empty roles: []
  empty sides: []
```

**Yes.** `re_represent` = 1 shape; the previously-empty `change` side is populated;
`empty_roles` and `empty_sides` are both now `[]`. The breadth gap the agent
diagnosed in iter-20 is closed. (`partition` also rose 6→7 — the rule-walker
additionally harvested a shape from `cross_ratio_relation`'s incidence/configuration
text, but the load-bearing change here is the change side going non-empty.)

---

## (5) THE TEST (Step 6, VERBATIM): does synthesize_gaps now derive a relational representation?

`synthesize_gaps` over the SAME honest `surface_feature_representation_frame` (the
iter-19 frame, unchanged), harvested shapes, max_order=3:

**WITHOUT acquired domain (iter-19 baseline) — 4 gaps, all preserve-side:**
```
    [partition] transitional probability / word-scale chunking / statistical segmentation
    [cancel   ] speaker normalization / formant ratio / vocal-tract-length normalization / f2/f1
    [cancel   ] coarticulation predict-remove / context normalization / carryover removal
    [partition] unsupervised-clustering / cross-speaker-clustering / cross-speaker
  >>> change-side (re_represent) gaps surfaced: 0
```

**WITH acquired domain — 4 gaps, IDENTICAL, all preserve-side:**
```
    [partition] transitional probability / word-scale chunking / statistical segmentation
    [cancel   ] speaker normalization / formant ratio / vocal-tract-length normalization / f2/f1
    [cancel   ] coarticulation predict-remove / context normalization / carryover removal
    [partition] unsupervised-clustering / cross-speaker-clustering / cross-speaker
  >>> change-side (re_represent) gaps surfaced: 0
```

**No.** The acquired `re_represent` shape exists in the library and closes the
breadth gap, but `synthesize_gaps` does NOT fire it on the perceptual frame. The
output is byte-identical to iter-19's normalizations-only result.

### Why — the honest derivation/transfer limit

The rule-derived shape carries `match_mode='all'` (the iter-19 "specificity at
birth" fix: a rule-derived shape fires only when its WHOLE structural antecedent
co-occurs in a postulate, so a single shared word like 'substrate' cannot fire it
promiscuously — see `differentiate()` line ~318 and the `harvest_shapes_from_rules`
docstring). Checking the shape's 8 antecedent anchors against the honest frame text:

```
  MISS   object          FIRES  instances
  MISS   related         FIRES  shifts
  MISS   transformation  FIRES  scales
  MISS   group
  MISS   absolute
```

Only 3 of 8 fire. The honest perceptual frame describes the SYMPTOM ("a change of
talker SHIFTS and SCALES the measured feature values ... CONFUSES instances") but
not the ABSTRACT transformation-group structure ("object / related / transformation
/ group / absolute"). Because the shape requires all 8, it correctly does not fire.

This limit is real and not patchable without a donkey move: making the shape fire
would require either (a) loosening the rule-walker's `match_mode='all'` (authoring a
weaker, promiscuous shape — the exact thing the iter-19 fix prevents) or (b)
rewriting the perceptual frame to seed the answer words (seeding the answer). Both
are forbidden by the experiment.

What is genuinely missing for the close to complete at the DERIVATION step: the
transfer measure between a postulate and a change-side shape is still lexical
(`match_mode='all'` over the antecedent's content words). A change-side shape
abstracts a STRUCTURAL kind ("instances related by a nuisance transformation of
their coordinates"), and the perceptual frame IS an instance of that kind — but the
two state it in different surface vocabulary, so the lexical-conjunction matcher
cannot bridge them. The Shape-lifted path (`match_mode='shape'`,
`shapes_compatible`) is the structural-not-lexical matcher already in the codebase,
but it requires both the shape AND the postulate to have registered Term-trees; the
prose perceptual frame has none. Bridging this needs the change-side shape and the
frame expressed as Term-trees so structural compatibility (not word overlap) decides
the transfer — that is the next iteration's work, not authorable here.

---

## (6) VERDICT

**Partial — the loop closes through HARVEST, not yet through DERIVE.**

- diagnose ✓ — the agent surfaced the empty `re_represent` / change side itself
  (iter-20), mechanically, with no answer fed.
- acquire ✓ — the gloss selected invariant theory / the Erlangen program; the
  general domain was ingested in the agent's own seed format (cited, general, not
  speech).
- harvest ✓ — the agent's OWN rule-walker abstracted a change-side `re_represent`
  shape from that general breadth; the breadth-audit confirms `re_represent` is now
  non-empty and NO role/side is empty. The breadth gap the agent diagnosed is
  closed by acquisition, mechanically, end-to-end.
- derive ✗ — `synthesize_gaps` over the honest perceptual frame still surfaces only
  the preserve-side normalizations (output identical to iter-19). The acquired shape
  does not transfer onto the frame because the rule-derived transfer test is a
  lexical conjunction (`match_mode='all'`) over the shape's antecedent, and the
  honest frame states the symptom in different words than the shape's
  transformation-group antecedent.

So: jabberwock **self-acquired the missing shape** (the deepest part — it diagnosed
its own breadth gap and filled it from its world via its own harvester) but did **not
yet derive the perceptual representation** it could not derive in iter-19. The
blocker is no longer breadth (the change side is populated) but TRANSFER: the
lexical-conjunction matcher cannot bridge a change-side shape's abstract
transformation-group antecedent to the frame's symptom-level prose. The
structural-not-lexical bridge (Term-tree Shape compatibility) already exists in the
codebase but needs both shape and frame as Term-trees — the next iteration's work.

Tests green: `test_stt_pipeline`, `test_perception_self_assessment`,
`test_process_meta_assessor`, `test_gap_guidance` — 32 passed.

Artifacts left in the working tree (not committed):
- `domains/invariant_representation.py` — the ingested general domain (world-adapter I/O)
- `scripts/jabberwock_acquires_shape.py` — Steps 4–6 runner
- this doc
