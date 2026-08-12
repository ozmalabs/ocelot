# Codebook partition consolidation — PREREG

**Registered:** 2026-08-12, before any file in the tree was modified.
**Worktree:** `/home/matt/ocelot-codebook-partition-consolidation`, branch
`codebook-partition-consolidation`, detached from `main`@`2b271bc`.
**Charter:** `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.4(a) — *"The codebook is partitioned
two different ways at once."* Fifteen `ShapeSignature*` node types, plus a `kind` attr,
plus 87 seed sites naming `"codebook_type": "ShapeSignature"` and ~30 naming other types.
The spike calls this an instance of `SHAPE_AUDIT.md`'s **sixth pattern** — *"the same
enumeration written twice, with nothing deriving one from the other."*

---

## 0. What this rung is, and what it is not

It is **not** "merge the fifteen types." It is **not** "leave it alone." It is:
*decide, per type, from read code and measured seed data, whether the separation is
load-bearing; then fix exactly the subset the evidence supports, and name the rest.*

Per this tree's standing culture, **a NO-GO or a two-type slice is a complete result**
if that is what the evidence says. The registered bars below are written so that
"nothing should be consolidated" is a reachable, reportable verdict, not a failure.

---

## 1. The registered question, sharpened

The spike's phrasing assumes the two partitions serve the **same need**:

> "it is the **same need** `kind` exists to serve, and the tree serves it both ways
> with nothing saying which to use when."

That assumption is itself under test here. Before any consolidation can be sized,
one mechanical question must be answered from the code, not from the doc:

**Q. Is `kind` a partition mechanism at all, or only a label?**

If `kind` never scopes a decode, then "the tree serves the same need both ways" is
false, and the whole framing of §3.4(a) inverts: there would be exactly **one**
working pool-partition mechanism (the node type) and one **inert restatement** of it
(the `kind` attr) — which is still the sixth pattern, but with the opposite fix.

---

## 2. Registered bars

### AR1 — per-type justification audit

For **each** of the 15 `ShapeSignature*` types, a verdict from evidence:

* **J (justified)** — separation is load-bearing: removing the type would change
  a decode result, demonstrably.
* **R (redundant)** — separation changes nothing mechanical; the type is doing
  documentation work a `kind` attr already does.
* **N (not a codebook)** — the type is named `ShapeSignature*` but its nodes are
  never loaded by `load_parts` at all.

Evidence required per verdict: (a) predicate vocabulary + relation-arity of the type's
`signature` attrs, measured over `seeds/*.json`; (b) every `codebook_type` site that
points at the type (seed rule bodies AND Python `native.evaluate` shims — both,
since the audit found the reading faculties supply `codebook_type` from Python
constants, not seed data); (c) the type's own stated reason where one exists in a
docstring or seed note, quoted.

**Registered in advance:** the verdicts are per type. A mixed outcome (some J, some R,
some N) is the expected shape and is reportable as-is. No target count.

### AR2 — the mechanical question, answered from the code

Read `shape_decode.rs::load_parts` and every filter parameter `ShapeDecode` /
`TransformDecode` / `DimInfer` accept, and state precisely:

1. Does any decode Term scope its candidate pool by the `kind` attr? Yes/No, with the
   line that decides it.
2. What filters DO exist, and what is each keyed on?
3. If `kind`-scoping does not exist: is it trivially buildable (a `kind` param on
   `load_parts`), and what would it cost?

**Pass condition:** the answer is stated with the line numbers that establish it and
is confirmed by a **live probe** — a decode over a two-`kind` population, showing
whether the foreign-`kind` entries are or are not candidates.

### AR3 — GO/NO-GO on consolidation, at a scope the evidence sets

Registered **decision rule**, fixed now, before the deciding measurement:

* A type is **consolidation-eligible** only if ALL of:
  1. AR1 verdict is R or N (not J);
  2. no `codebook_type` site anywhere points at it (seed or Python);
  3. a live before/after decode over the real seed data returns **identical**
     results with the type merged into `ShapeSignature{kind:...}`.
* A type with AR1 verdict **J stays separate**, and the RESULTS doc must state its
  reason in one sentence a reviewer can check.
* If clause 3 fails for a candidate — even one whose predicates look disjoint — that
  type is **NOT consolidated**, and the failure is reported as the finding.
* **NO-GO in full** is the verdict if clause 3 fails for every candidate, or if the
  blast radius (files touched × sites) exceeds what one rung can gate.

### AR4 — the ~30 other `codebook_type` names, categorized

Every non-`ShapeSignature` `codebook_type` value in the tree, each placed in exactly
one bucket, with the reason:

* **same-grain-redundant** — its parts share predicate vocabulary with the
  `ShapeSignature` pool and it could be a `kind` of it;
* **genuinely-different-grain** — its parts carry a different content shape
  (the `MetaShape` precedent: WILD-slotted lgg patterns, not literal parts —
  `META_SHAPE_FIRST_CLASS_RESULTS.md` §3(b)), or different reader semantics;
* **not-a-codebook** — never read by `load_parts`.

### AR5 — fixes applied, live before/after

For anything shipped: a probe over **real seed data** that shows the pre-change and
post-change decode returning the SAME recognition results. Behaviour-preserving is a
gate, not an aspiration. **If it cannot be shown, the change is not shipped** —
per the charter's own constraint.

### AR6 — regression, as node-id LISTS not counts

Per `CLAUDE.md`'s retracted-baseline rule (*"A BASELINE MUST BE A LIST OF NODE IDS,
NEVER A COUNT OR A CHARACTERISATION"*): a real sweep across the sd-loop /
decode / recognize / ink / reading-faculty suites, before and after, reported as
paired **lists** of failing node ids. Any id red after and not before is a regression
and blocks the change.

---

## 3. Registered risks

1. **Predicate disjointness is empirical, not enforced.** Two pools whose predicates
   do not overlap today can be merged without changing coverage — but `ShapeDecode`
   ranks candidates by `(covered DESC, shape_fit DESC)`, and `shape_fit` is an
   `AntiUnify`-based score that is **not** gated on predicate match. A foreign part
   could therefore still win a zero-coverage contest on fit alone. AR3 clause 3 exists
   specifically to catch this; it is registered as the most likely reason a
   plausible-looking merge fails.
2. **`codebook_type` is supplied from Python constants**, not only from seed rule
   bodies (`domains/narrative_structure.py:84`, `discourse_coherence.py:96`, …). A
   grep of `seeds/*.json` alone under-counts the live pool sites. Both must be swept.
3. **Seeds are emitted, not hand-edited.** Any migration must go through whatever
   emits the seed. If a seed has no emitter, that is itself a finding to report,
   and hand-editing it is grounds to reduce scope rather than proceed.
4. **The blast radius may exceed one rung.** 87 + ~30 `codebook_type` sites and 682
   `ShapeSignature*` node declarations. A NO-GO or a 2-type slice is registered in
   advance as an acceptable, complete outcome.

---

## 4. Out of scope, explicitly

* `domains/analogical_thinking.py`, `domains/reflective_faculty.py`,
  `domains/rule_signature.py`, `runners/dsl/src/py.rs`,
  `substrate/world_adapter.py`'s checkpoint-load region, `seeds/meta_shape_growth.json`
  — owned by other threads today.
* Any change to what gets recognized as what. This rung is a refactor of
  representation only.
* Building a `kind`-scoped decode filter in Rust **unless** AR2 shows it is both
  absent and necessary to a GO verdict. Adding an unused engine parameter is exactly
  the "scalar knob standing in for a shape" failure `CLAUDE.md` warns against.
