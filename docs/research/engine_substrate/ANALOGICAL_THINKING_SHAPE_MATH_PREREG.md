# ANALOGICAL THINKING — GENUINE SHAPE MATH — PREREG

**Status: REGISTERED BEFORE CODE.** Written against `main` at `d239b7c`
(`Merge shape-audit-pattern-c-fixes: three live corruption bugs closed`), in the
isolated worktree `/home/matt/ocelot-analogical-thinking-shape-math` on branch
`analogical-thinking-shape-math`.

**Charter.** `SHAPE_AUDIT.md` **§2.4** — the June 2026 MAC/FAC diagnosis at its
*original site*, re-confirmed still-live by `META_SHAPE_FIRST_CLASS_RESULTS.md`
§9.1 (*"`analogical_thinking._compute_analogy` still treats a string-token
overlap as the verdict at all five orders and never consults a concept's edges.
Confirmed still true; untouched."*). That rung named it and left it; this rung
takes it.

**Measurements taken before this document was written were READ-ONLY** — three
probes that boot the unmodified tree (`load_all_seeds`) and count. Nothing was
modified to produce them. They are quoted in §2 as the registered BEFORE, and
they are quoted *because they changed the design* — §2.1 in particular converts
one of the brief's own suggested fixes into a registered NO-GO.

---

## 0. The claim being tested, in one paragraph

The creator's June 2026 diagnosis of this faculty is that its cheap content
match is **a MAC stage treated as the verdict, with no FAC stage** — and the
prescription is *"make the bucket a FILTER, not a verdict — escalate every
surface survivor into an explicit structural-alignment pass."* The shape-math
algebra that would do the escalating (`AntiUnifyWitness`, `Substitute`,
`Unify`, `StructSim`, `Covers`) has been in `term.rs` since the same month, and
`RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §4 proved it operates correctly on real
data at the *rule* grain. This rung asks whether it can be pointed at the
population `analogical_thinking` actually reasons over — and, where it cannot,
says so precisely rather than forcing it.

---

## 1. What `_compute_analogy` actually does — AR1's object, read from the code

`domains/analogical_thinking.py:252-361`. Given a source concept `sc`, a target
concept `tc`, and a ceiling `order_n`, it scans **up to** that ceiling and
records, per order, a count of shared features:

| order | what is compared | how | line |
|---|---|---|---|
| 0 | concept **names** | `set(re.findall(r"[a-z]{3,}", name))` intersection | `:286-292` |
| 1 | `category` equality + concept **definitions** | string equality, then token-set intersection with a hard floor `len(common) >= 3` | `:294-308` |
| 2 | `FunctionalRole` vocabulary hits | `_vocab_hits`, a Rust `Exists`/`StringIndexOf(name + " " + definition, kw) >= 0` **substring** test | `:310-319` |
| 3 | `ShapePrinciple` vocabulary hits | same `_vocab_hits` | `:321-330` |
| 4 | `MetaShape` hits | order-3's principle set, then **any one** shared `has_principle` neighbour lights the shape | `:332-341`, `:117-130` |

The verdict is two derived quantities: `top_order = max(per_order)` (position on
the abstraction axis) and `feature_count = per_order[top_order]` (count at that
position). `features_total` is the `min_score` floor only.

**Every one of the five orders is a set overlap of strings.** Orders 0-1 overlap
raw tokens; orders 2-4 overlap the names of vocabulary entries whose *own*
keywords were substring-matched against a flat concatenation of the concept's
`name` and `definition`. The concept's typed slots are concatenated away before
scoring, and nothing at any order consults a relation.

Two downstream consequences that are part of the same defect:

* `emit_analogy_as_graph:379-387` writes a real `implements` **edge into the
  graph** when `order_n >= 2`, with the comment *"Lower-n matches are
  coincidence; n >= 2 indicates genuine structural correspondence."* That is a
  hand-set ordinal asserting a structural correspondence that was never
  computed — the audit's own words.
* `find_analogies` returns every pair above `min_score` (default 1), and
  `think_harder` emits the top 50. **There is no path by which this faculty
  says "no clear analogy here."** One shared vocabulary hit — including a
  wholly spurious one, see §2.2 — is an analogy with a rationale that reads
  *"shared functional role: input_output"*.

### 1.1 Every caller (AR1)

| caller | uses | note |
|---|---|---|
| `scripts/jabberwock_reads_looos.py:143` | `find_analogies` n=4,3,2 | **already hand-patches this faculty's defect**: it drops `input_output` with the comment *"the substring 'io' spuriously matches every '-tion' word (distor-tion / segmenta-tion)"* |
| `scripts/jabberwock_reads_shape_contexts.py:118` | `find_analogies` n=4,3,2 | same shape |
| `scripts/jabberwock_designs_runner_brain.py:120` | `find_analogies` n=4 | produced the seven-meta-shape decomposition now frozen in `seeds/seven_meta_shape_subsystems.json` |
| `scripts/jabberwock_reads_cognitive_models.py:24` | `_concept_functional_roles`, `_concept_abstract_principles` | direct order-2/3 readers |
| `tests/test_analogical_relative_ranking.py` | `find_analogies`, `emit_analogy_as_graph` | the standing gate: **`order_n` is primary, `feature_count` is the within-order tiebreak, no absolute `score`** |
| `tests/test_reframing_proposer.py:188` | `shape_hits` | asserts specific meta-shapes are read off specific prose |
| `tests/test_frame_manifold.py:201` | `metashape_realisation_counts` | |
| `scripts/meta_shape_first_class_probe.py:171` | `shape_hits`, `metashape_realisation_counts` | the previous rung's AR4 consumer check |
| `scripts/jabberwock_builds_comprehend_verify.py:50` | `shape_hits` | |

**Contract this rung must preserve:** the returned dict keys
(`source_concept`, `target_concept`, `source_mt`, `target_mt`, `source_node`,
`target_node`, `order_n`, `feature_count`, `features_total`, `rationale`), the
absence of a `"score"` key, and `order_n`-primary ranking.

*(Found in passing, not this rung's charter: `jabberwock_reads_looos.py:145` and
`jabberwock_reads_shape_contexts.py` still read `a["score"]`, a key deleted when
ranking was made relative. Both raise `KeyError` on the second candidate for a
claim. Pre-existing, reported, not repaired here.)*

---

## 2. THE REGISTERED BEFORE (read-only, measured on `d239b7c`)

Full `load_all_seeds` boot: 690 seeds, 25,019 nodes, 11,594 edges,
**10,775 `Concept` nodes**, 481 `Microtheory` nodes, 205 microtheories carrying
concepts (median 26 concepts each).

### 2.1 The population has no relational structure — and this decides the design

| measured | |
|---|---|
| `Concept` nodes | **10,775** |
| …with **≥1 outgoing edge of any type** | **114 (1.06%)** |
| `Concept -*-> Concept` edges, whole graph | **190** (`built_from` 40, `depends_on` 32, `grounds` 32, `subtype_of` 30, `expects_response` 9, `demonstrates` 5, `is_a` 4, `preferred_over` 3, `has_property` 3, `enables` 2, `requires` 2) |
| incoming edges to `Concept` | 6,312 × `has_concept` (the Mt membership edge) + 179 everything else |
| attribute keys present (4,000-concept sample) | `name` 4000, `definition` 3819, `domain` 3808, `category` 2244, `why` 736 |

**The audit's charge — "never consults a concept's edges" — is a correct
diagnosis of the code and a dead end as a prescription.** 98.9% of this
population has no edge to consult. A verdict built on relational alignment
would return *no evidence* for essentially every pair, which is not a fix.

### 2.2 The surface matcher is not merely cheap — it is wrong about half the time

`_vocab_hits` runs `StringIndexOf(text, keyword) >= 0` — an **unanchored
substring** test — against `name + " " + definition`. Re-scored read-only over
all 10,775 concepts × all 30 vocabulary entries, comparing the live test against
the same keywords anchored at a **token start**:

| | |
|---|---|
| concept × vocabulary-entry hits, live (unanchored substring) | **14,281** |
| the same, anchored at a token start | **7,553** |
| **hits that exist only because a keyword matched inside a word** | **6,728 — 47.1%** |
| concepts carrying ≥1 wholly-spurious vocabulary hit | **5,925 — 55.0%** |

Worst offenders, with real examples from the live graph:

| vocabulary entry | keyword | spurious hits | e.g. |
|---|---|---|---|
| `FunctionalRole input_output` | `io` | **5,650** | `operat`**`io`**`n_primitive`, `satisfact`**`io`**`n_fold` |
| `ShapePrinciple spatial_motion` | `posit` | 386 | `com`**`posit`**`ion pattern` |
| `FunctionalRole synchronize` | `sync`, `lock` | 165 | `a`**`sync`**`hronous`, `c`**`lock`**`wise` |
| `FunctionalRole integrate` | `synthesi`, `integrat` | 88 | `photo`**`synthesi`**`s`, `re`**`integrat`**`ion` |
| `FunctionalRole learn` | `train` | 86 | `cons`**`train`**`t` |
| `FunctionalRole gating` | `gate` | 65 | `ag`**`gregate`**`s` |
| `ShapePrinciple hierarchical_abstraction` | `layer` | 65 | `p`**`layer`** (`nash_equilibrium`, `zero_sum_game`) |

The `io` row is the one to stare at. It is **39.6% of every vocabulary hit in
the graph**, and it is already documented *inside this tree* — by a caller that
had to hand-patch around it (`jabberwock_reads_looos.py`, §1.1). The faculty's
own consumers know it is broken.

### 2.3 Order 4's meta-shape test is a 1-of-N disjunction

`_concept_meta_shapes` lights a `MetaShape` when **any one** of its
`has_principle` neighbours is in the concept's principle set. Seven of the
eleven shapes have exactly one principle, so for those, order 4 is a rename of
order 3. For the four multi-principle shapes it is a strict weakening: half the
evidence claims the whole shape, and order 4 then **outranks every lower order
outright** under the standing `order_n`-primary rule.

---

## 3. The registered design (AR2) — decided before building, from §2

### 3.1 COMBINATION, not replacement — and why

The brief permits either, conditional on measurement. §2.1 decides it:
**a structural verdict alone has almost nothing to read on this population.**
So the surface signal is kept — demoted to what MAC/FAC says it is, a **recall
filter** — and a genuine structural stage is added **as the verdict**. Replacing
it would delete the faculty's only recall mechanism.

This mirrors, independently, `RULE_SIGNATURE_SLICE_RESULTS.md`'s own finding
that structural and name-keyword selection are not strictly ordered. Here the
reason is different and sharper: not "both carry information", but "**one of
them has no input**".

### 3.2 PER-ORDER, not uniform

| order | treatment | why |
|---|---|---|
| 0, 1 | **unchanged** | honestly-labelled surface similarity, and the only recall floor there is. Registered explicitly so the results doc cannot claim credit for them. |
| 2, 3, 4 | vocabulary matching becomes **token-anchored** and **slot-addressed** | §2.2. A keyword matches at a token START (so `io` no longer matches `operation`), and *which slot it hit* is retained instead of being concatenated away — the exact information `META_SHAPE_FIRST_CLASS_RESULTS.md` §2 restored one grain up. |
| 4 | additionally reads a `MetaShape`'s structural `signature` via held **`Covers`** when one exists, else the `has_principle` disjunction | the previous rung made minted `MetaShape`s carry real anti-unified signatures. **Registered prediction: dormant on the eleven seeded shapes, which carry no `signature`** (`META_SHAPE_FIRST_CLASS_RESULTS.md` §3a). Wired anyway, same discipline as that rung's rung-3. |

**Evidence tiers, never a weighted sum** (the META_SHAPE precedent): a
vocabulary hit landing in the concept's own `name` slot is stronger evidence
than any quantity of hits buried in `definition` prose. An item whose *slot is*
the shape beats an item that merely talks about it.

### 3.3 The FAC stage: systematicity via `AntiUnifyWitness` — and the registered NO-GO on the naive transplant

**Registered NO-GO, stated up front because the brief asked me to verify rather
than assume:** `AntiUnifyWitness` applied to a *single pair's* concept signature
adds **nothing** over the set intersection already there. The operator
generalises element-wise over equal-length tuples; aligning two concept
signatures by predicate makes the predicate correspondence the *identity map*,
so the template's fixed leaves are exactly "the attributes that are equal" —
which is `category == category`, i.e. order 1. The values are opaque prose, so
no reusable transform exists inside one pair. **The naive per-pair transplant of
`RULE_REFERENCE_LAYER_SIZING_RESULTS.md` §4 does not transfer to this
population, and the results doc must report this whether or not the rest lands.**

**Where the operator does earn its place is exactly where §4 used it: ACROSS
pairs.** §4's parallelogram is `AntiUnifyWitness` over corners *a* and *b* to
extract a transform **T**, then `Substitute` **T** onto *c*. The same object at
the concept grain: a candidate pair `(A_src, B_tgt)` induces a transform
σ — the witness residue between the two concepts' shape signatures — and a
*different* pair `(C_src, D_tgt)` in the same microtheory bridge induces its
own. **When two pairs induce the SAME σ, they are the two corner-pairs of one
parallelogram, and each corroborates the other.** That is Gentner's
systematicity, computed rather than asserted, and it is information no
per-pair scorer of any sharpness can produce.

`corroboration(pair)` := the number of *other* candidate pairs in the same
Mt-bridge whose held `AntiUnifyWitness` template is identical. Computed by held
Terms (`AntiUnifyWitness` → `FixedCount`); Python assembles inputs and reads
outputs, decides nothing.

### 3.4 Ranking, and the deleted false-confidence claims

**Ranking key** (tiers, no sum):
`(-order_n, -corroboration, -slot_tier, -feature_count, -features_total)`.

`order_n` stays primary. That is the *previous* rung's registered and gated
finding (`test_analogical_relative_ranking.py`) and this rung does not
relitigate it; corroboration is the **within-order** discriminator, which is
precisely where MAC/FAC puts structure.

**Two false-confidence claims are deleted, per the META_SHAPE precedent that a
verdict which always answers can never produce a residual:**

1. `emit_analogy_as_graph`'s `implements` edge stops being written on the
   `order_n >= 2` ordinal and is written **only when structural corroboration
   was computed and is positive**.
2. A pair whose *entire* evidence is a prose-slot vocabulary hit with **zero
   corroboration** returns **`None`** — an honest non-answer — instead of an
   analogy whose rationale asserts a shared functional role.

### 3.5 Rust

**Registered prediction: ZERO new Rust.** `AntiUnifyWitness`, `FixedCount`,
`Covers`, `Exists`, `StringIndexOf`, `Gte`, `Eq` all exist and are all reachable
from `native.evaluate`. The token anchoring is expressible as
`StringIndexOf(haystack, kw) == 0` over a mechanically-built list of
token-boundary suffixes — a *different argument* to an existing Term, not a new
Term. If this prediction fails it will be reported as a failure, not
retro-fitted.

`domains/analogical_thinking.py` stays a mechanical adapter: it builds
signatures by destructuring, hands them to held Terms, and reads verdicts back.
No Python function judges structural similarity.

---

## 4. Bars

| bar | GO iff |
|---|---|
| **AR1 — investigation** | the five orders are documented from the code (§1), every caller enumerated (§1.1), and the population's compatibility with `AntiUnifyWitness`/`Substitute` **verified, not assumed** — including a negative verdict where one is warranted (§2.1, §3.3) |
| **AR2 — design registered before building** | §3, built as written; every deviation reported in a deviations table |
| **AR3 — live demonstration** | a curated set where the current scorer is WRONG or over-confident and the fix gives a correct answer or an honest non-answer, **plus** the broadest sweep the real population allows. Specifically: (a) the `io`-class spurious hits vanish; (b) at least one real cross-Mt pair flips or is withdrawn; (c) the honest non-answer fires on at least one pair the old code scored |
| **AR4 — no regression** | every test file touching `analogical_thinking` / `find_analogies` / `shape_hits` / `metashape_realisation_counts` run BEFORE and AFTER, reported as **paired failing node-id LISTS, never counts** (CLAUDE.md's retracted-baseline rule) |

## 5. Registered risks

1. **Blast radius of anchoring `_vocab_hits`.** `shape_hits`,
   `metashape_realisation_counts`, `_run_self_shape` and
   `jabberwock_reads_cognitive_models` all read it. §2.2 says ~47% of hits will
   disappear — **by design, they are wrong** — but a consumer test asserting a
   specific shape is read off specific prose may legitimately flip.
   `tests/test_reframing_proposer.py:188` is the named at-risk gate. If it
   flips, the flip is reported and adjudicated on the merits of the individual
   case, not silenced.
2. **Corroboration may be 0 everywhere on small bridges.** A 6-concept ×
   6-concept bridge may contain no two pairs sharing a transform, making the new
   tier inert. Registered as a real possible null.
3. **The honest-`None` rule may empty a caller.**
   `jabberwock_designs_runner_brain.py` produced a decomposition now frozen in a
   seed. If withdrawing spurious analogies changes that output, the change is
   reported; the seed is **not** edited by this rung.
4. **`order_n`-primary may be the wrong primary.** Corroboration is arguably
   better evidence than axis position. Not relitigated here: it is another
   rung's registered, gated result. Named as a limit, not fixed.

## 6. Explicitly out of scope

`domains/reflective_faculty.py` (concurrently owned), `domains/rule_signature.py`,
`runners/dsl/src/py.rs`, `substrate/world_adapter.py`,
`seeds/shape_vocabulary.json`'s *content* (the keyword lists themselves —
anchoring changes how they are matched, not what they are), the frozen
`seeds/seven_meta_shape_subsystems.json`, and the `a["score"]` `KeyError` in the
two reader scripts (§1.1).
