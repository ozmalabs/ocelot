# MAC/FAC A7-A9 — graph-resident structural-fallback wiring — RESULTS

Companion to `MAC_FAC_A7_A9_PREREG.md` (read first — it registers the
priority order, the design choice, the edit mechanism, and the validation
steps before any edit was made). Closes `SHAPE_AUDIT.md` §2.1's three
graph-resident sites, the seed-JSON twins of the already-fixed Python
sites A1 (`RULE_SIGNATURE_PRODUCTION_WIRING_RESULTS.md`), A3
(`SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md`), A4
(`EDIT_OP_APPLICABILITY_GATE_RESULTS.md`).

---

## GO on A9 and A7 (both duplicated copies of each). A8 sized as follow-on,
not attempted — confirmed, not merely predicted, to need a different fix
shape than structural fallback.

---

## 0. What the PREREG's own §0 predicted, and what reading the file
confirmed

The PREREG registered, before any edit, that the two prior RESULTS docs'
apparent A8/A9 label disagreement over `compose_experiment_mint_
parametric` was because each was naming the SAME enclosing Rule by the
DIFFERENT nested Argmax it had personally touched. Reading the file
confirmed this exactly: one Rule node (`local_id: 8`, `seeds/
composer_experiment_graph.json:463`) contains three structurally distinct
Argmax picks, matching the audit's own line numbers:

| letter | line (pre-edit) | var names | resolves to | reached via |
|---|---|---|---|---|
| A7 | 1127 (`apick`) + a **second copy** at 3029 (`best`, undocumented by either prior RESULTS doc) | RuleSummary Argmax | node or `null` | EAGER (baked into the minted rule's effects at compose time) |
| A8 | 1366 (`epick`) | EditOp Argmax, `Argmax(NodesOfType("EditOp"), ...)`, **no candidate Filter at all** | node or `null` | EAGER |
| A9 | 4675 (`skip_id`/`best`) + a **second copy** at 4886 (undocumented by either prior RESULTS doc, feeds a DIFFERENT attr, `skip_seed_id`) | SeedSummary Argmax | seed_id string or `""` | DEFERRED (`{"__term__": ...}` literal, evaluated when the SECOND-order minted rule later fires) |

The PREREG's registered prediction for A8 — *"will be found to need the
applicability-gate shape, not the structural-fallback shape"* — is
**confirmed by direct reading, not merely inferred from the prior RESULTS
doc's own finding**: `epick`'s Argmax source is bare `NodesOfType("EditOp")`
with no `Filter` at all (unlike `apick`'s `Filter(..., writes_chosen_
action==1 && skippable==1)`), and `EditOp` nodes carry no `where`/`match`/
`effects` of their own to derive a `where_signature_json`-style fallback
signature from — see §5.

---

## 1. Priority order — as executed

1. **A9 first** (both copies: `skip_seeds`, `skip_seed_id`) — highest
   real-world value, per `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md`'s own
   live finding that this exact rule is the ACTIVE/WINNING dispatch path
   for the common `'test'`-anchored, non-`'replay'` self-experiment
   concern.
2. **A7 second** (both copies: the `has_judge&&has_structure` `apick`
   branch, the `has_judge&&has_gradient` `best` branch).
3. **A8 — sized as follow-on, not attempted.** Confirmed harder, per §5.

Both duplicate copies of A9 were fixed together, and both duplicate
copies of A7 were fixed together, exactly as the PREREG registered
(fixing only one copy of a pair would produce a WORSE, inconsistent
state — `skip_seeds` naming a different seed than `skip_seed_id` for the
identical axis, or the "structure" and "gradient" experiment families
picking different acting rules for the identical residual).

---

## 2. The edit, as built

**Mechanism: wrap, not rewrite** (registered in the PREREG §3, executed
exactly as registered). For each of the four sites, the existing
collapsed pick (already node-or-`null` / already seed_id-or-`""`) is
renamed into a fresh `Let` binding (`primary_pick_apick` /
`primary_pick_grad` / `primary_seed_a` / `primary_seed_b`) whose body is:
if the primary result is the abstain sentinel, evaluate a SECOND `Argmax`
— over the IDENTICAL candidate `Filter`, scored by `StringIndexOf` against
`where_signature_json` instead of `keywords_text` — else return the
primary result unchanged. The existing Argmax/collapse interior (170+
lines each) was extracted **verbatim by brace-counting** (never
hand-retyped) and validated as standalone-parseable JSON
(`json.loads`) before being spliced into the new wrapper; the whole file
was validated with `json.loads` after every single edit. Tooling:
`wrap_fallback.py` (brace-matching extractor + wrapper builder) +
`apply_edits.py` (the four site-specific calls, in strictly descending
original-line-number order so an earlier edit's insertions never shift
the anchor line of a not-yet-applied later-in-file edit) — both written
for this rung, not part of the seed itself, kept in this worktree for
reproducibility.

No new Rust Term. Every Term used (`Argmax`, `Filter`, `Sum`,
`StringIndexOf`, `IfThenElse`, `Let`, `Eq`, `Gt`, `Attr`, `Var`, `Lit`) is
already used elsewhere in this exact file.

**Design choice (registered in PREREG §2, unchanged after building):**
reuse the EXISTING precomputed aggregate attrs
(`RuleSummary.where_signature_json` for A7, `SeedSummary.
where_signature_json` for A9) via the identical `StringIndexOf`-`Sum`
overlap shape `keywords_text` already uses — the same choice the Python
A1/A3 fixes already made and measured, not a new one.

**File-size delta**: `seeds/composer_experiment_graph.json` grew from
216,710 to 230,318 bytes (+769 lines / +6.3%) across all four sites — the
node/edge counts (`3` Rule nodes, `0` top-level edges) are UNCHANGED, as
registered as the correctness invariant in PREREG §4.2.

---

## 3. The reachability caveat — found exactly as PREREG §2 predicted it
would be, not discovered by surprise

Neither `RuleSummary.where_signature_json` nor `SeedSummary.
where_signature_json` is populated at boot, or by anything inside
`compose_experiment_mint_parametric`'s own firing. Both are populated by
exactly one Python call each
(`rule_signature.ensure_where_signature` / `seed_signature.
ensure_seed_signature`), from exactly the places CLAUDE.md's own prior
rungs already built them for the PYTHON A1/A3 fixes — nowhere else. A
graph-resident Rule cannot call Python, so on a cold graph the fallback
finds the attr absent on every candidate and correctly, honestly falls
through to the (still-honest) abstain sentinel — confirmed directly, see
§4's negative controls.

**Every live demonstration below primes the relevant attr explicitly as
test/demo setup** (`rsig.ensure_where_signature(ag.s)` /
`ssig.ensure_seed_signature(ag.s)`, called once, idempotent) — this is
the SAME precompute step the already-landed Python A1/A3 fixes themselves
depend on to do anything at all, not a new mechanism invented for this
rung. **Whether something should prime these attrs automatically before
`compose_experiment_mint_parametric` fires in a live daemon (e.g. a
low-cost pass at seed-load time, or triggering it from
`_ensure_acting_rule_provenance`'s own call site inside
`_route_experiment_composer`, which already runs unconditionally whenever
`want_gradient`/`want_structure`) is an honest, precisely-scoped residual,
not solved here** — sized in §6.

For A7 specifically this residual is **narrower than for A9**:
`_route_experiment_composer` already calls `_ensure_acting_rule_
provenance` unconditionally whenever `want_gradient or want_structure`
(`reflective_faculty.py:6131-6134`) — the SAME call site would only need
one more line (`rsig.ensure_where_signature(sub0)`) to close this for A7
in production. A9's seed-signature precompute has no equivalent
already-unconditional call site in the graph-dispatch path at all (the
Python `_compose_experiment_rule`'s own `vary` branch is exactly the
function A9 shadows in production, per `SEED_PICK_STRUCTURAL_FALLBACK_
RESULTS.md` §5) — closing it fully is the larger of the two asks. Neither
is attempted here; both are named precisely in §6.

---

## 4. Live demonstrations — through the REAL, loaded, edited seed's REAL
`compose_experiment_mint_parametric` rule, fired via `rf.ground_concern`
(the genuine production dispatch seam)

### 4.1 A9 (`demo_a9.py`)

A9's pick is **deferred**: the `{"__term__": ...}` payload is embedded
into the SECOND-order minted rule's own `SeedDelta` effects, to be
evaluated when THAT rule later fires — confirmed by the test suite's own
comment (`test_vary_bare_graph_rule_fires_and_picks_skip_seeds`: *"the
skip_seeds Argmax (deferred to the mint rule's own fire time)"*). A
**known, pre-existing, unrelated engine gotcha** blocks driving this
end-to-end through a SECOND `run_rules()` pass in this harness — see §4.3
— so, mirroring `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md`'s own §5
precedent exactly (same rigor, same reason): the REAL minted rule's own
`__term__` is extracted from the genuine `ground_concern` return value
(never hand-rebuilt) and evaluated directly via `native.evaluate(term,
{"axis": probe_axis_node})`.

Probes: target seed `investigation_loop` (REAL manifest on disk, REAL
`keywords_text` computed via the actual `boot_all._seed_keywords_text`,
REAL `where_signature_json` computed via the actual `seed_signature.
seed_where_signature` reading that manifest — nothing hand-invented), word
`has_plan` — reused directly from `SEED_PICK_STRUCTURAL_FALLBACK_
RESULTS.md`'s own already-measured Class-A probe list (`investigation_
loop` ← `has_plan`), sanity-reconfirmed on this file's own data before
use. Class B: seed `abandon_on_stuck`, word `committed` (that doc's own
Class-B probe).

```
[setup] real keywords_text('investigation_loop') lacks 'has_plan': OK
[setup] real keywords_text('abandon_on_stuck') contains 'committed': OK
[Class A setup] ensure_seed_signature minted 2 where_signature_json attrs
[Class A setup] investigation_loop's where_signature_json genuinely contains 'has_plan': OK
[Class A] real minted rule: 'author_experiment_from_residual_a9_classA'
[Class A] skip_seed_id Term (extracted from the REAL rule) picked: 'investigation_loop'
[Class A] skip_seeds Term (extracted from the REAL rule) picked: 'investigation_loop'
[Class A] PASS -- structural fallback recovered the real target seed on BOTH copies
[Class B] skip_seed_id Term picked: 'abandon_on_stuck' (where_signature_json NEVER primed)
[Class B] skip_seeds Term picked: 'abandon_on_stuck' (where_signature_json NEVER primed)
[Class B] PASS -- primary alone recovered the seed; fallback never needed
```

Class B is a genuine negative case for the fallback path, not just an
unchanged-primary check: `ensure_seed_signature` was deliberately never
called on that agent, so `where_signature_json` is absent on every node —
if the fallback had somehow been consulted it would have found nothing,
so a passing Class B here also indirectly confirms the primary branch's
`Ite` guard is doing its job (never falling through when it shouldn't).

### 4.2 A7 (`demo_a7.py`) — both copies

A7's pick is **eager**: `act_rule_varied` / `remove_rules` /
`edit_op_kind` are baked as plain literal strings into the minted rule's
own effects the moment `compose_experiment_mint_parametric` fires —
confirmed by inspecting the genuine `ground_concern` return value before
writing the demo (no `__term__` wrapper on these fields, unlike A9). This
means the ONE real `ground_concern` call **is** the full demonstration —
no extraction-and-standalone-evaluate step needed.

**A7b (gradient branch, `has_judge&&has_gradient`).** Target: grid_
navigation's only `writes_chosen_action` rule, `hop_descend_gradient`
(REAL `keywords_text` = `"hop descend gradient"`, REAL `where_signature_
json` genuinely contains `nav_mode` — confirmed by reading the minted
rule's own `where` clause, which literally compares `game.nav_mode` to
`'pocket_escape'`). Class A residual: `["test", "send", "judge", "acting
rule", "nav_mode"]` — `"acting rule"` grounds `has_gradient` via the SAME
`vary_acting_gradient` RelationCue the bare word `"gradient"` would
(confirmed: the grounded relation head is `"gradient"` regardless of
which of the cue's keyword phrases triggered it, so the residual carries
**no word that is a substring of `"hop descend gradient"`** — a genuine
primary abstention, not a near-miss):

```
[Class A setup] primed where_signature_json on 1 RuleSummary node(s)
[Class A] act_rule_varied='hop_descend_gradient' act_shift=5
[Class A] PASS
[Class B] act_rule_varied='hop_descend_gradient' (where_signature_json NEVER primed on this agent)
[Class B] PASS
```

**A7a (structure branch, `has_judge&&has_structure`).** Same target rule;
residual `["test", "send", "judge", "structure", "nav_mode", "flip"]`
(`"flip"` lets the untouched A8/`epick` pick a real EditOp kind so the
branch's OWN `Eq(op, null)` gate — independent of A7's own gate — doesn't
mask the result):

```
[Class A] structural_variant.built=True removed_rule='hop_descend_gradient' kind='flip_comparison'
[Class A] PASS
[Class B] structural_variant.built=True removed_rule='hop_descend_gradient' (where_signature_json NEVER primed)
[Class B] PASS
```

### 4.3 Negative control — genuine double-abstain still abstains honestly

Both A9 and A7b were also probed with a residual word matching NEITHER
`keywords_text` NOR `where_signature_json` on any candidate
(`"zzzznomatchxyzzy"`):

```
A9 double-abstain skip_seed_id -> ''
A9 double-abstain skip_seeds -> '[]'
A7b double-abstain act_rule_varied -> ''
NEGATIVE CONTROLS PASS -- genuine double-abstain still abstains honestly, no fabricated pick
```

This confirms the wrap did not accidentally widen the abstain condition
(e.g. by always falling through to *some* Argmax winner) — the fallback's
own `Gt(struct_overlap(...), 0.0)` guard correctly declines when it too
finds nothing.

### 4.3b The pre-existing engine gotcha the deferred-Term extraction
(§4.1) routes around, confirmed independently on THIS worktree, not
assumed from the prior rung's report

`tests/test_experiment_composer_graph.py::test_vary_bare_graph_rule_
fires_and_picks_skip_seeds` (behavioral: fires the SECOND-order minted
rule for real via a second `run_rules()` pass) fails **identically before
and after every edit in this rung** — `assert exp is not None` /
`assert None is not None`, i.e. the second-order rule never fires at all
in this harness shape, an entirely different symptom from anything A9's
Term itself computes. This is the exact "installed rule never fires via
`run_rules()`" gotcha `SEED_PICK_STRUCTURAL_FALLBACK_RESULTS.md` §5
already named for the SAME test family, independently reconfirmed here
rather than taken on trust — see §6's regression tables: this specific
test is in the baseline failing set, unchanged.

---

## 5. A8 — confirmed to need the applicability-gate shape, sized as
follow-on

Reading `epick`'s actual Term (`seeds/composer_experiment_graph.json`,
pre-edit line 1366) confirms the PREREG's own prediction:

```json
"value": {"type": "Argmax", "source": {"type": "NodesOfType", "node_type": "EditOp"}, "var_name": "s", ...}
```

**No `Filter` at all** — unlike `apick`'s `Filter(..., writes_chosen_
action==1 && skippable==1)`, `epick` scores literally every `EditOp` node
that exists. This matches `EDIT_OP_APPLICABILITY_GATE_RESULTS.md`'s own
finding for the PYTHON twin (A4) exactly: the fix that closed A4 was NOT
a structural-fallback Argmax (that shape was tried and independently
declined by an EVEN EARLIER rung, verdict NEGLIGIBLE — zero cross-blurb
keyword collision among the four `EditOp` kinds, and no `where`/`match`/
`effects` object on an `EditOp` node to derive a `where_signature_json`-
style signature from in the first place, since an `EditOp` names an
OPERATOR, not a rule). The actual A4 fix was an **applicability gate**:
restrict candidate EditOp KINDS to those structurally POSSIBLE on the
specific PICKED rule, computed in Python from that rule's own `rule_json`
dict via `edit_ops.find_comparison_nodes`/`find_attr_keys`. That same
RESULTS doc states explicitly: *"there is no Term that walks an arbitrary
JSON-shaped attribute value (the Term algebra reads the GRAPH, not the
internals of one string attribute)."*

**What WOULD close A8, sized precisely (not just "impossible"):** unlike
`rule_json` walking, this IS expressible in the existing Term algebra with
no new Rust, because `epick`'s Argmax runs INSIDE the branch where
`picked` (A7's OWN resolved RuleSummary node) is ALREADY in lexical scope
(confirmed by reading the structure: `epick` is nested inside the `other`
arm of `Eq(picked, null)`). The fix would be: (a) a NEW Python precompute,
mirroring `_ensure_acting_rule_provenance`'s own precedent, that stamps
FOUR new boolean attrs onto each `RuleSummary` node at mint time — one per
`_EDIT_OPS` kind (`applicable_flip`, `applicable_swap`, `applicable_drop`,
`applicable_guard`), using the SAME `edit_ops.find_comparison_nodes`/
`find_attr_keys` predicates `_editop_applicable_kinds` already computes
in Python for the A4 fix; (b) `epick`'s `Filter` restricted to `Or(And(Eq(
s.kind, "flip_comparison"), Eq(Attr(V("picked"), "applicable_flip"),
1.0)), ...)` — an ordinary `Filter`/`Or`/`And`/`Eq`/`Attr` restriction, the
same Term vocabulary already used throughout this file. **This is
correctly sized as a follow-on, not attempted this rung**, for two
reasons stated plainly: (1) it requires NEW Python-side precompute
infrastructure that has never been designed or measured (unlike A7/A9,
which reuse an attr this rung's sibling rungs already built and measured);
(2) per this rung's own house discipline — prioritise correctness over
completing all three, and elevated care specifically because this is
hand-edited LIVE seed-resident Term JSON — building and validating a NEW
four-flag precompute function plus its own powered Class-A/B oracle in the
same sitting as the A7/A9 edits would dilute the validation rigor applied
to each, not add to it.

---

## 6. Regression — captured per-edit, not just once at the end

**Baseline (BEFORE any edit, this worktree, tip `8af4fde`)** —
`tests/test_experiment_composer_graph.py` + `tests/test_composers_graph.py`:

```
10 failed, 98 passed in 173.90s
FAILED tests/test_experiment_composer_graph.py::test_full_combo_gradient_embed_matches_shift_rule_thresholds_oracle
FAILED tests/test_experiment_composer_graph.py::test_test_alone_graph_rule_mints_experiment_without_host_add_node
FAILED tests/test_experiment_composer_graph.py::test_vary_bare_structurally_matches_python_oracle
FAILED tests/test_experiment_composer_graph.py::test_vary_bare_graph_rule_fires_and_picks_skip_seeds
FAILED tests/test_experiment_composer_graph.py::test_embed_graph_rule_fires_and_embeds_a_real_variant
FAILED tests/test_experiment_composer_graph.py::test_parametric_mint_matches_python_oracle_matrix[bare_vary]
FAILED tests/test_experiment_composer_graph.py::test_parametric_mint_matches_python_oracle_matrix[embed]
FAILED tests/test_experiment_composer_graph.py::test_parametric_mint_matches_python_oracle_matrix[vary_no_send]
FAILED tests/test_experiment_composer_graph.py::test_parametric_mint_matches_python_oracle_matrix[vary_plus_structure]
FAILED tests/test_experiment_composer_graph.py::test_parametric_mint_matches_python_oracle_matrix[vary_embed_plus_gradient]
```

**AFTER A9 (both copies), same 2 files:**

```
10 failed, 98 passed in 171.70s
```

— the SAME 10 node ids, byte-identical (`diff` clean; verified before
proceeding to A7).

**AFTER A9 + A7 (all four sites), same 2 files:**

```
10 failed, 98 passed in 170.18s
```

— again the SAME 10 node ids, byte-identical.

**Broader net, run once after all four edits, paired against a
git-stash-isolated BEFORE run on the SAME worktree/commit** (`tests/
test_structural_variant.py` + `tests/test_acting_variant.py` + `tests/
test_experiment_composer.py`):

```
BEFORE (git stash):  3 failed, 36 passed, 2 skipped
AFTER  (edits back):  3 failed, 36 passed, 2 skipped
FAILED tests/test_structural_variant.py::test_full_structural_variant_loop_offline
FAILED tests/test_acting_variant.py::test_close_experiment_loop_names_the_varied_acting_rule
FAILED tests/test_experiment_composer.py::test_mint_rule_fires_without_host_add_node
```

— identical in both directions. `test_mint_rule_fires_without_host_add_
node` and `test_close_experiment_loop_names_the_varied_acting_rule` are
both independently already documented as pre-existing in `SEED_PICK_
STRUCTURAL_FALLBACK_RESULTS.md`'s own AR4 baseline; `test_full_
structural_variant_loop_offline` was not previously documented by name
but is confirmed pre-existing HERE, on this worktree, via the paired
stash comparison — not assumed from another rung's report.

**Zero test anywhere in either regression net went from green to red, and
zero went from red to green, across all four edits.**

---

## 7. What this does NOT establish

- **Does not fix A8.** Sized precisely in §5, not attempted — a genuinely
  different (applicability-gate, not structural-fallback) fix shape,
  requiring new Python precompute infrastructure this rung correctly
  declined to design and validate in the same sitting as the A7/A9 edits.
- **Does not make A9's (or A7's) fallback fire automatically in today's
  live daemon without the priming call.** Per §3, `where_signature_json`
  is populated only by an explicit precompute call this rung's demos make
  themselves, exactly mirroring the already-landed Python A1/A3 fixes'
  own dependency — not a new gap this rung introduced, but not closed by
  it either. Closing it (§3's two concretely-scoped options) is future
  work, not attempted here.
- **Does not fix the pre-existing "second-order minted rule doesn't
  re-fire via a second `run_rules()` pass" engine gotcha** (§4.3b) —
  independently reconfirmed present, unrelated to and unmoved by this
  rung's edits, already named by a prior rung.
- **A synthetic-proven mechanism, not a benchmark value**: this closes a
  real, demonstrated MAC/FAC gap at four specific graph-resident sites
  (A9 ×2, A7 ×2), through the REAL loaded, live-installed rule. It says
  nothing about how often, in practice, the primary `keywords_text`
  Argmax genuinely abstains on a live agent's real self-experiment
  concerns versus already matching — no prevalence measurement was in
  scope or attempted (the same honest boundary `EDIT_OP_APPLICABILITY_
  GATE_RESULTS.md` drew for A4).
- **Does not re-litigate whether `where_signature_json` should be a
  precomputed aggregate vs. a live join** — inherited, unchanged, from
  the Python A1/A3 rungs' own already-made and already-measured design
  choice (PREREG §2).

---

## Worktree / reproduce

**Worktree:** `/tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a7-a9`,
branch `mac-fac-a7-a9`, detached from `main` at `8af4fde`.

```bash
cd /tmp/claude-1000/-home-matt-ozmadev-ocelot/34a7cd08-5eb1-42bd-af0c-eedb1125fa76/scratchpad/mac-fac-a7-a9
git log --oneline -1                                   # on mac-fac-a7-a9, base 8af4fde
python3 -c "import json; json.load(open('seeds/composer_experiment_graph.json'))"   # valid JSON
python3 demo_a9.py                                      # A9 Class-A/B + negative control
python3 demo_a7.py                                       # A7 Class-A/B, both copies
python3 -m pytest tests/test_experiment_composer_graph.py tests/test_composers_graph.py -q
python3 -m pytest tests/test_structural_variant.py tests/test_acting_variant.py tests/test_experiment_composer.py -q
```
