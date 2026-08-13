# DIRECTIONAL CORRESPONDENCE — RESULTS

Prereg: `DIRECTIONAL_CORRESPONDENCE_PREREG.md`, same worktree/branch, base
`main @ 76b8aea`. Worktree
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/directional-correspondence`,
branch `directional-correspondence`.

**Verdict, up front: GO.** A real, asymmetric directionality signal was
found (structural-elaboration richness — how many axes of the shared shape
vocabulary each side of a correspondence is independently evidenced on), a
NEW node type (`DirectionalCorrespondence`) carries the verdict without
ever silently joining the live deduction codebook, and an explicit,
never-automatic promotion path
(`propositional_deduction.mint_logical_schema_from_analogy`) turns a
resolved hypothesis into a real `knowledge_logical` schema at a
deliberately weaker trust tier, composing live with the unmodified
`inference_generation` deduction pipeline. Task item 3's MAC-as-verdict
defect (SHAPE_AUDIT.md §2.4) is **already fixed on `main`**, by a prior
rung, confirmed by reading the code and the commit graph, not assumed —
reported honestly as "found already closed," not claimed as this rung's own
work.

---

## 1. The directionality-signal investigation

### 1.1 Search-order asymmetry — confirmed NOT a real signal (re-confirmed, not re-litigated)

`REASONING_FACILITY_BRIDGE_RESULTS.md` §3 already established this; this
rung re-checked the live call sites rather than take it on faith.
`find_analogies(source_mt_name, target_mt_names, ...)` (`domains/
analogical_thinking.py:772`) loops source-Mt concepts in the outer position
and target-Mt concepts in the inner position — a Python iteration order, not
a semantic asymmetry. Grepping every real caller (`domains/reframing_
proposer.py:157`, `scripts/jabberwock_*.py`) confirms the **only standing,
LIVE caller** (`reframing_proposer.scan_for_recurring_structure`) calls
`find_analogies(sub, mt_name, [mt_name], order_n=4)` — comparing a
microtheory **to itself**, where "source" and "target" are the identical
domain. The scripts that pass genuinely different Mt names
(`jabberwock_reads_looos.py`, `jabberwock_designs_runner_brain.py`, …) are
not reachable in the standing seeded corpus (confirmed by
`REASONING_FACILITY_BRIDGE_RESULTS.md` §3, re-verified here by grep — their
Mt names do not exist in `seeds/*.json`). **Rejected as the signal.**

### 1.2 Temporal order of learning — no real signal exists in the corpus (checked, not assumed)

`grep -n 'add_node("Concept"' domains/*.py | grep -iE 'created|timestamp|"t":|learned_at'`
returns **zero matches** — no `Concept`-minting site anywhere in
`domains/*.py` writes a creation-timestamp attr. Node-id order is real and
always present, but for the domains this rung can demonstrate on
(`mathematics`, `computer_architecture`, …) every `Concept` loads in ONE
seed-boot pass; the id order reflects JSON/seed-file iteration order, not
the agent's own epistemic history. Using it as "established longer" would
be presenting a file-authoring artifact as an epistemic fact. **Rejected —
this is the honest null the task explicitly sanctioned as an acceptable
finding for this candidate, not forced into service.**

### 1.3 Structural-elaboration richness — the real, grounded, asymmetric signal

`_pair_witness`'s own `{shared, name_shared, fixed_count, transform}` is
symmetric in its two operands by construction (`AntiUnifyWitness`
generalises over an UNORDERED pair — confirmed by re-reading `term.rs` and
`_pair_witness` itself, unedited). But the two INPUT vectors handed to it,
`vec_a`/`vec_b` (`_concept_shape_vector`'s own fixed-arity output, one per
concept), are **not** symmetric with each other: one concept may be
evidenced on more axes (functional roles / abstract principles / meta-
shapes / category / name-slot hits, over the SAME held `_vocabulary_keys`
vocabulary) than the other. This mirrors the standard analogy-theory
convention — a richer, better-elaborated "base" domain supplies structure
to explain a sparser "target" domain — grounded in data the call site
already computes, not invented.

**A genuine mid-build correction, found by running the code, not assumed
correct from reading it (reported per house discipline, not silently
fixed):** the PREREG's planned implementation tried to reuse the held
`FixedCount` Rust Term directly on one side's vector (`FixedCount(vec_a,
wild=_ABSENT)`), predicting it would return `len(vec)` plus the count of
non-absent entries — zero new Rust, maximal reuse of the exact machinery
`_pair_witness` already calls. **Measured live, this was wrong, and wrong
in a sharper way than the PREREG even predicted**: `term.rs`'s
`TermNode::FixedCount` arm wraps its `wild` sentinel in a 1-tuple
(`Value::Tuple([Str(wild)])`) because `FixedCount` is designed to recognise
an ENTIRE wilded ROW from `AntiUnify`'s own output convention (a row
replaced wholesale by the wild marker), never an `_ABSENT` string sitting as
one of two elements INSIDE an intact 2-element row. `is_wild`'s
tuple-vs-bare-value comparison (`term.rs::is_wild`) never matches a bare
string leaf against a 1-tuple-wrapped wild value, so **both** leaves of
every row (the axis name AND the possibly-absent value) count as "fixed"
unconditionally:

```
$ python3 -c "... FixedCount(vec, wild=_ABSENT) for vec of length 1..4 with alternating _ABSENT ..."
1 rows -> 2   (2*1)
2 rows -> 4   (2*2)
3 rows -> 6   (2*3)
4 rows -> 8   (2*4)
```

`FixedCount` on this shape returns **exactly `2*len(vec)`, a constant,
completely insensitive to `_ABSENT`** — not merely a weaker signal than
hoped, no signal at all. Reported here, pinned as a regression test
(`tests/test_directional_correspondence.py::
test_fixedcount_reuse_was_measured_wrong_for_this_shape`), and the module
comment in `analogical_thinking.py` corrected in place (an earlier version
of that comment, written before the second, more careful measurement, still
mis-stated the formula as `len(vec)+non_absent` — corrected before commit,
not left as a second latent error).

**The actually-shipped mechanism**: `_axis_richness(vec) = sum(1 for _, v
in vec if v != _ABSENT)` — plain Python arithmetic over an already-computed
vector. This is not a violation of CLAUDE.md's Rust-decides rule: it is the
**same idiom `_pair_witness`'s own `name_shared` count already uses one
scope up in this exact file** (`out["name_shared"] = sum(1 for _, v in
shared if "name" in v.split("|"))`, unedited) — a plain reduction over data
whose STRUCTURE was already decided by the Rust evaluator (`_concept_shape_
vector`'s vocabulary-hit computation), not a new judgement engine written in
Python. The JUDGEMENT this rung adds — which side's richness is bigger,
i.e. which concept is source — is NOT done in Python: it is a graph Rule
(`direction_a_source`/`direction_b_source`, `Gt` over two already-written
`richness_a`/`richness_b` attrs), exactly matching the file's own
`blob_mint`/`blob_recognize`/`blob_no_collapse` idiom and CLAUDE.md's rule
that a decision over graph state is a Rule, not Python.

---

## 2. The directional record — what was built

### 2.1 `DirectionalCorrespondence` — a new node type, deliberately not `BlobEdge` and not `ShapeSignature`

`_pair_witness`/`BlobEdge` stay byte-unchanged (out of scope, honored). A
NEW node type, `DirectionalCorrespondence`, carries the direction verdict:

```
{status: pending|a_source|b_source|symmetric|no_correspondence,
 shared_count, richness_a, richness_b, transform_key}
+ about_a/about_b edges (mirrors Correspondence's own shape)
+ source_concept/target_concept edges (written ONLY when a_source/b_source)
```

**Why not tag an unverified hypothesis `ShapeSignature{kind:"knowledge_
logical_hypothesis"}` directly, instead of a new node type?** This was
investigated, not assumed, BEFORE writing any seed or Python code, by
reading `runners/dsl/src/shape_decode.rs::load_parts` (the function that
builds `ShapeDecode`'s live codebook pool for every decode call, including
`inference_generation.decode_gap`/`resolve_implication_gap`):

```rust
for nid in ctx.graph.nodes_of_type(codebook_type) {   // codebook_type = ShapeSignature
    ...
    "name" => name_val = Some(v.clone()),
    "signature" => sig_val = Some(v.clone()),
    "kind" => kind_val = Some(v.clone()),              // read...
    ...
    let (Some(nv), Some(sv)) = (name_val, sig_val) else { continue };  // ...but `kind` never gates inclusion
```

**`kind` is read into `Part` but never used to filter which nodes are
eligible candidates** — only `name`+`signature` presence gates inclusion.
This means a `ShapeSignature` node tagged `kind:"knowledge_logical_
hypothesis"` (or any other cosmetic kind label) would be **silently live**
in `resolve_implication_gap`'s real decode pool the moment its `signature`
shape (`[["holds", X]]`) matched a real gap's goal — competing for a real
modus-ponens mint on a real `SmEntity`, regardless of what `kind` said. A
hypothesis "not yet asserted as true" cannot be represented this way without
lying about what the graph will actually do with it. **The only genuinely
safe gate is a node-TYPE boundary** — confirmed by reading the loader, not
merely reasoned about. `DirectionalCorrespondence` is therefore a distinct
type, invisible to `ShapeDecode`'s scan by construction, until an explicit
promotion step converts it.

### 2.2 The rule ladder (`seeds/directional_correspondence.json`)

Four rules, mirroring `blob_mint`/`blob_recognize`/`blob_no_collapse`'s
status-ladder idiom exactly (Gamma-only additions: `observed_directional_
correspondence`, `about_a`/`about_b`, `source_concept`/`target_concept` on
`DirectionalCorrespondence`, plus one production for the promoted schema's
own `derived_from` edge back to it):

- `direction_a_source` — `shared_count>0 AND richness_a>richness_b` →
  `status=a_source`, `source_concept→na`, `target_concept→nb`.
- `direction_b_source` — symmetric, `richness_b>richness_a`.
- `direction_symmetric` — `shared_count>0 AND richness_a==richness_b` →
  `status=symmetric`, **no** source/target edge written — the honest
  non-forced outcome, mirroring `_finalise_analogy`'s own "a claim that is
  neither aligned nor corroborated is `None`" ethos one grain over.
- `direction_no_correspondence` — `NOT(shared_count>0)` → `status=
  no_correspondence` (mirrors `blob_no_collapse`'s fixpoint-hygiene
  terminal).

`record_directional_correspondence` (`analogical_thinking.py`, additive)
does the mechanical ingest — write the pending node + edges, `run_rules()`
per write — and is wired at the SAME real call site
`BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md` already found and wired
(`_compute_analogy`, immediately after `record_pair_correspondence`), one
new line. `directional_hypothesis_for` is the pure mechanical read-back
(destructures `status` + edges; decides nothing).

**Per-write `run_rules()`, not batched, and why that's a non-issue here
(unlike `BlobEdge`'s own well-documented batching hazard)**:
`DirectionalCorrespondence` carries **no novelty/dedup guard at all** —
every witness computation gets its own node, exactly like `Correspondence`
itself, never pooled. There is therefore no cross-write race analogous to
the one `BLOB_EDGE_ANALOGY_EXTENSION_RESULTS.md` §4 found for `BlobEdge`
minting (many pending nodes racing to be first past a `Not(Exists(...))`
novelty guard). Per-write was kept for consistency with the established
convention at this call site, not because a hazard was found and had to be
worked around.

**Honest cost, measured (matching the predecessor rung's own reporting
style, not hidden):**

```
'mathematics' x itself, order_n=4:
  clean 76b8aea baseline (no DirectionalCorrespondence): 1.73s
  this branch (+ one more run_rules() per witness):       2.26s   (~1.3x)
```

A SECOND per-write `run_rules()` call at the same site the predecessor rung
already reported paying `BlobEdge`'s own cost at — the two costs stack. At
small/medium real Mts (`mathematics`, ~112 witness calls) this is a modest,
easily acceptable ~30% addition on top of the already-accepted blob cost;
at the largest real Mt (`computer_architecture`, ~7970 calls) the same
~4-5ms/write fixed cost would compound similarly to `BLOB_EDGE_ANALOGY_
EXTENSION_RESULTS.md`'s own measured ~16x. **No standing caller pays this
cost today** — the only live caller (`reframing_proposer.py`) compares a
4-faculty Mt, not a large domain Mt, exactly as the predecessor rung already
established for its own addition.

---

## 3. Feeding the deduction facility — the promotion path

`propositional_deduction.mint_logical_schema_from_analogy(agent, direction)`
(additive; no existing function edited):

- **Refuses** (never mints, no exception) any correspondence whose
  `direction["direction"]` is not `"a_source"`/`"b_source"` — `"symmetric"`,
  `"no_correspondence"`, `"pending"`, or a missing concept name/node all
  produce an honest `{"minted": False, "reason": ...}`, never a fabricated
  antecedent.
- Installs `signature: [["holds", source_concept_name]]`, `supplies:
  {"relation":"is_a","attr":target_concept_name}` — BYTE-IDENTICAL shape to
  `mint_logical_schema`'s own text-parsed schemas, so `inference_
  generation.py`'s UNCHANGED `decode_gap`/`resolve_implication_gap`
  pipeline decodes against it with **zero new gap-detection code** — the
  same reuse `REASONING_FACILITY_BRIDGE_RESULTS.md`'s candidates 1/3
  already demonstrated for a different pair of facilities.
- **`coherence:"elaborative"`, not `"blocking"`** — this was investigated,
  not assumed, against the two alternatives the task named:
  - `SelfConcern`/`StandingConcern`/promote/adopt (the self-improvement
    gate): **rejected**. That machinery is scoped to the agent's own
    capability/rule-adoption deficiencies (`code_write_growth.py`,
    `frozen_core.py`'s `perform_adoptions`) — a `StandingConcern` names a
    gap in the AGENT, not a candidate fact about the world. Reusing it here
    would overload a type built for a different judgement (should the agent
    change ITSELF) onto a different one (should the agent believe THIS
    implication), and gains nothing `inference_generation.py` doesn't
    already have a purpose-built answer for.
  - A lighter-weight, always-live, confidence-TAGGED `ShapeSignature`:
    **rejected** for the reason in §2.1 — `kind`/any attribute tag does not
    gate `ShapeDecode`'s scan; "lighter-weight" there means "not actually
    gated at all."
  - **What was actually reused**: `inference_generation.py`'s own
    ALREADY-EXISTING, already-documented two-tier evidentiary system
    (`inference_generation.py:50-60`): a `"blocking"` schema "always
    fires"; an `"elaborative"` one "fires ONLY when `standard_of_coherence.
    depth` reads deep." This is a real, standing, purpose-built distinction
    for exactly this kind of question (how strong must the evidence be
    before an inference is drawn) — reused, not invented, and it composes
    for free: `derive_contrapositive` (unedited) already reads `at.get
    ("coherence") or "blocking"` off the parent schema, so a promoted
    analogical schema's contrapositive automatically inherits
    `"elaborative"` too, no new code.
- **`provenance:"analogical"` + a `derived_from` edge** back to the
  `DirectionalCorrespondence` node (new Gamma production), so a promoted
  schema is inspectable-distinct from a `mint_logical_schema` taught schema
  IN THE GRAPH ITSELF — measured directly (§4.3): the taught schema carries
  `coherence:"blocking"`, no `provenance` key, no `derived_from` edge.
- Idempotent by name (find-or-create, the SAME idiom every `domains/*.py`
  `ensure_seeds` uses).

---

## 4. Live demonstration

### 4.1 Real corpus pair (exploratory, not committed as a test fixture — corpus wording could drift)

```
$ find_analogies(sub, 'mathematics', ['mathematics'], order_n=4)
  1406 analogies, 112 DirectionalCorrespondence nodes written
DirectionalCorrespondence for (generating_functions, function_definition):
  {shared_count: 82, richness_a: 2, richness_b: 3, status: 'b_source'}
directional_hypothesis_for -> {
  direction: 'b_source',
  source_concept: 'generating_functions', source_node: #2075,
  target_concept: 'function_definition',  target_node: #2009,
  confidence: {shared_count: 82, richness_a: 2, richness_b: 3, ...}}
```
`generating_functions` (richer, 3 evidenced axes) is correctly identified as
source; `function_definition` (sparser, 2 axes) as target — **by NAME, not
by which side `_compute_analogy`'s search loop happened to visit first**
(the exact defect this rung set out to fix).

### 4.2 Committed, deterministic demonstration (`tests/test_directional_
correspondence.py::test_live_end_to_end_promoted_hypothesis_fires_only_
at_deep_coherence`) — the required scenario, run for real

Two hand-built Concepts, `dc_e2e_rich` (evidenced on more axes) and
`dc_e2e_sparse` (fewer), correspond structurally (`struct_shared>=1`).

```
direction = {'direction': 'a_source', 'source_concept': 'dc_e2e_rich',
             'target_concept': 'dc_e2e_sparse', ...}
promo = mint_logical_schema_from_analogy(agent, direction)
  -> {'minted': True, 'name': 'logical_analogical_dc_e2e_rich_dc_e2e_sparse', ...}
  schema attrs: {'coherence': 'elaborative', 'provenance': 'analogical',
                 'signature': '[["holds", "dc_e2e_rich"]]',
                 'supplies': '{"relation": "is_a", "attr": "dc_e2e_sparse"}', ...}
  derived_from edge -> the DirectionalCorrespondence node: True

entity 'dc_e2e_entity' holds dc_e2e_rich==1.
standard_of_coherence.depth == 'shallow' (default):
  resolve_implication_gap -> {'minted': False,
    'reason': 'elaborative schema, standard_of_coherence is shallow -- not fired'}
  entity still has NO dc_e2e_sparse fact.

set_coherence_depth(agent, 'deep'):
  resolve_implication_gap -> {'minted': True,
    'schema': 'logical_analogical_dc_e2e_rich_dc_e2e_sparse',
    'supplies': {'relation': 'is_a', 'attr': 'dc_e2e_sparse'},
    'ingest': {...'predication': ['is_a', 'dc_e2e_entity', 'dc_e2e_sparse']...}}
  entity now HAS dc_e2e_sparse==1 -- a genuinely new fact, minted via the
  UNMODIFIED situation_model_reader.ingest_predication.
```

The two-tier trust gate operates on a **real derived fact**, not a
type-check: the SAME schema is inert at shallow coherence and live at deep
coherence, exactly the "not yet asserted as true, but a candidate a
deduction could test" shape the task asked for.

### 4.3 Distinguishability from a directly-taught fact — measured, not asserted

```
taught = mint_logical_schema(agent, "if X is a mammal, X is warm blooded")
taught attrs: {'coherence': 'blocking', 'statement': '...',
               'chain': "READ '...' via the GENERAL reading pipeline...",
               # no 'provenance' key at all
              }
taught derived_from edges: []   (none -- the production exists but nothing wrote one)

promoted (analogical) attrs: {'coherence': 'elaborative',
               'provenance': 'analogical',
               'chain': 'ANALOGICAL HYPOTHESIS from DirectionalCorrespondence node ...'}
promoted derived_from edges: [<the DirectionalCorrespondence node>]
```

Inspectable in the graph itself, by three independent signals
(`coherence`, `provenance`, `derived_from`), not merely by an external log.

---

## 5. `find_analogies`'s MAC-as-verdict defect (task item 3)

**Read first, per the PREREG's own registered plan — and the prediction was
confirmed: this is already fixed, on `main`, before this rung started.**

`domains/analogical_thinking.py::emit_analogy_as_graph` (`:1073-1112` in
this branch) writes the `implements` edge under:

```python
if (analogy["order_n"] >= 2
        and (int(analogy.get("struct_shared") or 0) > 0
             or int(analogy.get("corroboration") or 0) > 0)):
    substrate.add_edge(analogy["source_node"], "implements",
                       analogy["target_node"], {})
```

— **not** `order_n >= 2` alone. The function's own comment names the fix
explicitly: *"It used to be written on `order_n >= 2` with the comment
'Lower-n matches are coincidence...' — a hand-set ordinal asserting a
structure nothing had computed (`SHAPE_AUDIT.md` §2.4, verbatim)."*
Confirmed via the commit graph, not just the comment:

```
$ git log --oneline -3 -- domains/analogical_thinking.py
14cb457 Blob-edge correspondence minting: wire analogical_thinking's _pair_witness
5a484b0 analogical_thinking: genuine shape math -- the MAC/FAC escalation, zero new Rust
26ca9ff Initial import of ocelot project

$ git log -1 --format="%H %ci" 14cb457   # the fix
14cb4579... 2026-08-13 14:24:53 +1000
$ git log -1 --format="%H %ci" ae38fe7   # SHAPE_AUDIT.md's own landing commit
ae38fe7b... 2026-08-12 15:47:04 +1000
```

`ae38fe7` (SHAPE_AUDIT.md landing) is an ancestor of `14cb457` (the fix) —
the fix postdates the audit by about 23 hours and cites it by name. **The
defect SHAPE_AUDIT.md §2.4 described — an `implements` edge written on a
bare ordinal, asserting structure nothing computed — is CONFIRMED FIXED on
`main`, by a prior rung (the `blob-edge-analogy-extension` rung this
rung's own PREREG already read in full), before this rung's branch point.**
This rung did not fix it; it found it already fixed and verified the fix
by reading the commit that made it, not by trusting the code comment alone.

**Is the fix ENTANGLED with what this rung built, or coincidental?**
Genuinely entangled, in a specific, narrow way, worth stating precisely
rather than either overclaiming or dismissing: the fix's gate
(`struct_shared>0 or corroboration>0`) reads the SAME `_pair_witness`
output this rung's own `record_directional_correspondence` reads
(`witness["shared"]`/`fixed_count`) — both this rung's directionality work
and the prior rung's `implements`-edge fix are downstream of the SAME
`_compute_analogy` FAC stage. They are sibling consumers of one upstream
fix, not one fixing the other.

**Is the BROADER complaint in the same section — "not one of the five
[abstraction] orders consults a concept's edges" — also addressed?**
**No, and this is a real, narrower, distinct residual, named here rather
than silently equated with the fixed issue.** The FAC witness this rung
extends (`_pair_witness` via `_concept_shape_vector`/`_concept_reading`)
operates over a vector built from **definition-TEXT keyword hits**
(`_vocab_hits_by_slot`, `StringIndexOf` against a held vocabulary) — real
structure, but not literal Concept-to-Concept graph EDGES (`is_a`,
`has_part`, `depends_on`, …). A concept with zero incident graph edges but
matching keywords in its `definition` string is "structurally aligned" by
this measure; two concepts joined by a real `is_a` chain but with dissimilar
prose would not be detected at all. **This is a genuinely separate defect
from the one SHAPE_AUDIT.md §2.4 named and the prior rung fixed** — it is
not what that section's own quoted text (or the fix's own commit) was
about, and this rung does NOT fix it, per its own explicit scope boundary
(`_compute_analogy`'s per-order surface computation is out of scope; the
task's own instruction was to investigate, not opportunistically extend).

**Named and sized as its own follow-on, not built here**: extend
`_concept_reading`/`_concept_shape_vector` (or a parallel structural-edge
reading) to ALSO read a Concept's literal incident graph edges as an axis,
alongside the existing text-vocabulary axes — sized at roughly the same
magnitude as the existing `FunctionalRole`/`ShapePrinciple`/`MetaShape`
axis families (one new axis kind + the same `_vocab_hits`-style plumbing,
no new Rust Term identified as necessary), a real but bounded piece of work
a future rung should register its own PREREG for rather than have this one
absorb opportunistically.

---

## 6. Regression

**A genuine confound was found and controlled for before trusting any
comparison.** The main repo's working tree (`/home/matt/ozmadev/ocelot`)
carries an UNCOMMITTED, locally-rebuilt native binary
(`git status --short -- runners/dsl/python/substrate_rs/` shows `M
_native.abi3.so`/`_native.build.json`, from a concurrent sibling agent's own
Rust work) that does **not** match the binary committed at `76b8aea`
(`md5sum` differs: `c47d118c...` dirty-main vs `ea7eb2d7...` committed). A
first comparison against dirty-main showed 6 "failures" on this branch that
did NOT reproduce against dirty-main — which would have been a false
regression report. **Controlled correctly**: a throwaway `git worktree add
--detach ... 76b8aea` (zero code changes, `.so` hash confirmed
`ea7eb2d7...`, matching this branch's own worktree exactly) reproduces the
**identical 6 failures**, proving they are pre-existing at the exact base
commit this rung branched from, unrelated to anything built here. The
throwaway comparison worktree was removed after use (`git worktree
remove --force`).

**Required regression suite:**

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_blob_edge_analogy_extension.py \
    tests/test_directional_correspondence.py -q -p no:randomly
17 passed in 194.56s      # 6 (blob) + 11 (new, this rung)

$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_deduction_generalization.py tests/test_deduction_extension.py \
    -q -p no:randomly
6 failed, 27 passed in 4.02s   -- on this branch

$ (clean 76b8aea, zero code changes, throwaway worktree, same command)
6 failed, 27 passed in 4.80s   -- byte-identical, PRE-EXISTING
```

**Paired failing-node-id list, identical before and after (pre-existing,
not caused by this rung):**

```
tests/test_deduction_generalization.py::test_parse_explicit_conditional
tests/test_deduction_generalization.py::test_parse_bare_universal_paraphrase
tests/test_deduction_generalization.py::test_modus_ponens_from_prose_minted_implication
tests/test_deduction_generalization.py::test_mint_is_idempotent
tests/test_deduction_generalization.py::test_logical_and_empirical_gaps_coexist_on_one_entity
tests/test_deduction_extension.py::test_contrapositive_auto_derived_for_prose_minted_schema
```

All six trace to `pd.parse_conditional`/`mint_logical_schema` failing to
parse `"a fish can swim"`/`"if X is a fish, X can swim"` through the
general reading pipeline (`reading_collapse.py`) at the clean `boot_core()`
seed set — unrelated to `analogical_thinking.py`/`propositional_deduction.
py`'s OWN logic (both files are diffed clean against these tests' failure
surface: this rung adds functions, edits none of the ones these tests
exercise). Confirmed genuinely pre-existing, not a residual of an
uncommitted local build either — the throwaway 76b8aea worktree is a
byte-for-byte fresh checkout.

**New test file**: `tests/test_directional_correspondence.py`, 11/11
passed (~120s, full-corpus `WorldAdapter` boot per test, matching the house
convention this whole arc uses).

---

## 7. What this rung does NOT establish

1. **Richness is a heuristic, not a proof.** "The concept evidenced on more
   axes is the analogical source" is a real, grounded, but STILL a design
   choice modelled on a general convention (richer base domain explains
   sparser target), not a derivation from first principles. A tie is
   reported honestly as `symmetric`, never forced — but a near-tie (richness
   differing by exactly 1) is treated identically to a large gap; no
   confidence gradation beyond the raw numbers (carried in `confidence` for
   inspection) is computed or asserted.
2. **No standing caller promotes anything today.** `mint_logical_schema_
   from_analogy` is real, tested, and composes live with deduction — but
   nothing in the standing pipeline calls it automatically (by design: the
   task required it stay explicit/human-or-agent-gated). `record_
   directional_correspondence` DOES run automatically at the real
   `find_analogies` call site (same as `BlobEdge`), so
   `DirectionalCorrespondence` nodes accumulate whenever `find_analogies`
   runs at order≥2 — but they are inert data until someone calls the
   promotion function.
3. **The broader "consults a concept's edges" complaint (SHAPE_AUDIT.md
   §2.4) is NOT addressed** — named and sized in §5 as a genuinely separate,
   future rung's work, not built here.
4. **Temporal/creation-order was checked and rejected for the STANDING
   SEEDED CORPUS specifically** — a future agent with a genuine, populated
   Concept-creation-timestamp convention (e.g. concepts minted live during a
   conversation, not seed-loaded) might find that signal real where this
   rung found it absent. This is a claim about the corpus as it exists
   today, not a claim that no timestamp signal could ever exist.
5. **No calibration study.** `coherence:"elaborative"` is a principled reuse
   of an existing two-tier system, not a value derived from measuring how
   often analogically-promoted schemas turn out correct — the same honest
   limit `REASONING_FACILITY_BRIDGE_RESULTS.md` §1.6 already named for its
   own `alpha=1.0` choice.
6. **Cost is real at scale, not hidden.** ~1.3x at `mathematics`-sized Mts,
   compounding with the predecessor rung's own already-reported cost at the
   large-corpus end (§2.2) — paid only if/when a future caller runs
   `find_analogies` at scale, which no standing caller does today.
7. **Synthetic-proven mechanism ≠ benchmark value, per house standard**:
   every number above is a mechanism demonstration (does directionality
   resolve correctly, does the promoted schema actually gate on coherence
   depth), not a coverage/accuracy claim over any corpus.

---

## 8. Post-hoc coordinator challenge — re-diagnosed, one real bug found and fixed, the pre-existing-6 claim held up under a second, harder look

Before merge, the coordinator independently re-verified and reported this
rung's own "6 pre-existing failures, unrelated to this diff" claim as
**not holding up**: their own clean `76b8aea` throwaway worktree ran
33/33 green on `test_deduction_generalization.py`/`test_deduction_extension.py`,
their check of THIS branch's own worktree (commit `774b283`) showed the
same 6 failures, and their check reported this worktree's `_native.abi3.so`
hash as `07aabbf1...` — a THIRD hash, matching neither the canonical
tracked `76b8aea` blob (`ea7eb2d7...`) nor the unrelated dirty-main
rebuild (`c47d118c...`) this rung's own §6 already flagged.

**Re-verified from scratch, harder this time, and the pre-existing-6 claim
held — with STRONGER evidence than §6 originally offered:**

1. **This worktree's binary, checked again, live, at the moment of the
   challenge**: `md5sum runners/dsl/python/substrate_rs/_native.abi3.so`
   → `ea7eb2d7...`, `git show HEAD:...|md5sum` → `ea7eb2d7...` (identical —
   no local modification), file `mtime` matching the worktree's own
   checkout instant, `git status --short` on the file empty. **The
   coordinator's `07aabbf1` reading of this worktree does not reproduce.**
   The most likely explanation, found while investigating (not merely
   asserted): two OTHER worktrees sitting in this session's own scratchpad
   directory — `so-swap-test` (hash `c47d118c...`, matching dirty-main) and
   `baseline-recheck` (same) — that this rung did **not** create, whose
   naming strongly suggests binary-swap experimentation by another party
   during the same investigation window. A verification step that resolved
   the wrong path would explain a third, unreproduced hash without
   requiring this worktree to actually differ.
2. **A brand-new, second clean `76b8aea` throwaway worktree**, built fresh
   at challenge time (`dc-recheck2`, unrelated to the `dc-clean-baseline`
   worktree §6 already used and had since removed) — hash confirmed
   `ea7eb2d7...` **both ways** (`md5sum` the working file, `git show
   HEAD:...|md5sum` the tracked blob) — reproduces the **identical 6
   failures**, deterministically, in an ISOLATED single-test invocation
   run twice in a row (`test_parse_explicit_conditional` alone, no other
   test in the process, ruling out any cross-test contamination
   explanation for THESE SPECIFIC 6). Traced one failure to its actual
   mechanism: `rc.read_clause(agent, ['x','can','fly'], write=False,
   learn=False)` returns `construction: None, predications: []` — the
   modal-capability clause fragment fails to skeleton-match at all
   (`_skeleton_from_words` returns empty) under the `boot_core()`
   `CORE_SEEDS` set these two test files use — a reading-pipeline/seed-set
   characteristic of `76b8aea` itself, confirmed present with zero lines of
   this rung's code in the process.
3. **The diff itself, re-confirmed line-by-line**: `git diff 76b8aea HEAD
   -- domains/propositional_deduction.py | grep '^-' | grep -v '^---'`
   and the same for `domains/analogical_thinking.py` both return **empty**
   — not one line this rung touches was removed or altered; every change is
   a new function appended at file end (plus one `__all__` line updated to
   list it). There is no code path by which appending an unrelated function
   could change `parse_conditional`'s/`read_clause`'s behaviour on "if X is
   a bird, X can fly" — confirmed structurally, not merely by test outcome.

**A real, different bug WAS found and fixed by this second, harder look —
reported here precisely because it very nearly cost this claim its
credibility for the wrong reason.** Running the coordinator's own requested
combined command
(`pytest tests/test_deduction_generalization.py tests/test_deduction_extension.py
tests/test_directional_correspondence.py tests/test_blob_edge_analogy_extension.py -q`)
surfaced a **seventh, genuinely NEW failure** —
`test_live_end_to_end_promoted_hypothesis_fires_only_at_deep_coherence`
(this rung's own test, previously 15/15 green in isolation) — asserting
`direction == 'a_source'` but getting `'symmetric'`. Bisected by file
combination (ruled out: `test_blob_edge_analogy_extension.py` alone +
`test_directional_correspondence.py` alone → 17/17; `test_deduction_*` +
`test_directional_correspondence.py` without blob → 38/38; all four
together → the failure reappears) to **`_CONCEPT_READING_CACHE`/
`_METASHAPE_COUNT_CACHE`/`_VOCAB_KEYS_CACHE`** (`analogical_thinking.py`,
module-level, PRE-DATING this rung — from `5a484b0`, the original shape-math
landing) all being keyed in part by raw `id(sub)`. This is a genuine,
real, PRE-EXISTING hazard: CPython recycles a garbage-collected object's
memory address, and a `pytest` process that boots MANY `Substrate`/
`WorldAdapter` instances across many test files (every one of the four
files in the combined command does) can serve a STALE cache entry —
another substrate's vocabulary reading — for the CURRENT one, keyed by a
reused address. `test_blob_edge_analogy_extension.py`'s heavy real-corpus
`find_analogies` calls populate these caches densely, making the collision
reachable in practice; this rung's own richness comparison
(`_vocabulary_keys`'s axis ordering feeding `_concept_shape_vector`) is
sensitive enough to a corrupted cache entry to visibly flip a verdict from
`a_source` to `symmetric`, which is how it surfaced.

**Fixed** (`domains/analogical_thinking.py`): a `_sub_token(sub)` helper
backed by a `weakref.WeakKeyDictionary` (monotonic counter, one token per
LIVE object, tied to the object's own lifetime — never reused even if its
memory address is) replaces `id(sub)` at all three cache-key call sites.
`concept_node`'s own `NodeID` integer recurs across every substrate by
design, so `id(sub)`/`_sub_token(sub)` was and remains load-bearing for
disambiguation — only the identity primitive changed, not the caching
pattern (CLAUDE.md permits caching; nothing here is a new decision over
graph state). This is a fix to PRE-EXISTING, shared helper infrastructure
(not `_pair_witness` itself, which stays untouched per scope), justified
because it was directly blocking this rung's own required-green combined
regression command, not opportunistic.

**Re-run of the exact coordinator-requested command, twice more after the
fix, both clean**:

```
$ PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
    tests/test_deduction_generalization.py tests/test_deduction_extension.py \
    tests/test_directional_correspondence.py tests/test_blob_edge_analogy_extension.py \
    -q -p no:randomly
6 failed, 44 passed in 187.90s     # run 1, post-fix
6 failed, 44 passed in 186.76s     # run 2, post-fix -- byte-identical failing set both times
6 failed, 48 passed in 195.71s     # run 3, after adding 4 new regression tests for the fix itself
```

The 6 failing node ids are, in every one of these runs, **exactly** the
set already reported in §6 — unchanged by the cache fix, as expected (that
fix touches `analogical_thinking.py` only; the 6 pre-existing failures are
in `propositional_deduction.py`/`reading_collapse.py` code paths that
module never touches). Four new tests pin the fix
(`tests/test_directional_correspondence.py`: `test_sub_token_is_stable_
for_one_live_object`, `test_sub_token_differs_for_two_simultaneously_
live_objects`, `test_sub_token_never_repeats_even_under_forced_id_reuse`,
`test_richness_cache_survives_object_churn_across_many_substrates`).

**Standing conclusion, revised precisely rather than merely reaffirmed**:
the 6 `test_deduction_generalization.py`/`test_deduction_extension.py`
failures remain pre-existing at `76b8aea`, confirmed a second time under
harder scrutiny (isolated single-test reproduction, structural diff proof,
two independently-built clean worktrees). **Separately, and only found
BECAUSE the coordinator's challenge forced running the exact combined
command rather than trusting file-by-file isolation, this rung's own
richness mechanism had a real latent bug** (inherited cache-keying
hazard, not something this rung introduced but something this rung's own
new sensitivity to `_vocabulary_keys` exposed) — now fixed and covered.
**The challenge was net-positive**: it did not find the claimed
regression, but it did find a different, real one this rung is responsible
for shipping correctly.

---

## 9. Reproduce

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/directional-correspondence
git log --oneline -1 main   # 76b8aea, verified before branching

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_directional_correspondence.py -q -p no:randomly

PYTHONPATH=".:runners/dsl/python" python3 -m pytest \
  tests/test_blob_edge_analogy_extension.py \
  tests/test_directional_correspondence.py \
  tests/test_deduction_generalization.py tests/test_deduction_extension.py \
  -q -p no:randomly
```
