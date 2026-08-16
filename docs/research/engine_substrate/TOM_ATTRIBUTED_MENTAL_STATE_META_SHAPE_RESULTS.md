# ToM meta-shape: attributed mental state — RESULTS

Registered design: `TOM_ATTRIBUTED_MENTAL_STATE_META_SHAPE_PREREG.md`.
**All 5 predictions confirmed.** A misdiagnosis during investigation
(reported and retracted in the PREREG's own Sec0) is not repeated here.

## 1. Live run (`scripts/tom_meta_shape_demo.py`)

```
=== Prediction 1: character_tom-shaped observation, alone -> residual ===
status=residual covered_by=None signature=[['attributor', 'reader'], ['content_kind', 'belief'], ['is_a', 'attributedmentalstate'], ['target', 'sally']]

=== Predictions 2/3: bigville observation mints one shared shape; both converge ===
bigville obs: status=recognized covered_by=ms_attributor_content_kind_is_a_target
character_tom obs, AFTER: status=recognized covered_by=ms_attributor_content_kind_is_a_target
newly-minted MetaShape(s): [{'minted': 1, 'name': 'ms_attributor_content_kind_is_a_target', 'source': 'meta_shape_growth', 'support': 2, 'signature': (('attributor', ('·?·',)), ('content_kind', ('·?·',)), ['is_a', 'attributedmentalstate'], ('target', ('·?·',)))}]

=== Prediction 4: an unrelated observation stays residual ===
status=residual covered_by=None

=== Prediction 5: reproducible on a fresh agent, different names/content ===
run 1 minted: ms_attributor_content_kind_is_a_target
run 2 minted: ms_attributor_content_kind_is_a_target
match: True
```

## 2. Predictions

1. **A character_tom-shaped observation, alone, lands `residual`** —
   `PASS`. No existing MetaShape (the 11 already seeded — `feedback_
   control`, `prediction_minus_observation`, etc.) covers "attributed
   mental state" content.
2. **The second (bigville-shaped) observation mints exactly one new
   MetaShape and is recognized under it** — `PASS`. `support=2`,
   `minted=1`, signature `is_a=attributedmentalstate` FIXED (the one
   predicate BOTH domains share literally),
   `attributor`/`target`/`content_kind` WILDCARDED (`'·?·'` — the exact
   predicates whose VALUES genuinely differ per domain: "reader"/"sally"/
   "belief" vs. "resident"/"alex"/"agency_attribution").
3. **The first (character_tom-shaped) observation is retroactively
   recognized under the SAME new MetaShape** — `PASS`. `msg_redecode`'s
   re-arm correctly re-evaluates it once the codebook grew, converging
   both domains' independent instances onto one discovered shape — the
   "capability landing in one body, independently re-derived in another"
   pattern CLAUDE.md's own SHAPES-not-numbers section calls the strongest
   form of evidence in this project.
4. **An unrelated observation is not pulled in** — `PASS`. A plain
   `Concept` observation (no `is_a=attributedmentalstate` predicate)
   stays `residual`, confirming the mint is specific to the shared
   structure, not a catch-all absorbing anything novel.
5. **Reproducible** — `PASS`. A fresh agent, given the SAME two domain-
   shaped observations with DIFFERENT names/content ("wendy"/"knowledge"
   vs "jo"/"agency_attribution"), mints the IDENTICAL MetaShape name —
   mechanically derived from the sorted predicate list, not randomized.

## 3. A misdiagnosis, corrected before it went further

The first attempt at this rung used realistic-looking test vocabulary
(`content_kind="controllability"` for the bigville side) and found it
absorbed into an EXISTING MetaShape (`feedback_control`) instead of
landing `residual`. The immediate hypothesis — a type-coercion bug in
`msg_recognize_prior` passing a raw signature list where `RecogniseShape`
expected a string — was WRONG, and was corrected by direct verification
before being acted on: `domains/teach.py`'s own reference caller
(`categorise_by_shape`) passes the SAME kind of raw list, documented as
the term's "structural path." The real cause, found by directly querying
which `ShapePrinciple`s `feedback_control` actually links to: a SECOND
principle beyond the one first inspected, `regulate`, carries the literal
keyword `'control'` — a substring of `"controllability"`. This was
CORRECT, working recognition catching a genuine (if debatable) semantic
overlap, not an engine defect. The vocabulary was changed
(`"agency_attribution"`, checked directly against the full keyword list
before use) rather than any engine code touched. Reported here per this
arc's standing rule: a wrong hypothesis caught before shipping is not
hidden, it's the discipline working.

## 4. Honesty notes

**Does establish**: the already-landed `META_SHAPE_FIRST_CLASS_RESULTS.md`
infrastructure generalizes correctly to a genuinely new pair of domains
neither its own gate nor this session's earlier work exercised —
`character_tom.py`'s narrative belief-tracking and bigville's resident-
ToM belief, sharing ZERO attribute keys in their native representations,
converge on one shape once projected into a shared vocabulary, with ZERO
new Rust and ZERO new seeded rules. This is exactly what "unify the ToM
system" asked for at the level the user chose (live recognize/decode
convergence), not a cosmetic label.

**Does NOT establish**: any automatic wiring — registration is an
EXPLICIT action (`register_character_tom_attitude`/`register_resident_
tom_belief`), not fired by either domain's own runtime ingest. Does NOT
register any OTHER target-scoped Concept (`regard_for` etc.) under this
shape — scoped exactly to `controllability_for`, per `bigville_theory_
of_mind.py`'s own ToM-vs-affect distinction. Does NOT independently
validate the `attributor`/`target`/`content_kind` vocabulary choice
beyond confirming it avoids accidental collision with the existing
keyword taxonomy — a design decision, not a derived one.

## 5. Files

- `docs/research/engine_substrate/TOM_ATTRIBUTED_MENTAL_STATE_META_SHAPE_PREREG.md`
- `docs/research/engine_substrate/TOM_ATTRIBUTED_MENTAL_STATE_META_SHAPE_RESULTS.md` (this file)
- `domains/tom_meta_shape.py` (new)
- `scripts/tom_meta_shape_demo.py` (new)
- `tests/test_tom_meta_shape.py` (5/5, new)
