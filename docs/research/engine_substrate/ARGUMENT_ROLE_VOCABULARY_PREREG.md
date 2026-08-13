# ARGUMENT_ROLE VOCABULARY — PREREG

Base `main` at `9cb60c0` ("Merge two-novel-orbits-third-grain: prog_chunk_growth
confirmed safe, GO"), verified with `git log --oneline -1 main` immediately before
branching (the task brief's stated tip, `3719b50`, had already moved by the time this
rung started — re-checked, no conflict: the intervening commits touch
`prog_chunk_growth`/orbit-gate work, not `domains/reflective_faculty.py`'s
cue-authoring path or `seeds/relation_vocabulary.json`). Worktree
`/home/matt/ozmadev/ocelot-worktrees/argument-role-vocabulary`, branch
`argument-role-vocabulary`.

Direct follow-on to `docs/research/engine_substrate/RELATION_CUE_TOKEN_COLLISION_
RESULTS.md` §6 ("The representation question"), which named this rung's exact scope
and deliberately deferred it:

> "promote the uppercase role placeholders to a first-class, held
> `ArgumentRole{name, gloss}` node type — the direct structural analogue of the
> already-existing `FunctionalRole` vocabulary, one level down (`FunctionalRole`
> names system FUNCTIONS; `ArgumentRole` would name argument SLOTS). Each
> `RelationCue` would reference an `ArgumentRole` by identity instead of embedding a
> bare string; a mint-time guard (on `teach`/`ground_predicate`'s cue-minting path)
> would check whether a NEW cue reusing an EXISTING role-token string is extending
> the SAME held role (safe, the common case) or introducing a textual collision with
> a DIFFERENT one (needs disambiguation before install). This is a SHAPE, not a
> NUMBER... a growing, recognised vocabulary (sd-loop shaped: recognise the existing
> role or mint a new one), not a fixed string enum."

Explicitly **not** re-doing (already done, merged, out of scope): the
`_shared_shape`/`shape_fit` comparison-layer fix (axis-anchored on `RelationCue.name`
identity); the `POSITION`→`COORD` / `PRIOR`→`EVIDENCE` renames.

---

## 1. The question, restated precisely

1. Does `ArgumentRole{name, gloss}` — a held, deduped node type, one per
   argument-slot role — hold up as the direct structural analogue of
   `FunctionalRole`, and can it be seeded from the vocabulary's own current state
   (re-audited, not assumed stale)?
2. How should `RelationCue` reference an `ArgumentRole` by identity, given every
   real downstream consumer (`_load_relation_cues`, `_relation_cue_index`,
   `_shared_shape`, Rust `shape_fit`) reads `RelationCue.relation` as a bare JSON
   string today, and none of those four call sites may regress?
3. Is there a genuine mint-time hook — the one real cue-minting call site
   (`domains/reflective_faculty.py::ground_predicate`, via `teach(agent,
   "RelationCue", ...)`) — where a graph rule can decide RECOGNIZE / MINT / FLAG,
   sd-loop-shaped (mirroring `sd_recognize`/`sd_mint_quantum`,
   `seeds/blob_edge_correspondence.json`'s `blob_mint`/`blob_recognize`, and
   `seeds/gap_awareness.json`'s gap-filing rules — three live precedents for
   exactly this recognize/mint/flag shape, not a fourth invented mechanism)?
4. Can the guard be DEMONSTRATED, live, both directions — a genuinely new cue
   correctly reusing a held role accepted with zero friction, and a genuinely
   colliding reuse flagged, not silently installed?

---

## 2. The re-audited census (re-run, not trusted stale)

`python3 -c "..."` over the CURRENT `seeds/relation_vocabulary.json` (reproduced in
full in the RESULTS doc): **52 `RelationCue` nodes, 65 distinct uppercase tokens, 71
distinct lowercase tokens.** 20 uppercase tokens still collide (18 SHARED-INTENTIONAL
+ 2 AMBIGUOUS — `NEW`, `CONTENT` — exactly the prior rung's §3 classification,
unchanged since); 45 are unique to one cue, including the four rename-era tokens
(`POSITION`, `PRIOR`, `COORD`, `EVIDENCE`), each now used by exactly one cue. This
matches `RELATION_CUE_TOKEN_COLLISION_RESULTS.md` §4's own closing tally exactly
("20 upper + 11 lower" colliding after the rename) — the census has not drifted.

**Scope decision, registered before building:** `ArgumentRole` will be seeded for
the FULL uppercase-token census (65), not only the 20 that currently collide.
Reasoning, stated before building rather than after: a partial promotion (ArgumentRole
only for colliding tokens) would leave the representation half-migrated — 45 of 52
cues' single-cue tokens would still be bare strings with no held identity, and the
wiring mechanism (item 2) would need two different code paths depending on whether a
token happens to collide today. A token that is unique TODAY can collide tomorrow
(that is the entire point of a mint-time guard); giving every uppercase token an
`ArgumentRole` from the start means the guard's "does an ArgumentRole already exist
for this token" test is uniformly meaningful, not conditional on today's collision
census. This is offered as the SHAPE-correct reading of "promote the uppercase role
placeholders to a first-class node type" — full coverage, not a floor of "18+" — while
still reporting the 18+/20/65 breakdown explicitly since that is what the charter asks
to be reported.

---

## 3. Falsifiable predictions, registered before building

- **P1 (representation, Q1).** `ArgumentRole{name, gloss}` will seed cleanly as 65
  nodes, zero duplicate `name`s (by construction — one node per distinct token
  string), using `RELATION_CUE_TOKEN_COLLISION_RESULTS.md` §3/§4's own
  human-authored classification text for the 22 previously-classified tokens
  (18 shared + 2 ambiguous + the 2 rename-generated pairs) and a mechanically
  DERIVED gloss (from the token's one home cue's own `keywords`, no invented
  semantics) for the remaining ~43 unique tokens.
- **P2 (wiring, Q2).** `RelationCue.relation` stays BYTE-IDENTICAL (untouched
  string attr) — the four real consumers named above are predicted to need ZERO
  code change, verified by the existing regression suite plus a new pinned
  byte-identity test. Wiring is ADDITIVE: real `RelationCue -uses_role->
  ArgumentRole` edges, cross-referenced by `{"type": "RelationCue", "name": ...}`
  in the seed manifest (the SAME seed cross-ref mechanism `seeds/llm_partner.json`
  already uses for `{"type": "Lexicon", "id": "lexicon"}, confirmed by direct
  reading of `runners/dsl/src/py.rs::resolve_seed_ref`'s `type`-ref branch, not
  assumed) — for the 52 EXISTING cues, wired STATICALLY from the audited
  classification (this is human semantic judgement; predicted NOT mechanically
  re-derivable at boot from structure alone — see P3's negative finding).
- **P3 (guard mechanism, Q3) — a predicted NEGATIVE result, registered honestly
  before it is measured.** A purely structural recognizer (same predicate, same
  slot position, embedding overlap, etc.) is predicted to be UNABLE to reproduce
  the prior rung's human SAME-vs-DIFFERENT classification: genuinely-shared tokens
  (e.g. `SELF` across `adopt_winner`/`bounded`/`control_agency`/`self_reference`/
  `vary_self`) share almost no structure beyond the bare token itself (different
  predicates, different tuple positions), which is indistinguishable, structurally,
  from the two CONFIRMED-accidental collisions (`POSITION`/`PRIOR`, also
  structurally dissimilar beyond the token). Therefore the guard's real job is
  predicted to be: (a) recognize with confidence ONLY on a byte-identical relation
  tuple (a pure keyword-synonym addition — `ground_predicate`'s own, only, current
  live behaviour); (b) mint with confidence ONLY on a genuinely never-seen token
  (safe by construction, no collision possible); (c) FLAG — never silently accept —
  every other case (an existing token reused under a structurally different tuple),
  deferring the SAME/DIFFERENT judgement to a human/agent review via a filed
  `SelfConcern`, exactly as the charter's own words say ("flag it, don't silently
  install") rather than attempting an auto-classification the prior rung's own
  census shows is not mechanically recoverable from structure alone.
- **P4 (demonstration, Q4).** The live guard will be exercised in BOTH directions
  on real, not purely synthetic, data: (i) SAFE — replaying `ground_predicate`'s
  actual behaviour (teach a new keyword-only cue whose `relation` is byte-identical
  to an existing cue's) is predicted to hit the RECOGNIZE branch, wired, zero
  `SelfConcern` filed. (ii) COLLISION — two of the vocabulary's own already-recorded
  AMBIGUOUS occurrences (`attention_watch`'s `NEW`, `source_recognition`'s
  `CONTENT`) will be deliberately left OUT of the static wiring and replayed
  through the live guard as freshly-taught cues; predicted to hit the FLAG branch
  (their relation tuples are NOT byte-identical to any existing wired cue for that
  token), filing a `SelfConcern{kind:'argument_role_collision'}` and leaving the
  edge unwired. A third, fully SYNTHETIC case (a fabricated cue reusing `SELF` in
  a structurally novel tuple, e.g. `["announce","SELF","as","WINNER"]`) is also
  predicted to FLAG, demonstrating the guard is conservative for TOKENS the census
  currently classifies safe-shared, not merely for the two already-known-ambiguous
  ones — i.e. it does not special-case on the prior rung's classification, it
  reacts to structure at authoring time.

**A clean NO-GO / partial result is registered as fully acceptable**, per the
charter and per the prior rung's own model, specifically for P3: if the guard
cannot be built as a confident three-way discriminator (recognize/mint/flag) within
existing Terms, the honest fallback (recognize-on-identity, mint-on-novelty, flag
everything else) is reported as the FOUND design, not forced into a stronger claim.

---

## 4. GO/NO-GO bar

**GO on the vocabulary (P1)** iff `ArgumentRole` seeds with zero duplicate names and
the gloss text is traceable to either the prior rung's own classification or a
mechanical, quoted derivation (never fabricated prose).

**GO on the wiring (P2)** iff `RelationCue.relation` is unchanged byte-for-byte AND
the four real consumers (`_load_relation_cues`, `_relation_cue_index`,
`_shared_shape`, Rust `shape_fit`) pass the EXACT regression files
`RELATION_CUE_TOKEN_COLLISION_RESULTS.md` §7 already used, paired before/after,
zero new failing node ids.

**GO on the guard (P3/P4)** iff the recognize/mint/flag rules install and fire
through a real `WorldAdapter` + `load_all_seeds` boot, using ONLY existing Rust
Terms (no new Term — if one turns out to be required, STOP and report why, per the
task's explicit instruction), and the P4 demonstration produces the predicted
verdicts on real graph state (not a hand-mocked dict).

**NO-GO / partial**, reported honestly rather than inflated, on any piece that does
not clear its own bar — in particular P3's negative sub-claim (no confident
auto-classification of SAME-vs-DIFFERENT beyond identity) is not a failure of this
rung; it is the predicted, honest shape of the mechanism.

---

## 5. Explicitly out of scope (restated from the charter)

- Re-doing `_shared_shape`/`shape_fit`'s comparison-layer fix.
- Re-litigating `POSITION`→`COORD` / `PRIOR`→`EVIDENCE`.
- A sweep of every seed file beyond `relation_vocabulary.json` /
  `math_capability_shapes.json` for these tokens.
- New Rust Terms (graph data + seed rules only, mirroring the existing sd-loop /
  blob-edge / gap-awareness pattern; any genuine need for a new Term is a STOP,
  not a build).
- Resolving `NEW`/`CONTENT`'s genuine ambiguity — they remain AMBIGUOUS; the guard
  surfaces that ambiguity live (P4-ii), it does not resolve it.
