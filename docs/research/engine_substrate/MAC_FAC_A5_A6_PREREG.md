# MAC/FAC A5 + A6 — pre-registration

Companion to `SHAPE_AUDIT.md` §2.1 (the `keywords_text` family — one lambda,
six self-modification decisions) and the two already-landed rungs this task
extends directly: `SEED_PICK_STRUCTURAL_FALLBACK_PREREG.md`/`..._RESULTS.md`
(A3) and `EDIT_OP_APPLICABILITY_GATE_PREREG.md`/`..._RESULTS.md` (A4). Read
both before this doc — they are this rung's own templates, not background
colour: the lexicographic fallback-on-abstain shape (primary Argmax tried
first, unchanged; only on genuine abstain does a SECOND Argmax run against a
structural signal) is REUSED here, not reinvented, per the task's own
instruction.

**Worktree:**
`/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a5-a6`,
branch `mac-fac-a5-a6`, detached from `main` at `8af4fde` (`git log --oneline
-1 main` reconfirmed at worktree-creation time). No Rust touched:
`runners/dsl/python/substrate_rs/_native.abi3.so` sha256
`07aabbf14af065566b096403c8bd4cbee0d79eb4f7800ba5fc04f46e1b92b75e` (recorded
before any edit; expected unchanged after, since AR3 below adds zero PyO3
calls and zero new Term variants — checked at commit time, not merely
assumed).

**Sibling-agent collision check (done before starting):** no worktree or
recently-committed branch (`git worktree list`, `git for-each-ref
--sort=-committerdate`) names A5, A6, A7-A9, `composer_experiment_graph`,
`dedup`, or `deduction`; the four live worktrees at task-start
(`can-synchronous-update-fix`, `can-solver-theoretical-limits`,
`editop-applicability-gate`, `shape-decode-library-scaling`) touch CAN /
EditOp-A4 / shape-decode-scaling code, none of which overlaps
`domains/reflective_faculty.py`'s A5/A6 line ranges. `editop-applicability-gate`
DOES touch `reflective_faculty.py` (A4, already landed per its own RESULTS
doc, disjoint line range ~4084-4250) — read, not touched again here.

---

## 0. The two sites, re-verified this session (line numbers as of `8af4fde`)

- **A5**: `domains/reflective_faculty.py::_compose_datum_feedback_rule`
  (`:3792-3915`), candidate table `_DATUM_FEEDBACK_CANDIDATES` (`:3784-3789`,
  **exactly one row today**). WHICH (datum_attr, belief_attr) pair to author
  a feedback rule for: a plain-Python loop (`for row in
  _DATUM_FEEDBACK_CANDIDATES: overlap = sum(1 for w in words if w in
  row["keywords_text"].split())`), best-scoring row wins, abstain below a
  2-word floor.
- **A6**: `domains/reflective_faculty.py::_compose_rule_literal_variant`
  (`:3678-3774`). WHICH (RuleSummary, where-literal-candidate) PAIR to edit:
  a plain-Python nested loop over `writes_where_literal==1.0 AND
  skippable==1.0` RuleSummary nodes × each rule's own `_find_where_lits`
  candidates, scored by `_collect_vocab_tokens(cand)` token-membership
  overlap (a LOCAL read of ONE comparison subtree's own Attr keys / Lit
  strings / NodesOfType names — `:3471-3502`), abstain below a 2-word floor.

**Both re-verified live by direct read this session**, and both confirmed
NOT to have been touched by the concurrent `editop-applicability-gate` /
`shape-decode-library-scaling` / CAN worktrees (checked their branch diffs
against `main` before starting — see §6).

**A structural property shared by A5 and A6, different from A1/A2/A3/A4, and
load-bearing for the design decision in §1 below:** neither site's primary
pick is a native Term evaluated via `native0.evaluate` — both are PLAIN
PYTHON loops. A1/A2's fallback stays inside "ONE evaluated Term" because
their PRIMARY already was one; A3's fallback is embedded in a `{"__term__":
...}` effect because the whole pick is installed as a live rule. A5/A6 do
neither — their pick is a one-shot Python computation, called once per
`_compose_*` invocation, with no live-rule embedding and no existing Term to
extend. This is investigated, not assumed, in §1.

---

## 1. Design choice, registered before any edit: Python-side lexicographic
fallback, NOT a native Term

**Decision: implement the fallback as a SECOND plain-Python pass, run only
when the primary plain-Python pass finds no candidate at or above its own
existing floor — mirroring the site's OWN existing computational idiom, not
A1/A2/A4's Term-embedded idiom.**

Two alternatives considered and rejected, for the same reason in both
cases — introducing a NEW computational shape into a site that has never
used one, for no benefit the task requires:

- **Convert the whole pick into a native Term** (`Argmax`/`Filter`/`StrIdx`
  over graph nodes, `native0.evaluate` once), matching A1/A2/A4 verbatim.
  Rejected: A5's candidate pool is a compile-time PYTHON TUPLE
  (`_DATUM_FEEDBACK_CANDIDATES`), not a graph node population — there is
  nothing for `NodesOfType` to range over without first minting a graph
  node per table row, which is a real, unrequested schema change (turning a
  held Python constant into graph data) far outside this rung's scope. A6's
  candidate pool IS graph nodes (`RuleSummary`), but the unit being ranked
  is a PAIR (rule, literal-index-within-that-rule's-own-`where_lits`-list) —
  the literal candidates are dict values extracted by `_find_where_lits`,
  never graph nodes themselves, so an `Argmax` over them would need the same
  kind of node-per-candidate minting A5 would need. Neither site's data is
  Term-addressable without a schema change; the task brief authorises "no
  new Rust Term" but not implicitly "mint new graph nodes for existing
  Python tuples/dict-lists."
- **Leave the pick in Python but call `native0.evaluate` just for the
  structural SCORING sub-step** (e.g. reuse `rule_signature._structural_score`'s
  `FixedCount` call for A6). Considered for A6 specifically (it does have
  real `where_signature_json` on real graph nodes). Rejected in favour of
  the SAME plain substring/token check both sites already use everywhere
  else (`keywords_text` overlap is a plain Python `in` test, not a Term) —
  introducing a Rust round-trip for one sub-computation while the
  surrounding pick and the OTHER stage remain pure Python would be a
  genuinely new, asymmetric shape at this site, not a mirror of anything
  already there. `where_signature_json` is read as a plain attribute STRING
  and substring-matched in Python, exactly the way A1/A2's OWN fallback
  treats it as a Term-level string blob (`StrIdx(Attr(node_t,
  "where_signature_json"), V("w"))` is *also* just a substring test — A1/A2
  merely happen to run it inside `native0.evaluate` because their primary
  already does; the semantics, not the execution engine, are what this rung
  mirrors).

This is a genuine per-site judgement call, registered here before the code
changes, following `SEED_PICK_STRUCTURAL_FALLBACK_PREREG.md` §1.3's own
precedent of registering a design choice with its rejected alternative
before building.

---

## 2. A6 — the structural signal, and why it is directly reusable

**Confirmed by reading `domains/rule_signature.py::ensure_where_signature`
(`:321-358`): it mints `where_signature_json` on EVERY `RuleSummary` node
that carries a `rule_json`, unconditionally — NOT filtered to
`writes_chosen_action`/`writes_reply`.** The task brief's own open question
("does A6's candidate pool already intersect with A1/A2's
`writes_chosen_action`-filtered pool, or is it a genuinely different subset
needing its own signature computation") is answered directly by this read:
A6's pool (`writes_where_literal==1.0`) is DISJOINT from A1's
(`writes_chosen_action==1.0`) and A2's (`writes_reply==1.0`) in general (a
rule that shifts a where-clause floor is not the same rule that writes a
`chosen_action`/`reply` effect, though nothing forbids overlap) — but
`ensure_where_signature` computes its signature per-`RuleSummary`-node,
keyed only on `rule_json` being present, so calling it AGAIN over the
`writes_where_literal` pool (exactly the existing
`_ensure_acting_rule_provenance` + `ensure_where_signature` precall pattern
A1 already uses) mints the signature for A6's OWN pool directly — **the
SAME mechanism, reused with zero new code in `rule_signature.py`.**

**The genuine structural gap A6 has, distinct from A1/A2's gap.** A6's
EXISTING scorer (`_collect_vocab_tokens`) is already a "structural" read in
one sense — it walks Attr keys / `NodesOfType` names / short Lit strings
inside ONE comparison subtree, not a name-derived prose blurb the way
`keywords_text` is for A1-A5. But it is scoped to exactly the ONE
`_find_where_lits` candidate node being scored — a comparison's own `a`/`b`
operands and whatever is nested under them (e.g. a `Count(Filter(...))`
aggregate's inner predicate, per
`tests/test_rule_literal_variation_migrated.py::test_collect_vocab_tokens_reads_attr_and_type_and_lit_strings`).
**It never sees the rule's OTHER, sibling `And`-items** — a rule frequently
has non-numeric-literal `Eq`/`Not`/`Exists` guard conditions alongside its
numeric threshold(s) (verified directly: `escalate_narrative_shape`'s
`where` clause has FOUR sibling `Eq` conditions —
`goal.reading_report==1.0`, `spine_stage.name=="spine"`,
`spine_stage.flow==src.flow`, `spine_stage.status=="done"` — none reachable
from EITHER of its two `_find_where_lits` candidates, since `_find_where_lits`
only descends into comparison nodes carrying a numeric `Lit`, and these four
are plain string/attr equalities). `where_signature_json` (the FULL
`where`-clause flattening, `rule_signature.py:126-183`) covers the WHOLE
clause, siblings included — so a concern naming something the rule's guard
conditions read (but neither numeric-comparison candidate's own local
subtree reads) is exactly the Class A shape A1/A2 measured, one grain down:
present in the rule's structure, absent from what the LOCAL per-candidate
scorer can ever see.

**Two-tier resolution needed, registered here.** `where_signature_json` is a
per-RULE signature; A6 picks a per-(RULE, LITERAL) pair. The fallback
therefore resolves in two tiers, exactly mirroring how the two grains
already coexist in this file (A3 is per-seed, A1/A2 are per-rule; nothing
new in kind):
1. When the primary (per-`(rule,cand)`-pair, 2-word floor) genuinely
   abstains SYSTEM-WIDE (no pair anywhere scores >= 2), score each
   CANDIDATE RULE (the same `writes_where_literal==1.0 AND skippable==1.0`
   pool) by content-word substring overlap against its OWN
   `where_signature_json` blob (mirrors A1/A2's `StrIdx` semantics exactly:
   substring test against the whole JSON string, not exact token
   membership) — same 2-word floor, registered per-site per §3.1 below.
2. Within the structurally-picked rule, choose WHICH `_find_where_lits`
   candidate via the SAME LOCAL vocab scorer the primary already uses
   (`_collect_vocab_tokens`), but WITHOUT the 2-word floor (the floor's job
   — reject a signal too weak to trust — was already discharged by the
   rule-level structural match; picking among a validated rule's own few
   candidates by whichever has the highest, even zero, local overlap is the
   most content-relevant sub-choice available, ties broken by first
   `_find_where_lits` discovery order, matching the primary's own
   first-max-wins tie convention exactly).

---

## 3. A5 — the structural signal, and its honest limit

**Confirmed by reading `_DATUM_FEEDBACK_CANDIDATES` (`:3784-3789`): each row
carries `node_type`, `datum_attr`, `belief_attr` — real structured fields,
independent of `keywords_text`.** `keywords_text` is a hand-authored
DESCRIPTIVE blurb (arbitrary prose words chosen to evoke the concept:
`"reliability trust trustworthiness track record contradiction self report
belief calibrate recalibrate recalibration miscalibrated"`), directly
analogous to A1's rule-NAME-derived bag — a human-chosen label layered ON
TOP of the row's real operational identity. `node_type`/`datum_attr`/
`belief_attr` ARE that real operational identity: the literal graph
node-type and attribute names the authored rule actually reads and writes.
**This is the same MAC/FAC split as A1/A2, one level down: MAC = the
hand-written prose blurb; FAC = the row's own structural fields.**

**Measured, not assumed: which words are genuinely novel.** Splitting
`node_type`/`datum_attr`/`belief_attr` on `_` and comparing against
`keywords_text`'s own token set (both lower-cased):
`node_type="Interlocutor"` → `{interlocutor}` (NOT in keywords_text);
`datum_attr="self_report_contradiction_count"` → `{self, report,
contradiction, count}` (`self`/`report`/`contradiction` ARE already in
keywords_text; `count` is NOT); `belief_attr="self_report_reliability"` →
`{self, report, reliability}` (all three already present). **Exactly two
genuinely novel structural words exist in the current single-row table:
`interlocutor` and `count`.**

**The honest limit, stated before any demonstration is built, per the task
brief's own explicit invitation for this outcome:** `_DATUM_FEEDBACK_CANDIDATES`
has **exactly one row**. A fallback Argmax over a singleton candidate set
cannot demonstrate DISCRIMINATION (correctly preferring the right candidate
over a plausible wrong one) — there is no wrong one to reject. What CAN be
demonstrated, and is real: **avoiding a false abstain.** Today, content
words that name `count`/`interlocutor` but miss every `keywords_text` token
(e.g. a report that says "the interlocutor's contradiction *count* keeps
climbing" without ever saying "trust"/"reliability"/"calibrate") score 0-1
against the primary and the family returns `built: False` even though the
ONE held row is, on the structural evidence, obviously the intended target.
**Verdict registered here, before building: GO on a NARROWED claim** — the
fallback closes a genuine false-abstain gap on the real, single-row
production table, but this rung explicitly does NOT claim (and the RESULTS
doc will say so plainly) that it has been shown to discriminate correctly
among multiple candidates, because the real table does not yet have more
than one. This is reported as the honest, narrower sibling of the brief's
anticipated "no meaningful fallback" outcome — not that finding exactly (a
real, useful fix DOES exist), but sharing its epistemic caveat.

Same two-stage shape as A6, one grain simpler (no per-row secondary tier
needed — a table row already resolves everything the authored rule needs):
primary (`keywords_text`, 2-word floor) tried first, unchanged; only on
abstain does a second pass score each row by substring overlap against
`" ".join([node_type, datum_attr.replace("_"," "), belief_attr.replace("_",
" ")])`, same 2-word floor (registered per-site per §3.1).

### 3.1 Floor choice for both fallbacks: 2 words, matching each site's own
primary, not A1/A2's `> 0`

A1/A2's fallback abstains at `overlap <= 0` (any single genuine substring
hit is enough). A5/A6's OWN PRIMARY already uses a stricter 2-word floor,
with an explicit reason stated in both docstrings ("a bare 'threshold'
mention does not NAME a literal — it would pick an arbitrary comparison").
That risk is a property of the SITE (a single generic word can spuriously
name an unintended rule/table-row), not of which signal is scored — it
applies to the structural signal exactly as much as to the prose blurb.
**Decision: both fallbacks keep the SAME 2-word floor their own site's
primary already enforces**, registered here rather than silently
inherited or silently changed.

---

## AR1 — combination-wiring design (registered before the edit, both sites)

Identical shape to A1/A2/A3's own AR1: the primary pass is UNCHANGED and
tried first; only when it genuinely abstains (no candidate/pair reaches its
existing floor) does the SAME kind of pass (Sum-of-membership, `>=2` floor)
re-run against the structural signal instead of `keywords_text`. Not a
pre-filter, not a blend, for the identical reason A1/A2/A3 already give: the
two signals are not commensurable (a short hand-written blurb vs. a
structural JSON blob / attribute-identifier string), and a genuinely
name-native concern must not be pre-filtered out before the primary ever
sees it.

---

## AR2 — the powering bar

**A6**: real candidate population to be measured mechanically before any
number is trusted — `scripts/a6_discover_probes.py` (already written,
mirrors `scripts/seed_signature_discover_probes.py`'s own method: boot full
agent, run `_ensure_where_literal_rule_provenance` +
`rule_signature.ensure_where_signature`, walk every
`writes_where_literal==1.0 AND skippable==1.0` RuleSummary's own
`_find_where_lits` candidates, union their LOCAL vocab, then find words
present in some rule's `where_signature_json` but ABSENT from the ENTIRE
local-vocab union — genuine, system-wide Class A candidates; and words
present in some candidate's local vocab — genuine Class B). Floor: **at
least 2 genuine, mechanically-discovered Class A probes and at least 2
genuine Class B probes** (smaller than A1/A2's 40-probe design, per
`RULE_SIGNATURE_PRODUCTION_WIRING_PREREG.md` AR3's own "no fixed floor,
per-site judgement" framing, restated by `SEED_PICK_STRUCTURAL_FALLBACK_PREREG.md`
AR2 for exactly this reason at the seed grain — A6 is a further grain down
again). If the real population cannot support 2 genuine Class A probes, this
rung reports underpowered/NO-GO for A6 with the raw counts given exactly as
measured, not padded.

**A5**: per §3, the real table has exactly one row — no multi-candidate
discrimination oracle is possible. The demonstration instead directly
constructs the two REAL cases the fix changes behaviour for: (1) a
false-abstain probe (content names `count`/`interlocutor`, misses every
`keywords_text` token, primary abstains, fallback recovers `built: True`
against the one real row) and (2) a Class-B-style no-regression probe
(content already hits `keywords_text` at >=2, fallback never reached,
`built: True` with byte-identical fields to the pre-fix call). Both
constructed directly against the real, unmodified `_DATUM_FEEDBACK_CANDIDATES`
table — no synthetic second row minted into production data.

---

## AR3 — build scope

- `domains/reflective_faculty.py::_compose_rule_literal_variant` — extend the
  primary loop's abstain path (currently `if best is None: return
  {"built": False, ...}`) with the two-tier structural fallback per §2,
  calling `rule_signature.ensure_where_signature(sub0)` once before the
  fallback pass (mirrors `_ensure_where_literal_rule_provenance`'s own
  precall). Primary loop body UNCHANGED.
- `domains/reflective_faculty.py::_compose_datum_feedback_rule` — extend the
  primary loop's abstain path with the single-tier structural fallback per
  §3. No new import beyond what the module already has (no
  `rule_signature`/graph read needed — the structural signal is the row's
  own already-in-hand dict fields). Primary loop body UNCHANGED.
- Zero changes to `_pick_acting_rule`, `_pick_reply_rule`,
  `_compose_experiment_rule`, `_compose_structural_variant`/`_EDIT_OPS`, or
  any A1-A4/A7-A9 site.
- Zero new Rust Terms, zero new PyO3 bindings, zero graph-schema changes (no
  new node type, no new `add_node` call in `rule_signature.py`).

---

## AR4 — no regression

- **Paired failing-node-id lists, not counts**, for
  `tests/test_composer_capability_migrated.py` (A5) and
  `tests/test_rule_literal_variation_migrated.py` (A6), captured on this
  worktree BEFORE the production edit, then re-run after, diffed.
- **New test file(s)**: the Class A/B (or false-abstain/no-regression, for
  A5) live demonstrations land as pytest gates, not throwaway scripts.

---

## Reproduce (this doc's own validation, before any production edit)

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a5-a6
git log --oneline -1                                        # 8af4fde (detached base)
sha256sum runners/dsl/python/substrate_rs/_native.abi3.so   # 07aabbf1...92af

# A6 population + probe discovery
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 scripts/a6_discover_probes.py

# AR4 baseline (before edit)
systemd-run --scope --user -p MemoryMax=8G -p MemoryHigh=7G -- \
  python3 -m pytest tests/test_composer_capability_migrated.py \
    tests/test_rule_literal_variation_migrated.py -q
```
