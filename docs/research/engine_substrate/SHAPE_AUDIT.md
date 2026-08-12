# SHAPE AUDIT — an inventory of where a name, a length, a table or a number stands where a shape belongs

**Status: INVENTORY. No code, no seeds, no tests, no builds in this rung.** One
new file; nothing else in the repository is touched. Written against `main` at
`abae030` — **note that this is one merge later than the tip the brief named**
(`f4f29b3`); `abae030 Merge rule-signature-slice` landed between the brief being
written and this sweep starting, and §2.1 below depends on what it did and did
not change, so the discrepancy is load-bearing rather than cosmetic.

**Every claim below is grounded in code I read.** Grep hits that I did not open
are not reported. Where a candidate was checked and rejected, the rejection is
recorded with its reason — the rejections carry as much of this document's value
as the findings, because the failure mode this audit is most exposed to is
pattern-matching on a grep signature and calling it a defect.

---

## 0. The honest summary, in one paragraph

Today's two rungs found the same root defect twice — once in the Rule layer
(`RULES_AS_SHAPE_DESIGN_SPIKE.md`: a rule's shape is literally its *name*) and
once in the chunk layer (`PROGRAM_SYNTHESIS_CHUNK_EQUIVALENCE_RESULTS.md`:
`covers_value` demands equal-length relation lists). **It is not twice. Across
this sweep it is at minimum forty confirmed sites, and the single most
prevalent form is Pattern A — selection by name.** The `overlap = Sum(words,
"w", Ite(Gte(StringIndexOf(Attr(n, "keywords_text"), w), 0), 1, 0))` lambda that
`_pick_acting_rule` uses is **copy-pasted into six distinct self-modification
decision sites in `domains/reflective_faculty.py`, plus three graph-resident
twins in `seeds/composer_experiment_graph.json`** — it decides which *rule* to
vary, which *seed* to ablate, which *edit operator* to apply, which *numeric
belief* to shift, and (in `seeds/variation_ops.json`) which dispatch route an
unknown verb gets, the last of these by counting **shared letters**. Two further
findings I consider more consequential than any single Pattern A site, because
they are absences rather than defects: **the agent's meta-shape vocabulary is a
closed, hand-authored 11-entry table with no mint path anywhere in the tree**
(`seeds/shape_vocabulary.json` — the sd loop's fourth rung is not wired to the
faculty named "shape"), and **454 of 634 rule-carrying seed manifests declare
zero Γ productions, 159 of which mint edges from rule effects** — the
bigville/humanoid finding CLAUDE.md already names, generalised from four seeds
to the whole corpus. Pattern C turned out to be the pattern with the sharpest
*consequences* rather than the largest count: the Γ checkpoint-reload growth bug
fixed one commit before this baseline (+261 nodes/cycle, no convergence) is
exactly it, and **two unfixed siblings of the same shape sit in
`substrate/world_adapter.py`** — `learn_recursive_concept` and `learn_word` both
mint a duplicate `Concept` plus a duplicate definition subgraph on re-teach,
with `_concept_by_name`'s first-match scan then returning the *stale* one while
the evaluator reads the new one. The one thing this audit did *not* find is any new
count-divided seed-level learner outside the documented embodied 60; what it
found instead is that the same shape moved **into the Python adapters that wrap
the clean faculties** — `interlocutor_model.py` reproduces the F-16 regress
line-for-line (`1/n` → `max(0.05, …)`) inside the conversation faculty CLAUDE.md
holds up as clean, while `shape_decode.rs` and `space_quantize.rs` are, verified,
genuinely threshold-free.

---

## 1. Method, scope, and what is deliberately excluded

**Method.** Signature-driven grep over `runners/dsl/src/` (84 files), `domains/`
(727 files), `seeds/` (892 manifests), `substrate/`, `tools/build_*.py` and
`scripts/`, generating candidates; then each candidate read in place before
being reported. Breadth was prioritised over depth per the brief — today's two
rungs already did depth on Rules and chunks. Four parallel sweeps (one per
pattern family) examined roughly 150 candidates and rejected the majority;
**I personally read and verified 38 of the sites reported below, and personally
found 9 of them.** Where a finding
came from a sweep and I verified it, it is marked *(verified in place)*; where I
report a sweep's finding on its own reading, it is marked *(sweep, not
re-verified)* and ranked lower accordingly.

**Two corrections to sweep output, made during verification, recorded because
they show the failure rate of unverified candidates:**

* A sweep reported `domains/reason.py`'s `CAPABILITIES` (73 rows) and
  `COMPLEXITY` as drifted — 73 vs 65. **False.** My first count reproduced it and
  was also wrong: both regexes missed multi-key lines (`"even": lambda a: 1,
  "odd": lambda a: 1,`). Counted properly, both tables are **73/73 and in exact
  sync today.** The finding survives only in its weaker, honest form (§6.4).
* A sweep concluded "the entire repo is one commit, so no growth evidence
  exists anywhere." **Partly false**: there are 77 commits, but only 17 touch
  `seeds/` and `git log --follow` returns a single "Initial import" commit for
  most individual files. The conclusion (no per-file growth history) holds; the
  premise did not. **Consequence for this whole audit: no Pattern D finding
  below can cite git history as evidence of growth.** Growth evidence is
  textual only — accretion comments, arc labels, and self-documenting
  maintenance instructions.

**Explicitly excluded, per the brief and per CLAUDE.md:**

* CLAUDE.md's already-documented **60 count-divided `1/n` learners across 8
  embodied seeds** (F-16 / humanoid / bigville). Not re-derived, not
  re-reported; referenced for context only. All `seeds/*motor*`, `*humanoid*`,
  `*helicopter*`, `*embodied*`, `*driving*`, `*walker*`, `*f16*`, `*flight*`,
  `*bigville*`, `*lever*`, `*doom*` were held out of the Pattern E sweep.
* `scripts/jabberwock_daemon.py`'s `if kind == "code_write":` routing — CLAUDE.md
  sanctions it explicitly as *"a name-keyed registry lookup on the Term's
  verdict."*
* The twelve `_compose_*_rule` Python builders — CLAUDE.md: *"legal: they only
  assemble Rule JSON."*
* The 19 `composer_*_graph.json` seeds and `_pick_acting_rule` itself — already
  named in `RULES_AS_SHAPE_DESIGN_SPIKE.md` §2.5 / §7.1 as instances of this
  pattern. They appear below only as calibration anchors, and where a *sibling*
  site in the same family was not previously named, that sibling is the finding.
* `tests/*` numeric literals. An assertion is supposed to be literal. Test
  constants appear below only as evidence that a production constant is
  *pinned*.

**One methodological note on Pattern B.** The chunk-equivalence rung set the bar:
it found one genuinely-provably-safe rewrite, measured its prevalence at zero,
and declined. I have applied the same bar — a Pattern B candidate is only
reported where I can name two things that would *actually occur in this system*
and *actually matter*. Three candidates were rejected on exactly this ground and
are listed in §3.4.

---

## 2. Pattern A — selection/ranking by string/name, not structure

**The most prevalent pattern in the codebase, by a wide margin.** 16 confirmed
sites; 9 of them govern a self-modification decision.

### 2.1 The `keywords_text` family — one lambda, six self-modification decisions (VERIFIED IN PLACE)

`RULES_AS_SHAPE_DESIGN_SPIKE.md` §2.5 named *one* call site. There are **six in
`domains/reflective_faculty.py` alone**, plus three graph-resident twins in
seed data that would survive a Python-only fix. All share the identical scorer:

```python
overlap = lambda node_t: Sum(words, "w",
    Ite(Gte(StrIdx(Attr(node_t, "keywords_text"), V("w")), L(0)), L(1), L(0)))
```

| # | site | what it selects | scored against |
|---|---|---|---|
| A1 | `reflective_faculty.py:2704-2765` *(the known calibration case)* | which **rule** to vary | `RuleSummary.keywords_text` = `name.replace("_"," ")` |
| A2 | `reflective_faculty.py:2963-3006` (`_pick_reply_rule`) | which **conversational rule** to ablate | same, `writes_reply` pool |
| A3 | `reflective_faculty.py:4183-4196` | which of **888 seeds** to disable in a live self-experiment | `SeedSummary.keywords_text` |
| A4 | `reflective_faculty.py:3909-3999` (`_EDIT_OPS`) | which **edit operator** rewrites the rule | a hand-written synonym blurb per op |
| A5 | `reflective_faculty.py:3240-3262` | which **numeric belief** to shift | the Python attribute *identifier*, `_`-split |
| A6 | `reflective_faculty.py:3532-3560` | which **(rule, where-literal)** pair to edit | identifier spellings inside the comparison subtree |
| A7-A9 | `seeds/composer_experiment_graph.json:1127, 1366, 4712` | the graph-resident twins of A1, A4, A3 | same |

**A3 is the one I would flag first for severity.** `SeedSummary.keywords_text`
is built by `substrate/boot_all.py:190-215` as *the seed id's words + every rule
name split on `_` + every RelationCue keyword + concept names + the first 40
words of the description*. So the agent decides **which of its own 888 seeds to
switch off in a live experiment** by counting how many of a capability axis's
residual predicate words appear as substrings of that seed's filename, rule
names and blurb. What should be compared is what the seed's rules structurally
*do*; what is compared is a bag of its identifiers.

**A4 is the sharpest illustration of the MAC/FAC diagnosis** that
`RULES_AS_SHAPE_DESIGN_SPIKE.md` §4.2 imported from the creator's June grounding
doc. The comment directly above `_EDIT_OPS` (`reflective_faculty.py:3900-3907`)
says: *"WHERE (the site) is then read off the PICKED op's own structural scan of
the picked rule (find_comparison_nodes / find_attr_keys)."* **The structural
machinery is right there, and it runs only after the name-keyword Argmax has
already decided which operator to use.** A FAC stage exists; it is not used for
the selection, only to execute it.

**A5's failure mode is concrete and cheap to state:** it splits the *Python
attribute key* on `_`, counts word hits against the concern text, and requires
`overlap >= 2`. A belief stored as `confidence` and one stored as
`self_report_reliability` are compared by the spelling of their keys, not by
which rules read them — and `RuleSummary` already carries a `reads_text` field
that answers exactly that question and is not consulted.

**Severity: live, currently biting, and now measured.** The
`abae030` merge landed `domains/rule_signature.py` — the spike's §11.2 slice,
a path-addressed alpha-renamed `where`-clause signature — and *measured* that
structural and name-keyword picks disagree: Class A (concern words present in a
rule's `where` but not its name) structural **11/12** vs name-keyword **0/12**.
But that module's own docstring is explicit: *"It is never imported by
`reflective_faculty.py` … production rule selection is byte-unchanged by this
slice."* **A1–A9 are all still live in production, with a measured better
alternative sitting unwired beside them.** That combination — defect confirmed,
replacement built, not connected — is what makes this the cheapest finding in
the audit to act on.

### 2.2 `seeds/variation_ops.json:152` — route selection by shared LETTERS (VERIFIED IN PLACE)

The worst instance found anywhere. The `cue_route_pick` Program is evaluated
with the environment `{"verb": verb, "chars": list(verb)}`
(`reflective_faculty.py:3148`), and its value expression is a `Sum` over
`chars` of `StringIndexOf(Attr(c, "name"), ch) >= 0` — i.e. **an Argmin ranked
by how many of the verb's individual characters appear anywhere in a candidate
Concept's name.**

This decides which dispatch route (`world_action` vs `comprehend_text`) an
unrouted instruction verb is proposed for — the agent closing its own
instruction-coverage gap. `"drop"` and `"prod"` score identically. The seed's
own description at line 13 states it plainly: *"scored by character overlap with
the gap verb (a v1 held similarity)"*, and `reflective_faculty.py:3164` renders
it to the human as *"character-overlap Argmax over the route Concepts"*. It is
honestly labelled and still a letter-bag standing where the verb's argument
structure belongs. **Severity: live, low blast radius (one proposal path), high
diagnostic value.**

### 2.3 `seeds/composer_dispatch.json` — the priority IS the insertion index (VERIFIED IN PLACE, MINE)

CLAUDE.md sanctions the *Python* half of composer dispatch (*"Python does a
name-keyed registry lookup on the Term's verdict"*). **The verdict itself is not
sanctioned and is Pattern A + E.** The held `composer_pick` Program is:

```
Attr(key="composer",
     Argmin(Filter(NodesOfType("ComposerCue"), c, In(c.relation_head, heads)),
            x, x.priority))
```

— an exact string membership test of the concern's relation heads against 24
hand-written `relation_head` words, tie-broken by a hand-assigned integer
`priority`. Reading all 24 rows: **the priorities run 1, 2, 3, …, 23 with no
gaps and exactly one duplicate (5, shared by `communicate`/`decompose`). The
priority is the order the rows were added.** A composer added tomorrow gets 24
and loses every tie against everything already present, for no reason but
arrival time.

The contrast is available two files away: `sd_recognize`
(`seeds/shape_decode_loop.json`) ranks its candidates by
`FixedCount(AntiUnify(obs.signature, sig.signature))` — a *derived* specificity.
Here the same job is done by an asserted ordinal. **Severity: live; latent
correctness risk that grows monotonically with the number of composers.**

### 2.4 `domains/analogical_thinking.py` — the June diagnosis, still uncorrected at its original site (VERIFIED IN PLACE, MINE)

`RULES_AS_SHAPE_DESIGN_SPIKE.md` §4.2 imports the creator's June diagnosis of
`find_analogies` (*"the agent's bucket IS the MAC stage treated as the verdict —
with no FAC stage"*) and applies it to the rule layer. **I checked whether the
original site was ever fixed. It was not.** `_compute_analogy`
(`analogical_thinking.py:252-361`) computes, at every one of its five
abstraction orders, a **set overlap of string tokens**:

* n=0 — `_tokens(source_name) & _tokens(target_name)` (`:286-290`)
* n=1 — `category == category` plus `_tokens(defn) & _tokens(defn)` with a
  hard floor `len(common) >= 3` (`:297-306`)
* n=2/3/4 — `_vocab_hits(...)`, which is `StringIndexOf(name + " " + definition,
  keyword) >= 0` against a seeded keyword list (`:72-114`)

**Not one of the five orders consults a concept's edges.** The two concepts'
relational structure — the thing structure-mapping is *about* — is never
compared. Then `emit_analogy_as_graph:382` writes an `implements` edge into the
graph when `order_n >= 2`, with the comment *"Lower-n matches are coincidence;
n >= 2 indicates genuine structural correspondence"* — a hand-set ordinal
asserting structural correspondence that was never computed. **Severity:
medium-live** (this faculty is reachable via `think_harder` and the
`analogical_thinking` route, but I did not measure how often it fires on the
daemon).

### 2.5 `recognise_meta_shape` — the shape faculty recognises shape by substring, and ties break alphabetically (VERIFIED IN PLACE, MINE)

`runners/dsl/src/shape_decode.rs:5340-5395`. This is the **single shared
scorer** behind both `RecogniseShape` (the `teach` facility's
`categorise_by_shape`, `domains/teach.py:81-101`) and `eval_transfer_decode`
(mechanism transfer). It is:

```rust
let hit = kws.iter().any(|kw| {
    td_val_to_string(kw, ctx.interner).map(|k| text.contains(&k)).unwrap_or(false)
});
if hit { score += 1; }
...
scored.sort_by(|a, b| b.0.cmp(&a.0).then_with(|| a.1.cmp(&b.1)));
```

Three things stack here:

1. The `text` it scores is built by `teach.py:93` as `" ".join(str(v) for v in
   attrs.values() if isinstance(v, str)).lower()` — **every string attribute
   value concatenated, the keys discarded.** The item's typed structure is
   destroyed before scoring.
2. The score is a raw `contains` count over a hand-authored keyword list.
3. `then_with(|| a.1.cmp(&b.1))` — **ties break alphabetically by the
   meta-shape's own name.** `associative_recall` beats `feedback_control` on a
   tie for no reason but the letter `a`.

What it decides: which seed manifest a taught item is persisted into
(`teach.py:152-176`), i.e. the agent's own filing of its own knowledge.
**Severity: live, high** — and it composes with §5.1 below into what I consider
the audit's most consequential finding.

### 2.6 Further confirmed Pattern A sites *(sweep, not re-verified except where noted)*

| site | selects | by |
|---|---|---|
| `domains/investigation_operators.py:77-105` *(verified in place)* | which **Operator** investigates a CapabilityAxis | `sum(1 for kw in op.keywords if kw in " ".join(axis.capability_keys))`; docstring claims *"No decision — a registry lookup"* — it is a ranked selection |
| `seeds/control_kinds.json:461-600` | a `ControlKind`'s **effect_family** | Argmax over signal-words found in `name_lc`, *explicitly instead of* the wiki gloss the kind was grounded from (`scripts/gen_control_kinds_seed.py:11-12` states the choice as a feature) |
| `domains/self_model.py:315-325, 381-390, 449-490` | the self-model's rule/program mirrors | three more `keywords_text = name.replace("_"," ")` minters; `ensure_program_provenance:453` claims a *"structural read"* but flattens op-names and name-words into one haystack |
| `domains/self_model.py:599-620` | **which 12 of N matching rules** the agent reports about itself | `sorted(set(hits))[:12]` — alphabetical |
| `seeds/operational_planning.json:29` | which **OperationalCapability** an instruction clause invokes | token substring hits into a `token_blob` (`StringIndexOf`, so `"act"` matches `"extract"`) |
| `seeds/program_synthesis.json:528` + `domains/code_reading.py:386-414` | which **code-write construction** answers a request | shared trigger-token count; `code_reading._winner:400-402` already names the residual: *"does NOT fix same-kind collisions (two write shapes sharing a generic trigger word)"* |
| `domains/reflective_faculty.py:2016-2040` + browse composer twins | which **hyperlink** to click | goal-word substring hits in `label_lc` (ranked medium — a link's label is arguably its content) |

### 2.7 Rejected as NOT Pattern A

`selector_audit.rs` (determinism diagnostic, no strings); `retire_duplicate_gap`
and `retire_duplicate_residual_concern` (exact-equality dedup with an Argmin
canonical pick, not a similarity rank — though see §3.2); `topic_grounding.py`
title-token overlap (a Wikipedia article legitimately *is* identified by its
title); `self_model.py:527-546 _find_rule_summaries` (**deliberately** exact-match
only, *"never a nearest guess"* — the correct counter-example in the same file);
`conversation_action.py:699` (an arbitrary pick honestly presented as arbitrary);
`cross_text_prior.py:966` / `register_source.py:739` (name as a stable-order
tiebreak *after* a structural primary key); ~20 seed Argmax/Argmin sites where
the string only appears in an `Eq(kind, …)` *filter* and the ranked value is
numeric — boolean gating, explicitly out of scope.

---

## 3. Pattern B — exact/positional matching where equivalence-class recognition belongs

The narrowest pattern, held to the chunk-equivalence rung's own bar. **Three
confirmed; three rejected as speculative.**

### 3.1 The `CapabilityAxis` identity is a first-three-predicates, order-dependent, TRUNCATED string (VERIFIED IN PLACE)

This is the sharpest Pattern B instance in the audit, and it fails in **both
directions**.

`seeds/shape_decode_loop.json`'s `sd_mint_quantum` guards its mint with:

```json
{"type":"Not","arg":{"type":"Exists","source":{"type":"NodesOfType","node_type":"CapabilityAxis"},
 "var_name":"existing_ax","predicate":{"type":"And","items":[
   {"type":"Eq","a":{...existing_ax."induced"},"b":{"type":"Lit","value":1.0}},
   {"type":"Eq","a":{...existing_ax."capability_keys"},"b":{...obs."key"}}]}}}
```

and its effect sets `capability_keys` from `obs.key`, so **the axis's identity
is that key.** And `obs.key` is built, in Python, at
`domains/reflective_faculty.py:1286-1289`:

```python
preds = [st[0] for st in obs if isinstance(st, list) and st and isinstance(st[0], str)]
key = name_hint or (("induced_" + "_".join(preds[:3])) if preds else "induced_concern")
obs_node = sub.add_node("Observation", {"signature": obs, "key": [key], "status": "pending"})
```

**Order-dependent and truncated at three.** Everywhere else in this pipeline a
signature is an order-independent relation *set*: `build_candidate`
(`shape_decode.rs:1589-1591`) canonically sorts both sides with `cmp_value`
before comparing, `ShapeDecode` is a set cover, `AntiUnify`/`FixedCount` score
over sets. Only this key is positional.

**Failure direction 1 — missed match, duplicate axis.**
`induce_concern(agent, [["contains",…],["above",…]])` keys as
`induced_contains_above`; the identical relation system emitted in the other
order — which the decode itself treats as literally the same object — keys as
`induced_above_contains`. A second `CapabilityAxis` is minted with identical
`residual_predicates` and identical `closest_held_shape`. Those two axes then
compete as separate candidates in exactly the `keywords_text` Argmax of §2.1,
which reads `axis.residual_predicates` — so a duplicate mint does not merely
waste a node, it splits one gap's evidence across two axes and changes which
rule gets varied.

**Failure direction 2 — false match, SUPPRESSED mint. This is the dangerous
one.** `preds[:3]` truncates. Two observations agreeing on their first three
predicates and differing in relations 4+ collapse to the same key; the second
matches the guard, `sd_dedup_existing` fires instead, and its **only** effect is
`["set_attr","obs","status","recognized_duplicate"]` — verified directly in the
seed. A genuinely novel shape is silently marked recognised and **never mints.**
That is a growth failure that presents as successful recognition, in the loop
CLAUDE.md describes as the system's sole dynamic-quantization branch.

The fix shape is two lines away in the same pipeline: derive the key from the
canonically sorted, untruncated predicate set, the way `build_candidate` already
sorts before comparing. **Confidence: high on the mechanism (read both the
Python and both seed rules); medium on prevalence** — I did not measure how
often relation order varies or how often first-three collisions occur.

### 3.1b The part codebook dedups by NAME where it must dedup by signature *(sweep, mechanism verified by reading)*

`domains/reflective_faculty.py:7248-7259` (`grow_part_library`) skips an install
when `name in existing`, where `existing` is the *name* set from
`_load_shape_signatures`. `shape_decode.rs:239-247`'s `load_parts` inherits
exactly this, and says so in its own doc comment: *"first occurrence of a name
fixes its ORDER, a later duplicate name only overwrites its VALUE."*

So two Concepts with different names whose `author_signature` extraction yields
the **same relation skeleton** both install as separate codebook parts. This is
not hypothetical: `_bridge_keyword` (`reflective_faculty.py:7283-7290`) already
enumerates synonym clusters mapping to one structural concept
(`"recursion"/"recursive"/"phi"/"golden" → phi_bounded_recursion`). Two
consequences: `sd_recognize`'s `covered_by` `Argmax` becomes an arbitrary
tie-break between two identical parts (no tie rule, `default: null`), and every
duplicate install bumps `codebook_epoch`, re-arming `sd_redecode` across every
decoded observation in the graph for zero information gain.

### 3.2 Gap dedup is exact string equality on free-text `content` (VERIFIED IN PLACE, MINE)

All five gap-minting rules and the retire rule in `seeds/gap_awareness.json`
guard with `Eq(Attr(sc2, "content"), <this gap's content>)` — exact equality on
a natural-language string. Two gaps expressing the same deficiency in different
words are two gaps.

**This is not speculative, and CLAUDE.md documents the workaround without
naming it as one.** The "THE AGENT FIXES ITSELF" section records that
`_topic_facts` strips a leading possessive determiner *"so it files 'reasoning',
not 'your reasoning'"* — i.e. **a hand-written canonicaliser exists in Python
precisely because the dedup downstream is exact string equality.** That is the
same "canonicalize before hash" mechanism the chunk-equivalence rung §3
considered and declined at a different grain, here silently adopted, one
morphological rule at a time. The next surface variant ("my reasoning", "the
reasoning you do") needs the next strip rule. **Severity: live, low individual
impact, but it is the exact regress shape** — each normalisation needs its own
normalisation.

### 3.3 `teach()`'s idempotency is exact dict equality (VERIFIED IN PLACE, MINE)

`domains/teach.py:176-179`:

```python
for n in m["nodes"]:
    if n.get("type") == type_ and n.get("attrs") == attrs:
        return {..., "saved": False, ...}
```

Teaching the same fact with one attribute phrased differently persists a second
node into the seed manifest, permanently. Because `categorise_by_shape` (§2.5)
scores a *concatenation of all string attribute values*, the two near-duplicates
can also land in **different seed files**. **Severity: latent** — I found no
measured instance of this having happened, and the taught-seed population is
small; reported because the mechanism is unambiguous.

### 3.4 Rejected as speculative

Three candidates were dropped for failing the "name two things that would
actually occur and actually matter" bar: `rule_content_hash`
(`substrate.rs:2229-2247`, FNV over the whole serialised body) — already
correctly characterised in `RULES_AS_SHAPE_DESIGN_SPIKE.md` §2.2 as all-or-
nothing identity, and it is *supposed* to be exact (it backs CAS on rule
patches); `anti_unify_values`' equal-length constraint (`term.rs:3341-3355`) —
the mirror of a known finding, not an independent one; and Term-arena
`TermIdx` identity — a performance property, not a matching property.

---

## 4. Pattern C — fresh mint with no canonicalisation against existing content

The spike already established the two canonical instances (`TermArena::add`,
`term_to_subgraph`/`production_to_subgraph`). What this sweep adds is **one
worked example of the pattern actually biting, at production scale, one commit
before this audit**, and its unfixed siblings.

### 4.1 The Γ checkpoint-reload growth bug — Pattern C, measured, at +261 nodes/cycle (VERIFIED IN PLACE, MINE)

`git show f4f29b3` (the merge immediately before this audit's baseline):

> *"The Gamma PyO3 reroute NO-GO found `WorldAdapter.load()` replaying saved
> Gamma productions unboundedly on every checkpoint reload (+261 nodes/cycle, no
> convergence) **once `add_production` genuinely mints graph nodes**."*

That is the spike's §2.2 finding — `production_to_subgraph` mints a fresh
`GammaProduction` + two node patterns + two Term subgraphs per call, with no
find-or-create — cashed out as an **unbounded graph-growth bug in production**.
The fix (`add_production_no_mirror`, a py.rs-only method used solely by
`load()`'s replay) **suppresses the mirror on the replay path rather than making
the mirror idempotent.** The absence of canonicalisation is unchanged; one of
its callers now opts out.

**This is the strongest available evidence that Pattern C is not a latent
tidiness issue.** It is also the reason I rank the remaining C sites higher than
I otherwise would: the same absence, on any other repeated-call path, produces
the same bug.

**The generalisable shape, stated for reuse:** *an index or marker that lives
OUTSIDE the graph decides whether to mint, while the minted content lives INSIDE
the graph and is persisted.* Reload restores the content and not the index, so
the guard opens and the content doubles. Three of the findings below are that
exact shape, unfixed.

### 4.2 `learn_recursive_concept` — the replace path is unreachable across a reload (VERIFIED IN PLACE)

`substrate/world_adapter.py:10113-10131`:

```python
index = getattr(self, "_recursive_concepts", None)
...
cid = index.get(name)
if cid is not None:
    for tgt in list(self.inner.neighbours(cid, "definition")):
        self.inner.remove_edge_unchecked(cid, "definition", tgt)
        self.inner.remove_node(tgt)          # replace: old subgraph freed
else:
    cid = self.s.add_node("Concept", {"name": name})   # UNCONDITIONAL mint
    index[name] = cid
```

I grepped `_recursive_concepts` across the file: it occurs at **10117, 10120,
10135 and nowhere else.** It is not in `save()`'s blob
(`world_adapter.py:6130-6140` writes only `instances / concepts / body_types /
mirrored_edge_types / sensed_types`) and not restored in `load()`
(`:6196-6210`), which also bypasses `__init__` via `cls.__new__(cls)` so the
attribute is absent entirely.

**Concrete failure:** teach `factorial` → save → load → refine `factorial`. The
`else` branch fires, and the graph now holds **two** `Concept{name:"factorial"}`
nodes with two different `definition` subgraphs and two different
`definition_json` attrs. The replace branch — the only thing that ever frees a
stale definition subgraph — is unreachable across a reload, so it compounds once
per save/load cycle. Worse: `_concept_by_name` (`:1615-1621`) returns the
**first** node-order match, i.e. the STALE one, while `eval_recursive`
(`:10135+`) reads the new one. **This is silent divergence, not just growth.**
Everything needed for find-or-create is already graph-resident (the nodes carry
`definition_json`, and `load()` already rebuilds an equivalent index elsewhere
via `_reindex_semiotic_definitions`). **Confidence: high. Severity: live.**

### 4.3 `learn_word` mints unconditionally while holding a persisted index it never reads (VERIFIED IN PLACE)

`substrate/world_adapter.py:9987-9996`:

```python
root = self.inner.add_term_subgraph(definition_term_json)
cid = self.s.add_node("Concept", {"name": name})
self.inner.add_edge_unchecked(cid, "definition", root)
self._concepts[name] = cid
```

Unlike §4.2, `_concepts` **is** persisted and restored (`:6137`, `:6199`) —
`learn_word` simply never consults it. Re-teaching a word mints a second
`Concept{name}` plus a second full Term subgraph; `self._concepts[name]` is
overwritten to the new node while the old one stays in the graph and *wins*
`_concept_by_name`'s first-match scan.

The find-or-create precedent is in the same class, 5,000 lines up:
`_ensure_concept` (`:4308-4315`) is exactly `self._concept_by_name(name) or
add_node`, and `_ensure_world_instance` / `_interlocutor` (`:1623-1628`) follow
it. **`learn_word` is the odd one out.** Confidence: high.

### 4.4 `sd_recognize_dim` mints a `LatentDimension` per OBSERVATION, not per dimension *(sweep, mechanism verified by reading the rule)*

`seeds/shape_decode_loop.json`'s `sd_recognize_dim` effects mint both a
`Transform` and a `LatentDimension{name: "latent:" + <generator>}`, guarded only
by `Count(Neighbours(obs, has_transform)) == 0` — a **per-observation
fixpoint-termination guard, not a dedup.** A `Transform` genuinely is
per-observation data. A `LatentDimension` is a world-model fact:
`latent:rotation90` is the same dimension whichever observation revealed it.

**Concrete failure:** a rotating object observed over N frames mints N
`LatentDimension` nodes, byte-identical whenever two frames land on the same
`k` — which for a 4-cycle generator is every fourth frame by construction.
Downstream readers already assume the opposite:
`tests/test_stereo_infer_migrated.py:71`, `test_time_infer_migrated.py:61` and
`test_depth_infer_migrated.py:66` all filter `nodes("LatentDimension")` by name
and index `[0]`. `Effect::AddNodeIfAbsent` (`graph_rules.rs:261-277`) is
available in this rule dialect and used by ~70 sites elsewhere in `seeds/`.
**Confidence: high on the duplication; medium on downstream impact** — the `[0]`
indexing masks it.

### 4.5 Two public PyO3 methods still document the unguarded path as harmless *(sweep)*

`Grammar::add` (`grammar.rs:71-80`) is the `TermArena::add` of the Γ layer — a
pure append with no equivalence check. Every *internal* caller guards correctly
(`add_salient_shape:1929`, `wire_relation:2033`, `wire_relation_categorical:2135`
all wrap in `if !self.checker.grammar.knows_edge_type(...)`). But
`substrate.rs:1879-1895` still carries the comment *"Idempotent-ish (adding the
same production twice just adds a redundant candidate)"* — **stale since the
mirror landed**, because it is now "a redundant candidate *and* three permanent
graph nodes plus two Term subgraphs" — and that unguarded path is exposed
publicly as `py.rs:8357 declare_shares_shape` / `:8409 declare_relation_edge`.
**Severity: medium** (script-level callers today, not the daemon). Reported
mainly because the comment actively tells the next author it is safe.

### 4.6 `wire_self_extension` loads a seed manifest with no marker check *(sweep)*

`substrate/world_adapter.py:8125-8135` calls `load_seed_manifest` with no guard.
`load_seed_manifest` (`py.rs:1497-1524`) mints every manifest node with
`add_node` unconditionally — **all** idempotency in this system is the caller's
marker check, and every other call site honours that
(`boot_core.load_seeds_into:147-150` checks `Seed{id}` *and*
`SeedSummary{seed_id}`; `_ensure_shape_decode_loop:1256-1259` checks
`_installed_seed_ids`). This is the exact bug class the Wave-3 fix in
`load_seeds_into` documents (*"+16 duplicate rules, including a second copy of
`rule_mention_resolves_to_concept` — the single most expensive rule in the tick
profile"*). `tests/test_capkey_backfill_migrated.py:82` calls it with the
comment "(idempotent)" — **the false belief is already in the codebase.**

### 4.7 `_reconcile_seed_typed_nodes` — find-or-create by ONE key (VERIFIED IN PLACE)

CLAUDE.md documents `scripts/jabberwock_daemon.py`'s reconciliation as
idempotently find-or-creating missing top-level-seed nodes *"by `process`"*
(SelfProcess) and *"by name"* (Concept). That is a single-attribute content key
— the correct instinct, applied to one field. **Severity: latent, low** —
reported for completeness of the C inventory, not as an urgent item.

### 4.8 Rejected as NOT Pattern C

`code_cache::LruCache` (`code_cache.rs:135-186`) and `space_quantize`'s
`body_key` reuse (`space_quantize.rs:646`) — exact-key, but a miss costs only
recomputation and `space_quantize` correctly deletes-then-regenerates frontiers
(`:620-634`); performance-only, no duplication. `_gamma_meta_done` /
`_type_pair_to_rel` (`world_adapter.py:152, 89`) — same session-index-vs-
persisted-content shape as §4.2, but on a `load()`-resumed adapter the
attributes are *absent* rather than empty, so the callers raise `AttributeError`
instead of duplicating. **A real bug, in the wrong pattern** — flagged here only
so it is not later mistaken for a C instance.

Also noted in passing, as the *opposite* failure and likely to surface in the
same review: `sd_mint_generator` (`seeds/shape_decode_loop.json:1136`) guards on
`Not(Exists(g in DimensionGenerator, g.kind == "linear"))` — gated on `kind`
alone, so once any linear generator exists, a genuinely different discovered
matrix can never mint. **Over-coarse, not over-exact.**

---

## 5. Pattern D — a hand-maintained enumeration where a codebook belongs

### 5.1 THE HEADLINE: the meta-shape vocabulary is closed, hand-authored, and has no mint path (VERIFIED IN PLACE, MINE)

`seeds/shape_vocabulary.json` contains, in total:

| type | count |
|---|---|
| `MetaShape` | **11** |
| `ShapePrinciple` | 13 |
| `FunctionalRole` | 17 |

I grepped every `.py`, `.rs` and `.json` in the tree for anything that mints a
`MetaShape` or `ShapePrinciple` node at runtime. **Nothing does.** The only
non-seed writers are `scripts/arc6_ceiling_cd.py:221` and
`scripts/arc6_bc_ceiling.py:871`, which append `MetaShape` nodes into their own
generated experiment manifests — i.e. more hand-authoring, in another file.
Everything else (`reflective_faculty.py:650`, `analogical_thinking.py:126,157`,
`shape_decode.rs:7702,7980`) only *reads* the population.

**The consequence, stated precisely.** This is the codebook that:

* `teach()` files every taught item under (§2.5),
* `analogical_thinking` matches concepts with at order 4 (§2.4),
* `TransferDecode` derives a goal's shape from,
* and CLAUDE.md describes as *"its seven meta-shapes"* — the agent's answer to
  "what shape are you?"

and it **cannot grow from a residual.** A taught item that matches no keyword
does not mint a twelfth shape; `teach.py:145-147` falls back to the item's own
`category`/`domain`/`topic` string, and if that is absent, to the literal
`"taught"`. The sd loop's fourth rung — `sd_mint_quantum`, *"only after BOTH
rungs fail"* — is wired to `CapabilityAxis`, to stroke quanta, to program
chunks, to space quanta, and **not to the faculty named "shape".**

I want to be careful about what this does and does not establish. It does *not*
establish that the agent would be better with twelve shapes than eleven — a
closed taxonomy can be a legitimate design commitment, and the seven organising
meta-shapes are presented in CLAUDE.md as exactly that. What it establishes is
that **the choice was never made explicitly**: there is no design document
saying "this vocabulary is closed and here is why", and the *rest* of the system
is built on the premise that a codebook grows on residual. The absence is the
finding, not the count.

### 5.2 `seeds/question_targets.json` — 79 hand-written surface rows for 23 targets (VERIFIED IN PLACE, MINE)

The meta-target lexicon holds **79 entries mapping to 23 distinct
`meta_target`s** — an average of 3.4 hand-written phrasings per target. Four of
them are the same target reached four ways:

```json
{"meta_target":"math_bridge","match":["fractal"]}
{"meta_target":"math_bridge","match":["fractals"]}
{"meta_target":"math_bridge","match":["self","similarity"]}
{"meta_target":"math_bridge","match":["self","similar"]}
```

The file's own `_doc` states the maintenance model as a virtue: *"Adding a
question shape's target = adding an entry here, not code."* It is the same
rhetorical move the 19 composer seeds make, one grain up: the table is
graph-*data*, which is better than Python, and it is still an enumeration where
a decode belongs. Every new paraphrase — including every **morphological
variant of a word already in the table** — is a hand-written row.

Selection is **first-match-wins over the hand-ordered list**
(`comprehend_question.comprehend_meta:339-361` returns inside the loop), with no
specificity ranking. I checked whether that is currently biting: **it is not.**
A scan for cross-target strict-subset shadowing pairs (an earlier entry whose
`match` set is a strict subset of a later entry's, for a different target)
returns **0**. The consistency is real and is maintained by hand; nothing
enforces it. Contrast, again, `sd_recognize`'s `FixedCount` specificity rank.

### 5.3 The native-oracle set, enumerated three times across two languages *(verified in place)*

* `domains/prog_ir_emit.py:173` `NATIVE_ORACLES` — 32 names
* `domains/prog_ir_emit.py:192` `NATIVE_RECV_ORACLES` — 21 method names
* `domains/prog_ir_emit.py:211` `_RECV_BLOCKED_METHODS` — 13 names
* `runners/dsl/src/prog_eval.rs:1332` `call_native_oracle` / `:1789`
  `call_recv_oracle` — the corresponding Rust `match` arms

The sweep verified by parse that every Python name has a Rust arm and every
blocked name is absent — **no drift today.** The accretion is visible in the
source's own structure: the set is stratified by comment bands `# Q1
math_native`, `# Q1 container_ctor`, `# Q1 general_builtins`, and the header at
`:165` reads *"widened by Q1.5 with every Name-form / dotted-Name-form call the
Q1 engine landed a real native oracle for"*. It is an accretion log with
sections. The family it enumerates — Python's callable surface — is unbounded;
each benchmark miss adds a row in two languages. **Severity: latent (no drift
today), high maintenance cost, high drift risk.**

### 5.4 Further confirmed D sites *(sweep, not re-verified)*

| site | size | evidence of growth |
|---|---|---|
| `domains/grammar_teacher.py:36` `_LEXICON` | 141 | docstring: *"Extend it for non-English use or domain-specific terms by adding to `_LEXICON`"* |
| `domains/llvm_teacher.py:70` `_ENTRIES` + `:831` `_ALIASES` | 95 + 136 | `_ALIASES` is a hand-written string-similarity function (`"i8"/"i32"/"i64"/"iN" → "integer type"`); source is a versioned external spec |
| `domains/concept_grounding.py:151` `SYMBOL_TO_CONCEPT` | 55 | its own comment admits the coverage hole: *"the seed corpus has `drug_resistance` and `Reynolds_number` but no `resistance` concept … Honest coverage, not exhaustive"*; per-row apology comments `# ambiguous`, `# approximate` |
| `domains/bigville_entities.py` `ITEMS`/`RECIPES`/`SCARCITY` | 130/55/76 | three tables edited together per commodity; `SCARCITY` organised into hand-written taxonomic bands with a derivable regularity (every `*_seed` exactly 0.1 above its crop) typed out 12 times |
| `domains/reflective_faculty.py:7874` `_DISPATCH` | 25 + 4 setdefaults | 29 hand-written reflective answerers; sibling `:3881` `_VARIATION_REGISTRY` has *load-order carve-outs* (two entries registered later "after their builders are defined") |
| `domains/wordplay.py:104` `_SUFFIX_TABLE` | 15 | English derivational morphology is open-ended; two rows already share a gloss template |
| ~15 independent stop-word lists | 155/124/119/103/99/94/88/75/71/59/53… | **byte-identical 53-element copies** in `jabberwock_gemma_language_prior.py:37`, `jabberwock_prosodic_decode.py:71`, `jabberwock_tunable_ilm.py:46`, `jabberwock_gemma_forward_speech.py:36`; an identical 57-element pair elsewhere — the maintenance model is demonstrably copy-paste-and-tweak |
| `domains/comprehend_text.py:407` `_STRUCTURE_CUES` *(verified in place)* | 28 | labelled *"A closed cue set"* while containing **six spellings of one lemma** (organised/organized/organise/organize/organisation/organization) |

### 5.5 Rejected as NOT Pattern D

`seeds/bigville_*.json` (143 files) — opened three; genuinely different mechanics
per file, not one shape with swapped literals. `seeds/vision_lighting_l*.json` —
a prereg research ladder, l3↔l3b differ by ~950 lines. `prog_ir_statement_
histogram.py` (40 elif over `ast.X`), `prog_chunk_growth.py:209+` (14 elif over
Prog-IR node types), `llvm_ir_interp.py:105+` — closed *language* grammars, not
domain families. `shape_decode.rs:838`'s 7 generator arms — this **is** the
sanctioned codebook's transform dispatch, named in CLAUDE.md. `_mp3_huffman_
data.py`, `cabac_init_tables.rs`, `h264_*` — external spec tables, fixed
forever. `construct_compute_group_orders.py:71` — ATLAS generators; there are 26
sporadic groups and there will never be a 27th. `prog_synthesis.py:2434
_DISPATCH` — its own comment correctly identifies it as sanctioned
verdict-routing over a closed status vocabulary. `substrate/world_adapter.py` —
21 `elif` but no chain; scattered independent two-way conditionals.
`seeds/escalation_rungs.json` — the levels 1..5 are a genuine processing depth
(perception_units → segmentation → speaker_normalization → feature_extraction →
recognition), a declared ladder with a frame, not an asserted ordinal.

---

## 6. Pattern E — a scalar where a decoded quantity belongs, OUTSIDE the documented 60

**The scoping result first, because it is the honest headline of this section.**
Two positive controls came back clean and were verified: **`runners/dsl/src/
shape_decode.rs` carries no decision constants** (its own comments state the
discipline — `:2819` *"the shortest one is the best explanation — MDL, no
threshold"*; `:4369` *"read D, then DIVIDE. No threshold."*), and
**`runners/dsl/src/space_quantize.rs` contains no float in `0.1`–`0.9` at all.**
CLAUDE.md's claim that the shape-matching faculties never needed a number holds
**for the Rust engine and for the seeds.**

**Where the same shape reappears is in the Python adapters wrapping those clean
faculties.** I want this stated carefully, because it is a scoping observation,
not a refutation: CLAUDE.md's measured claim is about *60 count-divided learners
across 8 embodied seeds*, and it says none of them sit inside the sd-loop /
shape-codebook / spatial-quanta / conversation faculties. That is true of the
seeds. It was never a claim about `domains/*.py`, and the sweep below is
entirely in `domains/*.py`.

### 6.1 `domains/interlocutor_model.py:576-583` — the F-16 regress reproduced line for line (VERIFIED IN PLACE)

```python
prior = decoded["prior"]
n = int(at.get("self_report_count", 0) or 0)
k = decoded.get("decay_k", 5.0)
contradictions = int(at.get("self_report_contradiction_count", 0) or 0)
individual = (1.0 - (contradictions / n)) if n > 0 else prior
w = (n / (n + k)) if (n + k) > 0 else 0.0
value = prior * (1 - w) + individual * w
value = max(0.05, min(0.95, value))
```

CLAUDE.md quotes the F-16 regress as: *"1/n asserts stationarity → **declare a
floor 0.05** → a flat floor costs quiet regimes → declare a surprise factor 2.0
→ …"*. Line 580 is the `1/n`. **Line 583 is the 0.05 floor.** Same two steps,
same number, in the conversation faculty.

Compounding it: line 578's `decoded.get("decay_k", 5.0)` contradicts the
module's own stated discipline in two places — the header at `:398-403` and the
docstring at `:545-552` both say *"k = the WINNING SHAPE'S OWN evidence_decay_k,
**never a Python literal**."* The seeded path (`seeds/interlocutor_shapes.json`)
is real; the fallback is a literal.

**What it decides:** every Level-2 modelled belief's confidence, and — via
`_LOW_TOM_THRESHOLD = 0.4` (`:425`), consumed by `seeds/conversation_grice.json:33`'s
`Lt(ad.tom_capacity, 0.4)` — whether the agent prefixes a reply *"As I
mentioned, "* or answers plainly. **The clean replacement is already in the same
module**: `decode_shape` runs a real competition (best fit vs runner-up over
four dimensions) and `_record_shape_fit` already records `poor_fit_streak` as a
residual. The margin is computed and discarded in favour of the literal.
**Severity: live, and pinned** — `tests/test_interlocutor_modeling_migrated.py:325,334`
assert against the 0.4 threshold directly.

### 6.2 `domains/self_improvement_loop.py:223-229` — six rates, no terminator *(sweep)*

```python
eta: float = 0.01,
decay_rate: float = 0.001,
h_decay: float = 0.0001,
identity_alpha: float = 0.01,
identity_beta: float = 0.001,
identity_nudge_alpha: float = 0.05,
```

`h_id ← h_id + α·σ − β·h_id` (`:184`) is a decay whose two rates are both
hand-set. Then `:207`:

```python
alpha_eff = base_alpha * (1.0 + math.log(max(1, recurrence)))
```

with the comment *"log scaling so recurrence doesn't blow up — α grows but
bounded."* **A rate needed a rate-modifier; the modifier needed a bound; the
bound is a hand-picked functional form.** That is CLAUDE.md's *"each rate needs
a rate"* three levels deep, in the loop that governs how fast the agent's
identity field commits to a new basin.

### 6.3 `domains/stroke_codebook.py:82` — recognize-vs-mint decided by a calibrated scalar *(verified in place)*

```python
DEFAULT_DTW_THRESHOLD = 0.15
```

This decides whether two stroke prototypes are the same quantum — i.e. it is
`sd_recognize` vs `sd_mint_quantum`, decided by a number rather than by residual
coverage, **sitting directly on top of a `shape_decode.rs` that is verified
threshold-free.** The comment at `:74-81` is unusually honest and is worth
reading as evidence rather than as mitigation: it justifies `0.15` empirically
(realistic jitter ≈ 0.108, a different shape class ≈ 0.50) and records that
*"tests/test_ink_decode_migrated.py's own gate 5 / gate (c) / oov-mint gates
regressed at the initial 0.35 default."* **A swept, empirically-calibrated,
test-pinned scalar is still a scalar** — Pattern E is about the shape, not about
carelessness.

Its sibling `DEFAULT_CONTINUOUS_MINT_THRESHOLD = 0.30` (`:171`) is the same
shape one level up (mint a new top-level peer or not), **mitigated: it is DEFAULT
OFF** (`enable_continuous_mint=False` at every `decode_ink` call site) and its
own comment requires an honest sweep before use. I rank it lower for that
reason.

### 6.4 The half-migrated cases — where the finish line is visible in the same file *(sweep, spot-verified)*

These are the cheapest, because the codebase already contains the worked
conversion:

* `substrate/world_adapter.py:8882` `discover_action_affinities(min_samples=5,
  margin=0.7)` — `:8914` decides whether `typical_best_action` is written onto a
  `BodyType` by `leader_mean < (1.0 + margin) * runner_up_mean`. The *structure*
  is right (leader vs runner-up is a real competition); the criterion is a
  hand-set 70%. **2,600 lines earlier in the same file**, `:6279` reads
  `self.get_scalar_policy("insight_threshold", 0.7)` with the docstring *"the
  DECISION threshold is the seeded policy (a Lit the agent reads), **not a
  Python constant**."* One was converted; the other was not.
* `domains/compositional_chunking.py:88-89` `_PROMOTION_RATE_HIGH = 0.50` /
  `_PROMOTION_RATE_LOW = 0.05` — the *threshold* they tune
  (`lex.promotion_threshold`) is genuinely graph-resident and rule-editable, as
  the module documents at `:65-68`. **The band deciding when to retune it is two
  Python constants.** The rate got a rate.
* `domains/contextualization_depth.py:509-526` — computes `margin = best_ov -
  runner` (a real competition), then discards its magnitude through three
  hand-set constants (`0.34`, `0.85 ×`, `+0.12`, cap `0.97`).
* `domains/gap_prioritiser.py:332` `PROMISCUITY_FRAC = 0.10` — gates which gap
  the agent investigates next, and the comment at `:321-331` argues the case in
  **MDL bits**, a quantity `shape_decode.rs:2819/3053` already computes without
  a threshold. The justification names the decoded quantity and then substitutes
  a scalar for it.

### 6.5 A cluster nobody has a frame for: `information_commitment`'s asserted utilities (VERIFIED IN PLACE, MINE)

`domains/teach.py:180-192` calls `information_commitment.assess` with **six
literal scalars**:

```python
commit={"name": "teach_to_disk", "expected_goal_work": 2.0,
        "expected_information_gain": 1.0,
        "footprint": {"deleted_facts": 0.0, "overwritten_facts": 1.0,
                      "recoverability": 0.5, "externality": 0.0}},
wait={"delay_cost": 0.1}, refine={"refinement_cost": 1.0},
```

The **decision** is genuinely graph-native — `seeds/information_commitment.json`'s
six `ic_*` rules score the candidates and `ic_choose_unique_admissible_option`
picks. The **quantities** are asserted per call site with no shared unit:
`teach.py` says its work is worth `2.0`, `domains/voice_world.py:676` says
`1.0`, `domains/proposal_install.py:313` defaults to `10.0`,
`domains/fetch_dispatch.py:524` defaults to `0.0`. Nothing relates them.

And the scoring rule (`scripts/build_information_commitment_seed.py:49-57`) is:

```
COMMIT_VALUE = (expected_goal_work + expected_information_gain)
             − (information_destroyed + option_volume_lost + resource_cost
                + uncertainty × irreversibility)
```

— **an unweighted sum of six heterogeneous asserted quantities, minimised
greedily.** That is, structurally, the humanoid finding CLAUDE.md already names
(*"`HumanoidComposer` sums nine cost terms unconditionally and minimises
greedily"*), in the executive faculty, in a non-embodied domain, and it is not
among the documented 60. **Severity: live** — this gate decides whether the
agent's own learning is written to disk (`teach.py:193-198` returns
`saved: False` when it declines).

### 6.6 Rejected as NOT Pattern E

The `>= 0.5` truthiness idiom (~40 hits) — `self_verification.py:113` documents
it as *"the graph-native truthiness of a 1.0/0.0 flag"*; decoding a boolean, not
a threshold. Integer counts in a frame (`_WINDOW_SIZES`, `COARSE_TURN_BINS = 6`,
`PROTOTYPE_LEN = 16`, chunking's MIN/MAX/STEP) — CLAUDE.md's own in-frame-is-
integer rule says these MUST be integers. Engineering limits (`_FUEL = 10000`,
`_TOPK = 5`, `_CHUNKING_TICK_BUDGET_MS = 80.0`, all `timeout: int = 8`) —
`stroke_codebook.py:172-175` even pre-labels its own as *"A mechanical COST
BOUND … not a decision."* Physical constants with their frame
(`ink_dynamics.py:69 DEFAULT_SMOOTH_MS = 60.0`, justified against the 40–120 ms
handwriting literature; prosody theta bands in Hz). Measurement instruments
(`ink_dynamics.py:248 DEFAULT_AGREEMENT_TOL = 0.08` — a Gate-0 evaluation
tolerance with a Monte Carlo null; it measures the system, it does not steer
it). Prose rendering (`reflective_faculty.py:7835` picking
"highly"/"moderately"/"cautiously" — arbitrary, but nothing downstream reads
them). `world_adapter.py:849`'s `total_quanta / (total_quanta + sample_count)` —
reads like `n/(n+k)` but `k` **is** the sample count; no hand-set term, and it is
correctly labelled *"measurement metadata, not a judgment."*

---

## 7. A candidate SIXTH pattern — the same enumeration written twice, with nothing deriving one from the other

The brief invited a sixth pattern if one did not fit A–E. **One does.** It is
not "an enumeration where a codebook belongs" (that is D) — it is **two or three
copies of the SAME enumeration, in different layers or languages, that must
agree, with no derivation relation and no mechanism enforcing agreement.**

Five instances, all verified in place:

1. **The meta-target enumeration lives in three places.**
   `seeds/question_targets.json` (79 rows, 23 targets); `domains/comprehend_
   question.py:207-232` `_META_LEXICON_FALLBACK` (6 rows — a stale subset used
   when the seed is missing); and `:234-250` `_SELF_MODEL_META_ENTRIES` (3 rows
   appended in Python **always**, with a comment explaining exactly why the
   author could not put them in the seed: *"that file is a graph-DATA seed
   outside this task's editable-file set, and … `load_meta_lexicon` only falls
   back to a Python list when the seed is EMPTY, which it isn't (55 entries) —
   so a fallback-only addition would never be reached."*). **The comment is a
   contemporaneous record of the pattern forming.**
2. **The handler enumeration is a fourth copy, and it has already drifted.**
   `reflective_faculty.py:7874` `_DISPATCH` holds 29 keys. Comparing them to the
   seed's 23 `meta_target` values: **2 seed targets have no handler**
   (`code_capabilities`, `emitter_roadmap`) and **8 handlers have no seed row**
   (`reading_trace`, `referent_trace`, `self_kind`, `self_modification`,
   `self_model_rule`, `self_model_topic`, `self_model_touches`,
   `self_process`). The 8 orphaned handlers are reachable via the Python-append
   route or not at all; the 2 orphaned targets route to a handler that does not
   exist. **This is drift, measured, live.**
3. **Two consumers of the one lexicon disagree on how to select from it.**
   `comprehend_question.comprehend_meta:339-361` is **first-match-wins over the
   hand-ordered list**; `comprehend_text._best_meta_entry:245-253` is
   **best-covered-wins** (`_score_meta_entry` counts matched fragments and takes
   the max). The second is strictly better and its docstring says so — *"so the
   BEST-covered entry wins instead of the FIRST-listed one"* — but the first was
   not changed, so which selection semantics apply depends on which module the
   turn entered through.
4. **The `keywords_text` Argmax has Python and seed-data twins.** The six
   `reflective_faculty.py` sites of §2.1 have three graph-resident copies in
   `seeds/composer_experiment_graph.json` (10 `keywords_text` references).
   Fixing the Python alone would leave the seed copies live.
5. **The native-oracle set (§5.3)** — a Python frozenset and a Rust `match`,
   in sync today, with nothing deriving either from the other.

**Why this deserves its own name.** Pattern D's fix is "make it a codebook."
This pattern's fix is different and cheaper: **make one copy the source and
derive the others**, which is exactly what the Γ reflection mirror does for
productions (`grammar_reflect.rs`, with `round_trip_content_equal` as its gate)
and exactly what `RULES_AS_SHAPE_DESIGN_SPIKE.md` §6.4 argues the rule reference
layer must be. Instance 2 is the proof that "in sync today, maintained by hand"
does not stay true.

---

## 8. Ranked findings

Ranked by (consequence × confidence) ÷ cost-to-verify, with structural
similarity to something this session already knows how to fix as a tiebreak.

**1. The meta-shape codebook cannot grow (§5.1).** `seeds/shape_vocabulary.json`
— 11 `MetaShape` + 13 `ShapePrinciple` nodes, no mint path anywhere in the tree,
feeding `teach()`, `analogical_thinking` order-4, and `TransferDecode`. The
system's own generative primitive (`sd_mint_quantum`) is wired to five other
grains and not to this one. *Consequence:* the agent's self-categorisation is
capped at a hand-authored vocabulary. *Cost to verify:* trivial — one grep,
already done. *Fix shape:* genuinely new wiring, but of an existing loop to an
existing population; nothing needs inventing.

**2. `recognise_meta_shape` decides by substring and breaks ties alphabetically
(§2.5).** `shape_decode.rs:5340-5395` + `teach.py:93`. The scorer destroys the
item's typed structure (`" ".join(attrs.values())`) before scoring, and
`then_with(|| a.1.cmp(&b.1))` makes an alphabetical accident decide a
categorisation. *Pairs with #1* — together they are the whole shape faculty.
*Fix shape:* the same `StructSim`/`Covers` escalation the rule-signature slice
just measured, one grain over.

**3. The `keywords_text` family — six live self-modification decisions with a
measured better alternative sitting unwired (§2.1).**
`reflective_faculty.py:2704, 2963, 3240, 3532, 3909, 4183` + three seed twins.
`abae030` measured structural-vs-name at 11/12 vs 0/12 on the Class A oracle and
deliberately shipped it observational-only. *Cheapest fix in the audit* — the
replacement exists, is measured, and is one import away, though the six sites
differ in what they rank and only two are in the slice's scope. *Fix shape:*
already built (`domains/rule_signature.py`).

**4. 159 rule-carrying seeds mint edges with zero Γ productions** (a
standalone measurement made for this audit; recipe in §10).
Corpus-wide: **454 of 634 rule-carrying manifests declare `"productions": []`;
159 of those have rules with `add_edge` effects** (vs 124 that both mint edges
and declare productions). CLAUDE.md names this for 4 bigville violence seeds and
for the humanoid composer; this is the same finding at corpus scale. *Cost to
verify:* one script, run, reproducible in §10. *Caveat, stated honestly:* I did
**not** verify at the engine level that a rule-effect `add_edge` bypasses
`check_edge` — the humanoid doc asserts it (*"rule effects write via
`graph.insert_edge` directly … the `gated` flag is reserved and unbuilt"*) and I
found no `check_edge` call in `graph_rules.rs`, but I did not trace
`rewrite.rs:1499`'s apply path to ground. **Treat the 159 as a measured
population, not as 159 confirmed admissibility violations.**

**5. The `CapabilityAxis` identity is `"induced_" + "_".join(preds[:3])`
(§3.1).** Order-dependent and truncated at three, in a pipeline where every
other comparison is a canonically-sorted set. It fails both ways, and the second
way is the serious one: a first-three collision routes a genuinely novel
observation to `sd_dedup_existing`, whose only effect is
`status = "recognized_duplicate"` — **a growth failure that presents as
successful recognition, in the loop CLAUDE.md calls the system's sole
dynamic-quantization branch.** *Cheap to fix* — sort and untruncate, using the
canonical form `build_candidate` already computes two files away.

**6. Two unfixed siblings of the bug that just bit (§4.2, §4.3).**
`world_adapter.py:10113` (`learn_recursive_concept` — its index is never saved
or restored, verified by grep: three occurrences, none in `save`/`load`) and
`:9987` (`learn_word` — the index *is* persisted and simply never read). Both
mint a duplicate `Concept` + definition subgraph on re-teach; `_concept_by_name`
then returns the **stale** node to every reader while the evaluator uses the new
one. *This is divergence, not just growth,* and `_ensure_concept` in the same
class is the worked fix.

**7. The F-16 regress in the conversation faculty (§6.1).**
`interlocutor_model.py:580-583` — `1/n` on one line, `max(0.05, …)` three lines
later, in the faculty CLAUDE.md holds up as clean. *Documentary value is the
point*: this is the strongest evidence that the regress is not an
embodied-motor phenomenon. Pinned by two test assertions, so the fix is not
free.

**8. `composer_dispatch`'s priority IS the insertion index (§2.3).** 24 cues,
priorities 1..23 with one duplicate and no gaps. *Cheapest to verify of anything
here* (read 24 rows), and the correctness risk grows monotonically with every
composer added.

**9. `information_commitment`'s unweighted sum of asserted utilities (§6.5).**
The humanoid's nine-term greedy sum, in the executive faculty, gating whether
the agent's learning reaches disk. Six literals at one call site, four
incommensurable magnitudes across four call sites.

**10. The meta-target enumeration exists in four copies and has already drifted
(§7).** 2 orphaned seed targets, 8 orphaned handlers, two consumers with
different selection semantics over the same table. *This is the sixth pattern's
proof of existence, and it is the cheapest of all to check.*

**Just below the line, and named so they are not lost:**
`find_analogies` is still the MAC stage as verdict (§2.4) — the June diagnosis's
original site, uncorrected, now writing `implements` edges on a hand-set ordinal
(`order_n >= 2`); `sd_recognize_dim` mints a `LatentDimension` per observation
rather than per dimension (§4.4), which three test files already implicitly
assume it does not; `wire_self_extension` loads a whole seed manifest with no
marker check (§4.6), the exact bug class the Wave-3 `load_seeds_into` fix
documents; and `stroke_codebook.py:82`'s `DEFAULT_DTW_THRESHOLD = 0.15` (§6.3) —
recognize-vs-mint by scalar, sitting directly on top of a verified
threshold-free `shape_decode.rs`.

---

## 9. What this audit does NOT establish

1. **It is not exhaustive.** `runners/dsl/src/` is 84 files and ~106k lines;
   `domains/` is 727 files. Every section here is a sample, not a census, and
   Pattern C in particular has no clean grep signature (there is no search for
   "minted without checking first") — §4 is the pattern I am least confident is
   fully enumerated, despite being the one whose consequences are sharpest.
2. **Not one finding here has a number attached to its consequence.** Every
   severity judgement is a mechanism claim. Per CLAUDE.md's own standing rule
   (*"synthetic-proven mechanism ≠ benchmark value, report both"*), none of these
   is shown to move any measured outcome. The single exception is #3, where
   `abae030` measured that structural and name picks *differ* — and even there,
   "differ" is not "better in production", as that rung's own honest scoping
   says.
3. **Grep-shaped blind spots.** Pattern A was found by searching for
   `StringIndexOf`/`Argmax`/`keywords`. A selection-by-name implemented with a
   different idiom — a Python `dict` keyed by name, a `sorted()` with an
   implicit name key, a regex — would not have surfaced. Pattern E was found by
   searching for float literals; a magic quantity computed from two integers
   would not have surfaced.
4. **No git history evidence exists for Pattern D.** 77 commits, 17 touching
   `seeds/`, and `--follow` returns "Initial import" for essentially every
   individual file. **Every "this table grows" claim in §5 rests on textual
   evidence** — accretion comments, arc labels, self-documenting maintenance
   instructions — not on measured history. That is weaker evidence and should be
   read as such.
5. **I did not boot an agent.** Every measurement is a static scan of seed
   manifests and source. What a live graph contains, and which of these paths
   actually fire on the daemon, may differ — several seeds are not loaded by
   default. §2.4's severity in particular is unmeasured for this reason.
6. **The 159-seed Γ figure is a population, not a violation count** — see #4 in
   §8. I did not trace the engine's edge-apply path to confirm the bypass.
7. **The sweep-sourced findings have a measured error rate.** Two of them were
   wrong on verification (§1), and one of my own counts was wrong too. Every
   finding marked *(sweep, not re-verified)* should be treated as a
   high-quality candidate, not as a confirmed fact. That is: §3.1b, §4.4, §4.5,
   §4.6, §5.4's table, §6.2, §6.4's four sites, and the lower half of §2.6.
8. **"Most prevalent" is a claim about what this method found**, not about the
   codebase. Pattern A had the crispest grep signature of the five, which is
   part of why it dominates the count. Pattern C had the weakest, and is almost
   certainly under-represented here relative to its true frequency —
   **especially given that the only pattern in this audit with a *measured*
   production consequence (+261 nodes/cycle) is a Pattern C instance.**
9. **§4.4's prevalence is inferred, not observed.** The per-frame observation
   path that would produce N duplicate `LatentDimension` nodes is a reading of
   the accumulation runners, not a run. I did not boot a video path and count
   the nodes.
10. **No fix is proposed for anything.** Where §8 notes a fix shape, that is a
   one-sentence observation about resemblance to something already built, not a
   design, and certainly not a recommendation to build it.

---

## 10. Reproduce

Every count in this document, against `main` at `abae030`:

```bash
cd /home/matt/ozmadev/ocelot
git log --oneline -1 main          # abae030 (NOT f4f29b3 — see the header)

# §5.1 — the meta-shape vocabulary and its (absent) mint path
python3 -c "import json,collections;d=json.load(open('seeds/shape_vocabulary.json'));\
print(collections.Counter(n['type'] for n in d['nodes']))"          # MetaShape 11
grep -rn '\"MetaShape\"' --include=*.py --include=*.rs --include=*.json . | grep -v '^./tests/'

# §5.2 — question_targets: 79 rows -> 23 targets, and the shadowing check
python3 -c "import json,collections;d=json.load(open('seeds/question_targets.json'));\
c=collections.Counter(e['meta_target'] for e in d['meta_targets']);\
print(len(d['meta_targets']),'rows',len(c),'targets');print(c.most_common())"

# §2.3 — composer_dispatch priorities == insertion order
python3 -c "import json;d=json.load(open('seeds/composer_dispatch.json'));\
[print(n['attrs']) for n in d['nodes'] if n['type']=='ComposerCue']"

# §8 #4 — Γ productions, corpus-wide
python3 - <<'PY'
import json,glob
noprod=withprod=0; addedge_noprod=[]
for f in sorted(glob.glob('seeds/*.json')):
    try: d=json.load(open(f))
    except Exception: continue
    if not isinstance(d,dict) or not (d.get('rules') or []): continue
    p=d.get('productions') or []
    (withprod:=withprod+1) if p else (noprod:=noprod+1)
    if not p and any(isinstance(e,list) and e and str(e[0]).startswith('add_edge')
                     for r in d['rules'] for e in (r.get('effects') or [])):
        addedge_noprod.append(f)
print('rule-carrying seeds with 0 productions:',noprod,'of',noprod+withprod)
print('...of which rules mint edges:',len(addedge_noprod))
PY

# §7 #2 — the measured drift between the seed lexicon and _DISPATCH
python3 - <<'PY'
import json,re
seed={e['meta_target'] for e in json.load(open('seeds/question_targets.json'))['meta_targets']}
src=open('domains/reflective_faculty.py').read(); i=src.index('\n_DISPATCH = {')
disp=set(re.findall(r'"([a-z_0-9]+)"\s*:',src[i:src.index('\n}',i)]))
disp|=set(re.findall(r'_DISPATCH\.setdefault\("([a-z_0-9]+)"',src))
print('seed target, no handler :',sorted(seed-disp))
print('handler, no seed row    :',sorted(disp-seed))
PY
```

Code claims read directly:

```bash
sed -n '2704,2765p'   domains/reflective_faculty.py   # A1, the calibration case
sed -n '3900,3999p'   domains/reflective_faculty.py   # A4 — _EDIT_OPS + the FAC-after-MAC comment
sed -n '4175,4200p'   domains/reflective_faculty.py   # A3 — which seed to ablate
sed -n '190,215p'     substrate/boot_all.py           # SeedSummary.keywords_text is a name bag
sed -n '3140,3168p'   domains/reflective_faculty.py   # A2.2 — chars: list(verb)
sed -n '252,361p'     domains/analogical_thinking.py  # five orders, all token overlap
sed -n '5340,5395p'   runners/dsl/src/shape_decode.rs # substring score + alphabetical tiebreak
sed -n '81,101p;145,180p' domains/teach.py            # the text build, the fallback chain, exact-dict dedup
sed -n '576,583p'     domains/interlocutor_model.py   # 1/n then max(0.05, ...)
sed -n '398,406p;545,552p' domains/interlocutor_model.py  # "never a Python literal"
sed -n '70,90p'       domains/stroke_codebook.py      # DEFAULT_DTW_THRESHOLD = 0.15
sed -n '180,200p'     domains/teach.py                # six literal utilities
sed -n '20,60p'       scripts/build_information_commitment_seed.py  # the unweighted sum
sed -n '160,215p'     domains/prog_ir_emit.py         # the accretion log with sections
sed -n '227,256p;407,412p' domains/comprehend_text.py # _best_meta_entry; _STRUCTURE_CUES
sed -n '317,361p'     domains/comprehend_question.py  # first-match-wins
sed -n '234,250p'     domains/comprehend_question.py  # the Python-append comment
head -33              domains/rule_signature.py       # observational-only, by its own docstring
git show f4f29b3 --stat | head -25                    # the Γ reload growth bug
```
